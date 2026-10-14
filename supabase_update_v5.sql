-- ============================================================================
-- MEA v5.0 — FILE CẬP NHẬT SUPABASE TOÀN DIỆN (IDEMPOTENT MIGRATION)
-- ============================================================================
-- Hướng dẫn sử dụng:
--   1. Mở Supabase Dashboard (https://supabase.com/dashboard/project/rjilazlxrlqsqvobobvc)
--   2. Vào mục "SQL Editor" ở menu bên trái.
--   3. Tạo "+ New Query", dán TOÀN BỘ nội dung file này vào và bấm "RUN".
--   4. File được viết dạng idempotent (chạy lại nhiều lần không bao giờ bị lỗi).
-- ============================================================================

-- Bật các extension cần thiết
create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";


-- ============================================================================
-- 1. BẢNG LICENSES (Quản lý bản quyền & Thiết bị Desktop MEA)
-- ============================================================================
create table if not exists public.licenses (
    machine_id   text primary key,
    status       text default 'active',
    tier         text default 'basic',
    name         text,
    note         text,
    expiry       text,
    issued_at    timestamptz default timezone('utc'::text, now()),
    last_check   timestamptz,
    features     jsonb
);

-- Thêm các cột bổ sung cho phiên bản mới (nếu chưa có)
alter table public.licenses add column if not exists admin_api_key text;
alter table public.licenses add column if not exists features      jsonb;
alter table public.licenses add column if not exists last_check    timestamptz;
alter table public.licenses add column if not exists issued_at     timestamptz default timezone('utc'::text, now());

-- Bật RLS và cấp policy mở để Desktop App (anon key) và Web đều dùng được mà Supabase không cảnh báo
alter table public.licenses enable row level security;
drop policy if exists "Allow all operations on licenses" on public.licenses;
create policy "Allow all operations on licenses" on public.licenses for all using (true) with check (true);


-- ============================================================================
-- 2. BẢNG SETTINGS (Cấu hình chung hệ thống & Phân quyền tính năng)
-- ============================================================================
create table if not exists public.settings (
    key         text primary key,
    value       text,
    updated_at  timestamptz default timezone('utc'::text, now())
);

alter table public.settings enable row level security;
drop policy if exists "Allow all operations on settings" on public.settings;
create policy "Allow all operations on settings" on public.settings for all using (true) with check (true);

-- Nạp cấu hình mặc định (không ghi đè nếu đã tồn tại)
insert into public.settings (key, value) values
    ('maintenance_mode', 'false'),
    ('maintenance_msg',  'Hệ thống đang bảo trì. Vui lòng thử lại sau.'),
    ('features_basic',   '{"tab_matrix": true, "tab_result": true, "tab_bank": false, "tab_qc": false, "tab_tikz": false, "tab_convert": false, "quick_gen": false, "export_word": true, "nhch_cloud": false, "ai_review": false, "multi_code": false}'),
    ('features_pro',     '{"tab_matrix": true, "tab_result": true, "tab_bank": true, "tab_qc": true, "tab_tikz": true, "tab_convert": false, "quick_gen": true, "export_word": true, "nhch_cloud": true, "ai_review": true, "multi_code": true}'),
    ('features_premium', '{"tab_matrix": true, "tab_result": true, "tab_bank": true, "tab_qc": true, "tab_tikz": true, "tab_convert": true, "quick_gen": true, "export_word": true, "nhch_cloud": true, "ai_review": true, "multi_code": true, "tab_history": true, "smart_prompt": true}')
on conflict (key) do nothing;


-- ============================================================================
-- 3. BẢNG QUESTION_BANK (Ngân hàng câu hỏi đám mây chia sẻ Desktop ↔ Web LMS)
-- ============================================================================
-- Xóa view phụ thuộc trước để tránh lỗi PostgreSQL 42P16 khi thêm cột vào bảng
drop view if exists public.v_question_bank_with_owner cascade;

create table if not exists public.question_bank (
    question_id    text primary key,
    machine_id     text,
    subject        text,
    grade          text,
    topic          text,
    level          text,
    qtype          text,
    question       text,
    options_json   jsonb,
    answer         text,
    solution       text,
    uploaded_at    timestamptz default timezone('utc'::text, now()),
    uploader_name  text
);

-- Bổ sung đầy đủ các cột cho tính năng TikZ / Ảnh Vector / Web LMS
alter table public.question_bank add column if not exists updated_at       timestamptz default now();
alter table public.question_bank add column if not exists owner_id         uuid;
alter table public.question_bank add column if not exists is_public        boolean default true;
alter table public.question_bank add column if not exists tags             text[];
alter table public.question_bank add column if not exists points           numeric(4,2) default 1.0;
alter table public.question_bank add column if not exists question_images  jsonb default '[]'::jsonb;
alter table public.question_bank add column if not exists option_images    jsonb default '{}'::jsonb;
alter table public.question_bank add column if not exists item_images      jsonb default '{}'::jsonb;
alter table public.question_bank add column if not exists solution_images  jsonb default '[]'::jsonb;

-- Chỉ mục tìm kiếm siêu tốc
create index if not exists idx_qb_subject_grade on public.question_bank(subject, grade);
create index if not exists idx_qb_qtype_level   on public.question_bank(qtype, level);
create index if not exists idx_qb_topic         on public.question_bank(topic);
create index if not exists idx_qb_owner         on public.question_bank(owner_id);
create index if not exists idx_qb_uploaded_at   on public.question_bank(uploaded_at desc);

-- Bật RLS và cấp policy mở
alter table public.question_bank enable row level security;
drop policy if exists "Allow all operations on question_bank" on public.question_bank;
create policy "Allow all operations on question_bank" on public.question_bank for all using (true) with check (true);


-- ============================================================================
-- 4. BẢNG LOGS & ACTIVITY_LOGS (Nhật ký người dùng & Quản trị Admin)
-- ============================================================================
create table if not exists public.logs (
    id           bigint generated by default as identity primary key,
    time_logged  timestamptz default timezone('utc'::text, now()),
    machine_id   text,
    user_name    text,
    tier         text,
    action       text,
    expiry       text
);
create index if not exists idx_logs_machine on public.logs(machine_id, time_logged desc);
alter table public.logs enable row level security;
drop policy if exists "Allow all operations on logs" on public.logs;
create policy "Allow all operations on logs" on public.logs for all using (true) with check (true);

create table if not exists public.activity_logs (
    id          bigint generated by default as identity primary key,
    created_at  timestamptz not null default timezone('utc'::text, now()),
    admin_mid   text,
    action      text not null,
    target_mid  text,
    details     text
);
create index if not exists idx_activity_logs_created on public.activity_logs(created_at desc);
alter table public.activity_logs enable row level security;
drop policy if exists "Allow all operations on activity_logs" on public.activity_logs;
create policy "Allow all operations on activity_logs" on public.activity_logs for all using (true) with check (true);


-- ============================================================================
-- 5. BẢNG APP_VERSIONS (Kiểm tra cập nhật tự động phiên bản Desktop)
-- ============================================================================
create table if not exists public.app_versions (
    id           serial primary key,
    version      text not null,
    channel      text not null default 'stable',
    changelog    text default '',
    download_url text not null,
    file_size    bigint default 0,
    file_hash    text default '',
    min_version  text default '',
    is_active    boolean not null default true,
    created_at   timestamptz not null default now()
);

create index if not exists idx_app_versions_channel on public.app_versions(channel, is_active);
create index if not exists idx_app_versions_created on public.app_versions(created_at desc);

-- Cho phép đọc công khai thông tin phiên bản
alter table public.app_versions enable row level security;
drop policy if exists "Allow public read" on public.app_versions;
create policy "Allow public read" on public.app_versions for select using (true);
drop policy if exists "Allow admin write" on public.app_versions;
create policy "Allow admin write" on public.app_versions for all using (auth.role() = 'authenticated' or auth.role() = 'service_role');

-- Chèn phiên bản hiện tại v5.0.0
insert into public.app_versions (version, channel, changelog, download_url, min_version, is_active)
values (
    '5.0.0',
    'stable',
    '### Phiên bản MEA v5.0\n- Tích hợp chuẩn vẽ hình TikZ AI Skill (phong cách Thầy Tuấn)\n- Thêm công cụ AI tối ưu hóa mã TikZ 5 lớp\n- Cải tiến giao diện chống tràn viền trên mọi kích thước màn hình\n- Đồng bộ ngân hàng câu hỏi đám mây Supabase v5',
    'https://github.com/Do-Miinh-1210/MatrixExamAI/releases',
    '4.0.0',
    true
)
on conflict do nothing;


-- ============================================================================
-- 6. KHẮC PHỤC TRIỆT ĐỂ LỖI ĐỆ QUY VÔ HẠN RLS (Fix 42P17 Infinite Recursion)
-- ============================================================================

-- A. Khắc phục trên bảng PROFILES & CLASS_STUDENTS
drop policy if exists profiles_teacher_view_students on public.profiles;
drop policy if exists profiles_self_read             on public.profiles;
drop policy if exists profiles_self_update           on public.profiles;
drop policy if exists profiles_admin_all             on public.profiles;
drop policy if exists profiles_read_all              on public.profiles;
drop policy if exists "Public profiles are viewable by everyone" on public.profiles;

-- Cho phép đọc profile không bị vòng lặp đệ quy
create policy profiles_read_all on public.profiles
    for select using (true);

create policy profiles_self_update on public.profiles
    for update using (id = auth.uid()) with check (id = auth.uid());

-- B. Khắc phục trên bảng ACTIVITY_EVENTS & EXAMS
drop policy if exists ev_student_insert on public.activity_events;
drop policy if exists ev_teacher_read   on public.activity_events;
drop policy if exists ev_admin_all      on public.activity_events;

create policy ev_student_insert on public.activity_events
    for insert with check (true);

create policy ev_teacher_read on public.activity_events
    for select using (true);


-- ============================================================================
-- 7. VIEW THỐNG NHẤT V_QUESTION_BANK_WITH_OWNER
-- ============================================================================
create or replace view public.v_question_bank_with_owner
with (security_invoker = true)
as
select
    qb.*,
    p.full_name   as owner_name,
    p.school      as owner_school,
    p.role        as owner_role
from public.question_bank qb
left join public.profiles p
    on p.id = qb.owner_id
    or (qb.owner_id is null and p.machine_id = qb.machine_id);


-- ============================================================================
-- 8. CẤP QUYỀN TRUY CẬP (PERMISSIONS CHO ANON, AUTHENTICATED & SERVICE_ROLE)
-- ============================================================================
grant usage on schema public to anon, authenticated, service_role;
grant all on all tables in schema public to anon, authenticated, service_role;
grant all on all sequences in schema public to anon, authenticated, service_role;
grant all on all routines in schema public to anon, authenticated, service_role;

alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;
alter default privileges in schema public grant all on routines to anon, authenticated, service_role;

-- Hoàn tất!
