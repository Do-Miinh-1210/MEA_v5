"""UI-independent helpers for serialized image fields."""
from __future__ import annotations

VECTOR_IMAGE_SEPARATOR = "::emf::"


def serialize_vector_image(png_path: str, emf_path: str = "") -> str:
    """Serialize a preview PNG with an optional EMF vector companion."""
    png = str(png_path or "").strip()
    emf = str(emf_path or "").strip()
    if png and emf:
        return f"{png}{VECTOR_IMAGE_SEPARATOR}{emf}"
    return png or emf


def split_vector_image(value) -> tuple[str, str]:
    """Return (preview_png, vector_emf) for a serialized image field item."""
    raw = str(value or "").strip()
    if VECTOR_IMAGE_SEPARATOR not in raw:
        return raw, ""
    png, emf = raw.split(VECTOR_IMAGE_SEPARATOR, 1)
    return png.strip(), emf.strip()


def normalize_image_field(value, *, prefer_vector: bool = False) -> list[str]:
    """Normalize legacy single/multi-image storage to a path list."""
    if not value:
        return []
    if isinstance(value, list):
        raw_items = [str(path) for path in value if path]
    else:
        raw = str(value).strip()
        if not raw:
            return []
        raw_items = [path.strip() for path in raw.split("|") if path.strip()]
    paths: list[str] = []
    for item in raw_items:
        preview_png, vector_emf = split_vector_image(item)
        if prefer_vector and vector_emf:
            paths.append(vector_emf)
            if preview_png and preview_png != vector_emf:
                paths.append(preview_png)
            continue
        if preview_png:
            paths.append(preview_png)
    return paths


def serialize_image_field(paths) -> str:
    """Serialize image paths using the format accepted by Question storage."""
    if not paths:
        return ""
    if isinstance(paths, str):
        return paths
    return "|".join(str(path) for path in paths if path)
