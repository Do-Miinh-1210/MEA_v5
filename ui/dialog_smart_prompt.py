"""
ui/dialog_smart_prompt.py — Dialog "Smart Prompt" nâng cao.
Tab 1: Tạo đề từ Prompt (giữ nguyên logic cũ)
Tab 2: Tạo câu hỏi từ Prompt (mới) — tạo 1 câu hỏi + preview + chèn NHCH
"""

from __future__ import annotations
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Callable, Optional

from core.models import MatrixRow, MatrixData, Question, DSItem
from core.quick_matrix import get_topics_for_grade, TOPICS_BY_GRADE
from config import POINTS_MAP


# ── Constants ──────────────────────────────────────────────────────────────────

QTYPES = ["TN", "DS", "TLN", "TL"]
QTYPE_LABELS = {
    "TN": "Trắc nghiệm", "DS": "Đúng – Sai",
    "TLN": "Trả lời ngắn", "TL": "Tự luận",
}
LEVELS = ["NB", "TH", "VD"]
LEVEL_LABELS = {
    "NB": "Nhận biết", "TH": "Thông hiểu", "VD": "Vận dụng", "VDC": "Vận dụng cao",
}


class SmartPromptDialog(tk.Toplevel):
    """Dialog Smart Prompt 2 chức năng: Tạo đề + Tạo câu hỏi."""

    def __init__(
        self,
        parent,
        get_ai_call: Callable,
        get_ai_service: Callable,
        on_apply_matrix: Callable[[MatrixData, str, str], None],
        on_add_to_bank: Callable[[Question, str, str], None],
        default_subject: str = "Toán",
        default_grade: str = "12",
    ):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("💬 Smart Prompt — Tạo đề & câu hỏi bằng AI")

        self._get_ai_call = get_ai_call
        self._get_ai_service = get_ai_service
        self._on_apply_matrix = on_apply_matrix
        self._on_add_to_bank = on_add_to_bank
        self._default_subject = default_subject
        self._default_grade = default_grade
        self._generated_question: Optional[Question] = None
        self._image_path: str = ""
        self._tk_images: list = []  # prevent GC
        self._exam_history: list[MatrixData] = []
        self._exam_history_pos = -1

        # Event dùng để hủy retry-backoff trong worker thread khi user đóng
        # dialog. Worker dùng event.wait(2) thay cho time.sleep(2), nên khi
        # set() được gọi thì vòng retry thoát ngay lập tức.
        import threading as _th
        self._cancel_event = _th.Event()

        # ── Size ──
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(850, max(750, sw // 2))
        h = min(720, max(600, int(sh * 0.7)))
        x = (sw - w) // 2
        y = max(0, (sh - h) // 2 - 20)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(True, True)
        self.minsize(750, 600)
        self.maxsize(sw, sh - 40)
        self.grab_set()
        self.configure(bg="#FFFFFF")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build()
        self.focus_force()

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        # ── Header ──
        hdr = tk.Frame(self, bg="#0F2D52")
        hdr.pack(fill="x")
        try:
            from PIL import Image, ImageTk
            from pathlib import Path
            _logo_path = Path(__file__).parent.parent / "assets" / "app.png"
            if not _logo_path.exists():
                _logo_path = Path(__file__).parent.parent / "assets" / "icon4.png"
            if _logo_path.exists():
                _img = Image.open(_logo_path).convert("RGBA").resize((32, 32), Image.LANCZOS)
                self._hdr_logo = ImageTk.PhotoImage(_img)
                tk.Label(hdr, image=self._hdr_logo, bg="#0F2D52").pack(side="left", padx=(14, 6), pady=8)
        except Exception:
            pass
        tk.Label(hdr, text="Smart Prompt — Tạo đề & câu hỏi bằng AI",
                 bg="#0F2D52", fg="white", font=("Segoe UI", 12, "bold")).pack(side="left", padx=6, pady=8)
        tk.Frame(self, bg="#10B981", height=3).pack(fill="x")

        # ── Tabs ──
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=(8, 8))

        tab_exam = tk.Frame(nb, bg="#FFFFFF")
        tab_question = tk.Frame(nb, bg="#FFFFFF")
        nb.add(tab_exam, text="  📄 Tạo đề từ Prompt  ")
        nb.add(tab_question, text="  ✏️ Tạo câu hỏi từ Prompt  ")

        self._build_exam_tab(tab_exam)
        self._build_question_tab(tab_question)

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB 1: Tạo đề từ Prompt (giữ nguyên logic Smart Prompt cũ)
    # ──────────────────────────────────────────────────────────────────────────

    def _build_exam_tab(self, parent: tk.Frame):
        tk.Label(parent, text="Nhập yêu cầu bằng tiếng Việt tự nhiên:",
                 bg="#FFFFFF", fg="#0F172A", font=("Segoe UI", 11, "bold")).pack(
            padx=14, pady=(14, 4), anchor="w")
        tk.Label(parent,
                 text='VD: "Tạo đề 1 tiết Toán 9 chương 2" hoặc "Đề 90 phút lớp 12 về tích phân, 18 TN 4 DS"',
                 bg="#FFFFFF", fg="#64748B", font=("Segoe UI", 9), wraplength=700).pack(
            padx=14, pady=(0, 6), anchor="w")

        self._exam_input = tk.Text(parent, font=("Segoe UI", 11), height=5, wrap="word",
                                   relief="solid", bd=1, padx=8, pady=6)
        self._exam_input.pack(fill="both", expand=True, padx=14, pady=4)
        self._exam_input.focus_set()

        self._exam_result_lbl = tk.Label(parent, text="", bg="#FFFFFF", fg="#059669",
                                         font=("Segoe UI", 9), wraplength=700, anchor="w")
        self._exam_result_lbl.pack(fill="x", padx=14, pady=(4, 0))

        # ── [SMART-5] Follow-up panel (hidden ban đầu) ──────────────────
        self._exam_followup_frame = tk.LabelFrame(
            parent,
            text=" 💬 Điều chỉnh thêm (chat-style) — VD: 'Thêm 2 câu khó về tích phân' ",
            bg="#FFFBEB", fg="#92400E",
            font=("Segoe UI", 9, "bold"),
            padx=10, pady=8,
        )
        # KHÔNG pack → sẽ pack sau khi parse thành công

        # Quick-action chips
        chip_row = tk.Frame(self._exam_followup_frame, bg="#FFFBEB")
        chip_row.pack(fill="x", pady=(0, 4))
        tk.Label(chip_row, text="Gợi ý nhanh:",
                 bg="#FFFBEB", fg="#92400E",
                 font=("Segoe UI", 8)).pack(side="left", padx=(0, 4))
        for chip_text in [
            "+ 2 câu VD",
            "Tăng độ khó câu cuối",
            "Đổi câu 1 sang TN",
            "Xoá câu cuối",
        ]:
            tk.Button(
                chip_row, text=chip_text,
                bg="#FEF3C7", fg="#92400E",
                activebackground="#FDE68A",
                font=("Segoe UI", 8),
                relief="flat", cursor="hand2", bd=0,
                padx=6, pady=2,
                command=lambda t=chip_text: self._exam_followup_input.delete("1.0", "end") or
                                            self._exam_followup_input.insert("1.0", t),
            ).pack(side="left", padx=2)

        # Followup textbox + submit button
        fu_row = tk.Frame(self._exam_followup_frame, bg="#FFFBEB")
        fu_row.pack(fill="x")
        self._exam_followup_input = tk.Text(
            fu_row, font=("Segoe UI", 10),
            height=2, wrap="word",
            relief="solid", bd=1, padx=6, pady=4,
        )
        self._exam_followup_input.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._exam_followup_btn = tk.Button(
            fu_row, text="🤖 Áp dụng",
            bg="#F59E0B", fg="white",
            activebackground="#D97706",
            font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", bd=0,
            padx=10, pady=6,
            command=self._exam_followup_apply,
        )
        self._exam_followup_btn.pack(side="left")

        diff_box = ttk.LabelFrame(self._exam_followup_frame, text=" Preview thay đổi ")
        diff_box.pack(fill="both", expand=True, pady=(8, 0))
        self._exam_diff_text = scrolledtext.ScrolledText(
            diff_box,
            height=5,
            wrap="word",
            font=("Consolas", 9),
            bg="#FFFFFF",
            fg="#334155",
            relief="solid",
            bd=1,
        )
        self._exam_diff_text.pack(fill="both", expand=True, padx=6, pady=6)
        self._set_exam_diff("Chưa có thay đổi.")

        # Buttons
        btn_f = tk.Frame(parent, bg="#FFFFFF")
        btn_f.pack(fill="x", padx=14, pady=(8, 14), side="bottom")

        tk.Button(btn_f, text="  🔍 Phân tích  ", bg="#0EA5E9", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                  padx=14, pady=6, command=self._exam_parse).pack(side="left", padx=4)
        self._exam_apply_btn = tk.Button(
            btn_f, text="  ✅ Áp dụng  ", bg="#10B981", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            padx=14, pady=6, state="disabled")
        self._exam_apply_btn.pack(side="left", padx=4)
        self._exam_undo_btn = tk.Button(
            btn_f, text="  ↶ Undo  ", bg="#E2E8F0", fg="#334155",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            padx=10, pady=6, state="disabled", command=self._exam_undo)
        self._exam_undo_btn.pack(side="left", padx=4)
        self._exam_redo_btn = tk.Button(
            btn_f, text="  ↷ Redo  ", bg="#E2E8F0", fg="#334155",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            padx=10, pady=6, state="disabled", command=self._exam_redo)
        self._exam_redo_btn.pack(side="left", padx=4)
        tk.Button(btn_f, text="  Đóng  ", bg="#F1F5F9", fg="#475569",
                  font=("Segoe UI", 10), relief="flat", cursor="hand2",
                  padx=14, pady=6, command=self.destroy).pack(side="right", padx=4)

        self._exam_matrix = None
        self._exam_info = {}

    def _set_exam_diff(self, text: str):
        widget = getattr(self, "_exam_diff_text", None)
        if widget is None:
            return
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text or "Không có thay đổi.")
        widget.configure(state="disabled")

    def _push_exam_history(self, matrix: MatrixData) -> None:
        from core.smart_prompt import clone_matrix

        if self._exam_history_pos < len(self._exam_history) - 1:
            self._exam_history = self._exam_history[:self._exam_history_pos + 1]
        self._exam_history.append(clone_matrix(matrix))
        self._exam_history_pos = len(self._exam_history) - 1
        self._update_exam_history_buttons()

    def _update_exam_history_buttons(self) -> None:
        undo_state = "normal" if self._exam_history_pos > 0 else "disabled"
        redo_state = "normal" if self._exam_history_pos < len(self._exam_history) - 1 else "disabled"
        if hasattr(self, "_exam_undo_btn"):
            self._exam_undo_btn.config(state=undo_state)
        if hasattr(self, "_exam_redo_btn"):
            self._exam_redo_btn.config(state=redo_state)

    def _restore_exam_history(self, pos: int, action: str) -> None:
        if not (0 <= pos < len(self._exam_history)):
            return
        from core.smart_prompt import clone_matrix

        self._exam_history_pos = pos
        self._exam_matrix = clone_matrix(self._exam_history[pos])
        self._update_exam_history_buttons()
        n = len(self._exam_matrix.rows)
        self._exam_result_lbl.config(
            text=f"{action}: ma trận hiện tại {n} câu. Có thể chỉnh tiếp hoặc nhấn 'Áp dụng'.",
            fg="#059669",
        )
        self._set_exam_diff(f"{action}.\n\n" + self._format_current_matrix_brief())

    def _format_current_matrix_brief(self) -> str:
        if not self._exam_matrix:
            return ""
        from core.smart_prompt import dump_matrix_brief

        return dump_matrix_brief(self._exam_matrix)

    def _exam_undo(self):
        if self._exam_history_pos <= 0:
            return
        self._restore_exam_history(self._exam_history_pos - 1, "Đã undo")

    def _exam_redo(self):
        if self._exam_history_pos >= len(self._exam_history) - 1:
            return
        self._restore_exam_history(self._exam_history_pos + 1, "Đã redo")

    def _exam_parse(self):
        text = self._exam_input.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Thiếu yêu cầu", "Vui lòng nhập yêu cầu.", parent=self)
            return
        try:
            from core.smart_prompt import smart_prompt_to_matrix
            matrix, info = smart_prompt_to_matrix(text)
            grade = info.get("grade") or "12"
            subject = info.get("subject") or "Toán"
            self._exam_matrix = matrix
            self._exam_info = {"grade": grade, "subject": subject}
            self._exam_history = []
            self._exam_history_pos = -1
            self._push_exam_history(matrix)
            self._set_exam_diff(self._format_current_matrix_brief())

            self._exam_result_lbl.config(
                text=f"✅ Đã tạo: {len(matrix.rows)} câu | Lớp {grade} | "
                     f"{matrix.time_str} | Có thể chỉnh thêm phía dưới hoặc nhấn 'Áp dụng'.",
                fg="#059669")
            self._exam_apply_btn.config(state="normal", command=self._exam_apply)

            # [SMART-5] Show follow-up panel sau khi parse OK
            try:
                self._exam_followup_frame.pack(
                    fill="x", padx=14, pady=(6, 0), before=self._exam_result_lbl,
                )
            except tk.TclError:
                # Fallback: pack ở vị trí mặc định
                self._exam_followup_frame.pack(fill="x", padx=14, pady=(6, 0))
        except Exception as e:
            self._exam_result_lbl.config(text=f"❌ Lỗi: {e}", fg="#DC2626")

    def _exam_followup_apply(self):
        """[SMART-5] Áp dụng follow-up text lên matrix hiện tại."""
        if not self._exam_matrix:
            messagebox.showwarning(
                "Chưa có ma trận",
                "Hãy nhấn 'Phân tích' để tạo ma trận trước.",
                parent=self,
            )
            return

        followup = self._exam_followup_input.get("1.0", "end").strip()
        if not followup:
            messagebox.showwarning(
                "Thiếu yêu cầu",
                "Hãy nhập yêu cầu cần điều chỉnh (vd: 'Thêm 2 câu VD').",
                parent=self,
            )
            return

        # Disable button khi đang xử lý
        self._exam_followup_btn.config(state="disabled", text="⏳ Đang xử lý…")

        def _worker():
            try:
                from core.smart_prompt import (
                    clone_matrix,
                    diff_matrices,
                    followup_modify_matrix,
                    format_matrix_diff,
                )
                ai_call = self._get_ai_call() if self._get_ai_call else None
                if not ai_call:
                    raise RuntimeError("Chưa cấu hình AI ở tab Cài đặt.")

                subj = self._exam_info.get("subject", "Toán")
                grade = self._exam_info.get("grade", "12")
                old_matrix = clone_matrix(self._exam_matrix)
                new_matrix, msg = followup_modify_matrix(
                    old_matrix, followup, ai_call,
                    subject=subj, grade=grade,
                )
                diff_text = format_matrix_diff(diff_matrices(old_matrix, new_matrix))
                self.after(0, lambda m=msg, mx=new_matrix, d=diff_text:
                           self._on_followup_done(m, True, mx, d))
            except Exception as e:
                err = str(e)
                self.after(0, lambda m=err: self._on_followup_done(m, False))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_followup_done(
        self,
        msg: str,
        ok: bool,
        new_matrix: Optional[MatrixData] = None,
        diff_text: str = "",
    ):
        """Callback (main thread) sau khi follow-up worker xong."""
        self._exam_followup_btn.config(state="normal", text="🤖 Áp dụng")
        if ok:
            if new_matrix is not None:
                self._exam_matrix = new_matrix
                self._push_exam_history(new_matrix)
            self._exam_followup_input.delete("1.0", "end")
            n = len(self._exam_matrix.rows) if self._exam_matrix else 0
            self._set_exam_diff(diff_text)
            self._exam_result_lbl.config(
                text=f"✅ {msg} | Ma trận hiện tại: {n} câu. "
                     f"Có thể chỉnh tiếp hoặc nhấn 'Áp dụng'.",
                fg="#059669",
            )
        else:
            self._exam_result_lbl.config(
                text=f"❌ Lỗi follow-up: {msg[:120]}",
                fg="#DC2626",
            )

    def _exam_apply(self):
        if self._exam_matrix:
            self._on_apply_matrix(
                self._exam_matrix,
                self._exam_info.get("subject", "Toán"),
                self._exam_info.get("grade", "12"),
            )
            self.destroy()

    # ──────────────────────────────────────────────────────────────────────────
    #  TAB 2: Tạo câu hỏi từ Prompt
    # ──────────────────────────────────────────────────────────────────────────

    def _build_question_tab(self, parent: tk.Frame):
        # ── Config row ──
        cfg_f = ttk.LabelFrame(parent, text=" ⚙️ Thông tin câu hỏi ")
        cfg_f.pack(fill="x", padx=12, pady=(10, 6))

        g = tk.Frame(cfg_f, bg="#FFFFFF")
        g.pack(fill="x", padx=10, pady=8)

        # Row 1: Lớp, Loại câu, Mức độ
        tk.Label(g, text="Lớp:", bg="#FFFFFF", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        self._q_grade_var = tk.StringVar(value=self._default_grade)
        cb_grade = ttk.Combobox(g, textvariable=self._q_grade_var,
                                values=[str(i) for i in range(1, 13)],
                                width=5, state="readonly", font=("Segoe UI", 10))
        cb_grade.grid(row=0, column=1, padx=6, sticky="w")
        cb_grade.bind("<<ComboboxSelected>>", lambda _: self._refresh_q_topics())

        tk.Label(g, text="Loại câu:", bg="#FFFFFF", font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=(14, 0))
        self._q_qtype_var = tk.StringVar(value="TN")
        ttk.Combobox(g, textvariable=self._q_qtype_var,
                     values=[f"{k} — {v}" for k, v in QTYPE_LABELS.items()],
                     width=18, state="readonly", font=("Segoe UI", 10)).grid(row=0, column=3, padx=6, sticky="w")

        tk.Label(g, text="Mức độ:", bg="#FFFFFF", font=("Segoe UI", 10)).grid(row=0, column=4, sticky="w", padx=(14, 0))
        self._q_level_var = tk.StringVar(value="TH")
        ttk.Combobox(g, textvariable=self._q_level_var,
                     values=[f"{k} — {v}" for k, v in LEVEL_LABELS.items()],
                     width=16, state="readonly", font=("Segoe UI", 10)).grid(row=0, column=5, padx=6, sticky="w")

        # Row 2: Chủ đề
        tk.Label(g, text="Chủ đề:", bg="#FFFFFF", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=(8, 0))
        self._q_topic_var = tk.StringVar()
        self._q_topic_cb = ttk.Combobox(g, textvariable=self._q_topic_var,
                                        width=60, font=("Segoe UI", 10))
        self._q_topic_cb.grid(row=1, column=1, columnspan=5, padx=6, sticky="ew", pady=(8, 0))
        self._refresh_q_topics()

        g.columnconfigure(5, weight=1)

        # ── Image upload ──
        # Ẩn hoàn toàn nếu provider hiện tại KHÔNG hỗ trợ vision (DeepSeek).
        # Các biến luôn khởi tạo để tránh AttributeError ở chỗ khác.
        self._img_path_var = tk.StringVar(value="Chưa chọn hình ảnh")
        self._img_preview_lbl = tk.Label(parent, bg="#FFFFFF")  # placeholder (không pack)

        provider_supports_vision = self._provider_supports_vision()
        if provider_supports_vision:
            img_f = ttk.LabelFrame(parent, text=" 🖼️ Hình ảnh đính kèm (tùy chọn) ")
            img_f.pack(fill="x", padx=12, pady=(4, 6))

            img_row = tk.Frame(img_f, bg="#FFFFFF")
            img_row.pack(fill="x", padx=10, pady=6)

            tk.Button(img_row, text="📁 Chọn ảnh", bg="#6366F1", fg="white",
                      font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                      padx=8, pady=3, command=self._pick_image).pack(side="left", padx=(0, 6))
            tk.Button(img_row, text="🗑 Xóa ảnh", bg="#EF4444", fg="white",
                      font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                      padx=8, pady=3, command=self._remove_image).pack(side="left", padx=(0, 8))
            self._img_lbl = tk.Label(img_row, textvariable=self._img_path_var, bg="#FFFFFF",
                                     fg="#64748B", font=("Segoe UI", 9), anchor="w")
            self._img_lbl.pack(side="left", fill="x", expand=True)

            # Image preview (gắn lại vào img_f)
            self._img_preview_lbl.destroy()
            self._img_preview_lbl = tk.Label(img_f, bg="#FFFFFF")
            self._img_preview_lbl.pack(padx=10, pady=(0, 6))
        else:
            # Thông báo nhẹ: provider không hỗ trợ vision
            note_f = tk.Frame(parent, bg="#FEF3C7")
            note_f.pack(fill="x", padx=12, pady=(4, 6))
            tk.Label(note_f,
                     text="ℹ️ Provider hiện tại (DeepSeek) không hỗ trợ phân tích hình ảnh. "
                          "Chuyển sang Gemini hoặc Claude trong tab Cài đặt để dùng tính năng này.",
                     bg="#FEF3C7", fg="#92400E", font=("Segoe UI", 9),
                     wraplength=700, justify="left", anchor="w").pack(
                fill="x", padx=10, pady=6)

        # ── Prompt input ──
        prompt_f = ttk.LabelFrame(parent, text=" ✍️ Yêu cầu cho AI ")
        prompt_f.pack(fill="both", expand=True, padx=12, pady=(4, 6))

        tk.Label(prompt_f, text="Mô tả chi tiết câu hỏi bạn muốn tạo (AI sẽ kết hợp với hình ảnh nếu có):",
                 bg="#FFFFFF", fg="#475569", font=("Segoe UI", 9)).pack(
            padx=10, pady=(6, 2), anchor="w")

        self._q_prompt_input = tk.Text(prompt_f, font=("Segoe UI", 10), height=4, wrap="word",
                                       relief="solid", bd=1, padx=8, pady=6)
        self._q_prompt_input.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        # ── Buttons ──
        btn_f = tk.Frame(parent, bg="#FFFFFF")
        btn_f.pack(fill="x", padx=12, pady=(4, 12), side="bottom")

        self._q_gen_btn = tk.Button(
            btn_f, text="  ⚡ Tạo câu hỏi  ", bg="#F59E0B", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            padx=14, pady=6, command=self._generate_question)
        self._q_gen_btn.pack(side="left", padx=4)

        self._q_preview_btn = tk.Button(
            btn_f, text="  👁 Xem & Chỉnh sửa  ", bg="#6366F1", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            padx=14, pady=6, state="disabled", command=self._preview_question)
        self._q_preview_btn.pack(side="left", padx=4)

        self._q_insert_btn = tk.Button(
            btn_f, text="  📥 Chèn vào NHCH  ", bg="#10B981", fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
            padx=14, pady=6, state="disabled", command=self._insert_to_bank)
        self._q_insert_btn.pack(side="left", padx=4)

        tk.Button(btn_f, text="  Đóng  ", bg="#F1F5F9", fg="#475569",
                  font=("Segoe UI", 10), relief="flat", cursor="hand2",
                  padx=14, pady=6, command=self.destroy).pack(side="right", padx=4)

        # ── Progress bar + timer ──
        self._q_progress_frame = tk.Frame(parent, bg="#FFFFFF")
        self._q_progress_frame.pack(fill="x", padx=14, pady=(4, 2), before=btn_f)

        self._q_progress_bar = ttk.Progressbar(
            self._q_progress_frame, mode="indeterminate", length=300)
        self._q_progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self._q_timer_lbl = tk.Label(
            self._q_progress_frame, text="", bg="#FFFFFF", fg="#6366F1",
            font=("Segoe UI", 10, "bold"), width=8, anchor="e")
        self._q_timer_lbl.pack(side="right")

        self._q_progress_frame.pack_forget()  # Ẩn ban đầu

        self._q_status_lbl = tk.Label(parent, text="", bg="#FFFFFF", fg="#059669",
                                      font=("Segoe UI", 9, "italic"), anchor="w")
        self._q_status_lbl.pack(fill="x", padx=14, pady=(0, 0), before=btn_f)

        self._q_timer_running = False
        self._q_start_time = 0.0

    def _refresh_q_topics(self):
        grade = self._q_grade_var.get()
        topics = get_topics_for_grade(grade)[:40]
        self._q_topic_cb["values"] = topics

    def _provider_supports_vision(self) -> bool:
        """True nếu provider hiện tại hỗ trợ vision (Gemini / Claude).
        DeepSeek hiện chưa hỗ trợ vision qua endpoint OpenAI-compatible."""
        try:
            svc = self._get_ai_service() if self._get_ai_service else None
            name = (getattr(svc, "provider_name", "") or "").lower()
        except Exception:
            name = ""
        return ("gemini" in name) or ("claude" in name) or ("anthropic" in name)

    def _pick_image(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Chọn hình ảnh",
            filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("Tất cả", "*.*")],
        )
        if path:
            self._image_path = path
            self._img_path_var.set(path.split("/")[-1].split("\\")[-1])
            self._show_image_preview(path)

    def _remove_image(self):
        self._image_path = ""
        self._img_path_var.set("Chưa chọn hình ảnh")
        self._img_preview_lbl.config(image="")
        self._tk_images.clear()

    def _show_image_preview(self, path: str):
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            # Resize to fit preview
            max_w, max_h = 300, 150
            ratio = min(max_w / img.width, max_h / img.height, 1.0)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(img)
            self._tk_images.append(tk_img)
            self._img_preview_lbl.config(image=tk_img)
        except Exception:
            self._img_preview_lbl.config(image="", text="(Lỗi tải ảnh)")

    # ── Generate single question ──────────────────────────────────────────

    def _get_qtype(self) -> str:
        raw = self._q_qtype_var.get()
        return raw.split(" — ")[0].strip() if " — " in raw else raw.strip()

    def _get_level(self) -> str:
        raw = self._q_level_var.get()
        return raw.split(" — ")[0].strip() if " — " in raw else raw.strip()

    def _build_fast_prompt(self, qtype: str, level: str, topic: str,
                           grade: str, subject: str, user_req: str) -> str:
        """Prompt gọn cho 1 câu hỏi — không kèm chuongtrinhhoctap.txt (tiết kiệm token, nhanh hơn).
        Ở mức VD/VDC: nhúng bộ nguyên tắc ra đề toán thực tế (5 thành phần, bám chương trình lớp,
        nhiễu từ sai lầm điển hình).
        """
        level_desc = {"NB": "Nhận biết — dễ, kiểm tra kiến thức cơ bản",
                      "TH": "Thông hiểu — trung bình, cần hiểu bản chất",
                      "VD": "Vận dụng — bài toán thực tế, 2-3 bước suy luận",
                      "VDC": "Vận dụng cao — tối ưu/so sánh phương án, tự mô hình hóa"}.get(level, level)

        fmt_map = {
            "TN": ("===CAU===\nLOAI: TN\nMUCDO: {level}\nCHUONG: {topic}\n"
                   "NOIDUNG: <câu hỏi, công thức trong ${{...}}$>\n"
                   "A: <phương án A>\nB: <phương án B>\nC: <phương án C>\nD: <phương án D>\n"
                   "DAPAN: <A|B|C|D>\nLOIGIAI: <lời giải ngắn gọn>\n===KETCAU==="),
            "DS": ("===CAU===\nLOAI: DS\nMUCDO: {level}\nCHUONG: {topic}\n"
                   "NOIDUNG: <tình huống chung>\n"
                   "a: <nhận định a>\nb: <nhận định b>\nc: <nhận định c>\nd: <nhận định d>\n"
                   "DAPAN: a=D,b=S,c=D,d=S\n"
                   "LOIGIAI: a. Đúng. Vì ... | b. Sai. Vì ... | c. Đúng. Vì ... | d. Sai. Vì ...\n"
                   "===KETCAU==="),
            "TLN": ("===CAU===\nLOAI: TLN\nMUCDO: {level}\nCHUONG: {topic}\n"
                    "NOIDUNG: <bài toán>\nDAPAN: <số, tối đa 4 kí tự>\n"
                    "LOIGIAI: <lời giải ngắn>\n===KETCAU==="),
            "TL": ("===CAU===\nLOAI: TL\nMUCDO: {level}\nCHUONG: {topic}\n"
                   "NOIDUNG: <bài toán tự luận>\n"
                   "LOIGIAI: <lời giải đầy đủ>\n===KETCAU==="),
        }
        fmt = fmt_map.get(qtype, fmt_map["TL"]).replace("{level}", level).replace("{topic}", topic)

        req_line = f"\nYêu cầu GV: {user_req}" if user_req else ""

        # ── Bộ hướng dẫn VD / VDC (chỉ chèn khi cần — tiết kiệm token) ──
        vd_vdc_guide = ""
        if level in ("VD", "VDC"):
            grade_kb = {
                "6":  "phân số, tỉ số %, chu vi/diện tích hình phẳng cơ bản, ước-bội.",
                "7":  "tỉ lệ thức, đại lượng tỉ lệ thuận/nghịch, tam giác, tổng 3 góc.",
                "8":  "hằng đẳng thức, phân tích đa thức, Pythagore, tứ giác đặc biệt.",
                "9":  "hàm bậc nhất, y=ax², hệ phương trình, Vi-ét, hình trụ/nón/cầu.",
                "10": "BPT bậc nhất 2 ẩn (quy hoạch tuyến tính), vectơ, hệ thức lượng tam giác.",
                "11": "cấp số cộng/nhân, giới hạn, lượng giác, thể tích khối đa diện.",
                "12": "đạo hàm-tối ưu, nguyên hàm-tích phân, xác suất có điều kiện, tọa độ Oxyz.",
            }.get(str(grade), "theo đúng chương trình lớp này.")

            level_rule = (
                "• VD: 2-3 bước tính, áp dụng công thức vào tình huống quen thuộc; đề có thể gợi ý đặt ẩn."
                if level == "VD" else
                "• VDC: PHẢI có ý tối ưu (max/min) HOẶC so sánh ≥2 phương án HOẶC kết hợp ≥2 mảng kiến thức. "
                "Học sinh TỰ xây mô hình (đề KHÔNG gợi ý đặt ẩn)."
            )

            tn_rule = ("\n• Nếu là TN: 3 phương án nhiễu PHẢI xuất phát từ LỖI SAI ĐIỂN HÌNH "
                       "(nhầm công thức, quên đơn vị, sai dấu, chọn nhầm nghiệm loại…), KHÔNG nhiễu ngẫu nhiên."
                       if qtype == "TN" else "")

            vd_vdc_guide = (
                f"\n━━━ NGUYÊN TẮC RA ĐỀ THỰC TẾ (BẮT BUỘC) ━━━\n"
                f"1. NGỮ CẢNH thật tại Việt Nam (kinh doanh, sản xuất, xây dựng, nông nghiệp, "
                f"giao thông, tài chính, y tế…); số liệu hợp lý, tránh phi lý.\n"
                f"2. BÁM CHƯƠNG TRÌNH LỚP {grade}: chỉ dùng {grade_kb} KHÔNG vượt cấp.\n"
                f"3. ĐỦ 5 THÀNH PHẦN: ① Ngữ cảnh ② Dữ liệu cụ thể ③ Yêu cầu rõ "
                f"④ Mô hình hóa (HS tự lập PT/hàm/BPT) ⑤ Đa bước (≥2 bước suy luận).\n"
                f"4. PHÂN BIỆT MỨC ĐỘ:\n{level_rule}{tn_rule}\n"
                f"5. Số liệu ra kết quả \"đẹp\" hoặc làm tròn 2 chữ số thập phân; đáp số kèm đơn vị.\n"
                f"6. TỰ KIỂM: trước khi xuất, rà lại lời giải có đúng {level} không, có gắn đời sống không.\n"
            )

        return (
            f"Bạn là GV Toán Việt Nam giàu kinh nghiệm ra đề. Soạn 1 câu hỏi theo đúng mẫu.\n"
            f"Môn: {subject} — Lớp: {grade}\n"
            f"Loại: {QTYPE_LABELS.get(qtype, qtype)} | Mức độ: {level} ({level_desc}) | Chủ đề: {topic}"
            f"{req_line}"
            f"{vd_vdc_guide}\n"
            f"QUY TẮC ĐỊNH DẠNG: Công thức bọc ${{...}}$; đơn vị viết tiếng Việt NGOÀI $ "
            f"(VD: $x=3{{,}}5$ mét). Đáp án chính xác, lời giải rõ từng bước.\n\n"
            f"Chỉ trả về ĐÚNG 1 khối (không thêm ``` hay lời dẫn):\n{fmt}"
        )

    def _start_progress(self):
        """Hiện thanh tiến độ + bắt đầu đếm thời gian."""
        import time as _time
        self._q_start_time = _time.time()
        self._q_timer_running = True
        self._q_progress_frame.pack(fill="x", padx=14, pady=(4, 2),
                                    before=self._q_status_lbl)
        self._q_progress_bar.start(15)  # animation speed
        self._q_timer_lbl.config(text="0.0s")
        self._tick_timer()

    def _tick_timer(self):
        """Cập nhật thời gian mỗi 100ms."""
        if not self._q_timer_running:
            return
        import time as _time
        elapsed = _time.time() - self._q_start_time
        if elapsed < 60:
            self._q_timer_lbl.config(text=f"{elapsed:.1f}s")
        else:
            m, s = divmod(int(elapsed), 60)
            self._q_timer_lbl.config(text=f"{m}:{s:02d}")
        self.after(100, self._tick_timer)

    def _stop_progress(self, elapsed_text: str = ""):
        """Dừng thanh tiến độ + hiện thời gian hoàn thành."""
        self._q_timer_running = False
        self._q_progress_bar.stop()
        if elapsed_text:
            self._q_timer_lbl.config(text=elapsed_text)
        # Đổi sang determinate 100% để hiện hoàn thành
        self._q_progress_bar.config(mode="determinate", value=100)

    def _hide_progress(self):
        """Ẩn thanh tiến độ."""
        self._q_timer_running = False
        self._q_progress_bar.stop()
        self._q_progress_frame.pack_forget()

    def _generate_question(self):
        topic = self._q_topic_var.get().strip()
        if not topic:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn hoặc nhập chủ đề.", parent=self)
            return

        qtype = self._get_qtype()
        level = self._get_level()
        grade = self._q_grade_var.get()
        user_prompt = self._q_prompt_input.get("1.0", "end").strip()

        self._q_gen_btn.config(state="disabled", text="  ⏳ Đang tạo...  ")
        self._q_status_lbl.config(text="⏳ Đang gọi AI tạo câu hỏi...", fg="#F59E0B")
        self._q_preview_btn.config(state="disabled")
        self._q_insert_btn.config(state="disabled")
        self._start_progress()

        def _worker():
            MAX_RETRY = 3
            try:
                from core.parser import parse_one_question
                from core.models import assign_structured_ids
                import time as _time

                # Prompt gọn — không kèm toàn bộ chương trình học (nhanh hơn 3-5x)
                prompt = self._build_fast_prompt(
                    qtype, level, topic, grade, self._default_subject, user_prompt)

                if self._image_path:
                    prompt += (
                        "\n\nHÌNH ẢNH ĐÍNH KÈM: Quan sát hình ảnh và tạo câu hỏi "
                        "DỰA TRÊN nội dung hình ảnh.\n"
                    )

                last_err = None
                for attempt in range(MAX_RETRY):
                    # Kiểm tra cancel trước mỗi attempt (user đóng dialog)
                    if self._cancel_event.is_set():
                        return
                    try:
                        if attempt > 0:
                            self.after(0, lambda a=attempt: self._q_status_lbl.config(
                                text=f"⏳ Thử lại lần {a+1}/{MAX_RETRY}...", fg="#F59E0B"))
                            # event.wait(2) == time.sleep(2) trừ khi cancel
                            # được set → thoát ngay. Không block UI vì worker
                            # chạy trên thread riêng.
                            if self._cancel_event.wait(timeout=2):
                                return  # user đã đóng dialog

                        # Call AI
                        if self._image_path:
                            service = self._get_ai_service()
                            raw_response = service.generate_with_image(prompt, self._image_path)
                        else:
                            ai_call = self._get_ai_call()
                            raw_response = ai_call(prompt)

                        # Parse response
                        q = parse_one_question(raw_response)
                        if q:
                            q.topic = topic
                            q.requirement = user_prompt
                            assign_structured_ids([q], grade)
                            self._generated_question = q
                            self.after(0, lambda _q=q: self._on_gen_success(_q))
                            return
                        last_err = "AI trả về không đúng định dạng"
                    except Exception as e:
                        last_err = str(e)
                        continue

                self.after(0, lambda _m=last_err: self._on_gen_error(
                    f"Thử {MAX_RETRY} lần không thành công.\n{_m}"))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda _m=err_msg: self._on_gen_error(_m))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_close(self) -> None:
        """Gọi khi user đóng dialog (X / Esc).

        Set cancel_event để worker đang sleep retry-backoff thoát ngay,
        sau đó destroy widget. Worker chạy daemon nên sẽ không giữ tiến
        trình chính khi app tắt.
        """
        try:
            self._cancel_event.set()
        except Exception:
            pass
        self.destroy()

    def _elapsed_text(self) -> str:
        import time as _time
        elapsed = _time.time() - self._q_start_time
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        m, s = divmod(int(elapsed), 60)
        return f"{m}:{s:02d}"

    def _on_gen_success(self, q: Question):
        elapsed = self._elapsed_text()
        self._stop_progress(elapsed)
        self._q_gen_btn.config(state="normal", text="  ⚡ Tạo câu hỏi  ")
        self._q_preview_btn.config(state="normal")
        self._q_insert_btn.config(state="normal")

        qtype_label = QTYPE_LABELS.get(q.qtype, q.qtype)
        level_label = LEVEL_LABELS.get(q.level, q.level)
        self._q_status_lbl.config(
            text=f"✅ Đã tạo: [{q.question_id}] {qtype_label} — {level_label} "
                 f"({elapsed}) | Nhấn 'Xem & Chỉnh sửa' hoặc 'Chèn vào NHCH'",
            fg="#059669")

    def _on_gen_error(self, msg: str):
        elapsed = self._elapsed_text()
        self._stop_progress(elapsed)
        self._q_gen_btn.config(state="normal", text="  ⚡ Tạo câu hỏi  ")
        self._q_status_lbl.config(text=f"❌ Lỗi ({elapsed}): {msg[:100]}", fg="#DC2626")
        # Reset progress bar mode for next attempt
        self._q_progress_bar.config(mode="indeterminate", value=0)

    # ── Preview & Edit ────────────────────────────────────────────────────

    def _preview_question(self):
        q = self._generated_question
        if not q:
            return

        win = tk.Toplevel(self)
        win.title(f"📝 Xem & Chỉnh sửa — {q.question_id}")
        win.geometry("700x600")
        win.minsize(600, 500)
        win.grab_set()
        win.configure(bg="#FFFFFF")
        from ui import set_dialog_icon
        set_dialog_icon(win)

        # ── Header info ──
        info_f = tk.Frame(win, bg="#EFF6FF", bd=1, relief="groove")
        info_f.pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(info_f, text=f"ID: {q.question_id}  |  Loại: {QTYPE_LABELS.get(q.qtype, q.qtype)}  |  "
                              f"Mức độ: {LEVEL_LABELS.get(q.level, q.level)}  |  Chủ đề: {q.topic}",
                 bg="#EFF6FF", fg="#1E40AF", font=("Segoe UI", 10, "bold")).pack(padx=10, pady=8)

        # ── Scrollable edit area ──
        canvas = tk.Canvas(win, bg="#FFFFFF", highlightthickness=0)
        vsb = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="#FFFFFF")

        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 12), pady=6)
        canvas.pack(fill="both", expand=True, padx=(12, 0), pady=6)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _scroll(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _scroll)
        inner.bind("<MouseWheel>", _scroll)

        entries = {}

        def _add_field(label: str, key: str, value: str, height: int = 3):
            tk.Label(inner, text=label, bg="#FFFFFF", fg="#1E293B",
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
            t = tk.Text(inner, font=("Segoe UI", 10), height=height, wrap="word",
                        relief="solid", bd=1, padx=6, pady=4)
            t.pack(fill="x", padx=8, pady=(0, 4))
            t.insert("1.0", value)
            t.bind("<MouseWheel>", _scroll)
            entries[key] = t

        _add_field("📝 Câu hỏi:", "question", q.question, 4)

        if q.qtype == "TN":
            for opt_key in ["A", "B", "C", "D"]:
                _add_field(f"   {opt_key}.", f"opt_{opt_key}", q.options.get(opt_key, ""), 1)

            tk.Label(inner, text="🔑 Đáp án đúng:", bg="#FFFFFF", fg="#1E293B",
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
            ans_var = tk.StringVar(value=q.answer)
            ans_f = tk.Frame(inner, bg="#FFFFFF")
            ans_f.pack(anchor="w", padx=8, pady=(0, 4))
            for opt in ["A", "B", "C", "D"]:
                tk.Radiobutton(ans_f, text=opt, variable=ans_var, value=opt,
                               bg="#FFFFFF", font=("Segoe UI", 10, "bold"),
                               fg="#059669" if opt == q.answer else "#374151").pack(side="left", padx=6)
            entries["answer"] = ans_var

        elif q.qtype == "DS":
            for item_key in ["a", "b", "c", "d"]:
                _add_field(f"   {item_key})", f"item_{item_key}", q.items.get(item_key, ""), 1)
            # DS answers
            tk.Label(inner, text="🔑 Đáp án Đúng/Sai:", bg="#FFFFFF", fg="#1E293B",
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(8, 2))
            ds_ans_vars = {}
            ds_f = tk.Frame(inner, bg="#FFFFFF")
            ds_f.pack(anchor="w", padx=8, pady=(0, 4))
            for item_key in ["a", "b", "c", "d"]:
                v = tk.BooleanVar(value=q.answers.get(item_key, False))
                tk.Checkbutton(ds_f, text=f"{item_key}) Đúng", variable=v,
                               bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left", padx=8)
                ds_ans_vars[item_key] = v
            entries["ds_answers"] = ds_ans_vars

        elif q.qtype == "TLN":
            _add_field("🔑 Đáp án:", "answer_text", q.answer, 1)

        _add_field("💡 Lời giải:", "solution", q.solution, 3)

        # ── Save & close buttons ──
        btn_f = tk.Frame(win, bg="#FFFFFF")
        btn_f.pack(fill="x", padx=12, pady=(6, 12), side="bottom")

        def _save_edits():
            q.question = entries["question"].get("1.0", "end").strip()
            if q.qtype == "TN":
                for opt_key in ["A", "B", "C", "D"]:
                    q.options[opt_key] = entries[f"opt_{opt_key}"].get("1.0", "end").strip()
                q.answer = entries["answer"].get()
            elif q.qtype == "DS":
                for item_key in ["a", "b", "c", "d"]:
                    q.items[item_key] = entries[f"item_{item_key}"].get("1.0", "end").strip()
                for item_key, bv in entries["ds_answers"].items():
                    q.answers[item_key] = bv.get()
            elif q.qtype == "TLN":
                q.answer = entries["answer_text"].get("1.0", "end").strip()
            q.solution = entries["solution"].get("1.0", "end").strip()

            self._generated_question = q
            messagebox.showinfo("Đã lưu", f"Câu hỏi {q.question_id} đã được cập nhật.", parent=win)
            win.destroy()

        tk.Button(btn_f, text="  💾 Lưu chỉnh sửa  ", bg="#3B82F6", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                  padx=14, pady=6, command=_save_edits).pack(side="left", padx=4)
        tk.Button(btn_f, text="  Đóng  ", bg="#F1F5F9", fg="#475569",
                  font=("Segoe UI", 10), relief="flat", cursor="hand2",
                  padx=14, pady=6, command=win.destroy).pack(side="right", padx=4)

    # ── Insert to Question Bank ───────────────────────────────────────────

    def _insert_to_bank(self):
        q = self._generated_question
        if not q:
            return

        subject = self._default_subject
        grade = self._q_grade_var.get()

        try:
            self._on_add_to_bank(q, subject, grade)
            self._q_status_lbl.config(
                text=f"✅ Đã chèn [{q.question_id}] vào Ngân hàng câu hỏi thành công!",
                fg="#059669")
            self._q_insert_btn.config(state="disabled")
            messagebox.showinfo(
                "Thành công",
                f"Câu hỏi [{q.question_id}] đã được lưu vào Ngân hàng câu hỏi.\n"
                f"Loại: {QTYPE_LABELS.get(q.qtype, q.qtype)} | "
                f"Mức độ: {LEVEL_LABELS.get(q.level, q.level)}",
                parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể chèn câu hỏi:\n{e}", parent=self)
