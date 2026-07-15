#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# build_app.sh — versioned portable + installable PyInstaller builds
# Version comes from src/__init__.py (single source of truth).
# Outputs (example for 1.0.0):
#   dist/<platform>/1.0.0/portable/SubtitleMuxer-1.0.0
#   dist/<platform>/1.0.0/installable/SubtitleMuxer-1.0.0/...
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# CI can force a distro label (ubuntu/debian/mint/fedora/arch) via env.
if [[ -n "${SUBTITLE_MUXER_PLATFORM:-}" ]]; then
  PLATFORM="$SUBTITLE_MUXER_PLATFORM"
else
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
fi

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

VERSION="$(python scripts/read_version.py)"
APP_NAME="SubtitleMuxer-${VERSION}"
echo "App version: ${VERSION}"
echo "Artifact names: subtitle-muxer-${PLATFORM}-${VERSION}-portable / installable"
echo

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

echo "[1/2] Building portable (onefile) ..."
rm -rf "dist/${PLATFORM}/${VERSION}/portable" "build/${PLATFORM}/${VERSION}/portable"
mkdir -p "dist/${PLATFORM}/${VERSION}/portable" "build/${PLATFORM}/${VERSION}/portable"

pyinstaller "${COMMON_ARGS[@]}" \
  --onefile \
  --distpath "dist/${PLATFORM}/${VERSION}/portable" \
  --workpath "build/${PLATFORM}/${VERSION}/portable" \
  --specpath "build/${PLATFORM}/${VERSION}/portable" \
  src/__main__.py

echo "[2/2] Building installable (onedir) ..."
rm -rf "dist/${PLATFORM}/${VERSION}/installable" "build/${PLATFORM}/${VERSION}/installable"
mkdir -p "dist/${PLATFORM}/${VERSION}/installable" "build/${PLATFORM}/${VERSION}/installable"

pyinstaller "${COMMON_ARGS[@]}" \
  --onedir \
  --distpath "dist/${PLATFORM}/${VERSION}/installable" \
  --workpath "build/${PLATFORM}/${VERSION}/installable" \
  --specpath "build/${PLATFORM}/${VERSION}/installable" \
  src/__main__.py

echo
echo "Build complete:"
echo "  Portable    : dist/${PLATFORM}/${VERSION}/portable/${APP_NAME}"
echo "  Installable : dist/${PLATFORM}/${VERSION}/installable/${APP_NAME}/"
echo
