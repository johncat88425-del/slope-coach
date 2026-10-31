#!/usr/bin/env bash
# Start the backend (port 8000) and the frontend dev server (port 5173). No sudo needed.
# Without MODEL_API_KEY in .env the backend uses mock model hooks and model-free tracking.
set -euo pipefail
cd "$(dirname "$0")/.."
missing=()
command -v ffmpeg >/dev/null || missing+=("ffmpeg (brew install ffmpeg)")
PY=$(command -v python3.11 || command -v python3 || true)  # README pins 3.11; newer system pythons can fail to build the venv
[ -n "$PY" ] || missing+=("python 3.11 (brew install python@3.11)")
command -v npm >/dev/null || missing+=("node + npm (brew install node)")
if [ ${#missing[@]} -gt 0 ]; then printf 'Missing: %s\n' "${missing[@]}"; exit 1; fi
[ -d .venv ] || "$PY" -m venv .venv
.venv/bin/pip install -q -r requirements.txt
[ -d frontend/node_modules ] || (cd frontend && npm install)
if [ -f .env ]; then set -a; . ./.env; set +a; fi  # the key stays in .env; never echo it
.venv/bin/uvicorn backend.main:app --port 8000 &
trap 'kill $! 2>/dev/null' EXIT
cd frontend && npm run dev
