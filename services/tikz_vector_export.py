"""Export standalone TikZ PDF files to EMF vectors through Inkscape."""
from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

from services.tikz_renderer import _subprocess_window_options


_WINDOWS_INKSCAPE_PATHS = (
    Path(r"C:\Program Files\Inkscape\bin\inkscape.exe"),
    Path(r"C:\Program Files\Inkscape\inkscape.exe"),
    Path(r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe"),
)


def find_inkscape(explicit_path: str | os.PathLike[str] | None = None) -> Path:
    """Locate the Inkscape CLI used for PDF -> EMF conversion."""
    candidates: list[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path))
    if os.getenv("INKSCAPE_PATH"):
        candidates.append(Path(os.environ["INKSCAPE_PATH"]))
    discovered = shutil.which("inkscape")
    if discovered:
        candidates.append(Path(discovered))
    if os.name == "nt":
        candidates.extend(_WINDOWS_INKSCAPE_PATHS)

    for candidate in candidates:
        if candidate.expanduser().is_file():
            return candidate.expanduser().resolve()
    raise RuntimeError(
        "Chua tim thay Inkscape. Hay cai Inkscape hoac dat bien INKSCAPE_PATH "
        "tro den inkscape.exe."
    )


def convert_pdf_to_emf(
    pdf_path: str | os.PathLike[str],
    output_path: str | os.PathLike[str] | None = None,
    *,
    text_to_path: bool = True,
    inkscape_path: str | os.PathLike[str] | None = None,
    timeout: int = 120,
) -> Path:
    """Convert a standalone PDF to EMF while preserving vector geometry."""
    source = Path(pdf_path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Khong tim thay PDF TikZ: {source}")

    if output_path is None:
        out_dir = Path(tempfile.gettempdir()) / "MatrixExamAI_tikz_emf"
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / f"{source.stem}.emf"
    else:
        target = Path(output_path).expanduser().resolve()
        if target.suffix.lower() != ".emf":
            target = target.with_suffix(".emf")
        target.parent.mkdir(parents=True, exist_ok=True)

    executable = find_inkscape(inkscape_path)
    argv = [
        str(executable),
        str(source),
        "--export-type=emf",
        f"--export-filename={target}",
        "--export-overwrite",
    ]
    if text_to_path:
        argv.append("--export-text-to-path")

    result = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout,
        **_subprocess_window_options(),
    )
    if result.returncode != 0 or not target.is_file() or target.stat().st_size <= 0:
        details = ((result.stderr or "") + "\n" + (result.stdout or "")).strip()
        raise RuntimeError(
            "Inkscape khong tao duoc EMF."
            + (f"\n{details[-1500:]}" if details else "")
        )
    return target


def export_tikz_to_emf(
    tikz_code: str,
    output_path: str | os.PathLike[str] | None = None,
    *,
    text_to_path: bool = True,
    inkscape_path: str | os.PathLike[str] | None = None,
) -> Path:
    from services.latex_engine import safe_temporary_directory
    from services.tikz_renderer import _compile_pdf

    with safe_temporary_directory(prefix="tikz_emf_") as tmpdir:
        pdf_path, _log = _compile_pdf(tikz_code, tmpdir)
        return convert_pdf_to_emf(
            pdf_path,
            output_path,
            text_to_path=text_to_path,
            inkscape_path=inkscape_path,
        )


def copy_emf_to_clipboard(emf_path: str | os.PathLike[str]) -> Path:
    """Copy an EMF as CF_ENHMETAFILE so Word pastes a real vector image."""
    path = Path(emf_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Khong tim thay EMF: {path}")
    if os.name != "nt":
        raise RuntimeError("Copy EMF truc tiep chi duoc ho tro tren Windows.")

    from ctypes import wintypes

    cf_enhmetafile = 14
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32.GetEnhMetaFileW.argtypes = [wintypes.LPCWSTR]
    gdi32.GetEnhMetaFileW.restype = wintypes.HANDLE
    gdi32.DeleteEnhMetaFile.argtypes = [wintypes.HANDLE]
    gdi32.DeleteEnhMetaFile.restype = wintypes.BOOL
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.restype = wintypes.BOOL

    handle: Optional[int] = gdi32.GetEnhMetaFileW(str(path))
    if not handle:
        raise OSError(ctypes.get_last_error(), "Khong doc duoc EMF.")

    opened = False
    try:
        for _attempt in range(6):
            if user32.OpenClipboard(None):
                opened = True
                break
            time.sleep(0.08)
        if not opened:
            raise OSError(ctypes.get_last_error(), "Clipboard dang duoc ung dung khac su dung.")
        if not user32.EmptyClipboard():
            raise OSError(ctypes.get_last_error(), "Khong the xoa clipboard.")
        if not user32.SetClipboardData(cf_enhmetafile, handle):
            raise OSError(ctypes.get_last_error(), "Khong the copy EMF vao clipboard.")
        handle = None  # Clipboard owns the handle after SetClipboardData succeeds.
    finally:
        if opened:
            user32.CloseClipboard()
        if handle:
            gdi32.DeleteEnhMetaFile(handle)
    return path
