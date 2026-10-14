"""
core/natural_parser.py — Parse văn bản câu hỏi TỰ NHIÊN (không có khung
===CAU===/===KETCAU===) thành list[Question].

Mục đích:
  • Tab "AI Text → Câu hỏi" nhận văn bản paste từ ChatGPT / Word / PDF.
  • Đa số chatbot trả về dạng "Câu 1: … A. … B. … Đáp án: A" — ta PARSE TRỰC
    TIẾP thay vì tốn thêm 1 lượt gọi AI để chuyển sang ===CAU===.
  • Khi parser này nhận diện được ≥ 1 câu, UI dùng kết quả này; nếu không
    nhận diện được câu nào thì FALLBACK sang gọi AI "đồng bộ cấu trúc".

Hỗ trợ 4 loại câu hỏi theo chuẩn MEA:
  • TN  (trắc nghiệm, 4 phương án A/B/C/D)
  • DS  (đúng–sai, 4 ý a/b/c/d)
  • TLN (trả lời ngắn, đáp số là 1 con số / 1 biểu thức)
  • TL  (tự luận)

API:
    >>> from core.natural_parser import parse_natural_questions
    >>> qs = parse_natural_questions(text)
    >>> len(qs), qs[0].qtype
    (5, 'TN')

Quy ước nhận diện:
  • Tiêu đề câu: "Câu 1:", "Câu 1.", "Câu 1)", "Bài 1:", "CÂU 1:".
  • Phương án TN: "A.", "A)", "(A)", "A:" ở đầu dòng.
  • Ý DS:         "a)", "a.", "a:" ở đầu dòng kèm "Đ / S / Đúng / Sai" phía sau.
  • Đáp án:       "Đáp án:", "ĐA:", "Đ/A:", "Đáp số:", "Answer:".
  • Lời giải:     "Lời giải:", "Giải:", "Hướng dẫn giải:", "Hướng dẫn:".

Parser KHÔNG cố gắng "sửa" nội dung — giữ nguyên toàn bộ text người nhập.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from core.models import Question
# Regex chung — Single Source of Truth. Nếu cần tinh chỉnh "Câu N:" hay
# "A.", chỉ sửa ở core.question_parser_common.
from core.question_parser_common import (
    Q_HEADER_RE       as _Q_HEADER_RE,
    TN_OPT_RE         as _TN_OPT_RE,
    DS_ITEM_RE        as _DS_ITEM_RE,
    ANSWER_RE         as _ANSWER_RE,
    SOLUTION_RE       as _SOLUTION_RE,
    DS_MARK_TRUE      as _DS_MARK_TRUE,
    DS_MARK_FALSE     as _DS_MARK_FALSE,
    DS_MARK_TRUE_START as _DS_MARK_TRUE_START,
    DS_MARK_FALSE_START as _DS_MARK_FALSE_START,
    DS_ANSWER_TOKEN_RE as _DS_ANSWER_TOKEN_RE,
    sanitize_question_objects as _sanitize,
)

_log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def parse_natural_questions(text: str) -> list[Question]:
    """Parse văn bản tự nhiên → list[Question]. KHÔNG raise.

    Trả về list rỗng nếu không nhận diện được câu nào (để UI biết cần fallback
    sang AI).
    """
    if not text or not text.strip():
        return []

    # Loại bỏ các thẻ citation [cite: ...]
    text = re.sub(r"\[cite[a-z]*:\s*[\d,\s]+\]", "", text, flags=re.IGNORECASE)

    blocks = _split_into_blocks(text)
    if not blocks:
        return []

    questions: list[Question] = []
    for header_num, block_lines in blocks:
        q = _parse_block(block_lines)
        if q is not None:
            questions.append(q)

    # Bảo vệ downstream: clip text quá dài, log warning nếu AI trả dữ liệu lạ.
    sanitized, _warnings = _sanitize(questions, logger=_log)
    return sanitized


# ══════════════════════════════════════════════════════════════════════════════
#  SPLIT — tách text thành các block "Câu N: …"
# ══════════════════════════════════════════════════════════════════════════════

def _split_into_blocks(text: str) -> list[tuple[int, list[str]]]:
    """Tách text thành list (question_number, lines_of_block).

    Dòng "Câu N:" (và các biến thể) mở đầu block mới. Mọi dòng trước tiêu đề
    đầu tiên đều bị bỏ (lời chào chatbot, "Dưới đây là…").
    """
    lines = [ln.rstrip() for ln in text.splitlines()]

    blocks: list[tuple[int, list[str]]] = []
    current_num: Optional[int] = None
    current_lines: list[str] = []

    for ln in lines:
        m = _Q_HEADER_RE.match(ln)
        if m:
            # Flush block cũ
            if current_num is not None and current_lines:
                blocks.append((current_num, current_lines))
            current_num = int(m.group(1))
            # Bỏ phần "Câu N:" khỏi dòng, giữ phần còn lại
            rest = _Q_HEADER_RE.sub("", ln, count=1).strip()
            current_lines = [rest] if rest else []
        else:
            if current_num is not None:
                current_lines.append(ln)

    if current_num is not None and current_lines:
        blocks.append((current_num, current_lines))

    return blocks


# ══════════════════════════════════════════════════════════════════════════════
#  PARSE — 1 block thành Question
# ══════════════════════════════════════════════════════════════════════════════

def _parse_block(lines: list[str]) -> Optional[Question]:
    """Parse 1 block lines → Question. Trả None nếu invalid."""
    # 3 vùng: question_body, options/items, answer/solution
    question_lines: list[str] = []
    tn_options: dict[str, str] = {}
    ds_items: dict[str, str] = {}
    ds_inline_answers: dict[str, bool] = {}  # đáp án đoán từ "Đúng/Sai" cuối ý
    answer_raw: str = ""
    solution_lines: list[str] = []

    mode = "question"   # "question" | "options" | "solution"
    pending_opt_key: Optional[str] = None
    pending_opt_is_ds: bool = False

    def _flush_pending_opt(buf: str) -> None:
        nonlocal pending_opt_key, pending_opt_is_ds
        pending_opt_key = None
        pending_opt_is_ds = False

    def _append_to_pending(text: str) -> bool:
        """Nếu đang có option/item mở dang — nối tiếp vào. Trả True nếu nối."""
        nonlocal pending_opt_key, pending_opt_is_ds
        if pending_opt_key is None:
            return False
        store = ds_items if pending_opt_is_ds else tn_options
        store[pending_opt_key] = (store.get(pending_opt_key, "") + " " + text).strip()
        return True

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            # Dòng trống ở giữa — reset pending option, không nối nữa
            pending_opt_key = None
            continue

        # 1) Đáp án?
        m_ans = _ANSWER_RE.match(line)
        if m_ans:
            answer_raw = (m_ans.group(1) or "").strip()
            mode = "solution"
            pending_opt_key = None
            continue

        # 2) Lời giải?
        m_sol = _SOLUTION_RE.match(line)
        if m_sol:
            rest = (m_sol.group(1) or "").strip()
            if rest:
                solution_lines.append(rest)
            mode = "solution"
            pending_opt_key = None
            continue

        if mode == "solution":
            solution_lines.append(line)
            continue

        # 3) Phương án TN: "A. ...", "B) ...", v.v. — chỉ ở chế độ options/question
        m_tn = _TN_OPT_RE.match(line)
        if m_tn:
            key = m_tn.group(1).upper()
            if key in "ABCD":
                content = m_tn.group(2).strip()
                tn_options[key] = content
                pending_opt_key, pending_opt_is_ds = key, False
                mode = "options"
                continue

        # 4) Ý DS: "a) ...", "b. ...", "(c) ..."
        m_ds = _DS_ITEM_RE.match(line)
        if m_ds:
            key = m_ds.group(1).lower()
            if key in "abcd":
                content = m_ds.group(2).strip()
                # 1) "Đúng:" / "Sai:" / "(Đúng)" ở ĐẦU ý — strip + suy đáp án
                ms_t = _DS_MARK_TRUE_START.match(content)
                ms_f = _DS_MARK_FALSE_START.match(content)
                if ms_t:
                    ds_inline_answers[key] = True
                    content = _DS_MARK_TRUE_START.sub("", content, count=1).strip()
                elif ms_f:
                    ds_inline_answers[key] = False
                    content = _DS_MARK_FALSE_START.sub("", content, count=1).strip()
                # 2) Hoặc "Đúng/Sai" ở CUỐI ý — strip + suy đáp án
                mark_true  = _DS_MARK_TRUE.search(content)
                mark_false = _DS_MARK_FALSE.search(content)
                if mark_true and (not mark_false or mark_true.start() > mark_false.start()):
                    ds_inline_answers[key] = True
                    content = _DS_MARK_TRUE.sub("", content).strip(" .,;")
                elif mark_false:
                    ds_inline_answers[key] = False
                    content = _DS_MARK_FALSE.sub("", content).strip(" .,;")
                ds_items[key] = content
                pending_opt_key, pending_opt_is_ds = key, True
                mode = "options"
                continue

        # 5) Dòng không match — nối vào question hoặc option mở dang
        if mode == "question":
            question_lines.append(line)
        elif mode == "options":
            if not _append_to_pending(line):
                # Không có option mở dang → coi như phần tiếp của câu hỏi
                question_lines.append(line)

    # ────────────────────────────────────────────────────────────────────────
    # Xác định loại câu và build Question
    # ────────────────────────────────────────────────────────────────────────

    q_text = "\n".join(question_lines).strip()
    if not q_text:
        return None

    n_tn = sum(1 for k in "ABCD" if tn_options.get(k, "").strip())
    n_ds = sum(1 for k in "abcd" if ds_items.get(k, "").strip())

    # Heuristic ưu tiên: nếu có ≥ 3 phương án A-D và < 3 ý a-d → TN
    #                    nếu có ≥ 3 ý a-d và < 3 phương án A-D → DS
    #                    nếu cả hai đều có ≥ 3 → TN (ưu tiên, DS hiếm hơn)
    if n_tn >= 3 and n_ds < 3:
        return _build_tn(q_text, tn_options, answer_raw, solution_lines)

    if n_ds >= 3:
        return _build_ds(q_text, ds_items, ds_inline_answers, answer_raw,
                         solution_lines)

    # Không có options/items → TLN hoặc TL
    if answer_raw:
        # Có "Đáp án: X" → TLN nếu X có vẻ là đáp số ngắn gọn
        # Nếu X chứa ≥ 100 ký tự thì coi như TL (lời giải).
        if len(answer_raw) <= 80:
            return _build_tln(q_text, answer_raw, solution_lines)
        # Dài → TL, answer_raw thành phần đầu solution
        solution_lines.insert(0, answer_raw)

    return _build_tl(q_text, solution_lines)


# ══════════════════════════════════════════════════════════════════════════════
#  BUILDERS — 1 cho mỗi qtype
# ══════════════════════════════════════════════════════════════════════════════

def _build_tn(q_text: str, options: dict[str, str], answer_raw: str,
              solution_lines: list[str]) -> Optional[Question]:
    # Đảm bảo đủ 4 option
    for k in "ABCD":
        options.setdefault(k, "")
    if not all(options[k].strip() for k in "ABCD"):
        return None

    answer = ""
    if answer_raw:
        m = re.search(r"[A-D]", answer_raw.upper())
        if m:
            answer = m.group(0)
    if answer not in "ABCD":
        return None  # Không có đáp án rõ ràng → bỏ qua để AI xử lý

    return Question(
        qtype="TN",
        level="TH",
        topic="",
        question=q_text,
        options=dict(options),
        answer=answer,
        solution="\n".join(solution_lines).strip(),
    )


def _build_ds(q_text: str, items: dict[str, str],
              inline_answers: dict[str, bool], answer_raw: str,
              solution_lines: list[str]) -> Optional[Question]:
    # Parse "a=Đ, b=S, c=Đ, d=S" hoặc "a=D,b=S,c=D,d=S" (prompt template
    # khuyến cáo dùng D không dấu cho parser ổn định khi user dán text mà
    # chatbot tự normalize Unicode).
    answers: dict[str, bool] = {}
    if answer_raw:
        for m in _DS_ANSWER_TOKEN_RE.finditer(answer_raw):
            k = m.group(1).lower()
            v = m.group(2).upper()
            answers[k] = v in ("Đ", "D", "ĐÚNG", "DUNG", "DÚNG", "T", "TRUE")
    # Merge với inline (ưu tiên explicit answer_raw)
    for k, v in inline_answers.items():
        answers.setdefault(k, v)

    # Đảm bảo đủ 4 ý
    for k in "abcd":
        items.setdefault(k, "")
    if not all(items[k].strip() for k in "abcd"):
        return None
    if len(answers) < 4:
        return None

    # Tách lời giải từng ý (a/b/c/d) từ solution_lines để exporter không mất
    # "Lời giải" của từng ý khi tier=natural. Hỗ trợ các dạng:
    #   "a) Giải thích ý a..."
    #   "a. Giải thích..."
    #   "a: ..."
    #   "Ý a) ..."
    #   Hoặc 1 block "Lời giải: | a) ... | b) ... | c) ... | d) ..."
    item_solutions, overall_sol = _split_ds_item_solutions(solution_lines)

    return Question(
        qtype="DS",
        level="TH",
        topic="",
        question=q_text,
        items=dict(items),
        answers={k: answers[k] for k in "abcd"},
        item_solutions=item_solutions,
        solution=overall_sol,
    )


# Regex nhận diện "a) …", "a. …", "a: …", "(a) …", "Ý a) …"
_DS_SOL_ITEM_RE = re.compile(
    r"""^\s*(?:Ý\s+)?[\(\[]?([a-d])[\)\]\.:]\s*(.*)$""",
    re.IGNORECASE,
)


def _split_ds_item_solutions(solution_lines: list[str]) -> tuple[dict[str, str], str]:
    """Tách solution_lines thành ({a,b,c,d: str}, overall_solution_str).

    Strategy:
      • Nếu solution lines có marker "a)/a./a:/Ý a)" → tách theo marker.
      • Các dòng xuất hiện TRƯỚC marker đầu tiên → overall solution (intro).
      • Các dòng giữa marker i và marker i+1 → item_solutions[i].
      • Nếu không tìm thấy marker nào → overall_solution = full text.
    """
    if not solution_lines:
        return {k: "" for k in "abcd"}, ""

    # Flatten — có dòng có thể là "a) foo | b) bar" (1-liner with '|')
    lines: list[str] = []
    for ln in solution_lines:
        if "|" in ln and _DS_SOL_ITEM_RE.search(ln):
            # Tách theo "|" nếu thấy marker ở một phần
            for part in ln.split("|"):
                p = part.strip()
                if p:
                    lines.append(p)
        else:
            lines.append(ln)

    item_sol: dict[str, list[str]] = {k: [] for k in "abcd"}
    intro: list[str] = []
    current: Optional[str] = None

    for raw in lines:
        ln = raw.strip()
        if not ln:
            if current and item_sol[current]:
                item_sol[current].append("")  # giữ ngắt đoạn
            continue
        m = _DS_SOL_ITEM_RE.match(ln)
        if m:
            label = m.group(1).lower()
            rest  = m.group(2).strip()
            current = label
            if rest:
                item_sol[label].append(rest)
        else:
            if current:
                item_sol[current].append(ln)
            else:
                intro.append(ln)

    parsed = {k: "\n".join(v).strip() for k, v in item_sol.items()}
    overall = "\n".join(intro).strip()

    # Nếu không có marker nào (tất cả ý đều rỗng) → giữ nguyên overall
    if not any(parsed.values()):
        return {k: "" for k in "abcd"}, "\n".join(solution_lines).strip()

    return parsed, overall


def _build_tln(q_text: str, answer_raw: str,
               solution_lines: list[str]) -> Question:
    return Question(
        qtype="TLN",
        level="TH",
        topic="",
        question=q_text,
        answer=answer_raw.strip(),
        solution="\n".join(solution_lines).strip(),
        points=0.5,
    )


def _build_tl(q_text: str, solution_lines: list[str]) -> Question:
    return Question(
        qtype="TL",
        level="TH",
        topic="",
        question=q_text,
        solution="\n".join(solution_lines).strip(),
        points=1.0,
    )
