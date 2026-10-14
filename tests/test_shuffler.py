# -*- coding: utf-8 -*-
"""
tests/test_shuffler.py — Kiểm tra toàn diện engine trộn đề thi và xuất file.
"""
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omr_exam.models import ExamSection, ExamQuestion, OptionItem
from omr_exam.exam_shuffler import shuffle_exam, is_dependent_option_text
from omr_exam.excel_exporter import export_exam_keys_and_matrix_to_excel
from omr_exam.docx_exporter import export_shuffled_exams_to_docx

def test_dependent_options():
    assert is_dependent_option_text("Cả A và B đều đúng") == True
    assert is_dependent_option_text("Tất cả các đáp án trên") == True
    assert is_dependent_option_text("Tất cả các đáp án trên đều đúng.") == True
    assert is_dependent_option_text("Không có đáp án nào đúng") == True
    assert is_dependent_option_text("Cả 3 đáp án trên") == True
    assert is_dependent_option_text("All of the above") == True
    assert is_dependent_option_text("x = 5") == False
    assert is_dependent_option_text("Hình chóp tam giác đều") == False
    print("[OK] test_dependent_options PASSED")

def test_pin_options_and_questions():
    q1 = ExamQuestion(
        index=1,
        content="Câu hỏi số 1: Giá trị của x là?",
        options=[
            OptionItem("A", "x = 1", is_correct=False),
            OptionItem("B", "x = 2", is_correct=False),
            OptionItem("C", "Tất cả các đáp án trên đều đúng", is_correct=True),
            OptionItem("D", "x = 3", is_correct=False)
        ],
        correct_label="C"
    )
    q2 = ExamQuestion(
        index=2,
        content="Câu hỏi số 2: Câu cố định không được đảo?",
        options=[
            OptionItem("A", "Đúng", is_correct=True),
            OptionItem("B", "Sai", is_correct=False),
        ],
        correct_label="A"
    )
    sec = ExamSection(title="Phần I: Trắc nghiệm", questions=[q1, q2])
    
    # Ghim câu 2
    shuffled = shuffle_exam(
        [sec],
        num_codes=4,
        start_code=101,
        auto_pin_dependent_options=True,
        pinned_question_indices={2}
    )
    assert len(shuffled) == 4
    for ex in shuffled:
        qs = ex.sections[0].questions
        # Phương án phụ thuộc của câu 1 phải luôn ở nhãn D
        q1_shuffled = [q for q in qs if q.content.startswith("Câu hỏi số 1")][0]
        assert q1_shuffled.options[-1].label == "D"
        assert "Tất cả các đáp án trên" in q1_shuffled.options[-1].text
        assert ex.answer_key[q1_shuffled.index] == "D"
        
        # Câu 2 bị ghim ở vị trí 2
        assert qs[1].content.startswith("Câu hỏi số 2")
    print("[OK] test_pin_options_and_questions PASSED")

def test_export_all():
    q1 = ExamQuestion(
        index=1,
        content="Nghiệm của phương trình 2x - 4 = 0 là:",
        options=[
            OptionItem("A", "x = 1", is_correct=False),
            OptionItem("B", "x = 2", is_correct=True),
            OptionItem("C", "x = 3", is_correct=False),
            OptionItem("D", "Không có đáp án nào đúng", is_correct=False)
        ],
        correct_label="B"
    )
    q_tl = ExamQuestion(
        index=2,
        content="Giải phương trình bậc hai: x^2 - 3x + 2 = 0.",
        qtype="TL",
        tl_min_lines=3
    )
    sec = ExamSection(title="Phần I: Đề thi", questions=[q1, q_tl])
    shuffled = shuffle_exam([sec], num_codes=2, start_code=201)
    
    out_dir = "test_output_shuffler"
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
        
    files = export_shuffled_exams_to_docx(shuffled, out_dir, export_merged_docx=True)
    assert len(files) >= 4 # 2 de + 1 gop + 1 bang dap an docx + 1 excel
    assert any(f.endswith(".xlsx") for f in files)
    assert any("Tat_Ca_Ma_De_Gop.docx" in f for f in files)
    
    shutil.rmtree(out_dir)
    print("[OK] test_export_all PASSED")

if __name__ == "__main__":
    test_dependent_options()
    test_pin_options_and_questions()
    test_export_all()
    print("\nALL TESTS SUCCESSFULLY PASSED!")
