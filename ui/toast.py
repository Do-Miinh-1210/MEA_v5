"""
ui/toast.py — Toast notification widget cho MEA.

Non-modal, floating overlay ở góc dưới-phải cửa sổ chính. Tự fade-out sau N
giây hoặc khi user click X. Hỗ trợ action buttons (vd: "Đổi vị trí", "Lưu
thêm bản", "Tắt auto-export").

Dùng cho:
  • Báo xuất Word thành công + cho phép user override hành vi
  • Thông báo lưu NHCH / hết hạn / có update mới
  • Bất cứ feedback non-blocking nào

API:
    >>> toast = Toast(parent, title="✅ Đã xuất Word",
    ...               message="MEA_exam_20260512.docx",
    ...               actions=[
    ...                   ("📂 Đổi vị trí", on_relocate),
    ...                   ("➕ Lưu thêm bản", on_duplicate),
    ...               ],
    ...               duration_ms=10000)
    >>> toast.show()
"""

from __future__ import annotations
import tkinter as tk
from typing import Callable, Optional


# ── Color palette (khớp theme app) ──────────────────────────────────────────
_BG_SURFACE = "#FFFFFF"
_BG_HEADER  = "#ECFDF5"   # green-50 — success
_FG_TITLE   = "#065F46"   # green-800
_FG_BODY    = "#334155"   # slate-700
_FG_DIM     = "#64748B"   # slate-500
_BORDER     = "#10B981"   # emerald-500
_BTN_BG     = "#0EA5E9"
_BTN_HOVER  = "#0284C7"


class Toast:
    """Toast notification — floating, non-modal, auto-dismiss.

    Parameters
    ----------
    parent:       Tk root / Toplevel làm anchor (toast bám góc dưới-phải).
    title:        Tiêu đề ngắn (vd: "✅ Đã xuất Word").
    message:      Nội dung chính (multi-line OK).
    actions:      List[(label, callback)] — mỗi action 1 nút bấm.
                  Callback nhận () — toast tự đóng SAU khi callback chạy.
                  Để None nếu không muốn đóng tự động.
    duration_ms:  Thời gian tự đóng (ms). 0 = chỉ đóng khi user click X.
    variant:      "success" | "info" | "warning" | "error" — đổi màu border.
    """

    _VARIANTS = {
        "success": ("#ECFDF5", "#065F46", "#10B981"),
        "info":    ("#EFF6FF", "#1E40AF", "#3B82F6"),
        "warning": ("#FFFBEB", "#92400E", "#F59E0B"),
        "error":   ("#FEF2F2", "#991B1B", "#EF4444"),
    }

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        message: str = "",
        actions: Optional[list[tuple[str, Optional[Callable]]]] = None,
        duration_ms: int = 10_000,
        variant: str = "success",
    ):
        self._parent = parent
        self._title = title
        self._message = message
        self._actions = actions or []
        self._duration_ms = duration_ms
        self._variant = variant if variant in self._VARIANTS else "success"
        self._win: Optional[tk.Toplevel] = None
        self._after_id: Optional[str] = None

    # ──────────────────────────────────────────────────────────────────────
    def show(self) -> None:
        """Hiển thị toast. Idempotent — gọi nhiều lần chỉ tạo 1 toast."""
        if self._win is not None and self._win.winfo_exists():
            return

        hdr_bg, fg_title, border = self._VARIANTS[self._variant]

        win = tk.Toplevel(self._parent)
        win.overrideredirect(True)        # Không title-bar / nút X hệ thống
        win.attributes("-topmost", True)
        win.configure(bg=border)          # outer = border color
        try:
            win.attributes("-alpha", 0.0)  # fade-in
        except tk.TclError:
            pass

        # Inner frame (cách border 2px tạo viền)
        inner = tk.Frame(win, bg=_BG_SURFACE, bd=0)
        inner.pack(padx=2, pady=2, fill="both", expand=True)

        # ── Header ──
        hdr = tk.Frame(inner, bg=hdr_bg)
        hdr.pack(fill="x")

        tk.Label(
            hdr, text=self._title,
            bg=hdr_bg, fg=fg_title,
            font=("Segoe UI", 10, "bold"),
            anchor="w", padx=12, pady=6,
        ).pack(side="left", fill="x", expand=True)

        # Nút X đóng
        close_btn = tk.Label(
            hdr, text="✕",
            bg=hdr_bg, fg=fg_title,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2", padx=10, pady=4,
        )
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda _e: self.dismiss())

        # ── Message body ──
        if self._message:
            body = tk.Label(
                inner,
                text=self._message,
                bg=_BG_SURFACE, fg=_FG_BODY,
                font=("Segoe UI", 9),
                anchor="w", justify="left",
                padx=12, pady=8,
                wraplength=380,
            )
            body.pack(fill="x")

        # ── Action buttons ──
        if self._actions:
            act_row = tk.Frame(inner, bg=_BG_SURFACE)
            act_row.pack(fill="x", padx=8, pady=(0, 8))
            for label, cb in self._actions:
                btn = tk.Button(
                    act_row,
                    text=label,
                    bg=_BTN_BG, fg="white",
                    activebackground=_BTN_HOVER, activeforeground="white",
                    font=("Segoe UI", 8, "bold"),
                    relief="flat", bd=0, cursor="hand2",
                    padx=10, pady=4,
                    command=lambda c=cb: self._on_action(c),
                )
                btn.pack(side="left", padx=2)

        self._win = win

        # ── Position bottom-right of parent ──
        win.update_idletasks()
        self._position()

        # Fade-in animation
        self._fade_in()

        # Auto-dismiss timer
        if self._duration_ms > 0:
            self._after_id = win.after(self._duration_ms, self.dismiss)

    # ──────────────────────────────────────────────────────────────────────
    def _on_action(self, cb: Optional[Callable]) -> None:
        """Gọi callback rồi tự đóng. Callback bắt exception riêng."""
        try:
            if cb is not None:
                cb()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Toast action failed: %s", e)
        finally:
            self.dismiss()

    # ──────────────────────────────────────────────────────────────────────
    def _position(self) -> None:
        """Đặt toast ở góc dưới-phải parent. Lề 20px."""
        if not self._win:
            return
        try:
            # Lấy toạ độ parent
            try:
                p_x = self._parent.winfo_rootx()
                p_y = self._parent.winfo_rooty()
                p_w = self._parent.winfo_width()
                p_h = self._parent.winfo_height()
            except Exception:
                # Fallback: dùng screen
                p_x, p_y = 0, 0
                p_w = self._win.winfo_screenwidth()
                p_h = self._win.winfo_screenheight()

            w = self._win.winfo_width()
            h = self._win.winfo_height()
            margin = 20
            x = p_x + p_w - w - margin
            y = p_y + p_h - h - margin
            # Đảm bảo không ra ngoài screen
            x = max(0, x)
            y = max(0, y)
            self._win.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

    # ──────────────────────────────────────────────────────────────────────
    def _fade_in(self, step: int = 0) -> None:
        """Tăng alpha từ 0 → 1 trong ~150ms."""
        if not self._win or not self._win.winfo_exists():
            return
        try:
            alpha = min(1.0, step * 0.15)
            self._win.attributes("-alpha", alpha)
            if alpha < 1.0:
                self._win.after(20, lambda: self._fade_in(step + 1))
        except tk.TclError:
            pass

    # ──────────────────────────────────────────────────────────────────────
    def dismiss(self) -> None:
        """Đóng toast (idempotent)."""
        if self._after_id is not None:
            try:
                if self._win:
                    self._win.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self._win is not None:
            try:
                if self._win.winfo_exists():
                    self._win.destroy()
            except tk.TclError:
                pass
            self._win = None


# ── Convenience functions ─────────────────────────────────────────────────

def show_success(parent, title: str, message: str = "", **kw) -> Toast:
    t = Toast(parent, title=title, message=message, variant="success", **kw)
    t.show()
    return t


def show_info(parent, title: str, message: str = "", **kw) -> Toast:
    t = Toast(parent, title=title, message=message, variant="info", **kw)
    t.show()
    return t


def show_warning(parent, title: str, message: str = "", **kw) -> Toast:
    t = Toast(parent, title=title, message=message, variant="warning", **kw)
    t.show()
    return t


def show_error(parent, title: str, message: str = "", **kw) -> Toast:
    t = Toast(parent, title=title, message=message, variant="error", **kw)
    t.show()
    return t
