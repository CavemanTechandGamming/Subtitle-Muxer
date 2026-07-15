"""
Lightweight persisted user settings (default save folder, etc.).
Stored under the user's app data / home directory — not in the repo.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _settings_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "SubtitleMuxer" / "settings.json"


def load_settings() -> dict[str, Any]:
    path = _settings_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_settings(settings: dict[str, Any]) -> None:
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def get_default_output_dir() -> Path | None:
    raw = load_settings().get("default_output_dir")
    if not raw:
        return None
    path = Path(str(raw)).expanduser()
    return path if path.is_dir() else None


def set_default_output_dir(directory: Path | str) -> Path:
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"Not a directory: {directory}")
    settings = load_settings()
    settings["default_output_dir"] = str(directory)
    save_settings(settings)
    return directory
