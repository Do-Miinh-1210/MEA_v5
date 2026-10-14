"""
services/smart_defaults.py — v4.2 Smart Defaults.

Quyết định nguồn tạo đề mặc định dựa trên:
- Độ phủ NHCH theo ma trận hiện tại.
- Tier/tính năng license.
- Trạng thái quota gần đây của provider/model đang chọn.

Module này thuần logic để test được, UI chỉ dùng kết quả để gợi ý user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SourceRecommendation:
    """Gợi ý nguồn tạo đề cho ma trận hiện tại."""

    mode: str = "ai_only"          # ai_only | mixed | bank_only
    bank_ratio: int = 0            # % câu ưu tiên lấy từ NHCH khi mode=mixed
    confidence: str = "low"        # low | medium | high
    should_prompt: bool = False

    coverage_pct: float = 0.0
    bank_available: int = 0
    quota_level: str = "unknown"   # ok | warn | danger | over | unknown
    quota_percent: float = 0.0

    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def label(self) -> str:
        labels = {
            "ai_only": "AI mới hoàn toàn",
            "mixed": f"Mix {self.bank_ratio}% NHCH + {100 - self.bank_ratio}% AI",
            "bank_only": "100% NHCH",
        }
        return labels.get(self.mode, self.mode)


def _feature_enabled(features: Optional[dict[str, bool]], key: str, default: bool = True) -> bool:
    if features is None:
        return default
    return bool(features.get(key, default))


def _normalize_quota_status(provider: str, model: str, quota: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    if quota is not None:
        return quota
    if not provider or not model:
        return {"level": "unknown", "percent": 0}
    try:
        from services.ai_usage_log import quota_status

        return quota_status(provider, model)
    except Exception:
        return {"level": "unknown", "percent": 0}


def _coverage_for_rows(rows: list, subject: str, grade: str, coverage=None):
    if coverage is not None:
        return coverage
    try:
        from services.nhch_suggestor import analyze_matrix_coverage

        return analyze_matrix_coverage(rows, subject, grade)
    except Exception:
        return None


def recommend_source_mode(
    rows: list,
    *,
    subject: str = "",
    grade: str = "",
    provider: str = "",
    model: str = "",
    tier: str = "premium",
    features: Optional[dict[str, bool]] = None,
    coverage=None,
    quota: Optional[dict[str, Any]] = None,
) -> SourceRecommendation:
    """Trả về gợi ý nguồn tạo đề cho ma trận hiện tại.

    Không raise: nếu thiếu DB/quota/provider thì fallback về `ai_only`.
    """
    total = len(rows or [])
    rec = SourceRecommendation()
    if total <= 0:
        rec.reasons.append("Chưa có dòng ma trận đang bật.")
        return rec

    bank_allowed = (
        _feature_enabled(features, "tab_bank", tier.lower() != "basic")
        or _feature_enabled(features, "nhch_cloud", False)
    )
    if not bank_allowed:
        rec.reasons.append("Gói hiện tại chưa bật NHCH, giữ nguồn AI.")
        return rec

    cov = _coverage_for_rows(rows, subject, grade, coverage)
    if cov is not None:
        rec.coverage_pct = float(getattr(cov, "coverage_pct", 0.0) or 0.0)
        rec.bank_available = int(getattr(cov, "bank_available", 0) or 0)

    q = _normalize_quota_status(provider, model, quota)
    rec.quota_level = str(q.get("level") or "unknown")
    rec.quota_percent = float(q.get("percent") or 0.0)

    quota_hot = rec.quota_level in {"warn", "danger", "over"}
    if quota_hot:
        rec.warnings.append(
            f"Quota {provider or 'AI'} {model or ''} đang ở mức {rec.quota_level} ({rec.quota_percent:.0f}%).".strip()
        )

    if rec.coverage_pct >= 90 and rec.bank_available >= total:
        rec.mode = "bank_only"
        rec.bank_ratio = 100
        rec.confidence = "high"
        rec.should_prompt = True
        rec.reasons.append(f"NHCH phủ {rec.coverage_pct:.0f}% ma trận, đủ để tạo đề không tốn API.")
    elif rec.coverage_pct >= 60:
        rec.mode = "mixed"
        rec.bank_ratio = 80 if quota_hot else 70
        rec.confidence = "high" if quota_hot else "medium"
        rec.should_prompt = True
        rec.reasons.append(f"NHCH phủ {rec.coverage_pct:.0f}% ma trận, nên ưu tiên lấy lại câu phù hợp.")
    elif rec.coverage_pct >= 30:
        rec.mode = "mixed"
        rec.bank_ratio = 60 if quota_hot else 50
        rec.confidence = "medium"
        rec.should_prompt = True
        rec.reasons.append(f"NHCH phủ {rec.coverage_pct:.0f}% ma trận, có thể tiết kiệm một phần API.")
    else:
        rec.mode = "ai_only"
        rec.bank_ratio = 0
        rec.confidence = "low"
        rec.should_prompt = quota_hot and rec.bank_available > 0
        if rec.bank_available > 0:
            rec.reasons.append(
                f"NHCH có {rec.bank_available} câu nhưng chỉ khớp {rec.coverage_pct:.0f}% ma trận."
            )
        else:
            rec.reasons.append("NHCH chưa có câu phù hợp, giữ nguồn AI.")

    if quota_hot and rec.mode == "ai_only" and rec.bank_available > 0:
        rec.mode = "mixed"
        rec.bank_ratio = 40
        rec.confidence = "medium"
        rec.reasons.append("Do quota đang cao, vẫn nên thử lấy một phần từ NHCH trước.")

    return rec


def format_recommendation_summary(rec: SourceRecommendation, subject: str = "", grade: str = "") -> str:
    """Format ngắn gọn cho dialog/toast."""
    scope = " ".join(x for x in [subject, f"lớp {grade}" if grade else ""] if x).strip()
    lines = []
    if scope:
        lines.append(f"Phạm vi: {scope}")
    lines.append(
        f"NHCH: {rec.bank_available} câu, phủ khoảng {rec.coverage_pct:.0f}% ma trận."
    )
    if rec.quota_level != "unknown":
        lines.append(f"Quota AI: {rec.quota_level} ({rec.quota_percent:.0f}%).")
    lines.append(f"Đề xuất: {rec.label()} ({rec.confidence}).")
    if rec.reasons:
        lines.append("")
        lines.extend(f"• {reason}" for reason in rec.reasons[:3])
    if rec.warnings:
        lines.append("")
        lines.extend(f"⚠ {warning}" for warning in rec.warnings[:2])
    return "\n".join(lines)
