"""Compatibility facade for the V5 local backup service.

New V5 surfaces call :mod:`services.local_backup` directly.  These helpers
remain for older callers while sharing the same path validation, secret
handling and restore-point behavior.
"""
from __future__ import annotations

import logging
from pathlib import Path

from services.local_backup import (
    create_local_backup,
    iter_backup_sources,
    preview_local_backup,
    restore_local_backup,
)


_log = logging.getLogger(__name__)


def list_backup_files(include_sensitive: bool = False) -> list[Path]:
    """Return files included by the current V5 backup policy."""
    return iter_backup_sources(include_sensitive=include_sensitive)


def export_backup(
    output_path: str | None = None,
    include_sensitive: bool = False,
) -> str | None:
    """Create a safe backup, preserving the legacy optional output path API."""
    try:
        target = Path(output_path).expanduser() if output_path else None
        result = create_local_backup(
            output_dir=target.parent if target else None,
            include_sensitive=include_sensitive,
        )
        path = result.path
        if target is not None and path.resolve() != target.resolve():
            target.parent.mkdir(parents=True, exist_ok=True)
            path.replace(target)
            path = target
        return str(path)
    except Exception as exc:
        _log.warning("export_backup fail: %s", exc)
        return None


def inspect_backup(zip_path: str) -> dict | None:
    """Return preview metadata in the shape expected by legacy callers."""
    try:
        preview = preview_local_backup(zip_path)
        return {
            "created_at": preview.created_at,
            "include_sensitive": preview.include_sensitive,
            "files": [
                {"name": item.get("path", ""), "size": item.get("bytes", 0)}
                for item in preview.files
            ],
            "warnings": preview.warnings,
        }
    except Exception as exc:
        _log.warning("inspect_backup fail: %s", exc)
        return None


def import_backup(zip_path: str, *, make_safety_copy: bool = True) -> bool:
    """Restore through the service validation and restore-point policy."""
    try:
        restore_local_backup(
            zip_path,
            overwrite=True,
            create_restore_point=make_safety_copy,
        )
        return True
    except Exception as exc:
        _log.warning("import_backup fail: %s", exc)
        return False
