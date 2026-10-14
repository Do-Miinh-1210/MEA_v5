"""
v5/preferences.py — Mini dialog Preferences (Ctrl+,) cho v5.

Khác Settings view (port từ v4 tab_config — phức tạp, có API keys/backend
URL):  Preferences chỉ chứa toggle/dropdown quick mà user hay đổi:

    • Theme: System / Light / Dark
    • Accent color
    • ☑ Tự kiểm tra phiên bản mới khi mở app
    • ☑ Hiện dialog khi gặp lỗi (nếu tắt → chỉ ghi log im lặng)
    • ☑ Tự xuất Word sau khi sinh đề + thư mục lưu mặc định
    • Reset crash log
    • Reset session (xoá v5_session.json)
    • [Open ~/.exam_generator folder]

Mở qua phím Ctrl+, hoặc QuickSwitcher action "preferences".
"""
from __future__ import annotations

import sys
from pathlib import Path

import customtkinter as ctk

from v5 import settings_store


_ACCENT_LABELS = {
    "Xanh dương":  "blue",
    "Xanh lá":     "green",
    "Xanh đậm":    "dark-blue",
    "MEA Custom":  "mea-custom",
}


class PreferencesDialog(ctk.CTkToplevel):
    """Compact preferences dialog."""

    WIDTH = 440
    HEIGHT = 620

    def __init__(self, parent):
        super().__init__(parent)
        self.title("⚙ Tuỳ chọn — MEA v5")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        try: self.attributes("-topmost", True)
        except: pass

        s = settings_store.load()

        # ── Footer info & Close button docked at bottom ───────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(side="bottom", fill="x", pady=(4, 8))

        ctk.CTkButton(footer, text="Đóng", width=100,
                        fg_color=("#6B7280", "#374151"),
                        command=self.destroy
                        ).pack(pady=(0, 4))
        try:
            from v5 import __version__
            ver = __version__
        except Exception:
            ver = "?"
        ctk.CTkLabel(footer,
                      text=f"MEA v{ver}  •  python {sys.version.split()[0]}  •  "
                            f"{sys.platform}",
                      text_color=("#6B7280", "#9CA3AF"),
                      font=("Segoe UI", 9)
                      ).pack()

        # ── Scrollable Body ───────────────────────────────────────────────
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Section: Giao diện ────────────────────────────────────────────
        ctk.CTkLabel(body, text="Giao diện",
                      font=("Segoe UI", 13, "bold"),
                      anchor="w"
                      ).pack(fill="x", padx=14, pady=(12, 4))

        row_theme = ctk.CTkFrame(body, fg_color="transparent")
        row_theme.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(row_theme, text="Theme:", width=120, anchor="w"
                      ).pack(side="left")
        self._theme_var = ctk.StringVar(value=s.get("theme", "System"))
        ctk.CTkOptionMenu(
            row_theme, values=["System", "Light", "Dark"],
            variable=self._theme_var, width=160,
            command=self._on_theme_change
            ).pack(side="left", padx=8)

        row_accent = ctk.CTkFrame(body, fg_color="transparent")
        row_accent.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(row_accent, text="Màu chủ đạo:", width=120, anchor="w"
                      ).pack(side="left")
        inv = {v: k for k, v in _ACCENT_LABELS.items()}
        cur_acc = inv.get(s.get("color_accent", "blue"), "Xanh dương")
        self._accent_var = ctk.StringVar(value=cur_acc)
        ctk.CTkOptionMenu(
            row_accent, values=list(_ACCENT_LABELS.keys()),
            variable=self._accent_var, width=160,
            command=self._on_accent_change
            ).pack(side="left", padx=8)

        # ── Section: Hoạt động ────────────────────────────────────────────
        ctk.CTkLabel(body, text="Hoạt động & Lỗi",
                      font=("Segoe UI", 13, "bold"), anchor="w"
                      ).pack(fill="x", padx=14, pady=(16, 4))

        update_row = ctk.CTkFrame(body, fg_color="transparent")
        update_row.pack(fill="x", padx=14, pady=4)
        self._update_var = ctk.BooleanVar(value=s.get("check_updates", True))
        ctk.CTkCheckBox(update_row, variable=self._update_var,
                          text="Tự kiểm tra phiên bản mới khi mở app",
                          command=lambda: settings_store.set_value(
                              "check_updates", self._update_var.get())
                          ).pack(side="left")
        ctk.CTkButton(update_row, text="Kiểm tra ngay", width=104, height=28,
                        command=self._open_update_check
                        ).pack(side="right")

        self._dialog_var = ctk.BooleanVar(value=s.get("crash_dialog", True))
        ctk.CTkCheckBox(body, variable=self._dialog_var,
                          text="Hiện dialog khi gặp lỗi (tắt = chỉ ghi log)",
                          command=lambda: settings_store.set_value(
                              "crash_dialog", self._dialog_var.get())
                          ).pack(anchor="w", padx=14, pady=4)

        # ── Section: Tạo đề / Xuất Word ──────────────────────────────────
        ctk.CTkLabel(body, text="Tạo đề & Xuất Word",
                      font=("Segoe UI", 13, "bold"), anchor="w"
                      ).pack(fill="x", padx=14, pady=(16, 4))

        try:
            from config import (
                get_auto_export_dir,
                is_auto_export_enabled,
                is_word_auto_convert_tables_enabled,
            )
            auto_export_on = is_auto_export_enabled()
            auto_export_dir = str(get_auto_export_dir())
            auto_table_on = is_word_auto_convert_tables_enabled()
        except Exception:
            auto_export_on = True
            auto_export_dir = str(Path.home() / "Documents")
            auto_table_on = True

        self._auto_export_var = ctk.BooleanVar(value=auto_export_on)
        ctk.CTkCheckBox(body, variable=self._auto_export_var,
                          text="Tự xuất Word ngay sau khi sinh đề",
                          command=self._on_auto_export_change
                          ).pack(anchor="w", padx=14, pady=4)
        self._auto_table_var = ctk.BooleanVar(value=auto_table_on)
        ctk.CTkCheckBox(body, variable=self._auto_table_var,
                          text="Tự chuyển dòng có dấu | thành bảng Word",
                          command=self._on_auto_table_change
                          ).pack(anchor="w", padx=14, pady=4)
        ctk.CTkLabel(
            body,
            text="Tắt nếu công thức hoặc hình vẽ có dấu | bị nhận nhầm là bảng.",
            text_color="gray",
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(fill="x", padx=(38, 14), pady=(0, 2))

        export_row = ctk.CTkFrame(body, fg_color="transparent")
        export_row.pack(fill="x", padx=14, pady=4)
        self._auto_dir_lbl = ctk.CTkLabel(
            export_row, text=self._short_path(auto_export_dir),
            width=210, anchor="w", text_color="gray")
        self._auto_dir_lbl.pack(side="left", padx=(0, 6))
        ctk.CTkButton(export_row, text="📁 Đổi", width=70,
                        command=self._pick_auto_export_dir
                        ).pack(side="left", padx=2)
        ctk.CTkButton(export_row, text="📂 Mở", width=70,
                        command=self._open_auto_export_dir
                        ).pack(side="left", padx=2)

        # ── Section: Bảo trì ──────────────────────────────────────────────
        ctk.CTkLabel(body, text="Bảo trì dữ liệu",
                      font=("Segoe UI", 13, "bold"), anchor="w"
                      ).pack(fill="x", padx=14, pady=(16, 4))

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=4)
        ctk.CTkButton(btn_row, text="🩺 Chẩn đoán",
                        width=115, fg_color=("#0EA5E9", "#075985"),
                        hover_color=("#0284C7", "#0C4A6E"),
                        command=self._run_diagnostics
                        ).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="🛡 Crash log",
                        width=115, command=self._open_crash_log
                        ).pack(side="left", padx=2)
        ctk.CTkButton(btn_row, text="🗑 Xoá session",
                        width=125, fg_color=("#DC2626", "#7F1D1D"),
                        hover_color=("#B91C1C", "#5F1313"),
                        command=self._clear_session
                        ).pack(side="left", padx=2)

        backup_row = ctk.CTkFrame(body, fg_color="transparent")
        backup_row.pack(fill="x", padx=14, pady=4)
        ctk.CTkButton(backup_row, text="📦 Backup dữ liệu (ZIP)",
                        width=180, command=self._export_backup
                        ).pack(side="left", padx=2)
        ctk.CTkButton(backup_row, text="📥 Restore từ ZIP",
                        width=150, fg_color=("#F59E0B", "#92400E"),
                        hover_color=("#D97706", "#78350F"),
                        command=self._import_backup
                        ).pack(side="left", padx=2)

        desk_row = ctk.CTkFrame(body, fg_color="transparent")
        desk_row.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkButton(desk_row, text="📌 Thêm lối tắt Desktop",
                        width=180, fg_color="#10B981", hover_color="#059669",
                        command=self._create_desktop_shortcut
                        ).pack(side="left", padx=2)
        ctk.CTkButton(desk_row, text="📂 Thư mục cài đặt",
                        width=150, command=self._open_install_dir
                        ).pack(side="left", padx=2)

        ctk.CTkButton(body, text="📂 Mở thư mục dữ liệu (~/.exam_generator)",
                        height=32, command=self._open_data_folder
                        ).pack(fill="x", padx=14, pady=(4, 10))

        # ESC to close
        self.bind("<Escape>", lambda e: self.destroy())
        try: self.grab_set()
        except: pass
        try: self.focus_force()
        except: pass

    # ── Handlers ──────────────────────────────────────────────────────────
    def _on_theme_change(self, mode: str):
        ctk.set_appearance_mode(mode)
        settings_store.set_value("theme", mode)

    def _on_accent_change(self, label: str):
        accent = _ACCENT_LABELS.get(label, "blue")
        settings_store.set_value("color_accent", accent)
        from v5.toast import show_toast
        show_toast(self.master if self.master else self,
                    f"Đã đổi sang {label}. Khởi động lại để áp dụng đầy đủ.",
                    kind="info", duration=4)

    def _open_update_check(self):
        from v5.update_dialog import open_manual_update_check
        open_manual_update_check(self)

    @staticmethod
    def _short_path(path: str, max_len: int = 36) -> str:
        text = str(path or "")
        if len(text) <= max_len:
            return text
        return "..." + text[-(max_len - 3):]

    def _on_auto_export_change(self):
        try:
            from config import set_auto_export_enabled
            set_auto_export_enabled(bool(self._auto_export_var.get()))
            from v5.toast import show_toast
            show_toast(self.master if self.master else self,
                        "Đã bật tự xuất Word" if self._auto_export_var.get()
                        else "Đã tắt tự xuất Word",
                        kind="success" if self._auto_export_var.get() else "info")
        except Exception as exc:
            print(f"auto export toggle fail: {exc}")

    def _on_auto_table_change(self):
        try:
            from config import set_word_auto_convert_tables_enabled
            set_word_auto_convert_tables_enabled(bool(self._auto_table_var.get()))
            from v5.toast import show_toast
            show_toast(self.master if self.master else self,
                        "Đã bật chuyển dấu | thành bảng Word" if self._auto_table_var.get()
                        else "Đã tắt chuyển dấu | thành bảng Word",
                        kind="success" if self._auto_table_var.get() else "info")
        except Exception as exc:
            print(f"auto table toggle fail: {exc}")

    def _pick_auto_export_dir(self):
        try:
            from tkinter import filedialog
            from config import get_auto_export_dir, set_auto_export_dir
            current = str(get_auto_export_dir())
            folder = filedialog.askdirectory(
                parent=self, title="Chọn thư mục tự xuất Word",
                initialdir=current)
            if not folder:
                return
            set_auto_export_dir(folder)
            self._auto_dir_lbl.configure(text=self._short_path(folder))
            from v5.toast import show_toast
            show_toast(self.master if self.master else self,
                        "Đã đổi thư mục tự xuất Word", kind="success")
        except Exception as exc:
            print(f"pick auto export dir fail: {exc}")

    def _open_auto_export_dir(self):
        try:
            import os
            import subprocess
            from config import get_auto_export_dir
            folder = get_auto_export_dir()
            if sys.platform == "win32":
                os.startfile(str(folder))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:
            print(f"open auto export dir fail: {exc}")

    def _open_crash_log(self):
        try:
            from v5.crash_reporter import CrashLogViewer
            CrashLogViewer(self)
        except Exception as e:
            print(f"open crash log fail: {e}")

    def _run_diagnostics(self):
        """Chạy chẩn đoán hệ thống (thread) → hiện kết quả trong dialog."""
        import threading
        # Dialog kết quả
        dlg = ctk.CTkToplevel(self)
        dlg.title("🩺 Chẩn đoán hệ thống")
        dlg.geometry("620x440")
        try: dlg.attributes("-topmost", True)
        except Exception: pass
        dlg.bind("<Escape>", lambda e: dlg.destroy())

        ctk.CTkLabel(dlg, text="🩺 Đang kiểm tra cài đặt…",
                      font=("Segoe UI", 14, "bold")).pack(pady=(14, 4))
        status = ctk.CTkLabel(dlg, text="", text_color="gray",
                                font=("Segoe UI", 10))
        status.pack()
        box = ctk.CTkTextbox(dlg, font=("Consolas", 10), wrap="none")
        box.pack(fill="both", expand=True, padx=14, pady=10)
        box.insert("1.0", "Đang chạy các kiểm tra...\n(TikZ render cần "
                          "vài giây để biên dịch LaTeX)")
        box.configure(state="disabled")

        def _progress(name):
            try: dlg.after(0, lambda: status.configure(text=f"Đang kiểm tra: {name}…"))
            except Exception: pass

        def _worker():
            try:
                from v5.diagnostics import run_diagnostics, format_report
                results = run_diagnostics(progress_cb=_progress)
                report = format_report(results)
            except Exception as e:
                report = f"Lỗi chẩn đoán: {e}"
            def _show():
                try:
                    if not dlg.winfo_exists(): return
                    status.configure(text="✓ Hoàn tất")
                    box.configure(state="normal")
                    box.delete("1.0", "end")
                    box.insert("1.0", report)
                    box.configure(state="disabled")
                except Exception: pass
            try: dlg.after(0, _show)
            except Exception: pass

        threading.Thread(target=_worker, daemon=True).start()
        try: dlg.grab_set()
        except Exception: pass

    def _clear_session(self):
        from tkinter import messagebox
        try:
            from v5.session_autosave import clear_session
            if messagebox.askyesno(
                "Xoá session",
                "Xoá phiên đề tạm thời (v5_session.json)?\n"
                "Lần mở sau sẽ không có prompt khôi phục.",
                parent=self):
                clear_session()
                from v5.toast import show_toast
                show_toast(self.master if self.master else self,
                            "✓ Đã xoá session", kind="success")
        except Exception as e:
            print(f"clear session fail: {e}")

    def _create_desktop_shortcut(self):
        from services.desktop_shortcut import create_desktop_shortcut
        ok, msg = create_desktop_shortcut()
        from v5.toast import show_toast
        if ok:
            show_toast(self.master if self.master else self,
                       "Đã thêm lối tắt MEA v5 ra Màn hình chính (Desktop)!",
                       kind="success", duration=4)
        else:
            show_toast(self.master if self.master else self,
                       f"Không thể tạo lối tắt: {msg}", kind="error", duration=5)

    def _open_install_dir(self):
        from services.desktop_shortcut import open_install_directory
        open_install_directory()

    def _open_data_folder(self):
        try:
            import subprocess
            folder = Path.home() / ".exam_generator"
            folder.mkdir(parents=True, exist_ok=True)
            if sys.platform == "win32":
                subprocess.Popen(["explorer", str(folder)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as e:
            print(f"open folder fail: {e}")

    def _export_backup(self):
        from tkinter import messagebox
        from services.local_backup import create_local_backup
        from services.task_events import record_task_event

        include_sensitive = messagebox.askyesno(
            "Bao gồm dữ liệu nhạy cảm?",
            "Backup có cần bao gồm token LMS và API key đã mã hóa không?\n\n"
            "Có: chuyển máy đầy đủ, cần lưu file ZIP thật cẩn thận.\n"
            "Không: backup dữ liệu đề, NHCH, ảnh, settings và history.",
            parent=self)

        try:
            result = create_local_backup(include_sensitive=include_sensitive)
            size_mb = result.total_bytes / (1024 * 1024)
            record_task_event(
                kind="backup",
                title="Tạo backup dữ liệu",
                status="success",
                message=f"{result.file_count} file, {size_mb:.2f} MB",
                meta={"path": str(result.path), "include_sensitive": include_sensitive},
            )
            from v5.toast import show_toast
            show_toast(self.master if self.master else self,
                        f"✓ Đã backup {result.file_count} file → {result.path.name}",
                        kind="success", duration=5)
            if messagebox.askyesno(
                "Backup OK",
                f"Đã lưu vào:\n{result.path}\n\nMở thư mục chứa?",
                parent=self):
                try:
                    import subprocess
                    if sys.platform == "win32":
                        subprocess.Popen(["explorer", "/select,", str(result.path)])
                    else:
                        subprocess.Popen(["xdg-open", str(result.path.parent)])
                except Exception: pass
        except Exception as exc:
            try:
                record_task_event(
                    kind="backup",
                    title="Tạo backup dữ liệu",
                    status="error",
                    message=str(exc),
                )
            except Exception:
                pass
            messagebox.showerror("Backup fail",
                                  f"Không tạo được file ZIP: {exc}", parent=self)

    def _import_backup(self):
        from tkinter import filedialog, messagebox
        from config import APP_DIR
        from services.local_backup import preview_local_backup, restore_local_backup
        from services.task_events import record_task_event

        path = filedialog.askopenfilename(
            parent=self, title="Chọn file backup ZIP",
            initialdir=str(Path(APP_DIR) / "backups"),
            filetypes=[("ZIP archive", "*.zip")])
        if not path: return

        try:
            preview = preview_local_backup(path)
        except Exception as exc:
            messagebox.showerror("File hỏng",
                                  f"Không đọc được ZIP: {exc}",
                                  parent=self)
            return

        file_list = "\n".join(f"  • {item.get('path', '?')}"
                              for item in preview.files[:10])
        warning_text = ""
        if preview.warnings:
            warning_text = "\nCảnh báo:\n  • " + "\n  • ".join(preview.warnings[:5])
        sensitive_text = "Có" if preview.include_sensitive else "Không"
        msg = (f"Backup tạo: {preview.created_at or '?'}\n"
               f"Số file: {preview.file_count}\n"
               f"Dung lượng: {preview.total_bytes / (1024 * 1024):.2f} MB\n"
               f"Bao gồm dữ liệu nhạy cảm: {sensitive_text}\n\n{file_list}"
               f"{warning_text}\n\n"
               "Restore sẽ ghi đè dữ liệu hiện tại.\n"
               "App sẽ tạo restore-point đầy đủ trước khi ghi đè.\n\n"
               "Tiếp tục?")
        if not messagebox.askyesno("Xác nhận restore", msg, parent=self):
            return

        try:
            result = restore_local_backup(
                path,
                overwrite=True,
                create_restore_point=True,
            )
            record_task_event(
                kind="restore",
                title="Khôi phục backup",
                status="success",
                message=f"{result.restored_count} file, bỏ qua {result.skipped_count}",
                meta={
                    "path": str(result.path),
                    "restore_point": str(result.restore_point or ""),
                },
            )
            from v5.toast import show_toast
            show_toast(self.master if self.master else self,
                        f"✓ Restore {result.restored_count} file. Khởi động lại app để áp dụng.",
                        kind="success", duration=6)
        except Exception as exc:
            try:
                record_task_event(
                    kind="restore",
                    title="Khôi phục backup",
                    status="error",
                    message=str(exc),
                    meta={"path": str(path)},
                )
            except Exception:
                pass
            messagebox.showerror("Restore fail",
                                  f"Không restore được: {exc}",
                                  parent=self)
