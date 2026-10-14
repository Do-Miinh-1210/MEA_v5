from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from v5.ai_cost import estimate_cost
from v5.ai_usage_summary import (
    export_usage_csv,
    filter_usage_entries,
    normalize_usage_entry,
    quota_warnings,
    summarize_usage,
)


def _entry(ts: str, **extra) -> dict:
    base = {
        "ts": ts,
        "provider": "Google Gemini",
        "model": "gemini-2.5-pro",
        "kind": "generate",
        "prompt_chars": 4000,
        "response_chars": 800,
        "duration_ms": 2500,
        "ok": True,
    }
    base.update(extra)
    return base


def test_v5_usage_normalizes_v4_char_log_and_estimates_tokens():
    row = normalize_usage_entry(_entry("2026-05-26T08:00:00"))

    assert row["tokens_in"] == 1000
    assert row["tokens_out"] == 200
    assert row["tokens_estimated"] is True
    assert row["cost_usd"] == estimate_cost("gemini-2.5-pro", 1000, 200)
    assert row["task"] == "generate"
    assert row["duration_ms"] == 2500


def test_v5_usage_keeps_exact_token_log_shape():
    row = normalize_usage_entry(
        _entry(
            "2026-05-26T09:00:00",
            task="qc",
            tokens_in=123,
            tokens_out=45,
            elapsed=1.4,
            duration_ms=0,
            prompt_chars=0,
            response_chars=0,
        )
    )

    assert row["tokens_in"] == 123
    assert row["tokens_out"] == 45
    assert row["tokens_estimated"] is False
    assert row["task"] == "qc"
    assert row["duration_ms"] == 1400


def test_v5_usage_filters_and_summarizes_range():
    entries = [
        _entry("2026-05-26T08:00:00"),
        _entry("2026-05-22T08:00:00", ok=False, kind="generate_with_image"),
        _entry("2026-05-18T08:00:00", provider="OpenAI", model="gpt-4o"),
    ]

    filtered = filter_usage_entries(entries, "7", now=datetime(2026, 5, 26, 12))
    summary = summarize_usage(filtered)

    assert len(filtered) == 2
    assert summary["total"] == 2
    assert summary["errors"] == 1
    assert summary["success_rate"] == 50.0
    assert summary["by_provider"] == {"Google Gemini": 2}
    assert summary["by_kind"]["generate_with_image"] == 1
    assert summary["tokens_estimated"] is True
    assert summary["cost_usd"] > 0


def test_v5_usage_export_csv_uses_normalized_columns(tmp_path: Path):
    out = tmp_path / "usage.csv"
    count = export_usage_csv([_entry("2026-05-26T08:00:00")], out)

    assert count == 1
    with out.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["provider"] == "Google Gemini"
    assert rows[0]["tokens_in"] == "1000"
    assert rows[0]["tokens_estimated"] == "True"


def test_v5_usage_quota_warnings_are_injected_and_sorted():
    def fake_quota(provider: str, model: str) -> dict:
        level = "danger" if "pro" in model else "ok"
        percent = 97 if level == "danger" else 12
        return {
            "provider": provider,
            "model": model,
            "used_today": percent,
            "limit_today": 100,
            "percent": percent,
            "level": level,
        }

    statuses = quota_warnings(
        [
            _entry("2026-05-26T08:00:00", model="gemini-2.5-flash"),
            _entry("2026-05-26T09:00:00", model="gemini-2.5-pro"),
        ],
        quota_lookup=fake_quota,
    )

    assert [s["level"] for s in statuses] == ["danger", "ok"]
    assert statuses[0]["model"] == "gemini-2.5-pro"


def test_v5_tracking_wires_ctk_ai_usage_detail_dialog():
    root = Path(__file__).resolve().parents[1]
    tracking = (root / "v5" / "views" / "tracking.py").read_text(encoding="utf-8")
    dialog = (root / "v5" / "ai_usage_dialog.py").read_text(encoding="utf-8")

    assert "open_ai_usage_dialog" in tracking
    assert "AIUsageDialog" in tracking
    assert "export_usage_csv" in dialog
    assert "quota_warnings" in dialog
    assert "clear_log" in dialog
    assert "ui.tab_ai_usage" not in dialog
