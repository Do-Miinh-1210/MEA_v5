"""
services/task_events.py - Lightweight task history for long-running actions.

The log is intentionally append-only JSONL so background jobs can record useful
status without depending on Tkinter widgets. UI surfaces can read the newest
events and show them as a small task center.
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional


_LOG_LOCK = threading.RLock()
_VALID_STATUSES = {"started", "success", "error", "cancelled", "info"}


@dataclass(frozen=True)
class TaskEvent:
    id: str
    kind: str
    title: str
    status: str = "info"
    message: str = ""
    created_at: str = ""
    duration_ms: Optional[int] = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "status": self.status,
            "message": self.message,
            "created_at": self.created_at,
            "duration_ms": self.duration_ms,
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskEvent":
        return cls(
            id=str(data.get("id") or uuid.uuid4().hex),
            kind=str(data.get("kind") or "general"),
            title=str(data.get("title") or data.get("kind") or "Tác vụ"),
            status=_normalize_status(str(data.get("status") or "info")),
            message=str(data.get("message") or ""),
            created_at=str(data.get("created_at") or ""),
            duration_ms=data.get("duration_ms") if data.get("duration_ms") is not None else None,
            meta=data.get("meta") if isinstance(data.get("meta"), dict) else {},
        )


def _default_log_path() -> Path:
    from config import APP_DIR

    return Path(APP_DIR) / "logs" / "task_events.jsonl"


def _normalize_status(status: str) -> str:
    normalized = status.strip().lower()
    return normalized if normalized in _VALID_STATUSES else "info"


def _utc_timestamp(now: Optional[datetime] = None) -> str:
    return (now or datetime.now()).isoformat(timespec="seconds")


def record_task_event(
    *,
    kind: str,
    title: str,
    status: str = "info",
    message: str = "",
    meta: Optional[dict[str, Any]] = None,
    duration_ms: Optional[int] = None,
    log_path: Optional[str | Path] = None,
    now: Optional[datetime] = None,
) -> TaskEvent:
    """Append one task event and return the normalized event object."""
    path = Path(log_path) if log_path is not None else _default_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    event = TaskEvent(
        id=uuid.uuid4().hex,
        kind=str(kind or "general"),
        title=str(title or kind or "Tác vụ"),
        status=_normalize_status(status),
        message=str(message or ""),
        created_at=_utc_timestamp(now),
        duration_ms=duration_ms,
        meta=meta or {},
    )
    payload = json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)
    with _LOG_LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(payload + "\n")
    return event


def list_task_events(
    *,
    limit: int = 100,
    log_path: Optional[str | Path] = None,
) -> list[TaskEvent]:
    """Return newest task events first. Malformed log lines are ignored."""
    path = Path(log_path) if log_path is not None else _default_log_path()
    if not path.exists():
        return []

    events: list[TaskEvent] = []
    with _LOG_LOCK:
        lines = path.read_text(encoding="utf-8").splitlines()
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            if isinstance(raw, dict):
                events.append(TaskEvent.from_dict(raw))
        except json.JSONDecodeError:
            continue
        if len(events) >= limit:
            break
    return events


def clear_task_events(*, log_path: Optional[str | Path] = None) -> int:
    """Clear the task log and return how many events were removed."""
    path = Path(log_path) if log_path is not None else _default_log_path()
    removed = len(list_task_events(limit=100000, log_path=path))
    with _LOG_LOCK:
        if path.exists():
            path.unlink()
    return removed


def format_task_event(event: TaskEvent) -> str:
    bits = [event.created_at or "unknown", event.status.upper(), event.title]
    if event.message:
        bits.append(event.message)
    return " | ".join(bits)


def record_many(events: Iterable[TaskEvent], *, log_path: Optional[str | Path] = None) -> None:
    path = Path(log_path) if log_path is not None else _default_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _LOG_LOCK:
        with path.open("a", encoding="utf-8") as fh:
            for event in events:
                fh.write(json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")
