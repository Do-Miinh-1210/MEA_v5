"""
omr_exam/__init__.py — Package entry point for Exam Shuffle & OMR Auto-Grading System.
"""
from omr_exam.models import ExamQuestion, OptionItem, ExamSection, ShuffledExamCode
from omr_exam.docx_parser import parse_exam_docx
from omr_exam.exam_shuffler import shuffle_exam
from omr_exam.docx_exporter import export_shuffled_exams_to_docx
# Các module chấm OMR bằng camera (tùy chọn — không block tính năng Trộn đề khi thiếu numpy/cv2)
try:
    from omr_exam.sheet_generator import generate_omr_sheet_image
except Exception:
    generate_omr_sheet_image = None

try:
    from omr_exam.omr_grader import grade_omr_sheet, align_omr_sheet, ExamGradingReport
except Exception:
    grade_omr_sheet = None
    align_omr_sheet = None
    ExamGradingReport = None

try:
    from omr_exam.camera_usb import USBCameraManager
except Exception:
    USBCameraManager = None

__all__ = [
    "ExamQuestion",
    "OptionItem",
    "ExamSection",
    "ShuffledExamCode",
    "parse_exam_docx",
    "shuffle_exam",
    "export_shuffled_exams_to_docx",
    "generate_omr_sheet_image",
    "grade_omr_sheet",
    "align_omr_sheet",
    "ExamGradingReport",
    "USBCameraManager",
]
