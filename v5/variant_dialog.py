"""
v5/variant_dialog.py — Dialog V5 tạo đề tương tự từ đề hiện tại.

Port phần "đề tương tự" của tab_result V4 sang CustomTkinter:
  • Copy prompt thủ công để dùng với ChatGPT/Claude/Gemini ngoài app.
  • Sinh nhanh bằng services.similar_generator (Python/SymPy, không tốn API).
  • Sinh rộng hơn bằng services.ai_variant_generator qua provider đã cấu hình.

Module này chỉ gọi service/core dùng chung, không import UI Tkinter V4.
"""
from __future__ import annotations

import threading
import time
from tkinter import messagebox
from typing import Any, Callable

import customtkinter as ctk

from v5.ui_perf import UiThrottle


class VariantExamDialog(ctk.CTkToplevel):
    """CTk modal tạo bản đề tương tự rồi trả về ExamData qua callback."""

    WIDTH = 760
    HEIGHT = 640

    def __init__(
        self,
        parent,
        exam: Any,
        *,
        on_apply: Callable[[Any, dict], None] | None = None,
        get_ai_call: Callable[[], Callable[[str], str] | None] | None = None,
    ):
        super().__init__(parent)
        self.title("🧬  Tạo đề tương tự")
        self._exam = exam
        self._on_apply = on_apply
        self._get_ai_call = get_ai_call
        self._result_exam = None
        self._result_meta: dict = {}
        self._busy = False
        self._started_at = 0.0

        try:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = (sw - self.WIDTH) // 2
            y = (sh - self.HEIGHT) // 2
            self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        except Exception:
            self.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        try:
            self.attributes("-topmost", True)
        except Exception:
            pass
        try:
            self.grab_set()
        except Exception:
            pass

        self._mode_var = ctk.StringVar(value="sympy")
        self._seed_var = ctk.StringVar(value=str(int(time.time()) % 10000))
        self._retry_var = ctk.StringVar(value="2")
        self._status_var = ctk.StringVar(value="Chọn chế độ rồi bấm Sinh bản tương tự.")

        self._build()
        self.bind("<Escape>", lambda _e: self._on_close())
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self) -> None:
        hdr = ctk.CTkFrame(self, fg_color=("#1E3A8A", "#0F172A"),
                           corner_radius=0, height=62)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr,
            text="🧬  TẠO ĐỀ TƯƠNG TỰ",
            text_color="white",
            font=("Segoe UI", 15, "bold"),
            anchor="w",
        ).pack(side="left", padx=18, pady=12)

        total = len(getattr(self._exam, "questions", []) or [])
        title = (getattr(self._exam, "exam_title", "") or "Đề hiện tại")[:52]
        ctk.CTkLabel(
            hdr,
            text=f"{total} câu • {title}",
            text_color="#BFDBFE",
            font=("Segoe UI", 10),
            anchor="e",
        ).pack(side="right", padx=18, pady=12)

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=14)

        self._build_manual_card(body)
        self._build_auto_card(body)
        self._build_result_card(body)

        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=18, pady=(0, 14))
        self._apply_btn = ctk.CTkButton(
            foot,
            text="✓ Áp dụng vào đề hiện tại",
            fg_color="#10B981",
            hover_color="#059669",
            state="disabled",
            command=self._apply_result,
        )
        self._apply_btn.pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            foot,
            text="Đóng",
            fg_color="#6B7280",
            hover_color="#4B5563",
            command=self._on_close,
        ).pack(side="right")

    def _build_manual_card(self, parent) -> None:
        card = self._card(parent, "1. Prompt thủ công cho chatbot ngoài app")
        ctk.CTkLabel(
            card,
            text=(
                "Dùng khi bạn đã xuất Word gốc và muốn tự upload sang ChatGPT, "
                "Claude hoặc Gemini web. Prompt giữ cấu trúc đề, chỉ thay số và "
                "yêu cầu AI tính lại đáp án."
            ),
            wraplength=680,
            justify="left",
            text_color=("gray25", "gray75"),
        ).pack(fill="x", pady=(0, 10))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkButton(
            row,
            text="📋 Copy prompt",
            width=150,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self._copy_manual_prompt,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            row,
            text="✏️ Xem / sửa prompt",
            width=170,
            command=self._open_prompt_preview,
        ).pack(side="left", padx=4)

    def _build_auto_card(self, parent) -> None:
        card = self._card(parent, "2. Sinh bản tương tự trong V5")
        ctk.CTkLabel(
            card,
            text=(
                "Python/SymPy rất nhanh nhưng chỉ nhận một số dạng toán an toàn. "
                "AI chậm hơn, tốn API, nhưng xử lý được nhiều kiểu câu hơn."
            ),
            wraplength=680,
            justify="left",
            text_color=("gray25", "gray75"),
        ).pack(fill="x", pady=(0, 10))

        mode_row = ctk.CTkFrame(card, fg_color="transparent")
        mode_row.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(mode_row, text="Chế độ:", width=78,
                     font=("Segoe UI", 11, "bold")).pack(side="left")
        seg = ctk.CTkSegmentedButton(
            mode_row,
            values=["Python/SymPy", "AI provider"],
            command=lambda v: self._mode_var.set(
                "ai" if v.startswith("AI") else "sympy"),
        )
        seg.set("Python/SymPy")
        seg.pack(side="left", padx=4)

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", pady=6)
        ctk.CTkLabel(form, text="Seed:", width=78, anchor="w").pack(side="left")
        ctk.CTkEntry(form, textvariable=self._seed_var, width=110).pack(
            side="left", padx=(0, 18))
        ctk.CTkLabel(form, text="AI retry:", width=70, anchor="w").pack(side="left")
        ctk.CTkOptionMenu(
            form,
            variable=self._retry_var,
            values=["1", "2", "3"],
            width=80,
        ).pack(side="left")

        try:
            from services import similar_generator as _similar
            if getattr(_similar, "sp", None) is None:
                kinds = "SymPy chưa khả dụng trong runtime này; dùng AI provider hoặc prompt thủ công."
            else:
                kinds = " • ".join(_similar.supported_kinds())
        except Exception:
            kinds = "Phương trình bậc nhất • Phương trình bậc hai"
        ctk.CTkLabel(
            card,
            text=f"SymPy hiện hỗ trợ: {kinds}",
            text_color="gray",
            font=("Segoe UI", 10),
            wraplength=680,
            justify="left",
        ).pack(fill="x", pady=(2, 8))

        run_row = ctk.CTkFrame(card, fg_color="transparent")
        run_row.pack(fill="x", pady=(8, 0))
        self._run_btn = ctk.CTkButton(
            run_row,
            text="▶ Sinh bản tương tự",
            fg_color="#7C3AED",
            hover_color="#6D28D9",
            width=180,
            command=self._generate,
        )
        self._run_btn.pack(side="left", padx=(0, 8))
        self._progress = ctk.CTkProgressBar(run_row, width=250)
        self._progress.set(0)
        self._progress.pack(side="left", padx=8)

    def _build_result_card(self, parent) -> None:
        card = self._card(parent, "3. Kết quả")
        self._status = ctk.CTkLabel(
            card,
            textvariable=self._status_var,
            text_color="gray",
            font=("Segoe UI", 11),
            anchor="w",
            justify="left",
            wraplength=680,
        )
        self._status.pack(fill="x")

    def _card(self, parent, title: str):
        outer = ctk.CTkFrame(parent, fg_color=("#FFFFFF", "#1F2937"),
                             corner_radius=12, border_width=1,
                             border_color=("#E5E7EB", "#374151"))
        outer.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(inner, text=title, font=("Segoe UI", 13, "bold"),
                     anchor="w").pack(anchor="w", pady=(0, 8))
        return inner

    def _copy_manual_prompt(self) -> None:
        from services.ai_variant_generator import get_manual_variant_prompt

        self._copy_text(get_manual_variant_prompt())
        self._status_var.set(
            "✓ Đã copy prompt. Hãy xuất Word gốc, upload vào chatbot ngoài app "
            "rồi dán prompt này.")

    def _open_prompt_preview(self) -> None:
        from services.ai_variant_generator import get_manual_variant_prompt

        PromptPreviewDialog(self, get_manual_variant_prompt())

    def _copy_text(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        try:
            self.update()
        except Exception:
            pass

    def _generate(self) -> None:
        if self._busy:
            return
        if not getattr(self._exam, "questions", None):
            messagebox.showwarning("Chưa có đề", "Hãy tạo hoặc nạp đề trước.",
                                   parent=self)
            return

        mode = self._mode_var.get()
        self._busy = True
        self._result_exam = None
        self._result_meta = {}
        self._apply_btn.configure(state="disabled")
        self._run_btn.configure(state="disabled", text="⏳ Đang sinh...")
        self._status.configure(text_color="gray")
        self._progress.set(0)
        self._started_at = time.time()

        def _worker():
            try:
                if mode == "ai":
                    result = self._generate_ai()
                else:
                    result = self._generate_sympy()
                self.after(0, lambda r=result: self._on_done(*r))
            except Exception as exc:
                self.after(0, lambda err=str(exc): self._on_error(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _generate_sympy(self):
        from services import similar_generator as _similar

        if getattr(_similar, "sp", None) is None:
            raise RuntimeError(
                "SymPy chưa khả dụng trong runtime này. Hãy dùng AI provider "
                "hoặc copy prompt thủ công.")

        try:
            seed = int(self._seed_var.get() or "0")
        except ValueError:
            seed = 0
        self.after(0, lambda: self._status_var.set(
            "Đang thay số bằng Python/SymPy..."))
        exam, replaced, kept = _similar.make_variant_exam(self._exam, seed=seed)
        self._mark_exam_title(exam, "Đề tương tự")
        return exam, {
            "mode": "sympy",
            "replaced": replaced,
            "kept": kept,
            "total": replaced + kept,
        }

    def _generate_ai(self):
        from services.ai_variant_generator import generate_ai_variant_exam

        ai_call = self._get_ai_call() if callable(self._get_ai_call) else None
        if not ai_call:
            raise RuntimeError(
                "Chưa có API key/provider khả dụng. Hãy cấu hình AI hoặc dùng "
                "Python/SymPy / prompt thủ công.")
        try:
            retry = int(self._retry_var.get() or "2")
        except ValueError:
            retry = 2
        progress_throttle = UiThrottle(self, 80)

        def _progress(done: int, total: int) -> None:
            progress_throttle.schedule(self._update_ai_variant_progress, done, total)

        try:
            exam, replaced, kept = generate_ai_variant_exam(
                self._exam,
                ai_call=ai_call,
                progress_cb=_progress,
                max_retry=max(1, retry),
            )
        finally:
            try:
                self.after(0, progress_throttle.cancel)
            except Exception:
                pass
        self._mark_exam_title(exam, "Đề tương tự AI")
        return exam, {
            "mode": "ai",
            "replaced": replaced,
            "kept": kept,
            "total": replaced + kept,
        }

    def _update_ai_variant_progress(self, done: int, total: int) -> None:
        self._progress.set(done / max(total, 1))
        self._status_var.set(f"AI đang tạo biến thể: {done}/{total} câu...")

    def _mark_exam_title(self, exam, suffix: str) -> None:
        title = getattr(exam, "exam_title", "") or "Đề kiểm tra"
        if suffix.lower() not in title.lower():
            try:
                exam.exam_title = f"{title} - {suffix}"
            except Exception:
                pass

    def _on_done(self, exam, meta: dict) -> None:
        self._busy = False
        self._result_exam = exam
        self._result_meta = meta
        self._run_btn.configure(state="normal", text="▶ Sinh bản tương tự")
        self._progress.set(1)
        self._status.configure(text_color="#10B981")
        elapsed = max(0.1, time.time() - self._started_at)
        mode = "AI" if meta.get("mode") == "ai" else "Python/SymPy"
        replaced = int(meta.get("replaced", 0))
        kept = int(meta.get("kept", 0))
        self._status_var.set(
            f"✓ {mode} đã tạo xong trong {elapsed:.1f}s: "
            f"{replaced} câu thay số, {kept} câu giữ nguyên. "
            "Bấm Áp dụng để nạp vào màn Tạo đề.")
        if replaced > 0:
            self._apply_btn.configure(state="normal")
        else:
            self._status.configure(text_color="#F59E0B")
            self._status_var.set(
                "Chưa thay được câu nào. Với đề phức tạp, hãy dùng AI provider "
                "hoặc copy prompt thủ công sang chatbot ngoài app.")

    def _on_error(self, error: str) -> None:
        self._busy = False
        self._run_btn.configure(state="normal", text="▶ Sinh bản tương tự")
        self._progress.set(0)
        self._status.configure(text_color="#EF4444")
        self._status_var.set(f"✘ Không tạo được đề tương tự: {error[:240]}")

    def _apply_result(self) -> None:
        if self._result_exam is None:
            return
        if callable(self._on_apply):
            self._on_apply(self._result_exam, dict(self._result_meta))
        self.destroy()

    def _on_close(self) -> None:
        if self._busy:
            if not messagebox.askyesno(
                "Đang chạy",
                "Tác vụ tạo đề tương tự vẫn đang chạy. Bạn có muốn đóng dialog?",
                parent=self,
            ):
                return
        self.destroy()


class PromptPreviewDialog(ctk.CTkToplevel):
    """Preview/edit prompt thủ công trước khi copy."""

    WIDTH = 780
    HEIGHT = 620

    def __init__(self, parent, prompt: str, *, title: str | None = None, intro: str | None = None):
        super().__init__(parent)
        self.title(title or "📋  Prompt tạo đề tương tự")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        try:
            self.transient(parent)
            self.grab_set()
        except Exception:
            pass

        ctk.CTkLabel(
            self,
            text=intro or "Bạn có thể sửa tuỳ chọn trong prompt rồi copy sang chatbot ngoài app.",
            anchor="w",
            font=("Segoe UI", 11),
            text_color="gray",
        ).pack(fill="x", padx=14, pady=(14, 8))

        self._box = ctk.CTkTextbox(self, wrap="word")
        self._box.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self._box.insert("1.0", prompt)

        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.pack(fill="x", padx=14, pady=(0, 14))
        ctk.CTkButton(
            foot,
            text="📋 Copy nội dung đang sửa",
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self._copy,
        ).pack(side="left")
        ctk.CTkButton(
            foot,
            text="Đóng",
            fg_color="#6B7280",
            command=self.destroy,
        ).pack(side="right")
        self.bind("<Escape>", lambda _e: self.destroy())

    def _copy(self) -> None:
        text = self._box.get("1.0", "end").strip()
        self.clipboard_clear()
        self.clipboard_append(text)
        try:
            self.update()
        except Exception:
            pass
