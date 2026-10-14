"""Regression tests for the shared V4 desktop updater service."""
from __future__ import annotations

from pathlib import Path

from services import updater


ROOT = Path(__file__).resolve().parents[1]


def _info(version: str = "4.2.3", **updates) -> dict:
    data = {
        "version": version,
        "latest": version,
        "current": "4.2.2",
        "changelog": "Fixes",
        "notes": "Fixes",
        "release_notes": "Fixes",
        "download_url": "https://example.test/MEA_v4_Setup.exe",
        "file_size": 1024,
        "file_hash": "",
        "min_version": "",
        "is_mandatory": False,
        "asset_name": "MEA_v4_Setup.exe",
        "source": "endpoint",
    }
    data.update(updates)
    return data


def test_v4_updater_orders_alpha_beta_rc_and_stable_versions():
    assert updater._parse_version("4.2.3-alpha") < updater._parse_version("4.2.3-beta")
    assert updater._parse_version("4.2.3-beta") < updater._parse_version("4.2.3-rc1")
    assert updater._parse_version("4.2.3-rc1") < updater._parse_version("4.2.3")
    assert updater.is_newer("v4.2.3-alpha", "4.2.2")
    assert not updater.is_newer("4.2.2", "4.2.2")


def test_v4_updater_normalizes_backend_payload_and_prefers_setup_asset():
    info = updater._normalize_info(
        {
            "ok": True,
            "data": {
                "latest": "4.2.3",
                "release_notes": "Nội dung release",
                "assets": [
                    {
                        "name": "MEA_v4_Admin.exe",
                        "download_url": "https://example.test/admin.exe",
                        "size": 10,
                    },
                    {
                        "name": "MEA_v4_Setup.exe",
                        "download_url": "https://example.test/setup.exe",
                        "size": 20,
                    },
                ],
            },
        },
        source="lms",
    )

    assert info is not None
    assert info["version"] == "4.2.3"
    assert info["download_url"] == "https://example.test/setup.exe"
    assert info["asset_name"] == "MEA_v4_Setup.exe"
    assert info["release_notes"] == "Nội dung release"


def test_v4_updater_prefers_custom_endpoint_before_lms_and_github(monkeypatch):
    calls: list[tuple[str, str]] = []
    monkeypatch.delenv("MEA_UPDATE_URL_V4", raising=False)
    monkeypatch.setenv("MEA_UPDATE_URL", "https://updates.example.test/latest")
    monkeypatch.setattr(
        updater,
        "_check_endpoint",
        lambda url, *, source="endpoint": calls.append((source, url)) or _info(source=source),
    )
    monkeypatch.setattr(updater, "_check_lms_backend", lambda: (_ for _ in ()).throw(AssertionError("LMS should not run")))
    monkeypatch.setattr(updater, "_check_github", lambda _repo: (_ for _ in ()).throw(AssertionError("GitHub should not run")))
    monkeypatch.setattr(updater, "_is_skipped", lambda _version: False)

    result = updater.check_for_update(current_version="4.2.2")

    assert result is not None
    assert result["source"] == "endpoint"
    assert calls == [("endpoint", "https://updates.example.test/latest")]


def test_v4_updater_prefers_v4_endpoint_before_generic(monkeypatch):
    calls: list[str] = []
    monkeypatch.setenv("MEA_UPDATE_URL_V4", "https://updates.example.test/v4.json")
    monkeypatch.setenv("MEA_UPDATE_URL", "https://updates.example.test/generic.json")
    monkeypatch.setattr(
        updater,
        "_check_endpoint",
        lambda url, *, source="endpoint": calls.append(url) or _info(source=source),
    )
    monkeypatch.setattr(updater, "_check_lms_backend", lambda: (_ for _ in ()).throw(AssertionError("LMS should not run")))
    monkeypatch.setattr(updater, "_check_github", lambda _repo: (_ for _ in ()).throw(AssertionError("GitHub should not run")))
    monkeypatch.setattr(updater, "_is_skipped", lambda _version: False)

    result = updater.check_for_update(current_version="4.2.2")

    assert result is not None
    assert result["source"] == "endpoint"
    assert calls == ["https://updates.example.test/v4.json"]


def test_v4_updater_ignores_v5_manifest():
    info = updater._normalize_info(
        {
            "version": "5.1.74-alpha",
            "channel": "v5",
            "asset_name": "MEA_v5_alpha.exe",
            "download_url": "https://example.test/MEA_v5_alpha.exe",
        },
        source="endpoint",
    )

    assert info is None


def test_v4_lms_update_check_tries_v4_channel_before_generic(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr("services.api_client.api_url", lambda: "https://lms.example.test")

    def fake_endpoint(url: str, *, source: str = "lms"):
        calls.append(url)
        if url.endswith("/v1/desktop/version/v4"):
            return _info(source=source)
        return None

    monkeypatch.setattr(updater, "_check_endpoint", fake_endpoint)

    assert updater._check_lms_backend()["source"] == "lms"
    assert calls == ["https://lms.example.test/v1/desktop/version/v4"]


def test_v4_updater_falls_back_from_lms_to_github_repo(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(updater, "_env_value", lambda _key, default="": default)
    monkeypatch.setattr(updater, "_check_lms_backend", lambda: None)
    monkeypatch.setattr(updater, "_check_github", lambda repo: calls.append(repo) or _info(source="github"))
    monkeypatch.setattr(updater, "_is_skipped", lambda _version: False)

    result = updater.check_for_update(current_version="4.2.2")

    assert result is not None
    assert result["source"] == "github"
    assert calls == ["Do-Miinh-1210/MEA_byDoMiinh"]


def test_v4_updater_skip_is_persisted_and_manual_check_can_show_it(tmp_path, monkeypatch):
    skip_file = tmp_path / "skip_update.txt"
    monkeypatch.setattr(updater, "_SKIP_FILE", skip_file)
    monkeypatch.delenv("MEA_UPDATE_URL_V4", raising=False)
    monkeypatch.setenv("MEA_UPDATE_URL", "https://updates.example.test/latest")
    monkeypatch.setattr(updater, "_check_endpoint", lambda _url, *, source="endpoint": _info(source=source))

    updater.skip_version("4.2.3")

    assert updater._is_skipped("4.2.3")
    assert updater.check_for_update(current_version="4.2.2") is None
    assert updater.check_for_update(current_version="4.2.2", include_skipped=True) is not None

    updater.clear_skip()
    assert not updater._is_skipped("4.2.3")


def test_v4_updater_mandatory_min_version_ignores_skip(monkeypatch):
    monkeypatch.delenv("MEA_UPDATE_URL_V4", raising=False)
    monkeypatch.setenv("MEA_UPDATE_URL", "https://updates.example.test/latest")
    monkeypatch.setattr(
        updater,
        "_check_endpoint",
        lambda _url, *, source="endpoint": _info(source=source, min_version="4.2.3"),
    )
    monkeypatch.setattr(updater, "_is_skipped", lambda _version: True)

    result = updater.check_for_update(current_version="4.2.2")

    assert result is not None
    assert result["is_mandatory"] is True


def test_download_update_normalizes_sha256_prefix():
    digest = "A" * 64

    assert updater.normalize_expected_hash(f"sha256:{digest}") == digest.lower()
    assert updater.normalize_expected_hash(digest) == digest.lower()
    assert updater.normalize_expected_hash("sha256:not-a-real-digest") == ""


def test_download_update_requires_valid_hash_when_requested(tmp_path, monkeypatch):
    monkeypatch.setattr(updater, "_UPDATE_DIR", tmp_path)

    result = updater.download_update(
        "https://example.test/MEA_v4_Setup.exe",
        expected_hash="",
        require_hash=True,
    )

    assert result is None


def test_v4_update_dialog_requires_snapshot_before_installing():
    source = (ROOT / "ui" / "dialog_update.py").read_text(encoding="utf-8")

    backup_call = source.index("prepare_pre_update_snapshot")
    install_call = source.index("install_update")
    assert backup_call < install_call
    assert "require_hash=True" in source
    assert "pre-update-backup" in source
    assert "Cập nhật bị chặn vì chưa tạo được snapshot dữ liệu." in source


def test_v4_lms_update_check_uses_dict_contract_and_native_dialog():
    source = (ROOT / "ui" / "tab_lms_link.py").read_text(encoding="utf-8")

    assert "info.needs_update" not in source
    assert "UpdateDialog(" in source


def test_install_update_with_silent_and_very_silent_flags(tmp_path, monkeypatch):
    exe = tmp_path / "installer.exe"
    exe.write_text("dummy", encoding="utf-8")

    executed_cmd = []

    def fake_popen(cmd, **kwargs):
        executed_cmd.append(list(cmd))
        return None

    monkeypatch.setattr(updater.subprocess, "Popen", fake_popen)

    # Test very_silent
    success = updater.install_update(str(exe), very_silent=True)
    assert success is True
    assert "/VERYSILENT" in executed_cmd[-1]
    assert "/NORESTART" in executed_cmd[-1]

    # Test silent
    success = updater.install_update(str(exe), silent=True)
    assert success is True
    assert "/SILENT" in executed_cmd[-1]


def test_apply_update_downloads_and_executes_silent_installer(monkeypatch):
    executed_cmd = []
    exited = []

    class FakeResponse:
        def __init__(self):
            self._data = [b"chunk1", b"chunk2", b""]
            self._idx = 0

        def read(self, size):
            val = self._data[self._idx]
            self._idx = min(self._idx + 1, len(self._data) - 1)
            return val

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=120: FakeResponse())
    monkeypatch.setattr(updater.subprocess, "Popen", lambda cmd, **kwargs: executed_cmd.append(cmd))
    monkeypatch.setattr(updater.sys, "exit", lambda code: exited.append(code))

    updater.apply_update("https://example.com/test_setup.exe", silent=True)

    assert len(executed_cmd) == 1
    assert "/VERYSILENT" in executed_cmd[0]
    assert "/NORESTART" in executed_cmd[0]
    assert exited == [0]

