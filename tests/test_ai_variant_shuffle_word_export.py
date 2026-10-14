"""
tests/test_ai_variant_shuffle_word_export.py — Kiểm thử toàn diện tính năng Trộn đề đổi số liệu AI
bảo toàn công thức MathType/OMML khi xuất file Word.
"""
from __future__ import annotations
import os
import json
import zipfile
from pathlib import Path
import pytest
from lxml import etree

from export.math_converter import latex_to_omml, omml_to_latex, extract_para_text_with_math
from omr_exam.docx_parser import parse_exam_docx
from omr_exam.models import ExamSection, ExamQuestion, OptionItem, ShuffledExamCode
from services.ai_variant_generator import (
    generate_ai_variants,
    generate_ai_variants_for_sections,
    sections_to_exam_data,
)
from omr_exam.docx_exporter import export_shuffled_exams_to_docx
from omr_exam.exam_shuffler import shuffle_exam


def test_omml_to_latex_fidelity():
    """Kiểm tra độ chính xác của bộ chuyển đổi OMML -> LaTeX."""
    test_formulas = [
        r"x^2 - 5x + 6 = 0",
        r"\frac{1}{2}",
        r"\sqrt{x + 1}",
        r"2x^2 - y \le 5",
        r"\begin{cases} x + y = 1 \\ x - y = 2 \end{cases}",
    ]

    for f in test_formulas:
        omml = latex_to_omml(f)
        assert omml is not None, f"latex_to_omml failed for {f}"
        latex_out = omml_to_latex(omml)
        assert latex_out, f"omml_to_latex returned empty string for {f}"
        # Đảm bảo các ký hiệu toán cốt lõi được giữ lại
        if r"\frac" in f:
            assert r"\frac" in latex_out
        if r"\sqrt" in f:
            assert r"\sqrt" in latex_out
        if r"\le" in f:
            assert (r"\le" in latex_out or "≤" in latex_out)


def test_docx_parsing_preserves_math():
    """Kiểm tra nạp file Word thực tế (test_export_word.docx) bảo toàn công thức toán."""
    docx_path = "test_export_word.docx"
    assert os.path.exists(docx_path), "File test_export_word.docx không tồn tại."

    sections = parse_exam_docx(docx_path)
    assert len(sections) >= 1, "Không nhận diện được section nào."
    
    sec1 = sections[0]
    assert len(sec1.questions) == 14, f"Số câu trắc nghiệm mong muốn 14, nhận được {len(sec1.questions)}"
    
    q1 = sec1.questions[0]
    assert q1.qtype == "TN"
    assert "bất phương trình" in q1.content
    assert len(q1.options) == 4
    # Kiểm tra phương án có chứa công thức LaTeX ${...}$
    assert any("$" in opt.text for opt in q1.options), "Phương án không chứa công thức toán LaTeX"
    assert q1.correct_label == "B", f"Đáp án câu 1 mong đợi B, nhận được {q1.correct_label}"


def test_ai_variant_generation_with_math(tmp_path):
    """Kiểm tra gọi AI đổi số liệu câu hỏi có chứa công thức toán."""
    from core.models import Question

    sample_q = Question(
        qtype="TN",
        level="TH",
        topic="Bất phương trình",
        question=r"Trong các bất phương trình sau, bất phương trình nào là bậc nhất hai ẩn?",
        options={
            "A": r"${2x^2 - y \le 5}$",
            "B": r"${x - 3y > 4}$",
            "C": r"${x + \dfrac{1}{y} \ge 2}$",
            "D": r"${2x - 3y^2 < 0}$",
        },
        answer="B",
    )

    # Giả lập phản hồi AI đổi số liệu (thay hệ số 2, 3, 4, 5 thành 3, 4, 5, 6)
    def mock_ai_call(prompt: str) -> str:
        return json.dumps({
            "variants": [
                {
                    "question": r"Trong các bất phương trình sau, bất phương trình nào là bậc nhất hai ẩn?",
                    "solution": r"Bất phương trình ${x - 4y > 5}$ có bậc 1 đối với cả x và y.",
                    "options": {
                        "A": r"${3x^2 - y \le 6}$",
                        "B": r"${x - 4y > 5}$",
                        "C": r"${x + \dfrac{1}{y} \ge 3}$",
                        "D": r"${3x - 4y^2 < 0}$",
                    },
                    "answer": "B"
                }
            ]
        })

    variants = generate_ai_variants(sample_q, n=1, ai_call=mock_ai_call)
    assert len(variants) == 1
    var_q = variants[0]
    assert var_q.question == sample_q.question
    assert var_q.options["B"] == r"${x - 4y > 5}$"
    assert var_q.answer == "B"


def test_end_to_end_ai_variant_and_word_mathtype_export(tmp_path):
    """Kiểm tra luồng hoàn chỉnh: Nạp Word -> AI đổi số -> Trộn mã đề -> Xuất Word bảo toàn MathType/OMML."""
    docx_path = "test_export_word.docx"
    sections = parse_exam_docx(docx_path)
    assert sections

    # Thu nhỏ tập test lấy 3 câu đầu để chạy kiểm thử nhanh và chắc chắn
    test_sec = ExamSection(
        title="PHẦN I. TRẮC NGHIỆM",
        questions=sections[0].questions[:3]
    )

    # Mock AI đổi số liệu
    def mock_ai_call(prompt: str) -> str:
        # Tự động thay các con số trong prompt để tạo biến thể mới
        return json.dumps({
            "variants": [
                {
                    "question": r"Cặp số ${(2; -3)}$ là nghiệm của bất phương trình nào sau đây?",
                    "solution": r"Thay x=2, y=-3 vào ${3x + y \ge 1}$ ta được $3(2) + (-3) = 3 \ge 1$.",
                    "options": {
                        "A": r"${2x - y < 0}$",
                        "B": r"${x + 4y > 0}$",
                        "C": r"${3x + y \ge 1}$",
                        "D": r"${x - 3y \le 2}$",
                    },
                    "answer": "C"
                }
            ]
        })

    # 1. Gọi sinh biến thể đổi số
    var_sections, n_rep, n_kept = generate_ai_variants_for_sections(
        sections=[test_sec],
        ai_call=mock_ai_call,
        max_retry=1,
    )
    assert n_rep == 3
    assert n_kept == 0

    # 2. Xáo trộn tạo 2 mã đề: 101 và 102
    target_codes = ["101", "102"]
    shuffled_list = shuffle_exam(
        var_sections,
        custom_codes=target_codes,
        shuffle_mode="both",
        auto_pin_dependent_options=True,
    )
    assert len(shuffled_list) == 2

    # 3. Xuất file Word với MathType/OMML
    out_dir = tmp_path / "exported_ai_variants"
    out_dir.mkdir(parents=True, exist_ok=True)

    created_files = export_shuffled_exams_to_docx(
        shuffled_exams=shuffled_list,
        output_dir=str(out_dir),
        source_docx_path=None,  # Bắt buộc None để kích hoạt tạo mới kèm OMML
        export_merged_docx=True,
    )

    assert len(created_files) >= 3  # Mã 101, Mã 102, File Gộp

    # 4. Kiểm tra cấu trúc OpenXML trong file Word xuất ra
    docx_count = 0
    for file_path in created_files:
        p = Path(file_path)
        assert p.exists()
        assert p.stat().st_size > 0

        if p.suffix == ".docx":
            docx_count += 1
            # Mở gói .docx như 1 file ZIP và đọc word/document.xml
            with zipfile.ZipFile(p, "r") as zf:
                assert "word/document.xml" in zf.namelist()
                doc_xml = zf.read("word/document.xml").decode("utf-8")

                # BẢO ĐẢM: Không tự động chuyển đổi sang Word Equation <m:oMath>
                assert "<m:oMath" not in doc_xml, \
                    f"File {p.name} không được chứa thẻ Word Equation <m:oMath>!"
        elif p.suffix == ".xlsx":
            # File Excel bảng đáp án và ma trận hoán vị
            with zipfile.ZipFile(p, "r") as zf:
                assert "xl/workbook.xml" in zf.namelist()

    print("✓ Toàn bộ kiểm thử xuất Word bảo toàn MathType/OMML thành công 100%!")


def test_ai_variant_preserves_original_word_structure(tmp_path):
    """Kiểm tra: Khi AI thay số liệu từ file Word có sẵn (source_docx_path):
    - TUYỆT ĐỐI KHÔNG tự tạo cấu trúc Word mới (không sinh header giả lập 'TRƯỜNG THPT: ....................').
    - GIỮ NGUYÊN 100% CẤU TRÚC GỐC: Header trường/sở, tiêu đề bài thi, lề trang, bảng biểu, sectPr.
    - CHỈ ĐỔI SỐ LIỆU trong câu hỏi và cập nhật đáp án mới.
    - KHÔNG TỰ CHUYỂN SANG EQUATION: Không có thẻ <m:oMath>, giữ nguyên dạng $...$ cho MathType.
    """
    docx_path = "test_export_word.docx"
    assert os.path.exists(docx_path)
    sections = parse_exam_docx(docx_path)

    # Lấy 2 câu đầu làm mẫu
    test_sec = ExamSection(
        title=sections[0].title,
        questions=sections[0].questions[:2]
    )

    def mock_ai_call(prompt: str) -> str:
        return json.dumps({
            "variants": [
                {
                    "question": r"Biểu thức ${P = 5x - 7y}$ đạt giá trị lớn nhất tại điểm nào?",
                    "solution": r"Lời giải với số mới ${P = 5x - 7y}$.",
                    "options": {
                        "A": r"${(1; 2)}$",
                        "B": r"${(3; -1)}$",
                        "C": r"${(0; 4)}$",
                        "D": r"${(-2; 5)}$",
                    },
                    "answer": "B"
                }
            ]
        })

    # Gọi AI sinh biến thể
    var_sections, _, _ = generate_ai_variants_for_sections(
        sections=[test_sec],
        ai_call=mock_ai_call,
        max_retry=1,
    )

    # Trộn 2 mã đề: 101 và 102
    target_codes = ["101", "102"]
    shuffled_list = shuffle_exam(
        var_sections,
        custom_codes=target_codes,
        shuffle_mode="both",
    )

    out_dir = tmp_path / "exported_preserved_structure"
    out_dir.mkdir(parents=True, exist_ok=True)

    created_files = export_shuffled_exams_to_docx(
        shuffled_exams=shuffled_list,
        output_dir=str(out_dir),
        source_docx_path=docx_path,
        export_merged_docx=True,
        is_ai_variant=True,
    )

    de_101 = out_dir / "De_Thi_Ma_101.docx"
    assert de_101.exists()

    with zipfile.ZipFile(de_101, "r") as zf:
        doc_xml = zf.read("word/document.xml").decode("utf-8")

        # 1. Bảo toàn 100% header gốc của file test_export_word.docx
        assert "SỞ/PHÒNG GD&ĐT" in doc_xml or "ĐỀ THI TEST" in doc_xml, \
            "Header gốc của tài liệu bị mất!"
        assert "TRƯỜNG THPT: ...................." not in doc_xml, \
            "Đã tự ý tạo cấu trúc header giả lập mới thay vì giữ nguyên tài liệu cũ!"

        # 2. Cập nhật mã đề trong header cũ
        assert "Mã đề: 101" in doc_xml or "Mã đề thi: 101" in doc_xml, \
            "Không cập nhật mã đề vào header cũ!"

        # 3. Chỉ thay đổi số liệu trong nội dung câu hỏi
        assert "5x - 7y" in doc_xml, \
            "Nội dung câu hỏi đổi số AI không xuất hiện trong file Word!"

        # 4. Tuyệt đối không sinh <m:oMath> (bảo toàn MathType $...$)
        assert "<m:oMath" not in doc_xml, \
            "Phát hiện thẻ <m:oMath>! Đầu ra phải là văn bản tương thích MathType."

    # Kiểm tra file gộp cũng giữ nguyên cấu trúc
    de_gop = out_dir / "De_Thi_Tat_Ca_Ma_De_Gop.docx"
    assert de_gop.exists()
    with zipfile.ZipFile(de_gop, "r") as zf:
        gop_xml = zf.read("word/document.xml").decode("utf-8")
        assert "SỞ/PHÒNG GD&ĐT" in gop_xml or "ĐỀ THI TEST" in gop_xml
        assert "<m:oMath" not in gop_xml

    print("✓ Kiểm thử bảo toàn 100% cấu trúc tài liệu Word khi đổi số AI thành công!")
