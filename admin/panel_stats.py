"""
admin/panel_stats.py — Panel thống kê tổng quan (NEW feature).
Hiển thị biểu đồ text-based + thống kê nhanh cho admin.
"""

from __future__ import annotations
import threading
import tkinter as tk
from tkinter import ttk

from admin.constants import TIER_LABELS


class StatsPanel(tk.Frame):
    """Panel hiển thị thống kê tổng quan người dùng."""

    def __init__(self, parent, app, **kw):
        super().__init__(parent, bg="#F9F7F4", **kw)
        self._app = app
        self._expiring_load_id = 0
        self._build()

    def _build(self):
        tk.Label(self, text="📊  Thống kê tổng quan", font=("Segoe UI", 13, "bold"),
                 fg="#1F497D", bg="#F9F7F4").pack(anchor="w", padx=16, pady=(12, 8))

        # Cards row
        self._cards_frame = tk.Frame(self, bg="#F9F7F4")
        self._cards_frame.pack(fill="x", padx=16, pady=(0, 12))

        # Tier breakdown
        self._tier_frame = ttk.LabelFrame(self, text="📦  Phân bố theo gói")
        self._tier_frame.pack(fill="x", padx=16, pady=(0, 10))

        self._tier_content = tk.Frame(self._tier_frame, bg="white")
        self._tier_content.pack(fill="x", padx=12, pady=10)

        # Expiring soon
        self._expiry_frame = ttk.LabelFrame(self, text="⏰  Sắp hết hạn (30 ngày)")
        self._expiry_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        self._expiry_tree = ttk.Treeview(self._expiry_frame, columns=("mid", "name", "tier", "expiry"), show="headings", height=6)
        self._expiry_tree.heading("mid", text="Machine ID")
        self._expiry_tree.heading("name", text="Tên")
        self._expiry_tree.heading("tier", text="Gói")
        self._expiry_tree.heading("expiry", text="Hết hạn")
        self._expiry_tree.column("mid", width=120)
        self._expiry_tree.column("name", width=150)
        self._expiry_tree.column("tier", width=100)
        self._expiry_tree.column("expiry", width=100)
        self._expiry_tree.pack(fill="both", expand=True, padx=8, pady=8)

        # Refresh button
        tk.Button(self, text="  🔄 Làm mới thống kê  ", font=("Segoe UI", 10, "bold"),
                  bg="#3B82F6", fg="white", relief="flat", cursor="hand2", pady=6,
                  command=self.refresh_stats).pack(pady=(0, 12))

    def refresh_stats(self):
        """Cập nhật toàn bộ thống kê từ dữ liệu hiện có."""
        records = self._app.all_records

        # Clear cards
        for w in self._cards_frame.winfo_children():
            w.destroy()

        # Compute stats
        total = len(records)
        n_active = sum(1 for r in records if r.get("status") == "active")
        n_revoked = sum(1 for r in records if r.get("status") == "revoked")

        # Active in 7 days
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        n_active_7d = sum(1 for r in records if r.get("last_check") and str(r["last_check"]) >= week_ago)

        # Cards
        cards = [
            ("Tổng người dùng", str(total), "#3B82F6"),
            ("Đang hoạt động", str(n_active), "#10B981"),
            ("Đã thu hồi", str(n_revoked), "#EF4444"),
            ("Active 7 ngày", str(n_active_7d), "#F59E0B"),
        ]
        for i, (label, value, color) in enumerate(cards):
            card = tk.Frame(self._cards_frame, bg="white", bd=1, relief="solid", padx=16, pady=12)
            card.grid(row=0, column=i, sticky="ew", padx=6)
            tk.Label(card, text=value, bg="white", fg=color, font=("Segoe UI", 22, "bold")).pack()
            tk.Label(card, text=label, bg="white", fg="#64748B", font=("Segoe UI", 10)).pack()
        self._cards_frame.columnconfigure((0, 1, 2, 3), weight=1)

        # Tier breakdown bars
        for w in self._tier_content.winfo_children():
            w.destroy()

        tier_counts = {}
        for r in records:
            t = r.get("tier", "basic")
            tier_counts[t] = tier_counts.get(t, 0) + 1

        _TIER_COLORS = {"basic": "#64748B", "pro": "#2563EB", "premium": "#7C3AED"}
        for tier in ["basic", "pro", "premium"]:
            count = tier_counts.get(tier, 0)
            pct = (count / total * 100) if total > 0 else 0
            row = tk.Frame(self._tier_content, bg="white")
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"{tier.upper()}: {count}", bg="white", fg="#1F497D",
                     font=("Segoe UI", 10, "bold"), width=16, anchor="w").pack(side="left")
            # Bar
            bar_bg = tk.Frame(row, bg="#E2E8F0", height=20)
            bar_bg.pack(side="left", fill="x", expand=True, padx=(0, 8))
            bar_fill = tk.Frame(bar_bg, bg=_TIER_COLORS.get(tier, "#999"), height=20)
            bar_fill.place(relwidth=max(pct / 100, 0.01), relheight=1.0)
            tk.Label(row, text=f"{pct:.0f}%", bg="white", fg="#64748B",
                     font=("Segoe UI", 9), width=6).pack(side="right")

        # Expiring soon
        self._expiry_tree.delete(*self._expiry_tree.get_children())
        self._expiry_tree.insert("", "end", values=("", "Đang tải danh sách sắp hết hạn...", "", ""))
        self._expiring_load_id += 1
        load_id = self._expiring_load_id

        def _worker():
            try:
                from admin.supabase_api import fetch_expiring_soon
                expiring = fetch_expiring_soon(30)
                error = None
            except Exception as exc:
                expiring = []
                error = exc
            self.after(0, lambda: self._render_expiring(load_id, expiring, error))

        threading.Thread(target=_worker, daemon=True, name="AdminExpiringStats").start()

    def _render_expiring(self, load_id: int, expiring: list[dict], error: Exception | None):
        if load_id != self._expiring_load_id or not self.winfo_exists():
            return
        self._expiry_tree.delete(*self._expiry_tree.get_children())
        if error is not None:
            self._expiry_tree.insert("", "end", values=("", f"Lỗi tải dữ liệu: {error}", "", ""))
            return
        for r in expiring:
            self._expiry_tree.insert("", "end", values=(
                r.get("machine_id", ""), r.get("name", ""),
                r.get("tier", "").upper(), r.get("expiry", ""),
            ))
        if not expiring:
            self._expiry_tree.insert("", "end", values=("", "Không có ai sắp hết hạn", "", ""))
