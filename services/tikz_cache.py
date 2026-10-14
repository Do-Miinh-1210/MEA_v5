"""
services/tikz_cache.py — Cache PNG đã render từ TikZ, khóa theo SHA1 của code đã chuẩn hoá.

Điểm chốt (fix #2 trong ghi chú thiết kế):
- Chuẩn hoá code TRƯỚC khi hash (strip trailing whitespace, drop dòng trống thừa,
  LF-only). Nhờ vậy AI tạo lại cùng 1 hình dù format đôi khi lệch vẫn hit cache.
- Lưu flat file `cache/tikz_img/<hash>.png` — không cần DB. Filesystem đủ nhanh.
- Thread-safe put: copy tạm + rename atomic để tránh lần render song song ghi dở.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import time
from pathlib import Path

from config import APP_DIR  # type: ignore

_CACHE_DIR = APP_DIR / "cache" / "tikz_img"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Retry config cho WinError 5 (Access is denied) — antivirus/file handle
# race trên Windows khi mkstemp + save + replace.
_RETRY_DELAYS = (0.2, 0.5, 1.0, 2.0)


def _safe_replace(src: str, dst: str) -> None:
    """os.replace với retry — khắc phục WinError 5 (file đang bị scan/khoá).

    Trên Windows, antivirus có thể mở file vừa tạo để scan → os.replace fail.
    Retry vài lần với backoff. Cuối cùng nếu dst đang được mở bởi process khác
    (vd PIL preview), thử copy nội dung + xoá src.
    """
    last_err = None
    for delay in (0,) + _RETRY_DELAYS:
        if delay: time.sleep(delay)
        try:
            os.replace(src, dst)
            return
        except PermissionError as e:
            last_err = e
            continue
    # Cuối cùng: fallback copy + xoá src (dst có thể đang mở, copy ghi đè
    # thường thành công vì Windows cho ghi đè file đang đọc trong nhiều TH)
    try:
        shutil.copyfile(src, dst)
        try: os.unlink(src)
        except Exception: pass
        return
    except Exception:
        pass
    raise last_err if last_err else PermissionError(f"replace fail: {dst}")

# Số lần chuẩn hoá phải đồng nhất ở mọi caller — không được đổi, kẻo toàn bộ
# cache cũ trở thành "stale" (hash thay đổi).
_HASH_LEN = 16


def _normalize(code: str) -> str:
    """Chuẩn hoá code TikZ trước khi hash để stable giữa các lần sinh.

    Chuẩn hoá:
      - LF-only (loại \\r\\n / \\r)
      - Strip toàn khối (bỏ whitespace bao ngoài)
      - Strip trailing whitespace trên từng dòng
      - Bỏ dòng trống thừa đầu/cuối; gộp nhiều dòng trống liên tiếp thành 1
    KHÔNG strip leading whitespace giữa dòng — indent trong \\node{…} vẫn có ý nghĩa.
    """
    if not code:
        return ""
    # LF-only + strip toàn khối
    raw = code.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return ""
    lines = [ln.rstrip() for ln in raw.split("\n")]
    out: list[str] = []
    prev_blank = False
    for ln in lines:
        is_blank = not ln.strip()
        if is_blank and prev_blank:
            continue
        out.append(ln)
        prev_blank = is_blank
    return "\n".join(out).strip()


def hash_of(code: str) -> str:
    """Trả về hash SHA1[:16] của code TikZ đã chuẩn hoá."""
    norm = _normalize(code)
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:_HASH_LEN]


def path_for(code: str) -> Path:
    """Đường dẫn PNG (có thể chưa tồn tại) ứng với code."""
    return _CACHE_DIR / f"{hash_of(code)}.png"


def get(code: str) -> str | None:
    """Trả đường dẫn PNG nếu đã có trong cache, ngược lại None."""
    p = path_for(code)
    return str(p) if p.exists() and p.stat().st_size > 0 else None


def put_from_path(code: str, src_png: str) -> str:
    """Copy file PNG vào cache, trả về đường dẫn cuối cùng."""
    dst = path_for(code)
    src = Path(src_png).resolve()
    if src == dst.resolve() and dst.exists():
        return str(dst)
    # Cache hit: dst đã có + non-empty → trả luôn, tránh ghi lại + WinError 5
    if dst.exists() and dst.stat().st_size > 0:
        return str(dst)
    # Copy atomic qua tempfile để render song song không lẫn
    fd, tmp = tempfile.mkstemp(prefix="tikz_", suffix=".png", dir=str(_CACHE_DIR))
    os.close(fd)
    try:
        shutil.copyfile(str(src), tmp)
        _safe_replace(tmp, str(dst))    # retry WinError 5
    except Exception:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass
        raise
    return str(dst)


def put_pil(code: str, img) -> str:
    """Lưu PIL.Image vào cache, trả về đường dẫn PNG."""
    dst = path_for(code)
    # Cache hit → trả luôn
    if dst.exists() and dst.stat().st_size > 0:
        return str(dst)
    fd, tmp = tempfile.mkstemp(prefix="tikz_", suffix=".png", dir=str(_CACHE_DIR))
    os.close(fd)
    try:
        # Retry save nếu antivirus đang scan file vừa mkstemp
        last_err = None
        for delay in (0,) + _RETRY_DELAYS:
            if delay: time.sleep(delay)
            try:
                img.save(tmp, format="PNG", optimize=True)
                last_err = None; break
            except (PermissionError, OSError) as e:
                last_err = e
                continue
        if last_err: raise last_err
        _safe_replace(tmp, str(dst))    # retry WinError 5
    except Exception:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass
        raise
    return str(dst)


def clear() -> int:
    """Xóa toàn bộ cache. Trả về số file đã xóa."""
    n = 0
    for p in _CACHE_DIR.glob("*.png"):
        try:
            p.unlink()
            n += 1
        except Exception:
            pass
    return n


def stats() -> dict:
    """Trả số file + tổng dung lượng cache."""
    files = list(_CACHE_DIR.glob("*.png"))
    total = sum((p.stat().st_size for p in files), 0)
    return {"count": len(files), "bytes": total, "dir": str(_CACHE_DIR)}
