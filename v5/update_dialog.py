"""Dialog cập nhật CTk-native cho MatrixExamAI V5."""
from __future__ import annotations

import threading
from tkinter import messagebox

import customtkinter as ctk


def _source_label(source: str) -> str:
    return {
        "endpoint": "Máy chủ cập nhật",
        "lms": "Backend LMS",
        "github": "GitHub Releases",
    }.get(str(source or ""), "Máy chủ phát hành")


class UpdateDialogCTk(ctk.CTkToplevel):
    """Hiển thị metadata release và hỗ trợ tải installer nếu có."""

    WIDTH = 620
    HEIGHT = 560

    def __init__(self, parent, info: dict, *, current_version: str = ""):
        super().__init__(parent)
        self.title("Cập nhật MatrixExamAI")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(560, 500)
        self._info = dict(info)
        self._current_version = current_version
        self._downloading = False
        try:
            self.transient(parent)
            self.attributes("-topmost", True)
        except Exception:
            pass

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Escape>", lambda _event: self._close())
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _build(self) -> None:
        info = self._info
        header = ctk.CTkFrame(self, fg_color=("#1D4ED8", "#1E3A8A"), corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text="  🔔  Có phiên bản MatrixExamAI mới",
            font=("Segoe UI", 16, "bold"),
            text_color="white",
        ).pack(anchor="w", padx=18, pady=14)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=14)

        version = str(info.get("version") or "?")
        current = self._current_version or "?"
        meta = ctk.CTkFrame(body)
        meta.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            meta,
            text=f"Phiên bản hiện tại: v{current}    →    Phiên bản mới: v{version}",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(10, 4))

        size = int(info.get("file_size") or 0)
        size_text = f"  •  {size / (1024 * 1024):.1f} MB" if size else ""
        required = "  •  Bắt buộc" if info.get("is_mandatory") else ""
        ctk.CTkLabel(
            meta,
            text=f"Nguồn: {_source_label(info.get('source', ''))}{size_text}{required}",
            text_color=("gray35", "gray70"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(body, text="Nội dung cập nhật", font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x")
        notes = ctk.CTkTextbox(body, height=230, wrap="word")
        notes.pack(fill="both", expand=True, pady=(5, 10))
        notes.insert("1.0", str(info.get("notes") or "Phiên bản mới bao gồm các cải tiến và sửa lỗi."))
        notes.configure(state="disabled")

        self._progress = ctk.CTkProgressBar(body)
        self._progress.set(0)
        self._status = ctk.CTkLabel(body, text="Sẵn sàng.", anchor="w", text_color=("gray35", "gray70"))
        self._status.pack(fill="x", pady=(0, 6))

        actions = ctk.CTkFrame(body, fg_color="transparent")
        actions.pack(fill="x")
        self._download_btn = ctk.CTkButton(
            actions,
            text="⬇  Tải và cài đặt" if info.get("download_url") else "🌐  Mở trang tải",
            width=156,
            command=self._download_or_open,
        )
        self._download_btn.pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            actions,
            text="🌐  Trang phát hành",
            width=140,
            fg_color=("#64748B", "#475569"),
            command=self._open_release_page,
        ).pack(side="left", padx=6)

        if not info.get("is_mandatory"):
            ctk.CTkButton(
                actions,
                text="Bỏ qua bản này",
                width=126,
                fg_color=("#B91C1C", "#7F1D1D"),
                hover_color=("#991B1B", "#5F1313"),
                command=self._skip,
            ).pack(side="right", padx=(6, 0))
            ctk.CTkButton(
                actions,
                text="Nhắc sau",
                width=96,
                fg_color=("#64748B", "#475569"),
                command=self._close,
            ).pack(side="right", padx=6)

    def _download_or_open(self) -> None:
        download_url = str(self._info.get("download_url") or "")
        if not download_url:
            self._open_release_page()
            return
        if self._downloading:
            return
        self._downloading = True
        self._download_btn.configure(state="disabled", text="Đang tải...")
        self._progress.pack(fill="x", before=self._status, pady=(0, 6))

        from services.updater import download_update_async

        def _progress(downloaded: int, total: int) -> None:
            try:
                self.after(0, lambda: self._set_progress(downloaded, total))
            except Exception:
                pass

        def _done(path: str | None) -> None:
            try:
                self.after(0, lambda: self._download_done(path))
            except Exception:
                pass

        download_update_async(
            download_url,
            expected_hash=str(self._info.get("file_hash") or ""),
            require_hash=True,
            progress_callback=_progress,
            done_callback=_done,
        )

    def _set_progress(self, downloaded: int, total: int) -> None:
        ratio = min(1.0, downloaded / total) if total else 0.0
        self._progress.set(ratio)
        if total:
            self._status.configure(
                text=f"Đang tải: {downloaded / 1048576:.1f} / {total / 1048576:.1f} MB ({ratio * 100:.0f}%)"
            )
        else:
            self._status.configure(text=f"Đang tải: {downloaded / 1048576:.1f} MB")

    def _download_done(self, path: str | None) -> None:
        if not path:
            self._downloading = False
            self._download_btn.configure(state="normal", text="⬇  Thử tải lại")
            self._status.configure(text="Không thể tải installer. Kiểm tra mạng và thử lại.")
            return
        self._progress.set(1)
        self._status.configure(text=f"Đã tải xong: {path}")
        if not messagebox.askyesno(
            "Cài đặt cập nhật",
            "Installer đã tải xong. Đóng MatrixExamAI và chạy cài đặt ngay?",
            parent=self,
        ):
            self._downloading = False
            self._download_btn.configure(state="normal", text="⬇  Tải lại")
            return

        self._status.configure(text="Đang tạo snapshot dữ liệu trước khi cập nhật...")
        self._download_btn.configure(state="disabled", text="Đang backup...")

        def _worker() -> None:
            try:
                from services.update_safety import prepare_pre_update_snapshot
                snapshot = prepare_pre_update_snapshot(str(self._info.get("version") or ""))
                self.after(0, lambda snapshot_path=snapshot.path: self._install_after_snapshot(path, snapshot_path))
            except Exception as exc:
                self.after(0, lambda error=str(exc): self._snapshot_failed(path, error))

        threading.Thread(target=_worker, daemon=True, name="pre-update-backup").start()

    def _install_after_snapshot(self, installer_path: str, snapshot_path) -> None:
        self._status.configure(text=f"Đã backup dữ liệu: {snapshot_path.name}. Đang mở installer...")
        from services.updater import install_update
        if install_update(installer_path):
            top = self.master
            self.destroy()
            try:
                top.destroy()
            except Exception:
                pass
            return
        messagebox.showerror(
            "Không thể mở installer",
            f"Đã backup dữ liệu tại:\n{snapshot_path}\n\n"
            f"Bạn có thể chạy installer thủ công:\n{installer_path}",
            parent=self,
        )
        self._downloading = False
        self._download_btn.configure(state="normal", text="⬇  Thử lại")

    def _snapshot_failed(self, installer_path: str, error: str) -> None:
        messagebox.showerror(
            "Không thể backup trước cập nhật",
            "Ứng dụng chưa mở installer để tránh mất dữ liệu.\n\n"
            f"Lỗi: {error}\n\n"
            f"Installer đã tải tại:\n{installer_path}",
            parent=self,
        )
        self._status.configure(text="Cập nhật bị chặn vì chưa tạo được snapshot dữ liệu.")
        self._downloading = False
        self._download_btn.configure(state="normal", text="⬇  Thử lại")

    def _open_release_page(self) -> None:
        from v5.updater import _open_url
        _open_url(str(self._info.get("url") or self._info.get("download_url") or ""))

    def _skip(self) -> None:
        from v5.updater import skip_version
        skip_version(str(self._info.get("version") or ""))
        self._close()

    def _close(self) -> None:
        if self._info.get("is_mandatory"):
            messagebox.showwarning(
                "Cập nhật bắt buộc",
                "Phiên bản này cần được cập nhật trước khi tiếp tục sử dụng.",
                parent=self,
            )
            return
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


class CheckUpdateDialogCTk(ctk.CTkToplevel):
    """Kiểm tra cập nhật thủ công và mở dialog release nếu có."""

    WIDTH = 430
    HEIGHT = 190

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Kiểm tra cập nhật")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.resizable(False, False)
        try:
            self.transient(parent)
            self.attributes("-topmost", True)
        except Exception:
            pass

        ctk.CTkLabel(
            self,
            text="🔄  Kiểm tra cập nhật MatrixExamAI",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(22, 10))
        self._status = ctk.CTkLabel(self, text="Đang kết nối máy chủ phát hành...")
        self._status.pack(pady=8)
        self._close_btn = ctk.CTkButton(self, text="Đóng", width=100, command=self.destroy)
        self.bind("<Escape>", lambda _event: self.destroy())
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass
        self.after(120, self._start)

    def _start(self) -> None:
        from v5 import __version__
        from v5.updater import check_for_update, clear_skip

        clear_skip()

        def _worker():
            result = check_for_update(__version__, include_skipped=True)
            try:
                self.after(0, lambda: self._done(result))
            except Exception:
                pass

        threading.Thread(target=_worker, daemon=True, name="manual-updater").start()

    def _done(self, info: dict | None) -> None:
        if info:
            parent = self.master
            try:
                self.grab_release()
            except Exception:
                pass
            self.destroy()
            show_update_dialog(parent, info)
            return
        from v5 import __version__
        self._status.configure(text=f"✅ Bạn đang dùng phiên bản mới nhất: v{__version__}")
        self._close_btn.pack(pady=(12, 0))


def show_update_dialog(parent, info: dict):
    from v5 import __version__
    return UpdateDialogCTk(parent, info, current_version=__version__)


def open_manual_update_check(parent):
    return CheckUpdateDialogCTk(parent)
