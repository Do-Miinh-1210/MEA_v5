"""
services/desktop_shortcut.py — Quản lý và tạo lối tắt Desktop (Màn hình chính) cho MEA v5.

Giúp người dùng không rành công nghệ:
1. Tự động tìm vị trí Desktop chính xác trên Windows (kể cả Desktop thường hoặc Desktop qua OneDrive).
2. Tạo lối tắt .lnk trên Desktop trỏ trực tiếp đến app với icon và thư mục làm việc chuẩn.
3. Kiểm tra xem biểu tượng Desktop đã tồn tại hay chưa.
4. Mở nhanh thư mục cài đặt app trong Windows Explorer.
"""
from __future__ import annotations

import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Tuple, List, Optional

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore


ROOT_DIR = Path(__file__).resolve().parent.parent


def get_desktop_paths() -> List[Path]:
    """Trả về danh sách các thư mục Desktop có thể có của người dùng Windows."""
    paths: List[Path] = []
    seen = set()

    def _add(p: Optional[Path]):
        if p and p.exists() and str(p) not in seen:
            seen.add(str(p))
            paths.append(p)

    # 1. Tra cứu Registry User Shell Folders (Chính xác nhất kể cả khi OneDrive sync Desktop)
    if winreg is not None and sys.platform == "win32":
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            ) as key:
                val, _ = winreg.QueryValueEx(key, "Desktop")
                expanded = os.path.expandvars(str(val))
                _add(Path(expanded))
        except Exception:
            pass

    # 2. Thư mục OneDrive Desktop phổ biến ở Việt Nam
    _add(Path.home() / "OneDrive" / "Desktop")
    _add(Path.home() / "OneDrive - Personal" / "Desktop")

    # 3. Thư mục Desktop chuẩn trong User Profile
    _add(Path.home() / "Desktop")

    # 4. Thư mục Public Desktop (All Users)
    public_env = os.environ.get("PUBLIC", r"C:\Users\Public")
    _add(Path(public_env) / "Desktop")

    return paths


def get_primary_desktop() -> Path:
    """Lấy thư mục Desktop chính đang hiển thị của người dùng."""
    all_desktops = get_desktop_paths()
    if all_desktops:
        return all_desktops[0]
    return Path.home() / "Desktop"


def resolve_app_executable() -> Tuple[Path, Path]:
    """
    Xác định file thực thi và thư mục làm việc hiện tại.
    Trả về: (exe_path, working_dir)
    """
    # Nếu đang chạy từ EXE đóng gói (PyInstaller)
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        return exe, exe.parent

    # Nếu chạy từ source Python / Development
    candidates = [
        ROOT_DIR / "dist" / "MEA_v5_alpha.exe",
        ROOT_DIR / "dist" / "MEA_v5.exe",
        ROOT_DIR / "dist" / "MEA_v4.exe",
    ]
    for c in candidates:
        if c.exists():
            return c, ROOT_DIR

    # Fallback chạy file bat hoặc pythonw/python
    bat_v5 = ROOT_DIR / "Chay MEA_v5.bat"
    if bat_v5.exists():
        return bat_v5, ROOT_DIR

    return Path(sys.executable).resolve(), ROOT_DIR


def resolve_app_icon(working_dir: Optional[Path] = None) -> Optional[Path]:
    """Tìm file icon (.ico) của ứng dụng."""
    dirs_to_check = []
    if working_dir:
        dirs_to_check.append(working_dir)
    dirs_to_check.extend([ROOT_DIR, ROOT_DIR / "dist"])

    for d in dirs_to_check:
        for icon_name in ("app.ico", "icon3.ico", "assets/app.ico", "assets/icon3.ico"):
            p = d / icon_name
            if p.exists():
                return p.resolve()
    return None


def has_desktop_shortcut(shortcut_name: str = "MEA_v5") -> bool:
    """Kiểm tra xem shortcut trên Màn hình chính đã có chưa."""
    for d in get_desktop_paths():
        lnk = d / f"{shortcut_name}.lnk"
        if lnk.exists():
            return True
    return False


def create_desktop_shortcut(
    shortcut_name: str = "MEA_v5",
    exe_path: Optional[Path] = None,
    work_dir: Optional[Path] = None,
    icon_path: Optional[Path] = None,
    description: str = "MEA v5 — Biên soạn tài liệu và đề thi Toán thông minh bằng AI",
) -> Tuple[bool, str]:
    """
    Tạo lối tắt (.lnk) trên Màn hình chính (Desktop) của Windows.
    Trả về (thành_công: bool, thông_báo: str).
    """
    if sys.platform != "win32":
        return False, "Tính năng tạo lối tắt Desktop chỉ hỗ trợ trên hệ điều hành Windows."

    # Xác định exe và work dir
    resolved_exe, resolved_work = resolve_app_executable()
    target_exe = exe_path or resolved_exe
    target_work = work_dir or resolved_work
    target_icon = icon_path or resolve_app_icon(target_work)

    if not target_exe.exists():
        return False, f"Không tìm thấy file chương trình: {target_exe}"

    desktop_dir = get_primary_desktop()
    desktop_dir.mkdir(parents=True, exist_ok=True)
    shortcut_path = desktop_dir / f"{shortcut_name}.lnk"

    shortcut_path_str = str(shortcut_path).replace("'", "''")
    target_exe_str = str(target_exe).replace("'", "''")
    target_work_str = str(target_work).replace("'", "''")
    desc_str = description.replace("'", "''")

    icon_line = ""
    if target_icon and target_icon.exists():
        icon_str = str(target_icon).replace("'", "''")
        icon_line = f"$s.IconLocation = '{icon_str},0'"

    ps_content = f"""# MEA Shortcut Creator
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('{shortcut_path_str}')
$s.TargetPath = '{target_exe_str}'
$s.WorkingDirectory = '{target_work_str}'
$s.Description = '{desc_str}'
{icon_line}
$s.Save()
"""

    ps_file = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8-sig") as f:
            f.write(ps_content)
            ps_file = Path(f.name)

        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )

        if res.returncode == 0 and shortcut_path.exists():
            return True, f"Đã thêm lối tắt thành công vào Màn hình chính:\n{shortcut_path}"
        else:
            err = res.stderr.strip() or res.stdout.strip() or f"Mã thoát {res.returncode}"
            return False, f"Không thể tạo lối tắt: {err}"
    except Exception as exc:
        return False, f"Lỗi trong quá trình tạo lối tắt: {exc}"
    finally:
        if ps_file and ps_file.exists():
            try:
                ps_file.unlink()
            except Exception:
                pass


def open_install_directory() -> bool:
    """Mở thư mục cài đặt của MEA trong Windows Explorer."""
    _, work_dir = resolve_app_executable()
    target = work_dir if work_dir.exists() else ROOT_DIR
    try:
        if sys.platform == "win32":
            os.startfile(str(target))  # type: ignore[attr-defined]
            return True
        else:
            subprocess.Popen(["xdg-open", str(target)])
            return True
    except Exception:
        return False
