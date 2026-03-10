"""Paper trading engine."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable

from backend.engine.order_book import Order, Signal, Trade
from backend.engine import portfolio, risk
from backend.shared.db import get_connection

logger = logging.getLogger(__name__)

ALLOCATION_PCT = 0.05  # 5% of portfolio value per trade
SLIPPAGE_PCT = 0.0005  # 0.05%
FEE_PCT = 0.001  # 0.1%


class PaperTrader:
    def __init__(self, get_price_fn: Callable):
        self.get_price_fn = get_price_fn

    def execute_order(self, order: Order) -> Trade:
        """Validate, fill with slippage/fees, persist, and update portfolio."""
        price = self.get_price_fn(order.symbol)
        if price is None:
            raise ValueError(f"No price available for {order.symbol}")

        # Build positions map for risk check
        positions_list = portfolio.get_positions()
        positions_map = {p["symbol"]: p["quantity"] for p in positions_list}
        latest_prices = {order.symbol: price}
        for p in positions_list:
            if p["symbol"] not in latest_prices:
                p_price = self.get_price_fn(p["symbol"])
                if p_price:
                    latest_prices[p["symbol"]] = p_price

        account = portfolio.get_account()
        portfolio_data = portfolio.get_portfolio(latest_prices)

        allowed, reason = risk.check_order(
            order, account["cash"], positions_map, latest_prices, portfolio_data["total_value"]
        )
        if not allowed:
            raise ValueError(f"Order rejected: {reason}")

        # Apply slippage
        if order.side == "buy":
            fill_price = price * (1 + SLIPPAGE_PCT)
        else:
            fill_price = price * (1 - SLIPPAGE_PCT)

        # Calculate fee
        fee = order.quantity * fill_price * FEE_PCT

        trade = Trade(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            fill_price=fill_price,
            fee=fee,
            strategy_name=None,
            signal_strength=None,
            pnl=None,
            created_at=datetime.now(timezone.utc),
        )

        # Update portfolio (this also calculates realized P&L for sells)
        portfolio.update_position(trade)

        # Persist trade
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO trades (symbol, side, quantity, fill_price, fee, strategy_name, "
                    "signal_strength, pnl, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        trade.symbol, trade.side, trade.quantity, trade.fill_price,
                        trade.fee, trade.strategy_name, trade.signal_strength,
                        trade.pnl, trade.created_at,
                    ),
                )
            conn.commit()

        logger.info(
            "Executed %s %s %.6f @ %.2f (fee=%.4f, pnl=%s)",
            trade.side, trade.symbol, trade.quantity, trade.fill_price,
            trade.fee, trade.pnl,
        )
        return trade

    def process_signal(self, signal: Signal) -> Trade | None:
        """Convert a signal into an order and execute it."""
        if signal.action == "hold":
            return None

        price = self.get_price_fn(signal.symbol)
        if price is None:
            logger.warning("No price for %s, skipping signal", signal.symbol)
            return None

        latest_prices = {signal.symbol: price}
        portfolio_data = portfolio.get_portfolio(latest_prices)
        allocation = portfolio_data["total_value"] * ALLOCATION_PCT
        quantity = allocation / price

        if quantity <= 0:
            logger.warning("Calculated zero quantity for %s, skipping", signal.symbol)
            return None

        # For sell signals, check we actually hold the position
        if signal.action == "sell":
            positions = portfolio.get_positions()
            held = next((p for p in positions if p["symbol"] == signal.symbol), None)
            if not held or held["quantity"] <= 0:
                logger.info("No position in %s to sell, skipping", signal.symbol)
                return None
            quantity = held["quantity"]

        order = Order(
            symbol=signal.symbol,
            side=signal.action,
            order_type="market",
            quantity=quantity,
        )

        try:
            trade = self.execute_order(order)
        except ValueError as e:
            logger.warning("Signal order rejected: %s", e)
            return None

        # Update the persisted trade with strategy info
        trade.strategy_name = signal.strategy_name
        trade.signal_strength = signal.strength
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE trades SET strategy_name = %s, signal_strength = %s "
                    "WHERE symbol = %s AND created_at = %s",
                    (trade.strategy_name, trade.signal_strength, trade.symbol, trade.created_at),
                )
            conn.commit()

        return trade

    def get_trade_history(
        self,
        limit: int = 50,
        offset: int = 0,
        symbol: str | None = None,
        strategy: str | None = None,
    ) -> list[dict]:
        """Query trades table with optional filters."""
        query = (
            "SELECT symbol, side, quantity, fill_price, fee, strategy_name, "
            "signal_strength, pnl, created_at FROM trades"
        )
        conditions = []
        params: list = []

        if symbol:
            conditions.append("symbol = %s")
            params.append(symbol)
        if strategy:
            conditions.append("strategy_name = %s")
            params.append(strategy)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(params))
                rows = cur.fetchall()

        return [
            {
                "symbol": r[0],
                "side": r[1],
                "quantity": float(r[2]),
                "fill_price": float(r[3]),
                "fee": float(r[4]),
                "strategy_name": r[5],
                "signal_strength": float(r[6]) if r[6] is not None else None,
                "pnl": float(r[7]) if r[7] is not None else None,
                "created_at": r[8].isoformat() if r[8] else None,
            }
            for r in rows
        ]

    def get_trade_stats(self) -> dict:
        """Calculate aggregate trade statistics."""
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*), COALESCE(SUM(pnl), 0), COALESCE(AVG(pnl), 0) "
                    "FROM trades WHERE pnl IS NOT NULL"
                )
                row = cur.fetchone()
                trades_with_pnl = int(row[0])
                total_pnl = float(row[1])
                avg_pnl = float(row[2])

                winning = 0
                if trades_with_pnl > 0:
                    cur.execute("SELECT COUNT(*) FROM trades WHERE pnl > 0")
                    winning = int(cur.fetchone()[0])

                cur.execute("SELECT COUNT(*) FROM trades")
                total_trades = int(cur.fetchone()[0])

        return {
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "win_rate": winning / trades_with_pnl if trades_with_pnl > 0 else 0.0,
        }
