"""
ui/dialog_update.py — Dialog thông báo cập nhật phiên bản mới.

Hiển thị:
  - Phiên bản hiện tại vs. phiên bản mới
  - Changelog (danh sách thay đổi)
  - Nút: Cập nhật ngay / Nhắc sau / Bỏ qua bản này
  - Progress bar khi đang tải
"""

from __future__ import annotations

import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

BLUE = "#1F497D"
BG = "#F9F7F4"
GREEN = "#10B981"
RED = "#EF4444"


def _source_label(source: str, asset_name: str = "") -> str:
    label = {
        "endpoint": "Máy chủ cập nhật",
        "lms": "Backend LMS",
        "github": "GitHub Releases",
    }.get(str(source or ""), "Máy chủ phát hành")
    return f"{label} ({asset_name})" if asset_name else label


class UpdateDialog(tk.Toplevel):
    """Dialog thông báo có phiên bản mới."""

    def __init__(
        self,
        parent,
        update_info: dict,
        current_version: str = "",
        auto_start: bool = False,
        auto_install: bool = False,
    ):
        super().__init__(parent)
        from ui import set_dialog_icon
        try:
            set_dialog_icon(self)
        except Exception:
            pass

        self.title("Cập nhật phần mềm")
        self.geometry("520x480")
        self.resizable(False, False)
        self.configure(bg=BG)

        self._info = update_info
        self._current = current_version
        self._auto_start = auto_start
        self._auto_install = auto_install
        self._result = "later"  # "update" | "skip" | "later"
        self._downloading = False

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_later)

        # Center on screen
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

        self.grab_set()
        self.focus_set()

        if self._auto_start:
            self.after(500, self._on_update)

    @property
    def result(self) -> str:
        return self._result

    def _build(self):
        info = self._info
        is_mandatory = info.get("is_mandatory", False)
        new_ver = info.get("version", "?")
        changelog = (
            info.get("changelog")
            or info.get("notes")
            or info.get("release_notes")
            or ""
        )
        file_size = info.get("file_size", 0)
        source = info.get("source", "")
        asset_name = info.get("asset_name", "")

        # ── Header ──
        hdr = tk.Frame(self, bg=BLUE)
        hdr.pack(fill="x")

        icon_text = "🔒" if is_mandatory else "🔔"
        title_text = "Đang chuẩn bị cập nhật!" if self._auto_start else (
            "Cập nhật bắt buộc!" if is_mandatory else "Có phiên bản mới!"
        )
        tk.Label(hdr, text=f"  {icon_text}  {title_text}",
                 bg=BLUE, fg="white",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=12, pady=10)

        # ── Version info ──
        ver_f = tk.Frame(self, bg=BG)
        ver_f.pack(fill="x", padx=20, pady=(16, 8))

        tk.Label(ver_f, text="Phiên bản hiện tại:", bg=BG, fg="#6B7280",
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=2)
        tk.Label(ver_f, text=f"v{self._current}", bg=BG, fg="#374151",
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", padx=8)

        tk.Label(ver_f, text="Phiên bản mới:", bg=BG, fg="#6B7280",
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=2)
        tk.Label(ver_f, text=f"v{new_ver}", bg=BG, fg=GREEN,
                 font=("Segoe UI", 11, "bold")).grid(row=1, column=1, sticky="w", padx=8)

        if file_size > 0:
            size_mb = file_size / (1024 * 1024)
            tk.Label(ver_f, text="Dung lượng:", bg=BG, fg="#6B7280",
                     font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=2)
            tk.Label(ver_f, text=f"{size_mb:.1f} MB", bg=BG, fg="#374151",
                     font=("Segoe UI", 9)).grid(row=2, column=1, sticky="w", padx=8)

        if source:
            tk.Label(ver_f, text="Nguồn:", bg=BG, fg="#6B7280",
                     font=("Segoe UI", 9)).grid(row=3, column=0, sticky="w", pady=2)
            tk.Label(ver_f, text=_source_label(source, asset_name),
                     bg=BG, fg="#374151",
                     font=("Segoe UI", 9)).grid(row=3, column=1, sticky="w", padx=8)

        # ── Changelog ──
        cl_f = ttk.LabelFrame(self, text="  Nội dung cập nhật  ")
        cl_f.pack(fill="both", expand=True, padx=20, pady=(4, 8))

        cl_text = tk.Text(cl_f, font=("Segoe UI", 9), wrap="word",
                          bg="#FFFFFF", fg="#374151", relief="flat",
                          height=10, padx=8, pady=6)
        cl_text.pack(fill="both", expand=True, padx=4, pady=4)

        if changelog:
            cl_text.insert("1.0", changelog)
        else:
            cl_text.insert("1.0", "Phiên bản mới với nhiều cải tiến và sửa lỗi.")
        cl_text.config(state="disabled")

        # ── Progress bar (ẩn ban đầu) ──
        self._progress_frame = tk.Frame(self, bg=BG)
        # Không pack ngay — chỉ hiện khi download

        self._progress_var = tk.DoubleVar(value=0)
        self._progress_bar = ttk.Progressbar(
            self._progress_frame, variable=self._progress_var,
            maximum=100, length=400, mode="determinate",
        )
        self._progress_bar.pack(fill="x", padx=20, pady=4)

        self._progress_label = tk.Label(
            self._progress_frame, text="", bg=BG, fg="#6B7280",
            font=("Segoe UI", 8),
        )
        self._progress_label.pack(padx=20)

        # ── Buttons ──
        btn_f = tk.Frame(self, bg=BG)
        btn_f.pack(fill="x", padx=20, pady=(4, 16))

        self._btn_update = tk.Button(
            btn_f, text="⬇  Cập nhật ngay",
            font=("Segoe UI", 10, "bold"),
            bg=GREEN, fg="white", activebackground="#059669",
            relief="flat", cursor="hand2", padx=16, pady=8,
            command=self._on_update,
        )
        self._btn_update.pack(side="left", padx=4)

        if not is_mandatory and not self._auto_install:
            tk.Button(
                btn_f, text="Nhắc sau",
                font=("Segoe UI", 9),
                bg="#E5E7EB", fg="#374151", activebackground="#D1D5DB",
                relief="flat", cursor="hand2", padx=12, pady=6,
                command=self._on_later,
            ).pack(side="left", padx=4)

            tk.Button(
                btn_f, text="Bỏ qua bản này",
                font=("Segoe UI", 9),
                bg="#FEE2E2", fg="#991B1B", activebackground="#FECACA",
                relief="flat", cursor="hand2", padx=12, pady=6,
                command=self._on_skip,
            ).pack(side="left", padx=4)

        if is_mandatory or self._auto_install:
            tk.Label(btn_f, text="⚠ Bạn phải cập nhật để tiếp tục sử dụng.",
                     bg=BG, fg=RED,
                     font=("Segoe UI", 8, "italic")).pack(side="right", padx=8)

    # ── Actions ──

    def _on_update(self):
        """Bắt đầu tải và cài đặt bản cập nhật."""
        if self._downloading:
            return

        self._downloading = True
        self._btn_update.config(state="disabled", text="⏳ Đang tải cập nhật...")
        self._progress_frame.pack(fill="x", before=self._btn_update.master)
        self.update_idletasks()

        from services.updater import download_update_async

        download_url = self._info.get("download_url", "")
        file_hash = self._info.get("file_hash", "")

        if not download_url:
            messagebox.showerror("Lỗi", "Không tìm thấy link tải.", parent=self)
            self._downloading = False
            self._btn_update.config(state="normal", text="⬇  Cập nhật ngay")
            return

        def _on_progress(downloaded, total):
            if total > 0:
                pct = (downloaded / total) * 100
                self.after(0, lambda: self._update_progress(pct, downloaded, total))

        def _on_done(file_path):
            self.after(0, lambda: self._on_download_done(file_path))

        download_update_async(
            download_url=download_url,
            expected_hash=file_hash,
            require_hash=True,
            progress_callback=_on_progress,
            done_callback=_on_done,
        )

    def _update_progress(self, pct: float, downloaded: int, total: int):
        """Cập nhật progress bar (gọi từ main thread)."""
        self._progress_var.set(pct)
        dl_mb = downloaded / (1024 * 1024)
        total_mb = total / (1024 * 1024)
        self._progress_label.config(
            text=f"Đã tải: {dl_mb:.1f} / {total_mb:.1f} MB ({pct:.0f}%)"
        )

    def _on_download_done(self, file_path: Optional[str]):
        """Xử lý sau khi download xong."""
        if not file_path:
            messagebox.showerror(
                "Lỗi tải xuống",
                "Không thể tải bản cập nhật.\n"
                "Vui lòng kiểm tra kết nối mạng và thử lại.",
                parent=self,
            )
            self._downloading = False
            self._btn_update.config(state="normal", text="⬇  Cập nhật ngay")
            self._progress_frame.pack_forget()
            return

        self._progress_var.set(100)
        self._progress_label.config(text="Tải xong! Đang chuẩn bị cài đặt...")
        self.update_idletasks()

        if self._auto_install:
            ok = True
        else:
            ok = messagebox.askyesno(
                "Cài đặt cập nhật",
                f"Đã tải xong bản v{self._info.get('version', '?')}.\n\n"
                "Ứng dụng sẽ đóng lại để cài đặt bản mới.\n"
                "Bạn có muốn cài đặt ngay?",
                parent=self,
            )

        if ok:
            self._backup_then_install(file_path)
        else:
            self._downloading = False
            self._btn_update.config(state="normal", text="⬇  Cập nhật ngay")
            self._progress_label.config(text=f"Installer đã tải tại: {file_path}")

    def _backup_then_install(self, installer_path: str):
        """Tạo snapshot dữ liệu bắt buộc trước khi mở installer."""
        self._progress_label.config(
            text="Đang tạo snapshot dữ liệu trước khi cập nhật..."
        )
        self._btn_update.config(state="disabled", text="Đang backup...")
        self.update_idletasks()

        def _worker():
            try:
                from services.update_safety import prepare_pre_update_snapshot
                snapshot = prepare_pre_update_snapshot(
                    str(self._info.get("version") or "")
                )
                self.after(
                    0,
                    lambda snapshot_path=snapshot.path: self._install_after_snapshot(
                        installer_path,
                        snapshot_path,
                    ),
                )
            except Exception as exc:
                self.after(
                    0,
                    lambda error=str(exc): self._snapshot_failed(installer_path, error),
                )

        threading.Thread(
            target=_worker,
            daemon=True,
            name="pre-update-backup",
        ).start()

    def _install_after_snapshot(self, installer_path: str, snapshot_path):
        """Mở installer sau khi snapshot đã tạo thành công."""
        self._progress_label.config(
            text=f"Đã backup dữ liệu: {snapshot_path.name}. Đang mở installer..."
        )
        from services.updater import install_update
        if install_update(installer_path):
            self._result = "update"
            self.destroy()
            sys.exit(0)

        messagebox.showerror(
            "Lỗi",
            "Không thể chạy trình cài đặt.\n"
            f"Đã backup dữ liệu tại:\n{snapshot_path}\n\n"
            f"File installer đã lưu tại:\n{installer_path}\n\n"
            "Bạn có thể chạy thủ công.",
            parent=self,
        )
        self._downloading = False
        self._btn_update.config(state="normal", text="⬇  Thử lại")

    def _snapshot_failed(self, installer_path: str, error: str):
        """Chặn nâng cấp nếu không tạo được snapshot dữ liệu."""
        messagebox.showerror(
            "Không thể backup trước cập nhật",
            "Ứng dụng chưa mở installer để tránh mất dữ liệu.\n\n"
            f"Lỗi: {error}\n\n"
            f"Installer đã tải tại:\n{installer_path}",
            parent=self,
        )
        self._progress_label.config(
            text="Cập nhật bị chặn vì chưa tạo được snapshot dữ liệu."
        )
        self._downloading = False
        self._btn_update.config(state="normal", text="⬇  Thử lại")

    def _on_later(self):
        """Nhắc lại sau."""
        if self._info.get("is_mandatory", False):
            # Bắt buộc → không cho đóng, thoát app
            if messagebox.askyesno(
                "Cập nhật bắt buộc",
                "Bản cập nhật này là bắt buộc.\n"
                "Nếu không cập nhật, ứng dụng sẽ thoát.\n\n"
                "Bạn có muốn thoát?",
                parent=self,
            ):
                self._result = "later"
                self.destroy()
                sys.exit(0)
            return
        self._result = "later"
        self.destroy()

    def _on_skip(self):
        """Bỏ qua phiên bản này."""
        from services.updater import skip_version
        skip_version(self._info.get("version", ""))
        self._result = "skip"
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  Dialog kiểm tra cập nhật thủ công (từ menu/settings)
# ══════════════════════════════════════════════════════════════════════════════

class CheckUpdateDialog(tk.Toplevel):
    """Dialog kiểm tra cập nhật thủ công — hiển thị trạng thái checking."""

    def __init__(self, parent, current_version: str = ""):
        super().__init__(parent)
        from ui import set_dialog_icon
        try:
            set_dialog_icon(self)
        except Exception:
            pass

        self.title("Kiểm tra cập nhật")
        self.geometry("400x200")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._current = current_version
        self._parent = parent

        self._build()
        self._check()

        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

        self.grab_set()

    def _build(self):
        hdr = tk.Frame(self, bg=BLUE)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  🔄  Kiểm tra cập nhật",
                 bg=BLUE, fg="white",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=12, pady=8)

        self._status_label = tk.Label(
            self, text="⏳ Đang kiểm tra...",
            bg=BG, fg="#374151",
            font=("Segoe UI", 10),
        )
        self._status_label.pack(expand=True)

        self._btn_frame = tk.Frame(self, bg=BG)
        self._btn_frame.pack(fill="x", padx=20, pady=(0, 16))

    def _check(self):
        from services.updater import check_for_update_async, clear_skip
        clear_skip()  # Xóa skip khi user chủ động kiểm tra

        def _callback(result):
            self.after(0, lambda: self._on_result(result))

        check_for_update_async(callback=_callback, include_skipped=True)

    def _on_result(self, result: Optional[dict]):
        if result:
            # Có bản mới → đóng dialog này và mở UpdateDialog
            self.destroy()
            UpdateDialog(self._parent, result, self._current)
        else:
            self._status_label.config(
                text=f"✅ Bạn đang dùng phiên bản mới nhất (v{self._current}).",
                fg=GREEN,
            )
            tk.Button(
                self._btn_frame, text="  Đóng  ",
                font=("Segoe UI", 9),
                bg="#E5E7EB", fg="#374151",
                relief="flat", cursor="hand2", padx=12, pady=6,
                command=self.destroy,
            ).pack(pady=4)
