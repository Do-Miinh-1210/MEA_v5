"""Export Question objects to Vietnamese ``ex_test`` LaTeX structures.

The block formatter is intended for clipboard workflows, while
``export_to_latex`` writes a complete ``.tex`` document that can be opened in
an existing ex_test-enabled LaTeX environment.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable


_MATH_OR_TIKZ_RE = re.compile(
    r"(\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}|\$.*?\$)",
    re.DOTALL,
)


def _to_latex_text(value: Any) -> str:
    """Normalize app math delimiters and escape common plain-text separators."""
    text = "" if value is None else str(value)
    text = re.sub(r"\$\{(.*?)\}\$", r"$\1$", text, flags=re.DOTALL)

    parts = _MATH_OR_TIKZ_RE.split(text)
    out: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("$") or part.startswith(r"\begin{tikzpicture}"):
            out.append(part)
            continue
        part = re.sub(r"(?<!\\)%", r"\%", part)
        part = re.sub(r"(?<!\\)&", r"\&", part)
        out.append(part)
    return "".join(out).strip()


def _structured_question_id(question: Any) -> str:
    question_id = str(getattr(question, "question_id", "") or "").strip()
    if not question_id or question_id.startswith("QID-"):
        return ""
    return question_id


def _solution_text(question: Any) -> str:
    qtype = str(getattr(question, "qtype", "") or "").upper()
    item_solutions = getattr(question, "item_solutions", {}) or {}
    if qtype == "DS" and item_solutions:
        lines = [r"\begin{itemchoice}"]
        for key in "abcd":
            value = _to_latex_text(item_solutions.get(key, ""))
            if value:
                lines.append(r"\itemch " + value)
        lines.append(r"\end{itemchoice}")
        if len(lines) > 2:
            return "\n".join(lines)
    return _to_latex_text(getattr(question, "solution", ""))


def question_to_ex_test(
    question: Any,
    *,
    include_solution: bool = True,
    include_id: bool = True,
    stt: int = 0,
) -> str:
    """Convert one Question-like object to an ``ex_test`` question block.

    Args:
        stt: Số thứ tự câu (1-based). Nếu 0, không thêm comment header.
    """
    qtype = str(getattr(question, "qtype", "") or "").upper()
    level = str(getattr(question, "level", "") or "").strip()
    topic = str(getattr(question, "topic", "") or "").strip()

    env = "bt" if qtype == "TL" else "ex"
    lines: list[str] = []

    # ── Comment header: % Câu N [Mức độ]_[Chủ đề] ──────────────────────────
    if stt > 0:
        level_part = f"[{level}]" if level else ""
        topic_part = f"_[{topic}]" if topic else ""
        if level_part or topic_part:
            lines.append(f"% Câu {stt} {level_part}{topic_part}")

    lines.append(rf"\begin{{{env}}}")

    question_id = _structured_question_id(question)
    if include_id and question_id:
        lines.append(f"%[{question_id}]")

    question_text = _to_latex_text(getattr(question, "question", ""))
    if question_text:
        lines.append(question_text)

    if qtype == "TN":
        options = getattr(question, "options", {}) or {}
        answer = str(getattr(question, "answer", "") or "").strip().upper()
        lines.append(r"\choice")
        for key in "ABCD":
            value = _to_latex_text(options.get(key, ""))
            marker = r"\True " if key == answer else ""
            lines.append("{" + marker + value + "}")

    elif qtype == "DS":
        items = getattr(question, "items", {}) or {}
        answers = getattr(question, "answers", {}) or {}
        lines.append(r"\choiceTF")
        for key in "abcd":
            value = _to_latex_text(items.get(key, ""))
            marker = r"\True " if bool(answers.get(key, False)) else ""
            lines.append("{" + marker + value + "}")

    elif qtype == "TLN":
        answer = _to_latex_text(getattr(question, "answer", ""))
        lines.append(r"\shortans{" + answer + "}")

    if include_solution:
        solution = _solution_text(question)
        if solution:
            lines.extend([r"\loigiai{", solution, "}"])

    lines.append(rf"\end{{{env}}}")
    return "\n".join(lines)



def format_questions_ex_test(
    questions: Iterable[Any],
    *,
    include_solution: bool = True,
    include_id: bool = True,
    start_stt: int = 1,
) -> str:
    """Format multiple questions as copy-ready ``ex_test`` blocks.

    Args:
        start_stt: Số thứ tự bắt đầu (mặc định 1). Truyền 0 để tắt comment header.
    """
    blocks: list[str] = []
    for i, question in enumerate(questions):
        stt = (start_stt + i) if start_stt > 0 else 0
        blocks.append(question_to_ex_test(
            question,
            include_solution=include_solution,
            include_id=include_id,
            stt=stt,
        ))
    return "\n\n".join(blocks)


LATEX_DOCUMENT_TEMPLATE = r"""\documentclass[12pt,a4paper]{article}
\usepackage{iftex}
\ifPDFTeX
  \usepackage[utf8]{inputenc}
  \usepackage[T5]{fontenc}
\fi
\usepackage[vietnamese]{babel}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{tikz,pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{ex_test}

\begin{document}
%(content)s
\end{document}
"""


def build_latex_document(
    questions: Iterable[Any],
    *,
    include_solution: bool = True,
    include_id: bool = True,
) -> str:
    """Build a complete LaTeX document containing ``ex_test`` blocks."""
    content = format_questions_ex_test(
        questions,
        include_solution=include_solution,
        include_id=include_id,
    )
    return LATEX_DOCUMENT_TEMPLATE % {"content": content}


def export_to_latex(
    exam_or_questions: Any,
    path: str | Path,
    *,
    include_solution: bool = True,
    include_id: bool = True,
    full_document: bool = True,
) -> str:
    """Write questions to ``path`` and return the exported source."""
    questions = getattr(exam_or_questions, "questions", exam_or_questions)
    if full_document:
        source = build_latex_document(
            questions,
            include_solution=include_solution,
            include_id=include_id,
        )
    else:
        source = format_questions_ex_test(
            questions,
            include_solution=include_solution,
            include_id=include_id,
        )
    Path(path).write_text(source, encoding="utf-8")
    return source
