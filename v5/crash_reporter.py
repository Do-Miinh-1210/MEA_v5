"""
v5/crash_reporter.py — Bắt mọi exception chưa handle và ghi lại để debug.

Hooks 3 nguồn lỗi:
    1. sys.excepthook           — main thread Python exceptions
    2. threading.excepthook     — background thread exceptions
    3. Tk.report_callback_exception — Tkinter event-loop callbacks

Tính năng:
    • Ghi crash vào ~/.exam_generator/crashes.jsonl (JSONL append-only)
    • Privacy scrub: thay user dir, API key, password trong traceback
    • Hiện dialog xin lỗi user với "Sao chép TB" / "Mở thư mục log" / "Đóng"
    • CrashLogViewer: dialog xem lịch sử (open qua Ctrl+T → "crash log")
    • Optional Sentry: nếu env SENTRY_DSN set → init sentry_sdk (gọn không
      bắt buộc — app vẫn chạy nếu thiếu sentry_sdk)

Usage trong ModernApp:
    from v5.crash_reporter import install_crash_handlers
    install_crash_handlers(app)
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

_log = logging.getLogger(__name__)

CRASH_LOG = Path.home() / ".exam_generator" / "crashes.jsonl"
_MAX_ENTRIES = 200       # chỉ giữ 200 crash gần nhất
_SENTRY_INITED = False
_APP_REF = None          # weak ref tới app — đổ dialog cha


# ── Privacy scrub: ẩn user dir, API keys, password trong text ──────────────
_USER_HOME = str(Path.home())
_SCRUB_PATTERNS = [
    (re.compile(re.escape(_USER_HOME), re.IGNORECASE), "<HOME>"),
    (re.compile(r'(?i)(api[_-]?key["\']?\s*[:=]\s*["\']?)([\w\-\.]{8,})'),
     r'\1<SCRUBBED>'),
    (re.compile(r'(?i)(password["\']?\s*[:=]\s*["\']?)([^"\'\s]{4,})'),
     r'\1<SCRUBBED>'),
    (re.compile(r'(?i)(token["\']?\s*[:=]\s*["\']?)([\w\-\.]{20,})'),
     r'\1<SCRUBBED>'),
    (re.compile(r'(eyJ[\w\-]+\.[\w\-]+\.[\w\-]+)'),     # JWT
     '<JWT-SCRUBBED>'),
    (re.compile(r'(sk-[\w\-]{20,})'),                    # OpenAI/Anthropic key
     '<SK-SCRUBBED>'),
    (re.compile(r'(AIzaSy[\w\-]{20,})'),                 # Google AI Key
     '<GOOGLE-KEY-SCRUBBED>'),
]

# Các exception benign — chỉ log với context, KHÔNG show dialog:
# Phần lớn là race condition khi user navigate khỏi view giữa lúc bg thread
# fetch xong + gọi widget.configure trên widget đã destroy.
_BENIGN_PATTERNS = [
    re.compile(r'invalid command name "\.!.*"'),        # widget destroyed
    re.compile(r'application has been destroyed'),       # mainloop ended
    re.compile(r'bad window path name', re.IGNORECASE),
    re.compile(r'can\'t invoke "[^"]+" command'),
]


def _is_benign(exc_val) -> bool:
    """True nếu lỗi này là benign race condition — không cần dialog."""
    msg = str(exc_val) if exc_val else ""
    for pat in _BENIGN_PATTERNS:
        if pat.search(msg):
            return True
    return False


def _scrub(text: str) -> str:
    """Xoá thông tin nhạy cảm khỏi text trước khi save/show."""
    if not text:
        return text
    for pat, repl in _SCRUB_PATTERNS:
        text = pat.sub(repl, text)
    return text


# ── Log crash entry ────────────────────────────────────────────────────────
def _log_crash(exc_type, exc_val, exc_tb, *, context: str = "main"):
    """Append 1 crash entry vào JSONL. Best-effort — never raise."""
    try:
        tb_text = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
        tb_scrub = _scrub(tb_text)
        entry = {
            "ts":        datetime.now().isoformat(timespec="seconds"),
            "context":   context,
            "exc_type":  exc_type.__name__ if exc_type else "Unknown",
            "exc_msg":   _scrub(str(exc_val))[:500],
            "traceback": tb_scrub[-4000:],   # cap 4KB
            "python":    sys.version.split()[0],
            "platform":  sys.platform,
        }
        try:
            from v5 import __version__
            entry["app_version"] = __version__
        except Exception: pass

        CRASH_LOG.parent.mkdir(parents=True, exist_ok=True)
        # Append
        with CRASH_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        # Rotate nếu > _MAX_ENTRIES
        _maybe_rotate()

        # Forward to Sentry nếu init
        if _SENTRY_INITED:
            try:
                import sentry_sdk
                sentry_sdk.capture_exception((exc_type, exc_val, exc_tb))
            except Exception: pass

        return entry
    except Exception as e:
        _log.warning("log_crash fail: %s", e)
        return None


def _maybe_rotate():
    """Giữ tối đa _MAX_ENTRIES dòng gần nhất."""
    try:
        if not CRASH_LOG.exists(): return
        lines = CRASH_LOG.read_text(encoding="utf-8").splitlines()
        if len(lines) <= _MAX_ENTRIES: return
        keep = lines[-_MAX_ENTRIES:]
        CRASH_LOG.write_text("\n".join(keep) + "\n", encoding="utf-8")
    except Exception: pass


def load_crashes() -> list[dict]:
    """Đọc tất cả crash entry, mới nhất đứng đầu."""
    if not CRASH_LOG.exists(): return []
    try:
        out = []
        for line in CRASH_LOG.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line: continue
            try: out.append(json.loads(line))
            except: continue
        out.reverse()    # newest first
        return out
    except Exception as e:
        _log.warning("load_crashes fail: %s", e)
        return []


def clear_crashes() -> bool:
    try:
        CRASH_LOG.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def export_crashes_zip(output_path: str | None = None) -> str | None:
    """Pack crashes.jsonl + system_info.txt vào ZIP để user gửi support.

    Returns: absolute path tới file ZIP, hoặc None nếu fail.
    """
    import io
    import platform as plat
    import zipfile
    from datetime import datetime

    try:
        # Default location: ~/Desktop hoặc home
        if not output_path:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            desktop = Path.home() / "Desktop"
            target = desktop if desktop.exists() else Path.home()
            output_path = str(target / f"mea_crashes_{ts}.zip")

        out = Path(output_path)

        # System info text
        sysinfo = io.StringIO()
        sysinfo.write(f"=== MEA Crash Export ===\n")
        sysinfo.write(f"Generated: {datetime.now().isoformat()}\n\n")
        try:
            from v5 import __version__
            sysinfo.write(f"App version: {__version__}\n")
        except Exception: pass
        sysinfo.write(f"Python:      {sys.version}\n")
        sysinfo.write(f"Platform:    {sys.platform}\n")
        sysinfo.write(f"OS:          {plat.platform()}\n")
        sysinfo.write(f"Machine:     {plat.machine()}\n")
        sysinfo.write(f"Processor:   {plat.processor()}\n")
        sysinfo.write(f"\nFrozen (EXE): {getattr(sys, 'frozen', False)}\n")
        if getattr(sys, "frozen", False):
            sysinfo.write(f"Executable:  {sys.executable}\n")

        # Filter env vars (only MEA_* + safe ones)
        sysinfo.write(f"\n=== Env vars (filtered) ===\n")
        for k in sorted(os.environ.keys()):
            if k.startswith("MEA_") or k in (
                "OS", "PROCESSOR_ARCHITECTURE", "LANG", "LC_ALL"):
                val = os.environ[k]
                # Scrub if might be sensitive
                if any(s in k.lower() for s in
                        ("key", "secret", "token", "password", "dsn")):
                    val = "<SCRUBBED>"
                sysinfo.write(f"  {k} = {val[:120]}\n")

        # Counts
        crashes = load_crashes()
        sysinfo.write(f"\nCrash count: {len(crashes)}\n")
        if crashes:
            sysinfo.write(f"Oldest: {crashes[-1].get('ts', '?')}\n")
            sysinfo.write(f"Newest: {crashes[0].get('ts', '?')}\n")

        # Build ZIP
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("system_info.txt", sysinfo.getvalue())
            if CRASH_LOG.exists():
                zf.write(CRASH_LOG, arcname="crashes.jsonl")
            else:
                zf.writestr("crashes.jsonl", "")

        return str(out)
    except Exception as e:
        _log.warning("export_crashes_zip fail: %s", e)
        return None


# ── Crash dialog (báo user khi có lỗi) ─────────────────────────────────────
def _show_crash_dialog(exc_type, exc_val, tb_text: str):
    """Hiện messagebox kèm option sao chép / mở log folder.

    Chỉ hiện 1 dialog tại 1 thời điểm (anti-spam).
    """
    if getattr(_show_crash_dialog, "_active", False):
        return
    _show_crash_dialog._active = True

    def _do():
        try:
            import tkinter as tk
            from tkinter import messagebox
            short = f"{exc_type.__name__}: {str(exc_val)[:200]}"
            full = _scrub(tb_text)
            parent = _APP_REF if _APP_REF is not None else None
            try:
                # Detail dialog với 3 nút
                _CrashDialog(parent, short, full).wait_for_close()
            except Exception:
                # Fallback messagebox đơn giản
                messagebox.showerror(
                    "Lỗi không xử lý được",
                    f"Ứng dụng gặp lỗi:\n\n{short}\n\n"
                    f"Đã ghi vào ~/.exam_generator/crashes.jsonl",
                    parent=parent)
        finally:
            _show_crash_dialog._active = False

    # Schedule vào main loop (an toàn từ thread khác)
    if _APP_REF is not None:
        try:
            _APP_REF.after(0, _do)
            return
        except Exception: pass
    _do()


class _CrashDialog:
    """Modal dialog: hiển thị traceback + 3 button.

    Dùng CTk nếu app đã có; fallback Tk nếu chưa.
    """

    def __init__(self, parent, summary: str, full_tb: str):
        self._closed = False
        try:
            import customtkinter as ctk
            self._build_ctk(ctk, parent, summary, full_tb)
        except Exception:
            self._build_tk(parent, summary, full_tb)

    def _build_ctk(self, ctk, parent, summary, full_tb):
        self.win = ctk.CTkToplevel(parent) if parent else ctk.CTk()
        self.win.title("Lỗi không xử lý được — MEA v5")
        self.win.geometry("700x500")
        try: self.win.attributes("-topmost", True)
        except: pass

        ctk.CTkLabel(self.win, text="⚠️  Ứng dụng gặp lỗi",
                      font=("Segoe UI", 16, "bold"),
                      text_color=("#DC2626", "#F87171")
                      ).pack(pady=(16, 4))
        ctk.CTkLabel(self.win, text=summary,
                      font=("Segoe UI", 11),
                      wraplength=640
                      ).pack(padx=20, pady=(0, 12))

        # Traceback (read-only scrollable)
        tb_box = ctk.CTkTextbox(self.win, height=300,
                                  font=("Consolas", 10),
                                  wrap="none")
        tb_box.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        tb_box.insert("1.0", full_tb)
        tb_box.configure(state="disabled")

        # Buttons row
        btn_row = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))

        def _copy():
            try:
                self.win.clipboard_clear()
                self.win.clipboard_append(full_tb)
                ctk.CTkLabel(btn_row, text="✓ Đã sao chép",
                              text_color="#10B981",
                              font=("Segoe UI", 10)).pack(side="left", padx=8)
            except Exception: pass

        def _open_folder():
            try:
                import subprocess
                if sys.platform == "win32":
                    subprocess.Popen(["explorer", str(CRASH_LOG.parent)])
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(CRASH_LOG.parent)])
                else:
                    subprocess.Popen(["xdg-open", str(CRASH_LOG.parent)])
            except Exception: pass

        ctk.CTkButton(btn_row, text="📋 Sao chép",
                        width=120, command=_copy).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="📂 Mở thư mục log",
                        width=160, command=_open_folder).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text="Đóng",
                        width=100,
                        fg_color=("#6B7280", "#374151"),
                        command=self._close).pack(side="right", padx=4)

        self.win.protocol("WM_DELETE_WINDOW", self._close)
        try: self.win.grab_set()
        except: pass

    def _build_tk(self, parent, summary, full_tb):
        import tkinter as tk
        self.win = tk.Toplevel(parent) if parent else tk.Tk()
        self.win.title("Lỗi — MEA v5")
        self.win.geometry("700x500")
        tk.Label(self.win, text="⚠️ Ứng dụng gặp lỗi",
                  font=("Segoe UI", 14, "bold"), fg="#DC2626").pack(pady=10)
        tk.Label(self.win, text=summary, wraplength=640).pack(padx=20)
        txt = tk.Text(self.win, font=("Consolas", 9), wrap="none")
        txt.insert("1.0", full_tb)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True, padx=20, pady=8)
        tk.Button(self.win, text="Đóng", command=self._close).pack(pady=8)
        self.win.protocol("WM_DELETE_WINDOW", self._close)

    def _close(self):
        self._closed = True
        try: self.win.grab_release()
        except: pass
        try: self.win.destroy()
        except: pass

    def wait_for_close(self):
        try:
            self.win.wait_window()
        except Exception: pass


# ── CrashLogViewer — Xem lịch sử crash ────────────────────────────────────
class CrashLogViewer:
    """Dialog liệt kê tất cả crash từ JSONL, click 1 entry → xem chi tiết."""

    def __init__(self, parent):
        import customtkinter as ctk
        self.win = ctk.CTkToplevel(parent)
        self.win.title("Lịch sử lỗi — MEA v5")
        self.win.geometry("800x550")
        try: self.win.attributes("-topmost", True)
        except: pass
        # ESC to close
        self.win.bind("<Escape>", lambda e: self.win.destroy())
        try: self.win.focus_force()
        except: pass

        # Header
        hdr = ctk.CTkFrame(self.win, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(12, 6))
        crashes = load_crashes()
        ctk.CTkLabel(hdr, text=f"🛡  {len(crashes)} crash đã ghi nhận",
                      font=("Segoe UI", 13, "bold")
                      ).pack(side="left")
        ctk.CTkButton(hdr, text="🗑 Xoá tất cả", width=120, height=28,
                        fg_color=("#DC2626", "#7F1D1D"),
                        hover_color=("#B91C1C", "#5F1313"),
                        command=lambda: self._clear()
                        ).pack(side="right")
        ctk.CTkButton(hdr, text="📦 Export ZIP", width=120, height=28,
                        fg_color=("#10B981", "#065F46"),
                        hover_color=("#059669", "#047857"),
                        command=lambda: self._export_zip()
                        ).pack(side="right", padx=4)
        ctk.CTkButton(hdr, text="📂 Mở folder", width=120, height=28,
                        command=lambda: self._open_folder()
                        ).pack(side="right", padx=4)

        # 2-column layout: list trái, detail phải
        body = ctk.CTkFrame(self.win, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=6)
        body.grid_columnconfigure(0, weight=2, minsize=280)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        self._list = ctk.CTkScrollableFrame(body, label_text="Crash entries")
        self._list.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self._detail = ctk.CTkTextbox(body, font=("Consolas", 9), wrap="none")
        self._detail.grid(row=0, column=1, sticky="nsew")
        self._detail.insert("1.0", "← Chọn 1 crash entry để xem chi tiết\n")
        self._detail.configure(state="disabled")

        if not crashes:
            ctk.CTkLabel(self._list, text="(Chưa có crash nào — yay!)",
                          text_color=("#6B7280", "#9CA3AF"),
                          font=("Segoe UI", 11)).pack(pady=20)
        else:
            for i, c in enumerate(crashes):
                ts = c.get("ts", "?")[:19]
                etype = c.get("exc_type", "?")
                ctx   = c.get("context", "?")
                label = f"#{i+1}  {ts}\n  {etype}  •  {ctx}"
                btn = ctk.CTkButton(
                    self._list, text=label, anchor="w",
                    height=44, font=("Segoe UI", 10),
                    fg_color=("#F3F4F6", "#293548"),
                    text_color=("#1F2937", "#F1F5F9"),
                    hover_color=("#DBEAFE", "#1E3A8A"),
                    command=lambda cc=c: self._show_detail(cc))
                btn.pack(fill="x", padx=2, pady=2)

    def _show_detail(self, entry: dict):
        text = (
            f"Time:     {entry.get('ts', '?')}\n"
            f"Context:  {entry.get('context', '?')}\n"
            f"Type:     {entry.get('exc_type', '?')}\n"
            f"Message:  {entry.get('exc_msg', '?')}\n"
            f"Version:  {entry.get('app_version', '?')}\n"
            f"Python:   {entry.get('python', '?')}\n"
            f"Platform: {entry.get('platform', '?')}\n"
            f"{'-' * 60}\n"
            f"{entry.get('traceback', '')}\n"
        )
        self._detail.configure(state="normal")
        self._detail.delete("1.0", "end")
        self._detail.insert("1.0", text)
        self._detail.configure(state="disabled")

    def _clear(self):
        from tkinter import messagebox
        if messagebox.askyesno("Xoá lịch sử",
                                "Xoá toàn bộ crash log? Không khôi phục được.",
                                parent=self.win):
            clear_crashes()
            try: self.win.destroy()
            except: pass

    def _open_folder(self):
        try:
            import subprocess
            if sys.platform == "win32":
                subprocess.Popen(["explorer", str(CRASH_LOG.parent)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(CRASH_LOG.parent)])
            else:
                subprocess.Popen(["xdg-open", str(CRASH_LOG.parent)])
        except Exception: pass

    def _export_zip(self):
        from tkinter import filedialog, messagebox
        from datetime import datetime
        # Cho user chọn vị trí save
        default_name = f"mea_crashes_{datetime.now():%Y%m%d_%H%M%S}.zip"
        path = filedialog.asksaveasfilename(
            parent=self.win, title="Export crash log",
            defaultextension=".zip",
            initialfile=default_name,
            filetypes=[("ZIP archive", "*.zip")])
        if not path: return
        result = export_crashes_zip(path)
        if result:
            if messagebox.askyesno(
                "Export thành công",
                f"Đã lưu vào:\n{result}\n\nMở thư mục chứa file?",
                parent=self.win):
                try:
                    import subprocess
                    if sys.platform == "win32":
                        subprocess.Popen(["explorer", "/select,", result])
                    else:
                        subprocess.Popen(["xdg-open", str(Path(result).parent)])
                except Exception: pass
        else:
            messagebox.showerror("Export fail",
                                  "Không tạo được file ZIP. Xem console log.",
                                  parent=self.win)


# ── Optional Sentry init ──────────────────────────────────────────────────
def _init_sentry():
    """Init sentry_sdk nếu env SENTRY_DSN set + module installed."""
    global _SENTRY_INITED
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn: return False
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=0.0,    # chỉ error reporting, không trace
            send_default_pii=False,    # privacy
            release=_get_version(),
        )
        _SENTRY_INITED = True
        _log.info("Sentry initialized")
        return True
    except ImportError:
        _log.info("sentry_sdk not installed — skip")
    except Exception as e:
        _log.warning("Sentry init fail: %s", e)
    return False


def _get_version() -> str:
    try:
        from v5 import __version__
        return f"mea-v5@{__version__}"
    except Exception:
        return "mea-v5@unknown"


# ── Install all hooks ─────────────────────────────────────────────────────
def install_crash_handlers(app=None, *, show_dialog: bool = True):
    """Cài tất cả crash handler. Gọi 1 lần lúc khởi động app.

    Args:
        app: ModernApp instance (dùng làm parent cho dialog)
        show_dialog: True = show modal khi crash; False = chỉ log
    """
    global _APP_REF
    _APP_REF = app

    # 1. sys.excepthook (main thread)
    _orig_excepthook = sys.excepthook

    def _hook_main(exc_type, exc_val, exc_tb):
        tb_text = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
        # Bỏ qua KeyboardInterrupt — không log lỗi user-initiated
        if issubclass(exc_type, KeyboardInterrupt):
            _orig_excepthook(exc_type, exc_val, exc_tb)
            return
        _log_crash(exc_type, exc_val, exc_tb, context="sys.excepthook")
        if show_dialog and not _is_benign(exc_val):
            _show_crash_dialog(exc_type, exc_val, tb_text)
        _orig_excepthook(exc_type, exc_val, exc_tb)

    sys.excepthook = _hook_main

    # 2. threading.excepthook
    def _hook_thread(args):
        tb_text = "".join(traceback.format_exception(
            args.exc_type, args.exc_value, args.exc_traceback))
        _log_crash(args.exc_type, args.exc_value, args.exc_traceback,
                    context=f"thread:{args.thread.name if args.thread else '?'}")
        if show_dialog and not _is_benign(args.exc_value):
            _show_crash_dialog(args.exc_type, args.exc_value, tb_text)

    threading.excepthook = _hook_thread

    # 3. Tkinter callback exception (chạy trong event loop)
    if app is not None:
        def _hook_tk(self, exc_type, exc_val, exc_tb):
            tb_text = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            # Race widget destroyed — log nhẹ, không dialog
            if _is_benign(exc_val):
                _log.debug("benign tk race: %s", str(exc_val)[:120])
                return
            _log_crash(exc_type, exc_val, exc_tb, context="tkinter.callback")
            if show_dialog:
                _show_crash_dialog(exc_type, exc_val, tb_text)
        # Patch app instance
        try:
            import types
            app.report_callback_exception = types.MethodType(_hook_tk, app)
        except Exception as e:
            _log.warning("Patch report_callback_exception fail: %s", e)

    # 4. Optional Sentry
    _init_sentry()

    _log.info("Crash handlers installed (sentry=%s, dialog=%s)",
                _SENTRY_INITED, show_dialog)
