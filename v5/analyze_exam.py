"""CTk dialog for analysing an existing exam file into a matrix.

This is the V5-native replacement for ``ui.dialog_analyze_exam``.  The
business work stays in ``core.exam_parser`` and ``export.matrix_exporter``;
this module only presents the workflow and normalises optional AI output.
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from core.exam_parser import ExamPaper, parse_exam_file
from core.models import MatrixData, MatrixRow


_QTYPE_POINTS = {"TN": 0.25, "DS": 1.0, "TLN": 0.5, "TL": 1.0}


def matrix_from_exam_file(path: str) -> tuple[str, ExamPaper, MatrixData]:
    """Read an exam file and build a first-pass matrix from local parsing."""
    raw_text, paper = parse_exam_file(path)
    matrix = paper.to_matrix_data()
    return raw_text, paper, matrix


def build_ai_matrix_prompt(paper: ExamPaper, raw_text: str = "") -> str:
    """Build a compact prompt asking AI to refine topic/level/qtype rows."""
    question_lines: list[str] = []
    for q in paper.raw_questions:
        preview = " ".join((q.question or "").split())[:220]
        question_lines.append(
            f"Câu {q.stt}: loại={q.qtype}, mức={q.level}, "
            f"topic_dự_đoán={q.topic[:80]!r}, nội_dung={preview!r}"
        )
    if not question_lines and raw_text:
        question_lines.append(raw_text[:4000])

    return (
        "Bạn là chuyên gia xây dựng ma trận đặc tả đề Toán.\n"
        "Từ các câu hỏi đã trích xuất dưới đây, hãy trả về đúng 1 JSON object.\n"
        "Không markdown, không giải thích.\n\n"
        "Schema:\n"
        "{\n"
        '  "title": "Tên đề hoặc ma trận",\n'
        '  "time_str": "90 phút",\n'
        '  "rows": [\n'
        '    {"stt":"1","topic":"Chủ đề ngắn","level":"NB|TH|VD",'
        '"qtype":"TN|DS|TLN|TL","codes":["TN1"],'
        '"requirement":"Yêu cầu cần đạt cụ thể","points":0.25}\n'
        "  ]\n"
        "}\n\n"
        "Quy ước: NB=Nhận biết, TH=Thông hiểu, VD=Vận dụng. "
        "Điểm mặc định: TN 0.25, DS 1.0, TLN 0.5, TL 1.0.\n\n"
        "Câu hỏi:\n" + "\n".join(question_lines)
    )


def parse_ai_matrix_response(response: str) -> MatrixData:
    """Parse permissive AI JSON into a valid MatrixData."""
    text = (response or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("AI không trả về JSON.")
        data = json.loads(match.group())

    if not isinstance(data, dict):
        raise ValueError("JSON ma trận phải là object.")
    raw_rows = data.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise ValueError("JSON ma trận thiếu mảng rows.")

    rows: list[MatrixRow] = []
    for i, raw in enumerate(raw_rows, 1):
        if not isinstance(raw, dict):
            continue
        qtype = str(raw.get("qtype") or "TN").upper()
        if qtype not in _QTYPE_POINTS:
            qtype = "TN"
        level = str(raw.get("level") or "TH").upper()
        if level not in {"NB", "TH", "VD", "VDC"}:
            level = "TH"
        if level == "VDC":
            level = "VD"
        topic = str(raw.get("topic") or "Chủ đề chưa phân loại").strip()
        requirement = str(raw.get("requirement") or f"{topic} [{level}]").strip()
        codes = raw.get("codes")
        if isinstance(codes, str):
            codes = [codes]
        if not isinstance(codes, list) or not codes:
            codes = [f"{qtype}{i}"]
        try:
            points = float(raw.get("points", _QTYPE_POINTS[qtype]))
        except (TypeError, ValueError):
            points = _QTYPE_POINTS[qtype]
        rows.append(MatrixRow(
            stt=str(raw.get("stt") or i),
            topic=topic,
            level=level,
            qtype=qtype,
            codes=[str(code) for code in codes if str(code).strip()],
            requirement=requirement,
            points=points,
            enabled=bool(raw.get("enabled", True)),
        ))

    if not rows:
        raise ValueError("AI không tạo được dòng ma trận hợp lệ.")
    return MatrixData(
        title=str(data.get("title") or "Ma trận đặc tả từ đề thi"),
        time_str=str(data.get("time_str") or "90 phút"),
        rows=rows,
    )


class AnalyzeExamDialog(ctk.CTkToplevel):
    """Analyse DOCX/PDF/TXT exam papers and return a MatrixData object."""

    def __init__(
        self,
        parent,
        *,
        get_ai_call: Callable[[], Callable[[str], str] | None] | None = None,
        on_matrix_ready: Callable[[MatrixData], None] | None = None,
    ):
        super().__init__(parent)
        self.title("Phân tích đề thi -> Ma trận")
        self.geometry("980x620")
        self.minsize(820, 520)
        self.transient(parent)
        self.grab_set()

        self._get_ai_call = get_ai_call
        self._on_matrix_ready = on_matrix_ready
        self._raw_text = ""
        self._paper: ExamPaper | None = None
        self._matrix: MatrixData | None = None
        self._source_path: Path | None = None

        self._build()
        self.bind("<Escape>", lambda _e: self.destroy())

    def _build(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(
            header, text="Phân tích đề thi -> Ma trận đặc tả",
            font=("Segoe UI", 18, "bold")).pack(side="left")
        ctk.CTkButton(
            header, text="Chọn file đề", width=130,
            command=self._choose_file).pack(side="right", padx=4)

        hint = (
            "Hỗ trợ DOCX/PDF/TXT có text-layer. App tạo ma trận nháp bằng parser "
            "local; có thể dùng AI để tinh chỉnh chủ đề/mức độ/yêu cầu cần đạt."
        )
        ctk.CTkLabel(self, text=hint, text_color="gray", wraplength=900,
                     justify="left").pack(anchor="w", padx=16, pady=(0, 8))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=16, pady=(0, 8))
        self._ai_btn = ctk.CTkButton(
            toolbar, text="AI tinh chỉnh ma trận", width=160,
            fg_color=("#7C3AED", "#5B21B6"), state="disabled",
            command=self._ai_refine)
        self._ai_btn.pack(side="left", padx=(0, 6))
        self._export_docx_btn = ctk.CTkButton(
            toolbar, text="Xuất Word", width=110, state="disabled",
            command=lambda: self._export_matrix("docx"))
        self._export_docx_btn.pack(side="left", padx=2)
        self._export_csv_btn = ctk.CTkButton(
            toolbar, text="Xuất CSV", width=100, state="disabled",
            command=lambda: self._export_matrix("csv"))
        self._export_csv_btn.pack(side="left", padx=2)
        self._use_btn = ctk.CTkButton(
            toolbar, text="Dùng ma trận này", width=140, state="disabled",
            fg_color=("#10B981", "#047857"), command=self._use_matrix)
        self._use_btn.pack(side="left", padx=2)
        self._status = ctk.CTkLabel(toolbar, text="Chưa mở file",
                                    text_color="gray")
        self._status.pack(side="right")

        table_frame = ctk.CTkFrame(self, fg_color=("white", "#1E293B"))
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        columns = ("stt", "qtype", "level", "topic", "requirement", "points")
        self._tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        labels = {
            "stt": "#", "qtype": "Loại", "level": "Mức",
            "topic": "Chủ đề", "requirement": "Yêu cầu cần đạt", "points": "Điểm",
        }
        widths = {
            "stt": 46, "qtype": 62, "level": 58,
            "topic": 220, "requirement": 460, "points": 64,
        }
        for col in columns:
            self._tree.heading(col, text=labels[col])
            self._tree.column(
                col, width=widths[col],
                anchor=("w" if col in {"topic", "requirement"} else "center"),
                stretch=col in {"topic", "requirement"},
            )
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._tree)
        except Exception:
            pass
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self._tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal",
                            command=self._tree.xview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(0, 14))
        self._summary = ctk.CTkLabel(footer, text="", text_color="gray",
                                     anchor="w")
        self._summary.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(footer, text="Đóng", width=90,
                      fg_color=("#6B7280", "#374151"),
                      command=self.destroy).pack(side="right")

    def _choose_file(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Chọn file đề thi",
            filetypes=[
                ("Đề thi", "*.docx *.pdf *.txt"),
                ("Word", "*.docx"),
                ("PDF", "*.pdf"),
                ("Text", "*.txt"),
                ("Tất cả", "*.*"),
            ],
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str):
        self._status.configure(text=f"Đang đọc {Path(path).name}...",
                               text_color="#3B82F6")
        self._set_buttons("disabled")

        def _worker():
            try:
                raw, paper, matrix = matrix_from_exam_file(path)
                self.after(0, lambda: self._on_loaded(Path(path), raw, paper, matrix, None))
            except Exception as exc:
                error = exc
                self.after(0, lambda error=error: self._on_loaded(
                    Path(path), "", None, None, error))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_loaded(self, path: Path, raw: str, paper, matrix, error):
        if error is not None:
            self._status.configure(text=f"Lỗi: {str(error)[:80]}",
                                   text_color="#EF4444")
            messagebox.showerror("Lỗi đọc đề", str(error)[:300], parent=self)
            return
        self._source_path = path
        self._raw_text = raw
        self._paper = paper
        self._matrix = matrix
        self._status.configure(text=f"Đã đọc {path.name}", text_color="#10B981")
        self._set_buttons("normal")
        self._render_matrix()

    def _set_buttons(self, state: str):
        for button in (self._ai_btn, self._export_docx_btn,
                       self._export_csv_btn, self._use_btn):
            button.configure(state=state)

    def _render_matrix(self):
        self._tree.delete(*self._tree.get_children())
        matrix = self._matrix
        if not matrix:
            return
        for i, row in enumerate(matrix.rows, 1):
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self._tree.insert("", "end", values=(
                row.stt, row.qtype, row.level, row.topic,
                row.requirement, f"{row.points:g}",
            ), tags=(tag,))
        stats: dict[str, int] = {}
        for row in matrix.rows:
            stats[row.qtype] = stats.get(row.qtype, 0) + 1
        stat_text = ", ".join(f"{key}: {value}" for key, value in sorted(stats.items()))
        self._summary.configure(
            text=f"{len(matrix.rows)} dòng ma trận"
                 + (f" ({stat_text})" if stat_text else "")
                 + (f"  |  {matrix.time_str}" if matrix.time_str else ""))

    def _ai_refine(self):
        if not self._paper:
            return
        if not callable(self._get_ai_call):
            messagebox.showinfo("AI không khả dụng", "Chưa có hàm gọi AI.",
                                parent=self)
            return
        ai_call = self._get_ai_call()
        if not ai_call:
            messagebox.showinfo(
                "Thiếu API key",
                "Chưa có API key cho provider nào. Nhập trong Cấu hình trước.",
                parent=self,
            )
            return
        prompt = build_ai_matrix_prompt(self._paper, self._raw_text)
        self._status.configure(text="AI đang tinh chỉnh ma trận...",
                               text_color="#7C3AED")
        self._ai_btn.configure(state="disabled", text="Đang gọi AI...")

        def _worker():
            try:
                response = ai_call(prompt)
                matrix = parse_ai_matrix_response(response)
                self.after(0, lambda: self._on_ai_done(matrix, None))
            except Exception as exc:
                error = exc
                self.after(0, lambda error=error: self._on_ai_done(None, error))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_ai_done(self, matrix, error):
        self._ai_btn.configure(state="normal", text="AI tinh chỉnh ma trận")
        if error is not None:
            self._status.configure(text=f"AI lỗi: {str(error)[:80]}",
                                   text_color="#EF4444")
            messagebox.showerror("AI tinh chỉnh lỗi", str(error)[:300],
                                 parent=self)
            return
        self._matrix = matrix
        self._status.configure(text="AI đã tinh chỉnh ma trận",
                               text_color="#10B981")
        self._render_matrix()

    def _export_matrix(self, kind: str):
        if not self._matrix:
            return
        initial = (self._source_path.stem if self._source_path else "Ma_tran")
        filetypes = [("Word", "*.docx")] if kind == "docx" else [("CSV", "*.csv")]
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Xuất ma trận đặc tả",
            defaultextension=f".{kind}",
            initialfile=f"{initial}_ma_tran.{kind}",
            filetypes=filetypes,
        )
        if not path:
            return
        try:
            from export.matrix_exporter import export_matrix_csv, export_matrix_docx
            if kind == "csv":
                export_matrix_csv(self._matrix, path)
            else:
                export_matrix_docx(self._matrix, path)
            from v5.toast import show_toast
            show_toast(self.master if self.master else self,
                       f"Đã xuất ma trận: {Path(path).name}",
                       kind="success", duration=5)
        except Exception as exc:
            messagebox.showerror("Lỗi xuất ma trận", str(exc)[:300],
                                 parent=self)

    def _use_matrix(self):
        if not self._matrix:
            return
        if callable(self._on_matrix_ready):
            self._on_matrix_ready(self._matrix)
        self.destroy()
