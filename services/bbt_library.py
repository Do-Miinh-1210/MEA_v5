"""
services/bbt_library.py — Thư viện mẫu Bảng Biến Thiên (tkz-tab).

MỤC ĐÍCH:
- Cung cấp các TEMPLATE BBT chuẩn mực cho từng dạng hàm phổ biến.
- AI có thể tham khảo / copy-and-customize khi sinh đề có liên quan đến hàm số.
- Mọi template đều đã bọc trong `\\begin{tikzpicture}...\\end{tikzpicture}`,
  sẵn sàng render bởi tikz_pipeline.

CÁCH DÙNG:
    from services.bbt_library import get_template, list_templates, describe_templates
    tpl = get_template("quadratic_min")        # lấy template thô
    text = describe_templates()                # liệt kê cho prompt AI

TRIẾT LÝ:
- Mỗi template là 1 STRING đầy đủ — KHÔNG có placeholder. AI sẽ COPY và EDIT
  số liệu cụ thể (nghiệm, giá trị cực trị…) theo bài toán.
- Ký hiệu chuẩn: `+`, `-`, `0`, `\\parallel` (không xác định), `\\infty`.
- Tất cả nội dung toán trong `$...$` để tkz-tab render LaTeX.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# ══════════════════════════════════════════════════════════════════════════════
#  TEMPLATE CỤ THỂ CHO TỪNG DẠNG HÀM
# ══════════════════════════════════════════════════════════════════════════════

# ── Hàm bậc 2 ─────────────────────────────────────────────────────────────────

_BBT_QUADRATIC_MIN = r"""\begin{tikzpicture}
% BBT hàm bậc 2 có cực tiểu tại x = x_0 (vd y = a(x-x_0)^2 + y_0, a > 0)
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$-\infty$, $x_0$, $+\infty$}
\tkzTabLine{, -, 0, +, }
\tkzTabVar{+/$+\infty$, -/$y_0$, +/$+\infty$}
\end{tikzpicture}"""

_BBT_QUADRATIC_MAX = r"""\begin{tikzpicture}
% BBT hàm bậc 2 có cực đại tại x = x_0 (vd y = a(x-x_0)^2 + y_0, a < 0)
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$-\infty$, $x_0$, $+\infty$}
\tkzTabLine{, +, 0, -, }
\tkzTabVar{-/$-\infty$, +/$y_0$, -/$-\infty$}
\end{tikzpicture}"""

# ── Hàm bậc 3 ─────────────────────────────────────────────────────────────────

_BBT_CUBIC_TWO_EXTREMA_POS = r"""\begin{tikzpicture}
% BBT hàm bậc 3 có 2 cực trị, hệ số a > 0: CĐ tại x_1, CT tại x_2 (x_1 < x_2)
\tkzTabInit[lgt=2, espcl=2.5]{$x$/1, $y'$/1, $y$/2}%
{$-\infty$, $x_1$, $x_2$, $+\infty$}
\tkzTabLine{, +, 0, -, 0, +, }
\tkzTabVar{-/$-\infty$, +/$y_{CD}$, -/$y_{CT}$, +/$+\infty$}
\end{tikzpicture}"""

_BBT_CUBIC_TWO_EXTREMA_NEG = r"""\begin{tikzpicture}
% BBT hàm bậc 3 có 2 cực trị, hệ số a < 0: CT tại x_1, CĐ tại x_2 (x_1 < x_2)
\tkzTabInit[lgt=2, espcl=2.5]{$x$/1, $y'$/1, $y$/2}%
{$-\infty$, $x_1$, $x_2$, $+\infty$}
\tkzTabLine{, -, 0, +, 0, -, }
\tkzTabVar{+/$+\infty$, -/$y_{CT}$, +/$y_{CD}$, -/$-\infty$}
\end{tikzpicture}"""

_BBT_CUBIC_NO_EXTREMA_POS = r"""\begin{tikzpicture}
% BBT hàm bậc 3 không có cực trị, đơn điệu tăng (a > 0, y' >= 0 mọi x)
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$-\infty$, $+\infty$}
\tkzTabLine{, +, }
\tkzTabVar{-/$-\infty$, +/$+\infty$}
\end{tikzpicture}"""

_BBT_CUBIC_NO_EXTREMA_NEG = r"""\begin{tikzpicture}
% BBT hàm bậc 3 không có cực trị, đơn điệu giảm (a < 0, y' <= 0 mọi x)
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$-\infty$, $+\infty$}
\tkzTabLine{, -, }
\tkzTabVar{+/$+\infty$, -/$-\infty$}
\end{tikzpicture}"""

# ── Hàm bậc 4 trùng phương ────────────────────────────────────────────────────

_BBT_QUARTIC_W_SHAPE = r"""\begin{tikzpicture}
% BBT hàm bậc 4 trùng phương y = ax^4 + bx^2 + c, hình chữ W (a > 0, b < 0)
% 3 cực trị: CT tại x = -x_0, CĐ tại x = 0, CT tại x = x_0
\tkzTabInit[lgt=2, espcl=2]{$x$/1, $y'$/1, $y$/2}%
{$-\infty$, $-x_0$, $0$, $x_0$, $+\infty$}
\tkzTabLine{, -, 0, +, 0, -, 0, +, }
\tkzTabVar{+/$+\infty$, -/$y_{CT}$, +/$y_{CD}$, -/$y_{CT}$, +/$+\infty$}
\end{tikzpicture}"""

_BBT_QUARTIC_M_SHAPE = r"""\begin{tikzpicture}
% BBT hàm bậc 4 trùng phương y = ax^4 + bx^2 + c, hình chữ M (a < 0, b > 0)
\tkzTabInit[lgt=2, espcl=2]{$x$/1, $y'$/1, $y$/2}%
{$-\infty$, $-x_0$, $0$, $x_0$, $+\infty$}
\tkzTabLine{, +, 0, -, 0, +, 0, -, }
\tkzTabVar{-/$-\infty$, +/$y_{CD}$, -/$y_{CT}$, +/$y_{CD}$, -/$-\infty$}
\end{tikzpicture}"""

_BBT_QUARTIC_U_SHAPE = r"""\begin{tikzpicture}
% BBT hàm bậc 4 trùng phương y = ax^4 + bx^2 + c (a > 0, b >= 0) — chỉ 1 cực trị tại x=0
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$-\infty$, $0$, $+\infty$}
\tkzTabLine{, -, 0, +, }
\tkzTabVar{+/$+\infty$, -/$c$, +/$+\infty$}
\end{tikzpicture}"""

# ── Hàm phân thức y = (ax+b)/(cx+d) — 1 TCĐ + 1 TCN ──────────────────────────

_BBT_FRAC_11_POS = r"""\begin{tikzpicture}
% BBT hàm phân thức y = (ax+b)/(cx+d), ad-bc > 0 — đồng biến trên từng khoảng
% TCĐ: x = -d/c; TCN: y = a/c
\tkzTabInit[lgt=2, espcl=2.5]{$x$/1, $y'$/1, $y$/2}%
{$-\infty$, $-\frac{d}{c}$, $+\infty$}
\tkzTabLine{, +, d, +, }
\tkzTabVar{-/$\frac{a}{c}$, +D+/$+\infty$/$-\infty$, -/$\frac{a}{c}$}
\end{tikzpicture}"""

_BBT_FRAC_11_NEG = r"""\begin{tikzpicture}
% BBT hàm phân thức y = (ax+b)/(cx+d), ad-bc < 0 — nghịch biến trên từng khoảng
\tkzTabInit[lgt=2, espcl=2.5]{$x$/1, $y'$/1, $y$/2}%
{$-\infty$, $-\frac{d}{c}$, $+\infty$}
\tkzTabLine{, -, d, -, }
\tkzTabVar{+/$\frac{a}{c}$, -D+/$-\infty$/$+\infty$, +/$\frac{a}{c}$}
\end{tikzpicture}"""

# ── Hàm phân thức bậc 2/bậc 1 — có TC xiên ───────────────────────────────────

_BBT_FRAC_21 = r"""\begin{tikzpicture}
% BBT hàm phân thức y = (ax^2+bx+c)/(dx+e), có 2 cực trị và 1 TCĐ
% TCĐ: x = -e/d; TC xiên: y = (a/d)x + ...
% x_1 < -e/d < x_2 (CĐ và CT 2 bên TCĐ)
\tkzTabInit[lgt=2, espcl=2]{$x$/1, $y'$/1, $y$/2}%
{$-\infty$, $x_1$, $-\frac{e}{d}$, $x_2$, $+\infty$}
\tkzTabLine{, +, 0, -, d, -, 0, +, }
\tkzTabVar{-/$-\infty$, +/$y_{CD}$, -D-/$-\infty$/$-\infty$, +/$y_{CT}$, +/$+\infty$}
\end{tikzpicture}"""

# ── Hàm mũ và log ─────────────────────────────────────────────────────────────

_BBT_EXP_INCREASING = r"""\begin{tikzpicture}
% BBT hàm mũ y = a^x với a > 1 — đồng biến trên R
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$-\infty$, $+\infty$}
\tkzTabLine{, +, }
\tkzTabVar{-/$0^+$, +/$+\infty$}
\end{tikzpicture}"""

_BBT_EXP_DECREASING = r"""\begin{tikzpicture}
% BBT hàm mũ y = a^x với 0 < a < 1 — nghịch biến trên R
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$-\infty$, $+\infty$}
\tkzTabLine{, -, }
\tkzTabVar{+/$+\infty$, -/$0^+$}
\end{tikzpicture}"""

_BBT_LOG_INCREASING = r"""\begin{tikzpicture}
% BBT hàm log y = log_a(x) với a > 1 — đồng biến trên (0, +inf)
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$0$, $+\infty$}
\tkzTabLine{, +, }
\tkzTabVar{-/$-\infty$, +/$+\infty$}
\end{tikzpicture}"""

_BBT_LOG_DECREASING = r"""\begin{tikzpicture}
% BBT hàm log y = log_a(x) với 0 < a < 1 — nghịch biến trên (0, +inf)
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$0$, $+\infty$}
\tkzTabLine{, -, }
\tkzTabVar{+/$+\infty$, -/$-\infty$}
\end{tikzpicture}"""

# ── Hàm chứa căn ──────────────────────────────────────────────────────────────

_BBT_SQRT_SIMPLE = r"""\begin{tikzpicture}
% BBT hàm y = sqrt(x - a) — TXĐ: [a, +inf), đồng biến trên TXĐ
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$a$, $+\infty$}
\tkzTabLine{, +, }
\tkzTabVar{-/$0$, +/$+\infty$}
\end{tikzpicture}"""

_BBT_SQRT_PARABOLIC = r"""\begin{tikzpicture}
% BBT hàm y = sqrt(-x^2 + ax + b) — TXĐ là đoạn [x_1, x_2], có 1 cực đại
\tkzTabInit[lgt=2, espcl=2.5]{$x$/1, $y'$/1, $y$/2}%
{$x_1$, $x_0$, $x_2$}
\tkzTabLine{, +, 0, -, }
\tkzTabVar{-/$0$, +/$y_{max}$, -/$0$}
\end{tikzpicture}"""

# ── Hàm gián đoạn ─────────────────────────────────────────────────────────────

_BBT_DISCONTINUOUS = r"""\begin{tikzpicture}
% BBT hàm có điểm gián đoạn tại x = x_0 (không xác định)
% Ký hiệu `d` = chấm đứt (discontinuity)
\tkzTabInit[lgt=2, espcl=2.5]{$x$/1, $y'$/1, $y$/2}%
{$-\infty$, $x_0$, $+\infty$}
\tkzTabLine{, +, d, -, }
\tkzTabVar{-/$y_1$, +D-/$y_2$/$y_3$, -/$y_4$}
\end{tikzpicture}"""

# ── Xét dấu đơn giản (chỉ bảng xét dấu, không kèm BBT) ──────────────────────

_SIGN_QUADRATIC = r"""\begin{tikzpicture}
% Bảng xét dấu tam thức bậc 2 f(x) = ax^2 + bx + c có 2 nghiệm x_1 < x_2, a > 0
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $f(x)$/1}{$-\infty$, $x_1$, $x_2$, $+\infty$}
\tkzTabLine{, +, 0, -, 0, +, }
\end{tikzpicture}"""

_SIGN_LINEAR = r"""\begin{tikzpicture}
% Bảng xét dấu nhị thức f(x) = ax + b có nghiệm x = -b/a, a > 0
\tkzTabInit[lgt=2, espcl=3]{$x$/1, $f(x)$/1}{$-\infty$, $-\frac{b}{a}$, $+\infty$}
\tkzTabLine{, -, 0, +, }
\end{tikzpicture}"""


# ══════════════════════════════════════════════════════════════════════════════
#  CATALOG — map tên → (mô tả, template code)
# ══════════════════════════════════════════════════════════════════════════════

_CATALOG: Dict[str, Tuple[str, str]] = {
    # Bậc 2
    "quadratic_min": (
        "Hàm bậc 2 có cực tiểu (y=a(x-x_0)^2+y_0, a>0)",
        _BBT_QUADRATIC_MIN,
    ),
    "quadratic_max": (
        "Hàm bậc 2 có cực đại (a<0)",
        _BBT_QUADRATIC_MAX,
    ),
    # Bậc 3
    "cubic_two_extrema_pos": (
        "Hàm bậc 3 có 2 cực trị, a>0 (CĐ trước, CT sau)",
        _BBT_CUBIC_TWO_EXTREMA_POS,
    ),
    "cubic_two_extrema_neg": (
        "Hàm bậc 3 có 2 cực trị, a<0 (CT trước, CĐ sau)",
        _BBT_CUBIC_TWO_EXTREMA_NEG,
    ),
    "cubic_no_extrema_pos": (
        "Hàm bậc 3 đơn điệu tăng, không cực trị (a>0)",
        _BBT_CUBIC_NO_EXTREMA_POS,
    ),
    "cubic_no_extrema_neg": (
        "Hàm bậc 3 đơn điệu giảm, không cực trị (a<0)",
        _BBT_CUBIC_NO_EXTREMA_NEG,
    ),
    # Bậc 4 trùng phương
    "quartic_w": (
        "Hàm bậc 4 trùng phương hình chữ W (3 cực trị, a>0, b<0)",
        _BBT_QUARTIC_W_SHAPE,
    ),
    "quartic_m": (
        "Hàm bậc 4 trùng phương hình chữ M (3 cực trị, a<0, b>0)",
        _BBT_QUARTIC_M_SHAPE,
    ),
    "quartic_u": (
        "Hàm bậc 4 trùng phương hình chữ U (1 cực trị, a>0, b>=0)",
        _BBT_QUARTIC_U_SHAPE,
    ),
    # Phân thức
    "frac_11_pos": (
        "Phân thức y=(ax+b)/(cx+d), ad-bc>0 — đồng biến từng khoảng",
        _BBT_FRAC_11_POS,
    ),
    "frac_11_neg": (
        "Phân thức y=(ax+b)/(cx+d), ad-bc<0 — nghịch biến từng khoảng",
        _BBT_FRAC_11_NEG,
    ),
    "frac_21": (
        "Phân thức bậc 2/bậc 1 có TC xiên + 2 cực trị",
        _BBT_FRAC_21,
    ),
    # Mũ & log
    "exp_inc":   ("Hàm mũ y=a^x, a>1 — đồng biến",    _BBT_EXP_INCREASING),
    "exp_dec":   ("Hàm mũ y=a^x, 0<a<1 — nghịch biến", _BBT_EXP_DECREASING),
    "log_inc":   ("Hàm log y=log_a x, a>1 — đồng biến trên (0,+∞)",  _BBT_LOG_INCREASING),
    "log_dec":   ("Hàm log y=log_a x, 0<a<1 — nghịch biến trên (0,+∞)", _BBT_LOG_DECREASING),
    # Căn
    "sqrt_simple":    ("Hàm y=√(x-a) — đồng biến trên [a,+∞)", _BBT_SQRT_SIMPLE),
    "sqrt_parabolic": ("Hàm y=√(-x²+ax+b) — TXĐ là đoạn, có 1 cực đại", _BBT_SQRT_PARABOLIC),
    # Gián đoạn
    "discontinuous": (
        "Hàm có điểm gián đoạn (ký hiệu `d`)",
        _BBT_DISCONTINUOUS,
    ),
    # Xét dấu
    "sign_quadratic": ("Bảng xét dấu tam thức bậc 2 có 2 nghiệm", _SIGN_QUADRATIC),
    "sign_linear":    ("Bảng xét dấu nhị thức ax+b",              _SIGN_LINEAR),
}


# ══════════════════════════════════════════════════════════════════════════════
#  API CÔNG KHAI
# ══════════════════════════════════════════════════════════════════════════════

def list_templates() -> List[str]:
    """Trả về danh sách tên template có sẵn."""
    return list(_CATALOG.keys())


def get_template(name: str) -> str:
    """Lấy nội dung template theo tên. Raise KeyError nếu không có."""
    if name not in _CATALOG:
        raise KeyError(
            f"Không có template BBT '{name}'. "
            f"Có sẵn: {', '.join(list_templates())}"
        )
    return _CATALOG[name][1]


def get_description(name: str) -> str:
    """Lấy mô tả ngắn của template."""
    if name not in _CATALOG:
        raise KeyError(name)
    return _CATALOG[name][0]


def describe_templates() -> str:
    """Trả về chuỗi mô tả toàn bộ catalog — dùng để nhúng vào prompt AI."""
    lines = []
    for key, (desc, _code) in _CATALOG.items():
        lines.append(f"  • {key}: {desc}")
    return "\n".join(lines)


def prompt_block() -> str:
    """Khối prompt tham khảo BBT cho AI — nhúng vào prompt generator."""
    return (
        "THƯ VIỆN BẢNG BIẾN THIÊN (tkz-tab) — tham khảo khi sinh câu liên quan hàm số:\n"
        + describe_templates()
        + "\n\nMỗi template đã bọc trong \\begin{tikzpicture}...\\end{tikzpicture}."
        + " AI có thể: (1) copy template gần nhất rồi THAY số liệu cụ thể, hoặc"
        + " (2) viết BBT mới bám theo cú pháp tkz-tab chuẩn (\\tkzTabInit, \\tkzTabLine, \\tkzTabVar).\n"
    )


def suggest_template(func_desc: str) -> str | None:
    """Heuristic: gợi ý tên template theo mô tả hàm số (tiếng Việt).

    Dùng trong UI hoặc pipeline tăng cường — không bắt buộc dùng.
    """
    s = (func_desc or "").lower()
    # Thứ tự kiểm tra quan trọng: cụ thể → tổng quát
    if "bậc 4" in s or "trùng phương" in s or "x^4" in s:
        if "a > 0" in s or "a>0" in s:
            return "quartic_w"
        if "a < 0" in s or "a<0" in s:
            return "quartic_m"
        return "quartic_u"
    if "bậc 3" in s or "x^3" in s:
        if "không cực trị" in s or "đơn điệu" in s:
            return "cubic_no_extrema_pos" if "tăng" in s else "cubic_no_extrema_neg"
        return "cubic_two_extrema_pos" if "a > 0" in s or "a>0" in s else "cubic_two_extrema_neg"
    if "bậc 2" in s or "parabol" in s or "x^2" in s:
        return "quadratic_min" if ("min" in s or "cực tiểu" in s or "a > 0" in s) else "quadratic_max"
    if "phân thức" in s or "/(cx+d)" in s or "bậc 2/bậc 1" in s:
        if "bậc 2" in s and "bậc 1" in s:
            return "frac_21"
        return "frac_11_pos"
    if "log" in s:
        return "log_inc" if "a > 1" in s or "đồng biến" in s else "log_dec"
    if "mũ" in s or "a^x" in s or "e^x" in s:
        return "exp_inc" if "a > 1" in s or "đồng biến" in s else "exp_dec"
    if "căn" in s or "sqrt" in s or "√" in s:
        return "sqrt_parabolic" if "parabol" in s or "đoạn" in s else "sqrt_simple"
    if "gián đoạn" in s:
        return "discontinuous"
    if "xét dấu" in s:
        return "sign_quadratic" if "bậc 2" in s else "sign_linear"
    return None
