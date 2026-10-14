"""
ui/tab_qc.py — Tab ⑤ QC Pipeline: Kiểm soát chất lượng đa lớp.

Giao diện cho pipeline: Generator → Solver → Critic → Engine → Score → Pass/Reject
"""

from __future__ import annotations
import logging
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from typing import Callable, Optional

_log = logging.getLogger(__name__)

from core.models import ExamData, Question
from core.quality_pipeline import (
    QualityScore, run_qc_pipeline_batch, build_qc_summary,
    _get_kb_warnings,
)
from config import APP_DIR, TYPE_LABELS


# Màu sắc theo verdict
_COL_PASS   = "#2E7D32"   # Xanh lá
_COL_REVIEW = "#E65100"   # Cam
_COL_REJECT = "#C62828"   # Đỏ
_COL_BG_PASS   = "#F1F8E9"
_COL_BG_REVIEW = "#FFF3E0"
_COL_BG_REJECT = "#FFEBEE"


class TabQC(ttk.Frame):
    """Tab ⑤ — QC Pipeline."""

    def __init__(self, parent,
                 get_ai_call: Callable,
                 get_subject_grade: Callable,
                 get_exam_data: Callable):
        super().__init__(parent)
        self._get_ai          = get_ai_call
        self._get_subj_grade  = get_subject_grade
        self._get_exam        = get_exam_data
        self._results: list[tuple[Question, QualityScore]] = []
        self._qc_timer_active = False
        self._qc_started_at = 0.0
        self._qc_done = 0
        self._qc_total = 0
        self._qc_topic = ""
        self._qc_retry_count = 0
        self._qc_last_retry = ""
        self._build()

    # ── Build ──────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # ── Config panel ────────────────────────────────────────────────────
        cfg = ttk.LabelFrame(self, text="⚙️  Cấu hình kiểm tra chất lượng")
        cfg.pack(fill="x", padx=8, pady=4)
        cfg_inner = tk.Frame(cfg); cfg_inner.pack(fill="x", padx=10, pady=8)

        # Checkboxes chọn bước
        self._run_solver = tk.BooleanVar(value=True)
        self._run_critic = tk.BooleanVar(value=True)
        self._run_math   = tk.BooleanVar(value=True)

        tk.Label(cfg_inner, text="Bật/tắt các bước:",
                 font=("Segoe UI",9,"bold")).grid(row=0, column=0, sticky="w", padx=12)
        for col, (text, var, tip) in enumerate([
            ("🧠  AI Giải độc lập (kiểm chứng 2 lần)", self._run_solver,
             "Giải độc lập 2 lần, so sánh kết quả"),
            ("🔍  AI Phản biện (tìm lỗi)",     self._run_critic,
             "Chỉ tìm lỗi logic/wording/bẫy"),
            ("📐  Kiểm tra toán học (sympy)",      self._run_math,
             "Kiểm tra nghiệm bằng sympy"),
        ], start=1):
            f = tk.Frame(cfg_inner); f.grid(row=0, column=col, sticky="w", padx=8)
            ttk.Checkbutton(f, text=text, variable=var).pack(anchor="w")
            tk.Label(f, text=tip, fg="#777", font=("Segoe UI",7)).pack(anchor="w")

        # Score thresholds
        thresh_f = tk.Frame(cfg_inner); thresh_f.grid(row=0, column=4, padx=0, sticky="w")
        tk.Label(thresh_f, text="Ngưỡng điểm:",
                 font=("Segoe UI",9,"bold")).pack(anchor="w")
        tk.Label(thresh_f,
                 text="≥ 0.90 → ✅ PASS\n0.80–0.89 → ⚠️ Review\n< 0.80 → ❌ Reject",
                 fg="#555", font=("Segoe UI",8), justify="left").pack(anchor="w")

        # ── Action bar: modern dark toolbar (2 hàng chống tràn màn hình) ──
        act = tk.Frame(self, bg="#1E293B")
        act.pack(fill="x")

        act_row1 = tk.Frame(act, bg="#1E293B")
        act_row1.pack(fill="x", padx=4, pady=(4, 2))

        tk.Label(act_row1, text="  ✅  QC Pipeline",
                bg="#1E293B", fg="white",
                font=("Segoe UI", 10, "bold")).pack(side="left", padx=4, pady=2)

        for txt, cmd, bg_c in [
            ("▶ Chạy QC",        self._run_pipeline,     "#10B981"),
            ("🔁 Tạo lại lỗi",  self._regen_rejected, "#F59E0B"),
            ("📥 Báo cáo",       self._export_report,  "#0284C7"),
            ("✅ Áp dụng kết quả", self._apply_passed, "#059669"),
        ]:
            tk.Button(act_row1, text=txt, command=cmd,
                    bg=bg_c, fg="white", activebackground=bg_c,
                    font=("Segoe UI", 8, "bold"),
                    relief="flat", cursor="hand2", bd=0,
                    padx=10, pady=4).pack(side="left", padx=2)

        act_row2 = tk.Frame(act, bg="#0F172A")
        act_row2.pack(fill="x", padx=4, pady=(0, 4))

        self._ai_fix_btn = tk.Button(act_row2, text="🤖 AI sửa lỗi",
                   bg="#7C3AED", fg="white", activebackground="#6D28D9",
                   font=("Segoe UI", 8, "bold"),
                   relief="flat", cursor="hand2", bd=0,
                   padx=10, pady=4, command=self._ai_fix_failed)
        self._ai_fix_btn.pack(side="left", padx=2)

        # [SMART-4] Auto-fix loop — sửa đến khi đạt (max 3 vòng)
        self._auto_fix_btn = tk.Button(
            act_row2, text="🔄 Tự sửa đến khi đạt",
            bg="#10B981", fg="white", activebackground="#059669",
            font=("Segoe UI", 8, "bold"),
            relief="flat", cursor="hand2", bd=0,
            padx=10, pady=4, command=self._auto_fix_until_pass,
        )
        self._auto_fix_btn.pack(side="left", padx=2)

        # Xem câu hỏi đang chọn dưới dạng PDF (LaTeX render trực tiếp,
        # vector quality, zoom được). Khác với detail panel chỉ show text.
        self._view_pdf_btn = tk.Button(act_row2, text="📄 Xem PDF",
                   bg="#1E40AF", fg="white", activebackground="#1E3A8A",
                   font=("Segoe UI", 8, "bold"),
                   relief="flat", cursor="hand2", bd=0,
                   padx=10, pady=4, command=self._view_question_pdf)
        self._view_pdf_btn.pack(side="left", padx=2)

        self._progress = ttk.Progressbar(act_row2, mode="determinate", length=140)
        self._progress.pack(side="left", padx=8)
        self._prog_lbl = tk.Label(act_row2, text="", fg="#94A3B8",
                                   font=("Segoe UI", 9, "bold"), bg="#0F172A")
        self._prog_lbl.pack(side="left")

        self._qc_status_lbl = tk.Label(
            self,
            text="",
            fg="#334155",
            bg="#F8FAFC",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
            justify="left",
            padx=10,
            pady=3,
        )
        self._qc_status_lbl.pack(fill="x")
        self._qc_status_lbl.bind(
            "<Configure>",
            lambda e: self._qc_status_lbl.config(wraplength=max(320, e.width - 20)),
        )

        # ── Summary bar ──────────────────────────────────────────────────────
        self._summary_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self._summary_var,
                 fg="#1F497D", font=("Segoe UI",9,"bold"),
                 bg="#F0F4FF", anchor="w", padx=10).pack(fill="x")

        # ── Main area: Tree + Detail ─────────────────────────────────────────
        main = tk.Frame(self); main.pack(fill="both", expand=True, padx=8, pady=4)

        # Treeview kết quả
        cols = ("Câu", "Loại", "Mức", "Score", "Verdict",
                "Solver1", "Solver2", "Double✓", "Lỗi Critic", "Math")
        self._tree = ttk.Treeview(main, columns=cols, show="headings", height=16)
        ws = {"Câu":45,"Loại":70,"Mức":45,"Score":65,"Verdict":80,
              "Solver1":70,"Solver2":70,"Double✓":65,"Lỗi Critic":200,"Math":60}
        for c in cols:
            self._tree.heading(c, text=c)
            self._tree.column(c, width=ws[c], minwidth=40)

        # Tags màu
        self._tree.tag_configure("pass",   foreground=_COL_PASS,   background=_COL_BG_PASS)
        self._tree.tag_configure("review", foreground=_COL_REVIEW, background=_COL_BG_REVIEW)
        self._tree.tag_configure("reject", foreground=_COL_REJECT, background=_COL_BG_REJECT)

        vsb = ttk.Scrollbar(main, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(main, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Detail panel
        detail_f = tk.Frame(main, width=320); detail_f.grid(row=0, column=2, sticky="ns", padx=0)
        detail_f.grid_propagate(False)
        tk.Label(detail_f, text="Chi tiết QC",
                 font=("Segoe UI",9,"bold")).pack(anchor="w", pady=4)
        self._detail = scrolledtext.ScrolledText(
            detail_f, font=("Segoe UI",9), state="disabled",
            wrap="word", width=36, height=20)
        self._detail.pack(fill="both", expand=True)
        self._detail.tag_configure("hdr",    font=("Segoe UI",9,"bold"), foreground="#1F497D")
        self._detail.tag_configure("pass",   foreground=_COL_PASS)
        self._detail.tag_configure("review", foreground=_COL_REVIEW)
        self._detail.tag_configure("reject", foreground=_COL_REJECT)
        self._detail.tag_configure("sep",    foreground="#AAAAAA")

    # ── Run Pipeline ───────────────────────────────────────────────────────

    def _format_qc_elapsed(self) -> str:
        if not self._qc_started_at:
            return "00:00"
        elapsed = int(time.monotonic() - self._qc_started_at)
        m, s = divmod(elapsed, 60)
        return f"{m:02d}:{s:02d}"

    def _start_qc_timer(self, total: int) -> None:
        self._qc_timer_active = True
        self._qc_started_at = time.monotonic()
        self._qc_done = 0
        self._qc_total = total
        self._qc_topic = ""
        self._qc_retry_count = 0
        self._qc_last_retry = ""
        self._render_qc_status()
        self._tick_qc_timer()

    def _tick_qc_timer(self) -> None:
        if not self._qc_timer_active:
            return
        self._render_qc_status()
        self.after(1000, self._tick_qc_timer)

    def _render_qc_status(self) -> None:
        if not self._qc_timer_active:
            return
        retry = f"  |  Retry: {self._qc_retry_count}" if self._qc_retry_count else ""
        last = f"  |  {self._qc_last_retry}" if self._qc_last_retry else ""
        topic = f"  |  {self._qc_topic[:80]}" if self._qc_topic else ""
        self._qc_status_lbl.config(
            text=(
                f"Đang chạy QC  [{self._qc_done}/{self._qc_total}]  "
                f"⏱ {self._format_qc_elapsed()}{retry}{topic}{last}"
            ),
            fg="#1E40AF",
        )

    def _stop_qc_timer(self, prefix: str, color: str = "#059669") -> str:
        elapsed = self._format_qc_elapsed()
        self._qc_timer_active = False
        retry = f"  |  Retry: {self._qc_retry_count}" if self._qc_retry_count else ""
        self._qc_status_lbl.config(text=f"{prefix}  ⏱ {elapsed}{retry}", fg=color)
        return elapsed

    def _on_qc_retry(self, i: int, total: int, stage: str,
                     attempt: int, wait_s: float, err: str) -> None:
        self._qc_done = max(0, i - 1)
        self._qc_total = total
        self._qc_retry_count += 1
        self._qc_last_retry = (
            f"{stage}: retry {attempt}, chờ {wait_s:g}s"
            f" ({err[:60]})"
        )
        self._render_qc_status()

    def _run_pipeline(self) -> None:
        exam = self._get_exam()
        if not exam:
            messagebox.showwarning("Chưa có đề", "Vui lòng tạo đề ở Tab ③ trước.")
            return
        try:
            ai_call = self._get_ai()
        except Exception as e:
            messagebox.showerror("Lỗi AI", str(e)); return

        questions = [q for q in exam.questions if not q._error]
        if not questions:
            messagebox.showwarning("Không có câu", "Không có câu hợp lệ để kiểm tra.")
            return

        subject, grade = self._get_subj_grade()

        n_steps = (1 if self._run_solver.get() else 0) * 2 + \
                  (1 if self._run_critic.get() else 0) + \
                  (1 if self._run_math.get() else 0)
        est = len(questions) * max(n_steps, 1)
        if not messagebox.askyesno(
            "Chạy QC Pipeline",
            f"Sẽ chạy QC cho {len(questions)} câu hỏi.\n"
            f"Các bước bật: Solver={self._run_solver.get()}, "
            f"Critic={self._run_critic.get()}, Math={self._run_math.get()}\n"
            f"Ước tính ~{est} lần gọi AI. Tiếp tục?",
        ): return

        self._progress.config(maximum=len(questions), value=0)
        self._prog_lbl.config(text="[0/{}]".format(len(questions)))
        self._start_qc_timer(len(questions))
        self._tree.delete(*self._tree.get_children())
        self._summary_var.set("")
        checkpoint_path = APP_DIR / "qc_checkpoints" / "latest_qc.json"

        def _do():
            def pcb(i, total, topic):
                self.after(0, lambda _i=i, _t=total, _tp=topic: (
                    self._progress.config(value=_i),
                    self._prog_lbl.config(text=f"[{_i}/{_t}]"),
                    setattr(self, "_qc_done", _i),
                    setattr(self, "_qc_total", _t),
                    setattr(self, "_qc_topic", _tp or ""),
                    self._render_qc_status(),
                ))
            def rcb(i, total, stage, attempt, wait_s, err):
                self.after(0, lambda: self._on_qc_retry(
                    i, total, stage, attempt, wait_s, err,
                ))
            try:
                results = run_qc_pipeline_batch(
                    questions=questions,
                    subject=subject,
                    grade=grade,
                    ai_call=ai_call,
                    run_solver=self._run_solver.get(),
                    run_critic=self._run_critic.get(),
                    run_math=self._run_math.get(),
                    progress_cb=pcb,
                    retry_cb=rcb,
                    checkpoint_path=checkpoint_path,
                    resume=True,
                    adaptive=True,
                )
            except Exception as exc:
                self.after(0, lambda e=exc: self._on_pipeline_error(str(e)))
                return
            self.after(0, lambda r=results: self._on_pipeline_done(r))

        threading.Thread(target=_do, daemon=True).start()

    def _on_pipeline_done(self, results: list[tuple[Question, QualityScore]]) -> None:
        self._results = results
        self._progress.config(value=self._progress.cget("maximum"))
        self._prog_lbl.config(text="✅ Hoàn thành!")
        self._stop_qc_timer("QC hoàn thành")

        # Populate tree
        self._tree.delete(*self._tree.get_children())
        for i, (q, score) in enumerate(results, 1):
            if score.passed and not score.needs_review:
                tag    = "pass"
                verdict = "✅ PASS"
            elif score.needs_review:
                tag    = "review"
                verdict = "⚠️ Review"
            else:
                tag    = "reject"
                verdict = "❌ Reject"

            double_ok = "✓" if score.double_solve_ok >= 0.9 else "✗"
            math_str  = "✓" if score.math_engine_ok is True else (
                "✗" if score.math_engine_ok is False else "—")
            issues_str = "; ".join(score.critic_issues[:2]) if score.critic_issues else "Không"

            self._tree.insert("", "end", iid=str(i), values=(
                i,
                TYPE_LABELS.get(q.qtype, q.qtype),
                q.level,
                f"{score.final_score:.2f}",
                verdict,
                score.solver1_answer[:12],
                score.solver2_answer[:12],
                double_ok,
                issues_str[:60],
                math_str,
            ), tags=(tag,))

        # Summary
        summary = build_qc_summary(results)
        self._summary_var.set(
            f"Tổng: {summary['total']} câu  │  "
            f"✅ Pass: {summary['passed']}  │  "
            f"⚠️ Review: {summary['needs_review']}  │  "
            f"❌ Reject: {summary['rejected']}  │  "
            f"Điểm TB: {summary['avg_score']:.2f}  │  "
            f"Double đồng ý: {summary['double_agree']}/{summary['total']}  │  "
            f"Pass rate: {summary['pass_rate']}%"
        )

    def _on_pipeline_error(self, err: str) -> None:
        self._prog_lbl.config(text="❌ Lỗi QC")
        self._stop_qc_timer("QC lỗi", color="#DC2626")
        messagebox.showerror("Lỗi QC", err[:800], parent=self)

    # ── Detail panel ───────────────────────────────────────────────────────

    def _on_select(self, _event) -> None:
        sel = self._tree.selection()
        if not sel: return
        idx = int(sel[0]) - 1
        if idx < 0 or idx >= len(self._results): return
        q, score = self._results[idx]
        self._show_detail(q, score)

    def _show_detail(self, q: Question, score: QualityScore) -> None:
        dt = self._detail
        dt.config(state="normal"); dt.delete("1.0","end")

        def ins(t, tag=None):
            if tag: dt.insert("end", t, tag)
            else:   dt.insert("end", t)

        # Header
        verdict_tag = "pass" if (score.passed and not score.needs_review) \
                      else ("review" if score.needs_review else "reject")
        verdict_txt = "✅ PASS" if verdict_tag == "pass" else \
                      ("⚠️ Cần Review" if verdict_tag == "review" else "❌ Reject")
        ins(f"{verdict_txt}  │  Score: {score.final_score:.3f}\n", verdict_tag)
        ins("─"*36 + "\n", "sep")

        # Score breakdown
        ins("📊 QUALITY SCORE:\n", "hdr")
        scores = [
            ("Toán học",      score.math_correctness),
            ("Double-solve",  score.double_solve_ok),
            ("Rõ ràng",       score.clarity),
            ("Độ khó",        score.difficulty_match),
            ("Format",        score.format_ok),
            ("Mơ hồ(-)‍",     -score.ambiguity),
        ]
        for name, val in scores:
            bar_len = int(abs(val) * 12)
            bar = "█" * bar_len + "░" * (12 - bar_len)
            color = "pass" if val >= 0.8 else ("review" if val >= 0.6 else "reject")
            ins(f"  {name:<12} {bar} {val:+.2f}\n", color)

        ins("─"*36 + "\n", "sep")

        # Double Solve
        ins("🧠 DOUBLE SOLVE:\n", "hdr")
        match = score.double_solve_ok >= 0.9
        ins(f"  Solver 1: {score.solver1_answer}\n")
        ins(f"  Solver 2: {score.solver2_answer}\n")
        ins(f"  Kết quả: {'✓ Đồng ý' if match else '✗ Khác nhau!'}\n",
            "pass" if match else "reject")

        ins("─"*36 + "\n", "sep")

        # Critic
        ins("🔍 CRITIC:\n", "hdr")
        if score.critic_issues:
            for issue in score.critic_issues:
                ins(f"  ⚠️ {issue}\n", "review")
        else:
            ins("  ✓ Không phát hiện lỗi\n", "pass")

        # Math Engine
        ins("─"*36 + "\n", "sep")
        ins("📐 MATH ENGINE:\n", "hdr")
        if score.math_engine_ok is True:
            ins("  ✓ Nghiệm đúng\n", "pass")
        elif score.math_engine_ok is False:
            ins("  ✗ Nghiệm sai!\n", "reject")
        else:
            ins("  — Không kiểm tra được\n")

        # Reject reason
        if score.reject_reason:
            ins("─"*36 + "\n", "sep")
            ins("❌ LÝ DO REJECT:\n", "hdr")
            ins(f"  {score.reject_reason}\n", "reject")

        # KB warnings
        kb = _get_kb_warnings(q.topic)
        if kb:
            ins("─"*36 + "\n", "sep")
            ins("📚 Knowledge Base:\n", "hdr")
            ins(f"  {kb}\n")

        # Question preview
        ins("─"*36 + "\n", "sep")
        ins("📝 NỘI DUNG:\n", "hdr")
        ins(q.question[:200] + ("…" if len(q.question)>200 else "") + "\n")

        dt.config(state="disabled")

    # ── Actions ────────────────────────────────────────────────────────────

    def _view_question_pdf(self) -> None:
        """Render câu hỏi đang chọn → PDF (qua pdflatex) → mở dialog PDFPreview.

        Cho phép xem câu với LaTeX/math chuẩn ở vector quality, zoom được —
        thay vì chỉ đọc text trong detail panel.
        """
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo(
                "Chưa chọn câu",
                "Hãy click chọn 1 câu trong bảng trước khi xem PDF.",
                parent=self,
            )
            return
        idx = int(sel[0]) - 1
        if idx < 0 or idx >= len(self._results):
            return
        q, score = self._results[idx]

        # Build LaTeX body cho câu hỏi (text + math) + đáp án nếu có
        body_parts: list[str] = [
            r"\textbf{Câu " + str(idx + 1) + r":} ",
            self._latex_escape_question(q.question),
        ]
        # Trắc nghiệm: liệt kê 4 phương án A/B/C/D
        if q.qtype in ("TN", "NPA") and getattr(q, "options", None):
            body_parts.append(r"\par\medskip")
            for i, opt in enumerate(q.options[:6]):
                letter = "ABCDEF"[i]
                body_parts.append(
                    rf"\par \textbf{{{letter}.}} " + self._latex_escape_question(opt)
                )
        # Đúng/Sai: 4 mệnh đề
        elif q.qtype == "DS" and getattr(q, "ds_items", None):
            body_parts.append(r"\par\medskip")
            for i, item in enumerate(q.ds_items[:6]):
                letter = "abcd"[i]
                truth = "Đ" if item.is_true else "S"
                body_parts.append(
                    rf"\par \textbf{{{letter})}} ({truth}) "
                    + self._latex_escape_question(item.statement)
                )
        # Đáp án (nếu có)
        if getattr(q, "answer", None):
            body_parts.append(r"\par\medskip\textbf{Đáp án:} ")
            body_parts.append(self._latex_escape_question(str(q.answer)))

        body = "\n".join(body_parts)

        from ui.pdf_preview_dialog import PDFPreviewDialog
        PDFPreviewDialog.from_latex(
            self,
            latex_source=body,
            title=f"Câu {idx + 1} — {TYPE_LABELS.get(q.qtype, q.qtype)}",
        )

    @staticmethod
    def _latex_escape_question(text: str) -> str:
        """Escape ký tự LaTeX nguy hiểm trong text câu hỏi.

        GIỮ LẠI nguyên các block math `$...$` và `\\(...\\)` vì câu hỏi
        Toán THPT thường có công thức. Chỉ escape các ký tự ngoài math:
          & % # _ { } ~ ^ \\
        """
        import re
        if not text:
            return ""
        # Tách block math (giữ nguyên), escape phần còn lại
        # Match: $...$, \(...\), \[...\]
        pattern = re.compile(r"(\$[^$]*\$|\\\([^)]*\\\)|\\\[[^\]]*\\\])")
        parts = pattern.split(text)
        out = []
        for i, p in enumerate(parts):
            if i % 2 == 1:
                # Math block — giữ nguyên
                out.append(p)
            else:
                # Text thường — escape
                p = p.replace("\\", r"\textbackslash{}")
                p = p.replace("&", r"\&")
                p = p.replace("%", r"\%")
                p = p.replace("#", r"\#")
                p = p.replace("_", r"\_")
                p = p.replace("{", r"\{")
                p = p.replace("}", r"\}")
                p = p.replace("~", r"\textasciitilde{}")
                p = p.replace("^", r"\textasciicircum{}")
                out.append(p)
        return "".join(out)

    def _regen_rejected(self) -> None:
        """Tạo lại các câu bị Reject."""
        if not self._results:
            messagebox.showinfo("Chưa có kết quả","Chạy QC Pipeline trước."); return
        rejected = [(i, q, s) for i, (q, s) in enumerate(self._results) if not s.passed]
        if not rejected:
            messagebox.showinfo("Tốt lắm!","Không có câu nào bị Reject ✅"); return
        if not messagebox.askyesno("Tạo lại",
                                   f"Tạo lại {len(rejected)} câu bị Reject?"):
            return
        try:
            ai_call = self._get_ai()
        except Exception as e:
            messagebox.showerror("Lỗi AI", str(e)); return

        subject, grade = self._get_subj_grade()
        self._prog_lbl.config(text=f"🔁 Đang tạo lại {len(rejected)} câu…")

        def _do():
            from core.generator import generate_one
            from core.models import MatrixRow
            fixed = 0
            for list_idx, q, s in rejected:
                snap = q._row_snapshot or {}
                row  = MatrixRow(
                    stt="", topic=snap.get("topic", q.topic),
                    level=snap.get("level", q.level),
                    qtype=snap.get("qtype", q.qtype),
                    codes=snap.get("codes", []),
                    requirement=snap.get("requirement", q.requirement),
                    points=snap.get("points", q.points),
                )
                new_q = generate_one(row, subject, grade, ai_call)
                # Re-run QC
                new_q_out, new_score = run_qc_pipeline_batch(
                    [new_q], subject, grade, ai_call,
                    run_solver=self._run_solver.get(),
                    run_critic=self._run_critic.get(),
                    run_math=self._run_math.get(),
                )[0]
                self._results[list_idx] = (new_q_out, new_score)
                if new_score.passed:
                    fixed += 1
            self.after(0, lambda: (
                self._on_pipeline_done(self._results),
                messagebox.showinfo("Xong", f"Đã cải thiện {fixed}/{len(rejected)} câu."),
            ))

        threading.Thread(target=_do, daemon=True).start()


    def _ai_fix_failed(self) -> None:
        """Dùng AI Reviewer sửa các câu không đạt (score < 0.8)."""
        if not self._results:
            messagebox.showinfo("Chưa có kết quả", "Chạy QC Pipeline trước."); return

        failed = [(i, q, s) for i, (q, s) in enumerate(self._results)
                  if not s.passed or s.needs_review]
        if not failed:
            messagebox.showinfo("Tốt lắm!", "Không có câu nào cần sửa ✅"); return

        if not messagebox.askyesno(
            "AI sửa câu không đạt",
            f"Dùng AI Reviewer sửa {len(failed)} câu không đạt?\n"
            f"Style: safe (chỉ sửa lỗi toán/format, giữ nguyên nội dung)."
        ): return

        try:
            ai_call = self._get_ai()
        except Exception as e:
            messagebox.showerror("Lỗi AI", str(e)); return

        subject, grade = self._get_subj_grade()
        self._prog_lbl.config(text=f"🤖 Đang sửa {len(failed)} câu…")
        self._progress["maximum"] = len(failed)
        self._progress["value"]   = 0

        def _do():
            try:
                from core.ai_reviewer import fix_question
                fixed = 0
                for idx, (list_idx, q, s) in enumerate(failed):
                    try:
                        fixed_q, meta = fix_question(
                            q, subject, grade, ai_call, style_mode="safe"
                        )
                        # Re-run QC trên câu đã sửa
                        from core.quality_pipeline import run_qc_pipeline
                        fixed_q_out, new_score = run_qc_pipeline(
                            fixed_q, subject, grade, ai_call,
                            run_solver=self._run_solver.get(),
                            run_critic=self._run_critic.get(),
                            run_math=self._run_math.get(),
                        )
                        self._results[list_idx] = (fixed_q_out, new_score)
                        if new_score.passed and not new_score.needs_review:
                            fixed += 1
                    except Exception:
                        pass
                    self.after(0, lambda v=idx+1: self._progress.config(value=v))

                self.after(0, lambda: (
                    self._on_pipeline_done(self._results),
                    self._prog_lbl.config(text=f"✅ Đã sửa {fixed}/{len(failed)} câu"),
                    messagebox.showinfo("Hoàn tất",
                        f"AI đã sửa {fixed}/{len(failed)} câu.\n"
                        f"{len(failed)-fixed} câu vẫn cần xem lại thủ công."),
                ))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda m=err_msg: messagebox.showerror("Lỗi", m))

        threading.Thread(target=_do, daemon=True).start()

    # ── [SMART-4] Auto-fix loop ────────────────────────────────────────────

    _AUTO_FIX_MAX_ROUNDS = 3
    _AUTO_FIX_TARGET_AVG = 0.85    # Dừng sớm nếu avg score ≥ 0.85

    def _auto_fix_until_pass(self) -> None:
        """[SMART-4] Loop AI fix nhiều vòng cho đến khi đề đạt chất lượng.

        Mỗi vòng:
          1. Tìm tất cả câu fail (score < 0.8 hoặc needs_review).
          2. AI Reviewer sửa từng câu.
          3. Re-run QC trên câu đã sửa.
          4. Check avg score → stop nếu ≥ TARGET hoặc số câu fail = 0.
          5. Lặp tối đa _AUTO_FIX_MAX_ROUNDS vòng.
        """
        if not self._results:
            messagebox.showinfo(
                "Chưa có kết quả",
                "Chạy QC Pipeline trước khi auto-fix.")
            return

        # Snapshot ban đầu: lấy initial scores
        initial_failed = [(i, q, s)
                           for i, (q, s) in enumerate(self._results)
                           if not s.passed or s.needs_review]
        if not initial_failed:
            messagebox.showinfo(
                "Tốt lắm!",
                "Không có câu nào cần sửa. Tất cả đã PASS ✅")
            return

        if not messagebox.askyesno(
            "🔄 Tự sửa đến khi đạt",
            f"AI sẽ lặp tối đa {self._AUTO_FIX_MAX_ROUNDS} vòng:\n"
            f"  • Vòng đầu: sửa {len(initial_failed)} câu fail.\n"
            f"  • Re-run QC sau mỗi vòng.\n"
            f"  • Dừng sớm nếu avg score ≥ {self._AUTO_FIX_TARGET_AVG} hoặc hết câu fail.\n\n"
            f"Quá trình có thể mất vài phút và tốn nhiều lượt API.\n"
            f"Tiếp tục?"
        ):
            return

        try:
            ai_call = self._get_ai()
        except Exception as e:
            messagebox.showerror("Lỗi AI", str(e))
            return

        subject, grade = self._get_subj_grade()
        self._auto_fix_btn.config(state="disabled")
        self._ai_fix_btn.config(state="disabled")

        def _do():
            from core.ai_reviewer import fix_question
            from core.quality_pipeline import run_qc_pipeline

            total_fixed = 0
            rounds_used = 0
            for round_no in range(1, self._AUTO_FIX_MAX_ROUNDS + 1):
                rounds_used = round_no
                failed = [(i, q, s)
                          for i, (q, s) in enumerate(self._results)
                          if not s.passed or s.needs_review]
                if not failed:
                    _log.info("Auto-fix: round %d — không còn câu fail", round_no)
                    break

                self.after(0, lambda r=round_no, n=len(failed):
                           self._prog_lbl.config(
                               text=f"🔄 Vòng {r}/{self._AUTO_FIX_MAX_ROUNDS}: "
                                    f"sửa {n} câu fail…"))
                self.after(0, lambda n=len(failed): self._progress.config(
                    maximum=n, value=0))

                fixed_this_round = 0
                for f_idx, (list_idx, q, s) in enumerate(failed):
                    try:
                        fixed_q, _meta = fix_question(
                            q, subject, grade, ai_call, style_mode="safe")
                        fixed_q_out, new_score = run_qc_pipeline(
                            fixed_q, subject, grade, ai_call,
                            run_solver=self._run_solver.get(),
                            run_critic=self._run_critic.get(),
                            run_math=self._run_math.get(),
                        )
                        self._results[list_idx] = (fixed_q_out, new_score)
                        if new_score.passed and not new_score.needs_review:
                            fixed_this_round += 1
                    except Exception as e:
                        _log.warning("Auto-fix round %d câu %d failed: %s",
                                     round_no, list_idx, e)

                    self.after(0, lambda v=f_idx + 1:
                               self._progress.config(value=v))

                total_fixed += fixed_this_round
                # Compute avg score sau vòng
                if self._results:
                    avg = sum(s.score for _, s in self._results) / len(self._results)
                else:
                    avg = 0.0
                _log.info(
                    "Auto-fix round %d: fixed %d câu, avg score %.2f",
                    round_no, fixed_this_round, avg)

                # Stop early nếu đạt target
                if avg >= self._AUTO_FIX_TARGET_AVG:
                    _log.info("Auto-fix: avg %.2f ≥ target %.2f → dừng",
                              avg, self._AUTO_FIX_TARGET_AVG)
                    break

            # Final report
            final_failed = [
                (i, q, s) for i, (q, s) in enumerate(self._results)
                if not s.passed or s.needs_review
            ]
            avg_final = (
                sum(s.score for _, s in self._results) / len(self._results)
                if self._results else 0.0
            )

            def _finalize():
                self._on_pipeline_done(self._results)
                self._auto_fix_btn.config(state="normal")
                self._ai_fix_btn.config(state="normal")
                self._prog_lbl.config(
                    text=f"✅ Auto-fix xong: {rounds_used} vòng, avg {avg_final:.2f}")
                msg = (
                    f"🔄 Auto-fix hoàn tất ({rounds_used} vòng):\n\n"
                    f"  • Đã sửa: {total_fixed} câu\n"
                    f"  • Avg score cuối: {avg_final:.2f}\n"
                    f"  • Còn fail: {len(final_failed)} câu\n"
                )
                if avg_final >= self._AUTO_FIX_TARGET_AVG:
                    msg += "\n✅ Đạt target — đề đã chất lượng cao."
                elif len(final_failed) == 0:
                    msg += "\n✅ Không còn câu fail."
                else:
                    msg += (
                        f"\n⚠️ Vẫn còn {len(final_failed)} câu chưa đạt "
                        f"sau {rounds_used} vòng. Hãy review thủ công."
                    )
                messagebox.showinfo("Auto-fix kết quả", msg)

            self.after(0, _finalize)

        threading.Thread(target=_do, daemon=True).start()

    def _apply_passed(self) -> None:
        """Áp dụng các câu đã Pass vào đề hiện tại."""
        if not self._results:
            messagebox.showinfo("Chưa có kết quả","Chạy QC Pipeline trước."); return
        exam = self._get_exam()
        if not exam:
            messagebox.showwarning("Chưa có đề","Vui lòng tạo đề trước."); return

        passed = [(q, s) for q, s in self._results if s.passed]
        all_q  = [q for q, _ in self._results]

        if not messagebox.askyesno(
            "Áp dụng kết quả QC",
            f"Áp dụng {len(all_q)} câu đã qua QC vào đề hiện tại?\n"
            f"({len(passed)} Pass, {len(all_q)-len(passed)} Review)\n"
            f"Thao tác này sẽ cập nhật metadata chất lượng.",
        ): return

        # Cập nhật câu hỏi trong exam với metadata QC
        for i, (q_qc, score) in enumerate(self._results):
            if i < len(exam.questions):
                exam.questions[i]._review = q_qc._review
        messagebox.showinfo("✅ Đã áp dụng",
                            f"Metadata QC đã được gắn vào {len(self._results)} câu hỏi.\n"
                            f"Mở tab ③ để xem đề với thông tin chất lượng.")

    def _export_report(self) -> None:
        """Xuất báo cáo QC ra Excel."""
        if not self._results:
            messagebox.showinfo("Chưa có kết quả","Chạy QC Pipeline trước."); return

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel","*.xlsx"), ("CSV","*.csv")],
            initialfile="QC_Report.xlsx")
        if not path: return

        try:
            self._write_qc_excel(path)
            messagebox.showinfo("✅ Đã xuất", f"Báo cáo QC:\n{path}")
        except ImportError:
            # Fallback CSV
            self._write_qc_csv(path.replace(".xlsx",".csv"))
            messagebox.showinfo("✅ Đã xuất CSV", f"(cần cài openpyxl cho Excel)")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _write_qc_excel(self, path: str) -> None:
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        wb = openpyxl.Workbook()
        ws = wb.active; ws.title = "QC Pipeline Report"

        headers = ["STT","Loại","Mức","Score","Verdict",
                   "Math","Clarity","Double","Critic Issues",
                   "Solver 1","Solver 2","Lý do Reject","Câu hỏi (tóm tắt)"]
        widths  = [6,16,8,8,12,8,8,8,40,20,20,40,50]

        HDR = PatternFill("solid",fgColor="1F497D")
        HFONT = Font(bold=True,color="FFFFFF")
        thin  = Border(
            left=Side(style="thin",color="AAAAAA"),
            right=Side(style="thin",color="AAAAAA"),
            top=Side(style="thin",color="AAAAAA"),
            bottom=Side(style="thin",color="AAAAAA"))

        for col,(h,w) in enumerate(zip(headers,widths),1):
            cell = ws.cell(row=1,column=col,value=h)
            cell.fill=HDR; cell.font=HFONT
            cell.alignment=Alignment(horizontal="center",vertical="center")
            cell.border=thin
            ws.column_dimensions[cell.column_letter].width=w
        ws.row_dimensions[1].height=20

        fills = {
            "pass":   PatternFill("solid",fgColor="F1F8E9"),
            "review": PatternFill("solid",fgColor="FFF3E0"),
            "reject": PatternFill("solid",fgColor="FFEBEE"),
        }
        fonts = {
            "pass":   Font(color="2E7D32"),
            "review": Font(color="E65100"),
            "reject": Font(color="C62828",bold=True),
        }

        for row_i,(q,s) in enumerate(self._results,2):
            verdict_key = "pass" if (s.passed and not s.needs_review) \
                          else ("review" if s.needs_review else "reject")
            verdict_txt = {"pass":"✅ PASS","review":"⚠️ Review","reject":"❌ Reject"}[verdict_key]
            vals = [
                row_i-1,
                TYPE_LABELS.get(q.qtype,q.qtype),
                q.level,
                round(s.final_score,3),
                verdict_txt,
                round(s.math_correctness,2),
                round(s.clarity,2),
                "✓" if s.double_solve_ok>=0.9 else "✗",
                "; ".join(s.critic_issues[:3]),
                s.solver1_answer[:30],
                s.solver2_answer[:30],
                s.reject_reason[:60],
                q.question[:80],
            ]
            for col,val in enumerate(vals,1):
                cell = ws.cell(row=row_i,column=col,value=val)
                cell.fill=fills[verdict_key]
                cell.font=fonts[verdict_key] if col==5 else Font()
                cell.alignment=Alignment(wrap_text=True,vertical="top")
                cell.border=thin
            ws.row_dimensions[row_i].height=30

        # Summary sheet
        ws2 = wb.create_sheet("Tổng quan")
        from core.quality_pipeline import build_qc_summary
        s = build_qc_summary(self._results)
        for k,v in s.items():
            ws2.append([k,v])

        wb.save(path)

    def _write_qc_csv(self, path: str) -> None:
        import csv
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["STT","Loại","Mức","Score","Verdict",
                        "Solver1","Solver2","Critic Issues","Reject Reason"])
            for i,(q,s) in enumerate(self._results,1):
                w.writerow([
                    i, q.qtype, q.level, round(s.final_score,3),
                    "PASS" if s.passed else "REJECT",
                    s.solver1_answer, s.solver2_answer,
                    "; ".join(s.critic_issues),
                    s.reject_reason,
                ])

    # ── Feature gating ──────────────────────────────────────────────────
    def apply_feature_gates(self, features: dict[str, bool]) -> None:
        """Bản mở khóa: luôn kích hoạt nút AI Fix."""
        try:
            self._ai_fix_btn.config(state="normal", text="🤖  AI sửa câu không đạt")
        except Exception:
            pass
