"""
services/cache_service.py — Cache prompt → AI response.
Tránh gọi API trùng lặp trong cùng session và giữa các session.

Performance optimizations:
- LRU eviction (giữ max N entries trong RAM, xóa cũ nhất khi đầy)
- Memory limit (tự giải phóng khi vượt ngưỡng RAM)
- Thread-safe access (lock cho multi-threaded generation)
- Lazy file loading (chỉ load file khi cần, không load tất cả lúc startup)
"""

from __future__ import annotations
import hashlib
import json
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from config import CACHE_DIR, CACHE_ENABLED


class CacheService:
    """
    2-layer cache with LRU eviction:
      - L1: in-memory OrderedDict (LRU, max entries, thread-safe)
      - L2: file JSON (persistent, giữ qua các session)
    """

    def __init__(
        self,
        cache_dir: Path = CACHE_DIR,
        ttl_hours: float = 24.0,
        max_memory_entries: int = 200,
        max_memory_mb: float = 50.0,
    ):
        self._memory: OrderedDict[str, str] = OrderedDict()
        self._dir = cache_dir
        self._ttl = ttl_hours * 3600
        self._max_entries = max_memory_entries
        self._max_bytes = int(max_memory_mb * 1024 * 1024)
        self._lock = threading.Lock()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._enabled = CACHE_ENABLED
        self._memory_size = 0  # Ước tính bytes trong L1

    # ── Public API ───────────────────────────────────────────────────────────

    def get(self, prompt: str) -> Optional[str]:
        """Trả về cached response hoặc None nếu chưa có / đã hết hạn."""
        if not self._enabled:
            return None
        key = self._hash(prompt)
        with self._lock:
            # L1 — move to end (LRU: most recently used)
            if key in self._memory:
                self._memory.move_to_end(key)
                return self._memory[key]
        # L2 — load from file (outside lock to avoid blocking)
        return self._load_file(key)

    def set(self, prompt: str, response: str) -> None:
        """Lưu response vào cache."""
        if not self._enabled:
            return
        key = self._hash(prompt)
        with self._lock:
            # Evict oldest entries nếu đầy
            self._evict_if_needed(len(response.encode('utf-8', errors='ignore')))
            self._memory[key] = response
            self._memory.move_to_end(key)
            self._memory_size += len(response.encode('utf-8', errors='ignore'))
        # Save to file (outside lock)
        self._save_file(key, response)

    def clear_memory(self) -> None:
        """Xóa L1 cache (giải phóng RAM)."""
        with self._lock:
            self._memory.clear()
            self._memory_size = 0

    def clear_all(self) -> int:
        """Xóa toàn bộ cache files. Trả về số file đã xóa."""
        with self._lock:
            self._memory.clear()
            self._memory_size = 0
        count = 0
        for f in self._dir.glob("*.json"):
            try:
                f.unlink()
                count += 1
            except OSError:
                pass
        return count

    def stats(self) -> dict:
        files  = list(self._dir.glob("*.json"))
        size   = sum(f.stat().st_size for f in files)
        with self._lock:
            mem_entries = len(self._memory)
            mem_size_kb = self._memory_size / 1024
        return {
            "memory_entries": mem_entries,
            "memory_size_kb": round(mem_size_kb, 1),
            "file_entries":   len(files),
            "total_size_kb":  round(size / 1024, 1),
        }

    # ── Private ──────────────────────────────────────────────────────────────

    def _evict_if_needed(self, new_size: int = 0) -> None:
        """LRU eviction: xóa entries cũ nhất khi vượt giới hạn.
        Must be called with self._lock held.
        """
        # Evict by entry count
        while len(self._memory) >= self._max_entries:
            key, val = self._memory.popitem(last=False)  # FIFO = oldest
            self._memory_size -= len(val.encode('utf-8', errors='ignore'))

        # Evict by memory size
        while self._memory_size + new_size > self._max_bytes and self._memory:
            key, val = self._memory.popitem(last=False)
            self._memory_size -= len(val.encode('utf-8', errors='ignore'))

    @staticmethod
    def _hash(prompt: str) -> str:
        return hashlib.md5(prompt.encode("utf-8")).hexdigest()

    def _cache_path(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def _load_file(self, key: str) -> Optional[str]:
        path = self._cache_path(key)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                entry = json.load(f)
            # Kiểm tra TTL
            if time.time() - entry.get("ts", 0) > self._ttl:
                path.unlink(missing_ok=True)
                return None
            value = entry.get("v")
            if value:
                # Promote to L1 (with eviction check)
                val_size = len(value.encode('utf-8', errors='ignore'))
                with self._lock:
                    self._evict_if_needed(val_size)
                    self._memory[key] = value
                    self._memory.move_to_end(key)
                    self._memory_size += val_size
            return value
        except (json.JSONDecodeError, OSError):
            return None

    def _save_file(self, key: str, response: str) -> None:
        path = self._cache_path(key)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"ts": time.time(), "v": response}, f, ensure_ascii=False)
        except OSError:
            pass    # cache failure không nên crash app
