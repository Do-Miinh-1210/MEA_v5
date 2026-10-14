"""V5-native TikZ Shape Builder.

This ports the practical V4 workflow from ``ui.tikz_shape_builder`` into a
CustomTkinter dialog plus pure code-generation helpers.  The module avoids
importing ``ui.*`` so the V5 TikZ workflow stays independent of the old UI.
"""
from __future__ import annotations

import math
from typing import Any

import customtkinter as ctk
from tkinter import messagebox, ttk


SHAPE_DEFS: dict[str, list[tuple[str, str]]] = {
    "📐 Hình phẳng": [
        ("Tam giác", "triangle"),
        ("Tam giác vuông", "right_triangle"),
        ("Tam giác đều", "equilateral"),
        ("Tam giác cân", "isosceles"),
        ("Hình vuông", "square"),
        ("Hình chữ nhật", "rectangle"),
        ("Hình bình hành", "parallelogram"),
        ("Hình thang", "trapezoid"),
        ("Đường tròn", "circle"),
        ("Elip", "ellipse"),
        ("Đoạn thẳng", "segment"),
    ],
    "🧊 Hình không gian": [
        ("Hình chóp S.ABCD", "pyramid"),
        ("Hình hộp chữ nhật", "cuboid"),
        ("Hình trụ", "cylinder"),
        ("Hình nón", "cone"),
        ("Hình cầu", "sphere"),
    ],
    "📈 Đồ thị hàm số": [
        ("Hàm bậc 2", "graph_quad"),
        ("Hàm bậc 3", "graph_cubic"),
        ("Hàm bậc 4", "graph_quartic"),
        ("Hàm lượng giác", "graph_trig"),
        ("Hàm mũ / logarit", "graph_exp"),
    ],
    "📊 Biểu đồ": [
        ("Biểu đồ cột", "bar_chart"),
        ("Biểu đồ tròn", "pie_chart"),
        ("Biểu đồ đường", "line_chart"),
        ("Biểu đồ miền", "area_chart"),
    ],
    "📑 Bảng biến thiên": [
        ("Hàm bậc 2", "bbt_quad"),
        ("Hàm bậc 3 - 2 cực trị", "bbt_cubic_2ex"),
        ("Hàm bậc 3 - đơn điệu", "bbt_cubic_mono"),
        ("Hàm bậc 4 chữ W", "bbt_quartic_w"),
        ("Hàm bậc 4 chữ M", "bbt_quartic_m"),
        ("Hàm bậc 4 một cực trị", "bbt_quartic_u"),
        ("Phân thức bậc 1/bậc 1", "bbt_frac_11"),
        ("Hàm mũ", "bbt_exp"),
        ("Hàm logarit", "bbt_log"),
    ],
    "➕ Bảng xét dấu": [
        ("Nhị thức ax+b", "sign_linear"),
        ("Tam thức bậc 2 - 2 nghiệm", "sign_quad_2"),
        ("Tam thức bậc 2 - nghiệm kép", "sign_quad_1"),
        ("Tam thức bậc 2 - vô nghiệm", "sign_quad_0"),
        ("Tích/thương nhiều nhân tử", "sign_product"),
    ],
}


SHAPE_FIELDS: dict[str, list[tuple[str, str]]] = {
    "triangle": [("Ax", "0"), ("Ay", "0"), ("Bx", "4"), ("By", "0"),
                 ("Cx", "1.5"), ("Cy", "3"), ("Tên A", "A"),
                 ("Tên B", "B"), ("Tên C", "C")],
    "right_triangle": [("Cạnh a (ngang)", "4"), ("Cạnh b (đứng)", "3"),
                       ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C")],
    "equilateral": [("Độ dài cạnh", "4"), ("Tên A", "A"),
                    ("Tên B", "B"), ("Tên C", "C")],
    "isosceles": [("Đáy", "4"), ("Chiều cao", "3"), ("Tên A", "A"),
                  ("Tên B", "B"), ("Tên C", "C")],
    "square": [("Cạnh", "4"), ("Tên A", "A"), ("Tên B", "B"),
               ("Tên C", "C"), ("Tên D", "D")],
    "rectangle": [("Chiều rộng", "5"), ("Chiều cao", "3"),
                  ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C"),
                  ("Tên D", "D")],
    "parallelogram": [("Đáy", "5"), ("Chiều cao", "3"),
                      ("Độ nghiêng", "1.5"), ("Tên A", "A"),
                      ("Tên B", "B"), ("Tên C", "C"), ("Tên D", "D")],
    "trapezoid": [("Đáy dưới", "6"), ("Đáy trên", "4"),
                  ("Chiều cao", "3"), ("Tên A", "A"), ("Tên B", "B"),
                  ("Tên C", "C"), ("Tên D", "D")],
    "circle": [("Tâm X", "0"), ("Tâm Y", "0"), ("Bán kính", "2"),
               ("Tên tâm", "O")],
    "ellipse": [("Tâm X", "0"), ("Tâm Y", "0"), ("Bán trục lớn a", "3"),
                ("Bán trục nhỏ b", "1.5"), ("Tên tâm", "O")],
    "segment": [("X1", "0"), ("Y1", "0"), ("X2", "4"), ("Y2", "3"),
                ("Tên điểm 1", "A"), ("Tên điểm 2", "B"),
                ("Kiểu đường", "thick")],
    "pyramid": [("Cạnh đáy", "3"), ("Chiều cao", "4"), ("Tên A", "A"),
                ("Tên B", "B"), ("Tên C", "C"), ("Tên D", "D"),
                ("Tên S", "S")],
    "cuboid": [("Chiều dài", "4"), ("Chiều rộng", "3"),
               ("Chiều cao", "3"), ("Tên A", "A"), ("Tên B", "B"),
               ("Tên C", "C"), ("Tên D", "D")],
    "cylinder": [("Bán kính", "1.5"), ("Chiều cao", "3")],
    "cone": [("Bán kính", "1.5"), ("Chiều cao", "3.5")],
    "sphere": [("Bán kính", "2")],
    "graph_quad": [("a", "1"), ("b", "-2"), ("c", "-3"),
                   ("X min", "-5"), ("X max", "5")],
    "graph_cubic": [("a", "1"), ("b", "-3"), ("c", "0"),
                    ("d", "2"), ("X min", "-3"), ("X max", "4")],
    "graph_quartic": [("a", "1"), ("b", "0"), ("c", "-4"),
                      ("d", "0"), ("e", "2"), ("X min", "-3"),
                      ("X max", "3")],
    "graph_trig": [("Hàm", "sin"), ("a", "1"), ("b", "1"),
                   ("c", "0"), ("d", "0")],
    "graph_exp": [("Hàm", "e^x"), ("a", "1"), ("b", "1"), ("c", "0")],
    "bar_chart": [("Nhãn (cách nhau bởi dấu ,)", "A,B,C,D"),
                  ("Giá trị (cách nhau bởi dấu ,)", "25,40,30,55"),
                  ("Tiêu đề", "")],
    "pie_chart": [("Nhãn (cách nhau bởi dấu ,)", "Toán,Lý,Hóa,Sinh"),
                  ("Giá trị (cách nhau bởi dấu ,)", "30,25,20,15"),
                  ("Tiêu đề", "")],
    "line_chart": [("Nhãn (cách nhau bởi dấu ,)", "T1,T2,T3,T4"),
                   ("Giá trị (cách nhau bởi dấu ,)", "10,25,18,35"),
                   ("Tiêu đề", "")],
    "area_chart": [("Nhãn (cách nhau bởi dấu ,)", "T1,T2,T3,T4"),
                   ("Giá trị (cách nhau bởi dấu ,)", "10,25,18,35"),
                   ("Tiêu đề", "")],
    "bbt_quad": [("Hệ số a (a>0 CT, a<0 CĐ)", "1"),
                 ("Hoành độ đỉnh x₀", "1"),
                 ("Tung độ đỉnh y₀", "-2")],
    "bbt_cubic_2ex": [("Hệ số a (a>0 hoặc a<0)", "1"),
                      ("Điểm cực trị thứ nhất x₁", "-1"),
                      ("Điểm cực trị thứ hai x₂", "1"),
                      ("Giá trị cực đại y_CĐ", "2"),
                      ("Giá trị cực tiểu y_CT", "-2")],
    "bbt_cubic_mono": [("Hệ số a (a>0 tăng, a<0 giảm)", "1")],
    "bbt_quartic_w": [("Nghiệm y'₁ (x₁)", "-1"),
                      ("Nghiệm y'₂ (x₂)", "0"),
                      ("Nghiệm y'₃ (x₃)", "1"),
                      ("y tại x₁ (CT)", "-1"),
                      ("y tại x₂ (CĐ)", "0"),
                      ("y tại x₃ (CT)", "-1")],
    "bbt_quartic_m": [("Nghiệm y'₁ (x₁)", "-1"),
                      ("Nghiệm y'₂ (x₂)", "0"),
                      ("Nghiệm y'₃ (x₃)", "1"),
                      ("y tại x₁ (CĐ)", "1"),
                      ("y tại x₂ (CT)", "0"),
                      ("y tại x₃ (CĐ)", "1")],
    "bbt_quartic_u": [("Hoành độ cực trị x₀", "0"),
                      ("Tung độ cực trị y₀", "-1"),
                      ("Hướng (up/down)", "up")],
    "bbt_frac_11": [("Tiệm cận đứng x=", "1"),
                    ("Tiệm cận ngang y=", "2"),
                    ("Biến thiên (inc/dec)", "inc")],
    "bbt_exp": [("Cơ số a>1? (yes/no)", "yes")],
    "bbt_log": [("Cơ số a>1? (yes/no)", "yes")],
    "sign_linear": [("Hệ số a", "1"), ("Nghiệm x₀", "-2")],
    "sign_quad_2": [("Hệ số a", "1"), ("Nghiệm x₁ (nhỏ)", "-1"),
                    ("Nghiệm x₂ (lớn)", "2")],
    "sign_quad_1": [("Hệ số a", "1"), ("Nghiệm kép x₀", "1")],
    "sign_quad_0": [("Hệ số a", "1")],
    "sign_product": [("Các nghiệm (tăng dần, cách nhau ,)", "-2, 0, 3"),
                     ("Dấu đầu tiên (+/-)", "+")],
}


_OPTION_VALUES = {
    "Kiểu đường": ["thick", "dashed", "dotted", "arrow", "double arrow"],
    "Hàm": ["sin", "cos", "e^x", "ln(x)"],
    "Hướng (up/down)": ["up", "down"],
    "Biến thiên (inc/dec)": ["inc", "dec"],
    "Cơ số a>1? (yes/no)": ["yes", "no"],
    "Dấu đầu tiên (+/-)": ["+", "-"],
}


def _fmt(value: Any) -> str:
    try:
        number = float(value)
        if abs(number - int(number)) < 1e-9:
            return str(int(number))
        return f"{number:.3f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(value)


def _float(values: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(values.get(key, default))
    except (TypeError, ValueError):
        return default


def _text(values: dict[str, Any], key: str, default: str = "") -> str:
    value = str(values.get(key, default)).strip()
    return value or default


def _csv(values: dict[str, Any], key: str, default: str) -> list[str]:
    raw = _text(values, key, default)
    return [part.strip() for part in raw.split(",") if part.strip()]


def _csv_numbers(values: dict[str, Any], key: str, n: int) -> list[float]:
    raw = _csv(values, key, "")
    numbers: list[float] = []
    for item in raw:
        try:
            numbers.append(float(item))
        except ValueError:
            numbers.append(0.0)
    while len(numbers) < n:
        numbers.append(0.0)
    return numbers[:n]


def _wrap(lines: list[str]) -> str:
    return "\n".join(lines)


def _point(label: str, pos: str, name: str, xy: str) -> str:
    return f"  \\coordinate[label={pos}:${label}$] ({name}) at {xy};"


def _build_2d(shape_type: str, values: dict[str, Any]) -> str | None:
    if shape_type == "triangle":
        na, nb, nc = _text(values, "Tên A", "A"), _text(values, "Tên B", "B"), _text(values, "Tên C", "C")
        return _wrap([
            r"\begin{tikzpicture}[scale=1, thick]",
            _point(na, "below left", na, f"({_fmt(_float(values, 'Ax'))},{_fmt(_float(values, 'Ay'))})"),
            _point(nb, "below right", nb, f"({_fmt(_float(values, 'Bx', 4))},{_fmt(_float(values, 'By'))})"),
            _point(nc, "above", nc, f"({_fmt(_float(values, 'Cx', 1.5))},{_fmt(_float(values, 'Cy', 3))})"),
            f"  \\draw ({na})--({nb})--({nc})--cycle;",
            r"\end{tikzpicture}",
        ])
    if shape_type in {"right_triangle", "equilateral", "isosceles"}:
        na, nb, nc = _text(values, "Tên A", "A"), _text(values, "Tên B", "B"), _text(values, "Tên C", "C")
        if shape_type == "right_triangle":
            bx, cy = _float(values, "Cạnh a (ngang)", 4), _float(values, "Cạnh b (đứng)", 3)
            pts = ((0, 0), (bx, 0), (0, cy))
            extra = [f"  \\draw ({na}) +(0.3,0) -- +(0.3,0.3) -- +(0,0.3);"]
        elif shape_type == "equilateral":
            side = _float(values, "Độ dài cạnh", 4)
            pts = ((0, 0), (side, 0), (side / 2, side * 0.8660254))
            extra = []
        else:
            base, height = _float(values, "Đáy", 4), _float(values, "Chiều cao", 3)
            pts = ((0, 0), (base, 0), (base / 2, height))
            extra = []
        return _wrap([
            r"\begin{tikzpicture}[scale=1, thick]",
            _point(na, "below left", na, f"({_fmt(pts[0][0])},{_fmt(pts[0][1])})"),
            _point(nb, "below right", nb, f"({_fmt(pts[1][0])},{_fmt(pts[1][1])})"),
            _point(nc, "above", nc, f"({_fmt(pts[2][0])},{_fmt(pts[2][1])})"),
            f"  \\draw ({na})--({nb})--({nc})--cycle;",
            *extra,
            r"\end{tikzpicture}",
        ])
    if shape_type in {"square", "rectangle"}:
        w = _float(values, "Cạnh" if shape_type == "square" else "Chiều rộng", 4)
        h = w if shape_type == "square" else _float(values, "Chiều cao", 3)
        na, nb, nc, nd = (_text(values, "Tên A", "A"), _text(values, "Tên B", "B"),
                          _text(values, "Tên C", "C"), _text(values, "Tên D", "D"))
        return _wrap([
            r"\begin{tikzpicture}[scale=1, thick]",
            _point(na, "below left", na, "(0,0)"),
            _point(nb, "below right", nb, f"({_fmt(w)},0)"),
            _point(nc, "above right", nc, f"({_fmt(w)},{_fmt(h)})"),
            _point(nd, "above left", nd, f"(0,{_fmt(h)})"),
            f"  \\draw ({na})--({nb})--({nc})--({nd})--cycle;",
            r"\end{tikzpicture}",
        ])
    if shape_type == "parallelogram":
        w, h, skew = _float(values, "Đáy", 5), _float(values, "Chiều cao", 3), _float(values, "Độ nghiêng", 1.5)
        na, nb, nc, nd = (_text(values, "Tên A", "A"), _text(values, "Tên B", "B"),
                          _text(values, "Tên C", "C"), _text(values, "Tên D", "D"))
        return _wrap([
            r"\begin{tikzpicture}[scale=1, thick]",
            _point(na, "below left", na, "(0,0)"),
            _point(nb, "below right", nb, f"({_fmt(w)},0)"),
            _point(nc, "above right", nc, f"({_fmt(w + skew)},{_fmt(h)})"),
            _point(nd, "above left", nd, f"({_fmt(skew)},{_fmt(h)})"),
            f"  \\draw ({na})--({nb})--({nc})--({nd})--cycle;",
            r"\end{tikzpicture}",
        ])
    if shape_type == "trapezoid":
        bottom, top, h = _float(values, "Đáy dưới", 6), _float(values, "Đáy trên", 4), _float(values, "Chiều cao", 3)
        offset = (bottom - top) / 2
        na, nb, nc, nd = (_text(values, "Tên A", "A"), _text(values, "Tên B", "B"),
                          _text(values, "Tên C", "C"), _text(values, "Tên D", "D"))
        return _wrap([
            r"\begin{tikzpicture}[scale=1, thick]",
            _point(na, "below left", na, "(0,0)"),
            _point(nb, "below right", nb, f"({_fmt(bottom)},0)"),
            _point(nc, "above right", nc, f"({_fmt(bottom - offset)},{_fmt(h)})"),
            _point(nd, "above left", nd, f"({_fmt(offset)},{_fmt(h)})"),
            f"  \\draw ({na})--({nb})--({nc})--({nd})--cycle;",
            r"\end{tikzpicture}",
        ])
    if shape_type == "circle":
        label = _text(values, "Tên tâm", "O")
        cx, cy, r = _float(values, "Tâm X"), _float(values, "Tâm Y"), _float(values, "Bán kính", 2)
        return _wrap([
            r"\begin{tikzpicture}[scale=1, thick]",
            f"  \\coordinate ({label}) at ({_fmt(cx)},{_fmt(cy)});",
            f"  \\draw ({label}) circle ({_fmt(r)}cm);",
            f"  \\fill ({label}) circle (1.5pt) node[below]{{${label}$}};",
            f"  \\draw[dashed] ({label}) -- +({_fmt(r)},0) node[midway, above]{{$r={_fmt(r)}$}};",
            r"\end{tikzpicture}",
        ])
    if shape_type == "ellipse":
        label = _text(values, "Tên tâm", "O")
        cx, cy = _float(values, "Tâm X"), _float(values, "Tâm Y")
        a, b = _float(values, "Bán trục lớn a", 3), _float(values, "Bán trục nhỏ b", 1.5)
        return _wrap([
            r"\begin{tikzpicture}[scale=1, thick]",
            f"  \\draw ({_fmt(cx)},{_fmt(cy)}) ellipse ({_fmt(a)}cm and {_fmt(b)}cm);",
            f"  \\fill ({_fmt(cx)},{_fmt(cy)}) circle (1.5pt) node[below]{{${label}$}};",
            r"\end{tikzpicture}",
        ])
    if shape_type == "segment":
        styles = {
            "thick": "thick", "dashed": "dashed, thick",
            "dotted": "dotted, thick", "arrow": "->, thick",
            "double arrow": "<->, thick",
        }
        style = styles.get(_text(values, "Kiểu đường", "thick"), "thick")
        n1, n2 = _text(values, "Tên điểm 1", "A"), _text(values, "Tên điểm 2", "B")
        x1, y1 = _float(values, "X1"), _float(values, "Y1")
        x2, y2 = _float(values, "X2", 4), _float(values, "Y2", 3)
        return _wrap([
            r"\begin{tikzpicture}[scale=1]",
            _point(n1, "below left", n1, f"({_fmt(x1)},{_fmt(y1)})"),
            _point(n2, "below right", n2, f"({_fmt(x2)},{_fmt(y2)})"),
            f"  \\draw[{style}] ({n1})--({n2});",
            f"  \\fill ({n1}) circle (1.5pt);",
            f"  \\fill ({n2}) circle (1.5pt);",
            r"\end{tikzpicture}",
        ])
    return None


def _build_3d(shape_type: str, values: dict[str, Any]) -> str | None:
    if shape_type == "pyramid":
        side, height = _float(values, "Cạnh đáy", 3), _float(values, "Chiều cao", 4)
        half = side / 2
        na, nb, nc, nd, ns = (_text(values, "Tên A", "A"), _text(values, "Tên B", "B"),
                              _text(values, "Tên C", "C"), _text(values, "Tên D", "D"),
                              _text(values, "Tên S", "S"))
        return _wrap([
            r"\begin{tikzpicture}[scale=1.3, thick,",
            r"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]",
            _point(na, "below left", na, "(0,0,0)"),
            _point(nb, "below right", nb, f"({_fmt(side)},0,0)"),
            _point(nc, "right", nc, f"({_fmt(side)},{_fmt(side)},0)"),
            _point(nd, "left", nd, f"(0,{_fmt(side)},0)"),
            _point(ns, "above", ns, f"({_fmt(half)},{_fmt(half)},{_fmt(height)})"),
            f"  \\draw ({na})--({nb})--({nc});",
            f"  \\draw[dashed] ({nc})--({nd})--({na});",
            f"  \\draw ({ns})--({na}) ({ns})--({nb}) ({ns})--({nc});",
            f"  \\draw[dashed] ({ns})--({nd});",
            f"  \\draw[dashed] ({na})--({nc}) ({nb})--({nd});",
            r"\end{tikzpicture}",
        ])
    if shape_type == "cuboid":
        a, b, h = _float(values, "Chiều dài", 4), _float(values, "Chiều rộng", 3), _float(values, "Chiều cao", 3)
        return _wrap([
            r"\begin{tikzpicture}[scale=1.2, thick,",
            r"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]",
            f"  \\coordinate[label=below left:$A$] (A) at (0,0,0);",
            f"  \\coordinate[label=below right:$B$] (B) at ({_fmt(a)},0,0);",
            f"  \\coordinate[label=right:$C$] (C) at ({_fmt(a)},{_fmt(b)},0);",
            f"  \\coordinate[label=left:$D$] (D) at (0,{_fmt(b)},0);",
            f"  \\coordinate[label=above left:$A'$] (A1) at (0,0,{_fmt(h)});",
            f"  \\coordinate[label=above right:$B'$] (B1) at ({_fmt(a)},0,{_fmt(h)});",
            f"  \\coordinate[label=above right:$C'$] (C1) at ({_fmt(a)},{_fmt(b)},{_fmt(h)});",
            f"  \\coordinate[label=above left:$D'$] (D1) at (0,{_fmt(b)},{_fmt(h)});",
            r"  \draw (A)--(B)--(C);",
            r"  \draw[dashed] (C)--(D)--(A);",
            r"  \draw (A1)--(B1)--(C1)--(D1)--cycle;",
            r"  \draw (A)--(A1) (B)--(B1) (C)--(C1);",
            r"  \draw[dashed] (D)--(D1);",
            r"\end{tikzpicture}",
        ])
    if shape_type == "cylinder":
        r, h = _float(values, "Bán kính", 1.5), _float(values, "Chiều cao", 3)
        e = r * 0.35
        return _wrap([
            r"\begin{tikzpicture}[scale=1, thick]",
            f"  \\draw (-{_fmt(r)},0) arc (180:360:{_fmt(r)}cm and {_fmt(e)}cm);",
            f"  \\draw[dashed] (-{_fmt(r)},0) arc (180:0:{_fmt(r)}cm and {_fmt(e)}cm);",
            f"  \\draw (0,{_fmt(h)}) ellipse ({_fmt(r)}cm and {_fmt(e)}cm);",
            f"  \\draw (-{_fmt(r)},0)--(-{_fmt(r)},{_fmt(h)});",
            f"  \\draw ({_fmt(r)},0)--({_fmt(r)},{_fmt(h)});",
            f"  \\draw[dashed] (0,0)--(0,{_fmt(h)});",
            r"\end{tikzpicture}",
        ])
    if shape_type == "cone":
        r, h = _float(values, "Bán kính", 1.5), _float(values, "Chiều cao", 3.5)
        e = r * 0.35
        return _wrap([
            r"\begin{tikzpicture}[scale=1, thick]",
            f"  \\draw (-{_fmt(r)},0) arc (180:360:{_fmt(r)}cm and {_fmt(e)}cm);",
            f"  \\draw[dashed] (-{_fmt(r)},0) arc (180:0:{_fmt(r)}cm and {_fmt(e)}cm);",
            f"  \\coordinate[label=above:$S$] (S) at (0,{_fmt(h)});",
            f"  \\draw (-{_fmt(r)},0)--(S)--({_fmt(r)},0);",
            r"  \fill (0,0) circle (1.5pt) node[below right]{$O$};",
            r"  \draw[dashed] (0,0)--(S);",
            r"\end{tikzpicture}",
        ])
    if shape_type == "sphere":
        r = _float(values, "Bán kính", 2)
        e = r * 0.35
        return _wrap([
            r"\begin{tikzpicture}[scale=1, thick]",
            f"  \\draw (0,0) circle ({_fmt(r)}cm);",
            f"  \\draw (-{_fmt(r)},0) arc (180:360:{_fmt(r)}cm and {_fmt(e)}cm);",
            f"  \\draw[dashed] (-{_fmt(r)},0) arc (180:0:{_fmt(r)}cm and {_fmt(e)}cm);",
            r"  \fill (0,0) circle (1.5pt) node[below right]{$O$};",
            f"  \\draw[<->] (0,0)--({_fmt(r)},0) node[midway,above]{{$R={_fmt(r)}$}};",
            r"\end{tikzpicture}",
        ])
    return None


def _axis_header(xmin: float, xmax: float) -> list[str]:
    return [
        r"\begin{tikzpicture}",
        r"\begin{axis}[",
        r"  axis lines=center, xlabel={$x$}, ylabel={$y$},",
        f"  xmin={_fmt(xmin)}, xmax={_fmt(xmax)},",
        r"  grid=major, grid style={gray!30},",
        r"  width=10cm, height=8cm, samples=120,",
        r"]",
    ]


def _build_graph(shape_type: str, values: dict[str, Any]) -> str | None:
    xmin, xmax = _float(values, "X min", -5), _float(values, "X max", 5)
    if shape_type == "graph_quad":
        a, b, c = _float(values, "a", 1), _float(values, "b", -2), _float(values, "c", -3)
        expr = f"{_fmt(a)}*x^2 + {_fmt(b)}*x + {_fmt(c)}"
    elif shape_type == "graph_cubic":
        a, b, c, d = (_float(values, "a", 1), _float(values, "b", -3),
                      _float(values, "c", 0), _float(values, "d", 2))
        expr = f"{_fmt(a)}*x^3 + {_fmt(b)}*x^2 + {_fmt(c)}*x + {_fmt(d)}"
    elif shape_type == "graph_quartic":
        a, b, c, d, e = (_float(values, "a", 1), _float(values, "b", 0),
                         _float(values, "c", -4), _float(values, "d", 0),
                         _float(values, "e", 2))
        expr = f"{_fmt(a)}*x^4 + {_fmt(b)}*x^3 + {_fmt(c)}*x^2 + {_fmt(d)}*x + {_fmt(e)}"
    elif shape_type == "graph_trig":
        fn = "cos" if _text(values, "Hàm", "sin") == "cos" else "sin"
        a, b, c, d = (_float(values, "a", 1), _float(values, "b", 1),
                      _float(values, "c", 0), _float(values, "d", 0))
        expr = f"{_fmt(a)}*{fn}(deg({_fmt(b)}*x + {_fmt(c)})) + {_fmt(d)}"
        xmin, xmax = -7, 7
    elif shape_type == "graph_exp":
        fn = _text(values, "Hàm", "e^x")
        a, b, c = _float(values, "a", 1), _float(values, "b", 1), _float(values, "c", 0)
        expr = f"{_fmt(a)}*ln({_fmt(b)}*x) + {_fmt(c)}" if fn == "ln(x)" else f"{_fmt(a)}*exp({_fmt(b)}*x) + {_fmt(c)}"
        xmin, xmax = (0.1, 8) if fn == "ln(x)" else (-3, 3)
    else:
        return None
    return _wrap([
        *_axis_header(xmin, xmax),
        f"  \\addplot[blue, very thick, domain={_fmt(xmin)}:{_fmt(xmax)}] {{{expr}}};",
        r"\end{axis}",
        r"\end{tikzpicture}",
    ])


def _build_chart(shape_type: str, values: dict[str, Any]) -> str | None:
    if shape_type not in {"bar_chart", "pie_chart", "line_chart", "area_chart"}:
        return None
    labels = _csv(values, "Nhãn (cách nhau bởi dấu ,)", "A,B,C")
    vals = _csv_numbers(values, "Giá trị (cách nhau bởi dấu ,)", len(labels))
    title = _text(values, "Tiêu đề", "")
    if shape_type == "pie_chart":
        total = sum(vals) or 1
        colors = ["blue!60", "red!60", "green!60", "orange!60", "purple!60"]
        start = 0.0
        lines = [r"\begin{tikzpicture}"]
        if title:
            lines.append(f"  \\node[font=\\large\\bfseries] at (0,4.3) {{{title}}};")
        for i, (label, value) in enumerate(zip(labels, vals)):
            end = start + value / total * 360
            mid = (start + end) / 2
            pct = value / total * 100
            lines.append(f"  \\filldraw[fill={colors[i % len(colors)]}, draw=white, thick] (0,0) -- ({_fmt(start)}:3cm) arc ({_fmt(start)}:{_fmt(end)}:3cm) -- cycle;")
            lines.append(f"  \\node[font=\\small] at ({_fmt(mid)}:2cm) {{{label}\\\\{pct:.0f}\\%}};")
            start = end
        lines.append(r"\end{tikzpicture}")
        return _wrap(lines)
    coords = " ".join(f"({labels[i]},{_fmt(vals[i])})" for i in range(len(labels)))
    plot = r"\addplot[fill=blue!30, draw=blue, thick] coordinates {" + coords + r"} \closedcycle;" if shape_type == "area_chart" else (
        r"\addplot[blue, very thick, mark=*] coordinates {" + coords + r"};" if shape_type == "line_chart" else
        r"\addplot[fill=blue!60] coordinates {" + coords + r"};"
    )
    return _wrap([
        r"\begin{tikzpicture}",
        r"\begin{axis}[",
        ("  ybar, bar width=18pt," if shape_type == "bar_chart" else "  mark=*,"),
        f"  title={{{title}}}," if title else "  title={},",
        "  symbolic x coords={" + ", ".join(labels) + "},",
        r"  xtick=data, nodes near coords, width=12cm, height=7cm,",
        r"  grid=major, grid style={gray!20},",
        r"]",
        "  " + plot,
        r"\end{axis}",
        r"\end{tikzpicture}",
    ])


def _bbt_init(nodes: list[str], rows: str = r"{$x$/1, $y'$/1, $y$/2}") -> str:
    return r"\tkzTabInit[lgt=2, espcl=3]" + rows + "{" + ", ".join(nodes) + "}"


def _build_table(shape_type: str, values: dict[str, Any]) -> str | None:
    inf = r"$-\infty$"
    pinf = r"$+\infty$"
    if shape_type == "bbt_quad":
        a = _float(values, "Hệ số a (a>0 CT, a<0 CĐ)", 1)
        x0, y0 = _fmt(_float(values, "Hoành độ đỉnh x₀", 1)), _fmt(_float(values, "Tung độ đỉnh y₀", -2))
        line = r"\tkzTabLine{, -, 0, +, }" if a >= 0 else r"\tkzTabLine{, +, 0, -, }"
        var = r"\tkzTabVar{+/$+\infty$, -/$" + y0 + r"$, +/$+\infty$}" if a >= 0 else r"\tkzTabVar{-/$-\infty$, +/$" + y0 + r"$, -/$-\infty$}"
        return _wrap([r"\begin{tikzpicture}", _bbt_init([inf, f"${x0}$", pinf]), line, var, r"\end{tikzpicture}"])
    if shape_type == "bbt_cubic_2ex":
        a = _float(values, "Hệ số a (a>0 hoặc a<0)", 1)
        x1, x2 = _fmt(_float(values, "Điểm cực trị thứ nhất x₁", -1)), _fmt(_float(values, "Điểm cực trị thứ hai x₂", 1))
        ycd, yct = _fmt(_float(values, "Giá trị cực đại y_CĐ", 2)), _fmt(_float(values, "Giá trị cực tiểu y_CT", -2))
        line = r"\tkzTabLine{, +, 0, -, 0, +, }" if a >= 0 else r"\tkzTabLine{, -, 0, +, 0, -, }"
        var = r"\tkzTabVar{-/$-\infty$, +/$" + ycd + r"$, -/$" + yct + r"$, +/$+\infty$}" if a >= 0 else r"\tkzTabVar{+/$+\infty$, -/$" + yct + r"$, +/$" + ycd + r"$, -/$-\infty$}"
        return _wrap([r"\begin{tikzpicture}", _bbt_init([inf, f"${x1}$", f"${x2}$", pinf]), line, var, r"\end{tikzpicture}"])
    if shape_type == "bbt_cubic_mono":
        a = _float(values, "Hệ số a (a>0 tăng, a<0 giảm)", 1)
        line = r"\tkzTabLine{, +, }" if a >= 0 else r"\tkzTabLine{, -, }"
        var = r"\tkzTabVar{-/$-\infty$, +/$+\infty$}" if a >= 0 else r"\tkzTabVar{+/$+\infty$, -/$-\infty$}"
        return _wrap([r"\begin{tikzpicture}", _bbt_init([inf, pinf]), line, var, r"\end{tikzpicture}"])
    if shape_type in {"bbt_quartic_w", "bbt_quartic_m"}:
        x1, x2, x3 = (_fmt(_float(values, "Nghiệm y'₁ (x₁)", -1)),
                      _fmt(_float(values, "Nghiệm y'₂ (x₂)", 0)),
                      _fmt(_float(values, "Nghiệm y'₃ (x₃)", 1)))
        is_w = shape_type == "bbt_quartic_w"
        if is_w:
            y1, y2, y3 = (_fmt(_float(values, "y tại x₁ (CT)", -1)),
                          _fmt(_float(values, "y tại x₂ (CĐ)", 0)),
                          _fmt(_float(values, "y tại x₃ (CT)", -1)))
            line = r"\tkzTabLine{, -, 0, +, 0, -, 0, +, }"
            var = r"\tkzTabVar{+/$+\infty$, -/$" + y1 + r"$, +/$" + y2 + r"$, -/$" + y3 + r"$, +/$+\infty$}"
        else:
            y1, y2, y3 = (_fmt(_float(values, "y tại x₁ (CĐ)", 1)),
                          _fmt(_float(values, "y tại x₂ (CT)", 0)),
                          _fmt(_float(values, "y tại x₃ (CĐ)", 1)))
            line = r"\tkzTabLine{, +, 0, -, 0, +, 0, -, }"
            var = r"\tkzTabVar{-/$-\infty$, +/$" + y1 + r"$, -/$" + y2 + r"$, +/$" + y3 + r"$, -/$-\infty$}"
        return _wrap([r"\begin{tikzpicture}", _bbt_init([inf, f"${x1}$", f"${x2}$", f"${x3}$", pinf]), line, var, r"\end{tikzpicture}"])
    if shape_type == "bbt_quartic_u":
        x0, y0 = _fmt(_float(values, "Hoành độ cực trị x₀", 0)), _fmt(_float(values, "Tung độ cực trị y₀", -1))
        up = _text(values, "Hướng (up/down)", "up") == "up"
        line = r"\tkzTabLine{, -, 0, +, }" if up else r"\tkzTabLine{, +, 0, -, }"
        var = r"\tkzTabVar{+/$+\infty$, -/$" + y0 + r"$, +/$+\infty$}" if up else r"\tkzTabVar{-/$-\infty$, +/$" + y0 + r"$, -/$-\infty$}"
        return _wrap([r"\begin{tikzpicture}", _bbt_init([inf, f"${x0}$", pinf]), line, var, r"\end{tikzpicture}"])
    if shape_type == "bbt_frac_11":
        xd, yn = _fmt(_float(values, "Tiệm cận đứng x=", 1)), _fmt(_float(values, "Tiệm cận ngang y=", 2))
        inc = _text(values, "Biến thiên (inc/dec)", "inc") == "inc"
        line = r"\tkzTabLine{, +, d, +, }" if inc else r"\tkzTabLine{, -, d, -, }"
        var = r"\tkzTabVar{-/$" + yn + r"$, +D-/$+\infty$/$-\infty$, +/$" + yn + r"$}" if inc else r"\tkzTabVar{+/$" + yn + r"$, -D+/$-\infty$/$+\infty$, -/$" + yn + r"$}"
        return _wrap([r"\begin{tikzpicture}", _bbt_init([inf, f"${xd}$", pinf]), line, var, r"\end{tikzpicture}"])
    if shape_type in {"bbt_exp", "bbt_log"}:
        inc = _text(values, "Cơ số a>1? (yes/no)", "yes").lower() in {"yes", "y", "1", "true", "có"}
        nodes = [inf, pinf] if shape_type == "bbt_exp" else [r"$0$", pinf]
        line = r"\tkzTabLine{, +, }" if inc else r"\tkzTabLine{, -, }"
        if shape_type == "bbt_exp":
            var = r"\tkzTabVar{-/$0$, +/$+\infty$}" if inc else r"\tkzTabVar{+/$+\infty$, -/$0$}"
        else:
            var = r"\tkzTabVar{-/$-\infty$, +/$+\infty$}" if inc else r"\tkzTabVar{+/$+\infty$, -/$-\infty$}"
        return _wrap([r"\begin{tikzpicture}", _bbt_init(nodes), line, var, r"\end{tikzpicture}"])
    if shape_type == "sign_linear":
        a, x0 = _float(values, "Hệ số a", 1), _fmt(_float(values, "Nghiệm x₀", -2))
        line = r"\tkzTabLine{, -, 0, +, }" if a >= 0 else r"\tkzTabLine{, +, 0, -, }"
        return _wrap([r"\begin{tikzpicture}", r"\tkzTabInit[lgt=2, espcl=3]{$x$/1, $f(x)$/1}" + "{" + f"{inf}, ${x0}$, {pinf}" + "}", line, r"\end{tikzpicture}"])
    if shape_type in {"sign_quad_2", "sign_quad_1", "sign_quad_0"}:
        a = _float(values, "Hệ số a", 1)
        if shape_type == "sign_quad_2":
            x1, x2 = _fmt(_float(values, "Nghiệm x₁ (nhỏ)", -1)), _fmt(_float(values, "Nghiệm x₂ (lớn)", 2))
            line = r"\tkzTabLine{, +, 0, -, 0, +, }" if a >= 0 else r"\tkzTabLine{, -, 0, +, 0, -, }"
            nodes = [inf, f"${x1}$", f"${x2}$", pinf]
        elif shape_type == "sign_quad_1":
            x0 = _fmt(_float(values, "Nghiệm kép x₀", 1))
            line = r"\tkzTabLine{, +, 0, +, }" if a >= 0 else r"\tkzTabLine{, -, 0, -, }"
            nodes = [inf, f"${x0}$", pinf]
        else:
            line = r"\tkzTabLine{, +, }" if a >= 0 else r"\tkzTabLine{, -, }"
            nodes = [inf, pinf]
        return _wrap([r"\begin{tikzpicture}", r"\tkzTabInit[lgt=2, espcl=2.5]{$x$/1, $f(x)$/1}" + "{" + ", ".join(nodes) + "}", line, r"\end{tikzpicture}"])
    if shape_type == "sign_product":
        roots = _csv(values, "Các nghiệm (tăng dần, cách nhau ,)", "-2,0,3")
        sign = "+" if _text(values, "Dấu đầu tiên (+/-)", "+") == "+" else "-"
        nodes = [inf] + [f"${_fmt(root)}$" for root in roots] + [pinf]
        parts = [""]
        current = sign
        for i in range(len(roots) + 1):
            parts.append(current)
            if i < len(roots):
                parts.append("0")
            current = "-" if current == "+" else "+"
        parts.append("")
        line = r"\tkzTabLine{" + ", ".join(parts) + "}"
        return _wrap([r"\begin{tikzpicture}", r"\tkzTabInit[lgt=2, espcl=2.2]{$x$/1, $f(x)$/1}" + "{" + ", ".join(nodes) + "}", line, r"\end{tikzpicture}"])
    return None


def build_shape_code(shape_type: str, values: dict[str, Any] | None = None) -> str:
    """Generate TikZ code for one supported shape type."""
    values = values or {}
    defaults = {key: default for key, default in SHAPE_FIELDS.get(shape_type, [])}
    merged = {**defaults, **values}
    for builder in (_build_2d, _build_3d, _build_graph, _build_chart, _build_table):
        code = builder(shape_type, merged)
        if code:
            return code
    raise ValueError(f"Loại hình chưa hỗ trợ: {shape_type}")


class ShapeBuilderDialog(ctk.CTkToplevel):
    """Pick a shape, edit parameters, preview code, and insert into TikZ editor."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Công cụ tạo hình TikZ")
        self.geometry("960x700")
        self.minsize(820, 560)
        self.transient(parent)
        self.grab_set()

        self.result: str | None = None
        self._current_type = ""
        self._field_vars: dict[str, ctk.StringVar] = {}

        self._build()
        self.bind("<Escape>", lambda _e: self.destroy())

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=("#EEF2FF", "#1E1B4B"),
                              corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="📐  Tạo hình TikZ từ thông số",
            font=("Segoe UI", 19, "bold"),
            text_color=("#3730A3", "#C7D2FE"),
        ).pack(side="left", padx=18, pady=14)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=14, pady=12)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=2)

        left = ctk.CTkFrame(body, fg_color=("white", "#1E293B"))
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self._tree = ttk.Treeview(left, show="tree", selectmode="browse")
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._tree)
        except Exception:
            pass
        self._shape_map: dict[str, str] = {}
        for category, shapes in SHAPE_DEFS.items():
            parent = self._tree.insert("", "end", text=f" {category}", open=True)
            for label, shape_type in shapes:
                iid = self._tree.insert(parent, "end", text=f"  {label}")
                self._shape_map[iid] = shape_type
        vsb = ttk.Scrollbar(left, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        right = ctk.CTkFrame(body, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._fields_frame = ctk.CTkScrollableFrame(
            right, label_text="Thông số", height=250)
        self._fields_frame.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            self._fields_frame,
            text="Chọn loại hình bên trái để nhập thông số.",
            text_color="gray",
        ).pack(pady=30)

        self._code_box = ctk.CTkTextbox(
            right,
            font=("Consolas", 10),
            fg_color=("#F8FAFC", "#0F172A"),
            wrap="none",
        )
        self._code_box.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=14, pady=(0, 14))
        ctk.CTkButton(
            actions, text="🔄 Xem trước code", width=145,
            fg_color=("#8B5CF6", "#5B21B6"),
            hover_color=("#7C3AED", "#4C1D95"),
            command=self._preview_code,
        ).pack(side="left")
        ctk.CTkButton(
            actions, text="✅ Chèn vào editor", width=150,
            fg_color=("#10B981", "#047857"),
            hover_color=("#059669", "#065F46"),
            command=self._insert_code,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            actions, text="Huỷ", width=90,
            fg_color=("#6B7280", "#374151"),
            command=self.destroy,
        ).pack(side="right")

    def _on_select(self, _event=None):
        selection = self._tree.selection()
        if not selection:
            return
        shape_type = self._shape_map.get(str(selection[0]))
        if not shape_type:
            return
        self._current_type = shape_type
        self._render_fields(shape_type)
        self._preview_code()

    def _render_fields(self, shape_type: str):
        for widget in self._fields_frame.winfo_children():
            widget.destroy()
        self._field_vars.clear()
        for label, default in SHAPE_FIELDS.get(shape_type, []):
            row = ctk.CTkFrame(self._fields_frame, fg_color="transparent")
            row.pack(fill="x", padx=4, pady=3)
            ctk.CTkLabel(row, text=label, width=180, anchor="w").pack(
                side="left", padx=(0, 8))
            var = ctk.StringVar(value=default)
            options = _OPTION_VALUES.get(label)
            if label == "Hàm":
                options = ["sin", "cos"] if shape_type == "graph_trig" else ["e^x", "ln(x)"]
            if options:
                ctk.CTkOptionMenu(row, values=options, variable=var,
                                  width=170).pack(side="left", fill="x", expand=True)
            else:
                ctk.CTkEntry(row, textvariable=var).pack(
                    side="left", fill="x", expand=True)
            self._field_vars[label] = var

    def _values(self) -> dict[str, str]:
        return {key: var.get() for key, var in self._field_vars.items()}

    def _preview_code(self):
        if not self._current_type:
            return
        try:
            code = build_shape_code(self._current_type, self._values())
        except Exception as exc:
            messagebox.showerror("Lỗi tạo code", str(exc), parent=self)
            return
        self._code_box.delete("1.0", "end")
        self._code_box.insert("1.0", code)

    def _insert_code(self):
        if not self._current_type:
            messagebox.showinfo("Chọn loại hình", "Hãy chọn một loại hình trước.",
                                parent=self)
            return
        try:
            self.result = build_shape_code(self._current_type, self._values())
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Lỗi tạo code", str(exc), parent=self)
