"""Portfolio state manager."""

from datetime import datetime, timezone

from backend.engine.order_book import Trade
from backend.shared.db import get_connection


def get_account() -> dict:
    """Return {cash, initial_capital} from the account table."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT cash, initial_capital FROM account LIMIT 1")
            row = cur.fetchone()
    if row is None:
        return {"cash": 0.0, "initial_capital": 0.0}
    return {"cash": float(row[0]), "initial_capital": float(row[1])}


def get_positions() -> list[dict]:
    """Return all positions with quantity > 0."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT symbol, quantity, avg_entry FROM positions WHERE quantity > 0"
            )
            rows = cur.fetchall()
    return [
        {"symbol": r[0], "quantity": float(r[1]), "avg_entry": float(r[2])}
        for r in rows
    ]


def get_portfolio(latest_prices: dict) -> dict:
    """Build full portfolio view with unrealized P&L."""
    account = get_account()
    positions = get_positions()

    total_position_value = 0.0
    total_unrealized = 0.0

    for pos in positions:
        current_price = latest_prices.get(pos["symbol"], pos["avg_entry"])
        pos["current_price"] = current_price
        market_value = pos["quantity"] * current_price
        cost_basis = pos["quantity"] * pos["avg_entry"]
        pos["unrealized_pnl"] = market_value - cost_basis
        total_position_value += market_value
        total_unrealized += pos["unrealized_pnl"]

    # Sum realized P&L from trades table
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(SUM(pnl), 0) FROM trades WHERE pnl IS NOT NULL")
            realized_pnl = float(cur.fetchone()[0])

    return {
        "cash": account["cash"],
        "positions": positions,
        "total_value": account["cash"] + total_position_value,
        "unrealized_pnl": total_unrealized,
        "realized_pnl": realized_pnl,
    }


def update_position(trade: Trade) -> None:
    """Update positions and account cash after a trade."""
    cost = trade.quantity * trade.fill_price
    realized_pnl = 0.0

    with get_connection() as conn:
        with conn.cursor() as cur:
            if trade.side == "buy":
                cur.execute(
                    "UPDATE account SET cash = cash - %s, updated_at = NOW()",
                    (cost + trade.fee,),
                )

                cur.execute(
                    "SELECT quantity, avg_entry FROM positions WHERE symbol = %s",
                    (trade.symbol,),
                )
                row = cur.fetchone()

                if row and float(row[0]) > 0:
                    old_qty = float(row[0])
                    old_avg = float(row[1])
                    new_qty = old_qty + trade.quantity
                    new_avg = (old_qty * old_avg + cost) / new_qty
                    cur.execute(
                        "UPDATE positions SET quantity = %s, avg_entry = %s, updated_at = NOW() WHERE symbol = %s",
                        (new_qty, new_avg, trade.symbol),
                    )
                elif row:
                    cur.execute(
                        "UPDATE positions SET quantity = %s, avg_entry = %s, updated_at = NOW() WHERE symbol = %s",
                        (trade.quantity, trade.fill_price, trade.symbol),
                    )
                else:
                    cur.execute(
                        "INSERT INTO positions (symbol, quantity, avg_entry) VALUES (%s, %s, %s)",
                        (trade.symbol, trade.quantity, trade.fill_price),
                    )

            elif trade.side == "sell":
                cur.execute(
                    "SELECT quantity, avg_entry FROM positions WHERE symbol = %s",
                    (trade.symbol,),
                )
                row = cur.fetchone()
                if row:
                    avg_entry = float(row[1])
                    old_qty = float(row[0])
                    realized_pnl = trade.quantity * (trade.fill_price - avg_entry)
                    new_qty = old_qty - trade.quantity
                    cur.execute(
                        "UPDATE positions SET quantity = %s, updated_at = NOW() WHERE symbol = %s",
                        (max(new_qty, 0), trade.symbol),
                    )

                cur.execute(
                    "UPDATE account SET cash = cash + %s, updated_at = NOW()",
                    (cost - trade.fee,),
                )

        conn.commit()

    if trade.side == "sell" and realized_pnl != 0.0:
        trade.pnl = realized_pnl


def take_snapshot(latest_prices: dict) -> None:
    """Insert a portfolio snapshot row for equity curve tracking."""
    p = get_portfolio(latest_prices)
    positions_value = p["total_value"] - p["cash"]

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO portfolio_snapshots "
                "(total_value, cash_balance, positions_value, unrealized_pnl, realized_pnl, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    p["total_value"],
                    p["cash"],
                    positions_value,
                    p["unrealized_pnl"],
                    p["realized_pnl"],
                    datetime.now(timezone.utc),
                ),
            )
        conn.commit()


def get_snapshots(limit: int = 500) -> list[dict]:
    """Return recent portfolio snapshots for equity curve."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT total_value, cash_balance, positions_value, unrealized_pnl, realized_pnl, created_at "
                "FROM portfolio_snapshots ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            rows = cur.fetchall()

    return [
        {
            "total_value": float(r[0]),
            "cash_balance": float(r[1]),
            "positions_value": float(r[2]),
            "unrealized_pnl": float(r[3]),
            "realized_pnl": float(r[4]),
            "created_at": r[5].isoformat() if r[5] else None,
        }
        for r in reversed(rows)  # chronological order
    ]
