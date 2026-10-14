"""
admin/supabase_api.py — Tầng API giao tiếp Supabase cho Admin.
Tập trung tất cả thao tác CRUD trực tiếp với Supabase vào 1 nơi.
"""

from __future__ import annotations
from config import SUPABASE_URL, SUPABASE_KEY


def _get_client():
    """Tạo Supabase client (lazy, không cache vì admin ít gọi)."""
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── User CRUD (direct Supabase) ─────────────────────────────────────────────

def update_api_key(mid: str, key: str) -> None:
    sb = _get_client()
    sb.table('licenses').update({"admin_api_key": key}).eq("machine_id", mid).execute()


def clear_api_key(mid: str) -> None:
    update_api_key(mid, "")


def update_tier(mid: str, new_tier: str) -> None:
    sb = _get_client()
    sb.table('licenses').update({"tier": new_tier}).eq("machine_id", mid).execute()


def update_expiry(mid: str, expiry_iso: str) -> None:
    """expiry_iso: YYYY-MM-DD hoặc '' cho vĩnh viễn."""
    sb = _get_client()
    sb.table('licenses').update({"expiry": expiry_iso}).eq("machine_id", mid).execute()


# ── Activity logs ────────────────────────────────────────────────────────────

def fetch_activity_logs(limit: int = 200) -> list[dict]:
    """Lấy log hoạt động gần nhất từ bảng activity_logs (nếu có)."""
    try:
        sb = _get_client()
        resp = sb.table('activity_logs').select('*').order(
            'created_at', desc=True
        ).limit(limit).execute()
        return resp.data or []
    except Exception:
        return []


def log_admin_action(action: str, target_mid: str = "", details: str = "") -> None:
    """Ghi 1 dòng log hành động admin."""
    try:
        from services.license_manager import get_machine_id
        sb = _get_client()
        sb.table('activity_logs').insert({
            "admin_mid": get_machine_id(),
            "action": action,
            "target_mid": target_mid,
            "details": details,
        }).execute()
    except Exception:
        pass


# ── Stats ────────────────────────────────────────────────────────────────────

def fetch_user_stats() -> dict:
    """Lấy thống kê tổng quan từ bảng licenses."""
    try:
        sb = _get_client()
        resp = sb.table('licenses').select('status, tier, last_check, expiry').execute()
        records = resp.data or []
        total = len(records)
        by_status = {}
        by_tier = {}
        for r in records:
            s = r.get("status", "unknown")
            t = r.get("tier", "basic")
            by_status[s] = by_status.get(s, 0) + 1
            by_tier[t] = by_tier.get(t, 0) + 1

        # Active trong 7 ngày
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        active_7d = sum(
            1 for r in records
            if r.get("last_check") and r["last_check"] >= week_ago
        )

        return {
            "total": total,
            "by_status": by_status,
            "by_tier": by_tier,
            "active_7d": active_7d,
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_expiring_soon(days: int = 30) -> list[dict]:
    """Lấy danh sách user sắp hết hạn trong N ngày."""
    try:
        from datetime import datetime, timedelta
        sb = _get_client()
        cutoff = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        resp = sb.table('licenses').select('machine_id, name, tier, expiry, status').gt(
            'expiry', today
        ).lte('expiry', cutoff).eq('status', 'active').execute()
        return resp.data or []
    except Exception:
        return []
