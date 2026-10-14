"""
v5/smart_prompt.py — Smart Prompt dialog (CTk port của ui/dialog_smart_prompt.py).

2 mode (segmented button):
    📄 Tạo đề     — nhập prompt tiếng Việt → smart_prompt_to_matrix → ma trận
                     + follow-up chat-style → "Áp dụng vào Tạo đề"
    ✏️ 1 câu hỏi  — nhập prompt → AI sinh 1 câu → preview → "Thêm vào NHCH"

Reuse v4 core:
    core.smart_prompt — smart_prompt_to_matrix, followup_modify_matrix,
                         clone_matrix, diff_matrices, format_matrix_diff
    services.ai_service + key_manager — AI callable

Mở qua:
    Ctrl+T → "smart prompt"  hoặc  nút trong Exam Create view.
"""
from __future__ import annotations

import threading
from typing import Callable

import customtkinter as ctk
from tkinter import messagebox


def _resolve_ai_call():
    """Lấy AI callable từ key đã lưu (giống exam_create._resolve_ai_call)."""
    try:
        from services.key_manager import get_key_manager
        from services.ai_service import create_ai_service
        from services.retry_service import split_keys
        km = get_key_manager()
        for prov in ("Google Gemini", "Anthropic Claude", "DeepSeek", "OpenAI"):
            key = km.load(prov)
            if key:
                keys = key if isinstance(key, list) else split_keys(key)
                model = ("gemini-3.8-flash" if "Gemini" in prov
                          else "claude-sonnet-4-5" if "Claude" in prov
                          else "deepseek-chat" if "DeepSeek" in prov
                          else "gpt-4o")
                svc = create_ai_service(prov, keys, model)
                return svc.generate
    except Exception as e:
        print(f"smart_prompt resolve_ai_call fail: {e}")
    return None


class SmartPromptDialog(ctk.CTkToplevel):
    """Modal Smart Prompt — 2 mode tạo đề / tạo câu hỏi."""

    WIDTH = 760
    HEIGHT = 640

    def __init__(self, parent, *,
                  on_apply_matrix: Callable | None = None,
                  on_add_question: Callable | None = None,
                  default_subject: str = "Toán",
                  default_grade: str = "12"):
        super().__init__(parent)
        self.title("💬 Smart Prompt — Tạo đề & câu hỏi bằng AI")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(640, 560)
        try: self.attributes("-topmost", True)
        except: pass

        self._on_apply_matrix = on_apply_matrix
        self._on_add_question = on_add_question
        self._subject = default_subject
        self._grade = default_grade

        self._matrix = None         # MatrixData hiện tại
        self._matrix_info = {}
        self._question = None       # Question hiện tại (mode 2)
        self._busy = False

        self._build()
        self.bind("<Escape>", lambda e: self.destroy())
        try: self.grab_set(); self.focus_force()
        except: pass

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=("#0F2D52", "#0B1F35"),
                             corner_radius=0, height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="💬  Smart Prompt",
                      font=("Segoe UI", 16, "bold"),
                      text_color="white").pack(side="left", padx=16, pady=10)

        # Mode switch
        self._mode = ctk.StringVar(value="exam")
        seg = ctk.CTkSegmentedButton(
            hdr, values=["📄 Tạo đề", "✏️ 1 câu hỏi"],
            command=self._on_mode_change)
        seg.set("📄 Tạo đề")
        seg.pack(side="right", padx=16)

        # Body container — swap theo mode
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=14, pady=12)

        self._build_exam_mode()

    def _on_mode_change(self, choice: str):
        for c in self._body.winfo_children():
            c.destroy()
        if "câu hỏi" in choice:
            self._mode.set("question")
            self._build_question_mode()
        else:
            self._mode.set("exam")
            self._build_exam_mode()

    # ── MODE 1: Tạo đề ────────────────────────────────────────────────────
    def _build_exam_mode(self):
        ctk.CTkLabel(self._body,
                      text="Nhập yêu cầu bằng tiếng Việt tự nhiên:",
                      font=("Segoe UI", 12, "bold"), anchor="w"
                      ).pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(self._body,
                      text='VD: "Đề 90 phút lớp 12 về tích phân, 18 TN 4 ĐS" '
                            'hoặc "Đề 1 tiết Toán 9 chương 2"',
                      font=("Segoe UI", 10), text_color="gray", anchor="w",
                      wraplength=700, justify="left"
                      ).pack(fill="x", pady=(0, 6))

        self._exam_input = ctk.CTkTextbox(self._body, height=90,
                                            font=("Segoe UI", 12))
        self._exam_input.pack(fill="x", pady=4)

        btn_row = ctk.CTkFrame(self._body, fg_color="transparent")
        btn_row.pack(fill="x", pady=4)
        self._exam_parse_btn = ctk.CTkButton(
            btn_row, text="🔍 Phân tích", width=140,
            command=self._exam_parse)
        self._exam_parse_btn.pack(side="left")
        self._exam_apply_btn = ctk.CTkButton(
            btn_row, text="✓ Áp dụng vào Tạo đề", width=200,
            state="disabled", fg_color=("#10B981", "#065F46"),
            hover_color=("#059669", "#047857"),
            command=self._exam_apply)
        self._exam_apply_btn.pack(side="right")

        self._exam_status = ctk.CTkLabel(
            self._body, text="", font=("Segoe UI", 10),
            text_color="#059669", anchor="w", wraplength=700, justify="left")
        self._exam_status.pack(fill="x", pady=(4, 0))

        # Matrix preview
        prev_label = ctk.CTkLabel(self._body, text="Ma trận đề:",
                                    font=("Segoe UI", 11, "bold"), anchor="w")
        prev_label.pack(fill="x", pady=(8, 2))
        self._exam_preview = ctk.CTkTextbox(self._body, height=140,
                                              font=("Consolas", 10))
        self._exam_preview.pack(fill="both", expand=True, pady=2)
        self._exam_preview.insert("1.0", "(Chưa phân tích)")
        self._exam_preview.configure(state="disabled")

        # Follow-up
        fu_frame = ctk.CTkFrame(self._body, fg_color=("#FFFBEB", "#1F1B0F"),
                                  corner_radius=8)
        fu_frame.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(fu_frame,
                      text="💬 Điều chỉnh thêm (vd: 'Thêm 2 câu VD về tích phân'):",
                      font=("Segoe UI", 10, "bold"),
                      text_color=("#92400E", "#FCD34D"), anchor="w"
                      ).pack(fill="x", padx=10, pady=(8, 2))
        fu_row = ctk.CTkFrame(fu_frame, fg_color="transparent")
        fu_row.pack(fill="x", padx=10, pady=(0, 8))
        self._exam_followup = ctk.CTkEntry(
            fu_row, placeholder_text="Nhập điều chỉnh…")
        self._exam_followup.pack(side="left", fill="x", expand=True,
                                   padx=(0, 6))
        self._exam_fu_btn = ctk.CTkButton(
            fu_row, text="🤖 Áp dụng", width=110,
            fg_color=("#F59E0B", "#92400E"),
            hover_color=("#D97706", "#78350F"),
            command=self._exam_followup_apply)
        self._exam_fu_btn.pack(side="left")

    def _exam_parse(self):
        text = self._exam_input.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Thiếu yêu cầu",
                                    "Vui lòng nhập yêu cầu.", parent=self)
            return
        self._exam_parse_btn.configure(state="disabled", text="⏳ Đang phân tích…")

        def _worker():
            try:
                from core.smart_prompt import smart_prompt_to_matrix
                matrix, info = smart_prompt_to_matrix(text)
                self.after(0, lambda: self._on_parse_done(matrix, info, None))
            except Exception as e:
                err = str(e)
                self.after(0, lambda: self._on_parse_done(None, None, err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_parse_done(self, matrix, info, err):
        try:
            if not self.winfo_exists(): return
        except Exception: return
        self._exam_parse_btn.configure(state="normal", text="🔍 Phân tích")
        if err:
            self._exam_status.configure(text=f"❌ Lỗi: {err[:150]}",
                                          text_color="#DC2626")
            return
        self._matrix = matrix
        grade = (info or {}).get("grade") or self._grade
        subject = (info or {}).get("subject") or self._subject
        self._matrix_info = {"grade": grade, "subject": subject}
        n = len(matrix.rows) if matrix else 0
        time_str = getattr(matrix, "time_str", "?")
        self._exam_status.configure(
            text=f"✅ Đã tạo: {n} dòng ma trận | Lớp {grade} | {time_str}",
            text_color="#059669")
        self._exam_apply_btn.configure(state="normal")
        self._render_matrix_preview()

    def _render_matrix_preview(self):
        try:
            from core.smart_prompt import dump_matrix_brief
            brief = dump_matrix_brief(self._matrix)
        except Exception:
            brief = self._format_matrix_fallback()
        self._exam_preview.configure(state="normal")
        self._exam_preview.delete("1.0", "end")
        self._exam_preview.insert("1.0", brief)
        self._exam_preview.configure(state="disabled")

    def _format_matrix_fallback(self) -> str:
        if not self._matrix: return "(trống)"
        lines = []
        for r in getattr(self._matrix, "rows", []):
            lines.append(f"{getattr(r, 'topic', '?')}: "
                          f"NB={getattr(r, 'nb', 0)} "
                          f"TH={getattr(r, 'th', 0)} "
                          f"VD={getattr(r, 'vd', 0)} "
                          f"[{getattr(r, 'qtype', 'TN')}]")
        return "\n".join(lines)

    def _exam_followup_apply(self):
        if not self._matrix:
            messagebox.showwarning("Chưa có ma trận",
                                    "Hãy nhấn 'Phân tích' trước.", parent=self)
            return
        followup = self._exam_followup.get().strip()
        if not followup:
            return
        self._exam_fu_btn.configure(state="disabled", text="⏳…")

        def _worker():
            try:
                from core.smart_prompt import (clone_matrix, diff_matrices,
                    followup_modify_matrix, format_matrix_diff)
                ai_call = _resolve_ai_call()
                if not ai_call:
                    raise RuntimeError("Chưa cấu hình AI (vào ⚙ Cấu hình).")
                subj = self._matrix_info.get("subject", "Toán")
                grade = self._matrix_info.get("grade", "12")
                old = clone_matrix(self._matrix)
                new_matrix, msg = followup_modify_matrix(
                    old, followup, ai_call, subject=subj, grade=grade)
                self.after(0, lambda: self._on_followup_done(new_matrix, msg, None))
            except Exception as e:
                err = str(e)
                self.after(0, lambda: self._on_followup_done(None, None, err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_followup_done(self, new_matrix, msg, err):
        try:
            if not self.winfo_exists(): return
        except Exception: return
        self._exam_fu_btn.configure(state="normal", text="🤖 Áp dụng")
        if err:
            self._exam_status.configure(text=f"❌ {err[:150]}",
                                          text_color="#DC2626")
            return
        if new_matrix is not None:
            self._matrix = new_matrix
        self._exam_followup.delete(0, "end")
        n = len(self._matrix.rows) if self._matrix else 0
        self._exam_status.configure(
            text=f"✅ {msg} | Ma trận: {n} dòng", text_color="#059669")
        self._render_matrix_preview()

    def _exam_apply(self):
        if not self._matrix:
            return
        if self._on_apply_matrix:
            try:
                self._on_apply_matrix(self._matrix, self._matrix_info)
                from v5.toast import show_toast
                show_toast(self.master, "✓ Đã áp dụng ma trận vào Tạo đề",
                            kind="success")
                self.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi áp dụng", str(e), parent=self)
        else:
            messagebox.showinfo("Chưa kết nối",
                                  "Mở Smart Prompt từ view Tạo đề để áp dụng.",
                                  parent=self)

    # ── MODE 2: 1 câu hỏi ─────────────────────────────────────────────────
    def _build_question_mode(self):
        ctk.CTkLabel(self._body,
                      text="Mô tả câu hỏi muốn tạo:",
                      font=("Segoe UI", 12, "bold"), anchor="w"
                      ).pack(fill="x", pady=(0, 2))
        ctk.CTkLabel(self._body,
                      text='VD: "Câu TN về đạo hàm hàm bậc 3, mức TH" hoặc '
                            '"Câu ĐS về tích phân xác định, 4 ý, mức VD"',
                      font=("Segoe UI", 10), text_color="gray", anchor="w",
                      wraplength=700, justify="left"
                      ).pack(fill="x", pady=(0, 6))

        self._q_input = ctk.CTkTextbox(self._body, height=80,
                                         font=("Segoe UI", 12))
        self._q_input.pack(fill="x", pady=4)

        opt_row = ctk.CTkFrame(self._body, fg_color="transparent")
        opt_row.pack(fill="x", pady=4)
        ctk.CTkLabel(opt_row, text="Loại:").pack(side="left", padx=(0, 4))
        self._q_type = ctk.StringVar(value="TN")
        ctk.CTkOptionMenu(opt_row, values=["TN", "DS", "TLN", "TL"],
                            variable=self._q_type, width=80
                            ).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(opt_row, text="Mức:").pack(side="left", padx=(0, 4))
        self._q_level = ctk.StringVar(value="TH")
        ctk.CTkOptionMenu(opt_row, values=["NB", "TH", "VD", "VDC"],
                            variable=self._q_level, width=80
                            ).pack(side="left")

        self._q_gen_btn = ctk.CTkButton(
            opt_row, text="🤖 Tạo câu hỏi", width=160,
            command=self._gen_question)
        self._q_gen_btn.pack(side="right")

        self._q_status = ctk.CTkLabel(
            self._body, text="", font=("Segoe UI", 10),
            text_color="#059669", anchor="w", wraplength=700, justify="left")
        self._q_status.pack(fill="x", pady=(4, 0))

        ctk.CTkLabel(self._body, text="Câu hỏi đã tạo:",
                      font=("Segoe UI", 11, "bold"), anchor="w"
                      ).pack(fill="x", pady=(8, 2))
        self._q_preview = ctk.CTkTextbox(self._body, height=180,
                                           font=("Segoe UI", 11))
        self._q_preview.pack(fill="both", expand=True, pady=2)
        self._q_preview.insert("1.0", "(Chưa tạo)")
        self._q_preview.configure(state="disabled")

        self._q_add_btn = ctk.CTkButton(
            self._body, text="📚 Thêm vào NHCH", height=36,
            state="disabled", fg_color=("#10B981", "#065F46"),
            hover_color=("#059669", "#047857"),
            command=self._add_question_to_bank)
        self._q_add_btn.pack(fill="x", pady=(8, 0))

    def _gen_question(self):
        text = self._q_input.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Thiếu mô tả",
                                    "Vui lòng mô tả câu hỏi.", parent=self)
            return
        self._q_gen_btn.configure(state="disabled", text="⏳ Đang tạo…")

        def _worker():
            try:
                ai_call = _resolve_ai_call()
                if not ai_call:
                    raise RuntimeError("Chưa cấu hình AI (vào ⚙ Cấu hình).")
                q = self._call_gen_one_question(
                    ai_call, text, self._q_type.get(), self._q_level.get())
                self.after(0, lambda: self._on_question_done(q, None))
            except Exception as e:
                err = str(e)
                self.after(0, lambda: self._on_question_done(None, err))

        threading.Thread(target=_worker, daemon=True).start()

    def _call_gen_one_question(self, ai_call, prompt, qtype, level):
        """Sinh 1 câu hỏi qua generator (reuse core).

        generate_all cần đủ semester+year+ai_call và trả ExamData (hoặc list
        tuỳ version). Map mô tả → 1 MatrixRow theo level.
        """
        from core.models import MatrixRow
        from core.generator import generate_all
        # MatrixRow = 1 câu (level đơn + codes + requirement)
        row = MatrixRow(
            stt="1", topic=prompt[:80], level=level,
            qtype=qtype, codes=[f"{qtype}1"],
            requirement=prompt[:200],
            points=0.25, enabled=True)
        result = generate_all(
            [row], subject=self._subject, grade=self._grade,
            semester="1", year="", ai_call=ai_call)
        qs = result.questions if hasattr(result, "questions") else (result or [])
        return qs[0] if qs else None

    def _on_question_done(self, q, err):
        try:
            if not self.winfo_exists(): return
        except Exception: return
        self._q_gen_btn.configure(state="normal", text="🤖 Tạo câu hỏi")
        if err:
            self._q_status.configure(text=f"❌ {err[:150]}",
                                       text_color="#DC2626")
            return
        if not q:
            self._q_status.configure(text="❌ AI không trả về câu hỏi",
                                       text_color="#DC2626")
            return
        self._question = q
        self._q_status.configure(text="✅ Đã tạo câu hỏi", text_color="#059669")
        self._render_question_preview(q)
        self._q_add_btn.configure(state="normal")

    def _render_question_preview(self, q):
        lines = [f"[{getattr(q, 'qtype', '?')} · {getattr(q, 'level', '?')}]",
                  "", getattr(q, "question", "")]
        opts = getattr(q, "options", None) or {}
        for k, v in opts.items():
            lines.append(f"  {k}. {v}")
        ans = getattr(q, "answer", "")
        if ans: lines.append(f"\nĐáp án: {ans}")
        sol = getattr(q, "solution", "")
        if sol: lines.append(f"\nLời giải: {sol}")
        self._q_preview.configure(state="normal")
        self._q_preview.delete("1.0", "end")
        self._q_preview.insert("1.0", "\n".join(lines))
        self._q_preview.configure(state="disabled")

    def _add_question_to_bank(self):
        if not self._question:
            return
        # Gán structured ID nếu chưa có (nhất quán hệ ID)
        try:
            if not (getattr(self._question, "question_id", "") or "").strip():
                from core.models import compute_structured_id
                self._question.question_id = compute_structured_id(
                    self._question, str(self._grade))
        except Exception: pass
        if self._on_add_question:
            try:
                self._on_add_question(self._question,
                                       self._subject, self._grade)
                from v5.toast import show_toast
                show_toast(self.master, "✓ Đã thêm câu hỏi vào NHCH",
                            kind="success")
            except Exception as e:
                messagebox.showerror("Lỗi", str(e), parent=self)
        else:
            # Fallback: lưu thẳng qua storage (save_questions nhận list)
            try:
                from storage.database import save_questions
                n = save_questions([self._question], subject=self._subject,
                                     grade=self._grade, source="smart_prompt")
                from v5.toast import show_toast
                show_toast(self.master,
                            f"✓ Đã lưu {n} câu hỏi vào NHCH",
                            kind="success")
            except Exception as e:
                messagebox.showerror("Lỗi lưu", str(e), parent=self)
