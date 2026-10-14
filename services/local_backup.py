"""
services/local_backup.py - Local data backup helpers.

The module is intentionally UI-free. Callers choose the output folder and can
listen to progress events while the service creates a zip backup of app data.
"""

from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Optional


ProgressCallback = Callable[[dict[str, Any]], None]

_DEFAULT_EXCLUDED_DIRS = {"cache", "backups", "updates", "__pycache__"}
_EXPORTS_DIR_NAME = "exports"
_SENSITIVE_FILES = {"keys.enc", "lms.json"}


@dataclass(frozen=True)
class BackupResult:
    path: Path
    file_count: int
    total_bytes: int
    manifest: dict[str, Any]


@dataclass(frozen=True)
class BackupPreview:
    path: Path
    file_count: int
    total_bytes: int
    created_at: str
    root_dir: str
    include_exports: bool
    include_sensitive: bool
    metadata: dict[str, Any]
    files: list[dict[str, Any]]
    warnings: list[str]


@dataclass(frozen=True)
class RestoreResult:
    path: Path
    restored_count: int
    skipped_count: int
    total_bytes: int
    restore_point: Optional[Path]
    manifest: dict[str, Any]
    warnings: list[str]


def _default_app_dir() -> Path:
    from config import APP_DIR

    return Path(APP_DIR)


def _default_output_dir(root_dir: Optional[Path] = None) -> Path:
    root = Path(root_dir) if root_dir is not None else _default_app_dir()
    return root / "backups"


def _emit(progress_cb: Optional[ProgressCallback], **event: Any) -> None:
    if progress_cb:
        progress_cb(event)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _should_skip_dir(path: Path, root: Path, include_exports: bool) -> bool:
    name = path.name.lower()
    if name in _DEFAULT_EXCLUDED_DIRS:
        return True
    if not include_exports and name == _EXPORTS_DIR_NAME:
        return True
    if _is_relative_to(path, root / "backups"):
        return True
    return False


def iter_backup_sources(
    root_dir: Optional[str | Path] = None,
    *,
    include_exports: bool = False,
    include_sensitive: bool = False,
    extra_paths: Optional[Iterable[str | Path]] = None,
) -> list[Path]:
    """Return files that should be included in a local backup.

    The scan skips volatile/heavy folders by default: cache, backups and
    exports. Exports can be included explicitly when the user needs a full
    archive before moving machines.
    """
    root = Path(root_dir) if root_dir is not None else _default_app_dir()
    root = root.expanduser()
    if not root.exists():
        return []

    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(_should_skip_dir(parent, root, include_exports) for parent in path.parents):
            continue
        if not include_sensitive and path.name.lower() in _SENSITIVE_FILES:
            continue
        if path.is_symlink():
            continue
        files.append(path)

    for raw in extra_paths or []:
        path = Path(raw).expanduser()
        if (
            path.exists() and path.is_file() and not path.is_symlink()
            and (include_sensitive or path.name.lower() not in _SENSITIVE_FILES)
        ):
            files.append(path)

    unique: dict[Path, Path] = {p.resolve(): p for p in files}
    return sorted(unique.values(), key=lambda p: str(p).lower())


def _arcname(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return f"extra/{path.name}"


def _is_manifest_member(member_name: str) -> bool:
    return member_name.replace("\\", "/").strip("/").lower() == "manifest.json"


def _safe_member_relpath(member_name: str) -> Optional[Path]:
    normalized = member_name.replace("\\", "/")
    if not normalized or normalized.startswith("/"):
        return None

    pure = PurePosixPath(normalized)
    if pure.is_absolute():
        return None

    parts = pure.parts
    if not parts:
        return None
    if any(part in {"", ".", ".."} or ":" in part for part in parts):
        return None
    if parts[0].lower() == "manifest.json":
        return None
    return Path(*parts)


def _relpath_to_arcname(path: Path) -> str:
    return PurePosixPath(*path.parts).as_posix()


def _normalize_selected_paths(paths: Optional[Iterable[str | Path]]) -> Optional[set[str]]:
    if paths is None:
        return None

    normalized: set[str] = set()
    for raw in paths:
        rel = _safe_member_relpath(str(raw))
        if rel is not None:
            normalized.add(_relpath_to_arcname(rel))
    return normalized


def _unique_backup_path(output_dir: Path, timestamp: str) -> Path:
    base = output_dir / f"MEA_backup_{timestamp}.zip"
    if not base.exists():
        return base
    for i in range(2, 1000):
        candidate = output_dir / f"MEA_backup_{timestamp}_{i}.zip"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Could not create a unique backup filename.")


def create_local_backup(
    *,
    root_dir: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
    include_exports: bool = False,
    include_sensitive: bool = False,
    extra_paths: Optional[Iterable[str | Path]] = None,
    metadata: Optional[dict[str, Any]] = None,
    progress_cb: Optional[ProgressCallback] = None,
    now: Optional[datetime] = None,
) -> BackupResult:
    """Create a zip backup for MatrixExam AI local data."""
    root = Path(root_dir) if root_dir is not None else _default_app_dir()
    root = root.expanduser()
    out = Path(output_dir) if output_dir is not None else _default_output_dir(root)
    out = out.expanduser()
    out.mkdir(parents=True, exist_ok=True)

    timestamp = (now or datetime.now()).strftime("%Y%m%d_%H%M%S")
    backup_path = _unique_backup_path(out, timestamp)
    sources = iter_backup_sources(
        root,
        include_exports=include_exports,
        include_sensitive=include_sensitive,
        extra_paths=extra_paths,
    )

    _emit(progress_cb, stage="scan", done=0, total=len(sources), pct=0, message=f"Found {len(sources)} files")

    files_meta: list[dict[str, Any]] = []
    total_bytes = 0
    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for index, path in enumerate(sources, 1):
            if not path.exists() or not path.is_file():
                continue
            arcname = _arcname(root, path)
            size = path.stat().st_size
            zf.write(path, arcname)
            files_meta.append({"path": arcname, "bytes": size})
            total_bytes += size
            pct = int(index / max(len(sources), 1) * 100)
            _emit(
                progress_cb,
                stage="add",
                done=index,
                total=len(sources),
                pct=pct,
                path=arcname,
                message=f"Added {index}/{len(sources)} files",
            )

        manifest = {
            "app": "MatrixExamAI",
            "created_at": (now or datetime.now()).isoformat(timespec="seconds"),
            "root_dir": str(root),
            "include_exports": include_exports,
            "include_sensitive": include_sensitive,
            "metadata": dict(metadata or {}),
            "file_count": len(files_meta),
            "total_bytes": total_bytes,
            "files": files_meta,
        }
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    _emit(
        progress_cb,
        stage="done",
        done=len(files_meta),
        total=len(sources),
        pct=100,
        path=str(backup_path),
        message=f"Backup created: {backup_path}",
    )
    return BackupResult(
        path=backup_path,
        file_count=len(files_meta),
        total_bytes=total_bytes,
        manifest=manifest,
    )


def preview_local_backup(backup_path: str | Path) -> BackupPreview:
    """Read backup metadata and list restorable files without writing data."""
    path = Path(backup_path).expanduser()
    warnings: list[str] = []
    manifest: dict[str, Any] = {}
    files: list[dict[str, Any]] = []

    with zipfile.ZipFile(path, "r") as zf:
        if "manifest.json" in zf.namelist():
            try:
                manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                warnings.append(f"manifest.json không đọc được: {exc}")
        else:
            warnings.append("Backup không có manifest.json; sẽ khôi phục theo danh sách file trong zip.")

        for info in zf.infolist():
            if info.is_dir() or _is_manifest_member(info.filename):
                continue
            rel = _safe_member_relpath(info.filename)
            if rel is None:
                warnings.append(f"Bỏ qua đường dẫn không an toàn: {info.filename}")
                continue
            files.append({"path": _relpath_to_arcname(rel), "bytes": int(info.file_size)})

    total_bytes = sum(int(item.get("bytes", 0)) for item in files)
    return BackupPreview(
        path=path,
        file_count=len(files),
        total_bytes=total_bytes,
        created_at=str(manifest.get("created_at", "")),
        root_dir=str(manifest.get("root_dir", "")),
        include_exports=bool(manifest.get("include_exports", False)),
        include_sensitive=bool(manifest.get("include_sensitive", False)),
        metadata=manifest.get("metadata") if isinstance(manifest.get("metadata"), dict) else {},
        files=files,
        warnings=warnings,
    )


def restore_local_backup(
    backup_path: str | Path,
    *,
    target_root: Optional[str | Path] = None,
    selected_paths: Optional[Iterable[str | Path]] = None,
    overwrite: bool = False,
    create_restore_point: bool = True,
    progress_cb: Optional[ProgressCallback] = None,
) -> RestoreResult:
    """Restore files from a MatrixExamAI backup zip into the app data folder.

    The function never trusts zip member paths. Only relative, normalized paths
    are restored and every destination is checked to stay inside ``target_root``.
    """
    path = Path(backup_path).expanduser()
    root = Path(target_root) if target_root is not None else _default_app_dir()
    root = root.expanduser()
    root.mkdir(parents=True, exist_ok=True)

    selected = _normalize_selected_paths(selected_paths)
    preview = preview_local_backup(path)
    manifest = {
        "app": "MatrixExamAI",
        "source_backup": str(path),
        "preview_created_at": preview.created_at,
        "preview_root_dir": preview.root_dir,
        "preview_include_exports": preview.include_exports,
        "preview_include_sensitive": preview.include_sensitive,
        "preview_metadata": dict(preview.metadata),
        "preview_file_count": preview.file_count,
        "preview_total_bytes": preview.total_bytes,
    }
    warnings = list(preview.warnings)

    restore_point: Optional[Path] = None
    if create_restore_point:
        restore_point_result = create_local_backup(
            root_dir=root,
            output_dir=root / "backups" / "restore_points",
            include_exports=True,
            include_sensitive=True,
        )
        restore_point = restore_point_result.path

    with zipfile.ZipFile(path, "r") as zf:
        members: list[tuple[zipfile.ZipInfo, Path, str]] = []
        for info in zf.infolist():
            if info.is_dir() or _is_manifest_member(info.filename):
                continue
            rel = _safe_member_relpath(info.filename)
            if rel is None:
                continue
            arcname = _relpath_to_arcname(rel)
            if selected is not None and arcname not in selected:
                continue
            members.append((info, rel, arcname))

        _emit(
            progress_cb,
            stage="scan",
            done=0,
            total=len(members),
            pct=0,
            message=f"Ready to restore {len(members)} files",
        )

        restored_count = 0
        skipped_count = 0
        total_bytes = 0
        for index, (info, rel, arcname) in enumerate(members, 1):
            dest = (root / rel).resolve()
            if not _is_relative_to(dest, root):
                skipped_count += 1
                warnings.append(f"Bỏ qua đường dẫn vượt ngoài thư mục app: {arcname}")
                continue
            if dest.exists() and not overwrite:
                skipped_count += 1
                _emit(
                    progress_cb,
                    stage="skip",
                    done=index,
                    total=len(members),
                    pct=int(index / max(len(members), 1) * 100),
                    path=arcname,
                    message=f"Skipped existing file: {arcname}",
                )
                continue
            if dest.exists() and dest.is_dir():
                skipped_count += 1
                warnings.append(f"Bỏ qua vì đích là thư mục: {arcname}")
                continue

            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as source, dest.open("wb") as target:
                shutil.copyfileobj(source, target)
            restored_count += 1
            total_bytes += int(info.file_size)
            _emit(
                progress_cb,
                stage="restore",
                done=index,
                total=len(members),
                pct=int(index / max(len(members), 1) * 100),
                path=arcname,
                message=f"Restored {index}/{len(members)} files",
            )

    _emit(
        progress_cb,
        stage="done",
        done=restored_count,
        total=len(members),
        pct=100,
        path=str(path),
        message=f"Restored {restored_count} files",
    )
    manifest.update(
        {
            "restored_count": restored_count,
            "skipped_count": skipped_count,
            "total_bytes": total_bytes,
            "restore_point": str(restore_point) if restore_point else "",
        }
    )
    return RestoreResult(
        path=path,
        restored_count=restored_count,
        skipped_count=skipped_count,
        total_bytes=total_bytes,
        restore_point=restore_point,
        manifest=manifest,
        warnings=warnings,
    )


def list_local_backups(
    *,
    root_dir: Optional[str | Path] = None,
    output_dir: Optional[str | Path] = None,
) -> list[Path]:
    out = Path(output_dir) if output_dir is not None else _default_output_dir(
        Path(root_dir) if root_dir is not None else None
    )
    if not out.exists():
        return []
    return sorted(
        out.glob("MEA_backup_*.zip"),
        key=lambda p: (p.stat().st_mtime, p.name),
        reverse=True,
    )
