"""
Reusable CustomTkinter widgets: file drop zones and subtitle track checklist.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tkinter import BooleanVar

import customtkinter as ctk

from src.core.probe import SubtitleTrack

# Accepted video extensions for drop / browse filters
VIDEO_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".m4v",
    ".avi",
    ".mov",
    ".wmv",
    ".webm",
    ".ts",
    ".m2ts",
    ".mpg",
    ".mpeg",
}


def looks_like_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


class FileDropZone(ctk.CTkFrame):
    """
    Dark drop / browse panel for a single video path.

    Drag-and-drop is wired by the parent window (TkinterDnD); this widget
    only exposes ``set_path`` / ``get_path`` and a browse button.
    """

    def __init__(
        self,
        master,
        title: str,
        hint: str,
        on_path_changed: Callable[[Path | None], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, corner_radius=10, **kwargs)
        self._on_path_changed = on_path_changed
        self._path: Path | None = None

        self.grid_columnconfigure(0, weight=1)

        self._title = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        )
        self._title.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))

        self._path_label = ctk.CTkLabel(
            self,
            text=hint,
            font=ctk.CTkFont(size=12),
            text_color=("gray70", "gray60"),
            anchor="w",
            wraplength=420,
            justify="left",
        )
        self._path_label.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))

        self._browse_btn = ctk.CTkButton(
            btn_row,
            text="Browse…",
            width=100,
            command=self._browse,
        )
        self._browse_btn.pack(side="left")

        self._clear_btn = ctk.CTkButton(
            btn_row,
            text="Clear",
            width=80,
            fg_color=("gray40", "gray30"),
            hover_color=("gray35", "gray25"),
            command=self.clear,
        )
        self._clear_btn.pack(side="left", padx=(8, 0))
        self.configure(border_width=2)

    def highlight(self, active: bool) -> None:
        """Visual feedback while dragging over this zone."""
        if active:
            self.configure(border_color="#3B8ED0")
        else:
            self.configure(border_color=("gray60", "gray35"))

    def get_path(self) -> Path | None:
        return self._path

    def set_path(self, path: Path | None) -> None:
        self._path = path
        if path is None:
            self._path_label.configure(
                text="Drop a video here or click Browse…",
                text_color=("gray70", "gray60"),
            )
        else:
            self._path_label.configure(
                text=str(path),
                text_color=("gray10", "gray90"),
            )
        if self._on_path_changed:
            self._on_path_changed(path)

    def clear(self) -> None:
        self.set_path(None)

    def _browse(self) -> None:
        from tkinter import filedialog

        chosen = filedialog.askopenfilename(
            title="Select video",
            filetypes=[
                ("Video files", "*.mkv *.mp4 *.m4v *.avi *.mov *.wmv *.webm *.ts *.m2ts *.mpg *.mpeg"),
                ("All files", "*.*"),
            ],
        )
        if chosen:
            self.set_path(Path(chosen))


class _AutoHideScrollableFrame(ctk.CTkScrollableFrame):
    """CTkScrollableFrame that hides the scrollbar when content fits."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        # CTk always shows the bar; hide it when top==0 and bottom==1.
        self._parent_canvas.configure(
            yscrollcommand=lambda top, bottom: self._auto_hide_scrollbar(top, bottom)
        )

    def _auto_hide_scrollbar(self, top, bottom) -> None:
        if float(top) <= 0.0 and float(bottom) >= 1.0:
            self._scrollbar.grid_remove()
        else:
            self._scrollbar.grid()
        self._scrollbar.set(top, bottom)


class SubtitleTrackList(ctk.CTkFrame):
    """Checklist of subtitle tracks with Select All (scrolls only when needed)."""

    _EMPTY_NO_SOURCE = "Load a source video to list subtitle tracks."
    _EMPTY_NO_TRACKS = "No subtitle tracks found in the source video."

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._track_vars: list[tuple[SubtitleTrack, BooleanVar]] = []
        self._select_all_var = BooleanVar(value=True)
        self._rows: list[ctk.CTkCheckBox] = []

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=4, pady=(4, 8))

        self._select_all = ctk.CTkCheckBox(
            header,
            text="Select All",
            variable=self._select_all_var,
            command=self._on_select_all,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._select_all.pack(side="left")

        self._status = ctk.CTkLabel(
            header,
            text="No source loaded",
            text_color=("gray60", "gray55"),
            font=ctk.CTkFont(size=12),
        )
        self._status.pack(side="right")

        # Tracks live in a scrollable body so Select All stays pinned above.
        self._body = _AutoHideScrollableFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True)

        self._empty = ctk.CTkLabel(
            self._body,
            text=self._EMPTY_NO_SOURCE,
            text_color=("gray60", "gray55"),
        )
        self._empty.pack(pady=20)

    def set_tracks(self, tracks: list[SubtitleTrack]) -> None:
        """Replace the checklist with new tracks (all selected by default)."""
        self._clear_rows()

        if not tracks:
            self._show_empty(self._EMPTY_NO_TRACKS)
            self._status.configure(text="0 tracks")
            self._select_all_var.set(False)
            return

        self._hide_empty()
        self._select_all_var.set(True)
        for track in tracks:
            var = BooleanVar(value=True)
            cb = ctk.CTkCheckBox(
                self._body,
                text=track.display_label(),
                variable=var,
                command=self._sync_select_all_state,
            )
            cb.pack(fill="x", padx=8, pady=3)
            self._rows.append(cb)
            self._track_vars.append((track, var))

        self._status.configure(text=f"{len(tracks)} track(s)")

    def track_count(self) -> int:
        return len(self._track_vars)

    def clear(self) -> None:
        """Reset to the pre-load empty state (no source selected)."""
        self._clear_rows()
        self._show_empty(self._EMPTY_NO_SOURCE)
        self._status.configure(text="No source loaded")
        self._select_all_var.set(True)

    def selected_indices(self) -> list[int] | None:
        """
        Return selected subtitle-relative indices.

        Returns None when every track is selected (map all / Select All).
        Returns [] if nothing is selected.
        """
        if not self._track_vars:
            return []

        selected = [t.subtitle_index for t, v in self._track_vars if v.get()]
        if len(selected) == len(self._track_vars):
            return None  # caller maps all with -map 1:s
        return selected

    def selected_tracks(self) -> list[SubtitleTrack]:
        """Return SubtitleTrack objects currently checked in the list."""

        if not self._track_vars:
            return []
        indices = self.selected_indices()
        if indices is None:
            return [t for t, _ in self._track_vars]
        wanted = set(indices)
        return [t for t, _ in self._track_vars if t.subtitle_index in wanted]

    def _clear_rows(self) -> None:
        for row in self._rows:
            row.destroy()
        self._rows.clear()
        self._track_vars.clear()

    def _hide_empty(self) -> None:
        if self._empty.winfo_exists():
            self._empty.pack_forget()

    def _show_empty(self, text: str) -> None:
        self._hide_empty()
        if not self._empty.winfo_exists():
            self._empty = ctk.CTkLabel(
                self._body,
                text=text,
                text_color=("gray60", "gray55"),
            )
        else:
            self._empty.configure(text=text)
        self._empty.pack(pady=20)

    def _on_select_all(self) -> None:
        checked = self._select_all_var.get()
        for _, var in self._track_vars:
            var.set(checked)

    def _sync_select_all_state(self) -> None:
        if not self._track_vars:
            return
        all_on = all(v.get() for _, v in self._track_vars)
        self._select_all_var.set(all_on)

