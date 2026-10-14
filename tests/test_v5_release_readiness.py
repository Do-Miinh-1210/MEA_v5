"""Release gates for the V5 frozen build and installer."""
from __future__ import annotations

from pathlib import Path

from services import api_client
from v5 import __version__
from v5.diagnostics import format_report, release_checks_pass
from v5.quickswitch import _DEFAULT_ITEMS
from v5.whats_new import CHANGELOG


ROOT = Path(__file__).resolve().parents[1]


def test_api_url_is_persisted_to_runtime_env_atomically(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("OTHER=value\nMEA_API_URL=http://old\n", encoding="utf-8")
    monkeypatch.setattr(api_client, "_runtime_env_path", lambda: env_file)
    monkeypatch.delenv("MEA_API_URL", raising=False)

    saved_path = api_client.save_api_url("https://lms.example.test/")

    assert saved_path == env_file
    assert api_client.api_url() == "https://lms.example.test"
    assert "MEA_API_URL=https://lms.example.test" in env_file.read_text(encoding="utf-8")
    assert not (tmp_path / ".env.tmp").exists()


def test_v5_build_bundles_data_without_v4_ui_package():
    source = (ROOT / "build_v5_alpha.py").read_text(encoding="utf-8")

    assert "'v5', 'core', 'services', 'storage', 'export', 'ui'" not in source
    assert "(r'{SRC / \"data\"}', 'data')" in source
    assert "'PyQt5', 'PyQt6', 'PySide6'" in source
    assert "_part.startswith(('test_', '_test'))" in source
    assert "(r'{NATIVE_DLL}', 'native')" in source
    assert '"build_native.py"' in source


def test_installer_uses_single_file_exe_resources():
    generator = (ROOT / "build_v5_installer.py").read_text(encoding="utf-8")
    generated = (ROOT / "installer_v5.iss").read_text(encoding="utf-8")

    assert r'{DIST}\\assets\\*' not in generator
    assert r"dist\assets\*" not in generated
    assert r"UninstallDisplayIcon={app}\{#MyAppExeName}" in generated


def test_v5_version_stays_in_sync_with_changelog_and_generated_installer():
    generator = (ROOT / "build_v5_installer.py").read_text(encoding="utf-8")
    generated = (ROOT / "installer_v5.iss").read_text(encoding="utf-8")

    assert next(iter(CHANGELOG)) == __version__
    assert "from v5 import __version__ as APP_VERSION" in generator
    assert f'#define MyAppVersion "{__version__}"' in generated


def test_v5_shell_does_not_launch_v4_fallback():
    source = (ROOT / "v5" / "app.py").read_text(encoding="utf-8")

    assert "_open_v4" not in source
    assert "MEA_v4.exe" not in source


def test_legacy_v5_backup_facade_delegates_to_safe_service():
    source = (ROOT / "v5" / "backup.py").read_text(encoding="utf-8")

    assert "from services.local_backup import" in source
    assert "restore_local_backup(" in source
    assert "zipfile" not in source


def test_quick_switcher_exposes_all_eight_v5_views():
    views = {key for kind, key, _label in _DEFAULT_ITEMS if kind == "view"}

    assert views == {
        "home", "setup", "exam_create", "nhch", "convert",
        "qc", "tracking", "guide",
    }


def test_v5_shell_wires_license_gating_and_documents_all_view_shortcuts():
    source = (ROOT / "v5" / "app.py").read_text(encoding="utf-8")
    wizard_source = (ROOT / "v5" / "import_wizard.py").read_text(encoding="utf-8")

    assert "from v5.license_access import" in source
    assert "self._can_use_feature" in source
    assert "app._current_view_id == vid" in source
    assert 'self._pending_initial_view = "exam_create"' in source
    assert "Ctrl+5" in source
    assert "Ctrl+8" in source
    assert "Ctrl+9" not in source
    assert 'if not self._can_use_feature("tab_bank")' in source
    assert 'self._feature_allowed("nhch_cloud")' in wizard_source


def test_selftest_allows_unconfigured_optional_features():
    results = [
        ("Import modules", True, "OK"),
        ("LaTeX engine", False, "not installed"),
        ("Xuất Word", True, "OK"),
        ("TikZ render", False, "needs LaTeX"),
        ("Core + NHCH", True, "OK"),
        ("API key", False, "not configured"),
    ]

    assert release_checks_pass(results) is True
    assert "[INFO] LaTeX engine" in format_report(results)
    assert "[INFO] API key" in format_report(results)


def test_selftest_fails_when_tikz_is_broken_with_engine_available():
    results = [
        ("Import modules", True, "OK"),
        ("LaTeX engine", True, "pdflatex"),
        ("Xuất Word", True, "OK"),
        ("TikZ render", False, "compile failed"),
        ("Core + NHCH", True, "OK"),
        ("API key", False, "not configured"),
    ]

    assert release_checks_pass(results) is False
    assert "[FAIL] TikZ render" in format_report(results)
