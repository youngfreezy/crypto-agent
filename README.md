# Crypto Trading Agent

Autonomous AI-powered crypto trading agent. Claude analyzes live market data, reasons about price action and technical indicators, and makes paper trading decisions with no human in the loop.

## How It Works

1. **Market Feed** pulls live OHLCV candles from Kraken every 10 seconds via ccxt
2. **AI Agent** (Claude Haiku) analyzes price action, technical indicators, portfolio state, and its own trade history — then decides to buy, sell, or hold
3. **Rule-Based Strategies** (SMA Crossover, RSI) run alongside the AI agent as pluggable alternatives
4. **Paper Trader** simulates order execution with realistic slippage (0.05%) and fees (0.1%)
5. **Dashboard** shows portfolio, AI reasoning timeline, trades, charts, and strategy performance

## Architecture

```
┌──────────────────────────────────────────────────┐
│  Next.js Dashboard (localhost:3000)              │
│  Dashboard · AI Agent · Portfolio · Trades       │
│  Strategies · Market                             │
└───────────────────┬──────────────────────────────┘
                    │ REST API
┌───────────────────▼──────────────────────────────┐
│  FastAPI Backend (localhost:8000)                 │
│                                                  │
│  ┌──────────┐  ┌─────────────┐  ┌────────────┐  │
│  │ Market   │→ │ Claude AI   │→ │ Paper      │  │
│  │ Feed     │  │ Strategy    │  │ Trader     │  │
│  │ (ccxt)   │  │ (reasoning) │  │ (sim)      │  │
│  └──────────┘  └─────────────┘  └────────────┘  │
│                ┌─────────────┐                   │
│                │ SMA / RSI   │                   │
│                │ (rule-based)│                   │
│                └─────────────┘                   │
│  ┌──────────────────────────────────────────┐    │
│  │ Postgres (candles, trades, ai_analyses)  │    │
│  └──────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

## The AI Agent

The `claude_ai` strategy is an autonomous trading agent that:

- **Reasons** about market conditions using price action, SMA/RSI indicators, volume, and cross-symbol context
- **Adapts** by reviewing its own trade history and P&L before making new decisions
- **Explains** every decision with 2-3 sentence reasoning, persisted to the database and shown in the dashboard
- **Manages risk** conservatively — most of the time it holds, only trading when multiple signals align

Every 5 minutes (configurable), Claude receives:
- Last 60 candles of price action
- Pre-computed SMA(10), SMA(50), RSI(14)
- Current portfolio state and positions
- Its own recent trade history
- Prices across all symbols

And returns: `{"action": "buy|sell|hold", "strength": 0.7, "reasoning": "..."}`

**Cost**: ~$1-2/day on Claude Haiku 4.5 with 5-minute intervals.

## Quick Start

```bash
# Clone
git clone https://github.com/youngfreezy/crypto-agent.git
cd crypto-agent

# Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env for AI agent (optional)

# Install backend
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt && cd ..

# Install frontend
cd frontend && npm install && cd ..

# Start everything (Docker + backend + frontend)
npm start
```

Open http://localhost:3000 to see the dashboard.

To activate the AI agent:
```bash
# Activate on all symbols
curl -X POST http://localhost:8000/api/strategies/claude_ai/activate \
  -H 'Content-Type: application/json' -d '{"symbol": "BTC/USDT"}'
```

## Strategies

| Strategy | Logic | Config |
|----------|-------|--------|
| **Claude AI** | Autonomous reasoning — analyzes indicators, portfolio, trade history | 5-min interval |
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

- **Backend**: FastAPI, ccxt, psycopg, numpy, Anthropic SDK
- **Frontend**: Next.js 14, TradingView lightweight-charts, shadcn/ui, Tailwind CSS
- **AI**: Claude Haiku 4.5 (Anthropic API)
- **Database**: PostgreSQL 16
- **Infra**: Docker Compose

## API

```
GET  /api/health                     - Health check
GET  /api/portfolio                  - Current portfolio state
GET  /api/trades                     - Trade history
GET  /api/strategies                 - Active strategies
GET  /api/market/:symbol             - OHLCV candles for a symbol
GET  /api/ai-analyses                - AI decision history
GET  /api/ai-analyses/latest         - Latest AI analysis per symbol
POST /api/trades                     - Execute a manual trade
POST /api/strategies/:name/activate  - Activate a strategy on a symbol
```

## Roadmap

- [x] **Phase 1: Infrastructure** — Live data, paper execution, rule-based strategies, dashboard
- [x] **Phase 2: AI Agent** — Claude-powered autonomous market analysis and trading
- [ ] **Phase 3: Multi-Agent** — Separate agents for research, risk assessment, and execution
- [ ] **Phase 4: Live Trading** — Graduate from paper to real orders on Kraken

## License

MIT
