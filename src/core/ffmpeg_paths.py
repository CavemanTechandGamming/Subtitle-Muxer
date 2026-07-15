"""
Ensure ffmpeg / ffprobe are available for this process.

Uses the ``static-ffmpeg`` package (installed into the virtualenv) which
downloads platform binaries on first use and prepends them to PATH.
A system-wide FFmpeg install still takes precedence when present.
"""

from __future__ import annotations

import shutil
from functools import lru_cache


class FFmpegBootstrapError(Exception):
    """Raised when bundled or system FFmpeg cannot be made available."""


@lru_cache(maxsize=1)
def ensure_ffmpeg_on_path() -> None:
    """
    Make ``ffmpeg`` and ``ffprobe`` resolvable via PATH.

    Prefer an existing system install; otherwise fetch/use static-ffmpeg.
    Safe to call multiple times.
    """
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return

    try:
        import static_ffmpeg
    except ImportError as exc:
        raise FFmpegBootstrapError(
            "FFmpeg is not on PATH and the 'static-ffmpeg' package is not installed. "
            "Run scripts\\setup_env.bat (or pip install -r requirements/requirements.txt)."
        ) from exc

    try:
        # weak=True: keep a real system FFmpeg if already present
        static_ffmpeg.add_paths(weak=True)
    except Exception as exc:  # noqa: BLE001 — surface download / platform errors clearly
        raise FFmpegBootstrapError(
            "Could not download or register bundled FFmpeg binaries. "
            f"Check your network connection and try again.\n\nDetails: {exc}"
        ) from exc

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise FFmpegBootstrapError(
            "Bundled FFmpeg was installed but ffmpeg/ffprobe are still not on PATH."
        )


def ffmpeg_binary() -> str:
    """Return the path/name of the ffmpeg executable."""
    ensure_ffmpeg_on_path()
    path = shutil.which("ffmpeg")
    if not path:
        raise FFmpegBootstrapError("ffmpeg binary not found after bootstrap.")
    return path


def ffprobe_binary() -> str:
    """Return the path/name of the ffprobe executable."""
    ensure_ffmpeg_on_path()
    path = shutil.which("ffprobe")
    if not path:
        raise FFmpegBootstrapError("ffprobe binary not found after bootstrap.")
    return path
