"""
tests/test_natural_parser.py — Test core/natural_parser.py.

Verify parse_natural_questions correctly handles:
  • TN với 4 phương án A/B/C/D + Đáp án
  • DS với 4 ý a/b/c/d
  • Old format $...$ AND new format ${...}$ (compatibility)
"""
from __future__ import annotations

import pytest

from core.natural_parser import parse_natural_questions


# ══════════════════════════════════════════════════════════════════════════
# TN — Trắc nghiệm
# ══════════════════════════════════════════════════════════════════════════

def test_tn_basic():
    text = """Câu 1: Tính 2+2.
A. 3
B. 4
C. 5
D. 6
Đáp án: B
Lời giải: 2+2 = 4."""
    qs = parse_natural_questions(text)
    assert len(qs) == 1
    q = qs[0]
    assert q.qtype == "TN"
    assert q.options["A"] == "3"
    assert q.options["B"] == "4"
    assert q.answer == "B"
    assert "4" in q.solution


def test_tn_multiple_questions():
    text = """Câu 1: Câu hỏi 1?
A. a1
B. b1
C. c1
D. d1
Đáp án: A

Câu 2: Câu hỏi 2?
A. a2
B. b2
C. c2
D. d2
Đáp án: C"""
    qs = parse_natural_questions(text)
    assert len(qs) == 2
    assert qs[0].answer == "A"
    assert qs[1].answer == "C"


def test_tn_with_old_format_dollar():
    """Compatibility: $x^2$ (cũ) vẫn parse OK."""
    text = """Câu 1: Tính $x^2$ tại $x=3$.
A. $9$
B. $6$
C. $\\sqrt{3}$
D. $0$
Đáp án: A"""
    qs = parse_natural_questions(text)
    assert len(qs) == 1
    assert "${x^2}$" in qs[0].question


def test_tn_with_new_format_braces():
    """Compatibility: ${x^2}$ (mới — chuẩn app) vẫn parse OK."""
    text = """Câu 1: Tính ${x^2}$ tại ${x=3}$.
A. ${9}$
B. ${6}$
C. ${\\sqrt{3}}$
D. ${0}$
Đáp án: A"""
    qs = parse_natural_questions(text)
    assert len(qs) == 1
    assert "${x^2}$" in qs[0].question


# ══════════════════════════════════════════════════════════════════════════
# DS — Đúng/Sai
# ══════════════════════════════════════════════════════════════════════════

def test_ds_basic():
    text = """Câu 1: Cho hàm số $f(x) = x^2$. Xét các khẳng định sau.
a) $f(0) = 0$. Đúng
b) $f(-1) = 1$. Đúng
c) $f(2) = 5$. Sai
d) $f$ đồng biến trên $[0; +\\infty)$. Đúng"""
    qs = parse_natural_questions(text)
    assert len(qs) == 1
    q = qs[0]
    assert q.qtype == "DS"
    assert len(q.items) == 4
    assert q.answers == {"a": True, "b": True, "c": False, "d": True}


def test_ds_with_explicit_dapan():
    text = """Câu 1: Tình huống chung.
a) Mệnh đề a.
b) Mệnh đề b.
c) Mệnh đề c.
d) Mệnh đề d.
Đáp án: a=Đ, b=S, c=Đ, d=S"""
    qs = parse_natural_questions(text)
    assert len(qs) == 1
    q = qs[0]
    assert q.qtype == "DS"
    assert q.answers == {"a": True, "b": False, "c": True, "d": False}


def test_ds_with_plain_d_dapan_matches_prompt_template():
    # Prompt template (Prompt Chatbot/01_PROMPT_TAO_CAU_HOI_CHUAN_APP.md,
    # /04_PROMPT_TAO_DE_TUONG_TU.md, /10_PROMPT_GEM_FULL_TUONG_THICH_APP.md)
    # khuyến cáo dùng "a=D,b=S,c=D,d=S" (D không dấu). Parser phải hiểu.
    text = """Câu 1: Tình huống chung.
a) Mệnh đề a.
b) Mệnh đề b.
c) Mệnh đề c.
d) Mệnh đề d.
DAPAN: a=D,b=S,c=D,d=S"""
    qs = parse_natural_questions(text)
    assert len(qs) == 1
    q = qs[0]
    assert q.qtype == "DS"
    assert q.answers == {"a": True, "b": False, "c": True, "d": False}


def test_ds_with_d_dapan_without_solution_inline_hints():
    # Trường hợp lỗi gốc: AI Text tab nhận block không có "a. Đúng/Sai"
    # cứu vớt qua inline_answers, chỉ có DAPAN: a=D,b=D,c=S,d=S thuần.
    # Trước fix: regex không hiểu D nên answers empty và câu bị bỏ qua.
    text = """Câu 1: Cho mặt cầu (S).
a) Mệnh đề a.
b) Mệnh đề b.
c) Mệnh đề c.
d) Mệnh đề d.
DAPAN: a=D,b=D,c=S,d=S"""
    qs = parse_natural_questions(text)
    assert len(qs) == 1
    q = qs[0]
    assert q.qtype == "DS"
    assert q.answers == {"a": True, "b": True, "c": False, "d": False}


# ══════════════════════════════════════════════════════════════════════════
# TLN — Trả lời ngắn
# ══════════════════════════════════════════════════════════════════════════

def test_tln_basic():
    text = """Câu 1: Tính tổng 1+2+3.
Đáp án: 6
Lời giải: 1+2+3 = 6."""
    qs = parse_natural_questions(text)
    assert len(qs) == 1
    assert qs[0].qtype == "TLN"
    assert qs[0].answer == "6"


# ══════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ══════════════════════════════════════════════════════════════════════════

def test_empty_input():
    assert parse_natural_questions("") == []
    assert parse_natural_questions("   ") == []


def test_no_question_header():
    text = "Đây là văn bản không có 'Câu N:' nào."
    assert parse_natural_questions(text) == []


def test_chatbot_preamble_ignored():
    """Lời chào của chatbot không gây sai parser."""
    text = """Sure, here are the questions:

Câu 1: Test question?
A. a
B. b
C. c
D. d
Đáp án: A"""
    qs = parse_natural_questions(text)
    assert len(qs) == 1


def test_question_with_bài_prefix():
    """'Bài 1:' cũng được nhận diện."""
    text = """Bài 1: Câu hỏi.
A. a
B. b
C. c
D. d
Đáp án: B"""
    qs = parse_natural_questions(text)
    assert len(qs) == 1
    assert qs[0].answer == "B"
