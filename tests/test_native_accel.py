"""Regression tests for the optional C++ text accelerator."""
from __future__ import annotations

from core.exam_file_loader import _EXACT_BLOCK_RE
from services import native_accel


def test_native_backend_is_built_for_release_checkout():
    assert native_accel.is_available()
    assert native_accel.backend_name() == "C++ DLL ABI 1"


def test_native_exact_scanner_matches_python_regex_for_unicode_and_spacing():
    text = (
        "mở đầu\n"
        "=== CAU ===\nNỘI DUNG: Tính tích phân π\n=== KETCAU ===\n"
        "noise\n"
        "===cau===\nNOIDUNG: Đường tròn\n===ketcau===\n"
    )

    assert native_accel.find_exact_blocks(text) == _EXACT_BLOCK_RE.findall(text)


def test_native_exact_scanner_ignores_unclosed_block():
    text = "===CAU===\nNOIDUNG: thiếu marker đóng"

    assert native_accel.find_exact_blocks(text) == []


def test_native_blank_line_collapse_matches_python_fallback():
    cases = [
        "",
        "  A\n\n \nB\n\n\n  ",
        "\n\nNỘI DUNG\n \t\n\nĐÁP ÁN\n",
        "A\r\n\r\n\r\nB\r\n",
    ]

    for text in cases:
        assert native_accel.collapse_blank_lines(text) == (
            native_accel._python_collapse_blank_lines(text)
        )


def test_python_fallback_remains_functional(monkeypatch):
    monkeypatch.setattr(native_accel, "_LIB", None)
    text = "===CAU===\nNỘI DUNG\n===KETCAU==="

    assert native_accel.backend_name() == "Python fallback"
    assert native_accel.find_exact_blocks(text) == ["\nNỘI DUNG\n"]
    assert native_accel.collapse_blank_lines(" A\n\n\nB ") == "A\n\nB"
