"""Regression tests for copy/export-ready ex_test LaTeX output."""
from __future__ import annotations

from core.latex_parser import parse_latex_text
from core.models import Question
from export.latex_exporter import (
    build_latex_document,
    export_to_latex,
    format_questions_ex_test,
)


def _questions() -> list[Question]:
    return [
        Question(
            qtype="TN",
            level="NB",
            topic="Đạo hàm",
            question="Đạo hàm của ${x^2}$ là gì?",
            options={"A": "${2x}$", "B": "${x}$", "C": "2", "D": "0"},
            answer="A",
            solution="Ta có ${\\left(x^2\\right)'=2x}$.",
        ),
        Question(
            qtype="DS",
            level="TH",
            topic="Hàm số",
            question="Xét các mệnh đề sau.",
            items={"a": "Mệnh đề a.", "b": "Mệnh đề b.", "c": "Mệnh đề c.", "d": "Mệnh đề d."},
            answers={"a": True, "b": False, "c": True, "d": False},
            item_solutions={"a": "Đúng.", "b": "Sai.", "c": "Đúng.", "d": "Sai."},
        ),
        Question(
            qtype="TLN",
            level="VD",
            topic="Số học",
            question="Tính ${2+3}$.",
            answer="5",
            solution="Kết quả bằng 5.",
        ),
        Question(
            qtype="TL",
            level="VD",
            topic="Tự luận",
            question="Chứng minh một khẳng định.",
            solution="Trình bày lời giải.",
        ),
    ]


def test_format_questions_ex_test_writes_all_supported_question_types():
    source = format_questions_ex_test(_questions())

    assert source.count(r"\begin{ex}") == 3
    assert source.count(r"\begin{bt}") == 1
    assert r"\choice" in source
    assert r"\choiceTF" in source
    assert r"\shortans{5}" in source
    assert r"{\True $2x$}" in source
    assert r"\begin{itemchoice}" in source
    assert "${" not in source


def test_ex_test_output_round_trips_through_latex_parser():
    parsed = parse_latex_text(format_questions_ex_test(_questions()))

    assert [question.qtype for question in parsed] == ["TN", "DS", "TLN", "TL"]
    assert parsed[0].answer == "A"
    assert parsed[1].answers == {"a": True, "b": False, "c": True, "d": False}
    assert parsed[2].answer == "5"


def test_export_to_latex_writes_complete_document(tmp_path):
    path = tmp_path / "convert.tex"

    source = export_to_latex(_questions(), path)

    assert source == path.read_text(encoding="utf-8")
    assert source == build_latex_document(_questions())
    assert r"\usepackage{ex_test}" in source
    assert r"\begin{document}" in source
    assert r"\end{document}" in source
