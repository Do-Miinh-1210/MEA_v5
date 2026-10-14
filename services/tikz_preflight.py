"""
services/tikz_preflight.py — Pre-flight syntax check cho code TikZ TRƯỚC khi
gọi pdflatex. Bắt các lỗi phổ biến trong vài ms thay vì chờ pdflatex 10-30s.

API:
    >>> from services import tikz_preflight as pf
    >>> issues = pf.check(tikz_code)        # list[Issue]
    >>> for i in issues: print(i.severity, i.message)
    >>> fixed = pf.auto_fix(tikz_code)      # apply quick fixes (best-effort)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Severity(Enum):
    ERROR = "error"      # Sẽ fail pdflatex chắc chắn
    WARNING = "warning"  # Có thể fail, có thể không
    INFO = "info"        # Style hint, không fail


@dataclass
class Issue:
    severity: Severity
    line:     int           # 1-based line number, 0 = unknown
    message:  str
    rule:     str           # tên rule (debug)
    fixable:  bool = False  # auto_fix có sửa được không


# ══════════════════════════════════════════════════════════════════════════
# RULES — danh sách check
# ══════════════════════════════════════════════════════════════════════════

def _check_balanced_braces(code: str) -> list[Issue]:
    """Check { và } cân bằng. Bỏ qua {} trong comment (% ...)."""
    issues = []
    open_count = 0
    for line_no, line in enumerate(code.splitlines(), 1):
        # Bỏ phần sau %
        line_no_comment = re.split(r"(?<!\\)%", line, 1)[0]
        for ch in line_no_comment:
            if ch == "{":
                open_count += 1
            elif ch == "}":
                open_count -= 1
                if open_count < 0:
                    issues.append(Issue(
                        Severity.ERROR, line_no,
                        "Thừa `}` — đóng ngoặc nhiều hơn mở",
                        "balanced_braces",
                    ))
                    open_count = 0  # reset để báo các lỗi tiếp theo
    if open_count > 0:
        issues.append(Issue(
            Severity.ERROR, 0,
            f"Thiếu {open_count} dấu `}}` — không cân bằng ngoặc",
            "balanced_braces",
        ))
    return issues


def _check_begin_end_pairs(code: str) -> list[Issue]:
    """Check \\begin{X} ... \\end{X} cân bằng và đúng cặp."""
    issues = []
    stack: list[tuple[int, str]] = []  # (line, env_name)
    for line_no, line in enumerate(code.splitlines(), 1):
        for m in re.finditer(r"\\begin\{(\w+)\}", line):
            stack.append((line_no, m.group(1)))
        for m in re.finditer(r"\\end\{(\w+)\}", line):
            env = m.group(1)
            if not stack:
                issues.append(Issue(
                    Severity.ERROR, line_no,
                    f"`\\end{{{env}}}` không có `\\begin` tương ứng",
                    "begin_end_pairs",
                ))
                continue
            open_line, open_env = stack[-1]
            if open_env != env:
                issues.append(Issue(
                    Severity.ERROR, line_no,
                    f"`\\end{{{env}}}` không khớp với `\\begin{{{open_env}}}` "
                    f"ở dòng {open_line}",
                    "begin_end_pairs",
                ))
            else:
                stack.pop()
    for open_line, open_env in stack:
        issues.append(Issue(
            Severity.ERROR, open_line,
            f"`\\begin{{{open_env}}}` không có `\\end` tương ứng",
            "begin_end_pairs",
        ))
    return issues


def _check_tikzpicture_present(code: str) -> list[Issue]:
    """Phải có ít nhất 1 \\begin{tikzpicture} (hoặc tkz-tab bare, hoặc tabular)."""
    if "\\begin{tikzpicture}" in code:
        return []
    if "\\tkzTabInit" in code:
        # tkz-tab bare — pipeline khác sẽ wrap, OK
        return []
    if "\\begin{tabular}" in code:
        return []
    return [Issue(
        Severity.ERROR, 0,
        "Code không có `\\begin{tikzpicture}` hoặc `\\begin{tabular}` — thiếu khối chính",
        "tikzpicture_present",
    )]


def _check_pgfplots_y_variable(code: str) -> list[Issue]:
    """Bug phổ biến: dùng `y` làm biến tự do của \\addplot — pgfplots báo lỗi
    'Sorry, you can't use 'y' in this context'. Phải dùng `variable=\\t`."""
    issues = []
    for line_no, line in enumerate(code.splitlines(), 1):
        # Match \addplot[...] (...,y) hoặc \addplot[...] (y,...)
        # Heuristic: parametric không có variable= và có y trong biểu thức
        if "\\addplot" in line and "(" in line:
            if "variable=" not in line and re.search(r"\([^)]*\by\b[^)]*\)", line):
                issues.append(Issue(
                    Severity.WARNING, line_no,
                    "PGFPlots: dùng `y` làm biến tự do — phải khai báo "
                    "`variable=\\t` và dùng `\\t` thay `y`",
                    "pgfplots_y_variable", fixable=False,
                ))
    return issues


def _check_implicit_multiplication(code: str) -> list[Issue]:
    """`\\addplot {2x}` — phải là `2*x`. Heuristic phát hiện trong biểu thức."""
    issues = []
    for line_no, line in enumerate(code.splitlines(), 1):
        if "\\addplot" in line:
            # Tìm biểu thức trong {...}
            for m in re.finditer(r"\{([^{}]+)\}", line):
                expr = m.group(1)
                # Pattern: digit theo sau là chữ (e.g. 2x, 3y) — nhưng NOT 2pt, 2cm
                if re.search(r"\b\d+[a-z]\b", expr) and not re.search(
                    r"\b\d+(pt|cm|mm|in|em|ex)\b", expr,
                ):
                    issues.append(Issue(
                        Severity.WARNING, line_no,
                        f"PGFPlots biểu thức `{expr[:30]}` thiếu `*` "
                        f"(VD: `2x` → `2*x`)",
                        "implicit_multiplication", fixable=True,
                    ))
                    break
    return issues


def _check_addplot_in_axis(code: str) -> list[Issue]:
    """\\addplot phải nằm trong \\begin{axis}...\\end{axis}."""
    issues = []
    in_axis = 0
    for line_no, line in enumerate(code.splitlines(), 1):
        if "\\begin{axis}" in line or "\\begin{semilogxaxis}" in line \
                or "\\begin{semilogyaxis}" in line or "\\begin{loglogaxis}" in line:
            in_axis += 1
        if "\\end{axis}" in line or "\\end{semilogxaxis}" in line \
                or "\\end{semilogyaxis}" in line or "\\end{loglogaxis}" in line:
            in_axis -= 1
        if in_axis <= 0 and "\\addplot" in line:
            issues.append(Issue(
                Severity.ERROR, line_no,
                "`\\addplot` phải nằm trong `\\begin{axis}...\\end{axis}`",
                "addplot_in_axis",
            ))
    return issues


def _check_unicode_math_outside_dollar(code: str) -> list[Issue]:
    """Ký hiệu Unicode toán (², √, ≠, π, ∫…) ngoài $...$ → render xấu."""
    issues = []
    unicode_math = "²³√≠≤≥πα∫∑∞×÷±"
    for line_no, line in enumerate(code.splitlines(), 1):
        # Bỏ phần sau %
        line_no_comment = re.split(r"(?<!\\)%", line, 1)[0]
        # Đếm $ — chia thành các đoạn ngoài $$
        in_math = False
        outside = []
        cur = []
        for ch in line_no_comment:
            if ch == "$":
                in_math = not in_math
                if not in_math and cur:
                    cur = []
            elif not in_math:
                cur.append(ch)
                outside.append(ch)
        outside_str = "".join(outside)
        for ch in unicode_math:
            if ch in outside_str:
                issues.append(Issue(
                    Severity.INFO, line_no,
                    f"Ký hiệu Unicode `{ch}` ngoài $...$ — nên dùng LaTeX command "
                    f"(VD: `²` → `$^2$`, `π` → `$\\pi$`)",
                    "unicode_math_outside_dollar", fixable=False,
                ))
                break
    return issues


def _check_documentclass_present(code: str) -> list[Issue]:
    """User KHÔNG nên kèm \\documentclass — app tự thêm."""
    if "\\documentclass" in code:
        for line_no, line in enumerate(code.splitlines(), 1):
            if "\\documentclass" in line:
                return [Issue(
                    Severity.WARNING, line_no,
                    "Code có `\\documentclass` — app tự thêm; bạn nên xoá để "
                    "tránh xung đột",
                    "documentclass_present", fixable=True,
                )]
    return []


_FOREACH_VARIABLES_RE = re.compile(
    r"\\foreach\s+(?P<variables>"
    r"(?:\\[A-Za-z@][A-Za-z0-9@]*\s*/\s*)*"
    r"\\[A-Za-z@][A-Za-z0-9@]*"
    r")\s+in\s*\{"
)

_FOREACH_DIGIT_WORDS = {
    "0": "Zero", "1": "One", "2": "Two", "3": "Three", "4": "Four",
    "5": "Five", "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine",
}


def _foreach_variable_names(variables: str) -> list[str]:
    return re.findall(r"\\([A-Za-z@][A-Za-z0-9@]*)", variables)


def _foreach_variable_replacements(variables: str) -> dict[str, str]:
    """Build safe names for ``\\foreach`` variables that TeX cannot define."""
    replacements: dict[str, str] = {}
    for name in _foreach_variable_names(variables):
        if name == "text":
            replacements[rf"\{name}"] = r"\tikzforeachlabel"
        elif any(char.isdigit() for char in name):
            suffix = "".join(_FOREACH_DIGIT_WORDS.get(char, char) for char in name)
            replacements[rf"\{name}"] = rf"\tikzforeach{suffix}"
    return replacements


def _check_reserved_foreach_variables(code: str) -> list[Issue]:
    """Catch loop variables that overwrite LaTeX commands or contain digits."""
    issues = []
    for match in _FOREACH_VARIABLES_RE.finditer(code):
        variables = match.group("variables")
        line_no = code.count("\n", 0, match.start("variables")) + 1
        replacements = _foreach_variable_replacements(variables)
        if r"\text" in replacements:
            issues.append(Issue(
                Severity.ERROR,
                line_no,
                "`\\text` la lenh LaTeX co san, khong the dung lam bien `\\foreach`; "
                "hay doi thanh `\\tikzforeachlabel`.",
                "reserved_foreach_variable",
                fixable=True,
            ))
        digit_variables = [
            name for name in _foreach_variable_names(variables)
            if any(char.isdigit() for char in name)
        ]
        if digit_variables:
            display_names = ", ".join(rf"\{name}" for name in digit_variables)
            issues.append(Issue(
                Severity.ERROR,
                line_no,
                f"Bien `\\foreach` {display_names} co chu so sau dau `\\`; "
                "hay dung ten chi gom chu cai.",
                "invalid_foreach_variable_name",
                fixable=True,
            ))
    return issues


def _check_balanced_delimiters(code: str) -> list[Issue]:
    """Check (), [] balance in non-comment code as a TikZ-friendly hint.
    Bỏ qua nội dung bên trong {...} để tránh báo lỗi sai với các công thức toán
    học (ví dụ: khoảng nửa mở `[0, 1)`, hoặc lệnh `\\left[...\\right)`).
    """
    issues = []
    pairs = {"(": ")", "[": "]"}
    counters = {key: 0 for key in pairs}
    first_open_line = {key: 0 for key in pairs}
    
    # 1. Strip comments first
    lines = []
    for line in code.splitlines():
        clean_line = re.split(r"(?<!\\)%", line, maxsplit=1)[0]
        lines.append(clean_line)
    
    clean_code = "\n".join(lines)
    
    # 2. Mask contents inside {...}
    masked_chars = []
    depth = 0
    for ch in clean_code:
        if ch == "{":
            if depth == 0:
                masked_chars.append(ch)
            else:
                masked_chars.append(" ")
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                masked_chars.append(ch)
            else:
                masked_chars.append(" ")
            if depth < 0:
                depth = 0
        elif depth > 0:
            if ch == "\n":
                masked_chars.append(ch)
            else:
                masked_chars.append(" ")
        else:
            masked_chars.append(ch)
            
    masked_code = "".join(masked_chars)
    
    # 3. Check balance on masked code
    for line_no, line in enumerate(masked_code.splitlines(), 1):
        for ch in line:
            if ch in pairs:
                counters[ch] += 1
                first_open_line[ch] = first_open_line[ch] or line_no
            elif ch in pairs.values():
                opener = next(k for k, v in pairs.items() if v == ch)
                counters[opener] -= 1
                if counters[opener] < 0:
                    issues.append(Issue(
                        Severity.ERROR,
                        line_no,
                        f"Thừa `{ch}` — đóng ngoặc trước khi mở `{opener}`",
                        "balanced_delimiters",
                    ))
                    counters[opener] = 0
                    
    for opener, count in counters.items():
        if count > 0:
            issues.append(Issue(
                Severity.ERROR,
                first_open_line.get(opener) or 0,
                f"Thiếu {count} dấu `{pairs[opener]}` — chưa đóng `{opener}`",
                "balanced_delimiters",
            ))
    return issues


def _check_likely_missing_semicolon(code: str) -> list[Issue]:
    """Catch common one-line TikZ commands that forgot the trailing semicolon."""
    issues = []
    command_re = re.compile(r"^\s*\\(draw|node|coordinate|fill|path|addplot)\b")
    for line_no, line in enumerate(code.splitlines(), 1):
        clean = re.split(r"(?<!\\)%", line, 1)[0].strip()
        if not clean or not command_re.search(clean):
            continue
        if clean.endswith((";", "{", ",")) or clean.startswith(r"\path"):
            continue
        if "\\foreach" in clean or clean.endswith("}"):
            continue
        issues.append(Issue(
            Severity.WARNING,
            line_no,
            "Có thể thiếu dấu `;` cuối lệnh TikZ",
            "missing_semicolon",
            fixable=False,
        ))
    return issues


def _check_tkz_tab_commands(code: str) -> list[Issue]:
    """Phát hiện lệnh sai phổ biến trong tkz-tab (vd: \\tkzTabVector thay vì \\tkzTabVar)."""
    issues = []
    invalid_var_re = re.compile(r"\\tkzTab(?:Vector|Variation|Vectors)\b")
    for line_no, line in enumerate(code.splitlines(), 1):
        clean = re.split(r"(?<!\\)%", line, 1)[0]
        m = invalid_var_re.search(clean)
        if m:
            cmd = m.group(0)
            issues.append(Issue(
                Severity.ERROR,
                line_no,
                f"Lệnh `{cmd}` không tồn tại trong gói tkz-tab — lệnh đúng là `\\tkzTabVar`",
                "invalid_tkztab_command",
                fixable=True,
            ))
    return issues


def _check_forbidden_line_cap(code: str) -> list[Issue]:
    """Phát hiện `line cap=round` — quy tắc TikZ cấm dùng thuộc tính này."""
    issues = []
    line_cap_re = re.compile(r"\bline\s+cap\s*=\s*round\b", re.IGNORECASE)
    for line_no, line in enumerate(code.splitlines(), 1):
        clean = re.split(r"(?<!\\)%", line, 1)[0]
        if line_cap_re.search(clean):
            issues.append(Issue(
                Severity.WARNING,
                line_no,
                "Phát hiện `line cap=round` — chuẩn vẽ TikZ cấm dùng thuộc tính này vì gây mất nét chuẩn",
                "forbidden_line_cap",
                fixable=True,
            ))
    return issues


def _check_legacy_patterns(code: str) -> list[Issue]:
    """Phát hiện pattern cũ (north west/east lines) thay vì patterns.meta chuẩn Thầy Đỗ Minh."""
    issues = []
    legacy_pat_re = re.compile(r"\bpattern\s*=\s*north\s*(?:west|east)\s*lines\b", re.IGNORECASE)
    for line_no, line in enumerate(code.splitlines(), 1):
        clean = re.split(r"(?<!\\)%", line, 1)[0]
        if legacy_pat_re.search(clean):
            issues.append(Issue(
                Severity.INFO,
                line_no,
                "Khuyến nghị dùng `patterns.meta` (Lines[angle=45, distance=4pt, line width=0.3pt]) thay vì pattern cũ",
                "legacy_pattern",
                fixable=True,
            ))
    return issues


def _check_tkz_tab_var_style(code: str) -> list[Issue]:
    """Khuyến nghị vẽ mũi tên thủ công thay vì \\tkzTabVar theo chuẩn TikZ AI Skill."""
    issues = []
    for line_no, line in enumerate(code.splitlines(), 1):
        clean = re.split(r"(?<!\\)%", line, 1)[0]
        if r"\tkzTabVar" in clean:
            issues.append(Issue(
                Severity.INFO,
                line_no,
                "Gợi ý: Dùng path + draw[-Stealth] để vẽ mũi tên BBT tùy biến tọa độ thay cho `\\tkzTabVar`",
                "tkz_tab_var_style",
                fixable=False,
            ))
    return issues


_RULES = [
    _check_balanced_braces,
    _check_balanced_delimiters,
    _check_begin_end_pairs,
    _check_tikzpicture_present,
    _check_pgfplots_y_variable,
    _check_implicit_multiplication,
    _check_addplot_in_axis,
    _check_unicode_math_outside_dollar,
    _check_documentclass_present,
    _check_reserved_foreach_variables,
    _check_likely_missing_semicolon,
    _check_tkz_tab_commands,
    _check_forbidden_line_cap,
    _check_legacy_patterns,
    _check_tkz_tab_var_style,
]


# ══════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════

def check(code: str) -> list[Issue]:
    """Chạy tất cả rules, trả list issues sorted theo (severity, line)."""
    if not code or not code.strip():
        return [Issue(Severity.ERROR, 0, "Code TikZ rỗng", "empty")]
    issues: list[Issue] = []
    for rule in _RULES:
        try:
            issues.extend(rule(code))
        except Exception as e:
            issues.append(Issue(
                Severity.WARNING, 0,
                f"Rule {rule.__name__} lỗi: {e}", "rule_error",
            ))
    sev_order = {Severity.ERROR: 0, Severity.WARNING: 1, Severity.INFO: 2}
    issues.sort(key=lambda i: (sev_order[i.severity], i.line))
    return issues


def has_blocking_errors(code: str) -> bool:
    """True nếu có ít nhất 1 issue ERROR — pdflatex sẽ fail chắc chắn."""
    return any(i.severity == Severity.ERROR for i in check(code))


def auto_fix(code: str) -> str:
    """Apply các quick fix tự động (chỉ những issue `fixable=True`).
    Best-effort — không thay đổi code nếu không chắc chắn."""
    fixed = code

    # Fix 1: bỏ \documentclass (và đoạn preamble) nếu có
    if "\\documentclass" in fixed:
        # Tìm \begin{document} → giữ phần sau
        m = re.search(r"\\begin\{document\}\s*", fixed)
        if m:
            fixed = fixed[m.end():]
        m = re.search(r"\\end\{document\}\s*$", fixed)
        if m:
            fixed = fixed[:m.start()]
        fixed = fixed.strip()

    # Fix 2: implicit multiplication trong \addplot (chỉ digit-letter cơ bản)
    def _fix_mult(match):
        expr = match.group(1)
        # Thêm * giữa digit và letter, tránh đơn vị (pt, cm, etc.)
        new_expr = re.sub(
            r"(\d)([a-z])",
            lambda m: m.group(0) if m.group(2) in "pcmi" else f"{m.group(1)}*{m.group(2)}",
            expr,
        )
        return "{" + new_expr + "}"

    fixed = re.sub(
        r"(\\addplot[^{]*?)\{([^{}]+)\}",
        lambda m: m.group(1) + "{" + re.sub(
            r"(\d)([a-z])",
            lambda m2: m2.group(0) if m2.group(2) in "pcmi" else f"{m2.group(1)}*{m2.group(2)}",
            m.group(2),
        ) + "}",
        fixed,
    )

    # Fix 3: repair invalid ``\\foreach`` variable names and their bare uses.
    fixed = _fix_invalid_foreach_variables(fixed)

    # Fix 4: tkz-tab invalid variation command typos (vd: \tkzTabVector -> \tkzTabVar)
    fixed = re.sub(r"\\tkzTab(?:Vector|Variation|Vectors)\b", r"\\tkzTabVar", fixed)

    # Fix 5: remove forbidden line cap=round (quy tắc Thầy Đỗ Minh)
    fixed = re.sub(r",\s*line\s+cap\s*=\s*round", "", fixed, flags=re.IGNORECASE)
    fixed = re.sub(r"line\s+cap\s*=\s*round\s*,\s*", "", fixed, flags=re.IGNORECASE)
    fixed = re.sub(r"\bline\s+cap\s*=\s*round\b", "", fixed, flags=re.IGNORECASE)

    # Fix 6: modernize legacy patterns to patterns.meta (Lines[angle=..., distance=4pt, line width=0.3pt])
    fixed = re.sub(
        r"\bpattern\s*=\s*north\s*west\s*lines\b",
        r"pattern={Lines[angle=45, distance=4pt, line width=0.3pt]}",
        fixed,
        flags=re.IGNORECASE,
    )
    fixed = re.sub(
        r"\bpattern\s*=\s*north\s*east\s*lines\b",
        r"pattern={Lines[angle=135, distance=4pt, line width=0.3pt]}",
        fixed,
        flags=re.IGNORECASE,
    )
    # Tùy chỉnh màu pattern sang gray!70 nếu dùng black
    fixed = re.sub(
        r"\bpattern\s+color\s*=\s*black(!70)?\b",
        r"pattern color=gray!70",
        fixed,
        flags=re.IGNORECASE,
    )

    return fixed


def _find_matching_brace(code: str, open_index: int) -> Optional[int]:
    """Return the closing brace matching ``open_index``."""
    depth = 0
    index = open_index
    while index < len(code):
        char = code[index]
        if char == "\\":
            index += 2
            continue
        if char == "%":
            newline = code.find("\n", index + 1)
            index = len(code) if newline < 0 else newline + 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _fix_invalid_foreach_variables(code: str) -> str:
    """Rename invalid ``\\foreach`` variables only within their own loop."""
    parts: list[str] = []
    cursor = 0
    search_from = 0
    while True:
        match = _FOREACH_VARIABLES_RE.search(code, search_from)
        if not match:
            parts.append(code[cursor:])
            return "".join(parts)

        variables = match.group("variables")
        replacements = _foreach_variable_replacements(variables)
        if not replacements:
            search_from = match.end()
            continue

        items_open = match.end() - 1
        items_close = _find_matching_brace(code, items_open)
        if items_close is None:
            search_from = match.end()
            continue
        body_open = items_close + 1
        while body_open < len(code) and code[body_open].isspace():
            body_open += 1
        if body_open >= len(code) or code[body_open] != "{":
            search_from = match.end()
            continue
        body_close = _find_matching_brace(code, body_open)
        if body_close is None:
            search_from = match.end()
            continue

        renamed_variables = variables
        for original, replacement in replacements.items():
            renamed_variables = re.sub(
                re.escape(original) + r"(?![A-Za-z0-9@])",
                lambda _match, value=replacement: value,
                renamed_variables,
            )
        body = code[body_open + 1:body_close]
        renamed_body = body
        for original, replacement in replacements.items():
            if original == r"\text":
                pattern = r"\\text(?![A-Za-z@]|\s*\{)"
            else:
                pattern = re.escape(original) + r"(?![A-Za-z0-9@])"
            renamed_body = re.sub(
                pattern,
                lambda _match, value=replacement: value,
                renamed_body,
            )
        parts.extend((
            code[cursor:match.start()],
            code[match.start():match.start("variables")],
            renamed_variables,
            code[match.end("variables"):body_open + 1],
            renamed_body,
            "}",
        ))
        cursor = body_close + 1
        search_from = cursor


def format_issues(issues: list[Issue]) -> str:
    """Format issues thành text đẹp để hiện trên console."""
    if not issues:
        return "  ✓ Pre-flight check OK — không có vấn đề."
    lines = [f"Pre-flight check phát hiện {len(issues)} vấn đề:"]
    icon = {Severity.ERROR: "❌", Severity.WARNING: "⚠", Severity.INFO: "ℹ"}
    for i in issues:
        prefix = f"  {icon[i.severity]} "
        if i.line > 0:
            prefix += f"L{i.line}: "
        suffix = "  [auto-fixable]" if i.fixable else ""
        lines.append(f"{prefix}{i.message}{suffix}")
    return "\n".join(lines)


def explain_render_error(error_text: str, code: str = "") -> str:
    """Turn raw LaTeX/render errors into a concise user-facing diagnosis."""
    raw = (error_text or "").strip()
    if not raw:
        return "Không nhận được log lỗi. Hãy kiểm tra LaTeX engine và thử render lại."

    lower = raw.lower()
    details: list[str] = []

    if "không tìm thấy latex engine" in lower or "latex engine" in lower and "không tìm thấy" in lower:
        details.append(
            "Nguyên nhân: máy chưa cài hoặc chưa cấu hình LaTeX engine trong PATH "
            "(pdflatex/xelatex/tectonic)."
        )
        details.append("Cách xử lý: cài MiKTeX hoặc TeX Live, rồi mở lại app.")
    if "không thể chuyển pdf sang png" in lower or "pymupdf" in lower or "pdftoppm" in lower:
        details.append(
            "Nguyên nhân: đã biên dịch PDF nhưng thiếu thư viện chuyển PDF sang ảnh "
            "(PyMuPDF/fitz hoặc pdftoppm)."
        )
        details.append("Cách xử lý: cài PyMuPDF hoặc Poppler/pdftoppm.")

    missing_pkg = re.search(r"LaTeX Error:\s*File [`']([^`']+)[`'] not found", raw)
    if missing_pkg:
        details.append(f"Nguyên nhân: thiếu gói/file LaTeX `{missing_pkg.group(1)}`.")
        details.append("Cách xử lý: mở MiKTeX Console/TeX Live để cài package còn thiếu.")

    undefined_env = re.search(r"LaTeX Error:\s*Environment\s+([^\s]+)\s+undefined", raw)
    if undefined_env:
        details.append(f"Nguyên nhân: môi trường `{undefined_env.group(1)}` chưa được hỗ trợ hoặc thiếu package.")

    if "undefined control sequence" in lower:
        details.append(
            "Nguyên nhân: có lệnh LaTeX/TikZ chưa được định nghĩa "
            "(thường do gõ sai lệnh hoặc thiếu thư viện/package)."
        )
    if "missing } inserted" in lower or "runaway argument" in lower:
        details.append("Nguyên nhân: khả năng cao thiếu dấu `}` hoặc đóng ngoặc sai.")
    if "extra }" in lower:
        details.append("Nguyên nhân: thừa dấu `}` hoặc đóng nhóm quá sớm.")
    if "pgfkeys error" in lower:
        details.append("Nguyên nhân: key/style TikZ hoặc pgfplots không hợp lệ.")
    if "i can't find file" in lower or "cannot find" in lower and "figure.tex" in lower:
        details.append("Nguyên nhân: LaTeX engine không đọc được file tạm hoặc cấu hình PATH bị lỗi.")

    line_match = re.search(r"\bl\.(\d+)\s+(.+)", raw)
    if line_match:
        line_no = int(line_match.group(1))
        details.append(f"Log chỉ tới dòng LaTeX l.{line_no}: {line_match.group(2).strip()[:160]}")
        if code:
            code_lines = code.splitlines()
            if 1 <= line_no <= len(code_lines):
                details.append(f"Dòng code tương ứng: {code_lines[line_no - 1].strip()[:180]}")

    bang_line = next((line.strip() for line in raw.splitlines() if line.strip().startswith("!")), "")
    if bang_line:
        details.append(f"Thông báo gốc: {bang_line[:220]}")

    if not details:
        details.append("LaTeX báo lỗi nhưng chưa nhận diện được mẫu lỗi phổ biến.")
        details.append("Xem log gốc bên dưới để biết lệnh/dòng gây lỗi.")

    tail = "\n".join(raw.splitlines()[-12:])
    return "\n".join(details + ["", "Log gốc (rút gọn):", tail[:1200]])
