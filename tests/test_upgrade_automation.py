"""Guard tests for the V4/V5 automated upgrade pipeline."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_upgrade_automation_stages_builds_and_generates_manifest():
    source = (ROOT / "tools" / "upgrade_app.py").read_text(encoding="utf-8")

    assert "tempfile.mkdtemp" in source
    assert "sys.path.insert(0, str(ROOT))" in source
    assert "build_helper.DIST = stage_dist" in source
    assert "build_helper.BUILD_TMP = stage_work" in source
    assert "update_manifest_v4.json" in source
    assert "update_manifest_v5.json" in source
    assert '"channel": "v4"' in source
    assert '"channel": "v5"' in source
    assert '"download_url"' in source
    assert '"file_hash"' in source
    assert "sha256:" in source
    assert "_selftest(stage_dist / APP_EXE)" in source
    assert "_selftest(v5_stage_dist / V5_EXE)" in source
    assert "_selftest(DIST / APP_EXE)" in source
    assert "_selftest(DIST / V5_EXE)" in source
    assert "CREATE_NO_WINDOW" in source
    assert "timeout=420" in source


def test_upgrade_automation_has_fast_test_gate_and_skip_build_mode():
    source = (ROOT / "tools" / "upgrade_app.py").read_text(encoding="utf-8")

    assert "tests/test_updater.py" in source
    assert "tests/test_update_safety.py" in source
    assert "tests/test_v5_release_readiness.py" in source
    assert "tests/test_v4_v5_tikz_vector_parity.py" in source
    assert "tests/test_v5_question_cards.py" in source
    assert "tests/test_exe_smoke.py" in source
    assert "--target" in source
    assert '"all", "v4", "v5"' in source
    assert "--test-mode" in source
    assert "--skip-build" in source
    assert "--manifest-only" in source


def test_upgrade_automation_builds_v5_in_staging_and_keeps_v4_url_compat():
    source = (ROOT / "tools" / "upgrade_app.py").read_text(encoding="utf-8")

    assert "def _build_v5_to_stage" in source
    assert 'env["MEA_V5_DIST"] = str(stage_dist)' in source
    assert 'env["MEA_V5_BUILD_TMP"] = str(stage_work)' in source
    assert "build_v5_alpha.py" in source
    assert "def _write_v5_manifest" in source
    assert "from v5 import __version__" in source
    assert "download_url=args.download_url_v4 or args.download_url" in source
    assert "download_url=args.download_url_v5" in source


def test_v4_entrypoint_has_headless_selftest_before_ui_startup():
    source = (ROOT / "main.py").read_text(encoding="utf-8")

    selftest_branch = source.index('if "--selftest" in sys.argv:')
    tkinter_import = source.index("# 3. Import tkinter")
    assert selftest_branch < tkinter_import
    assert "def _run_selftest()" in source
    assert "updater._normalize_info" in source
