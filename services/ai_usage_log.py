"""
services/ai_usage_log.py — AI usage tracking.

Mỗi request AI ghi 1 dòng JSON vào `~/.exam_generator/ai_usage.jsonl`:

    {
      "ts": "2026-04-27T16:32:01",
      "provider": "Google Gemini",
      "model": "gemini-2.5-flash",
      "kind": "generate",        # generate | generate_with_image
      "prompt_chars": 1234,
      "response_chars": 5678,
      "duration_ms": 2340,
      "ok": true,
      "error": ""                 # chỉ khi !ok
    }

API:
    >>> from services import ai_usage_log as log
    >>> log.record(provider="...", model="...", kind="generate",
    ...            prompt_chars=1234, response_chars=5678,
    ...            duration_ms=2340, ok=True)
    >>> log.stats_today()         # {"requests": 12, "errors": 1, ...}
    >>> log.stats_range(days=7)
    >>> log.recent_entries(n=20)
    >>> log.is_near_quota("Google Gemini", "gemini-2.5-flash")  # True/False
"""

from __future__ import annotations

import datetime
import json
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Optional

_log = logging.getLogger(__name__)


# ── Quota knowledge (free tier defaults — có thể chỉnh trong settings) ────

# Cấu trúc: provider → {model_pattern: {requests_per_day, requests_per_minute}}
# requests_per_minute là rough — không thực thi rate limit, chỉ dùng để cảnh báo.
_FREE_TIER_QUOTAS: dict[str, dict[str, dict]] = {
    "Google Gemini": {
        "gemini-3.5-flash":      {"rpd": 1500, "rpm": 15},
        "gemini-3.1-pro-preview": {"rpd": 50,   "rpm": 2},
        "gemini-3-flash-preview": {"rpd": 1500, "rpm": 15},
        "gemini-3.1-flash-lite": {"rpd": 1500, "rpm": 15},
        "gemini-2.5-flash":     {"rpd": 1500, "rpm": 15},
        "gemini-2.5-pro":       {"rpd": 50,   "rpm": 2},
        "_default":             {"rpd": 1500, "rpm": 15},
    },
    "Anthropic Claude": {
        # Anthropic không có free tier rộng — đặt threshold cho user paid để cảnh báo
        "_default":             {"rpd": 1000, "rpm": 50},
    },
    "DeepSeek": {
        "_default":             {"rpd": 10000, "rpm": 60},
    },
    "OpenAI": {
        "_default":             {"rpd": 10000, "rpm": 60},
    },
}

# Cảnh báo khi đã dùng X% quota
_WARN_THRESHOLD = 0.80   # 80% → warn yellow
_DANGER_THRESHOLD = 0.95  # 95% → warn red


def _log_file() -> Path:
    """Trả về đường dẫn file log JSONL. Tạo thư mục nếu cần."""
    from config import APP_DIR
    p = APP_DIR / "ai_usage.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# ══════════════════════════════════════════════════════════════════════════
# RECORD — gọi từ ai_service sau mỗi request
# ══════════════════════════════════════════════════════════════════════════

def record(
    *,
    provider: str,
    model: str,
    kind: str = "generate",
    prompt_chars: int = 0,
    response_chars: int = 0,
    duration_ms: int = 0,
    ok: bool = True,
    error: str = "",
) -> None:
    """Append 1 dòng JSON vào log file. KHÔNG raise (best-effort)."""
    entry = {
        "ts":             datetime.datetime.now().isoformat(timespec="seconds"),
        "provider":       provider,
        "model":          model,
        "kind":           kind,
        "prompt_chars":   int(prompt_chars),
        "response_chars": int(response_chars),
        "duration_ms":    int(duration_ms),
        "ok":             bool(ok),
        "error":          (error or "")[:200],
    }
    try:
        with _log_file().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        _log.debug("ai_usage_log.record failed: %s", e)


# ══════════════════════════════════════════════════════════════════════════
# READ
# ══════════════════════════════════════════════════════════════════════════

def _iter_entries() -> Iterable[dict]:
    """Yield mọi entry từ log file. Bỏ qua dòng hỏng."""
    p = _log_file()
    if not p.exists():
        return
    try:
        with p.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        _log.warning("Cannot read %s: %s", p, e)
        return


def recent_entries(n: int = 20) -> list[dict]:
    """Trả về N entries gần nhất (mới → cũ)."""
    all_entries = list(_iter_entries())
    return all_entries[-n:][::-1]


def _today_str() -> str:
    return datetime.date.today().isoformat()


def stats_today(provider: Optional[str] = None,
                model: Optional[str] = None) -> dict:
    """Thống kê hôm nay (có thể lọc theo provider/model)."""
    return _stats_for_dates({_today_str()}, provider=provider, model=model)


def stats_range(days: int = 7,
                provider: Optional[str] = None,
                model: Optional[str] = None) -> dict:
    """Thống kê N ngày gần nhất."""
    today = datetime.date.today()
    dates = {(today - datetime.timedelta(days=i)).isoformat() for i in range(days)}
    return _stats_for_dates(dates, provider=provider, model=model)


def _stats_for_dates(date_strs: set[str],
                     provider: Optional[str] = None,
                     model: Optional[str] = None) -> dict:
    """Aggregate over entries whose date in `date_strs`."""
    total = 0
    errors = 0
    total_prompt_chars = 0
    total_response_chars = 0
    total_duration_ms = 0
    by_provider: Counter[str] = Counter()
    by_model: Counter[str] = Counter()
    by_kind: Counter[str] = Counter()
    by_date: Counter[str] = Counter()

    for e in _iter_entries():
        ts = e.get("ts", "")
        date = ts[:10] if len(ts) >= 10 else ""
        if date_strs and date not in date_strs:
            continue
        if provider and e.get("provider") != provider:
            continue
        if model and e.get("model") != model:
            continue

        total += 1
        if not e.get("ok", True):
            errors += 1
        total_prompt_chars   += int(e.get("prompt_chars", 0))
        total_response_chars += int(e.get("response_chars", 0))
        total_duration_ms    += int(e.get("duration_ms", 0))
        by_provider[e.get("provider", "?")] += 1
        by_model[e.get("model", "?")] += 1
        by_kind[e.get("kind", "?")] += 1
        by_date[date] += 1

    avg_duration = total_duration_ms // total if total > 0 else 0

    return {
        "total":          total,
        "errors":         errors,
        "success_rate":   round((total - errors) / total * 100, 1) if total else 0.0,
        "prompt_chars":   total_prompt_chars,
        "response_chars": total_response_chars,
        "total_chars":    total_prompt_chars + total_response_chars,
        "avg_duration_ms": avg_duration,
        "by_provider":    dict(by_provider.most_common()),
        "by_model":       dict(by_model.most_common()),
        "by_kind":        dict(by_kind.most_common()),
        "by_date":        dict(sorted(by_date.items())),
    }


# ══════════════════════════════════════════════════════════════════════════
# QUOTA WARNINGS
# ══════════════════════════════════════════════════════════════════════════

def get_quota(provider: str, model: str) -> dict:
    """Trả về quota free tier {rpd, rpm} cho 1 model.
    Match theo prefix nếu không có exact match."""
    prov = _FREE_TIER_QUOTAS.get(provider, {})
    if model in prov:
        return prov[model]
    # Match prefix
    for k, v in prov.items():
        if k != "_default" and (model.startswith(k) or k in model):
            return v
    return prov.get("_default", {"rpd": 9999, "rpm": 999})


def quota_status(provider: str, model: str) -> dict:
    """Trả về tình trạng quota hiện tại của provider/model:
        {used_today, limit_today, percent, level}
    Level: 'ok' / 'warn' (≥80%) / 'danger' (≥95%) / 'over' (≥100%)
    """
    quota = get_quota(provider, model)
    rpd_limit = quota.get("rpd", 9999)
    used = stats_today(provider=provider, model=model)["total"]
    pct = used / rpd_limit if rpd_limit > 0 else 0
    if pct >= 1.0:
        level = "over"
    elif pct >= _DANGER_THRESHOLD:
        level = "danger"
    elif pct >= _WARN_THRESHOLD:
        level = "warn"
    else:
        level = "ok"
    return {
        "provider":    provider,
        "model":       model,
        "used_today":  used,
        "limit_today": rpd_limit,
        "percent":     round(pct * 100, 1),
        "level":       level,
    }


def is_near_quota(provider: str, model: str) -> bool:
    """True nếu đã dùng ≥80% quota hôm nay."""
    return quota_status(provider, model)["level"] in ("warn", "danger", "over")


# ══════════════════════════════════════════════════════════════════════════
# MAINTENANCE
# ══════════════════════════════════════════════════════════════════════════

def clear_log() -> bool:
    """Xoá toàn bộ log. Trả True nếu xoá được."""
    try:
        p = _log_file()
        if p.exists():
            p.unlink()
        return True
    except Exception as e:
        _log.warning("clear_log failed: %s", e)
        return False


def log_size_bytes() -> int:
    """Trả về size của log file (bytes)."""
    p = _log_file()
    return p.stat().st_size if p.exists() else 0
