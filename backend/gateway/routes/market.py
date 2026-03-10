"""Market data endpoints."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api", tags=["market"])


@router.get("/market/prices")
async def get_prices(request: Request):
    market_feed = request.app.state.market_feed
    return market_feed.get_all_prices()


@router.get("/market/candles")
async def get_candles(
    symbol: str = "BTC/USDT",
    timeframe: str = "1m",
    limit: int = 200,
):
    from backend.market.candle_store import get_candles as fetch_candles

    return fetch_candles(symbol, timeframe, limit=limit)
