"""
ui/tikz_shape_builder.py — Công cụ vẽ hình trực quan cho TikZ.

Người dùng chọn loại hình, nhập thông số → app tự tạo code TikZ.
Hỗ trợ:
  - Hình học: tam giác, vuông, chữ nhật, tròn, đoạn thẳng, tam giác đều/cân
  - Đồ thị hàm số: bậc 2, 3, 4 (nhập hệ số)
  - Biểu đồ: cột, tròn, đường, miền
  - Bảng biến thiên (tkz-tab): bậc 2, bậc 3 (2 cực trị / đơn điệu),
    bậc 4 trùng phương, phân thức hữu tỉ, mũ/log
  - Bảng xét dấu: nhị thức, tam thức 2 nghiệm, tam thức vô nghiệm, tích/thương
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Optional

BG = "#F9F7F4"


# ══════════════════════════════════════════════════════════════════════════════
#  CODE GENERATORS — Tạo code TikZ từ thông số
# ══════════════════════════════════════════════════════════════════════════════

def _gen_triangle(ax, ay, bx, by, cx, cy, na="A", nb="B", nc="C",
                  show_angle=False, style="thick"):
    lines = [r"\begin{tikzpicture}[scale=1, " + style + "]"]
    lines.append(f"  \\coordinate[label=below left:${na}$]  ({na}) at ({ax},{ay});")
    lines.append(f"  \\coordinate[label=below right:${nb}$] ({nb}) at ({bx},{by});")
    lines.append(f"  \\coordinate[label=above:${nc}$]       ({nc}) at ({cx},{cy});")
    lines.append(f"  \\draw ({na})--({nb})--({nc})--cycle;")
    if show_angle:
        lines.append(f"  \\pic[draw, angle radius=0.5cm] {{angle={nb}--{na}--{nc}}};")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_equilateral(side, na="A", nb="B", nc="C"):
    h = round(side * 0.866, 2)
    return _gen_triangle(0, 0, side, 0, round(side / 2, 2), h, na, nb, nc)


def _gen_isosceles(base, height, na="A", nb="B", nc="C"):
    return _gen_triangle(0, 0, base, 0, round(base / 2, 2), height, na, nb, nc)


def _gen_right_triangle(a, b, na="A", nb="B", nc="C"):
    lines = [r"\begin{tikzpicture}[scale=1, thick]"]
    lines.append(f"  \\coordinate[label=below left:${na}$]  ({na}) at (0,0);")
    lines.append(f"  \\coordinate[label=below right:${nb}$] ({nb}) at ({a},0);")
    lines.append(f"  \\coordinate[label=above left:${nc}$]  ({nc}) at (0,{b});")
    lines.append(f"  \\draw ({na})--({nb})--({nc})--cycle;")
    lines.append(f"  % Góc vuông tại {na}")
    lines.append(f"  \\draw ({na}) +(0.3,0) -- +(0.3,0.3) -- +(0,0.3);")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_rectangle(w, h, na="A", nb="B", nc="C", nd="D"):
    lines = [r"\begin{tikzpicture}[scale=1, thick]"]
    lines.append(f"  \\coordinate[label=below left:${na}$]  ({na}) at (0,0);")
    lines.append(f"  \\coordinate[label=below right:${nb}$] ({nb}) at ({w},0);")
    lines.append(f"  \\coordinate[label=above right:${nc}$] ({nc}) at ({w},{h});")
    lines.append(f"  \\coordinate[label=above left:${nd}$]  ({nd}) at (0,{h});")
    lines.append(f"  \\draw ({na})--({nb})--({nc})--({nd})--cycle;")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_square(side, na="A", nb="B", nc="C", nd="D"):
    return _gen_rectangle(side, side, na, nb, nc, nd)


def _gen_circle(cx, cy, r, label="O"):
    lines = [r"\begin{tikzpicture}[scale=1, thick]"]
    lines.append(f"  \\coordinate ({label}) at ({cx},{cy});")
    lines.append(f"  \\draw ({label}) circle ({r}cm);")
    lines.append(f"  \\fill ({label}) circle (1.5pt) node[below]{{${label}$}};")
    lines.append(f"  % Bán kính")
    lines.append(f"  \\draw[dashed] ({label}) -- +({r},0) node[midway, above]{{$r={r}$}};")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_segment(x1, y1, x2, y2, n1="A", n2="B", style="thick"):
    style_map = {
        "thick": "thick",
        "dashed": "dashed, thick",
        "dotted": "dotted, thick",
        "arrow": "->, thick",
        "double arrow": "<->, thick",
    }
    tikz_style = style_map.get(style, "thick")
    lines = [r"\begin{tikzpicture}[scale=1]"]
    lines.append(f"  \\coordinate[label=below left:${n1}$] ({n1}) at ({x1},{y1});")
    lines.append(f"  \\coordinate[label=below right:${n2}$] ({n2}) at ({x2},{y2});")
    lines.append(f"  \\draw[{tikz_style}] ({n1})--({n2});")
    lines.append(f"  \\fill ({n1}) circle (1.5pt);")
    lines.append(f"  \\fill ({n2}) circle (1.5pt);")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_parallelogram(w, h, skew, na="A", nb="B", nc="C", nd="D"):
    lines = [r"\begin{tikzpicture}[scale=1, thick]"]
    lines.append(f"  \\coordinate[label=below left:${na}$]  ({na}) at (0,0);")
    lines.append(f"  \\coordinate[label=below right:${nb}$] ({nb}) at ({w},0);")
    lines.append(f"  \\coordinate[label=above right:${nc}$] ({nc}) at ({round(w + skew, 2)},{h});")
    lines.append(f"  \\coordinate[label=above left:${nd}$]  ({nd}) at ({skew},{h});")
    lines.append(f"  \\draw ({na})--({nb})--({nc})--({nd})--cycle;")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_trapezoid(bottom, top, h, na="A", nb="B", nc="C", nd="D"):
    offset = round((bottom - top) / 2, 2)
    lines = [r"\begin{tikzpicture}[scale=1, thick]"]
    lines.append(f"  \\coordinate[label=below left:${na}$]  ({na}) at (0,0);")
    lines.append(f"  \\coordinate[label=below right:${nb}$] ({nb}) at ({bottom},0);")
    lines.append(f"  \\coordinate[label=above right:${nc}$] ({nc}) at ({round(bottom - offset, 2)},{h});")
    lines.append(f"  \\coordinate[label=above left:${nd}$]  ({nd}) at ({offset},{h});")
    lines.append(f"  \\draw ({na})--({nb})--({nc})--({nd})--cycle;")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_ellipse(cx, cy, a, b, label="O"):
    lines = [r"\begin{tikzpicture}[scale=1, thick]"]
    lines.append(f"  \\draw ({cx},{cy}) ellipse ({a}cm and {b}cm);")
    lines.append(f"  \\fill ({cx},{cy}) circle (1.5pt) node[below]{{${label}$}};")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


# ── Hình không gian ──────────────────────────────────────────────────────────

def _gen_pyramid(side, height, na="A", nb="B", nc="C", nd="D", ns="S"):
    half = round(side / 2, 2)
    lines = [r"\begin{tikzpicture}[scale=1.3, thick,"]
    lines.append(r"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]")
    lines.append(f"  \\coordinate[label=below left:${na}$]  ({na}) at (0,0,0);")
    lines.append(f"  \\coordinate[label=below right:${nb}$] ({nb}) at ({side},0,0);")
    lines.append(f"  \\coordinate[label=right:${nc}$]       ({nc}) at ({side},{side},0);")
    lines.append(f"  \\coordinate[label=left:${nd}$]        ({nd}) at (0,{side},0);")
    lines.append(f"  \\coordinate[label=above:${ns}$]       ({ns}) at ({half},{half},{height});")
    lines.append(f"  % Đáy")
    lines.append(f"  \\draw ({na})--({nb})--({nc});")
    lines.append(f"  \\draw[dashed] ({nc})--({nd})--({na});")
    lines.append(f"  % Cạnh bên")
    lines.append(f"  \\draw ({ns})--({na}) ({ns})--({nb}) ({ns})--({nc});")
    lines.append(f"  \\draw[dashed] ({ns})--({nd});")
    lines.append(f"  \\draw[dashed] ({na})--({nc}) ({nb})--({nd});")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_cuboid(a, b, h, na="A", nb="B", nc="C", nd="D"):
    lines = [r"\begin{tikzpicture}[scale=1.2, thick,"]
    lines.append(r"    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]")
    lines.append(f"  \\coordinate[label=below left:${na}$]   ({na}) at (0,0,0);")
    lines.append(f"  \\coordinate[label=below right:${nb}$]  ({nb}) at ({a},0,0);")
    lines.append(f"  \\coordinate[label=right:${nc}$]        ({nc}) at ({a},{b},0);")
    lines.append(f"  \\coordinate[label=left:${nd}$]         ({nd}) at (0,{b},0);")
    lines.append(f"  \\coordinate[label=above left:${na}'$]  ({na}1) at (0,0,{h});")
    lines.append(f"  \\coordinate[label=above right:${nb}'$] ({nb}1) at ({a},0,{h});")
    lines.append(f"  \\coordinate[label=above right:${nc}'$] ({nc}1) at ({a},{b},{h});")
    lines.append(f"  \\coordinate[label=above left:${nd}'$]  ({nd}1) at (0,{b},{h});")
    lines.append(f"  % Đáy")
    lines.append(f"  \\draw ({na})--({nb})--({nc});")
    lines.append(f"  \\draw[dashed] ({nc})--({nd})--({na});")
    lines.append(f"  % Mặt trên")
    lines.append(f"  \\draw ({na}1)--({nb}1)--({nc}1)--({nd}1)--cycle;")
    lines.append(f"  % Cạnh bên")
    lines.append(f"  \\draw ({na})--({na}1) ({nb})--({nb}1) ({nc})--({nc}1);")
    lines.append(f"  \\draw[dashed] ({nd})--({nd}1);")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_cylinder(r, h):
    e = round(r * 0.35, 2)
    lines = [r"\begin{tikzpicture}[scale=1, thick]"]
    lines.append(f"  \\draw (0,0) ellipse ({r}cm and {e}cm);")
    lines.append(f"  \\draw (0,{h}) ellipse ({r}cm and {e}cm);")
    lines.append(f"  \\draw (-{r},0)--(-{r},{h});")
    lines.append(f"  \\draw ({r},0)--({r},{h});")
    lines.append(f"  \\draw[dashed] (0,0)--(0,{h});")
    lines.append(f"  \\fill (0,0) circle (1.5pt) node[below]{{$O$}};")
    lines.append(f"  \\fill (0,{h}) circle (1.5pt) node[above]{{$O'$}};")
    lines.append(f"  \\draw[<->] ({round(r + 0.4, 1)},0)--({round(r + 0.4, 1)},{h}) node[midway,right]{{$h={h}$}};")
    lines.append(f"  \\draw[<->] (0,{round(-e - 0.3, 1)})--({r},{round(-e - 0.3, 1)}) node[midway,below]{{$r={r}$}};")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_cone(r, h):
    e = round(r * 0.35, 2)
    lines = [r"\begin{tikzpicture}[scale=1, thick]"]
    lines.append(f"  \\draw (0,0) ellipse ({r}cm and {e}cm);")
    lines.append(f"  \\coordinate[label=above:$S$] (S) at (0,{h});")
    lines.append(f"  \\draw (-{r},0)--(S)--({r},0);")
    lines.append(f"  \\draw[dashed] (0,0)--(S);")
    lines.append(f"  \\fill (0,0) circle (1.5pt) node[below right]{{$O$}};")
    lines.append(f"  \\fill (S) circle (1.5pt);")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_sphere(r):
    e = round(r * 0.35, 2)
    lines = [r"\begin{tikzpicture}[scale=1, thick]"]
    lines.append(f"  \\shade[ball color=blue!10!white, opacity=0.5] (0,0) circle ({r}cm);")
    lines.append(f"  \\draw (0,0) circle ({r}cm);")
    lines.append(f"  \\draw[dashed] (0,0) ellipse ({r}cm and {e}cm);")
    lines.append(f"  \\fill (0,0) circle (1.5pt) node[below right]{{$O$}};")
    lines.append(f"  \\draw[<->] (0,0)--({r},0) node[midway,above]{{$R={r}$}};")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


# ── Đồ thị hàm số ────────────────────────────────────────────────────────────

def _gen_graph_quadratic(a, b, c, xmin=-5, xmax=5):
    ymin = round(a * ((- b / (2 * a)) ** 2) + b * (-b / (2 * a)) + c - 3, 1) if a != 0 else -5
    ymax = ymin + 10
    expr = f"{a}*x^2 + {b}*x + {c}"
    label = f"$y = {a}x^2"
    if b > 0: label += f" + {b}x"
    elif b < 0: label += f" {b}x"
    if c > 0: label += f" + {c}"
    elif c < 0: label += f" {c}"
    label += "$"
    lines = [r"\begin{tikzpicture}"]
    lines.append(r"\begin{axis}[")
    lines.append(f"  axis lines=center, xlabel={{$x$}}, ylabel={{$y$}},")
    lines.append(f"  xmin={xmin}, xmax={xmax}, ymin={round(ymin)}, ymax={round(ymax)},")
    lines.append(f"  grid=major, grid style={{gray!30}},")
    lines.append(f"  width=10cm, height=8cm, samples=100,")
    lines.append(r"]")
    lines.append(f"  \\addplot[blue, very thick, domain={xmin}:{xmax}] {{{expr}}};")
    lines.append(f"  \\addlegendentry{{{label}}}")
    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_graph_cubic(a, b, c, d, xmin=-5, xmax=5):
    expr = f"{a}*x^3 + {b}*x^2 + {c}*x + {d}"
    label = f"$y = {a}x^3"
    if b > 0: label += f" + {b}x^2"
    elif b < 0: label += f" {b}x^2"
    if c > 0: label += f" + {c}x"
    elif c < 0: label += f" {c}x"
    if d > 0: label += f" + {d}"
    elif d < 0: label += f" {d}"
    label += "$"
    lines = [r"\begin{tikzpicture}"]
    lines.append(r"\begin{axis}[")
    lines.append(f"  axis lines=center, xlabel={{$x$}}, ylabel={{$y$}},")
    lines.append(f"  xmin={xmin}, xmax={xmax},")
    lines.append(f"  grid=major, grid style={{gray!30}},")
    lines.append(f"  width=10cm, height=8cm, samples=100,")
    lines.append(r"]")
    lines.append(f"  \\addplot[blue, very thick, domain={xmin}:{xmax}] {{{expr}}};")
    lines.append(f"  \\addlegendentry{{{label}}}")
    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_graph_quartic(a, b, c, d, e, xmin=-5, xmax=5):
    expr = f"{a}*x^4 + {b}*x^3 + {c}*x^2 + {d}*x + {e}"
    lines = [r"\begin{tikzpicture}"]
    lines.append(r"\begin{axis}[")
    lines.append(f"  axis lines=center, xlabel={{$x$}}, ylabel={{$y$}},")
    lines.append(f"  xmin={xmin}, xmax={xmax},")
    lines.append(f"  grid=major, grid style={{gray!30}},")
    lines.append(f"  width=10cm, height=8cm, samples=100,")
    lines.append(r"]")
    lines.append(f"  \\addplot[blue, very thick, domain={xmin}:{xmax}] {{{expr}}};")
    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_graph_trig(func, a, b, c, d):
    fn = "sin" if func == "sin" else "cos"
    expr = f"{a}*{fn}(deg({b}*x + {c})) + {d}"
    lines = [r"\begin{tikzpicture}"]
    lines.append(r"\begin{axis}[")
    lines.append(f"  axis lines=center, xlabel={{$x$}}, ylabel={{$y$}},")
    lines.append(f"  xtick={{-6.28, -3.14, 0, 3.14, 6.28}},")
    lines.append(f"  xticklabels={{$-2\\pi$, $-\\pi$, $0$, $\\pi$, $2\\pi$}},")
    lines.append(f"  xmin=-7, xmax=7,")
    lines.append(f"  grid=major, grid style={{gray!30}},")
    lines.append(f"  width=12cm, height=7cm, samples=200,")
    lines.append(r"]")
    lines.append(f"  \\addplot[blue, very thick, domain=-7:7] {{{expr}}};")
    lines.append(f"  \\addlegendentry{{$y = {a}\\{fn}({b}x + {c}) + {d}$}}")
    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_graph_exp(func, a, b, c):
    if func == "e^x":
        expr = f"{a}*exp({b}*x) + {c}"
        legend = f"$y = {a} \\cdot e^{{{b}x}} + {c}$"
        dom = "-3:3"
    else:
        expr = f"{a}*ln({b}*x) + {c}"
        legend = f"$y = {a} \\cdot \\ln({b}x) + {c}$"
        dom = "0.1:8"
    lines = [r"\begin{tikzpicture}"]
    lines.append(r"\begin{axis}[")
    lines.append(f"  axis lines=center, xlabel={{$x$}}, ylabel={{$y$}},")
    lines.append(f"  grid=major, grid style={{gray!30}},")
    lines.append(f"  width=10cm, height=8cm, samples=100,")
    lines.append(r"]")
    lines.append(f"  \\addplot[blue, very thick, domain={dom}] {{{expr}}};")
    lines.append(f"  \\addlegendentry{{{legend}}}")
    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


# ── Biểu đồ ──────────────────────────────────────────────────────────────────

def _gen_bar_chart(labels: list, values: list, title=""):
    n = len(labels)
    lines = [r"\begin{tikzpicture}"]
    lines.append(r"\begin{axis}[")
    lines.append(f"  ybar, bar width=18pt,")
    lines.append(f"  xlabel={{}}, ylabel={{}},")
    if title:
        lines.append(f"  title={{{title}}},")
    lines.append(f"  symbolic x coords={{{', '.join(labels)}}},")
    lines.append(f"  xtick=data,")
    lines.append(f"  x tick label style={{rotate=0, anchor=north}},")
    lines.append(f"  nodes near coords, nodes near coords align={{vertical}},")
    lines.append(f"  ymin=0,")
    lines.append(f"  width=12cm, height=8cm,")
    lines.append(f"  grid=major, grid style={{gray!20}},")
    lines.append(r"]")
    coords = " ".join(f"({labels[i]},{values[i]})" for i in range(n))
    lines.append(f"  \\addplot[fill=blue!60] coordinates {{{coords}}};")
    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_pie_chart(labels: list, values: list, title=""):
    total = sum(values) if sum(values) > 0 else 1
    colors = ["blue!60", "red!60", "green!60", "orange!60", "purple!60",
              "cyan!60", "yellow!60", "pink!60", "brown!60", "gray!60"]
    lines = [r"\begin{tikzpicture}"]
    if title:
        lines.append(f"  \\node[font=\\large\\bfseries] at (0,4.5) {{{title}}};")
    start = 0
    for i, (label, val) in enumerate(zip(labels, values)):
        pct = val / total * 100
        end = start + val / total * 360
        mid = (start + end) / 2
        color = colors[i % len(colors)]
        lines.append(f"  % {label}: {pct:.1f}%")
        lines.append(f"  \\filldraw[fill={color}, draw=white, thick]")
        lines.append(f"    (0,0) -- ({start}:3cm) arc ({start}:{end}:3cm) -- cycle;")
        # Label
        import math
        lx = round(2 * math.cos(math.radians(mid)), 2)
        ly = round(2 * math.sin(math.radians(mid)), 2)
        lines.append(f"  \\node[font=\\small] at ({mid}:2cm) {{{label}\\\\{pct:.0f}\\%}};")
        start = end
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_line_chart(labels: list, values: list, title=""):
    n = len(labels)
    lines = [r"\begin{tikzpicture}"]
    lines.append(r"\begin{axis}[")
    if title:
        lines.append(f"  title={{{title}}},")
    lines.append(f"  xlabel={{}}, ylabel={{}},")
    lines.append(f"  symbolic x coords={{{', '.join(labels)}}},")
    lines.append(f"  xtick=data,")
    lines.append(f"  mark=*,")
    lines.append(f"  nodes near coords,")
    lines.append(f"  width=12cm, height=7cm,")
    lines.append(f"  grid=major, grid style={{gray!20}},")
    lines.append(r"]")
    coords = " ".join(f"({labels[i]},{values[i]})" for i in range(n))
    lines.append(f"  \\addplot[blue, very thick, mark=*] coordinates {{{coords}}};")
    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


def _gen_area_chart(labels: list, values: list, title=""):
    n = len(labels)
    lines = [r"\begin{tikzpicture}"]
    lines.append(r"\begin{axis}[")
    if title:
        lines.append(f"  title={{{title}}},")
    lines.append(f"  xlabel={{}}, ylabel={{}},")
    lines.append(f"  symbolic x coords={{{', '.join(labels)}}},")
    lines.append(f"  xtick=data,")
    lines.append(f"  width=12cm, height=7cm,")
    lines.append(f"  grid=major, grid style={{gray!20}},")
    lines.append(f"  stack plots=y,")
    lines.append(f"  area style,")
    lines.append(r"]")
    coords = " ".join(f"({labels[i]},{values[i]})" for i in range(n))
    lines.append(f"  \\addplot[fill=blue!30, draw=blue, thick] coordinates {{{coords}}} \\closedcycle;")
    lines.append(r"\end{axis}")
    lines.append(r"\end{tikzpicture}")
    return "\n".join(lines)


# ── Bảng biến thiên (tkz-tab) ────────────────────────────────────────────────
# Quy ước chung:
#   • \tkzTabInit{$x$/1, $y'$/1, $y$/2}{mốc_1, mốc_2, ...}
#   • \tkzTabLine{, dấu_1, điểm_1, dấu_2, điểm_2, ...}
#       Điểm: 0 (nghiệm), d (không xác định — điểm gián đoạn)
#       Dấu:  +, -
#   • \tkzTabVar{ chiều_1/giá_trị, chiều_2/giá_trị, ... }
#       Chiều: + (mũi tên lên), - (mũi tên xuống)
#       Với tiệm cận đứng: "+D-/y_1/y_2" hoặc "+D+/y_1/y_2"
# Tất cả hàm trả về đoạn code đã bọc \begin{tikzpicture}...\end{tikzpicture}.


def _fmt_num(v) -> str:
    """Format số: bỏ đuôi .0 cho integer đẹp hơn."""
    try:
        fv = float(v)
        if fv.is_integer():
            return str(int(fv))
        return str(round(fv, 4)).rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return str(v)


def _gen_bbt_quadratic(a, x0, y0):
    """Bảng biến thiên hàm bậc 2 y=a(x-x0)^2+y0.
    a>0: cực tiểu tại x0, y=y0; dấu y': -,0,+; chiều y: +∞ → y0 → +∞
    a<0: cực đại tại x0, y=y0; dấu y': +,0,-; chiều y: -∞ → y0 → -∞
    """
    xs = _fmt_num(x0)
    ys = _fmt_num(y0)
    try:
        a_val = float(a)
    except (TypeError, ValueError):
        a_val = 1.0
    if a_val >= 0:
        line = r"\tkzTabLine{, -, 0, +, }"
        var = r"\tkzTabVar{+/$+\infty$, -/$" + ys + r"$, +/$+\infty$}"
    else:
        line = r"\tkzTabLine{, +, 0, -, }"
        var = r"\tkzTabVar{-/$-\infty$, +/$" + ys + r"$, -/$-\infty$}"
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}"
        r"{$-\infty$, $" + xs + r"$, $+\infty$}" "\n"
        f"{line}\n{var}\n"
        r"\end{tikzpicture}"
    )


def _gen_bbt_cubic_two_extrema(a, x1, x2, y_cd, y_ct):
    """Bảng biến thiên bậc 3 có 2 cực trị.
    a>0: CĐ tại x1 (y=y_cd), CT tại x2 (y=y_ct); dấu y': +,0,-,0,+
    a<0: CT tại x1 (y=y_ct), CĐ tại x2 (y=y_cd); dấu y': -,0,+,0,-
    """
    x1s = _fmt_num(x1)
    x2s = _fmt_num(x2)
    ycd = _fmt_num(y_cd)
    yct = _fmt_num(y_ct)
    try:
        a_val = float(a)
    except (TypeError, ValueError):
        a_val = 1.0
    if a_val >= 0:
        line = r"\tkzTabLine{, +, 0, -, 0, +, }"
        var = (
            r"\tkzTabVar{-/$-\infty$, +/$" + ycd + r"$, -/$" + yct
            + r"$, +/$+\infty$}"
        )
    else:
        line = r"\tkzTabLine{, -, 0, +, 0, -, }"
        var = (
            r"\tkzTabVar{+/$+\infty$, -/$" + yct + r"$, +/$" + ycd
            + r"$, -/$-\infty$}"
        )
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=2.5]{$x$/1, $y'$/1, $y$/2}"
        r"{$-\infty$, $" + x1s + r"$, $" + x2s + r"$, $+\infty$}" "\n"
        f"{line}\n{var}\n"
        r"\end{tikzpicture}"
    )


def _gen_bbt_cubic_monotone(a):
    """Bảng biến thiên bậc 3 đơn điệu (không cực trị).
    a>0: dấu y' luôn + , y: -∞ → +∞
    a<0: dấu y' luôn - , y: +∞ → -∞
    """
    try:
        a_val = float(a)
    except (TypeError, ValueError):
        a_val = 1.0
    if a_val >= 0:
        line = r"\tkzTabLine{, +, }"
        var = r"\tkzTabVar{-/$-\infty$, +/$+\infty$}"
    else:
        line = r"\tkzTabLine{, -, }"
        var = r"\tkzTabVar{+/$+\infty$, -/$-\infty$}"
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}"
        r"{$-\infty$, $+\infty$}" "\n"
        f"{line}\n{var}\n"
        r"\end{tikzpicture}"
    )


def _gen_bbt_quartic_w(x1, x2, x3, y_ct1, y_cd, y_ct2):
    """Bảng biến thiên bậc 4 trùng phương có 3 cực trị (hình chữ W — a>0).
    x1<x2<x3; CT tại x1,x3; CĐ tại x2.
    """
    x1s, x2s, x3s = _fmt_num(x1), _fmt_num(x2), _fmt_num(x3)
    yct1, ycd, yct2 = _fmt_num(y_ct1), _fmt_num(y_cd), _fmt_num(y_ct2)
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=2]{$x$/1, $y'$/1, $y$/2}"
        r"{$-\infty$, $" + x1s + r"$, $" + x2s + r"$, $" + x3s
        + r"$, $+\infty$}" "\n"
        r"\tkzTabLine{, -, 0, +, 0, -, 0, +, }" "\n"
        r"\tkzTabVar{+/$+\infty$, -/$" + yct1 + r"$, +/$" + ycd
        + r"$, -/$" + yct2 + r"$, +/$+\infty$}" "\n"
        r"\end{tikzpicture}"
    )


def _gen_bbt_quartic_m(x1, x2, x3, y_cd1, y_ct, y_cd2):
    """Bảng biến thiên bậc 4 trùng phương có 3 cực trị (hình chữ M — a<0).
    CĐ tại x1, x3; CT tại x2.
    """
    x1s, x2s, x3s = _fmt_num(x1), _fmt_num(x2), _fmt_num(x3)
    ycd1, yct, ycd2 = _fmt_num(y_cd1), _fmt_num(y_ct), _fmt_num(y_cd2)
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=2]{$x$/1, $y'$/1, $y$/2}"
        r"{$-\infty$, $" + x1s + r"$, $" + x2s + r"$, $" + x3s
        + r"$, $+\infty$}" "\n"
        r"\tkzTabLine{, +, 0, -, 0, +, 0, -, }" "\n"
        r"\tkzTabVar{-/$-\infty$, +/$" + ycd1 + r"$, -/$" + yct
        + r"$, +/$" + ycd2 + r"$, -/$-\infty$}" "\n"
        r"\end{tikzpicture}"
    )


def _gen_bbt_quartic_u(x0, y0, direction="up"):
    """Bảng biến thiên bậc 4 trùng phương chỉ có 1 cực trị.
    direction="up": chữ U, CT tại x0 (a>0, b>=0)
    direction="down": chữ ngược U, CĐ tại x0 (a<0, b<=0)
    """
    xs, ys = _fmt_num(x0), _fmt_num(y0)
    if direction == "up":
        line = r"\tkzTabLine{, -, 0, +, }"
        var = r"\tkzTabVar{+/$+\infty$, -/$" + ys + r"$, +/$+\infty$}"
    else:
        line = r"\tkzTabLine{, +, 0, -, }"
        var = r"\tkzTabVar{-/$-\infty$, +/$" + ys + r"$, -/$-\infty$}"
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}"
        r"{$-\infty$, $" + xs + r"$, $+\infty$}" "\n"
        f"{line}\n{var}\n"
        r"\end{tikzpicture}"
    )


def _gen_bbt_frac_11(x_tcd, y_tcn, direction="inc"):
    """Bảng biến thiên hàm phân thức y=(ax+b)/(cx+d).
    x_tcd: nghiệm mẫu → tiệm cận đứng.
    y_tcn: giới hạn tại ±∞ → tiệm cận ngang.
    direction="inc": đồng biến trên từng khoảng (ad-bc>0)
    direction="dec": nghịch biến (ad-bc<0)
    """
    xd = _fmt_num(x_tcd)
    yn = _fmt_num(y_tcn)
    if direction == "inc":
        line = r"\tkzTabLine{, +, d, +, }"
        # y: yn → +∞ ; -∞ → yn
        var = (
            r"\tkzTabVar{-/$" + yn + r"$, +D-/$+\infty$/$-\infty$, +/$"
            + yn + r"$}"
        )
    else:
        line = r"\tkzTabLine{, -, d, -, }"
        var = (
            r"\tkzTabVar{+/$" + yn + r"$, -D+/$-\infty$/$+\infty$, -/$"
            + yn + r"$}"
        )
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}"
        r"{$-\infty$, $" + xd + r"$, $+\infty$}" "\n"
        f"{line}\n{var}\n"
        r"\end{tikzpicture}"
    )


def _gen_bbt_exp(a_gt_1=True):
    """BBT hàm mũ y=a^x.
    a>1 → đồng biến; 0<a<1 → nghịch biến.
    """
    if a_gt_1:
        line = r"\tkzTabLine{, +, }"
        var = r"\tkzTabVar{-/$0$, +/$+\infty$}"
    else:
        line = r"\tkzTabLine{, -, }"
        var = r"\tkzTabVar{+/$+\infty$, -/$0$}"
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}"
        r"{$-\infty$, $+\infty$}" "\n"
        f"{line}\n{var}\n"
        r"\end{tikzpicture}"
    )


def _gen_bbt_log(a_gt_1=True):
    """BBT hàm log y=log_a(x) trên (0,+∞).
    a>1 → đồng biến; 0<a<1 → nghịch biến.
    """
    if a_gt_1:
        line = r"\tkzTabLine{, +, }"
        var = r"\tkzTabVar{-/$-\infty$, +/$+\infty$}"
    else:
        line = r"\tkzTabLine{, -, }"
        var = r"\tkzTabVar{+/$+\infty$, -/$-\infty$}"
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}"
        r"{$0$, $+\infty$}" "\n"
        f"{line}\n{var}\n"
        r"\end{tikzpicture}"
    )


# ── Bảng xét dấu ─────────────────────────────────────────────────────────────

def _gen_sign_linear(a, x0):
    """Bảng xét dấu nhị thức f(x)=ax+b, nghiệm x0=-b/a.
    a>0: trái dấu a | 0 | cùng dấu a  →  -,0,+
    a<0: cùng dấu a | 0 | trái dấu a →  +,0,-
    """
    xs = _fmt_num(x0)
    try:
        a_val = float(a)
    except (TypeError, ValueError):
        a_val = 1.0
    if a_val >= 0:
        line = r"\tkzTabLine{, -, 0, +, }"
    else:
        line = r"\tkzTabLine{, +, 0, -, }"
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=3]{$x$/1, $f(x)$/1}"
        r"{$-\infty$, $" + xs + r"$, $+\infty$}" "\n"
        f"{line}\n"
        r"\end{tikzpicture}"
    )


def _gen_sign_quadratic_2roots(a, x1, x2):
    """Bảng xét dấu tam thức f(x)=ax^2+bx+c có 2 nghiệm x1<x2.
    a>0: +,0,-,0,+ (trong khoảng 2 nghiệm thì trái dấu a)
    a<0: -,0,+,0,- (trong khoảng 2 nghiệm thì trái dấu a)
    """
    x1s, x2s = _fmt_num(x1), _fmt_num(x2)
    try:
        a_val = float(a)
    except (TypeError, ValueError):
        a_val = 1.0
    if a_val >= 0:
        line = r"\tkzTabLine{, +, 0, -, 0, +, }"
    else:
        line = r"\tkzTabLine{, -, 0, +, 0, -, }"
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=2.5]{$x$/1, $f(x)$/1}"
        r"{$-\infty$, $" + x1s + r"$, $" + x2s + r"$, $+\infty$}" "\n"
        f"{line}\n"
        r"\end{tikzpicture}"
    )


def _gen_sign_quadratic_1root(a, x0):
    """Tam thức có nghiệm kép x0 (Δ=0): luôn cùng dấu a trừ tại x0."""
    xs = _fmt_num(x0)
    try:
        a_val = float(a)
    except (TypeError, ValueError):
        a_val = 1.0
    if a_val >= 0:
        line = r"\tkzTabLine{, +, 0, +, }"
    else:
        line = r"\tkzTabLine{, -, 0, -, }"
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=3]{$x$/1, $f(x)$/1}"
        r"{$-\infty$, $" + xs + r"$, $+\infty$}" "\n"
        f"{line}\n"
        r"\end{tikzpicture}"
    )


def _gen_sign_quadratic_noroot(a):
    """Tam thức Δ<0: cùng dấu a trên toàn R."""
    try:
        a_val = float(a)
    except (TypeError, ValueError):
        a_val = 1.0
    line = r"\tkzTabLine{, +, }" if a_val >= 0 else r"\tkzTabLine{, -, }"
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=3]{$x$/1, $f(x)$/1}"
        r"{$-\infty$, $+\infty$}" "\n"
        f"{line}\n"
        r"\end{tikzpicture}"
    )


def _gen_sign_product(roots_str, sign_first="+"):
    """Bảng xét dấu tích/thương f(x)=∏(x - x_i).
    roots_str: danh sách nghiệm phân cách bởi dấu phẩy, đã sort tăng dần.
    sign_first: dấu đầu tiên (bên trái tất cả nghiệm) — "+" hoặc "-".
    Dấu xen kẽ qua mỗi nghiệm.
    """
    roots = [r.strip() for r in str(roots_str).split(",") if r.strip()]
    if not roots:
        return _gen_sign_linear(1, 0)
    mocs = [r"$-\infty$"] + [f"${_fmt_num(r)}$" for r in roots] + [r"$+\infty$"]
    # Xen kẽ dấu bắt đầu từ sign_first
    signs = []
    cur = "+" if sign_first == "+" else "-"
    for _ in range(len(roots) + 1):
        signs.append(cur)
        cur = "-" if cur == "+" else "+"
    # Ghép line: , s1, 0, s2, 0, s3, ..., sn,
    parts = [""]
    for i, s in enumerate(signs):
        parts.append(s)
        if i < len(roots):
            parts.append("0")
    parts.append("")
    line = r"\tkzTabLine{" + ", ".join(parts) + "}"
    espcl = max(1.8, 8.0 / max(1, len(roots) + 1))
    return (
        r"\begin{tikzpicture}" "\n"
        r"\tkzTabInit[lgt=2, espcl=" + _fmt_num(round(espcl, 1))
        + r"]{$x$/1, $f(x)$/1}"
        r"{" + ", ".join(mocs) + "}\n"
        f"{line}\n"
        r"\end{tikzpicture}"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  SHAPE BUILDER DIALOG
# ══════════════════════════════════════════════════════════════════════════════

# Shape categories & definitions
_SHAPE_DEFS = {
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
        ("Hàm bậc 2 (ax\u00b2+bx+c)", "graph_quad"),
        ("Hàm bậc 3 (ax\u00b3+bx\u00b2+cx+d)", "graph_cubic"),
        ("Hàm bậc 4", "graph_quartic"),
        ("Hàm lượng giác (sin/cos)", "graph_trig"),
        ("Hàm mũ / logarit", "graph_exp"),
    ],
    "📊 Biểu đồ": [
        ("Biểu đồ cột", "bar_chart"),
        ("Biểu đồ tròn", "pie_chart"),
        ("Biểu đồ đường", "line_chart"),
        ("Biểu đồ miền", "area_chart"),
    ],
    "📑 Bảng biến thiên": [
        ("Hàm bậc 2 (có cực trị)", "bbt_quad"),
        ("Hàm bậc 3 (2 cực trị)", "bbt_cubic_2ex"),
        ("Hàm bậc 3 (đơn điệu)", "bbt_cubic_mono"),
        ("Hàm bậc 4 — chữ W (3 cực trị, a>0)", "bbt_quartic_w"),
        ("Hàm bậc 4 — chữ M (3 cực trị, a<0)", "bbt_quartic_m"),
        ("Hàm bậc 4 — 1 cực trị (U / ∩)", "bbt_quartic_u"),
        ("Phân thức y=(ax+b)/(cx+d)", "bbt_frac_11"),
        ("Hàm mũ y=a^x", "bbt_exp"),
        ("Hàm logarit y=log_a(x)", "bbt_log"),
    ],
    "➕ Bảng xét dấu": [
        ("Nhị thức ax+b", "sign_linear"),
        ("Tam thức bậc 2 (2 nghiệm)", "sign_quad_2"),
        ("Tam thức bậc 2 (nghiệm kép)", "sign_quad_1"),
        ("Tam thức bậc 2 (vô nghiệm)", "sign_quad_0"),
        ("Tích/thương nhiều nhân tử", "sign_product"),
    ],
}

# Fields per shape type
_SHAPE_FIELDS = {
    "triangle":    [("Ax", "0"), ("Ay", "0"), ("Bx", "4"), ("By", "0"),
                    ("Cx", "1.5"), ("Cy", "3"), ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C")],
    "right_triangle": [("Cạnh a (ngang)", "4"), ("Cạnh b (đứng)", "3"),
                       ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C")],
    "equilateral": [("Độ dài cạnh", "4"), ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C")],
    "isosceles":   [("Đáy", "4"), ("Chiều cao", "3"), ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C")],
    "square":      [("Cạnh", "4"), ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C"), ("Tên D", "D")],
    "rectangle":   [("Chiều rộng", "5"), ("Chiều cao", "3"),
                    ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C"), ("Tên D", "D")],
    "parallelogram": [("Đáy", "5"), ("Chiều cao", "3"), ("Độ nghiêng", "1.5"),
                      ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C"), ("Tên D", "D")],
    "trapezoid":   [("Đáy dưới", "6"), ("Đáy trên", "4"), ("Chiều cao", "3"),
                    ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C"), ("Tên D", "D")],
    "circle":      [("Tâm X", "0"), ("Tâm Y", "0"), ("Bán kính", "2"), ("Tên tâm", "O")],
    "ellipse":     [("Tâm X", "0"), ("Tâm Y", "0"),
                    ("Bán trục lớn a", "3"), ("Bán trục nhỏ b", "1.5"), ("Tên tâm", "O")],
    "segment":     [("X1", "0"), ("Y1", "0"), ("X2", "4"), ("Y2", "3"),
                    ("Tên điểm 1", "A"), ("Tên điểm 2", "B"),
                    ("Kiểu đường", "thick")],  # thick/dashed/dotted/arrow/double arrow
    "pyramid":     [("Cạnh đáy", "3"), ("Chiều cao", "4"),
                    ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C"), ("Tên D", "D"), ("Tên S", "S")],
    "cuboid":      [("Chiều dài", "4"), ("Chiều rộng", "3"), ("Chiều cao", "3"),
                    ("Tên A", "A"), ("Tên B", "B"), ("Tên C", "C"), ("Tên D", "D")],
    "cylinder":    [("Bán kính", "1.5"), ("Chiều cao", "3")],
    "cone":        [("Bán kính", "1.5"), ("Chiều cao", "3.5")],
    "sphere":      [("Bán kính", "2")],
    "graph_quad":  [("a", "1"), ("b", "-2"), ("c", "-3"), ("X min", "-5"), ("X max", "5")],
    "graph_cubic": [("a", "1"), ("b", "-3"), ("c", "0"), ("d", "2"),
                    ("X min", "-3"), ("X max", "4")],
    "graph_quartic": [("a", "1"), ("b", "0"), ("c", "-4"), ("d", "0"), ("e", "2"),
                      ("X min", "-3"), ("X max", "3")],
    "graph_trig":  [("Hàm", "sin"), ("a", "1"), ("b", "1"), ("c", "0"), ("d", "0")],
    "graph_exp":   [("Hàm", "e^x"), ("a", "1"), ("b", "1"), ("c", "0")],
    "bar_chart":   [("Nhãn (cách nhau bởi dấu ,)", "A,B,C,D,E"),
                    ("Giá trị (cách nhau bởi dấu ,)", "25,40,30,55,45"),
                    ("Tiêu đề", "")],
    "pie_chart":   [("Nhãn (cách nhau bởi dấu ,)", "Toán,Lý,Hóa,Sinh,Anh"),
                    ("Giá trị (cách nhau bởi dấu ,)", "30,25,20,15,10"),
                    ("Tiêu đề", "")],
    "line_chart":  [("Nhãn (cách nhau bởi dấu ,)", "T1,T2,T3,T4,T5,T6"),
                    ("Giá trị (cách nhau bởi dấu ,)", "10,25,18,35,28,42"),
                    ("Tiêu đề", "")],
    "area_chart":  [("Nhãn (cách nhau bởi dấu ,)", "T1,T2,T3,T4,T5,T6"),
                    ("Giá trị (cách nhau bởi dấu ,)", "10,25,18,35,28,42"),
                    ("Tiêu đề", "")],

    # ── Bảng biến thiên ─────────────────────────────────────────────
    "bbt_quad":        [("Hệ số a (a>0 CT, a<0 CĐ)", "1"),
                        ("Hoành độ đỉnh x₀", "1"),
                        ("Tung độ đỉnh y₀", "-2")],
    "bbt_cubic_2ex":   [("Hệ số a (a>0 hoặc a<0)", "1"),
                        ("Điểm cực trị thứ nhất x₁", "-1"),
                        ("Điểm cực trị thứ hai x₂", "1"),
                        ("Giá trị cực đại y_CĐ", "2"),
                        ("Giá trị cực tiểu y_CT", "-2")],
    "bbt_cubic_mono":  [("Hệ số a (a>0 tăng, a<0 giảm)", "1")],
    "bbt_quartic_w":   [("Nghiệm y'₁ (x₁)", "-1"),
                        ("Nghiệm y'₂ (x₂)", "0"),
                        ("Nghiệm y'₃ (x₃)", "1"),
                        ("y tại x₁ (CT)", "-1"),
                        ("y tại x₂ (CĐ)", "0"),
                        ("y tại x₃ (CT)", "-1")],
    "bbt_quartic_m":   [("Nghiệm y'₁ (x₁)", "-1"),
                        ("Nghiệm y'₂ (x₂)", "0"),
                        ("Nghiệm y'₃ (x₃)", "1"),
                        ("y tại x₁ (CĐ)", "1"),
                        ("y tại x₂ (CT)", "0"),
                        ("y tại x₃ (CĐ)", "1")],
    "bbt_quartic_u":   [("Hoành độ cực trị x₀", "0"),
                        ("Tung độ cực trị y₀", "-1"),
                        ("Hướng (up/down)", "up")],
    "bbt_frac_11":     [("Tiệm cận đứng x=", "1"),
                        ("Tiệm cận ngang y=", "2"),
                        ("Biến thiên (inc/dec)", "inc")],
    "bbt_exp":         [("Cơ số a>1? (yes/no)", "yes")],
    "bbt_log":         [("Cơ số a>1? (yes/no)", "yes")],

    # ── Bảng xét dấu ────────────────────────────────────────────────
    "sign_linear":     [("Hệ số a", "1"),
                        ("Nghiệm x₀", "-2")],
    "sign_quad_2":     [("Hệ số a", "1"),
                        ("Nghiệm x₁ (nhỏ)", "-1"),
                        ("Nghiệm x₂ (lớn)", "2")],
    "sign_quad_1":     [("Hệ số a", "1"),
                        ("Nghiệm kép x₀", "1")],
    "sign_quad_0":     [("Hệ số a", "1")],
    "sign_product":    [("Các nghiệm (tăng dần, cách nhau ,)", "-2, 0, 3"),
                        ("Dấu đầu tiên (+/-)", "+")],
}


class ShapeBuilderDialog(tk.Toplevel):
    """Dialog chọn loại hình + nhập thông số → tạo code TikZ."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Công cụ vẽ hình — Chọn loại & nhập thông số")
        self.configure(bg=BG)
        self.transient(parent)
        self.grab_set()
        self.result: Optional[str] = None

        try:
            from ui import set_dialog_icon
            set_dialog_icon(self)
        except Exception:
            pass

        self._fields: dict[str, tk.Entry] = {}
        self._current_type = ""
        self._build()

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(920, sw - 60), min(720, sh - 60)
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.minsize(800, 580)

    def _build(self):
        # ── Header ──
        hdr = tk.Frame(self, bg="#1F497D")
        hdr.pack(fill="x")
        tk.Label(hdr, text="  📐 Công cụ vẽ hình trực quan",
                 font=("Segoe UI", 13, "bold"), bg="#1F497D", fg="white"
                 ).pack(side="left", padx=12, pady=10)
        tk.Frame(self, bg="#10B981", height=3).pack(fill="x")

        # ── Bottom button bar (pack first so it stays at bottom) ──
        btn_bar = tk.Frame(self, bg="#E5E7EB", bd=0)
        btn_bar.pack(side="bottom", fill="x")
        tk.Frame(btn_bar, bg="#CBD5E1", height=1).pack(fill="x")

        inner_btn = tk.Frame(btn_bar, bg="#E5E7EB")
        inner_btn.pack(fill="x", padx=16, pady=10)

        tk.Button(inner_btn, text="  🔄 Xem trước code  ",
                  font=("Segoe UI", 10, "bold"),
                  bg="#8B5CF6", fg="white", activebackground="#7C3AED",
                  relief="flat", cursor="hand2", padx=14, pady=5,
                  command=self._preview_code).pack(side="left", padx=(0, 8))

        tk.Button(inner_btn, text="  ✅ Chèn vào Editor  ",
                  font=("Segoe UI", 10, "bold"),
                  bg="#10B981", fg="white", activebackground="#059669",
                  relief="flat", cursor="hand2", padx=14, pady=5,
                  command=self._generate).pack(side="right", padx=(8, 0))

        tk.Button(inner_btn, text="  Hủy  ",
                  font=("Segoe UI", 10),
                  bg="#94A3B8", fg="white", relief="flat", cursor="hand2",
                  padx=14, pady=5,
                  command=self.destroy).pack(side="right", padx=(0, 8))

        # ── Main content area ──
        main = ttk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=10, pady=8)

        # ── LEFT: Shape list ──
        left = tk.Frame(main, bg="white", bd=1, relief="solid")
        main.add(left, weight=0)

        tk.Label(left, text=" Chọn loại hình:", font=("Segoe UI", 10, "bold"),
                 bg="#EEF2FF", fg="#1F497D", anchor="w",
                 padx=8, pady=6).pack(fill="x")

        tree_frame = tk.Frame(left, bg="white")
        tree_frame.pack(fill="both", expand=True, padx=2, pady=2)

        style = ttk.Style()
        style.configure("Shape.Treeview", font=("Segoe UI", 10), rowheight=26)

        self._tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse",
                                  style="Shape.Treeview")
        self._tree.column("#0", width=220, minwidth=180)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True)

        self._shape_map = {}
        for cat, shapes in _SHAPE_DEFS.items():
            parent = self._tree.insert("", "end", text=f" {cat}", open=True)
            for label, stype in shapes:
                iid = self._tree.insert(parent, "end", text=f"  {label}")
                self._shape_map[iid] = stype

        self._tree.bind("<<TreeviewSelect>>", self._on_shape_select)

        # ── RIGHT: Fields + Code preview ──
        right = tk.Frame(main, bg=BG)
        main.add(right, weight=1)

        # Fields area (top half)
        self._fields_frame = tk.LabelFrame(right, text=" Thông số ",
                                           font=("Segoe UI", 10, "bold"),
                                           bg=BG, fg="#1F497D", padx=12, pady=8)
        self._fields_frame.pack(fill="both", expand=True, padx=4, pady=(0, 6))

        self._placeholder = tk.Label(self._fields_frame,
                                     text="← Chọn loại hình bên trái\n    để nhập thông số",
                                     font=("Segoe UI", 12), fg="#9CA3AF", bg=BG)
        self._placeholder.pack(expand=True)

        # Segment style dropdown (hidden initially)
        self._style_var = tk.StringVar(value="thick")

        # Code preview (bottom half)
        code_lf = tk.LabelFrame(right, text=" Mã TikZ sinh ra ",
                                font=("Segoe UI", 9, "bold"),
                                bg=BG, fg="#374151", padx=4, pady=4)
        code_lf.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        self._code_text = tk.Text(code_lf, font=("Consolas", 10),
                                  bg="#1E293B", fg="#E2E8F0",
                                  wrap="none", height=8, state="disabled",
                                  padx=6, pady=4)
        c_scroll = ttk.Scrollbar(code_lf, orient="vertical",
                                  command=self._code_text.yview)
        self._code_text.configure(yscrollcommand=c_scroll.set)
        c_scroll.pack(side="right", fill="y")
        self._code_text.pack(fill="both", expand=True)

    def _on_shape_select(self, event=None):
        sel = self._tree.selection()
        if not sel:
            return
        stype = self._shape_map.get(sel[0])
        if not stype:
            return

        self._current_type = stype

        # Clear old fields
        for w in self._fields_frame.winfo_children():
            w.destroy()
        self._fields.clear()

        fields = _SHAPE_FIELDS.get(stype, [])
        if not fields:
            return

        for i, (label, default) in enumerate(fields):
            row = tk.Frame(self._fields_frame, bg=BG)
            row.pack(fill="x", pady=3)

            tk.Label(row, text=label + ":", font=("Segoe UI", 10),
                     bg=BG, fg="#374151", width=24, anchor="w").pack(side="left")

            if label == "Kiểu đường":
                cb = ttk.Combobox(row, textvariable=self._style_var,
                                  values=["thick", "dashed", "dotted", "arrow", "double arrow"],
                                  state="readonly", width=18, font=("Segoe UI", 10))
                cb.pack(side="left", fill="x", expand=True)
                cb.set(default)
                self._fields[label] = cb
            elif label == "Hàm" and stype == "graph_trig":
                var = tk.StringVar(value=default)
                cb = ttk.Combobox(row, textvariable=var,
                                  values=["sin", "cos"],
                                  state="readonly", width=18, font=("Segoe UI", 10))
                cb.pack(side="left", fill="x", expand=True)
                self._fields[label] = cb
                self._trig_func_var = var
            elif label == "Hàm" and stype == "graph_exp":
                var = tk.StringVar(value=default)
                cb = ttk.Combobox(row, textvariable=var,
                                  values=["e^x", "ln(x)"],
                                  state="readonly", width=18, font=("Segoe UI", 10))
                cb.pack(side="left", fill="x", expand=True)
                self._fields[label] = cb
                self._exp_func_var = var
            else:
                e = tk.Entry(row, font=("Segoe UI", 11), bd=1, relief="solid")
                e.pack(side="left", fill="x", expand=True, ipady=3)
                e.insert(0, default)
                self._fields[label] = e

    def _get_val(self, key: str, fallback: str = "0") -> str:
        w = self._fields.get(key)
        if not w:
            return fallback
        if isinstance(w, ttk.Combobox):
            return w.get() or fallback
        return w.get().strip() or fallback

    def _get_float(self, key: str, fallback: float = 0) -> float:
        try:
            return float(self._get_val(key, str(fallback)))
        except ValueError:
            return fallback

    def _generate(self):
        code = self._build_code()
        if code:
            self.result = code
            self.destroy()

    def _preview_code(self):
        """Show TikZ code preview without closing dialog."""
        code = self._build_code()
        if code:
            self._show_code(code)

    def _show_code(self, code: str):
        self._code_text.config(state="normal")
        self._code_text.delete("1.0", "end")
        self._code_text.insert("1.0", code)
        self._code_text.config(state="disabled")

    def _build_code(self) -> Optional[str]:
        """Build TikZ code from current params."""
        t = self._current_type
        if not t:
            return None

        code = ""
        try:
            if t == "triangle":
                code = _gen_triangle(
                    self._get_float("Ax"), self._get_float("Ay"),
                    self._get_float("Bx"), self._get_float("By"),
                    self._get_float("Cx"), self._get_float("Cy"),
                    self._get_val("Tên A", "A"), self._get_val("Tên B", "B"),
                    self._get_val("Tên C", "C"))
            elif t == "right_triangle":
                code = _gen_right_triangle(
                    self._get_float("Cạnh a (ngang)", 4),
                    self._get_float("Cạnh b (đứng)", 3),
                    self._get_val("Tên A", "A"), self._get_val("Tên B", "B"),
                    self._get_val("Tên C", "C"))
            elif t == "equilateral":
                code = _gen_equilateral(
                    self._get_float("Độ dài cạnh", 4),
                    self._get_val("Tên A", "A"), self._get_val("Tên B", "B"),
                    self._get_val("Tên C", "C"))
            elif t == "isosceles":
                code = _gen_isosceles(
                    self._get_float("Đáy", 4), self._get_float("Chiều cao", 3),
                    self._get_val("Tên A", "A"), self._get_val("Tên B", "B"),
                    self._get_val("Tên C", "C"))
            elif t == "square":
                code = _gen_square(
                    self._get_float("Cạnh", 4),
                    self._get_val("Tên A", "A"), self._get_val("Tên B", "B"),
                    self._get_val("Tên C", "C"), self._get_val("Tên D", "D"))
            elif t == "rectangle":
                code = _gen_rectangle(
                    self._get_float("Chiều rộng", 5), self._get_float("Chiều cao", 3),
                    self._get_val("Tên A", "A"), self._get_val("Tên B", "B"),
                    self._get_val("Tên C", "C"), self._get_val("Tên D", "D"))
            elif t == "parallelogram":
                code = _gen_parallelogram(
                    self._get_float("Đáy", 5), self._get_float("Chiều cao", 3),
                    self._get_float("Độ nghiêng", 1.5),
                    self._get_val("Tên A", "A"), self._get_val("Tên B", "B"),
                    self._get_val("Tên C", "C"), self._get_val("Tên D", "D"))
            elif t == "trapezoid":
                code = _gen_trapezoid(
                    self._get_float("Đáy dưới", 6), self._get_float("Đáy trên", 4),
                    self._get_float("Chiều cao", 3),
                    self._get_val("Tên A", "A"), self._get_val("Tên B", "B"),
                    self._get_val("Tên C", "C"), self._get_val("Tên D", "D"))
            elif t == "circle":
                code = _gen_circle(
                    self._get_float("Tâm X"), self._get_float("Tâm Y"),
                    self._get_float("Bán kính", 2), self._get_val("Tên tâm", "O"))
            elif t == "ellipse":
                code = _gen_ellipse(
                    self._get_float("Tâm X"), self._get_float("Tâm Y"),
                    self._get_float("Bán trục lớn a", 3),
                    self._get_float("Bán trục nhỏ b", 1.5),
                    self._get_val("Tên tâm", "O"))
            elif t == "segment":
                code = _gen_segment(
                    self._get_float("X1"), self._get_float("Y1"),
                    self._get_float("X2", 4), self._get_float("Y2", 3),
                    self._get_val("Tên điểm 1", "A"), self._get_val("Tên điểm 2", "B"),
                    self._style_var.get())
            elif t == "pyramid":
                code = _gen_pyramid(
                    self._get_float("Cạnh đáy", 3), self._get_float("Chiều cao", 4),
                    self._get_val("Tên A", "A"), self._get_val("Tên B", "B"),
                    self._get_val("Tên C", "C"), self._get_val("Tên D", "D"),
                    self._get_val("Tên S", "S"))
            elif t == "cuboid":
                code = _gen_cuboid(
                    self._get_float("Chiều dài", 4), self._get_float("Chiều rộng", 3),
                    self._get_float("Chiều cao", 3),
                    self._get_val("Tên A", "A"), self._get_val("Tên B", "B"),
                    self._get_val("Tên C", "C"), self._get_val("Tên D", "D"))
            elif t == "cylinder":
                code = _gen_cylinder(
                    self._get_float("Bán kính", 1.5), self._get_float("Chiều cao", 3))
            elif t == "cone":
                code = _gen_cone(
                    self._get_float("Bán kính", 1.5), self._get_float("Chiều cao", 3.5))
            elif t == "sphere":
                code = _gen_sphere(self._get_float("Bán kính", 2))
            elif t == "graph_quad":
                code = _gen_graph_quadratic(
                    self._get_float("a", 1), self._get_float("b", -2),
                    self._get_float("c", -3),
                    self._get_float("X min", -5), self._get_float("X max", 5))
            elif t == "graph_cubic":
                code = _gen_graph_cubic(
                    self._get_float("a", 1), self._get_float("b", -3),
                    self._get_float("c", 0), self._get_float("d", 2),
                    self._get_float("X min", -3), self._get_float("X max", 4))
            elif t == "graph_quartic":
                code = _gen_graph_quartic(
                    self._get_float("a", 1), self._get_float("b", 0),
                    self._get_float("c", -4), self._get_float("d", 0),
                    self._get_float("e", 2),
                    self._get_float("X min", -3), self._get_float("X max", 3))
            elif t == "graph_trig":
                func = getattr(self, '_trig_func_var', tk.StringVar(value="sin")).get()
                code = _gen_graph_trig(
                    func,
                    self._get_float("a", 1), self._get_float("b", 1),
                    self._get_float("c", 0), self._get_float("d", 0))
            elif t == "graph_exp":
                func = getattr(self, '_exp_func_var', tk.StringVar(value="e^x")).get()
                code = _gen_graph_exp(
                    func,
                    self._get_float("a", 1), self._get_float("b", 1),
                    self._get_float("c", 0))
            elif t == "bbt_quad":
                code = _gen_bbt_quadratic(
                    self._get_float("Hệ số a (a>0 CT, a<0 CĐ)", 1),
                    self._get_float("Hoành độ đỉnh x₀", 1),
                    self._get_float("Tung độ đỉnh y₀", -2))
            elif t == "bbt_cubic_2ex":
                code = _gen_bbt_cubic_two_extrema(
                    self._get_float("Hệ số a (a>0 hoặc a<0)", 1),
                    self._get_float("Điểm cực trị thứ nhất x₁", -1),
                    self._get_float("Điểm cực trị thứ hai x₂", 1),
                    self._get_float("Giá trị cực đại y_CĐ", 2),
                    self._get_float("Giá trị cực tiểu y_CT", -2))
            elif t == "bbt_cubic_mono":
                code = _gen_bbt_cubic_monotone(
                    self._get_float("Hệ số a (a>0 tăng, a<0 giảm)", 1))
            elif t == "bbt_quartic_w":
                code = _gen_bbt_quartic_w(
                    self._get_float("Nghiệm y'₁ (x₁)", -1),
                    self._get_float("Nghiệm y'₂ (x₂)", 0),
                    self._get_float("Nghiệm y'₃ (x₃)", 1),
                    self._get_float("y tại x₁ (CT)", -1),
                    self._get_float("y tại x₂ (CĐ)", 0),
                    self._get_float("y tại x₃ (CT)", -1))
            elif t == "bbt_quartic_m":
                code = _gen_bbt_quartic_m(
                    self._get_float("Nghiệm y'₁ (x₁)", -1),
                    self._get_float("Nghiệm y'₂ (x₂)", 0),
                    self._get_float("Nghiệm y'₃ (x₃)", 1),
                    self._get_float("y tại x₁ (CĐ)", 1),
                    self._get_float("y tại x₂ (CT)", 0),
                    self._get_float("y tại x₃ (CĐ)", 1))
            elif t == "bbt_quartic_u":
                direction = self._get_val("Hướng (up/down)", "up").strip().lower()
                if direction not in ("up", "down"):
                    direction = "up"
                code = _gen_bbt_quartic_u(
                    self._get_float("Hoành độ cực trị x₀", 0),
                    self._get_float("Tung độ cực trị y₀", -1),
                    direction)
            elif t == "bbt_frac_11":
                direction = self._get_val("Biến thiên (inc/dec)", "inc").strip().lower()
                if direction not in ("inc", "dec"):
                    direction = "inc"
                code = _gen_bbt_frac_11(
                    self._get_float("Tiệm cận đứng x=", 1),
                    self._get_float("Tiệm cận ngang y=", 2),
                    direction)
            elif t == "bbt_exp":
                ans = self._get_val("Cơ số a>1? (yes/no)", "yes").strip().lower()
                code = _gen_bbt_exp(ans in ("yes", "y", "1", "true", "có"))
            elif t == "bbt_log":
                ans = self._get_val("Cơ số a>1? (yes/no)", "yes").strip().lower()
                code = _gen_bbt_log(ans in ("yes", "y", "1", "true", "có"))
            elif t == "sign_linear":
                code = _gen_sign_linear(
                    self._get_float("Hệ số a", 1),
                    self._get_float("Nghiệm x₀", -2))
            elif t == "sign_quad_2":
                code = _gen_sign_quadratic_2roots(
                    self._get_float("Hệ số a", 1),
                    self._get_float("Nghiệm x₁ (nhỏ)", -1),
                    self._get_float("Nghiệm x₂ (lớn)", 2))
            elif t == "sign_quad_1":
                code = _gen_sign_quadratic_1root(
                    self._get_float("Hệ số a", 1),
                    self._get_float("Nghiệm kép x₀", 1))
            elif t == "sign_quad_0":
                code = _gen_sign_quadratic_noroot(
                    self._get_float("Hệ số a", 1))
            elif t == "sign_product":
                code = _gen_sign_product(
                    self._get_val("Các nghiệm (tăng dần, cách nhau ,)", "-2, 0, 3"),
                    self._get_val("Dấu đầu tiên (+/-)", "+"))
            elif t in ("bar_chart", "pie_chart", "line_chart", "area_chart"):
                labels_str = self._get_val("Nhãn (cách nhau bởi dấu ,)", "A,B,C")
                values_str = self._get_val("Giá trị (cách nhau bởi dấu ,)", "10,20,30")
                title_str = self._get_val("Tiêu đề", "")
                labels = [l.strip() for l in labels_str.split(",") if l.strip()]
                try:
                    values = [float(v.strip()) for v in values_str.split(",") if v.strip()]
                except ValueError:
                    values = [0] * len(labels)
                while len(values) < len(labels):
                    values.append(0)
                values = values[:len(labels)]

                if t == "bar_chart":
                    code = _gen_bar_chart(labels, values, title_str)
                elif t == "pie_chart":
                    code = _gen_pie_chart(labels, values, title_str)
                elif t == "line_chart":
                    code = _gen_line_chart(labels, values, title_str)
                elif t == "area_chart":
                    code = _gen_area_chart(labels, values, title_str)

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi", f"Không thể tạo code:\n{e}")
            return None

        return code if code else None
