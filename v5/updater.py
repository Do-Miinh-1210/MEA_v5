"""
v5/updater.py — Kiểm tra phiên bản mới cho desktop V5.

Thứ tự nguồn:
    1. MEA_UPDATE_URL_V5 hoặc MEA_UPDATE_URL: endpoint JSON chỉ định riêng.
    2. Backend LMS đã cấu hình: /v1/desktop/version/v5, query channel v5, rồi generic.
    3. GitHub Releases của repo phát hành.

Module này chỉ xử lý metadata và lịch kiểm tra nền. Dialog tải/cài đặt nằm ở
``v5.update_dialog`` để runtime V5 không phụ thuộc UI V4.
"""
from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
import urllib.request
from pathlib import Path
from typing import Callable

_log = logging.getLogger(__name__)

try:
    from config import GITHUB_UPDATE_REPO as DEFAULT_GITHUB_REPO
except Exception:
    DEFAULT_GITHUB_REPO = "Do-Miinh-1210/MEA_byDoMiinh"

GITHUB_API = "https://api.github.com/repos/{repo}/releases/latest"
TIMEOUT_SEC = 4
APP_UPDATE_CHANNEL = "v5"
APP_UPDATE_ENV = "MEA_UPDATE_URL_V5"
GENERIC_UPDATE_ENV = "MEA_UPDATE_URL"


def _runtime_env_path() -> Path:
    """Return the packaged/source .env path used by update checks."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / ".env"
    return Path(__file__).resolve().parents[1] / ".env"


def _env_value(key: str, default: str = "") -> str:
    value = os.environ.get(key, "").strip()
    if value:
        return value
    try:
        for envfile in (Path.cwd() / ".env", _runtime_env_path()):
            if not envfile.exists():
                continue
            for line in envfile.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                name, _, raw_value = line.partition("=")
                if name.strip() == key:
                    return raw_value.strip().strip('"').strip("'")
    except Exception:
        pass
    return default


def _parse_version(version: str) -> tuple[int, int, int, int, int, str]:
    """Parse semantic-ish version thành tuple luôn so sánh được.

    Thứ tự suffix: alpha < beta < rc < suffix khác < stable.
    """
    text = str(version or "").strip().lstrip("vV ").strip()
    match = re.fullmatch(
        r"(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-+]([0-9A-Za-z._-]+))?",
        text,
    )
    if not match:
        return (0, 0, 0, 0, 0, text.lower())

    major, minor, patch, suffix = match.groups()
    if not suffix:
        return (int(major), int(minor or 0), int(patch or 0), 9, 0, "")

    suffix_text = suffix.lower()
    suffix_match = re.match(r"(alpha|beta|rc)[._-]?(\d*)", suffix_text)
    if suffix_match:
        label, number = suffix_match.groups()
        rank = {"alpha": 1, "beta": 2, "rc": 3}[label]
        return (
            int(major), int(minor or 0), int(patch or 0),
            rank, int(number or 0), suffix_text,
        )
    return (int(major), int(minor or 0), int(patch or 0), 5, 0, suffix_text)


def _is_newer(remote: str, local: str) -> bool:
    return _parse_version(remote) > _parse_version(local)


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _has_channel_token(text: str, token: str) -> bool:
    return re.search(rf"(^|[^a-z0-9]){re.escape(token)}([^a-z0-9]|$)", text.lower()) is not None


def _targets_other_channel(data: dict, *, asset_name: str, download_url: str, page_url: str) -> bool:
    declared = str(
        data.get("channel")
        or data.get("app")
        or data.get("target")
        or data.get("product")
        or ""
    ).lower()
    if declared:
        if _has_channel_token(declared, "v4") and not _has_channel_token(declared, APP_UPDATE_CHANNEL):
            return True
        if _has_channel_token(declared, APP_UPDATE_CHANNEL) or "all" in declared or "desktop" in declared:
            return False

    probe = f"{asset_name} {download_url} {page_url}".lower()
    has_v4 = _has_channel_token(probe, "v4") or "mea_v4" in probe
    has_v5 = _has_channel_token(probe, APP_UPDATE_CHANNEL) or "mea_v5" in probe
    return has_v4 and not has_v5


def _fetch_json(url: str) -> dict | None:
    """GET JSON và trả None khi endpoint không khả dụng."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "MEA-V5-Updater/1.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
        return data if isinstance(data, dict) else None
    except Exception as exc:
        _log.info("update fetch fail for %s: %s", url, exc)
        return None


def _unwrap_payload(data: dict) -> dict:
    """Support direct release JSON and LMS wrappers like {ok, data:{...}}."""
    if not isinstance(data, dict):
        return {}
    release_keys = {
        "version", "latest", "latest_version", "tag_name", "name",
        "download_url", "installer_url", "assets",
    }
    nested = data.get("data")
    if isinstance(nested, dict) and not any(key in data for key in release_keys):
        return nested
    return data


def _select_release_asset(assets: list[dict]) -> dict | None:
    """Chọn installer Windows phù hợp nhất từ GitHub release."""
    installers = [
        item for item in assets
        if str(item.get("name", "")).lower().endswith(".exe")
        and item.get("browser_download_url")
    ]
    if not installers:
        return None

    def _score(item: dict) -> tuple[int, str]:
        name = str(item.get("name", "")).lower()
        url = str(item.get("browser_download_url") or "").lower()
        text = f"{name} {url}"
        points = 0
        for token in ("mea_v5", "v5"):
            if token in text:
                points += 8
        for token in ("mea_v4", "v4"):
            if token in text:
                points -= 8
        points += sum(token in text for token in ("setup", "installer", "install", "update", "mea"))
        return points, name

    return sorted(installers, key=_score, reverse=True)[0]


def _normalize_info(data: dict, *, source: str) -> dict | None:
    """Chuẩn hóa JSON endpoint/GitHub về contract dùng chung cho dialog V5."""
    payload = _unwrap_payload(data)
    version = (
        payload.get("version")
        or payload.get("latest_version")
        or payload.get("latest")
        or payload.get("tag_name")
        or payload.get("name")
    )
    if not version:
        return None

    asset = _select_release_asset(payload.get("assets") or payload.get("files") or []) or {}
    page_url = (
        payload.get("html_url")
        or payload.get("release_url")
        or payload.get("page_url")
        or payload.get("url")
        or ""
    )
    download_url = (
        payload.get("download_url")
        or payload.get("installer_url")
        or payload.get("windows_url")
        or payload.get("win64_url")
        or asset.get("browser_download_url")
        or ""
    )
    if not download_url and str(page_url).lower().endswith(".exe"):
        download_url = page_url
    asset_name = str(payload.get("asset_name") or asset.get("name") or "")
    if _targets_other_channel(
        payload,
        asset_name=asset_name,
        download_url=str(download_url),
        page_url=str(page_url),
    ):
        return None

    return {
        "version": str(version).lstrip("vV"),
        "url": str(page_url or download_url),
        "notes": str(
            payload.get("notes")
            or payload.get("changelog")
            or payload.get("release_notes")
            or payload.get("body")
            or ""
        ),
        "download_url": str(download_url),
        "file_size": int(payload.get("file_size") or asset.get("size") or 0),
        "file_hash": str(
            payload.get("file_hash")
            or payload.get("sha256")
            or payload.get("digest")
            or asset.get("digest")
            or ""
        ),
        "min_version": str(payload.get("min_version") or ""),
        "is_mandatory": _as_bool(
            payload.get("is_mandatory")
            or payload.get("mandatory")
            or payload.get("force_update")
        ),
        "asset_name": asset_name,
        "source": source,
    }


def _check_endpoint(url: str, *, source: str = "endpoint") -> dict | None:
    data = _fetch_json(url)
    return _normalize_info(data, source=source) if data else None


def _check_lms_backend() -> dict | None:
    try:
        from services import api_client
        base_url = api_client.api_url().rstrip("/")
    except Exception:
        return None
    if not base_url:
        return None
    for suffix in (
        f"/v1/desktop/version/{APP_UPDATE_CHANNEL}",
        f"/v1/desktop/version?channel={APP_UPDATE_CHANNEL}",
        "/v1/desktop/version",
    ):
        info = _check_endpoint(f"{base_url}{suffix}", source="lms")
        if info:
            return info
    return None


def _check_github(repo: str) -> dict | None:
    data = _fetch_json(GITHUB_API.format(repo=repo))
    return _normalize_info(data, source="github") if data else None


def skip_version(version: str) -> None:
    """Không nhắc lại một phiên bản tùy chọn đã bị người dùng bỏ qua."""
    try:
        from v5 import settings_store
        settings_store.set_value("skipped_update_version", str(version or "").strip())
    except Exception as exc:
        _log.info("save skipped update fail: %s", exc)


def clear_skip() -> None:
    """Xóa trạng thái bỏ qua khi người dùng chủ động kiểm tra cập nhật."""
    skip_version("")


def _is_skipped(version: str) -> bool:
    try:
        from v5 import settings_store
        skipped = settings_store.get("skipped_update_version", "")
        return bool(skipped) and str(skipped).strip() == str(version or "").strip()
    except Exception:
        return False


def check_for_update(current_version: str, *, include_skipped: bool = False) -> dict | None:
    """Trả metadata bản mới nhất hoặc None nếu đã cập nhật.

    ``include_skipped`` dùng cho thao tác kiểm tra thủ công: người dùng vẫn thấy
    bản từng bỏ qua và có thể tải lại.
    """
    info = None

    endpoint = (
        _env_value(APP_UPDATE_ENV, "").strip()
        or _env_value(GENERIC_UPDATE_ENV, "").strip()
    )
    if endpoint:
        info = _check_endpoint(endpoint, source="endpoint")

    if not info:
        info = _check_lms_backend()

    if not info:
        repo = (
            _env_value("MEA_GITHUB_REPO_V5", "").strip()
            or _env_value("MEA_GITHUB_REPO", DEFAULT_GITHUB_REPO).strip()
        )
        if repo and "/" in repo:
            info = _check_github(repo)

    if not info or not _is_newer(info["version"], current_version):
        return None

    min_version = info.get("min_version", "")
    if min_version and _is_newer(min_version, current_version):
        info["is_mandatory"] = True

    if not info.get("is_mandatory") and not include_skipped and _is_skipped(info["version"]):
        return None
    return info


def check_for_update_async(
    app,
    *,
    delay_ms: int = 5000,
    on_found: Callable[[dict], None] | None = None,
):
    """Kiểm tra nền sau ``delay_ms`` và hiện toast chi tiết nếu có bản mới."""
    from v5 import __version__

    try:
        from v5 import settings_store
        if not settings_store.load().get("check_updates", True):
            _log.info("update check disabled via settings")
            return
    except Exception:
        pass

    def _worker():
        info = check_for_update(__version__)
        if not info:
            return

        def _show():
            try:
                from v5.toast import show_toast
                show_toast(
                    app,
                    f"🎉 Có phiên bản mới: v{info['version']}",
                    kind="info",
                    duration=8,
                    action_label="Chi tiết",
                    action_cb=lambda: _show_update_details(app, info),
                )
            except Exception as exc:
                _log.warning("show update toast fail: %s", exc)
            if on_found:
                try:
                    on_found(info)
                except Exception:
                    pass

        try:
            app.after(0, _show)
        except Exception:
            pass

    def _start():
        threading.Thread(target=_worker, daemon=True, name="updater").start()

    try:
        app.after(delay_ms, _start)
    except Exception:
        _start()


def _show_update_details(parent, info: dict) -> None:
    try:
        from v5.update_dialog import show_update_dialog
        show_update_dialog(parent, info)
    except Exception as exc:
        _log.warning("open update dialog fail: %s", exc)
        _open_url(info.get("url") or info.get("download_url", ""))


def _open_url(url: str) -> None:
    if not url:
        return
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception as exc:
        _log.warning("open url fail: %s", exc)
