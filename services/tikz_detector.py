"""
services/tikz_detector.py — Quét Question tìm các khối TikZ / BBT cần render.

Điểm chốt:
- Hỗ trợ cả khối trần `\\begin{tikzpicture}...\\end{tikzpicture}` và khối bọc
  fence ```tikz ... ``` mà một số model hay xuất.
- Hỗ trợ thêm KHỐI BẢNG BIẾN THIÊN (tkz-tab) đứng một mình — AI đôi khi xuất
  `\\tkzTabInit...\\tkzTabVar` mà quên gói trong `\\begin{tikzpicture}`.
  Detector sẽ auto-wrap khối này thành tikzpicture hợp lệ trước khi render.
- Trả về đối tượng `TikzBlock(field, start, end, code)` để pipeline biết đâu
  là "nơi gốc" của khối TikZ — quyết định ghi ảnh vào slot nào của Question.
- Không mutate Question: chỉ đọc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

# Tên các "trường" mà pipeline nhận dạng để biết ảnh render xong nên gán vào đâu:
#   "tikz_code"          → q.question_image  (block dedicated, thay cả field)
#   "question"           → q.question_image  (strip TikZ khỏi q.question)
#   "solution"           → q.solution_image  (strip TikZ khỏi q.solution)
#   "items.<a|b|c|d>"    → q.item_images[x]  (DS: strip khỏi q.items[x])
#   "item_solutions.<x>" → q.solution_image  (fallback — model không có slot riêng)
#   "options.<A|B|C|D>"  → q.option_images[X]

_TIKZ_RE = re.compile(
    r"\\begin\{tikzpicture\}(?:\[[^\]]*\])?.*?\\end\{tikzpicture\}",
    re.DOTALL,
)
# Fence ```tikz \n ... \n ``` hoặc ```latex ...``` bao quanh TikZ / tkz-tab
_FENCE_RE = re.compile(
    r"```(?:tikz|latex|tkz-tab)?\s*"
    r"(\\begin\{tikzpicture\}(?:\[[^\]]*\])?.*?\\end\{tikzpicture\})"
    r"\s*```",
    re.DOTALL,
)
# Dòng "TikZ: \begin{...}" đôi khi AI sinh theo spec prompt
_PREFIX_RE = re.compile(
    r"(?:^|\n)\s*TikZ\s*:\s*(\\begin\{tikzpicture\}(?:\[[^\]]*\])?.*?\\end\{tikzpicture\})",
    re.DOTALL,
)

# ── tkz-tab BARE: AI xuất \tkzTabInit...\tkzTabVar mà quên \begin{tikzpicture} ─
# Chộp toàn bộ từ \tkzTabInit đến \tkzTabVar/\tkzTabLine/\tkzTabSlope gần nhất.
# Ba mẫu theo thứ tự ưu tiên: tất cả bare command sequence.
# Heuristic: bắt đầu từ \tkzTabInit, kết thúc ở LẦN CUỐI \tkzTabVar
# trước khi gặp blank-line 2 lần / "===" / EOF.
_TKZTAB_BARE_RE = re.compile(
    r"(?<!\\begin\{tikzpicture\})"       # không đi ngay sau \begin{tikzpicture}
    r"(?<!\{tikzpicture\})"              # nới thêm — vì có thể có khoảng trắng
    r"(\\tkzTabInit\b.*?\\tkzTabVar\{[^}]*\}(?:\s*\{[^}]*\})?(?:\s*\{[^}]*\})?)"
    r"(?=\s*(?:\n\s*\n|\Z|===|```|\\tkzTabInit))",
    re.DOTALL,
)

# Prefix "BBT:" hoặc "Bảng biến thiên:" trước khối tkz-tab bare
_BBT_PREFIX_RE = re.compile(
    r"(?:^|\n)\s*(?:BBT|Bảng\s*biến\s*thiên|B[ảa]ng\s*bi[ếe]n\s*thi[êe]n)\s*:\s*\n?",
    re.IGNORECASE,
)


_TABULAR_RE = re.compile(
    r"\\begin\{tabular\}\s*(?:\[[^\]]*\])?\s*(?:\{[^}]*\})?.*?\\end\{tabular\}",
    re.DOTALL,
)

def _wrap_tkztab(bare_code: str) -> str:
    """Gói khối tkz-tab bare vào `\\begin{tikzpicture}...\\end{tikzpicture}`."""
    bare = bare_code.strip()
    if bare.startswith("\\begin{tikzpicture}"):
        return bare
    return "\\begin{tikzpicture}\n" + bare + "\n\\end{tikzpicture}"


@dataclass
class TikzBlock:
    """Một khối TikZ / BBT / Tabular phát hiện được trong Question.

    Attributes:
        field:  Tên trường nguồn (xem mapping ở đầu module).
        start:  Offset đầu khối trong text gốc (để strip).
        end:    Offset cuối (exclusive).
        code:   Nội dung TikZ/BBT/Tabular đã CHUẨN HOÁ — luôn bắt đầu bằng
                `\\begin{...}` và kết thúc `\\end{...}`, kể cả
                khi input là tkz-tab bare (đã được auto-wrap).
    """
    field: str
    start: int
    end:   int
    code:  str


def _iter_matches(text: str) -> Iterable[tuple[int, int, str]]:
    """Yield (start, end, code) cho mọi khối TikZ/BBT/Tabular, dedupe theo span đã thấy."""
    seen: list[tuple[int, int]] = []

    def _overlap(a: int, b: int) -> bool:
        return any(s <= a and b <= e for s, e in seen)

    # 1) Fence bao quanh (ưu tiên vì span lớn hơn → dễ strip sạch)
    # Cập nhật fence RE inline để ăn cả tabular
    _FENCE_ANY_RE = re.compile(
        r"```(?:tikz|latex|tkz-tab)?\s*"
        r"(\\begin\{(?:tikzpicture|tabular)\}\s*(?:\[[^\]]*\])?.*?\\end\{(?:tikzpicture|tabular)\})"
        r"\s*```",
        re.DOTALL,
    )
    for m in _FENCE_ANY_RE.finditer(text):
        yield m.start(), m.end(), m.group(1).strip()
        seen.append((m.start(), m.end()))

    # 2) Dòng "TikZ: \begin{...}" — strip nguyên dòng prefix
    for m in _PREFIX_RE.finditer(text):
        if _overlap(m.start(), m.end()):
            continue
        yield m.start(), m.end(), m.group(1).strip()
        seen.append((m.start(), m.end()))

    # 3) Khối trần tikzpicture
    for m in _TIKZ_RE.finditer(text):
        if _overlap(m.start(), m.end()):
            continue
        yield m.start(), m.end(), m.group(0).strip()
        seen.append((m.start(), m.end()))
        
    # 3.5) Khối trần tabular
    for m in _TABULAR_RE.finditer(text):
        if _overlap(m.start(), m.end()):
            continue
        yield m.start(), m.end(), m.group(0).strip()
        seen.append((m.start(), m.end()))

    # 4) Bảng biến thiên bare — tkz-tab không bọc tikzpicture
    #    (AI đôi khi quên wrap). Auto-wrap để render được.
    for m in _TKZTAB_BARE_RE.finditer(text):
        s, e = m.start(), m.end()
        if _overlap(s, e):
            continue
        # Mở rộng span để nuốt luôn prefix "BBT:" nếu có ngay trước đó
        span_start = s
        prefix_match = _BBT_PREFIX_RE.search(text, max(0, s - 60), s + 5)
        if prefix_match and prefix_match.end() >= s - 2:
            span_start = prefix_match.start()
        yield span_start, e, _wrap_tkztab(m.group(1))
        seen.append((span_start, e))


def find_in_text(text: str, field: str) -> list[TikzBlock]:
    """Tìm mọi khối TikZ/BBT/Tabular trong chuỗi text, gắn nhãn `field`."""
    if not text:
        return []
    # Quick reject: phải có ít nhất 1 trong các marker
    if ("\\begin{tikzpicture}" not in text) and ("\\tkzTabInit" not in text) and ("\\begin{tabular}" not in text):
        return []
    return [TikzBlock(field, s, e, code) for s, e, code in _iter_matches(text)]


def scan_question(q) -> list[TikzBlock]:
    """Quét toàn bộ Question: tikz_code, question, solution, items, item_solutions, options.

    Hỗ trợ cả tkz-tab bare (AI quên wrap trong `\\begin{tikzpicture}`) — sẽ
    auto-wrap trước khi trả về.
    """
    blocks: list[TikzBlock] = []

    # 1) Các field có text → scan inline trước (cần strip block khi render)
    blocks += find_in_text(getattr(q, "question", "") or "", "question")
    blocks += find_in_text(getattr(q, "solution", "") or "", "solution")

    items = getattr(q, "items", {}) or {}
    for k, v in items.items():
        blocks += find_in_text(v or "", f"items.{k}")

    item_sols = getattr(q, "item_solutions", {}) or {}
    for k, v in item_sols.items():
        blocks += find_in_text(v or "", f"item_solutions.{k}")

    options = getattr(q, "options", {}) or {}
    for k, v in options.items():
        blocks += find_in_text(v or "", f"options.{k}")

    # 2) Field dedicated: q.tikz_code — chỉ thêm nếu KHÔNG trùng với bất kỳ khối inline nào
    tc = (getattr(q, "tikz_code", "") or "").strip()
    if tc:
        code = ""
        if "\\begin{tikzpicture}" in tc:
            # Trường hợp q.tikz_code chứa nhiều hơn 1 block: chỉ lấy cái đầu
            m = _TIKZ_RE.search(tc)
            code = m.group(0).strip() if m else tc
        elif "\\begin{tabular}" in tc:
            m = _TABULAR_RE.search(tc)
            code = m.group(0).strip() if m else tc
        elif "\\tkzTabInit" in tc:
            # BBT bare trong tikz_code → auto-wrap
            m = _TKZTAB_BARE_RE.search(tc)
            if m:
                code = _wrap_tkztab(m.group(1))
            else:
                # Fallback: wrap toàn bộ (có thể AI xuất nhiều lệnh tkz rời rạc)
                code = _wrap_tkztab(tc)

        if code:
            norm_code = "".join(code.split())
            already_scanned = any(
                norm_code == "".join(b.code.split())
                or norm_code in "".join((getattr(q, b.field, "") or "").split())
                for b in blocks
            )
            if not already_scanned:
                blocks.append(TikzBlock("tikz_code", 0, len(tc), code))

    return blocks


def count_blocks(q) -> int:
    """Đếm nhanh số block TikZ (dùng cho progress bar trước khi render)."""
    return len(scan_question(q))
