"""
tests/test_overleaf_exporter.py -- Test services/overleaf_exporter.py.

Coverage:
  - Wrap bare TikZ into a complete LaTeX document.
  - Preserve already-complete LaTeX documents.
  - Build the Overleaf encoded_snip launcher form.
  - Write/open local launcher without touching a real browser in tests.
"""
from __future__ import annotations

from services import overleaf_exporter


BARE_TIKZ = r"""\begin{tikzpicture}
  \draw (0,0) -- (1,1);
\end{tikzpicture}"""


def test_build_tikz_tex_source_wraps_bare_tikz():
    tex = overleaf_exporter.build_tikz_tex_source(BARE_TIKZ)

    assert r"\documentclass" in tex
    assert r"\usepackage{tikz}" in tex
    assert r"\usepackage{pgfplots}" in tex
    assert BARE_TIKZ in tex


def test_build_tikz_tex_source_preserves_full_document():
    source = "\\documentclass{article}\r\n\\begin{document}\r\nHi\r\n\\end{document}"

    tex = overleaf_exporter.build_tikz_tex_source(source)

    assert tex == "\\documentclass{article}\n\\begin{document}\nHi\n\\end{document}"


def test_build_tikz_tex_source_rejects_empty_input():
    try:
        overleaf_exporter.build_tikz_tex_source("  ")
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty TikZ source")


def test_build_overleaf_launcher_html_contains_encoded_form():
    tex = overleaf_exporter.build_tikz_tex_source(BARE_TIKZ)

    html = overleaf_exporter.build_overleaf_launcher_html(tex)

    assert 'action="https://www.overleaf.com/docs"' in html
    assert 'name="encoded_snip"' in html
    assert 'name="engine" value="pdflatex"' in html
    assert 'name="main_document" value="main.tex"' in html
    assert "%5Cdocumentclass" in html
    assert r"\begin{tikzpicture}" in html


def test_write_overleaf_launcher_creates_local_html(tmp_path, monkeypatch):
    monkeypatch.setattr(
        overleaf_exporter.tempfile,
        "gettempdir",
        lambda: str(tmp_path),
    )

    path, tex = overleaf_exporter.write_overleaf_launcher(BARE_TIKZ)

    assert path.exists()
    assert path.parent == tmp_path / "MatrixExamAI_overleaf"
    assert r"\begin{tikzpicture}" in tex
    assert "encoded_snip" in path.read_text(encoding="utf-8")


def test_open_tikz_in_overleaf_uses_browser_launcher(tmp_path, monkeypatch):
    opened: list[tuple[str, int]] = []
    monkeypatch.setattr(
        overleaf_exporter.tempfile,
        "gettempdir",
        lambda: str(tmp_path),
    )
    monkeypatch.setattr(
        overleaf_exporter.webbrowser,
        "open",
        lambda url, new=0: opened.append((url, new)) or True,
    )

    path, tex = overleaf_exporter.open_tikz_in_overleaf(BARE_TIKZ)

    assert path.exists()
    assert r"\documentclass" in tex
    assert opened == [(path.as_uri(), 2)]
