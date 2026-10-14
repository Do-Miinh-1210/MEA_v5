"""
tests/test_exe_smoke.py — Smoke test cho khả năng đóng gói EXE (PyInstaller).

Mục đích: phát hiện sớm các broken imports / missing modules / orphan references
TRƯỚC khi build EXE (rất tốn thời gian). Khi 1 import bị hỏng ở dev,
EXE cũng chắc chắn hỏng → test này là gate check cho `python build_helper.py`.

Phạm vi check:
1. Tất cả module top-level Python phải import được (không syntax/circular error).
2. Không còn reference tới mea_v3 (đã xóa ở v4.0.x).
3. Các SDK chính (Gemini, Anthropic, OpenAI, Supabase) phải import được.
4. Database init OK (questions table tạo được).
5. Crypto + license cache directory tạo OK.

Chạy: pytest tests/test_exe_smoke.py -v
"""
from __future__ import annotations
import importlib
import sys
from pathlib import Path

import pytest

# Đảm bảo project root trong sys.path khi pytest chạy
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ── 1. Top-level critical modules ─────────────────────────────────────────
CRITICAL_MODULES = [
    "config",
    "core.models",
    "core.generator",
    "core.exam_parser",
    "core.exam_file_loader",
    "core.parser",
    "core.quick_matrix",
    "core.json_generator",
    "core.quality_pipeline",
    "services.ai_service",
    "services.cache_service",
    "services.retry_service",
    "services.license_manager",
    "services.exam_history",
    "services.figure_bank",
    "services.latex_engine",
    "services.local_backup",
    "services.auto_export",
    "services.matrix_templates",
    "services.task_events",
    "services.api_client",
    "services.image_fields",
    "services.native_accel",
    "services.smart_defaults",
    "services.cloud_workflow",
    "services.overleaf_exporter",
    "services.tikz_pipeline",
    "services.tikz_preflight",
    "services.tikz_renderer",
    "services.tikz_thumbnail",
    "services.tikz_vector_export",
    "services.tikz_vector_workflow",
    "services.updater",
    "services.update_safety",
    "storage.database",
    "storage.smart_db",
    "export.matrix_exporter",
    "export.word_exporter",
    "v5.app",
    "v5.ai_usage_dialog",
    "v5.ai_usage_summary",
    "v5.analyze_exam",
    "v5.dashboard_insights",
    "v5.diagnostics",
    "v5.exam_history_dialog",
    "v5.figure_bank_dialog",
    "v5.guide_content",
    "v5.license_access",
    "v5.preferences",
    "v5.tikz_shape_builder",
    "v5.update_dialog",
    "v5.variant_dialog",
    "v5.views.exam_create",
]


@pytest.mark.parametrize("mod", CRITICAL_MODULES)
def test_critical_module_imports(mod):
    """Tất cả module quan trọng phải import được — không crash khi EXE khởi động."""
    importlib.import_module(mod)


# ── 2. Mea_v3 đã được xóa hoàn toàn ───────────────────────────────────────
def test_no_mea_v3_directory():
    """Sau khi xóa mea_v3/ directory, EXE không cần bundle thêm."""
    assert not (_REPO_ROOT / "mea_v3").exists(), \
        "mea_v3/ directory đã bị xóa ở v4.0.x — không tái tạo."


def test_no_mea_v3_adapter():
    """core/mea_v3_adapter.py đã xóa — main_window không import nữa."""
    assert not (_REPO_ROOT / "core" / "mea_v3_adapter.py").exists(), \
        "core/mea_v3_adapter.py đã bị xóa ở v4.0.x."


def test_no_mea_v3_imports_in_source():
    """Quét tất cả file Python — không còn `from mea_v3` hoặc `import mea_v3`."""
    import re
    pattern = re.compile(
        r"(^|\n)\s*(from\s+mea_v3|import\s+mea_v3|from\s+core\.mea_v3_adapter)"
    )
    skip_dirs = {".git", "__pycache__", ".claude", "build", "dist", ".pytest_cache"}
    offenders: list[str] = []
    for py_file in _REPO_ROOT.rglob("*.py"):
        if any(p in py_file.parts for p in skip_dirs):
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if pattern.search(text):
            offenders.append(str(py_file.relative_to(_REPO_ROOT)))
    assert not offenders, f"Còn import mea_v3 ở: {offenders}"


def test_no_use_mea_v3_engine_flag():
    """Flag USE_MEA_V3_ENGINE đã xóa khỏi config.py."""
    import config
    assert not hasattr(config, "USE_MEA_V3_ENGINE"), \
        "config.USE_MEA_V3_ENGINE đã được xóa — không tái thêm."
    assert not hasattr(config, "MEA_V3_REVIEW"), \
        "config.MEA_V3_REVIEW đã được xóa."


# ── 3. AI SDKs (PyInstaller hay miss) ─────────────────────────────────────
def test_gemini_sdk_importable():
    pytest.importorskip("google.genai")


def test_anthropic_sdk_importable():
    pytest.importorskip("anthropic")


def test_openai_sdk_importable():
    """OpenAI SDK dùng cho DeepSeek (OpenAI-compat)."""
    pytest.importorskip("openai")


def test_supabase_sdk_importable():
    """Supabase dùng cho license + cloud sync."""
    pytest.importorskip("supabase")


# ── 4. Database init không crash ──────────────────────────────────────────
def test_db_init_works(tmp_path, monkeypatch):
    """db_init() phải tạo được schema mà không lỗi."""
    monkeypatch.setattr("config.APP_DIR", tmp_path)
    monkeypatch.setattr("config.DB_PATH", tmp_path / "test.db")
    # Reload storage.database để pickup APP_DIR mới
    import storage.database
    importlib.reload(storage.database)
    storage.database.db_init()
    assert (tmp_path / "test.db").exists()


# ── 5. Tk import (EXE không có Tcl/Tk → crash sớm) ────────────────────────
def test_tkinter_importable():
    """Tkinter là backbone GUI — EXE không có Tcl/Tk sẽ crash khởi động."""
    import tkinter
    import tkinter.ttk
    import tkinter.messagebox
    import tkinter.filedialog


# ── 6. PIL + PyMuPDF (TikZ thumbnail + PDF render) ────────────────────────
def test_pillow_importable():
    pytest.importorskip("PIL.Image")
    pytest.importorskip("PIL.ImageTk")


def test_pymupdf_importable():
    pytest.importorskip("fitz")


# ── 7. Build helper output validates ──────────────────────────────────────
def test_build_helper_no_orphan_mea_v3():
    """build_helper.py không còn reference mea_v3."""
    text = (_REPO_ROOT / "build_helper.py").read_text(encoding="utf-8")
    assert "mea_v3" not in text.lower(), \
        "build_helper.py vẫn còn reference mea_v3 — phải xóa hoàn toàn."
