"""
Mux subtitle streams from a source video onto a target video via FFmpeg stream copy.

Command shape (zero-loss copy):
  ffmpeg -y -i [target] -i [source]
         -map 0:v -map 0:a
         -map 1:s:N ...
         -c copy
         [output]
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from src.core.ffmpeg_paths import FFmpegBootstrapError, ffmpeg_binary


class MuxerError(Exception):
    """Raised when FFmpeg cannot mux the selected streams."""


@dataclass(frozen=True)
class MuxOptions:
    """Parameters for a single mux job."""

    target: Path
    source: Path
    output: Path
    # Subtitle-relative indices (for -map 1:s:N). Empty / None => map all (1:s).
    subtitle_indices: Sequence[int] | None = None
    # Container hint; used only for validation / default extension.
    container: str = "mkv"  # "mkv" | "mp4"


LogCallback = Callable[[str], None]


def _require_ffmpeg() -> str:
    """Return the ffmpeg binary path or raise MuxerError."""
    try:
        return ffmpeg_binary()
    except FFmpegBootstrapError as exc:
        raise MuxerError(str(exc)) from exc


def build_ffmpeg_command(options: MuxOptions) -> list[str]:
    """
    Build the argv list for FFmpeg.

    Input 0 = target (video + audio kept)
    Input 1 = source (selected subtitle tracks mapped)
    """
    ffmpeg_bin = _require_ffmpeg()

    cmd: list[str] = [
        ffmpeg_bin,
        "-hide_banner",
        "-y",
        "-i",
        str(options.target),
        "-i",
        str(options.source),
        "-map",
        "0:v",
        "-map",
        "0:a?",  # optional: target may lack audio
    ]

    # None => map every subtitle stream; explicit list => map those indices only
    if options.subtitle_indices is None:
        cmd.extend(["-map", "1:s"])
    else:
        indices = list(options.subtitle_indices)
        if not indices:
            raise MuxerError("No subtitle indices selected.")
        for idx in indices:
            cmd.extend(["-map", f"1:s:{idx}"])

    # Stream copy — no re-encode
    cmd.extend(["-c", "copy"])

    # MP4 often needs +faststart for playback; harmless with -c copy when compatible
    if options.container.lower() == "mp4":
        cmd.extend(["-movflags", "+faststart"])

    cmd.append(str(options.output))
    return cmd


def mux_subtitles(
    options: MuxOptions,
    on_log: LogCallback | None = None,
    cancel_event: Callable[[], bool] | None = None,
) -> None:
    """
    Run FFmpeg and stream stdout/stderr lines to *on_log*.

    *cancel_event*, if provided, should return True when the caller wants
    the process aborted (e.g. threading.Event.is_set).
    """
    if options.container.lower() not in {"mkv", "mp4"}:
        raise MuxerError(f"Unsupported container: {options.container}")

    output = options.output
    if output.exists() and output.is_dir():
        raise MuxerError(f"Output path is a directory: {output}")

    # Ensure parent directory exists
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = build_ffmpeg_command(options)
    if on_log:
        on_log("$ " + " ".join(cmd))

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # merge; FFmpeg logs progress on stderr
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
    except OSError as exc:
        raise MuxerError(f"Failed to start FFmpeg: {exc}") from exc

    assert process.stdout is not None
    try:
        for line in process.stdout:
            if cancel_event and cancel_event():
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                raise MuxerError("Mux cancelled by user.")
            text = line.rstrip("\n\r")
            if text and on_log:
                on_log(text)
    finally:
        process.stdout.close()

    return_code = process.wait()
    if return_code != 0:
        raise MuxerError(
            f"FFmpeg exited with code {return_code}. "
            "Subtitle mapping may be incompatible with the selected container "
            "(MP4 has limited subtitle codec support — try MKV)."
        )

    if on_log:
        on_log(f"Done — wrote {output}")
