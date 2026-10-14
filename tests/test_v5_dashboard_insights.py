from __future__ import annotations

from pathlib import Path

from core.models import ExamData, Question
from v5.dashboard_insights import (
    bank_report_lines,
    exam_report_lines,
    export_dashboard_report,
    normalize_bank_stats,
    quality_bucket_rows,
    summarize_exam,
)


def _question(qtype: str, score=None, **extra) -> Question:
    review = None
    if score is not None:
        review = {"quality_score": {"final_score": score}}
    review_extra = extra.pop("review", None)
    if review_extra:
        review = {**(review or {}), **review_extra}
    q = Question(qtype=qtype, level="NB", topic="Hàm số", question="Câu hỏi")
    q._review = review
    for key, value in extra.items():
        setattr(q, key, value)
    return q


def test_dashboard_summarizes_current_exam_quality_and_suspects():
    exam = ExamData(
        exam_title="Đề test",
        subject="Toán",
        grade="12",
        semester="1",
        year="2026",
        time="90 phút",
        questions=[
            _question("TN", 0.95),
            _question("DS", 0.82),
            _question("TLN", 0.65),
            _question("TL", review={"needs_review": True}),
        ],
    )

    summary = summarize_exam(exam)

    assert summary["has_exam"] is True
    assert summary["total"] == 4
    assert summary["by_type"] == {"TN": 1, "DS": 1, "TLN": 1, "TL": 1}
    assert summary["avg_score"] == 0.807
    assert summary["pass_08"] == 2
    assert summary["pass_09"] == 1
    assert summary["buckets"]["≥ 0.9"] == 1
    assert summary["buckets"]["< 0.7"] == 1
    assert len(summary["suspects"]) == 2
    assert summary["suspects"][0]["severity"] == "reject"


def test_dashboard_normalizes_legacy_bank_stats_and_formats_lines():
    stats = normalize_bank_stats({
        "total": 3,
        "by_type": {"TN": 2, "DS": 1},
        "by_level": {"NB": 3},
    })
    lines = bank_report_lines(stats)

    assert stats["valid"] == 3
    assert stats["invalid"] == 0
    assert any("Tổng số câu:            3" in line for line in lines)
    assert any("TN: 2 câu" in line for line in lines)


def test_dashboard_quality_bucket_rows_include_percentages():
    summary = summarize_exam(ExamData(
        exam_title="Đề",
        subject="Toán",
        grade="12",
        semester="1",
        year="2026",
        time="45 phút",
        questions=[_question("TN", 0.91), _question("TN", None)],
    ))

    rows = quality_bucket_rows(summary)
    by_bucket = {row["bucket"]: row for row in rows}

    assert by_bucket["≥ 0.9"]["percent"] == 50
    assert by_bucket["Chưa QC"]["percent"] == 50


def test_dashboard_export_report_writes_bank_exam_and_model_sections(tmp_path: Path):
    exam_summary = summarize_exam(ExamData(
        exam_title="Đề xuất báo cáo",
        subject="Toán",
        grade="12",
        semester="1",
        year="2026",
        time="45 phút",
        questions=[_question("TN", 0.92)],
    ))
    output = export_dashboard_report(
        tmp_path / "report.txt",
        bank_stats={"total": 1, "valid": 1, "by_type": {"TN": 1}},
        exam_summary=exam_summary,
        model_rows=[{"model": "gemini", "count": 1, "avg_score": 0.92, "pass_count": 1}],
    )

    text = output.read_text(encoding="utf-8")
    assert "BÁO CÁO BẢNG ĐIỀU KHIỂN - MEA V5" in text
    assert "NGÂN HÀNG CÂU HỎI" in text
    assert "ĐỀ THI HIỆN TẠI" in text
    assert "gemini: 1 câu" in text


def test_tracking_ports_v4_dashboard_actions_without_v4_ui_dependency():
    root = Path(__file__).resolve().parents[1]
    tracking = (root / "v5" / "views" / "tracking.py").read_text(encoding="utf-8")
    source = (root / "v5" / "dashboard_insights.py").read_text(encoding="utf-8")

    assert "_build_dashboard" in tracking
    assert "_analyze_feedback" in tracking
    assert "export_dashboard_report" in tracking
    assert "get_current_exam" in tracking
    assert "from ui." not in source
    assert "import ui." not in source
