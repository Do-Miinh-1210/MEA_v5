"""
tests/test_tikz_ai_skill.py — Unit tests cho TikZ AI Skill (Phong cách Thầy Đỗ Minh - DoMinhMath).
"""

from __future__ import annotations

import pytest
from services import tikz_ai_skill
from services import tikz_preflight as pf
from services import overleaf_exporter


def test_get_tikz_system_prompt():
    prompt = tikz_ai_skill.get_tikz_system_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 500
    assert "QUY TRÌNH 5 BƯỚC" in prompt or "QUY TẮC" in prompt
    assert r"\normalsize" in prompt
    assert "line cap=round" in prompt
    assert "tkzTabVar" in prompt


def test_get_tikz_draw_prompt():
    desc = "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng a"
    kb = r"""=== TEMPLATE: Chóp tam giác đều ===
\begin{tikzpicture}
  \path (0,0) coordinate (A);
\end{tikzpicture}"""
    prompt = tikz_ai_skill.get_tikz_draw_prompt(desc, kb)
    assert desc in prompt
    assert "MẪU THƯ VIỆN THAM KHẢO" in prompt
    assert kb in prompt
    assert "declare function" in prompt


def test_get_tikz_edit_prompt():
    code = r"\begin{tikzpicture}\draw (0,0)--(1,1);\end{tikzpicture}"
    req = "Thêm nhãn A tại (0,0) và B tại (1,1)"
    prompt = tikz_ai_skill.get_tikz_edit_prompt(code, req)
    assert code in prompt
    assert req in prompt
    assert "BẢO TỒN NGUYÊN TRẠNG" in prompt


def test_get_tikz_optimization_prompt():
    code = r"\begin{tikzpicture}\draw (0,0)--(2,0)--(1,1)--cycle;\end{tikzpicture}"
    prompt = tikz_ai_skill.get_tikz_optimization_prompt(code)
    assert code in prompt
    assert "THAM SỐ HÓA" in prompt or "Parameterization" in prompt
    assert "LAYERING RULES" in prompt or "5 lớp" in prompt


def test_extract_tikz_code():
    # 1. From documentclass and begin/end document
    full_doc = r"""\documentclass{standalone}
\usepackage{tikz}
\begin{document}
\begin{tikzpicture}[scale=1.5]
  \draw (0,0) circle (1);
\end{tikzpicture}
\end{document}"""
    assert tikz_ai_skill.extract_tikz_code(full_doc) == (
        "\\begin{tikzpicture}[scale=1.5]\n  \\draw (0,0) circle (1);\n\\end{tikzpicture}"
    )

    # 2. From markdown fence
    fenced = """Đây là code bạn cần:
```latex
\\begin{tikzpicture}
  \\draw (0,0) -- (1,1);
\\end{tikzpicture}
```
Chúc bạn thành công!"""
    assert tikz_ai_skill.extract_tikz_code(fenced) == (
        "\\begin{tikzpicture}\n  \\draw (0,0) -- (1,1);\n\\end{tikzpicture}"
    )

    # 3. Circuitikz environment
    circuit = r"""\begin{circuitikz}[european]
  \draw (0,0) to[battery] (0,2);
\end{circuitikz}"""
    assert tikz_ai_skill.extract_tikz_code(circuit) == circuit

    # 4. Axis environment auto-wrap
    axis_snippet = r"""\begin{axis}[xmin=-2, xmax=2]
  \addplot {x^2};
\end{axis}"""
    extracted_axis = tikz_ai_skill.extract_tikz_code(axis_snippet)
    assert extracted_axis.startswith(r"\begin{tikzpicture}")
    assert extracted_axis.endswith(r"\end{tikzpicture}")
    assert r"\begin{axis}" in extracted_axis


def test_build_standalone_latex():
    # Test auto detection of packages & libraries
    sample = r"""\begin{tikzpicture}[scale=1]
  \draw pic{right angle=A--B--C};
  \fill[pattern={Lines[angle=45, distance=4pt, line width=0.3pt]}] (0,0) rectangle (2,2);
  \node at (0,0) {$\qty{5}{\metre\per\second}$};
  \addplot {x^2};
\end{tikzpicture}"""
    standalone = tikz_ai_skill.build_standalone_latex(sample)
    assert r"\documentclass[tikz,border=10mm]{standalone}" in standalone
    assert r"\usepackage[utf8]{vietnam}" in standalone
    assert "angles" in standalone
    assert "quotes" in standalone
    assert "patterns.meta" in standalone
    assert "physics,siunitx" in standalone
    assert "pgfplots" in standalone
    assert r"\begin{document}" in standalone
    assert r"\end{document}" in standalone


def test_overleaf_exporter_integration():
    code = r"""\begin{tikzpicture}
  \draw pic{right angle=A--B--C};
\end{tikzpicture}"""
    tex = overleaf_exporter.build_tikz_tex_source(code)
    assert r"\documentclass[tikz,border=10mm]{standalone}" in tex
    assert "angles" in tex


def test_preflight_rules_and_autofix():
    # 1. line cap=round
    code_linecap = r"\begin{tikzpicture}[scale=1.2, line cap=round, line join=round]\draw (0,0)--(1,1);\end{tikzpicture}"
    issues = pf.check(code_linecap)
    assert any(i.rule == "forbidden_line_cap" for i in issues)
    fixed = pf.auto_fix(code_linecap)
    assert "line cap=round" not in fixed
    assert "scale=1.2" in fixed

    # 2. legacy pattern
    code_pattern = r"\fill[pattern=north west lines, pattern color=black] (0,0) rectangle (1,1);"
    issues_pat = pf.check(code_pattern)
    assert any(i.rule == "legacy_pattern" for i in issues_pat)
    fixed_pat = pf.auto_fix(code_pattern)
    assert "pattern={Lines[angle=45" in fixed_pat
    assert "gray!70" in fixed_pat

    # 3. tkzTabVar style hint
    code_tabvar = r"\begin{tikzpicture}\tkzTabVar{+/$+\infty$, -/$-1$}\end{tikzpicture}"
    issues_tab = pf.check(code_tabvar)
    assert any(i.rule == "tkz_tab_var_style" for i in issues_tab)


def test_skill_docs_and_examples():
    docs = tikz_ai_skill.get_skill_docs()
    if docs:
        assert "SKILL.md" in docs or "01-workflow.md" in docs
    examples = tikz_ai_skill.get_skill_examples()
    if examples:
        assert r"\begin{tikzpicture}" in examples


def test_get_tikz_vision_prompt_and_clean_boilerplate():
    prompt = tikz_ai_skill.get_tikz_vision_prompt(
        extra_prompt="Vẽ hình chóp tứ giác đều",
        tasks=["Bảng biến thiên (BBT)", "Đồ thị"],
        enable_notes=True,
        bbt_no_frame=False,
    )
    assert "QUY TRÌNH XỬ LÝ TRỰC QUAN" in prompt
    assert "Bảng biến thiên (BBT)" in prompt
    assert "Vẽ hình chóp tứ giác đều" in prompt
    assert r"\normalsize" in prompt

    # Test clean_tikz_boilerplate
    raw_ai_output = """Dưới đây là mã TikZ:
```latex
\\begin{tikzpicture}[every node/.style={font=\\normalsize}]
  \\draw (0,0) -- (1,1);
\\end{tikzpicture}
```
Chúc bạn học tốt!"""
    cleaned = tikz_ai_skill.clean_tikz_boilerplate(raw_ai_output)
    assert cleaned.startswith(r"\begin{tikzpicture}")
    assert cleaned.endswith(r"\end{tikzpicture}")
    assert "```" not in cleaned
    assert "Dưới đây là" not in cleaned

    # Test clean_boilerplate (tuple format)
    cleaned2, was_removed = tikz_ai_skill.clean_boilerplate(raw_ai_output)
    assert was_removed is True
    assert cleaned2.startswith(r"\begin{tikzpicture}")
    assert cleaned2.endswith(r"\end{tikzpicture}")

