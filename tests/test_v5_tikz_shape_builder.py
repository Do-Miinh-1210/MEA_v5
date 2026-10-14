"""Guard rails for the V5 TikZ Shape Builder workflow."""
from __future__ import annotations

from pathlib import Path

from v5.tikz_shape_builder import SHAPE_FIELDS, build_shape_code


ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_shape_builder_generates_every_registered_shape():
    for shape_type in SHAPE_FIELDS:
        code = build_shape_code(shape_type)
        assert r"\begin{tikzpicture}" in code, shape_type
        assert r"\end{tikzpicture}" in code, shape_type


def test_right_triangle_builder_keeps_right_angle_marker():
    code = build_shape_code(
        "right_triangle",
        {"Cạnh a (ngang)": "3", "Cạnh b (đứng)": "4"},
    )

    assert "(B) at (3,0)" in code
    assert "(C) at (0,4)" in code
    assert "+(0.3,0) -- +(0.3,0.3) -- +(0,0.3)" in code


def test_shape_builder_generates_charts_and_tkz_tables():
    chart = build_shape_code(
        "bar_chart",
        {
            "Nhãn (cách nhau bởi dấu ,)": "A,B",
            "Giá trị (cách nhau bởi dấu ,)": "10,20",
            "Tiêu đề": "Kết quả",
        },
    )
    sign = build_shape_code(
        "sign_product",
        {
            "Các nghiệm (tăng dần, cách nhau ,)": "-2,0,3",
            "Dấu đầu tiên (+/-)": "-",
        },
    )

    assert "symbolic x coords={A, B}" in chart
    assert "(A,10) (B,20)" in chart
    assert r"\tkzTabLine" in sign
    assert "$-2$" in sign and "$3$" in sign


def test_v5_shape_builder_has_no_v4_ui_dependency():
    source = _source("v5/tikz_shape_builder.py")

    assert "class ShapeBuilderDialog" in source
    assert "build_shape_code" in source
    assert "from ui." not in source
    assert "import ui." not in source


def test_qc_tikz_ports_v4_shape_builder_action():
    source = _source("v5/views/qc.py")

    assert "def _open_shape_builder" in source
    assert "from v5.tikz_shape_builder import ShapeBuilderDialog" in source
    assert "Tạo hình" in source
