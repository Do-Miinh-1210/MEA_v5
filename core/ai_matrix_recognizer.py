"""
core/ai_matrix_recognizer.py — Nhận diện cấu trúc ma trận đề kiểm tra bằng AI.

Khi parser truyền thống trả về 0 câu, module này gửi toàn bộ nội dung
văn bản của file .docx cho AI để nhận diện:
  - Chủ đề / nội dung kiến thức
  - Loại câu hỏi (TN, DS, TLN, TL)
  - Mức độ (NB, TH, VD)
  - Số câu, điểm/câu
  - Yêu cầu cần đạt

Nếu không nhận diện được cấu trúc, module có thể tạo ma trận mới
dựa trên nội dung kiến thức trong file.
"""

from __future__ import annotations
import json
import re
from typing import Callable, Optional

from core.models import MatrixData, MatrixRow

# ══════════════════════════════════════════════════════════════════════════════
#  PROMPT NHẬN DIỆN CẤU TRÚC MA TRẬN
# ══════════════════════════════════════════════════════════════════════════════

_RECOGNIZE_PROMPT = """Bạn là chuyên gia phân tích cấu trúc đề kiểm tra THCS/THPT Việt Nam cho TẤT CẢ CÁC MÔN HỌC.

Tôi gửi NỘI DUNG một tài liệu Word hoặc PDF: có thể là ma trận đề / bảng đặc tả, hoặc ĐỀ THI HOÀN CHỈNH (các khối "Câu 1:", TN có A.B.C.D., phần tự luận…).
Hãy NHẬN DIỆN CẤU TRÚC MA TRẬN từ nội dung này (gom các câu theo chủ đề, loại TN/DS/TLN/TL, mức NB/TH/VD, điểm hợp lý).

CÁC MÔN HỌC HỖ TRỢ:
- Toán, Vật lý (Lý), Hóa học (Hóa), Sinh học (Sinh)
- Ngữ văn (Văn), Tiếng Anh, Lịch sử (Sử), Địa lý (Địa)
- GDCD/GDKTPL, Tin học, Công nghệ
- Và các môn khác

LƯU Ý QUAN TRỌNG:
- NHẬN DIỆN MÔN HỌC từ nội dung (tiêu đề, chủ đề, từ khóa đặc trưng)
- Nội dung có thể là BẢNG (các cột phân cách bằng " | ")
- Mỗi dòng bảng chứa: STT, Chủ đề/Chương, Nội dung, Mức độ (Nhận biết/Thông hiểu/Vận dụng), Số câu, Điểm
- Bảng đặc tả thường có CỘT mức độ: "Nhận biết", "Thông hiểu", "Vận dụng"
- Số trong cột mức độ là SỐ CÂU ở mức đó
- Nếu bảng có dòng "Câu 1, 2, 3..." hoặc "TL1, TL2..." → đó là mã câu hỏi
- Phân biệt loại câu: câu trắc nghiệm (TN), câu đúng-sai (DS), trả lời ngắn (TLN), tự luận (TL)
- Nếu đề ghi "40 câu trắc nghiệm" → tất cả là TN
- Nếu có câu "TL1, TL2..." → loại = "TL" (tự luận)
- "Vận dụng cao" cũng xếp vào level "VD"
- Các môn KHTN (Lý, Hóa, Sinh) có thể gộp 3 phần trong 1 đề
- Các môn KHXH (Sử, Địa, GDCD) có thể gộp 3 phần trong 1 đề
- Đề Ngữ văn thường có: Đọc hiểu (TN/TLN) + Viết (TL)
- Đề Tiếng Anh có thể có: Reading, Writing, Listening, Use of English

ĐẶC TRƯNG CẤU TRÚC TỪNG MÔN:
- Toán: TN + DS + TLN + TL, tổng 10 điểm
- Lý/Hóa/Sinh: TN (chủ yếu), có thể kèm TL, mỗi phần thường 3.33 điểm nếu gộp KHTN
- Sử/Địa/GDCD: TN (chủ yếu), có thể kèm TL, mỗi phần thường 3.33 điểm nếu gộp KHXH
- Ngữ văn: Đọc hiểu (2-3đ) + Nghị luận văn học/xã hội (7-8đ)
- Tiếng Anh: TN (chủ yếu), có thể kèm viết lại câu

Mỗi câu hỏi nhận diện cần:
- topic: Chủ đề/Chương (giữ nguyên tên gốc trong tài liệu)
- qtype: "TN" | "DS" | "TLN" | "TL"
- level: "NB" (nhận biết) | "TH" (thông hiểu) | "VD" (vận dụng)
- count: Số câu (>= 1)
- points: Điểm/câu (TN thường = 0.25, DS = 1.0, TLN = 0.5, TL = 1.0 nếu không rõ)
- requirement: Mô tả yêu cầu cần đạt (lấy từ nội dung bảng hoặc tóm tắt)

TRẢ VỀ JSON duy nhất:
{{
  "title": "Tiêu đề đề kiểm tra",
  "subject": "Toán|Lý|Hóa|Sinh|Văn|Anh|Sử|Địa|GDCD|Tin|...",
  "time_str": "90 phút",
  "rows": [
    {{
      "topic": "Chủ đề",
      "qtype": "TN",
      "level": "NB",
      "count": 3,
      "points": 0.25,
      "requirement": "Yêu cầu cần đạt"
    }}
  ]
}}

CHỈ trả về JSON, KHÔNG kèm text giải thích.

NỘI DUNG TÀI LIỆU:
{doc_text}
"""

# ══════════════════════════════════════════════════════════════════════════════
#  PROMPT TẠO MA TRẬN TỪ NỘI DUNG KIẾN THỨC
# ══════════════════════════════════════════════════════════════════════════════

_CREATE_PROMPT = """Bạn là chuyên gia biên soạn đề kiểm tra THCS/THPT Việt Nam cho TẤT CẢ CÁC MÔN HỌC.

Tôi gửi NỘI DUNG một tài liệu Word hoặc PDF (kiến thức, bài học, hoặc đề thi mẫu).
File có thể KHÔNG có sẵn bảng ma trận, nhưng chứa chủ đề hoặc danh sách câu hỏi.

Hãy TẠO MỘT MA TRẬN ĐỀ KIỂM TRA PHÙ HỢP dựa trên các chủ đề kiến thức trong file.

BƯỚC 1 — NHẬN DIỆN MÔN HỌC:
Xác định môn học từ nội dung: Toán, Lý, Hóa, Sinh, Văn, Anh, Sử, Địa, GDCD, Tin, Công nghệ, ...

BƯỚC 2 — TẠO MA TRẬN THEO ĐẶC TRƯNG MÔN:

Cấu trúc theo MÔN TOÁN:
  - TN: 50-70% (0.25đ/câu), DS: 10-20% (1.0đ/câu), TLN: 10-15% (0.5đ/câu), TL: 10-20% (1.0đ/câu)

Cấu trúc theo MÔN LÝ/HÓA/SINH (KHTN):
  - TN: 70-80% (0.25đ/câu), TL: 20-30% (1.0-2.0đ/câu)
  - Nếu đề gộp KHTN: mỗi môn khoảng 3.33đ

Cấu trúc theo MÔN SỬ/ĐỊA/GDCD (KHXH):
  - TN: 70-80% (0.25đ/câu), TL: 20-30% (1.0-2.0đ/câu)
  - Nếu đề gộp KHXH: mỗi môn khoảng 3.33đ

Cấu trúc theo MÔN NGỮ VĂN:
  - Đọc hiểu: TN + TLN (2-3đ)
  - Nghị luận xã hội: TL (2-3đ)
  - Nghị luận văn học: TL (4-5đ)

Cấu trúc theo MÔN TIẾNG ANH:
  - TN: 80-90% (0.25đ/câu), viết: TL (1.0-2.0đ/câu)

Cấu trúc MẶC ĐỊNH (các môn khác):
  - TN: 60-80% (0.25đ/câu), TL: 20-40% (1.0đ/câu)

PHÂN BỔ MỨC ĐỘ (chung cho mọi môn):
  - Nhận biết (NB): ~30%, Thông hiểu (TH): ~30%, Vận dụng (VD): ~40%

Tổng điểm: 10.0

TRẢ VỀ JSON duy nhất:
{{
  "title": "Đề kiểm tra [tên môn/chủ đề]",
  "subject": "Toán|Lý|Hóa|Sinh|Văn|Anh|Sử|Địa|GDCD|Tin|...",
  "time_str": "90 phút",
  "rows": [
    {{
      "topic": "Chủ đề kiến thức",
      "qtype": "TN",
      "level": "NB",
      "count": 3,
      "points": 0.25,
      "requirement": "Yêu cầu cần đạt"
    }}
  ]
}}

CHỈ trả về JSON, KHÔNG kèm text giải thích.

NỘI DUNG TÀI LIỆU:
{doc_text}
"""


def _omml_to_text(elem) -> str:
    """Convert OMML math element to readable text."""
    texts = []
    for node in elem.iter():
        tag = node.tag.split('}')[-1] if '}' in node.tag else node.tag
        if tag == 't' and node.text:
            texts.append(node.text)
    return ' '.join(texts).strip()


def _extract_para_text_with_math(para) -> str:
    """Extract paragraph text including OMML math."""
    parts = []
    for child in para._element:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'r':
            text = ''.join(
                t.text or '' for t in child.findall(
                    './/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'
                )
            )
            if text:
                parts.append(text)
        elif tag in ('oMathPara', 'oMath'):
            math_text = _omml_to_text(child)
            if math_text:
                parts.append(f"${{{math_text}}}$")
        elif tag == 'hyperlink':
            text = ''.join(
                t.text or '' for t in child.findall(
                    './/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'
                )
            )
            if text:
                parts.append(text)
    return ''.join(parts).strip()


def extract_doc_text(filepath: str) -> str:
    """Trích xuất toàn bộ text từ file .docx (bảng + đoạn văn + MathType/OMML)."""
    from docx import Document

    doc = Document(filepath)
    parts: list[str] = []

    for para in doc.paragraphs:
        text = _extract_para_text_with_math(para)
        if text:
            parts.append(text)

    for table in doc.tables:
        for row in table.rows:
            cells = []
            for cell in row.cells:
                cell_parts = []
                for para in cell.paragraphs:
                    t = _extract_para_text_with_math(para)
                    if t:
                        cell_parts.append(t)
                cells.append(" ".join(cell_parts))
            parts.append(" | ".join(cells))

    return "\n".join(parts)


def extract_text_from_matrix_source(filepath: str) -> str:
    """
    Trích văn bản từ .docx (bảng + đoạn) hoặc .pdf (PyMuPDF/pdfplumber).
    """
    from pathlib import Path

    ext = Path(filepath).suffix.lower()
    if ext == ".docx":
        return extract_doc_text(filepath)
    if ext == ".pdf":
        from core.doc_question_parser import extract_plain_text_for_matrix

        return extract_plain_text_for_matrix(filepath)
    return ""


def _parse_ai_response(raw: str) -> Optional[dict]:
    """Parse JSON từ phản hồi AI (loại bỏ markdown fences nếu có)."""
    text = raw.strip()

    # Loại bỏ ```json ... ``` wrapper
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()

    # Tìm JSON object đầu tiên
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        text = text[start:end]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _normalize_qtype(raw: str) -> str:
    """Chuẩn hóa loại câu hỏi."""
    raw = raw.strip().upper()
    mapping = {
        "TN": "TN", "TRACNGHIEM": "TN", "TRẮC NGHIỆM": "TN",
        "DS": "DS", "ĐÚNG SAI": "DS", "DUNGSAI": "DS", "ĐÚNG-SAI": "DS", "Đ/S": "DS", "Đ-S": "DS", "D/S": "DS", "D-S": "DS",
        "TLN": "TLN", "TRẢLỜINGẮN": "TLN", "TRẢ LỜI NGẮN": "TLN",
        "TL": "TL", "TỰLUẬN": "TL", "TỰ LUẬN": "TL",
    }
    return mapping.get(raw, raw if raw in ("TN", "DS", "TLN", "TL") else "TN")


def _normalize_level(raw: str) -> str:
    """Chuẩn hóa mức độ."""
    raw = raw.strip().upper()
    mapping = {
        "NB": "NB", "NHẬN BIẾT": "NB", "NHẬNBIẾT": "NB",
        "TH": "TH", "THÔNG HIỂU": "TH", "THÔNGHIỂU": "TH",
        "VD": "VD", "VẬN DỤNG": "VD", "VẬNDỤNG": "VD",
            }
    return mapping.get(raw, raw if raw in ("NB", "TH", "VD") else "NB")


_DEFAULT_POINTS = {"TN": 0.25, "DS": 1.0, "TLN": 0.5, "TL": 1.0}


def _build_matrix_from_json(data: dict) -> Optional[MatrixData]:
    """Chuyển JSON đã parse thành MatrixData."""
    if not data or "rows" not in data:
        return None

    title = data.get("title", "Ma trận nhận diện bằng AI")
    subject = data.get("subject", "")
    if subject and subject not in title:
        title = f"{title} — {subject}"
    time_str = data.get("time_str", "")

    rows: list[MatrixRow] = []
    stt = 1
    for item in data["rows"]:
        if not isinstance(item, dict):
            continue

        topic = item.get("topic", "").strip()
        if not topic:
            continue

        qtype = _normalize_qtype(item.get("qtype", "TN"))
        level = _normalize_level(item.get("level", "NB"))
        count = max(1, int(item.get("count", 1)))
        points = float(item.get("points", _DEFAULT_POINTS.get(qtype, 1.0)))
        requirement = item.get("requirement", "").strip()

        for _ in range(count):
            rows.append(MatrixRow(
                stt=str(stt),
                topic=topic,
                level=level,
                qtype=qtype,
                codes=[],
                requirement=requirement,
                points=points,
                enabled=True,
            ))
            stt += 1

    if not rows:
        return None

    return MatrixData(title=title, time_str=time_str, rows=rows)


def recognize_matrix(
    filepath: str,
    ai_call: Callable[[str], str],
    on_progress: Optional[Callable[[str], None]] = None,
) -> Optional[MatrixData]:
    """
    Nhận diện cấu trúc ma trận từ file .docx hoặc .pdf bằng AI.

    Returns:
        MatrixData nếu thành công, None nếu thất bại
    """
    if on_progress:
        on_progress("Đang trích xuất nội dung tài liệu...")

    doc_text = extract_text_from_matrix_source(filepath)
    if not doc_text.strip():
        return None

    # Giới hạn text gửi AI (tránh vượt token limit)
    if len(doc_text) > 15000:
        doc_text = doc_text[:15000] + "\n... (nội dung đã được cắt bớt)"

    prompt = _RECOGNIZE_PROMPT.format(doc_text=doc_text)

    if on_progress:
        on_progress("Đang gửi AI phân tích cấu trúc ma trận...")

    raw_response = ai_call(prompt)

    if on_progress:
        on_progress("Đang xử lý kết quả...")

    data = _parse_ai_response(raw_response)
    return _build_matrix_from_json(data)


def create_matrix_from_content(
    filepath: str,
    ai_call: Callable[[str], str],
    on_progress: Optional[Callable[[str], None]] = None,
) -> Optional[MatrixData]:
    """
    Tạo ma trận mới từ nội dung kiến thức trong file .docx / .pdf bằng AI.
    Dùng khi AI không nhận diện được cấu trúc ma trận sẵn có.

    Returns:
        MatrixData nếu thành công, None nếu thất bại
    """
    if on_progress:
        on_progress("Đang trích xuất nội dung tài liệu...")

    doc_text = extract_text_from_matrix_source(filepath)
    if not doc_text.strip():
        return None

    if len(doc_text) > 15000:
        doc_text = doc_text[:15000] + "\n... (nội dung đã được cắt bớt)"

    prompt = _CREATE_PROMPT.format(doc_text=doc_text)

    if on_progress:
        on_progress("AI đang tạo ma trận từ nội dung kiến thức...")

    raw_response = ai_call(prompt)

    if on_progress:
        on_progress("Đang xử lý kết quả...")

    data = _parse_ai_response(raw_response)
    result = _build_matrix_from_json(data)
    if result and not result.title.startswith("Ma trận"):
        result.title = f"{result.title} (AI tạo)"
    return result


# ══════════════════════════════════════════════════════════════════════════════
#  TẠO MA TRẬN TỪ MÔ TẢ (KHÔNG CẦN FILE)
# ══════════════════════════════════════════════════════════════════════════════

_GENERATE_MATRIX_PROMPT = """Bạn là chuyên gia biên soạn đề kiểm tra THCS/THPT Việt Nam.

Hãy TẠO MA TRẬN ĐỀ KIỂM TRA theo yêu cầu sau:

THÔNG TIN ĐỀ:
- Môn: {subject}
- Lớp: {grade}
- Thời lượng: {duration}
- Học kỳ: {semester}
{extra_requirements}

CẤU TRÚC THEO CHUẨN BỘ GIÁO DỤC:

Cấu trúc theo MÔN TOÁN:
  - TN: 50-70% (0.25đ/câu), DS: 10-20% (1.0đ/câu), TLN: 10-15% (0.5đ/câu), TL: 10-20% (1.0đ/câu)

Cấu trúc theo MÔN LÝ/HÓA/SINH (KHTN):
  - TN: 70-80% (0.25đ/câu), TL: 20-30% (1.0-2.0đ/câu)

Cấu trúc theo MÔN SỬ/ĐỊA/GDCD (KHXH):
  - TN: 70-80% (0.25đ/câu), TL: 20-30% (1.0-2.0đ/câu)

Cấu trúc theo MÔN NGỮ VĂN:
  - Đọc hiểu: TN + TLN (2-3đ)
  - Nghị luận xã hội: TL (2-3đ)
  - Nghị luận văn học: TL (4-5đ)

Cấu trúc theo MÔN TIẾNG ANH:
  - TN: 80-90% (0.25đ/câu), viết: TL (1.0-2.0đ/câu)

Cấu trúc MẶC ĐỊNH (các môn khác):
  - TN: 60-80% (0.25đ/câu), TL: 20-40% (1.0đ/câu)

PHÂN BỔ MỨC ĐỘ (chung):
  - Nhận biết (NB): ~30%
  - Thông hiểu (TH): ~30%
  - Vận dụng (VD): ~40%

Tổng điểm: 10.0

CHỦ ĐỀ PHÙ HỢP VỚI LỚP {grade} HỌC KỲ {semester}:
{topics_hint}

YÊU CẦU:
- Chủ đề phải PHÙ HỢP với lớp {grade}, học kỳ {semester}
- Mỗi row có requirement (yêu cầu cần đạt) cụ thể, chi tiết
- Phân bổ chủ đề đa dạng, không tập trung vào 1 chủ đề
- Tổng điểm = 10.0

TRẢ VỀ JSON duy nhất:
{{
  "title": "MA TRẬN ĐỀ KIỂM TRA {duration} — {subject} {grade}",
  "subject": "{subject}",
  "time_str": "{duration}",
  "rows": [
    {{
      "topic": "Tên chủ đề cụ thể",
      "qtype": "TN",
      "level": "NB",
      "count": 3,
      "points": 0.25,
      "requirement": "Yêu cầu cần đạt chi tiết"
    }}
  ]
}}

CHỈ trả về JSON, KHÔNG kèm giải thích.
"""


def generate_matrix_from_description(
    subject: str,
    grade: str,
    duration: str,
    semester: str,
    ai_call: Callable[[str], str],
    extra_requirements: str = "",
    on_progress: Optional[Callable[[str], None]] = None,
) -> Optional[MatrixData]:
    """
    Tạo ma trận đề bằng AI từ mô tả (không cần file).

    Args:
        subject: Tên môn học (Toán, Lý, Hóa, ...)
        grade: Lớp (10, 11, 12, ...)
        duration: Thời lượng (15 phút, 45 phút, 90 phút, ...)
        semester: Học kỳ (I, II)
        ai_call: Hàm gọi AI
        extra_requirements: Yêu cầu thêm từ user
        on_progress: Callback tiến trình

    Returns:
        MatrixData hoặc None
    """
    if on_progress:
        on_progress("Đang chuẩn bị prompt...")

    # Load topics hint từ chương trình học
    topics_hint = ""
    try:
        from core.quick_matrix import load_chuong_trinh
        data = load_chuong_trinh()
        grade_key = f"lop{grade}"
        if grade_key in data:
            topics = data[grade_key]
            if isinstance(topics, list):
                topics_hint = "\n".join(f"- {t}" for t in topics[:20])
            elif isinstance(topics, dict):
                for chapter, items in list(topics.items())[:10]:
                    if isinstance(items, list):
                        topics_hint += f"\n{chapter}: {', '.join(items[:5])}"
                    else:
                        topics_hint += f"\n- {chapter}"
    except Exception:
        pass

    if not topics_hint:
        topics_hint = "(Tự xác định chủ đề phù hợp với chương trình SGK hiện hành)"

    extra_block = ""
    if extra_requirements.strip():
        extra_block = f"- Yêu cầu thêm: {extra_requirements.strip()}"

    prompt = _GENERATE_MATRIX_PROMPT.format(
        subject=subject,
        grade=grade,
        duration=duration,
        semester=semester,
        extra_requirements=extra_block,
        topics_hint=topics_hint,
    )

    if on_progress:
        on_progress("Đang gọi AI tạo ma trận...")

    raw = ai_call(prompt)

    if on_progress:
        on_progress("Đang xử lý kết quả...")

    data = _parse_ai_response(raw)
    result = _build_matrix_from_json(data)
    return result
