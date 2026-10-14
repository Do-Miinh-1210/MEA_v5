"""
v5/splash.py — Splash screen hiển thị khi v5 khởi động.

Show 1.5-3s while main app initializes:
    • Logo + tên app
    • Version
    • Loading bar indeterminate
    • Step messages: "Loading config..." → "Loading views..." → "Ready!"

Auto-close khi MainApp đã sẵn sàng (gọi splash.finish()).
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path

from v5 import __version__


class SplashScreen(tk.Toplevel):
    """Splash window — borderless, centered, 480×280."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.overrideredirect(True)         # bỏ title bar
        self.attributes("-topmost", True)
        self.configure(bg="#1F497D")

        # Center
        w, h = 480, 280
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        # Container
        wrap = tk.Frame(self, bg="#1F497D", padx=24, pady=20)
        wrap.pack(fill="both", expand=True)

        # Logo (π emoji as fallback nếu không có file)
        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo_1.png"
        try:
            from PIL import Image, ImageTk
            if logo_path.exists():
                img = Image.open(logo_path).resize((80, 80), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                tk.Label(wrap, image=self._logo_img, bg="#1F497D"
                          ).pack(pady=(8, 4))
            else:
                tk.Label(wrap, text="π", font=("Segoe UI", 60, "bold"),
                          fg="white", bg="#1F497D").pack(pady=(0, 4))
        except Exception:
            tk.Label(wrap, text="π", font=("Segoe UI", 60, "bold"),
                      fg="white", bg="#1F497D").pack(pady=(0, 4))

        # App name
        tk.Label(wrap, text="MatrixExam AI",
                  font=("Segoe UI", 18, "bold"),
                  fg="white", bg="#1F497D").pack()
        tk.Label(wrap, text=f"v{__version__}  •  Modern UI (CustomTkinter)",
                  font=("Segoe UI", 9), fg="#93C5FD",
                  bg="#1F497D").pack(pady=(2, 16))

        # Status label
        self._status_var = tk.StringVar(value="Khởi động...")
        tk.Label(wrap, textvariable=self._status_var,
                  font=("Segoe UI", 10), fg="#E2E8F0",
                  bg="#1F497D").pack(pady=(0, 2))

        # Progress bar (determinate, manual set_progress)
        from tkinter import ttk
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
            style.configure("SplashPB.Horizontal.TProgressbar",
                              troughcolor="#0B1F35",
                              bordercolor="#1F497D",
                              background="#3B82F6",
                              lightcolor="#3B82F6",
                              darkcolor="#3B82F6")
        except Exception: pass
        self._pb = ttk.Progressbar(wrap, mode="determinate", length=380,
                                      maximum=100, value=0,
                                      style="SplashPB.Horizontal.TProgressbar")
        self._pb.pack(pady=(0, 0))
        self._current_progress = 0

        # Percent label dưới bar
        self._pct_var = tk.StringVar(value="0%")
        tk.Label(wrap, textvariable=self._pct_var,
                  font=("Segoe UI", 9), fg="#93C5FD",
                  bg="#1F497D").pack(pady=(2, 4))

        # Footer
        tk.Label(wrap, text="© 2026 DoMiinhMath  •  Click để bỏ qua",
                  font=("Segoe UI", 8), fg="#64748B",
                  bg="#1F497D").pack(side="bottom", pady=(8, 0))

        # n23: Click bất kỳ đâu trên splash → skip ngay
        for w in (self, wrap):
            try: w.bind("<Button-1>", lambda e: self.finish())
            except Exception: pass

        self.update()

    def set_status(self, msg: str, pct: int | None = None):
        """Update status + optional progress percentage."""
        self._status_var.set(msg)
        if pct is not None:
            self.set_progress(pct)
        try: self.update()
        except tk.TclError: pass

    def set_progress(self, pct: int):
        """Set progress 0-100. Animate smoothly từ current → target."""
        target = max(0, min(100, int(pct)))
        # Animate trong vài frame (3-5 steps) cho mượt
        try:
            self._animate_to(target, step=0)
        except Exception:
            try:
                self._pb["value"] = target
                self._pct_var.set(f"{target}%")
                self.update()
            except tk.TclError: pass

    def _animate_to(self, target: int, step: int = 0, max_steps: int = 6):
        try:
            current = self._current_progress
            if step >= max_steps or current == target:
                self._current_progress = target
                self._pb["value"] = target
                self._pct_var.set(f"{target}%")
                try: self.update()
                except tk.TclError: pass
                return
            new = current + (target - current) // max(1, max_steps - step)
            if new == current and target != current:
                new = target
            self._current_progress = new
            self._pb["value"] = new
            self._pct_var.set(f"{new}%")
            try:
                self.update()
                self.after(20, lambda: self._animate_to(target, step + 1, max_steps))
            except tk.TclError: pass
        except Exception: pass

    def finish(self):
        """Set 100% then destroy."""
        try:
            self.set_progress(100)
            self.after(120, self.destroy)
        except tk.TclError:
            pass


def show_splash(parent=None) -> SplashScreen:
    """Tạo và hiển thị splash. Caller gọi `.finish()` khi app ready."""
    return SplashScreen(parent)
