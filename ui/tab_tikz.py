"""
ui/tab_tikz.py — Tab TikZ: Vẽ hình toán học bằng TikZ, render chất lượng cao,
cho phép copy ảnh để chèn vào bài dạy.

Tính năng:
- Vẽ hình bằng AI (mô tả → TikZ code)
- Chỉnh sửa code bằng AI
- Console log pdflatex + đọc lỗi dễ hiểu
- Autocomplete / gợi ý code TikZ
- Hỗ trợ pgfplots cho đồ thị hàm số
"""
from __future__ import annotations
import base64
import os
import re
import shutil   # render_tikz_to_image + save PDF — top-level để tránh
                # NameError trong PyInstaller-frozen build (lazy local import
                # đôi khi không bind đúng scope khi exception trước đó xảy ra)
import tempfile
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field
from typing import List, Tuple, Any

BG = "#F9F7F4"

# ── TikZ Templates ───────────────────────────────────────────────────────────

_TEMPLATES = {
    # ==========================================
    # 1. HÌNH HỌC PHẲNG (2D GEOMETRY)
    # ==========================================
    "Tam giác ABC": r"""\begin{tikzpicture}[scale=1.5, thick]
  \coordinate[label=below left:$A$]  (A) at (0,0);
  \coordinate[label=below right:$B$] (B) at (4,0);
  \coordinate[label=above:$C$]       (C) at (1.5,3);
  \draw (A)--(B)--(C)--cycle;
  % Đánh dấu góc
  \pic[draw, angle radius=0.5cm, "$\alpha$"] {angle=B--A--C};
\end{tikzpicture}""",

    "Tam giác vuông ABC": r"""\begin{tikzpicture}[scale=1.5, thick]
  \coordinate[label=below left:$A$] (A) at (0,0);
  \coordinate[label=below right:$B$] (B) at (3,0);
  \coordinate[label=above left:$C$] (C) at (0,2);
  \draw (A)--(B)--(C)--cycle;
  % Ký hiệu góc vuông tại A
  \draw (A) rectangle ++(0.2,0.2);
  % Đánh dấu góc tại B và C
  \pic[draw, angle radius=0.6cm, "$33^\circ$"] {angle=C--B--A};
  \pic[draw, angle radius=0.5cm, "$57^\circ$"] {angle=A--C--B};
  \node at (1.5,0) [below] {$c$};
  \node at (0,1) [left] {$b$};
  \node at (1.5,1.2) [above right] {$a$};
\end{tikzpicture}""",

    "Hình bình hành ABCD": r"""\begin{tikzpicture}[scale=1.2, thick]
  \coordinate[label=below left:$A$] (A) at (0,0);
  \coordinate[label=below right:$B$] (B) at (4,0);
  \coordinate[label=above right:$C$] (C) at (5,2);
  \coordinate[label=above left:$D$] (D) at (1,2);
  \draw (A)--(B)--(C)--(D)--cycle;
  % Đường chéo
  \draw[dashed] (A)--(C) (B)--(D);
  \node at (2.5,1) [above] {$O$};
\end{tikzpicture}""",

    "Hình thang ABCD": r"""\begin{tikzpicture}[scale=1.2, thick]
  \coordinate[label=below left:$A$] (A) at (0,0);
  \coordinate[label=below right:$B$] (B) at (4,0);
  \coordinate[label=above right:$C$] (C) at (3,2);
  \coordinate[label=above left:$D$] (D) at (1,2);
  \draw (A)--(B)--(C)--(D)--cycle;
  % Đường cao
  \draw[dashed] (D)--(1,0) node[below] {$H$};
  \draw[dashed] (C)--(3,0) node[below] {$K$};
  \draw[<->] (0.5,2.2)--(1.5,2.2) node[midway,above] {$a$};
  \draw[<->] (3.2,2.2)--(4.2,2.2) node[midway,above] {$b$};
\end{tikzpicture}""",

    "Hình thoi ABCD": r"""\begin{tikzpicture}[scale=1.2, thick]
  \coordinate[label=below:$A$] (A) at (0,0);
  \coordinate[label=right:$B$] (B) at (2,1.5);
  \coordinate[label=above:$C$] (C) at (0,3);
  \coordinate[label=left:$D$] (D) at (-2,1.5);
  \draw (A)--(B)--(C)--(D)--cycle;
  \draw[dashed] (A)--(C) (B)--(D);
  \node at (0,1.5) [below right] {$O$};
  \draw (0,1.5) rectangle ++(0.2,0.2);
\end{tikzpicture}""",

    "Đường tròn & tiếp tuyến": r"""\begin{tikzpicture}[scale=1.2, thick]
  \coordinate (O) at (0,0);
  \draw (O) circle (2cm);
  \fill (O) circle (1.5pt) node[below]{$O$};
  % Điểm trên đường tròn
  \coordinate (A) at (60:2);
  \coordinate (B) at (-30:2);
  \fill (A) circle (1.5pt) node[above right]{$A$};
  \fill (B) circle (1.5pt) node[right]{$B$};
  \draw (A)--(B);
  % Tiếp tuyến tại A
  \draw[blue] ($(A)+(-1.5,{1.5*tan(30)})$)--($(A)+(1.5,{-1.5*tan(30)})$);
  \node[blue, above] at ($(A)+(0.8,0.3)$) {$d$};
  \draw[dashed] (O)--(A);
  % Góc vuông tiếp tuyến
  \pic[draw, angle radius=0.3cm] {angle=O--A--{$(A)+(1.5,{-1.5*tan(30)})$}};
\end{tikzpicture}""",

    "Đường tròn nội/ngoại tiếp": r"""\begin{tikzpicture}[scale=1.5, thick]
  \coordinate (A) at (0,0);
  \coordinate (B) at (4,0);
  \coordinate (C) at (1,3);
  \draw (A)--(B)--(C)--cycle;
  % Tâm ngoại tiếp & nội tiếp
  \coordinate (O) at (2,0.8);
  \coordinate (I) at (1.2,1.0);
  % Ngoại tiếp (gạch sọc — rõ khi photo)
  \draw[densely dashed] (O) circle (2.2cm);
  \fill (O) circle (1pt) node[below right] {$O$};
  % Nội tiếp (chấm — phân biệt với ngoại tiếp)
  \draw[densely dotted] (I) circle (0.9cm);
  \fill (I) circle (1pt) node[below right] {$I$};
\end{tikzpicture}""",

    # ==========================================
    # 2. HÌNH HỌC KHÔNG GIAN (3D GEOMETRY)
    # ==========================================
    "Hình chóp S.ABCD": r"""\begin{tikzpicture}[scale=1.4, thick,
    x={(1cm,0cm)}, y={(0.4cm,0.3cm)}, z={(0cm,1cm)}]
  \coordinate[label=below left:$A$]  (A) at (0,0,0);
  \coordinate[label=below right:$B$] (B) at (3,0,0);
  \coordinate[label=right:$C$]       (C) at (3,3,0);
  \coordinate[label=left:$D$]        (D) at (0,3,0);
  \coordinate[label=above:$S$]       (S) at (1.5,1.5,3.5);
  % Đáy
  \draw (A)--(B)--(C);
  % Cạnh bên
  \draw (S)--(A) (S)--(B) (S)--(C);
  % Nét đứt cạnh khuất
  \draw[dashed] (A)--(C) (B)--(D) (A)--(D) (C)--(D) (S)--(D);
\end{tikzpicture}""",

    "Hình trụ": r"""\begin{tikzpicture}[scale=1, thick]
  % Đáy dưới
  \draw (0,0) ellipse (1.5cm and 0.5cm);
  % Đáy trên
  \draw (0,3) ellipse (1.5cm and 0.5cm);
  % Cạnh bên
  \draw (-1.5,0)--(-1.5,3);
  \draw (1.5,0)--(1.5,3);
  % Trục & Chiều cao
  \draw[dashed] (0,0)--(0,3);
  \fill (0,0) circle (1.5pt) node[below]{$O$};
  \fill (0,3) circle (1.5pt) node[above]{$O'$};
  % Nhãn
  \draw[<->] (1.8,0)--(1.8,3) node[midway,right]{$h$};
  \draw[<->, dashed] (0,0)--(1.5,0) node[midway,below]{$r$};
\end{tikzpicture}""",

    "Hình nón": r"""\begin{tikzpicture}[scale=1, thick]
  % Đáy
  \draw (0,0) ellipse (2cm and 0.7cm);
  % Đỉnh
  \coordinate (S) at (0,3);
  \node[above] at (S) {$S$};
  % Cạnh bên
  \draw (-2,0)--(S) (2,0)--(S);
  % Đáy khuất
  \draw[dashed] (-2,0) arc (180:360:2cm and 0.7cm);
  \draw[dashed] (-2,0) arc (180:0:2cm and 0.7cm);
  % Tâm đáy
  \fill (0,0) circle (1.5pt) node[below] {$O$};
  \draw[dashed] (0,0)--(S);
  \draw[dashed] (0,0)--(2,0) node[midway,below] {$r$};
  \draw[<->] (0.3,0)--(0.3,3) node[midway,right] {$h$};
\end{tikzpicture}""",

    "Hình cầu": r"""\begin{tikzpicture}[scale=1, thick]
  \draw (0,0) circle (2cm);
  \draw[dashed] (2,0) arc (0:180:2cm and 0.6cm);
  \draw (2,0) arc (360:180:2cm and 0.6cm);
  % Đường kính
  \draw[<->] (-2,0.3)--(2,0.3) node[midway,above] {$2R$};
  \fill (0,0) circle (1.5pt) node[below right] {$O$};
  \draw[->, blue] (0,0)--(30:2) node[midway,above left] {$R$};
\end{tikzpicture}""",

    # ==========================================
    # 3. ĐỒ THỊ HÀM SỐ (GRAPHS)
    # ==========================================
    "Đồ thị hàm số bậc 3": r"""\begin{tikzpicture}
\begin{axis}[
  axis lines=center, xlabel={$x$}, ylabel={$y$},
  xmin=-3, xmax=4, ymin=-5, ymax=6,
  grid=major, grid style={gray!30},
  width=10cm, height=8cm, samples=100,
  legend pos=north west,
]
  \addplot[blue, very thick, domain=-2:3.5] {0.5*x^3 - 2*x^2 + 0.5*x + 3};
  \addlegendentry{$y = 0{,}5x^3 - 2x^2 + 0{,}5x + 3$}
  % Điểm cực trị
  \addplot[only marks, mark=*, red, mark size=3pt] coordinates {(0.13, 3.03) (2.54, -1.29)};
  \node[red, above right] at (axis cs:0.13, 3.03) {CĐ};
  \node[red, below right] at (axis cs:2.54, -1.29) {CT};
\end{axis}
\end{tikzpicture}""",

    "Đồ thị hàm số bậc 4 (Trùng phương)": r"""\begin{tikzpicture}
\begin{axis}[
  axis lines=center, xlabel={$x$}, ylabel={$y$},
  xmin=-3, xmax=3, ymin=-2, ymax=5,
  grid=major, grid style={gray!30},
  width=10cm, height=8cm, samples=100,
]
  \addplot[blue, very thick, domain=-2.5:2.5] {x^4 - 3*x^2 + 1};
  \addlegendentry{$y = x^4 - 3x^2 + 1$}
\end{axis}
\end{tikzpicture}""",

    "Parabol": r"""\begin{tikzpicture}
\begin{axis}[
  axis lines=center, xlabel=$x$, ylabel=$y$,
  xmin=-3, xmax=3, ymin=-1, ymax=5,
  width=8cm, height=7cm, samples=100,
]
  \addplot[blue, thick, domain=-2.5:2.5] {x^2};
  \addlegendentry{$y=x^2$}
  \node[red] at (axis cs:0,0) [circle,fill,inner sep=1.5pt] {};
  \node[below right] at (axis cs:0,0) {Đỉnh $O$};
\end{axis}
\end{tikzpicture}""",

    "Đồ thị lượng giác": r"""\begin{tikzpicture}
\begin{axis}[
  axis lines=center, xlabel={$x$}, ylabel={$y$},
  xmin=-7, xmax=7, ymin=-1.5, ymax=1.5,
  xtick={-6.28, -3.14, 0, 3.14, 6.28},
  xticklabels={$-2\pi$, $-\pi$, $0$, $\pi$, $2\pi$},
  grid=major, grid style={gray!30},
  width=12cm, height=6cm, samples=200, legend pos=north east,
]
  \addplot[blue, very thick, domain=-6.5:6.5] {sin(deg(x))};
  \addlegendentry{$y = \sin x$}
  \addplot[red, thick, dashed, domain=-6.5:6.5] {cos(deg(x))};
  \addlegendentry{$y = \cos x$}
\end{axis}
\end{tikzpicture}""",

    "Elip": r"""\begin{tikzpicture}
\begin{axis}[
  axis lines=center, xlabel=$x$, ylabel=$y$,
  xmin=-4, xmax=4, ymin=-4, ymax=4,
  width=8cm, height=8cm, samples=100, domain=-4:4,
]
  \addplot[blue, thick, domain=-3:3, samples=100] {sqrt(9 - x^2/4*9)};
  \addplot[blue, thick, domain=-3:3, samples=100] {-sqrt(9 - x^2/4*9)};
  \addlegendentry{$\frac{x^2}{4}+\frac{y^2}{9}=1$}
\end{axis}
\end{tikzpicture}""",

    "Hyperbol": r"""\begin{tikzpicture}
\begin{axis}[
  axis lines=center, xlabel=$x$, ylabel=$y$,
  xmin=-4, xmax=4, ymin=-4, ymax=4,
  width=8cm, height=8cm, samples=150,
]
  \addplot[blue, thick, domain=-4:-1] {sqrt(x^2 - 1)};
  \addplot[blue, thick, domain=1:4] {sqrt(x^2 - 1)};
  \addplot[blue, thick, domain=-4:-1] {-sqrt(x^2 - 1)};
  \addplot[blue, thick, domain=1:4] {-sqrt(x^2 - 1)};
  \addplot[dashed, gray, domain=-4:4] {x};
  \addplot[dashed, gray, domain=-4:4] {-x};
  \addlegendentry{$x^2 - y^2 = 1$}
\end{axis}
\end{tikzpicture}""",

    "Đồ thị hàm mũ & Logarit": r"""\begin{tikzpicture}
\begin{axis}[
  axis lines=center, xlabel=$x$, ylabel=$y$,
  xmin=-2, xmax=4, ymin=-2, ymax=4,
  grid=major, width=10cm, height=10cm, samples=100,
  legend pos=north west,
]
  \addplot[blue, thick, domain=-2:1.5] {exp(x)};
  \addlegendentry{$y=e^x$}
  \addplot[red, dashed, thick, domain=0.1:4] {ln(x)};
  \addlegendentry{$y=\ln x$}
  \addplot[gray, dotted, domain=-2:4] {x}; % Đường y=x
\end{axis}
\end{tikzpicture}""",

    # ==========================================
    # 4. BẢNG XÉT DẤU & BẢNG BIẾN THIÊN (TKZ-TAB)
    # ==========================================
    "Bảng xét dấu nhị thức bậc 1": r"""\begin{tikzpicture}
\tkzTabInit[lgt=3,espcl=3]{$x$ / 1, $f(x)=ax+b$ / 1}{$-\infty$, $-\frac{b}{a}$, $+\infty$}
\tkzTabLine{ , -, 0, +, }
\end{tikzpicture}""",

    "Bảng xét dấu tam thức bậc 2": r"""\begin{tikzpicture}
\tkzTabInit[lgt=3,espcl=2.5]{$x$ / 1, $f(x)=ax^2+bx+c$ / 1}{$-\infty$, $x_1$, $x_2$, $+\infty$}
\tkzTabLine{ , +, 0, -, 0, +, }
\end{tikzpicture}""",

    "Bảng biến thiên Parabol (a>0)": r"""\begin{tikzpicture}
\tkzTabInit[lgt=2,espcl=3]{$x$ / 1, $y'$ / 1, $y$ / 2}{$-\infty$, $-\frac{b}{2a}$, $+\infty$}
\tkzTabLine{ , -, 0, +, }
\tkzTabVar{+/ $+\infty$, -/ $-\frac{\Delta}{4a}$, +/ $+\infty$}
\end{tikzpicture}""",

    "Bảng biến thiên hàm bậc 3": r"""\begin{tikzpicture}
\tkzTabInit[lgt=2,espcl=3]{$x$ / 1, $y'$ / 1, $y$ / 2.5}{$-\infty$, $x_1$, $x_2$, $+\infty$}
\tkzTabLine{ , +, 0, -, 0, +, }
\tkzTabVar{-/ $-\infty$, +/ $y_{C\text{Đ}}$, -/ $y_{CT}$, +/ $+\infty$}
\end{tikzpicture}""",

    "Bảng biến thiên hàm trùng phương": r"""\begin{tikzpicture}
\tkzTabInit[lgt=2,espcl=2.5]{$x$ / 1, $y'$ / 1, $y$ / 2.5}{$-\infty$, $-x_0$, $0$, $x_0$, $+\infty$}
\tkzTabLine{ , -, 0, +, 0, -, 0, +, }
\tkzTabVar{+/ $+\infty$, -/ $y_{CT}$, +/ $y_{C\text{Đ}}$, -/ $y_{CT}$, +/ $+\infty$}
\end{tikzpicture}""",

    "Bảng biến thiên phân thức bậc 1 / bậc 1": r"""\begin{tikzpicture}
\tkzTabInit[lgt=2.5,espcl=3]{$x$ / 1, $y'$ / 1, $y$ / 2.5}{$-\infty$, $-\frac{d}{c}$, $+\infty$}
\tkzTabLine{ , +, d, +, }
\tkzTabVar{-/ $\frac{a}{c}$, +D-/ $+\infty$ / $-\infty$, +/ $\frac{a}{c}$}
\end{tikzpicture}""",

    # ==========================================
    # 5. BIỂU ĐỒ (CHARTS)
    # ==========================================
    "Biểu đồ cột đơn giản": r"""\begin{tikzpicture}
\begin{axis}[
  ybar,
  symbolic x coords={Toán, Lý, Hóa, Sinh},
  xtick=data, ylabel={Điểm}, title={Kết quả thi},
  width=10cm, height=7cm, nodes near coords,
  ymin=0, ymax=10,
]
  \addplot[fill=blue!50] coordinates {(Toán,8) (Lý,7) (Hóa,9) (Sinh,6)};
\end{axis}
\end{tikzpicture}""",

    "Biểu đồ đường": r"""\begin{tikzpicture}
\begin{axis}[
  axis lines=left, xlabel={Tháng}, ylabel={Doanh số},
  title={Tăng trưởng}, width=10cm, height=6cm,
  grid=major, ymin=0, ymax=30,
]
  \addplot[blue, mark=*, thick] coordinates {(1,10) (2,15) (3,12) (4,20) (5,25)};
  \addlegendentry{Năm 2024}
\end{axis}
\end{tikzpicture}""",

    "Trống (tự viết)": "",
}


# ── External KB merge ──────────────────────────────────────────────────────
# Templates above là FALLBACK (giữ tương thích nếu không đọc được KB ngoài).
# Chuẩn: app đọc data/tikz_kb/**/*.txt lúc startup → merge vào _TEMPLATES.
# User thêm template MỚI bằng cách tạo file .txt trong các thư mục con —
# KHÔNG cần build lại app.
def _merge_kb_templates() -> int:
    try:
        from services import tikz_kb
        tikz_kb.load()
        added = 0
        for tpl in tikz_kb.all_templates():
            # KB ưu tiên — ghi đè entry cùng tên trong _TEMPLATES
            _TEMPLATES[tpl.name] = tpl.code
            added += 1
        return added
    except Exception:
        # Nếu KB lỗi → giữ nguyên _TEMPLATES hardcoded (fallback)
        return 0


_KB_LOADED_COUNT = _merge_kb_templates()


# ── LaTeX wrapper ─────────────────────────────────────────────────────────────

_LATEX_TEMPLATE = r"""\documentclass[border=10pt,tikz,preview]{{standalone}}
\usepackage{{iftex}}
\ifPDFTeX
  \usepackage[utf8]{{inputenc}}
  \usepackage[T5]{{fontenc}}
\fi
\usepackage{{amsmath,amssymb,amsfonts}}
\usepackage{{preview}}
\usepackage{{tikz}}
\usepackage{{pgfplots}}
\usepackage{{tkz-tab}}
\usepackage{{tikz-3dplot}}
\usepackage{{array,booktabs,cellspace}}
\usepackage{{bm}}
\pgfplotsset{{compat=1.18}}
\usetikzlibrary{{calc,angles,quotes,patterns,patterns.meta,arrows,arrows.meta,decorations.markings,decorations.pathmorphing,decorations.pathreplacing,decorations.text,intersections,3d,shapes,shapes.geometric,positioning,fit,backgrounds,shadings,through,math,perspective}}
\PreviewEnvironment{{tikzpicture}}
\pagestyle{{empty}}
\begin{{document}}
{tikz_code}
\end{{document}}
"""

# ── AI Prompt for TikZ generation ────────────────────────────────────────────
# Kiến trúc: Computational Geometry Engine + Vector Reconstruction Engine +
# TikZ Rendering Engine + Visual Validation System.
# AI KHÔNG vẽ cảm tính — TÁI TẠO hình bằng toán học và dữ liệu.

_AI_DRAW_PROMPT = r"""Bạn là một HỆ THỐNG chuyên sâu gồm 4 engine:
  • Computational Geometry Engine
  • Vector Reconstruction Engine
  • TikZ Rendering Engine
  • Visual Validation System

Bạn KHÔNG phải AI vẽ hình thông thường. Bạn TÁI TẠO hình bằng TOÁN HỌC + DỮ LIỆU.

══════════════════════════════════════════════════════════════════════════
INPUT: Mô tả / đề bài hình học
══════════════════════════════════════════════════════════════════════════
{description}

{kb_examples}

══════════════════════════════════════════════════════════════════════════
[I] PHÂN LOẠI MODE (BẮT BUỘC — chọn TRƯỚC khi vẽ)
══════════════════════════════════════════════════════════════════════════
  • GEOMETRIC MODE  — bài toán hình học thuần (tam giác, đường tròn, chóp…)
  • PROBLEM MODE    — đề bài Toán có RÀNG BUỘC (vd: AB<AC, BD>CD, ⊥, //, ∈…)
                      → CHỈ vẽ minh hoạ; ràng buộc PHẢI ĐÚNG TUYỆT ĐỐI
  • VECTOR MODE     — tái tạo từ ảnh / logo / silhouette
  • HYBRID MODE     — hình học có yếu tố đồ hoạ
→ Mặc định: PROBLEM MODE cho đề bài Toán có chữ; GEOMETRIC MODE cho mô tả thuần.

══════════════════════════════════════════════════════════════════════════
[I.5] PROBLEM-CONSTRAINT EXTRACTION (BẮT BUỘC NẾU PROBLEM MODE)
══════════════════════════════════════════════════════════════════════════
TRƯỚC khi viết code, LIỆT KÊ TẤT CẢ ràng buộc trong đề (làm NGẦM, không in):

  RÀNG BUỘC TÍNH CHẤT:
  • Vuông tại đâu? (vd: ΔABC vuông tại A → AB ⊥ AC)
  • Bất đẳng thức cạnh? (vd: AB < AC → trong tọa độ: |AB| < |AC|)
  • So sánh đoạn? (vd: BD > CD → D gần C hơn B)

  RÀNG BUỘC THUỘC ĐƯỜNG:
  • Điểm nào THUỘC đoạn nào? (vd: D ∈ BC → D = (1-t)·B + t·C, t ∈ [0,1])
  • Đường vuông góc tại điểm? (vd: đường qua D ⊥ BC)
  • Giao điểm? (vd: M = (đường ⊥ BC tại D) ∩ AB)

  RÀNG BUỘC THỨ TỰ TRÊN ĐƯỜNG:
  • Khi đề nói "cắt AB tại M", M phải nằm trên ĐOẠN AB (không kéo dài)
    UNLESS đề nói rõ "cắt tia AB" hoặc "cắt AB kéo dài".
  • Khi đề nói "đường qua D ⊥ BC cắt AB tại M, cắt AC tại N":
    → đường thẳng ⊥ BC tại D phải GIAO CẢ AB lẫn AC.
    → Trong ΔABC vuông tại A, kiểm tra: với D ∈ BC, đường ⊥ BC tại D có
      thể KHÔNG giao đoạn AB nếu D quá gần B (vì đường này song song AB
      khi D = chân vuông góc từ A). Phải đặt D ở vị trí HỢP LÝ.

  CÁCH ĐẶT TỌA ĐỘ ƯU TIÊN (cho ΔABC vuông tại A, AB<AC):
    A = (0, 0)
    B = (0, 3)            % AB = 3 (theo trục y, vì AB nhỏ hơn)
    C = (5, 0)            % AC = 5 (theo trục x, AC > AB)
    Khi đó BC nối (0,3) và (5,0), vector BC = (5,-3).

  D ∈ BC với BD > CD: D gần C → D = B + 0.65·(C-B) = (3.25, 1.05).
  Đường ⊥ BC qua D: pháp tuyến = (3,5) (vuông góc với BC=(5,-3)).
    Cắt AB (trục y, x=0): solve x_D + 3t = 0 → t = -x_D/3. Vào y:
      y_M = y_D + 5·t = y_D - 5·x_D/3
    Nếu y_M ∈ [0, 3] → M ∈ đoạn AB; ngược lại M ngoài đoạn.
  Cắt AC (trục x, y=0): t = -y_D/5; x_N = x_D + 3·t = x_D - 3·y_D/5.

  KIỂM CHỨNG: tính nhẩm xem M, N có rơi đúng đoạn không. Nếu KHÔNG, đặt
  lại D vị trí khác. KHÔNG vẽ M, N "ước lượng" — phải tính chính xác.

⚠️ CẤM TUYỆT ĐỐI:
  ✗ Vẽ D ở giữa BC khi đề nói BD>CD (D phải gần C).
  ✗ Vẽ M ngoài đoạn AB khi đề nói "cắt AB tại M" (M phải trên ĐOẠN AB).
  ✗ Đoán vị trí M, N — phải dùng `intersection of` hoặc tính tọa độ.

CÚ PHÁP TIKZ TÍNH GIAO ĐIỂM (KHUYẾN NGHỊ):
  \coordinate (D) at ($(B)!0.65!(C)$);   % D = B + 0.65*(C-B), gần C
  % Đường thẳng ⊥ BC qua D — dùng \path để extend dài, dùng intersections:
  \path[name path=perp]
    ($(D)!1cm!90:(C)$) -- ($(D)!1cm!-90:(C)$);
  \path[name path=AB] (A)--(B);
  \path[name path=AC] (A)--(C);
  \draw[name intersections={{of=perp and AB, by=M}}];
  \draw[name intersections={{of=perp and AC, by=N}}];
  % Sau đó vẽ đường thẳng từ M đến N (đường ⊥ BC):
  \draw (M)--(N);

CẤM:
  ✗ \draw (D) -- (M);  với M là tọa độ "ước lượng"
  ✗ Dùng `y_vec_BC`, `x_vec_BC` hoặc bất kỳ macro nào tự bịa
    (PGF chỉ có \pgfmathsetmacro, KHÔNG có "y_vec_BC")

══════════════════════════════════════════════════════════════════════════
[II] NGUYÊN TẮC TUYỆT ĐỐI — KHOÁ LỖI
══════════════════════════════════════════════════════════════════════════
⚠️ NGUYÊN TẮC SỐ 1 — TỐI THIỂU (MINIMAL):
  ✗ KHÔNG thêm điểm/đoạn/nét/nhãn/đường mà MÔ TẢ KHÔNG ĐỀ CẬP.
  ✗ KHÔNG tô màu, KHÔNG fill, KHÔNG decoration nếu mô tả không yêu cầu.
  ✗ KHÔNG thêm "đường phụ cho đẹp" hoặc "đánh dấu cho rõ".
  ✓ Vẽ ĐÚNG NHỮNG GÌ MÔ TẢ NÓI — KHÔNG HƠN, KHÔNG KÉM.
  ✓ Output gọn: chỉ những lệnh `\draw` / `\fill` / `\node` cần thiết.

CẤM TUYỆT ĐỐI:
  ✗ Vẽ cảm tính (đoán hình)
  ✗ Đặt tọa độ tuỳ ý (mọi điểm phải có NGUỒN GỐC)
  ✗ Vẽ "gần đúng" hoặc "na ná"
  ✗ Bỏ qua kiểm chứng
  ✗ Thêm pattern / decoration nếu mô tả KHÔNG có item 12 về compound

BẮT BUỘC:
  ✓ Mọi điểm phải có nguồn gốc (derivation) — tính bằng tọa độ hoặc dùng `$(A)!t!(B)$`
  ✓ Mọi quan hệ phải đúng TOÁN HỌC (vuông góc, song song, tiếp xúc, bằng nhau…)
  ✓ Mọi đường cong phải có MÔ HÌNH TOÁN (Bézier, arc, ellipse) hoặc spline
  ✓ Tỉ lệ hợp lý: đoạn dài hơn → vẽ dài hơn; góc lớn hơn → vẽ rộng hơn
  ✓ Nếu mô tả ghi rõ "THẤY/KHUẤT" cho từng cạnh 3D → tuân thủ TUYỆT ĐỐI (không tự đảo)
  ✓ Nếu mô tả gợi ý "TỶ LỆ & SCALE TIKZ" → ÁP DỤNG đúng options đó vào `\begin{{tikzpicture}}[...]`
  ✓ Nếu mô tả có "(nhãn không rõ tại vị trí X)" → ƯU TIÊN logic toán học chọn tên hợp lý
    (vd: chân vuông góc thường là H, tâm thường là O/I, trung điểm thường là M)

══════════════════════════════════════════════════════════════════════════
[III] KIẾN TRÚC 5-LAYER (BẮT BUỘC — KHÔNG TRỘN LAYER)
══════════════════════════════════════════════════════════════════════════
Code TikZ phải chia rõ 5 phần, theo đúng thứ tự:
  1. CONFIG    — \tikzset, định nghĩa style, libraries, scale
  2. DATA      — \coordinate (mọi điểm)
  3. GEOMETRY  — \path (quan hệ ẩn — projection, intersection, midpoint)
  4. PATH      — \path (đường vô hình dùng để derive điểm phụ)
  5. RENDER    — \draw / \fill / \node (vẽ và nhãn cuối cùng)

Mẫu chuẩn:
  \begin{{tikzpicture}}[scale=1.2, thick]
    % CONFIG
    \tikzset{{tick/.style={{...}}}}
    % DATA
    \coordinate (A) at (0,0);
    \coordinate (B) at (3,0);
    % GEOMETRY (điểm phụ — trung điểm, chân vuông góc, …)
    \coordinate (M) at ($(A)!0.5!(B)$);
    \coordinate (H) at ($(A)!(C)!(B)$);   % chân vuông góc từ C xuống AB
    % RENDER
    \draw (A)--(B)--(C)--cycle;
    \draw pic [draw, angle radius=3mm] {{right angle = A--H--C}};
    \node[below left] at (A) {{$A$}};
  \end{{tikzpicture}}

══════════════════════════════════════════════════════════════════════════
[IV] QUY CHUẨN HÌNH HỌC PHẲNG (HHPT) — CÔNG THỨC TỌA ĐỘ
══════════════════════════════════════════════════════════════════════════

[1] TAM GIÁC — đặt tọa độ ƯU TIÊN trục để dễ kiểm soát:
  • Vuông tại A  : A=(0,0), B=(a,0), C=(0,b)        → AB ⟂ AC tự nhiên
  • Cân tại A    : A=(0,h), B=(-a,0), C=(a,0)        → trục đối xứng = Oy
  • Đều cạnh a   : A=(0,0), B=(a,0), C=(a/2, a*0.866)  (0.866 ≈ √3/2)
  • Bất kỳ       : đặt tự do nhưng KHÔNG thẳng hàng

[2] TRUNG ĐIỂM — dùng $(A)!0.5!(B)$ (KHÔNG tính bằng tay rồi gõ tọa độ):
    \coordinate (M) at ($(A)!0.5!(B)$);

[3] CHIA ĐOẠN THEO TỈ LỆ k:1-k:
    \coordinate (P) at ($(A)!0.4!(B)$);   % AP : PB = 0.4 : 0.6 = 2 : 3

[4] CHÂN ĐƯỜNG VUÔNG GÓC từ C xuống AB — projection syntax:
    \coordinate (H) at ($(A)!(C)!(B)$);

[5] PHÂN GIÁC — chia góc đôi bằng vector normalize hoặc thư viện angles:
    Hoặc dùng định lý phân giác (BD : DC = AB : AC).

[6] ĐƯỜNG TRÒN:
    \draw (O) circle (R);
    \coordinate (A) at ($(O)+(\theta:R)$);   % điểm trên (O) tại góc \theta

[7] TIẾP TUYẾN tại A của (O):
  → BẮT BUỘC: bán kính OA ⟂ tiếp tuyến tại A.
  → Vector tiếp tuyến = vector OA xoay 90°. Trong TikZ: tính (Ax-Ox, Ay-Oy)
    rồi xoay → (-(Ay-Oy), Ax-Ox).

[8] GÓC:
    \pic [draw, angle radius=6mm, "$\alpha$"] {{angle = B--A--C}};
  Góc vuông (CHỈ DÙNG `right angle`, KHÔNG dùng rectangle):
    \draw pic [draw, angle radius=3mm] {{right angle = A--B--C}};

[9] SONG SONG: mọi cặp cạnh song song phải có VECTOR CÙNG HƯỚNG.
    Đánh dấu bằng mũi tên giữa cạnh (1 mũi / 2 mũi để phân biệt cặp).

[10] CẠNH BẰNG NHAU: dùng tick chéo (1 vạch / 2 vạch — phân biệt nhóm):
    \tikzset{{tick/.style={{postaction={{decorate}}, decoration={{markings,
      mark=at position 0.5 with {{\draw (-2pt,-2pt)--(2pt,2pt);}}}}}}}}
    \draw[tick] (A)--(B);

══════════════════════════════════════════════════════════════════════════
[V] QUY CHUẨN HÌNH HỌC KHÔNG GIAN (HHKG)
══════════════════════════════════════════════════════════════════════════

[1] PHÉP CHIẾU XIÊN (oblique projection — chuẩn SGK):
    \begin{{tikzpicture}}[x={{(1cm,0cm)}}, y={{(0.5cm,0.3cm)}}, z={{(0cm,1cm)}}, scale=1.2]
  Quy ước trục:
    • x: ngang sang phải
    • y: chéo lùi (gãy 30°, rút ngắn 0.5)
    • z: thẳng đứng

[2] QUY TẮC NÉT VẼ — TUYỆT ĐỐI:
    • THẤY (mặt trước, không bị che) : \draw[thick]
    • KHUẤT (mặt sau, bị mặt trước che): \draw[dashed, thick]
    • Đường cao SH (trong khối): \draw[dashed]

[3] HÌNH CHÓP đều S.ABCD:
  → Đỉnh S nằm THẲNG ĐỨNG trên TÂM H của đáy (H = giao 2 đường chéo).
  → SH ⟂ (ABCD); SA = SB = SC = SD (tick chéo cạnh bên).
  → Vẽ đáy TRƯỚC; với góc nhìn chuẩn: AB, BC THẤY; CD, DA KHUẤT.
    SA, SB, SC THẤY; SD KHUẤT.

[4] HÌNH LĂNG TRỤ ĐỨNG: cạnh bên ⟂ 2 đáy; đáy trên = tịnh tiến đáy dưới
    theo trục z. Cạnh khuất → dashed.

[5] HÌNH TRỤ — RẤT QUAN TRỌNG: ĐÁY DƯỚI bị thân trụ CHE PHÍA SAU:
  ✓ Đáy DƯỚI:
      \draw         (-r,0) arc (180:360:r and r/3);   % nửa trước (liền)
      \draw[dashed] (-r,0) arc (180:0  :r and r/3);   % nửa sau (đứt)
  ✓ Đáy TRÊN (cao, không bị che): vẽ NGUYÊN ellipse liền:
      \draw (0,h) ellipse (r and r/3);
  ✓ Trục OO': dashed (vì bị thân trụ che).

[6] HÌNH NÓN — đáy bị thân nón che:
    \draw         (-r,0) arc (180:360:r and r/3);   % nửa trước (liền)
    \draw[dashed] (-r,0) arc (180:0  :r and r/3);   % nửa sau (đứt)
    \draw (S)--(-r,0); \draw (S)--(r,0);             % 2 đường sinh biên
    \draw[dashed] (S)--(0,0);                         % đường cao SO

[7] HÌNH CẦU — silhouette là đường tròn liền; xích đạo (đường tròn lớn nằm
    ngang): nửa trước liền, nửa sau dashed.

[8] GÓC VUÔNG TRONG 3D — CẤM `right angle` (chỉ chạy 2D); thay bằng "ô vuông"
    3 cạnh trong tọa độ 3D:
      \draw[thin] ($(A)+(0,0,0.3)$) -- ($(A)+(0.3,0,0.3)$) -- ($(A)+(0.3,0,0)$);

══════════════════════════════════════════════════════════════════════════
[VI] CONTINUITY & SMOOTHNESS (đường cong)
══════════════════════════════════════════════════════════════════════════
Mọi đường cong phải đạt:
  • C0 — liên tục (đầu mút trùng nhau)
  • C1 — tiếp tuyến liên tục (không gãy khúc)
  • C2 — độ cong mượt (ưu tiên)

Cú pháp:
  • Bézier:  (A) .. controls (c1) and (c2) .. (B)
  • Arc:     (A) arc (start_angle:end_angle:radius)
  • Ellipse: (O) ellipse (a and b)

══════════════════════════════════════════════════════════════════════════
[VII] SYMMETRY ENGINE
══════════════════════════════════════════════════════════════════════════
Nếu phát hiện đối xứng (qua trục/qua điểm):
  → Chỉ DỰNG 1 NỬA bằng tọa độ chính xác
  → Mirror sang nửa còn lại bằng `xscale=-1` hoặc đối xứng tọa độ
  → Giảm sai số + tối ưu code.

══════════════════════════════════════════════════════════════════════════
[VII.5] COMPOUND / DECORATIVE SHAPES (CHỈ KÍCH HOẠT KHI MÔ TẢ CÓ ITEM 12)
══════════════════════════════════════════════════════════════════════════
⚠️ CHỈ áp dụng section này NẾU mô tả input có MỤC 12 ghi rõ về hình trang trí
   (mũi tên cách điệu, recycle, hoa văn, ngôi sao…).
   Nếu mô tả KHÔNG nhắc gì về trang trí → BỎ QUA section này hoàn toàn,
   KHÔNG tự ý thêm pattern/decoration vào code.

[1] PATTERN ĐỐI XỨNG QUAY quanh 1 tâm (vd: 3 mũi tên xoay 120°):
    → Định nghĩa polygon GỐC dùng tọa độ (x,0) với x = bán kính phân bố.
    → Lặp bằng `\foreach \angle in {{0,120,240}}` + `rotate around={{\angle:(O)}}`:
      \foreach \angle in {{0,120,240}} {{
        \begin{{scope}}[rotate around={{\angle:(O)}}]
          \filldraw[fill=blue!20, draw=blue, thick]
            (1.0,0)--(1.5,0.3)--(1.3,0.3)--(1.3,0.7)
            --(0.7,0.7)--(0.7,0.3)--(0.5,0.3)--cycle;
        \end{{scope}}
      }}
    → BẮT BUỘC: "rotate around={{\angle:(O)}}" — KHÔNG dùng "rotate=\angle"
      vì sẽ xoay quanh gốc (0,0), không phải tâm O.

[2] MŨI TÊN ĐƠN giản:
    → Polygon 7 đỉnh: thân (rectangle) + đầu (triangle).
    → Hoặc dùng arrows.meta: `\draw[-{{Stealth[length=8pt,width=6pt]}}] (A)--(B);`

[3] BIỂU TƯỢNG TÁI CHẾ (recycle) = 3 mũi tên CONG xoay 120°:
    → Mỗi mũi tên = arc + đầu mũi tên ở cuối arc.
    → Lặp pattern xoay như [1].

[4] NGÔI SAO N CÁNH:
    → Dùng `\foreach \i in {{0,...,N-1}}` với góc \i*(360/N).

[5] CẤM trộn pattern và đối tượng chính trong 1 \draw — tách scope rõ ràng.

══════════════════════════════════════════════════════════════════════════
[VIII] ĐỒ THỊ HÀM SỐ (PGFPLOTS) — TRÁNH LỖI COMPILE
══════════════════════════════════════════════════════════════════════════
A. Biến tự do mặc định = `x`. CẤM dùng `y` làm biến tự do.
   ✗ \addplot[domain=0:12] (f(y), y);
   ✓ \addplot[variable=\t, domain=0:12, samples=100] ({{f(\t)}}, \t);
B. Hàm y=f(x): \addplot[domain=-5:5, samples=100] {{x^2 + 2*x}};
   (bao biểu thức trong {{...}}, KHÔNG dùng (...))
C. Phép NHÂN tường minh: `2*x` (CẤM `2x`). Lũy thừa: `^`.
D. Lượng giác: bọc deg(): `sin(deg(x))`, `cos(deg(x))`.
E. samples=100 (cong) hoặc samples=200 (lượng giác / sóng).
F. Cực trị: \addplot[only marks, mark=*, mark size=2pt] coordinates {{(1,2)}};

══════════════════════════════════════════════════════════════════════════
[IX] BẢNG BIẾN THIÊN (tkz-tab) — khi đề khảo sát hàm số
══════════════════════════════════════════════════════════════════════════
Cú pháp:
  \begin{{tikzpicture}}
    \tkzTabInit[lgt=2, espcl=3]{{$x$/1, $y'$/1, $y$/2}}{{$-\infty$, $x_0$, $+\infty$}}
    \tkzTabLine{{, -, 0, +, }}
    \tkzTabVar{{+/$+\infty$, -/$y_0$, +/$+\infty$}}
  \end{{tikzpicture}}

Khi đề yêu cầu KHẢO SÁT hàm số → trả VỀ CẢ 2 tikzpicture: (1) đồ thị,
(2) BBT — đồng bộ TXĐ/nghiệm/cực trị/tiệm cận.

══════════════════════════════════════════════════════════════════════════
[X] PACKAGES + LIBRARIES CÓ SẴN TRONG APP
══════════════════════════════════════════════════════════════════════════
amsmath, amssymb, tikz, pgfplots (compat=1.18), tkz-tab, bm, array, booktabs.
TikZ libraries: calc, angles, quotes, patterns, arrows.meta,
decorations.markings, intersections, decorations.pathreplacing, positioning,
3d, shapes.geometric, backgrounds.

══════════════════════════════════════════════════════════════════════════
[XI] OUTPUT FORMAT — CHỈ CODE, KHÔNG GIẢI THÍCH
══════════════════════════════════════════════════════════════════════════
1. CHỈ trả code TikZ — bắt đầu \begin{{tikzpicture}}, kết thúc \end{{tikzpicture}}.
2. KHÔNG kèm \documentclass / \usepackage / \begin{{document}} (app tự thêm).
3. KHÔNG dùng marker rời `===tikz===` / `===endtikz===` / fence ```tikz.
4. Tiếng Việt có dấu cho nhãn / comment.
5. Comment chia 5 layer rõ ràng (% CONFIG, % DATA, % GEOMETRY, % PATH, % RENDER).

══════════════════════════════════════════════════════════════════════════
[XII] SELF-CHECK — TRƯỚC KHI XUẤT (BẮT BUỘC, không bỏ qua)
══════════════════════════════════════════════════════════════════════════
  ✔ TỐI THIỂU?     (KHÔNG có điểm/đoạn/nhãn nào THỪA so với mô tả)
                   ✗ Nếu mô tả nói 2 đường tròn tiếp xúc → CHỈ vẽ 2 đường tròn
                     và điểm tiếp xúc, KHÔNG thêm dây cung/tiếp tuyến/màu...
                   ✗ KHÔNG tô màu fill nếu mô tả không yêu cầu.
                   ✗ KHÔNG thêm \pic angle nếu mô tả không có ký hiệu góc.
  ✔ Đủ?            (KHÔNG thiếu thông tin mà mô tả ĐÃ ghi)
  ✔ Đúng hình học?  (vuông là vuông, song song là song song, tiếp tuyến ⟂ bán kính)
  ✔ Đúng tỉ lệ?    (cạnh dài hơn vẽ dài hơn)
  ✔ Đúng nhãn?    (tên điểm khớp mô tả CHÍNH XÁC, không bịa thêm tên mới,
                   không trùng lặp, không đè cạnh)
  ✔ Đúng nét khuất? (3D: thấy=liền, khuất=dashed; trụ/nón: nửa sau đáy đứt)
  ✔ Không suy biến? (3 điểm không thẳng hàng nếu là tam giác; mẫu ≠ 0)
  ✔ Mượt?          (đường cong C1 trở lên, không gãy khúc giả)
  ✔ Compound?      (CHỈ vẽ pattern nếu mô tả có item 12 — KHÔNG tự thêm)

Nếu bất kỳ check nào SAI → SỬA, KHÔNG được xuất code sai.
NGUYÊN TẮC VÀNG: "Đúng và TỐI THIỂU" > "Đầy đủ và THỪA"

══════════════════════════════════════════════════════════════════════════
META GOAL: TikZ chuẩn SGK + chuẩn đề thi chuyên + production-ready.
Bạn KHÔNG vẽ. Bạn TÁI TẠO hình học bằng TOÁN HỌC và DỮ LIỆU.
══════════════════════════════════════════════════════════════════════════"""

_AI_EDIT_PROMPT = r"""Bạn là HỆ THỐNG Computational Geometry + TikZ Rendering Engine
chuyên debug và refactor code TikZ.

══════════════════════════════════════════════════════════════════════════
CODE TIKZ HIỆN TẠI:
══════════════════════════════════════════════════════════════════════════
{current_code}

══════════════════════════════════════════════════════════════════════════
YÊU CẦU CHỈNH SỬA:
══════════════════════════════════════════════════════════════════════════
{edit_request}

══════════════════════════════════════════════════════════════════════════
[I] NGUYÊN TẮC TUYỆT ĐỐI
══════════════════════════════════════════════════════════════════════════
CẤM:
  ✗ Đoán tọa độ — mọi điểm phải truy được nguồn gốc
  ✗ Vẽ "gần đúng" — vuông là VUÔNG, song song là SONG SONG
  ✗ Bỏ qua kiểm chứng (self-check)

BẮT BUỘC:
  ✓ GIỮ NGUYÊN phần không liên quan; chỉ sửa phần được yêu cầu
  ✓ Tổ chức code theo 5-layer: CONFIG → DATA → GEOMETRY → PATH → RENDER
  ✓ Mọi quan hệ hình học phải đúng TUYỆT ĐỐI

══════════════════════════════════════════════════════════════════════════
[II] OUTPUT
══════════════════════════════════════════════════════════════════════════
1. Trả TOÀN BỘ code TikZ đã chỉnh — từ \begin{{tikzpicture}} đến \end{{tikzpicture}}.
2. KHÔNG kèm \documentclass / \usepackage / \begin{{document}} (app tự thêm).
3. KHÔNG dùng marker `===tikz===` / `===endtikz===` / fence ```tikz.
4. Thêm comment `% sửa: <lý do>` ở phần đã chỉnh.

══════════════════════════════════════════════════════════════════════════
[III] PACKAGES + LIBRARIES CÓ SẴN
══════════════════════════════════════════════════════════════════════════
amsmath, amssymb, tikz, pgfplots (compat=1.18), tkz-tab, bm, array, booktabs.
TikZ libraries: calc, angles, quotes, patterns, arrows.meta,
decorations.markings, intersections, decorations.pathreplacing, positioning,
3d, shapes.geometric, backgrounds.

══════════════════════════════════════════════════════════════════════════
[IV] CHECKLIST TRƯỚC KHI XUẤT
══════════════════════════════════════════════════════════════════════════

[A] PGFPLOTS:
  • Biến tự do mặc định = `x`. CẤM dùng `y`. Parametric: `variable=\t`.
  • Hàm: `\addplot[domain=-5:5, samples=100] {{x^2 + 2*x}};` — bao {{...}}.
  • Phép nhân tường minh: `2*x` (KHÔNG `2x`). Lũy thừa `^`.
  • Lượng giác: `sin(deg(x))`, `cos(deg(x))`.
  • Mọi \addplot PHẢI NẰM TRONG \begin{{axis}}...\end{{axis}}.

[B] TIKZ CHUNG:
  • Tọa độ: `(x,y)` dùng dấu phẩy; tên node không khoảng trắng/dấu.
  • Nhãn: `\node[anchor=...] at (P) {{$A$}};` — anchor để tránh đè.
  • Trung điểm: `$(A)!0.5!(B)$`. Chân vuông góc: `$(A)!(C)!(B)$`.
  • Góc vuông 2D: `\draw pic [draw, angle radius=3mm] {{right angle=A--B--C}};`
  • Góc vuông 3D: vẽ "ô vuông" 3 cạnh — KHÔNG dùng `right angle` trong 3D.

[C] LOGIC HÌNH HỌC — sau khi sửa kiểm tra:
  ✔ Nhãn điểm/cạnh/góc còn khớp đề gốc?
  ✔ Vuông góc / song song / tiếp xúc / bằng nhau còn đúng?
  ✔ Tỉ lệ hợp lý (đoạn dài hơn vẽ dài hơn)?
  ✔ 3D: thấy=liền, khuất=dashed?
  ✔ Trụ/nón: nửa SAU đáy dưới đứt (vì bị thân khối che)?

══════════════════════════════════════════════════════════════════════════
CHỈ trả code TikZ, KHÔNG giải thích.
══════════════════════════════════════════════════════════════════════════"""

_AI_DESCRIBE_IMAGE_PROMPT = r"""Bạn là chuyên gia hình học Toán THPT + Computer Vision.
Sứ mệnh: phân tích ảnh/hình vẽ và xuất MÔ TẢ CHI TIẾT đủ để 1 AI khác vẽ lại CHÍNH XÁC bằng TikZ.

══════════════════════════════════════════════════════════════════════════
QUY TRÌNH PHÂN TÍCH 5 BƯỚC (THỰC HIỆN NGẦM — KHÔNG IN RA)
══════════════════════════════════════════════════════════════════════════
[A] PHÂN LOẠI HÌNH (chọn 1 nhóm — có thể CHỒNG nếu hình kép):
    • 3D: chóp / lăng trụ / trụ / nón / cầu / hộp / đa diện đều
    • 2D: tam giác / tứ giác / đường tròn / đa giác / cung tròn / conic
    • Đồ thị hàm số (kèm hệ trục, tiệm cận, điểm cực trị)
    • Bảng biến thiên (BBT) / Bảng xét dấu (BXD)
    • Hình thực tế / mô phỏng / vẽ tay / sơ đồ
    • COMPOUND/TRANG TRÍ (CHỈ KHI THỰC SỰ THẤY — KHÔNG BỊA): mũi tên cách điệu,
      recycle, ngôi sao, hoa văn LẶP ĐỐI XỨNG quanh tâm. Nếu ảnh là HÌNH HỌC
      THUẦN (chỉ có điểm/đoạn/đường tròn) → KHÔNG ghi gì cho mục này.

[B] TRÍCH XUẤT NHÃN (KHÔNG SAI - KHÔNG THIẾU - KHÔNG BỊA):
    • Tên điểm: A, B, C, S, M, N, H, K, O, I... — đọc CHÍNH XÁC từng chữ
    • Nhãn trục: x, y, z (3D) hoặc x, y (2D)
    • Giá trị số: $-\infty$, $+\infty$, $0$, các phân số/căn cụ thể (vd: $-\dfrac{22}{27}$)
    • Ký hiệu toán: $\alpha, \beta, \theta$, ô vuông góc, cung, vạch song song, vạch bằng nhau
    • → Nếu nhãn nhòe/không đọc được, GHI rõ "(nhãn không rõ tại vị trí X)" — KHÔNG tự bịa.

[C] TỌA ĐỘ TƯƠNG ĐỐI:
    • Trên / dưới / trái / phải / trước / sau (3D) so với điểm khác
    • Độ sâu trong không gian 3D (góc nhìn, vị trí biểu kiến)
    • Tính đối xứng (qua trục / qua tâm) nếu có

[D] NÉT ĐẶC BIỆT:
    • Nét LIỀN (đối tượng thấy) vs nét ĐỨT (khuất sau mặt khác)
    • Mũi tên (chiều biến thiên, vector, hướng trục)
    • Vùng tô màu / pattern (gạch chéo / chấm)
    • Đoạn vuông góc (ô vuông), cung góc, vạch bằng nhau (1 vạch / 2 vạch)

[E] TỶ LỆ ƯỚC LƯỢNG:
    • Tỷ số cạnh / bán kính / chiều cao (vd: AB ≈ 2·AC, h ≈ 1.5·r)
    • Góc nhìn 3D (góc xoay trục, độ rút ngắn của trục y)
    • Vị trí gốc tọa độ trong khung hình

[F] HÌNH TRANG TRÍ / COMPOUND SHAPES (CHỈ MÔ TẢ NẾU ẢNH THỰC SỰ CÓ):
    ⚠️ NGUYÊN TẮC SỐ 1: KHÔNG BỊA. Nếu ảnh CHỈ là hình học toán học thuần
    (điểm, đoạn, đường tròn, tam giác, đồ thị…) → BỎ QUA mục này hoàn toàn,
    KHÔNG viết gì.
    Chỉ áp dụng khi ảnh có CỤ THỂ:
    • Mũi tên cách điệu (arrow stylized) lặp đối xứng quanh 1 tâm
    • Biểu tượng tái chế (recycle = 3 mũi tên cong xoay 120°)
    • Ngôi sao, hoa văn hexagon, pattern hoa lá
    • Logo / icon vector
    Khi áp dụng, mô tả: loại, số đỉnh polygon, tâm pattern, góc xoay, số bản
    sao, hướng, màu fill/draw.

══════════════════════════════════════════════════════════════════════════
QUY TẮC ĐẶC BIỆT
══════════════════════════════════════════════════════════════════════════
• NHIỀU ẢNH (user dán nhiều): tổng hợp thông tin từ TẤT CẢ ảnh. Các ảnh có
  thể là góc nhìn khác nhau hoặc bước trung gian của cùng 1 hình. Nếu mâu
  thuẫn → ưu tiên ảnh có nhãn rõ nhất.
• ẢNH NHÒE / KHÔNG RÕ: suy luận theo logic toán chuẩn (chóp đều: đáy dưới
  đỉnh trên; bậc 3: đối xứng qua điểm uốn; tiếp tuyến ⟂ bán kính tại tiếp
  điểm...). Ưu tiên đúng NHÃN và CẤU TRÚC; có thể đề xuất tỷ lệ "đẹp toán
  học" hơn ảnh gốc — KHÔNG vẽ "mò".
• HÌNH THỰC TẾ (nhà cửa, sơ đồ giao thông, ảnh chụp...): trích CHỈ thành
  phần TOÁN HỌC cần vẽ (điểm, đoạn, góc), bỏ qua chi tiết trang trí.
• KHÔNG bịa chi tiết KHÔNG có trong ảnh.

══════════════════════════════════════════════════════════════════════════
ĐỊNH DẠNG MÔ TẢ (VIẾT TIẾNG VIỆT CÓ DẤU)
══════════════════════════════════════════════════════════════════════════
⚠️ NGUYÊN TẮC TỐI THƯỢNG — TRƯỚC KHI VIẾT MÔ TẢ:
   • CHỈ MÔ TẢ NHỮNG GÌ THỰC SỰ THẤY TRONG ẢNH.
   • KHÔNG thêm chi tiết "cho hợp logic toán" mà ảnh KHÔNG có.
   • KHÔNG bịa nhãn, KHÔNG đoán điểm phụ, KHÔNG thêm đường nét trang trí.
   • Mục nào KHÔNG áp dụng cho ảnh → BỎ QUA, KHÔNG ghi "không có".

CÁC MỤC (ÁP DỤNG KHI ẢNH CÓ):
1.  PHÂN LOẠI: <kết quả [A]>.
2.  ĐỈNH/ĐIỂM: liệt kê TẤT CẢ tên + vị trí tương đối (từ [B][C]).
3.  CẠNH/ĐOẠN: đoạn nối điểm nào; THẤY (liền) hay KHUẤT (đứt) — bắt buộc cho 3D.
4.  ĐƯỜNG ĐẶC BIỆT (chỉ liệt kê đường THẬT SỰ THẤY): đường cao / trung tuyến /
    phân giác / trung trực / đường kính / tiếp tuyến / dây cung.
5.  KÝ HIỆU GÓC (chỉ ghi nếu ảnh có): vị trí ô vuông góc 90°;
    góc $\alpha, \beta$ ở đâu; số đo độ.
6.  KÝ HIỆU BẰNG NHAU (chỉ ghi nếu ảnh có vạch tick): cạnh nào có vạch đơn/kép.
7.  SỐ ĐO (chỉ ghi nếu ảnh có chữ số): độ dài, góc, tọa độ — chính xác theo ảnh.
8.  TÔ ĐẬM/PATTERN (chỉ ghi nếu ảnh có): phần nào tô, màu gì.
9.  ĐỒ THỊ (chỉ khi ảnh là đồ thị hàm số): dạng hàm, điểm đặc biệt.
10. BBT/XÉT DẤU (chỉ khi ảnh là bảng): biến, đạo hàm, chiều tăng-giảm.
11. TỶ LỆ & SCALE TIKZ GỢI Ý: dựa [E], gợi ý options hợp lý cho TikZ
    (vd: `scale=1.2, thick`; 3D thì `x={(1cm,0cm)}, y={(0.5cm,0.3cm)},
    z={(0cm,1cm)}` — chuẩn phép chiếu xiên SGK).
12. HÌNH TRANG TRÍ / COMPOUND (CHỈ KHI ẢNH THỰC SỰ CÓ — xem [F]):
    Hình học thuần → BỎ QUA mục này hoàn toàn.

NGUYÊN TẮC TRÌNH BÀY:
- Câu đủ chủ-vị, tiếng Việt có dấu.
- Nêu QUAN HỆ (vuông góc, song song, tiếp xúc, nằm trên...) — KHÔNG chỉ liệt kê.
- CHỈ trả MÔ TẢ, KHÔNG viết code TikZ.
- TỐI GIẢN: mô tả ngắn gọn, đủ ý, KHÔNG dài dòng. Mỗi mục 1-3 câu.

META: Mô tả của bạn sẽ được đưa cho 1 AI khác để vẽ TikZ. Mô tả càng đầy
đủ và chính xác → AI sau vẽ càng đúng. Thiếu thông tin → AI phải đoán → sai."""

_AI_DESCRIBE_TEXT_PROMPT = r"""Bạn là chuyên gia hình học Toán THPT. Phân tích đề bài / mô tả dưới đây và TẠO MÔ TẢ CHI TIẾT để vẽ lại bằng TikZ.

NỘI DUNG:
{content}

══════════════════════════════════════════════════════════════════════════
BƯỚC 1 — TRÍCH XUẤT RÀNG BUỘC (BẮT BUỘC, làm NGẦM, không in)
══════════════════════════════════════════════════════════════════════════
Đọc đề và LIỆT KÊ các ràng buộc dưới dạng formal:

  TÍNH CHẤT TAM GIÁC / TỨ GIÁC:
  • Vuông tại đâu? (vd: "ΔABC vuông tại A" → AB ⊥ AC)
  • Cân tại đâu? (vd: "cân tại A" → AB = AC)
  • Đều? (3 cạnh bằng)

  BẤT ĐẲNG THỨC:
  • So sánh cạnh: AB < AC, BD > CD…
  • So sánh góc: ∠B < ∠C, ∠A = 60°…

  THUỘC ĐƯỜNG / TIA / ĐOẠN:
  • Điểm THUỘC đoạn: D ∈ BC (D giữa B và C)
  • Điểm trên TIA: M ∈ tia AB (có thể trên đoạn AB hoặc kéo dài qua B)
  • Phân biệt rõ "ĐOẠN" vs "TIA" vs "ĐƯỜNG THẲNG" trong đề.

  GIAO ĐIỂM / VUÔNG GÓC / SONG SONG:
  • "đường qua D ⊥ BC" → đường thẳng vuông góc với BC tại D.
  • "cắt AB tại M" → M ∈ đường thẳng AB. Nếu đề không nói "kéo dài"
    thì M phải ∈ đoạn AB (giữa A và B).
  • "BN cắt CM tại K" → K = giao điểm 2 đường thẳng (hoặc đoạn).

══════════════════════════════════════════════════════════════════════════
BƯỚC 2 — DỰNG TỌA ĐỘ TRÊN GIẤY (BẮT BUỘC, làm NGẦM, không in)
══════════════════════════════════════════════════════════════════════════
Đặt hệ tọa độ HỢP LÝ thoả MỌI ràng buộc. Quy tắc thường dùng:

  ΔABC vuông tại A:
    A = (0, 0); AB và AC dọc theo trục.
    Nếu AB < AC: AB theo trục y (ngắn), AC theo trục x (dài).
      VD: A=(0,0), B=(0,3), C=(5,0)
    Nếu AB > AC thì ngược lại.

  ΔABC cân tại A: A=(0,h), B=(-a,0), C=(a,0). Trục đối xứng = Oy.

  ΔABC đều cạnh a: A=(0,0), B=(a,0), C=(a/2, a·√3/2).

TIẾP THEO, tính tọa độ ĐIỂM PHỤ theo CÔNG THỨC, KHÔNG ƯỚC LƯỢNG:
  • D ∈ BC với BD = k·BC: D = B + k·(C-B); ghi rõ k ∈ (0,1).
    Nếu BD>CD thì k>0.5; nếu BD<CD thì k<0.5.
  • Trung điểm M của AB: M = (A+B)/2.
  • Chân vuông góc H từ C xuống AB: H = projection of C onto AB.
  • Đường thẳng qua D ⊥ BC: pháp tuyến của BC.
  • Giao điểm 2 đường: dùng `intersection of` trong TikZ
    (HOẶC giải hệ rồi cho TikZ tọa độ chính xác).

KIỂM TRA: với tọa độ đã đặt, MỌI ràng buộc đề bài có ĐÚNG không?
  • Nếu CÓ → ghi vào mô tả.
  • Nếu KHÔNG → đặt lại tọa độ, KHÔNG xuất mô tả sai.

══════════════════════════════════════════════════════════════════════════
BƯỚC 3 — VIẾT MÔ TẢ (CÁC MỤC ÁP DỤNG)
══════════════════════════════════════════════════════════════════════════
1. PHÂN LOẠI: hình phẳng / không gian / đồ thị / BBT / biểu đồ.
2. ĐỈNH/ĐIỂM: tên và TỌA ĐỘ CHÍNH XÁC từ Bước 2 (vd: A=(0,0), B=(0,3), C=(5,0)).
3. CẠNH/ĐOẠN: đoạn thẳng nào nối những điểm nào; phân biệt thấy/khuất (3D).
4. ĐIỂM PHỤ + CÁCH DỰNG: D ∈ BC với BD/BC = 0.65 → D=B+0.65·(C-B);
   M = (đường ⊥ BC tại D) ∩ AB → dùng intersections trong TikZ.
5. GÓC: góc vuông cần đánh dấu; góc $\alpha, \beta$ ở đâu; số đo độ.
6. CẠNH BẰNG: gạch đơn/kép cho các cặp cạnh bằng nhau.
7. SỐ ĐO: độ dài, góc, tọa độ — khớp CHÍNH XÁC đề.
8. ĐỒ THỊ: dạng hàm, điểm đặc biệt (cực trị, giao trục, tiệm cận, điểm uốn).
9. BBT: chiều biến thiên, giá trị tại các mốc quan trọng.
10. MIỀN NGHIỆM: đường biên (nét liền nếu bao gồm, nét đứt nếu không), miền tô.
11. TỶ LỆ & SCALE TIKZ GỢI Ý: scale=1.2, thick (mặc định 2D).

NGUYÊN TẮC:
- Viết TIẾNG VIỆT có dấu, rõ ràng.
- TỌA ĐỘ phải LÀ SỐ CỤ THỂ (vd: D=(3.25, 1.05)) — KHÔNG ghi "D nằm gần C".
- Nêu đầy đủ QUAN HỆ (vuông góc, song song, tiếp xúc, đi qua…) theo dữ kiện đề.
- KHÔNG bịa dữ kiện không có trong đề.

CHỈ trả MÔ TẢ, KHÔNG viết code TikZ."""

# ── Autocomplete dictionary ──────────────────────────────────────────────────

_TIKZ_COMPLETIONS = [
    # Drawing commands
    (r"\draw", r"\draw[{options}] ({start}) -- ({end});"),
    (r"\draw[->]", r"\draw[->, {options}] ({start}) -- ({end});"),
    (r"\draw[dashed]", r"\draw[dashed] ({start}) -- ({end});"),
    (r"\draw[thick]", r"\draw[thick] ({start}) -- ({end});"),
    (r"\draw[very thick]", r"\draw[very thick] ({start}) -- ({end});"),
    (r"\draw[blue]", r"\draw[blue, thick] ({start}) -- ({end});"),
    (r"\fill", r"\fill[{color}] ({point}) circle ({radius}pt);"),
    (r"\filldraw", r"\filldraw[fill={color}!20, draw={color}] ({shape});"),
    (r"\node", r"\node[{position}] at ({x},{y}) {{$label$}};"),
    (r"\coordinate", r"\coordinate[label={pos}:$name$] ({name}) at ({x},{y});"),
    (r"\path", r"\path ({start}) -- ({end});"),
    # Shapes
    (r"\circle", r"\draw ({center}) circle ({radius}cm);"),
    (r"\ellipse", r"\draw ({center}) ellipse ({a}cm and {b}cm);"),
    (r"\rectangle", r"\draw ({x1},{y1}) rectangle ({x2},{y2});"),
    (r"\arc", r"\draw ({start}) arc ({start_angle}:{end_angle}:{radius}cm);"),
    (r"\grid", r"\draw[gray, very thin, step=1] ({x1},{y1}) grid ({x2},{y2});"),
    # Labels & annotations
    (r"\label", r"\node[{position}] at ({x},{y}) {{$text$}};"),
    (r"\pic", r"\pic[draw, angle radius=0.5cm, \"$angle$\"] {{angle={B}--{A}--{C}}};"),
    # TikZ environments
    (r"\begin{tikzpicture}", r"\begin{tikzpicture}[scale=1, thick]"),
    (r"\end{tikzpicture}", r"\end{tikzpicture}"),
    (r"\begin{scope}", r"\begin{scope}[{options}]"),
    (r"\end{scope}", r"\end{scope}"),
    # PGFPlots
    (r"\begin{axis}", r"\begin{axis}[\n  axis lines=center,\n  xlabel={{$x$}}, ylabel={{$y$}},\n  grid=major,\n  width=10cm, height=8cm,\n  samples=100,\n]"),
    (r"\end{axis}", r"\end{axis}"),
    (r"\addplot", r"\addplot[blue, very thick, domain={a}:{b}] {{{expression}}};"),
    (r"\addlegendentry", r"\addlegendentry{{$formula$}}"),
    # Transformations
    (r"\scale", r"[scale={factor}]"),
    (r"\rotate", r"[rotate={angle}]"),
    (r"\shift", r"[shift={{({x},{y})}}]"),
    # Styles
    (r"\tikzset", r"\tikzset{{{style_name}/.style={{{options}}}}}"),
    (r"domain=", r"domain={a}:{b}"),
    (r"samples=", r"samples=100"),
    (r"smooth", r"smooth, variable=\x"),
    # 3D
    (r"x={", r"x={{(1cm,0cm)}}"),
    (r"y={", r"y={{(0.4cm,0.3cm)}}"),
    (r"z={", r"z={{(0cm,1cm)}}"),
    # Common patterns
    (r"\foreach", r"\foreach \i in {{1,...,{n}}} {{  }}"),
    (r"\pgfmathsetmacro", r"\pgfmathsetmacro{{\name}}{{expression}}"),
    (r"\def", r"\def\name{{value}}"),
]

# Flatten to just the trigger words for matching
_COMPLETION_TRIGGERS = [(c[0], c[1]) for c in _TIKZ_COMPLETIONS]

# ── User-friendly error messages ─────────────────────────────────────────────

_ERROR_PATTERNS = [
    (r"! LaTeX Error: File `(.+?)' not found",
     lambda m: f"Thiếu package: {m.group(1)}\n-> Cài thêm package hoặc kiểm tra tên file."),
    (r"! Undefined control sequence.*?\\(\w+)",
     lambda m: f"Lệnh không tồn tại: \\{m.group(1)}\n-> Kiểm tra lại tên lệnh hoặc thiếu package."),
    (r"! Missing \$ inserted",
     lambda m: "Thiếu dấu $ cho công thức toán.\n-> Bọc nội dung toán học trong $...$"),
    (r"! Missing \} inserted",
     lambda m: "Thiếu dấu đóng ngoặc }\n-> Kiểm tra các cặp { } có đủ không."),
    (r"! Extra \}, or forgotten \$",
     lambda m: "Thừa dấu } hoặc thiếu dấu $\n-> Kiểm tra cặp ngoặc { } và $ $"),
    (r"! Package pgfplots Error",
     lambda m: "Lỗi PGFPlots — kiểm tra cú pháp \\begin{axis}...\\end{axis}"),
    (r"! Package tikz Error",
     lambda m: "Lỗi TikZ — kiểm tra cú pháp vẽ hình."),
    (r"! Illegal unit of measure \(pt inserted\)",
     lambda m: "Thiếu đơn vị đo (cm, pt, mm...)\n-> Thêm đơn vị sau số, ví dụ: 2cm thay vì 2"),
    (r"! Dimension too large",
     lambda m: "Kích thước quá lớn.\n-> Giảm scale hoặc giá trị tọa độ."),
    (r"Runaway argument",
     lambda m: "Thiếu dấu đóng ngoặc hoặc dấu kết thúc.\n-> Kiểm tra { }, [ ], \\end{...}"),
    (r"l\.(\d+)",
     lambda m: f"  (tại dòng {m.group(1)} trong code)"),
]


def _parse_pdflatex_errors(log: str) -> str:
    """Parse pdflatex log and return user-friendly error messages."""
    lines = log.splitlines()
    errors = []
    raw_errors = []
    line_numbers = []

    for i, line in enumerate(lines):
        if line.startswith("!"):
            raw_errors.append(line)
            # Try to find line number from next lines
            for j in range(i + 1, min(i + 5, len(lines))):
                lm = re.match(r"l\.(\d+)\s*(.*)", lines[j])
                if lm:
                    line_numbers.append(int(lm.group(1)))
                    break

    if not raw_errors:
        # No ! errors found, return last part of log
        return log[-1500:] if len(log) > 1500 else log

    # Build friendly messages
    full_error = "\n".join(raw_errors)
    friendly = []

    for pattern, formatter in _ERROR_PATTERNS:
        m = re.search(pattern, full_error, re.IGNORECASE)
        if m:
            friendly.append(formatter(m))

    if not friendly:
        friendly = [e.lstrip("! ") for e in raw_errors[:5]]

    result_parts = ["PHÂN TÍCH LỖI:"]
    result_parts.append("=" * 50)
    for i, msg in enumerate(friendly, 1):
        result_parts.append(f"  {i}. {msg}")

    if line_numbers:
        result_parts.append("")
        result_parts.append(f"  Vi trí lỗi: dòng {', '.join(str(n) for n in line_numbers)}")

    result_parts.append("")
    result_parts.append("LOG GỐC (pdflatex):")
    result_parts.append("-" * 50)
    for e in raw_errors[:8]:
        result_parts.append(f"  {e}")

    return "\n".join(result_parts)


class TabTikZ(ttk.Frame):
    """Tab TikZ — Vẽ hình toán học, render chất lượng cao, copy ảnh."""

    def __init__(self, parent, get_ai_call: Callable | None = None, **kw):
        super().__init__(parent)
        self._img_pil: Optional["Image.Image"] = None
        self._img_tk = None
        self._img_pdf_path: Optional[str] = None
        self._img_emf_path: Optional[str] = None
        self._dpi_var = tk.StringVar(value="300")
        self._get_ai_call = get_ai_call
        self._autocomplete_win = None
        self._last_render_log = ""
        self._ai_generated = False   # flag: code vừa được AI tạo
        # Lưu mô tả AI vẽ gần nhất → cho phép "Vẽ lại" khi 503 / không ưng ý
        # mà không phải dán ảnh + AI phân tích lại
        self._last_ai_description: str = ""
        # PDF renderer cho preview vector-quality (re-render at zoom level)
        # Nếu None → fallback resize PIL (như cũ).
        self._pdf_renderer = None  # services.pdf_renderer.PDFRenderer | None
        # Base DPI = DPI compile gốc; zoom càng lớn → re-render at higher DPI
        self._pdf_base_dpi: int = 150
        # Zoom state
        self._zoom = 1.0
        self._zoom_min = 0.1
        self._zoom_max = 10.0
        self._zoom_step = 0.1
        self._render_started_at = 0.0
        self._render_timer_active = False
        self._render_status_msg = "Đang render"
        self._build()

    def _close_pdf_renderer(self) -> None:
        """Release PyMuPDF handle. Gọi trước khi mở PDF mới hoặc destroy tab."""
        if self._pdf_renderer is not None:
            try:
                self._pdf_renderer.close()
            except Exception:
                pass
            self._pdf_renderer = None

    def destroy(self):
        # Đảm bảo PDF handle được release khi tab bị destroy
        self._close_pdf_renderer()
        super().destroy()

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        # ── Header ──
        hdr = tk.Frame(self, bg="#1F497D")
        hdr.pack(fill="x")
        tk.Label(hdr, text="  TikZ — Vẽ hình toán học chất lượng cao",
                 font=("Segoe UI", 13, "bold"), bg="#1F497D", fg="white"
                 ).pack(side="left", padx=12, pady=10)
        tk.Frame(self, bg="#10B981", height=3).pack(fill="x")

        # ── Main paned ──
        pw = ttk.PanedWindow(self, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=6, pady=6)

        # ── LEFT: editor ──
        left = tk.Frame(pw, bg=BG)
        pw.add(left, weight=1)

        # Toolbar row 1: Template + Render + DPI
        tb = tk.Frame(left, bg="#E2E8F0")
        tb.pack(fill="x")

        # ── Mẫu hình: nút mở picker dialog (dễ duyệt hơn Combobox dài) ──
        tk.Label(tb, text="Mẫu hình:", font=("Segoe UI", 9, "bold"),
                 bg="#E2E8F0").pack(side="left", padx=4, pady=4)
        self._tpl_var = tk.StringVar(value="(chưa chọn)")
        self._tpl_label = tk.Label(
            tb, textvariable=self._tpl_var,
            bg="#FFFFFF", fg="#0F2D52",
            font=("Segoe UI", 9), relief="solid", bd=1,
            anchor="w", padx=6, pady=2, width=18,
        )
        self._tpl_label.pack(side="left", padx=2, pady=4)
        tk.Button(tb, text="📚 Mẫu",
                  font=("Segoe UI", 9, "bold"),
                  bg="#0891B2", fg="white", activebackground="#0E7490",
                  relief="flat", cursor="hand2", padx=8, pady=4,
                  command=self._open_template_picker).pack(side="left", padx=2, pady=4)

        tk.Button(tb, text="▶ Render", font=("Segoe UI", 9, "bold"),
                  bg="#10B981", fg="white", activebackground="#059669",
                  relief="flat", cursor="hand2", padx=8, pady=4,
                  command=self._render).pack(side="left", padx=6, pady=4)

        tk.Label(tb, text="DPI:", font=("Segoe UI", 9), bg="#E2E8F0"
                 ).pack(side="left", padx=4)
        dpi_box = tk.Frame(tb, bg="#E2E8F0")
        dpi_box.pack(side="left", padx=2, pady=4)
        tk.Button(
            dpi_box, text="−", font=("Segoe UI", 11, "bold"),
            width=2, bg="#94A3B8", fg="white",
            activebackground="#64748B", activeforeground="white",
            relief="flat", cursor="hand2", padx=4, pady=2,
            command=lambda: self._dpi_step(-50),
        ).pack(side="left")
        self._dpi_entry = tk.Entry(
            dpi_box, textvariable=self._dpi_var, width=4,
            font=("Segoe UI", 10, "bold"), justify="center",
            relief="solid", bd=1, bg="white", fg="#1E293B",
            highlightthickness=1, highlightcolor="#3B82F6",
        )
        self._dpi_entry.pack(side="left", padx=4, ipady=2)
        self._dpi_entry.bind("<FocusOut>", self._on_dpi_focus_out)
        self._dpi_entry.bind("<Return>", self._on_dpi_focus_out)
        tk.Button(
            dpi_box, text="+", font=("Segoe UI", 11, "bold"),
            width=2, bg="#3B82F6", fg="white",
            activebackground="#2563EB", activeforeground="white",
            relief="flat", cursor="hand2", padx=4, pady=2,
            command=lambda: self._dpi_step(50),
        ).pack(side="left")
        tk.Label(
            dpi_box, text="150-600", font=("Segoe UI", 8),
            bg="#E2E8F0", fg="#64748B",
        ).pack(side="left", padx=0)

        # Toolbar row 2: Shape builder + AI features (chia 2 hàng thoáng đãng, không bị che khuất)
        tb2 = tk.Frame(left, bg="#DBEAFE")
        tb2.pack(fill="x")

        # Hàng 1: Sáng tạo & AI TikZ
        tb2_row1 = tk.Frame(tb2, bg="#DBEAFE")
        tb2_row1.pack(fill="x", padx=4, pady=(3, 1))

        tk.Button(tb2_row1, text="📐 Tạo hình", font=("Segoe UI", 9, "bold"),
                  bg="#0D9488", fg="white", activebackground="#0F766E",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._open_shape_builder).pack(side="left", padx=2)
        tk.Button(tb2_row1, text="🤖 AI vẽ", font=("Segoe UI", 9, "bold"),
                  bg="#7C3AED", fg="white", activebackground="#6D28D9",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._ai_paste_draw).pack(side="left", padx=2)
        # Nút "Vẽ lại" — dùng khi 503 hoặc kết quả không ưng ý: chỉnh mô tả + vẽ lại
        # mà không phải dán lại ảnh + AI phân tích lại (tiết kiệm 1 lần gọi vision)
        tk.Button(tb2_row1, text="🔁 Vẽ lại", font=("Segoe UI", 9, "bold"),
                  bg="#F59E0B", fg="white", activebackground="#D97706",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._ai_redraw_last).pack(side="left", padx=2)
        tk.Button(tb2_row1, text="✏️ AI sửa", font=("Segoe UI", 9, "bold"),
                  bg="#2563EB", fg="white", activebackground="#1D4ED8",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._ai_edit).pack(side="left", padx=2)
        tk.Button(tb2_row1, text="⚡ AI tối ưu", font=("Segoe UI", 9, "bold"),
                  bg="#9333EA", fg="white", activebackground="#7E22CE",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._ai_optimize).pack(side="left", padx=2)

        # Hàng 2: Kho lưu trữ & Tiện ích trình soạn thảo (hiển thị đầy đủ chữ, không bị cắt cụt)
        tb2_row2 = tk.Frame(tb2, bg="#DBEAFE")
        tb2_row2.pack(fill="x", padx=4, pady=(1, 3))

        # ── NHCH HÌNH VẼ — lưu / duyệt ──
        tk.Button(tb2_row2, text="💾 Lưu kho", font=("Segoe UI", 9, "bold"),
                  bg="#10B981", fg="white", activebackground="#059669",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._save_to_figure_bank).pack(side="left", padx=2)
        tk.Button(tb2_row2, text="📚 Kho hình", font=("Segoe UI", 9, "bold"),
                  bg="#0891B2", fg="white", activebackground="#0E7490",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._open_figure_bank).pack(side="left", padx=2)
        tk.Button(tb2_row2, text="✨ Lọc mã sạch", font=("Segoe UI", 9),
                  bg="#475569", fg="white", activebackground="#334155",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._clean_code_boilerplate).pack(side="left", padx=2)
        tk.Button(tb2_row2, text="🧹 Xóa trắng", font=("Segoe UI", 9),
                  bg="#64748B", fg="white", activebackground="#475569",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._clear_editor).pack(side="left", padx=2)

        self._ai_status = tk.Label(tb2, text="", fg="#64748B",
                                   font=("Segoe UI", 8), bg="#DBEAFE",
                                   anchor="w", justify="left")
        self._ai_status.pack(fill="x", padx=8, pady=(0, 4))
        self._ai_status.bind(
            "<Configure>",
            lambda e: self._ai_status.config(wraplength=max(240, e.width - 16)),
        )

        # Editor label
        ed_lbl = tk.Label(left, text="Mã TikZ (Ctrl+Space: gợi ý code):",
                          font=("Segoe UI", 9, "bold"), bg=BG, anchor="w")
        ed_lbl.pack(fill="x", padx=8, pady=0)

        ed_frame = tk.Frame(left, bg="#1E293B", bd=1, relief="solid")
        ed_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # Line numbers
        self._line_nums = tk.Text(ed_frame, font=("Consolas", 11),
                                  bg="#0F172A", fg="#475569", width=4,
                                  padx=4, pady=6, state="disabled",
                                  wrap="none", cursor="arrow",
                                  selectbackground="#0F172A",
                                  borderwidth=0, highlightthickness=0)
        self._line_nums.pack(side="left", fill="y")

        self._editor = tk.Text(ed_frame, font=("Consolas", 11),
                               bg="#1E293B", fg="#E2E8F0",
                               insertbackground="#10B981",
                               selectbackground="#334155",
                               wrap="none", undo=True, padx=8, pady=6)
        ed_vsb = ttk.Scrollbar(ed_frame, orient="vertical", command=self._sync_scroll_y)
        ed_hsb = ttk.Scrollbar(ed_frame, orient="horizontal", command=self._editor.xview)
        self._editor.configure(yscrollcommand=self._on_editor_scroll_y,
                               xscrollcommand=ed_hsb.set)
        ed_vsb.pack(side="right", fill="y")
        ed_hsb.pack(side="bottom", fill="x")
        self._editor.pack(fill="both", expand=True)

        def _ed_wheel(e):
            n = int(-3 * (e.delta / 120))
            self._editor.yview_scroll(n, "units")
            return "break"

        self._editor.bind("<MouseWheel>", _ed_wheel)
        self._line_nums.bind("<MouseWheel>", _ed_wheel)
        self._editor.bind("<Control-v>", self._on_paste_event)
        self._editor.bind("<Control-V>", self._on_paste_event)

        # Load default template
        self._editor.insert("1.0", _TEMPLATES["Tam giác ABC"])

        # Syntax highlighting tags
        self._editor.tag_configure("command", foreground="#22D3EE")
        self._editor.tag_configure("comment", foreground="#6B7280",
                                   font=("Consolas", 11, "italic"))
        self._editor.tag_configure("bracket", foreground="#FBBF24")
        self._editor.tag_configure("math", foreground="#A78BFA")
        self._editor.tag_configure("number", foreground="#F97316")
        self._editor.bind("<KeyRelease>", self._on_key_release)
        self._editor.bind("<Control-space>", self._trigger_autocomplete)
        self._editor.bind("<Escape>", lambda e: self._close_autocomplete())
        self._ed_vsb = ed_vsb
        self._update_line_numbers()

        # ── RIGHT: preview + actions + console ──
        right = tk.Frame(pw, bg=BG)
        pw.add(right, weight=1)

        # Action bar
        act = tk.Frame(right, bg="#E2E8F0")
        act.pack(fill="x")
        act_btns = tk.Frame(act, bg="#E2E8F0")
        act_btns.pack(fill="x")

        tk.Button(act_btns, text="📋 Copy ảnh", font=("Segoe UI", 9, "bold"),
                  bg="#3B82F6", fg="white", activebackground="#2563EB",
                  relief="flat", cursor="hand2", padx=6, pady=3,
                  command=self._copy_image).pack(side="left", padx=3, pady=4)
        tk.Button(act_btns, text="📝 Copy mã", font=("Segoe UI", 9, "bold"),
                  bg="#4F46E5", fg="white", activebackground="#4338CA",
                  relief="flat", cursor="hand2", padx=6, pady=3,
                  command=self._copy_tikz_code).pack(side="left", padx=2, pady=4)
        tk.Button(act_btns, text="💾 PNG", font=("Segoe UI", 9, "bold"),
                  bg="#8B5CF6", fg="white", activebackground="#7C3AED",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._save_png).pack(side="left", padx=2, pady=4)
        tk.Button(act_btns, text="💾 SVG", font=("Segoe UI", 9, "bold"),
                  bg="#0891B2", fg="white", activebackground="#0E7490",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._save_svg).pack(side="left", padx=2, pady=4)
        tk.Button(act_btns, text="📄 PDF", font=("Segoe UI", 9, "bold"),
                  bg="#DC2626", fg="white", activebackground="#B91C1C",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._save_pdf).pack(side="left", padx=2, pady=4)
        tk.Button(act_btns, text="🔍 Xem", font=("Segoe UI", 9, "bold"),
                  bg="#059669", fg="white", activebackground="#047857",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._view_pdf).pack(side="left", padx=2, pady=4)

        # Hàng riêng cho vector/online để không che nút khi cửa sổ hẹp.
        vector_btns = tk.Frame(act, bg="#E2E8F0")
        vector_btns.pack(fill="x")
        tk.Button(vector_btns, text="💾 EMF", font=("Segoe UI", 9, "bold"),
                  bg="#0EA5E9", fg="white", activebackground="#0284C7",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._save_emf).pack(side="left", padx=4, pady=(0, 4))
        tk.Button(vector_btns, text="📋 Copy EMF", font=("Segoe UI", 9, "bold"),
                  bg="#0891B2", fg="white", activebackground="#0E7490",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._copy_emf).pack(side="left", padx=2, pady=(0, 4))
        tk.Button(vector_btns, text="🌐 Overleaf", font=("Segoe UI", 9, "bold"),
                  bg="#16A34A", fg="white", activebackground="#15803D",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._open_overleaf).pack(side="left", padx=2, pady=(0, 4))
        tk.Button(vector_btns, text="⚙ Engine", font=("Segoe UI", 9, "bold"),
                  bg="#475569", fg="white", activebackground="#334155",
                  relief="flat", cursor="hand2", padx=7, pady=3,
                  command=self._check_latex_engine).pack(side="left", padx=2, pady=(0, 4))

        self._status_lbl = tk.Label(act, text="Chưa render", fg="#64748B",
                                     font=("Segoe UI", 8, "bold"), bg="#E2E8F0",
                                     anchor="w", justify="left")
        self._status_lbl.pack(fill="x", padx=8, pady=(0, 4))
        self._status_lbl.bind(
            "<Configure>",
            lambda e: self._status_lbl.config(wraplength=max(240, e.width - 16)),
        )

        # Right paned: preview (top) + console (bottom)
        right_pw = ttk.PanedWindow(right, orient="vertical")
        right_pw.pack(fill="both", expand=True, padx=8, pady=8)

        # Preview canvas
        prev_outer = tk.Frame(right_pw, bg=BG)
        right_pw.add(prev_outer, weight=3)

        prev_lbl = tk.Label(prev_outer, text="Xem trước:", font=("Segoe UI", 9, "bold"),
                            bg=BG, anchor="w")
        prev_lbl.pack(fill="x", pady=0)

        # Zoom control bar
        zoom_bar = tk.Frame(prev_outer, bg="#E2E8F0")
        zoom_bar.pack(fill="x", pady=4)

        tk.Label(zoom_bar, text="Phóng to/thu nhỏ:", font=("Segoe UI", 9, "bold"),
                 bg="#E2E8F0", fg="#374151").pack(side="left", padx=4)

        tk.Button(zoom_bar, text="−", font=("Segoe UI", 11, "bold"),
                  bg="#CBD5E1", fg="#1E293B", relief="flat", cursor="hand2",
                  width=2, padx=4, pady=2, command=self._zoom_out).pack(side="left", padx=2)

        self._zoom_lbl = tk.Label(zoom_bar, text="100%", font=("Segoe UI", 9, "bold"),
                                  bg="#E2E8F0", fg="#1E293B", width=6)
        self._zoom_lbl.pack(side="left", padx=2)

        tk.Button(zoom_bar, text="+", font=("Segoe UI", 11, "bold"),
                  bg="#CBD5E1", fg="#1E293B", relief="flat", cursor="hand2",
                  width=2, padx=4, pady=2, command=self._zoom_in).pack(side="left", padx=2)

        tk.Button(zoom_bar, text="↺ Chuẩn", font=("Segoe UI", 9, "bold"),
                  bg="#94A3B8", fg="white", relief="flat", cursor="hand2",
                  padx=8, pady=3, command=self._zoom_reset).pack(side="left", padx=4)

        tk.Button(zoom_bar, text="⊡ Vừa cửa sổ", font=("Segoe UI", 9, "bold"),
                  bg="#6366F1", fg="white", relief="flat", cursor="hand2",
                  padx=8, pady=3, command=self._zoom_fit).pack(side="left", padx=2)

        tk.Label(zoom_bar, text="(kéo chuột trái để di chuyển)", font=("Segoe UI", 8),
                 bg="#E2E8F0", fg="#64748B").pack(side="left", padx=4)

        prev_frame = tk.Frame(prev_outer, bg="white", bd=1, relief="solid")
        prev_frame.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(prev_frame, bg="white", highlightthickness=0,
                                  xscrollincrement=1, yscrollincrement=1)
        c_vsb = ttk.Scrollbar(prev_frame, orient="vertical", command=self._canvas.yview)
        c_hsb = ttk.Scrollbar(prev_frame, orient="horizontal", command=self._canvas.xview)
        self._preview_vsb = c_vsb
        self._canvas.configure(yscrollcommand=self._on_preview_scroll_y,
                               xscrollcommand=c_hsb.set)
        c_vsb.pack(side="right", fill="y")
        c_hsb.pack(side="bottom", fill="x")
        self._canvas.pack(fill="both", expand=True)

        # Mouse wheel zoom binding
        self._canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self._canvas.bind("<Control-MouseWheel>", self._on_ctrl_mouse_wheel)
        # Pan: kéo bằng chuột trái (và chuột giữa nếu có)
        self._canvas.bind("<Button-1>", self._on_pan_start)
        self._canvas.bind("<B1-Motion>", self._on_pan_move)
        self._canvas.bind("<ButtonRelease-1>", self._on_pan_end)
        self._canvas.bind("<Button-2>", self._on_pan_start)
        self._canvas.bind("<B2-Motion>", self._on_pan_move)
        self._canvas.bind("<ButtonRelease-2>", self._on_pan_end)
        self._canvas._pan_data = {"start_x": 0, "start_y": 0,
                                   "orig_x": 0, "orig_y": 0, "active": False}

        self._canvas.create_text(200, 150, text="Nhấn ▶ Render để xem hình",
                                  fill="#9CA3AF", font=("Segoe UI", 14))

        # Console log panel
        console_outer = tk.Frame(right_pw, bg=BG)
        right_pw.add(console_outer, weight=1)

        console_hdr = tk.Frame(console_outer, bg="#1E293B")
        console_hdr.pack(fill="x")
        tk.Label(console_hdr, text="  Console (pdflatex log)",
                 font=("Consolas", 9, "bold"), bg="#1E293B", fg="#94A3B8"
                 ).pack(side="left", padx=4, pady=2)
        tk.Button(console_hdr, text="Xóa", font=("Segoe UI", 8),
                  bg="#334155", fg="#E2E8F0", relief="flat", cursor="hand2",
                  padx=6, command=self._clear_console
                  ).pack(side="right", padx=4, pady=2)

        console_frame = tk.Frame(console_outer, bg="#0F172A", bd=1, relief="solid")
        console_frame.pack(fill="both", expand=True)

        self._console = tk.Text(console_frame, font=("Consolas", 9),
                                bg="#0F172A", fg="#94A3B8",
                                wrap="word", state="disabled",
                                padx=6, pady=4, height=6)
        c_scroll = ttk.Scrollbar(console_frame, orient="vertical",
                                 command=self._console.yview)
        self._console.configure(yscrollcommand=c_scroll.set)
        c_scroll.pack(side="right", fill="y")
        self._console.pack(fill="both", expand=True)

        # Console tags
        self._console.tag_configure("error", foreground="#EF4444",
                                    font=("Consolas", 9, "bold"))
        self._console.tag_configure("success", foreground="#10B981")
        self._console.tag_configure("info", foreground="#60A5FA")
        self._console.tag_configure("warn", foreground="#F59E0B")

    # DPI: 150–600, bước 50 (nút lớn thay cho spinbox mặc định)
    _DPI_MIN, _DPI_MAX, _DPI_STEP = 150, 600, 50

    def _dpi_snap(self, v: int) -> int:
        v = max(self._DPI_MIN, min(self._DPI_MAX, v))
        return int(round((v - self._DPI_MIN) / self._DPI_STEP) * self._DPI_STEP + self._DPI_MIN)

    def _get_dpi_int(self) -> int:
        try:
            raw = self._dpi_var.get().strip()
            cur = int(raw) if raw else 300
        except ValueError:
            cur = 300
        return self._dpi_snap(cur)

    def _dpi_step(self, delta: int) -> None:
        cur = self._get_dpi_int()
        self._dpi_var.set(str(self._dpi_snap(cur + delta)))

    def _on_dpi_focus_out(self, event=None) -> str | None:
        self._dpi_var.set(str(self._get_dpi_int()))
        if event and getattr(event, "keysym", "") == "Return":
            return "break"
        return None

    # ══════════════════════════════════════════════════════════════════════════
    #  LINE NUMBERS + SCROLL SYNC
    # ══════════════════════════════════════════════════════════════════════════

    def _update_line_numbers(self):
        self._line_nums.config(state="normal")
        self._line_nums.delete("1.0", "end")
        line_count = int(self._editor.index("end-1c").split(".")[0])
        nums = "\n".join(str(i) for i in range(1, line_count + 1))
        self._line_nums.insert("1.0", nums)
        self._line_nums.config(state="disabled")

    def _sync_scroll_y(self, *args):
        self._editor.yview(*args)
        self._line_nums.yview(*args)

    def _on_editor_scroll_y(self, first, last):
        self._ed_vsb.set(first, last)
        self._line_nums.yview_moveto(first)

    # ══════════════════════════════════════════════════════════════════════════
    #  CONSOLE LOG
    # ══════════════════════════════════════════════════════════════════════════

    def _log_console(self, text: str, tag: str = ""):
        self._console.config(state="normal")
        if tag:
            self._console.insert("end", text + "\n", tag)
        else:
            self._console.insert("end", text + "\n")
        self._console.see("end")
        self._console.config(state="disabled")

    def _clear_console(self):
        self._console.config(state="normal")
        self._console.delete("1.0", "end")
        self._console.config(state="disabled")

    # ══════════════════════════════════════════════════════════════════════════
    #  SYNTAX HIGHLIGHTING
    # ══════════════════════════════════════════════════════════════════════════

    def _highlight(self):
        text = self._editor.get("1.0", "end")
        for tag in ("command", "comment", "bracket", "math", "number"):
            self._editor.tag_remove(tag, "1.0", "end")

        for m in re.finditer(r'\\[a-zA-Z]+', text):
            s, e = m.start(), m.end()
            self._editor.tag_add("command", f"1.0+{s}c", f"1.0+{e}c")
        for m in re.finditer(r'%.*', text):
            s, e = m.start(), m.end()
            self._editor.tag_add("comment", f"1.0+{s}c", f"1.0+{e}c")
        for m in re.finditer(r'[\{\}\[\]\(\)]', text):
            s, e = m.start(), m.end()
            self._editor.tag_add("bracket", f"1.0+{s}c", f"1.0+{e}c")
        for m in re.finditer(r'\$[^$]+\$', text):
            s, e = m.start(), m.end()
            self._editor.tag_add("math", f"1.0+{s}c", f"1.0+{e}c")
        for m in re.finditer(r'(?<![a-zA-Z])-?\d+\.?\d*', text):
            s, e = m.start(), m.end()
            self._editor.tag_add("number", f"1.0+{s}c", f"1.0+{e}c")

    def _on_key_release(self, event=None):
        self._highlight()
        self._update_line_numbers()

    # ══════════════════════════════════════════════════════════════════════════
    #  AUTOCOMPLETE / CODE SUGGESTIONS
    # ══════════════════════════════════════════════════════════════════════════

    def _trigger_autocomplete(self, event=None):
        # Get current word being typed
        cursor_pos = self._editor.index("insert")
        line = self._editor.get(f"{cursor_pos} linestart", cursor_pos)
        # Find partial command: last backslash-word or word
        m = re.search(r'(\\?\w[\w.*=]*)$', line)
        if not m:
            return "break"
        prefix = m.group(1)
        self._show_autocomplete(prefix, cursor_pos, len(prefix))
        return "break"

    def _show_autocomplete(self, prefix: str, cursor_pos: str, prefix_len: int):
        self._close_autocomplete()
        prefix_lower = prefix.lower()
        matches = [(t, s) for t, s in _COMPLETION_TRIGGERS
                   if t.lower().startswith(prefix_lower)]
        if not matches:
            return

        # Create popup
        self._autocomplete_win = tk.Toplevel(self)
        self._autocomplete_win.wm_overrideredirect(True)
        self._autocomplete_win.wm_attributes("-topmost", True)

        # Position below cursor
        bbox = self._editor.bbox(cursor_pos)
        if bbox:
            x = self._editor.winfo_rootx() + bbox[0]
            y = self._editor.winfo_rooty() + bbox[1] + bbox[3] + 2
        else:
            x = self._editor.winfo_rootx() + 50
            y = self._editor.winfo_rooty() + 50

        self._autocomplete_win.geometry(f"+{x}+{y}")

        lb = tk.Listbox(self._autocomplete_win, font=("Consolas", 10),
                        bg="#1E293B", fg="#E2E8F0",
                        selectbackground="#334155", selectforeground="#22D3EE",
                        activestyle="none", bd=1, relief="solid",
                        highlightthickness=0, width=50,
                        height=min(len(matches), 8))
        lb.pack()

        for trigger, snippet in matches:
            lb.insert("end", trigger)

        self._ac_matches = matches
        self._ac_prefix_len = prefix_len
        lb.select_set(0)

        lb.bind("<Return>", lambda e: self._accept_autocomplete(lb))
        lb.bind("<Double-1>", lambda e: self._accept_autocomplete(lb))
        lb.bind("<Escape>", lambda e: self._close_autocomplete())
        lb.bind("<Tab>", lambda e: self._accept_autocomplete(lb))
        lb.focus_set()

    def _accept_autocomplete(self, listbox):
        sel = listbox.curselection()
        if not sel:
            self._close_autocomplete()
            return
        idx = sel[0]
        trigger, snippet = self._ac_matches[idx]

        # Delete the prefix and insert the snippet
        cursor = self._editor.index("insert")
        start = f"{cursor}-{self._ac_prefix_len}c"
        self._editor.delete(start, cursor)
        # Clean snippet for insertion (remove placeholder markers)
        clean = snippet.replace(r"\n", "\n")
        self._editor.insert(start, clean)
        self._close_autocomplete()
        self._highlight()
        self._editor.focus_set()

    def _close_autocomplete(self):
        if self._autocomplete_win:
            self._autocomplete_win.destroy()
            self._autocomplete_win = None

    # ══════════════════════════════════════════════════════════════════════════
    #  TEMPLATE
    # ══════════════════════════════════════════════════════════════════════════

    def _on_template(self, event=None):
        name = self._tpl_var.get()
        code = _TEMPLATES.get(name, "")
        self._editor.delete("1.0", "end")
        self._editor.insert("1.0", code)
        self._highlight()
        self._update_line_numbers()

    def _open_template_picker(self):
        """Mở dialog chọn mẫu hình — duyệt theo nhóm/chủ đề + preview code.

        UX hơn Combobox dài (88+ entries chen chật) — dùng Treeview phân nhóm
        theo folder KB (Plane / Solid / Graphs / Tables / Charts / Misc).
        """
        dlg = _TemplatePickerDialog(self.winfo_toplevel())
        self.wait_window(dlg)
        if dlg.selected_name:
            self._tpl_var.set(dlg.selected_name)
            code = _TEMPLATES.get(dlg.selected_name, "")
            self._editor.delete("1.0", "end")
            self._editor.insert("1.0", code)
            self._highlight()
            self._update_line_numbers()
            self._log_console(
                f"[Mẫu] Đã chèn '{dlg.selected_name}' vào editor", "success",
            )

    # ══════════════════════════════════════════════════════════════════════════
    #  SHAPE BUILDER — Tạo hình trực quan
    # ══════════════════════════════════════════════════════════════════════════

    def _open_shape_builder(self):
        from ui.tikz_shape_builder import ShapeBuilderDialog
        dlg = ShapeBuilderDialog(self.winfo_toplevel())
        self.wait_window(dlg)
        if dlg.result:
            self._editor.delete("1.0", "end")
            self._editor.insert("1.0", dlg.result)
            self._highlight()
            self._update_line_numbers()
            self._log_console("[Tạo hình] Đã chèn code TikZ từ công cụ tạo hình", "success")

    # ══════════════════════════════════════════════════════════════════════════
    #  NHCH HÌNH VẼ (figure_bank)
    # ══════════════════════════════════════════════════════════════════════════

    def _save_to_figure_bank(self):
        """Lưu code TikZ hiện tại + (tuỳ chọn) ảnh PNG đã render vào kho sau khi xác nhận."""
        code = self._editor.get("1.0", "end-1c").strip()
        if not code:
            messagebox.showwarning(
                "Trống", "Hãy nhập code TikZ trước khi lưu vào kho.",
                parent=self,
            )
            return

        # Tận dụng ảnh render hiện tại hoặc từ cache
        img_to_save = self._img_pil
        if img_to_save is None:
            try:
                from services import tikz_cache
                cached = tikz_cache.get(code)
                if cached and os.path.isfile(cached):
                    from PIL import Image as PILImage
                    with PILImage.open(cached) as im:
                        img_to_save = im.copy()
            except Exception:
                pass

        from services import figure_bank
        dlg = _SaveFigureDialog(
            self.winfo_toplevel(),
            has_rendered_image=img_to_save is not None,
        )
        self.wait_window(dlg)
        if not dlg.confirmed:
            return

        try:
            fid = figure_bank.save(
                tikz_code=code,
                title=dlg.result_title,
                description=dlg.result_desc,
                tags=dlg.result_tags,
                source="ai" if self._ai_generated else "manual",
                png_pil=img_to_save if dlg.save_png else None,
            )
            self._log_console(
                f"[Kho hình] Đã lưu figure_{fid}.tex"
                + (" + .png" if dlg.save_png and img_to_save else "")
                + f" — '{dlg.result_title}'",
                "success",
            )
            messagebox.showinfo(
                "Đã lưu",
                f"Đã lưu hình vào kho:\n  ID: {fid}\n  Tên: {dlg.result_title}",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror("Lỗi lưu kho", str(e), parent=self)

    def _open_figure_bank(self):
        """Mở dialog duyệt NHCH hình vẽ — nạp code VÀ mở ngay ảnh render sẵn vào preview."""
        dlg = _FigureBankDialog(self.winfo_toplevel())
        self.wait_window(dlg)
        if dlg.loaded_tikz:
            self._editor.delete("1.0", "end")
            self._editor.insert("1.0", dlg.loaded_tikz)
            self._highlight()
            self._update_line_numbers()

            # Mở luôn ảnh đã render sẵn nếu có (từ kho hoặc cache)
            loaded_img = None
            png_path = getattr(dlg, "loaded_png_path", "")
            if png_path and os.path.isfile(png_path):
                try:
                    from PIL import Image as PILImage
                    with PILImage.open(png_path) as im:
                        loaded_img = im.copy()
                except Exception as exc:
                    self._log_console(
                        f"[Kho hình] Không đọc được ảnh render sẵn: {exc}", "warn"
                    )

            if loaded_img:
                self._img_pil = loaded_img
                self._img_pdf_path = None
                self._img_emf_path = None
                self._show_image(self._img_pil)
                self._status_lbl.config(
                    text=f"✅ Đã nạp & mở ảnh render sẵn ({loaded_img.width}×{loaded_img.height}px) — '{dlg.loaded_title}'",
                    fg="#059669",
                )
                self._log_console(
                    f"[Kho hình] Đã nạp '{dlg.loaded_title}' và hiển thị ngay ảnh render sẵn ({loaded_img.width}×{loaded_img.height}px)!",
                    "success",
                )
            else:
                self._status_lbl.config(
                    text=f"ℹ️ Đã nạp code '{dlg.loaded_title}' (chưa có ảnh sẵn — bấm '▶ Render' để vẽ)",
                    fg="#2563EB",
                )
                self._log_console(
                    f"[Kho hình] Đã nạp '{dlg.loaded_title}' vào editor (chưa có ảnh sẵn)", "info",
                )

    # ══════════════════════════════════════════════════════════════════════════
    #  AI DRAW — Generate TikZ from description
    # ══════════════════════════════════════════════════════════════════════════

    def _ai_paste_draw(self, prefill_image=None):
        """Mở dialog dán nội dung/ảnh → AI phân tích & tự động vẽ TikZ (chuẩn WebTikZ)."""
        if not self._get_ai_call:
            messagebox.showwarning("Chưa cấu hình AI",
                                   "Cần nhập API Key ở tab Cài đặt.")
            return
        try:
            ai_call = self._get_ai_call()
        except Exception as e:
            messagebox.showerror("Lỗi AI", str(e))
            return

        dlg = _AIPasteDrawDialog(self, ai_call=ai_call, prefill_image=prefill_image)
        self.wait_window(dlg)
        if getattr(dlg, "result_code", None):
            # One-shot direct draw từ ảnh chuẩn WebTikZ
            code = dlg.result_code.strip()
            self._editor.delete("1.0", "end")
            self._editor.insert("1.0", code)
            self._highlight()
            self._update_line_numbers()
            if getattr(dlg, "result_description", None):
                self._last_ai_description = dlg.result_description
            p_text = f" ({dlg.used_provider})" if getattr(dlg, "used_provider", "") else ""
            self._ai_status.config(text=f"✅ AI đã vẽ hình xong{p_text}!", fg="#059669")
            self._log_console(f"[AI TikZ] Đã hoàn thành vẽ hình tự động từ ảnh{p_text}!", "success")
            # Tự động render xem trước ngay lập tức!
            self.after(100, self._render)
        elif getattr(dlg, "result_description", None):
            # Lưu mô tả → cho phép "Vẽ lại" sau này
            self._last_ai_description = dlg.result_description
            self._draw_from_description(dlg.result_description)

    def _draw_from_description(self, description: str):
        """Tách helper để dùng chung cho `_ai_paste_draw` và `_ai_redraw_last`."""
        # Inject 1-2 KB examples liên quan với mô tả → giúp AI có context cụ thể
        try:
            from services import tikz_kb
            kb_block = tikz_kb.build_few_shot_block(
                description, k=2, max_chars=2500,
            )
        except Exception:
            kb_block = ""

        try:
            from services import tikz_ai_skill
            prompt = tikz_ai_skill.get_tikz_draw_prompt(
                description=description,
                kb_examples=kb_block,
            )
        except Exception:
            prompt = _AI_DRAW_PROMPT.format(
                description=description,
                kb_examples=kb_block,
            )

        self._run_ai_task(
            prompt=prompt,
            status_text="AI đang vẽ hình từ mô tả (chuẩn Thầy Đỗ Minh)...",
            done_text="AI đã tạo code TikZ từ hình mẫu",
        )

    def _ai_redraw_last(self):
        """Vẽ lại từ mô tả gần nhất — dùng khi 503 hoặc kết quả không ưng ý.
        Không cần dán lại ảnh + AI phân tích lại.
        """
        if not self._last_ai_description:
            messagebox.showinfo(
                "Chưa có mô tả",
                "Bạn chưa dùng 'Vẽ hình bằng AI' lần nào trong phiên này.\n"
                "Hãy nhấn '🤖 AI vẽ' để bắt đầu.",
                parent=self,
            )
            return
        if not self._get_ai_call:
            messagebox.showwarning("Chưa cấu hình AI",
                                    "Cần nhập API Key ở tab Cài đặt.")
            return
        # Hỏi xác nhận + cho user chỉnh mô tả nếu cần
        dlg = _AIInputDialog(
            self,
            "Vẽ lại từ mô tả gần nhất",
            "Mô tả sẽ dùng để vẽ lại (có thể chỉnh trước khi vẽ):",
            default=self._last_ai_description,
            multiline=True,
        )
        self.wait_window(dlg)
        if not dlg.result:
            return
        self._last_ai_description = dlg.result
        self._draw_from_description(dlg.result)

    def _ai_edit(self):
        current = self._editor.get("1.0", "end-1c").strip()
        if not current:
            messagebox.showwarning("Trống", "Hãy nhập hoặc tạo code TikZ trước.")
            return
        dlg = _AIInputDialog(self, "AI chỉnh sửa",
                             "Yêu cầu chỉnh sửa (ví dụ: thêm đường cao AH, "
                             "đổi màu đồ thị sang đỏ, thêm nhãn cho các cạnh...):")
        self.wait_window(dlg)
        if not dlg.result:
            return
        try:
            from services import tikz_ai_skill
            prompt = tikz_ai_skill.get_tikz_edit_prompt(
                current_code=current,
                edit_request=dlg.result,
            )
        except Exception:
            prompt = _AI_EDIT_PROMPT.format(current_code=current, edit_request=dlg.result)

        self._run_ai_task(
            prompt=prompt,
            status_text="AI đang chỉnh sửa code TikZ (chuẩn Thầy Đỗ Minh)...",
            done_text="AI đã chỉnh sửa code",
        )

    def _ai_optimize(self):
        """Tối ưu hóa mã TikZ hiện tại theo 5 lớp cấu trúc và 10 invariants (Skill Thầy Đỗ Minh)."""
        current = self._editor.get("1.0", "end-1c").strip()
        if not current:
            messagebox.showwarning("Trống", "Hãy nhập hoặc tạo code TikZ trước để tối ưu hóa.")
            return
        try:
            from services import tikz_ai_skill
            prompt = tikz_ai_skill.get_tikz_optimization_prompt(current)
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không thể tạo prompt tối ưu: {exc}")
            return
        self._run_ai_task(
            prompt=prompt,
            status_text="AI đang tối ưu hóa mã TikZ 5 lớp (chuẩn Thầy Đỗ Minh)...",
            done_text="AI đã tối ưu hóa mã TikZ",
        )

    def _run_ai_task(self, prompt: str, status_text: str, done_text: str):
        if not self._get_ai_call:
            messagebox.showwarning("Chưa cấu hình AI",
                                   "Cần nhập API Key ở tab Cài đặt.")
            return
        try:
            ai_call = self._get_ai_call()
        except Exception as e:
            messagebox.showerror("Lỗi AI", str(e))
            return

        # ── BẮT ĐẦU TIMER — biết AI có đang chạy không ──
        import time as _time
        self._ai_started_at = _time.monotonic()
        self._ai_timer_active = True
        self._ai_status_msg = status_text
        self._ai_done_text = done_text
        self._render_ai_progress()
        self._tick_ai_timer()
        self._log_console(f"[AI] {status_text} (bắt đầu)", "info")

        def _worker():
            # Retry 503/UNAVAILABLE/overloaded: 2s → 5s → 10s
            SERVER_ERROR_KW = ("503", "500", "529", "unavailable",
                                "overloaded", "internal", "high demand")
            BACKOFF_DELAYS = (2, 5, 10)
            last_err: Exception | None = None
            for attempt, delay in enumerate(BACKOFF_DELAYS):
                try:
                    raw = ai_call(prompt)
                    code = self._extract_tikz_code(raw)
                    self.after(0, lambda c=code, d=done_text: self._on_ai_done(c, d))
                    return
                except Exception as e:
                    last_err = e
                    msg = str(e).lower()
                    # Server error → backoff retry
                    if any(kw in msg for kw in SERVER_ERROR_KW):
                        if attempt < len(BACKOFF_DELAYS) - 1:
                            self.after(0, lambda d=delay, a=attempt: (
                                self._log_console(
                                    f"[AI] Server quá tải (503), đợi {d}s rồi thử lại "
                                    f"(lần {a+2}/{len(BACKOFF_DELAYS)})...",
                                    "warn",
                                ) if hasattr(self, "_log_console") else None
                            ))
                            import time as _t
                            _t.sleep(delay)
                            continue
                    # Lỗi khác hoặc hết retry
                    break
            # Format thông báo lỗi thân thiện
            err_str = str(last_err) if last_err else "Unknown"
            err_lower = err_str.lower()
            if any(kw in err_lower for kw in SERVER_ERROR_KW):
                err_msg = (
                    "Máy chủ AI đang quá tải (503/UNAVAILABLE).\n"
                    f"Đã thử lại {len(BACKOFF_DELAYS)} lần nhưng vẫn lỗi.\n\n"
                    "💡 GIẢI PHÁP:\n"
                    "  • Đợi 1-2 phút rồi nhấn lại nút 'Vẽ hình bằng AI'.\n"
                    "  • Hoặc đổi sang model khác trong tab Cài đặt.\n"
                    "  • Hoặc đổi sang nhà cung cấp khác (Gemini ↔ Claude)."
                )
            else:
                err_msg = err_str
            self.after(0, lambda m=err_msg: self._on_ai_error(m))

        threading.Thread(target=_worker, daemon=True).start()

    # ── AI Progress Timer ──────────────────────────────────────────────────
    def _tick_ai_timer(self):
        """Re-schedule mỗi 1s để cập nhật đồng hồ trên status label."""
        if not getattr(self, "_ai_timer_active", False):
            return
        try:
            self._render_ai_progress()
        except Exception:
            return
        self.after(1000, self._tick_ai_timer)

    def _render_ai_progress(self):
        """Hiển thị '⏳ msg ⏱ Mm Ss' trên ai_status label."""
        import time as _time
        if not hasattr(self, "_ai_started_at"):
            return
        elapsed = int(_time.monotonic() - self._ai_started_at)
        mins, secs = divmod(elapsed, 60)
        tstr = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"
        msg = getattr(self, "_ai_status_msg", "Đang xử lý")
        self._ai_status.config(text=f"⏳ {msg}   ⏱ {tstr}", fg="#7C3AED")

    def _stop_ai_timer(self) -> str:
        """Dừng timer, trả chuỗi thời gian đã chạy (để hiển thị)."""
        import time as _time
        self._ai_timer_active = False
        if not hasattr(self, "_ai_started_at"):
            return "0s"
        elapsed = int(_time.monotonic() - self._ai_started_at)
        mins, secs = divmod(elapsed, 60)
        return f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

    def _start_render_timer(self, msg: str = "Đang render") -> None:
        """Start visible render timer on the render status row."""
        self._render_started_at = time.monotonic()
        self._render_timer_active = True
        self._render_status_msg = msg
        self._render_render_progress()
        self._tick_render_timer()

    def _tick_render_timer(self) -> None:
        if not getattr(self, "_render_timer_active", False):
            return
        self._render_render_progress()
        self.after(1000, self._tick_render_timer)

    def _render_render_progress(self) -> None:
        if not getattr(self, "_render_started_at", 0.0):
            return
        elapsed = int(time.monotonic() - self._render_started_at)
        mins, secs = divmod(elapsed, 60)
        tstr = f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"
        msg = getattr(self, "_render_status_msg", "Đang render")
        self._status_lbl.config(text=f"⏳ {msg}   ⏱ {tstr}", fg="#D97706")

    def _stop_render_timer(self) -> str:
        self._render_timer_active = False
        if not getattr(self, "_render_started_at", 0.0):
            return "0s"
        elapsed = int(time.monotonic() - self._render_started_at)
        mins, secs = divmod(elapsed, 60)
        return f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s"

    def _on_render_done_status(self, img, dpi: int) -> None:
        elapsed = self._stop_render_timer()
        self._status_lbl.config(
            text=f"✅ Render OK — {img.width}×{img.height}px — {dpi} DPI — ⏱ {elapsed}",
            fg="#059669",
        )

    def _extract_tikz_code(self, raw: str) -> str:
        """Extract TikZ code from AI response using services.tikz_ai_skill."""
        try:
            from services import tikz_ai_skill
            code = tikz_ai_skill.extract_tikz_code(raw)
            if code:
                return code
        except Exception:
            pass

        # Fallback
        m = re.search(r"```(?:latex|tex)?\s*([\s\S]*?)```", raw)
        if m:
            raw = m.group(1).strip()

        m = re.search(r"(\\begin\{tikzpicture\}[\s\S]*?\\end\{tikzpicture\})", raw)
        if m:
            return m.group(1).strip()

        m = re.search(r"(\\begin\{axis\}[\s\S]*?\\end\{axis\})", raw)
        if m:
            return "\\begin{tikzpicture}\n" + m.group(1).strip() + "\n\\end{tikzpicture}"

        return raw.strip()

    def _on_ai_done(self, code: str, done_text: str):
        elapsed = self._stop_ai_timer()
        self._editor.delete("1.0", "end")
        self._editor.insert("1.0", code)
        self._highlight()
        self._update_line_numbers()
        self._ai_status.config(text=f"✅ {done_text}  (⏱ {elapsed})", fg="#059669")
        self._log_console(
            f"[AI] {done_text} — {len(code)} ký tự — chạy {elapsed}", "success",
        )
        # Tự động render sau khi AI tạo code
        self._ai_generated = True
        self._log_console("[Auto] Tự động render hình...", "info")
        self.after(300, self._render)

    def _on_ai_error(self, err: str):
        elapsed = self._stop_ai_timer()
        self._ai_status.config(text=f"❌ Lỗi AI  (sau {elapsed})", fg="#DC2626")
        self._log_console(f"[AI] Lỗi (sau {elapsed}): {err}", "error")
        messagebox.showerror("Lỗi AI", f"(sau {elapsed})\n\n{err[:500]}")

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDER — pdflatex → PDF → high-res PNG via PyMuPDF
    # ══════════════════════════════════════════════════════════════════════════

    def _render(self, _event=None):
        tikz_code = self._editor.get("1.0", "end-1c").strip()
        if not tikz_code:
            if not self._ai_generated:
                messagebox.showwarning("Trống", "Hãy nhập mã TikZ trước.")
            return

        # ── PRE-FLIGHT SYNTAX CHECK (nhanh — vài ms, tiết kiệm 10-30s nếu lỗi) ──
        try:
            from services import tikz_preflight as _pf
            issues = _pf.check(tikz_code)
            errors = [i for i in issues if i.severity == _pf.Severity.ERROR]
            warnings = [i for i in issues if i.severity == _pf.Severity.WARNING]

            # Auto-fix bất kỳ issue nào fixable=True (vd: \documentclass)
            if any(i.fixable for i in issues):
                fixed = _pf.auto_fix(tikz_code)
                if fixed != tikz_code:
                    self._editor.delete("1.0", "end")
                    self._editor.insert("1.0", fixed)
                    self._highlight()
                    self._update_line_numbers()
                    tikz_code = fixed
                    self._log_console(
                        "[Pre-flight] Đã auto-fix một số vấn đề nhỏ trước khi render",
                        "info",
                    )
                    # Re-check sau khi fix
                    issues = _pf.check(tikz_code)
                    errors = [i for i in issues if i.severity == _pf.Severity.ERROR]
                    warnings = [i for i in issues if i.severity == _pf.Severity.WARNING]

            if errors:
                # Có lỗi nghiêm trọng → KHÔNG gọi pdflatex (tiết kiệm thời gian)
                msg = _pf.format_issues(errors)
                self._log_console(
                    "[Pre-flight] " + msg, "error",
                )
                self._status_lbl.config(
                    text=f"❌ Pre-flight: {len(errors)} lỗi syntax",
                    fg="#DC2626",
                )
                # Nếu code do AI tạo → trigger auto-heal
                if self._ai_generated and self._get_ai_call:
                    self._ai_generated = False
                    self._auto_heal_ai_code(tikz_code, msg, round_num=1)
                else:
                    messagebox.showerror(
                        "Lỗi cú pháp TikZ", msg, parent=self,
                    )
                return
            if warnings:
                self._log_console(
                    f"[Pre-flight] {len(warnings)} cảnh báo (vẫn render):", "warn",
                )
                for w in warnings[:3]:
                    self._log_console(f"  ⚠ L{w.line}: {w.message}", "warn")
        except Exception as e:
            # Pre-flight không được phép cản trở render — chỉ log
            self._log_console(f"[Pre-flight] Skip (lỗi nội bộ): {e}", "warn")

        # Hiển thị engine đang dùng (auto-detected hoặc forced bởi config)
        render_msg = "Đang render"
        try:
            from services import latex_engine
            engine = latex_engine.get_engine()
            render_msg = f"Đang render bằng {engine.name}"
            self._log_console(
                f"[Render] Bắt đầu compile bằng {engine.name}...", "info")
        except Exception:
            self._log_console("[Render] Bắt đầu compile...", "info")
        self._start_render_timer(render_msg)

        threading.Thread(target=self._do_render, args=(tikz_code,), daemon=True).start()

    def _do_render(self, tikz_code: str):
        try:
            dpi = self._get_dpi_int()
            img, log, pdf_path = render_tikz_to_image(tikz_code, dpi=dpi, return_log=True)
            self._img_pil = img
            self._img_pdf_path = pdf_path
            self._img_emf_path = None
            self._last_render_log = log
            # Không tự động lưu vào kho hình khi render nháp để tránh rác.
            # Chỉ lưu khi người dùng chủ động bấm '💾 Lưu kho' và xác nhận.
            self.after(0, lambda: self._show_image(img))
            self.after(0, lambda img=img, dpi=dpi: self._on_render_done_status(img, dpi))
            self.after(0, lambda: self._log_console(
                f"[Render] Thành công: {img.width}×{img.height}px, {dpi} DPI", "success"))
            # Show warnings from log — bỏ qua Overfull/Underfull vì với
            # standalone+preview đó là "false positive": LaTeX cảnh báo line-box
            # rộng hơn paperwidth mặc định nhưng `\PreviewEnvironment` đã cắt
            # đúng kích thước hình → không ảnh hưởng output PDF/PNG.
            if log:
                _ignore_kw = ("overfull", "underfull")
                warnings = [
                    l for l in log.splitlines()
                    if "warning" in l.lower()
                    and not any(kw in l.lower() for kw in _ignore_kw)
                ]
                if warnings:
                    self.after(0, lambda: self._log_console(
                        "[Cảnh báo] " + "; ".join(warnings[:3]), "warn"))
        except Exception as e:
            # Format error CHI TIẾT — kèm traceback ngắn để dev/user biết
            # chính xác file:line gây lỗi (NameError/import/v.v.). Trước đây
            # chỉ str(e) → mất bản chất khi gặp NameError như "shutil is not
            # defined" (không biết shutil bị reference ở đâu).
            import traceback
            tb = traceback.format_exc()
            # Lấy 4 dòng cuối traceback (frame gây lỗi + tên exception)
            tb_lines = [l for l in tb.splitlines() if l.strip()]
            tb_brief = "\n".join(tb_lines[-4:]) if tb_lines else str(e)
            err_msg = f"{type(e).__name__}: {e}\n\nTraceback (đoạn cuối):\n{tb_brief}"
            # Log full traceback to file qua services.logger nếu có
            try:
                from services import logger as _svc_log
                _svc_log.get_log().error(
                    model="tikz_render", error=tb[-500:])
            except Exception:
                pass
            self.after(0, lambda m=err_msg: self._show_render_error(m))

    # ── Auto-heal multi-round ─────────────────────────────────────────────
    _MAX_AUTO_HEAL_ROUNDS = 3

    def _auto_heal_ai_code(self, current_code: str, error_msg: str,
                           round_num: int = 1):
        """Multi-round auto-heal: AI fix → render → nếu vẫn lỗi → fix tiếp.
        Tối đa 3 vòng. Tránh vòng lặp vô tận bằng `_ai_generated=False`."""
        if round_num > self._MAX_AUTO_HEAL_ROUNDS:
            self._log_console(
                f"[Auto-heal] Đã thử {self._MAX_AUTO_HEAL_ROUNDS} lần, "
                f"AI vẫn không fix được. Vui lòng sửa thủ công.",
                "error",
            )
            messagebox.showerror(
                "Auto-heal thất bại",
                f"AI đã thử sửa {self._MAX_AUTO_HEAL_ROUNDS} lần nhưng "
                f"vẫn không render được.\n\n"
                f"Lỗi cuối:\n{error_msg[:300]}\n\n"
                "Hãy sửa code thủ công, hoặc xóa và yêu cầu AI vẽ lại.",
                parent=self,
            )
            return

        self._log_console(
            f"[Auto-heal] Vòng {round_num}/{self._MAX_AUTO_HEAL_ROUNDS} — "
            f"đang nhờ AI sửa lỗi...",
            "info",
        )

        fix_prompt = (
            f"Code TikZ sau bị lỗi khi compile bằng pdflatex (lần thử {round_num}):\n"
            f"```\n{current_code}\n```\n\n"
            f"LỖI:\n{error_msg[:1500]}\n\n"
            f"Hãy sửa lỗi và trả về TOÀN BỘ code TikZ đã sửa.\n"
            f"YÊU CẦU:\n"
            f"  1. KHÔNG kèm \\documentclass, \\usepackage, \\begin{{document}}.\n"
            f"  2. KHÔNG dùng marker `===tikz===` hay fence ```tikz.\n"
            f"  3. Code phải compile được — kiểm tra:\n"
            f"     • Cân bằng {{ }} và \\begin/\\end\n"
            f"     • \\addplot trong \\begin{{axis}}\n"
            f"     • Phép nhân tường minh: 2*x (KHÔNG 2x)\n"
            f"     • Lượng giác: sin(deg(x)) (KHÔNG sin(x))\n"
            f"     • Parametric: variable=\\t, dùng \\t (KHÔNG dùng y)\n"
            f"  4. Packages có sẵn: amsmath, amssymb, tikz, pgfplots (compat=1.18),\n"
            f"     tkz-tab. Libraries: calc, angles, quotes, patterns, arrows.meta,\n"
            f"     decorations.markings, intersections, 3d.\n\n"
            f"CHỈ trả code TikZ — bắt đầu \\begin{{tikzpicture}}, kết thúc "
            f"\\end{{tikzpicture}}. KHÔNG giải thích."
        )

        # Đặt flag để callback _on_ai_done biết phải retry render
        self._auto_heal_round = round_num
        self._auto_heal_active = True

        self._run_ai_task(
            prompt=fix_prompt,
            status_text=f"AI đang sửa lỗi (vòng {round_num}/{self._MAX_AUTO_HEAL_ROUNDS})...",
            done_text=f"AI đã sửa code (vòng {round_num})",
        )

    def _show_render_error(self, msg: str):
        elapsed = self._stop_render_timer()
        self._status_lbl.config(text=f"❌ Lỗi render — sau {elapsed}", fg="#DC2626")
        # Parse and show friendly errors in console
        friendly = _parse_pdflatex_errors(msg)
        self._log_console(friendly, "error")

        missing_engine = (
            "Không tìm thấy LaTeX engine" in msg
            or "TeX Live" in msg
            or "MiKTeX" in msg
            or "Tectonic" in msg
        )
        if missing_engine:
            answer = messagebox.askyesno(
                "Thiếu LaTeX engine",
                "Máy chưa có TeX Live/MiKTeX/tectonic nên không render local được.\n\n"
                "Bạn có muốn mở code TikZ hiện tại trên Overleaf để xem hình online không?\n"
                "Source .tex cũng sẽ được copy vào clipboard để dán thủ công nếu cần.",
                parent=self,
            )
            if answer:
                self._open_overleaf()
            return

        # Nếu đang trong vòng auto-heal → tiếp tục vòng tiếp
        if getattr(self, "_auto_heal_active", False):
            current_code = self._editor.get("1.0", "end-1c").strip()
            next_round = getattr(self, "_auto_heal_round", 0) + 1
            self._auto_heal_active = False  # sẽ được bật lại nếu < MAX
            self._auto_heal_ai_code(current_code, msg, round_num=next_round)
            return

        # Nếu code do AI tạo → hỏi user có muốn auto-heal không
        if self._ai_generated and self._get_ai_call:
            self._ai_generated = False
            answer = messagebox.askyesno(
                "AI Fix",
                "Code TikZ do AI tạo bị lỗi khi render.\n\n"
                f"{friendly[:300]}\n\n"
                f"Bạn có muốn AI tự động sửa lỗi không?\n"
                f"(AI sẽ thử tối đa {self._MAX_AUTO_HEAL_ROUNDS} lần — auto-render giữa mỗi lần)",
                parent=self,
            )
            if answer:
                current_code = self._editor.get("1.0", "end-1c").strip()
                self._auto_heal_ai_code(current_code, msg, round_num=1)

    def _show_image(self, img):
        """Hiển thị ảnh vừa render. Đồng thời mở PDFRenderer (nếu có pdf_path)
        để zoom vector-quality từ lần thứ 2 trở đi.
        """
        from PIL import Image as PILImage, ImageTk
        cw = self._canvas.winfo_width() or 500
        ch = self._canvas.winfo_height() or 400
        scale = min(cw / img.width, ch / img.height, 1.0)
        if scale < 1.0:
            display = img.resize((int(img.width * scale), int(img.height * scale)),
                                  resample=PILImage.LANCZOS)
        else:
            display = img

        self._img_tk = ImageTk.PhotoImage(display)
        self._canvas.delete("all")
        self._canvas.create_image(cw // 2, ch // 2, image=self._img_tk, anchor="center")
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._zoom = 1.0
        self._update_zoom_label()

        # Mở PDF renderer cho zoom vector-quality
        self._close_pdf_renderer()
        if self._img_pdf_path and os.path.exists(self._img_pdf_path):
            try:
                from services.pdf_renderer import PDFRenderer
                self._pdf_renderer = PDFRenderer(self._img_pdf_path)
                # Lưu base DPI = DPI hiển thị ban đầu (cho fit) → zoom theo bội
                self._pdf_base_dpi = max(72, int(72 * scale * self._get_dpi_int() / 72))
            except Exception as e:
                # PDF render fail (vd: pymupdf thiếu) → fallback raster zoom
                self._pdf_renderer = None
                if hasattr(self, "_log_console"):
                    self._log_console(
                        f"[PDF] Không mở được PDF cho zoom vector: {e}", "warn")

    def _on_preview_scroll_y(self, first, last):
        """Canvas gọi khi vùng nhìn đổi — cập nhật thumb thanh cuộn dọc."""
        self._preview_vsb.set(first, last)

    # ══════════════════════════════════════════════════════════════════════════
    #  ZOOM CONTROLS
    # ══════════════════════════════════════════════════════════════════════════

    def _update_zoom_label(self):
        self._zoom_lbl.config(text=f"{int(self._zoom * 100)}%")

    def _zoom_in(self):
        if not self._img_pil or not self._img_tk:
            return
        self._set_zoom(min(self._zoom + self._zoom_step * 2, self._zoom_max))

    def _zoom_out(self):
        if not self._img_pil or not self._img_tk:
            return
        self._set_zoom(max(self._zoom - self._zoom_step * 2, self._zoom_min))

    def _zoom_reset(self):
        if not self._img_pil:
            return
        self._set_zoom(1.0)

    def _zoom_fit(self):
        if not self._img_pil:
            return
        cw = self._canvas.winfo_width() or 500
        ch = self._canvas.winfo_height() or 400
        fit_scale = min(cw / self._img_pil.width, ch / self._img_pil.height)
        self._set_zoom(fit_scale)

    def _set_zoom(self, zoom: float):
        """Apply zoom level. Ưu tiên PDF re-render (vector) nếu có; fallback
        raster resize PIL nếu không có PDF (vd: render fail, chỉ còn ảnh)."""
        if not self._img_pil:
            return
        new_zoom = max(self._zoom_min, min(zoom, self._zoom_max))
        self._zoom = new_zoom
        self._update_zoom_label()

        # ── ƯU TIÊN: re-render từ PDF tại DPI tương ứng zoom (vector quality) ──
        if self._pdf_renderer is not None:
            try:
                # Cap DPI để tránh OOM khi user zoom quá lớn
                target_dpi = min(int(self._pdf_base_dpi * new_zoom), 1200)
                target_dpi = max(target_dpi, 36)  # tối thiểu để tránh ảnh quá nhỏ
                display = self._pdf_renderer.render(page=0, dpi=target_dpi)
            except Exception:
                # Fail → fallback raster
                display = None
            if display is not None:
                from PIL import ImageTk
                self._img_tk = ImageTk.PhotoImage(display)
                cw = self._canvas.winfo_width() or 500
                ch = self._canvas.winfo_height() or 400
                self._canvas.delete("all")
                self._canvas.create_image(cw // 2, ch // 2,
                                           image=self._img_tk, anchor="center")
                self._canvas.configure(scrollregion=self._canvas.bbox("all"))
                return

        # ── FALLBACK: resize raster (như cũ) — mất chất lượng khi zoom > 1 ──
        w = max(1, int(self._img_pil.width * new_zoom))
        h = max(1, int(self._img_pil.height * new_zoom))
        from PIL import Image as PILImage
        if new_zoom > 1.0:
            display = self._img_pil.resize((w, h), resample=PILImage.LANCZOS)
        else:
            display = self._img_pil.copy()
            display.thumbnail((w, h), resample=PILImage.LANCZOS)

        from PIL import ImageTk
        self._img_tk = ImageTk.PhotoImage(display)
        cw = self._canvas.winfo_width() or 500
        ch = self._canvas.winfo_height() or 400
        self._canvas.delete("all")
        self._canvas.create_image(cw // 2, ch // 2, image=self._img_tk, anchor="center")
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_mouse_wheel(self, event):
        """Zoom with mouse wheel."""
        if not self._img_pil:
            return
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()
        return "break"

    def _on_ctrl_mouse_wheel(self, event):
        """Fine zoom with Ctrl+Mouse wheel."""
        if not self._img_pil:
            return
        delta = event.delta / 120
        self._set_zoom(self._zoom + delta * self._zoom_step)
        return "break"

    # Pan support
    def _on_pan_start(self, event):
        self._canvas._pan_data["start_x"] = event.x
        self._canvas._pan_data["start_y"] = event.y
        self._canvas._pan_data["orig_x"] = self._canvas.xview()[0]
        self._canvas._pan_data["orig_y"] = self._canvas.yview()[0]
        self._canvas._pan_data["active"] = True
        self._canvas.configure(cursor="hand2")

    def _on_pan_move(self, event):
        if not self._canvas._pan_data["active"]:
            return
        dx = event.x - self._canvas._pan_data["start_x"]
        dy = event.y - self._canvas._pan_data["start_y"]
        cw = self._canvas.winfo_width() or 1
        ch = self._canvas.winfo_height() or 1
        x0 = self._canvas._pan_data["orig_x"]
        y0 = self._canvas._pan_data["orig_y"]
        self._canvas.xview_moveto(x0 - dx / cw)
        self._canvas.yview_moveto(y0 - dy / ch)

    def _on_pan_end(self, event):
        self._canvas._pan_data["active"] = False
        self._canvas.configure(cursor="")

    # ══════════════════════════════════════════════════════════════════════════
    #  COPY & SAVE
    # ══════════════════════════════════════════════════════════════════════════

    def _auto_save_rendered_figure(self, tikz_code: str, img) -> None:
        """Lưu preview thành công vào Kho hình, chống trùng theo hash TikZ."""
        try:
            from services import figure_bank

            fid, created = figure_bank.save_rendered(
                tikz_code,
                png_pil=img,
                title="Hình TikZ tự lưu sau render",
                description="Tự động lưu từ tab TikZ V4 sau khi render preview.",
                tags=["TikZ", "tự lưu"],
                source="rendered",
            )
            if created:
                self.after(0, lambda: self._log_console(
                    f"[Kho hình] Đã tự lưu hình render vào kho (ID {fid})",
                    "success",
                ))
        except Exception as exc:
            self.after(0, lambda error=str(exc): self._log_console(
                f"[Kho hình] Không thể tự lưu hình render: {error}",
                "warn",
            ))

    def _create_emf_async(self, on_ready) -> None:
        """Chuyển PDF standalone đã render sang EMF vector bằng Inkscape."""
        if (self._img_emf_path
                and os.path.exists(self._img_emf_path)):
            on_ready(self._img_emf_path)
            return
        if not self._img_pdf_path or not os.path.exists(self._img_pdf_path):
            messagebox.showwarning(
                "Chưa có PDF",
                "Hãy render hình trước để tạo PDF vector rồi xuất EMF.",
                parent=self,
            )
            return
        pdf_path = self._img_pdf_path

        self._status_lbl.config(
            text="⏳ Đang chuyển PDF vector → EMF bằng Inkscape...",
            fg="#2563EB",
        )
        self._log_console("[EMF] Bắt đầu chuyển PDF vector → EMF bằng Inkscape...", "info")

        def _worker():
            try:
                from services.tikz_vector_export import convert_pdf_to_emf

                target = Path(pdf_path).with_suffix(".emf")
                emf_path = convert_pdf_to_emf(
                    pdf_path,
                    target,
                    text_to_path=True,
                )

                def _done(path=str(emf_path)):
                    self._img_emf_path = path
                    on_ready(path)

                self.after(0, _done)
            except Exception as exc:
                error = str(exc)
                self.after(0, lambda: messagebox.showerror(
                    "Lỗi xuất EMF",
                    error,
                    parent=self,
                ))

        threading.Thread(target=_worker, daemon=True,
                         name="tikz-v4-pdf-to-emf").start()

    def _save_emf(self):
        """Lưu EMF vector để chèn vào Word mà không vỡ nét."""
        def _save(emf_path: str):
            path = filedialog.asksaveasfilename(
                defaultextension=".emf",
                filetypes=[("Enhanced Metafile", "*.emf")],
                initialfile="tikz_figure.emf",
            )
            if not path:
                return
            try:
                shutil.copy2(emf_path, path)
                self._status_lbl.config(text="✓ Đã lưu EMF vector", fg="#059669")
                self._log_console(f"[EMF] Đã lưu EMF vector: {path}", "success")
                messagebox.showinfo(
                    "Lưu thành công",
                    f"Đã lưu EMF vector tại:\n{path}\n\n"
                    "Có thể chèn vào Word và phóng lớn mà không vỡ nét.",
                    parent=self,
                )
            except Exception as exc:
                messagebox.showerror("Lỗi lưu EMF", str(exc), parent=self)

        self._create_emf_async(_save)

    def _copy_emf(self):
        """Copy CF_ENHMETAFILE để Word dán ảnh vector thật."""
        def _copy(emf_path: str):
            try:
                from services.tikz_vector_export import copy_emf_to_clipboard

                copy_emf_to_clipboard(emf_path)
                self._status_lbl.config(text="✓ Đã copy EMF vector", fg="#059669")
                self._log_console(
                    "[EMF] Đã copy EMF vector vào clipboard. Dán vào Word bằng Ctrl+V.",
                    "success",
                )
            except Exception as exc:
                messagebox.showerror("Lỗi copy EMF", str(exc), parent=self)

        self._create_emf_async(_copy)

    def _copy_image(self):
        if not self._img_pil:
            messagebox.showwarning("Chưa có ảnh", "Hãy render hình trước.")
            return
        try:
            _copy_pil_to_clipboard(self._img_pil)
            self._status_lbl.config(text="📋 Đã copy ảnh PNG vào clipboard!", fg="#059669")
            self._log_console("[Copy] Đã copy ảnh PNG chất lượng cao vào clipboard", "success")
        except Exception as e:
            messagebox.showerror("Lỗi copy", str(e))

    def _copy_tikz_code(self):
        """Sao chép toàn bộ mã TikZ hiện tại vào clipboard với 1 click."""
        code = self._editor.get("1.0", "end-1c").strip()
        if not code:
            messagebox.showwarning("Trống", "Chưa có mã TikZ trong trình soạn thảo để sao chép.", parent=self)
            return
        self.clipboard_clear()
        self.clipboard_append(code)
        self._status_lbl.config(text="📝 Đã copy mã TikZ vào clipboard!", fg="#059669")
        self._log_console(f"[Copy] Đã copy mã TikZ ({len(code)} ký tự) vào clipboard", "success")

    def _clear_editor(self):
        """Xóa trắng nội dung trình soạn thảo để bắt đầu hình vẽ mới."""
        code = self._editor.get("1.0", "end-1c").strip()
        if not code:
            return
        if messagebox.askyesno("Xóa trắng", "Bạn có chắc muốn xóa toàn bộ mã trong trình soạn thảo để vẽ mới?", parent=self):
            self._editor.delete("1.0", "end")
            self._highlight()
            self._update_line_numbers()
            self._log_console("[Soạn thảo] Đã xóa trắng nội dung.", "info")
            self._status_lbl.config(text="Đã xóa trắng soạn thảo.", fg="#64748B")

    def _clean_code_boilerplate(self):
        """Bóc tách bỏ \\documentclass, \\usepackage, \\begin{document} thừa (tương tự WebTikZ cleanBoilerplate)."""
        code = self._get_code()
        if not code.strip():
            return
        from services.tikz_ai_skill import clean_boilerplate
        cleaned, changed = clean_boilerplate(code)
        if changed:
            self._editor.delete("1.0", "end")
            self._editor.insert("1.0", cleaned)
            self._highlight()
            self._update_line_numbers()
            self._status_lbl.config(text="✨ Đã bóc tách mã TikZ sạch, loại bỏ preamble thừa!", fg="#059669")
            self._log_console("[Boilerplate] Đã làm sạch mã TikZ, loại bỏ preamble/document thừa.", "success")
        else:
            self._status_lbl.config(text="ℹ️ Mã TikZ đã ở dạng chuẩn sạch.", fg="#64748B")
            self._log_console("[Boilerplate] Mã TikZ đã ở dạng chuẩn sạch, không có preamble thừa.", "info")

    def _on_paste_event(self, event=None):
        """Nếu clipboard chứa ảnh (chụp màn hình/copy ảnh), tự động mở dialog AI Vẽ Hình và nạp ảnh."""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is not None:
                self._ai_paste_draw(prefill_image=img)
                return "break"
        except Exception:
            pass
        return None

    def _save_png(self):
        if not self._img_pil:
            messagebox.showwarning("Chưa có ảnh", "Hãy render hình trước.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image (lossless)", "*.png")],
            initialfile="tikz_figure.png")
        if path:
            # Save at render DPI (the actual rendered DPI, not display DPI)
            dpi = self._get_dpi_int()
            self._img_pil.save(path, dpi=(dpi, dpi))
            self._log_console(f"[Save] Đã lưu PNG {self._img_pil.width}×{self._img_pil.height}px @{dpi} DPI: {path}", "success")
            messagebox.showinfo("Lưu thành công",
                               f"Đã lưu PNG tại:\n{path}\n\n"
                               f"Kích thước: {self._img_pil.width}×{self._img_pil.height}px\n"
                               f"Chất lượng: {dpi} DPI\n\n"
                               f"Có thể phóng to/thu nhỏ không bị vỡ ảnh!")

    def _save_svg(self):
        tikz_code = self._editor.get("1.0", "end-1c").strip()
        if not tikz_code:
            messagebox.showwarning("Trống", "Hãy nhập mã TikZ trước.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG Image", "*.svg")],
            initialfile="tikz_figure.svg")
        if not path:
            return
        try:
            svg_text = render_tikz_to_svg(tikz_code)
            Path(path).write_text(svg_text, encoding="utf-8")
            self._log_console(f"[Save] Đã lưu SVG: {path}", "success")
            messagebox.showinfo("Lưu thành công", f"Đã lưu SVG tại:\n{path}")
        except Exception as e:
            messagebox.showerror("Lỗi SVG", str(e))

    def _save_pdf(self):
        if not self._img_pdf_path or not os.path.exists(self._img_pdf_path):
            # Re-render to get PDF if not cached
            tikz_code = self._editor.get("1.0", "end-1c").strip()
            if not tikz_code:
                messagebox.showwarning("Trống", "Hãy render hình trước.")
                return
            try:
                _, _, pdf_path = render_tikz_to_image(
                    tikz_code, dpi=self._get_dpi_int(), return_log=True)
                self._img_pdf_path = pdf_path
            except Exception as e:
                messagebox.showerror("Lỗi render", str(e))
                return

        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            initialfile="tikz_figure.pdf")
        if not path:
            return
        try:
            shutil.copy2(self._img_pdf_path, path)
            self._log_console(f"[Save] Đã lưu PDF: {path}", "success")
            messagebox.showinfo("Lưu thành công", f"Đã lưu PDF tại:\n{path}")
        except Exception as e:
            messagebox.showerror("Lỗi lưu PDF", str(e))

    def _view_pdf(self):
        """Open the rendered PDF in the default PDF viewer."""
        if not self._img_pdf_path or not os.path.exists(self._img_pdf_path):
            tikz_code = self._editor.get("1.0", "end-1c").strip()
            if not tikz_code:
                messagebox.showwarning("Trống", "Hãy render hình trước.")
                return
            try:
                _, _, pdf_path = render_tikz_to_image(
                    tikz_code, dpi=self._get_dpi_int(), return_log=True)
                self._img_pdf_path = pdf_path
            except Exception as e:
                messagebox.showerror("Lỗi render", str(e))
                return

        try:
            os.startfile(self._img_pdf_path) if os.name == "nt" else os.system(f"xdg-open {self._img_pdf_path}")
            self._log_console(f"[View] Đã mở PDF: {self._img_pdf_path}", "success")
        except Exception as e:
            messagebox.showerror("Lỗi mở PDF", str(e))

    def _copy_overleaf_source(self, tex_source: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(tex_source)
        self.update()

    def _open_overleaf(self):
        """Open current TikZ code in Overleaf and copy the .tex fallback."""
        tikz_code = self._editor.get("1.0", "end-1c").strip()
        if not tikz_code:
            messagebox.showwarning("Trống", "Hãy nhập mã TikZ trước.")
            return
        try:
            from services import overleaf_exporter
            launcher_path, tex_source = overleaf_exporter.open_tikz_in_overleaf(tikz_code)
            self._copy_overleaf_source(tex_source)
            self._status_lbl.config(text="🌐 Đã mở Overleaf", fg="#16A34A")
            self._log_console(
                f"[Overleaf] Đã mở trình duyệt qua launcher: {launcher_path}",
                "success",
            )
            messagebox.showinfo(
                "Đã mở Overleaf",
                "Đã mở code TikZ trong Overleaf.\n\n"
                "Nếu trình duyệt không tự import code, source .tex đã được copy vào clipboard để bạn dán thủ công.",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror("Lỗi Overleaf", str(e), parent=self)

    def _check_latex_engine(self):
        """Check local LaTeX engine and compile a tiny TikZ smoke document."""
        self._start_render_timer("Đang kiểm tra LaTeX engine")
        self._log_console("[Engine] Đang kiểm tra pdflatex/xelatex/tectonic...", "info")

        def _worker():
            try:
                from services import latex_engine
                status = latex_engine.check_engine_status()
                if not status.get("ok"):
                    self.after(0, lambda s=status: self._show_engine_missing(s))
                    return
                smoke = latex_engine.smoke_test_engine(timeout=25)
                self.after(0, lambda s=status, sm=smoke: self._show_engine_check_result(s, sm))
            except Exception as exc:
                self.after(0, lambda e=exc: self._show_engine_exception(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_engine_missing(self, status: dict) -> None:
        elapsed = self._stop_render_timer()
        hints = "\n".join(f"  • {h}" for h in status.get("install_hints", []))
        self._status_lbl.config(text=f"⚠ Chưa có LaTeX engine — ⏱ {elapsed}", fg="#D97706")
        self._log_console("[Engine] Không tìm thấy engine local. Có thể dùng Overleaf fallback.", "warn")
        answer = messagebox.askyesno(
            "Chưa có LaTeX engine",
            "Máy chưa tìm thấy pdflatex/xelatex/tectonic trong PATH.\n\n"
            "Có thể cài một trong các lựa chọn:\n"
            f"{hints}\n\n"
            "Bạn có muốn mở code TikZ hiện tại trên Overleaf không?",
            parent=self,
        )
        if answer:
            self._open_overleaf()

    def _show_engine_check_result(self, status: dict, smoke: dict) -> None:
        elapsed = self._stop_render_timer()
        engine = status.get("engine", "")
        binary = status.get("binary", "")
        if smoke.get("ok"):
            self._status_lbl.config(text=f"✅ {engine} OK — compile mẫu thành công — ⏱ {elapsed}", fg="#059669")
            self._log_console(f"[Engine] {engine} OK: {binary}", "success")
            messagebox.showinfo(
                "LaTeX engine OK",
                f"Engine: {engine}\n"
                f"Đường dẫn: {binary}\n\n"
                f"Compile mẫu TikZ thành công sau {elapsed}.",
                parent=self,
            )
            return

        log = (smoke.get("log") or "").strip()
        self._status_lbl.config(text=f"⚠ {engine} lỗi compile mẫu — ⏱ {elapsed}", fg="#D97706")
        self._log_console(f"[Engine] {smoke.get('message', 'Compile mẫu thất bại')}", "warn")
        if log:
            self._log_console(log[-1200:], "warn")
        messagebox.showwarning(
            "LaTeX engine cần kiểm tra",
            f"Đã tìm thấy engine: {engine}\n"
            f"Đường dẫn: {binary}\n\n"
            f"{smoke.get('message', 'Compile mẫu thất bại')}.\n\n"
            "Bạn vẫn có thể dùng nút Overleaf để render online.",
            parent=self,
        )

    def _show_engine_exception(self, exc: Exception) -> None:
        elapsed = self._stop_render_timer()
        self._status_lbl.config(text=f"❌ Lỗi kiểm tra engine — ⏱ {elapsed}", fg="#DC2626")
        self._log_console(f"[Engine] Lỗi kiểm tra: {exc}", "error")
        messagebox.showerror("Lỗi kiểm tra engine", str(exc), parent=self)

    # ══════════════════════════════════════════════════════════════════════════
    #  REFRESH (stub for main_window compatibility)
    # ══════════════════════════════════════════════════════════════════════════

    def refresh(self):
        pass

    def apply_feature_gates(self, features: dict) -> None:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  AI INPUT DIALOG
# ══════════════════════════════════════════════════════════════════════════════

class _AIInputDialog(tk.Toplevel):
    """Simple dialog for AI input prompt.

    Tham số:
        default:   text điền sẵn vào ô input (vd: mô tả gần nhất để chỉnh)
        multiline: True → ENTER xuống dòng, Ctrl+Enter để submit;
                   False (default) → ENTER submit (giữ hành vi cũ)
    """

    def __init__(self, parent, title: str, prompt_text: str,
                 default: str = "", multiline: bool = False):
        super().__init__(parent)
        self.title(title)
        self.configure(bg="#F9F7F4")
        top = parent.winfo_toplevel()
        self.transient(top)
        self.grab_set()
        self.result = ""

        try:
            from ui import set_dialog_icon
            set_dialog_icon(self)
        except Exception:
            pass

        # Header
        hdr = tk.Frame(self, bg="#2563EB")
        hdr.pack(fill="x", side="top")
        tk.Label(hdr, text=f"  ✏️ {title}", font=("Segoe UI", 11, "bold"),
                 bg="#2563EB", fg="white").pack(side="left", padx=12, pady=8)

        # Buttons — pack TRƯỚC body để luôn hiển thị ở đáy
        btn_frame = tk.Frame(self, bg="#F9F7F4")
        btn_frame.pack(fill="x", side="bottom", padx=16, pady=10)

        tk.Button(btn_frame, text="  Tạo  ", font=("Segoe UI", 10, "bold"),
                  bg="#2563EB", fg="white", activebackground="#1D4ED8",
                  activeforeground="white",
                  relief="flat", cursor="hand2", padx=16, pady=5,
                  command=self._ok).pack(side="right", padx=4)
        tk.Button(btn_frame, text="  Hủy  ", font=("Segoe UI", 10),
                  bg="#94A3B8", fg="white", activeforeground="white",
                  relief="flat", cursor="hand2",
                  padx=16, pady=5,
                  command=self.destroy).pack(side="right", padx=4)

        # Body — expand giữa header và buttons
        body = tk.Frame(self, bg="#F9F7F4")
        body.pack(fill="both", expand=True, padx=16, pady=(12, 0))

        tk.Label(body, text=prompt_text, font=("Segoe UI", 10),
                 bg="#F9F7F4", wraplength=450, justify="left"
                 ).pack(anchor="w", pady=(4, 4))

        # Multiline mode → cao hơn để đủ chỗ chỉnh mô tả dài
        height = 12 if multiline else 6
        self._text = tk.Text(body, font=("Segoe UI", 11), height=height,
                             wrap="word", bd=1, relief="solid")
        self._text.pack(fill="both", expand=True)
        if default:
            self._text.insert("1.0", default)
        self._text.focus_set()

        if multiline:
            # Ctrl+Enter submit; Enter xuống dòng (mặc định)
            self.bind("<Control-Return>", lambda e: self._ok())
        else:
            self.bind("<Return>", lambda e: self._ok())

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = (640, 480) if multiline else (540, 340)
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.minsize(420, 280)
        self.lift()
        self.focus_force()

    def _ok(self):
        self.result = self._text.get("1.0", "end-1c").strip()
        if self.result:
            self.destroy()


class _AIPasteDrawDialog(tk.Toplevel):
    """Dialog AI Vẽ Hình TikZ — Chuẩn WebTikZ & Phong cách Thầy Đỗ Minh (DoMinhMath).

    Hỗ trợ:
    - Gửi/Dán ảnh (Ctrl+V) hoặc nhập mô tả/đề bài bằng văn bản.
    - Checkboxes chọn tác vụ nhanh: Bảng biến thiên (BBT), BBT không khung, Đồ thị, Hình học, BXD, Mạch điện, Vẽ tất cả.
    - Nút 1 chạm "🚀 Phân tích & Tự động vẽ TikZ": AI phân tích toàn diện và sinh mã TikZ trực tiếp.
    - Tự động fallback vision: Nếu provider hiện tại (như DeepSeek) không hỗ trợ ảnh hoặc lỗi mạng,
      hệ thống tự động sử dụng khóa Google Gemini / OpenAI GPT / Anthropic Claude có sẵn trong KeyManager.
    - Trả về mã TikZ để nạp vào editor và tự động kích hoạt preview render tức thì.
    """

    def __init__(self, parent, ai_call: Callable, prefill_image=None):
        super().__init__(parent)
        self.title("AI Vẽ Hình TikZ — Chuẩn WebTikZ & Thầy Đỗ Minh (DoMinhMath)")
        # Giữ modal bằng grab_set; không dùng transient() để Windows hiển thị đủ 3 nút Thu nhỏ/Phóng to/Đóng
        self.grab_set()

        self.result_code: str = ""
        self.result_description: str = ""
        self.used_provider: str = ""
        self._ai_call = ai_call
        self._image_bytes: bytes = b""
        self._image_b64: str = ""
        self._image_mime: str = "image/png"
        self._img_tk = None
        self._analyzing = False
        self._analyze_start_time: float | None = None
        self._analyze_tick_id: str | None = None

        svc = getattr(self._ai_call, "__self__", None)
        self._active_provider = getattr(svc, "provider_name", "AI")
        self._active_model = getattr(svc, "model_name", "")

        try:
            from ui import set_dialog_icon
            set_dialog_icon(self)
        except Exception:
            pass

        # ── Header ──
        hdr = tk.Frame(self, bg="#6D28D9")
        hdr.pack(fill="x")
        hdr_top = tk.Frame(hdr, bg="#6D28D9")
        hdr_top.pack(fill="x", padx=14, pady=(8, 2))
        tk.Label(
            hdr_top,
            text="🎨 AI Vẽ Hình TikZ — Phân tích & Tự động vẽ",
            font=("Segoe UI", 11, "bold"),
            bg="#6D28D9",
            fg="white",
        ).pack(side="left")
        tk.Label(
            hdr,
            text="Chỉ cần dán ảnh (Ctrl+V) hoặc chọn file, AI sẽ tự động phân tích và vẽ mã TikZ chuẩn Thầy Đỗ Minh (DoMinhMath).",
            font=("Segoe UI", 8),
            bg="#6D28D9",
            fg="#E0E7FF",
        ).pack(anchor="w", padx=14, pady=(0, 8))

        # ── Info Bar: Active Provider ──
        info_bar = tk.Frame(self, bg="#EEF2F6", bd=1, relief="solid")
        info_bar.pack(fill="x", padx=14, pady=(8, 4))
        p_info_text = f"⚡ Provider hiện tại: {self._active_provider} ({self._active_model})"
        if self._active_provider == "DeepSeek":
            p_info_text += " — 🔄 Tự động chuyển Vision sang Gemini/Claude/OpenAI khi gửi ảnh"
        tk.Label(
            info_bar,
            text=p_info_text,
            font=("Segoe UI", 8),
            bg="#EEF2F6",
            fg="#334155",
        ).pack(side="left", padx=10, pady=4)

        # ── Bottom Action Bar (Cố định ở đáy, không bao giờ bị che) ──
        btn_bar = tk.Frame(self, bg="#F8FAFC", bd=1, relief="ridge")
        btn_bar.pack(fill="x", side="bottom", padx=12, pady=(4, 8))

        # Nút Đóng luôn ở góc trái
        tk.Button(
            btn_bar,
            text="  ✕ Đóng  ",
            font=("Segoe UI", 9, "bold"),
            bg="#64748B",
            fg="white",
            activebackground="#475569",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.destroy,
        ).pack(side="left", padx=4)

        # Các nút hành động chính ở góc phải (không bao giờ đè lên nút Đóng)
        self._draw_btn = tk.Button(
            btn_bar,
            text="  🚀 Phân tích & Tự động vẽ TikZ  ",
            font=("Segoe UI", 10, "bold"),
            bg="#059669",
            fg="white",
            activebackground="#047857",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=6,
            command=self._auto_draw,
        )
        self._draw_btn.pack(side="right", padx=4)

        self._desc_btn = tk.Button(
            btn_bar,
            text="  📝 Chỉ tạo mô tả (2 bước)  ",
            font=("Segoe UI", 9),
            bg="#475569",
            fg="white",
            activebackground="#334155",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
            command=self._describe_only,
        )
        self._desc_btn.pack(side="right", padx=4)

        # Dải hiển thị trạng thái nằm riêng biệt phía trên thanh nút đáy
        status_strip = tk.Frame(self, bg="#F1F5F9", bd=1, relief="solid")
        status_strip.pack(fill="x", side="bottom", padx=12, pady=(0, 2))

        self._status_lbl = tk.Label(
            status_strip,
            text="Sẵn sàng — Dán ảnh (Ctrl+V) hoặc chọn file để bắt đầu.",
            font=("Segoe UI", 8),
            bg="#F1F5F9",
            fg="#475569",
            anchor="w",
        )
        self._status_lbl.pack(fill="x", padx=10, pady=2)

        # ── Scrollable Body Area ──
        body_container = tk.Frame(self, bg="#F8FAFC")
        body_container.pack(fill="both", expand=True, padx=12, pady=(4, 0))

        self._body_canvas = tk.Canvas(body_container, bg="#F8FAFC", highlightthickness=0)
        body_vsb = ttk.Scrollbar(body_container, orient="vertical", command=self._body_canvas.yview)
        body = tk.Frame(self._body_canvas, bg="#F8FAFC")

        self._body_window = self._body_canvas.create_window((0, 0), window=body, anchor="nw")
        self._body_canvas.configure(yscrollcommand=body_vsb.set)

        def _on_body_cfg(e):
            self._body_canvas.configure(scrollregion=self._body_canvas.bbox("all"))

        def _on_canvas_cfg(e):
            self._body_canvas.itemconfig(self._body_window, width=e.width)

        body.bind("<Configure>", _on_body_cfg)
        self._body_canvas.bind("<Configure>", _on_canvas_cfg)

        body_vsb.pack(side="right", fill="y")
        self._body_canvas.pack(side="left", fill="both", expand=True)

        def _on_mousewheel(e):
            if isinstance(e.widget, tk.Text):
                return
            self._body_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            return "break"

        self._body_canvas.bind("<MouseWheel>", _on_mousewheel)
        body.bind("<MouseWheel>", _on_mousewheel)

        # ── 1. Image Section ──
        step1 = tk.LabelFrame(
            body,
            text=" 1. Hình ảnh mẫu (Đề bài, đồ thị, hình vẽ, BBT) ",
            font=("Segoe UI", 9, "bold"),
            bg="#F8FAFC",
            fg="#1E293B",
        )
        step1.pack(fill="x", padx=2, pady=(0, 6))

        img_ctrl = tk.Frame(step1, bg="#F8FAFC")
        img_ctrl.pack(fill="x", padx=8, pady=(4, 2))

        self._choose_btn = tk.Button(
            img_ctrl,
            text="  📁 Chọn ảnh từ máy  ",
            font=("Segoe UI", 9, "bold"),
            bg="#2563EB",
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._choose_image,
        )
        self._choose_btn.pack(side="left", padx=(0, 4))

        self._paste_btn = tk.Button(
            img_ctrl,
            text="  📋 Dán ảnh (Ctrl+V)  ",
            font=("Segoe UI", 9),
            bg="#475569",
            fg="white",
            activebackground="#334155",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self._paste_image,
        )
        self._paste_btn.pack(side="left", padx=2)

        self._clear_img_btn = tk.Button(
            img_ctrl,
            text=" ❌ Xóa ảnh ",
            font=("Segoe UI", 8, "bold"),
            bg="#EF4444",
            fg="white",
            activebackground="#DC2626",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2,
            command=self._clear_image,
        )
        # initially hidden

        self._img_status = tk.Label(
            step1,
            text="Chưa có ảnh (Nhấn Ctrl+V bất cứ đâu để dán ảnh chụp màn hình)",
            font=("Segoe UI", 8),
            bg="#F8FAFC",
            fg="#64748B",
            anchor="w",
        )
        self._img_status.pack(fill="x", padx=10, pady=(2, 4))

        # Image preview frame
        self._img_preview_frame = tk.Frame(step1, bg="#E2E8F0", bd=1, relief="solid")
        # initially hidden

        # ── 2. Quick Tasks (WebTikZ Features) ──
        step2 = tk.LabelFrame(
            body,
            text=" 2. Tùy chọn tác vụ & dạng hình vẽ (Chuẩn WebTikZ & Thầy Đỗ Minh) ",
            font=("Segoe UI", 9, "bold"),
            bg="#F8FAFC",
            fg="#1E293B",
        )
        step2.pack(fill="x", padx=2, pady=(0, 6))

        tasks_f = tk.Frame(step2, bg="#F8FAFC")
        tasks_f.pack(fill="x", padx=8, pady=4)

        self._task_bbt = tk.BooleanVar(value=False)
        self._task_bbt_no_frame = tk.BooleanVar(value=False)
        self._task_graph = tk.BooleanVar(value=False)
        self._task_geo = tk.BooleanVar(value=False)
        self._task_bxd = tk.BooleanVar(value=False)
        self._task_circuit = tk.BooleanVar(value=False)
        self._task_all = tk.BooleanVar(value=False)
        self._opt_notes = tk.BooleanVar(value=True)

        tasks_grid = tk.Frame(tasks_f, bg="#F8FAFC")
        tasks_grid.pack(fill="x", padx=2, pady=2)
        tasks_grid.columnconfigure(0, weight=1)
        tasks_grid.columnconfigure(1, weight=1)
        tasks_grid.columnconfigure(2, weight=1)

        # Cột 1: Đại số & Giải tích
        tk.Checkbutton(tasks_grid, text="📊 BBT có khung", variable=self._task_bbt,
                       bg="#F8FAFC", font=("Segoe UI", 9), anchor="w").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        tk.Checkbutton(tasks_grid, text="📊 BBT không khung", variable=self._task_bbt_no_frame,
                       bg="#F8FAFC", font=("Segoe UI", 9), anchor="w").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        tk.Checkbutton(tasks_grid, text="📋 Bảng xét dấu", variable=self._task_bxd,
                       bg="#F8FAFC", font=("Segoe UI", 9), anchor="w").grid(row=2, column=0, sticky="w", padx=4, pady=3)

        # Cột 2: Đồ thị & Hình học
        tk.Checkbutton(tasks_grid, text="📈 Đồ thị (Ox, Oy, tiệm cận)", variable=self._task_graph,
                       bg="#F8FAFC", font=("Segoe UI", 9), anchor="w").grid(row=0, column=1, sticky="w", padx=4, pady=3)
        tk.Checkbutton(tasks_grid, text="📐 Hình học (2D & 3D)", variable=self._task_geo,
                       bg="#F8FAFC", font=("Segoe UI", 9), anchor="w").grid(row=1, column=1, sticky="w", padx=4, pady=3)
        tk.Checkbutton(tasks_grid, text="🔌 Sơ đồ mạch điện", variable=self._task_circuit,
                       bg="#F8FAFC", font=("Segoe UI", 9), anchor="w").grid(row=2, column=1, sticky="w", padx=4, pady=3)

        # Cột 3: Tác vụ tổng thể & Chú thích
        tk.Checkbutton(tasks_grid, text="🎯 Vẽ tất cả trong ảnh", variable=self._task_all,
                       bg="#F8FAFC", font=("Segoe UI", 9), anchor="w").grid(row=0, column=2, sticky="w", padx=4, pady=3)
        tk.Checkbutton(tasks_grid, text="📝 Chú thích bố cục (%)", variable=self._opt_notes,
                       bg="#F8FAFC", font=("Segoe UI", 9, "bold"), fg="#4338CA", anchor="w").grid(row=1, column=2, sticky="w", padx=4, pady=3)

        # ── 3. Extra Prompt / Text Problem ──
        step3 = tk.LabelFrame(
            body,
            text=" 3. Yêu cầu bổ sung hoặc nhập đề bài (Văn bản) ",
            font=("Segoe UI", 9, "bold"),
            bg="#F8FAFC",
            fg="#1E293B",
        )
        step3.pack(fill="x", padx=2, pady=(0, 6))

        input_container = tk.Frame(step3, bg="white")
        input_container.pack(fill="x", padx=8, pady=4)
        self._input_text = tk.Text(
            input_container,
            font=("Segoe UI", 10),
            height=4,
            wrap="word",
            bd=1,
            relief="solid",
            bg="white",
        )
        input_vsb = ttk.Scrollbar(input_container, orient="vertical", command=self._input_text.yview)
        self._input_text.configure(yscrollcommand=input_vsb.set)
        input_vsb.pack(side="right", fill="y")
        self._input_text.pack(side="left", fill="both", expand=True)

        # ── 4. Expandable Description Area (Dành riêng cho 2 bước) ──
        self._desc_frame = tk.Frame(body, bg="#F8FAFC")
        self._desc_lbl = tk.Label(
            self._desc_frame,
            text="Mô tả AI tạo ra (Bạn có thể chỉnh sửa trước khi xác nhận vẽ):",
            font=("Segoe UI", 9, "bold"),
            bg="#F8FAFC",
            fg="#0F766E",
        )
        self._desc_lbl.pack(anchor="w", padx=2, pady=(2, 2))
        
        desc_container = tk.Frame(self._desc_frame, bg="#F8FAFC")
        desc_container.pack(fill="x", padx=2, pady=(0, 4))
        self._desc_text = tk.Text(
            desc_container,
            font=("Consolas", 10),
            height=6,
            wrap="word",
            bd=1,
            relief="solid",
            bg="#F0FDF4",
        )
        desc_vsb = ttk.Scrollbar(desc_container, orient="vertical", command=self._desc_text.yview)
        self._desc_text.configure(yscrollcommand=desc_vsb.set)
        desc_vsb.pack(side="right", fill="y")
        self._desc_text.pack(side="left", fill="both", expand=True)

        self._confirm_desc_btn = tk.Button(
            self._desc_frame,
            text="  👉 Xác nhận vẽ từ mô tả này  ",
            font=("Segoe UI", 9, "bold"),
            bg="#0D9488",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._confirm_description,
        )
        self._confirm_desc_btn.pack(side="right", padx=2, pady=(0, 4))
        # initially hidden

        # Bindings
        self.bind("<Control-v>", self._on_ctrl_v)
        self.bind("<Control-V>", self._on_ctrl_v)
        self.bind("<Escape>", lambda e: self.destroy())

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(1040, max(920, int(sw * 0.75)))
        h = min(780, max(580, int(sh * 0.85)))
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.minsize(820, 520)
        self.resizable(True, True)
        try:
            self.attributes("-toolwindow", False)
        except Exception:
            pass
        self.lift()
        self.focus_force()

        if prefill_image is not None:
            try:
                import io
                buf = io.BytesIO()
                prefill_image.save(buf, format="PNG")
                self._set_image_data(buf.getvalue(), "image/png", prefill_image)
            except Exception as e:
                _log.warning("Không nạp được ảnh prefill: %s", e)

    # ── Input Handling & Image Management ──

    def _on_ctrl_v(self, event=None):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is not None:
                self._paste_image()
                return "break"
        except Exception:
            pass
        return None

    def _choose_image(self):
        path = filedialog.askopenfilename(
            title="Chọn ảnh hình mẫu",
            filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"),
                       ("Tất cả", "*.*")],
            parent=self,
        )
        if path:
            self._load_image_file(path)

    def _paste_image(self):
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is None:
                self._img_status.config(
                    text="Clipboard không có ảnh. Hãy nhấn Win+Shift+S chụp rồi dán lại.",
                    fg="#EF4444",
                )
                return
            import io
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            data = buf.getvalue()
            self._set_image_data(data, "image/png", img)
        except Exception as e:
            self._img_status.config(text=f"Lỗi dán: {e}", fg="#EF4444")

    def _load_image_file(self, path: str):
        try:
            from PIL import Image
            img = Image.open(path)
            data = Path(path).read_bytes()
            ext = Path(path).suffix.lower().lstrip(".")
            mime = "image/png"
            if ext in ("jpg", "jpeg"):
                mime = "image/jpeg"
            elif ext == "webp":
                mime = "image/webp"
            elif ext == "gif":
                mime = "image/gif"
            self._set_image_data(data, mime, img)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được ảnh:\n{e}", parent=self)

    def _set_image_data(self, data: bytes, mime: str, pil_img):
        import base64
        self._image_bytes = data
        self._image_b64 = base64.b64encode(data).decode("utf-8")
        self._image_mime = mime
        size_kb = len(data) / 1024
        self._img_status.config(
            text=f"✅ Đã nhận ảnh: {pil_img.width}x{pil_img.height}px ({size_kb:.0f} KB)",
            fg="#059669",
        )

        from PIL import ImageTk
        preview = pil_img.copy()
        max_w, max_h = 240, 110
        preview.thumbnail((max_w, max_h))
        self._img_tk = ImageTk.PhotoImage(preview)

        self._img_preview_frame.pack(fill="x", padx=8, pady=4)
        for w in self._img_preview_frame.winfo_children():
            w.destroy()
        lbl = tk.Label(self._img_preview_frame, image=self._img_tk, bg="#E2E8F0")
        lbl.pack(padx=4, pady=4)
        self._clear_img_btn.pack(side="left", padx=8)

    def _clear_image(self):
        self._image_bytes = b""
        self._image_b64 = ""
        self._image_mime = "image/png"
        self._img_tk = None
        self._img_status.config(text="Chưa có ảnh (Nhấn Ctrl+V bất cứ đâu để dán)", fg="#64748B")
        self._img_preview_frame.pack_forget()
        self._clear_img_btn.pack_forget()

    def _get_selected_tasks(self) -> list[str]:
        tasks = []
        if self._task_bbt.get():
            tasks.append("Bảng biến thiên (BBT) (nocadre=true)" if self._task_bbt_no_frame.get() else "Bảng biến thiên (BBT) có kẻ bảng (nocadre=false)")
        elif self._task_bbt_no_frame.get():
            tasks.append("Bảng biến thiên (BBT) (nocadre=true)")
        if self._task_graph.get():
            tasks.append("Đồ thị hàm số")
        if self._task_geo.get():
            tasks.append("Hình vẽ hình học (2D hoặc 3D không gian)")
        if self._task_bxd.get():
            tasks.append("Bảng xét dấu")
        if self._task_circuit.get():
            tasks.append("Sơ đồ mạch điện (circuitikz)")
        if self._task_all.get():
            tasks.append("Tất cả các hình vẽ, đồ thị, bảng biến thiên có trong ảnh mà không bỏ sót")
        return tasks

    def _set_ui_state(self, state: str):
        self._draw_btn.config(state=state)
        self._desc_btn.config(state=state)
        self._choose_btn.config(state=state)
        self._paste_btn.config(state=state)
        if hasattr(self, "_clear_img_btn"):
            self._clear_img_btn.config(state=state)

    def _tick_analyze(self):
        if not self._analyzing or self._analyze_start_time is None:
            return
        elapsed = time.time() - self._analyze_start_time
        has_image = bool(self._image_bytes)
        prefix = "AI đang phân tích ảnh & lập trình TikZ" if has_image else "AI đang xử lý văn bản"
        try:
            self._status_lbl.config(
                text=f"⏳ {prefix}... ({elapsed:.1f}s)",
                fg="#6D28D9",
            )
        except tk.TclError:
            return
        self._analyze_tick_id = self.after(100, self._tick_analyze)

    def _stop_tick_analyze(self):
        if self._analyze_tick_id is not None:
            try:
                self.after_cancel(self._analyze_tick_id)
            except Exception:
                pass
            self._analyze_tick_id = None

    # ── One-shot Direct Draw (Chuẩn WebTikZ) ──

    def _auto_draw(self):
        has_image = bool(self._image_bytes)
        extra_text = self._input_text.get("1.0", "end-1c").strip()

        if not has_image and not extra_text:
            messagebox.showwarning(
                "Chưa có dữ liệu",
                "Vui lòng chọn/dán ảnh (Ctrl+V) hoặc nhập yêu cầu/đề bài vào ô văn bản.",
                parent=self,
            )
            return

        if self._analyzing:
            return

        self._analyzing = True
        self._analyze_start_time = time.time()
        self._set_ui_state("disabled")
        self._status_lbl.config(
            text="⏳ AI đang phân tích và tự động vẽ TikZ... (0.0s)",
            fg="#6D28D9",
        )
        self._tick_analyze()

        tasks = self._get_selected_tasks()
        enable_notes = self._opt_notes.get()
        bbt_no_frame = self._task_bbt_no_frame.get()

        def _worker():
            try:
                from services import tikz_ai_skill
                from services.ai_service import execute_vision_call

                service = getattr(self._ai_call, "__self__", None)

                if has_image:
                    prompt = tikz_ai_skill.get_tikz_vision_prompt(
                        extra_prompt=extra_text,
                        tasks=tasks,
                        enable_notes=enable_notes,
                        bbt_no_frame=bbt_no_frame,
                    )
                    res, used_p = execute_vision_call(
                        prompt=prompt,
                        image_data=self._image_bytes,
                        mime_type=self._image_mime,
                        active_service=service,
                    )
                    cleaned = tikz_ai_skill.clean_tikz_boilerplate(res)
                    self.after(0, lambda c=cleaned, p=used_p: self._on_auto_draw_done(c, p))
                else:
                    full_text = extra_text
                    if tasks:
                        full_text = f"Yêu cầu: {', '.join(tasks)}.\n{extra_text}"
                    prompt = tikz_ai_skill.get_tikz_draw_prompt(full_text)
                    raw_res = self._ai_call(prompt)
                    cleaned = tikz_ai_skill.clean_tikz_boilerplate(raw_res)
                    p_name = getattr(service, "provider_name", "AI")
                    self.after(0, lambda c=cleaned, p=p_name: self._on_auto_draw_done(c, p))

            except Exception as exc:
                err_str = str(exc)
                self.after(0, lambda err=err_str: self._on_analyze_error(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_auto_draw_done(self, code: str, provider_name: str):
        self._stop_tick_analyze()
        self._analyzing = False
        self.result_code = code
        self.used_provider = provider_name
        self.destroy()

    def _on_analyze_error(self, err: str):
        elapsed = (time.time() - self._analyze_start_time
                   if self._analyze_start_time else 0.0)
        self._analyzing = False
        self._stop_tick_analyze()
        self._set_ui_state("normal")
        self._status_lbl.config(
            text=f"❌ Lỗi sau {elapsed:.1f}s: {err[:60]}",
            fg="#EF4444",
        )
        messagebox.showerror("Lỗi AI", f"Không thể xử lý yêu cầu:\n\n{err}", parent=self)

    # ── Two-step Describe Workflow (Chỉ tạo mô tả) ──

    def _describe_only(self):
        has_image = bool(self._image_bytes)
        extra_text = self._input_text.get("1.0", "end-1c").strip()

        if not has_image and not extra_text:
            messagebox.showwarning(
                "Chưa có dữ liệu",
                "Vui lòng chọn/dán ảnh (Ctrl+V) hoặc nhập nội dung vào ô văn bản.",
                parent=self,
            )
            return

        if self._analyzing:
            return

        self._analyzing = True
        self._analyze_start_time = time.time()
        self._set_ui_state("disabled")
        self._status_lbl.config(
            text="⏳ AI đang phân tích tạo mô tả... (0.0s)",
            fg="#6D28D9",
        )
        self._tick_analyze()

        def _worker():
            try:
                from services.ai_service import execute_vision_call
                service = getattr(self._ai_call, "__self__", None)
                if has_image:
                    prompt = _AI_DESCRIBE_IMAGE_PROMPT
                    if extra_text:
                        prompt += f"\n\nGỢI Ý THÊM TỪ NGƯỜI DÙNG:\n{extra_text}"
                    desc, used_p = execute_vision_call(
                        prompt=prompt,
                        image_data=self._image_bytes,
                        mime_type=self._image_mime,
                        active_service=service,
                    )
                else:
                    prompt = _AI_DESCRIBE_TEXT_PROMPT.format(content=extra_text)
                    desc = self._ai_call(prompt)
                self.after(0, lambda d=desc: self._on_describe_done(d))
            except Exception as exc:
                err_str = str(exc)
                self.after(0, lambda err=err_str: self._on_analyze_error(err))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_describe_done(self, description: str):
        elapsed = (time.time() - self._analyze_start_time
                   if self._analyze_start_time else 0.0)
        self._analyzing = False
        self._stop_tick_analyze()
        self._set_ui_state("normal")
        self._status_lbl.config(
            text=f"✅ Đã tạo mô tả xong ({elapsed:.1f}s)",
            fg="#059669",
        )
        self._desc_frame.pack(fill="x", padx=2, pady=4)
        self._desc_text.delete("1.0", "end")
        self._desc_text.insert("1.0", description.strip())
        try:
            self.after(50, lambda: self._body_canvas.yview_moveto(1.0))
        except Exception:
            pass

    def _confirm_description(self):
        desc = self._desc_text.get("1.0", "end-1c").strip()
        if not desc:
            messagebox.showwarning("Trống", "Chưa có mô tả để vẽ.", parent=self)
            return
        self.result_description = desc
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  RENDER ENGINE — pdflatex → PDF → PNG (via PyMuPDF) hoặc SVG (via dvisvgm)
# ══════════════════════════════════════════════════════════════════════════════

def _get_startupinfo():
    """Return startupinfo to hide CMD window on Windows."""
    if os.name == "nt":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        return si
    return None


def render_tikz_to_image(tikz_code: str, dpi: int = 300,
                         return_log: bool = False):
    """Render TikZ code → high-quality PIL Image.

    If return_log=True, returns (img, log_text, pdf_path) tuple.
    pdf_path trỏ tới file trong %TEMP% với tên duy nhất theo PID + UUID (tránh
    race condition WinError 32 khi pipeline render song song). Nếu
    return_log=False (mặc định — pipeline dùng), KHÔNG copy PDF ra ngoài tmpdir,
    tránh lock file giữa các worker.
    """
    # shutil đã import top-level — KHÔNG re-import local
    # (local re-import từng gây NameError ở PyInstaller frozen build)
    from PIL import Image
    from config import PDFLATEX_TIMEOUT
    from services import latex_engine

    try:
        engine = latex_engine.get_engine()
    except latex_engine.LatexEngineNotFound as e:
        raise RuntimeError(str(e))

    si = _get_startupinfo()
    cflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    with latex_engine.safe_temporary_directory(prefix="tikz_") as tmpdir:
        tex_path = os.path.join(tmpdir, "figure.tex")
        pdf_path = os.path.join(tmpdir, "figure.pdf")

        latex_src = _LATEX_TEMPLATE.format(tikz_code=tikz_code)
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_src)

        result = subprocess.run(
            engine.build_argv("figure.tex"),
            cwd=tmpdir,
            capture_output=True, text=True, timeout=PDFLATEX_TIMEOUT,
            startupinfo=si, creationflags=cflags,
        )

        # Gộp cả stdout + stderr — pdflatex log có thể ở stderr (vd lỗi I/O,
        # missing package) → trước đây err_msg rỗng vì chỉ đọc stdout.
        log_text = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
        # Đọc thêm .log file nếu có (chứa traceback chi tiết hơn stdout)
        log_file = os.path.join(tmpdir, "figure.log")
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8", errors="replace") as _lf:
                    log_text += "\n" + _lf.read()
            except Exception: pass

        if not os.path.exists(pdf_path):
            err_lines = [l for l in log_text.splitlines() if l.startswith("!")]
            # Thêm context: lines around "! Emergency stop" / "Fatal error"
            if not err_lines:
                # Lấy 30 dòng cuối (thường chứa error context)
                tail_lines = log_text.splitlines()[-30:]
                err_msg = "\n".join(tail_lines) if tail_lines else \
                    "Không có log — pdflatex có thể chưa cài hoặc bị block."
            else:
                err_msg = "\n".join(err_lines[:15])
            raise RuntimeError(f"{engine.name} thất bại:\n{err_msg[:2000]}")

        # Chỉ sao chép PDF ra ngoài %TEMP% khi caller thực sự cần (UI preview).
        # Tránh race condition WinError 32 khi pipeline render song song:
        # nhiều thread cùng ghi vào MỘT file path = cùng lúc lock nhau.
        persistent_pdf = ""
        if return_log:
            # Tên file duy nhất mỗi call để nhiều UI preview cũng không đụng.
            import uuid
            persistent_pdf = os.path.join(
                tempfile.gettempdir(),
                f"MatrixExamAI_tikz_preview_{os.getpid()}_{uuid.uuid4().hex[:8]}.pdf",
            )
            try:
                shutil.copy2(pdf_path, persistent_pdf)
            except OSError:
                # Nếu copy fail cũng không làm hỏng render chính — vẫn trả ảnh
                persistent_pdf = ""

        # PDF → high-res PNG via PyMuPDF
        try:
            import fitz
            doc = fitz.open(pdf_path)
            try:
                page = doc[0]
                zoom = dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                if return_log:
                    return img, log_text, persistent_pdf
                return img
            finally:
                doc.close()
        except ImportError:
            pass

        # Fallback: pdftoppm
        pdftoppm = shutil.which("pdftoppm")
        if pdftoppm:
            png_prefix = os.path.join(tmpdir, "out")
            subprocess.run(
                [pdftoppm, "-r", str(dpi), "-png", pdf_path, png_prefix],
                capture_output=True, timeout=15,
                startupinfo=si, creationflags=cflags,
            )
            for cand in [f"{png_prefix}-1.png", f"{png_prefix}-01.png"]:
                if os.path.exists(cand):
                    img = Image.open(cand).copy()
                    if return_log:
                        return img, log_text, persistent_pdf
                    return img

        raise RuntimeError("Không thể chuyển PDF→PNG. Cần cài PyMuPDF hoặc pdftoppm.")


def render_tikz_to_svg(tikz_code: str) -> str:
    """Render TikZ → chuỗi SVG.

    Thứ tự: (1) LaTeX engine → PDF, (2) PyMuPDF Page.get_svg_image (khớp luồng PNG),
    (3) dvisvgm nếu có (thử vài tùy chọn). PyMuPDF thường ổn định hơn dvisvgm trên Windows.
    """
    # shutil đã import top-level — không cần re-import
    from config import PDFLATEX_TIMEOUT
    from services import latex_engine

    try:
        engine = latex_engine.get_engine()
    except latex_engine.LatexEngineNotFound as e:
        raise RuntimeError(str(e))

    si = _get_startupinfo()
    cflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    with latex_engine.safe_temporary_directory(prefix="tikz_svg_") as tmpdir:
        tex_path = os.path.join(tmpdir, "figure.tex")
        pdf_path = os.path.join(tmpdir, "figure.pdf")
        svg_path = os.path.join(tmpdir, "figure.svg")

        latex_src = _LATEX_TEMPLATE.format(tikz_code=tikz_code)
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_src)

        plog = subprocess.run(
            engine.build_argv("figure.tex"),
            cwd=tmpdir, capture_output=True, text=True, timeout=PDFLATEX_TIMEOUT,
            startupinfo=si, creationflags=cflags,
        )
        if not os.path.exists(pdf_path):
            tail = (plog.stdout or "")[-2000:]
            raise RuntimeError(
                f"{engine.name} thất bại khi tạo SVG.\n" + tail
            )

        # ── 1) PyMuPDF: PDF → SVG (cùng engine với xem trước PNG) ──
        try:
            import fitz
            doc = fitz.open(pdf_path)
            try:
                page = doc[0]
                getter = getattr(page, "get_svg_image", None)
                if callable(getter):
                    svg_text = getter()
                    if isinstance(svg_text, bytes):
                        svg_text = svg_text.decode("utf-8", errors="replace")
                    if svg_text and "<svg" in svg_text.lower():
                        return svg_text
            finally:
                doc.close()
        except Exception:
            pass

        # ── 2) dvisvgm (fallback): thử lệnh khác nhau, ghi log lỗi ──
        dvisvgm = shutil.which("dvisvgm")
        if not dvisvgm:
            raise RuntimeError(
                "Không tạo được SVG bằng PyMuPDF và không tìm thấy dvisvgm.\n"
                "→ Cài: pip install pymupdf\n"
                "   hoặc cài dvisvgm (MiKTeX → dvisvgm package)."
            )

        cmd_variants = [
            [dvisvgm, "--pdf", "-o", svg_path, pdf_path],
            [dvisvgm, "--pdf", "--bbox=min", "-o", svg_path, pdf_path],
            [dvisvgm, "--pdf", "--no-fonts", "-o", svg_path, pdf_path],
        ]
        last_err = ""
        for cmd in cmd_variants:
            try:
                if os.path.exists(svg_path):
                    os.remove(svg_path)
            except OSError:
                pass
            r = subprocess.run(
                cmd, cwd=tmpdir, capture_output=True, text=True, timeout=60,
                startupinfo=si, creationflags=cflags,
            )
            if os.path.exists(svg_path):
                return Path(svg_path).read_text(encoding="utf-8")
            chunk = ((r.stderr or "") + "\n" + (r.stdout or "")).strip()
            if chunk:
                last_err = chunk[-1500:]

        hint = last_err or f"mã thoát dvisvgm (lần cuối): {r.returncode}"
        raise RuntimeError(
            "dvisvgm không tạo được file SVG.\n"
            "Gợi ý: cài PyMuPDF (pip install pymupdf) để xuất SVG không cần dvisvgm.\n\n"
            f"Chi tiết:\n{hint}"
        )


# ══════════════════════════════════════════════════════════════════════════════
#  CLIPBOARD — Copy PIL Image to Windows clipboard
# ══════════════════════════════════════════════════════════════════════════════

def _copy_pil_to_clipboard(img: "Image.Image"):
    """Copy a PIL Image to the Windows clipboard as BMP."""
    import io
    import ctypes
    from ctypes import c_size_t, c_void_p

    bmp_buffer = io.BytesIO()
    img.convert("RGB").save(bmp_buffer, format="BMP")
    bmp_data = bmp_buffer.getvalue()

    dib_data = bmp_data[14:]

    CF_DIB = 8
    GHND = 0x0042

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    kernel32.GlobalAlloc.restype = c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, c_size_t]
    kernel32.GlobalLock.restype = c_void_p
    kernel32.GlobalLock.argtypes = [c_void_p]
    kernel32.GlobalUnlock.argtypes = [c_void_p]
    user32.SetClipboardData.restype = c_void_p
    user32.SetClipboardData.argtypes = [ctypes.c_uint, c_void_p]

    user32.OpenClipboard(0)
    user32.EmptyClipboard()

    hMem = kernel32.GlobalAlloc(GHND, len(dib_data))
    pMem = kernel32.GlobalLock(hMem)
    ctypes.memmove(pMem, dib_data, len(dib_data))
    kernel32.GlobalUnlock(hMem)
    user32.SetClipboardData(CF_DIB, hMem)
    user32.CloseClipboard()


# ══════════════════════════════════════════════════════════════════════════
#  DIALOG: SAVE TO FIGURE BANK
# ══════════════════════════════════════════════════════════════════════════

class _SaveFigureDialog(tk.Toplevel):
    """Dialog nhập metadata trước khi lưu hình vào kho NHCH hình."""

    def __init__(self, parent, has_rendered_image: bool):
        super().__init__(parent)
        self.title("💾 Lưu hình vào kho NHCH")
        self.configure(bg="#F8FAFC")
        self.transient(parent)
        self.grab_set()

        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w, h = 540, 520
        x = max(20, (sw - w) // 2)
        y = max(20, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(520, 500)
        self.resizable(False, False)
        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Control-Return>", lambda _e: self._on_save())

        try:
            from ui import set_dialog_icon
            set_dialog_icon(self)
        except Exception:
            pass

        self.confirmed = False
        self.result_title = ""
        self.result_desc = ""
        self.result_tags: list[str] = []
        self.save_png = False
        self._has_image = has_rendered_image

        self._build()
        self._title_entry.focus()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg="#0F2D52")
        hdr.pack(fill="x")
        tk.Label(hdr, text="  💾  LƯU HÌNH VÀO KHO NHCH",
                 bg="#0F2D52", fg="white",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=12, pady=10)

        # Footer cố định ngoài body để nút không bị cắt khi Windows scaling >100%.
        btn_footer = tk.Frame(self, bg="#E2E8F0", height=58)
        btn_footer.pack(fill="x", side="bottom")
        btn_row = tk.Frame(btn_footer, bg="#E2E8F0")
        btn_row.pack(fill="x", padx=20, pady=10)
        tk.Button(btn_row, text="  💾 Lưu hình  ",
                  bg="#10B981", fg="white", activebackground="#059669",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2", padx=14, pady=6,
                  command=self._on_save).pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="  Huỷ  ",
                  bg="#94A3B8", fg="white", activebackground="#64748B",
                  font=("Segoe UI", 10),
                  relief="flat", cursor="hand2", padx=14, pady=6,
                  command=self.destroy).pack(side="right")

        body = tk.Frame(self, bg="#F8FAFC")
        body.pack(fill="both", expand=True, padx=20, pady=(14, 6))

        tk.Label(body, text="Tên hình *:", bg="#F8FAFC",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self._title_entry = tk.Entry(body, font=("Segoe UI", 10), relief="solid", bd=1)
        self._title_entry.pack(fill="x", pady=(2, 8))

        tk.Label(body, text="Mô tả ngắn (tuỳ chọn):", bg="#F8FAFC",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self._desc_text = tk.Text(body, height=4, font=("Segoe UI", 10),
                                  relief="solid", bd=1, wrap="word")
        self._desc_text.pack(fill="x", pady=(2, 8))

        tk.Label(body, text="Tags (cách nhau bởi dấu phẩy, vd: 2D, tam giác, vuông):",
                 bg="#F8FAFC", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self._tags_entry = tk.Entry(body, font=("Segoe UI", 10), relief="solid", bd=1)
        self._tags_entry.pack(fill="x", pady=(2, 12))

        # Tuỳ chọn lưu PNG
        self._save_png_var = tk.BooleanVar(value=self._has_image)
        chk = tk.Checkbutton(
            body,
            text=("Lưu thêm ảnh PNG (đã render)" if self._has_image
                  else "Lưu ảnh PNG — chưa render hình, chỉ lưu .tex"),
            variable=self._save_png_var,
            state="normal" if self._has_image else "disabled",
            bg="#F8FAFC", font=("Segoe UI", 10),
        )
        chk.pack(anchor="w")

    def _on_save(self):
        title = self._title_entry.get().strip()
        if not title:
            messagebox.showwarning("Thiếu tên", "Hãy nhập tên cho hình.", parent=self)
            return
        self.result_title = title
        self.result_desc = self._desc_text.get("1.0", "end-1c").strip()
        self.result_tags = [t.strip() for t in self._tags_entry.get().split(",")
                            if t.strip()]
        self.save_png = bool(self._save_png_var.get()) and self._has_image
        self.confirmed = True
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════
#  DIALOG: BROWSE FIGURE BANK — REDESIGNED (v2)
# ══════════════════════════════════════════════════════════════════════════
#  Cải thiện so với v1:
#   • Layout 2 cột rõ ràng: list bên trái + preview bên phải (PNG thumbnail
#     khi có / code text khi không có PNG).
#   • Font lớn hơn (10pt) cho tree + preview header.
#   • Action buttons to vừa phải (padx=14, pady=8) — không quá nhỏ/quá to.
#   • Thanh search + filter rộng rãi, tăng khoảng cách.
#   • Header có icon + thống kê tổng số hình + có/không PNG nổi bật.
#   • Notebook tab: "📋 Code TikZ" / "🖼 Ảnh PNG" — chuyển nhanh xem code/ảnh.

class _FigureBankDialog(tk.Toplevel):
    """Dialog duyệt kho NHCH hình — list, search, preview, load, delete."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("📚 Kho NHCH hình vẽ")
        self.configure(bg="#F8FAFC")
        # KHÔNG transient — để title bar có nút min/max chuẩn Windows.
        self.grab_set()

        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w, h = min(1080, sw - 80), min(680, sh - 100)
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.resizable(True, True)
        self.minsize(720, 480)

        # Bật min/max trên title bar
        try:
            self.attributes("-toolwindow", False)
        except Exception:
            pass

        try:
            from ui import set_dialog_icon
            set_dialog_icon(self)
        except Exception:
            pass

        # Output: nếu user double-click hoặc bấm "Nạp & Mở hình ngay"
        self.loaded_tikz = ""
        self.loaded_title = ""
        self.loaded_png_path = ""
        self._tk_preview_img = None  # giữ ref ảnh preview

        self._build()
        self._refresh_list()

        # Phím tắt
        self.bind("<F11>",    lambda _e: self._toggle_maximize())
        self.bind("<Escape>", lambda _e: self.destroy())

    def _toggle_maximize(self):
        """F11 toggle phóng to — phụ trợ cho nút 🗖 trên title bar."""
        import sys
        try:
            if sys.platform == "win32":
                self.state("zoomed" if self.state() != "zoomed" else "normal")
            else:
                cur = bool(self.attributes("-fullscreen"))
                self.attributes("-fullscreen", not cur)
        except Exception:
            pass

    def _build(self):
        # ══ THỨ TỰ PACK QUAN TRỌNG ═══════════════════════════════════════
        # Pack hint + action bar TRƯỚC body (với side="bottom") để các nút
        # luôn hiện ở đáy, dù body expand=True hoặc cửa sổ resize.
        # ════════════════════════════════════════════════════════════════

        # ── 1. Header ──
        hdr = tk.Frame(self, bg="#0F2D52", height=56)
        hdr.pack(side="top", fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  📚  KHO NHCH HÌNH VẼ",
                 bg="#0F2D52", fg="white",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=16, pady=12)
        self._stats_lbl = tk.Label(hdr, text="", bg="#0F2D52", fg="#FCD34D",
                                    font=("Segoe UI", 11, "bold"))
        self._stats_lbl.pack(side="right", padx=16, pady=12)
        # Double-click header để toggle maximize
        hdr.bind("<Double-1>", lambda _e: self._toggle_maximize())

        # ── 2. Accent line ──
        tk.Frame(self, bg="#10B981", height=3).pack(side="top", fill="x")

        # ── 3. Search + filter bar ──
        sb = tk.Frame(self, bg="#E2E8F0", height=50)
        sb.pack(side="top", fill="x")
        sb.pack_propagate(False)

        tk.Label(sb, text="🔍 Tìm:", bg="#E2E8F0",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=(12, 4), pady=10)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh_list())
        ent = tk.Entry(sb, textvariable=self._search_var, font=("Segoe UI", 11),
                       relief="solid", bd=1, width=28)
        ent.pack(side="left", padx=(0, 16), pady=10, ipady=4)

        tk.Label(sb, text="Nguồn:", bg="#E2E8F0",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=(0, 4))
        self._src_var = tk.StringVar(value="all")
        for label, val in [("Tất cả", "all"), ("🤖 AI", "ai"),
                           ("✋ Thủ công", "manual"), ("📐 Mẫu", "template"),
                           ("🗂 NHCH", "nhch"), ("💾 Render", "rendered")]:
            tk.Radiobutton(sb, text=label, variable=self._src_var, value=val,
                           bg="#E2E8F0", font=("Segoe UI", 10),
                           command=self._refresh_list).pack(side="left", padx=4)

        # ── 4 + 5. PACK FOOTER TRƯỚC BODY → luôn hiện ở đáy ──
        self._build_footer()

        # ── 6. Body — 2 cột: list (trái) + preview (phải) ──
        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(side="top", fill="both", expand=True, padx=10, pady=(8, 4))

        # LIST PANEL ─────────────────────────────────────────────────
        list_f = tk.Frame(body, bg="#FFFFFF", bd=1, relief="solid")
        body.add(list_f, weight=2)

        # Header với toggle View
        hdr_row = tk.Frame(list_f, bg="#1E293B")
        hdr_row.pack(fill="x")
        tk.Label(hdr_row, text="Danh sách hình",
                 bg="#1E293B", fg="white", font=("Segoe UI", 10, "bold"),
                 anchor="w", padx=10, pady=6).pack(side="left")
        # Toggle: List ⟷ Grid
        self._view_mode = tk.StringVar(value="list")
        view_box = tk.Frame(hdr_row, bg="#1E293B")
        view_box.pack(side="right", padx=8, pady=4)
        for label, val in [("📋 List", "list"), ("🖼 Grid", "grid")]:
            tk.Radiobutton(
                view_box, text=label, variable=self._view_mode, value=val,
                bg="#1E293B", fg="white", selectcolor="#3B82F6",
                activebackground="#334155", activeforeground="white",
                font=("Segoe UI", 9, "bold"),
                command=self._switch_view,
            ).pack(side="left", padx=2)

        # Container cho 2 view (chỉ hiện 1 tại 1 thời điểm)
        self._list_container = tk.Frame(list_f, bg="#FFFFFF")
        self._list_container.pack(fill="both", expand=True)
        self._grid_container = tk.Frame(list_f, bg="#F1F5F9")

        # ttk style — tăng row height + font
        style = ttk.Style()
        style.configure("Bank.Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Bank.Treeview.Heading", font=("Segoe UI", 10, "bold"))

        # ── View 1: List (Treeview) ──
        cols = ("id", "title", "source", "tags", "created")
        self._tree = ttk.Treeview(self._list_container, columns=cols,
                                   show="headings", style="Bank.Treeview",
                                   height=18)
        for c, width, h in [("id", 60, "ID"), ("title", 250, "Tên hình"),
                            ("source", 120, "Nguồn"), ("tags", 150, "Tags"),
                            ("created", 110, "Ngày tạo")]:
            self._tree.heading(c, text=h)
            self._tree.column(c, width=width, anchor="w")
        vsb = ttk.Scrollbar(self._list_container, orient="vertical",
                            command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", lambda e: self._on_load())

        # ── View 2: Grid (canvas + scrollable frame chứa cards) ──
        self._grid_canvas = tk.Canvas(self._grid_container, bg="#F1F5F9",
                                       highlightthickness=0)
        gvsb = ttk.Scrollbar(self._grid_container, orient="vertical",
                             command=self._grid_canvas.yview)
        self._grid_canvas.configure(yscrollcommand=gvsb.set)
        gvsb.pack(side="right", fill="y")
        self._grid_canvas.pack(side="left", fill="both", expand=True)
        self._grid_inner = tk.Frame(self._grid_canvas, bg="#F1F5F9")
        self._grid_canvas.create_window((0, 0), window=self._grid_inner,
                                         anchor="nw")
        self._grid_inner.bind(
            "<Configure>",
            lambda e: self._grid_canvas.configure(
                scrollregion=self._grid_canvas.bbox("all")
            ),
        )
        self._grid_canvas.bind(
            "<MouseWheel>",
            lambda e: self._grid_canvas.yview_scroll(
                int(-3 * (e.delta / 120)), "units",
            ),
        )
        # Giữ ref các PhotoImage để Tk không GC mất
        self._grid_thumbs: list = []
        self._grid_selected_fid: str = ""

        # PREVIEW PANEL ──────────────────────────────────────────────
        prev_f = tk.Frame(body, bg="#F8FAFC", bd=1, relief="solid")
        body.add(prev_f, weight=3)

        # Header
        prev_hdr = tk.Frame(prev_f, bg="#1E293B")
        prev_hdr.pack(fill="x")
        tk.Label(prev_hdr, text="Xem trước",
                 bg="#1E293B", fg="white", font=("Segoe UI", 10, "bold"),
                 anchor="w", padx=10, pady=6).pack(side="left")
        self._preview_meta_lbl = tk.Label(
            prev_hdr, text="", bg="#1E293B", fg="#94A3B8",
            font=("Segoe UI", 9), anchor="e",
        )
        self._preview_meta_lbl.pack(side="right", padx=10, pady=6)

        # Notebook 2 tabs: Image (PNG) + Code (TikZ)
        nb = ttk.Notebook(prev_f)
        nb.pack(fill="both", expand=True, padx=4, pady=4)

        # Tab 1: Image
        img_tab = tk.Frame(nb, bg="#FFFFFF")
        nb.add(img_tab, text="  🖼  Ảnh PNG  ")
        self._img_canvas = tk.Canvas(img_tab, bg="#F1F5F9", highlightthickness=0)
        self._img_canvas.pack(fill="both", expand=True, padx=4, pady=4)

        # Tab 2: Code
        code_tab = tk.Frame(nb, bg="#1E293B")
        nb.add(code_tab, text="  📋  Code TikZ  ")
        self._preview = tk.Text(code_tab, font=("Consolas", 10), wrap="none",
                                bg="#1E293B", fg="#E2E8F0", relief="flat", bd=0,
                                state="disabled")
        psb = ttk.Scrollbar(code_tab, orient="vertical", command=self._preview.yview)
        self._preview.configure(yscrollcommand=psb.set)
        psb.pack(side="right", fill="y")
        self._preview.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        self._preview_nb = nb

    def _build_footer(self):
        """Pack hint + action bar ở ĐÁY cửa sổ TRƯỚC khi pack body — đảm
        bảo nút luôn hiện dù cửa sổ resize hoặc body expand=True."""
        # Hint phím tắt — đáy nhất
        tk.Label(self,
                 text="💡 F11 hoặc Double-click header = Phóng to  •  "
                      "Double-click hình = Mở & xem ngay  •  Esc = Đóng",
                 bg="#F8FAFC", fg="#64748B",
                 font=("Segoe UI", 8, "italic"),
                 ).pack(side="bottom", fill="x", pady=(0, 6))

        # Action bar — trên hint
        ab = tk.Frame(self, bg="#E2E8F0")
        ab.pack(side="bottom", fill="x", padx=10, pady=(4, 0))

        def _btn(parent, text, bg, hover_bg, cmd, primary=False):
            return tk.Button(
                parent, text=text,
                bg=bg, fg="white",
                activebackground=hover_bg, activeforeground="white",
                font=("Segoe UI", 10 if not primary else 11, "bold"),
                relief="flat", cursor="hand2",
                padx=10, pady=6, bd=0,
                command=cmd,
            )

        ab.grid_columnconfigure(50, weight=1)   # spacer ở giữa

        # NHÓM TRÁI (4 nút thao tác)
        _btn(ab, "  🚀  Nạp & Mở hình ngay  ", "#10B981", "#059669",
             self._on_load, primary=True).grid(row=0, column=1, padx=3, pady=4)
        _btn(ab, "  📋  Copy code  ", "#3B82F6", "#2563EB",
             self._on_copy, primary=True).grid(row=0, column=2, padx=3, pady=4)
        _btn(ab, "  ✏️  Sửa  ", "#7C3AED", "#6D28D9",
             self._on_edit_meta).grid(row=0, column=3, padx=3, pady=4)
        _btn(ab, "  🗑  Xoá  ", "#EF4444", "#DC2626",
             self._on_delete).grid(row=0, column=4, padx=3, pady=4)

        # NHÓM PHẢI (2 nút) — KHÔNG còn nút "Toàn màn hình",
        # user dùng nút 🗖 trên title bar Windows hoặc F11.
        _btn(ab, "  📁  Thư mục  ", "#0891B2", "#0E7490",
             self._on_open_folder).grid(row=0, column=98, padx=3, pady=4)
        _btn(ab, "  ✕  Đóng  ", "#94A3B8", "#64748B",
             self.destroy).grid(row=0, column=100, padx=3, pady=4)

        # Hint phím tắt
        tk.Label(self,
                 text="💡 F11 = Toàn màn hình  •  Esc = Thu nhỏ  •  Double-click hình = Mở & xem ngay",
                 bg="#F8FAFC", fg="#64748B",
                 font=("Segoe UI", 8, "italic"),
                 ).pack(side="bottom", pady=(0, 4))

    def _refresh_list(self):
        from services import figure_bank
        for item in self._tree.get_children():
            self._tree.delete(item)
        src = self._src_var.get()
        entries = figure_bank.list_entries(
            query=self._search_var.get(),
            source_filter="" if src == "all" else src,
        )
        for e in entries:
            tags_str = ", ".join(e.tags[:3])
            created = e.created_at[:10] if e.created_at else ""
            # Source emoji tag
            src_tag = {"ai": "🤖 AI", "manual": "✋ Manual",
                       "template": "📐 Mẫu", "imported": "📥 Import",
                       "nhch": "🗂 NHCH tự động",
                       "rendered": "💾 Render tự động"}
            src_label = src_tag.get(e.source, e.source)
            # Tag PNG
            png_mark = "🖼 " if e.has_png else ""
            self._tree.insert("", "end", iid=e.id,
                              values=(e.id, png_mark + e.title, src_label,
                                      tags_str, created))
        s = figure_bank.stats()
        png_str = f"  •  🖼 {s['with_png']} có PNG" if s['with_png'] else ""
        self._stats_lbl.config(text=f"Tổng: {s['total']} hình{png_str}")
        # Rebuild grid view (lazy — chỉ khi đang ở grid mode)
        if self._view_mode.get() == "grid":
            self._render_grid()
        # Clear preview
        self._clear_preview()

    # ── View toggle ──────────────────────────────────────────────────────

    def _switch_view(self):
        """Chuyển đổi giữa List view và Grid view."""
        mode = self._view_mode.get()
        if mode == "list":
            self._grid_container.pack_forget()
            self._list_container.pack(fill="both", expand=True)
        else:
            self._list_container.pack_forget()
            self._grid_container.pack(fill="both", expand=True)
            self._render_grid()

    def _render_grid(self):
        """Vẽ grid 3 cột với thumbnail cards."""
        from services import figure_bank, tikz_thumbnail

        # Clear cũ
        for w in self._grid_inner.winfo_children():
            w.destroy()
        self._grid_thumbs.clear()

        src = self._src_var.get()
        entries = figure_bank.list_entries(
            query=self._search_var.get(),
            source_filter="" if src == "all" else src,
        )

        if not entries:
            tk.Label(self._grid_inner,
                     text="(Không có hình nào — hãy lưu hình từ tab TikZ)",
                     bg="#F1F5F9", fg="#94A3B8",
                     font=("Segoe UI", 11, "italic"),
                     ).pack(pady=40)
            return

        cols = 3
        for i, e in enumerate(entries):
            row, col = divmod(i, cols)
            self._make_grid_card(self._grid_inner, e, row, col)

        # Configure grid weight cho responsive
        for c in range(cols):
            self._grid_inner.grid_columnconfigure(c, weight=1, uniform="g")

    def _make_grid_card(self, parent, entry, row: int, col: int):
        """Tạo 1 card thumbnail cho figure entry."""
        from services import tikz_thumbnail

        is_selected = (entry.id == self._grid_selected_fid)
        border = "#3B82F6" if is_selected else "#CBD5E1"
        card_bg = "#EFF6FF" if is_selected else "#FFFFFF"

        # Outer border
        outer = tk.Frame(parent, bg=border, bd=0)
        outer.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
        card = tk.Frame(outer, bg=card_bg, bd=0)
        card.pack(fill="both", expand=True, padx=2, pady=2)

        # Thumbnail (lazy — render nếu chưa có)
        png = entry.png_path()
        thumb_path = None
        try:
            if png and png.exists():
                # Có sẵn PNG full → resize
                thumb_path = tikz_thumbnail.get_from_png(png, code_hint=str(entry.id))
            else:
                # Render từ TikZ code (có thể tốn thời gian — nhưng đã được cache)
                from services import figure_bank
                code = figure_bank.get_tikz(entry.id)
                # Chỉ render nếu cache đã có (tránh block UI)
                thumb_path = tikz_thumbnail.get(code, render_if_missing=False)
        except Exception:
            thumb_path = None

        thumb_lbl = tk.Label(card, bg="#F8FAFC", relief="flat",
                              width=20, height=10)
        if thumb_path:
            try:
                from PIL import Image as PILImage, ImageTk
                pil = PILImage.open(thumb_path)
                tk_img = ImageTk.PhotoImage(pil)
                self._grid_thumbs.append(tk_img)   # giữ ref
                thumb_lbl.config(image=tk_img, width=tikz_thumbnail.THUMB_SIZE[0],
                                 height=tikz_thumbnail.THUMB_SIZE[1],
                                 text="")
            except Exception:
                thumb_lbl.config(text="(lỗi ảnh)", fg="#94A3B8")
        else:
            thumb_lbl.config(text="🎨\n(chưa render)", fg="#94A3B8",
                             font=("Segoe UI", 10))
        thumb_lbl.pack(padx=4, pady=4)

        # Title (truncate)
        title = entry.title if len(entry.title) <= 24 else entry.title[:22] + "…"
        tk.Label(card, text=title, bg=card_bg, fg="#0F2D52",
                 font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(fill="x", padx=6, pady=(0, 2))

        # Meta line
        src_emoji = {"ai": "🤖", "manual": "✋", "template": "📐",
                     "nhch": "🗂", "rendered": "💾"}.get(
            entry.source, "•",
        )
        date = entry.created_at[:10] if entry.created_at else ""
        tk.Label(
            card,
            text=f"{src_emoji}  {date}",
            bg=card_bg, fg="#64748B", font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", padx=6, pady=(0, 4))

        # Click → select; double-click → load
        def _on_click(_e, fid=entry.id):
            self._grid_selected_fid = fid
            # Update preview như khi chọn trong tree
            self._select_grid_entry(fid)
            # Re-render grid để highlight
            self._render_grid()

        def _on_dblclick(_e, fid=entry.id):
            self._grid_selected_fid = fid
            self._select_grid_entry(fid)
            self._on_load()

        for w in (card, thumb_lbl):
            w.bind("<Button-1>", _on_click)
            w.bind("<Double-Button-1>", _on_dblclick)
            w.configure(cursor="hand2")

    def _select_grid_entry(self, fid: str):
        """Khi user click 1 grid card — sync preview như tree select."""
        # Sync với tree (để các action button dùng selection từ tree)
        try:
            self._tree.selection_set(fid)
            self._tree.see(fid)
        except Exception:
            pass
        # Trigger preview update
        self._on_select_for_id(fid)

    def _on_select_for_id(self, fid: str):
        """Helper — update preview cho 1 fid cụ thể (dùng cả tree + grid)."""
        from services import figure_bank
        e = figure_bank.get(fid)
        if not e:
            return
        meta = f"ID {e.id}  •  {len(figure_bank.get_tikz(fid))} ký tự"
        self._preview_meta_lbl.config(text=meta)
        code = figure_bank.get_tikz(fid)
        self._preview.config(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.insert("1.0", code)
        self._preview.config(state="disabled")
        # Image update — same as _on_select
        self._update_preview_image(e)

    def _update_preview_image(self, entry):
        """Update tab Image preview cho 1 entry — share giữa tree + grid."""
        self._img_canvas.delete("all")
        self._tk_preview_img = None
        png = entry.png_path()
        if not (png and png.exists()):
            try:
                from pathlib import Path
                from services import tikz_cache, figure_bank
                code_str = figure_bank.get_tikz(entry.id)
                cached = tikz_cache.get(code_str)
                if cached and os.path.isfile(cached):
                    png = Path(cached)
            except Exception:
                pass
        if png and png.exists():
            try:
                from PIL import Image as PILImage, ImageTk
                pil = PILImage.open(png)
                self.update_idletasks()
                cw = self._img_canvas.winfo_width() or 600
                ch = self._img_canvas.winfo_height() or 400
                scale = min(cw / pil.width, ch / pil.height, 1.0)
                if scale < 1.0:
                    pil = pil.resize(
                        (int(pil.width * scale), int(pil.height * scale)),
                        resample=PILImage.LANCZOS,
                    )
                self._tk_preview_img = ImageTk.PhotoImage(pil)
                self._img_canvas.create_image(
                    cw // 2, ch // 2,
                    image=self._tk_preview_img, anchor="center",
                )
            except Exception as exc:
                self._img_canvas.create_text(
                    300, 100, text=f"Không tải được PNG:\n{exc}",
                    fill="#DC2626", font=("Segoe UI", 10),
                )
        else:
            self._img_canvas.create_text(
                300, 100,
                text="(Hình này chưa có ảnh PNG — chỉ có code .tex)\n"
                     "Bấm tab '📋 Code TikZ' để xem code",
                fill="#94A3B8", font=("Segoe UI", 11), justify="center",
            )

    def _clear_preview(self):
        self._preview.config(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.config(state="disabled")
        self._img_canvas.delete("all")
        self._tk_preview_img = None
        self._preview_meta_lbl.config(text="")

    def _on_select(self, _e=None):
        """Tree selection — delegate to shared `_on_select_for_id`."""
        sel = self._tree.selection()
        if not sel:
            return
        self._on_select_for_id(sel[0])

    def _on_edit_meta(self):
        """Cho phép user sửa title/description/tags của hình đã chọn."""
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Chọn hình",
                                "Hãy chọn 1 hình để sửa thông tin.",
                                parent=self)
            return
        from services import figure_bank
        e = figure_bank.get(sel[0])
        if not e:
            return
        from tkinter import simpledialog
        new_title = simpledialog.askstring(
            "Sửa tên", "Tên hình:", initialvalue=e.title, parent=self,
        )
        if new_title is None:
            return
        new_desc = simpledialog.askstring(
            "Sửa mô tả", "Mô tả:", initialvalue=e.description, parent=self,
        )
        new_tags_str = simpledialog.askstring(
            "Sửa tags", "Tags (cách bằng dấu phẩy):",
            initialvalue=", ".join(e.tags), parent=self,
        )
        new_tags = [t.strip() for t in (new_tags_str or "").split(",") if t.strip()]
        if figure_bank.update_metadata(e.id, title=new_title,
                                       description=new_desc, tags=new_tags):
            self._refresh_list()

    def _on_load(self):
        sel = self._tree.selection()
        fid = sel[0] if sel else getattr(self, "_grid_selected_fid", None)
        if not fid:
            messagebox.showinfo("Chọn hình", "Hãy chọn 1 hình trong danh sách.",
                                parent=self)
            return
        from services import figure_bank
        e = figure_bank.get(fid)
        if not e:
            return
        self.loaded_tikz = figure_bank.get_tikz(fid)
        self.loaded_title = e.title

        # Lấy file PNG đã render sẵn (từ figure_bank hoặc fallback tikz_cache)
        png_p = e.png_path()
        if png_p and png_p.is_file():
            self.loaded_png_path = str(png_p)
        else:
            try:
                from services import tikz_cache
                cached = tikz_cache.get(self.loaded_tikz)
                if cached and os.path.isfile(cached):
                    self.loaded_png_path = str(cached)
                else:
                    self.loaded_png_path = ""
            except Exception:
                self.loaded_png_path = ""
        self.destroy()

    def _on_copy(self):
        sel = self._tree.selection()
        if not sel:
            return
        from services import figure_bank
        code = figure_bank.get_tikz(sel[0])
        self.clipboard_clear()
        self.clipboard_append(code)
        messagebox.showinfo("Đã copy",
                            f"Đã copy code TikZ ({len(code)} ký tự) vào clipboard.",
                            parent=self)

    def _on_delete(self):
        sel = self._tree.selection()
        if not sel:
            return
        fid = sel[0]
        if not messagebox.askyesno(
            "Xoá hình",
            f"Bạn có chắc muốn xoá hình ID {fid}?\n(Xoá cả file .tex và .png)",
            parent=self,
        ):
            return
        from services import figure_bank
        if figure_bank.delete(fid):
            self._refresh_list()

    def _on_open_folder(self):
        from services import figure_bank
        folder = figure_bank.stats().get("dir", "")
        if not folder:
            return
        try:
            import os, sys, subprocess
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)


# ══════════════════════════════════════════════════════════════════════════
#  DIALOG: TEMPLATE PICKER — duyệt mẫu hình KB theo nhóm
# ══════════════════════════════════════════════════════════════════════════
#  Thay cho Combobox dài 88 entries — dùng Treeview phân nhóm theo folder KB:
#    01_plane_geometry → Tam giác / Tứ giác / Đường tròn / …
#    02_solid_geometry → Chóp / Lăng trụ / Khối tròn xoay
#    03_graphs / 04_tables / 05_charts / 06_misc
#  Click vào nhóm để mở; click vào template để xem code preview.

class _TemplatePickerDialog(tk.Toplevel):
    """Picker mẫu hình — duyệt theo nhóm, có search và preview code."""

    _GROUP_LABELS = {
        "01_plane_geometry": "📐 Hình học phẳng",
        "02_solid_geometry": "📦 Hình học không gian",
        "03_graphs":         "📈 Đồ thị hàm số",
        "04_tables":         "📊 Bảng biến thiên",
        "05_charts":         "📊 Biểu đồ",
        "06_misc":           "🔢 Trục số / Conic / Khác",
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.title("📚 Chọn mẫu hình TikZ")
        self.configure(bg="#F8FAFC")
        # KHÔNG dùng transient() — vì transient ẩn nút min/max trên Windows.
        # Chỉ dùng grab_set() để giữ tính modal (chặn tương tác parent).
        self.grab_set()

        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w, h = min(1000, sw - 80), min(640, sh - 100)
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.resizable(True, True)
        self.minsize(640, 420)

        # Bật min/max trên title bar (mặc định Toplevel có cả 3 nút).
        try:
            self.attributes("-toolwindow", False)
        except Exception:
            pass

        try:
            from ui import set_dialog_icon
            set_dialog_icon(self)
        except Exception:
            pass

        self.selected_name = ""   # output

        self._build()
        self._populate_tree()

        # Phím tắt
        self.bind("<F11>",    lambda _e: self._toggle_maximize())
        self.bind("<Escape>", lambda _e: self.destroy())

    def _toggle_maximize(self):
        """Bật/tắt phóng to (zoomed) — phụ trợ cho phím F11.
        Người dùng vẫn có thể bấm nút 🗖 trên title bar Windows."""
        import sys
        try:
            if sys.platform == "win32":
                self.state("zoomed" if self.state() != "zoomed" else "normal")
            else:
                cur = bool(self.attributes("-fullscreen"))
                self.attributes("-fullscreen", not cur)
        except Exception:
            pass

    def _build(self):
        # ══ THỨ TỰ PACK QUAN TRỌNG ═══════════════════════════════════════
        # Trên Tk, để các thanh ở DƯỚI luôn hiện dù body expand=True, ta
        # PHẢI pack chúng TRƯỚC body và dùng side="bottom".  Pack order:
        #   1. Header (top)
        #   2. Accent line (top)
        #   3. Search bar (top)
        #   4. Hint label    (BOTTOM — đáy nhất)
        #   5. Action bar    (BOTTOM — trên hint)
        #   6. Body          (cuối cùng, fill phần giữa)
        # ════════════════════════════════════════════════════════════════

        # ── 1. Header ──
        hdr = tk.Frame(self, bg="#0F2D52", height=56)
        hdr.pack(side="top", fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  📚  CHỌN MẪU HÌNH TỪ KHO",
                 bg="#0F2D52", fg="white",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=16, pady=12)
        self._count_lbl = tk.Label(hdr, text="", bg="#0F2D52", fg="#FCD34D",
                                    font=("Segoe UI", 11, "bold"))
        self._count_lbl.pack(side="right", padx=16, pady=12)
        # Double-click trên header để toggle maximize (UX bonus)
        for w in (hdr,):
            w.bind("<Double-1>", lambda _e: self._toggle_maximize())

        # ── 2. Accent line ──
        tk.Frame(self, bg="#0891B2", height=3).pack(side="top", fill="x")

        # ── 3. Search bar ──
        sb = tk.Frame(self, bg="#E2E8F0", height=50)
        sb.pack(side="top", fill="x")
        sb.pack_propagate(False)
        tk.Label(sb, text="🔍 Tìm mẫu:", bg="#E2E8F0",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=(12, 4), pady=10)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._populate_tree())
        ent = tk.Entry(sb, textvariable=self._search_var,
                       font=("Segoe UI", 11), relief="solid", bd=1, width=40)
        ent.pack(side="left", padx=(0, 12), pady=10, ipady=4)
        tk.Label(sb, text="(VD: \"chóp đều\", \"hình trụ\", \"đồ thị bậc 3\"…)",
                 bg="#E2E8F0", fg="#64748B",
                 font=("Segoe UI", 9, "italic")).pack(side="left")

        # ── 4 + 5. PACK FOOTER TRƯỚC BODY → luôn hiện dưới đáy ──
        self._build_footer()

        # ── 6. Body — split: tree (trái) + preview (phải) ──
        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(side="top", fill="both", expand=True, padx=10, pady=(8, 4))

        # TREE
        tree_f = tk.Frame(body, bg="#FFFFFF", bd=1, relief="solid")
        body.add(tree_f, weight=2)

        tk.Label(tree_f, text="Danh sách mẫu (theo nhóm)",
                 bg="#1E293B", fg="white", font=("Segoe UI", 10, "bold"),
                 anchor="w", padx=10, pady=6).pack(fill="x")

        style = ttk.Style()
        style.configure("Picker.Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Picker.Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self._tree = ttk.Treeview(tree_f, show="tree", style="Picker.Treeview")
        vsb = ttk.Scrollbar(tree_f, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(side="left", fill="both", expand=True)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", lambda e: self._on_choose())

        # PREVIEW
        prev_f = tk.Frame(body, bg="#F8FAFC", bd=1, relief="solid")
        body.add(prev_f, weight=3)

        # Header
        prev_hdr = tk.Frame(prev_f, bg="#1E293B")
        prev_hdr.pack(fill="x")
        tk.Label(prev_hdr, text="Xem trước",
                 bg="#1E293B", fg="white", font=("Segoe UI", 10, "bold"),
                 anchor="w", padx=10, pady=6).pack(side="left")
        self._prev_meta_lbl = tk.Label(
            prev_hdr, text="", bg="#1E293B", fg="#94A3B8",
            font=("Segoe UI", 9), anchor="e",
        )
        self._prev_meta_lbl.pack(side="right", padx=10, pady=6)

        # Notes box (highlight metadata if available)
        self._notes_lbl = tk.Label(
            prev_f, text="", bg="#FEF3C7", fg="#854D0E",
            font=("Segoe UI", 10, "italic"), anchor="w",
            justify="left", padx=10, pady=6, wraplength=560,
        )

        # ── Notebook: Ảnh PNG + Code TikZ ──
        nb = ttk.Notebook(prev_f)
        nb.pack(fill="both", expand=True, padx=4, pady=4)
        self._preview_nb = nb

        # Tab 1: Ảnh PNG (thumbnail/full render) + zoom toolbar + scrollbars
        img_tab = tk.Frame(nb, bg="#FFFFFF")
        nb.add(img_tab, text="  🖼  Ảnh PNG  ")

        # ── Zoom toolbar ──
        zoom_bar = tk.Frame(img_tab, bg="#E2E8F0", height=34)
        zoom_bar.pack(side="top", fill="x")
        zoom_bar.pack_propagate(False)

        def _zbtn(text, cmd, tip=""):
            b = tk.Button(zoom_bar, text=text, command=cmd,
                          font=("Segoe UI", 10, "bold"),
                          bg="#FFFFFF", fg="#1E293B",
                          activebackground="#CBD5E1",
                          relief="solid", bd=1, width=3, cursor="hand2")
            b.pack(side="left", padx=(6, 2), pady=4)
            return b

        _zbtn("−", lambda: self._zoom_out())
        _zbtn("Fit", lambda: self._zoom_fit())
        _zbtn("+", lambda: self._zoom_in())
        self._zoom_lbl = tk.Label(zoom_bar, text="Fit",
                                   bg="#E2E8F0", fg="#0F2D52",
                                   font=("Segoe UI", 10, "bold"), width=7)
        self._zoom_lbl.pack(side="left", padx=(8, 4))
        tk.Label(zoom_bar,
                 text="(Ctrl+Wheel = zoom · Kéo chuột = di chuyển)",
                 bg="#E2E8F0", fg="#64748B",
                 font=("Segoe UI", 8, "italic")).pack(side="left", padx=8)

        # ── Canvas + scrollbars ──
        cvs_frame = tk.Frame(img_tab, bg="#FFFFFF")
        cvs_frame.pack(side="top", fill="both", expand=True, padx=4, pady=4)

        self._img_canvas = tk.Canvas(cvs_frame, bg="#F1F5F9",
                                      highlightthickness=0)
        self._img_vsb = ttk.Scrollbar(cvs_frame, orient="vertical",
                                       command=self._img_canvas.yview)
        self._img_hsb = ttk.Scrollbar(cvs_frame, orient="horizontal",
                                       command=self._img_canvas.xview)
        self._img_canvas.configure(yscrollcommand=self._img_vsb.set,
                                    xscrollcommand=self._img_hsb.set)
        self._img_canvas.grid(row=0, column=0, sticky="nsew")
        self._img_vsb.grid(row=0, column=1, sticky="ns")
        self._img_hsb.grid(row=1, column=0, sticky="ew")
        cvs_frame.rowconfigure(0, weight=1)
        cvs_frame.columnconfigure(0, weight=1)

        self._tk_preview_img = None       # giữ ref ảnh hiện tại
        self._preview_pil_orig = None     # PIL gốc (chưa resize)
        self._preview_zoom: float | None = None   # None = fit, else absolute scale

        # Bindings: wheel zoom + drag-pan + resize
        self._img_canvas.bind("<MouseWheel>", self._on_canvas_wheel)
        self._img_canvas.bind("<Button-4>",  self._on_canvas_wheel)  # Linux up
        self._img_canvas.bind("<Button-5>",  self._on_canvas_wheel)  # Linux down
        self._img_canvas.bind("<ButtonPress-1>",   self._on_pan_start)
        self._img_canvas.bind("<B1-Motion>",       self._on_pan_move)
        self._img_canvas.bind("<ButtonPress-2>",   self._on_pan_start)  # middle
        self._img_canvas.bind("<B2-Motion>",       self._on_pan_move)
        self._img_canvas.bind("<Configure>",       self._on_canvas_resize)

        # Tab 2: Code TikZ
        code_tab = tk.Frame(nb, bg="#1E293B")
        nb.add(code_tab, text="  📋  Code TikZ  ")
        self._code_text = tk.Text(code_tab, font=("Consolas", 10), wrap="none",
                                  bg="#1E293B", fg="#E2E8F0", relief="flat", bd=0,
                                  state="disabled")
        cvsb = ttk.Scrollbar(code_tab, orient="vertical", command=self._code_text.yview)
        chsb = ttk.Scrollbar(code_tab, orient="horizontal", command=self._code_text.xview)
        self._code_text.configure(yscrollcommand=cvsb.set, xscrollcommand=chsb.set)
        cvsb.pack(side="right", fill="y")
        chsb.pack(side="bottom", fill="x")
        self._code_text.pack(side="left", fill="both", expand=True)

    def _build_footer(self):
        """Pack footer (hint + action bar) ở ĐÁY cửa sổ, TRƯỚC body.
        Đảm bảo nút luôn hiện dù body expand=True hoặc cửa sổ resize."""
        # Hint phím tắt — đáy NHẤT (pack đầu tiên với side=bottom)
        tk.Label(self,
                 text="💡 F11 = Phóng to dialog  •  Double-click mẫu = Chọn nhanh  •  "
                      "Ctrl+Wheel = Zoom ảnh  •  Kéo chuột = Di chuyển  •  Esc = Đóng",
                 bg="#F8FAFC", fg="#64748B",
                 font=("Segoe UI", 8, "italic"),
                 ).pack(side="bottom", fill="x", pady=(0, 6))

        # Action bar — TRÊN hint, dưới body
        ab = tk.Frame(self, bg="#E2E8F0")
        ab.pack(side="bottom", fill="x", padx=10, pady=(4, 0))

        def _btn(parent, text, bg, hover_bg, cmd, primary=False):
            return tk.Button(
                parent, text=text,
                bg=bg, fg="white",
                activebackground=hover_bg, activeforeground="white",
                font=("Segoe UI", 10 if not primary else 11, "bold"),
                relief="flat", cursor="hand2",
                padx=10, pady=6, bd=0,
                command=cmd,
            )

        # 3 nút trái + 1 nút phải (đóng) — KHÔNG còn nút "Toàn màn hình"
        # vì user dùng nút 🗖 trên title bar Windows hoặc F11.
        ab.grid_columnconfigure(50, weight=1)   # spacer co giãn ở giữa

        _btn(ab, "  ✅  Chọn mẫu này  ", "#10B981", "#059669",
             self._on_choose, primary=True).grid(row=0, column=1, padx=3, pady=4)
        _btn(ab, "  📋  Copy code  ", "#3B82F6", "#2563EB",
             self._on_copy, primary=True).grid(row=0, column=2, padx=3, pady=4)
        _btn(ab, "  📁  Thư mục KB  ", "#0891B2", "#0E7490",
             self._on_open_kb).grid(row=0, column=3, padx=3, pady=4)

        _btn(ab, "  ✕  Đóng  ", "#94A3B8", "#64748B",
             self.destroy).grid(row=0, column=100, padx=3, pady=4)

    def _populate_tree(self):
        """Group templates by folder, optionally filter by search query."""
        from services import tikz_kb
        from pathlib import Path
        for it in self._tree.get_children():
            self._tree.delete(it)

        q = self._search_var.get().lower().strip()
        # Group templates by parent folder name
        groups: dict[str, list] = {}
        all_tpls = tikz_kb.all_templates()
        for tpl in all_tpls:
            if q:
                hay = (tpl.name + " " + " ".join(tpl.tags) + " "
                       + " ".join(tpl.keywords) + " " + tpl.notes).lower()
                if q not in hay:
                    continue
            folder = Path(tpl.source).parent.name if tpl.source else "_misc"
            groups.setdefault(folder, []).append(tpl)

        # Add fallback hardcoded templates (those not in KB)
        kb_names = {t.name for t in all_tpls}
        ui_only = [n for n in _TEMPLATES.keys() if n not in kb_names and n != "Trống (tự viết)"]
        if ui_only:
            for n in ui_only:
                if q and q not in n.lower():
                    continue
                groups.setdefault("_fallback", []).append(
                    type("T", (), {"name": n, "code": _TEMPLATES.get(n, ""),
                                   "tags": [], "keywords": [], "notes": "",
                                   "source": ""})()
                )

        # Insert into tree — sorted by group label
        order = ["01_plane_geometry", "02_solid_geometry", "03_graphs",
                 "04_tables", "05_charts", "06_misc", "_fallback"]
        total = 0
        for folder in order + sorted(g for g in groups if g not in order):
            tpls = groups.get(folder)
            if not tpls:
                continue
            label = self._GROUP_LABELS.get(
                folder,
                folder.replace("_", " ").title() if folder != "_fallback"
                else "📦 Templates cũ (fallback)"
            )
            gid = self._tree.insert("", "end", text=f"{label}  ({len(tpls)})",
                                     open=bool(q))   # mở khi search
            for tpl in sorted(tpls, key=lambda x: x.name):
                self._tree.insert(gid, "end", iid=tpl.name, text=tpl.name)
                total += 1

        self._count_lbl.config(text=f"Hiện: {total} mẫu")

    def _on_select(self, _e=None):
        sel = self._tree.selection()
        if not sel:
            return
        name = sel[0]
        # Skip if it's a group node
        if name.startswith("I001") or self._tree.parent(name) == "":
            return
        from services import tikz_kb
        tpl = tikz_kb.get_template(name)
        # Code
        if tpl:
            code = tpl.code
            self._notes_lbl.config(text=tpl.notes if tpl.notes else "")
            if tpl.notes:
                # Pack ngay TRƯỚC notebook (chứ không phải code_text.master nữa)
                self._notes_lbl.pack(fill="x", before=self._preview_nb, padx=4)
            else:
                self._notes_lbl.pack_forget()
            self._prev_meta_lbl.config(
                text=f"{len(code)} ký tự" + (
                    f"  •  tags: {', '.join(tpl.tags[:3])}" if tpl.tags else ""
                ),
            )
        else:
            code = _TEMPLATES.get(name, "")
            self._notes_lbl.pack_forget()
            self._prev_meta_lbl.config(text=f"{len(code)} ký tự")

        self._code_text.config(state="normal")
        self._code_text.delete("1.0", "end")
        self._code_text.insert("1.0", code)
        self._code_text.config(state="disabled")

        # ── Image preview: thumbnail nếu cache có sẵn, render bg nếu chưa ──
        self._update_image_preview(code)

    def _update_image_preview(self, code: str):
        """Load thumbnail (cache-only) hoặc trigger background render."""
        self._img_canvas.delete("all")
        self._tk_preview_img = None
        self._preview_pil_orig = None
        self._preview_zoom = None  # reset Fit cho mẫu mới
        # reset scrollbars về (0,0)
        try:
            self._img_canvas.configure(scrollregion=(0, 0, 0, 0))
        except Exception:
            pass

        if not code or not code.strip():
            self._img_canvas.create_text(
                300, 100, text="(Chưa có code)",
                fill="#94A3B8", font=("Segoe UI", 11),
            )
            return

        try:
            from services import tikz_thumbnail
            # Lần đầu: thử cache (không block)
            path = tikz_thumbnail.get(code, render_if_missing=False)
            if path:
                self._show_preview_image(path)
                return
            # Chưa có cache → hiện hint + trigger background render
            self._img_canvas.create_text(
                300, 80,
                text="🎨  Đang render thumbnail...\n(lần đầu tốn vài giây)",
                fill="#64748B", font=("Segoe UI", 11), justify="center",
            )

            import threading
            def _bg():
                try:
                    rendered = tikz_thumbnail.get(code, render_if_missing=True)
                    if rendered:
                        # Quay về main thread để update UI
                        self.after(0, lambda p=rendered: self._show_preview_image(p))
                    else:
                        self.after(0, lambda: self._img_canvas.itemconfigure(
                            "all",  # noqa — placeholder, will be replaced
                        ) or self._show_render_failed())
                except Exception:
                    self.after(0, self._show_render_failed)

            threading.Thread(target=_bg, daemon=True, name="ThumbRender").start()
        except Exception as e:
            self._img_canvas.create_text(
                300, 80, text=f"(Không tải được preview: {e})",
                fill="#DC2626", font=("Segoe UI", 10),
            )

    def _show_preview_image(self, png_path: str):
        """Load PNG vào cache + render lần đầu (zoom = Fit)."""
        try:
            from PIL import Image as PILImage
            pil = PILImage.open(png_path)
            pil.load()  # đọc data ngay, file handle có thể đóng
            self._preview_pil_orig = pil
            self._preview_zoom = None  # mặc định Fit khi load mới
            self._redraw_preview()
        except Exception as e:
            self._preview_pil_orig = None
            self._tk_preview_img = None
            self._img_canvas.delete("all")
            self._img_canvas.create_text(
                300, 80, text=f"(Lỗi load ảnh: {e})",
                fill="#DC2626", font=("Segoe UI", 10),
            )

    # ── Zoom/Pan helpers ─────────────────────────────────────────────────
    _ZOOM_STEP = 1.25
    _ZOOM_MIN  = 0.10
    _ZOOM_MAX  = 8.0

    def _current_effective_scale(self) -> float:
        """Scale đang áp dụng (kể cả khi đang ở chế độ Fit)."""
        if self._preview_zoom is not None:
            return self._preview_zoom
        return self._compute_fit_scale()

    def _compute_fit_scale(self) -> float:
        if self._preview_pil_orig is None:
            return 1.0
        cw = max(1, self._img_canvas.winfo_width() or 600)
        ch = max(1, self._img_canvas.winfo_height() or 400)
        pil = self._preview_pil_orig
        return min(cw / pil.width, ch / pil.height, 1.0)

    def _redraw_preview(self):
        """Vẽ lại ảnh trên canvas theo zoom hiện tại + cập nhật scrollregion."""
        from PIL import Image as PILImage, ImageTk
        if self._preview_pil_orig is None:
            return
        pil = self._preview_pil_orig
        cw = max(1, self._img_canvas.winfo_width() or 600)
        ch = max(1, self._img_canvas.winfo_height() or 400)

        scale = self._current_effective_scale()
        new_w = max(1, int(pil.width * scale))
        new_h = max(1, int(pil.height * scale))

        if abs(scale - 1.0) < 1e-6:
            display = pil
        else:
            display = pil.resize((new_w, new_h), resample=PILImage.LANCZOS)
        self._tk_preview_img = ImageTk.PhotoImage(display)

        self._img_canvas.delete("all")
        if new_w <= cw and new_h <= ch:
            # Ảnh nhỏ hơn canvas → căn giữa, không cần scroll
            self._img_canvas.create_image(
                cw // 2, ch // 2,
                image=self._tk_preview_img, anchor="center",
            )
            self._img_canvas.configure(scrollregion=(0, 0, cw, ch))
        else:
            # Ảnh lớn hơn → đặt ở (0,0), bật scroll
            self._img_canvas.create_image(
                0, 0, image=self._tk_preview_img, anchor="nw",
            )
            self._img_canvas.configure(scrollregion=(0, 0, new_w, new_h))

        # Cập nhật label
        if self._preview_zoom is None:
            self._zoom_lbl.config(text=f"Fit ({int(scale * 100)}%)")
        else:
            self._zoom_lbl.config(text=f"{int(self._preview_zoom * 100)}%")

    def _zoom_in(self):
        if self._preview_pil_orig is None:
            return
        cur = self._current_effective_scale()
        new = min(self._ZOOM_MAX, cur * self._ZOOM_STEP)
        self._preview_zoom = new
        self._redraw_preview()

    def _zoom_out(self):
        if self._preview_pil_orig is None:
            return
        cur = self._current_effective_scale()
        new = max(self._ZOOM_MIN, cur / self._ZOOM_STEP)
        self._preview_zoom = new
        self._redraw_preview()

    def _zoom_fit(self):
        if self._preview_pil_orig is None:
            return
        self._preview_zoom = None
        self._redraw_preview()

    def _on_canvas_wheel(self, e):
        # Ctrl+Wheel = zoom; wheel thường = scroll dọc nếu có scrollregion
        ctrl_held = bool(e.state & 0x4)  # 0x4 = Control mask trên hầu hết platform
        # delta dương = lên/zoom-in trên Windows; Linux dùng Button-4/5
        if hasattr(e, "delta") and e.delta:
            up = e.delta > 0
        else:
            up = (getattr(e, "num", 0) == 4)
        if ctrl_held:
            (self._zoom_in if up else self._zoom_out)()
            return "break"
        # Plain wheel: nếu ảnh lớn hơn canvas → scroll dọc
        self._img_canvas.yview_scroll(-1 if up else 1, "units")
        return "break"

    def _on_pan_start(self, e):
        # Chỉ pan khi ảnh lớn hơn canvas (có scrollregion thực)
        if self._preview_pil_orig is None:
            return
        self._img_canvas.scan_mark(e.x, e.y)

    def _on_pan_move(self, e):
        if self._preview_pil_orig is None:
            return
        self._img_canvas.scan_dragto(e.x, e.y, gain=1)

    def _on_canvas_resize(self, _e):
        # Khi user resize dialog & đang ở Fit → vẽ lại để khớp size mới
        if self._preview_zoom is None and self._preview_pil_orig is not None:
            self._redraw_preview()

    def _show_render_failed(self):
        """Hiển thị message khi render fail."""
        self._preview_pil_orig = None
        self._tk_preview_img = None
        self._img_canvas.delete("all")
        self._img_canvas.create_text(
            300, 80,
            text="⚠ Không render được thumbnail\n"
                 "(LaTeX engine chưa cài? hoặc code có lỗi syntax)\n\n"
                 "Bấm tab '📋 Code TikZ' để xem code",
            fill="#DC2626", font=("Segoe UI", 10), justify="center",
        )

    def _on_choose(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Chọn mẫu",
                                "Hãy chọn 1 mẫu (không phải nhóm) trước.",
                                parent=self)
            return
        name = sel[0]
        if self._tree.parent(name) == "":
            # Group node — không thể chọn
            messagebox.showinfo("Chọn mẫu",
                                "Đây là nhóm. Hãy mở nhóm và chọn mẫu cụ thể.",
                                parent=self)
            return
        self.selected_name = name
        self.destroy()

    def _on_copy(self):
        sel = self._tree.selection()
        if not sel:
            return
        name = sel[0]
        if self._tree.parent(name) == "":
            return
        from services import tikz_kb
        tpl = tikz_kb.get_template(name)
        code = tpl.code if tpl else _TEMPLATES.get(name, "")
        if code:
            self.clipboard_clear()
            self.clipboard_append(code)
            messagebox.showinfo(
                "Đã copy",
                f"Đã copy code TikZ ({len(code)} ký tự) vào clipboard.",
                parent=self,
            )

    def _on_open_kb(self):
        from services import tikz_kb
        folder = str(tikz_kb._kb_dir())
        try:
            import os, sys, subprocess
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)
