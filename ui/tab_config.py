"""
ui/tab_config.py — Tab ① Cài đặt: chọn AI provider/model, API key, file ma trận.
Cập nhật: hiển thị nguồn API key (admin cấp hay tự nhập)
"""

from __future__ import annotations
import os
import re
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Callable, Optional

from config import (
    AI_PROVIDERS,
    MODEL_DESC,
    get_selected_ai_provider,
    set_selected_ai_provider,
    get_selected_ai_model,
    set_selected_ai_model,
    get_selected_api_source,
    set_selected_api_source,
)
from core.parser import parse_matrix_file
from core.models import MatrixData
from ui.theme import C, FONT, PAD
from services.retry_service import split_keys
from services.key_manager import get_key_manager


class TabConfig(ttk.Frame):
    """
    Tab ① — Cài đặt.
    Callback contracts (được gọi từ main_window):
        on_matrix_loaded(matrix_data: MatrixData) → None
    """

    def __init__(self, parent, on_matrix_loaded: Callable[[MatrixData], None], license_info: dict = None):
        super().__init__(parent)
        self._on_loaded = on_matrix_loaded
        self.matrix_data: Optional[MatrixData] = None
        self._key_visible = True   # widget bắt đầu ở trạng thái hiện (editable)
        self._saved_keys = ""      # lưu nội dung key gốc khi ẩn
        self._license_info = license_info or {}
        self._admin_key = ""
        self._build()

    # ── Build ──────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # ── Vùng cuộn dọc: nội dung dài (API key, file, preview) không đẩy mất "Thông tin đề" ──
        _bg = C.get("bg", "#F8FAFC")
        canvas = tk.Canvas(self, highlightthickness=0, bg=_bg, borderwidth=0)
        vsb = ttk.Scrollbar(
            self,
            orient="vertical",
            command=canvas.yview,
        )
        host = tk.Frame(canvas, bg=_bg)
        win_id = canvas.create_window((0, 0), window=host, anchor="nw")

        self._canvas = canvas
        self._host = host

        def _on_wheel(e):
            try:
                delta = getattr(e, "delta", 0)
                if delta:
                    n = -1 if delta > 0 else 1
                else:
                    num = getattr(e, "num", 0)
                    n = -1 if num == 4 else 1
                canvas.yview_scroll(n * 3, "units")
            except Exception:
                pass
            return "break"

        self._on_canvas_wheel = _on_wheel

        def _bind_mousewheel_tree(w):
            try:
                key_widget = getattr(self, "_key_text", None)
                if w is not key_widget:
                    w.bind("<MouseWheel>", _on_wheel, add="+")
                    w.bind("<Button-4>", _on_wheel, add="+")
                    w.bind("<Button-5>", _on_wheel, add="+")
                for child in w.winfo_children():
                    _bind_mousewheel_tree(child)
            except Exception:
                pass

        self._bind_mousewheel_tree = _bind_mousewheel_tree

        def _sync_scroll(_event=None):
            try:
                canvas.update_idletasks()
                bbox = canvas.bbox("all")
                req_h = host.winfo_reqheight()
                req_w = host.winfo_reqwidth()
                h = max(req_h, bbox[3] if bbox else 0)
                w = max(req_w, bbox[2] if bbox else 0)
                if h > 0:
                    canvas.configure(scrollregion=(0, 0, w, h))
                _bind_mousewheel_tree(host)
            except Exception:
                pass

        self._sync_scroll = _sync_scroll

        def _fill_width(event):
            canvas.itemconfig(win_id, width=event.width)

        host.bind("<Configure>", _sync_scroll)
        canvas.bind("<Configure>", lambda e: (_fill_width(e), _sync_scroll()))
        self.bind("<Map>", lambda _: self.after(100, _sync_scroll))

        canvas.bind("<MouseWheel>", _on_wheel)
        host.bind("<MouseWheel>", _on_wheel)
        canvas.bind("<Button-4>", _on_wheel)
        canvas.bind("<Button-5>", _on_wheel)
        host.bind("<Button-4>", _on_wheel)
        host.bind("<Button-5>", _on_wheel)

        canvas.pack(side="left", fill="both", expand=True)
        canvas.configure(yscrollcommand=vsb.set)
        # Scrollbar luôn hiển thị — hiện rõ con trượt khi nội dung dài
        vsb.pack(side="right", fill="y")

        # ── Header bar ───────────────────────────────────────────────────
        hdr = tk.Frame(host, bg="#E2E8F0")
        hdr.pack(fill="x", padx=8, pady=4)
        tk.Label(hdr, text="⚙️  Cài đặt AI & Thông tin đề",
                bg="#E2E8F0", fg="#0284C7",
                font=("Segoe UI", 9, "bold")).pack(side="left", padx=4, pady=4)


        # ── Thông tin đề ───────────────────────────────────────────────────
        frm_info = ttk.LabelFrame(host, text="📋 Thông tin đề kiểm tra")
        frm_info.pack(fill="x", padx=8, pady=3)
        g2 = tk.Frame(frm_info)
        g2.pack(fill="x", padx=8, pady=4)

        # Row 0: Môn | Lớp | Kỳ | Năm
        tk.Label(g2, text="Môn:", font=("Segoe UI", 8)).grid(row=0, column=0, sticky="w", pady=2)
        self.subject_var = tk.StringVar(value="Toán")
        ttk.Entry(g2, textvariable=self.subject_var, width=12).grid(
            row=0, column=1, sticky="w", padx=4)

        tk.Label(g2, text="Lớp:", font=("Segoe UI", 8)).grid(row=0, column=2, sticky="w", padx=(4, 0))
        self.grade_var = tk.StringVar(value="12")
        ttk.Combobox(g2, textvariable=self.grade_var,
            values=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"],
            width=5, state="readonly").grid(row=0, column=3, sticky="w", padx=4)

        tk.Label(g2, text="Kỳ:", font=("Segoe UI", 8)).grid(row=0, column=4, sticky="w", padx=(4, 0))
        self.semester_var = tk.StringVar(value="Giữa kì II")
        ttk.Combobox(g2, textvariable=self.semester_var,
            values=["Giữa kì I", "Cuối kì I", "Giữa kì II", "Cuối kì II"],
            width=12, state="readonly").grid(row=0, column=5, sticky="w", padx=4)

        tk.Label(g2, text="Năm:", font=("Segoe UI", 8)).grid(row=0, column=6, sticky="w", padx=(4, 0))
        self.year_var = tk.StringVar(value="2026-2027")
        ttk.Entry(g2, textvariable=self.year_var, width=10).grid(
            row=0, column=7, sticky="w", padx=4)

        tk.Label(g2, text="Thời gian:", font=("Segoe UI", 8)).grid(row=1, column=0, sticky="w", pady=2)
        self.time_var = tk.StringVar(value="90 phút")
        ttk.Combobox(g2, textvariable=self.time_var,
            values=["15 phút", "45 phút", "60 phút", "90 phút", "120 phút"],
            width=12, state="readonly").grid(row=1, column=1, sticky="w", padx=4)

        # Separator
        ttk.Separator(g2, orient="horizontal").grid(
            row=2, column=0, columnspan=8, sticky="ew", pady=4)

        # Row 3: Trường & GV
        tk.Label(g2, text="Tên trường:", font=("Segoe UI", 8)).grid(row=3, column=0, sticky="w", pady=2)
        self.school_var = tk.StringVar()
        ttk.Entry(g2, textvariable=self.school_var, width=28).grid(
            row=3, column=1, sticky="w", padx=4, columnspan=3)

        tk.Label(g2, text="GV ra đề:", font=("Segoe UI", 8)).grid(row=3, column=4, sticky="w", padx=(4, 0))
        self.teacher_var = tk.StringVar()
        ttk.Entry(g2, textvariable=self.teacher_var, width=18).grid(
            row=3, column=5, sticky="w", padx=4)

        tk.Button(g2, text="💾", font=("Segoe UI", 8, "bold"),
                  bg="#10B981", fg="white", relief="flat", cursor="hand2",
                  padx=8, pady=2, command=self._save_school_info).grid(
                      row=3, column=6, sticky="w", padx=4)

        self._load_school_info()


        # ── Section 1: AI Provider & Model ──────────────────────────────
        frm_ai = ttk.LabelFrame(host, text="🤖  Nhà cung cấp & Mô hình AI")
        frm_ai.pack(fill="x", padx=8, pady=3)

        ai_row = tk.Frame(frm_ai, bg="#FFFFFF")
        ai_row.pack(fill="x", padx=8, pady=4)

        # Provider
        tk.Label(ai_row, text="Nhà cung cấp:",
                bg="#FFFFFF", fg="#334155",
                font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w", padx=4)
        saved_prov = get_selected_ai_provider()
        self.provider_var = tk.StringVar(value=saved_prov)
        cb_p = ttk.Combobox(ai_row, textvariable=self.provider_var,
                           values=list(AI_PROVIDERS.keys()),
                           state="readonly", width=16)
        cb_p.grid(row=0, column=1, sticky="w", padx=8)
        cb_p.bind("<<ComboboxSelected>>", lambda _: self._on_provider_change())

        # Model
        tk.Label(ai_row, text="Mô hình:",
                bg="#FFFFFF", fg="#334155",
                font=("Segoe UI", 8, "bold")).grid(row=0, column=2, sticky="w", padx=4)
        self.model_var = tk.StringVar()
        self.cb_model = ttk.Combobox(ai_row, textvariable=self.model_var,
                                    state="readonly", width=28)
        self.cb_model.grid(row=0, column=3, sticky="w")
        self.cb_model.bind("<<ComboboxSelected>>", lambda _: self._on_model_change())

        self._model_desc = tk.Label(ai_row, text="",
                bg="#FFFFFF", fg="#059669",
                font=("Segoe UI", 7, "italic"))
        self._model_desc.grid(row=1, column=0, columnspan=4, sticky="w", pady=0)

        # ── Section 2: Cross-Model Verification ───────────────────────
        from config import CROSS_MODEL_VERIFY, DEFAULT_VERIFIER_MODEL
        self._cross_model_var = tk.BooleanVar(value=CROSS_MODEL_VERIFY)

        frm_cm = ttk.LabelFrame(host, text="🔬  Cross-Model Verification")
        frm_cm.pack(fill="x", padx=8, pady=3)

        cm_row = tk.Frame(frm_cm, bg="#EFF6FF")
        cm_row.pack(fill="x", padx=8, pady=4)

        tk.Checkbutton(cm_row, text="Bật xác minh 2 model",
                      variable=self._cross_model_var, bg="#EFF6FF",
                      font=("Segoe UI", 8, "bold"), activebackground="#EFF6FF",
                      command=self._on_cross_model_toggle).pack(side="left")

        tk.Label(cm_row, text="  Verifier:",
                bg="#EFF6FF", fg="#475569",
                font=("Segoe UI", 7)).pack(side="left", padx=4)

        self._verifier_provider_var = tk.StringVar(value="Anthropic Claude")
        cb_vp = ttk.Combobox(cm_row, textvariable=self._verifier_provider_var,
                             values=list(AI_PROVIDERS.keys()),
                             state="readonly", width=14)
        cb_vp.pack(side="left", padx=4)
        cb_vp.bind("<<ComboboxSelected>>", lambda _: self._on_verifier_provider_change())

        self._verifier_model_var = tk.StringVar(value=DEFAULT_VERIFIER_MODEL)
        self._cb_verifier_model = ttk.Combobox(cm_row, textvariable=self._verifier_model_var,
                                                state="readonly", width=22)
        self._cb_verifier_model.pack(side="left", padx=4)

        tk.Label(frm_cm, text="Model chính tạo → Verifier xác nhận → Tự động tạo lại nếu không đồng ý.",
                bg="#EFF6FF", fg="#1D4ED8",
                font=("Segoe UI", 7, "italic")).pack(anchor="w", padx=8, pady=2)

        self._on_verifier_provider_change()

        # ── Section 2b: Auto-TikZ (AI tự vẽ hình khi cần) ───────────────
        try:
            from config import is_auto_tikz_enabled as _is_auto_tikz
            _auto_tikz_init = _is_auto_tikz()
        except Exception:
            _auto_tikz_init = True
        self._auto_tikz_var = tk.BooleanVar(value=_auto_tikz_init)

        frm_tikz = ttk.LabelFrame(host, text="🖌️  Tự động vẽ hình (TikZ)")
        frm_tikz.pack(fill="x", padx=8, pady=3)

        tikz_row = tk.Frame(frm_tikz, bg="#FEF3C7")
        tikz_row.pack(fill="x", padx=8, pady=4)

        tk.Checkbutton(
            tikz_row,
            text="Chèn lệnh vẽ TikZ khi tạo câu hỏi (AI tự nhận diện khi cần)",
            variable=self._auto_tikz_var, bg="#FEF3C7",
            font=("Segoe UI", 8, "bold"), activebackground="#FEF3C7",
            command=self._on_auto_tikz_toggle,
        ).pack(side="left")

        tk.Label(
            frm_tikz,
            text="• Bật: AI sẽ tự nhận diện câu cần hình (hình học, đồ thị, bảng biến thiên, biểu đồ…) và chèn \\begin{tikzpicture}…\\end{tikzpicture}.\n"
                 "• Hình vẽ sẽ khớp với dữ kiện đề bài và dùng packages: tikz, pgfplots (compat=1.18), tkz-tab.",
            bg="#FEF3C7", fg="#92400E",
            font=("Segoe UI", 7, "italic"), justify="left",
        ).pack(anchor="w", padx=8, pady=(0, 3))

        # ── Section 2c: Auto-export Word sau gen [SPEED-1] ───────────────
        try:
            from config import is_auto_export_enabled as _is_auto_export
            _auto_export_init = _is_auto_export()
        except Exception:
            _auto_export_init = True
        self._auto_export_var = tk.BooleanVar(value=_auto_export_init)

        frm_export = ttk.LabelFrame(host, text="⚡  Tự xuất Word sau khi tạo đề")
        frm_export.pack(fill="x", padx=8, pady=3)

        export_row = tk.Frame(frm_export, bg="#DBEAFE")
        export_row.pack(fill="x", padx=8, pady=4)

        tk.Checkbutton(
            export_row,
            text="Tự xuất Word & mở file ngay sau khi tạo đề xong",
            variable=self._auto_export_var, bg="#DBEAFE",
            font=("Segoe UI", 8, "bold"), activebackground="#DBEAFE",
            command=self._on_auto_export_toggle,
        ).pack(side="left")

        # Row: thư mục mặc định
        dir_row = tk.Frame(frm_export, bg="#DBEAFE")
        dir_row.pack(fill="x", padx=8, pady=(0, 4))

        try:
            from config import get_auto_export_dir
            _cur_dir = str(get_auto_export_dir())
        except Exception:
            _cur_dir = "(Documents/MEA Exam)"

        tk.Label(dir_row, text="Thư mục lưu:", bg="#DBEAFE", fg="#1E3A8A",
                 font=("Segoe UI", 8)).pack(side="left")
        self._auto_export_dir_lbl = tk.Label(
            dir_row, text=_cur_dir,
            bg="#DBEAFE", fg="#1E40AF",
            font=("Segoe UI", 8, "bold"),
        )
        self._auto_export_dir_lbl.pack(side="left", padx=4)
        tk.Button(
            dir_row, text="📂 Đổi…", font=("Segoe UI", 8),
            bg="#EFF6FF", fg="#1E40AF", relief="flat", cursor="hand2",
            padx=6, pady=1, command=self._on_pick_auto_export_dir,
        ).pack(side="left", padx=4)

        tk.Label(
            frm_export,
            text="• Bật: ngay sau khi AI tạo xong, app tự lưu file Word + mở file. Toast hiện cho phép đổi vị trí / lưu thêm bản.\n"
                 "• Tắt: app sẽ hỏi vị trí lưu mỗi lần (như cũ).\n"
                 "• Tên file mặc định: MEA_{Môn}{Lớp}_{ngày_giờ}.docx",
            bg="#DBEAFE", fg="#1E3A8A",
            font=("Segoe UI", 7, "italic"), justify="left",
        ).pack(anchor="w", padx=8, pady=(0, 3))

        # ── Section 3: API Key ────────────────────────────────────────
        tier = self._license_info.get("tier", "basic")
        admin_key = self._license_info.get("admin_api_key", "")
        tier_upper = {"basic": "🥉 BASIC", "pro": "🥈 PRO", "premium": "🏆 PRE"}.get(tier, tier.upper())
        tier_badge_bg = {"basic": "#64748B", "pro": "#0284C7", "premium": "#8B5CF6"}.get(tier, "#64748B")

        frm_key = ttk.LabelFrame(host, text=f"🔑  API Key  —  {tier_upper}")
        frm_key.pack(fill="x", padx=8, pady=3)

        saved_source = get_selected_api_source()
        if saved_source == "admin" and admin_key and tier in ("pro", "premium"):
            initial_source = "admin"
        elif saved_source == "self":
            initial_source = "self"
        else:
            initial_source = "admin" if admin_key and tier in ("pro", "premium") else "self"
        self._api_source_var = tk.StringVar(value=initial_source)

        # Key input row: label | text | buttons
        row_k = tk.Frame(frm_key, bg="#FFFFFF")
        row_k.pack(fill="x", padx=8, pady=3)
        row_k.columnconfigure(1, weight=1)

        # Source radio buttons (PRO/Premium)
        lbl_frame = tk.Frame(row_k, bg="#FFFFFF")
        lbl_frame.grid(row=0, column=0, sticky="nw", padx=4, pady=2)
        tk.Label(lbl_frame, text="Nguồn:",
                bg="#FFFFFF", fg="#334155",
                font=("Segoe UI", 7, "bold")).pack(anchor="w")
        if tier in ("pro", "premium") and admin_key:
            for val, txt in [("admin", "🔑 Admin"), ("self", "✏️ Tự nhập")]:
                tk.Radiobutton(lbl_frame, text=txt, variable=self._api_source_var,
                              value=val, font=("Segoe UI", 7),
                              bg="#FFFFFF", command=self._on_api_source_change).pack(anchor="w")

        # Container chứa text widget và scrollbar dọc
        key_box = tk.Frame(row_k, bg="#FFFFFF")
        key_box.grid(row=0, column=1, sticky="nsew", padx=2, pady=1)
        key_box.columnconfigure(0, weight=1)
        key_box.rowconfigure(0, weight=1)

        # Key text — wrap="none" để giữ key trên 1 dòng dài mượt mà, cuộn ngang xem tới lui
        self._key_text = tk.Text(key_box, height=1, font=("Consolas", 8),
                                wrap="none", relief="solid", borderwidth=1,
                                bg="#FFFBEB")
        self._key_text.grid(row=0, column=0, sticky="nsew")

        # Scrollbar dọc (hiển thị khi mở rộng nhiều dòng)
        self._key_vsb = ttk.Scrollbar(key_box, orient="vertical", command=self._key_text.yview)
        self._key_text.configure(yscrollcommand=self._key_vsb.set)
        self._key_expanded = False

        # Xử lý cuộn chuột thông minh trên ô nhập Key:
        # - Chế độ 1 dòng: Lăn chuột để cuộn ngang xem key từ đầu tới cuối (coi key tới lui)
        # - Chế độ mở rộng: Lăn chuột để cuộn dọc xem danh sách key
        def _on_key_wheel(e):
            try:
                delta = getattr(e, "delta", 0)
                if delta:
                    notch = -1 if delta > 0 else 1
                else:
                    num = getattr(e, "num", 0)
                    notch = -1 if num == 4 else 1

                if not getattr(self, "_key_expanded", False):
                    self._key_text.xview_scroll(notch * 3, "units")
                else:
                    self._key_text.yview_scroll(notch * 2, "units")
            except Exception:
                pass
            return "break"

        def _on_key_shift_wheel(e):
            try:
                delta = getattr(e, "delta", 0)
                notch = -1 if delta > 0 else 1
                self._key_text.xview_scroll(notch * 3, "units")
            except Exception:
                pass
            return "break"

        self._key_text.bind("<MouseWheel>", _on_key_wheel)
        self._key_text.bind("<Shift-MouseWheel>", _on_key_shift_wheel)
        self._key_text.bind("<Button-4>", _on_key_wheel)
        self._key_text.bind("<Button-5>", _on_key_wheel)

        # Buttons — xếp ngang cạnh nhau để khớp chiều cao 1 dòng, không bị tràn hay che khuất
        btn_col = tk.Frame(row_k, bg="#FFFFFF")
        btn_col.grid(row=0, column=2, sticky="ne", padx=(4, 2), pady=1)

        self._toggle_btn = tk.Button(btn_col, text="👁",
                                    bg="#64748B", fg="white", activebackground="#475569",
                                    font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", bd=0,
                                    padx=6, pady=2, command=self._toggle_key)
        self._toggle_btn.pack(side="left", padx=1)

        self._expand_btn = tk.Button(btn_col, text="↕ Mở rộng",
                                     bg="#2563EB", fg="white", activebackground="#1D4ED8",
                                     font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", bd=0,
                                     padx=6, pady=2, command=self._toggle_expand_key)
        self._expand_btn.pack(side="left", padx=1)

        tk.Button(btn_col, text="💾 Lưu",
                 bg="#10B981", fg="white", activebackground="#059669",
                 font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2", bd=0,
                 padx=8, pady=2, command=self._save_key_encrypted).pack(side="left", padx=1)

        # Hàng nút phụ: chọn file api.txt + mở link lấy API key + mẹo lăn chuột
        row_k2 = tk.Frame(frm_key, bg="#FFFFFF")
        row_k2.pack(fill="x", padx=8, pady=(1, 4))
        tk.Button(row_k2, text="📁  Chọn file api.txt",
                 bg="#0EA5E9", fg="white", activebackground="#0284C7",
                 font=("Segoe UI", 7, "bold"), relief="flat", cursor="hand2", bd=0,
                 padx=8, pady=2, command=self._pick_api_key_file).pack(side="left", padx=2)
        tk.Button(row_k2, text="🌐  Lấy API key",
                 bg="#F59E0B", fg="white", activebackground="#D97706",
                 font=("Segoe UI", 7, "bold"), relief="flat", cursor="hand2", bd=0,
                 padx=8, pady=2, command=self._open_get_key_url).pack(side="left", padx=2)
        tk.Label(row_k2,
                text="💡 Lăn chuột trong ô để xem key tới lui; bấm “↕ Mở rộng” để xem nhiều dòng.",
                bg="#FFFFFF", fg="#475569",
                font=("Segoe UI", 7, "italic")).pack(side="left", padx=6)

        self._key_hint = tk.Label(frm_key, text="", fg="#64748B",
                                  font=("Segoe UI", 7))
        self._key_hint.pack(anchor="w", padx=8, pady=1)
        self._key_source_lbl = tk.Label(frm_key, text="", fg="#1F497D",
                                        font=("Segoe UI", 7, "italic"))
        self._key_source_lbl.pack(anchor="w", padx=8)

        # ── Section 4: Ma trận đặc tả hoặc đề thi ─────────────────────────
        frm_file = ttk.LabelFrame(
            host,
            text="📄  Ma trận đặc tả / Đề thi (.docx / .pdf → AI phân tích thành ma trận)",
        )
        frm_file.pack(fill="x", padx=8, pady=3)

        # File path row
        row_f = tk.Frame(frm_file, bg="#FFFFFF")
        row_f.pack(fill="x", padx=8, pady=3)
        self._file_var = tk.StringVar()
        ttk.Entry(row_f, textvariable=self._file_var).pack(
            side="left", fill="x", expand=True, padx=4)
        ttk.Button(row_f, text="📂",
                   width=5, command=self._pick_file).pack(side="left", padx=2)
        ttk.Button(row_f, text="📥",
                   width=5, command=self._download_template).pack(side="left", padx=2)
        # Nút AI nhận diện ma trận — luôn dùng AI bất kể parser truyền thống
        # có thành công hay không. Hữu ích khi parser bỏ sót hoặc cấu trúc lạ.
        self._ai_recog_btn = tk.Button(
            row_f, text="🤖  AI nhận diện ma trận",
            bg="#7C3AED", fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2", padx=10, pady=3,
            activebackground="#6D28D9",
            activeforeground="white",
            command=self._on_ai_analyze_click)
        self._ai_recog_btn.pack(side="left", padx=4)

        # Status row
        row_st = tk.Frame(frm_file, bg="#FFFFFF")
        row_st.pack(fill="x", padx=8, pady=2)
        self._file_status_var = tk.StringVar(value="⚠️  Chưa chọn file")
        self._file_status_lbl = tk.Label(row_st, textvariable=self._file_status_var,
                                         fg="#B45309", bg="#FFFFFF",
                                         font=("Segoe UI", 8, "bold"))
        self._file_status_lbl.pack(side="left")
        self._matrix_stat_var = tk.StringVar()
        tk.Label(row_st, textvariable=self._matrix_stat_var,
                fg="#059669", bg="#FFFFFF",
                font=("Segoe UI", 8, "bold")).pack(side="left", padx=8)

        self._preview = scrolledtext.ScrolledText(frm_file, height=2,
                font=("Consolas", 7), state="disabled", wrap="word",
                bg="#F8FAFC")
        self._preview.pack(fill="x", padx=8, pady=3)

        # ── Phân tích đề thi & Tải ma trận ─────────────────────────────────
        row_act = tk.Frame(frm_file, bg="#FFFFFF")
        row_act.pack(fill="x", padx=8, pady=(0, 4))

        tk.Button(
            row_act,
            text="📋  Phân tích đề thi → Ma trận",
            bg="#2563EB", fg="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat", cursor="hand2",
            padx=8, pady=3,
            activebackground="#1D4ED8",
            command=self._open_analyze_exam,
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            row_act,
            text="📥  Tải ma trận đã lưu…",
            bg="#0891B2", fg="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat", cursor="hand2",
            padx=8, pady=3,
            activebackground="#0E7490",
            command=self._load_matrix_from_file,
        ).pack(side="left", padx=(0, 4))

        tk.Label(
            row_act,
            text="💡 Nút 🤖 (tím, ở trên) = AI đọc lại file ma trận khi đọc tự động bị sai/thiếu",
            bg="#FFFFFF", fg="#64748B",
            font=("Segoe UI", 7, "italic"),
        ).pack(side="left", padx=8)

        # ── Cài đặt ứng dụng (variables only — UI in settings dialog) ──
        self._nhch_var = tk.StringVar()
        self._autostart_var = tk.BooleanVar(value=False)
        self._open_after_var = tk.BooleanVar(value=True)
        self._load_app_settings()

        # Khởi tạo provider (cũng auto-load key đã lưu)
        self._on_provider_change()

        # Đảm bảo tính toán đúng vùng cuộn sau khi toàn bộ widget render
        self.after(50, self._sync_scroll)
        self.after(200, self._sync_scroll)
        self.after(600, self._sync_scroll)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _on_api_source_change(self) -> None:
        """Xử lý khi người dùng chuyển đổi nguồn API key (admin/self)."""
        source = self._api_source_var.get()
        set_selected_api_source(source)
        admin_key = self._license_info.get("admin_api_key", "")
        if source == "admin" and admin_key:
            self._set_key_text(admin_key)
            self._key_source_lbl.config(
                text="🔑 Đang dùng API Key do Admin cấp",
                fg="#2E7D32",
            )
            self._key_text.config(state="disabled", bg="#F0F0F0")
            self._admin_key = admin_key
        else:
            self._admin_key = ""
            self._key_source_lbl.config(text="🔑 Nhập API Key của bạn")
            self._key_text.config(state="normal", bg="#FFFFF0")
            # Load key đã lưu
            self._load_env_key_self()

    def _on_provider_change(self) -> None:
        prov = self.provider_var.get()
        set_selected_ai_provider(prov)
        info = AI_PROVIDERS.get(prov, {})
        models = info.get("models", [])
        self.cb_model["values"] = models
        saved_model = get_selected_ai_model(prov)
        if models:
            target_model = saved_model if saved_model in models else models[0]
            self.model_var.set(target_model)
            set_selected_ai_model(prov, target_model)
        self._key_hint.config(
            text=f"Định dạng: {info.get('key_hint','')}   |   {info.get('install','')}",
        )
        self._update_model_desc()
        # Load key đã lưu cho provider mới
        self._load_env_key()

    def _on_model_change(self) -> None:
        prov = self.provider_var.get()
        model = self.model_var.get()
        set_selected_ai_model(prov, model)
        self._update_model_desc()

    def _update_model_desc(self) -> None:
        self._model_desc.config(text=MODEL_DESC.get(self.model_var.get(), ""))

    def _on_cross_model_toggle(self) -> None:
        """Bật/tắt cross-model verification."""
        enabled = self._cross_model_var.get()
        if enabled:
            # Kiểm tra có đủ key cho verifier không
            vp = self._verifier_provider_var.get()
            keys = self._get_keys_for_provider(vp)
            if not keys or not keys[0].strip():
                from tkinter import messagebox
                messagebox.showwarning(
                    "Thiếu API Key cho Verifier",
                    f"Bạn đã bật Cross-Model Verification nhưng chưa có API Key cho {vp}.\n"
                    f"Hãy nhập API Key và nhấn '💾 Lưu key' trước khi sử dụng tính năng này.",
                    parent=self,
                )

    def _on_auto_tikz_toggle(self) -> None:
        """Bật/tắt tính năng AI tự động vẽ TikZ khi tạo câu hỏi.

        Ghi ngay vào app_settings.json để prompt-builder đọc được ở lần tạo
        câu tiếp theo, không cần khởi động lại app.
        """
        try:
            from config import set_auto_tikz_enabled
            set_auto_tikz_enabled(bool(self._auto_tikz_var.get()))
        except Exception:
            pass

    def _on_auto_export_toggle(self) -> None:
        """Bật/tắt [SPEED-1] auto-export Word sau khi gen."""
        try:
            from config import set_auto_export_enabled
            set_auto_export_enabled(bool(self._auto_export_var.get()))
        except Exception:
            pass

    def _on_pick_auto_export_dir(self) -> None:
        """Chọn thư mục mặc định cho auto-export."""
        from tkinter import filedialog
        try:
            from config import get_auto_export_dir, set_auto_export_dir
            cur = str(get_auto_export_dir())
        except Exception:
            cur = ""
        new_dir = filedialog.askdirectory(
            title="Chọn thư mục mặc định cho file Word",
            initialdir=cur or None,
            parent=self.winfo_toplevel(),
        )
        if not new_dir:
            return
        try:
            set_auto_export_dir(new_dir)
            self._auto_export_dir_lbl.config(text=new_dir)
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi", f"Không lưu được: {e}",
                                  parent=self.winfo_toplevel())

    def _on_verifier_provider_change(self) -> None:
        """Cập nhật danh sách model khi đổi provider của verifier."""
        vp = self._verifier_provider_var.get()
        models = AI_PROVIDERS.get(vp, {}).get("models", [])
        if models:
            self._cb_verifier_model.config(values=models)
            self._verifier_model_var.set(models[0])

    def _get_keys_for_provider(self, provider: str) -> list[str]:
        """Lấy API keys cho provider cụ thể."""
        all_keys = self.get_api_keys()
        if not all_keys or not all_keys[0]:
            return []
        keys = [k.strip() for k in all_keys[0].splitlines() if k.strip()]
        return keys

    def _toggle_key(self) -> None:
        """Chuyển đổi giữa hiển thị key thật và hiển thị số lượng key."""
        if self._key_visible:
            # Chuyển sang chế độ ẩn: lưu key hiện tại, hiển thị số lượng
            self._saved_keys = self._key_text.get("1.0", "end-1c")
            count = len(split_keys(self._saved_keys))
            self._key_text.config(state="normal")
            self._key_text.delete("1.0", "end")
            self._key_text.insert("1.0", f"🔒 Đã nhập {count} key")
            self._key_text.config(state="disabled", bg="#f0f0f0")
            self._key_visible = False
        else:
            # Chuyển sang chế độ hiện: khôi phục key đã lưu
            self._key_text.config(state="normal", bg="#FFFFF0")
            self._key_text.delete("1.0", "end")
            self._key_text.insert("1.0", self._saved_keys)
            self._key_visible = True

    def _toggle_expand_key(self) -> None:
        """Mở rộng hoặc thu nhỏ ô nhập API Key (1 dòng <-> 5 dòng) để người dùng dễ nhập và xem key."""
        self._key_expanded = not getattr(self, "_key_expanded", False)
        if self._key_expanded:
            self._key_text.config(height=5)
            try:
                self._key_vsb.grid(row=0, column=1, sticky="ns")
            except Exception:
                pass
            if hasattr(self, "_expand_btn"):
                self._expand_btn.config(text="↕ Thu nhỏ", bg="#475569")
        else:
            self._key_text.config(height=1)
            try:
                self._key_vsb.grid_remove()
            except Exception:
                pass
            if hasattr(self, "_expand_btn"):
                self._expand_btn.config(text="↕ Mở rộng", bg="#2563EB")
        if hasattr(self, "_sync_scroll"):
            self.after(50, self._sync_scroll)

    # ── Tiện ích nhập API key ─────────────────────────────────────────────

    def _pick_api_key_file(self) -> None:
        """Chọn file .txt chứa API key. Nhận diện key theo dòng / dấu phẩy / khoảng trắng.

        Quy tắc nhận diện (theo provider đang chọn):
            - Google Gemini  → key bắt đầu bằng "AIzaSy..."
            - Anthropic      → key bắt đầu bằng "sk-ant-..."
            - DeepSeek       → key bắt đầu bằng "sk-..."
        Nếu không khớp hint, vẫn lấy tất cả chuỗi "có vẻ là key" (≥ 20 ký tự,
        chỉ gồm chữ-số-dấu gạch).
        """
        # Không cho ghi đè khi đang dùng admin key
        if getattr(self, "_api_source_var", None) and self._api_source_var.get() == "admin":
            messagebox.showinfo(
                "Đang dùng API Key do Admin cấp",
                "Vui lòng chuyển nguồn sang “✏️ Tự nhập” trước khi nạp key từ file.",
            )
            return

        path = filedialog.askopenfilename(
            title="Chọn file chứa API key (api.txt)",
            filetypes=[("Text", "*.txt"), ("Tất cả", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
        except OSError as err:
            messagebox.showerror("Lỗi đọc file", f"Không đọc được file:\n{err}")
            return

        prov = self.provider_var.get()
        hint = (AI_PROVIDERS.get(prov, {}).get("key_hint") or "").rstrip(".").strip()
        # Prefix hợp lệ (bỏ "...") — ví dụ "AIzaSy", "sk-ant-", "sk-"
        prefix = hint.replace("...", "").strip()

        # Tách token theo khoảng trắng, xuống dòng, dấu phẩy, dấu chấm phẩy
        tokens = [t.strip() for t in re.split(r"[\s,;]+", content) if t.strip()]

        keys: list[str] = []
        seen: set[str] = set()

        if prefix:
            for tok in tokens:
                if tok.startswith(prefix) and len(tok) >= 20 and tok not in seen:
                    keys.append(tok)
                    seen.add(tok)

        # Fallback: nếu không tìm thấy theo prefix, chấp nhận mọi token dài ≥ 20
        if not keys:
            for tok in tokens:
                if len(tok) >= 20 and re.fullmatch(r"[A-Za-z0-9._\-]+", tok) and tok not in seen:
                    keys.append(tok)
                    seen.add(tok)

        if not keys:
            messagebox.showwarning(
                "Không tìm thấy API key",
                f"File đã chọn không chứa key phù hợp với {prov}.\n"
                f"Gợi ý: mỗi dòng 1 key, bắt đầu bằng “{prefix or '...'}”.",
            )
            return

        # Nối nhiều key bằng dấu phẩy (định dạng app đã hỗ trợ — xem split_keys)
        merged = ", ".join(keys)
        self._set_key_text(merged)
        # Đảm bảo widget về trạng thái "hiện" để người dùng kiểm tra
        self._key_visible = True
        self._toggle_btn.config(text="👁")
        try:
            self._key_hint.config(
                text=f"✅ Đã nạp {len(keys)} key từ: {os.path.basename(path)}",
                fg="#047857",
            )
        except Exception:
            pass

    def _open_get_key_url(self) -> None:
        """Mở trình duyệt tới trang lấy API key của provider đang chọn."""
        prov = self.provider_var.get()
        info = AI_PROVIDERS.get(prov, {}) or {}
        url = info.get("key_url", "")
        if not url:
            messagebox.showinfo(
                "Chưa có đường dẫn",
                f"Nhà cung cấp “{prov}” chưa được khai báo URL lấy API key.",
            )
            return
        try:
            webbrowser.open(url, new=2)
        except Exception as err:
            messagebox.showerror("Không mở được trình duyệt", f"{err}\n\nURL: {url}")

    def _load_env_key_self(self) -> None:
        """Load key tự nhập: env var → encrypted storage."""
        prov = self.provider_var.get()
        # 1. Thử env var trước
        env_name = AI_PROVIDERS.get(prov, {}).get("key_env", "")
        env_key = os.environ.get(env_name, "")
        if env_key:
            self._set_key_text(env_key)
            return
        # 2. Thử load từ encrypted storage (key_manager)
        try:
            km = get_key_manager()
            saved = km.load(prov)
            if saved:
                self._set_key_text(saved)
                return
        except Exception:
            pass
        # 3. Không có key → xóa trắng
        self._set_key_text("")

    def _load_env_key(self) -> None:
        """Tự động điền key: kiểm tra nguồn API → admin key / tự nhập."""
        tier = self._license_info.get("tier", "")
        admin_key = self._license_info.get("admin_api_key", "")

        # Nếu tier pro/premium và có admin_key, kiểm tra nguồn đã chọn
        source = getattr(self, "_api_source_var", None)
        use_admin = (
            tier in ("pro", "premium")
            and admin_key
            and (source is None or source.get() == "admin")
        )

        if use_admin:
            self._set_key_text(admin_key)
            self._key_source_lbl.config(
                text="🔑 Đang sử dụng API Key do Admin cấp",
                fg="#2E7D32",
            )
            self._key_text.config(state="disabled", bg="#F0F0F0")
            self._admin_key = admin_key
            return

        # Nếu không dùng admin key, dùng key tự nhập
        self._key_source_lbl.config(text="🔑 Nhập API Key của bạn")
        self._key_text.config(state="normal", bg="#FFFFF0")
        self._admin_key = ""
        self._load_env_key_self()

    def _set_key_text(self, key: str) -> None:
        """Đặt nội dung key vào text widget (đảm bảo đồng bộ _saved_keys)."""
        # Đảm bảo widget ở trạng thái editable
        self._key_text.config(state="normal", bg="#FFFFF0")
        self._key_text.delete("1.0", "end")
        if key:
            self._key_text.insert("1.0", key)
        self._saved_keys = key
        self._key_visible = True

    def _pick_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Chọn ma trận đặc tả hoặc đề thi (.docx, .pdf)",
            filetypes=[
                ("Word", "*.docx"),
                ("PDF", "*.pdf"),
                ("Tất cả", "*.*"),
            ],
        )
        if not path:
            return
        self._file_var.set(path)
        self._file_status_var.set("⏳  Đang đọc file…")
        self._file_status_lbl.config(fg="#0055AA")
        self._matrix_stat_var.set("")
        self.update_idletasks()

        fname = Path(path).name
        ext = Path(path).suffix.lower()

        # PDF: không có bảng Word → luôn phân tích bằng AI
        if ext == ".pdf":
            self._file_status_var.set(f"📄  PDF: {fname}")
            self._file_status_lbl.config(fg="#0369A1")
            self._matrix_stat_var.set("🤖 Đang gọi AI phân tích cấu trúc đề / ma trận...")
            self.update_idletasks()
            self._ai_recognize_matrix(path, fname)
            return

        try:
            data = parse_matrix_file(path)
        except Exception as e:
            self._file_status_var.set(f"❌  Lỗi: {e}")
            self._file_status_lbl.config(fg="#CC0000")
            return

        n = len(data.rows)

        # ── Nếu parser truyền thống trả 0 câu → tự động gọi AI nhận diện ──
        if n == 0:
            self._file_status_var.set(f"⚠️  Không nhận diện được cấu trúc từ {fname}")
            self._file_status_lbl.config(fg="#B45309")
            self._matrix_stat_var.set("🤖 Đang khởi chạy AI nhận diện cấu trúc ma trận...")
            self.update_idletasks()
            self._ai_recognize_matrix(path, fname)
            return

        self._display_matrix_result(data, fname)

    def _display_matrix_result(self, data: MatrixData, fname: str) -> None:
        """Hiển thị kết quả parse/nhận diện ma trận lên UI."""
        rows = data.rows
        n = len(rows)
        tn = sum(1 for r in rows if r.qtype == "TN")
        ds = sum(1 for r in rows if r.qtype == "DS")
        tl = sum(1 for r in rows if r.qtype in ("TL", "TLN"))
        total_pts = sum(r.points for r in rows)

        self._file_status_var.set(f"✅  Đã đọc: {fname}")
        self._file_status_lbl.config(fg="#006600")
        self._matrix_stat_var.set(
            f"📊 Tổng: {n} câu  ({tn} TN + {ds} Đ/S + {tl} TL)    "
            f"💯 Tổng điểm: {total_pts:.1f}"
        )

        # Preview
        preview_lines = []
        for r in rows[:15]:
            preview_lines.append(
                f"  {r.stt}. [{r.qtype}/{r.level}] {r.topic[:50]}  "
                f"({r.points:.2f}đ)  — {r.requirement[:40]}"
            )
        if n > 15:
            preview_lines.append(f"  ... và {n - 15} câu khác")
        self._preview.config(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.insert("1.0", "\n".join(preview_lines))
        self._preview.config(state="disabled")

        # Cập nhật time từ ma trận nếu có
        if data.time_str:
            self.time_var.set(data.time_str)

        self.matrix_data = data
        self._on_loaded(data)

    def _on_ai_analyze_click(self) -> None:
        """Nút AI phân tích thủ công — gọi AI bất kể parser có nhận hay không."""
        path = self._file_var.get().strip()
        if not path or not Path(path).exists():
            from tkinter import messagebox
            messagebox.showwarning("Chưa chọn file", "Hãy chọn file ma trận trước.", parent=self)
            return
        ext = Path(path).suffix.lower()
        if ext not in (".docx", ".pdf"):
            from tkinter import messagebox
            messagebox.showwarning(
                "Định dạng không hỗ trợ",
                "AI phân tích ma trận chỉ hỗ trợ file .docx hoặc .pdf.",
                parent=self,
            )
            return
        fname = Path(path).name
        self._file_status_var.set(f"🤖 Đang gọi AI phân tích {fname}...")
        self._file_status_lbl.config(fg="#7C3AED")
        self._matrix_stat_var.set("Vui lòng chờ AI xử lý...")
        self.update_idletasks()
        self._ai_recognize_matrix(path, fname)

    def _ai_recognize_matrix(self, filepath: str, fname: str) -> None:
        """Gọi AI nhận diện cấu trúc ma trận."""
        import threading
        from services.ai_service import create_ai_service

        provider = self.provider_var.get()
        model = self.model_var.get()
        keys = self.get_api_keys()

        if not keys:
            self._file_status_var.set("❌  Chưa nhập API Key — không thể gọi AI nhận diện")
            self._file_status_lbl.config(fg="#CC0000")
            self._matrix_stat_var.set("")
            return

        try:
            service = create_ai_service(provider, keys, model)
        except Exception as e:
            self._file_status_var.set(f"❌  Lỗi khởi tạo AI: {e}")
            self._file_status_lbl.config(fg="#CC0000")
            self._matrix_stat_var.set("")
            return

        # Lưu filepath + service để dùng cho fallback tạo ma trận
        self._ai_filepath = filepath
        self._ai_fname = fname
        self._ai_service = service

        # Bắt đầu đếm thời gian xử lý AI
        self._ai_progress_msg = "Đang khởi chạy AI..."
        self._start_ai_timer()

        def on_progress(msg: str):
            def _update():
                self._ai_progress_msg = msg
                # Render ngay với thời gian hiện tại
                self._render_ai_progress()
            self.after(0, _update)

        def _do_recognize():
            try:
                from core.ai_matrix_recognizer import recognize_matrix
                result = recognize_matrix(
                    filepath=filepath,
                    ai_call=service.generate,
                    on_progress=on_progress,
                )
                self.after(0, lambda r=result: self._on_ai_recognize_done(r, fname))
            except Exception as e:
                self.after(0, lambda err=str(e): self._on_ai_recognize_error(err))

        threading.Thread(target=_do_recognize, daemon=True).start()

    # ── AI Progress Timer ─────────────────────────────────────────────────
    def _start_ai_timer(self) -> None:
        """Bắt đầu đếm thời gian xử lý AI và update label mỗi giây."""
        import time
        self._ai_started_at = time.monotonic()
        self._ai_timer_active = True
        self._render_ai_progress()
        self._tick_ai_timer()

    def _stop_ai_timer(self) -> None:
        """Dừng timer AI."""
        self._ai_timer_active = False

    def _tick_ai_timer(self) -> None:
        """Tự re-schedule mỗi 1s để cập nhật đồng hồ."""
        if not getattr(self, "_ai_timer_active", False):
            return
        try:
            self._render_ai_progress()
        except Exception:
            return
        self.after(1000, self._tick_ai_timer)

    def _render_ai_progress(self) -> None:
        """Hiển thị 'msg ⏱ Mm Ss' lên status label."""
        import time
        if not hasattr(self, "_ai_started_at"):
            return
        elapsed = int(time.monotonic() - self._ai_started_at)
        mins, secs = divmod(elapsed, 60)
        if mins > 0:
            tstr = f"{mins}m {secs:02d}s"
        else:
            tstr = f"{secs}s"
        msg = getattr(self, "_ai_progress_msg", "Đang xử lý")
        self._matrix_stat_var.set(f"🤖 {msg}   ⏱ {tstr}")

    def _on_ai_recognize_done(self, result, fname: str) -> None:
        """Xử lý kết quả nhận diện AI."""
        from ui.dialog_ai_matrix import AIMatrixConfirmDialog

        self._stop_ai_timer()
        elapsed_str = self._format_ai_elapsed()

        if result is None or not result.rows:
            # Nhận diện thất bại → hỏi người dùng có muốn AI TẠO ma trận không
            from tkinter import messagebox
            ans = messagebox.askyesno(
                "AI không nhận diện được cấu trúc",
                f"AI không tìm thấy cấu trúc ma trận trong file '{fname}'.\n"
                f"(AI đã chạy {elapsed_str})\n\n"
                "Bạn có muốn AI TẠO MỘT MA TRẬN MỚI dựa trên\n"
                "nội dung kiến thức trong file không?",
                parent=self,
            )
            if ans:
                self._ai_progress_msg = "AI đang tạo ma trận từ nội dung kiến thức..."
                self._start_ai_timer()
                self.update_idletasks()
                self._ai_create_matrix()
            else:
                self._file_status_var.set(f"⚠️  AI không nhận diện được cấu trúc từ {fname}")
                self._file_status_lbl.config(fg="#B45309")
                self._matrix_stat_var.set(f"⏱ Đã chạy {elapsed_str}")
            return

        # Hiển thị dialog xác nhận
        dlg = AIMatrixConfirmDialog(self.winfo_toplevel(), result)
        self.wait_window(dlg)

        if dlg.result is not None:
            self._display_matrix_result(dlg.result, f"{fname} (AI · {elapsed_str})")
        else:
            self._file_status_var.set(f"⚠️  Đã hủy nhận diện AI cho {fname}")
            self._file_status_lbl.config(fg="#B45309")
            self._matrix_stat_var.set(f"⏱ Đã chạy {elapsed_str}")

    def _format_ai_elapsed(self) -> str:
        """Format thời gian đã chạy cho AI thành 'Mm Ss' hoặc 'Ss'."""
        import time
        if not hasattr(self, "_ai_started_at"):
            return "0s"
        elapsed = int(time.monotonic() - self._ai_started_at)
        mins, secs = divmod(elapsed, 60)
        return f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

    def _ai_create_matrix(self) -> None:
        """AI tạo ma trận mới từ nội dung kiến thức trong file."""
        import threading
        from ui.dialog_ai_matrix import AIMatrixConfirmDialog

        filepath = getattr(self, "_ai_filepath", "")
        fname = getattr(self, "_ai_fname", "")
        service = getattr(self, "_ai_service", None)

        if not filepath or not service:
            self._on_ai_recognize_error("Không có thông tin file/AI service")
            return

        def on_progress(msg: str):
            def _update():
                self._ai_progress_msg = msg
                self._render_ai_progress()
            self.after(0, _update)

        def _do_create():
            try:
                from core.ai_matrix_recognizer import create_matrix_from_content
                result = create_matrix_from_content(
                    filepath=filepath,
                    ai_call=service.generate,
                    on_progress=on_progress,
                )
                self.after(0, lambda r=result: self._on_ai_create_done(r, fname))
            except Exception as e:
                self.after(0, lambda err=str(e): self._on_ai_recognize_error(err))

        threading.Thread(target=_do_create, daemon=True).start()

    def _on_ai_create_done(self, result, fname: str) -> None:
        """Xử lý kết quả tạo ma trận bởi AI."""
        from ui.dialog_ai_matrix import AIMatrixConfirmDialog

        self._stop_ai_timer()
        elapsed_str = self._format_ai_elapsed()

        if result is None or not result.rows:
            self._file_status_var.set(f"⚠️  AI không tạo được ma trận từ {fname}")
            self._file_status_lbl.config(fg="#CC0000")
            self._matrix_stat_var.set(f"⏱ Đã chạy {elapsed_str} — Vui lòng kiểm tra lại nội dung file.")
            return

        dlg = AIMatrixConfirmDialog(self.winfo_toplevel(), result)
        self.wait_window(dlg)

        if dlg.result is not None:
            self._display_matrix_result(dlg.result, f"{fname} (AI tạo · {elapsed_str})")
        else:
            self._file_status_var.set(f"⚠️  Đã hủy ma trận AI tạo cho {fname}")
            self._file_status_lbl.config(fg="#B45309")
            self._matrix_stat_var.set(f"⏱ Đã chạy {elapsed_str}")

    def _on_ai_recognize_error(self, err: str) -> None:
        """Xử lý lỗi khi gọi AI."""
        self._stop_ai_timer()
        elapsed_str = self._format_ai_elapsed() if hasattr(self, "_ai_started_at") else ""
        suffix = f" (sau {elapsed_str})" if elapsed_str else ""
        self._file_status_var.set(f"❌  Lỗi AI{suffix}: {err}")
        self._file_status_lbl.config(fg="#CC0000")
        self._matrix_stat_var.set("Kiểm tra API key và thử lại.")

    # ── Phân tích đề thi → Ma trận ──────────────────────────────────────────

    def _open_analyze_exam(self) -> None:
        """Mở dialog phân tích đề thi (Word/PDF) → ma trận đặc tả."""
        from ui.dialog_analyze_exam import AnalyzeExamDialog

        # Lấy AI call từ parent (main_window)
        ai_call = None
        try:
            parent = self.winfo_toplevel()
            if hasattr(parent, "_make_ai_call"):
                ai_call = parent._make_ai_call
        except Exception:
            pass

        def on_matrix_ready(md: MatrixData):
            self._display_matrix_result(md, "Đề phân tích từ AI")
            self.matrix_data = md
            self._on_loaded(md)

        dlg = AnalyzeExamDialog(
            self,
            get_ai_call=ai_call,
            on_matrix_ready=on_matrix_ready,
        )
        # Khi dialog đóng, có thể lấy ma trận từ đó
        self.wait_window(dlg)

    def _load_matrix_from_file(self) -> None:
        """Tải ma trận đặc tả đã lưu (.docx, .json)."""
        path = filedialog.askopenfilename(
            title="Tải ma trận đặc tả",
            filetypes=[
                ("Ma trận Word", "*.docx"),
                ("Ma trận JSON", "*.json"),
                ("Tất cả", "*.*"),
            ],
        )
        if not path:
            return

        ext = os.path.splitext(path)[1].lower()
        self._file_status_var.set(f"⏳ Đang đọc {os.path.basename(path)}…")
        self._file_status_lbl.config(fg="#0055AA")
        self.update_idletasks()

        try:
            if ext == ".json":
                import json
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                md = MatrixData.from_dict(data)
            elif ext == ".docx":
                # Dùng parser ma trận có sẵn
                md = parse_matrix_file(path)
            else:
                raise ValueError(f"Không hỗ trợ định dạng: {ext}")

            self._display_matrix_result(md, os.path.basename(path))
            self.matrix_data = md
            self._on_loaded(md)

        except Exception as e:
            self._file_status_var.set(f"❌ Lỗi: {e}")
            self._file_status_lbl.config(fg="#CC0000")
            self._matrix_stat_var.set("")
            from tkinter import messagebox
            messagebox.showerror("Lỗi tải ma trận", str(e), parent=self)

    # ── Public API (được main_window gọi) ──────────────────────────────────

    def _save_key_encrypted(self) -> None:
        """Lưu API key đã mã hóa vào disk."""
        # Nếu đang dùng admin key, không cho lưu riêng
        if self._admin_key:
            from tkinter import messagebox
            messagebox.showinfo("Thông báo", "Bạn đang sử dụng API Key do Admin cấp. Không cần lưu riêng.")
            return
        # Luôn đọc key từ nguồn đúng
        if self._key_visible:
            keys = self._key_text.get("1.0", "end-1c").strip()
        else:
            keys = self._saved_keys.strip()

        if not keys or keys.startswith("🔒"):
            from tkinter import messagebox
            messagebox.showwarning("Chưa nhập key", "Hãy nhập API key trước.")
            return
        try:
            km = get_key_manager()
            km.save(self.provider_var.get(), keys)
            set_selected_api_source("self")
            if hasattr(self, "_api_source_var"):
                self._api_source_var.set("self")
            # Đồng bộ _saved_keys để get_api_keys() luôn trả đúng
            self._saved_keys = keys
            enc = (
                "Fernet (AES-128)"
                if km.is_encrypted()
                else "Base64 (cài cryptography để mã hóa mạnh hơn)"
            )
            from tkinter import messagebox
            messagebox.showinfo(
                "Đã lưu",
                f"API key đã lưu an toàn.\nMã hóa: {enc}\n\n"
                f"Key sẽ tự động load khi mở app lần sau.",
            )
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi lưu key", str(e))

    def get_api_keys(self) -> list[str]:
        # Nếu đang dùng admin key, trả về admin key
        if self._admin_key:
            return split_keys(self._admin_key)
        # Nếu không, lấy từ text widget
        if not self._key_visible:
            raw = self._saved_keys
        else:
            raw = self._key_text.get("1.0", "end-1c")
        return split_keys(raw.strip())

    def get_provider(self) -> str:
        return self.provider_var.get()

    def get_model(self) -> str:
        return self.model_var.get()

    def get_subject(self) -> str:
        return self.subject_var.get()

    def set_subject(self, val: str) -> None:
        """[SMART-1] Cho phép code khác (vd Convert auto-detect) set môn."""
        try:
            self.subject_var.set(val)
        except Exception:
            pass

    def get_grade(self) -> str:
        return self.grade_var.get()

    def set_grade(self, val: str) -> None:
        """[SMART-1] Cho phép code khác set lớp."""
        try:
            self.grade_var.set(val)
        except Exception:
            pass

    def get_semester(self) -> str:
        return self.semester_var.get()

    def get_year(self) -> str:
        return self.year_var.get()

    def get_time(self) -> str:
        return getattr(self, "time_var", None) and self.time_var.get() or "90 phút"

    def get_school_name(self) -> str:
        return getattr(self, "school_var", None) and self.school_var.get() or ""

    def get_teacher_name(self) -> str:
        return getattr(self, "teacher_var", None) and self.teacher_var.get() or ""

    def get_cross_model_enabled(self) -> bool:
        """Kiểm tra có bật cross-model verification không."""
        return getattr(self, "_cross_model_var", None) and self._cross_model_var.get() or False

    def get_verifier_provider(self) -> str:
        """Lấy provider cho verifier."""
        return getattr(self, "_verifier_provider_var", None) and self._verifier_provider_var.get() or "Anthropic Claude"

    def get_verifier_model(self) -> str:
        """Lấy model cho verifier."""
        return getattr(self, "_verifier_model_var", None) and self._verifier_model_var.get() or ""

    def get_verifier_keys(self) -> list[str]:
        """Lấy API keys cho verifier provider."""
        vp = self.get_verifier_provider()
        return self._get_keys_for_provider(vp)

    # ── YC5: Lưu/đọc thông tin trường ──────────────────────────────────────

    def _save_school_info(self) -> None:
        """Lưu tên trường & giáo viên vào settings file."""
        import json
        sf = Path.home() / ".exam_generator" / "web_settings.json"
        sf.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if sf.exists():
            try:
                data = json.loads(sf.read_text(encoding="utf-8"))
            except Exception:
                pass
        data["school_name"] = self.school_var.get().strip()
        data["teacher_name"] = self.teacher_var.get().strip()
        sf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        from tkinter import messagebox
        messagebox.showinfo("Đã lưu", "Thông tin trường/GV đã được lưu.")

    # ── YC6: Tải mẫu ma trận ──────────────────────────────────────────────

    def _download_template(self) -> None:
        """Cho user chọn mẫu ma trận và lưu file .docx."""
        from tkinter import simpledialog

        # Dialog chọn mẫu
        win = tk.Toplevel(self)
        win.title("Tải mẫu ma trận")
        win.geometry("400x400")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg="#F9F7F4")

        tk.Label(
            win, text="Chọn mẫu ma trận để tải về:",
            bg="#F9F7F4", fg="#1F497D",
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=8)

        from export.template_matrix import TEMPLATE_INFO
        sel_var = tk.StringVar(value=TEMPLATE_INFO[0]["id"])

        for t in TEMPLATE_INFO:
            f = tk.Frame(win, bg="#F9F7F4")
            f.pack(fill="x", padx=24, pady=2)
            ttk.Radiobutton(f, text="", variable=sel_var, value=t["id"]).pack(side="left")
            lbl = tk.Label(
                f, text=f"{t['label']}  —  {t['desc']}",
                bg="#F9F7F4", fg="#333",
                font=("Segoe UI", 9), wraplength=320, justify="left",
                cursor="hand2",
            )
            lbl.pack(side="left", padx=4)
            lbl.bind("<Button-1>", lambda e, v=t["id"]: sel_var.set(v))

        def do_save():
            tid = sel_var.get()
            info = next((t for t in TEMPLATE_INFO if t["id"] == tid), None)
            if not info:
                return
            path = filedialog.asksaveasfilename(
                defaultextension=".docx",
                filetypes=[("Word Document", "*.docx")],
                initialfile=info["filename"],
                parent=win,
            )
            if not path:
                return
            try:
                info["builder"](path)
                win.destroy()
                from tkinter import messagebox
                messagebox.showinfo("Tải thành công", f"Đã lưu mẫu ma trận tại:\n{path}")
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Lỗi", str(e), parent=win)

        btn_f = tk.Frame(win, bg="#F9F7F4")
        btn_f.pack(pady=12)
        ttk.Button(btn_f, text="Hủy", command=win.destroy).pack(side="right", padx=4)
        tk.Button(
            btn_f, text="  💾 Lưu mẫu  ",
            bg="#10B981", fg="white", font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2",
            command=do_save,
        ).pack(side="right", padx=4)

    def _load_school_info(self) -> None:
        """Đọc tên trường & giáo viên từ settings file."""
        import json
        sf = Path.home() / ".exam_generator" / "web_settings.json"
        if sf.exists():
            try:
                data = json.loads(sf.read_text(encoding="utf-8"))
                self.school_var.set(data.get("school_name", ""))
                self.teacher_var.set(data.get("teacher_name", ""))
            except Exception:
                pass

    # ── Cài đặt ứng dụng (NHCH, auto-start, open-after-export) ──────────

    def _load_app_settings(self) -> None:
        """Load app settings vào UI."""
        from config import load_app_settings, get_nhch_dir
        settings = load_app_settings()
        self._nhch_var.set(settings.get("nhch_dir", str(get_nhch_dir())))
        self._autostart_var.set(settings.get("auto_start", False))
        self._open_after_var.set(settings.get("open_after_export", True))

    def _save_app_settings(self) -> None:
        """Lưu app settings."""
        from config import load_app_settings, save_app_settings
        settings = load_app_settings()
        nhch = self._nhch_var.get().strip()
        if nhch:
            Path(nhch).mkdir(parents=True, exist_ok=True)
            settings["nhch_dir"] = nhch
        settings["auto_start"] = self._autostart_var.get()
        settings["open_after_export"] = self._open_after_var.get()
        save_app_settings(settings)

    def _browse_nhch(self) -> None:
        """Chọn thư mục NHCH."""
        d = filedialog.askdirectory(
            title="Chọn thư mục lưu Ngân hàng câu hỏi",
            initialdir=self._nhch_var.get())
        if d:
            self._nhch_var.set(d)
            self._save_app_settings()
            from tkinter import messagebox
            messagebox.showinfo("Đã cập nhật",
                                f"Thư mục NHCH mới:\n{d}")

    def _toggle_autostart(self) -> None:
        """Bật/tắt khởi động cùng Windows."""
        enable = self._autostart_var.get()
        try:
            import sys
            # Gọi hàm từ main.py
            from main import _set_auto_start
            _set_auto_start(enable)
        except Exception as e:
            print(f"[CẢNH BÁO] Không thể cập nhật auto-start: {e}")
        self._save_app_settings()

    def get_open_after_export(self) -> bool:
        """Trả về setting có mở file sau khi xuất không."""
        return self._open_after_var.get()