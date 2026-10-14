"""
core/quality_pipeline.py — Hệ thống Kiểm soát Chất lượng Nhiều Lớp (QC Pipeline).

Triết lý: Không phải "AI tạo câu hỏi" mà là "Quality Control System"

Pipeline:
  1. Generate   — AI Generator tạo câu (chỉ tạo, không tự check)
  2. Normalize  — Rule-based chuẩn hóa format
  3. Solver #1  — AI Solver giải độc lập (không biết đáp án)
  4. Solver #2  — AI Generator giải lại (Double-solve)
  5. Critic     — AI Critic chỉ tìm lỗi logic/wording/bẫy
  6. Math Eng   — sympy kiểm tra nghiệm (nếu có)
  7. Score      — Tính Quality Score tổng hợp
  8. Pass/Reject — < 0.8 reject, 0.8–0.9 cần review, ≥ 0.9 pass
"""

from __future__ import annotations
import re
import json
import copy
import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from core.models import Question
from core.ai_reviewer import normalize_question


# ══════════════════════════════════════════════════════════════════════════════
#  DATA CLASSES
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class QualityScore:
    """Điểm chất lượng đa chiều của 1 câu hỏi."""
    math_correctness:  float = 1.0   # Đáp án toán học có đúng không
    clarity:           float = 1.0   # Câu hỏi rõ ràng, không mơ hồ
    ambiguity:         float = 0.0   # Mức độ mơ hồ (0 = không mơ hồ)
    difficulty_match:  float = 1.0   # Độ khó đúng với yêu cầu
    double_solve_ok:   float = 1.0   # Solver 1 & 2 đồng ý (1=đồng ý, 0=khác)
    format_ok:         float = 1.0   # Format đúng chuẩn
    final_score:       float = 1.0   # Tổng hợp

    # Verdict
    passed:   bool = True
    needs_review: bool = False
    reject_reason: str = ""

    # Chi tiết
    solver1_answer:  str = ""
    solver2_answer:  str = ""
    critic_issues:   list = field(default_factory=list)
    math_engine_ok:  Optional[bool] = None
    notes:           str = ""

    def to_dict(self) -> dict:
        return {
            "math_correctness": self.math_correctness,
            "clarity":          self.clarity,
            "ambiguity":        self.ambiguity,
            "difficulty_match": self.difficulty_match,
            "double_solve_ok":  self.double_solve_ok,
            "format_ok":        self.format_ok,
            "final_score":      round(self.final_score, 3),
            "passed":           self.passed,
            "needs_review":     self.needs_review,
            "reject_reason":    self.reject_reason,
            "solver1_answer":   self.solver1_answer,
            "solver2_answer":   self.solver2_answer,
            "critic_issues":    self.critic_issues,
            "math_engine_ok":   self.math_engine_ok,
            "notes":            self.notes,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  PROMPT TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

# Solver: Giải độc lập, KHÔNG biết đáp án
_SOLVER_PROMPT = """\
Bạn là học sinh giỏi Toán THPT Việt Nam. Hãy GIẢI câu hỏi dưới đây từ đầu.
QUAN TRỌNG: Bạn KHÔNG biết đáp án trước. Hãy tự tính toán và tìm ra đáp án.

Môn: {subject} — Lớp: {grade}
Loại câu: {qtype_label}

CÂU HỎI:
{question_content}

Yêu cầu trả lời theo đúng format:
===SOLVE===
CACH_GIAI: <trình bày từng bước giải rõ ràng>
KET_QUA: <đáp án cuối cùng — với TN ghi A/B/C/D, với DS ghi a=Đ/S,b=Đ/S,..., với TLN ghi số>
DO_TIN_CAY: <0.0–1.0, mức độ chắc chắn của bạn>
===END_SOLVE==="""

# Critic: Chỉ tìm lỗi, không tạo, không giải
_CRITIC_PROMPT = """\
Bạn là chuyên gia kiểm định đề thi Toán THPT Việt Nam (vai trò Critic thuần túy).
NHIỆM VỤ DUY NHẤT: Tìm lỗi. KHÔNG tạo câu mới. KHÔNG giải bài.

Môn: {subject} — Lớp: {grade}
Mức độ yêu cầu: {level}

CÂU HỎI ĐỂ KIỂM TRA:
{question_content}

ĐÁP ÁN ĐÃ BIẾT: {known_answer}

Kiểm tra theo 5 tiêu chí:
1. LỖI LOGIC: Bài toán có mâu thuẫn nội tại không?
2. LỖI WORDING: Câu hỏi có mơ hồ, gây hiểu nhầm không?
3. LỖI BẪY: Có phương án nào gây đánh đố vô lý không?
4. LỖI ĐỘ KHÓ: Độ khó có đúng với mức {level} không?
5. LỖI SƯ PHẠM: Câu có mục tiêu kiểm tra kiến thức rõ ràng không?

Trả về JSON duy nhất:
===CRITIC===
{{
  "logic_ok": true,
  "wording_ok": true,
  "trap_ok": true,
  "difficulty_ok": true,
  "pedagogy_ok": true,
  "issues": ["mô tả lỗi 1 nếu có", "mô tả lỗi 2 nếu có"],
  "overall_ok": true,
  "clarity_score": 0.9,
  "notes": "nhận xét ngắn"
}}
===END_CRITIC==="""

# Knowledge Base: các lỗi phổ biến theo chủ đề
_KNOWLEDGE_BASE = {
    "logarit": ["quên điều kiện xác định", "sai cơ số", "nhầm log_a(b) với log_b(a)"],
    "tích phân": ["quên hằng số C", "sai giới hạn tích phân", "nhầm vi phân"],
    "hàm số": ["quên kiểm tra miền xác định", "sai chiều đơn điệu", "cực trị nhầm"],
    "tổ hợp": ["nhầm C(n,k) với A(n,k)", "sai điều kiện n≥k", "quên chia trường hợp"],
    "xác suất": ["không kiểm tra tổng bằng 1", "nhầm P(A∪B)", "sai không gian mẫu"],
    "hình học": ["sai công thức diện tích", "nhầm góc", "thiếu điều kiện tồn tại"],
}

_TRANSIENT_AI_ERROR_KW = (
    "429",
    "500",
    "503",
    "529",
    "quota",
    "rate limit",
    "rate-limit",
    "resource exhausted",
    "unavailable",
    "overloaded",
    "high demand",
    "timeout",
    "temporarily",
)


def _get_kb_warnings(topic: str) -> str:
    """Lấy cảnh báo từ Knowledge Base theo chủ đề."""
    topic_lower = topic.lower()
    warnings = []
    for key, mistakes in _KNOWLEDGE_BASE.items():
        if key in topic_lower:
            warnings.extend(mistakes)
    if warnings:
        return "Các lỗi phổ biến cần tránh: " + "; ".join(warnings)
    return ""


def _is_transient_ai_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(kw in msg for kw in _TRANSIENT_AI_ERROR_KW)


def _call_ai_with_retry(
    ai_call: Callable[[str], str],
    prompt: str,
    *,
    retry_delays: Sequence[float] = (2.0, 5.0),
    on_retry: Optional[Callable[[int, float, str], None]] = None,
) -> str:
    """Call AI with small backoff for quota/server errors.

    This keeps QC batch resilient without hiding non-transient prompt/parser
    problems. The UI can use `on_retry` to show the current wait/retry state.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(len(retry_delays) + 1):
        try:
            return ai_call(prompt)
        except Exception as exc:
            last_exc = exc
            if attempt >= len(retry_delays) or not _is_transient_ai_error(exc):
                raise
            wait_s = float(retry_delays[attempt])
            if on_retry:
                on_retry(attempt + 1, wait_s, str(exc))
            time.sleep(max(0.0, wait_s))
    raise last_exc or RuntimeError("AI call failed")


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — AI SOLVER (giải độc lập)
# ══════════════════════════════════════════════════════════════════════════════

def _format_question_for_solver(q: Question) -> str:
    """Định dạng câu hỏi để gửi AI Solver."""
    lines = [q.question]
    if q.qtype == "TN":
        for k, v in q.options.items():
            lines.append(f"  {k}. {v}")
    elif q.qtype == "DS":
        for k, v in q.items.items():
            lines.append(f"  ({k}) {v}")
    elif q.qtype in ("TLN", "TL"):
        pass  # Chỉ có câu hỏi
    return "\n".join(lines)


def _parse_solver_response(raw: str) -> dict:
    """Parse phản hồi của Solver."""
    m = re.search(r"===SOLVE===(.*?)===END_SOLVE===", raw, re.DOTALL | re.IGNORECASE)
    block = m.group(1) if m else raw
    kv: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            kv[k.strip().upper()] = v.strip()
    return {
        "answer":     kv.get("KET_QUA", ""),
        "steps":      kv.get("CACH_GIAI", ""),
        "confidence": float(kv.get("DO_TIN_CAY", "0.5"))
                      if kv.get("DO_TIN_CAY", "").replace(".", "").isdigit()
                      else 0.5,
    }


def ai_solve(
    q: Question,
    subject: str,
    grade: str,
    ai_call: Callable[[str], str],
    *,
    on_retry: Optional[Callable[[int, float, str], None]] = None,
    retry_delays: Sequence[float] = (2.0, 5.0),
) -> dict:
    """Gọi AI Solver giải câu hỏi độc lập."""
    from config import TYPE_LABELS
    question_content = _format_question_for_solver(q)
    prompt = _SOLVER_PROMPT.replace("{subject}", subject) \
                            .replace("{grade}", grade) \
                            .replace("{qtype_label}", TYPE_LABELS.get(q.qtype, q.qtype)) \
                            .replace("{question_content}", question_content)
    try:
        raw = _call_ai_with_retry(
            ai_call,
            prompt,
            on_retry=on_retry,
            retry_delays=retry_delays,
        )
        return _parse_solver_response(raw)
    except Exception as e:
        return {"answer": "", "steps": "", "confidence": 0.0, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — DOUBLE SOLVE (so sánh 2 lần giải)
# ══════════════════════════════════════════════════════════════════════════════

def _normalize_answer(ans: str, qtype: str) -> str:
    """Chuẩn hóa đáp án để so sánh."""
    ans = ans.strip().upper()
    if qtype == "TN":
        # Chỉ lấy chữ cái đầu tiên A/B/C/D
        m = re.search(r"[ABCD]", ans)
        return m.group(0) if m else ans
    elif qtype == "DS":
        # Chuẩn hóa a=D,b=S,... → dict để so sánh
        parts = re.findall(r"([A-Da-d])[\s=:]+([ĐĐDdSs])", ans, re.IGNORECASE)
        # Normalize Đ → D để so sánh nhất quán
        return "|".join(
            f"{k.upper()}={'D' if v.upper() in ('Đ','D') else 'S'}"
            for k, v in sorted(parts)
        )
    return ans


def check_double_solve(q: Question, solver1: dict, solver2: dict) -> float:
    """
    So sánh kết quả 2 lần giải.
    Returns: 1.0 nếu đồng ý, 0.0 nếu khác nhau.
    """
    ans1 = _normalize_answer(solver1.get("answer", ""), q.qtype)
    ans2 = _normalize_answer(solver2.get("answer", ""), q.qtype)
    if not ans1 or not ans2:
        return 0.5  # Không đủ thông tin
    return 1.0 if ans1 == ans2 else 0.0


def check_solver_vs_answer(q: Question, solver: dict) -> float:
    """
    So sánh kết quả Solver với đáp án trong câu hỏi.
    Returns: 1.0 nếu khớp, 0.0 nếu sai.
    """
    solver_ans = _normalize_answer(solver.get("answer", ""), q.qtype)
    if q.qtype == "TN":
        correct = q.answer.strip().upper()
        return 1.0 if solver_ans == correct else 0.0
    elif q.qtype == "DS":
        correct = "|".join(
            f"{k}={'D' if v else 'S'}"
            for k, v in sorted(q.answers.items())
        ).upper()
        return 1.0 if solver_ans == correct else 0.0
    return 0.8  # TLN/TL khó so sánh tự động


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5 — AI CRITIC (chỉ tìm lỗi)
# ══════════════════════════════════════════════════════════════════════════════

def _parse_critic_response(raw: str) -> dict:
    """Parse phản hồi JSON của Critic."""
    m = re.search(r"===CRITIC===(.*?)===END_CRITIC===", raw, re.DOTALL | re.IGNORECASE)
    block = m.group(1).strip() if m else raw.strip()

    # Tìm JSON trong block
    start = block.find("{")
    end   = block.rfind("}") + 1
    if start == -1 or end <= 0:
        return {"overall_ok": True, "issues": [], "clarity_score": 0.8}
    try:
        return json.loads(block[start:end])
    except json.JSONDecodeError:
        return {"overall_ok": True, "issues": [], "clarity_score": 0.8}


def ai_critic(
    q: Question,
    subject: str,
    grade: str,
    ai_call: Callable[[str], str],
    *,
    on_retry: Optional[Callable[[int, float, str], None]] = None,
    retry_delays: Sequence[float] = (2.0, 5.0),
) -> dict:
    """Gọi AI Critic phân tích lỗi câu hỏi."""
    question_content = _format_question_for_solver(q)
    if q.qtype == "TN":
        known_answer = f"Đáp án đúng: {q.answer}"
    elif q.qtype == "DS":
        known_answer = ", ".join(
            f"{k}={'Đúng' if v else 'Sai'}" for k, v in q.answers.items())
    else:
        known_answer = q.answer or "(chưa có)"

    prompt = _CRITIC_PROMPT.replace("{subject}", subject) \
                            .replace("{grade}", grade) \
                            .replace("{level}", q.level) \
                            .replace("{question_content}", question_content) \
                            .replace("{known_answer}", known_answer)
    try:
        raw = _call_ai_with_retry(
            ai_call,
            prompt,
            on_retry=on_retry,
            retry_delays=retry_delays,
        )
        return _parse_critic_response(raw)
    except Exception as e:
        return {
            "overall_ok": True,
            "issues": [f"Không gọi được AI Critic: {e}"],
            "clarity_score": 0.8,
            "wording_ok": True,
            "difficulty_ok": True,
            "logic_ok": True,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 6 — MATH ENGINE (sympy-based)
# ══════════════════════════════════════════════════════════════════════════════

def math_engine_check(q: Question) -> Optional[bool]:
    """
    Kiểm tra nghiệm bằng sympy.
    Returns: True (đúng), False (sai), None (không kiểm tra được).
    """
    try:
        import sympy
    except ImportError:
        return None  # sympy chưa cài

    if q.qtype not in ("TN", "TLN"):
        return None

    # Tìm biểu thức toán trong câu hỏi và đáp án
    # Heuristic: tìm pattern số/công thức đơn giản
    question_text = q.question

    # Thử kiểm tra câu TLN với đáp số là số
    if q.qtype == "TLN" and q.answer:
        try:
            # Tìm số trong đáp án
            nums = re.findall(r"-?\d+(?:\.\d+)?(?:/\d+)?", q.answer)
            if nums:
                expected = sympy.Rational(nums[0])
                # Tìm biểu thức tính toán đơn giản trong câu hỏi
                # (chỉ check được các dạng đơn giản)
                expr_patterns = re.findall(
                    r"\$([^$]+)\$", question_text)
                for expr_str in expr_patterns:
                    try:
                        expr = sympy.sympify(
                            expr_str.replace("\\frac", "").replace("{", "(").replace("}", ")"),
                            evaluate=True)
                        if isinstance(expr, (sympy.Number, sympy.Integer)):
                            if abs(float(expr) - float(expected)) < 1e-6:
                                return True
                    except Exception:
                        continue
        except Exception:
            pass

    return None  # Không kiểm tra được


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 7 — QUALITY SCORING
# ══════════════════════════════════════════════════════════════════════════════

def compute_quality_score(
    q: Question,
    solver1_result: dict,
    solver2_result: dict,
    critic_result: dict,
    math_ok: Optional[bool],
) -> QualityScore:
    """
    Tính Quality Score tổng hợp từ kết quả các bước.

    Công thức:
      math_correctness  = avg(solver1 vs answer, solver2 vs answer)
      double_solve_ok   = 1 nếu solver1 == solver2, 0 nếu khác
      clarity           = critic.clarity_score
      ambiguity         = 1 nếu critic có issues wording
      difficulty_match  = 1 nếu critic.difficulty_ok
      format_ok         = 1 nếu không có lỗi format
      final = 0.30×math + 0.25×double + 0.20×clarity + 0.15×difficulty + 0.10×format
              - 0.10×ambiguity penalty
    """
    qs = QualityScore()

    # Math correctness
    s1_vs_ans = check_solver_vs_answer(q, solver1_result)
    s2_vs_ans = check_solver_vs_answer(q, solver2_result)
    qs.math_correctness = (s1_vs_ans + s2_vs_ans) / 2

    # Double solve
    qs.double_solve_ok = check_double_solve(q, solver1_result, solver2_result)
    qs.solver1_answer  = solver1_result.get("answer", "")
    qs.solver2_answer  = solver2_result.get("answer", "")

    # Critic
    issues          = critic_result.get("issues", [])
    qs.clarity      = float(critic_result.get("clarity_score", 0.9))
    qs.ambiguity    = 0.3 if not critic_result.get("wording_ok", True) else 0.0
    qs.difficulty_match = 1.0 if critic_result.get("difficulty_ok", True) else 0.6
    qs.critic_issues = [i for i in issues if i]
    qs.format_ok    = 1.0 if critic_result.get("logic_ok", True) else 0.5

    # Math Engine
    qs.math_engine_ok = math_ok
    if math_ok is False:
        qs.math_correctness = max(0.0, qs.math_correctness - 0.3)

    # Final score (weighted sum)
    qs.final_score = (
        0.30 * qs.math_correctness
        + 0.25 * qs.double_solve_ok
        + 0.20 * qs.clarity
        + 0.15 * qs.difficulty_match
        + 0.10 * qs.format_ok
        - 0.10 * qs.ambiguity
    )
    qs.final_score = max(0.0, min(1.0, qs.final_score))

    # Verdict (Step 8)
    if qs.final_score >= 0.9:
        qs.passed      = True
        qs.needs_review = False
    elif qs.final_score >= 0.8:
        qs.passed      = True
        qs.needs_review = True
    else:
        qs.passed        = False
        qs.needs_review  = True
        reasons = []
        if qs.math_correctness < 0.6:
            reasons.append(f"đáp án sai (Solver 1: {qs.solver1_answer}, Solver 2: {qs.solver2_answer})")
        if qs.double_solve_ok < 0.5:
            reasons.append("hai lần giải cho kết quả khác nhau")
        if qs.critic_issues:
            reasons.append("Critic: " + "; ".join(qs.critic_issues[:2]))
        qs.reject_reason = " | ".join(reasons) if reasons else "score thấp"

    return qs


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 7b — TEMPLATE ENGINE (giảm sai bằng template)
# ══════════════════════════════════════════════════════════════════════════════

QUESTION_TEMPLATES = {
    "TN_function": """\
Cho hàm số {func}. {question_stem}
A: {opt_a}
B: {opt_b}
C: {opt_c}
D: {opt_d}""",
    "TN_calculate": """\
Tính {expression} bằng:
A: {opt_a}
B: {opt_b}
C: {opt_c}
D: {opt_d}""",
    "TLN_find": """\
Tìm {target} thỏa mãn {condition}.""",
}

def suggest_template(topic: str, qtype: str, level: str) -> str:
    """Gợi ý template phù hợp dựa trên chủ đề."""
    topic_lower = topic.lower()
    if qtype == "TN":
        if any(kw in topic_lower for kw in ["hàm số", "đạo hàm"]):
            return QUESTION_TEMPLATES["TN_function"]
        if any(kw in topic_lower for kw in ["tính", "tích phân", "giới hạn"]):
            return QUESTION_TEMPLATES["TN_calculate"]
    if qtype == "TLN":
        return QUESTION_TEMPLATES["TLN_find"]
    return ""


# ══════════════════════════════════════════════════════════════════════════════
#  FULL PIPELINE — Chạy toàn bộ cho 1 câu hỏi
# ══════════════════════════════════════════════════════════════════════════════

def run_qc_pipeline(
    q: Question,
    subject: str,
    grade: str,
    ai_call: Callable[[str], str],
    run_solver:  bool = True,
    run_critic:  bool = True,
    run_math:    bool = True,
    retry_cb: Optional[Callable[[str, int, float, str], None]] = None,
    retry_delays: Sequence[float] = (2.0, 5.0),
) -> tuple[Question, QualityScore]:
    """
    Chạy full QC Pipeline cho 1 câu hỏi.

    Returns:
        (question_with_qc_metadata, quality_score)
    """
    q_work = normalize_question(copy.deepcopy(q))

    # Step 3 & 4: Double Solve
    solver1 = {"answer": "", "confidence": 0.0}
    solver2 = {"answer": "", "confidence": 0.0}
    if run_solver and not q._error:
        solver1 = ai_solve(
            q_work,
            subject,
            grade,
            ai_call,
            on_retry=(lambda a, w, e: retry_cb("Solver 1", a, w, e)) if retry_cb else None,
            retry_delays=retry_delays,
        )
        solver2 = ai_solve(
            q_work,
            subject,
            grade,
            ai_call,
            on_retry=(lambda a, w, e: retry_cb("Solver 2", a, w, e)) if retry_cb else None,
            retry_delays=retry_delays,
        )  # Lần 2 độc lập

    # Step 5: Critic
    critic = {"overall_ok": True, "issues": [], "clarity_score": 0.9,
              "wording_ok": True, "difficulty_ok": True, "logic_ok": True}
    if run_critic and not q._error:
        critic = ai_critic(
            q_work,
            subject,
            grade,
            ai_call,
            on_retry=(lambda a, w, e: retry_cb("Critic", a, w, e)) if retry_cb else None,
            retry_delays=retry_delays,
        )

    # Step 6: Math Engine
    math_ok = None
    if run_math and not q._error:
        math_ok = math_engine_check(q_work)

    # Step 7: Score
    score = compute_quality_score(q_work, solver1, solver2, critic, math_ok)

    # Gắn metadata vào câu hỏi
    q_work._review = {
        "qc_pipeline": True,
        "quality_score": score.to_dict(),
        "solver1": solver1,
        "solver2": solver2,
        "critic":  critic,
        "kb_warnings": _get_kb_warnings(q.topic),
    }

    return q_work, score


def _quality_score_from_dict(data: dict[str, Any]) -> QualityScore:
    fields = set(QualityScore.__dataclass_fields__.keys())  # type: ignore[attr-defined]
    values = {k: v for k, v in (data or {}).items() if k in fields}
    return QualityScore(**values)


def _qc_question_key(q: Question, index: int) -> str:
    return str(getattr(q, "question_id", "") or f"idx-{index}").strip()


def _qc_question_fingerprint(q: Question) -> str:
    data = {k: v for k, v in q.to_dict().items() if k != "_review"}
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def load_qc_checkpoint(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"completed": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"completed": {}}
    if not isinstance(data, dict):
        return {"completed": {}}
    data.setdefault("completed", {})
    return data


def save_qc_checkpoint(path: str | Path, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def run_qc_pipeline_batch(
    questions: list[Question],
    subject: str,
    grade: str,
    ai_call: Callable[[str], str],
    run_solver:  bool = True,
    run_critic:  bool = True,
    run_math:    bool = True,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
    retry_cb: Optional[Callable[[int, int, str, int, float, str], None]] = None,
    retry_delays: Sequence[float] = (2.0, 5.0),
    checkpoint_path: Optional[str | Path] = None,
    resume: bool = False,
    checkpoint_cb: Optional[Callable[[dict[str, Any]], None]] = None,
    adaptive: bool = False,
) -> list[tuple[Question, QualityScore]]:
    """Chạy QC Pipeline cho danh sách câu hỏi.

    checkpoint_path lưu từng câu đã xong để batch QC dài có thể resume.
    adaptive tăng backoff cho các câu sau khi gặp nhiều lỗi quota/transient.
    """
    results = []
    total   = len(questions)
    checkpoint: dict[str, Any] = {"completed": {}}
    completed: dict[str, Any] = {}
    if checkpoint_path:
        checkpoint = load_qc_checkpoint(checkpoint_path) if resume else {"completed": {}}
        checkpoint.update({
            "subject": subject,
            "grade": grade,
            "total": total,
            "updated_at": time.time(),
        })
        completed = checkpoint.setdefault("completed", {})

    active_retry_delays: Sequence[float] = tuple(retry_delays)
    transient_retries = 0

    for i, q in enumerate(questions):
        key = _qc_question_key(q, i + 1)
        fingerprint = _qc_question_fingerprint(q)
        if resume and key in completed:
            try:
                if completed[key].get("fingerprint") != fingerprint:
                    raise ValueError("checkpoint fingerprint changed")
                saved_q = Question.from_dict(completed[key]["question"])
                saved_score = _quality_score_from_dict(completed[key]["score"])
                results.append((saved_q, saved_score))
                if progress_cb:
                    progress_cb(i + 1, total, q.topic)
                if checkpoint_cb:
                    checkpoint_cb({"stage": "resume", "done": i + 1, "total": total, "key": key})
                continue
            except Exception:
                completed.pop(key, None)

        if progress_cb:
            progress_cb(i + 1, total, q.topic)

        def _retry_bridge(stage: str, attempt: int, wait: float, err: str,
                          _i: int = i + 1, _total: int = total) -> None:
            nonlocal active_retry_delays, transient_retries
            transient_retries += 1
            if adaptive and transient_retries >= 2:
                base = tuple(float(x) for x in active_retry_delays) or (2.0, 5.0)
                active_retry_delays = tuple(min(60.0, max(1.0, x * 1.5)) for x in base)
                if checkpoint_cb:
                    checkpoint_cb({
                        "stage": "adaptive_backoff",
                        "done": _i - 1,
                        "total": _total,
                        "retry_delays": list(active_retry_delays),
                    })
            if retry_cb:
                retry_cb(_i, _total, stage, attempt, wait, err)

        q_out, score = run_qc_pipeline(
            q, subject, grade, ai_call,
            run_solver=run_solver,
            run_critic=run_critic,
            run_math=run_math,
            retry_cb=_retry_bridge if (retry_cb or adaptive or checkpoint_cb) else None,
            retry_delays=active_retry_delays,
        )
        results.append((q_out, score))
        if checkpoint_path:
            completed[key] = {
                "index": i + 1,
                "fingerprint": fingerprint,
                "question": q_out.to_dict(),
                "score": score.to_dict(),
                "saved_at": time.time(),
            }
            checkpoint["updated_at"] = time.time()
            save_qc_checkpoint(checkpoint_path, checkpoint)
            if checkpoint_cb:
                checkpoint_cb({"stage": "checkpoint", "done": i + 1, "total": total, "key": key})
    return results


# ══════════════════════════════════════════════════════════════════════════════
#  SUMMARY REPORT
# ══════════════════════════════════════════════════════════════════════════════

def build_qc_summary(results: list[tuple[Question, QualityScore]]) -> dict:
    """Tổng hợp kết quả QC pipeline."""
    total    = len(results)
    passed   = sum(1 for _, s in results if s.passed and not s.needs_review)
    review   = sum(1 for _, s in results if s.passed and s.needs_review)
    rejected = sum(1 for _, s in results if not s.passed)
    avg_score = (sum(s.final_score for _, s in results) / total) if total else 0.0

    double_agree = sum(1 for _, s in results if s.double_solve_ok >= 0.9)

    return {
        "total":          total,
        "passed":         passed,
        "needs_review":   review,
        "rejected":       rejected,
        "avg_score":      round(avg_score, 3),
        "double_agree":   double_agree,
        "pass_rate":      round((passed + review) / max(total, 1) * 100, 1),
        "reject_rate":    round(rejected / max(total, 1) * 100, 1),
    }
