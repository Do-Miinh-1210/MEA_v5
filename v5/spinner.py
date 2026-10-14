"""
v5/spinner.py — Loading spinner overlay.

Dùng khi long operation (Generate exam, QC pipeline, Push LMS).

Usage:
    from v5.spinner import LoadingOverlay
    overlay = LoadingOverlay(parent, "Đang sinh đề...")
    # ... do work ...
    overlay.close()

Hoặc context manager:
    with LoadingOverlay(parent, "Đang tải..."):
        ... long work ...
"""
from __future__ import annotations

import customtkinter as ctk

from v5.ui_perf import ANIMATION_INTERVAL_MS


# Frames spinner — vòng quay 12 step
_SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class LoadingOverlay(ctk.CTkToplevel):
    """Modal overlay với spinner + message — block input parent."""

    SIZE = (320, 140)

    def __init__(self, parent, message: str = "Đang xử lý..."):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=("#FFFFFF", "#1E293B"))

        # Border effect
        border = ctk.CTkFrame(self, fg_color=("#3B82F6", "#3B82F6"),
                                corner_radius=12)
        border.pack(fill="both", expand=True, padx=2, pady=2)
        inner = ctk.CTkFrame(border, fg_color=("#FFFFFF", "#1E293B"),
                                corner_radius=10)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        # Spinner label
        self._spin_lbl = ctk.CTkLabel(
            inner, text="⠋",
            font=("Segoe UI", 36),
            text_color="#3B82F6")
        self._spin_lbl.pack(pady=(16, 4))

        # Message
        self._msg_var = ctk.StringVar(value=message)
        ctk.CTkLabel(inner, textvariable=self._msg_var,
                      font=("Segoe UI", 11),
                      text_color=("#1F2937", "#F1F5F9"),
                      wraplength=280
                      ).pack(pady=(0, 8), padx=12)

        # Sub-message (cho progress detail)
        self._sub_var = ctk.StringVar()
        ctk.CTkLabel(inner, textvariable=self._sub_var,
                      font=("Segoe UI", 9),
                      text_color=("#6B7280", "#94A3B8"),
                      wraplength=280
                      ).pack(pady=(0, 12), padx=12)

        # Center
        self._center(parent)

        # Bắt đầu animate
        self._step = 0
        self._active = True
        self._animate()

        # Block parent input
        try: self.grab_set()
        except Exception: pass

    def _center(self, parent):
        try:
            parent.update_idletasks()
            px = parent.winfo_rootx() + parent.winfo_width() // 2
            py = parent.winfo_rooty() + parent.winfo_height() // 2
            w, h = self.SIZE
            self.geometry(f"{w}x{h}+{px - w//2}+{py - h//2}")
        except Exception:
            self.geometry(f"{self.SIZE[0]}x{self.SIZE[1]}+100+100")

    def _animate(self):
        if not self._active:
            return
        try:
            self._spin_lbl.configure(text=_SPINNER_CHARS[self._step])
            self._step = (self._step + 1) % len(_SPINNER_CHARS)
            self.after(ANIMATION_INTERVAL_MS, self._animate)
        except Exception:
            pass

    def set_message(self, msg: str):
        """Update main message text."""
        self._msg_var.set(msg)

    def set_sub(self, sub: str):
        """Update sub message (vd progress detail)."""
        self._sub_var.set(sub)

    def close(self):
        self._active = False
        try:
            self.grab_release()
            self.destroy()
        except Exception: pass

    # Context manager
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
