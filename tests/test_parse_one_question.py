"""Regression tests for core.parser.parse_one_question.

Covers the ===CAU===...===KETCAU=== structured-block path used by the
"AI Text → Câu hỏi" Convert tab and any caller that pastes prompt-template
output. The natural-text path has its own coverage in test_natural_parser.py.
"""
from core.parser import parse_one_question


def test_parse_ds_block_with_plain_d_dapan_and_newline_loigiai():
    """User-reported regression: DS block with DAPAN: a=D,b=D,c=S,d=S
    and LOIGIAI items separated by NEWLINES (not pipes) must produce a
    Question with all 4 answers and all 4 item_solutions populated."""
    block = """===CAU===
LOAI: DS
MUCDO: VD
CHUONG: Phương pháp tọa độ trong không gian
NOIDUNG: Trong không gian ${Oxyz}$, cho mặt cầu ${(S)}$.
a: Vectơ ${\\vec{u} = (1; -1; 0)}$ là một vectơ chỉ phương.
b: Khoảng cách từ tâm bằng ${6\\sqrt{2}}$.
c: Bán kính bằng 25.
d: Có thời điểm tiếp xúc.
DAPAN: a=D,b=D,c=S,d=S
LOIGIAI: a. Đúng. Ta có đường thẳng ${d}$.
b. Đúng. Từ phương trình mặt cầu.
c. Sai. Bán kính là 5.
d. Sai. Vô nghiệm.
===KETCAU==="""

    q = parse_one_question(block)
    assert q is not None
    assert q.qtype == "DS"
    assert q.level == "VD"
    assert q.topic == "Phương pháp tọa độ trong không gian"

    # All 4 answers parsed (no LOIGIAI inline-Đúng fallback needed).
    assert q.answers == {"a": True, "b": True, "c": False, "d": False}

    # All 4 items present.
    assert set(q.items.keys()) == {"a", "b", "c", "d"}
    assert "vectơ" in q.items["a"].lower() or "Vectơ" in q.items["a"]

    # All 4 per-item solutions captured from newline-separated LOIGIAI.
    assert set(q.item_solutions.keys()) >= {"a", "b", "c", "d"}
    assert "đường thẳng" in q.item_solutions["a"].lower()
    assert "phương trình" in q.item_solutions["b"].lower()
    assert "bán kính" in q.item_solutions["c"].lower()
    assert "vô nghiệm" in q.item_solutions["d"].lower()


def test_parse_ds_block_with_pipe_separated_loigiai_still_works():
    """Legacy format: items separated by '|' on a single LOIGIAI line."""
    block = """===CAU===
LOAI: DS
MUCDO: TH
CHUONG: Hàm số
NOIDUNG: Cho hàm số.
a: Mệnh đề a.
b: Mệnh đề b.
c: Mệnh đề c.
d: Mệnh đề d.
DAPAN: a=Đ,b=S,c=Đ,d=S
LOIGIAI: a. Vì lý do A. | b. Vì lý do B. | c. Vì lý do C. | d. Vì lý do D.
===KETCAU==="""

    q = parse_one_question(block)
    assert q is not None
    assert q.qtype == "DS"
    assert q.answers == {"a": True, "b": False, "c": True, "d": False}
    assert q.item_solutions["a"].startswith("Vì lý do A")
    assert q.item_solutions["b"].startswith("Vì lý do B")
    assert q.item_solutions["c"].startswith("Vì lý do C")
    assert q.item_solutions["d"].startswith("Vì lý do D")


def test_parse_ds_block_with_tikz_inside_noidung():
    """The NOIDUNG can hold a raw tikzpicture block before the a/b/c/d
    items — make sure the parser does not lose the items because of the
    embedded LaTeX."""
    block = r"""===CAU===
LOAI: DS
MUCDO: VD
CHUONG: Hình học không gian
NOIDUNG: Cho hình lăng trụ.
\begin{tikzpicture}
\draw (0,0) -- (1,0);
\end{tikzpicture}
a: Mệnh đề a.
b: Mệnh đề b.
c: Mệnh đề c.
d: Mệnh đề d.
DAPAN: a=D,b=S,c=D,d=S
LOIGIAI: a. Đúng.
b. Sai.
c. Đúng.
d. Sai.
===KETCAU==="""

    q = parse_one_question(block)
    assert q is not None
    assert q.qtype == "DS"
    assert q.answers == {"a": True, "b": False, "c": True, "d": False}
    assert set(q.items.keys()) == {"a", "b", "c", "d"}
    assert all(q.items[k].strip() for k in "abcd")
    # TikZ must be captured somewhere so the figure is not lost on save.
    assert ("tikzpicture" in q.question) or bool(getattr(q, "tikz_code", ""))


def test_parse_tn_block_basic_smoke():
    """Sanity check that TN still parses; this regression suite is new
    so we ensure parse_one_question isn't broken for the common case."""
    block = """===CAU===
LOAI: TN
MUCDO: NB
CHUONG: Đạo hàm
NOIDUNG: Đạo hàm của ${y = x^2}$ bằng?
A: ${2x}$
B: ${x}$
C: ${x^2}$
D: ${2}$
DAPAN: A
LOIGIAI: ${y' = 2x}$.
===KETCAU==="""

    q = parse_one_question(block)
    assert q is not None
    assert q.qtype == "TN"
    assert q.answer == "A"
    assert q.options["A"].strip() == "${2x}$"
