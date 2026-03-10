"""Market data feed using ccxt polling."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from functools import partial
from typing import Callable

import ccxt

from backend.shared.config import get_settings
from backend.market.symbols import get_symbols
from backend.market.candle_store import insert_candles

logger = logging.getLogger(__name__)


class MarketFeed:
    """Polls exchange OHLCV data on a regular interval using sync ccxt."""

    def __init__(self) -> None:
        settings = get_settings()
        self._exchange: ccxt.Exchange = getattr(ccxt, settings.EXCHANGE)()
        self._symbols = get_symbols()
        self._timeframe: str = settings.CANDLE_TIMEFRAME
        self._poll_interval: int = settings.POLL_INTERVAL_SECONDS
        self._history_days: int = settings.CANDLE_HISTORY_DAYS
        self._task: asyncio.Task | None = None
        self._latest_prices: dict[str, float] = {}
        self._on_candle_close: Callable | None = None

    async def start(self) -> None:
        """Start the polling loop. Fetches history first, then polls."""
        logger.info(
            "MarketFeed starting for %s on %s (%s)",
            self._symbols, self._exchange.id, self._timeframe,
        )
        await self._fetch_history()
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Cancel the polling task."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("MarketFeed stopped.")

    def get_latest_price(self, symbol: str) -> float | None:
        """Return the latest known price for a symbol, or None."""
        return self._latest_prices.get(symbol)

    def get_all_prices(self) -> dict[str, float]:
        """Return a copy of all latest prices."""
        return dict(self._latest_prices)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _run_sync(self, fn, *args):
        """Run a sync ccxt method in the default executor."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(fn, *args))

    async def _fetch_history(self) -> None:
        """Fetch historical candles for all symbols on first run."""
        since_ms = int(
            (datetime.now(timezone.utc).timestamp() - self._history_days * 86400) * 1000
        )
        for symbol in self._symbols:
            try:
                candles = await self._run_sync(
                    self._exchange.fetch_ohlcv,
                    symbol,
                    self._timeframe,
                    since_ms,
                    1000,
                )
                if candles:
                    insert_candles(symbol, self._timeframe, candles)
                    self._latest_prices[symbol] = candles[-1][4]  # close
                    logger.info(
                        "Loaded %d historical candles for %s", len(candles), symbol
                    )
            except Exception:
                logger.exception("Failed to fetch history for %s", symbol)

    async def _poll_loop(self) -> None:
        """Continuously poll for new candles."""
        while True:
            try:
                await asyncio.sleep(self._poll_interval)
                for symbol in self._symbols:
                    await self._poll_symbol(symbol)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Error in poll loop, retrying next interval")

    async def _poll_symbol(self, symbol: str) -> None:
        """Fetch the latest candles for a single symbol."""
        try:
            candles = await self._run_sync(
                self._exchange.fetch_ohlcv,
                symbol,
                self._timeframe,
                None,
                5,
            )
            if not candles:
                return

            insert_candles(symbol, self._timeframe, candles)

            latest_close = candles[-1][4]
            prev_price = self._latest_prices.get(symbol)
            self._latest_prices[symbol] = latest_close

            # Detect new closed candle: if the second-to-last candle timestamp
            # changed compared to what we had, a candle closed.
            if self._on_candle_close and len(candles) >= 2:
                closed = candles[-2]
                candle_data = {
                    "timestamp": datetime.fromtimestamp(
                        closed[0] / 1000, tz=timezone.utc
                    ),
                    "open": closed[1],
                    "high": closed[2],
                    "low": closed[3],
                    "close": closed[4],
                    "volume": closed[5],
                }
                try:
                    result = self._on_candle_close(symbol, candle_data)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    logger.exception(
                        "Error in _on_candle_close callback for %s", symbol
                    )

        except Exception:
            logger.exception("Failed to poll %s", symbol)
