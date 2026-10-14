"""
tests/test_tab_shuffle_standalone.py — Kiểm tra Tab Trộn đề hoạt động độc lập
không phụ thuộc vào các thư viện đã bị exclude khi đóng gói (cv2, numpy, customtkinter, matplotlib).
"""
import sys
import pytest


def test_tab_shuffle_loads_without_excluded_dependencies():
    # Giả lập môi trường EXE đã exclude các thư viện nặng
    sys.modules['cv2'] = None
    sys.modules['numpy'] = None
    sys.modules['customtkinter'] = None
    sys.modules['matplotlib'] = None

    # omr_exam models & exporter & shuffler phải import được
    from omr_exam.models import ExamSection, ExamQuestion, OptionItem, ShuffledExamCode
    from omr_exam.docx_parser import parse_exam_docx
    from omr_exam.exam_shuffler import shuffle_exam
    from omr_exam.docx_exporter import export_shuffled_exams_to_docx
    from omr_exam.excel_exporter import export_exam_keys_and_matrix_to_excel
    from omr_exam.docx_shuffler_xml import preview_shuffled_keys, shuffle_docx_with_full_xml_preservation

    assert ExamSection is not None
    assert callable(parse_exam_docx)
    assert callable(shuffle_exam)
    assert callable(export_shuffled_exams_to_docx)

    # ui.tab_shuffle phải import được mà không báo lỗi
    from ui.tab_shuffle import TabShuffle, LoadedExamItem
    assert TabShuffle is not None
    assert LoadedExamItem is not None


def test_tab_shuffle_instantiation_without_excluded_dependencies():
    import tkinter as tk
    from tkinter import ttk

    # Mock exclusions
    sys.modules['cv2'] = None
    sys.modules['numpy'] = None
    sys.modules['customtkinter'] = None
    sys.modules['matplotlib'] = None

    try:
        root = tk.Tk()
        root.withdraw()
    except Exception:
        pytest.skip("Không có môi trường hiển thị GUI Tkinter")

    try:
        nb = ttk.Notebook(root)
        from ui.tab_shuffle import TabShuffle
        tab = TabShuffle(nb)
        assert tab is not None
        assert hasattr(tab, "_on_choose_docx")
        assert hasattr(tab, "_on_do_shuffle")
    finally:
        root.destroy()
