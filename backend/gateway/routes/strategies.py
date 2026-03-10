"""Strategy endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["strategies"])


class SymbolRequest(BaseModel):
    symbol: str


@router.get("/strategies")
async def list_strategies():
    from backend.strategies.registry import list_strategies, get_active

    strategies = list_strategies()
    active = get_active()
    return [
        {**s, "active_symbols": active.get(s["name"], [])}
        for s in strategies
    ]


@router.post("/strategies/{name}/activate")
async def activate_strategy(name: str, req: SymbolRequest):
    from backend.strategies.registry import activate

    activate(name, req.symbol)
    return {"status": "activated", "strategy": name, "symbol": req.symbol}


@router.post("/strategies/{name}/deactivate")
async def deactivate_strategy(name: str, req: SymbolRequest):
    from backend.strategies.registry import deactivate

    deactivate(name, req.symbol)
    return {"status": "deactivated", "strategy": name, "symbol": req.symbol}
