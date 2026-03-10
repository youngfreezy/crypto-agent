"""Candle persistence layer."""

from datetime import datetime, timezone

from backend.shared.db import get_connection


def insert_candles(symbol: str, timeframe: str, candles: list[list]) -> None:
    """Bulk upsert OHLCV candle rows.

    Each candle is [timestamp_ms, open, high, low, close, volume] (ccxt format).
    """
    if not candles:
        return

    rows = [
        (
            symbol,
            timeframe,
            datetime.fromtimestamp(c[0] / 1000, tz=timezone.utc),
            c[1],  # open
            c[2],  # high
            c[3],  # low
            c[4],  # close
            c[5],  # volume
        )
        for c in candles
    ]

    sql = """
        INSERT INTO candles (symbol, timeframe, timestamp, open, high, low, close, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (symbol, timeframe, timestamp)
        DO UPDATE SET
            open   = EXCLUDED.open,
            high   = EXCLUDED.high,
            low    = EXCLUDED.low,
            close  = EXCLUDED.close,
            volume = EXCLUDED.volume
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, rows)
        conn.commit()


def get_candles(symbol: str, timeframe: str, limit: int = 200) -> list[dict]:
    """Query the most recent candles, returned oldest-first as list of dicts."""
    sql = """
        SELECT timestamp, open, high, low, close, volume
        FROM candles
        WHERE symbol = %s AND timeframe = %s
        ORDER BY timestamp DESC
        LIMIT %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (symbol, timeframe, limit))
            rows = cur.fetchall()

    # Reverse so oldest is first (chronological order)
    return [
        {
            "timestamp": row[0],
            "open": row[1],
            "high": row[2],
            "low": row[3],
            "close": row[4],
            "volume": row[5],
        }
        for row in reversed(rows)
    ]
