from datetime import datetime

from services.task_events import clear_task_events, format_task_event, list_task_events, record_task_event


def test_record_and_list_task_events_newest_first(tmp_path):
    log_path = tmp_path / "task_events.jsonl"
    older = record_task_event(
        kind="backup",
        title="Tạo backup",
        status="success",
        message="2 file",
        log_path=log_path,
        now=datetime(2026, 5, 14, 8, 0, 0),
    )
    newer = record_task_event(
        kind="restore",
        title="Khôi phục backup",
        status="success",
        message="2 file",
        log_path=log_path,
        now=datetime(2026, 5, 14, 9, 0, 0),
    )

    events = list_task_events(log_path=log_path)

    assert [event.id for event in events] == [newer.id, older.id]
    assert events[0].created_at == "2026-05-14T09:00:00"
    assert "Khôi phục backup" in format_task_event(events[0])


def test_task_events_ignore_malformed_lines_and_clear(tmp_path):
    log_path = tmp_path / "task_events.jsonl"
    record_task_event(kind="cloud", title="Sync cloud", status="not-real", log_path=log_path)
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write("{bad json\n")

    events = list_task_events(log_path=log_path)
    removed = clear_task_events(log_path=log_path)

    assert len(events) == 1
    assert events[0].status == "info"
    assert removed == 1
    assert list_task_events(log_path=log_path) == []
