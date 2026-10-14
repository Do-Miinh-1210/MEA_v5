"""
services/logger.py — Logging & Monitoring (Spec module 10).

Ghi log có cấu trúc:
  - prompt / response / error / retry
  - Lưu vào SQLite (cùng DB_PATH) để dashboard query được
  - Thread-safe
  - Không bao giờ crash app khi log lỗi

Usage:
    from services.logger import get_logger
    log = get_logger()
    log.prompt(model="gemini-2.5-flash", prompt_len=420, topic="Nguyên hàm")
    log.response(model="gemini-2.5-flash", ok=True, latency_ms=1200, score=0.87)
    log.error(model="gemini-2.5-flash", error="RateLimitError", attempt=2)
    log.retry(model="gemini-2.5-flash", attempt=2, reason="bad_json")
"""

from __future__ import annotations
import datetime
import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

from config import DB_PATH

# ── Python stdlib logger (also writes to file) ───────────────────────────────
_LOG_FILE = DB_PATH.parent / "app.log"
_handlers: list[logging.Handler] = [logging.StreamHandler()]
try:
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _handlers.insert(0, logging.FileHandler(str(_LOG_FILE), encoding="utf-8"))
except OSError:
    # Logging must never block app startup or EXE smoke tests. If the user's
    # profile log file is locked or not writable, keep logging to stderr.
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=_handlers,
)
_stdlib_logger = logging.getLogger("exam_ai")

# ── Schema ────────────────────────────────────────────────────────────────────
_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS ai_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event       TEXT NOT NULL,
    model       TEXT DEFAULT '',
    topic       TEXT DEFAULT '',
    qtype       TEXT DEFAULT '',
    prompt_len  INTEGER DEFAULT 0,
    response_ok INTEGER DEFAULT 1,
    latency_ms  INTEGER DEFAULT 0,
    quality_score REAL DEFAULT NULL,
    error_type  TEXT DEFAULT '',
    attempt     INTEGER DEFAULT 1,
    extra_json  TEXT DEFAULT '{}',
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_log_event ON ai_logs(event);
CREATE INDEX IF NOT EXISTS idx_log_model ON ai_logs(model);
CREATE INDEX IF NOT EXISTS idx_log_time  ON ai_logs(created_at);
"""

_lock = threading.Lock()
_initialized = False


def _ensure_schema() -> None:
    global _initialized
    if _initialized:
        return
    with _lock:
        if _initialized:
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(DB_PATH)) as con:
            con.executescript(_LOG_SCHEMA)
        _initialized = True


def _write(event: str, **kwargs) -> None:
    """Thread-safe write một log entry."""
    try:
        _ensure_schema()
        now = datetime.datetime.now().isoformat()
        extra = {k: v for k, v in kwargs.items()
                 if k not in ("model","topic","qtype","prompt_len",
                              "response_ok","latency_ms","quality_score",
                              "error_type","attempt")}
        with _lock:
            with sqlite3.connect(str(DB_PATH)) as con:
                con.execute(
                    """INSERT INTO ai_logs
                       (event,model,topic,qtype,prompt_len,response_ok,
                        latency_ms,quality_score,error_type,attempt,extra_json,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        event,
                        kwargs.get("model",""),
                        kwargs.get("topic",""),
                        kwargs.get("qtype",""),
                        int(kwargs.get("prompt_len", 0)),
                        int(bool(kwargs.get("response_ok", True))),
                        int(kwargs.get("latency_ms", 0)),
                        kwargs.get("quality_score"),
                        kwargs.get("error_type",""),
                        int(kwargs.get("attempt", 1)),
                        json.dumps(extra, ensure_ascii=False),
                        now,
                    )
                )
    except Exception:
        pass  # Never crash the app


# ── Public API ────────────────────────────────────────────────────────────────

class AppLogger:
    """Facade logger cho toàn app."""

    def prompt(self, model: str = "", prompt_len: int = 0,
               topic: str = "", qtype: str = "") -> None:
        _stdlib_logger.info(f"[PROMPT] model={model} topic={topic} len={prompt_len}")
        _write("prompt", model=model, prompt_len=prompt_len,
               topic=topic, qtype=qtype)

    def response(self, model: str = "", ok: bool = True,
                 latency_ms: int = 0, score: Optional[float] = None,
                 topic: str = "", qtype: str = "") -> None:
        status = "OK" if ok else "FAIL"
        _stdlib_logger.info(f"[RESP] {status} model={model} latency={latency_ms}ms score={score}")
        _write("response", model=model, response_ok=ok,
               latency_ms=latency_ms, quality_score=score,
               topic=topic, qtype=qtype)

    def error(self, *args, model: str = "", error: str = "",
              attempt: int = 1, topic: str = "", **kwargs) -> None:
        if args:
            msg = args[0]
            fmt_args = args[1:]
            if fmt_args:
                try:
                    err_text = str(msg) % fmt_args
                except Exception:
                    err_text = f"{msg} {fmt_args}"
            else:
                err_text = str(msg)
            if not error:
                error = err_text
        _stdlib_logger.error(f"[ERROR] model={model} attempt={attempt} err={error}" if model else error)
        _write("error", model=model, error_type=str(error)[:100],
               attempt=attempt, topic=topic, response_ok=False, **kwargs)

    def warning(self, msg: str = "", *args, **kwargs) -> None:
        if args:
            try:
                formatted = str(msg) % args
            except Exception:
                formatted = f"{msg} {args}"
        else:
            formatted = str(msg)
        _stdlib_logger.warning(formatted)
        _write("warning", error_type=formatted[:100], **kwargs)

    def warn(self, msg: str = "", *args, **kwargs) -> None:
        self.warning(msg, *args, **kwargs)

    def debug(self, msg: str = "", *args, **kwargs) -> None:
        if args:
            try:
                formatted = str(msg) % args
            except Exception:
                formatted = f"{msg} {args}"
        else:
            formatted = str(msg)
        _stdlib_logger.debug(formatted)

    def exception(self, msg: str = "", *args, **kwargs) -> None:
        _stdlib_logger.exception(msg, *args)
        _write("exception", error_type=str(msg)[:100], **kwargs)

    def retry(self, model: str = "", attempt: int = 1,
              reason: str = "", topic: str = "") -> None:
        _stdlib_logger.info(f"[RETRY] model={model} attempt={attempt} reason={reason}")
        _write("retry", model=model, attempt=attempt,
               error_type=reason, topic=topic)

    def fix(self, model: str = "", style: str = "safe",
            corrected: bool = False, topic: str = "") -> None:
        _stdlib_logger.info(f"[FIX] model={model} style={style} corrected={corrected}")
        _write("fix", model=model, topic=topic,
               extra={"style": style, "corrected": corrected})

    def info(self, msg: str, *args, **kwargs) -> None:
        if args:
            try:
                formatted = str(msg) % args
            except Exception:
                formatted = f"{msg} {args}"
        else:
            formatted = str(msg)
        _stdlib_logger.info(formatted)
        _write("info", error_type=formatted[:100], **kwargs)


# ── Singleton ─────────────────────────────────────────────────────────────────
_app_logger: Optional[AppLogger] = None


def get_logger() -> AppLogger:
    global _app_logger
    if _app_logger is None:
        _app_logger = AppLogger()
    return _app_logger


get_log = get_logger


# ── Monitoring queries (for Dashboard) ────────────────────────────────────────

def get_monitor_stats(hours: int = 24) -> dict:
    """
    Thống kê hoạt động trong N giờ gần nhất.
    Dùng cho Dashboard tab ⑥.
    """
    try:
        _ensure_schema()
        since = (datetime.datetime.now()
                 - datetime.timedelta(hours=hours)).isoformat()
        with sqlite3.connect(str(DB_PATH)) as con:
            con.row_factory = sqlite3.Row
            total_calls = con.execute(
                "SELECT COUNT(*) FROM ai_logs WHERE event='prompt' AND created_at>?",
                (since,)
            ).fetchone()[0]

            ok_calls = con.execute(
                "SELECT COUNT(*) FROM ai_logs WHERE event='response' AND response_ok=1 AND created_at>?",
                (since,)
            ).fetchone()[0]

            err_calls = con.execute(
                "SELECT COUNT(*) FROM ai_logs WHERE event='error' AND created_at>?",
                (since,)
            ).fetchone()[0]

            retry_calls = con.execute(
                "SELECT COUNT(*) FROM ai_logs WHERE event='retry' AND created_at>?",
                (since,)
            ).fetchone()[0]

            avg_latency = con.execute(
                "SELECT AVG(latency_ms) FROM ai_logs WHERE event='response' AND created_at>?",
                (since,)
            ).fetchone()[0]

            avg_score = con.execute(
                "SELECT AVG(quality_score) FROM ai_logs WHERE quality_score IS NOT NULL AND created_at>?",
                (since,)
            ).fetchone()[0]

            by_model = dict(con.execute(
                "SELECT model, COUNT(*) FROM ai_logs WHERE event='prompt' AND model!='' AND created_at>? GROUP BY model",
                (since,)
            ).fetchall())

            model_errors = dict(con.execute(
                "SELECT model, COUNT(*) FROM ai_logs WHERE event='error' AND model!='' AND created_at>? GROUP BY model",
                (since,)
            ).fetchall())

            recent_errors = [
                dict(row) for row in con.execute(
                    "SELECT model,error_type,topic,created_at FROM ai_logs "
                    "WHERE event='error' AND created_at>? ORDER BY created_at DESC LIMIT 10",
                    (since,)
                ).fetchall()
            ]

        success_rate = round(ok_calls / max(ok_calls + err_calls, 1) * 100, 1)
        error_rate   = round(err_calls / max(total_calls, 1) * 100, 1)

        return {
            "hours":         hours,
            "total_calls":   total_calls,
            "ok_calls":      ok_calls,
            "error_calls":   err_calls,
            "retry_calls":   retry_calls,
            "success_rate":  success_rate,
            "error_rate":    error_rate,
            "avg_latency_ms": round(avg_latency or 0),
            "avg_score":     round(avg_score or 0, 3),
            "by_model":      by_model,
            "model_errors":  model_errors,
            "recent_errors": recent_errors,
        }
    except Exception as e:
        return {"error": str(e), "total_calls": 0}


def get_log_tail(n: int = 50) -> list[dict]:
    """Lấy N log entries gần nhất."""
    try:
        _ensure_schema()
        with sqlite3.connect(str(DB_PATH)) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT * FROM ai_logs ORDER BY created_at DESC LIMIT ?", (n,)
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
