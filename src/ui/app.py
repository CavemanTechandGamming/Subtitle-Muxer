"""
Main CustomTkinter window — dark-mode Subtitle Muxer UI.

UI responsibilities only; FFmpeg work lives in ``src.core``.
"""

from __future__ import annotations

import queue
import threading
from pathlib import Path

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from src.core.muxer import MuxOptions, MuxerError, mux_subtitles
from src.core.probe import ProbeError, assert_video_file, probe_source
from src.core.settings import get_default_output_dir, set_default_output_dir
from src.ui.about import show_about
from src.ui.dialogs import ask_yes_no, show_error, show_info, show_warning
from src.ui.widgets import FileDropZone, SubtitleTrackList, looks_like_video


# Force dark appearance for the entire app (no light-mode toggle).
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


class SubtitleMuxerApp(ctk.CTk, TkinterDnD.DnDWrapper):
    """Root window combining CustomTkinter styling with tkinterdnd2 drops."""

    def __init__(self) -> None:
        super().__init__()
        # Enable native DnD on this Tk root
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("Subtitle Muxer")
        self.geometry("960x820")
        self.minsize(820, 700)

        self._log_queue: queue.Queue[str] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._cancel = threading.Event()
        self._closing = False
        self._poll_after_id: str | None = None
        self._filename_user_edited = False

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_layout()
        self._wire_drag_and_drop()
        self._poll_after_id = self.after(100, self._drain_log_queue)

    # ── layout ──────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # track list grows
        self.grid_rowconfigure(6, weight=1)  # log grows

        header_row = ctk.CTkFrame(self, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 4))
        header_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_row,
            text="Subtitle Muxer",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header_row,
            text="About",
            width=80,
            height=28,
            fg_color=("gray40", "gray30"),
            hover_color=("gray35", "gray25"),
            command=lambda: show_about(self),
        ).grid(row=0, column=1, sticky="e")

        subtitle = ctk.CTkLabel(
            self,
            text="Copy subtitle tracks from a source video onto an upscaled target — stream copy, no re-encode.",
            font=ctk.CTkFont(size=13),
            text_color="gray65",
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))

        # Source + Target drop zones side by side
        files_row = ctk.CTkFrame(self, fg_color="transparent")
        files_row.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))
        files_row.grid_columnconfigure(0, weight=1)
        files_row.grid_columnconfigure(1, weight=1)

        self.source_zone = FileDropZone(
            files_row,
            title="Source Video (with subtitles)",
            hint="Drop source video here or click Browse…",
            on_path_changed=self._on_source_changed,
            border_color=("gray60", "gray35"),
        )
        self.source_zone.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.target_zone = FileDropZone(
            files_row,
            title="Target Video (upscaled / no subs)",
            hint="Drop target video here or click Browse…",
            on_path_changed=self._on_target_changed,
            border_color=("gray60", "gray35"),
        )
        self.target_zone.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Subtitle track list
        tracks_frame = ctk.CTkFrame(self, corner_radius=10, border_width=1, border_color=("gray60", "gray35"))
        tracks_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=8)
        tracks_frame.grid_columnconfigure(0, weight=1)
        tracks_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            tracks_frame,
            text="Subtitle Tracks",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))

        self.track_list = SubtitleTrackList(tracks_frame, fg_color="transparent")
        self.track_list.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 10))

        # Destination (HandBrake-style save location)
        dest = ctk.CTkFrame(self, corner_radius=10, border_width=1, border_color=("gray60", "gray35"))
        dest.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 4))
        dest.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            dest,
            text="Destination",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, sticky="ew", padx=12, pady=(10, 6))

        ctk.CTkLabel(dest, text="Save to:", width=70, anchor="w").grid(
            row=1, column=0, sticky="w", padx=(12, 8), pady=4
        )

        initial_dir = get_default_output_dir() or (Path.home() / "Videos")
        if not initial_dir.is_dir():
            initial_dir = Path.home()

        self._save_dir_var = ctk.StringVar(value=str(initial_dir))
        self.save_dir_entry = ctk.CTkEntry(dest, textvariable=self._save_dir_var)
        self.save_dir_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=4)
        self._save_dir_var.trace_add("write", lambda *_: self._refresh_destination_preview())

        ctk.CTkButton(
            dest,
            text="Browse…",
            width=90,
            command=self._browse_save_dir,
        ).grid(row=1, column=2, sticky="e", padx=(0, 8), pady=4)

        ctk.CTkButton(
            dest,
            text="Same as target",
            width=120,
            fg_color=("gray40", "gray30"),
            hover_color=("gray35", "gray25"),
            command=self._use_target_dir,
        ).grid(row=1, column=3, sticky="e", padx=(0, 12), pady=4)

        ctk.CTkLabel(dest, text="Filename:", width=70, anchor="w").grid(
            row=2, column=0, sticky="w", padx=(12, 8), pady=4
        )

        self._filename_var = ctk.StringVar(value="")
        self.filename_entry = ctk.CTkEntry(dest, textvariable=self._filename_var)
        self.filename_entry.grid(row=2, column=1, columnspan=3, sticky="ew", padx=(0, 12), pady=4)
        self._filename_var.trace_add("write", self._on_filename_typed)

        self._dest_preview = ctk.CTkLabel(
            dest,
            text="Full path: (set a target video)",
            font=ctk.CTkFont(size=12),
            text_color="gray65",
            anchor="w",
            wraplength=860,
            justify="left",
        )
        self._dest_preview.grid(row=3, column=0, columnspan=4, sticky="ew", padx=12, pady=(2, 10))

        # Output options + actions
        options = ctk.CTkFrame(self, fg_color="transparent")
        options.grid(row=5, column=0, sticky="ew", padx=16, pady=8)
        options.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            options,
            text="Output container:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=(4, 12))

        self._container = ctk.StringVar(value="mkv")
        radio_row = ctk.CTkFrame(options, fg_color="transparent")
        radio_row.grid(row=0, column=1, sticky="w")

        ctk.CTkRadioButton(
            radio_row,
            text="MKV (recommended)",
            variable=self._container,
            value="mkv",
            command=self._on_container_changed,
        ).pack(side="left", padx=(0, 16))

        ctk.CTkRadioButton(
            radio_row,
            text="MP4",
            variable=self._container,
            value="mp4",
            command=self._on_container_changed,
        ).pack(side="left")

        self.mux_btn = ctk.CTkButton(
            options,
            text="Mux Subtitles",
            width=160,
            height=36,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._start_mux,
        )
        self.mux_btn.grid(row=0, column=2, sticky="e", padx=(12, 4))

        # Log console
        log_frame = ctk.CTkFrame(self, corner_radius=10, border_width=1, border_color=("gray60", "gray35"))
        log_frame.grid(row=6, column=0, sticky="nsew", padx=16, pady=(8, 16))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            log_header,
            text="FFmpeg Log",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(side="left")

        ctk.CTkButton(
            log_header,
            text="Clear",
            width=70,
            height=26,
            fg_color=("gray40", "gray30"),
            hover_color=("gray35", "gray25"),
            command=self._clear_log,
        ).pack(side="right")

        self.log_box = ctk.CTkTextbox(
            log_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            activate_scrollbars=True,
            wrap="word",
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.log_box.configure(state="disabled")

    # ── drag & drop ─────────────────────────────────────────────────────

    def _wire_drag_and_drop(self) -> None:
        """Register each drop zone as a DnD target for file paths."""
        for zone, role in (
            (self.source_zone, "source"),
            (self.target_zone, "target"),
        ):
            zone.drop_target_register(DND_FILES)
            zone.dnd_bind("<<DropEnter>>", lambda e, z=zone: self._on_dnd_enter(e, z))
            zone.dnd_bind("<<DropLeave>>", lambda e, z=zone: self._on_dnd_leave(e, z))
            zone.dnd_bind(
                "<<Drop>>",
                lambda e, z=zone, r=role: self._on_drop(e, z, r),
            )

    def _on_dnd_enter(self, event, zone: FileDropZone):
        zone.highlight(True)
        return event.action

    def _on_dnd_leave(self, _event, zone: FileDropZone):
        zone.highlight(False)

    def _on_drop(self, event, zone: FileDropZone, role: str):
        zone.highlight(False)
        paths = self._parse_drop_data(event.data)
        if not paths:
            return

        path = paths[0]
        if not looks_like_video(path):
            show_warning(
                self,
                "Not a video",
                f"'{path.name}' does not look like a supported video file.",
            )
            return

        zone.set_path(path)
        self._append_log(f"Loaded {role}: {path}")

    def _parse_drop_data(self, data: str) -> list[Path]:
        """Convert Tk DnD payload into Path objects (handles braces / spaces)."""
        try:
            raw = self.tk.splitlist(data)
        except Exception:
            raw = [data.strip()]
        return [Path(p) for p in raw if p]

    # ── source / target callbacks ───────────────────────────────────────

    def _on_source_changed(self, path: Path | None) -> None:
        if path is None:
            self.track_list.clear()
            return
        self._load_subtitle_tracks(path)

    def _on_target_changed(self, path: Path | None) -> None:
        if path:
            self._append_log(f"Target set: {path}")
            # If the user hasn't chosen a remembered folder, follow the target (HandBrake-like).
            if get_default_output_dir() is None:
                self._save_dir_var.set(str(path.parent))
            self._filename_user_edited = False
            self._suggest_filename()
        else:
            self._refresh_destination_preview()

    # ── destination helpers ─────────────────────────────────────────────

    def _suggested_filename(self, target: Path | None = None) -> str:
        target = target or self.target_zone.get_path()
        container = self._container.get()
        if target is None:
            return f"output Subtitle Muxer.{container}"
        return f"{target.stem} Subtitle Muxer.{container}"

    def _suggest_filename(self) -> None:
        if self._filename_user_edited:
            # Still keep extension in sync with the container radio.
            name = self._filename_var.get().strip()
            container = self._container.get()
            if name:
                stem = Path(name).stem or name
                self._filename_var.set(f"{stem}.{container}")
            self._refresh_destination_preview()
            return
        self._filename_var.set(self._suggested_filename())
        self._filename_user_edited = False
        self._refresh_destination_preview()

    def _on_filename_typed(self, *_args) -> None:
        # Ignore programmatic updates that call set() during suggest.
        if self.focus_get() is self.filename_entry:
            self._filename_user_edited = True
        self._refresh_destination_preview()

    def _on_container_changed(self) -> None:
        self._suggest_filename()

    def _browse_save_dir(self) -> None:
        from tkinter import filedialog

        current = self._save_dir_var.get().strip()
        initial = current if Path(current).is_dir() else str(Path.home())
        chosen = filedialog.askdirectory(title="Choose default save folder", initialdir=initial)
        if not chosen:
            return
        path = set_default_output_dir(chosen)
        self._save_dir_var.set(str(path))
        self._append_log(f"Default save folder: {path}")

    def _use_target_dir(self) -> None:
        target = self.target_zone.get_path()
        if target is None:
            show_info(self, "No target", "Load a target video first.")
            return
        path = set_default_output_dir(target.parent)
        self._save_dir_var.set(str(path))
        self._append_log(f"Default save folder: {path}")

    def _destination_path(self) -> Path | None:
        folder = self._save_dir_var.get().strip()
        name = self._filename_var.get().strip()
        if not folder or not name:
            return None
        container = self._container.get()
        path = Path(folder) / name
        if path.suffix.lower() != f".{container}":
            path = path.with_suffix(f".{container}")
        return path

    def _refresh_destination_preview(self) -> None:
        path = self._destination_path()
        if path is None:
            self._dest_preview.configure(text="Full path: (choose a save folder and filename)")
        else:
            self._dest_preview.configure(text=f"Full path: {path}")

    def _load_subtitle_tracks(self, path: Path) -> None:
        self._append_log(f"Probing source for subtitle tracks: {path.name}")
        try:
            result = probe_source(path)
        except ProbeError as exc:
            self.track_list.clear()
            self._append_log(f"ERROR: {exc}")
            show_error(self, "Probe failed", str(exc))
            # Clear invalid selection
            self.source_zone.clear()
            return

        self.track_list.set_tracks(result.tracks)
        if result.tracks:
            self._append_log(f"Found {len(result.tracks)} subtitle track(s).")
            return

        self._append_log("Warning: no soft subtitle streams found in this file.")
        self._append_log("Streams detected:")
        self._append_log(result.stream_summary)
        if result.has_closed_captions:
            self._append_log(
                "Note: this file has embedded closed captions inside the "
                "video stream (CEA-608/708). Those are not separate "
                "subtitle tracks and cannot be stream-copied this way."
            )

    # ── mux workflow ────────────────────────────────────────────────────

    def _start_mux(self) -> None:
        if self._worker and self._worker.is_alive():
            show_info(self, "Busy", "A mux job is already running.")
            return

        source = self.source_zone.get_path()
        target = self.target_zone.get_path()

        if not source or not target:
            show_warning(
                self,
                "Missing files",
                "Please choose both a Source video and a Target video.",
            )
            return

        try:
            assert_video_file(target)
        except ProbeError as exc:
            show_error(self, "Invalid target", str(exc))
            self._append_log(f"ERROR: {exc}")
            return

        selected = self.track_list.selected_indices()
        if selected is not None and len(selected) == 0:
            show_warning(
                self,
                "No tracks selected",
                "Select at least one subtitle track, or use Select All.",
            )
            return

        # selected is None when Select All is active; still need tracks present
        if selected is None and self.track_list.track_count() == 0:
            show_warning(
                self,
                "No subtitles",
                "The source video has no subtitle tracks to copy.",
            )
            return

        container = self._container.get()
        output = self._destination_path()
        if output is None:
            show_warning(
                self,
                "Destination incomplete",
                "Choose a save folder and filename in the Destination section.",
            )
            return

        folder = output.parent
        if not folder.is_dir():
            show_error(
                self,
                "Invalid folder",
                f"Save folder does not exist:\n{folder}",
            )
            return

        # Remember this folder for next launch
        try:
            set_default_output_dir(folder)
        except ValueError:
            pass

        if output.exists():
            if not ask_yes_no(
                self,
                "Overwrite?",
                f"This file already exists:\n{output}\n\nOverwrite it?",
            ):
                return

        if container == "mp4":
            self._append_log(
                "Note: MP4 has limited subtitle codec support. "
                "If mux fails, switch to MKV."
            )

        options = MuxOptions(
            target=target,
            source=source,
            output=output,
            subtitle_indices=selected,
            container=container,
        )

        self._cancel.clear()
        self.mux_btn.configure(state="disabled", text="Muxing…")
        self._append_log("— Starting mux —")

        self._worker = threading.Thread(
            target=self._run_mux_worker,
            args=(options,),
            daemon=True,
        )
        self._worker.start()

    def _run_mux_worker(self, options: MuxOptions) -> None:
        try:
            mux_subtitles(
                options,
                on_log=lambda line: self._log_queue.put(line),
                cancel_event=self._cancel.is_set,
            )
            self._log_queue.put("__SUCCESS__")
        except MuxerError as exc:
            self._log_queue.put(f"ERROR: {exc}")
            self._log_queue.put("__FAIL__")
        except Exception as exc:  # noqa: BLE001 — surface unexpected errors in log
            self._log_queue.put(f"ERROR: Unexpected failure: {exc}")
            self._log_queue.put("__FAIL__")

    # ── logging ─────────────────────────────────────────────────────────

    def _append_log(self, text: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _drain_log_queue(self) -> None:
        """Poll worker log lines onto the UI thread."""
        if self._closing:
            return
        try:
            while True:
                line = self._log_queue.get_nowait()
                if line == "__SUCCESS__":
                    self.mux_btn.configure(state="normal", text="Mux Subtitles")
                    show_info(self, "Success", "Subtitles muxed successfully.")
                elif line == "__FAIL__":
                    self.mux_btn.configure(state="normal", text="Mux Subtitles")
                    show_error(
                        self,
                        "Mux failed",
                        "FFmpeg reported an error. Check the log for details.",
                    )
                else:
                    self._append_log(line)
        except queue.Empty:
            pass
        if not self._closing:
            self._poll_after_id = self.after(100, self._drain_log_queue)

    def _on_close(self) -> None:
        """Clean shutdown — cancel work, stop polling, exit mainloop."""
        if self._closing:
            return
        self._closing = True
        self._cancel.set()

        if self._poll_after_id is not None:
            try:
                self.after_cancel(self._poll_after_id)
            except Exception:
                pass
            self._poll_after_id = None

        # Ask the mux worker to unwind (daemon thread; terminate best-effort)
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=1.0)

        try:
            self.quit()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass


def run_app() -> None:
    """Create and start the application main loop."""
    app = SubtitleMuxerApp()
    try:
        app.mainloop()
    finally:
        # Belt-and-suspenders for sticky Tk/DnD process on Windows
        if not app._closing:
            app._on_close()
