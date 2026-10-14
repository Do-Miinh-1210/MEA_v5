"""ctypes bridge for small CPU-heavy text primitives implemented in C++.

MEA remains fully functional without the DLL. Packaged V5 builds include the
native backend, while source checkouts can use the Python fallback until
``python build_native.py`` has been run.
"""
from __future__ import annotations

import ctypes
import os
import re
import sys
from pathlib import Path


_ABI_VERSION = 1
_EXACT_BLOCK_RE = re.compile(
    r"===\s*CAU\s*===(.*?)===\s*KETCAU\s*===",
    re.DOTALL | re.IGNORECASE,
)


def _dll_candidates() -> list[Path]:
    paths: list[Path] = []
    override = os.environ.get("MEA_NATIVE_DLL", "").strip()
    if override:
        paths.append(Path(override))
    bundle_root = getattr(sys, "_MEIPASS", "")
    if bundle_root:
        paths.append(Path(bundle_root) / "native" / "mea_native.dll")
    paths.append(Path(__file__).resolve().parents[1] / "native" / "bin" / "mea_native.dll")
    return paths


def _load_library():
    for path in _dll_candidates():
        if not path.exists():
            continue
        try:
            lib = ctypes.CDLL(str(path))
            lib.mea_native_abi_version.argtypes = []
            lib.mea_native_abi_version.restype = ctypes.c_uint32
            if lib.mea_native_abi_version() != _ABI_VERSION:
                continue
            size_t_pointer = ctypes.POINTER(ctypes.c_size_t)
            lib.mea_find_exact_blocks_utf8.argtypes = [
                ctypes.c_char_p, ctypes.c_size_t,
                size_t_pointer, size_t_pointer, ctypes.c_size_t,
            ]
            lib.mea_find_exact_blocks_utf8.restype = ctypes.c_size_t
            lib.mea_collapse_blank_lines_utf8.argtypes = [
                ctypes.c_char_p, ctypes.c_size_t,
                ctypes.c_void_p, ctypes.c_size_t,
            ]
            lib.mea_collapse_blank_lines_utf8.restype = ctypes.c_size_t
            return lib, path
        except (AttributeError, OSError):
            continue
    return None, None


_LIB, _LIB_PATH = _load_library()


def is_available() -> bool:
    return _LIB is not None


def backend_name() -> str:
    return f"C++ DLL ABI {_ABI_VERSION}" if is_available() else "Python fallback"


def require_native() -> str:
    if not is_available():
        raise RuntimeError(
            "Thiếu native/bin/mea_native.dll; chạy python build_native.py trước khi đóng gói."
        )
    return backend_name()


def _python_find_exact_blocks(text: str) -> list[str]:
    return _EXACT_BLOCK_RE.findall(text or "")


def find_exact_blocks(text: str) -> list[str]:
    """Extract structured ``===CAU===...===KETCAU===`` payloads."""
    if not text:
        return []
    if _LIB is None:
        return _python_find_exact_blocks(text)

    encoded = text.encode("utf-8")
    count = _LIB.mea_find_exact_blocks_utf8(encoded, len(encoded), None, None, 0)
    if not count:
        return []
    starts = (ctypes.c_size_t * count)()
    ends = (ctypes.c_size_t * count)()
    actual = _LIB.mea_find_exact_blocks_utf8(
        encoded, len(encoded), starts, ends, count)
    return [encoded[starts[i]:ends[i]].decode("utf-8") for i in range(actual)]


def _python_collapse_blank_lines(text: str) -> str:
    lines = (text or "").split("\n")
    squashed: list[str] = []
    previous_blank = False
    for line in lines:
        blank = not line.strip()
        if blank and previous_blank:
            continue
        squashed.append(line)
        previous_blank = blank
    return "\n".join(squashed).strip()


def collapse_blank_lines(text: str) -> str:
    """Collapse repeated blank lines with a native fast path."""
    if not text:
        return text
    if _LIB is None:
        return _python_collapse_blank_lines(text)

    encoded = text.encode("utf-8")
    out_len = _LIB.mea_collapse_blank_lines_utf8(encoded, len(encoded), None, 0)
    if not out_len:
        return ""
    output = ctypes.create_string_buffer(out_len)
    actual = _LIB.mea_collapse_blank_lines_utf8(
        encoded, len(encoded), output, out_len)
    return output.raw[:actual].decode("utf-8")

