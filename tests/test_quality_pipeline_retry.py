"""
tests/test_quality_pipeline_retry.py -- Retry/backoff behavior for QC AI calls.
"""
from __future__ import annotations

from core.quality_pipeline import _call_ai_with_retry


def test_call_ai_with_retry_recovers_from_transient_error():
    calls = {"n": 0}
    retries: list[tuple[int, float, str]] = []

    def flaky(_prompt: str) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("429 quota exceeded")
        return "ok"

    result = _call_ai_with_retry(
        flaky,
        "prompt",
        retry_delays=(0,),
        on_retry=lambda attempt, wait, err: retries.append((attempt, wait, err)),
    )

    assert result == "ok"
    assert calls["n"] == 2
    assert retries == [(1, 0.0, "429 quota exceeded")]


def test_call_ai_with_retry_does_not_retry_non_transient_error():
    calls = {"n": 0}

    def broken(_prompt: str) -> str:
        calls["n"] += 1
        raise ValueError("bad prompt")

    try:
        _call_ai_with_retry(broken, "prompt", retry_delays=(0, 0))
    except ValueError as exc:
        assert str(exc) == "bad prompt"
    else:
        raise AssertionError("Expected non-transient error to be raised")

    assert calls["n"] == 1
