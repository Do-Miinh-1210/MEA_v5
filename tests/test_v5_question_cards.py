"""Guard rails for V5 full question preview cards and TikZ-to-EMF action."""
from __future__ import annotations

from pathlib import Path
import zipfile

from PIL import Image

from core.models import ExamData, Question
from v5.question_cards import (
    answer_lines,
    clone_question_for_edit,
    image_rows,
    pending_tikz_count,
)


ROOT = Path(__file__).resolve().parents[1]


def test_question_card_lines_show_tn_answers_and_ds_verdicts():
    tn = Question(
        qtype="TN", level="NB", topic="Đạo hàm", question="Chọn đáp án.",
        options={"A": "1", "B": "2", "C": "3", "D": "4"}, answer="B",
    )
    ds = Question(
        qtype="DS", level="TH", topic="Hàm số", question="Xét đúng sai.",
        items={"a": "Mệnh đề a", "b": "Mệnh đề b"},
        answers={"a": True, "b": False},
    )

    assert answer_lines(tn)[1] == ("B", "2", True)
    assert answer_lines(ds) == [
        ("a", "Mệnh đề a", True),
        ("b", "Mệnh đề b", False),
    ]


def test_question_card_lists_png_slots_and_pending_tikz():
    question = Question(
        qtype="TL", level="VD", topic="Hình học",
        question=r"Cho hình sau. \begin{tikzpicture}\draw (0,0)--(1,0);\end{tikzpicture}",
        question_image="q.png",
        solution_image="sol.png",
        option_images={"A": "opt.png"},
        item_images={"a": "item.png"},
    )

    assert pending_tikz_count(question) == 1
    assert image_rows(question) == [
        ("Hình câu hỏi", "q.png"),
        ("Hình đáp án A", "opt.png"),
        ("Hình ý a", "item.png"),
        ("Hình lời giải", "sol.png"),
    ]


def test_question_card_pending_tikz_warning_matches_conversion_menu():
    source = (ROOT / "v5" / "question_cards.py").read_text(encoding="utf-8")

    assert "menu TikZ" in source
    assert "sang EMF" not in source


def test_exam_create_wires_full_card_preview_and_editor_callback():
    source = (ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")
    cards_source = (ROOT / "v5" / "question_cards.py").read_text(encoding="utf-8")

    assert "from v5.question_cards import QuestionCardsPanel" in source
    assert "self._question_cards.set_questions(self._generated_questions)" in source
    assert "def _open_preview_question" in source
    assert "Nội dung, đáp án, lời giải và ảnh PNG" in source
    assert "class QuestionCardsPanel" in cards_source
    assert "ui.tab_result" not in source


def test_clone_question_for_edit_creates_clean_copy():
    original = Question(
        qtype="TN",
        level="TH",
        topic="Hàm số",
        question="Câu gốc",
        options={"A": "1", "B": "2"},
        answer="A",
    )
    original._review = {"ok": False}
    original._error = True
    original._error_msg = "Lỗi cũ"
    original._row_snapshot = {"topic": "Hàm số", "points": 0.25}

    cloned = clone_question_for_edit(original)

    assert cloned is not original
    assert cloned.question == original.question
    assert cloned.question_id != original.question_id
    assert cloned._review is None
    assert cloned._error is False
    assert cloned._error_msg == ""
    assert cloned._row_snapshot == original._row_snapshot


def test_exam_create_wires_quick_edit_toolbar_for_result_questions():
    source = (ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")

    assert "self._question_jump_var" in source
    assert "self._quick_edit_btn" in source
    assert "self._duplicate_question_btn" in source
    assert "self._insert_blank_question_btn" in source
    assert "def _jump_to_preview_question" in source
    assert "def _edit_selected_preview_question" in source
    assert "def _duplicate_preview_question" in source
    assert "def _insert_blank_preview_question" in source
    assert "def _make_blank_preview_question" in source
    assert "clone_question_for_edit" in source
    assert "Câu trống" in source
    assert "Nhân bản để sửa" in source
    assert "from ui." not in source


def test_v5_question_editor_uses_multiline_answer_fields_for_long_data():
    source = (ROOT / "v5" / "edit_question.py").read_text(encoding="utf-8")

    assert "self._q_text = ctk.CTkTextbox(self._left, height=160" in source
    assert "self._sol_text = ctk.CTkTextbox(self._left, height=170" in source
    assert "ent = ctk.CTkTextbox(row, height=52" in source
    assert "ent = ctk.CTkTextbox(row, height=56" in source
    assert "def _get_text_widget" in source
    assert "def _set_text_widget" in source
    assert "self._get_text_widget(e)" in source
    assert 'self._set_text_widget(ent, opts.get(k, "") or "")' in source
    assert 'self._set_text_widget(ent, items.get(k, "") or "")' in source
    assert "from ui." not in source


def test_exam_create_wires_card_move_and_delete_actions():
    source = (ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")
    cards_source = (ROOT / "v5" / "question_cards.py").read_text(encoding="utf-8")

    assert "on_move=self._move_preview_question" in source
    assert "on_delete=self._delete_preview_question" in source
    assert "def _move_preview_question" in source
    assert "def _delete_preview_question" in source
    assert "def _sync_preview_questions_to_exam" in source
    assert "self._exam.questions = list(self._generated_questions)" in source
    assert "del self._generated_questions[idx]" in source
    assert "on_move: Callable[[int, int], None]" in cards_source
    assert "on_delete: Callable[[int], None]" in cards_source
    assert 'text="↑"' in cards_source
    assert 'text="↓"' in cards_source
    assert 'text="✕"' in cards_source


def test_exam_create_wires_card_regenerate_action_without_v4_ui():
    source = (ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")
    cards_source = (ROOT / "v5" / "question_cards.py").read_text(encoding="utf-8")

    assert "on_regenerate=self._regenerate_preview_question" in source
    assert "def _regenerate_preview_question" in source
    assert "def _on_regenerate_preview_done" in source
    assert "MatrixRow.from_dict(dict(row_dict))" in source
    assert "generate_one(row, subject, grade, ai_call)" in source
    assert "old_question_id" in source
    assert "on_regenerate: Callable[[int], None]" in cards_source
    assert 'text="🔄 Tạo lại"' in cards_source
    assert "from ui." not in source


def test_exam_create_wires_retry_failed_batch_action_without_v4_ui():
    source = (ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")

    assert "self._retry_failed_btn" in source
    assert "def _failed_question_indexes" in source
    assert "def _retry_failed_preview_questions" in source
    assert "def _on_retry_failed_batch_done" in source
    assert "def _update_retry_failed_progress" in source
    assert "generate_one(row, subject, grade, ai_call)" in source
    assert "self._sync_preview_questions_to_exam()" in source
    assert "Tạo lại lỗi" in source
    assert "from ui." not in source


def test_exam_create_wires_tikz_to_emf_pipeline_without_v4_ui():
    source = (ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")

    assert "self._tikz_mode_menu" in source
    assert "TIKZ_CONVERSION_OPTIONS" in source
    assert "TIKZ_TO_PNG_ACTION_LABEL" in source
    assert "self._tikz_emf_btn" in source
    assert "def _convert_exam_tikz_to_emf" in source
    assert "count_pending_blocks" in source
    assert "convert_exam_tikz_to_emf" in source
    assert "convert_exam_tikz_to_png" in source
    assert "def _on_tikz_emf_done" in source
    assert "TIKZ_TO_EMF_ACTION_LABEL" in source
    assert "get_tikz_conversion_option" in source
    assert "from ui." not in source
    assert "import ui." not in source


def test_tikz_pipeline_emf_keeps_png_preview_in_question_card_slots(monkeypatch, tmp_path):
    from services import figure_bank, tikz_cache, tikz_pipeline

    cache_dir = tmp_path / "tikz_cache"
    cache_dir.mkdir()
    saved: list[dict] = []
    monkeypatch.setattr(tikz_cache, "_CACHE_DIR", cache_dir)
    monkeypatch.setattr(
        figure_bank,
        "save_rendered",
        lambda code, **kwargs: saved.append({"code": code, **kwargs}) or ("001", True),
    )
    monkeypatch.setattr(
        tikz_pipeline,
        "_get_render_fn",
        lambda: lambda _code, dpi=300, return_log=False: (
            (Image.new("RGB", (16, 8), "white"), "", "") if return_log
            else Image.new("RGB", (16, 8), "white")
        ),
    )
    emf_dir = tmp_path / "tikz_emf"
    emf_dir.mkdir()
    monkeypatch.setattr(tikz_pipeline, "_EMF_CACHE_DIR", emf_dir)
    monkeypatch.setattr(
        "services.tikz_vector_export.export_tikz_to_emf",
        lambda _code, target, **_kwargs: Path(target).write_bytes(b"EMF") or Path(target),
    )
    question = Question(
        qtype="TL",
        level="VD",
        topic="Hình học",
        question=(
            r"Cho hình sau. \begin{tikzpicture}"
            r"\draw (0,0)--(1,0); \end{tikzpicture}"
        ),
    )
    exam = ExamData("ĐỀ KIỂM TRA", "Toán", "9", "I", "2025-2026", "90 phút",
                    questions=[question])

    report = tikz_pipeline.process_exam(exam, max_workers=1)
    rows = image_rows(question)

    assert report.ok == 1
    assert report.failed == 0
    assert r"\begin{tikzpicture}" not in question.question
    assert rows[0][0] == "Hình câu hỏi"
    assert Path(rows[0][1]).exists()
    assert "::emf::" in question.question_image
    assert report.emf == 1
    assert report.bank_saved == 1
    assert saved[0]["source"] == "nhch"


def test_tikz_pipeline_png_mode_skips_emf_and_keeps_png_slot(monkeypatch, tmp_path):
    from services import figure_bank, tikz_cache, tikz_pipeline

    cache_dir = tmp_path / "tikz_cache"
    cache_dir.mkdir()
    monkeypatch.setattr(tikz_cache, "_CACHE_DIR", cache_dir)
    monkeypatch.setattr(
        figure_bank,
        "save_rendered",
        lambda code, **kwargs: ("001", True),
    )
    monkeypatch.setattr(
        tikz_pipeline,
        "_get_render_fn",
        lambda: lambda _code, dpi=300, return_log=False: (
            (Image.new("RGB", (16, 8), "white"), "", "") if return_log
            else Image.new("RGB", (16, 8), "white")
        ),
    )
    monkeypatch.setattr(
        "services.tikz_vector_export.export_tikz_to_emf",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("EMF export called")),
    )
    question = Question(
        qtype="TL",
        level="VD",
        topic="Hình học",
        question=(
            r"Cho hình sau. \begin{tikzpicture}"
            r"\draw (0,0)--(1,0); \end{tikzpicture}"
        ),
    )
    exam = ExamData("ĐỀ KIỂM TRA", "Toán", "9", "I", "2025-2026", "90 phút",
                    questions=[question])

    report = tikz_pipeline.process_exam(exam, max_workers=1, output_mode="png")
    rows = image_rows(question)

    assert report.output_mode == "png"
    assert report.ok == 1
    assert report.failed == 0
    assert report.emf == 0
    assert "PNG: 1" in report.summary()
    assert r"\begin{tikzpicture}" not in question.question
    assert rows[0][0] == "Hình câu hỏi"
    assert Path(rows[0][1]).exists()
    assert "::emf::" not in question.question_image


def test_vector_image_field_prefers_emf_for_export_but_png_for_preview():
    from services.image_fields import normalize_image_field, serialize_vector_image

    value = serialize_vector_image("figure.png", "figure.emf")

    assert normalize_image_field(value) == ["figure.png"]
    assert normalize_image_field(value, prefer_vector=True) == [
        "figure.emf",
        "figure.png",
    ]


def test_word_export_embeds_emf_when_vector_slot_exists(tmp_path):
    from export.word_exporter import export_to_word
    from services.image_fields import serialize_vector_image

    png = tmp_path / "figure.png"
    emf = tmp_path / "figure.emf"
    out = tmp_path / "exam.docx"
    Image.new("RGB", (24, 12), "white").save(png)
    emf.write_bytes(b"EMF-test")
    question = Question(
        qtype="TL",
        level="NB",
        topic="TikZ",
        question="Câu có hình vector.",
        question_image=serialize_vector_image(str(png), str(emf)),
    )
    exam = ExamData("ĐỀ", "Toán", "9", "I", "2025-2026", "45 phút",
                    questions=[question])

    export_to_word(exam, str(out))

    with zipfile.ZipFile(out) as archive:
        media = [name for name in archive.namelist()
                 if name.startswith("word/media/")]

    assert any(name.endswith(".emf") for name in media)
    assert not any(name.endswith(".png") for name in media)
