"""Shared exam-level TikZ -> EMF workflow for the V4 and V5 desktop UIs.

The app keeps a PNG preview so Tk/CustomTkinter can display the figure, while
the paired EMF is used by Word export for vector-quality output.
"""
from __future__ import annotations

import threading
from typing import Callable, Optional


TIKZ_OUTPUT_MODE_EMF = "emf"
TIKZ_OUTPUT_MODE_PNG = "png"
TIKZ_CONVERT_ACTION_LABEL = "TikZ ▾"
TIKZ_TO_EMF_ACTION_LABEL = "TikZ → EMF"
TIKZ_TO_EMF_DESCRIPTION = (
    "Tạo EMF vector cho Word, kèm PNG preview để xem trong app."
)
TIKZ_TO_PNG_ACTION_LABEL = "TikZ → PNG"
TIKZ_TO_PNG_DESCRIPTION = (
    "Tạo PNG để xem và xuất nhanh, không tạo EMF vector."
)
TIKZ_CONVERSION_OPTIONS = [
    {
        "mode": TIKZ_OUTPUT_MODE_EMF,
        "label": TIKZ_TO_EMF_ACTION_LABEL,
        "description": TIKZ_TO_EMF_DESCRIPTION,
        "confirm": (
            "Tạo EMF vector để giữ nét khi chèn/xuất Word, "
            "đồng thời giữ PNG preview để xem trực tiếp trong app?"
        ),
        "result_name": "EMF vector",
    },
    {
        "mode": TIKZ_OUTPUT_MODE_PNG,
        "label": TIKZ_TO_PNG_ACTION_LABEL,
        "description": TIKZ_TO_PNG_DESCRIPTION,
        "confirm": (
            "Tạo PNG nhanh để xem trong app và chèn vào Word. "
            "Chế độ này không tạo EMF vector."
        ),
        "result_name": "PNG",
    },
]


def get_tikz_conversion_option(mode: str) -> dict[str, str]:
    """Return the shared UI/service metadata for a TikZ conversion mode."""
    for option in TIKZ_CONVERSION_OPTIONS:
        if option["mode"] == mode:
            return option
    raise ValueError(f"Unsupported TikZ conversion mode: {mode}")


def count_pending_blocks(exam_or_questions) -> int:
    """Count TikZ blocks that still need conversion in an exam or question list."""
    from services import tikz_detector

    if isinstance(exam_or_questions, (list, tuple)):
        questions = list(exam_or_questions)
    else:
        questions = list(getattr(exam_or_questions, "questions", []) or [])
    return sum(tikz_detector.count_blocks(question) for question in questions)


def convert_exam_tikz_to_emf(
    exam,
    *,
    dpi: int = 300,
    max_workers: Optional[int] = None,
    progress_cb: Optional[Callable[[int, int, int], None]] = None,
    cancel_event: Optional[threading.Event] = None,
):
    """Convert all pending TikZ blocks to EMF vectors with PNG previews."""
    from services import tikz_pipeline

    if isinstance(exam, (list, tuple)):
        class _ExamWrapper:
            def __init__(self, qs):
                self.questions = qs
        exam = _ExamWrapper(list(exam))

    return tikz_pipeline.process_exam(
        exam,
        dpi=dpi,
        max_workers=max_workers,
        progress_cb=progress_cb,
        cancel_event=cancel_event,
        output_mode=TIKZ_OUTPUT_MODE_EMF,
    )


def convert_questions_tikz_to_emf(
    questions: list,
    *,
    dpi: int = 300,
    max_workers: Optional[int] = None,
    progress_cb: Optional[Callable[[int, int, int], None]] = None,
    cancel_event: Optional[threading.Event] = None,
):
    """Convenience helper to convert a list of Question objects to EMF/PNG."""
    return convert_exam_tikz_to_emf(
        questions,
        dpi=dpi,
        max_workers=max_workers,
        progress_cb=progress_cb,
        cancel_event=cancel_event,
    )


def convert_exam_tikz_to_png(
    exam,
    *,
    dpi: int = 300,
    max_workers: Optional[int] = None,
    progress_cb: Optional[Callable[[int, int, int], None]] = None,
    cancel_event: Optional[threading.Event] = None,
):
    """Convert all pending TikZ blocks to PNG images only."""
    from services import tikz_pipeline

    if isinstance(exam, (list, tuple)):
        class _ExamWrapper:
            def __init__(self, qs):
                self.questions = qs
        exam = _ExamWrapper(list(exam))

    return tikz_pipeline.process_exam(
        exam,
        dpi=dpi,
        max_workers=max_workers,
        progress_cb=progress_cb,
        cancel_event=cancel_event,
        output_mode=TIKZ_OUTPUT_MODE_PNG,
    )

