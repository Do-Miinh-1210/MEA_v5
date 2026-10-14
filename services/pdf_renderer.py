"""
services/pdf_renderer.py — Render PDF page → PIL.Image at any zoom level.

Mục đích: thay vì render TikZ/LaTeX → PNG cố định 300 DPI rồi resize khi zoom
(mất chất lượng vì raster scaling), giữ PDF gốc và RE-RENDER tại đúng DPI tương
ứng với zoom hiện tại. Hiệu quả như viewer PDF native (Acrobat/Edge).

Sử dụng:
    >>> from services.pdf_renderer import PDFRenderer
    >>> r = PDFRenderer("path/to/file.pdf")
    >>> img = r.render(page=0, dpi=150)  # PIL Image, sắc nét tại 150 DPI
    >>> img2 = r.render(page=0, dpi=600) # Re-render at 600 DPI for zoom-in
    >>> r.close()                        # giải phóng PDF handle

Hoặc one-shot:
    >>> from services.pdf_renderer import render_pdf_page
    >>> img = render_pdf_page("file.pdf", page=0, dpi=300)

Tích hợp với LaTeX:
    >>> from services.pdf_renderer import compile_latex_to_pdf
    >>> pdf_path = compile_latex_to_pdf(latex_source, workdir=tmpdir)

Yêu cầu: pymupdf (đã có trong requirements.txt).
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# Import PyMuPDF lazily — nếu thiếu thì raise ở call-time với message rõ.
_FITZ = None


def _get_fitz():
    """Lazy import fitz (PyMuPDF)."""
    global _FITZ
    if _FITZ is None:
        try:
            import fitz  # type: ignore
            _FITZ = fitz
        except ImportError as exc:
            raise ImportError(
                "PyMuPDF (fitz) chưa được cài. Chạy: pip install pymupdf"
            ) from exc
    return _FITZ


class PDFRenderer:
    """Wrapper PyMuPDF — giữ PDF mở, render từng trang at any DPI on demand.

    LƯU Ý: phải gọi `.close()` sau khi dùng để release file handle (Windows
    sẽ lock file đến khi handle đóng → không xóa được).
    """

    def __init__(self, pdf_path: str):
        fitz = _get_fitz()
        self._pdf_path = pdf_path
        self._doc = fitz.open(pdf_path)

    @property
    def page_count(self) -> int:
        return self._doc.page_count

    @property
    def path(self) -> str:
        return self._pdf_path

    def render(self, page: int = 0, dpi: int = 150):
        """Render `page` thành PIL.Image tại DPI chỉ định.

        DPI cao hơn = ảnh nét hơn (tốn RAM hơn). Khuyến nghị:
          - Default view: 150 DPI
          - Zoom 2x: 300 DPI
          - Zoom 4x: 600 DPI (đủ cho hầu hết màn hình 4K)
          - Cap: 1200 DPI (vượt là phí RAM)
        """
        from PIL import Image
        if page < 0 or page >= self._doc.page_count:
            raise IndexError(
                f"Page {page} ngoài phạm vi PDF (có {self._doc.page_count} trang)"
            )
        # PyMuPDF: matrix scale = dpi/72 (1 point = 1/72 inch)
        zoom = dpi / 72.0
        fitz = _get_fitz()
        mat = fitz.Matrix(zoom, zoom)
        page_obj = self._doc[page]
        pix = page_obj.get_pixmap(matrix=mat, alpha=False)
        # Convert pixmap → PIL Image
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return img

    def page_size_pt(self, page: int = 0) -> tuple[float, float]:
        """Kích thước page tại 72 DPI (point). Dùng để tính fit-to-window."""
        rect = self._doc[page].rect
        return rect.width, rect.height

    def close(self) -> None:
        """Release PDF file handle. Bắt buộc gọi khi không cần nữa."""
        try:
            self._doc.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def render_pdf_page(pdf_path: str, page: int = 0, dpi: int = 150):
    """One-shot render: mở PDF → render 1 page → close.

    Tiện cho use case không zoom (chỉ xem 1 lần).
    """
    with PDFRenderer(pdf_path) as r:
        return r.render(page=page, dpi=dpi)


# ── LaTeX compilation helper ────────────────────────────────────────────────

# Template LaTeX cho câu hỏi đơn (math + tiếng Việt). Tách riêng để tab_qc
# có thể compile câu hỏi → PDF để review.
_QUESTION_LATEX_TEMPLATE = r"""\documentclass[12pt,border=10pt]{standalone}
\usepackage{iftex}
\ifPDFTeX
  \usepackage[utf8]{inputenc}
  \usepackage[T5]{fontenc}
\fi
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usetikzlibrary{calc,angles,quotes,patterns,arrows.meta,intersections}
\usepackage{varwidth}
\begin{document}
\begin{varwidth}{15cm}
%(content)s
\end{varwidth}
\end{document}
"""


def compile_latex_to_pdf(
    latex_source: str,
    workdir: Optional[str] = None,
    timeout: int = 30,
) -> str:
    """Compile LaTeX source → PDF, trả về absolute path tới file PDF.

    Args:
        latex_source: full document LaTeX (đã có \\documentclass + \\begin{document}).
                      Hoặc chỉ content body — sẽ wrap qua _QUESTION_LATEX_TEMPLATE.
        workdir: thư mục làm việc. None = tạo tmp dir (caller tự cleanup).
        timeout: giây timeout cho pdflatex.

    Returns:
        Absolute path tới `figure.pdf` trong workdir.

    Raises:
        RuntimeError nếu compile fail (kèm log).
    """
    from services import latex_engine

    # Auto-wrap nếu source là body content (không có \documentclass)
    if r"\documentclass" not in latex_source:
        latex_source = _QUESTION_LATEX_TEMPLATE % {"content": latex_source}

    if workdir is None:
        workdir = tempfile.mkdtemp(prefix="latex_pdf_")

    workdir_path = Path(workdir)
    workdir_path.mkdir(parents=True, exist_ok=True)

    tex_path = workdir_path / "figure.tex"
    pdf_path = workdir_path / "figure.pdf"
    tex_path.write_text(latex_source, encoding="utf-8")

    try:
        engine = latex_engine.get_engine()
    except latex_engine.LatexEngineNotFound as exc:
        raise RuntimeError(str(exc)) from exc

    # Hide CMD window on Windows
    si = None
    cflags = 0
    if os.name == "nt":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        cflags = subprocess.CREATE_NO_WINDOW

    result = subprocess.run(
        engine.build_argv("figure.tex"),
        cwd=str(workdir_path),
        capture_output=True, text=True, timeout=timeout,
        startupinfo=si, creationflags=cflags,
    )

    if not pdf_path.exists():
        # Compile failed — extract last meaningful error
        log = (result.stdout or "") + (result.stderr or "")
        # Lấy 2000 ký tự cuối log để dễ debug
        log_tail = log[-2000:] if len(log) > 2000 else log
        raise RuntimeError(
            f"LaTeX compile thất bại (engine={engine.name}).\n"
            f"--- LOG ---\n{log_tail}"
        )

    return str(pdf_path)
