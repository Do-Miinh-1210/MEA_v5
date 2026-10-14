"""
core/doc_question_parser.py — Parse câu hỏi từ file Word/PDF lên ngân hàng câu hỏi.

Hỗ trợ:
  - Word (.docx): đọc trực tiếp bằng python-docx / mammoth
  - PDF (.pdf):   đọc bằng AI-assisted parsing (gửi text cho AI phân tích)

Định dạng câu hỏi được nhận dạng:
  - "Câu X:" hoặc "Câu X." cho TN
  - "A." / "B." / "C." / "D." cho đáp án TN
  - "Đáp án:" cho đáp án
  - "Bài X:" cho TL
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional
from core.models import Question


def parse_questions_from_file(filepath: str) -> list[Question]:
    """Parse câu hỏi từ file Word, PDF hoặc LaTeX.

    Mọi tier parser đều chạy qua `sanitize_question_objects` trước khi trả
    để UI/DB không bao giờ nhận text quá dài hoặc cấu trúc DS/TN bất thường.
    """
    import logging as _lg
    _log = _lg.getLogger(__name__)

    path = Path(filepath)
    ext = path.suffix.lower()

    if ext == ".docx":
        qs = _parse_docx(filepath)
    elif ext == ".pdf":
        qs = _parse_pdf(filepath)
    elif ext == ".tex":
        from core.latex_parser import parse_latex_file
        qs = parse_latex_file(filepath)
    else:
        raise ValueError(f"Định dạng file không hỗ trợ: {ext}. Chấp nhận: .docx, .pdf, .tex")

    from core.question_parser_common import sanitize_question_objects
    sanitized, _warnings = sanitize_question_objects(qs, logger=_log)
    return sanitized


def _extract_text_docx(filepath: str) -> str:
    """Extract full text from a .docx file, including MathType/OMML equations."""
    try:
        from docx import Document
        from lxml import etree
        doc = Document(filepath)

        # Namespace map for OMML math
        _nsmap = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
            'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        }

        def _extract_para_with_math(para) -> str:
            """Extract paragraph text with OMML math converted to LaTeX notation."""
            try:
                from export.math_converter import extract_para_text_with_math
                return extract_para_text_with_math(para)
            except Exception:
                parts = []
                for child in para._element:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if tag == 'r':
                        text = ''.join(t.text or '' for t in child.findall('.//' + '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
                        if text:
                            parts.append(text)
                    elif tag == 'oMathPara' or tag == 'oMath':
                        try:
                            from export.math_converter import omml_to_latex
                            ltx = omml_to_latex(child)
                            if ltx:
                                parts.append(f"${{{ltx}}}$")
                        except Exception:
                            pass
                    elif tag == 'hyperlink':
                        text = ''.join(t.text or '' for t in child.findall('.//' + '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
                        if text:
                            parts.append(text)
                return ''.join(parts).strip()

        lines = []
        for para in doc.paragraphs:
            text = _extract_para_with_math(para)
            if text:
                lines.append(text)

        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        text = _extract_para_with_math(para)
                        if text:
                            lines.append(text)

        if lines:
            return "\n".join(lines)
    except ImportError:
        pass

    # Fallback to mammoth (handles MathType as images/text)
    try:
        import mammoth
        with open(filepath, "rb") as f:
            result = mammoth.extract_raw_text(f)
        return result.value
    except ImportError:
        raise ImportError("Cần cài python-docx hoặc mammoth để đọc file .docx")


def _extract_text_pdf(filepath: str) -> str:
    """Extract text from a PDF file with improved math handling.

    Trả về text rỗng "" nếu PDF là **scan ảnh** (không có text-layer) — UI nên
    chuyển sang AI Vision pipeline (`core.pdf_to_questions`) cho trường hợp này.
    Chỉ raise ImportError khi THỰC SỰ thiếu thư viện PDF.
    """
    text_parts = []
    fitz_available = False
    pdfplumber_available = False

    # Try PyMuPDF (fitz) first — best quality
    try:
        import fitz  # PyMuPDF
        fitz_available = True
        doc = fitz.open(filepath)
        for page in doc:
            text = page.get_text("text")
            if text and text.strip():
                text_parts.append(text)
        doc.close()
        if text_parts:
            combined = "\n".join(text_parts)
            combined = re.sub(r'\n{3,}', '\n\n', combined)
            return combined
    except ImportError:
        pass

    # Try pdfplumber — good for tables
    try:
        import pdfplumber
        pdfplumber_available = True
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                t = page.extract_text(layout=True)
                if not t:
                    t = page.extract_text()
                if t:
                    text_parts.append(t)

                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            row_text = " | ".join(str(cell or "") for cell in row)
                            if row_text.strip():
                                text_parts.append(row_text)

        if text_parts:
            return "\n".join(text_parts)
    except ImportError:
        pass

    # Tới đây: 1 trong 2 trường hợp
    if not fitz_available and not pdfplumber_available:
        raise ImportError(
            "Thiếu thư viện PDF. Cài: pip install PyMuPDF pdfplumber"
        )

    # Có ít nhất 1 lib nhưng PDF KHÔNG có text-layer (PDF scan ảnh).
    # Trả "" để caller biết là scan → có thể chuyển sang AI Vision pipeline.
    import logging as _lg
    _lg.getLogger(__name__).info(
        "PDF '%s' không có text-layer (scan ảnh). "
        "Caller nên dùng core.pdf_to_questions cho AI Vision OCR.",
        filepath
    )
    return ""


def _parse_docx(filepath: str) -> list[Question]:
    text = _extract_text_docx(filepath)
    return _parse_text_to_questions(text)


def _parse_pdf(filepath: str) -> list[Question]:
    text = _extract_text_pdf(filepath)
    return _parse_text_to_questions(text)


def _parse_text_to_questions(text: str) -> list[Question]:
    """Parse raw text into Question objects.

    Recognizes patterns:
    - "Câu X:" or "Câu X." → start of a question
    - "A." / "B." / "C." / "D." → multiple choice options
    - "Đáp án:" / "ĐA:" → correct answer
    - "Bài X:" → essay question
    """
    questions: list[Question] = []
    lines = text.splitlines()

    # Split into question blocks
    blocks: list[list[str]] = []
    current_block: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Start of a new question?
        if re.match(r'^(Câu|CÂU|Bài|BÀI)\s*\d+', line):
            if current_block:
                blocks.append(current_block)
            current_block = [line]
        elif current_block:
            current_block.append(line)

    if current_block:
        blocks.append(current_block)

    # Parse each block
    for block in blocks:
        q = _parse_one_block(block)
        if q:
            questions.append(q)

    return questions


def _parse_one_block(block: list[str]) -> Optional[Question]:
    """Parse a single question block into a Question.

    Dùng regex chung từ `core.question_parser_common` để đảm bảo nhận
    diện "Câu N:", "A.", "Đáp án:" và "Lời giải:" nhất quán với
    `natural_parser`. Nếu cần mở rộng cú pháp (VD: chấp nhận "Bài tập:"),
    sửa ở module chung thay vì ở đây.
    """
    if not block:
        return None

    # Import cục bộ để không tăng module import graph khi chỉ dùng text-only
    from core.question_parser_common import (
        TN_OPT_RE, ANSWER_RE, SOLUTION_RE,
        strip_question_prefix, detect_qtype_from_options,
        extract_answer_letter,
    )

    # Detect if it's TN (has A. B. C. D. options) or TL
    options: dict[str, str] = {}
    answer_line = ""
    question_lines: list[str] = []
    solution_lines: list[str] = []
    in_solution = False

    for line in block:
        stripped = line.strip()

        # Check for answer indicator
        da_match = ANSWER_RE.match(stripped)
        if da_match:
            answer_line = (da_match.group(1) or "").strip()
            in_solution = True
            continue

        loi_giai_match = SOLUTION_RE.match(stripped)
        if loi_giai_match:
            rest = (loi_giai_match.group(1) or "").strip()
            if rest:
                solution_lines.append(rest)
            in_solution = True
            continue

        if in_solution:
            solution_lines.append(stripped)
            continue

        # Check for options (A./B./C./D.)
        opt_match = TN_OPT_RE.match(stripped)
        if opt_match:
            key = opt_match.group(1).upper()
            options[key] = opt_match.group(2).strip()
            continue

        question_lines.append(stripped)

    # Extract question text (remove "Câu X:" prefix)
    q_text = strip_question_prefix("\n".join(question_lines))

    if not q_text.strip():
        return None

    # Determine question type
    qtype = detect_qtype_from_options(options, n_ds_items=0)
    if qtype == "TN":
        answer = extract_answer_letter(answer_line) or "A"  # default
        return Question(
            qtype="TN",
            level="TH",  # default, user can adjust
            topic="",
            question=q_text.strip(),
            options=options,
            answer=answer,
            solution="\n".join(solution_lines).strip(),
        )
    # Essay / short answer
    return Question(
        qtype="TL",
        level="TH",
        topic="",
        question=q_text.strip(),
        answer=answer_line,
        solution="\n".join(solution_lines).strip(),
    )


def extract_plain_text_for_matrix(filepath: str) -> str:
    """
    Trích toàn bộ văn bản từ .docx hoặc .pdf để AI phân tích ma trận / đề thi.
    Dùng chung với core.ai_matrix_recognizer.
    """
    path = Path(filepath)
    ext = path.suffix.lower()
    if ext == ".docx":
        return _extract_text_docx(filepath)
    if ext == ".pdf":
        return _extract_text_pdf(filepath)
    raise ValueError(f"Chỉ hỗ trợ .docx hoặc .pdf, không nhận: {ext}")
