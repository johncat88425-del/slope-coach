#!/usr/bin/env bash
# scripts/dev.sh: Start backend and frontend simultaneously

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# 1. Load .env if present
if [ -f ".env" ]; then
  echo "[dev.sh] Loading .env configuration..."
  set -a
  source .env
  set +a
fi

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# 2. Check Python environment
PYTHON_BIN="python3"
if [ -f ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
elif [ -f "venv/bin/python" ]; then
  PYTHON_BIN="venv/bin/python"
elif command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
fi

echo "[dev.sh] Using Python: $($PYTHON_BIN --version 2>&1 || echo 'unknown')"

# 3. Clean shutdown handler
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "[dev.sh] Shutting down services..."
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "[dev.sh] Stopping backend (PID $BACKEND_PID)..."
    kill -TERM "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo "[dev.sh] Stopping frontend (PID $FRONTEND_PID)..."
    kill -TERM "$FRONTEND_PID" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
  echo "[dev.sh] All services stopped."
  exit 0
}

trap cleanup INT TERM EXIT

# 4. Start backend
echo "[dev.sh] Starting backend on http://localhost:${BACKEND_PORT}..."
if [ -d "backend" ]; then
  $PYTHON_BIN -m uvicorn backend.main:app --reload --port "$BACKEND_PORT" &
  BACKEND_PID=$!
else
  echo "[dev.sh] Notice: backend/ directory not found. Waiting..."
fi

# 5. Start frontend
echo "[dev.sh] Starting frontend on http://localhost:${FRONTEND_PORT}..."
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
  (cd frontend && npm run dev -- --port "$FRONTEND_PORT") &
  FRONTEND_PID=$!
else
  echo "[dev.sh] Notice: frontend/package.json not found. Waiting..."
fi

echo "[dev.sh] Slope Coach development environment is up. Press Ctrl+C to stop."

# Wait indefinitely for processes
wait
