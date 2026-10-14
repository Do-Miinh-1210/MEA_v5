"""Regression tests for V5 session persistence."""
from __future__ import annotations

from core.models import ExamData, Question
from v5 import session_autosave


def _exam_with_asset_slots() -> ExamData:
    return ExamData(
        exam_title="Đề NHCH",
        subject="Toán",
        grade="12",
        semester="1",
        year="2026",
        time="45 phút",
        school="THPT V5",
        teacher="Tổ Toán",
        questions=[
            Question(
                qtype="TN",
                level="TH",
                topic="Đồ thị",
                question="Chọn đồ thị đúng.",
                options={"A": "Hình A", "B": "Hình B"},
                answer="A",
                question_image="question.png",
                option_images={"A": "option-a.png"},
                solution_image="solution.png",
                tikz_code="\\begin{tikzpicture}\\end{tikzpicture}",
                question_id="BANK-ASSET-01",
            )
        ],
    )


def test_session_save_is_readable_and_preserves_question_assets(monkeypatch, tmp_path):
    session_file = tmp_path / "v5_session.json"
    monkeypatch.setattr(session_autosave, "_FILE", session_file)

    assert session_autosave.save_now(_exam_with_asset_slots()) is True
    data = session_autosave.load_session()
    restored = session_autosave._dict_to_exam(data)

    question = restored.questions[0]
    assert question.question_image == "question.png"
    assert question.option_images == {"A": "option-a.png"}
    assert question.solution_image == "solution.png"
    assert "tikzpicture" in question.tikz_code
    assert restored.school == "THPT V5"
    assert restored.teacher == "Tổ Toán"
    assert list(tmp_path.glob("*.tmp")) == []


def test_examdata_dict_preserves_word_header_metadata():
    exam = _exam_with_asset_slots()
    restored = ExamData.from_dict(exam.to_dict())

    assert restored.school == "THPT V5"
    assert restored.teacher == "Tổ Toán"
