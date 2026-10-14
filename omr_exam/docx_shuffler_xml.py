"""
omr_exam/docx_shuffler_xml.py — Trộn đề thi trực tiếp ở cấp độ OpenXML của file Word (.docx).
Bảo toàn 100%:
- Công thức MathType (OLE objects <w:object>, oleObject*.bin)
- Công thức OMML (<m:oMath>, <m:oMathPara>)
- Hình ảnh, sơ đồ, bảng biểu (<w:drawing>, <w:tbl>)
- Định dạng font, cỡ chữ, căn lề, tab stops (<w:pPr>, <w:rPr>)
- Thêm dòng kẻ chấm chấm cho câu tự luận (+2 dòng theo cấu trúc)
- Hỗ trợ 3 chế độ trộn, tự động ghim đáp án phụ thuộc ("Tất cả...", "Cả A và B..."), ghim câu hỏi.
- Xuất file Word từng mã đề, File Word GỘP tất cả mã đề, Bảng đáp án Word và Bảng đáp án + Ma trận hoán vị Excel (.xlsx).
"""
from __future__ import annotations
import os
import copy
import re
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set, Any
import docx
from lxml import etree

from omr_exam.exam_shuffler import is_dependent_option_text, _shuffle_with_pinned
from omr_exam.excel_exporter import export_exam_keys_and_matrix_to_excel

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def make_label_run(label: str, base_rPr: Optional[etree.Element] = None) -> etree.Element:
    """Tạo XML run <w:r> cho nhãn đáp án 'A. ', 'B. ' (in đậm, font Times New Roman hoặc kế thừa base_rPr)."""
    r = etree.Element(f"{{{W_NS}}}r")
    rPr = copy.deepcopy(base_rPr) if base_rPr is not None else etree.Element(f"{{{W_NS}}}rPr")
    if rPr.find(f"{{{W_NS}}}b") is None:
        etree.SubElement(rPr, f"{{{W_NS}}}b")
    i_elem = rPr.find(f"{{{W_NS}}}i")
    if i_elem is not None:
        rPr.remove(i_elem)
    if rPr.find(f"{{{W_NS}}}rFonts") is None:
        rFonts = etree.SubElement(rPr, f"{{{W_NS}}}rFonts")
        rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
        rFonts.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
    r.append(rPr)
    t = etree.SubElement(r, f"{{{W_NS}}}t")
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = f"{label}. "
    return r


def make_stem_label_run(prefix: str, q_num: int, sep: str = ".", base_rPr: Optional[etree.Element] = None) -> etree.Element:
    """Tạo XML run <w:r> cho tiền tố câu hỏi (VD: 'Câu 1. ' hoặc 'Câu 1: ')."""
    r = etree.Element(f"{{{W_NS}}}r")
    rPr = copy.deepcopy(base_rPr) if base_rPr is not None else etree.Element(f"{{{W_NS}}}rPr")
    if rPr.find(f"{{{W_NS}}}b") is None:
        etree.SubElement(rPr, f"{{{W_NS}}}b")
    i_elem = rPr.find(f"{{{W_NS}}}i")
    if i_elem is not None:
        rPr.remove(i_elem)
    if rPr.find(f"{{{W_NS}}}rFonts") is None:
        rFonts = etree.SubElement(rPr, f"{{{W_NS}}}rFonts")
        rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
        rFonts.set(f"{{{W_NS}}}hAnsi", "Times New Roman")
    r.append(rPr)
    t = etree.SubElement(r, f"{{{W_NS}}}t")
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    t.text = f"{prefix} {q_num}{sep} "
    return r


def make_text_runs_xml(
    text: str,
    base_rPr: Optional[etree.Element] = None,
    default_bold: bool = False,
    default_italic: bool = False,
) -> List[etree.Element]:
    """Tạo danh sách các thẻ <w:r> từ text chuỗi.
    Bảo toàn công thức toán dạng $...$ với chữ nghiêng (<w:i/>),
    TUYỆT ĐỐI KHÔNG tạo Word Equation (<m:oMath>) để tương thích 100% với MathType (Toggle TeX / Alt+\).
    Kế thừa font và kích thước từ base_rPr nếu có.
    """
    runs = []
    try:
        from export.math_converter import split_text_and_math
        parts = split_text_and_math(text) if "$" in text else [(False, text)]
    except Exception:
        parts = [(False, text)]

    for is_math, chunk in parts:
        if not chunk and not is_math:
            continue
        r = etree.Element(f"{{{W_NS}}}r")
        rPr = copy.deepcopy(base_rPr) if base_rPr is not None else etree.Element(f"{{{W_NS}}}rPr")

        if rPr.find(f"{{{W_NS}}}rFonts") is None:
            rFonts = etree.SubElement(rPr, f"{{{W_NS}}}rFonts")
            rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
            rFonts.set(f"{{{W_NS}}}hAnsi", "Times New Roman")

        if default_bold and rPr.find(f"{{{W_NS}}}b") is None:
            etree.SubElement(rPr, f"{{{W_NS}}}b")

        if is_math:
            if rPr.find(f"{{{W_NS}}}i") is None:
                etree.SubElement(rPr, f"{{{W_NS}}}i")
            math_text = f"${chunk}$" if not (chunk.startswith("$") and chunk.endswith("$")) else chunk
            t = etree.SubElement(r, f"{{{W_NS}}}t")
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            t.text = math_text
        else:
            if default_italic and rPr.find(f"{{{W_NS}}}i") is None:
                etree.SubElement(rPr, f"{{{W_NS}}}i")
            t = etree.SubElement(r, f"{{{W_NS}}}t")
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            t.text = chunk

        r.insert(0, rPr)
        runs.append(r)
    return runs


def make_tab_run() -> etree.Element:
    """Tạo XML run <w:r><w:tab/></w:r>."""
    r = etree.Element(f"{{{W_NS}}}r")
    etree.SubElement(r, f"{{{W_NS}}}tab")
    return r


def make_page_break_p() -> etree.Element:
    """Tạo đoạn ngắt trang <w:p><w:r><w:br w:type='page'/></w:r></w:p>."""
    p = etree.Element(f"{{{W_NS}}}p")
    r = etree.SubElement(p, f"{{{W_NS}}}r")
    br = etree.SubElement(r, f"{{{W_NS}}}br")
    br.set(f"{{{W_NS}}}type", "page")
    return p


def make_dotted_line_p() -> etree.Element:
    """Tạo 1 dòng kẻ chấm chấm để học sinh viết bài tự luận."""
    p = etree.Element(f"{{{W_NS}}}p")
    pPr = etree.SubElement(p, f"{{{W_NS}}}pPr")
    spacing = etree.SubElement(pPr, f"{{{W_NS}}}spacing")
    spacing.set(f"{{{W_NS}}}after", "40")
    
    r = etree.SubElement(p, f"{{{W_NS}}}r")
    rPr = etree.SubElement(r, f"{{{W_NS}}}rPr")
    color = etree.SubElement(rPr, f"{{{W_NS}}}color")
    color.set(f"{{{W_NS}}}val", "999999")
    rFonts = etree.SubElement(rPr, f"{{{W_NS}}}rFonts")
    rFonts.set(f"{{{W_NS}}}ascii", "Times New Roman")
    
    t = etree.SubElement(r, f"{{{W_NS}}}t")
    t.text = ". . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . ."
    return p


def extract_answer_keys(doc: docx.Document) -> Dict[int, str]:
    """Trích xuất đáp án từ bảng đáp án hoặc văn bản giải/đáp án ở cuối đề thi."""
    keys: Dict[int, str] = {}
    
    # 1. Bảng đáp án nhiều hàng (hàng số câu + hàng đáp án)
    for table in doc.tables:
        rows = table.rows
        for r_idx in range(len(rows) - 1):
            cells_top = [c.text.strip() for c in rows[r_idx].cells]
            cells_bot = [c.text.strip() for c in rows[r_idx + 1].cells]
            for c1, c2 in zip(cells_top, cells_bot):
                if c1.isdigit() and c2.upper() in ("A", "B", "C", "D"):
                    keys[int(c1)] = c2.upper()
                    
    # 2. Text lời giải / đáp án: "Chọn C.", "Đáp án: B", "Đ/A: A"
    cur_q = None
    for p in doc.paragraphs:
        txt = p.text.strip()
        m_q = re.match(r"^(Câu|Bài)\s*(\d+)", txt, re.I)
        if m_q:
            cur_q = int(m_q.group(2))
        m_ans = re.search(r"(?:Chọn|Đáp án|Đ/A)\s*([A-D])\b", txt, re.I)
        if m_ans and cur_q:
            if cur_q not in keys:
                keys[cur_q] = m_ans.group(1).upper()
                
    # 3. Dạng 1.A, 2.B, 3.C
    for p in doc.paragraphs:
        txt = p.text.strip()
        matches = re.findall(r"\b(\d+)[\.\s:\-–]+([A-D])\b", txt, re.I)
        for q_s, a_s in matches:
            q_num = int(q_s)
            if q_num not in keys and 1 <= q_num <= 100:
                keys[q_num] = a_s.upper()
                
    return keys


class XMLQuestion:
    """Đại diện cho 1 câu hỏi ở cấp độ XML nguyên bản."""
    def __init__(self, original_index: int, qtype: str = "TN"):
        self.original_index = original_index
        self.index = original_index
        self.qtype = qtype
        self.stem_elements: List[etree.Element] = []
        self.option_elements: List[etree.Element] = []
        self.option_runs: Dict[str, List[etree.Element]] = {"A": [], "B": [], "C": [], "D": []}
        self.option_layout: str = "1_para" # "1_para", "2_para", "4_para"
        self.option_pPrs: List[Optional[etree.Element]] = []
        self.correct_key: str = ""
        self.tl_min_lines: int = 4

    def parse_options(self):
        """Phân tích các đoạn đáp án thành từng phương án A, B, C, D (giữ trọn XML runs)."""
        if self.qtype != "TN" or not self.option_elements:
            return
            
        current_label = None
        for p in self.option_elements:
            pPr = p.find(f"{{{W_NS}}}pPr")
            self.option_pPrs.append(copy.deepcopy(pPr) if pPr is not None else None)
            
            for child in list(p):
                tag = child.tag.split("}")[-1]
                if tag == "pPr":
                    continue
                # Lấy text trong các thẻ w:t của child
                txt = "".join(t.text or "" for t in child.findall(f".//{{{W_NS}}}t")).strip()
                m = re.match(r"^([A-D])[\.\)]\s*(.*)", txt)
                if m:
                    current_label = m.group(1).upper()
                    rem = m.group(2).strip()
                    if rem:
                        r_clone = copy.deepcopy(child)
                        for t_elem in r_clone.findall(f".//{{{W_NS}}}t"):
                            t_elem.text = rem
                            break
                        self.option_runs[current_label].append(r_clone)
                elif current_label:
                    is_tab = (tag == "r" and ("\t" in txt or child.find(f"{{{W_NS}}}tab") is not None))
                    if not is_tab:
                        self.option_runs[current_label].append(copy.deepcopy(child))
                        
        n_paras = len(self.option_elements)
        if n_paras == 1:
            self.option_layout = "1_para"
        elif n_paras == 2:
            self.option_layout = "2_para"
        else:
            self.option_layout = "4_para"

    def get_option_plain_text(self, label: str) -> str:
        """Lấy text thuần túy của phương án để kiểm tra nội dung."""
        runs = self.option_runs.get(label, [])
        texts = []
        for r in runs:
            for t in r.findall(f".//{{{W_NS}}}t"):
                if t.text:
                    texts.append(t.text)
        return " ".join(texts).strip()

    def find_dependent_option(self) -> Optional[str]:
        """Tìm phương án phụ thuộc ('Tất cả...', 'Cả A và B...'). Trả về 'A', 'B', 'C', 'D' nếu có."""
        for lbl in ["A", "B", "C", "D"]:
            txt = self.get_option_plain_text(lbl)
            if is_dependent_option_text(txt):
                return lbl
        return None


class XMLSection:
    """Đại diện cho 1 phần thi (Phần I, Phần II, Tự luận...)."""
    def __init__(self, title_element: Optional[etree.Element] = None, title_text: str = ""):
        self.title_element = title_element
        self.title_text = title_text
        self.questions: List[XMLQuestion] = []


def parse_docx_xml_structure(docx_path: str) -> Tuple[List[etree.Element], List[XMLSection], List[etree.Element], Dict[int, str]]:
    """Phân tích tài liệu Word thành Header, Các Phần, Kết thúc và Bảng đáp án."""
    doc = docx.Document(docx_path)
    body = doc._body._body
    
    answer_keys = extract_answer_keys(doc)
    
    headers: List[etree.Element] = []
    sections: List[XMLSection] = []
    current_section: Optional[XMLSection] = None
    footers: List[etree.Element] = []
    
    current_q: Optional[XMLQuestion] = None
    in_test_content = False
    in_post_test = False
    
    for el in list(body):
        tag = el.tag.split("}")[-1]
        if tag == "sectPr":
            continue
            
        txt = "".join(t.text or "" for t in el.findall(f".//{{{W_NS}}}t")).strip()
        
        # Kiểm tra phần kết thúc đề thi ("HẾT", "HET", "ĐÁP ÁN", "LỜI GIẢI")
        if re.search(r"^(HẾT|HET)\b", txt, re.I) or re.search(r"^(ĐÁP ÁN|DAP AN|LỜI GIẢI)\b", txt, re.I):
            in_post_test = True
            if current_q:
                current_q.parse_options()
                if current_section:
                    current_section.questions.append(current_q)
                current_q = None
            if re.search(r"^(HẾT|HET)\b", txt, re.I):
                footers.append(el)
            continue
            
        if in_post_test:
            continue
            
        # Kiểm tra tiêu đề Phần
        sec_m = re.match(r"^(PHẦN|Phần|PHAN|Phan|B\.\s*TỰ LUẬN|B\.\s*TU LUAN|A\.\s*TRẮC NGHIỆM|A\.\s*TRAC NGHIEM)\s*([IVXLCDM\d\.:\-–—]*.*)", txt, re.I)
        if sec_m:
            in_test_content = True
            if current_q:
                current_q.parse_options()
                if current_section:
                    current_section.questions.append(current_q)
                current_q = None
            current_section = XMLSection(title_element=el, title_text=txt)
            sections.append(current_section)
            continue
            
        # Kiểm tra bắt đầu câu hỏi: "Câu 1.", "Câu 1:", "Bài 1."
        q_m = re.match(r"^(Câu|Bài|Cau|Bai)\s*(\d+)[\.\:]\s*(.*)", txt, re.I)
        if q_m:
            in_test_content = True
            if current_q:
                current_q.parse_options()
                if current_section:
                    current_section.questions.append(current_q)
                    
            if not current_section:
                current_section = XMLSection(title_text="Phần I: Trắc nghiệm")
                sections.append(current_section)
                
            q_num = int(q_m.group(2))
            is_tl = any(kw in current_section.title_text.lower() for kw in ("tự luận", "tu luan", "phần iv", "phan iv")) or q_m.group(1).lower() in ("bài", "bai")
            
            current_q = XMLQuestion(original_index=q_num, qtype="TL" if is_tl else "TN")
            current_q.correct_key = answer_keys.get(q_num, "")
            current_q.stem_elements.append(el)
            continue
            
        if not in_test_content:
            headers.append(el)
        else:
            if current_q:
                # Kiểm tra nếu đoạn này chứa lựa chọn đáp án A/B/C/D
                has_opt = bool(re.search(r"\b[A-D][\.\)]", txt))
                if has_opt and current_q.qtype == "TN":
                    current_q.option_elements.append(el)
                else:
                    if not current_q.option_elements:
                        current_q.stem_elements.append(el)
                        
    if current_q:
        current_q.parse_options()
        if current_section:
            current_section.questions.append(current_q)
            
    return headers, sections, footers, answer_keys


def shuffle_docx_with_full_xml_preservation(
    source_docx_path: str,
    output_dir: str,
    num_codes: int = 4,
    start_code: int = 101,
    custom_codes: Optional[List[str]] = None,
    shuffle_mode: str = "both",  # "both", "questions_only", "options_only"
    auto_pin_dependent_options: bool = True,
    pinned_question_indices: Optional[Set[int]] = None,
    export_merged_docx: bool = True,
    shuffled_exams: Optional[List[Any]] = None,
    is_ai_variant: bool = False,
) -> Tuple[List[str], Dict[str, Dict[int, str]], str, str, Dict[str, Dict[int, int]], Dict[str, Dict[int, Dict[str, str]]]]:
    """
    Trộn đề thi bảo toàn 100% MathType/OMML/Hình ảnh bằng cách tái sử dụng gói OpenXML gốc.
    
    Hỗ trợ:
    - Giữ 100% cấu trúc file Word gốc (Header trường/lớp/SBD/thời gian, lề trang, font, bảng biểu, sectPr).
    - Hỗ trợ đổi số liệu bằng AI: chỉ đổi số và đáp án trực tiếp trong tài liệu có sẵn, không tự tạo cấu trúc Word mới.
    - Công thức toán bảo toàn dạng MathType ($...$), tuyệt đối KHÔNG tự chuyển sang Equation (<m:oMath>).
    - 3 Chế độ trộn ('both', 'questions_only', 'options_only').
    - Smart Fixed Options: Tự động phát hiện và ghim phương án phụ thuộc ("Tất cả...", "Cả A và B...") ở vị trí D.
    - Ghim câu hỏi chỉ định qua pinned_question_indices.
    - Xuất từng file Word riêng + File Word gộp All-in-One.
    - Xuất Bảng đáp án Word (.docx) và Bảng đáp án + Ma trận hoán vị Excel (.xlsx).
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    headers, sections, footers, orig_keys = parse_docx_xml_structure(source_docx_path)
    
    generated_files: List[str] = []
    keys_by_code: Dict[str, Dict[int, str]] = {}
    question_map_by_code: Dict[str, Dict[int, int]] = {}
    option_map_by_code: Dict[str, Dict[int, Dict[str, str]]] = {}
    
    pinned_set = set(pinned_question_indices or [])
    
    if custom_codes and len(custom_codes) > 0:
        codes = [str(c).strip() for c in custom_codes if str(c).strip()]
    else:
        codes = [str(start_code + i) for i in range(num_codes)]
        
    labels = ["A", "B", "C", "D"]

    # Nhận diện chế độ AI đổi số liệu (giữ 100% cấu trúc Word gốc, chỉ đổi số liệu và đáp án)
    is_ai_mode = is_ai_variant or any(
        getattr(q, "_variant", False) or getattr(ex, "is_ai_variant", False)
        for ex in (shuffled_exams or [])
        for s in getattr(ex, "sections", [])
        for q in getattr(s, "questions", [])
    )
    
    # Chuẩn bị file gộp nếu được yêu cầu
    merged_doc = None
    merged_body = None
    if export_merged_docx:
        merged_doc = docx.Document(source_docx_path)
        merged_body = merged_doc._body._body
        merged_body.clear()
        
    master_sectPr = None

    for code_idx, code_str in enumerate(codes):
        digits = re.sub(r"\D", "", code_str)
        code_seed = int(digits) if digits else (abs(hash(code_str)) % 100000)
        rng = random.Random(code_seed)
        
        doc = docx.Document(source_docx_path)
        body = doc._body._body
        
        sectPr = None
        for el in list(body):
            if el.tag.split("}")[-1] == "sectPr":
                sectPr = copy.deepcopy(el)
                if master_sectPr is None:
                    master_sectPr = copy.deepcopy(el)
                break
                
        body.clear()
        
        # 1. Chèn lại Headers & cập nhật Mã đề thi (giữ 100% cấu trúc, chỉ cập nhật mã đề)
        code_headers = []
        for h in headers:
            h_clone = copy.deepcopy(h)
            for p in h_clone.iter(f"{{{W_NS}}}p"):
                p_txt = "".join(t.text or "" for t in p.findall(f".//{{{W_NS}}}t"))
                if re.search(r"Mã đề(\s+thi)?", p_txt, re.I):
                    replaced = False
                    for t in p.findall(f".//{{{W_NS}}}t"):
                        if re.search(r"Mã đề(\s+thi)?\s*[:\s]*[\w\.\…–—]*", t.text or "", re.I):
                            t.text = re.sub(
                                r"Mã đề(\s+thi)?\s*[:\s]*[\w\.\…–—]*",
                                lambda m: f"Mã đề{m.group(1) or ''}: {code_str}",
                                t.text,
                                flags=re.I
                            )
                            replaced = True
                            break
                    if not replaced:
                        found_lbl = False
                        for t in p.findall(f".//{{{W_NS}}}t"):
                            if re.search(r"Mã đề(\s+thi)?", t.text or "", re.I):
                                t.text = re.sub(r"(Mã đề(\s+thi)?\s*[:\s]*).*", lambda m: f"{m.group(1)}{code_str}", t.text, flags=re.I)
                                found_lbl = True
                            elif found_lbl and t.text and re.match(r"^[\s\.\…–—\d]+$", t.text):
                                t.text = ""
            body.append(h_clone)
            code_headers.append(h_clone)
            
        shuffled_keys: Dict[int, str] = {}
        q_map_code: Dict[int, int] = {}
        opt_map_code: Dict[int, Dict[str, str]] = {}
        global_q_counter = 1
        
        code_body_elements: List[etree.Element] = []

        # Tìm exam object tương ứng cho mã đề này
        matched_exam = None
        if shuffled_exams:
            matched_exam = next((ex for ex in shuffled_exams if str(getattr(ex, "code", "")) == code_str), None)
            if matched_exam is None and code_idx < len(shuffled_exams):
                matched_exam = shuffled_exams[code_idx]
        
        # 2. Xử lý từng phần (Section)
        for sec_idx, sec in enumerate(sections):
            if sec.title_element is not None:
                body.append(copy.deepcopy(sec.title_element))
                code_body_elements.append(copy.deepcopy(sec.title_element))

            # Tìm section tương ứng trong matched_exam nếu có
            matched_sec = None
            if matched_exam and getattr(matched_exam, "sections", None):
                if sec_idx < len(matched_exam.sections):
                    matched_sec = matched_exam.sections[sec_idx]
                else:
                    matched_sec = next((s for s in matched_exam.sections if getattr(s, "title", "") == sec.title_text), None)

            if is_ai_mode and matched_sec:
                # ─── NHÁNH ĐỔI SỐ LIỆU BẰNG AI: GIỮ NGUYÊN CẤU TRÚC GỐC, CHỈ ĐỔI SỐ VÀ ĐÁP ÁN ───
                first_q_in_sec_is_1 = (len(sec.questions) > 0 and sec.questions[0].original_index == 1)
                for q_idx, q_ai in enumerate(matched_sec.questions):
                    cur_q_num = (q_idx + 1) if first_q_in_sec_is_1 else global_q_counter
                    global_q_counter += 1
                    orig_q_num = getattr(q_ai, "index", q_idx + 1)
                    q_map_code[cur_q_num] = orig_q_num

                    # Tìm XMLQuestion gốc tương ứng để tái sử dụng định dạng layout & styling (<w:pPr>, <w:rPr>)
                    orig_xq = next((xq for xq in sec.questions if xq.index == orig_q_num), None)
                    if orig_xq is None and q_idx < len(sec.questions):
                        orig_xq = sec.questions[q_idx]

                    orig_stem_p = orig_xq.stem_elements[0] if (orig_xq and orig_xq.stem_elements) else None
                    base_rPr = None
                    if orig_stem_p is not None:
                        first_r = orig_stem_p.find(f".//{{{W_NS}}}r")
                        if first_r is not None:
                            first_rPr = first_r.find(f"{{{W_NS}}}rPr")
                            if first_rPr is not None:
                                base_rPr = copy.deepcopy(first_rPr)

                    prefix = "Câu"
                    sep = "."
                    if orig_stem_p is not None:
                        orig_t = "".join(t.text or "" for t in orig_stem_p.findall(f".//{{{W_NS}}}t"))
                        m_pfx = re.match(r"^(Câu|Bài|Cau|Bai)\s*\d+([\.\:])", orig_t, re.I)
                        if m_pfx:
                            prefix = m_pfx.group(1)
                            sep = m_pfx.group(2)

                    # 2a. Tạo Stem câu hỏi: Giữ nguyên 100% <w:pPr> của câu gốc
                    p_stem = copy.deepcopy(orig_stem_p) if orig_stem_p is not None else etree.Element(f"{{{W_NS}}}p")
                    for child in list(p_stem):
                        if child.tag.split("}")[-1] != "pPr":
                            p_stem.remove(child)

                    p_stem.append(make_stem_label_run(prefix, cur_q_num, sep, base_rPr))
                    clean_stem = re.sub(r"^(Câu|Bài|Cau|Bai)\s*\d+[\.\:]\s*", "", getattr(q_ai, "content", "").strip(), flags=re.I)
                    content_runs = make_text_runs_xml(clean_stem, base_rPr=base_rPr)
                    for r in content_runs:
                        p_stem.append(r)

                    body.append(p_stem)
                    code_body_elements.append(p_stem)

                    # Nếu câu gốc có thêm hình ảnh / bảng trong stem (các stem_element phía sau), giữ nguyên
                    if orig_xq and len(orig_xq.stem_elements) > 1:
                        for add_el in orig_xq.stem_elements[1:]:
                            body.append(copy.deepcopy(add_el))
                            code_body_elements.append(copy.deepcopy(add_el))

                    # 2b. Xử lý Phương án trắc nghiệm A, B, C, D
                    ai_options = getattr(q_ai, "options", [])
                    if ai_options and (getattr(q_ai, "qtype", "TN") == "TN" or (orig_xq and orig_xq.qtype == "TN")):
                        opts_map = {opt.label.upper(): opt.text for opt in ai_options}
                        opt_runs = {}
                        for lbl in labels:
                            raw_txt = opts_map.get(lbl, "")
                            clean_opt = re.sub(r"^[A-D][\.\:\)]\s*", "", raw_txt.strip(), flags=re.I)
                            opt_runs[lbl] = make_text_runs_xml(clean_opt, base_rPr=base_rPr)

                        layout = orig_xq.option_layout if orig_xq else "1_para"
                        opt_elements = orig_xq.option_elements if orig_xq else []
                        opt_paras_created = []

                        if layout == "1_para" and opt_elements:
                            p = copy.deepcopy(opt_elements[0])
                            for child in list(p):
                                if child.tag.split("}")[-1] != "pPr":
                                    p.remove(child)
                            for i_lbl, lbl in enumerate(labels):
                                p.append(make_label_run(lbl, base_rPr))
                                for r in opt_runs[lbl]:
                                    p.append(copy.deepcopy(r))
                                if i_lbl < 3:
                                    p.append(make_tab_run())
                            body.append(p)
                            opt_paras_created.append(p)
                        elif layout == "2_para" and len(opt_elements) >= 2:
                            p1 = copy.deepcopy(opt_elements[0])
                            for child in list(p1):
                                if child.tag.split("}")[-1] != "pPr":
                                    p1.remove(child)
                            p1.append(make_label_run("A", base_rPr))
                            for r in opt_runs["A"]: p1.append(copy.deepcopy(r))
                            p1.append(make_tab_run())
                            p1.append(make_label_run("B", base_rPr))
                            for r in opt_runs["B"]: p1.append(copy.deepcopy(r))
                            body.append(p1)
                            opt_paras_created.append(p1)

                            p2 = copy.deepcopy(opt_elements[1])
                            for child in list(p2):
                                if child.tag.split("}")[-1] != "pPr":
                                    p2.remove(child)
                            p2.append(make_label_run("C", base_rPr))
                            for r in opt_runs["C"]: p2.append(copy.deepcopy(r))
                            p2.append(make_tab_run())
                            p2.append(make_label_run("D", base_rPr))
                            for r in opt_runs["D"]: p2.append(copy.deepcopy(r))
                            body.append(p2)
                            opt_paras_created.append(p2)
                        else:
                            base_p = opt_elements[0] if opt_elements else etree.Element(f"{{{W_NS}}}p")
                            for idx, lbl in enumerate(labels):
                                p = copy.deepcopy(opt_elements[idx] if idx < len(opt_elements) else base_p)
                                for child in list(p):
                                    if child.tag.split("}")[-1] != "pPr":
                                        p.remove(child)
                                p.append(make_label_run(lbl, base_rPr))
                                for r in opt_runs[lbl]:
                                    p.append(copy.deepcopy(r))
                                body.append(p)
                                opt_paras_created.append(p)
                        code_body_elements.extend(opt_paras_created)

                        # Cập nhật đáp án đúng
                        ans_label = getattr(q_ai, "correct_label", "")
                        if matched_exam and matched_exam.answer_key and cur_q_num in matched_exam.answer_key:
                            ans_label = matched_exam.answer_key[cur_q_num]
                        shuffled_keys[cur_q_num] = ans_label
                        if matched_exam and matched_exam.option_map and cur_q_num in matched_exam.option_map:
                            opt_map_code[cur_q_num] = matched_exam.option_map[cur_q_num]
                    elif getattr(q_ai, "qtype", "") == "TL" or (orig_xq and orig_xq.qtype == "TL"):
                        lines_needed = max(getattr(q_ai, "tl_min_lines", 3), 4) + 2
                        for _ in range(lines_needed):
                            dot_p = make_dotted_line_p()
                            body.append(dot_p)
                            code_body_elements.append(dot_p)
                    else:
                        if orig_xq and len(orig_xq.stem_elements) > 1:
                            for add_p in orig_xq.stem_elements[1:]:
                                body.append(copy.deepcopy(add_p))
                                code_body_elements.append(copy.deepcopy(add_p))
            else:
                # ─── NHÁNH TRỘN ĐỀ THÔNG THƯỜNG (BẢO TOÀN NGUYÊN BẢN XML BINARY CỦA MATHTYPE/OMML) ───
                if shuffle_mode in ("both", "questions_only"):
                    shuffled_qs = _shuffle_with_pinned(list(sec.questions), pinned_set, rng)
                else:
                    shuffled_qs = list(sec.questions)

                for q in shuffled_qs:
                    cur_q_num = global_q_counter
                    orig_q_num = q.original_index
                    global_q_counter += 1
                    q_map_code[cur_q_num] = orig_q_num

                    # 2a. Thêm nội dung câu hỏi (Stem), đổi nhãn thành Câu {cur_q_num}.
                    for s_idx, stem in enumerate(q.stem_elements):
                        s_clone = copy.deepcopy(stem)
                        if s_idx == 0:
                            for t in s_clone.findall(f".//{{{W_NS}}}t"):
                                txt = t.text or ""
                                m_num = re.match(r"^(Câu|Bài|Cau|Bai)\s*(\d+)[\.\:]\s*(.*)", txt, re.I)
                                if m_num:
                                    prefix = m_num.group(1)
                                    rem = m_num.group(3)
                                    t.text = f"{prefix} {cur_q_num}. {rem}"
                                    break
                        body.append(s_clone)
                        code_body_elements.append(s_clone)

                    # 2b. Xử lý phương án trắc nghiệm A, B, C, D
                    if q.qtype == "TN":
                        if shuffle_mode in ("both", "options_only"):
                            dep_lbl = q.find_dependent_option() if auto_pin_dependent_options else None
                            if dep_lbl in labels:
                                other_lbls = [l for l in labels if l != dep_lbl]
                                rng.shuffle(other_lbls)
                                perm_sources = other_lbls + [dep_lbl]  # dep_lbl luôn ở D
                            else:
                                perm_sources = labels[:]
                                rng.shuffle(perm_sources)
                        else:
                            perm_sources = labels[:]

                        new_opts = {}
                        q_opt_perm = {}
                        for new_lbl, old_lbl in zip(labels, perm_sources):
                            new_opts[new_lbl] = q.option_runs.get(old_lbl, [])
                            q_opt_perm[new_lbl] = old_lbl
                            if q.correct_key and q.correct_key == old_lbl:
                                shuffled_keys[cur_q_num] = new_lbl
                        opt_map_code[cur_q_num] = q_opt_perm

                        # Tái tạo các đoạn phương án đáp án theo đúng layout gốc
                        opt_paras_created = []
                        if q.option_layout == "1_para" and q.option_elements:
                            p = copy.deepcopy(q.option_elements[0])
                            for child in list(p):
                                if child.tag.split("}")[-1] != "pPr":
                                    p.remove(child)
                            for i_lbl, lbl in enumerate(labels):
                                p.append(make_label_run(lbl))
                                for r in new_opts[lbl]:
                                    p.append(copy.deepcopy(r))
                                if i_lbl < 3:
                                    p.append(make_tab_run())
                            body.append(p)
                            opt_paras_created.append(p)
                        elif q.option_layout == "2_para" and len(q.option_elements) >= 2:
                            p1 = copy.deepcopy(q.option_elements[0])
                            for child in list(p1):
                                if child.tag.split("}")[-1] != "pPr":
                                    p1.remove(child)
                            p1.append(make_label_run("A"))
                            for r in new_opts["A"]: p1.append(copy.deepcopy(r))
                            p1.append(make_tab_run())
                            p1.append(make_label_run("B"))
                            for r in new_opts["B"]: p1.append(copy.deepcopy(r))
                            body.append(p1)
                            opt_paras_created.append(p1)

                            p2 = copy.deepcopy(q.option_elements[1])
                            for child in list(p2):
                                if child.tag.split("}")[-1] != "pPr":
                                    p2.remove(child)
                            p2.append(make_label_run("C"))
                            for r in new_opts["C"]: p2.append(copy.deepcopy(r))
                            p2.append(make_tab_run())
                            p2.append(make_label_run("D"))
                            for r in new_opts["D"]: p2.append(copy.deepcopy(r))
                            body.append(p2)
                            opt_paras_created.append(p2)
                        else:
                            base_p = q.option_elements[0] if q.option_elements else etree.Element(f"{{{W_NS}}}p")
                            for lbl in labels:
                                p = copy.deepcopy(base_p)
                                for child in list(p):
                                    if child.tag.split("}")[-1] != "pPr":
                                        p.remove(child)
                                p.append(make_label_run(lbl))
                                for r in new_opts[lbl]:
                                    p.append(copy.deepcopy(r))
                                body.append(p)
                                opt_paras_created.append(p)
                        code_body_elements.extend(opt_paras_created)
                    else:
                        # Tự luận: Tạo các dòng kẻ chấm chấm để học sinh viết đáp án (+2 dòng)
                        lines_needed = max(q.tl_min_lines, 4) + 2
                        for _ in range(lines_needed):
                            dot_p = make_dotted_line_p()
                            body.append(dot_p)
                            code_body_elements.append(dot_p)

        # Đồng bộ toàn bộ answer key từ matched_exam nếu có
        if matched_exam and getattr(matched_exam, "answer_key", None):
            for k_q, k_v in matched_exam.answer_key.items():
                if k_q not in shuffled_keys:
                    shuffled_keys[k_q] = k_v
                        
        # 3. Footer kết thúc
        code_footers = []
        for f in footers:
            f_clone = copy.deepcopy(f)
            body.append(f_clone)
            code_footers.append(f_clone)
            
        # 4. Giữ sectPr
        if sectPr is not None:
            body.append(sectPr)
            
        # Lưu file Word đề thi đơn lẻ
        out_file = out_dir / f"De_Thi_Ma_{code_str}.docx"
        doc.save(str(out_file))
        generated_files.append(str(out_file))
        
        keys_by_code[code_str] = shuffled_keys
        question_map_by_code[code_str] = q_map_code
        option_map_by_code[code_str] = opt_map_code
        
        # Nếu xuất file gộp, ghép vào merged_body
        if merged_body is not None:
            for h in code_headers:
                merged_body.append(copy.deepcopy(h))
            for el in code_body_elements:
                merged_body.append(copy.deepcopy(el))
            for f in code_footers:
                merged_body.append(copy.deepcopy(f))
            if code_idx < len(codes) - 1:
                merged_body.append(make_page_break_p())
                
    # 5. Lưu file Word GỘP nếu có
    if merged_doc is not None and merged_body is not None:
        if master_sectPr is not None:
            merged_body.append(copy.deepcopy(master_sectPr))
        merged_file = out_dir / "De_Thi_Tat_Ca_Ma_De_Gop.docx"
        merged_doc.save(str(merged_file))
        generated_files.append(str(merged_file))
        
    # 6. Xuất file Bảng Đáp Án Các Mã Đề Word (Bang_Dap_An_Cac_Ma_De.docx)
    ans_file = out_dir / "Bang_Dap_An_Cac_Ma_De.docx"
    _export_answer_keys_doc(keys_by_code, str(ans_file))
    generated_files.append(str(ans_file))
    
    # 7. Xuất file Bảng Đáp Án & Ma Trận Hoán Vị Excel (.xlsx)
    excel_file = out_dir / "Bang_Dap_An_Va_Ma_Tran_Hoan_Vi.xlsx"
    export_exam_keys_and_matrix_to_excel(
        str(excel_file),
        keys_by_code,
        question_map_by_code,
        orig_keys,
        option_map_by_code
    )
    generated_files.append(str(excel_file))
    
    return generated_files, keys_by_code, str(ans_file), str(excel_file), question_map_by_code, option_map_by_code


def _export_answer_keys_doc(keys_by_code: Dict[str, Dict[int, str]], output_path: str) -> None:
    """Tạo file Word bảng đáp án đối chiếu cho giáo viên."""
    doc = docx.Document()
    
    p = doc.add_paragraph()
    p.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("BẢNG ĐÁP ÁN CÁC MÃ ĐỀ THI")
    r.font.bold = True
    r.font.size = docx.shared.Pt(16)
    r.font.color.rgb = docx.shared.RGBColor(31, 73, 125)
    r.font.name = "Times New Roman"
    
    codes = sorted(keys_by_code.keys())
    if not codes:
        doc.save(output_path)
        return
        
    all_q_nums = sorted(list({q for code in codes for q in keys_by_code[code].keys()}))
    if not all_q_nums:
        doc.save(output_path)
        return
        
    table = doc.add_table(rows=len(all_q_nums) + 1, cols=len(codes) + 1)
    table.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    
    # Header row
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Câu"
    for idx, c in enumerate(codes):
        hdr_cells[idx + 1].text = f"Mã {c}"
        
    for r in table.rows[0].cells:
        for p in r.paragraphs:
            p.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.bold = True
                run.font.name = "Times New Roman"
                
    # Data rows
    for row_idx, q_num in enumerate(all_q_nums, 1):
        row_cells = table.rows[row_idx].cells
        row_cells[0].text = str(q_num)
        for col_idx, c in enumerate(codes):
            ans = keys_by_code[c].get(q_num, "-")
            row_cells[col_idx + 1].text = ans
            
        for r in row_cells:
            for p in r.paragraphs:
                p.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.name = "Times New Roman"
                    
    doc.save(output_path)


def preview_shuffled_keys(
    source_docx_path: str,
    num_codes: int = 4,
    start_code: int = 101,
    custom_codes: Optional[List[str]] = None,
    shuffle_mode: str = "both",
    auto_pin_dependent_options: bool = True,
    pinned_question_indices: Optional[Set[int]] = None,
) -> Tuple[Dict[str, Dict[int, str]], Dict[str, Dict[int, int]], Dict[str, Dict[int, Dict[str, str]]]]:
    """Tính trước bảng đáp án và ma trận hoán vị theo đúng thứ tự xáo trộn OpenXML."""
    headers, sections, footers, orig_keys = parse_docx_xml_structure(source_docx_path)
    
    if custom_codes and len(custom_codes) > 0:
        codes = [str(c).strip() for c in custom_codes if str(c).strip()]
    else:
        codes = [str(start_code + i) for i in range(num_codes)]
        
    keys_by_code: Dict[str, Dict[int, str]] = {}
    question_map_by_code: Dict[str, Dict[int, int]] = {}
    option_map_by_code: Dict[str, Dict[int, Dict[str, str]]] = {}
    
    pinned_set = set(pinned_question_indices or [])
    labels = ["A", "B", "C", "D"]
    
    for code_str in codes:
        digits = re.sub(r"\D", "", code_str)
        code_seed = int(digits) if digits else (abs(hash(code_str)) % 100000)
        rng = random.Random(code_seed)
        
        shuffled_keys: Dict[int, str] = {}
        q_map_code: Dict[int, int] = {}
        opt_map_code: Dict[int, Dict[str, str]] = {}
        global_q_counter = 1
        
        for sec in sections:
            if shuffle_mode in ("both", "questions_only"):
                shuffled_qs = _shuffle_with_pinned(list(sec.questions), pinned_set, rng)
            else:
                shuffled_qs = list(sec.questions)
                
            for q in shuffled_qs:
                cur_q_num = global_q_counter
                orig_q_num = q.original_index
                global_q_counter += 1
                q_map_code[cur_q_num] = orig_q_num
                
                if q.qtype == "TN":
                    if shuffle_mode in ("both", "options_only"):
                        dep_lbl = q.find_dependent_option() if auto_pin_dependent_options else None
                        if dep_lbl in labels:
                            other_lbls = [l for l in labels if l != dep_lbl]
                            rng.shuffle(other_lbls)
                            perm_sources = other_lbls + [dep_lbl]
                        else:
                            perm_sources = labels[:]
                            rng.shuffle(perm_sources)
                    else:
                        perm_sources = labels[:]
                        
                    q_opt_perm = {}
                    for new_lbl, old_lbl in zip(labels, perm_sources):
                        q_opt_perm[new_lbl] = old_lbl
                        if q.correct_key and q.correct_key == old_lbl:
                            shuffled_keys[cur_q_num] = new_lbl
                    opt_map_code[cur_q_num] = q_opt_perm
                    
        keys_by_code[code_str] = shuffled_keys
        question_map_by_code[code_str] = q_map_code
        option_map_by_code[code_str] = opt_map_code
        
    return keys_by_code, question_map_by_code, option_map_by_code
