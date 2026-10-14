"""
services/nhch_suggestor.py — [SMART-3] Suggestion engine cho NHCH.

Trước khi user gọi AI tạo đề, check xem NHCH đã có sẵn câu nào khớp
(subject, grade, topic, level, qtype) hay không. Nếu khớp đủ ≥ threshold
→ suggest user dùng lại NHCH (FREE) thay vì gen mới (tốn API).

API:
    >>> from services.nhch_suggestor import analyze_matrix_coverage
    >>> result = analyze_matrix_coverage(rows, subject="Toán", grade="12")
    >>> result.total_needed      # 22
    >>> result.bank_available    # 47
    >>> result.coverage_pct      # 73.4 (% nhu cầu được cover)
    >>> result.suggest_mode      # "bank_only" | "mixed" | "ai_only"
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional

_log = logging.getLogger(__name__)


@dataclass
class CoverageResult:
    """Kết quả phân tích cover của NHCH."""
    total_needed:    int = 0   # Tổng số câu cần (= số row enabled)
    bank_available:  int = 0   # Tổng câu trong NHCH cùng subject+grade
    matches_by_row:  list[int] = field(default_factory=list)
    # Số câu match trong NHCH cho mỗi MatrixRow (cùng index)
    coverage_pct:    float = 0.0   # % của total_needed có thể dùng NHCH (capped 100)
    suggest_mode:    str = "ai_only"  # "ai_only" | "mixed" | "bank_only"
    sample_ids:      list[str] = field(default_factory=list)
    # Vài question_id mẫu để hiển thị preview

    @property
    def has_matches(self) -> bool:
        return self.bank_available > 0


# ── Threshold để quyết định suggest_mode ────────────────────────────────
_BANK_ONLY_THRESHOLD  = 0.90   # ≥ 90% câu được cover → đề nghị bank_only
_MIXED_THRESHOLD       = 0.30   # ≥ 30% → đề nghị mixed


def analyze_matrix_coverage(
    rows: list,
    subject: str,
    grade: str,
    *,
    max_sample: int = 6,
) -> CoverageResult:
    """[SMART-3] Phân tích NHCH coverage cho ma trận đề.

    Đếm số câu trong NHCH khớp với mỗi MatrixRow theo (subject, grade,
    topic, level, qtype). Trả CoverageResult với suggest_mode.

    Parameters
    ----------
    rows:    list[MatrixRow] đã filter enabled=True
    subject: môn (vd "Toán")
    grade:   lớp (vd "12")
    max_sample: tối đa bao nhiêu question_id mẫu để return

    Returns
    -------
    CoverageResult — KHÔNG raise; nếu lỗi DB, trả result với
    bank_available=0 + suggest_mode="ai_only".
    """
    result = CoverageResult(total_needed=len(rows))
    if not rows:
        return result

    try:
        from storage.database import search_questions
    except Exception as e:
        _log.warning("Failed to import search_questions: %s", e)
        return result

    # ── Pass 1: tổng số câu trong NHCH cho subject+grade ──
    try:
        all_in_bank = search_questions(
            subject=subject, grade=grade, limit=5000)
    except Exception as e:
        _log.warning("NHCH search failed: %s", e)
        return result
    result.bank_available = len(all_in_bank)

    # ── Pass 2: match từng row ──
    matches_per_row: list[int] = []
    total_satisfied = 0
    sample: list[str] = []

    for row in rows:
        try:
            topic = (getattr(row, "topic", "") or "").strip()
            level = (getattr(row, "level", "") or "").strip()
            qtype = (getattr(row, "qtype", "") or "").strip()

            # Match strict: cùng level + qtype + topic LIKE
            # search_questions hỗ trợ topic LIKE '%...%' → fuzzy match OK
            matched = search_questions(
                subject=subject, grade=grade,
                topic=topic[:30],   # truncate cho LIKE
                level=level, qtype=qtype,
                limit=20,
            )
        except Exception as e:
            _log.debug("Row match failed: %s", e)
            matched = []

        n_match = len(matched)
        matches_per_row.append(n_match)
        if n_match > 0:
            total_satisfied += 1
            # Lấy ID đầu làm sample
            if len(sample) < max_sample:
                for q in matched[:1]:
                    qid = q.get("question_id") or q.get("_bank_id")
                    if qid:
                        sample.append(str(qid))

    result.matches_by_row = matches_per_row
    result.sample_ids = sample
    if result.total_needed > 0:
        result.coverage_pct = round(
            100.0 * total_satisfied / result.total_needed, 1)

    # ── Suggest mode ──
    pct = result.coverage_pct / 100.0
    if pct >= _BANK_ONLY_THRESHOLD:
        result.suggest_mode = "bank_only"
    elif pct >= _MIXED_THRESHOLD:
        result.suggest_mode = "mixed"
    else:
        result.suggest_mode = "ai_only"

    _log.info(
        "[SMART-3] Coverage analysis: %d/%d rows matched (%.1f%%), "
        "bank=%d, suggest=%s",
        total_satisfied, result.total_needed, result.coverage_pct,
        result.bank_available, result.suggest_mode,
    )
    return result


def format_suggestion_summary(result: CoverageResult,
                                subject: str = "", grade: str = "") -> str:
    """Build human-friendly summary cho dialog."""
    if not result.has_matches:
        return ""

    lines = [
        f"📊 NHCH có {result.bank_available} câu hỏi cho {subject} lớp {grade}.",
        "",
        f"Bộ câu yêu cầu của bạn ({result.total_needed} câu) — NHCH có thể đáp ứng:",
        f"  • {result.coverage_pct:.0f}% số dòng có ít nhất 1 câu khớp.",
    ]

    mode = result.suggest_mode
    if mode == "bank_only":
        lines += [
            "",
            "💡 ĐỀ XUẤT: Dùng 100% NHCH — KHÔNG TỐN API.",
            "    Tất cả câu đều có sẵn trong ngân hàng của bạn.",
        ]
    elif mode == "mixed":
        lines += [
            "",
            "💡 ĐỀ XUẤT: Mix 70% NHCH + 30% AI mới — tiết kiệm ~70% API.",
            "    Đa số câu lấy từ NHCH, AI chỉ sinh phần còn thiếu.",
        ]
    else:
        lines += [
            "",
            "💡 GỢI Ý: NHCH có ít câu khớp — nên dùng AI tạo mới (như cũ).",
        ]
    return "\n".join(lines)
