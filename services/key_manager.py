"""
services/key_manager.py — Encrypted API Key storage (Spec module 17).

Bảo mật:
  - API key mã hóa bằng Fernet (AES-128-CBC + HMAC)
  - Master key sinh từ machine_id + app salt → không cần user nhập password
  - Lưu encrypted key vào ~/.exam_generator/keys.enc
  - KHÔNG bao giờ lưu plain text

Fallback: Nếu cryptography chưa cài → lưu obfuscated (base64) thay plain text.

Usage:
    from services.key_manager import KeyManager
    km = KeyManager()
    km.save("Gemini", "AIzaSy...")
    key = km.load("Gemini")   # → "AIzaSy..."
    km.delete("Gemini")
"""

from __future__ import annotations
import base64
import hashlib
import json
import os
import platform
from pathlib import Path
from typing import Optional

from config import APP_DIR

_KEY_FILE = APP_DIR / "keys.enc"
_SALT = b"exam_ai_app_v1_salt_2026"


def _get_master_key() -> bytes:
    """
    Sinh master key từ thông tin máy (không cần user nhập password).
    Đủ an toàn cho lưu trữ local — không phù hợp nếu ai đó có full disk access.
    """
    try:
        # Dùng machine-specific info
        machine_id = ""
        if platform.system() == "Windows":
            import subprocess
            _si = subprocess.STARTUPINFO()
            _si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            _si.wShowWindow = subprocess.SW_HIDE
            result = subprocess.run(
                ["wmic", "csproduct", "get", "uuid"],
                capture_output=True, text=True, timeout=3,
                startupinfo=_si,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            machine_id = result.stdout.strip().split("\n")[-1].strip()
        elif platform.system() == "Darwin":
            import subprocess
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True, text=True, timeout=3
            )
            for line in result.stdout.split("\n"):
                if "IOPlatformUUID" in line:
                    machine_id = line.split('"')[-2]
                    break
        else:
            machine_id = Path("/etc/machine-id").read_text().strip()
    except Exception:
        machine_id = platform.node() or "fallback_machine_id"

    raw = _SALT + machine_id.encode() + b"exam_ai_secret"
    key_bytes = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(key_bytes)


def _fernet():
    """Trả về Fernet instance hoặc None nếu không có cryptography."""
    try:
        from cryptography.fernet import Fernet
        return Fernet(_get_master_key())
    except ImportError:
        return None


class KeyManager:
    """Quản lý API keys an toàn."""

    def __init__(self, key_file: Path = _KEY_FILE):
        self._file = key_file
        self._file.parent.mkdir(parents=True, exist_ok=True)

    def _load_store(self) -> dict:
        """Load toàn bộ key store đã mã hóa."""
        if not self._file.exists():
            return {}
        try:
            raw = self._file.read_bytes()
            f = _fernet()
            if f:
                decrypted = f.decrypt(raw)
                return json.loads(decrypted.decode("utf-8"))
            else:
                # Fallback: base64 obfuscation
                return json.loads(base64.b64decode(raw).decode("utf-8"))
        except Exception:
            return {}

    def _save_store(self, store: dict) -> None:
        """Lưu toàn bộ key store đã mã hóa."""
        raw = json.dumps(store, ensure_ascii=False).encode("utf-8")
        f = _fernet()
        if f:
            encrypted = f.encrypt(raw)
            self._file.write_bytes(encrypted)
        else:
            # Fallback: base64 obfuscation
            self._file.write_bytes(base64.b64encode(raw))

    def save(self, provider: str, keys_raw: str) -> None:
        """Lưu API key(s) cho provider. keys_raw có thể là nhiều key phân cách bằng dấu phẩy."""
        store = self._load_store()
        store[provider] = keys_raw.strip()
        self._save_store(store)

    def load(self, provider: str) -> str:
        """Trả về raw key string (chưa split). Trả về "" nếu không tìm thấy."""
        return self._load_store().get(provider, "")

    def load_all(self) -> dict[str, str]:
        """Trả về tất cả provider → key_string."""
        return self._load_store()

    def delete(self, provider: str) -> None:
        """Xóa key của provider."""
        store = self._load_store()
        store.pop(provider, None)
        self._save_store(store)

    def has_key(self, provider: str) -> bool:
        """Kiểm tra xem đã có key chưa."""
        return bool(self.load(provider))

    def is_encrypted(self) -> bool:
        """Kiểm tra có đang dùng mã hóa thật không (vs fallback)."""
        return _fernet() is not None

    def clear_all(self) -> None:
        """Xóa toàn bộ keys."""
        if self._file.exists():
            self._file.unlink()


# ── Singleton ─────────────────────────────────────────────────────────────────
_key_manager: Optional[KeyManager] = None


def get_key_manager() -> KeyManager:
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyManager()
    return _key_manager


def get_effective_api_key(provider: str, license_info: dict) -> str:
    """Trả về API key hiệu dụng dựa trên tier và admin_api_key."""
    km = get_key_manager()
    user_key = km.load(provider)
    tier = license_info.get("tier", "basic")
    admin_key = license_info.get("admin_api_key", "")
    if tier in ("pro", "premium") and admin_key:
        return admin_key
    return user_key