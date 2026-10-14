"""
core/latex_id_manager.py — Quản lý ID câu hỏi LaTeX

══ NEW FORMAT ══  LMYTZ-QQ     ví dụ: 12D1N1-01
    L  = Lớp (1–12)
    M  = Môn (D: Đại số, H: Hình học)
    Y  = Chương (≥1)
    T  = Level (N/T/V/G) + Dạng bài (≥1)
    QQ = Số thứ tự câu hỏi (01–99, luôn 2 chữ số)

══ OLD FORMAT ══  2 hệ thống:
  System A (không có môn):  [G][Level][Ch][TypeLetter][Sub]-[Q]
    ví dụ: 1C6B1-2   →  grade 11, Cơ bản, ch.6, dạng B, bài 1, câu 2
  System B (có môn D/H):   [G][Subj][Ch][Level][Type]-[Q]
    ví dụ: 2D2K3-2   →  grade 12, Đại số, ch.2, Khá, dạng 3, câu 2
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════
#  CONSTANTS — NEW FORMAT
# ═══════════════════════════════════════════════════════════════════════

VALID_SUBJECTS = {"D", "H"}
VALID_LEVELS = {"N", "T", "V", "G"}

SUBJECT_NAMES = {"D": "Đại số", "H": "Hình học"}
LEVEL_NAMES = {
    "N": "Nhận biết",
    "T": "Thông hiểu",
    "V": "Vận dụng",
    "G": "Vận dụng cao",
}
_LEVEL_ORDER = {"N": 0, "T": 1, "V": 2, "G": 3}
_SUBJECT_ORDER = {"D": 0, "H": 1}

# ── New-format regex ─────────────────────────────────────────────────
_ID_RE = re.compile(
    r"^(\d{1,2})([DH])(\d+)([NTVG])(\d+)-(\d{2})$"
)
_ID_COMMENT_RE = re.compile(
    r"%\s*\[(\d{1,2}[DH]\d+[NTVG]\d+-\d{2})\]"
)

# ── LaTeX environments ───────────────────────────────────────────────
_ENV_BEGIN_RE = re.compile(r"\\begin\{(vd|bt|ex)\}")
_ENV_END_RE = re.compile(r"\\end\{(vd|bt|ex)\}")


# ═══════════════════════════════════════════════════════════════════════
#  CONSTANTS — OLD FORMAT
# ═══════════════════════════════════════════════════════════════════════

# Old ID: [Digit][Letter][Digit][Letter][AlphaNum] optionally -[Digits]
_OLD_ID_RE = re.compile(
    r"^(\d)([A-Z])(\d)([A-Z])([A-Z\d])(?:-(\d+))?$"
)
_OLD_ID_COMMENT_RE = re.compile(
    r"%\s*\[(\d[A-Z]\d[A-Z][A-Z\d](?:-\d+)?)\]"
)

# Combined regex: tìm cả old lẫn new ID trong comment %[…]
_ANY_ID_COMMENT_RE = re.compile(
    r"%\s*\[("
    r"\d{1,2}[DH]\d+[NTVG]\d+-\d{2}"       # new
    r"|"
    r"\d[A-Z]\d[A-Z][A-Z\d](?:-\d+)?"       # old
    r")\]"
)

# Grade code → actual grade
OLD_GRADE_MAP: dict[str, int] = {
    "0": 10, "1": 11, "2": 12, "3": 13,
    "4": 14, "5": 15, "6": 6, "7": 7, "8": 8, "9": 9,
}

# System A: second char (level) → new level
OLD_LEVEL_MAP_A: dict[str, str] = {
    "C": "N",   # Cơ bản    → Nhận biết
    "T": "T",   # Thông hiểu → Thông hiểu
    "K": "V",   # Khá       → Vận dụng
    "G": "G",   # Giỏi      → Vận dụng cao
}

# System B: fourth char (level) → new level
OLD_LEVEL_MAP_B: dict[str, str] = {
    "B": "N",   # Basic       → Nhận biết
    "N": "N",   # Nhận biết   → Nhận biết
    "Y": "N",   # Yếu / rất cơ bản → Nhận biết
    "H": "T",   # Hard        → Thông hiểu
    "T": "T",   # Thông hiểu  → Thông hiểu
    "K": "V",   # Khá         → Vận dụng
    "V": "V",   # Vận dụng    → Vận dụng
    "C": "V",   # Cao         → Vận dụng (cao)
    "G": "G",   # Giỏi        → Vận dụng cao
}

# System A SubCode first letter → dạng bài (type number)
OLD_TYPE_MAP_A: dict[str, int] = {
    "B": 1,  # Bài tập
    "Y": 2,  # Yêu cầu / Vận dụng
    "T": 3,  # Trắc nghiệm / Thực hành
    "K": 4,  # Kiểm tra / Khá
}

# Old level names for display
OLD_LEVEL_NAMES_A: dict[str, str] = {
    "C": "Cơ bản", "T": "Thông hiểu", "K": "Khá", "G": "Giỏi",
}
OLD_LEVEL_NAMES_B: dict[str, str] = {
    "B": "Basic", "N": "Nhận biết", "C": "Cơ bản",
    "H": "Hard", "T": "Thông hiểu", "Y": "Trung bình",
    "K": "Khá", "V": "Vận dụng", "G": "Giỏi",
}


# ═══════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class QuestionID:
    """Một ID câu hỏi (new format) đã được parse."""
    grade: int       # 1–12
    subject: str     # D | H
    chapter: int     # ≥1
    level: str       # N | T | V | G
    qtype: int       # ≥1
    question: int    # ≥1

    def to_string(self) -> str:
        return (
            f"{self.grade}{self.subject}{self.chapter}"
            f"{self.level}{self.qtype}"
            f"-{self.question:02d}"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.to_string(),
            "grade": self.grade,
            "subject": self.subject,
            "subject_name": SUBJECT_NAMES.get(self.subject, ""),
            "chapter": self.chapter,
            "level": self.level,
            "level_name": LEVEL_NAMES.get(self.level, ""),
            "type": self.qtype,
            "question": self.question,
        }

    def sort_key(self) -> tuple:
        return (
            self.grade,
            _SUBJECT_ORDER.get(self.subject, 9),
            self.chapter,
            _LEVEL_ORDER.get(self.level, 9),
            self.qtype,
            self.question,
        )

    def group_key(self) -> str:
        """Prefix chung (không chứa số câu) — dùng để nhóm."""
        return (
            f"{self.grade}{self.subject}{self.chapter}"
            f"{self.level}{self.qtype}"
        )


@dataclass
class OldQuestionID:
    """Một ID câu hỏi (old format) đã được parse."""
    raw: str
    system: str         # "A" | "B"
    grade_code: int     # single digit
    chapter: int
    question: int       # 0 = không có
    # System A
    level_a: str = ""   # C, T, K, G
    subcode1: str = ""  # first letter of SubCode
    subcode2: str = ""  # second char (digit or letter)
    # System B
    subject: str = ""   # D | H
    level_b: str = ""   # B, H, K, G, N, T, V, Y, C
    type_digit: int = 0


# ═══════════════════════════════════════════════════════════════════════
#  CORE FUNCTIONS — NEW FORMAT
# ═══════════════════════════════════════════════════════════════════════

def parse_id(id_str: str) -> Optional[QuestionID]:
    """Parse chuỗi ID mới → QuestionID.  Trả None nếu sai format."""
    m = _ID_RE.match(id_str.strip())
    if not m:
        return None
    return QuestionID(
        grade=int(m.group(1)),
        subject=m.group(2),
        chapter=int(m.group(3)),
        level=m.group(4),
        qtype=int(m.group(5)),
        question=int(m.group(6)),
    )


def generate_id(
    grade: int, subject: str, chapter: int,
    level: str, qtype: int, question: int,
) -> str:
    """Tạo chuỗi ID mới từ các thành phần."""
    if subject not in VALID_SUBJECTS:
        raise ValueError(f"Môn '{subject}' không hợp lệ — cần D hoặc H")
    if level not in VALID_LEVELS:
        raise ValueError(f"Mức độ '{level}' không hợp lệ — cần N/T/V/G")
    return (
        f"{grade}{subject}{chapter}"
        f"{level}{qtype}"
        f"-{question:02d}"
    )


def validate_id(id_str: str) -> tuple[bool, str]:
    """Kiểm tra ID mới.  Trả (is_valid, message)."""
    m = _ID_RE.match(id_str.strip())
    if not m:
        return False, f"Sai format: '{id_str}' — cần dạng 12D1N1-01"
    grade    = int(m.group(1))
    subject  = m.group(2)
    chapter  = int(m.group(3))
    level    = m.group(4)
    qtype    = int(m.group(5))
    question = int(m.group(6))
    errors: list[str] = []
    if not 1 <= grade <= 12:
        errors.append(f"Lớp {grade} ngoài phạm vi 1–12")
    if subject not in VALID_SUBJECTS:
        errors.append(f"Môn '{subject}' không hợp lệ — cần D hoặc H")
    if chapter < 1:
        errors.append(f"Chương {chapter} phải ≥ 1")
    if level not in VALID_LEVELS:
        errors.append(f"Mức độ '{level}' không hợp lệ — cần N/T/V/G")
    if qtype < 1:
        errors.append(f"Dạng bài {qtype} phải ≥ 1")
    if question < 1:
        errors.append(f"Số câu {question} phải ≥ 1")
    if errors:
        return False, "; ".join(errors)
    return True, "Hợp lệ"


def next_id(id_str: str) -> Optional[str]:
    """Tăng số câu lên 1."""
    qid = parse_id(id_str)
    if not qid:
        return None
    qid.question += 1
    return qid.to_string()


# ═══════════════════════════════════════════════════════════════════════
#  CORE FUNCTIONS — OLD FORMAT
# ═══════════════════════════════════════════════════════════════════════

def parse_old_id(id_str: str) -> Optional[OldQuestionID]:
    """Parse chuỗi ID cũ → OldQuestionID.  Trả None nếu sai format."""
    s = id_str.strip()
    m = _OLD_ID_RE.match(s)
    if not m:
        return None

    g1 = m.group(1)           # grade code  (1 digit)
    g2 = m.group(2)           # second char
    g3 = int(m.group(3))      # chapter
    g4 = m.group(4)           # fourth char
    g5 = m.group(5)           # fifth char (letter or digit)
    g6 = int(m.group(6)) if m.group(6) else 0  # question

    if g2 in ("D", "H"):
        # System B: [G][Subject][Ch][Level][Type]-[Q]
        return OldQuestionID(
            raw=s, system="B", grade_code=int(g1),
            chapter=g3, question=g6,
            subject=g2,
            level_b=g4,
            type_digit=int(g5) if g5.isdigit() else 1,
        )
    else:
        # System A: [G][Level][Ch][TypeLetter][Sub]-[Q]
        return OldQuestionID(
            raw=s, system="A", grade_code=int(g1),
            chapter=g3, question=g6,
            level_a=g2,
            subcode1=g4,
            subcode2=g5,
        )


def convert_old_to_new(
    old_id_str: str,
    grade_override: Optional[int] = None,
    subject_override: Optional[str] = None,
) -> Optional[str]:
    """Chuyển ID cũ → ID mới.  Trả None nếu không parse được."""
    old = parse_old_id(old_id_str)
    if not old:
        return None

    grade = grade_override or OLD_GRADE_MAP.get(
        str(old.grade_code), old.grade_code + 10
    )

    if old.system == "B":
        subject  = subject_override or old.subject
        chapter  = old.chapter
        level    = OLD_LEVEL_MAP_B.get(old.level_b, "N")
        qtype    = old.type_digit or 1
        question = old.question or 1
    else:
        subject = subject_override or "D"
        chapter = old.chapter
        level   = OLD_LEVEL_MAP_A.get(old.level_a, "N")
        qtype    = OLD_TYPE_MAP_A.get(old.subcode1, 1)
        question = old.question or 1

    return generate_id(grade, subject, chapter, level, qtype, question)


def describe_old_id(id_str: str) -> Optional[str]:
    """Mô tả ý nghĩa ID cũ bằng tiếng Việt."""
    old = parse_old_id(id_str)
    if not old:
        return None
    grade = OLD_GRADE_MAP.get(str(old.grade_code), old.grade_code + 10)
    if old.system == "B":
        subj = SUBJECT_NAMES.get(old.subject, old.subject)
        lv = OLD_LEVEL_NAMES_B.get(old.level_b, old.level_b)
        return (
            f"Lớp {grade}, {subj}, Chương {old.chapter}, "
            f"Mức {lv}, Dạng {old.type_digit}, Câu {old.question or '?'}"
        )
    else:
        lv = OLD_LEVEL_NAMES_A.get(old.level_a, old.level_a)
        sub = old.subcode1 + old.subcode2
        return (
            f"Lớp {grade}, Chương {old.chapter}, "
            f"Mức {lv}, SubCode {sub}, Câu {old.question or '?'}"
        )


def is_old_format(id_str: str) -> bool:
    """Kiểm tra xem chuỗi có phải ID cũ không."""
    return _OLD_ID_RE.match(id_str.strip()) is not None


def is_new_format(id_str: str) -> bool:
    """Kiểm tra xem chuỗi có phải ID mới không."""
    return _ID_RE.match(id_str.strip()) is not None


# ═══════════════════════════════════════════════════════════════════════
#  INTERNAL ENTRY
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class _IDEntry:
    qid: QuestionID
    file: str = ""
    line: int = 0
    env: str = ""          # vd | bt | ex
    old_id: str = ""       # ID cũ gốc (nếu được chuyển đổi)


# ═══════════════════════════════════════════════════════════════════════
#  MANAGER CLASS
# ═══════════════════════════════════════════════════════════════════════

class LatexIDManager:
    """Đọc, tạo, chuyển đổi và quản lý ID câu hỏi từ file LaTeX."""

    def __init__(self):
        self._entries: dict[str, _IDEntry] = {}

    # ── Properties ───────────────────────────────────────────────────
    @property
    def ids(self) -> list[str]:
        return list(self._entries.keys())

    @property
    def count(self) -> int:
        return len(self._entries)

    # ── Expose stateless helpers ─────────────────────────────────────
    parse_id         = staticmethod(parse_id)
    generate_id      = staticmethod(generate_id)
    validate_id      = staticmethod(validate_id)
    next_id          = staticmethod(next_id)
    parse_old_id     = staticmethod(parse_old_id)
    convert_old_to_new = staticmethod(convert_old_to_new)
    describe_old_id  = staticmethod(describe_old_id)

    # ─────────────────────────────────────────────────────────────────
    #  SCAN FILE  (new-format only)
    # ─────────────────────────────────────────────────────────────────

    def scan_tex_file(self, filepath: str) -> list[dict]:
        """Scan file .tex cho ID mới, trả list {id,line,env,file}."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy: {filepath}")
        text = path.read_text(encoding="utf-8")
        return self._scan_new(text, str(path))

    def load_tex_file(self, filepath: str) -> list[str]:
        """Scan + đăng ký ID mới từ file.  Trả danh sách trùng."""
        return self._register(self.scan_tex_file(filepath))

    def load_tex_string(self, text: str, source: str = "<string>") -> list[str]:
        """Scan + đăng ký ID mới từ chuỗi.  Trả trùng."""
        return self._register(self._scan_new(text, source))

    def _scan_new(self, text: str, source: str) -> list[dict]:
        results: list[dict] = []
        cur_env = ""
        for lineno, line in enumerate(text.splitlines(), 1):
            em = _ENV_BEGIN_RE.search(line)
            if em:
                cur_env = em.group(1)
            em2 = _ENV_END_RE.search(line)
            if em2 and em2.group(1) == cur_env:
                cur_env = ""
            for m in _ID_COMMENT_RE.finditer(line):
                id_str = m.group(1)
                if parse_id(id_str):
                    results.append({
                        "id": id_str, "line": lineno,
                        "env": cur_env, "file": source,
                    })
        return results

    def _register(self, items: list[dict], old_id: str = "") -> list[str]:
        dups: list[str] = []
        for item in items:
            id_str = item["id"]
            if id_str in self._entries:
                dups.append(id_str)
                continue
            qid = parse_id(id_str)
            if qid:
                self._entries[id_str] = _IDEntry(
                    qid=qid, file=item.get("file", ""),
                    line=item.get("line", 0), env=item.get("env", ""),
                    old_id=item.get("old_id", old_id),
                )
        return dups

    # ─────────────────────────────────────────────────────────────────
    #  SCAN & CONVERT OLD → NEW
    # ─────────────────────────────────────────────────────────────────

    def scan_old_ids_in_file(self, filepath: str) -> list[dict]:
        """Tìm tất cả ID cũ trong file .tex.

        Trả list {old_id, new_id, line, env, file, description}.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy: {filepath}")
        text = path.read_text(encoding="utf-8")
        return self._scan_old(text, str(path))

    def scan_old_ids_in_string(
        self, text: str, source: str = "<string>",
    ) -> list[dict]:
        """Tìm tất cả ID cũ trong chuỗi LaTeX."""
        return self._scan_old(text, source)

    def _scan_old(
        self, text: str, source: str,
        grade_override: Optional[int] = None,
        subject_override: Optional[str] = None,
    ) -> list[dict]:
        results: list[dict] = []
        cur_env = ""
        for lineno, line in enumerate(text.splitlines(), 1):
            em = _ENV_BEGIN_RE.search(line)
            if em:
                cur_env = em.group(1)
            em2 = _ENV_END_RE.search(line)
            if em2 and em2.group(1) == cur_env:
                cur_env = ""
            for m in _OLD_ID_COMMENT_RE.finditer(line):
                old_str = m.group(1)
                # Bỏ qua nếu đây thực ra là ID mới
                if is_new_format(old_str):
                    continue
                if not is_old_format(old_str):
                    continue
                new_str = convert_old_to_new(
                    old_str,
                    grade_override=grade_override,
                    subject_override=subject_override,
                )
                results.append({
                    "old_id": old_str,
                    "new_id": new_str or "???",
                    "description": describe_old_id(old_str) or "",
                    "line": lineno,
                    "env": cur_env,
                    "file": source,
                })
        return results

    def convert_tex_file(
        self, filepath: str,
        grade_override: Optional[int] = None,
        subject_override: Optional[str] = None,
    ) -> tuple[str, list[dict]]:
        """Đọc file .tex, chuyển tất cả ID cũ → mới.

        Returns (new_text, conversion_log).
        conversion_log = list of {old_id, new_id, line}.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy: {filepath}")
        text = path.read_text(encoding="utf-8")
        return self.convert_tex_string(
            text, source=str(path),
            grade_override=grade_override,
            subject_override=subject_override,
        )

    def convert_tex_string(
        self, text: str, source: str = "<string>",
        grade_override: Optional[int] = None,
        subject_override: Optional[str] = None,
    ) -> tuple[str, list[dict]]:
        """Chuyển tất cả ID cũ → mới trong chuỗi LaTeX.

        - Thay %[old_id] bằng %[new_id]
        - Đếm trùng: nếu cùng new_id đã xuất hiện → tự tăng câu
        - Trả (new_text, conversion_log)
        """
        log: list[dict] = []
        # Track new IDs đã dùng để tránh trùng
        used_groups: dict[str, int] = {}  # group_key → max question

        # Pre-load existing entries
        for entry in self._entries.values():
            gk = entry.qid.group_key()
            used_groups[gk] = max(
                used_groups.get(gk, 0), entry.qid.question,
            )

        lines = text.splitlines()
        result: list[str] = []
        cur_env = ""

        for lineno, line in enumerate(lines, 1):
            em = _ENV_BEGIN_RE.search(line)
            if em:
                cur_env = em.group(1)
            em2 = _ENV_END_RE.search(line)
            if em2 and em2.group(1) == cur_env:
                cur_env = ""

            new_line = line
            for m in _OLD_ID_COMMENT_RE.finditer(line):
                old_str = m.group(1)
                if is_new_format(old_str):
                    continue
                if not is_old_format(old_str):
                    continue

                new_str = convert_old_to_new(
                    old_str,
                    grade_override=grade_override,
                    subject_override=subject_override,
                )
                if not new_str:
                    continue

                # Xử lý trùng: tăng question number
                qid = parse_id(new_str)
                if qid:
                    gk = qid.group_key()
                    cur_max = used_groups.get(gk, 0)
                    if qid.question <= cur_max:
                        qid.question = cur_max + 1
                    used_groups[gk] = qid.question
                    new_str = qid.to_string()

                    # Đăng ký
                    if new_str not in self._entries:
                        self._entries[new_str] = _IDEntry(
                            qid=qid, file=source, line=lineno,
                            env=cur_env, old_id=old_str,
                        )

                new_line = new_line.replace(
                    f"%[{old_str}]", f"%[{new_str}]", 1,
                )
                log.append({
                    "old_id": old_str,
                    "new_id": new_str,
                    "line": lineno,
                    "env": cur_env,
                })

            result.append(new_line)

        return "\n".join(result), log

    def load_and_convert_tex_file(
        self, filepath: str,
        grade_override: Optional[int] = None,
        subject_override: Optional[str] = None,
    ) -> tuple[str, list[dict]]:
        """Đọc file .tex, chuyển old→new, đăng ký, trả (new_text, log).

        Tiện dùng khi upload file .tex vào kho NHCH.
        """
        return self.convert_tex_file(
            filepath,
            grade_override=grade_override,
            subject_override=subject_override,
        )

    # ─────────────────────────────────────────────────────────────────
    #  DUPLICATE CHECK
    # ─────────────────────────────────────────────────────────────────

    def check_duplicate(self, id_str: str) -> dict:
        """Kiểm tra trùng + gợi ý ID tiếp theo."""
        exists = id_str in self._entries
        entry = self._entries.get(id_str)
        return {
            "id": id_str,
            "duplicate": exists,
            "existing_file": entry.file if entry else "",
            "existing_line": entry.line if entry else 0,
            "suggestion": self.suggest_next(id_str) if exists else "",
        }

    def suggest_next(self, id_str: str) -> str:
        """Gợi ý ID tiếp theo trong cùng nhóm."""
        qid = parse_id(id_str)
        if not qid:
            return ""
        group = qid.group_key()
        max_q = 0
        for entry in self._entries.values():
            if entry.qid.group_key() == group:
                max_q = max(max_q, entry.qid.question)
        return f"{group}-{max_q + 1:02d}"

    # ─────────────────────────────────────────────────────────────────
    #  AUTO-ASSIGN
    # ─────────────────────────────────────────────────────────────────

    def auto_assign_ids(
        self, text: str,
        grade: int, subject: str, chapter: int,
        level: str, qtype: int,
    ) -> str:
        r"""Tự gán ID cho \begin{vd|bt|ex} chưa có %[…]."""
        group = f"{grade}{subject}{chapter}{level}{qtype}"
        max_q = 0
        for entry in self._entries.values():
            if entry.qid.group_key() == group:
                max_q = max(max_q, entry.qid.question)

        lines = text.splitlines()
        result: list[str] = []
        for line in lines:
            if _ENV_BEGIN_RE.search(line) \
               and not _ID_COMMENT_RE.search(line) \
               and not _OLD_ID_COMMENT_RE.search(line):
                max_q += 1
                new_id = f"{group}-{max_q:02d}"
                line = f"{line}  %[{new_id}]"
                qid = parse_id(new_id)
                if qid:
                    self._entries[new_id] = _IDEntry(
                        qid=qid, file="<auto>", line=0, env="",
                    )
            result.append(line)
        return "\n".join(result)

    # ─────────────────────────────────────────────────────────────────
    #  EXPORT / SORT / FILTER / SUMMARY
    # ─────────────────────────────────────────────────────────────────

    def export_json(self, filepath: str = "") -> str:
        """Export toàn bộ ID ra JSON."""
        data = []
        for id_str in self.sorted_ids():
            entry = self._entries[id_str]
            d = entry.qid.to_dict()
            d["file"] = entry.file
            d["line"] = entry.line
            d["env"] = entry.env
            d["old_id"] = entry.old_id
            data.append(d)
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        if filepath:
            Path(filepath).write_text(json_str, encoding="utf-8")
        return json_str

    def sorted_ids(self) -> list[str]:
        return sorted(
            self._entries,
            key=lambda x: self._entries[x].qid.sort_key(),
        )

    def filter_by_chapter(
        self, grade: int, subject: str, chapter: int,
    ) -> list[str]:
        return sorted(
            (s for s, e in self._entries.items()
             if e.qid.grade == grade
             and e.qid.subject == subject
             and e.qid.chapter == chapter),
            key=lambda x: self._entries[x].qid.sort_key(),
        )

    def filter_by_level(self, level: str) -> list[str]:
        return sorted(
            (s for s, e in self._entries.items() if e.qid.level == level),
            key=lambda x: self._entries[x].qid.sort_key(),
        )

    def summary(self) -> dict:
        from collections import Counter
        levels: Counter[str] = Counter()
        subjects: Counter[str] = Counter()
        chapters: Counter[str] = Counter()
        for entry in self._entries.values():
            q = entry.qid
            levels[q.level] += 1
            subjects[q.subject] += 1
            chapters[f"L{q.grade}{q.subject}-C{q.chapter}"] += 1
        return {
            "total": self.count,
            "by_level": {
                LEVEL_NAMES.get(k, k): v
                for k, v in sorted(
                    levels.items(),
                    key=lambda x: _LEVEL_ORDER.get(x[0], 9),
                )
            },
            "by_subject": {
                SUBJECT_NAMES.get(k, k): v for k, v in subjects.items()
            },
            "by_chapter": dict(sorted(chapters.items())),
        }


# ═══════════════════════════════════════════════════════════════════════
#  DEMO
# ═══════════════════════════════════════════════════════════════════════

_DEMO_OLD_LATEX = r"""
\section{LUỸ THỪA VỚI SỐ MŨ THỰC}
\subsection{Các dạng bài tập}
\begin{dang}{Tính giá trị biểu thức}
\end{dang}
\begin{vd}%[1K6BH-1]
Tính $16^{\tfrac{3}{2}}$.
\end{vd}
\begin{vd}%[1C6B1-2]
Rút gọn $\sqrt[3]{\dfrac{125}{64}}\cdot \sqrt[4]{81}$.
\end{vd}
\begin{bt}%[1C6B1-1]
Tính $8^{\tfrac{-2}{3}}$.
\end{bt}
\begin{bt}%[2D2B1-1]
Rút gọn biểu thức $a^3 \cdot a^{-5}$.
\end{bt}
\begin{vd}%[2D2K3-2]
Cho $\log_a b = 3$. Tính $\log_{a^2} b^5$.
\end{vd}
\begin{bt}%[2D2G4-4]
Giải phương trình $4^x - 3 \cdot 2^x + 2 = 0$.
\end{bt}
\begin{vd}%[1T6Y2-1]
Tính $\log_2 \dfrac{1}{4}$.
\end{vd}
\begin{bt}%[1K6BH-1]
Tính $A=\left(\dfrac{1}{2}\right)^{-8}\cdot 8^{-2}$.
\end{bt}
\begin{vd}
Câu chưa có ID — test auto assign.
\end{vd}
"""


def demo():
    """Chạy demo minh hoạ toàn bộ chức năng (old + new)."""
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    SEP = "=" * 66

    print(SEP)
    print("  DEMO — LatexIDManager  (Old ↔ New ID Conversion)")
    print(SEP)

    mgr = LatexIDManager()

    # ═══════════════════════════════════════════════════════════════
    # PART 1: PARSE OLD IDs
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("  PART 1: PARSE OLD ID")
    print("─" * 50)
    old_tests = [
        "1C6B1-2",    # System A: grade 11, Cơ bản, ch.6
        "1K6BH-1",    # System A: grade 11, Khá, ch.6
        "1T6Y2-1",    # System A: grade 11, Thông hiểu, ch.6
        "2D2B1-1",    # System B: grade 12, Đại số, ch.2
        "2D2K3-2",    # System B: grade 12, Khá, ch.2
        "2D2G4-4",    # System B: grade 12, Giỏi, ch.2
        "2D2B3",      # System B: no question number
    ]
    for t in old_tests:
        old = parse_old_id(t)
        desc = describe_old_id(t) or "?"
        print(f"  {t:15s} → System {old.system}  |  {desc}")

    # ═══════════════════════════════════════════════════════════════
    # PART 2: CONVERT OLD → NEW
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("  PART 2: CONVERT OLD → NEW")
    print("─" * 50)
    for t in old_tests:
        new = convert_old_to_new(t)
        print(f"  {t:15s} → {new}")

    # ═══════════════════════════════════════════════════════════════
    # PART 3: SCAN & CONVERT LaTeX STRING
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("  PART 3: SCAN & CONVERT .tex (auto old→new)")
    print("─" * 50)
    new_text, log = mgr.convert_tex_string(
        _DEMO_OLD_LATEX, source="demo_old.tex",
    )
    print(f"  Converted {len(log)} IDs:")
    for entry in log:
        print(f"    Line {entry['line']:3d}:  {entry['old_id']:12s} → "
              f"{entry['new_id']:18s}  [{entry['env']}]")

    # Show a snippet of converted text
    print("\n  Converted text (first \\begin lines):")
    for ln in new_text.splitlines():
        if "\\begin{vd}" in ln or "\\begin{bt}" in ln:
            print(f"    {ln.strip()}")

    # ═══════════════════════════════════════════════════════════════
    # PART 4: DUPLICATE HANDLING
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("  PART 4: DUPLICATE HANDLING (1K6BH-1 appeared 2x)")
    print("─" * 50)
    # 1K6BH-1 appears twice in demo → second one auto-incremented
    dup_entries = [e for e in log if e["old_id"] == "1K6BH-1"]
    for e in dup_entries:
        print(f"    Line {e['line']}: {e['old_id']} → {e['new_id']}")
    print("    (Second occurrence auto-incremented question number)")

    # ═══════════════════════════════════════════════════════════════
    # PART 5: ALL REGISTERED IDs (sorted)
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("  PART 5: ALL REGISTERED IDs (sorted)")
    print("─" * 50)
    for s in mgr.sorted_ids():
        entry = mgr._entries[s]
        old_tag = f"  (was {entry.old_id})" if entry.old_id else ""
        print(f"    {s}{old_tag}")

    # ═══════════════════════════════════════════════════════════════
    # PART 6: SUMMARY
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("  PART 6: SUMMARY")
    print("─" * 50)
    sm = mgr.summary()
    print(f"    Tổng:     {sm['total']}")
    print(f"    Mức độ:   {sm['by_level']}")
    print(f"    Môn:      {sm['by_subject']}")
    print(f"    Chương:   {sm['by_chapter']}")

    # ═══════════════════════════════════════════════════════════════
    # PART 7: EXPORT JSON
    # ═══════════════════════════════════════════════════════════════
    print("\n" + "─" * 50)
    print("  PART 7: EXPORT JSON (first 3 entries)")
    print("─" * 50)
    json_str = mgr.export_json()
    data = json.loads(json_str)
    for item in data[:3]:
        print(f"    {json.dumps(item, ensure_ascii=False)}")
    print(f"    ... ({len(data)} entries total)")

    print(f"\n{SEP}")
    print("  DEMO COMPLETE")
    print(SEP)


if __name__ == "__main__":
    demo()
