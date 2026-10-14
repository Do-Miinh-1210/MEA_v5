"""
omr_exam/docx_parser.py — Phân tích đề thi từ file Word (.docx)
Bảo toàn MathType/OMML, công thức và cấu trúc đáp án.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from docx import Document
from omr_exam.models import ExamQuestion, OptionItem, ExamSection


def parse_exam_docx(docx_path: str) -> List[ExamSection]:
    """
    Đọc file Word đề thi và nhận diện:
    - Các phần (Phần I, Phần II, Phần tự luận...)
    - Từng câu hỏi (Câu 1, Câu 2... hoặc Bài 1...)
    - Các phương án A, B, C, D
    - Đáp án đúng (qua in đậm, gạch chân, hoặc bảng đáp án cuối bài)
    """
    doc = Document(docx_path)
    
    sections: List[ExamSection] = []
    current_section = ExamSection(title="Phần I: Trắc nghiệm")
    sections.append(current_section)
    
    # Gom các đoạn văn bản
    paragraphs = doc.paragraphs
    
    # 1. Kiểm tra xem có bảng đáp án ở cuối văn bản không (bảng đáp án dạng: 1.A 2.B 3.C...)
    answer_keys_from_text = _extract_answer_keys_from_tables_or_text(doc)
    
    current_q: Optional[ExamQuestion] = None
    q_index_counter = 1
    
    for para in paragraphs:
        text = _get_para_text(para).strip()
        if not text:
            continue
            
        # Dừng nhận diện nội dung câu hỏi khi gặp phần kết thúc đề thi ("HẾT", "ĐÁP ÁN", "LỜI GIẢI")
        if re.search(r"^(HẾT|HET)\b", text, re.I) or re.search(r"^(ĐÁP ÁN|DAP AN|LỜI GIẢI|HƯỚNG DẪN GIẢI|BẢNG ĐÁP ÁN)\b", text, re.I):
            if current_q:
                current_section.questions.append(current_q)
                current_q = None
            break

        # Kiểm tra tiêu đề Phần (hỗ trợ cả có dấu và không dấu)
        sec_match = re.match(r'^(PHẦN|Phần|PHAN|Phan|B\.\s*TỰ LUẬN|B\.\s*TU LUAN|A\.\s*TRẮC NGHIỆM|A\.\s*TRAC NGHIEM)\s*[IVXLCDM\d\.:\-–—]*(.*)', text, re.IGNORECASE)
        if sec_match:
            title = text
            if current_q:
                current_section.questions.append(current_q)
                current_q = None
            current_section = ExamSection(title=title)
            sections.append(current_section)
            continue
            
        # Kiểm tra bắt đầu câu hỏi: "Câu 1:", "Câu 1.", "Bài 1:", "Cau 1:", "Bai 1:"...
        q_match = re.match(r'^(Câu|Bài|Cau|Bai)\s*(\d+)[\s.:\-–—](.*)', text, re.IGNORECASE)
        if q_match:
            # Lưu câu trước đó nếu có
            if current_q:
                current_section.questions.append(current_q)
                
            q_num = int(q_match.group(2))
            rest_text = q_match.group(3).strip()
            
            is_tl = any(kw in current_section.title.lower() for kw in ("tự luận", "tu luan")) or q_match.group(1).lower() in ("bài", "bai")
            current_q = ExamQuestion(
                index=q_num,
                section=current_section.title,
                qtype="TL" if is_tl else "TN",
                content=rest_text,
                options=[],
                correct_label="",
                tl_min_lines=4 if is_tl else 0
            )
            q_index_counter += 1
            
            # Kiểm tra xem ngay trong đoạn câu hỏi có chứa đáp án A/B/C/D không
            _parse_options_in_paragraph(para, current_q)
            continue
            
        # Nếu đang trong 1 câu hỏi, kiểm tra xem đoạn này có chứa các phương án A/B/C/D không
        if current_q and current_q.qtype == "TN":
            has_options = _parse_options_in_paragraph(para, current_q)
            if not has_options:
                # Nếu không phải đáp án thì là dòng nội dung tiếp theo của câu hỏi
                if not current_q.options:
                    current_q.content += "\n" + text
                else:
                    # Hoặc là nội dung bổ trợ
                    pass
        elif current_q and current_q.qtype == "TL":
            # Câu tự luận: cộng dồn nội dung
            current_q.content += "\n" + text
            
    # Lưu câu hỏi cuối cùng
    if current_q:
        current_section.questions.append(current_q)
        
    # Gán đáp án đúng từ bảng đáp án nếu có (ưu tiên số 1)
    for sec in sections:
        for q in sec.questions:
            if q.index in answer_keys_from_text:
                q.correct_label = answer_keys_from_text[q.index]
                for opt in q.options:
                    opt.is_correct = (opt.label == q.correct_label)
                        
    # Lọc bỏ các section rỗng
    sections = [s for s in sections if s.questions]
    return sections


def _get_para_text(para) -> str:
    """Lấy nội dung đoạn văn bản kèm công thức toán LaTeX ${...}$."""
    try:
        from export.math_converter import extract_para_text_with_math
        t = extract_para_text_with_math(para)
        if t:
            return t
    except Exception:
        pass
    return para.text.strip()


def _split_options_safely(text: str) -> Dict[str, str]:
    """Tìm các phương án A, B, C, D không bị nhầm lẫn với ký hiệu bên trong ${...}$."""
    math_spans = []
    i = 0
    while i < len(text):
        if text[i] == '$':
            j = text.find('$', i + 1)
            if j != -1:
                math_spans.append((i, j + 1))
                i = j + 1
            else:
                break
        else:
            i += 1

    def is_inside_math(idx: int) -> bool:
        return any(start <= idx < end for start, end in math_spans)

    expected_labels = ['A', 'B', 'C', 'D']
    pattern = re.compile(r'(?:^|[\t\n\r\s])([A-D])[\.\)]\s*')

    matches = []
    exp_idx = 0
    for m in pattern.finditer(text):
        lbl = m.group(1).upper()
        label_idx = m.start(1)
        if is_inside_math(label_idx):
            continue
        if exp_idx < len(expected_labels) and lbl == expected_labels[exp_idx]:
            matches.append((label_idx, lbl, m.end()))
            exp_idx += 1

    if not matches:
        return {}

    opts = {}
    for idx, (l_start, lbl, content_start) in enumerate(matches):
        next_start = matches[idx + 1][0] if idx + 1 < len(matches) else len(text)
        opts[lbl] = text[content_start:next_start].strip()
    return opts


def _parse_options_in_paragraph(para, q: ExamQuestion) -> bool:
    """Tìm các phương án A., B., C., D. trong một đoạn văn bản."""
    text = _get_para_text(para)
    opts_map = _split_options_safely(text)

    if not opts_map:
        return False

    for label, opt_text in opts_map.items():
        # Chỉ kiểm tra gạch chân (underline) vì nhãn A/B/C/D thường mặc định in đậm
        is_correct = False
        for run in para.runs:
            if label in run.text and run.font.underline:
                is_correct = True
                break

        # Thêm vào danh sách phương án
        existing = [opt for opt in q.options if opt.label == label]
        if not existing:
            opt_item = OptionItem(label=label, text=opt_text, is_correct=is_correct)
            q.options.append(opt_item)
            if is_correct:
                q.correct_label = label

    return True


def _extract_answer_keys_from_tables_or_text(doc: Document) -> Dict[int, str]:
    """Tìm bảng đáp án dạng: 1.A, 2.B hoặc bảng table ở cuối file Word."""
    keys: Dict[int, str] = {}
    
    # 1. Quét qua các bảng trong Word
    for table in doc.tables:
        rows = table.rows
        # 1a. Bảng 2 hàng: hàng trên số câu, hàng dưới đáp án
        for r_idx in range(len(rows) - 1):
            cells_top = [c.text.strip() for c in rows[r_idx].cells]
            cells_bot = [c.text.strip() for c in rows[r_idx + 1].cells]
            for c1, c2 in zip(cells_top, cells_bot):
                if c1.isdigit() and c2.upper() in ("A", "B", "C", "D"):
                    keys[int(c1)] = c2.upper()
                    
        # 1b. Bảng các cặp ô liền kề (ô i là số, ô i+1 là chữ)
        for row in rows:
            cells = [c.text.strip() for c in row.cells]
            for i in range(len(cells) - 1):
                if cells[i].isdigit() and cells[i+1].upper() in ("A", "B", "C", "D"):
                    keys[int(cells[i])] = cells[i+1].upper()
                    
    # 2. Quét qua text: 'Chọn C.', 'Đáp án: B', 'Đ/A: A'
    cur_q = None
    for para in doc.paragraphs:
        txt = para.text.strip()
        m_q = re.match(r"^(Câu|Bài)\s*(\d+)", txt, re.I)
        if m_q:
            cur_q = int(m_q.group(2))
        m_ans = re.search(r"(?:Chọn|Đáp án|Đ/A)\s*([A-D])\b", txt, re.I)
        if m_ans and cur_q:
            if cur_q not in keys:
                keys[cur_q] = m_ans.group(1).upper()
                
    # 3. Quét qua text dạng: 1.A, 2.B, 3.C
    for para in doc.paragraphs:
        txt = para.text.strip()
        matches = re.findall(r"\b(\d+)[\.\s:\-–]+([A-D])\b", txt, re.IGNORECASE)
        for q_str, ans_str in matches:
            q_num = int(q_str)
            if q_num not in keys and 1 <= q_num <= 100:
                keys[q_num] = ans_str.upper()
            
    return keys
