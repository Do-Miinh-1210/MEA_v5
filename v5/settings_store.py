"""
v5/settings_store.py — Persist UI state qua JSON.

Lưu/đọc các state:
    • theme (light/dark/system)
    • last_view (id của view mở cuối)
    • window_geometry (vd "1280x800+100+50")
    • sidebar_collapsed (bool)
    • login_email_last (gợi ý login lần sau)

File: ~/.exam_generator/v5_settings.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

_FILE = Path.home() / ".exam_generator" / "v5_settings.json"
_FILE.parent.mkdir(parents=True, exist_ok=True)

_DEFAULTS = {
    "theme":              "System",       # System | Light | Dark
    "last_view":          "home",
    "window_geometry":    "1280x800",
    "sidebar_collapsed":  False,
    "login_email_last":   "",
    "color_accent":       "blue",         # blue | green | dark-blue
    "onboarded":          False,
    "recent_files":       [],             # list[str] — max 10 file paths
    "check_updates":      True,           # auto check GitHub releases khi mở
    "skipped_update_version": "",         # phiên bản tùy chọn user không muốn nhắc lại
    "crash_dialog":       True,           # show modal khi crash (False = silent)
    "last_opened_ts":     "",             # ISO timestamp lần mở app trước
    "show_whats_new":     True,           # auto popup What's New khi version đổi
    "seen_whats_new":     "",             # version đã đọc changelog
    "crashes_seen_count": 0,              # số crash đã xem (badge tính unread)
}


# ── Recent files API ────────────────────────────────────────────────────────

_RECENT_MAX = 10


def add_recent_file(path: str) -> None:
    """Push path lên đầu list recent_files; cắt còn 10 phần tử."""
    if not path:
        return
    cur = load().get("recent_files") or []
    cur = [p for p in cur if p != path]   # remove duplicates
    cur.insert(0, path)
    cur = cur[:_RECENT_MAX]
    save({"recent_files": cur})


def get_recent_files() -> list[str]:
    """Trả list path mới nhất, filter bỏ file đã bị xoá khỏi disk."""
    from pathlib import Path
    out = []
    for p in (load().get("recent_files") or []):
        if Path(p).exists():
            out.append(p)
    return out


def load() -> dict[str, Any]:
    """Load settings; merge với defaults nếu key thiếu."""
    if not _FILE.exists():
        return dict(_DEFAULTS)
    try:
        data = json.loads(_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, dict): return dict(_DEFAULTS)
        return {**_DEFAULTS, **data}
    except Exception as e:
        _log.warning("Load v5 settings fail: %s", e)
        return dict(_DEFAULTS)


def save(updates: dict[str, Any]) -> None:
    """Merge updates vào file (đọc → merge → ghi)."""
    try:
        current = load()
        current.update(updates)
        _FILE.write_text(
            json.dumps(current, ensure_ascii=False, indent=2),
            encoding="utf-8")
    except Exception as e:
        _log.warning("Save v5 settings fail: %s", e)


def get(key: str, default=None):
    return load().get(key, default if default is not None else _DEFAULTS.get(key))


def set_value(key: str, value: Any) -> None:
    save({key: value})
