"""
core/question_parser_common.py — Shared regex + helpers cho các parser câu hỏi.

Được dùng bởi:
  • core/natural_parser.py      — parser tự nhiên từ AI output / plain text
  • core/doc_question_parser.py — parser từ .docx / .pdf văn bản đã trích
  • core/exam_file_loader.py    — orchestrator 3-tầng (exact → natural → AI)

Mục tiêu:
  1. Single Source of Truth cho các regex "Câu N:", "A.", "Đáp án:", ...
     — fix 1 chỗ thay vì 3 chỗ.
  2. Helper functions tái sử dụng: strip_question_prefix,
     detect_qtype_from_options, normalize_ds_answer_token, ...
  3. Không import domain models — chỉ stdlib + re → tránh circular import.

Nguyên tắc thiết kế:
  • Regex chịu cả diacritic & non-diacritic ("Câu"/"Cau").
  • Khoan dung với bracket/punct variants ("A.", "A)", "(A)", "A:").
  • KHÔNG nuốt exception — caller chịu trách nhiệm error handling.
"""

from __future__ import annotations

import re
from typing import Optional


# ══════════════════════════════════════════════════════════════════════════════
#  REGEX CHUNG — PUBLIC
# ══════════════════════════════════════════════════════════════════════════════

# Bắt đầu 1 câu mới: "Câu 1:", "Bài 1.", "Câu 12)", với cả biến thể không dấu.
# Biến thể không dấu (Cau/Bai) thường gặp khi OCR hoặc copy từ file PDF chưa
# có font Unicode tiếng Việt.
Q_HEADER_RE = re.compile(
    r"""^\s*(?:Câu|CÂU|câu|Cau|CAU|cau|
             Bài|BÀI|bài|Bai|BAI|bai|
             Question|Q)\s*(\d+)\s*[:.\)]\s*""",
    re.IGNORECASE | re.VERBOSE,
)

# Phương án TN: "A.", "A)", "(A)", "A:" ở đầu dòng. Group 1 = letter, Group 2 = text.
# KHÔNG dùng IGNORECASE — TN phải CHỮ HOA để KHÔNG nhầm với ý DS (chữ thường).
TN_OPT_RE = re.compile(
    r"""^\s*[\(\[]?\s*([A-D])\s*[\)\]\.:]\s*(.+)$""",
)

# Ý DS (chữ thường a-d): "a)", "a.", "(a)", "a:". KHÔNG match chữ HOA
# để không nhầm với TN_OPT_RE.
DS_ITEM_RE = re.compile(
    r"""^\s*[\(\[]?\s*([a-d])\s*[\)\]\.:]\s*(.+)$""",
)

# Dòng "Đáp án:" (và các biến thể, bao gồm không dấu)
ANSWER_RE = re.compile(
    r"""^\s*[-=>*•\s]*(?:Đáp\s*án|ĐÁP\s*ÁN|ĐA|Đ/A|DAP\s*AN|
             Đáp\s*số|Dap\s*an|Answer|Ans)\s*[:.]\s*(.*)$""",
    re.IGNORECASE | re.VERBOSE,
)

# Dòng "Lời giải:"
SOLUTION_RE = re.compile(
    r"""^\s*(?:Lời\s*giải|LỜI\s*GIẢI|Giải|Loi\s*giai|
             Hướng\s*dẫn\s*giải|Huong\s*dan\s*giai|
             Hướng\s*dẫn|Solution)\s*[:.]\s*(.*)$""",
    re.IGNORECASE | re.VERBOSE,
)

# Chữ Đ/D/S xuất hiện cuối ý DS để suy đáp án khi không có dòng "Đáp án:".
# Multi-char alternatives (Đúng/Dung/True/Sai/False) đặt trước single-char để
# regex engine khớp từ dài nhất; D/S/T/F để cuối làm fallback.
DS_MARK_TRUE = re.compile(
    r"""[\(\[\-\|\s](Đúng|ĐÚNG|Dúng|Dung|True|Đ|D|T)[\)\]\s\.\,\!]*\s*$""",
    re.IGNORECASE,
)
DS_MARK_FALSE = re.compile(
    r"""[\(\[\-\|\s](Sai|SAI|False|S|F)[\)\]\s\.\,\!]*\s*$""",
    re.IGNORECASE,
)
# Bắt "Đúng:" / "Sai." / "(Đúng)" / "[Đúng]" ở ĐẦU ý — tránh app thêm trùng.
# 2 dạng: (a) có dấu phân cách `:.-` sau, HOẶC (b) trong ngoặc + space.
DS_MARK_TRUE_START = re.compile(
    r"""^\s*(?:
        (?:Đúng|ĐÚNG|Dúng|Dung|True|Đ)\s*[:\.\-]\s*       # Đúng: text / Đúng. text
        | [\(\[]\s*(?:Đúng|ĐÚNG|Dúng|Dung|True|Đ)\s*[\)\]]\s+   # (Đúng) text / [Đúng] text
       )""",
    re.IGNORECASE | re.VERBOSE,
)
DS_MARK_FALSE_START = re.compile(
    r"""^\s*(?:
        (?:Sai|SAI|False|S)\s*[:\.\-]\s*
        | [\(\[]\s*(?:Sai|SAI|False|S)\s*[\)\]]\s+
       )""",
    re.IGNORECASE | re.VERBOSE,
)

# Token "a=Đ, b=S, c=Đ, d=S" / "a=D,b=S,c=D,d=S" / "a-Đ b-S c-S d-Đ" / "a:Đ b:S"
# Chấp nhận cả D (không dấu) lẫn Đ (có dấu) cho Đúng — match prompt templates.
DS_ANSWER_TOKEN_RE = re.compile(
    r"""([a-d])\s*[=:\-/\s]\s*(Đúng|ĐÚNG|Dúng|Dung|True|Sai|SAI|False|Đ|D|T|S|F)""",
    re.IGNORECASE | re.VERBOSE,
)

# Prefix "Câu N:"/"Bài N:" để strip — KHÁC Q_HEADER_RE ở chỗ dùng cho re.sub
# trên text đã nối (không cần anchor ^).
Q_PREFIX_STRIP_RE = re.compile(
    r"""^(?:Câu|CÂU|Cau|CAU|Bài|BÀI|Bai|BAI|Question|Q)\s*\d+\s*[:.\)]\s*""",
    re.IGNORECASE,
)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS PUBLIC
# ══════════════════════════════════════════════════════════════════════════════

def strip_question_prefix(text: str) -> str:
    """Xoá prefix "Câu N:" / "Bài N:" ở đầu chuỗi (1 lần).

    >>> strip_question_prefix("Câu 1: Tính đạo hàm của y=x²")
    'Tính đạo hàm của y=x²'
    >>> strip_question_prefix("   Cau 12) Cho hàm số")
    'Cho hàm số'
    """
    return Q_PREFIX_STRIP_RE.sub("", (text or "").lstrip(), count=1)


def detect_qtype_from_options(options: dict[str, str],
                              n_ds_items: int = 0) -> str:
    """Đoán qtype dựa số option / DS items.

    Ưu tiên: DS (≥3 items) > TN (≥3 options) > TL (fallback).
    TLN không detect được chỉ từ options — caller phải có signal khác.

    Parameters
    ----------
    options   : dict đáp án TN (A/B/C/D → text)
    n_ds_items: số ý DS (a/b/c/d) đã parse được
    """
    if n_ds_items >= 3:
        return "DS"
    if len(options) >= 3:
        return "TN"
    return "TL"


def normalize_ds_answer_token(tok: str) -> Optional[bool]:
    """Chuẩn hoá token Đ/S → bool. Trả None nếu không nhận ra.

    >>> normalize_ds_answer_token("Đ")
    True
    >>> normalize_ds_answer_token("sai")
    False
    >>> normalize_ds_answer_token("x")  # None
    """
    if not tok:
        return None
    t = tok.strip().lower()
    if t in ("đ", "đúng", "t", "true", "dung", "dúng"):
        return True
    if t in ("s", "sai", "f", "false"):
        return False
    return None


def extract_answer_letter(answer_line: str) -> str:
    """Trích ký tự A/B/C/D từ dòng 'Đáp án:' — bỏ qua padding/punct.

    >>> extract_answer_letter("A.")
    'A'
    >>> extract_answer_letter("Đáp án đúng là B")
    'B'
    >>> extract_answer_letter("")
    ''
    """
    if not answer_line:
        return ""
    m = re.search(r"[A-D]", answer_line.upper())
    return m.group(0) if m else ""


def is_question_header(line: str) -> bool:
    """True nếu dòng là tiêu đề câu hỏi ('Câu N:')."""
    return bool(Q_HEADER_RE.match(line or ""))


def iter_question_headers(text: str):
    """Yield (line_idx, question_num, line_content) cho mọi header câu.

    Dùng để tách văn bản thành các block câu mà không phải viết lại logic.
    """
    for i, ln in enumerate((text or "").splitlines()):
        m = Q_HEADER_RE.match(ln)
        if m:
            try:
                num = int(m.group(1))
            except (ValueError, IndexError):
                num = -1
            yield i, num, ln


# ══════════════════════════════════════════════════════════════════════════════
#  VALIDATION — ngăn chặn dữ liệu lạ lọt vào Question (2.4)
# ══════════════════════════════════════════════════════════════════════════════

# Giới hạn an toàn — các giá trị này bảo vệ memory & UI khi AI trả về text quá
# dài (VD: Gemini đôi khi stream duplicate nội dung khi stream bị interrupt).
MAX_QUESTION_TEXT_LEN = 32_000       # ký tự — ~8k tokens, đủ cho bài toán dài
MAX_OPTION_TEXT_LEN   = 4_000
MAX_SOLUTION_TEXT_LEN = 64_000
MAX_OPTION_COUNT      = 10           # TN tối đa 6 (A-F) + buffer
MAX_DS_ITEM_COUNT     = 8            # DS tối đa 4 ý + buffer
VALID_QTYPES = ("TN", "DS", "TLN", "TL")
VALID_LEVELS = ("NB", "TH", "VD", "VDC")
VALID_TN_ANSWERS = ("A", "B", "C", "D", "E", "F")


class QuestionValidationError(ValueError):
    """Raised khi Question data vi phạm ràng buộc bảo mật / nhất quán."""
    pass


def validate_question_dict(q_data: dict, *, strict: bool = False) -> list[str]:
    """Kiểm tra dict câu hỏi, trả về list WARNING (không raise trừ khi strict).

    Parameters
    ----------
    q_data : dict
        Dict câu hỏi trước khi tạo Question object. Thường từ AI response
        sau parse, hoặc từ session load sau migrate.
    strict : bool
        Nếu True → raise QuestionValidationError khi có lỗi nghiêm trọng.
        Nếu False (default) → chỉ trả warnings, caller tự xử lý (VD: UI
        có thể hỏi user có muốn dùng câu này không).

    Returns
    -------
    list[str] — danh sách warning (rỗng = hoàn toàn hợp lệ).

    Examples
    --------
    >>> validate_question_dict({"qtype": "TN", "question": "OK"})
    ['TN phải có ít nhất 3 phương án (hiện có 0)', 'TN không có đáp án']

    >>> # Text quá dài
    >>> bad = {"qtype":"TL", "question": "x" * 100_000}
    >>> warns = validate_question_dict(bad)
    >>> any("dài" in w for w in warns)
    True
    """
    warnings: list[str] = []

    # qtype
    qtype = (q_data.get("qtype") or "").upper()
    if qtype not in VALID_QTYPES:
        warnings.append(
            f"qtype '{qtype}' không hợp lệ — phải thuộc {VALID_QTYPES}")

    # level
    level = (q_data.get("level") or "").upper()
    if level and level not in VALID_LEVELS:
        warnings.append(
            f"level '{level}' không hợp lệ — phải thuộc {VALID_LEVELS}")

    # question text
    q_text = q_data.get("question") or ""
    if not isinstance(q_text, str):
        warnings.append(f"question không phải str (type={type(q_text).__name__})")
    else:
        if not q_text.strip():
            warnings.append("question rỗng")
        elif len(q_text) > MAX_QUESTION_TEXT_LEN:
            warnings.append(
                f"question quá dài ({len(q_text):,} ký tự, "
                f"giới hạn {MAX_QUESTION_TEXT_LEN:,})")

    # solution (optional but checked length)
    sol = q_data.get("solution") or ""
    if isinstance(sol, str) and len(sol) > MAX_SOLUTION_TEXT_LEN:
        warnings.append(
            f"solution quá dài ({len(sol):,} ký tự, "
            f"giới hạn {MAX_SOLUTION_TEXT_LEN:,})")

    # TN-specific
    if qtype == "TN":
        options = q_data.get("options") or {}
        if not isinstance(options, dict):
            warnings.append(
                f"TN.options phải là dict (hiện {type(options).__name__})")
        else:
            if len(options) < 3:
                warnings.append(
                    f"TN phải có ít nhất 3 phương án (hiện có {len(options)})")
            if len(options) > MAX_OPTION_COUNT:
                warnings.append(
                    f"TN có quá nhiều phương án ({len(options)} > {MAX_OPTION_COUNT})")
            for k, v in options.items():
                if not isinstance(v, str):
                    warnings.append(f"TN.options[{k!r}] không phải str")
                elif len(v) > MAX_OPTION_TEXT_LEN:
                    warnings.append(
                        f"TN.options[{k!r}] quá dài ({len(v):,} ký tự)")

            answer = (q_data.get("answer") or "").upper().strip()
            if not answer:
                warnings.append("TN không có đáp án")
            elif answer not in VALID_TN_ANSWERS:
                warnings.append(f"TN.answer='{answer}' không hợp lệ")
            elif answer not in options:
                warnings.append(
                    f"TN.answer='{answer}' không có trong options "
                    f"({list(options.keys())})")

    # DS-specific
    if qtype == "DS":
        items = q_data.get("items") or {}
        answers = q_data.get("answers") or {}
        if not isinstance(items, dict) or not isinstance(answers, dict):
            warnings.append("DS.items / DS.answers phải là dict")
        else:
            if len(items) < 2:
                warnings.append(
                    f"DS phải có ít nhất 2 ý (hiện có {len(items)})")
            if len(items) > MAX_DS_ITEM_COUNT:
                warnings.append(
                    f"DS có quá nhiều ý ({len(items)} > {MAX_DS_ITEM_COUNT})")
            missing_ans = [k for k in items.keys() if k not in answers]
            if missing_ans:
                warnings.append(
                    f"DS thiếu đáp án cho các ý: {missing_ans}")
            for k, v in answers.items():
                if not isinstance(v, bool):
                    warnings.append(
                        f"DS.answers[{k!r}] phải là bool (True/False), "
                        f"hiện {type(v).__name__}={v!r}")

    if strict and warnings:
        raise QuestionValidationError("; ".join(warnings))
    return warnings


_CLIP_SUFFIX = "… (đã cắt bớt)"
_CLIP_SUFFIX_SHORT = "…"


def _truncate(text: str, limit: int, suffix: str = _CLIP_SUFFIX) -> str:
    """Cắt text sao cho tổng độ dài (text + suffix) ≤ limit."""
    keep = max(0, limit - len(suffix))
    return text[:keep] + suffix


def sanitize_question_objects(
    qs: list,
    *,
    logger=None,
) -> tuple[list, list[str]]:
    """Clip + validate một list Question objects, trả về list mới đã an toàn.

    Dùng duck-typing qua `to_dict()` / `from_dict()` — KHÔNG import `Question`
    ở module level để tránh circular import (common ↔ models ↔ parsers).

    Parameters
    ----------
    qs     : list[Question] — list câu hỏi vừa parse xong, trước khi expose
             ra UI / session store.
    logger : logging.Logger hoặc None — nếu có, log warnings ở level DEBUG.

    Returns
    -------
    (sanitized_list, all_warnings) — caller có thể hiển thị warnings cho user.
    """
    if not qs:
        return list(qs), []

    # Lazy import — tránh cycle. Nếu q không có to_dict/from_dict thì skip clip.
    try:
        from core.models import Question as _Q  # type: ignore
    except Exception:
        _Q = None

    out: list = []
    all_warnings: list[str] = []
    for q in qs:
        if _Q is None or not hasattr(q, "to_dict") or not hasattr(_Q, "from_dict"):
            out.append(q)
            continue
        try:
            d = q.to_dict()
            d, warns = validate_and_clip_question_dict(d)
            if warns:
                all_warnings.extend(warns)
                if logger is not None:
                    logger.debug("Question warnings: %s", "; ".join(warns))
            out.append(_Q.from_dict(d))
        except Exception as e:
            # Không chặn pipeline — giữ nguyên object gốc nếu sanitize fail
            if logger is not None:
                logger.debug("sanitize failed, keep original: %s", e)
            out.append(q)
    return out, all_warnings


def validate_and_clip_question_dict(q_data: dict) -> tuple[dict, list[str]]:
    """Chạy validate + TRUNCATE các field quá dài — không raise.

    Trả về (dict_clipped, warnings). Đảm bảo dict trả về LUÔN an toàn để
    lưu DB / hiển thị UI, kể cả khi AI response bị bug stream.

    Text đã được cắt sao cho độ dài sau cùng KHÔNG vượt các MAX_*_LEN, nên
    warnings chỉ phản ánh các vi phạm KHÁC (VD: thiếu đáp án, qtype sai).
    """
    # Copy shallow để không mutate đối tượng caller
    out = dict(q_data)

    # Loại bỏ các thẻ citation [cite: ...] do AI/NotebookLM sinh ra
    if isinstance(out.get("question"), str):
        out["question"] = re.sub(r"\[cite[a-z]*:\s*[\d,\s]+\]", "", out["question"], flags=re.IGNORECASE)
    if isinstance(out.get("solution"), str):
        out["solution"] = re.sub(r"\[cite[a-z]*:\s*[\d,\s]+\]", "", out["solution"], flags=re.IGNORECASE)

    q_text = out.get("question") or ""
    if isinstance(q_text, str) and len(q_text) > MAX_QUESTION_TEXT_LEN:
        out["question"] = _truncate(q_text, MAX_QUESTION_TEXT_LEN)

    sol = out.get("solution") or ""
    if isinstance(sol, str) and len(sol) > MAX_SOLUTION_TEXT_LEN:
        out["solution"] = _truncate(sol, MAX_SOLUTION_TEXT_LEN)

    opts = out.get("options")
    if isinstance(opts, dict):
        new_opts = {}
        for k, v in list(opts.items())[:MAX_OPTION_COUNT]:
            if isinstance(v, str):
                v = re.sub(r"\[cite[a-z]*:\s*[\d,\s]+\]", "", v, flags=re.IGNORECASE)
                if len(v) > MAX_OPTION_TEXT_LEN:
                    v = _truncate(v, MAX_OPTION_TEXT_LEN, _CLIP_SUFFIX_SHORT)
            new_opts[k] = v
        out["options"] = new_opts

    items = out.get("items")
    if isinstance(items, dict):
        new_items = {}
        for k, v in list(items.items())[:MAX_DS_ITEM_COUNT]:
            if isinstance(v, str):
                v = re.sub(r"\[cite[a-z]*:\s*[\d,\s]+\]", "", v, flags=re.IGNORECASE)
            new_items[k] = v
        out["items"] = new_items

    item_sols = out.get("item_solutions")
    if isinstance(item_sols, dict):
        new_item_sols = {}
        for k, v in list(item_sols.items())[:MAX_DS_ITEM_COUNT]:
            if isinstance(v, str):
                v = re.sub(r"\[cite[a-z]*:\s*[\d,\s]+\]", "", v, flags=re.IGNORECASE)
            new_item_sols[k] = v
        out["item_solutions"] = new_item_sols

    warnings = validate_question_dict(out, strict=False)
    return out, warnings
