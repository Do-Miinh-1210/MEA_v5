"""
ui/tab_dashboard.py — Tab ⑥ Bảng điều khiển & Thống kê.
Toàn bộ giao diện sử dụng tiếng Việt có dấu.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Callable, Optional


class TabDashboard(ttk.Frame):
    """Tab ⑥ — Bảng điều khiển & Thống kê chất lượng."""

    def __init__(self, parent,
                 get_exam_data: Callable,
                 get_ai_call: Callable,
                 get_subject_grade: Callable):
        super().__init__(parent)
        self._get_exam       = get_exam_data
        self._get_ai         = get_ai_call
        self._get_subj_grade = get_subject_grade
        self._build()
        self.refresh()

    def _build(self):
        # ── Thanh hành động ────────────────────────────────────────────────
        act = tk.Frame(self, bg="#E2E8F0")
        act.pack(fill="x")
        btns = [
            ("🔄 Làm mới",           self.refresh),
            ("📊 Phân tích phản hồi", self._analyze_feedback),
            ("📄 Xuất báo cáo",       self._export_report),
        ]
        for label, cmd in btns:
            ttk.Button(act, text=label, command=cmd).pack(
                side="left", padx=8 if label == btns[0][0] else 4, pady=6, ipadx=8)

        # ── Nội dung chính: 2 cột ──────────────────────────────────────────
        main = tk.Frame(self)
        main.pack(fill="both", expand=True, padx=8, pady=8)
        left  = tk.Frame(main); left.pack(side="left",  fill="both", expand=True, padx=(0, 4))
        right = tk.Frame(main); right.pack(side="right", fill="both", expand=True, padx=(4, 0))

        # ── Trái: Thống kê ngân hàng câu hỏi ─────────────────────────────
        bank_f = ttk.LabelFrame(left, text="📚  Ngân hàng câu hỏi")
        bank_f.pack(fill="both", expand=True, pady=(0, 8))
        self._bank_text = scrolledtext.ScrolledText(
            bank_f, font=("Segoe UI", 10), height=14,
            state="disabled", wrap="word")
        self._bank_text.pack(fill="both", expand=True, padx=6, pady=6)

        # ── Trái: Đề thi hiện tại ─────────────────────────────────────────
        exam_f = ttk.LabelFrame(left, text="📝  Đề thi hiện tại")
        exam_f.pack(fill="both", expand=True)
        self._exam_text = scrolledtext.ScrolledText(
            exam_f, font=("Segoe UI", 10), height=10,
            state="disabled", wrap="word")
        self._exam_text.pack(fill="both", expand=True, padx=6, pady=6)

        # ── Phải: Biểu đồ phân bổ chất lượng ────────────────────────────
        heat_f = ttk.LabelFrame(right, text="📊  Phân bổ chất lượng câu hỏi")
        heat_f.pack(fill="both", expand=True, pady=(0, 8))
        self._heat_frame = tk.Frame(heat_f)
        self._heat_frame.pack(fill="both", expand=True, padx=6, pady=6)

        # ── Phải: So sánh mô hình AI ──────────────────────────────────────
        model_f = ttk.LabelFrame(right, text="🤖  So sánh mô hình AI")
        model_f.pack(fill="both", expand=True, pady=(0, 8))
        cols_m = ("Mô hình", "Số câu", "Điểm TB", "Đạt ngưỡng")
        self._model_tree = ttk.Treeview(
            model_f, columns=cols_m, show="headings", height=5)
        for c, w in zip(cols_m, [180, 60, 90, 90]):
            self._model_tree.heading(c, text=c)
            self._model_tree.column(c, width=w, anchor="center")
        self._model_tree.pack(fill="both", padx=6, pady=6)

        # ── Phải: Câu nghi ngờ sai ────────────────────────────────────────
        sus_f = ttk.LabelFrame(right, text="⚠️  Câu nghi ngờ sai (cần xem lại)")
        sus_f.pack(fill="both", expand=True)
        cols_s = ("Câu", "Loại", "Vấn đề", "Điểm")
        self._sus_tree = ttk.Treeview(
            sus_f, columns=cols_s, show="headings", height=6)
        for c, w in zip(cols_s, [45, 70, 220, 70]):
            self._sus_tree.heading(c, text=c)
            self._sus_tree.column(c, width=w, anchor="w")
        self._sus_tree.tag_configure("reject", background="#FFEBEE")
        self._sus_tree.tag_configure("review", background="#FFF8E1")
        self._sus_tree.pack(fill="both", padx=6, pady=6)

    # ── Làm mới toàn bộ ───────────────────────────────────────────────────────
    def refresh(self):
        self._refresh_bank_stats()
        self._refresh_exam_stats()
        self._refresh_heatmap()
        self._refresh_model_comparison()
        self._refresh_suspect_questions()

    def _refresh_bank_stats(self):
        try:
            from storage.smart_db import smart_stats
            s = smart_stats()
        except Exception:
            try:
                from storage.database import db_stats
                s = db_stats()
                s.setdefault("valid", s.get("total", 0))
                s.setdefault("avg_quality_score", None)
                s.setdefault("top_quality_count", 0)
                s.setdefault("total_feedback", 0)
                s.setdefault("by_model", {})
            except Exception:
                s = {}

        dong = [
            f"Tổng số câu:            {s.get('total', 0)}",
            f"Hợp lệ:                 {s.get('valid', 0)}",
            f"Không hợp lệ:           {s.get('invalid', 0)}",
            "",
            f"Điểm chất lượng TB:     {s.get('avg_quality_score') or 'Chưa có'}",
            f"Câu đạt ≥ 0.9:          {s.get('top_quality_count', 0)}",
            "",
            "Theo loại câu:",
        ]
        for k, v in s.get("by_type", {}).items():
            dong.append(f"  {k}: {v} câu")
        dong.append("")
        dong.append("Theo mức độ:")
        for k, v in s.get("by_level", {}).items():
            dong.append(f"  {k}: {v} câu")
        dong.append("")
        dong.append(f"Tổng phản hồi:          {s.get('total_feedback', 0)}")
        self._set_text(self._bank_text, "\n".join(dong))

    def _refresh_exam_stats(self):
        exam = None
        try:
            exam = self._get_exam()
        except Exception:
            pass
        if not exam:
            self._set_text(self._exam_text, "Chưa có đề thi hiện tại.")
            return
        qs   = exam.questions
        n    = len(qs)
        errs = sum(1 for q in qs if q._error)
        by_type, scores = {}, []
        for q in qs:
            by_type[q.qtype] = by_type.get(q.qtype, 0) + 1
            if q._review and "quality_score" in q._review:
                sc = q._review["quality_score"]
                if isinstance(sc, dict): sc = sc.get("final_score")
                if sc is not None: scores.append(float(sc))

        dong = [f"Tổng số câu: {n}", f"Câu bị lỗi:  {errs}", "", "Theo loại:"]
        for k, v in by_type.items():
            dong.append(f"  {k}: {v} câu")
        if scores:
            dong += [
                "",
                f"Điểm QC trung bình:  {sum(scores)/len(scores):.3f}",
                f"Đạt ngưỡng (≥ 0.8):  {sum(1 for s in scores if s>=0.8)}/{len(scores)}",
                f"Pass (≥ 0.9):         {sum(1 for s in scores if s>=0.9)}/{len(scores)}",
            ]
        self._set_text(self._exam_text, "\n".join(dong))

    def _refresh_heatmap(self):
        for w in self._heat_frame.winfo_children():
            w.destroy()
        exam = None
        try:
            exam = self._get_exam()
        except Exception:
            pass
        if not exam:
            tk.Label(self._heat_frame, text="Chưa có đề thi.").pack()
            return

        qs = exam.questions
        buckets = {"≥ 0.9": 0, "0.8–0.9": 0, "0.7–0.8": 0, "< 0.7": 0, "Chưa QC": 0}
        colors  = {"≥ 0.9": "#2E7D32", "0.8–0.9": "#558B2F",
                   "0.7–0.8": "#E65100", "< 0.7": "#C62828", "Chưa QC": "#78909C"}
        for q in qs:
            sc = None
            if q._review and "quality_score" in q._review:
                v = q._review["quality_score"]
                if isinstance(v, dict): v = v.get("final_score")
                if v is not None: sc = float(v)
            if sc is None:              buckets["Chưa QC"] += 1
            elif sc >= 0.9:             buckets["≥ 0.9"]   += 1
            elif sc >= 0.8:             buckets["0.8–0.9"] += 1
            elif sc >= 0.7:             buckets["0.7–0.8"] += 1
            else:                       buckets["< 0.7"]   += 1

        total = len(qs) or 1
        tk.Label(self._heat_frame, text="Phân bổ điểm chất lượng:",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        bar_f = tk.Frame(self._heat_frame)
        bar_f.pack(fill="x", pady=4)
        for label, count in buckets.items():
            if count == 0: continue
            pct = count / total
            row = tk.Frame(bar_f); row.pack(fill="x", pady=1)
            tk.Label(row, text=f"{label:10s}", width=10, anchor="w",
                     font=("Segoe UI", 9)).pack(side="left")
            bar_outer = tk.Frame(row, bg="#E0E0E0", height=16)
            bar_outer.pack(side="left", fill="x", expand=True, padx=4)
            bar_outer.update_idletasks()
            tk.Frame(bar_outer, bg=colors[label],
                     width=max(4, int(pct * 200)), height=16).place(x=0, y=0)
            tk.Label(row, text=f"{count} ({pct*100:.0f}%)",
                     font=("Segoe UI", 9), width=12).pack(side="left")

    def _refresh_model_comparison(self):
        self._model_tree.delete(*self._model_tree.get_children())
        try:
            from storage.smart_db import _get_con
            with _get_con() as con:
                rows = con.execute("""
                    SELECT source_model,
                           COUNT(*) as cnt,
                           AVG(quality_score) as avg_qs,
                           SUM(CASE WHEN quality_score>=0.9 THEN 1 ELSE 0 END) as pass_cnt
                    FROM questions_v2
                    WHERE source_model!='' AND is_valid=1
                    GROUP BY source_model
                    ORDER BY avg_qs DESC
                """).fetchall()
        except Exception:
            rows = []
        for row in rows:
            avg      = f"{row['avg_qs']:.3f}" if row["avg_qs"] else "Chưa có"
            pass_pct = f"{row['pass_cnt']}/{row['cnt']}" if row["cnt"] else "—"
            self._model_tree.insert("", "end", values=(
                row["source_model"] or "Không rõ",
                row["cnt"], avg, pass_pct,
            ))

    def _refresh_suspect_questions(self):
        self._sus_tree.delete(*self._sus_tree.get_children())
        exam = None
        try:
            exam = self._get_exam()
        except Exception:
            pass
        if not exam: return
        for i, q in enumerate(exam.questions):
            rev  = q._review or {}
            sc   = None
            if "quality_score" in rev:
                v = rev["quality_score"]
                if isinstance(v, dict): v = v.get("final_score")
                if v is not None: sc = float(v)
            issue, tag = "", ""
            if q._error:
                issue, tag = "Lỗi tạo câu", "reject"
            elif rev.get("cross_model_disagree"):
                issue, tag = "Hai mô hình không đồng ý", "review"
            elif sc is not None and sc < 0.8:
                qc = rev.get("quality_score", {})
                reason = (qc.get("reject_reason", "") if isinstance(qc, dict) else "")
                issue = reason[:50] if reason else f"Điểm thấp ({sc:.2f})"
                tag   = "reject" if sc < 0.7 else "review"
            elif rev.get("needs_review"):
                issue, tag = "Cần xem lại", "review"
            if issue:
                self._sus_tree.insert("", "end", tags=(tag,), values=(
                    f"Câu {i+1}", q.qtype, issue,
                    f"{sc:.2f}" if sc is not None else "—",
                ))

    # ── Hành động ─────────────────────────────────────────────────────────────
    def _analyze_feedback(self):
        try:
            from services.adaptive_prompt import extract_patterns_from_feedback
            result = extract_patterns_from_feedback()
            bad  = result.get("bad",  [])
            good = result.get("good", [])
            msg  = f"Đã phân tích phản hồi:\n\nLỗi thường gặp ({len(bad)}):\n"
            msg += "\n".join(f"  - {p}" for p in bad[:5]) or "  Chưa có"
            msg += f"\n\nMẫu tốt ({len(good)}):\n"
            msg += "\n".join(f"  - {p}" for p in good[:5]) or "  Chưa có"
            msg += "\n\nCác mẫu này sẽ được tự động đưa vào prompt lần tạo đề tiếp theo."
            messagebox.showinfo("Phân tích phản hồi", msg)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _export_report(self):
        from tkinter.filedialog import asksaveasfilename
        path = asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Văn bản", "*.txt")],
            initialfile="bao_cao_dashboard.txt",
        )
        if not path: return
        try:
            from storage.smart_db import smart_stats
            s = smart_stats()
        except Exception:
            s = {}
        dong = [
            "BÁO CÁO BẢNG ĐIỀU KHIỂN — HỆ THỐNG TẠO ĐỀ KIỂM TRA AI",
            "=" * 55,
            f"Tổng câu trong ngân hàng: {s.get('total', 0)}",
            f"Câu hợp lệ:               {s.get('valid', 0)}",
            f"Điểm chất lượng TB:       {s.get('avg_quality_score','Chưa có')}",
            f"Câu đạt ≥ 0.9:            {s.get('top_quality_count', 0)}",
            f"Tổng phản hồi:            {s.get('total_feedback', 0)}",
            "",
            "THEO MÔ HÌNH:",
        ]
        for k, v in s.get("by_model", {}).items():
            dong.append(f"  {k}: {v} câu")
        from pathlib import Path
        Path(path).write_text("\n".join(dong), encoding="utf-8")
        messagebox.showinfo("Đã xuất", f"Lưu tại:\n{path}")

    @staticmethod
    def _set_text(widget, text: str):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.config(state="disabled")
