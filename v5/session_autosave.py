"""
v5/session_autosave.py — Tự động save current exam_data mỗi 60s.

Lưu vào ~/.exam_generator/v5_session.json. Khi khởi động app, nếu file tồn
tại + có data → hỏi user "Khôi phục phiên cũ?".

Usage trong ModernApp:
    from v5.session_autosave import start_autosave, check_restore_prompt
    check_restore_prompt(self)              # khi mở app
    start_autosave(self, get_exam_callback) # background loop
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

_log = logging.getLogger(__name__)

_FILE = Path.home() / ".exam_generator" / "v5_session.json"
_INTERVAL = 60   # seconds


def _exam_to_dict(exam) -> dict:
    """Snapshot ExamData → dict serializable."""
    if exam is None:
        return {}
    qs = []
    for q in (getattr(exam, "questions", []) or []):
        if hasattr(q, "to_dict") and callable(q.to_dict):
            qs.append(q.to_dict())
        else:
            qs.append({
                "question_id": getattr(q, "question_id", ""),
                "qtype":     q.qtype,
                "level":     q.level,
                "topic":     q.topic,
                "question":  q.question,
                "options":   q.options or {},
                "answer":    q.answer or "",
                "solution":  q.solution or "",
                "points":    float(getattr(q, "points", 1.0)),
                "items":     getattr(q, "items", {}) or {},
                "answers":   getattr(q, "answers", {}) or {},
            })
    # ExamData dùng field exam_title / time (vd "45 phút"), không phải
    # title / duration_min. Đọc cả 2 để tương thích ngược.
    title = getattr(exam, "exam_title", None) or getattr(exam, "title", "")
    time_str = getattr(exam, "time", "") or ""
    # Parse số phút từ time_str (vd "45 phút" → 45)
    import re as _re
    m = _re.search(r"\d+", str(time_str))
    duration = int(m.group(0)) if m else int(getattr(exam, "duration_min", 45))
    return {
        "saved_at":     datetime.now().isoformat(timespec="seconds"),
        "title":        title,
        "subject":      getattr(exam, "subject", "Toán"),
        "grade":        str(getattr(exam, "grade", "12")),
        "semester":     str(getattr(exam, "semester", "1")),
        "year":         str(getattr(exam, "year", "")),
        "duration_min": duration,
        "school":       str(getattr(exam, "school", "")),
        "teacher":      str(getattr(exam, "teacher", "")),
        "questions":    qs,
    }


def _dict_to_exam(d: dict):
    """Restore dict → ExamData (best-effort)."""
    try:
        from core.models import ExamData, Question
    except Exception:
        return None
    dur = int(d.get("duration_min", 45))
    exam = ExamData(exam_title=d.get("title", "Đề khôi phục"),
                     subject=d.get("subject", "Toán"),
                     grade=str(d.get("grade", "12")),
                     semester=str(d.get("semester", "1")),
                     year=str(d.get("year", "")),
                     time=f"{dur} phút",
                     school=str(d.get("school", "")),
                     teacher=str(d.get("teacher", "")),
                     questions=[])
    for qd in d.get("questions", []):
        q = Question.from_dict(qd)
        exam.questions.append(q)
    return exam


def save_now(exam) -> bool:
    """Snapshot 1 lần ngay (không qua loop)."""
    try:
        data = _exam_to_dict(exam)
        if not data.get("questions"):
            return False
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, ensure_ascii=False, indent=2)
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=str(_FILE.parent),
                prefix=f"{_FILE.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(payload)
                temp_path = Path(handle.name)
            os.replace(temp_path, _FILE)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
        return True
    except Exception as e:
        _log.warning("autosave fail: %s", e)
        return False


def load_session() -> dict | None:
    """Load v5_session.json nếu có. Trả None nếu không có hoặc lỗi."""
    if not _FILE.exists():
        return None
    try:
        data = json.loads(_FILE.read_text(encoding="utf-8"))
        return data if data.get("questions") else None
    except Exception as e:
        _log.warning("load session fail: %s", e)
        return None


def clear_session() -> None:
    try: _FILE.unlink(missing_ok=True)
    except Exception: pass


def start_autosave(app, get_exam: Callable, interval: int = _INTERVAL):
    """Spawn background thread save mỗi `interval` giây."""
    stop = threading.Event()

    def _loop():
        while not stop.is_set():
            time.sleep(interval)
            try:
                exam = get_exam()
                if exam:
                    save_now(exam)
            except Exception as e:
                _log.debug("autosave loop tick fail: %s", e)

    threading.Thread(target=_loop, daemon=True).start()
    # Lưu stop event vào app để có thể dừng khi quit
    app._autosave_stop = stop


def check_restore_prompt(app):
    """Khi mở app — nếu có session.json → hỏi user khôi phục.

    Caller cần có method `_restore_session(exam_data)` trên app (optional).
    """
    data = load_session()
    if not data:
        return
    # Gói trong messagebox sau 1s để splash kịp đóng
    def _ask():
        from tkinter import messagebox
        n = len(data.get("questions", []))
        saved = data.get("saved_at", "?")
        title = data.get("title", "")[:60]
        if messagebox.askyesno(
            "Khôi phục phiên cũ",
            f"Tìm thấy phiên đề cũ chưa lưu:\n\n"
            f"  Tiêu đề: {title}\n"
            f"  Số câu: {n}\n"
            f"  Saved at: {saved}\n\n"
            f"Khôi phục để tiếp tục?", parent=app):
            try:
                exam = _dict_to_exam(data)
                if exam and hasattr(app, "_restore_session"):
                    app._restore_session(exam)
                    from v5.toast import show_toast
                    show_toast(app, f"Đã khôi phục {n} câu từ phiên cũ",
                                kind="success")
            except Exception as e:
                messagebox.showerror("Lỗi restore", str(e), parent=app)
        else:
            clear_session()
    try:
        app.after(1500, _ask)
    except Exception: pass
