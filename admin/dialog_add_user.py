"""
admin/dialog_add_user.py — Hộp thoại cấp quyền truy cập mới cho người dùng MEA.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from config import SUPABASE_URL, SUPABASE_KEY
from admin.constants import TIER_STYLES, TIER_OFF_BG, TIER_OFF_FG
from admin.date_picker import ExpiryEditor
from admin.supabase_api import update_api_key
from services.license_manager import admin_add


class AddUserDialog(tk.Toplevel):
    """Hộp thoại Cấp quyền truy cập mới — Giao diện thoáng đãng, chuyên nghiệp."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self.title("➕ Cấp Quyền Truy Cập Mới — MEA Admin")
        self.geometry("620x680")
        self.minsize(560, 600)
        self.configure(bg="#F4F8F7")
        self.grab_set()
        self.focus_force()

        # Center on parent window
        self.update_idletasks()
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            w = 620
            h = 680
            x = max(0, px + (pw - w) // 2)
            y = max(0, py + (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────────
        header = tk.Frame(self, bg="#0B2F33", height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        htext = tk.Frame(header, bg="#0B2F33")
        htext.pack(side="left", padx=20, pady=10)
        tk.Label(
            htext,
            text="➕ CẤP QUYỀN TRUY CẬP MỚI",
            font=("Segoe UI", 13, "bold"),
            fg="white",
            bg="#0B2F33",
        ).pack(anchor="w")
        tk.Label(
            htext,
            text="Thêm giấy phép sử dụng MEA cho máy tính giáo viên / người dùng",
            font=("Segoe UI", 9),
            fg="#9CC9C3",
            bg="#0B2F33",
        ).pack(anchor="w")

        # ── Scrollable Body ──────────────────────────────────────────────────
        container = tk.Frame(self, bg="#F4F8F7")
        container.pack(fill="both", expand=True, padx=18, pady=14)

        # 1. Card: Machine ID
        mid_card = tk.Frame(container, bg="white", highlightbackground="#D8E4E0", highlightthickness=1)
        mid_card.pack(fill="x", pady=(0, 10))
        
        mid_inner = tk.Frame(mid_card, bg="white", padx=16, pady=12)
        mid_inner.pack(fill="x")
        
        lbl_mid_row = tk.Frame(mid_inner, bg="white")
        lbl_mid_row.pack(fill="x", pady=(0, 6))
        tk.Label(lbl_mid_row, text="Machine ID", font=("Segoe UI", 10, "bold"), fg="#17313A", bg="white").pack(side="left")
        tk.Label(lbl_mid_row, text=" * (Bắt buộc)", font=("Segoe UI", 9, "bold"), fg="#DC2626", bg="white").pack(side="left")

        input_row = tk.Frame(mid_inner, bg="white")
        input_row.pack(fill="x")
        self._mid_var = tk.StringVar()
        self._mid_entry = ttk.Entry(input_row, textvariable=self._mid_var, font=("Consolas", 12, "bold"))
        self._mid_entry.pack(side="left", fill="x", expand=True, ipady=4)
        
        paste_btn = tk.Button(
            input_row,
            text="📋 Dán từ Clipboard",
            font=("Segoe UI", 9, "bold"),
            bg="#E2E8F0",
            fg="#1E293B",
            activebackground="#CBD5E1",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self._paste_mid,
        )
        paste_btn.pack(side="left", padx=(8, 0))

        # 2. Card: User Details
        info_card = tk.Frame(container, bg="white", highlightbackground="#D8E4E0", highlightthickness=1)
        info_card.pack(fill="x", pady=(0, 10))
        
        info_inner = tk.Frame(info_card, bg="white", padx=16, pady=12)
        info_inner.pack(fill="x")
        info_inner.columnconfigure((0, 1), weight=1)

        # Name
        tk.Label(info_inner, text="Tên người dùng / Giáo viên:", font=("Segoe UI", 10, "bold"), fg="#17313A", bg="white").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 4))
        self._name_var = tk.StringVar()
        ttk.Entry(info_inner, textvariable=self._name_var, font=("Segoe UI", 10)).grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 10), ipady=3)

        # Note
        tk.Label(info_inner, text="Ghi chú (Trường / Lớp / Liên hệ):", font=("Segoe UI", 10, "bold"), fg="#17313A", bg="white").grid(row=0, column=1, sticky="w", padx=(8, 0), pady=(0, 4))
        self._note_var = tk.StringVar()
        ttk.Entry(info_inner, textvariable=self._note_var, font=("Segoe UI", 10)).grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 10), ipady=3)

        # 3. Card: Tier Selector
        tier_card = tk.Frame(container, bg="white", highlightbackground="#D8E4E0", highlightthickness=1)
        tier_card.pack(fill="x", pady=(0, 10))

        tier_inner = tk.Frame(tier_card, bg="white", padx=16, pady=12)
        tier_inner.pack(fill="x")
        tk.Label(tier_inner, text="Gói dịch vụ (Tier):", font=("Segoe UI", 10, "bold"), fg="#17313A", bg="white").pack(anchor="w", pady=(0, 8))

        tier_btns_frame = tk.Frame(tier_inner, bg="white")
        tier_btns_frame.pack(fill="x")
        tier_btns_frame.columnconfigure((0, 1, 2), weight=1)

        self._tier_var = tk.StringVar(value="pro")
        self._tier_widgets: dict[str, tk.Label] = {}

        tiers_info = [
            ("basic", "🥉 BASIC", "2 đề/ngày\nTự nhập API key", "#64748B"),
            ("pro", "🥈 PRO (Khuyên dùng)", "Không giới hạn đề\nTích hợp sẵn API", "#2563EB"),
            ("premium", "🏆 PREMIUM", "Full tính năng AI\nƯu tiên hỗ trợ", "#7C3AED"),
        ]

        def _select_tier(t: str):
            self._tier_var.set(t)
            for k, (lbl, active_color) in self._tier_widgets.items():
                if k == t:
                    lbl.configure(bg=active_color, fg="white", relief="solid", bd=2)
                else:
                    lbl.configure(bg="#F1F5F9", fg="#475569", relief="flat", bd=1)

        for idx, (t_key, t_title, t_desc, t_color) in enumerate(tiers_info):
            is_active = (t_key == "pro")
            t_box = tk.Label(
                tier_btns_frame,
                text=f"{t_title}\n{t_desc}",
                font=("Segoe UI", 9, "bold"),
                bg=t_color if is_active else "#F1F5F9",
                fg="white" if is_active else "#475569",
                relief="solid" if is_active else "flat",
                bd=2 if is_active else 1,
                cursor="hand2",
                padx=8,
                pady=8,
                justify="center",
            )
            t_box.grid(row=0, column=idx, sticky="ew", padx=4 if idx == 1 else 0)
            t_box.bind("<Button-1>", lambda _e, k=t_key: _select_tier(k))
            self._tier_widgets[t_key] = (t_box, t_color)

        # 4. Card: Expiry & API Key
        exp_card = tk.Frame(container, bg="white", highlightbackground="#D8E4E0", highlightthickness=1)
        exp_card.pack(fill="x", pady=(0, 10))

        exp_inner = tk.Frame(exp_card, bg="white", padx=16, pady=12)
        exp_inner.pack(fill="x")

        tk.Label(exp_inner, text="Hạn sử dụng:", font=("Segoe UI", 10, "bold"), fg="#17313A", bg="white").pack(anchor="w", pady=(0, 6))
        self._expiry_editor = ExpiryEditor(exp_inner, bg="white", day_default=45)
        self._expiry_editor.pack(fill="x", pady=(0, 10))

        tk.Label(exp_inner, text="Admin API Key (tùy chọn - cấp riêng cho user này):", font=("Segoe UI", 9, "bold"), fg="#475569", bg="white").pack(anchor="w", pady=(4, 4))
        self._admin_key_var = tk.StringVar()
        ttk.Entry(exp_inner, textvariable=self._admin_key_var, font=("Consolas", 10)).pack(fill="x", ipady=3)

        # ── Footer Actions ───────────────────────────────────────────────────
        footer = tk.Frame(self, bg="#E8F0ED", height=60)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        btn_box = tk.Frame(footer, bg="#E8F0ED")
        btn_box.pack(side="right", padx=18, pady=10)

        cancel_btn = tk.Button(
            btn_box,
            text="Hủy bỏ",
            font=("Segoe UI", 10),
            bg="#D1D5DB",
            fg="#1F2937",
            activebackground="#9CA3AF",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=6,
            command=self.destroy,
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        submit_btn = tk.Button(
            btn_box,
            text="  ➕ CẤP QUYỀN NGAY  ",
            font=("Segoe UI", 10, "bold"),
            bg="#0F9F6E",
            fg="white",
            activebackground="#0B7A54",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=6,
            command=self._do_add,
        )
        submit_btn.pack(side="left")

        # Focus entry
        self.after(100, lambda: self._mid_entry.focus_set())

    def _paste_mid(self):
        try:
            val = self.clipboard_get().strip()
            if val:
                self._mid_var.set(val.upper())
        except Exception:
            pass

    def _do_add(self):
        mid = self._mid_var.get().strip().upper()
        name = self._name_var.get().strip() or "Không rõ"
        note = self._note_var.get().strip()
        tier = self._tier_var.get()

        if not mid:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Machine ID của người dùng.", parent=self)
            self._mid_entry.focus_set()
            return

        try:
            exp = self._expiry_editor.get_iso_value()
        except ValueError:
            messagebox.showerror(
                "Sai định dạng ngày",
                "Ngày hết hạn phải theo định dạng DD-MM-YYYY (VD: 31-12-2026).",
                parent=self,
            )
            return

        admin_key = self._admin_key_var.get().strip()
        self._app.set_status(f"⏳ Đang cấp quyền cho {mid}...")
        try:
            result = admin_add(mid, name, tier, note, exp)
            if result.get("ok"):
                if SUPABASE_URL and SUPABASE_KEY and admin_key:
                    update_api_key(mid, admin_key)
                self._app.set_status(f"✅ Đã cấp quyền thành công cho [{name}] ({mid})")
                messagebox.showinfo(
                    "Thành công",
                    f"Đã cấp quyền truy cập thành công!\n\n"
                    f"• Người dùng: {name}\n"
                    f"• Machine ID: {mid}\n"
                    f"• Gói: {tier.upper()}\n"
                    f"• Hạn sử dụng: {exp or 'Vĩnh viễn'}",
                    parent=self._app,
                )
                self.destroy()
                self._app.refresh()
            else:
                messagebox.showwarning("Lỗi cấp quyền", result.get("error", "Không thể thêm."), parent=self)
                self._app.set_status("⚠️ Thêm thất bại")
        except Exception as exc:
            messagebox.showerror("Lỗi hệ thống", str(exc), parent=self)
            self._app.set_status(f"❌ Lỗi: {exc}")
