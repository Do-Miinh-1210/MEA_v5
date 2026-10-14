import threading

from services.cloud_workflow import (
    build_conflict_details,
    download_questions_with_progress,
    format_conflict_details,
    format_conflict_summary,
    resolve_cloud_import,
    summarize_cloud_import,
    upload_questions_with_progress,
)


def test_upload_questions_with_progress_chunks_and_reports_done():
    calls = []
    events = []

    def upload_batch(batch, mid, uploader_name=""):
        calls.append((len(batch), mid, uploader_name))
        return {"ok": True, "added": len(batch), "skipped": 0}

    result = upload_questions_with_progress(
        [{"question_id": f"Q{i}"} for i in range(5)],
        mid="MID-1",
        uploader_name="tester",
        batch_size=2,
        upload_batch_fn=upload_batch,
        progress_cb=events.append,
        sleep_fn=lambda _s: None,
    )

    assert result.ok is True
    assert result.added == 5
    assert [c[0] for c in calls] == [2, 2, 1]
    assert events[-1]["stage"] == "done"
    assert events[-1]["pct"] == 100


def test_upload_questions_retries_transient_error():
    attempts = {"n": 0}
    events = []

    def upload_batch(batch, mid, uploader_name=""):
        attempts["n"] += 1
        if attempts["n"] == 1:
            return {"ok": False, "error": "429 quota exceeded"}
        return {"ok": True, "added": len(batch), "skipped": 0}

    result = upload_questions_with_progress(
        [{"question_id": "Q1"}],
        mid="MID-1",
        upload_batch_fn=upload_batch,
        progress_cb=events.append,
        sleep_fn=lambda _s: None,
    )

    assert result.ok is True
    assert attempts["n"] == 2
    assert any(e["stage"] == "retry" for e in events)


def test_upload_questions_can_cancel_before_first_batch():
    cancel = threading.Event()
    cancel.set()
    calls = []

    result = upload_questions_with_progress(
        [{"question_id": "Q1"}],
        mid="MID-1",
        upload_batch_fn=lambda batch, mid, uploader_name="": calls.append(batch),
        cancel_event=cancel,
    )

    assert result.ok is False
    assert result.cancelled is True
    assert calls == []


def test_download_questions_with_progress_reports_batches():
    events = []

    def list_fn(subject="", grade="", level="", qtype="", limit=200):
        assert subject == "Toán"
        assert grade == "12"
        return [{"question_id": f"Q{i}"} for i in range(5)]

    result = download_questions_with_progress(
        subject="Toán",
        grade="12",
        limit=10,
        page_size=2,
        list_fn=list_fn,
        progress_cb=events.append,
    )

    assert result.ok is True
    assert result.processed == 5
    assert len(result.questions) == 5
    assert [e["stage"] for e in events].count("progress") == 3
    assert events[-1]["stage"] == "done"


def test_download_questions_can_cancel_before_fetch():
    cancel = threading.Event()
    cancel.set()
    calls = []

    result = download_questions_with_progress(
        list_fn=lambda **kwargs: calls.append(kwargs),
        cancel_event=cancel,
    )

    assert result.ok is False
    assert result.cancelled is True
    assert calls == []


def test_summarize_cloud_import_detects_same_new_and_conflict():
    local = [
        {"question_id": "A", "question": "1+1?", "answer": "2"},
        {"question_id": "B", "question": "2+2?", "answer": "4"},
    ]
    cloud = [
        {"question_id": "A", "question": "1+1?", "answer": "2"},
        {"question_id": "B", "question": "2+2?", "answer": "5"},
        {"question_id": "C", "question": "3+3?", "answer": "6"},
    ]

    summary = summarize_cloud_import(cloud, local)

    assert summary.same_count == 1
    assert summary.conflict_count == 1
    assert summary.new_count == 1
    assert summary.conflict_ids == ["B"]
    assert "Xung" in format_conflict_summary(summary)


def test_build_conflict_details_reports_changed_fields_and_previews():
    local = [{"question_id": "B", "question": "2+2?", "answer": "4", "topic": "So hoc"}]
    cloud = [{"question_id": "B", "question": "2+2 bang may?", "answer": "5", "topic": "So hoc"}]

    details = build_conflict_details(cloud, local)

    assert len(details) == 1
    assert details[0].question_id == "B"
    assert set(details[0].changed_fields) == {"question", "answer"}
    formatted = format_conflict_details(details)
    assert "B" in formatted
    assert "Cloud:" in formatted


def test_resolve_cloud_import_can_copy_conflicts_as_separate_questions():
    local = [{"question_id": "B", "question": "2+2?", "answer": "4"}]
    cloud = [{"question_id": "B", "question": "2+2?", "answer": "5"}]

    result = resolve_cloud_import(cloud, local, default_conflict_action="copy")

    assert result.conflict_count == 1
    assert result.copied_cloud == 1
    assert result.questions[0]["question_id"].startswith("B-CLOUD-")
    assert result.questions[0]["_source_question_id"] == "B"


def test_resolve_cloud_import_skips_same_and_local_conflicts():
    local = [
        {"question_id": "A", "question": "1+1?", "answer": "2"},
        {"question_id": "B", "question": "2+2?", "answer": "4"},
    ]
    cloud = [
        {"question_id": "A", "question": "1+1?", "answer": "2"},
        {"question_id": "B", "question": "2+2?", "answer": "5"},
        {"question_id": "C", "question": "3+3?", "answer": "6"},
    ]

    result = resolve_cloud_import(cloud, local, default_conflict_action="skip")

    assert result.same_count == 1
    assert result.kept_local == 1
    assert [q["question_id"] for q in result.questions] == ["C"]
