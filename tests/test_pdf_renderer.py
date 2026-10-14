"""
tests/test_pdf_renderer.py — Test cho services/pdf_renderer.py.

Bao gồm:
- compile_latex_to_pdf: compile LaTeX → PDF (yêu cầu pdflatex/xelatex/tectonic)
- PDFRenderer: render trang PDF tại nhiều DPI
- one-shot render_pdf_page

Test compile sẽ skip nếu không có LaTeX engine — không break CI khi máy không
cài MikTeX/TeX Live.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _has_latex_engine() -> bool:
    """True nếu có ít nhất 1 LaTeX engine khả dụng."""
    try:
        from services import latex_engine
        latex_engine.get_engine()
        return True
    except Exception:
        return False


_HAS_LATEX = _has_latex_engine()
_skip_no_latex = pytest.mark.skipif(
    not _HAS_LATEX, reason="Không có pdflatex/xelatex/tectonic trong PATH"
)


# ── Test PDFRenderer / render_pdf_page ─────────────────────────────────────

def test_pdf_renderer_import():
    from services.pdf_renderer import PDFRenderer, render_pdf_page  # noqa: F401


def test_pdf_renderer_requires_pymupdf():
    """fitz (PyMuPDF) là dependency hard. Nếu thiếu, lazy raise."""
    import services.pdf_renderer as mod
    assert callable(mod._get_fitz)


@_skip_no_latex
def test_compile_simple_latex(tmp_path):
    from services.pdf_renderer import compile_latex_to_pdf
    src = r"$E=mc^2$"  # body content → wrap qua template
    pdf = compile_latex_to_pdf(src, workdir=str(tmp_path))
    assert os.path.exists(pdf)
    assert os.path.getsize(pdf) > 1000  # PDF non-trivial size


@_skip_no_latex
def test_compile_full_document(tmp_path):
    """Source đã có \\documentclass thì không wrap lại."""
    from services.pdf_renderer import compile_latex_to_pdf
    src = (
        r"\documentclass[border=10pt]{standalone}"
        + r"\begin{document}Hello $x^2$\end{document}"
    )
    pdf = compile_latex_to_pdf(src, workdir=str(tmp_path))
    assert os.path.exists(pdf)


@_skip_no_latex
def test_compile_invalid_raises():
    """LaTeX sai cú pháp phải raise RuntimeError với log."""
    from services.pdf_renderer import compile_latex_to_pdf
    bad_src = r"\undefined_command{x}"
    tmpdir = tempfile.mkdtemp(prefix="pdftest_bad_")
    try:
        with pytest.raises(RuntimeError) as excinfo:
            compile_latex_to_pdf(bad_src, workdir=tmpdir)
        # Log phải có tail của pdflatex error
        assert "LOG" in str(excinfo.value) or "LaTeX" in str(excinfo.value)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@_skip_no_latex
def test_render_at_multiple_dpi(tmp_path):
    """Render cùng 1 trang ở nhiều DPI → kích thước scale theo DPI (vector)."""
    from services.pdf_renderer import compile_latex_to_pdf, PDFRenderer
    pdf = compile_latex_to_pdf(r"$x^2 + y^2 = z^2$", workdir=str(tmp_path))
    with PDFRenderer(pdf) as r:
        assert r.page_count >= 1
        img150 = r.render(page=0, dpi=150)
        img300 = r.render(page=0, dpi=300)
        # 300 DPI phải có kích thước gấp đôi 150 DPI (±1px tolerance)
        assert abs(img300.width - img150.width * 2) <= 2
        assert abs(img300.height - img150.height * 2) <= 2


@_skip_no_latex
def test_one_shot_render(tmp_path):
    """render_pdf_page: open + render + close trong 1 call."""
    from services.pdf_renderer import compile_latex_to_pdf, render_pdf_page
    pdf = compile_latex_to_pdf(r"Test $\alpha$", workdir=str(tmp_path))
    img = render_pdf_page(pdf, page=0, dpi=100)
    assert img.width > 0
    assert img.height > 0


@_skip_no_latex
def test_render_invalid_page_raises(tmp_path):
    from services.pdf_renderer import compile_latex_to_pdf, PDFRenderer
    pdf = compile_latex_to_pdf(r"x", workdir=str(tmp_path))
    with PDFRenderer(pdf) as r:
        with pytest.raises(IndexError):
            r.render(page=999)


@_skip_no_latex
def test_page_size_pt(tmp_path):
    from services.pdf_renderer import compile_latex_to_pdf, PDFRenderer
    pdf = compile_latex_to_pdf(r"x", workdir=str(tmp_path))
    with PDFRenderer(pdf) as r:
        w, h = r.page_size_pt(0)
        assert w > 0 and h > 0


@_skip_no_latex
def test_renderer_close_releases_handle(tmp_path):
    """Sau khi close, file phải có thể xóa (Windows quan trọng)."""
    from services.pdf_renderer import compile_latex_to_pdf, PDFRenderer
    workdir = tempfile.mkdtemp(prefix="pdftest_close_")
    try:
        pdf = compile_latex_to_pdf(r"y", workdir=workdir)
        r = PDFRenderer(pdf)
        _ = r.render(page=0, dpi=72)
        r.close()
        # Sau close, có thể xóa file
        os.remove(pdf)
        assert not os.path.exists(pdf)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ── Test PDFPreviewDialog imports (UI không init thật) ─────────────────────

def test_pdf_preview_dialog_importable():
    from ui.pdf_preview_dialog import PDFPreviewDialog
    assert hasattr(PDFPreviewDialog, "from_latex")
    assert hasattr(PDFPreviewDialog, "_zoom_in")
    assert hasattr(PDFPreviewDialog, "_zoom_out")
    assert hasattr(PDFPreviewDialog, "_zoom_fit")


# ── Tab QC integration smoke ───────────────────────────────────────────────

def test_tab_qc_has_view_pdf_method():
    from ui.tab_qc import TabQC
    assert hasattr(TabQC, "_view_question_pdf")
    assert hasattr(TabQC, "_latex_escape_question")


def test_latex_escape_preserves_math():
    """Escape phải giữ nguyên block math $...$."""
    from ui.tab_qc import TabQC
    text = "Tính $x^2 + 2x = 0$ với x ∈ {1, 2}"
    out = TabQC._latex_escape_question(text)
    assert "$x^2 + 2x = 0$" in out  # math giữ nguyên
    assert r"\{" in out  # { ngoài math được escape
    assert r"\}" in out


def test_latex_escape_special_chars():
    from ui.tab_qc import TabQC
    text = "100% & a_b # ~ ^"
    out = TabQC._latex_escape_question(text)
    assert r"\%" in out
    assert r"\&" in out
    assert r"\_" in out
    assert r"\#" in out


def test_latex_escape_empty():
    from ui.tab_qc import TabQC
    assert TabQC._latex_escape_question("") == ""
    assert TabQC._latex_escape_question(None) == ""  # type: ignore


# ── Tab TikZ integration smoke ─────────────────────────────────────────────

def test_tab_tikz_has_pdf_renderer_lifecycle():
    from ui.tab_tikz import TabTikZ
    assert hasattr(TabTikZ, "_close_pdf_renderer")


# ── Regression: prompt format() không có brace literal chưa escape ─────────
# Lỗi "KeyError: 'of=perp and AB, by=M'" ở v4.0.1 — TikZ literal trong prompt
# có `{...}` bị Python format() hiểu là placeholder. Test này chặn re-occurrence.

def test_ai_draw_prompt_format_safe():
    """_AI_DRAW_PROMPT.format(description=..., kb_examples=...) phải không
    raise KeyError. Nghĩa là tất cả `{`/`}` literal trong prompt đã được
    escape thành `{{`/`}}`. Chỉ `{description}` và `{kb_examples}` là
    placeholder thật."""
    from ui.tab_tikz import _AI_DRAW_PROMPT
    out = _AI_DRAW_PROMPT.format(description="dummy desc", kb_examples="dummy kb")
    assert "dummy desc" in out
    assert len(out) > 5000  # prompt lớn, nếu < 5KB là format() đã ăn nhiều


def test_ai_describe_text_prompt_format_safe():
    from ui.tab_tikz import _AI_DESCRIBE_TEXT_PROMPT
    out = _AI_DESCRIBE_TEXT_PROMPT.format(content="ΔABC vuông tại A, AB<AC")
    assert "ΔABC" in out


def test_ai_describe_image_prompt_no_format_args():
    """_AI_DESCRIBE_IMAGE_PROMPT KHÔNG dùng .format() (gọi trực tiếp).
    Nhưng vẫn phải hợp lệ Python string — kiểm tra import được.
    """
    from ui.tab_tikz import _AI_DESCRIBE_IMAGE_PROMPT
    assert isinstance(_AI_DESCRIBE_IMAGE_PROMPT, str)
    assert len(_AI_DESCRIBE_IMAGE_PROMPT) > 1000
