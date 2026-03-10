"""Database table definitions and initialization."""

import logging

logger = logging.getLogger(__name__)


def ensure_tables(conn) -> None:
    """Create all tables if they don't already exist."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS candles (
                id          BIGSERIAL PRIMARY KEY,
                symbol      TEXT NOT NULL,
                timeframe   TEXT NOT NULL,
                timestamp   TIMESTAMPTZ NOT NULL,
                open        DOUBLE PRECISION NOT NULL,
                high        DOUBLE PRECISION NOT NULL,
                low         DOUBLE PRECISION NOT NULL,
                close       DOUBLE PRECISION NOT NULL,
                volume      DOUBLE PRECISION NOT NULL,
                created_at  TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (symbol, timeframe, timestamp)
            );

            CREATE INDEX IF NOT EXISTS idx_candles_symbol_tf_ts
                ON candles (symbol, timeframe, timestamp DESC);

            CREATE TABLE IF NOT EXISTS trades (
                id              BIGSERIAL PRIMARY KEY,
                symbol          TEXT NOT NULL,
                side            TEXT NOT NULL,
                quantity        DOUBLE PRECISION NOT NULL,
                fill_price      DOUBLE PRECISION NOT NULL,
                fee             DOUBLE PRECISION DEFAULT 0,
                strategy_name   TEXT,
                signal_strength DOUBLE PRECISION,
                pnl             DOUBLE PRECISION,
                created_at      TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_trades_symbol_created
                ON trades (symbol, created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_trades_strategy_created
                ON trades (strategy_name, created_at DESC);

            CREATE TABLE IF NOT EXISTS positions (
                id          BIGSERIAL PRIMARY KEY,
                symbol      TEXT UNIQUE NOT NULL,
                quantity    DOUBLE PRECISION DEFAULT 0,
                avg_entry   DOUBLE PRECISION DEFAULT 0,
                updated_at  TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id              BIGSERIAL PRIMARY KEY,
                total_value     DOUBLE PRECISION NOT NULL,
                cash_balance    DOUBLE PRECISION NOT NULL,
                positions_value DOUBLE PRECISION NOT NULL,
                unrealized_pnl  DOUBLE PRECISION NOT NULL,
                realized_pnl    DOUBLE PRECISION NOT NULL,
                created_at      TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_snapshots_created
                ON portfolio_snapshots (created_at DESC);

            CREATE TABLE IF NOT EXISTS account (
                id              INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
                cash            DOUBLE PRECISION NOT NULL,
                initial_capital DOUBLE PRECISION NOT NULL,
                created_at      TIMESTAMPTZ DEFAULT NOW(),
                updated_at      TIMESTAMPTZ DEFAULT NOW()
            );
        """)
    logger.info("All tables ensured.")


def init_account(conn, initial_capital: float) -> None:
    """Insert the singleton account row if it doesn't already exist."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO account (id, cash, initial_capital)
            VALUES (1, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (initial_capital, initial_capital),
        )
    logger.info("Account initialized with capital=%.2f", initial_capital)
