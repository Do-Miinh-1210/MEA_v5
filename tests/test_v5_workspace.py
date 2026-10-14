"""Unit tests cho state holder cua workflow V5."""
from __future__ import annotations

from core.models import ExamData, Question
from v5.workspace import ExamWorkspace


def _exam(title: str, question: str) -> ExamData:
    return ExamData(
        exam_title=title,
        subject="Toán",
        grade="12",
        semester="1",
        year="2026",
        time="90 phút",
        questions=[
            Question(
                qtype="TN",
                level="NB",
                topic="Đạo hàm",
                question=question,
                options={"A": "1", "B": "2"},
                answer="A",
                points=0.25,
            )
        ],
    )


def _blank_exam(title: str) -> ExamData:
    return ExamData(
        exam_title=title,
        subject="Toán",
        grade="12",
        semester="1",
        year="2026",
        time="90 phút",
        questions=[],
    )


def test_workspace_keeps_current_exam_outside_a_view():
    workspace = ExamWorkspace()
    current = _exam("Đề đang làm", "Câu hiện tại?")

    workspace.set_exam(current)

    assert workspace.current_exam is current
    assert workspace.current_exam.questions[0].question == "Câu hiện tại?"


def test_history_restore_snapshots_current_exam_before_replacing_it():
    workspace = ExamWorkspace()
    current = _exam("Đề đang làm", "Câu hiện tại?")
    previous_version = _exam("Đề cũ", "Câu từ history?")
    saved: list[tuple[ExamData, str, str]] = []

    def _snapshot(exam, *, source: str, note: str):
        saved.append((exam, source, note))

    workspace.set_exam(current)
    restored = workspace.restore_history(
        previous_version.to_dict(), snapshotter=_snapshot)

    assert saved == [(current, "manual", "V5: trước khi khôi phục lịch sử")]
    assert workspace.current_exam is restored
    assert restored.exam_title == "Đề cũ"
    assert restored.questions[0].question == "Câu từ history?"


def test_history_restore_without_current_exam_does_not_create_snapshot():
    workspace = ExamWorkspace()
    saved: list[ExamData] = []

    restored = workspace.restore_history(
        _exam("Đề cũ", "Câu từ history?").to_dict(),
        snapshotter=lambda exam, **_: saved.append(exam),
    )

    assert restored.exam_title == "Đề cũ"
    assert saved == []


def test_add_questions_creates_draft_exam_and_skips_duplicates():
    workspace = ExamWorkspace()
    selected = _exam("Nguồn", "Câu chọn từ NHCH?").questions[0]

    result = workspace.add_questions(
        [selected, selected],
        exam_factory=lambda: _blank_exam("Đề nháp"),
    )

    assert result.created_exam is True
    assert result.added == 1
    assert result.skipped == 1
    assert len(result.exam.questions) == 1


def test_add_questions_appends_to_current_exam_without_mutating_source():
    workspace = ExamWorkspace()
    current = _exam("Đề đang làm", "Câu hiện tại?")
    selected = _exam("Nguồn", "Câu chọn từ NHCH?").questions[0]
    workspace.set_exam(current)

    result = workspace.add_questions(
        [selected], exam_factory=lambda: _blank_exam("Không dùng"))

    assert result.created_exam is False
    assert result.added == 1
    assert result.exam is current
    assert result.exam.questions[-1] is not selected
