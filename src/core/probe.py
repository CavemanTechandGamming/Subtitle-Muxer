"""
Probe video files with ffprobe and extract subtitle track metadata.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.ffmpeg_paths import FFmpegBootstrapError, ensure_ffmpeg_on_path, ffprobe_binary


class ProbeError(Exception):
    """Raised when a file cannot be probed or is not a usable video."""


# Codec names that are always subtitle even if codec_type is odd/missing.
_SUBTITLE_CODEC_HINTS = {
    "subrip",
    "srt",
    "ass",
    "ssa",
    "mov_text",
    "webvtt",
    "hdmv_pgs_subtitle",
    "pgssub",
    "dvd_subtitle",
    "dvdsub",
    "dvb_subtitle",
    "dvb_teletext",
    "xsub",
    "eia_608",
    "cc_dec",
    "timed_id3",
    "arib_caption",
}


@dataclass(frozen=True)
class SubtitleTrack:
    """One subtitle stream discovered in the source video."""

    # Index among subtitle streams only (0, 1, 2…), used for -map 1:s:N
    subtitle_index: int
    # Absolute stream index from the container (informative)
    stream_index: int
    codec: str
    language: str
    title: str
    is_forced: bool
    is_default: bool

    def display_label(self) -> str:
        """Human-readable label for the track list UI."""
        lang = self.language or "und"
        parts = [f"[{self.subtitle_index}]", lang.upper(), self.codec]
        if self.title:
            parts.append(f"— {self.title}")
        flags: list[str] = []
        if self.is_default:
            flags.append("default")
        if self.is_forced:
            flags.append("forced")
        if flags:
            parts.append(f"({', '.join(flags)})")
        return "  ".join(parts)


# Codecs that usually stream-copy into MP4 without remux/convert.
# Everything else (ASS, PGS, SRT, DVD, …) tends to fail with -c copy.
_MP4_STREAM_COPY_OK = frozenset({
    "mov_text",
    "tx3g",
})


def is_mp4_stream_copy_friendly(codec: str) -> bool:
    """True if *codec* is known to stream-copy into MP4 reliably."""

    return (codec or "").strip().lower() in _MP4_STREAM_COPY_OK


def mp4_incompatible_tracks(tracks: Sequence[SubtitleTrack]) -> list[SubtitleTrack]:
    """Return selected tracks that are unlikely to stream-copy into MP4."""

    return [t for t in tracks if not is_mp4_stream_copy_friendly(t.codec)]


def _is_subtitle_stream(stream: dict[str, Any]) -> bool:
    codec_type = (stream.get("codec_type") or "").lower()
    if codec_type == "subtitle":
        return True
    codec_name = (stream.get("codec_name") or "").lower()
    return codec_name in _SUBTITLE_CODEC_HINTS


def _probe(path: Path) -> dict[str, Any]:
    """
    Run ffprobe with a large probesize so late-multiplexed subtitle streams
    (common in MKV / some MP4) are not missed by default probe limits.
    """
    try:
        ensure_ffmpeg_on_path()
        probe_bin = ffprobe_binary()
    except FFmpegBootstrapError as exc:
        raise ProbeError(str(exc)) from exc

    cmd = [
        probe_bin,
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-probesize",
        "200M",
        "-analyzeduration",
        "200M",
        "-of",
        "json",
        str(path),
    ]

    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as exc:
        raise ProbeError(
            "ffprobe was not found. Re-run scripts\\setup_env.bat to install "
            "bundled FFmpeg, or install FFmpeg on your system PATH."
        ) from exc
    except OSError as exc:
        raise ProbeError(f"Failed to run ffprobe: {exc}") from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip() or f"exit {completed.returncode}"
        raise ProbeError(f"Failed to probe '{path.name}': {detail}")

    try:
        return json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise ProbeError(f"ffprobe returned invalid JSON for '{path.name}'.") from exc


def format_stream_summary(info: dict[str, Any]) -> str:
    """Short human-readable summary of all streams (for the log panel)."""
    lines: list[str] = []
    for stream in info.get("streams") or []:
        idx = stream.get("index", "?")
        ctype = stream.get("codec_type", "?")
        cname = stream.get("codec_name", "?")
        tags = stream.get("tags") or {}
        lang = tags.get("language") or tags.get("LANGUAGE") or ""
        title = tags.get("title") or tags.get("TITLE") or ""
        extra = " ".join(p for p in (lang, title) if p)
        lines.append(f"  #{idx} {ctype}/{cname}" + (f" ({extra})" if extra else ""))
    if not lines:
        return "  (no streams)"
    return "\n".join(lines)


def info_has_embedded_closed_captions(info: dict[str, Any]) -> bool:
    """True if video streams advertise CEA-608/708-style closed captions."""
    for stream in info.get("streams") or []:
        if stream.get("codec_type") != "video":
            continue
        if stream.get("closed_captions") in (1, "1", True):
            return True
    return False


def assert_video_file(path: Path | str) -> Path:
    """
    Validate that *path* exists and contains at least one video stream.

    Returns the resolved Path on success.
    """
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise ProbeError(f"File not found: {path}")

    info = _probe(path)
    streams = info.get("streams") or []
    has_video = any(s.get("codec_type") == "video" for s in streams)
    if not has_video:
        raise ProbeError(
            f"'{path.name}' does not contain a video stream. "
            "Please select a valid video file."
        )
    return path


def _tracks_from_info(info: dict[str, Any]) -> list[SubtitleTrack]:
    tracks: list[SubtitleTrack] = []
    subtitle_index = 0

    for stream in info.get("streams") or []:
        if not _is_subtitle_stream(stream):
            continue

        tags = stream.get("tags") or {}
        disposition = stream.get("disposition") or {}

        language = (
            tags.get("language")
            or tags.get("LANGUAGE")
            or "und"
        )
        title = tags.get("title") or tags.get("TITLE") or ""

        tracks.append(
            SubtitleTrack(
                subtitle_index=subtitle_index,
                stream_index=int(stream.get("index", subtitle_index)),
                codec=stream.get("codec_name") or stream.get("codec_type") or "unknown",
                language=str(language),
                title=str(title),
                is_forced=bool(disposition.get("forced")),
                is_default=bool(disposition.get("default")),
            )
        )
        subtitle_index += 1

    return tracks


def probe_subtitle_tracks(path: Path | str) -> list[SubtitleTrack]:
    """
    Return every subtitle stream in *path*, ordered by appearance.

    Raises ProbeError if the file is missing, not a video, or cannot be probed.
    """
    return probe_source(path).tracks


@dataclass(frozen=True)
class ProbeResult:
    """Full probe outcome used by the UI (one ffprobe call)."""

    path: Path
    tracks: list[SubtitleTrack]
    stream_summary: str
    has_closed_captions: bool


@dataclass(frozen=True)
class DurationMismatch:
    """Source and target durations differ enough to warrant a confirm dialog."""

    source_seconds: float
    target_seconds: float

    @property
    def delta_seconds(self) -> float:
        return abs(self.source_seconds - self.target_seconds)


# Warn when |source − target| is at least this many seconds.
DURATION_MISMATCH_THRESHOLD_SECONDS = 2.0


def duration_from_info(info: dict[str, Any]) -> float | None:
    """Best-effort media duration in seconds from an ffprobe JSON blob."""

    format_block = info.get("format") or {}
    raw = format_block.get("duration")
    if raw is not None and raw != "N/A":
        try:
            value = float(raw)
            if value > 0:
                return value
        except (TypeError, ValueError):
            pass

    # Fall back to the longest video stream duration if format lacks one.
    best: float | None = None
    for stream in info.get("streams") or []:
        if stream.get("codec_type") != "video":
            continue
        raw = stream.get("duration")
        if raw is None or raw == "N/A":
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value > 0 and (best is None or value > best):
            best = value
    return best


def format_duration(seconds: float) -> str:
    """Format seconds as ``H:MM:SS`` or ``M:SS`` for dialogs."""

    total = max(0, int(round(seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def probe_duration_seconds(path: Path | str) -> float | None:
    """Return media duration in seconds, or None if unknown."""

    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise ProbeError(f"File not found: {path}")
    return duration_from_info(_probe(path))


def check_duration_mismatch(
    source: Path | str,
    target: Path | str,
    *,
    threshold_seconds: float = DURATION_MISMATCH_THRESHOLD_SECONDS,
) -> DurationMismatch | None:
    """
    Compare source vs target duration.

    Returns a DurationMismatch when both durations are known and differ by
    at least *threshold_seconds*. Returns None when durations match closely
    enough, or when either duration cannot be determined (no false alarms).
    """

    source_dur = probe_duration_seconds(source)
    target_dur = probe_duration_seconds(target)
    if source_dur is None or target_dur is None:
        return None

    delta = abs(source_dur - target_dur)
    if delta < threshold_seconds:
        return None

    return DurationMismatch(source_seconds=source_dur, target_seconds=target_dur)


def probe_source(path: Path | str) -> ProbeResult:
    """Probe a source video once and return tracks + diagnostic summary."""
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise ProbeError(f"File not found: {path}")

    info = _probe(path)
    streams = info.get("streams") or []
    if not any(s.get("codec_type") == "video" for s in streams):
        raise ProbeError(
            f"'{path.name}' does not contain a video stream. "
            "Please select a valid video file."
        )

    return ProbeResult(
        path=path,
        tracks=_tracks_from_info(info),
        stream_summary=format_stream_summary(info),
        has_closed_captions=info_has_embedded_closed_captions(info),
    )
