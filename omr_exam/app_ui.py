"""
omr_exam/app_ui.py — Giao diện Quản lý Trộn đề & Hoán vị mã đề (CustomTkinter).
Đã loại bỏ hoàn toàn phần quét camera USB/chấm OMR theo yêu cầu;
chỉ tập trung tối đa vào tính năng Trộn đề thi và Xuất bản phẩm chuyên sâu (Word & Excel).
"""
from __future__ import annotations
import os
import re
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
try:
    import customtkinter as ctk
    _FrameBase = ctk.CTkFrame
except Exception:
    ctk = None
    import tkinter as tk
    _FrameBase = tk.Frame

from omr_exam.models import ExamSection, ExamQuestion, OptionItem, ShuffledExamCode
from omr_exam.docx_parser import parse_exam_docx
from omr_exam.exam_shuffler import shuffle_exam
from omr_exam.docx_exporter import export_shuffled_exams_to_docx
from omr_exam.excel_exporter import export_exam_keys_and_matrix_to_excel


class OMRExamApp(_FrameBase):
    """Giao diện Quản lý Trộn đề & Sinh mã đề độc lập (Tương thích CustomTkinter view v5)."""
    
    def __init__(self, parent):
        if ctk:
            super().__init__(parent, fg_color="transparent")
        else:
            super().__init__(parent)
        
        self._parsed_sections: list[ExamSection] = []
        self._shuffled_exams: list[ShuffledExamCode] = []
        self._source_docx_path: str | None = None
        self._keys_by_code: dict[str, dict[int, str]] = {}
        self._question_map_by_code: dict[str, dict[int, int]] = {}
        self._option_map_by_code: dict[str, dict[int, dict[str, str]]] = {}
        self._last_exported_folder: str | None = None
        
        self._build_ui()

    def _build_ui(self):
        # Header
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(10, 6))
        ctk.CTkLabel(
            head,
            text="🎲  Trộn Đề Thi Trắc Nghiệm & Hoán Vị Mã Đề",
            font=("Segoe UI", 20, "bold")
        ).pack(side="left")
        
        # Tabview 2 bước làm việc chính (Đã bỏ bước 3 Chấm OMR Camera)
        self._tabs = ctk.CTkTabview(
            self,
            segmented_button_selected_color="#1F497D",
            segmented_button_selected_hover_color="#163D6B"
        )
        self._tabs.pack(fill="both", expand=True, padx=16, pady=8)
        
        self._tab1 = self._tabs.add("1. Nguồn Đề & Thiết Lập Trộn")
        self._tab2 = self._tabs.add("2. Bảng Đáp Án & Xuất Bản Phẩm")
        
        self._build_tab1(self._tab1)
        self._build_tab2(self._tab2)

    # ── TAB 1: NGUỒN ĐỀ & THIẾT LẬP TRỘN ──────────────────────────────────────
    def _build_tab1(self, parent):
        f = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Card 1: Chọn file Word hoặc nạp đề
        c1 = ctk.CTkFrame(f)
        c1.pack(fill="x", pady=6, padx=4)
        ctk.CTkLabel(c1, text="📁  Nguồn Đề Thi Gốc (.docx hoặc Đề Hiện Tại)", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        
        r1 = ctk.CTkFrame(c1, fg_color="transparent")
        r1.pack(fill="x", padx=12, pady=8)
        self._lbl_file = ctk.CTkLabel(r1, text="Chưa nạp file đề thi", text_color="gray", width=420, anchor="w")
        self._lbl_file.pack(side="left", padx=(0, 10))
        ctk.CTkButton(r1, text="📂 Chọn file Word...", width=140, command=self._on_choose_docx).pack(side="left", padx=4)
        
        self._lbl_parse_status = ctk.CTkLabel(c1, text="", font=("Segoe UI", 12))
        self._lbl_parse_status.pack(anchor="w", padx=12, pady=(0, 8))
        
        # Card 2: Cấu hình trộn
        c2 = ctk.CTkFrame(f)
        c2.pack(fill="x", pady=6, padx=4)
        ctk.CTkLabel(c2, text="🔀  Thiết Lập Trộn Đề & Sinh Mã Đề Nâng Cao", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        
        r2_1 = ctk.CTkFrame(c2, fg_color="transparent")
        r2_1.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(r2_1, text="Số lượng mã đề:").pack(side="left", padx=(0, 6))
        self._spin_codes = ctk.CTkOptionMenu(r2_1, values=["2", "4", "6", "8", "12", "16", "24"], width=80)
        self._spin_codes.set("4")
        self._spin_codes.pack(side="left", padx=(0, 16))
        
        ctk.CTkLabel(r2_1, text="Mã bắt đầu:").pack(side="left", padx=(0, 6))
        self._entry_start_code = ctk.CTkEntry(r2_1, width=80)
        self._entry_start_code.insert(0, "101")
        self._entry_start_code.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(r2_1, text="Hoặc mã tự nhập:").pack(side="left", padx=(0, 6))
        self._entry_custom_codes = ctk.CTkEntry(r2_1, width=220, placeholder_text="VD: 101, 102, 103, 104")
        self._entry_custom_codes.pack(side="left", padx=(0, 10))

        # Hàng 2: Chế độ trộn
        r2_2 = ctk.CTkFrame(c2, fg_color="transparent")
        r2_2.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(r2_2, text="Chế độ trộn:").pack(side="left", padx=(0, 8))
        self._mode_opt = ctk.CTkOptionMenu(
            r2_2,
            values=[
                "Trộn cả câu hỏi & đáp án A/B/C/D",
                "Chỉ trộn câu hỏi (giữ nguyên A/B/C/D)",
                "Chỉ trộn đáp án (giữ nguyên thứ tự câu)"
            ],
            width=320
        )
        self._mode_opt.set("Trộn cả câu hỏi & đáp án A/B/C/D")
        self._mode_opt.pack(side="left", padx=(0, 16))

        # Checkbox ghim phương án phụ thuộc
        self._chk_pin_dependent = ctk.CTkCheckBox(
            r2_2,
            text="Ghim phương án phụ thuộc ('Tất cả...', 'Cả A và B...') ở cuối (D)",
            onvalue=True, offvalue=False
        )
        self._chk_pin_dependent.select()
        self._chk_pin_dependent.pack(side="left")

        # Hàng 3: Ghim câu & Nút trộn
        r2_3 = ctk.CTkFrame(c2, fg_color="transparent")
        r2_3.pack(fill="x", padx=12, pady=(6, 12))
        
        ctk.CTkLabel(r2_3, text="📌 Cố định câu (không đảo):").pack(side="left", padx=(0, 6))
        self._entry_pinned = ctk.CTkEntry(r2_3, width=160, placeholder_text="VD: 1, 2, 5")
        self._entry_pinned.pack(side="left", padx=(0, 20))

        self._btn_shuffle = ctk.CTkButton(
            r2_3, text="⚡ Bắt Đầu Trộn Đề",
            fg_color="#10B981", hover_color="#059669", font=("Segoe UI", 13, "bold"),
            command=self._on_do_shuffle, state="disabled"
        )
        self._btn_shuffle.pack(side="left", padx=10)
        
        # Xem trước các câu hỏi đã nhận diện
        ctk.CTkLabel(f, text="🔍 Xem trước câu hỏi đã nhận diện:", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=4, pady=(10, 2))
        self._txt_preview = ctk.CTkTextbox(f, height=220, font=("Segoe UI", 11))
        self._txt_preview.pack(fill="both", expand=True, padx=4, pady=4)

    def _on_choose_docx(self):
        fn = filedialog.askopenfilename(filetypes=[("Word Document", "*.docx")])
        if not fn: return
        self._source_docx_path = fn
        self._lbl_file.configure(text=os.path.basename(fn), text_color="#10B981")
        try:
            self._parsed_sections = parse_exam_docx(fn)
            total_q = sum(len(s.questions) for s in self._parsed_sections)
            tn_q = sum(len([q for q in s.questions if q.qtype == "TN"]) for s in self._parsed_sections)
            tl_q = total_q - tn_q
            self._lbl_parse_status.configure(
                text=f"✓ Đã nhận diện {len(self._parsed_sections)} phần | {total_q} câu hỏi ({tn_q} trắc nghiệm, {tl_q} tự luận)",
                text_color="#10B981"
            )
            
            # Preview nội dung
            self._txt_preview.delete("1.0", "end")
            for s in self._parsed_sections:
                self._txt_preview.insert("end", f"=== {s.title} ({len(s.questions)} câu) ===\n")
                for q in s.questions[:6]:
                    opts_str = " | ".join([f"{o.label}. {o.text}" for o in q.options])
                    corr_str = f" [Đ/A: {q.correct_label}]" if q.correct_label else ""
                    self._txt_preview.insert("end", f"Câu {q.index} ({q.qtype}): {q.content[:60]}... {corr_str}\n  {opts_str}\n\n")
            if total_q > 6:
                self._txt_preview.insert("end", f"... và {total_q - 6} câu hỏi khác.\n")
                
            self._btn_shuffle.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc file: {e}")

    def load_from_exam_data(self, exam_data):
        """Nạp trực tiếp từ ExamData của MatrixExamAI."""
        tn_questions = []
        tl_questions = []
        
        for i, q in enumerate(exam_data.questions, 1):
            qtype = getattr(q, "qtype", "TN")
            if qtype in ("TN", "MCQ", "SINGLE", "MULTIPLE"):
                options = []
                correct = (getattr(q, "answer", "") or "").strip().upper()
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
                    content=getattr(q, "question", "") or "",
                    options=options,
                    correct_label=correct,
                ))
            else:
                pts = getattr(q, "points", 1.0) or 1.0
                tl_questions.append(ExamQuestion(
                    index=i,
                    section="Phần II: Tự luận",
                    qtype="TL",
                    content=getattr(q, "question", "") or "",
                    tl_min_lines=max(3, int(pts * 3)),
                ))
                
        sections = []
        if tn_questions:
            sections.append(ExamSection(title="Phần I: Câu hỏi trắc nghiệm nhiều phương án lựa chọn", questions=tn_questions))
        if tl_questions:
            sections.append(ExamSection(title="Phần II: Câu hỏi tự luận", questions=tl_questions))
            
        if not sections:
            return
            
        self._parsed_sections = sections
        total_q = sum(len(s.questions) for s in self._parsed_sections)
        tn_q = len(tn_questions)
        tl_q = len(tl_questions)
        
        title = getattr(exam_data, "exam_title", "") or "Đề kiểm tra hiện tại"
        self._lbl_file.configure(text=f"📌 {title}", text_color="#10B981")
        self._lbl_parse_status.configure(text=f"✓ Đã nạp từ đề hiện tại | {total_q} câu hỏi ({tn_q} trắc nghiệm, {tl_q} tự luận)", text_color="#10B981")
        
        self._txt_preview.delete("1.0", "end")
        for s in self._parsed_sections:
            self._txt_preview.insert("end", f"=== {s.title} ({len(s.questions)} câu) ===\n")
            for q in s.questions[:6]:
                opts_str = " | ".join([f"{o.label}. {o.text}" for o in q.options])
                corr_str = f" [Đ/A: {q.correct_label}]" if q.correct_label else ""
                self._txt_preview.insert("end", f"Câu {q.index} ({q.qtype}): {q.content[:60]}... {corr_str}\n  {opts_str}\n\n")
        if total_q > 6:
            self._txt_preview.insert("end", f"... và {total_q - 6} câu hỏi khác.\n")
            
        self._btn_shuffle.configure(state="normal")

    def _on_do_shuffle(self):
        if not self._parsed_sections: return
        try:
            raw_custom = self._entry_custom_codes.get().strip()
            custom_codes = [c.strip() for c in re.split(r"[,;\s]+", raw_custom) if c.strip()] if raw_custom else None
            num = int(self._spin_codes.get())
            start = int(self._entry_start_code.get())

            m_val = self._mode_opt.get()
            mode = "both"
            if "Chỉ trộn câu" in m_val: mode = "questions_only"
            elif "Chỉ trộn đáp án" in m_val: mode = "options_only"

            auto_pin = bool(self._chk_pin_dependent.get())

            raw_pinned = self._entry_pinned.get().strip()
            pinned_set = set()
            if raw_pinned:
                for p in re.split(r"[,;\s]+", raw_pinned):
                    if p.isdigit(): pinned_set.add(int(p))

            self._shuffled_exams = shuffle_exam(
                self._parsed_sections,
                num_codes=num,
                start_code=start,
                custom_codes=custom_codes,
                shuffle_mode=mode,
                auto_pin_dependent_options=auto_pin,
                pinned_question_indices=pinned_set
            )
            
            # Nếu có file Word gốc, tính trước đáp án theo OpenXML
            if self._source_docx_path and os.path.exists(self._source_docx_path):
                from omr_exam.docx_shuffler_xml import preview_shuffled_keys
                xml_keys, xml_map, xml_opts = preview_shuffled_keys(
                    self._source_docx_path,
                    num_codes=num,
                    start_code=start,
                    custom_codes=custom_codes,
                    shuffle_mode=mode,
                    auto_pin_dependent_options=auto_pin,
                    pinned_question_indices=pinned_set
                )
                for ex in self._shuffled_exams:
                    if ex.code in xml_keys: ex.answer_key = xml_keys[ex.code]
                    if ex.code in xml_map: ex.question_map = xml_map[ex.code]
                    if ex.code in xml_opts: ex.option_map = xml_opts[ex.code]
                        
            self._keys_by_code = {ex.code: ex.answer_key for ex in self._shuffled_exams}
            self._question_map_by_code = {ex.code: ex.question_map for ex in self._shuffled_exams}
            self._option_map_by_code = {ex.code: getattr(ex, "option_map", {}) for ex in self._shuffled_exams}
            
            messagebox.showinfo(
                "Thành công",
                f"Đã trộn thành công {len(self._shuffled_exams)} mã đề độc lập!\n"
                f"Đáp án đúng & ma trận hoán vị đã được cập nhật chính xác theo từng mã đề."
            )
            self._tabs.set("2. Bảng Đáp Án & Xuất Bản Phẩm")
            self._refresh_tab2_ui()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    # ── TAB 2: XUẤT ĐỀ & BẢNG ĐÁP ÁN ─────────────────────────────────────────
    def _build_tab2(self, parent):
        f = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=8, pady=8)
        
        c1 = ctk.CTkFrame(f)
        c1.pack(fill="x", pady=6, padx=4)
        ctk.CTkLabel(c1, text="📄  Xuất Bản Phẩm Đề Thi & Bảng Đáp Án (Word & Excel)", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        
        r1 = ctk.CTkFrame(c1, fg_color="transparent")
        r1.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkButton(
            r1, text="📥 Xuất Toàn Bộ File Word (.docx)...",
            fg_color="#2563EB", hover_color="#1D4ED8",
            command=self._on_export_docx_files
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            r1, text="📊 Xuất Đáp Án & Phiếu Soi (.xlsx)...",
            fg_color="#059669", hover_color="#047857",
            command=self._on_export_excel_file
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            r1, text="📂 Mở Thư Mục Kết Quả",
            fg_color="#475569", hover_color="#334155",
            command=self._on_open_last_folder
        ).pack(side="left", padx=(0, 10))

        self._lbl_export_status = ctk.CTkLabel(r1, text="")
        self._lbl_export_status.pack(side="left")
        
        # Khung preview bảng đáp án
        ctk.CTkLabel(f, text="📋 Bảng Tổng Hợp Đáp Án Các Mã Đề:", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=8, pady=(12, 4))
        self._txt_keys = ctk.CTkTextbox(f, height=240, font=("Consolas", 11))
        self._txt_keys.pack(fill="both", expand=True, padx=4, pady=4)
        
    def _refresh_tab2_ui(self):
        if not self._shuffled_exams: return
        self._txt_keys.delete("1.0", "end")
        header = f"{'Câu':<6}" + "".join([f"{'Đề ' + ex.code:<12}" for ex in self._shuffled_exams]) + "\n"
        self._txt_keys.insert("end", header)
        self._txt_keys.insert("end", "-" * len(header) + "\n")
        
        max_q = max((max(ex.answer_key.keys(), default=0) for ex in self._shuffled_exams), default=0)
        for q in range(1, max_q + 1):
            row = f"{q:<6}"
            for ex in self._shuffled_exams:
                row += f"{ex.answer_key.get(q, '-'):<12}"
            self._txt_keys.insert("end", row + "\n")

    def _on_export_docx_files(self):
        if not self._shuffled_exams:
            messagebox.showwarning("Cảnh báo", "Hãy trộn đề ở Bước 1 trước.")
            return
        folder = filedialog.askdirectory(title="Chọn thư mục lưu các mã đề")
        if not folder: return
        try:
            files = export_shuffled_exams_to_docx(
                self._shuffled_exams, folder,
                source_docx_path=getattr(self, "_source_docx_path", None),
                export_merged_docx=True
            )
            self._last_exported_folder = folder
            self._lbl_export_status.configure(
                text=f"✓ Đã xuất {len(files)} file hoàn chỉnh!",
                text_color="#10B981"
            )
            os.startfile(folder)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _on_export_excel_file(self):
        if not self._keys_by_code:
            messagebox.showwarning("Cảnh báo", "Hãy trộn đề trước khi xuất Excel.")
            return
        fn = filedialog.asksaveasfilename(
            title="Lưu file Excel Bảng Đáp Án",
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile="Bang_Dap_An_Va_Ma_Tran_Hoan_Vi.xlsx"
        )
        if not fn: return
        try:
            export_exam_keys_and_matrix_to_excel(
                fn,
                keys_by_code=self._keys_by_code,
                question_map_by_code=self._question_map_by_code,
                option_map_by_code=self._option_map_by_code
            )
            os.startfile(fn)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _on_open_last_folder(self):
        if self._last_exported_folder and os.path.exists(self._last_exported_folder):
            os.startfile(self._last_exported_folder)
