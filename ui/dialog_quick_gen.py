"""
ui/dialog_quick_gen.py — Dialog "Tạo đề nhanh" cho desktop app.
Cho phép người dùng tự nhập dữ liệu đề kiểm tra (chủ đề, loại câu, mức độ, số câu)
hoặc dùng mẫu nhanh theo thời lượng.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from core.quick_matrix import (
    get_available_durations,
    get_topics_for_grade,
    get_chapters_for_grade,
    build_quick_matrix,
    build_quick_matrix_custom,
    TOPICS_BY_GRADE,
)
from core.models import MatrixData, MatrixRow, DSItem
from config import POINTS_MAP
from ui.theme import get_checkbox_images, get_radio_images


# ══════════════════════════════════════════════════════════════════════════════
#  QTYPE / LEVEL constants
# ══════════════════════════════════════════════════════════════════════════════

QTYPES = ["TN", "DS", "TLN", "TL"]
QTYPE_LABELS = {
    "TN": "Trắc nghiệm",
    "DS": "Đúng – Sai",
    "TLN": "Trả lời ngắn",
    "TL": "Tự luận",
}
LEVELS = ["NB", "TH", "VD"]
LEVEL_LABELS = {
    "NB": "Nhận biết",
    "TH": "Thông hiểu",
    "VD": "Vận dụng",
}


class QuickGenDialog(tk.Toplevel):
    """Dialog cho phép nhập dữ liệu đề kiểm tra thủ công hoặc dùng mẫu nhanh."""

    def __init__(
        self,
        parent,
        on_accept: Callable[[MatrixData, str, str], None],
    ):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("Tạo đề nhanh")

        # ── THUẬT TOÁN TỰ ĐỘNG CANH GIỮA MÀN HÌNH ──
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(1100, max(950, sw // 2))   # 950–1100px
        h = min(820, max(700, int(sh * 0.75)))  # 700–820px
        x = (sw - w) // 2
        y = max(0, (sh - h) // 2 - 20)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(True, True)
        self.minsize(950, 700)
        self.maxsize(sw, sh - 40)
        # Không cho maximize bằng double-click titlebar (Windows)
        self.attributes("-toolwindow", False)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.grab_set()
        self.configure(bg="#F9F7F4")
        self._on_accept = on_accept
        self._row_widgets: list[dict] = []
        self._build()
        self.focus_force()

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        # ── Header với logo ──
        hdr = tk.Frame(self, bg="#0F2D52")
        hdr.pack(fill="x")
        tk.Frame(self, bg="#10B981", height=4).pack(fill="x")

        try:
            from PIL import Image, ImageTk
            from pathlib import Path
            _logo_path = Path(__file__).parent.parent / "assets" / "app.png"
            if not _logo_path.exists():
                _logo_path = Path(__file__).parent.parent / "assets" / "icon4.png"
            if _logo_path.exists():
                _img = Image.open(_logo_path).convert("RGBA").resize((36, 36), Image.LANCZOS)
                self._hdr_logo = ImageTk.PhotoImage(_img)
                tk.Label(hdr, image=self._hdr_logo, bg="#0F2D52").pack(side="left", padx=(16, 6), pady=10)
        except Exception:
            pass

        tk.Label(
            hdr, text="TẠO ĐỀ NHANH — Thiết lập cấu trúc đề kiểm tra",
            bg="#0F2D52", fg="white", font=("Segoe UI", 13, "bold"),
        ).pack(side="left", padx=6, pady=10)

        # ── Nút Action CỐ ĐỊNH Ở DƯỚI CÙNG (Pack TRƯỚC để không bao giờ bị che) ──
        self._build_bottom_bar()

        # ── Tab control: Mẫu nhanh / Tự nhập ──
        style = ttk.Style()
        style.configure("QuickGen.TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[14, 5])
        
        self._notebook = ttk.Notebook(self, style="QuickGen.TNotebook")
        self._notebook.pack(fill="both", expand=True, padx=12, pady=(10, 10))

        tab_manual = tk.Frame(self._notebook, bg="#F9F7F4")
        tab_preset = tk.Frame(self._notebook, bg="#F9F7F4")
        self._notebook.add(tab_manual, text="  Tự nhập dữ liệu  ")
        self._notebook.add(tab_preset, text="  Dùng mẫu nhanh  ")

        self._build_manual_tab(tab_manual)
        self._build_preset_tab(tab_preset)

        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _build_bottom_bar(self):
        """Khung chứa nút Tạo đề luôn luôn nằm ở dưới đáy Dialog."""
        self._action_frame = tk.Frame(self, bg="#E2E8F0")
        self._action_frame.pack(fill="x", side="bottom", padx=12, pady=(0, 12))

        tk.Frame(self._action_frame, bg="#10B981", height=2).pack(fill="x", pady=(0, 10))

        btn_container = tk.Frame(self._action_frame, bg="#E2E8F0")
        btn_container.pack(fill="x", padx=8, pady=(0, 10))

        tk.Button(
            btn_container, text="TẠO ĐỀ NGAY",
            bg="#10B981", fg="white", font=("Segoe UI", 12, "bold"),
            relief="flat", cursor="hand2", width=18, padx=12, pady=10,
            activebackground="#059669", command=self._on_ok,
        ).pack(side="right", padx=(10, 0))

        tk.Button(
            btn_container, text="Hủy bỏ",
            bg="#64748B", fg="white", font=("Segoe UI", 11, "bold"),
            relief="flat", cursor="hand2", width=12, padx=10, pady=10,
            activebackground="#475569", command=self.destroy,
        ).pack(side="right")

        self._act_summary = tk.Label(
            btn_container, text="", bg="#E2E8F0", fg="#1F497D",
            font=("Segoe UI", 11, "bold", "italic"))
        self._act_summary.pack(side="left", padx=8, pady=10)

    def _on_tab_changed(self, event):
        current_tab = self._notebook.index(self._notebook.select())
        if current_tab == 0:
            self._update_summary()
        else:
            self._act_summary.config(text="Hệ thống sẽ tự động bốc câu theo thời lượng.")

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB 1: Tự nhập dữ liệu
    # ──────────────────────────────────────────────────────────────────────────

    def _build_manual_tab(self, parent: tk.Frame):
        frm_info = ttk.LabelFrame(parent, text=" Thông tin chung ")
        frm_info.pack(fill="x", padx=12, pady=(10, 4))
        g = tk.Frame(frm_info, bg="#F9F7F4")
        g.pack(fill="x", padx=10, pady=10)

        tk.Label(g, text="Môn:", bg="#F9F7F4", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        self._m_subj_var = tk.StringVar(value="Toán")
        ttk.Entry(g, textvariable=self._m_subj_var, width=16, font=("Segoe UI", 10)).grid(row=0, column=1, padx=6, sticky="w")

        tk.Label(g, text="Lớp:", bg="#F9F7F4", font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=(16, 0))
        self._m_grade_var = tk.StringVar(value="12")
        cb_m_grade = ttk.Combobox(g, textvariable=self._m_grade_var, values=[str(i) for i in range(1, 13)], width=6, state="readonly", font=("Segoe UI", 10))
        cb_m_grade.grid(row=0, column=3, padx=6, sticky="w")
        cb_m_grade.bind("<<ComboboxSelected>>", lambda _: self._refresh_row_topics())

        tk.Label(g, text="Kỳ:", bg="#F9F7F4", font=("Segoe UI", 10)).grid(row=0, column=4, sticky="w", padx=(16, 0))
        self._m_sem_var = tk.StringVar(value="Giữa kì II")
        ttk.Combobox(g, textvariable=self._m_sem_var, values=["Giữa kì I", "Cuối kì I", "Giữa kì II", "Cuối kì II"], width=14, state="readonly", font=("Segoe UI", 10)).grid(row=0, column=5, padx=6, sticky="w")

        tk.Label(g, text="Năm:", bg="#F9F7F4", font=("Segoe UI", 10)).grid(row=0, column=6, sticky="w", padx=(16, 0))
        self._m_year_var = tk.StringVar(value="2025-2026")
        ttk.Entry(g, textvariable=self._m_year_var, width=12, font=("Segoe UI", 10)).grid(row=0, column=7, padx=6, sticky="w")

        tk.Label(g, text="Thời gian:", bg="#F9F7F4", font=("Segoe UI", 10)).grid(row=0, column=8, sticky="w", padx=(16, 0))
        self._m_time_var = tk.StringVar(value="90 phút")
        ttk.Entry(g, textvariable=self._m_time_var, width=10, font=("Segoe UI", 10)).grid(row=0, column=9, padx=6, sticky="w")

        # ── Yêu cầu cho AI ──
        frm_ai_req = ttk.LabelFrame(parent, text=" Yêu cầu thêm cho AI (tùy chọn) ")
        frm_ai_req.pack(fill="x", padx=12, pady=(4, 4))
        self._m_ai_req_var = tk.StringVar()
        ai_req_entry = ttk.Entry(frm_ai_req, textvariable=self._m_ai_req_var, font=("Segoe UI", 10))
        ai_req_entry.pack(fill="x", padx=10, pady=8, ipady=3)
        ai_req_entry.insert(0, "VD: Câu hỏi phải có bảng số liệu, câu hỏi thực tế, không quá khó...")
        ai_req_entry.bind("<FocusIn>", lambda e: (ai_req_entry.delete(0, "end") if "VD:" in ai_req_entry.get() else None))
        ai_req_entry.bind("<FocusOut>", lambda e: (ai_req_entry.insert(0, "VD: Câu hỏi phải có bảng số liệu, câu hỏi thực tế, không quá khó...") if not ai_req_entry.get().strip() else None))

        tb = tk.Frame(parent, bg="#F9F7F4")
        tb.pack(fill="x", padx=12, pady=(10, 4))

        tk.Button(tb, text="+ Thêm hàng", bg="#3B82F6", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", width=13, padx=6, pady=4, command=self._add_row).pack(side="left", padx=4)
        tk.Button(tb, text="Thêm mẫu 5 hàng", bg="#8B5CF6", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", width=18, padx=6, pady=4, command=self._add_sample_rows).pack(side="left", padx=4)
        tk.Button(tb, text="Xóa tất cả", bg="#6B7280", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", width=12, padx=6, pady=4, command=self._clear_all_rows).pack(side="left", padx=4)

        # ── Table header co giãn ──
        hdr_f = tk.Frame(parent, bg="#E2E8F0")
        hdr_f.pack(fill="x", padx=12, pady=(6, 0))
        headers = [
            ("STT", 4), ("Chủ đề / Nội dung", 25),
            ("Loại câu", 15), ("Mức độ", 15),
            ("Số câu", 7), ("Điểm/câu", 7), ("Yêu cầu cần đạt", 18), ("Xóa", 4),
        ]
        for i, (text, w) in enumerate(headers):
            tk.Label(hdr_f, text=text, bg="#CBD5E1", fg="#1E293B", font=("Segoe UI", 10, "bold"), width=w, anchor="center", relief="groove", borderwidth=1, pady=6).grid(row=0, column=i, sticky="nsew", padx=0)

        # Cấu hình trọng số để lấp đầy màn hình
        hdr_f.columnconfigure(1, weight=2)
        hdr_f.columnconfigure(6, weight=3)
        hdr_f.columnconfigure(7, weight=0)

        # ── Scrollable row area ──
        canvas_f = tk.Frame(parent, bg="#F9F7F4", bd=1, relief="solid")
        canvas_f.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self._row_canvas = tk.Canvas(canvas_f, bg="#FAFAFA", highlightthickness=0)
        vsb = ttk.Scrollbar(
            canvas_f,
            orient="vertical",
            command=self._row_canvas.yview,
        )
        self._row_inner = tk.Frame(self._row_canvas, bg="#FAFAFA")

        self._row_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._row_canvas.pack(side="left", fill="both", expand=True)

        self._row_window = self._row_canvas.create_window((0, 0), window=self._row_inner, anchor="nw")

        self._row_inner.bind("<Configure>", lambda e: self._row_canvas.configure(scrollregion=self._row_canvas.bbox("all")))
        self._row_canvas.bind("<Configure>", lambda e: self._row_canvas.itemconfig(self._row_window, width=e.width))

        # Cuộn chuột — nhanh hơn (nhiều đơn vị mỗi notch)
        def _canvas_scroll(e):
            if self._row_inner.winfo_reqheight() > self._row_canvas.winfo_height():
                self._row_canvas.yview_scroll(-4 * (e.delta // 120), "units")
        self._canvas_scroll_fn = _canvas_scroll
        self._row_canvas.bind("<MouseWheel>", self._canvas_scroll_fn)
        self._row_inner.bind("<MouseWheel>", self._canvas_scroll_fn)

        for _ in range(3):
            self._add_row()

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB 2: Mẫu nhanh (Giao diện 2 cột thông minh)
    # ──────────────────────────────────────────────────────────────────────────

    def _build_preset_tab(self, parent: tk.Frame):
        tk.Label(parent, text="Chọn thời lượng → App sẽ tự động bốc câu và tạo cấu trúc ma trận chuẩn.", bg="#F9F7F4", fg="#3B82F6", font=("Segoe UI", 10, "italic", "bold")).pack(pady=(12, 4), anchor="w", padx=16)

        body = tk.Frame(parent, bg="#F9F7F4")
        body.pack(fill="both", expand=True, padx=16, pady=4)

        top_frame = tk.Frame(body, bg="#F9F7F4")
        top_frame.pack(fill="x", pady=4)

        frm_dur = ttk.LabelFrame(top_frame, text=" Thời lượng đề thi ")
        frm_dur.pack(side="left", fill="y", padx=(0, 6))
        self._dur_var = tk.StringVar(value="45 phút")
        dur_f = tk.Frame(frm_dur, bg="#FAFAFA")
        dur_f.pack(fill="both", expand=True, padx=12, pady=10)

        durations = get_available_durations()
        self._rb_off, self._rb_on = get_radio_images(22)
        for dur in durations:
            tk.Radiobutton(
                dur_f,
                text=f"  {dur['label']} ({dur['desc']})",
                variable=self._dur_var,
                value=dur["label"],
                command=self._on_duration_change,
                font=("Segoe UI", 11),
                bg="#FAFAFA",
                activebackground="#F0F9FF",
                activeforeground="#1E293B",
                image=self._rb_off,
                selectimage=self._rb_on,
                indicatoron=False,
                compound="left",
                relief="flat",
                overrelief="flat",
                bd=0,
                anchor="w",
                padx=6,
                pady=8,
            ).pack(anchor="w", pady=2)

        # ── Tùy chỉnh số lượng câu hỏi ──
        frm_qty = ttk.LabelFrame(top_frame, text=" Số lượng câu (tùy chỉnh) ")
        frm_qty.pack(side="left", fill="y", padx=(6, 6))
        qty_f = tk.Frame(frm_qty, bg="#FAFAFA")
        qty_f.pack(fill="both", expand=True, padx=12, pady=10)

        self._qty_tn = tk.IntVar(value=12)
        self._qty_ds = tk.IntVar(value=2)
        self._qty_tln = tk.IntVar(value=3)
        self._qty_tl = tk.IntVar(value=0)

        _qty_items = [
            ("TN (Trắc nghiệm):", self._qty_tn, 0, 30),
            ("DS (Đúng-Sai):", self._qty_ds, 0, 10),
            ("TLN (Trả lời ngắn):", self._qty_tln, 0, 10),
            ("TL (Tự luận):", self._qty_tl, 0, 10),
        ]
        for i, (lbl, var, lo, hi) in enumerate(_qty_items):
            tk.Label(qty_f, text=lbl, bg="#FAFAFA", font=("Segoe UI", 10)).grid(row=i, column=0, sticky="w", pady=4)
            box = tk.Frame(qty_f, bg="#FAFAFA")
            box.grid(row=i, column=1, sticky="w", padx=(10, 0), pady=4)

            def _dec(v=var, l=lo):
                v.set(max(l, int(v.get()) - 1))

            def _inc(v=var, h=hi):
                v.set(min(h, int(v.get()) + 1))

            tk.Button(
                box, text="−", font=("Segoe UI", 12, "bold"),
                width=2, relief="flat", bg="#64748B", fg="white",
                activebackground="#475569", cursor="hand2",
                padx=4, pady=2, command=_dec,
            ).pack(side="left")
            tk.Entry(
                box, textvariable=var, width=4,
                font=("Segoe UI", 11, "bold"), justify="center",
                relief="solid", bd=1,
            ).pack(side="left", padx=4, ipady=2)
            tk.Button(
                box, text="+", font=("Segoe UI", 12, "bold"),
                width=2, relief="flat", bg="#0284C7", fg="white",
                activebackground="#0369A1", cursor="hand2",
                padx=4, pady=2, command=_inc,
            ).pack(side="left")

        self._on_duration_change()  # khởi tạo giá trị mặc định

        frm_info = ttk.LabelFrame(top_frame, text=" Thông tin đề ")
        frm_info.pack(side="left", fill="both", expand=True, padx=(6, 0))
        g2 = tk.Frame(frm_info, bg="#FAFAFA")
        g2.pack(fill="both", expand=True, padx=12, pady=10)

        tk.Label(g2, text="Môn:", bg="#FAFAFA", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=8)
        self._p_subj_var = tk.StringVar(value="Toán")
        ttk.Entry(g2, textvariable=self._p_subj_var, width=16, font=("Segoe UI", 10)).grid(row=0, column=1, padx=10, sticky="w")

        tk.Label(g2, text="Lớp:", bg="#FAFAFA", font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=(16, 0))
        self._p_grade_var = tk.StringVar(value="12")
        cb_grade = ttk.Combobox(g2, textvariable=self._p_grade_var, values=[str(i) for i in range(1, 13)], width=6, state="readonly", font=("Segoe UI", 10))
        cb_grade.grid(row=0, column=3, padx=10, sticky="w")
        cb_grade.bind("<<ComboboxSelected>>", lambda _: self._refresh_topics())

        tk.Label(g2, text="Kỳ:", bg="#FAFAFA", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=8)
        self._p_sem_var = tk.StringVar(value="Giữa kì II")
        ttk.Combobox(g2, textvariable=self._p_sem_var, values=["Giữa kì I", "Cuối kì I", "Giữa kì II", "Cuối kì II"], width=16, state="readonly", font=("Segoe UI", 10)).grid(row=1, column=1, padx=10, sticky="w")

        tk.Label(g2, text="Năm:", bg="#FAFAFA", font=("Segoe UI", 10)).grid(row=1, column=2, sticky="w", padx=(16, 0))
        self._p_year_var = tk.StringVar(value="2025-2026")
        ttk.Entry(g2, textvariable=self._p_year_var, width=14, font=("Segoe UI", 10)).grid(row=1, column=3, padx=10, sticky="w")

        # ── Yêu cầu cho AI (Preset tab) ──
        frm_ai_req2 = ttk.LabelFrame(body, text=" Yêu cầu thêm cho AI (tùy chọn) ")
        frm_ai_req2.pack(fill="x", pady=(4, 4))
        self._p_ai_req_var = tk.StringVar()
        ai_req2_entry = ttk.Entry(frm_ai_req2, textvariable=self._p_ai_req_var, font=("Segoe UI", 10))
        ai_req2_entry.pack(fill="x", padx=10, pady=8, ipady=3)
        ai_req2_entry.insert(0, "VD: Câu hỏi phải có bảng số liệu, câu hỏi thực tế, không quá khó...")
        ai_req2_entry.bind("<FocusIn>", lambda e: (ai_req2_entry.delete(0, "end") if "VD:" in ai_req2_entry.get() else None))
        ai_req2_entry.bind("<FocusOut>", lambda e: (ai_req2_entry.insert(0, "VD: Câu hỏi phải có bảng số liệu, câu hỏi thực tế, không quá khó...") if not ai_req2_entry.get().strip() else None))

        frm_topics = ttk.LabelFrame(body, text=" Chọn chương / bài học (click > để mở rộng - bỏ tick chương = bỏ qua cả chương đó) ")
        frm_topics.pack(fill="both", expand=True, pady=(10, 0))

        add_topic_f = tk.Frame(frm_topics, bg="#F9F7F4")
        add_topic_f.pack(fill="x", padx=8, pady=(8, 4))

        self._custom_topic_var = tk.StringVar()
        custom_entry = ttk.Entry(add_topic_f, textvariable=self._custom_topic_var, font=("Segoe UI", 10))
        custom_entry.pack(side="left", fill="x", expand=True, padx=(4, 8), ipady=3)
        custom_entry.insert(0, "Nhập chủ đề mới nếu chưa có trong danh sách bên dưới...")
        
        custom_entry.bind("<FocusIn>", lambda e: (custom_entry.delete(0, "end") if "Nhập chủ đề mới" in custom_entry.get() else None))
        custom_entry.bind("<FocusOut>", lambda e: (custom_entry.insert(0, "Nhập chủ đề mới nếu chưa có trong danh sách bên dưới...") if not custom_entry.get().strip() else None))
        custom_entry.bind("<Return>", lambda e: self._add_custom_topic())

        tk.Button(add_topic_f, text="+ THÊM CHỦ ĐỀ", font=("Segoe UI", 9, "bold"), bg="#3B82F6", fg="white", activebackground="#2563EB", relief="flat", cursor="hand2", width=15, padx=8, pady=3, command=self._add_custom_topic).pack(side="left")

        canvas_f = tk.Frame(frm_topics, bg="white", bd=1, relief="solid")
        canvas_f.pack(fill="both", expand=True, padx=12, pady=(6, 6))

        self._topic_canvas = tk.Canvas(canvas_f, bg="white", highlightthickness=0)
        vsb_topic = ttk.Scrollbar(
            canvas_f,
            orient="vertical",
            command=self._topic_canvas.yview,
        )
        self._topic_inner = tk.Frame(self._topic_canvas, bg="white")

        self._topic_canvas.configure(yscrollcommand=vsb_topic.set)
        vsb_topic.pack(side="right", fill="y")
        self._topic_canvas.pack(side="left", fill="both", expand=True)

        self._topic_window = self._topic_canvas.create_window((0, 0), window=self._topic_inner, anchor="nw")
        self._topic_inner.bind("<Configure>", lambda e: self._topic_canvas.configure(scrollregion=self._topic_canvas.bbox("all")))
        self._topic_canvas.bind("<Configure>", lambda e: self._topic_canvas.itemconfig(self._topic_window, width=e.width))

        def _on_topic_scroll(e):
            n = int(-5 * (e.delta / 120))
            if n == 0:
                n = -1 if e.delta > 0 else 1
            self._topic_canvas.yview_scroll(n, "units")

        self._topic_canvas.bind("<MouseWheel>", _on_topic_scroll)
        self._topic_inner.bind("<MouseWheel>", _on_topic_scroll)

        self._topic_vars: list[tuple[str, tk.BooleanVar]] = []
        self._refresh_topics()

        sel_f = tk.Frame(frm_topics, bg="#F9F7F4")
        sel_f.pack(fill="x", padx=12, pady=(2, 10))
        tk.Button(sel_f, text="Chọn tất cả", font=("Segoe UI", 9, "bold"), bg="#10B981", fg="white", relief="flat", cursor="hand2", width=12, pady=4, command=self._select_all).pack(side="left", padx=(0, 8))
        tk.Button(sel_f, text="Bỏ chọn", font=("Segoe UI", 9, "bold"), bg="#64748B", fg="white", relief="flat", cursor="hand2", width=10, pady=4, command=self._deselect_all).pack(side="left")


    # ══════════════════════════════════════════════════════════════════════════
    #  DURATION CHANGE → CẬP NHẬT SỐ LƯỢNG CÂU
    # ══════════════════════════════════════════════════════════════════════════

    _DURATION_DEFAULTS = {
        "15 phút": (7, 0, 0, 0),
        "45 phút": (12, 2, 3, 0),
        "60 phút": (15, 3, 4, 1),
        "90 phút": (18, 4, 6, 2),
    }

    def _on_duration_change(self):
        """Cập nhật spinbox số lượng câu khi chọn thời lượng khác."""
        dur = self._dur_var.get()
        defaults = self._DURATION_DEFAULTS.get(dur, (12, 2, 3, 0))
        self._qty_tn.set(defaults[0])
        self._qty_ds.set(defaults[1])
        self._qty_tln.set(defaults[2])
        self._qty_tl.set(defaults[3])

    # ══════════════════════════════════════════════════════════════════════════
    #  ROW MANAGEMENT (Manual tab)
    # ══════════════════════════════════════════════════════════════════════════

    def _repack_action_frame(self):
        self._row_canvas.update_idletasks()
        # Chỉ cuộn xuống đáy khi nội dung tràn khỏi vùng hiển thị
        if self._row_inner.winfo_reqheight() > self._row_canvas.winfo_height():
            self._row_canvas.yview_moveto(1.0)

    def _add_row(self, topic: str = "", qtype: str = "TN", level: str = "NB",
                 count: int = 1, points: float = 0.0, requirement: str = ""):
        idx = len(self._row_widgets)

        row_f = tk.Frame(self._row_inner, bg="#FFFFFF" if idx % 2 == 0 else "#F8FAFC")
        row_f.pack(fill="x", padx=0, pady=0)
        bg = row_f.cget("bg")

        stt_lbl = tk.Label(row_f, text=str(idx + 1), width=4, bg=bg, font=("Segoe UI", 10, "bold"), anchor="center")
        stt_lbl.grid(row=0, column=0, sticky="nsew", pady=4)

        topic_var = tk.StringVar(value=topic)
        topic_entry = ttk.Combobox(row_f, textvariable=topic_var, width=22, font=("Segoe UI", 10))
        # Load topics based on current grade
        grade = self._m_grade_var.get() if hasattr(self, "_m_grade_var") else "12"
        topic_entry["values"] = get_topics_for_grade(grade)[:30]
        topic_entry.grid(row=0, column=1, sticky="nsew", padx=2, pady=4)

        qtype_var = tk.StringVar(value=qtype)
        qtype_cb = ttk.Combobox(row_f, textvariable=qtype_var, values=[f"{k} — {v}" for k, v in QTYPE_LABELS.items()], width=14, state="readonly", font=("Segoe UI", 10))
        qtype_cb.set(f"{qtype} — {QTYPE_LABELS.get(qtype, qtype)}")
        qtype_cb.grid(row=0, column=2, sticky="nsew", padx=2, pady=4)
        qtype_cb.bind("<<ComboboxSelected>>", lambda e, rf=row_f: self._on_qtype_change(e, rf))

        level_var = tk.StringVar(value=level)
        level_cb = ttk.Combobox(row_f, textvariable=level_var, values=[f"{k} — {v}" for k, v in LEVEL_LABELS.items()], width=14, state="readonly", font=("Segoe UI", 10))
        level_cb.set(f"{level} — {LEVEL_LABELS.get(level, level)}")
        level_cb.grid(row=0, column=3, sticky="nsew", padx=2, pady=4)

        count_var = tk.StringVar(value=str(count))
        count_entry = ttk.Entry(row_f, textvariable=count_var, width=8, justify="center", font=("Segoe UI", 10, "bold"))
        count_entry.grid(row=0, column=4, sticky="nsew", padx=2, pady=4)

        if points <= 0: points = POINTS_MAP.get(qtype, 1.0)
        points_var = tk.StringVar(value=str(points))
        points_entry = ttk.Entry(row_f, textvariable=points_var, width=8, justify="center", font=("Segoe UI", 10))
        points_entry.grid(row=0, column=5, sticky="nsew", padx=2, pady=4)

        req_var = tk.StringVar(value=requirement)
        req_entry = ttk.Entry(row_f, textvariable=req_var, width=18, font=("Segoe UI", 10))
        req_entry.grid(row=0, column=6, sticky="nsew", padx=2, pady=4)

        # Nút xóa hàng này
        del_btn = tk.Button(
            row_f, text="X", bg="#FEE2E2", fg="#DC2626",
            font=("Segoe UI", 10), relief="flat", cursor="hand2", width=3,
            activebackground="#FECACA",
            command=lambda: self._remove_row_by_widget(row_f),
        )
        del_btn.grid(row=0, column=7, sticky="nsew", padx=2, pady=4)

        # Auto-fill requirement when topic is selected
        def _on_topic_selected(e, tv=topic_var, rv=req_var):
            t = tv.get().strip()
            if t and not rv.get().strip():
                saved = self._load_requirements().get(t, "")
                if saved:
                    rv.set(saved)
        topic_entry.bind("<<ComboboxSelected>>", _on_topic_selected)

        # Save requirement when focus leaves
        def _on_req_leave(e, tv=topic_var, rv=req_var):
            t = tv.get().strip()
            r = rv.get().strip()
            if t and r:
                self._save_requirement(t, r)
        req_entry.bind("<FocusOut>", _on_req_leave)

        # CẤU HÌNH TRỌNG SỐ CHO HÀNG DỮ LIỆU BÊN TRONG CỘT
        row_f.columnconfigure(1, weight=2)
        row_f.columnconfigure(6, weight=3)

        # Bind cuộn chuột cho tất cả widget trong hàng
        row_f.bind("<MouseWheel>", self._canvas_scroll_fn)
        for child in row_f.winfo_children():
            child.bind("<MouseWheel>", self._canvas_scroll_fn)

        self._row_widgets.append({
            "frame": row_f, "stt_lbl": stt_lbl, "topic": topic_var, "topic_entry": topic_entry,
            "qtype_cb": qtype_cb, "qtype": qtype_var,
            "level_cb": level_cb, "level": level_var, "count": count_var, "points": points_var, "requirement": req_var,
        })

        self._repack_action_frame()
        self._update_summary()

    def _find_row_by_frame(self, frame) -> dict | None:
        for rw in self._row_widgets:
            if rw["frame"] is frame:
                return rw
        return None

    def _on_qtype_change(self, event, frame) -> None:
        rw = self._find_row_by_frame(frame)
        if not rw:
            return
        raw = rw["qtype_cb"].get()
        qt = raw.split(" — ")[0].strip() if " — " in raw else raw.strip()
        default_pts = POINTS_MAP.get(qt, 1.0)
        rw["points"].set(str(default_pts))

        # DS: hiện/ẩn 4 hàng nhỏ a,b,c,d
        if qt == "DS":
            self._show_ds_subitems(rw)
        else:
            self._hide_ds_subitems(rw)

        self._update_summary()

    def _show_ds_subitems(self, rw: dict):
        """Hiện 4 hàng phụ a,b,c,d cho câu Đúng-Sai."""
        if "ds_frame" in rw and rw["ds_frame"].winfo_exists():
            return  # đã hiện rồi

        parent = rw["frame"]
        ds_f = tk.Frame(parent, bg="#F0E6FF", bd=1, relief="groove")
        ds_f.grid(row=1, column=0, columnspan=8, sticky="ew", padx=(30, 4), pady=(2, 4))

        ds_widgets = []
        default_levels = ["NB", "TH", "VD", "VD"]
        for i, label in enumerate(["a", "b", "c", "d"]):
            row_f = tk.Frame(ds_f, bg="#F0E6FF")
            row_f.pack(fill="x", padx=4, pady=1)

            tk.Label(row_f, text=f"  {label})", bg="#F0E6FF",
                     font=("Segoe UI", 9, "bold"), fg="#6B21A8",
                     width=3).pack(side="left")

            lv_var = tk.StringVar(value=default_levels[i])
            lv_cb = ttk.Combobox(row_f, textvariable=lv_var,
                                 values=[f"{k} — {v}" for k, v in LEVEL_LABELS.items()],
                                 width=14, state="readonly", font=("Segoe UI", 9))
            lv_cb.set(f"{default_levels[i]} — {LEVEL_LABELS.get(default_levels[i], '')}")
            lv_cb.pack(side="left", padx=2)

            req_var = tk.StringVar()
            req_e = ttk.Entry(row_f, textvariable=req_var, font=("Segoe UI", 9))
            req_e.pack(side="left", fill="x", expand=True, padx=2)
            req_e.insert(0, f"Yêu cầu ý {label}...")
            req_e.bind("<FocusIn>", lambda e, w=req_e: (w.delete(0, "end") if "Yêu cầu ý" in w.get() else None))

            ds_widgets.append({"label": label, "level": lv_var, "level_cb": lv_cb, "requirement": req_var})

        rw["ds_frame"] = ds_f
        rw["ds_widgets"] = ds_widgets

    def _hide_ds_subitems(self, rw: dict):
        """Ẩn 4 hàng phụ a,b,c,d."""
        if "ds_frame" in rw and rw["ds_frame"].winfo_exists():
            rw["ds_frame"].destroy()
        rw.pop("ds_frame", None)
        rw.pop("ds_widgets", None)

    def _remove_row_by_widget(self, frame: tk.Frame):
        """Xóa một hàng cụ thể theo widget frame."""
        target = None
        for rw in self._row_widgets:
            if rw["frame"] is frame:
                target = rw
                break
        if not target:
            return
        self._row_widgets.remove(target)
        if "ds_frame" in target and target["ds_frame"].winfo_exists():
            target["ds_frame"].destroy()
        target["frame"].destroy()
        self._renumber_rows()
        self._repack_action_frame()
        self._update_summary()

    def _clear_all_rows(self):
        for rw in self._row_widgets:
            if "ds_frame" in rw:
                try: rw["ds_frame"].destroy()
                except Exception: pass
            rw["frame"].destroy()
        self._row_widgets.clear()
        self._repack_action_frame()
        self._update_summary()

    def _add_sample_rows(self):
        grade = self._m_grade_var.get()
        topics = TOPICS_BY_GRADE.get(grade, ["Chủ đề 1", "Chủ đề 2", "Chủ đề 3"])
        samples = [
            (topics[0 % len(topics)], "TN", "NB", 4, 0, ""),
            (topics[1 % len(topics)], "TN", "TH", 3, 0, ""),
            (topics[2 % len(topics)], "DS", "TH", 2, 0, ""),
            (topics[0 % len(topics)], "TLN", "VD", 2, 0, ""),
            (topics[1 % len(topics)], "TL", "VD", 1, 0, ""),
        ]
        for t, qt, lv, cnt, pts, req in samples: self._add_row(t, qt, lv, cnt, pts, req)

    def _renumber_rows(self):
        for i, rw in enumerate(self._row_widgets): rw["stt_lbl"].configure(text=str(i + 1))

    def _refresh_row_topics(self):
        """Cập nhật danh sách gợi ý chủ đề cho tất cả hàng khi đổi lớp."""
        grade = self._m_grade_var.get() if hasattr(self, "_m_grade_var") else "12"
        new_topics = get_topics_for_grade(grade)[:30]
        for rw in self._row_widgets:
            topic_entry = rw.get("topic_entry")
            if topic_entry and topic_entry.winfo_exists():
                topic_entry["values"] = new_topics

    def _update_summary(self):
        total_q = 0; total_pts = 0.0
        for rw in self._row_widgets:
            try: cnt = int(rw["count"].get())
            except ValueError: cnt = 0
            try: pts = float(rw["points"].get())
            except ValueError: pts = 0
            total_q += cnt
            total_pts += cnt * pts
        txt = f"Tổng số: {total_q} câu  |  Tổng điểm: {total_pts:.1f} điểm"
        if hasattr(self, "_act_summary"): self._act_summary.configure(text=txt)

    # ══════════════════════════════════════════════════════════════════════════
    #  PRESET TAB helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_topics(self):
        """Refresh hierarchical chapter/lesson tree.

        Mỗi chương = 1 frame có:
          • Header: [>/v] expand + checkbox + tên chương + (n bài)
          • Body (collapsed by default trừ khi chương đó có ≤ 5 bài):
              indented list các bài (lessons) với checkbox riêng

        Khi tick chapter checkbox → tự tick/uncheck tất cả lessons con.
        Khi user uncheck 1 lesson → chapter chuyển trạng thái indeterminate.
        """
        for w in self._topic_inner.winfo_children():
            w.destroy()
        self._topic_vars.clear()
        # Map chapter_name → {var, lesson_vars, expand_state, expand_btn}
        self._chapter_state: dict = {}

        grade = self._p_grade_var.get()
        chapters_data = get_chapters_for_grade(grade)

        # Append custom topics as their own "chapter"
        custom = self._load_custom_topics().get(grade, [])
        if custom:
            chapters_data = chapters_data + [{
                "chapter": "Chủ đề tùy chỉnh của bạn",
                "lessons": custom,
                "topics":  custom,  # custom dùng nguyên chuỗi user nhập
            }]

        # Single column (chapter là 1 block ngang full-width, không grid 2 cột)
        self._topic_inner.grid_columnconfigure(0, weight=1)
        try:
            self._topic_inner.grid_columnconfigure(1, weight=0)
        except tk.TclError:
            pass

        def _scroll_handler(e):
            n = int(-5 * (e.delta / 120))
            if n == 0:
                n = -1 if e.delta > 0 else 1
            self._topic_canvas.yview_scroll(n, "units")

        self._cb_off, self._cb_on = get_checkbox_images(20)

        for ci, chap in enumerate(chapters_data):
            self._build_chapter_block(
                ci, chap, _scroll_handler,
            )

        # Update manual tab topic suggestions (flat list)
        if hasattr(self, "_row_widgets"):
            flat_topics = [
                t for state in self._chapter_state.values()
                for t in state["topic_list"]
            ]
            for rw in self._row_widgets:
                if "topic_entry" in rw:
                    rw["topic_entry"]["values"] = flat_topics[:30]

    def _build_chapter_block(self, ci: int, chap: dict, scroll_handler) -> None:
        """Tạo 1 block chương: header (expand + checkbox + tên) + lessons list."""
        chapter_name = chap.get("chapter", f"Chương {ci+1}")
        lessons      = chap.get("lessons", [])
        topics       = chap.get("topics", [chapter_name])
        n_lessons    = len(lessons)
        # Mặc định expand nếu ≤ 5 bài, collapse nếu nhiều
        is_expanded  = n_lessons <= 5

        # ── Block frame ─────────────────────────────────────────────────
        block = tk.Frame(self._topic_inner, bg="white",
                         highlightbackground="#E2E8F0", highlightthickness=1)
        block.grid(row=ci, column=0, columnspan=2, sticky="ew",
                   padx=8, pady=(6, 2))
        block.bind("<MouseWheel>", scroll_handler)

        # ── Header row: [>/v] checkbox + chapter name (n bài) ─────────
        hdr = tk.Frame(block, bg="#F1F5F9")
        hdr.pack(fill="x")
        hdr.bind("<MouseWheel>", scroll_handler)

        # Expand/collapse button
        expand_var = tk.StringVar(value="v" if is_expanded else ">")
        expand_btn = tk.Label(
            hdr, textvariable=expand_var,
            bg="#F1F5F9", fg="#475569",
            font=("Consolas", 10, "bold"),
            width=2,
            padx=8, cursor="hand2",
        )
        expand_btn.pack(side="left")
        expand_btn.bind("<MouseWheel>", scroll_handler)

        # Chapter checkbox
        chap_var = tk.BooleanVar(value=True)
        chap_cb = tk.Checkbutton(
            hdr, text="", variable=chap_var,
            bg="#F1F5F9", activebackground="#F1F5F9",
            image=self._cb_off, selectimage=self._cb_on,
            indicatoron=False, compound="left",
            relief="flat", overrelief="flat", bd=0,
            padx=0, pady=0, cursor="hand2",
        )
        chap_cb.pack(side="left", padx=(0, 6), pady=4)
        chap_cb.bind("<MouseWheel>", scroll_handler)

        # Chapter name label (clickable to expand)
        chap_label = tk.Label(
            hdr, text=f"{chapter_name}  ({n_lessons} bài)" if n_lessons else chapter_name,
            bg="#F1F5F9", fg="#0F172A",
            font=("Segoe UI", 11, "bold"),
            anchor="w", cursor="hand2",
            padx=4, pady=6,
        )
        chap_label.pack(side="left", fill="x", expand=True)
        chap_label.bind("<MouseWheel>", scroll_handler)

        # ── Body: lessons frame ─────────────────────────────────────────
        body = tk.Frame(block, bg="white")
        if is_expanded:
            body.pack(fill="x")
        body.bind("<MouseWheel>", scroll_handler)

        # Tạo state trước khi tạo lesson cb (để callback truy cập được)
        state = {
            "var":         chap_var,
            "lesson_vars": [],   # list[tuple[topic_str, BooleanVar]]
            "topic_list":  topics,
            "body":        body,
            "expand_var":  expand_var,
            "is_expanded": is_expanded,
        }
        self._chapter_state[chapter_name] = state

        # Nếu chương không có lessons (custom) → vẫn add chapter_name là topic
        if not lessons:
            # custom topics — mỗi topic là 1 lesson độc lập
            for ti, t in enumerate(topics):
                lvar = tk.BooleanVar(value=True)
                lvar.trace_add("write",
                    lambda *_, s=state: self._on_lesson_changed(s))
                lcb = tk.Checkbutton(
                    body, text=f"  {t}", variable=lvar,
                    font=("Segoe UI", 10),
                    bg="white", fg="#1E293B",
                    activebackground="#F0F9FF",
                    image=self._cb_off, selectimage=self._cb_on,
                    indicatoron=False, compound="left",
                    relief="flat", overrelief="flat", bd=0,
                    anchor="w", wraplength=600, justify="left",
                    padx=6, pady=4,
                )
                lcb.pack(fill="x", anchor="w", padx=(36, 8), pady=2)
                lcb.bind("<MouseWheel>", scroll_handler)
                state["lesson_vars"].append((t, lvar))
                self._topic_vars.append((t, lvar))
        else:
            # Hiển thị lessons với indent + checkbox riêng
            for li, (lesson, topic) in enumerate(zip(lessons, topics)):
                lvar = tk.BooleanVar(value=True)
                lvar.trace_add("write",
                    lambda *_, s=state: self._on_lesson_changed(s))
                lcb = tk.Checkbutton(
                    body, text=f"  {lesson}", variable=lvar,
                    font=("Segoe UI", 10),
                    bg="white", fg="#334155",
                    activebackground="#F0F9FF",
                    image=self._cb_off, selectimage=self._cb_on,
                    indicatoron=False, compound="left",
                    relief="flat", overrelief="flat", bd=0,
                    anchor="w", wraplength=600, justify="left",
                    padx=6, pady=3,
                )
                lcb.pack(fill="x", anchor="w", padx=(36, 8), pady=1)
                lcb.bind("<MouseWheel>", scroll_handler)
                state["lesson_vars"].append((topic, lvar))
                self._topic_vars.append((topic, lvar))

        # ── Hooks ───────────────────────────────────────────────────────
        # Chapter checkbox → toggle all lessons
        chap_cb.configure(command=lambda s=state: self._on_chapter_toggle(s))

        # Expand/collapse: click label hoặc button
        def _toggle_expand(_evt=None, s=state):
            s["is_expanded"] = not s["is_expanded"]
            s["expand_var"].set("v" if s["is_expanded"] else ">")
            if s["is_expanded"]:
                s["body"].pack(fill="x")
            else:
                s["body"].pack_forget()
            # Re-trigger scroll region recalc
            self._topic_inner.update_idletasks()
            self._topic_canvas.configure(scrollregion=self._topic_canvas.bbox("all"))

        expand_btn.bind("<Button-1>", _toggle_expand)
        chap_label.bind("<Button-1>", _toggle_expand)

    def _on_chapter_toggle(self, state: dict) -> None:
        """Chapter checkbox bị toggle → set tất cả lessons theo state mới."""
        val = bool(state["var"].get())
        # Suppress callback recursion bằng cờ
        state["_suppress"] = True
        try:
            for _, lvar in state["lesson_vars"]:
                lvar.set(val)
        finally:
            state["_suppress"] = False

    def _on_lesson_changed(self, state: dict) -> None:
        """Lesson được tick/uncheck → cập nhật chapter indeterminate state.

        Logic: nếu tất cả lessons = checked → chapter = checked.
        Nếu tất cả = unchecked → chapter = unchecked.
        Nếu mixed → chapter giữ trạng thái hiện tại (visual: bán-check sẽ
        khó hiển thị với image-based checkbox, nên ta dùng heuristic:
        chapter = True nếu BẤT KỲ lesson nào được tick).
        """
        if state.get("_suppress"):
            return
        any_checked = any(lvar.get() for _, lvar in state["lesson_vars"])
        # Update chapter var WITHOUT triggering _on_chapter_toggle
        state["_suppress"] = True
        try:
            state["var"].set(any_checked)
        finally:
            state["_suppress"] = False

    def _add_custom_topic(self):
        """Thêm chủ đề tùy chỉnh.

        Sau khi save vào storage → gọi `_refresh_topics()` để rebuild
        tree. Topic mới sẽ xuất hiện trong block "Chủ đề tùy chỉnh
        của bạn" ở cuối danh sách.
        """
        topic = self._custom_topic_var.get().strip()
        if not topic or "Nhập chủ đề mới" in topic:
            return

        existing = [t for t, _ in self._topic_vars]
        if topic in existing:
            return

        # Persist trước rồi refresh — tránh duplicate logic xây checkbox
        grade = self._p_grade_var.get()
        self._save_custom_topic(grade, topic)
        self._custom_topic_var.set("")
        self._refresh_topics()

    def _load_custom_topics(self) -> dict:
        """Load user-saved custom topics from storage/custom_topics.json."""
        import json
        try:
            from pathlib import Path
            p = Path(__file__).parent.parent / "storage" / "custom_topics.json"
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_custom_topic(self, grade: str, topic: str):
        """Persist a user-added topic for a grade."""
        import json
        from pathlib import Path
        p = Path(__file__).parent.parent / "storage" / "custom_topics.json"
        p.parent.mkdir(exist_ok=True)
        data = self._load_custom_topics()
        if grade not in data:
            data[grade] = []
        if topic not in data[grade]:
            data[grade].append(topic)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_requirements(self) -> dict:
        """Load stored topic → requirement mappings."""
        import json
        try:
            from pathlib import Path
            p = Path(__file__).parent.parent / "storage" / "topic_requirements.json"
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _save_requirement(self, topic: str, requirement: str):
        """Persist topic → requirement mapping for auto-suggest."""
        import json
        from pathlib import Path
        p = Path(__file__).parent.parent / "storage" / "topic_requirements.json"
        p.parent.mkdir(exist_ok=True)
        data = self._load_requirements()
        data[topic] = requirement
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _select_all(self):
        """Tick tất cả chương + bài học."""
        for state in getattr(self, "_chapter_state", {}).values():
            state["_suppress"] = True
            try:
                state["var"].set(True)
                for _, lvar in state["lesson_vars"]:
                    lvar.set(True)
            finally:
                state["_suppress"] = False

    def _deselect_all(self):
        """Untick tất cả chương + bài học."""
        for state in getattr(self, "_chapter_state", {}).values():
            state["_suppress"] = True
            try:
                state["var"].set(False)
                for _, lvar in state["lesson_vars"]:
                    lvar.set(False)
            finally:
                state["_suppress"] = False

    # ══════════════════════════════════════════════════════════════════════════
    #  OK — Build MatrixData
    # ══════════════════════════════════════════════════════════════════════════

    def _on_ok(self):
        current_tab = self._notebook.index(self._notebook.select())
        if current_tab == 0:
            self._on_ok_manual()
        else:
            self._on_ok_preset()

    def _on_ok_manual(self):
        subject, grade, sem, year, time_str = self._m_subj_var.get().strip(), self._m_grade_var.get().strip(), self._m_sem_var.get().strip(), self._m_year_var.get().strip(), self._m_time_var.get().strip()

        if not subject: messagebox.showwarning("Thiếu thông tin", "Hãy nhập tên môn học.", parent=self); return
        if not self._row_widgets: messagebox.showwarning("Chưa có dữ liệu", "Hãy thêm ít nhất 1 hàng dữ liệu.", parent=self); return

        # Lấy yêu cầu AI tùy chọn
        ai_req = self._m_ai_req_var.get().strip()
        if ai_req and "VD:" in ai_req:
            ai_req = ""  # placeholder text

        rows: list[MatrixRow] = []; stt = 0; errors = []

        for i, rw in enumerate(self._row_widgets):
            topic = rw["topic"].get().strip()
            if not topic: errors.append(f"Hàng {i+1}: Thiếu chủ đề"); continue

            raw_qt = rw["qtype_cb"].get()
            qtype = raw_qt.split(" — ")[0].strip() if " — " in raw_qt else raw_qt.strip()
            if qtype not in QTYPES: errors.append(f"Hàng {i+1}: Loại câu không hợp lệ '{qtype}'"); continue

            raw_lv = rw["level_cb"].get()
            level = raw_lv.split(" — ")[0].strip() if " — " in raw_lv else raw_lv.strip()
            if level not in LEVELS: errors.append(f"Hàng {i+1}: Mức độ không hợp lệ '{level}'"); continue

            try:
                count = int(rw["count"].get().strip())
                if count <= 0: raise ValueError
            except ValueError: errors.append(f"Hàng {i+1}: Số câu phải là số nguyên dương"); continue

            try:
                points = float(rw["points"].get().strip())
                if points < 0: raise ValueError
            except ValueError: errors.append(f"Hàng {i+1}: Điểm không hợp lệ"); continue

            requirement = rw["requirement"].get().strip() or f"{topic} [{level}]"
            # Gắn thêm yêu cầu AI tùy chọn
            if ai_req:
                requirement = f"{requirement} | Yêu cầu thêm: {ai_req}"

            if qtype == "DS":
                # Đọc dữ liệu từng ý a,b,c,d từ sub-item widgets (nếu có)
                ds_sub = rw.get("ds_widgets")
                for k in range(count):
                    stt += 1; items: list[DSItem] = []
                    if ds_sub and len(ds_sub) == 4:
                        for dw in ds_sub:
                            raw_lv2 = dw["level_cb"].get()
                            sub_lv = raw_lv2.split(" — ")[0].strip() if " — " in raw_lv2 else raw_lv2.strip()
                            sub_req = dw["requirement"].get().strip()
                            if not sub_req or "Yêu cầu ý" in sub_req:
                                sub_req = f"{topic} [{sub_lv}]"
                            items.append(DSItem(label=dw["label"], level=sub_lv, requirement=sub_req, code=f"DS{stt}{dw['label']}"))
                    else:
                        for idx_item, lv in enumerate(["NB", "TH", "VD", "VD"]):
                            label = chr(ord('a') + idx_item)
                            items.append(DSItem(label=label, level=lv, requirement=f"{topic} [{lv}]", code=f"DS{stt}{label}"))
                    all_reqs = " | ".join(f"ý {s.label} [{s.level}]: {s.requirement}" for s in items)
                    rows.append(MatrixRow(stt=str(stt), topic=topic, level=level, qtype="DS", codes=[s.code for s in items], requirement=all_reqs, points=points, enabled=True, ds_items=items))
            else:
                for k in range(count):
                    stt += 1
                    rows.append(MatrixRow(stt=str(stt), topic=topic, level=level, qtype=qtype, codes=[f"{qtype}{stt}"], requirement=requirement, points=points, enabled=True))

        if errors: messagebox.showwarning("Lỗi dữ liệu", "Vui lòng sửa các lỗi sau:\n\n" + "\n".join(errors), parent=self); return
        if not rows: messagebox.showwarning("Chưa có dữ liệu", "Không có hàng hợp lệ nào.", parent=self); return

        self._on_accept(MatrixData(title=f"ĐỀ KIỂM TRA {sem.upper()} — {subject.upper()} {grade}", time_str=time_str, rows=rows), subject, grade)
        self.destroy()

    def _on_ok_preset(self):
        dur_label = self._dur_var.get()
        grade, subject = self._p_grade_var.get(), self._p_subj_var.get().strip()

        if not subject: messagebox.showwarning("Thiếu môn học", "Hãy nhập tên môn học.", parent=self); return

        # Lấy yêu cầu AI tùy chọn
        ai_req = self._p_ai_req_var.get().strip()
        if ai_req and "VD:" in ai_req:
            ai_req = ""  # placeholder text

        selected = [t for t, var in self._topic_vars if var.get()] or None

        # Lấy số lượng câu tùy chỉnh từ spinbox
        n_tn = max(0, self._qty_tn.get())
        n_ds = max(0, self._qty_ds.get())
        n_tln = max(0, self._qty_tln.get())
        n_tl = max(0, self._qty_tl.get())

        if n_tn + n_ds + n_tln + n_tl == 0:
            messagebox.showwarning("Chưa có câu", "Tổng số câu phải > 0.", parent=self)
            return

        try:
            matrix = build_quick_matrix_custom(
                n_tn=n_tn, n_ds=n_ds, n_tln=n_tln, n_tl=n_tl,
                time_str=dur_label, grade=grade, topics=selected, subject=subject,
            )
            matrix.title = f"ĐỀ KIỂM TRA {self._p_sem_var.get().upper()} — {subject.upper()} {grade}"
            # Gắn yêu cầu AI vào từng row
            if ai_req:
                for row in matrix.rows:
                    row.requirement = f"{row.requirement} | Yêu cầu thêm: {ai_req}"
        except Exception as e:
            messagebox.showerror("Lỗi tạo ma trận", str(e), parent=self)
            return

        self._on_accept(matrix, subject, grade)
        self.destroy()
