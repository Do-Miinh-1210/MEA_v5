"""Tests for mixed MatrixExamAI app blocks and LaTeX ex_test input."""
from __future__ import annotations

from core.exam_file_loader import load_exam_from_file, parse_questions_from_text
from core.pdf_to_questions import pdf_or_image_to_questions


APP_BLOCK = """===CAU===
LOAI: TN
MUCDO: NB
CHUONG: Cấu trúc app
NOIDUNG: Câu hỏi từ cấu trúc app?
A: Đáp án A
B: Đáp án B
C: Đáp án C
D: Đáp án D
DAPAN: A
LOIGIAI: Lời giải app.
===KETCAU==="""

LATEX_BLOCK = r"""\begin{ex}
Câu hỏi từ LaTeX ex_test?
\choice
{\True Đáp án A}
{Đáp án B}
{Đáp án C}
{Đáp án D}
\loigiai{Lời giải LaTeX.}
\end{ex}"""


def test_parse_questions_from_text_supports_latex_ex_test():
    questions, tier = parse_questions_from_text(LATEX_BLOCK)

    assert tier == "latex"
    assert len(questions) == 1
    assert questions[0].question == "Câu hỏi từ LaTeX ex_test?"
    assert questions[0].answer == "A"


def test_parse_questions_from_text_keeps_mixed_source_order():
    text = f"{LATEX_BLOCK}\n\n{APP_BLOCK}"

    questions, tier = parse_questions_from_text(text)

    assert tier == "mixed"
    assert len(questions) == 2
    assert questions[0].question == "Câu hỏi từ LaTeX ex_test?"
    assert questions[1].question == "Câu hỏi từ cấu trúc app?"


def test_load_tex_file_keeps_app_and_latex_questions(tmp_path):
    path = tmp_path / "mixed.tex"
    path.write_text(f"{APP_BLOCK}\n\n{LATEX_BLOCK}", encoding="utf-8")

    result = load_exam_from_file(str(path), use_cache=False)

    assert result["tier"] == "mixed"
    assert [question.question for question in result["questions"]] == [
        "Câu hỏi từ cấu trúc app?",
        "Câu hỏi từ LaTeX ex_test?",
    ]


def test_document_convert_pipeline_reads_tex_without_calling_ai(tmp_path):
    path = tmp_path / "questions.tex"
    path.write_text(LATEX_BLOCK, encoding="utf-8")

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("TeX import must not call AI")

    result = pdf_or_image_to_questions(str(path), ai_vision_call=fail_if_called)

    assert result["method"] == "document"
    assert len(result["questions"]) == 1
