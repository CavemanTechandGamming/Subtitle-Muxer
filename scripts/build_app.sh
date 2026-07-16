#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# build_app.sh — versioned PyInstaller builds (Linux / macOS)
#
# Version comes from src/__init__.py (single source of truth).
#
# By default builds a single onefile binary — Linux/Mac only need one packaging
# style. Set SUBTITLE_MUXER_BUILD_KINDS=both to also build the onedir (installer)
# layout (mainly useful for local testing; CI does not publish that for Mac/Linux).
#
# Outputs (example):
#   dist/mac-apple-silicon/0.1.0/portable/SubtitleMuxer-0.1.0
#   dist/ubuntu/0.1.0/portable/SubtitleMuxer-0.1.0
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Embed icon assets so the packaged app can set a native window icon.
ICON_PNG="assets/subtitle-muxer-icon-steampunk.png"
ICON_PNG_256="assets/subtitle-muxer-icon-steampunk-256.png"
if [[ ! -f "$ICON_PNG" ]]; then
  echo "ERROR: Missing icon PNG: $ICON_PNG"
  exit 1
fi

# CI / local override for the platform folder label.
if [[ -n "${SUBTITLE_MUXER_PLATFORM:-}" ]]; then
  PLATFORM="$SUBTITLE_MUXER_PLATFORM"
else
  uname_s="$(uname -s | tr '[:upper:]' '[:lower:]')"
  case "$uname_s" in
    linux*)
      PLATFORM="linux"
      ;;
    darwin*)
      # Distinguish Apple Silicon vs Intel for artifact naming.
      machine="$(uname -m)"
      if [[ "$machine" == "arm64" ]]; then
        PLATFORM="mac-apple-silicon"
      else
        PLATFORM="mac-intel"
      fi
      ;;
    msys*|cygwin*|mingw*)
      PLATFORM="windows"
      ;;
    *)
      echo "ERROR: Unsupported OS: $(uname -s)"
      exit 1
      ;;
  esac
fi

# portable | installer | both  (default: portable only)
BUILD_KINDS="${SUBTITLE_MUXER_BUILD_KINDS:-portable}"

echo
echo "=== Subtitle Muxer — PyInstaller build (${PLATFORM}) ==="
echo "Working directory: $ROOT"
echo "Build kinds: ${BUILD_KINDS}"
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
echo

COMMON_ARGS=(
  --noconfirm
  --clean
  --windowed
  --name "$APP_NAME"
  --paths=.
  --add-data "${ICON_PNG}:."
  --collect-all customtkinter
  --collect-all tkinterdnd2
  --collect-all static_ffmpeg
  --hidden-import=tkinterdnd2
  --hidden-import=ffmpeg
  --hidden-import=static_ffmpeg
)
if [[ -f "$ICON_PNG_256" ]]; then
  COMMON_ARGS+=(--add-data "${ICON_PNG_256}:.")
fi

build_portable() {
  echo "Building portable (onefile) ..."
  rm -rf "dist/${PLATFORM}/${VERSION}/portable" "build/${PLATFORM}/${VERSION}/portable"
  mkdir -p "dist/${PLATFORM}/${VERSION}/portable" "build/${PLATFORM}/${VERSION}/portable"

  pyinstaller "${COMMON_ARGS[@]}" \
    --onefile \
    --distpath "dist/${PLATFORM}/${VERSION}/portable" \
    --workpath "build/${PLATFORM}/${VERSION}/portable" \
    --specpath "build/${PLATFORM}/${VERSION}/portable" \
    src/__main__.py

  echo "  -> dist/${PLATFORM}/${VERSION}/portable/${APP_NAME}"
}

build_installer() {
  echo "Building installer (onedir) ..."
  rm -rf "dist/${PLATFORM}/${VERSION}/installer" "build/${PLATFORM}/${VERSION}/installer"
  mkdir -p "dist/${PLATFORM}/${VERSION}/installer" "build/${PLATFORM}/${VERSION}/installer"

  pyinstaller "${COMMON_ARGS[@]}" \
    --onedir \
    --distpath "dist/${PLATFORM}/${VERSION}/installer" \
    --workpath "build/${PLATFORM}/${VERSION}/installer" \
    --specpath "build/${PLATFORM}/${VERSION}/installer" \
    src/__main__.py

  echo "  -> dist/${PLATFORM}/${VERSION}/installer/${APP_NAME}/"
}

case "$BUILD_KINDS" in
  portable)
    build_portable
    ;;
  installer)
    build_installer
    ;;
  both)
    build_portable
    build_installer
    ;;
  *)
    echo "ERROR: SUBTITLE_MUXER_BUILD_KINDS must be portable, installer, or both (got: ${BUILD_KINDS})"
    exit 1
    ;;
esac

echo
echo "Build complete."
echo
