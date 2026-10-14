"""
v5/views/setup.py — Cấu hình AI Provider + Subject/Grade + License info.

Port từ tab_config.py (v4) — gọn nhẹ, không phá business logic.
Reuse services.key_manager để save/load API key (Fernet encrypted).
Reuse services.license_manager để hiển thị license info.
"""
from __future__ import annotations

import os
import re
import threading
import webbrowser
from typing import Callable

import customtkinter as ctk
from tkinter import messagebox

# Reuse v4 services
from services.key_manager import get_key_manager
from services.license_manager import check_license, get_machine_id, get_machine_display
from v5.user_profile import (
    expiry_status,
    feature_count,
    feature_rows,
    license_source_label,
    support_text,
    tier_color,
    tier_key,
    tier_label,
)

PROVIDERS = [
    ("Google Gemini",    [
        "gemini-3.8-flash",
        "gemini-3.1-pro",
        "gemini-3.8-live",
        "gemini-3.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
    ]),
    ("Anthropic Claude", ["claude-sonnet-4-5", "claude-sonnet-4-6"]),
    ("DeepSeek",         ["deepseek-chat", "deepseek-reasoner"]),
    ("OpenAI",           ["gpt-4o", "gpt-4o-mini"]),
    ("9Router",          [
        "ag/gemini-3.8-flash",
        "ag/gemini-3.8-flash-high",
        "ag/gemini-3.7-flash-high",
        "ag/gemini-3.6-flash-high",
        "ag/gemini-3.1-pro-low",
        "ag/claude-sonnet-4-6",
        "ag/gpt-oss-120b-medium",
        "gemini-3.8-flash",
    ]),
]
API_KEY_URL_FALLBACKS = {
    "Google Gemini": "https://aistudio.google.com/apikey",
    "Anthropic Claude": "https://console.anthropic.com/settings/keys",
    "DeepSeek": "https://platform.deepseek.com/api_keys",
    "OpenAI": "https://platform.openai.com/api-keys",
    "9Router": "http://localhost:20128",
}
SUBJECTS = ["Toán", "Lý", "Hóa", "Sinh", "Văn", "Anh", "Sử", "Địa", "GDCD", "Tin"]
GRADES   = [str(g) for g in range(6, 13)]


class SetupView(ctk.CTkFrame):
    """Cấu hình app: AI Provider + Subject/Grade + License."""

    def __init__(
        self,
        parent,
        *,
        on_navigate: Callable[[str], None] | None = None,
        on_license_update: Callable[[dict], None] | None = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self._on_navigate = on_navigate
        self._on_license_update = on_license_update
        self._km = get_key_manager()
        self._license_data: dict = {}
        self._key_plaintext = ""
        self._key_hidden = False
        self._build()
        # Load license async để không block UI
        threading.Thread(target=self._refresh_license, daemon=True).start()

    def _build(self):
        # Header
        ctk.CTkLabel(self, text="⚙️  Cấu hình hệ thống",
                      font=("Segoe UI", 24, "bold")
                      ).pack(anchor="w", pady=(4, 12))

        # ── Tabview 3 tabs ───────────────────────────────────────────
        self._tabs = ctk.CTkTabview(self,
                                       segmented_button_selected_color="#1F497D",
                                       segmented_button_selected_hover_color="#163D6B")
        self._tabs.pack(fill="both", expand=True)
        self._TAB_AI      = "🤖  AI Provider"
        self._TAB_SUBJECT = "📚  Môn / Lớp"
        self._TAB_LICENSE = "🪪  License"
        self._TAB_SYSTEM  = "🖥️  Hệ thống & Desktop"
        for name in (self._TAB_AI, self._TAB_SUBJECT, self._TAB_LICENSE, self._TAB_SYSTEM):
            self._tabs.add(name)

        # Build vào từng tab thay vì stack
        self._build_ai_section(self._tabs.tab(self._TAB_AI))
        self._build_subject_section(self._tabs.tab(self._TAB_SUBJECT))
        self._build_license_section(self._tabs.tab(self._TAB_LICENSE))
        self._build_system_section(self._tabs.tab(self._TAB_SYSTEM))

    # ── Public API: switch inner tab (gọi từ sidebar action) ────────────
    def focus_ai_provider(self):
        try: self._tabs.set(self._TAB_AI)
        except Exception: pass

    def focus_license(self):
        try: self._tabs.set(self._TAB_LICENSE)
        except Exception: pass

    def focus_subject(self):
        try: self._tabs.set(self._TAB_SUBJECT)
        except Exception: pass

    def focus_system(self):
        try: self._tabs.set(self._TAB_SYSTEM)
        except Exception: pass

    # ── AI Provider ───────────────────────────────────────────────────────
    def _build_ai_section(self, parent=None):
        root = parent if parent is not None else self
        scroll = ctk.CTkScrollableFrame(root, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        card = self._card("🤖  AI Provider + API Key", parent=scroll)

        # Row: provider + model
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="Provider:", width=80, anchor="w"
                      ).pack(side="left", padx=(0, 6))

        self._provider_var = ctk.StringVar(value="Google Gemini")
        self._provider_menu = ctk.CTkOptionMenu(
            row, values=[p[0] for p in PROVIDERS],
            variable=self._provider_var, width=180,
            command=self._on_provider_change)
        self._provider_menu.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row, text="Model:", width=60, anchor="w"
                      ).pack(side="left", padx=(0, 6))
        self._model_var = ctk.StringVar()
        self._model_menu = ctk.CTkOptionMenu(
            row, variable=self._model_var, width=220,
            command=self._on_model_change)
        self._model_menu.pack(side="left")
        self._on_provider_change()   # init model list

        # Row: API key
        key_head = ctk.CTkFrame(card, fg_color="transparent")
        key_head.pack(fill="x", pady=(8, 2))
        ctk.CTkLabel(key_head, text="API Key (mỗi dòng 1 key):",
                      anchor="w").pack(side="left")
        self._key_link_btn = ctk.CTkButton(
            key_head,
            text="🔗  Lấy API key",
            width=128,
            height=28,
            fg_color=("#2563EB", "#1D4ED8"),
            hover_color=("#1D4ED8", "#1E40AF"),
            command=self._open_api_key_url,
        )
        self._key_link_btn.pack(side="right")
        self._key_entry = ctk.CTkTextbox(
            card,
            height=86,
            font=("Consolas", 11),
            wrap="none",
            border_width=1,
            border_color=("#CBD5E1", "#475569"),
        )
        self._key_entry.pack(fill="x", pady=(0, 6))

        # Load saved key
        saved = self._km.load(self._provider_var.get()) or ""
        if isinstance(saved, list):
            saved = "\n".join(saved)
        self._set_key_text(saved, hidden=bool(saved))

        # Buttons row
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", pady=(4, 0))
        # Lưu key = SECONDARY (h=32) — CTA quan trọng. Hiện/Ẩn + Xoá ở
        # TERTIARY (h=28) — operational.
        ctk.CTkButton(btns, text="💾  Lưu key",
                       width=130, height=32,
                       font=("Segoe UI", 12, "bold"),
                       fg_color="#10B981", hover_color="#059669",
                       command=self._save_key,
                       ).pack(side="left", padx=(0, 6))
        self._test_btn = ctk.CTkButton(
            btns, text="⚡  Kiểm tra kết nối",
            width=140, height=32,
            font=("Segoe UI", 12, "bold"),
            fg_color="#2563EB", hover_color="#1D4ED8",
            command=self._test_connection,
        )
        self._test_btn.pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="👁  Hiện/Ẩn",
                       width=100, height=28,
                       fg_color="#6B7280", hover_color="#4B5563",
                       command=self._toggle_show_key,
                       ).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="🗑  Xoá key",
                       width=100, height=28,
                       fg_color="#EF4444", hover_color="#DC2626",
                       command=self._delete_key,
                       ).pack(side="left", padx=2)

        self._key_status = ctk.CTkLabel(card, text="", text_color="gray",
                                          font=("Segoe UI", 10))
        self._key_status.pack(anchor="w", pady=(4, 0))

        # Restore saved default provider and model from settings_store or config
        try:
            from v5 import settings_store
            from config import get_selected_ai_provider, get_selected_ai_model
            saved_prov = settings_store.get("ai_provider") or get_selected_ai_provider()
            all_provs = [p[0] for p in PROVIDERS]
            if saved_prov and saved_prov in all_provs:
                self._provider_var.set(saved_prov)
                self._on_provider_change()
                saved_model = settings_store.get("ai_model") or get_selected_ai_model(saved_prov)
                if saved_model:
                    self._model_var.set(saved_model)
        except Exception:
            pass

    def _on_model_change(self, model: str):
        prov = self._provider_var.get()
        try:
            from v5 import settings_store
            settings_store.set_value("ai_model", model)
            from config import set_selected_ai_model
            set_selected_ai_model(prov, model)
        except Exception:
            pass

    def _on_provider_change(self, *_):
        prov = self._provider_var.get()
        models = list(next((m for p, m in PROVIDERS if p == prov), []))
        self._model_menu.configure(values=models)
        if models:
            self._model_var.set(models[0])
        # Reload key cho provider mới
        if hasattr(self, "_key_entry"):
            saved = self._km.load(prov) or ""
            if isinstance(saved, list):
                saved = "\n".join(saved)
            self._set_key_text(saved, hidden=bool(saved))
            self._key_status.configure(
                text=f"  {'✓ Đã có key' if saved else '⚠ Chưa có key'}")
        if hasattr(self, "_key_link_btn"):
            state = "normal" if self._api_key_url(prov) else "disabled"
            self._key_link_btn.configure(state=state)

        # Lưu lựa chọn provider & model
        try:
            from v5 import settings_store
            settings_store.set_value("ai_provider", prov)
            target_model = self._model_var.get()
            if target_model:
                settings_store.set_value("ai_model", target_model)
            from config import set_selected_ai_provider, set_selected_ai_model
            set_selected_ai_provider(prov)
            if target_model:
                set_selected_ai_model(prov, target_model)
        except Exception:
            pass

        # Nếu là 9Router, fetch live models ngầm từ local endpoint
        if prov == "9Router":
            threading.Thread(target=self._fetch_9router_models_async, daemon=True).start()

    def _fetch_9router_models_async(self):
        try:
            import json
            import urllib.request
            from config import AI_PROVIDERS
            base_url = AI_PROVIDERS.get("9Router", {}).get("base_url", "http://localhost:20128/v1")
            url = f"{base_url.rstrip('/')}/models"
            key = self._km.load("9Router")
            if isinstance(key, list):
                key = key[0] if key else ""
            headers = {"Authorization": f"Bearer {key}"} if key else {}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m["id"] for m in data.get("data", []) if "id" in m]
                if models and self._provider_var.get() == "9Router":
                    self.after(0, lambda: self._apply_fetched_models(models))
        except Exception:
            pass

    def _apply_fetched_models(self, models: list[str]):
        if self._provider_var.get() != "9Router":
            return
        current = self._model_var.get()
        self._model_menu.configure(values=models)
        if current in models:
            self._model_var.set(current)
        elif models:
            self._model_var.set(models[0])

    def _test_connection(self):
        prov = self._provider_var.get()
        model = self._model_var.get()
        key_raw = self._get_key_text()
        from v5.toast import show_toast
        if not key_raw and prov != "9Router":
            show_toast(self.winfo_toplevel(), f"Hãy nhập API key cho {prov} trước khi kiểm tra.", kind="warn")
            return

        self._test_btn.configure(state="disabled", text="⏳ Đang kiểm tra...")
        self._key_status.configure(text=f"  ⏳ Đang kết nối tới {prov} ({model})...", text_color="#3B82F6")

        def _worker():
            import time
            from services.ai_service import create_ai_service
            from services.retry_service import split_keys
            t0 = time.time()
            try:
                keys = split_keys(key_raw) if key_raw else ["dummy_key"]
                svc = create_ai_service(prov, keys, model)
                ans = svc.generate("1+1=? Trả lời ngắn gọn số").strip()
                ms = int((time.time() - t0) * 1000)
                msg = f"✓ Kết nối thành công! (Phản hồi: {ans} trong {ms}ms)"
                self.after(0, lambda: self._on_test_done(True, msg))
            except Exception as e:
                err_str = str(e)
                if len(err_str) > 120:
                    err_str = err_str[:120] + "..."
                msg = f"✗ Lỗi kết nối: {err_str}"
                self.after(0, lambda: self._on_test_done(False, msg))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_test_done(self, ok: bool, message: str):
        self._test_btn.configure(state="normal", text="⚡  Kiểm tra kết nối")
        color = "#10B981" if ok else "#EF4444"
        self._key_status.configure(text=f"  {message}", text_color=color)
        from v5.toast import show_toast
        show_toast(self.winfo_toplevel(), message, kind="success" if ok else "error", duration=5)

    @staticmethod
    def _mask_keys(raw: str) -> str:
        parts = [p.strip() for p in re.split(r"[,\n]+", raw or "") if p.strip()]
        if not parts:
            return ""
        return "\n".join("•" * min(max(len(part), 8), 28) for part in parts)

    def _set_key_text(self, text: str, *, hidden: bool | None = None) -> None:
        self._key_plaintext = str(text or "")
        if hidden is not None:
            self._key_hidden = bool(hidden)
        display = self._mask_keys(self._key_plaintext) if self._key_hidden else self._key_plaintext
        self._key_entry.configure(state="normal")
        self._key_entry.delete("1.0", "end")
        if display:
            self._key_entry.insert("1.0", display)
        if self._key_hidden and self._key_plaintext:
            self._key_entry.configure(state="disabled")

    def _get_key_text(self) -> str:
        if self._key_hidden:
            return self._key_plaintext.strip()
        self._key_plaintext = self._key_entry.get("1.0", "end-1c")
        return self._key_plaintext.strip()

    def _api_key_url(self, provider: str) -> str:
        try:
            from config import AI_PROVIDERS
            value = AI_PROVIDERS.get(provider, {}).get("key_url", "")
            if value:
                return str(value)
        except Exception:
            pass
        return API_KEY_URL_FALLBACKS.get(provider, "")

    def _open_api_key_url(self) -> None:
        from v5.toast import show_toast
        prov = self._provider_var.get()
        url = self._api_key_url(prov)
        if not url:
            show_toast(self.winfo_toplevel(), f"Chưa có đường dẫn lấy key cho {prov}.",
                       kind="warn")
            return
        try:
            webbrowser.open(url)
            show_toast(self.winfo_toplevel(), f"Đã mở trang lấy API key {prov}.",
                       kind="info")
        except Exception as exc:
            show_toast(self.winfo_toplevel(), f"Lỗi mở đường dẫn: {exc}",
                       kind="error", duration=5)

    def _save_key(self):
        from v5.toast import show_toast
        key = self._get_key_text()
        if not key:
            show_toast(self.winfo_toplevel(), "Hãy nhập key trước.",
                       kind="warn"); return
        try:
            self._km.save(self._provider_var.get(), key)
            self._key_status.configure(text="  ✓ Đã lưu (encrypted)",
                                          text_color="#10B981")
            show_toast(self.winfo_toplevel(),
                       f"Đã lưu key {self._provider_var.get()} (Fernet)",
                       kind="success")
        except Exception as e:
            show_toast(self.winfo_toplevel(), f"Lỗi lưu key: {e}",
                       kind="error", duration=5)

    def _toggle_show_key(self):
        if not self._key_hidden:
            self._key_plaintext = self._key_entry.get("1.0", "end-1c")
        self._set_key_text(self._key_plaintext, hidden=not self._key_hidden)

    def _delete_key(self):
        if not messagebox.askyesno("Xoá", "Xoá key cho provider hiện tại?",
                                     parent=self): return
        try:
            self._km.delete(self._provider_var.get())
            self._set_key_text("", hidden=False)
            self._key_status.configure(text="  ✓ Đã xoá", text_color="gray")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    # ── Subject / Grade ───────────────────────────────────────────────────
    def _build_subject_section(self, parent=None):
        root = parent if parent is not None else self
        scroll = ctk.CTkScrollableFrame(root, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)
        card = self._card("📚  Môn / Lớp / Học kỳ", parent=scroll)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", pady=4)

        ctk.CTkLabel(row, text="Môn:", width=60).pack(side="left", padx=(0, 6))
        self._subject_var = ctk.StringVar(value="Toán")
        ctk.CTkOptionMenu(row, values=SUBJECTS, variable=self._subject_var,
                            width=120).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row, text="Lớp:", width=40).pack(side="left", padx=(0, 6))
        self._grade_var = ctk.StringVar(value="12")
        ctk.CTkOptionMenu(row, values=GRADES, variable=self._grade_var,
                            width=80).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(row, text="HK:", width=40).pack(side="left", padx=(0, 6))
        self._semester_var = ctk.StringVar(value="II")
        ctk.CTkOptionMenu(row, values=["I", "II"], variable=self._semester_var,
                            width=70).pack(side="left")

    # ── License ───────────────────────────────────────────────────────────
    def _build_license_section(self, parent=None):
        root = parent if parent is not None else self
        scroll = ctk.CTkScrollableFrame(root, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        hero = ctk.CTkFrame(scroll, fg_color=("#E0F2FE", "#0F172A"),
                            corner_radius=14, border_width=1,
                            border_color=("#BAE6FD", "#334155"))
        hero.pack(fill="x", pady=(0, 12))
        hero.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hero, text="👤", width=58,
                      font=("Segoe UI", 28)).grid(row=0, column=0,
                                                   rowspan=2, padx=16, pady=14)
        self._lic_status_lbl = ctk.CTkLabel(
            hero, text="⏳ Đang kiểm tra license...",
            font=("Segoe UI", 18, "bold"), anchor="w")
        self._lic_status_lbl.grid(row=0, column=1, sticky="ew",
                                  padx=(0, 14), pady=(14, 2))
        self._lic_tier_lbl = ctk.CTkLabel(
            hero, text="Đang đồng bộ thông tin người dùng",
            font=("Segoe UI", 11), anchor="w", text_color="gray")
        self._lic_tier_lbl.grid(row=1, column=1, sticky="ew",
                                padx=(0, 14), pady=(0, 14))

        machine_card = self._card("💻  Mã máy & nguồn license", parent=scroll)
        self._machine_id_var = ctk.StringVar(value=get_machine_id())
        machine_row = ctk.CTkFrame(machine_card, fg_color="transparent")
        machine_row.pack(fill="x", pady=(0, 6))
        self._lic_machine_entry = ctk.CTkEntry(
            machine_row, textvariable=self._machine_id_var,
            font=("Consolas", 11), height=32)
        self._lic_machine_entry.pack(side="left", fill="x", expand=True,
                                     padx=(0, 8))
        self._lic_machine_entry.configure(state="disabled")
        ctk.CTkButton(machine_row, text="📋 Copy mã máy",
                       width=132, height=32,
                       command=self._copy_machine_id
                       ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(machine_row, text="📋 Copy hỗ trợ",
                       width=132, height=32,
                       fg_color="#6B7280", hover_color="#4B5563",
                       command=self._copy_support_info
                       ).pack(side="left")

        self._lic_display_lbl = ctk.CTkLabel(
            machine_card, text=get_machine_display(),
            font=("Segoe UI", 10), anchor="w", text_color="gray",
            justify="left")
        self._lic_display_lbl.pack(anchor="w", pady=2)
        self._lic_source_lbl = ctk.CTkLabel(
            machine_card, text="Nguồn: đang kiểm tra",
            font=("Segoe UI", 10), anchor="w", text_color="gray")
        self._lic_source_lbl.pack(anchor="w", pady=2)

        expiry_card = self._card("⏳  Thời hạn sử dụng", parent=scroll)
        self._lic_expiry_lbl = ctk.CTkLabel(
            expiry_card, text="Đang kiểm tra...",
            font=("Segoe UI", 15, "bold"), anchor="w")
        self._lic_expiry_lbl.pack(anchor="w", pady=(0, 2))
        self._lic_expiry_detail_lbl = ctk.CTkLabel(
            expiry_card, text="", font=("Segoe UI", 10),
            text_color="gray", anchor="w", justify="left")
        self._lic_expiry_detail_lbl.pack(anchor="w", pady=(0, 8))
        self._lic_expiry_bar = ctk.CTkProgressBar(expiry_card, height=10)
        self._lic_expiry_bar.pack(fill="x", pady=(0, 2))
        self._lic_expiry_bar.set(0)

        feature_card = self._card("🎁  Quyền tính năng theo gói", parent=scroll)
        self._lic_feature_summary_lbl = ctk.CTkLabel(
            feature_card, text="Đang tải danh sách quyền...",
            font=("Segoe UI", 11, "bold"), anchor="w", justify="left")
        self._lic_feature_summary_lbl.pack(anchor="w", pady=(0, 8))
        self._lic_feature_box = ctk.CTkFrame(
            feature_card, fg_color=("#F8FAFC", "#111827"),
            corner_radius=8)
        self._lic_feature_box.pack(fill="both", expand=True)

        detail_card = self._card("📞  Liên hệ & thao tác", parent=scroll)
        self._lic_detail_lbl = ctk.CTkLabel(
            detail_card,
            text="Zalo/SĐT: 033.999.8261\nEmail: dominh200270@gmail.com",
            font=("Segoe UI", 10), anchor="w", text_color="gray",
            justify="left")
        self._lic_detail_lbl.pack(anchor="w", pady=(0, 8))
        btns = ctk.CTkFrame(detail_card, fg_color="transparent")
        btns.pack(fill="x")
        ctk.CTkButton(btns, text="🔄 Refresh license online",
                       width=190, height=34,
                       command=lambda: threading.Thread(
                           target=self._refresh_license, daemon=True).start()
                       ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="🪪 Focus license",
                       width=130, height=34,
                       fg_color="#6B7280", hover_color="#4B5563",
                       command=self.focus_license
                       ).pack(side="left")

    def _copy_machine_id(self):
        mid = self._machine_id_var.get() if hasattr(self, "_machine_id_var") else get_machine_id()
        self.clipboard_clear()
        self.clipboard_append(mid)
        from v5.toast import show_toast
        show_toast(self.winfo_toplevel(), "Đã copy mã máy để gửi admin.", kind="success")

    def _copy_support_info(self):
        mid = self._machine_id_var.get() if hasattr(self, "_machine_id_var") else get_machine_id()
        text = support_text(
            self._license_data,
            machine_id=mid,
            machine_display=get_machine_display(),
        )
        self.clipboard_clear()
        self.clipboard_append(text)
        from v5.toast import show_toast
        show_toast(self.winfo_toplevel(), "Đã copy thông tin hỗ trợ.", kind="success")

    def _render_feature_rows(self, rows: list[dict]):
        if not hasattr(self, "_lic_feature_box"):
            return
        for child in self._lic_feature_box.winfo_children():
            child.destroy()
        for row in rows:
            enabled = bool(row.get("enabled"))
            color = "#10B981" if enabled else "#EF4444"
            icon = "✓" if enabled else "✕"
            note = "admin override" if row.get("override") else row.get("source", "")
            item = ctk.CTkFrame(self._lic_feature_box, fg_color="transparent")
            item.pack(fill="x", padx=8, pady=3)
            ctk.CTkLabel(item, text=icon, width=24,
                          font=("Segoe UI", 12, "bold"),
                          text_color=color).pack(side="left")
            ctk.CTkLabel(item, text=str(row.get("label") or row.get("key")),
                          anchor="w", font=("Segoe UI", 10)
                          ).pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(item, text=str(note),
                          width=110, anchor="e", text_color="gray",
                          font=("Segoe UI", 9)).pack(side="right")

    def _refresh_license(self):
        info = check_license(force_online=True)
        # Push UI update vào main thread (safe_after kiểm widget tồn tại)
        from v5.safe_ui import safe_after
        def _apply():
            self._update_license_ui(info)
            if callable(self._on_license_update):
                self._on_license_update(info)
        safe_after(self, 0, _apply)

    def _update_license_ui(self, info: dict):
        # Nếu view đã destroy (user navigate sang view khác) → bỏ qua
        try:
            if not self.winfo_exists(): return
        except Exception: return
        try:
            self._do_update_license_ui(info)
        except Exception as e:
            import tkinter as tk
            if not isinstance(e, tk.TclError):
                print(f"_update_license_ui fail: {e}")
            # TclError = widget destroyed → silent

    def _do_update_license_ui(self, info: dict):
        self._license_data = info or {}
        data = self._license_data
        mid = str(data.get("mid") or data.get("machine_id") or get_machine_id())
        display = get_machine_display()
        if hasattr(self, "_machine_id_var"):
            self._machine_id_var.set(mid)
        if hasattr(self, "_lic_display_lbl"):
            self._lic_display_lbl.configure(text=display)

        if data.get("ok"):
            tier = tier_key(data)
            name = data.get("name") or "Khách"
            self._lic_status_lbl.configure(
                text=f"✓ {name}",
                text_color=tier_color(data))
            if hasattr(self, "_lic_tier_lbl"):
                self._lic_tier_lbl.configure(
                    text=f"{tier.upper()} - {tier_label(data)}")
        else:
            status = str(data.get("status") or "error")
            self._lic_status_lbl.configure(text=f"✕ {status}", text_color="#EF4444")
            if hasattr(self, "_lic_tier_lbl"):
                self._lic_tier_lbl.configure(
                    text=str(data.get("message") or "License chưa được xác minh."))

        if hasattr(self, "_lic_source_lbl"):
            self._lic_source_lbl.configure(
                text=f"Nguồn: {license_source_label(data)}")

        expiry = expiry_status(data.get("expiry"))
        if hasattr(self, "_lic_expiry_lbl"):
            self._lic_expiry_lbl.configure(
                text=expiry["title"], text_color=expiry["color"])
        if hasattr(self, "_lic_expiry_detail_lbl"):
            self._lic_expiry_detail_lbl.configure(text=expiry["detail"])
        if hasattr(self, "_lic_expiry_bar"):
            self._lic_expiry_bar.set(float(expiry["progress"]) / 100.0)
            self._lic_expiry_bar.configure(progress_color=expiry["color"])

        rows = feature_rows(data)
        enabled, total = feature_count(data)
        if hasattr(self, "_lic_feature_summary_lbl"):
            self._lic_feature_summary_lbl.configure(
                text=f"Đang bật {enabled}/{total} tính năng - {tier_label(data)}")
        self._render_feature_rows(rows)

        if hasattr(self, "_lic_detail_lbl"):
            self._lic_detail_lbl.configure(
                text="Zalo/SĐT: 033.999.8261\n"
                     "Email: dominh200270@gmail.com\n"
                     "Copy mã máy hoặc thông tin hỗ trợ khi cần kích hoạt/gia hạn.")

    # ── System & Desktop Section ──────────────────────────────────────────
    def _build_system_section(self, parent=None):
        root = parent if parent is not None else self
        scroll = ctk.CTkScrollableFrame(root, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        from services.desktop_shortcut import (
            has_desktop_shortcut,
            get_primary_desktop,
            resolve_app_executable,
            open_install_directory,
        )

        # Card 1: Desktop shortcut
        card_desk = self._card("🖥️  Màn hình chính (Desktop Shortcut)", parent=scroll)
        ctk.CTkLabel(
            card_desk,
            text="Tạo biểu tượng lối tắt trên Desktop để mở MEA v5 nhanh chóng mà không cần dò tìm file trong ổ đĩa.",
            font=("Segoe UI", 11),
            text_color="gray",
            anchor="w",
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        has_icon = has_desktop_shortcut()
        self._shortcut_status_lbl = ctk.CTkLabel(
            card_desk,
            text="✓ Đã có biểu tượng trên Màn hình chính (Desktop)" if has_icon else "⚠ Chưa có biểu tượng trên Màn hình chính",
            font=("Segoe UI", 11, "bold"),
            text_color="#10B981" if has_icon else "#F59E0B",
            anchor="w",
        )
        self._shortcut_status_lbl.pack(anchor="w", pady=(0, 4))

        desk_dir = get_primary_desktop()
        ctk.CTkLabel(
            card_desk,
            text=f"Đường dẫn Desktop: {desk_dir}",
            font=("Segoe UI", 9),
            text_color="gray",
            anchor="w",
        ).pack(anchor="w", pady=(0, 10))

        desk_btns = ctk.CTkFrame(card_desk, fg_color="transparent")
        desk_btns.pack(fill="x", pady=(2, 0))

        ctk.CTkButton(
            desk_btns,
            text="📌  Thêm vào Màn hình chính (Desktop)",
            width=270,
            height=34,
            font=("Segoe UI", 11, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            command=self._create_desktop_shortcut_action,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            desk_btns,
            text="📂  Mở Desktop",
            width=120,
            height=34,
            fg_color=("#6B7280", "#374151"),
            command=self._open_desktop_folder_action,
        ).pack(side="left")

        # Card 2: Install location & Data
        card_dir = self._card("📁  Thư mục cài đặt & Dữ liệu phần mềm", parent=scroll)
        exe_path, work_dir = resolve_app_executable()
        ctk.CTkLabel(
            card_dir,
            text=f"File đang chạy: {exe_path.name}\nThư mục cài đặt: {work_dir}",
            font=("Consolas", 10),
            anchor="w",
            justify="left",
            text_color="gray",
        ).pack(anchor="w", pady=(0, 8))

        dir_btns = ctk.CTkFrame(card_dir, fg_color="transparent")
        dir_btns.pack(fill="x", pady=(2, 0))

        ctk.CTkButton(
            dir_btns,
            text="📂  Mở thư mục cài đặt app",
            width=200,
            height=32,
            command=open_install_directory,
        ).pack(side="left", padx=(0, 8))

        from config import APP_DIR
        ctk.CTkButton(
            dir_btns,
            text="📂  Mở thư mục dữ liệu cá nhân",
            width=220,
            height=32,
            fg_color=("#6B7280", "#374151"),
            command=lambda: os.startfile(str(APP_DIR)) if hasattr(os, "startfile") else None,
        ).pack(side="left")

        # Card 3: Installer notes
        card_info = self._card("ℹ️  Bộ cài đặt chuẩn Windows", parent=scroll)
        ctk.CTkLabel(
            card_info,
            text="Phiên bản cài đặt chính thức (MEA_v5_Setup.exe) được thiết kế theo tiêu chuẩn phần mềm lớn trên Windows:\n"
                 "  • Tự động cài đặt sâu vào ổ C tại: C:\\Program Files\\MEA_v5\n"
                 "  • Tự động tạo biểu tượng ngoài Màn hình chính (Desktop) và Menu Start\n"
                 "  • Hỗ trợ gỡ cài đặt sạch sẽ trong Windows Settings / Control Panel\n"
                 "  • Người dùng không rành công nghệ chỉ cần tải bộ cài, bấm Tiếp tục (Next) là sử dụng được ngay.",
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
            text_color="gray",
        ).pack(anchor="w", pady=4)

    def _create_desktop_shortcut_action(self):
        from services.desktop_shortcut import create_desktop_shortcut
        ok, msg = create_desktop_shortcut()
        from v5.toast import show_toast
        if ok:
            show_toast(self.winfo_toplevel(), "Đã thêm lối tắt vào Màn hình chính (Desktop) thành công!", kind="success", duration=4)
            if hasattr(self, "_shortcut_status_lbl"):
                self._shortcut_status_lbl.configure(
                    text="✓ Đã có biểu tượng trên Màn hình chính (Desktop)",
                    text_color="#10B981"
                )
        else:
            show_toast(self.winfo_toplevel(), f"Không thể tạo lối tắt: {msg}", kind="error", duration=5)

    def _open_desktop_folder_action(self):
        from services.desktop_shortcut import get_primary_desktop
        desk = get_primary_desktop()
        if hasattr(os, "startfile"):
            os.startfile(str(desk))

    # ── Card helper ───────────────────────────────────────────────────────
    def _card(self, title: str, parent=None) -> ctk.CTkFrame:
        p = parent if parent is not None else self
        outer = ctk.CTkFrame(p, fg_color=("white", "#293548"),
                                corner_radius=10, border_width=1,
                                border_color=("#E5E7EB", "#334155"))
        outer.pack(fill="x", pady=(8, 12))
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(inner, text=title,
                      font=("Segoe UI", 13, "bold"),
                      anchor="w").pack(anchor="w", pady=(0, 8))
        return inner

    # ── Public API (cho view khác lấy state) ──────────────────────────────
    def get_provider(self) -> str: return self._provider_var.get()
    def get_model(self) -> str:    return self._model_var.get()
    def get_subject(self) -> str:  return self._subject_var.get()
    def get_grade(self) -> str:    return self._grade_var.get()
