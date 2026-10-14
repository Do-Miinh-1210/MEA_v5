"""
v5/views/tracking.py — Dashboard + Lịch sử đề + AI Usage.

Reuse:
    storage.database — exam_history, NHCH stats
    services.ai_usage_log — đọc ai_usage.jsonl
"""
from __future__ import annotations

import threading
from collections import Counter
from datetime import datetime, timedelta
from typing import Callable

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from v5.ai_usage_summary import (
    filter_usage_entries,
    format_cost_label,
    format_duration_ms,
    format_number,
    normalize_usage_entry,
    read_usage_entries,
    recent_usage_rows,
    summarize_usage,
)
from v5.dashboard_insights import (
    bank_report_lines,
    exam_report_lines,
    export_dashboard_report,
    load_bank_stats,
    load_model_quality_rows,
    quality_bucket_rows,
    summarize_exam,
)


class TrackingView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        *,
        on_navigate: Callable[[str], None] | None = None,
        on_restore_exam: Callable[[dict], None] | None = None,
        get_current_exam: Callable[[], object | None] | None = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self._on_navigate = on_navigate
        self._on_restore_exam = on_restore_exam
        self._get_current_exam = get_current_exam
        self._dashboard_state: dict = {
            "bank": load_bank_stats(),
            "exam": summarize_exam(None),
            "models": [],
        }
        self._build()
        threading.Thread(target=self._load_data, daemon=True).start()

    def _build(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", pady=(4, 16))
        ctk.CTkLabel(head, text="📊  Theo dõi & Thống kê",
                      font=("Segoe UI", 24, "bold")
                      ).pack(side="left")
        ctk.CTkButton(head, text="📊 Chi tiết AI",
                       width=128, height=32,
                       font=("Segoe UI", 12, "bold"),
                       fg_color=("#7C3AED", "#5B21B6"),
                       hover_color=("#6D28D9", "#4C1D95"),
                       command=self.open_ai_usage_dialog
                       ).pack(side="right", padx=4)
        # SECONDARY tier — đồng nhất với NHCH/Convert/Exam Create headers
        ctk.CTkButton(head, text="🔄 Reload",
                       width=110, height=32,
                       font=("Segoe UI", 12, "bold"),
                       command=lambda: threading.Thread(
                           target=self._load_data, daemon=True).start()
                       ).pack(side="right", padx=4)

        # ── 4 stat cards ──────────────────────────────────────────────
        stat_row = ctk.CTkFrame(self, fg_color="transparent")
        stat_row.pack(fill="x", pady=(0, 16))
        for i in range(4):
            stat_row.grid_columnconfigure(i, weight=1, uniform="stats")

        self._stat_lbls: dict[str, ctk.CTkLabel] = {}
        cards = [
            ("📋", "Đề đã tạo",      "exam_count",  "#3B82F6"),
            ("📚", "Câu trong NHCH", "nhch_count",  "#A78BFA"),
            ("🤖", "AI calls (30d)", "ai_calls",    "#10B981"),
            ("💵", "Chi phí 30d ($)", "cost",        "#F59E0B"),
        ]
        for i, (icon, label, key, color) in enumerate(cards):
            self._build_stat_card(stat_row, icon, label, key, color, i)

        # ── Tabview: Dashboard | Chart | Provider | Lịch sử | AI Usage ─
        self._tabs = ctk.CTkTabview(self)
        self._tabs.pack(fill="both", expand=True)
        self._TAB_DASHBOARD = "📊  Tổng quan"
        self._TAB_CHART    = "📈  Biểu đồ"
        self._TAB_PROVIDER = "🥧  Theo Provider"
        self._TAB_HISTORY  = "🕐  Lịch sử đề"
        self._TAB_USAGE    = "📋  AI Usage log"
        for name in (self._TAB_DASHBOARD, self._TAB_CHART, self._TAB_PROVIDER,
                      self._TAB_HISTORY, self._TAB_USAGE):
            self._tabs.add(name)

        self._build_dashboard(self._tabs.tab(self._TAB_DASHBOARD))
        self._build_chart(self._tabs.tab(self._TAB_CHART))
        self._build_provider_chart(self._tabs.tab(self._TAB_PROVIDER))
        self._build_history(self._tabs.tab(self._TAB_HISTORY))
        self._build_usage(self._tabs.tab(self._TAB_USAGE))

    # ── Public API: switch inner tab (gọi từ sidebar action) ────────────
    def focus_dashboard(self):
        try: self._tabs.set(self._TAB_DASHBOARD)
        except Exception: pass

    def focus_history(self):
        try: self._tabs.set(self._TAB_HISTORY)
        except Exception: pass

    def focus_usage(self):
        try: self._tabs.set(self._TAB_USAGE)
        except Exception: pass

    def focus_provider(self):
        try: self._tabs.set(self._TAB_PROVIDER)
        except Exception: pass

    def open_exam_history(self):
        """Mở dialog lịch sử CTk và khôi phục đề vào workspace V5."""
        try:
            from v5.exam_history_dialog import ExamHistoryDialogCTk
            from tkinter import messagebox

            def _on_restore(snap: dict):
                if callable(self._on_restore_exam):
                    self._on_restore_exam(snap)
                    return
                messagebox.showwarning(
                    "Chưa thể khôi phục",
                    "Workspace V5 chưa sẵn sàng nhận phiên bản này.",
                    parent=self.winfo_toplevel(),
                )

            ExamHistoryDialogCTk(self.winfo_toplevel(), on_restore=_on_restore)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi mở Lịch sử phiên bản",
                                   f"{type(e).__name__}: {e}",
                                   parent=self.winfo_toplevel())

    def open_ai_usage_dialog(self):
        """Mở dialog thống kê AI Usage chi tiết kiểu V4 nhưng CTk-native."""
        try:
            from v5.ai_usage_dialog import AIUsageDialog
            AIUsageDialog(self.winfo_toplevel())
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi mở AI Usage",
                                   f"{type(e).__name__}: {e}",
                                   parent=self.winfo_toplevel())

    def _build_dashboard(self, parent):
        """V4 dashboard parity: NHCH, đề hiện tại, quality buckets, model rows."""
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", pady=(8, 4))
        ctk.CTkLabel(
            bar,
            text="Tổng quan kiểu V4: NHCH, đề đang mở, phân bổ QC và mô hình AI.",
            font=("Segoe UI", 10),
            text_color="gray",
            anchor="w",
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            bar, text="📊 Phân tích phản hồi", height=30,
            fg_color=("#7C3AED", "#5B21B6"),
            hover_color=("#6D28D9", "#4C1D95"),
            font=("Segoe UI", 11, "bold"),
            command=self._analyze_feedback,
        ).pack(side="right", padx=4)
        ctk.CTkButton(
            bar, text="📄 Xuất báo cáo", height=30,
            fg_color=("#0EA5E9", "#0369A1"),
            hover_color=("#0284C7", "#075985"),
            font=("Segoe UI", 11, "bold"),
            command=self._export_dashboard_report,
        ).pack(side="right", padx=4)

        body = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        body.pack(fill="both", expand=True, pady=4)
        body.grid_columnconfigure(0, weight=1, uniform="dashboard")
        body.grid_columnconfigure(1, weight=1, uniform="dashboard")
        body.grid_rowconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        self._bank_box = self._make_dashboard_text_panel(
            body, "📚  Ngân hàng câu hỏi", 0, 0)
        self._exam_box = self._make_dashboard_text_panel(
            body, "📝  Đề thi hiện tại", 0, 1)

        heat_panel = ctk.CTkFrame(body, fg_color=("white", "#1E293B"), corner_radius=10)
        heat_panel.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(8, 0))
        ctk.CTkLabel(heat_panel, text="📊  Phân bổ chất lượng câu hỏi",
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        self._quality_frame = ctk.CTkFrame(heat_panel, fg_color="transparent")
        self._quality_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=(8, 0))
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        model_panel = ctk.CTkFrame(right, fg_color=("white", "#1E293B"), corner_radius=10)
        model_panel.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        ctk.CTkLabel(model_panel, text="🤖  So sánh mô hình AI",
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        self._model_tree = self._make_tree(
            model_panel,
            ("model", "count", "avg", "pass"),
            {"model": "Mô hình", "count": "Số câu", "avg": "Điểm TB", "pass": "Đạt ≥0.9"},
            {"model": 180, "count": 70, "avg": 90, "pass": 90},
            height=4,
        )

        suspect_panel = ctk.CTkFrame(right, fg_color=("white", "#1E293B"), corner_radius=10)
        suspect_panel.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        ctk.CTkLabel(suspect_panel, text="⚠  Câu nghi ngờ sai",
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
        self._sus_tree = self._make_tree(
            suspect_panel,
            ("label", "qtype", "issue", "score"),
            {"label": "Câu", "qtype": "Loại", "issue": "Vấn đề", "score": "Điểm"},
            {"label": 64, "qtype": 64, "issue": 260, "score": 70},
            height=4,
        )
        try:
            self._sus_tree.tag_configure("reject", background="#FEE2E2", foreground="#7F1D1D")
            self._sus_tree.tag_configure("review", background="#FEF3C7", foreground="#92400E")
        except Exception:
            pass
        self._render_dashboard(self._dashboard_state)

    def _make_dashboard_text_panel(self, parent, title: str, row: int, col: int):
        panel = ctk.CTkFrame(parent, fg_color=("white", "#1E293B"), corner_radius=10)
        panel.grid(row=row, column=col, sticky="nsew",
                   padx=(0, 5) if col == 0 else (5, 0), pady=(0, 0))
        ctk.CTkLabel(panel, text=title, font=("Segoe UI", 12, "bold")
                     ).pack(anchor="w", padx=10, pady=(8, 2))
        box = ctk.CTkTextbox(panel, wrap="word", height=150)
        box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        box.configure(state="disabled")
        return box

    def _make_tree(self, parent, cols, labels, widths, *, height: int):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        tree = ttk.Treeview(wrap, columns=cols, show="headings", height=height)
        for col in cols:
            tree.heading(col, text=labels[col])
            tree.column(col, width=widths[col],
                        anchor=("w" if col in ("model", "issue") else "center"))
        try:
            from v5.tree_style import style_treeview
            style_treeview(tree, font_size=10)
        except Exception:
            pass
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        return tree

    def _render_dashboard(self, state: dict):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        bank = state.get("bank", {})
        exam = state.get("exam", summarize_exam(None))
        models = state.get("models", [])
        self._set_textbox(self._bank_box, "\n".join(bank_report_lines(bank)))
        self._set_textbox(self._exam_box, "\n".join(exam_report_lines(exam)))
        self._render_quality_buckets(exam)

        from v5.tree_style import zebra_tag
        self._model_tree.delete(*self._model_tree.get_children())
        for index, row in enumerate(models):
            avg = row.get("avg_score")
            avg_text = f"{avg:.3f}" if isinstance(avg, float) else "Chưa có"
            pass_count = row.get("pass_count")
            pass_text = "—" if pass_count is None else f"{pass_count}/{row.get('count', 0)}"
            self._model_tree.insert("", "end", values=(
                row.get("model", "Không rõ"), row.get("count", 0),
                avg_text, pass_text,
            ), tags=(zebra_tag(index),))

        self._sus_tree.delete(*self._sus_tree.get_children())
        for index, item in enumerate(exam.get("suspects", [])[:20]):
            score = item.get("score")
            score_text = f"{score:.2f}" if isinstance(score, float) else "—"
            tag = item.get("severity") or zebra_tag(index)
            self._sus_tree.insert("", "end", values=(
                item.get("label", ""), item.get("qtype", ""),
                item.get("issue", ""), score_text,
            ), tags=(tag,))

    def _render_quality_buckets(self, exam_summary: dict):
        for child in self._quality_frame.winfo_children():
            child.destroy()
        if not exam_summary.get("has_exam"):
            ctk.CTkLabel(self._quality_frame, text="Chưa có đề thi hiện tại.",
                         text_color="gray").pack(anchor="w", pady=10)
            return
        for row in quality_bucket_rows(exam_summary):
            line = ctk.CTkFrame(self._quality_frame, fg_color="transparent")
            line.pack(fill="x", pady=3)
            ctk.CTkLabel(line, text=row["bucket"], width=84, anchor="w",
                         font=("Segoe UI", 10)).pack(side="left")
            bar = ctk.CTkProgressBar(line, height=14, progress_color=row["color"])
            bar.pack(side="left", fill="x", expand=True, padx=8)
            try:
                bar.set(row["percent"] / 100)
            except Exception:
                pass
            ctk.CTkLabel(line, text=f"{row['count']} ({row['percent']}%)",
                         width=84, anchor="e", font=("Segoe UI", 10)
                         ).pack(side="left")

    @staticmethod
    def _set_textbox(box, text: str):
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("end", text)
        box.configure(state="disabled")

    def _analyze_feedback(self):
        try:
            from services.adaptive_prompt import extract_patterns_from_feedback
            result = extract_patterns_from_feedback()
            bad = result.get("bad", []) or []
            good = result.get("good", []) or []
            msg = "Đã phân tích phản hồi:\n\n"
            msg += f"Lỗi thường gặp ({len(bad)}):\n"
            msg += "\n".join(f"  - {item}" for item in bad[:5]) or "  Chưa có"
            msg += f"\n\nMẫu tốt ({len(good)}):\n"
            msg += "\n".join(f"  - {item}" for item in good[:5]) or "  Chưa có"
            msg += "\n\nCác mẫu này sẽ được tự động đưa vào prompt lần tạo đề tiếp theo."
            messagebox.showinfo("Phân tích phản hồi", msg, parent=self.winfo_toplevel())
            threading.Thread(target=self._load_data, daemon=True).start()
        except Exception as exc:
            messagebox.showerror("Lỗi phân tích phản hồi", str(exc),
                                 parent=self.winfo_toplevel())

    def _export_dashboard_report(self):
        path = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            title="Xuất báo cáo Dashboard",
            defaultextension=".txt",
            initialfile="bao_cao_dashboard_v5.txt",
            filetypes=[("Văn bản", "*.txt")],
        )
        if not path:
            return
        try:
            export_dashboard_report(
                path,
                bank_stats=self._dashboard_state.get("bank", {}),
                exam_summary=self._dashboard_state.get("exam", summarize_exam(None)),
                model_rows=self._dashboard_state.get("models", []),
            )
            messagebox.showinfo("Đã xuất", f"Lưu tại:\n{path}",
                                parent=self.winfo_toplevel())
        except Exception as exc:
            messagebox.showerror("Lỗi xuất báo cáo", str(exc),
                                 parent=self.winfo_toplevel())

    def _build_chart(self, parent):
        """Matplotlib chart: AI calls/day (7d + 30d toggle)."""
        # Toggle 7d / 30d
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(8, 4))
        ctk.CTkLabel(row, text="Khoảng thời gian:",
                      font=("Segoe UI", 11)).pack(side="left", padx=(0, 8))
        self._chart_range = ctk.StringVar(value="7")
        ctk.CTkSegmentedButton(
            row, values=["7", "30"], variable=self._chart_range,
            command=lambda _: self._render_chart()
            ).pack(side="left")
        ctk.CTkLabel(row, text="ngày").pack(side="left", padx=4)

        # Canvas container
        self._chart_frame = ctk.CTkFrame(parent, fg_color=("white", "#0F172A"),
                                            corner_radius=8)
        self._chart_frame.pack(fill="both", expand=True, pady=4)
        self._chart_canvas = None
        self._chart_fig = None
        self._render_chart()

    def _render_chart(self):
        """Vẽ chart AI calls/day vào _chart_frame."""
        import matplotlib
        matplotlib.use("TkAgg")
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        # Clear cũ
        for c in self._chart_frame.winfo_children():
            c.destroy()
        if self._chart_canvas:
            self._chart_canvas = None

        days = int(self._chart_range.get())
        counts: Counter[str] = Counter()
        token_sums: Counter[str] = Counter()
        for item in filter_usage_entries(read_usage_entries(), str(days)):
            row = normalize_usage_entry(item)
            if row["dt"] is None:
                continue
            key = row["dt"].strftime("%m/%d")
            counts[key] += 1
            token_sums[key] += row["total_tokens"]

        # Build x labels (last N days)
        labels = [(datetime.now() - timedelta(days=i)).strftime("%m/%d")
                   for i in range(days - 1, -1, -1)]
        calls = [counts.get(l, 0) for l in labels]
        tokens = [token_sums.get(l, 0) for l in labels]

        # Tạo figure (dark/light theo theme)
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        bg = "#0F172A" if is_dark else "white"
        fg = "#E2E8F0" if is_dark else "#1F2937"
        grid = "#334155" if is_dark else "#E5E7EB"

        fig = Figure(figsize=(9, 4), dpi=90, facecolor=bg)
        ax = fig.add_subplot(111)
        ax.set_facecolor(bg)

        # Bar: calls
        bars = ax.bar(labels, calls, color="#3B82F6", alpha=0.8,
                       label="AI calls")
        # Line on twin: tokens
        ax2 = ax.twinx()
        ax2.plot(labels, tokens, color="#F59E0B", marker="o", linewidth=2,
                  label="Tokens", markersize=4)

        # Style
        ax.set_xlabel("Ngày", color=fg)
        ax.set_ylabel("AI calls", color="#3B82F6")
        ax2.set_ylabel("Tokens", color="#F59E0B")
        ax.tick_params(colors=fg, labelsize=8)
        ax2.tick_params(colors="#F59E0B", labelsize=8)
        ax.set_title(f"AI Usage — {days} ngày gần nhất", color=fg,
                      fontsize=11, pad=10)
        ax.grid(True, axis="y", linestyle="--", alpha=0.3, color=grid)
        for spine in ax.spines.values():
            spine.set_color(grid)
        for spine in ax2.spines.values():
            spine.set_color(grid)

        # Rotate x labels if many days
        if days > 14:
            for tick in ax.get_xticklabels():
                tick.set_rotation(45); tick.set_ha("right")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self._chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._chart_canvas = canvas
        self._chart_fig = fig

    def _build_provider_chart(self, parent):
        """Pie + bar chart: AI calls + cost theo provider."""
        # Toggle 7d / 30d / all
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(8, 4))
        ctk.CTkLabel(row, text="Khoảng thời gian:",
                      font=("Segoe UI", 11)).pack(side="left", padx=(0, 8))
        self._prov_range = ctk.StringVar(value="30")
        ctk.CTkSegmentedButton(
            row, values=["7", "30", "all"], variable=self._prov_range,
            command=lambda _: self._render_provider_chart()
            ).pack(side="left")
        ctk.CTkLabel(row, text="(ngày, 'all' = toàn bộ)"
                      ).pack(side="left", padx=4)

        self._prov_frame = ctk.CTkFrame(parent, fg_color=("white", "#0F172A"),
                                           corner_radius=8)
        self._prov_frame.pack(fill="both", expand=True, pady=4)
        self._prov_canvas = None
        self._render_provider_chart()

    def _render_provider_chart(self):
        """Vẽ 2 chart: pie chart calls + bar chart cost theo provider."""
        import matplotlib
        matplotlib.use("TkAgg")
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        for c in self._prov_frame.winfo_children():
            c.destroy()

        rng = self._prov_range.get()
        shown = filter_usage_entries(read_usage_entries(), rng)
        summary = summarize_usage(shown)
        calls_by_prov = Counter(summary["by_provider"])
        cost_by_prov = summary["cost_by_provider"]
        cost_is_estimated = bool(summary["tokens_estimated"])

        if not calls_by_prov:
            ctk.CTkLabel(self._prov_frame,
                          text="(Chưa có dữ liệu AI usage)",
                          font=("Segoe UI", 13),
                          text_color="gray").pack(pady=80)
            return

        # Sort by calls desc
        provs = sorted(calls_by_prov.keys(),
                        key=lambda p: -calls_by_prov[p])
        calls = [calls_by_prov[p] for p in provs]
        costs = [float(cost_by_prov.get(p, 0.0) or 0.0) for p in provs]

        # Color map
        _PROV_COLOR = {
            "gemini":     "#4285F4",
            "google":     "#4285F4",
            "claude":     "#C97342",
            "anthropic":  "#C97342",
            "openai":     "#10A37F",
            "gpt":        "#10A37F",
            "deepseek":   "#7C3AED",
        }
        colors = []
        for p in provs:
            pl = p.lower()
            c = "#6B7280"  # default
            for k, v in _PROV_COLOR.items():
                if k in pl: c = v; break
            colors.append(c)

        is_dark = ctk.get_appearance_mode().lower() == "dark"
        bg = "#0F172A" if is_dark else "white"
        fg = "#E2E8F0" if is_dark else "#1F2937"

        fig = Figure(figsize=(8.2, 3.8), dpi=90, facecolor=bg)
        # Pie: calls
        ax1 = fig.add_subplot(121)
        ax1.set_facecolor(bg)
        wedges, texts, autotexts = ax1.pie(
            calls, labels=provs, colors=colors,
            autopct=lambda pct: f"{pct:.1f}%\n({int(pct/100*sum(calls))})",
            startangle=90, textprops={"color": fg, "fontsize": 9})
        ax1.set_title(f"AI calls theo provider ({rng}{'d' if rng!='all' else ''})",
                       color=fg, fontsize=11, pad=8)

        # Bar: cost
        ax2 = fig.add_subplot(122)
        ax2.set_facecolor(bg)
        bars = ax2.bar(provs, costs, color=colors, alpha=0.85)
        ax2.set_ylabel("Chi phí (USD)", color=fg)
        ax2.set_title(f"Cost theo provider ({rng}{'d' if rng!='all' else ''})",
                       color=fg, fontsize=11, pad=8)
        ax2.tick_params(colors=fg, labelsize=8)
        for spine in ax2.spines.values(): spine.set_color(fg)
        ax2.grid(True, axis="y", linestyle="--", alpha=0.3)
        # Bar value labels
        for b, c in zip(bars, costs):
            ax2.text(b.get_x() + b.get_width() / 2, b.get_height(),
                      f" {format_cost_label(c, estimated=cost_is_estimated)}",
                      ha="center", va="bottom",
                      color=fg, fontsize=8)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self._prov_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        self._prov_canvas = canvas

    def _build_stat_card(self, parent, icon, label, key, color, col):
        card = ctk.CTkFrame(parent, fg_color=("white", "#293548"),
                              corner_radius=10, border_width=1,
                              border_color=("#E5E7EB", "#334155"))
        card.grid(row=0, column=col, sticky="nsew", padx=6, pady=4)
        hdr = ctk.CTkFrame(card, fg_color=color, height=6, corner_radius=10)
        hdr.pack(fill="x", side="top")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)
        ctk.CTkLabel(inner, text=f"{icon} {label}",
                      text_color="gray", font=("Segoe UI", 10),
                      anchor="w").pack(anchor="w")
        val_lbl = ctk.CTkLabel(inner, text="...",
                                  font=("Segoe UI", 24, "bold"),
                                  anchor="w")
        val_lbl.pack(anchor="w", pady=(4, 0))
        self._stat_lbls[key] = val_lbl

    def _build_history(self, parent):
        # Toolbar mở lịch sử phiên bản đề CTk.
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", pady=(8, 4))
        ctk.CTkLabel(bar,
                      text="Phiên gần đây (list_recent_sessions). "
                           "Nhấn nút bên phải để duyệt lịch sử PHIÊN BẢN của từng đề.",
                      font=("Segoe UI", 10),
                      text_color="gray", anchor="w").pack(side="left", padx=4)
        ctk.CTkButton(bar, text="🕒  Lịch sử phiên bản đề…", height=30,
                       fg_color=("#7C3AED", "#5B21B6"),
                       hover_color=("#6D28D9", "#4C1D95"),
                       font=("Segoe UI", 11, "bold"),
                       command=self.open_exam_history
                       ).pack(side="right", padx=4)

        wrap = ctk.CTkFrame(parent, fg_color=("white", "#1E293B"))
        wrap.pack(fill="both", expand=True, pady=8)
        cols = ("date", "title", "subject", "grade", "n_questions", "duration")
        self._hist_tree = ttk.Treeview(wrap, columns=cols, show="headings",
                                          height=12)
        labels = {"date": "Ngày", "title": "Tiêu đề", "subject": "Môn",
                  "grade": "Lớp", "n_questions": "Số câu",
                  "duration": "Thời lượng"}
        widths = {"date": 140, "title": 280, "subject": 80,
                  "grade": 60, "n_questions": 80, "duration": 100}
        for c in cols:
            self._hist_tree.heading(c, text=labels[c])
            self._hist_tree.column(c, width=widths[c],
                                       anchor=("center" if c in ("grade",
                                                                 "n_questions",
                                                                 "duration")
                                                else "w"))
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._hist_tree)
        except Exception: pass
        # Alpha 21: thêm HSB + grid layout
        vsb = ttk.Scrollbar(wrap, orient="vertical",
                              command=self._hist_tree.yview)
        hsb = ttk.Scrollbar(wrap, orient="horizontal",
                              command=self._hist_tree.xview)
        self._hist_tree.configure(yscrollcommand=vsb.set,
                                     xscrollcommand=hsb.set)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        self._hist_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    def _build_usage(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", pady=(8, 4))
        ctk.CTkLabel(
            bar,
            text="Log AI gần nhất. Dấu * nghĩa là token/cost được ước tính từ ký tự.",
            font=("Segoe UI", 10),
            text_color="gray",
            anchor="w",
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            bar,
            text="📊  Thống kê chi tiết…",
            height=30,
            fg_color=("#7C3AED", "#5B21B6"),
            hover_color=("#6D28D9", "#4C1D95"),
            font=("Segoe UI", 11, "bold"),
            command=self.open_ai_usage_dialog,
        ).pack(side="right", padx=4)

        wrap = ctk.CTkFrame(parent, fg_color=("white", "#1E293B"))
        wrap.pack(fill="both", expand=True, pady=8)
        cols = ("ts", "provider", "model", "task", "tokens_in",
                "tokens_out", "cost", "elapsed")
        self._usage_tree = ttk.Treeview(wrap, columns=cols, show="headings",
                                           height=12)
        labels = {"ts": "Thời gian", "provider": "Provider", "model": "Model",
                  "task": "Task", "tokens_in": "Token in",
                  "tokens_out": "Token out", "cost": "Cost",
                  "elapsed": "Time"}
        widths = {"ts": 140, "provider": 100, "model": 170, "task": 110,
                  "tokens_in": 76, "tokens_out": 76, "cost": 78, "elapsed": 78}
        for c in cols:
            self._usage_tree.heading(c, text=labels[c])
            self._usage_tree.column(c, width=widths[c],
                                        anchor=("center" if c not in ("ts", "model")
                                                 else "w"))
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._usage_tree)
        except Exception: pass
        # Alpha 21: HSB + grid layout
        vsb = ttk.Scrollbar(wrap, orient="vertical",
                              command=self._usage_tree.yview)
        hsb = ttk.Scrollbar(wrap, orient="horizontal",
                              command=self._usage_tree.xview)
        self._usage_tree.configure(yscrollcommand=vsb.set,
                                      xscrollcommand=hsb.set)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        self._usage_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

    # ── Data loaders ──────────────────────────────────────────────────────
    def _load_data(self):
        stats = {"exam_count": "—", "nhch_count": "—",
                 "ai_calls": "—", "cost": "—"}
        dashboard_state = {
            "bank": load_bank_stats(),
            "exam": summarize_exam(self._get_current_exam() if callable(self._get_current_exam) else None),
            "models": load_model_quality_rows(),
        }

        # NHCH count (search_questions không filter = tất cả)
        try:
            from storage.database import search_questions
            stats["nhch_count"] = f"{len(search_questions() or []):,}"
        except Exception: pass

        # Exam history — dùng list_recent_sessions (list_exam_history không có)
        history = []
        try:
            from storage.database import list_recent_sessions
            history = list_recent_sessions(n=50) or []
            stats["exam_count"] = f"{len(history):,}"
        except Exception: pass

        # AI usage log
        usage_rows = read_usage_entries()
        try:
            usage_30d = filter_usage_entries(usage_rows, "30")
            usage_summary = summarize_usage(usage_30d)
            stats["ai_calls"] = f"{usage_summary['total']:,}"
            stats["cost"] = format_cost_label(
                usage_summary["cost_usd"],
                estimated=usage_summary["tokens_estimated"],
            )
        except Exception:
            pass

        from v5.safe_ui import safe_after
        safe_after(self, 0, lambda: self._render(stats, history, usage_rows, dashboard_state))

    def _render(self, stats: dict, history: list, usage: list, dashboard_state: dict | None = None):
        # Guard: view có thể đã destroy khi user chuyển tab giữa lúc load
        try:
            if not self.winfo_exists(): return
        except Exception: return
        if dashboard_state is not None:
            self._dashboard_state = dashboard_state
            self._render_dashboard(dashboard_state)
        for k, lbl in self._stat_lbls.items():
            lbl.configure(text=stats.get(k, "—"))

        # History table
        from v5.tree_style import zebra_tag
        self._hist_tree.delete(*self._hist_tree.get_children())
        for i, h in enumerate(history[:50]):
            self._hist_tree.insert("", "end", values=(
                (h.get("saved_at") or h.get("created_at", ""))[:16],
                (h.get("title") or h.get("name", ""))[:50],
                h.get("subject", ""), h.get("grade", ""),
                h.get("n_questions", 0),
                f"{h.get('duration_min', 0)}p"), tags=(zebra_tag(i),))

        # Usage table (last 50) — supports V4 char logs and V5 token logs.
        self._usage_tree.delete(*self._usage_tree.get_children())
        for i, row in enumerate(recent_usage_rows(usage, limit=50)):
            token_note = "*" if row["tokens_estimated"] else ""
            self._usage_tree.insert("", "end", values=(
                row["ts"][:19],
                row["provider"], row["model"][:24],
                row["task"],
                f"{format_number(row['tokens_in'])}{token_note}",
                f"{format_number(row['tokens_out'])}{token_note}",
                format_cost_label(row["cost_usd"],
                                  estimated=row["tokens_estimated"]),
                format_duration_ms(row["duration_ms"]),
            ), tags=(zebra_tag(i),))
