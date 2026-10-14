"""
services/updater.py — Auto-update service cho MEA desktop.

Workflow:
  1. Khi app mở, kiểm tra metadata cập nhật theo thứ tự:
     MEA_UPDATE_URL_V4 -> MEA_UPDATE_URL -> backend LMS channel v4 -> GitHub Releases.
  2. So sánh release version với APP_VERSION hiện tại.
  3. Nếu có bản mới, lấy installer .exe, tải xuống và verify SHA-256 nếu có.
  4. UI tạo snapshot dữ liệu trước khi mở installer.

Repo fallback mặc định:
  https://github.com/Do-Miinh-1210/MEA_byDoMiinh
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Optional

from config import (
    APP_VERSION,
    APP_DIR,
    GITHUB_UPDATE_API_URL,
    GITHUB_UPDATE_REPO,
)

# Thư mục lưu file download tạm
_UPDATE_DIR = APP_DIR / "updates"
_UPDATE_DIR.mkdir(parents=True, exist_ok=True)

# File đánh dấu "bỏ qua phiên bản này"
_SKIP_FILE = APP_DIR / "skip_update.txt"

GITHUB_API = "https://api.github.com/repos/{repo}/releases/latest"
TIMEOUT_SEC = 6
APP_UPDATE_CHANNEL = "v4"
APP_UPDATE_ENV = "MEA_UPDATE_URL_V4"
GENERIC_UPDATE_ENV = "MEA_UPDATE_URL"


# ══════════════════════════════════════════════════════════════════════════════
#  SO SÁNH PHIÊN BẢN (semantic versioning)
# ══════════════════════════════════════════════════════════════════════════════

def _parse_version(v: str) -> tuple[int, int, int, int, int, str]:
    """Parse semantic-ish version thành tuple luôn so sánh được.

    Thứ tự suffix: alpha < beta < rc < suffix khác < stable.
    """
    text = str(v or "").strip().lstrip("vV ").strip()
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


def is_newer(remote: str, local: str = APP_VERSION) -> bool:
    """True nếu remote version > local version."""
    return _parse_version(remote) > _parse_version(local)


def is_mandatory(min_version: str, local: str = APP_VERSION) -> bool:
    """True nếu local < min_version → bắt buộc cập nhật."""
    if not min_version:
        return False
    return _parse_version(local) < _parse_version(min_version)


# ══════════════════════════════════════════════════════════════════════════════
#  KIỂM TRA CẬP NHẬT
# ══════════════════════════════════════════════════════════════════════════════

def _runtime_env_path() -> Path:
    """Vị trí .env khi chạy source hoặc khi đã đóng gói EXE."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / ".env"
    return Path(__file__).resolve().parent.parent / ".env"


def _env_value(key: str, default: str = "") -> str:
    """Đọc biến môi trường, fallback sang .env cạnh app/source."""
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


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        return default


def normalize_expected_hash(expected_hash: str) -> str:
    """Return normalized SHA-256 digest or empty string when metadata is unusable."""
    text = str(expected_hash or "").replace("sha256:", "").strip().lower()
    if re.fullmatch(r"[0-9a-f]{64}", text):
        return text
    return ""


def _fetch_json(url: str) -> Optional[dict]:
    """GET JSON, trả None nếu nguồn cập nhật không khả dụng."""
    try:
        import urllib.request

        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": f"MEA-Updater/{APP_VERSION}",
            },
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        return data if isinstance(data, dict) else None
    except Exception as e:
        try:
            print(f"[Updater] Fetch update metadata fail for {url}: {e}")
        except Exception:
            pass
        return None


def _unwrap_payload(data: dict) -> dict:
    """Hỗ trợ endpoint trả {ok, data:{...}} lẫn JSON release trực tiếp."""
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


def _asset_url(asset: dict) -> str:
    return str(
        asset.get("browser_download_url")
        or asset.get("download_url")
        or asset.get("installer_url")
        or asset.get("url")
        or ""
    )


def _looks_like_exe(name: str, url: str) -> bool:
    text = f"{name} {url}".lower()
    return ".exe" in text and not text.endswith(".zip")


def _has_channel_token(text: str, token: str) -> bool:
    return re.search(rf"(^|[^a-z0-9]){re.escape(token)}([^a-z0-9]|$)", text.lower()) is not None


def _targets_other_channel(payload: dict, *, asset_name: str, download_url: str, page_url: str) -> bool:
    declared = str(
        payload.get("channel")
        or payload.get("app")
        or payload.get("target")
        or payload.get("product")
        or ""
    ).lower()
    if declared:
        if _has_channel_token(declared, "v5") and not _has_channel_token(declared, APP_UPDATE_CHANNEL):
            return True
        if _has_channel_token(declared, APP_UPDATE_CHANNEL) or "all" in declared or "desktop" in declared:
            return False

    probe = f"{asset_name} {download_url} {page_url}".lower()
    has_v5 = _has_channel_token(probe, "v5") or "mea_v5" in probe
    has_v4 = _has_channel_token(probe, APP_UPDATE_CHANNEL) or "mea_v4" in probe
    return has_v5 and not has_v4


def _select_release_asset(assets: list[dict]) -> Optional[dict]:
    """Chọn asset installer Windows phù hợp nhất từ release metadata."""
    installers = []
    for asset in assets:
        if not isinstance(asset, dict):
            continue
        url = _asset_url(asset)
        name = str(asset.get("name") or Path(url).name or "")
        if url and _looks_like_exe(name, url):
            installers.append(asset)
    if not installers:
        return None

    def score(asset: dict) -> tuple[int, str]:
        name = str(asset.get("name", "")).lower()
        url = _asset_url(asset).lower()
        text = f"{name} {url}"
        points = 0
        for token in ("mea_v4", "v4"):
            if token in text:
                points += 8
        for token in ("mea_v5", "v5"):
            if token in text:
                points -= 8
        for token in ("setup", "installer", "install", "update"):
            if token in text:
                points += 4
        for token in ("mea", "matrixexam", "windows", "win64", "x64"):
            if token in text:
                points += 1
        for token in ("admin", "source", "debug", "portable"):
            if token in text:
                points -= 3
        return (points, name)

    return sorted(installers, key=score, reverse=True)[0]


def _normalize_info(data: dict, *, source: str) -> Optional[dict]:
    """Chuẩn hóa endpoint/GitHub về contract dùng chung cho UI updater."""
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
    asset_url = _asset_url(asset)
    page_url = str(
        payload.get("html_url")
        or payload.get("release_url")
        or payload.get("page_url")
        or payload.get("url")
        or ""
    )
    download_url = str(
        payload.get("download_url")
        or payload.get("installer_url")
        or payload.get("windows_url")
        or payload.get("win64_url")
        or asset_url
        or ""
    )
    if not download_url and page_url.lower().endswith(".exe"):
        download_url = page_url

    notes = str(
        payload.get("notes")
        or payload.get("changelog")
        or payload.get("release_notes")
        or payload.get("body")
        or ""
    )
    remote_ver = str(version).strip().lstrip("vV")
    mandatory = (
        _as_bool(payload.get("is_mandatory"))
        or _as_bool(payload.get("mandatory"))
        or _as_bool(payload.get("force_update"))
    )
    file_hash = str(
        payload.get("file_hash")
        or payload.get("sha256")
        or payload.get("digest")
        or asset.get("digest")
        or ""
    )
    asset_name = str(payload.get("asset_name") or asset.get("name") or "")
    if _targets_other_channel(
        payload,
        asset_name=asset_name,
        download_url=download_url,
        page_url=page_url,
    ):
        return None

    return {
        "version":       remote_ver,
        "latest":        remote_ver,
        "current":       APP_VERSION,
        "tag_name":      str(payload.get("tag_name") or f"v{remote_ver}"),
        "changelog":     notes,
        "notes":         notes,
        "release_notes": notes,
        "download_url":  download_url,
        "file_size":     _safe_int(payload.get("file_size") or asset.get("size")),
        "file_hash":     file_hash,
        "min_version":   str(payload.get("min_version") or ""),
        "is_mandatory":  mandatory,
        "html_url":      page_url,
        "url":           page_url or download_url,
        "asset_name":    asset_name,
        "source":        source,
    }


def _check_endpoint(url: str, *, source: str = "endpoint") -> Optional[dict]:
    data = _fetch_json(url)
    return _normalize_info(data, source=source) if data else None


def _check_lms_backend() -> Optional[dict]:
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


def _check_github(repo: str) -> Optional[dict]:
    if repo == GITHUB_UPDATE_REPO:
        url = GITHUB_UPDATE_API_URL
    else:
        url = GITHUB_API.format(repo=repo)
    data = _fetch_json(url)
    if not data or data.get("draft"):
        return None
    info = _normalize_info(data, source="github")
    if not info:
        return None
    info["repo"] = repo
    # Giữ hành vi V4 hiện tại: release GitHub fallback là cập nhật bắt buộc,
    # trừ khi metadata có min_version/mandatory rõ ràng từ endpoint phát hành.
    if not any(key in data for key in ("is_mandatory", "mandatory", "force_update", "min_version")):
        info["is_mandatory"] = True
    return info


def check_for_update(
    channel: str = "stable",
    *,
    current_version: str = APP_VERSION,
    include_skipped: bool = False,
) -> Optional[dict]:
    """Kiểm tra release mới nhất từ endpoint/backend/GitHub.

    Returns dict nếu có bản mới:
        {
            "version":      "4.1.1",
            "tag_name":     "v4.1.1",
            "changelog":    release body,
            "download_url": browser_download_url của asset .exe,
            "file_size":    asset size,
            "file_hash":    asset digest nếu GitHub trả về,
            "html_url":     release page,
            "asset_name":   tên file installer,
            "source":       "github",
            "is_mandatory": True,
        }
    Returns None nếu đã mới nhất hoặc lỗi.
    """
    try:
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
                _env_value("MEA_GITHUB_REPO_V4", "").strip()
                or _env_value("MEA_GITHUB_REPO", GITHUB_UPDATE_REPO).strip()
            )
            if repo and "/" in repo:
                info = _check_github(repo)

        if not info:
            return None

        remote_ver = str(info.get("version") or "").strip()
        if not remote_ver or not is_newer(remote_ver, current_version):
            return None

        min_version = str(info.get("min_version") or "")
        if min_version and is_mandatory(min_version, current_version):
            info["is_mandatory"] = True

        if (
            not info.get("is_mandatory", False)
            and not include_skipped
            and _is_skipped(remote_ver)
        ):
            return None

        info["current"] = current_version
        return info

    except Exception as e:
        try:
            print(f"[Updater] Update check error: {e}")
        except Exception:
            pass
        return None


def check_for_update_async(
    callback,
    channel: str = "stable",
    include_skipped: bool = False,
) -> threading.Thread:
    """Kiểm tra cập nhật trong background thread.

    callback(result: Optional[dict]) sẽ được gọi khi xong.
    """
    def _worker():
        result = check_for_update(channel, include_skipped=include_skipped)
        callback(result)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


# ══════════════════════════════════════════════════════════════════════════════
#  DOWNLOAD CẬP NHẬT
# ══════════════════════════════════════════════════════════════════════════════

def download_update(
    download_url: str,
    expected_hash: str = "",
    require_hash: bool = False,
    progress_callback=None,
) -> Optional[str]:
    """Download file cập nhật từ URL.

    progress_callback(downloaded_bytes, total_bytes) được gọi định kỳ.

    Returns đường dẫn file đã tải, hoặc None nếu lỗi.
    """
    try:
        import urllib.request
        import urllib.error

        clean_expected = normalize_expected_hash(expected_hash)
        if require_hash and not clean_expected:
            print("[Updater] Refusing to download installer without a valid SHA-256 hash.")
            return None

        # Xác định tên file từ URL
        from urllib.parse import urlparse
        parsed = urlparse(download_url)
        filename = Path(parsed.path).name or "MEA_Setup.exe"
        dest = _UPDATE_DIR / filename

        # Xóa file cũ nếu có
        if dest.exists():
            dest.unlink()

        # Download với progress
        req = urllib.request.Request(download_url)
        req.add_header("User-Agent", f"MEA/{APP_VERSION}")

        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            hasher = hashlib.sha256()

            with open(str(dest), "wb") as f:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    hasher.update(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)

        # Verify hash
        if clean_expected:
            actual_hash = hasher.hexdigest()
            # Hash có thể có prefix "sha256:"
            if actual_hash.lower() != clean_expected:
                print(f"[Updater] Hash mismatch! expected={clean_expected}, got={actual_hash}")
                dest.unlink(missing_ok=True)
                return None

        return str(dest)

    except Exception as e:
        try:
            print(f"[Updater] Download error: {e}")
        except Exception:
            pass
        return None


def download_update_async(
    download_url: str,
    expected_hash: str = "",
    require_hash: bool = False,
    progress_callback=None,
    done_callback=None,
) -> threading.Thread:
    """Download trong background thread.

    done_callback(file_path: Optional[str]) khi xong.
    """
    def _worker():
        result = download_update(
            download_url,
            expected_hash=expected_hash,
            require_hash=require_hash,
            progress_callback=progress_callback,
        )
        if done_callback:
            done_callback(result)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


# ══════════════════════════════════════════════════════════════════════════════
#  CÀI ĐẶT CẬP NHẬT
# ══════════════════════════════════════════════════════════════════════════════

def install_update(installer_path: str, silent: bool = False, very_silent: bool = False) -> bool:
    """Chạy installer và thoát app hiện tại.

    Returns False nếu không thể chạy installer.
    """
    p = Path(installer_path)
    if not p.exists() or not p.suffix.lower() == ".exe":
        try:
            print(f"[Updater] Invalid installer file: {installer_path}")
        except Exception:
            pass
        return False

    try:
        flags = []
        if very_silent:
            flags = ["/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES"]
        elif silent:
            flags = ["/SILENT"]
        cmd = [str(p)] + flags
        subprocess.Popen(
            cmd,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            if sys.platform == "win32" else 0,
        )
        return True
    except Exception as e:
        try:
            print(f"[Updater] Installer error: {e}")
        except Exception:
            pass
        return False


def apply_update(download_url: str, silent: bool = True) -> None:
    """Tải và thực thi installer ngầm theo chuẩn github-auto-update."""
    temp_installer = Path(tempfile.gettempdir()) / "mea_setup_update.exe"
    # ponytail: stdlib urllib chunked stream download; upgrade to resume-capable downloader if large files fail on unstable connections.
    import urllib.request
    req = urllib.request.Request(
        download_url,
        headers={"User-Agent": f"MEA-Updater/{APP_VERSION}"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        with open(str(temp_installer), "wb") as f:
            while True:
                chunk = resp.read(8192)
                if not chunk:
                    break
                f.write(chunk)

    flags = ["/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES"] if silent else []
    cmd = [str(temp_installer)] + flags
    subprocess.Popen(
        cmd,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        if sys.platform == "win32" else 0,
    )
    sys.exit(0)


# ══════════════════════════════════════════════════════════════════════════════
#  SKIP VERSION
# ══════════════════════════════════════════════════════════════════════════════

def skip_version(version: str) -> None:
    """Đánh dấu bỏ qua phiên bản này (không nhắc lại)."""
    try:
        _SKIP_FILE.write_text(version.strip(), encoding="utf-8")
    except Exception:
        pass


def _is_skipped(version: str) -> bool:
    """Kiểm tra phiên bản có bị skip không."""
    try:
        if _SKIP_FILE.exists():
            return _SKIP_FILE.read_text(encoding="utf-8").strip() == version.strip()
    except Exception:
        pass
    return False


def clear_skip() -> None:
    """Xóa đánh dấu skip (dùng khi user chủ động kiểm tra cập nhật)."""
    try:
        _SKIP_FILE.unlink(missing_ok=True)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  CLEANUP
# ══════════════════════════════════════════════════════════════════════════════

def cleanup_old_downloads() -> None:
    """Xóa các file installer cũ trong thư mục updates."""
    try:
        for f in _UPDATE_DIR.iterdir():
            if f.is_file() and f.suffix.lower() in (".exe", ".msi", ".tmp"):
                try:
                    f.unlink()
                except Exception:
                    pass
    except Exception:
        pass
