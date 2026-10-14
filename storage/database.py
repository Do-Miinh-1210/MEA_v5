"""
storage/database.py — SQLite question bank và session management.
Hai responsibility nhưng cùng layer storage nên để chung.

Performance optimizations:
- Thread-local connection pooling (tránh tạo/đóng connection mỗi lần query)
- WAL mode (Write-Ahead Logging) — concurrent read/write nhanh hơn
- PRAGMA tuning (cache_size, synchronous, temp_store)
- Batch inserts thay vì từng dòng
"""

from __future__ import annotations
import datetime
import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Optional

from config import DB_PATH, SESSION_DIR, SESSION_VERSION
from core.models import Question, ExamData, MatrixData, MatrixRow

_log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  CONNECTION POOL — thread-local, tái sử dụng connections
# ══════════════════════════════════════════════════════════════════════════════

_local = threading.local()
_init_done = False
_init_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    """Lấy connection cho thread hiện tại (tạo mới + optimize nếu chưa có)."""
    if not hasattr(_local, 'conn') or _local.conn is None:
        conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        # ── PRAGMA optimizations ──
        conn.execute("PRAGMA journal_mode=WAL")       # Write-Ahead Logging — nhanh 2-5x
        conn.execute("PRAGMA synchronous=NORMAL")      # Cân bằng speed/safety
        conn.execute("PRAGMA cache_size=-8000")         # 8MB cache (thay vì default 2MB)
        conn.execute("PRAGMA temp_store=MEMORY")        # Temp tables trong RAM
        conn.execute("PRAGMA mmap_size=67108864")       # 64MB memory-mapped I/O
        _local.conn = conn
    return _local.conn


def close_db() -> None:
    """Đóng connection của thread hiện tại (gọi khi tắt app)."""
    if hasattr(_local, 'conn') and _local.conn:
        try:
            _local.conn.close()
        except Exception:
            pass
        _local.conn = None


# ══════════════════════════════════════════════════════════════════════════════
#  QUESTION BANK
# ══════════════════════════════════════════════════════════════════════════════

def db_init() -> None:
    """Tạo schema nếu chưa có. Thread-safe, chỉ chạy 1 lần."""
    global _init_done
    if _init_done:
        return
    with _init_lock:
        if _init_done:
            return
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        con = _get_conn()
        con.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                subject     TEXT,
                grade       TEXT,
                topic       TEXT,
                level       TEXT,
                qtype       TEXT,
                question    TEXT,
                data_json   TEXT,
                created_at  TEXT,
                source      TEXT
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_sg ON questions(subject, grade)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_lq ON questions(level, qtype)")
        # search_questions ORDER BY created_at DESC — nếu không có idx,
        # SQLite phải full-scan + sort in-memory khi bank > vài nghìn câu.
        con.execute("CREATE INDEX IF NOT EXISTS idx_q_created ON questions(created_at DESC)")
        # Composite cho filter thường dùng subject+grade+level trong UI bank.
        con.execute("CREATE INDEX IF NOT EXISTS idx_q_sgl ON questions(subject, grade, level)")
        # Migration: thêm cột question_id nếu DB cũ chưa có
        try:
            con.execute("ALTER TABLE questions ADD COLUMN question_id TEXT")
            con.commit()
        except Exception as e:
            _log.debug("question_id column already exists: %s", e)
        # Index cho question_id (tạo sau migration)
        try:
            con.execute("CREATE INDEX IF NOT EXISTS idx_qid ON questions(question_id)")
        except Exception as e:
            _log.debug("idx_qid create skipped: %s", e)
        # Thêm bảng exam_history để giới hạn đề cho gói Basic
        con.execute("""
            CREATE TABLE IF NOT EXISTS exam_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT,
                created_at TEXT
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_exam_history_machine ON exam_history(machine_id)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_exam_history_date ON exam_history(created_at)")
        # get_today_exam_count dùng WHERE machine_id=? AND DATE(created_at)=?
        # → composite index giúp range-scan hiệu quả hơn 2 index đơn lẻ.
        con.execute(
            "CREATE INDEX IF NOT EXISTS idx_exam_hist_comp "
            "ON exam_history(machine_id, created_at)"
        )
        con.commit()
        _init_done = True


def save_questions(
    questions: list[Question],
    subject: str,
    grade: str,
    source: str = "",
) -> int:
    """
    Lưu danh sách câu hỏi vào ngân hàng.
    Bỏ qua câu lỗi. Dùng batch insert — nhanh hơn 5-10x.
    Trả về số câu đã lưu.
    """
    db_init()
    now = datetime.datetime.now().isoformat()
    # Batch insert — chuẩn bị tất cả rows trước, executemany 1 lần
    rows_to_insert = []
    for q in questions:
        if q._error:
            continue
        qid = getattr(q, "question_id", None) or ""
        rows_to_insert.append((
            qid, subject, grade, q.topic, q.level, q.qtype,
            q.question[:200],
            json.dumps(q.to_dict(), ensure_ascii=False),
            now, source,
        ))
    if not rows_to_insert:
        return 0
    con = _get_conn()
    con.executemany(
        """INSERT INTO questions
           (question_id, subject, grade, topic, level, qtype, question, data_json, created_at, source)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        rows_to_insert,
    )
    con.commit()
    return len(rows_to_insert)


def search_questions(
    subject:  str = "",
    grade:    str = "",
    topic:    str = "",
    level:    str = "",
    qtype:    str = "",
    keyword:  str = "",
    limit:    int = 5000,
) -> list[dict]:
    """
    Tìm kiếm câu hỏi trong ngân hàng.
    Trả về list dict (mỗi dict là 1 câu hỏi với thêm _bank_id, _created_at, _source).
    Dùng connection pool — nhanh hơn 3-5x so với tạo mới mỗi lần.
    """
    db_init()
    where:  list[str] = []
    params: list      = []
    if subject: where.append("subject=?");        params.append(subject)
    if grade:   where.append("grade=?");          params.append(grade)
    if topic:   where.append("topic LIKE ?");     params.append(f"%{topic}%")
    if level:   where.append("level=?");          params.append(level)
    if qtype:   where.append("qtype=?");          params.append(qtype)
    if keyword: where.append("question LIKE ?");  params.append(f"%{keyword}%")

    sql = "SELECT * FROM questions"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY created_at DESC LIMIT {limit}"

    con = _get_conn()
    con.row_factory = sqlite3.Row
    rows = con.execute(sql, params).fetchall()
    con.row_factory = None  # Reset

    result = []
    for row in rows:
        try:
            q = json.loads(row["data_json"])
            q["_bank_id"]    = row["id"]
            q["question_id"] = row["question_id"] or q.get("question_id", "")
            q["_created_at"] = row["created_at"]
            q["_source"]     = row["source"]
            q["subject"]     = row["subject"] or q.get("subject", "")
            q["grade"]       = row["grade"] or q.get("grade", "")
            result.append(q)
        except (json.JSONDecodeError, KeyError):
            pass
    return result


def delete_question(bank_id: int) -> None:
    """Xóa 1 câu hỏi khỏi ngân hàng theo ID."""
    con = _get_conn()
    con.execute("DELETE FROM questions WHERE id=?", (bank_id,))
    con.commit()


def db_stats() -> dict:
    """Thống kê ngân hàng câu hỏi."""
    db_init()
    con = _get_conn()
    total      = con.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    by_subject = dict(con.execute(
        "SELECT subject||' '||grade, COUNT(*) FROM questions GROUP BY subject, grade"
    ).fetchall())
    by_type  = dict(con.execute(
        "SELECT qtype, COUNT(*) FROM questions GROUP BY qtype"
    ).fetchall())
    by_level = dict(con.execute(
        "SELECT level, COUNT(*) FROM questions GROUP BY level"
    ).fetchall())
    return {
        "total":      total,
        "by_subject": by_subject,
        "by_type":    by_type,
        "by_level":   by_level,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

# ── Session migration registry ────────────────────────────────────────────────
# Ghi rõ các version trong quá khứ để UI + load_session biết phải migrate gì.
# Thêm version mới: bump SESSION_VERSION trong config.py + thêm entry vào
# _SESSION_MIGRATIONS (key = version nguồn, value = (version đích, func)).

# Các phiên bản chính thức đã tồn tại — không bao giờ xóa khỏi list
SESSION_KNOWN_VERSIONS: tuple[str, ...] = ("1.0", "3.0", "4.0")


def _migrate_1_0_to_3_0(data: dict) -> dict:
    """Migrate session v1.0 → v3.0.

    Thay đổi chính từ v1.0 (MEA v1) sang v3.0:
      • Thêm field "ma_de" cho ExamData (mã đề) — default "".
      • question_id không tồn tại ở v1.0 — Question.from_dict sẽ auto-gen
        qua default_factory, không cần làm gì ở đây.
    """
    ex = data.get("exam_data")
    if isinstance(ex, dict):
        ex.setdefault("ma_de", "")
        # Trong v1.0, stats được lưu dưới dạng dict → bỏ (nay là @property)
        ex.pop("stats", None)
    data["version"] = "3.0"
    return data


def _migrate_3_0_to_4_0(data: dict) -> dict:
    """Migrate session v3.0 → v4.0.

    Thay đổi chính từ v3.0 (MEA v3) sang v4.0:
      • Question có thêm slot ảnh: question_image / option_images /
        solution_image / item_images — default "" hoặc {}.
      • Thêm tikz_code — default "".
      • _review là dict hoặc None — không đổi.
    Question.from_dict đã filter-by-known-field nên missing key không crash,
    nhưng ta vẫn setdefault để value có mặt trong dict (cho UI biết về ảnh).
    """
    ex = data.get("exam_data")
    if isinstance(ex, dict):
        for q in ex.get("questions", []) or []:
            if not isinstance(q, dict):
                continue
            q.setdefault("question_image", "")
            q.setdefault("option_images", {})
            q.setdefault("solution_image", "")
            q.setdefault("item_images", {})
            q.setdefault("tikz_code", "")
            q.setdefault("item_solutions", {})
    data["version"] = "4.0"
    return data


# Mapping: from_version → (to_version, migrator_fn)
_SESSION_MIGRATIONS: dict[str, tuple[str, callable]] = {  # type: ignore[type-arg]
    "1.0": ("3.0", _migrate_1_0_to_3_0),
    "3.0": ("4.0", _migrate_3_0_to_4_0),
}


def _migrate_session_data(data: dict) -> tuple[dict, list[str]]:
    """Áp dụng chuỗi migration cho đến khi đạt SESSION_VERSION hiện tại.

    Returns
    -------
    (migrated_data, warnings)
        warnings là list các chuỗi mô tả migration đã chạy (để UI hiển thị).

    Raises
    ------
    ValueError  — nếu version mới hơn SESSION_VERSION (file từ version tương
                  lai, không biết cách downgrade).
    """
    warnings: list[str] = []
    ver = str(data.get("version", "1.0"))

    if ver == SESSION_VERSION:
        return data, warnings

    # File từ tương lai → từ chối
    if ver not in SESSION_KNOWN_VERSIONS:
        raise ValueError(
            f"Phiên làm việc có version='{ver}' — app hiện tại là v{SESSION_VERSION}. "
            "Có thể file được tạo bởi phiên bản mới hơn. "
            "Vui lòng nâng cấp MatrixExamAI."
        )

    cur = ver
    # Chạy tuần tự các bước migration
    while cur != SESSION_VERSION and cur in _SESSION_MIGRATIONS:
        next_ver, fn = _SESSION_MIGRATIONS[cur]
        try:
            data = fn(data)
        except Exception as e:
            _log.exception("Migration %s → %s thất bại: %s", cur, next_ver, e)
            raise ValueError(
                f"Không migrate được phiên từ v{cur} sang v{next_ver}: {e}"
            ) from e
        warnings.append(f"Đã nâng cấp cấu trúc phiên v{cur} → v{next_ver}")
        _log.info("Migrated session v%s → v%s", cur, next_ver)
        cur = next_ver

    if cur != SESSION_VERSION:
        # Không có đường migrate, nhưng version nằm trong KNOWN_VERSIONS
        # (trường hợp lạ — vẫn trả data thô và cảnh báo)
        warnings.append(
            f"Phiên v{cur} không có migration path đến v{SESSION_VERSION}, "
            "dữ liệu có thể bị thiếu một số trường."
        )

    return data, warnings


def save_session(
    path: str,
    subject:     str,
    grade:       str,
    semester:    str,
    year:        str,
    provider:    str,
    model:       str,
    matrix_data: Optional[MatrixData],
    table_rows:  list[MatrixRow],
    exam_data:   Optional[ExamData],
) -> None:
    """Lưu toàn bộ phiên làm việc ra file JSON."""
    data = {
        "version":     SESSION_VERSION,
        "saved_at":    datetime.datetime.now().isoformat(),
        "subject":     subject,
        "grade":       grade,
        "semester":    semester,
        "year":        year,
        "provider":    provider,
        "model":       model,
        "matrix_data": matrix_data.to_dict() if matrix_data else None,
        "table_rows":  [r.to_dict() for r in table_rows],
        "exam_data":   exam_data.to_dict() if exam_data else None,
    }
    # Atomic write: viết ra file tạm rồi rename — tránh corrupt nếu crash
    # giữa chừng (user mất đề cũ).
    path_obj = Path(path)
    tmp_path = path_obj.with_suffix(path_obj.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp_path.replace(path_obj)  # atomic rename
    except Exception:
        # Dọn file tạm nếu có lỗi ghi
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def load_session(path: str) -> dict:
    """
    Tải phiên từ file JSON với auto-migration.
    Trả về dict thô (deserialization domain models ở tầng UI).
    Dict có thêm key '_migration_warnings' (list[str]) nếu đã chạy migration.

    Raises
    ------
    ValueError
        Version không nhận diện được hoặc mới hơn app.
    json.JSONDecodeError
        File hỏng / không phải JSON.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    ver = str(data.get("version", "1.0"))
    if ver == SESSION_VERSION:
        data["_migration_warnings"] = []
        return data

    data, warnings = _migrate_session_data(data)
    data["_migration_warnings"] = warnings
    return data


def list_recent_sessions(n: int = 15) -> list[dict]:
    """Trả về metadata của n phiên gần nhất trong SESSION_DIR."""
    files = sorted(
        SESSION_DIR.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    result = []
    for f in files[:n]:
        try:
            with open(f, encoding="utf-8") as fh:
                meta = json.load(fh)
            n_q = len((meta.get("exam_data") or {}).get("questions", []))
            result.append({
                "path":        str(f),
                "name":        f.stem,
                "saved_at":    meta.get("saved_at", ""),
                "subject":     meta.get("subject", ""),
                "grade":       meta.get("grade", ""),
                "n_questions": n_q,
            })
        except (json.JSONDecodeError, OSError):
            pass
    return result


def autosave_session(
    subject:     str,
    grade:       str,
    semester:    str,
    year:        str,
    provider:    str,
    model:       str,
    matrix_data: Optional[MatrixData],
    table_rows:  list[MatrixRow],
    exam_data:   Optional[ExamData],
) -> str:
    """
    Lưu tự động vào SESSION_DIR với tên theo timestamp.
    Trả về path đã lưu.
    """
    ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    subj = subject.replace(" ", "_")
    path = SESSION_DIR / f"autosave_{subj}{grade}_{ts}.json"
    save_session(
        str(path), subject, grade, semester, year,
        provider, model, matrix_data, table_rows, exam_data,
    )
    return str(path)


def update_question(bank_id: int, q: "Question") -> None:
    """Cập nhật câu hỏi trong ngân hàng (Yêu cầu 3)."""
    db_init()
    con = _get_conn()
    con.execute(
        """UPDATE questions SET topic=?, level=?, qtype=?, question=?,
           data_json=? WHERE id=?""",
        (q.topic, q.level, q.qtype, q.question[:200],
         json.dumps(q.to_dict(), ensure_ascii=False),
         bank_id)
    )
    con.commit()


# ══════════════════════════════════════════════════════════════════════════════
#  EXAM HISTORY (for basic tier limit)
# ══════════════════════════════════════════════════════════════════════════════

def log_exam_generation(machine_id: str) -> None:
    """Ghi nhận một lần tạo đề thành công."""
    db_init()
    con = _get_conn()
    con.execute(
        "INSERT INTO exam_history (machine_id, created_at) VALUES (?, ?)",
        (machine_id, datetime.datetime.now().isoformat())
    )
    con.commit()


def get_today_exam_count(machine_id: str) -> int:
    """Đếm số đề đã tạo trong ngày hôm nay."""
    db_init()
    today = datetime.datetime.now().date().isoformat()
    con = _get_conn()
    cur = con.execute(
        "SELECT COUNT(*) FROM exam_history WHERE machine_id=? AND DATE(created_at)=?",
        (machine_id, today)
    )
    return cur.fetchone()[0]