"""
tests/conftest.py — Shared fixtures.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure repo root is on sys.path so `from core.* import *` works
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ── Fixture paths ──────────────────────────────────────────────────────────

@pytest.fixture
def fixtures_dir() -> Path:
    """Path to tests/fixtures/ folder."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def repo_root() -> Path:
    """Path to repo root."""
    return _REPO_ROOT


# ── Real-world matrix file (user's actual file from D:\Dạy\TOÁN LỚP 12) ─────

USER_MATRIX_PATH = Path(
    r"D:\Dạy\TOÁN LỚP 12\MA TRẬN ĐỀ KIỂM TRA CUỐI KÌ II. Toán 12-2025-2026 (Lựu).docx"
)


@pytest.fixture
def user_matrix_file(request) -> Path:
    """User's real matrix file. Skips if not present (e.g. CI)."""
    if not USER_MATRIX_PATH.exists():
        pytest.skip(f"User matrix file not present: {USER_MATRIX_PATH}")
    return USER_MATRIX_PATH


# ── Isolated APP_DIR for tests that touch ~/.exam_generator ────────────────

@pytest.fixture
def isolated_app_dir(monkeypatch, tmp_path):
    """Redirect APP_DIR / FIGURES_DIR to a tmp dir so tests don't touch real data."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    # config.py uses Path.home() — patch that too
    import pathlib
    monkeypatch.setattr(pathlib.Path, "home", classmethod(lambda cls: fake_home))
    # Force config to recompute
    import importlib
    import config as _cfg
    importlib.reload(_cfg)
    return fake_home / ".exam_generator"
