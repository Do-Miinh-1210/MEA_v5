"""Guard rails for the shared V4/V5 TikZ conversion workflow."""
from __future__ import annotations

from pathlib import Path

import pytest

from core.models import ExamData, Question
from services import tikz_vector_workflow


ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_shared_workflow_counts_pending_tikz_blocks():
    exam = ExamData(
        "ĐỀ",
        "Toán",
        "12",
        "I",
        "2025-2026",
        "90 phút",
        questions=[
            Question(
                qtype="TL",
                level="VD",
                topic="Hình học",
                question=(
                    r"Cho hình. \begin{tikzpicture}"
                    r"\draw (0,0)--(1,0); \end{tikzpicture}"
                ),
            ),
            Question(qtype="TN", level="NB", topic="Đại số", question="Không có hình."),
        ],
    )

    assert tikz_vector_workflow.count_pending_blocks(exam) == 1


def test_shared_workflow_delegates_to_vector_pipeline(monkeypatch):
    exam = ExamData("ĐỀ", "Toán", "12", "I", "2025-2026", "90 phút")
    marker = object()
    calls: list[dict] = []

    def fake_process(target_exam, **kwargs):
        calls.append({"exam": target_exam, **kwargs})
        return marker

    monkeypatch.setattr("services.tikz_pipeline.process_exam", fake_process)

    result = tikz_vector_workflow.convert_exam_tikz_to_emf(
        exam,
        dpi=220,
        max_workers=2,
    )

    assert result is marker
    assert calls == [{
        "exam": exam,
        "dpi": 220,
        "max_workers": 2,
        "progress_cb": None,
        "cancel_event": None,
        "output_mode": "emf",
    }]


def test_shared_workflow_delegates_png_mode_to_pipeline(monkeypatch):
    exam = ExamData("ĐỀ", "Toán", "12", "I", "2025-2026", "90 phút")
    marker = object()
    calls: list[dict] = []

    def fake_process(target_exam, **kwargs):
        calls.append({"exam": target_exam, **kwargs})
        return marker

    monkeypatch.setattr("services.tikz_pipeline.process_exam", fake_process)

    result = tikz_vector_workflow.convert_exam_tikz_to_png(
        exam,
        dpi=180,
        max_workers=1,
    )

    assert result is marker
    assert calls == [{
        "exam": exam,
        "dpi": 180,
        "max_workers": 1,
        "progress_cb": None,
        "cancel_event": None,
        "output_mode": "png",
    }]


def test_v4_and_v5_result_screens_use_the_same_vector_workflow():
    v4_source = _source("ui/tab_result.py")
    v5_source = _source("v5/views/exam_create.py")

    for source in (v4_source, v5_source):
        assert "TIKZ_CONVERSION_OPTIONS" in source
        assert "TIKZ_TO_EMF_ACTION_LABEL" in source
        assert "TIKZ_TO_EMF_DESCRIPTION" in source
        assert "convert_exam_tikz_to_emf" in source
        assert "convert_exam_tikz_to_png" in source
        assert "count_pending_blocks" in source
        assert "TikZ → Ảnh" not in source
        assert "tikz_pipeline.process_exam" not in source


def test_v4_result_toolbar_keeps_actions_visible_at_minimum_width():
    import tkinter as tk

    from ui.tab_result import TabResult

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk display is unavailable: {exc}")

    try:
        root.geometry("860x600")
        view = TabResult(
            root,
            get_ai_call=lambda: None,
            get_subject_grade=lambda: ("Toán", "12"),
        )
        view.pack(fill="both", expand=True)
        root.update_idletasks()
        root.update()

        expected = {
            "📄 Xuất Word & mở",
            "📂 Nhiều mã đề",
            f"📐 {tikz_vector_workflow.TIKZ_CONVERT_ACTION_LABEL}",
            "⚙️ Cài đặt xuất",
            "🔁 Tạo lại lỗi",
            "✅ Kiểm tra chất lượng",
            "Kèm lời giải & đáp án",
        }
        controls = {}
        for row in (view._toolbar_primary_row, view._toolbar_secondary_row):
            for widget in row.winfo_children():
                try:
                    text = widget.cget("text")
                except tk.TclError:
                    continue
                if text in expected:
                    controls[text] = widget

        assert set(controls) == expected
        for widget in controls.values():
            assert widget.winfo_ismapped()
            assert widget.winfo_x() + widget.winfo_width() <= widget.master.winfo_width()
    finally:
        root.destroy()


def test_vector_contract_is_shared_from_pipeline_to_word_export():
    pipeline_source = _source("services/tikz_pipeline.py")
    image_fields_source = _source("services/image_fields.py")
    exporter_source = _source("export/word_exporter.py")

    assert "serialize_vector_image" in pipeline_source
    assert "EMF vector" in pipeline_source
    assert 'VECTOR_IMAGE_SEPARATOR = "::emf::"' in image_fields_source
    assert "normalize_image_field(image_value, prefer_vector=True)" in exporter_source
    assert "def _add_emf_image" in exporter_source


def test_v4_release_version_uses_config_as_the_single_source():
    from config import APP_VERSION

    build_source = _source("build_helper.py")
    installer_source = _source("installer.iss")
    readme_source = _source("README.md")

    assert "from config import APP_VERSION" in build_source
    assert f'#define MyAppVersion "{APP_VERSION}"' in installer_source
    assert f"# MEA — MatrixExam AI v{APP_VERSION}" in readme_source


def test_scan_question_deduplicates_mirrored_tikz_code():
    from services import tikz_detector

    code = r"""\begin{tikzpicture}
\draw (0,0) -- (1,1);
\end{tikzpicture}"""
    q = Question(
        qtype="TN",
        level="NB",
        topic="Toán",
        question=f"Cho hình vẽ:\n{code}\nChọn đáp án đúng.",
    )
    q.tikz_code = code

    blocks = tikz_detector.scan_question(q)
    assert len(blocks) == 1
    assert blocks[0].field == "question"
