"""
admin/panel_logs.py — Panel xem log hoạt động admin (NEW feature).
"""

from __future__ import annotations
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime


class LogViewerPanel(tk.Frame):
    """Panel hiển thị log hoạt động admin."""

    def __init__(self, parent, app, **kw):
        super().__init__(parent, bg="#F9F7F4", **kw)
        self._app = app
        self._logs: list[dict] = []
        self._filter_after_id: str | None = None
        self._loading = False
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg="#F9F7F4")
        hdr.pack(fill="x", padx=16, pady=(12, 8))
        tk.Label(hdr, text="📝  Log hoạt động Admin", font=("Segoe UI", 13, "bold"),
                 fg="#1F497D", bg="#F9F7F4").pack(side="left")

        tk.Button(hdr, text="  🔄 Làm mới  ", font=("Segoe UI", 9, "bold"),
                  bg="#3B82F6", fg="white", relief="flat", cursor="hand2", pady=4,
                  command=self.refresh_logs).pack(side="right", padx=4)
        tk.Button(hdr, text="  📤 Xuất Log  ", font=("Segoe UI", 9, "bold"),
                  bg="#F59E0B", fg="white", relief="flat", cursor="hand2", pady=4,
                  command=self._export_logs).pack(side="right", padx=4)

        # Filter
        flt = tk.Frame(self, bg="#F9F7F4")
        flt.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(flt, text="Lọc hành động:", bg="#F9F7F4", font=("Segoe UI", 10)).pack(side="left")
        self._action_filter = tk.StringVar(value="Tất cả")
        ttk.Combobox(flt, textvariable=self._action_filter,
                     values=["Tất cả", "add", "revoke", "restore", "tier_change", "expiry_change", "api_key", "maintenance", "lock", "unlock"],
                     width=16, state="readonly", font=("Segoe UI", 10)).pack(side="left", padx=8)
        self._action_filter.trace_add("write", lambda *_: self._schedule_filter())

        tk.Label(flt, text="Tìm:", bg="#F9F7F4", font=("Segoe UI", 10)).pack(side="left", padx=(16, 4))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._schedule_filter())
        ttk.Entry(flt, textvariable=self._search_var, width=20, font=("Segoe UI", 10)).pack(side="left")

        # Treeview
        cols = ("time", "action", "target", "admin", "details")
        tbl_f = tk.Frame(self); tbl_f.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        vsb = ttk.Scrollbar(tbl_f, orient="vertical"); vsb.pack(side="right", fill="y")

        self._tree = ttk.Treeview(tbl_f, columns=cols, show="headings", yscrollcommand=vsb.set, height=15)
        vsb.config(command=self._tree.yview)

        self._tree.heading("time", text="Thời gian")
        self._tree.heading("action", text="Hành động")
        self._tree.heading("target", text="Đối tượng")
        self._tree.heading("admin", text="Admin")
        self._tree.heading("details", text="Chi tiết")
        self._tree.column("time", width=150)
        self._tree.column("action", width=120)
        self._tree.column("target", width=130)
        self._tree.column("admin", width=130)
        self._tree.column("details", width=300)
        self._tree.pack(fill="both", expand=True)

        # Info label
        self._info_lbl = tk.Label(self, text="Nhấn 'Làm mới' để tải log.", bg="#F9F7F4",
                                   fg="#64748B", font=("Segoe UI", 9, "italic"))
        self._info_lbl.pack(pady=(0, 8))

    def refresh_logs(self):
        if self._loading:
            return
        self._loading = True
        """Tải log từ Supabase."""
        self._info_lbl.config(text="⏳ Đang tải log...")
        def _worker() -> None:
            try:
                from admin.supabase_api import fetch_activity_logs
                logs = fetch_activity_logs(500)
                error = None
            except Exception as exc:
                logs = []
                error = exc
            try:
                self.after(0, lambda: self._finish_refresh_logs(logs, error))
            except tk.TclError:
                pass

        threading.Thread(target=_worker, daemon=True, name="AdminLogs").start()
        return
        self.update_idletasks()
        from admin.supabase_api import fetch_activity_logs
        self._logs = fetch_activity_logs(500)
        self._apply_filter()
        n = len(self._logs)
        self._info_lbl.config(text=f"Hiển thị {n} bản ghi log" if n else "Không có log hoặc bảng activity_logs chưa tồn tại.")

    def _finish_refresh_logs(self, logs: list[dict], error: Exception | None):
        self._loading = False
        if error is not None:
            self._tree.delete(*self._tree.get_children())
            self._info_lbl.config(text=f"Lá»—i táº£i log: {error}")
            return
        self._logs = logs
        self._apply_filter()
        n = len(self._logs)
        self._info_lbl.config(text=f"Hiá»ƒn thá»‹ {n} báº£n ghi log" if n else "KhÃ´ng cÃ³ log hoáº·c báº£ng activity_logs chÆ°a tá»“n táº¡i.")

    def _schedule_filter(self):
        if self._filter_after_id is not None:
            try:
                self.after_cancel(self._filter_after_id)
            except tk.TclError:
                pass
        self._filter_after_id = self.after(140, self._apply_filter)

    def _apply_filter(self):
        self._filter_after_id = None
        self._tree.delete(*self._tree.get_children())
        action_f = self._action_filter.get()
        kw = self._search_var.get().lower()

        for log in self._logs:
            action = log.get("action", "")
            if action_f != "Tất cả" and action != action_f:
                continue
            if kw and kw not in str(log).lower():
                continue
            self._tree.insert("", "end", values=(
                str(log.get("created_at", ""))[:19],
                action,
                log.get("target_mid", ""),
                log.get("admin_mid", ""),
                log.get("details", ""),
            ))

    def _export_logs(self):
        if not self._logs:
            messagebox.showinfo("Trống", "Không có log để xuất.", parent=self._app)
            return
        import csv
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            title="Xuất log ra CSV",
            initialfile=f"Admin_Logs_{datetime.now().strftime('%Y%m%d')}.csv",
            parent=self._app,
        )
        if not path: return
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Thời gian", "Hành động", "Đối tượng", "Admin", "Chi tiết"])
                for log in self._logs:
                    writer.writerow([
                        str(log.get("created_at", ""))[:19],
                        log.get("action", ""),
                        log.get("target_mid", ""),
                        log.get("admin_mid", ""),
                        log.get("details", ""),
                    ])
            messagebox.showinfo("Thành công", f"Đã xuất log ra:\n{path}", parent=self._app)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất:\n{e}", parent=self._app)
