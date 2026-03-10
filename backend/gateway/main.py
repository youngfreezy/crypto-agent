"""FastAPI gateway for the Crypto Trading Agent.

Provides the REST API that the Next.js frontend consumes.
Manages the market feed lifecycle and paper trading engine.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
_log_fmt = logging.Formatter("%(levelname)s %(name)s: %(message)s")
_console = logging.StreamHandler()
_console.setFormatter(_log_fmt)
_handlers: list[logging.Handler] = [_console]
if os.environ.get("LOG_TO_FILE", "true").lower() == "true":
    _file = logging.FileHandler("backend.log", mode="a")
    _file.setFormatter(_log_fmt)
    _handlers.append(_file)
logging.basicConfig(level=logging.INFO, handlers=_handlers)
for _noisy in ("httpcore", "httpx", "urllib3", "watchfiles", "asyncio"):
    logging.getLogger(_noisy).setLevel(logging.ERROR)

from backend.shared.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    settings = get_settings()
    logger.info("Starting Crypto Agent gateway (log_level=%s)", settings.LOG_LEVEL)

    # --- Ensure DB tables exist ---
    from backend.shared.tables import ensure_tables, init_account
    from backend.shared.db import get_connection

    with get_connection() as conn:
        ensure_tables(conn)
        init_account(conn, settings.INITIAL_CAPITAL)
        conn.commit()
    logger.info("Database tables ready")

    # --- Start market feed ---
    from backend.market.feed import MarketFeed

    market_feed = MarketFeed()

    # --- Set up paper trader ---
    from backend.engine.paper_trader import PaperTrader

    paper_trader = PaperTrader(get_price_fn=market_feed.get_latest_price)

    # --- Wire strategy evaluation on candle close ---
    from backend.strategies.registry import get_active, get_strategy
    from backend.market.candle_store import get_candles

    def on_candle_close(symbol: str, candle: list):
        """Called when a new candle closes — evaluate active strategies."""
        active = get_active()
        for strategy_name, symbols in active.items():
            if symbol not in symbols:
                continue
            try:
                strategy = get_strategy(strategy_name)
                needed = strategy.required_candles()
                candles = get_candles(symbol, settings.CANDLE_TIMEFRAME, limit=needed)
                if len(candles) < needed:
                    continue
                signal = strategy.evaluate(symbol, candles)
                if signal and signal.action != "hold":
                    paper_trader.process_signal(signal)
                    logger.info(
                        "Strategy %s → %s %s (strength=%.3f)",
                        strategy_name, signal.action.upper(), symbol, signal.strength,
                    )
            except Exception:
                logger.exception("Strategy %s error on %s", strategy_name, symbol)

    market_feed._on_candle_close = on_candle_close

    # --- Start portfolio snapshots task ---
    import asyncio

    async def snapshot_loop():
        from backend.engine.portfolio import take_snapshot
        while True:
            await asyncio.sleep(300)  # every 5 minutes
            try:
                prices = market_feed.get_all_prices()
                if prices:
                    take_snapshot(prices)
                    logger.debug("Portfolio snapshot taken")
            except Exception:
                logger.exception("Snapshot error")

    snapshot_task = asyncio.create_task(snapshot_loop())

    # Start market feed
    await market_feed.start()
    logger.info("Market feed started")

    # Attach to app.state
    app.state.market_feed = market_feed
    app.state.paper_trader = paper_trader
    app.state.settings = settings

    yield

    # --- Shutdown ---
    logger.info("Shutting down Crypto Agent gateway")
    snapshot_task.cancel()
    await market_feed.stop()

    from backend.shared.db import close_pool
    close_pool()


_app_ref: FastAPI | None = None


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Crypto Trading Agent API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # --- CORS ---
    _origins = [
        "http://localhost:3000",
        "https://localhost:3000",
    ]
    _extra_origins = os.environ.get("CORS_ORIGINS", "")
    if _extra_origins:
        _origins.extend(o.strip() for o in _extra_origins.split(",") if o.strip())

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routes ---
    from backend.gateway.routes.health import router as health_router
    from backend.gateway.routes.portfolio import router as portfolio_router
    from backend.gateway.routes.trades import router as trades_router
    from backend.gateway.routes.strategies import router as strategies_router
    from backend.gateway.routes.market import router as market_router
    from backend.gateway.routes.ai_analyses import router as ai_analyses_router

    app.include_router(health_router)
    app.include_router(portfolio_router)
    app.include_router(trades_router)
    app.include_router(strategies_router)
    app.include_router(market_router)
    app.include_router(ai_analyses_router)

    return app


app = create_app()
_app_ref = app
