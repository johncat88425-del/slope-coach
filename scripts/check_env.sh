#!/usr/bin/env bash
# scripts/check_env.sh: Check required development tools on macOS

echo "=== Slope Coach Environment Check ==="

MISSING=0

# 1. git
if command -v git >/dev/null 2>&1; then
  echo "[OK] git: $(git --version)"
else
  echo "[FAIL] git is missing. Install with: xcode-select --install"
  MISSING=$((MISSING + 1))
fi

# 2. Python 3.11
if command -v python3.11 >/dev/null 2>&1; then
  echo "[OK] python3.11: $(python3.11 --version)"
elif command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 11) else 1)' 2>/dev/null; then
  echo "[OK] python3: $(python3 --version)"
else
  echo "[FAIL] Python 3.11 is missing (current default: $(python3 --version 2>&1 || echo 'none'))."
  echo "       Install with Homebrew: brew install python@3.11"
  MISSING=$((MISSING + 1))
fi

# 3. Node.js (Node 20+)
if command -v node >/dev/null 2>&1; then
  NODE_VER=$(node -v)
  echo "[OK] node: $NODE_VER"
else
  echo "[FAIL] node is missing."
  echo "       Install with Homebrew: brew install node@20"
  echo "       Or using nvm: nvm install 20 && nvm use 20"
  MISSING=$((MISSING + 1))
fi

# 4. ffmpeg / ffprobe
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  echo "[OK] ffmpeg & ffprobe: $(ffmpeg -version | head -n1)"
else
  echo "[FAIL] ffmpeg/ffprobe is missing."
  echo "       Install with Homebrew: brew install ffmpeg"
  MISSING=$((MISSING + 1))
fi

# 5. muse (Muse Code CLI)
if command -v muse >/dev/null 2>&1; then
  echo "[OK] muse CLI: $(muse --version 2>&1 || echo 'detected')"
else
  echo "[FAIL] muse CLI is missing."
  echo "       Install according to Meta Developer Hackathon instructions / Discord."
  MISSING=$((MISSING + 1))
fi

echo "======================================"
if [ "$MISSING" -eq 0 ]; then
  echo "All development dependencies are ready!"
else
  echo "There are $MISSING missing tools. Please install them before proceeding."
fi
exit "$MISSING"
