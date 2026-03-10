"""Centralised configuration loaded from environment / .env file."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # --- Postgres ---
    DATABASE_URL: str = (
        "postgresql://cryptoagent:cryptoagent_dev@localhost:5434/cryptoagent"
    )

    # --- Exchange ---
    EXCHANGE: str = "binance"
    SYMBOLS: str = "BTC/USDT,ETH/USDT,SOL/USDT"

    # --- Paper trading ---
    INITIAL_CAPITAL: float = 100_000.0
    MAX_POSITION_PCT: float = 0.20

    # --- Strategy defaults ---
    DEFAULT_STRATEGY: str = "sma_crossover"
    SMA_FAST_PERIOD: int = 10
    SMA_SLOW_PERIOD: int = 50
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0

    # --- Data collection ---
    CANDLE_TIMEFRAME: str = "1m"
    CANDLE_HISTORY_DAYS: int = 7
    POLL_INTERVAL_SECONDS: int = 10

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": (
            str(_PROJECT_ROOT / ".env"),
            str(_PROJECT_ROOT / ".env.local"),
        ),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()  # type: ignore[call-arg]


def get_settings() -> Settings:
    return settings
