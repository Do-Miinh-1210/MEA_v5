"""
ui/dialog_ai_gen_matrix.py — Dialog tạo ma trận đề kiểm tra bằng AI.

Cho phép user nhập: Môn, Lớp, Thời lượng, Học kỳ, Yêu cầu thêm
→ AI tự động tạo ma trận phù hợp chuẩn BGD.
"""

from __future__ import annotations
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable

from core.models import MatrixData
from ui.theme import C, FONT


class AIGenMatrixDialog(tk.Toplevel):
    """Dialog tạo ma trận đề bằng AI."""

    def __init__(self, parent, get_ai_call: Callable):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("🤖 Tạo ma trận đề bằng AI")

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(700, int(sw * 0.45))
        h = min(580, int(sh * 0.6))
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(True, True)
        self.minsize(600, 480)
        self.grab_set()

        self._get_ai_call = get_ai_call
        self._result: Optional[MatrixData] = None
        self._busy = False
        self._build()
        self.focus_force()

    @property
    def result(self) -> Optional[MatrixData]:
        return self._result

    def _build(self):
        BG = "#F8FAFC"
        self.configure(bg=BG)

        # ── Header ──
        hdr = tk.Frame(self, bg="#0F2D52")
        hdr.pack(fill="x")
        tk.Frame(self, bg="#10B981", height=3).pack(fill="x")

        tk.Label(
            hdr, text="🤖  TẠO MA TRẬN ĐỀ BẰNG AI",
            bg="#0F2D52", fg="white",
            font=(FONT["app"], 12, "bold"),
        ).pack(side="left", padx=16, pady=10)

        tk.Label(
            hdr, text="AI tự động phân bổ câu hỏi theo chuẩn BGD",
            bg="#0F2D52", fg="#94A3B8",
            font=(FONT["app"], 9),
        ).pack(side="right", padx=16, pady=10)

        # ── Body ──
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=12)

        # Row 1: Môn + Lớp
        row1 = tk.Frame(body, bg=BG)
        row1.pack(fill="x", pady=(0, 8))

        tk.Label(row1, text="Môn học:", bg=BG, fg=C["text_main"],
                 font=(FONT["app"], 10, "bold")).pack(side="left")
        self._subject_var = tk.StringVar(value="Toán")
        subjects = [
            "Toán", "Vật lý", "Hóa học", "Sinh học",
            "Ngữ văn", "Tiếng Anh",
            "Lịch sử", "Địa lý", "GDCD/GDKTPL",
            "Tin học", "Công nghệ",
        ]
        sub_cb = ttk.Combobox(row1, textvariable=self._subject_var,
                              values=subjects, width=14, state="readonly",
                              font=(FONT["app"], 10))
        sub_cb.pack(side="left", padx=(8, 20))

        tk.Label(row1, text="Lớp:", bg=BG, fg=C["text_main"],
                 font=(FONT["app"], 10, "bold")).pack(side="left")
        self._grade_var = tk.StringVar(value="12")
        grade_cb = ttk.Combobox(
            row1, textvariable=self._grade_var,
            values=[str(i) for i in range(6, 13)],
            width=5, state="readonly",
            font=(FONT["app"], 10))
        grade_cb.pack(side="left", padx=(8, 0))

        # Row 2: Thời lượng + Học kỳ
        row2 = tk.Frame(body, bg=BG)
        row2.pack(fill="x", pady=(0, 8))

        tk.Label(row2, text="Thời lượng:", bg=BG, fg=C["text_main"],
                 font=(FONT["app"], 10, "bold")).pack(side="left")
        self._duration_var = tk.StringVar(value="45 phút")
        dur_cb = ttk.Combobox(
            row2, textvariable=self._duration_var,
            values=["15 phút", "45 phút", "60 phút", "90 phút"],
            width=10, state="readonly",
            font=(FONT["app"], 10))
        dur_cb.pack(side="left", padx=(8, 20))

        tk.Label(row2, text="Học kỳ:", bg=BG, fg=C["text_main"],
                 font=(FONT["app"], 10, "bold")).pack(side="left")
        self._semester_var = tk.StringVar(value="I")
        sem_cb = ttk.Combobox(
            row2, textvariable=self._semester_var,
            values=["I", "II"],
            width=5, state="readonly",
            font=(FONT["app"], 10))
        sem_cb.pack(side="left", padx=(8, 0))

        # Row 3: Yêu cầu thêm
        tk.Label(body, text="Yêu cầu thêm (tùy chọn):", bg=BG,
                 fg=C["text_main"],
                 font=(FONT["app"], 10, "bold")).pack(anchor="w", pady=(4, 4))

        hint_text = (
            "Ví dụ:\n"
            "• Tập trung chương Đạo hàm và Tích phân\n"
            "• Thêm nhiều câu hình học không gian\n"
            "• Bao gồm bài tập thực tế, ứng dụng\n"
            "• Không ra câu chương Xác suất"
        )
        self._extra_text = tk.Text(
            body, height=5, wrap="word",
            font=(FONT["app"], 10),
            bg="white", fg=C["text_body"],
            relief="solid", bd=1,
            highlightcolor=C["primary"],
            highlightthickness=1,
        )
        self._extra_text.pack(fill="x", pady=(0, 4))
        self._extra_text.insert("1.0", "")
        # Placeholder
        self._extra_text._placeholder = hint_text
        self._extra_text.insert("1.0", hint_text)
        self._extra_text.configure(fg=C["text_hint"])
        self._extra_text.bind("<FocusIn>", self._on_text_focus_in)
        self._extra_text.bind("<FocusOut>", self._on_text_focus_out)

        # ── Info box: AI sẽ tạo gì ──
        info_frame = tk.Frame(body, bg="#EBF5FF",
                              highlightbackground=C["primary"],
                              highlightthickness=1)
        info_frame.pack(fill="x", pady=(8, 8))

        tk.Label(
            info_frame,
            text="💡 AI sẽ tự động:",
            bg="#EBF5FF", fg=C["primary"],
            font=(FONT["app"], 10, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(8, 2))

        for tip in [
            "• Phân bổ câu hỏi TN / DS / TLN / TL theo chuẩn BGD",
            "• Chia mức độ NB / TH / VD phù hợp thời lượng",
            "• Chọn chủ đề đa dạng theo chương trình lớp đã chọn",
            "• Tổng điểm = 10.0, có yêu cầu cần đạt chi tiết",
        ]:
            tk.Label(
                info_frame, text=tip,
                bg="#EBF5FF", fg=C["text_body"],
                font=(FONT["app"], 9), anchor="w",
            ).pack(fill="x", padx=12, pady=1)
        tk.Label(info_frame, text="", bg="#EBF5FF").pack(pady=2)

        # ── Progress ──
        self._progress_var = tk.StringVar(value="")
        self._progress_lbl = tk.Label(
            body, textvariable=self._progress_var,
            bg=BG, fg=C["primary"],
            font=(FONT["app"], 9, "bold"))
        self._progress_lbl.pack(anchor="w", pady=(0, 4))

        # ── Buttons ──
        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(fill="x", pady=(4, 0))

        self._gen_btn = tk.Button(
            btn_row, text="🤖 Tạo ma trận",
            bg="#10B981", fg="white",
            activebackground="#059669", activeforeground="white",
            font=(FONT["app"], 11, "bold"),
            relief="flat", cursor="hand2", bd=0,
            padx=20, pady=8,
            command=self._start_generate,
        )
        self._gen_btn.pack(side="left", padx=(0, 8))

        tk.Button(
            btn_row, text="Đóng",
            bg=C["surface_2"], fg=C["text_body"],
            activebackground=C["surface_3"],
            font=(FONT["app"], 10),
            relief="flat", cursor="hand2", bd=0,
            padx=16, pady=8,
            command=self.destroy,
        ).pack(side="right")

    # ── Placeholder handling ──

    def _on_text_focus_in(self, _event=None):
        if self._extra_text.get("1.0", "end-1c") == self._extra_text._placeholder:
            self._extra_text.delete("1.0", "end")
            self._extra_text.configure(fg=C["text_body"])

    def _on_text_focus_out(self, _event=None):
        if not self._extra_text.get("1.0", "end-1c").strip():
            self._extra_text.insert("1.0", self._extra_text._placeholder)
            self._extra_text.configure(fg=C["text_hint"])

    # ── Generate ──

    def _start_generate(self):
        if self._busy:
            return
        import time

        self._busy = True
        self._gen_btn.configure(state="disabled", text="⏳ Đang tạo…")
        self._ai_progress_msg = "Đang gọi AI tạo ma trận..."
        self._ai_started_at = time.monotonic()
        self._ai_timer_active = True
        self._render_progress()
        self._tick_timer()

        subject = self._subject_var.get()
        grade = self._grade_var.get()
        duration = self._duration_var.get()
        semester = self._semester_var.get()

        extra = self._extra_text.get("1.0", "end-1c").strip()
        if extra == self._extra_text._placeholder:
            extra = ""

        def _on_progress(msg: str):
            def _update():
                self._ai_progress_msg = msg
                self._render_progress()
            self.after(0, _update)

        def _worker():
            try:
                from core.ai_matrix_recognizer import generate_matrix_from_description

                ai_gen = self._get_ai_call()
                service = ai_gen.__self__

                result = generate_matrix_from_description(
                    subject=subject,
                    grade=grade,
                    duration=duration,
                    semester=semester,
                    ai_call=service.generate,
                    extra_requirements=extra,
                    on_progress=_on_progress,
                )
                self.after(0, self._on_done, result)
            except Exception as e:
                self.after(0, self._on_error, str(e))

        threading.Thread(target=_worker, daemon=True).start()

    # ── Progress timer ────────────────────────────────────────────────────
    def _tick_timer(self):
        if not getattr(self, "_ai_timer_active", False):
            return
        try:
            self._render_progress()
        except Exception:
            return
        self.after(1000, self._tick_timer)

    def _format_elapsed(self) -> str:
        import time
        if not hasattr(self, "_ai_started_at"):
            return "0s"
        elapsed = int(time.monotonic() - self._ai_started_at)
        mins, secs = divmod(elapsed, 60)
        return f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

    def _render_progress(self):
        msg = getattr(self, "_ai_progress_msg", "Đang xử lý")
        self._progress_var.set(f"🤖 {msg}   ⏱ {self._format_elapsed()}")

    def _on_done(self, result: Optional[MatrixData]):
        self._ai_timer_active = False
        elapsed_str = self._format_elapsed()
        self._busy = False
        self._gen_btn.configure(state="normal", text="🤖 Tạo ma trận")

        if result is None or not result.rows:
            self._progress_var.set(f"❌ AI không tạo được ma trận (sau {elapsed_str}). Thử lại.")
            messagebox.showerror(
                "Lỗi",
                f"AI không tạo được ma trận (đã chạy {elapsed_str}).\nKiểm tra API key và thử lại.",
                parent=self)
            return

        self._progress_var.set(
            f"✅ Đã tạo {len(result.rows)} câu trong {elapsed_str} — {result.title}")

        # Hiện dialog xác nhận
        from ui.dialog_ai_matrix import AIMatrixConfirmDialog
        dlg = AIMatrixConfirmDialog(self, result)
        self.wait_window(dlg)

        if dlg.result is not None:
            self._result = dlg.result
            self.destroy()
        else:
            self._progress_var.set("Đã hủy. Nhấn 'Tạo ma trận' để thử lại.")

    def _on_error(self, err: str):
        self._ai_timer_active = False
        elapsed_str = self._format_elapsed() if hasattr(self, "_ai_started_at") else ""
        self._busy = False
        self._gen_btn.configure(state="normal", text="🤖 Tạo ma trận")
        suffix = f" (sau {elapsed_str})" if elapsed_str else ""
        self._progress_var.set(f"❌ Lỗi{suffix}: {err[:80]}")
        messagebox.showerror("Lỗi AI", f"Lỗi khi gọi AI{suffix}:\n{err}", parent=self)
