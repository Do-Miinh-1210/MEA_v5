"""
export/template_matrix.py — Tạo file .docx mẫu ma trận đề thi cho giáo viên.

3 định dạng:
  1. BGD 19 cột  (Bộ Giáo dục & Đào tạo)
  2. Trường 12 cột (tùy chỉnh theo trường)
  3. Đơn giản 6 cột (mặc định app)
"""

from __future__ import annotations
from pathlib import Path


def _ensure_docx():
    try:
        from docx import Document
        return Document
    except ImportError:
        raise ImportError("Chưa cài python-docx. Chạy: pip install python-docx")


# ─── Format 1: BGD 19 cột ──────────────────────────────────────────────────

def create_bgd_template(output_path: str) -> str:
    """Ma trận theo mẫu Bộ Giáo dục — 2 bảng (ma trận + bản đặc tả)."""
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(10)

    section = doc.sections[0]
    section.orientation = 1  # Landscape
    section.page_width = Cm(29.7)
    section.page_height = Cm(21.0)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)

    # ── Title ──
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("MA TRẬN ĐỀ KIỂM TRA GIỮA HỌC KỲ I — NĂM HỌC 2025–2026")
    r.bold = True
    r.font.size = Pt(13)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Môn: TOÁN — Lớp 12 — Thời gian: 90 phút (không kể phát đề)")
    r2.font.size = Pt(11)

    doc.add_paragraph()  # spacing

    # ── BẢNG 1: MA TRẬN (summary table) ──
    h1 = doc.add_paragraph()
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rh1 = h1.add_run("BẢNG 1: MA TRẬN")
    rh1.bold = True
    rh1.font.size = Pt(11)

    # Headers: STT | Chủ đề | TN (NB/TH/VD) | DS (NB/TH/VD) | TLN (NB/TH/VD) | TL (NB/TH/VD) | Tổng
    # = 1 + 1 + 4*3 + 1 = 15 columns
    qtypes = ["TN", "DS", "TLN", "TL"]
    levels = ["NB", "TH", "VD"]

    table = doc.add_table(rows=5, cols=15)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Row 0: merged header
    row0 = table.rows[0]
    row0.cells[0].text = "STT"
    row0.cells[1].text = "Chủ đề / Nội dung"
    col = 2
    for qt in qtypes:
        row0.cells[col].text = qt
        # Merge 3 cells for each qtype
        row0.cells[col].merge(row0.cells[col + 2])
        col += 3
    row0.cells[14].text = "Tổng"

    # Row 1: sub-headers (NB/TH/VD under each type)
    row1 = table.rows[1]
    row1.cells[0].text = ""
    row1.cells[1].text = ""
    col = 2
    for _ in qtypes:
        for lv in levels:
            row1.cells[col].text = lv
            col += 1
    row1.cells[14].text = ""

    # Sample data rows
    # Columns 2-14: TN_NB, TN_TH, TN_VD, DS_NB, DS_TH, DS_VD, TLN_NB, TLN_TH, TLN_VD, TL_NB, TL_TH, TL_VD, Tổng
    topics = [
        ("1", "Ứng dụng đạo hàm", ["2", "", "1", "", "1", "", "", "", "1", "", "", "", "4"]),
        ("2", "Nguyên hàm – Tích phân", ["1", "1", "", "1", "", "", "", "1", "", "", "", "1", "5"]),
        ("", "Tổng", ["3", "1", "1", "1", "1", "", "", "1", "1", "", "", "1", "10"]),
    ]

    for i, (stt, topic, vals) in enumerate(topics):
        row = table.rows[i + 2]
        row.cells[0].text = stt
        row.cells[1].text = topic
        for j, v in enumerate(vals):
            row.cells[j + 2].text = v

    # Bold formatting
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                    run.font.name = "Times New Roman"

    doc.add_paragraph()  # spacing

    # ── BẢNG 2: BẢN ĐẶC TẢ ──
    h2 = doc.add_paragraph()
    h2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rh2 = h2.add_run("BẢNG 2: BẢN ĐẶC TẢ")
    rh2.bold = True
    rh2.font.size = Pt(11)

    spec = doc.add_table(rows=7, cols=6)
    spec.style = "Table Grid"
    spec.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Headers
    spec_headers = ["STT", "Nội dung kiến thức", "Mức độ", "Dạng câu hỏi", "Câu hỏi", "Yêu cầu cần đạt"]
    for i, h in enumerate(spec_headers):
        spec.rows[0].cells[i].text = h
        for p in spec.rows[0].cells[i].paragraphs:
            for run in p.runs:
                run.bold = True

    # Sample spec rows
    spec_data = [
        ("1", "Ứng dụng đạo hàm", "NB", "TN", "1,2", "Tìm khoảng đơn điệu của hàm số"),
        ("", "", "TH", "TN", "3", "Tìm GTLN, GTNN trên đoạn"),
        ("", "", "VD", "TLN", "7", "Giải bài toán tiếp tuyến"),
        ("2", "Nguyên hàm – Tích phân", "NB", "TN", "4", "Tìm nguyên hàm cơ bản"),
        ("", "", "TH", "DS", "5", "Tính tích phân xác định"),
        ("", "", "VD", "TL", "8", "Ứng dụng tích phân tính diện tích"),
    ]
    for i, row_data in enumerate(spec_data):
        row = spec.rows[i + 1]
        for j, val in enumerate(row_data):
            row.cells[j].text = val

    for row in spec.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(10)
                    run.font.name = "Times New Roman"

    doc.save(output_path)
    return output_path


# ─── Format 2: Trường 12 cột ───────────────────────────────────────────────

def create_school_template(output_path: str) -> str:
    """Ma trận theo mẫu trường — bảng 12 cột đơn."""
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(10)

    section = doc.sections[0]
    section.orientation = 1
    section.page_width = Cm(29.7)
    section.page_height = Cm(21.0)
    section.top_margin = Cm(1.5)
    section.bottom_margin = Cm(1.5)
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("MA TRẬN ĐỀ KIỂM TRA — MẪU TRƯỜNG")
    r.bold = True
    r.font.size = Pt(13)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Môn: TOÁN — Lớp 12 — Thời gian: 90 phút")
    r2.font.size = Pt(11)

    doc.add_paragraph()

    # 12 columns: STT | Chủ đề | Mức độ | TN | DS | TLN | TL | Số câu | Điểm | Mã câu | Yêu cầu | Ghi chú
    table = doc.add_table(rows=6, cols=12)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["STT", "Chủ đề", "Mức độ", "TN", "DS", "TLN", "TL", "Số câu", "Điểm", "Mã câu", "Yêu cầu cần đạt", "Ghi chú"]
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
        for p in table.rows[0].cells[i].paragraphs:
            for run in p.runs:
                run.bold = True

    sample = [
        ("1", "Ứng dụng đạo hàm", "NB", "2", "", "", "", "2", "0.5", "C1,C2", "Xét tính đơn điệu", ""),
        ("", "", "TH", "1", "", "", "", "1", "0.25", "C3", "Tìm cực trị", ""),
        ("", "", "VD", "", "", "1", "", "1", "0.5", "C7", "Tiếp tuyến", ""),
        ("2", "Tích phân", "NB", "1", "", "", "", "1", "0.25", "C4", "Nguyên hàm cơ bản", ""),
        ("", "", "TH", "", "1", "", "", "1", "1.0", "C5", "Tích phân xác định", ""),
    ]
    for i, row_data in enumerate(sample):
        row = table.rows[i + 1]
        for j, val in enumerate(row_data):
            row.cells[j].text = val

    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in paragraph.runs:
                    run.font.size = Pt(9)
                    run.font.name = "Times New Roman"

    doc.save(output_path)
    return output_path


# ─── Format 3: Đơn giản 6 cột ─────────────────────────────────────────────

def create_simple_template(output_path: str) -> str:
    """Ma trận đơn giản — 6 cột, dễ dùng nhất."""
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(11)

    section = doc.sections[0]
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("MA TRẬN ĐỀ KIỂM TRA — MẪU ĐƠN GIẢN")
    r.bold = True
    r.font.size = Pt(13)

    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run("Môn: TOÁN — Lớp 12 — Thời gian: 45 phút")
    r2.font.size = Pt(11)

    doc.add_paragraph()

    # 6 columns: STT | Chủ đề | Mức độ | Dạng | Số câu | Yêu cầu cần đạt
    table = doc.add_table(rows=8, cols=6)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["STT", "Chủ đề", "Mức độ", "Dạng câu", "Số câu", "Yêu cầu cần đạt"]
    for i, h in enumerate(headers):
        table.rows[0].cells[i].text = h
        for p in table.rows[0].cells[i].paragraphs:
            for run in p.runs:
                run.bold = True

    sample = [
        ("1", "Hàm số và đồ thị", "NB", "TN", "3", "Nhận dạng đồ thị hàm số bậc 3, bậc 4"),
        ("", "", "TH", "TN", "2", "Xác định tính đơn điệu, cực trị"),
        ("", "", "VD", "TLN", "1", "Tìm GTLN, GTNN trên đoạn"),
        ("2", "Mũ và Logarit", "NB", "TN", "2", "Tính giá trị biểu thức mũ, logarit"),
        ("", "", "TH", "DS", "1", "So sánh, biến đổi biểu thức"),
        ("", "", "VD", "TN", "1", "Giải phương trình mũ, logarit"),
        ("3", "Nguyên hàm", "VD", "TL", "1", "Tính tích phân bằng phương pháp đặt ẩn"),
    ]
    for i, row_data in enumerate(sample):
        row = table.rows[i + 1]
        for j, val in enumerate(row_data):
            row.cells[j].text = val

    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(10)
                    run.font.name = "Times New Roman"

    # Add note
    doc.add_paragraph()
    note = doc.add_paragraph()
    rn = note.add_run("Hướng dẫn: ")
    rn.bold = True
    rn.font.size = Pt(10)
    note.add_run(
        "Điền thông tin vào bảng trên. Cột 'Dạng câu' gồm: TN (trắc nghiệm), "
        "DS (đúng/sai 4 ý), TLN (trả lời ngắn), TL (tự luận). "
        "Cột 'Mức độ' gồm: NB (nhận biết), TH (thông hiểu), VD (vận dụng). "
        "Upload file này vào ExamAI để tạo đề tự động."
    ).font.size = Pt(10)

    doc.save(output_path)
    return output_path


# ─── Public API ─────────────────────────────────────────────────────────────

TEMPLATE_INFO = [
    {
        "id": "bgd",
        "label": "Mẫu BGD (19 cột)",
        "desc": "Ma trận theo chuẩn Bộ Giáo dục — gồm bảng ma trận và bản đặc tả",
        "filename": "MaTran_Mau_BGD.docx",
        "builder": create_bgd_template,
    },
    {
        "id": "school",
        "label": "Mẫu Trường (12 cột)",
        "desc": "Ma trận tùy chỉnh theo trường — 12 cột chi tiết",
        "filename": "MaTran_Mau_Truong.docx",
        "builder": create_school_template,
    },
    {
        "id": "simple",
        "label": "Mẫu Đơn giản (6 cột)",
        "desc": "Ma trận đơn giản nhất — 6 cột, dễ sử dụng",
        "filename": "MaTran_Mau_DonGian.docx",
        "builder": create_simple_template,
    },
]


def get_or_create_template(template_id: str, output_dir: str | Path) -> Path:
    """Get or create a template file. Returns the file path."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for info in TEMPLATE_INFO:
        if info["id"] == template_id:
            path = output_dir / info["filename"]
            if not path.exists():
                info["builder"](str(path))
            return path

    raise ValueError(f"Unknown template: {template_id}")
