"""
services/ai_variant_generator.py — Sinh đề tương tự bằng AI (AI chỉ thay số).

Triết lý:
  • AI KHÔNG tạo đề mới, KHÔNG đổi dạng toán.
  • AI nhận đề gốc → giữ nguyên cấu trúc → thay các con số → tính lại.
  • Output là JSON danh sách biến thể, mỗi phần tử là Question đã thay số +
    đáp án mới đã tính.
  • So với `similar_generator.py` (pure Python/sympy): rộng hơn vì không bị
    giới hạn các dạng mà regex/sympy parse được. Đánh đổi: chậm + tốn API + cần
    validation sau.

Luồng dùng:
    from services.ai_variant_generator import generate_ai_variants
    variants = generate_ai_variants(question, n=4, ai_call=ai_call)
    # variants: list[Question]

`ai_call` là callable nhận prompt str → trả về response str (đã được parent
build sẵn từ `main_window._make_ai_call()`).
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import asdict
from typing import Any, Callable, List, Optional


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT
# ══════════════════════════════════════════════════════════════════════════════

_VARIANT_PROMPT = r"""Bạn là một AI kỹ sư xử lý hậu kỳ dữ liệu toán học.

Bạn KHÔNG tạo đề mới. Bạn KHÔNG đổi dạng toán. Bạn KHÔNG đổi ngôn ngữ.
Công việc của bạn: NHẬN 1 câu hỏi gốc (đã được AI khác tạo đúng) rồi
sinh ra $N$ phiên bản câu hỏi tương tự bằng cách:

  1. Giữ NGUYÊN cấu trúc câu, dạng toán, từ ngữ, cách diễn đạt.
  2. BẢO TOÀN ĐỘ KHÓ: Tuyệt đối giữ nguyên mức độ nhận thức (Nhận biết/Thông hiểu/Vận dụng).
     KHÔNG làm bài toán trở nên quá khó hoặc quá cồng kềnh.
     Ưu tiên các con số vừa phải, nghiệm đẹp (nguyên hoặc phân số đơn giản).
  3. Chỉ thay các CON SỐ (hệ số, hằng số, tham số, toạ độ điểm gán…) sao cho:
        - Các số mới hợp lý cho cấp lớp và bối cảnh của đề.
        - Đáp án mới tính được chính xác.
        - Phương trình/biểu thức không suy biến (mẫu ≠ 0, Δ hợp lý…).
  4. TÍNH LẠI đáp án đúng cho mỗi phiên bản. TUYỆT ĐỐI KHÔNG giữ đáp án gốc.
  5. Với Trắc nghiệm (TN): sinh lại toàn bộ 4 lựa chọn A/B/C/D, trong đó 1
     lựa chọn đúng là đáp án mới. Các distractor phải là lỗi sai hợp lý
     (nhầm dấu, sai căn bậc hai, sai công thức nghiệm…).
  6. Với Đúng/Sai (DS): sinh lại 4 items a/b/c/d + đáp án (đúng/sai) từng ý.
  7. Giải thích lời giải (solution) phải được viết lại với số mới.

INPUT JSON — đề gốc:
$INPUT_JSON

SỐ LƯỢNG biến thể cần sinh: $N

OUTPUT BẮT BUỘC: trả về duy nhất 1 JSON hợp lệ, không thêm text/markdown:

{
  "variants": [
    {
      "question": "<nội dung câu hỏi — giống cấu trúc gốc, chỉ khác số>",
      "solution": "<lời giải đã viết lại với số mới>",
      "options":  {"A": "...", "B": "...", "C": "...", "D": "..."},   // chỉ TN
      "answer":   "A",                                                 // chỉ TN; ký tự A/B/C/D
      "items":    {"a": "...", "b": "...", "c": "...", "d": "..."},    // chỉ DS
      "answers":  {"a": true, "b": false, "c": true, "d": false}       // chỉ DS
    }
  ]
}

QUY TẮC BẮT BUỘC VỀ CÔNG THỨC TOÁN (BẢO TOÀN MATHTYPE / WORD MATH):
  • LaTeX: CHỈ dùng "${...}$" — luôn có cặp { } bọc trong cặp $ $.
        ĐÚNG : ${x^2 - 5x + 6 = 0}$, ${\frac{1}{2}}$, ${\sqrt{x+1}}$, ${\begin{cases} x+y=1 \\ x-y=2 \end{cases}}$
        SAI  : $x^2 - 5x + 6 = 0$              ← thiếu { }
        SAI  : $$\int_0^1 x^2\,dx$$            ← CẤM $$ ... $$
        SAI  : \(x^2\), \[x^2\]                ← CẤM \( \) và \[ \]
  • Lý do: Hệ thống xuất Word MathType/OMML chỉ nhận diện chuẩn ${...}$.
  • Số nguyên nhỏ (trong khoảng -15..15) được ưu tiên cho đề cơ bản.
  • KHÔNG đổi qtype, level, topic, requirement — chỉ thay số.
  • KHÔNG copy y nguyên số gốc cho bất kỳ biến thể nào (phải khác hẳn).
  • Với TN: đáp án đúng phải tính ra được; các distractor KHÔNG trùng đáp án đúng.
"""


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT THỦ CÔNG — user copy & dán vào ChatGPT/Claude/Gemini (KHÔNG tốn API)
# ══════════════════════════════════════════════════════════════════════════════
#
# Dùng khi người dùng muốn tự gửi đề Word sang chatbot bên ngoài:
#   1. Xuất 1 file Word gốc từ app này.
#   2. Mở ChatGPT / Claude / Gemini (bản web miễn phí).
#   3. Upload file Word.
#   4. Paste prompt dưới đây.
#   5. AI trả về đề tương tự cùng cấu trúc, chỉ khác số liệu.
#
# Prompt được viết cực kỳ chi tiết: chỉ thay số, tính lại đáp án, LaTeX bắt buộc
# trong $...$ / $$...$$, distractor không trùng đáp án đúng, v.v.

MANUAL_VARIANT_PROMPT = r"""Bạn là AI kỹ sư xử lý hậu kỳ đề toán bậc THPT.

NHIỆM VỤ
Bạn nhận 1 FILE WORD (.docx) đề thi đính kèm trong tin nhắn này.
Hãy tạo MÃ ĐỀ TƯƠNG TỰ — GIỮ NGUYÊN cấu trúc, thứ tự, định dạng — CHỈ THAY SỐ.

════════════════════════════════════════════════════════════════════════
[★] TUỲ CHỌN CỦA TÔI — ĐIỀN VÀO [...] TRƯỚC KHI GỬI
════════════════════════════════════════════════════════════════════════
• Số mã đề cần sinh           : [1]
• Khoảng số nguyên ưu tiên     : [-15..15]   (cho đề cơ bản; đổi sang [-50..50] cho VD)
• Có giữ y nguyên ngữ cảnh đề  : [Có/Không] (mặc định Có)
• Yêu cầu thêm                 : [VD: tránh đáp án 0 và 1; nghiệm phải nguyên; ...]

════════════════════════════════════════════════════════════════════════
QUY TẮC TUYỆT ĐỐI — KHÔNG ĐƯỢC VI PHẠM BẤT KỲ ĐIỀU NÀO
════════════════════════════════════════════════════════════════════════

1. GIỮ NGUYÊN 100% CẤU TRÚC FILE WORD GỐC
   • Đúng số câu, đúng thứ tự câu.
   • Đúng thứ tự các phần (Phần I/II/III, TN / Đúng–Sai / Tự luận…).
   • Đúng 4 lựa chọn A/B/C/D cho câu trắc nghiệm.
   • Đúng 4 ý a/b/c/d cho câu Đúng/Sai.
   • Đúng các đoạn văn dẫn, tiêu đề, ghi chú, điểm số.
   • KHÔNG thêm, KHÔNG xoá, KHÔNG đổi loại câu, KHÔNG viết lại đề mới.

2. CHỈ ĐƯỢC PHÉP THAY CÁC CON SỐ
   • Các hệ số, hằng số, tham số, điểm gán, toạ độ, độ dài, góc…
   • Ưu tiên số trong khoảng do user chọn ở mục [★] (mặc định −15..15).
   • Số mới BẮT BUỘC khác số gốc (không copy lại bất kỳ con số nào).
   • Tránh suy biến toán học:
        – Mẫu số ≠ 0.
        – Biệt thức Δ ≥ 0 nếu đề yêu cầu nghiệm thực.
        – Nghiệm/đáp án ra số "đẹp" (ưu tiên nguyên, phân số đơn giản).

3. TÍNH LẠI ĐÁP ÁN THEO SỐ MỚI
   • TUYỆT ĐỐI KHÔNG giữ đáp án cũ.
   • Với mọi câu, tự kiểm tra bằng cách thay nghiệm ngược vào biểu thức gốc.
   • Lời giải / "Hướng dẫn giải" (nếu file gốc có) phải được viết lại với số mới.

4. VỚI CÂU TRẮC NGHIỆM (TN)
   • Sinh lại cả 4 lựa chọn A/B/C/D.
   • Đúng 1 đáp án đúng. 3 distractor phải là LỖI SAI HỢP LÝ mà học sinh
     thường mắc: sai dấu, sai căn bậc hai, quên chia hệ số, nhầm công thức
     nghiệm, sai điều kiện xác định, v.v.
   • Không distractor nào được trùng đáp án đúng, không trùng nhau.

5. VỚI CÂU ĐÚNG/SAI (DS)
   • Sinh lại đủ 4 ý a/b/c/d.
   • Mỗi ý đánh dấu rõ: Đúng hoặc Sai.

6. CÔNG THỨC TOÁN — CHỈ DÙNG ${...}$ (KHÔNG dùng $$...$$)
   • CHỈ MỘT định dạng duy nhất: ${biểu_thức}$ — luôn có cặp { } bọc
     trong cặp $ $.
        ĐÚNG : ${x^2 - 5x + 6 = 0}$
        ĐÚNG : ${\frac{1}{2}}$, ${\sqrt{x+1}}$, ${\int_0^1 x^2\,dx}$
        SAI  : $x^2 - 5x + 6 = 0$            ← thiếu { }
        SAI  : $$\int_0^1 x^2\,dx$$          ← CẤM $$ ... $$
        SAI  : \(x^2\), \[x^2\]              ← CẤM \( \) và \[ \]
   • Lý do: app chỉ render đúng dạng ${...}$. $$ ... $$ hay \( \) sẽ bị
     hỏng định dạng khi import lại vào app.
   • CẤM Unicode ký hiệu toán trực tiếp:
        – SAI : x² − 5x + 6 = 0   |  ĐÚNG : ${x^2 - 5x + 6 = 0}$
        – SAI : √(x+1)             |  ĐÚNG : ${\sqrt{x+1}}$
        – SAI : ≤, ≥, ≠            |  ĐÚNG : ${\leq}$, ${\geq}$, ${\neq}$
        – SAI : π, α, β             |  ĐÚNG : ${\pi}$, ${\alpha}$, ${\beta}$
   • Phân số ${\frac{a}{b}}$, căn ${\sqrt{x}}$, mũ ${x^{n}}$,
     chỉ số ${a_{n}}$. Dấu nhân ${\cdot}$ — KHÔNG dùng × hay *.
   • Ngoặc bao biểu thức cao: dùng \left( \right), \left[ \right],
     \left\{ \right\}, \left| \right|.
   • Ký hiệu góc: ${\widehat{ABC}}$ — KHÔNG dùng ${\angle ABC}$.

ĐỊNH DẠNG TRẢ VỀ

Trả về text thuần theo MẪU dưới đây (KHÔNG thêm ```markdown```, KHÔNG thêm
lời chào, KHÔNG giải thích trước/sau):

────────────────────────────────────────
PHẦN I. TRẮC NGHIỆM

Câu 1: [nội dung câu hỏi, công thức trong ${...}$]
A. [lựa chọn A]
B. [lựa chọn B]
C. [lựa chọn C]
D. [lựa chọn D]
Đáp án: [A/B/C/D]
Lời giải: [lời giải chi tiết với số mới]

Câu 2: ...

PHẦN II. ĐÚNG/SAI

Câu 1: [đề dẫn chung]
a) [mệnh đề a]  →  [Đúng/Sai]
b) [mệnh đề b]  →  [Đúng/Sai]
c) [mệnh đề c]  →  [Đúng/Sai]
d) [mệnh đề d]  →  [Đúng/Sai]
Lời giải: [giải thích từng ý — bắt đầu "Đúng. Vì..." hoặc "Sai. Vì..."]

PHẦN III. TRẢ LỜI NGẮN / TỰ LUẬN

Câu 1: [nội dung]
Đáp án: [kết quả; với TLN: số tối đa 4 ký tự, dấu , VN: VD 0,5]
Lời giải: [chi tiết, viết liền mạch không chia "Bước 1/2"]
────────────────────────────────────────

VÍ DỤ MỘT CÂU TN ĐÚNG ĐỊNH DẠNG (chú ý mọi ${...}$ đều có { }):

Câu 1: Giải phương trình ${x^2 - 5x + 6 = 0}$, ta được tập nghiệm là:
A. ${\left\{1;\,6\right\}}$
B. ${\left\{2;\,3\right\}}$
C. ${\left\{-2;\,-3\right\}}$
D. ${\left\{0;\,5\right\}}$
Đáp án: B
Lời giải: Ta có ${\Delta = 25 - 24 = 1 > 0}$. Nghiệm
${x = \frac{5 \pm 1}{2}}$, tức ${x_1 = 2}$ hoặc ${x_2 = 3}$.

(Chỉ giữ các phần nào TỒN TẠI trong file Word gốc. Nếu gốc không có Đúng/Sai
thì không sinh Đúng/Sai.)

Nếu user yêu cầu nhiều mã đề (ví dụ [3]), in lần lượt:
   ===== MÃ ĐỀ 1 =====
   ...
   ===== MÃ ĐỀ 2 =====
   ...
Mỗi mã đề CÓ BỘ SỐ KHÁC NHAU.

CHECKLIST BẮT BUỘC TỰ KIỂM TRA TRƯỚC KHI TRẢ LỜI

[ ] Đã giữ đúng thứ tự và số câu như file Word gốc.
[ ] Tất cả con số đã khác đề gốc (không có số nào trùng).
[ ] Đã tính lại đáp án cho TỪNG câu, đã thay ngược để kiểm tra.
[ ] MỌI công thức nằm trong ${...}$ — có { và } bọc trong cặp $.
[ ] KHÔNG có $$...$$, KHÔNG có \(...\), KHÔNG có \[...\].
[ ] Không dùng Unicode ký hiệu toán (×, ÷, ², ³, √, ≠, ≤, ≥, π, α, β).
[ ] Trắc nghiệm có đủ 4 lựa chọn, 1 đúng 3 distractor không trùng nhau.
[ ] Lời giải viết lại theo số mới, không copy lời giải gốc.
[ ] Số mã đề trả về đúng bằng giá trị user điền ở mục [★].

BẮT ĐẦU TRẢ LỜI NGAY — không mở đầu bằng "Được rồi", "Đã hiểu", hoặc giải thích.
"""


def get_manual_variant_prompt() -> str:
    """Trả về prompt để người dùng copy sang chatbot bên ngoài.

    Tách thành hàm để UI có thể gọi mà không cần import biến module-level
    (dễ hot-patch / tuỳ biến sau này).
    """
    return MANUAL_VARIANT_PROMPT


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS: serialize Question → JSON cho AI đọc
# ══════════════════════════════════════════════════════════════════════════════

def _question_to_dict(q: Any) -> dict:
    """Chuyển Question → dict JSON-friendly, loại bỏ metadata nội bộ."""
    PUBLIC_FIELDS = (
        "qtype", "level", "topic", "question", "solution",
        "options", "answer", "items", "answers", "item_solutions",
        "requirement", "points", "tikz_code",
    )
    d: dict = {}
    for f in PUBLIC_FIELDS:
        if hasattr(q, f):
            v = getattr(q, f)
            if v or isinstance(v, (int, float, bool)):
                d[f] = v
    return d


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS: parse JSON trả về từ AI (an toàn với text thừa)
# ══════════════════════════════════════════════════════════════════════════════

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)
_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_json(text: str) -> Optional[dict]:
    """Trích JSON hợp lệ từ response AI. Thử fence trước, sau đó raw."""
    if not text:
        return None
    # Fence ```json { ... } ```
    m = _FENCE_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # Raw: lấy { ... } đầu tiên (greedy)
    m = _JSON_BLOCK_RE.search(text)
    if m:
        s = m.group(0)
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            # Thử cắt dần từ cuối nếu có text thừa
            for end in range(len(s), 0, -1):
                try:
                    return json.loads(s[:end])
                except json.JSONDecodeError:
                    continue
    return None


# ══════════════════════════════════════════════════════════════════════════════
# API CHÍNH
# ══════════════════════════════════════════════════════════════════════════════

def build_variant_prompt(question: Any, n: int) -> str:
    """Ghép prompt để AI sinh biến thể. Dùng $INPUT_JSON / $N để tránh xung đột
    với các dấu ngoặc nhọn trong LaTeX (không dùng .format())."""
    q_dict = _question_to_dict(question)
    input_json = json.dumps(q_dict, ensure_ascii=False, indent=2)
    prompt = _VARIANT_PROMPT.replace("$INPUT_JSON", input_json)
    prompt = prompt.replace("$N", str(n))
    return prompt


def generate_ai_variants(
    question: Any,
    n: int,
    ai_call: Callable[[str], str],
    max_retry: int = 2,
) -> List[Any]:
    """Gọi AI thay số cho 1 Question, trả về list Question mới.

    Parameters
    ----------
    question:   Question gốc
    n:          số biến thể cần sinh
    ai_call:    callable(prompt: str) -> response: str
    max_retry:  thử lại khi AI trả JSON hỏng (tăng N mỗi lần để giảm xác suất lặp)

    Returns
    -------
    list[Question] — có thể ít hơn n nếu AI trả thiếu
    """
    if n <= 0:
        return []

    prompt = build_variant_prompt(question, n)
    variants: list = []

    for attempt in range(max_retry):
        try:
            resp = ai_call(prompt)
        except Exception:
            continue
        data = _extract_json(resp) if resp else None
        if not data:
            continue
        raw_list = data.get("variants") or []
        if not isinstance(raw_list, list):
            continue
        variants = _apply_variants(question, raw_list)
        if variants:
            break

    return variants[:n]


def _apply_variants(src_question: Any, raw_list: list) -> List[Any]:
    """Áp dụng các dict từ AI vào bản copy của src_question."""
    out: list = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        new_q = copy.deepcopy(src_question)
        # Các trường override
        for key in ("question", "solution"):
            if key in item and isinstance(item[key], str):
                setattr(new_q, key, item[key])
        # TN
        if getattr(new_q, "qtype", "") == "TN":
            opts = item.get("options")
            ans = item.get("answer")
            if isinstance(opts, dict) and isinstance(ans, str):
                # Đảm bảo 4 key A/B/C/D đầy đủ
                clean_opts = {k: str(opts.get(k, "")) for k in ("A", "B", "C", "D")}
                if any(clean_opts.values()):
                    new_q.options = clean_opts
                if ans.upper() in ("A", "B", "C", "D"):
                    new_q.answer = ans.upper()
        # DS
        elif getattr(new_q, "qtype", "") == "DS":
            items = item.get("items")
            answers = item.get("answers")
            if isinstance(items, dict):
                new_q.items = {k: str(items.get(k, "")) for k in ("a", "b", "c", "d")
                               if k in items}
            if isinstance(answers, dict):
                new_q.answers = {k: bool(answers.get(k)) for k in ("a", "b", "c", "d")
                                 if k in answers}
        # Cờ variant
        try:
            new_q._variant = True
        except Exception:
            pass
        out.append(new_q)
    return out


def generate_ai_variant_exam(
    exam_data: Any,
    ai_call: Callable[[str], str],
    progress_cb: Optional[Callable[[int, int], None]] = None,
    max_retry: int = 2,
) -> "tuple[Any, int, int]":
    """Gọi AI thay số cho TOÀN BỘ exam, mỗi câu sinh 1 biến thể.

    Parameters
    ----------
    exam_data:    ExamData gốc
    ai_call:      callable(prompt) -> str
    progress_cb:  callback(i_current, n_total) để báo tiến độ
    max_retry:    thử lại AI khi lỗi

    Returns
    -------
    (new_exam, n_replaced, n_kept)
    """
    new_exam = copy.deepcopy(exam_data)
    total = len(new_exam.questions)
    n_replaced = 0
    n_kept = 0
    for i, q in enumerate(new_exam.questions):
        if progress_cb:
            try:
                progress_cb(i + 1, total)
            except Exception:
                pass
        variants = generate_ai_variants(q, n=1, ai_call=ai_call, max_retry=max_retry)
        if variants:
            new_exam.questions[i] = variants[0]
            n_replaced += 1
        else:
            n_kept += 1
    return new_exam, n_replaced, n_kept


def generate_ai_variants_for_sections(
    sections: List[Any],
    ai_call: Callable[[str], str],
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
    max_retry: int = 2,
) -> "tuple[List[Any], int, int]":
    """Gọi AI thay số cho TOÀN BỘ các câu hỏi trong List[ExamSection].
    Bảo toàn dạng toán, cấu trúc và mức độ khó của đề thi.

    Returns
    -------
    (new_sections, n_replaced, n_kept)
    """
    from core.models import Question
    from omr_exam.models import OptionItem

    new_sections = copy.deepcopy(sections)
    total_qs = sum(len(s.questions) for s in new_sections)
    current_count = 0
    n_replaced = 0
    n_kept = 0

    for s in new_sections:
        for i, eq in enumerate(s.questions):
            current_count += 1
            if progress_cb:
                try:
                    progress_cb(current_count, total_qs, f"Đang đổi số câu {eq.index} ({eq.qtype})...")
                except Exception:
                    pass

            # Chuyển ExamQuestion -> Question để dùng chung bộ sinh AI
            q_opts = {opt.label: opt.text for opt in getattr(eq, "options", [])}
            q_model = Question(
                qtype=getattr(eq, "qtype", "TN"),
                level="TH",
                topic=getattr(eq, "section", ""),
                question=getattr(eq, "content", ""),
                options=q_opts,
                answer=getattr(eq, "correct_label", ""),
            )

            variants = generate_ai_variants(q_model, n=1, ai_call=ai_call, max_retry=max_retry)
            if variants:
                var_q = variants[0]
                eq.content = var_q.question
                if getattr(eq, "qtype", "TN") == "TN" and getattr(var_q, "options", None):
                    new_options = []
                    new_correct = (var_q.answer or "").upper()
                    for lbl in ("A", "B", "C", "D"):
                        txt = str(var_q.options.get(lbl, ""))
                        new_options.append(OptionItem(
                            label=lbl,
                            text=txt,
                            is_correct=(lbl == new_correct),
                        ))
                    eq.options = new_options
                    eq.correct_label = new_correct
                n_replaced += 1
            else:
                n_kept += 1

    return new_sections, n_replaced, n_kept


def sections_to_exam_data(sections: List[Any], title: str = "ĐỀ THI") -> Any:
    """Chuyển danh sách ExamSection thành ExamData để xuất file Word chuẩn MEA."""
    from core.models import ExamData, Question

    questions: list[Question] = []
    for s in sections:
        for eq in s.questions:
            q_opts = {opt.label: opt.text for opt in getattr(eq, "options", [])}
            q = Question(
                qtype=getattr(eq, "qtype", "TN"),
                level="TH",
                topic=s.title,
                question=getattr(eq, "content", ""),
                options=q_opts,
                answer=getattr(eq, "correct_label", ""),
            )
            questions.append(q)

    return ExamData(
        exam_title=title,
        questions=questions,
    )

