"""Guard rails for V5 per-question LaTeX preview."""
from __future__ import annotations

from pathlib import Path

from core.models import Question
from v5.latex_preview import question_to_latex, render_question_latex


ROOT = Path(__file__).resolve().parents[1]


def test_question_to_latex_formats_tn_answer_and_math_text():
    question = Question(
        qtype="TN",
        level="TH",
        topic="Đạo hàm",
        question="Tính ${x+1}$ khi a & b đạt 10%.",
        options={"A": "1", "B": "${2}$", "C": "3", "D": "4"},
        answer="B",
        solution="Vì ${x=1}$.",
    )

    latex = question_to_latex(question, 2)

    assert r"\textbf{Câu 3.}" in latex
    assert "$x+1$" in latex
    assert r"a \& b đạt 10\%." in latex
    assert r"\item $2$ \quad $\Leftarrow$ \textbf{ĐÁP ÁN}" in latex
    assert r"\noindent\textbf{Lời giải:}" in latex


def test_question_to_latex_formats_ds_verdicts_and_item_solutions():
    question = Question(
        qtype="DS",
        level="NB",
        topic="Hàm số",
        question="Xét các mệnh đề.",
        items={"a": "Mệnh đề a", "b": "Mệnh đề b"},
        answers={"a": True, "b": False},
        item_solutions={"a": "Đúng vì A", "b": "Sai vì B"},
    )

    latex = question_to_latex(question, 0)

    assert r"\textbf{a.} Mệnh đề a \hfill \textbf{(Đ)}" in latex
    assert r"\textbf{b.} Mệnh đề b \hfill \textbf{(S)}" in latex
    assert r"\textbf{a.} Đúng vì A" in latex
    assert r"\textbf{b.} Sai vì B" in latex


def test_render_question_latex_uses_shared_pdf_renderer(monkeypatch, tmp_path):
    from services import pdf_renderer

    captured: dict[str, object] = {}
    sentinel = object()

    def fake_compile(source: str, workdir=None, timeout=0):
        captured["source"] = source
        captured["workdir"] = workdir
        captured["timeout"] = timeout
        pdf_path = Path(workdir or tmp_path) / "figure.pdf"
        pdf_path.write_bytes(b"%PDF")
        return str(pdf_path)

    def fake_render(pdf_path: str, page: int = 0, dpi: int = 150):
        captured["pdf_path"] = pdf_path
        captured["page"] = page
        captured["dpi"] = dpi
        return sentinel

    monkeypatch.setattr(pdf_renderer, "compile_latex_to_pdf", fake_compile)
    monkeypatch.setattr(pdf_renderer, "render_pdf_page", fake_render)

    question = Question(qtype="TLN", level="TH", topic="Số học", question="Tính.", answer="42")
    image = render_question_latex(question, 0, dpi=180)

    assert image is sentinel
    assert r"\documentclass" in str(captured["source"])
    assert r"\textbf{Đáp số:} 42" in str(captured["source"])
    assert captured["timeout"] == 45
    assert captured["page"] == 0
    assert captured["dpi"] == 180


def test_exam_create_wires_latex_preview_without_v4_ui():
    source = (ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")
    preview_source = (ROOT / "v5" / "latex_preview.py").read_text(encoding="utf-8")
    cards_source = (ROOT / "v5" / "question_cards.py").read_text(encoding="utf-8")

    assert "on_latex=self._preview_question_latex" in source
    assert "def _preview_question_latex" in source
    assert "from v5.latex_preview import LatexPreviewDialog" in source
    assert "on_latex: Callable[[int], None]" in cards_source
    assert 'text="👁 LaTeX"' in cards_source
    assert "from ui." not in preview_source
    assert "import ui." not in preview_source
