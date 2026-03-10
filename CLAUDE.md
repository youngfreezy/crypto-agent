# Crypto Trading Agent - Claude Code Instructions

## Project Architecture
- **Backend**: FastAPI + ccxt (Python), venv at `backend/venv/`
- **Frontend**: Next.js 14 App Router + Tailwind + shadcn/ui (port 3000)
- **Backend port**: 8000
- **Docker Compose**: Postgres (5433)
- **Start everything**: `npm start` from root (Docker, backend, frontend)

## Code Standards
- Simplicity first. Minimal code impact.
- No over-engineering. Only make changes that are directly requested.
- Never silently fall back to mock data when a real service fails. Fail loudly.
- Every route needs a `loading.tsx` with animate-pulse skeleton
- Root layout must have `nextjs-toploader` for route transitions

## Git
- Never include `Co-Authored-By` or AI attribution in commit messages
- Never skip hooks (--no-verify) unless explicitly asked
