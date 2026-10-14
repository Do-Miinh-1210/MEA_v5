"""
services/license_manager.py — Online License Manager (Supabase-based) v3.
Cập nhật: đổi unlimited → premium, thêm admin_api_key.
"""

from __future__ import annotations
import hashlib
import json
import logging
import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from supabase import create_client, Client

# Logger — dùng để log các fallback attempt (wmic/winreg/ioreg/machine-id)
# ở debug level, không làm crash app nhưng vẫn có audit trail khi debug.
_log = logging.getLogger(__name__)

from config import (
    SUPABASE_URL,
    SUPABASE_KEY,
    APP_NAME,
    APP_VERSION,
    LICENSE_CACHE_HOURS,
    FEATURE_CATALOG,
    get_default_features,
)

_CACHE_FILE = Path.home() / ".exam_generator" / "license_cache.json"
_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── KHỞI TẠO SUPABASE CLIENT ──────────────────────────────────────────────────
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        supabase = None
except Exception as e:
    _log.error("Lỗi khởi tạo Supabase client: %s", e, exc_info=True)
    supabase = None


# ── MACHINE ID ────────────────────────────────────────────────────────────────
def get_machine_id() -> str:
    raw = _get_hardware_uuid()
    h   = hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()[:12].upper()
    return f"{h[0:4]}-{h[4:8]}-{h[8:12]}"

def _get_hardware_uuid() -> str:
    system = platform.system()
    if system == "Windows":
        try:
            _si = subprocess.STARTUPINFO()
            _si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            _si.wShowWindow = subprocess.SW_HIDE
            out = subprocess.check_output(
                ["wmic", "csproduct", "get", "uuid"],
                timeout=5, stderr=subprocess.DEVNULL,
                creationflags=0x08000000,
                startupinfo=_si,
            ).decode(errors="ignore")
            lines = [l.strip() for l in out.splitlines() if l.strip() and l.strip() != "UUID"]
            if lines: return lines[0]
        except Exception as e:
            _log.debug("wmic csproduct uuid fallback: %s", e)
        try:
            import winreg
            key  = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            guid, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            return guid
        except Exception as e:
            _log.debug("winreg MachineGuid fallback: %s", e)
    elif system == "Darwin":
        try:
            out = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                timeout=5, stderr=subprocess.DEVNULL,
            ).decode(errors="ignore")
            for line in out.splitlines():
                if "IOPlatformUUID" in line:
                    return line.split('"')[-2]
        except Exception as e:
            _log.debug("ioreg IOPlatformUUID fallback: %s", e)
    elif system == "Linux":
        for p in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
            try:
                c = Path(p).read_text().strip()
                if c: return c
            except Exception as e:
                _log.debug("read %s fallback: %s", p, e)
    _log.warning("Không xác định được hardware UUID, dùng fallback tổ hợp platform info.")
    return f"{platform.node()}|{os.environ.get('USERNAME','')}|{platform.machine()}"

def get_machine_display() -> str:
    return f"{platform.system()} {platform.release()} — {platform.node()}"


# ── CACHE ─────────────────────────────────────────────────────────────────────
def _load_cache() -> Optional[dict]:
    try:
        data = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
        age_hours = (datetime.now() - cached_at).total_seconds() / 3600
        if age_hours < LICENSE_CACHE_HOURS:
            return data
    except FileNotFoundError:
        # Cache chưa tồn tại — bình thường ở lần chạy đầu
        pass
    except Exception as e:
        _log.debug("license cache read failed: %s", e, exc_info=True)
    return None

def _save_cache(result: dict) -> None:
    try:
        result["cached_at"] = datetime.now().isoformat()
        _CACHE_FILE.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        _log.warning("Không thể ghi license cache: %s", e)

def _clear_cache() -> None:
    try:
        _CACHE_FILE.unlink(missing_ok=True)
    except Exception as e:
        _log.debug("clear license cache: %s", e)


def _resolve_features(tier: str, custom_features: dict) -> dict[str, bool]:
    defaults = get_default_features("premium")
    # Bản mở khóa: luôn kích hoạt toàn bộ tính năng
    for k in FEATURE_CATALOG:
        defaults[k] = True
    return defaults


# ── PUBLIC API (Client App) ───────────────────────────────────────────────────
def check_license(force_online: bool = False) -> dict:
    mid = get_machine_id()

    if not force_online and LICENSE_CACHE_HOURS > 0:
        cached = _load_cache()
        if cached and cached.get("mid") == mid and cached.get("ok"):
            cached["from_cache"] = True
            cached["features"] = get_default_features("premium")
            cached["tier"] = "premium"
            return cached

    # ── (v5 path) Nếu user đã cấu hình MEA_API_URL → gọi FastAPI ──────────────
    try:
        from services import api_client
        if api_client.is_api_enabled() and api_client.is_logged_in():
            api_res = api_client.license_ping(mid, APP_VERSION)
            if api_res.get("ok"):
                d = api_res.get("data", {})
                result = {
                    "ok":         True,
                    "status":     "active",
                    "tier":       "premium",
                    "name":       d.get("name", "Người dùng MEA"),
                    "expiry":     "Vĩnh viễn",
                    "features":   get_default_features("premium"),
                    "message":    "OK",
                    "from_cache": False,
                    "mid":        mid,
                    "via_api":    True,
                }
                _save_cache(result)
                return result
    except Exception as e:
        _log.debug("api_client path skipped: %s", e)

    # Fallback bản mở khóa khi không có Supabase / Supabase lỗi
    unlocked_result = {
        "ok": True,
        "status": "active",
        "tier": "premium",
        "name": "Bản mở khóa cục bộ",
        "expiry": "Vĩnh viễn",
        "features": get_default_features("premium"),
        "message": "Đã mở khóa toàn bộ tính năng (chế độ độc lập)",
        "from_cache": False,
        "mid": mid,
        "offline": True,
    }

    if not supabase:
        return unlocked_result

    try:
        # Lấy dữ liệu user từ database (nếu kết nối được)
        user_res = supabase.table('licenses').select('*').eq('machine_id', mid).execute()
        if not user_res.data:
            # Nếu máy chưa đăng ký trong DB hoặc DB bị lỗi, vẫn mở khóa Premium
            return unlocked_result
        
        user = user_res.data[0]
        admin_api_key = user.get('admin_api_key', '')

        # Active -> Cập nhật last_check nếu có thể
        try:
            now_str = datetime.now().isoformat()
            supabase.table('licenses').update({'last_check': now_str}).eq('machine_id', mid).execute()
        except Exception:
            pass

        result = {
            "ok": True,
            "status": "active",
            "tier": "premium",
            "name": user.get('name') or "Bản mở khóa cục bộ",
            "expiry": "Vĩnh viễn",
            "features": get_default_features("premium"),
            "message": "OK",
            "from_cache": False,
            "mid": mid,
            "admin_api_key": admin_api_key,
        }
        _save_cache(result)
        return result

    except Exception as e:
        _log.debug("Supabase query error (%s), fallback unlocked: %s", e)
        return unlocked_result

def is_activated() -> bool:
    return True

def get_tier() -> str:
    return "premium"


# ── ADMIN HELPERS ─────────────────────────────────────────────────────────────
def admin_add(mid: str, name: str, tier: str = "pro", note: str = "", expiry: str = "") -> dict:
    try:
        exists = supabase.table('licenses').select('machine_id').eq('machine_id', mid).execute()
        if exists.data:
            return {"ok": False, "error": "machine_id đã tồn tại"}
        
        data = {
            "machine_id": mid,
            "status": "active",
            "tier": tier,
            "name": name,
            "note": note,
            "expiry": expiry,
            "issued_at": datetime.now().isoformat()
        }
        supabase.table('licenses').insert(data).execute()
        return {"ok": True, "message": f"Đã thêm {mid}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def admin_import_users(users_list: list[dict]) -> dict:
    try:
        if not users_list:
            return {"ok": True, "message": "Không có dữ liệu"}
        for i in range(0, len(users_list), 100):
            batch = users_list[i:i+100]
            supabase.table('licenses').upsert(batch).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def admin_revoke(mid: str) -> dict:
    try:
        supabase.table('licenses').update({"status": "revoked"}).eq('machine_id', mid).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def admin_restore(mid: str) -> dict:
    try:
        supabase.table('licenses').update({"status": "active"}).eq('machine_id', mid).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def admin_list() -> list[dict]:
    try:
        res = supabase.table('licenses').select('*').order('issued_at', desc=True).execute()
        return res.data
    except Exception:
        return []

def admin_list_with_settings() -> dict:
    try:
        records = admin_list()
        maint_res = supabase.table('settings').select('value').eq('key', 'maintenance_mode').execute()
        maint = False
        if maint_res.data and str(maint_res.data[0]['value']).lower() == 'true':
            maint = True
        return {"ok": True, "records": records, "maintenance_mode": maint}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def admin_maintenance_on(msg: str = "") -> dict:
    try:
        supabase.table('settings').upsert({"key": "maintenance_mode", "value": "true"}).execute()
        if msg:
            supabase.table('settings').upsert({"key": "maintenance_msg", "value": msg}).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def admin_maintenance_off() -> dict:
    try:
        supabase.table('settings').upsert({"key": "maintenance_mode", "value": "false"}).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def admin_lock_all() -> dict:
    try:
        supabase.table('licenses').update({"status": "revoked"}).eq('status', 'active').execute()
        return {"ok": True, "message": "Đã khóa thành công"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def admin_unlock_all() -> dict:
    try:
        supabase.table('licenses').update({"status": "active"}).eq('status', 'revoked').execute()
        return {"ok": True, "message": "Đã mở khóa thành công"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def admin_get_settings() -> dict:
    try:
        res = supabase.table('settings').select('*').execute()
        return {row['key']: row['value'] for row in res.data}
    except Exception:
        return {}

def admin_set_settings(key: str, value: str) -> dict:
    try:
        supabase.table('settings').upsert({"key": key, "value": str(value)}).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def admin_set_features(mid: str, features: dict[str, bool]) -> dict:
    try:
        supabase.table('licenses').update({"features": features}).eq('machine_id', mid).execute()
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── NHCH (Ngân hàng câu hỏi chung — chia sẻ v4 ↔ v5) ─────────────────────────
def nhch_upload_batch(
    questions: list[dict],
    mid: str,
    uploader_name: str = "",
    overwrite: bool = False,
) -> dict:
    """Upload/đồng bộ NHCH lên Supabase (bảng `question_bank`).

    Quan trọng (v5 compatibility):
        - KHÔNG truncate `question` / `solution` — giữ nguyên LaTeX dài.
        - Mặc định `is_public=True` để Web LMS thấy ngay câu mới (không cần convert).
        - Nếu `overwrite=True`: upsert đè câu trùng `question_id` (dùng khi sửa câu cũ).
          Nếu `overwrite=False` (mặc định): chỉ insert câu mới, bỏ qua câu trùng.

    Schema (xem `schema_v4_v5_unified.sql`):
        question_id (PK), machine_id, subject, grade, topic, level, qtype,
        question, options_json, answer, solution, uploaded_at, uploader_name,
        updated_at, owner_id, is_public, tags, points.
    """
    if not supabase:
        return {"ok": False, "error": "Chưa kết nối Supabase"}
    if not questions:
        return {"ok": True, "saved": 0, "skipped": 0, "added": 0}

    # ── (v5 path) Ưu tiên gọi qua API nếu MEA_API_URL set + đã login ──────
    # Lý do: an toàn hơn ghi thẳng Supabase từ EXE; centralize RLS + audit.
    try:
        from services import api_client
        if api_client.is_api_enabled() and api_client.is_logged_in():
            payload = []
            for q in questions:
                qid = q.get("question_id") or q.get("qid")
                if not qid:
                    continue
                payload.append({
                    "question_id": qid,
                    "subject":  q.get("subject", "") or "",
                    "grade":    str(q.get("grade", "") or ""),
                    "topic":    q.get("topic", "") or "",
                    "level":    q.get("level", "") or "",
                    "qtype":    q.get("qtype", "") or "",
                    "question": q.get("question", "") or "",
                    "options":  q.get("options") or q.get("options_json") or {},
                    "answer":   q.get("answer", "") or "",
                    "solution": q.get("solution", "") or "",
                    "points":   float(q.get("points", 1.0) or 1.0),
                })
            api_res = api_client.sync_questions(payload)
            if api_res.get("ok"):
                d = api_res.get("data", {})
                return {
                    "ok":      True,
                    "added":   d.get("upserted", 0),
                    "saved":   d.get("upserted", 0),
                    "skipped": d.get("skipped", 0),
                    "via_api": True,
                    "message": f"(API) Upsert {d.get('upserted', 0)} câu, "
                                 f"bỏ qua {d.get('skipped', 0)}.",
                }
            _log.warning("sync_questions via API fail (%s) → fallback Supabase",
                          api_res.get("error", "?"))
    except Exception as e:
        _log.debug("api_client path skipped: %s", e)

    try:
        # 1. Dedup theo qid trong batch + lọc bỏ qid rỗng
        seen: set[str] = set()
        clean: list[dict] = []
        skipped_local = 0
        for q in questions:
            qid = q.get("question_id") or q.get("qid")
            if not qid or qid in seen:
                skipped_local += 1
                continue
            seen.add(qid)
            clean.append({**q, "question_id": qid})

        if not clean:
            return {"ok": True, "added": 0, "saved": 0, "skipped": skipped_local,
                    "message": "Không có câu hợp lệ để upload."}

        # 2. Nếu KHÔNG overwrite → loại bỏ câu đã tồn tại trên server
        skipped_dup = 0
        rows_to_upsert: list[dict] = []

        if not overwrite:
            qids = [q["question_id"] for q in clean]
            # Supabase .in_() có giới hạn URL ~2KB → chia batch 100
            existing_ids: set[str] = set()
            for i in range(0, len(qids), 100):
                chunk = qids[i:i+100]
                res = supabase.table('question_bank').select('question_id').in_('question_id', chunk).execute()
                existing_ids.update(row['question_id'] for row in (res.data or []))

            for q in clean:
                if q["question_id"] in existing_ids:
                    skipped_dup += 1
                    continue
                rows_to_upsert.append(_build_qb_row(q, mid, uploader_name))
        else:
            rows_to_upsert = [_build_qb_row(q, mid, uploader_name) for q in clean]

        # 3. Upsert theo batch 100 (tránh payload quá lớn)
        added = 0
        for i in range(0, len(rows_to_upsert), 100):
            chunk = rows_to_upsert[i:i+100]
            ins = supabase.table('question_bank').upsert(
                chunk, on_conflict='question_id'
            ).execute()
            added += len(ins.data or [])

        skipped = skipped_local + skipped_dup
        return {
            "ok": True,
            "added": added,
            "saved": added,
            "skipped": skipped,
            "skipped_invalid": skipped_local,
            "skipped_duplicate": skipped_dup,
            "message": f"Đã upload {added} câu, bỏ qua {skipped} câu (trùng: {skipped_dup}, lỗi: {skipped_local})."
        }
    except Exception as e:
        _log.error("nhch_upload_batch error: %s", e, exc_info=True)
        return {"ok": False, "error": str(e), "added": 0, "skipped": 0}


def _build_qb_row(q: dict, mid: str, uploader_name: str) -> dict:
    """Chuyển 1 dict câu hỏi v4 → row khớp schema unified (v4+v5).

    KHÔNG truncate question/solution (giữ LaTeX dài). is_public=True để
    Web LMS thấy ngay câu này khi GV search NHCH.
    """
    return {
        "question_id":   q["question_id"],
        "machine_id":    mid or "",
        "subject":       q.get("subject", "") or "",
        "grade":         str(q.get("grade", "") or ""),
        "topic":         q.get("topic", "") or "",
        "level":         q.get("level", "") or "",
        "qtype":         q.get("qtype", "") or "",
        "question":      q.get("question", "") or "",        # ⚠️ KHÔNG truncate
        "options_json":  q.get("options") or q.get("options_json") or {},
        "answer":        q.get("answer", "") or "",
        "solution":      q.get("solution", "") or "",        # ⚠️ KHÔNG truncate
        "uploader_name": uploader_name or mid or "",
        "is_public":     True,                               # v5 — câu sẵn sàng cho Web LMS
        "points":        float(q.get("points", 1.0) or 1.0),
        # owner_id sẽ được FastAPI tự gán khi GV đăng nhập web (link machine_id → profile)
    }


def nhch_list(subject: str = "", grade: str = "", level: str = "", qtype: str = "", limit: int = 200) -> list[dict]:
    try:
        query = supabase.table('question_bank').select('*').order('uploaded_at', desc=True)
        if subject: query = query.eq('subject', subject)
        if grade:   query = query.eq('grade', grade)
        if level:   query = query.eq('level', level)
        if qtype:   query = query.eq('qtype', qtype)
        
        res = query.limit(limit).execute()
        questions = res.data
        
        for q in questions:
            if "options_json" in q:
                q["options"] = q["options_json"] or {}
        return questions
    except Exception as e:
        raise RuntimeError(f"Lỗi tải NHCH: {e}") from e


def nhch_stats() -> dict:
    try:
        res = supabase.table('question_bank').select('qtype, level, subject').execute()
        data = res.data
        total = len(data)
        byType, byLevel, bySubject = {}, {}, {}
        for row in data:
            t = row.get('qtype', '')
            l = row.get('level', '')
            s = row.get('subject', '')
            if t: byType[t] = byType.get(t, 0) + 1
            if l: byLevel[l] = byLevel.get(l, 0) + 1
            if s: bySubject[s] = bySubject.get(s, 0) + 1
            
        return {
            "ok": True, "total": total,
            "by_type": byType, "by_level": byLevel, "by_subject": bySubject
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def nhch_delete(question_id: str) -> dict:
    try:
        supabase.table('question_bank').delete().eq('question_id', question_id).execute()
        return {"ok": True, "message": "Đã xóa câu hỏi."}
    except Exception as e:
        return {"ok": False, "error": str(e)}