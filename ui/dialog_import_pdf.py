"""
ui/dialog_import_pdf.py — Wizard "Import đề thi từ PDF/Word/Ảnh → NHCH".

Luồng UX:
    1. Chọn file (.pdf / .docx / .png / .jpg / ...)
    2. Chọn AI provider + model + tuỳ chọn auto-solve
    3. Bấm "Bắt đầu" → progress bar realtime (per page)
    4. Xem preview table → tick chọn câu → tuỳ chỉnh → push NHCH

Tích hợp:
    from ui.dialog_import_pdf import open_import_pdf_dialog
    open_import_pdf_dialog(parent_window, subject="Toán", grade="12")
"""
from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable, Optional

from core.pdf_to_questions import (
    pdf_or_image_to_questions,
    questions_to_nhch_rows,
    IMAGE_EXTS, PDF_EXTS, DOC_EXTS,
)

BLUE   = "#1F497D"
GREEN  = "#10B981"
RED    = "#EF4444"
GRAY   = "#6B7280"
BG     = "#F9F7F4"
SURF   = "#FFFFFF"


class ImportPdfDialog(tk.Toplevel):
    """Dialog wizard import PDF → NHCH."""

    SUPPORTED_EXTS = sorted(IMAGE_EXTS | PDF_EXTS | DOC_EXTS)

    # Provider name PHẢI khớp với services.ai_service.create_ai_service():
    #   "Google Gemini" | "Anthropic Claude" | "DeepSeek"
    PROVIDERS = [
        ("Google Gemini",    ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]),
        ("Anthropic Claude", ["claude-sonnet-4-5", "claude-sonnet-4-6"]),
        ("DeepSeek",         ["deepseek-chat", "deepseek-reasoner"]),
    ]

    def __init__(self, parent, *, subject: str = "Toán", grade: str = "12",
                 default_provider: str = "Google Gemini",
                 tab_config=None):
        super().__init__(parent)
        try:
            from ui import set_dialog_icon
            set_dialog_icon(self)
        except Exception:
            pass

        self.title("📄  Import đề thi từ PDF / Word / Ảnh")
        self.geometry("1100x760")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.grab_set()

        self._subject = subject
        self._grade   = grade
        self._default_provider = default_provider
        # Reference tới TabConfig của main window — để LẤY THẲNG provider/key/model
        # đã chọn (thay vì user phải chọn lại + check KeyManager thủ công).
        self._tab_config = tab_config or self._find_tab_config(parent)

        # State
        self._filepath:    Optional[str]  = None
        self._questions:   list           = []
        self._meta:        dict           = {}
        self._worker:      Optional[threading.Thread] = None
        self._cancel_flag: threading.Event = threading.Event()

        self._build()
        # Pre-fill provider/model từ tab Cài đặt (nếu có)
        self._sync_from_tab_config()

    @staticmethod
    def _find_tab_config(parent):
        """Tìm `tab_config` từ cây widget (parent thường là MainWindow)."""
        try:
            top = parent.winfo_toplevel()
            return getattr(top, "_tab_config", None)
        except Exception:
            return None

    def _sync_from_tab_config(self):
        """Đồng bộ provider/model từ tab Cài đặt đã chọn."""
        if not self._tab_config:
            return
        try:
            prov = self._tab_config.get_provider()
            if prov:
                self._provider_var.set(prov)
                self._on_provider_change()
            model = self._tab_config.get_model()
            if model:
                self._model_var.set(model)
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────
    #  BUILD UI
    # ──────────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BLUE)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  📄  Import đề thi → Ngân hàng câu hỏi",
                 bg=BLUE, fg="white",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=12, pady=8)

        # ── PART 1: File selector ─────────────────────────────────────────
        part1 = tk.LabelFrame(self, text="  Bước 1 — Chọn file  ",
                               bg=BG, font=("Segoe UI", 10, "bold"),
                               fg=BLUE, padx=12, pady=8)
        part1.pack(fill="x", padx=10, pady=(8, 4))

        f1 = tk.Frame(part1, bg=BG); f1.pack(fill="x")
        tk.Label(f1, text="File:", bg=BG, font=("Segoe UI", 10)).pack(side="left")
        self._file_var = tk.StringVar(value="(chưa chọn file)")
        tk.Entry(f1, textvariable=self._file_var, state="readonly",
                 font=("Consolas", 9), width=80).pack(
                     side="left", fill="x", expand=True, padx=6)
        tk.Button(f1, text="📂  Browse…", font=("Segoe UI", 9, "bold"),
                  bg=BLUE, fg="white", relief="flat", cursor="hand2",
                  padx=10, pady=2, command=self._pick_file).pack(side="left")

        self._file_info = tk.Label(
            part1, text="Hỗ trợ: " + ", ".join(self.SUPPORTED_EXTS),
            fg=GRAY, bg=BG, font=("Segoe UI", 8))
        self._file_info.pack(anchor="w", pady=(4, 0))

        # ── PART 2: Settings ──────────────────────────────────────────────
        part2 = tk.LabelFrame(self, text="  Bước 2 — Cài đặt xử lý  ",
                               bg=BG, font=("Segoe UI", 10, "bold"),
                               fg=BLUE, padx=12, pady=8)
        part2.pack(fill="x", padx=10, pady=4)

        s1 = tk.Frame(part2, bg=BG); s1.pack(fill="x")

        # AI Provider + Model
        tk.Label(s1, text="AI Provider:", bg=BG, font=("Segoe UI", 10)
                 ).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
        self._provider_var = tk.StringVar(value=self._default_provider)
        provider_cb = ttk.Combobox(
            s1, textvariable=self._provider_var,
            values=[p[0] for p in self.PROVIDERS],
            state="readonly", width=12, font=("Segoe UI", 10))
        provider_cb.grid(row=0, column=1, sticky="w", padx=(0, 16), pady=2)
        provider_cb.bind("<<ComboboxSelected>>", self._on_provider_change)

        tk.Label(s1, text="Model:", bg=BG, font=("Segoe UI", 10)
                 ).grid(row=0, column=2, sticky="w", padx=(0, 4), pady=2)
        self._model_var = tk.StringVar()
        self._model_cb = ttk.Combobox(
            s1, textvariable=self._model_var,
            state="readonly", width=24, font=("Segoe UI", 10))
        self._model_cb.grid(row=0, column=3, sticky="w", padx=(0, 16), pady=2)
        self._on_provider_change()  # populate models cho provider mặc định

        # Subject + Grade
        tk.Label(s1, text="Môn:", bg=BG, font=("Segoe UI", 10)
                 ).grid(row=1, column=0, sticky="w", padx=(0, 4), pady=2)
        self._subject_var = tk.StringVar(value=self._subject)
        ttk.Combobox(s1, textvariable=self._subject_var,
                     values=["Toán", "Lý", "Hóa", "Sinh", "Văn", "Anh",
                             "Sử", "Địa", "GDCD", "Tin"],
                     width=10, font=("Segoe UI", 10)
                     ).grid(row=1, column=1, sticky="w", padx=(0, 16), pady=2)

        tk.Label(s1, text="Lớp:", bg=BG, font=("Segoe UI", 10)
                 ).grid(row=1, column=2, sticky="w", padx=(0, 4), pady=2)
        self._grade_var = tk.StringVar(value=self._grade)
        ttk.Combobox(s1, textvariable=self._grade_var,
                     values=[str(g) for g in range(6, 13)],
                     width=6, font=("Segoe UI", 10), state="readonly"
                     ).grid(row=1, column=3, sticky="w", padx=(0, 16), pady=2)

        # Options checkboxes
        opt_f = tk.Frame(part2, bg=BG); opt_f.pack(fill="x", pady=(8, 0))
        self._autosolve_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_f, text="🤖  Tự giải đáp án + lời giải còn trống",
                       variable=self._autosolve_var, bg=BG,
                       font=("Segoe UI", 9), cursor="hand2"
                       ).pack(side="left", padx=(0, 16))

        self._use_textlayer_var = tk.BooleanVar(value=True)
        tk.Checkbutton(opt_f, text="⚡  Ưu tiên text-layer (nhanh, miễn phí)",
                       variable=self._use_textlayer_var, bg=BG,
                       font=("Segoe UI", 9), cursor="hand2"
                       ).pack(side="left", padx=(0, 16))

        tk.Label(opt_f, text="Max trang:", bg=BG,
                 font=("Segoe UI", 9)).pack(side="left", padx=(8, 4))
        self._maxpages_var = tk.IntVar(value=20)
        ttk.Spinbox(opt_f, from_=1, to=100, increment=1,
                    textvariable=self._maxpages_var, width=6,
                    font=("Segoe UI", 9)).pack(side="left")

        # ── PART 3: Run + Progress ────────────────────────────────────────
        run_f = tk.Frame(self, bg=BG); run_f.pack(fill="x", padx=10, pady=6)
        self._run_btn = tk.Button(
            run_f, text="▶  Bắt đầu xử lý",
            font=("Segoe UI", 11, "bold"),
            bg=GREEN, fg="white", activebackground="#059669",
            relief="flat", cursor="hand2", padx=20, pady=8,
            command=self._on_run)
        self._run_btn.pack(side="left")

        self._cancel_btn = tk.Button(
            run_f, text="⛔  Dừng",
            font=("Segoe UI", 10), state="disabled",
            bg=RED, fg="white", activebackground="#DC2626",
            relief="flat", cursor="hand2", padx=12, pady=8,
            command=self._on_cancel)
        self._cancel_btn.pack(side="left", padx=4)

        self._prog_lbl = tk.Label(run_f, text="", bg=BG, fg=BLUE,
                                    font=("Segoe UI", 9, "italic"))
        self._prog_lbl.pack(side="left", padx=10)

        self._prog = ttk.Progressbar(self, mode="determinate", length=600)
        self._prog.pack(fill="x", padx=10, pady=(0, 4))

        # ── PART 5: Bottom actions (pack side="bottom" để luôn ghim đáy) ──
        bot = tk.Frame(self, bg=BG)
        bot.pack(side="bottom", fill="x", padx=10, pady=8)

        tk.Button(bot, text="☑ Tick tất cả", font=("Segoe UI", 9),
                  bg=GRAY, fg="white", relief="flat", cursor="hand2",
                  padx=8, pady=4, command=lambda: self._toggle_all(True)
                  ).pack(side="left", padx=2)
        tk.Button(bot, text="☐ Bỏ tick tất cả", font=("Segoe UI", 9),
                  bg=GRAY, fg="white", relief="flat", cursor="hand2",
                  padx=8, pady=4, command=lambda: self._toggle_all(False)
                  ).pack(side="left", padx=2)
        tk.Button(bot, text="🗑️  Xoá câu đã tick", font=("Segoe UI", 9),
                  bg=RED, fg="white", relief="flat", cursor="hand2",
                  padx=8, pady=4, command=self._delete_chosen
                  ).pack(side="left", padx=2)

        self._summary_lbl = tk.Label(bot, text="", bg=BG, fg=BLUE,
                                       font=("Segoe UI", 9, "italic"))
        self._summary_lbl.pack(side="left", padx=12)

        tk.Button(bot, text="  Hủy  ", font=("Segoe UI", 9),
                  bg=GRAY, fg="white", relief="flat", cursor="hand2",
                  padx=12, pady=6, command=self.destroy
                  ).pack(side="right", padx=2)

        self._push_btn = tk.Button(
            bot, text="💾  Đẩy câu đã tick lên NHCH",
            font=("Segoe UI", 10, "bold"),
            bg=BLUE, fg="white", relief="flat", cursor="hand2",
            padx=14, pady=6, state="disabled",
            command=self._on_push_nhch)
        self._push_btn.pack(side="right", padx=4)

        # ── PART 4: Result table (chiếm toàn bộ khoảng trống còn lại) ──
        part4 = tk.LabelFrame(self, text="  Bước 3 — Kết quả (tick để chọn câu push lên NHCH)  ",
                               bg=BG, font=("Segoe UI", 10, "bold"),
                               fg=BLUE, padx=8, pady=4)
        part4.pack(fill="both", expand=True, padx=10, pady=4)

        tbl_wrap = tk.Frame(part4, bg=SURF, relief="solid", bd=1)
        tbl_wrap.pack(fill="both", expand=True)

        cols = ("chosen", "no", "qtype", "level", "topic", "preview", "answer")
        self._tree = ttk.Treeview(tbl_wrap, columns=cols, show="headings",
                                    height=12)
        widths = {"chosen": 50, "no": 40, "qtype": 60, "level": 50,
                  "topic": 160, "preview": 460, "answer": 100}
        labels = {"chosen": "✓", "no": "#", "qtype": "Loại", "level": "Mức",
                  "topic": "Chủ đề", "preview": "Nội dung câu hỏi (preview)",
                  "answer": "Đáp án"}
        for c in cols:
            self._tree.heading(c, text=labels[c])
            anchor = "center" if c in ("chosen", "no", "qtype", "level") else "w"
            self._tree.column(c, width=widths[c], anchor=anchor)

        vsb = ttk.Scrollbar(tbl_wrap, orient="vertical",
                             command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Click vào cột "✓" → toggle chosen
        self._tree.bind("<Button-1>", self._on_tree_click)
        self._tree.bind("<Double-1>", self._on_tree_dblclick)

        # Tag colors theo qtype
        self._tree.tag_configure("TN",  background="#F0F9FF")
        self._tree.tag_configure("DS",  background="#FEF3C7")
        self._tree.tag_configure("TLN", background="#F0FDF4")
        self._tree.tag_configure("TL",  background="#FAE8FF")


    # ──────────────────────────────────────────────────────────────────────
    #  EVENTS
    # ──────────────────────────────────────────────────────────────────────

    def _on_provider_change(self, *_):
        prov = self._provider_var.get()
        models = next((m for p, m in self.PROVIDERS if p == prov), [])
        self._model_cb["values"] = models
        if models:
            self._model_var.set(models[0])

    def _pick_file(self):
        types = [("Đề thi", " ".join(f"*{e}" for e in self.SUPPORTED_EXTS)),
                 ("PDF", "*.pdf"),
                 ("Word", "*.docx"),
                 ("Ảnh", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
                 ("Tất cả", "*.*")]
        path = filedialog.askopenfilename(parent=self, title="Chọn file đề thi",
                                            filetypes=types)
        if not path:
            return
        self._filepath = path
        self._file_var.set(path)

        # Phát hiện loại + số trang
        ext = Path(path).suffix.lower()
        info = f"Loại: {ext}"
        try:
            if ext in PDF_EXTS:
                import fitz
                doc = fitz.open(path); n = len(doc); doc.close()
                info = f"PDF • {n} trang • {Path(path).stat().st_size/1024:.0f} KB"
            elif ext in IMAGE_EXTS:
                info = f"Ảnh • {Path(path).stat().st_size/1024:.0f} KB"
            elif ext in DOC_EXTS:
                info = f"Word document • {Path(path).stat().st_size/1024:.0f} KB"
        except Exception as e:
            info += f" (lỗi đọc metadata: {e})"
        self._file_info.config(text=info, fg=BLUE)

    def _on_run(self):
        if not self._filepath:
            messagebox.showwarning("Thiếu file", "Vui lòng chọn file trước.",
                                    parent=self); return
        if self._worker and self._worker.is_alive():
            return

        # Lấy API keys — ƯU TIÊN từ tab Cài đặt (đã load + decrypt sẵn),
        # fallback KeyManager với cả 2 dạng tên ("Google Gemini" / "Gemini").
        prov = self._provider_var.get()
        api_keys = self._resolve_api_keys(prov)
        if not api_keys:
            messagebox.showerror(
                "Thiếu API key",
                f"Chưa có API key cho {prov}.\n\n"
                f"Mở tab Cài đặt → chọn provider {prov} → "
                f"nhập API key → 💾 Lưu, rồi mở lại dialog này.",
                parent=self)
            return

        # Clear cũ
        self._tree.delete(*self._tree.get_children())
        self._questions = []
        self._meta = {}
        self._cancel_flag.clear()

        self._run_btn.config(state="disabled")
        self._cancel_btn.config(state="normal")
        self._push_btn.config(state="disabled")
        self._prog["value"] = 0

        # Spawn worker
        self._worker = threading.Thread(target=self._do_import,
                                          args=(api_keys,), daemon=True)
        self._worker.start()

    def _resolve_api_keys(self, prov: str) -> list[str]:
        """Lấy API keys từ tab Cài đặt (nếu provider khớp), fallback KeyManager.

        Hỗ trợ cả 2 cách user lưu key:
          1. Qua tab Cài đặt → key_manager → encrypted
          2. Đoán đúng cả khi provider hơi khác tên (Gemini vs Google Gemini)
        """
        # 1. Lấy từ tab Cài đặt nếu provider khớp
        if self._tab_config:
            try:
                cur_prov = self._tab_config.get_provider()
                if cur_prov == prov:
                    keys = self._tab_config.get_api_keys()
                    if keys and keys[0]:
                        return [k for k in keys if k]
            except Exception:
                pass

        # 2. Fallback KeyManager với các biến thể tên
        try:
            from services.key_manager import get_key_manager
            km = get_key_manager()
            for name in self._provider_name_variants(prov):
                k = km.load(name)
                if k:
                    # km.load có thể trả về string (1 key) hoặc list
                    if isinstance(k, str):
                        return [s.strip() for s in k.splitlines() if s.strip()]
                    if isinstance(k, list):
                        return [s for s in k if s]
        except Exception:
            pass
        return []

    @staticmethod
    def _provider_name_variants(prov: str) -> list[str]:
        """Trả các tên có thể của 1 provider để thử load key."""
        prov = prov.strip()
        m = {
            "Google Gemini":    ["Google Gemini", "Gemini", "gemini"],
            "Anthropic Claude": ["Anthropic Claude", "Claude", "claude"],
            "DeepSeek":         ["DeepSeek", "deepseek"],
        }
        return m.get(prov, [prov])

    def _on_cancel(self):
        self._cancel_flag.set()
        self._prog_lbl.config(text="⛔ Đang dừng…", fg=RED)

    # ──────────────────────────────────────────────────────────────────────
    #  WORKER THREAD
    # ──────────────────────────────────────────────────────────────────────

    def _do_import(self, api_keys: list[str]):
        try:
            from services.ai_service import create_ai_service
            prov  = self._provider_var.get()
            model = self._model_var.get()
            ai = create_ai_service(prov, api_keys, model)

            def progress(i, n, msg):
                if self._cancel_flag.is_set():
                    raise InterruptedError("User cancel")
                self.after(0, self._set_progress, i, n, msg)

            res = pdf_or_image_to_questions(
                self._filepath,
                ai_vision_call=ai.generate_with_image,
                ai_text_call=ai.generate if self._autosolve_var.get() else None,
                auto_solve=self._autosolve_var.get(),
                progress_cb=progress,
                use_text_layer=self._use_textlayer_var.get(),
                max_pages=self._maxpages_var.get(),
            )

            self._questions = res["questions"]
            self._meta = res["meta"]
            self.after(0, self._populate_results, res)

        except InterruptedError:
            self.after(0, self._reset_after_run, "⛔ Đã dừng theo yêu cầu", RED)
        except Exception as e:
            err = str(e)[:200]
            self.after(0, lambda: messagebox.showerror(
                "Lỗi xử lý", err, parent=self))
            self.after(0, self._reset_after_run, f"✘ Lỗi: {err[:60]}", RED)

    def _set_progress(self, i: int, n: int, msg: str):
        if n > 0:
            self._prog["maximum"] = n
            self._prog["value"]   = i
        self._prog_lbl.config(text=f"  {msg}", fg=BLUE)

    def _reset_after_run(self, msg: str = "", color: str = BLUE):
        self._run_btn.config(state="normal")
        self._cancel_btn.config(state="disabled")
        if msg:
            self._prog_lbl.config(text=msg, fg=color)

    def _populate_results(self, res: dict):
        questions = res["questions"]
        meta = res["meta"]
        warnings = res.get("warnings", [])

        # Auto-detect môn/lớp nếu user chưa override
        if meta.get("subject") and not self._subject_var.get().strip():
            self._subject_var.set(meta["subject"])
        if meta.get("grade") and not self._grade_var.get().strip():
            self._grade_var.set(meta["grade"])

        for i, q in enumerate(questions, 1):
            preview = (q.question or "").replace("\n", " ")[:120]
            answer = q.answer or ""
            if q.qtype == "DS" and q.answers:
                answer = ",".join(f"{k}={'Đ' if v else 'S'}"
                                   for k, v in q.answers.items())
            self._tree.insert("", "end", iid=str(i), values=(
                "✓", i, q.qtype, q.level, q.topic or "(chưa)",
                preview, answer or "(trống)"
            ), tags=(q.qtype,))

        warn_str = f"  ⚠️ {len(warnings)} cảnh báo" if warnings else ""
        self._summary_lbl.config(
            text=f"✓ {len(questions)} câu • method={res['method']} • "
                  f"pages={res['n_pages']}{warn_str}")
        self._reset_after_run(f"✓ Xong — {len(questions)} câu sẵn sàng", GREEN)
        if questions:
            self._push_btn.config(state="normal")

        if warnings:
            short = "\n".join(warnings[:5])
            if len(warnings) > 5:
                short += f"\n…và {len(warnings)-5} cảnh báo khác"
            messagebox.showwarning("Cảnh báo trong quá trình xử lý",
                                    short, parent=self)

    # ──────────────────────────────────────────────────────────────────────
    #  TABLE INTERACTIONS
    # ──────────────────────────────────────────────────────────────────────

    def _on_tree_click(self, event):
        region = self._tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        col = self._tree.identify_column(event.x)
        if col != "#1":  # chỉ cột "chosen"
            return
        iid = self._tree.identify_row(event.y)
        if not iid:
            return
        vals = list(self._tree.item(iid, "values"))
        vals[0] = "" if vals[0] == "✓" else "✓"
        self._tree.item(iid, values=vals)
        self._update_count_label()

    def _on_tree_dblclick(self, event):
        """Double-click → mở dialog sửa câu (nếu module có sẵn)."""
        iid = self._tree.focus()
        if not iid:
            return
        try:
            idx = int(iid) - 1
            q = self._questions[idx]
        except (ValueError, IndexError):
            return

        # Mở edit dialog nếu có
        try:
            from ui.dialogs_new import EditQuestionDialogV2
            def _on_save(updated_q):
                self._questions[idx] = updated_q
                # Refresh row
                preview = (updated_q.question or "").replace("\n", " ")[:120]
                answer = updated_q.answer or ""
                if updated_q.qtype == "DS" and updated_q.answers:
                    answer = ",".join(f"{k}={'Đ' if v else 'S'}"
                                       for k, v in updated_q.answers.items())
                vals = list(self._tree.item(iid, "values"))
                vals[3] = updated_q.level
                vals[4] = updated_q.topic or "(chưa)"
                vals[5] = preview
                vals[6] = answer or "(trống)"
                self._tree.item(iid, values=vals)
            # Lấy callable AI từ MainWindow (_make_ai_call) để nút "🤖 AI
            # sửa theo gợi ý" hiển thị và hoạt động được.
            try:
                top = self.winfo_toplevel()
                get_ai_call = getattr(top, "_make_ai_call", None)
            except Exception:
                get_ai_call = None
            EditQuestionDialogV2(self, q, on_save_cb=_on_save,
                                  get_ai_call=get_ai_call,
                                  subject=self._subject_var.get(),
                                  grade=self._grade_var.get())
        except Exception as e:
            messagebox.showinfo("Sửa câu",
                f"Không mở được dialog sửa: {e}\n\n"
                f"Bạn vẫn có thể tick / bỏ tick câu này.",
                parent=self)

    def _toggle_all(self, on: bool):
        mark = "✓" if on else ""
        for iid in self._tree.get_children():
            vals = list(self._tree.item(iid, "values"))
            vals[0] = mark
            self._tree.item(iid, values=vals)
        self._update_count_label()

    def _delete_chosen(self):
        to_remove = [iid for iid in self._tree.get_children()
                     if self._tree.item(iid, "values")[0] == "✓"]
        if not to_remove:
            return
        if not messagebox.askyesno("Xác nhận",
            f"Xoá {len(to_remove)} câu đã tick?", parent=self):
            return
        # Build new questions list bỏ qua các index đã chọn
        keep_ids = set()
        for iid in self._tree.get_children():
            if self._tree.item(iid, "values")[0] != "✓":
                keep_ids.add(int(iid) - 1)
        self._questions = [q for i, q in enumerate(self._questions)
                            if i in keep_ids]
        # Rebuild tree
        self._tree.delete(*self._tree.get_children())
        for i, q in enumerate(self._questions, 1):
            preview = (q.question or "").replace("\n", " ")[:120]
            answer = q.answer or ""
            if q.qtype == "DS" and q.answers:
                answer = ",".join(f"{k}={'Đ' if v else 'S'}"
                                   for k, v in q.answers.items())
            self._tree.insert("", "end", iid=str(i), values=(
                "✓", i, q.qtype, q.level, q.topic or "(chưa)",
                preview, answer or "(trống)"
            ), tags=(q.qtype,))
        self._update_count_label()

    def _update_count_label(self):
        chosen = sum(1 for iid in self._tree.get_children()
                     if self._tree.item(iid, "values")[0] == "✓")
        total = len(self._tree.get_children())
        self._summary_lbl.config(text=f"✓ Tick {chosen}/{total} câu")

    # ──────────────────────────────────────────────────────────────────────
    #  PUSH NHCH
    # ──────────────────────────────────────────────────────────────────────

    def _on_push_nhch(self):
        chosen_idxs = [int(iid) - 1
                       for iid in self._tree.get_children()
                       if self._tree.item(iid, "values")[0] == "✓"]
        if not chosen_idxs:
            messagebox.showwarning("Chưa chọn câu",
                "Tick chọn ít nhất 1 câu để đẩy lên NHCH.", parent=self)
            return

        qs_chosen = [self._questions[i] for i in chosen_idxs]
        meta = {
            "subject": self._subject_var.get() or "Toán",
            "grade":   self._grade_var.get() or "12",
            "topic":   self._meta.get("topic", ""),
        }

        if not messagebox.askyesno(
            "Xác nhận đẩy lên NHCH",
            f"Đẩy {len(qs_chosen)} câu lên NHCH (Supabase)?\n\n"
            f"Môn: {meta['subject']} • Lớp: {meta['grade']}\n"
            f"Câu sẽ được lưu vào NHCH chung.",
            parent=self):
            return

        self._push_btn.config(state="disabled")
        self._prog_lbl.config(text="📤 Đang upload…", fg=BLUE)

        def _do_push():
            try:
                from services.license_manager import (
                    nhch_upload_batch, get_machine_id
                )
                from core.pdf_to_questions import questions_to_nhch_rows

                rows = questions_to_nhch_rows(
                    qs_chosen, meta,
                    id_prefix="PDF",
                    source_file=self._filepath or "",
                )
                result = nhch_upload_batch(
                    rows, get_machine_id(),
                    uploader_name="Import PDF Dialog")
                self.after(0, self._on_push_done, result)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Lỗi upload", str(e)[:300], parent=self))
                self.after(0, lambda: self._push_btn.config(state="normal"))

        threading.Thread(target=_do_push, daemon=True).start()

    def _on_push_done(self, result: dict):
        if result.get("ok"):
            added   = result.get("added", 0)
            skipped = result.get("skipped", 0)
            messagebox.showinfo(
                "Upload thành công",
                f"✅ Đã đẩy {added} câu lên NHCH.\n"
                f"⏭ Bỏ qua {skipped} câu trùng.\n\n"
                f"Câu đã sẵn sàng dùng trong NHCH chung.",
                parent=self)
            self._prog_lbl.config(
                text=f"✓ Đã đẩy {added} câu • bỏ qua {skipped} trùng", fg=GREEN)
        else:
            err = result.get("error", "Lỗi không rõ")
            messagebox.showerror("Upload thất bại", err, parent=self)
            self._prog_lbl.config(text=f"✘ {err[:80]}", fg=RED)
        self._push_btn.config(state="normal")


# ═════════════════════════════════════════════════════════════════════════════
#  Public helper
# ═════════════════════════════════════════════════════════════════════════════

def open_import_pdf_dialog(parent, *, subject: str = "Toán",
                            grade: str = "12",
                            default_provider: str = "Google Gemini",
                            tab_config=None) -> None:
    """Tiện ích mở dialog từ menu/toolbar.

    `tab_config` (tuỳ chọn): truyền thẳng TabConfig để dialog lấy luôn
    provider/model/api_keys đã chọn ở tab Cài đặt. Nếu không truyền, dialog
    sẽ tự tìm từ `parent.winfo_toplevel()._tab_config`.
    """
    ImportPdfDialog(parent, subject=subject, grade=grade,
                     default_provider=default_provider,
                     tab_config=tab_config)
