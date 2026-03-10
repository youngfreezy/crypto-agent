# Crypto Trading Agent

Paper trading platform with live market data, pluggable strategies, and a real-time dashboard. Built as the foundation for an autonomous AI-powered trading agent.

## Status

**Phase 1 (current)**: Trading infrastructure — live data, paper execution, rule-based strategies, dashboard. No AI yet.

**Phase 2 (next)**: The "agent" part — Claude analyzes market conditions, adapts strategy selection, and makes autonomous decisions with no human in the loop.

## How It Works

1. **Market Feed** pulls live OHLCV candles from Kraken every 10 seconds via ccxt
2. **Strategy Engine** evaluates pluggable rule-based strategies (SMA Crossover, RSI) on each candle close
3. **Paper Trader** simulates order execution with realistic slippage (0.05%) and fees (0.1%)
4. **Risk Engine** enforces position limits (max 20%, 5% allocation per trade)
5. **Dashboard** shows portfolio, trades, candlestick charts, and strategy performance in real time

## Architecture

```
┌─────────────────────────────────────────────┐
│  Next.js Dashboard (localhost:3000)          │
│  Portfolio · Trades · Charts · Strategies    │
└──────────────────┬──────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────┐
│  FastAPI Backend (localhost:8000)            │
│                                             │
│  ┌───────────┐  ┌───────────┐  ┌─────────┐ │
│  │ Market    │→ │ Strategy  │→ │ Paper   │ │
│  │ Feed      │  │ Engine    │  │ Trader  │ │
│  │ (ccxt)    │  │ (SMA/RSI) │  │ (sim)   │ │
│  └───────────┘  └───────────┘  └─────────┘ │
│                                             │
│  ┌─────────────────────────────────────────┐│
│  │ Postgres (candles, trades, positions)   ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

## Quick Start

```bash
# Clone
git clone https://github.com/youngfreezy/crypto-agent.git
cd crypto-agent

# Configure
cp .env.example .env
# Edit .env if needed (defaults work for local dev)

# Install backend
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && cd ..

# Install frontend
cd frontend && npm install && cd ..

# Start everything (Docker + backend + frontend)
npm start
```

Open http://localhost:3000 to see the dashboard.

## Strategies

| Strategy | Logic | Default Config |
|----------|-------|----------------|
| SMA Crossover | Buy when fast SMA crosses above slow SMA, sell on cross below | 10/50 periods |
| RSI | Buy when RSI < 30 (oversold), sell when RSI > 70 (overbought) | 14 periods |

Strategies are pluggable — add a new one by extending `Strategy` in `backend/strategies/base.py`.

## Paper Trading

- **Starting capital**: $100,000 USDT
- **Slippage**: 0.05% simulated
- **Fees**: 0.1% per trade
- **Position sizing**: 5% of portfolio per trade
- **Symbols**: BTC/USDT, ETH/USDT, SOL/USDT

## Tech Stack

- **Backend**: FastAPI, ccxt, psycopg, numpy
- **Frontend**: Next.js 14, TradingView lightweight-charts, shadcn/ui, Tailwind CSS
- **Database**: PostgreSQL 16
- **Infra**: Docker Compose

## API

```
GET  /api/health              - Health check
GET  /api/portfolio            - Current portfolio state
GET  /api/trades               - Trade history
GET  /api/strategies           - Active strategies
GET  /api/market/:symbol       - OHLCV candles for a symbol
POST /api/trades               - Execute a manual trade
POST /api/strategies/:name     - Toggle a strategy on/off
```

## Roadmap

- [ ] **Phase 2: AI Agent** — Claude-powered market analysis, adaptive strategy selection, autonomous trading decisions
- [ ] **Phase 3: Multi-Agent** — Separate agents for research, risk assessment, and execution
- [ ] **Phase 4: Live Trading** — Graduate from paper to real orders on Kraken

## License

MIT
