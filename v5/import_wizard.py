"""
v5/import_wizard.py — Import PDF/Word/Ảnh → NHCH bằng CustomTkinter (Alpha 11).

Thay thế ui/dialog_import_pdf.py (Tkinter v4). Reuse core pipeline:
    core.pdf_to_questions.pdf_or_image_to_questions  (AI Vision OCR)
    core.pdf_to_questions.questions_to_nhch_rows
    services.ai_service.create_ai_service (.generate_with_image)

Luồng (1 dialog, cuộn dọc):
    1. File info (PDF trang / ảnh / Word)
    2. Tuỳ chọn: provider/model, lọc loại câu, tự giải, dùng text-layer, max trang
    3. [▶ Trích xuất] → progress → AI Vision đọc câu
    4. Preview danh sách câu
    5. [💾 Lưu NHCH local] + [☁ Push Cloud] (tuỳ chọn)
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk
from tkinter import messagebox, ttk

from v5.ui_perf import UiThrottle
from v5.ui_theme import UI_COLORS

QTYPE_FILTERS = ["auto", "TN", "DS", "TLN", "TL"]
PROVIDERS = ["Google Gemini", "Anthropic Claude", "OpenAI"]
_MODEL_DEFAULT = {
    "Google Gemini":    "gemini-3.8-flash",
    "Anthropic Claude": "claude-sonnet-4-5",
    "OpenAI":           "gpt-4o",
}
_MODEL_OPTIONS = {
    "Google Gemini": [
        "gemini-3.8-flash",
        "gemini-3.1-pro",
        "gemini-3.8-live",
        "gemini-3.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
    ],
    "Anthropic Claude": ["claude-sonnet-4-5", "claude-opus-4-1", "claude-haiku-4-5"],
    "OpenAI": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"],
}


class ImportWizardCTk(ctk.CTkToplevel):
    """Dialog import PDF/Word/Ảnh → NHCH (thuần CTk)."""

    def __init__(self, parent, filepath: str = "", *,
                  subject: str = "Toán", grade: str = "12",
                  can_use_feature: Callable[..., bool] | None = None):
        super().__init__(parent)
        self._filepath = filepath
        self._subject = subject
        self._grade = grade
        self._can_use_feature = can_use_feature
        self._questions: list = []
        self._meta: dict = {}
        self._cancel = threading.Event()

        self.title("📥 Import PDF/Word/Ảnh → NHCH")
        try:
            sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
            w = min(900, int(sw * 0.8)); h = min(820, int(sh * 0.9))
            self.geometry(f"{w}x{h}+{(sw-w)//2}+{max(0,(sh-h)//2-20)}")
        except Exception:
            self.geometry("900x800")
        self.minsize(760, 600)

        self._build()
        self.bind("<Escape>", lambda e: self._on_close())
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        try: self.grab_set(); self.focus_force()
        except Exception: pass
        if filepath:
            self._refresh_file_info()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=("#1F497D", "#0B1F35"),
                             corner_radius=0, height=46)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="📥  Import → NHCH (AI Vision OCR)",
                      font=("Segoe UI", 15, "bold"), text_color="white"
                      ).pack(side="left", padx=14, pady=8)

        self._footer = ctk.CTkFrame(
            self, fg_color=UI_COLORS["surface_alt"], corner_radius=0,
            border_width=1, border_color=UI_COLORS["border"])
        self._footer.pack(fill="x", side="bottom")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=8)

        # 1. File
        f_card = self._card(body, "1️⃣  File nguồn")
        frow = ctk.CTkFrame(f_card, fg_color="transparent")
        frow.pack(fill="x")
        self._file_var = ctk.StringVar(value=self._filepath or "(chưa chọn)")
        ctk.CTkEntry(frow, textvariable=self._file_var, state="readonly"
                      ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(frow, text="📂 Chọn", width=90,
                        command=self._pick_file).pack(side="left")
        self._file_info = ctk.CTkLabel(f_card, text="", text_color="gray",
                                          font=("Segoe UI", 10), anchor="w")
        self._file_info.pack(fill="x", pady=(4, 0))

        # 2. Options
        o_card = self._card(body, "2️⃣  Tuỳ chọn trích xuất")
        opt_grid = ctk.CTkFrame(o_card, fg_color="transparent")
        opt_grid.pack(fill="x", pady=2)
        opt_grid.grid_columnconfigure(1, weight=1)
        opt_grid.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(opt_grid, text="AI:", width=40, anchor="w").grid(
            row=0, column=0, padx=(0, 6), pady=3, sticky="w")
        self._provider_var = ctk.StringVar(value=self._detect_provider())
        ctk.CTkOptionMenu(opt_grid, values=PROVIDERS, variable=self._provider_var,
                            width=160, command=self._on_provider_change
                            ).grid(row=0, column=1, padx=(0, 12), pady=3, sticky="w")
        ctk.CTkLabel(opt_grid, text="Model:", width=58, anchor="w").grid(
            row=0, column=2, padx=(0, 6), pady=3, sticky="w")
        self._model_var = ctk.StringVar(
            value=_MODEL_DEFAULT.get(self._provider_var.get(), "gemini-3.8-flash"))
        self._model_menu = ctk.CTkOptionMenu(
            opt_grid,
            values=self._model_options(self._provider_var.get()),
            variable=self._model_var,
            width=190,
        )
        self._model_menu.grid(row=0, column=3, padx=(0, 0), pady=3, sticky="w")

        ctk.CTkLabel(opt_grid, text="Lọc loại:", width=70, anchor="w").grid(
            row=1, column=0, padx=(0, 6), pady=3, sticky="w")
        self._qtype_var = ctk.StringVar(value="auto")
        ctk.CTkOptionMenu(opt_grid, values=QTYPE_FILTERS, variable=self._qtype_var,
                            width=90).grid(row=1, column=1, padx=(0, 12), pady=3, sticky="w")
        ctk.CTkLabel(opt_grid, text="Max trang:", width=80, anchor="w").grid(
            row=1, column=2, padx=(0, 6), pady=3, sticky="w")
        self._maxpages_var = ctk.StringVar(value="50")
        ctk.CTkEntry(opt_grid, textvariable=self._maxpages_var, width=70).grid(
            row=1, column=3, pady=3, sticky="w")

        self._autosolve_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opt_grid, text="Tự giải (AI giải + điền đáp án)",
                          variable=self._autosolve_var).grid(
                              row=2, column=0, columnspan=2,
                              padx=(0, 16), pady=(5, 1), sticky="w")
        self._textlayer_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opt_grid, text="Ưu tiên text-layer (PDF số)",
                          variable=self._textlayer_var).grid(
                              row=2, column=2, columnspan=2,
                              pady=(5, 1), sticky="w")

        # 3. Run
        run_row = ctk.CTkFrame(body, fg_color="transparent")
        run_row.pack(fill="x", pady=(4, 6))
        self._run_btn = ctk.CTkButton(
            run_row, text="▶  Trích xuất câu hỏi", height=38,
            font=("Segoe UI", 13, "bold"),
            fg_color=("#10B981", "#065F46"), hover_color=("#059669", "#047857"),
            command=self._on_run)
        self._run_btn.pack(side="left", padx=(0, 6))
        self._cancel_btn = ctk.CTkButton(
            run_row, text="⛔ Dừng", width=90, height=38, state="disabled",
            fg_color=("#DC2626", "#7F1D1D"), command=lambda: self._cancel.set())
        self._cancel_btn.pack(side="left")

        self._prog = ctk.CTkProgressBar(body); self._prog.set(0)
        self._prog.pack(fill="x", pady=(0, 2))
        self._prog_lbl = ctk.CTkLabel(body, text="", text_color="gray",
                                        font=("Segoe UI", 10), anchor="w")
        self._prog_lbl.pack(fill="x")

        # 4. Preview
        p_card = self._card(body, "4️⃣  Câu trích được", expand=True)
        pv = ctk.CTkFrame(p_card, fg_color=("white", "#1E293B"))
        pv.pack(fill="both", expand=True)
        cols = ("no", "qtype", "level", "preview")
        self._tree = ttk.Treeview(pv, columns=cols, show="headings", height=8)
        preview_widths = {"no": 40, "qtype": 70, "level": 62, "preview": 620}
        preview_minwidths = {"no": 36, "qtype": 62, "level": 56, "preview": 320}
        preview_labels = {"no": "#", "qtype": "Loại", "level": "Mức", "preview": "Nội dung"}
        for c in cols:
            l = preview_labels[c]
            self._tree.heading(c, text=l)
            self._tree.column(c, width=preview_widths[c],
                                  minwidth=preview_minwidths[c],
                                  stretch=(c == "preview"),
                                  anchor=("w" if c == "preview" else "center"))
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._tree)
        except Exception: pass
        # Alpha 21: HSB + grid layout
        vsb = ttk.Scrollbar(pv, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(pv, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set,
                                xscrollcommand=hsb.set)
        pv.grid_rowconfigure(0, weight=1)
        pv.grid_columnconfigure(0, weight=1)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # 5. Save
        save_row = ctk.CTkFrame(self._footer, fg_color="transparent")
        save_row.pack(fill="x", padx=10, pady=10)
        save_row.grid_columnconfigure(2, weight=1)
        self._save_btn = ctk.CTkButton(
            save_row, text="💾 Lưu vào NHCH local", height=38, state="disabled",
            fg_color="#3B82F6", hover_color="#2563EB", command=self._save_local)
        self._save_btn.grid(row=0, column=0, sticky="w", padx=(0, 6))
        self._push_btn = ctk.CTkButton(
            save_row, text="☁ Push lên Cloud", height=38, state="disabled",
            fg_color=("#A78BFA", "#5B21B6"), hover_color=("#8B5CF6", "#4C1D95"),
            command=self._push_cloud)
        self._push_btn.grid(row=0, column=1, sticky="w", padx=2)
        ctk.CTkButton(save_row, text="Đóng", height=38, width=90,
                        fg_color=("#6B7280", "#374151"),
                        command=self._on_close).grid(row=0, column=3, sticky="e")

    # ── Helpers ──────────────────────────────────────────────────────────
    def _card(self, parent, title, *, expand: bool = False):
        outer = ctk.CTkFrame(parent, fg_color=("white", "#162033"),
                               corner_radius=8)
        outer.pack(fill=("both" if expand else "x"), expand=expand, pady=(0, 8))
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)
        ctk.CTkLabel(inner, text=title, font=("Segoe UI", 12, "bold"),
                      anchor="w").pack(fill="x", pady=(0, 6))
        return inner

    def _detect_provider(self) -> str:
        try:
            from services.key_manager import get_key_manager
            km = get_key_manager()
            for p in PROVIDERS:
                if km.load(p): return p
        except Exception: pass
        return "Google Gemini"

    def _on_provider_change(self, prov):
        values = self._model_options(prov)
        if hasattr(self, "_model_menu"):
            self._model_menu.configure(values=values)
        self._model_var.set(_MODEL_DEFAULT.get(prov, values[0]))

    @staticmethod
    def _model_options(prov: str) -> list[str]:
        return _MODEL_OPTIONS.get(prov) or [_MODEL_DEFAULT.get(prov, "gemini-3.8-flash")]

    def _feature_allowed(self, feature: str, *, notify: bool = True) -> bool:
        if not callable(self._can_use_feature):
            return True
        try:
            return bool(self._can_use_feature(feature, notify=notify))
        except TypeError:
            return bool(self._can_use_feature(feature))

    def _pick_file(self):
        from tkinter import filedialog
        p = filedialog.askopenfilename(
            parent=self, title="Chọn PDF/Word/Ảnh",
            filetypes=[("Hỗ trợ", "*.pdf *.docx *.png *.jpg *.jpeg *.webp"),
                        ("PDF", "*.pdf"), ("Word", "*.docx"),
                        ("Ảnh", "*.png *.jpg *.jpeg *.webp")])
        if p:
            self._filepath = p
            self._file_var.set(p)
            self._refresh_file_info()

    def _refresh_file_info(self):
        p = Path(self._filepath)
        if not p.exists():
            self._file_info.configure(text="(file không tồn tại)")
            return
        ext = p.suffix.lower()
        size_kb = p.stat().st_size / 1024
        if ext == ".pdf":
            try:
                import fitz
                d = fitz.open(str(p)); n = len(d); d.close()
                self._file_info.configure(
                    text=f"PDF • {n} trang • {size_kb:.0f} KB",
                    text_color=("#1F497D", "#60A5FA"))
            except Exception:
                self._file_info.configure(text=f"PDF • {size_kb:.0f} KB")
        else:
            self._file_info.configure(
                text=f"{ext.upper()[1:]} • {size_kb:.0f} KB",
                text_color=("#1F497D", "#60A5FA"))

    def _resolve_keys(self) -> list[str]:
        try:
            from services.key_manager import get_key_manager
            from services.retry_service import split_keys
            km = get_key_manager()
            k = km.load(self._provider_var.get())
            if k: return k if isinstance(k, list) else split_keys(k)
        except Exception: pass
        return []

    # ── Run extraction ─────────────────────────────────────────────────────
    def _on_run(self):
        if not self._filepath or not Path(self._filepath).exists():
            messagebox.showwarning("Thiếu file", "Hãy chọn file trước.",
                                     parent=self); return
        keys = self._resolve_keys()
        if not keys:
            messagebox.showwarning(
                "Thiếu API key",
                f"Chưa có key cho {self._provider_var.get()}. "
                f"Vào ⚙️ Cấu hình nhập key.", parent=self); return

        self._cancel.clear()
        self._run_btn.configure(state="disabled", text="⏳ Đang xử lý…")
        self._cancel_btn.configure(state="normal")
        self._save_btn.configure(state="disabled")
        self._push_btn.configure(state="disabled")
        self._tree.delete(*self._tree.get_children())
        self._prog.set(0)

        try: max_pages = int(self._maxpages_var.get())
        except Exception: max_pages = 50
        progress_throttle = UiThrottle(self, 80)

        def _worker():
            try:
                from services.ai_service import create_ai_service
                from core.pdf_to_questions import pdf_or_image_to_questions
                ai = create_ai_service(self._provider_var.get(), keys,
                                         self._model_var.get())

                def _progress(i, n, msg):
                    if self._cancel.is_set():
                        raise InterruptedError("cancel")
                    progress_throttle.schedule(self._set_progress, i, n, msg)

                res = pdf_or_image_to_questions(
                    self._filepath,
                    ai_vision_call=ai.generate_with_image,
                    ai_text_call=ai.generate if self._autosolve_var.get() else None,
                    auto_solve=self._autosolve_var.get(),
                    progress_cb=_progress,
                    qtype_filter=self._qtype_var.get(),
                    use_text_layer=self._textlayer_var.get(),
                    max_pages=max_pages)
                self.after(0, lambda: (
                    progress_throttle.cancel(),
                    self._on_extract_done(res, None)))
            except InterruptedError:
                self.after(0, lambda: (
                    progress_throttle.cancel(),
                    self._on_extract_done(None, "Đã dừng")))
            except Exception as e:
                err = str(e)
                self.after(0, lambda: (
                    progress_throttle.cancel(),
                    self._on_extract_done(None, err)))

        threading.Thread(target=_worker, daemon=True).start()

    def _set_progress(self, i, n, msg):
        try:
            if not self.winfo_exists(): return
            self._prog.set(i / max(n, 1))
            self._prog_lbl.configure(text=f"  {i}/{n}  {msg[:60]}")
        except Exception: pass

    def _on_extract_done(self, res, err):
        try:
            if not self.winfo_exists(): return
        except Exception: return
        self._run_btn.configure(state="normal", text="▶  Trích xuất câu hỏi")
        self._cancel_btn.configure(state="disabled")
        if err:
            self._prog_lbl.configure(text=f"✘ {err[:70]}", text_color="#EF4444")
            return
        self._questions = res.get("questions", []) or []
        self._meta = res.get("meta", {}) or {}
        n = len(self._questions)
        self._prog.set(1.0)
        self._prog_lbl.configure(
            text=f"✓ Trích được {n} câu", text_color="#10B981")
        from v5.tree_style import zebra_tag
        for i, q in enumerate(self._questions, 1):
            preview = (getattr(q, "question", "") or "").replace("\n", " ")[:120]
            self._tree.insert("", "end", values=(
                i, getattr(q, "qtype", "?"), getattr(q, "level", "?"), preview),
                tags=(zebra_tag(i),))
        if n > 0:
            self._save_btn.configure(state="normal")
            self._push_btn.configure(state="normal")
            if not self._feature_allowed("nhch_cloud", notify=False):
                self._push_btn.configure(text="🔒 Push lên Cloud")

    # ── Save ─────────────────────────────────────────────────────────────
    def _save_local(self):
        if not self._questions:
            return
        try:
            # Gán structured ID cho câu chưa có (nhất quán hệ ID 12D1T1-0001)
            try:
                from core.models import compute_structured_id
                seen = set()
                for q in self._questions:
                    if not (getattr(q, "question_id", "") or "").strip():
                        q.question_id = compute_structured_id(
                            q, str(self._grade), existing_qids=seen)
                    seen.add(q.question_id)
            except Exception: pass

            from storage.database import save_questions
            n = save_questions(self._questions, subject=self._subject,
                                 grade=self._grade, source="import_v5")
            from v5.toast import show_toast
            show_toast(self.master, f"✓ Đã lưu {n} câu vào NHCH local",
                        kind="success", duration=5)
            self._prog_lbl.configure(text=f"✓ Đã lưu {n} câu local",
                                       text_color="#10B981")
        except Exception as e:
            messagebox.showerror("Lỗi lưu", str(e)[:300], parent=self)

    def _push_cloud(self):
        if not self._feature_allowed("nhch_cloud"):
            return
        if not self._questions:
            return
        self._push_btn.configure(state="disabled", text="⏳ Đang push…")

        def _do():
            try:
                from core.pdf_to_questions import questions_to_nhch_rows
                from services.license_manager import (nhch_upload_batch,
                                                       get_machine_id)
                rows = questions_to_nhch_rows(
                    self._questions, self._meta,
                    id_prefix="PDF", source_file=self._filepath or "")
                res = nhch_upload_batch(rows, get_machine_id(),
                                          uploader_name="v5 Import Wizard")
                self.after(0, lambda: self._on_push_done(res, None))
            except Exception as e:
                err = str(e)
                self.after(0, lambda: self._on_push_done(None, err))

        threading.Thread(target=_do, daemon=True).start()

    def _on_push_done(self, res, err):
        try:
            if not self.winfo_exists(): return
        except Exception: return
        self._push_btn.configure(state="normal", text="☁ Push lên Cloud")
        if err:
            messagebox.showerror("Push thất bại", err[:300], parent=self)
            return
        if res and res.get("ok"):
            added = res.get("added", 0); skipped = res.get("skipped", 0)
            from v5.toast import show_toast
            show_toast(self.master,
                        f"✓ Push {added} câu lên Cloud (bỏ {skipped} trùng)",
                        kind="success", duration=5)
            self._prog_lbl.configure(
                text=f"✓ Cloud: +{added} • bỏ {skipped} trùng",
                text_color="#10B981")
        else:
            messagebox.showerror("Push thất bại",
                                  (res or {}).get("error", "?"), parent=self)

    def _on_close(self):
        self._cancel.set()
        try: self.grab_release()
        except Exception: pass
        try: self.destroy()
        except Exception: pass
