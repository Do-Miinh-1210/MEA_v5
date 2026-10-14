"""
v5/views/qc.py — QC chất lượng + TikZ vẽ hình (2 tab nội bộ).

Tab 1: ✅ QC — bảng đánh giá câu hỏi
Tab 2: 🎨 TikZ — editor + render

Workflow QC, sửa câu, TikZ preview, auto-heal và kho mẫu chạy trong V5.
"""
from __future__ import annotations

import threading
from typing import Any, Callable

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from v5.ui_perf import UiThrottle


TIKZ_SNIPPETS: dict[str, tuple[str, str]] = {
    "#diem": ("Điểm có nhãn", r"\coordinate[label=above right:$A$] (A) at (60:2);"),
    "#diemtron": ("Điểm tròn + nhãn", r"\draw (A) circle (0.6pt) node[shift={(45:8pt)}, font=\large] {$A$};"),
    "#doan": ("Đoạn thẳng AB", r"\draw[thick] (A) -- (B);"),
    "#netdut": ("Nét khuất", r"\draw[dash pattern=on 2pt off 1.5pt] (A) -- (B);"),
    "#goc": ("Đánh dấu góc", r"\pic[draw, angle radius=7mm, angle eccentricity=1.35, \"$60^\circ$\"] {angle=B--A--C};"),
    "#truc": ("Hệ trục tọa độ", "\\draw[-Stealth, line width=0.7pt] (-4,0) -- (4,0) node[below] {$x$};\n\\draw[-Stealth, line width=0.7pt] (0,-3) -- (0,3) node[shift={(-6pt,-5pt)}] {$y$};"),
    "#ham": ("Đồ thị hàm số", "\\begin{axis}[axis lines=middle, xmin=-4, xmax=4, ymin=-3, ymax=5, samples=160]\n  \\addplot[blue, thick, domain=-3:3] {x^2 - 2*x};\n\\end{axis}"),
    "#duongtron": ("Đường tròn", "\\coordinate[label=below left:$O$] (O) at (0,0);\n\\draw[thick] (O) circle (2);\n\\draw (O) circle (0.6pt);"),
    "#elip": ("Elip", r"\draw[thick] (0,0) ellipse (2.4 and 1.1);"),
    "#foreach": ("Vẽ/gán nhãn hàng loạt", r"\foreach \p/\pos in {A/135, B/-45, C/45}{ \draw (\p) circle (0.6pt) node[shift={(\pos:8pt)}, font=\large] {$\p$}; }"),
    "#giao": ("Giao điểm paths", "\\path[name path=d1] (A) -- (B);\n\\path[name path=d2] (C) -- (D);\n\\path[name intersections={of=d1 and d2, by=I}];\n\\draw (I) circle (0.6pt) node[above right] {$I$};"),
    "#pattern": ("Miền gạch chéo", r"\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray!70] (A)--(B)--(C)--cycle;"),
    "#bbt": ("Bảng biến thiên khung", "\\begin{tikzpicture}[>=stealth, every node/.style={font=\\Large}]\n\\tkzTabInit[nocadre=false, lgt=1.2, espcl=2.5, deltacl=0.6]{$x$/1,$f'(x)$/0.7,$f(x)$/2.5}{$-\\infty$,$0$,$+\\infty$}\n\\tkzTabLine{,+,0,-,}\n\\path ([yshift=8pt]N13) node (A1) {$-\\infty$} ([yshift=-8pt]N22) node (A2) {$1$} ([yshift=8pt]N33) node (A3) {$-\\infty$};\n\\foreach \\i/\\j in {1/2,2/3}{\\draw[-Stealth] (A\\i)--(A\\j);}\n\\end{tikzpicture}"),
    "#bxd": ("Bảng xét dấu", "\\begin{tikzpicture}[>=stealth, every node/.style={font=\\Large}]\n\\tkzTabInit[nocadre=false, lgt=1.2, espcl=2.5, deltacl=0.6]{$x$/1,$f'(x)$/0.7}{$-\\infty$,$0$,$+\\infty$}\n\\tkzTabLine{,+,0,-,}\n\\end{tikzpicture}"),
    "#3d": ("Tọa độ 3D", "\\tdplotsetmaincoords{65}{115}\n\\begin{tikzpicture}[tdplot_main_coords, line join=round, line cap=round]\n  \\coordinate[label=below:$O$] (O) at (0,0,0);\n\\end{tikzpicture}"),
}

QC_AI_PROVIDERS = ["Google Gemini", "Anthropic Claude", "DeepSeek", "9Router"]
QC_AI_MODEL_DEFAULT = {
    "Google Gemini": "gemini-3.8-flash",
    "Anthropic Claude": "claude-sonnet-4-5",
    "DeepSeek": "deepseek-chat",
    "9Router": "ag/gemini-3.8-flash",
}
QC_AI_MODEL_OPTIONS = {
    "Google Gemini": [
        "gemini-3.8-flash",
        "gemini-3.1-pro",
        "gemini-3.8-live",
        "gemini-3.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
    ],
    "Anthropic Claude": ["claude-sonnet-4-5", "claude-opus-4-1", "claude-haiku-4-5"],
    "DeepSeek": ["deepseek-chat", "deepseek-reasoner"],
    "9Router": [
        "ag/gemini-3.8-flash",
        "ag/gemini-3.8-flash-high",
        "ag/gemini-3.7-flash-high",
        "ag/gemini-3.6-flash-high",
        "ag/gemini-3.1-pro-low",
        "ag/claude-sonnet-4-6",
        "ag/gpt-oss-120b-medium",
        "gemini-3.8-flash",
    ],
}


class QCView(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        *,
        on_navigate: Callable[[str], None] | None = None,
        can_use_feature: Callable[..., bool] | None = None,
        initial_exam: Any | None = None,
        get_current_exam: Callable[[], Any | None] | None = None,
        on_exam_changed: Callable[[Any | None], None] | None = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self._on_navigate = on_navigate
        self._can_use_feature = can_use_feature
        self._initial_exam = initial_exam
        self._get_current_exam = get_current_exam
        self._on_exam_changed = on_exam_changed
        self._build()
        if getattr(initial_exam, "questions", None):
            self.after(0, self._load_from_current_exam)

    def _build(self):
        ctk.CTkLabel(self, text="✅  Chất lượng + Vẽ hình",
                      font=("Segoe UI", 24, "bold")
                      ).pack(anchor="w", pady=(4, 16))

        # ── Tabview ──────────────────────────────────────────────────
        # KHÔNG đặt height cố định — để fill="both" + expand=True chiếm
        # toàn bộ chiều cao window (Alpha 18: trước có height=580 chèn TikZ
        # preview xuống 1×1 px khi window cao hơn 580).
        self._tabs = ctk.CTkTabview(self,
                                       segmented_button_selected_color="#10B981",
                                       segmented_button_selected_hover_color="#059669")
        self._tabs.pack(fill="both", expand=True)
        self._TAB_QC   = "✅  QC Chất lượng"
        self._TAB_TIKZ = "🎨  TikZ Vẽ hình"
        self._tabs.add(self._TAB_QC)
        self._tabs.add(self._TAB_TIKZ)

        self._build_qc(self._tabs.tab(self._TAB_QC))
        self._build_tikz(self._tabs.tab(self._TAB_TIKZ))

    # ── Public API: switch inner tab (gọi từ sidebar action) ────────────
    def focus_qc(self):
        try: self._tabs.set(self._TAB_QC)
        except Exception: pass

    def focus_tikz(self):
        try: self._tabs.set(self._TAB_TIKZ)
        except Exception: pass

    def focus_ai_review(self):
        """AI Review & Fix nằm trong tab QC (double-click câu lỗi). Focus tab QC."""
        self.focus_qc()

    def _feature_allowed(self, feature: str, *, notify: bool = True) -> bool:
        if not callable(self._can_use_feature):
            return True
        try:
            return bool(self._can_use_feature(feature, notify=notify))
        except TypeError:
            return bool(self._can_use_feature(feature))

    # ── Tab 1: QC ─────────────────────────────────────────────────────────
    def _build_qc(self, parent):
        self._qc_questions: list = []   # list[Question] đang QC
        self._qc_reviews: list = []     # list[dict] result tương ứng
        self._qc_reviewed_questions: list = []
        self._qc_source_exam = None

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                           scrollbar_button_color=("#CBD5E1",
                                                                    "#475569"))
        scroll.pack(fill="both", expand=True)
        parent = scroll

        ctk.CTkLabel(parent,
                      text="Quy trình QC:  ①  Load câu  →  ②  Chạy QC (AI giải "
                           "2 lần + Critic + Math + Format → điểm 0-10)  →  "
                           "③  Double-click câu lỗi để sửa.",
                      font=("Segoe UI", 11, "bold"),
                      text_color=("#1E40AF", "#93C5FD"),
                      justify="left", wraplength=760
                      ).pack(anchor="w", pady=(8, 4))
        ctk.CTkLabel(parent,
                      text="Câu đạt (✅) là đã được AI giải khớp đáp án + không "
                           "lỗi format. Câu lỗi (❌) hiện gợi ý để bạn sửa.",
                      font=("Segoe UI", 10), text_color="gray",
                      justify="left", wraplength=760
                      ).pack(anchor="w", pady=(0, 12))

        # Card load source
        c = self._card(parent, "①  Chọn nguồn câu hỏi")
        src_row = ctk.CTkFrame(c, fg_color="transparent")
        src_row.pack(fill="x")
        # PRIMARY tier (h=40) — CTA chính đầu pipeline QC
        ctk.CTkButton(src_row, text="📚  Load từ NHCH local",
                       width=200, height=40,
                       font=("Segoe UI", 13, "bold"),
                       fg_color="#3B82F6", hover_color="#2563EB",
                       command=self._load_from_nhch
                       ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(src_row, text="📄  Load đề hiện tại",
                       width=190, height=40,
                       font=("Segoe UI", 13, "bold"),
                       fg_color=("#0EA5E9", "#075985"),
                       hover_color=("#0284C7", "#0C4A6E"),
                       command=self._load_from_current_exam
                       ).pack(side="left", padx=(0, 6))
        self._qc_source_lbl = ctk.CTkLabel(c,
            text="(chưa load câu nào — bấm 'Load từ NHCH' hoặc 'Load đề hiện tại' để bắt đầu)",
            text_color="gray", font=("Segoe UI", 10, "italic"))
        self._qc_source_lbl.pack(anchor="w", pady=(4, 0))

        # Card run QC + stats
        c2 = self._card(parent, "▶  Chạy QC")
        ai_row = ctk.CTkFrame(c2, fg_color=("white", "#1E293B"),
                              corner_radius=8, border_width=1,
                              border_color=("#E5E7EB", "#334155"))
        ai_row.pack(fill="x", pady=(0, 8))
        ai_row.grid_columnconfigure(5, weight=1)
        ctk.CTkLabel(
            ai_row,
            text="AI QC:",
            width=58,
            anchor="w",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=0, padx=(10, 6), pady=8, sticky="w")
        self._qc_provider_var = ctk.StringVar(value=self._detect_qc_ai_provider())
        ctk.CTkOptionMenu(
            ai_row,
            values=QC_AI_PROVIDERS,
            variable=self._qc_provider_var,
            width=170,
            command=self._on_qc_ai_provider_change,
        ).grid(row=0, column=1, padx=(0, 8), pady=8, sticky="w")
        self._qc_model_var = ctk.StringVar(
            value=QC_AI_MODEL_DEFAULT.get(self._qc_provider_var.get(), "gemini-3.8-flash")
        )
        self._qc_model_menu = ctk.CTkOptionMenu(
            ai_row,
            values=self._qc_ai_model_options(self._qc_provider_var.get()),
            variable=self._qc_model_var,
            width=210,
        )
        self._qc_model_menu.grid(row=0, column=2, padx=(0, 10), pady=8, sticky="w")
        ctk.CTkLabel(
            ai_row,
            text="Dùng cho chạy QC và AI sửa câu khi double-click dòng lỗi.",
            text_color="gray",
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=0, column=3, columnspan=3, sticky="ew", padx=(0, 10), pady=8)

        run_row = ctk.CTkFrame(c2, fg_color="transparent")
        run_row.pack(fill="x", pady=(0, 8))
        run_row.grid_columnconfigure(3, weight=1)
        # PRIMARY tier (h=40) — CTA chính của tab QC
        self._qc_run_btn = ctk.CTkButton(
            run_row, text="🤖  Bắt đầu QC", state="disabled",
            width=200, height=40,
            font=("Segoe UI", 13, "bold"),
            fg_color="#10B981", hover_color="#059669",
            command=self._on_run_qc)
        self._qc_run_btn.grid(row=0, column=0, sticky="w", padx=(0, 12))
        self._qc_report_btn = ctk.CTkButton(
            run_row, text="📥  Báo cáo", state="disabled",
            width=120, height=40,
            fg_color=("#0284C7", "#075985"),
            hover_color=("#0369A1", "#0C4A6E"),
            command=self._export_qc_report)
        self._qc_report_btn.grid(row=0, column=1, sticky="w", padx=(0, 12))
        self._qc_apply_btn = ctk.CTkButton(
            run_row, text="✅  Áp dụng", state="disabled",
            width=125, height=40,
            fg_color=("#059669", "#047857"),
            hover_color=("#047857", "#065F46"),
            command=self._apply_qc_results)
        self._qc_apply_btn.grid(row=0, column=2, sticky="w", padx=(0, 12))

        self._qc_prog = ctk.CTkProgressBar(run_row, width=280,
                                              progress_color="#10B981")
        self._qc_prog.set(0)
        self._qc_prog.grid(row=1, column=0, columnspan=3, sticky="ew",
                           pady=(8, 0), padx=(0, 12))
        self._qc_prog_lbl = ctk.CTkLabel(run_row, text="",
                                            text_color="gray",
                                            font=("Segoe UI", 10),
                                            anchor="w")
        self._qc_prog_lbl.grid(row=1, column=3, sticky="ew", pady=(8, 0))

        # 4 stat cards
        stat_row = ctk.CTkFrame(c2, fg_color="transparent")
        stat_row.pack(fill="x", pady=(8, 0))
        self._qc_stat_lbls: dict[str, ctk.CTkLabel] = {}
        for icon, label, key in [
            ("✅", "Đạt",       "ok"),
            ("❌", "Không đạt", "fail"),
            ("⭐", "Điểm TB",   "avg"),
            ("📊", "Tổng",     "total"),
        ]:
            box = ctk.CTkFrame(stat_row, fg_color=("white", "#1E293B"),
                                  corner_radius=8, border_width=1,
                                  border_color=("#E5E7EB", "#334155"))
            box.pack(side="left", padx=4, fill="x", expand=True)
            ctk.CTkLabel(box, text=f"{icon} {label}",
                          text_color="gray", font=("Segoe UI", 10)
                          ).pack(padx=10, pady=(8, 0))
            val_lbl = ctk.CTkLabel(box, text="—",
                                      font=("Segoe UI", 18, "bold"))
            val_lbl.pack(padx=10, pady=(0, 8))
            self._qc_stat_lbls[key] = val_lbl

        # Card result table
        c3 = self._card(parent, "📋  Chi tiết QC")
        tbl_wrap = ctk.CTkFrame(c3, fg_color=("white", "#1E293B"))
        tbl_wrap.pack(fill="both", expand=True, pady=(0, 4))

        cols = ("no", "qtype", "level", "score", "status", "issue")
        self._qc_tree = ttk.Treeview(tbl_wrap, columns=cols,
                                         show="headings", height=10)
        labels = {"no": "#", "qtype": "Loại", "level": "Mức",
                  "score": "Điểm", "status": "Đạt?", "issue": "Vấn đề / Gợi ý"}
        widths = {"no": 40, "qtype": 60, "level": 50, "score": 60,
                  "status": 60, "issue": 500}
        minwidths = {"no": 36, "qtype": 58, "level": 50, "score": 58,
                     "status": 58, "issue": 280}
        for cc in cols:
            self._qc_tree.heading(cc, text=labels[cc])
            anchor = "center" if cc != "issue" else "w"
            self._qc_tree.column(cc, width=widths[cc], minwidth=minwidths[cc],
                                 anchor=anchor, stretch=(cc == "issue"))
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._qc_tree)
        except Exception: pass
        # Dùng grid cho HSB+VSB (Alpha 21: thêm horizontal scrollbar)
        vsb = ttk.Scrollbar(tbl_wrap, orient="vertical",
                              command=self._qc_tree.yview)
        hsb = ttk.Scrollbar(tbl_wrap, orient="horizontal",
                              command=self._qc_tree.xview)
        self._qc_tree.configure(yscrollcommand=vsb.set,
                                  xscrollcommand=hsb.set)
        tbl_wrap.grid_rowconfigure(0, weight=1)
        tbl_wrap.grid_columnconfigure(0, weight=1)
        self._qc_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        # Double-click 1 câu → mở dialog sửa kèm gợi ý QC
        self._qc_tree.bind("<Double-1>", self._on_qc_edit)

    def _reset_qc_results(self) -> None:
        self._qc_reviews = []
        self._qc_reviewed_questions = []
        try:
            self._qc_tree.delete(*self._qc_tree.get_children())
        except Exception:
            pass
        for label in getattr(self, "_qc_stat_lbls", {}).values():
            try:
                label.configure(text="—", text_color=("black", "white"))
            except Exception:
                pass
        try:
            self._qc_prog.set(0)
            self._qc_prog_lbl.configure(text="")
            self._qc_report_btn.configure(state="disabled")
            self._qc_apply_btn.configure(state="disabled")
        except Exception:
            pass

    def _load_exam_questions(self, exam, source_name: str) -> bool:
        questions = list(getattr(exam, "questions", []) or []) if exam is not None else []
        if not questions:
            return False
        self._qc_questions = questions
        self._qc_source_exam = exam
        self._reset_qc_results()
        self._qc_source_lbl.configure(
            text=f"  ✓ Đã load {len(self._qc_questions)} câu từ {source_name}",
            text_color="#10B981",
        )
        self._qc_run_btn.configure(state="normal")
        self.focus_qc()
        return True

    def _load_from_current_exam(self):
        """Load đề đang mở trong workspace V5 để chạy QC trực tiếp."""
        exam = None
        if callable(self._get_current_exam):
            try:
                exam = self._get_current_exam()
            except Exception:
                exam = None
        exam = exam or self._initial_exam
        if self._load_exam_questions(exam, "đề hiện tại"):
            return
        messagebox.showinfo(
            "Chưa có đề hiện tại",
            "Chưa có đề nào đang mở để chạy QC. Hãy tạo/nạp đề trước hoặc load từ NHCH.",
            parent=self,
        )

    def _on_qc_edit(self, event=None):
        """Double-click câu trong QC → mở dialog sửa kèm gợi ý QC."""
        sel = self._qc_tree.selection()
        if not sel: return
        try:
            idx = self._qc_tree.index(sel[0])
            if idx < 0 or idx >= len(self._qc_questions): return
            q = self._qc_questions[idx]
            rev = self._qc_reviews[idx] if idx < len(self._qc_reviews) else {}
        except Exception:
            return
        qc_hint = (rev.get("issue", "") or rev.get("tip", "") or "")

        def _on_save(updated_q):
            try:
                self._qc_questions[idx] = updated_q
                # Lưu lại vào NHCH local
                from storage.database import save_questions
                save_questions([updated_q], subject="Toán", grade="12",
                                source="qc_fix")
                from v5.toast import show_toast
                show_toast(self.winfo_toplevel(),
                            "✓ Đã sửa & lưu câu (chạy QC lại để kiểm tra)",
                            kind="success")
            except Exception as e:
                messagebox.showerror("Lỗi lưu", str(e), parent=self)

        try:
            from v5.edit_question import EditQuestionDialogCTk
            EditQuestionDialogCTk(self.winfo_toplevel(), q,
                                    on_save_cb=_on_save,
                                    get_ai_call=(self._resolve_ai_call_qc_factory()
                                        if self._feature_allowed("ai_review", notify=False)
                                        else None),
                                    subject="Toán", grade="12",
                                    qc_issues=qc_hint)
        except Exception as e:
            messagebox.showerror("Lỗi mở dialog", str(e), parent=self)

    def _resolve_ai_call_qc_factory(self):
        """Factory () -> ai_call cho dialog sửa (get_ai_call pattern)."""
        ai = self._resolve_ai_call_qc()
        return (lambda: ai) if ai else None

    def _detect_qc_ai_provider(self) -> str:
        try:
            from services.key_manager import get_key_manager

            manager = get_key_manager()
            for provider in QC_AI_PROVIDERS:
                if manager.load(provider):
                    return provider
        except Exception:
            pass
        return "Google Gemini"

    def _on_qc_ai_provider_change(self, provider: str) -> None:
        values = self._qc_ai_model_options(provider)
        if hasattr(self, "_qc_model_menu"):
            self._qc_model_menu.configure(values=values)
        self._qc_model_var.set(QC_AI_MODEL_DEFAULT.get(provider, values[0]))

    @staticmethod
    def _qc_ai_model_options(provider: str) -> list[str]:
        return QC_AI_MODEL_OPTIONS.get(provider) or [
            QC_AI_MODEL_DEFAULT.get(provider, "gemini-3.8-flash")
        ]

    def _load_from_nhch(self):
        """Load 1 batch câu từ NHCH local để chạy QC."""
        try:
            from storage.database import search_questions
            all_q = search_questions() or []
            if not all_q:
                messagebox.showinfo("NHCH trống", "Chưa có câu nào trong NHCH.",
                                      parent=self); return
            # Lấy tối đa 20 câu gần nhất để demo
            batch = all_q[-20:]
            from core.models import Question
            self._qc_source_exam = None
            self._qc_questions = []
            for d in batch:
                q = Question(qtype=d.get("qtype", "TN"),
                              level=d.get("level", "TH"),
                              topic=d.get("topic", ""),
                              question=d.get("question", ""),
                              options=d.get("options") or d.get("options_json") or {},
                              answer=d.get("answer", ""),
                              solution=d.get("solution", ""),
                              points=float(d.get("points", 1.0) or 1.0))
                q.question_id = d.get("question_id", "")
                # DS items/answers — QC pipeline cần để review câu Đúng/Sai
                q.items   = d.get("items", {}) or {}
                q.answers = d.get("answers", {}) or {}
                self._qc_questions.append(q)
            self._reset_qc_results()
            self._qc_source_lbl.configure(
                text=f"  ✓ Đã load {len(self._qc_questions)} câu (mới nhất)",
                text_color="#10B981")
            self._qc_run_btn.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Lỗi load NHCH", str(e), parent=self)

    def _on_run_qc(self):
        if not self._qc_questions:
            return
        # Resolve AI
        ai_call = self._resolve_ai_call_qc()
        if not ai_call:
            messagebox.showwarning("Thiếu AI key",
                                     "Cấu hình API key ở tab ⚙️ Cấu hình trước.",
                                     parent=self); return

        self._qc_run_btn.configure(state="disabled", text="⏳ Đang QC...")
        self._qc_prog.set(0)
        self._qc_prog_lbl.configure(text="", text_color="gray")
        self._qc_tree.delete(*self._qc_tree.get_children())
        self._configure_qc_tree_tags()

        def _worker():
            try:
                self._do_qc(ai_call)
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror(
                    "Lỗi QC", err[:300], parent=self))
            finally:
                self.after(0, lambda: self._qc_run_btn.configure(
                    state="normal", text="🤖  Bắt đầu QC"))
        threading.Thread(target=_worker, daemon=True).start()

    def _do_qc(self, ai_call):
        """Chạy quality_pipeline cho từng câu.

        run_qc_pipeline(q, subject, grade, ai_call) trả (Question, QualityScore).
        QualityScore.final_score thang 0.0-1.0 → ×10 để hiển thị /10.
        """
        from core.quality_pipeline import run_qc_pipeline

        self._qc_reviews = []
        self._qc_reviewed_questions = []
        n = len(self._qc_questions)
        progress_throttle = UiThrottle(self, 80)
        row_throttle = UiThrottle(self, 80)
        row_batch = []
        row_lock = threading.Lock()

        def _flush_rows():
            with row_lock:
                batch = list(row_batch)
                row_batch.clear()
            for idx, question, review in batch:
                self._add_qc_row(idx, question, review)

        def _finish_qc_ui():
            progress_throttle.cancel()
            row_throttle.cancel()
            _flush_rows()
            self._update_qc_progress(n, n)
            self._update_qc_stats()

        for i, q in enumerate(self._qc_questions, 1):
            progress_throttle.schedule(self._update_qc_progress, i, n)
            try:
                reviewed_q, qs = run_qc_pipeline(
                    q, subject="Toán", grade="12", ai_call=ai_call)
                # Convert QualityScore → dict mà _add_qc_row mong đợi
                issues = getattr(qs, "critic_issues", None) or []
                issue_text = (getattr(qs, "reject_reason", "") or
                              ("; ".join(str(x) for x in issues) if issues
                               else getattr(qs, "notes", "")))
                rev = {
                    "ok":    bool(getattr(qs, "passed", True)),
                    "score": round(float(getattr(qs, "final_score", 0.5)) * 10, 1),
                    "issue": issue_text or "",
                    "tip":   getattr(qs, "notes", "") or "",
                    "needs_review": bool(getattr(qs, "needs_review", False)),
                }
            except Exception as e:
                reviewed_q = q
                rev = {"ok": False, "score": 0,
                       "issue": f"Pipeline lỗi: {str(e)[:80]}",
                       "tip": ""}
            self._qc_reviews.append(rev)
            self._qc_reviewed_questions.append(reviewed_q)
            with row_lock:
                row_batch.append((i, q, rev))
            row_throttle.schedule(_flush_rows)

        # Update stats
        self.after(0, _finish_qc_ui)

    def _configure_qc_tree_tags(self) -> None:
        self._qc_tree.tag_configure("fail",
                                       background="#FEE2E2",
                                       foreground="#7F1D1D")
        self._qc_tree.tag_configure("ok",
                                       foreground="#065F46")

    def _update_qc_progress(self, done: int, total: int) -> None:
        total = max(total, 1)
        self._qc_prog.set(done / total)
        self._qc_prog_lbl.configure(text=f"  Câu {done}/{total}...")

    def _add_qc_row(self, idx: int, q, rev: dict):
        ok = "✅" if rev.get("ok", True) else "❌"
        score = rev.get("score", 5)
        issue = (rev.get("issue", "") or rev.get("tip", "") or "")[:200]
        tag = "ok" if rev.get("ok", True) else "fail"
        self._qc_tree.insert("", "end", values=(
            idx, q.qtype, q.level, f"{score}/10", ok, issue), tags=(tag,))

    def _update_qc_stats(self):
        total = len(self._qc_reviews)
        ok = sum(1 for r in self._qc_reviews if r.get("ok", True))
        fail = total - ok
        avg = (sum(r.get("score", 5) for r in self._qc_reviews) / max(total, 1))
        self._qc_stat_lbls["total"].configure(text=str(total))
        self._qc_stat_lbls["ok"].configure(text=str(ok),
                                              text_color="#10B981")
        self._qc_stat_lbls["fail"].configure(text=str(fail),
                                                text_color="#EF4444" if fail else "gray")
        self._qc_stat_lbls["avg"].configure(text=f"{avg:.1f}/10")
        self._qc_prog_lbl.configure(text=f"  ✓ Hoàn tất ({total} câu)",
                                       text_color="#10B981")
        self._qc_report_btn.configure(state=("normal" if total else "disabled"))
        self._qc_apply_btn.configure(state=("normal" if total else "disabled"))

    def _resolve_apply_target_exam(self):
        exam = self._qc_source_exam
        if exam is None and callable(self._get_current_exam):
            try:
                exam = self._get_current_exam()
            except Exception:
                exam = None
        return exam

    def _apply_qc_reviews_to_exam(self, exam) -> int:
        if exam is None or not getattr(exam, "questions", None):
            return 0
        applied = 0
        by_id = {
            str(getattr(question, "question_id", "") or ""): question
            for question in getattr(exam, "questions", [])
            if getattr(question, "question_id", "")
        }
        for index, reviewed_q in enumerate(self._qc_reviewed_questions):
            review_meta = getattr(reviewed_q, "_review", None)
            if not review_meta:
                continue
            qid = str(getattr(reviewed_q, "question_id", "") or "")
            target = by_id.get(qid) if qid else None
            if target is None and index < len(exam.questions):
                target = exam.questions[index]
            if target is None:
                continue
            target._review = review_meta
            applied += 1
        return applied

    def _apply_qc_results(self) -> None:
        """Áp dụng metadata QC vào đề hiện tại, tương đương action V4."""
        if not self._qc_reviews:
            messagebox.showinfo("Chưa có kết quả", "Chạy QC trước khi áp dụng kết quả.", parent=self)
            return
        exam = self._resolve_apply_target_exam()
        if exam is None or not getattr(exam, "questions", None):
            messagebox.showwarning("Chưa có đề", "Chưa có đề hiện tại để gắn metadata QC.", parent=self)
            return
        applied = self._apply_qc_reviews_to_exam(exam)
        if callable(self._on_exam_changed):
            self._on_exam_changed(exam)
        self._qc_prog_lbl.configure(
            text=f"  ✓ Đã áp dụng metadata QC cho {applied}/{len(self._qc_reviews)} câu",
            text_color="#10B981" if applied else "#D97706",
        )
        try:
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(), f"✓ Đã áp dụng QC cho {applied} câu", kind="success")
        except Exception:
            pass
        messagebox.showinfo(
            "Đã áp dụng",
            f"Metadata QC đã được gắn vào {applied}/{len(self._qc_reviews)} câu trong đề hiện tại.",
            parent=self,
        )

    def _export_qc_report(self) -> None:
        """Xuất báo cáo QC giống action Báo cáo của V4, nhưng dùng dữ liệu V5."""
        if not self._qc_reviews:
            messagebox.showinfo("Chưa có kết quả", "Chạy QC trước khi xuất báo cáo.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Xuất báo cáo QC",
            defaultextension=".xlsx",
            initialfile="QC_Report_V5.xlsx",
            filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")],
        )
        if not path:
            return
        try:
            if path.lower().endswith(".csv"):
                self._write_qc_report_csv(path)
            else:
                try:
                    self._write_qc_report_xlsx(path)
                except ImportError:
                    csv_path = str(path).rsplit(".", 1)[0] + ".csv"
                    self._write_qc_report_csv(csv_path)
                    path = csv_path
            self._qc_prog_lbl.configure(text=f"  ✓ Đã xuất báo cáo QC: {path}", text_color="#10B981")
            try:
                from v5.toast import show_toast
                show_toast(self.winfo_toplevel(), "✓ Đã xuất báo cáo QC", kind="success")
            except Exception:
                pass
            messagebox.showinfo("Đã xuất", f"Báo cáo QC:\n{path}", parent=self)
        except Exception as exc:
            messagebox.showerror("Lỗi xuất báo cáo QC", str(exc)[:300], parent=self)

    def _qc_report_rows(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for index, question in enumerate(self._qc_questions, 1):
            review = self._qc_reviews[index - 1] if index - 1 < len(self._qc_reviews) else {}
            score = float(review.get("score", 0) or 0)
            ok = bool(review.get("ok", False))
            issue = str(review.get("issue", "") or review.get("tip", "") or "")
            rows.append({
                "STT": index,
                "Loại": getattr(question, "qtype", ""),
                "Mức": getattr(question, "level", ""),
                "Điểm": score,
                "Kết quả": "PASS" if ok else "REVIEW/FAIL",
                "Vấn đề / Gợi ý": issue,
                "Chủ đề": getattr(question, "topic", ""),
                "Nội dung": " ".join(str(getattr(question, "question", "") or "").split())[:240],
            })
        return rows

    def _write_qc_report_csv(self, path: str) -> None:
        import csv

        rows = self._qc_report_rows()
        columns = ["STT", "Loại", "Mức", "Điểm", "Kết quả", "Vấn đề / Gợi ý", "Chủ đề", "Nội dung"]
        with open(path, "w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

    def _write_qc_report_xlsx(self, path: str) -> None:
        import openpyxl
        from openpyxl.styles import Alignment, Font, PatternFill

        rows = self._qc_report_rows()
        columns = ["STT", "Loại", "Mức", "Điểm", "Kết quả", "Vấn đề / Gợi ý", "Chủ đề", "Nội dung"]
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "QC Report"
        ws.append(columns)
        for cell in ws[1]:
            cell.fill = PatternFill("solid", fgColor="1F497D")
            cell.font = Font(color="FFFFFF", bold=True)
            cell.alignment = Alignment(horizontal="center")
        for row in rows:
            ws.append([row.get(col, "") for col in columns])
        widths = [8, 10, 10, 10, 14, 44, 28, 60]
        for idx, width in enumerate(widths, 1):
            ws.column_dimensions[ws.cell(row=1, column=idx).column_letter].width = width
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        summary = wb.create_sheet("Tổng quan")
        total = len(rows)
        passed = sum(1 for row in rows if row.get("Kết quả") == "PASS")
        avg = sum(float(row.get("Điểm", 0) or 0) for row in rows) / max(total, 1)
        summary.append(["Tổng câu", total])
        summary.append(["PASS", passed])
        summary.append(["REVIEW/FAIL", total - passed])
        summary.append(["Điểm TB", round(avg, 2)])
        wb.save(path)

    def _resolve_ai_call_qc(self):
        try:
            from services.key_manager import get_key_manager
            from services.ai_service import create_ai_service

            provider = (
                self._qc_provider_var.get()
                if hasattr(self, "_qc_provider_var")
                else self._detect_qc_ai_provider()
            )
            model = (
                self._qc_model_var.get()
                if hasattr(self, "_qc_model_var")
                else QC_AI_MODEL_DEFAULT.get(provider, "gemini-3.8-flash")
            )
            key = get_key_manager().load(provider)
            if key or provider == "9Router":
                from services.retry_service import split_keys
                keys = (key if isinstance(key, list) else split_keys(key)) if key else ["dummy_key"]
                return create_ai_service(provider, keys, model).generate
        except Exception: pass
        return None

    # ── Tab 2: TikZ ───────────────────────────────────────────────────────
    def _build_tikz(self, parent):
        # Wrap content trong scrollable frame — editor + AI + buttons +
        # preview cộng lại lớn hơn chiều cao tabview, nếu không scroll
        # thì preview label bị bóp xuống 1×1 px (xem Alpha 18 bug fix).
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                           scrollbar_button_color=("#CBD5E1",
                                                                    "#475569"))
        scroll.pack(fill="both", expand=True)
        parent = scroll  # mọi card phía dưới pack vào scroll

        ctk.CTkLabel(parent,
                      text="Editor TikZ + AI vẽ hình + render preview (LaTeX). "
                           "Auto-heal, kho mẫu và preview PDF chạy trực tiếp trong V5.",
                      font=("Segoe UI", 11), text_color="gray",
                      justify="left"
                      ).pack(anchor="w", pady=(8, 12))

        # Editor
        ed_card = self._card(parent, "📝  Editor TikZ")
        hint_row = ctk.CTkFrame(ed_card, fg_color="transparent")
        hint_row.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            hint_row,
            text="Gõ nhanh: #diem, #truc, #ham, #bbt, #bxd, #goc... rồi nhấn Space/Tab/Enter để bung code.",
            text_color=("#475569", "#CBD5E1"),
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)
        snippet_labels = [f"{key} — {label}" for key, (label, _code) in TIKZ_SNIPPETS.items()]
        self._tikz_snippet_var = ctk.StringVar(value=snippet_labels[0])
        ctk.CTkOptionMenu(
            hint_row,
            values=snippet_labels,
            variable=self._tikz_snippet_var,
            width=230,
        ).pack(side="left", padx=(8, 4))
        ctk.CTkButton(
            hint_row,
            text="Chèn mẫu",
            width=86,
            height=28,
            command=self._insert_selected_tikz_snippet,
        ).pack(side="left")
        self._tikz_editor = ctk.CTkTextbox(
            ed_card, height=360, font=("Consolas", 12),
            fg_color=("#FAFAFA", "#0F172A"))
        self._tikz_editor.pack(fill="both", expand=True, pady=(0, 8))
        self._tikz_editor.bind("<space>", self._expand_tikz_snippet, add="+")
        self._tikz_editor.bind("<Tab>", self._expand_tikz_snippet, add="+")
        self._tikz_editor.bind("<Return>", self._expand_tikz_snippet, add="+")
        self._tikz_editor.insert("end",
            r"""\begin{tikzpicture}
  \draw[->] (-1,0) -- (4,0) node[right] {$x$};
  \draw[->] (0,-1) -- (0,4) node[above] {$y$};
  \draw[blue, thick] plot[domain=-0.5:2.5] (\x, {\x*\x});
  \node[blue] at (2.5, 3.5) {$y = x^2$};
\end{tikzpicture}""")

        # AI input
        ai_card = self._card(parent, "🤖  AI vẽ hình từ mô tả")
        ai_row = ctk.CTkFrame(ai_card, fg_color="transparent")
        ai_row.pack(fill="x")
        self._ai_desc = ctk.CTkEntry(
            ai_row, width=500,
            placeholder_text="vd: 'tam giác ABC vuông tại A, AB=3, AC=4'")
        self._ai_desc.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(ai_row, text="🤖  Generate", width=120,
                       fg_color="#A78BFA", hover_color="#8B5CF6",
                       command=self._ai_generate_tikz
                       ).pack(side="left", padx=2)

        self._tikz_status = ctk.CTkLabel(ai_card, text="",
                                            text_color="gray",
                                            font=("Segoe UI", 10, "italic"))
        self._tikz_status.pack(anchor="w", pady=(6, 0))
        self._tikz_error_box = ctk.CTkTextbox(
            ai_card,
            height=130,
            font=("Consolas", 10),
            wrap="word",
            fg_color=("#FFF7ED", "#1E1B12"),
            text_color=("#7C2D12", "#FED7AA"),
        )
        self._tikz_error_box.pack(fill="x", pady=(6, 0))
        self._set_tikz_error_text(
            "Khu vực báo lỗi chi tiết: thiếu ngoặc, sai cú pháp TikZ/LaTeX, thiếu package hoặc chưa cài LaTeX sẽ hiện ở đây."
        )

        # Actions
        act = ctk.CTkFrame(parent, fg_color="transparent")
        act.pack(fill="x", pady=8)
        act_r1 = ctk.CTkFrame(act, fg_color="transparent")
        act_r1.pack(fill="x", pady=(0, 4))
        act_r2 = ctk.CTkFrame(act, fg_color="transparent")
        act_r2.pack(fill="x")

        ctk.CTkButton(act_r1, text="🖼  Render preview", width=160,
                       fg_color=("#10B981", "#065F46"),
                       hover_color=("#059669", "#047857"),
                       command=self._render_tikz_preview
                       ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(act_r1, text="🔧 Auto-fix", width=110,
                       fg_color=("#F59E0B", "#92400E"),
                       hover_color=("#D97706", "#78350F"),
                       command=self._tikz_autofix
                       ).pack(side="left", padx=2)
        ctk.CTkButton(act_r1, text="📐 Tạo hình", width=110,
                       fg_color=("#0EA5E9", "#075985"),
                       hover_color=("#0284C7", "#0C4A6E"),
                       command=self._open_shape_builder
                       ).pack(side="left", padx=2)
        ctk.CTkButton(act_r1, text="📋 Copy", width=90,
                       command=self._copy_tikz
                       ).pack(side="left", padx=2)

        ctk.CTkButton(act_r2, text="📚 Kho mẫu", width=110,
                       fg_color=("#A78BFA", "#5B21B6"),
                       hover_color=("#8B5CF6", "#4C1D95"),
                       command=self._open_tikz_kb
                       ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(act_r2, text="💾 Lưu kho", width=110,
                       fg_color=("#14B8A6", "#0F766E"),
                       hover_color=("#0D9488", "#115E59"),
                       command=self._save_tikz_to_bank
                       ).pack(side="left", padx=2)
        ctk.CTkButton(act_r2, text="🗂 Kho hình", width=110,
                       fg_color=("#6366F1", "#3730A3"),
                       hover_color=("#4F46E5", "#312E81"),
                       command=self._open_figure_bank
                       ).pack(side="left", padx=2)

        # Preview area — Overleaf-style PDF viewer (Alpha 22d)
        self._tikz_preview_card = self._card(parent, "📄  Preview PDF")
        # Action toolbar phía trên viewer (copy/save/external open)
        prev_toolbar = ctk.CTkFrame(self._tikz_preview_card,
                                       fg_color="transparent")
        prev_toolbar.pack(fill="x", pady=(0, 4))
        pt_r1 = ctk.CTkFrame(prev_toolbar, fg_color="transparent")
        pt_r1.pack(fill="x", pady=(0, 3))
        pt_r2 = ctk.CTkFrame(prev_toolbar, fg_color="transparent")
        pt_r2.pack(fill="x")

        ctk.CTkButton(pt_r1, text="📋 Copy ảnh", width=110, height=28,
                        font=("Segoe UI", 11),
                        fg_color="#3B82F6", hover_color="#2563EB",
                        command=self._tikz_copy_image
                        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(pt_r1, text="💾 Lưu PNG", width=100, height=28,
                        font=("Segoe UI", 11),
                        command=lambda: self._tikz_save("png")
                        ).pack(side="left", padx=2)
        ctk.CTkButton(pt_r1, text="💾 Lưu PDF", width=100, height=28,
                        font=("Segoe UI", 11),
                        fg_color="#A78BFA", hover_color="#8B5CF6",
                        command=self._tikz_save_pdf
                        ).pack(side="left", padx=2)
        ctk.CTkButton(pt_r1, text="💾 Lưu EMF", width=100, height=28,
                        font=("Segoe UI", 11),
                        fg_color="#0EA5E9", hover_color="#0284C7",
                        command=self._tikz_save_emf
                        ).pack(side="left", padx=2)

        ctk.CTkButton(pt_r2, text="📋 Copy EMF", width=110, height=28,
                        font=("Segoe UI", 11),
                        fg_color="#0891B2", hover_color="#0E7490",
                        command=self._tikz_copy_emf
                        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(pt_r2, text="📄 Mở PDF ngoài", width=140, height=28,
                        font=("Segoe UI", 11),
                        command=self._tikz_open_pdf
                        ).pack(side="left", padx=2)
        ctk.CTkButton(pt_r2, text="🌐 Overleaf", width=110, height=28,
                        font=("Segoe UI", 11),
                        fg_color="#16A34A", hover_color="#15803D",
                        command=self._tikz_open_overleaf
                        ).pack(side="left", padx=2)

        # PDF viewer widget — Overleaf-style (multi-page + zoom in/out + pan)
        from v5.pdf_viewer import PDFViewer
        viewer_wrap = ctk.CTkFrame(self._tikz_preview_card,
                                      fg_color=("#E5E7EB", "#0F172A"),
                                      corner_radius=6, height=480)
        viewer_wrap.pack(fill="both", expand=True, pady=(0, 4))
        viewer_wrap.pack_propagate(False)
        self._tikz_viewer = PDFViewer(viewer_wrap)
        self._tikz_viewer.pack(fill="both", expand=True)

        # State giữ lại cho copy/save (PIL image render từ PDF page đầu)
        self._tikz_zoom = 1.0
        self._tikz_pil_img = None   # giữ PIL Image cho copy/save PNG
        self._tikz_png_path = ""
        self._tikz_pdf_path = ""
        self._tikz_emf_path = ""

    def _set_tikz_error_text(self, text: str) -> None:
        box = getattr(self, "_tikz_error_box", None)
        if box is None:
            return
        try:
            box.configure(state="normal")
            box.delete("0.0", "end")
            box.insert("end", text or "")
            box.configure(state="disabled")
        except Exception:
            pass

    def _insert_tikz_snippet(self, key: str) -> None:
        snippet = TIKZ_SNIPPETS.get(key)
        if not snippet:
            return
        _label, code = snippet
        try:
            self._tikz_editor.insert("insert", code)
            self._tikz_status.configure(
                text=f"✓ Đã chèn snippet {key}",
                text_color="#10B981",
            )
        except Exception:
            self._tikz_editor.insert("end", code)

    def _insert_selected_tikz_snippet(self) -> None:
        label = self._tikz_snippet_var.get() if hasattr(self, "_tikz_snippet_var") else ""
        key = label.split("—", 1)[0].strip()
        self._insert_tikz_snippet(key)

    def _expand_tikz_snippet(self, event=None):
        try:
            line_start = self._tikz_editor.index("insert linestart")
            line_text = self._tikz_editor.get(line_start, "insert")
            token = line_text.split()[-1] if line_text.split() else ""
            if token not in TIKZ_SNIPPETS:
                return None
            token_start = f"insert-{len(token)}c"
            self._tikz_editor.delete(token_start, "insert")
            self._insert_tikz_snippet(token)
            return "break"
        except Exception:
            return None

    def _render_tikz_preview(self):
        """Render code TikZ → PNG + PDF → hiển thị inline (Alpha 22b).

        Khác Alpha 10b: gọi render_tikz_to_image(return_log=True) để giữ
        luôn file PDF gốc trong cache → nút 'Mở PDF' hoạt động được.
        """
        code = self._tikz_editor.get("0.0", "end").strip()
        if not code:
            return
        self._tikz_status.configure(text="⏳ Đang render LaTeX...",
                                       text_color="#3B82F6")
        self._set_tikz_error_text("Đang kiểm tra cú pháp TikZ trước khi render...")
        try: self._tikz_viewer._show_message("⏳ Đang biên dịch LaTeX...")
        except Exception: pass
        self._tikz_pdf_path = ""   # reset
        self._tikz_emf_path = ""

        def _do():
            try:
                # Auto-heal layer 1: rule-based fix trước khi render
                from services.tikz_preflight import auto_fix, check, format_issues, Severity
                code_fixed = auto_fix(code)
                # Nếu auto_fix sửa code → cập nhật editor
                if code_fixed != code:
                    self.after(0, lambda: (
                        self._tikz_editor.delete("0.0", "end"),
                        self._tikz_editor.insert("end", code_fixed)))
                issues = check(code_fixed)
                blocking = [issue for issue in issues if issue.severity == Severity.ERROR]
                if blocking:
                    raise RuntimeError("Preflight TikZ phát hiện lỗi trước khi render:\n" + format_issues(issues))
                if issues:
                    self.after(0, lambda: self._set_tikz_error_text(format_issues(issues)))

                # Check cache PNG + PDF trước
                from services import tikz_cache
                png_path = tikz_cache.get(code_fixed)
                pdf_path = ""
                if png_path:
                    # Có PNG cached → check PDF cùng hash đã cache chưa
                    from pathlib import Path
                    cache_pdf = Path(png_path).with_suffix(".pdf")
                    if cache_pdf.exists():
                        pdf_path = str(cache_pdf)

                if not png_path or not pdf_path:
                    # Render mới (hoặc lấy PDF còn thiếu) và giữ PDF để preview.
                    from services.tikz_renderer import render_tikz_to_image
                    img, log_text, tmp_pdf = render_tikz_to_image(
                        code_fixed, dpi=200, return_log=True)
                    # Save PNG vào cache (luôn) + copy PDF cạnh PNG
                    if not png_path:
                        png_path = tikz_cache.put_pil(code_fixed, img)
                    if tmp_pdf:
                        try:
                            import shutil
                            from pathlib import Path as _P
                            cache_pdf = _P(png_path).with_suffix(".pdf")
                            shutil.copy2(tmp_pdf, str(cache_pdf))
                            pdf_path = str(cache_pdf)
                        except Exception as e:
                            print(f"copy pdf to cache fail: {e}")

                self.after(0, lambda: self._on_tikz_rendered(
                    png_path, "", code_fixed, pdf_path=pdf_path))
            except Exception as e:
                err = str(e)
                self.after(0, lambda: self._on_tikz_rendered(None, err, code))
        threading.Thread(target=_do, daemon=True).start()

    def _on_tikz_rendered(self, png, err, code="", pdf_path=""):
        try:
            if not self.winfo_exists(): return
        except Exception: return
        if err or not png:
            try:
                from services.tikz_preflight import explain_render_error
                detail = explain_render_error(err or "không tạo được PNG", code)
            except Exception:
                detail = err or "không tạo được PNG"
            self._tikz_status.configure(
                text=f"✘ Lỗi render TikZ — xem chi tiết bên dưới",
                text_color="#EF4444")
            self._set_tikz_error_text(detail)
            try: self._tikz_viewer._show_message(
                f"✘ Render thất bại.\n{detail[:500]}")
            except Exception: pass
            # Auto-heal layer 2: offer AI fix
            if code and messagebox.askyesno(
                "Render thất bại",
                "Code TikZ biên dịch lỗi.\n\n🩹 Dùng AI sửa tự động (auto-heal)?",
                parent=self):
                self._tikz_status.configure(text="🩹 AI đang sửa code…",
                                               text_color="#3B82F6")
                self._ai_heal_tikz(code, err or "render fail")
            return
        # Lưu state cho copy/save
        try:
            from PIL import Image
            self._tikz_pil_img = Image.open(png)
            self._tikz_png_path = png
            self._tikz_pdf_path = pdf_path or ""
            self._auto_save_rendered_figure(code, png)
        except Exception as e:
            print(f"load PIL fail: {e}")

        # Load PDF vào PDFViewer (Overleaf-style) — nguồn hiển thị chính
        if pdf_path:
            try:
                ok = self._tikz_viewer.load_pdf(pdf_path)
                if ok:
                    self._set_tikz_error_text("✓ Render OK — không phát hiện lỗi TikZ/LaTeX.")
                    self._tikz_status.configure(
                        text="✓ Render OK  •  📄 PDF viewer (Overleaf-style) — "
                              "Ctrl+Wheel = zoom, Shift+Drag = pan",
                        text_color="#10B981")
                    return
            except Exception as e:
                print(f"viewer load_pdf fail: {e}")
        # Fallback: nếu không có PDF (raise tại render) → show PNG inline
        self._tikz_status.configure(
            text="⚠ Render OK nhưng KHÔNG có PDF — fallback PNG",
            text_color="#F59E0B")
        try:
            self._tikz_viewer._show_message(
                "PDF chưa cache. Render lại để có PDF viewer.")
        except Exception: pass

    def _tikz_copy_image(self):
        """Copy PIL image vào clipboard (Windows)."""
        if self._tikz_pil_img is None:
            messagebox.showwarning("Chưa có ảnh",
                "Bấm 'Render preview' trước.", parent=self)
            return
        try:
            from io import BytesIO
            import sys
            output = BytesIO()
            self._tikz_pil_img.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]  # bỏ BMP header 14 bytes
            output.close()
            if sys.platform == "win32":
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                self._tikz_status.configure(text="✓ Đã copy ảnh vào clipboard",
                                              text_color="#10B981")
            else:
                # Fallback: copy file path
                from pathlib import Path
                if self._tikz_png_path:
                    self.clipboard_clear()
                    self.clipboard_append(self._tikz_png_path)
                self._tikz_status.configure(
                    text="✓ Copy path (Linux/Mac không hỗ trợ binary clipboard)",
                    text_color="#10B981")
        except Exception as e:
            messagebox.showerror("Lỗi copy",
                f"{type(e).__name__}: {e}\n\n"
                "Có thể thiếu pywin32. Cài: pip install pywin32",
                parent=self)

    def _tikz_save(self, fmt: str = "png"):
        """Lưu ảnh ra file (.png hoặc .svg)."""
        if self._tikz_pil_img is None:
            messagebox.showwarning("Chưa có ảnh",
                "Bấm 'Render preview' trước.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=f".{fmt}",
            filetypes=[("PNG image", "*.png"), ("JPEG image", "*.jpg"),
                        ("All", "*.*")],
            initialfile=f"tikz_render.{fmt}")
        if not path: return
        try:
            self._tikz_pil_img.save(path)
            self._tikz_status.configure(text=f"✓ Đã lưu: {path[-40:]}",
                                           text_color="#10B981")
        except Exception as e:
            messagebox.showerror("Lỗi lưu", str(e), parent=self)

    def _auto_save_rendered_figure(self, code: str, png_path: str) -> None:
        """Đồng bộ preview thành công vào kho hình, không tạo bản ghi trùng."""
        try:
            from services import figure_bank

            figure_bank.save_rendered(
                code,
                png_path=png_path,
                title="Hình TikZ tự lưu sau render",
                description="Tự động lưu từ màn TikZ V5 sau khi render preview.",
                tags=["TikZ", "tự lưu"],
                source="rendered",
            )
        except Exception as exc:
            print(f"auto save rendered figure fail: {exc}")

    def _tikz_open_overleaf(self):
        """Mở code hiện tại trên Overleaf và copy source .tex dự phòng."""
        code = self._tikz_editor.get("0.0", "end").strip()
        if not code:
            messagebox.showwarning("Chưa có code", "Nhập code TikZ trước.",
                                   parent=self)
            return
        try:
            from services import overleaf_exporter

            _launcher_path, tex_source = overleaf_exporter.open_tikz_in_overleaf(code)
            self.clipboard_clear()
            self.clipboard_append(tex_source)
            self.update()
            self._tikz_status.configure(
                text="✓ Đã mở Overleaf • source .tex đã copy dự phòng",
                text_color="#10B981",
            )
        except Exception as exc:
            messagebox.showerror("Lỗi Overleaf", str(exc), parent=self)

    def _ensure_tikz_emf_async(self, on_ready):
        """Tạo EMF cạnh PDF cache bằng Inkscape rồi gọi callback trên UI thread."""
        from pathlib import Path

        pdf_path = self._tikz_pdf_path or ""
        if not pdf_path and self._tikz_png_path:
            candidate = Path(self._tikz_png_path).with_suffix(".pdf")
            if candidate.is_file():
                pdf_path = str(candidate)
        if not pdf_path or not Path(pdf_path).is_file():
            messagebox.showwarning(
                "Chưa có PDF",
                "Bấm 'Render preview' trước để tạo PDF vector rồi xuất EMF.",
                parent=self,
            )
            return

        self._tikz_status.configure(
            text="⏳ Đang chuyển PDF vector → EMF bằng Inkscape...",
            text_color="#3B82F6",
        )

        def _worker():
            try:
                from services.tikz_vector_export import convert_pdf_to_emf

                emf_path = convert_pdf_to_emf(
                    pdf_path,
                    Path(pdf_path).with_suffix(".emf"),
                    text_to_path=True,
                )
                self.after(0, lambda path=str(emf_path): on_ready(path))
            except Exception as exc:
                error = str(exc)
                self.after(0, lambda: messagebox.showerror(
                    "Lỗi xuất EMF",
                    error,
                    parent=self,
                ))

        threading.Thread(target=_worker, daemon=True,
                         name="tikz-pdf-to-emf").start()

    def _tikz_save_emf(self):
        """Lưu EMF vector để chèn vào Word mà không vỡ nét."""
        def _save(emf_path: str):
            self._tikz_emf_path = emf_path
            path = filedialog.asksaveasfilename(
                parent=self,
                defaultextension=".emf",
                filetypes=[("Enhanced Metafile", "*.emf"), ("All", "*.*")],
                initialfile="tikz_render.emf",
            )
            if not path:
                return
            try:
                import shutil

                shutil.copy2(emf_path, path)
                self._tikz_status.configure(
                    text=f"✓ Đã lưu EMF vector: {path[-40:]}",
                    text_color="#10B981",
                )
            except Exception as exc:
                messagebox.showerror("Lỗi lưu EMF", str(exc), parent=self)

        self._ensure_tikz_emf_async(_save)

    def _tikz_copy_emf(self):
        """Copy CF_ENHMETAFILE để Word dán đúng ảnh vector."""
        def _copy(emf_path: str):
            try:
                from services.tikz_vector_export import copy_emf_to_clipboard

                copy_emf_to_clipboard(emf_path)
                self._tikz_emf_path = emf_path
                self._tikz_status.configure(
                    text="✓ Đã copy EMF vector • dán trực tiếp vào Word bằng Ctrl+V",
                    text_color="#10B981",
                )
            except Exception as exc:
                messagebox.showerror("Lỗi copy EMF", str(exc), parent=self)

        self._ensure_tikz_emf_async(_copy)

    def _tikz_open_pdf(self):
        """Mở PDF gốc của TikZ trong viewer hệ thống.

        Alpha 22b: PDF được lưu cùng cache PNG (xem _render_tikz_preview).
        Thứ tự tìm: self._tikz_pdf_path (set khi render) > cùng folder PNG.
        Nếu không có PDF → render lại với return_log=True.
        """
        from pathlib import Path
        pdf_path = self._tikz_pdf_path or ""
        # Fallback: thử path cùng cache
        if not pdf_path and self._tikz_png_path:
            cand = Path(self._tikz_png_path).with_suffix(".pdf")
            if cand.exists():
                pdf_path = str(cand)

        if not pdf_path:
            # Không có PDF → render lại để sinh
            code = self._tikz_editor.get("0.0", "end").strip()
            if not code:
                messagebox.showwarning("Chưa có code",
                    "Nhập code TikZ trước.", parent=self)
                return
            if not messagebox.askyesno(
                "PDF chưa có",
                "Chưa có PDF cache. Render lại để sinh PDF?\n"
                "(Mất 1-3 giây)",
                parent=self):
                return
            self._tikz_status.configure(text="⏳ Đang render PDF…",
                                           text_color="#3B82F6")

            def _do_render_pdf():
                try:
                    from services.tikz_preflight import auto_fix
                    from services.tikz_renderer import render_tikz_to_image
                    from services import tikz_cache
                    import shutil
                    code_fixed = auto_fix(code)
                    img, _log, tmp_pdf = render_tikz_to_image(
                        code_fixed, dpi=200, return_log=True)
                    png_path = (tikz_cache.get(code_fixed)
                                  or tikz_cache.put_pil(code_fixed, img))
                    final_pdf = ""
                    if tmp_pdf:
                        cache_pdf = Path(png_path).with_suffix(".pdf")
                        try:
                            shutil.copy2(tmp_pdf, str(cache_pdf))
                            final_pdf = str(cache_pdf)
                        except Exception: pass
                    if final_pdf:
                        self._tikz_pdf_path = final_pdf
                        self.after(0, lambda: self._open_pdf_file(final_pdf))
                    else:
                        self.after(0, lambda: messagebox.showerror(
                            "Lỗi render PDF",
                            "Không tạo được file PDF.",
                            parent=self))
                except Exception as e:
                    err = str(e)
                    self.after(0, lambda: messagebox.showerror(
                        "Lỗi render PDF", err, parent=self))
            threading.Thread(target=_do_render_pdf, daemon=True).start()
            return

        self._open_pdf_file(pdf_path)

    def _open_pdf_file(self, pdf_path: str):
        """Mở file PDF bằng viewer hệ thống."""
        try:
            import subprocess, sys, os
            if sys.platform == "win32":
                os.startfile(pdf_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", pdf_path])
            else:
                subprocess.Popen(["xdg-open", pdf_path])
            self._tikz_status.configure(text=f"✓ Đã mở PDF",
                                           text_color="#10B981")
        except Exception as e:
            messagebox.showerror("Lỗi mở PDF", str(e), parent=self)

    def _tikz_save_pdf(self):
        """Lưu file PDF gốc ra vị trí user chọn."""
        if not self._tikz_pdf_path:
            messagebox.showwarning(
                "Chưa có PDF",
                "Bấm '🖼 Render preview' trước, hoặc '📄 Mở PDF' để sinh PDF.",
                parent=self)
            return
        from pathlib import Path
        if not Path(self._tikz_pdf_path).exists():
            messagebox.showerror(
                "PDF không tìm thấy",
                f"File PDF không còn ở:\n{self._tikz_pdf_path}\n"
                "Render lại để sinh PDF mới.",
                parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".pdf",
            filetypes=[("PDF document", "*.pdf"), ("All", "*.*")],
            initialfile="tikz_render.pdf")
        if not path: return
        try:
            import shutil
            shutil.copy2(self._tikz_pdf_path, path)
            self._tikz_status.configure(text=f"✓ Đã lưu PDF: {path[-40:]}",
                                           text_color="#10B981")
        except Exception as e:
            messagebox.showerror("Lỗi lưu PDF", str(e), parent=self)

    def _ai_generate_tikz(self):
        desc = self._ai_desc.get().strip()
        if not desc:
            messagebox.showwarning("Trống", "Nhập mô tả trước.", parent=self)
            return
        self._tikz_status.configure(text="⏳ Đang gọi AI...",
                                       text_color="#3B82F6")
        def _do():
            try:
                from services.key_manager import get_key_manager
                from services.ai_service import create_ai_service
                km = get_key_manager()
                key = km.load("Google Gemini")
                if not key:
                    self.after(0, lambda: self._tikz_status.configure(
                        text="✘ Chưa có Gemini key (Cấu hình → API key)",
                        text_color="#EF4444"))
                    return
                from services.retry_service import split_keys
                keys = key if isinstance(key, list) else split_keys(key)
                svc = create_ai_service("Google Gemini", keys, "gemini-3.8-flash")
                prompt = (
                    "Vẽ hình bằng TikZ theo mô tả. CHỈ trả code TikZ "
                    "trong khối \\begin{tikzpicture}...\\end{tikzpicture}, "
                    "không markdown fence, không lời mở đầu.\n\n"
                    f"Mô tả: {desc}")
                raw = svc.generate(prompt)
                # Extract tikzpicture
                import re
                m = re.search(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
                                raw, re.DOTALL)
                code = m.group(0) if m else raw
                self.after(0, lambda c=code: (
                    self._tikz_editor.delete("0.0", "end"),
                    self._tikz_editor.insert("end", c),
                    self._tikz_status.configure(
                        text="✓ AI đã sinh code", text_color="#10B981")))
            except Exception as e:
                self.after(0, lambda err=str(e): self._tikz_status.configure(
                    text=f"✘ Lỗi: {err[:80]}", text_color="#EF4444"))
        threading.Thread(target=_do, daemon=True).start()

    def _copy_tikz(self):
        code = self._tikz_editor.get("0.0", "end").strip()
        if not code: return
        self.clipboard_clear(); self.clipboard_append(code)
        self._tikz_status.configure(text="✓ Đã copy",
                                       text_color="#10B981")

    def _save_tikz_to_bank(self):
        """Lưu code TikZ hiện tại vào Figure Bank V5."""
        code = self._tikz_editor.get("0.0", "end").strip()
        if not code:
            messagebox.showwarning("Chưa có code", "Nhập code TikZ trước.",
                                   parent=self)
            return
        try:
            from v5.figure_bank_dialog import SaveFigureDialog
            dlg = SaveFigureDialog(
                self.winfo_toplevel(),
                has_rendered_image=self._tikz_pil_img is not None,
            )
            self.wait_window(dlg)
            if not getattr(dlg, "confirmed", False):
                return
            from services import figure_bank
            fid = figure_bank.save(
                tikz_code=code,
                title=dlg.result_title,
                description=dlg.result_desc,
                tags=dlg.result_tags,
                source="manual",
                png_pil=(self._tikz_pil_img if dlg.save_png else None),
            )
            self._tikz_status.configure(
                text=f"✓ Đã lưu hình vào kho (ID {fid})",
                text_color="#10B981")
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(),
                       f"✓ Đã lưu hình TikZ vào kho (ID {fid})",
                       kind="success", duration=4)
        except Exception as e:
            messagebox.showerror("Lỗi lưu kho hình", str(e)[:300],
                                 parent=self)

    def _open_figure_bank(self):
        """Mở Figure Bank V5 để nạp lại code TikZ đã lưu."""
        try:
            from v5.figure_bank_dialog import FigureBankDialog

            def _load(code: str, title: str):
                self._tikz_editor.delete("0.0", "end")
                self._tikz_editor.insert("end", code)
                self._tikz_status.configure(
                    text=f"✓ Đã nạp hình từ kho: {title[:48]}",
                    text_color="#10B981")

            FigureBankDialog(self.winfo_toplevel(), on_load=_load)
        except Exception as e:
            messagebox.showerror("Lỗi mở kho hình", str(e)[:300],
                                 parent=self)

    def _open_shape_builder(self):
        """Mở công cụ tạo hình TikZ từ thông số, thay thế Shape Builder V4."""
        try:
            from v5.tikz_shape_builder import ShapeBuilderDialog
            dlg = ShapeBuilderDialog(self.winfo_toplevel())
            self.wait_window(dlg)
            code = getattr(dlg, "result", None)
            if not code:
                return
            self._tikz_editor.delete("0.0", "end")
            self._tikz_editor.insert("end", code)
            self._tikz_status.configure(
                text="✓ Đã chèn code từ công cụ tạo hình",
                text_color="#10B981")
        except Exception as e:
            messagebox.showerror("Lỗi tạo hình", str(e)[:300], parent=self)

    def _tikz_autofix(self):
        """Auto-fix lỗi LaTeX thường gặp (rule-based) + báo issue (Alpha 12)."""
        code = self._tikz_editor.get("0.0", "end").strip()
        if not code:
            return
        try:
            from services.tikz_preflight import auto_fix, check, format_issues
            fixed = auto_fix(code)
            issues = check(fixed)
            if fixed != code:
                self._tikz_editor.delete("0.0", "end")
                self._tikz_editor.insert("end", fixed)
            msg = format_issues(issues) if issues else "không còn lỗi rõ ràng"
            self._set_tikz_error_text(msg)
            n = len(issues)
            self._tikz_status.configure(
                text=(f"🔧 Auto-fix xong"
                      + (" (đã sửa code)" if fixed != code else "")
                      + f" · {n} cảnh báo: {msg[:60]}"),
                text_color=("#10B981" if n == 0 else "#F59E0B"))
        except Exception as e:
            self._tikz_status.configure(text=f"✘ Auto-fix lỗi: {e}",
                                           text_color="#EF4444")

    def _ai_heal_tikz(self, code: str, error: str):
        """AI sửa code TikZ khi render fail (auto-heal layer 2)."""
        def _do():
            try:
                from services.key_manager import get_key_manager
                from services.ai_service import create_ai_service
                km = get_key_manager()
                key = km.load("Google Gemini")
                if not key:
                    self.after(0, lambda: self._tikz_status.configure(
                        text="✘ Cần Gemini key để AI heal", text_color="#EF4444"))
                    return
                from services.retry_service import split_keys
                keys = key if isinstance(key, list) else split_keys(key)
                svc = create_ai_service("Google Gemini", keys, "gemini-3.8-flash")
                prompt = (
                    "Code TikZ sau bị lỗi khi biên dịch LaTeX. Hãy SỬA để "
                    "biên dịch được. CHỈ trả code trong khối "
                    "\\begin{tikzpicture}...\\end{tikzpicture}, không giải thích.\n\n"
                    f"Lỗi:\n{error[:300]}\n\nCode:\n{code}")
                raw = svc.generate(prompt)
                import re
                m = re.search(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
                                raw, re.DOTALL)
                healed = m.group(0) if m else raw
                self.after(0, lambda: self._on_heal_done(healed))
            except Exception as e:
                self.after(0, lambda: self._tikz_status.configure(
                    text=f"✘ AI heal lỗi: {str(e)[:60]}", text_color="#EF4444"))
        import threading as _th
        _th.Thread(target=_do, daemon=True).start()

    def _on_heal_done(self, healed: str):
        try:
            if not self.winfo_exists(): return
        except Exception: return
        self._tikz_editor.delete("0.0", "end")
        self._tikz_editor.insert("end", healed)
        self._tikz_status.configure(
            text="🩹 AI đã sửa code — nhấn Render lại để kiểm tra",
            text_color="#10B981")

    def _open_tikz_kb(self):
        """Mở dialog kho mẫu TikZ (88 mẫu) — search + insert (Alpha 12)."""
        try:
            from services.tikz_kb import get_template_names, get_template_code, find_relevant
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được kho mẫu: {e}", parent=self)
            return

        dlg = ctk.CTkToplevel(self)
        dlg.title("📚 Kho mẫu TikZ")
        dlg.geometry("560x560")
        try: dlg.attributes("-topmost", True)
        except Exception: pass
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        ctk.CTkLabel(dlg, text="📚 Kho mẫu TikZ — chọn để chèn vào editor",
                      font=("Segoe UI", 13, "bold")).pack(pady=(12, 4))

        # Top row: search + group filter (Alpha 22 — phân nhóm)
        top_row = ctk.CTkFrame(dlg, fg_color="transparent")
        top_row.pack(fill="x", padx=14, pady=(0, 4))
        search_var = ctk.StringVar()
        ctk.CTkEntry(top_row, textvariable=search_var,
                      placeholder_text="🔍 Tìm mẫu (vd: tam giác, BBT, parabol)…"
                      ).pack(side="left", fill="x", expand=True)

        # Define groups: (display label, list of matching tags / keywords)
        GROUPS = [
            ("🌐 Tất cả",         None),
            ("📐 Hình phẳng",     {"2d", "tam giác", "tứ giác", "đường tròn",
                                     "hình bình hành", "đường cao"}),
            ("🔷 Hình không gian", {"3d", "hình chóp", "hình lập phương",
                                     "hình trụ", "pyramid", "lập phương"}),
            ("📈 Đồ thị hàm số",   {"graph", "chart", "bậc 2", "bậc 3",
                                     "bậc 4", "lượng giác", "sin", "mũ",
                                     "log", "hyperbol", "trùng phương",
                                     "phân thức", "nghịch biến"}),
            ("📊 BBT",            {"bbt"}),
            ("➖ Khác",            {"trục số", "misc"}),
        ]
        group_var = ctk.StringVar(value=GROUPS[0][0])
        group_lookup = {g[0]: g[1] for g in GROUPS}
        ctk.CTkOptionMenu(top_row, variable=group_var,
                            values=[g[0] for g in GROUPS], width=180,
                            command=lambda _v: _render_list()
                            ).pack(side="left", padx=(8, 0))

        # Count badge
        count_lbl = ctk.CTkLabel(dlg, text="", text_color="gray",
                                    font=("Segoe UI", 10, "italic"))
        count_lbl.pack(anchor="w", padx=18)

        lst = ctk.CTkScrollableFrame(dlg, fg_color=("#F9FAFB", "#0F172A"))
        lst.pack(fill="both", expand=True, padx=14, pady=(2, 12))

        def _insert(name):
            code = get_template_code(name)
            if code:
                self._tikz_editor.delete("0.0", "end")
                self._tikz_editor.insert("end", code)
                self._tikz_status.configure(
                    text=f"✓ Đã chèn mẫu: {name[:40]}", text_color="#10B981")
            dlg.destroy()

        def _filter_by_group(templates, group_tags):
            """Lọc templates theo nhóm: match nếu có bất kỳ tag nào trong group_tags."""
            if not group_tags:
                return templates
            result = []
            for t in templates:
                tag_low = [tag.lower() for tag in (t.tags or [])]
                name_low = t.name.lower()
                if any(g in tag_low or g in name_low for g in group_tags):
                    result.append(t)
            return result

        def _render_list(*_):
            for c in lst.winfo_children(): c.destroy()
            q = search_var.get().strip()
            group_tags = group_lookup.get(group_var.get())

            from services.tikz_kb import all_templates
            templates = all_templates()
            # 1. Filter group
            templates = _filter_by_group(templates, group_tags)
            # 2. Filter search
            if q:
                ql = q.lower()
                try: relevant_names = {t.name for t in find_relevant(q, k=40)}
                except Exception: relevant_names = set()
                templates = [t for t in templates
                              if ql in t.name.lower()
                              or ql in " ".join(t.tags or []).lower()
                              or t.name in relevant_names]
            count_lbl.configure(text=f"  {len(templates)} mẫu  "
                                       f"(nhóm: {group_var.get()})")
            for t in templates[:80]:
                # Hiển thị name + 2-3 tags đầu
                tags_str = (" · ".join(t.tags[:3]) if t.tags else "")
                btn_text = t.name
                if tags_str:
                    btn_text = f"{t.name}    🏷 {tags_str}"
                ctk.CTkButton(lst, text=btn_text, anchor="w", height=32,
                                font=("Segoe UI", 10),
                                fg_color=("#FFFFFF", "#293548"),
                                text_color=("#1F2937", "#F1F5F9"),
                                hover_color=("#DBEAFE", "#1E3A8A"),
                                command=lambda n=t.name: _insert(n)
                                ).pack(fill="x", padx=2, pady=1)
            if not templates:
                ctk.CTkLabel(lst, text="(không tìm thấy mẫu trong nhóm này)",
                              text_color="gray").pack(pady=20)

        search_var.trace_add("write", _render_list)
        _render_list()
        try: dlg.grab_set()
        except Exception: pass

    # ── Card helper ───────────────────────────────────────────────────────
    def _card(self, parent, title: str) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(parent, fg_color=("white", "#293548"),
                                corner_radius=10, border_width=1,
                                border_color=("#E5E7EB", "#334155"))
        outer.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(inner, text=title,
                      font=("Segoe UI", 13, "bold"),
                      anchor="w").pack(anchor="w", pady=(0, 8))
        return inner
