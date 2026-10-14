"""
services/overleaf_exporter.py -- Open TikZ code in Overleaf without local TeX.

Overleaf supports "Open in Overleaf" by posting a LaTeX snippet to
https://www.overleaf.com/docs. This module builds a complete .tex document and
opens a tiny local HTML launcher that auto-submits the source to Overleaf.
"""

from __future__ import annotations

import html
import tempfile
import uuid
import webbrowser
from pathlib import Path
from urllib.parse import quote

OVERLEAF_DOCS_URL = "https://www.overleaf.com/docs"


_OVERLEAF_TIKZ_TEMPLATE = r"""\documentclass[border=10pt,tikz,preview]{standalone}
\usepackage{iftex}
\ifPDFTeX
  \usepackage[utf8]{inputenc}
  \usepackage[T5]{fontenc}
\fi
\usepackage{amsmath,amssymb}
\usepackage{preview}
\usepackage{tikz}
\usepackage{pgfplots}
\usepackage{tkz-tab}
\usepackage{array,booktabs,cellspace}
\usepackage{bm}
\pgfplotsset{compat=1.18}
\usetikzlibrary{calc,angles,quotes,patterns,arrows.meta,decorations.markings,intersections,decorations.pathreplacing}
\PreviewEnvironment{tikzpicture}
\pagestyle{empty}
\begin{document}
% TikZ source exported from MatrixExam AI.
% If Overleaf asks for an engine, choose pdfLaTeX.
{tikz_code}
\end{document}
"""


def build_tikz_tex_source(tikz_code: str) -> str:
    """Return a complete LaTeX document ready for Overleaf.

    If the input is already a full LaTeX document, keep it as-is. Otherwise
    wrap the TikZ block using tikz_ai_skill's intelligent package/library detection.
    """
    code = (tikz_code or "").strip()
    if not code:
        raise ValueError("TikZ code is empty.")
    if "\\documentclass" in code and "\\begin{document}" in code:
        return code.replace("\r\n", "\n").replace("\r", "\n")
    try:
        from services import tikz_ai_skill
        return tikz_ai_skill.build_standalone_latex(code)
    except Exception:
        return _OVERLEAF_TIKZ_TEMPLATE.replace("{tikz_code}", code)


def build_overleaf_launcher_html(tex_source: str, *, engine: str = "pdflatex") -> str:
    """Build an auto-submit HTML page that posts source to Overleaf."""
    encoded = quote(tex_source.replace("\r\n", "\n").replace("\r", "\n"), safe="")
    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <title>Open TikZ in Overleaf</title>
  <style>
    body {{
      font-family: Segoe UI, Arial, sans-serif;
      margin: 32px;
      color: #0f172a;
      background: #f8fafc;
    }}
    button {{
      background: #16a34a;
      color: white;
      border: 0;
      padding: 10px 16px;
      border-radius: 6px;
      font-weight: 700;
      cursor: pointer;
    }}
    textarea {{
      width: 100%;
      min-height: 220px;
      margin-top: 16px;
      font-family: Consolas, monospace;
      font-size: 12px;
    }}
  </style>
</head>
<body onload="document.getElementById('ol_form').submit()">
  <h2>Đang mở TikZ trong Overleaf...</h2>
  <p>Nếu trình duyệt không tự chuyển tiếp, bấm nút bên dưới.</p>
  <form id="ol_form" action="{OVERLEAF_DOCS_URL}" method="post">
    <input type="hidden" name="encoded_snip" value="{html.escape(encoded, quote=True)}">
    <input type="hidden" name="engine" value="{html.escape(engine, quote=True)}">
    <input type="hidden" name="main_document" value="main.tex">
    <button type="submit">Mở trên Overleaf</button>
  </form>
  <p>Source dự phòng để copy thủ công:</p>
  <textarea readonly>{html.escape(tex_source)}</textarea>
</body>
</html>
"""


def write_overleaf_launcher(tikz_code: str) -> tuple[Path, str]:
    """Write the local launcher HTML and return (path, tex_source)."""
    tex_source = build_tikz_tex_source(tikz_code)
    html_text = build_overleaf_launcher_html(tex_source)
    out_dir = Path(tempfile.gettempdir()) / "MatrixExamAI_overleaf"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"overleaf_tikz_{uuid.uuid4().hex[:10]}.html"
    path.write_text(html_text, encoding="utf-8")
    return path, tex_source


def open_tikz_in_overleaf(tikz_code: str) -> tuple[Path, str]:
    """Open the TikZ code in Overleaf through the local launcher."""
    path, tex_source = write_overleaf_launcher(tikz_code)
    webbrowser.open(path.as_uri(), new=2)
    return path, tex_source
