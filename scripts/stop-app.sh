#!/usr/bin/env bash
# Stop all crypto-agent services

DIR="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME="$DIR/.runtime"

echo "Stopping crypto-agent services..."

# Kill launcher
if [ -f "$RUNTIME/launcher.pid" ]; then
  kill "$(cat "$RUNTIME/launcher.pid")" 2>/dev/null
  rm -f "$RUNTIME/launcher.pid"
fi

# Kill backend
if [ -f "$RUNTIME/backend.pid" ]; then
  kill "$(cat "$RUNTIME/backend.pid")" 2>/dev/null
  rm -f "$RUNTIME/backend.pid"
fi

# Kill frontend
if [ -f "$RUNTIME/frontend.pid" ]; then
  kill "$(cat "$RUNTIME/frontend.pid")" 2>/dev/null
  rm -f "$RUNTIME/frontend.pid"
fi

# Stop Docker containers
docker compose -f "$DIR/docker-compose.yml" down 2>/dev/null

echo "All services stopped."
