from __future__ import annotations

from core.models import Question
from core.quality_pipeline import load_qc_checkpoint, run_qc_pipeline_batch


def _question(qid: str, answer: str = "A") -> Question:
    return Question(
        qtype="TN",
        level="NB",
        topic="So hoc",
        question="1+1 bang bao nhieu?",
        options={"A": "2", "B": "3", "C": "4", "D": "5"},
        answer=answer,
        question_id=qid,
    )


def test_qc_batch_writes_and_resumes_checkpoint(tmp_path):
    checkpoint = tmp_path / "qc.json"
    events: list[dict] = []

    first = run_qc_pipeline_batch(
        [_question("Q1")],
        subject="Toan",
        grade="12",
        ai_call=lambda _prompt: "unused",
        run_solver=False,
        run_critic=False,
        run_math=False,
        checkpoint_path=checkpoint,
        checkpoint_cb=events.append,
    )

    assert len(first) == 1
    assert "Q1" in load_qc_checkpoint(checkpoint)["completed"]

    second = run_qc_pipeline_batch(
        [_question("Q1"), _question("Q2")],
        subject="Toan",
        grade="12",
        ai_call=lambda _prompt: "unused",
        run_solver=False,
        run_critic=False,
        run_math=False,
        checkpoint_path=checkpoint,
        resume=True,
        checkpoint_cb=events.append,
    )

    saved = load_qc_checkpoint(checkpoint)["completed"]
    assert len(second) == 2
    assert set(saved) == {"Q1", "Q2"}
    assert any(e["stage"] == "resume" and e["key"] == "Q1" for e in events)


def test_qc_batch_adaptive_backoff_emits_event_after_transient_retries():
    calls = {"n": 0}
    events: list[dict] = []

    def flaky_solver(_prompt: str) -> str:
        calls["n"] += 1
        if calls["n"] <= 2:
            raise RuntimeError("429 quota")
        return """===SOLVE===
CACH_GIAI: 1+1=2
KET_QUA: A
DO_TIN_CAY: 0.95
===END_SOLVE==="""

    run_qc_pipeline_batch(
        [_question("Q1")],
        subject="Toan",
        grade="12",
        ai_call=flaky_solver,
        run_solver=True,
        run_critic=False,
        run_math=False,
        retry_delays=(0, 0),
        adaptive=True,
        checkpoint_cb=events.append,
    )

    assert calls["n"] >= 3
    assert any(e["stage"] == "adaptive_backoff" for e in events)
