# MEA v5 Desktop beta candidate — CustomTkinter rewrite

> **Mục tiêu**: thay Tkinter cũ bằng CustomTkinter cho UI hiện đại, sidebar,
> dark mode, gom 25 tab → 8 view rõ ràng. Song song với v4 — không phá build cũ.
>
> **Trạng thái migration đã audit (2026-05-27)**: các workflow runtime trong
> package `v5/` không còn import UI V4. Xem lộ trình beta và tiêu chí phát hành tại
> [V5_MIGRATION_ROADMAP.md](../V5_MIGRATION_ROADMAP.md).

## ⚡ Chạy thử

```bash
# Từ source
pip install customtkinter>=5.2.0 matplotlib>=3.7.0 tkinterdnd2
python -m v5.app

# Hoặc dùng EXE đã build
dist/MEA_v5_alpha.exe   # 152.7 MB
```

## 🎨 UI Layout

```
┌────────────────────────────────────────────────────────────┐
│ π MEA AI   [Xanh dương▾] [F1 Phím tắt] [☀🌙💻] GÓI THỰC    │  TopBar 48px
├─────────┬──────────────────────────────────────────────────┤
│ ☰       │                                                   │
│ 🏠 Home  │           View hiện tại                          │
│ ⚙️ Setup │                                                   │
│ ✏️ Create│           ┌──────┐                               │
│ 🏛 NHCH  │           │ ⠋ ⠹  │  ← Loading overlay khi long op │
│ 🔄 Convert│          │ msg  │                                │
│ ✅ QC    │           └──────┘                                │
│ 📊 Track │                                                   │
│ v5-alpha │                                                   │
├─────────┴──────────────────────────────────────────────────┤
│ │🌐 Online│🤖 5 calls│🏛 142 câu│📡 teacher@x   v5.0.0       │  StatusBar 28px
└────────────────────────────────────────────────────────────┘

[bottom-right]   ┌──────────────────────────┐
                 │ ✓ Đã lưu thay đổi         │  ← Toast 3s fade
                 └──────────────────────────┘
```

## 📦 Package V5 chính

```
v5/
├── __init__.py
├── app.py            ← Main app + routing + shortcuts (~360 LOC)
├── sidebar.py        ← Sidebar 8 view + collapse mode
├── splash.py         ← Splash 1.5s loading (~95 LOC)
├── onboarding.py     ← Wizard 3 bước lần đầu (~320 LOC)
├── settings_store.py ← JSON persist + recent_files API (~90 LOC)
├── toast.py          ← Toast widget stack-able (~95 LOC)
├── statusbar.py      ← 4 indicator refresh 30s (~100 LOC)
├── spinner.py        ← Loading overlay modal (~110 LOC)
├── ai_usage_summary.py ← Normalize + summarize/export AI usage logs
├── ai_usage_dialog.py  ← CTk AI Usage parity dialog
├── dashboard_insights.py ← Dashboard V4 summary/report helpers
├── user_profile.py   ← User/license profile helpers for Setup > License
├── question_cards.py ← Full question-by-question Exam Create preview cards
├── latex_preview.py  ← Per-question LaTeX render/copy/save dialog
├── variant_dialog.py ← Similar exam / AI variant dialog
├── README.md
└── views/
    ├── home.py
    ├── setup.py        (3 tab: AI / Lớp / License)
    ├── exam_create.py  (matrix + generate + multi mã + nguồn NHCH)
    ├── nhch.py         (browse + filter + recent files + sync)
    ├── qc.py           (pipeline 6 tiêu chí + TikZ)
    ├── tracking.py     (matplotlib chart + lịch sử + AI usage)
    ├── convert.py      (Ảnh/PDF/Word/Text → câu hỏi — CTk native)
    └── guide.py        (Alpha 13: Hướng dẫn 8 mục — 2 cột sidebar + content)
```

## ✨ 46 features production-ready

| # | Component | Mô tả |
|:-:|---|---|
| 1 | **App shell** | TopBar + Sidebar + Content + StatusBar grid |
| 2 | **Splash screen** | Logo + loading bar 1.5s |
| 3 | **Onboarding wizard** | 3 bước lần đầu (Welcome → API key → Done) |
| 4 | **8 view modular** | Home / Setup / Create / NHCH / Convert / QC / Track / Guide |
| 5 | **Sidebar collapse** | ☰ button toggle 250 ↔ 60 px (icons-only mode) |
| 6 | **TopBar** | Accent picker + F1 help + Theme switcher (☀🌙💻) |
| 7 | **Settings persist** | theme + last_view + geometry + onboarded + recent_files |
| 8 | **Drag-drop** | Thả 1 hoặc nhiều file PDF/Word/Ảnh → auto Import Wizard |
| 9 | **Keyboard shortcuts** | Ctrl+1..8 (đủ 8 view), Ctrl+G/E (action), F1, F5, Ctrl+Q |
| 10 | **Matplotlib chart** | AI usage 7d/30d (bar + line dual axis, dark/light theme) |
| 11 | **Toast notifications** | success/info/warn/error stack góc dưới-phải, fade 3s |
| 12 | **Loading spinner** | Modal overlay Braille animation cho long ops |
| 13 | **Recent files** | Menu 📂 trong NHCH — tracked auto, max 10, filter file đã xoá |
| 14 | **Status bar 4 indicator** | 🌐 Online / 🤖 AI calls / 🏛 NHCH / 📡 Backend status |
| 15 | **Image handling** | Chuẩn hóa ảnh local cho Convert, NHCH và xuất Word |
| 16 | **Lazy-load views** | Module imports chỉ chạy khi click → splash→paint nhanh hơn |
| 17 | **License parity** | Badge gói thật + feature gate dùng chung catalog với V4 |
| 18 | **Exam Create V4 parity** | Thư viện mẫu ma trận, xuất ma trận, auto-export + lưu NHCH sau khi sinh đề |
| 19 | **Analyze Exam parity** | Phân tích DOCX/PDF/TXT thành ma trận, AI tinh chỉnh, xuất Word/CSV |
| 20 | **Figure Bank parity** | Lưu, tìm, sửa, copy, xoá và nạp lại hình TikZ đã lưu trong V5 |
| 21 | **TikZ Shape Builder parity** | Dựng 39 loại hình/đồ thị/BBT/bảng xét dấu từ form thông số |
| 22 | **AI Usage parity** | Dialog CTk chi tiết: KPI, provider/model, quota warning, CSV, mở/xoá log |
| 23 | **Dashboard parity** | Tổng quan NHCH/đề đang mở, phân bổ QC, so sánh model, phân tích feedback, xuất báo cáo |
| 24 | **Similar exam parity** | Tạo đề tương tự bằng Python/SymPy, AI provider hoặc copy prompt thủ công |
| 25 | **Multi-code export parity** | Xuất mã A-F bằng service V4: trộn câu/đáp án, bảng đáp án, variant mode |
| 26 | **Load exam file parity** | Nạp DOCX/PDF/TeX/TXT/HTML vào preview bằng parser 3 tầng + AI fallback |
| 27 | **Exam metadata parity** | Sửa tiêu đề/môn/lớp/kỳ/năm/thời gian/trường/GV trong Tạo đề, đồng bộ autosave/history/Word |
| 28 | **Word export settings parity** | Chọn Text/MathType, kèm lời giải, tự mở file, auto-export và header mặc định như V4 |
| 29 | **User profile parity** | Setup > License hiển thị hồ sơ người dùng, copy mã máy/support info, hạn dùng và quyền theo gói như tab Người dùng V4 |
| 30 | **Question result cards parity** | Kết quả Tạo đề hiển thị đầy đủ từng câu, đáp án/lời giải/ảnh và mở sửa trực tiếp như V4 |
| 31 | **TikZ → EMF parity** | Chuyển TikZ trong đề thành EMF vector cho Word, giữ PNG preview và dùng workflow chung với V4 |
| 32 | **Question card actions parity** | Đổi thứ tự và xoá câu ngay trên card kết quả, đồng bộ cho preview/export/NHCH như V4 |
| 33 | **Question LaTeX preview parity** | Xem LaTeX từng câu trên card kết quả, copy ảnh hoặc lưu PNG bằng pipeline V5 độc lập UI V4 |
| 34 | **Question regenerate parity** | Tạo lại đúng một câu từ card kết quả bằng AI, giữ đồng bộ preview/export/NHCH/autosave như V4 |
| 35 | **Retry failed questions parity** | Tạo lại toàn bộ câu lỗi trong đề hiện tại, tự bật/tắt theo số câu `_error` và đồng bộ dữ liệu sau batch |
| 36 | **Current exam QC parity** | Chạy QC trực tiếp trên đề đang mở từ màn Kết quả hoặc tab QC, không cần load lại từ NHCH |
| 37 | **Result diagnostics parity** | Kiểm tra tổng điểm và xuất báo cáo câu lỗi ngay tại màn Kết quả, giống các thao tác nhanh của V4 |
| 38 | **Quick solution toggle parity** | Checkbox nhanh Kèm ĐA/LG trên màn Kết quả, đồng bộ với mọi đường xuất Word |
| 39 | **QC report export parity** | Xuất báo cáo QC từ V5 ra Excel/CSV với điểm, trạng thái, vấn đề và nội dung rút gọn |
| 40 | **QC apply results parity** | Áp dụng metadata `_review` từ kết quả QC vào đúng câu trong đề hiện tại theo `question_id`, đồng bộ autosave/history/export |
| 41 | **Quick exam editing UX** | Thanh Sửa nhanh trong Kết quả: đi tới câu theo số, sửa câu đang chọn, nhân bản để sửa và chèn câu trống thủ công |
| 42 | **Theme + Guide polish** | Palette V5 dùng chung, chữ phụ rõ hơn, tab Hướng dẫn 2 cột không lệch, có tìm mục lục và Bắt đầu nhanh |
| 43 | **UI frame pacing** | Gom cập nhật progress/QC/Convert theo nhịp khung hình, giảm animation toast/spinner quá dày để app mượt hơn khi sinh đề hoặc QC nhiều câu |
| 44 | **Incremental card rendering** | Panel xem từng câu render theo lô nhỏ, Import Wizard/AI Matrix/Variant cũng throttle progress để giảm khựng khi đề hoặc file import lớn |
| 45 | **Smooth mouse wheel router** | Cuộn chuột dùng router toàn cục, gom wheel bằng `after_idle`, tránh bindtags trùng và giữ Text/Treeview/PDF zoom cuộn đúng ngữ cảnh |
| 46 | **ChatBotAI prompt library** | Convert > AI Text có thư viện mẫu prompt Gemini GEM, ChatGPT, DeepSeek cho TN/DS/TLN/TL, TikZ, ma trận, OCR/import, tạo tương tự và sửa format |

## 🔧 8 view chi tiết

### 🏠 Home
4 quick-action cards (Tạo đề / Import PDF / QC / Convert) + 3 stat cards + tip box.

### ⚙️ Setup (3 tabs)
- **AI Provider**: 5 providers (Gemini / Claude / DeepSeek / OpenAI / Local), Fernet encrypted API key
- **Môn / Lớp**: Subject + Grade + HK
- **License**: Hồ sơ người dùng, Machine ID copy được, nguồn license, đếm ngược hạn dùng, quyền theo gói/admin override và refresh real-time

### ✏️ Exam Create
- Matrix table với add/delete dialog
- **📋 Phân tích đề** — đọc DOCX/PDF/TXT, tạo ma trận đặc tả, AI tinh chỉnh, xuất Word/CSV
- **📚 Thư viện mẫu ma trận** — nạp mẫu đóng gói theo lớp/từ khóa
- **📥 Xuất ma trận** — Word chuẩn BGD hoặc CSV
- Generate progress + spinner overlay
- Preview table
- **✏️ Sửa nhanh** — nhập số câu để đi tới/sửa, nhân bản câu làm bản mới hoặc chèn câu trống để soạn thủ công
- **👁 Xem chi tiết từng câu** — card nội dung/đáp án/lời giải/ảnh, sửa trực tiếp như V4
- **👁 LaTeX từng câu** — render công thức toán cho từng card, copy ảnh hoặc lưu PNG ngay trong V5
- **🔄 Tạo lại từng câu** — sinh lại một câu bằng AI từ ma trận gốc và thay vào đề hiện tại
- **🔁 Tạo lại lỗi** — tự sinh lại toàn bộ câu lỗi `_error`, cập nhật lại đề sau batch
- **✅ QC đề hiện tại** — chuyển sang tab Chất lượng với đúng đề đang mở trong workspace V5
- **🧮 Kiểm tra điểm / 📋 Báo cáo lỗi** — rà tổng điểm 10 và xuất TXT các câu `_error` để sửa nhanh
- **☑ Kèm ĐA/LG** — bật/tắt nhanh việc kèm đáp án và lời giải khi xuất Word, giống thanh Result V4
- **↕/✕ Thao tác card** — chuyển câu lên/xuống hoặc xoá khỏi đề đang mở, đồng bộ export/NHCH/autosave
- **📐 TikZ → EMF** — tạo EMF vector cho Word, giữ PNG preview và cập nhật card ngay trong app
- **✏️ Thông tin đề** — sửa metadata in trên header Word: tiêu đề, môn, lớp, kỳ, năm, thời gian, trường, GV
- **⚙️ Cài đặt xuất** — Text/MathType, kèm đáp án-lời giải, tự mở file sau xuất, auto-export, trường/GV mặc định
- **📥 Nạp đề file** — đọc DOCX/PDF/TeX/TXT/HTML vào preview để sửa/xuất/trộn mã
- **🔀 Trộn mã A-F** — service V4 parity: trộn câu trong từng phần, trộn đáp án TN, xuất Word + bảng đáp án
- **🧬 Đề tương tự** — thay số bằng Python/SymPy hoặc AI provider, kèm prompt thủ công cho chatbot ngoài app
- **🎛 Nguồn tạo đề** — chọn AI mới, 100% NHCH hoặc kết hợp theo tỉ lệ NHCH/AI
- **⚡ Auto-export Word sau khi sinh đề** + mở thư mục / bản sao / đổi chỗ / tắt tự xuất
- **🏛 Lưu câu hợp lệ vào NHCH** ngay từ màn kết quả
- **📄 Xuất Word thủ công**

### 🏛 NHCH
- Browse SQLite local
- Filter (qtype/level) + search keyword
- Tích `☐/☑` một/nhiều câu → **➕ Thêm vào đề** (tự tạo đề nháp nếu chưa có đề mở)
- **📂 Recent files** dropdown menu (10 files gần nhất)
- Import wizard CTk native
- Double-click → mở editor câu hỏi V5
- ☁ Sync ↑/↓ Cloud

### 🔄 Convert
- **Ảnh → Câu hỏi**: chọn nhiều ảnh hoặc dán clipboard, nhận diện bằng AI Vision.
- **PDF/Word → Câu hỏi**: ưu tiên text-layer cho PDF số, dùng Vision cho PDF scan.
- **AI Text → Câu hỏi**: chọn prompt gợi ý cho Gemini GEM / ChatGPT / DeepSeek, copy sang chatbot ngoài app, rồi parse cục bộ hoặc chuẩn hóa bằng AI.
- Kết quả hỗ trợ sửa, copy, xuất Word, lưu NHCH và **Thêm vào đề** đang mở.

### ✅ QC + TikZ (2 inner tabs)
- Load NHCH hoặc **Load đề hiện tại** từ workspace V5 → run `quality_pipeline` 6 tiêu chí
- 4 stat cards + bảng chi tiết màu Pass/Fail
- **📥 Báo cáo** — xuất kết quả QC ra Excel/CSV ngay trong V5
- **✅ Áp dụng** — gắn metadata `_review` từ QC vào đề hiện tại để autosave/history/export nhận đúng trạng thái kiểm định
- TikZ editor + AI generate code from description
- Render preview/PDF và thumbnail qua `services.tikz_renderer` không phụ thuộc UI V4
- **📐 Tạo hình** — Shape Builder thuần CTk sinh TikZ từ thông số, không cần gọi AI
- **🗂 Kho hình / 💾 Lưu kho** — Figure Bank thuần CTk: lưu metadata, PNG, tìm/lọc, nạp lại code

### 📊 Tracking (5 inner tabs)
- 4 stat cards (Đề / NHCH / AI calls 30d / Cost 30d)
- **📊 Tổng quan** — Dashboard V4 parity: NHCH, đề đang mở, phân bổ QC, model AI, câu nghi ngờ sai
- **🧠 Phân tích phản hồi** và **📄 Xuất báo cáo** ngay trong Tracking
- **📈 Biểu đồ matplotlib** — bar (calls) + line (tokens/ước tính token), toggle 7d/30d
- Lịch sử đề từ `exam_history`, có dialog CTk xem/so sánh/khôi phục phiên bản
- AI Usage log từ `~/.exam_generator/ai_usage.jsonl`
- **📊 Chi tiết AI** — KPI theo phạm vi, provider/model breakdown, quota warning, 50 request gần nhất, CSV, mở/xoá log

### 📖 Hướng dẫn
- 8 mục hướng dẫn chi tiết theo từng tab; sidebar mục lục + nội dung step-by-step.
- Layout 2 cột cố định, không lệch khi đổi kích thước cửa sổ.
- Có ô tìm mục hướng dẫn và khối **Bắt đầu nhanh** cho thao tác hay dùng.
- Palette dùng chung của V5 giúp chữ phụ/viền/nền rõ hơn ở cả light và dark mode.

### 🛡 Bảo trì dữ liệu
- Preferences tạo backup toàn bộ NHCH, ảnh, history và settings qua `services.local_backup`.
- API key mã hóa không được đưa vào backup trừ khi người dùng chọn rõ.
- Restore luôn tạo restore-point trước khi ghi đè và ghi kết quả vào Task Log.

### 🪪 License và quyền tính năng
- TopBar hiển thị gói license thực tế; trạng thái hết hạn/thu hồi khóa thao tác biên soạn.
- V5 dùng cùng `FEATURE_CATALOG` với V4 cho NHCH, QC, Convert, Smart Prompt, trộn mã đề và Cloud.
- Import qua kéo-thả hoặc file gần đây vẫn đi qua quyền NHCH, không tạo đường vòng.

## ⚡ Phím tắt toàn cục

| Phím | Tác dụng |
|---|---|
| `Ctrl+1` → `Ctrl+8` | Switch đủ 8 view (Home / Setup / ... / Convert / Guide) |
| `Ctrl+G` | Tạo đề (trong Exam Create) |
| `Ctrl+E` | Xuất Word |
| `F1` | Hiển thị help phím tắt |
| `F5` | Reload view hiện tại |
| `Ctrl+Q` | Thoát app |

## 🎨 Themes

| Mode | Chọn ở |
|---|---|
| Light / Dark / System | TopBar `[☀🌙💻]` segmented button |
| Accent color (Xanh dương / Xanh lá / Xanh đậm) | TopBar `[▾]` dropdown |

State save vào `~/.exam_generator/v5_settings.json`.

## 🚀 Build EXE

```bash
# v5 alpha
python build_v5_alpha.py
# → dist/MEA_v5_alpha.exe (~152.7 MB)
# Kiểm tra artifact:
dist/MEA_v5_alpha.exe --selftest

# Installer Inno Setup
python build_v5_installer.py
# → installer_v5.iss
# → (nếu có Inno Setup) dist/installer/MEA_v5_Setup.exe
```

## 📊 Migration status v4 → v5

| Feature v4 | Status v5 |
|---|:-:|
| AI Provider config | ✅ Setup view |
| Ma trận đặc tả + Generate | ✅ Exam Create + thư viện mẫu + xuất ma trận |
| Phân tích đề thi → ma trận | ✅ `v5/analyze_exam.py` thuần CTk + AI tinh chỉnh |
| Multi mã đề | ✅ Exam Create |
| Xuất Word | ✅ Exam Create |
| NHCH local | ✅ NHCH view |
| Filter / Search NHCH | ✅ NHCH view |
| Import PDF/Word/Ảnh | ✅ `v5/import_wizard.py` thuần CTk |
| Sửa câu | ✅ `v5/edit_question.py` thuần CTk |
| QC pipeline | ✅ QC view |
| TikZ vẽ hình | ✅ Editor + AI gen + renderer service V5-independent |
| TikZ Shape Builder | ✅ `v5/tikz_shape_builder.py` thuần CTk, 39 loại hình/form |
| Figure Bank / Kho hình | ✅ `v5/figure_bank_dialog.py` thuần CTk + `services.figure_bank` |
| AI Review & Fix | ✅ Trong dialog sửa câu (🤖 AI fix) |
| Dashboard / Lịch sử | ✅ Tracking view + tab Tổng quan V4 parity |
| AI Usage stats | ✅ Tracking chart + provider/cost + dialog chi tiết CTk |
| Login LMS + Push | ✅ LMS view + Exam Create |
| Smart Prompt | ✅ `v5/smart_prompt.py` (Ctrl+Shift+P) |
| Import PDF/Word/Ảnh | ✅ `v5/import_wizard.py` thuần CTk |
| Tải NHCH từ Cloud | ✅ `nhch_list` → save local |
| TikZ KB / Auto-heal | ✅ Auto-fix + 88 mẫu KB + AI heal (QC tab) |
| Multi-image edit | ✅ Trong dialog sửa câu CTk |

→ **UI CTk đã phủ các workflow chính** và package `v5/` không còn import UI V4
trong runtime. V5 dùng badge/quyền tính năng theo license thật như V4. EXE
ứng viên beta cục bộ đã qua selftest và viewtest; bước còn lại là
staging LMS, smoke DPI/dữ liệu thực và compile installer trên máy có Inno Setup.

## 🎯 Roadmap

```
✅ Alpha 1-7  — Full feature scaffolding + polish
✅ Alpha 8    — Crash reporter, updater, preferences, backup, Smart Prompt
✅ Alpha 9    — Audit & fix toàn bộ core function (generate/QC/export/NHCH)
✅ Alpha 10   — NHCH edit CTk + TikZ render + fix build (docx/fitz/jaraco)
✅ Alpha 11   — Import wizard CTk + tải Cloud + self-diagnostics
✅ Alpha 12   — TikZ auto-heal (rule + AI) + 88 mẫu KB → v5 ĐỘC LẬP 100%
✅ Alpha 13   — Port tab_convert (Vision OCR) + tab_guide (Hướng dẫn) → 9 views
✅ Alpha 14   — CTk Quick Gen dialog + sidebar action dispatch (3-tuple items)
✅ Alpha 15   — focus_*() methods cho QC/Tracking/Setup → sidebar sub-items
                  switch trực tiếp inner CTkTabview (immediate dispatch)
✅ Alpha 16   — Convert sub-actions (image/pdf/ai_text mode switch) + nút
                  "🕒 Lịch sử phiên bản đề" trong Tracking; quickswitch thêm
                  quick_gen + exam_history actions (16/20 sub-items có action)
✅ Alpha 17   — NHCH Stats dialog (CTk-native) + Task Log + Cache AI dialog;
                  Ctrl+T thêm 4 actions: quick_gen / exam_history / nhch_stats /
                  task_log (14 actions tổng)
✅ Alpha 18   — Fix TikZ preview bị bóp 1×1 px: wrap TikZ tab trong
                  CTkScrollableFrame + bỏ height=580 ràng buộc + preview inner
                  có height=420 + pack_propagate(False) (bbox: 1×1 → 1427×600)
✅ Alpha 19   — AI Gen Matrix dialog (CTk port từ ui/dialog_ai_gen_matrix.py):
                  form môn/lớp/HK/duration → core.ai_matrix_recognizer →
                  MatrixData. Wired vào exam_create header + Ctrl+T action.
                  15 QuickSwitcher actions tổng.
✅ Alpha 20   — Chuẩn hoá button sizes: v5/ui_constants.py 3-tier
                  (PRIMARY h=40 / SECONDARY h=32 / TERTIARY h=28). Apply:
                  NHCH/Tracking/Convert headers (28→32), LMS Login (28→40
                  PRIMARY), Setup Lưu key (28→32), QC Load + Start (36→40).
                  Heights giảm 5 → 4 tier, viewtest 9/9 PASS.
✅ Alpha 21   — UX rà soát toàn diện table + scroll:
                  • Thêm horizontal scrollbar cho 7 Treeviews (NHCH, QC,
                    Tracking history+usage, Exam Create preview, Task Log,
                    Import Wizard) — trước user mất nội dung khi window hẹp.
                  • Monkey-patch CTkScrollableFrame.__init__ trong v5/__init__
                    → auto-bind <MouseWheel> + Button-4/-5 (Linux) cho MỌI
                    instance. Trước phải kéo scrollbar bằng chuột.
                  • Helper v5.safe_ui.enable_mousewheel(scroll) cho usage
                    chính xác hơn.
✅ Alpha 24   — Vẽ lại kho TikZ: rà soát + fix 7 templates có toán SAI:
                  • build_tikz_contact_sheet.py — render 88 thumbnails →
                    ghép thành 4 trang PNG (dist/tikz_kb_pages/page_NN.png
                    + combined dist/tikz_kb_contact_sheet.png) cho user
                    inspect.
                  • Phát hiện bugs:
                    - Mặt cầu ngoại tiếp/nội tiếp lập phương + ngoại tiếp
                      chóp: circle dùng coord 2D trong scope 3D → LỆCH
                      khỏi cube/chóp center. Fix: scope lồng, dùng
                      coord I đã transform.
                    - Đường tròn ngoại/nội tiếp tam giác: circumcenter +
                      incenter sai vị trí (O=(2,1) cho tam giác (0,0)
                      (4,0)(1.5,3) thực ra là (2,0.875)). Fix: chuyển
                      sang tam giác đều — O = I = G = centroid.
                    - Tam giác có trực tâm H + trọng tâm G: tọa độ
                      scattered. Fix: tam giác đều → toán đơn giản.
✅ Alpha 29   — AI Usage V4 parity trong Tracking:
                  • v5/ai_usage_summary.py chuẩn hoá log prompt_chars/
                    response_chars của service hiện tại và tokens_in/
                    tokens_out nếu log mới có sẵn.
                  • v5/ai_usage_dialog.py CTk-native: KPI theo phạm vi,
                    provider/model/task breakdown, quota warning, 50 request
                    gần nhất, CSV export, mở thư mục log và xoá log.
                  • Tracking chart/provider/cost dùng chung helper mới nên
                    không còn hiển thị cost 0 giả khi log chỉ có ký tự.
✅ Alpha 30   — Dashboard V4 parity trong Tracking:
                  • Thêm tab "Tổng quan" với thống kê NHCH, đề đang mở,
                    phân bổ điểm QC, so sánh mô hình AI và câu nghi ngờ sai.
                  • Nút "Phân tích phản hồi" gọi services.adaptive_prompt để
                    rút bad/good patterns như V4.
                  • v5/dashboard_insights.py tách logic thuần + xuất báo cáo
                    text, không phụ thuộc ui.tab_dashboard.
✅ Alpha 31   — Đề tương tự / AI variant parity trong Tạo đề:
                  • Thêm nút "Đề tương tự" trong màn Tạo đề, nạp kết quả về
                    preview/export/push/NHCH như đề hiện tại.
                  • Dialog mới hỗ trợ copy/xem-sửa prompt thủ công, tạo bằng
                    Python/SymPy và tạo bằng AI provider đã cấu hình.
                  • v5/variant_dialog.py dùng services.similar_generator và
                    services.ai_variant_generator, không phụ thuộc ui.tab_result.
✅ Alpha 32   — Xuất nhiều mã đề giống V4 hơn:
                  • Nút "Trộn mã" chuyển sang dùng export.word_exporter.export_multi_code
                    thay vì tự shuffle trong view.
                  • Dialog có số mã A-F, trộn câu trong từng phần, trộn đáp án,
                    kèm lời giải, bảng đáp án riêng và progress khi xuất.
                  • Hỗ trợ variant mode ngay lúc xuất: none / Python-SymPy / AI
                    provider, kèm copy/xem-sửa prompt thủ công cho AI ngoài app.
✅ Alpha 33   — Nạp đề từ file vào màn Tạo đề:
                  • Thêm nút "Nạp đề file" trong phần Kết quả, hỗ trợ DOCX,
                    PDF, TeX, TXT và HTML như tab_result V4.
                  • Dùng core.exam_file_loader với parser 3 tầng:
                    ===CAU===, natural parser và LaTeX parser.
                  • Nếu parser cục bộ thất bại nhưng đọc được text, V5 hỏi
                    dùng AI fallback qua v5.convert_pipeline, không import ui.tab_convert.
✅ Alpha 34   — Sửa thông tin đề / header Word như V4:
                  • Thêm nút "Thông tin đề" trong phần Kết quả để sửa tiêu đề,
                    môn, lớp, kỳ, năm học, thời gian, trường và GV ra đề.
                  • Word export, auto-export và nhiều mã đề dùng trực tiếp metadata
                    đang mở; school/teacher được giữ qua ExamData.to_dict/from_dict.
                  • Autosave, lịch sử đề và app_settings không làm rơi thông tin
                    trường/GV khi khôi phục hoặc tạo đề tiếp theo.
✅ Alpha 35   — Cài đặt xuất Word giống V4 hơn:
                  • Thêm nút "Cài đặt xuất" trong Tạo đề: chọn Text inline hoặc
                    MathType/OMML, bật/tắt kèm đáp án-lời giải.
                  • Xuất thủ công, lưu bản sao và auto-export đọc cùng cấu hình
                    include-solution/open-after/math mode; nhiều mã đề lấy mặc định kèm lời giải từ đó.
                  • Trường/GV có thể chỉnh ngay trong cài đặt xuất và lưu làm mặc định
                    qua app_settings.
✅ Alpha 36   — Figure Bank save dialog không còn mất nút:
                  • Dialog "Lưu hình vào kho" có footer cố định, kích thước tối thiểu
                    lớn hơn và phím tắt Ctrl+Enter/Esc.
                  • Guard test chặn V4/V5 tái xuất hiện lỗi dialog lưu hình thiếu nút.
✅ Alpha 37   — User profile / License parity:
                  • Setup > License có hồ sơ người dùng giống tab Người dùng V4:
                    copy mã máy, copy thông tin hỗ trợ, nguồn license, liên hệ admin.
                  • Đếm ngược ngày hết hạn và danh sách tính năng bật/tắt theo tier,
                    gồm cả admin override.
✅ Alpha 38   — Question preview + TikZ conversion parity:
                  • Màn Tạo đề hiển thị card đầy đủ cho từng câu đã sinh, gồm
                    đáp án, lời giải, hình ảnh và nút sửa trực tiếp.
                  • Nút chuyển TikZ dùng pipeline chung; hiện đã nâng lên EMF
                    vector cho Word và vẫn giữ PNG preview trong card.
✅ Alpha 39   — Question card actions giống V4 hơn:
                  • Card kết quả có nút ↑/↓ để đổi thứ tự câu ngay trên màn Tạo đề.
                  • Nút ✕ xoá câu khỏi đề đang mở, không xoá dữ liệu đã lưu trong NHCH.
                  • Thứ tự/xoá được đồng bộ về ExamData cho export Word, trộn mã,
                    LMS push và autosave.
                  • v5/user_profile.py tách logic format license thuần để test được.
✅ Alpha 40   — LaTeX preview từng câu giống V4 hơn:
                  • Card kết quả có nút 👁 LaTeX để render riêng từng câu hỏi/công thức.
                  • Dialog V5 có Copy ảnh và Lưu PNG, dùng services.pdf_renderer thay vì UI cũ.
                  • Guard test kiểm tra Question→LaTeX, render service và wiring card.
✅ Alpha 41   — Tạo lại từng câu ngay trên card:
                  • Card kết quả có nút 🔄 Tạo lại để sinh lại đúng một câu bằng AI.
                  • Dùng _row_snapshot/MatrixRow gốc, thay câu mới vào đề hiện tại và giữ question_id cũ nếu có.
                  • Preview, export Word, trộn mã, LMS và autosave đều nhận câu mới sau khi tạo lại.
✅ Alpha 42   — Tạo lại toàn bộ câu lỗi:
                  • Màn Kết quả có nút 🔁 Tạo lại lỗi, chỉ bật khi đề có câu _error.
                  • Batch retry dùng row snapshot gốc, cập nhật tiến trình từng câu và thay lại vào đề hiện tại.
                  • Sau batch, preview/export Word/trộn mã/LMS/autosave đều đồng bộ theo câu mới.
✅ Alpha 43   — QC trực tiếp đề hiện tại:
                  • Màn Kết quả có nút ✅ QC đề hiện tại để chuyển thẳng sang tab Chất lượng.
                  • QCView nhận ExamData từ workspace V5, có nút Load đề hiện tại và reset bảng/thống kê trước khi chạy.
                  • Không cần lưu vào NHCH rồi load lại chỉ để kiểm tra chất lượng đề vừa tạo.
✅ Alpha 44   — Kiểm tra điểm và báo cáo lỗi ở Kết quả:
                  • Màn Kết quả có nút 🧮 Kiểm tra điểm, ưu tiên điểm từ row snapshot của ma trận.
                  • Nút 📋 Báo cáo lỗi xuất TXT các câu `_error`, kèm loại/mức/chủ đề/nội dung rút gọn.
                  • Guard test đảm bảo hai action này ở V5 không phụ thuộc `ui.tab_result`.
✅ Alpha 45   — Toggle nhanh kèm đáp án/lời giải:
                  • Màn Kết quả có checkbox ☑ Kèm ĐA/LG giống thanh Result V4.
                  • Toggle dùng chung `set_export_solution_enabled`, đồng bộ với dialog Cài đặt xuất.
                  • Xuất Word, auto-export và trộn mã đề đều đọc trạng thái qua `_include_solutions_on_export()`.
✅ Alpha 46   — Báo cáo QC trong V5:
                  • Tab Chất lượng có nút 📥 Báo cáo để xuất kết quả QC ra Excel/CSV.
                  • File report gồm loại, mức, điểm, PASS/REVIEW, vấn đề/gợi ý, chủ đề và nội dung rút gọn.
                  • Có test CSV thật để bảo đảm báo cáo đọc được và không phụ thuộc UI V4.
✅ Alpha 47   — Áp dụng kết quả QC vào đề hiện tại:
                  • Tab Chất lượng có nút ✅ Áp dụng giống action V4.
                  • Gắn metadata `_review` vào đúng câu trong `ExamData` theo `question_id`, fallback theo thứ tự khi cần.
                  • App shell nhận callback cập nhật đề để workspace, autosave, history và export thấy metadata QC mới.
✅ Alpha 48   — Sửa đề nhanh và dễ hơn:
                  • Màn Kết quả có thanh Sửa nhanh: nhập số câu, Đi tới, Sửa câu đang chọn.
                  • Thêm Nhân bản để sửa: tạo câu mới với `question_id` mới và xoá lỗi/QC cũ.
                  • Thêm Câu trống để soạn thủ công ngay trong đề hiện tại, không cần gọi AI lại.
✅ Alpha 49   — Theme rõ hơn và sửa lệch Hướng dẫn:
                  • Thêm `v5.ui_theme` để gom màu nền, viền, chữ phụ, cảnh báo và accent Guide.
                  • Tab Hướng dẫn chuyển layout 2 cột cố định, có tìm mục lục và khối Bắt đầu nhanh.
                  • Các dòng hướng dẫn dùng grid theo cột số/bullet + nội dung, bỏ màu gray mờ khó đọc.
✅ Alpha 50   — Giảm giật lag khung hình UI:
                  • Thêm `v5.ui_perf.UiThrottle` để gom các cập nhật progress theo nhịp 80ms thay vì bắn callback liên tục.
                  • QC batch insert dòng kết quả, tạo đề/tạo lại lỗi/upload LMS đều được throttle để giao diện còn thở khi chạy tác vụ dài.
                  • Toast và spinner dùng nhịp animation nhẹ hơn, bỏ ép `update_idletasks()` trong toast.
✅ Alpha 51   — Render đề dài mượt hơn:
                  • Card xem từng câu trong màn Tạo đề render theo lô 6 card/lần, không dựng toàn bộ đề trong một frame.
                  • Import Wizard, Tạo ma trận AI và Đề tương tự AI dùng throttle progress chung.
                  • Guard test hiệu năng UI mở rộng để giữ các workflow này không quay lại kiểu cập nhật quá dày.
✅ Alpha 52   — Cuộn chuột bớt khựng:
                  • `enable_mousewheel()` chuyển sang router toàn cục idempotent, không swap bindtags theo từng vùng scroll.
                  • MouseWheel/Treeview gom nhiều nấc bằng `after_idle`, giảm số lần repaint khi lăn nhanh.
                  • Router bỏ qua Text/Listbox/Treeview có scroll riêng và giữ Ctrl+Wheel cho zoom PDF/LaTeX.
✅ Alpha 53   — Prompt ChatBotAI nhiều mẫu:
                  • Convert > AI Text có thư viện prompt cho Gemini GEM, ChatGPT và DeepSeek, copy/xem-sửa ngay trong V5.
                  • Mẫu phủ TN, Đúng/Sai, trả lời ngắn, tự luận, TikZ, tạo theo ma trận, tạo tương tự, OCR/import và sửa format.
                  • Guard test catalog prompt và UI Copy/Xem prompt để không mất lại luồng tạo câu hỏi từ chatbot ngoài app.
✅ Alpha 54   — Convert AI Text gọn và dễ thao tác hơn:
                  • Card Prompt ChatBotAI dùng nhãn mẫu ngắn, tách hàng chọn mẫu khỏi hàng thông số để không đè ô nhập.
                  • Vùng nhập và hàng nút chuyển sang grid cố định, giữ Nhận diện cục bộ / Chuẩn hóa bằng AI luôn hiện rõ.
                  • Bỏ hàng ghi chú thừa trên form nhanh, dồn yêu cầu thêm vào ô Chủ đề/yêu cầu để giảm rối mắt.
✅ Alpha 55   — Bảng kết quả Convert không bị che chữ:
                  • Gộp `Loại` và `Mức` thành cột `Loại/Mức` để bảng bên phải còn 4 cột, dễ đọc hơn khi cửa sổ hẹp.
                  • Đặt minwidth cho cột số thứ tự/Loại-Mức và để `Chủ đề`/`Nội dung` co giãn theo khung.
                  • Guard test không cho quay lại layout 5 cột gây bóp chữ `Loại`, `Mức`.
✅ Alpha 56   — Đủ nút thao tác Convert:
                  • Hàng nút kết quả chuyển từ pack ngang sang grid 2x2 để không đẩy `Thêm vào đề` ra ngoài mép phải.
                  • Hai cột nút tự chia đều chiều rộng panel: `Copy / Xuất Word`, `Lưu NHCH / Thêm vào đề`.
                  • Guard test không cho quay lại hàng action pack ngang dễ bị che khi cửa sổ hẹp.
✅ Alpha 57   — Prompt ChatBotAI tiếng Việt có dấu:
                  • Toàn bộ catalog Gemini GEM / ChatGPT / DeepSeek và prompt dựng động được viết lại bằng tiếng Việt có dấu.
                  • Giữ nguyên token parser `===CAU===`, `LOAI`, `DAPAN`, LaTeX và TikZ để workflow import không đổi.
                  • Không thêm chế độ không dấu; guard test xác nhận prompt mặc định dễ đọc và không quay lại tiêu đề ASCII cũ.
✅ Alpha 58   — Cập nhật phần mềm thuần V5:
                  • Dialog CTk mới cho phép kiểm tra phiên bản, xem changelog, tải installer, mở trang phát hành và bỏ qua bản tùy chọn.
                  • Updater ưu tiên `MEA_UPDATE_URL_V5`, fallback `MEA_UPDATE_URL`, backend LMS theo kênh `/v1/desktop/version/v5`, rồi GitHub Releases đúng repo phát hành.
                  • Quick Switcher, Tuỳ chọn và About đều có đường mở `Kiểm tra cập nhật`; guard test chặn quay lại dialog UI V4.
✅ Alpha 59   — Snapshot an toàn trước cập nhật:
                  • Trước khi chạy installer, updater tự backup dữ liệu đầy đủ vào `backups/pre_updates`, gồm token LMS và API key đã mã hóa.
                  • Chỉ giữ 5 snapshot gần nhất, ghi task log và chặn mở installer nếu backup thất bại.
                  • Loại thư mục `updates/` khỏi backup để không đóng gói ngược installer dung lượng lớn.
✅ Alpha 60   — TikZ vector cho Word và tự lưu kho hình:
                  • Toolbar preview TikZ có nút `Overleaf`, `Lưu EMF` và `Copy EMF`.
                  • Pipeline EMF dùng `TikZ → PDF standalone → Inkscape → EMF`, chuyển chữ/công thức thành path để Word dán vector không vỡ nét.
                  • Preview và pipeline NHCH tự lưu hình render thành công vào Kho hình, chống trùng bằng hash TikZ chuẩn hoá.
✅ Alpha 61   — Đồng bộ phiên bản hiển thị V5:
                  • Tab Hướng dẫn lấy version từ `v5.__version__`, không còn hiện nhầm `config.APP_VERSION` của V4.
                  • Shell, What's New, Hướng dẫn và script installer dùng cùng nguồn version V5.
                  • Guard test kiểm header Hướng dẫn và version khớp changelog cùng `installer_v5.iss`.
✅ Alpha 23c  — Toast / NotificationCenter bị Windows taskbar che + hiện
                  trong Alt+Tab → fix triệt để:
                  • transient(parent) + attributes(-toolwindow, True) +
                    wm_title("") → KHÔNG còn entry "CTkToplevel" trong
                    Alt+Tab / taskbar.
                  • Position clamp với TASKBAR_MARGIN=60 (Windows taskbar
                    ~48px + safety) → toast LUÔN nằm trên taskbar.
                  • Two-pass reposition + re-measure actual size sau 50ms
                    (CTkToplevel auto-grow theo content, không respect
                    wm_maxsize).
                  • wm_maxsize(WIDTH, 200) + minsize cố gắng giới hạn
                    chiều rộng — clamp logic xử lý đúng dù width thực
                    grow tới 510px.
✅ Alpha 23b  — Fix mousewheel LAG + ẩn badge PDF + Treeview wheel:
                  • ROOT CAUSE LAG: enable_mousewheel() trước có
                    bind_all("<Map>", ...) → mỗi widget mount thêm 1 binding.
                    Sau vài lần navigate có HÀNG NGHÌN duplicates → mỗi wheel
                    notch trigger 1000+ callbacks → khựng nặng.
                  • FIX: idempotent (flag _v5_wheel_bound), bỏ bind_all <Map>,
                    dùng bindtags swap via <Enter>/<Leave> để route wheel
                    qua canvas. Calls nhiều lần không tạo duplicate.
                  • Step nhỏ hơn: 2 units/notch (trước 4) → cuộn mượt.
                  • Helper enable_treeview_mousewheel() áp dụng vào
                    style_treeview() → mọi Treeview tự có wheel binding.
                  • PDFViewer: bỏ "Trang N/M" overlay trong page (đã có ở
                    toolbar), debounce update_page_indicator 80ms.
✅ Alpha 23   — v5/pdf_viewer.py — OVERLEAF-STYLE PDF VIEWER:
                  • Widget CTkFrame chứa Canvas + scrollbars + toolbar.
                  • Toolbar: ◀ ▶ navigate, page indicator "1 / 3", 🔍+/-/Fit/
                    100% zoom (0.25x → 5x), status hiển thị filename + page
                    count.
                  • Multi-page: render từng PDF page qua PyMuPDF, vẽ lên
                    Canvas theo chiều dọc, có shadow + badge số trang.
                  • Interactive: MouseWheel cuộn, Ctrl+Wheel zoom, Shift+Drag
                    pan, chuột giữa pan, Home/End/PgUp/PgDn keyboard.
                  • Tích hợp vào QC TikZ tab: thay _tikz_preview_lbl bằng
                    PDFViewer, _on_tikz_rendered gọi viewer.load_pdf(path)
                    → render đầy đủ Overleaf-style.
                  • Vector quality ở mọi zoom (re-rasterize PDF qua fitz.
                    Matrix) — không pixelate như resize PNG.
✅ Alpha 22c  — TikZ preview RENDER TRỰC TIẾP TỪ PDF (vector quality):
                  • _tikz_render_image() ưu tiên render từ self._tikz_pdf_path
                    qua PyMuPDF.get_pixmap() ở DPI = 150 × zoom_factor → mỗi
                    zoom level re-rasterize từ PDF gốc, KHÔNG resize PNG.
                  • Zoom max 4.0x (trước 3.0x) — vì PDF vẫn nét ở zoom cao.
                  • Status badge: "📄 hiển thị từ PDF (vector)" hoặc
                    "🖼 PNG" (fallback) — user biết rõ mode hiện tại.
                  • Helper _render_pdf_page(pdf, dpi, page_idx) re-usable.
✅ Alpha 22b  — TikZ render giữ luôn PDF (giống v4):
                  • _render_tikz_preview dùng render_tikz_to_image(return_log=
                    True) thay vì render_single → nhận luôn img + log + PDF
                    path. PDF được copy cạnh PNG trong cache (~/.exam_generator
                    /cache/tikz_img/<hash>.pdf).
                  • _tikz_open_pdf: nếu PDF chưa có → render lại với return_log
                    thay vì báo "PDF không có" (trước phải render trước rồi mới
                    mở PDF được).
                  • Thêm "💾 Lưu PDF" button — copy PDF cache ra vị trí user
                    chọn.
✅ Alpha 22   — Fix 5 UX issues từ screenshot user:
                  ① NotificationCenter: bị cắt cạnh phải → clamp position
                     trong màn hình + nút "✕ Đóng" to đỏ (30px) + Clear 80px.
                  ② Matrix table: trống bên phải → cột "Chủ đề" và
                     "Yêu cầu cần đạt" stretch=True để fill width.
                  ③ TikZ preview thiếu v4 features → thêm toolbar: 🔍+/-/↺
                     zoom, 📋 Copy ảnh clipboard (Windows BMP), 💾 Lưu PNG,
                     📄 Mở PDF gốc trong cache.
                  ④ Splash tạo orphan tk root (cửa sổ trống thừa) → tạo
                     ModernApp trước + withdraw, splash dùng app làm parent.
                  ⑤ TikZ KB chưa group → dialog "Kho mẫu" có dropdown 6 nhóm
                     (📐 Hình phẳng / 🔷 Hình KG / 📈 Đồ thị / 📊 BBT / ➖ Khác /
                     🌐 Tất cả), hiển thị tags trong nút.
⏳ Beta 1     — User testing, i18n, cross-platform
⏳ Beta 1-2   — User testing, bug fix, cross-platform
🎯 GA          Q4 2026
```

## 📞 Liên hệ

Zalo: 033.999.8261 • Email: dominh200270@gmail.com
