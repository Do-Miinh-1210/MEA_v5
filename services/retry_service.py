"""
services/retry_service.py — Retry wrapper với key rotation.
Tách biệt logic retry khỏi AI service để dễ test độc lập.
"""

from __future__ import annotations
import re
import time
from typing import Callable, Optional

from config import (
    MAX_RETRY,
    AI_RATE_LIMIT_BACKOFF_BASE,
    AI_RATE_LIMIT_BACKOFF_MAX,
)


class RetryService:
    """
    Bọc một callable AI (str → str) với:
    - Retry tối đa N lần khi parse thất bại
    - Exponential backoff khi gặp rate-limit (429)
    - Log callback để UI có thể hiển thị trạng thái
    """

    def __init__(
        self,
        max_retry: int = MAX_RETRY,
        log_cb: Optional[Callable[[str], None]] = None,
    ):
        self._max_retry = max_retry
        self._log = log_cb or (lambda msg: None)

    def call(
        self,
        ai_fn: Callable[[str], str],
        prompt: str,
        validate_fn: Optional[Callable[[str], bool]] = None,
    ) -> str:
        """
        Gọi ai_fn(prompt), retry nếu:
        - Kết quả không pass validate_fn (nếu có)
        - Exception tạm thời (rate-limit 429)

        Args:
            ai_fn:       hàm gọi AI
            prompt:      prompt đầu vào
            validate_fn: (response_text) → bool, trả False = retry

        Returns:
            response text

        Raises:
            RuntimeError: sau MAX_RETRY lần thất bại
        """
        last_err: Optional[Exception] = None
        for attempt in range(1, self._max_retry + 1):
            try:
                response = ai_fn(prompt)
                if validate_fn and not validate_fn(response):
                    self._log(f"  Retry {attempt}/{self._max_retry} — response không đúng format")
                    last_err = ValueError("Response không đúng định dạng")
                    continue
                return response
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                if "429" in msg or "rate" in msg or "resource_exhausted" in msg.lower():
                    # Gemini free tier: 429 rất thường xảy ra khi parallel requests.
                    # Backoff exponent + cap cấu hình trong config.py
                    wait = min(
                        AI_RATE_LIMIT_BACKOFF_MAX,
                        AI_RATE_LIMIT_BACKOFF_BASE ** attempt,
                    )
                    self._log(
                        f"  Rate-limit 429 — chờ {wait}s (lần {attempt})")
                    time.sleep(wait)
                elif attempt < self._max_retry:
                    self._log(f"  Retry {attempt}/{self._max_retry} — {type(e).__name__}: {e}")
                else:
                    break

        raise RuntimeError(
            f"Thất bại sau {self._max_retry} lần thử.\nLỗi cuối: {last_err}"
        )


def split_keys(raw: str) -> list[str]:
    """Tách chuỗi key (phân cách bởi dấu phẩy hoặc newline) thành list."""
    keys = [k.strip() for k in re.split(r"[,\n]+", raw) if k.strip()]
    return keys if keys else [raw.strip()]
