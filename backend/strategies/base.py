from abc import ABC, abstractmethod
from typing import Optional

from backend.engine.order_book import Signal


class Strategy(ABC):
    name: str
    description: str

    @abstractmethod
    def evaluate(self, symbol: str, candles: list[dict]) -> Optional[Signal]:
        """Given recent candles (list of dicts with open/high/low/close/volume/timestamp keys), return a Signal or None."""
        ...

    @abstractmethod
    def required_candles(self) -> int:
        """Minimum candle history needed."""
        ...
