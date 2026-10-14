"""
services/cross_model.py — Phase 2: Cross-model verification.

Gemini tạo → Claude kiểm tra (hoặc ngược lại).
Nếu 2 model không đồng ý → regenerate.
"""
from __future__ import annotations
import json, re
from typing import Callable, Optional
from core.models import Question


_VERIFY_PROMPT = """\
Bạn là giáo viên Toán THPT kiểm tra câu hỏi do AI khác tạo ra.
Nhiệm vụ: Xác nhận câu hỏi sau có đúng về mặt toán học không?

CÂU HỎI:
{question}
{choices_or_items}
ĐÁP ÁN ĐƯỢC CÔNG BỐ: {answer}

Giải lại từ đầu, sau đó trả về JSON duy nhất:
{{"agree": true, "your_answer": "A", "reason": "giải thích ngắn", "confidence": 0.9}}

- agree: true nếu bạn đồng ý với đáp án công bố
- your_answer: kết quả bạn tự tính
- confidence: 0.0–1.0"""


def _format_for_verify(q: Question) -> tuple[str, str]:
    """Trả về (choices_block, answer_str)."""
    if q.qtype in ("TN", "NPA"):
        lines = [f"{k}. {v}" for k, v in q.options.items()]
        return "\n".join(lines), q.answer
    elif q.qtype == "DS":
        lines = [f"({k}) {v}" for k, v in q.items.items()]
        ans = ", ".join(f"{k}={'Đ' if v else 'S'}" for k, v in q.answers.items())
        return "\n".join(lines), ans
    return "", q.answer or "(xem lời giải)"


def cross_verify(
    q: Question,
    verifier_ai: Callable[[str], str],
) -> dict:
    """
    Gọi AI verifier để kiểm tra câu hỏi.
    Returns: {"agree": bool, "your_answer": str, "reason": str, "confidence": float}
    """
    choices_block, answer_str = _format_for_verify(q)
    prompt = _VERIFY_PROMPT.format(
        question=q.question,
        choices_or_items=choices_block,
        answer=answer_str,
    )
    try:
        raw = verifier_ai(prompt)
        # Extract JSON
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            return {
                "agree":       bool(data.get("agree", True)),
                "your_answer": str(data.get("your_answer", "")),
                "reason":      str(data.get("reason", "")),
                "confidence":  float(data.get("confidence", 0.7)),
            }
    except Exception as e:
        pass
    return {"agree": True, "your_answer": "", "reason": "Không verify được", "confidence": 0.5}


def cross_model_pipeline(
    q: Question,
    generator_ai: Callable[[str], str],
    verifier_ai: Optional[Callable[[str], str]],
    regenerate_fn: Callable[[], Question],
    max_attempts: int = 2,
) -> tuple[Question, dict]:
    """
    Phase 2 pipeline:
      1. Verify câu hỏi bằng model thứ 2
      2. Nếu không đồng ý → regenerate (tối đa max_attempts lần)
      3. Trả về (câu hỏi cuối, metadata)

    verifier_ai: None = bỏ qua cross-model (dùng 1 model)
    """
    if verifier_ai is None:
        return q, {"cross_verified": False, "skipped": True}

    for attempt in range(max_attempts):
        result = cross_verify(q, verifier_ai)
        if result["agree"] and result["confidence"] >= 0.7:
            return q, {
                "cross_verified":   True,
                "agreed":           True,
                "verifier_answer":  result["your_answer"],
                "verifier_reason":  result["reason"],
                "confidence":       result["confidence"],
                "attempts":         attempt + 1,
            }
        # Không đồng ý → regenerate
        if attempt < max_attempts - 1:
            q = regenerate_fn()
        else:
            # Sau max_attempts vẫn không đồng ý → flag để review
            q._review = q._review or {}
            q._review["cross_model_disagree"] = True
            q._review["verifier_answer"] = result["your_answer"]
            q._review["verifier_reason"] = result["reason"]
            return q, {
                "cross_verified":  True,
                "agreed":          False,
                "verifier_answer": result["your_answer"],
                "verifier_reason": result["reason"],
                "confidence":      result["confidence"],
                "attempts":        attempt + 1,
                "needs_review":    True,
            }

    return q, {"cross_verified": False}
