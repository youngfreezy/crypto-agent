"""Autonomous AI trading strategy powered by Claude."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional

import numpy as np

from backend.engine.order_book import Signal
from backend.engine.portfolio import get_account, get_portfolio, get_positions
from backend.shared.config import get_settings
from backend.shared.db import get_connection
from backend.strategies.base import Strategy
from backend.strategies.claude_api import analyze_market

logger = logging.getLogger(__name__)
settings = get_settings()


class ClaudeStrategy(Strategy):
    name = "claude_ai"
    description = "Autonomous AI reasoning (Claude Haiku)"

    def __init__(self) -> None:
        self._last_eval_time: dict[str, datetime] = {}
        self._last_prices: dict[str, float] = {}

    def required_candles(self) -> int:
        return 60  # 1 hour of 1m candles

    def evaluate(self, symbol: str, candles: list[dict]) -> Optional[Signal]:
        if not settings.ANTHROPIC_API_KEY:
            return None

        if not self._should_evaluate(symbol, candles):
            return None

        logger.info("Claude AI evaluating %s...", symbol)

        # Compute technical indicators
        indicators = self._compute_indicators(candles)

        # Get portfolio context
        portfolio = self._get_portfolio_context()

        # Get recent trades by this strategy
        recent_trades = self._get_recent_trades(symbol)

        # Get all prices for cross-symbol context
        all_prices = self._get_all_prices(candles, symbol)

        # Call Claude
        result = analyze_market(
            symbol=symbol,
            candles=candles,
            indicators=indicators,
            portfolio=portfolio,
            recent_trades=recent_trades,
            all_prices=all_prices,
        )

        if result is None:
            return None

        # Persist analysis (including holds)
        self._persist_analysis(symbol, result, indicators)

        logger.info(
            "Claude AI → %s %s (strength=%.2f): %s",
            result["action"].upper(),
            symbol,
            result["strength"],
            result["reasoning"][:100],
        )

        # Update tracking
        self._last_eval_time[symbol] = datetime.now(timezone.utc)
        if candles:
            self._last_prices[symbol] = candles[-1]["close"]

        if result["action"] == "hold":
            return None

        return Signal(
            symbol=symbol,
            action=result["action"],
            strength=result["strength"],
            strategy_name=self.name,
        )

    def _should_evaluate(self, symbol: str, candles: list[dict]) -> bool:
        """Check if enough time has passed and price has moved enough."""
        now = datetime.now(timezone.utc)

        # Check interval
        last_time = self._last_eval_time.get(symbol)
        if last_time:
            elapsed_minutes = (now - last_time).total_seconds() / 60
            if elapsed_minutes < settings.AI_EVAL_INTERVAL_MINUTES:
                return False

        # Check price change threshold
        if candles:
            current_price = candles[-1]["close"]
            last_price = self._last_prices.get(symbol)
            if last_price and last_price > 0:
                change = abs(current_price - last_price) / last_price
                if change < settings.AI_PRICE_CHANGE_THRESHOLD:
                    # Price hasn't moved enough, but still evaluate if interval is 2x
                    if last_time:
                        elapsed = (now - last_time).total_seconds() / 60
                        if elapsed < settings.AI_EVAL_INTERVAL_MINUTES * 2:
                            return False

        return True

    def _compute_indicators(self, candles: list[dict]) -> dict:
        """Compute SMA and RSI from candle data."""
        closes = np.array([c["close"] for c in candles], dtype=float)

        result = {}

        # SMA
        if len(closes) >= settings.SMA_FAST_PERIOD:
            result["sma_fast"] = float(np.mean(closes[-settings.SMA_FAST_PERIOD:]))
        if len(closes) >= settings.SMA_SLOW_PERIOD:
            result["sma_slow"] = float(np.mean(closes[-settings.SMA_SLOW_PERIOD:]))

        # RSI
        if len(closes) >= settings.RSI_PERIOD + 1:
            deltas = np.diff(closes[-(settings.RSI_PERIOD + 1):])
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains) if len(gains) > 0 else 0
            avg_loss = np.mean(losses) if len(losses) > 0 else 0
            if avg_loss == 0:
                result["rsi"] = 100.0
            else:
                rs = avg_gain / avg_loss
                result["rsi"] = float(100.0 - (100.0 / (1.0 + rs)))

        # Volume average
        volumes = [c["volume"] for c in candles]
        if volumes:
            result["volume_avg"] = float(np.mean(volumes))

        return result

    def _get_portfolio_context(self) -> dict:
        """Get current portfolio state for Claude's context."""
        try:
            account = get_account()
            positions = get_positions()
            total_pos_value = 0
            for p in positions:
                # Use last known price as approximation
                last_price = self._last_prices.get(p["symbol"], p["avg_entry"])
                p["current_price"] = last_price
                p["unrealized_pnl"] = p["quantity"] * (last_price - p["avg_entry"])
                total_pos_value += p["quantity"] * last_price

            return {
                "cash": account["cash"],
                "total_value": account["cash"] + total_pos_value,
                "positions": positions,
            }
        except Exception as e:
            logger.warning("Error getting portfolio context: %s", e)
            return {"cash": 0, "total_value": 0, "positions": []}

    def _get_recent_trades(self, symbol: str) -> list[dict]:
        """Get last 10 trades by this strategy."""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT symbol, side, quantity, fill_price, pnl, created_at "
                        "FROM trades WHERE strategy_name = %s "
                        "ORDER BY created_at DESC LIMIT 10",
                        (self.name,),
                    )
                    rows = cur.fetchall()
            return [
                {
                    "symbol": r[0],
                    "side": r[1],
                    "quantity": float(r[2]),
                    "fill_price": float(r[3]),
                    "pnl": float(r[4]) if r[4] else None,
                    "created_at": r[5].isoformat() if r[5] else None,
                }
                for r in rows
            ]
        except Exception as e:
            logger.warning("Error getting recent trades: %s", e)
            return []

    def _get_all_prices(self, candles: list[dict], current_symbol: str) -> dict:
        """Get latest prices for all symbols."""
        prices = dict(self._last_prices)
        if candles:
            prices[current_symbol] = candles[-1]["close"]
        return prices

    def _persist_analysis(self, symbol: str, result: dict, indicators: dict) -> None:
        """Save analysis to the ai_analyses table."""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO ai_analyses "
                        "(symbol, action, strength, reasoning, market_summary, indicators, "
                        "model, input_tokens, output_tokens, latency_ms) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (
                            symbol,
                            result["action"],
                            result["strength"],
                            result["reasoning"],
                            result.get("market_summary", ""),
                            json.dumps(indicators),
                            "claude-haiku-4-5",
                            result.get("input_tokens"),
                            result.get("output_tokens"),
                            result.get("latency_ms"),
                        ),
                    )
                conn.commit()
        except Exception as e:
            logger.error("Error persisting AI analysis: %s", e)
