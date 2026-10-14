"""
core/exam_parser.py — Extract structured questions from a Word/PDF exam paper,
then convert to MatrixData (ma trận đặc tả).

Workflow:
    1. parse_exam_file(path)       — reads .docx or .pdf
    2. ExamPaper.from_raw_text()   — normalises raw text into structured blocks
    3. ExamPaper.to_matrix_data()   — produces MatrixData ready for AI generation
"""

from __future__ import annotations
import re
import os
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
#  Raw question structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class RawQuestion:
    """One question extracted from the exam paper."""
    stt:          int          # số thứ tự câu (1-based)
    qtype:        str          # TN | DS | TLN | TL
    level:        str          # NB | TH | VD
    topic:        str          # chủ đề / nội dung chính
    question:     str          # nội dung câu hỏi đầy đủ
    answer:       str          # đáp án đúng (TN) hoặc keys (DS)
    options:      dict[str, str] = field(default_factory=dict)   # A/B/C/D for TN
    sub_items:    list[str]    = field(default_factory=list)    # a/b/c/d for DS
    requirement:  str = ""


# ──────────────────────────────────────────────────────────────────────────────
#  Question-type helpers
# ──────────────────────────────────────────────────────────────────────────────

_QTYPE_MAP = {
    "trắc nghiệm": "TN",
    "tn": "TN",
    "đúng sai": "DS",
    "đúng/sai": "DS",
    "ds": "DS",
    "tự luận": "TL",
    "tự luận ngắn": "TLN",
    "tl": "TL",
    "tln": "TLN",
    "trả lời ngắn": "TLN",
    "câu hỏi": "TN",
}

_LEVEL_MAP = {
    "nhận biết": "NB",
    "thông hiểu": "TH",
    "vận dụng": "VD",
    "nb": "NB",
    "th": "TH",
    "vd": "VD",
}


def _normalise_qtype(raw: str) -> str:
    raw = raw.strip().lower()
    return _QTYPE_MAP.get(raw, "TN")


def _normalise_level(raw: str) -> str:
    raw = raw.strip().lower()
    return _LEVEL_MAP.get(raw, "NB")


def _normalise_options(lines: list[str]) -> dict[str, str]:
    """Extract A/B/C/D options from option lines."""
    opts: dict[str, str] = {}
    for line in lines:
        m = re.match(r"^\s*([A-Da-d])[.\)]\s*(.+)", line)
        if m:
            opts[m.group(1).upper()] = m.group(2).strip()
    return opts


# ──────────────────────────────────────────────────────────────────────────────
#  ExamPaper
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ExamPaper:
    """Normalised exam paper."""
    title:       str
    subject:     str
    grade:       str
    time_str:    str
    raw_questions: list[RawQuestion] = field(default_factory=list)
    _raw_blocks: list[dict] = field(default_factory=list, repr=False)

    @classmethod
    def from_raw_text(cls, text: str, subject: str = "", grade: str = "12") -> "ExamPaper":
        """Parse raw text (already extracted from docx/pdf) into structured blocks."""
        lines = text.splitlines()
        blocks: list[dict] = []
        current: dict = {}

        for line in lines:
            line = line.strip()
            if not line:
                if current:
                    blocks.append(current)
                    current = {}
                continue

            # Detect question number: "Câu 1.", "Câu 1:", "1.", "1)", "Câu 1 –", "PHẦN I"
            q_m = re.match(
                r"(?:câu\s+)?(\d+)[.\):\-–\s]+(.*)",
                line,
                re.IGNORECASE,
            )
            if q_m:
                if current:
                    blocks.append(current)
                stt = int(q_m.group(1))
                rest = q_m.group(2).strip()

                # Detect type from heading lines before the question
                qtype = "TN"
                level = "NB"
                topic = ""

                # Check if it's a section header like "PHẦN I — NHẬN BIẾT"
                sec_m = re.match(r"phần\s+[IVX\d]+\s*[-—]\s*(.+)", line, re.IGNORECASE)
                if sec_m:
                    current = {"stt": 0, "type": "HEADER", "text": line}
                    blocks.append(current)
                    current = {}
                    continue

                # Detect TN / DS / TL from keywords
                low = rest.lower()
                if any(k in low for k in ["đúng", "sai", "ds"]):
                    qtype = "DS"
                elif any(k in low for k in ["tự luận"]):
                    qtype = "TL"
                elif any(k in low for k in ["trả lời ngắn", "tln"]):
                    qtype = "TLN"

                # Detect level from keywords
                low2 = (rest + " " + line).lower()
                if "vận dụng" in low2:
                    level = "VD"
                elif "thông hiểu" in low2:
                    level = "TH"

                current = {
                    "stt": stt,
                    "type": qtype,
                    "level": level,
                    "topic": topic,
                    "question": rest,
                    "lines": [],
                    "options": [],
                    "answer": "",
                }
            elif current:
                current.setdefault("lines", []).append(line)

        if current:
            blocks.append(current)

        # Second pass: extract options & answers
        questions: list[RawQuestion] = []
        for b in blocks:
            if b.get("type") == "HEADER":
                continue
            stt = b.get("stt", 0)
            qtype = b.get("type", "TN")
            level = b.get("level", "NB")
            question_lines: list[str] = []
            option_lines: list[str] = []
            answer = ""

            for ln in b.get("lines", []):
                m_opt = re.match(r"^\s*[A-Da-d][.\)]\s*(.+)", ln)
                if m_opt:
                    option_lines.append(ln)
                else:
                    question_lines.append(ln)
                # Look for answer hints: "Đáp án: A", "a) Đ", etc.
                am = re.search(
                    r"(?:đáp án|đáp\s*án)\s*[:.]?\s*([A-Da-d\?]?)",
                    ln,
                    re.IGNORECASE,
                )
                if am and not answer:
                    raw_ans = am.group(1).strip()
                    if raw_ans:
                        answer = raw_ans.upper()

            question_text = " ".join(question_lines).strip()
            opts = _normalise_options(option_lines)

            # Detect sub-items (DS): a) Đ b) S ...
            sub_items: list[str] = []
            for ln in option_lines:
                sm = re.match(r"^\s*([a-d])\)\s*(.+)", ln)
                if sm:
                    sub_items.append(sm.group(1).upper())

            questions.append(RawQuestion(
                stt=stt,
                qtype=qtype,
                level=level,
                topic=question_text[:80],
                question=question_text,
                answer=answer,
                options=opts,
                sub_items=sub_items,
            ))

        return cls(
            title="",
            subject=subject,
            grade=grade,
            time_str="90 phút",
            raw_questions=questions,
            _raw_blocks=blocks,
        )

    def to_matrix_data(self) -> "MatrixData":
        """Convert structured questions to MatrixData for AI generation."""
        from core.models import MatrixData, MatrixRow

        rows: list[MatrixRow] = []
        for q in self.raw_questions:
            row = MatrixRow(
                stt=str(q.stt),
                topic=q.topic or q.question[:60],
                level=q.level,
                qtype=q.qtype,
                codes=[],
                requirement=q.requirement or "",
                points=0.25 if q.qtype in ("TN", "DS") else 1.0,
                enabled=True,
                ds_items=[],
            )
            rows.append(row)

        return MatrixData(
            title=self.title or f"Ma trận — {self.subject} lớp {self.grade}",
            time_str=self.time_str,
            rows=rows,
        )


# ──────────────────────────────────────────────────────────────────────────────
#  Main entry point
# ──────────────────────────────────────────────────────────────────────────────

def parse_exam_file(filepath: str) -> tuple[str, ExamPaper]:
    """
    Read a .docx or .pdf file and return (raw_text, ExamPaper).

    Raises:
        ValueError — if the file type is unsupported or unreadable.
    """
    path = os.path.abspath(filepath)
    ext = os.path.splitext(path)[1].lower()

    raw_text = ""

    if ext == ".docx":
        try:
            import docx
            doc = docx.Document(path)
            raw_text = "\n".join(para.text.strip() for para in doc.paragraphs if para.text.strip())

            # Also extract tables
            for table in doc.tables:
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    raw_text += "\n" + " | ".join(cells)

        except ImportError:
            raise ValueError("Thư viện python-docx chưa được cài. Chạy: pip install python-docx")

    elif ext == ".pdf":
        try:
            import pdfplumber
            pages_text: list[str] = []
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        pages_text.append(t)
            raw_text = "\n\n".join(pages_text)

        except ImportError:
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(path)
                pages_text = [doc[i].get_text() for i in range(len(doc))]
                raw_text = "\n\n".join(pages_text)
            except ImportError:
                raise ValueError("Cần cài pdfplumber (pip install pdfplumber) hoặc PyMuPDF (pip install pymupdf)")

    else:
        # Try plain text
        try:
            raw_text = open(path, encoding="utf-8").read()
        except Exception:
            raise ValueError(f"Không đọc được file: {ext} (chỉ hỗ trợ .docx, .pdf, .txt)")

    if not raw_text.strip():
        raise ValueError("File trống hoặc không trích xuất được nội dung.")

    # Parse into ExamPaper
    paper = ExamPaper.from_raw_text(raw_text)

    # Auto-detect title from first non-empty lines
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    if lines:
        paper.title = lines[0][:200]

    return raw_text, paper
