import zipfile
from pathlib import Path

import pytest

docx = pytest.importorskip("docx")

from core.models import ExamData, Question
from export.word_exporter import export_multi_code, export_to_word


pytestmark = pytest.mark.docx


def _build_exam(image_path: str = "") -> ExamData:
    return ExamData(
        exam_title="Đề thi thử tốt nghiệp 2026",
        subject="Toán",
        grade="12",
        semester="HK2",
        year="2025-2026",
        time="90 phút",
        school="SỞ GIÁO DỤC VÀ ĐÀO TẠO AN GIANG",
        teacher="Tổ Toán",
        questions=[
            Question(
                qtype="TN",
                level="NB",
                topic="Hàm số",
                question="Cho hàm số $f(x)=x^2+1$. Giá trị $f(1)$ bằng",
                options={"A": "2", "B": "1", "C": "0", "D": "3"},
                answer="A",
                solution="Ta có $f(1)=1^2+1=2$.",
                question_image=image_path,
                solution_image=image_path,
            ),
            Question(
                qtype="DS",
                level="TH",
                topic="Đạo hàm",
                question="Xét các mệnh đề sau về hàm số $y=x^2$.",
                items={
                    "a": "$y'=2x$",
                    "b": "Hàm số đồng biến trên $\\mathbb{R}$",
                    "c": "$y(0)=0$",
                    "d": "Đồ thị đi qua điểm $(1;1)$",
                },
                answers={"a": True, "b": False, "c": True, "d": True},
                item_solutions={
                    "a": "Đạo hàm đúng.",
                    "b": "Hàm số không đồng biến trên toàn bộ trục số.",
                    "c": "Thay $x=0$ được $0$.",
                    "d": "Thay $x=1$ được $1$.",
                },
            ),
            Question(
                qtype="TLN",
                level="VD",
                topic="Xác suất",
                question="Tính $P(A)$ biết số kết quả thuận lợi là 3 và không gian mẫu có 10 phần tử.",
                answer="0,3",
                solution="$P(A)=\\frac{3}{10}=0,3$.",
            ),
            Question(
                qtype="TL",
                level="VD",
                topic="Tích phân",
                question="Tính tích phân $I=\\int_0^1 2x\\,dx$.",
                answer="1",
                solution="$I=x^2\\big|_0^1=1$.",
                points=1.0,
            ),
        ],
    )


def _doc_text(path: Path) -> str:
    document = docx.Document(str(path))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    table_cells = [
        cell.text
        for table in document.tables
        for row in table.rows
        for cell in row.cells
        if cell.text.strip()
    ]
    return "\n".join(paragraphs + table_cells)


def test_word_export_exam_structure_contains_expected_sections(tmp_path):
    output = tmp_path / "exam.docx"
    export_to_word(_build_exam(), str(output), include_solution=True)

    text = _doc_text(output)

    assert "PHẦN I" in text
    assert "PHẦN II" in text
    assert "PHẦN III" in text
    assert "PHẦN IV" in text
    assert "HẾT" in text
    assert "ĐÁP ÁN THAM KHẢO" in text
    assert "LỜI GIẢI THAM KHẢO" in text
    assert text.index("HẾT") < text.index("ĐÁP ÁN THAM KHẢO")


def test_word_export_header_is_two_column_table(tmp_path):
    output = tmp_path / "exam.docx"
    export_to_word(_build_exam(), str(output), include_solution=False)

    document = docx.Document(str(output))
    header = document.tables[0]
    header_text = "\n".join(cell.text for row in header.rows for cell in row.cells)

    assert len(header.columns) == 2
    assert "SỞ GIÁO DỤC VÀ ĐÀO TẠO AN GIANG" in header_text
    assert "Môn thi: TOÁN" in header_text
    assert "Thời gian làm bài 90 phút" in header_text


def test_word_export_answer_tables_are_present(tmp_path):
    output = tmp_path / "exam.docx"
    export_to_word(_build_exam(), str(output), include_solution=True)

    document = docx.Document(str(output))
    table_texts = [
        "\n".join(cell.text for row in table.rows for cell in row.cells)
        for table in document.tables
    ]

    assert any("Đáp án" in text and "A" in text for text in table_texts)
    assert any("a" in text and "Đ" in text and "S" in text for text in table_texts)
    assert any("Đáp số" in text and "0,3" in text for text in table_texts)


def test_word_export_can_disable_auto_pipe_tables(tmp_path):
    exam = _build_exam()
    exam.questions = [
        Question(
            qtype="TL",
            level="VD",
            topic="Vector",
            question=(
                "Bảng biến thiên:\n\n"
                "| $x$ | $-\\infty$ | $0$ | $+\\infty$ |\n"
                "|---|---|---|---|\n"
                "| $y$ | 1 | 2 | 3 |\n\n"
                "Done."
            ),
            answer="\\sqrt{11}",
            solution="",
        )
    ]

    auto_output = tmp_path / "auto_table.docx"
    plain_output = tmp_path / "plain_text.docx"
    export_to_word(exam, str(auto_output), include_solution=False, auto_convert_tables=True)
    export_to_word(exam, str(plain_output), include_solution=False, auto_convert_tables=False)

    auto_doc = docx.Document(str(auto_output))
    plain_doc = docx.Document(str(plain_output))
    plain_text = _doc_text(plain_output)

    assert len(auto_doc.tables) > len(plain_doc.tables)
    assert len(plain_doc.tables) == 1
    assert "Bảng biến thiên" in plain_text
    assert "\\infty" in plain_text


def test_word_export_embeds_images_and_omml(tmp_path):
    Image = pytest.importorskip("PIL.Image")
    pytest.importorskip("latex2mathml.converter")

    image = tmp_path / "chart.png"
    Image.new("RGB", (120, 80), color=(255, 255, 255)).save(image)
    output = tmp_path / "exam.docx"

    export_to_word(_build_exam(str(image)), str(output), include_solution=True, math_mode="equation")

    with zipfile.ZipFile(output) as zf:
        names = zf.namelist()
        document_xml = zf.read("word/document.xml").decode("utf-8")

    assert any(name.startswith("word/media/") for name in names)
    assert "<m:oMath" in document_xml or "officeDocument/2006/math" in document_xml


def test_export_multi_code_creates_docs_and_answer_key(tmp_path):
    output_dir = tmp_path / "multi"

    files = export_multi_code(
        _build_exam(),
        str(output_dir),
        n_codes=2,
        include_solution=True,
        shuffle_questions=True,
        shuffle_answers=True,
    )

    assert len(files) == 3
    doc_paths = [Path(p) for p in files if p.endswith(".docx")]
    answer_paths = [Path(p) for p in files if p.endswith(".txt")]
    assert [p.name for p in doc_paths] == ["De_Toán12_MaA.docx", "De_Toán12_MaB.docx"]
    assert answer_paths == [output_dir / "Bang_dap_an_Toán12.txt"]

    first_text = _doc_text(doc_paths[0])
    second_text = _doc_text(doc_paths[1])
    answer_text = answer_paths[0].read_text(encoding="utf-8")

    assert "Mã đề A" in first_text
    assert "Mã đề B" in second_text
    assert "BẢNG ĐÁP ÁN" in answer_text
    assert "Mã A" in answer_text and "Mã B" in answer_text
