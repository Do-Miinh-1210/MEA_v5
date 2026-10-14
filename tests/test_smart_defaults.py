from services.nhch_suggestor import CoverageResult
from services.smart_defaults import recommend_source_mode, format_recommendation_summary


def _rows(n=10):
    return [object() for _ in range(n)]


def test_recommend_bank_only_when_coverage_is_high():
    cov = CoverageResult(total_needed=10, bank_available=20, coverage_pct=95)

    rec = recommend_source_mode(
        _rows(10),
        subject="Toán",
        grade="12",
        tier="premium",
        features={"tab_bank": True},
        coverage=cov,
        quota={"level": "ok", "percent": 10},
    )

    assert rec.mode == "bank_only"
    assert rec.bank_ratio == 100
    assert rec.should_prompt is True
    assert rec.confidence == "high"


def test_recommend_mixed_more_bank_when_quota_is_hot():
    cov = CoverageResult(total_needed=10, bank_available=12, coverage_pct=65)

    rec = recommend_source_mode(
        _rows(10),
        tier="premium",
        features={"tab_bank": True},
        coverage=cov,
        quota={"level": "danger", "percent": 97},
    )

    assert rec.mode == "mixed"
    assert rec.bank_ratio == 80
    assert rec.warnings


def test_recommend_ai_when_bank_feature_is_unavailable():
    cov = CoverageResult(total_needed=10, bank_available=99, coverage_pct=100)

    rec = recommend_source_mode(
        _rows(10),
        tier="basic",
        features={"tab_bank": False, "nhch_cloud": False},
        coverage=cov,
        quota={"level": "ok", "percent": 0},
    )

    assert rec.mode == "ai_only"
    assert rec.should_prompt is False
    assert "chưa bật NHCH" in rec.reasons[0]


def test_format_recommendation_summary_contains_decision():
    cov = CoverageResult(total_needed=10, bank_available=8, coverage_pct=50)
    rec = recommend_source_mode(
        _rows(10),
        subject="Toán",
        grade="11",
        features={"tab_bank": True},
        coverage=cov,
        quota={"level": "warn", "percent": 82},
    )

    text = format_recommendation_summary(rec, "Toán", "11")

    assert "Đề xuất" in text
    assert "Mix" in text
    assert "Quota AI" in text
