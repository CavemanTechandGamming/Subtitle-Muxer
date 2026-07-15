#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# setup_env.sh — create/refresh the local virtual environment (Linux / macOS)
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo
echo "=== Subtitle Muxer — environment setup (Unix) ==="
echo "Working directory: $ROOT"
echo

if command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON=python
else
  echo "ERROR: Python 3 was not found on PATH."
  exit 1
fi

echo "[1/4] Creating virtual environment at .venv ..."
"$PYTHON" -m venv .venv

# Prefer the venv interpreter directly (more reliable than activate in CI).
VENV_PY="$ROOT/.venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  echo "ERROR: venv python was not created at $VENV_PY"
  exit 1
fi

echo "[2/4] Upgrading pip ..."
"$VENV_PY" -m pip install --upgrade pip

echo "[3/4] Installing dependencies from requirements/requirements.txt ..."
"$VENV_PY" -m pip install -r requirements/requirements.txt

echo "[4/4] Downloading bundled FFmpeg into the virtualenv (first run may take a bit) ..."
"$VENV_PY" -c "from src.core.ffmpeg_paths import ensure_ffmpeg_on_path, ffmpeg_binary, ffprobe_binary; ensure_ffmpeg_on_path(); print('ffmpeg :', ffmpeg_binary()); print('ffprobe:', ffprobe_binary())"

echo
echo "Setup complete. Activate later with:"
echo "  source .venv/bin/activate"
echo
