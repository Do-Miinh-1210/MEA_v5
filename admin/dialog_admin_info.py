"""
admin/dialog_admin_info.py — Hộp thoại thông tin Machine ID máy Admin.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from services.license_manager import get_machine_id


class AdminInfoDialog(tk.Toplevel):
    """Hộp thoại hiển thị thông tin máy tính Admin hiện tại."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self.title("💻 Machine ID Máy Admin — MEA")
        self.geometry("480x280")
        self.minsize(420, 240)
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
            w = 480
            h = 280
            x = max(0, px + (pw - w) // 2)
            y = max(0, py + (ph - h) // 2)
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────────
        header = tk.Frame(self, bg="#0B2F33", height=54)
        header.pack(fill="x")
        header.pack_propagate(False)

        htext = tk.Frame(header, bg="#0B2F33")
        htext.pack(side="left", padx=16, pady=8)
        tk.Label(
            htext,
            text="💻 MÁY TÍNH NÀY (ADMIN)",
            font=("Segoe UI", 12, "bold"),
            fg="white",
            bg="#0B2F33",
        ).pack(anchor="w")

        # ── Body ─────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg="#F4F8F7", padx=18, pady=14)
        body.pack(fill="both", expand=True)

        mid_card = tk.Frame(body, bg="white", highlightbackground="#D8E4E0", highlightthickness=1, padx=16, pady=14)
        mid_card.pack(fill="both", expand=True)

        tk.Label(
            mid_card,
            text="Machine ID phần cứng máy hiện tại:",
            font=("Segoe UI", 10, "bold"),
            fg="#17313A",
            bg="white",
        ).pack(anchor="w", pady=(0, 8))

        mid_admin = get_machine_id()

        row = tk.Frame(mid_card, bg="white")
        row.pack(fill="x", pady=(0, 10))

        e = tk.Entry(
            row,
            font=("Consolas", 12, "bold"),
            fg="#1F497D",
            bg="#F8FAFC",
            relief="solid",
            bd=1,
            justify="center",
        )
        e.pack(side="left", fill="x", expand=True, ipady=6)
        e.insert(0, mid_admin)
        e.config(state="readonly")

        def _copy():
            self.clipboard_clear()
            self.clipboard_append(mid_admin)
            self._app.set_status(f"📋 Đã sao chép Machine ID Admin: {mid_admin}")
            messagebox.showinfo("Đã sao chép", f"Đã sao chép Machine ID vào clipboard:\n{mid_admin}", parent=self)

        copy_btn = tk.Button(
            row,
            text="📋 Sao chép",
            font=("Segoe UI", 9, "bold"),
            bg="#0F9F6E",
            fg="white",
            activebackground="#0B7A54",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=5,
            command=_copy,
        )
        copy_btn.pack(side="left", padx=(8, 0))

        tk.Label(
            mid_card,
            text="Mẹo: Bạn có thể cấp gói PRO/PREMIUM cho chính Machine ID này để sử dụng MEA v4/v5 đầy đủ tính năng.",
            font=("Segoe UI", 8, "italic"),
            fg="#64748B",
            bg="white",
            wraplength=380,
            justify="left",
        ).pack(anchor="w")

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
