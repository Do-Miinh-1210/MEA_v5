"""
services/tikz_thumbnail.py — Thumbnail cache cho preview nhỏ.

Khác `services/tikz_cache.py` (full-res render): module này lưu thumbnail
160×160 (mặc định) cho:
  • NHCH hình vẽ (grid view với ảnh nhỏ)
  • Template picker (icon ảnh cạnh tên)

Cache flat: `~/.exam_generator/cache/tikz_thumbs/<hash>.png`

Strategy:
  1. Có sẵn ảnh full-res từ tikz_cache → resize → save → return
  2. Có file PNG riêng (figure_bank PNG) → resize từ đó
  3. Render mới ở DPI thấp (75) → cache cả full + thumb

API:
    >>> from services import tikz_thumbnail as thumb
    >>> path = thumb.get(tikz_code)              # → Path | None (None nếu render fail)
    >>> path = thumb.get_from_png(png_path)      # resize PNG có sẵn
    >>> thumb.preload_async([code1, code2, …])   # background render KB
"""

from __future__ import annotations

import hashlib
import logging
import threading
from pathlib import Path
from typing import Iterable, Optional

_log = logging.getLogger(__name__)

# ── Cache directory ───────────────────────────────────────────────────────

def _cache_dir() -> Path:
    from config import APP_DIR
    d = APP_DIR / "cache" / "tikz_thumbs"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Config ─────────────────────────────────────────────────────────────────

THUMB_SIZE = (160, 160)   # default thumbnail bounding box
LOWRES_DPI = 75           # DPI khi render fresh cho thumbnail
HASH_LEN = 16


def _hash(code: str) -> str:
    """SHA1 of normalized code, prefix 16 chars."""
    from services.tikz_cache import _normalize
    norm = _normalize(code)
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:HASH_LEN]


def _cache_path(code: str) -> Path:
    return _cache_dir() / f"{_hash(code)}.png"


def _resize_to_thumb(pil_image, size=THUMB_SIZE):
    """Resize PIL Image vào bounding box giữ tỉ lệ. Pad trắng nếu nhỏ hơn."""
    from PIL import Image as PILImage
    w, h = pil_image.size
    max_w, max_h = size
    scale = min(max_w / w, max_h / h, 1.0)
    if scale < 1.0:
        pil_image = pil_image.resize(
            (int(w * scale), int(h * scale)),
            resample=PILImage.LANCZOS,
        )
    # Pad sang nền trắng để thumb nào cũng cùng size
    bg = PILImage.new("RGB", size, "white")
    paste_x = (size[0] - pil_image.width) // 2
    paste_y = (size[1] - pil_image.height) // 2
    if pil_image.mode in ("RGBA", "LA"):
        bg.paste(pil_image, (paste_x, paste_y), pil_image.split()[-1])
    else:
        bg.paste(pil_image, (paste_x, paste_y))
    return bg


def _save_thumb(pil_image, dst: Path) -> None:
    """Save PIL Image as PNG (atomic via tempfile)."""
    import os
    import tempfile
    fd, tmp = tempfile.mkstemp(prefix="thumb_", suffix=".png", dir=str(dst.parent))
    os.close(fd)
    try:
        pil_image.save(tmp, format="PNG", optimize=True)
        os.replace(tmp, str(dst))
    except Exception:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass
        raise


# ══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════

def get(code: str, render_if_missing: bool = True) -> Optional[str]:
    """Trả về đường dẫn thumbnail PNG. Render mới nếu cần.

    Args:
        code: TikZ code (raw — sẽ được normalize trước khi hash)
        render_if_missing: nếu False, chỉ trả None khi không có cache

    Returns:
        Đường dẫn PNG, hoặc None nếu render fail.
    """
    if not code or not code.strip():
        return None
    dst = _cache_path(code)
    if dst.exists() and dst.stat().st_size > 0:
        return str(dst)
    if not render_if_missing:
        return None
    return _render_and_cache(code, dst)


def get_from_png(png_path: str | Path, code_hint: str = "") -> Optional[str]:
    """Tạo thumbnail từ PNG có sẵn (vd: figure_bank lưu PNG full-res).
    Cache key dựa vào code_hint nếu có, ngược lại dùng PNG file path."""
    src = Path(png_path)
    if not src.exists():
        return None
    if code_hint:
        dst = _cache_path(code_hint)
    else:
        h = hashlib.sha1(str(src.resolve()).encode("utf-8")).hexdigest()[:HASH_LEN]
        dst = _cache_dir() / f"frompng_{h}.png"
    if dst.exists() and dst.stat().st_size > 0:
        return str(dst)
    try:
        from PIL import Image as PILImage
        img = PILImage.open(src)
        thumb = _resize_to_thumb(img)
        _save_thumb(thumb, dst)
        return str(dst)
    except Exception as e:
        _log.warning("get_from_png failed for %s: %s", src, e)
        return None


def _render_and_cache(code: str, dst: Path) -> Optional[str]:
    """Render TikZ → resize → save thumbnail. Trả None nếu fail."""
    # 1. Thử tikz_cache (full-res) trước — nếu có thì chỉ cần resize
    try:
        from services import tikz_cache
        full_path = tikz_cache.get(code)
        if full_path:
            from PIL import Image as PILImage
            img = PILImage.open(full_path)
            thumb = _resize_to_thumb(img)
            _save_thumb(thumb, dst)
            return str(dst)
    except Exception as e:
        _log.debug("tikz_cache lookup failed: %s", e)

    # 2. Render mới ở DPI thấp
    try:
        # Lazy import service renderer; thumbnail generation is not a UI concern.
        from services.tikz_renderer import render_tikz_to_image
        img = render_tikz_to_image(code, dpi=LOWRES_DPI)
        # Cache cả full ở tikz_cache để lần sau không phải render lại
        try:
            from services import tikz_cache
            tikz_cache.put_pil(code, img)
        except Exception:
            pass
        thumb = _resize_to_thumb(img)
        _save_thumb(thumb, dst)
        return str(dst)
    except Exception as e:
        _log.info("Thumbnail render failed (%s): %s",
                  code[:50].replace("\n", " "), e)
        return None


# ══════════════════════════════════════════════════════════════════════════
# BACKGROUND PRE-RENDER
# ══════════════════════════════════════════════════════════════════════════

def preload_async(
    codes: Iterable[str],
    on_progress: Optional[callable] = None,
    on_done: Optional[callable] = None,
) -> threading.Thread:
    """Render tuần tự danh sách code trong background thread.

    Args:
        codes: list TikZ code cần thumbnail
        on_progress: callback (done: int, total: int, name: str) — gọi mỗi item
        on_done: callback (done: int, failed: int) — gọi khi xong

    Returns: Thread object (đã start)
    """
    codes_list = list(codes)
    total = len(codes_list)

    def _worker():
        done = 0
        failed = 0
        for i, code in enumerate(codes_list, 1):
            try:
                result = get(code, render_if_missing=True)
                if result:
                    done += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
            if on_progress:
                try:
                    on_progress(i, total, code[:40])
                except Exception:
                    pass
        if on_done:
            try:
                on_done(done, failed)
            except Exception:
                pass

    t = threading.Thread(target=_worker, daemon=True, name="ThumbPreload")
    t.start()
    return t


# ══════════════════════════════════════════════════════════════════════════
# MAINTENANCE
# ══════════════════════════════════════════════════════════════════════════

def clear() -> int:
    """Xoá toàn bộ thumbnail cache. Trả về số file đã xoá."""
    n = 0
    for p in _cache_dir().glob("*.png"):
        try:
            p.unlink()
            n += 1
        except Exception:
            pass
    return n


def stats() -> dict:
    """Tổng số file + dung lượng cache."""
    files = list(_cache_dir().glob("*.png"))
    total = sum(p.stat().st_size for p in files)
    return {"count": len(files), "bytes": total, "dir": str(_cache_dir())}


def has_thumb(code: str) -> bool:
    """True nếu thumbnail đã được cache (không trigger render)."""
    p = _cache_path(code)
    return p.exists() and p.stat().st_size > 0
