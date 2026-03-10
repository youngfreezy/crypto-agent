"""Portfolio endpoints."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api", tags=["portfolio"])


@router.get("/portfolio")
async def get_portfolio(request: Request):
    market_feed = request.app.state.market_feed
    prices = market_feed.get_all_prices()

    from backend.engine.portfolio import get_portfolio
    return get_portfolio(prices)


@router.get("/portfolio/history")
async def get_portfolio_history(limit: int = 500):
    from backend.engine.portfolio import get_snapshots
    return get_snapshots(limit=limit)
