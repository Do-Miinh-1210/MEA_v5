"""
ui/image_helper.py — Tiện ích chèn/hiển thị ảnh cho câu hỏi trong tkinter.
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

from config import IMAGES_DIR

# Kích thước preview tối đa trong tkinter (pixels)
_PREVIEW_MAX_W = 360
_PREVIEW_MAX_H = 240


def _copy_to_images_dir(src: Path, parent=None) -> Optional[str]:
    """Copy 1 file ảnh nguồn → IMAGES_DIR với tên unique. Trả path mới."""
    if not src.is_file():
        return None
    ext = src.suffix.lower() or ".png"
    dst = IMAGES_DIR / f"img_{uuid.uuid4().hex[:12]}{ext}"
    try:
        shutil.copy2(str(src), str(dst))
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể copy ảnh:\n{e}", parent=parent)
        return None
    return str(dst)


def pick_and_copy_image(parent=None) -> Optional[str]:
    """Mở file dialog chọn 1 ảnh, copy vào IMAGES_DIR, trả về đường dẫn mới.

    Returns None nếu hủy hoặc lỗi.
    """
    path = filedialog.askopenfilename(
        parent=parent,
        title="Chọn hình ảnh",
        filetypes=[
            ("Hình ảnh", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("Tất cả", "*.*"),
        ],
    )
    if not path:
        return None
    return _copy_to_images_dir(Path(path), parent=parent)


def pick_and_copy_images(parent=None) -> list[str]:
    """Mở file dialog cho phép CHỌN NHIỀU ảnh cùng lúc (Ctrl/Shift + click).

    Mỗi ảnh được copy vào IMAGES_DIR với tên unique. Trả list path mới.
    Returns [] nếu user hủy.

    Dùng cho UI có thể chèn N ảnh cho 1 vùng (vd: câu hỏi nhiều đồ thị).
    """
    paths = filedialog.askopenfilenames(
        parent=parent,
        title="Chọn 1 hoặc nhiều hình ảnh (Ctrl/Shift để chọn nhiều)",
        filetypes=[
            ("Hình ảnh", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
            ("PNG", "*.png"),
            ("JPEG", "*.jpg *.jpeg"),
            ("Tất cả", "*.*"),
        ],
    )
    if not paths:
        return []
    out: list[str] = []
    for p in paths:
        new_path = _copy_to_images_dir(Path(p), parent=parent)
        if new_path:
            out.append(new_path)
    return out


def normalize_image_field(value) -> list[str]:
    """Chuẩn hoá field ảnh cũ/mới về list[str].

    Backward-compat: app cũ lưu `question_image: str` (1 path). App mới hỗ
    trợ list. Hàm này nhận cả 2 dạng:
        ""                  → []
        "path/a.png"         → ["path/a.png"]
        "a.png|b.png"        → ["a.png", "b.png"]    (separator '|')
        ["a.png", "b.png"]   → ["a.png", "b.png"]    (passthrough)
        None / sai kiểu      → []
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if x]
    s = str(value).strip()
    if not s:
        return []
    if "|" in s:
        return [p.strip() for p in s.split("|") if p.strip()]
    return [s]


def serialize_image_field(paths) -> str:
    """Chuyển list[str] → string '|'-separated để lưu vào legacy `str` field.

    Dùng khi cần giữ tương thích với cột DB / Question.question_image: str.
    """
    if not paths:
        return ""
    if isinstance(paths, str):
        return paths
    return "|".join(str(p) for p in paths if p)


def remove_image(image_path: str) -> None:
    """Xóa file ảnh (nếu nằm trong IMAGES_DIR)."""
    if not image_path:
        return
    p = Path(image_path)
    if p.exists() and IMAGES_DIR in p.parents:
        try:
            p.unlink()
        except Exception:
            pass


def load_tk_image(image_path: str, max_w: int = _PREVIEW_MAX_W,
                  max_h: int = _PREVIEW_MAX_H):
    """Load ảnh từ file và trả về tk.PhotoImage (resize nếu cần).

    Cần Pillow (PIL). Trả về None nếu không load được.
    """
    if not image_path:
        return None
    p = Path(image_path)
    if not p.exists():
        return None
    try:
        from PIL import Image, ImageTk
        img = Image.open(str(p))
        # Resize giữ tỉ lệ
        w, h = img.size
        ratio = min(max_w / w, max_h / h, 1.0)
        if ratio < 1.0:
            new_w = int(w * ratio)
            new_h = int(h * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except ImportError:
        return None
    except Exception:
        return None
