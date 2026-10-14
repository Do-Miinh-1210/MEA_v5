"""V5 image selection/storage helpers using the shared field contract."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from tkinter import filedialog, messagebox

from config import IMAGES_DIR
from services.image_fields import normalize_image_field, serialize_image_field


def copy_to_images_dir(src: Path, parent=None) -> str | None:
    """Copy one imported image into app storage and return its new path."""
    if not src.is_file():
        return None
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    ext = src.suffix.lower() or ".png"
    destination = IMAGES_DIR / f"img_{uuid.uuid4().hex[:12]}{ext}"
    try:
        shutil.copy2(str(src), str(destination))
    except Exception as exc:
        messagebox.showerror("Lỗi thêm ảnh", str(exc), parent=parent)
        return None
    return str(destination)


def pick_and_copy_images(parent=None) -> list[str]:
    """Select one or more image files and persist copies for V5."""
    selected = filedialog.askopenfilenames(
        parent=parent,
        title="Chọn ảnh",
        filetypes=[
            ("Ảnh", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
            ("Tất cả tệp", "*.*"),
        ],
    )
    copied: list[str] = []
    for filename in selected:
        path = copy_to_images_dir(Path(filename), parent=parent)
        if path:
            copied.append(path)
    return copied
