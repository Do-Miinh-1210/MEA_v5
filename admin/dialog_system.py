"""
admin/dialog_system.py — Hộp thoại kiểm soát toàn hệ thống (bảo trì, khóa/mở khóa toàn bộ).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from services.license_manager import (
    admin_maintenance_on,
    admin_maintenance_off,
    admin_lock_all,
    admin_unlock_all,
)


class SystemControlDialog(tk.Toplevel):
    """Hộp thoại Kiểm soát toàn hệ thống — Thiết kế an toàn, rõ ràng, hiện đại."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self._app = app
        self.title("🛡️ Kiểm Soát Toàn Hệ Thống — MEA Admin")
        self.geometry("580x520")
        self.minsize(520, 480)
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
            w = 580
            h = 520
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
            text="🛡️ KIỂM SOÁT TOÀN HỆ THỐNG",
            font=("Segoe UI", 13, "bold"),
            fg="white",
            bg="#0B2F33",
        ).pack(anchor="w")
        tk.Label(
            htext,
            text="Quản lý chế độ bảo trì và khóa/mở khóa truy cập tài khoản đồng loạt",
            font=("Segoe UI", 9),
            fg="#9CC9C3",
            bg="#0B2F33",
        ).pack(anchor="w")

        # ── Body ─────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg="#F4F8F7")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        # 1. Card: Maintenance Mode
        maint_card = tk.Frame(body, bg="white", highlightbackground="#D8E4E0", highlightthickness=1)
        maint_card.pack(fill="x", pady=(0, 14))

        maint_inner = tk.Frame(maint_card, bg="white", padx=16, pady=14)
        maint_inner.pack(fill="x")

        tk.Label(
            maint_inner,
            text="1. Chế độ bảo trì hệ thống (Maintenance Mode)",
            font=("Segoe UI", 10, "bold"),
            fg="#17313A",
            bg="white",
        ).pack(anchor="w", pady=(0, 6))

        # Live status banner inside card
        is_maint = getattr(self._app, "maintenance_on", False)
        self._maint_status_frame = tk.Frame(
            maint_inner,
            bg="#FEE2E2" if is_maint else "#ECFDF5",
            highlightbackground="#FCA5A5" if is_maint else "#A7F3D0",
            highlightthickness=1,
            padx=12,
            pady=8,
        )
        self._maint_status_frame.pack(fill="x", pady=(0, 10))

        self._maint_status_lbl = tk.Label(
            self._maint_status_frame,
            text="🔴 ĐANG BẬT BẢO TRÌ — Tất cả người dùng đang bị chặn truy cập app." if is_maint else "🟢 HOẠT ĐỘNG BÌNH THƯỜNG — Người dùng active sử dụng app bình thường.",
            font=("Segoe UI", 9, "bold"),
            fg="#991B1B" if is_maint else "#065F46",
            bg="#FEE2E2" if is_maint else "#ECFDF5",
        )
        self._maint_status_lbl.pack(anchor="w")

        self._maint_toggle_btn = tk.Button(
            maint_inner,
            text="✅ Tắt chế độ bảo trì" if is_maint else "🔧 Bật chế độ bảo trì",
            font=("Segoe UI", 10, "bold"),
            bg="#0F9F6E" if is_maint else "#DC2626",
            fg="white",
            activebackground="#0B7A54" if is_maint else "#B91C1C",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
            command=self._toggle_maintenance,
        )
        self._maint_toggle_btn.pack(anchor="w")

        # 2. Card: Bulk Lock / Unlock
        bulk_card = tk.Frame(body, bg="white", highlightbackground="#D8E4E0", highlightthickness=1)
        bulk_card.pack(fill="x", pady=(0, 14))

        bulk_inner = tk.Frame(bulk_card, bg="white", padx=16, pady=14)
        bulk_inner.pack(fill="x")

        tk.Label(
            bulk_inner,
            text="2. Khóa / Mở khóa toàn bộ người dùng",
            font=("Segoe UI", 10, "bold"),
            fg="#17313A",
            bg="white",
        ).pack(anchor="w", pady=(0, 4))
        tk.Label(
            bulk_inner,
            text="Cẩn trọng: Thao tác này sẽ áp dụng lên toàn bộ danh sách tài khoản trong cơ sở dữ liệu.",
            font=("Segoe UI", 8),
            fg="#64748B",
            bg="white",
        ).pack(anchor="w", pady=(0, 10))

        btn_row = tk.Frame(bulk_inner, bg="white")
        btn_row.pack(fill="x")

        lock_btn = tk.Button(
            btn_row,
            text="🔒 Khóa tất cả người dùng",
            font=("Segoe UI", 9, "bold"),
            bg="#EA580C",
            fg="white",
            activebackground="#C2410C",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
            command=self._lock_all,
        )
        lock_btn.pack(side="left", padx=(0, 10))

        unlock_btn = tk.Button(
            btn_row,
            text="🔓 Mở khóa tất cả người dùng",
            font=("Segoe UI", 9, "bold"),
            bg="#0284C7",
            fg="white",
            activebackground="#0369A1",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
            command=self._unlock_all,
        )
        unlock_btn.pack(side="left")

        # 3. Card: System Settings Shortcut
        cfg_card = tk.Frame(body, bg="white", highlightbackground="#D8E4E0", highlightthickness=1)
        cfg_card.pack(fill="x")

        cfg_inner = tk.Frame(cfg_card, bg="white", padx=16, pady=12)
        cfg_inner.pack(fill="x")

        tk.Label(
            cfg_inner,
            text="3. Bảng giá & Tính năng theo gói",
            font=("Segoe UI", 10, "bold"),
            fg="#17313A",
            bg="white",
        ).pack(anchor="w", pady=(0, 6))

        tk.Button(
            cfg_inner,
            text="⚙️ Mở Bảng Quản Lý Tính Năng & Giá Gói...",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
            command=self._open_settings,
        ).pack(anchor="w")

        # ── Footer ───────────────────────────────────────────────────────────
        footer = tk.Frame(self, bg="#E8F0ED", height=50)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        close_btn = tk.Button(
            footer,
            text="Đóng",
            font=("Segoe UI", 9, "bold"),
            bg="#CBD5E1",
            fg="#1E293B",
            activebackground="#94A3B8",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=5,
            command=self.destroy,
        )
        close_btn.pack(side="right", padx=18, pady=8)

    def _toggle_maintenance(self):
        is_on = getattr(self._app, "maintenance_on", False)
        if not is_on:
            msg = simpledialog.askstring(
                "Thông báo bảo trì",
                "Nhập thông báo hiển thị cho người dùng khi mở app:\n(Để trống = dùng thông báo mặc định)",
                parent=self,
                initialvalue="Hệ thống đang nâng cấp định kỳ. Vui lòng thử lại sau 30 phút.",
            )
            if msg is None:
                return
            if not messagebox.askyesno(
                "Xác nhận bật bảo trì",
                "Bạn có chắc muốn BẬT chế độ bảo trì?\n\nTẤT CẢ người dùng sẽ bị chặn truy cập ngay lập tức.",
                parent=self,
            ):
                return
            try:
                r = admin_maintenance_on(msg)
                if r.get("ok"):
                    self._app.maintenance_on = True
                    self._app.show_maintenance_banner(True)
                    self._app.set_status("🔧 Chế độ bảo trì ĐÃ BẬT")
                    self._update_maint_ui(True)
                    messagebox.showinfo("Đã bật bảo trì", "Hệ thống đã chuyển sang chế độ BẢO TRÌ thành công.", parent=self)
                else:
                    messagebox.showerror("Lỗi", r.get("error", "Không bật được bảo trì."), parent=self)
            except Exception as e:
                messagebox.showerror("Lỗi kết nối", str(e), parent=self)
        else:
            if not messagebox.askyesno(
                "Xác nhận tắt bảo trì",
                "Bạn có chắc muốn TẮT chế độ bảo trì?\n\nNgười dùng có giấy phép hoạt động sẽ vào lại được app.",
                parent=self,
            ):
                return
            try:
                r = admin_maintenance_off()
                if r.get("ok"):
                    self._app.maintenance_on = False
                    self._app.show_maintenance_banner(False)
                    self._app.set_status("✅ Chế độ bảo trì đã TẮT")
                    self._update_maint_ui(False)
                    messagebox.showinfo("Đã tắt bảo trì", "Hệ thống đã hoạt động bình thường trở lại.", parent=self)
                else:
                    messagebox.showerror("Lỗi", r.get("error", "Không tắt được bảo trì."), parent=self)
            except Exception as e:
                messagebox.showerror("Lỗi kết nối", str(e), parent=self)

    def _update_maint_ui(self, is_maint: bool):
        if is_maint:
            self._maint_status_frame.configure(bg="#FEE2E2", highlightbackground="#FCA5A5")
            self._maint_status_lbl.configure(
                text="🔴 ĐANG BẬT BẢO TRÌ — Tất cả người dùng đang bị chặn truy cập app.",
                fg="#991B1B",
                bg="#FEE2E2",
            )
            self._maint_toggle_btn.configure(
                text="✅ Tắt chế độ bảo trì",
                bg="#0F9F6E",
                activebackground="#0B7A54",
            )
        else:
            self._maint_status_frame.configure(bg="#ECFDF5", highlightbackground="#A7F3D0")
            self._maint_status_lbl.configure(
                text="🟢 HOẠT ĐỘNG BÌNH THƯỜNG — Người dùng active sử dụng app bình thường.",
                fg="#065F46",
                bg="#ECFDF5",
            )
            self._maint_toggle_btn.configure(
                text="🔧 Bật chế độ bảo trì",
                bg="#DC2626",
                activebackground="#B91C1C",
            )

    def _lock_all(self):
        if not messagebox.askyesno(
            "Cảnh báo: Khóa toàn bộ người dùng",
            "Bạn có chắc muốn KHÓA TẤT CẢ người dùng đang hoạt động (active)?\n\nNgười dùng sẽ không thể truy cập cho đến khi được mở khóa.",
            parent=self,
        ):
            return
        self._app.set_status("⏳ Đang khóa toàn bộ người dùng...")
        try:
            r = admin_lock_all()
            if r.get("ok"):
                messagebox.showinfo("Đã khóa", r.get("message", "Đã khóa toàn bộ người dùng thành công."), parent=self)
                self._app.refresh()
            else:
                messagebox.showerror("Lỗi", r.get("error", "Không thể khóa."), parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi kết nối", str(e), parent=self)

    def _unlock_all(self):
        if not messagebox.askyesno(
            "Xác nhận mở khóa toàn bộ",
            "Mở khóa cho TẤT CẢ người dùng đang bị thu hồi/khóa trong hệ thống?",
            parent=self,
        ):
            return
        self._app.set_status("⏳ Đang mở khóa toàn bộ người dùng...")
        try:
            r = admin_unlock_all()
            if r.get("ok"):
                messagebox.showinfo("Đã mở khóa", r.get("message", "Đã mở khóa toàn bộ thành công."), parent=self)
                self._app.refresh()
            else:
                messagebox.showerror("Lỗi", r.get("error", "Không thể mở khóa."), parent=self)
        except Exception as e:
            messagebox.showerror("Lỗi kết nối", str(e), parent=self)

    def _open_settings(self):
        from admin.dialog_settings import AdminSystemSettingsDialog
        AdminSystemSettingsDialog(self._app)
