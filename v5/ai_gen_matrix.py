"""
v5/ai_gen_matrix.py — Dialog "Tạo ma trận bằng AI" (CTk port).

Khác với Smart Prompt:
  • Smart Prompt: free-text description → AI parse → MatrixData.
  • AI Gen Matrix: form fields (môn / lớp / thời lượng / HK / yêu cầu thêm)
    → ``core.ai_matrix_recognizer.generate_matrix_from_description``.

API:
    AIGenMatrixDialogV5(parent, on_accept=lambda matrix, subject, grade: ...)
"""
from __future__ import annotations

import threading
import time
from tkinter import messagebox
from typing import Callable, Optional

import customtkinter as ctk

from v5.ui_perf import UiThrottle


SUBJECTS = [
    "Toán", "Vật lý", "Hóa học", "Sinh học",
    "Ngữ văn", "Tiếng Anh",
    "Lịch sử", "Địa lý", "GDCD/GDKTPL",
    "Tin học", "Công nghệ",
]
GRADES = [str(i) for i in range(6, 13)]
DURATIONS = ["15 phút", "45 phút", "60 phút", "90 phút"]
SEMESTERS = ["I", "II"]

PLACEHOLDER = (
    "Ví dụ:\n"
    "• Tập trung chương Đạo hàm và Tích phân\n"
    "• Thêm nhiều câu hình học không gian\n"
    "• Bao gồm bài tập thực tế, ứng dụng\n"
    "• Không ra câu chương Xác suất"
)


class AIGenMatrixDialogV5(ctk.CTkToplevel):
    WIDTH = 720
    HEIGHT = 640

    def __init__(self, parent,
                 on_accept: Optional[Callable] = None,
                 default_subject: str = "Toán",
                 default_grade: str = "12"):
        super().__init__(parent)
        self.title("🤖  Tạo ma trận đề bằng AI")
        self._on_accept = on_accept
        self._busy = False
        self._started_at = 0.0
        self._timer_active = False
        self._result = None

        try:
            sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
            x = (sw - self.WIDTH) // 2; y = (sh - self.HEIGHT) // 2
            self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        except Exception:
            self.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        try: self.attributes("-topmost", True)
        except: pass
        try: self.grab_set()
        except: pass

        self._subject_var  = ctk.StringVar(value=default_subject)
        self._grade_var    = ctk.StringVar(value=default_grade)
        self._duration_var = ctk.StringVar(value="45 phút")
        self._semester_var = ctk.StringVar(value="I")
        self._progress_var = ctk.StringVar(value="")

        self._build()
        self.bind("<Escape>", lambda e: self._on_close())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        if self._busy:
            if not messagebox.askyesno("Đang chạy",
                "AI đang tạo ma trận. Bạn có chắc muốn huỷ?",
                parent=self):
                return
        self._timer_active = False
        self.destroy()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=("#0F2D52", "#0B1F35"),
                            corner_radius=0, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🤖  TẠO MA TRẬN ĐỀ BẰNG AI",
                      text_color="white",
                      font=("Segoe UI", 14, "bold")
                      ).pack(side="left", padx=16, pady=12)
        ctk.CTkLabel(hdr,
                      text="AI tự phân bổ câu hỏi theo chuẩn BGD",
                      text_color="#94A3B8",
                      font=("Segoe UI", 10)
                      ).pack(side="right", padx=16, pady=12)
        ctk.CTkFrame(self, fg_color="#10B981", height=3,
                      corner_radius=0).pack(fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=12)

        # Row: Môn + Lớp
        row1 = ctk.CTkFrame(body, fg_color="transparent")
        row1.pack(fill="x", pady=4)
        ctk.CTkLabel(row1, text="Môn học:", width=80,
                      font=("Segoe UI", 11, "bold")
                      ).pack(side="left")
        ctk.CTkOptionMenu(row1, variable=self._subject_var,
                            values=SUBJECTS, width=160
                            ).pack(side="left", padx=(4, 24))
        ctk.CTkLabel(row1, text="Lớp:", width=40,
                      font=("Segoe UI", 11, "bold")
                      ).pack(side="left")
        ctk.CTkOptionMenu(row1, variable=self._grade_var,
                            values=GRADES, width=80
                            ).pack(side="left", padx=4)

        # Row: Duration + HK
        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=4)
        ctk.CTkLabel(row2, text="Thời lượng:", width=80,
                      font=("Segoe UI", 11, "bold")
                      ).pack(side="left")
        ctk.CTkOptionMenu(row2, variable=self._duration_var,
                            values=DURATIONS, width=120
                            ).pack(side="left", padx=(4, 24))
        ctk.CTkLabel(row2, text="Học kỳ:", width=60,
                      font=("Segoe UI", 11, "bold")
                      ).pack(side="left")
        ctk.CTkOptionMenu(row2, variable=self._semester_var,
                            values=SEMESTERS, width=70
                            ).pack(side="left", padx=4)

        # Extra requirements
        ctk.CTkLabel(body, text="Yêu cầu thêm (tuỳ chọn):",
                      font=("Segoe UI", 11, "bold"),
                      anchor="w").pack(anchor="w", pady=(12, 4))
        self._extra_text = ctk.CTkTextbox(
            body, height=110, font=("Segoe UI", 11),
            fg_color=("#FFFFFF", "#0F172A"))
        self._extra_text.pack(fill="x", pady=(0, 4))
        self._extra_text.insert("1.0", PLACEHOLDER)
        self._is_placeholder = True
        self._extra_text.configure(text_color=("#94A3B8", "#64748B"))
        self._extra_text.bind("<FocusIn>", self._on_text_focus_in)
        self._extra_text.bind("<FocusOut>", self._on_text_focus_out)

        # Info box
        info = ctk.CTkFrame(body, fg_color=("#EBF5FF", "#172033"),
                              corner_radius=8)
        info.pack(fill="x", pady=(10, 8))
        ctk.CTkLabel(info, text="💡 AI sẽ tự động:",
                      text_color=("#1E40AF", "#93C5FD"),
                      font=("Segoe UI", 11, "bold"),
                      anchor="w"
                      ).pack(anchor="w", padx=12, pady=(8, 2))
        for tip in [
            "• Phân bổ câu hỏi TN / DS / TLN / TL theo chuẩn BGD",
            "• Chia mức độ NB / TH / VD phù hợp thời lượng",
            "• Chọn chủ đề đa dạng theo chương trình lớp đã chọn",
            "• Tổng điểm = 10.0, có yêu cầu cần đạt chi tiết",
        ]:
            ctk.CTkLabel(info, text=tip,
                          text_color=("#374151", "#E5E7EB"),
                          font=("Segoe UI", 10), anchor="w"
                          ).pack(anchor="w", padx=12, pady=1)
        ctk.CTkLabel(info, text="", font=("Segoe UI", 4)
                      ).pack(pady=2)

        # Progress
        self._progress_lbl = ctk.CTkLabel(
            body, textvariable=self._progress_var,
            text_color=("#1F497D", "#60A5FA"),
            font=("Segoe UI", 10, "bold"), anchor="w")
        self._progress_lbl.pack(anchor="w", pady=(0, 4))

        # Buttons
        btns = ctk.CTkFrame(self, fg_color=("#F3F4F6", "#0F172A"),
                              height=56, corner_radius=0)
        btns.pack(fill="x", side="bottom")
        btns.pack_propagate(False)
        ctk.CTkButton(btns, text="❌  Đóng", width=110, height=34,
                       fg_color=("#6B7280", "#374151"),
                       hover_color=("#4B5563", "#1F2937"),
                       command=self._on_close
                       ).pack(side="right", padx=10, pady=10)
        self._gen_btn = ctk.CTkButton(
            btns, text="🤖  Tạo ma trận", width=170, height=34,
            fg_color="#10B981", hover_color="#059669",
            font=("Segoe UI", 12, "bold"),
            command=self._start_generate)
        self._gen_btn.pack(side="right", padx=4, pady=10)

    # ── Placeholder text handling ─────────────────────────────────────
    def _on_text_focus_in(self, _e=None):
        if self._is_placeholder:
            self._extra_text.delete("1.0", "end")
            self._extra_text.configure(text_color=("#1F2937", "#F1F5F9"))
            self._is_placeholder = False

    def _on_text_focus_out(self, _e=None):
        text = self._extra_text.get("1.0", "end-1c").strip()
        if not text:
            self._extra_text.delete("1.0", "end")
            self._extra_text.insert("1.0", PLACEHOLDER)
            self._extra_text.configure(text_color=("#94A3B8", "#64748B"))
            self._is_placeholder = True

    # ── Generate ───────────────────────────────────────────────────────
    def _start_generate(self):
        if self._busy:
            return
        # Lấy AI generator
        try:
            from services.key_manager import get_key_manager
            from services.ai_service import create_ai_service
            km = get_key_manager()
            ai_call = None
            for prov, model in [
                ("Google Gemini",    "gemini-3.8-flash"),
                ("Anthropic Claude", "claude-sonnet-4-5"),
                ("DeepSeek",         "deepseek-chat"),
                ("OpenAI",           "gpt-4o-mini"),
            ]:
                k = km.load(prov)
                if k:
                    from services.retry_service import split_keys
                    keys = k if isinstance(k, list) else split_keys(k)
                    svc = create_ai_service(prov, keys, model)
                    ai_call = svc.generate
                    break
            if not ai_call:
                messagebox.showerror(
                    "Thiếu API Key",
                    "Chưa cấu hình AI provider.\n"
                    "Vào ⚙️ Cấu hình → AI Provider để nhập API Key.",
                    parent=self)
                return
        except Exception as e:
            messagebox.showerror("Lỗi AI", f"{type(e).__name__}: {e}",
                                  parent=self)
            return

        self._busy = True
        self._gen_btn.configure(state="disabled", text="⏳ Đang tạo…")
        self._started_at = time.monotonic()
        self._timer_active = True
        self._cur_msg = "Đang gọi AI tạo ma trận…"
        self._render_progress()
        self._tick_timer()

        subject  = self._subject_var.get()
        grade    = self._grade_var.get()
        duration = self._duration_var.get()
        semester = self._semester_var.get()
        extra = ("" if self._is_placeholder
                  else self._extra_text.get("1.0", "end-1c").strip())
        progress_throttle = UiThrottle(self, 80)

        def _on_progress(msg: str):
            progress_throttle.schedule(self._set_progress_message, msg)

        def _worker():
            try:
                from core.ai_matrix_recognizer import (
                    generate_matrix_from_description)
                matrix = generate_matrix_from_description(
                    subject=subject, grade=grade,
                    duration=duration, semester=semester,
                    ai_call=ai_call,
                    extra_requirements=extra,
                    on_progress=_on_progress,
                )
                try: self.after(0, lambda: (
                    progress_throttle.cancel(),
                    self._on_done(matrix)))
                except Exception: pass
            except Exception as e:
                try: self.after(0, lambda err=str(e): (
                    progress_throttle.cancel(),
                    self._on_error(err)))
                except Exception: pass

        threading.Thread(target=_worker, daemon=True).start()

    def _set_progress_message(self, msg: str) -> None:
        self._cur_msg = msg
        self._render_progress()

    def _tick_timer(self):
        if not self._timer_active: return
        try: self._render_progress()
        except Exception: return
        try: self.after(1000, self._tick_timer)
        except Exception: pass

    def _format_elapsed(self) -> str:
        elapsed = int(time.monotonic() - self._started_at)
        m, s = divmod(elapsed, 60)
        return f"{m}m {s:02d}s" if m > 0 else f"{s}s"

    def _render_progress(self):
        try:
            self._progress_var.set(
                f"🤖 {self._cur_msg}   ⏱ {self._format_elapsed()}")
        except Exception: pass

    def _on_done(self, matrix):
        self._timer_active = False
        elapsed = self._format_elapsed()
        self._busy = False
        try: self._gen_btn.configure(state="normal", text="🤖  Tạo ma trận")
        except Exception: pass

        if matrix is None or not getattr(matrix, "rows", None):
            self._progress_var.set(
                f"❌ AI không tạo được ma trận (sau {elapsed}). Thử lại.")
            messagebox.showerror(
                "Lỗi",
                f"AI không tạo được ma trận (đã chạy {elapsed}).\n"
                "Kiểm tra API key và thử lại.", parent=self)
            return

        self._progress_var.set(
            f"✅ Đã tạo {len(matrix.rows)} câu trong {elapsed} — "
            f"{matrix.title[:50]}")

        # Confirm và áp dụng
        if not messagebox.askyesno(
            "Áp dụng?",
            f"AI đã tạo ma trận:\n\n"
            f"  📋 {matrix.title}\n"
            f"  📝 {len(matrix.rows)} câu\n"
            f"  ⏱ {matrix.time_str}\n\n"
            f"Áp dụng vào Exam Create?",
            parent=self): return

        try:
            if callable(self._on_accept):
                self._on_accept(matrix,
                                  self._subject_var.get(),
                                  self._grade_var.get())
        except Exception as e:
            messagebox.showerror("Lỗi callback", str(e), parent=self)
            return

        self.destroy()

    def _on_error(self, err: str):
        self._timer_active = False
        elapsed = self._format_elapsed()
        self._busy = False
        try: self._gen_btn.configure(state="normal", text="🤖  Tạo ma trận")
        except Exception: pass
        self._progress_var.set(f"❌ Lỗi (sau {elapsed}): {err[:80]}")
        messagebox.showerror("Lỗi AI",
            f"Lỗi khi gọi AI (sau {elapsed}):\n{err}", parent=self)
