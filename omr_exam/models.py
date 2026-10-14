"""
omr_exam/models.py — Data structures for Exam, Question, Choices, and OMR Sheet.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class OptionItem:
    """Một phương án lựa chọn A, B, C, D..."""
    label: str       # "A", "B", "C", "D"
    text: str        # Nội dung chữ
    is_correct: bool = False
    xml_content: Optional[str] = None  # Giữ XML runs (MathType, images...) nếu có


@dataclass
class ExamQuestion:
    """Một câu hỏi trong đề."""
    index: int                          # Số thứ tự trong đề gốc (1, 2, 3...)
    section: str = "Trắc nghiệm"        # Tên phần: "Phần I", "Phần II", "Tự luận"...
    qtype: str = "TN"                   # "TN" (Trắc nghiệm A/B/C/D) hoặc "TL" (Tự luận)
    content: str = ""                   # Nội dung câu hỏi
    options: List[OptionItem] = field(default_factory=list)
    correct_label: str = ""             # Đáp án đúng gốc: "A", "B", "C", hoặc "D"
    tl_min_lines: int = 3               # Độ dài dự kiến (số dòng) nếu là câu Tự luận
    xml_paras: List[str] = field(default_factory=list)  # Lưu xml nguyên bản để tái tạo chính xác 100%


@dataclass
class ExamSection:
    """Một phần thi (VD: Phần I: Trắc nghiệm 4 lựa chọn, Phần II: Tự luận)."""
    title: str
    questions: List[ExamQuestion] = field(default_factory=list)


@dataclass
class ShuffledExamCode:
    """Một mã đề sau khi đã trộn (câu hỏi + đáp án)."""
    code: str                           # Mã đề: "101", "102"...
    sections: List[ExamSection] = field(default_factory=list)
    # answer_key: {1: "B", 2: "A", 3: "D", ...}
    answer_key: Dict[int, str] = field(default_factory=dict)
    # mapping: {câu_mới: câu_cũ} để tra cứu đối chiếu
    question_map: Dict[int, int] = field(default_factory=dict)
    # mapping chi tiết phương án: {câu_mới: {'A': 'B', 'B': 'A', ...}}
    option_map: Dict[int, Dict[str, str]] = field(default_factory=dict)
