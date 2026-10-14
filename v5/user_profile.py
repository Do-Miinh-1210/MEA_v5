"""Helpers for the V5 user/license profile panel.

The old V4 "Nguoi dung" tab mixed Tk widgets with license formatting.  V5 keeps
that presentation logic here so the Setup license panel can be tested without a
desktop window.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from config import FEATURE_CATALOG
from v5.license_access import effective_features


TIER_LABELS = {
    "basic": "Basic - tu nhap API key",
    "pro": "PRO - admin cap API key, mo rong tinh nang",
    "premium": "Premium - toan quyen, uu tien API key",
}

TIER_COLORS = {
    "basic": "#64748B",
    "pro": "#0284C7",
    "premium": "#8B5CF6",
}

PERMANENT_EXPIRY_VALUES = {"", "0", "none", "never", "permanent", "vinh vien", "vĩnh viễn"}


def tier_key(info: dict[str, Any] | None) -> str:
    tier = str((info or {}).get("tier") or "basic").strip().lower()
    return tier if tier in TIER_LABELS else "basic"


def tier_label(info: dict[str, Any] | None) -> str:
    return TIER_LABELS[tier_key(info)]


def tier_color(info: dict[str, Any] | None) -> str:
    return TIER_COLORS[tier_key(info)]


def license_source_label(info: dict[str, Any] | None) -> str:
    data = info or {}
    if data.get("via_api"):
        return "API backend V5"
    if data.get("offline"):
        return "Cache offline"
    if data.get("ok"):
        return "Supabase truc tiep"
    return "Chua xac minh"


def display_date(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text or _is_permanent(text):
        return "Vinh vien"
    parsed = _parse_expiry(text)
    if parsed:
        return parsed.strftime("%d/%m/%Y")
    return text


def expiry_status(raw: Any, *, today: date | None = None) -> dict[str, Any]:
    """Return V4-style expiry countdown information.

    The progress value is intentionally simple and UI-friendly: it is not a
    billing metric, only a visual urgency meter.
    """
    text = str(raw or "").strip()
    if not text or _is_permanent(text):
        return {
            "state": "permanent",
            "title": "Vinh vien",
            "detail": "Goi hien tai khong co thoi han.",
            "display": "Vinh vien",
            "days_remaining": None,
            "progress": 100,
            "color": "#10B981",
        }

    exp_date = _parse_expiry(text)
    if not exp_date:
        return {
            "state": "unknown",
            "title": text,
            "detail": "Khong nhan dien duoc dinh dang ngay het han.",
            "display": text,
            "days_remaining": None,
            "progress": 0,
            "color": "#64748B",
        }

    today = today or date.today()
    remaining = (exp_date - today).days
    display = exp_date.strftime("%d/%m/%Y")

    if remaining < 0:
        return {
            "state": "expired",
            "title": f"Da het han {abs(remaining)} ngay truoc",
            "detail": f"Het han: {display}. Lien he admin de gia han.",
            "display": display,
            "days_remaining": remaining,
            "progress": 0,
            "color": "#EF4444",
        }
    if remaining == 0:
        return {
            "state": "today",
            "title": "Het han hom nay",
            "detail": f"Ngay het han: {display}",
            "display": display,
            "days_remaining": remaining,
            "progress": 1,
            "color": "#F59E0B",
        }
    if remaining <= 7:
        return {
            "state": "warning",
            "title": f"Con {remaining} ngay",
            "detail": f"Het han: {display} - sap het han.",
            "display": display,
            "days_remaining": remaining,
            "progress": max(5, remaining * 3),
            "color": "#F59E0B",
        }
    if remaining <= 30:
        return {
            "state": "soon",
            "title": f"Con {remaining} ngay",
            "detail": f"Het han: {display}",
            "display": display,
            "days_remaining": remaining,
            "progress": min(100, remaining * 3),
            "color": "#0284C7",
        }
    return {
        "state": "active",
        "title": f"Con {remaining} ngay",
        "detail": f"Het han: {display}",
        "display": display,
        "days_remaining": remaining,
        "progress": min(100, remaining),
        "color": "#10B981",
    }


def feature_rows(info: dict[str, Any] | None) -> list[dict[str, Any]]:
    data = info or {}
    tier = tier_key(data)
    overrides = data.get("features") if isinstance(data.get("features"), dict) else {}
    resolved = effective_features(data)
    rows: list[dict[str, Any]] = []
    for key, meta in FEATURE_CATALOG.items():
        default_enabled = bool(meta.get(tier, False))
        enabled = bool(resolved.get(key, default_enabled))
        is_override = key in overrides and bool(overrides[key]) != default_enabled
        rows.append({
            "key": key,
            "label": str(meta.get("label") or key),
            "enabled": enabled,
            "default_enabled": default_enabled,
            "override": is_override,
            "source": "admin override" if is_override else f"default {tier}",
        })
    return rows


def feature_count(info: dict[str, Any] | None) -> tuple[int, int]:
    rows = feature_rows(info)
    return sum(1 for row in rows if row["enabled"]), len(rows)


def support_text(
    info: dict[str, Any] | None,
    *,
    machine_id: str = "",
    machine_display: str = "",
) -> str:
    data = info or {}
    enabled, total = feature_count(data)
    expiry = expiry_status(data.get("expiry"))
    return "\n".join([
        "MatrixExamAI - thong tin nguoi dung",
        f"Ten: {data.get('name') or 'Khach'}",
        f"Goi: {tier_key(data).upper()} ({tier_label(data)})",
        f"Trang thai: {data.get('status') or ('active' if data.get('ok') else 'unknown')}",
        f"Het han: {expiry['display']}",
        f"Tinh nang: {enabled}/{total}",
        f"Nguon license: {license_source_label(data)}",
        f"Machine ID: {machine_id or data.get('mid') or data.get('machine_id') or 'N/A'}",
        f"May: {machine_display or data.get('machine_display') or ''}",
    ]).strip()


def _is_permanent(text: str) -> bool:
    normalized = text.strip().lower()
    return normalized in PERMANENT_EXPIRY_VALUES


def _parse_expiry(text: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            pass
    return None
