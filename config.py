"""
config.py — Hằng số toàn ứng dụng (đã đồng bộ V1 + V2).
Cập nhật: loại bỏ các model preview đã bị Google thu hồi.
         Thêm DeepSeek provider. Secrets đọc từ env vars.
         Hỗ trợ PyInstaller EXE (sys.frozen).
         Chuyển đổi hoàn toàn sang Supabase.
         Đổi unlimited → premium.
"""

import os
import sys
from pathlib import Path

# ── Xác định thư mục gốc (hỗ trợ cả chạy script lẫn EXE đóng gói) ──────────
if getattr(sys, "frozen", False):
    _BASE_DIR = Path(sys.executable).parent   # thư mục chứa .exe
else:
    _BASE_DIR = Path(__file__).resolve().parent

# ── Load .env file (nếu có) ─────────────────────────────────────────────────
_env_file = _BASE_DIR / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

# ── Thư mục dữ liệu ──────────────────────────────────────────────────────────
APP_DIR     = Path.home() / ".exam_generator"
SESSION_DIR = APP_DIR / "sessions"
CACHE_DIR   = APP_DIR / "cache"
DB_PATH     = APP_DIR / "question_bank.db"

EXPORT_DIR  = APP_DIR / "exports"
IMAGES_DIR  = APP_DIR / "question_images"
# NHCH HÌNH VẼ — kho TikZ + ảnh PNG do AI vẽ / user lưu lại từ tab TikZ
FIGURES_DIR = APP_DIR / "figures"

# File lưu cài đặt app (settings chung: đường dẫn NHCH, auto-start, ...)
SETTINGS_FILE = APP_DIR / "app_settings.json"

for _d in (APP_DIR, SESSION_DIR, CACHE_DIR, EXPORT_DIR, IMAGES_DIR, FIGURES_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def get_figures_dir() -> Path:
    """Trả về thư mục lưu NHCH hình vẽ. Ưu tiên app_settings.figures_dir."""
    import json
    if SETTINGS_FILE.exists():
        try:
            s = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            custom = s.get("figures_dir", "")
            if custom and Path(custom).exists():
                return Path(custom)
        except Exception:
            pass
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    return FIGURES_DIR


def load_app_settings() -> dict:
    """Đọc app_settings.json. Trả về dict rỗng nếu chưa có."""
    import json
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_app_settings(settings: dict) -> None:
    """Ghi app_settings.json."""
    import json
    SETTINGS_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_school_info() -> tuple[str, str]:
    """Return default school/teacher info used in exam headers."""
    s = load_app_settings()
    return str(s.get("school_name", "") or ""), str(s.get("teacher_name", "") or "")


def set_school_info(school_name: str, teacher_name: str) -> None:
    """Persist default school/teacher info for future Word exports."""
    s = load_app_settings()
    s["school_name"] = str(school_name or "").strip()
    s["teacher_name"] = str(teacher_name or "").strip()
    save_app_settings(s)


def get_word_math_mode() -> str:
    """Return Word export math mode: text or equation."""
    s = load_app_settings()
    mode = str(s.get("word_math_mode", "text") or "text").strip().lower()
    return mode if mode in {"text", "equation"} else "text"


def set_word_math_mode(mode: str) -> None:
    s = load_app_settings()
    value = str(mode or "text").strip().lower()
    s["word_math_mode"] = value if value in {"text", "equation"} else "text"
    save_app_settings(s)


def is_word_auto_convert_tables_enabled() -> bool:
    """Return whether Word export should auto-convert pipe-delimited text to tables."""
    s = load_app_settings()
    return bool(s.get("word_auto_convert_tables", True))


def set_word_auto_convert_tables_enabled(enabled: bool) -> None:
    s = load_app_settings()
    s["word_auto_convert_tables"] = bool(enabled)
    save_app_settings(s)


def is_export_solution_enabled() -> bool:
    s = load_app_settings()
    return bool(s.get("export_include_solution", True))


def set_export_solution_enabled(enabled: bool) -> None:
    s = load_app_settings()
    s["export_include_solution"] = bool(enabled)
    save_app_settings(s)


def is_open_after_export_enabled() -> bool:
    s = load_app_settings()
    return bool(s.get("open_after_export", True))


def set_open_after_export_enabled(enabled: bool) -> None:
    s = load_app_settings()
    s["open_after_export"] = bool(enabled)
    save_app_settings(s)


def get_nhch_dir() -> Path:
    """Trả về thư mục lưu NHCH (ngân hàng câu hỏi).
    Ưu tiên: app_settings.nhch_dir → mặc định APP_DIR/nhch.
    """
    s = load_app_settings()
    custom = s.get("nhch_dir", "")
    if custom and Path(custom).exists():
        return Path(custom)
    default = APP_DIR / "nhch"
    default.mkdir(parents=True, exist_ok=True)
    return default


def is_first_run() -> bool:
    """Kiểm tra lần chạy đầu tiên (chưa có settings file)."""
    return not SETTINGS_FILE.exists()


# ── Auto-TikZ: AI tự sinh hình vẽ khi cần ────────────────────────────────────
# Mặc định BẬT: prompt sẽ có thêm block hướng dẫn AI tự nhận diện khi nào cần
# vẽ hình (hình học phẳng/không gian, đồ thị hàm, bảng biến thiên, biểu đồ…)
# và chèn khối \begin{tikzpicture}...\end{tikzpicture} vào câu hỏi.
AUTO_TIKZ_DEFAULT = True


def is_auto_tikz_enabled() -> bool:
    """Kiểm tra người dùng có bật 'Tự động vẽ TikZ khi cần' không."""
    s = load_app_settings()
    val = s.get("auto_tikz", AUTO_TIKZ_DEFAULT)
    return bool(val)


def set_auto_tikz_enabled(enabled: bool) -> None:
    """Cập nhật cờ auto_tikz vào app_settings.json."""
    s = load_app_settings()
    s["auto_tikz"] = bool(enabled)
    save_app_settings(s)


# ── Auto-export Word sau khi gen ─────────────────────────────────────────────
# Mặc định BẬT: sau khi AI gen xong, app tự lưu file Word vào EXPORT_DIR và
# tự mở file. User xem ngay kết quả thay vì phải vào tab "Xuất đề" → click
# "📄 Xuất Word" → chọn nơi lưu → mở file (6 click → 0 click).
# Toast notification kèm theo cho phép user [Đổi vị trí] [Lưu thêm bản]
# [Thêm vào NHCH] [Tắt auto-export].
AUTO_EXPORT_DEFAULT = True


def is_auto_export_enabled() -> bool:
    """Cờ tự xuất Word sau khi gen — mặc định BẬT."""
    s = load_app_settings()
    val = s.get("auto_export_after_gen", AUTO_EXPORT_DEFAULT)
    return bool(val)


def set_auto_export_enabled(enabled: bool) -> None:
    s = load_app_settings()
    s["auto_export_after_gen"] = bool(enabled)
    save_app_settings(s)


def get_auto_export_dir() -> "Path":
    """Thư mục mặc định cho auto-export.

    Ưu tiên app_settings.auto_export_dir → ~/Documents/MEA Exam → EXPORT_DIR
    (fallback nếu không có Documents folder).
    """
    s = load_app_settings()
    p = s.get("auto_export_dir")
    if p:
        try:
            from pathlib import Path as _Path
            pth = _Path(p)
            pth.mkdir(parents=True, exist_ok=True)
            return pth
        except Exception:
            pass

    # Default: ~/Documents/MEA Exam (cross-platform; Windows = Documents folder)
    docs = Path.home() / "Documents"
    if docs.exists():
        target = docs / "MEA Exam"
        try:
            target.mkdir(parents=True, exist_ok=True)
            return target
        except Exception:
            pass

    # Fallback: APP_DIR/exports (luôn tồn tại)
    return EXPORT_DIR


def set_auto_export_dir(path: str) -> None:
    s = load_app_settings()
    s["auto_export_dir"] = str(path)
    save_app_settings(s)


# ── Phiên bản ─────────────────────────────────────────────────────────────────
APP_NAME        = "MEA - MatrixExam AI"
APP_VERSION     = "5.0.0"
SESSION_VERSION = "5.0"

# ── Auto-update desktop ──────────────────────────────────────────────────────
# Thứ tự kiểm tra: MEA_UPDATE_URL -> MEA_API_URL/v1/desktop/version -> GitHub.
# Release cần đính kèm file installer .exe (ưu tiên tên có "setup"/"installer").
GITHUB_UPDATE_REPO = "Do-Miinh-1210/MEA_byDoMiinh"
GITHUB_UPDATE_API_URL = f"https://api.github.com/repos/{GITHUB_UPDATE_REPO}/releases/latest"
AUTO_UPDATE_ON_STARTUP = True
AUTO_UPDATE_INSTALL_AFTER_DOWNLOAD = True

# ── AI providers & models ─────────────────────────────────────────────────────
# Cập nhật 10/2026: model mới nhất từ Google, Anthropic, OpenAI, DeepSeek
# Thêm provider 9Router (OpenAI-compatible, aggregator local)
AI_PROVIDERS: dict[str, dict] = {
    "Google Gemini": {
        "models": [
            "gemini-3.8-flash",          # GA ⭐ — agent/coding/reasoning nhanh nhất
            "gemini-3.1-pro",            # GA — bài toán khó, coding phức tạp
            "gemini-3.8-live",           # Live/Streaming — real-time multimodal
            "gemini-3.6-flash",          # GA — cân bằng tốc độ & chất lượng
            "gemini-3.5-flash-lite",     # GA — rẻ, nhanh, batch/extract
            "gemini-2.5-pro",            # fallback ổn định cũ
            "gemini-2.5-flash",          # fallback nhanh cũ
        ],
        "key_hint": "AIzaSy...",
        "key_env":  "GEMINI_API_KEY",
        "install":  "pip install google-genai",
        "key_url":  "https://aistudio.google.com/apikey",
    },
    "Anthropic Claude": {
        "models": [
            "claude-sonnet-5",           # GA ⭐ — cân bằng tốt nhất
            "claude-opus-5",             # GA — mạnh nhất Anthropic
            "claude-opus-5-5",           # GA — phiên bản nâng cao Opus 5
            "claude-haiku-4-5",          # GA — nhanh & rẻ
            "claude-fable-5",            # GA — sáng tạo/viết lách
            "claude-opus-4-8",           # GA — thế hệ trước ổn định
        ],
        "key_hint": "sk-ant-...",
        "key_env":  "ANTHROPIC_API_KEY",
        "install":  "pip install anthropic",
        "key_url":  "https://console.anthropic.com/settings/keys",
    },
    "OpenAI GPT": {
        "models": [
            "gpt-6-astra",               # GA ⭐ — GPT-6 flagship đa năng
            "gpt-6.1-sol",               # GA — GPT-6 Sol (tốc độ cao)
            "gpt-6-luna",                # GA — GPT-6 Luna (cân bằng)
            "gpt-5.6-sol",               # GA — GPT-5.6 Sol nhanh
            "gpt-5.6-luna",              # GA — GPT-5.6 Luna tiết kiệm
        ],
        "key_hint": "sk-...",
        "key_env":  "OPENAI_API_KEY",
        "install":  "pip install openai",
        "key_url":  "https://platform.openai.com/api-keys",
    },
    "DeepSeek": {
        "models": [
            "deepseek-v4.1-flash",       # GA ⭐ — nhanh nhất DeepSeek 2026
            "deepseek-v4-flash",         # GA — V4 Flash ổn định
            "deepseek-r1-0528",          # Reasoning — tốt cho Toán/Logic
            "deepseek-v3.2",             # GA — V3.2 cân bằng
            "deepseek-chat",             # alias V3 — tương thích ngược
            "deepseek-reasoner",         # alias R1 — tương thích ngược
        ],
        "key_hint": "sk-...",
        "key_env":  "DEEPSEEK_API_KEY",
        "install":  "pip install openai",
        "key_url":  "https://platform.deepseek.com/api_keys",
    },
    "9Router": {
        "models": [
            "ag/gemini-3.8-flash",          # Google Gemini 3.8 qua 9Router ⭐
            "ag/gemini-3.8-flash-high",
            "ag/gemini-3.7-flash-high",
            "ag/gemini-3.6-flash-high",
            "ag/gemini-3.1-pro-low",
            "ag/claude-sonnet-4-6",         # Claude qua 9Router
            "ag/gpt-oss-120b-medium",       # GPT Open-Source qua 9Router
            "gemini-3.8-flash",             # Alias tương thích ngược
            "gemini-3.1-pro",
            "claude-sonnet-5",
            "gpt-6-astra",
            "deepseek-v4.1-flash",
        ],
        "key_hint": "sk-... (Copy từ 9Router Dashboard)",
        "key_env":  "NINEROUTER_API_KEY",
        "install":  "pip install openai",
        "key_url":  "http://localhost:20128",
        "base_url": "http://localhost:20128/v1",  # OpenAI-compatible endpoint
    },
}

MODEL_DESC: dict[str, str] = {
    # Gemini
    "gemini-3.8-flash":      "Gemini 3.8 Flash ⭐ GA — Nhanh nhất, đa năng",
    "gemini-3.1-pro":        "Gemini 3.1 Pro — Bài toán khó, lý luận sâu",
    "gemini-3.8-live":       "Gemini 3.8 Live — Tương tác thời gian thực",
    "gemini-3.6-flash":      "Gemini 3.6 Flash — Cân bằng",
    "gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite — Rẻ, nhanh",
    "gemini-2.5-pro":        "Gemini 2.5 Pro — Ổn định (Legacy)",
    "gemini-2.5-flash":      "Gemini 2.5 Flash — Nhanh (Legacy)",
    
    # Claude
    "claude-sonnet-5":       "Claude Sonnet 5 ⭐ — Cân bằng & hiệu quả",
    "claude-opus-5":         "Claude Opus 5 — Suy luận phức tạp nhất",
    "claude-opus-5-5":       "Claude Opus 5.5 — Mới nhất từ Anthropic",
    "claude-haiku-4-5":      "Claude Haiku 4.5 — Nhanh & tiết kiệm",
    "claude-fable-5":        "Claude Fable 5 — Sáng tạo, viết lách",
    "claude-opus-4-8":       "Claude Opus 4.8 — Ổn định",

    # GPT
    "gpt-6-astra":           "GPT-6 Astra ⭐ — Flagship đa năng của OpenAI",
    "gpt-6.1-sol":           "GPT-6.1 Sol — Tốc độ cao",
    "gpt-6-luna":            "GPT-6 Luna — Cân bằng",
    "gpt-5.6-sol":           "GPT-5.6 Sol — Nhanh",
    "gpt-5.6-luna":          "GPT-5.6 Luna — Tiết kiệm",
    
    # DeepSeek
    "deepseek-v4.1-flash":   "DeepSeek V4.1 Flash ⭐ — Tốc độ & chính xác",
    "deepseek-v4-flash":     "DeepSeek V4 Flash — Phiên bản ổn định",
    "deepseek-r1-0528":      "DeepSeek R1 — Chuyên Toán & Logic (Reasoning)",
    "deepseek-v3.2":         "DeepSeek V3.2 — Cân bằng chi phí",
    "deepseek-chat":         "DeepSeek V3 (Chat) — Tương thích ngược",
    "deepseek-reasoner":     "DeepSeek R1 (Reasoner) — Tương thích ngược",
}

# Temperature / max_tokens đặc biệt theo model
MODEL_TEMPERATURE: dict[str, float] = {
    "deepseek-reasoner": 0.0,  # R1 reasoning nên dùng temperature thấp
    "deepseek-r1-0528": 0.0,
}
MODEL_MAX_TOKENS: dict[str, int] = {
    "gemini-3.8-flash":    16384,
    "gemini-3.1-pro":      16384,
    "gemini-3.8-live":     16384,
    "gemini-3.6-flash":    8192,
    "gemini-2.5-pro":      16384,
    "claude-sonnet-5":     16384,
    "claude-opus-5":       16384,
    "gpt-6-astra":         16384,
    "deepseek-v4.1-flash": 16384,
    "deepseek-r1-0528":    16384,
}
DEFAULT_TEMPERATURE = 0.45
DEFAULT_MAX_TOKENS  = 8000

# ── Persist AI provider / model / source ─────────────────────────────────────
def get_selected_ai_provider() -> str:
    """Trả về AI provider được chọn gần nhất, mặc định Google Gemini."""
    s = load_app_settings()
    p = str(s.get("selected_ai_provider", "Google Gemini") or "Google Gemini")
    return p if p in AI_PROVIDERS else "Google Gemini"


def set_selected_ai_provider(provider: str) -> None:
    """Lưu AI provider được chọn vào app_settings.json."""
    if provider in AI_PROVIDERS:
        s = load_app_settings()
        s["selected_ai_provider"] = provider
        save_app_settings(s)


def get_selected_ai_model(provider: str | None = None) -> str:
    """Trả về AI model được chọn gần nhất của provider (hoặc model mặc định)."""
    s = load_app_settings()
    prov = provider or get_selected_ai_provider()
    models = AI_PROVIDERS.get(prov, {}).get("models", [])
    default_model = models[0] if models else ""
    saved = s.get(f"selected_ai_model_{prov}") or s.get("selected_ai_model") or default_model
    return saved if saved in models else default_model


def set_selected_ai_model(provider: str, model: str) -> None:
    """Lưu AI model được chọn của provider vào app_settings.json."""
    s = load_app_settings()
    s[f"selected_ai_model_{provider}"] = model
    s["selected_ai_model"] = model
    save_app_settings(s)


def get_selected_api_source() -> str:
    """Trả về nguồn API được chọn: 'admin' (Admin cấp) hoặc 'self' (Tự nhập)."""
    s = load_app_settings()
    source = str(s.get("selected_api_source", "") or "").strip().lower()
    return source if source in {"admin", "self"} else ""


def set_selected_api_source(source: str) -> None:
    """Lưu nguồn API được chọn vào app_settings.json."""
    val = str(source or "").strip().lower()
    if val in {"admin", "self"}:
        s = load_app_settings()
        s["selected_api_source"] = val
        save_app_settings(s)


# ── Domain constants ──────────────────────────────────────────────────────────
LEVEL_COLORS: dict[str, str] = {
    "NB":  "#4CAF50",
    "TH":  "#2196F3",
    "VD":  "#FF9800",
    }
LEVEL_DESC: dict[str, str] = {
    "NB":  "Nhận biết",
    "TH":  "Thông hiểu",
    "VD":  "Vận dụng",
}
TYPE_LABELS: dict[str, str] = {
    "TN":  "Trắc nghiệm nhiều phương án",
    "DS":  "Đúng / Sai",
    "TLN": "Trả lời ngắn",
    "TL":  "Tự luận",
    "NPA": "Trắc nghiệm nhiều phương án",   # alias V1
}

# ── Feature Gating (quản lý tính năng từ xa) ─────────────────────────────────
# Mỗi feature: label hiển thị + mặc định theo tier (basic/pro/premium).
# Bản mở khóa: mặc định hoạt động ở cấp Premium với toàn bộ tính năng.
FEATURE_CATALOG: dict[str, dict] = {
    "tab_matrix":    {"label": "Bảng câu hỏi",         "basic": True,  "pro": True,  "premium": True},
    "tab_result":    {"label": "Xem đề & Xuất file",   "basic": True,  "pro": True,  "premium": True},
    "tab_bank":      {"label": "Ngân hàng câu hỏi",    "basic": False, "pro": True,  "premium": True},
    "tab_qc":        {"label": "Kiểm tra chất lượng",  "basic": False, "pro": False, "premium": True},
    "tab_tikz":      {"label": "TikZ vẽ hình",         "basic": False, "pro": False, "premium": True},
    "tab_convert":   {"label": "Convert (Ảnh/PDF)",    "basic": False, "pro": True,  "premium": True},
    "quick_gen":     {"label": "Tạo đề nhanh",         "basic": False, "pro": True,  "premium": True},
    "export_word":   {"label": "Xuất Word",             "basic": True,  "pro": True,  "premium": True},
    "nhch_cloud":    {"label": "NHCH chung (Cloud)",    "basic": False, "pro": True,  "premium": True},
    "ai_review":     {"label": "AI Review & Fix",       "basic": False, "pro": False, "premium": True},
    "multi_code":    {"label": "Nhiều mã đề",          "basic": False, "pro": False, "premium": True},
    "tab_history":   {"label": "Lịch sử đề",          "basic": True,  "pro": True,  "premium": True},
    "smart_prompt":  {"label": "Smart Prompt",         "basic": False, "pro": True,  "premium": True},
}


def get_default_features(tier: str = "premium") -> dict[str, bool]:
    """Trả về dict {feature_key: enabled} mặc định cho tier. Mặc định là premium."""
    tier = tier.lower() if tier else "premium"
    if tier not in ("basic", "pro", "premium"):
        tier = "premium"
    return {k: v.get(tier, False) for k, v in FEATURE_CATALOG.items()}


# ── Generation settings ───────────────────────────────────────────────────────
NPA_BATCH_SIZE = 1
MAX_WORKERS    = 2   # Giảm để tránh 429 rate-limit
MAX_RETRY      = 3
CACHE_ENABLED  = True

# ── AI Service timing & backoff (tập trung ở đây để dễ tune production) ───
# Tất cả constant dưới đây trước đây bị hardcode rải rác trong ai_service.py,
# retry_service.py. Gộp về đây để admin / support điều chỉnh nhanh khi gặp
# rate-limit / lỗi 5xx trên môi trường thực.

# Timeout cho 1 lần call AI (giây). Quá lâu → user sốt ruột; quá ngắn →
# false-timeout trên mạng chậm. 60s là ngưỡng tốt cho Gemini Flash.
AI_CALL_TIMEOUT = 60

# Server error retry (503/500/overloaded/unavailable/internal): delay cố
# định trước khi retry. Tăng khi thường xuyên bị overload.
AI_SERVER_ERROR_RETRY_DELAY = 3        # giây

# Rate-limit (429) backoff: công thức `min(max, base ** attempt)`.
# Với base=3: 3s → 9s → 27s. Với max=30: capped ở 30s.
AI_RATE_LIMIT_BACKOFF_BASE = 3         # exponent base
AI_RATE_LIMIT_BACKOFF_MAX  = 30        # giây, cap

# Khi server gợi ý retry_delay (Gemini trả về trong error body), ta honor
# nhưng cap ở đây để tránh chờ vô tận.
AI_SERVER_SUGGESTED_RETRY_CAP = 60     # giây

# Keywords nhận diện loại lỗi — đặt ngoài để dễ mở rộng khi model mới dùng
# message khác. Lowercase match. Giữ tuple cho membership check nhanh.
AI_ERROR_KEYWORDS_INVALID_KEY = (
    "quota", "429", "403", "invalid", "key", "rate", "resource_exhausted",
)
AI_ERROR_KEYWORDS_SERVER = (
    "503", "500", "unavailable", "overloaded", "internal",
)

# ── LaTeX / TikZ render ───────────────────────────────────────────────────────
# pdflatex chạy trong worker thread — timeout bảo vệ thread khỏi bị treo nếu
# TeX package installer chạy lần đầu (MiKTeX tải gói mới). 30s = cân bằng.
# Tăng lên 60-90s nếu user báo render lần đầu trên máy mới hay bị timeout.
PDFLATEX_TIMEOUT = 30  # giây

# Engine LaTeX được dùng để compile.
#   "auto"      → tự detect theo thứ tự pdflatex > xelatex > tectonic
#   "pdflatex"  → ép pdflatex (TeX Live / MiKTeX)
#   "xelatex"   → ép xelatex (font Việt tốt hơn cho 1 số trường)
#   "tectonic"  → ép tectonic (1 file, không cần TeX distribution; lần đầu chạy
#                 phải tải gói nên có thể chậm 1-2 phút — sau đó rất nhanh)
# Nếu engine ép không tồn tại trong PATH, hệ thống fallback auto-detect + log warning.
LATEX_ENGINE_PREFERENCE = "auto"

# ── Export ────────────────────────────────────────────────────────────────────
MA_DE_LABELS = ["A", "B", "C", "D", "E", "F"]
POINTS_MAP: dict[str, float] = {
    "TN": 0.25, "NPA": 0.25, "DS": 1.0, "TLN": 0.5, "TL": 1.0,
}
TIME_MAP: dict[str, str] = {
    "10": "60 phút", "11": "60 phút", "12": "90 phút",
}

# ── QC Pipeline settings ──────────────────────────────────────────────────────
QC_PASS_THRESHOLD   = 0.90   # ≥ 0.90 → PASS
QC_REVIEW_THRESHOLD = 0.80   # 0.80–0.89 → cần Review
# Weights cho Quality Score
QC_WEIGHTS = {
    "math_correctness": 0.30,
    "double_solve":     0.25,
    "clarity":          0.20,
    "difficulty_match": 0.15,
    "format_ok":        0.10,
    "ambiguity_penalty": 0.10,
}
# Có dùng sympy không (cần cài: pip install sympy)
MATH_ENGINE_ENABLED = True
# Double-solve: gọi Solver 2 lần hay 1 lần
DOUBLE_SOLVE_ENABLED = True

# ── Phase 1: JSON Generator ───────────────────────────────────────────────────
USE_JSON_PROMPT   = True    # True = dùng JSON prompt (ổn định hơn)
JSON_MAX_RETRY    = 3       # Số lần retry khi JSON không đúng schema

# ── Phase 2: Cross-model Verification ────────────────────────────────────────
# Bật CROSS_MODEL_VERIFY để dùng 2 model xác nhận nhau
# Model chính: model được chọn trong tab Cài đặt
# Model xác minh: verifier_model được chọn trong tab Cài đặt
# Nếu 2 model không đồng ý → tự động tạo lại (tối đa CROSS_MODEL_MAX_ATTEMPTS lần)
CROSS_MODEL_VERIFY = True   # ✅ Đã bật — tăng độ chính xác đáng kể
CROSS_MODEL_MAX_ATTEMPTS = 2

# Model mặc định cho cross-model verifier
# Khuyến nghị: dùng model khác hãng với model chính để tăng hiệu quả
# Ví dụ: Chính = Gemini, Verifier = Claude (hoặc ngược lại)
DEFAULT_VERIFIER_MODEL = "claude-sonnet-5"

# ── Phase 4: Smart DB ─────────────────────────────────────────────────────────
USE_SMART_DB      = True    # True = dùng questions_v2 (có quality_score)
MIN_QUALITY_SCORE = 0.75    # Chỉ lấy câu từ NHCH nếu score >= ngưỡng này

# ── Phase 5: Adaptive Prompt ─────────────────────────────────────────────────
ADAPTIVE_PROMPT   = True    # Inject bad patterns + few-shot từ lịch sử

# ── Phase 6: Dashboard ────────────────────────────────────────────────────────
DASHBOARD_AUTO_REFRESH = True

# ── License & Database (Supabase) ─────────────────────────────────────────────
# Supabase credentials được mã hóa base64 để tránh lộ khi đóng gói EXE.
# Đổi Supabase: chạy python -c "import base64; print(base64.b64encode(b'URL_MỚI').decode())"
# rồi cập nhật _SUPABASE_URL_ENC / _SUPABASE_KEY_ENC bên dưới.
_SUPABASE_URL_ENC = "aHR0cHM6Ly9yamlsYXpseHJscXNxdm9ib2J2Yy5zdXBhYmFzZS5jbw=="
_SUPABASE_KEY_ENC = "c2JfcHVibGlzaGFibGVfNHhBNzZfVm5PNkVFNUFseWtKUEFlZ19WZ3daSUc0Sg=="

def _clean_supabase_url(url: str) -> str:
    """Chuẩn hóa URL Supabase: loại bỏ /rest/v1 và dấu gạch chéo cuối nếu có."""
    if not url:
        return ""
    u = url.strip().rstrip("/")
    if u.endswith("/rest/v1"):
        u = u[:-len("/rest/v1")].rstrip("/")
    return u

def _decode_supabase():
    """Decode Supabase credentials từ base64. Đọc env var để override (cho dev)."""
    import base64
    url = _SUPABASE_URL_ENC
    key = _SUPABASE_KEY_ENC
    try:
        url = base64.b64decode(_SUPABASE_URL_ENC.encode()).decode()
        key = base64.b64decode(_SUPABASE_KEY_ENC.encode()).decode()
    except Exception:
        pass
    # Override bằng env var (để dev / Vercel không cần sửa file)
    raw_url = os.environ.get("SUPABASE_URL", url)
    raw_key = os.environ.get("SUPABASE_KEY", key)
    return _clean_supabase_url(raw_url), (raw_key or "").strip()

SUPABASE_URL, SUPABASE_KEY = _decode_supabase()

# Vercel environment (đặt biến VERCEL=1 trên Vercel Dashboard → env vars)
IS_VERCEL = os.environ.get("VERCEL", "") == "1"

# Cache license bao nhiêu giờ (0 = luôn check online mỗi lần khởi động)
# Đặt = 0 để admin khóa/xóa có hiệu lực ngay lập tức
LICENSE_CACHE_HOURS = 0
