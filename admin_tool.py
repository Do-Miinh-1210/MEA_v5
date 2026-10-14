"""
admin_tool.py — Launcher quản trị License ExamAI.
Chạy: python admin_tool.py

Logic đã được tách ra admin/ package:
  admin/app.py          — Orchestrator chính
  admin/panel_users.py  — Quản lý người dùng
  admin/panel_system.py — Kiểm soát hệ thống
  admin/panel_stats.py  — Thống kê tổng quan
  admin/panel_logs.py   — Log hoạt động
  admin/panel_exports.py— Xuất dữ liệu
  admin/dialog_settings.py — Thiết lập tính năng & bảng giá
  admin/dialog_features.py — Ghi đè tính năng cá nhân
  admin/supabase_api.py — Tầng API Supabase
  admin/constants.py    — Hằng số
"""

import sys
from pathlib import Path

# PyInstaller EXE: dùng sys._MEIPASS thay vì __file__
if getattr(sys, "frozen", False):
    _DIR = Path(sys._MEIPASS)
    # Fix SSL certificates cho httpx/requests trong EXE
    import os
    _cacert = _DIR / "certifi" / "cacert.pem"
    if _cacert.exists():
        os.environ["SSL_CERT_FILE"] = str(_cacert)
        os.environ["REQUESTS_CA_BUNDLE"] = str(_cacert)
        # Monkey-patch certifi.where() vì httpx gọi trực tiếp
        try:
            import certifi
            certifi.where = lambda: str(_cacert)
        except ImportError:
            pass
else:
    _DIR = Path(__file__).parent
sys.path.insert(0, str(_DIR))


def _fix_dpi():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "DoMinhMath.ExamAI.Admin.1")
        except Exception:
            pass


if __name__ == "__main__":
    _fix_dpi()
    from admin import launch
    launch()
