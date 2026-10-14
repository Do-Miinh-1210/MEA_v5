"""
ui/dropdown_recent.py — [SPEED-5] Dropdown menu "Mở lại đề gần đây".

Hiển thị 5 phiên gần nhất dạng popover bám dưới nút toolbar. Mỗi item là
1 card với: icon nguồn / title / metadata (lớp môn) / stats (số câu) /
thời gian (Hôm nay / Hôm qua / Thứ X / dd/mm/yyyy).

Click item → callback restore_cb(exam_data) — main_window load vào TabResult.

API:
    >>> dd = RecentExamsDropdown(parent_btn, on_restore=lambda exam: ...)
    >>> dd.show()  # popup dưới parent_btn
"""

from __future__ import annotations
import logging
import tkinter as tk
from typing import Callable, Optional

from services.exam_history import (
    list_recent_exams_with_meta, load_recent_as_examdata,
)

_log = logging.getLogger(__name__)


# ── Colors ────────────────────────────────────────────────────────────
_BG          = "#FFFFFF"
_BORDER      = "#CBD5E1"
_HOVER_BG    = "#EFF6FF"
_HEADER_BG   = "#F1F5F9"
_FG_TITLE    = "#0F172A"
_FG_BODY     = "#475569"
_FG_DIM      = "#94A3B8"
_FG_ACCENT   = "#1E40AF"

_SOURCE_ICONS = {
    "ai":     "✨",
    "manual": "✏️",
    "regen":  "🔁",
    "import": "📥",
    "":       "📄",
}


class RecentExamsDropdown:
    """Popover menu hiển thị 5 phiên gần nhất.

    Parameters
    ----------
    anchor:      Widget làm anchor — popup sẽ bám dưới-trái của widget này
    on_restore:  callback(exam_data: ExamData) khi user chọn 1 item
    limit:       số items hiển thị (mặc định 5)
    """

    def __init__(
        self,
        anchor: tk.Misc,
        on_restore: Callable,
        limit: int = 5,
    ):
        self._anchor = anchor
        self._on_restore = on_restore
        self._limit = limit
        self._win: Optional[tk.Toplevel] = None

    # ──────────────────────────────────────────────────────────────────
    def show(self) -> None:
        """Hiện dropdown. Idempotent — nếu đang mở thì đóng (toggle)."""
        if self._win is not None and self._win.winfo_exists():
            self.dismiss()
            return

        items = list_recent_exams_with_meta(limit=self._limit)

        win = tk.Toplevel(self._anchor)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=_BORDER)

        inner = tk.Frame(win, bg=_BG)
        inner.pack(padx=1, pady=1, fill="both", expand=True)

        # ── Header ──
        hdr = tk.Frame(inner, bg=_HEADER_BG)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="📂  Đề gần đây",
            bg=_HEADER_BG, fg=_FG_TITLE,
            font=("Segoe UI", 10, "bold"),
            anchor="w", padx=12, pady=6,
        ).pack(side="left", fill="x", expand=True)

        # Close X
        close = tk.Label(
            hdr, text="✕",
            bg=_HEADER_BG, fg=_FG_BODY,
            font=("Segoe UI", 11, "bold"),
            cursor="hand2", padx=10, pady=4,
        )
        close.pack(side="right")
        close.bind("<Button-1>", lambda _e: self.dismiss())

        # ── Items ──
        if not items:
            tk.Label(
                inner,
                text=("Chưa có đề nào.\n"
                      "Sau khi tạo đề bằng AI / load file, sẽ xuất hiện ở đây."),
                bg=_BG, fg=_FG_DIM,
                font=("Segoe UI", 9, "italic"),
                pady=24, padx=20, justify="center",
            ).pack(fill="x")
        else:
            for it in items:
                self._build_item(inner, it)

        # ── Footer ──
        ftr = tk.Frame(inner, bg=_HEADER_BG)
        ftr.pack(fill="x")
        tk.Label(
            ftr, text=f"  Hiển thị {len(items)} đề gần nhất  ",
            bg=_HEADER_BG, fg=_FG_DIM,
            font=("Segoe UI", 8, "italic"),
        ).pack(side="left", padx=4, pady=4)
        # "Xem tất cả" link tới tab Lịch sử — handle qua callback nếu set
        if self._on_view_all is not None:
            view_all = tk.Label(
                ftr, text="Xem tất cả →",
                bg=_HEADER_BG, fg=_FG_ACCENT,
                font=("Segoe UI", 8, "bold", "underline"),
                cursor="hand2", padx=8, pady=4,
            )
            view_all.pack(side="right")
            view_all.bind("<Button-1>",
                          lambda _e: (self.dismiss(), self._on_view_all()))

        self._win = win

        # Position dưới anchor (left-align)
        win.update_idletasks()
        self._position()

        # Fade-in alpha
        try:
            win.attributes("-alpha", 0.0)
            self._fade_in()
        except tk.TclError:
            pass

        # Auto-close khi click ngoài
        win.bind("<FocusOut>", lambda _e: self.dismiss())
        win.bind("<Escape>", lambda _e: self.dismiss())
        win.focus_set()

    # ──────────────────────────────────────────────────────────────────
    _on_view_all: Optional[Callable] = None

    def set_view_all_callback(self, cb: Callable) -> None:
        """Set callback cho link 'Xem tất cả →' ở footer."""
        self._on_view_all = cb

    # ──────────────────────────────────────────────────────────────────
    def _build_item(self, parent: tk.Misc, item: dict) -> None:
        """1 card item — clickable, hover highlight."""
        src = item.get("source", "")
        icon = _SOURCE_ICONS.get(src, "📄")

        row = tk.Frame(parent, bg=_BG, cursor="hand2")
        row.pack(fill="x")

        # Subtle separator (thin line on top, except first)
        sep = tk.Frame(parent, bg=_BORDER, height=1)
        sep.pack(fill="x")
        sep.lower(row)

        # Inner: icon + content
        body = tk.Frame(row, bg=_BG)
        body.pack(fill="x", padx=10, pady=6)

        # Icon
        icon_lbl = tk.Label(
            body, text=icon,
            bg=_BG, font=("Segoe UI", 16),
            padx=4,
        )
        icon_lbl.pack(side="left", padx=(0, 8))

        # Content column
        content = tk.Frame(body, bg=_BG)
        content.pack(side="left", fill="x", expand=True)

        # Title (truncate)
        title = item.get("title") or "(Đề không có tiêu đề)"
        if len(title) > 55:
            title = title[:52] + "…"
        title_lbl = tk.Label(
            content, text=title,
            bg=_BG, fg=_FG_TITLE,
            font=("Segoe UI", 9, "bold"),
            anchor="w", justify="left",
        )
        title_lbl.pack(anchor="w", fill="x")

        # Meta line: Lớp X Môn Y • N câu (TN/DS/TLN/TL)
        subj = item.get("subject", "?")
        grade = item.get("grade", "?")
        n = item.get("n_questions", 0)
        n_tn  = item.get("n_tn", 0)
        n_ds  = item.get("n_ds", 0)
        n_tln = item.get("n_tln", 0)
        n_tl  = item.get("n_tl", 0)
        stat_parts = []
        if n_tn:  stat_parts.append(f"{n_tn} TN")
        if n_ds:  stat_parts.append(f"{n_ds} DS")
        if n_tln: stat_parts.append(f"{n_tln} TLN")
        if n_tl:  stat_parts.append(f"{n_tl} TL")
        stat_str = " • ".join(stat_parts) if stat_parts else f"{n} câu"

        meta_lbl = tk.Label(
            content, text=f"  {grade} {subj}  •  {stat_str}",
            bg=_BG, fg=_FG_BODY,
            font=("Segoe UI", 8),
            anchor="w",
        )
        meta_lbl.pack(anchor="w", fill="x")

        # Time (right side, dim color)
        time_lbl = tk.Label(
            body, text=item.get("time_pretty", ""),
            bg=_BG, fg=_FG_DIM,
            font=("Segoe UI", 8, "italic"),
            padx=8,
        )
        time_lbl.pack(side="right", anchor="ne", pady=(2, 0))

        # ── Hover behaviour ──
        def _on_enter(_e=None, widgets=(row, body, content, icon_lbl,
                                         title_lbl, meta_lbl, time_lbl)):
            for w in widgets:
                try:
                    w.configure(bg=_HOVER_BG)
                except tk.TclError:
                    pass

        def _on_leave(_e=None, widgets=(row, body, content, icon_lbl,
                                         title_lbl, meta_lbl, time_lbl)):
            for w in widgets:
                try:
                    w.configure(bg=_BG)
                except tk.TclError:
                    pass

        # Click → restore
        def _on_click(_e=None, exam_id=item["exam_id"]):
            try:
                exam = load_recent_as_examdata(exam_id)
                if exam is None:
                    return
                self.dismiss()
                self._on_restore(exam)
            except Exception as e:
                _log.warning("Restore failed for %s: %s", exam_id, e)

        for w in (row, body, content, icon_lbl, title_lbl, meta_lbl, time_lbl):
            w.bind("<Enter>", _on_enter)
            w.bind("<Leave>", _on_leave)
            w.bind("<Button-1>", _on_click)

    # ──────────────────────────────────────────────────────────────────
    def _position(self) -> None:
        """Bám popup dưới-trái anchor button. Ép vào viewport nếu tràn."""
        if not self._win:
            return
        try:
            ax = self._anchor.winfo_rootx()
            ay = self._anchor.winfo_rooty()
            ah = self._anchor.winfo_height()
            ww = self._win.winfo_width()
            wh = self._win.winfo_height()
            sw = self._win.winfo_screenwidth()
            sh = self._win.winfo_screenheight()

            x = ax
            y = ay + ah + 4  # 4px gap dưới anchor

            # Nếu tràn phải → căn phải mép anchor
            if x + ww > sw - 10:
                aw = self._anchor.winfo_width()
                x = max(10, ax + aw - ww)
            # Nếu tràn đáy → hiển thị PHÍA TRÊN anchor
            if y + wh > sh - 10:
                y = max(10, ay - wh - 4)

            self._win.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass

    # ──────────────────────────────────────────────────────────────────
    def _fade_in(self, step: int = 0) -> None:
        if not self._win or not self._win.winfo_exists():
            return
        try:
            alpha = min(1.0, step * 0.2)
            self._win.attributes("-alpha", alpha)
            if alpha < 1.0:
                self._win.after(16, lambda: self._fade_in(step + 1))
        except tk.TclError:
            pass

    # ──────────────────────────────────────────────────────────────────
    def dismiss(self) -> None:
        if self._win is not None:
            try:
                if self._win.winfo_exists():
                    self._win.destroy()
            except tk.TclError:
                pass
            self._win = None
