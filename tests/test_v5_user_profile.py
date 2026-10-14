"""Guard rails for V5 user/license profile parity."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from v5.user_profile import (
    expiry_status,
    feature_count,
    feature_rows,
    license_source_label,
    support_text,
    tier_label,
)


ROOT = Path(__file__).resolve().parents[1]


def test_expiry_status_matches_v4_countdown_states():
    today = date(2026, 5, 27)

    assert expiry_status("", today=today)["state"] == "permanent"
    assert expiry_status("2026-05-27", today=today)["state"] == "today"
    assert expiry_status("2026-05-30", today=today)["state"] == "warning"
    assert expiry_status("2026-06-20", today=today)["state"] == "soon"
    assert expiry_status("2026-04-30", today=today)["state"] == "expired"


def test_feature_rows_apply_tier_defaults_and_admin_overrides():
    info = {
        "ok": True,
        "tier": "pro",
        "features": {"tab_qc": True, "nhch_cloud": False},
    }

    rows = {row["key"]: row for row in feature_rows(info)}

    assert rows["tab_bank"]["enabled"] is True
    assert rows["tab_qc"]["enabled"] is True
    assert rows["tab_qc"]["override"] is True
    assert rows["nhch_cloud"]["enabled"] is False
    assert rows["nhch_cloud"]["override"] is True
    assert feature_count(info)[1] == len(rows)


def test_support_text_contains_license_profile_for_admin_copy():
    info = {
        "ok": True,
        "name": "Teacher A",
        "tier": "premium",
        "status": "active",
        "expiry": "2026-06-30",
        "via_api": True,
    }

    text = support_text(info, machine_id="MID-123", machine_display="Windows PC")

    assert "Teacher A" in text
    assert "MID-123" in text
    assert "API backend V5" in text
    assert "PREMIUM" in text
    assert license_source_label(info) == "API backend V5"
    assert "Premium" in tier_label(info)


def test_setup_license_panel_uses_v5_user_profile_helpers():
    source = (ROOT / "v5" / "views" / "setup.py").read_text(encoding="utf-8")

    assert "from v5.user_profile import" in source
    assert "_copy_machine_id" in source
    assert "_copy_support_info" in source
    assert "_render_feature_rows" in source
    assert "CTkScrollableFrame(root" in source
    assert "ui.tab_user_info" not in source


def test_setup_api_key_editor_supports_multiline_and_provider_links():
    source = (ROOT / "v5" / "views" / "setup.py").read_text(encoding="utf-8")

    assert "API_KEY_URL_FALLBACKS" in source
    assert "self._key_entry = ctk.CTkTextbox" in source
    assert 'self._key_entry.get("1.0", "end-1c")' in source
    assert "def _open_api_key_url" in source
    assert "webbrowser.open(url)" in source
    assert "platform.openai.com/api-keys" in source


def test_v5_ai_call_sites_split_saved_multiline_keys():
    paths = [
        "v5/views/convert.py",
        "v5/views/exam_create.py",
        "v5/views/nhch.py",
        "v5/views/qc.py",
        "v5/smart_prompt.py",
        "v5/ai_gen_matrix.py",
        "v5/import_wizard.py",
    ]

    combined = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in paths)

    assert "split_keys" in combined
    assert "else [key]" not in combined
    assert "else [k]" not in combined
