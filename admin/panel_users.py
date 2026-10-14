"""
admin/panel_users.py — Panel quản lý người dùng (bảng dữ liệu, toolbar tác vụ hiện đại & context menu).
"""

from __future__ import annotations

import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from config import SUPABASE_URL, SUPABASE_KEY, FEATURE_CATALOG, get_default_features
from admin.constants import TIER_LABELS, STATUS_BG, TIER_STYLES, TIER_OFF_BG, TIER_OFF_FG
from admin.date_picker import ExpiryEditor
from admin.supabase_api import update_api_key, clear_api_key, update_tier, update_expiry
from services.license_manager import (
    admin_add, admin_revoke, admin_restore,
    admin_set_features, get_machine_id, admin_import_users,
)
from admin.dialog_add_user import AddUserDialog
from admin.dialog_system import SystemControlDialog
from admin.dialog_lookup import LookupUserDialog
from admin.dialog_admin_info import AdminInfoDialog


class UserTablePanel(tk.Frame):
    """Panel chính quản lý người dùng: Toolbar tác vụ + Bảng full-width + Context menu."""

    def __init__(self, parent, app, **kw):
        super().__init__(parent, bg="#EDF3F1", **kw)
        self._app = app
        self._filter_after_id: str | None = None
        self._render_after_id: str | None = None
        self._filtered_records: list[dict] = []
        self._pending_rows: list[tuple[str, str, tuple]] = []
        self._build()

    def _build(self):
        # ── 1. Top Action Toolbar ─────────────────────────────────────────────
        top_bar = tk.Frame(self, bg="white", highlightbackground="#D8E4E0", highlightthickness=1)
        top_bar.pack(fill="x", pady=(0, 10))

        # Row 1: Main Action Buttons
        r1 = tk.Frame(top_bar, bg="white", padx=14, pady=10)
        r1.pack(fill="x")

        # Left: Primary Actions
        left_actions = tk.Frame(r1, bg="white")
        left_actions.pack(side="left")

        self._btn_add = tk.Button(
            left_actions,
            text="  ➕ Cấp quyền mới  ",
            font=("Segoe UI", 10, "bold"),
            bg="#0F9F6E",
            fg="white",
            activebackground="#0B7A54",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
            command=self._open_add_user,
        )
        self._btn_add.pack(side="left", padx=(0, 8))

        self._btn_system = tk.Button(
            left_actions,
            text="🛡️ Kiểm soát hệ thống",
            font=("Segoe UI", 9, "bold"),
            bg="#0B2F33",
            fg="white",
            activebackground="#116466",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=8,
            command=self._open_system_controls,
        )
        self._btn_system.pack(side="left", padx=(0, 8))

        self._btn_pricing = tk.Button(
            left_actions,
            text="⚙️ Tính năng & Bảng giá",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=8,
            command=self._open_settings,
        )
        self._btn_pricing.pack(side="left", padx=(0, 8))

        self._btn_lookup = tk.Button(
            left_actions,
            text="🔍 Tra cứu Machine ID",
            font=("Segoe UI", 9),
            bg="#E2E8F0",
            fg="#1E293B",
            activebackground="#CBD5E1",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=8,
            command=self._open_lookup,
        )
        self._btn_lookup.pack(side="left", padx=(0, 8))

        self._btn_admin_info = tk.Button(
            left_actions,
            text="💻 ID Máy Admin",
            font=("Segoe UI", 9),
            bg="#E2E8F0",
            fg="#1E293B",
            activebackground="#CBD5E1",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=8,
            command=self._open_admin_info,
        )
        self._btn_admin_info.pack(side="left")

        # Right: CSV & Refresh
        right_actions = tk.Frame(r1, bg="white")
        right_actions.pack(side="right")

        tk.Button(
            right_actions,
            text="📥 Nhập CSV",
            font=("Segoe UI", 9, "bold"),
            bg="#F1F5F9",
            fg="#334155",
            activebackground="#E2E8F0",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=7,
            command=self._import_csv,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            right_actions,
            text="📤 Xuất CSV",
            font=("Segoe UI", 9, "bold"),
            bg="#F1F5F9",
            fg="#334155",
            activebackground="#E2E8F0",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=7,
            command=self._export_csv,
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            right_actions,
            text="🔄 Làm mới",
            font=("Segoe UI", 9, "bold"),
            bg="#E0F2FE",
            fg="#0369A1",
            activebackground="#BAE6FD",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=7,
            command=self._app.refresh,
        ).pack(side="left")

        # Separator line
        tk.Frame(top_bar, bg="#E2E8F0", height=1).pack(fill="x")

        # Row 2: Search & Filter bar
        r2 = tk.Frame(top_bar, bg="#FAFCFB", padx=14, pady=8)
        r2.pack(fill="x")

        # Left label
        tk.Label(
            r2,
            text="📋 Danh sách giấy phép",
            font=("Segoe UI", 10, "bold"),
            fg="#0B2F33",
            bg="#FAFCFB",
        ).pack(side="left")

        # Right filters
        r2_right = tk.Frame(r2, bg="#FAFCFB")
        r2_right.pack(side="right")

        tk.Label(r2_right, text="Tìm kiếm:", bg="#FAFCFB", fg="#475569", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 4))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._schedule_filter())
        search_entry = ttk.Entry(r2_right, textvariable=self._search_var, width=24, font=("Segoe UI", 9))
        search_entry.pack(side="left", padx=(0, 16), ipady=2)

        tk.Label(r2_right, text="Trạng thái:", bg="#FAFCFB", fg="#475569", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 4))
        self._filter_var = tk.StringVar(value="Tất cả")
        filter_cb = ttk.Combobox(
            r2_right,
            textvariable=self._filter_var,
            values=["Tất cả", "active", "revoked", "expired"],
            width=12,
            state="readonly",
            font=("Segoe UI", 9),
        )
        filter_cb.pack(side="left", ipady=2)
        self._filter_var.trace_add("write", lambda *_: self._schedule_filter())

        # ── 2. Stats summary bar ──────────────────────────────────────────────
        self._stats_lbl = tk.Label(
            self,
            text="  Đang tải danh sách...",
            bg="#E6F4F1",
            fg="#0B2F33",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            padx=14,
            pady=5,
            highlightbackground="#D8E4E0",
            highlightthickness=1,
        )
        self._stats_lbl.pack(fill="x", pady=(0, 6))

        # ── 3. Full-width Treeview Table ──────────────────────────────────────
        tbl_container = tk.Frame(self, bg="white", highlightbackground="#D8E4E0", highlightthickness=1)
        tbl_container.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(tbl_container, orient="vertical")
        vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(tbl_container, orient="horizontal")
        hsb.pack(side="bottom", fill="x")

        cols = ("Machine ID", "Tên người dùng", "Gói cước", "Trạng thái", "API Key", "Hạn dùng", "Ngày cấp", "Lần kiểm tra cuối", "Ghi chú")
        self._tree = ttk.Treeview(
            tbl_container,
            columns=cols,
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="browse",
        )
        vsb.config(command=self._tree.yview)
        hsb.config(command=self._tree.xview)

        cw = {
            "Machine ID": 130,
            "Tên người dùng": 150,
            "Gói cước": 110,
            "Trạng thái": 95,
            "API Key": 85,
            "Hạn dùng": 105,
            "Ngày cấp": 120,
            "Lần kiểm tra cuối": 125,
            "Ghi chú": 180,
        }
        for c, w in cw.items():
            self._tree.heading(c, text=c)
            self._tree.column(c, width=w, minwidth=60, anchor="w")
        self._tree.pack(fill="both", expand=True)

        for status, bg in STATUS_BG.items():
            self._tree.tag_configure(status, background=bg)

        self._tree.bind("<Button-3>", self._show_ctx)
        self._tree.bind("<Double-1>", lambda e: self._on_double_click())

        # ── 4. Context Menu ───────────────────────────────────────────────────
        self._ctx = tk.Menu(self._app, tearoff=0, font=("Segoe UI", 10))
        self._ctx.add_command(label="➕ Cấp quyền mới (Thêm user)", command=self._open_add_user)
        self._ctx.add_separator()
        self._ctx.add_command(label="✅ Kích hoạt lại (Restore)", command=self._ctx_restore)
        self._ctx.add_command(label="🔒 Thu hồi quyền (Revoke)", command=self._ctx_revoke)
        self._ctx.add_separator()
        self._ctx.add_command(label="🔑 Cấp / Cập nhật API Key", command=self._ctx_set_api_key)
        self._ctx.add_command(label="📦 Nâng cấp / Hạ gói cước", command=self._ctx_change_tier)
        self._ctx.add_command(label="📅 Thay đổi hạn sử dụng", command=self._ctx_change_expiry)
        self._ctx.add_command(label="⚙️ Ghi đè tính năng cá nhân", command=self._ctx_features)
        self._ctx.add_separator()
        self._ctx.add_command(label="📋 Sao chép Machine ID", command=self._ctx_copy_mid)
        self._ctx.add_command(label="🔄 Làm mới danh sách", command=self._app.refresh)

    # ── Action Openers ────────────────────────────────────────────────────────

    def _open_add_user(self):
        AddUserDialog(self, self._app)

    def _open_system_controls(self):
        SystemControlDialog(self, self._app)

    def _open_settings(self):
        from admin.dialog_settings import AdminSystemSettingsDialog
        AdminSystemSettingsDialog(self._app)

    def _open_lookup(self):
        LookupUserDialog(self, self._app)

    def _open_admin_info(self):
        AdminInfoDialog(self, self._app)

    def set_maintenance_state(self, is_on: bool):
        if is_on:
            self._btn_system.configure(
                text="🛡️ Hệ thống: [ĐANG BẢO TRÌ]",
                bg="#DC2626",
                activebackground="#B91C1C",
            )
        else:
            self._btn_system.configure(
                text="🛡️ Kiểm soát hệ thống",
                bg="#0B2F33",
                activebackground="#116466",
            )

    # ── Table Filtering & Rendering ───────────────────────────────────────────

    def _schedule_filter(self):
        if self._filter_after_id is not None:
            try:
                self.after_cancel(self._filter_after_id)
            except tk.TclError:
                pass
        self._filter_after_id = self.after(120, self.apply_filter)

    def _cancel_render(self):
        if self._render_after_id is not None:
            try:
                self.after_cancel(self._render_after_id)
            except tk.TclError:
                pass
            self._render_after_id = None

    def _row_values(self, record: dict) -> tuple:
        has_key = "🔑 Có" if record.get("admin_api_key", "") else "—"
        return (
            record.get("machine_id", ""),
            record.get("name", ""),
            TIER_LABELS.get(str(record.get("tier", "")), record.get("tier", "")),
            record.get("status", "?").upper(),
            has_key,
            record.get("expiry", "") or "Vĩnh viễn",
            str(record.get("issued_at", ""))[:16] if record.get("issued_at") else "",
            str(record.get("last_check", ""))[:16] if record.get("last_check") else "Chưa từng",
            record.get("note", ""),
        )

    def _render_rows(self, start: int = 0):
        if start == 0:
            self._tree.delete(*self._tree.get_children())
        end = min(start + 120, len(self._pending_rows))
        for iid, tag, values in self._pending_rows[start:end]:
            try:
                self._tree.insert("", "end", iid=iid, tags=(tag,), values=values)
            except tk.TclError:
                pass
        if end < len(self._pending_rows):
            self._render_after_id = self.after(1, lambda: self._render_rows(end))
        else:
            self._render_after_id = None

    def apply_filter(self, *_):
        self._filter_after_id = None
        self._cancel_render()
        kw = self._search_var.get().lower().strip()
        sf = self._filter_var.get()
        records = list(self._app.all_records)

        if kw:
            records = [r for r in records if (
                kw in str(r.get("machine_id", "")).lower()
                or kw in str(r.get("name", "")).lower()
                or kw in str(r.get("note", "")).lower()
                or kw in str(r.get("tier", "")).lower()
            )]
        if sf != "Tất cả":
            records = [r for r in records if str(r.get("status", "")).lower() == sf.lower()]

        self._filtered_records = records
        total_all = len(self._app.all_records)
        n_act = sum(1 for r in self._app.all_records if r.get("status") == "active")
        n_rev = sum(1 for r in self._app.all_records if r.get("status") == "revoked")
        extra = f"  ●  Hiển thị: {len(records)}" if kw or sf != "Tất cả" else ""
        self._stats_lbl.config(
            text=f"  📊 Tổng: {total_all} tài khoản  ●  🟢 Hoạt động: {n_act}  ●  🔒 Thu hồi: {n_rev}{extra}"
        )

        rows: list[tuple[str, str, tuple]] = []
        seen_iids: dict[str, int] = {}
        for idx, r in enumerate(records):
            tag = r.get("status", "?") if r.get("status", "?") in STATUS_BG else "active"
            base_iid = str(r.get("machine_id", "")) or f"row-{idx}"
            count = seen_iids.get(base_iid, 0)
            seen_iids[base_iid] = count + 1
            iid = base_iid if count == 0 else f"{base_iid}#{count}"
            rows.append((iid, tag, self._row_values(r)))
        self._pending_rows = rows
        self._render_rows(0)

    # ── Context Menu Helpers ─────────────────────────────────────────────────

    def _selected_mid(self) -> str:
        sel = self._tree.selection()
        if not sel:
            return ""
        values = self._tree.item(sel[0], "values")
        return str(values[0]) if values else str(sel[0])

    def _show_ctx(self, event):
        if item := self._tree.identify_row(event.y):
            self._tree.selection_set(item)
            self._ctx.tk_popup(event.x_root, event.y_root)

    def _on_double_click(self):
        mid = self._selected_mid()
        if mid:
            self._ctx_copy_mid()

    def _ctx_copy_mid(self):
        if mid := self._selected_mid():
            self._app.clipboard_clear()
            self._app.clipboard_append(mid)
            self._app.set_status(f"📋 Đã sao chép Machine ID: {mid}")
            messagebox.showinfo("Đã sao chép", f"Đã sao chép Machine ID:\n{mid}", parent=self._app)

    def _ctx_revoke(self):
        mid = self._selected_mid()
        if not mid or not messagebox.askyesno("Xác nhận thu hồi", f"Thu hồi quyền truy cập của Machine ID:\n{mid}?", parent=self._app):
            return
        try:
            r = admin_revoke(mid)
            if r.get("ok"):
                self._app.set_status(f"🔒 Đã thu hồi: {mid}")
                self._app.refresh()
            else:
                messagebox.showwarning("Lỗi", r.get("error", ""), parent=self._app)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self._app)

    def _ctx_restore(self):
        mid = self._selected_mid()
        if not mid:
            return
        try:
            r = admin_restore(mid)
            if r.get("ok"):
                self._app.set_status(f"✅ Đã khôi phục: {mid}")
                self._app.refresh()
            else:
                messagebox.showwarning("Lỗi", r.get("error", ""), parent=self._app)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self._app)

    def _ctx_set_api_key(self):
        mid = self._selected_mid()
        if not mid:
            return
        record = next((r for r in self._app.all_records if r.get("machine_id") == mid), {})
        current_key = record.get("admin_api_key", "")
        name = record.get("name", mid)
        tier = record.get("tier", "basic")

        win = tk.Toplevel(self._app)
        win.title(f"🔑 Cấp API Key — {name} ({mid})")
        win.geometry("600x340")
        win.grab_set()
        win.configure(bg="#F4F8F7")

        header = tk.Frame(win, bg="#0B2F33", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text=f"🔑 CẤP / CẬP NHẬT API KEY: {name}",
            bg="#0B2F33",
            fg="white",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=16, pady=10)

        body = tk.Frame(win, bg="#F4F8F7", padx=16, pady=12)
        body.pack(fill="both", expand=True)

        tk.Label(body, text=f"Machine ID: {mid}  |  Gói: {tier.upper()}", bg="#F4F8F7", fg="#64748B", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 8))

        tk.Label(body, text="API Key (nhập key OpenAI / Anthropic / Gemini riêng cho user này):", bg="#F4F8F7", font=("Segoe UI", 10, "bold"), fg="#17313A").pack(anchor="w", pady=(0, 4))
        key_text = tk.Text(body, height=4, font=("Consolas", 10), wrap="word", relief="solid", borderwidth=1, bg="#FFFFFF")
        key_text.pack(fill="x", pady=(0, 6))
        if current_key:
            key_text.insert("1.0", current_key)

        tk.Label(body, text="Sau khi lưu, người dùng mở app chọn nguồn 'Admin cấp' sẽ tự nhận key này.", bg="#F4F8F7", fg="#64748B", font=("Segoe UI", 8, "italic")).pack(anchor="w")

        def _save():
            new_key = key_text.get("1.0", "end-1c").strip()
            try:
                update_api_key(mid, new_key)
                messagebox.showinfo("Thành công", f"Đã cập nhật API Key cho {name}.", parent=win)
                self._app.set_status(f"✅ Đã cấp API key cho [{name}]")
                win.destroy()
                self._app.refresh()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu API Key:\n{e}", parent=win)

        def _clear():
            try:
                clear_api_key(mid)
                messagebox.showinfo("Đã xóa", f"Đã xóa API Key của {name}.", parent=win)
                self._app.set_status(f"🗑 Đã xóa API key của [{name}]")
                win.destroy()
                self._app.refresh()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa API Key:\n{e}", parent=win)

        btn_f = tk.Frame(win, bg="#E8F0ED", height=50)
        btn_f.pack(fill="x", side="bottom")
        btn_f.pack_propagate(False)

        tk.Button(btn_f, text="  💾 Lưu API Key  ", font=("Segoe UI", 10, "bold"), bg="#0F9F6E", fg="white", relief="flat", cursor="hand2", padx=14, pady=5, command=_save).pack(side="right", padx=(4, 16), pady=8)
        tk.Button(btn_f, text="  🗑 Xóa Key  ", font=("Segoe UI", 9), bg="#EF4444", fg="white", relief="flat", cursor="hand2", padx=10, pady=5, command=_clear).pack(side="right", padx=4, pady=8)
        tk.Button(btn_f, text="Hủy", font=("Segoe UI", 9), bg="#CBD5E1", fg="#1E293B", relief="flat", cursor="hand2", padx=10, pady=5, command=win.destroy).pack(side="right", padx=4, pady=8)

    def _ctx_change_tier(self):
        mid = self._selected_mid()
        if not mid:
            return
        record = next((r for r in self._app.all_records if r.get("machine_id") == mid), {})
        name = record.get("name", mid)
        current_tier = record.get("tier", "basic")

        win = tk.Toplevel(self._app)
        win.title(f"📦 Đổi Gói Cước — {name}")
        win.geometry("460x300")
        win.grab_set()
        win.configure(bg="#F4F8F7")

        header = tk.Frame(win, bg="#0B2F33", height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text=f"📦 ĐỔI GÓI CƯỚC: {name}",
            bg="#0B2F33",
            fg="white",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=16, pady=10)

        body = tk.Frame(win, bg="#F4F8F7", padx=16, pady=12)
        body.pack(fill="both", expand=True)

        tk.Label(body, text=f"Machine ID: {mid}", bg="#F4F8F7", fg="#64748B", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 4))
        tk.Label(body, text=f"Gói hiện tại: {TIER_LABELS.get(current_tier, current_tier)}", bg="#F4F8F7", fg="#0B2F33", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))

        tier_var = tk.StringVar(value=current_tier)
        tf = tk.Frame(body, bg="#F4F8F7")
        tf.pack(fill="x", pady=4)
        tf.columnconfigure((0, 1, 2), weight=1)

        _STYLES = {
            "basic": {"bg": "#64748B", "text": "🥉 BASIC\n2 đề/ngày"},
            "pro": {"bg": "#2563EB", "text": "🥈 PRO\nKhông giới hạn"},
            "premium": {"bg": "#7C3AED", "text": "🏆 PREMIUM\nToàn quyền"},
        }
        btns: dict[str, tk.Label] = {}

        def _sel(t):
            tier_var.set(t)
            for k, b in btns.items():
                if k == t:
                    b.configure(bg=_STYLES[k]["bg"], fg="white", relief="solid", bd=2)
                else:
                    b.configure(bg="#F1F5F9", fg="#64748B", relief="flat", bd=1)

        for ci, t in enumerate(["basic", "pro", "premium"]):
            s = _STYLES[t]
            is_sel = (t == current_tier)
            lbl = tk.Label(
                tf,
                text=s["text"],
                font=("Segoe UI", 9, "bold"),
                bg=s["bg"] if is_sel else "#F1F5F9",
                fg="white" if is_sel else "#64748B",
                relief="solid" if is_sel else "flat",
                bd=2 if is_sel else 1,
                cursor="hand2",
                padx=8,
                pady=12,
                justify="center",
            )
            lbl.grid(row=0, column=ci, sticky="ew", padx=4)
            lbl.bind("<Button-1>", lambda _e, t=t: _sel(t))
            btns[t] = lbl

        def _save():
            new_tier = tier_var.get()
            if new_tier == current_tier:
                win.destroy()
                return
            try:
                update_tier(mid, new_tier)
                messagebox.showinfo("Thành công", f"Đã đổi gói của {name} từ {current_tier.upper()} → {new_tier.upper()}.", parent=win)
                self._app.set_status(f"📦 Đổi gói [{name}]: {current_tier} → {new_tier}")
                win.destroy()
                self._app.refresh()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đổi gói:\n{e}", parent=win)

        btn_f = tk.Frame(win, bg="#E8F0ED", height=50)
        btn_f.pack(fill="x", side="bottom")
        btn_f.pack_propagate(False)

        tk.Button(btn_f, text="  💾 Lưu  ", font=("Segoe UI", 10, "bold"), bg="#0F9F6E", fg="white", relief="flat", cursor="hand2", padx=14, pady=5, command=_save).pack(side="right", padx=(4, 16), pady=8)
        tk.Button(btn_f, text="Hủy", font=("Segoe UI", 9), bg="#CBD5E1", fg="#1E293B", relief="flat", cursor="hand2", padx=10, pady=5, command=win.destroy).pack(side="right", padx=4, pady=8)

    def _ctx_change_expiry(self):
        mid = self._selected_mid()
        if not mid:
            return
        record = next((r for r in self._app.all_records if r.get("machine_id") == mid), {})
        name = record.get("name", mid)
        current_expiry = record.get("expiry", "") or "Vĩnh viễn"

        current_display = current_expiry
        if current_expiry and current_expiry not in ("Vĩnh viễn", "0", ""):
            try:
                d = datetime.strptime(current_expiry, "%Y-%m-%d")
                current_display = d.strftime("%d-%m-%Y")
            except Exception:
                pass

        win = tk.Toplevel(self._app)
        win.title(f"📅 Thay Đổi Hạn Sử Dụng — {name}")
        win.geometry("520x400")
        win.grab_set()
        win.configure(bg="#F4F8F7")

        header = tk.Frame(win, bg="#0B2F33", height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text=f"📅 THAY ĐỔI HẠN SỬ DỤNG: {name}",
            bg="#0B2F33",
            fg="white",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=16, pady=10)

        body = tk.Frame(win, bg="#F4F8F7", padx=16, pady=12)
        body.pack(fill="both", expand=True)

        tk.Label(body, text=f"Machine ID: {mid}", bg="#F4F8F7", fg="#64748B", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 4))
        tk.Label(body, text=f"Hạn hiện tại: {current_display}", bg="#F4F8F7", fg="#0B2F33", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 10))

        pf = tk.Frame(body, bg="#F4F8F7")
        pf.pack(fill="x", pady=4)
        expiry_editor = ExpiryEditor(
            pf,
            bg="#F4F8F7",
            initial_iso=current_expiry if current_expiry not in ("Vĩnh viễn", "0", "") else "",
            day_default=45,
        )
        expiry_editor.pack(fill="x")

        def _save():
            val = expiry_editor.get_display_value()
            try:
                new_expiry = expiry_editor.get_iso_value()
            except ValueError:
                messagebox.showerror("Sai định dạng", "Ngày phải theo định dạng DD-MM-YYYY.\nVD: 31-12-2026", parent=win)
                return
            try:
                update_expiry(mid, new_expiry)
                display = val or "Vĩnh viễn"
                messagebox.showinfo("Thành công", f"Đã cập nhật hạn sử dụng của {name}:\n{current_display} → {display}", parent=win)
                self._app.set_status(f"📅 Đổi hạn [{name}]: {current_display} → {display}")
                win.destroy()
                self._app.refresh()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể cập nhật:\n{e}", parent=win)

        btn_f = tk.Frame(win, bg="#E8F0ED", height=50)
        btn_f.pack(fill="x", side="bottom")
        btn_f.pack_propagate(False)

        tk.Button(btn_f, text="  💾 Lưu  ", font=("Segoe UI", 10, "bold"), bg="#0F9F6E", fg="white", relief="flat", cursor="hand2", padx=14, pady=5, command=_save).pack(side="right", padx=(4, 16), pady=8)
        tk.Button(btn_f, text="Hủy", font=("Segoe UI", 9), bg="#CBD5E1", fg="#1E293B", relief="flat", cursor="hand2", padx=10, pady=5, command=win.destroy).pack(side="right", padx=4, pady=8)

    def _ctx_features(self):
        if mid := self._selected_mid():
            from admin.dialog_features import FeatureDialog
            dlg = FeatureDialog(self._app, mid=mid, record=next((r for r in self._app.all_records if r.get("machine_id") == mid), {}))
            self._app.wait_window(dlg)
            if getattr(dlg, "_saved", False):
                self._app.refresh()

    # ── CSV Import / Export ──────────────────────────────────────────────────

    def _export_csv(self):
        records = list(self._filtered_records)
        if not records:
            messagebox.showinfo("Trống", "Không có dữ liệu để xuất.", parent=self._app)
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Excel", "*.csv"), ("Tất cả", "*.*")],
            title="Lưu danh sách ra file CSV",
            initialfile=f"DanhSach_NguoiDung_{datetime.now().strftime('%Y%m%d')}.csv",
            parent=self._app,
        )
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Machine ID", "Tên người dùng", "Gói", "Trạng thái", "API Key", "Hạn dùng", "Ngày cấp", "Lần kiểm tra cuối", "Ghi chú"])
                for record in records:
                    writer.writerow(self._row_values(record))
            messagebox.showinfo("Thành công", f"Đã xuất dữ liệu ra file:\n{path}", parent=self._app)
            self._app.set_status(f"✅ Đã xuất file: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu file:\n{str(e)}", parent=self._app)

    def _import_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV Excel", "*.csv"), ("Tất cả", "*.*")],
            title="Chọn file CSV danh sách người dùng",
            parent=self._app,
        )
        if not path:
            return
        self._app.set_status("⏳ Đang đọc file CSV...")
        self._app.update_idletasks()
        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                records = list(reader)
            if not records:
                messagebox.showinfo("Trống", "File CSV không có dữ liệu.", parent=self._app)
                return
            users_to_upsert = []
            for row in records:
                mid = (row.get('Machine ID') or row.get('machine_id') or '').strip().upper()
                if not mid:
                    continue
                name = (row.get('Tên người dùng') or row.get('Tên') or row.get('name') or '').strip()
                raw_tier = (row.get('Gói cước') or row.get('Gói') or row.get('tier') or '').lower()
                if 'premium' in raw_tier or 'toàn quyền' in raw_tier or 'pre' in raw_tier:
                    tier = 'premium'
                elif 'pro' in raw_tier:
                    tier = 'pro'
                else:
                    tier = 'basic'
                raw_status = (row.get('Trạng thái') or row.get('status') or '').lower()
                if 'revoked' in raw_status or 'khóa' in raw_status:
                    status = 'revoked'
                elif 'suspended' in raw_status:
                    status = 'suspended'
                else:
                    status = 'active'
                expiry = (row.get('Hạn dùng') or row.get('expiry') or '').strip()
                if expiry.lower() in ['vĩnh viễn', 'none', 'null', '']:
                    expiry = ''
                issued_at = (row.get('Ngày cấp') or row.get('Cấp lúc') or row.get('issued_at') or '').strip()
                if not issued_at:
                    issued_at = datetime.now().isoformat()
                last_check = (row.get('Lần kiểm tra cuối') or row.get('Lần cuối') or row.get('last_check') or '').strip()
                note = (row.get('Ghi chú') or row.get('note') or '').strip()
                user_data = {"machine_id": mid, "name": name, "tier": tier, "status": status, "expiry": expiry, "issued_at": issued_at, "note": note}
                if last_check:
                    user_data["last_check"] = last_check
                users_to_upsert.append(user_data)

            self._app.set_status(f"⏳ Đang đồng bộ {len(users_to_upsert)} người dùng lên Supabase...")
            self._app.update_idletasks()
            res = admin_import_users(users_to_upsert)
            if res.get("ok"):
                messagebox.showinfo("Hoàn tất", f"✅ Đã đồng bộ thành công {len(users_to_upsert)} người dùng lên cơ sở dữ liệu!", parent=self._app)
                self._app.refresh()
            else:
                messagebox.showerror("Lỗi", f"Có lỗi khi đồng bộ lên Supabase:\n{res.get('error')}", parent=self._app)
                self._app.set_status("❌ Lỗi đồng bộ")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc file CSV:\n{str(e)}", parent=self._app)
            self._app.set_status("❌ Lỗi nhập file")


# Compatibility fallback alias for any external caller
UserFormPanel = UserTablePanel
