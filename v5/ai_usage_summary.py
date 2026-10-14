"""
v5/ai_usage_summary.py -- Normalise, summarise and export AI usage logs.

The shared service currently writes the V4-compatible schema
``prompt_chars``/``response_chars``/``duration_ms``. Some newer V5 surfaces
also understand ``tokens_in``/``tokens_out``/``elapsed``. This module keeps the
Tracking view and the detailed dialog on one contract so both log shapes render
correctly.
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Iterable

from v5.ai_cost import estimate_cost, format_cost


RANGE_KEYS = ("today", "7", "30", "all")
CSV_COLUMNS = (
    "ts",
    "provider",
    "model",
    "kind",
    "ok",
    "prompt_chars",
    "response_chars",
    "tokens_in",
    "tokens_out",
    "tokens_estimated",
    "cost_usd",
    "duration_ms",
    "error",
)


def usage_log_path() -> Path:
    from config import APP_DIR
    return APP_DIR / "ai_usage.jsonl"


def read_usage_entries(path: str | Path | None = None) -> list[dict]:
    """Read JSONL usage entries, skipping broken lines."""
    log_path = Path(path) if path is not None else usage_log_path()
    if not log_path.exists():
        return []
    rows: list[dict] = []
    try:
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                rows.append(data)
    except OSError:
        return []
    return rows


def _as_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def parse_usage_time(entry: dict) -> datetime | None:
    raw = str(entry.get("ts") or "")
    if not raw:
        return None
    for candidate in (raw[:19], raw.replace("Z", "+00:00")):
        try:
            dt = datetime.fromisoformat(candidate)
            return dt.replace(tzinfo=None)
        except ValueError:
            continue
    return None


def _estimate_tokens(chars: int) -> int:
    if chars <= 0:
        return 0
    return max(1, math.ceil(chars / 4))


def normalize_usage_entry(entry: dict) -> dict:
    """Return a stable row for V5 usage UI.

    If exact token counts are absent, tokens are estimated from character
    counts so the V5 cost/chart surfaces do not show an empty zero-cost view
    for the current service logger.
    """
    prompt_chars = _as_int(entry.get("prompt_chars"))
    response_chars = _as_int(entry.get("response_chars"))
    has_token_fields = "tokens_in" in entry or "tokens_out" in entry
    tokens_in = _as_int(entry.get("tokens_in"))
    tokens_out = _as_int(entry.get("tokens_out"))
    tokens_estimated = False
    if not has_token_fields:
        tokens_in = _estimate_tokens(prompt_chars)
        tokens_out = _estimate_tokens(response_chars)
        tokens_estimated = bool(tokens_in or tokens_out)

    duration_ms = _as_int(entry.get("duration_ms"))
    if not duration_ms and entry.get("elapsed") not in (None, ""):
        try:
            duration_ms = _as_int(float(entry.get("elapsed") or 0) * 1000)
        except (TypeError, ValueError):
            duration_ms = 0

    ok = bool(entry.get("ok", True))
    task = str(entry.get("task") or entry.get("kind") or "")
    model = str(entry.get("model") or "")
    cost = estimate_cost(model, tokens_in, tokens_out) if (tokens_in or tokens_out) else 0.0
    return {
        "ts": str(entry.get("ts") or ""),
        "dt": parse_usage_time(entry),
        "provider": str(entry.get("provider") or ""),
        "model": model,
        "kind": task,
        "task": task,
        "ok": ok,
        "error": str(entry.get("error") or ""),
        "prompt_chars": prompt_chars,
        "response_chars": response_chars,
        "total_chars": prompt_chars + response_chars,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "total_tokens": tokens_in + tokens_out,
        "tokens_estimated": tokens_estimated,
        "cost_usd": cost,
        "duration_ms": duration_ms,
    }


def filter_usage_entries(
    entries: Iterable[dict],
    range_key: str = "30",
    *,
    now: datetime | None = None,
) -> list[dict]:
    key = range_key if range_key in RANGE_KEYS else "30"
    if key == "all":
        return list(entries)
    now = now or datetime.now()
    today = now.date()
    if key == "today":
        start = today
    else:
        start = today - timedelta(days=max(1, int(key)) - 1)

    filtered: list[dict] = []
    for entry in entries:
        dt = parse_usage_time(entry)
        if dt is None:
            continue
        if start <= dt.date() <= today:
            filtered.append(entry)
    return filtered


def summarize_usage(entries: Iterable[dict]) -> dict:
    rows = [normalize_usage_entry(e) for e in entries]
    total = len(rows)
    errors = sum(1 for row in rows if not row["ok"])
    total_duration = sum(row["duration_ms"] for row in rows)
    by_provider: Counter[str] = Counter()
    by_model: Counter[str] = Counter()
    by_kind: Counter[str] = Counter()
    by_date: Counter[str] = Counter()
    cost_by_provider: Counter[str] = Counter()

    for row in rows:
        provider = row["provider"] or "?"
        model = row["model"] or "?"
        kind = row["kind"] or "?"
        by_provider[provider] += 1
        by_model[model] += 1
        by_kind[kind] += 1
        cost_by_provider[provider] += row["cost_usd"]
        if row["dt"] is not None:
            by_date[row["dt"].strftime("%Y-%m-%d")] += 1

    return {
        "total": total,
        "errors": errors,
        "success_rate": round((total - errors) / total * 100, 1) if total else 0.0,
        "prompt_chars": sum(row["prompt_chars"] for row in rows),
        "response_chars": sum(row["response_chars"] for row in rows),
        "total_chars": sum(row["total_chars"] for row in rows),
        "tokens_in": sum(row["tokens_in"] for row in rows),
        "tokens_out": sum(row["tokens_out"] for row in rows),
        "total_tokens": sum(row["total_tokens"] for row in rows),
        "tokens_estimated": any(row["tokens_estimated"] for row in rows),
        "avg_duration_ms": total_duration // total if total else 0,
        "cost_usd": round(sum(row["cost_usd"] for row in rows), 6),
        "by_provider": dict(by_provider.most_common()),
        "by_model": dict(by_model.most_common()),
        "by_kind": dict(by_kind.most_common()),
        "by_date": dict(sorted(by_date.items())),
        "cost_by_provider": dict(cost_by_provider),
    }


def recent_usage_rows(entries: Iterable[dict], limit: int = 50) -> list[dict]:
    rows = [normalize_usage_entry(e) for e in entries]
    rows.sort(key=lambda row: row["dt"] or datetime.min, reverse=True)
    return rows[:limit]


def quota_warnings(
    entries: Iterable[dict],
    *,
    quota_lookup: Callable[[str, str], dict] | None = None,
) -> list[dict]:
    """Return quota status for provider/model pairs used in the given rows."""
    if quota_lookup is None:
        from services.ai_usage_log import quota_status as quota_lookup

    pairs = {
        (row["provider"], row["model"])
        for row in (normalize_usage_entry(e) for e in entries)
        if row["provider"] and row["model"]
    }
    statuses: list[dict] = []
    level_rank = {"over": 0, "danger": 1, "warn": 2, "ok": 3}
    for provider, model in sorted(pairs, key=lambda item: (item[0], item[1])):
        try:
            status = quota_lookup(provider, model)
        except Exception:
            continue
        statuses.append(status)
    statuses.sort(key=lambda item: (
        level_rank.get(str(item.get("level")), 9),
        -float(item.get("percent", 0) or 0),
        str(item.get("model", "")),
    ))
    return statuses


def export_usage_csv(entries: Iterable[dict], output_path: str | Path) -> int:
    rows = [normalize_usage_entry(e) for e in entries]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in CSV_COLUMNS})
    return len(rows)


def format_number(value: int | float) -> str:
    value = int(value or 0)
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def format_duration_ms(ms: int | float) -> str:
    ms = int(ms or 0)
    if ms <= 0:
        return "-"
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms / 1000:.1f}s"


def format_cost_label(cost_usd: float, *, estimated: bool = False) -> str:
    label = format_cost(cost_usd)
    return f"{label}*" if estimated and cost_usd > 0 else label


def range_label(range_key: str) -> str:
    return {
        "today": "hôm nay",
        "7": "7 ngày gần nhất",
        "30": "30 ngày gần nhất",
        "all": "tất cả",
    }.get(range_key, "30 ngày gần nhất")
