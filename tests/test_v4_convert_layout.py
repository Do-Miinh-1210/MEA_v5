"""Regression tests for the V4 Convert UI layout."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path

import pytest

from core.models import Question
from ui.tab_convert import TabConvert


def _question(index: int) -> Question:
    return Question(
        qtype="TN",
        level="NB",
        topic="Chủ đề",
        question=f"Câu hỏi số {index}",
        options={"A": "A", "B": "B", "C": "C", "D": "D"},
        answer="A",
    )


def test_ai_text_question_table_is_usable_at_minimum_window_size():
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk display is unavailable: {exc}")

    try:
        root.geometry("860x600")
        view = TabConvert(
            root,
            get_subject_grade=lambda: ("Toán", "12"),
        )
        view.pack(fill="both", expand=True)
        view._mode_var.set("ai_text")
        view._on_mode_change()
        root.update_idletasks()
        root.update()

        view._show_parsed_questions_direct([_question(i) for i in range(1, 11)])
        root.update_idletasks()
        root.update()

        panes = view._ai_result_panes.panes()
        assert len(panes) == 2
        assert view._ai_q_tree.winfo_ismapped()
        assert view._ai_result_panes.winfo_width() >= 350
        assert view._ai_q_panel.winfo_height() >= 240
        assert view._ai_q_tree.winfo_height() >= 160
        assert view._ai_output_panel.winfo_height() >= 170
        assert view._ai_q_tree.bind("<Double-1>")

        root_right = root.winfo_rootx() + root.winfo_width()
        root_bottom = root.winfo_rooty() + root.winfo_height()
        for button in (
            view._prompt_copy_btn,
            view._ai_load_text_btn,
            view._ai_invoke_btn,
            view._ai_convert_btn,
            view._ai_direct_export_btn,
            view._ai_nhch_btn,
            view._ai_copy_btn,
            view._ai_copy_latex_btn,
            view._ai_export_latex_btn,
            view._ai_status_lbl,
        ):
            assert button.winfo_ismapped()
            assert button.winfo_rootx() + button.winfo_width() <= root_right
            assert button.winfo_rooty() + button.winfo_height() <= root_bottom
    finally:
        root.destroy()


def test_ai_text_source_exposes_mixed_parser_and_latex_actions():
    source = (Path(__file__).resolve().parents[1] / "ui" / "tab_convert.py").read_text(
        encoding="utf-8"
    )

    assert "from core.exam_file_loader import parse_questions_from_text" in source
    assert "def _ai_text_load_files" in source
    assert "askopenfilenames" in source
    assert "*.tex *.txt *.docx *.html *.htm" in source
    assert "Copy LaTeX" in source
    assert "Xuất LaTeX" in source
    assert "format_questions_ex_test" in source
    assert "export_to_latex" in source
