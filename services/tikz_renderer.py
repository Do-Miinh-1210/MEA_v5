"""Render TikZ through LaTeX without depending on a desktop UI module."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from config import PDFLATEX_TIMEOUT
from services import latex_engine


_LATEX_TEMPLATE = r"""\documentclass[border=10pt,tikz,preview]{{standalone}}
\usepackage{{iftex}}
\ifPDFTeX
  \usepackage[utf8]{{inputenc}}
  \usepackage[T5]{{fontenc}}
\fi
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{preview}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\usepackage{{tkz-tab}}
\usepackage{{tikz-3dplot}}
\usepackage{{array,booktabs,cellspace}}
\usepackage{{bm}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{calc,angles,quotes,patterns,patterns.meta,arrows,arrows.meta,decorations.markings,decorations.pathmorphing,decorations.pathreplacing,decorations.text,intersections,3d,shapes,shapes.geometric,positioning,fit,backgrounds,shadings,through,math,perspective}}
\PreviewEnvironment{{tikzpicture}}
\PreviewEnvironment{{tabular}}
\pagestyle{{empty}}
\begin{{document}}
{tikz_code}
\end{{document}}
"""


def _subprocess_window_options() -> dict:
    """Hide compiler windows on Windows desktops."""
    if os.name != "nt":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "startupinfo": startupinfo,
        "creationflags": subprocess.CREATE_NO_WINDOW,
    }


def _compile_pdf(tikz_code: str, tmpdir: str) -> tuple[str, str]:
    try:
        engine = latex_engine.get_engine()
    except latex_engine.LatexEngineNotFound as exc:
        raise RuntimeError(str(exc)) from exc

    from services.tikz_preflight import auto_fix
    sanitized_code = auto_fix(tikz_code)

    tex_path = os.path.join(tmpdir, "figure.tex")
    pdf_path = os.path.join(tmpdir, "figure.pdf")
    Path(tex_path).write_text(
        _LATEX_TEMPLATE.format(tikz_code=sanitized_code),
        encoding="utf-8",
    )
    result = subprocess.run(
        engine.build_argv("figure.tex"),
        cwd=tmpdir,
        capture_output=True,
        text=True,
        timeout=PDFLATEX_TIMEOUT,
        **_subprocess_window_options(),
    )
    log_text = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
    log_file = Path(tmpdir) / "figure.log"
    if log_file.exists():
        try:
            log_text += "\n" + log_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if not Path(pdf_path).exists():
        error_lines = [line for line in log_text.splitlines() if line.startswith("!")]
        detail = "\n".join(error_lines[:15]) if error_lines else "\n".join(log_text.splitlines()[-30:])
        if not detail:
            detail = "Không có log - LaTeX engine có thể chưa cài hoặc bị chặn."
        raise RuntimeError(f"{engine.name} thất bại:\n{detail[:2000]}")
    return pdf_path, log_text


def render_tikz_to_image(tikz_code: str, dpi: int = 300, return_log: bool = False):
    """Render TikZ to a PIL image and optionally retain its source PDF."""
    from PIL import Image

    with latex_engine.safe_temporary_directory(prefix="tikz_") as tmpdir:
        pdf_path, log_text = _compile_pdf(tikz_code, tmpdir)
        persistent_pdf = ""
        if return_log:
            persistent_pdf = os.path.join(
                tempfile.gettempdir(),
                f"MatrixExamAI_tikz_preview_{os.getpid()}_{uuid.uuid4().hex[:8]}.pdf",
            )
            try:
                shutil.copy2(pdf_path, persistent_pdf)
            except OSError:
                persistent_pdf = ""

        try:
            import fitz

            document = fitz.open(pdf_path)
            try:
                page = document[0]
                pixmap = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False)
                image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
                return (image, log_text, persistent_pdf) if return_log else image
            finally:
                document.close()
        except ImportError:
            pass

        pdftoppm = shutil.which("pdftoppm")
        if pdftoppm:
            png_prefix = os.path.join(tmpdir, "out")
            subprocess.run(
                [pdftoppm, "-r", str(dpi), "-png", pdf_path, png_prefix],
                capture_output=True,
                timeout=15,
                **_subprocess_window_options(),
            )
            for candidate in (f"{png_prefix}-1.png", f"{png_prefix}-01.png"):
                if Path(candidate).exists():
                    image = Image.open(candidate).copy()
                    return (image, log_text, persistent_pdf) if return_log else image
        raise RuntimeError("Không thể chuyển PDF sang PNG. Cần cài PyMuPDF hoặc pdftoppm.")


def render_tikz_to_svg(tikz_code: str) -> str:
    """Render TikZ to SVG, preferring PyMuPDF and falling back to dvisvgm."""
    with latex_engine.safe_temporary_directory(prefix="tikz_svg_") as tmpdir:
        pdf_path, _log = _compile_pdf(tikz_code, tmpdir)
        try:
            import fitz

            document = fitz.open(pdf_path)
            try:
                svg_text = document[0].get_svg_image()
                if isinstance(svg_text, bytes):
                    svg_text = svg_text.decode("utf-8", errors="replace")
                if svg_text and "<svg" in svg_text.lower():
                    return svg_text
            finally:
                document.close()
        except Exception:
            pass

        dvisvgm = shutil.which("dvisvgm")
        if not dvisvgm:
            raise RuntimeError("Không tạo được SVG. Cần cài PyMuPDF hoặc dvisvgm.")
        svg_path = os.path.join(tmpdir, "figure.svg")
        last_log = ""
        for command in (
            [dvisvgm, "--pdf", "-o", svg_path, pdf_path],
            [dvisvgm, "--pdf", "--bbox=min", "-o", svg_path, pdf_path],
            [dvisvgm, "--pdf", "--no-fonts", "-o", svg_path, pdf_path],
        ):
            result = subprocess.run(
                command,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=60,
                **_subprocess_window_options(),
            )
            if Path(svg_path).exists():
                return Path(svg_path).read_text(encoding="utf-8")
            last_log = ((result.stderr or "") + "\n" + (result.stdout or "")).strip()
        raise RuntimeError(f"dvisvgm không tạo được SVG.\n{last_log[-1500:]}")
