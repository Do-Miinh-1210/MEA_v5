"""Guardrails for V5 similar-exam / variant parity."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.models import ExamData, Question


ROOT = Path(__file__).resolve().parents[1]


def _sample_exam() -> ExamData:
    return ExamData(
        exam_title="Đề kiểm tra thử",
        subject="Toán",
        grade="12",
        semester="1",
        year="2026",
        time="45 phút",
        questions=[
            Question(
                qtype="TN",
                level="NB",
                topic="Phương trình",
                question="Giải phương trình: 2x + 4 = 0",
                options={"A": "x = -2", "B": "x = 2", "C": "x = 0", "D": "x = 4"},
                answer="A",
                solution="2x + 4 = 0 nên x = -2",
            )
        ],
    )


def test_sympy_variant_exam_changes_detected_question():
    pytest.importorskip("sympy")

    from services.similar_generator import make_variant_exam

    exam = _sample_exam()
    new_exam, replaced, kept = make_variant_exam(exam, seed=17)

    assert replaced == 1
    assert kept == 0
    assert new_exam is not exam
    assert new_exam.questions[0].question != exam.questions[0].question
    assert getattr(new_exam.questions[0], "_variant", False) is True


def test_ai_variant_exam_uses_json_response_without_network():
    from services.ai_variant_generator import generate_ai_variant_exam

    def fake_ai_call(prompt: str) -> str:
        assert "Giải phương trình: 2x + 4 = 0" in prompt
        return json.dumps({
            "variants": [{
                "question": "Giải phương trình: 3x + 6 = 0",
                "solution": "3x + 6 = 0 nên x = -2",
                "options": {
                    "A": "x = 2",
                    "B": "x = -2",
                    "C": "x = 0",
                    "D": "x = 6",
                },
                "answer": "B",
            }]
        }, ensure_ascii=False)

    new_exam, replaced, kept = generate_ai_variant_exam(_sample_exam(), fake_ai_call)

    assert replaced == 1
    assert kept == 0
    assert new_exam.questions[0].question == "Giải phương trình: 3x + 6 = 0"
    assert new_exam.questions[0].answer == "B"
    assert new_exam.questions[0].options["B"] == "x = -2"
    assert getattr(new_exam.questions[0], "_variant", False) is True


def test_manual_variant_prompt_is_available_for_external_chatbots():
    from services.ai_variant_generator import get_manual_variant_prompt

    prompt = get_manual_variant_prompt()

    assert "FILE WORD" in prompt
    assert "CHỈ THAY SỐ" in prompt
    assert "CHECKLIST" in prompt


def test_v5_variant_dialog_is_ctk_native_and_uses_shared_services():
    source = (ROOT / "v5" / "variant_dialog.py").read_text(encoding="utf-8")

    assert "class VariantExamDialog" in source
    assert "get_manual_variant_prompt" in source
    assert "make_variant_exam" in source
    assert "generate_ai_variant_exam" in source
    assert "from ui." not in source
    assert "import ui." not in source


def test_exam_create_exposes_variant_workflow():
    source = (ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")

    assert "_variant_btn" in source
    assert "_open_variant_dialog" in source
    assert "VariantExamDialog" in source
    assert "🧬  Đề tương tự" in source
