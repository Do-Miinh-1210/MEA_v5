"""
services/auto_export.py — Auto-export Word sau khi gen.

Logic core của [SPEED-1] trong ROADMAP: sau khi AI gen xong, app tự
1) Lưu file Word vào ~/Documents/MEA Exam/MEA_exam_{timestamp}.docx
2) Mở file (os.startfile)
3) UI hiển thị toast cho phép user override (đổi vị trí, lưu thêm bản…)

Bỏ qua hoàn toàn dialog "lưu vào đâu" cũ — user có thể nhấn 1 nút trong
toast nếu muốn quay về flow chọn thủ công.

Mặc định BẬT. User có thể tắt qua tab Cài đặt → "Tự động xuất Word sau
khi tạo đề".
"""

from __future__ import annotations
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

_log = logging.getLogger(__name__)


# ── Sanitize filename (Windows + macOS safe) ────────────────────────────────

_INVALID_FN_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe_filename(text: str, max_len: int = 60) -> str:
    """Strip ký tự invalid khỏi tên file, giới hạn độ dài.

    Giữ tiếng Việt có dấu (Windows hỗ trợ).
    """
    if not text:
        return ""
    cleaned = _INVALID_FN_CHARS.sub("", text)
    # Strip leading/trailing space + dot (Windows không cho)
    cleaned = cleaned.strip(" .")
    # Cắt độ dài
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip(" .")
    return cleaned


def build_default_filename(exam_data) -> str:
    """Tên file mặc định: 'MEA_{Mon}{Lop}_{HHmm}.docx'.

    Ví dụ:
        MEA_Toan12_1530.docx
        MEA_LiK10_0845.docx
    """
    subj  = _safe_filename(getattr(exam_data, "subject", "") or "", 20)
    grade = _safe_filename(getattr(exam_data, "grade", "") or "", 5)
    # Loại khoảng trắng để compact
    subj_clean  = re.sub(r"\s+", "", subj)
    grade_clean = re.sub(r"\s+", "", grade)

    parts = ["MEA"]
    if subj_clean or grade_clean:
        parts.append(f"{subj_clean}{grade_clean}")
    parts.append(datetime.now().strftime("%Y%m%d_%H%M"))
    return "_".join(parts) + ".docx"


def _resolve_auto_convert_tables(auto_convert_tables: Optional[bool]) -> bool:
    if auto_convert_tables is not None:
        return bool(auto_convert_tables)
    try:
        from config import is_word_auto_convert_tables_enabled
        return is_word_auto_convert_tables_enabled()
    except Exception:
        return True


# ── Core auto-export ────────────────────────────────────────────────────────

def auto_export_exam(
    exam_data,
    target_dir: Optional[Path] = None,
    include_solution: bool = True,
    open_after: bool = True,
    auto_convert_tables: Optional[bool] = None,
) -> tuple[Optional[Path], Optional[str]]:
    """Xuất exam_data → Word file rồi tự mở.

    Parameters
    ----------
    exam_data:        ExamData
    target_dir:       Path thư mục lưu. Default = get_auto_export_dir() (Documents/MEA Exam).
    include_solution: Có kèm lời giải không (mặc định True).
    open_after:       Có `os.startfile()` sau khi lưu không.

    Returns
    -------
    (path, error):
        path: Path tới file đã lưu, hoặc None nếu lỗi.
        error: chuỗi lỗi human-readable, None nếu thành công.
    """
    try:
        from export.word_exporter import export_to_word
    except Exception as e:
        return None, f"Không import được word_exporter: {e}"

    if target_dir is None:
        try:
            from config import get_auto_export_dir
            target_dir = get_auto_export_dir()
        except Exception:
            target_dir = Path.home() / "Documents"

    try:
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return None, f"Không tạo được thư mục {target_dir}: {e}"

    filename = build_default_filename(exam_data)
    save_path = target_dir / filename

    # Tránh ghi đè: nếu file đã tồn tại (gen 2 lần trong cùng phút) → thêm _v2, _v3…
    # Giữ nguyên timestamp trong tên file gốc, chỉ append "_vN" trước ".docx".
    original_stem = save_path.stem
    counter = 2
    while save_path.exists():
        save_path = target_dir / f"{original_stem}_v{counter}.docx"
        counter += 1
        if counter > 100:
            return None, "Quá nhiều file trùng tên — vui lòng đổi thư mục"

    try:
        # Lấy school + teacher từ exam_data nếu có
        school  = getattr(exam_data, "school", "") or ""
        teacher = getattr(exam_data, "teacher", "") or ""
        export_to_word(
            exam_data, str(save_path),
            include_solution=include_solution,
            school_name=school, teacher_name=teacher,
            auto_convert_tables=_resolve_auto_convert_tables(auto_convert_tables),
        )
    except Exception as e:
        _log.exception("auto-export failed")
        return None, f"Lỗi xuất Word: {e}"

    # Mở file
    if open_after:
        try:
            if os.name == "nt":
                os.startfile(str(save_path))
            elif os.name == "posix":
                import subprocess
                subprocess.Popen(["xdg-open", str(save_path)])
        except Exception as e:
            _log.warning("Không tự mở được file: %s", e)
            # Không fail — file vẫn được lưu OK

    return save_path, None


# ── Helper: lưu thêm bản với tên user chọn ──────────────────────────────────

def save_extra_copy(
    exam_data,
    initial_dir: Optional[Path] = None,
    initial_filename: Optional[str] = None,
    include_solution: bool = True,
    auto_convert_tables: Optional[bool] = None,
) -> tuple[Optional[Path], Optional[str]]:
    """Mở filedialog cho user chọn nơi lưu thêm bản. Trả (path, error)."""
    try:
        from tkinter import filedialog
        from export.word_exporter import export_to_word
    except Exception as e:
        return None, f"Lỗi import: {e}"

    if initial_dir is None:
        try:
            from config import get_auto_export_dir
            initial_dir = get_auto_export_dir()
        except Exception:
            initial_dir = Path.home() / "Documents"

    if initial_filename is None:
        initial_filename = build_default_filename(exam_data)

    path_str = filedialog.asksaveasfilename(
        title="Lưu thêm bản — chọn nơi & tên file",
        defaultextension=".docx",
        initialdir=str(initial_dir),
        initialfile=initial_filename,
        filetypes=[("Word Document", "*.docx")],
    )
    if not path_str:
        return None, None  # User cancelled — không phải lỗi

    save_path = Path(path_str)
    try:
        school  = getattr(exam_data, "school", "") or ""
        teacher = getattr(exam_data, "teacher", "") or ""
        export_to_word(
            exam_data, str(save_path),
            include_solution=include_solution,
            school_name=school, teacher_name=teacher,
            auto_convert_tables=_resolve_auto_convert_tables(auto_convert_tables),
        )
        return save_path, None
    except Exception as e:
        _log.exception("save_extra_copy failed")
        return None, f"Lỗi xuất Word: {e}"
