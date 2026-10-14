"""
core/ai_reviewer.py — Hệ thống AI đa vai trò theo system prompt spec.
Cập nhật: yêu cầu công thức trong ${...}, DS có lời giải bắt đầu bằng "Đúng. Vì..." / "Sai. Vì...".
"""

from __future__ import annotations
import json
import re
from typing import Callable, Optional

from core.models import Question
from core.parser import parse_one_question
from config import TYPE_LABELS, LEVEL_DESC


# ══════════════════════════════════════════════════════════════════════════════
#  PROMPT TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

_FEW_SHOT_TN = """
VÍ DỤ câu TN MẪU (dùng làm tham khảo chất lượng):
===CAU===
LOAI: TN
MUCDO: TH
CHUONG: Nguyên hàm - Tích phân
NOIDUNG: Tính nguyên hàm ${\\int \\left(3x^{2} - 2x + 1\\right)\\,dx}$ bằng.
A: ${x^{3} - x^{2} + x + C}$
B: ${x^{3} + x^{2} - x + C}$
C: ${6x - 2 + C}$
D: ${x^{3} - x^{2} - x + C}$
DAPAN: A
LOIGIAI: Áp dụng công thức ${\\int x^n\\,dx = \\frac{x^{n+1}}{n+1}+C}$: kết quả ${x^3 - x^2 + x + C}$.
===KETCAU===
"""

_FEW_SHOT_DS = """
VÍ DỤ câu DS MẪU (dùng làm tham khảo):
===CAU===
LOAI: DS
MUCDO: TH
CHUONG: Hàm số mũ và logarithm
NOIDUNG: Cho hàm số ${f(x) = 2^{x}}$. Xét tính đúng sai của các mệnh đề sau.
a: Hàm số ${f(x)}$ đồng biến trên ${\\mathbb{R}}$.
GIAI_a: Đúng. Vì cơ số ${2 > 1}$ nên hàm mũ đồng biến.
b: ${f(0) = 1}$.
GIAI_b: Đúng. Vì ${2^0 = 1}$.
c: ${f(-1) = -\\frac{1}{2}}$.
GIAI_c: Sai. Vì ${2^{-1} = \\frac{1}{2} > 0}$, không âm.
d: ${\\lim_{x\\to -\\infty} f(x) = 0}$.
GIAI_d: Đúng. Vì hàm mũ cơ số lớn hơn 1 tiến về 0 khi ${x\\to-\\infty}$.
DAPAN: a=D,b=D,c=S,d=D
===KETCAU===
"""

# ── Prompt cho chế độ FIX ────────────────────────────────────────────────────

_FIX_PROMPT_SAFE = """\
Bạn là hệ thống AI kiểm duyệt đề thi Toán THPT Việt Nam, gồm 3 vai trò:
1. Giáo viên ra đề — hiểu sâu nội dung toán học
2. Người kiểm duyệt độc lập — phát hiện lỗi khách quan
3. Hệ thống chuẩn hóa — đảm bảo format đúng chuẩn

Môn: {subject} — Lớp: {grade}

CÂU HỎI CẦN KIỂM TRA (mode=fix, style=safe):
{question_json}

NHIỆM VỤ (thực hiện đúng thứ tự):

Bước 1 — CHUẨN HÓA (không dùng AI suy diễn):
  - Trim khoảng trắng thừa
  - Câu hỏi phải kết thúc bằng dấu "."
  - Đảm bảo đủ A,B,C,D nếu là trắc nghiệm
  - Chuẩn hóa format LaTeX trong ${{...}}$ (bắt buộc)
  - NGOẶC TỰ ĐỘNG SCALE: TẤT CẢ ngoặc trong $...$ PHẢI dùng \\left...\\right
    (vd: ${{f\\left(x\\right)}}$, ${{\\left[1,2\\right]}}$, ${{\\left|x\\right|}}$).
    Nếu thấy `(` `[` `{{` `|` thường → SỬA thành \\left/\\right.

Bước 2 — PHÂN TÍCH LỖI (chỉ sửa trong style=safe):
  - Sai toán học (tính toán, công thức)
  - Sai đáp án
  - Lỗi format
  - KHÔNG thay đổi cách diễn đạt nếu đã đủ rõ

Bước 3 — TỰ KIỂM TRA:
  - Giải lại bài toán từ đầu
  - So sánh kết quả với đáp án đã sửa
  - Nếu vẫn sai → sửa lại

Bước 4 — VALIDATION:
  - Chỉ 1 đáp án đúng
  - Đáp án nằm trong A/B/C/D (hoặc a=D/S cho câu DS)
  - Lời giải khớp đáp án
  - Với câu DS: mỗi GIAI_x phải bắt đầu bằng "Đúng. Vì..." hoặc "Sai. Vì..."

Trả về JSON DUY NHẤT (không có text ngoài JSON):
{{
  "final": {{
    "question": "...",
    "options": {{"A":"...","B":"...","C":"...","D":"..."}},
    "correct_answer": "A",
    "solution": "...",
    "items": {{}},
    "answers": {{}},
    "item_solutions": {{}}
  }},
  "is_corrected": true,
  "difficulty_changed": false,
  "confidence": 0.95,
  "notes": "Mô tả ngắn: đã sửa gì hoặc giữ nguyên vì đúng"
}}
"""

_FIX_PROMPT_SMART = """\
Bạn là hệ thống AI kiểm duyệt đề thi Toán THPT Việt Nam, gồm 3 vai trò:
1. Giáo viên ra đề — hiểu sâu nội dung toán học
2. Người kiểm duyệt độc lập — phát hiện lỗi khách quan
3. Hệ thống chuẩn hóa — đảm bảo format và chất lượng cao nhất

Môn: {subject} — Lớp: {grade}

CÂU HỎI CẦN KIỂM TRA (mode=fix, style=smart):
{question_json}

NHIỆM VỤ (thực hiện đúng thứ tự):

Bước 1 — CHUẨN HÓA:
  - Trim khoảng trắng, chuẩn hóa format
  - Câu hỏi kết thúc bằng dấu "."
  - Chuẩn hóa LaTeX trong ${{...}}$ (bắt buộc)
  - NGOẶC TỰ ĐỘNG SCALE: TẤT CẢ ngoặc trong $...$ PHẢI dùng \\left...\\right
    (vd: ${{f\\left(x\\right)}}$, ${{\\left[1,2\\right]}}$, ${{\\left|x\\right|}}$).
    Nếu thấy `(` `[` `{{` `|` thường → SỬA thành \\left/\\right.

Bước 2 — PHÂN TÍCH & SỬA (style=smart cho phép):
  - Sửa: lỗi toán, sai đáp án, lỗi format
  - Có thể viết lại câu hỏi rõ ràng hơn nếu mơ hồ
  - Tối ưu wording các phương án cho cân bằng và rõ nghĩa
  - Bắt buộc giữ: ý nghĩa toán học, độ khó gần tương đương

Bước 3 — TỰ KIỂM TRA (bắt buộc):
  - Giải lại bài toán từ đầu
  - Kiểm tra từng phương án: chỉ 1 đúng, 3 sai hợp lý (không quá dễ đoán)
  - So sánh với đáp án → sửa nếu cần

Bước 4 — KIỂM TRA ĐỘ KHÓ:
  - Đánh giá: độ khó sau sửa có thay đổi nhiều so với ban đầu không?
  - Nếu thay đổi rõ rệt → difficulty_changed: true + ghi rõ trong notes

Bước 5 — VALIDATION:
  - Đúng 1 đáp án đúng
  - Lời giải ngắn gọn, chính xác, giải thích được tại sao đúng
  - Với câu DS: mỗi GIAI_x phải bắt đầu bằng "Đúng. Vì..." hoặc "Sai. Vì..."

Trả về JSON DUY NHẤT:
{{
  "final": {{
    "question": "...",
    "options": {{"A":"...","B":"...","C":"...","D":"..."}},
    "correct_answer": "A",
    "solution": "...",
    "items": {{}},
    "answers": {{}},
    "item_solutions": {{}}
  }},
  "is_corrected": true,
  "difficulty_changed": false,
  "confidence": 0.95,
  "notes": "Mô tả: đã sửa gì, tại sao, độ khó có thay đổi không"
}}
"""

# ── Prompt với few-shot cho generate ─────────────────────────────────────────

_GENERATE_SYSTEM = """\
Bạn là giáo viên Toán THPT Việt Nam giàu kinh nghiệm. \
Hãy soạn câu hỏi chất lượng cao theo đúng yêu cầu.\
"""

FEW_SHOT_BANK = {
    "TN":  _FEW_SHOT_TN,
    "NPA": _FEW_SHOT_TN,
    "DS":  _FEW_SHOT_DS,
}


def get_few_shot(qtype: str) -> str:
    """Trả về few-shot example cho loại câu hỏi tương ứng."""
    return FEW_SHOT_BANK.get(qtype, "")


# ══════════════════════════════════════════════════════════════════════════════
#  NORMALIZE — Bước 1 (không cần AI)
# ══════════════════════════════════════════════════════════════════════════════

def normalize_question(q: Question) -> Question:
    import copy
    nq = copy.deepcopy(q)

    nq.question = nq.question.strip()
    nq.solution = nq.solution.strip()

    if nq.question and not nq.question.endswith((".", "?", "!")):
        nq.question = nq.question + "."

    if nq.qtype in ("TN", "NPA"):
        nq.options = {k: v.strip() for k, v in nq.options.items()}
        nq.answer  = nq.answer.strip().upper()
        if nq.answer not in ("A", "B", "C", "D"):
            nq.answer = "A"

    elif nq.qtype == "DS":
        nq.items          = {k: v.strip() for k, v in nq.items.items()}
        nq.item_solutions = {k: v.strip() for k, v in nq.item_solutions.items()}

    return nq


# ══════════════════════════════════════════════════════════════════════════════
#  FIX — Bước 2-5 (dùng AI)
# ══════════════════════════════════════════════════════════════════════════════

def _question_to_fix_json(q: Question) -> str:
    data: dict = {
        "type":     q.qtype,
        "level":    q.level,
        "topic":    q.topic,
        "question": q.question,
        "solution": q.solution,
    }
    if q.qtype in ("TN", "NPA"):
        data["options"]        = q.options
        data["correct_answer"] = q.answer
    elif q.qtype == "DS":
        data["items"]          = q.items
        data["answers"]        = {k: ("D" if v else "S") for k, v in q.answers.items()}
        data["item_solutions"] = q.item_solutions
    else:
        data["answer"] = q.answer
        data["points"] = q.points
    return json.dumps(data, ensure_ascii=False, indent=2)


def _parse_fix_response(raw: str) -> Optional[dict]:
    m = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    text = m.group(1).strip() if m else raw.strip()
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return None


def apply_fix_result(original: Question, fix_result: dict) -> Question:
    import copy
    q = copy.deepcopy(original)
    final = fix_result.get("final", {})

    if "question" in final:
        q.question = final["question"]
    if "solution" in final:
        q.solution = final["solution"]

    if q.qtype in ("TN", "NPA"):
        if "options" in final:
            q.options = final["options"]
        if "correct_answer" in final:
            q.answer = final["correct_answer"]

    elif q.qtype == "DS":
        if "items" in final:
            q.items = final["items"]
        if "answers" in final:
            raw_ans = final["answers"]
            if isinstance(raw_ans, dict):
                q.answers = {
                    k: (v in ("D", "Đ", True, "true", "True", 1))
                    if not isinstance(v, bool) else v
                    for k, v in raw_ans.items()
                }
        if "item_solutions" in final:
            q.item_solutions = final["item_solutions"]

    elif q.qtype in ("TLN", "TL"):
        if "answer" in final:
            q.answer = final["answer"]

    q._review = {
        "is_corrected":      fix_result.get("is_corrected", False),
        "difficulty_changed": fix_result.get("difficulty_changed", False),
        "confidence":        fix_result.get("confidence", 0.5),
        "notes":             fix_result.get("notes", ""),
        "mode":              "fix",
    }
    q._error = False
    return q


def fix_question(
    q: Question,
    subject: str,
    grade: str,
    ai_call: Callable[[str], str],
    style_mode: str = "safe",
) -> tuple[Question, dict]:
    q_norm = normalize_question(q)
    q_json = _question_to_fix_json(q_norm)

    template = _FIX_PROMPT_SAFE if style_mode == "safe" else _FIX_PROMPT_SMART
    prompt = template.format(
        subject=subject,
        grade=grade,
        question_json=q_json,
    )

    last_raw = ""
    fix_result: Optional[dict] = None
    for attempt in range(3):
        try:
            raw = ai_call(prompt)
            last_raw = raw
            fix_result = _parse_fix_response(raw)
            if fix_result and "final" in fix_result:
                break
        except Exception:
            pass

    if not fix_result:
        meta = {
            "is_corrected":      False,
            "difficulty_changed": False,
            "confidence":        0.0,
            "notes":             "Không parse được phản hồi AI",
            "mode":              "fix",
        }
        q_norm._review = meta
        return q_norm, meta

    fixed_q = apply_fix_result(q_norm, fix_result)
    meta = {
        "is_corrected":      fix_result.get("is_corrected", False),
        "difficulty_changed": fix_result.get("difficulty_changed", False),
        "confidence":        fix_result.get("confidence", 0.5),
        "notes":             fix_result.get("notes", ""),
        "mode":              "fix",
        "style":             style_mode,
    }
    return fixed_q, meta


def fix_questions_batch(
    questions: list[Question],
    subject: str,
    grade: str,
    ai_call: Callable[[str], str],
    style_mode: str = "safe",
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
) -> list[dict]:
    results = []
    total = len(questions)

    for i, q in enumerate(questions):
        if progress_cb:
            progress_cb(i, total, q.topic)

        if q._error:
            results.append({
                "original":          q,
                "final":             q,
                "is_corrected":      False,
                "difficulty_changed": False,
                "confidence":        0.0,
                "notes":             "Câu lỗi — bỏ qua fix",
            })
            continue

        fixed_q, meta = fix_question(q, subject, grade, ai_call, style_mode)
        results.append({
            "original":          q,
            "final":             fixed_q,
            "is_corrected":      meta["is_corrected"],
            "difficulty_changed": meta["difficulty_changed"],
            "confidence":        meta["confidence"],
            "notes":             meta["notes"],
        })

    return results


def to_fix_output_json(results: list[dict]) -> str:
    output_questions = []
    for r in results:
        orig: Question = r["original"]
        final: Question = r["final"]

        def q_to_output(q: Question) -> dict:
            d = {
                "question": q.question,
                "solution": q.solution,
            }
            if q.qtype in ("TN", "NPA"):
                d["options"]        = q.options
                d["correct_answer"] = q.answer
            elif q.qtype == "DS":
                d["items"]          = q.items
                d["answers"]        = {k: ("D" if v else "S") for k, v in q.answers.items()}
                d["item_solutions"] = q.item_solutions
            else:
                d["answer"] = q.answer
                d["points"] = q.points
            return d

        output_questions.append({
            "original":          q_to_output(orig),
            "final":             q_to_output(final),
            "is_corrected":      r["is_corrected"],
            "difficulty_changed": r["difficulty_changed"],
            "confidence":        r["confidence"],
            "notes":             r["notes"],
        })

    return json.dumps({"questions": output_questions}, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
#  SCORE VALIDATOR — Kiểm tra tổng điểm đề
# ══════════════════════════════════════════════════════════════════════════════

def validate_exam_score(questions: list[Question]) -> dict:
    from config import POINTS_MAP

    breakdown: dict[str, float] = {}
    total = 0.0

    for q in questions:
        if q._error:
            continue
        pts = POINTS_MAP.get(q.qtype, q.points)
        if q.qtype == "TN":
            pts = 0.25
        elif q.qtype == "DS":
            pts = 1.0
        elif q.qtype == "TLN":
            pts = q.points if q.points else 0.5
        elif q.qtype == "TL":
            pts = q.points if q.points else 1.0
        key = q.qtype
        breakdown[key] = breakdown.get(key, 0.0) + pts
        total += pts

    ok = abs(total - 10.0) < 0.01
    warning = None
    if not ok:
        diff = total - 10.0
        if diff > 0:
            warning = f"Đề dư {diff:.2f}đ so với 10đ"
        else:
            warning = f"Đề thiếu {abs(diff):.2f}đ so với 10đ"

    return {
        "total":     round(total, 2),
        "ok":        ok,
        "breakdown": {k: round(v, 2) for k, v in breakdown.items()},
        "warning":   warning,
    }