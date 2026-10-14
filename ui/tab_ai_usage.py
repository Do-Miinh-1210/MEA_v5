"""
ui/tab_ai_usage.py — Tab "📊 Sử dụng AI".

Hiển thị thống kê AI usage:
  • Tổng request hôm nay / tuần / tháng
  • Phân bố theo provider / model / kind (generate vs vision)
  • Cảnh báo quota: vàng (≥80%) / đỏ (≥95%) / đen (≥100%)
  • Bảng 50 request gần nhất (timestamp, provider, model, status, duration)
  • Nút "Refresh" + "Xoá log" + "Mở thư mục"

Dữ liệu lấy từ services/ai_usage_log.py.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from services import ai_usage_log


_LEVEL_COLORS = {
    "ok":     ("#10B981", "white"),
    "warn":   ("#F59E0B", "white"),
    "danger": ("#EF4444", "white"),
    "over":   ("#7F1D1D", "white"),
}


class TabAIUsage(ttk.Frame):
    """Tab thống kê sử dụng AI."""

    def __init__(self, parent):
        super().__init__(parent)
        self._build()
        self.refresh()

    # ── Build ────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg="#0F2D52")
        hdr.pack(fill="x")
        tk.Label(hdr, text="  📊  THỐNG KÊ SỬ DỤNG AI",
                 bg="#0F2D52", fg="white",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=12, pady=10)
        tk.Frame(self, bg="#10B981", height=3).pack(fill="x")

        # Toolbar
        tb = tk.Frame(self, bg="#E2E8F0")
        tb.pack(fill="x")
        tk.Button(tb, text="  🔄  Làm mới  ",
                  bg="#3B82F6", fg="white", activebackground="#2563EB",
                  activeforeground="white",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2", padx=14, pady=6, bd=0,
                  command=self.refresh).pack(side="left", padx=8, pady=6)
        tk.Button(tb, text="  📁  Mở thư mục log  ",
                  bg="#0891B2", fg="white", activebackground="#0E7490",
                  activeforeground="white",
                  font=("Segoe UI", 10),
                  relief="flat", cursor="hand2", padx=12, pady=6, bd=0,
                  command=self._open_log_dir).pack(side="left", padx=4, pady=6)
        tk.Button(tb, text="  🗑  Xoá log  ",
                  bg="#EF4444", fg="white", activebackground="#DC2626",
                  activeforeground="white",
                  font=("Segoe UI", 10),
                  relief="flat", cursor="hand2", padx=12, pady=6, bd=0,
                  command=self._clear_log).pack(side="left", padx=4, pady=6)

        # Range selector
        tk.Label(tb, text="Phạm vi:", bg="#E2E8F0",
                 font=("Segoe UI", 10, "bold")).pack(side="left", padx=(16, 4))
        self._range_var = tk.StringVar(value="today")
        for label, val in [("Hôm nay", "today"), ("7 ngày", "7"),
                           ("30 ngày", "30"), ("Tất cả", "all")]:
            tk.Radiobutton(tb, text=label, variable=self._range_var, value=val,
                           bg="#E2E8F0", font=("Segoe UI", 9),
                           command=self.refresh).pack(side="left", padx=2)

        # Body — 2 hàng: stats cards + table
        body = tk.Frame(self, bg="#F8FAFC")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Top: stats cards (4 KPI cards) ──
        cards = tk.Frame(body, bg="#F8FAFC")
        cards.pack(fill="x", pady=(0, 10))

        for i in range(4):
            cards.grid_columnconfigure(i, weight=1, uniform="card")

        self._kpi_total      = self._make_kpi_card(cards, 0, "📨", "Tổng request", "#3B82F6")
        self._kpi_success    = self._make_kpi_card(cards, 1, "✅", "Tỉ lệ thành công", "#10B981")
        self._kpi_chars      = self._make_kpi_card(cards, 2, "📝", "Tổng ký tự", "#7C3AED")
        self._kpi_avg_time   = self._make_kpi_card(cards, 3, "⏱", "Avg duration", "#F59E0B")

        # ── Middle: provider/model breakdown + quota warnings ──
        mid = tk.Frame(body, bg="#F8FAFC")
        mid.pack(fill="x", pady=(0, 10))

        # By provider
        prov_frame = tk.LabelFrame(mid, text="  Theo provider  ",
                                    font=("Segoe UI", 10, "bold"),
                                    bg="#FFFFFF", fg="#0F2D52", bd=1, relief="solid")
        prov_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self._prov_text = tk.Text(prov_frame, height=6,
                                   font=("Segoe UI", 10), bg="#FFFFFF",
                                   relief="flat", state="disabled", padx=10, pady=6)
        self._prov_text.pack(fill="both", expand=True)

        # Quota warnings
        quota_frame = tk.LabelFrame(mid, text="  Cảnh báo quota  ",
                                     font=("Segoe UI", 10, "bold"),
                                     bg="#FFFFFF", fg="#0F2D52", bd=1, relief="solid")
        quota_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        self._quota_text = tk.Text(quota_frame, height=6,
                                    font=("Segoe UI", 10), bg="#FFFFFF",
                                    relief="flat", state="disabled", padx=10, pady=6)
        self._quota_text.pack(fill="both", expand=True)
        self._quota_text.tag_configure("ok",     foreground="#10B981")
        self._quota_text.tag_configure("warn",   foreground="#F59E0B", font=("Segoe UI", 10, "bold"))
        self._quota_text.tag_configure("danger", foreground="#EF4444", font=("Segoe UI", 10, "bold"))
        self._quota_text.tag_configure("over",   foreground="#7F1D1D", font=("Segoe UI", 10, "bold"))

        # ── Bottom: recent requests table ──
        rec_frame = tk.LabelFrame(body, text="  50 request gần nhất  ",
                                   font=("Segoe UI", 10, "bold"),
                                   bg="#FFFFFF", fg="#0F2D52", bd=1, relief="solid")
        rec_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("Usage.Treeview", rowheight=24, font=("Segoe UI", 9))
        style.configure("Usage.Treeview.Heading", font=("Segoe UI", 9, "bold"))

        cols = ("ts", "provider", "model", "kind", "status",
                "prompt", "response", "duration")
        self._tree = ttk.Treeview(rec_frame, columns=cols, show="headings",
                                   style="Usage.Treeview", height=12)
        col_widths = {
            "ts": 130, "provider": 130, "model": 150, "kind": 100,
            "status": 60, "prompt": 60, "response": 60, "duration": 70,
        }
        col_labels = {
            "ts": "Thời gian", "provider": "Provider", "model": "Model",
            "kind": "Kind", "status": "OK", "prompt": "Prompt",
            "response": "Response", "duration": "Time(ms)",
        }
        for c in cols:
            self._tree.heading(c, text=col_labels[c])
            self._tree.column(c, width=col_widths[c],
                              anchor="w" if c in ("ts", "provider", "model", "kind") else "e")
        vsb = ttk.Scrollbar(rec_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)

        # Status bar
        self._status_lbl = tk.Label(self, text="", bg="#F8FAFC",
                                     fg="#64748B", anchor="w",
                                     font=("Segoe UI", 8, "italic"))
        self._status_lbl.pack(side="bottom", fill="x", padx=10, pady=(0, 4))

    def _make_kpi_card(self, parent, col: int, icon: str, label: str,
                       color: str) -> dict:
        """Tạo 1 KPI card (icon + value + label). Trả dict các widget để update."""
        card = tk.Frame(parent, bg=color, bd=0, relief="flat")
        card.grid(row=0, column=col, sticky="ew", padx=4)
        inner = tk.Frame(card, bg="#FFFFFF", bd=0)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        tk.Label(inner, text=icon, bg="#FFFFFF", fg=color,
                 font=("Segoe UI", 22)).pack(pady=(8, 0))
        value_lbl = tk.Label(inner, text="0", bg="#FFFFFF", fg=color,
                             font=("Segoe UI", 18, "bold"))
        value_lbl.pack(pady=(0, 0))
        tk.Label(inner, text=label, bg="#FFFFFF", fg="#64748B",
                 font=("Segoe UI", 9)).pack(pady=(0, 8))
        return {"value_lbl": value_lbl, "color": color}

    # ── Refresh ────────────────────────────────────────────────────────────

    def refresh(self):
        """Re-load data và update toàn bộ UI."""
        rng = self._range_var.get()
        if rng == "today":
            stats = ai_usage_log.stats_today()
            range_label = "hôm nay"
        elif rng == "all":
            # All-time: dùng range lớn 365 ngày
            stats = ai_usage_log.stats_range(days=365)
            range_label = "tất cả (365 ngày)"
        else:
            days = int(rng)
            stats = ai_usage_log.stats_range(days=days)
            range_label = f"{days} ngày gần nhất"

        # KPIs
        self._kpi_total["value_lbl"].config(text=str(stats["total"]))
        self._kpi_success["value_lbl"].config(text=f"{stats['success_rate']}%")
        self._kpi_chars["value_lbl"].config(
            text=self._fmt_num(stats["total_chars"]))
        self._kpi_avg_time["value_lbl"].config(
            text=self._fmt_duration(stats["avg_duration_ms"]))

        # Provider breakdown
        self._prov_text.config(state="normal")
        self._prov_text.delete("1.0", "end")
        if stats["by_provider"]:
            for prov, n in stats["by_provider"].items():
                pct = n / stats["total"] * 100 if stats["total"] else 0
                self._prov_text.insert("end", f"  • {prov}:  {n:>4} request  ({pct:.0f}%)\n")
            self._prov_text.insert("end", "\n  Theo model:\n")
            for model, n in list(stats["by_model"].items())[:5]:
                self._prov_text.insert("end", f"    – {model}:  {n}\n")
        else:
            self._prov_text.insert("end", "  (Chưa có request nào)")
        self._prov_text.config(state="disabled")

        # Quota warnings (cho hôm nay — luôn check theo daily quota)
        today_stats = ai_usage_log.stats_today()
        self._quota_text.config(state="normal")
        self._quota_text.delete("1.0", "end")
        models_used = today_stats.get("by_model", {})
        if not models_used:
            self._quota_text.insert("end", "  ✓ Hôm nay chưa dùng AI\n")
        else:
            # Map model → provider (từ recent entries)
            provider_for_model: dict[str, str] = {}
            for e in ai_usage_log.recent_entries(n=200):
                m = e.get("model", "")
                if m and m not in provider_for_model:
                    provider_for_model[m] = e.get("provider", "")
            for model, used in models_used.items():
                provider = provider_for_model.get(model, "?")
                if provider == "?":
                    continue
                qs = ai_usage_log.quota_status(provider, model)
                lvl = qs["level"]
                icon = {"ok": "✓", "warn": "⚠", "danger": "🔥", "over": "⛔"}[lvl]
                line = (f"  {icon}  {model[:30]:30}  "
                        f"{qs['used_today']:>4} / {qs['limit_today']:>5}  "
                        f"({qs['percent']:5.1f}%)\n")
                self._quota_text.insert("end", line, lvl)
        self._quota_text.config(state="disabled")

        # Recent table — luôn show 50 mới nhất (không filter theo range)
        for it in self._tree.get_children():
            self._tree.delete(it)
        for e in ai_usage_log.recent_entries(n=50):
            ts = e.get("ts", "")[:19].replace("T", " ")
            ok = "✓" if e.get("ok") else "✗"
            self._tree.insert("", "end", values=(
                ts, e.get("provider", ""), e.get("model", ""),
                e.get("kind", ""), ok,
                self._fmt_num(e.get("prompt_chars", 0)),
                self._fmt_num(e.get("response_chars", 0)),
                e.get("duration_ms", 0),
            ))

        # Status
        size_kb = ai_usage_log.log_size_bytes() / 1024
        self._status_lbl.config(
            text=f"📁 Log file: {size_kb:.1f} KB  •  "
                 f"Phạm vi hiển thị: {range_label}  •  "
                 f"Lỗi: {stats['errors']} / {stats['total']}"
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _fmt_num(n: int) -> str:
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)

    @staticmethod
    def _fmt_duration(ms: int) -> str:
        if ms == 0:
            return "—"
        if ms < 1000:
            return f"{ms}ms"
        return f"{ms/1000:.1f}s"

    def _open_log_dir(self):
        from config import APP_DIR
        try:
            import os, sys, subprocess
            if sys.platform == "win32":
                os.startfile(APP_DIR)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(APP_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(APP_DIR)])
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def _clear_log(self):
        if not messagebox.askyesno(
            "Xác nhận xoá",
            "Xoá toàn bộ log AI usage?\n(Không thể khôi phục)",
            parent=self,
        ):
            return
        if ai_usage_log.clear_log():
            messagebox.showinfo("Đã xoá", "Đã xoá log usage.", parent=self)
            self.refresh()
        else:
            messagebox.showerror("Lỗi", "Không xoá được log.", parent=self)
