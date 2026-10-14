"""
tests/test_tikz_thumbnail.py — Test services/tikz_thumbnail.py.

Lưu ý: KHÔNG test render thật (cần pdflatex installed) — dùng monkeypatch
để mô phỏng render fail/success.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def tmp_thumb_cache(monkeypatch, tmp_path):
    """Redirect thumbnail cache vào tmp_path."""
    from services import tikz_thumbnail as tt
    fake_dir = tmp_path / "thumbs"
    fake_dir.mkdir()
    monkeypatch.setattr(tt, "_cache_dir", lambda: fake_dir)
    return fake_dir


# ══════════════════════════════════════════════════════════════════════════
# HASH STABILITY
# ══════════════════════════════════════════════════════════════════════════

def test_hash_stable():
    """Cùng code → cùng hash, kể cả whitespace khác."""
    from services import tikz_thumbnail as tt
    h1 = tt._hash("\\begin{tikzpicture}\n\\draw (0,0)--(1,1);\n\\end{tikzpicture}")
    h2 = tt._hash("  \\begin{tikzpicture}\n\\draw (0,0)--(1,1);\n\\end{tikzpicture}\n\n")
    assert h1 == h2


def test_hash_differs_on_content_change():
    from services import tikz_thumbnail as tt
    h1 = tt._hash("\\begin{tikzpicture}\\draw (0,0)--(1,1);\\end{tikzpicture}")
    h2 = tt._hash("\\begin{tikzpicture}\\draw (0,0)--(2,2);\\end{tikzpicture}")
    assert h1 != h2


# ══════════════════════════════════════════════════════════════════════════
# CACHE (no render)
# ══════════════════════════════════════════════════════════════════════════

def test_get_returns_none_when_render_disabled(tmp_thumb_cache):
    from services import tikz_thumbnail as tt
    code = "\\begin{tikzpicture}\\draw (0,0)--(1,1);\\end{tikzpicture}"
    # Cache rỗng + render_if_missing=False → None
    assert tt.get(code, render_if_missing=False) is None


def test_get_returns_path_when_cached(tmp_thumb_cache):
    """Pre-place file vào cache → get() phải trả path đó."""
    from services import tikz_thumbnail as tt
    code = "\\begin{tikzpicture}\\draw (0,0)--(1,1);\\end{tikzpicture}"
    dst = tt._cache_path(code)
    # Tạo file giả 1 byte
    dst.write_bytes(b"\x89PNG\r\n\x1a\n")  # PNG magic header
    result = tt.get(code, render_if_missing=False)
    assert result == str(dst)


def test_has_thumb(tmp_thumb_cache):
    from services import tikz_thumbnail as tt
    code = "\\begin{tikzpicture}\\end{tikzpicture}"
    assert not tt.has_thumb(code)
    tt._cache_path(code).write_bytes(b"\x89PNG")
    assert tt.has_thumb(code)


def test_get_empty_code():
    from services import tikz_thumbnail as tt
    assert tt.get("") is None
    assert tt.get("   ") is None


# ══════════════════════════════════════════════════════════════════════════
# FROM PNG
# ══════════════════════════════════════════════════════════════════════════

def test_get_from_png_nonexistent(tmp_thumb_cache):
    from services import tikz_thumbnail as tt
    assert tt.get_from_png("/nonexistent/path/file.png") is None


def test_get_from_png_real_file(tmp_thumb_cache, tmp_path):
    """PNG thật → tạo thumbnail OK."""
    from services import tikz_thumbnail as tt
    try:
        from PIL import Image as PILImage
    except ImportError:
        pytest.skip("Pillow not installed")
    # Tạo PNG 200×200
    src = tmp_path / "src.png"
    PILImage.new("RGB", (200, 200), "red").save(src)
    result = tt.get_from_png(src, code_hint="\\begin{tikzpicture}test\\end{tikzpicture}")
    assert result is not None
    # File thumbnail tồn tại
    from pathlib import Path
    assert Path(result).exists()
    # Size = THUMB_SIZE
    img = PILImage.open(result)
    assert img.size == tt.THUMB_SIZE


# ══════════════════════════════════════════════════════════════════════════
# RESIZE LOGIC
# ══════════════════════════════════════════════════════════════════════════

def test_resize_keeps_aspect_ratio():
    from services.tikz_thumbnail import _resize_to_thumb
    try:
        from PIL import Image as PILImage
    except ImportError:
        pytest.skip("Pillow not installed")
    # Wide image 400×100 → thumb 160×160 với letterbox
    src = PILImage.new("RGB", (400, 100), "blue")
    out = _resize_to_thumb(src, size=(160, 160))
    assert out.size == (160, 160)


def test_resize_small_image_padded():
    """Ảnh nhỏ hơn THUMB_SIZE → giữ nguyên size + pad trắng."""
    from services.tikz_thumbnail import _resize_to_thumb
    try:
        from PIL import Image as PILImage
    except ImportError:
        pytest.skip("Pillow not installed")
    src = PILImage.new("RGB", (50, 50), "green")
    out = _resize_to_thumb(src, size=(160, 160))
    assert out.size == (160, 160)


# ══════════════════════════════════════════════════════════════════════════
# STATS / CLEAR
# ══════════════════════════════════════════════════════════════════════════

def test_stats_empty(tmp_thumb_cache):
    from services import tikz_thumbnail as tt
    s = tt.stats()
    assert s["count"] == 0
    assert s["bytes"] == 0


def test_stats_with_files(tmp_thumb_cache):
    from services import tikz_thumbnail as tt
    (tt._cache_dir() / "a.png").write_bytes(b"\x89PNGabc")
    (tt._cache_dir() / "b.png").write_bytes(b"\x89PNGxyz")
    s = tt.stats()
    assert s["count"] == 2
    assert s["bytes"] > 0


def test_clear(tmp_thumb_cache):
    from services import tikz_thumbnail as tt
    (tt._cache_dir() / "a.png").write_bytes(b"\x89PNG")
    (tt._cache_dir() / "b.png").write_bytes(b"\x89PNG")
    n = tt.clear()
    assert n == 2
    assert tt.stats()["count"] == 0
