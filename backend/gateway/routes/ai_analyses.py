"""AI analysis endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from backend.shared.db import get_connection

router = APIRouter(prefix="/api", tags=["ai"])


@router.get("/ai-analyses")
async def get_ai_analyses(
    symbol: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """Get paginated AI analysis history."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            if symbol:
                cur.execute(
                    "SELECT id, symbol, action, strength, reasoning, indicators, "
                    "model, input_tokens, output_tokens, latency_ms, created_at "
                    "FROM ai_analyses WHERE symbol = %s "
                    "ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    (symbol, limit, offset),
                )
            else:
                cur.execute(
                    "SELECT id, symbol, action, strength, reasoning, indicators, "
                    "model, input_tokens, output_tokens, latency_ms, created_at "
                    "FROM ai_analyses "
                    "ORDER BY created_at DESC LIMIT %s OFFSET %s",
                    (limit, offset),
                )
            rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "symbol": r[1],
            "action": r[2],
            "strength": r[3],
            "reasoning": r[4],
            "indicators": r[5],
            "model": r[6],
            "input_tokens": r[7],
            "output_tokens": r[8],
            "latency_ms": r[9],
            "created_at": r[10].isoformat() if r[10] else None,
        }
        for r in rows
    ]


@router.get("/ai-analyses/latest")
async def get_latest_analyses():
    """Get the most recent analysis per symbol."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT ON (symbol) "
                "id, symbol, action, strength, reasoning, indicators, "
                "model, input_tokens, output_tokens, latency_ms, created_at "
                "FROM ai_analyses ORDER BY symbol, created_at DESC"
            )
            rows = cur.fetchall()

    return [
        {
            "id": r[0],
            "symbol": r[1],
            "action": r[2],
            "strength": r[3],
            "reasoning": r[4],
            "indicators": r[5],
            "model": r[6],
            "input_tokens": r[7],
            "output_tokens": r[8],
            "latency_ms": r[9],
            "created_at": r[10].isoformat() if r[10] else None,
        }
        for r in rows
    ]
