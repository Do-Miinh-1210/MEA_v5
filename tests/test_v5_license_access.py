"""Feature access parity between the V5 shell and the shared license catalog."""
from __future__ import annotations

from v5.license_access import (
    badge_presentation,
    effective_features,
    feature_allowed,
    license_locked,
    restriction_message,
    view_feature,
)


def test_unlocked_version_allows_all_workflows():
    info = {"ok": True, "status": "active", "tier": "basic"}

    assert feature_allowed(info, "tab_matrix") is True
    assert feature_allowed(info, "export_word") is True
    assert feature_allowed(info, "tab_bank") is True
    assert feature_allowed(info, "tab_qc") is True
    assert feature_allowed(info, "tab_convert") is True
    assert feature_allowed(info, "smart_prompt") is True
    assert view_feature("nhch") == "tab_bank"
    assert view_feature("qc") == "tab_qc"


def test_effective_features_includes_all_catalog_items():
    info = {"ok": True, "status": "active", "tier": "premium"}
    features = effective_features(info)

    assert features["tab_qc"] is True
    assert features["tab_matrix"] is True
    assert features["tab_bank"] is True
    assert feature_allowed(info, "tab_qc") is True
    assert feature_allowed(info, "nhch_cloud") is True


def test_database_error_or_offline_does_not_lock_authoring():
    info = {"ok": False, "status": "error", "tier": "premium"}

    assert license_locked(info) is False
    assert feature_allowed(info, "tab_matrix") is True
    assert feature_allowed(info, "export_word") is True


def test_gated_operation_always_allowed():
    assert feature_allowed({}, "tab_matrix", checked=True) is True
    assert feature_allowed({}, "tab_bank", checked=True) is True


def test_badge_reflects_premium_state():
    assert badge_presentation({}, checked=True)[0] == "PREMIUM"
    assert badge_presentation({"offline": True}, checked=True)[0] == "PREMIUM OFFLINE"
