#!/usr/bin/env python3
"""
Subtitle Muxer — package entry point.

Usage (from repository root):
    python -m src
"""

from src.core.ffmpeg_paths import FFmpegBootstrapError, ensure_ffmpeg_on_path
from src.ui.app import run_app


def main() -> None:
    # Put venv-bundled ffmpeg/ffprobe on PATH before any probing/muxing.
    try:
        ensure_ffmpeg_on_path()
    except FFmpegBootstrapError as exc:
        # Still launch the UI so the user can see a clear error dialog/log.
        print(f"Warning: {exc}")
    run_app()


if __name__ == "__main__":
    main()
