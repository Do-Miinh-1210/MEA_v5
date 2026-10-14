"""
admin/dialog_lookup.py — Hộp thoại tra cứu nhanh trạng thái Machine ID.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from admin.constants import TIER_LABELS


class LookupUserDialog(tk.Toplevel):
    """Hộp thoại tra cứu thông tin chi tiết một Machine ID."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self.title("🔍 Tra Cứu Trạng Thái Machine ID — MEA Admin")
        self.geometry("540x440")
        self.minsize(480, 380)
        self.configure(bg="#F4F8F7")
        self.grab_set()
        self.focus_force()

        # Center on parent
        self.update_idletasks()
        try:
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            w = 540
            h = 440
            x = max(0, px + (pw - w) // 2)
            y = max(0, py + (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────────
        header = tk.Frame(self, bg="#0B2F33", height=56)
        header.pack(fill="x")
        header.pack_propagate(False)

        htext = tk.Frame(header, bg="#0B2F33")
        htext.pack(side="left", padx=18, pady=8)
        tk.Label(
            htext,
            text="🔍 TRA CỨU TRẠNG THÁI MACHINE ID",
            font=("Segoe UI", 12, "bold"),
            fg="white",
            bg="#0B2F33",
        ).pack(anchor="w")

        # ── Search input ──────────────────────────────────────────────────────
        body = tk.Frame(self, bg="#F4F8F7", padx=18, pady=14)
        body.pack(fill="both", expand=True)

        input_card = tk.Frame(body, bg="white", highlightbackground="#D8E4E0", highlightthickness=1, padx=14, pady=12)
        input_card.pack(fill="x", pady=(0, 12))

        tk.Label(input_card, text="Nhập hoặc dán Machine ID cần tra cứu:", font=("Segoe UI", 10, "bold"), fg="#17313A", bg="white").pack(anchor="w", pady=(0, 6))

        irow = tk.Frame(input_card, bg="white")
        irow.pack(fill="x")

        self._mid_var = tk.StringVar()
        self._entry = ttk.Entry(irow, textvariable=self._mid_var, font=("Consolas", 11, "bold"))
        self._entry.pack(side="left", fill="x", expand=True, ipady=4)
        self._entry.bind("<Return>", lambda _e: self._do_check())

        paste_btn = tk.Button(
            irow,
            text="📋 Dán",
            font=("Segoe UI", 9),
            bg="#E2E8F0",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=3,
            command=self._paste_mid,
        )
        paste_btn.pack(side="left", padx=6)

        check_btn = tk.Button(
            irow,
            text="  🔍 Kiểm Tra  ",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._do_check,
        )
        check_btn.pack(side="left")

        # ── Result display card ───────────────────────────────────────────────
        self._result_card = tk.Frame(body, bg="white", highlightbackground="#D8E4E0", highlightthickness=1, padx=16, pady=14)
        self._result_card.pack(fill="both", expand=True)

        self._result_text = tk.Label(
            self._result_card,
            text="Vui lòng nhập Machine ID và bấm 'Kiểm Tra'.",
            font=("Segoe UI", 10),
            fg="#64748B",
            bg="white",
            justify="left",
            anchor="nw",
        )
        self._result_text.pack(fill="both", expand=True)

        # ── Footer ───────────────────────────────────────────────────────────
        footer = tk.Frame(self, bg="#E8F0ED", height=46)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        tk.Button(
            footer,
            text="Đóng",
            font=("Segoe UI", 9, "bold"),
            bg="#CBD5E1",
            fg="#1E293B",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=4,
            command=self.destroy,
        ).pack(side="right", padx=16, pady=6)

        self.after(100, lambda: self._entry.focus_set())

    def _paste_mid(self):
        try:
            val = self.clipboard_get().strip()
            if val:
                self._mid_var.set(val.upper())
                self._do_check()
        except Exception:
            pass

    def _do_check(self):
        mid = self._mid_var.get().strip()
        if not mid:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập Machine ID cần kiểm tra.", parent=self)
            return

        rec = next((r for r in self._app.all_records if str(r.get("machine_id", "")).strip().upper() == mid.upper()), None)
        if rec:
            status = str(rec.get("status", "?")).upper()
            tier = TIER_LABELS.get(str(rec.get("tier", "")), str(rec.get("tier", "")).upper())
            expiry = rec.get("expiry") or "Vĩnh viễn"
            name = rec.get("name") or "(Chưa đặt tên)"
            note = rec.get("note") or "(Không có)"
            has_key = "Đã cấp riêng" if rec.get("admin_api_key") else "Chưa cấp (Dùng key mặc định/tự nhập)"
            issued = str(rec.get("issued_at", ""))[:16] if rec.get("issued_at") else "Chưa rõ"
            last = str(rec.get("last_check", ""))[:16] if rec.get("last_check") else "Chưa từng"

            status_icon = "🟢 ACTIVE (Đang hoạt động)" if status == "ACTIVE" else f"🔴 {status} (Bị khóa/Thu hồi)"

            info = (
                f"✅ TÌM THẤY TRONG CƠ SỞ DỮ LIỆU:\n\n"
                f"• Machine ID: {rec.get('machine_id')}\n"
                f"• Tên người dùng: {name}\n"
                f"• Trạng thái: {status_icon}\n"
                f"• Gói dịch vụ: {tier}\n"
                f"• Hạn sử dụng: {expiry}\n"
                f"• Admin API Key: {has_key}\n"
                f"• Ngày cấp quyền: {issued}\n"
                f"• Lần kiểm tra cuối: {last}\n"
                f"• Ghi chú: {note}"
            )
            self._result_text.configure(text=info, fg="#17313A", font=("Segoe UI", 10))
        else:
            self._result_text.configure(
                text=f"❌ KHÔNG TÌM THẤY:\n\nMachine ID '{mid}' không tồn tại trong danh sách giấy phép của hệ thống.",
                fg="#DC2626",
                font=("Segoe UI", 10, "bold"),
            )
