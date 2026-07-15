"""
Dark-themed modal dialogs that match the CustomTkinter UI.

Replaces tkinter.messagebox, which always follows the OS light chrome on Windows.
"""

from __future__ import annotations

import customtkinter as ctk


def _center_on_parent(window: ctk.CTkToplevel, parent) -> None:
    try:
        window.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w = window.winfo_width()
        h = window.winfo_height()
        window.geometry(f"+{px + (pw - w) // 2}+{py + (ph - h) // 2}")
    except Exception:
        pass


class _MessageDialog(ctk.CTkToplevel):
    """Shared look-and-feel for info / warning / error / confirm dialogs."""

    def __init__(
        self,
        master,
        *,
        title: str,
        message: str,
        kind: str = "info",
        buttons: tuple[tuple[str, str], ...] = (("OK", "ok"),),
    ):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.result: str | None = None

        accent = {
            "info": ("#3B8ED0", "Info"),
            "warning": ("#C9A227", "Warning"),
            "error": ("#C0392B", "Error"),
            "confirm": ("#3B8ED0", "Confirm"),
        }.get(kind, ("#3B8ED0", "Info"))
        accent_color, kind_label = accent

        self.grid_columnconfigure(0, weight=1)

        badge = ctk.CTkLabel(
            self,
            text=kind_label,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=accent_color,
            anchor="w",
        )
        badge.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=13),
            wraplength=360,
            justify="left",
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=3, column=0, sticky="e", padx=20, pady=(0, 16))

        for i, (label, value) in enumerate(buttons):
            is_primary = i == len(buttons) - 1
            btn = ctk.CTkButton(
                row,
                text=label,
                width=100,
                fg_color=accent_color if is_primary and kind != "error" else None,
                command=lambda v=value: self._finish(v),
            )
            if kind == "error" and is_primary:
                btn.configure(fg_color=accent_color, hover_color="#A93226")
            if not is_primary:
                btn.configure(
                    fg_color=("gray40", "gray30"),
                    hover_color=("gray35", "gray25"),
                )
            btn.pack(side="left", padx=(8, 0) if i else 0)

        self.protocol("WM_DELETE_WINDOW", lambda: self._finish(None))
        self.bind("<Escape>", lambda _e: self._finish(buttons[0][1] if len(buttons) == 1 else None))
        self.bind("<Return>", lambda _e: self._finish(buttons[-1][1]))

        self.update_idletasks()
        # Height follows content; set a sensible width
        self.geometry(f"420x{max(180, self.winfo_reqheight())}")
        self.after(10, lambda: _center_on_parent(self, master))

    def _finish(self, value: str | None) -> None:
        self.result = value
        self.grab_release()
        self.destroy()


def _run_dialog(dialog: _MessageDialog) -> str | None:
    dialog.wait_window()
    return dialog.result


def show_info(master, title: str, message: str) -> None:
    _run_dialog(_MessageDialog(master, title=title, message=message, kind="info"))


def show_warning(master, title: str, message: str) -> None:
    _run_dialog(_MessageDialog(master, title=title, message=message, kind="warning"))


def show_error(master, title: str, message: str) -> None:
    _run_dialog(_MessageDialog(master, title=title, message=message, kind="error"))


def ask_yes_no(master, title: str, message: str) -> bool:
    result = _run_dialog(
        _MessageDialog(
            master,
            title=title,
            message=message,
            kind="confirm",
            buttons=(("No", "no"), ("Yes", "yes")),
        )
    )
    return result == "yes"
