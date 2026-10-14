"""Guard rails for V4 result/matrix workflows migrated into V5 Exam Create."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_exam_create_ports_v4_matrix_template_and_export_workflows():
    source = _source("v5/views/exam_create.py")

    assert "def _open_template_library" in source
    assert "from services.matrix_templates import list_templates, load_template" in source
    assert "load_template(template_id)" in source
    assert "def _export_matrix" in source
    assert "export_matrix_csv" in source
    assert "export_matrix_docx" in source
    assert "def _current_matrix_data" in source


def test_exam_create_ports_v4_analyze_exam_to_matrix_workflow():
    source = _source("v5/views/exam_create.py")
    dialog_source = _source("v5/analyze_exam.py")

    assert "def _open_analyze_exam" in source
    assert "from v5.analyze_exam import AnalyzeExamDialog" in source
    assert "Phân tích đề" in source
    assert "parse_exam_file" in dialog_source
    assert "parse_ai_matrix_response" in dialog_source
    assert "export_matrix_docx" in dialog_source


def test_exam_create_ports_v4_post_generate_actions():
    source = _source("v5/views/exam_create.py")

    assert "def _run_post_generate_export" in source
    assert "from services.auto_export import auto_export_exam" in source
    assert "from services.auto_export import save_extra_copy" in source
    assert "def _remember_export_path" in source
    assert "def _relocate_export" in source
    assert "def _disable_auto_export" in source
    assert "def _save_exam_to_nhch" in source
    assert "from storage.database import save_questions" in source
    assert '("tab_bank", self._bank_btn' in source


def test_exam_create_exposes_nhch_source_ratio_controls():
    source = _source("v5/views/exam_create.py")

    assert 'values=["AI mới", "100% NHCH", "Kết hợp"]' in source
    assert "self._source_ratio_slider" in source
    assert '"100% NHCH": "bank_only"' in source
    assert '"Kết hợp": "mixed"' in source
    assert "generate_exam_with_source" in source
    assert "bank_ratio=source_ratio" in source
    assert "NHCH thiếu câu phù hợp" in source


def test_exam_create_ports_v4_multi_code_export_options():
    source = _source("v5/views/exam_create.py")

    assert "def _export_multi_code" in source
    assert "def _do_export_multi" in source
    assert "from export.word_exporter import export_multi_code" in source
    assert "shuffle_questions" in source
    assert "shuffle_answers" in source
    assert "include_solution" in source
    assert "variant_mode" in source
    assert "progress_cb=_progress" in source
    assert "PromptPreviewDialog" in source
    assert "random.shuffle(ex.questions)" not in source
    assert "export_to_word(ex" not in source


def test_exam_create_ports_v4_load_exam_file_workflow_without_v4_ui():
    source = _source("v5/views/exam_create.py")

    assert "def _load_exam_from_file" in source
    assert "from core.exam_file_loader import load_exam_from_file" in source
    assert "def _populate_exam_from_loaded" in source
    assert "def _offer_ai_fallback_for_loaded_file" in source
    assert "build_text_normalize_prompt" in source
    assert "parse_text_questions" in source
    assert "DOCX/PDF/TeX/TXT/HTML" in source
    assert "ui.tab_convert" not in source
    assert "from ui." not in source
    assert "import ui." not in source


def test_exam_create_ports_v4_exam_metadata_dialog():
    source = _source("v5/views/exam_create.py")

    assert "self._meta_btn" in source
    assert "def _open_exam_metadata_dialog" in source
    assert "exam.school = school_var.get().strip()" in source
    assert "exam.teacher = teacher_var.get().strip()" in source
    assert "set_school_info" in source
    assert "_publish_exam_change()" in source
    assert "_sync_result_action_state()" in source
    assert "ui.tab_result" not in source


def test_exam_create_ports_v4_export_settings_dialog():
    source = _source("v5/views/exam_create.py")
    config_source = _source("config.py")

    assert "self._export_settings_btn" in source
    assert "self._include_solution_var" in source
    assert "self._include_solution_check" in source
    assert "self._auto_table_var" in source
    assert "self._auto_table_check" in source
    assert "def _open_export_settings_dialog" in source
    assert "def _set_include_solutions_from_quick_toggle" in source
    assert "def _set_auto_convert_tables_from_quick_toggle" in source
    assert "set_word_math_mode" in source
    assert "set_word_auto_convert_tables_enabled" in source
    assert "set_export_solution_enabled" in source
    assert "set_open_after_export_enabled" in source
    assert "Kèm ĐA/LG" in source
    assert "self._include_solution_var.set(bool(include_sol_var.get()))" in source
    assert "self._auto_table_var.set(bool(auto_table_var.get()))" in source
    assert "math_mode=self._word_math_mode()" in source
    assert "auto_convert_tables=self._word_auto_convert_tables()" in source
    assert "include_solution=self._include_solutions_on_export()" in source
    assert "open_after=self._open_after_export_enabled()" in source
    assert "def get_word_math_mode" in config_source
    assert "def is_word_auto_convert_tables_enabled" in config_source
    assert "def is_export_solution_enabled" in config_source
    assert "def is_open_after_export_enabled" in config_source
    assert "ui.tab_result" not in source


def test_exam_create_ports_v4_quick_include_solution_toggle():
    source = _source("v5/views/exam_create.py")

    assert "self._include_solution_var = ctk.BooleanVar" in source
    assert "self._include_solution_check = ctk.CTkCheckBox" in source
    assert "variable=self._include_solution_var" in source
    assert "command=self._set_include_solutions_from_quick_toggle" in source
    assert "def _set_include_solutions_from_quick_toggle" in source
    assert "set_export_solution_enabled(enabled)" in source
    assert "include_solution=self._include_solutions_on_export()" in source
    assert "Kèm ĐA/LG" in source
    assert "from ui." not in source


def test_exam_create_ports_v4_qc_current_exam_workflow():
    source = _source("v5/views/exam_create.py")
    qc_source = _source("v5/views/qc.py")
    app_source = _source("v5/app.py")

    assert "self._qc_current_btn" in source
    assert "def _open_qc_current_exam" in source
    assert 'self._on_navigate("qc")' in source
    assert "self._sync_preview_questions_to_exam()" in source
    assert "initial_exam: Any | None" in qc_source
    assert "get_current_exam: Callable[[], Any | None]" in qc_source
    assert "def _load_from_current_exam" in qc_source
    assert "def _load_exam_questions" in qc_source
    assert "Load đề hiện tại" in qc_source
    assert 'kwargs["initial_exam"] = self._workspace.current_exam' in app_source
    assert 'kwargs["get_current_exam"] = lambda: self._workspace.current_exam' in app_source
    assert "from ui." not in source
    assert "from ui." not in qc_source


def test_exam_create_ports_v4_score_and_error_report_actions():
    source = _source("v5/views/exam_create.py")

    assert "self._score_check_btn" in source
    assert "self._error_report_btn" in source
    assert "def _question_score_value" in source
    assert "def _check_result_score" in source
    assert "def _export_error_report" in source
    assert '"📋  Báo cáo lỗi ({failed_count})"' in source
    assert 'snapshot.get("points")' in source
    assert "POINTS_MAP.get(qtype, 0.25)" in source
    assert "bao_cao_loi_v5.txt" in source
    assert "output_path.write_text" in source
    assert "from ui." not in source


def test_preferences_exposes_v4_auto_export_settings():
    source = _source("v5/preferences.py")

    assert "Tự xuất Word ngay sau khi sinh đề" in source
    assert "is_auto_export_enabled" in source
    assert "set_auto_export_enabled" in source
    assert "is_word_auto_convert_tables_enabled" in source
    assert "set_word_auto_convert_tables_enabled" in source
    assert "self._auto_table_var" in source
    assert "get_auto_export_dir" in source
    assert "set_auto_export_dir" in source
    assert "def _pick_auto_export_dir" in source
    assert "def _open_auto_export_dir" in source


def test_exam_create_result_preview_and_toolbar_are_responsive():
    source = _source("v5/views/exam_create.py")

    assert "minwidths_pv" in source
    assert 'stretch=(c in ("topic", "preview"))' in source
    assert "pv_wrap.grid_rowconfigure(2, weight=0)" in source
    assert ').grid(row=2, column=0, columnspan=2, sticky="ew"' in source
    assert "media_row.grid_columnconfigure(6, weight=1)" in source
    assert "self._tikz_mode_menu.grid(row=0, column=0" in source
    assert "self._tikz_emf_btn.grid(row=0, column=1" in source
    assert "self._error_report_btn.grid(row=0, column=5" in source
    assert "self._tikz_emf_status.grid(row=1, column=0, columnspan=7" in source
