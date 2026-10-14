"""
ui/dialog_nhch_preview.py — Dialog xem trước & chỉnh sửa câu hỏi trước khi lưu vào NHCH.

Cho phép người dùng:
  - Xem danh sách câu hỏi (bảng)
  - Xóa câu không muốn lưu
  - Chỉnh sửa metadata: mức độ, lớp, dạng, chủ đề, điểm
  - Chỉnh nội dung câu hỏi, đáp án, lời giải
  - Kiểm tra trùng lặp trước khi lưu
  - Tìm kiếm/lọc nhanh theo dạng/mức độ
  - Undo/Redo khi chỉnh sửa
  - Xác nhận / Hủy upload
"""

from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from core.models import Question
from config import LEVEL_DESC, TYPE_LABELS
from ui.image_helper import (pick_and_copy_image, pick_and_copy_images,
                                load_tk_image, normalize_image_field,
                                serialize_image_field)


# ── Hằng số giao diện ────────────────────────────────────────────────────────
_BG = "#FFFFFF"
_BG_HDR = "#F8FAFC"
_FG = "#0F172A"
_FG2 = "#475569"
_ACCENT = "#0EA5E9"
_GREEN = "#10B981"
_RED = "#EF4444"
_ORANGE = "#F59E0B"
_FONT = ("Segoe UI", 9)
_FONT_B = ("Segoe UI", 10, "bold")
_FONT_H = ("Segoe UI", 12, "bold")

_LEVELS = list(LEVEL_DESC.keys())           # NB, TH, VD
_QTYPES = ["TN", "DS", "TLN", "TL"]
_GRADES = ["10", "11", "12"]

# ── Undo/Redo stack ──────────────────────────────────────────────────────────
UNDO_LIMIT = 50


def _normalize_text(text: str) -> str:
    """Chuẩn hóa text để so sánh: bỏ khoảng trắng, lower, bỏ dấu câu."""
    text = text.lower().strip()
    text = re.sub(r'[\s\n\r]+', ' ', text)
    # Bỏ dấu câu phổ biến
    text = re.sub(r'[.,;:!?()\[\]{}"\']+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _compute_similarity(text1: str, text2: str) -> float:
    """Tính độ giống nhau của 2 text (0.0 – 1.0) bằng Jaccard n-gram."""
    t1 = _normalize_text(text1)
    t2 = _normalize_text(text2)
    if not t1 or not t2:
        return 0.0

    # Tách thành bigrams
    def ngrams(s: str, n: int = 2) -> set:
        return set(s[i:i+n] for i in range(max(0, len(s)-n+1)))

    ng1 = ngrams(t1)
    ng2 = ngrams(t2)
    if not ng1 or not ng2:
        return 0.0

    # Jaccard similarity
    intersection = len(ng1 & ng2)
    union = len(ng1 | ng2)
    return intersection / union if union > 0 else 0.0


def _find_duplicates(questions: list[Question], threshold: float = 0.80) -> list[set[int]]:
    """Tìm các cặp câu trùng lặp. Trả về list các set chỉ số trùng nhau."""
    texts = [q.question or "" for q in questions]
    dup_groups: list[set[int]] = []

    for i in range(len(texts)):
        found = False
        for group in dup_groups:
            if i in group:
                found = True
                break
        if found:
            continue

        group = {i}
        for j in range(i + 1, len(texts)):
            if texts[j]:
                sim = _compute_similarity(texts[i], texts[j])
                if sim >= threshold:
                    # Kiểm tra j chưa trong group nào
                    already_in = False
                    for g in dup_groups:
                        if j in g:
                            already_in = True
                            break
                    if not already_in:
                        group.add(j)

        if len(group) > 1:
            dup_groups.append(group)

    return dup_groups


class NHCHPreviewDialog(tk.Toplevel):
    """Dialog xem trước câu hỏi trước khi upload vào NHCH."""

    def __init__(
        self,
        parent: tk.Widget,
        questions: list[Question],
        subject: str = "Toán",
        grade: str = "12",
        on_confirm: Optional[callable] = None,
    ):
        super().__init__(parent)
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        w = min(1200, max(1050, screen_w - 80))
        h = min(780, max(640, screen_h - 100))
        self.geometry(f"{w}x{h}")
        self.minsize(920, 540)
        self.configure(bg=_BG)
        self.grab_set()
        self.focus_set()

        self._questions = list(questions)  # bản sao để chỉnh sửa
        self._subject = subject
        self._grade = grade
        self._on_confirm = on_confirm
        self._confirmed = False

        # ── Undo/Redo stacks ────────────────────────────────────────────────
        self._undo_stack: list[list[dict]] = []
        self._redo_stack: list[list[dict]] = []
        self._undo_pos = -1  # -1 = ở trạng thái hiện tại

        # ── Bộ lọc & tìm kiếm ──────────────────────────────────────────────
        self._filter_qtype = tk.StringVar(value="")
        self._filter_level = tk.StringVar(value="")
        self._filter_text = tk.StringVar(value="")
        self._dup_only_var = tk.BooleanVar(value=False)
        self._dup_only_var.trace_add("write", lambda *_: self._apply_filters())

        # ── Kết quả trùng lặp ──────────────────────────────────────────────
        self._dup_groups: list[set[int]] = []
        self._dup_highlight: set[int] = set()

        # ── Chỉ số hiện tại sau lọc ───────────────────────────────────────
        self._filtered_indices: list[int] = []  # maps tree rows → _questions indices

        self._build_ui()
        self._check_duplicates()
        self._populate_tree()

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    # ══════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=_BG_HDR)
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="Xem trước câu hỏi trước khi lưu vào NHCH",
            bg=_BG_HDR, fg=_FG, font=_FONT_H,
        ).pack(side="left", padx=16, pady=10)
        self._count_lbl = tk.Label(
            hdr, text="", bg=_BG_HDR, fg=_FG2, font=_FONT,
        )
        self._count_lbl.pack(side="right", padx=16)

        # Override Lớp + Môn — cho phép user đổi trước khi lưu vào NHCH
        # (vd: import từ nguồn khác lớp với cấu hình hiện tại)
        meta_f = tk.Frame(self, bg=_BG)
        meta_f.pack(fill="x", padx=16, pady=(8, 0))
        tk.Label(meta_f, text="📚 Lưu vào — Môn:", bg=_BG, fg=_FG2,
                 font=_FONT).pack(side="left")
        self._save_subject_var = tk.StringVar(value=self._subject)
        ttk.Entry(meta_f, textvariable=self._save_subject_var, width=12
                  ).pack(side="left", padx=(4, 12))

        tk.Label(meta_f, text="Lớp:", bg=_BG, fg=_FG2,
                 font=_FONT).pack(side="left")
        self._save_grade_var = tk.StringVar(value=str(self._grade))
        ttk.Combobox(
            meta_f, textvariable=self._save_grade_var, width=6,
            values=["1","2","3","4","5","6","7","8","9","10","11","12"],
            state="normal",
        ).pack(side="left", padx=(4, 12))

        tk.Label(meta_f,
                 text="(thông tin này sẽ được tag cho TẤT CẢ câu khi lưu — "
                      "phục vụ filter trong tab Ngân hàng)",
                 bg=_BG, fg="#94A3B8", font=("Segoe UI", 8, "italic")
                 ).pack(side="left")

        tk.Frame(self, bg="#E2E8F0", height=1).pack(fill="x", pady=(8, 0))

        # ── Thanh tìm kiếm & lọc ──────────────────────────────────────────
        filter_f = tk.Frame(self, bg=_BG)
        filter_f.pack(fill="x", padx=12, pady=(6, 0))

        # Tìm kiếm
        tk.Label(filter_f, text="🔍 Tìm:", bg=_BG, fg=_FG2,
                 font=_FONT).pack(side="left", padx=(0, 4))
        search_entry = tk.Entry(filter_f, textvariable=self._filter_text,
                                font=_FONT, width=30)
        search_entry.pack(side="left", padx=(0, 12))
        self._filter_text.trace_add("write", lambda *_: self._apply_filters())

        # Lọc theo dạng
        tk.Label(filter_f, text="Dạng:", bg=_BG, fg=_FG2,
                 font=_FONT).pack(side="left", padx=(0, 4))
        qtype_cb = ttk.Combobox(filter_f, textvariable=self._filter_qtype,
                                values=[""] + _QTYPES, width=8,
                                state="readonly", font=_FONT)
        qtype_cb.pack(side="left", padx=(0, 8))
        qtype_cb.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # Lọc theo mức độ
        tk.Label(filter_f, text="Mức:", bg=_BG, fg=_FG2,
                 font=_FONT).pack(side="left", padx=(0, 4))
        level_cb = ttk.Combobox(filter_f, textvariable=self._filter_level,
                                values=[""] + _LEVELS, width=8,
                                state="readonly", font=_FONT)
        level_cb.pack(side="left", padx=(0, 8))
        level_cb.bind("<<ComboboxSelected>>", lambda e: self._apply_filters())

        # Nút xóa filter
        tk.Button(filter_f, text="✕ Xóa lọc", font=_FONT,
                  bg="#F1F5F9", fg=_FG2, activebackground="#E2E8F0",
                  relief="flat", cursor="hand2", padx=8, pady=2,
                  command=self._clear_filters).pack(side="left", padx=(4, 0))

        # Checkbox trùng lặp
        tk.Checkbutton(filter_f, text="⚠️ Chỉ hiện trùng lặp",
                       variable=self._dup_only_var, bg=_BG,
                       font=_FONT, anchor="w",
                       activebackground=_BG).pack(side="right", padx=(8, 0))

        # ── Thanh công cụ ──
        tb = tk.Frame(self, bg=_BG)
        tb.pack(fill="x", padx=12, pady=(4, 2))

        tk.Button(
            tb, text="  Xóa câu đã chọn  ", font=_FONT_B,
            bg=_RED, fg="white", activebackground="#DC2626",
            relief="flat", cursor="hand2", padx=10, pady=4,
            command=self._delete_selected,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            tb, text="  Chỉnh sửa  ", font=_FONT_B,
            bg=_ACCENT, fg="white", activebackground="#0284C7",
            relief="flat", cursor="hand2", padx=10, pady=4,
            command=self._edit_selected,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            tb, text="  ↩️ Undo  ", font=_FONT,
            bg="#F1F5F9", fg=_FG2, activebackground="#E2E8F0",
            relief="flat", cursor="hand2", padx=8, pady=4,
            command=self._undo,
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            tb, text="  ↪️ Redo  ", font=_FONT,
            bg="#F1F5F9", fg=_FG2, activebackground="#E2E8F0",
            relief="flat", cursor="hand2", padx=8, pady=4,
            command=self._redo,
        ).pack(side="left", padx=(0, 4))

        # Nút hiện/ẩn cảnh báo trùng lặp
        self._dup_warning_btn = tk.Button(
            tb, text="", font=_FONT_B,
            bg=_ORANGE, fg="white", activebackground="#D97706",
            relief="flat", cursor="hand2", padx=10, pady=4,
            command=self._toggle_dup_warning,
        )
        self._dup_warning_btn.pack(side="left", padx=(8, 0))

        tk.Button(
            tb, text="  Chọn tất cả  ", font=_FONT,
            bg="#F1F5F9", fg=_FG2, activebackground="#E2E8F0",
            relief="flat", cursor="hand2", padx=8, pady=4,
            command=self._select_all,
        ).pack(side="right", padx=(0, 4))

        tk.Button(
            tb, text="  Bỏ chọn  ", font=_FONT,
            bg="#F1F5F9", fg=_FG2, activebackground="#E2E8F0",
            relief="flat", cursor="hand2", padx=8, pady=4,
            command=self._deselect_all,
        ).pack(side="right")

        # ── Thanh nút thao tác cuối: LUÔN GHIM CỐ ĐỊNH Ở ĐÁY CỬA SỔ (không bị che khuất) ──
        ft = tk.Frame(self, bg=_BG)
        ft.pack(side="bottom", fill="x", padx=16, pady=(8, 12))

        tk.Button(
            ft, text="  💾 Xác nhận lưu vào NHCH  ", font=_FONT_B,
            bg=_GREEN, fg="white", activebackground="#059669",
            relief="flat", cursor="hand2", padx=18, pady=8,
            command=self._on_confirm_click,
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            ft, text="  ✕ Hủy  ", font=_FONT,
            bg="#F1F5F9", fg=_FG2, activebackground="#E2E8F0",
            relief="flat", cursor="hand2", padx=16, pady=8,
            command=self._on_cancel,
        ).pack(side="right")

        # Nút kiểm tra trùng lặp thủ công
        tk.Button(
            ft, text="  🔍 Kiểm tra trùng  ", font=_FONT,
            bg=_ORANGE, fg="white", activebackground="#D97706",
            relief="flat", cursor="hand2", padx=12, pady=8,
            command=self._check_duplicates,
        ).pack(side="left")

        # ── Bảng + chi tiết: PanedWindow chiếm toàn bộ khoảng trống còn lại ở giữa ──
        main_pane = ttk.PanedWindow(self, orient="vertical")
        main_pane.pack(fill="both", expand=True, padx=12, pady=4)

        tree_f = tk.Frame(main_pane, bg=_BG)
        main_pane.add(tree_f, weight=5)

        cols = ("stt", "qtype", "level", "topic", "question", "answer", "points", "dup")
        self._tree = ttk.Treeview(
            tree_f, columns=cols, show="headings", selectmode="extended",
            height=12,
        )

        col_cfg = {
            "stt":      ("STT",              45,  "center"),
            "qtype":    ("Dạng",             60,  "center"),
            "level":    ("Mức độ",           65,  "center"),
            "topic":    ("Chủ đề",          160, "w"),
            "question": ("Nội dung câu hỏi", 320, "w"),
            "answer":   ("Đáp án",          100, "w"),
            "points":   ("Điểm",             50,  "center"),
            "dup":      ("Trùng",            60,  "center"),
        }
        for cid, (heading, width, anchor) in col_cfg.items():
            self._tree.heading(cid, text=heading)
            self._tree.column(cid, width=width, minwidth=40, anchor=anchor)

        vsb = ttk.Scrollbar(tree_f, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_f, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_f.rowconfigure(0, weight=1)
        tree_f.columnconfigure(0, weight=1)

        self._tree.tag_configure("duplicate", background="#FEF3C7")
        self._tree.tag_configure("error_row", background="#FEE2E2")

        self._tree.bind("<Double-1>", lambda e: self._edit_selected())

        bottom_f = tk.Frame(main_pane, bg=_BG)
        main_pane.add(bottom_f, weight=2)

        pv = tk.LabelFrame(bottom_f, text=" Xem chi tiết ", bg=_BG, fg=_FG2, font=_FONT)
        pv.pack(fill="both", expand=True, padx=0, pady=(0, 2))
        self._preview_text = tk.Text(
            pv, height=5, wrap="word", font=("Consolas", 10),
            bg="#F1F5F9", fg=_FG, relief="solid", borderwidth=1, state="disabled",
        )
        self._preview_text.pack(fill="both", expand=True, padx=6, pady=6)
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    # ══════════════════════════════════════════════════════════════════════
    #  DUPLICATE CHECK
    # ══════════════════════════════════════════════════════════════════════

    def _check_duplicates(self):
        """Kiểm tra trùng lặp giữa các câu trong danh sách."""
        self._dup_groups = _find_duplicates(self._questions, threshold=0.80)

        # Tạo set chỉ số bị trùng
        self._dup_highlight = set()
        for group in self._dup_groups:
            self._dup_highlight.update(group)

        self._update_dup_button()

    def _update_dup_button(self):
        n = len(self._dup_groups)
        if n == 0:
            self._dup_warning_btn.config(
                text="  ✅ Không có trùng lặp  ",
                bg=_GREEN, fg="white",
                activebackground="#059669",
            )
        else:
            total_dup = len(self._dup_highlight)
            self._dup_warning_btn.config(
                text=f"  ⚠️ {n} nhóm trùng ({total_dup} câu)  ",
                bg=_ORANGE, fg="white",
                activebackground="#D97706",
            )

    def _toggle_dup_warning(self):
        """Bật/tắt hiện chỉ các câu trùng lặp."""
        self._dup_only_var.set(not self._dup_only_var.get())

    # ══════════════════════════════════════════════════════════════════════
    #  POPULATE / REFRESH
    # ══════════════════════════════════════════════════════════════════════

    def _get_visible_indices(self) -> list[int]:
        """Lấy danh sách chỉ số _questions đang hiển thị (sau lọc)."""
        visible = []
        for i, q in enumerate(self._questions):
            if q._error:
                continue
            # Áp dụng bộ lọc
            if self._filter_qtype.get() and q.qtype != self._filter_qtype.get():
                continue
            if self._filter_level.get() and q.level != self._filter_level.get():
                continue
            if self._filter_text.get():
                kw = self._filter_text.get().lower()
                in_question = kw in (q.question or "").lower()
                in_topic = kw in (q.topic or "").lower()
                in_answer = kw in (q.answer or "").lower()
                if not (in_question or in_topic or in_answer):
                    continue
            if self._dup_only_var.get() and i not in self._dup_highlight:
                continue
            visible.append(i)
        return visible

    def _apply_filters(self):
        """Áp dụng lại bộ lọc và cập nhật tree."""
        self._filtered_indices = self._get_visible_indices()
        self._populate_tree()

    def _clear_filters(self):
        """Xóa tất cả bộ lọc."""
        self._filter_qtype.set("")
        self._filter_level.set("")
        self._filter_text.set("")
        self._dup_only_var.set(False)
        self._apply_filters()

    def _populate_tree(self):
        for item in self._tree.get_children():
            self._tree.delete(item)

        # Cập nhật filtered indices
        self._filtered_indices = self._get_visible_indices()

        for display_i, q_idx in enumerate(self._filtered_indices):
            q = self._questions[q_idx]
            q_text = (q.question or "")[:120].replace("\n", " ")
            ans = q.answer or ""
            if q.qtype == "DS" and q.answers:
                ans = " | ".join(f"{k}:{'Đ' if v else 'S'}" for k, v in q.answers.items())

            # Cờ trùng lặp
            is_dup = q_idx in self._dup_highlight
            dup_mark = "⚠️" if is_dup else ""

            tags = ()
            if is_dup:
                tags = ("duplicate",)

            self._tree.insert("", "end", iid=str(q_idx), values=(
                display_i + 1,
                q.qtype,
                q.level,
                q.topic[:40] if q.topic else "",
                q_text,
                ans[:50],
                q.points,
                dup_mark,
            ), tags=tags)

        total = sum(1 for q in self._questions if not q._error)
        shown = len(self._filtered_indices)
        dup_n = len(self._dup_highlight)

        count_text = f"Hiện: {shown}/{total} câu"
        if dup_n > 0:
            count_text += f" | ⚠️ {dup_n} câu trùng lặp"
        self._count_lbl.config(text=count_text)

        if not self._tree.get_children():
            self._preview_text.config(state="normal")
            self._preview_text.delete("1.0", "end")
            self._preview_text.insert(
                "1.0",
                "Không có câu hỏi hiển thị.\n"
                "• Có thể tất cả câu đang bị đánh dấu lỗi (_error).\n"
                "• Hoặc bộ lọc đang loại hết — thử «✕ Xóa lọc».",
            )
            self._preview_text.config(state="disabled")
        else:
            first = self._tree.get_children()[0]
            self._tree.selection_set(first)
            self._tree.focus(first)
            self._on_tree_select()

    def _on_tree_select(self, event=None):
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx >= len(self._questions):
            return
        q = self._questions[idx]

        self._preview_text.config(state="normal")
        self._preview_text.delete("1.0", "end")

        lines = [
            f"[{q.qtype}] [{q.level}] {q.topic}",
            "",
            q.question or "(không có nội dung)",
        ]

        # Hiện cảnh báo trùng lặp
        if idx in self._dup_highlight:
            for group in self._dup_groups:
                if idx in group:
                    others = [f"Câu {self._filtered_indices.index(j)+1}" for j in group if j != idx]
                    if others:
                        lines.append(f"\n⚠️ TRÙNG LẶP với: {', '.join(others)}")
                    break

        if q.options:
            lines.append("")
            for k, v in q.options.items():
                marker = " <-- đáp án đúng" if k == q.answer else ""
                lines.append(f"  {k}. {v}{marker}")
        if q.qtype == "DS" and q.items:
            lines.append("")
            for k, v in q.items.items():
                da = q.answers.get(k, None)
                da_str = "Đúng" if da else "Sai" if da is not None else "?"
                lines.append(f"  {k}) {v}  [{da_str}]")
        if q.answer and q.qtype not in ("TN", "DS"):
            lines.append(f"\nĐáp án: {q.answer}")
        if q.solution:
            lines.append(f"\nLời giải: {q.solution[:200]}")

        self._preview_text.insert("1.0", "\n".join(lines))
        self._preview_text.config(state="disabled")

    # ══════════════════════════════════════════════════════════════════════
    #  UNDO / REDO
    # ══════════════════════════════════════════════════════════════════════

    def _save_undo_state(self):
        """Lưu trạng thái hiện tại vào undo stack."""
        state = []
        for q in self._questions:
            state.append({
                "qtype": q.qtype,
                "level": q.level,
                "topic": q.topic,
                "question": q.question,
                "answer": q.answer,
                "solution": q.solution,
                "options": dict(q.options) if q.options else {},
                "items": dict(q.items) if q.items else {},
                "answers": dict(q.answers) if q.answers else {},
                "item_solutions": dict(q.item_solutions) if q.item_solutions else {},
                "points": q.points,
                "_error": q._error,
                "_error_msg": q._error_msg,
            })

        # Xóa redo stack nếu đang ở giữa lịch sử
        self._redo_stack.clear()

        # Giới hạn kích thước stack
        if len(self._undo_stack) >= UNDO_LIMIT:
            self._undo_stack.pop(0)

        self._undo_stack.append(state)
        self._undo_pos = len(self._undo_stack) - 1

    def _restore_state(self, state: list[dict]):
        """Khôi phục trạng thái từ undo/redo stack."""
        self._questions = []
        for s in state:
            q = Question(
                qtype=s["qtype"],
                level=s["level"],
                topic=s["topic"],
                question=s["question"],
                answer=s["answer"],
                solution=s["solution"],
                options=s.get("options", {}),
                items=s.get("items", {}),
                answers=s.get("answers", {}),
                item_solutions=s.get("item_solutions", {}),
                points=s.get("points", 1.0),
                _error=s.get("_error", False),
                _error_msg=s.get("_error_msg", ""),
            )
            self._questions.append(q)

    def _undo(self):
        """Quay lại trạng thái trước đó."""
        if not self._undo_stack or self._undo_pos <= 0:
            messagebox.showinfo("Undo", "Không có thao tác nào để undo.", parent=self)
            return
        self._undo_pos -= 1
        self._restore_state(self._undo_stack[self._undo_pos])
        self._check_duplicates()
        self._populate_tree()
        messagebox.showinfo("Undo", "Đã khôi phục trạng thái trước đó.", parent=self)

    def _redo(self):
        """Tiến tới trạng thái sau đó."""
        if not self._undo_stack or self._undo_pos >= len(self._undo_stack) - 1:
            messagebox.showinfo("Redo", "Không có thao tác nào để redo.", parent=self)
            return
        self._undo_pos += 1
        self._restore_state(self._undo_stack[self._undo_pos])
        self._check_duplicates()
        self._populate_tree()
        messagebox.showinfo("Redo", "Đã tiến tới trạng thái sau đó.", parent=self)

    # ══════════════════════════════════════════════════════════════════════
    #  ACTIONS
    # ══════════════════════════════════════════════════════════════════════

    def _select_all(self):
        for iid in self._tree.get_children():
            self._tree.selection_add(iid)

    def _deselect_all(self):
        self._tree.selection_remove(*self._tree.get_children())

    def _delete_selected(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Chưa chọn câu nào để xóa.", parent=self)
            return
        if not messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc muốn xóa {len(sel)} câu hỏi khỏi danh sách?",
            parent=self,
        ):
            return
        self._save_undo_state()
        indices = sorted([int(iid) for iid in sel], reverse=True)
        for idx in indices:
            if 0 <= idx < len(self._questions):
                self._questions[idx]._error = True
                self._questions[idx]._error_msg = "Người dùng đã xóa"
        self._check_duplicates()
        self._populate_tree()

    def _edit_selected(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Thông báo", "Vui lòng chọn 1 câu để chỉnh sửa.", parent=self)
            return
        idx = int(sel[0])
        q = self._questions[idx]
        _QuestionEditDialog(self, q, self._subject, self._grade, self._on_edit_done)

    def _on_edit_done(self):
        self._save_undo_state()
        self._check_duplicates()
        self._populate_tree()

    def _on_confirm_click(self):
        # Kiểm tra trùng lặp trước khi lưu
        if self._dup_highlight:
            dup_n = len(self._dup_highlight)
            resp = messagebox.askyesno(
                "⚠️ Cảnh báo trùng lặp",
                f"Phát hiện {dup_n} câu hỏi bị trùng lặp trong danh sách!\n\n"
                f"Bạn có chắc muốn lưu tất cả không?\n"
                f"(Nhấn 'Có' để lưu, 'Không' để quay lại kiểm tra)",
                parent=self,
            )
            if not resp:
                return

        valid = [q for q in self._questions if not q._error]
        if not valid:
            messagebox.showwarning("Không có câu hỏi", "Không còn câu nào để lưu.", parent=self)
            return

        # Đồng bộ override Môn + Lớp (nếu user đã sửa trong header) — caller
        # đọc qua self.final_subject / self.final_grade trước khi gọi
        # save_questions() để tag đúng thông tin.
        try:
            self._subject = (self._save_subject_var.get().strip()
                              or self._subject)
            self._grade   = (self._save_grade_var.get().strip()
                              or self._grade)
        except Exception:
            pass
        self.final_subject = self._subject
        self.final_grade   = self._grade

        # Thông báo kết quả
        dup_count = len(self._dup_highlight) if hasattr(self, '_dup_highlight') else 0
        self._confirmed = True
        if self._on_confirm:
            # Truyền grade override qua attribute để caller cũ vẫn chạy
            # (signature on_confirm(questions) giữ nguyên).
            self._on_confirm(valid)

        # Hiện thông báo
        msg = f"Đã lưu {len(valid)} câu hỏi vào NHCH!"
        if dup_count > 0:
            msg += f"\n⚠️ Lưu ý: {dup_count} câu bị trùng lặp đã được lưu."
        messagebox.showinfo("Thành công", msg, parent=self)
        self.destroy()

    def _on_cancel(self):
        self._confirmed = False
        self.destroy()

    @property
    def confirmed(self) -> bool:
        return self._confirmed

    @property
    def result_questions(self) -> list[Question]:
        """Danh sách câu hỏi sau khi chỉnh sửa (chỉ câu hợp lệ)."""
        return [q for q in self._questions if not q._error]


# ══════════════════════════════════════════════════════════════════════════════
#  EDIT DIALOG — Chỉnh sửa 1 câu hỏi
# ══════════════════════════════════════════════════════════════════════════════

class _QuestionEditDialog(tk.Toplevel):
    """Dialog chỉnh sửa metadata + nội dung 1 câu hỏi."""

    def __init__(
        self,
        parent: tk.Widget,
        question: Question,
        subject: str,
        grade: str,
        on_save: Optional[callable] = None,
    ):
        super().__init__(parent)
        self.title(f"Chỉnh sửa câu hỏi — {question.question_id}")
        # Đặt geometry mặc định (khi user thoát maximize sẽ về kích thước này)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = min(1760, max(1100, int(sw * 0.92)))
        h = min(1000, max(680, int(sh * 0.9)))
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2 - 20)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(1024, 640)
        self.resizable(True, True)
        self.configure(bg=_BG)
        self.grab_set()
        self.focus_set()

        # ── Mở MAXIMIZED sẵn để có nhiều không gian ──────────────────────
        # F11: toggle fullscreen (ẩn title bar) | Esc: thoát fullscreen
        try:
            self.state("zoomed")              # Windows
        except tk.TclError:
            try:
                self.attributes("-zoomed", True)   # Linux
            except tk.TclError:
                pass

        self._is_fullscreen = False
        def _toggle_fs(_e=None):
            self._is_fullscreen = not self._is_fullscreen
            self.attributes("-fullscreen", self._is_fullscreen)
        def _exit_fs(_e=None):
            if self._is_fullscreen:
                self._is_fullscreen = False
                self.attributes("-fullscreen", False)
        self.bind("<F11>", _toggle_fs)
        self.bind("<Escape>", _exit_fs)

        self._q = question
        self._subject = subject
        self._grade = grade
        self._on_save = on_save
        self._tk_images: list = []       # giữ reference ảnh
        self._img_vars: dict[str, tk.StringVar] = {}  # key → path var

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

    # ── ID auto-compute & live update ────────────────────────────────────────
    @staticmethod
    def _is_auto_format(qid: str) -> bool:
        """Check ID có dạng auto-structured (vd 12D1N1-01) hay user custom?"""
        import re as _re
        return bool(_re.match(r"^\d{1,2}[DH]\d+[NTVG]\d+-\d+$", (qid or "").strip()))

    def _auto_assign_id_initial(self, q) -> None:
        """Tính ID lần đầu khi mở dialog (nếu q chưa có)."""
        try:
            from core.models import compute_structured_id
            new_id = compute_structured_id(
                q, grade_str=self._grade or "12",
                existing_qids=self._get_existing_qids(),
            )
            if new_id:
                q.question_id = new_id
        except Exception:
            pass

    def _get_existing_qids(self) -> set:
        try:
            from storage.database import list_all_questions
            return {(d.get("question_id") or "") for d in
                    (list_all_questions() or [])
                    if d.get("question_id")}
        except Exception:
            return set()

    def _on_meta_change(self) -> None:
        """Khi user đổi topic/qtype/level → re-compute ID nếu đang auto."""
        if not getattr(self, "_id_auto", False):
            return   # user đã chỉnh ID tay → tôn trọng
        try:
            from core.models import compute_structured_id
            # Build temp question với meta mới
            tmp = type(self._q)(qtype=self._qtype_var.get() or "TN",
                                  level=self._level_var.get() or "TH",
                                  topic=self._topic_var.get() or "")
            existing = self._get_existing_qids() - {self._q.question_id or ""}
            new_id = compute_structured_id(
                tmp, grade_str=self._grade or "12",
                existing_qids=existing,
            )
            if new_id:
                self._last_auto_id = new_id  # đánh dấu để skip trace
                self._id_var.set(new_id)
        except Exception:
            pass

    def _force_regen_id(self) -> None:
        """Bấm nút 🔄 → ép re-gen ID dù user đã edit tay."""
        self._id_auto = True
        self._on_meta_change()

    # ── ID Tooltip / Duplicate-warn / Format-validate / Group-list ───────
    def _attach_id_tooltip(self, widget):
        """Hover lên ID Entry → popup giải thích từng ký tự."""
        from config import TYPE_LABELS as _TL
        _SUBJ = {"D": "Đại số", "H": "Hình học"}
        _LV   = {"N": "Nhận biết", "T": "Thông hiểu",
                 "V": "Vận dụng",   "G": "Vận dụng cao"}
        _QT   = {1: "TN", 2: "DS", 3: "TLN", 4: "TL"}
        tip = {"win": None}

        def _show(_e=None):
            import re as _re
            qid = (self._id_var.get() or "").strip()
            m = _re.match(r"^(\d{1,2})([DH])(\d+)([NTVG])(\d+)-(\d+)$", qid)
            if not m:
                lines = ["⚠ ID không theo chuẩn auto-format.",
                         "Auto: [Lớp][Môn][Ch][Mức][Loại]-[Seq]",
                         "Ví dụ: 12D1N1-0001"]
            else:
                g, s, c, l, t, n = m.groups()
                lines = [
                    f"🔑 Phân tích {qid}:",
                    f"  • Lớp:   {g}",
                    f"  • Môn:   {s} = {_SUBJ.get(s, '?')}",
                    f"  • Chương: {c}",
                    f"  • Mức độ: {l} = {_LV.get(l, '?')}",
                    f"  • Loại:  {t} = {_QT.get(int(t), '?')}",
                    f"  • Số TT: {int(n)}",
                ]
            if tip["win"]:
                try: tip["win"].destroy()
                except Exception: pass
            tw = tk.Toplevel(widget); tw.wm_overrideredirect(True)
            tw.attributes("-topmost", True)
            x = widget.winfo_rootx() + 4
            y = widget.winfo_rooty() + widget.winfo_height() + 4
            tw.wm_geometry(f"+{x}+{y}")
            tk.Label(tw, text="\n".join(lines),
                     bg="#FFFBEB", fg="#374151", justify="left",
                     font=("Consolas", 9), padx=10, pady=6,
                     relief="solid", bd=1).pack()
            tip["win"] = tw

        def _hide(_e=None):
            if tip["win"]:
                try: tip["win"].destroy()
                except Exception: pass
                tip["win"] = None

        widget.bind("<Enter>", _show)
        widget.bind("<Leave>", _hide)

    def _on_id_change(self, initial: bool = False) -> None:
        """Real-time check: trùng / sai format / cùng group → update UI."""
        qid = (self._id_var.get() or "").strip()

        # Detect user vs auto edit
        if not initial and qid != getattr(self, "_last_auto_id", ""):
            self._id_auto = False

        existing = self._get_existing_qids() - {self._q.question_id or ""}

        # 3 trạng thái: empty / duplicate / bad-format / OK
        if not qid:
            self._id_entry.config(highlightbackground="#FBBF24",
                                    highlightcolor="#FBBF24")
            self._id_status.config(text="⚠ ID rỗng", fg="#B45309")
            group_ids = []
        elif qid in existing:
            self._id_entry.config(highlightbackground="#EF4444",
                                    highlightcolor="#EF4444")
            self._id_status.config(text="✘ Trùng ID trong NHCH!", fg="#B91C1C")
            group_ids = self._find_group_ids(qid, existing)
        elif not self._is_auto_format(qid):
            self._id_entry.config(highlightbackground="#FBBF24",
                                    highlightcolor="#FBBF24")
            self._id_status.config(text="⚠ Không theo chuẩn auto",
                                     fg="#B45309")
            group_ids = []
        else:
            self._id_entry.config(highlightbackground="#10B981",
                                    highlightcolor="#10B981")
            self._id_status.config(text="✓ Hợp lệ", fg="#059669")
            group_ids = self._find_group_ids(qid, existing)

        # Hiển thị danh sách cùng group
        if group_ids:
            preview = ", ".join(sorted(group_ids)[:6])
            extra = f" (+{len(group_ids)-6})" if len(group_ids) > 6 else ""
            self._id_group_lbl.config(
                text=f"  📋 Cùng nhóm trong NHCH: {preview}{extra}",
                fg="#6B7280")
        else:
            self._id_group_lbl.config(text="  📋 Chưa có câu cùng nhóm.",
                                        fg="#9CA3AF")

    @staticmethod
    def _find_group_ids(qid: str, existing_qids: set) -> list:
        """Lấy các ID cùng prefix (cùng grade/subj/ch/level/qtype)."""
        prefix = qid.rsplit("-", 1)[0] + "-" if "-" in qid else qid
        return [q for q in existing_qids if q.startswith(prefix) and q != qid]

    def _make_image_holder(self, key: str, initial, refresh_cb) -> object:
        """Helper chung: tạo _Holder cho list ảnh + lưu vào self._img_vars.
        `_Holder.get()` trả '|'-joined str (backward compat với q.field: str).
        `_Holder.get_list()` trả list[str].
        """
        paths = normalize_image_field(initial)

        class _Holder:
            __slots__ = ("paths", "_refresh")
            def __init__(self): self.paths = paths; self._refresh = refresh_cb
            def get(self):       return serialize_image_field(self.paths)
            def get_list(self):  return list(self.paths)
            def set(self, v):
                self.paths = normalize_image_field(v); self._refresh()
            def add(self, ps):
                self.paths.extend(p for p in ps if p); self._refresh()
            def remove_at(self, i):
                if 0 <= i < len(self.paths):
                    self.paths.pop(i); self._refresh()
            def clear(self):     self.paths = []; self._refresh()

        h = _Holder()
        self._img_vars[key] = h
        return h

    def _add_compact_image_button(self, parent, image_path, key: str):
        """Frame nhỏ với nút ➕📷 + grid mini-thumbnails (60px).

        Multi-image: bấm nút "+📷" mở picker multi-select. Mỗi ảnh có nút ✕
        riêng để xoá. Đặt được vào hàng DS/TN compact.
        """
        wrap = tk.Frame(parent, bg=_BG)
        btn_box = tk.Frame(wrap, bg=_BG); btn_box.pack(side="left")
        thumbs_box = tk.Frame(wrap, bg=_BG); thumbs_box.pack(side="left", padx=(2, 0))

        def _refresh():
            for c in thumbs_box.winfo_children(): c.destroy()
            n = len(holder.paths)
            count_lbl.config(text=f"{n}" if n else "")
            for idx, p in enumerate(holder.paths):
                cell = tk.Frame(thumbs_box, bg="#F0F0F0", relief="flat", bd=0)
                cell.pack(side="left", padx=1)
                tk_img = load_tk_image(p, max_w=80, max_h=50)
                if tk_img:
                    self._tk_images.append(tk_img)
                    tk.Label(cell, image=tk_img, bg="#F0F0F0").pack()
                else:
                    tk.Label(cell, text="⚠", bg="#FEF3C7",
                             width=8, height=2).pack()
                tk.Button(cell, text="✕", font=("Segoe UI", 6, "bold"),
                          bg="#FEE2E2", fg="#991B1B", relief="flat",
                          cursor="hand2", padx=2, pady=0,
                          command=lambda i=idx: holder.remove_at(i)
                          ).pack(fill="x")

        holder = self._make_image_holder(key, image_path, _refresh)

        tk.Button(btn_box, text="➕📷", font=("Segoe UI", 8, "bold"),
                  bg="#A78BFA", fg="white", relief="flat", cursor="hand2",
                  padx=4, pady=1,
                  command=lambda: holder.add(pick_and_copy_images(self)),
                  ).pack(side="left", padx=(4, 0))
        count_lbl = tk.Label(btn_box, text="", bg=_BG, fg="#6B7280",
                              font=("Segoe UI", 7))
        count_lbl.pack(side="left", padx=2)
        _refresh()
        return wrap

    def _add_image_row(self, parent, image_path, key: str,
                       row_num: int, pad: dict) -> int:
        """Hàng chèn ảnh full-row với grid thumbnails (180×120) + drag-drop."""
        img_f = tk.Frame(parent, bg=_BG)
        img_f.grid(row=row_num, column=0, columnspan=3, sticky="ew", **pad)

        btn_box = tk.Frame(img_f, bg=_BG); btn_box.pack(side="left", anchor="n",
                                                          padx=(0, 6))
        thumbs_box = tk.Frame(img_f, bg=_BG); thumbs_box.pack(side="left",
                                                                fill="x", expand=True)

        drag_state = {"src": -1, "tgt": -1}

        def _refresh():
            for c in thumbs_box.winfo_children(): c.destroy()
            n = len(holder.paths)
            count_lbl.config(text=f"({n} ảnh)" if n else "(chưa có ảnh)")
            for idx, p in enumerate(holder.paths):
                cell = tk.Frame(thumbs_box, bg="#F0F0F0",
                                  relief="groove", bd=1, cursor="fleur")
                cell.pack(side="left", padx=2, pady=2)
                cell._img_idx = idx
                tk_img = load_tk_image(p, max_w=180, max_h=120)
                if tk_img:
                    self._tk_images.append(tk_img)
                    lbl = tk.Label(cell, image=tk_img, bg="#F0F0F0",
                                     cursor="fleur")
                    lbl.pack(padx=2, pady=2)
                else:
                    from pathlib import Path as _P
                    lbl = tk.Label(cell, text=f"⚠ {_P(p).name[:18]}", bg="#FEF3C7",
                             fg="#92400E", font=("Segoe UI", 8),
                             padx=10, pady=14, cursor="fleur")
                    lbl.pack()
                # Bind drag-drop
                for w in (cell, lbl):
                    w.bind("<Button-1>", lambda e, i=idx: _drag_start(i))
                    w.bind("<B1-Motion>", lambda e: _drag_motion(e))
                    w.bind("<ButtonRelease-1>", lambda e: _drag_end())
                bot = tk.Frame(cell, bg="#F0F0F0")
                bot.pack(fill="x", padx=2, pady=(0, 2))
                from pathlib import Path as _P
                tk.Label(bot, text=f"#{idx+1}  {_P(p).name[:15]}",
                         fg="#6B7280", bg="#F0F0F0", font=("Segoe UI", 7),
                         anchor="w").pack(side="left", fill="x", expand=True)
                tk.Button(bot, text="✕", font=("Segoe UI", 8, "bold"),
                          bg="#FEE2E2", fg="#991B1B", relief="flat",
                          cursor="hand2", padx=4, pady=0,
                          command=lambda i=idx: holder.remove_at(i)
                          ).pack(side="right")

        def _drag_start(i: int):
            drag_state["src"] = i

        def _drag_motion(event):
            w = event.widget.winfo_containing(event.x_root, event.y_root)
            tgt = -1
            while w is not None and w is not thumbs_box:
                if hasattr(w, "_img_idx"):
                    tgt = w._img_idx; break
                w = w.master
            drag_state["tgt"] = tgt

        def _drag_end():
            src, tgt = drag_state["src"], drag_state["tgt"]
            drag_state["src"] = drag_state["tgt"] = -1
            if src < 0 or tgt < 0 or src == tgt: return
            if 0 <= src < len(holder.paths) and 0 <= tgt < len(holder.paths):
                item = holder.paths.pop(src)
                holder.paths.insert(tgt, item)
                _refresh()

        holder = self._make_image_holder(key, image_path, _refresh)

        tk.Button(btn_box, text="🖼 + Ảnh", font=("Segoe UI", 8),
                  bg="#E0E7FF", fg="#3730A3", relief="flat", cursor="hand2",
                  padx=6, pady=2,
                  command=lambda: holder.add([pick_and_copy_image(self) or ""]),
                  ).pack(side="top", pady=1)
        tk.Button(btn_box, text="🖼🖼 + Nhiều", font=("Segoe UI", 8, "bold"),
                  bg="#A78BFA", fg="white", relief="flat", cursor="hand2",
                  padx=6, pady=2,
                  command=lambda: holder.add(pick_and_copy_images(self)),
                  ).pack(side="top", pady=1)
        tk.Button(btn_box, text="🗑 Xoá hết", font=("Segoe UI", 7),
                  bg="#FCA5A5", fg="#7F1D1D", relief="flat", cursor="hand2",
                  padx=4, pady=1, command=holder.clear,
                  ).pack(side="top", pady=1)
        count_lbl = tk.Label(btn_box, text="", bg=_BG, fg="#6B7280",
                              font=("Segoe UI", 7))
        count_lbl.pack(side="top", pady=(2, 0))

        _refresh()
        return row_num + 1

    def _build_ui(self):
        q = self._q

        # ── Nội dung cuộn được ──
        canvas = tk.Canvas(self, bg=_BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg=_BG)

        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)

        # Khi dialog/canvas đổi kích thước, ép content width = canvas width
        # để 2 cột bên trong stretch đều theo chiều rộng có sẵn.
        # Đồng thời ép content height = canvas height NẾU đủ chỗ — để text
        # widgets có thể giãn dọc theo window (qua rowconfigure weight).
        # Nếu content tự nhiên cao hơn canvas → giữ natural height (scroll vẫn chạy).
        def _on_canvas_resize(event):
            canvas.itemconfigure(content_window, width=event.width)
            canvas.update_idletasks()
            natural_h = content.winfo_reqheight()
            new_h = max(event.height, natural_h)
            canvas.itemconfigure(content_window, height=new_h)
        canvas.bind("<Configure>", _on_canvas_resize)

        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Cuộn bằng chuột.
        # Vấn đề: dialog là 1 canvas cuộn được CHỨA nhiều Text widget cũng
        # cuộn được. Nếu dùng bind_all toàn cục, khi user lăn chuột TRÊN
        # Text widget, cả Text TỰ cuộn (handler mặc định Tk) và canvas
        # CŨNG cuộn (bind_all của ta) → "trang chính cuộn theo".
        # Fix: trong handler, đi ngược qua cây widget từ event.widget; nếu
        # gặp Text trước khi gặp canvas/dialog thì BỎ canvas scroll, để
        # Text tự xử lý.
        def _on_mousewheel(event):
            """Chỉ scroll canvas khi mouse THỰC SỰ trong canvas tree.

            Trước đây: nếu walk parent chain đến `self` (dialog) mà chưa qua
            canvas → vẫn scroll canvas (sai — mouse có thể trên Notebook,
            scrollbar khác, hoặc nút). Fix: phân biệt 2 nhánh.
            """
            cur = event.widget
            inside_canvas = False
            for _ in range(30):                  # giới hạn depth
                if cur is None:
                    break
                if isinstance(cur, tk.Text):
                    return None                   # Text tự cuộn — KHÔNG break-event
                if cur is canvas:
                    inside_canvas = True
                    break
                if cur is self:
                    break                          # đã ra ngoài canvas tree
                try:
                    cur = cur.master
                except Exception:
                    break
            if not inside_canvas:
                return None                       # default handle (Notebook, …)
            n = int(-1 * (event.delta / 120))    # 1 line/tick (mượt hơn 4)
            if n == 0:
                n = -1 if event.delta > 0 else 1
            canvas.yview_scroll(n, "units")
            return "break"

        canvas.bind("<MouseWheel>", _on_mousewheel)
        self.bind("<MouseWheel>", _on_mousewheel, add="+")

        pad = {"padx": 12, "pady": 4}
        # 2 cột bằng nhau cho body; meta + separator + buttons sẽ
        # columnspan=2 chiếm toàn bộ chiều rộng.
        content.columnconfigure(0, weight=1, uniform="col")
        content.columnconfigure(1, weight=1, uniform="col")

        row = 0

        # ── Thông tin câu hỏi (đặt trên 2 hàng grid, 4 trường ngang) ─────────
        tk.Label(content, text="Thông tin câu hỏi", bg=_BG, fg=_FG,
                 font=_FONT_B).grid(row=row, column=0, columnspan=2, sticky="w", **pad)
        row += 1

        meta_f = tk.Frame(content, bg=_BG)
        meta_f.grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        meta_f.columnconfigure(1, weight=0)
        meta_f.columnconfigure(3, weight=1)
        meta_f.columnconfigure(5, weight=0)
        meta_f.columnconfigure(6, weight=0)

        # Hàng 1: Dạng | Chủ đề (entry stretch) | Điểm
        tk.Label(meta_f, text="Dạng:", bg=_BG, fg=_FG2, font=_FONT
                 ).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        self._qtype_var = tk.StringVar(value=q.qtype)
        ttk.Combobox(meta_f, textvariable=self._qtype_var,
                     values=_QTYPES, width=10, state="readonly"
                     ).grid(row=0, column=1, sticky="w", padx=(0, 16), pady=2)

        tk.Label(meta_f, text="Chủ đề:", bg=_BG, fg=_FG2, font=_FONT
                 ).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=2)
        self._topic_var = tk.StringVar(value=q.topic)
        tk.Entry(meta_f, textvariable=self._topic_var, font=_FONT
                 ).grid(row=0, column=3, sticky="ew", padx=(0, 16), pady=2)

        tk.Label(meta_f, text="Điểm:", bg=_BG, fg=_FG2, font=_FONT
                 ).grid(row=0, column=5, sticky="w", padx=(0, 4), pady=2)
        self._points_var = tk.StringVar(value=str(q.points))
        tk.Entry(meta_f, textvariable=self._points_var, font=_FONT, width=8
                 ).grid(row=0, column=6, sticky="w", pady=2)

        # Hàng 2: Mức độ | (ID — readonly để user biết đang sửa câu nào)
        tk.Label(meta_f, text="Mức độ:", bg=_BG, fg=_FG2, font=_FONT
                 ).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
        self._level_var = tk.StringVar(value=q.level)
        ttk.Combobox(meta_f, textvariable=self._level_var,
                     values=_LEVELS, width=10, state="readonly"
                     ).grid(row=1, column=1, sticky="w", padx=(0, 16), pady=2)

        tk.Label(meta_f, text="ID:", bg=_BG, fg=_FG2, font=_FONT
                 ).grid(row=1, column=2, sticky="w", padx=(0, 4), pady=2)

        # ID Entry — editable + auto-fill + live update + dup-warn + tooltip
        if not (q.question_id or "").strip():
            self._auto_assign_id_initial(q)
        self._id_var = tk.StringVar(value=q.question_id or "")
        self._id_auto = bool(q.question_id) and self._is_auto_format(q.question_id)
        self._id_entry = tk.Entry(meta_f, textvariable=self._id_var,
                                    font=("Consolas", 10, "bold"), fg="#7C3AED",
                                    relief="solid", bd=1, width=18,
                                    highlightthickness=1,
                                    highlightbackground="#D1D5DB")
        self._id_entry.grid(row=1, column=3, sticky="w", padx=(0, 6), pady=2)

        # Tooltip giải thích ID khi hover
        self._attach_id_tooltip(self._id_entry)

        # Nút 🔄 regen ID
        tk.Button(meta_f, text="🔄", bg="#E0E7FF", fg="#3730A3",
                  relief="flat", cursor="hand2", padx=4,
                  font=("Segoe UI", 8),
                  command=self._force_regen_id
                  ).grid(row=1, column=4, sticky="w", padx=(0, 6), pady=2)

        # Label trạng thái (✓ OK / ⚠ trùng / ✘ sai format)
        self._id_status = tk.Label(meta_f, text="", bg=_BG,
                                     font=("Segoe UI", 8, "italic"))
        self._id_status.grid(row=1, column=5, sticky="w", pady=2)

        # Hàng "Cùng nhóm:" — hiển thị các ID cùng group đã có trong NHCH
        self._id_group_lbl = tk.Label(
            meta_f, text="", bg=_BG, fg="#6B7280",
            font=("Consolas", 8), anchor="w", wraplength=600, justify="left")
        self._id_group_lbl.grid(row=2, column=0, columnspan=7,
                                  sticky="w", padx=(0, 16), pady=(0, 2))

        # Trigger live update + dup check
        self._qtype_var.trace_add("write", lambda *_: self._on_meta_change())
        self._topic_var.trace_add("write", lambda *_: self._on_meta_change())
        self._level_var.trace_add("write", lambda *_: self._on_meta_change())
        # User tự gõ ID → check trùng + sai format real-time
        self._id_var.trace_add("write", lambda *_: self._on_id_change())
        # Run check 1 lần đầu để show status + group list
        self._on_id_change(initial=True)
        row += 1

        tk.Frame(content, bg="#E2E8F0", height=1).grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1

        # ── BODY 2 CỘT ───────────────────────────────────────────────────────
        # Cột trái: Nội dung câu hỏi + các phương án/ý
        # Cột phải: Lời giải tổng quát + lời giải từng ý (DS)
        # Cả hai cùng row, sticky="nsew" để giãn theo chiều rộng đều.
        left_col = tk.Frame(content, bg=_BG)
        left_col.grid(row=row, column=0, sticky="nsew", padx=(12, 6), pady=4)
        left_col.columnconfigure(0, weight=1)
        right_col = tk.Frame(content, bg=_BG)
        right_col.grid(row=row, column=1, sticky="nsew", padx=(6, 12), pady=4)
        right_col.columnconfigure(0, weight=1)
        body_row = row
        row += 1

        # === CỘT TRÁI ===
        left_row = 0

        # ── Nội dung câu hỏi ──
        tk.Label(left_col, text="Nội dung câu hỏi:", bg=_BG, fg=_FG,
                 font=_FONT_B).grid(row=left_row, column=0, sticky="w", pady=(0, 4))
        left_row += 1

        # Text giãn cả 2 chiều khi maximize (nsew + rowconfigure weight=1)
        self._question_text = tk.Text(left_col, height=20, wrap="word",
                                       font=("Consolas", 11), bg="#F8FAFC")
        self._question_text.grid(row=left_row, column=0, sticky="nsew", pady=(0, 4))
        left_col.rowconfigure(left_row, weight=3)   # ưu tiên giãn cho câu hỏi
        self._question_text.insert("1.0", q.question or "")
        left_row += 1
        left_row = self._add_image_row(left_col, q.question_image,
                                       "img_question", left_row,
                                       {"padx": 0, "pady": 4})

        # ── Phương án (cho câu TN) ──
        if q.qtype == "TN" and q.options:
            tk.Label(left_col, text="Các phương án:", bg=_BG, fg=_FG,
                     font=_FONT_B).grid(row=left_row, column=0, sticky="w",
                                        pady=(8, 4))
            left_row += 1

            self._opt_entries: dict[str, tk.Text] = {}
            opt_panel = tk.Frame(left_col, bg=_BG)
            opt_panel.grid(row=left_row, column=0, sticky="ew", pady=(0, 4))
            opt_panel.columnconfigure(1, weight=1)
            for r_i, (letter, text) in enumerate(q.options.items()):
                tk.Label(opt_panel, text=f"{letter}.", bg=_BG, fg=_FG2,
                         font=_FONT_B, width=2, anchor="nw"
                         ).grid(row=r_i, column=0, sticky="nw", padx=(0, 4),
                                pady=(4, 4))
                txt = tk.Text(opt_panel, height=2, wrap="word",
                              font=("Consolas", 9), bg="#FFFFFF",
                              relief="solid", bd=1, highlightthickness=0)
                txt.grid(row=r_i, column=1, sticky="ew", padx=(0, 4), pady=2)
                txt.insert("1.0", text or "")
                self._opt_entries[letter] = txt
                btn_wrap = self._add_compact_image_button(
                    opt_panel, q.option_images.get(letter, ""),
                    f"img_opt_{letter}",
                )
                btn_wrap.grid(row=r_i, column=2, sticky="ne", padx=(0, 0),
                              pady=4)
            left_row += 1

            ans_f = tk.Frame(left_col, bg=_BG)
            ans_f.grid(row=left_row, column=0, sticky="w", pady=(4, 4))
            tk.Label(ans_f, text="Đáp án đúng:", bg=_BG, fg=_FG2, font=_FONT
                     ).pack(side="left", padx=(0, 6))
            self._answer_var = tk.StringVar(value=q.answer)
            ttk.Combobox(ans_f, textvariable=self._answer_var,
                         values=list(q.options.keys()), width=8, state="readonly",
                         ).pack(side="left")
            left_row += 1
        elif q.qtype == "TLN":
            self._opt_entries = {}
            ans_f = tk.Frame(left_col, bg=_BG)
            ans_f.grid(row=left_row, column=0, sticky="w", pady=(8, 4))
            tk.Label(ans_f, text="Đáp án:", bg=_BG, fg=_FG2, font=_FONT
                     ).pack(side="left", padx=(0, 6))
            self._answer_var = tk.StringVar(value=q.answer)
            tk.Entry(ans_f, textvariable=self._answer_var, font=_FONT, width=30
                     ).pack(side="left")
            left_row += 1
        else:
            # DS / TL: q.answer không dùng (DS → q.answers dict per-item;
            # TL → đáp án nằm trong lời giải). Vẫn giữ StringVar để _save
            # không phải thay đổi nhiều, nhưng KHÔNG hiển thị field gây nhầm.
            self._opt_entries = {}
            self._answer_var = tk.StringVar(value=q.answer)

        # ── Các ý Đúng/Sai (cho câu DS) — card style ─────────────────────────
        if q.qtype == "DS" and q.items:
            tk.Label(left_col, text="Các ý Đúng / Sai:", bg=_BG, fg=_FG,
                     font=_FONT_B).grid(row=left_row, column=0, sticky="w",
                                        pady=(8, 4))
            left_row += 1

            ds_panel = tk.Frame(left_col, bg=_BG)
            ds_panel.grid(row=left_row, column=0, sticky="ew", pady=(0, 4))
            ds_panel.columnconfigure(0, weight=1)

            self._ds_entries: dict[str, tk.Text] = {}
            self._ds_answers = {}
            for r_i, (label, text) in enumerate(q.items.items()):
                card = tk.Frame(ds_panel, bg="#F8FAFC",
                                highlightbackground="#E2E8F0",
                                highlightthickness=1, bd=0)
                card.grid(row=r_i, column=0, sticky="ew", pady=(0, 6))
                card.columnconfigure(1, weight=1)

                # Header row: label + radio + image button
                tk.Label(card, text=f"Ý {label})", bg="#F8FAFC", fg=_FG,
                         font=_FONT_B
                         ).grid(row=0, column=0, sticky="w", padx=(8, 6),
                                pady=(6, 2))

                var_a = tk.BooleanVar(value=q.answers.get(label, False))
                ds_choice = tk.Frame(card, bg="#F8FAFC")
                ds_choice.grid(row=0, column=1, sticky="w", padx=0, pady=(6, 2))
                tk.Radiobutton(ds_choice, text=" Đúng", variable=var_a,
                               value=True, bg="#F8FAFC", fg=_GREEN,
                               selectcolor="#D1FAE5", activebackground="#ECFDF5",
                               font=("Segoe UI", 9, "bold"),
                               ).pack(side="left", padx=(0, 8))
                tk.Radiobutton(ds_choice, text=" Sai", variable=var_a,
                               value=False, bg="#F8FAFC", fg=_RED,
                               selectcolor="#FEE2E2", activebackground="#FEF2F2",
                               font=("Segoe UI", 9, "bold"),
                               ).pack(side="left")

                btn_wrap = self._add_compact_image_button(
                    card, q.item_images.get(label, ""), f"img_item_{label}",
                )
                btn_wrap.configure(bg="#F8FAFC")
                btn_wrap.grid(row=0, column=2, sticky="e", padx=(0, 8),
                              pady=(6, 2))

                # Body: Text widget nhiều dòng wrap=word (4 dòng để hiện trọn
                # các ý có công thức dài + ngữ cảnh)
                txt = tk.Text(card, height=4, wrap="word",
                              font=("Consolas", 9), bg="#FFFFFF",
                              relief="solid", bd=1, highlightthickness=0)
                txt.grid(row=1, column=0, columnspan=3, sticky="ew",
                         padx=8, pady=(0, 8))
                txt.insert("1.0", text or "")
                self._ds_entries[label] = txt
                self._ds_answers[label] = var_a
            left_row += 1
        else:
            self._ds_entries = {}
            self._ds_answers = {}

        # === CỘT PHẢI ===
        right_row = 0

        # ── Lời giải tổng quát ───────────────────────────────────────────────
        sol_title = "Lời giải tổng quát:" if (q.qtype == "DS" and q.items) else "Lời giải:"
        tk.Label(right_col, text=sol_title, bg=_BG, fg=_FG,
                 font=_FONT_B).grid(row=right_row, column=0, sticky="w",
                                    pady=(0, 4))
        right_row += 1

        # Khi là DS, lời giải tổng quát thường ngắn (intro); khi không phải DS
        # (TN/TLN/TL), lời giải là toàn bộ → cho cao hơn + giãn theo window.
        sol_height = 8 if (q.qtype == "DS" and q.items) else 22
        self._solution_text = tk.Text(right_col, height=sol_height, wrap="word",
                                       font=("Consolas", 11), bg="#F8FAFC")
        self._solution_text.grid(row=right_row, column=0, sticky="nsew",
                                 pady=(0, 4))
        right_col.rowconfigure(right_row, weight=3)  # giãn dọc theo window
        self._solution_text.insert("1.0", q.solution or "")
        right_row += 1
        right_row = self._add_image_row(right_col, q.solution_image,
                                        "img_solution", right_row,
                                        {"padx": 0, "pady": 4})

        # ── Lời giải từng ý (chỉ DS) — Text 7 dòng/ý để hiển thị đủ chi tiết ─
        self._ds_sol_texts: dict[str, tk.Text] = {}
        if q.qtype == "DS" and q.items:
            tk.Label(right_col, text="Lời giải từng ý:", bg=_BG, fg=_FG,
                     font=_FONT_B).grid(row=right_row, column=0, sticky="w",
                                        pady=(8, 4))
            right_row += 1

            sol_per_panel = tk.Frame(right_col, bg=_BG)
            sol_per_panel.grid(row=right_row, column=0, sticky="ew", pady=(0, 4))
            sol_per_panel.columnconfigure(0, weight=1)
            for r_i, label in enumerate(q.items.keys()):
                # Mỗi ý là 1 card riêng cho dễ phân biệt với cột bên trái.
                card = tk.Frame(sol_per_panel, bg="#F8FAFC",
                                highlightbackground="#E2E8F0",
                                highlightthickness=1, bd=0)
                card.grid(row=r_i, column=0, sticky="ew", pady=(0, 6))
                card.columnconfigure(0, weight=1)
                tk.Label(card, text=f"Ý {label})", bg="#F8FAFC", fg=_FG,
                         font=_FONT_B, anchor="w"
                         ).grid(row=0, column=0, sticky="w", padx=8,
                                pady=(6, 2))
                txt = tk.Text(card, height=7, wrap="word",
                              font=("Consolas", 9), bg="#FFFFFF",
                              relief="solid", bd=1, highlightthickness=0)
                txt.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))
                txt.insert("1.0", q.item_solutions.get(label, "") or "")
                self._ds_sol_texts[label] = txt
            right_row += 1

        # ── Nút lưu / hủy (spans full width below body) ──────────────────────
        btn_f = tk.Frame(content, bg=_BG)
        btn_f.grid(row=row, column=0, columnspan=2, pady=12)

        tk.Button(
            btn_f, text="  Lưu thay đổi  ", font=_FONT_B,
            bg=_GREEN, fg="white", activebackground="#059669",
            relief="flat", cursor="hand2", padx=14, pady=6,
            command=self._save,
        ).pack(side="left", padx=8)

        tk.Button(
            btn_f, text="  Hủy  ", font=_FONT,
            bg="#F1F5F9", fg=_FG2, activebackground="#E2E8F0",
            relief="flat", cursor="hand2", padx=14, pady=6,
            command=self.destroy,
        ).pack(side="left")

    def _save(self):
        q = self._q

        q.qtype = self._qtype_var.get()
        q.level = self._level_var.get()
        q.topic = self._topic_var.get().strip()

        # ── Validate ID trước khi commit ──────────────────────────────
        if hasattr(self, "_id_var"):
            new_id = self._id_var.get().strip()
            existing = self._get_existing_qids() - {q.question_id or ""}
            from tkinter import messagebox

            # 1. ID rỗng → block save
            if not new_id:
                messagebox.showwarning(
                    "Thiếu ID", "Câu hỏi cần có ID. Bấm 🔄 để auto-tạo.",
                    parent=self)
                return

            # 2. ID trùng NHCH → confirm overwrite
            if new_id in existing:
                if not messagebox.askyesno(
                    "ID trùng trong NHCH",
                    f"ID '{new_id}' đã tồn tại trong NHCH.\n\n"
                    f"Lưu vẫn sẽ GHI ĐÈ câu cũ. Tiếp tục?",
                    icon="warning", parent=self): return

            # 3. Chỉ hỏi chuẩn hoá khi user đổi sang ID custom mới.
            # Câu legacy đang dùng ID custom vẫn phải lưu được khi sửa nội dung.
            original_id = (q.question_id or "").strip()
            if new_id != original_id and not self._is_auto_format(new_id):
                choice = messagebox.askyesnocancel(
                    "ID không theo chuẩn",
                    f"ID '{new_id}' không khớp format chuẩn "
                    f"[Lớp][Môn][Ch][Mức][Loại]-[Seq] (vd 12D1N1-0001).\n\n"
                    f"• Yes  → Auto-fix về ID chuẩn\n"
                    f"• No   → Lưu nguyên ID custom\n"
                    f"• Cancel → Quay lại sửa",
                    parent=self)
                if choice is None:    # Cancel
                    return
                if choice is True:    # Yes → regen
                    self._force_regen_id()
                    new_id = self._id_var.get().strip()

            q.question_id = new_id
        try:
            q.points = float(self._points_var.get())
        except ValueError:
            pass

        q.question = self._question_text.get("1.0", "end-1c").strip()
        q.answer = self._answer_var.get().strip()
        q.solution = self._solution_text.get("1.0", "end-1c").strip()

        # Cập nhật phương án TN (_opt_entries giờ là dict[letter] -> Text widget)
        if self._opt_entries:
            for letter, txt_widget in self._opt_entries.items():
                q.options[letter] = txt_widget.get("1.0", "end-1c").strip()

        # Cập nhật các ý Đúng/Sai (_ds_entries giờ là dict[label] -> Text widget)
        if self._ds_entries:
            for label, txt_widget in self._ds_entries.items():
                q.items[label] = txt_widget.get("1.0", "end-1c").strip()
            for label, var in self._ds_answers.items():
                q.answers[label] = var.get()
            # Lời giải từng ý — chỉ ghi đè khi user thực sự nhập
            for label, txt_widget in self._ds_sol_texts.items():
                q.item_solutions[label] = txt_widget.get("1.0", "end-1c").strip()

        # Lưu ảnh
        if "img_question" in self._img_vars:
            q.question_image = self._img_vars["img_question"].get()
        if "img_solution" in self._img_vars:
            q.solution_image = self._img_vars["img_solution"].get()
        if q.qtype == "TN":
            q.option_images = {}
            for letter in q.options:
                key = f"img_opt_{letter}"
                if key in self._img_vars:
                    val = self._img_vars[key].get()
                    if val:
                        q.option_images[letter] = val
        if q.qtype == "DS":
            q.item_images = {}
            for label in (self._ds_entries or {}):
                key = f"img_item_{label}"
                if key in self._img_vars:
                    val = self._img_vars[key].get()
                    if val:
                        q.item_images[label] = val

        if self._on_save:
            self._on_save()

        self.destroy()
