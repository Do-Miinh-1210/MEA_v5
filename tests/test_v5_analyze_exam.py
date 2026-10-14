"""Guard rails for the V5 analyse-exam-to-matrix workflow."""
from __future__ import annotations

from core.exam_parser import ExamPaper
from v5.analyze_exam import (
    build_ai_matrix_prompt,
    matrix_from_exam_file,
    parse_ai_matrix_response,
)


def test_parse_ai_matrix_response_normalizes_fenced_json():
    raw = """```json
{
  "title": "Đề thử",
  "time_str": "45 phút",
  "rows": [
    {
      "stt": "1",
      "topic": "Hàm số",
      "level": "VDC",
      "qtype": "TN",
      "requirement": "Vận dụng hàm số",
      "points": "0.25"
    },
    {"topic": "Tích phân", "qtype": "TLN"}
  ]
}
```"""

    matrix = parse_ai_matrix_response(raw)

    assert matrix.title == "Đề thử"
    assert matrix.time_str == "45 phút"
    assert len(matrix.rows) == 2
    assert matrix.rows[0].level == "VD"
    assert matrix.rows[0].codes == ["TN1"]
    assert matrix.rows[0].points == 0.25
    assert matrix.rows[1].qtype == "TLN"
    assert matrix.rows[1].codes == ["TLN2"]
    assert matrix.rows[1].points == 0.5


def test_build_ai_matrix_prompt_contains_extracted_questions():
    paper = ExamPaper.from_raw_text(
        "Câu 1. Nhận biết\n"
        "Cho hàm số f(x)=x^2.\n"
        "A. 1\nB. 2\nC. 3\nD. 4\n\n"
        "Câu 2. Vận dụng\n"
        "Tính tích phân của hàm số đã cho."
    )

    prompt = build_ai_matrix_prompt(paper)

    assert '"rows"' in prompt
    assert "NB|TH|VD" in prompt
    assert "Câu 1" in prompt
    assert "Cho hàm số" in prompt
    assert "Tính tích phân" in prompt


def test_matrix_from_exam_file_supports_text_file(tmp_path):
    exam = tmp_path / "exam.txt"
    exam.write_text(
        "ĐỀ KIỂM TRA GIỮA KÌ\n\n"
        "Câu 1. Nhận biết\n"
        "Cho hàm số f(x)=x^2.\n"
        "A. 1\nB. 2\nC. 3\nD. 4\n\n"
        "Câu 2. Vận dụng tự luận\n"
        "Tính tích phân của hàm số đã cho.",
        encoding="utf-8",
    )

    raw_text, paper, matrix = matrix_from_exam_file(str(exam))

    assert "ĐỀ KIỂM TRA" in raw_text
    assert paper.title == "ĐỀ KIỂM TRA GIỮA KÌ"
    assert len(paper.raw_questions) == 2
    assert len(matrix.rows) == 2
    assert matrix.rows[1].qtype == "TL"
    assert matrix.rows[1].level == "VD"
