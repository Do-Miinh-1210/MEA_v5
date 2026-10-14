"""Tests for the UI-independent TikZ rendering service."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from services import tikz_renderer


def _has_latex_engine() -> bool:
    try:
        tikz_renderer.latex_engine.get_engine()
        return True
    except Exception:
        return False


def test_tikz_renderer_exports_render_contract():
    assert callable(tikz_renderer.render_tikz_to_image)
    assert callable(tikz_renderer.render_tikz_to_svg)
    assert r"\usepackage{{tikz}}" in tikz_renderer._LATEX_TEMPLATE
    assert "intersections" in tikz_renderer._LATEX_TEMPLATE


def test_compile_pdf_reports_missing_engine(monkeypatch, tmp_path):
    def missing_engine():
        raise tikz_renderer.latex_engine.LatexEngineNotFound("missing engine")

    monkeypatch.setattr(tikz_renderer.latex_engine, "get_engine", missing_engine)

    with pytest.raises(RuntimeError, match="missing engine"):
        tikz_renderer._compile_pdf(
            r"\begin{tikzpicture}\end{tikzpicture}",
            str(tmp_path),
        )


def test_compile_pdf_writes_tex_and_invokes_engine(monkeypatch, tmp_path):
    class FakeEngine:
        name = "fake"

        @staticmethod
        def build_argv(filename):
            return ["fake-engine", filename]

    monkeypatch.setattr(tikz_renderer.latex_engine, "get_engine", lambda: FakeEngine())

    def fake_run(*_args, **_kwargs):
        (tmp_path / "figure.pdf").write_bytes(b"%PDF-test")
        return SimpleNamespace(stdout="compile ok", stderr="")

    monkeypatch.setattr(tikz_renderer.subprocess, "run", fake_run)

    pdf_path, log_text = tikz_renderer._compile_pdf(
        r"\begin{tikzpicture}\draw (0,0)--(1,1);\end{tikzpicture}",
        str(tmp_path),
    )

    assert Path(pdf_path).exists()
    assert "tikzpicture" in (tmp_path / "figure.tex").read_text(encoding="utf-8")
    assert "compile ok" in log_text


@pytest.mark.skipif(not _has_latex_engine(), reason="Không có LaTeX engine")
def test_render_simple_tikz_to_png_and_pdf():
    image, _log_text, pdf_path = tikz_renderer.render_tikz_to_image(
        r"\begin{tikzpicture}\draw (0,0) circle (1cm);\end{tikzpicture}",
        dpi=120,
        return_log=True,
    )

    assert image.width > 0 and image.height > 0
    assert Path(pdf_path).exists()
    Path(pdf_path).unlink(missing_ok=True)
