"""
v5/views/lms.py — Tab LMS: cấu hình URL, login, push đề lên Web LMS.

Modern UI version của ui/tab_lms_link.py (v4). Reuse:
    services.api_client — login + JWT + sync_exam
"""
from __future__ import annotations

import threading
from typing import Callable

import customtkinter as ctk
from tkinter import messagebox

from services import api_client


class LMSView(ctk.CTkFrame):
    """Kết nối Web LMS qua FastAPI Backend."""

    def __init__(self, parent, *, on_navigate: Callable[[str], None] | None = None):
        super().__init__(parent, fg_color="transparent")
        self._on_navigate = on_navigate
        self._build()
        self._refresh_status()

    def _build(self):
        ctk.CTkLabel(self, text="🌐  Kết nối Web LMS",
                      font=("Segoe UI", 24, "bold")
                      ).pack(anchor="w", pady=(4, 16))

        # ── 1. URL ─────────────────────────────────────────────────────
        card_url = self._card("1️⃣  Cấu hình Backend URL")
        row = ctk.CTkFrame(card_url, fg_color="transparent")
        row.pack(fill="x")
        ctk.CTkLabel(row, text="API URL:", width=80).pack(side="left",
                                                              padx=(0, 6))
        self._url_var = ctk.StringVar(value=api_client.api_url()
                                              or "http://localhost:8000")
        ctk.CTkEntry(row, textvariable=self._url_var, width=400,
                       font=("Consolas", 11)
                       ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(row, text="💾 Lưu", width=80,
                       command=self._save_url
                       ).pack(side="left", padx=2)
        ctk.CTkButton(row, text="🩺 Test", width=80,
                       fg_color="#6B7280", hover_color="#4B5563",
                       command=self._test_conn
                       ).pack(side="left", padx=2)
        self._url_status = ctk.CTkLabel(card_url, text="",
                                          font=("Segoe UI", 10, "italic"),
                                          text_color="gray")
        self._url_status.pack(anchor="w", pady=(6, 0))

        # ── 2. Login ────────────────────────────────────────────────────
        card_login = self._card("2️⃣  Đăng nhập tài khoản LMS")
        row1 = ctk.CTkFrame(card_login, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(row1, text="Email:", width=80).pack(side="left",
                                                             padx=(0, 6))
        self._email_var = ctk.StringVar()
        ctk.CTkEntry(row1, textvariable=self._email_var, width=300
                       ).pack(side="left")

        row2 = ctk.CTkFrame(card_login, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(row2, text="Password:", width=80).pack(side="left",
                                                                padx=(0, 6))
        self._pwd_var = ctk.StringVar()
        ctk.CTkEntry(row2, textvariable=self._pwd_var, width=300, show="•"
                       ).pack(side="left")

        row3 = ctk.CTkFrame(card_login, fg_color="transparent")
        row3.pack(fill="x")
        # Đăng nhập = PRIMARY tier (h=40, font 13 bold) — CTA quan trọng nhất
        # của LMS view. Logout giữ SECONDARY (32) — phụ thuộc đăng nhập.
        self._login_btn = ctk.CTkButton(
            row3, text="🔑  Đăng nhập",
            width=170, height=40,
            font=("Segoe UI", 13, "bold"),
            fg_color="#10B981", hover_color="#059669",
            command=self._do_login)
        self._login_btn.pack(side="left", padx=(0, 6))
        self._logout_btn = ctk.CTkButton(
            row3, text="🚪 Đăng xuất", state="disabled",
            width=140, height=32,
            font=("Segoe UI", 12, "bold"),
            fg_color="#EF4444", hover_color="#DC2626",
            command=self._do_logout)
        self._logout_btn.pack(side="left", padx=2)
        self._login_status = ctk.CTkLabel(
            card_login, text="", font=("Segoe UI", 11, "bold"),
            text_color="gray")
        self._login_status.pack(anchor="w", pady=(6, 0))

        # ── 3. Push exam ────────────────────────────────────────────────
        card_push = self._card("3️⃣  Đồng bộ dữ liệu lên LMS")
        ctk.CTkLabel(card_push,
                      text="✓ Push đề đã hoạt động trực tiếp trong v5!\n\n"
                           "Cách dùng: vào ✏️ Tạo đề → tạo/khôi phục đề → nút "
                           "'🚀 Push lên LMS'. Ảnh local sẽ tự upload Storage "
                           "trước khi publish. Token JWT chia sẻ qua "
                           "~/.exam_generator/lms.json.",
                      font=("Segoe UI", 11), text_color="gray",
                      justify="left", anchor="w"
                      ).pack(anchor="w", pady=(0, 4))
        ctk.CTkButton(card_push, text="✏️  Tới Tạo đề để push",
                        width=200,
                        command=lambda: (self._on_navigate("exam_create")
                                          if self._on_navigate else None)
                        ).pack(anchor="w", pady=(0, 8))

        # ── Log ─────────────────────────────────────────────────────────
        card_log = self._card("📋  Log hoạt động")
        self._log_box = ctk.CTkTextbox(card_log, height=140,
                                          font=("Consolas", 10),
                                          fg_color=("#0F172A", "#0F172A"),
                                          text_color="#E2E8F0")
        self._log_box.pack(fill="both", expand=True)
        self._log_box.configure(state="disabled")

    # ── Actions ───────────────────────────────────────────────────────────
    def _log(self, msg: str, level: str = "info"):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        color = {"info": "🔵", "success": "✅", "error": "❌", "warn": "⚠️"}.get(level, "")
        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"[{ts}] {color} {msg}\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _save_url(self):
        url = self._url_var.get().strip().rstrip("/")
        if not url:
            messagebox.showwarning("Trống", "Nhập URL trước.", parent=self)
            return
        try:
            api_client.save_api_url(url)
            self._log(f"Lưu MEA_API_URL = {url}", "success")
        except Exception as e:
            self._log(f"Lưu .env lỗi: {e}", "error")
        self._refresh_status()

    def _test_conn(self):
        self._url_status.configure(text="⏳ Đang test…",
                                      text_color="#3B82F6")
        def _do():
            ok = api_client.is_api_reachable()
            self.after(0, lambda: (
                self._url_status.configure(
                    text=("✓ Backend OK" if ok else "✘ Không kết nối được"),
                    text_color=("#10B981" if ok else "#EF4444")),
                self._log(f"Test backend → {'OK' if ok else 'FAIL'}",
                            "success" if ok else "error")))
        threading.Thread(target=_do, daemon=True).start()

    def _do_login(self):
        email = self._email_var.get().strip()
        pwd = self._pwd_var.get()
        if not email or not pwd:
            messagebox.showwarning("Trống", "Nhập email + password.",
                                     parent=self); return
        self._login_btn.configure(state="disabled")
        self._log(f"Đăng nhập {email}…", "info")
        def _do():
            res = api_client.login(email, pwd)
            self.after(0, lambda: self._on_login_done(res))
        threading.Thread(target=_do, daemon=True).start()

    def _on_login_done(self, res: dict):
        self._login_btn.configure(state="normal")
        if res.get("ok"):
            self._log(f"Đăng nhập OK ({res.get('email')})", "success")
            self._pwd_var.set("")
            self._refresh_status()
        else:
            self._log(f"Lỗi: {res.get('error', '?')[:200]}", "error")
            messagebox.showerror("Đăng nhập thất bại",
                                  res.get("error", "?"), parent=self)

    def _do_logout(self):
        api_client.clear_token()
        self._log("Đã đăng xuất", "info")
        self._refresh_status()

    def _refresh_status(self):
        logged = api_client.is_logged_in()
        tok = api_client.load_token()
        if logged:
            self._login_status.configure(
                text=f"✓ Đã đăng nhập: {tok.get('email', '?')}",
                text_color="#10B981")
            self._login_btn.configure(state="disabled")
            self._logout_btn.configure(state="normal")
        else:
            self._login_status.configure(
                text="✘ Chưa đăng nhập", text_color="gray")
            self._login_btn.configure(state="normal")
            self._logout_btn.configure(state="disabled")

    def _card(self, title: str) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(self, fg_color=("white", "#293548"),
                                corner_radius=10, border_width=1,
                                border_color=("#E5E7EB", "#334155"))
        outer.pack(fill="x", pady=(0, 12))
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=12)
        ctk.CTkLabel(inner, text=title,
                      font=("Segoe UI", 13, "bold"),
                      anchor="w").pack(anchor="w", pady=(0, 8))
        return inner
