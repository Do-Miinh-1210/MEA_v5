"""
ui/tab_shuffle.py — Tab Trộn Đề Thi Hoán Vị Mã Đề (Tích hợp trực tiếp vào app gốc MatrixExam AI).
Thay thế hoàn toàn cửa sổ popup cũ và loại bỏ phần quét máy OMR.
Nâng cấp các tính năng chuyên nghiệp theo chuẩn Bộ GD&ĐT 2025, McMIX & SmartTest:
- 2 Nguồn nạp đề: File Word (.docx) bên ngoài HOẶC Nạp trực tiếp đề thi đang soạn trong app.
- 3 Chế độ trộn linh hoạt: Cả câu & đáp án / Chỉ đảo câu / Chỉ đảo đáp án.
- Smart Fixed Options: Tự động phát hiện và ghim phương án phụ thuộc ("Tất cả...", "Cả A và B...") ở vị trí D.
- Pin Questions: Cố định vị trí các câu hỏi chỉ định không bị xáo trộn.
- Xuất file Word từng mã đề, File Word GỘP All-in-One, Bảng đáp án Word và Bảng đáp án + Ma trận hoán vị Excel (.xlsx).
"""
from __future__ import annotations
import os
import re
import time
from pathlib import Path
from typing import Callable, Optional, List, Dict, Set
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from omr_exam.models import ExamSection, ExamQuestion, OptionItem, ShuffledExamCode
from omr_exam.docx_parser import parse_exam_docx
from omr_exam.exam_shuffler import shuffle_exam
from omr_exam.docx_exporter import export_shuffled_exams_to_docx
from omr_exam.excel_exporter import export_exam_keys_and_matrix_to_excel


class LoadedExamItem:
    """Đại diện cho 1 bộ đề thi đã nạp (từ file Word hoặc từ App)."""
    def __init__(self, name: str, file_path: Optional[str], sections: List[ExamSection]):
        self.name = name
        self.file_path = file_path
        self.sections = sections
        self.shuffled_exams: List[ShuffledExamCode] = []
        self.keys_by_code: Dict[str, Dict[int, str]] = {}
        self.question_map_by_code: Dict[str, Dict[int, int]] = {}
        self.option_map_by_code: Dict[str, Dict[int, Dict[str, str]]] = {}
        self.is_ai_variant: bool = False

    @property
    def total_questions(self) -> int:
        return sum(len(s.questions) for s in self.sections)

    @property
    def tn_count(self) -> int:
        return sum(len([q for q in s.questions if q.qtype == "TN"]) for s in self.sections)

    @property
    def tl_count(self) -> int:
        return self.total_questions - self.tn_count


class TabShuffle(ttk.Frame):
    """Giao diện Quản lý Trộn đề & Hoán vị mã đề tích hợp trong MainWindow."""

    def __init__(
        self,
        parent,
        get_exam_data: Optional[Callable[[], Optional[object]]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
        get_ai_call: Optional[Callable] = None,
    ):
        super().__init__(parent)
        self._get_exam_data = get_exam_data
        self._on_status_change = on_status_change
        self._get_ai_call = get_ai_call

        self._loaded_exams: List[LoadedExamItem] = []
        self._active_exam_idx: int = -1
        self._last_exported_folder: Optional[str] = None

        # Bộ đếm giờ cho tiến trình tạo đề / đổi số bằng AI
        self._ai_timer_start: float = 0.0
        self._ai_timer_running: bool = False
        self._ai_timer_after_id: Optional[str] = None
        self._current_progress_desc: str = ""

        self._build_ui()

    @property
    def _current_exam(self) -> Optional[LoadedExamItem]:
        if 0 <= self._active_exam_idx < len(self._loaded_exams):
            return self._loaded_exams[self._active_exam_idx]
        return None

    def _ensure_current_exam(self, default_name: str = "Đề thi") -> LoadedExamItem:
        ex = self._current_exam
        if ex is None:
            ex = LoadedExamItem(name=default_name, file_path=None, sections=[])
            self._loaded_exams.append(ex)
            self._active_exam_idx = len(self._loaded_exams) - 1
        return ex

    @property
    def _parsed_sections(self) -> List[ExamSection]:
        ex = self._current_exam
        return ex.sections if ex else []

    @_parsed_sections.setter
    def _parsed_sections(self, val: List[ExamSection]):
        ex = self._ensure_current_exam()
        ex.sections = val

    @property
    def _shuffled_exams(self) -> List[ShuffledExamCode]:
        ex = self._current_exam
        return ex.shuffled_exams if ex else []

    @_shuffled_exams.setter
    def _shuffled_exams(self, val: List[ShuffledExamCode]):
        ex = self._ensure_current_exam()
        ex.shuffled_exams = val

    @property
    def _source_docx_path(self) -> Optional[str]:
        ex = self._current_exam
        return ex.file_path if ex else None

    @_source_docx_path.setter
    def _source_docx_path(self, val: Optional[str]):
        ex = self._ensure_current_exam()
        ex.file_path = val

    @property
    def _keys_by_code(self) -> Dict[str, Dict[int, str]]:
        ex = self._current_exam
        return ex.keys_by_code if ex else {}

    @_keys_by_code.setter
    def _keys_by_code(self, val: Dict[str, Dict[int, str]]):
        ex = self._ensure_current_exam()
        ex.keys_by_code = val

    @property
    def _question_map_by_code(self) -> Dict[str, Dict[int, int]]:
        ex = self._current_exam
        return ex.question_map_by_code if ex else {}

    @_question_map_by_code.setter
    def _question_map_by_code(self, val: Dict[str, Dict[int, int]]):
        ex = self._ensure_current_exam()
        ex.question_map_by_code = val

    @property
    def _option_map_by_code(self) -> Dict[str, Dict[int, Dict[str, str]]]:
        ex = self._current_exam
        return ex.option_map_by_code if ex else {}

    @_option_map_by_code.setter
    def _option_map_by_code(self, val: Dict[str, Dict[int, Dict[str, str]]]):
        ex = self._ensure_current_exam()
        ex.option_map_by_code = val

    @property
    def _is_ai_variant(self) -> bool:
        ex = self._current_exam
        return ex.is_ai_variant if ex else False

    @_is_ai_variant.setter
    def _is_ai_variant(self, val: bool):
        ex = self._ensure_current_exam()
        ex.is_ai_variant = val

    def _set_status(self, msg: str):
        if self._on_status_change:
            try:
                self._on_status_change(msg)
            except Exception:
                pass

    def _start_ai_timer(self, initial_text: str = "") -> None:
        """Bắt đầu đồng hồ đếm thời gian thực hiện (live stopwatch)."""
        self._ai_timer_start = time.time()
        self._ai_timer_running = True
        self._current_progress_desc = initial_text
        if self._ai_timer_after_id:
            try:
                self.after_cancel(self._ai_timer_after_id)
            except Exception:
                pass
            self._ai_timer_after_id = None
        self._tick_ai_timer()

    def _stop_ai_timer(self) -> float:
        """Dừng đồng hồ và trả về tổng số giây đã trôi qua."""
        self._ai_timer_running = False
        if self._ai_timer_after_id:
            try:
                self.after_cancel(self._ai_timer_after_id)
            except Exception:
                pass
            self._ai_timer_after_id = None
        if self._ai_timer_start > 0:
            return max(0.0, time.time() - self._ai_timer_start)
        return 0.0

    def _tick_ai_timer(self) -> None:
        """Cập nhật bộ đếm giờ mỗi giây một lần trên UI."""
        if not self._ai_timer_running:
            return
        elapsed = int(time.time() - self._ai_timer_start)
        mins = elapsed // 60
        secs = elapsed % 60
        time_str = f"{mins:02d}:{secs:02d}"
        desc = self._current_progress_desc or "Đang xử lý..."
        try:
            self._lbl_shuffle_status.configure(
                text=f"⏱️ {time_str} | {desc}",
                fg="#7C3AED"
            )
        except Exception:
            pass
        self._ai_timer_after_id = self.after(1000, self._tick_ai_timer)

    def _update_ai_status(self, desc: str) -> None:
        """Cập nhật trạng thái kèm thời gian đếm giây hiện tại."""
        self._current_progress_desc = desc
        if self._ai_timer_running:
            elapsed = int(time.time() - self._ai_timer_start)
            mins = elapsed // 60
            secs = elapsed % 60
            time_str = f"{mins:02d}:{secs:02d}"
            try:
                self._lbl_shuffle_status.configure(
                    text=f"⏱️ {time_str} | {desc}",
                    fg="#7C3AED"
                )
            except Exception:
                pass
        else:
            try:
                self._lbl_shuffle_status.configure(text=desc)
            except Exception:
                pass

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format số giây thành chuỗi thời gian thân thiện (vd: '2 phút 15 giây' hoặc '3.4 giây')."""
        if seconds < 60:
            return f"{seconds:.1f} giây"
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        if secs == 0:
            return f"{mins} phút"
        return f"{mins} phút {secs:02d} giây"

    def _build_ui(self):
        # Container có thanh cuộn mượt mà
        canvas = tk.Canvas(self, bg="#F8FAFC", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#F8FAFC")

        self._canvas = canvas
        self._scrollable_frame = scrollable_frame

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        cw = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_canvas_configure(e):
            canvas.itemconfig(cw, width=e.width)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        pad_f = tk.Frame(scrollable_frame, bg="#F8FAFC", padx=16, pady=12)
        pad_f.pack(fill="both", expand=True)
        self._pad_f = pad_f

        def _on_wheel(e):
            delta = getattr(e, "delta", 0)
            if delta:
                n = int(-3 * (delta / 120.0))
                if n == 0:
                    n = -1 if delta > 0 else 1
            else:
                num = getattr(e, "num", 0)
                n = -3 if num == 4 else (3 if num == 5 else 0)
            if n:
                canvas.yview_scroll(n, "units")
            return "break"

        self._on_canvas_wheel = _on_wheel
        canvas.bind("<MouseWheel>", _on_wheel)
        scrollable_frame.bind("<MouseWheel>", _on_wheel)
        pad_f.bind("<MouseWheel>", _on_wheel)
        canvas.bind("<Button-4>", _on_wheel)
        canvas.bind("<Button-5>", _on_wheel)
        scrollable_frame.bind("<Button-4>", _on_wheel)
        scrollable_frame.bind("<Button-5>", _on_wheel)
        pad_f.bind("<Button-4>", _on_wheel)
        pad_f.bind("<Button-5>", _on_wheel)
        self.bind("<MouseWheel>", _on_wheel)
        self.bind("<Button-4>", _on_wheel)
        self.bind("<Button-5>", _on_wheel)

        # ── HEADER CARD ──────────────────────────────────────────────────────
        hdr_frame = tk.Frame(pad_f, bg="#FFFFFF", relief="solid", bd=1)
        hdr_frame.pack(fill="x", pady=(0, 10))
        tk.Frame(hdr_frame, bg="#2563EB", height=4).pack(fill="x")
        
        hdr_content = tk.Frame(hdr_frame, bg="#FFFFFF", padx=16, pady=10)
        hdr_content.pack(fill="x")
        
        tk.Label(
            hdr_content,
            text="🎲  TRỘN ĐỀ THI TRẮC NGHIỆM & TỰ LUẬN HOÁN VỊ MÃ ĐỀ",
            font=("Segoe UI", 14, "bold"),
            fg="#1E293B", bg="#FFFFFF"
        ).pack(anchor="w")
        
        tk.Label(
            hdr_content,
            text="Hỗ trợ nạp từ file Word (.docx) bên ngoài HOẶC nạp trực tiếp đề thi đang soạn trong ứng dụng. "
                 "Bảo toàn 100% MathType, hình ảnh, bảng biểu.",
            font=("Segoe UI", 9),
            fg="#64748B", bg="#FFFFFF"
        ).pack(anchor="w", pady=(2, 0))

        # ── CARD 1: NGUỒN ĐỀ THI (HỖ TRỢ NẠP & TRỘN NHIỀU BỘ ĐỀ) ──────────────
        c1 = tk.LabelFrame(
            pad_f, text=" 📁 1. Nguồn Đề Thi (Chọn File Word HOẶC Nạp Từ Đề Đang Soạn — Hỗ Trợ Nhiều Bộ Đề) ",
            font=("Segoe UI", 10, "bold"), fg="#1E3A8A", bg="#FFFFFF", padx=14, pady=10, relief="solid", bd=1
        )
        c1.pack(fill="x", pady=6)

        # Hàng 1: Nút tác vụ chọn & xóa file
        r1 = tk.Frame(c1, bg="#FFFFFF")
        r1.pack(fill="x", pady=(0, 6))

        btn_choose = tk.Button(
            r1, text="📂 Chọn File Word (.docx)...",
            bg="#2563EB", fg="white", activebackground="#1D4ED8", activeforeground="white",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", padx=12, pady=6, bd=0,
            command=self._on_choose_docx
        )
        btn_choose.pack(side="left", padx=(0, 8))

        btn_load_current = tk.Button(
            r1, text="📥 Nạp Đề Đang Soạn Trong App",
            bg="#0D9488", fg="white", activebackground="#0F766E", activeforeground="white",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", padx=12, pady=6, bd=0,
            command=self._on_load_from_app_exam
        )
        btn_load_current.pack(side="left", padx=(0, 8))

        btn_remove = tk.Button(
            r1, text="❌ Xóa Đề Đang Chọn",
            bg="#EF4444", fg="white", activebackground="#DC2626", activeforeground="white",
            font=("Segoe UI", 9), relief="flat", cursor="hand2", padx=10, pady=6, bd=0,
            command=self._on_remove_selected_exam
        )
        btn_remove.pack(side="left", padx=(0, 8))

        btn_clear = tk.Button(
            r1, text="🗑️ Xóa Tất Cả / Làm Mới",
            bg="#64748B", fg="white", activebackground="#475569", activeforeground="white",
            font=("Segoe UI", 9), relief="flat", cursor="hand2", padx=10, pady=6, bd=0,
            command=self._on_clear_all
        )
        btn_clear.pack(side="left", padx=(0, 10))

        self._lbl_exam_count = tk.Label(
            r1, text="(Chưa có đề nào)", font=("Segoe UI", 9, "italic"),
            fg="#64748B", bg="#FFFFFF", anchor="w"
        )
        self._lbl_exam_count.pack(side="left", fill="x", expand=True)

        # Hàng 2: Bộ chọn đề thi đang làm việc
        r1_sel = tk.Frame(c1, bg="#F1F5F9", relief="solid", bd=1, padx=8, pady=5)
        r1_sel.pack(fill="x", pady=(2, 6))

        tk.Label(
            r1_sel, text="🎯 Đang làm việc với đề:",
            font=("Segoe UI", 9, "bold"), fg="#1E3A8A", bg="#F1F5F9"
        ).pack(side="left", padx=(0, 8))

        self._cb_exam_selector = ttk.Combobox(r1_sel, state="readonly", width=42)
        self._cb_exam_selector.pack(side="left", padx=(0, 10))
        self._cb_exam_selector.bind("<<ComboboxSelected>>", self._on_select_active_exam)

        self._lbl_source_info = tk.Label(
            r1_sel, text="Chưa nạp đề thi nào", font=("Segoe UI", 9, "italic"),
            fg="#64748B", bg="#F1F5F9", anchor="w"
        )
        self._lbl_source_info.pack(side="left", fill="x", expand=True)

        # Status chi tiết
        self._lbl_parse_detail = tk.Label(
            c1, text="", font=("Segoe UI", 9), fg="#10B981", bg="#FFFFFF", anchor="w"
        )
        self._lbl_parse_detail.pack(fill="x", pady=(2, 6))

        # Preview câu hỏi
        tk.Label(
            c1, text="Xem trước cấu trúc câu hỏi đã nhận diện:",
            font=("Segoe UI", 8, "bold"), fg="#475569", bg="#FFFFFF"
        ).pack(anchor="w")

        preview_frame = tk.Frame(c1, bg="#F1F5F9", relief="solid", bd=1)
        preview_frame.pack(fill="both", expand=True, pady=(2, 4))

        self._txt_preview = tk.Text(
            preview_frame, height=6, font=("Segoe UI", 9), bg="#F8FAFC", fg="#1E293B",
            relief="flat", wrap="word"
        )
        prev_sb = ttk.Scrollbar(preview_frame, orient="vertical", command=self._txt_preview.yview)
        self._txt_preview.configure(yscrollcommand=prev_sb.set)
        prev_sb.pack(side="right", fill="y")
        self._txt_preview.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        self._txt_preview.insert("1.0", "Hãy chọn file Word đề thi hoặc bấm 'Nạp Đề Đang Soạn Trong App' để bắt đầu.")
        self._txt_preview.configure(state="disabled")

        # ── CARD 2: CẤU HÌNH & THIẾT LẬP TRỘN ĐỀ ──────────────────────────────
        c2 = tk.LabelFrame(
            pad_f, text=" 🔀 2. Thiết Lập & Tùy Chọn Trộn Đề Thông Minh ",
            font=("Segoe UI", 10, "bold"), fg="#1E3A8A", bg="#FFFFFF", padx=14, pady=10, relief="solid", bd=1
        )
        c2.pack(fill="x", pady=6)

        # Hàng 0: Phạm vi trộn đề (Trộn tất cả các bộ đề hoặc chỉ đề đang chọn)
        r2_scope = tk.Frame(c2, bg="#EFF6FF", relief="solid", bd=1, padx=10, pady=6)
        r2_scope.pack(fill="x", pady=(0, 6))

        tk.Label(
            r2_scope, text="📦 Phạm vi trộn đề:",
            font=("Segoe UI", 9, "bold"), fg="#1E40AF", bg="#EFF6FF"
        ).pack(side="left", padx=(0, 10))

        self._var_batch_scope = tk.StringVar(value="all")
        rb_scope_all = ttk.Radiobutton(
            r2_scope,
            text="Trộn TẤT CẢ các bộ đề đã nạp (Tự động chia thành từng bộ mã riêng biệt)",
            variable=self._var_batch_scope,
            value="all"
        )
        rb_scope_all.pack(side="left", padx=(0, 14))

        rb_scope_curr = ttk.Radiobutton(
            r2_scope,
            text="Chỉ trộn bộ đề đang chọn",
            variable=self._var_batch_scope,
            value="current"
        )
        rb_scope_curr.pack(side="left")

        # Hàng 1: Số lượng & Mã đề
        r2_1 = tk.Frame(c2, bg="#FFFFFF")
        r2_1.pack(fill="x", pady=4)

        tk.Label(r2_1, text="Số lượng mã đề:", font=("Segoe UI", 9), bg="#FFFFFF").pack(side="left", padx=(0, 6))
        self._spin_codes = ttk.Combobox(r2_1, values=["2", "4", "6", "8", "12", "16", "24"], width=5, state="readonly")
        self._spin_codes.set("4")
        self._spin_codes.pack(side="left", padx=(0, 16))

        tk.Label(r2_1, text="Mã bắt đầu:", font=("Segoe UI", 9), bg="#FFFFFF").pack(side="left", padx=(0, 6))
        self._entry_start_code = ttk.Entry(r2_1, width=8)
        self._entry_start_code.insert(0, "101")
        self._entry_start_code.pack(side="left", padx=(0, 16))

        tk.Label(r2_1, text="Hoặc danh sách mã đề tùy ý:", font=("Segoe UI", 9), bg="#FFFFFF").pack(side="left", padx=(0, 6))
        self._entry_custom_codes = ttk.Entry(r2_1, width=28)
        self._entry_custom_codes.pack(side="left", padx=(0, 10))
        tk.Label(r2_1, text="(VD: 101, 102, 103, 104)", font=("Segoe UI", 8), fg="#94A3B8", bg="#FFFFFF").pack(side="left")

        # Hàng 2: Chế độ trộn
        r2_2 = tk.Frame(c2, bg="#FFFFFF")
        r2_2.pack(fill="x", pady=6)

        tk.Label(r2_2, text="Chế độ xáo trộn:", font=("Segoe UI", 9, "bold"), bg="#FFFFFF").pack(side="left", padx=(0, 8))
        self._var_shuffle_mode = tk.StringVar(value="both")

        rb1 = ttk.Radiobutton(r2_2, text="Trộn cả câu hỏi & đáp án A/B/C/D (Mặc định)", variable=self._var_shuffle_mode, value="both")
        rb1.pack(side="left", padx=(0, 12))

        rb2 = ttk.Radiobutton(r2_2, text="Chỉ trộn câu hỏi (giữ nguyên A/B/C/D)", variable=self._var_shuffle_mode, value="questions_only")
        rb2.pack(side="left", padx=(0, 12))

        rb3 = ttk.Radiobutton(r2_2, text="Chỉ trộn đáp án (giữ nguyên thứ tự câu)", variable=self._var_shuffle_mode, value="options_only")
        rb3.pack(side="left", padx=(0, 10))

        # Hàng 3: Tính năng nâng cao (Ghim đáp án phụ thuộc + Ghim câu hỏi)
        r2_3 = tk.Frame(c2, bg="#FFFFFF")
        r2_3.pack(fill="x", pady=4)

        self._var_auto_pin = tk.BooleanVar(value=True)
        cb_pin = ttk.Checkbutton(
            r2_3,
            text="🔒 Tự động ghim phương án phụ thuộc ('Tất cả đáp án trên', 'Cả A và B...', 'Không có...') cố định ở cuối (D)",
            variable=self._var_auto_pin
        )
        cb_pin.pack(side="left", padx=(0, 16))

        self._var_merged_docx = tk.BooleanVar(value=True)
        cb_merge = ttk.Checkbutton(
            r2_3,
            text="📑 Tự động xuất thêm 1 file Word GỘP chứa tất cả các mã đề (thuận tiện in photocopy)",
            variable=self._var_merged_docx
        )
        cb_merge.pack(side="left")

        # Hàng 4: Ghim câu hỏi chỉ định
        r2_4 = tk.Frame(c2, bg="#FFFFFF")
        r2_4.pack(fill="x", pady=4)

        tk.Label(r2_4, text="📌 Cố định câu hỏi không đảo (nhập số câu):", font=("Segoe UI", 9), bg="#FFFFFF").pack(side="left", padx=(0, 6))
        self._entry_pinned_qs = ttk.Entry(r2_4, width=22)
        self._entry_pinned_qs.pack(side="left", padx=(0, 8))
        tk.Label(r2_4, text="(Ví dụ: 1, 2, 5 hoặc để trống nếu muốn đảo toàn bộ)", font=("Segoe UI", 8), fg="#94A3B8", bg="#FFFFFF").pack(side="left")

        # Hàng 5: Tuỳ chọn Trộn đề đổi số liệu từ AI
        r2_ai = tk.Frame(c2, bg="#F0FDF4", relief="solid", bd=1, padx=10, pady=8)
        r2_ai.pack(fill="x", pady=(6, 4))

        self._var_ai_variant = tk.BooleanVar(value=False)
        cb_ai = ttk.Checkbutton(
            r2_ai,
            text="🤖  Trộn đề đổi số liệu bằng AI (Tạo đề tương tự — AI chỉ thay số, giữ nguyên dạng toán & độ khó)",
            variable=self._var_ai_variant,
            command=self._on_toggle_ai_variant,
        )
        cb_ai.pack(anchor="w")

        self._lbl_ai_hint = tk.Label(
            r2_ai,
            text="   💡 Công nghệ AI: Đọc công thức MathType/OMML -> AI đổi số & tính lại đáp án -> Xuất Word chuẩn (không tự đổi sang Equation).",
            font=("Segoe UI", 8, "italic"), fg="#047857", bg="#F0FDF4"
        )
        self._lbl_ai_hint.pack(anchor="w", pady=(2, 0))

        # Nút thực hiện trộn đề
        r2_btn = tk.Frame(c2, bg="#FFFFFF")
        r2_btn.pack(fill="x", pady=(8, 2))

        self._btn_do_shuffle = tk.Button(
            r2_btn, text="⚡ Bắt Đầu Trộn Đề & Sinh Mã Đề",
            bg="#10B981", fg="white", activebackground="#059669", activeforeground="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", padx=16, pady=8, bd=0,
            command=self._on_do_shuffle, state="disabled"
        )
        self._btn_do_shuffle.pack(side="left", padx=(0, 12))

        self._lbl_shuffle_status = tk.Label(
            r2_btn, text="", font=("Segoe UI", 9, "bold"), fg="#10B981", bg="#FFFFFF"
        )
        self._lbl_shuffle_status.pack(side="left")

        # ── CARD 3: KẾT QUẢ ĐÁP ÁN & XUẤT BẢN PHẨM ────────────────────────────
        c3 = tk.LabelFrame(
            pad_f, text=" 📊 3. Kết Quả Đáp Án & Xuất Bản Phẩm (Word & Excel) ",
            font=("Segoe UI", 10, "bold"), fg="#1E3A8A", bg="#FFFFFF", padx=14, pady=10, relief="solid", bd=1
        )
        c3.pack(fill="both", expand=True, pady=6)

        # Hàng chọn bộ đề xem kết quả
        r3_sel = tk.Frame(c3, bg="#FFFFFF")
        r3_sel.pack(fill="x", pady=(0, 6))

        tk.Label(
            r3_sel, text="👀 Xem trước kết quả của bộ đề:",
            font=("Segoe UI", 9, "bold"), fg="#1E3A8A", bg="#FFFFFF"
        ).pack(side="left", padx=(0, 8))

        self._cb_result_exam_selector = ttk.Combobox(r3_sel, state="readonly", width=42)
        self._cb_result_exam_selector.pack(side="left", padx=(0, 10))
        self._cb_result_exam_selector.bind("<<ComboboxSelected>>", self._on_select_result_exam)

        self._lbl_result_exam_info = tk.Label(
            r3_sel, text="", font=("Segoe UI", 9, "italic"), fg="#64748B", bg="#FFFFFF"
        )
        self._lbl_result_exam_info.pack(side="left", fill="x", expand=True)

        # Hàng nút xuất file
        r3_btns = tk.Frame(c3, bg="#FFFFFF")
        r3_btns.pack(fill="x", pady=(0, 8))

        self._btn_export_all = tk.Button(
            r3_btns, text="📥 Xuất Toàn Bộ File Word (.docx)...",
            bg="#2563EB", fg="white", activebackground="#1D4ED8", activeforeground="white",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", padx=12, pady=6, bd=0,
            command=self._on_export_docx_files, state="disabled"
        )
        self._btn_export_all.pack(side="left", padx=(0, 8))

        self._btn_export_excel = tk.Button(
            r3_btns, text="📊 Xuất Đáp Án & Phiếu Soi Câu (.xlsx)...",
            bg="#059669", fg="white", activebackground="#047857", activeforeground="white",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", padx=12, pady=6, bd=0,
            command=self._on_export_excel_file, state="disabled"
        )
        self._btn_export_excel.pack(side="left", padx=(0, 8))

        self._btn_open_folder = tk.Button(
            r3_btns, text="📂 Mở Thư Mục Kết Quả",
            bg="#475569", fg="white", activebackground="#334155", activeforeground="white",
            font=("Segoe UI", 9), relief="flat", cursor="hand2", padx=10, pady=6, bd=0,
            command=self._on_open_last_folder, state="disabled"
        )
        self._btn_open_folder.pack(side="left", padx=(0, 10))

        self._lbl_export_result = tk.Label(
            r3_btns, text="", font=("Segoe UI", 9), fg="#10B981", bg="#FFFFFF"
        )
        self._lbl_export_result.pack(side="left", fill="x", expand=True)

        # Tabs xem trước: Tab Bảng đáp án & Tab Phiếu soi câu
        nb_res = ttk.Notebook(c3)
        nb_res.pack(fill="both", expand=True, pady=(4, 0))

        # Sub-tab 1: Bảng đáp án
        f_tab_keys = ttk.Frame(nb_res)
        nb_res.add(f_tab_keys, text="📋 Bảng Tổng Hợp Đáp Án")
        self._txt_keys = tk.Text(
            f_tab_keys, height=9, font=("Consolas", 10), bg="#F8FAFC", fg="#0F172A",
            relief="flat", wrap="none"
        )
        sb_keys_y = ttk.Scrollbar(f_tab_keys, orient="vertical", command=self._txt_keys.yview)
        sb_keys_x = ttk.Scrollbar(f_tab_keys, orient="horizontal", command=self._txt_keys.xview)
        self._txt_keys.configure(yscrollcommand=sb_keys_y.set, xscrollcommand=sb_keys_x.set)
        sb_keys_y.pack(side="right", fill="y")
        sb_keys_x.pack(side="bottom", fill="x")
        self._txt_keys.pack(side="left", fill="both", expand=True)
        self._txt_keys.insert("1.0", "Bảng đáp án các mã đề sẽ hiển thị tại đây sau khi bạn bấm 'Bắt Đầu Trộn Đề'.")
        self._txt_keys.configure(state="disabled")

        # Sub-tab 2: Phiếu soi câu (Hoán vị)
        f_tab_map = ttk.Frame(nb_res)
        nb_res.add(f_tab_map, text="🔍 Phiếu Soi Câu (Ma Trận Hoán Vị)")
        self._txt_map = tk.Text(
            f_tab_map, height=9, font=("Consolas", 10), bg="#F8FAFC", fg="#0F172A",
            relief="flat", wrap="none"
        )
        sb_map_y = ttk.Scrollbar(f_tab_map, orient="vertical", command=self._txt_map.yview)
        sb_map_x = ttk.Scrollbar(f_tab_map, orient="horizontal", command=self._txt_map.xview)
        self._txt_map.configure(yscrollcommand=sb_map_y.set, xscrollcommand=sb_map_x.set)
        sb_map_y.pack(side="right", fill="y")
        sb_map_x.pack(side="bottom", fill="x")
        self._txt_map.pack(side="left", fill="both", expand=True)
        self._txt_map.insert("1.0", "Bảng tra cứu đối chiếu câu hỏi mới với câu gốc sẽ hiển thị tại đây.")
        self._txt_map.configure(state="disabled")

        # Hỗ trợ cuộn chuột thông minh trên các widget Text (tự động nổi bọt lên trang chính khi đã ở đỉnh/đáy)
        def _bind_smart_wheel(txt_widget):
            def _txt_wheel(e):
                delta = getattr(e, "delta", 0)
                notch = (float(delta) / 120.0) if delta else (1.0 if getattr(e, "num", 0) == 4 else -1.0)
                try:
                    first, last = txt_widget.yview()
                    if first <= 0.001 and last >= 0.999:
                        return _on_wheel(e)
                    if notch > 0 and first <= 0.001:
                        return _on_wheel(e)
                    if notch < 0 and last >= 0.999:
                        return _on_wheel(e)
                    n = int(-2 * notch)
                    if n == 0:
                        n = -1 if notch > 0 else 1
                    txt_widget.yview_scroll(n, "units")
                    return "break"
                except Exception:
                    return None
            txt_widget.bind("<MouseWheel>", _txt_wheel)
            txt_widget.bind("<Button-4>", _txt_wheel)
            txt_widget.bind("<Button-5>", _txt_wheel)

        _bind_smart_wheel(self._txt_preview)
        _bind_smart_wheel(self._txt_keys)
        _bind_smart_wheel(self._txt_map)

    # ── XỬ LÝ NẠP ĐỀ & QUẢN LÝ DANH SÁCH BỘ ĐỀ ───────────────────────────────

    def check_auto_load_exam(self):
        """Tự động kiểm tra và hỏi nạp nếu trong app có exam_data mà tab chưa có dữ liệu."""
        if not self._loaded_exams and self._get_exam_data:
            exam_data = self._get_exam_data()
            if exam_data and getattr(exam_data, "questions", None):
                self._on_load_from_app_exam(silent=True)

    def _on_choose_docx(self):
        """Chọn 1 hoặc nhiều file Word (.docx) bên ngoài để nạp vào danh sách trộn."""
        files = filedialog.askopenfilenames(
            title="Chọn một hoặc nhiều file đề thi Word (.docx)",
            filetypes=[("Word Document", "*.docx")]
        )
        if not files:
            return

        added_items = []
        errors = []
        first_added_idx = len(self._loaded_exams)

        for fn in files:
            base_name = os.path.basename(fn)
            # Kiểm tra xem file đã được nạp chưa
            if any(item.file_path == fn for item in self._loaded_exams):
                continue
            try:
                sections = parse_exam_docx(fn)
                if not sections:
                    errors.append(f"{base_name}: Không tìm thấy câu hỏi hợp lệ.")
                    continue
                item = LoadedExamItem(name=base_name, file_path=fn, sections=sections)
                self._loaded_exams.append(item)
                added_items.append(item)
            except Exception as e:
                errors.append(f"{base_name}: {e}")

        if errors:
            messagebox.showwarning("Cảnh Báo Đọc File", "Một số file không thể đọc:\n" + "\n".join(errors))

        if added_items:
            if self._active_exam_idx < 0:
                self._active_exam_idx = 0
            else:
                self._active_exam_idx = first_added_idx
            self._update_exam_list_ui()
            self._set_status(f"✓ Đã nạp thành công {len(added_items)} đề thi vào danh sách.")

    def _on_load_from_app_exam(self, silent: bool = False):
        """Nạp trực tiếp từ đề thi đang mở/soạn trong ứng dụng MEA."""
        if not self._get_exam_data:
            if not silent:
                messagebox.showwarning("Thông báo", "Không tìm thấy dữ liệu đề thi trong app.")
            return

        exam_data = self._get_exam_data()
        if not exam_data or not getattr(exam_data, "questions", None):
            if not silent:
                messagebox.showinfo(
                    "Chưa có đề thi",
                    "Hiện tại chưa có câu hỏi nào trong đề thi đang soạn.\n"
                    "Bạn hãy tạo câu hỏi ở Tab Cài đặt & Câu hỏi trước hoặc chọn file Word (.docx) bên ngoài."
                )
            return

        title = getattr(exam_data, "exam_title", "") or "Đề thi hiện tại trong MEA"

        # Chuyển đổi questions của exam_data thành ExamSection / ExamQuestion
        tn_questions: List[ExamQuestion] = []
        tl_questions: List[ExamQuestion] = []

        for i, q in enumerate(exam_data.questions, 1):
            qtype = getattr(q, "qtype", "TN")
            q_content = getattr(q, "question", "") or ""
            correct = (getattr(q, "answer", "") or "").strip().upper()

            if qtype in ("TN", "MCQ", "SINGLE", "MULTIPLE"):
                options = []
                q_opts = getattr(q, "options", {}) or {}
                for k in ["A", "B", "C", "D"]:
                    txt = str(q_opts.get(k, "") or "")
                    options.append(OptionItem(
                        label=k,
                        text=txt,
                        is_correct=(k == correct)
                    ))
                tn_questions.append(ExamQuestion(
                    index=i,
                    section="Phần I: Trắc nghiệm",
                    qtype="TN",
                    content=q_content,
                    options=options,
                    correct_label=correct,
                ))
            else:
                pts = getattr(q, "points", 1.0) or 1.0
                tl_questions.append(ExamQuestion(
                    index=i,
                    section="Phần II: Tự luận",
                    qtype="TL",
                    content=q_content,
                    tl_min_lines=max(3, int(pts * 3)),
                ))

        sections: List[ExamSection] = []
        if tn_questions:
            sections.append(ExamSection(title="Phần I: Câu hỏi trắc nghiệm nhiều phương án lựa chọn", questions=tn_questions))
        if tl_questions:
            sections.append(ExamSection(title="Phần II: Câu hỏi tự luận", questions=tl_questions))

        # Kiểm tra xem đã có đề từ app trong danh sách chưa
        existing = next((item for item in self._loaded_exams if item.file_path is None), None)
        if existing:
            existing.name = f"📌 {title}"
            existing.sections = sections
            existing.shuffled_exams = []
            self._active_exam_idx = self._loaded_exams.index(existing)
        else:
            new_item = LoadedExamItem(name=f"📌 {title}", file_path=None, sections=sections)
            self._loaded_exams.append(new_item)
            self._active_exam_idx = len(self._loaded_exams) - 1

        self._update_exam_list_ui()
        if not silent:
            self._set_status("✓ Đã nạp thành công đề thi từ ứng dụng vào module Trộn đề.")

    def _on_remove_selected_exam(self):
        """Xóa đề thi đang chọn khỏi danh sách nạp."""
        if not self._loaded_exams or self._active_exam_idx < 0:
            messagebox.showinfo("Thông báo", "Chưa có đề thi nào trong danh sách để xóa.")
            return

        cur = self._current_exam
        cur_name = cur.name if cur else "đề này"
        if not messagebox.askyesno("Xác Nhận Xóa Đề", f"Bạn có chắc muốn xóa '{cur_name}' khỏi danh sách?"):
            return

        self._loaded_exams.pop(self._active_exam_idx)
        if not self._loaded_exams:
            self._on_clear_all(silent=True)
            self._set_status(f"✓ Đã xóa '{cur_name}'. Danh sách hiện đang trống.")
            return

        if self._active_exam_idx >= len(self._loaded_exams):
            self._active_exam_idx = len(self._loaded_exams) - 1

        self._update_exam_list_ui()
        self._set_status(f"✓ Đã xóa '{cur_name}'. Hiện còn {len(self._loaded_exams)} bộ đề.")

    def _on_clear_all(self, silent: bool = False):
        """Xóa toàn bộ danh sách đề thi và làm mới giao diện về trạng thái ban đầu."""
        if not silent and self._loaded_exams:
            if not messagebox.askyesno("Xác Nhận Làm Mới", "Bạn có chắc muốn xóa TẤT CẢ các bộ đề đã nạp và làm mới giao diện?"):
                return

        self._loaded_exams.clear()
        self._active_exam_idx = -1
        self._last_exported_folder = None

        # Reset Card 1 UI
        self._cb_exam_selector.configure(values=[])
        self._cb_exam_selector.set("")
        self._lbl_exam_count.configure(text="(Chưa có đề nào)")
        self._lbl_source_info.configure(text="Chưa nạp đề thi nào", fg="#64748B", font=("Segoe UI", 9, "italic"))
        self._lbl_parse_detail.configure(text="")

        self._txt_preview.configure(state="normal")
        self._txt_preview.delete("1.0", "end")
        self._txt_preview.insert("1.0", "Hãy chọn file Word đề thi hoặc bấm 'Nạp Đề Đang Soạn Trong App' để bắt đầu.")
        self._txt_preview.configure(state="disabled")

        # Reset Card 2
        self._stop_ai_timer()
        self._btn_do_shuffle.configure(state="disabled")
        self._lbl_shuffle_status.configure(text="")

        # Reset Card 3
        self._cb_result_exam_selector.configure(values=[])
        self._cb_result_exam_selector.set("")
        self._lbl_result_exam_info.configure(text="")
        self._btn_export_all.configure(state="disabled")
        self._btn_export_excel.configure(state="disabled")
        self._btn_open_folder.configure(state="disabled")
        self._lbl_export_result.configure(text="")

        self._txt_keys.configure(state="normal")
        self._txt_keys.delete("1.0", "end")
        self._txt_keys.insert("1.0", "Bảng đáp án các mã đề sẽ hiển thị tại đây sau khi bạn bấm 'Bắt Đầu Trộn Đề'.")
        self._txt_keys.configure(state="disabled")

        self._txt_map.configure(state="normal")
        self._txt_map.delete("1.0", "end")
        self._txt_map.insert("1.0", "Bảng tra cứu đối chiếu câu hỏi mới với câu gốc sẽ hiển thị tại đây.")
        self._txt_map.configure(state="disabled")

        if not silent:
            self._set_status("✓ Đã xóa toàn bộ đề và làm mới giao diện.")

    def _update_exam_list_ui(self):
        """Đồng bộ Combobox chọn đề và cập nhật preview cho đề đang chọn."""
        if not self._loaded_exams:
            self._on_clear_all(silent=True)
            return

        if self._active_exam_idx < 0 or self._active_exam_idx >= len(self._loaded_exams):
            self._active_exam_idx = 0

        total_exams = len(self._loaded_exams)
        values = []
        for i, item in enumerate(self._loaded_exams, 1):
            q_info = f"{item.total_questions} câu ({item.tn_count} TN, {item.tl_count} TL)"
            values.append(f"[{i}/{total_exams}] {item.name} — {q_info}")

        self._cb_exam_selector.configure(values=values)
        self._cb_exam_selector.current(self._active_exam_idx)
        self._lbl_exam_count.configure(
            text=f"(Đang có {total_exams} bộ đề)",
            fg="#2563EB" if total_exams > 1 else "#64748B",
            font=("Segoe UI", 9, "bold") if total_exams > 1 else ("Segoe UI", 9)
        )

        cur = self._current_exam
        if cur:
            if cur.file_path:
                self._lbl_source_info.configure(
                    text=f"📄 {os.path.basename(cur.file_path)}",
                    fg="#2563EB", font=("Segoe UI", 9, "bold")
                )
            else:
                self._lbl_source_info.configure(
                    text=f"{cur.name}",
                    fg="#0D9488", font=("Segoe UI", 9, "bold")
                )
            self._update_parsed_preview()

        self._btn_do_shuffle.configure(state="normal")
        self._update_result_selector_ui()

    def _on_select_active_exam(self, event=None):
        """Xử lý khi người dùng chọn một đề khác trong combobox Card 1."""
        idx = self._cb_exam_selector.current()
        if 0 <= idx < len(self._loaded_exams):
            self._active_exam_idx = idx
            cur = self._current_exam
            if cur:
                if cur.file_path:
                    self._lbl_source_info.configure(
                        text=f"📄 {os.path.basename(cur.file_path)}",
                        fg="#2563EB", font=("Segoe UI", 9, "bold")
                    )
                else:
                    self._lbl_source_info.configure(
                        text=f"{cur.name}",
                        fg="#0D9488", font=("Segoe UI", 9, "bold")
                    )
                self._update_parsed_preview()
                if cur.shuffled_exams:
                    self._refresh_results_display(target_item=cur)

    def _update_parsed_preview(self):
        """Cập nhật chi tiết nhận diện và khung xem trước câu hỏi của đề đang chọn."""
        cur = self._current_exam
        if not cur or not cur.sections:
            self._lbl_parse_detail.configure(text="")
            self._txt_preview.configure(state="normal")
            self._txt_preview.delete("1.0", "end")
            self._txt_preview.insert("1.0", "Chưa có câu hỏi nào.")
            self._txt_preview.configure(state="disabled")
            return

        total_q = cur.total_questions
        tn_q = cur.tn_count
        tl_q = cur.tl_count
        with_ans = sum(len([q for q in s.questions if q.correct_label]) for s in cur.sections)

        self._lbl_parse_detail.configure(
            text=f"✓ Đã nhận diện ({cur.name}): {len(cur.sections)} phần | {total_q} câu hỏi "
                 f"({tn_q} trắc nghiệm, {tl_q} tự luận) | {with_ans}/{tn_q} câu có sẵn đáp án đúng",
            fg="#10B981"
        )

        self._txt_preview.configure(state="normal")
        self._txt_preview.delete("1.0", "end")
        for s in cur.sections:
            self._txt_preview.insert("end", f"=== {s.title} ({len(s.questions)} câu) ===\n")
            for q in s.questions[:6]:
                opts_str = " | ".join([f"{o.label}. {o.text}" for o in q.options])
                corr_str = f" [Đ/A: {q.correct_label}]" if q.correct_label else ""
                self._txt_preview.insert("end", f"Câu {q.index} ({q.qtype}): {q.content[:70]}... {corr_str}\n  {opts_str}\n\n")
        if total_q > 6:
            self._txt_preview.insert("end", f"... và {total_q - 6} câu hỏi khác tiếp theo.\n")
        self._txt_preview.configure(state="disabled")

        self._btn_do_shuffle.configure(state="normal")

    # ── XỬ LÝ TRỘN ĐỀ ────────────────────────────────────────────────────────

    def _parse_pinned_indices(self) -> Set[int]:
        """Bóc tách danh sách số câu ghim từ ô nhập."""
        raw = self._entry_pinned_qs.get().strip()
        if not raw:
            return set()
        pinned = set()
        parts = re.split(r"[,;\s]+", raw)
        for p in parts:
            if not p:
                continue
            if "-" in p:
                sub = p.split("-")
                if len(sub) == 2 and sub[0].isdigit() and sub[1].isdigit():
                    start, end = int(sub[0]), int(sub[1])
                    for n in range(min(start, end), max(start, end) + 1):
                        pinned.add(n)
            elif p.isdigit():
                pinned.add(int(p))
        return pinned

    def _parse_target_codes(self) -> List[str]:
        """Lấy danh sách mã đề từ form (custom hoặc tự sinh)."""
        raw_custom = self._entry_custom_codes.get().strip()
        if raw_custom:
            codes = [c.strip() for c in re.split(r"[,;\s]+", raw_custom) if c.strip()]
            if codes:
                return codes

        try:
            num = int(self._spin_codes.get())
        except Exception:
            num = 4
        try:
            start = int(self._entry_start_code.get())
        except Exception:
            start = 101

        return [str(start + i) for i in range(num)]

    def _on_toggle_ai_variant(self):
        """Thay đổi nút và giao diện khi bật/tắt chế độ đổi số AI."""
        if self._var_ai_variant.get():
            self._btn_do_shuffle.configure(
                text="🤖 Bắt Đầu Trộn Đề & Đổi Số Liệu AI",
                bg="#7C3AED", activebackground="#6D28D9"
            )
        else:
            self._btn_do_shuffle.configure(
                text="⚡ Bắt Đầu Trộn Đề & Sinh Mã Đề",
                bg="#10B981", activebackground="#059669"
            )

    def _on_do_shuffle(self):
        """Thực hiện xáo trộn đề thi (hỗ trợ trộn hàng loạt tất cả bộ đề hoặc chỉ đề đang chọn)."""
        if not self._loaded_exams:
            messagebox.showwarning("Cảnh báo", "Hãy chọn file đề thi hoặc nạp đề trước.")
            return

        if self._var_ai_variant.get():
            self._do_ai_variant_shuffle()
            return

        codes = self._parse_target_codes()
        shuffle_mode = self._var_shuffle_mode.get()
        auto_pin = self._var_auto_pin.get()
        pinned_qs = self._parse_pinned_indices()

        batch_scope = self._var_batch_scope.get()
        exams_to_shuffle = self._loaded_exams if (batch_scope == "all" and len(self._loaded_exams) > 1) else [self._current_exam]
        exams_to_shuffle = [e for e in exams_to_shuffle if e is not None and e.sections]

        if not exams_to_shuffle:
            messagebox.showwarning("Cảnh báo", "Không có bộ đề hợp lệ nào để trộn.")
            return

        t0 = time.perf_counter()
        try:
            from omr_exam.docx_shuffler_xml import preview_shuffled_keys

            for ex_item in exams_to_shuffle:
                ex_item.is_ai_variant = False
                ex_item.shuffled_exams = shuffle_exam(
                    ex_item.sections,
                    custom_codes=codes,
                    shuffle_mode=shuffle_mode,
                    auto_pin_dependent_options=auto_pin,
                    pinned_question_indices=pinned_qs,
                )

                # Nếu có file Word gốc OpenXML, tính trước đáp án chính xác theo OpenXML
                if ex_item.file_path and os.path.exists(ex_item.file_path):
                    xml_keys, xml_map, xml_opts = preview_shuffled_keys(
                        ex_item.file_path,
                        custom_codes=codes,
                        shuffle_mode=shuffle_mode,
                        auto_pin_dependent_options=auto_pin,
                        pinned_question_indices=pinned_qs,
                    )
                    for ex in ex_item.shuffled_exams:
                        if ex.code in xml_keys:
                            ex.answer_key = xml_keys[ex.code]
                        if ex.code in xml_map:
                            ex.question_map = xml_map[ex.code]
                        if ex.code in xml_opts:
                            ex.option_map = xml_opts[ex.code]

                ex_item.keys_by_code = {ex.code: ex.answer_key for ex in ex_item.shuffled_exams}
                ex_item.question_map_by_code = {ex.code: ex.question_map for ex in ex_item.shuffled_exams}
                ex_item.option_map_by_code = {ex.code: getattr(ex, "option_map", {}) for ex in ex_item.shuffled_exams}

            self._update_result_selector_ui()
            self._refresh_results_display()

            self._btn_export_all.configure(state="normal")
            self._btn_export_excel.configure(state="normal")

            elapsed_sec = time.perf_counter() - t0
            time_str = f"{elapsed_sec:.2f}s"

            if len(exams_to_shuffle) > 1:
                status_text = f"✓ Đã trộn thành công {len(exams_to_shuffle)} bộ đề, mỗi bộ gồm {len(codes)} mã ({', '.join(codes)}) trong ⏱️ {time_str}!"
            else:
                status_text = f"✓ Đã trộn thành công {len(codes)} mã đề: {', '.join(codes)} trong ⏱️ {time_str}!"

            self._lbl_shuffle_status.configure(text=status_text, fg="#10B981")
            self._set_status(status_text)

            messagebox.showinfo(
                "Trộn Thành Công",
                f"{status_text}\n\n"
                f"⏱️ Thời gian thực hiện: {time_str}\n"
                f"• Chế độ: {shuffle_mode}\n"
                f"• Ghim phương án phụ thuộc: {'Bật' if auto_pin else 'Tắt'}\n"
                f"• Câu cố định: {len(pinned_qs)} câu\n\n"
                "Bạn có thể xem trước bảng đáp án và bấm 'Xuất Toàn Bộ File Word' hoặc 'Xuất Excel'."
            )
        except Exception as e:
            messagebox.showerror("Lỗi Trộn Đề", f"Quá trình trộn gặp lỗi:\n{e}")

    def _do_ai_variant_shuffle(self):
        """Thực hiện trộn đề và đổi số liệu bằng AI cho các mã đề (hỗ trợ trộn hàng loạt)."""
        if not self._get_ai_call:
            messagebox.showerror(
                "Chưa Có Dịch Vụ AI",
                "Không tìm thấy cấu hình AI. Vui lòng cấu hình API Key tại Tab Cài đặt đề."
            )
            return

        try:
            ai_call = self._get_ai_call()
        except Exception as exc:
            messagebox.showerror(
                "Lỗi Kết Nối AI",
                f"Không thể khởi tạo dịch vụ AI:\n{exc}\n\n"
                "Vui lòng kiểm tra lại API Key ở Tab Cài đặt đề."
            )
            return

        batch_scope = self._var_batch_scope.get()
        exams_to_shuffle = self._loaded_exams if (batch_scope == "all" and len(self._loaded_exams) > 1) else [self._current_exam]
        exams_to_shuffle = [e for e in exams_to_shuffle if e is not None and e.sections]

        if not exams_to_shuffle:
            messagebox.showwarning("Cảnh báo", "Không có bộ đề nào để đổi số bằng AI.")
            return

        codes = self._parse_target_codes()
        shuffle_mode = self._var_shuffle_mode.get()
        auto_pin = self._var_auto_pin.get()
        pinned_qs = self._parse_pinned_indices()

        total_qs = sum(sum(len(s.questions) for s in item.sections) for item in exams_to_shuffle)
        msg_confirm = (
            f"Bắt đầu trộn đề và đổi số liệu bằng AI:\n\n"
            f"• Số lượng bộ đề: {len(exams_to_shuffle)} bộ đề\n"
            f"• Số lượng mã mỗi bộ: {len(codes)} ({', '.join(codes)})\n"
            f"• Tổng số câu cần xử lý: {total_qs} câu\n"
            f"• Mục tiêu: Giữ nguyên dạng toán & độ khó, AI chỉ thay số & tính lại đáp án\n"
            f"• Định dạng công thức: Giữ nguyên văn bản chuẩn $..$, tương thích MathType (không chuyển sang Equation)\n\n"
            "Quá trình gọi AI sẽ xử lý từng câu hỏi. Bạn có muốn bắt đầu không?"
        )
        if not messagebox.askyesno("Xác Nhận Đổi Số Bằng AI", msg_confirm):
            return

        self._btn_do_shuffle.configure(state="disabled")
        self._btn_export_all.configure(state="disabled")
        self._btn_export_excel.configure(state="disabled")
        self._start_ai_timer("Đang kết nối AI và bắt đầu đổi số liệu...")
        self.update_idletasks()

        import threading

        def _worker():
            try:
                from services.ai_variant_generator import generate_ai_variants_for_sections
                from omr_exam.exam_shuffler import shuffle_exam

                for item_idx, item in enumerate(exams_to_shuffle, 1):
                    shuffled_codes_list = []
                    for code_idx, code in enumerate(codes, 1):
                        def _progress(cur, tot, desc, it_idx=item_idx, c_idx=code_idx, c_code=code, it_name=item.name):
                            p_desc = f"⏳ [Bộ {it_idx}/{len(exams_to_shuffle)}: {it_name[:15]}] [Mã {c_code} ({c_idx}/{len(codes)})] {desc} ({cur}/{tot})"
                            self.after(0, lambda t=p_desc: self._update_ai_status(t))

                        var_sections, n_rep, n_kept = generate_ai_variants_for_sections(
                            sections=item.sections,
                            ai_call=ai_call,
                            progress_cb=_progress,
                            max_retry=2,
                        )

                        single_code_res = shuffle_exam(
                            var_sections,
                            custom_codes=[code],
                            shuffle_mode=shuffle_mode,
                            auto_pin_dependent_options=auto_pin,
                            pinned_question_indices=pinned_qs,
                        )
                        if single_code_res:
                            shuffled_codes_list.append(single_code_res[0])

                    item.shuffled_exams = shuffled_codes_list
                    item.keys_by_code = {ex.code: ex.answer_key for ex in item.shuffled_exams}
                    item.question_map_by_code = {ex.code: ex.question_map for ex in item.shuffled_exams}
                    item.option_map_by_code = {ex.code: getattr(ex, "option_map", {}) for ex in item.shuffled_exams}
                    item.is_ai_variant = True

                def _on_done():
                    elapsed_sec = self._stop_ai_timer()
                    dur_str = self._format_duration(elapsed_sec)
                    mins = int(elapsed_sec) // 60
                    secs = int(elapsed_sec) % 60
                    clock_str = f"{mins:02d}:{secs:02d}"

                    self._update_result_selector_ui()
                    self._refresh_results_display()
                    self._btn_do_shuffle.configure(state="normal")
                    self._btn_export_all.configure(state="normal")
                    self._btn_export_excel.configure(state="normal")

                    if len(exams_to_shuffle) > 1:
                        status_ok = f"✓ AI đã đổi số & sinh thành công cho {len(exams_to_shuffle)} bộ đề ({', '.join(codes)}) trong ⏱️ {clock_str}!"
                    else:
                        status_ok = f"✓ AI đã đổi số & sinh thành công {len(codes)} mã đề ({', '.join(codes)}) trong ⏱️ {clock_str}!"

                    self._lbl_shuffle_status.configure(text=status_ok, fg="#10B981")
                    self._set_status(status_ok)
                    messagebox.showinfo(
                        "AI Đổi Số Liệu Hoàn Tất",
                        f"{status_ok}\n\n"
                        f"⏱️ Tổng thời gian thực hiện: {dur_str}\n"
                        f"• Toàn bộ công thức toán đã được bảo toàn ở dạng MathType/OMML.\n"
                        f"• Đáp án các mã đề đã được tính toán lại chính xác.\n\n"
                        "Bấm 'Xuất Toàn Bộ File Word' để lưu các bộ đề .docx kèm file gộp và Excel."
                    )

                self.after(0, _on_done)
            except Exception as e:
                def _on_err(err_msg):
                    self._stop_ai_timer()
                    self._btn_do_shuffle.configure(state="normal")
                    self._lbl_shuffle_status.configure(text=f"❌ Lỗi: {err_msg}", fg="#EF4444")
                    messagebox.showerror("Lỗi Quá Trình AI", f"Gặp lỗi khi đổi số bằng AI:\n{err_msg}")
                self.after(0, lambda: _on_err(str(e)))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    # ── KẾT QUẢ & HIỂN THỊ ĐÁP ÁN ─────────────────────────────────────────────

    def _update_result_selector_ui(self):
        """Đồng bộ danh sách bộ đề đã trộn vào Combobox xem kết quả ở Card 3."""
        shuffled_items = [item for item in self._loaded_exams if item.shuffled_exams]
        if not shuffled_items:
            self._cb_result_exam_selector.configure(values=[])
            self._cb_result_exam_selector.set("")
            self._lbl_result_exam_info.configure(text="")
            return

        vals = []
        for i, itm in enumerate(shuffled_items, 1):
            c_list = ", ".join(sorted(itm.keys_by_code.keys()))
            vals.append(f"[{i}/{len(shuffled_items)}] {itm.name} ({len(itm.shuffled_exams)} mã: {c_list})")

        self._cb_result_exam_selector.configure(values=vals)
        cur = self._current_exam
        if cur and cur in shuffled_items:
            sel_idx = shuffled_items.index(cur)
        else:
            sel_idx = 0
        self._cb_result_exam_selector.current(sel_idx)
        self._lbl_result_exam_info.configure(text=f"Đang xem: {shuffled_items[sel_idx].name}")

    def _on_select_result_exam(self, event=None):
        """Xử lý khi người dùng đổi bộ đề cần xem đáp án/ma trận ở Card 3."""
        shuffled_items = [item for item in self._loaded_exams if item.shuffled_exams]
        idx = self._cb_result_exam_selector.current()
        if 0 <= idx < len(shuffled_items):
            item = shuffled_items[idx]
            self._lbl_result_exam_info.configure(text=f"Đang xem: {item.name}")
            self._refresh_results_display(target_item=item)

    def _refresh_results_display(self, target_item: Optional[LoadedExamItem] = None):
        """Cập nhật dữ liệu vào Textbox Bảng đáp án và Phiếu soi câu."""
        item = target_item or self._current_exam
        if not item or not item.shuffled_exams:
            shuffled_items = [it for it in self._loaded_exams if it.shuffled_exams]
            if shuffled_items:
                item = shuffled_items[0]
            else:
                return

        shuffled_exams = item.shuffled_exams

        # 1. Bảng Đáp Án
        self._txt_keys.configure(state="normal")
        self._txt_keys.delete("1.0", "end")

        header = f"{'Câu':<6}" + "".join([f"{'Mã ' + ex.code:<12}" for ex in shuffled_exams]) + "\n"
        sep = "-" * len(header) + "\n"
        self._txt_keys.insert("end", f"=== BẢNG TỔNG HỢP ĐÁP ÁN: {item.name.upper()} ===\n\n")
        self._txt_keys.insert("end", header)
        self._txt_keys.insert("end", sep)

        max_q = max((max(ex.answer_key.keys(), default=0) for ex in shuffled_exams), default=0)
        for q in range(1, max_q + 1):
            row = f"{q:<6}"
            for ex in shuffled_exams:
                row += f"{ex.answer_key.get(q, '-'):<12}"
            self._txt_keys.insert("end", row + "\n")
        self._txt_keys.configure(state="disabled")

        # 2. Phiếu Soi Câu (Hoán vị)
        self._txt_map.configure(state="normal")
        self._txt_map.delete("1.0", "end")
        self._txt_map.insert("end", f"=== MA TRẬN HOÁN VỊ CÂU HỎI (PHIẾU SOI CÂU): {item.name.upper()} ===\n\n")

        for ex in shuffled_exams:
            self._txt_map.insert("end", f"▶ MÃ ĐỀ: {ex.code}\n")
            q_map = ex.question_map
            line_parts = []
            for q_new in sorted(q_map.keys()):
                q_orig = q_map[q_new]
                ans = ex.answer_key.get(q_new, "-")
                line_parts.append(f"C{q_new}→[Gốc {q_orig}: {ans}]")
                if len(line_parts) == 6:
                    self._txt_map.insert("end", "  " + " | ".join(line_parts) + "\n")
                    line_parts = []
            if line_parts:
                self._txt_map.insert("end", "  " + " | ".join(line_parts) + "\n")
            self._txt_map.insert("end", "\n")

        self._txt_map.configure(state="disabled")

    # ── XỬ LÝ XUẤT FILE ──────────────────────────────────────────────────────

    def _on_export_docx_files(self):
        """Xuất danh sách mã đề ra thư mục (hỗ trợ xuất nhiều bộ đề vào các thư mục riêng biệt)."""
        shuffled_items = [item for item in self._loaded_exams if item.shuffled_exams]
        if not shuffled_items:
            messagebox.showwarning("Cảnh báo", "Hãy thực hiện trộn đề ở Bước 2 trước khi xuất.")
            return

        folder = filedialog.askdirectory(title="Chọn thư mục lưu trữ các file đề thi đã trộn")
        if not folder:
            return

        try:
            shuffle_mode = self._var_shuffle_mode.get()
            auto_pin = self._var_auto_pin.get()
            pinned_qs = self._parse_pinned_indices()
            export_merged = self._var_merged_docx.get()

            total_files = 0
            datasets_for_master_excel = []

            if len(shuffled_items) == 1:
                # Chỉ có 1 bộ đề: Xuất trực tiếp ra thư mục người dùng chọn
                item = shuffled_items[0]
                src_path = item.file_path if (item.file_path and os.path.exists(item.file_path)) else None

                files = export_shuffled_exams_to_docx(
                    shuffled_exams=item.shuffled_exams,
                    output_dir=folder,
                    source_docx_path=src_path,
                    shuffle_mode=shuffle_mode,
                    auto_pin_dependent_options=auto_pin,
                    pinned_question_indices=pinned_qs,
                    export_merged_docx=export_merged,
                    is_ai_variant=item.is_ai_variant,
                )
                total_files = len(files)
                msg_done = f"Đã xuất thành công {total_files} file (gồm các mã đề, file gộp và bảng đáp án) vào thư mục:\n{folder}"
            else:
                # Nhiều bộ đề: Tự động chia thành các thư mục con: Bộ 01 - <Tên đề>, Bộ 02 - <Tên đề>...
                created_subdirs = []
                for idx, item in enumerate(shuffled_items, 1):
                    clean_name = re.sub(r'[\\/*?:"<>|]', '_', item.name).replace(".docx", "").strip()
                    sub_dir = os.path.join(folder, f"Bộ {idx:02d} - {clean_name}")
                    os.makedirs(sub_dir, exist_ok=True)
                    created_subdirs.append(sub_dir)

                    src_path = item.file_path if (item.file_path and os.path.exists(item.file_path)) else None
                    sub_files = export_shuffled_exams_to_docx(
                        shuffled_exams=item.shuffled_exams,
                        output_dir=sub_dir,
                        source_docx_path=src_path,
                        shuffle_mode=shuffle_mode,
                        auto_pin_dependent_options=auto_pin,
                        pinned_question_indices=pinned_qs,
                        export_merged_docx=export_merged,
                        is_ai_variant=item.is_ai_variant,
                    )
                    total_files += len(sub_files)

                    datasets_for_master_excel.append({
                        "name": clean_name,
                        "keys_by_code": item.keys_by_code,
                        "question_map_by_code": item.question_map_by_code,
                        "option_map_by_code": item.option_map_by_code,
                    })

                # Xuất thêm file Excel tổng hợp tất cả bộ đề tại thư mục gốc
                from omr_exam.excel_exporter import export_consolidated_master_excel
                master_excel_path = os.path.join(folder, "Tong_Hop_Dap_An_Va_Ma_Tran_Tat_Ca_Bo_De.xlsx")
                export_consolidated_master_excel(master_excel_path, datasets_for_master_excel)
                total_files += 1

                msg_done = (
                    f"Đã xuất thành công {len(shuffled_items)} bộ đề ({total_files} files) vào các thư mục riêng biệt:\n"
                    f"• Mỗi bộ đề được chia vào 1 thư mục riêng (gồm các mã đề .docx, file gộp & Excel đáp án).\n"
                    f"• Đã tạo file Excel tổng hợp: Tong_Hop_Dap_An_Va_Ma_Tran_Tat_Ca_Bo_De.xlsx tại thư mục gốc.\n\n"
                    f"Thư mục: {folder}"
                )

            self._last_exported_folder = folder
            self._btn_open_folder.configure(state="normal")
            self._lbl_export_result.configure(text=f"✓ Đã xuất {total_files} file hoàn chỉnh!", fg="#10B981")
            self._set_status(f"✓ Đã xuất {total_files} file vào {folder}")

            ans = messagebox.askyesno("Xuất Hoàn Tất", f"{msg_done}\n\nBạn có muốn mở thư mục ngay bây giờ không?")
            if ans:
                os.startfile(folder)
        except Exception as e:
            messagebox.showerror("Lỗi Xuất File", f"Không thể xuất file:\n{e}")

    def _on_export_excel_file(self):
        """Xuất riêng file Bảng đáp án & Phiếu soi câu ra Excel (.xlsx)."""
        shuffled_items = [item for item in self._loaded_exams if item.shuffled_exams]
        if not shuffled_items:
            messagebox.showwarning("Cảnh báo", "Hãy thực hiện trộn đề trước khi xuất Excel.")
            return

        if len(shuffled_items) > 1:
            fn = filedialog.asksaveasfilename(
                title="Lưu Bảng Đáp Án & Ma Trận Tổng Hợp Tất Cả Bộ Đề",
                defaultextension=".xlsx",
                filetypes=[("Excel Workbook", "*.xlsx")],
                initialfile="Tong_Hop_Dap_An_Va_Ma_Tran_Tat_Ca_Bo_De.xlsx"
            )
            if not fn:
                return

            try:
                from omr_exam.excel_exporter import export_consolidated_master_excel
                datasets = []
                for itm in shuffled_items:
                    clean_name = re.sub(r'[\\/*?:"<>|]', '_', itm.name).replace(".docx", "").strip()
                    datasets.append({
                        "name": clean_name,
                        "keys_by_code": itm.keys_by_code,
                        "question_map_by_code": itm.question_map_by_code,
                        "option_map_by_code": itm.option_map_by_code,
                    })
                export_consolidated_master_excel(fn, datasets)
                self._set_status(f"✓ Đã lưu file Excel tổng hợp: {os.path.basename(fn)}")
                ans = messagebox.askyesno(
                    "Xuất Excel Thành Công",
                    f"Đã lưu thành công file Excel Bảng Đáp Án & Ma Trận cho {len(shuffled_items)} bộ đề tại:\n{fn}\n\nBạn có muốn mở file ngay không?"
                )
                if ans:
                    os.startfile(fn)
            except Exception as e:
                messagebox.showerror("Lỗi Xuất Excel", f"Không thể tạo file Excel:\n{e}")
        else:
            item = shuffled_items[0]
            clean_name = re.sub(r'[\\/*?:"<>|]', '_', item.name).replace(".docx", "").strip()
            fn = filedialog.asksaveasfilename(
                title="Lưu Bảng Đáp Án & Ma Trận Hoán Vị Excel",
                defaultextension=".xlsx",
                filetypes=[("Excel Workbook", "*.xlsx")],
                initialfile=f"Bang_Dap_An_{clean_name}.xlsx"
            )
            if not fn:
                return

            try:
                export_exam_keys_and_matrix_to_excel(
                    filepath=fn,
                    keys_by_code=item.keys_by_code,
                    question_map_by_code=item.question_map_by_code,
                    option_map_by_code=item.option_map_by_code,
                )
                self._set_status(f"✓ Đã lưu file Excel: {os.path.basename(fn)}")
                ans = messagebox.askyesno(
                    "Xuất Excel Thành Công",
                    f"Đã lưu thành công file Excel Bảng Đáp Án & Phiếu Soi Câu tại:\n{fn}\n\nBạn có muốn mở file ngay không?"
                )
                if ans:
                    os.startfile(fn)
            except Exception as e:
                messagebox.showerror("Lỗi Xuất Excel", f"Không thể tạo file Excel:\n{e}")

    def _on_open_last_folder(self):
        """Mở thư mục xuất kết quả gần nhất."""
        if self._last_exported_folder and os.path.exists(self._last_exported_folder):
            os.startfile(self._last_exported_folder)
        else:
            messagebox.showinfo("Thông báo", "Chưa có thư mục xuất nào được ghi nhận.")

