"""
v5/quickswitch.py — Quick switcher (Ctrl+T) như VSCode command palette.

Popup nhỏ ở giữa cửa sổ với:
    • Input box fuzzy search
    • List 8 view + recent files + action shortcuts
    • Arrow keys điều hướng, Enter chọn, Esc đóng
"""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk


# Items mặc định: 8 view + actions
_DEFAULT_ITEMS = [
    ("view",   "home",        "🏠  Trang chủ"),
    ("view",   "setup",       "⚙️  Cấu hình"),
    ("view",   "exam_create", "✏️  Tạo đề"),
    ("view",   "nhch",        "🏛  Ngân hàng câu hỏi"),
    ("view",   "convert",     "🔄  Convert câu hỏi"),
    ("view",   "qc",          "✅  QC chất lượng"),
    ("view",   "tracking",    "📊  Theo dõi & Thống kê"),
    ("view",   "guide",       "📖  Hướng dẫn sử dụng"),
    ("action", "F1",          "❓  Hiển thị phím tắt (F1)"),
    ("action", "theme",       "🎨  Đổi theme (Light/Dark)"),
    ("action", "collapse",    "☰  Toggle sidebar collapse"),
    ("action", "import",      "📄  Mở Import Wizard"),
    ("action", "smart_prompt","💬  Smart Prompt (tạo đề/câu hỏi từ mô tả)"),
    ("action", "quick_gen",   "🚀  Tạo đề nhanh (theo thời lượng / số câu)"),
    ("action", "ai_gen_matrix","🤖  AI tạo ma trận (form môn/lớp/HK)"),
    ("action", "exam_history","🕒  Lịch sử phiên bản đề"),
    ("action", "nhch_stats",  "📊  Thống kê ngân hàng câu hỏi"),
    ("action", "task_log",    "📋  Nhật ký tác vụ + Cache AI"),
    ("action", "prefs",       "⚙  Tuỳ chọn (Ctrl+,)"),
    ("action", "check_update","🔄  Kiểm tra cập nhật"),
    ("action", "whats_new",   "✨  Có gì mới (changelog)"),
    ("action", "crash_log",   "🛡  Xem lịch sử lỗi (crash log)"),
    ("action", "about",       "ℹ  Về MEA v5"),
    ("action", "quit",        "🚪  Thoát app (Ctrl+Q)"),
]


def _fuzzy_match(query: str, text: str) -> int:
    """Fuzzy score: cao = match tốt hơn. 0 = không match."""
    q = query.lower().strip()
    t = text.lower()
    if not q:
        return 1   # show all if empty query
    if q in t:
        # Substring match: ưu tiên prefix
        return 1000 - t.index(q)
    # Subsequence match (mỗi char query xuất hiện theo thứ tự trong text)
    pos = 0; score = 0
    for ch in q:
        idx = t.find(ch, pos)
        if idx == -1: return 0
        score += (100 - (idx - pos))
        pos = idx + 1
    return score


class QuickSwitcher(ctk.CTkToplevel):
    """Modal popup: fuzzy search + navigate."""

    WIDTH = 540
    HEIGHT = 380

    def __init__(self, parent, *, on_navigate: Callable[[str], None],
                  on_action: Callable[[str], None] | None = None):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=("#FFFFFF", "#1E293B"))

        self._on_navigate = on_navigate
        self._on_action = on_action
        self._items = self._build_items()
        self._selected_idx = 0

        # Center
        try:
            parent.update_idletasks()
            px = parent.winfo_rootx() + parent.winfo_width() // 2
            py = parent.winfo_rooty() + 80
            self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{px - self.WIDTH//2}+{py}")
        except Exception:
            self.geometry(f"{self.WIDTH}x{self.HEIGHT}+200+200")

        # Border
        border = ctk.CTkFrame(self, fg_color=("#3B82F6", "#3B82F6"),
                                corner_radius=10)
        border.pack(fill="both", expand=True, padx=1, pady=1)
        inner = ctk.CTkFrame(border, fg_color=("#FFFFFF", "#1E293B"),
                                corner_radius=9)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Search input
        self._query_var = ctk.StringVar()
        self._entry = ctk.CTkEntry(
            inner, textvariable=self._query_var,
            placeholder_text="🔍  Tìm view / action…",
            height=44, font=("Segoe UI", 13),
            border_width=0, corner_radius=0,
            fg_color=("#F3F4F6", "#293548"))
        self._entry.pack(fill="x", padx=2, pady=(2, 0))
        self._query_var.trace_add("write", lambda *_: self._render())

        # Results list (scrollable)
        self._list_frame = ctk.CTkScrollableFrame(
            inner, fg_color=("#FFFFFF", "#1E293B"),
            corner_radius=0)
        self._list_frame.pack(fill="both", expand=True, padx=2, pady=(0, 2))

        # Hint footer
        ctk.CTkLabel(inner,
                      text="↑↓ điều hướng  •  Enter chọn  •  Esc đóng",
                      font=("Segoe UI", 9),
                      text_color=("#9CA3AF", "#64748B"),
                      fg_color=("#F3F4F6", "#293548"),
                      height=22
                      ).pack(fill="x", padx=2, pady=(0, 2))

        # Bindings
        self._entry.bind("<Return>",     lambda e: self._activate())
        self._entry.bind("<Escape>",     lambda e: self._close())
        self._entry.bind("<Down>",       lambda e: self._move(1))
        self._entry.bind("<Up>",         lambda e: self._move(-1))
        self.bind("<FocusOut>",          lambda e: self.after(150, self._maybe_close))

        try: self.grab_set()
        except: pass
        self._entry.focus_set()
        self._render()

    def _build_items(self):
        """Default items + recent files (max 5)."""
        items = list(_DEFAULT_ITEMS)
        try:
            from v5 import settings_store
            for p in settings_store.get_recent_files()[:5]:
                from pathlib import Path
                items.append(("recent", p, f"📄  {Path(p).name}"))
        except Exception: pass
        return items

    def _render(self):
        q = self._query_var.get()
        # Filter + score
        scored = []
        for kind, key, label in self._items:
            s = _fuzzy_match(q, label)
            if s > 0:
                scored.append((s, kind, key, label))
        scored.sort(key=lambda x: -x[0])
        self._filtered = scored[:12]
        # Reset selection
        if self._selected_idx >= len(self._filtered):
            self._selected_idx = max(0, len(self._filtered) - 1)
        # Render
        for c in self._list_frame.winfo_children():
            c.destroy()
        for i, (_, kind, key, label) in enumerate(self._filtered):
            # CTk không cho tuple ('transparent','transparent') → dùng string
            bg = (("#DBEAFE", "#1E3A8A") if i == self._selected_idx
                   else "transparent")
            row = ctk.CTkButton(
                self._list_frame, text=label, anchor="w",
                height=36, font=("Segoe UI", 12),
                fg_color=bg,
                text_color=("#1F2937", "#F1F5F9"),
                hover_color=("#BFDBFE", "#1E40AF"),
                corner_radius=4,
                command=lambda k=key, kd=kind: self._select_and_activate(kd, k))
            row.pack(fill="x", padx=2, pady=1)

    def _move(self, delta: int):
        if not self._filtered: return
        self._selected_idx = (self._selected_idx + delta) % len(self._filtered)
        self._render()

    def _activate(self):
        if not self._filtered: return
        _, kind, key, _ = self._filtered[self._selected_idx]
        self._select_and_activate(kind, key)

    def _select_and_activate(self, kind: str, key: str):
        self._close()
        if kind == "view":
            self._on_navigate(key)
        elif kind == "recent":
            # Mở Import wizard với file
            try:
                from pathlib import Path
                top = self.master
                while top and not hasattr(top, "_open_import_for"):
                    top = getattr(top, "master", None)
                if top and hasattr(top, "_open_import_for"):
                    top._open_import_for(Path(key))
            except Exception as e: print(f"recent action fail: {e}")
        elif kind == "action" and self._on_action:
            self._on_action(key)

    def _maybe_close(self):
        # Khi mất focus và không phải sang child
        try:
            if self.focus_get() is None or not str(self.focus_get()).startswith(str(self)):
                self._close()
        except Exception: pass

    def _close(self):
        try: self.grab_release()
        except: pass
        try: self.destroy()
        except: pass
