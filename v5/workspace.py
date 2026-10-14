"""
v5/workspace.py - Trang thai de dang lam cua MEA v5.

View trong app duoc tao lai moi khi nguoi dung dieu huong. Vi vay, de thi
hien tai phai song o cap ung dung, khong duoc gan rieng vao ExamCreateView.
Module nay khong phu thuoc UI de co the kiem thu luong restore an toan.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from core.models import ExamData, Question


Snapshotter = Callable[..., Any]


@dataclass(frozen=True)
class AddQuestionsResult:
    exam: ExamData
    added: int
    skipped: int
    created_exam: bool


class ExamWorkspace:
    """Nguon su that duy nhat cho de dang mo trong phien V5."""

    def __init__(self) -> None:
        self._exam: ExamData | None = None

    @property
    def current_exam(self) -> ExamData | None:
        return self._exam

    def set_exam(self, exam: ExamData | None) -> ExamData | None:
        self._exam = exam
        return exam

    @staticmethod
    def _question_keys(question: Question) -> set[tuple[str, ...]]:
        """Nhận diện câu đã có theo ID và theo nội dung để tránh thêm lặp."""
        keys: set[tuple[str, ...]] = set()
        qid = str(getattr(question, "question_id", "") or "").strip()
        if qid:
            keys.add(("id", qid))
        keys.add((
            "content",
            str(question.qtype or "").strip().upper(),
            str(question.topic or "").strip().lower(),
            str(question.question or "").strip(),
        ))
        return keys

    def add_questions(
        self,
        questions: list[Question],
        *,
        exam_factory: Callable[[], ExamData],
    ) -> AddQuestionsResult:
        """Thêm các câu đã chọn vào đề hiện tại, bỏ qua câu bị trùng."""
        created_exam = self._exam is None
        exam = self._exam or exam_factory()
        existing_keys: set[tuple[str, ...]] = set()
        for question in exam.questions:
            existing_keys.update(self._question_keys(question))

        added = 0
        skipped = 0
        for question in questions:
            keys = self._question_keys(question)
            if keys & existing_keys:
                skipped += 1
                continue
            copied = deepcopy(question)
            exam.questions.append(copied)
            existing_keys.update(keys)
            added += 1

        self._exam = exam
        return AddQuestionsResult(
            exam=exam,
            added=added,
            skipped=skipped,
            created_exam=created_exam,
        )

    def restore_history(
        self,
        snapshot_data: dict,
        *,
        snapshotter: Snapshotter | None = None,
    ) -> ExamData:
        """Nap snapshot history va bao toan ban dang lam truoc khi thay the."""
        if not isinstance(snapshot_data, dict):
            raise ValueError("Dữ liệu phiên bản không hợp lệ.")

        restored = ExamData.from_dict(snapshot_data)
        previous = self._exam
        if (
            snapshotter is not None
            and previous is not None
            and previous.questions
        ):
            snapshotter(
                previous,
                source="manual",
                note="V5: trước khi khôi phục lịch sử",
            )

        self._exam = restored
        return restored
