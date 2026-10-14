"""
bootstrap_v5.py — Setup tự động cho integration MEA v4 ↔ v5 Web LMS.

Chạy 1 lệnh để:
    1. Test kết nối Supabase (service_role key)
    2. ALTER schema: thêm columns images vào question_bank
    3. Tạo Storage bucket 'question-images' (public)
    4. Setup RLS policy cho bucket (anyone read, authenticated write)
    5. Seed teacher test (optional)
    6. Verify end-to-end

Usage:
    # Mặc định dùng SUPABASE_SERVICE_ROLE_KEY từ env hoặc backend/.env
    python bootstrap_v5.py

    # Override URL/key qua CLI
    python bootstrap_v5.py --url https://xxx.supabase.co --key eyJ...

    # Chỉ chạy phần cụ thể
    python bootstrap_v5.py --only schema       # chỉ ALTER
    python bootstrap_v5.py --only bucket       # chỉ tạo bucket
    python bootstrap_v5.py --only seed         # chỉ tạo teacher test
    python bootstrap_v5.py --skip seed         # bỏ qua phần đó

Yêu cầu:
    - pip install supabase>=2.15.0 requests
    - SUPABASE_SERVICE_ROLE_KEY (KHÔNG phải anon!) — lấy từ Supabase Dashboard
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────
BUCKET_NAME = "question-images"
DEFAULT_TEACHER_EMAIL = "teacher.test@mea-lms.local"
DEFAULT_TEACHER_PASS  = "TestPass123!"

ALTER_SQL = """
-- ── Bổ sung columns images cho question_bank (v4.2+) ─────────────────────────
alter table public.question_bank
    add column if not exists question_images  jsonb default '[]'::jsonb,
    add column if not exists option_images    jsonb default '{}'::jsonb,
    add column if not exists item_images      jsonb default '{}'::jsonb,
    add column if not exists solution_images  jsonb default '[]'::jsonb;

-- ── Drop policies _admin_all dùng is_admin() → tránh RLS recursion ──────────
do $$ begin
    drop policy if exists profiles_admin_all              on public.profiles;
    drop policy if exists profiles_teacher_view_students  on public.profiles;
    drop policy if exists classes_admin_all               on public.classes;
    drop policy if exists cs_admin_all                    on public.class_students;
    drop policy if exists exams_admin_all                 on public.exams;
    drop policy if exists ea_admin_all                    on public.exam_assignments;
    drop policy if exists subs_admin_all                  on public.submissions;
    drop policy if exists answers_admin_all               on public.answers;
    drop policy if exists ev_admin_all                    on public.activity_events;
end $$;
"""

STORAGE_RLS_SQL = """
-- ── Storage RLS cho bucket question-images ──────────────────────────────────
-- Anyone có thể READ ảnh (vì bucket public)
drop policy if exists "question_images public read"  on storage.objects;
create policy "question_images public read"
    on storage.objects for select
    using (bucket_id = 'question-images');

-- Authenticated user (teacher) có thể UPLOAD ảnh
drop policy if exists "question_images auth upload"  on storage.objects;
create policy "question_images auth upload"
    on storage.objects for insert
    with check (
        bucket_id = 'question-images'
        and auth.role() = 'authenticated'
    );

-- Owner có thể DELETE ảnh của mình
drop policy if exists "question_images owner delete" on storage.objects;
create policy "question_images owner delete"
    on storage.objects for delete
    using (
        bucket_id = 'question-images'
        and auth.uid() = owner
    );
"""

# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _read_env_file(path: Path, key: str) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    return ""


def _resolve_url_and_key(args) -> tuple[str, str]:
    """Lấy URL + SERVICE_ROLE_KEY từ args / env / .env files."""
    url = (args.url or os.environ.get("SUPABASE_URL", "") or
           _read_env_file(Path(__file__).parent / ".env", "SUPABASE_URL"))
    key = (args.key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or
           _read_env_file(Path(__file__).parent.parent / "MEA_v5_web" / "backend" / ".env",
                           "SUPABASE_SERVICE_ROLE_KEY"))
    return url.rstrip("/"), key


def _execute_sql_via_pg_api(url: str, service_key: str, sql: str) -> dict:
    """Execute raw SQL qua Supabase Management API hoặc PostgREST RPC."""
    # Supabase REST không expose arbitrary SQL trực tiếp; nhưng có thể dùng
    # Management API (cần Personal Access Token). Workaround: tạo function
    # `exec_sql` 1 lần bằng tay, sau đó gọi qua RPC.
    # → Phương án thực tế: in SQL ra cho user paste.
    import requests
    print()
    print("─" * 60)
    print("  ⚠ KHÔNG exec SQL DDL trực tiếp được qua REST API")
    print("  → Paste SQL dưới đây vào Supabase SQL Editor:")
    print("    https://supabase.com/dashboard/project/_/sql/new")
    print("─" * 60)
    print(sql.strip())
    print("─" * 60)
    return {"ok": False, "manual_paste_required": True}


# ─────────────────────────────────────────────────────────────────────────────
#  Steps
# ─────────────────────────────────────────────────────────────────────────────

def step_test_connection(url: str, key: str) -> bool:
    """1. Test kết nối + xác minh service_role key."""
    print("\n[1] 🔌 Test kết nối Supabase...")
    try:
        from supabase import create_client
        sb = create_client(url, key)
        # Thử select từ bảng licenses (cần đã chạy schema v4)
        r = sb.table("licenses").select("machine_id", count="exact").limit(1).execute()
        print(f"    ✓ Kết nối OK ({r.count or 0} licenses)")
        # Verify service_role bằng cách list users
        users = sb.auth.admin.list_users()
        print(f"    ✓ service_role key hợp lệ ({len(users)} auth users)")
        return True
    except Exception as e:
        print(f"    ✘ FAIL: {e}")
        return False


def step_alter_schema(url: str, key: str) -> bool:
    """2. ALTER schema: thêm columns images + drop bad policies."""
    print("\n[2] 🗄  ALTER schema (cần paste vào SQL Editor)...")
    _execute_sql_via_pg_api(url, key, ALTER_SQL)
    return False  # luôn manual


def step_create_bucket(url: str, key: str) -> bool:
    """3. Tạo Storage bucket question-images (public)."""
    print("\n[3] 🪣 Tạo bucket Storage 'question-images'...")
    try:
        from supabase import create_client
        sb = create_client(url, key)
        # List buckets để check tồn tại chưa
        try:
            buckets = sb.storage.list_buckets()
            names = [b.name if hasattr(b, "name") else b["name"]
                       for b in buckets]
        except Exception as e:
            print(f"    ⚠ list_buckets fail: {e}")
            names = []

        if BUCKET_NAME in names:
            print(f"    ✓ Bucket '{BUCKET_NAME}' đã tồn tại")
        else:
            try:
                sb.storage.create_bucket(BUCKET_NAME, options={"public": True})
                print(f"    ✓ Đã tạo bucket '{BUCKET_NAME}' (public)")
            except Exception as e:
                print(f"    ✘ create_bucket fail: {e}")
                print(f"    → Tạo thủ công: https://supabase.com/dashboard/project/_/storage/buckets")
                print(f"      Name: {BUCKET_NAME}  | ☑ Public bucket")
                return False
        return True
    except Exception as e:
        print(f"    ✘ FAIL: {e}")
        return False


def step_storage_rls(url: str, key: str) -> bool:
    """4. Setup RLS policy cho bucket."""
    print("\n[4] 🔒 Setup RLS policy cho bucket...")
    _execute_sql_via_pg_api(url, key, STORAGE_RLS_SQL)
    return False  # luôn manual


def step_seed_teacher(url: str, key: str,
                       email: str = DEFAULT_TEACHER_EMAIL,
                       pwd: str = DEFAULT_TEACHER_PASS) -> bool:
    """5. Seed 1 teacher để test."""
    print(f"\n[5] 👨‍🏫 Seed teacher: {email}")
    try:
        from supabase import create_client
        sb = create_client(url, key)
        users = sb.auth.admin.list_users()
        existing = next((u for u in users if u.email == email), None)
        if existing:
            print(f"    ✓ Đã tồn tại (id={existing.id[:8]}…)")
            tid = existing.id
        else:
            res = sb.auth.admin.create_user({
                "email": email, "password": pwd, "email_confirm": True,
                "user_metadata": {"full_name": "Teacher Test"},
            })
            tid = res.user.id
            print(f"    ✓ Tạo mới (id={tid[:8]}…)")

        # Đảm bảo role = teacher
        import time; time.sleep(1)  # đợi trigger handle_new_user
        sb.table("profiles").update({"role": "teacher",
                                       "full_name": "Teacher Test"}
                                       ).eq("id", tid).execute()
        prof = sb.table("profiles").select("role").eq("id", tid).execute()
        print(f"    ✓ profile.role = {prof.data[0]['role']}")
        print(f"\n    📋 Credential test:")
        print(f"       Email   : {email}")
        print(f"       Password: {pwd}")
        return True
    except Exception as e:
        print(f"    ✘ FAIL: {e}")
        return False


def step_verify_e2e(url: str, key: str) -> bool:
    """6. Verify end-to-end: insert question với images, đọc lại."""
    print("\n[6] 🧪 Verify E2E (insert + read question_bank với images)...")
    try:
        from supabase import create_client
        import time
        sb = create_client(url, key)
        qid = f"BOOTSTRAP-TEST-{int(time.time())}"
        sb.table("question_bank").insert({
            "question_id": qid,
            "subject": "Toán", "grade": "12", "topic": "Bootstrap",
            "level": "NB", "qtype": "TN",
            "question": "Câu test bootstrap.",
            "options_json": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "answer": "A", "solution": "",
            "question_images": ["https://example.com/test1.png",
                                  "https://example.com/test2.png"],
            "option_images": {"A": ["https://example.com/opt_a.png"]},
        }).execute()
        r = sb.table("question_bank").select("*").eq("question_id", qid).execute()
        if r.data:
            row = r.data[0]
            img_ok = (len(row.get("question_images") or []) == 2
                        and len(row.get("option_images", {}).get("A", [])) == 1)
            print(f"    ✓ Insert + read OK (images persistent: {img_ok})")
            sb.table("question_bank").delete().eq("question_id", qid).execute()
            return img_ok
        else:
            print(f"    ✘ Read failed sau insert")
            return False
    except Exception as e:
        print(f"    ✘ FAIL: {e}")
        print(f"    → Có thể schema chưa ALTER xong. Chạy step [2] trước.")
        return False


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

STEPS = {
    "connection": step_test_connection,
    "schema":     step_alter_schema,
    "bucket":     step_create_bucket,
    "rls":        step_storage_rls,
    "seed":       step_seed_teacher,
    "verify":     step_verify_e2e,
}


def main():
    ap = argparse.ArgumentParser(description="MEA v4↔v5 bootstrap setup")
    ap.add_argument("--url", help="SUPABASE_URL (override env)")
    ap.add_argument("--key", help="SUPABASE_SERVICE_ROLE_KEY (override env)")
    ap.add_argument("--only", choices=list(STEPS.keys()), help="Chạy chỉ 1 step")
    ap.add_argument("--skip", nargs="+", choices=list(STEPS.keys()), default=[],
                    help="Bỏ qua các step")
    ap.add_argument("--email", default=DEFAULT_TEACHER_EMAIL)
    ap.add_argument("--password", default=DEFAULT_TEACHER_PASS)
    args = ap.parse_args()

    print("═" * 60)
    print("  MEA v4 ↔ v5 — Bootstrap setup")
    print("═" * 60)

    url, key = _resolve_url_and_key(args)
    if not url or not key:
        print("\n✘ Thiếu SUPABASE_URL hoặc SUPABASE_SERVICE_ROLE_KEY")
        print("  Cách 1: set env var:")
        print("    SUPABASE_URL=https://xxx.supabase.co")
        print("    SUPABASE_SERVICE_ROLE_KEY=eyJhbG...")
        print("  Cách 2: --url + --key qua CLI")
        print("  Cách 3: copy MEA_v5_web/backend/.env vào root")
        sys.exit(1)

    print(f"\n  URL: {url}")
    print(f"  Key: {key[:12]}…{key[-8:]}")

    steps_to_run = ([args.only] if args.only
                      else [s for s in STEPS if s not in args.skip])
    results = {}
    for name in steps_to_run:
        fn = STEPS[name]
        if name == "seed":
            results[name] = fn(url, key, args.email, args.password)
        else:
            results[name] = fn(url, key)

    # ── Summary ──────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  SUMMARY")
    print("═" * 60)
    for name, ok in results.items():
        status = "✅ OK" if ok else "⚠ Manual paste"
        print(f"  {status}  {name}")
    print()
    print("  Tài liệu: SHARED_DB_SETUP.md, MIGRATION_TO_V5.md")
    print("═" * 60)


if __name__ == "__main__":
    main()
