"""Unit tests for native V5 Convert business helpers."""
from __future__ import annotations

from pathlib import Path

from core.models import Question
from v5.convert_pipeline import (
    assign_ids_for_save,
    build_chatbot_prompt,
    build_text_normalize_prompt,
    chatbot_prompt_catalog,
    combine_results,
    get_chatbot_prompt_template,
    parse_text_questions,
    rewrite_prompt_and_tikz_text,
    rewrite_tikz_blocks_in_text,
)


ROOT = Path(__file__).resolve().parents[1]


def test_parse_text_questions_prefers_structured_blocks():
    text = """===CAU===
LOAI: TN
MUCDO: NB
CHUONG: Dao ham
NOIDUNG: Dao ham cua x^2 la gi?
A: 2x
B: x
C: 2
D: 0
DAPAN: A
LOIGIAI: Ap dung cong thuc.
===KETCAU==="""

    questions = parse_text_questions(text)

    assert len(questions) == 1
    assert questions[0].qtype == "TN"
    assert questions[0].answer == "A"


def test_parse_text_questions_supports_natural_question_text():
    questions = parse_text_questions(
        "Cau 1: Gia tri cua 2 + 2 la?\n"
        "A. 3\nB. 4\nC. 5\nD. 6\n"
        "Dap an: B"
    )

    assert len(questions) == 1
    assert questions[0].options["B"] == "4"


def test_parse_text_questions_supports_latex_and_mixed_structures():
    latex = r"""\begin{ex}
Latex question?
\choice{\True A}{B}{C}{D}
\end{ex}"""
    app = """===CAU===
LOAI: TL
NOIDUNG: App question?
LOIGIAI: Solution.
===KETCAU==="""

    questions = parse_text_questions(f"{latex}\n\n{app}")

    assert [question.question for question in questions] == [
        "Latex question?",
        "App question?",
    ]


def test_combine_results_joins_questions_warnings_and_latest_meta():
    first = Question(qtype="TN", level="NB", topic="", question="A")
    second = Question(qtype="TLN", level="TH", topic="", question="B")
    result = combine_results(
        [
            {"questions": [first], "warnings": ["w1"], "meta": {"subject": "Toan"}, "method": "image"},
            {"questions": [second], "warnings": [], "meta": {"grade": "11"}, "method": "text-layer"},
        ]
    )

    assert result["questions"] == [first, second]
    assert result["warnings"] == ["w1"]
    assert result["meta"]["grade"] == "11"
    assert result["methods"] == ["image", "text-layer"]


def test_assign_ids_for_save_only_replaces_temporary_ids():
    pending = Question(qtype="TN", level="NB", topic="Dai so", question="A")
    existing = Question(
        qtype="TN",
        level="NB",
        topic="Dai so",
        question="B",
        question_id="EXISTING-ID",
    )

    assign_ids_for_save([pending, existing], "12")

    assert not pending.question_id.startswith("QID-")
    assert existing.question_id == "EXISTING-ID"


def test_assign_ids_for_save_keeps_new_ids_unique():
    first = Question(qtype="TN", level="NB", topic="Dai so", question="A")
    second = Question(qtype="TN", level="NB", topic="Dai so", question="B")

    assign_ids_for_save([first, second], "12")

    assert first.question_id != second.question_id


def test_build_text_normalize_prompt_includes_source_text():
    prompt = build_text_normalize_prompt("Cau 1: noi dung")

    assert "===CAU===" in prompt
    assert "Cau 1: noi dung" in prompt


def test_chatbot_prompt_catalog_covers_gemini_chatgpt_deepseek_variants():
    catalog = chatbot_prompt_catalog()
    families = {item["family"] for item in catalog}
    ids = {item["id"] for item in catalog}

    assert len(catalog) >= 14
    assert {"Gemini GEM", "ChatGPT", "DeepSeek"}.issubset(families)
    assert {"gemini_gem_master", "chatgpt_standard", "deepseek_reasoner_math"}.issubset(ids)
    assert all(item["label"].startswith(item["family"]) for item in catalog)


def test_build_chatbot_prompt_includes_template_context_and_app_format():
    prompt = build_chatbot_prompt(
        "chatgpt_reasoned_solution",
        subject="Toán",
        grade="11",
        topic="Cấp số nhân",
        count="6",
        qtype="TN",
        level="VD",
        extra="có 2 câu thực tế",
    )

    assert "ChatGPT - Lời giải chất lượng cao" in prompt
    assert "- Lớp/phạm vi: 11" in prompt
    assert "- Chủ đề: Cấp số nhân" in prompt
    assert "- Số câu: 6" in prompt
    assert "- Loại câu ưu tiên: TN" in prompt
    assert "có 2 câu thực tế" in prompt
    assert "ĐỊNH DẠNG BẮT BUỘC CHO MATRIXEXAMAI" in prompt
    assert "DANH SÁCH KIỂM TRA TRƯỚC KHI TRẢ LỜI" in prompt
    assert "===CAU===" in prompt
    assert "LOAI: TN" in prompt
    assert "LOAI: DS" in prompt
    assert "LOAI: TLN" in prompt
    assert "LOAI: TL" in prompt
    assert "Hãy bắt đầu ngay bằng ===CAU===" in prompt


def test_chatbot_prompt_defaults_to_template_type_and_safe_fallback():
    prompt = build_chatbot_prompt("deepseek_tln_numeric", count="bad", qtype="auto", level="auto")
    fallback = get_chatbot_prompt_template("missing-template-id")

    assert "- Số câu: 10" in prompt
    assert "- Loại câu ưu tiên: TLN" in prompt
    assert "- Mức độ ưu tiên: VD" in prompt
    assert fallback["id"] == "gemini_gem_master"


def test_chatbot_prompt_defaults_to_accented_vietnamese_without_mode_switch():
    prompt = build_chatbot_prompt("gemini_gem_master")

    assert "VAI TRÒ / MODEL:" in prompt
    assert "NHIỆM VỤ:" in prompt
    assert "- Môn: Toán" in prompt
    assert "- Lớp/phạm vi: 1-12" in prompt
    assert "- Lớp/phạm vi: 12" not in prompt
    assert "- Chủ đề: chủ đề giáo viên cung cấp" in prompt
    assert "- Yêu cầu thêm: Không." in prompt
    assert "VAI TRO / MODEL:" not in prompt
    assert "THONG TIN DE TAO:" not in prompt
    assert "GEM MASTER MATRIXEXAMAI" in prompt
    assert "Chế độ A - Tạo đề tương tự từ file" in prompt
    assert "Chế độ A' - Chuyển đề về cấu trúc app" in prompt
    assert "DS dùng D/S không dấu" in prompt
    assert "TIKZ VÀ HÌNH VẼ" in prompt


def test_rewrite_prompt_and_tikz_text_builds_single_gem_prompt_and_cleans_tikz():
    source = r"""Hay tao cau hoi co hinh.
\begin{tikzpicture}
\begin{axis}
\addplot {2x+1};
\end{axis}
\end{tikzpicture}
"""

    rewritten = rewrite_prompt_and_tikz_text(source)

    assert "GEM MASTER MATRIXEXAMAI" in rewritten
    assert "PROMPT NGUON CAN VIET LAI" in rewritten
    assert r"\addplot {2*x+1};" in rewritten


def test_rewrite_tikz_blocks_keeps_structured_blocks_parseable():
    source = r"""===CAU===
LOAI: TL
NOIDUNG: \begin{tikzpicture}
\begin{axis}
\addplot {3x};
\end{axis}
\end{tikzpicture}
===KETCAU==="""

    rewritten = rewrite_tikz_blocks_in_text(source)

    assert rewritten.startswith("===CAU===")
    assert r"\addplot {3*x};" in rewritten


def test_convert_view_exposes_chatbot_prompt_suggestions():
    source = (ROOT / "v5" / "views" / "convert.py").read_text(encoding="utf-8")
    dialog_source = (ROOT / "v5" / "variant_dialog.py").read_text(encoding="utf-8")

    assert "chatbot_prompt_catalog" in source
    assert "build_chatbot_prompt" in source
    assert "_copy_chatbot_prompt" in source
    assert "_copy_gem_master_prompt" in source
    assert "_rewrite_prompt_tikz_locally" in source
    assert "MODEL_OPTIONS" in source
    assert "self._model_menu = ctk.CTkOptionMenu" in source
    assert "self._model_menu.configure(values=values)" in source
    assert "rewrite_prompt_and_tikz_text" in source
    assert "_preview_chatbot_prompt" in source
    assert "Gemini GEM / ChatGPT / DeepSeek" in source
    assert "Prompt gợi ý ChatBotAI" in source
    assert "short_title = title if len(title) <= 28" in source
    assert "container.grid_rowconfigure(2, weight=1)" in source
    assert "self._text_input.grid(row=2" in source
    assert "buttons.grid(row=3" in source
    assert 'cols = ("no", "kind", "topic", "question")' in source
    assert '"Loại/Mức"' in source
    assert 'kind = f"{qtype}/{level}"' in source
    assert 'cols = ("no", "qtype", "level", "topic", "question")' not in source
    assert 'actions.grid_columnconfigure((0, 1, 2), weight=1' in source
    assert 'self._add_btn.grid(row=1, column=2, sticky="ew"' in source
    assert 'self._add_btn.pack(side="left"' not in source
    assert "Copy LaTeX" in source
    assert "Xuất LaTeX" in source
    assert "askopenfilenames" in source
    assert "*.tex" in source
    assert "format_questions_ex_test" in source
    assert "export_to_latex" in source
    assert "title: str | None = None" in dialog_source
    assert "intro: str | None = None" in dialog_source


def test_convert_result_table_keeps_horizontal_scroll_for_long_content():
    source = (ROOT / "v5" / "views" / "convert.py").read_text(encoding="utf-8")

    assert 'hscroll = ttk.Scrollbar(table, orient="horizontal"' in source
    assert "xscrollcommand=hscroll.set" in source
    assert 'hscroll.grid(row=1, column=0, sticky="ew")' in source
    assert "table.grid_rowconfigure(1, weight=0)" in source
    assert 'actions.grid_columnconfigure((0, 1, 2), weight=1' in source
