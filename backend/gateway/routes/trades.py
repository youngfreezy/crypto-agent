"""Trade endpoints."""

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["trades"])


class TradeRequest(BaseModel):
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float


@router.post("/trades")
async def create_trade(req: TradeRequest, request: Request):
    from backend.engine.order_book import Order

    paper_trader = request.app.state.paper_trader
    order = Order(
        symbol=req.symbol,
        side=req.side,
        order_type="market",
        quantity=req.quantity,
    )
    trade = paper_trader.execute_order(order)
    return {
        "symbol": trade.symbol,
        "side": trade.side,
        "quantity": trade.quantity,
        "fill_price": trade.fill_price,
        "fee": trade.fee,
        "pnl": trade.pnl,
        "created_at": trade.created_at.isoformat(),
    }


@router.get("/trades")
async def get_trades(
    limit: int = 50,
    offset: int = 0,
    symbol: Optional[str] = None,
    strategy: Optional[str] = None,
    request: Request = None,
):
    paper_trader = request.app.state.paper_trader
    return paper_trader.get_trade_history(
        limit=limit, offset=offset, symbol=symbol, strategy=strategy
    )


@router.get("/trades/stats")
async def get_trade_stats(request: Request):
    paper_trader = request.app.state.paper_trader
    return paper_trader.get_trade_stats()
