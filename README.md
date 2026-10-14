# MEA — MatrixExam AI v5.0.0

> **Desktop app cho giáo viên Toán THPT tạo đề kiểm tra bằng AI**
> Tkinter • Python 3.10+ • 5 AI providers • Share Supabase DB với MEA v5 Web LMS

## ⚡ Khởi động nhanh

```bash
# Chạy từ source
pip install -r requirements.txt
python main.py

# Hoặc dùng EXE đã build
dist/MEA_v4.exe
```

Lần đầu chạy: nhập **API key** ở tab **⚙️ Cài đặt** (Gemini / Claude / DeepSeek).

## ✨ Tính năng chính

| Nhóm | Chi tiết |
|---|---|
| **Tạo đề bằng AI** | Ma trận đặc tả NB/TH/VD × TN/DS/TLN/TL — 5 AI providers |
| **Import từ file** | PDF / Word / Ảnh → AI Vision OCR → câu hỏi (format chuẩn Bộ 2024-2026) |
| **NHCH** | SQLite cục bộ + đồng bộ Supabase Cloud (chia sẻ với LMS v5 Web) |
| **Chất lượng (QC)** | Solver1→Solver2→Critic→Math→Score — AI Review & auto-fix |
| **TikZ vẽ hình** | Editor + AI sinh hình từ mô tả, Overleaf, tự lưu Kho hình, PDF → EMF vector cho Word |
| **Xuất Word** | Multi mã đề (A-F), đáp án, lời giải, multi-image, ưu tiên EMF vector |
| **🌐 LMS Sync** | Login Web LMS → push đề → HS thi online qua mã đề |

## 📂 Cấu trúc

```
MEA_v4/
├── main.py                  # Entry point
├── config.py                # Constants + license tiers
├── core/                    # Business logic (parser, generator, models, ID system)
├── services/                # AI providers, license, api_client, updater, TikZ, cache
├── ui/                      # 25 tab + 15 dialog (Tkinter)
├── storage/                 # SQLite NHCH cục bộ
├── export/                  # Word + matrix exporters
├── admin/                   # Sub-app Tkinter quản trị
├── admin_web/               # Flask Vercel (legacy — sẽ migrate Next.js v5)
├── data/                    # Chương trình học, ma trận mẫu
├── assets/                  # Icon, logo
├── tests/                   # 25 file pytest
└── dist/                    # EXE output (132 MB)
```

## 🔑 Cấu hình `.env`

```env
# Dùng chung Supabase với Web LMS v5
SUPABASE_URL=https://rjilazlxrlqsqvobobvc.supabase.co
SUPABASE_KEY=sb_publishable_4xA76_VnO6EE5AlykJPAeg_VgwZIG4J

# Tuỳ chọn: bật v5 API path (license/NHCH đi qua FastAPI thay vì direct Supabase)
MEA_API_URL=http://localhost:8000
```

App có sẵn fallback hardcoded trong [config.py](config.py) — không cần `.env` cũng chạy được.

## 🏗 Build EXE

```bash
pip install pyinstaller>=6.0
python tools/upgrade_app.py --test-mode fast
# → dist/MEA_v4.exe + dist/MEA_v4_Admin.exe + dist/MEA_v5_alpha.exe
```

Lệnh `tools/upgrade_app.py` tự chạy test gate, build ở thư mục tạm trên ổ còn
trống, selftest EXE rồi mới thay artifact trong `dist/`. Mặc định lệnh build cả
V4 và V5; có thể dùng `--target v4` hoặc `--target v5` khi chỉ cần một bản.
Nếu chỉ cần tạo manifest cho bản EXE hiện có:

```bash
python tools/upgrade_app.py --skip-build --test-mode fast --manifest-only
# → dist/update_manifest_v4.json + dist/update_manifest_v5.json
```

Mỗi manifest có trường `channel` tương ứng `v4` hoặc `v5`. Khi phát hành riêng hai bản,
đặt `MEA_UPDATE_URL_V4` và `MEA_UPDATE_URL_V5`; biến chung `MEA_UPDATE_URL` vẫn dùng
được như fallback tương thích cũ.

Build installer (cần [Inno Setup 6](https://jrsoftware.org/isdl.php)):

```bash
iscc installer.iss
# → dist/installer/MEA_v4_Setup.exe
```

## 🔗 Tích hợp với MEA v5 Web LMS

App v4 đã sẵn sàng share Supabase với [MEA_v5_web](../MEA_v5_web/). Xem [SHARED_DB_SETUP.md](SHARED_DB_SETUP.md) để setup chung 1 project Supabase.

**Workflow GV:**
1. Tạo đề trong app Desktop (AI hoặc NHCH)
2. Tab **🌐 LMS** → Login → Push đề → nhận `exam_code`
3. HS truy cập `http://lms.matrixexam.ai/exam/{code}` để thi online

## 📚 Tài liệu chi tiết

| File | Nội dung |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Kiến trúc & data flow |
| [FEATURES.md](FEATURES.md) | Chi tiết từng tab + feature |
| [WORKFLOWS.md](WORKFLOWS.md) | Use cases & user journeys |
| [ROADMAP.md](ROADMAP.md) | Lộ trình v4 → v5 |
| [SHARED_DB_SETUP.md](SHARED_DB_SETUP.md) | Setup chung DB với LMS v5 |
| [MIGRATION_TO_V5.md](MIGRATION_TO_V5.md) | Lộ trình hoàn thiện vấn đề tồn đọng |
| [schema_v4_v5_unified.sql](schema_v4_v5_unified.sql) | SQL schema (4 v4 + 9 v5 tables + RLS) |
| [RELEASE_NOTES_v4.2.2.md](RELEASE_NOTES_v4.2.2.md) | Changelog v4.2.2 |
| [RELEASE_NOTES_v4.2.1.md](RELEASE_NOTES_v4.2.1.md) | Changelog v4.2.1 |
| [RELEASE_NOTES_v4.2.0.md](RELEASE_NOTES_v4.2.0.md) | Changelog v4.2.0 |
| [tests/README.md](tests/README.md) | Hướng dẫn chạy test |
| [Prompt Chatbot/README.md](Prompt%20Chatbot/README.md) | Prompts AI dùng trong app |

## 📦 Yêu cầu hệ thống

- **Windows 10/11** (chính); macOS/Linux chưa test
- **Python 3.10+** (nếu chạy source)
- **LaTeX engine** cho TikZ (tuỳ chọn): TeX Live / MiKTeX / Tectonic
- **Inkscape** (tuỳ chọn): cần khi dùng xuất hoặc copy EMF vector sang Word
- **Internet**: cần để gọi AI + sync NHCH Cloud

## 📞 Liên hệ

Zalo: 033.999.8261 • Email: dominh200270@gmail.com

(c) 2026 DoMiinhMath — Cá nhân/giáo dục.
