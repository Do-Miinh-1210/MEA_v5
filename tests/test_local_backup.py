import json
import zipfile
from datetime import datetime

from services.local_backup import (
    create_local_backup,
    iter_backup_sources,
    list_local_backups,
    preview_local_backup,
    restore_local_backup,
)


def test_iter_backup_sources_skips_cache_backups_and_exports_by_default(tmp_path):
    (tmp_path / "question_bank.db").write_text("db", encoding="utf-8")
    (tmp_path / "app_settings.json").write_text("{}", encoding="utf-8")
    (tmp_path / "sessions").mkdir()
    (tmp_path / "sessions" / "latest.json").write_text("{}", encoding="utf-8")
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "plot.png").write_bytes(b"png")
    (tmp_path / "cache").mkdir()
    (tmp_path / "cache" / "tmp.bin").write_bytes(b"cache")
    (tmp_path / "backups").mkdir()
    (tmp_path / "backups" / "old.zip").write_bytes(b"old")
    (tmp_path / "exports").mkdir()
    (tmp_path / "exports" / "exam.docx").write_bytes(b"docx")
    (tmp_path / "updates").mkdir()
    (tmp_path / "updates" / "MEA_v5_Setup.exe").write_bytes(b"installer")
    (tmp_path / "lms.json").write_text('{"token": "secret"}', encoding="utf-8")
    (tmp_path / "keys.enc").write_bytes(b"encrypted")

    sources = {p.relative_to(tmp_path).as_posix() for p in iter_backup_sources(tmp_path)}

    assert "question_bank.db" in sources
    assert "app_settings.json" in sources
    assert "sessions/latest.json" in sources
    assert "figures/plot.png" in sources
    assert "cache/tmp.bin" not in sources
    assert "backups/old.zip" not in sources
    assert "exports/exam.docx" not in sources
    assert "updates/MEA_v5_Setup.exe" not in sources
    assert "lms.json" not in sources
    assert "keys.enc" not in sources


def test_iter_backup_sources_includes_sensitive_files_only_when_requested(tmp_path):
    (tmp_path / "lms.json").write_text('{"token": "secret"}', encoding="utf-8")
    (tmp_path / "keys.enc").write_bytes(b"encrypted")

    sources = {
        path.relative_to(tmp_path).as_posix()
        for path in iter_backup_sources(tmp_path, include_sensitive=True)
    }

    assert {"lms.json", "keys.enc"} <= sources


def test_create_local_backup_writes_manifest_and_expected_files(tmp_path):
    (tmp_path / "question_bank.db").write_text("db", encoding="utf-8")
    (tmp_path / "sessions").mkdir()
    (tmp_path / "sessions" / "latest.json").write_text('{"ok": true}', encoding="utf-8")
    events = []

    result = create_local_backup(
        root_dir=tmp_path,
        output_dir=tmp_path / "safe",
        progress_cb=events.append,
        now=datetime(2026, 5, 13, 10, 30, 0),
    )

    assert result.path.exists()
    assert result.file_count == 2
    assert events[0]["stage"] == "scan"
    assert events[-1]["stage"] == "done"

    with zipfile.ZipFile(result.path) as zf:
        names = set(zf.namelist())
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))

    assert "question_bank.db" in names
    assert "sessions/latest.json" in names
    assert manifest["file_count"] == 2
    assert manifest["include_exports"] is False
    assert manifest["include_sensitive"] is False


def test_list_local_backups_returns_newest_first(tmp_path):
    older = create_local_backup(
        root_dir=tmp_path,
        output_dir=tmp_path / "backups",
        now=datetime(2026, 5, 13, 9, 0, 0),
    )
    newer = create_local_backup(
        root_dir=tmp_path,
        output_dir=tmp_path / "backups",
        now=datetime(2026, 5, 13, 10, 0, 0),
    )

    backups = list_local_backups(output_dir=tmp_path / "backups")

    assert backups[:2] == [newer.path, older.path]


def test_preview_and_restore_local_backup_roundtrip(tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    (root / "app_settings.json").write_text('{"theme": "dark"}', encoding="utf-8")
    (root / "sessions").mkdir()
    (root / "sessions" / "latest.json").write_text('{"exam": 1}', encoding="utf-8")

    backup = create_local_backup(
        root_dir=root,
        output_dir=tmp_path / "backups",
        now=datetime(2026, 5, 14, 8, 15, 0),
    )
    (root / "app_settings.json").write_text('{"theme": "broken"}', encoding="utf-8")
    (root / "sessions" / "latest.json").unlink()

    preview = preview_local_backup(backup.path)
    events = []
    restored = restore_local_backup(
        backup.path,
        target_root=root,
        overwrite=True,
        create_restore_point=False,
        progress_cb=events.append,
    )

    assert preview.file_count == 2
    assert preview.created_at == "2026-05-14T08:15:00"
    assert restored.restored_count == 2
    assert restored.skipped_count == 0
    assert (root / "app_settings.json").read_text(encoding="utf-8") == '{"theme": "dark"}'
    assert (root / "sessions" / "latest.json").read_text(encoding="utf-8") == '{"exam": 1}'
    assert events[0]["stage"] == "scan"
    assert events[-1]["stage"] == "done"


def test_restore_local_backup_skips_unsafe_zip_members(tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    backup_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps({"created_at": "2026-05-14T09:00:00"}))
        zf.writestr("../evil.txt", "owned")
        zf.writestr("C:evil.txt", "drive-relative")
        zf.writestr("safe/good.txt", "ok")

    preview = preview_local_backup(backup_path)
    restored = restore_local_backup(
        backup_path,
        target_root=root,
        overwrite=True,
        create_restore_point=False,
    )

    assert preview.file_count == 1
    assert any("không an toàn" in warning for warning in preview.warnings)
    assert restored.restored_count == 1
    assert (root / "safe" / "good.txt").read_text(encoding="utf-8") == "ok"
    assert not (tmp_path / "evil.txt").exists()
    assert not (root / "C:evil.txt").exists()


def test_restore_creates_full_restore_point_before_overwrite(tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    (root / "v5_settings.json").write_text('{"theme": "before"}', encoding="utf-8")
    (root / "lms.json").write_text('{"token": "current"}', encoding="utf-8")
    source = tmp_path / "source"
    source.mkdir()
    (source / "v5_settings.json").write_text('{"theme": "after"}', encoding="utf-8")
    backup = create_local_backup(root_dir=source, output_dir=tmp_path / "incoming")

    restored = restore_local_backup(backup.path, target_root=root, overwrite=True)

    assert restored.restore_point is not None
    with zipfile.ZipFile(restored.restore_point) as zf:
        names = set(zf.namelist())
    assert "v5_settings.json" in names
    assert "lms.json" in names
    assert (root / "v5_settings.json").read_text(encoding="utf-8") == '{"theme": "after"}'
