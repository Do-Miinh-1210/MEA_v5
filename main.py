"""
main.py — Entry point duy nhất của ứng dụng MatrixExam AI.

Chạy:
    pythonw main.py      ← Khuyến nghị (không hiện terminal/CMD)
    python  main.py      ← Debug mode
"""

import sys
import os

# PyInstaller EXE: __file__ nằm trong temp folder, dùng sys._MEIPASS
if getattr(sys, "frozen", False):
    _APP_DIR = sys._MEIPASS
    # Fix SSL certificates cho httpx/requests trong EXE
    _cacert = os.path.join(_APP_DIR, "certifi", "cacert.pem")
    if os.path.exists(_cacert):
        os.environ["SSL_CERT_FILE"] = _cacert
        os.environ["REQUESTS_CA_BUNDLE"] = _cacert
        # Monkey-patch certifi.where() vì httpx gọi trực tiếp
        try:
            import certifi
            certifi.where = lambda: _cacert
        except ImportError:
            pass
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

try:
    from config import APP_VERSION as _APP_VERSION
except Exception:
    _APP_VERSION = "5.0.0"


def _run_selftest() -> int:
    """Headless health check for frozen EXE/release automation.

    Keep this path UI-free and network-free: it is used by tools/upgrade_app.py
    before replacing release artifacts.
    """
    try:
        import importlib

        for module_name in (
            "config",
            "core.models",
            "services.updater",
            "services.update_safety",
            "services.local_backup",
            "storage.database",
            "export.word_exporter",
        ):
            importlib.import_module(module_name)

        from storage.database import db_init
        db_init()

        from services import updater
        assert updater.is_newer("4.2.3", "4.2.2")
        info = updater._normalize_info(
            {
                "version": "4.2.3",
                "download_url": "https://example.test/MEA_v4_Setup.exe",
            },
            source="selftest",
        )
        assert info and info["version"] == "4.2.3"
        return 0
    except Exception as exc:
        try:
            print(f"SELFTEST_FAIL: {exc}", file=sys.stderr)
        except Exception:
            pass
        return 1


# ══════════════════════════════════════════════════════════════════════════════
#  CRASH HANDLER — ghi lỗi chưa handle vào app.log + hiện dialog cho user
# ══════════════════════════════════════════════════════════════════════════════

def _install_crash_handler() -> None:
    """Cài sys.excepthook + threading.excepthook.

    Tất cả exception chưa được handle sẽ:
      1. Được ghi đầy đủ traceback vào ~/.exam_generator/app.log.
      2. Hiển thị dialog thân thiện cho user (nếu Tk có thể init).
      3. KHÔNG swallow KeyboardInterrupt — giữ Ctrl-C hoạt động bình thường.
    """
    import logging
    import threading
    import traceback

    # Đảm bảo logging đã config (services.logger auto-config khi import)
    try:
        from services import logger as _svc_logger  # noqa: F401
    except Exception:
        # Fallback: basicConfig tối thiểu để crash handler còn chạy được
        from pathlib import Path as _Path
        _fallback_log = _Path.home() / ".exam_generator" / "app.log"
        _fallback_log.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler(str(_fallback_log), encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )

    _crash_log = logging.getLogger("crash")

    def _excepthook(exc_type, exc_value, exc_tb):
        # Không chặn Ctrl-C / SystemExit
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        _crash_log.critical("Unhandled exception:\n%s", tb_str)
        # Cố gắng show messagebox — nếu Tk chưa init hoặc đã tắt, skip
        try:
            import tkinter.messagebox as _mb
            _mb.showerror(
                "Lỗi nghiêm trọng",
                f"Đã xảy ra lỗi không mong muốn:\n\n"
                f"{exc_type.__name__}: {exc_value}\n\n"
                f"Chi tiết đã được ghi vào:\n"
                f"~/.exam_generator/app.log\n\n"
                "Vui lòng gửi file log cho nhà phát triển nếu lỗi lặp lại."
            )
        except Exception:
            # Tk chưa khởi tạo / đã đóng — ít nhất in ra stderr
            sys.__excepthook__(exc_type, exc_value, exc_tb)

    def _thread_excepthook(args):
        # threading.ExceptHookArgs: exc_type, exc_value, exc_traceback, thread
        if args.exc_type is SystemExit:
            return
        tb_str = "".join(traceback.format_exception(
            args.exc_type, args.exc_value, args.exc_traceback))
        _crash_log.error(
            "Unhandled exception in thread %r:\n%s",
            getattr(args.thread, "name", "?"),
            tb_str,
        )

    sys.excepthook = _excepthook
    # threading.excepthook có từ Python 3.8+
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_excepthook


# Install ngay khi module được import — trước khi bất kỳ UI nào khởi động
_install_crash_handler()


# ══════════════════════════════════════════════════════════════════════════════
#  HIGH-DPI FIX (phải gọi TRƯỚC khi import tkinter)
# ══════════════════════════════════════════════════════════════════════════════

def _fix_high_dpi() -> None:
    """Khắc phục UI mờ trên màn hình 2K/4K. Gọi trước mọi thứ."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)   # Per-Monitor v2
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()    # Fallback
        except Exception:
            pass

    # Set AppUserModelID để Windows nhóm taskbar đúng và hiển thị icon riêng
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "DoMinhMath.MatrixExamAI.Desktop.1")
    except Exception:
        pass


def _get_dpi_scale() -> float:
    """Hệ số DPI thực tế để cấu hình tkinter scaling."""
    try:
        if sys.platform == "win32":
            import ctypes
            hdc = ctypes.windll.user32.GetDC(0)
            dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
            ctypes.windll.user32.ReleaseDC(0, hdc)
            return dpi / 72.0
    except Exception:
        pass
    return 1.0


# ══════════════════════════════════════════════════════════════════════════════
#  SPLASH SCREEN
# ══════════════════════════════════════════════════════════════════════════════

def _show_splash(root) -> object:
    """
    Hiển thị splash screen 1/2 màn hình trong lúc app đang tải.
    - Kéo di chuyển được
    - Thanh tiến trình có % cụ thể
    - Nút chạy nền (thu nhỏ)
    """
    import tkinter as tk
    from tkinter import ttk

    BG = "#0F2D52"

    splash = tk.Toplevel(root)
    splash.overrideredirect(True)
    splash.configure(bg=BG)
    splash.attributes("-topmost", True)
    splash.attributes("-alpha", 0.97)

    # 1/2 màn hình, căn giữa
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    w = sw // 2
    h = sh // 2
    x = (sw - w) // 2
    y = (sh - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")

    # ── Kéo di chuyển splash ──
    splash._drag_data = {"x": 0, "y": 0}

    def _on_drag_start(e):
        splash._drag_data["x"] = e.x
        splash._drag_data["y"] = e.y

    def _on_drag_motion(e):
        dx = e.x - splash._drag_data["x"]
        dy = e.y - splash._drag_data["y"]
        nx = splash.winfo_x() + dx
        ny = splash.winfo_y() + dy
        splash.geometry(f"+{nx}+{ny}")

    splash.bind("<Button-1>", _on_drag_start)
    splash.bind("<B1-Motion>", _on_drag_motion)

    # ── Accent bar trên ──
    tk.Frame(splash, bg="#10B981", height=4).pack(fill="x")

    # ── Nút đóng + chạy nền (góc phải trên) ──
    top_bar = tk.Frame(splash, bg=BG)
    top_bar.pack(fill="x")

    def _minimize():
        splash.withdraw()
        # Hiện nút trong system tray (đơn giản: hiện lại khi splash tự đóng)
        splash._minimized = True

    btn_minimize = tk.Label(top_bar, text="▬", bg=BG, fg="#94A3B8",
                             font=("Segoe UI", 10), cursor="hand2", padx=8)
    btn_minimize.pack(side="right", padx=(0, 4), pady=2)
    btn_minimize.bind("<Button-1>", lambda e: _minimize())

    # Tooltip cho nút
    splash._minimized = False

    # ── Body center ──
    body = tk.Frame(splash, bg=BG)
    body.pack(fill="both", expand=True)

    body.grid_rowconfigure(0, weight=3)
    body.grid_rowconfigure(8, weight=4)
    body.grid_columnconfigure(0, weight=1)

    # Logo
    logo_loaded = False
    try:
        from PIL import Image, ImageTk
        from pathlib import Path
        for name in ("logo_1.png", "logo_main.png", "icon4.png"):
            lp = Path(_APP_DIR) / "assets" / name
            if lp.exists():
                img = Image.open(lp).convert("RGBA")
                logo_size = min(320, h * 45 // 100)
                img = img.resize((logo_size, logo_size), Image.LANCZOS)
                splash._ph = ImageTk.PhotoImage(img)
                tk.Label(body, image=splash._ph,
                         bg=BG).grid(row=1, column=0, pady=(0, 8))
                logo_loaded = True
                break
    except Exception:
        pass

    if not logo_loaded:
        tk.Label(body, text="π",
                 bg=BG, fg="#10B981",
                 font=("Segoe UI", 64, "bold")).grid(row=1, column=0, pady=(0, 8))

    # Tên app
    tk.Label(body,
             text="MatrixExamAI — Đỗ Minh Math",
             bg=BG, fg="white",
             font=("Segoe UI", 28, "bold")).grid(row=2, column=0, pady=(0, 2))

    # Tagline
    tk.Label(body,
             text="Hệ thống tạo đề kiểm tra THCS/THPT bằng AI",
             bg=BG, fg="#38BDF8",
             font=("Segoe UI", 13)).grid(row=3, column=0, pady=(0, 16))

    # ── Progress bar có % ──
    pb_frame = tk.Frame(body, bg=BG)
    pb_frame.grid(row=4, column=0, sticky="ew", padx=w // 4, pady=(0, 4))

    style = ttk.Style(splash)
    style.configure("Splash.Horizontal.TProgressbar",
                     troughcolor="#1A3A5C", background="#10B981", thickness=8)
    pb = ttk.Progressbar(pb_frame, mode="determinate", maximum=100,
                          style="Splash.Horizontal.TProgressbar")
    pb.pack(fill="x")
    pb["value"] = 0
    splash._pb = pb

    # % label
    splash._pct_var = tk.StringVar(value="0%")
    tk.Label(body, textvariable=splash._pct_var,
             bg=BG, fg="#94A3B8",
             font=("Segoe UI", 9)).grid(row=5, column=0, pady=(0, 2))

    # Status text
    splash._status_var = tk.StringVar(value="Đang khởi động...")
    tk.Label(body,
             textvariable=splash._status_var,
             bg=BG, fg="#6EE7B7",
             font=("Segoe UI", 11)).grid(row=6, column=0, pady=(2, 0))

    # Helper: cập nhật progress
    def _set_progress(pct: int, text: str = ""):
        """Cập nhật thanh tiến trình (0-100) và status text."""
        try:
            pb["value"] = pct
            splash._pct_var.set(f"{pct}%")
            if text:
                splash._status_var.set(text)
            splash.update_idletasks()
        except Exception:
            pass

    splash.set_progress = _set_progress

    # Footer
    footer = tk.Frame(splash, bg=BG)
    footer.pack(side="bottom", fill="x")
    tk.Frame(footer, bg="#10B981", height=4).pack(fill="x", side="bottom")
    tk.Label(footer,
             text=f"v{_APP_VERSION}  •  © 2026 Đỗ Minh Math",
             bg=BG, fg="#64748B",
             font=("Segoe UI", 9)).pack(pady=8)

    splash.update()
    return splash


# ══════════════════════════════════════════════════════════════════════════════
#  FIRST-RUN SETUP
# ══════════════════════════════════════════════════════════════════════════════

def _show_first_run_setup(parent) -> None:
    """Hiển thị dialog chọn vị trí lưu NHCH lần đầu chạy app.
    Dialog hiện ĐÈ LÊN splash — topmost, không transient.
    """
    import tkinter as tk
    from tkinter import filedialog, messagebox
    from pathlib import Path
    from config import APP_DIR, save_app_settings, load_app_settings

    default_dir = str(APP_DIR / "nhch")

    dlg = tk.Toplevel(parent)
    dlg.title("Cấu hình lần đầu — MatrixExamAI")
    # KHÔNG transient(parent) — parent đang withdraw → dialog sẽ bị ẩn
    dlg.attributes("-topmost", True)
    dlg.grab_set()
    dlg.resizable(False, False)
    dlg.configure(bg="#F8FAFC")

    # Xử lý đóng cửa sổ (X) — vẫn tạo settings mặc định
    def _on_close():
        settings = load_app_settings()
        settings["nhch_dir"] = default_dir
        settings["open_after_export"] = True
        save_app_settings(settings)
        try:
            Path(default_dir).mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        dlg.destroy()

    dlg.protocol("WM_DELETE_WINDOW", _on_close)

    # Center — rộng hơn cho dễ nhìn
    dw, dh = 640, 480
    sw = dlg.winfo_screenwidth()
    sh = dlg.winfo_screenheight()
    dlg.geometry(f"{dw}x{dh}+{(sw-dw)//2}+{(sh-dh)//2}")

    # ── Header ──
    hdr = tk.Frame(dlg, bg="#0F2D52")
    hdr.pack(fill="x")
    tk.Label(hdr, text="  Chào mừng bạn đến với MatrixExamAI!",
             font=("Segoe UI", 15, "bold"), bg="#0F2D52", fg="white"
             ).pack(pady=14, anchor="w", padx=16)

    tk.Frame(dlg, bg="#10B981", height=3).pack(fill="x")

    # ── Body ──
    body = tk.Frame(dlg, bg="#F8FAFC")
    body.pack(fill="both", expand=True, padx=24, pady=(14, 0))

    # Vị trí NHCH
    tk.Label(body, text="Thư mục lưu trữ Ngân hàng câu hỏi (NHCH):",
             font=("Segoe UI", 10, "bold"), bg="#F8FAFC", fg="#334155"
             ).pack(anchor="w", pady=(0, 6))

    path_var = tk.StringVar(value=default_dir)
    row = tk.Frame(body, bg="#F8FAFC")
    row.pack(fill="x", pady=(0, 10))
    ent = tk.Entry(row, textvariable=path_var, font=("Consolas", 9))
    ent.pack(side="left", fill="x", expand=True)

    def _browse():
        dlg.attributes("-topmost", False)
        d = filedialog.askdirectory(title="Chọn thư mục lưu NHCH",
                                     initialdir=path_var.get())
        dlg.attributes("-topmost", True)
        if d:
            path_var.set(d)

    tk.Button(row, text="📂 Duyệt...", command=_browse,
              bg="#3B82F6", fg="white", font=("Segoe UI", 9, "bold"),
              relief="flat", cursor="hand2", padx=8
              ).pack(side="left", padx=(8, 0))

    # ── Separator ──
    tk.Frame(body, bg="#E2E8F0", height=1).pack(fill="x", pady=(4, 8))

    # ── Tùy chọn ──
    tk.Label(body, text="Tùy chọn cài đặt:",
             font=("Segoe UI", 10, "bold"), bg="#F8FAFC", fg="#334155"
             ).pack(anchor="w", pady=(0, 6))

    opts_frame = tk.Frame(body, bg="#F8FAFC")
    opts_frame.pack(fill="x")

    desktop_var = tk.BooleanVar(value=True)
    tk.Checkbutton(opts_frame, text="Tạo biểu tượng trên Màn hình chính (Desktop)",
                    variable=desktop_var, bg="#F8FAFC",
                    font=("Segoe UI", 10), anchor="w"
                    ).pack(fill="x", pady=2)

    auto_var = tk.BooleanVar(value=False)
    tk.Checkbutton(opts_frame, text="Khởi động MatrixExamAI cùng Windows",
                    variable=auto_var, bg="#F8FAFC",
                    font=("Segoe UI", 10), anchor="w"
                    ).pack(fill="x", pady=2)

    open_after_var = tk.BooleanVar(value=True)
    tk.Checkbutton(opts_frame, text="Hỏi mở file Word sau khi xuất",
                    variable=open_after_var, bg="#F8FAFC",
                    font=("Segoe UI", 10), anchor="w"
                    ).pack(fill="x", pady=2)

    tk.Label(body, text="Bạn có thể thay đổi các cài đặt này sau trong Tab Cài đặt",
             font=("Segoe UI", 8, "italic"), bg="#F8FAFC", fg="#94A3B8"
             ).pack(anchor="w", pady=(8, 0))

    # ── Nút xác nhận (nổi bật, luôn nhìn thấy) ──
    btn_frame = tk.Frame(dlg, bg="#F8FAFC")
    btn_frame.pack(fill="x", padx=24, pady=(8, 16))

    def _confirm():
        chosen = path_var.get().strip()
        if not chosen:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn thư mục lưu NHCH.",
                                    parent=dlg)
            return
        try:
            Path(chosen).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo thư mục:\n{e}", parent=dlg)
            return

        settings = load_app_settings()
        settings["nhch_dir"] = chosen
        settings["auto_start"] = auto_var.get()
        settings["open_after_export"] = open_after_var.get()
        save_app_settings(settings)

        _set_auto_start(auto_var.get())

        if desktop_var.get():
            _create_desktop_shortcut()

        dlg.destroy()

    tk.Button(btn_frame, text="  Xác nhận & Tiếp tục  ", command=_confirm,
              bg="#10B981", fg="white", font=("Segoe UI", 12, "bold"),
              relief="flat", cursor="hand2", padx=24, pady=8
              ).pack(expand=True)

    dlg.update()
    dlg.focus_force()
    parent.wait_window(dlg)


def _create_desktop_shortcut() -> None:
    """Tạo shortcut MatrixExamAI trên Desktop."""
    if sys.platform != "win32":
        return
    try:
        import subprocess
        desktop = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")
        if not os.path.isdir(desktop):
            return

        shortcut_path = os.path.join(desktop, "MatrixExamAI.lnk")
        if os.path.exists(shortcut_path):
            return  # Đã có rồi

        if getattr(sys, "frozen", False):
            target = sys.executable
        else:
            target = sys.executable
            arguments = f'"{os.path.abspath(__file__)}"'

        # Dùng PowerShell để tạo .lnk
        icon_path = os.path.join(_APP_DIR, "assets", "app.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(_APP_DIR, "assets", "icon_app.ico")
        ps_script = f'''
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut("{shortcut_path}")
$sc.TargetPath = "{target}"
'''
        if not getattr(sys, "frozen", False):
            ps_script += f'$sc.Arguments = "{os.path.abspath(__file__)}"\n'

        ps_script += f'$sc.WorkingDirectory = "{_APP_DIR}"\n'

        if os.path.exists(icon_path):
            ps_script += f'$sc.IconLocation = "{icon_path}"\n'

        ps_script += '$sc.Save()\n'

        _si = subprocess.STARTUPINFO()
        _si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        _si.wShowWindow = subprocess.SW_HIDE
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, timeout=10,
            startupinfo=_si,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception as e:
        print(f"[CẢNH BÁO] Không thể tạo shortcut desktop: {e}")


def _set_auto_start(enable: bool) -> None:
    """Đăng ký / hủy MatrixExamAI khởi động cùng Windows (Registry)."""
    if sys.platform != "win32":
        return
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE,
        )
        if enable:
            # Tìm exe path — dùng pythonw.exe để ẩn CMD khi khởi động cùng Windows
            if getattr(sys, "frozen", False):
                exe_path = f'"{sys.executable}"'
            else:
                # Thay python.exe → pythonw.exe để không hiện cửa sổ CMD
                py = sys.executable
                pythonw = py.replace("python.exe", "pythonw.exe")
                if os.path.exists(pythonw):
                    exe_path = f'"{pythonw}" "{os.path.abspath(__file__)}"'
                else:
                    exe_path = f'"{py}" "{os.path.abspath(__file__)}"'
            winreg.SetValueEx(key, "MatrixExamAI", 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, "MatrixExamAI")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"[CẢNH BÁO] Không thể cập nhật auto-start: {e}")


def _is_auto_start_enabled() -> bool:
    """Kiểm tra MatrixExamAI có trong startup registry không."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_READ,
        )
        try:
            winreg.QueryValueEx(key, "MatrixExamAI")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    if "--selftest" in sys.argv:
        sys.exit(_run_selftest())

    # 1. Fix DPI TRƯỚC KHI import UI
    _fix_high_dpi()

    # 2. Kiểm tra Python version
    if sys.version_info < (3, 9):
        print("❌ Yêu cầu Python 3.9 trở lên.")
        sys.exit(1)

    # 3. Import tkinter
    try:
        import tkinter as tk
        from tkinter import ttk
    except ImportError:
        print("❌ Không tìm thấy tkinter.\n  Linux: sudo apt install python3-tk")
        sys.exit(1)

    os.environ.setdefault("GDK_SCALE", "1")
    os.environ.setdefault("GDK_DPI_SCALE", "1")

    # 4. Hiển thị Splash screen ngay lập tức
    _root_pre = tk.Tk()
    _root_pre.withdraw()
    try:
        _root_pre.tk.call("tk", "scaling", _get_dpi_scale())
    except Exception:
        pass

    # Set icon cho cửa sổ + taskbar
    try:
        from pathlib import Path as _P
        # app.ico = logo chính trên taskbar
        for _ico_name in ("app.ico", "icon_app.ico"):
            _ico = _P(_APP_DIR) / "assets" / _ico_name
            if _ico.exists():
                _root_pre.iconbitmap(default=str(_ico))
                break
        # wm_iconphoto cho taskbar — dùng app.png
        from PIL import Image as _Img, ImageTk as _ITk
        for _icon_name in ("app.png", "icon4.png"):
            _icon_p = _P(_APP_DIR) / "assets" / _icon_name
            if _icon_p.exists():
                _im = _Img.open(_icon_p).convert("RGBA")
                _icons = []
                for sz in (256, 64, 48, 32, 16):
                    _icons.append(_ITk.PhotoImage(_im.resize((sz, sz), _Img.LANCZOS)))
                _root_pre._taskbar_icons = _icons
                _root_pre.wm_iconphoto(True, *_icons)
                break
    except Exception:
        pass

    splash = _show_splash(_root_pre)
    splash.set_progress(5, "Đang khởi động...")
    _root_pre.update()

    # 4b. PRELOAD: import heavy modules ở background trong lúc hiện splash
    import threading

    _preload_done = threading.Event()
    def _preload_modules():
        """Import các module nặng trước để MainWindow khởi tạo nhanh hơn."""
        try:
            import json, sqlite3, hashlib, pathlib  # noqa: F401
            from core.models import MatrixData, MatrixRow, ExamData, Question  # noqa: F401
            from services.cache_service import CacheService  # noqa: F401
            from storage.database import db_init
            db_init()  # Init DB schema sẵn
        except Exception:
            pass
        finally:
            _preload_done.set()
    threading.Thread(target=_preload_modules, daemon=True).start()

    # 5a. First-run: hỏi vị trí lưu NHCH
    try:
        from config import is_first_run
        if is_first_run():
            splash.set_progress(10, "Cấu hình lần đầu...")
            # Ẩn splash hoàn toàn — dialog first-run sẽ hiện trên cùng
            splash.withdraw()
            _show_first_run_setup(_root_pre)
            # Hiện lại splash sau khi user xác nhận
            splash.deiconify()
            splash.attributes("-topmost", True)
            splash.set_progress(20, "Đã cấu hình xong!")
    except Exception as e:
        print(f"[CẢNH BÁO] Lỗi first-run setup: {e}")
        # Nếu lỗi → đảm bảo splash vẫn hiện
        try:
            splash.deiconify()
        except Exception:
            pass

    # 5. Kiểm tra license
    splash.set_progress(30, "Đang kiểm tra giấy phép...")
    license_ok     = False
    license_result = {}
    try:
        import threading
        from services.license_manager import check_license, _clear_cache
        _clear_cache()

        _lr_result = {}
        _lr_error  = [None]

        def _check_thread():
            try:
                _lr_result.update(check_license(force_online=True))
            except Exception as exc:
                _lr_error[0] = exc

        t = threading.Thread(target=_check_thread, daemon=True)
        t.start()

        # Chờ tối đa 8s, cập nhật progress mỗi 0.5s
        for tick in range(16):
            t.join(timeout=0.5)
            if not t.is_alive():
                break
            pct = 30 + min(tick * 3, 40)  # 30% → 70%
            splash.set_progress(pct, f"Đang kiểm tra giấy phép... ({(tick+1)/2:.0f}s)")

        splash.set_progress(75, "Xử lý kết quả...")

        if t.is_alive():
            print("[THÔNG BÁO] Kiểm tra giấy phép quá 8s — tự động kích hoạt bản mở khóa độc lập")
            from config import get_default_features
            license_result = {
                "ok": True, "status": "active", "tier": "premium",
                "name": "Bản mở khóa cục bộ",
                "message": "Đang dùng chế độ mở khóa toàn bộ tính năng.",
                "offline": True,
                "features": get_default_features("premium"),
            }
            license_ok = True
        elif _lr_error[0]:
            print(f"[THÔNG BÁO] Database/Mạng: {_lr_error[0]} — tự động kích hoạt bản mở khóa độc lập")
            from config import get_default_features
            license_result = {
                "ok": True, "status": "active", "tier": "premium",
                "name": "Bản mở khóa cục bộ",
                "message": "Đang dùng chế độ mở khóa toàn bộ tính năng.",
                "offline": True,
                "features": get_default_features("premium"),
            }
            license_ok = True
        else:
            license_result = _lr_result or {}
            license_result["tier"] = "premium"
            license_result["ok"] = True
            from config import get_default_features
            license_result["features"] = get_default_features("premium")
            license_ok = True

    except Exception as e:
        print(f"[THÔNG BÁO] Chuyển sang bản mở khóa độc lập: {e}")
        license_ok = True
        from config import get_default_features
        license_result = {
            "ok": True, "status": "active", "tier": "premium",
            "name": "Bản mở khóa cục bộ",
            "features": get_default_features("premium"),
            "offline": True,
        }

    splash.set_progress(90, "Đang tải giao diện...")

    # 6. Đóng splash
    try:
        splash.set_progress(100, "Hoàn tất!")
        splash.update_idletasks()
        splash.after(100)  # Hiện 100% trong 0.1s
        splash.update()
        splash.destroy()
    except Exception:
        pass

    # 7. Nếu chưa kích hoạt → hiện dialog activation
    if not license_ok:
        try:
            _root_pre.tk.call("tk", "scaling", _get_dpi_scale())
        except Exception:
            pass

        try:
            from ui.activation_dialog import ActivationDialog
            dlg = ActivationDialog(_root_pre, license_result=license_result)
            _root_pre.wait_window(dlg)
            activated = getattr(dlg, "activated", False)
        except Exception as e:
            print(f"[LỖI] Không mở được dialog kích hoạt: {e}")
            activated = False
        finally:
            try:
                _root_pre.destroy()
            except Exception:
                pass

        if not activated:
            sys.exit(0)
    else:
        try:
            _root_pre.destroy()
        except Exception:
            pass

    # 8. Chờ preload hoàn tất (thường đã xong từ lúc license check)
    _preload_done.wait(timeout=5)

    # 8b. Kiểm tra cập nhật GitHub (async — không block khởi động)
    _update_info_holder = [None]  # dùng list để closure có thể ghi
    _update_app_holder = [None]
    _update_dialog_shown = [False]

    def _show_update_dialog():
        app_ref = _update_app_holder[0]
        info = _update_info_holder[0]
        if not app_ref or not info or _update_dialog_shown[0]:
            return
        _update_dialog_shown[0] = True
        try:
            from ui.dialog_update import UpdateDialog
            from config import AUTO_UPDATE_INSTALL_AFTER_DOWNLOAD
            UpdateDialog(
                app_ref,
                info,
                current_version=_APP_VERSION,
                auto_start=True,
                auto_install=AUTO_UPDATE_INSTALL_AFTER_DOWNLOAD,
            )
        except Exception as e:
            print(f"[CẢNH BÁO] Lỗi hiển thị dialog cập nhật: {e}")

    def _on_update_check(result):
        _update_info_holder[0] = result
        app_ref = _update_app_holder[0]
        if result and app_ref:
            app_ref.after(0, _show_update_dialog)

    try:
        from config import AUTO_UPDATE_ON_STARTUP
        from services.updater import check_for_update_async, cleanup_old_downloads
        if AUTO_UPDATE_ON_STARTUP:
            cleanup_old_downloads()
            check_for_update_async(callback=_on_update_check)
    except Exception as e:
        print(f"[CẢNH BÁO] Lỗi kiểm tra cập nhật: {e}")

    # 9. Khởi động MainWindow (truyền license_result để gating features)
    try:
        from ui.main_window import MainWindow
        app = MainWindow(license_result=license_result)
        _update_app_holder[0] = app
        try:
            app.tk.call("tk", "scaling", _get_dpi_scale())
        except Exception:
            pass

        # 9b. Nếu update check đã trả kết quả trước khi UI sẵn sàng, mở dialog.
        app.after(800, _show_update_dialog)

        app.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            import tkinter.messagebox as mb
            mb.showerror("Lỗi khởi động",
                         f"Không thể khởi động ứng dụng:\n{e}\n\n"
                         "Xem terminal để biết thêm chi tiết.")
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
