"""
Simple About dialog — short blurb + optional support link.
"""

from __future__ import annotations

import webbrowser

import customtkinter as ctk

from src import __version__

# ── Change this to your page before publishing ──────────────────────────────
BUY_ME_A_COFFEE_URL = "https://www.buymeacoffee.com/caveman117"
# ────────────────────────────────────────────────────────────────────────────

_ABOUT_BLURB = (
    "Subtitle Muxer copies soft subtitle tracks from a source video onto a "
    "target video (for example an upscaled file) using FFmpeg stream copy — "
    "no re-encode, no quality loss.\n\n"
    "Pick your source and target, choose which tracks to keep, set a "
    "destination, and mux."
)


class AboutDialog(ctk.CTkToplevel):
    """Compact, dark About window."""

    def __init__(self, master):
        super().__init__(master)
        self.title("About Subtitle Muxer")
        self.geometry("420x320")
        self.minsize(380, 280)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text="Subtitle Muxer",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 2))

        ctk.CTkLabel(
            self,
            text=f"Version {__version__}",
            font=ctk.CTkFont(size=12),
            text_color="gray65",
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            self,
            text=_ABOUT_BLURB,
            font=ctk.CTkFont(size=13),
            wraplength=370,
            justify="left",
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 16))
        buttons.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            buttons,
            text="Buy Me a Coffee",
            command=self._open_coffee,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ctk.CTkButton(
            buttons,
            text="Close",
            fg_color=("gray40", "gray30"),
            hover_color=("gray35", "gray25"),
            command=self.destroy,
        ).grid(row=1, column=0, sticky="ew")

        self.after(10, self._center_on_parent)

    def _center_on_parent(self) -> None:
        try:
            self.update_idletasks()
            parent = self.master
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            w = self.winfo_width()
            h = self.winfo_height()
            self.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")
        except Exception:
            pass

    def _open_coffee(self) -> None:
        webbrowser.open(BUY_ME_A_COFFEE_URL)


def show_about(master) -> None:
    """Open the About dialog (one instance at a time is fine for this app)."""
    dialog = AboutDialog(master)
    dialog.focus()
