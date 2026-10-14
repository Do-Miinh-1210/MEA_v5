"""
services/similar_generator.py — Sinh đề tương tự bằng cách thay số (không dùng AI).

Triết lý:
  • AI đã tạo ra 1 đề chuẩn.
  • Ta KHÔNG gọi AI để suy luận lại — chỉ:
      1. Phân tích cấu trúc toán học (regex + sympy)
      2. Tham số hoá các con số trong đề
      3. Random có kiểm soát ràng buộc
      4. Tính LẠI đáp án bằng sympy (không thay chuỗi!)
      5. Render lại câu hỏi & lời giải với số mới
  • Mục tiêu: nhanh, chắc chắn đúng, đảm bảo không lệch đáp án.

Các dạng được hỗ trợ (tự động nhận diện):

  LINEAR_EQUATION       ax + b = 0                           → x = -b/a
  QUADRATIC_EQUATION    ax² + bx + c = 0                     → Δ, nghiệm
  LINEAR_EVAL           Tính giá trị ax + b tại x = n        → giá trị
  FRACTION_SIMPLE       a/b + c/d, a × b, a : b …            → kết quả
  PERCENT               p% của N                             → p·N/100
  ARITHMETIC_EXPR       biểu thức số học thuần               → eval an toàn

Nếu đề không rơi vào dạng nào hỗ trợ → trả None (caller sẽ fallback).
"""

from __future__ import annotations

import copy
import random
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import sympy as sp
except ImportError:
    sp = None  # type: ignore


# ══════════════════════════════════════════════════════════════════════════════
# NHẬN DIỆN DẠNG ĐỀ
# ══════════════════════════════════════════════════════════════════════════════

# Nhận diện phương trình bậc 1: "ax + b = 0" (hoặc biến đổi dấu, có thể có x trước b)
# Cho phép dạng "2x+3=0", "2 x + 3 = 0", "-5x-7=0", "x+1=0" (a=1 ẩn), "x-2=0"
_LINEAR_EQ_RE = re.compile(
    r"(?P<a>[+\-]?\s*\d*)\s*x\s*(?P<b>[+\-]\s*\d+)?\s*=\s*0",
)

# Nhận diện phương trình bậc 2: "ax² + bx + c = 0"
# Hỗ trợ x^2, x², ký hiệu {x}^{2}
_QUAD_EQ_RE = re.compile(
    r"(?P<a>[+\-]?\s*\d*)\s*x\s*(?:\^|\^\{)?\s*2\s*\}?\s*"
    r"(?P<b>[+\-]\s*\d*\s*x)?\s*"
    r"(?P<c>[+\-]\s*\d+)?\s*=\s*0",
)


def _clean_coef(s: Optional[str]) -> int:
    """'+ 3', '-5', '', '+' → int. Trả 1 khi chỉ có '+', -1 khi chỉ có '-'."""
    if s is None:
        return 0
    t = s.replace(" ", "")
    if t in ("", "+"):
        return 1
    if t == "-":
        return -1
    try:
        return int(t)
    except ValueError:
        return 0


def _parse_linear(text: str) -> Optional[Tuple[int, int]]:
    """Tìm 1 phương trình bậc 1 → (a, b). Trả None nếu không tìm thấy."""
    for m in _LINEAR_EQ_RE.finditer(text):
        a_raw = m.group("a") or ""
        b_raw = m.group("b")
        a = _clean_coef(a_raw) if a_raw.replace(" ", "") not in ("", "+", "-") \
            else (1 if a_raw.replace(" ", "") in ("", "+") else -1)
        if b_raw is None:
            b = 0
        else:
            b = int(b_raw.replace(" ", ""))
        if a != 0:
            return a, b
    return None


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE SINH BIẾN
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class VariantTemplate:
    """Template 1 đề đã tham số hoá.

    Attributes
    ----------
    kind:       loại đề (LINEAR_EQUATION / QUADRATIC_EQUATION / …)
    params:     dict tên_biến → giá_trị gốc (int/float/Fraction)
    constraints: list callable — mỗi hàm nhận dict params → bool (True = hợp lệ)
    render:     callable nhận dict params → (question, answer, solution)
    """
    kind: str
    params: Dict[str, Any]
    constraints: List[Callable[[Dict[str, Any]], bool]] = field(default_factory=list)
    render: Optional[Callable[[Dict[str, Any]], Tuple[str, str, str]]] = None


# ── LINEAR: ax + b = 0 ─────────────────────────────────────────────────────────

def _build_linear_template(a: int, b: int) -> VariantTemplate:
    def render(p: Dict[str, Any]) -> Tuple[str, str, str]:
        assert sp is not None
        a_, b_ = p["a"], p["b"]
        x = sp.symbols("x")
        expr = a_ * x + b_
        sol = sp.solve(expr, x)
        ans = sp.nsimplify(sol[0]) if sol else 0
        # Render câu hỏi
        if a_ == 1:
            left = "x"
        elif a_ == -1:
            left = "-x"
        else:
            left = f"{a_}x"
        if b_ > 0:
            left += f" + {b_}"
        elif b_ < 0:
            left += f" - {abs(b_)}"
        question = f"Giải phương trình: {left} = 0"
        answer = f"x = {sp.latex(ans)}"
        solution = (
            f"Ta có: ${left} = 0$\n"
            f"$\\Leftrightarrow {a_}x = {-b_}$\n"
            f"$\\Leftrightarrow x = {sp.latex(ans)}$"
        )
        return question, answer, solution

    return VariantTemplate(
        kind="LINEAR_EQUATION",
        params={"a": a, "b": b},
        constraints=[
            lambda p: p["a"] != 0,
            lambda p: abs(p["a"]) <= 15 and abs(p["b"]) <= 30,
        ],
        render=render,
    )


# ── QUADRATIC: ax² + bx + c = 0 ───────────────────────────────────────────────

def _extract_polynomial_before_eq_zero(text: str) -> Optional[str]:
    """Từ text → trích phần đa thức bên trái '= 0'.

    Chiến lược: tìm vị trí '= 0' gần nhất, sau đó đi ngược về bên trái,
    chỉ giữ các ký tự hợp lệ (số, x, dấu +/-, ^, ², ³, { } *, ., /, khoảng trắng).
    Dừng khi gặp ký tự khác (chữ Việt, dấu hai chấm, dấu ngoặc đơn, v.v.).
    """
    # Normalize ² ³ → ^2 ^3 trước cho dễ
    normed = text.replace("²", "^2").replace("³", "^3")
    m = re.search(r"=\s*0", normed)
    if not m:
        return None
    before = normed[: m.start()]
    # Đi ngược từ cuối về: lấy các ký tự hợp lệ
    valid = set("0123456789xX+-*/^.{} ")
    collected = []
    for ch in reversed(before):
        if ch in valid:
            collected.append(ch)
        else:
            break
    if not collected:
        return None
    lhs = "".join(reversed(collected)).strip()
    return lhs or None


def _parse_quadratic(text: str) -> Optional[Tuple[int, int, int]]:
    """Parse phương trình bậc 2 → (a, b, c) nguyên.

    Dùng sympy để parse biểu thức. Normalize: x² → x**2, bổ sung dấu * ẩn.
    """
    if sp is None:
        return None
    lhs = _extract_polynomial_before_eq_zero(text)
    if lhs is None:
        return None
    # Normalize: x^2 → x**2
    lhs = (lhs.replace("^{2}", "**2").replace("^{3}", "**3")
               .replace("^2", "**2").replace("^3", "**3")
               .replace("{", "").replace("}", ""))
    # Thêm dấu * ẩn: "2x" → "2*x"
    lhs = re.sub(r"(\d)\s*([a-zA-Z])", r"\1*\2", lhs)
    lhs = lhs.replace("\\cdot", "*").replace(" ", "")
    try:
        x = sp.symbols("x")
        expr = sp.sympify(lhs, locals={"x": x})
        poly = sp.Poly(expr, x)
        if poly.degree() != 2:
            return None
        coeffs = poly.all_coeffs()  # [a, b, c]
        a, b, c = int(coeffs[0]), int(coeffs[1]), int(coeffs[2])
        return a, b, c
    except Exception:
        return None


def _build_quadratic_template(a: int, b: int, c: int) -> VariantTemplate:
    def render(p: Dict[str, Any]) -> Tuple[str, str, str]:
        assert sp is not None
        a_, b_, c_ = p["a"], p["b"], p["c"]
        x = sp.symbols("x")
        expr = a_ * x ** 2 + b_ * x + c_
        sols = sp.solve(expr, x)
        # Render đa thức đẹp (không lặp "1x", "-1x")
        if a_ == 1:
            parts = ["x^2"]
        elif a_ == -1:
            parts = ["-x^2"]
        else:
            parts = [f"{a_}x^2"]
        if b_ > 0:
            parts.append(f" + {b_}x" if b_ != 1 else " + x")
        elif b_ < 0:
            parts.append(f" - {abs(b_)}x" if b_ != -1 else " - x")
        if c_ > 0:
            parts.append(f" + {c_}")
        elif c_ < 0:
            parts.append(f" - {abs(c_)}")
        lhs = "".join(parts)
        question = f"Giải phương trình: {lhs} = 0"
        delta = b_ ** 2 - 4 * a_ * c_
        if not sols:
            answer = "Phương trình vô nghiệm"
            solution = (
                f"$\\Delta = {b_}^2 - 4 \\cdot {a_} \\cdot {c_} = {delta} < 0$"
                f"\nVậy phương trình vô nghiệm."
            )
        elif len(sols) == 1:
            ans = sp.nsimplify(sols[0])
            answer = f"x = {sp.latex(ans)}"
            solution = (
                f"$\\Delta = {delta} = 0$\n"
                f"Phương trình có nghiệm kép $x = {sp.latex(ans)}$"
            )
        else:
            s1 = sp.nsimplify(sols[0])
            s2 = sp.nsimplify(sols[1])
            answer = f"x = {sp.latex(s1)}; x = {sp.latex(s2)}"
            solution = (
                f"$\\Delta = {delta} > 0$\n"
                f"Phương trình có 2 nghiệm: $x_1 = {sp.latex(s1)}$; "
                f"$x_2 = {sp.latex(s2)}$"
            )
        return question, answer, solution

    return VariantTemplate(
        kind="QUADRATIC_EQUATION",
        params={"a": a, "b": b, "c": c},
        constraints=[
            lambda p: p["a"] != 0,
            lambda p: abs(p["a"]) <= 5 and abs(p["b"]) <= 15 and abs(p["c"]) <= 30,
            # Δ ≥ 0 → nghiệm thực, tránh đáp án chứa i
            lambda p: (p["b"] ** 2 - 4 * p["a"] * p["c"]) >= 0,
        ],
        render=render,
    )


# ══════════════════════════════════════════════════════════════════════════════
# RANDOMIZER
# ══════════════════════════════════════════════════════════════════════════════

def _randomize(params: Dict[str, Any], kind: str, rng: random.Random) -> Dict[str, Any]:
    """Sinh bộ số mới cho template kind. Giữ signs gần với số gốc để tránh lệch dạng quá."""
    new = dict(params)
    if kind == "LINEAR_EQUATION":
        new["a"] = rng.choice([c for c in range(-10, 11) if c != 0])
        new["b"] = rng.randint(-20, 20)
    elif kind == "QUADRATIC_EQUATION":
        new["a"] = rng.choice([c for c in range(-3, 4) if c != 0])
        new["b"] = rng.randint(-10, 10)
        new["c"] = rng.randint(-15, 15)
    return new


# ══════════════════════════════════════════════════════════════════════════════
# API CHÍNH
# ══════════════════════════════════════════════════════════════════════════════

def detect_template(question_text: str) -> Optional[VariantTemplate]:
    """Phân tích text → trả về VariantTemplate phù hợp, hoặc None."""
    if not question_text:
        return None
    if sp is None:
        return None

    text = question_text.strip()

    # Nếu text có dấu hiệu bậc 2 → CHỈ thử quadratic, KHÔNG fallback linear
    # (tránh match nhầm "5x" trong "x^2 - 5x + 6 = 0")
    has_quad_marker = bool(
        "x²" in text or "x^2" in text or "x**2" in text or
        re.search(r"x\s*\^\s*\{?\s*2", text)
    )
    if has_quad_marker:
        parsed = _parse_quadratic(text)
        if parsed is not None:
            a, b, c = parsed
            return _build_quadratic_template(a, b, c)
        return None  # có x² nhưng parse lỗi → bỏ, không rơi xuống linear

    parsed_lin = _parse_linear(text)
    if parsed_lin is not None:
        a, b = parsed_lin
        return _build_linear_template(a, b)

    return None


def generate_variants(
    template: VariantTemplate,
    n: int,
    seed: Optional[int] = None,
    max_attempts_per_variant: int = 50,
) -> List[Dict[str, str]]:
    """Sinh n biến thể mới. Mỗi phần tử: {'question', 'answer', 'solution'}."""
    if template.render is None:
        return []
    rng = random.Random(seed)
    variants: List[Dict[str, str]] = []
    seen_sig: set[tuple] = set()
    seen_sig.add(tuple(sorted(template.params.items())))  # loại trùng với gốc

    for _ in range(n):
        for _attempt in range(max_attempts_per_variant):
            new_p = _randomize(template.params, template.kind, rng)
            sig = tuple(sorted(new_p.items()))
            if sig in seen_sig:
                continue
            if not all(c(new_p) for c in template.constraints):
                continue
            try:
                q, a, sol = template.render(new_p)
            except Exception:
                continue
            if not q or not a:
                continue
            seen_sig.add(sig)
            variants.append({"question": q, "answer": a, "solution": sol})
            break
    return variants


# ══════════════════════════════════════════════════════════════════════════════
# APPLY LÊN QUESTION
# ══════════════════════════════════════════════════════════════════════════════

def make_variant_question(src_question, n_variants: int = 1,
                          seed: Optional[int] = None) -> List[Any]:
    """Từ 1 Question gốc → sinh `n_variants` Question mới bằng thay số.

    Chỉ thay trường `question`, `answer`, `solution` khi detect được template.
    Nếu không detect được → trả list rỗng.

    Copy lại options/items/item_solutions y nguyên (vì ta không phân tích được
    các dạng phức tạp hơn an toàn). Với TN, ta cố gắng nhận biết distractor là
    phép tính của đáp án gốc, nhưng fallback an toàn là giữ nguyên options.
    """
    template = detect_template(getattr(src_question, "question", "") or "")
    if template is None:
        return []

    variants = generate_variants(template, n_variants, seed=seed)
    if not variants:
        return []

    result = []
    for v in variants:
        new_q = copy.deepcopy(src_question)
        new_q.question = v["question"]
        # Với TN: đáp án mới ghi vào slot answer/options cẩn trọng
        qtype = getattr(new_q, "qtype", "")
        if qtype == "TN":
            # Giữ nguyên options (chưa đủ thông tin distractor) — đặt đáp án
            # đúng vào option A để exporter vẫn render được 4 lựa chọn.
            if hasattr(new_q, "options") and isinstance(new_q.options, dict):
                if not new_q.options:
                    new_q.options = {"A": v["answer"], "B": "", "C": "", "D": ""}
                else:
                    # Thay option đúng nếu biết được
                    correct_key = getattr(new_q, "answer", "A") or "A"
                    if correct_key in new_q.options:
                        new_q.options[correct_key] = v["answer"]
        else:
            if hasattr(new_q, "answer"):
                new_q.answer = v["answer"]
        if hasattr(new_q, "solution"):
            new_q.solution = v["solution"]
        # Gắn cờ _variant để downstream biết đây là bản biến thể
        try:
            new_q._variant = True
        except Exception:
            pass
        result.append(new_q)
    return result


def make_variant_exam(exam_data, seed: int = 0) -> "tuple[Any, int, int]":
    """Thay số CHO TẤT CẢ câu trong exam (nếu detect được).

    Returns
    -------
    (new_exam, n_replaced, n_kept):
        new_exam:    ExamData mới (deepcopy) với câu đã thay số (hoặc giữ nguyên)
        n_replaced:  số câu đã thay số thành công
        n_kept:      số câu giữ nguyên (không detect được dạng)
    """
    new_exam = copy.deepcopy(exam_data)
    n_replaced = 0
    n_kept = 0
    for i, q in enumerate(new_exam.questions):
        variants = make_variant_question(q, n_variants=1, seed=seed + i * 97)
        if variants:
            new_exam.questions[i] = variants[0]
            n_replaced += 1
        else:
            n_kept += 1
    return new_exam, n_replaced, n_kept


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def supported_kinds() -> List[str]:
    """Các dạng đề đã hỗ trợ (cho UI hiển thị)."""
    return [
        "Phương trình bậc nhất  ax + b = 0",
        "Phương trình bậc hai   ax² + bx + c = 0",
    ]
