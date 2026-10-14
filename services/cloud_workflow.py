"""
services/cloud_workflow.py — v4.2 Cloud Workflow helpers.

Các hàm trong module này không biết Tkinter. UI truyền progress callback/cancel
event vào để sync cloud theo batch mà không treo giao diện.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Optional


ProgressCallback = Callable[[dict[str, Any]], None]


@dataclass
class CloudSyncResult:
    ok: bool = True
    total: int = 0
    processed: int = 0
    added: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    cancelled: bool = False

    @property
    def message(self) -> str:
        if self.cancelled:
            return f"Đã hủy sau {self.processed}/{self.total} câu."
        if not self.ok:
            return self.errors[0] if self.errors else "Cloud sync lỗi."
        return f"Đã upload {self.added} câu, bỏ qua {self.skipped} câu."


@dataclass
class CloudDownloadResult:
    ok: bool = True
    total: int = 0
    processed: int = 0
    questions: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    cancelled: bool = False

    @property
    def message(self) -> str:
        if self.cancelled:
            return f"Đã hủy tải sau {self.processed}/{self.total} câu."
        if not self.ok:
            return self.errors[0] if self.errors else "Tải cloud lỗi."
        return f"Đã tải {self.processed}/{self.total} câu từ cloud."


@dataclass
class ConflictSummary:
    total: int = 0
    new_count: int = 0
    same_count: int = 0
    conflict_count: int = 0
    missing_id_count: int = 0
    conflict_ids: list[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return self.conflict_count > 0


@dataclass
class ConflictDetail:
    question_id: str
    changed_fields: list[str] = field(default_factory=list)
    local_preview: str = ""
    cloud_preview: str = ""
    local_question: dict = field(default_factory=dict)
    cloud_question: dict = field(default_factory=dict)


@dataclass
class ConflictResolutionResult:
    questions: list[dict] = field(default_factory=list)
    new_count: int = 0
    same_count: int = 0
    conflict_count: int = 0
    copied_cloud: int = 0
    accepted_cloud: int = 0
    kept_local: int = 0
    missing_id_count: int = 0

    @property
    def total_input(self) -> int:
        return self.new_count + self.same_count + self.conflict_count

    @property
    def message(self) -> str:
        parts = [f"import {len(self.questions)} cau"]
        if self.copied_cloud:
            parts.append(f"{self.copied_cloud} ban cloud copy")
        if self.accepted_cloud:
            parts.append(f"{self.accepted_cloud} ghi nhan cloud")
        if self.kept_local:
            parts.append(f"{self.kept_local} giu local")
        if self.same_count:
            parts.append(f"{self.same_count} bo qua do trung")
        if self.missing_id_count:
            parts.append(f"{self.missing_id_count} thieu ID")
        return " | ".join(parts)


def _chunks(items: list[dict], size: int) -> Iterable[list[dict]]:
    size = max(1, int(size or 1))
    for i in range(0, len(items), size):
        yield items[i:i + size]


def _is_transient_error(message: str) -> bool:
    msg = (message or "").lower()
    return any(k in msg for k in ("429", "quota", "rate", "timeout", "503", "502", "unavailable"))


def _emit(progress_cb: Optional[ProgressCallback], **event: Any) -> None:
    if progress_cb:
        progress_cb(event)


def upload_questions_with_progress(
    questions: list[dict],
    *,
    mid: str,
    uploader_name: str = "",
    batch_size: int = 40,
    retry_delays: tuple[float, ...] = (2.0, 5.0),
    cancel_event=None,
    progress_cb: Optional[ProgressCallback] = None,
    upload_batch_fn: Optional[Callable[[list[dict], str, str], dict]] = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> CloudSyncResult:
    """Upload NHCH theo batch, có progress/retry/cancel.

    `upload_batch_fn` mặc định là `license_manager.nhch_upload_batch`.
    """
    total = len(questions or [])
    result = CloudSyncResult(total=total)
    if total == 0:
        _emit(progress_cb, stage="done", done=0, total=0, pct=100, message="Không có câu để upload.")
        return result

    if upload_batch_fn is None:
        from services.license_manager import nhch_upload_batch

        upload_batch_fn = nhch_upload_batch

    started = time.monotonic()
    processed = 0
    _emit(progress_cb, stage="prepare", done=0, total=total, pct=0, message=f"Chuẩn bị upload {total} câu...")

    for batch_index, batch in enumerate(_chunks(questions, batch_size), 1):
        if cancel_event is not None and cancel_event.is_set():
            result.cancelled = True
            result.ok = False
            break

        attempts = 0
        while True:
            attempts += 1
            pct = int(processed / total * 100)
            _emit(
                progress_cb,
                stage="upload",
                batch=batch_index,
                done=processed,
                total=total,
                pct=pct,
                message=f"☁️ Upload batch {batch_index}: {processed}/{total} câu...",
            )
            try:
                res = upload_batch_fn(batch, mid, uploader_name)
            except Exception as exc:
                res = {"ok": False, "error": str(exc), "added": 0, "skipped": 0}

            if res.get("ok"):
                result.added += int(res.get("added", res.get("saved", 0)) or 0)
                result.skipped += int(res.get("skipped", 0) or 0)
                processed += len(batch)
                result.processed = processed
                elapsed = max(time.monotonic() - started, 0.1)
                rate = processed / elapsed
                remain = int((total - processed) / rate) if rate > 0 else 0
                _emit(
                    progress_cb,
                    stage="progress",
                    batch=batch_index,
                    done=processed,
                    total=total,
                    pct=int(processed / total * 100),
                    added=result.added,
                    skipped=result.skipped,
                    eta_seconds=remain,
                    message=f"☁️ Đã upload {processed}/{total} câu, ETA ~{remain}s",
                )
                break

            err = str(res.get("error") or "Cloud sync lỗi")
            can_retry = _is_transient_error(err) and attempts <= len(retry_delays)
            if not can_retry:
                result.ok = False
                result.errors.append(err)
                processed += len(batch)
                result.processed = processed
                break

            wait = retry_delays[attempts - 1]
            _emit(
                progress_cb,
                stage="retry",
                batch=batch_index,
                done=processed,
                total=total,
                pct=int(processed / total * 100),
                retry=attempts,
                wait_seconds=wait,
                error=err,
                message=f"Cloud bận/quota, thử lại batch {batch_index} sau {int(wait)}s...",
            )
            sleep_fn(wait)

        if not result.ok and result.errors:
            break

    if result.cancelled:
        _emit(progress_cb, stage="cancelled", done=result.processed, total=total, pct=int(result.processed / total * 100), message=result.message)
    elif result.ok:
        result.processed = total
        _emit(progress_cb, stage="done", done=total, total=total, pct=100, added=result.added, skipped=result.skipped, message=result.message)
    else:
        _emit(progress_cb, stage="error", done=result.processed, total=total, pct=int(result.processed / total * 100), error=result.message, message=result.message)

    return result


def download_questions_with_progress(
    *,
    subject: str = "",
    grade: str = "",
    level: str = "",
    qtype: str = "",
    limit: int = 200,
    page_size: int = 100,
    cancel_event=None,
    progress_cb: Optional[ProgressCallback] = None,
    list_fn: Optional[Callable[..., list[dict]]] = None,
) -> CloudDownloadResult:
    """Download NHCH with UI-friendly progress/cancel events.

    Supabase currently exposes one list call in `license_manager.nhch_list`; this
    helper wraps that call and then processes the returned questions in batches
    so the UI can show progress, ETA and cancellation consistently.
    """
    limit = max(1, int(limit or 200))
    page_size = max(1, int(page_size or 100))
    result = CloudDownloadResult(total=limit)

    if list_fn is None:
        from services.license_manager import nhch_list

        list_fn = nhch_list

    if cancel_event is not None and cancel_event.is_set():
        result.ok = False
        result.cancelled = True
        _emit(progress_cb, stage="cancelled", done=0, total=limit, pct=0, message=result.message)
        return result

    started = time.monotonic()
    _emit(
        progress_cb,
        stage="fetch",
        done=0,
        total=limit,
        pct=0,
        message=f"Đang tải tối đa {limit} câu từ cloud...",
    )

    try:
        fetched = list_fn(subject=subject, grade=grade, level=level, qtype=qtype, limit=limit)
    except Exception as exc:
        result.ok = False
        result.errors.append(str(exc))
        _emit(progress_cb, stage="error", done=0, total=limit, pct=0, error=str(exc), message=result.message)
        return result

    questions = list(fetched or [])[:limit]
    result.total = len(questions)
    if not questions:
        result.processed = 0
        _emit(progress_cb, stage="done", done=0, total=0, pct=100, message="Không tìm thấy câu nào trên cloud.")
        return result

    processed_questions: list[dict] = []
    for batch in _chunks(questions, page_size):
        if cancel_event is not None and cancel_event.is_set():
            result.ok = False
            result.cancelled = True
            break

        processed_questions.extend(batch)
        result.processed = len(processed_questions)
        elapsed = max(time.monotonic() - started, 0.1)
        rate = result.processed / elapsed
        remain = int((result.total - result.processed) / rate) if rate > 0 else 0
        _emit(
            progress_cb,
            stage="progress",
            done=result.processed,
            total=result.total,
            pct=int(result.processed / result.total * 100),
            eta_seconds=remain,
            message=f"Đã tải {result.processed}/{result.total} câu, ETA ~{remain}s",
        )

    result.questions = processed_questions
    if result.cancelled:
        _emit(
            progress_cb,
            stage="cancelled",
            done=result.processed,
            total=result.total,
            pct=int(result.processed / max(result.total, 1) * 100),
            message=result.message,
        )
    else:
        result.ok = True
        result.processed = result.total
        result.questions = questions
        _emit(progress_cb, stage="done", done=result.total, total=result.total, pct=100, message=result.message)
    return result


def _question_id(q: dict) -> str:
    return str(q.get("question_id") or q.get("qid") or "").strip()


def _load_local_questions() -> list[dict]:
    try:
        from storage.database import search_questions

        return search_questions(limit=50000)
    except Exception:
        return []


def _fingerprint(q: dict) -> str:
    opts = q.get("options") if "options" in q else q.get("options_json")
    if isinstance(opts, str):
        try:
            opts = json.loads(opts)
        except Exception:
            pass
    payload = {
        "qtype": q.get("qtype") or q.get("type") or "",
        "level": q.get("level") or "",
        "topic": q.get("topic") or "",
        "question": q.get("question") or "",
        "options": opts or {},
        "answer": q.get("answer") or "",
        "solution": q.get("solution") or "",
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)


def _field_value(q: dict, field_name: str) -> Any:
    if field_name == "options":
        opts = q.get("options") if "options" in q else q.get("options_json")
        if isinstance(opts, str):
            try:
                return json.loads(opts)
            except Exception:
                return opts
        return opts or {}
    return q.get(field_name) or ""


def _question_preview(q: dict, limit: int = 120) -> str:
    text = str(q.get("question") or q.get("content") or q.get("prompt") or "").strip()
    text = " ".join(text.split())
    return text[:limit] + ("..." if len(text) > limit else "")


def build_conflict_details(
    cloud_questions: list[dict],
    local_questions: Optional[list[dict]] = None,
    *,
    limit: int = 50,
) -> list[ConflictDetail]:
    """Return per-question conflict details for the cloud import resolver."""
    if local_questions is None:
        local_questions = _load_local_questions()

    local_by_id = {_question_id(q): q for q in (local_questions or []) if _question_id(q)}
    details: list[ConflictDetail] = []
    compare_fields = ("qtype", "level", "topic", "question", "options", "answer", "solution")

    for cloud_q in cloud_questions or []:
        qid = _question_id(cloud_q)
        if not qid:
            continue
        local_q = local_by_id.get(qid)
        if not local_q or _fingerprint(cloud_q) == _fingerprint(local_q):
            continue

        changed = [
            field_name
            for field_name in compare_fields
            if _field_value(cloud_q, field_name) != _field_value(local_q, field_name)
        ]
        details.append(ConflictDetail(
            question_id=qid,
            changed_fields=changed,
            local_preview=_question_preview(local_q),
            cloud_preview=_question_preview(cloud_q),
            local_question=local_q,
            cloud_question=cloud_q,
        ))
        if len(details) >= limit:
            break
    return details


def format_conflict_details(details: list[ConflictDetail], max_items: int = 5) -> str:
    if not details:
        return ""
    lines: list[str] = []
    for item in details[:max_items]:
        fields = ", ".join(item.changed_fields) if item.changed_fields else "noi dung"
        lines.append(f"- {item.question_id}: khac {fields}")
        if item.local_preview:
            lines.append(f"  Local: {item.local_preview}")
        if item.cloud_preview:
            lines.append(f"  Cloud: {item.cloud_preview}")
    if len(details) > max_items:
        lines.append(f"... va {len(details) - max_items} cau khac")
    return "\n".join(lines)


def resolve_cloud_import(
    cloud_questions: list[dict],
    local_questions: Optional[list[dict]] = None,
    *,
    decisions: Optional[dict[str, str]] = None,
    default_conflict_action: str = "copy",
) -> ConflictResolutionResult:
    """Resolve NHCH cloud import conflicts before saving to local DB.

    Actions:
      - copy: import cloud as a separate question_id.
      - skip/local: keep local and do not import the conflicted cloud question.
      - cloud/replace: keep the cloud question_id in the returned list. The caller
        is responsible for performing an actual replace if its storage supports it.
    """
    if local_questions is None:
        local_questions = _load_local_questions()

    decisions = decisions or {}
    default_conflict_action = (default_conflict_action or "copy").lower()
    local_by_id = {_question_id(q): q for q in (local_questions or []) if _question_id(q)}
    result = ConflictResolutionResult()
    copy_index = 1

    for cloud_q in cloud_questions or []:
        qid = _question_id(cloud_q)
        if not qid:
            result.missing_id_count += 1
            result.new_count += 1
            result.questions.append(dict(cloud_q))
            continue

        local_q = local_by_id.get(qid)
        if not local_q:
            result.new_count += 1
            result.questions.append(dict(cloud_q))
            continue

        if _fingerprint(cloud_q) == _fingerprint(local_q):
            result.same_count += 1
            continue

        result.conflict_count += 1
        action = (decisions.get(qid) or default_conflict_action).lower()
        if action in {"skip", "local", "keep_local"}:
            result.kept_local += 1
            continue
        if action in {"cloud", "replace", "use_cloud"}:
            result.accepted_cloud += 1
            result.questions.append(dict(cloud_q))
            continue

        cloud_copy = dict(cloud_q)
        source_id = qid
        cloud_copy["_source_question_id"] = source_id
        cloud_copy["_cloud_conflict_copy"] = True
        cloud_copy["question_id"] = f"{source_id}-CLOUD-{copy_index:02d}"
        copy_index += 1
        result.copied_cloud += 1
        result.questions.append(cloud_copy)

    return result


def summarize_cloud_import(
    cloud_questions: list[dict],
    local_questions: Optional[list[dict]] = None,
) -> ConflictSummary:
    """So sánh cloud questions với local questions theo `question_id`.

    Nếu `local_questions` không truyền vào, hàm tự đọc NHCH local.
    """
    if local_questions is None:
        local_questions = _load_local_questions()

    local_by_id = {_question_id(q): q for q in (local_questions or []) if _question_id(q)}
    summary = ConflictSummary(total=len(cloud_questions or []))

    for q in cloud_questions or []:
        qid = _question_id(q)
        if not qid:
            summary.missing_id_count += 1
            summary.new_count += 1
            continue
        local = local_by_id.get(qid)
        if not local:
            summary.new_count += 1
            continue
        if _fingerprint(q) == _fingerprint(local):
            summary.same_count += 1
        else:
            summary.conflict_count += 1
            if len(summary.conflict_ids) < 10:
                summary.conflict_ids.append(qid)
    return summary


def format_conflict_summary(summary: ConflictSummary) -> str:
    parts = [
        f"Mới: {summary.new_count}",
        f"Đã có giống: {summary.same_count}",
        f"Xung đột: {summary.conflict_count}",
    ]
    if summary.missing_id_count:
        parts.append(f"Thiếu ID: {summary.missing_id_count}")
    return " │ ".join(parts)
