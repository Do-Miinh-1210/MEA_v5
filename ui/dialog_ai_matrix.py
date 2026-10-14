"""
ui/dialog_ai_matrix.py — Dialog xác nhận kết quả nhận diện ma trận bằng AI.

Hiển thị bảng preview các câu hỏi mà AI đã nhận diện,
cho phép người dùng chỉnh sửa trước khi chèn vào bảng ma trận.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional

from core.models import MatrixData, MatrixRow


class AIMatrixConfirmDialog(tk.Toplevel):
    """Dialog xác nhận cấu trúc ma trận được AI nhận diện."""

    def __init__(self, parent, matrix_data: MatrixData):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("🤖 Xác nhận cấu trúc ma trận — Nhận diện bằng AI")

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(1100, int(sw * 0.7))
        h = min(650, int(sh * 0.7))
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(True, True)
        self.minsize(800, 500)
        self.grab_set()

        self._matrix = matrix_data
        self._result: Optional[MatrixData] = None
        self._build()
        self.focus_force()

    @property
    def result(self) -> Optional[MatrixData]:
        return self._result

    def _build(self):
        # ── Header ──
        hdr = tk.Frame(self, bg="#0F2D52")
        hdr.pack(fill="x")
        tk.Frame(self, bg="#10B981", height=3).pack(fill="x")

        tk.Label(
            hdr, text="🤖  AI ĐÃ NHẬN DIỆN CẤU TRÚC MA TRẬN",
            bg="#0F2D52", fg="white", font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=12, pady=8)

        # ── Info ──
        info_f = tk.Frame(self, bg="#EBF5FF")
        info_f.pack(fill="x", padx=12, pady=(10, 0))

        rows = self._matrix.rows
        tn = sum(1 for r in rows if r.qtype == "TN")
        ds = sum(1 for r in rows if r.qtype == "DS")
        tl = sum(1 for r in rows if r.qtype in ("TL", "TLN"))
        total_pts = sum(r.points for r in rows)

        info_text = (
            f"📋 Tiêu đề: {self._matrix.title}    "
            f"⏱ Thời gian: {self._matrix.time_str or 'N/A'}    "
            f"📊 Tổng: {len(rows)} câu ({tn} TN + {ds} Đ/S + {tl} TL)    "
            f"💯 Tổng điểm: {total_pts:.1f}"
        )
        tk.Label(
            info_f, text=info_text, bg="#EBF5FF", fg="#1E40AF",
            font=("Segoe UI", 8, "bold"), wraplength=820, justify="left",
        ).pack(padx=10, pady=6, anchor="w")

        # ── Nút hành động (ghim cố định ở đáy cửa sổ) ──
        btn_f = tk.Frame(self, bg="#E2E8F0")
        btn_f.pack(side="bottom", fill="x", padx=12, pady=(4, 10))

        tk.Frame(btn_f, bg="#10B981", height=2).pack(fill="x", pady=(0, 8))

        btn_row = tk.Frame(btn_f, bg="#E2E8F0")
        btn_row.pack(fill="x", padx=8, pady=(0, 6))

        tk.Label(
            btn_row, text="⚠️  Vui lòng kiểm tra lại trước khi xác nhận",
            bg="#E2E8F0", fg="#92400E", font=("Segoe UI", 8, "italic"),
        ).pack(side="left", padx=6)

        tk.Button(
            btn_row, text="  ✅ XÁC NHẬN — Sử dụng ma trận này  ",
            bg="#10B981", fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", padx=12, pady=6,
            activebackground="#059669", command=self._on_accept,
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            btn_row, text="  ✖ Hủy bỏ  ",
            bg="#64748B", fg="white", font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", padx=10, pady=6,
            activebackground="#475569", command=self._on_cancel,
        ).pack(side="right")

        # ── Bảng kết quả (chiếm phần còn lại ở giữa) ──
        tree_f = tk.Frame(self)
        tree_f.pack(fill="both", expand=True, padx=12, pady=(8, 0))

        cols = ("STT", "Chủ đề / Nội dung", "Loại", "Mức độ", "Điểm", "Yêu cầu cần đạt")
        self._tree = ttk.Treeview(tree_f, columns=cols, show="headings", selectmode="extended")

        widths = {"STT": 40, "Chủ đề / Nội dung": 220, "Loại": 52, "Mức độ": 58, "Điểm": 48, "Yêu cầu cần đạt": 280}
        for c in cols:
            self._tree.heading(c, text=c)
            self._tree.column(c, width=widths[c], minwidth=40)

        vsb = ttk.Scrollbar(tree_f, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_f, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_f.rowconfigure(0, weight=1)
        tree_f.columnconfigure(0, weight=1)

        # Load data
        for i, r in enumerate(rows):
            qtype_map = {"TN": "Trắc nghiệm", "DS": "Đúng-Sai", "TLN": "Trả lời ngắn", "TL": "Tự luận"}
            level_map = {"NB": "Nhận biết", "TH": "Thông hiểu", "VD": "Vận dụng"}
            tag = r.level
            self._tree.insert("", "end", iid=str(i), values=(
                r.stt,
                r.topic[:60],
                qtype_map.get(r.qtype, r.qtype),
                level_map.get(r.level, r.level),
                f"{r.points:.2f}",
                r.requirement[:80],
            ), tags=(tag,))

        self._tree.tag_configure("NB", background="#E8F5E9")
        self._tree.tag_configure("TH", background="#E3F2FD")
        self._tree.tag_configure("VD", background="#FFF3E0")



    def _on_accept(self):
        self._result = self._matrix
        self.destroy()

    def _on_cancel(self):
        self._result = None
        self.destroy()
