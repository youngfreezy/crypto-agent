from typing import Optional

import numpy as np

from backend.engine.order_book import Signal
from backend.shared.config import get_settings
from backend.strategies.base import Strategy

settings = get_settings()


class SMACrossoverStrategy(Strategy):
    name = "sma_crossover"
    description = "Simple Moving Average Crossover"

    def __init__(self) -> None:
        self.fast_period: int = settings.SMA_FAST_PERIOD
        self.slow_period: int = settings.SMA_SLOW_PERIOD

    def evaluate(self, symbol: str, candles: list[dict]) -> Optional[Signal]:
        closes = np.array([c["close"] for c in candles], dtype=float)

        if len(closes) < self.slow_period + 2:
            return None

        fast = np.convolve(closes, np.ones(self.fast_period) / self.fast_period, mode="valid")
        slow = np.convolve(closes, np.ones(self.slow_period) / self.slow_period, mode="valid")

        # Align arrays so indices correspond to the same candle
        offset = self.slow_period - self.fast_period
        fast = fast[offset:]

        if len(fast) < 2 or len(slow) < 2:
            return None

        strength = abs(fast[-1] - slow[-1]) / slow[-1]

        # BUY: fast crosses above slow
        if fast[-1] > slow[-1] and fast[-2] <= slow[-2]:
            return Signal(
                symbol=symbol,
                action="buy",
                strength=strength,
                strategy_name=self.name,
            )

        # SELL: fast crosses below slow
        if fast[-1] < slow[-1] and fast[-2] >= slow[-2]:
            return Signal(
                symbol=symbol,
                action="sell",
                strength=strength,
                strategy_name=self.name,
            )

        return None

    def required_candles(self) -> int:
        return self.slow_period + 2
