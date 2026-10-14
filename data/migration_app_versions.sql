-- ============================================================================
--  Migration: Tạo bảng app_versions cho auto-update
--  Chạy trên Supabase Dashboard → SQL Editor
-- ============================================================================

-- Bảng lưu thông tin các phiên bản đã phát hành
CREATE TABLE IF NOT EXISTS app_versions (
    id          SERIAL PRIMARY KEY,
    version     TEXT NOT NULL,                          -- "4.1.0"
    channel     TEXT NOT NULL DEFAULT 'stable',         -- stable | beta
    changelog   TEXT DEFAULT '',                        -- Nội dung thay đổi (markdown)
    download_url TEXT NOT NULL,                         -- URL tải installer (.exe)
    file_size   BIGINT DEFAULT 0,                      -- Dung lượng file (bytes)
    file_hash   TEXT DEFAULT '',                        -- SHA256 hash để verify
    min_version TEXT DEFAULT '',                        -- Phiên bản tối thiểu (bắt buộc nâng cấp nếu < min)
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,          -- Còn hiệu lực hay đã thu hồi
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Index tìm kiếm nhanh
CREATE INDEX IF NOT EXISTS idx_app_versions_channel ON app_versions(channel, is_active);
CREATE INDEX IF NOT EXISTS idx_app_versions_created ON app_versions(created_at DESC);

-- Bật RLS (Row Level Security) — cho phép đọc công khai, chỉ admin ghi
ALTER TABLE app_versions ENABLE ROW LEVEL SECURITY;

-- Policy: Mọi người được SELECT (app kiểm tra cập nhật)
CREATE POLICY "Allow public read" ON app_versions
    FOR SELECT USING (true);

-- Policy: Chỉ authenticated users (admin) được INSERT/UPDATE/DELETE
CREATE POLICY "Allow admin write" ON app_versions
    FOR ALL USING (auth.role() = 'authenticated');

-- ============================================================================
--  Ví dụ: Thêm bản phát hành đầu tiên
-- ============================================================================
--
-- INSERT INTO app_versions (version, channel, changelog, download_url, file_size, file_hash, min_version)
-- VALUES (
--     '4.1.0',
--     'stable',
--     '- Thêm tính năng chèn ảnh vào câu hỏi và đáp án
-- - Thêm tính năng cập nhật tự động
-- - Sửa lỗi xuất Word',
--     'https://github.com/Do-Miinh-1210/MatrixExamAI/releases/download/v4.1.0/MEA_v4_Setup.exe',
--     52428800,
--     'sha256:abcdef1234567890...',
--     '4.0.0'
-- );
