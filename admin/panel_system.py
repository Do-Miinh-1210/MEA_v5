"""
admin/panel_system.py — Panel & Dialog kiểm soát hệ thống (maintenance, lock/unlock).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from services.license_manager import (
    admin_maintenance_on, admin_maintenance_off,
    admin_lock_all, admin_unlock_all,
)
from admin.dialog_system import SystemControlDialog


class SystemControlPanel(tk.Frame):
    """Panel widget chứa các nút điều khiển hệ thống (giữ tương thích)."""

    def __init__(self, parent, app, **kw):
        super().__init__(parent, bg="white", **kw)
        self._app = app
        self._build()

    def _build(self):
        ctrl_frm = ttk.LabelFrame(self, text="🛡️ Kiểm soát hệ thống")
        ctrl_frm.pack(fill="x", pady=(0, 10))
        cf = tk.Frame(ctrl_frm, bg="white")
        cf.pack(fill="x", padx=10, pady=10)

        self._maint_btn = tk.Button(
            cf,
            text="🔧 Bật chế độ bảo trì",
            font=("Segoe UI", 9, "bold"),
            bg="#DC2626",
            fg="white",
            activebackground="#B91C1C",
            relief="flat",
            cursor="hand2",
            pady=7,
            command=self._toggle_maintenance,
        )
        self._maint_btn.pack(fill="x", pady=(0, 6))

        tk.Button(
            cf,
            text="🔒 Khóa tất cả người dùng",
            font=("Segoe UI", 9, "bold"),
            bg="#EA580C",
            fg="white",
            activebackground="#C2410C",
            relief="flat",
            cursor="hand2",
            pady=6,
            command=self._lock_all,
        ).pack(fill="x", pady=(0, 6))

        tk.Button(
            cf,
            text="🔓 Mở khóa tất cả người dùng",
            font=("Segoe UI", 9, "bold"),
            bg="#0284C7",
            fg="white",
            activebackground="#0369A1",
            relief="flat",
            cursor="hand2",
            pady=6,
            command=self._unlock_all,
        ).pack(fill="x", pady=(0, 6))

        tk.Button(
            cf,
            text="⚙️ Tính năng & Bảng giá",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            relief="flat",
            cursor="hand2",
            pady=7,
            command=self._open_system_settings,
        ).pack(fill="x")

    def set_maintenance_state(self, is_on: bool):
        if is_on:
            self._maint_btn.config(text="✅ Tắt chế độ bảo trì", bg="#0F9F6E")
        else:
            self._maint_btn.config(text="🔧 Bật chế độ bảo trì", bg="#DC2626")

    def _toggle_maintenance(self):
        if not getattr(self._app, "maintenance_on", False):
            msg = simpledialog.askstring(
                "Thông báo bảo trì",
                "Nhập thông báo hiển thị cho người dùng:\n(Để trống = dùng thông báo mặc định)",
                parent=self._app,
                initialvalue="Hệ thống đang nâng cấp định kỳ. Vui lòng thử lại sau 30 phút.",
            )
            if msg is None:
                return
            if not messagebox.askyesno("Xác nhận", "Bật chế độ bảo trì?\n\nTẤT CẢ người dùng sẽ bị chặn ngay khi mở app.", parent=self._app):
                return
            try:
                r = admin_maintenance_on(msg)
                if r.get("ok"):
                    self._app.maintenance_on = True
                    self._app.show_maintenance_banner(True)
                    self.set_maintenance_state(True)
                    self._app.set_status("🔧 Chế độ bảo trì ĐÃ BẬT")
                else:
                    messagebox.showerror("Lỗi", r.get("error", "Không bật được."), parent=self._app)
            except Exception as e:
                messagebox.showerror("Lỗi kết nối", str(e), parent=self._app)
        else:
            if not messagebox.askyesno("Xác nhận", "Tắt chế độ bảo trì?\n\nNgười dùng active sẽ vào được app.", parent=self._app):
                return
            try:
                r = admin_maintenance_off()
                if r.get("ok"):
                    self._app.maintenance_on = False
                    self._app.show_maintenance_banner(False)
                    self.set_maintenance_state(False)
                    self._app.set_status("✅ Chế độ bảo trì đã tắt")
                else:
                    messagebox.showerror("Lỗi", r.get("error", ""), parent=self._app)
            except Exception as e:
                messagebox.showerror("Lỗi kết nối", str(e), parent=self._app)

    def _lock_all(self):
        if not messagebox.askyesno("Xác nhận", "Khóa TẤT CẢ người dùng đang active?", parent=self._app):
            return
        self._app.set_status("⏳ Đang khóa toàn bộ...")
        self._app.update_idletasks()
        try:
            r = admin_lock_all()
            if r.get("ok"):
                messagebox.showinfo("Đã khóa", r.get("message", "Đã khóa"), parent=self._app)
                self._app.refresh()
            else:
                messagebox.showerror("Lỗi", r.get("error", ""), parent=self._app)
        except Exception as e:
            messagebox.showerror("Lỗi kết nối", str(e), parent=self._app)

    def _unlock_all(self):
        if not messagebox.askyesno("Xác nhận", "Mở khóa TẤT CẢ người dùng bị khóa?", parent=self._app):
            return
        self._app.set_status("⏳ Đang mở khóa...")
        self._app.update_idletasks()
        try:
            r = admin_unlock_all()
            if r.get("ok"):
                messagebox.showinfo("Đã mở khóa", r.get("message", "Đã mở khóa"), parent=self._app)
                self._app.refresh()
            else:
                messagebox.showerror("Lỗi", r.get("error", ""), parent=self._app)
        except Exception as e:
            messagebox.showerror("Lỗi kết nối", str(e), parent=self._app)

    def _open_system_settings(self):
        from admin.dialog_settings import AdminSystemSettingsDialog
        AdminSystemSettingsDialog(self._app)
