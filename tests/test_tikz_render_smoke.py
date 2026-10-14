"""
tests/test_tikz_render_smoke.py — Smoke test cho render TikZ end-to-end.

Render thực sự bằng pdflatex/xelatex/tectonic + PyMuPDF, không mock. Mục đích:
- Đảm bảo render_tikz_to_image() không bị regression NameError/ImportError
  (vd: lỗi "name 'shutil' is not defined" gặp ở v4.0.1)
- Verify các thư viện TikZ thường dùng (calc, intersections, angles, ...) đã
  được include trong _LATEX_TEMPLATE
- Verify TikZ phức tạp (name path, name intersections, foreach, declare
  function) render được — đây là cú pháp AI hay sinh ra

Skip toàn bộ nếu không có LaTeX engine (CI không cài MikTeX/TeX Live).
"""
from __future__ import annotations
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _has_latex_engine() -> bool:
    try:
        from services import latex_engine
        latex_engine.get_engine()
        return True
    except Exception:
        return False


_skip_no_latex = pytest.mark.skipif(
    not _has_latex_engine(), reason="Không có pdflatex/xelatex/tectonic"
)


# ── shutil regression ─────────────────────────────────────────────────────

def test_shutil_imported_at_module_level():
    """shutil phải được import ở top-level tab_tikz để tránh NameError trong
    PyInstaller frozen build (gặp ở v4.0.1: 'name shutil is not defined')."""
    src = (_REPO_ROOT / "ui" / "tab_tikz.py").read_text(encoding="utf-8")
    # Lấy phần trước class TabTikZ — phải có 'import shutil'
    head = src.split("class TabTikZ", 1)[0]
    assert "import shutil" in head, (
        "shutil chưa được import top-level ở ui/tab_tikz.py — "
        "sẽ gây NameError trong frozen EXE."
    )


def test_render_tikz_function_exists():
    from ui.tab_tikz import render_tikz_to_image, render_tikz_to_svg
    assert callable(render_tikz_to_image)
    assert callable(render_tikz_to_svg)


def test_v4_tikz_toolbar_wires_emf_overleaf_and_auto_bank_save():
    src = (_REPO_ROOT / "ui" / "tab_tikz.py").read_text(encoding="utf-8")

    assert "def _save_emf" in src
    assert "def _copy_emf" in src
    assert "def _create_emf_async" in src
    assert "def _open_overleaf" in src
    assert "def _auto_save_rendered_figure" in src
    assert "figure_bank.save_rendered" in src
    assert "💾 EMF" in src
    assert "📋 Copy EMF" in src
    assert "🌐 Overleaf" in src


# ── Render thực tế ─────────────────────────────────────────────────────────

@_skip_no_latex
def test_render_simple_circle():
    from ui.tab_tikz import render_tikz_to_image
    tikz = r"\begin{tikzpicture} \draw (0,0) circle (1cm); \end{tikzpicture}"
    img, log, pdf = render_tikz_to_image(tikz, dpi=150, return_log=True)
    assert img.width > 0 and img.height > 0


@_skip_no_latex
def test_render_with_calc_library():
    """Cú pháp calc: $(A)!t!(B)$ phải render được — thư viện calc đã include."""
    from ui.tab_tikz import render_tikz_to_image
    tikz = r"""\begin{tikzpicture}
\coordinate (A) at (0,0);
\coordinate (B) at (4,0);
\coordinate (M) at ($(A)!0.5!(B)$);
\draw (A)--(B);
\fill (M) circle (2pt);
\end{tikzpicture}"""
    img, _, _ = render_tikz_to_image(tikz, dpi=150, return_log=True)
    assert img.width > 0


@_skip_no_latex
def test_render_with_intersections_library():
    """name path + name intersections — thư viện intersections đã include."""
    from ui.tab_tikz import render_tikz_to_image
    tikz = r"""\begin{tikzpicture}
\coordinate (A) at (0,0);
\coordinate (B) at (4,0);
\coordinate (C) at (2,3);
\path[name path=AB] (A)--(B);
\path[name path=ray] (C)--(2,-1);
\path[name intersections={of=AB and ray, by=P}];
\draw (A)--(B)--(C)--cycle;
\fill (P) circle (2pt);
\end{tikzpicture}"""
    img, _, _ = render_tikz_to_image(tikz, dpi=150, return_log=True)
    assert img.width > 0


@_skip_no_latex
def test_render_with_angles_library():
    """\\pic angle — thư viện angles + quotes."""
    from ui.tab_tikz import render_tikz_to_image
    tikz = r"""\begin{tikzpicture}
\coordinate (A) at (0,0);
\coordinate (B) at (3,0);
\coordinate (C) at (0,2);
\draw (A)--(B)--(C)--cycle;
\pic[draw, angle radius=0.4cm, "$\alpha$"] {angle=B--A--C};
\end{tikzpicture}"""
    img, _, _ = render_tikz_to_image(tikz, dpi=150, return_log=True)
    assert img.width > 0


@_skip_no_latex
def test_render_complex_user_example():
    """Code TikZ user thực sự muốn render được — tổng hợp:
    - declare function
    - calc projection $(A)!(H)!(B)$
    - name path + name intersections (2 cặp)
    - foreach
    """
    from ui.tab_tikz import render_tikz_to_image
    tikz = r"""\begin{tikzpicture}[line join=round, line cap=round, declare function={a=6; h=3;}]
\coordinate (B) at (0,0);
\coordinate (C) at (6,0);
\coordinate (H) at (2,0);
\coordinate (A) at (2,3);
\coordinate (M) at ($(A)!(H)!(B)$);
\coordinate (N) at ($(A)!(H)!(C)$);
\coordinate (D) at ($(A)!(B)!(C)$);
\path[name path=ah] (A) -- (H);
\path[name path=bd] (B) -- (D);
\path[name intersections={of=ah and bd, by=E}];
\coordinate (MN_dir) at ($(N)-(M)$);
\coordinate (D_next) at ($(D)+(MN_dir)$);
\path[name path=df] (D) -- (D_next);
\path[name path=ab] (A) -- (B);
\path[name intersections={of=df and ab, by=F}];
\draw[line width=0.6pt] (A) -- (B) -- (C) -- cycle;
\draw[line width=0.6pt] (A) -- (H);
\draw[line width=0.6pt] (B) -- (D);
\draw[line width=0.6pt] (D) -- (F);
\draw[line width=0.6pt] (E) -- (F);
\foreach \p/\pos in {A/90, B/180, C/0, H/-90, M/135, N/45, D/45, E/-45, F/180} {
  \draw (\p) circle (0.6pt) node[shift={(\pos:8pt)}, font=\large] {$\p$};
}
\end{tikzpicture}"""
    img, log, pdf = render_tikz_to_image(tikz, dpi=300, return_log=True)
    assert img.width > 100 and img.height > 100
    # PDF path returned (return_log=True)
    assert pdf and Path(pdf).exists()


@_skip_no_latex
def test_render_pgfplots_function():
    """pgfplots với hàm số — kiểm tra package pgfplots đã include."""
    from ui.tab_tikz import render_tikz_to_image
    tikz = r"""\begin{tikzpicture}
\begin{axis}[axis lines=center, width=8cm, height=6cm,
             xmin=-3, xmax=3, ymin=-1, ymax=9]
\addplot[blue, thick, domain=-3:3, samples=80] {x^2};
\end{axis}
\end{tikzpicture}"""
    img, _, _ = render_tikz_to_image(tikz, dpi=150, return_log=True)
    assert img.width > 0


@_skip_no_latex
def test_render_returns_pdf_path_when_requested():
    """return_log=True phải trả pdf_path tới file persistent (UI dùng để
    zoom vector qua PDFRenderer)."""
    from ui.tab_tikz import render_tikz_to_image
    tikz = r"\begin{tikzpicture} \draw (0,0)--(2,1); \end{tikzpicture}"
    img, log, pdf = render_tikz_to_image(tikz, dpi=150, return_log=True)
    assert pdf, "Phải có persistent_pdf path khi return_log=True"
    assert Path(pdf).exists()
    assert Path(pdf).stat().st_size > 100  # PDF non-trivial
