"""Regression tests cho snapshot dữ liệu trước khi cập nhật desktop."""
from __future__ import annotations

import json
import os
import zipfile
from datetime import datetime
from pathlib import Path

import pytest

from services import update_safety
from services.task_events import list_task_events


ROOT = Path(__file__).resolve().parents[1]


def test_prepare_pre_update_snapshot_keeps_sensitive_data_and_skips_installer(tmp_path):
    root = tmp_path / "app"
    root.mkdir()
    (root / "question_bank.db").write_text("db", encoding="utf-8")
    (root / "lms.json").write_text('{"token": "secret"}', encoding="utf-8")
    (root / "keys.enc").write_bytes(b"encrypted")
    (root / "updates").mkdir()
    (root / "updates" / "MEA_v5_Setup.exe").write_bytes(b"large installer")
    output = root / "backups" / "pre_updates"
    log_path = tmp_path / "task_events.jsonl"

    snapshot = update_safety.prepare_pre_update_snapshot(
        "5.1.59-alpha",
        root_dir=root,
        output_dir=output,
        task_log_path=log_path,
        now=datetime(2026, 5, 31, 17, 0, 0),
    )

    assert snapshot.path.exists()
    assert snapshot.target_version == "5.1.59-alpha"
    with zipfile.ZipFile(snapshot.path) as zf:
        names = set(zf.namelist())
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))

    assert {"question_bank.db", "lms.json", "keys.enc"} <= names
    assert "updates/MEA_v5_Setup.exe" not in names
    assert manifest["include_sensitive"] is True
    assert manifest["metadata"] == {
        "kind": "pre_update",
        "target_version": "5.1.59-alpha",
    }
    events = list_task_events(log_path=log_path)
    assert [event.status for event in events] == ["success", "started"]
    assert events[0].meta["path"] == str(snapshot.path)


def test_prune_pre_update_snapshots_keeps_newest_archives(tmp_path):
    output = tmp_path / "backups" / "pre_updates"
    output.mkdir(parents=True)
    archives = []
    for index in range(4):
        path = output / f"MEA_backup_20260531_17000{index}.zip"
        path.write_bytes(b"zip")
        os.utime(path, (index + 1, index + 1))
        archives.append(path)

    removed = update_safety.prune_pre_update_snapshots(output_dir=output, keep=2)

    assert removed == 2
    assert set(output.glob("*.zip")) == {archives[2], archives[3]}


def test_prune_pre_update_snapshots_rejects_unexpected_directory(tmp_path):
    with pytest.raises(ValueError, match="không hợp lệ"):
        update_safety.prune_pre_update_snapshots(output_dir=tmp_path / "backups")


def test_prepare_pre_update_snapshot_records_error_and_reraises(tmp_path, monkeypatch):
    log_path = tmp_path / "task_events.jsonl"
    monkeypatch.setattr(
        update_safety,
        "create_local_backup",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("disk full")),
    )

    with pytest.raises(RuntimeError, match="disk full"):
        update_safety.prepare_pre_update_snapshot(
            "5.1.59-alpha",
            root_dir=tmp_path / "app",
            output_dir=tmp_path / "app" / "backups" / "pre_updates",
            task_log_path=log_path,
        )

    events = list_task_events(log_path=log_path)
    assert [event.status for event in events] == ["error", "started"]
    assert "disk full" in events[0].message


def test_update_dialog_requires_snapshot_before_installing():
    source = (ROOT / "v5" / "update_dialog.py").read_text(encoding="utf-8")

    backup_call = source.index("prepare_pre_update_snapshot")
    install_call = source.index("install_update")
    assert backup_call < install_call
    assert "pre-update-backup" in source
    assert "Cập nhật bị chặn vì chưa tạo được snapshot dữ liệu." in source
