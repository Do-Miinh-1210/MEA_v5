"""
v5/edit_question.py — Dialog sửa câu hỏi thuần CustomTkinter (Alpha 10).

Thay thế việc reuse v4 EditQuestionDialogV2 (Tkinter) — UI nhất quán với
phần còn lại của v5.

Tính năng:
    • Selector qtype / level / topic / points (live cập nhật ID)
    • Editor câu hỏi (CTkTextbox)
    • Vùng đáp án động theo loại:
        TN  → 4 option A/B/C/D + chọn đáp án đúng (radio)
        DS  → 4 ý a/b/c/d + mỗi ý Đúng/Sai (switch)
        TLN → 1 ô đáp án ngắn
        TL  → chỉ lời giải
    • Editor lời giải
    • Multi-image: ảnh đề + ảnh lời giải (v5.image_fields)
    • Nút 🤖 AI sửa theo gợi ý QC (nếu có get_ai_call)
    • Live structured ID (compute_structured_id)
    • ESC để đóng, scroll mượt

Usage:
    EditQuestionDialogCTk(parent, question, on_save_cb=fn,
                           get_ai_call=factory, subject="Toán", grade="12",
                           qc_issues="...")
"""
from __future__ import annotations

import threading
from typing import Callable, Optional

import customtkinter as ctk
from tkinter import messagebox

QTYPES = ["TN", "DS", "TLN", "TL"]
QTYPE_LABELS = {"TN": "Trắc nghiệm", "DS": "Đúng – Sai",
                "TLN": "Trả lời ngắn", "TL": "Tự luận"}
LEVELS = ["NB", "TH", "VD", "VDC"]
LEVEL_LABELS = {"NB": "Nhận biết", "TH": "Thông hiểu",
                "VD": "Vận dụng", "VDC": "Vận dụng cao"}
DS_KEYS = ["a", "b", "c", "d"]
TN_KEYS = ["A", "B", "C", "D"]


class EditQuestionDialogCTk(ctk.CTkToplevel):
    """Dialog sửa câu hỏi — pure CTk, full screen-friendly."""

    def __init__(self, parent, question, *,
                  on_save_cb: Callable,
                  get_ai_call: Optional[Callable] = None,
                  subject: str = "Toán", grade: str = "12",
                  qc_issues: str = ""):
        super().__init__(parent)
        self._q = question
        self._save_cb = on_save_cb
        self._get_ai = get_ai_call
        self._subject = subject
        self._grade = grade
        self._qc_issues = qc_issues

        self.title(f"✏️ Sửa câu — {QTYPE_LABELS.get(question.qtype, question.qtype)}")
        # Mở gần full màn hình
        try:
            sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
            w = min(1180, int(sw * 0.85)); h = min(820, int(sh * 0.9))
            self.geometry(f"{w}x{h}+{(sw-w)//2}+{max(0,(sh-h)//2-20)}")
        except Exception:
            self.geometry("1180x800")
        self.minsize(900, 600)

        self._q_images = _norm_images(getattr(question, "question_image", ""))
        self._sol_images = _norm_images(getattr(question, "solution_image", ""))

        self._build()
        self.bind("<Escape>", lambda e: self._on_close())
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        try: self.grab_set(); self.focus_force()
        except Exception: pass

    # ── Build ───────────────────────────────────────────────────────────────
    def _build(self):
        # Header với live ID
        hdr = ctk.CTkFrame(self, fg_color=("#1F497D", "#0B1F35"),
                             corner_radius=0, height=46)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        self._id_var = ctk.StringVar()
        ctk.CTkLabel(hdr, textvariable=self._id_var,
                      font=("Segoe UI", 12, "bold"),
                      text_color="white").pack(side="left", padx=14, pady=8)
        if self._qc_issues:
            ctk.CTkLabel(hdr, text="⚠ Có gợi ý QC",
                          font=("Segoe UI", 10),
                          text_color="#FCD34D").pack(side="right", padx=14)

        # Body: 2 cột (form trái scrollable | meta + ảnh + AI phải)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2, minsize=320)
        body.grid_rowconfigure(0, weight=1)

        self._left = ctk.CTkScrollableFrame(body, fg_color=("#FFFFFF", "#162033"))
        self._left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._right = ctk.CTkScrollableFrame(body, fg_color=("#F8FAFC", "#0F1A2E"))
        self._right.grid(row=0, column=1, sticky="nsew")

        self._build_meta()
        self._build_question_editor()
        self._answer_zone = ctk.CTkFrame(self._left, fg_color="transparent")
        self._answer_zone.pack(fill="x", padx=10, pady=(4, 8))
        self._build_answer_zone()
        self._build_solution_editor()

        self._build_right_panel()

        # Footer buttons
        ftr = ctk.CTkFrame(self, fg_color="transparent")
        ftr.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkButton(ftr, text="✓ Lưu thay đổi", width=160, height=38,
                        fg_color=("#10B981", "#065F46"),
                        hover_color=("#059669", "#047857"),
                        font=("Segoe UI", 13, "bold"),
                        command=self._on_save).pack(side="right", padx=4)
        ctk.CTkButton(ftr, text="Huỷ", width=100, height=38,
                        fg_color=("#6B7280", "#374151"),
                        command=self._on_close).pack(side="right", padx=4)

        self._refresh_id()

    def _build_meta(self):
        card = ctk.CTkFrame(self._left, fg_color=("#F3F4F6", "#1E2A40"),
                              corner_radius=8)
        card.pack(fill="x", padx=10, pady=(10, 4))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(row, text="Loại:").pack(side="left", padx=(0, 4))
        self._qtype_var = ctk.StringVar(value=self._q.qtype)
        ctk.CTkOptionMenu(row, values=QTYPES, variable=self._qtype_var, width=70,
                            command=self._on_qtype_change).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(row, text="Mức:").pack(side="left", padx=(0, 4))
        self._level_var = ctk.StringVar(value=self._q.level)
        ctk.CTkOptionMenu(row, values=LEVELS, variable=self._level_var, width=72,
                            command=lambda _: self._refresh_id()).pack(side="left", padx=(0, 12))

        ctk.CTkLabel(row, text="Điểm:").pack(side="left", padx=(0, 4))
        self._points_var = ctk.StringVar(value=str(getattr(self._q, "points", 0.25)))
        ctk.CTkEntry(row, textvariable=self._points_var, width=60).pack(side="left")

        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(row2, text="Chủ đề:").pack(side="left", padx=(0, 4))
        self._topic_var = ctk.StringVar(value=getattr(self._q, "topic", ""))
        ent = ctk.CTkEntry(row2, textvariable=self._topic_var)
        ent.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._topic_var.trace_add("write", lambda *_: self._refresh_id())

    def _build_question_editor(self):
        ctk.CTkLabel(self._left, text="Nội dung câu hỏi:",
                      font=("Segoe UI", 12, "bold"), anchor="w"
                      ).pack(fill="x", padx=10, pady=(8, 2))
        self._q_text = ctk.CTkTextbox(self._left, height=160,
                                        font=("Segoe UI", 12), wrap="word")
        self._q_text.pack(fill="x", padx=10, pady=2)
        self._q_text.insert("1.0", getattr(self._q, "question", "") or "")

    def _build_answer_zone(self):
        """Render vùng đáp án theo qtype hiện tại."""
        for c in self._answer_zone.winfo_children():
            c.destroy()
        qtype = self._qtype_var.get()
        if qtype == "TN":
            self._build_tn_options()
        elif qtype == "DS":
            self._build_ds_items()
        elif qtype == "TLN":
            self._build_tln_answer()
        else:  # TL
            ctk.CTkLabel(self._answer_zone,
                          text="(Tự luận — chỉ cần nhập lời giải bên dưới)",
                          text_color="gray", font=("Segoe UI", 11)
                          ).pack(anchor="w")

    def _build_tn_options(self):
        ctk.CTkLabel(self._answer_zone, text="Phương án (chọn đáp án đúng):",
                      font=("Segoe UI", 12, "bold"), anchor="w"
                      ).pack(fill="x", pady=(0, 4))
        self._tn_answer_var = ctk.StringVar(
            value=(getattr(self._q, "answer", "") or "A").strip()[:1] or "A")
        self._tn_opt_entries = {}
        opts = getattr(self._q, "options", None) or {}
        for k in TN_KEYS:
            row = ctk.CTkFrame(self._answer_zone, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkRadioButton(row, text=k, variable=self._tn_answer_var,
                                value=k, width=44).pack(side="left", padx=(0, 6))
            ent = ctk.CTkTextbox(row, height=52, font=("Segoe UI", 11), wrap="word")
            ent.pack(side="left", fill="x", expand=True)
            self._set_text_widget(ent, opts.get(k, "") or "")
            self._tn_opt_entries[k] = ent

    def _build_ds_items(self):
        ctk.CTkLabel(self._answer_zone, text="Các ý (Đúng/Sai):",
                      font=("Segoe UI", 12, "bold"), anchor="w"
                      ).pack(fill="x", pady=(0, 4))
        self._ds_item_entries = {}
        self._ds_answer_vars = {}
        items = getattr(self._q, "items", None) or {}
        answers = getattr(self._q, "answers", None) or {}
        for k in DS_KEYS:
            row = ctk.CTkFrame(self._answer_zone, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{k})", width=28).pack(side="left")
            ent = ctk.CTkTextbox(row, height=56, font=("Segoe UI", 11), wrap="word")
            ent.pack(side="left", fill="x", expand=True, padx=(0, 6))
            self._set_text_widget(ent, items.get(k, "") or "")
            self._ds_item_entries[k] = ent
            var = ctk.BooleanVar(value=bool(answers.get(k, False)))
            self._ds_answer_vars[k] = var
            ctk.CTkSwitch(row, text="Đúng", variable=var, width=60
                            ).pack(side="left")

    def _build_tln_answer(self):
        ctk.CTkLabel(self._answer_zone, text="Đáp án ngắn:",
                      font=("Segoe UI", 12, "bold"), anchor="w"
                      ).pack(fill="x", pady=(0, 4))
        self._tln_answer_var = ctk.StringVar(
            value=getattr(self._q, "answer", "") or "")
        ctk.CTkEntry(self._answer_zone, textvariable=self._tln_answer_var
                      ).pack(fill="x")

    def _build_solution_editor(self):
        ctk.CTkLabel(self._left, text="Lời giải:",
                      font=("Segoe UI", 12, "bold"), anchor="w"
                      ).pack(fill="x", padx=10, pady=(8, 2))
        self._sol_text = ctk.CTkTextbox(self._left, height=170,
                                          font=("Segoe UI", 12), wrap="word")
        self._sol_text.pack(fill="x", padx=10, pady=(2, 10))
        self._sol_text.insert("1.0", getattr(self._q, "solution", "") or "")

    @staticmethod
    def _get_text_widget(widget) -> str:
        if isinstance(widget, ctk.CTkTextbox):
            return widget.get("1.0", "end").strip()
        return str(widget.get() or "").strip()

    @staticmethod
    def _set_text_widget(widget, value: str) -> None:
        text = str(value or "")
        if isinstance(widget, ctk.CTkTextbox):
            widget.delete("1.0", "end")
            widget.insert("1.0", text)
            return
        widget.delete(0, "end")
        widget.insert(0, text)

    # ── Right panel: ảnh + AI ────────────────────────────────────────────
    def _build_right_panel(self):
        # QC issues
        if self._qc_issues:
            qc_card = ctk.CTkFrame(self._right,
                                     fg_color=("#FEF2F2", "#3F1D1D"),
                                     corner_radius=8)
            qc_card.pack(fill="x", padx=8, pady=(8, 4))
            ctk.CTkLabel(qc_card, text="⚠ Gợi ý QC:",
                          font=("Segoe UI", 11, "bold"),
                          text_color=("#DC2626", "#FCA5A5"), anchor="w"
                          ).pack(fill="x", padx=8, pady=(6, 2))
            ctk.CTkLabel(qc_card, text=self._qc_issues[:400],
                          font=("Segoe UI", 10), wraplength=280,
                          justify="left", anchor="w",
                          text_color=("#7F1D1D", "#FCA5A5")
                          ).pack(fill="x", padx=8, pady=(0, 6))

        # AI fix
        if self._get_ai:
            ai_card = ctk.CTkFrame(self._right,
                                     fg_color=("#F5F3FF", "#2E1065"),
                                     corner_radius=8)
            ai_card.pack(fill="x", padx=8, pady=4)
            ctk.CTkLabel(ai_card, text="🤖 AI sửa câu",
                          font=("Segoe UI", 12, "bold"), anchor="w"
                          ).pack(fill="x", padx=8, pady=(6, 2))
            ctk.CTkLabel(ai_card,
                          text="AI đọc câu + gợi ý QC → đề xuất bản sửa.",
                          font=("Segoe UI", 10), text_color="gray",
                          wraplength=280, justify="left", anchor="w"
                          ).pack(fill="x", padx=8, pady=(0, 4))
            self._ai_btn = ctk.CTkButton(
                ai_card, text="🤖 AI sửa theo gợi ý", height=34,
                fg_color=("#7C3AED", "#5B21B6"),
                hover_color=("#6D28D9", "#4C1D95"),
                command=self._ai_fix)
            self._ai_btn.pack(fill="x", padx=8, pady=(0, 4))
            self._ai_status = ctk.CTkLabel(ai_card, text="",
                                             font=("Segoe UI", 9),
                                             text_color="gray", anchor="w")
            self._ai_status.pack(fill="x", padx=8, pady=(0, 6))

        # Ảnh đề
        self._build_image_section(self._right, "Ảnh đề bài",
                                    self._q_images, "q")
        # Ảnh lời giải
        self._build_image_section(self._right, "Ảnh lời giải",
                                    self._sol_images, "sol")

    def _build_image_section(self, parent, title, paths_list, kind):
        card = ctk.CTkFrame(parent, fg_color=("#FFFFFF", "#162033"),
                              corner_radius=8)
        card.pack(fill="x", padx=8, pady=4)
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=8, pady=(6, 2))
        ctk.CTkLabel(head, text=f"🖼 {title}",
                      font=("Segoe UI", 11, "bold")).pack(side="left")
        ctk.CTkButton(head, text="+ Thêm", width=70, height=26,
                        command=lambda: self._add_images(kind)
                        ).pack(side="right")
        lst = ctk.CTkFrame(card, fg_color="transparent")
        lst.pack(fill="x", padx=8, pady=(0, 6))
        setattr(self, f"_imglist_{kind}", lst)
        self._render_image_list(kind)

    def _render_image_list(self, kind):
        lst = getattr(self, f"_imglist_{kind}")
        for c in lst.winfo_children():
            c.destroy()
        paths = self._q_images if kind == "q" else self._sol_images
        if not paths:
            ctk.CTkLabel(lst, text="(chưa có ảnh)", text_color="gray",
                          font=("Segoe UI", 9)).pack(anchor="w")
            return
        from pathlib import Path
        for i, p in enumerate(paths):
            row = ctk.CTkFrame(lst, fg_color=("#F3F4F6", "#1E2A40"),
                                 corner_radius=4)
            row.pack(fill="x", pady=1)
            name = p if p.startswith("http") else Path(p).name
            ctk.CTkLabel(row, text=f"{i+1}. {name[:30]}", anchor="w",
                          font=("Segoe UI", 9)
                          ).pack(side="left", padx=6, fill="x", expand=True)
            ctk.CTkButton(row, text="✕", width=24, height=22,
                            fg_color="transparent", text_color="#EF4444",
                            hover_color=("#FEE2E2", "#7F1D1D"),
                            command=lambda idx=i: self._remove_image(kind, idx)
                            ).pack(side="right", padx=2)

    def _add_images(self, kind):
        try:
            from v5.image_fields import pick_and_copy_images
            new = pick_and_copy_images(parent=self)
            if not new: return
            target = self._q_images if kind == "q" else self._sol_images
            target.extend(new)
            self._render_image_list(kind)
        except Exception as e:
            messagebox.showerror("Lỗi thêm ảnh", str(e), parent=self)

    def _remove_image(self, kind, idx):
        target = self._q_images if kind == "q" else self._sol_images
        if 0 <= idx < len(target):
            target.pop(idx)
            self._render_image_list(kind)

    # ── Live ID ──────────────────────────────────────────────────────────
    def _refresh_id(self):
        try:
            # Sync field vào q tạm để compute
            self._q.qtype = self._qtype_var.get()
            self._q.level = self._level_var.get()
            self._q.topic = self._topic_var.get()
            from core.models import compute_structured_id
            qid = compute_structured_id(self._q, str(self._grade))
            self._id_var.set(f"ID: {qid}   ·   {QTYPE_LABELS.get(self._q.qtype, '')}")
        except Exception:
            self._id_var.set(f"ID: {getattr(self._q, 'question_id', '?')}")

    def _on_qtype_change(self, _=None):
        self._build_answer_zone()
        self._refresh_id()

    # ── AI fix ─────────────────────────────────────────────────────────────
    def _ai_fix(self):
        if not self._get_ai:
            return
        self._ai_btn.configure(state="disabled", text="⏳ AI đang sửa…")
        self._ai_status.configure(text="Đang gọi AI...", text_color="#3B82F6")

        # Snapshot current edits vào q
        self._collect_into_question(self._q)
        qc = self._qc_issues

        def _worker():
            try:
                ai_call = self._get_ai() if callable(self._get_ai) else None
                if not ai_call:
                    raise RuntimeError("Không lấy được AI call (cấu hình key?)")
                from core.ai_reviewer import fix_question
                # fix_question(q, subject, grade, ai_call) -> (Question, dict)
                result = fix_question(self._q, self._subject,
                                        str(self._grade), ai_call)
                fixed_q = result[0] if isinstance(result, tuple) else result
                self.after(0, lambda: self._on_ai_done(fixed_q, None))
            except Exception as e:
                err = str(e)
                self.after(0, lambda: self._on_ai_done(None, err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_ai_done(self, fixed, err):
        try:
            if not self.winfo_exists(): return
        except Exception: return
        self._ai_btn.configure(state="normal", text="🤖 AI sửa theo gợi ý")
        if err:
            self._ai_status.configure(text=f"✘ {err[:60]}", text_color="#EF4444")
            return
        if not fixed:
            self._ai_status.configure(text="✘ AI không trả về", text_color="#EF4444")
            return
        # Nạp lại UI từ fixed question
        self._reload_from_question(fixed)
        self._ai_status.configure(text="✓ Đã áp dụng bản AI sửa",
                                    text_color="#10B981")

    def _reload_from_question(self, q):
        """Cập nhật toàn bộ field UI từ 1 Question object."""
        try:
            self._q_text.delete("1.0", "end")
            self._q_text.insert("1.0", getattr(q, "question", "") or "")
            self._sol_text.delete("1.0", "end")
            self._sol_text.insert("1.0", getattr(q, "solution", "") or "")
            self._qtype_var.set(q.qtype)
            self._level_var.set(q.level)
            self._build_answer_zone()
            # Re-fill answer zone từ q
            qtype = q.qtype
            if qtype == "TN":
                opts = getattr(q, "options", {}) or {}
                for k, ent in getattr(self, "_tn_opt_entries", {}).items():
                    self._set_text_widget(ent, opts.get(k, "") or "")
                if getattr(q, "answer", ""):
                    self._tn_answer_var.set(q.answer.strip()[:1])
            elif qtype == "DS":
                items = getattr(q, "items", {}) or {}
                answers = getattr(q, "answers", {}) or {}
                for k, ent in getattr(self, "_ds_item_entries", {}).items():
                    self._set_text_widget(ent, items.get(k, "") or "")
                for k, var in getattr(self, "_ds_answer_vars", {}).items():
                    var.set(bool(answers.get(k, False)))
            elif qtype == "TLN":
                if hasattr(self, "_tln_answer_var"):
                    self._tln_answer_var.set(getattr(q, "answer", "") or "")
            self._refresh_id()
        except Exception as e:
            print(f"reload_from_question fail: {e}")

    # ── Save ─────────────────────────────────────────────────────────────
    def _collect_into_question(self, q):
        """Đọc toàn bộ field UI → ghi vào Question object."""
        q.qtype = self._qtype_var.get()
        q.level = self._level_var.get()
        q.topic = self._topic_var.get().strip()
        try: q.points = float(self._points_var.get())
        except Exception: q.points = 0.25
        q.question = self._q_text.get("1.0", "end").strip()
        q.solution = self._sol_text.get("1.0", "end").strip()

        qtype = q.qtype
        if qtype == "TN":
            q.options = {k: self._get_text_widget(e)
                          for k, e in getattr(self, "_tn_opt_entries", {}).items()}
            q.answer = self._tn_answer_var.get()
            q.items = {}; q.answers = {}
        elif qtype == "DS":
            q.items = {k: self._get_text_widget(e)
                        for k, e in getattr(self, "_ds_item_entries", {}).items()}
            q.answers = {k: bool(v.get())
                          for k, v in getattr(self, "_ds_answer_vars", {}).items()}
            q.options = {}; q.answer = ""
        elif qtype == "TLN":
            q.answer = (getattr(self, "_tln_answer_var", None).get()
                         if hasattr(self, "_tln_answer_var") else "")
            q.options = {}; q.items = {}; q.answers = {}
        else:  # TL
            q.options = {}; q.items = {}; q.answers = {}; q.answer = ""

        # Images → serialize về '|'-joined cho tương thích legacy
        from v5.image_fields import serialize_image_field
        q.question_image = serialize_image_field(self._q_images)
        q.solution_image = serialize_image_field(self._sol_images)

    def _on_save(self):
        q = self._q
        self._collect_into_question(q)
        if not q.question:
            if not messagebox.askyesno("Câu hỏi trống",
                "Nội dung câu hỏi đang trống. Vẫn lưu?", parent=self):
                return
        # Gán structured ID nếu chưa có
        try:
            if not (getattr(q, "question_id", "") or "").strip():
                from core.models import compute_structured_id
                q.question_id = compute_structured_id(q, str(self._grade))
        except Exception: pass
        try:
            self._save_cb(q)
            self._on_close()
        except Exception as e:
            messagebox.showerror("Lỗi lưu", str(e), parent=self)

    def _on_close(self):
        try: self.grab_release()
        except Exception: pass
        try: self.destroy()
        except Exception: pass


def _norm_images(value) -> list[str]:
    try:
        from v5.image_fields import normalize_image_field
        return normalize_image_field(value)
    except Exception:
        if not value: return []
        if isinstance(value, list): return list(value)
        return [p for p in str(value).split("|") if p.strip()]
