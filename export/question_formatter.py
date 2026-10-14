"""
export/question_formatter.py — Unified Word-ready text formatter.

Một nguồn duy nhất cho format câu hỏi → text "paste thẳng vào Word đẹp ngay".
Dùng cho:
  • Preview trong tab Convert / tab Result / dialog NHCH
  • Copy text → clipboard → paste vào Word (giữ TAB giữa phương án TN)
  • Là tham chiếu cấu trúc cho `export/word_exporter.py` (bold + indent)

Quy tắc chính (theo spec người dùng):
  - "Câu N." mở đầu mỗi câu (in đậm trong .docx; plain text giữ nguyên).
  - TN: A./B./C./D. cùng 1 dòng, ngăn bằng TAB "\\t" thật của Word.
  - DS: a./b./c./d. mỗi ý 1 dòng.
  - TLN: hộp đáp án |c1|c2|c3|c4| (4 ô, mỗi ô 1 ký tự, thiếu = trống).
  - Mỗi câu kết thúc bằng dấu câu (. ! ? : ;) — tự thêm "." nếu thiếu.
  - Giữa 2 câu cách nhau ĐÚNG 1 dòng trống.
  - Không markdown (#, *, -, ```), không bảng |---|, không icon trang trí (►, ✓…).
  - Công thức ${...}$ inline — KHÔNG dùng Unicode toán.
"""

from __future__ import annotations
import re
from typing import Iterable


_DS_TRUE_LABEL  = "Đúng"
_DS_FALSE_LABEL = "Sai"

# Các dấu kết thúc câu được chấp nhận (không thêm "." khi đã có dấu này)
_TERMINATORS = (".", "!", "?", ":", ";")


def ensure_terminator(text: str) -> str:
    """Đảm bảo chuỗi kết thúc bằng 1 dấu câu hợp lệ.

    Nếu chuỗi đã kết thúc bằng ., !, ?, :, ; → giữ nguyên.
    Nếu kết thúc bằng dấu ngoặc/đóng công thức $ … $ → vẫn thêm "."
    để khớp spec "kết thúc bằng dấu câu phù hợp ngữ nghĩa".
    Chuỗi rỗng → trả về chuỗi rỗng.
    """
    t = (text or "").rstrip()
    if not t:
        return ""
    if t.endswith(_TERMINATORS):
        return t
    return t + "."


def _strip_dot(text: str) -> str:
    """Loại dấu '.' cuối — dùng khi nội dung sẽ được nối vào câu tiếp theo."""
    t = (text or "").rstrip()
    if t.endswith("."):
        return t[:-1].rstrip()
    return t


def _tln_boxes(answer: str) -> str:
    """Render đáp án TLN dạng 4 ô |a|b|c|d|.

    Lấy tối đa 4 ký tự đầu; thiếu thì để khoảng trống. Bỏ qua khoảng trắng
    đầu/cuối nhưng GIỮ khoảng trắng giữa (vd "0,75" → 4 ký tự).

    Ví dụ:
        "12"    → "|1|2| | |"
        "0,75"  → "|0|,|7|5|"
        ""      → "| | | | |"
    """
    a = (answer or "").strip()
    chars = list(a[:4])
    while len(chars) < 4:
        chars.append(" ")
    return "|" + "|".join(chars) + "|"


def _format_ds_answer(q) -> str:
    """Tạo chuỗi đáp án cho câu DS dạng 'a=Đ, b=S, c=Đ, d=S'."""
    if not q.answers:
        return ""
    parts: list[str] = []
    for k in "abcd":
        if k in q.answers:
            mark = "Đ" if q.answers[k] else "S"
            parts.append(f"{k}={mark}")
    return ", ".join(parts)


def format_question(q, idx: int, include_solution: bool = True) -> str:
    """Format 1 Question → plain text Word-ready (multi-dòng).

    Cấu trúc theo loại:
      TN  →  Câu N. <nội dung>.
             A. ... \\t B. ... \\t C. ... \\t D. ...
             Đáp án: X
             Lời giải: ...

      DS  →  Câu N. <nội dung>.
             a. ...
             b. ...
             c. ...
             d. ...
             Đáp án: a=Đ, b=S, c=Đ, d=S
             Lời giải:
             a. Đúng/Sai. <giải>.
             ...

      TLN →  Câu N. <nội dung>.
             Đáp án: | | | |          ← hộp TRỐNG (để học sinh điền)
             Lời giải: <giải>.
             Đáp án: |c1|c2|c3|c4|    ← hộp ĐIỀN đáp án thực tế

      TL  →  Câu N. <nội dung>.
             Lời giải: ...

    Parameters
    ----------
    q:                Question object (core.models.Question)
    idx:              Số thứ tự câu (>=1)
    include_solution: Có in kèm đáp án + lời giải hay không
    """
    lines: list[str] = []

    # ── 1) Heading: "Câu N. <nội dung>." ─────────────────────────────────
    content = ensure_terminator((q.question or "").strip())
    lines.append(f"Câu {idx}. {content}")

    qtype = (q.qtype or "").upper()

    # ── 2) Phương án / mệnh đề / hộp đáp án trống (TLN) ──────────────────
    if qtype == "TN":
        # A./B./C./D. cùng dòng, ngăn TAB
        parts: list[str] = []
        for k in "ABCD":
            v = ensure_terminator(q.options.get(k, ""))
            parts.append(f"{k}. {v}")
        lines.append("\t".join(parts))

    elif qtype == "DS":
        # a./b./c./d. mỗi ý 1 dòng
        for k in "abcd":
            v = ensure_terminator(q.items.get(k, ""))
            lines.append(f"{k}. {v}")

    elif qtype == "TLN":
        # Hộp đáp án TRỐNG ngay sau câu hỏi — học sinh điền
        lines.append(f"Đáp án: {_tln_boxes('')}")

    # TL: không có phương án — sang trực tiếp lời giải

    if not include_solution:
        return "\n".join(lines)

    # ── 3) Đáp án rõ — cho TN và DS (TLN sẽ in hộp điền ở cuối) ───────────
    if qtype == "TN":
        ans = (q.answer or "").strip().upper()
        if ans and ans[0] in "ABCD":
            lines.append(f"Đáp án: {ans[0]}")
    elif qtype == "DS":
        ds_ans = _format_ds_answer(q)
        if ds_ans:
            lines.append(f"Đáp án: {ds_ans}")
    # TLN: đáp án thực tế sẽ in SAU lời giải (mục [4])
    # TL: đáp án nằm trong lời giải

    # ── 4) Lời giải ───────────────────────────────────────────────────────
    if qtype == "DS" and q.item_solutions:
        # Mỗi ý 1 dòng "a. Đúng/Sai. <giải>."
        lines.append("Lời giải:")
        for k in "abcd":
            sol = (q.item_solutions.get(k, "") or "").strip()
            if not sol:
                continue
            verd = ""
            if q.answers and k in q.answers:
                verd = _DS_TRUE_LABEL if q.answers[k] else _DS_FALSE_LABEL
            prefix = f"{k}. {verd}. " if verd else f"{k}. "
            lines.append(prefix + ensure_terminator(sol))
    elif (q.solution or "").strip():
        sol = q.solution.strip()
        # Nếu lời giải nhiều dòng → "Lời giải:" trên 1 dòng, nội dung dòng tiếp
        if "\n" in sol:
            lines.append("Lời giải:")
            for ln in sol.splitlines():
                if ln.strip():
                    lines.append(ln.rstrip())
        else:
            lines.append(f"Lời giải: {ensure_terminator(sol)}")

    # ── 5) TLN: hộp đáp án ĐIỀN ở cuối (sau lời giải) ────────────────────
    if qtype == "TLN":
        a = (q.answer or "").strip()
        if a:
            lines.append(f"Đáp án: {_tln_boxes(a)}")

    return "\n".join(lines)


def format_questions(questions: Iterable, include_solution: bool = True) -> str:
    """Format nhiều Question — giữa các câu ĐÚNG 1 dòng trống.

    Trả về chuỗi sẵn sàng copy vào Word. Không có dòng trống thừa đầu/cuối.
    """
    parts: list[str] = []
    for i, q in enumerate(questions, 1):
        parts.append(format_question(q, i, include_solution=include_solution))
    return "\n\n".join(parts)


# ── Helpers cho exporter Word (để bold đúng chỗ, không phải re-parse text) ──

def split_options_for_tn(q) -> list[tuple[str, str]]:
    """Trả list [("A", "nội dung A."), ...] đã chuẩn hoá dấu '.' cuối."""
    out: list[tuple[str, str]] = []
    for k in "ABCD":
        v = ensure_terminator(q.options.get(k, ""))
        out.append((k, v))
    return out


def split_items_for_ds(q) -> list[tuple[str, str]]:
    """Trả list [("a", "nội dung a."), ...]."""
    out: list[tuple[str, str]] = []
    for k in "abcd":
        v = ensure_terminator(q.items.get(k, ""))
        out.append((k, v))
    return out


def tln_boxes_text(answer: str) -> str:
    """Public alias để Word exporter render box giống text preview."""
    return _tln_boxes(answer)


def ds_answer_text(q) -> str:
    """Public alias — chuỗi 'a=Đ, b=S…' cho mục Đáp án trong Word."""
    return _format_ds_answer(q)
