"""
services/exam_history.py — Version control nội bộ cho ExamData.

Mỗi lần user lưu hoặc tạo lại đề → snapshot đề vào:
    ~/.exam_generator/exam_history/<exam_id>/v<N>__<timestamp>.json

Mỗi snapshot lưu metadata: number of questions, breakdown, source (manual/ai/regen),
diff summary so với snapshot trước.

API:
    >>> from services import exam_history
    >>> exam_history.snapshot(exam, source="ai", note="Initial generation")
    >>> versions = exam_history.list_versions(exam_id)
    >>> exam = exam_history.restore(exam_id, version_num=3)
    >>> exam_history.compare(exam_id, v1=2, v2=3)  # diff summary
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

_log = logging.getLogger(__name__)


# ── Storage layout ─────────────────────────────────────────────────────────

def _history_root() -> Path:
    from config import APP_DIR
    p = APP_DIR / "exam_history"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _exam_dir(exam_id: str) -> Path:
    """Sanitize exam_id và tạo folder."""
    safe = re.sub(r"[^\w\-]+", "_", exam_id)[:80] or "untitled"
    p = _history_root() / safe
    p.mkdir(parents=True, exist_ok=True)
    return p


def _exam_id_from_data(exam) -> str:
    """Tạo exam_id stable từ ExamData (title + subject + grade + year)."""
    title = (getattr(exam, "exam_title", "") or
             getattr(exam, "title", "") or "untitled").strip()
    subj = getattr(exam, "subject", "") or ""
    grade = getattr(exam, "grade", "") or ""
    year = getattr(exam, "year", "") or ""
    raw = f"{title}__{subj}_{grade}_{year}"
    sanitized = re.sub(r"[^\w\-]+", "_", raw)[:80]
    return sanitized or "untitled"


# ── Data structures ───────────────────────────────────────────────────────

@dataclass
class VersionInfo:
    version:    int
    timestamp:  str          # ISO datetime
    filename:   str
    source:     str          # "manual" | "ai" | "regen" | "import"
    note:       str          # short user note
    n_questions: int
    n_tn:        int
    n_ds:        int
    n_tln:       int
    n_tl:        int
    total_points: float
    content_hash: str = ""   # to detect identical content


# ── Internal helpers ──────────────────────────────────────────────────────

def _exam_to_dict(exam) -> dict:
    """Serialize ExamData. Dùng to_dict() nếu có; fallback __dict__."""
    if hasattr(exam, "to_dict") and callable(exam.to_dict):
        try:
            return exam.to_dict()
        except Exception:
            pass
    # Fallback: build manually
    return {
        "exam_title": getattr(exam, "exam_title", ""),
        "subject":    getattr(exam, "subject", ""),
        "grade":      getattr(exam, "grade", ""),
        "semester":   getattr(exam, "semester", ""),
        "year":       getattr(exam, "year", ""),
        "time":       getattr(exam, "time", ""),
        "school":     getattr(exam, "school", ""),
        "teacher":    getattr(exam, "teacher", ""),
        "questions":  [_q_to_dict(q) for q in getattr(exam, "questions", [])],
    }


def _q_to_dict(q) -> dict:
    """Serialize 1 Question."""
    if hasattr(q, "to_dict") and callable(q.to_dict):
        try:
            return q.to_dict()
        except Exception:
            pass
    # Fallback: dataclass
    try:
        from dataclasses import asdict, is_dataclass
        if is_dataclass(q):
            return asdict(q)
    except Exception:
        pass
    return {k: v for k, v in vars(q).items() if not k.startswith("_")}


def _hash_content(data: dict) -> str:
    """SHA1 of JSON dump for content identity check."""
    s = json.dumps(data.get("questions", []), ensure_ascii=False,
                   sort_keys=True, default=str)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def _summarize(data: dict) -> dict:
    """Extract question stats for VersionInfo."""
    questions = data.get("questions", [])
    n_tn = sum(1 for q in questions if q.get("qtype") == "TN")
    n_ds = sum(1 for q in questions if q.get("qtype") == "DS")
    n_tln = sum(1 for q in questions if q.get("qtype") == "TLN")
    n_tl = sum(1 for q in questions if q.get("qtype") == "TL")
    pts = sum(float(q.get("points", 0) or 0) for q in questions)
    return {
        "n_questions": len(questions),
        "n_tn": n_tn,
        "n_ds": n_ds,
        "n_tln": n_tln,
        "n_tl": n_tl,
        "total_points": round(pts, 2),
    }


# ── Public API ────────────────────────────────────────────────────────────

def snapshot(exam, source: str = "manual", note: str = "") -> Optional[VersionInfo]:
    """Lưu snapshot của ExamData. Trả VersionInfo hoặc None nếu fail.

    Tránh lưu trùng: nếu content_hash giống snapshot cuối → skip.
    """
    try:
        exam_id = _exam_id_from_data(exam)
        d = _exam_dir(exam_id)
        data = _exam_to_dict(exam)
        h = _hash_content(data)

        # Check duplicate với snapshot cuối
        existing = list_versions(exam_id)
        if existing and existing[0].content_hash == h:
            _log.info("Snapshot skipped (identical to v%d)", existing[0].version)
            return existing[0]

        next_v = (existing[0].version + 1) if existing else 1
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        ts_safe = ts.replace(":", "-")
        fname = f"v{next_v:03d}__{ts_safe}.json"
        fpath = d / fname

        summary = _summarize(data)
        info = VersionInfo(
            version=next_v,
            timestamp=ts,
            filename=fname,
            source=source,
            note=note[:120],
            content_hash=h,
            **summary,
        )

        # Lưu data + metadata
        snapshot_data = {
            "_meta":    asdict(info),
            "_data":    data,
        }
        fpath.write_text(
            json.dumps(snapshot_data, ensure_ascii=False, indent=2,
                       default=str),
            encoding="utf-8",
        )
        _log.info("Snapshot saved: %s/%s", exam_id, fname)
        return info
    except Exception as e:
        _log.warning("snapshot failed: %s", e, exc_info=True)
        return None


def list_versions(exam_id: str) -> list[VersionInfo]:
    """List versions của 1 exam (mới → cũ)."""
    d = _exam_dir(exam_id)
    versions: list[VersionInfo] = []
    for f in sorted(d.glob("v*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            meta = data.get("_meta", {})
            if meta:
                versions.append(VersionInfo(**meta))
        except Exception as e:
            _log.debug("Skip corrupted %s: %s", f, e)
    versions.sort(key=lambda v: v.version, reverse=True)
    return versions


def list_all_exams() -> list[tuple[str, int, str]]:
    """List tất cả exams có history.
    Trả: [(exam_id, n_versions, latest_timestamp), ...]"""
    out = []
    for d in _history_root().iterdir():
        if not d.is_dir():
            continue
        versions = list_versions(d.name)
        if versions:
            out.append((d.name, len(versions), versions[0].timestamp))
    out.sort(key=lambda t: t[2], reverse=True)
    return out


def list_recent_exams_with_meta(limit: int = 5) -> list[dict]:
    """[SPEED-5] Trả list các exam gần nhất KÈM metadata để hiển thị dropdown.

    Mỗi dict chứa:
        exam_id:       str         — ID dùng để restore
        version:       int         — version mới nhất
        timestamp:     str         — ISO datetime
        time_pretty:   str         — "Hôm nay 14:30" hoặc "12/05/2026 14:30"
        title:         str         — exam_title từ latest data
        subject:       str         — môn
        grade:         str         — lớp
        n_questions:   int
        n_tn / n_ds / n_tln / n_tl: int
        source:        str         — "ai" / "manual" / "regen" / "import"

    Sắp xếp: mới nhất trước. Bỏ qua exam đã rỗng (n_questions=0).
    """
    out: list[dict] = []
    for d in _history_root().iterdir():
        if not d.is_dir():
            continue
        versions = list_versions(d.name)
        if not versions:
            continue
        latest = versions[0]
        # Skip empty / corrupted
        if latest.n_questions <= 0:
            continue

        # Load latest data để lấy title, subject, grade
        data = restore(d.name, latest.version) or {}
        title   = data.get("exam_title", "")
        subject = data.get("subject", "")
        grade   = data.get("grade", "")

        out.append({
            "exam_id":      d.name,
            "version":      latest.version,
            "timestamp":    latest.timestamp,
            "time_pretty":  _format_time_pretty(latest.timestamp),
            "title":        title,
            "subject":      subject,
            "grade":        grade,
            "n_questions":  latest.n_questions,
            "n_tn":         latest.n_tn,
            "n_ds":         latest.n_ds,
            "n_tln":        latest.n_tln,
            "n_tl":         latest.n_tl,
            "source":       latest.source,
            "note":         latest.note,
        })

    out.sort(key=lambda x: x["timestamp"], reverse=True)
    return out[:limit]


def _format_time_pretty(iso_ts: str) -> str:
    """Format ISO timestamp → human-friendly Vietnamese.

    Hôm nay → "Hôm nay 14:30"
    Hôm qua → "Hôm qua 14:30"
    Trong tuần → "Thứ Tư 14:30"
    Cũ hơn → "12/05/2026 14:30"
    """
    try:
        dt = datetime.datetime.fromisoformat(iso_ts)
    except Exception:
        return iso_ts[:16]

    now = datetime.datetime.now()
    today = now.date()
    that_day = dt.date()
    delta = (today - that_day).days

    hm = dt.strftime("%H:%M")
    if delta == 0:
        return f"Hôm nay {hm}"
    if delta == 1:
        return f"Hôm qua {hm}"
    if 1 < delta <= 6:
        weekdays = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm",
                    "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
        return f"{weekdays[dt.weekday()]} {hm}"
    return dt.strftime("%d/%m/%Y %H:%M")


def load_recent_as_examdata(exam_id: str, version: Optional[int] = None):
    """[SPEED-5] Restore 1 exam → ExamData object ready-to-use.

    Nếu version=None → restore latest.
    Trả None nếu fail.
    """
    if version is None:
        data = restore_latest(exam_id)
    else:
        data = restore(exam_id, version)
    if not data:
        return None

    try:
        from core.models import ExamData
        return ExamData.from_dict(data)
    except Exception as e:
        _log.warning("load_recent_as_examdata failed: %s", e)
        return None


def restore(exam_id: str, version: int) -> Optional[dict]:
    """Trả dict data của 1 version (chưa convert thành ExamData object).
    Caller sẽ tự build ExamData từ dict."""
    d = _exam_dir(exam_id)
    for f in d.glob(f"v{version:03d}__*.json"):
        try:
            blob = json.loads(f.read_text(encoding="utf-8"))
            return blob.get("_data", {})
        except Exception as e:
            _log.warning("restore failed: %s", e)
            return None
    return None


def restore_latest(exam_id: str) -> Optional[dict]:
    """Restore version mới nhất."""
    vs = list_versions(exam_id)
    if not vs:
        return None
    return restore(exam_id, vs[0].version)


def delete_version(exam_id: str, version: int) -> bool:
    """Xoá 1 version. Trả True nếu xoá được."""
    d = _exam_dir(exam_id)
    for f in d.glob(f"v{version:03d}__*.json"):
        try:
            f.unlink()
            return True
        except Exception:
            return False
    return False


def delete_exam_history(exam_id: str) -> int:
    """Xoá toàn bộ history của 1 exam. Trả về số version đã xoá."""
    d = _exam_dir(exam_id)
    n = 0
    for f in d.glob("v*.json"):
        try:
            f.unlink()
            n += 1
        except Exception:
            pass
    try:
        d.rmdir()  # xóa folder nếu rỗng
    except Exception:
        pass
    return n


def compare(exam_id: str, v1: int, v2: int) -> dict:
    """So sánh 2 version → trả dict diff summary.

    Returns:
        {
            'v1': VersionInfo, 'v2': VersionInfo,
            'q_added':   int,    # số câu mới ở v2 không có ở v1
            'q_removed': int,    # số câu ở v1 không có ở v2
            'q_changed': int,    # số câu cùng vị trí nhưng khác nội dung
            'pts_diff':  float,  # v2.total_points - v1.total_points
        }
    """
    versions = {v.version: v for v in list_versions(exam_id)}
    info1 = versions.get(v1)
    info2 = versions.get(v2)
    if not info1 or not info2:
        return {"error": f"Version {v1} hoặc {v2} không tồn tại"}

    data1 = restore(exam_id, v1) or {}
    data2 = restore(exam_id, v2) or {}
    qs1 = data1.get("questions", [])
    qs2 = data2.get("questions", [])

    # Hash từng câu để so sánh content (key = "qtype|topic|question[:80]")
    def _q_key(q):
        return (q.get("qtype", ""), q.get("topic", ""),
                (q.get("question", "") or "")[:80])

    keys1 = {_q_key(q) for q in qs1}
    keys2 = {_q_key(q) for q in qs2}
    added = keys2 - keys1
    removed = keys1 - keys2

    # Same position different content
    n_changed = 0
    for i, (q1, q2) in enumerate(zip(qs1, qs2)):
        if _q_key(q1) != _q_key(q2):
            n_changed += 1

    return {
        "v1":        info1,
        "v2":        info2,
        "q_added":   len(added),
        "q_removed": len(removed),
        "q_changed": n_changed,
        "pts_diff":  round(info2.total_points - info1.total_points, 2),
    }


def stats() -> dict:
    """Thống kê tổng."""
    exams = list_all_exams()
    total_versions = sum(n for _, n, _ in exams)
    total_size = 0
    for d in _history_root().iterdir():
        if d.is_dir():
            for f in d.glob("v*.json"):
                try:
                    total_size += f.stat().st_size
                except Exception:
                    pass
    return {
        "n_exams":        len(exams),
        "total_versions": total_versions,
        "size_bytes":     total_size,
        "dir":            str(_history_root()),
    }
