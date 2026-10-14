"""
admin/panel_exports.py — Panel quản lý xuất dữ liệu hàng loạt (NEW feature).
"""

from __future__ import annotations
import csv
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from admin.constants import TIER_LABELS


class ExportManagerPanel(tk.Frame):
    """Panel cho admin xuất/backup dữ liệu người dùng."""

    def __init__(self, parent, app, **kw):
        super().__init__(parent, bg="#F9F7F4", **kw)
        self._app = app
        self._build()

    def _build(self):
        tk.Label(self, text="📤  Xuất & Backup dữ liệu", font=("Segoe UI", 13, "bold"),
                 fg="#1F497D", bg="#F9F7F4").pack(anchor="w", padx=16, pady=(12, 8))

        # Export options
        opts = ttk.LabelFrame(self, text="Tùy chọn xuất")
        opts.pack(fill="x", padx=16, pady=(0, 10))

        cards_f = tk.Frame(opts, bg="#F9F7F4")
        cards_f.pack(fill="x", padx=12, pady=12)

        exports = [
            ("📋 Xuất CSV\nDanh sách người dùng", "#3B82F6", self._export_users_csv),
            ("📊 Xuất JSON\nFull backup dữ liệu", "#10B981", self._export_full_json),
            ("📦 Xuất theo gói\nTách file theo tier", "#7C3AED", self._export_by_tier),
            ("⏰ Xuất sắp hết hạn\nUser hết hạn 30 ngày", "#F59E0B", self._export_expiring),
        ]

        for i, (text, color, cmd) in enumerate(exports):
            btn = tk.Button(cards_f, text=text, font=("Segoe UI", 10, "bold"),
                           bg=color, fg="white", activebackground=color, relief="flat",
                           cursor="hand2", padx=16, pady=16, command=cmd, justify="center")
            btn.grid(row=0, column=i, sticky="ew", padx=6, pady=4)
        cards_f.columnconfigure((0, 1, 2, 3), weight=1)

        # Filter export
        filter_frm = ttk.LabelFrame(self, text="Xuất có lọc")
        filter_frm.pack(fill="x", padx=16, pady=(0, 10))
        ff = tk.Frame(filter_frm, bg="#F9F7F4"); ff.pack(fill="x", padx=12, pady=10)

        tk.Label(ff, text="Gói:", bg="#F9F7F4", font=("Segoe UI", 10)).pack(side="left")
        self._tier_filter = tk.StringVar(value="Tất cả")
        ttk.Combobox(ff, textvariable=self._tier_filter,
                     values=["Tất cả", "basic", "pro", "premium"],
                     width=12, state="readonly", font=("Segoe UI", 10)).pack(side="left", padx=8)

        tk.Label(ff, text="Trạng thái:", bg="#F9F7F4", font=("Segoe UI", 10)).pack(side="left", padx=(16, 0))
        self._status_filter = tk.StringVar(value="Tất cả")
        ttk.Combobox(ff, textvariable=self._status_filter,
                     values=["Tất cả", "active", "revoked", "expired"],
                     width=12, state="readonly", font=("Segoe UI", 10)).pack(side="left", padx=8)

        tk.Button(ff, text="  📤 Xuất theo bộ lọc  ", font=("Segoe UI", 10, "bold"),
                  bg="#2563EB", fg="white", relief="flat", cursor="hand2", pady=6,
                  command=self._export_filtered).pack(side="left", padx=16)

        # Recent exports info
        self._info_lbl = tk.Label(self, text="Chọn một tùy chọn xuất ở trên.", bg="#F9F7F4",
                                   fg="#64748B", font=("Segoe UI", 10, "italic"))
        self._info_lbl.pack(pady=16)

    def _get_records(self) -> list[dict]:
        return self._app.all_records

    def _ask_save_path(self, ext: str, prefix: str) -> str:
        return filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[(f"{ext.upper()}", f"*.{ext}"), ("Tất cả", "*.*")],
            title="Lưu file xuất",
            initialfile=f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.{ext}",
            parent=self._app,
        )

    def _export_users_csv(self):
        records = self._get_records()
        if not records:
            messagebox.showinfo("Trống", "Không có dữ liệu.", parent=self._app)
            return
        path = self._ask_save_path("csv", "DanhSach_NguoiDung")
        if not path: return
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Machine ID", "Tên", "Gói", "Trạng thái", "Hạn dùng", "Cấp lúc", "Lần cuối", "Ghi chú"])
                for r in records:
                    writer.writerow([
                        r.get("machine_id", ""), r.get("name", ""), r.get("tier", ""),
                        r.get("status", ""), r.get("expiry", "") or "Vĩnh viễn",
                        str(r.get("issued_at", ""))[:16], str(r.get("last_check", ""))[:16],
                        r.get("note", ""),
                    ])
            self._info_lbl.config(text=f"✅ Đã xuất CSV: {os.path.basename(path)}")
            messagebox.showinfo("Thành công", f"Đã xuất {len(records)} người dùng.", parent=self._app)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self._app)

    def _export_full_json(self):
        records = self._get_records()
        if not records:
            messagebox.showinfo("Trống", "Không có dữ liệu.", parent=self._app)
            return
        path = self._ask_save_path("json", "Backup_Full")
        if not path: return
        try:
            data = {
                "exported_at": datetime.now().isoformat(),
                "total": len(records),
                "records": records,
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._info_lbl.config(text=f"✅ Đã backup JSON: {os.path.basename(path)}")
            messagebox.showinfo("Thành công", f"Đã backup {len(records)} người dùng ra JSON.", parent=self._app)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self._app)

    def _export_by_tier(self):
        records = self._get_records()
        if not records:
            messagebox.showinfo("Trống", "Không có dữ liệu.", parent=self._app)
            return
        folder = filedialog.askdirectory(title="Chọn thư mục lưu", parent=self._app)
        if not folder: return
        try:
            by_tier: dict[str, list] = {}
            for r in records:
                t = r.get("tier", "basic")
                by_tier.setdefault(t, []).append(r)

            for tier, recs in by_tier.items():
                path = os.path.join(folder, f"users_{tier}_{datetime.now().strftime('%Y%m%d')}.csv")
                with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Machine ID", "Tên", "Trạng thái", "Hạn dùng", "Ghi chú"])
                    for r in recs:
                        writer.writerow([r.get("machine_id", ""), r.get("name", ""), r.get("status", ""),
                                         r.get("expiry", "") or "Vĩnh viễn", r.get("note", "")])

            summary = ", ".join(f"{t}: {len(recs)}" for t, recs in by_tier.items())
            self._info_lbl.config(text=f"✅ Đã tách theo gói: {summary}")
            messagebox.showinfo("Thành công", f"Đã xuất tách file theo gói:\n{summary}", parent=self._app)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self._app)

    def _export_expiring(self):
        from admin.supabase_api import fetch_expiring_soon
        expiring = fetch_expiring_soon(30)
        if not expiring:
            messagebox.showinfo("Không có", "Không có user nào sắp hết hạn trong 30 ngày.", parent=self._app)
            return
        path = self._ask_save_path("csv", "SapHetHan_30ngay")
        if not path: return
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Machine ID", "Tên", "Gói", "Hết hạn", "Trạng thái"])
                for r in expiring:
                    writer.writerow([r.get("machine_id", ""), r.get("name", ""), r.get("tier", ""),
                                     r.get("expiry", ""), r.get("status", "")])
            self._info_lbl.config(text=f"✅ Đã xuất {len(expiring)} user sắp hết hạn.")
            messagebox.showinfo("Thành công", f"Đã xuất {len(expiring)} user sắp hết hạn.", parent=self._app)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self._app)

    def _export_filtered(self):
        records = self._get_records()
        tier_f = self._tier_filter.get()
        status_f = self._status_filter.get()

        if tier_f != "Tất cả":
            records = [r for r in records if r.get("tier") == tier_f]
        if status_f != "Tất cả":
            records = [r for r in records if r.get("status") == status_f]

        if not records:
            messagebox.showinfo("Trống", "Không có dữ liệu phù hợp bộ lọc.", parent=self._app)
            return

        path = self._ask_save_path("csv", f"Filtered_{tier_f}_{status_f}")
        if not path: return
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Machine ID", "Tên", "Gói", "Trạng thái", "Hạn dùng", "Ghi chú"])
                for r in records:
                    writer.writerow([r.get("machine_id", ""), r.get("name", ""), r.get("tier", ""),
                                     r.get("status", ""), r.get("expiry", "") or "Vĩnh viễn", r.get("note", "")])
            self._info_lbl.config(text=f"✅ Đã xuất {len(records)} người dùng (lọc: {tier_f}/{status_f}).")
            messagebox.showinfo("Thành công", f"Đã xuất {len(records)} người dùng.", parent=self._app)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self._app)
