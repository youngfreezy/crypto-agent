from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Signal:
    symbol: str
    action: str  # "buy", "sell", or "hold"
    strength: float
    strategy_name: str


@dataclass
class Order:
    symbol: str
    side: str  # "buy" or "sell"
    order_type: str  # "market" or "limit"
    quantity: float
    limit_price: Optional[float] = None


@dataclass
class Trade:
    symbol: str
    side: str
    quantity: float
    fill_price: float
    fee: float
    strategy_name: Optional[str]
    signal_strength: Optional[float]
    pnl: Optional[float]
    created_at: datetime
