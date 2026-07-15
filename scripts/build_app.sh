#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# build_app.sh — PyInstaller onefile + onedir builds (Linux / macOS)
# Outputs:
#   dist/<platform>/onefile/SubtitleMuxer
#   dist/<platform>/onedir/SubtitleMuxer/...
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

APP_NAME="SubtitleMuxer"

uname_s="$(uname -s | tr '[:upper:]' '[:lower:]')"
case "$uname_s" in
  linux*)  PLATFORM="linux" ;;
  darwin*) PLATFORM="macos" ;;
  msys*|cygwin*|mingw*) PLATFORM="windows" ;;
  *)
    echo "ERROR: Unsupported OS: $(uname -s)"
    exit 1
    ;;
esac

echo
echo "=== Subtitle Muxer — PyInstaller build (${PLATFORM}) ==="
echo "Working directory: $ROOT"
echo

if [[ ! -x .venv/bin/python ]]; then
  echo "Virtual environment not found. Running setup_env.sh ..."
  bash scripts/setup_env.sh
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "ERROR: pyinstaller not found in the virtual environment."
  echo "Run scripts/setup_env.sh first."
  exit 1
fi

# Shared flags for CustomTkinter + tkinterdnd2 + static-ffmpeg
# --paths=. keeps ``import src...`` working when the entry script lives under src/
COMMON_ARGS=(
  --noconfirm
  --clean
  --windowed
  --name "$APP_NAME"
  --paths=.
  --collect-all customtkinter
  --collect-all tkinterdnd2
  --collect-all static_ffmpeg
  --hidden-import=tkinterdnd2
  --hidden-import=ffmpeg
  --hidden-import=static_ffmpeg
)

echo "[1/2] Building --onefile (portable) ..."
rm -rf "dist/${PLATFORM}/onefile" "build/${PLATFORM}/onefile"
mkdir -p "dist/${PLATFORM}/onefile" "build/${PLATFORM}/onefile"

pyinstaller "${COMMON_ARGS[@]}" \
  --onefile \
  --distpath "dist/${PLATFORM}/onefile" \
  --workpath "build/${PLATFORM}/onefile" \
  --specpath "build/${PLATFORM}/onefile" \
  src/__main__.py

echo "[2/2] Building --onedir (installable structure) ..."
rm -rf "dist/${PLATFORM}/onedir" "build/${PLATFORM}/onedir"
mkdir -p "dist/${PLATFORM}/onedir" "build/${PLATFORM}/onedir"

pyinstaller "${COMMON_ARGS[@]}" \
  --onedir \
  --distpath "dist/${PLATFORM}/onedir" \
  --workpath "build/${PLATFORM}/onedir" \
  --specpath "build/${PLATFORM}/onedir" \
  src/__main__.py

echo
echo "Build complete:"
echo "  Portable : dist/${PLATFORM}/onefile/${APP_NAME}"
echo "  Onedir   : dist/${PLATFORM}/onedir/${APP_NAME}/"
echo
