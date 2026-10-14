"""Guard rails for V5 QC report export parity."""
from __future__ import annotations

import csv
from pathlib import Path

from core.models import Question
from core.models import ExamData
from v5.views.qc import QCView


ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class _DummyQC:
    pass


def test_qc_view_ports_v4_report_export_actions_without_v4_ui():
    source = _source("v5/views/qc.py")

    assert "self._qc_report_btn" in source
    assert "def _export_qc_report" in source
    assert "def _qc_report_rows" in source
    assert "def _write_qc_report_csv" in source
    assert "def _write_qc_report_xlsx" in source
    assert "QC_Report_V5.xlsx" in source
    assert "📥  Báo cáo" in source
    assert "from ui." not in source


def test_qc_view_ports_v4_apply_results_to_current_exam():
    source = _source("v5/views/qc.py")
    app_source = _source("v5/app.py")

    assert "self._qc_apply_btn" in source
    assert "def _apply_qc_results" in source
    assert "def _apply_qc_reviews_to_exam" in source
    assert "def _resolve_apply_target_exam" in source
    assert "target._review = review_meta" in source
    assert "self._on_exam_changed(exam)" in source
    assert 'kwargs["on_exam_changed"] = self._on_exam_changed' in app_source
    assert "✅  Áp dụng" in source
    assert "from ui." not in source


def test_qc_view_exposes_model_selector_and_responsive_table():
    source = _source("v5/views/qc.py")

    assert "QC_AI_MODEL_OPTIONS" in source
    assert "self._qc_model_menu = ctk.CTkOptionMenu" in source
    assert "def _on_qc_ai_provider_change" in source
    assert "self._qc_model_menu.configure(values=values)" in source
    assert "model = (" in source
    assert "self._qc_model_var.get()" in source
    assert "create_ai_service(provider, keys, model).generate" in source
    assert "run_row.grid_columnconfigure(3, weight=1)" in source
    assert "self._qc_prog.grid(row=1, column=0, columnspan=3" in source
    assert "self._qc_prog_lbl.grid(row=1, column=3" in source
    assert "minwidths = {" in source
    assert "minwidth=minwidths[cc]" in source
    assert 'stretch=(cc == "issue")' in source


def test_qc_report_csv_contains_questions_and_review_rows(tmp_path: Path):
    dummy = _DummyQC()
    dummy._qc_questions = [
        Question(
            qtype="TN",
            level="TH",
            topic="Hàm số",
            question="Cho hàm số $y=x^2$. Chọn mệnh đề đúng.",
            answer="A",
        )
    ]
    dummy._qc_reviews = [
        {"ok": False, "score": 7.5, "issue": "Đáp án chưa khớp lời giải."}
    ]
    dummy._qc_report_rows = lambda: QCView._qc_report_rows(dummy)

    out = tmp_path / "qc.csv"
    QCView._write_qc_report_csv(dummy, str(out))

    with out.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    assert rows[0]["STT"] == "1"
    assert rows[0]["Loại"] == "TN"
    assert rows[0]["Mức"] == "TH"
    assert rows[0]["Điểm"] == "7.5"
    assert rows[0]["Kết quả"] == "REVIEW/FAIL"
    assert "Đáp án chưa khớp" in rows[0]["Vấn đề / Gợi ý"]


def test_qc_apply_reviews_updates_matching_exam_questions():
    target = Question(
        qtype="TN",
        level="NB",
        topic="Hàm số",
        question="Câu gốc",
        answer="A",
    )
    reviewed = Question(
        qtype="TN",
        level="NB",
        topic="Hàm số",
        question="Câu đã QC",
        answer="A",
    )
    reviewed.question_id = target.question_id
    reviewed._review = {"qc_pipeline": True, "quality_score": {"passed": True}}

    exam = ExamData(
        exam_title="Đề test",
        subject="Toán",
        grade="12",
        semester="I",
        year="2026",
        time="45 phút",
        questions=[target],
    )
    dummy = _DummyQC()
    dummy._qc_reviewed_questions = [reviewed]

    applied = QCView._apply_qc_reviews_to_exam(dummy, exam)

    assert applied == 1
    assert target._review == reviewed._review
