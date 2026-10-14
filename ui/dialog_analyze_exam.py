"""
ui/dialog_analyze_exam.py — Dialog phân tích đề thi (Word/PDF) → ma trận đặc tả.

Cho phép người dùng:
  1. Upload file đề thi (.docx / .pdf)
  2. Xem danh sách câu hỏi đã nhận diện (Treeview)
  3. Chỉnh sửa loại câu / mức độ / chủ đề / điểm
  4. Gọi AI để chuyển đổi chính xác hơn
  5. Xuất ma trận đặc tả ra file Word
"""

from __future__ import annotations

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Callable

from core.exam_parser import parse_exam_file, ExamPaper
from core.models import MatrixData, MatrixRow


# ──────────────────────────────────────────────────────────────────────────────
#  Constants
# ──────────────────────────────────────────────────────────────────────────────

_BG = "#F8FAFC"
_BG_HDR = "#EFF6FF"
_FG = "#0F172A"
_FG2 = "#475569"
_ACCENT = "#0EA5E9"
_PURPLE = "#7C3AED"
_GREEN = "#10B981"
_RED = "#EF4444"
_ORANGE = "#F59E0B"
_FONT = ("Segoe UI", 8)
_FONT_B = ("Segoe UI", 9, "bold")
_FONT_H = ("Segoe UI", 11, "bold")

_QTYPE_LIST = ["TN", "DS", "TLN", "TL"]
_LEVEL_LIST = ["NB", "TH", "VD"]


# ──────────────────────────────────────────────────────────────────────────────
#  Helper — convert ExamPaper → MatrixData (AI-enhanced)
# ──────────────────────────────────────────────────────────────────────────────

def _paper_to_matrix(paper: ExamPaper, subject: str = "", grade: str = "12") -> MatrixData:
    """Convert an ExamPaper to MatrixData."""
    return paper.to_matrix_data()


# ──────────────────────────────────────────────────────────────────────────────
#  Dialog
# ──────────────────────────────────────────────────────────────────────────────

class AnalyzeExamDialog(tk.Toplevel):
    """
    Dialog phân tích đề thi: chọn file → xem trước câu hỏi → xuất ma trận.
    """

    def __init__(
        self,
        parent: tk.Widget,
        get_ai_call: Optional[Callable] = None,
        on_matrix_ready: Optional[Callable[[MatrixData], None]] = None,
    ):
        super().__init__(parent)
        self.title("📋 Phân tích đề thi → Ma trận đặc tả")
        self.geometry("1000x620")
        self.minsize(780, 480)
        self.configure(bg=_BG)
        self.grab_set()
        self.focus_set()

        self._get_ai_call = get_ai_call
        self._on_matrix_ready = on_matrix_ready
        self._paper: Optional[ExamPaper] = None
        self._matrix_data: Optional[MatrixData] = None
        self._q_widgets: dict[int, dict] = {}  # row_index → {qtype_cb, level_cb, topic_en, pts_en}

        self._build_ui()

        # Auto-open file dialog after window appears
        self.after(200, self._open_file_picker)

    # ── Build UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=_BG_HDR)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="📋  Phân tích đề thi → Ma trận đặc tả",
            bg=_BG_HDR, fg=_FG, font=_FONT_H,
        ).pack(side="left", padx=16, pady=8)

        # Info row
        info_f = tk.Frame(self, bg=_BG)
        info_f.pack(fill="x", padx=12, pady=(4, 0))

        tk.Button(
            info_f, text="📂  Chọn file đề (.docx / .pdf)",
            font=_FONT_B, bg=_ACCENT, fg="white",
            activebackground="#0284C7", relief="flat", cursor="hand2", padx=10, pady=4,
            command=self._open_file_picker,
        ).pack(side="left", padx=(0, 8))

        tk.Label(info_f, text="Hỗ trợ: Word (.docx), PDF (.pdf), Text (.txt)",
                bg=_BG, fg=_FG2, font=_FONT).pack(side="left")

        # Toolbar
        tb = tk.Frame(self, bg=_BG)
        tb.pack(fill="x", padx=12, pady=(4, 2))

        self._ai_btn = tk.Button(
            tb, text="🤖  AI chuyển đổi chính xác",
            font=_FONT_B, bg=_PURPLE, fg="white",
            activebackground="#6D28D9", activeforeground="white",
            disabledforeground="#F8FAFC",
            relief="flat", cursor="hand2", padx=10, pady=4,
            command=self._ai_convert,
        )
        self._ai_btn.pack(side="left", padx=(0, 6))
        self._ai_btn.config(state="disabled")

        tk.Button(
            tb, text="💾  Xuất ma trận đặc tả (Word)",
            font=_FONT_B, bg=_GREEN, fg="white",
            activebackground="#059669", relief="flat", cursor="hand2", padx=10, pady=4,
            command=self._export_matrix,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            tb, text="✅  Dùng ma trận này",
            font=_FONT_B, bg="#0284C7", fg="white",
            activebackground="#0369A1", relief="flat", cursor="hand2", padx=10, pady=4,
            command=self._use_matrix,
        ).pack(side="left", padx=(0, 6))

        self._status_lbl = tk.Label(tb, text="Chưa mở file",
                                    bg=_BG, fg=_FG2, font=_FONT)
        self._status_lbl.pack(side="right")

        # Table header
        hdr_f = tk.Frame(self, bg="#E2E8F0")
        hdr_f.pack(fill="x", padx=12, pady=(4, 0))

        col_specs = [
            ("STT", 5), ("Loại", 8), ("Mức", 7),
            ("Chủ đề / Nội dung", 28), ("Điểm", 7), ("✓", 4),
        ]
        self._hdr_labels = {}
        for i, (txt, w) in enumerate(col_specs):
            lbl = tk.Label(hdr_f, text=txt, bg="#E2E8F0", fg="#334155",
                           font=("Segoe UI", 8, "bold"), anchor="center",
                           relief="groove", borderwidth=1, pady=4)
            lbl.grid(row=0, column=i, sticky="nsew", padx=0)
            hdr_f.columnconfigure(i, weight=1 if txt == "Chủ đề / Nội dung" else 0)

        # Status bar (ghim đáy trước)
        sb = tk.Frame(self, bg="#E2E8F0", height=24)
        sb.pack(fill="x", side="bottom", pady=0)

        # Treeview (chiếm phần còn lại ở giữa)
        tree_f = tk.Frame(self, bg=_BG)
        tree_f.pack(fill="both", expand=True, padx=12, pady=(0, 4))

        cols = ["stt", "qtype", "level", "topic", "points", "use"]
        self._tree = ttk.Treeview(
            tree_f, columns=cols, show="headings",
            selectmode="extended", height=18,
        )

        col_ws = {"stt": 50, "qtype": 80, "level": 70,
                  "topic": 400, "points": 70, "use": 40}
        col_anchors = {"stt": "center", "qtype": "center",
                       "level": "center", "topic": "w",
                       "points": "center", "use": "center"}

        for cid in cols:
            self._tree.heading(cid, text=self._tree.cget("columns")[list(cols).index(cid)]
                               if cid != "use" else "✓")
            self._tree.column(cid, width=col_ws.get(cid, 100),
                              anchor=col_anchors.get(cid, "w"), minwidth=30)

        vsb = ttk.Scrollbar(tree_f, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_f, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_f.rowconfigure(0, weight=1)
        tree_f.columnconfigure(0, weight=1)

        self._tree.tag_configure("hdr_row", background="#F1F5F9", foreground="#64748B")
        self._tree.tag_configure("odd", background="#FAFBFC")

        self._tree.bind("<Double-1>", self._on_tree_double_click)
        self._sb_lbl = tk.Label(sb, text="", bg="#E2E8F0", fg=_FG2, font=_FONT)
        self._sb_lbl.pack(side="left", padx=8, pady=4)

        tk.Label(sb, text="  Nhấn đúp dòng để chỉnh sửa  ",
                bg="#E2E8F0", fg="#94A3B8", font=("Segoe UI", 7)).pack(side="right", padx=8)

    # ── File picking ─────────────────────────────────────────────────────────

    def _open_file_picker(self):
        path = filedialog.askopenfilename(
            title="Chọn file đề thi",
            filetypes=[
                ("Word / PDF", "*.docx *.pdf"),
                ("Word", "*.docx"),
                ("PDF", "*.pdf"),
                ("Text", "*.txt"),
                ("Tất cả", "*.*"),
            ],
        )
        if not path:
            return
        self._load_file(path)

    def _load_file(self, path: str):
        self._status_lbl.config(text=f"⏳ Đang đọc {os.path.basename(path)}…", fg=_ACCENT)
        self.update_idletasks()

        try:
            _raw, self._paper = parse_exam_file(path)
        except Exception as e:
            messagebox.showerror("Lỗi đọc file", str(e), parent=self)
            self._status_lbl.config(text=f"❌ Lỗi: {e}", fg=_RED)
            return

        qs = self._paper.raw_questions
        self._populate_tree(qs)

        self._status_lbl.config(
            text=f"✅ Đọc xong — {len(qs)} câu hỏi nhận diện được",
            fg=_GREEN,
        )
        self._sb_lbl.config(text=f"Tổng: {len(qs)} câu  |  Loại: TN={sum(1 for q in qs if q.qtype=='TN')}  DS={sum(1 for q in qs if q.qtype=='DS')}  TL={sum(1 for q in qs if q.qtype in('TL','TLN'))}")
        self._ai_btn.config(state="normal")

    def _populate_tree(self, questions):
        for item in self._tree.get_children():
            self._tree.delete(item)

        self._q_widgets.clear()
        for i, q in enumerate(questions):
            tag = "hdr_row" if q.stt == 0 else ("odd" if i % 2 else "")
            stt = q.stt if q.stt else ""
            self._tree.insert("", "end", values=(
                stt, q.qtype, q.level,
                q.topic or q.question[:80],
                q.points if q.points else ("0.25" if q.qtype in ("TN", "DS") else "1.0"),
                "☑",
            ), tags=(tag,) if tag else ())

        if not self._tree.get_children():
            self._tree.insert("", "end", values=(
                "—", "—", "—", "(Không nhận diện được câu hỏi nào — hãy thử gọi AI chuyển đổi)", "—", "—",
            ))

    # ── AI conversion ───────────────────────────────────────────────────────

    def _ai_convert(self):
        if not self._paper:
            return
        if not self._get_ai_call:
            messagebox.showinfo("AI không khả dụng", "Không có kết nối AI.", parent=self)
            return

        qs = self._paper.raw_questions
        raw_lines = []
        for q in qs:
            raw_lines.append(
                f"Câu {q.stt} [{q.qtype}]: {q.topic or q.question[:120]}"
            )
        raw_text = "\n".join(raw_lines)

        prompt = (
            "Bạn là chuyên gia phân tích đề thi.\n"
            "Dưới đây là các câu hỏi đã trích xuất từ đề thi:\n\n"
            f"{raw_text}\n\n"
            "Hãy chuyển đổi thành ma trận đặc tả dạng JSON với cấu trúc sau "
            "(mỗi câu 1 object, gộp thành mảng `rows`):\n"
            "{\n"
            '  "title": "Tên đề",\n'
            '  "time_str": "90 phút",\n'
            '  "rows": [\n'
            '    {\n'
            '      "stt": "1",\n'
            '      "topic": "Chủ đề ngắn",\n'
            '      "level": "NB|TH|VD",\n'
            '      "qtype": "TN|DS|TLN|TL",\n'
            '      "codes": [],\n'
            '      "requirement": "Yêu cầu cần đạt",\n'
            '      "points": 0.25\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Chỉ trả về JSON, không giải thích gì thêm."
        )

        import time
        self._ai_started_at = time.monotonic()
        self._ai_timer_active = True
        self._render_ai_progress("AI đang phân tích đề")
        self._tick_ai_timer()

        def done(response: str):
            self.after(0, lambda: self._handle_ai_response(response))

        try:
            ai_call = self._get_ai_call()
            ai_call(prompt, done_callback=done)
        except Exception as e:
            self._ai_timer_active = False
            messagebox.showerror("Lỗi AI", str(e), parent=self)
            self._status_lbl.config(text=f"❌ Lỗi: {e}", fg=_RED)

    def _tick_ai_timer(self):
        if not getattr(self, "_ai_timer_active", False):
            return
        try:
            self._render_ai_progress(getattr(self, "_ai_progress_msg", "AI đang phân tích"))
        except Exception:
            return
        self.after(1000, self._tick_ai_timer)

    def _render_ai_progress(self, msg: str):
        import time
        self._ai_progress_msg = msg
        if not hasattr(self, "_ai_started_at"):
            self._status_lbl.config(text=f"🤖 {msg}…", fg=_PURPLE)
            return
        elapsed = int(time.monotonic() - self._ai_started_at)
        mins, secs = divmod(elapsed, 60)
        tstr = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"
        self._status_lbl.config(text=f"🤖 {msg}…   ⏱ {tstr}", fg=_PURPLE)

    def _handle_ai_response(self, response: str):
        import json
        import time
        # Stop ticking and capture elapsed time
        self._ai_timer_active = False
        elapsed_str = ""
        if hasattr(self, "_ai_started_at"):
            elapsed = int(time.monotonic() - self._ai_started_at)
            mins, secs = divmod(elapsed, 60)
            elapsed_str = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

        # Try to extract JSON from the response
        text = response.strip()
        # Remove markdown code fences
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON block
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    data = json.loads(m.group())
                except Exception:
                    messagebox.showerror(
                        "Lỗi phân tích AI",
                        f"AI trả về không đúng định dạng JSON (sau {elapsed_str}).\n"
                        f"Nội dung:\n{text[:500]}",
                        parent=self,
                    )
                    self._status_lbl.config(text=f"❌ AI trả sai định dạng (⏱ {elapsed_str})", fg=_RED)
                    return
            else:
                messagebox.showerror("Lỗi phân tích AI",
                                     f"Không tìm thấy JSON trong phản hồi (sau {elapsed_str}):\n{text[:300]}",
                                     parent=self)
                self._status_lbl.config(text=f"❌ Không tìm được JSON (⏱ {elapsed_str})", fg=_RED)
                return

        try:
            md = MatrixData.from_dict(data)
        except Exception:
            messagebox.showerror("Lỗi cấu trúc", "Dữ liệu ma trận không đúng định dạng.",
                                 parent=self)
            self._status_lbl.config(text=f"❌ Sai cấu trúc ma trận (⏱ {elapsed_str})", fg=_RED)
            return

        self._matrix_data = md
        qs_from_md = [
            type("Q", (), {"stt": r.stt, "qtype": r.qtype, "level": r.level,
                            "topic": r.topic, "points": r.points})()
            for r in md.rows
        ]
        self._populate_tree(qs_from_md)
        self._status_lbl.config(
            text=f"✅ AI hoàn thành — {len(md.rows)} dòng ma trận (⏱ {elapsed_str})",
            fg=_GREEN,
        )
        self._sb_lbl.config(
            text=f"Ma trận: {len(md.rows)} dòng  |  {md.time_str}  |  AI chạy: {elapsed_str}"
        )

    # ── Export matrix ───────────────────────────────────────────────────────

    def _export_matrix(self):
        md = self._get_matrix_data()
        if not md or not md.rows:
            messagebox.showwarning("Chưa có ma trận",
                                   "Hãy mở file đề thi trước.",
                                   parent=self)
            return

        path = filedialog.asksaveasfilename(
            title="Lưu ma trận đặc tả",
            defaultextension=".docx",
            filetypes=[("Word", "*.docx"), ("JSON", "*.json")],
            initialfile="ma_tran_dat_ta.docx",
        )
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()
        if ext == ".json":
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(md.to_dict(), f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Đã lưu", f"Ma trận đã lưu vào:\n{path}", parent=self)
            return

        # Export as Word
        try:
            import docx
            from docx.shared import Pt, RGBColor, Cm
            from docx.enum.text import WD_ALIGN_PARAGRAPH

            doc = docx.Document()
            # Page margins
            sec = doc.sections[0]
            sec.left_margin = sec.right_margin = Cm(1.5)
            sec.top_margin = sec.bottom_margin = Cm(1.5)

            # Title
            title_p = doc.add_paragraph(md.title or "Ma trận đặc tả")
            title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = title_p.runs[0]
            run.bold = True
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(0x0F, 0x2D, 0x52)

            # Meta
            doc.add_paragraph(f"Thời gian: {md.time_str}")

            # Table header
            headers = ["STT", "Chủ đề", "Loại", "Mức", "Yêu cầu cần đạt", "Điểm"]
            tbl = doc.add_table(rows=1, cols=len(headers))
            tbl.style = "Table Grid"
            hdr_cells = tbl.rows[0].cells
            for i, h in enumerate(headers):
                hdr_cells[i].text = h
                hdr_cells[i].paragraphs[0].runs[0].bold = True
                hdr_cells[i].paragraphs[0].runs[0].font.size = Pt(9)

            for row in md.rows:
                cells = tbl.add_row().cells
                cells[0].text = str(row.stt)
                cells[1].text = str(row.topic)
                cells[2].text = str(row.qtype)
                cells[3].text = str(row.level)
                cells[4].text = str(row.requirement)
                cells[5].text = f"{row.points:.2f}"
                for c in cells:
                    c.paragraphs[0].runs[0].font.size = Pt(8)

            doc.save(path)
            messagebox.showinfo("Đã lưu", f"Ma trận đặc tả đã lưu vào:\n{path}", parent=self)

        except ImportError:
            messagebox.showwarning("Thiếu thư viện",
                                  "python-docx chưa được cài.\n"
                                  "Ma trận sẽ được lưu dưới dạng JSON.",
                                  parent=self)
            import json
            json_path = path.replace(".docx", ".json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(md.to_dict(), f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Đã lưu (JSON)", f"Ma trận đã lưu vào:\n{json_path}", parent=self)

    # ── Use matrix ───────────────────────────────────────────────────────────

    def _use_matrix(self):
        md = self._get_matrix_data()
        if not md or not md.rows:
            messagebox.showwarning("Chưa có ma trận",
                                   "Hãy mở file đề thi trước.",
                                   parent=self)
            return
        if self._on_matrix_ready:
            self._on_matrix_ready(md)
        self.destroy()

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _get_matrix_data(self) -> Optional[MatrixData]:
        if self._matrix_data:
            return self._matrix_data
        if self._paper:
            return _paper_to_matrix(self._paper)
        return None

    def _on_tree_double_click(self, event):
        """Allow inline editing by double-click (simplified: just show info)."""
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(self._tree.index(sel[0]))
        if self._paper and idx < len(self._paper.raw_questions):
            q = self._paper.raw_questions[idx]
            messagebox.showinfo(
                f"Câu {q.stt}",
                f"Loại: {q.qtype}\nMức: {q.level}\n"
                f"Chủ đề: {q.topic}\n\nNội dung:\n{q.question[:300]}",
                parent=self,
            )
