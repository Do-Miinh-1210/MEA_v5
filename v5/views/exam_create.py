"""
v5/views/exam_create.py — Tạo đề từ ma trận đặc tả.

Sections:
    1. Ma trận đặc tả — bảng nhập rows (chủ đề × NB/TH/VD × qtype)
    2. Settings — đề tài, thời lượng
    3. Generate — gọi AI sinh đề, progress
    4. Preview — list câu hỏi đã tạo
    5. Export — xuất Word .docx

Reuse:
    core.models — MatrixRow, ExamData, Question
    core.generator — generate_all
    services.ai_service — create_ai_service (5 providers)
    export.word_exporter — xuất Word
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from core.models import MatrixRow, ExamData, Question
from services.tikz_vector_workflow import (
    TIKZ_CONVERSION_OPTIONS,
    TIKZ_TO_EMF_ACTION_LABEL,
    TIKZ_TO_EMF_DESCRIPTION,
    TIKZ_TO_PNG_ACTION_LABEL,
    TIKZ_OUTPUT_MODE_EMF,
    TIKZ_OUTPUT_MODE_PNG,
    get_tikz_conversion_option,
)
from v5.question_cards import QuestionCardsPanel, clone_question_for_edit
from v5.ui_perf import UiThrottle

# v5 setup view để lấy provider/key
TOPICS = [
    "Hàm số và đồ thị", "Đạo hàm và ứng dụng", "Nguyên hàm và tích phân",
    "Hình học không gian", "Hình học tọa độ trong không gian",
    "Lượng giác", "Hàm số mũ và logarithm", "Tổ hợp và xác suất",
    "Số phức", "Dãy số - Cấp số cộng - Cấp số nhân",
]


class ExamCreateView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        *,
        on_navigate: Callable[[str], None] | None = None,
        initial_exam: ExamData | None = None,
        on_exam_changed: Callable[[ExamData | None], None] | None = None,
        can_use_feature: Callable[..., bool] | None = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self._on_navigate = on_navigate
        self._on_exam_changed = on_exam_changed
        self._can_use_feature = can_use_feature
        self._matrix_rows: list[dict] = []     # [{topic, nb, th, vd, qtype, points}]
        # Ma trận đặc tả CHI TIẾT từng câu (giữ yêu cầu cần đạt từ file tải lên)
        # [{stt, topic, level, qtype, requirement, points, codes}]
        self._matrix_detail: list[dict] = []
        self._generated_questions: list = []
        self._exam: ExamData | None = None
        self._last_export_path: Path | None = None
        self._include_solution_var = ctk.BooleanVar(value=self._include_solutions_on_export())
        self._auto_table_var = ctk.BooleanVar(value=self._word_auto_convert_tables())
        self._source_mode_var = ctk.StringVar(value="AI mới")
        self._source_ratio_var = ctk.IntVar(value=50)
        self._source_mode = "ai_only"
        self._busy = False
        self._build()
        # Seed 2 row mặc định
        self._add_row({"topic": "Đạo hàm và ứng dụng", "nb": 2, "th": 3, "vd": 1, "qtype": "TN", "points": 0.25})
        self._add_row({"topic": "Tích phân",            "nb": 1, "th": 2, "vd": 2, "qtype": "TN", "points": 0.25})
        self._render_matrix()
        if initial_exam is not None:
            self.load_exam(initial_exam)

    def load_exam(self, exam: ExamData) -> None:
        """Nạp đề từ workspace/history để tiếp tục sửa, xuất hoặc push."""
        self._exam = exam
        self._apply_default_exam_metadata(self._exam)
        self._generated_questions = list(exam.questions or [])
        self._title_var.set(exam.exam_title or "Đề khôi phục")
        if exam.grade:
            self._grade_var.set(str(exam.grade))
        import re as _re
        duration = _re.search(r"\d+", str(exam.time or ""))
        if duration:
            self._duration_var.set(duration.group(0))
        self._render_preview()
        self._sync_result_action_state()

    def _publish_exam_change(self) -> None:
        if callable(self._on_exam_changed):
            self._on_exam_changed(self._exam)

    def _sync_result_action_state(self) -> None:
        has_questions = bool(self._generated_questions)
        q_state = "normal" if has_questions else "disabled"
        for button in (
            self._export_btn,
            self._multi_btn,
            self._variant_btn,
            self._bank_btn,
            self._tikz_emf_btn,
            self._score_check_btn,
        ):
            button.configure(state=q_state)
        if hasattr(self, "_tikz_mode_menu"):
            self._tikz_mode_menu.configure(state=q_state)
        if hasattr(self, "_retry_failed_btn"):
            failed_count = len(self._failed_question_indexes()) if has_questions else 0
            self._retry_failed_btn.configure(
                state=("normal" if failed_count else "disabled"),
                text=(f"🔁  Tạo lại lỗi ({failed_count})" if failed_count else "🔁  Tạo lại lỗi"),
            )
        if hasattr(self, "_qc_current_btn"):
            self._qc_current_btn.configure(state=q_state)
        if hasattr(self, "_error_report_btn"):
            failed_count = len(self._failed_question_indexes()) if has_questions else 0
            self._error_report_btn.configure(
                state=q_state,
                text=(f"📋  Báo cáo lỗi ({failed_count})" if failed_count else "📋  Báo cáo lỗi"),
            )
        if hasattr(self, "_meta_btn"):
            self._meta_btn.configure(state=("normal" if self._exam else "disabled"))
        for name in ("_jump_question_btn", "_quick_edit_btn", "_duplicate_question_btn"):
            if hasattr(self, name):
                getattr(self, name).configure(state=q_state)

    def _default_school_info(self) -> tuple[str, str]:
        try:
            from config import get_school_info
            return get_school_info()
        except Exception:
            return "", ""

    def _apply_default_exam_metadata(self, exam: ExamData | None) -> None:
        if exam is None:
            return
        school, teacher = self._default_school_info()
        if school and not getattr(exam, "school", ""):
            exam.school = school
        if teacher and not getattr(exam, "teacher", ""):
            exam.teacher = teacher

    def _word_math_mode(self) -> str:
        try:
            from config import get_word_math_mode
            return get_word_math_mode()
        except Exception:
            return "text"

    def _word_auto_convert_tables(self) -> bool:
        if hasattr(self, "_auto_table_var"):
            try:
                return bool(self._auto_table_var.get())
            except Exception:
                pass
        try:
            from config import is_word_auto_convert_tables_enabled
            return is_word_auto_convert_tables_enabled()
        except Exception:
            return True

    def _include_solutions_on_export(self) -> bool:
        if hasattr(self, "_include_solution_var"):
            try:
                return bool(self._include_solution_var.get())
            except Exception:
                pass
        try:
            from config import is_export_solution_enabled
            return is_export_solution_enabled()
        except Exception:
            return True

    def _set_include_solutions_from_quick_toggle(self) -> None:
        """V4 parity: checkbox nhanh kèm đáp án/lời giải ngay trên màn Kết quả."""
        enabled = bool(self._include_solution_var.get())
        try:
            from config import set_export_solution_enabled
            set_export_solution_enabled(enabled)
        except Exception as exc:
            messagebox.showerror("Lỗi lưu cài đặt xuất", str(exc)[:300], parent=self)
            return
        label = "bật" if enabled else "tắt"
        self._result_status.configure(
            text=f"☑ Đã {label} kèm đáp án/lời giải khi xuất Word.",
            text_color=("#10B981" if enabled else "gray"),
        )
        try:
            from v5.toast import show_toast
            show_toast(
                self.winfo_toplevel(),
                f"Đã {label} kèm đáp án/lời giải khi xuất Word",
                kind=("success" if enabled else "info"),
            )
        except Exception:
            pass

    def _set_auto_convert_tables_from_quick_toggle(self) -> None:
        """Persist the quick toggle for converting pipe-delimited lines to Word tables."""
        enabled = bool(self._auto_table_var.get())
        try:
            from config import set_word_auto_convert_tables_enabled
            set_word_auto_convert_tables_enabled(enabled)
        except Exception as exc:
            messagebox.showerror("Lỗi lưu cài đặt xuất", str(exc)[:300], parent=self)
            return
        label = "bật" if enabled else "tắt"
        self._result_status.configure(
            text=f"☑ Đã {label} tự chuyển dòng có dấu | thành bảng Word.",
            text_color=("#10B981" if enabled else "gray"),
        )
        try:
            from v5.toast import show_toast
            show_toast(
                self.winfo_toplevel(),
                f"Đã {label} chuyển dấu | thành bảng Word",
                kind=("success" if enabled else "info"),
            )
        except Exception:
            pass

    def _open_after_export_enabled(self) -> bool:
        try:
            from config import is_open_after_export_enabled
            return is_open_after_export_enabled()
        except Exception:
            return True

    def _build(self):
        # Toàn bộ nội dung trong vùng cuộn — view dài hơn cửa sổ vẫn xem hết
        # (ma trận nhiều dòng + section ④ Kết quả ở dưới).
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)

        head = ctk.CTkFrame(self._scroll, fg_color="transparent")
        head.pack(fill="x", pady=(4, 6))
        ctk.CTkLabel(head, text="✏️  Tạo đề kiểm tra",
                      font=("Segoe UI", 24, "bold")
                      ).pack(side="left")
        # Smart Prompt shortcut — tạo ma trận từ mô tả tiếng Việt
        self._smart_btn = ctk.CTkButton(
            head, text="💬 Smart Prompt", width=150, height=32,
            fg_color=("#7C3AED", "#5B21B6"),
            hover_color=("#6D28D9", "#4C1D95"),
            command=self._open_smart_prompt)
        self._smart_btn.pack(side="right", padx=4)
        # Quick Gen — tạo ma trận theo mẫu thời lượng / số câu (KHÔNG gọi AI)
        self._quick_btn = ctk.CTkButton(
            head, text="🚀 Tạo đề nhanh", width=150, height=32,
            fg_color=("#10B981", "#047857"),
            hover_color=("#059669", "#065F46"),
            command=self.open_quick_gen)
        self._quick_btn.pack(side="right", padx=4)
        # AI Gen Matrix — AI tự tạo ma trận từ form fields
        ctk.CTkButton(head, text="🤖 AI tạo ma trận", width=160, height=32,
                       fg_color=("#0EA5E9", "#075985"),
                       hover_color=("#0284C7", "#0C4A6E"),
                       command=self.open_ai_gen_matrix
                       ).pack(side="right", padx=4)

        # ── Banner quy trình (hướng dẫn rõ từng bước) ─────────────────
        guide = ctk.CTkFrame(self._scroll, fg_color=("#EFF6FF", "#172033"),
                               corner_radius=8)
        guide.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(guide,
                      text="Quy trình:  ①  Lập ma trận (chủ đề × số câu mỗi mức)  "
                           "→  ②  AI sinh đề  →  ③  Kiểm tra & sửa  →  "
                           "④  Xuất Word / lưu NHCH",
                      font=("Segoe UI", 11, "bold"),
                      text_color=("#1E40AF", "#93C5FD"),
                      anchor="w", justify="left", wraplength=820
                      ).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(guide,
                      text="💡 Mới dùng? Bấm 💬 Smart Prompt rồi gõ "
                           "\"Đề 90 phút lớp 12 về tích phân, 18 TN 4 ĐS\" "
                           "— AI tự lập ma trận giúp bạn.",
                      font=("Segoe UI", 10),
                      text_color=("#6B7280", "#9CA3AF"),
                      anchor="w", justify="left", wraplength=820
                      ).pack(anchor="w", padx=12, pady=(0, 8))

        # ── Settings ──────────────────────────────────────────────────
        s_card = self._card("①  Cài đặt đề")
        row = ctk.CTkFrame(s_card, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text="Tiêu đề:", width=80
                      ).pack(side="left", padx=(0, 4))
        self._title_var = ctk.StringVar(value="Đề kiểm tra Toán 12")
        ctk.CTkEntry(row, textvariable=self._title_var, width=220
                       ).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(row, text="Lớp:", width=34
                      ).pack(side="left", padx=(0, 2))
        self._grade_var = ctk.StringVar(value="12")
        ctk.CTkOptionMenu(row, values=["10", "11", "12", "9", "8", "7", "6"],
                            variable=self._grade_var, width=64
                            ).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(row, text="Thời lượng:", width=74
                      ).pack(side="left", padx=(0, 2))
        self._duration_var = ctk.StringVar(value="90")
        ctk.CTkEntry(row, textvariable=self._duration_var, width=54
                       ).pack(side="left")
        ctk.CTkLabel(row, text="phút").pack(side="left", padx=4)

        # ── Ma trận đặc tả ────────────────────────────────────────────
        m_card = self._card("②  Ma trận đặc tả")
        # Toggle chế độ xem + chú thích
        mode_row = ctk.CTkFrame(m_card, fg_color="transparent")
        mode_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(mode_row, text="Chế độ xem:",
                      font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
        self._matrix_mode = ctk.StringVar(value="grouped")
        ctk.CTkSegmentedButton(
            mode_row, values=["Gộp chủ đề", "Chi tiết từng câu"],
            command=self._on_matrix_mode_change, width=280
            ).pack(side="left")
        self._mode_hint = ctk.CTkLabel(
            mode_row, text="  (double-click 1 dòng để sửa)",
            font=("Segoe UI", 9), text_color="gray")
        self._mode_hint.pack(side="left", padx=8)

        ctk.CTkLabel(m_card,
                      text="NB = Nhận biết · TH = Thông hiểu · VD = Vận dụng. "
                           "'Chi tiết từng câu' hiện yêu cầu cần đạt mỗi câu "
                           "(từ file ma trận đặc tả).",
                      font=("Segoe UI", 10), text_color="gray",
                      anchor="w", justify="left", wraplength=820
                      ).pack(anchor="w", pady=(0, 6))

        # Bảng treeview — superset cột, đổi displaycolumns theo mode.
        # Dùng grid để có CẢ scrollbar dọc + NGANG (cột Yêu cầu rộng).
        tbl_wrap = ctk.CTkFrame(m_card, fg_color=("white", "#1E293B"))
        tbl_wrap.pack(fill="x", pady=(0, 8))
        tbl_wrap.grid_rowconfigure(0, weight=1)
        tbl_wrap.grid_columnconfigure(0, weight=1)

        allcols = ("stt", "topic", "level", "nb", "th", "vd",
                    "qtype", "requirement", "points")
        self._tree = ttk.Treeview(tbl_wrap, columns=allcols, show="headings",
                                     height=10)
        # stretch=False khắp → cột giữ width, tràn thì cuộn ngang được
        colcfg = {
            "stt":         ("#", 40, "center"),
            "topic":       ("Chủ đề", 230, "w"),
            "level":       ("Mức", 55, "center"),
            "nb":          ("NB", 45, "center"),
            "th":          ("TH", 45, "center"),
            "vd":          ("VD", 45, "center"),
            "qtype":       ("Loại", 60, "center"),
            "requirement": ("Yêu cầu cần đạt", 420, "w"),
            "points":      ("Điểm", 60, "center"),
        }
        # Alpha 22: cột "Chủ đề" và "Yêu cầu cần đạt" stretch=True để
        # lấp đầy width khi widget rộng hơn tổng cột. Trước tất cả
        # stretch=False → bảng có nhiều khoảng trống bên phải.
        for c in allcols:
            text, w, anc = colcfg[c]
            self._tree.heading(c, text=text)
            stretch = c in ("topic", "requirement")
            self._tree.column(c, width=w, anchor=anc, stretch=stretch)
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._tree)
        except Exception: pass
        self._tree.grid(row=0, column=0, sticky="nsew")
        self._tree.bind("<Double-1>", self._on_matrix_dblclick)

        vsb = ttk.Scrollbar(tbl_wrap, orient="vertical",
                              command=self._tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(tbl_wrap, orient="horizontal",
                              command=self._tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        # Set displaycolumns ban đầu (grouped)
        self._tree.configure(
            displaycolumns=("topic", "nb", "th", "vd", "qtype", "points"))

        # Nguồn ma trận + xuất đặc tả (các luồng V4 đã dùng trước khi sinh đề)
        matrix_io_row = ctk.CTkFrame(m_card, fg_color="transparent")
        matrix_io_row.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(matrix_io_row, text="📂  Tải file ma trận", width=160,
                       fg_color=("#0891B2", "#0E7490"),
                       hover_color=("#0E7490", "#155E75"),
                       command=self._upload_matrix_file
                       ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(matrix_io_row, text="📋  Phân tích đề", width=145,
                       fg_color=("#F59E0B", "#92400E"),
                       hover_color=("#D97706", "#78350F"),
                       command=self._open_analyze_exam
                       ).pack(side="left", padx=2)
        ctk.CTkButton(matrix_io_row, text="📚  Thư viện mẫu", width=150,
                       fg_color=("#7C3AED", "#5B21B6"),
                       hover_color=("#6D28D9", "#4C1D95"),
                       command=self._open_template_library
                       ).pack(side="left", padx=2)
        ctk.CTkButton(matrix_io_row, text="📥  Xuất ma trận", width=145,
                       fg_color=("#0EA5E9", "#075985"),
                       hover_color=("#0284C7", "#0C4A6E"),
                       command=self._export_matrix
                       ).pack(side="left", padx=2)

        btn_row = ctk.CTkFrame(m_card, fg_color="transparent")
        btn_row.pack(fill="x")
        ctk.CTkButton(btn_row, text="➕  Thêm dòng", width=120,
                       command=self._add_row_dialog
                       ).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="🗑  Xoá dòng", width=110,
                       fg_color="#EF4444", hover_color="#DC2626",
                       command=self._delete_selected_row
                       ).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="🧹  Xoá hết", width=100,
                       fg_color="#6B7280", hover_color="#4B5563",
                       command=self._clear_all_rows
                       ).pack(side="left", padx=2)
        self._matrix_summary = ctk.CTkLabel(btn_row, text="",
                                               text_color="gray",
                                               font=("Segoe UI", 10))
        self._matrix_summary.pack(side="left", padx=14)

        # ── Generate ──────────────────────────────────────────────────
        g_card = self._card("③  Nguồn & sinh đề")
        source_row = ctk.CTkFrame(g_card, fg_color="transparent")
        source_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            source_row,
            text="Nguồn tạo đề:",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=(0, 8))
        self._source_menu = ctk.CTkOptionMenu(
            source_row,
            values=["AI mới", "100% NHCH", "Kết hợp"],
            variable=self._source_mode_var,
            width=130,
            command=self._on_source_mode_changed,
        )
        self._source_menu.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(
            source_row,
            text="Tỉ lệ NHCH:",
            font=("Segoe UI", 10),
        ).pack(side="left", padx=(0, 6))
        self._source_ratio_slider = ctk.CTkSlider(
            source_row,
            from_=10,
            to=90,
            number_of_steps=8,
            width=160,
            command=self._on_source_ratio_changed,
        )
        self._source_ratio_slider.set(self._source_ratio_var.get())
        self._source_ratio_slider.pack(side="left", padx=(0, 6))
        self._source_ratio_lbl = ctk.CTkLabel(
            source_row,
            text="50%",
            width=42,
            font=("Segoe UI", 10, "bold"),
        )
        self._source_ratio_lbl.pack(side="left", padx=(0, 10))
        self._source_hint = ctk.CTkLabel(
            source_row,
            text="AI tạo toàn bộ câu mới theo ma trận.",
            text_color="gray",
            font=("Segoe UI", 10),
            anchor="w",
        )
        self._source_hint.pack(side="left", fill="x", expand=True)
        self._refresh_source_controls()
        gen_row = ctk.CTkFrame(g_card, fg_color="transparent")
        gen_row.pack(fill="x")
        self._gen_btn = ctk.CTkButton(
            gen_row, text="▶  Tạo đề",
            font=("Segoe UI", 13, "bold"), height=40,
            fg_color="#10B981", hover_color="#059669",
            command=self._on_generate, width=200)
        self._gen_btn.pack(side="left", padx=(0, 6))
        # Nút Dừng — set cancel_event để generate_all thoát sớm
        self._gen_cancel_btn = ctk.CTkButton(
            gen_row, text="⛔ Dừng", height=40, width=90, state="disabled",
            fg_color=("#DC2626", "#7F1D1D"), hover_color=("#B91C1C", "#5F1313"),
            command=self._cancel_generate)
        self._gen_cancel_btn.pack(side="left", padx=(0, 12))

        self._prog_bar = ctk.CTkProgressBar(gen_row, width=300,
                                               progress_color="#10B981")
        self._prog_bar.set(0)
        self._prog_bar.pack(side="left", padx=(0, 12), pady=10)

        self._prog_lbl = ctk.CTkLabel(gen_row, text="",
                                         font=("Segoe UI", 11),
                                         text_color="gray")
        self._prog_lbl.pack(side="left")

        # ── Preview + Export ──────────────────────────────────────────
        p_card = self._card("④  Kết quả  —  double-click 1 câu để sửa")
        self._preview_lbl = ctk.CTkLabel(
            p_card, text="(Chưa có câu nào — bấm 'Tạo đề' ở trên)",
            text_color="gray", font=("Segoe UI", 11))
        self._preview_lbl.pack(anchor="w", pady=(0, 6))

        quick_edit_row = ctk.CTkFrame(
            p_card,
            fg_color=("#F8FAFC", "#111827"),
            corner_radius=8,
        )
        quick_edit_row.pack(fill="x", pady=(0, 8))
        quick_actions_row = ctk.CTkFrame(quick_edit_row, fg_color="transparent")
        quick_actions_row.pack(fill="x", padx=8, pady=(6, 2))
        ctk.CTkLabel(
            quick_actions_row,
            text="Sửa nhanh câu:",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(2, 5))
        self._question_jump_var = ctk.StringVar(value="1")
        self._question_jump_entry = ctk.CTkEntry(
            quick_actions_row,
            textvariable=self._question_jump_var,
            width=58,
            placeholder_text="#",
        )
        self._question_jump_entry.pack(side="left", padx=(0, 6))
        self._question_jump_entry.bind("<Return>", lambda _e: self._jump_to_preview_question())
        self._jump_question_btn = ctk.CTkButton(
            quick_actions_row,
            text="Đi tới",
            width=70,
            height=30,
            state="disabled",
            command=self._jump_to_preview_question,
        )
        self._jump_question_btn.pack(side="left", padx=(0, 6))
        self._quick_edit_btn = ctk.CTkButton(
            quick_actions_row,
            text="✏️ Sửa câu đang chọn",
            width=150,
            height=30,
            state="disabled",
            fg_color=("#2563EB", "#1D4ED8"),
            hover_color=("#1D4ED8", "#1E40AF"),
            command=self._edit_selected_preview_question,
        )
        self._quick_edit_btn.pack(side="left", padx=(0, 6))
        self._duplicate_question_btn = ctk.CTkButton(
            quick_actions_row,
            text="📄 Nhân bản để sửa",
            width=145,
            height=30,
            state="disabled",
            fg_color=("#7C3AED", "#5B21B6"),
            hover_color=("#6D28D9", "#4C1D95"),
            command=self._duplicate_preview_question,
        )
        self._duplicate_question_btn.pack(side="left", padx=(0, 6))
        self._insert_blank_question_btn = ctk.CTkButton(
            quick_actions_row,
            text="➕ Câu trống",
            width=115,
            height=30,
            fg_color=("#10B981", "#047857"),
            hover_color=("#059669", "#065F46"),
            command=self._insert_blank_preview_question,
        )
        self._insert_blank_question_btn.pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            quick_edit_row,
            text="Chọn dòng trong bảng hoặc nhập số câu để sửa/chèn nhanh.",
            font=("Segoe UI", 9),
            text_color="gray",
        ).pack(anchor="w", padx=10, pady=(0, 6))

        pv_wrap = ctk.CTkFrame(p_card, fg_color=("white", "#1E293B"),
                                  height=220)
        pv_wrap.pack(fill="both", expand=False, pady=(0, 8))
        pv_wrap.pack_propagate(False)

        self._preview_tree = ttk.Treeview(
            pv_wrap, columns=("no", "qtype", "level", "topic", "preview"),
            show="headings", height=8)
        labels_pv = {"no": "#", "qtype": "Loại", "level": "Mức",
                     "topic": "Chủ đề", "preview": "Nội dung"}
        widths_pv = {"no": 40, "qtype": 60, "level": 50,
                     "topic": 160, "preview": 500}
        minwidths_pv = {"no": 36, "qtype": 58, "level": 50,
                        "topic": 130, "preview": 260}
        for c, l in labels_pv.items():
            self._preview_tree.heading(c, text=l)
            self._preview_tree.column(c, width=widths_pv[c],
                                          minwidth=minwidths_pv[c],
                                          anchor=("w" if c in ("topic", "preview")
                                                   else "center"),
                                          stretch=(c in ("topic", "preview")))
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._preview_tree)
        except Exception: pass
        # Alpha 21: thêm HSB + VSB qua grid
        pv_vsb = ttk.Scrollbar(pv_wrap, orient="vertical",
                                  command=self._preview_tree.yview)
        pv_hsb = ttk.Scrollbar(pv_wrap, orient="horizontal",
                                  command=self._preview_tree.xview)
        self._preview_tree.configure(yscrollcommand=pv_vsb.set,
                                         xscrollcommand=pv_hsb.set)
        pv_wrap.grid_rowconfigure(0, weight=1)
        pv_wrap.grid_rowconfigure(2, weight=0)
        pv_wrap.grid_columnconfigure(0, weight=1)
        self._preview_tree.grid(row=0, column=0, sticky="nsew")
        pv_vsb.grid(row=0, column=1, sticky="ns")
        pv_hsb.grid(row=1, column=0, sticky="ew")
        # Double-click 1 câu → mở dialog sửa câu (CTk), lưu xong re-render
        self._preview_tree.bind("<Double-1>", self._on_preview_edit)
        self._preview_tree.bind("<<TreeviewSelect>>", self._on_preview_select)
        # Hint
        ctk.CTkLabel(pv_wrap, text="💡 Double-click 1 câu để sửa trước khi xuất",
                      font=("Segoe UI", 9), text_color="gray", anchor="w"
                      ).grid(row=2, column=0, columnspan=2, sticky="ew",
                             padx=8, pady=(2, 6))

        detail_head = ctk.CTkFrame(p_card, fg_color="transparent")
        detail_head.pack(fill="x", pady=(8, 2))
        ctk.CTkLabel(
            detail_head,
            text="👁  Xem chi tiết từng câu",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            detail_head,
            text="Nội dung, đáp án, lời giải và ảnh PNG hiển thị trực tiếp như bản V4.",
            font=("Segoe UI", 9),
            text_color="gray",
            anchor="w",
        ).pack(side="left", padx=12)
        self._question_cards = QuestionCardsPanel(
            p_card,
            on_edit=self._open_preview_question,
            on_latex=self._preview_question_latex,
            on_regenerate=self._regenerate_preview_question,
            on_move=self._move_preview_question,
            on_delete=self._delete_preview_question,
        )
        self._question_cards.pack(fill="x", pady=(0, 10))

        export_row = ctk.CTkFrame(p_card, fg_color="transparent")
        export_row.pack(fill="x")
        self._load_exam_btn = ctk.CTkButton(
            export_row, text="📥  Nạp đề file", width=145,
            fg_color=("#0891B2", "#0E7490"),
            hover_color=("#0E7490", "#155E75"),
            command=self._load_exam_from_file)
        self._load_exam_btn.pack(side="left", padx=(0, 6))
        self._export_btn = ctk.CTkButton(
            export_row, text="📄  Xuất Word", width=140,
            fg_color="#3B82F6", hover_color="#2563EB",
            state="disabled", command=self._export_word)
        self._export_btn.pack(side="left", padx=(0, 6))
        self._export_settings_btn = ctk.CTkButton(
            export_row, text="⚙️  Cài đặt xuất", width=130,
            fg_color=("#475569", "#334155"),
            hover_color=("#334155", "#1E293B"),
            command=self._open_export_settings_dialog)
        self._export_settings_btn.pack(side="left", padx=(0, 6))
        self._include_solution_check = ctk.CTkCheckBox(
            export_row,
            text="Kèm ĐA/LG",
            variable=self._include_solution_var,
            command=self._set_include_solutions_from_quick_toggle,
            width=108,
        )
        self._include_solution_check.pack(side="left", padx=(0, 8))
        self._auto_table_check = ctk.CTkCheckBox(
            export_row,
            text="| -> bảng Word",
            variable=self._auto_table_var,
            command=self._set_auto_convert_tables_from_quick_toggle,
            width=124,
        )
        self._auto_table_check.pack(side="left", padx=(0, 8))

        # 🔀 Trộn mã & Đề tương tự
        mix_row = ctk.CTkFrame(p_card, fg_color="transparent")
        mix_row.pack(fill="x", pady=(6, 0))
        self._multi_btn = ctk.CTkButton(
            mix_row, text="🔀  Trộn mã (A-F)", width=160,
            fg_color="#F59E0B", hover_color="#D97706",
            state="disabled", command=self._export_multi_code)
        self._multi_btn.pack(side="left", padx=(0, 6))

        self._variant_btn = ctk.CTkButton(
            mix_row, text="🧬  Đề tương tự", width=145,
            fg_color="#7C3AED", hover_color="#6D28D9",
            state="disabled", command=self._open_variant_dialog)
        self._variant_btn.pack(side="left", padx=(0, 6))

        post_row = ctk.CTkFrame(p_card, fg_color="transparent")
        post_row.pack(fill="x", pady=(8, 0))
        self._bank_btn = ctk.CTkButton(
            post_row, text="🏛  Lưu vào NHCH", width=145,
            fg_color=("#7C3AED", "#5B21B6"),
            hover_color=("#6D28D9", "#4C1D95"),
            state="disabled", command=self._save_exam_to_nhch)
        self._bank_btn.pack(side="left", padx=(0, 6))
        self._meta_btn = ctk.CTkButton(
            post_row, text="✏️ Thông tin đề", width=135,
            fg_color=("#0EA5E9", "#075985"),
            hover_color=("#0284C7", "#0C4A6E"),
            state="disabled", command=self._open_exam_metadata_dialog)
        self._meta_btn.pack(side="left", padx=2)
        self._folder_btn = ctk.CTkButton(
            post_row, text="📂 Thư mục", width=105, state="disabled",
            command=self._open_export_folder)
        self._folder_btn.pack(side="left", padx=2)
        self._copy_btn = ctk.CTkButton(
            post_row, text="➕ Bản sao", width=105, state="disabled",
            command=self._save_export_copy)
        self._copy_btn.pack(side="left", padx=2)
        self._relocate_btn = ctk.CTkButton(
            post_row, text="📁 Đổi chỗ", width=105, state="disabled",
            command=self._relocate_export)
        self._relocate_btn.pack(side="left", padx=2)
        self._auto_off_btn = ctk.CTkButton(
            post_row, text="⏸ Tắt tự xuất", width=125,
            fg_color=("#6B7280", "#374151"),
            command=self._disable_auto_export)
        self._auto_off_btn.pack(side="left", padx=2)

        media_row = ctk.CTkFrame(p_card, fg_color="transparent")
        media_row.pack(fill="x", pady=(8, 0))
        media_row.grid_columnconfigure(6, weight=1)
        self._tikz_options_by_label = {
            option["label"]: option for option in TIKZ_CONVERSION_OPTIONS
        }
        self._tikz_mode_var = ctk.StringVar(value=TIKZ_TO_EMF_ACTION_LABEL)
        self._tikz_mode_menu = ctk.CTkOptionMenu(
            media_row,
            values=list(self._tikz_options_by_label),
            variable=self._tikz_mode_var,
            width=105,
            height=34,
            state="disabled",
            command=self._on_tikz_mode_changed,
        )
        self._tikz_mode_menu.grid(row=0, column=0, sticky="w", padx=(0, 4))
        self._tikz_emf_btn = ctk.CTkButton(
            media_row, text="📐  Chuyển", width=78, height=34,
            fg_color=("#F59E0B", "#92400E"),
            hover_color=("#D97706", "#78350F"),
            state="disabled", command=self._convert_exam_tikz_to_emf)
        self._tikz_emf_btn.grid(row=0, column=1, sticky="w", padx=(0, 4))
        self._retry_failed_btn = ctk.CTkButton(
            media_row, text="🔁  Tạo lại lỗi", width=98, height=34,
            fg_color=("#D97706", "#92400E"),
            hover_color=("#B45309", "#78350F"),
            state="disabled", command=self._retry_failed_preview_questions)
        self._retry_failed_btn.grid(row=0, column=2, sticky="w", padx=(0, 4))
        self._qc_current_btn = ctk.CTkButton(
            media_row, text="✅  QC đề hiện tại", width=115, height=34,
            fg_color=("#0369A1", "#075985"),
            hover_color=("#075985", "#0C4A6E"),
            state="disabled", command=self._open_qc_current_exam)
        self._qc_current_btn.grid(row=0, column=3, sticky="w", padx=(0, 4))
        self._score_check_btn = ctk.CTkButton(
            media_row, text="🧮  Kiểm tra điểm", width=105, height=34,
            fg_color=("#4F46E5", "#3730A3"),
            hover_color=("#4338CA", "#312E81"),
            state="disabled", command=self._check_result_score)
        self._score_check_btn.grid(row=0, column=4, sticky="w", padx=(0, 4))
        self._error_report_btn = ctk.CTkButton(
            media_row, text="📋  Báo cáo lỗi", width=100, height=34,
            fg_color=("#64748B", "#334155"),
            hover_color=("#475569", "#1E293B"),
            state="disabled", command=self._export_error_report)
        self._error_report_btn.grid(row=0, column=5, sticky="w", padx=(0, 4))
        self._tikz_emf_status = ctk.CTkLabel(
            media_row,
            text=TIKZ_TO_EMF_DESCRIPTION,
            text_color="gray", font=("Segoe UI", 10), anchor="w")
        self._tikz_emf_status.grid(row=1, column=0, columnspan=7, sticky="ew",
                                   pady=(4, 0))

        self._result_status = ctk.CTkLabel(
            p_card, text="Tự xuất Word: sẽ chạy sau khi sinh đề (có thể đổi trong Tuỳ chọn).",
            text_color="gray", font=("Segoe UI", 10), anchor="w")
        self._result_status.pack(fill="x", pady=(7, 0))

    # ── Card helper ───────────────────────────────────────────────────────
    def _card(self, title: str) -> ctk.CTkFrame:
        parent = getattr(self, "_scroll", self)
        outer = ctk.CTkFrame(parent, fg_color=("white", "#293548"),
                                corner_radius=10, border_width=1,
                                border_color=("#E5E7EB", "#334155"))
        outer.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(inner, text=title,
                      font=("Segoe UI", 13, "bold"),
                      anchor="w").pack(anchor="w", pady=(0, 8))
        return inner

    # ── Matrix CRUD ───────────────────────────────────────────────────────
    def _add_row(self, data: dict):
        self._matrix_rows.append(data)

    def _add_row_dialog(self, edit_idx: int | None = None):
        """Popup thêm/sửa 1 dòng ma trận gộp. edit_idx != None = sửa dòng đó."""
        editing = (edit_idx is not None and 0 <= edit_idx < len(self._matrix_rows))
        cur = self._matrix_rows[edit_idx] if editing else {}
        dlg = ctk.CTkToplevel(self)
        dlg.title("Sửa dòng ma trận" if editing else "Thêm dòng ma trận")
        dlg.geometry("440x340")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        ctk.CTkLabel(dlg, text="Chủ đề (theo chương của lớp đã chọn):"
                      ).pack(anchor="w", padx=20, pady=(20, 2))
        try:
            from core.quick_matrix import get_topics_for_grade
            _g = self._grade_var.get() if hasattr(self, "_grade_var") else "12"
            topics = get_topics_for_grade(_g) or TOPICS
        except Exception:
            topics = TOPICS
        topic_var = ctk.StringVar(
            value=cur.get("topic") or (topics[0] if topics else ""))
        ctk.CTkComboBox(dlg, values=topics, variable=topic_var, width=400
                          ).pack(padx=20, pady=2)

        row1 = ctk.CTkFrame(dlg, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(row1, text="NB:").pack(side="left", padx=(0, 4))
        nb_var = ctk.StringVar(value=str(cur.get("nb", 2)))
        ctk.CTkEntry(row1, textvariable=nb_var, width=60).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(row1, text="TH:").pack(side="left", padx=(0, 4))
        th_var = ctk.StringVar(value=str(cur.get("th", 2)))
        ctk.CTkEntry(row1, textvariable=th_var, width=60).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(row1, text="VD:").pack(side="left", padx=(0, 4))
        vd_var = ctk.StringVar(value=str(cur.get("vd", 1)))
        ctk.CTkEntry(row1, textvariable=vd_var, width=60).pack(side="left")

        row2 = ctk.CTkFrame(dlg, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(row2, text="Loại:").pack(side="left", padx=(0, 4))
        qtype_var = ctk.StringVar(value=cur.get("qtype", "TN"))
        ctk.CTkOptionMenu(row2, values=["TN", "DS", "TLN", "TL"],
                            variable=qtype_var, width=80
                            ).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(row2, text="Điểm/câu:").pack(side="left", padx=(0, 4))
        pts_var = ctk.StringVar(value=str(cur.get("points", 0.25)))
        ctk.CTkEntry(row2, textvariable=pts_var, width=80).pack(side="left")

        def _confirm():
            try:
                data = {
                    "topic": topic_var.get(),
                    "nb": int(nb_var.get() or 0),
                    "th": int(th_var.get() or 0),
                    "vd": int(vd_var.get() or 0),
                    "qtype": qtype_var.get(),
                    "points": float(pts_var.get() or 0.25),
                }
                if editing:
                    self._matrix_rows[edit_idx] = data
                else:
                    self._add_row(data)
                # Sửa grouped → detail không còn khớp → xoá detail (sẽ expand lại)
                self._matrix_detail.clear()
                self._render_matrix()
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e), parent=dlg)

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(pady=20)
        ctk.CTkButton(btn_row, text=("✓ Lưu" if editing else "✓ Thêm"),
                       fg_color="#10B981", hover_color="#059669",
                       command=_confirm).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Hủy", fg_color="#6B7280",
                       command=dlg.destroy).pack(side="left", padx=4)

    def _delete_selected_row(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Chưa chọn",
                                  "Hãy chọn 1 dòng trong bảng để xoá.",
                                  parent=self)
            return
        idx = self._tree.index(sel[0])
        if self._is_detail_mode():
            rows = self._matrix_detail or self._expand_grouped_to_detail()
            if 0 <= idx < len(rows):
                rows.pop(idx)
                # đánh số lại stt
                for i, d in enumerate(rows, 1): d["stt"] = i
                self._matrix_detail = rows
                self._rebuild_grouped_from_detail()
                self._render_matrix()
        else:
            if 0 <= idx < len(self._matrix_rows):
                self._matrix_rows.pop(idx)
                self._matrix_detail.clear()
                self._render_matrix()

    def _clear_all_rows(self):
        if messagebox.askyesno("Xoá hết", "Xoá toàn bộ ma trận?", parent=self):
            self._matrix_rows.clear()
            self._matrix_detail.clear()
            self._render_matrix()

    def _is_detail_mode(self) -> bool:
        return self._matrix_mode.get() == "detail"

    def _on_matrix_mode_change(self, choice: str):
        self._matrix_mode.set("detail" if "Chi tiết" in choice else "grouped")
        if self._is_detail_mode():
            self._tree.configure(displaycolumns=(
                "stt", "topic", "level", "qtype", "requirement", "points"))
            # Nếu chưa có detail (nhập tay) → expand từ grouped để xem/sửa
            if not self._matrix_detail and self._matrix_rows:
                self._matrix_detail = self._expand_grouped_to_detail()
        else:
            self._tree.configure(displaycolumns=(
                "topic", "nb", "th", "vd", "qtype", "points"))
        self._render_matrix()

    def _expand_grouped_to_detail(self) -> list:
        """Expand grouped rows → per-question detail rows (requirement rỗng)."""
        out = []; stt = 0
        for r in self._matrix_rows:
            for lvl, cnt in (("NB", r["nb"]), ("TH", r["th"]), ("VD", r["vd"])):
                for _ in range(int(cnt or 0)):
                    stt += 1
                    out.append({"stt": stt, "topic": r["topic"], "level": lvl,
                                 "qtype": r["qtype"],
                                 "requirement": f"{r['topic']} [{lvl}]",
                                 "points": float(r["points"]),
                                 "codes": [f"{r['qtype']}{stt}"]})
        return out

    def _render_matrix(self):
        from v5.tree_style import zebra_tag
        self._tree.delete(*self._tree.get_children())
        if self._is_detail_mode():
            rows = self._matrix_detail or self._expand_grouped_to_detail()
            for i, d in enumerate(rows):
                self._tree.insert("", "end", values=(
                    d.get("stt", i + 1), d.get("topic", ""),
                    d.get("level", ""), "", "", "",
                    d.get("qtype", ""), d.get("requirement", ""),
                    f"{float(d.get('points', 0.25)):.2f}"),
                    tags=(zebra_tag(i),))
            total_q = len(rows)
            total_pts = sum(float(d.get("points", 0.25)) for d in rows)
        else:
            for i, r in enumerate(self._matrix_rows):
                self._tree.insert("", "end", values=(
                    "", r["topic"], "", r["nb"], r["th"], r["vd"],
                    r["qtype"], "", f"{r['points']:.2f}"),
                    tags=(zebra_tag(i),))
            total_q = sum(r["nb"] + r["th"] + r["vd"] for r in self._matrix_rows)
            total_pts = sum((r["nb"] + r["th"] + r["vd"]) * r["points"]
                             for r in self._matrix_rows)
        self._matrix_summary.configure(
            text=f"  Tổng: {total_q} câu • {total_pts:.2f} điểm")

    def _on_matrix_dblclick(self, event=None):
        """Double-click 1 dòng ma trận → mở dialog sửa (theo mode)."""
        sel = self._tree.selection()
        if not sel:
            return
        idx = self._tree.index(sel[0])
        if self._is_detail_mode():
            self._edit_detail_row(idx)
        else:
            if 0 <= idx < len(self._matrix_rows):
                self._add_row_dialog(edit_idx=idx)

    def _edit_detail_row(self, idx: int):
        """Dialog sửa 1 câu trong ma trận chi tiết (chủ đề/mức/loại/yêu cầu)."""
        rows = self._matrix_detail or self._expand_grouped_to_detail()
        if not (0 <= idx < len(rows)):
            return
        self._matrix_detail = rows   # đảm bảo đã materialize
        d = rows[idx]
        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Sửa câu #{d.get('stt', idx+1)} trong ma trận")
        dlg.geometry("560x420")
        dlg.transient(self.winfo_toplevel()); dlg.grab_set()
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        ctk.CTkLabel(dlg, text=f"✏️ Đặc tả câu #{d.get('stt', idx+1)}",
                      font=("Segoe UI", 14, "bold")).pack(pady=(14, 8))
        frm = ctk.CTkFrame(dlg, fg_color="transparent")
        frm.pack(fill="x", padx=18)
        r1 = ctk.CTkFrame(frm, fg_color="transparent"); r1.pack(fill="x", pady=3)
        ctk.CTkLabel(r1, text="Chủ đề:", width=70, anchor="w").pack(side="left")
        topic_var = ctk.StringVar(value=d.get("topic", ""))
        ctk.CTkEntry(r1, textvariable=topic_var).pack(side="left", fill="x",
                                                        expand=True)
        r2 = ctk.CTkFrame(frm, fg_color="transparent"); r2.pack(fill="x", pady=3)
        ctk.CTkLabel(r2, text="Mức:", width=70, anchor="w").pack(side="left")
        level_var = ctk.StringVar(value=d.get("level", "TH"))
        ctk.CTkOptionMenu(r2, values=["NB", "TH", "VD", "VDC"],
                            variable=level_var, width=90).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(r2, text="Loại:", width=44, anchor="w").pack(side="left")
        qtype_var = ctk.StringVar(value=d.get("qtype", "TN"))
        ctk.CTkOptionMenu(r2, values=["TN", "DS", "TLN", "TL"],
                            variable=qtype_var, width=80).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(r2, text="Điểm:", width=44, anchor="w").pack(side="left")
        pts_var = ctk.StringVar(value=str(d.get("points", 0.25)))
        ctk.CTkEntry(r2, textvariable=pts_var, width=70).pack(side="left")

        ctk.CTkLabel(frm, text="Yêu cầu cần đạt (nội dung đặc tả câu này):",
                      anchor="w").pack(fill="x", pady=(8, 2))
        req_box = ctk.CTkTextbox(frm, height=140, font=("Segoe UI", 12),
                                   wrap="word")
        req_box.pack(fill="both", expand=True)
        req_box.insert("1.0", d.get("requirement", ""))

        def _save():
            d["topic"] = topic_var.get().strip()
            d["level"] = level_var.get()
            d["qtype"] = qtype_var.get()
            try: d["points"] = float(pts_var.get())
            except Exception: d["points"] = 0.25
            d["requirement"] = req_box.get("1.0", "end").strip()
            # Sync grouped lại từ detail để 2 view khớp
            self._rebuild_grouped_from_detail()
            self._render_matrix()
            dlg.destroy()

        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack(pady=14)
        ctk.CTkButton(btns, text="✓ Lưu", fg_color="#10B981",
                        hover_color="#059669", command=_save
                        ).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Huỷ", fg_color="#6B7280",
                        command=dlg.destroy).pack(side="left", padx=4)

    def _rebuild_grouped_from_detail(self):
        """Gộp lại _matrix_rows từ _matrix_detail (theo topic+qtype)."""
        groups = {}; order = []
        for d in self._matrix_detail:
            key = (d.get("topic", ""), d.get("qtype", "TN"))
            if key not in groups:
                groups[key] = {"topic": d.get("topic", ""), "nb": 0, "th": 0,
                                "vd": 0, "qtype": d.get("qtype", "TN"),
                                "points": float(d.get("points", 0.25))}
                order.append(key)
            lk = {"NB": "nb", "TH": "th", "VD": "vd",
                   "VDC": "vd"}.get(d.get("level", "TH"), "th")
            groups[key][lk] += 1
        self._matrix_rows = [groups[k] for k in order]

    # ── Generate ──────────────────────────────────────────────────────────
    _SOURCE_LABEL_TO_MODE = {
        "AI mới": "ai_only",
        "100% NHCH": "bank_only",
        "Kết hợp": "mixed",
    }

    def _selected_source_mode(self) -> str:
        return self._SOURCE_LABEL_TO_MODE.get(self._source_mode_var.get(), "ai_only")

    def _selected_source_ratio(self) -> int:
        mode = self._selected_source_mode()
        if mode == "ai_only":
            return 0
        if mode == "bank_only":
            return 100
        try:
            return max(10, min(90, int(self._source_ratio_var.get())))
        except Exception:
            return 50

    def _source_label(self) -> str:
        mode = self._selected_source_mode()
        ratio = self._selected_source_ratio()
        if mode == "bank_only":
            return "100% NHCH"
        if mode == "mixed":
            return f"Kết hợp {ratio}% NHCH"
        return "AI mới"

    def _on_source_ratio_changed(self, value) -> None:
        ratio = int(round(float(value) / 10) * 10)
        ratio = max(10, min(90, ratio))
        self._source_ratio_var.set(ratio)
        self._refresh_source_controls()

    def _on_source_mode_changed(self, _label: str | None = None) -> None:
        self._source_mode = self._selected_source_mode()
        self._refresh_source_controls()

    def _refresh_source_controls(self) -> None:
        mode = self._selected_source_mode()
        ratio = self._selected_source_ratio()
        if hasattr(self, "_source_ratio_lbl"):
            self._source_ratio_lbl.configure(text=f"{ratio}%")
        if hasattr(self, "_source_ratio_slider"):
            self._source_ratio_slider.configure(
                state=("normal" if mode == "mixed" else "disabled"))
        hint = {
            "ai_only": "AI tạo toàn bộ câu mới theo ma trận.",
            "bank_only": "Chỉ ưu tiên lấy câu từ NHCH local; câu thiếu sẽ báo lỗi để bạn bổ sung.",
            "mixed": f"Ưu tiên {ratio}% câu từ NHCH, phần còn lại AI tạo mới.",
        }.get(mode, "")
        if hasattr(self, "_source_hint"):
            self._source_hint.configure(text=hint)
        if hasattr(self, "_gen_btn"):
            self._gen_btn.configure(text=f"▶  Tạo đề ({self._source_label()})")

    def _feature_allowed(self, feature: str, *, notify: bool = True) -> bool:
        if not callable(self._can_use_feature):
            return True
        try:
            return bool(self._can_use_feature(feature, notify=notify))
        except TypeError:
            return bool(self._can_use_feature(feature))

    def apply_feature_gates(self, features: dict[str, bool]) -> None:
        """Mark restricted actions while retaining click feedback from the shell."""
        labels = [
            ("smart_prompt", self._smart_btn, "💬 Smart Prompt"),
            ("quick_gen", self._quick_btn, "🚀 Tạo đề nhanh"),
            ("export_word", self._export_btn, "📄  Xuất Word"),
            ("multi_code", self._multi_btn, "🔀  Trộn mã đề"),
            ("multi_code", self._variant_btn, "🧬  Đề tương tự"),
            ("tab_bank", self._bank_btn, "🏛  Lưu vào NHCH"),
        ]
        for feature, button, label in labels:
            prefix = "" if features.get(feature, True) else "🔒 "
            button.configure(text=prefix + label)

    def _on_generate(self):
        if not self._feature_allowed("tab_matrix"):
            return
        if self._busy:
            return
        if not self._matrix_rows:
            messagebox.showwarning("Trống", "Hãy thêm ít nhất 1 dòng ma trận.",
                                     parent=self); return
        source_mode = self._selected_source_mode()
        if source_mode in {"bank_only", "mixed"} and not self._feature_allowed("tab_bank"):
            return
        # Lấy ai_call từ setup view (qua main window). Chế độ 100% NHCH không
        # bắt buộc có API key, vì phần AI chỉ là fallback nếu NHCH thiếu câu.
        ai_call = self._resolve_ai_call()
        if not ai_call and source_mode != "bank_only":
            if messagebox.askyesno(
                "Thiếu AI key",
                "Chưa có API key cho AI provider nào.\n\n"
                "Mở ⚙️ Cấu hình để nhập key ngay?",
                parent=self):
                if self._on_navigate:
                    self._on_navigate("setup")
            return

        self._busy = True
        import threading as _th
        self._gen_cancel = _th.Event()
        self._gen_btn.configure(state="disabled", text="⏳ Đang sinh...")
        self._gen_cancel_btn.configure(state="normal")
        self._prog_bar.set(0)
        self._prog_lbl.configure(text="Bắt đầu...")
        self._generated_questions = []
        self._generate_progress_throttle = UiThrottle(self, 80)

        # Show loading overlay (spinner) trong khi chờ AI khởi tạo
        from v5.spinner import LoadingOverlay
        self._overlay = LoadingOverlay(
            self.winfo_toplevel(),
            "Đang chuẩn bị nguồn tạo đề...")

        def _worker():
            try:
                self.after(0, lambda: self._overlay.set_message(
                    f"Đang tạo đề ({self._source_label()})..."))
                self._do_generate(ai_call)
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror(
                    "Lỗi sinh đề", err[:300], parent=self))
            finally:
                self.after(0, self._finish_generate_worker)
        threading.Thread(target=_worker, daemon=True).start()

    def _open_smart_prompt(self):
        """Mở Smart Prompt dialog — apply matrix trực tiếp vào view này."""
        if not self._feature_allowed("smart_prompt"):
            return
        from v5.smart_prompt import SmartPromptDialog

        def _apply(matrix, info):
            try:
                # MatrixData.rows = nhiều MatrixRow (mỗi cái 1 câu, level đơn).
                # Gộp lại theo (topic, qtype) → đếm số câu mỗi mức cho UI v5.
                self._matrix_rows.clear()
                self._apply_matrix_to_rows(matrix)
                self._render_matrix()
                import re as _re
                ts = _re.search(r"\d+", str(getattr(matrix, "time_str", "") or ""))
                if ts and hasattr(self, "_duration_var"):
                    self._duration_var.set(ts.group(0))
            except Exception as e:
                print(f"exam_create apply matrix fail: {e}")

        SmartPromptDialog(self.winfo_toplevel(),
                            on_apply_matrix=_apply,
                            on_add_question=None)

    def open_quick_gen(self):
        """Mở dialog 'Tạo đề nhanh' — sinh ma trận theo mẫu thời lượng /
        số câu tự nhập (KHÔNG cần API key, không gọi AI)."""
        if not self._feature_allowed("quick_gen"):
            return
        from v5.quick_gen import QuickGenDialogV5

        def _apply(matrix, subject, grade):
            try:
                self._matrix_rows.clear()
                self._apply_matrix_to_rows(matrix)
                self._render_matrix()
                # Title
                t = getattr(matrix, "title", "") or ""
                if t and hasattr(self, "_title_var"):
                    self._title_var.set(t[:80])
                # Lớp
                if grade and hasattr(self, "_grade_var"):
                    try: self._grade_var.set(str(grade))
                    except Exception: pass
                # Thời lượng (lấy số phút)
                import re as _re
                ts = _re.search(r"\d+",
                                  str(getattr(matrix, "time_str", "") or ""))
                if ts and hasattr(self, "_duration_var"):
                    self._duration_var.set(ts.group(0))
            except Exception as e:
                print(f"exam_create quick_gen apply fail: {e}")

        default_grade = (self._grade_var.get()
                          if hasattr(self, "_grade_var") else "12")
        QuickGenDialogV5(self.winfo_toplevel(),
                          on_accept=_apply,
                          default_subject="Toán",
                          default_grade=default_grade)

    def open_ai_gen_matrix(self):
        """Mở dialog 'Tạo ma trận đề bằng AI' (form fields → AI sinh)."""
        if not self._feature_allowed("tab_matrix"):
            return
        from v5.ai_gen_matrix import AIGenMatrixDialogV5

        def _apply(matrix, subject, grade):
            try:
                self._matrix_rows.clear()
                self._apply_matrix_to_rows(matrix)
                self._render_matrix()
                t = getattr(matrix, "title", "") or ""
                if t and hasattr(self, "_title_var"):
                    self._title_var.set(t[:80])
                if grade and hasattr(self, "_grade_var"):
                    try: self._grade_var.set(str(grade))
                    except Exception: pass
                import re as _re
                ts = _re.search(r"\d+",
                                  str(getattr(matrix, "time_str", "") or ""))
                if ts and hasattr(self, "_duration_var"):
                    self._duration_var.set(ts.group(0))
            except Exception as e:
                print(f"exam_create ai_gen_matrix apply fail: {e}")

        default_grade = (self._grade_var.get()
                          if hasattr(self, "_grade_var") else "12")
        AIGenMatrixDialogV5(self.winfo_toplevel(),
                              on_accept=_apply,
                              default_subject="Toán",
                              default_grade=default_grade)

    def _upload_matrix_file(self):
        """Tải file ma trận (Word/Excel/PDF/ảnh) → parse rule-based, fallback
        AI nhận diện → nạp vào bảng ma trận (port luồng V4 tab_config)."""
        from pathlib import Path
        path = filedialog.askopenfilename(
            parent=self, title="Chọn file ma trận đặc tả",
            filetypes=[("Hỗ trợ", "*.docx *.doc *.xlsx *.xls *.pdf "
                                   "*.png *.jpg *.jpeg"),
                        ("Word", "*.docx *.doc"), ("Excel", "*.xlsx *.xls"),
                        ("PDF", "*.pdf"), ("Ảnh", "*.png *.jpg *.jpeg")])
        if not path:
            return
        ext = Path(path).suffix.lower()
        fname = Path(path).name

        from v5.spinner import LoadingOverlay
        ov = LoadingOverlay(self.winfo_toplevel(),
                              f"Đang quét ma trận từ {fname}…")

        def _done(matrix, err):
            try: ov.close()
            except Exception: pass
            try:
                if not self.winfo_exists(): return
            except Exception: return
            if err:
                messagebox.showerror("Lỗi quét ma trận", str(err)[:300],
                                      parent=self)
                return
            if matrix is None or not getattr(matrix, "rows", None):
                messagebox.showwarning(
                    "Không nhận diện được",
                    f"Không quét được ma trận từ {fname}.\n"
                    "Thử file khác hoặc nhập tay / dùng Smart Prompt.",
                    parent=self)
                return
            # Nạp vào bảng (aggregate level đơn → grouped)
            self._matrix_rows.clear()
            self._apply_matrix_to_rows(matrix)
            self._render_matrix()
            # Title/time nếu có
            import re as _re
            t = getattr(matrix, "title", "") or ""
            if t and hasattr(self, "_title_var"):
                self._title_var.set(t[:80])
            ts = _re.search(r"\d+", str(getattr(matrix, "time_str", "") or ""))
            if ts and hasattr(self, "_duration_var"):
                self._duration_var.set(ts.group(0))
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(),
                        f"✓ Đã nạp ma trận {len(self._matrix_rows)} chủ đề "
                        f"từ {fname}", kind="success", duration=5)

        def _worker():
            matrix = None; err = None
            try:
                # PDF/ảnh → AI; Word/Excel → parse rule-based trước
                if ext in (".pdf", ".png", ".jpg", ".jpeg"):
                    matrix = self._ai_recognize_matrix(path)
                else:
                    try:
                        from core.parser import parse_matrix_file
                        matrix = parse_matrix_file(path)
                    except Exception as e:
                        matrix = None
                    # parse rỗng → fallback AI
                    if matrix is None or not getattr(matrix, "rows", None):
                        matrix = self._ai_recognize_matrix(path)
            except Exception as e:
                err = e
            self.after(0, lambda: _done(matrix, err))

        import threading as _th
        _th.Thread(target=_worker, daemon=True).start()

    def _ai_recognize_matrix(self, filepath: str):
        """Gọi AI nhận diện ma trận từ file. Trả MatrixData hoặc None."""
        ai_call = self._resolve_ai_call()
        if not ai_call:
            raise RuntimeError("Cần API key (⚙ Cấu hình) để AI nhận diện ma trận.")
        from core.ai_matrix_recognizer import recognize_matrix
        return recognize_matrix(filepath, ai_call)

    def _apply_matrix_to_rows(self, matrix):
        """Nạp MatrixData → lưu CẢ chi tiết từng câu (giữ yêu cầu cần đạt)
        VÀ bản gộp {topic, nb, th, vd, qtype, points} cho bảng v5."""
        # 1. Chi tiết từng câu (giữ requirement + codes)
        self._matrix_detail = []
        for i, r in enumerate(getattr(matrix, "rows", []), 1):
            self._matrix_detail.append({
                "stt": i,
                "topic": getattr(r, "topic", "") or "",
                "level": (getattr(r, "level", "TH") or "TH").upper(),
                "qtype": getattr(r, "qtype", "TN") or "TN",
                "requirement": getattr(r, "requirement", "") or "",
                "points": float(getattr(r, "points", 0.25) or 0.25),
                "codes": list(getattr(r, "codes", []) or []),
            })
        # 2. Gộp từ detail
        self._rebuild_grouped_from_detail()

    def _open_analyze_exam(self):
        """Phân tích đề thi đã có thành ma trận đặc tả V5."""
        if not self._feature_allowed("tab_matrix"):
            return
        from v5.analyze_exam import AnalyzeExamDialog

        def _apply(matrix):
            try:
                self._matrix_rows.clear()
                self._apply_matrix_to_rows(matrix)
                title = getattr(matrix, "title", "") or ""
                if title:
                    self._title_var.set(title[:100])
                import re as _re
                duration = _re.search(r"\d+", str(getattr(matrix, "time_str", "") or ""))
                if duration:
                    self._duration_var.set(duration.group(0))
                self._render_matrix()
                from v5.toast import show_toast
                show_toast(
                    self.winfo_toplevel(),
                    f"✓ Đã nạp ma trận từ đề ({len(matrix.rows)} dòng)",
                    kind="success",
                    duration=5,
                )
            except Exception as exc:
                messagebox.showerror("Lỗi nạp ma trận", str(exc)[:300],
                                     parent=self)

        AnalyzeExamDialog(
            self.winfo_toplevel(),
            get_ai_call=self._resolve_ai_call,
            on_matrix_ready=_apply,
        )

    def _open_template_library(self):
        """Chọn một mẫu ma trận đóng gói và nạp vào trình biên soạn V5."""
        if not self._feature_allowed("tab_matrix"):
            return
        from services.matrix_templates import list_templates, load_template

        templates = list_templates(filter_subject="Toán")
        if not templates:
            messagebox.showinfo("Thư viện mẫu", "Không có mẫu ma trận đóng gói.",
                                parent=self)
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("📚 Thư viện mẫu ma trận")
        dlg.geometry("780x620")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="📚  THƯ VIỆN MẪU MA TRẬN ĐỀ",
                      font=("Segoe UI", 18, "bold")).pack(
                          anchor="w", padx=18, pady=(16, 4))
        ctk.CTkLabel(
            dlg, text="Chọn mẫu để thay ma trận hiện tại; bạn vẫn sửa từng dòng trước khi sinh đề.",
            text_color="gray").pack(anchor="w", padx=18, pady=(0, 10))

        filter_row = ctk.CTkFrame(dlg, fg_color="transparent")
        filter_row.pack(fill="x", padx=18, pady=(0, 10))
        query_var = ctk.StringVar()
        ctk.CTkEntry(filter_row, textvariable=query_var,
                     placeholder_text="Tìm tên, tag hoặc mô tả...",
                     width=390).pack(side="left", padx=(0, 10))
        grade_var = ctk.StringVar(value="Tất cả lớp")
        ctk.CTkOptionMenu(
            filter_row, values=["Tất cả lớp", "10", "11", "12"],
            variable=grade_var, width=135,
            command=lambda _choice: _render()).pack(side="left")

        listing = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        listing.pack(fill="both", expand=True, padx=14, pady=4)
        count_lbl = ctk.CTkLabel(dlg, text="", text_color="gray")
        count_lbl.pack(anchor="w", padx=18, pady=(4, 12))

        def _apply(template_id: str):
            if self._matrix_rows and not messagebox.askyesno(
                "Thay ma trận hiện tại",
                "Nạp mẫu sẽ thay toàn bộ ma trận đang chỉnh. Tiếp tục?",
                parent=dlg,
            ):
                return
            matrix = load_template(template_id)
            if matrix is None:
                messagebox.showerror("Lỗi", "Không đọc được mẫu đã chọn.",
                                     parent=dlg)
                return
            self._matrix_rows.clear()
            self._apply_matrix_to_rows(matrix)
            self._title_var.set(matrix.title[:100])
            import re as _re
            duration = _re.search(r"\d+", str(matrix.time_str or ""))
            if duration:
                self._duration_var.set(duration.group(0))
            for item in templates:
                if item["id"] == template_id and item.get("grade"):
                    self._grade_var.set(str(item["grade"]))
                    break
            self._render_matrix()
            dlg.destroy()
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(), "✓ Đã nạp mẫu ma trận",
                       kind="success", duration=4)

        def _render(*_args):
            for widget in listing.winfo_children():
                widget.destroy()
            query = query_var.get().strip().lower()
            grade = grade_var.get()
            visible = []
            for item in templates:
                if grade != "Tất cả lớp" and str(item.get("grade")) != grade:
                    continue
                haystack = " ".join([
                    item.get("name", ""), item.get("description", ""),
                    " ".join(item.get("tags", [])),
                ]).lower()
                if query and query not in haystack:
                    continue
                visible.append(item)
            count_lbl.configure(text=f"{len(visible)} mẫu phù hợp")
            for item in visible:
                card = ctk.CTkFrame(listing, fg_color=("#F3F4F6", "#293548"))
                card.pack(fill="x", padx=4, pady=4)
                text_box = ctk.CTkFrame(card, fg_color="transparent")
                text_box.pack(side="left", fill="x", expand=True, padx=12, pady=9)
                ctk.CTkLabel(
                    text_box,
                    text=f"{item.get('icon', '📋')}  {item.get('name', '')}",
                    font=("Segoe UI", 12, "bold"), anchor="w").pack(anchor="w")
                stats = item.get("stats", {})
                summary = (
                    f"Lớp {item.get('grade', '?')} • {item.get('time_str', '')} • "
                    f"{item.get('n_rows', 0)} câu "
                    f"(TN {stats.get('TN', 0)}, DS {stats.get('DS', 0)}, "
                    f"TLN {stats.get('TLN', 0)}, TL {stats.get('TL', 0)})")
                ctk.CTkLabel(text_box, text=summary, text_color="gray",
                             anchor="w").pack(anchor="w")
                ctk.CTkLabel(text_box, text=item.get("description", ""),
                             text_color="gray", anchor="w",
                             wraplength=500, justify="left").pack(anchor="w")
                ctk.CTkButton(
                    card, text="Dùng mẫu", width=100,
                    command=lambda tid=item["id"]: _apply(tid)).pack(
                        side="right", padx=12)
            if not visible:
                ctk.CTkLabel(listing, text="Không tìm thấy mẫu phù hợp.",
                             text_color="gray").pack(pady=30)

        query_var.trace_add("write", _render)
        _render()

    def _current_matrix_data(self):
        """Dựng MatrixData từ bảng V5 hiện tại để xuất đặc tả."""
        from core.models import MatrixData, MatrixRow
        rows: list[MatrixRow] = []
        if self._matrix_detail:
            for i, item in enumerate(self._matrix_detail, 1):
                rows.append(MatrixRow(
                    stt=str(item.get("stt", i)),
                    topic=item.get("topic", ""),
                    level=item.get("level", "TH"),
                    qtype=item.get("qtype", "TN"),
                    codes=list(item.get("codes") or [f"Q{i}"]),
                    requirement=item.get("requirement", ""),
                    points=float(item.get("points", 0.25) or 0.25),
                    enabled=True,
                ))
        else:
            idx = 0
            for item in self._matrix_rows:
                for level, count in (("NB", item["nb"]), ("TH", item["th"]),
                                     ("VD", item["vd"])):
                    for _ in range(int(count or 0)):
                        idx += 1
                        qtype = item["qtype"]
                        rows.append(MatrixRow(
                            stt=str(idx), topic=item["topic"], level=level,
                            qtype=qtype, codes=[f"{qtype}{idx}"],
                            requirement=f"{item['topic']} [{level}]",
                            points=float(item["points"]), enabled=True,
                        ))
        return MatrixData(
            title=self._title_var.get() or "MA TRẬN ĐỀ KIỂM TRA",
            time_str=f"{self._duration_var.get() or '90'} phút",
            rows=rows,
        )

    def _export_matrix(self):
        """Xuất ma trận đặc tả đang chỉnh sang Word chuẩn BGD hoặc CSV."""
        if not self._feature_allowed("tab_matrix"):
            return
        matrix = self._current_matrix_data()
        if not matrix.rows:
            messagebox.showwarning("Ma trận trống", "Chưa có dòng nào để xuất.",
                                   parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self, title="Xuất ma trận đặc tả",
            defaultextension=".docx",
            initialfile="Ma_tran_de_kiem_tra.docx",
            filetypes=[("Word chuẩn BGD", "*.docx"), ("CSV", "*.csv")])
        if not path:
            return
        try:
            from export.matrix_exporter import export_matrix_csv, export_matrix_docx
            if Path(path).suffix.lower() == ".csv":
                export_matrix_csv(matrix, path)
            else:
                export_matrix_docx(matrix, path)
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(), f"✓ Đã xuất ma trận: {Path(path).name}",
                       kind="success", duration=5)
        except Exception as exc:
            messagebox.showerror("Lỗi xuất ma trận", str(exc)[:300], parent=self)

    def _resolve_ai_call(self):
        """Lấy callable AI từ Setup view / settings_store."""
        try:
            from services.key_manager import get_key_manager
            from services.ai_service import create_ai_service
            from services.retry_service import split_keys
            from v5 import settings_store
            from config import AI_PROVIDERS

            km = get_key_manager()
            saved_prov = settings_store.get("ai_provider")
            saved_model = settings_store.get("ai_model")

            # Ưu tiên provider đã được user chọn trong Cấu hình
            prov_order = []
            if saved_prov:
                prov_order.append(saved_prov)
            for p in ("9Router", "Google Gemini", "Anthropic Claude", "DeepSeek", "OpenAI GPT"):
                if p not in prov_order:
                    prov_order.append(p)

            for prov in prov_order:
                key = km.load(prov)
                if key or prov == "9Router":
                    keys = (key if isinstance(key, list) else split_keys(key)) if key else ["dummy_key"]
                    if prov == saved_prov and saved_model:
                        model = saved_model
                    else:
                        models = AI_PROVIDERS.get(prov, {}).get("models", [])
                        model = models[0] if models else "gemini-3.8-flash"
                    svc = create_ai_service(prov, keys, model)
                    return svc.generate
        except Exception as e:
            print(f"resolve_ai_call fail: {e}")
        return None

    def _update_generate_progress(self, done: int, total: int, msg: str = "") -> None:
        total = max(total, 1)
        self._prog_bar.set(done / total)
        self._prog_lbl.configure(text=f"{done}/{total} {msg[:50]}")
        overlay = getattr(self, "_overlay", None)
        if overlay is not None:
            try:
                overlay.set_sub(f"{done}/{total} {msg[:70]}")
            except Exception:
                pass

    def _finish_generate_worker(self) -> None:
        throttle = getattr(self, "_generate_progress_throttle", None)
        if throttle is not None:
            throttle.cancel()
            self._generate_progress_throttle = None
        self._after_generate()

    def _do_generate(self, ai_call):
        """Build matrix rows → gọi generator → câu hỏi."""
        from core.models import MatrixRow
        from core.generator import generate_all, generate_exam_with_source
        from core.models import ExamData

        # Build list MatrixRow. Nếu có ma trận CHI TIẾT (từ file tải lên) →
        # dùng nguyên requirement từng câu (chất lượng cao hơn). Nếu không →
        # expand từ grouped {nb,th,vd}.
        rows = []
        if self._matrix_detail:
            for i, d in enumerate(self._matrix_detail, 1):
                rows.append(MatrixRow(
                    stt=str(d.get("stt", i)), topic=d.get("topic", ""),
                    level=d.get("level", "TH"), qtype=d.get("qtype", "TN"),
                    codes=(d.get("codes") or [f"{d.get('qtype','TN')}{i}"]),
                    requirement=d.get("requirement", "")
                                  or f"{d.get('topic','')} [{d.get('level','TH')}]",
                    points=float(d.get("points", 0.25)), enabled=True))
        else:
            stt = 0
            for r in self._matrix_rows:
                qtype = r["qtype"]; topic = r["topic"]; pts = float(r["points"])
                for level, count in (("NB", r["nb"]), ("TH", r["th"]),
                                      ("VD", r["vd"])):
                    for _ in range(int(count or 0)):
                        stt += 1
                        rows.append(MatrixRow(
                            stt=str(stt), topic=topic, level=level,
                            qtype=qtype, codes=[f"{qtype}{stt}"],
                            requirement=f"{topic} [{level}]",
                            points=pts, enabled=True))
        if not rows:
            self.after(0, lambda: messagebox.showwarning(
                "Ma trận trống",
                "Tổng số câu = 0. Hãy nhập NB/TH/VD > 0 ở ít nhất 1 dòng.",
                parent=self))
            return

        duration = self._duration_var.get() or "90"
        title = self._title_var.get() or "Đề kiểm tra Toán 12"

        # Progress callback (signature đúng: progress_cb, không phải callback)
        def _on_progress(done: int, total: int, msg: str = ""):
            throttle = getattr(self, "_generate_progress_throttle", None)
            if throttle is None:
                throttle = UiThrottle(self, 80)
                self._generate_progress_throttle = throttle
            throttle.schedule(self._update_generate_progress, done, total, msg)

        source_mode = self._selected_source_mode()
        source_ratio = self._selected_source_ratio()
        fallback_ai_call = ai_call
        if fallback_ai_call is None:
            def fallback_ai_call(*_args, **_kwargs):
                raise RuntimeError(
                    "NHCH thiếu câu phù hợp và chưa có API key để tạo bù."
                )

        # Gọi generator — TRẢ VỀ ExamData (AI-only) hoặc list[Question] (NHCH/mixed).
        # ExamData dùng field exam_title/semester/year/time (KHÔNG phải
        # title/duration_min/rows).
        grade = self._grade_var.get() if hasattr(self, "_grade_var") else "12"
        if source_mode == "ai_only":
            result = generate_all(
                rows, subject="Toán", grade=grade,
                semester="1", year="",
                ai_call=fallback_ai_call, progress_cb=_on_progress,
                cancel_event=getattr(self, "_gen_cancel", None))
        else:
            result = generate_exam_with_source(
                rows, subject="Toán", grade=grade,
                ai_call=fallback_ai_call,
                mode=source_mode,
                bank_ratio=source_ratio,
                progress_cb=lambda i, n, msg: _on_progress(i + 1, n, msg),
            )

        if hasattr(result, "questions"):
            # Dùng ExamData generator trả về, chỉ override exam_title + time
            exam = result
            try:
                exam.exam_title = title
                exam.time = f"{duration} phút"
            except Exception: pass
            questions = exam.questions
        else:
            # Version cũ trả list[Question] → build ExamData đúng field
            questions = result or []
            exam = ExamData(
                exam_title=title, subject="Toán", grade=grade,
                semester="1", year="", time=f"{duration} phút",
                questions=questions)

        self._apply_default_exam_metadata(exam)
        self._exam = exam
        self._generated_questions = questions
        try:
            self._result_status.configure(
                text=f"✓ Nguồn tạo đề: {self._source_label()}",
                text_color="#10B981")
        except Exception:
            pass
        self._publish_exam_change()

    def _cancel_generate(self):
        """Set cancel_event → generate_all thoát sớm ở câu tiếp theo."""
        ev = getattr(self, "_gen_cancel", None)
        if ev is not None:
            ev.set()
        self._gen_cancel_btn.configure(state="disabled", text="⛔ Đang dừng…")
        self._prog_lbl.configure(text="⛔ Đang dừng sau câu hiện tại…")

    def _after_generate(self):
        self._busy = False
        self._gen_btn.configure(state="normal", text=f"▶  Tạo đề ({self._source_label()})")
        self._refresh_source_controls()
        try: self._gen_cancel_btn.configure(state="disabled", text="⛔ Dừng")
        except Exception: pass
        # Close spinner overlay
        try:
            if hasattr(self, "_overlay") and self._overlay:
                self._overlay.close(); self._overlay = None
        except Exception: pass

        # Toast success/fail
        try:
            from v5.toast import show_toast
            if self._generated_questions:
                show_toast(self.winfo_toplevel(),
                            f"Đã sinh {len(self._generated_questions)} câu",
                            kind="success")
        except Exception: pass

        n = len(self._generated_questions)
        self._prog_bar.set(1.0 if n > 0 else 0)
        self._prog_lbl.configure(
            text=f"✓ Sinh xong {n} câu" if n > 0 else "✘ Không có câu")
        self._render_preview()
        self._sync_result_action_state()
        if n > 0:
            self._run_post_generate_export()

    def _run_post_generate_export(self):
        """Tự xuất Word sau khi sinh đề, dùng lại hành vi/service của V4."""
        if not self._exam or not self._exam.questions:
            return
        if not self._feature_allowed("export_word", notify=False):
            self._result_status.configure(
                text="Tự xuất Word không khả dụng với quyền hiện tại.",
                text_color="#F59E0B")
            return
        try:
            from config import is_auto_export_enabled
            enabled = is_auto_export_enabled()
        except Exception:
            enabled = True
        if not enabled:
            self._result_status.configure(
                text="Tự xuất Word đang tắt; dùng nút Xuất Word để chọn file.",
                text_color="gray")
            return

        exam = self._exam
        self._result_status.configure(text="⏳ Đang tự xuất Word...",
                                      text_color="#3B82F6")

        def _worker():
            try:
                from services.auto_export import auto_export_exam
                path, error = auto_export_exam(
                    exam,
                    include_solution=self._include_solutions_on_export(),
                    open_after=self._open_after_export_enabled(),
                    auto_convert_tables=self._word_auto_convert_tables())
            except Exception as exc:
                path, error = None, str(exc)
            self.after(0, lambda: self._on_auto_export_done(path, error))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_auto_export_done(self, path, error):
        if error or path is None:
            self._result_status.configure(
                text=f"✘ Tự xuất lỗi: {(error or 'không tạo được file')[:100]}",
                text_color="#EF4444")
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(),
                       "Auto-export thất bại; hãy bấm Xuất Word để lưu thủ công.",
                       kind="warn", duration=6)
            return
        self._remember_export_path(Path(path), auto=True)

    def _remember_export_path(self, path: Path, *, auto: bool = False):
        self._last_export_path = Path(path)
        for button in (self._folder_btn, self._copy_btn, self._relocate_btn):
            button.configure(state="normal")
        prefix = "Tự xuất xong" if auto else "Đã xuất"
        self._result_status.configure(
            text=f"✓ {prefix}: {self._last_export_path}",
            text_color="#10B981")
        from v5.toast import show_toast
        show_toast(
            self.winfo_toplevel(),
            f"✓ Đã lưu Word: {self._last_export_path.name}",
            kind="success", duration=8,
            action_label="Thư mục", action_cb=self._open_export_folder)

    def _open_export_folder(self):
        path = self._last_export_path
        if path is None:
            return
        try:
            import os
            import subprocess
            import sys
            folder = path.parent
            if os.name == "nt":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:
            messagebox.showerror("Lỗi mở thư mục", str(exc), parent=self)

    def _open_export_file(self, path: Path) -> None:
        try:
            import os
            import subprocess
            import sys
            if os.name == "nt":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showwarning("Không mở được file", str(exc)[:240], parent=self)

    def _save_export_copy(self):
        if not self._exam:
            return
        try:
            from services.auto_export import save_extra_copy
            initial_dir = (self._last_export_path.parent
                           if self._last_export_path else None)
            initial_name = (self._last_export_path.name
                            if self._last_export_path else None)
            path, error = save_extra_copy(
                self._exam, initial_dir=initial_dir,
                initial_filename=initial_name,
                include_solution=self._include_solutions_on_export(),
                auto_convert_tables=self._word_auto_convert_tables())
            if error:
                raise RuntimeError(error)
            if path:
                self._remember_export_path(Path(path), auto=False)
        except Exception as exc:
            messagebox.showerror("Lỗi lưu bản sao", str(exc)[:300],
                                 parent=self)

    def _relocate_export(self):
        """Chuyển file vừa xuất và lưu thư mục mặc định cho lần sau."""
        if self._last_export_path is None:
            return
        folder = filedialog.askdirectory(
            parent=self, title="Đổi thư mục tự xuất Word",
            initialdir=str(self._last_export_path.parent))
        if not folder:
            return
        source = self._last_export_path
        destination = Path(folder) / source.name
        if destination == source:
            return
        try:
            counter = 2
            while destination.exists():
                destination = Path(folder) / f"{source.stem}_v{counter}{source.suffix}"
                counter += 1
            import shutil
            shutil.move(str(source), str(destination))
            from config import set_auto_export_dir
            set_auto_export_dir(str(folder))
            self._last_export_path = destination
            self._result_status.configure(
                text=f"✓ Đã chuyển file; lần sau tự xuất vào: {folder}",
                text_color="#10B981")
            self._open_export_folder()
        except Exception as exc:
            messagebox.showerror("Lỗi đổi thư mục", str(exc)[:300],
                                 parent=self)

    def _disable_auto_export(self):
        from config import set_auto_export_enabled
        set_auto_export_enabled(False)
        self._result_status.configure(
            text="Tự xuất Word đã tắt; có thể bật lại trong Tuỳ chọn (Ctrl+,).",
            text_color="gray")
        from v5.toast import show_toast
        show_toast(self.winfo_toplevel(), "Đã tắt tự xuất Word", kind="info")

    def _save_exam_to_nhch(self):
        """Lưu các câu hợp lệ của đề hiện tại vào NHCH local như workflow V4."""
        if not self._feature_allowed("tab_bank"):
            return
        if not self._exam or not self._exam.questions:
            return
        valid = [q for q in self._exam.questions if not getattr(q, "_error", False)]
        if not valid:
            messagebox.showinfo("NHCH", "Không có câu hợp lệ để lưu.",
                                parent=self)
            return
        if not messagebox.askyesno(
            "Lưu vào NHCH",
            f"Lưu {len(valid)} câu hợp lệ của đề hiện tại vào NHCH local?",
            parent=self,
        ):
            return
        try:
            from storage.database import save_questions
            saved = save_questions(
                valid, self._exam.subject or "Toán",
                str(self._exam.grade or self._grade_var.get() or "12"),
                source=self._exam.exam_title or "V5 Exam Create")
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(),
                       f"✓ Đã lưu {saved} câu vào NHCH",
                       kind="success", duration=5)
        except Exception as exc:
            messagebox.showerror("Lỗi lưu NHCH", str(exc)[:300], parent=self)

    def _selected_tikz_conversion_mode(self) -> str:
        selected = self._tikz_mode_var.get() if hasattr(self, "_tikz_mode_var") else ""
        option = getattr(self, "_tikz_options_by_label", {}).get(selected)
        if option:
            return option["mode"]
        return TIKZ_OUTPUT_MODE_EMF

    def _on_tikz_mode_changed(self, selected: str | None = None) -> None:
        option = getattr(self, "_tikz_options_by_label", {}).get(
            selected or self._tikz_mode_var.get()
        )
        if option and hasattr(self, "_tikz_emf_status"):
            self._tikz_emf_status.configure(text=option["description"], text_color="gray")

    def _convert_exam_tikz_to_emf(self):
        """Render toàn bộ TikZ trong đề theo lựa chọn EMF hoặc PNG."""
        mode = self._selected_tikz_conversion_mode()
        option = get_tikz_conversion_option(mode)
        label = option["label"]
        if not self._exam or not self._exam.questions:
            messagebox.showinfo(label, "Hãy tạo hoặc nạp đề trước.", parent=self)
            return
        from services.tikz_vector_workflow import (
            convert_exam_tikz_to_emf,
            convert_exam_tikz_to_png,
            count_pending_blocks,
        )
        converter = (
            convert_exam_tikz_to_png
            if mode == TIKZ_OUTPUT_MODE_PNG
            else convert_exam_tikz_to_emf
        )

        total = count_pending_blocks(self._exam)
        if total <= 0:
            messagebox.showinfo(
                "Không có TikZ",
                f"Đề hiện tại không có khối TikZ nào cần chuyển bằng {label}.",
                parent=self,
            )
            return
        if not messagebox.askyesno(
            f"Chuyển {label}",
            f"Tìm thấy {total} khối TikZ.\n\n"
            f"{option['confirm']}",
            parent=self,
        ):
            return

        self._tikz_emf_btn.configure(state="disabled", text="⏳  Đang chuyển...")
        self._tikz_emf_status.configure(
            text=f"Đang chuyển 0/{total} khối TikZ...", text_color="#3B82F6")
        self._result_status.configure(
            text=f"⏳ Đang chuyển {total} khối TikZ thành {option['result_name']}...",
            text_color="#3B82F6")
        self._tikz_current_mode = mode
        exam = self._exam

        def _progress(done: int, count: int, errors: int):
            self.after(0, lambda: self._tikz_emf_status.configure(
                text=f"Đang chuyển {done}/{count} khối TikZ"
                     f"{' - lỗi: ' + str(errors) if errors else ''}...",
                text_color=("#F59E0B" if errors else "#3B82F6")))

        def _worker():
            try:
                report = converter(
                    exam, dpi=300, progress_cb=_progress)
                self.after(0, lambda: self._on_tikz_emf_done(report))
            except Exception as exc:
                self.after(0, lambda err=str(exc): self._on_tikz_emf_error(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_tikz_emf_done(self, report) -> None:
        mode = getattr(report, "output_mode", getattr(self, "_tikz_current_mode", TIKZ_OUTPUT_MODE_EMF))
        option = get_tikz_conversion_option(mode)
        label = option["label"]
        has_questions = bool(self._exam and self._exam.questions)
        self._tikz_emf_btn.configure(
            state=("normal" if has_questions else "disabled"),
            text="📐  Chuyển")
        self._generated_questions = list(self._exam.questions) if self._exam else []
        self._publish_exam_change()
        self._render_preview()
        summary = report.summary()
        if report.failed:
            failed = [
                f"Câu {result.q_index + 1}: {result.error}"
                for result in report.results if result.error
            ]
            self._tikz_emf_status.configure(text=summary, text_color="#F59E0B")
            self._result_status.configure(
                text=f"⚠ {label} hoàn tất một phần: {summary}",
                text_color="#F59E0B")
            messagebox.showwarning(
                f"Báo cáo {label}",
                summary + "\n\n" + "\n".join(failed)[:900],
                parent=self,
            )
            return
        self._tikz_emf_status.configure(text=summary, text_color="#10B981")
        self._result_status.configure(
            text=f"✓ {label} hoàn tất: {summary}",
            text_color="#10B981")
        try:
            from v5.toast import show_toast
            show_toast(
                self.winfo_toplevel(),
                f"✓ Đã chuyển {report.emf or report.ok} hình TikZ thành {option['result_name']}",
                kind="success",
                duration=5,
            )
        except Exception:
            pass

    def _on_tikz_emf_error(self, error: str) -> None:
        mode = getattr(self, "_tikz_current_mode", TIKZ_OUTPUT_MODE_EMF)
        label = get_tikz_conversion_option(mode)["label"]
        self._tikz_emf_btn.configure(
            state="normal",
            text="📐  Chuyển",
        )
        self._tikz_emf_status.configure(text=f"Chuyển {label} thất bại.", text_color="#EF4444")
        self._result_status.configure(
            text=f"✕ {label} lỗi: {error[:120]}",
            text_color="#EF4444")
        messagebox.showerror(f"Lỗi {label}", error[:700], parent=self)

    def _open_exam_metadata_dialog(self) -> None:
        """Sửa metadata đề như tab Kết quả V4, đồng bộ cho Word export."""
        if not self._exam:
            messagebox.showinfo(
                "Chưa có đề",
                "Hãy tạo hoặc nạp một đề trước khi sửa thông tin.",
                parent=self,
            )
            return

        exam = self._exam
        default_school, default_teacher = self._default_school_info()
        dlg = ctk.CTkToplevel(self)
        dlg.title("Sửa thông tin đề")
        dlg.geometry("760x470")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.resizable(False, False)
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        hdr = ctk.CTkFrame(dlg, fg_color=("#0F2D52", "#0B1F3A"), corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr,
            text="✏️  Sửa thông tin đề kiểm tra",
            font=("Segoe UI", 16, "bold"),
            text_color="white",
            anchor="w",
        ).pack(side="left", padx=18, pady=12)
        ctk.CTkLabel(
            hdr,
            text="Dữ liệu này đi thẳng vào header Word/export",
            font=("Segoe UI", 10),
            text_color="#BFDBFE",
        ).pack(side="right", padx=18, pady=12)

        body = ctk.CTkFrame(dlg, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=16)
        for col, weight in enumerate((0, 1, 0, 1)):
            body.grid_columnconfigure(col, weight=weight)

        title_var = ctk.StringVar(value=getattr(exam, "exam_title", "") or self._title_var.get())
        subject_var = ctk.StringVar(value=getattr(exam, "subject", "") or "Toán")
        grade_var = ctk.StringVar(value=str(getattr(exam, "grade", "") or self._grade_var.get() or "12"))
        semester_var = ctk.StringVar(value=str(getattr(exam, "semester", "") or ""))
        year_var = ctk.StringVar(value=str(getattr(exam, "year", "") or ""))
        time_var = ctk.StringVar(value=str(getattr(exam, "time", "") or f"{self._duration_var.get() or '90'} phút"))
        school_var = ctk.StringVar(value=str(getattr(exam, "school", "") or default_school))
        teacher_var = ctk.StringVar(value=str(getattr(exam, "teacher", "") or default_teacher))
        save_defaults_var = ctk.BooleanVar(value=False)

        def _label(row: int, col: int, text: str) -> None:
            ctk.CTkLabel(
                body,
                text=text,
                font=("Segoe UI", 11, "bold"),
                anchor="e",
                width=96,
            ).grid(row=row, column=col, sticky="e", padx=(0, 8), pady=6)

        def _entry(row: int, label: str, var, *, col: int = 0, width: int = 210,
                   values: list[str] | None = None):
            _label(row, col * 2, label)
            if values is None:
                widget = ctk.CTkEntry(body, textvariable=var, width=width)
            else:
                widget = ctk.CTkOptionMenu(body, values=values, variable=var, width=width)
            widget.grid(row=row, column=col * 2 + 1, sticky="we", padx=(0, 18), pady=6)
            return widget

        _label(0, 0, "Tiêu đề đề:")
        ctk.CTkEntry(body, textvariable=title_var, width=560).grid(
            row=0, column=1, columnspan=3, sticky="we", padx=(0, 18), pady=6)

        _entry(1, "Môn:", subject_var, col=0)
        _entry(1, "Lớp:", grade_var, col=1, width=110,
               values=[str(i) for i in range(1, 13)])
        _entry(2, "Kỳ:", semester_var, col=0,
               values=["", "Giữa kì I", "Cuối kì I", "Giữa kì II", "Cuối kì II", "I", "II"])
        _entry(2, "Năm:", year_var, col=1, width=140)
        _entry(3, "Thời gian:", time_var, col=0,
               values=["15 phút", "30 phút", "45 phút", "60 phút", "90 phút", "120 phút"])

        _label(4, 0, "Tên trường:")
        ctk.CTkEntry(body, textvariable=school_var, width=560).grid(
            row=4, column=1, columnspan=3, sticky="we", padx=(0, 18), pady=6)
        _label(5, 0, "GV ra đề:")
        ctk.CTkEntry(body, textvariable=teacher_var, width=560).grid(
            row=5, column=1, columnspan=3, sticky="we", padx=(0, 18), pady=6)

        ctk.CTkCheckBox(
            body,
            text="Lưu trường/GV làm mặc định cho các đề sau",
            variable=save_defaults_var,
        ).grid(row=6, column=1, columnspan=3, sticky="w", pady=(8, 0))

        ctk.CTkLabel(
            body,
            text="Mẹo: để trống Trường/GV nếu muốn Word dùng header mặc định.",
            text_color="gray",
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=7, column=1, columnspan=3, sticky="we", pady=(8, 0))

        def _save() -> None:
            import re as _re
            title = title_var.get().strip()
            subject = subject_var.get().strip()
            grade = grade_var.get().strip()
            semester = semester_var.get().strip()
            year = year_var.get().strip()
            time_text = time_var.get().strip()
            if time_text and time_text.isdigit():
                time_text = f"{time_text} phút"

            exam.exam_title = title or exam.exam_title
            exam.subject = subject or exam.subject
            exam.grade = grade or exam.grade
            exam.semester = semester
            exam.year = year
            exam.time = time_text or exam.time
            exam.school = school_var.get().strip()
            exam.teacher = teacher_var.get().strip()

            if save_defaults_var.get():
                try:
                    from config import set_school_info
                    set_school_info(exam.school, exam.teacher)
                except Exception:
                    pass

            self._title_var.set((exam.exam_title or "")[:80])
            if exam.grade:
                self._grade_var.set(str(exam.grade))
            duration = _re.search(r"\d+", str(exam.time or ""))
            if duration:
                self._duration_var.set(duration.group(0))
            self._publish_exam_change()
            self._render_preview()
            self._sync_result_action_state()
            self._result_status.configure(
                text=f"✓ Đã cập nhật thông tin đề: {exam.exam_title}",
                text_color="#10B981")
            try:
                from v5.toast import show_toast
                show_toast(self.winfo_toplevel(),
                           "✓ Đã lưu thông tin đề cho export Word",
                           kind="success", duration=4)
            except Exception:
                pass
            dlg.destroy()

        actions = ctk.CTkFrame(dlg, fg_color="transparent")
        actions.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkButton(
            actions,
            text="✓ Lưu thông tin",
            width=150,
            fg_color="#10B981",
            hover_color="#059669",
            command=_save,
        ).pack(side="right", padx=(6, 0))
        ctk.CTkButton(
            actions,
            text="Hủy",
            width=90,
            fg_color="#6B7280",
            hover_color="#4B5563",
            command=dlg.destroy,
        ).pack(side="right")

    def _open_export_settings_dialog(self) -> None:
        """Cài đặt xuất Word như V4: math mode, lời giải, tự mở file, header."""
        try:
            from config import is_auto_export_enabled
            auto_export_init = is_auto_export_enabled()
        except Exception:
            auto_export_init = True

        default_school, default_teacher = self._default_school_info()
        school_init = (getattr(self._exam, "school", "") or default_school
                       if self._exam else default_school)
        teacher_init = (getattr(self._exam, "teacher", "") or default_teacher
                        if self._exam else default_teacher)

        dlg = ctk.CTkToplevel(self)
        dlg.title("Cài đặt xuất Word")
        dlg.geometry("560x560")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.resizable(False, False)
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        hdr = ctk.CTkFrame(dlg, fg_color=("#0F2D52", "#0B1F3A"), corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(
            hdr,
            text="⚙️  Cài đặt xuất Word",
            font=("Segoe UI", 16, "bold"),
            text_color="white",
            anchor="w",
        ).pack(side="left", padx=18, pady=12)

        body = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=14)

        def _settings_card(title: str):
            card = ctk.CTkFrame(body, fg_color=("#F8FAFC", "#1E293B"),
                                corner_radius=10, border_width=1,
                                border_color=("#E5E7EB", "#334155"))
            card.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(card, text=title, font=("Segoe UI", 12, "bold"),
                         anchor="w").pack(fill="x", padx=12, pady=(10, 6))
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=(0, 12))
            return inner

        math_mode_var = ctk.StringVar(value=self._word_math_mode())
        include_sol_var = ctk.BooleanVar(value=self._include_solutions_on_export())
        open_after_var = ctk.BooleanVar(value=self._open_after_export_enabled())
        auto_export_var = ctk.BooleanVar(value=auto_export_init)
        auto_table_var = ctk.BooleanVar(value=self._word_auto_convert_tables())
        school_var = ctk.StringVar(value=school_init)
        teacher_var = ctk.StringVar(value=teacher_init)

        math_card = _settings_card("1. Chế độ công thức toán")
        for value, text, note in (
            ("text", "Text inline $...$", "Nhanh, giữ công thức dạng văn bản LaTeX trong Word."),
            ("mathtype", "MathType / OMML", "Chậm hơn, nhưng công thức có thể chỉnh trong Word."),
        ):
            ctk.CTkRadioButton(
                math_card,
                text=text,
                variable=math_mode_var,
                value=value,
                font=("Segoe UI", 11),
            ).pack(anchor="w", pady=(4, 0))
            ctk.CTkLabel(math_card, text=note, text_color="gray",
                         font=("Segoe UI", 9), wraplength=470,
                         justify="left").pack(anchor="w", padx=28)

        header_card = _settings_card("2. Thông tin in trên đầu đề")
        ctk.CTkLabel(header_card, text="Trường:", font=("Segoe UI", 10, "bold"),
                     anchor="w").pack(fill="x")
        ctk.CTkEntry(header_card, textvariable=school_var).pack(fill="x", pady=(2, 8))
        ctk.CTkLabel(header_card, text="GV ra đề:", font=("Segoe UI", 10, "bold"),
                     anchor="w").pack(fill="x")
        ctk.CTkEntry(header_card, textvariable=teacher_var).pack(fill="x", pady=(2, 0))

        behavior_card = _settings_card("3. Hành vi sau khi xuất")
        ctk.CTkCheckBox(
            behavior_card,
            text="Kèm đáp án và lời giải khi xuất Word",
            variable=include_sol_var,
        ).pack(anchor="w", pady=4)
        ctk.CTkCheckBox(
            behavior_card,
            text="Tự mở file Word sau khi xuất thủ công / auto-export",
            variable=open_after_var,
        ).pack(anchor="w", pady=4)
        ctk.CTkCheckBox(
            behavior_card,
            text="Tự xuất Word ngay sau khi tạo đề bằng AI",
            variable=auto_export_var,
        ).pack(anchor="w", pady=4)
        ctk.CTkCheckBox(
            behavior_card,
            text="Tự chuyển dòng có dấu | thành bảng Word",
            variable=auto_table_var,
        ).pack(anchor="w", pady=(10, 2))
        ctk.CTkLabel(
            behavior_card,
            text="Tắt nếu công thức hoặc hình vẽ bị nhảy thành bảng.",
            text_color="gray",
            font=("Segoe UI", 9),
            wraplength=470,
            justify="left",
        ).pack(anchor="w", padx=28)

        def _save() -> None:
            try:
                from config import (
                    set_auto_export_enabled,
                    set_export_solution_enabled,
                    set_open_after_export_enabled,
                    set_school_info,
                    set_word_auto_convert_tables_enabled,
                    set_word_math_mode,
                )
                set_word_math_mode(math_mode_var.get())
                set_word_auto_convert_tables_enabled(bool(auto_table_var.get()))
                set_export_solution_enabled(bool(include_sol_var.get()))
                set_open_after_export_enabled(bool(open_after_var.get()))
                set_auto_export_enabled(bool(auto_export_var.get()))
                set_school_info(school_var.get(), teacher_var.get())
                self._include_solution_var.set(bool(include_sol_var.get()))
                self._auto_table_var.set(bool(auto_table_var.get()))
            except Exception as exc:
                messagebox.showerror("Lỗi lưu cài đặt", str(exc)[:300], parent=dlg)
                return

            if self._exam is not None:
                self._exam.school = school_var.get().strip()
                self._exam.teacher = teacher_var.get().strip()
                self._publish_exam_change()
                self._render_preview()

            self._result_status.configure(
                text="✓ Đã lưu cài đặt xuất Word.",
                text_color="#10B981")
            try:
                from v5.toast import show_toast
                show_toast(self.winfo_toplevel(),
                           "✓ Đã lưu cài đặt xuất Word",
                           kind="success", duration=4)
            except Exception:
                pass
            dlg.destroy()

        actions = ctk.CTkFrame(dlg, fg_color="transparent")
        actions.pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkButton(
            actions,
            text="✓ Lưu cài đặt",
            width=145,
            fg_color="#10B981",
            hover_color="#059669",
            command=_save,
        ).pack(side="right", padx=(6, 0))
        ctk.CTkButton(
            actions,
            text="Hủy",
            width=90,
            fg_color="#6B7280",
            hover_color="#4B5563",
            command=dlg.destroy,
        ).pack(side="right")

    def _ensure_editable_exam(self) -> ExamData:
        """Tạo ExamData nháp khi người dùng muốn soạn/sửa thủ công trước khi gọi AI."""
        if self._exam is None:
            title = self._title_var.get().strip() or "Đề đang soạn"
            grade = self._grade_var.get().strip() or "12"
            duration = self._duration_var.get().strip() or "90"
            self._exam = ExamData(
                exam_title=title,
                subject="Toán",
                grade=grade,
                semester="1",
                year="",
                time=f"{duration} phút",
                questions=list(self._generated_questions),
            )
            self._apply_default_exam_metadata(self._exam)
        return self._exam

    def _default_blank_question_topic(self) -> str:
        idx = self._selected_preview_index(prefer_selection=True, notify=False)
        if idx is not None and 0 <= idx < len(self._generated_questions):
            topic = str(getattr(self._generated_questions[idx], "topic", "") or "").strip()
            if topic:
                return topic
        if self._matrix_detail:
            topic = str(self._matrix_detail[0].get("topic", "") or "").strip()
            if topic:
                return topic
        if self._matrix_rows:
            topic = str(self._matrix_rows[0].get("topic", "") or "").strip()
            if topic:
                return topic
        return TOPICS[0]

    def _make_blank_preview_question(self) -> Question:
        """Câu nháp tối thiểu để mở editor ngay, giúp sửa đề thủ công nhanh hơn."""
        topic = self._default_blank_question_topic()
        question = Question(
            qtype="TN",
            level="NB",
            topic=topic,
            question="Nhập nội dung câu hỏi tại đây.",
            solution="",
            options={"A": "", "B": "", "C": "", "D": ""},
            answer="A",
            points=0.25,
        )
        question._row_snapshot = {
            "topic": topic,
            "level": "NB",
            "qtype": "TN",
            "points": 0.25,
            "requirement": "Câu thêm thủ công",
        }
        return question

    def _preview_index_from_entry(self, *, notify: bool = False) -> int | None:
        if not self._generated_questions:
            if notify:
                messagebox.showinfo("Chưa có câu", "Chưa có câu nào trong đề để chọn.", parent=self)
            return None
        raw = self._question_jump_var.get().strip() if hasattr(self, "_question_jump_var") else ""
        try:
            number = int(raw)
        except (TypeError, ValueError):
            if notify:
                messagebox.showwarning("Số câu chưa hợp lệ", "Nhập số câu cần thao tác, ví dụ: 1, 2, 3.", parent=self)
            return None
        if number < 1 or number > len(self._generated_questions):
            if notify:
                messagebox.showwarning(
                    "Ngoài phạm vi",
                    f"Đề hiện có {len(self._generated_questions)} câu. Hãy nhập số từ 1 đến {len(self._generated_questions)}.",
                    parent=self,
                )
            return None
        return number - 1

    def _selected_preview_index(self, *, prefer_selection: bool = True, notify: bool = False) -> int | None:
        if prefer_selection and hasattr(self, "_preview_tree"):
            sel = self._preview_tree.selection()
            if sel:
                try:
                    return self._preview_tree.index(sel[0])
                except Exception:
                    pass
        return self._preview_index_from_entry(notify=notify)

    def _select_preview_question(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._generated_questions):
            return
        children = self._preview_tree.get_children()
        if idx < len(children):
            item = children[idx]
            self._preview_tree.selection_set(item)
            self._preview_tree.focus(item)
            self._preview_tree.see(item)
        if hasattr(self, "_question_jump_var"):
            self._question_jump_var.set(str(idx + 1))
        self._result_status.configure(
            text=f"Đã chọn Câu {idx + 1}. Bấm Sửa, Nhân bản hoặc double-click để chỉnh.",
            text_color="gray",
        )

    def _on_preview_select(self, _event=None) -> None:
        sel = self._preview_tree.selection()
        if not sel:
            return
        try:
            idx = self._preview_tree.index(sel[0])
        except Exception:
            return
        if hasattr(self, "_question_jump_var"):
            self._question_jump_var.set(str(idx + 1))

    def _jump_to_preview_question(self) -> None:
        idx = self._preview_index_from_entry(notify=True)
        if idx is not None:
            self._select_preview_question(idx)

    def _edit_selected_preview_question(self) -> None:
        idx = self._selected_preview_index(prefer_selection=True, notify=True)
        if idx is not None:
            self._open_preview_question(idx)

    def _duplicate_preview_question(self) -> None:
        """Nhân bản câu đang chọn rồi mở editor để sửa thành câu mới."""
        idx = self._selected_preview_index(prefer_selection=True, notify=True)
        if idx is None:
            return
        clone = clone_question_for_edit(self._generated_questions[idx])
        insert_at = idx + 1
        self._generated_questions.insert(insert_at, clone)
        self._ensure_editable_exam()
        self._sync_preview_questions_to_exam()
        self._render_preview()
        self._sync_result_action_state()
        self._select_preview_question(insert_at)
        self._result_status.configure(
            text=f"✓ Đã nhân bản Câu {idx + 1} thành Câu {insert_at + 1}. Hãy sửa nội dung rồi lưu.",
            text_color="#10B981",
        )
        self._open_preview_question(insert_at)

    def _insert_blank_preview_question(self) -> None:
        """Chèn một câu trống vào đề hiện tại và mở editor ngay."""
        idx = self._selected_preview_index(prefer_selection=True, notify=False)
        insert_at = (idx + 1) if idx is not None else len(self._generated_questions)
        question = self._make_blank_preview_question()
        self._generated_questions.insert(insert_at, question)
        self._ensure_editable_exam()
        self._sync_preview_questions_to_exam()
        self._render_preview()
        self._sync_result_action_state()
        self._select_preview_question(insert_at)
        self._prog_bar.set(1.0 if self._generated_questions else 0.0)
        self._prog_lbl.configure(text=f"✓ Đang soạn {len(self._generated_questions)} câu")
        self._result_status.configure(
            text=f"✓ Đã chèn Câu {insert_at + 1} trống. Editor đã mở để nhập nội dung.",
            text_color="#10B981",
        )
        self._open_preview_question(insert_at)

    def _render_preview(self):
        from v5.tree_style import zebra_tag
        self._preview_tree.delete(*self._preview_tree.get_children())
        for i, q in enumerate(self._generated_questions, 1):
            preview = (q.question or "").replace("\n", " ")[:120]
            self._preview_tree.insert("", "end", values=(
                i, q.qtype, q.level, (q.topic or "")[:24], preview),
                tags=(zebra_tag(i),))
        count = len(self._generated_questions)
        self._preview_lbl.configure(
            text=(f"  {count} câu đã tạo:"
                  if count
                  else "(Chưa có câu nào — bấm 'Tạo đề' ở trên)"))
        if hasattr(self, "_question_jump_var"):
            if count:
                current = self._preview_index_from_entry(notify=False)
                if current is None:
                    self._question_jump_var.set("1")
            else:
                self._question_jump_var.set("1")
        if hasattr(self, "_question_cards"):
            self._question_cards.set_questions(self._generated_questions)

    def _on_preview_edit(self, event=None):
        """Double-click câu trong preview → mở dialog sửa (CTk)."""
        sel = self._preview_tree.selection()
        if not sel:
            return
        try:
            idx = self._preview_tree.index(sel[0])
        except Exception:
            return
        self._open_preview_question(idx)

    def _open_preview_question(self, idx: int):
        """Mở editor cho một card/câu trong phần xem chi tiết V5."""
        if idx < 0 or idx >= len(self._generated_questions):
            return
        q = self._generated_questions[idx]

        def _on_save(updated_q):
            # Cập nhật câu trong list + sync vào exam + re-render
            try:
                self._generated_questions[idx] = updated_q
                if self._exam and idx < len(self._exam.questions):
                    self._exam.questions[idx] = updated_q
                self._publish_exam_change()
                self._render_preview()
                from v5.toast import show_toast
                show_toast(self.winfo_toplevel(), "✓ Đã cập nhật câu hỏi",
                            kind="success")
            except Exception as e:
                messagebox.showerror("Lỗi", str(e), parent=self)

        try:
            from v5.edit_question import EditQuestionDialogCTk
            _g = self._grade_var.get() if hasattr(self, "_grade_var") else "12"
            EditQuestionDialogCTk(self.winfo_toplevel(), q,
                                    on_save_cb=_on_save,
                                    get_ai_call=(self._resolve_ai_call_factory()
                                        if self._feature_allowed("ai_review", notify=False)
                                        else None),
                                    subject="Toán", grade=_g)
        except Exception as e:
            messagebox.showerror("Lỗi mở dialog sửa", str(e), parent=self)

    def _preview_question_latex(self, idx: int) -> None:
        """Mở xem trước LaTeX cho từng câu ngay trên card kết quả."""
        if idx < 0 or idx >= len(self._generated_questions):
            return
        try:
            from v5.latex_preview import LatexPreviewDialog
            LatexPreviewDialog(
                self.winfo_toplevel(),
                self._generated_questions[idx],
                idx,
            )
        except Exception as e:
            messagebox.showerror("Lỗi xem LaTeX", str(e), parent=self)

    def _finish_single_regenerate(self) -> None:
        self._busy = False
        try:
            self._gen_btn.configure(state="normal", text=f"▶  Tạo đề ({self._source_label()})")
            self._gen_cancel_btn.configure(state="disabled", text="⛔ Dừng")
        except Exception:
            pass

    def _failed_question_indexes(self) -> list[int]:
        return [
            index for index, question in enumerate(self._generated_questions)
            if bool(getattr(question, "_error", False))
        ]

    def _regenerate_preview_question(self, idx: int) -> None:
        """Tạo lại một câu bằng AI từ row snapshot gốc, giống thao tác card V4."""
        if not self._feature_allowed("tab_matrix"):
            return
        if self._busy:
            messagebox.showinfo("Đang xử lý", "Đợi tác vụ hiện tại hoàn tất rồi tạo lại câu.", parent=self)
            return
        if idx < 0 or idx >= len(self._generated_questions):
            return
        question = self._generated_questions[idx]
        row_dict = getattr(question, "_row_snapshot", None)
        if not isinstance(row_dict, dict) or not row_dict:
            messagebox.showwarning(
                "Không thể tạo lại",
                f"Câu {idx + 1} không có thông tin ma trận gốc.\n"
                "Chỉ có thể tạo lại câu được sinh từ AI trong phiên tạo đề.",
                parent=self,
            )
            return
        if not messagebox.askyesno(
            "Tạo lại câu hỏi",
            f"Tạo lại Câu {idx + 1} bằng AI?\n"
            f"Chủ đề: {getattr(question, 'topic', '')}\n"
            f"Loại: {getattr(question, 'qtype', '')} | Mức: {getattr(question, 'level', '')}",
            parent=self,
        ):
            return

        try:
            from core.models import MatrixRow
            row = MatrixRow.from_dict(dict(row_dict))
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không thể khôi phục thông tin ma trận:\n{exc}", parent=self)
            return

        ai_call = self._resolve_ai_call()
        if not ai_call:
            if messagebox.askyesno(
                "Thiếu AI key",
                "Chưa có API key cho AI provider nào.\n\nMở ⚙️ Cấu hình để nhập key ngay?",
                parent=self,
            ) and self._on_navigate:
                self._on_navigate("setup")
            return

        grade = self._grade_var.get() if hasattr(self, "_grade_var") else "12"
        subject = getattr(self._exam, "subject", "") if self._exam else ""
        subject = subject or "Toán"
        old_question_id = str(getattr(question, "question_id", "") or "")

        self._busy = True
        self._gen_btn.configure(state="disabled", text="⏳ Đang tạo lại...")
        try:
            self._gen_cancel_btn.configure(state="disabled", text="⛔ Dừng")
        except Exception:
            pass
        self._prog_lbl.configure(text=f"⏳ Đang tạo lại Câu {idx + 1}...")
        self._result_status.configure(
            text=f"⏳ Đang tạo lại Câu {idx + 1} bằng AI...",
            text_color="#2563EB",
        )

        def _worker():
            try:
                from core.generator import generate_one
                new_question = generate_one(row, subject, grade, ai_call)
                self.after(
                    0,
                    lambda: self._on_regenerate_preview_done(
                        idx, new_question, old_question_id, row, grade
                    ),
                )
            except Exception as exc:
                self.after(0, lambda err=str(exc): self._on_regenerate_preview_error(idx, err))

        threading.Thread(target=_worker, daemon=True).start()

    def _retry_failed_preview_questions(self) -> None:
        """Tạo lại toàn bộ câu lỗi trong đề hiện tại từ row snapshot gốc."""
        if not self._feature_allowed("tab_matrix"):
            return
        if self._busy:
            messagebox.showinfo("Đang xử lý", "Đợi tác vụ hiện tại hoàn tất rồi tạo lại câu lỗi.", parent=self)
            return
        failed = self._failed_question_indexes()
        if not failed:
            messagebox.showinfo("Tạo lại lỗi", "Đề hiện tại không có câu lỗi.", parent=self)
            return
        retryable: list[tuple[int, object, dict]] = []
        missing_snapshot: list[int] = []
        for idx in failed:
            question = self._generated_questions[idx]
            row_dict = getattr(question, "_row_snapshot", None)
            if isinstance(row_dict, dict) and row_dict:
                retryable.append((idx, question, row_dict))
            else:
                missing_snapshot.append(idx + 1)
        if not retryable:
            messagebox.showwarning(
                "Không thể tạo lại",
                "Các câu lỗi hiện tại không có thông tin ma trận gốc để sinh lại.",
                parent=self,
            )
            return

        note = ""
        if missing_snapshot:
            note = "\n\nBỏ qua câu thiếu ma trận gốc: " + ", ".join(map(str, missing_snapshot))
        if not messagebox.askyesno(
            "Tạo lại câu lỗi",
            f"Tạo lại {len(retryable)} câu lỗi bằng AI?{note}",
            parent=self,
        ):
            return

        ai_call = self._resolve_ai_call()
        if not ai_call:
            if messagebox.askyesno(
                "Thiếu AI key",
                "Chưa có API key cho AI provider nào.\n\nMở ⚙️ Cấu hình để nhập key ngay?",
                parent=self,
            ) and self._on_navigate:
                self._on_navigate("setup")
            return

        grade = self._grade_var.get() if hasattr(self, "_grade_var") else "12"
        subject = getattr(self._exam, "subject", "") if self._exam else ""
        subject = subject or "Toán"
        self._busy = True
        self._gen_btn.configure(state="disabled", text="⏳ Đang tạo lại lỗi...")
        self._retry_failed_btn.configure(state="disabled", text="⏳  Đang tạo lại lỗi...")
        self._prog_bar.set(0)
        self._prog_lbl.configure(text=f"0/{len(retryable)} câu lỗi")
        self._result_status.configure(
            text=f"⏳ Đang tạo lại {len(retryable)} câu lỗi bằng AI...",
            text_color="#2563EB",
        )
        progress_throttle = UiThrottle(self, 80)

        def _worker():
            results = []
            errors = []
            try:
                from core.generator import generate_one
                from core.models import MatrixRow

                total = len(retryable)
                for done, (idx, old_question, row_dict) in enumerate(retryable, 1):
                    try:
                        row = MatrixRow.from_dict(dict(row_dict))
                        new_question = generate_one(row, subject, grade, ai_call)
                        old_id = str(getattr(old_question, "question_id", "") or "")
                        results.append((idx, new_question, old_id, row))
                    except Exception as exc:
                        errors.append((idx, str(exc)))
                    progress_throttle.schedule(
                        self._update_retry_failed_progress, done, total, idx)
            except Exception as exc:
                self.after(0, lambda err=str(exc): (
                    progress_throttle.cancel(),
                    self._on_retry_failed_batch_error(err)))
                return
            self.after(0, lambda: (
                progress_throttle.cancel(),
                self._on_retry_failed_batch_done(results, errors, grade)))

        threading.Thread(target=_worker, daemon=True).start()

    def _update_retry_failed_progress(self, done: int, total: int, idx: int) -> None:
        self._prog_bar.set(done / max(total, 1))
        self._prog_lbl.configure(text=f"{done}/{total} câu lỗi")
        self._result_status.configure(
            text=f"⏳ Đang tạo lại Câu {idx + 1} ({done}/{total})...",
            text_color="#2563EB",
        )

    def _on_retry_failed_batch_done(self, results: list, errors: list, grade: str) -> None:
        self._finish_single_regenerate()
        replaced = 0
        still_error = 0
        for idx, new_question, old_question_id, row in results:
            if idx < 0 or idx >= len(self._generated_questions):
                continue
            try:
                if old_question_id:
                    new_question.question_id = old_question_id
                else:
                    from core.models import assign_structured_ids
                    assign_structured_ids([new_question], grade, rows=[row])
            except Exception:
                pass
            self._generated_questions[idx] = new_question
            replaced += 1
            if getattr(new_question, "_error", False):
                still_error += 1
        self._sync_preview_questions_to_exam()
        self._render_preview()
        self._sync_result_action_state()
        failed_left = len(self._failed_question_indexes())
        self._prog_bar.set(1.0 if self._generated_questions else 0.0)
        self._prog_lbl.configure(text=f"✓ Đã thử tạo lại {replaced} câu lỗi")
        if errors or still_error:
            self._result_status.configure(
                text=(f"⚠ Đã tạo lại {replaced} câu; còn {failed_left} câu lỗi "
                      f"({len(errors)} lỗi chạy, {still_error} câu AI trả lỗi)."),
                text_color="#D97706",
            )
        else:
            self._result_status.configure(
                text=f"✓ Đã tạo lại {replaced} câu lỗi. Đề hiện không còn câu lỗi.",
                text_color="#10B981",
            )
        try:
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(), f"✓ Đã xử lý {replaced} câu lỗi", kind="success")
        except Exception:
            pass

    def _on_retry_failed_batch_error(self, error: str) -> None:
        self._finish_single_regenerate()
        self._sync_result_action_state()
        self._result_status.configure(
            text=f"✘ Lỗi tạo lại câu lỗi: {error[:90]}",
            text_color="#EF4444",
        )
        messagebox.showerror("Lỗi tạo lại câu lỗi", error[:500], parent=self)

    def _open_qc_current_exam(self) -> None:
        """Đưa đề hiện tại sang tab QC để kiểm tra chất lượng như action V4."""
        if not self._feature_allowed("tab_qc"):
            return
        if not self._generated_questions:
            messagebox.showinfo("Chưa có đề", "Hãy tạo hoặc nạp đề trước khi chạy QC.", parent=self)
            return
        self._sync_preview_questions_to_exam()
        if callable(self._on_navigate):
            self._on_navigate("qc")
        else:
            messagebox.showinfo(
                "QC đề hiện tại",
                "Đề đã sẵn sàng. Mở tab Kiểm tra chất lượng để chạy QC.",
                parent=self,
            )

    def _on_regenerate_preview_done(self, idx: int, new_question, old_question_id: str, row, grade: str) -> None:
        """Cập nhật preview khi tạo lại một câu hoàn tất."""
        self._finish_single_regenerate()
        if idx < 0 or idx >= len(self._generated_questions):
            self._result_status.configure(text="⚠ Câu đã thay đổi trong lúc tạo lại.", text_color="#D97706")
            return
        try:
            if old_question_id:
                new_question.question_id = old_question_id
            else:
                from core.models import assign_structured_ids
                assign_structured_ids([new_question], grade, rows=[row])
        except Exception:
            pass
        self._generated_questions[idx] = new_question
        if self._exam is not None:
            if idx < len(self._exam.questions):
                self._exam.questions[idx] = new_question
            else:
                self._exam.questions = list(self._generated_questions)
        self._publish_exam_change()
        self._render_preview()
        self._sync_result_action_state()
        self._prog_bar.set(1.0 if self._generated_questions else 0.0)
        if getattr(new_question, "_error", False):
            error_msg = str(getattr(new_question, "_error_msg", "") or "AI trả về câu lỗi.")
            self._result_status.configure(
                text=f"✘ Tạo lại Câu {idx + 1} chưa thành công: {error_msg[:90]}",
                text_color="#EF4444",
            )
            messagebox.showerror("Tạo lại câu lỗi", error_msg[:500], parent=self)
            return
        self._prog_lbl.configure(text=f"✓ Đã tạo lại Câu {idx + 1}")
        self._result_status.configure(
            text=f"✓ Đã tạo lại Câu {idx + 1} và cập nhật đề hiện tại.",
            text_color="#10B981",
        )
        try:
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(), f"✓ Đã tạo lại Câu {idx + 1}", kind="success")
        except Exception:
            pass

    def _on_regenerate_preview_error(self, idx: int, error: str) -> None:
        self._finish_single_regenerate()
        self._result_status.configure(
            text=f"✘ Lỗi tạo lại Câu {idx + 1}: {error[:90]}",
            text_color="#EF4444",
        )
        messagebox.showerror("Lỗi tạo lại", error[:500], parent=self)

    def _sync_preview_questions_to_exam(self) -> None:
        """Đồng bộ thứ tự/xoá/sửa card về ExamData trước khi export/push."""
        if self._exam is not None:
            self._exam.questions = list(self._generated_questions)
        self._publish_exam_change()

    def _question_score_value(self, question) -> float:
        """Điểm câu hỏi, ưu tiên snapshot ma trận để không mất điểm tuỳ chỉnh."""
        snapshot = getattr(question, "_row_snapshot", None) or {}
        if isinstance(snapshot, dict):
            try:
                return float(snapshot.get("points"))
            except (TypeError, ValueError):
                pass
        qtype = str(getattr(question, "qtype", "") or "").upper()
        if qtype in {"TLN", "TL"}:
            try:
                return float(getattr(question, "points"))
            except (TypeError, ValueError):
                pass
        try:
            from config import POINTS_MAP
            return float(POINTS_MAP.get(qtype, 0.25))
        except Exception:
            return 0.25

    def _check_result_score(self) -> None:
        """Kiểm tra tổng điểm của đề hiện tại như action Result ở V4."""
        if not self._generated_questions:
            messagebox.showinfo("Kiểm tra điểm", "Hãy tạo hoặc nạp đề trước.", parent=self)
            return
        self._sync_preview_questions_to_exam()
        total = sum(self._question_score_value(q) for q in self._generated_questions)
        delta = 10.0 - total
        if abs(delta) < 0.01:
            verdict = "✅ Đạt thang 10 điểm."
            color = "#10B981"
        elif delta > 0:
            verdict = f"⚠ Chưa đủ 10 điểm (còn thiếu {delta:.2f} điểm)."
            color = "#D97706"
        else:
            verdict = f"⚠ Vượt thang 10 điểm ({abs(delta):.2f} điểm)."
            color = "#D97706"
        summary = (
            "Tổng điểm tính theo thang 10:\n\n"
            f"Số câu: {len(self._generated_questions)}\n"
            f"Tổng điểm: {total:.2f}\n\n"
            f"{verdict}"
        )
        self._result_status.configure(
            text=f"🧮 Kiểm tra điểm: {len(self._generated_questions)} câu, tổng {total:.2f}/10.",
            text_color=color,
        )
        messagebox.showinfo("Kiểm tra điểm", summary, parent=self)

    def _export_error_report(self) -> None:
        """Xuất danh sách câu lỗi `_error` ra TXT, giữ lại thông tin để sửa nhanh."""
        if not self._generated_questions:
            messagebox.showinfo("Báo cáo lỗi", "Hãy tạo hoặc nạp đề trước.", parent=self)
            return
        self._sync_preview_questions_to_exam()
        errors = [
            (index + 1, question)
            for index, question in enumerate(self._generated_questions)
            if bool(getattr(question, "_error", False))
        ]
        if not errors:
            self._result_status.configure(
                text="📋 Báo cáo lỗi: đề hiện tại không có câu bị lỗi.",
                text_color="#10B981",
            )
            messagebox.showinfo("Báo cáo lỗi", "✅ Không có câu bị lỗi!", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Lưu báo cáo lỗi",
            defaultextension=".txt",
            filetypes=[("Văn bản", "*.txt")],
            initialfile="bao_cao_loi_v5.txt",
        )
        if not path:
            return
        exam_title = getattr(self._exam, "exam_title", "") if self._exam else ""
        lines = [
            f"BÁO CÁO LỖI — {len(errors)} câu bị lỗi",
            f"Đề: {exam_title or self._title_var.get().strip() or 'Chưa đặt tên'}",
            f"Tổng số câu: {len(self._generated_questions)}",
            "",
        ]
        for number, question in errors:
            msg = str(getattr(question, "_error_msg", "") or "Không rõ lỗi").strip()
            qtype = str(getattr(question, "qtype", "") or "").strip()
            level = str(getattr(question, "level", "") or "").strip()
            topic = str(getattr(question, "topic", "") or "").strip()
            body = " ".join(str(getattr(question, "question", "") or "").split())
            if len(body) > 240:
                body = f"{body[:237]}..."
            lines.extend([
                f"Câu {number}: {msg}",
                f"  Loại/Mức: {qtype or '-'} / {level or '-'}",
                f"  Chủ đề: {topic or '-'}",
                f"  Nội dung: {body or '-'}",
                "",
            ])
        output_path = Path(path)
        try:
            output_path.write_text("\n".join(lines), encoding="utf-8")
            self._result_status.configure(
                text=f"📋 Đã xuất báo cáo lỗi: {output_path.name}",
                text_color="#10B981",
            )
            try:
                from v5.toast import show_toast
                show_toast(self.winfo_toplevel(), f"✓ Đã xuất báo cáo lỗi: {output_path.name}", kind="success")
            except Exception:
                pass
            messagebox.showinfo("Đã xuất", f"Lưu báo cáo lỗi tại:\n{output_path}", parent=self)
        except Exception as exc:
            messagebox.showerror("Lỗi xuất báo cáo lỗi", str(exc)[:300], parent=self)

    def _move_preview_question(self, idx: int, direction: int) -> None:
        """Đổi thứ tự câu ngay trên card kết quả, giống nút lên/xuống ở V4."""
        target = idx + direction
        if idx < 0 or idx >= len(self._generated_questions):
            return
        if target < 0 or target >= len(self._generated_questions):
            return
        self._generated_questions[idx], self._generated_questions[target] = (
            self._generated_questions[target],
            self._generated_questions[idx],
        )
        self._sync_preview_questions_to_exam()
        self._render_preview()
        self._sync_result_action_state()
        self._result_status.configure(
            text=f"✓ Đã chuyển câu {idx + 1} {'xuống' if direction > 0 else 'lên'} vị trí {target + 1}.",
            text_color="#10B981",
        )

    def _delete_preview_question(self, idx: int) -> None:
        """Xoá một câu khỏi đề hiện tại từ card xem chi tiết."""
        if idx < 0 or idx >= len(self._generated_questions):
            return
        question = self._generated_questions[idx]
        topic = str(getattr(question, "topic", "") or "").strip()
        detail = f"\nChủ đề: {topic}" if topic else ""
        if not messagebox.askyesno(
            "Xoá câu hỏi",
            f"Xoá Câu {idx + 1} khỏi đề hiện tại?{detail}\n\n"
            "Thao tác này chỉ xoá khỏi đề đang mở, không xoá câu đã lưu trong NHCH.",
            parent=self,
        ):
            return
        del self._generated_questions[idx]
        self._sync_preview_questions_to_exam()
        self._render_preview()
        self._sync_result_action_state()
        n = len(self._generated_questions)
        self._prog_bar.set(1.0 if n > 0 else 0.0)
        self._prog_lbl.configure(text=f"✓ Còn {n} câu" if n else "Đề hiện tại đã trống")
        self._result_status.configure(
            text=f"✓ Đã xoá Câu {idx + 1}. Còn {n} câu trong đề.",
            text_color="#10B981",
        )
        try:
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(), f"✓ Đã xoá Câu {idx + 1}", kind="info")
        except Exception:
            pass

    def _resolve_ai_call_factory(self):
        """Trả factory () -> ai_call cho dialog sửa (get_ai_call pattern)."""
        ai = self._resolve_ai_call()
        return (lambda: ai) if ai else None

    def _push_lms(self):
        try:
            from v5.toast import show_toast
            show_toast(
                self.winfo_toplevel(),
                "Bản Web/LMS đang tạm ẩn; hãy xuất Word hoặc lưu NHCH trước.",
                kind="info",
                duration=5,
            )
        except Exception:
            messagebox.showinfo(
                "Web/LMS đang ẩn",
                "Bản Web/LMS đang tạm ẩn; hãy xuất Word hoặc lưu NHCH trước.",
                parent=self,
            )
        return
        """Push đề hiện tại lên Web LMS qua FastAPI."""
        if not self._feature_allowed("tab_result"):
            return
        if not self._exam or not self._exam.questions:
            return
        from services import api_client
        from v5.toast import show_toast
        if not api_client.is_api_enabled():
            show_toast(self.winfo_toplevel(),
                        "Cấu hình MEA_API_URL ở tab 🌐 LMS trước",
                        kind="warn", duration=4); return
        if not api_client.is_logged_in():
            show_toast(self.winfo_toplevel(),
                        "Đăng nhập ở tab 🌐 LMS trước khi push",
                        kind="warn", duration=4); return

        _exam_title = (getattr(self._exam, "exam_title", None)
                        or getattr(self._exam, "title", "") or "Đề kiểm tra")
        if not messagebox.askyesno(
            "Xác nhận push",
            f"Push {len(self._exam.questions)} câu lên LMS?\n\n"
            f"Đề: {_exam_title}\n"
            f"Subject: {self._exam.subject} | Lớp: {self._exam.grade}",
            parent=self): return

        self._push_btn.configure(state="disabled", text="⏳ Đang push...")
        self._push_status.configure(text="⏳ Đang gọi API...",
                                       text_color="#3B82F6")
        status_throttle = UiThrottle(self, 120)

        def _set_push_status(text: str, color: str) -> None:
            status_throttle.schedule(
                self._push_status.configure, text=text, text_color=color)

        def _finish_push(res: dict) -> None:
            status_throttle.cancel()
            self._on_push_done(res)

        def _worker():
            try:
                # Convert ExamData → API payload (đọc exam_title + parse time)
                exam = self._exam
                import re as _re
                _title = (getattr(exam, "exam_title", None)
                           or getattr(exam, "title", "") or "Đề kiểm tra")
                _m = _re.search(r"\d+", str(getattr(exam, "time", "") or ""))
                _dur = int(_m.group(0)) if _m else 45
                exam_payload = {
                    "title": _title,
                    "subject": exam.subject or "Toán",
                    "grade": str(exam.grade or "12"),
                    "duration_min": _dur,
                }
                qs = []
                for i, q in enumerate(exam.questions, 1):
                    opts = q.options if q.qtype == "TN" else {}
                    ans = q.answer or ""
                    if q.qtype == "DS" and q.answers:
                        ans = ",".join(f"{k}={'Đ' if v else 'S'}"
                                         for k, v in q.answers.items())

                    # Gom các ảnh local của câu (multi-image support)
                    from v5.image_fields import normalize_image_field
                    q_images = normalize_image_field(getattr(q, "question_image", "") or [])
                    sol_images = normalize_image_field(getattr(q, "solution_image", "") or [])
                    opt_images = {k: normalize_image_field(v)
                                    for k, v in (getattr(q, "option_images", {}) or {}).items()}
                    item_images = {k: normalize_image_field(v)
                                     for k, v in (getattr(q, "item_images", {}) or {}).items()}

                    qs.append({
                        "question_id": getattr(q, "question_id", "")
                                          or f"V5-{id(q):x}-{i:03d}",
                        "subject": exam.subject or "Toán",
                        "grade":   str(exam.grade or "12"),
                        "topic":   q.topic or "",
                        "level":   q.level or "TH",
                        "qtype":   q.qtype,
                        "question": q.question or "",
                        "options": opts,
                        "answer":  ans,
                        "solution": q.solution or "",
                        "points":  float(getattr(q, "points", 1.0)),
                        # ── Images (sẽ upload Storage trước khi push) ──────
                        "question_images":  q_images,
                        "option_images":    opt_images,
                        "item_images":      item_images,
                        "solution_images":  sol_images,
                    })

                # ── Upload all local images → Supabase Storage → URLs ─────
                # Đếm tổng ảnh local cần upload
                n_local = 0
                for qd in qs:
                    n_local += len([p for p in qd.get("question_images", [])
                                     if not p.startswith("http")])
                    n_local += len([p for p in qd.get("solution_images", [])
                                     if not p.startswith("http")])
                    for v in qd.get("option_images", {}).values():
                        n_local += len([p for p in v if not p.startswith("http")])
                    for v in qd.get("item_images", {}).values():
                        n_local += len([p for p in v if not p.startswith("http")])

                if n_local > 0:
                    _set_push_status(f"⏳ Upload {n_local} ảnh...", "#A78BFA")
                    # Upload từng question (api_client.upload_question_images)
                    qs_with_urls = []
                    for idx, qd in enumerate(qs, 1):
                        upgraded = api_client.upload_question_images(
                            qd, folder=f"exam-{exam_payload.get('grade', '12')}")
                        qs_with_urls.append(upgraded)
                        _set_push_status(f"⏳ Upload ảnh {idx}/{len(qs)}...", "#A78BFA")
                    qs = qs_with_urls

                _set_push_status("⏳ Gọi sync_exam API...", "#3B82F6")
                res = api_client.sync_exam(exam_payload, qs, publish=True)
                self.after(0, lambda: _finish_push(res))
            except Exception as e:
                self.after(0, lambda err=str(e):
                             _finish_push({"ok": False, "error": err}))
        threading.Thread(target=_worker, daemon=True).start()

    def _on_push_done(self, res: dict):
        self._push_btn.configure(state="normal", text="🚀  Push lên LMS")
        if res.get("ok"):
            d = res.get("data", {})
            code = d.get("code", "?")
            self._push_status.configure(
                text=f"✓ Code: {code}  ({d.get('questions_added')} câu)",
                text_color="#10B981")
            messagebox.showinfo(
                "Push thành công",
                f"✅ Đã publish đề!\n\n"
                f"Mã đề: {code}\n"
                f"HS truy cập:\n"
                f"{__import__('services.api_client', fromlist=['api_url']).api_url().replace(':8000', ':3000')}/exam/{code}",
                parent=self)
        else:
            err = (res.get("error") or "?")[:200]
            self._push_status.configure(text=f"✘ {err[:50]}",
                                          text_color="#EF4444")
            messagebox.showerror("Push thất bại", err, parent=self)

    def _load_exam_from_file(self):
        """Nạp đề đã có vào preview: DOCX/PDF/TeX/TXT/HTML -> ExamData."""
        path = filedialog.askopenfilename(
            parent=self,
            title="Chọn file đề cần nạp",
            filetypes=[
                ("Đề thi hỗ trợ", "*.docx *.pdf *.tex *.txt *.html *.htm"),
                ("Word", "*.docx"),
                ("PDF", "*.pdf"),
                ("LaTeX", "*.tex"),
                ("Text", "*.txt"),
                ("HTML", "*.html *.htm"),
                ("Tất cả file", "*.*"),
            ],
        )
        if not path:
            return
        if self._exam and self._exam.questions:
            if not messagebox.askyesno(
                "Thay đề hiện tại?",
                "Đề đang mở sẽ được thay bằng đề nạp từ file.\n\n"
                "Bạn có muốn tiếp tục?",
                parent=self,
            ):
                return

        self._result_status.configure(text=f"⏳ Đang đọc {Path(path).name}...",
                                      text_color="#3B82F6")
        self._load_exam_btn.configure(state="disabled", text="⏳ Đang nạp...")

        def _worker():
            try:
                from core.exam_file_loader import load_exam_from_file
                result = load_exam_from_file(path)
                self.after(0, lambda: self._on_exam_file_loaded(path, result))
            except Exception as exc:
                self.after(0, lambda err=str(exc):
                           self._on_exam_file_error(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_exam_file_loaded(self, path: str, result: dict):
        self._load_exam_btn.configure(state="normal", text="📥  Nạp đề file")
        questions = list(result.get("questions") or [])
        tier = str(result.get("tier") or "none")
        raw_text = str(result.get("text") or "")
        error = str(result.get("error") or "")
        if questions:
            self._populate_exam_from_loaded(questions, path, tier)
            return
        if raw_text.strip():
            self._offer_ai_fallback_for_loaded_file(raw_text, path, error)
            return
        self._result_status.configure(text="✘ Không đọc được câu hỏi từ file.",
                                      text_color="#EF4444")
        messagebox.showerror(
            "Không nạp được đề",
            error or "File rỗng hoặc không có nội dung câu hỏi nhận diện được.",
            parent=self)

    def _on_exam_file_error(self, error: str):
        self._load_exam_btn.configure(state="normal", text="📥  Nạp đề file")
        self._result_status.configure(text=f"✘ Lỗi đọc file: {error[:100]}",
                                      text_color="#EF4444")
        messagebox.showerror("Lỗi đọc file", error[:300], parent=self)

    def _populate_exam_from_loaded(self, questions: list, src_path: str, tier: str):
        tier_label = {
            "exact": "khung ===CAU=== chuẩn",
            "natural": "nhận diện tự nhiên",
            "latex": "LaTeX cấu trúc",
            "mixed": "cấu trúc app + LaTeX ex_test",
            "ai": "AI chuẩn hoá cấu trúc",
        }.get(tier, tier or "parser")
        grade = self._grade_var.get() if hasattr(self, "_grade_var") else "12"
        exam = ExamData(
            exam_title=f"ĐỀ TẢI TỪ FILE - {Path(src_path).stem}",
            subject="Toán",
            grade=grade or "12",
            semester="",
            year="",
            time=f"{self._duration_var.get() or '90'} phút",
            questions=list(questions),
        )
        self._apply_default_exam_metadata(exam)
        self._exam = exam
        self._generated_questions = list(exam.questions or [])
        self._title_var.set(exam.exam_title[:80])
        self._publish_exam_change()
        self._render_preview()
        self._sync_result_action_state()
        self._prog_bar.set(1.0 if self._generated_questions else 0)
        self._prog_lbl.configure(text=f"✓ Nạp {len(self._generated_questions)} câu")
        self._result_status.configure(
            text=f"✓ Đã nạp {len(self._generated_questions)} câu từ {Path(src_path).name} ({tier_label}).",
            text_color="#10B981")
        try:
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(),
                       f"✓ Đã nạp {len(self._generated_questions)} câu từ file",
                       kind="success", duration=5)
        except Exception:
            pass

    def _offer_ai_fallback_for_loaded_file(self, text: str, src_path: str, err: str):
        ai_call = self._resolve_ai_call()
        if ai_call is None:
            self._result_status.configure(text="⚠ Parser cục bộ không nhận diện được câu hỏi.",
                                          text_color="#F59E0B")
            messagebox.showerror(
                "Không nhận diện được",
                f"File {Path(src_path).name} đã đọc được text nhưng parser cục bộ "
                "không tìm thấy câu hỏi hợp lệ.\n\n"
                f"Lý do: {(err or 'Không khớp cấu trúc câu hỏi chuẩn.')[:220]}\n\n"
                "Hãy chỉnh file theo dạng 'Câu 1:', A/B/C/D, 'Đáp án:' hoặc "
                "cấu hình AI để app chuẩn hoá tự động.",
                parent=self)
            return
        preview = " ".join(text.strip().split())[:320]
        if len(text.strip()) > 320:
            preview += "..."
        if not messagebox.askyesno(
            "Dùng AI chuẩn hoá file?",
            f"Parser cục bộ chưa nhận diện được câu hỏi trong {Path(src_path).name}.\n\n"
            "Bạn có muốn dùng AI provider đang cấu hình để chuyển text này về "
            "cấu trúc câu hỏi V5 không?\n\n"
            f"Xem trước: {preview}",
            parent=self,
        ):
            self._result_status.configure(text="Đã huỷ AI chuẩn hoá file.",
                                          text_color="gray")
            return

        self._load_exam_btn.configure(state="disabled", text="🤖 AI đang nạp...")
        self._result_status.configure(text="🤖 AI đang chuẩn hoá file đề...",
                                      text_color="#7C3AED")

        def _worker():
            try:
                from v5.convert_pipeline import build_text_normalize_prompt, parse_text_questions
                response = ai_call(build_text_normalize_prompt(text))
                questions = parse_text_questions(response)
                self.after(0, lambda: self._on_ai_exam_file_loaded(
                    questions, src_path, None))
            except Exception as exc:
                self.after(0, lambda err=str(exc): self._on_ai_exam_file_loaded(
                    [], src_path, err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_ai_exam_file_loaded(self, questions: list, src_path: str, error: str | None):
        self._load_exam_btn.configure(state="normal", text="📥  Nạp đề file")
        if error:
            self._result_status.configure(text=f"✘ AI chuẩn hoá lỗi: {error[:90]}",
                                          text_color="#EF4444")
            messagebox.showerror("AI chuẩn hoá lỗi", error[:300], parent=self)
            return
        if not questions:
            self._result_status.configure(text="⚠ AI không trả về câu hỏi hợp lệ.",
                                          text_color="#F59E0B")
            messagebox.showwarning(
                "AI không nhận diện được",
                "AI đã gọi thành công nhưng không trả về câu hỏi hợp lệ.",
                parent=self)
            return
        self._populate_exam_from_loaded(questions, src_path, "ai")

    def _export_word(self):
        if not self._feature_allowed("export_word"):
            return
        if not self._exam or not self._exam.questions:
            return
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".docx",
            filetypes=[("Word", "*.docx")],
            initialfile=f"{self._title_var.get() or 'De'}.docx")
        if not path:
            return
        try:
            from export.word_exporter import export_to_word
            output_path = Path(path)
            export_to_word(
                self._exam,
                path,
                include_solution=self._include_solutions_on_export(),
                math_mode=self._word_math_mode(),
                auto_convert_tables=self._word_auto_convert_tables(),
            )
            self._remember_export_path(output_path, auto=False)
            if self._open_after_export_enabled():
                self._open_export_file(output_path)
            messagebox.showinfo("Xuất xong",
                                  f"Đã lưu:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi xuất Word",
                                  str(e)[:300], parent=self)

    def _open_variant_dialog(self):
        """Tạo đề tương tự từ đề hiện tại: prompt thủ công, SymPy hoặc AI."""
        if not self._feature_allowed("multi_code"):
            return
        if not self._exam or not self._exam.questions:
            messagebox.showinfo(
                "Chưa có đề",
                "Hãy tạo hoặc nạp một đề trước khi sinh đề tương tự.",
                parent=self)
            return
        try:
            from v5.variant_dialog import VariantExamDialog
        except Exception as exc:
            messagebox.showerror("Lỗi mở dialog", str(exc)[:300], parent=self)
            return

        def _apply(new_exam, meta: dict):
            self._apply_default_exam_metadata(new_exam)
            self._exam = new_exam
            self._generated_questions = list(getattr(new_exam, "questions", []) or [])
            title = getattr(new_exam, "exam_title", "") or self._title_var.get()
            if title:
                self._title_var.set(str(title)[:80])
            self._publish_exam_change()
            self._render_preview()
            self._sync_result_action_state()
            replaced = int(meta.get("replaced", 0) or 0)
            kept = int(meta.get("kept", 0) or 0)
            mode = "AI" if meta.get("mode") == "ai" else "Python/SymPy"
            self._result_status.configure(
                text=f"✓ Đã nạp đề tương tự bằng {mode}: {replaced} câu thay số, {kept} câu giữ nguyên.",
                text_color="#10B981")
            try:
                from v5.toast import show_toast
                show_toast(
                    self.winfo_toplevel(),
                    f"✓ Đã nạp đề tương tự ({replaced} câu thay số)",
                    kind="success",
                    duration=5)
            except Exception:
                pass

        VariantExamDialog(
            self.winfo_toplevel(),
            self._exam,
            on_apply=_apply,
            get_ai_call=lambda: self._resolve_ai_call(),
        )

    def _export_multi_code(self):
        """Xuất nhiều mã đề bằng service V4 parity (shuffle + answer key + variant)."""
        if not self._feature_allowed("multi_code"):
            return
        if not self._exam or not self._exam.questions:
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("🔀  Xuất nhiều mã đề")
        dlg.geometry("620x620")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.bind("<Escape>", lambda _e: dlg.destroy())

        hdr = ctk.CTkFrame(dlg, fg_color=("#1F497D", "#0B1F35"),
                           corner_radius=0, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr,
            text="🔀  XUẤT NHIỀU MÃ ĐỀ",
            text_color="white",
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        ).pack(side="left", padx=16, pady=12)
        ctk.CTkLabel(
            hdr,
            text=f"{len(self._exam.questions)} câu từ đề hiện tại",
            text_color="#BFDBFE",
            font=("Segoe UI", 10),
        ).pack(side="right", padx=16, pady=12)

        body = ctk.CTkScrollableFrame(dlg, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=14)

        n_var = ctk.StringVar(value="4")
        shuffle_q_var = ctk.StringVar(value="1")
        shuffle_a_var = ctk.StringVar(value="1")
        include_sol_var = ctk.StringVar(value=("1" if self._include_solutions_on_export() else "0"))
        variant_mode_var = ctk.StringVar(value="none")

        card = self._multi_card(body, "1. Số lượng và cách trộn")
        n_row = ctk.CTkFrame(card, fg_color="transparent")
        n_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(n_row, text="Số mã đề:", width=110, anchor="w",
                     font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkOptionMenu(n_row, values=["2", "3", "4", "5", "6"],
                          variable=n_var, width=90).pack(side="left")
        ctk.CTkLabel(n_row, text="Tối đa A-F như V4", text_color="gray",
                     font=("Segoe UI", 10)).pack(side="left", padx=10)

        for text, var, note in (
            ("Trộn câu hỏi trong từng phần", shuffle_q_var,
             "Giữ thứ tự phần TN / Đúng-Sai / Trả lời ngắn / Tự luận, chỉ đảo câu bên trong từng phần."),
            ("Trộn đáp án A/B/C/D cho câu trắc nghiệm", shuffle_a_var,
             "Tự remap đáp án đúng sau khi đảo phương án."),
            ("Kèm lời giải trong từng file Word", include_sol_var,
             "Tắt mặc định như V4; app vẫn xuất file bảng đáp án riêng."),
        ):
            ctk.CTkCheckBox(
                card,
                text=text,
                variable=var,
                onvalue="1",
                offvalue="0",
                font=("Segoe UI", 11),
            ).pack(anchor="w", pady=(6, 0))
            ctk.CTkLabel(card, text=note, text_color="gray",
                         font=("Segoe UI", 9), wraplength=520,
                         justify="left").pack(anchor="w", padx=28)

        card2 = self._multi_card(body, "2. Đa dạng hoá số liệu")
        ctk.CTkLabel(
            card2,
            text="Chế độ này dùng cùng service export_multi_code của V4.",
            text_color="gray",
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", pady=(0, 6))
        for value, text, note in (
            ("none", "Không thay số", "Các mã dùng chung số liệu, chỉ trộn câu/phương án."),
            ("python", "Thay số bằng Python/SymPy", "Nhanh và chắc, nhưng chỉ hỗ trợ một số dạng toán an toàn."),
            ("ai", "Thay số bằng AI provider", "Đa dạng hơn, chậm hơn và cần API key đang cấu hình."),
        ):
            ctk.CTkRadioButton(
                card2,
                text=text,
                variable=variant_mode_var,
                value=value,
                font=("Segoe UI", 11),
            ).pack(anchor="w", pady=(7, 0))
            ctk.CTkLabel(card2, text=note, text_color="gray",
                         font=("Segoe UI", 9), wraplength=520,
                         justify="left").pack(anchor="w", padx=28)

        card3 = self._multi_card(body, "3. Prompt thủ công cho AI ngoài app")
        ctk.CTkLabel(
            card3,
            text="Giống V4: copy prompt, upload file Word gốc vào ChatGPT/Claude/Gemini web, rồi yêu cầu AI sinh đề khác số.",
            text_color="gray",
            font=("Segoe UI", 10),
            wraplength=520,
            justify="left",
        ).pack(fill="x", pady=(0, 8))
        prompt_row = ctk.CTkFrame(card3, fg_color="transparent")
        prompt_row.pack(fill="x")

        def _copy_manual_prompt():
            try:
                from services.ai_variant_generator import get_manual_variant_prompt
                prompt_text = get_manual_variant_prompt()
                dlg.clipboard_clear()
                dlg.clipboard_append(prompt_text)
                messagebox.showinfo(
                    "Đã copy prompt",
                    "Prompt đã được copy. Hãy xuất Word gốc, upload vào chatbot ngoài app rồi dán prompt.",
                    parent=dlg)
            except Exception as exc:
                messagebox.showerror("Lỗi copy prompt", str(exc)[:300], parent=dlg)

        def _preview_manual_prompt():
            try:
                from services.ai_variant_generator import get_manual_variant_prompt
                from v5.variant_dialog import PromptPreviewDialog
                PromptPreviewDialog(dlg, get_manual_variant_prompt())
            except Exception as exc:
                messagebox.showerror("Lỗi mở prompt", str(exc)[:300], parent=dlg)

        ctk.CTkButton(
            prompt_row,
            text="📋 Copy prompt",
            width=140,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=_copy_manual_prompt,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            prompt_row,
            text="✏️ Xem / sửa",
            width=130,
            command=_preview_manual_prompt,
        ).pack(side="left", padx=4)

        def _do():
            try:
                n_codes = int(n_var.get())
            except Exception:
                n_codes = 4
            options = {
                "n_codes": max(2, min(6, n_codes)),
                "shuffle_questions": shuffle_q_var.get() == "1",
                "shuffle_answers": shuffle_a_var.get() == "1",
                "include_solution": include_sol_var.get() == "1",
                "variant_mode": variant_mode_var.get() or "none",
            }
            dlg.destroy()
            self._do_export_multi(options)

        foot = ctk.CTkFrame(dlg, fg_color="transparent")
        foot.pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkButton(
            foot,
            text="✓ Chọn thư mục & Xuất",
            fg_color="#F59E0B",
            hover_color="#D97706",
            command=_do,
            width=180,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            foot,
            text="Hủy",
            fg_color="#6B7280",
            hover_color="#4B5563",
            command=dlg.destroy,
            width=90,
        ).pack(side="right")

    def _multi_card(self, parent, title: str) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(parent, fg_color=("#FFFFFF", "#1F2937"),
                             corner_radius=12, border_width=1,
                             border_color=("#E5E7EB", "#374151"))
        outer.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(inner, text=title, font=("Segoe UI", 13, "bold"),
                     anchor="w").pack(anchor="w", pady=(0, 8))
        return inner

    def _do_export_multi(self, options: dict):
        variant_mode = options.get("variant_mode", "none")
        ai_call = None
        if variant_mode == "ai":
            ai_call = self._resolve_ai_call()
            if ai_call is None:
                messagebox.showerror(
                    "Chưa cấu hình AI",
                    "Chế độ thay số bằng AI yêu cầu đã cấu hình API key/provider.",
                    parent=self)
                return
        elif variant_mode == "python":
            try:
                from services import similar_generator as _similar
                if getattr(_similar, "sp", None) is None:
                    raise RuntimeError("SymPy chưa khả dụng trong runtime này.")
            except Exception as exc:
                messagebox.showerror(
                    "Không dùng được Python/SymPy",
                    f"{str(exc)[:220]}\n\nHãy chọn 'Không thay số', 'AI provider' hoặc dùng prompt thủ công.",
                    parent=self)
                return

        folder = filedialog.askdirectory(parent=self,
                                         title="Chọn thư mục lưu các mã đề")
        if not folder:
            return

        self._multi_btn.configure(state="disabled", text="⏳ Đang xuất...")
        self._result_status.configure(text="⏳ Đang xuất nhiều mã đề...",
                                      text_color="#3B82F6")

        def _progress(stage: str, done: int, total: int):
            label = "Đang thay số" if stage == "variant" else "Đang xuất Word"
            self.after(0, lambda: self._result_status.configure(
                text=f"⏳ {label}: {done}/{total}",
                text_color="#3B82F6"))

        def _worker():
            try:
                from export.word_exporter import export_multi_code
                files = export_multi_code(
                    self._exam,
                    folder,
                    n_codes=options["n_codes"],
                    include_solution=options["include_solution"],
                    shuffle_questions=options["shuffle_questions"],
                    shuffle_answers=options["shuffle_answers"],
                    variant_mode=variant_mode,
                    ai_call=ai_call,
                    progress_cb=_progress,
                    auto_convert_tables=self._word_auto_convert_tables(),
                )
                self.after(0, lambda: self._on_multi_export_done(files, folder, variant_mode))
            except Exception as exc:
                self.after(0, lambda err=str(exc): self._on_multi_export_error(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_multi_export_done(self, files: list[str], folder: str, variant_mode: str):
        self._multi_btn.configure(state="normal", text="🔀  Trộn mã (A-F)")
        docx_count = sum(1 for f in files if str(f).lower().endswith(".docx"))
        txt_count = sum(1 for f in files if str(f).lower().endswith(".txt"))
        if files:
            self._last_export_path = Path(files[0])
            self._folder_btn.configure(state="normal")
        mode_text = {
            "none": "không thay số",
            "python": "thay số Python/SymPy",
            "ai": "thay số AI",
        }.get(variant_mode, variant_mode)
        self._result_status.configure(
            text=f"✓ Đã xuất {docx_count} mã đề + {txt_count} bảng đáp án ({mode_text}): {folder}",
            text_color="#10B981")
        try:
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(),
                       f"✓ Đã xuất {docx_count} mã đề",
                       kind="success", duration=6,
                       action_label="Thư mục", action_cb=self._open_export_folder)
        except Exception:
            pass
        messagebox.showinfo(
            "Xuất nhiều mã đề xong",
            f"Đã tạo {docx_count} file Word và {txt_count} bảng đáp án.\n\n"
            f"Thư mục:\n{folder}",
            parent=self)

    def _on_multi_export_error(self, error: str):
        self._multi_btn.configure(state="normal", text="🔀  Trộn mã (A-F)")
        self._result_status.configure(
            text=f"✘ Xuất nhiều mã đề lỗi: {error[:120]}",
            text_color="#EF4444")
        messagebox.showerror("Lỗi xuất nhiều mã đề", error[:300], parent=self)
