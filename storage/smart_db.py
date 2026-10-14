"""
storage/smart_db.py — Phase 4: Lưu trữ thông minh.

Schema nâng cấp:
  questions_v2: thêm quality_score, usage_count, is_valid, content_hash,
                feedback_score, bad_patterns, source_model
  feedback:     log chỉnh sửa của người dùng
  patterns:     good/bad patterns học từ feedback

App "học từ dữ liệu" — càng dùng càng tốt.
"""
from __future__ import annotations
import datetime, hashlib, json, sqlite3
from pathlib import Path
from typing import Optional

from config import DB_PATH
from core.models import Question


# ── Schema ────────────────────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS questions_v2 (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    subject        TEXT NOT NULL,
    grade          TEXT NOT NULL,
    topic          TEXT,
    level          TEXT,
    qtype          TEXT,
    question       TEXT,
    data_json      TEXT,
    content_hash   TEXT UNIQUE,
    quality_score  REAL DEFAULT NULL,
    usage_count    INTEGER DEFAULT 0,
    is_valid       INTEGER DEFAULT 1,
    feedback_score REAL DEFAULT NULL,
    source_model   TEXT DEFAULT '',
    created_at     TEXT,
    updated_at     TEXT,
    source         TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_v2_sg    ON questions_v2(subject, grade);
CREATE INDEX IF NOT EXISTS idx_v2_lq    ON questions_v2(level, qtype);
CREATE INDEX IF NOT EXISTS idx_v2_hash  ON questions_v2(content_hash);
CREATE INDEX IF NOT EXISTS idx_v2_score ON questions_v2(quality_score);
CREATE INDEX IF NOT EXISTS idx_v2_valid ON questions_v2(is_valid);
-- smart_search thường order_by="created_at DESC" → avoid full-table sort.
CREATE INDEX IF NOT EXISTS idx_v2_created ON questions_v2(created_at DESC);
-- get_good_examples + mặc định order_by="quality_score DESC" luôn kèm
-- is_valid=1 → composite này giúp SQLite dùng index thay vì sort riêng.
CREATE INDEX IF NOT EXISTS idx_v2_valid_score
  ON questions_v2(is_valid, quality_score DESC);

CREATE TABLE IF NOT EXISTS feedback (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER REFERENCES questions_v2(id),
    action      TEXT,  -- 'edit'|'delete'|'accept'|'reject'
    old_data    TEXT,
    new_data    TEXT,
    created_at  TEXT
);
-- feedback được filter thường xuyên theo action trong smart_stats.
CREATE INDEX IF NOT EXISTS idx_feedback_action ON feedback(action);

CREATE TABLE IF NOT EXISTS patterns (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern    TEXT UNIQUE,
    kind       TEXT,   -- 'good'|'bad'
    count      INTEGER DEFAULT 1,
    topic      TEXT DEFAULT '',
    updated_at TEXT
);
-- get_bad_patterns: WHERE kind='bad' ORDER BY count DESC
CREATE INDEX IF NOT EXISTS idx_patterns_kind_count
  ON patterns(kind, count DESC);
"""


def _get_con() -> sqlite3.Connection:
    """Lấy connection cho smart_db — dùng connection pool từ database.py."""
    from storage.database import _get_conn
    con = _get_conn()
    con.row_factory = sqlite3.Row
    return con


def smart_db_init() -> None:
    con = _get_con()
    con.executescript(_SCHEMA)
    con.row_factory = None  # Reset sau khi dùng


def content_hash(q: Question) -> str:
    text = f"{q.qtype}|{q.topic}|{q.question[:120]}"
    return hashlib.md5(text.encode()).hexdigest()


# ── Save with dedup ────────────────────────────────────────────────────────────

def smart_save(
    questions: list[Question],
    subject: str,
    grade: str,
    source: str = "",
    source_model: str = "",
) -> dict:
    """
    Lưu câu hỏi vào questions_v2.
    - Skip câu lỗi
    - Skip câu trùng (content_hash)
    - Lưu quality_score nếu đã có từ QC pipeline
    Returns: {"saved": n, "skipped_error": n, "skipped_dup": n}
    """
    smart_db_init()
    now = datetime.datetime.now().isoformat()
    saved = skipped_err = skipped_dup = 0

    with _get_con() as con:
        for q in questions:
            if q._error:
                skipped_err += 1
                continue
            chash = content_hash(q)
            # Check trùng
            exists = con.execute(
                "SELECT id FROM questions_v2 WHERE content_hash=?", (chash,)
            ).fetchone()
            if exists:
                skipped_dup += 1
                continue

            # Lấy quality_score từ _review nếu có
            qs = None
            if q._review:
                qc = q._review.get("quality_score")
                if qc:
                    qs = qc.get("final_score")

            con.execute("""
                INSERT INTO questions_v2
                (subject,grade,topic,level,qtype,question,data_json,
                 content_hash,quality_score,source_model,created_at,updated_at,source)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (subject, grade, q.topic, q.level, q.qtype,
                  q.question[:200],
                  json.dumps(q.to_dict(), ensure_ascii=False),
                  chash, qs, source_model, now, now, source))
            saved += 1
        con.commit()
    return {"saved": saved, "skipped_error": skipped_err, "skipped_dup": skipped_dup}


# ── Smart search (with quality filter) ────────────────────────────────────────

def smart_search(
    subject:       str   = "",
    grade:         str   = "",
    topic:         str   = "",
    level:         str   = "",
    qtype:         str   = "",
    keyword:       str   = "",
    min_score:     float = 0.0,
    valid_only:    bool  = True,
    order_by:      str   = "quality_score DESC",
    limit:         int   = 200,
) -> list[dict]:
    """Tìm kiếm với lọc quality_score và is_valid."""
    smart_db_init()
    where, params = [], []
    if subject:  where.append("subject=?");       params.append(subject)
    if grade:    where.append("grade=?");          params.append(grade)
    if topic:    where.append("topic LIKE ?");     params.append(f"%{topic}%")
    if level:    where.append("level=?");          params.append(level)
    if qtype:    where.append("qtype=?");          params.append(qtype)
    if keyword:  where.append("question LIKE ?");  params.append(f"%{keyword}%")
    if min_score > 0: where.append("(quality_score IS NULL OR quality_score>=?)"); params.append(min_score)
    if valid_only: where.append("is_valid=1")

    sql = "SELECT * FROM questions_v2"
    if where: sql += " WHERE " + " AND ".join(where)
    safe_order = order_by if order_by in (
        "quality_score DESC","quality_score ASC",
        "usage_count DESC","created_at DESC"
    ) else "quality_score DESC"
    sql += f" ORDER BY {safe_order} LIMIT ?"
    params.append(limit)

    with _get_con() as con:
        rows = con.execute(sql, params).fetchall()

    result = []
    for row in rows:
        try:
            q = json.loads(row["data_json"])
            q["_bank_id"]      = row["id"]
            q["_created_at"]   = row["created_at"]
            q["_source"]       = row["source"]
            q["_quality_score"]= row["quality_score"]
            q["_usage_count"]  = row["usage_count"]
            q["_is_valid"]     = row["is_valid"]
            q["_source_model"] = row["source_model"]
            result.append(q)
        except Exception:
            pass
    return result


# ── Track usage ────────────────────────────────────────────────────────────────

def increment_usage(bank_id: int) -> None:
    """Tăng usage_count mỗi khi câu được dùng vào đề."""
    with _get_con() as con:
        con.execute(
            "UPDATE questions_v2 SET usage_count=usage_count+1, updated_at=? WHERE id=?",
            (datetime.datetime.now().isoformat(), bank_id)
        )


def update_quality_score(bank_id: int, score: float) -> None:
    """Cập nhật quality_score sau khi QC pipeline chạy."""
    with _get_con() as con:
        con.execute(
            "UPDATE questions_v2 SET quality_score=?, updated_at=? WHERE id=?",
            (score, datetime.datetime.now().isoformat(), bank_id)
        )


def mark_invalid(bank_id: int, reason: str = "") -> None:
    """Đánh dấu câu không hợp lệ (không xóa, chỉ ẩn)."""
    with _get_con() as con:
        con.execute(
            "UPDATE questions_v2 SET is_valid=0, updated_at=? WHERE id=?",
            (datetime.datetime.now().isoformat(), bank_id)
        )


# ── Feedback loop (Phase 5) ────────────────────────────────────────────────────

def log_feedback(
    question_id: int,
    action: str,  # 'edit'|'delete'|'accept'|'reject'
    old_data: Optional[dict] = None,
    new_data: Optional[dict] = None,
) -> None:
    """Ghi lại hành động của người dùng. Nguồn dữ liệu cho tự học."""
    smart_db_init()
    now = datetime.datetime.now().isoformat()
    with _get_con() as con:
        con.execute(
            "INSERT INTO feedback (question_id,action,old_data,new_data,created_at) VALUES (?,?,?,?,?)",
            (question_id, action,
             json.dumps(old_data, ensure_ascii=False) if old_data else None,
             json.dumps(new_data, ensure_ascii=False) if new_data else None,
             now)
        )
        # Nếu user sửa câu → giảm nhẹ feedback_score
        if action == "edit":
            con.execute(
                "UPDATE questions_v2 SET feedback_score=COALESCE(feedback_score,1.0)-0.1 WHERE id=?",
                (question_id,)
            )
        elif action == "accept":
            con.execute(
                "UPDATE questions_v2 SET feedback_score=COALESCE(feedback_score,0.8)+0.1 WHERE id=?",
                (question_id,)
            )
        elif action in ("delete", "reject"):
            mark_invalid(question_id)


def update_patterns(pattern: str, kind: str, topic: str = "") -> None:
    """Lưu good/bad pattern từ feedback."""
    smart_db_init()
    now = datetime.datetime.now().isoformat()
    with _get_con() as con:
        existing = con.execute(
            "SELECT id,count FROM patterns WHERE pattern=?", (pattern,)
        ).fetchone()
        if existing:
            con.execute(
                "UPDATE patterns SET count=count+1, updated_at=? WHERE id=?",
                (now, existing["id"])
            )
        else:
            con.execute(
                "INSERT INTO patterns (pattern,kind,topic,updated_at) VALUES (?,?,?,?)",
                (pattern, kind, topic, now)
            )


def get_bad_patterns(topic: str = "", limit: int = 10) -> list[str]:
    """Lấy bad patterns để inject vào prompt (Phase 5)."""
    smart_db_init()
    with _get_con() as con:
        where = "kind='bad'"
        params: list = []
        if topic:
            where += " AND (topic='' OR topic LIKE ?)"
            params.append(f"%{topic}%")
        rows = con.execute(
            f"SELECT pattern FROM patterns WHERE {where} ORDER BY count DESC LIMIT ?",
            params + [limit]
        ).fetchall()
    return [r["pattern"] for r in rows]


def get_good_examples(
    qtype: str, level: str, topic: str = "", limit: int = 3
) -> list[dict]:
    """Lấy câu hỏi tốt nhất làm few-shot examples (Phase 5)."""
    return smart_search(
        qtype=qtype, level=level, topic=topic,
        min_score=0.85, valid_only=True,
        order_by="quality_score DESC",
        limit=limit,
    )


# ── Statistics ────────────────────────────────────────────────────────────────

def smart_stats() -> dict:
    """Thống kê toàn diện cho dashboard (Phase 6)."""
    smart_db_init()
    with _get_con() as con:
        total   = con.execute("SELECT COUNT(*) FROM questions_v2").fetchone()[0]
        valid   = con.execute("SELECT COUNT(*) FROM questions_v2 WHERE is_valid=1").fetchone()[0]
        avg_qs  = con.execute("SELECT AVG(quality_score) FROM questions_v2 WHERE quality_score IS NOT NULL").fetchone()[0]
        top_qs  = con.execute("SELECT COUNT(*) FROM questions_v2 WHERE quality_score>=0.9").fetchone()[0]
        n_fb    = con.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
        n_edit  = con.execute("SELECT COUNT(*) FROM feedback WHERE action='edit'").fetchone()[0]
        by_type = dict(con.execute(
            "SELECT qtype,COUNT(*) FROM questions_v2 WHERE is_valid=1 GROUP BY qtype"
        ).fetchall())
        by_lvl  = dict(con.execute(
            "SELECT level,COUNT(*) FROM questions_v2 WHERE is_valid=1 GROUP BY level"
        ).fetchall())
        by_subj = dict(con.execute(
            "SELECT subject||' '||grade,COUNT(*) FROM questions_v2 WHERE is_valid=1 GROUP BY subject,grade"
        ).fetchall())
        model_stats = dict(con.execute(
            "SELECT source_model,COUNT(*) FROM questions_v2 WHERE source_model!='' GROUP BY source_model"
        ).fetchall())
    return {
        "total": total, "valid": valid, "invalid": total - valid,
        "avg_quality_score": round(avg_qs or 0, 3),
        "top_quality_count": top_qs,
        "total_feedback": n_fb, "edits": n_edit,
        "by_type": by_type, "by_level": by_lvl,
        "by_subject": by_subj, "by_model": model_stats,
    }
