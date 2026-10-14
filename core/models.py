"""
core/models.py — Domain models (dataclasses thuần túy, không phụ thuộc gì ngoài stdlib).
"""

from __future__ import annotations
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional


# ── Sub-model cho câu Đúng/Sai ────────────────────────────────────────────────

@dataclass
class DSItem:
    """Một ý (a/b/c/d) trong câu Đúng–Sai."""
    label:       str          # "a", "b", "c", "d"
    level:       str          # "NB", "TH", "VD"
    requirement: str          # yêu cầu cần đạt cho ý này
    code:        str          # mã gốc từ bảng đặc tả (vd: "1a")


# ── Một hàng trong bảng đặc tả (sau khi parse từ .docx) ─────────────────────

@dataclass
class MatrixRow:
    """Đại diện cho 1 dòng trong bảng đặc tả (= 1 câu hỏi cần tạo)."""
    stt:         str
    topic:       str
    level:       str          # NB | TH | VD
    qtype:       str          # TN | DS | TLN | TL
    codes:       list[str]
    requirement: str
    points:      float        = 1.0
    enabled:     bool         = True
    ds_items:    list[DSItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["ds_items"] = [item.__dict__ for item in self.ds_items]
        return d

    @staticmethod
    def from_dict(d: dict) -> "MatrixRow":
        ds_items = [DSItem(**item) for item in d.pop("ds_items", [])]
        return MatrixRow(**d, ds_items=ds_items)


# ── Câu hỏi đã được AI tạo ra ─────────────────────────────────────────────────

@dataclass
class Question:
    """Câu hỏi hoàn chỉnh sau khi AI sinh ra."""
    qtype:    str             # TN | DS | TLN | TL
    level:    str
    topic:    str
    question: str             # nội dung câu hỏi (NOIDUNG)
    solution: str = ""

    # TN
    options: dict[str, str] = field(default_factory=dict)
    answer:  str             = ""

    # DS
    items:          dict[str, str]  = field(default_factory=dict)
    answers:        dict[str, bool] = field(default_factory=dict)
    item_solutions: dict[str, str]  = field(default_factory=dict)

    # TLN / TL
    points: float = 1.0

    # Hình ảnh đính kèm (đường dẫn tuyệt đối tới file ảnh)
    question_image: str = ""                           # ảnh cho câu hỏi
    option_images:  dict[str, str] = field(default_factory=dict)  # ảnh cho từng đáp án: {"A": "path", ...}
    solution_image: str = ""                           # ảnh cho lời giải
    item_images:    dict[str, str] = field(default_factory=dict)  # ảnh cho từng ý DS: {"a": "path", ...}

    # Mã TikZ do AI tự sinh kèm theo câu hỏi (nếu đề bài có hình vẽ/đồ thị/bảng biến thiên…)
    # Nội dung là khối "\\begin{tikzpicture} ... \\end{tikzpicture}" thuần, chưa bọc document.
    #
    # ── Hợp đồng giữa TikZ Pipeline và Exporter (Word/PDF) ───────────────────
    # Sau khi người dùng chạy
    # `services.tikz_vector_workflow.convert_exam_tikz_to_emf(exam)`:
    #   - Mọi khối TikZ trong `question`/`solution`/`items[x]`/`options[X]` bị
    #     STRIP khỏi text gốc.
    #   - Slot ảnh nhận cặp PNG preview + EMF vector (serialize bằng image_fields):
    #       tikz_code / question (inline)    →  question_image (str)
    #       solution (inline)                →  solution_image (str)
    #       items[x] (inline)                →  item_images[x]  (dict)
    #       options[X] (inline)              →  option_images[X] (dict)
    #       item_solutions[x] (inline)       →  solution_image  (fallback)
    #   - UI đọc PNG preview; Word exporter ưu tiên EMF để giữ nét khi phóng to.
    tikz_code: str = ""

    # Metadata
    requirement:   str  = ""
    _error:        bool = False
    _error_msg:    str  = ""
    _row_snapshot: Optional[dict] = field(default=None, repr=False)

    # ID duy nhất cho mỗi câu hỏi (sinh tự động khi tạo câu)
    question_id: str = field(default_factory=lambda: f"QID-{uuid.uuid4().hex[:10].upper()}")

    # Review result (sau khi AI review)
    _review: Optional[dict] = field(default=None, repr=False)

    def __post_init__(self):
        """Tự động chuẩn hoá công thức toán học (bọc {...} vào $...$) khi khởi tạo."""
        try:
            from core.parser import ensure_math_braces
        except ImportError:
            return  # Tránh lỗi nếu parser chưa sẵn sàng

        if self.question:
            self.question = ensure_math_braces(self.question)
        if self.solution:
            self.solution = ensure_math_braces(self.solution)
        
        if self.options:
            for k, v in self.options.items():
                if v: self.options[k] = ensure_math_braces(v)
        
        if self.items:
            for k, v in self.items.items():
                if v: self.items[k] = ensure_math_braces(v)
        
        if self.item_solutions:
            for k, v in self.item_solutions.items():
                if v: self.item_solutions[k] = ensure_math_braces(v)

    def to_dict(self) -> dict:
        """Chuyển sang dict để serialize JSON."""
        return {k: v for k, v in self.__dict__.items()}

    @staticmethod
    def from_dict(d: dict) -> "Question":
        known = {f.name for f in Question.__dataclass_fields__.values()}  # type: ignore
        filtered = {k: v for k, v in d.items() if k in known}
        return Question(**filtered)

    @property
    def type(self) -> str:
        """Alias cho qtype để tương thích với code cũ."""
        return self.qtype


# ── Ma trận đề (sau khi parse file .docx) ────────────────────────────────────

@dataclass
class MatrixData:
    """Toàn bộ dữ liệu từ file ma trận đặc tả."""
    title:     str
    time_str:  str
    rows:      list[MatrixRow] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "title":    self.title,
            "time_str": self.time_str,
            "rows":     [r.to_dict() for r in self.rows],
        }

    @staticmethod
    def from_dict(d: dict) -> "MatrixData":
        rows = [MatrixRow.from_dict(r) for r in d.get("rows", [])]
        return MatrixData(title=d["title"], time_str=d["time_str"], rows=rows)


# ── Đề kiểm tra hoàn chỉnh ───────────────────────────────────────────────────

@dataclass
class ExamData:
    """Đề thi hoàn chỉnh: metadata + danh sách câu hỏi."""
    exam_title: str
    subject:    str
    grade:      str
    semester:   str
    year:       str
    time:       str
    questions:  list[Question] = field(default_factory=list)
    ma_de:      str            = ""   # "A", "B", ... nếu là bản mã đề
    # Thông tin trường + GV ra đề — cho phép edit SAU khi tạo qua dialog
    # Backward compat: nếu phiên cũ load lên không có 2 field này, default = "".
    school:     str            = ""   # vd: "THCS Nguyễn Trãi"
    teacher:    str            = ""   # vd: "Đỗ Minh"

    # Thống kê nhanh
    @property
    def stats(self) -> dict[str, int]:
        return {
            "TN":  sum(1 for q in self.questions if q.qtype == "TN"),
            "DS":  sum(1 for q in self.questions if q.qtype == "DS"),
            "TLN": sum(1 for q in self.questions if q.qtype == "TLN"),
            "TL":  sum(1 for q in self.questions if q.qtype == "TL"),
            "errors": sum(1 for q in self.questions if q._error),
            "total":  len(self.questions),
        }

    def to_dict(self) -> dict:
        return {
            "exam_title": self.exam_title,
            "subject":    self.subject,
            "grade":      self.grade,
            "semester":   self.semester,
            "year":       self.year,
            "time":       self.time,
            "ma_de":      self.ma_de,
            "school":     self.school,
            "teacher":    self.teacher,
            "questions":  [q.to_dict() for q in self.questions],
        }

    @staticmethod
    def from_dict(d: dict) -> "ExamData":
        questions = [Question.from_dict(q) for q in d.get("questions", [])]
        return ExamData(
            exam_title=d.get("exam_title", "ĐỀ KIỂM TRA"),
            subject=d.get("subject", ""),
            grade=d.get("grade", ""),
            semester=d.get("semester", ""),
            year=d.get("year", ""),
            time=d.get("time", "90 phút"),
            ma_de=d.get("ma_de", ""),
            school=d.get("school", ""),
            teacher=d.get("teacher", ""),
            questions=questions,
        )


# ── Kết quả review ────────────────────────────────────────────────────────────

@dataclass
class ReviewResult:
    score: int   = 5
    ok:    bool  = True
    issue: str   = ""
    tip:   str   = ""


# ── Hệ thống ID có cấu trúc ─────────────────────────────────────────────────

_GEOM_KW = (
    "hình", "tam giác", "đường tròn", "véc tơ", "tọa độ", "không gian",
    "mặt phẳng", "mặt cầu", "hình chóp", "hình trụ", "hình nón",
    "hình lăng trụ", "hình hộp", "elip", "parabol", "hyperbol",
    "góc", "sin", "cos", "tan", "lượng giác",
)

_LEVEL_TO_CODE = {"NB": "N", "TH": "T", "VD": "V", "VDC": "G"}
_QTYPE_TO_NUM  = {"TN": 1, "DS": 2, "TLN": 3, "TL": 4}

_CHAP_RE = re.compile(
    r"(?:chương|ch\.?|chapter)\s*(\d+)", re.IGNORECASE
)


def _detect_subject(topic: str) -> str:
    """Phát hiện môn D (Đại số) hay H (Hình học) từ tên chủ đề."""
    t = topic.lower()
    return "H" if any(kw in t for kw in _GEOM_KW) else "D"


def _extract_chapter(topic: str, stt: str = "", topic_map: dict | None = None) -> int:
    """Trích số chương từ tên chủ đề hoặc STT.

    topic_map dùng để đảm bảo cùng 1 chủ đề luôn cho cùng 1 chương.
    """
    m = _CHAP_RE.search(topic)
    if m:
        return max(1, int(m.group(1)))
    # Nếu có topic_map → gán chương theo thứ tự topic xuất hiện
    if topic_map is not None:
        key = topic.strip().lower()
        if key not in topic_map:
            topic_map[key] = len(topic_map) + 1
        return topic_map[key]
    digits = re.sub(r"\D", "", stt)
    if digits:
        return max(1, int(digits))
    return 1


def compute_structured_id(
    q: "Question",
    grade_str: str,
    existing_qids: set[str] | list[str] | None = None,
    topic_chapter_map: dict | None = None,
) -> str:
    """Tính ID có cấu trúc cho MỘT câu hỏi — dùng trong dialog Sửa câu.

    Khác `assign_structured_ids`: hàm này chạy trên 1 câu, tự xác định
    sequence number = max(existing_qids cùng group_key) + 1 để tránh trùng.

    Args:
        q: Question (đã có topic/level/qtype)
        grade_str: "10"/"11"/"12" — từ tab Cài đặt
        existing_qids: tập ID đã tồn tại (NHCH local + đề hiện tại) để gán seq
                       tiếp theo. None → seq=1.
        topic_chapter_map: map {topic_normalized → chapter_no} để cùng topic
                            luôn cho cùng chương trong session.

    Returns:
        ID dạng "12D1N1-0001" hoặc "" nếu thiếu thông tin.

    Examples:
        >>> q = Question(qtype="TN", level="NB", topic="Đạo hàm")
        >>> compute_structured_id(q, "12")
        '12D1N1-0001'
        >>> compute_structured_id(q, "12", existing_qids={'12D1N1-0001', '12D1N1-0002'})
        '12D1N1-0003'

    Lưu ý: seq dùng 4 chữ số (`0001-9999`) để hỗ trợ NHCH lớn. Vẫn parse
    được ID cũ 2 chữ số (`01-99`) để tính next seq → backward-compatible.
    """
    grade_num = int(re.sub(r"\D", "", grade_str or "") or "0")
    if grade_num < 1 or grade_num > 12:
        return ""

    topic = (q.topic or "").strip()
    level_raw = (q.level or "NB").upper()
    qtype_raw = (q.qtype or "TN").upper()

    subject = _detect_subject(topic)
    chapter = _extract_chapter(topic, "", topic_chapter_map)
    level   = _LEVEL_TO_CODE.get(level_raw, "N")
    qtype   = _QTYPE_TO_NUM.get(qtype_raw, 1)

    # Sequence: max(existing seq trong cùng group) + 1
    prefix = f"{grade_num}{subject}{chapter}{level}{qtype}-"
    seq = 1
    if existing_qids:
        max_seq = 0
        for qid in existing_qids:
            if isinstance(qid, str) and qid.startswith(prefix):
                tail = qid[len(prefix):]
                try:
                    n = int(tail.split("-")[0].split("_")[0])
                    if n > max_seq:
                        max_seq = n
                except ValueError:
                    continue
        seq = max_seq + 1

    return f"{prefix}{seq:04d}"


def assign_structured_ids(
    questions: list[Question],
    grade_str: str,
    rows: list[MatrixRow] | None = None,
) -> None:
    """Gán ID có cấu trúc cho danh sách câu hỏi.

    Format: [Grade][Subj][Chap][Level][Qtype]-[Seq:02d]
    Ví dụ : 11D1N1-01

    Nếu thiếu thông tin → giữ nguyên QID cũ (không ghi đè).
    """
    grade_num = int(re.sub(r"\D", "", grade_str) or "0")
    if grade_num < 1 or grade_num > 12:
        return  # không đủ thông tin

    # Bộ đếm theo nhóm (subject, chapter, level, qtype) → sequence
    counters: dict[tuple, int] = {}
    topic_chapter_map: dict[str, int] = {}  # đảm bảo cùng topic → cùng chapter

    for i, q in enumerate(questions):
        if q._error:
            continue

        # Lấy thông tin từ row snapshot hoặc row gốc
        row = rows[i] if rows and i < len(rows) else None
        topic = q.topic or (row.topic if row else "")
        level_raw = q.level or (row.level if row else "NB")
        qtype_raw = q.qtype or (row.qtype if row else "TN")
        stt = row.stt if row else ""

        subject = _detect_subject(topic)
        chapter = _extract_chapter(topic, stt, topic_chapter_map)
        level   = _LEVEL_TO_CODE.get(level_raw.upper(), "N")
        qtype   = _QTYPE_TO_NUM.get(qtype_raw.upper(), 1)

        group_key = (subject, chapter, level, qtype)
        counters[group_key] = counters.get(group_key, 0) + 1
        seq = counters[group_key]

        try:
            new_id = (
                f"{grade_num}{subject}{chapter}"
                f"{level}{qtype}"
                f"-{seq:04d}"
            )
            q.question_id = new_id
        except Exception:
            pass  # giữ QID cũ
