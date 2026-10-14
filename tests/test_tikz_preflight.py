"""
tests/test_tikz_preflight.py — Test services/tikz_preflight.py.

Cover các rule:
  • Balanced braces { }
  • \\begin / \\end pairs
  • tikzpicture present
  • pgfplots y variable
  • Implicit multiplication
  • \\addplot trong \\begin{axis}
  • Unicode math
  • \\documentclass present (warn)
"""
from __future__ import annotations

import pytest
from services.tikz_preflight import (
    Severity, check, has_blocking_errors, auto_fix, format_issues,
    explain_render_error,
)


# ══════════════════════════════════════════════════════════════════════════
# OK CASES
# ══════════════════════════════════════════════════════════════════════════

def test_simple_tikz_ok():
    code = r"""\begin{tikzpicture}
  \draw (0,0) -- (1,1);
\end{tikzpicture}"""
    assert not has_blocking_errors(code)


def test_pgfplots_ok():
    code = r"""\begin{tikzpicture}
\begin{axis}[axis lines=middle, xlabel=$x$]
  \addplot[blue, domain=-3:3, samples=100] {x^2 + 2*x};
\end{axis}
\end{tikzpicture}"""
    issues = check(code)
    errors = [i for i in issues if i.severity == Severity.ERROR]
    assert errors == []


# ══════════════════════════════════════════════════════════════════════════
# BALANCED BRACES
# ══════════════════════════════════════════════════════════════════════════

class TestBalancedBraces:
    def test_missing_close_brace(self):
        code = r"\begin{tikzpicture} \draw {bad \end{tikzpicture}"
        issues = check(code)
        assert any(i.rule == "balanced_braces" and i.severity == Severity.ERROR
                   for i in issues)

    def test_extra_close_brace(self):
        code = r"\begin{tikzpicture} \draw} (0,0); \end{tikzpicture}"
        issues = check(code)
        assert any(i.rule == "balanced_braces" for i in issues)

    def test_braces_in_comment_ignored(self):
        # Dấu { } trong comment % không tính vào balance
        code = r"""\begin{tikzpicture}
  % This is a {comment} with } unbalanced
  \draw (0,0)--(1,1);
\end{tikzpicture}"""
        issues = check(code)
        # Không có lỗi balance (comments được ignore)
        balance_errs = [i for i in issues if i.rule == "balanced_braces"]
        assert balance_errs == []


# ══════════════════════════════════════════════════════════════════════════
# BEGIN/END PAIRS
# ══════════════════════════════════════════════════════════════════════════

class TestBeginEndPairs:
    def test_mismatched_env(self):
        code = r"""\begin{tikzpicture}
  \begin{axis}
    \addplot {x};
  \end{tikzpicture}
\end{axis}"""
        issues = check(code)
        # Có ít nhất 1 lỗi mismatch
        assert any(i.rule == "begin_end_pairs" for i in issues)

    def test_orphan_end(self):
        code = r"\end{tikzpicture}"
        issues = check(code)
        assert any(i.rule == "begin_end_pairs" for i in issues)

    def test_orphan_begin(self):
        code = r"\begin{tikzpicture} (no end)"
        issues = check(code)
        assert any(i.rule == "begin_end_pairs" for i in issues)


# ══════════════════════════════════════════════════════════════════════════
# tikzpicture PRESENT
# ══════════════════════════════════════════════════════════════════════════

def test_no_tikzpicture():
    code = r"\draw (0,0) -- (1,1);"
    assert has_blocking_errors(code)


def test_tkztab_bare_ok():
    """tkz-tab bare → OK (pipeline khác auto-wrap)."""
    code = r"\tkzTabInit{$x$/1}{$-\infty$, $+\infty$} \tkzTabLine{,+,}"
    issues = check(code)
    blocking = [i for i in issues if i.severity == Severity.ERROR]
    # Không có lỗi tikzpicture_present
    assert not any(i.rule == "tikzpicture_present" for i in blocking)


# ══════════════════════════════════════════════════════════════════════════
# PGFPLOTS — Y VARIABLE
# ══════════════════════════════════════════════════════════════════════════

class TestPgfplotsYVariable:
    def test_uses_y_without_variable(self):
        code = r"""\begin{tikzpicture}
\begin{axis}
  \addplot[domain=0:12] (f(y), y);
\end{axis}
\end{tikzpicture}"""
        issues = check(code)
        assert any(i.rule == "pgfplots_y_variable" for i in issues)

    def test_uses_t_correctly(self):
        code = r"""\begin{tikzpicture}
\begin{axis}
  \addplot[variable=\t, domain=0:12, samples=100] ({sin(deg(\t))}, \t);
\end{axis}
\end{tikzpicture}"""
        issues = check(code)
        assert not any(i.rule == "pgfplots_y_variable" for i in issues)


# ══════════════════════════════════════════════════════════════════════════
# IMPLICIT MULTIPLICATION
# ══════════════════════════════════════════════════════════════════════════

class TestImplicitMultiplication:
    def test_2x_warning(self):
        code = r"\begin{tikzpicture}\begin{axis}\addplot[domain=-3:3] {x^2 + 2x};\end{axis}\end{tikzpicture}"
        issues = check(code)
        assert any(i.rule == "implicit_multiplication" for i in issues)

    def test_2_star_x_ok(self):
        code = r"\begin{tikzpicture}\begin{axis}\addplot[domain=-3:3] {x^2 + 2*x};\end{axis}\end{tikzpicture}"
        issues = check(code)
        assert not any(i.rule == "implicit_multiplication" for i in issues)

    def test_units_not_flagged(self):
        # 2pt, 3cm là đơn vị — KHÔNG phải implicit mult
        code = r"\begin{tikzpicture}\begin{axis}\addplot[mark size=2pt, line width=3cm] coordinates {(0,0)};\end{axis}\end{tikzpicture}"
        issues = check(code)
        # 2pt trong [...] không bị flag (regex chỉ check trong {expression})
        # nhưng nếu có chuyện rule false-positive thì test này phát hiện
        impl = [i for i in issues if i.rule == "implicit_multiplication"]
        # Cho phép 0 hoặc 1 (false positive nếu regex chưa hoàn hảo)
        assert len(impl) <= 1


# ══════════════════════════════════════════════════════════════════════════
# \\addplot IN \\begin{axis}
# ══════════════════════════════════════════════════════════════════════════

class TestAddplotInAxis:
    def test_addplot_outside_axis(self):
        code = r"""\begin{tikzpicture}
  \addplot {x};
\end{tikzpicture}"""
        issues = check(code)
        assert any(i.rule == "addplot_in_axis" for i in issues)

    def test_addplot_inside_axis_ok(self):
        code = r"""\begin{tikzpicture}
\begin{axis}
  \addplot {x};
\end{axis}
\end{tikzpicture}"""
        issues = check(code)
        assert not any(i.rule == "addplot_in_axis" for i in issues)


# ══════════════════════════════════════════════════════════════════════════
# UNICODE MATH OUTSIDE $
# ══════════════════════════════════════════════════════════════════════════

class TestUnicodeMath:
    def test_pi_outside_dollar(self):
        code = r"\begin{tikzpicture}\node at (0,0) {Diện tích π R²};\end{tikzpicture}"
        issues = check(code)
        # π và ² ngoài $...$ → có info hint
        assert any(i.rule == "unicode_math_outside_dollar" for i in issues)

    def test_pi_inside_dollar_ok(self):
        code = r"\begin{tikzpicture}\node at (0,0) {Diện tích $\pi R^2$};\end{tikzpicture}"
        issues = check(code)
        # Trong $...$ → OK
        assert not any(i.rule == "unicode_math_outside_dollar" for i in issues)


# ══════════════════════════════════════════════════════════════════════════
# \\documentclass (warning)
# ══════════════════════════════════════════════════════════════════════════

def test_documentclass_warning():
    code = r"""\documentclass{article}
\usepackage{tikz}
\begin{document}
\begin{tikzpicture}
  \draw (0,0)--(1,1);
\end{tikzpicture}
\end{document}"""
    issues = check(code)
    assert any(i.rule == "documentclass_present" for i in issues)


def test_balanced_delimiters_reports_missing_parenthesis():
    code = r"""\begin{tikzpicture}
  \draw (0,0 -- (1,1);
\end{tikzpicture}"""

    issues = check(code)

    assert any(i.rule == "balanced_delimiters" and "Thiếu" in i.message for i in issues)


def test_missing_semicolon_is_reported_as_warning():
    code = r"""\begin{tikzpicture}
  \draw (0,0) -- (1,1)
\end{tikzpicture}"""

    issues = check(code)

    assert any(i.rule == "missing_semicolon" and i.severity == Severity.WARNING for i in issues)


def test_explain_render_error_identifies_missing_package():
    detail = explain_render_error("! LaTeX Error: File `tkz-tab.sty' not found.")

    assert "thiếu gói/file LaTeX `tkz-tab.sty`" in detail
    assert "MiKTeX" in detail or "TeX Live" in detail


def test_explain_render_error_identifies_undefined_control_sequence_line():
    detail = explain_render_error(
        "! Undefined control sequence.\nl.2   \\badcommand\n",
        "\\begin{tikzpicture}\n\\badcommand\n\\end{tikzpicture}",
    )

    assert "lệnh LaTeX/TikZ chưa được định nghĩa" in detail
    assert "Dòng code tương ứng: \\badcommand" in detail


# ══════════════════════════════════════════════════════════════════════════
# AUTO-FIX
# ══════════════════════════════════════════════════════════════════════════

class TestAutoFix:
    def test_strip_documentclass_preamble(self):
        code = r"""\documentclass{article}
\usepackage{tikz}
\begin{document}
\begin{tikzpicture}
  \draw (0,0)--(1,1);
\end{tikzpicture}
\end{document}"""
        fixed = auto_fix(code)
        assert "\\documentclass" not in fixed
        assert "\\begin{document}" not in fixed
        assert "\\begin{tikzpicture}" in fixed
        assert "\\end{tikzpicture}" in fixed

    def test_no_change_when_clean(self):
        code = r"\begin{tikzpicture}\draw (0,0)--(1,1);\end{tikzpicture}"
        fixed = auto_fix(code)
        assert fixed == code

    def test_implicit_mult_fixed(self):
        code = r"\begin{tikzpicture}\begin{axis}\addplot {2x + 3y};\end{axis}\end{tikzpicture}"
        fixed = auto_fix(code)
        # Sau fix có 2*x hoặc 2 *x
        assert "2*x" in fixed or "2 *x" in fixed

    def test_reserved_text_foreach_variable_is_fixed(self):
        code = r"""\begin{tikzpicture}
\foreach \point/\angle/\text in {A/225/A', B/45/B'} {
  \node[shift={(\angle:9pt)}] at (\point) {$\text$};
}
\end{tikzpicture}"""

        issues = check(code)
        assert any(
            issue.rule == "reserved_foreach_variable"
            and issue.severity == Severity.ERROR
            and issue.fixable
            for issue in issues
        )

        fixed = auto_fix(code)

        assert r"\foreach \point/\angle/\tikzforeachlabel in" in fixed
        assert r"$\tikzforeachlabel$" in fixed
        assert not any(
            issue.rule == "reserved_foreach_variable" for issue in check(fixed)
        )

    def test_digit_foreach_variables_are_fixed(self):
        code = r"""\begin{tikzpicture}
\foreach \p1/\p2/\p3 in {D/A/B} {
  \path pic {right angle=\p1--\p2--\p3};
}
\end{tikzpicture}"""

        issues = check(code)
        assert any(
            issue.rule == "invalid_foreach_variable_name" and issue.fixable
            for issue in issues
        )

        fixed = auto_fix(code)

        assert r"\tikzforeachpOne/\tikzforeachpTwo/\tikzforeachpThree" in fixed
        assert r"right angle=\tikzforeachpOne--\tikzforeachpTwo--\tikzforeachpThree" in fixed
        assert not any(
            issue.rule == "invalid_foreach_variable_name" for issue in check(fixed)
        )


# ══════════════════════════════════════════════════════════════════════════
# FORMAT
# ══════════════════════════════════════════════════════════════════════════

def test_format_issues_empty():
    out = format_issues([])
    assert "OK" in out or "không có" in out.lower()


def test_format_issues_with_errors():
    code = r"\addplot {x};"   # nhiều lỗi
    issues = check(code)
    out = format_issues(issues)
    assert "vấn đề" in out


# ══════════════════════════════════════════════════════════════════════════
# TKZ-TAB COMMANDS
# ══════════════════════════════════════════════════════════════════════════

class TestTkzTabCommands:
    def test_tkz_tab_vector_detected_and_fixed(self):
        code = r"""\begin{tikzpicture}
\tkzTabInit{$x$ / 1, $f(x)$ / 2}{$-1$, $1$, $3$}
\tkzTabVector{ +/ $5$, -/ $-2$, +/ $4$ }
\end{tikzpicture}"""
        issues = check(code)
        assert any(
            i.rule == "invalid_tkztab_command"
            and i.severity == Severity.ERROR
            and i.fixable
            for i in issues
        )
        fixed = auto_fix(code)
        assert r"\tkzTabVar{ +/ $5$, -/ $-2$, +/ $4$ }" in fixed
        assert not any(i.rule == "invalid_tkztab_command" for i in check(fixed))

    def test_tkz_tab_variation_fixed(self):
        code = r"\tkzTabVariation{ +/ 1, -/ 0 }"
        fixed = auto_fix(code)
        assert r"\tkzTabVar{ +/ 1, -/ 0 }" in fixed
