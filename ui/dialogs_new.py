"""
ui/dialogs_new.py — Dialogs: AI-fix, source selector, review, NHCH save.
"""
from __future__ import annotations
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from copy import deepcopy
from pathlib import Path
from typing import Callable, Optional

from config import TYPE_LABELS, LEVEL_COLORS
from core.models import Question, ExamData, MatrixRow
from core.generator import _safe_format as _fill, _PROMPT, _DS_NOTE, _FMT_TN, _FMT_DS, _FMT_TLN, _FMT_TL
from core.parser import parse_one_question
from ui.image_helper import (pick_and_copy_image, pick_and_copy_images,
                                remove_image, load_tk_image,
                                normalize_image_field, serialize_image_field)

BLUE = "#1F497D"; BG = "#F9F7F4"

# ── Tiện ích render LaTeX đơn giản cho tkinter ────────────────────────────────
def _tex_preview(text: str) -> str:
    """Chuyển ${...}$ → ký hiệu Unicode dễ đọc (preview nhanh trong Text widget)."""
    # Giữ nguyên — render thực sẽ do cách hiển thị LaTeX ngoài ứng dụng
    return text  # tkinter không render LaTeX; hiển thị nguyên bản là OK


# ══════════════════════════════════════════════════════════════════════════════
#  EditQuestionDialogV2 — Sửa câu + AI fix + gợi ý
# ══════════════════════════════════════════════════════════════════════════════

class EditQuestionDialogV2(tk.Toplevel):
    """Chỉnh sửa câu hỏi với:
    - Cột Gợi ý chỉnh sửa cho AI (nhập hướng dẫn trước khi bấm AI Fix)
    - Hiển thị diff trước/sau
    - Lưu vào NHCH với chọn nơi lưu (cục bộ / GAS)
    """

    def __init__(self, parent, question: Question, on_save_cb: Callable,
                 get_ai_call: Optional[Callable] = None,
                 subject: str = "", grade: str = "",
                 qc_issues: str = ""):          # truyền từ Tab QC
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title(f"✏️  Sửa câu — {TYPE_LABELS.get(question.qtype, question.qtype)}")
        self.geometry("1180x760")
        self.resizable(True, True)
        self.minsize(960, 600)
        self.grab_set()
        self._q        = question
        self._save     = on_save_cb
        self._get_ai   = get_ai_call
        self._subject  = subject
        self._grade    = grade
        self._qc_issues = qc_issues
        self._widgets: dict = {}
        self._orig_question = question.question  # backup để so sánh diff
        self._tk_images: list = []  # giữ reference để không bị GC
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # ── Header (compact + live ID) ────────────────────────────────────
        hdr = tk.Frame(self, bg=BLUE)
        hdr.pack(fill="x")
        q = self._q

        # Auto-compute ID nếu chưa có (lúc mở dialog)
        if not (getattr(q, "question_id", "") or "").strip():
            self._auto_assign_id(q)

        # Header dùng StringVar để LIVE update khi user đổi topic/level/qtype
        self._header_var = tk.StringVar()
        hdr_lbl = tk.Label(hdr, textvariable=self._header_var,
                             bg=BLUE, fg="white", cursor="question_arrow",
                             font=("Segoe UI", 10, "bold"))
        hdr_lbl.pack(side="left", padx=12, pady=6)
        # Tooltip giải thích ID khi hover lên header
        self._attach_id_tooltip(hdr_lbl)
        self._refresh_header()

        # ── Main: 2 cột (Form chỉnh sửa | Helper Notebook) ──────────────
        main_pane = tk.PanedWindow(self, orient="horizontal",
                                    sashwidth=6, sashrelief="groove",
                                    bg="#E5E7EB")
        main_pane.pack(fill="both", expand=True, padx=4, pady=4)

        # ── CỘT TRÁI: Form chỉnh sửa (scrollable) ──────────────────────────
        left_wrap = tk.Frame(main_pane, bg="white")
        main_pane.add(left_wrap, minsize=560, stretch="always", width=820)

        canvas = tk.Canvas(left_wrap, highlightthickness=0, bg="white")
        vsb    = ttk.Scrollbar(left_wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, padx=12, pady=10, bg="white")
        wid   = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))

        # FIX v2: bind_all + check widget chain → chỉ scroll canvas khi mouse
        # THỰC SỰ trong canvas tree. Tránh Enter/Leave bug khi mouse di chuyển
        # nhanh giữa các Text widget con (Enter/Leave có thể không fire đúng).
        # Text widget có wheel handler riêng → nó tự scroll nội dung khi cần;
        # các Frame/Label/Entry khác trong canvas → wheel fire xuống canvas.
        def _wheel(e):
            # Walk parent chain of e.widget — nếu gặp canvas thì scroll
            w = e.widget
            for _ in range(20):                # giới hạn depth phòng loop
                if w is canvas:
                    canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
                    return "break"
                # Nếu w là Text/Listbox/Treeview → để widget tự handle wheel,
                # KHÔNG scroll canvas. Trả None để event tiếp tục propagate.
                if isinstance(w, (tk.Text, tk.Listbox)):
                    try:
                        # Text widget không cần scroll nếu đã ở giới hạn
                        # → fallback canvas scroll. Đơn giản: để Text tự xử
                        return None
                    except Exception:
                        break
                try:
                    w = w.master
                except Exception:
                    break
                if w is None:
                    break
            return None  # ngoài canvas → default handle (Notebook etc.)

        canvas.bind("<MouseWheel>", _wheel)
        self.bind("<MouseWheel>", _wheel, add="+")

        if q._error:
            tk.Label(inner, text=f"⚠️ Câu bị lỗi: {q._error_msg}",
                     fg="#CC0000", bg="#FFF0F0",
                     font=("Segoe UI", 9, "bold"), wraplength=600,
                     relief="solid", padx=6, pady=4).pack(fill="x", pady=(0, 8))

        # ── Helper: tạo block "label trên, Text dưới" — rộng full chiều ngang ─
        def section_text(lbl: str, content: str, height: int = 4,
                          bg: str = "white", highlight_math: bool = True,
                          label_color: str = "#1F2937") -> tk.Text:
            tk.Label(inner, text=lbl, anchor="w",
                     font=("Segoe UI", 10, "bold"), fg=label_color,
                     bg="white").pack(fill="x", pady=(6, 2))
            w = tk.Text(inner, height=height, font=("Segoe UI", 11),
                        wrap="word", relief="solid", borderwidth=1,
                        bg=bg, padx=6, pady=4)
            w.insert("1.0", content or "")
            w.tag_configure("math_formula",
                             foreground="#7C3AED", font=("Consolas", 11, "bold"))
            w.pack(fill="x", expand=False)
            if highlight_math:
                _highlight_math_in_widget(w)
                w.bind("<KeyRelease>", lambda e, _w=w: _highlight_math_in_widget(_w))
            return w

        # ── Metadata: Chủ đề + Mức độ (1 hàng) ────────────────────
        meta_f = tk.Frame(inner, bg="white")
        meta_f.pack(fill="x", pady=(0, 4))

        tk.Label(meta_f, text="Chủ đề:", anchor="w", bg="white",
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 4))
        self._topic_var = tk.StringVar(value=q.topic or "")
        topic_e = ttk.Combobox(meta_f, textvariable=self._topic_var, width=32,
                                font=("Segoe UI", 10))
        topic_e["values"] = [
            "Hàm số và đồ thị",
            "Giới hạn và liên tục",
            "Đạo hàm và ứng dụng",
            "Nguyên hàm và tích phân",
            "Số phức",
            "Hình học không gian",
            "Hình học tọa độ trong không gian",
            "Hình học tọa độ phẳng",
            "Xác suất và thống kê",
            "Lượng giác",
            "Hàm số mũ và logarithm",
            "Tổ hợp và xác suất",
            "Dãy số - Cấp số cộng - Cấp số nhân",
            "Phương trình - Bất phương trình",
            "Vectơ",
        ]
        topic_e.pack(side="left", padx=(0, 16))

        tk.Label(meta_f, text="Mức độ:", anchor="w", bg="white",
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 4))
        self._level_var = tk.StringVar(value=q.level or "TH")
        level_cb = ttk.Combobox(meta_f, textvariable=self._level_var, width=8,
                                 font=("Segoe UI", 10), state="readonly")
        level_cb["values"] = ["NB", "TH", "VD"]
        level_cb.pack(side="left")

        # Live update ID khi user đổi topic/level → header tự refresh
        self._topic_var.trace_add("write", lambda *_: self._on_meta_change())
        self._level_var.trace_add("write", lambda *_: self._on_meta_change())

        # ── Câu hỏi (lớn hơn — 8 dòng) ────────────────────────────────────
        self._q_text = section_text("📝  Câu hỏi:", q.question, height=8,
                                      label_color=BLUE)
        self._make_image_row(inner, q.question_image, "img_question")

        if q.qtype == "TN":
            # ── 4 phương án (3 dòng mỗi cái — đủ cho 1-2 dòng LaTeX) ─────
            tk.Label(inner, text="🔤  Phương án:", anchor="w", bg="white",
                     font=("Segoe UI", 10, "bold"), fg=BLUE).pack(fill="x", pady=(10, 2))
            for k in "ABCD":
                opt_row = tk.Frame(inner, bg="white")
                opt_row.pack(fill="x", pady=2)
                tk.Label(opt_row, text=f"{k}.", width=3, anchor="nw",
                         font=("Segoe UI", 11, "bold"), fg="#374151",
                         bg="white").pack(side="left", padx=(4, 4), pady=4)
                w = tk.Text(opt_row, height=3, font=("Segoe UI", 11),
                            wrap="word", relief="solid", borderwidth=1,
                            padx=6, pady=4)
                w.insert("1.0", q.options.get(k, ""))
                w.tag_configure("math_formula",
                                 foreground="#7C3AED",
                                 font=("Consolas", 11, "bold"))
                w.pack(side="left", fill="x", expand=True)
                _highlight_math_in_widget(w)
                w.bind("<KeyRelease>", lambda e, _w=w: _highlight_math_in_widget(_w))
                self._widgets[f"opt_{k}"] = w
                self._make_image_row(inner, q.option_images.get(k, ""), f"img_opt_{k}")

            # ── Đáp án đúng — radio inline ─────────────────────────────────
            ans_f = tk.Frame(inner, bg="white"); ans_f.pack(fill="x", pady=(8, 4))
            tk.Label(ans_f, text="✓  Đáp án đúng:", anchor="w", bg="white",
                     font=("Segoe UI", 10, "bold"), fg="#059669").pack(side="left", padx=(0, 8))
            ans_var = tk.StringVar(value=q.answer)
            for k in "ABCD":
                ttk.Radiobutton(ans_f, text=k, variable=ans_var, value=k).pack(
                    side="left", padx=8)
            self._widgets["answer_var"] = ans_var

            # ── Lời giải (lớn — 6 dòng) ────────────────────────────────────
            self._widgets["solution_w"] = section_text(
                "💡  Lời giải:", q.solution, height=6,
                bg="#FFFDF0", label_color="#92400E")
            self._make_image_row(inner, q.solution_image, "img_solution")

        elif q.qtype == "DS":
            tk.Label(inner, text="📋  4 ý đúng/sai:", anchor="w", bg="white",
                     font=("Segoe UI", 10, "bold"), fg=BLUE).pack(fill="x", pady=(10, 2))
            for k in "abcd":
                lf = tk.LabelFrame(inner, text=f"  Ý ({k})  ", padx=8, pady=6,
                                    bg="white", font=("Segoe UI", 9, "bold"))
                lf.pack(fill="x", pady=4)
                item_w = tk.Text(lf, height=3, font=("Segoe UI", 11),
                                  wrap="word", relief="solid", borderwidth=1,
                                  padx=6, pady=3)
                item_w.insert("1.0", q.items.get(k, ""))
                item_w.tag_configure("math_formula",
                                      foreground="#7C3AED",
                                      font=("Consolas", 11, "bold"))
                item_w.pack(fill="x")
                _highlight_math_in_widget(item_w)
                item_w.bind("<KeyRelease>",
                             lambda e, w=item_w: _highlight_math_in_widget(w))
                self._make_image_row(lf, q.item_images.get(k, ""), f"img_item_{k}")
                ds_f   = tk.Frame(lf, bg="white"); ds_f.pack(anchor="w", pady=(4, 2))
                ds_var = tk.BooleanVar(value=q.answers.get(k, False))
                ttk.Radiobutton(ds_f, text="✓ Đúng", variable=ds_var, value=True).pack(
                    side="left", padx=4)
                ttk.Radiobutton(ds_f, text="✗ Sai", variable=ds_var, value=False).pack(
                    side="left", padx=4)
                tk.Label(lf, text="Giải thích:", font=("Segoe UI", 9),
                          fg="#6B7280", bg="white").pack(anchor="w", pady=(4, 2))
                sol_w = tk.Text(lf, height=3, font=("Segoe UI", 10),
                                 wrap="word", relief="solid", borderwidth=1,
                                 bg="#FFFDF0", padx=6, pady=3)
                sol_w.insert("1.0", q.item_solutions.get(k, ""))
                sol_w.pack(fill="x")
                self._widgets[f"item_{k}"] = item_w
                self._widgets[f"ds_{k}"]   = ds_var
                self._widgets[f"giai_{k}"] = sol_w

        elif q.qtype in ("TLN", "TL"):
            if q.qtype == "TLN":
                ans_var = tk.StringVar(value=q.answer)
                f2 = tk.Frame(inner, bg="white"); f2.pack(fill="x", pady=(8, 4))
                tk.Label(f2, text="✓  Đáp số:", anchor="w", bg="white",
                          font=("Segoe UI", 10, "bold"), fg="#059669").pack(side="left", padx=(0, 8))
                ttk.Entry(f2, textvariable=ans_var, width=40,
                          font=("Segoe UI", 11)).pack(side="left", fill="x", expand=True)
                self._widgets["answer_var"] = ans_var
            pts_var = tk.StringVar(value=str(q.points))
            f3 = tk.Frame(inner, bg="white"); f3.pack(fill="x", pady=(4, 4))
            tk.Label(f3, text="🎯  Điểm:", anchor="w", bg="white",
                      font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 8))
            ttk.Entry(f3, textvariable=pts_var, width=10,
                      font=("Segoe UI", 10)).pack(side="left")
            self._widgets["pts_var"] = pts_var
            self._widgets["solution_w"] = section_text(
                "💡  Lời giải:", q.solution, height=8,
                bg="#FFFDF0", label_color="#92400E")
            self._make_image_row(inner, q.solution_image, "img_solution")

        # ── CỘT PHẢI: Notebook 3 tab (Gọn — không chiếm chỗ) ──────────────
        right_wrap = tk.Frame(main_pane, bg=BG)
        main_pane.add(right_wrap, minsize=300, stretch="never", width=340)

        nb = ttk.Notebook(right_wrap)
        nb.pack(fill="both", expand=True, padx=6, pady=6)

        # ── Tab 1: Gợi ý AI ───────────────────────────────────────────────
        tab_hint = tk.Frame(nb, bg=BG)
        nb.add(tab_hint, text="💡 Gợi ý AI")

        tk.Label(tab_hint,
                 text="Nhập hướng dẫn cụ thể để AI sửa đúng hơn:",
                 fg="#374151", font=("Segoe UI", 9, "bold"),
                 bg=BG).pack(anchor="w", padx=8, pady=(8, 4))

        self._hint_text = tk.Text(tab_hint, font=("Segoe UI", 10),
                                   wrap="word", relief="solid", borderwidth=1,
                                   bg="#FFFDF0", padx=6, pady=4)
        if self._qc_issues:
            self._hint_text.insert("1.0",
                f"Vấn đề từ QC:\n{self._qc_issues}\n\nYêu cầu sửa: ")
        else:
            placeholder = ("Ví dụ:\n"
                           "- Sửa lại đáp án cho chính xác\n"
                           "- Viết lại câu hỏi rõ ràng hơn\n"
                           "- Đảm bảo công thức ${...}$ đúng\n"
                           "- Điều chỉnh mức độ khó")
            self._hint_text.insert("1.0", placeholder)
            self._hint_text.config(fg="#9CA3AF")
            def _clear_placeholder(e):
                if self._hint_text.get("1.0", "end-1c") == placeholder:
                    self._hint_text.delete("1.0", "end")
                    self._hint_text.config(fg="black")
            self._hint_text.bind("<FocusIn>", _clear_placeholder)
        self._hint_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # ── Tab 2: Quy ước LaTeX ──────────────────────────────────────────
        tab_math = tk.Frame(nb, bg=BG)
        nb.add(tab_math, text="📐 LaTeX")
        tk.Label(tab_math,
                 text="Sử dụng cú pháp  ${...}$  cho công thức Toán:\n\n"
                      "  ${x^2}$         →  x bình\n"
                      "  ${x_1}$         →  x chỉ số 1\n"
                      "  ${\\frac{a}{b}}$    →  phân số\n"
                      "  ${\\sqrt{x}}$    →  căn bậc hai\n"
                      "  ${\\sqrt[3]{x}}$  →  căn bậc ba\n"
                      "  ${\\int_0^1 f(x)dx}$  →  tích phân\n"
                      "  ${\\sum_{i=1}^n}$    →  tổng\n"
                      "  ${A}$, ${AB}$, ${ABC}$  →  điểm/đoạn\n"
                      "  ${\\vec{AB}}$  →  vectơ\n"
                      "  ${\\alpha}$, ${\\beta}$  →  ký tự Hy Lạp\n\n"
                      "💡 Công thức tự động tô màu tím khi gõ.",
                 bg="#FFFBF0", fg="#374151",
                 font=("Segoe UI", 9), justify="left",
                 anchor="nw").pack(fill="both", expand=True, padx=8, pady=8)

        # ── Tab 3: So sánh trước/sau AI sửa ───────────────────────────────
        tab_diff = tk.Frame(nb, bg=BG)
        nb.add(tab_diff, text="📋 So sánh")
        tk.Label(tab_diff,
                 text="Hiển thị thay đổi sau khi AI sửa câu:",
                 fg="#374151", font=("Segoe UI", 9, "bold"),
                 bg=BG).pack(anchor="w", padx=8, pady=(8, 4))
        self._diff_text = tk.Text(tab_diff, font=("Consolas", 9),
                                   state="disabled", wrap="word",
                                   bg="#F8F8F8", padx=6, pady=4)
        self._diff_text.tag_configure("added",   foreground="#166534",
                                       background="#DCFCE7")
        self._diff_text.tag_configure("removed", foreground="#991B1B",
                                       background="#FEE2E2", overstrike=True)
        self._diff_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # ── Bottom: Buttons + status ──────────────────────────────────────
        bot = tk.Frame(self, bg=BG)
        bot.pack(fill="x", padx=8, pady=6)

        tk.Button(bot, text="💾  Lưu thay đổi",
                   font=("Segoe UI", 10, "bold"),
                   bg="#10b981", fg="white", activebackground="#059669",
                   relief="flat", cursor="hand2", padx=14, pady=6,
                   command=self._on_save).pack(side="left", padx=4)

        if self._get_ai:
            tk.Button(bot, text="🤖  AI sửa theo gợi ý",
                       font=("Segoe UI", 10, "bold"),
                       bg=BLUE, fg="white", activebackground="#163d6b",
                       relief="flat", cursor="hand2", padx=14, pady=6,
                       command=self._ai_fix).pack(side="left", padx=4)

        tk.Button(bot, text="💾  Lưu vào NHCH",
                   font=("Segoe UI", 9),
                   bg="#7C3AED", fg="white", activebackground="#6D28D9",
                   relief="flat", cursor="hand2", padx=10, pady=6,
                   command=self._save_to_nhch).pack(side="left", padx=4)

        tk.Button(bot, text="  Hủy  ", font=("Segoe UI", 9),
                  bg="#6B7280", fg="white", activebackground="#4B5563",
                  relief="flat", cursor="hand2", pady=4,
                  command=self.destroy).pack(side="left", padx=4)

        self._ai_status = tk.StringVar(value="")
        tk.Label(bot, textvariable=self._ai_status,
                 fg=BLUE, font=("Segoe UI", 8, "italic"), bg=BG).pack(
                     side="left", padx=8)

    # ── ID auto-compute & live update ────────────────────────────────────────
    def _auto_assign_id(self, q: "Question") -> None:
        """Tính + gán ID structured cho q (nếu thiếu)."""
        from core.models import compute_structured_id
        existing = self._get_existing_qids()
        new_id = compute_structured_id(
            q, grade_str=self._grade or "12",
            existing_qids=existing,
        )
        if new_id:
            q.question_id = new_id

    def _get_existing_qids(self) -> set[str]:
        """Lấy tập question_id đã tồn tại (NHCH local) để tránh trùng seq."""
        try:
            from storage.database import list_all_questions
            return {(d.get("question_id") or "") for d in
                    (list_all_questions() or [])
                    if d.get("question_id")}
        except Exception:
            return set()

    def _on_meta_change(self) -> None:
        """Callback khi user đổi topic/level → recompute ID + refresh header."""
        from core.models import compute_structured_id
        # Sync vars vào question (tạm) để compute đúng
        self._q.topic = self._topic_var.get().strip()
        self._q.level = (self._level_var.get() or "TH").strip()
        # Recompute ID
        existing = self._get_existing_qids() - {getattr(self._q, "question_id", "")}
        new_id = compute_structured_id(
            self._q, grade_str=self._grade or "12",
            existing_qids=existing,
        )
        if new_id:
            self._q.question_id = new_id
        self._refresh_header()

    def _refresh_header(self) -> None:
        q = self._q
        qid = getattr(q, "question_id", "") or "(chưa có ID)"
        topic = (self._topic_var.get() if hasattr(self, "_topic_var")
                  else q.topic) or "(chưa phân loại)"
        level = (self._level_var.get() if hasattr(self, "_level_var")
                  else q.level) or "?"
        self._header_var.set(
            f"  ✏️  {TYPE_LABELS.get(q.qtype, q.qtype)}  │  {level}  │  {topic}  │  🔑 {qid}"
        )

    def _attach_id_tooltip(self, widget) -> None:
        """Hover → popup giải thích từng ký tự của ID hiện tại."""
        _SUBJ = {"D": "Đại số", "H": "Hình học"}
        _LV   = {"N": "Nhận biết", "T": "Thông hiểu",
                  "V": "Vận dụng",   "G": "Vận dụng cao"}
        _QT   = {1: "TN", 2: "DS", 3: "TLN", 4: "TL"}
        tip = {"win": None}

        def _show(_e=None):
            qid = (getattr(self._q, "question_id", "") or "").strip()
            m = re.match(r"^(\d{1,2})([DH])(\d+)([NTVG])(\d+)-(\d+)$", qid)
            if not m:
                lines = [f"🔑 ID hiện tại: {qid or '(rỗng)'}",
                         "(không theo chuẩn — bấm 🔄 trong NHCH preview để regen)"]
            else:
                g, s, c, l, t, n = m.groups()
                lines = [
                    f"🔑 {qid}",
                    f"  • Lớp:    {g}",
                    f"  • Môn:    {s} = {_SUBJ.get(s,'?')}",
                    f"  • Chương:  {c}",
                    f"  • Mức độ:  {l} = {_LV.get(l,'?')}",
                    f"  • Loại:    {t} = {_QT.get(int(t),'?')}",
                    f"  • Số TT:   {int(n)}",
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

    # ── Image helpers (multi-image support) ──────────────────────────────────
    def _make_image_row(self, parent, image_path, key: str) -> tk.Frame:
        """Tạo 1 hàng gồm nút chèn nhiều ảnh + grid thumbnails.

        `image_path` chấp nhận str (1 ảnh — backward compat), list[str], hay
        "a.png|b.png" (legacy '|'-separated).

        Lưu vào `self._widgets[key]` 1 _ImageListHolder — có `.get()` trả về
        '|'-joined str (legacy Question.field schema) và `.get_list()` trả list[str].
        """
        # ── Holder lưu list path + UI refresh callback ─────────────────────
        paths: list[str] = normalize_image_field(image_path)

        class _Holder:
            __slots__ = ("paths", "_refresh")
            def __init__(self, p, r): self.paths = p; self._refresh = r
            def get(self):       return serialize_image_field(self.paths)
            def get_list(self):  return list(self.paths)
            def set(self, v):
                self.paths = normalize_image_field(v); self._refresh()
            def add(self, new_paths):
                self.paths.extend(p for p in new_paths if p)
                self._refresh()
            def remove_at(self, idx):
                if 0 <= idx < len(self.paths):
                    self.paths.pop(idx); self._refresh()
            def clear(self):     self.paths = []; self._refresh()

        # ── Container layout ───────────────────────────────────────────────
        row = tk.Frame(parent, bg=parent["bg"] if "bg" in parent.keys() else "white")
        row.pack(fill="x", pady=2)

        # Vùng nút (trái) | Vùng thumbnails (phải, wraps)
        btn_f = tk.Frame(row, bg=row["bg"])
        btn_f.pack(side="left", padx=(14, 6), anchor="n")

        thumbs_frame = tk.Frame(row, bg=row["bg"])
        thumbs_frame.pack(side="left", fill="x", expand=True)

        # Drag-drop state: {dragging_idx, drop_target_idx}
        drag_state = {"src": -1, "tgt": -1}

        def _refresh_thumbs():
            # Clear old
            for child in thumbs_frame.winfo_children():
                child.destroy()
            n = len(holder.paths)
            count_lbl.config(text=f"({n} ảnh)" if n else "(chưa có ảnh)")
            # Render mỗi ảnh: thumbnail + nút ✕ + drag-handle
            for idx, p in enumerate(holder.paths):
                cell = tk.Frame(thumbs_frame, bg="#F0F0F0",
                                  relief="groove", bd=1, cursor="fleur")
                cell.pack(side="left", padx=2, pady=2)
                cell._img_idx = idx       # gắn idx vào widget để drag-drop tra

                tk_img = load_tk_image(p, max_w=160, max_h=110)
                if tk_img:
                    self._tk_images.append(tk_img)
                    lbl = tk.Label(cell, image=tk_img, bg="#F0F0F0",
                                     cursor="fleur")
                    lbl.pack(side="top", padx=2, pady=(2, 0))
                else:
                    from pathlib import Path as _P
                    lbl = tk.Label(cell, text=f"⚠ {_P(p).name}", bg="#FEF3C7",
                             fg="#92400E", font=("Segoe UI", 8),
                             wraplength=140, padx=8, pady=20, cursor="fleur")
                    lbl.pack()
                # Bind drag-drop trên cell + image label
                for w in (cell, lbl):
                    w.bind("<Button-1>",
                             lambda e, i=idx: _drag_start(i))
                    w.bind("<B1-Motion>",
                             lambda e: _drag_motion(e))
                    w.bind("<ButtonRelease-1>",
                             lambda e: _drag_end())
                # Bottom: filename + ordinal + remove button
                bot = tk.Frame(cell, bg="#F0F0F0")
                bot.pack(side="top", fill="x", padx=2, pady=(0, 2))
                from pathlib import Path as _P
                tk.Label(bot, text=f"#{idx+1}  {_P(p).name[:15]}",
                         fg="#6B7280", bg="#F0F0F0", font=("Segoe UI", 7),
                         anchor="w").pack(side="left", fill="x", expand=True)
                tk.Button(bot, text="✕", font=("Segoe UI", 8, "bold"),
                          bg="#FEE2E2", fg="#991B1B", relief="flat",
                          cursor="hand2", padx=4, pady=0,
                          command=lambda i=idx: holder.remove_at(i)
                          ).pack(side="right")

        def _drag_start(idx: int):
            drag_state["src"] = idx

        def _drag_motion(event):
            # Tìm widget dưới chuột
            w = event.widget.winfo_containing(event.x_root, event.y_root)
            tgt = -1
            while w is not None and w is not thumbs_frame:
                if hasattr(w, "_img_idx"):
                    tgt = w._img_idx; break
                w = w.master
            drag_state["tgt"] = tgt

        def _drag_end():
            src, tgt = drag_state["src"], drag_state["tgt"]
            drag_state["src"] = drag_state["tgt"] = -1
            if src < 0 or tgt < 0 or src == tgt:
                return
            if 0 <= src < len(holder.paths) and 0 <= tgt < len(holder.paths):
                # Swap-and-reorder: pop src, insert at tgt
                item = holder.paths.pop(src)
                holder.paths.insert(tgt, item)
                _refresh_thumbs()

        holder = _Holder(paths, _refresh_thumbs)
        self._widgets[key] = holder

        # Nút chèn ảnh (single)
        def _pick_one():
            new_path = pick_and_copy_image(self)
            if new_path:
                holder.add([new_path])

        # Nút chèn NHIỀU ảnh
        def _pick_many():
            new_paths = pick_and_copy_images(self)
            if new_paths:
                holder.add(new_paths)

        tk.Button(btn_f, text="🖼 + Ảnh", font=("Segoe UI", 8),
                  bg="#E0E7FF", fg="#3730A3", relief="flat", cursor="hand2",
                  padx=6, pady=2, command=_pick_one,
                  ).pack(side="top", padx=2, pady=(0, 2))
        tk.Button(btn_f, text="🖼🖼 + Nhiều", font=("Segoe UI", 8, "bold"),
                  bg="#A78BFA", fg="white", relief="flat", cursor="hand2",
                  padx=6, pady=2, command=_pick_many,
                  ).pack(side="top", padx=2, pady=(0, 2))
        tk.Button(btn_f, text="🗑 Xoá hết", font=("Segoe UI", 7),
                  bg="#FCA5A5", fg="#7F1D1D", relief="flat", cursor="hand2",
                  padx=4, pady=1, command=holder.clear,
                  ).pack(side="top", padx=2)
        count_lbl = tk.Label(btn_f, text="", fg="#6B7280",
                              font=("Segoe UI", 7), bg=row["bg"])
        count_lbl.pack(side="top", pady=(2, 0))

        _refresh_thumbs()
        return row

    # ── Save ──────────────────────────────────────────────────────────────────
    def _save_images_to_question(self, q: Question) -> None:
        """Lưu đường dẫn ảnh từ widgets vào Question object."""
        # Ảnh câu hỏi
        if "img_question" in self._widgets:
            q.question_image = self._widgets["img_question"].get()
        # Ảnh lời giải
        if "img_solution" in self._widgets:
            q.solution_image = self._widgets["img_solution"].get()
        # Ảnh phương án TN
        if q.qtype == "TN":
            q.option_images = {}
            for k in "ABCD":
                key = f"img_opt_{k}"
                if key in self._widgets:
                    val = self._widgets[key].get()
                    if val:
                        q.option_images[k] = val
        # Ảnh ý DS
        if q.qtype == "DS":
            q.item_images = {}
            for k in "abcd":
                key = f"img_item_{k}"
                if key in self._widgets:
                    val = self._widgets[key].get()
                    if val:
                        q.item_images[k] = val

    def _on_save(self) -> None:
        q     = self._q
        q.question = self._q_text.get("1.0", "end").strip()
        q.topic = self._topic_var.get().strip()
        q.level = self._level_var.get().strip() or "TH"
        qtype = q.qtype

        if qtype == "TN":
            q.options  = {k: self._widgets[f"opt_{k}"].get("1.0","end").strip()
                          for k in "ABCD"}
            q.answer   = self._widgets["answer_var"].get()
            q.solution = self._widgets["solution_w"].get("1.0","end").strip()
            q._error   = False
        elif qtype == "DS":
            q.items          = {k: self._widgets[f"item_{k}"].get("1.0","end").strip()
                                for k in "abcd"}
            q.answers        = {k: self._widgets[f"ds_{k}"].get() for k in "abcd"}
            q.item_solutions = {k: self._widgets[f"giai_{k}"].get("1.0","end").strip()
                                for k in "abcd"}
            q._error = False
        elif qtype in ("TLN", "TL"):
            if "answer_var" in self._widgets:
                q.answer = self._widgets["answer_var"].get()
            if "pts_var" in self._widgets:
                try:
                    q.points = float(self._widgets["pts_var"].get().replace(",","."))
                except ValueError:
                    pass
            q.solution = self._widgets["solution_w"].get("1.0","end").strip()
            q._error   = False

        self._save_images_to_question(q)
        self._save(q)
        self.destroy()

    # ── Lưu vào NHCH (chọn nơi lưu) ──────────────────────────────────────────
    def _save_to_nhch(self) -> None:
        """Hỏi người dùng muốn lưu cục bộ hay lên GAS."""
        dlg = _NHCHSaveDialog(self, self._q, self._subject, self._grade)
        self.wait_window(dlg)

    # ── AI Fix ────────────────────────────────────────────────────────────────
    def _ai_fix(self) -> None:
        hint = self._hint_text.get("1.0", "end").strip()
        # Lọc placeholder
        if hint.startswith("Ví dụ:"):
            hint = ""

        self._ai_status.set("⏳ AI đang sửa câu…")
        self.update_idletasks()

        q     = self._q
        qtype = q.qtype
        FMT   = {"TN": _FMT_TN, "DS": _FMT_DS, "TLN": _FMT_TLN, "TL": _FMT_TL}

        current_question = self._q_text.get("1.0", "end").strip()

        def _fmt_current() -> str:
            lines = [f"Câu hỏi: {current_question}"]
            if qtype == "TN":
                for k in "ABCD":
                    v    = self._widgets[f"opt_{k}"].get("1.0","end").strip()
                    mark = " ← ĐÁP ÁN" if k == self._widgets["answer_var"].get() else ""
                    lines.append(f"  {k}. {v}{mark}")
            elif qtype == "DS":
                for k in "abcd":
                    v       = self._widgets[f"item_{k}"].get("1.0","end").strip()
                    verdict = "Đ" if self._widgets[f"ds_{k}"].get() else "S"
                    lines.append(f"  ({k}) {v}  [{verdict}]")
            return "\n".join(lines)

        fmt_block = _fill(FMT.get(qtype, _FMT_TL),
                          level=q.level, topic=q.topic, points=q.points)
        hint_section = (
            f"\n\nGỢI Ý CHỈNH SỬA TỪ NGƯỜI DÙNG:\n{hint}\n"
            if hint else "\n"
        )

        prompt = (
            f"Bạn là giáo viên Toán THPT Việt Nam.\n"
            f"Hãy SỬA câu hỏi sau theo yêu cầu. Giữ nguyên cấu trúc định dạng.\n"
            f"Môn: {self._subject} — Lớp: {self._grade}\n"
            f"Loại: {TYPE_LABELS.get(qtype,qtype)} | Mức: {q.level} | Chủ đề: {q.topic}\n\n"
            f"NỘI DUNG HIỆN TẠI:\n{_fmt_current()}"
            f"{hint_section}"
            f"YÊU CẦU CHỈNH SỬA:\n"
            f"1. Sửa lỗi sai về toán học / kiến thức\n"
            f"2. Đảm bảo công thức dùng cú pháp ${{...}}$ (ví dụ: ${{x^2}}$, ${{\\\\sqrt{{a}}}}$)\n"
            f"3. Sửa câu từ mơ hồ, không rõ ràng\n"
            f"4. Đảm bảo đáp án chính xác\n"
            f"5. Giữ nguyên mức độ {q.level}\n\n"
            f"Trả về câu đã sửa theo định dạng:\n{fmt_block}"
        )

        def do_fix():
            try:
                ai_call = self._get_ai()
                raw     = ai_call(prompt)
                fixed   = parse_one_question(raw)
                if not fixed or fixed._error:
                    self.after(0, lambda: self._ai_status.set(
                        "❌ AI không trả về đúng định dạng. Thử lại hoặc sửa tay."))
                    return
                self.after(0, lambda f=fixed: self._apply_fix(f))
            except Exception as e:
                self.after(0, lambda err=str(e):
                           self._ai_status.set(f"❌ Lỗi: {err[:80]}"))

        threading.Thread(target=do_fix, daemon=True).start()

    def _apply_fix(self, fixed: Question) -> None:
        old_text = self._q_text.get("1.0", "end-1c")
        qtype    = self._q.qtype

        # Cập nhật widgets
        self._q_text.delete("1.0", "end")
        self._q_text.insert("1.0", fixed.question)
        _highlight_math_in_widget(self._q_text)

        if qtype == "TN":
            for k in "ABCD":
                self._widgets[f"opt_{k}"].delete("1.0", "end")
                self._widgets[f"opt_{k}"].insert("1.0", fixed.options.get(k, ""))
                _highlight_math_in_widget(self._widgets[f"opt_{k}"])
            if fixed.answer in "ABCD":
                self._widgets["answer_var"].set(fixed.answer)
            self._widgets["solution_w"].delete("1.0", "end")
            self._widgets["solution_w"].insert("1.0", fixed.solution)

        elif qtype == "DS":
            for k in "abcd":
                self._widgets[f"item_{k}"].delete("1.0", "end")
                self._widgets[f"item_{k}"].insert("1.0", fixed.items.get(k, ""))
                _highlight_math_in_widget(self._widgets[f"item_{k}"])
                self._widgets[f"ds_{k}"].set(fixed.answers.get(k, False))
                self._widgets[f"giai_{k}"].delete("1.0", "end")
                self._widgets[f"giai_{k}"].insert("1.0", fixed.item_solutions.get(k, ""))

        elif qtype in ("TLN", "TL"):
            if "answer_var" in self._widgets:
                self._widgets["answer_var"].set(fixed.answer)
            self._widgets["solution_w"].delete("1.0", "end")
            self._widgets["solution_w"].insert("1.0", fixed.solution)

        # Hiển thị diff đơn giản
        self._show_diff(old_text, fixed.question)
        self._ai_status.set("✅ AI đã sửa xong — kiểm tra rồi nhấn 💾 Lưu")

    def _show_diff(self, old: str, new: str) -> None:
        """Hiển thị so sánh trước/sau trong cột phải."""
        dt = self._diff_text
        dt.config(state="normal")
        dt.delete("1.0", "end")
        dt.insert("end", "▼ TRƯỚC:\n", "removed")
        dt.insert("end", old[:300] + ("…" if len(old) > 300 else "") + "\n\n")
        dt.insert("end", "▼ SAU:\n", "added")
        dt.insert("end", new[:300] + ("…" if len(new) > 300 else ""))
        dt.config(state="disabled")


# ── Hàm tô màu công thức ${...}$ trong Text widget ───────────────────────────
def _highlight_math_in_widget(widget: tk.Text) -> None:
    """Tô màu tím các công thức ${...}$ trong widget."""
    widget.tag_remove("math_formula", "1.0", "end")
    content = widget.get("1.0", "end")
    for m in re.finditer(r'\$\{[^}]*\}\$', content):
        start = m.start()
        end   = m.end()
        # Tính vị trí dạng line.col cho tkinter
        line_start = content[:start].count('\n') + 1
        col_start  = start - content[:start].rfind('\n') - 1
        line_end   = content[:end].count('\n') + 1
        col_end    = end - content[:end].rfind('\n') - 1
        try:
            widget.tag_add("math_formula",
                           f"{line_start}.{col_start}",
                           f"{line_end}.{col_end}")
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  Dialog chọn nơi lưu NHCH
# ══════════════════════════════════════════════════════════════════════════════

class _NHCHSaveDialog(tk.Toplevel):
    """Hỏi người dùng lưu câu vào đâu: cục bộ / GAS / cả hai."""

    def __init__(self, parent, question: Question, subject: str, grade: str):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("💾  Lưu vào Ngân hàng câu hỏi")
        self.geometry("440x360")
        self.resizable(False, False)
        self.grab_set()
        self._q       = question
        self._subject = subject
        self._grade   = grade
        self._choice  = tk.StringVar(value="local")
        self._build()

    def _build(self):
        tk.Label(self, text="Chọn nơi lưu câu hỏi",
                 font=("Segoe UI", 12, "bold"), fg=BLUE).pack(pady=(16, 8))

        options = [
            ("local",  "💻  Lưu cục bộ (trên máy này)",
             "Lưu vào SQLite trên máy tính của bạn."),
            ("gas",    "☁️   Lưu lên GAS (Ngân hàng chung)",
             "Upload lên Google Sheets để chia sẻ với cộng đồng."),
            ("both",   "💾  Lưu cả hai nơi",
             "Lưu cục bộ VÀ upload lên GAS đồng thời."),
        ]
        for value, title, desc in options:
            f = tk.Frame(self, relief="ridge", bd=1, padx=10, pady=6)
            f.pack(fill="x", padx=20, pady=3)
            ttk.Radiobutton(f, text=title, variable=self._choice,
                             value=value).pack(anchor="w")
            tk.Label(f, text=desc, fg="#666",
                     font=("Segoe UI", 8)).pack(anchor="w", padx=20)

        btn_f = tk.Frame(self); btn_f.pack(pady=12)
        tk.Button(btn_f, text="💾  Lưu",
                   font=("Segoe UI", 10, "bold"),
                   bg="#10b981", fg="white", activebackground="#059669",
                   relief="flat", cursor="hand2", padx=14, pady=6,
                   command=self._do_save).pack(side="left", padx=6)
        tk.Button(btn_f, text="  Hủy  ", font=("Segoe UI", 9),
                  bg="#6B7280", fg="white", activebackground="#4B5563",
                  relief="flat", cursor="hand2", pady=6,
                  command=self.destroy).pack(side="left", padx=4)

    def _do_save(self):
        choice = self._choice.get()
        q      = self._q
        saved_local = saved_gas = False

        # Lưu cục bộ
        if choice in ("local", "both"):
            try:
                from storage.database import save_questions
                cnt = save_questions([q], self._subject, self._grade,
                                     source="manual_edit")
                saved_local = cnt > 0
            except Exception as e:
                messagebox.showerror("Lỗi lưu cục bộ", str(e), parent=self)
                return

        # Upload GAS
        if choice in ("gas", "both"):
            try:
                from services.license_manager import nhch_upload_batch, get_machine_id
                import uuid
                qid = getattr(q, "question_id", "") or f"QID-{uuid.uuid4().hex[:10].upper()}"
                result = nhch_upload_batch([{
                    "question_id": qid,
                    "subject":     self._subject,
                    "grade":       self._grade,
                    "topic":       q.topic,
                    "level":       q.level,
                    "qtype":       q.qtype,
                    "question":    q.question,
                    "options":     q.options or {},
                    "answer":      q.answer or "",
                    "solution":    q.solution or "",
                }], get_machine_id())
                saved_gas = result.get("ok", False)
            except Exception as e:
                messagebox.showerror("Lỗi upload GAS", str(e), parent=self)
                if choice == "gas":
                    return

        # Thông báo kết quả
        parts = []
        if saved_local: parts.append("✅ Đã lưu cục bộ")
        if saved_gas:   parts.append("☁️ Đã upload GAS")
        if parts:
            messagebox.showinfo("Lưu thành công",
                                "\n".join(parts), parent=self)
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  SourceSelectorDialog — Chọn nguồn tạo đề (fixed layout)
# ══════════════════════════════════════════════════════════════════════════════

class SourceSelectorDialog(tk.Toplevel):
    """Chọn phương thức tạo đề: AI mới / NHCH / Kết hợp."""

    MODES = [
        ("ai_only",   "✨  Tạo mới hoàn toàn bằng AI",
         "AI sẽ tạo câu hỏi hoàn toàn mới theo ma trận. Không dùng NHCH."),
        ("bank_only", "📚  Lấy 100% từ Ngân hàng câu hỏi",
         "Chỉ lấy câu từ NHCH đã lưu. Nếu thiếu câu, sẽ thông báo."),
        ("mixed",     "🔀  Kết hợp AI + Ngân hàng câu hỏi",
         "Ưu tiên lấy từ NHCH, câu còn thiếu sẽ được AI tạo mới."),
    ]

    def __init__(self, parent, on_confirm_cb: Callable):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("🎯  Chọn phương thức tạo đề")
        self.resizable(True, False)
        self.grab_set()
        self._cb          = on_confirm_cb
        self._mode        = tk.StringVar(value="ai_only")
        self._bank_ratio  = tk.IntVar(value=50)
        self._build()
        # Căn giữa + đặt kích thước sau khi build xong
        self.update_idletasks()
        W, H = max(self.winfo_reqwidth(), 480), max(self.winfo_reqheight(), 340)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

    def _build(self) -> None:
        # Dùng Canvas + Scrollbar để đảm bảo không bị cắt nút
        outer = tk.Frame(self); outer.pack(fill="both", expand=True)

        tk.Label(outer, text="🎯  Chọn phương thức tạo đề",
                 font=("Segoe UI", 12, "bold"), fg=BLUE).pack(pady=(14, 8), padx=16)

        for mode, title, desc in self.MODES:
            f = tk.Frame(outer, relief="ridge", bd=1, padx=10, pady=8,
                          cursor="hand2")
            f.pack(fill="x", padx=16, pady=4)
            rb = ttk.Radiobutton(f, text=title, variable=self._mode,
                                  value=mode, style="TRadiobutton")
            rb.pack(anchor="w")
            tk.Label(f, text=desc, fg="#555",
                     font=("Segoe UI", 8), justify="left",
                     wraplength=420).pack(anchor="w", padx=20)
            # Kích vào cả frame để chọn
            f.bind("<Button-1>", lambda e, m=mode: self._mode.set(m))

        # Tỉ lệ mixed
        ratio_f = tk.Frame(outer, padx=16, pady=4)
        ratio_f.pack(fill="x")
        tk.Label(ratio_f, text="% câu lấy từ NHCH (chế độ Kết hợp):",
                 font=("Segoe UI", 9)).pack(side="left")
        ttk.Spinbox(ratio_f, from_=10, to=90, increment=10,
                    textvariable=self._bank_ratio, width=6).pack(side="left", padx=6)
        tk.Label(ratio_f, text="(phần còn lại AI tạo mới)",
                 fg="#888", font=("Segoe UI", 8)).pack(side="left")

        # Buttons — luôn hiển thị
        btn_f = tk.Frame(outer, pady=14)
        btn_f.pack()
        tk.Button(btn_f, text="  ▶  Xác nhận  ",
                   font=("Segoe UI", 10, "bold"),
                   bg=BLUE, fg="white", activebackground="#163d6b",
                   relief="flat", cursor="hand2", padx=14, pady=7,
                   command=self._confirm).pack(side="left", padx=8)
        tk.Button(btn_f, text="  Hủy  ", font=("Segoe UI", 9),
                  bg="#6B7280", fg="white", activebackground="#4B5563",
                  relief="flat", cursor="hand2", pady=7,
                  command=self.destroy).pack(side="left", padx=4)

    def _confirm(self) -> None:
        mode  = self._mode.get()
        ratio = (self._bank_ratio.get() if mode == "mixed"
                 else (0 if mode == "ai_only" else 100))
        self.destroy()
        self._cb(mode, ratio)


# ══════════════════════════════════════════════════════════════════════════════
#  ReviewDialogV2 — Kết quả QC với nút AI sửa tất cả
# ══════════════════════════════════════════════════════════════════════════════

class ReviewDialogV2(tk.Toplevel):
    """Kết quả QC + nút AI sửa từng câu / tất cả câu không đạt."""

    def __init__(self, parent, exam: ExamData,
                 questions: list[Question], reviews: list[dict],
                 get_ai_call: Optional[Callable] = None,
                 subject: str = "", grade: str = ""):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("📊  Kết quả kiểm tra chất lượng")
        self.geometry("980x580")
        self.resizable(True, True)
        self.grab_set()
        self._exam      = exam
        self._questions = questions
        self._reviews   = reviews
        self._get_ai    = get_ai_call
        self._subject   = subject
        self._grade     = grade
        for q, r in zip(questions, reviews):
            q._review = r
        self._build()

    def _build(self) -> None:
        # Toolbar
        tb = tk.Frame(self, bg="#E8EDF2"); tb.pack(fill="x", padx=6, pady=4)
        ok   = sum(1 for r in self._reviews if r.get("ok", True))
        fail = len(self._reviews) - ok
        avg  = sum(r.get("score", 5) for r in self._reviews) / max(len(self._reviews), 1)

        tk.Label(tb,
                 text=f"✅ {ok}/{len(self._reviews)} câu đạt  │  "
                      f"❌ {fail} câu cần sửa  │  Điểm TB: {avg:.1f}/10",
                 font=("Segoe UI", 10, "bold"), fg=BLUE,
                 bg="#E8EDF2").pack(side="left", padx=8)

        if self._get_ai and fail > 0:
            tk.Button(tb, text=f"🤖  AI sửa tất cả {fail} câu không đạt",
                       font=("Segoe UI", 9, "bold"),
                       bg="#EF4444", fg="white", activebackground="#DC2626",
                       relief="flat", cursor="hand2", padx=10, pady=4,
                       command=self._ai_fix_all).pack(side="right", padx=4)

        ttk.Button(tb, text="📥  Xuất CSV",
                   command=self._export_csv).pack(side="right", padx=4)

        # Treeview
        cols = ("Câu", "Loại", "Mức", "Điểm", "Đạt?", "Vấn đề", "Gợi ý sửa")
        self._tree = ttk.Treeview(self, columns=cols, show="headings", height=16)
        ws = {"Câu": 50, "Loại": 80, "Mức": 50, "Điểm": 60,
              "Đạt?": 50, "Vấn đề": 200, "Gợi ý sửa": 260}
        for c in cols:
            self._tree.heading(c, text=c)
            self._tree.column(c, width=ws[c], minwidth=40)

        for i, (q, r) in enumerate(zip(self._questions, self._reviews), 1):
            ok_str = "✅" if r.get("ok", True) else "❌"
            tag    = "ok" if r.get("ok", True) else "fail"
            self._tree.insert("", "end", iid=str(i), values=(
                i,
                TYPE_LABELS.get(q.qtype, q.qtype),
                q.level,
                f"{r.get('score', 5)}/10",
                ok_str,
                r.get("issue", "")[:70],
                r.get("tip", "")[:120],
            ), tags=(tag,))

        self._tree.tag_configure("fail", foreground="#CC0000", background="#FFF0F0")
        self._tree.tag_configure("ok",   foreground="#006600")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=4)
        vsb.pack(side="left", fill="y", pady=4)

        # Bind double click để sửa câu
        self._tree.bind("<Double-1>", self._on_dblclick_fix)

        # Right panel: hint cho câu đang chọn
        rp = tk.Frame(self, width=260); rp.pack(side="left", fill="y", padx=4)
        rp.pack_propagate(False)
        tk.Label(rp, text="💡 Gợi ý sửa câu đang chọn:",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(8, 4))
        self._detail_lbl = tk.Label(rp, text="Nhấn đúp vào câu để mở dialog sửa.",
                                     font=("Segoe UI", 9), fg="#555",
                                     wraplength=240, justify="left")
        self._detail_lbl.pack(anchor="w", padx=4)

        self._tree.bind("<<TreeviewSelect>>", self._on_select_show_hint)

        # Bottom
        bot = tk.Frame(self); bot.pack(side="bottom", pady=6)
        ttk.Button(bot, text="Đóng", command=self.destroy).pack(
            side="left", padx=8, ipadx=14)

    def _on_select_show_hint(self, _event) -> None:
        sel = self._tree.selection()
        if not sel: return
        idx = int(sel[0]) - 1
        if 0 <= idx < len(self._reviews):
            r    = self._reviews[idx]
            hint = r.get("tip", "") or r.get("issue", "") or "Không có gợi ý cụ thể."
            self._detail_lbl.config(text=f"Câu {idx+1}:\n\n{hint}\n\nNhấn đúp để mở sửa.")

    def _on_dblclick_fix(self, _event) -> None:
        """Mở dialog sửa câu đang chọn, truyền gợi ý từ QC."""
        sel = self._tree.selection()
        if not sel: return
        idx = int(sel[0]) - 1
        if not (0 <= idx < len(self._questions)): return

        q   = self._questions[idx]
        rev = self._reviews[idx]
        tip = rev.get("tip", "") or rev.get("issue", "")

        def _on_save(updated_q: Question) -> None:
            self._questions[idx] = updated_q

        EditQuestionDialogV2(
            self, q,
            on_save_cb   = _on_save,
            get_ai_call  = self._get_ai,
            subject      = self._subject,
            grade        = self._grade,
            qc_issues    = tip,
        )

    def _ai_fix_all(self) -> None:
        """Tự động gọi AI sửa tất cả câu không đạt (chạy nền)."""
        failed = [(i, q, r) for i, (q, r) in enumerate(
            zip(self._questions, self._reviews)) if not r.get("ok", True)]
        if not failed:
            messagebox.showinfo("Không có câu cần sửa", "Tất cả câu đã đạt chất lượng!",
                                parent=self); return

        if not messagebox.askyesno("AI sửa tất cả",
            f"Tự động gọi AI sửa {len(failed)} câu không đạt?\n\n"
            "Quá trình có thể mất vài phút. Tiếp tục?", parent=self): return

        FMT = {"TN": _FMT_TN, "DS": _FMT_DS, "TLN": _FMT_TLN, "TL": _FMT_TL}
        self._prog_win = _FixProgressWindow(self, total=len(failed))

        def _fix_all_thread():
            try:
                ai_call = self._get_ai()
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda m=err_msg: messagebox.showerror(
                    "Lỗi AI", m, parent=self))
                return

            for done_idx, (i, q, r) in enumerate(failed):
                tip = r.get("tip", "") or r.get("issue", "")
                fmt = _fill(FMT.get(q.qtype, _FMT_TL),
                             level=q.level, topic=q.topic, points=q.points)
                prompt = (
                    f"Bạn là giáo viên Toán THPT Việt Nam.\n"
                    f"Hãy SỬA câu hỏi sau theo gợi ý QC.\n"
                    f"Môn: {self._subject} — Lớp: {self._grade}\n"
                    f"Loại: {TYPE_LABELS.get(q.qtype,q.qtype)} | "
                    f"Mức: {q.level} | Chủ đề: {q.topic}\n\n"
                    f"NỘI DUNG:\n{q.question}\n\n"
                    f"VẤN ĐỀ TỪ QC:\n{tip}\n\n"
                    f"Hãy sửa lại và đảm bảo dùng ${{...}}$ cho công thức.\n"
                    f"Trả về theo định dạng:\n{fmt}"
                )
                try:
                    raw   = ai_call(prompt)
                    fixed = parse_one_question(raw)
                    if fixed and not fixed._error:
                        self._questions[i] = fixed
                        self.after(0, lambda idx=i: self._mark_fixed_in_tree(idx))
                except Exception:
                    pass
                self.after(0, lambda d=done_idx+1: self._prog_win.update(d))

            self.after(0, self._prog_win.done)

        threading.Thread(target=_fix_all_thread, daemon=True).start()

    def _mark_fixed_in_tree(self, idx: int) -> None:
        iid = str(idx + 1)
        try:
            vals = list(self._tree.item(iid)["values"])
            vals[4] = "🔧"
            self._tree.item(iid, values=vals, tags=("fixed",))
            self._tree.tag_configure("fixed",
                                      foreground="#7C3AED", background="#F5F3FF")
        except Exception:
            pass

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"BaoCaoQC_{self._exam.subject}{self._exam.grade}.csv",
            parent=self)
        if not path: return
        try:
            lines = ["Câu,Loại,Mức,Điểm,Đạt?,Vấn đề,Gợi ý sửa"]
            for i, (q, r) in enumerate(zip(self._questions, self._reviews), 1):
                ok = "OK" if r.get("ok", True) else "FAIL"
                lines.append(
                    f"{i},{q.qtype},{q.level},{r.get('score',5)},{ok},"
                    f"\"{r.get('issue','')}\",\"{r.get('tip','')}\"")
            Path(path).write_text("\n".join(lines), encoding="utf-8-sig")
            messagebox.showinfo("Xuất xong", f"Đã lưu tại:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)


class _FixProgressWindow(tk.Toplevel):
    def __init__(self, parent, total: int):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("🤖 AI đang sửa câu hỏi…")
        self.geometry("320x110")
        self.resizable(False, False)
        self.grab_set()
        self._total = total
        tk.Label(self, text="AI đang tự động sửa các câu không đạt…",
                 font=("Segoe UI", 9)).pack(pady=(16, 6))
        self._pb = ttk.Progressbar(self, maximum=total, length=280)
        self._pb.pack(pady=4)
        self._lbl = tk.Label(self, text=f"0 / {total}", font=("Segoe UI", 9))
        self._lbl.pack()

    def update(self, done: int) -> None:
        self._pb.config(value=done)
        self._lbl.config(text=f"{done} / {self._total}")

    def done(self) -> None:
        messagebox.showinfo("Hoàn tất",
                             f"AI đã sửa xong {self._total} câu.\n"
                             "Kiểm tra lại và nhấn 'Áp dụng kết quả' ở Tab ⑤.",
                             parent=self)
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  SessionDialog (giữ nguyên)
# ══════════════════════════════════════════════════════════════════════════════

class SessionDialog(tk.Toplevel):
    """Dialog chọn phiên làm việc gần đây."""
    def __init__(self, parent, sessions: list[dict], on_select_cb: Callable):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("📂  Chọn phiên làm việc")
        self.geometry("600x380")
        self.grab_set()
        self._cb = on_select_cb
        self._sessions = sessions
        self._build()

    def _build(self):
        tk.Label(self, text="Phiên làm việc gần đây",
                 font=("Segoe UI", 11, "bold"), fg=BLUE).pack(pady=(12, 6))
        cols = ("Tên", "Môn", "Lớp", "Số câu", "Ngày lưu")
        tree = ttk.Treeview(self, columns=cols, show="headings", height=12)
        for c, w in zip(cols, [200, 80, 60, 70, 140]):
            tree.heading(c, text=c); tree.column(c, width=w)
        for s in self._sessions:
            tree.insert("", "end", iid=s.get("path",""), values=(
                s.get("name",""),
                s.get("subject",""),
                s.get("grade",""),
                s.get("n_questions",0),
                s.get("saved_at","")[:16],
            ))
        tree.pack(fill="both", expand=True, padx=8, pady=4)
        tree.bind("<Double-1>", lambda e: self._select(tree))
        btn_f = tk.Frame(self); btn_f.pack(pady=6)
        tk.Button(btn_f, text="  📂 Mở  ", font=("Segoe UI", 9, "bold"),
                  bg="#3B82F6", fg="white", activebackground="#2563EB",
                  relief="flat", cursor="hand2", pady=4,
                  command=lambda: self._select(tree)).pack(side="left", padx=6)
        tk.Button(btn_f, text="  Hủy  ", font=("Segoe UI", 9),
                  bg="#6B7280", fg="white", activebackground="#4B5563",
                  relief="flat", cursor="hand2", pady=4,
                  command=self.destroy).pack(side="left", padx=4)

    def _select(self, tree):
        sel = tree.selection()
        if not sel: return
        self.destroy()
        self._cb(str(sel[0]))
