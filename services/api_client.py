"""
services/api_client.py — HTTP client tới FastAPI Backend v5 (tuỳ chọn).

Mục đích chính: thay thế DẦN việc EXE gọi thẳng Supabase bằng việc gọi qua
FastAPI có JWT — giúp:
  • Không phải hardcode SUPABASE_KEY trong EXE (xem config.py:414-415).
  • Centralize RLS + audit log ở backend.
  • Sync EXE ↔ Web LMS qua API duy nhất.

Bật tính năng: set `MEA_API_URL=http://localhost:8000` trong .env
                (mặc định: nếu chưa set → license_manager fallback Supabase trực tiếp).

Token storage:
  ~/.exam_generator/lms.json — { access_token, refresh_token, email, ts }
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

_log = logging.getLogger(__name__)

_TOKEN_FILE = Path.home() / ".exam_generator" / "lms.json"
_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

# Default timeouts (seconds)
DEFAULT_TIMEOUT = 30
LOGIN_TIMEOUT = 15


# ═════════════════════════════════════════════════════════════════════════════
#  Public API
# ═════════════════════════════════════════════════════════════════════════════

def api_url() -> str:
    """Trả MEA_API_URL từ env. "" nếu chưa cấu hình (caller phải fallback)."""
    return (os.environ.get("MEA_API_URL", "")
              or _read_env_file_var("MEA_API_URL", "")).rstrip("/")


def is_api_enabled() -> bool:
    """True khi user đã cấu hình MEA_API_URL → ưu tiên dùng API thay Supabase."""
    return bool(api_url())


def _runtime_env_path() -> Path:
    """Return the .env location read on the next source or frozen startup."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / ".env"
    return Path(__file__).resolve().parent.parent / ".env"


def save_api_url(url: str) -> Path:
    """Persist MEA_API_URL beside the application and update this process."""
    normalized = str(url or "").strip().rstrip("/")
    if not normalized:
        raise ValueError("MEA_API_URL không được để trống.")
    os.environ["MEA_API_URL"] = normalized
    env_path = _runtime_env_path()
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    updated = False
    for index, line in enumerate(lines):
        if line.strip().startswith("MEA_API_URL="):
            lines[index] = f"MEA_API_URL={normalized}"
            updated = True
            break
    if not updated:
        lines.append(f"MEA_API_URL={normalized}")
    env_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = env_path.with_name(env_path.name + ".tmp")
    temp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    temp_path.replace(env_path)
    return env_path


def is_api_reachable(timeout: float = 3.0) -> bool:
    """Ping /health của backend FastAPI v5. Trả False nếu down/timeout."""
    url = api_url()
    if not url:
        return False
    try:
        import requests
        r = requests.get(f"{url}/health", timeout=timeout)
        return r.status_code == 200 and r.json().get("ok") is True
    except Exception as e:
        _log.debug("API not reachable: %s", e)
        return False


# ── Token mgmt ───────────────────────────────────────────────────────────────

def load_token() -> dict[str, Any]:
    """Đọc token từ ~/.exam_generator/lms.json. Trả {} nếu chưa có."""
    try:
        if _TOKEN_FILE.exists():
            return json.loads(_TOKEN_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        _log.warning("Read token fail: %s", e)
    return {}


def save_token(data: dict[str, Any]) -> None:
    """Lưu token + timestamp vào ~/.exam_generator/lms.json."""
    try:
        data = {**data, "ts": int(time.time())}
        _TOKEN_FILE.write_text(json.dumps(data, ensure_ascii=False),
                                 encoding="utf-8")
    except Exception as e:
        _log.warning("Save token fail: %s", e)


def clear_token() -> None:
    try:
        _TOKEN_FILE.unlink(missing_ok=True)
    except Exception:
        pass


# ── Auth ─────────────────────────────────────────────────────────────────────

def login(email: str, password: str) -> dict[str, Any]:
    """Đăng nhập qua Supabase Auth (POST trực tiếp /auth/v1/token).

    Trả dict {ok, access_token, refresh_token, email, error}.
    Không qua FastAPI vì Supabase Auth endpoint là public REST.

    LƯU Ý: cần SUPABASE_URL + SUPABASE_KEY (anon) trong env hoặc config.
    """
    try:
        import requests
        from config import SUPABASE_URL, SUPABASE_KEY
        url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        headers = {
            "apikey":       SUPABASE_KEY,
            "Content-Type": "application/json",
        }
        r = requests.post(url, headers=headers,
                            json={"email": email, "password": password},
                            timeout=LOGIN_TIMEOUT)
        if r.status_code != 200:
            return {"ok": False,
                    "error": f"HTTP {r.status_code}: {r.text[:200]}"}
        data = r.json()
        token = {
            "access_token":  data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", ""),
            "email":         email,
            "expires_in":    data.get("expires_in", 3600),
        }
        save_token(token)
        return {"ok": True, **token}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def refresh_access_token() -> dict[str, Any]:
    """Refresh access_token bằng refresh_token đã lưu."""
    try:
        import requests
        from config import SUPABASE_URL, SUPABASE_KEY
        tok = load_token()
        rt = tok.get("refresh_token")
        if not rt:
            return {"ok": False, "error": "No refresh_token. Hãy login lại."}
        url = f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token"
        headers = {"apikey": SUPABASE_KEY, "Content-Type": "application/json"}
        r = requests.post(url, headers=headers,
                            json={"refresh_token": rt}, timeout=LOGIN_TIMEOUT)
        if r.status_code != 200:
            clear_token()
            return {"ok": False,
                    "error": f"Refresh failed: {r.status_code}"}
        data = r.json()
        new_tok = {
            "access_token":  data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", rt),
            "email":         tok.get("email", ""),
            "expires_in":    data.get("expires_in", 3600),
        }
        save_token(new_tok)
        return {"ok": True, **new_tok}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def is_logged_in() -> bool:
    return bool(load_token().get("access_token"))


# ── API call wrapper ─────────────────────────────────────────────────────────

def call(method: str, path: str, *,
         json_body: Optional[dict] = None,
         params: Optional[dict] = None,
         timeout: float = DEFAULT_TIMEOUT,
         auto_refresh: bool = True) -> dict[str, Any]:
    """Gọi 1 endpoint FastAPI với JWT tự động + auto-refresh khi 401.

    Trả dict {ok, status, data, error}.
    """
    url = api_url()
    if not url:
        return {"ok": False, "error": "MEA_API_URL chưa cấu hình"}
    tok = load_token()
    access = tok.get("access_token", "")
    if not access:
        return {"ok": False, "error": "Chưa login. Gọi api_client.login() trước."}

    try:
        import requests
        full = f"{url}{path if path.startswith('/') else '/' + path}"
        headers = {"Authorization": f"Bearer {access}",
                   "Content-Type": "application/json"}
        r = requests.request(method.upper(), full,
                               headers=headers,
                               json=json_body, params=params,
                               timeout=timeout)
        if r.status_code == 401 and auto_refresh:
            ref = refresh_access_token()
            if ref.get("ok"):
                # Retry 1 lần (không auto_refresh nữa để tránh loop vô tận)
                return call(method, path, json_body=json_body, params=params,
                             timeout=timeout, auto_refresh=False)
            return {"ok": False, "status": 401, "error": "Token hết hạn, login lại."}

        try:
            data = r.json()
        except Exception:
            data = r.text

        return {
            "ok":     r.status_code < 400,
            "status": r.status_code,
            "data":   data,
            "error":  "" if r.status_code < 400 else str(data)[:300],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Convenience methods cho các endpoint v5 ──────────────────────────────────

def license_ping(machine_id: str, app_version: str = "4.1.0") -> dict[str, Any]:
    """POST /v1/desktop/license — đồng bộ machine_id + lấy license info."""
    return call("POST", "/v1/desktop/license",
                  json_body={"machine_id": machine_id,
                             "app_version": app_version})


def latest_version(channel: str = "") -> dict[str, Any]:
    """GET /v1/desktop/version[/channel] — kiểm tra bản mới (public, không cần auth)."""
    url = api_url()
    if not url:
        return {"ok": False, "error": "MEA_API_URL chưa cấu hình"}
    channel = str(channel or "").strip().strip("/")
    suffix = f"/v1/desktop/version/{channel}" if channel else "/v1/desktop/version"
    try:
        import requests
        r = requests.get(f"{url}{suffix}", timeout=10)
        return {"ok": r.status_code == 200, "data": r.json()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def sync_questions(questions: list[dict]) -> dict[str, Any]:
    """POST /v1/desktop/sync/questions — upload NHCH qua API (an toàn hơn ghi thẳng)."""
    return call("POST", "/v1/desktop/sync/questions",
                  json_body={"questions": questions})


# ── Image upload via Supabase Storage (cho push ảnh local lên cloud) ─────────

_STORAGE_BUCKET = "question-images"

def upload_image_to_storage(local_path: str, *, folder: str = "") -> dict[str, Any]:
    """Upload 1 file ảnh từ local → Supabase Storage `question-images` bucket.

    Trả {ok, url, error}. URL là public URL có thể dùng trực tiếp trong web LMS.
    Yêu cầu bucket `question-images` đã tồn tại (public). Xem README để tạo.

    Args:
        local_path: đường dẫn file ảnh
        folder: subfolder trong bucket (vd "uploads/2026-05" cho organize)
    """
    from pathlib import Path
    p = Path(local_path)
    if not p.exists() or not p.is_file():
        return {"ok": False, "error": f"File không tồn tại: {local_path}"}

    try:
        from config import SUPABASE_URL, SUPABASE_KEY
        # Tên file unique
        import uuid as _u
        ext = p.suffix.lower() or ".png"
        fname = f"{folder.rstrip('/') + '/' if folder else ''}img_{_u.uuid4().hex[:12]}{ext}"

        # Cần token user (RLS storage). Nếu chưa login → fail rõ ràng.
        tok = load_token()
        access = tok.get("access_token", "")
        if not access:
            # Fallback: dùng anon key (chỉ chạy nếu bucket policy cho phép anon write)
            access = SUPABASE_KEY

        import requests
        # MIME type
        ctype_map = {".png": "image/png", ".jpg": "image/jpeg",
                     ".jpeg": "image/jpeg", ".gif": "image/gif",
                     ".webp": "image/webp", ".bmp": "image/bmp"}
        ctype = ctype_map.get(ext, "application/octet-stream")

        url_upload = f"{SUPABASE_URL}/storage/v1/object/{_STORAGE_BUCKET}/{fname}"
        with p.open("rb") as f:
            r = requests.post(url_upload, data=f.read(),
                                headers={"Authorization": f"Bearer {access}",
                                         "Content-Type": ctype,
                                         "x-upsert": "true"},
                                timeout=60)
        if r.status_code not in (200, 201):
            return {"ok": False,
                    "error": f"Upload fail HTTP {r.status_code}: {r.text[:200]}"}

        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{_STORAGE_BUCKET}/{fname}"
        return {"ok": True, "url": public_url, "path": fname}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def upload_images_batch(local_paths: list[str], *, folder: str = "",
                          progress_cb=None) -> list[str]:
    """Upload nhiều ảnh → trả list URL public theo thứ tự.

    File upload thất bại → giữ NGUYÊN local path trong list (caller có thể
    detect bằng cách check `startswith('http')`).
    """
    out: list[str] = []
    n = len(local_paths)
    for i, p in enumerate(local_paths, 1):
        if progress_cb:
            progress_cb(i, n, f"Upload ảnh {i}/{n}...")
        # Nếu đã là URL → skip upload
        if isinstance(p, str) and (p.startswith("http://") or p.startswith("https://")):
            out.append(p); continue
        r = upload_image_to_storage(p, folder=folder)
        out.append(r["url"] if r.get("ok") else p)
    return out


def upload_question_images(q_dict: dict, *, folder: str = "") -> dict:
    """Helper: trong 1 dict câu hỏi, upload tất cả ảnh local → thay = URL.

    Tự sửa các field: question_images, option_images, item_images,
    solution_images. Trả về dict mới (không mutate input).
    """
    from services.image_fields import normalize_image_field
    out = dict(q_dict)
    # Single-list fields
    for key in ("question_images", "solution_images"):
        local = normalize_image_field(out.get(key) or [])
        out[key] = upload_images_batch(local, folder=folder) if local else []
    # Dict fields (option_images / item_images)
    for dict_key in ("option_images", "item_images"):
        d = out.get(dict_key) or {}
        new_d = {}
        for k, v in d.items():
            local = normalize_image_field(v)
            new_d[k] = upload_images_batch(local, folder=folder) if local else []
        out[dict_key] = new_d
    return out


def sync_exam(exam: dict, questions: list[dict], publish: bool = True) -> dict[str, Any]:
    """POST /v1/desktop/sync/exam — push 1 đề + câu hỏi → tạo exam + publish."""
    return call("POST", "/v1/desktop/sync/exam",
                  json_body={**exam, "questions": questions, "publish": publish})


# ── Helpers ──────────────────────────────────────────────────────────────────

def _read_env_file_var(key: str, default: str = "") -> str:
    """Đọc 1 key từ file .env (tránh phụ thuộc python-dotenv)."""
    try:
        from pathlib import Path
        for envfile in (Path.cwd() / ".env", _runtime_env_path()):
            if envfile.exists():
                for line in envfile.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("#") or "=" not in line:
                        continue
                    k, _, v = line.partition("=")
                    if k.strip() == key:
                        return v.strip().strip('"').strip("'")
    except Exception:
        pass
    return default
