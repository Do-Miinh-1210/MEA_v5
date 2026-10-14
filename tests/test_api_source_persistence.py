"""
tests/test_api_source_persistence.py — Kiểm tra cơ chế lưu nguồn API, Provider, Model và Key.
"""

import tempfile
from pathlib import Path
import pytest

from config import (
    AI_PROVIDERS,
    load_app_settings,
    save_app_settings,
    get_selected_ai_provider,
    set_selected_ai_provider,
    get_selected_ai_model,
    set_selected_ai_model,
    get_selected_api_source,
    set_selected_api_source,
)
from services.key_manager import KeyManager
from services.retry_service import split_keys


@pytest.fixture(autouse=True)
def isolated_app_settings(monkeypatch, tmp_path):
    """Cô lập SETTINGS_FILE trong môi trường test tạm thời."""
    fake_settings_file = tmp_path / "app_settings.json"
    import config
    monkeypatch.setattr(config, "SETTINGS_FILE", fake_settings_file)
    return fake_settings_file


def test_selected_ai_provider_persistence():
    # Ban đầu chưa có cài đặt -> mặc định là Google Gemini
    assert get_selected_ai_provider() == "Google Gemini"

    # Lưu sang DeepSeek
    set_selected_ai_provider("DeepSeek")
    assert get_selected_ai_provider() == "DeepSeek"

    # Lưu sang Anthropic Claude
    set_selected_ai_provider("Anthropic Claude")
    assert get_selected_ai_provider() == "Anthropic Claude"

    # Thử đặt provider không hợp lệ -> không ghi đè giá trị hợp lệ hiện có
    set_selected_ai_provider("NonExistentProvider")
    assert get_selected_ai_provider() == "Anthropic Claude"


def test_selected_ai_model_persistence():
    # Model mặc định của Google Gemini
    gemini_models = AI_PROVIDERS["Google Gemini"]["models"]
    assert get_selected_ai_model("Google Gemini") == gemini_models[0]

    # Đổi sang model thứ 2 của Google Gemini
    if len(gemini_models) > 1:
        target_model = gemini_models[1]
        set_selected_ai_model("Google Gemini", target_model)
        assert get_selected_ai_model("Google Gemini") == target_model

    # Đổi sang DeepSeek và đặt model riêng cho DeepSeek
    deepseek_models = AI_PROVIDERS["DeepSeek"]["models"]
    set_selected_ai_provider("DeepSeek")
    assert get_selected_ai_model("DeepSeek") == deepseek_models[0]
    set_selected_ai_model("DeepSeek", deepseek_models[-1])
    assert get_selected_ai_model("DeepSeek") == deepseek_models[-1]

    # Kiểm tra model của Google Gemini vẫn được bảo toàn riêng biệt
    if len(gemini_models) > 1:
        assert get_selected_ai_model("Google Gemini") == gemini_models[1]


def test_selected_api_source_persistence():
    # Ban đầu
    assert get_selected_api_source() in ("", "admin", "self")

    # Chọn nguồn "admin" (Admin cấp)
    set_selected_api_source("admin")
    assert get_selected_api_source() == "admin"

    # Chọn nguồn "self" (Tự nhập)
    set_selected_api_source("self")
    assert get_selected_api_source() == "self"

    # Thử đặt giá trị không hợp lệ
    set_selected_api_source("hack_source")
    assert get_selected_api_source() == "self"


def test_key_manager_encryption_and_rotation(tmp_path):
    key_file = tmp_path / "test_keys.enc"
    km = KeyManager(key_file=key_file)

    # Chưa có key
    assert km.load("Google Gemini") == ""
    assert not km.has_key("Google Gemini")

    # Lưu 1 key
    single_key = "AIzaSyTestKey1234567890"
    km.save("Google Gemini", single_key)
    assert km.load("Google Gemini") == single_key
    assert km.has_key("Google Gemini")

    # Lưu đa key phân cách bằng dấu phẩy
    multi_keys = "AIzaSyKeyA11111111111, AIzaSyKeyB22222222222, AIzaSyKeyC33333333333"
    km.save("Google Gemini", multi_keys)
    loaded = km.load("Google Gemini")
    assert loaded == multi_keys

    # Kiểm tra hàm split_keys xoay vòng chuẩn xác
    parsed = split_keys(loaded)
    assert len(parsed) == 3
    assert parsed[0] == "AIzaSyKeyA11111111111"
    assert parsed[1] == "AIzaSyKeyB22222222222"
    assert parsed[2] == "AIzaSyKeyC33333333333"

    # Kiểm tra file đã được mã hóa, không lưu plain text thô
    raw_content = key_file.read_bytes()
    assert b"AIzaSyKeyA11111111111" not in raw_content

    # Xóa key
    km.delete("Google Gemini")
    assert km.load("Google Gemini") == ""
    assert not km.has_key("Google Gemini")
