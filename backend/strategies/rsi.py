from typing import Optional

import numpy as np

from backend.engine.order_book import Signal
from backend.shared.config import get_settings
from backend.strategies.base import Strategy

settings = get_settings()


class RSIStrategy(Strategy):
    name = "rsi"
    description = "Relative Strength Index"

    def __init__(self) -> None:
        self.period: int = settings.RSI_PERIOD
        self.overbought: float = settings.RSI_OVERBOUGHT
        self.oversold: float = settings.RSI_OVERSOLD

    def _compute_rsi(self, closes: np.ndarray) -> np.ndarray:
        """Compute RSI series from close prices."""
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)

        # Seed with simple average over the first `period` changes
        avg_gain = np.mean(gains[: self.period])
        avg_loss = np.mean(losses[: self.period])

        rsi_values = []
        for i in range(self.period, len(deltas)):
            avg_gain = (avg_gain * (self.period - 1) + gains[i]) / self.period
            avg_loss = (avg_loss * (self.period - 1) + losses[i]) / self.period

            if avg_loss == 0:
                rsi_values.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100.0 - 100.0 / (1.0 + rs))

        return np.array(rsi_values)

    def evaluate(self, symbol: str, candles: list[dict]) -> Optional[Signal]:
        closes = np.array([c["close"] for c in candles], dtype=float)

        if len(closes) < self.period + 2:
            return None

        rsi = self._compute_rsi(closes)

        if len(rsi) < 2:
            return None

        # Strength: distance from midpoint (50), normalized to 0-1
        strength = abs(rsi[-1] - 50.0) / 50.0
        strength = min(strength, 1.0)

        # BUY: RSI crosses above oversold from below
        if rsi[-1] > self.oversold and rsi[-2] <= self.oversold:
            return Signal(
                symbol=symbol,
                action="buy",
                strength=strength,
                strategy_name=self.name,
            )

        # SELL: RSI crosses below overbought from above
        if rsi[-1] < self.overbought and rsi[-2] >= self.overbought:
            return Signal(
                symbol=symbol,
                action="sell",
                strength=strength,
                strategy_name=self.name,
            )

        return None

    def required_candles(self) -> int:
        return self.period + 2
