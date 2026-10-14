"""Guard tests cho updater CTk-native của desktop V5."""
from __future__ import annotations

from pathlib import Path

from v5 import settings_store
from v5 import updater
from v5.quickswitch import _DEFAULT_ITEMS


ROOT = Path(__file__).resolve().parents[1]


def _info(version: str = "5.1.58-alpha", **updates) -> dict:
    data = {
        "version": version,
        "url": "https://example.test/releases/v5.1.58-alpha",
        "notes": "Sửa lỗi",
        "download_url": "https://example.test/MEA_v5_Setup.exe",
        "file_size": 1024,
        "file_hash": "",
        "min_version": "",
        "is_mandatory": False,
        "asset_name": "MEA_v5_Setup.exe",
        "source": "endpoint",
    }
    data.update(updates)
    return data


def test_v5_updater_orders_alpha_beta_rc_and_stable_versions():
    assert updater._parse_version("5.1.58-alpha") < updater._parse_version("5.1.58-beta")
    assert updater._parse_version("5.1.58-beta") < updater._parse_version("5.1.58-rc1")
    assert updater._parse_version("5.1.58-rc1") < updater._parse_version("5.1.58")
    assert updater._is_newer("v5.1.58-alpha", "5.1.57-alpha")
    assert not updater._is_newer("5.1.57-alpha", "5.1.57-alpha")


def test_v5_updater_normalizes_github_release_and_selects_installer():
    info = updater._normalize_info(
        {
            "tag_name": "v5.1.58-alpha",
            "html_url": "https://github.test/releases/v5.1.58-alpha",
            "body": "Nội dung release",
            "assets": [
                {"name": "source.zip", "browser_download_url": "https://example.test/source.zip"},
                {"name": "MEA_v5_alpha.exe", "browser_download_url": "https://example.test/app.exe", "size": 10},
                {"name": "MEA_v5_Setup.exe", "browser_download_url": "https://example.test/setup.exe", "size": 20},
            ],
        },
        source="github",
    )

    assert info is not None
    assert info["version"] == "5.1.58-alpha"
    assert info["download_url"] == "https://example.test/setup.exe"
    assert info["asset_name"] == "MEA_v5_Setup.exe"
    assert info["notes"] == "Nội dung release"


def test_v5_updater_normalizes_wrapped_lms_payload():
    info = updater._normalize_info(
        {
            "ok": True,
            "data": {
                "latest": "5.1.58-alpha",
                "channel": "v5",
                "release_notes": "LMS release notes",
                "download_url": "https://example.test/MEA_v5_alpha.exe",
                "asset_name": "MEA_v5_alpha.exe",
                "sha256": "abc123",
            },
        },
        source="lms",
    )

    assert info is not None
    assert info["version"] == "5.1.58-alpha"
    assert info["download_url"] == "https://example.test/MEA_v5_alpha.exe"
    assert info["file_hash"] == "abc123"
    assert info["notes"] == "LMS release notes"


def test_v5_updater_prefers_custom_endpoint_before_lms_and_github(monkeypatch):
    calls: list[tuple[str, str]] = []
    monkeypatch.delenv("MEA_UPDATE_URL_V5", raising=False)
    monkeypatch.setenv("MEA_UPDATE_URL", "https://updates.example.test/latest")
    monkeypatch.setattr(
        updater,
        "_check_endpoint",
        lambda url, *, source="endpoint": calls.append((source, url)) or _info(source=source),
    )
    monkeypatch.setattr(updater, "_check_lms_backend", lambda: (_ for _ in ()).throw(AssertionError("LMS should not run")))
    monkeypatch.setattr(updater, "_check_github", lambda _repo: (_ for _ in ()).throw(AssertionError("GitHub should not run")))
    monkeypatch.setattr(updater, "_is_skipped", lambda _version: False)

    result = updater.check_for_update("5.1.57-alpha")

    assert result is not None
    assert result["source"] == "endpoint"
    assert calls == [("endpoint", "https://updates.example.test/latest")]


def test_v5_updater_prefers_v5_endpoint_before_generic(monkeypatch):
    calls: list[str] = []
    monkeypatch.setenv("MEA_UPDATE_URL_V5", "https://updates.example.test/v5.json")
    monkeypatch.setenv("MEA_UPDATE_URL", "https://updates.example.test/generic.json")
    monkeypatch.setattr(
        updater,
        "_check_endpoint",
        lambda url, *, source="endpoint": calls.append(url) or _info(source=source),
    )
    monkeypatch.setattr(updater, "_check_lms_backend", lambda: (_ for _ in ()).throw(AssertionError("LMS should not run")))
    monkeypatch.setattr(updater, "_check_github", lambda _repo: (_ for _ in ()).throw(AssertionError("GitHub should not run")))
    monkeypatch.setattr(updater, "_is_skipped", lambda _version: False)

    result = updater.check_for_update("5.1.57-alpha")

    assert result is not None
    assert result["source"] == "endpoint"
    assert calls == ["https://updates.example.test/v5.json"]


def test_v5_updater_ignores_v4_manifest():
    info = updater._normalize_info(
        {
            "version": "4.2.3",
            "channel": "v4",
            "asset_name": "MEA_v4.exe",
            "download_url": "https://example.test/MEA_v4.exe",
        },
        source="endpoint",
    )

    assert info is None


def test_v5_lms_update_check_tries_v5_channel_before_generic(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr("services.api_client.api_url", lambda: "https://lms.example.test")

    def fake_endpoint(url: str, *, source: str = "lms"):
        calls.append(url)
        if url.endswith("/v1/desktop/version/v5"):
            return _info(source=source)
        return None

    monkeypatch.setattr(updater, "_check_endpoint", fake_endpoint)

    assert updater._check_lms_backend()["source"] == "lms"
    assert calls == ["https://lms.example.test/v1/desktop/version/v5"]


def test_v5_updater_falls_back_from_lms_to_real_github_repo(monkeypatch):
    calls: list[str] = []
    monkeypatch.delenv("MEA_UPDATE_URL_V5", raising=False)
    monkeypatch.delenv("MEA_UPDATE_URL", raising=False)
    monkeypatch.delenv("MEA_GITHUB_REPO_V5", raising=False)
    monkeypatch.delenv("MEA_GITHUB_REPO", raising=False)
    monkeypatch.setattr(updater, "_check_lms_backend", lambda: None)
    monkeypatch.setattr(updater, "_check_github", lambda repo: calls.append(repo) or _info(source="github"))
    monkeypatch.setattr(updater, "_is_skipped", lambda _version: False)

    result = updater.check_for_update("5.1.57-alpha")

    assert result is not None
    assert calls == ["Do-Miinh-1210/MEA_byDoMiinh"]
    assert "placeholder" not in updater.DEFAULT_GITHUB_REPO.lower()


def test_v5_updater_skip_is_persisted_and_manual_check_can_show_it(tmp_path, monkeypatch):
    settings_file = tmp_path / "v5_settings.json"
    monkeypatch.setattr(settings_store, "_FILE", settings_file)
    monkeypatch.delenv("MEA_UPDATE_URL_V5", raising=False)
    monkeypatch.setenv("MEA_UPDATE_URL", "https://updates.example.test/latest")
    monkeypatch.setattr(updater, "_check_endpoint", lambda _url, *, source="endpoint": _info(source=source))

    updater.skip_version("5.1.58-alpha")

    assert updater._is_skipped("5.1.58-alpha")
    assert updater.check_for_update("5.1.57-alpha") is None
    assert updater.check_for_update("5.1.57-alpha", include_skipped=True) is not None

    updater.clear_skip()
    assert not updater._is_skipped("5.1.58-alpha")


def test_v5_updater_mandatory_min_version_ignores_skip(monkeypatch):
    monkeypatch.delenv("MEA_UPDATE_URL_V5", raising=False)
    monkeypatch.setenv("MEA_UPDATE_URL", "https://updates.example.test/latest")
    monkeypatch.setattr(
        updater,
        "_check_endpoint",
        lambda _url, *, source="endpoint": _info(source=source, min_version="5.1.58-alpha"),
    )
    monkeypatch.setattr(updater, "_is_skipped", lambda _version: True)

    result = updater.check_for_update("5.1.57-alpha")

    assert result is not None
    assert result["is_mandatory"] is True


def test_v5_update_dialog_is_native_and_accessible_from_common_entry_points():
    dialog_source = (ROOT / "v5" / "update_dialog.py").read_text(encoding="utf-8")
    app_source = (ROOT / "v5" / "app.py").read_text(encoding="utf-8")
    prefs_source = (ROOT / "v5" / "preferences.py").read_text(encoding="utf-8")
    about_source = (ROOT / "v5" / "about.py").read_text(encoding="utf-8")
    actions = {key for kind, key, _label in _DEFAULT_ITEMS if kind == "action"}

    assert "import customtkinter as ctk" in dialog_source
    assert "from ui." not in dialog_source
    assert "import ui." not in dialog_source
    assert "require_hash=True" in dialog_source
    assert "check_update" in actions
    assert 'elif key == "check_update":' in app_source
    assert "open_manual_update_check" in prefs_source
    assert "open_manual_update_check" in about_source
