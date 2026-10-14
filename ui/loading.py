"""
ui/loading.py — Loading indicators cho UI.
Cung cấp: spinner overlay, skeleton frames, progress helpers.
Giúp user thấy feedback ngay lập tức khi app đang xử lý.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import threading


class LoadingOverlay:
    """
    Overlay mờ + spinner hiện trên widget khi đang xử lý.

    Usage:
        overlay = LoadingOverlay(parent_frame, text="Đang tải dữ liệu...")
        overlay.show()
        # ... do work ...
        overlay.hide()

    Hoặc dùng context manager:
        with LoadingOverlay(parent, "Đang xử lý..."):
            heavy_work()
    """

    def __init__(self, parent: tk.Widget, text: str = "Đang xử lý...", bg: str = "#F8FAFC"):
        self._parent = parent
        self._text = text
        self._bg = bg
        self._frame: Optional[tk.Frame] = None

    def show(self) -> None:
        if self._frame:
            return
        self._frame = tk.Frame(self._parent, bg=self._bg)
        self._frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._frame.lift()

        # Spinner text (animated dots)
        self._lbl = tk.Label(
            self._frame, text=self._text,
            font=("Segoe UI", 12), fg="#64748B", bg=self._bg,
        )
        self._lbl.place(relx=0.5, rely=0.45, anchor="center")

        # Progress bar
        self._pb = ttk.Progressbar(
            self._frame, mode="indeterminate", length=200,
        )
        self._pb.place(relx=0.5, rely=0.55, anchor="center")
        self._pb.start(15)

        self._frame.update_idletasks()

    def hide(self) -> None:
        if self._frame:
            try:
                self._pb.stop()
                self._frame.destroy()
            except Exception:
                pass
            self._frame = None

    def set_text(self, text: str) -> None:
        if self._lbl:
            try:
                self._lbl.config(text=text)
            except Exception:
                pass

    def __enter__(self):
        self.show()
        return self

    def __exit__(self, *args):
        self.hide()


class SkeletonFrame(tk.Frame):
    """
    Skeleton UI — hiển thị khung xám nhấp nháy trong lúc load data.
    Giống Facebook/YouTube loading state.

    Usage:
        skeleton = SkeletonFrame(parent, rows=5, col_widths=[200, 100, 300])
        skeleton.pack(fill="both", expand=True)
        # When data loaded:
        skeleton.destroy()
    """

    def __init__(self, parent, rows: int = 5, col_widths: list[int] = None, **kwargs):
        super().__init__(parent, bg="#F8FAFC", **kwargs)
        widths = col_widths or [200, 150, 300]
        self._bars: list[tk.Frame] = []

        for r in range(rows):
            row_frame = tk.Frame(self, bg="#F8FAFC")
            row_frame.pack(fill="x", padx=16, pady=4)
            for w in widths:
                bar = tk.Frame(row_frame, bg="#E2E8F0", height=14, width=w)
                bar.pack(side="left", padx=4)
                bar.pack_propagate(False)
                self._bars.append(bar)

        # Animate: fade in/out
        self._alpha = 0.4
        self._direction = 1
        self._animate()

    def _animate(self) -> None:
        try:
            self._alpha += 0.05 * self._direction
            if self._alpha >= 0.9:
                self._direction = -1
            elif self._alpha <= 0.4:
                self._direction = 1

            # Simulate opacity with color interpolation
            gray = int(226 + (248 - 226) * (1 - self._alpha))  # E2 to F8
            color = f"#{gray:02x}{gray:02x}{gray:02x}"
            for bar in self._bars:
                bar.configure(bg=color)

            self.after(80, self._animate)
        except tk.TclError:
            pass  # Widget destroyed


def run_with_loading(
    parent: tk.Widget,
    task: Callable,
    on_done: Optional[Callable] = None,
    on_error: Optional[Callable] = None,
    text: str = "Đang xử lý...",
) -> None:
    """
    Helper: hiện loading overlay, chạy task ở background, ẩn overlay khi xong.

    Usage:
        run_with_loading(
            self, task=lambda: api_call(),
            on_done=lambda result: show_result(result),
            text="Đang gọi API..."
        )
    """
    overlay = LoadingOverlay(parent, text)
    overlay.show()

    def _worker():
        try:
            result = task()
            parent.after(0, lambda r=result: _finish(r, None))
        except Exception as e:
            err = e
            parent.after(0, lambda x=err: _finish(None, x))

    def _finish(result, error):
        overlay.hide()
        if error:
            if on_error:
                on_error(error)
        else:
            if on_done:
                on_done(result)

    threading.Thread(target=_worker, daemon=True).start()
