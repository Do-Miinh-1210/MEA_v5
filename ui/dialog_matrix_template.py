"""
ui/dialog_matrix_template.py — Modal picker cho [SPEED-3] Matrix Templates.

Hiển thị danh sách template dạng card grid 2 cột, mỗi card có:
  • Icon + tên template
  • Mô tả ngắn
  • Stats (số câu / loại / thời lượng / lớp)
  • Tags
  • Nút "Chọn" — load template vào tab Câu hỏi

User có thể filter theo lớp ở thanh trên cùng.

Khi user chọn 1 template → callback `on_pick(matrix_data)` được gọi với
MatrixData ready-to-use; dialog tự đóng.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from core.models import MatrixData
from services.matrix_templates import list_templates, load_template


# ── Color palette ──────────────────────────────────────────────────────────
_BG          = "#F8FAFC"
_HEADER_BG   = "#0F2D52"
_HEADER_FG   = "#FFFFFF"
_CARD_BG     = "#FFFFFF"
_CARD_BORDER = "#E2E8F0"
_TITLE_FG    = "#0F172A"
_DESC_FG     = "#475569"
_TAG_BG      = "#EFF6FF"
_TAG_FG      = "#1E40AF"
_BTN_PRIMARY = "#10B981"
_BTN_HOVER   = "#059669"
_FILTER_BG   = "#E2E8F0"
_STAT_BG     = "#F1F5F9"


class MatrixTemplatePickerDialog(tk.Toplevel):
    """Modal dialog chọn template ma trận."""

    def __init__(
        self,
        parent: tk.Misc,
        on_pick: Callable[[MatrixData, dict], None],
        current_grade: Optional[str] = None,
    ):
        super().__init__(parent)
        try:
            from ui import set_dialog_icon
            set_dialog_icon(self)
        except Exception:
            pass

        self.title("📂 Chọn template ma trận đề")

        # Center on screen
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(1100, max(900, sw // 2))
        h = min(800, max(620, int(sh * 0.78)))
        x = (sw - w) // 2
        y = max(0, (sh - h) // 2 - 20)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(True, True)
        self.minsize(900, 600)

        self.grab_set()
        self.focus_set()
        self.configure(bg=_BG)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._on_pick = on_pick
        self._current_grade = str(current_grade) if current_grade else None
        # Pre-select grade ngay từ StringVar init — `_build` đọc giá trị này
        # để render đúng button trạng thái ban đầu.
        # Hợp lệ: "all" hoặc "6".."12".
        valid_grades = {"6", "7", "8", "9", "10", "11", "12"}
        initial_grade = (
            self._current_grade
            if self._current_grade and self._current_grade in valid_grades
            else "all"
        )
        self._filter_grade  = tk.StringVar(value=initial_grade)
        self._search_text   = tk.StringVar(value="")
        self._templates: list[dict] = []

        self._build()
        self._refresh_grid()
        self.focus_force()

    # ──────────────────────────────────────────────────────────────────────
    #  BUILD
    # ──────────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Header ──────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=_HEADER_BG)
        hdr.pack(fill="x")
        tk.Frame(self, bg=_BTN_PRIMARY, height=3).pack(fill="x")

        tk.Label(
            hdr, text="📂  THƯ VIỆN TEMPLATE MA TRẬN ĐỀ",
            bg=_HEADER_BG, fg=_HEADER_FG,
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left", padx=16, pady=12)

        tk.Label(
            hdr,
            text="(Chọn 1 template — sẽ thay toàn bộ ma trận hiện tại)",
            bg=_HEADER_BG, fg="#94A3B8",
            font=("Segoe UI", 9, "italic"),
        ).pack(side="left", padx=4, pady=12)

        # ── Filter bar ──────────────────────────────────────────────────
        flt = tk.Frame(self, bg=_FILTER_BG)
        flt.pack(fill="x", pady=(0, 0))

        tk.Label(flt, text="🔍 Tìm:", bg=_FILTER_BG, fg=_TITLE_FG,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(12, 4), pady=6)
        search_entry = tk.Entry(
            flt, textvariable=self._search_text,
            font=("Segoe UI", 10), relief="solid", bd=1,
            width=28,
        )
        search_entry.pack(side="left", padx=4, pady=6, ipady=2)
        self._search_text.trace_add("write", lambda *_: self._refresh_grid())

        tk.Label(flt, text="  |  Lớp:",
                 bg=_FILTER_BG, fg=_TITLE_FG,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(8, 4), pady=6)

        # Grade buttons — tất cả / 6 / 7 / 8 / 9 / 10 / 11 / 12
        self._grade_btns: dict[str, tk.Label] = {}
        for val, label in [
            ("all", "Tất cả"),
            ("6", "6"), ("7", "7"), ("8", "8"), ("9", "9"),
            ("10", "10"), ("11", "11"), ("12", "12"),
        ]:
            btn = tk.Label(
                flt, text=f" {label} ",
                bg=_BTN_PRIMARY if val == self._filter_grade.get() else "#CBD5E1",
                fg="white" if val == self._filter_grade.get() else "#1E293B",
                font=("Segoe UI", 9, "bold"),
                cursor="hand2", padx=8, pady=4,
            )
            btn.pack(side="left", padx=2, pady=6)
            btn.bind("<Button-1>", lambda _e, v=val: self._set_grade(v))
            self._grade_btns[val] = btn

        # NOTE: grade pre-select đã handle qua StringVar init ở __init__,
        # buttons render đúng trạng thái ngay từ vòng for ở trên.

        # ── Footer (close button) — pack BEFORE body to anchor bottom ───
        footer = tk.Frame(self, bg=_BG)
        footer.pack(fill="x", side="bottom", padx=12, pady=10)

        self._info_lbl = tk.Label(
            footer, text="",
            bg=_BG, fg=_DESC_FG,
            font=("Segoe UI", 9, "italic"),
        )
        self._info_lbl.pack(side="left")

        tk.Button(
            footer, text="  ✖ Đóng  ",
            bg="#64748B", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", padx=14, pady=6,
            activebackground="#475569",
            command=self.destroy,
        ).pack(side="right")

        # ── Body: scrollable card grid ──────────────────────────────────
        body_wrap = tk.Frame(self, bg=_BG)
        body_wrap.pack(fill="both", expand=True, padx=12, pady=10)

        self._canvas = tk.Canvas(body_wrap, bg=_BG, highlightthickness=0)
        vsb = ttk.Scrollbar(body_wrap, orient="vertical",
                             command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._grid_inner = tk.Frame(self._canvas, bg=_BG)
        self._grid_window = self._canvas.create_window(
            (0, 0), window=self._grid_inner, anchor="nw",
        )

        self._grid_inner.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(self._grid_window, width=e.width),
        )

        # Mouse wheel scroll
        def _on_mousewheel(e):
            n = int(-5 * (e.delta / 120))
            if n == 0:
                n = -1 if e.delta > 0 else 1
            self._canvas.yview_scroll(n, "units")
        self._canvas.bind("<MouseWheel>", _on_mousewheel)
        self._grid_inner.bind("<MouseWheel>", _on_mousewheel)
        self._mousewheel_handler = _on_mousewheel

    # ──────────────────────────────────────────────────────────────────────
    #  FILTER
    # ──────────────────────────────────────────────────────────────────────

    def _set_grade(self, val: str):
        """Switch grade filter, update button styles."""
        self._filter_grade.set(val)
        for k, btn in self._grade_btns.items():
            if k == val:
                btn.configure(bg=_BTN_PRIMARY, fg="white")
            else:
                btn.configure(bg="#CBD5E1", fg="#1E293B")
        self._refresh_grid()

    # ──────────────────────────────────────────────────────────────────────
    #  GRID REFRESH
    # ──────────────────────────────────────────────────────────────────────

    def _refresh_grid(self):
        """Re-render card grid theo filter hiện tại."""
        # Clear
        for w in self._grid_inner.winfo_children():
            w.destroy()

        # Reload + filter
        grade = self._filter_grade.get()
        grade_filter = None if grade == "all" else grade
        all_t = list_templates(filter_grade=grade_filter)

        search = self._search_text.get().strip().lower()
        if search:
            def _match(t):
                hay = " ".join([
                    t.get("name", ""),
                    t.get("description", ""),
                    " ".join(t.get("tags", [])),
                    t.get("title", ""),
                ]).lower()
                return search in hay
            templates = [t for t in all_t if _match(t)]
        else:
            templates = all_t

        self._templates = templates

        # Info label
        n = len(templates)
        if n == 0:
            self._info_lbl.config(text="Không có template nào khớp bộ lọc.")
            # Empty state in grid
            tk.Label(
                self._grid_inner,
                text=("📭  Không tìm thấy template.\n\n"
                      "Thử chọn lớp khác hoặc xoá từ khoá tìm."),
                bg=_BG, fg=_DESC_FG,
                font=("Segoe UI", 11),
                justify="center", pady=80,
            ).pack(fill="both", expand=True)
            return
        else:
            self._info_lbl.config(text=f"{n} template phù hợp.")

        # Grid 2 columns
        self._grid_inner.grid_columnconfigure(0, weight=1, uniform="card_col")
        self._grid_inner.grid_columnconfigure(1, weight=1, uniform="card_col")

        for i, t in enumerate(templates):
            self._build_card(t, row=i // 2, col=i % 2)

    # ──────────────────────────────────────────────────────────────────────
    #  CARD BUILDER
    # ──────────────────────────────────────────────────────────────────────

    def _build_card(self, t: dict, row: int, col: int):
        """1 card hiển thị 1 template."""
        outer = tk.Frame(
            self._grid_inner, bg=_CARD_BORDER,
        )
        outer.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        outer.bind("<MouseWheel>", self._mousewheel_handler)

        card = tk.Frame(outer, bg=_CARD_BG)
        card.pack(fill="both", expand=True, padx=1, pady=1)
        card.bind("<MouseWheel>", self._mousewheel_handler)

        # ── Header: icon + name ────────────────────────────────────────
        hdr = tk.Frame(card, bg=_CARD_BG)
        hdr.pack(fill="x", padx=12, pady=(10, 4))
        hdr.bind("<MouseWheel>", self._mousewheel_handler)

        icon_lbl = tk.Label(
            hdr, text=t.get("icon", "📋"),
            bg=_CARD_BG, font=("Segoe UI", 22),
        )
        icon_lbl.pack(side="left", padx=(0, 8))
        icon_lbl.bind("<MouseWheel>", self._mousewheel_handler)

        name_f = tk.Frame(hdr, bg=_CARD_BG)
        name_f.pack(side="left", fill="x", expand=True)
        name_f.bind("<MouseWheel>", self._mousewheel_handler)

        tk.Label(
            name_f, text=t.get("name", ""),
            bg=_CARD_BG, fg=_TITLE_FG,
            font=("Segoe UI", 11, "bold"),
            anchor="w", justify="left", wraplength=380,
        ).pack(anchor="w", fill="x")

        # Subtitle: lớp + thời lượng
        sub = f"  Lớp {t.get('grade', '?')} • {t.get('time_str', '?')}"
        tk.Label(
            name_f, text=sub,
            bg=_CARD_BG, fg=_DESC_FG,
            font=("Segoe UI", 9, "italic"),
            anchor="w",
        ).pack(anchor="w", fill="x")

        # ── Description ────────────────────────────────────────────────
        desc = t.get("description", "")
        if desc:
            tk.Label(
                card, text=desc,
                bg=_CARD_BG, fg=_DESC_FG,
                font=("Segoe UI", 9),
                anchor="w", justify="left",
                wraplength=440, padx=12, pady=4,
            ).pack(fill="x")

        # ── Stats badge ────────────────────────────────────────────────
        stats = t.get("stats", {})
        stat_text = (
            f"📊 {t.get('n_rows', 0)} câu • "
            f"TN:{stats.get('TN', 0)} "
            f"DS:{stats.get('DS', 0)} "
            f"TLN:{stats.get('TLN', 0)} "
            f"TL:{stats.get('TL', 0)}"
        )
        stat_frame = tk.Frame(card, bg=_STAT_BG)
        stat_frame.pack(fill="x", padx=12, pady=(6, 4))
        tk.Label(
            stat_frame, text=stat_text,
            bg=_STAT_BG, fg=_TITLE_FG,
            font=("Segoe UI", 9, "bold"),
            padx=8, pady=4, anchor="w",
        ).pack(anchor="w", fill="x")

        # ── Tags row ───────────────────────────────────────────────────
        tags = t.get("tags", [])
        if tags:
            tag_row = tk.Frame(card, bg=_CARD_BG)
            tag_row.pack(fill="x", padx=12, pady=(2, 4))
            for tag in tags[:5]:
                tk.Label(
                    tag_row, text=f" #{tag} ",
                    bg=_TAG_BG, fg=_TAG_FG,
                    font=("Segoe UI", 8, "bold"),
                    padx=4, pady=1,
                ).pack(side="left", padx=2)

        # ── Action buttons ─────────────────────────────────────────────
        btn_row = tk.Frame(card, bg=_CARD_BG)
        btn_row.pack(fill="x", padx=12, pady=(6, 10))

        choose_btn = tk.Button(
            btn_row, text="  ✓ Chọn template này  ",
            bg=_BTN_PRIMARY, fg="white",
            activebackground=_BTN_HOVER, activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", bd=0,
            padx=10, pady=6,
            command=lambda tid=t["id"]: self._on_choose(tid),
        )
        choose_btn.pack(side="left")

        preview_btn = tk.Button(
            btn_row, text="  👁 Xem trước  ",
            bg="#EFF6FF", fg=_TAG_FG,
            activebackground="#DBEAFE",
            font=("Segoe UI", 9),
            relief="flat", cursor="hand2", bd=0,
            padx=10, pady=6,
            command=lambda tid=t["id"]: self._on_preview(tid),
        )
        preview_btn.pack(side="left", padx=6)

    # ──────────────────────────────────────────────────────────────────────
    #  ACTIONS
    # ──────────────────────────────────────────────────────────────────────

    def _on_choose(self, template_id: str):
        """User chọn template → load + callback + đóng dialog."""
        matrix = load_template(template_id)
        if matrix is None:
            messagebox.showerror(
                "Lỗi",
                f"Không load được template: {template_id}",
                parent=self,
            )
            return

        # Tìm metadata để gửi kèm callback
        meta = next((t for t in self._templates if t["id"] == template_id), {})

        try:
            self._on_pick(matrix, meta)
        except Exception as e:
            messagebox.showerror(
                "Lỗi áp dụng template", str(e),
                parent=self,
            )
            return

        self.destroy()

    def _on_preview(self, template_id: str):
        """Mở mini-preview window hiển thị các dòng MatrixRow của template."""
        matrix = load_template(template_id)
        if matrix is None:
            messagebox.showerror(
                "Lỗi", f"Không load được template: {template_id}",
                parent=self,
            )
            return

        pv = tk.Toplevel(self)
        try:
            from ui import set_dialog_icon
            set_dialog_icon(pv)
        except Exception:
            pass
        pv.title(f"👁 Xem trước — {matrix.title[:50]}")
        pv.geometry("900x600")
        pv.transient(self)
        pv.grab_set()

        # Header
        tk.Label(
            pv, text=matrix.title,
            bg=_HEADER_BG, fg="white",
            font=("Segoe UI", 11, "bold"),
            pady=8,
        ).pack(fill="x")
        tk.Label(
            pv, text=f"⏱ {matrix.time_str}  •  {len(matrix.rows)} câu",
            bg="#F1F5F9", fg=_TITLE_FG,
            font=("Segoe UI", 9, "italic"),
            pady=4,
        ).pack(fill="x")

        # Treeview
        cols = ("stt", "qtype", "level", "topic", "requirement", "points")
        tree = ttk.Treeview(pv, columns=cols, show="headings", height=20)
        tree.heading("stt", text="STT")
        tree.heading("qtype", text="Loại")
        tree.heading("level", text="Mức")
        tree.heading("topic", text="Chủ đề")
        tree.heading("requirement", text="Yêu cầu")
        tree.heading("points", text="Điểm")
        tree.column("stt", width=40, anchor="center")
        tree.column("qtype", width=55, anchor="center")
        tree.column("level", width=45, anchor="center")
        tree.column("topic", width=180, anchor="w")
        tree.column("requirement", width=320, anchor="w")
        tree.column("points", width=50, anchor="center")

        # Row coloring
        tree.tag_configure("NB", background="#E8F5E9")
        tree.tag_configure("TH", background="#E3F2FD")
        tree.tag_configure("VD", background="#FFF3E0")

        for r in matrix.rows:
            tree.insert("", "end", values=(
                r.stt, r.qtype, r.level,
                r.topic[:50], r.requirement[:60], r.points,
            ), tags=(r.level,))

        tree.pack(fill="both", expand=True, padx=8, pady=4)

        btn_f = tk.Frame(pv, bg=_BG)
        btn_f.pack(fill="x", padx=8, pady=8)

        tk.Button(
            btn_f, text="  ✓ Áp dụng template này  ",
            bg=_BTN_PRIMARY, fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", padx=14, pady=6,
            activebackground=_BTN_HOVER,
            command=lambda: (pv.destroy(), self._on_choose(template_id)),
        ).pack(side="right", padx=4)

        tk.Button(
            btn_f, text="  Đóng  ",
            bg="#64748B", fg="white",
            font=("Segoe UI", 10),
            relief="flat", cursor="hand2", padx=14, pady=6,
            activebackground="#475569",
            command=pv.destroy,
        ).pack(side="right")
