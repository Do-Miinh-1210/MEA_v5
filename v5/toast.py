"""
v5/toast.py — Toast notification widget cho v5.

Hiển thị popup nhỏ ở góc dưới-phải cửa sổ, tự fade-out sau N giây.
Cũng lưu LỊCH SỬ vào memory để Notification Center xem lại.

Usage:
    from v5.toast import show_toast, get_history, clear_history
    show_toast(parent, "✓ Đã lưu thay đổi", kind="success")
"""
from __future__ import annotations

from datetime import datetime
from collections import deque

import customtkinter as ctk

from v5.ui_perf import TOAST_FADE_INTERVAL_MS

# Track active toasts (đang hiển thị) để stack theo chiều dọc
_active_toasts: list = []
_MAX_ACTIVE = 5    # max toast hiện đồng thời — vượt sẽ pop cái cũ nhất

# History lưu max 50 toast gần nhất (memory only, không persist)
_HISTORY_MAX = 50
_history: deque = deque(maxlen=_HISTORY_MAX)


def get_history() -> list[dict]:
    """Trả về copy của history (mới nhất trước)."""
    return list(reversed(_history))


def clear_history() -> None:
    _history.clear()


_STYLES = {
    "success": {"bg": "#10B981", "fg": "white",  "icon": "✓"},
    "info":    {"bg": "#3B82F6", "fg": "white",  "icon": "ℹ"},
    "warn":    {"bg": "#F59E0B", "fg": "white",  "icon": "⚠"},
    "error":   {"bg": "#EF4444", "fg": "white",  "icon": "✘"},
}


class Toast(ctk.CTkToplevel):
    """Borderless toast widget — popup, auto-dismiss."""

    WIDTH  = 288
    HEIGHT = 44
    ACTION_WIDTH = 360
    ACTION_HEIGHT = 52
    MARGIN_RIGHT  = 14
    MARGIN_BOTTOM = 14
    SPACING = 5

    def __init__(self, parent, message: str, *, kind: str = "info",
                  duration: int = 3,
                  action_label: str | None = None,
                  action_cb=None):
        super().__init__(parent)
        # Alpha 23c: ẩn khỏi taskbar Windows + Alt+Tab
        try: self.wm_title("")
        except Exception: pass
        try:
            if parent is not None:
                self.transient(parent)
        except Exception: pass
        try: self.attributes("-toolwindow", True)
        except Exception: pass
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)

        style = _STYLES.get(kind, _STYLES["info"])
        self.configure(fg_color=style["bg"])
        if action_label:
            self.WIDTH = self.ACTION_WIDTH
            self.HEIGHT = self.ACTION_HEIGHT
        elif len(str(message or "")) > 44:
            self.HEIGHT = 52

        # Khóa kích thước compact để CTk/Windows không tự phóng to Toplevel.
        try:
            self.resizable(False, False)
            self.maxsize(self.WIDTH, self.HEIGHT)
            self.minsize(self.WIDTH, self.HEIGHT)
        except Exception: pass

        # Layout: icon | message [ | action_btn ]
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(wrap, text=style["icon"],
                      font=("Segoe UI", 16, "bold"),
                      text_color=style["fg"]
                      ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(wrap, text=message,
                      font=("Segoe UI", 10),
                      text_color=style["fg"],
                      anchor="w",
                      wraplength=(214 if not action_label else 214),
                      justify="left"
                      ).pack(side="left", fill="x", expand=True)
        if action_label and action_cb:
            def _run_action():
                try: action_cb()
                except Exception as e: print(f"toast action fail: {e}")
                self._dismiss()
            ctk.CTkButton(wrap, text=action_label, width=76, height=24,
                            font=("Segoe UI", 10, "bold"),
                            fg_color="white", text_color=style["bg"],
                            hover_color="#F3F4F6",
                            command=_run_action
                            ).pack(side="right", padx=(8, 0))

        # n25: Click toast (toàn bộ frame) → dismiss ngay
        # Skip nếu có action button — user có thể muốn đọc + click button
        if not action_label:
            for w in (self, wrap):
                try: w.bind("<Button-1>", lambda e: self._dismiss())
                except Exception: pass
            # Cursor pointer để hint
            try: self.configure(cursor="hand2")
            except Exception: pass

        # Position
        self._parent = parent
        _active_toasts.append(self)
        _reposition_active_toasts(parent)
        self.after(50, lambda: _reposition_active_toasts(parent))

        # Fade in
        self._fade(in_=True)

        # Auto-dismiss
        self.after(duration * 1000, self._dismiss)

    def _reposition(self, parent):
        """Stack compact ở góc dưới-phải, toast mới nhất nằm sát đáy."""
        try:
            ax_right  = parent.winfo_rootx() + parent.winfo_width()
            ay_bottom = parent.winfo_rooty() + parent.winfo_height()
        except Exception:
            ax_right  = self.winfo_screenwidth()
            ay_bottom = self.winfo_screenheight()

        actual_w = self.WIDTH
        actual_h = self.HEIGHT

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        TASKBAR_MARGIN = 48

        x = ax_right - actual_w - self.MARGIN_RIGHT
        if x + actual_w > sw - 8:
            x = sw - actual_w - 8
        if x < 8: x = 8

        try:
            stack_index = max(0, len(_active_toasts) - 1 - _active_toasts.index(self))
        except ValueError:
            stack_index = 0
        base_y = min(ay_bottom, sh - TASKBAR_MARGIN)
        y = (base_y - self.MARGIN_BOTTOM - actual_h
              - stack_index * (actual_h + self.SPACING))
        if y + actual_h > sh - TASKBAR_MARGIN:
            y = sh - TASKBAR_MARGIN - actual_h
        if y < 8: y = 8

        self.geometry(f"{actual_w}x{actual_h}+{x}+{y}")

    def _fade(self, in_: bool, alpha: float | None = None):
        """Fade in/out animation."""
        if alpha is None:
            alpha = 0.0 if in_ else 0.95
        step = 0.10 if in_ else -0.10
        target = 0.95 if in_ else 0.0

        try:
            self.attributes("-alpha", alpha)
        except Exception: return

        if (in_ and alpha < target) or (not in_ and alpha > target):
            self.after(TOAST_FADE_INTERVAL_MS, lambda: self._fade(in_, alpha + step))
        elif not in_:
            try: self.destroy()
            except Exception: pass

    def _dismiss(self):
        if self in _active_toasts:
            _active_toasts.remove(self)
            _reposition_active_toasts(self._parent)
        self._fade(in_=False)


def _reposition_active_toasts(parent) -> None:
    for toast in list(_active_toasts):
        try:
            toast._reposition(parent)
        except Exception:
            pass


def show_toast(parent, message: str, *,
                kind: str = "info", duration: int = 3,
                action_label: str | None = None,
                action_cb=None):
    """Tạo và hiển thị 1 toast. Tự stack + log vào history.

    kind: 'success' | 'info' | 'warn' | 'error'
    duration: seconds trước khi auto-dismiss
    action_label/action_cb: optional button bên phải toast (vd "Tải về")
    """
    # Push vào history TRƯỚC (kể cả khi parent chưa ready)
    _history.append({
        "ts": datetime.now().strftime("%H:%M:%S"),
        "kind": kind,
        "message": message,
    })
    # Queue limit: nếu đã có >= _MAX_ACTIVE toast → dismiss cái cũ nhất
    # để tránh stack chồng quá nhiều
    while len(_active_toasts) >= _MAX_ACTIVE:
        try:
            old = _active_toasts[0]
            old._dismiss()
        except Exception:
            # Force pop nếu dismiss fail
            try: _active_toasts.pop(0)
            except Exception: break
    try:
        Toast(parent, message, kind=kind, duration=duration,
               action_label=action_label, action_cb=action_cb)
    except Exception as e:
        print(f"Toast fail: {e}")


class NotificationCenter(ctk.CTkToplevel):
    """Panel hiển thị 50 toast gần nhất, popup từ statusbar."""

    WIDTH = 420
    HEIGHT = 520

    def __init__(self, parent):
        super().__init__(parent)
        # Alpha 23c: ẩn khỏi taskbar (transient + toolwindow)
        try: self.wm_title("")
        except Exception: pass
        try:
            if parent is not None: self.transient(parent)
        except Exception: pass
        try: self.attributes("-toolwindow", True)
        except Exception: pass
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=("#FFFFFF", "#1E293B"))

        # Position: góc dưới-phải cửa sổ chính, CLAMP trong screen
        # (Alpha 23c: thêm TASKBAR_MARGIN 60px để không che bởi taskbar).
        try:
            parent.update_idletasks()
            ax_right = parent.winfo_rootx() + parent.winfo_width()
            ay_bottom = parent.winfo_rooty() + parent.winfo_height()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            TASKBAR_MARGIN = 60
            # X: clamp trong screen
            x = ax_right - self.WIDTH - 8
            if x + self.WIDTH > sw - 8: x = sw - self.WIDTH - 8
            if x < 8: x = 8
            # Y: dưới đáy app nhưng không vượt taskbar
            base_y = min(ay_bottom, sh - TASKBAR_MARGIN)
            y = base_y - self.HEIGHT - 40
            if y + self.HEIGHT > sh - TASKBAR_MARGIN:
                y = sh - TASKBAR_MARGIN - self.HEIGHT
            if y < 8: y = 8
            self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        except Exception:
            self.geometry(f"{self.WIDTH}x{self.HEIGHT}+200+200")

        border = ctk.CTkFrame(self, fg_color=("#3B82F6", "#3B82F6"),
                                corner_radius=10)
        border.pack(fill="both", expand=True, padx=1, pady=1)
        inner = ctk.CTkFrame(border, fg_color=("#FFFFFF", "#1E293B"),
                                corner_radius=9)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Header — nút ✕ to + đậm để dễ thấy (Alpha 22 fix: trước nhỏ
        # và chìm nên user không tìm thấy)
        hdr = ctk.CTkFrame(inner, fg_color=("#F3F4F6", "#0F172A"),
                            corner_radius=8, height=44)
        hdr.pack(fill="x", padx=4, pady=(4, 4))
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🔔  Thông báo gần đây",
                      font=("Segoe UI", 13, "bold"),
                      anchor="w"
                      ).pack(side="left", padx=12)
        ctk.CTkButton(hdr, text="✕  Đóng",
                       width=80, height=30,
                       font=("Segoe UI", 11, "bold"),
                       fg_color=("#DC2626", "#991B1B"),
                       hover_color=("#B91C1C", "#7F1D1D"),
                       text_color="white",
                       command=self._close).pack(side="right", padx=6)
        ctk.CTkButton(hdr, text="🗑 Clear", width=80, height=30,
                       fg_color="#6B7280", hover_color="#4B5563",
                       font=("Segoe UI", 11),
                       command=self._clear).pack(side="right", padx=2)

        # Scrollable list
        self._list = ctk.CTkScrollableFrame(
            inner, fg_color=("#F9FAFB", "#0F172A"))
        self._list.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        self._render()

        # Đóng: Escape, click ra ngoài (FocusOut), hoặc tự đóng sau 12s
        self.bind("<Escape>", lambda e: self._close())
        self.bind("<FocusOut>", lambda e: self.after(200, self._maybe_close))
        try: self.focus_force()
        except: pass
        # Auto-close để không che nội dung nếu user quên đóng
        try: self.after(12000, self._close)
        except: pass

    def _render(self):
        for c in self._list.winfo_children(): c.destroy()
        hist = get_history()
        if not hist:
            ctk.CTkLabel(self._list, text="(Chưa có thông báo nào)",
                          text_color="gray", font=("Segoe UI", 11)
                          ).pack(pady=40)
            return
        colors = {
            "success": "#10B981", "info": "#3B82F6",
            "warn": "#F59E0B",    "error": "#EF4444",
        }
        for item in hist:
            row = ctk.CTkFrame(self._list,
                                  fg_color=("#FFFFFF", "#293548"),
                                  corner_radius=6, border_width=1,
                                  border_color=("#E5E7EB", "#334155"))
            row.pack(fill="x", padx=4, pady=2)
            # Bar màu trái
            ctk.CTkFrame(row, fg_color=colors.get(item["kind"], "#3B82F6"),
                          width=4, corner_radius=2
                          ).pack(side="left", fill="y", padx=(4, 6), pady=4)
            txt = ctk.CTkFrame(row, fg_color="transparent")
            txt.pack(side="left", fill="x", expand=True, pady=4)
            ctk.CTkLabel(txt, text=item["message"],
                          anchor="w", justify="left",
                          wraplength=320, font=("Segoe UI", 11)
                          ).pack(anchor="w", padx=4)
            ctk.CTkLabel(txt, text=f"  {item['ts']}",
                          text_color="gray", anchor="w",
                          font=("Segoe UI", 9)
                          ).pack(anchor="w", padx=4)

    def _clear(self):
        clear_history()
        self._render()

    def _close(self):
        try: self.destroy()
        except: pass

    def _maybe_close(self):
        try:
            if self.focus_get() is None:
                self._close()
        except: pass
