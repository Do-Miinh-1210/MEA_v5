"""
v5/dashboard_insights.py -- V5-native dashboard summaries.

This ports the useful logic from V4's ``tab_dashboard`` into testable helpers:
bank statistics, current-exam quality distribution, model comparison rows and
plain-text report export. UI code lives in ``v5.views.tracking``.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable


QUALITY_BUCKETS = ("≥ 0.9", "0.8-0.9", "0.7-0.8", "< 0.7", "Chưa QC")
BUCKET_COLORS = {
    "≥ 0.9": "#2E7D32",
    "0.8-0.9": "#558B2F",
    "0.7-0.8": "#E65100",
    "< 0.7": "#C62828",
    "Chưa QC": "#78909C",
}


def _as_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def question_quality_score(question: Any) -> float | None:
    review = getattr(question, "_review", None) or {}
    if not isinstance(review, dict) or "quality_score" not in review:
        return None
    raw = review.get("quality_score")
    if isinstance(raw, dict):
        raw = raw.get("final_score")
    return _as_float(raw)


def _bucket_for_score(score: float | None) -> str:
    if score is None:
        return "Chưa QC"
    if score >= 0.9:
        return "≥ 0.9"
    if score >= 0.8:
        return "0.8-0.9"
    if score >= 0.7:
        return "0.7-0.8"
    return "< 0.7"


def summarize_exam(exam: Any | None) -> dict:
    if exam is None:
        return {
            "has_exam": False,
            "title": "",
            "total": 0,
            "errors": 0,
            "by_type": {},
            "scores": [],
            "avg_score": None,
            "pass_08": 0,
            "pass_09": 0,
            "reviewed": 0,
            "buckets": {key: 0 for key in QUALITY_BUCKETS},
            "suspects": [],
        }

    questions = list(getattr(exam, "questions", []) or [])
    by_type: Counter[str] = Counter()
    scores: list[float] = []
    buckets: Counter[str] = Counter({key: 0 for key in QUALITY_BUCKETS})
    suspects: list[dict] = []

    for index, question in enumerate(questions, start=1):
        qtype = str(getattr(question, "qtype", "") or "?")
        by_type[qtype] += 1
        score = question_quality_score(question)
        if score is not None:
            scores.append(score)
        buckets[_bucket_for_score(score)] += 1

        review = getattr(question, "_review", None) or {}
        issue = ""
        severity = ""
        if getattr(question, "_error", False):
            issue = str(getattr(question, "_error_msg", "") or "Lỗi tạo câu")
            severity = "reject"
        elif isinstance(review, dict) and review.get("cross_model_disagree"):
            issue = "Hai mô hình không đồng ý"
            severity = "review"
        elif score is not None and score < 0.8:
            qc = review.get("quality_score") if isinstance(review, dict) else {}
            reason = qc.get("reject_reason", "") if isinstance(qc, dict) else ""
            issue = str(reason or f"Điểm thấp ({score:.2f})")
            severity = "reject" if score < 0.7 else "review"
        elif isinstance(review, dict) and review.get("needs_review"):
            issue = "Cần xem lại"
            severity = "review"

        if issue:
            suspects.append({
                "label": f"Câu {index}",
                "qtype": qtype,
                "issue": issue[:80],
                "score": score,
                "severity": severity,
            })

    total = len(questions)
    errors = sum(1 for question in questions if getattr(question, "_error", False))
    return {
        "has_exam": True,
        "title": str(getattr(exam, "exam_title", "") or "Đề đang mở"),
        "total": total,
        "errors": errors,
        "by_type": dict(by_type),
        "scores": scores,
        "avg_score": round(sum(scores) / len(scores), 3) if scores else None,
        "pass_08": sum(1 for score in scores if score >= 0.8),
        "pass_09": sum(1 for score in scores if score >= 0.9),
        "reviewed": len(scores),
        "buckets": {key: int(buckets.get(key, 0)) for key in QUALITY_BUCKETS},
        "suspects": suspects,
    }


def normalize_bank_stats(stats: dict | None) -> dict:
    data = dict(stats or {})
    total = int(data.get("total", 0) or 0)
    valid = int(data.get("valid", total) or 0)
    invalid = int(data.get("invalid", max(total - valid, 0)) or 0)
    return {
        "total": total,
        "valid": valid,
        "invalid": invalid,
        "avg_quality_score": data.get("avg_quality_score"),
        "top_quality_count": int(data.get("top_quality_count", 0) or 0),
        "total_feedback": int(data.get("total_feedback", 0) or 0),
        "edits": int(data.get("edits", 0) or 0),
        "by_type": dict(data.get("by_type", {}) or {}),
        "by_level": dict(data.get("by_level", {}) or {}),
        "by_subject": dict(data.get("by_subject", {}) or {}),
        "by_model": dict(data.get("by_model", {}) or {}),
    }


def load_bank_stats() -> dict:
    try:
        from storage.smart_db import smart_stats
        return normalize_bank_stats(smart_stats())
    except Exception:
        try:
            from storage.database import db_stats
            return normalize_bank_stats(db_stats())
        except Exception:
            return normalize_bank_stats({})


def load_model_quality_rows() -> list[dict]:
    try:
        from storage.smart_db import _get_con, smart_db_init

        smart_db_init()
        with _get_con() as con:
            rows = con.execute("""
                SELECT source_model,
                       COUNT(*) AS count,
                       AVG(quality_score) AS avg_score,
                       SUM(CASE WHEN quality_score>=0.9 THEN 1 ELSE 0 END) AS pass_count
                FROM questions_v2
                WHERE source_model!='' AND is_valid=1
                GROUP BY source_model
                ORDER BY avg_score DESC
            """).fetchall()
        return [
            {
                "model": row["source_model"] or "Không rõ",
                "count": int(row["count"] or 0),
                "avg_score": _as_float(row["avg_score"]),
                "pass_count": int(row["pass_count"] or 0),
            }
            for row in rows
        ]
    except Exception:
        stats = load_bank_stats()
        return [
            {"model": model or "Không rõ", "count": int(count or 0),
             "avg_score": None, "pass_count": None}
            for model, count in stats.get("by_model", {}).items()
        ]


def bank_report_lines(stats: dict) -> list[str]:
    data = normalize_bank_stats(stats)
    avg = data["avg_quality_score"]
    avg_text = "Chưa có" if avg in (None, "") else str(avg)
    lines = [
        f"Tổng số câu:            {data['total']}",
        f"Hợp lệ:                 {data['valid']}",
        f"Không hợp lệ:           {data['invalid']}",
        "",
        f"Điểm chất lượng TB:     {avg_text}",
        f"Câu đạt ≥ 0.9:          {data['top_quality_count']}",
        f"Tổng phản hồi:          {data['total_feedback']}",
        f"Lượt sửa:               {data['edits']}",
        "",
        "Theo loại câu:",
    ]
    lines.extend(_dict_lines(data["by_type"]))
    lines.append("")
    lines.append("Theo mức độ:")
    lines.extend(_dict_lines(data["by_level"]))
    lines.append("")
    lines.append("Theo môn/lớp:")
    lines.extend(_dict_lines(data["by_subject"], limit=8))
    return lines


def exam_report_lines(summary: dict) -> list[str]:
    if not summary.get("has_exam"):
        return ["Chưa có đề thi hiện tại.", "Mở Tạo đề hoặc khôi phục lịch sử để xem thống kê."]

    reviewed = int(summary.get("reviewed", 0) or 0)
    lines = [
        f"Tiêu đề: {summary.get('title', '')}",
        f"Tổng số câu: {summary.get('total', 0)}",
        f"Câu bị lỗi:  {summary.get('errors', 0)}",
        "",
        "Theo loại:",
    ]
    lines.extend(_dict_lines(summary.get("by_type", {})))
    if reviewed:
        lines.extend([
            "",
            f"Điểm QC trung bình:  {summary.get('avg_score')}",
            f"Đạt ngưỡng (≥ 0.8):  {summary.get('pass_08', 0)}/{reviewed}",
            f"Pass (≥ 0.9):         {summary.get('pass_09', 0)}/{reviewed}",
        ])
    else:
        lines.extend(["", "Chưa có kết quả QC cho đề hiện tại."])
    return lines


def _dict_lines(data: dict, *, limit: int | None = None) -> list[str]:
    items = sorted((str(k or "Không rõ"), int(v or 0)) for k, v in data.items())
    if limit is not None:
        items = items[:limit]
    if not items:
        return ["  Chưa có"]
    return [f"  {key}: {value} câu" for key, value in items]


def quality_bucket_rows(summary: dict) -> list[dict]:
    total = max(int(summary.get("total", 0) or 0), 1)
    buckets = dict(summary.get("buckets", {}) or {})
    return [
        {
            "bucket": bucket,
            "count": int(buckets.get(bucket, 0) or 0),
            "percent": int(round(int(buckets.get(bucket, 0) or 0) / total * 100)),
            "color": BUCKET_COLORS[bucket],
        }
        for bucket in QUALITY_BUCKETS
    ]


def export_dashboard_report(
    output_path: str | Path,
    *,
    bank_stats: dict,
    exam_summary: dict,
    model_rows: Iterable[dict] = (),
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "BÁO CÁO BẢNG ĐIỀU KHIỂN - MEA V5",
        "=" * 45,
        "",
        "NGÂN HÀNG CÂU HỎI",
        "-" * 45,
        *bank_report_lines(bank_stats),
        "",
        "ĐỀ THI HIỆN TẠI",
        "-" * 45,
        *exam_report_lines(exam_summary),
        "",
        "SO SÁNH MÔ HÌNH AI",
        "-" * 45,
    ]
    rows = list(model_rows)
    if not rows:
        lines.append("Chưa có dữ liệu mô hình.")
    else:
        for row in rows:
            avg = row.get("avg_score")
            avg_text = f"{avg:.3f}" if isinstance(avg, float) else "Chưa có"
            pass_count = row.get("pass_count")
            pass_text = "—" if pass_count is None else f"{pass_count}/{row.get('count', 0)}"
            lines.append(
                f"{row.get('model', 'Không rõ')}: {row.get('count', 0)} câu, "
                f"điểm TB {avg_text}, đạt {pass_text}"
            )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
