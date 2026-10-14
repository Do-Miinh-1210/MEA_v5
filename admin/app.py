"""
admin/app.py - AdminApp shell.

This module owns the desktop admin layout and wires the existing admin panels
into a cleaner dashboard-style shell.
"""

from __future__ import annotations

import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

if getattr(sys, "frozen", False):
    _DIR = Path(sys.executable).resolve().parent
else:
    _DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_DIR))

from config import SUPABASE_URL, SUPABASE_KEY, APP_NAME, APP_VERSION
from services.license_manager import admin_list_with_settings


class AdminApp(tk.Tk):
    BG = "#EDF3F1"
    PANEL = "#FFFFFF"
    PANEL_SOFT = "#F7FAF9"
    SIDEBAR = "#0B2F33"
    SIDEBAR_ACTIVE = "#116466"
    SIDEBAR_MUTED = "#9CC9C3"
    TEXT = "#17313A"
    MUTED = "#667985"
    BORDER = "#D8E4E0"
    SUCCESS = "#0F9F6E"
    DANGER = "#D84A3A"
    WARNING = "#D99A22"
    BLUE = "#2563EB"

    NAV_ITEMS = (
        ("users", "Users", "Người dùng"),
        ("stats", "Stats", "Thống kê"),
        ("logs", "Logs", "Log hoạt động"),
        ("exports", "Export", "Xuất dữ liệu"),
    )

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} - Quản trị giấy phép")
        self.geometry("1280x820")
        self.minsize(1060, 680)
        self.configure(bg=self.BG)

        try:
            self.state("zoomed")
        except Exception:
            pass

        try:
            for icon_name in ("icon3.ico", "icon_app.ico"):
                icon_path = _DIR / "assets" / icon_name
                if icon_path.exists():
                    self.iconbitmap(default=str(icon_path))
                    break
        except Exception:
            pass

        self.maintenance_on = False
        self.all_records: list[dict] = []
        self._nav_buttons: dict[str, tk.Button] = {}
        self._pages: dict[str, tk.Widget] = {}
        self._metric_vars: dict[str, tk.StringVar] = {}
        self._active_section = "users"
        self._refresh_running = False
        self._refresh_pending = False

        self._configure_styles()
        self._build()
        self._check_supabase_config()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=self.BG)
        style.configure("Admin.TLabelframe", background=self.PANEL, bordercolor=self.BORDER, relief="solid")
        style.configure(
            "Admin.TLabelframe.Label",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "Treeview",
            background=self.PANEL,
            fieldbackground=self.PANEL,
            foreground=self.TEXT,
            rowheight=30,
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background="#E8F0ED",
            foreground=self.TEXT,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )
        style.map("Treeview", background=[("selected", "#CFE8E5")], foreground=[("selected", self.TEXT)])
        style.configure("TEntry", fieldbackground="#FFFFFF", bordercolor=self.BORDER, lightcolor=self.BORDER)
        style.configure("TCombobox", fieldbackground="#FFFFFF", bordercolor=self.BORDER, lightcolor=self.BORDER)

    def _build(self) -> None:
        self._shell = tk.Frame(self, bg=self.BG)
        self._shell.pack(fill="both", expand=True)

        self._build_sidebar(self._shell)
        self._build_main(self._shell)
        self._build_statusbar()

    def _build_sidebar(self, parent: tk.Widget) -> None:
        sidebar = tk.Frame(parent, bg=self.SIDEBAR, width=250)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=self.SIDEBAR)
        brand.pack(fill="x", padx=18, pady=(22, 18))

        logo_box = tk.Frame(brand, bg=self.SIDEBAR_ACTIVE, width=42, height=42)
        logo_box.pack(side="left")
        logo_box.pack_propagate(False)
        tk.Label(logo_box, text="MEA", bg=self.SIDEBAR_ACTIVE, fg="white", font=("Segoe UI", 10, "bold")).pack(expand=True)

        text_box = tk.Frame(brand, bg=self.SIDEBAR)
        text_box.pack(side="left", padx=(10, 0), fill="x", expand=True)
        tk.Label(text_box, text="Admin Center", bg=self.SIDEBAR, fg="white", font=("Segoe UI", 14, "bold"), anchor="w").pack(fill="x")
        tk.Label(text_box, text=f"Desktop v{APP_VERSION}", bg=self.SIDEBAR, fg=self.SIDEBAR_MUTED, font=("Segoe UI", 9), anchor="w").pack(fill="x")

        nav = tk.Frame(sidebar, bg=self.SIDEBAR)
        nav.pack(fill="x", padx=12, pady=(4, 0))
        for key, icon, label in self.NAV_ITEMS:
            btn = tk.Button(
                nav,
                text=f"  {icon}   {label}",
                anchor="w",
                bd=0,
                relief="flat",
                padx=16,
                pady=12,
                cursor="hand2",
                font=("Segoe UI", 10, "bold"),
                command=lambda section=key: self._show_section(section),
            )
            btn.pack(fill="x", pady=3)
            self._nav_buttons[key] = btn

        footer = tk.Frame(sidebar, bg=self.SIDEBAR)
        footer.pack(side="bottom", fill="x", padx=14, pady=16)
        tk.Button(
            footer,
            text="Refresh dữ liệu",
            bg="#E9B44C",
            fg="#17313A",
            activebackground="#F2C96B",
            bd=0,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=10,
            command=self.refresh,
        ).pack(fill="x")
        tk.Button(
            footer,
            text="Cấu hình Supabase",
            bg="#DDE9E5",
            fg=self.TEXT,
            activebackground="#CFE0DC",
            bd=0,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=10,
            command=self._show_setup_dialog,
        ).pack(fill="x", pady=(8, 0))
        tk.Label(
            footer,
            text="Không chia sẻ bản admin",
            bg=self.SIDEBAR,
            fg="#F7B0A5",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(10, 0))

    def _build_main(self, parent: tk.Widget) -> None:
        self._main = tk.Frame(parent, bg=self.BG)
        self._main.pack(side="left", fill="both", expand=True)

        header = tk.Frame(self._main, bg=self.BG)
        header.pack(fill="x", padx=22, pady=(20, 12))
        header.columnconfigure(0, weight=1)

        title_box = tk.Frame(header, bg=self.BG)
        title_box.grid(row=0, column=0, sticky="ew")
        tk.Label(
            title_box,
            text="LICENSE OPERATIONS",
            bg=self.BG,
            fg=self.SIDEBAR_ACTIVE,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="Quản trị giấy phép và tài khoản MEA",
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="Theo dõi trạng thái, cấp quyền, khóa truy cập và xuất dữ liệu trong một màn hình.",
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(3, 0))

        self._conn_lbl = tk.Label(
            header,
            text="Chưa kết nối",
            bg="#FDE8E4",
            fg="#A63A2F",
            padx=14,
            pady=8,
            font=("Segoe UI", 10, "bold"),
        )
        self._conn_lbl.grid(row=0, column=1, sticky="ne", padx=(14, 0))

        metrics = tk.Frame(self._main, bg=self.BG)
        metrics.pack(fill="x", padx=22, pady=(0, 14))
        for i, (key, label, color) in enumerate(
            (
                ("total", "Tổng người dùng", self.BLUE),
                ("active", "Đang hoạt động", self.SUCCESS),
                ("revoked", "Đã thu hồi", self.DANGER),
                ("maintenance", "Bảo trì", self.WARNING),
            )
        ):
            metrics.columnconfigure(i, weight=1)
            self._metric_vars[key] = tk.StringVar(value="-")
            self._metric_card(metrics, i, label, self._metric_vars[key], color)

        self._maint_banner = tk.Frame(self._main, bg="#B83227")
        tk.Label(
            self._maint_banner,
            text="Chế độ bảo trì đang bật. Người dùng đang bị chặn cho đến khi tắt bảo trì.",
            bg="#B83227",
            fg="white",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=16, pady=9)

        self._content_host = tk.Frame(self._main, bg=self.BG)
        self._content_host.pack(fill="both", expand=True, padx=22, pady=(0, 16))
        self._content_host.rowconfigure(0, weight=1)
        self._content_host.columnconfigure(0, weight=1)

        users_page = tk.Frame(self._content_host, bg=self.BG)
        self._pages["users"] = users_page
        self._build_users_tab(users_page)

        from admin.panel_stats import StatsPanel
        from admin.panel_logs import LogViewerPanel
        from admin.panel_exports import ExportManagerPanel

        self._stats_panel = StatsPanel(self._content_host, self)
        self._logs_panel = LogViewerPanel(self._content_host, self)
        self._exports_panel = ExportManagerPanel(self._content_host, self)
        self._pages["stats"] = self._stats_panel
        self._pages["logs"] = self._logs_panel
        self._pages["exports"] = self._exports_panel

        for page in self._pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self._show_section("users")

    def _metric_card(self, parent: tk.Widget, column: int, label: str, var: tk.StringVar, color: str) -> None:
        card = tk.Frame(parent, bg=self.PANEL, highlightbackground=self.BORDER, highlightthickness=1)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0), ipady=4)
        stripe = tk.Frame(card, bg=color, width=4)
        stripe.pack(side="left", fill="y")
        body = tk.Frame(card, bg=self.PANEL)
        body.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        tk.Label(body, textvariable=var, bg=self.PANEL, fg=color, font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(body, text=label, bg=self.PANEL, fg=self.MUTED, font=("Segoe UI", 9)).pack(anchor="w")

    def _build_users_tab(self, parent: tk.Widget) -> None:
        from admin.panel_users import UserTablePanel

        self._user_table = UserTablePanel(parent, self)
        self._user_table.pack(fill="both", expand=True)

    def _build_statusbar(self) -> None:
        statusbar = tk.Frame(self, bg="#DDE9E5", height=30)
        statusbar.pack(fill="x", side="bottom")
        self._status_var = tk.StringVar(value="Sẵn sàng")
        tk.Label(
            statusbar,
            textvariable=self._status_var,
            bg="#DDE9E5",
            fg=self.TEXT,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(side="left", padx=14, pady=5)
        tk.Label(
            statusbar,
            text=f"{APP_NAME} Admin v{APP_VERSION}",
            bg="#DDE9E5",
            fg=self.MUTED,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="right", padx=14, pady=5)

    def _show_section(self, section: str) -> None:
        self._active_section = section
        for key, btn in self._nav_buttons.items():
            active = key == section
            btn.configure(
                bg=self.SIDEBAR_ACTIVE if active else self.SIDEBAR,
                fg="white" if active else self.SIDEBAR_MUTED,
                activebackground=self.SIDEBAR_ACTIVE,
                activeforeground="white",
            )
        page = self._pages.get(section)
        if page is not None:
            page.tkraise()
        if section == "stats":
            self._stats_panel.refresh_stats()
        elif section == "logs" and not self._logs_panel._logs:
            self._logs_panel.refresh_logs()

    def _update_overview(self) -> None:
        total = len(self.all_records)
        active = sum(1 for r in self.all_records if r.get("status") == "active")
        revoked = sum(1 for r in self.all_records if r.get("status") == "revoked")
        self._metric_vars["total"].set(str(total))
        self._metric_vars["active"].set(str(active))
        self._metric_vars["revoked"].set(str(revoked))
        self._metric_vars["maintenance"].set("Bật" if self.maintenance_on else "Tắt")

    def set_status(self, text: str) -> None:
        self._status_var.set(text)

    def refresh(self) -> None:
        if self._refresh_running:
            self._refresh_pending = True
            self.set_status("Đang tải dữ liệu, sẽ làm mới lại ngay sau lượt hiện tại...")
            return

        self._refresh_running = True
        self._refresh_pending = False
        self.set_status("Đang tải danh sách từ Supabase...")
        self._conn_lbl.config(text="Đang đồng bộ...", bg="#FFF2D9", fg="#9A6618")

        def _worker() -> None:
            try:
                result = admin_list_with_settings()
                error: Exception | None = None
            except Exception as exc:
                result = None
                error = exc
            self.after(0, lambda: self._finish_refresh(result, error))

        threading.Thread(target=_worker, daemon=True, name="AdminRefresh").start()

    def _finish_refresh(self, result: dict | None, error: Exception | None) -> None:
        self._refresh_running = False
        try:
            if error is not None:
                raise error
            if result is None:
                raise RuntimeError("Không nhận được dữ liệu từ Supabase.")
            if not result.get("ok"):
                raise Exception(result.get("error"))
            self.all_records = result.get("records", [])
            self.maintenance_on = bool(result.get("maintenance_mode", False))
            self.show_maintenance_banner(self.maintenance_on)
            if hasattr(self._user_table, "set_maintenance_state"):
                self._user_table.set_maintenance_state(self.maintenance_on)
            self._user_table.apply_filter()
            self._update_overview()
            self._conn_lbl.config(text="Đã kết nối Supabase", bg="#E0F4EC", fg="#087251")
            self.set_status(f"Tải xong: {len(self.all_records)} người dùng")
            if self._active_section == "stats":
                self._stats_panel.refresh_stats()
        except Exception as exc:
            self._conn_lbl.config(text="Lỗi kết nối", bg="#FDE8E4", fg="#A63A2F")
            detail = self._format_refresh_error(exc)
            self.set_status(f"Lỗi: {detail}")
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu:\n{detail}", parent=self)
        finally:
            if self._refresh_pending:
                self.after(50, self.refresh)

    def _format_refresh_error(self, exc: Exception) -> str:
        raw = str(exc)
        lower = raw.lower()
        if "getaddrinfo failed" in lower or "name resolution" in lower or "non-existent domain" in lower:
            return (
                "Không phân giải được domain Supabase.\n"
                f"URL hiện tại: {SUPABASE_URL or '(chưa cấu hình)'}\n\n"
                "Project Supabase có thể đã bị xóa, đổi project-ref hoặc URL trong .env/config.py đã cũ. "
                "Bấm 'Cấu hình Supabase' để nhập lại Project URL và API Key đúng."
            )
        if "timed out" in lower or "timeout" in lower:
            return (
                "Kết nối Supabase bị timeout. Kiểm tra mạng, VPN/proxy hoặc thử lại sau.\n"
                f"URL hiện tại: {SUPABASE_URL or '(chưa cấu hình)'}"
            )
        return raw

    def show_maintenance_banner(self, show: bool) -> None:
        if show:
            if not self._maint_banner.winfo_ismapped():
                self._maint_banner.pack(fill="x", padx=22, pady=(0, 12), before=self._content_host)
        else:
            self._maint_banner.pack_forget()
        if "maintenance" in self._metric_vars:
            self._metric_vars["maintenance"].set("Bật" if show else "Tắt")

    def _check_supabase_config(self) -> None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            self._show_setup_dialog()
        else:
            self.refresh()

    def _show_setup_dialog(self) -> None:
        win = tk.Toplevel(self)
        win.title("Cấu hình Supabase")
        win.geometry("620x350")
        win.configure(bg=self.BG)
        win.grab_set()

        tk.Label(
            win,
            text="Cấu hình Supabase Database",
            font=("Segoe UI", 14, "bold"),
            fg=self.TEXT,
            bg=self.BG,
        ).pack(pady=(18, 4))

        steps = ttk.LabelFrame(win, text="Thông tin kết nối")
        steps.pack(fill="x", padx=20, pady=8)
        for step in (
            "Tìm thông tin tại Supabase: Project Settings -> API.",
            "Dùng API key anon / public cho admin desktop hiện tại.",
        ):
            tk.Label(steps, text=step, font=("Segoe UI", 9), fg=self.MUTED, anchor="w", bg=self.PANEL).pack(anchor="w", padx=12, pady=1)

        tk.Label(win, text="Project URL:", font=("Segoe UI", 10, "bold"), fg=self.TEXT, bg=self.BG).pack(anchor="w", padx=20, pady=(10, 2))
        url_var = tk.StringVar()
        ttk.Entry(win, textvariable=url_var, font=("Consolas", 10), width=70).pack(padx=20, fill="x", ipady=5)

        tk.Label(win, text="Project API Key:", font=("Segoe UI", 10, "bold"), fg=self.TEXT, bg=self.BG).pack(anchor="w", padx=20, pady=(10, 2))
        key_var = tk.StringVar()
        ttk.Entry(win, textvariable=key_var, font=("Consolas", 10), width=70).pack(padx=20, fill="x", ipady=5)

        def save_url() -> None:
            import os

            url = url_var.get().strip()
            key = key_var.get().strip()
            if not url.startswith("https://"):
                messagebox.showwarning("URL không hợp lệ", "URL phải bắt đầu bằng https://", parent=win)
                return
            if not key:
                messagebox.showwarning("Thiếu API Key", "Vui lòng nhập API Key.", parent=win)
                return

            env_path = _DIR / ".env"
            lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
            new_lines: list[str] = []
            found_url = found_key = False
            for line in lines:
                if line.strip().startswith("SUPABASE_URL="):
                    new_lines.append(f"SUPABASE_URL={url}")
                    found_url = True
                elif line.strip().startswith("SUPABASE_KEY="):
                    new_lines.append(f"SUPABASE_KEY={key}")
                    found_key = True
                else:
                    new_lines.append(line)
            if not found_url:
                new_lines.append(f"SUPABASE_URL={url}")
            if not found_key:
                new_lines.append(f"SUPABASE_KEY={key}")
            env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            os.environ["SUPABASE_URL"] = url
            os.environ["SUPABASE_KEY"] = key
            messagebox.showinfo("Đã lưu", "Đã lưu cấu hình Supabase. Khởi động lại admin_tool để áp dụng.", parent=win)
            win.destroy()
            sys.exit(0)

        tk.Button(
            win,
            text="Lưu và thoát",
            font=("Segoe UI", 11, "bold"),
            bg=self.SUCCESS,
            fg="white",
            activebackground="#0C7E58",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
            command=save_url,
        ).pack(pady=16)
