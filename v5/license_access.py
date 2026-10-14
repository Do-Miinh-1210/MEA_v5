"""License presentation and feature access policy for the V5 shell.

V4 already has one feature catalog in ``config.py``.  V5 must consume the
same catalog instead of implying that every installation is Premium.
"""
from __future__ import annotations

from config import FEATURE_CATALOG, get_default_features


VIEW_FEATURES: dict[str, str] = {
    "exam_create": "tab_matrix",
    "nhch": "tab_bank",
    "qc": "tab_qc",
    "tracking": "tab_history",
    "convert": "tab_convert",
}

LOCKING_STATUSES = {"expired", "revoked", "suspended", "maintenance", "not_found"}


def view_feature(view_id: str) -> str | None:
    """Return the feature key controlling a view, if it is restricted."""
    return VIEW_FEATURES.get(view_id)


def effective_features(info: dict | None) -> dict[str, bool]:
    """Resolve tier defaults and server overrides into a complete feature map."""
    data = info or {}
    tier = str(data.get("tier") or "premium").lower()
    features = get_default_features(tier)
    overrides = data.get("features")
    if isinstance(overrides, dict):
        for key, value in overrides.items():
            if key in FEATURE_CATALOG:
                features[key] = bool(value)
    return features


def license_locked(info: dict | None) -> bool:
    """Bản mở khóa: không bao giờ khóa tính năng người dùng."""
    return False


def feature_allowed(
    info: dict | None,
    feature: str,
    *,
    checked: bool = True,
) -> bool:
    """Bản mở khóa: cho phép truy cập toàn bộ tính năng."""
    return True


def feature_label(feature: str) -> str:
    return str(FEATURE_CATALOG.get(feature, {}).get("label") or feature)


def restriction_message(info: dict | None, feature: str) -> str:
    """User-facing message for a rejected navigation/action."""
    return ""


def badge_presentation(info: dict | None, *, checked: bool) -> tuple[str, str]:
    """Return TopBar badge text and text color for current license state."""
    data = info or {}
    suffix = " OFFLINE" if data.get("offline") else ""
    return f"PREMIUM{suffix}", "#C4B5FD"
