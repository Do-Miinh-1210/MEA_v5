"""
v5/views/nhch.py — Duyệt NHCH local + Import PDF/Word/Ảnh + Sync Cloud.

Reuse:
    storage.database — SQLite local NHCH
    services.license_manager — nhch_upload_batch (push) + nhch_list (tải)
    v5.import_wizard.ImportWizardCTk — wizard import thuần CTk
    v5.edit_question.EditQuestionDialogCTk — sửa câu thuần CTk
"""
from __future__ import annotations

import threading
from typing import Callable

import customtkinter as ctk
from tkinter import messagebox, ttk

# Reuse v4 — search_questions() không filter = trả về tất cả câu (limit 5000)
try:
    from storage.database import search_questions as list_all_questions
except Exception:
    list_all_questions = lambda: []


AI_PROVIDERS = ["Google Gemini", "Anthropic Claude", "DeepSeek", "9Router"]
AI_MODEL_DEFAULT = {
    "Google Gemini": "gemini-3.8-flash",
    "Anthropic Claude": "claude-sonnet-4-5",
    "DeepSeek": "deepseek-chat",
    "9Router": "ag/gemini-3.8-flash",
}
AI_MODEL_OPTIONS = {
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


class NHCHView(ctk.CTkFrame):
    """Browse câu hỏi local + nút Import + Sync Cloud."""

    def __init__(
        self,
        parent,
        *,
        on_navigate: Callable[[str], None] | None = None,
        on_add_questions: Callable[[list, dict], None] | None = None,
        can_use_feature: Callable[..., bool] | None = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self._on_navigate = on_navigate
        self._on_add_questions = on_add_questions
        self._can_use_feature = can_use_feature
        self._questions_cache: list = []
        self._row_questions: dict[str, dict] = {}
        self._checked_keys: set[str] = set()
        self._build()
        # Load NHCH async
        threading.Thread(target=self._reload_questions, daemon=True).start()

    def _build(self):
        # Toàn bộ nội dung trong vùng cuộn (CTkScrollableFrame) để chống co ép
        # khi chiều cao cửa sổ ở minsize (600px khả dụng) hoặc thu nhỏ
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)

        # Header
        head = ctk.CTkFrame(self._scroll, fg_color="transparent")
        head.pack(fill="x", pady=(4, 12))
        ctk.CTkLabel(head, text="🏛  Ngân hàng câu hỏi",
                      font=("Segoe UI", 24, "bold")
                      ).pack(side="left")
        # Header buttons: SECONDARY tier (h=32, font 12 bold) — đồng nhất
        # với Exam Create / Convert headers. Trước Alpha 20 ở h=28 không khớp.
        ctk.CTkButton(head, text="🔄 Reload",
                       width=110, height=32,
                       font=("Segoe UI", 12, "bold"),
                       command=lambda: threading.Thread(
                           target=self._reload_questions, daemon=True).start()
                       ).pack(side="right", padx=4)
        ctk.CTkButton(head, text="📊 Thống kê",
                       width=130, height=32,
                       font=("Segoe UI", 12, "bold"),
                       fg_color=("#10B981", "#047857"),
                       hover_color=("#059669", "#065F46"),
                       command=self.open_stats
                       ).pack(side="right", padx=4)

        # Hướng dẫn ngắn
        ctk.CTkLabel(self._scroll,
                      text="Kho câu hỏi cá nhân (lưu máy). Thêm câu bằng: "
                           "📄 Import đề cũ (AI đọc) · ✏️ Tạo đề rồi push · "
                           "☁ Tải từ Cloud. Tích ☐ ở các câu cần lấy, "
                           "bấm ➕ để đưa vào đề. Double-click để sửa.",
                      font=("Segoe UI", 10), text_color="gray",
                      anchor="w", justify="left", wraplength=820
                      ).pack(anchor="w", pady=(0, 8))

        # ── Toolbar: Local & Cloud clusters ───────────────────────────
        toolbar = ctk.CTkFrame(self._scroll, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 10))

        # Cụm công cụ Local (Import, Gần đây, Thêm vào đề)
        local_grp = ctk.CTkFrame(toolbar, fg_color="transparent")
        local_grp.pack(anchor="w", pady=(0, 6))

        ctk.CTkButton(local_grp, text="📄  Import PDF/Word/Ảnh",
                       fg_color="#A78BFA", hover_color="#8B5CF6",
                       height=38, font=("Segoe UI", 12, "bold"),
                       command=self._open_import_pdf
                       ).pack(side="left", padx=(0, 6))

        # Recent files dropdown
        self._recent_btn = ctk.CTkButton(
            local_grp, text="📂  Gần đây ▾", width=115,
            fg_color="#6B7280", hover_color="#4B5563",
            height=38, font=("Segoe UI", 11),
            command=self._show_recent_menu)
        self._recent_btn.pack(side="left", padx=(0, 6))

        self._add_exam_btn = ctk.CTkButton(
            local_grp, text="➕  Thêm vào đề", width=140,
            fg_color="#10B981", hover_color="#059669",
            height=38, font=("Segoe UI", 12, "bold"),
            command=self._add_selected_to_exam)
        self._add_exam_btn.pack(side="left", padx=(0, 6))

        # Cụm công cụ Cloud (Sync & Tải Cloud)
        cloud_grp = ctk.CTkFrame(toolbar, fg_color="transparent")
        cloud_grp.pack(anchor="w")

        self._upload_btn = ctk.CTkButton(
            cloud_grp, text="☁  Sync ↑ Cloud",
            fg_color="#3B82F6", hover_color="#2563EB",
            height=38, font=("Segoe UI", 12),
            command=self._sync_to_cloud)
        self._upload_btn.pack(side="left", padx=(0, 6))
        self._download_btn = ctk.CTkButton(
            cloud_grp, text="☁  Tải ↓ Cloud",
            fg_color="#0891B2", hover_color="#0E7490",
            height=38, font=("Segoe UI", 12),
            command=self._download_from_cloud)
        self._download_btn.pack(side="left")

        ai_bar = ctk.CTkFrame(self._scroll, fg_color=("white", "#293548"),
                              corner_radius=8, border_width=1,
                              border_color=("#E5E7EB", "#334155"))
        ai_bar.pack(fill="x", pady=(0, 8))
        ai_inner = ctk.CTkFrame(ai_bar, fg_color="transparent")
        ai_inner.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(ai_inner, text="AI NHCH:", width=68, anchor="w",
                     font=("Segoe UI", 11, "bold")).pack(side="left")
        self._ai_provider_var = ctk.StringVar(value=self._detect_ai_provider())
        ctk.CTkOptionMenu(
            ai_inner,
            values=AI_PROVIDERS,
            variable=self._ai_provider_var,
            width=170,
            command=self._on_ai_provider_change,
        ).pack(side="left", padx=(0, 8))
        self._ai_model_var = ctk.StringVar(
            value=AI_MODEL_DEFAULT.get(self._ai_provider_var.get(), "gemini-3.8-flash")
        )
        self._ai_model_menu = ctk.CTkOptionMenu(
            ai_inner,
            values=self._ai_model_options(self._ai_provider_var.get()),
            variable=self._ai_model_var,
            width=210,
        )
        self._ai_model_menu.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(
            ai_inner,
            text="Dung cho AI sua/QC khi double-click cau hoi.",
            text_color="gray",
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        # ── Filter bar ─────────────────────────────────────────────────
        filt = ctk.CTkFrame(self._scroll, fg_color=("white", "#293548"),
                              corner_radius=8, border_width=1,
                              border_color=("#E5E7EB", "#334155"))
        filt.pack(fill="x", pady=(0, 10))
        finner = ctk.CTkFrame(filt, fg_color="transparent")
        finner.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(finner, text="🔍 Tìm:", width=40
                      ).grid(row=0, column=0, padx=(0, 4))
        self._search_var = ctk.StringVar()
        ctk.CTkEntry(finner, textvariable=self._search_var, width=200,
                       placeholder_text="Từ khoá..."
                       ).grid(row=0, column=1, padx=(0, 12))
        # Debounce: chờ 250ms sau keystroke cuối mới render (NHCH lớn không lag)
        self._search_after_id = None
        self._search_var.trace_add("write", lambda *_: self._debounced_search())

        ctk.CTkLabel(finner, text="Loại:", width=40
                      ).grid(row=0, column=2, padx=(0, 4))
        self._qtype_var = ctk.StringVar(value="Tất cả")
        ctk.CTkOptionMenu(finner, values=["Tất cả", "TN", "DS", "TLN", "TL"],
                            variable=self._qtype_var, width=100,
                            command=lambda _: self._render_table()
                            ).grid(row=0, column=3, padx=(0, 12))

        ctk.CTkLabel(finner, text="Mức:", width=40
                      ).grid(row=0, column=4, padx=(0, 4))
        self._level_var = ctk.StringVar(value="Tất cả")
        ctk.CTkOptionMenu(finner, values=["Tất cả", "NB", "TH", "VD", "VDC"],
                            variable=self._level_var, width=100,
                            command=lambda _: self._render_table()
                            ).grid(row=0, column=5, padx=(0, 12))

        self._count_lbl = ctk.CTkLabel(finner, text="  ⏳ Đang tải NHCH…",
                                          text_color="gray")
        self._count_lbl.grid(row=0, column=6, padx=(12, 0))

        # ── Table (ttk.Treeview — tốt hơn CTk table cho danh sách lớn) ─
        table_wrap = ctk.CTkFrame(self._scroll, fg_color=("white", "#293548"),
                                     corner_radius=8, border_width=1,
                                     border_color=("#E5E7EB", "#334155"))
        table_wrap.pack(fill="x", pady=(0, 8))

        style = ttk.Style()
        if ctk.get_appearance_mode().lower() == "dark":
            style.theme_use("clam")
            style.configure("Treeview", background="#293548",
                            foreground="#F1F5F9",
                            fieldbackground="#293548",
                            rowheight=26)
            style.configure("Treeview.Heading",
                            background="#1F2937", foreground="#F1F5F9")

        cols = ("pick", "qid", "qtype", "level", "topic", "preview", "answer")
        self._tree = ttk.Treeview(table_wrap, columns=cols,
                                     show="headings", height=10,
                                     selectmode="extended")
        widths = {"pick": 46, "qid": 140, "qtype": 60, "level": 50,
                  "topic": 160, "preview": 480, "answer": 90}
        minwidths = {"pick": 44, "qid": 120, "qtype": 58, "level": 50,
                     "topic": 130, "preview": 280, "answer": 78}
        labels = {"pick": "☑", "qid": "QID", "qtype": "Loại", "level": "Mức",
                  "topic": "Chủ đề", "preview": "Câu hỏi (preview)",
                  "answer": "Đáp án"}
        for c in cols:
            if c == "pick":
                self._tree.heading(c, text=labels[c],
                                   command=self._toggle_visible_checks)
            else:
                self._tree.heading(c, text=labels[c])
            anchor = "center" if c in ("pick", "qtype", "level") else "w"
            self._tree.column(c, width=widths[c], minwidth=minwidths[c],
                              anchor=anchor, stretch=c in ("topic", "preview"))
        vsb = ttk.Scrollbar(table_wrap, orient="vertical",
                              command=self._tree.yview)
        hsb = ttk.Scrollbar(table_wrap, orient="horizontal",
                              command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set,
                              xscrollcommand=hsb.set)
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._tree)
        except Exception: pass
        # Dùng grid để hsb cuộn ngang nằm dưới tree (pack hỗn hợp side=
        # "left"/"right" không cho phép hsb dưới đáy bám đúng).
        for w in (self._tree, vsb, hsb):
            try: w.pack_forget()
            except Exception: pass
        table_wrap.grid_rowconfigure(0, weight=1)
        table_wrap.grid_columnconfigure(0, weight=1)
        self._tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=(8, 0))
        vsb.grid(row=0, column=1, sticky="ns", pady=(8, 0))
        hsb.grid(row=1, column=0, sticky="ew", padx=(8, 0), pady=(0, 8))

        # Click ô đầu tiên → tích chọn; double-click nội dung → sửa câu.
        self._tree.bind("<Button-1>", self._on_tree_click, add="+")
        self._tree.bind("<Double-1>", self._on_dblclick)

        self._selection_lbl = ctk.CTkLabel(
            self._scroll, text="Chưa tích câu nào để thêm vào đề. Bấm ☑ ở tiêu đề để chọn tất cả dòng đang thấy.",
            font=("Segoe UI", 10), text_color="gray", anchor="w")
        self._selection_lbl.pack(anchor="w", pady=(0, 8))

    # ── Actions ───────────────────────────────────────────────────────────
    def _open_import_pdf(self):
        """Mở Import Wizard CTk thuộc workflow V5."""
        def _after_close():
            # Refresh NHCH sau khi wizard đóng (có thể đã thêm câu)
            threading.Thread(target=self._reload_questions, daemon=True).start()
        try:
            from v5.import_wizard import ImportWizardCTk
            dlg = ImportWizardCTk(self.winfo_toplevel(),
                                    subject="Toán", grade="12",
                                    can_use_feature=self._can_use_feature)
            # Refresh table khi wizard đóng
            dlg.bind("<Destroy>", lambda e: _after_close()
                       if e.widget is dlg else None)
        except Exception as e:
            messagebox.showerror("Lỗi Import V5",
                                 f"Không mở được wizard: {e}",
                                 parent=self)

    def _show_recent_menu(self):
        """Popup menu các file đã import gần đây — click để re-open wizard."""
        from v5 import settings_store
        from pathlib import Path
        recent = settings_store.get_recent_files()
        if not recent:
            from v5.toast import show_toast
            show_toast(self.winfo_toplevel(),
                        "Chưa có file import nào gần đây",
                        kind="info"); return

        # tk.Menu popup
        import tkinter as tk
        menu = tk.Menu(self.winfo_toplevel(), tearoff=False)
        for path in recent[:10]:
            name = Path(path).name
            full = path if len(path) <= 60 else "..." + path[-58:]
            menu.add_command(
                label=f"  📄  {name}",
                command=lambda p=path: self._reopen_recent(p))
        menu.add_separator()
        menu.add_command(label="  🗑  Xoá lịch sử",
                          command=self._clear_recent)
        # Hiện menu dưới button
        try:
            x = self._recent_btn.winfo_rootx()
            y = self._recent_btn.winfo_rooty() + self._recent_btn.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _reopen_recent(self, filepath: str):
        """Mở Import Wizard với file đã chọn."""
        from pathlib import Path
        from v5.toast import show_toast
        if not Path(filepath).exists():
            show_toast(self.winfo_toplevel(),
                        f"File không còn: {Path(filepath).name}",
                        kind="error"); return
        # Forward sang app._open_import_for nếu có
        top = self.winfo_toplevel()
        if hasattr(top, "_open_import_for"):
            top._open_import_for(Path(filepath))
        else:
            # Fallback: mở wizard rỗng
            self._open_import_pdf()

    def _clear_recent(self):
        """Xoá toàn bộ recent_files."""
        from v5 import settings_store
        from v5.toast import show_toast
        settings_store.save({"recent_files": []})
        show_toast(self.winfo_toplevel(), "Đã xoá lịch sử recent files",
                    kind="info")

    @staticmethod
    def _question_key(row: dict) -> str:
        bank_id = row.get("_bank_id")
        if bank_id is not None:
            return f"bank:{bank_id}"
        qid = str(row.get("question_id", "") or "").strip()
        if qid:
            return f"qid:{qid}"
        return "|".join((
            str(row.get("qtype", "")),
            str(row.get("topic", "")),
            str(row.get("question", "")),
        ))

    def _on_tree_click(self, event):
        """Bật/tắt dấu tích khi click cột chọn đầu bảng."""
        if self._tree.identify_region(event.x, event.y) != "cell":
            return None
        if self._tree.identify_column(event.x) != "#1":
            return None
        iid = self._tree.identify_row(event.y)
        if iid:
            self._toggle_checked_row(iid)
            return "break"
        return None

    def _toggle_checked_row(self, iid: str):
        row = self._row_questions.get(iid)
        if row is None:
            return
        key = self._question_key(row)
        if key in self._checked_keys:
            self._checked_keys.remove(key)
        else:
            self._checked_keys.add(key)
        values = list(self._tree.item(iid, "values"))
        if values:
            values[0] = "☑" if key in self._checked_keys else "☐"
            self._tree.item(iid, values=values)
        self._on_select_rows()

    def _toggle_visible_checks(self):
        """Click heading ☑ để tích/bỏ tích toàn bộ các dòng đang hiển thị."""
        visible = list(self._row_questions.items())
        if not visible:
            return
        all_checked = all(
            self._question_key(row) in self._checked_keys
            for _iid, row in visible
        )
        for iid, row in visible:
            key = self._question_key(row)
            if all_checked:
                self._checked_keys.discard(key)
            else:
                self._checked_keys.add(key)
            values = list(self._tree.item(iid, "values"))
            values[0] = "☑" if key in self._checked_keys else "☐"
            self._tree.item(iid, values=values)
        self._on_select_rows()

    def _on_dblclick(self, event):
        """Double-click để mở trình sửa câu hỏi V5."""
        if self._tree.identify_column(event.x) == "#1":
            return "break"
        iid = self._tree.identify_row(event.y)
        q_dict = self._row_questions.get(iid)
        if not q_dict:
            return

        # Convert dict → Question object
        try:
            from core.models import Question
            q = self._dict_to_question(q_dict)
        except Exception as e:
            messagebox.showerror("Lỗi convert", str(e), parent=self)
            return

        def _on_save(updated_q):
            # Save lại vào local DB + refresh table
            try:
                self._save_question_to_db(updated_q)
                threading.Thread(target=self._reload_questions, daemon=True).start()
            except Exception as e:
                messagebox.showerror("Lỗi lưu", str(e), parent=self)

        # Lấy get_ai_call cho nút "🤖 AI sửa theo gợi ý"
        get_ai = (
            self._resolve_ai_call()
            if self._feature_allowed("ai_review", notify=False)
            else None
        )

        # Dialog sua cau thuoc V5.
        try:
            from v5.edit_question import EditQuestionDialogCTk
            EditQuestionDialogCTk(self.winfo_toplevel(), q,
                                    on_save_cb=_on_save,
                                    get_ai_call=get_ai,
                                    subject=q.topic or "Toán", grade="12")
        except Exception as e:
            messagebox.showerror("Lỗi mở trình sửa V5",
                                 f"Không mở được trình sửa câu hỏi: {e}",
                                 parent=self)

    def _on_select_rows(self, _event=None):
        count = len(self._checked_keys)
        if count:
            self._selection_lbl.configure(
                text=f"Đã tích {count} câu. Bấm ➕ Thêm vào đề để tiếp tục biên soạn.",
                text_color=("#047857", "#34D399"),
            )
        else:
            self._selection_lbl.configure(
                text="Chưa tích câu nào để thêm vào đề. Bấm ☑ ở tiêu đề để chọn tất cả dòng đang thấy.",
                text_color="gray",
            )

    def _selected_question_dicts(self) -> list[dict]:
        return [
            row for row in self._questions_cache
            if self._question_key(row) in self._checked_keys
        ]

    def _add_selected_to_exam(self):
        selected = self._selected_question_dicts()
        if not selected:
            messagebox.showinfo(
                "Chưa tích câu",
                "Hãy tích ít nhất một câu trong bảng trước khi thêm vào đề.",
                parent=self,
            )
            return
        if not callable(self._on_add_questions):
            messagebox.showwarning(
                "Chưa sẵn sàng",
                "Workspace đề thi chưa sẵn sàng nhận câu hỏi.",
                parent=self,
            )
            return
        questions = [self._dict_to_question(row) for row in selected]
        try:
            from services.tikz_vector_workflow import convert_questions_tikz_to_emf, count_pending_blocks
            if count_pending_blocks(questions) > 0:
                convert_questions_tikz_to_emf(questions)
        except Exception:
            pass
        metadata = {
            "subject": selected[0].get("subject", "Toán"),
            "grade": selected[0].get("grade", "12"),
        }
        self._on_add_questions(questions, metadata)

    @staticmethod
    def _dict_to_question(d: dict):
        """Convert NHCH dict → Question object (đầy đủ field cho dialog sửa).

        Map cả items/answers (DS), images, item_solutions — nếu thiếu thì
        sửa câu DS/có-ảnh sẽ mất dữ liệu.
        """
        from core.models import Question
        q = Question(
            qtype=d.get("qtype", "TN"),
            level=d.get("level", "TH"),
            topic=d.get("topic", ""),
            question=d.get("question", ""),
            options=d.get("options") or d.get("options_json") or {},
            answer=d.get("answer", ""),
            solution=d.get("solution", ""),
            points=float(d.get("points", 1.0) or 1.0),
        )
        q.question_id = d.get("question_id") or q.question_id
        # DS items + answers
        q.items   = d.get("items", {}) or {}
        q.answers = d.get("answers", {}) or {}
        q.item_solutions = d.get("item_solutions", {}) or {}
        # Images (đề / lời giải / option / item)
        q.question_image = d.get("question_image", "") or ""
        q.solution_image = d.get("solution_image", "") or ""
        q.option_images  = d.get("option_images", {}) or {}
        q.item_images    = d.get("item_images", {}) or {}
        return q

    def _detect_ai_provider(self) -> str:
        try:
            from services.key_manager import get_key_manager
            km = get_key_manager()
            for provider in AI_PROVIDERS:
                if km.load(provider):
                    return provider
        except Exception:
            pass
        return "Google Gemini"

    @staticmethod
    def _ai_model_options(provider: str) -> list[str]:
        return AI_MODEL_OPTIONS.get(provider) or [AI_MODEL_DEFAULT.get(provider, "gemini-3.8-flash")]

    def _on_ai_provider_change(self, provider: str) -> None:
        values = self._ai_model_options(provider)
        if hasattr(self, "_ai_model_menu"):
            self._ai_model_menu.configure(values=values)
        self._ai_model_var.set(AI_MODEL_DEFAULT.get(provider, values[0]))

    def _resolve_ai_call(self):
        """Build AI call from the selected NHCH provider/model."""
        try:
            from services.key_manager import get_key_manager
            from services.ai_service import create_ai_service
            from services.retry_service import split_keys
            km = get_key_manager()
            prov = self._ai_provider_var.get() if hasattr(self, "_ai_provider_var") else self._detect_ai_provider()
            model = self._ai_model_var.get() if hasattr(self, "_ai_model_var") else AI_MODEL_DEFAULT.get(prov, "gemini-3.8-flash")
            key = km.load(prov)
            if key or prov == "9Router":
                keys = (key if isinstance(key, list) else split_keys(key)) if key else ["dummy_key"]
                svc = create_ai_service(prov, keys, model)
                return lambda: svc.generate
        except Exception: pass
        return None

    @staticmethod
    def _save_question_to_db(q):
        """Lưu Question đã edit vào SQLite local (upsert qua database.save_questions)."""
        try:
            from storage.database import save_questions
            save_questions([q], subject="Toán", grade="12",
                            source="v5_edit")
        except Exception as e:
            raise

    def open_stats(self):
        """Mở dialog 📊 Thống kê ngân hàng câu hỏi (CTk-native)."""
        try:
            from v5.nhch_stats import NHCHStatsDialog
            NHCHStatsDialog(self.winfo_toplevel())
        except Exception as e:
            messagebox.showerror("Lỗi mở Thống kê",
                                   f"{type(e).__name__}: {e}",
                                   parent=self.winfo_toplevel())

    def _feature_allowed(self, feature: str, *, notify: bool = True) -> bool:
        if not callable(self._can_use_feature):
            return True
        try:
            return bool(self._can_use_feature(feature, notify=notify))
        except TypeError:
            return bool(self._can_use_feature(feature))

    def apply_feature_gates(self, features: dict[str, bool]) -> None:
        unlocked = features.get("nhch_cloud", True)
        self._upload_btn.configure(
            text="☁  Sync ↑ Cloud" if unlocked else "🔒  Sync ↑ Cloud")
        self._download_btn.configure(
            text="☁  Tải ↓ Cloud" if unlocked else "🔒  Tải ↓ Cloud")

    def _sync_to_cloud(self):
        if not self._feature_allowed("nhch_cloud"):
            return
        if not self._questions_cache:
            messagebox.showwarning("Trống", "NHCH local trống.", parent=self)
            return
        if not messagebox.askyesno("Xác nhận",
            f"Push {len(self._questions_cache)} câu lên Cloud?\n\n"
            f"(Câu trùng question_id sẽ bị bỏ qua)", parent=self):
            return

        def _do():
            try:
                from services.license_manager import (
                    nhch_upload_batch, get_machine_id)
                res = nhch_upload_batch(self._questions_cache,
                                          get_machine_id(),
                                          uploader_name="v5 desktop")
                self.after(0, lambda: messagebox.showinfo(
                    "Sync xong",
                    f"✓ {res.get('added', 0)} thêm mới\n"
                    f"⏭ {res.get('skipped', 0)} bỏ qua trùng",
                    parent=self))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Lỗi sync", str(e), parent=self))
        threading.Thread(target=_do, daemon=True).start()

    def _download_from_cloud(self):
        """Tải NHCH từ Cloud (Supabase) → lưu vào local (Alpha 11)."""
        if not self._feature_allowed("nhch_cloud"):
            return
        if not messagebox.askyesno(
            "Tải NHCH từ Cloud",
            "Tải câu hỏi từ Cloud về NHCH local?\n\n"
            "(Tối đa 200 câu mỗi lần · câu trùng question_id sẽ ghi đè)",
            parent=self):
            return

        def _do():
            try:
                from services.license_manager import nhch_list
                from core.models import Question
                from storage.database import save_questions
                cloud = nhch_list(limit=200) or []
                if not cloud:
                    self.after(0, lambda: messagebox.showinfo(
                        "Trống", "Cloud không có câu nào (hoặc chưa đăng nhập).",
                        parent=self))
                    return
                # Convert dict → Question (đầy đủ field như _dict_to_question)
                qs = [self._dict_to_question(d) for d in cloud]
                n = save_questions(qs, subject="Toán", grade="12",
                                     source="cloud_download")
                self.after(0, lambda: self._on_download_done(n, len(cloud)))
            except Exception as e:
                err = str(e)
                self.after(0, lambda: messagebox.showerror(
                    "Lỗi tải Cloud", err[:300], parent=self))

        threading.Thread(target=_do, daemon=True).start()

    def _on_download_done(self, saved: int, total: int):
        from v5.toast import show_toast
        show_toast(self.winfo_toplevel(),
                    f"✓ Đã tải {saved}/{total} câu từ Cloud về local",
                    kind="success", duration=5)
        threading.Thread(target=self._reload_questions, daemon=True).start()

    # ── Data ──────────────────────────────────────────────────────────────
    def _reload_questions(self):
        try:
            self._questions_cache = list_all_questions() or []
            valid_keys = {
                self._question_key(row) for row in self._questions_cache
            }
            self._checked_keys.intersection_update(valid_keys)
        except Exception as e:
            self._questions_cache = []
            self._checked_keys.clear()
            print(f"Load NHCH lỗi: {e}")
        from v5.safe_ui import safe_after
        safe_after(self, 0, self._render_table)

    def _debounced_search(self):
        """Huỷ job render đang chờ, lên lịch lại sau 250ms (debounce)."""
        if self._search_after_id is not None:
            try: self.after_cancel(self._search_after_id)
            except Exception: pass
        self._search_after_id = self.after(250, self._render_table)

    def _render_table(self):
        self._search_after_id = None
        # Guard: view có thể đã destroy khi reload thread gọi after(0)
        try:
            if not self.winfo_exists(): return
        except Exception: return
        # Clear
        self._tree.delete(*self._tree.get_children())
        self._row_questions = {}

        kw    = (self._search_var.get() or "").lower().strip()
        qtype = self._qtype_var.get()
        level = self._level_var.get()

        _RENDER_CAP = 500   # tránh insert hàng nghìn row → UI freeze
        shown = 0; matched = 0; capped = False
        for q in self._questions_cache:
            if qtype != "Tất cả" and q.get("qtype") != qtype:
                continue
            if level != "Tất cả" and q.get("level") != level:
                continue
            if kw:
                blob = f"{q.get('question_id','')} {q.get('topic','')} {q.get('question','')}".lower()
                if kw not in blob:
                    continue
            matched += 1
            if shown >= _RENDER_CAP:
                capped = True
                continue   # vẫn đếm matched nhưng không render thêm
            preview = (q.get("question", "") or "").replace("\n", " ")[:120]
            from v5.tree_style import zebra_tag
            key = self._question_key(q)
            iid = self._tree.insert("", "end", values=(
                "☑" if key in self._checked_keys else "☐",
                q.get("question_id", ""), q.get("qtype", ""),
                q.get("level", ""), q.get("topic", "")[:25],
                preview, (q.get("answer", "") or "")[:20]
            ), tags=(zebra_tag(shown),))
            self._row_questions[iid] = q
            shown += 1
        self._on_select_rows()

        total = len(self._questions_cache)
        # Empty state context-aware
        if total == 0:
            self._count_lbl.configure(
                text="  📭 NHCH trống — Import PDF/Word/Ảnh hoặc Tạo đề "
                     "rồi push để thêm câu",
                text_color=("#92400E", "#FCD34D"))
        elif matched == 0:
            self._count_lbl.configure(
                text=f"  🔍 Không có câu khớp bộ lọc (tổng {total:,} câu)",
                text_color=("#DC2626", "#F87171"))
        elif capped:
            self._count_lbl.configure(
                text=f"  Hiển thị {shown:,} đầu / {matched:,} khớp "
                     f"(tổng {total:,}) — gõ từ khoá để lọc hẹp hơn",
                text_color=("#F59E0B", "#FBBF24"))
        else:
            self._count_lbl.configure(
                text=f"  Hiển thị {shown:,} / {total:,} câu",
                text_color=("#4B5563", "#CBD5E1"))
