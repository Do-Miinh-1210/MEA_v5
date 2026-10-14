"""Data safeguards used before launching a desktop application update."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from services.local_backup import create_local_backup
from services.task_events import record_task_event


DEFAULT_KEEP_SNAPSHOTS = 5


@dataclass(frozen=True)
class PreUpdateSnapshot:
    path: Path
    file_count: int
    total_bytes: int
    target_version: str
    removed_old_snapshots: int


def _default_app_dir() -> Path:
    from config import APP_DIR
    return Path(APP_DIR)


def _pre_update_dir(root_dir: Optional[str | Path] = None) -> Path:
    root = Path(root_dir) if root_dir is not None else _default_app_dir()
    return root.expanduser() / "backups" / "pre_updates"


def prune_pre_update_snapshots(
    *,
    output_dir: Optional[str | Path] = None,
    keep: int = DEFAULT_KEEP_SNAPSHOTS,
) -> int:
    """Keep only the newest pre-update archives inside the dedicated folder."""
    directory = (
        Path(output_dir).expanduser()
        if output_dir is not None
        else _pre_update_dir()
    )
    if directory.name != "pre_updates":
        raise ValueError(f"Thư mục snapshot cập nhật không hợp lệ: {directory}")
    if not directory.exists():
        return 0

    keep_count = max(1, int(keep))
    archives = sorted(
        (path for path in directory.glob("MEA_backup_*.zip") if path.is_file()),
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )
    removed = 0
    resolved_dir = directory.resolve()
    for path in archives[keep_count:]:
        if path.resolve().parent != resolved_dir:
            continue
        path.unlink()
        removed += 1
    return removed


def prepare_pre_update_snapshot(
    target_version: str,
    *,
    root_dir: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
    keep: int = DEFAULT_KEEP_SNAPSHOTS,
    task_log_path: Optional[str | Path] = None,
    now: Optional[datetime] = None,
) -> PreUpdateSnapshot:
    """Create a full local data snapshot before launching an installer."""
    root = Path(root_dir) if root_dir is not None else _default_app_dir()
    root = root.expanduser()
    out = Path(output_dir).expanduser() if output_dir is not None else _pre_update_dir(root)
    if out.name != "pre_updates":
        raise ValueError(f"Thư mục snapshot cập nhật không hợp lệ: {out}")

    version = str(target_version or "").strip() or "unknown"
    record_task_event(
        kind="pre_update_backup",
        title="Snapshot trước cập nhật",
        status="started",
        message=f"Chuẩn bị nâng cấp lên v{version}",
        meta={"target_version": version},
        log_path=task_log_path,
        now=now,
    )
    try:
        result = create_local_backup(
            root_dir=root,
            output_dir=out,
            include_sensitive=True,
            metadata={"kind": "pre_update", "target_version": version},
            now=now,
        )
        removed = prune_pre_update_snapshots(output_dir=out, keep=keep)
        record_task_event(
            kind="pre_update_backup",
            title="Snapshot trước cập nhật",
            status="success",
            message=f"{result.file_count} file, {result.total_bytes / 1048576:.2f} MB",
            meta={
                "path": str(result.path),
                "target_version": version,
                "removed_old_snapshots": removed,
            },
            log_path=task_log_path,
            now=now,
        )
        return PreUpdateSnapshot(
            path=result.path,
            file_count=result.file_count,
            total_bytes=result.total_bytes,
            target_version=version,
            removed_old_snapshots=removed,
        )
    except Exception as exc:
        record_task_event(
            kind="pre_update_backup",
            title="Snapshot trước cập nhật",
            status="error",
            message=str(exc),
            meta={"target_version": version},
            log_path=task_log_path,
            now=now,
        )
        raise
