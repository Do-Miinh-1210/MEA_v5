"""
core/latex_parser.py — Parse câu hỏi từ file LaTeX (.tex) vào ngân hàng câu hỏi.

Hỗ trợ cấu trúc LaTeX phổ biến của Việt Nam (ex_test, hoctoan, BGD2025…):
  1. TN  (Trắc nghiệm):  \\begin{ex} ... \\choice {...}{...}{...}{...} \\end{ex}
  2. DS  (Đúng/Sai):      \\begin{ex} ... \\choiceTF {...}{...}{...}{...} \\end{ex}
  3. TLN (Trả lời ngắn):  \\begin{ex} ... \\shortans[...]{...} \\end{ex}
  4. TL  (Tự luận):       \\begin{bt} ... \\end{bt}
  5. VD  (Ví dụ):         \\begin{vd} ... \\end{vd}  (auto-detect TN/DS/TLN/TL)

Đặc điểm nhận dạng:
  - \\True đánh dấu đáp án đúng
  - \\loigiai{...} chứa lời giải
  - \\begin{itemchoice} \\itemch ... cho lời giải Đúng/Sai
  - \\immini{câu hỏi}{hình vẽ} cho câu có hình
  - %[mã câu] extract metadata + level
  - \\section{...} / \\subsection{...} extract chủ đề
  - Đường dẫn file → extract chủ đề từ tên thư mục
"""

from __future__ import annotations
import os
import re
from typing import Optional
from core.models import Question


def parse_latex_file(filepath: str) -> list[Question]:
    """Đọc file .tex và parse tất cả câu hỏi."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    questions = parse_latex_text(content)

    # Nếu vẫn thiếu topic → thử đoán từ đường dẫn file
    if questions and not questions[0].topic:
        guessed = _guess_topic_from_path(filepath)
        if guessed:
            for q in questions:
                if not q.topic:
                    q.topic = guessed

    return questions


def parse_latex_text(text: str) -> list[Question]:
    """Parse nội dung LaTeX thành danh sách Question."""
    questions: list[Question] = []

    # ── Extract chủ đề từ \section{...} hoặc \subsection{...} ──
    section_topic = _extract_topic(text)

    # ── Build map: vị trí \begin{ex} → metadata từ comment header ──
    # Format: % Câu N [Mức độ]_[Chủ đề]  (ngay trước \begin{ex})
    _HEADER_RE = re.compile(
        r'%\s*Câu\s*\d+\s*\[([^\]]*)\]_\[([^\]]*)\]\s*\n\s*\\begin\{(ex|bt|vd)\}',
        re.DOTALL,
    )
    # Cũng hỗ trợ không có chủ đề: % Câu N [Mức độ]
    _HEADER_RE2 = re.compile(
        r'%\s*Câu\s*\d+\s*\[([^\]]*)\]\s*\n\s*\\begin\{(ex|bt|vd)\}',
        re.DOTALL,
    )
    # Map: start_pos của \begin{ex} → (level_str, topic_str)
    header_map: dict[int, tuple[str, str]] = {}
    for m in _HEADER_RE.finditer(text):
        # Vị trí bắt đầu của \begin{...} là vị trí của ký tự '\\' trong \begin
        begin_pos = text.index(r'\begin', m.start())
        level_raw = m.group(1).strip()
        topic_raw = m.group(2).strip()
        header_map[begin_pos] = (level_raw, topic_raw)
    for m in _HEADER_RE2.finditer(text):
        begin_pos = text.index(r'\begin', m.start())
        if begin_pos not in header_map:
            level_raw = m.group(1).strip()
            header_map[begin_pos] = (level_raw, "")

    # Bảng map mức độ tiếng Việt → mã ngắn
    _LEVEL_MAP = {
        "nhận biết": "NB", "nhan biet": "NB",
        "thông hiểu": "TH", "thong hieu": "TH",
        "vận dụng cao": "VDC", "van dung cao": "VDC",
        "vận dụng": "VD", "van dung": "VD",
        "nb": "NB", "th": "TH", "vd": "VD", "vdc": "VDC",
    }

    def _norm_level(raw: str) -> str:
        key = raw.lower().strip()
        return _LEVEL_MAP.get(key, raw.upper() if raw else "")

    # Tìm tất cả khối \begin{ex/bt/vd}...\end{ex/bt/vd}
    pattern = re.compile(
        r'\\begin\{(ex|bt|vd)\}(.*?)\\end\{\1\}',
        re.DOTALL,
    )

    for match in pattern.finditer(text):
        env_type = match.group(1)
        body = match.group(2).strip()
        q = _parse_one_question(body, env_type, section_topic)
        if q:
            # Áp dụng metadata từ comment header (nếu có)
            begin_pos = match.start()
            if begin_pos in header_map:
                level_raw, topic_raw = header_map[begin_pos]
                if level_raw:
                    q.level = _norm_level(level_raw)
                if topic_raw and not q.topic:
                    q.topic = topic_raw
            questions.append(q)

    # ── Xử lý trùng ID: nếu nhiều câu cùng ID, tăng số thứ tự ──
    _dedup_structured_ids(questions)

    return questions



def _dedup_structured_ids(questions: list[Question]) -> None:
    """Nếu nhiều câu có cùng question_id (structured), tăng số thứ tự -01, -02, ..."""
    from collections import Counter
    id_counts: Counter = Counter()
    # Đếm số lần mỗi ID xuất hiện
    for q in questions:
        qid = q.question_id
        if qid and not qid.startswith("QID-"):
            id_counts[qid] += 1

    # Chỉ xử lý ID trùng
    dupes = {k for k, v in id_counts.items() if v > 1}
    if not dupes:
        return

    # Gán lại ID theo nhóm prefix (phần trước -XX)
    group_counters: dict[str, int] = {}
    for q in questions:
        qid = q.question_id
        if qid and not qid.startswith("QID-") and qid in dupes:
            # Tách prefix (ví dụ "12D1B1N1") và sequence
            dash_pos = qid.rfind("-")
            if dash_pos > 0:
                prefix = qid[:dash_pos]
                group_counters[prefix] = group_counters.get(prefix, 0) + 1
                q.question_id = f"{prefix}-{group_counters[prefix]:02d}"


def _extract_topic(text: str) -> str:
    """Extract chủ đề từ \\section, \\subsection, hoặc \\chapter."""
    # Ưu tiên \section (chủ đề chính)
    sec_m = re.search(r'\\section\*?\{([^}]+)\}', text)
    if sec_m:
        topic = _clean_latex(sec_m.group(1))
        # Nếu topic quá chung ("Đề 1"), tìm thêm
        if not re.match(r'^Đề\s*\d+$', topic, re.IGNORECASE):
            return topic

    # \subsection — thường là "Đề X", skip nếu chỉ là số đề
    # Tìm subsection có nội dung thực chất (không phải "Đề 1")
    for sub_m in re.finditer(r'\\subsection\*?\{([^}]+)\}', text):
        sub_topic = _clean_latex(sub_m.group(1))
        if not re.match(r'^Đề\s*\d+$', sub_topic, re.IGNORECASE):
            return sub_topic

    # \chapter
    ch_m = re.search(r'\\chapter\*?\{([^}]+)\}', text)
    if ch_m:
        return _clean_latex(ch_m.group(1))

    return ""


def _guess_topic_from_path(filepath: str) -> str:
    """Đoán chủ đề từ đường dẫn file / tên file.

    Ví dụ: "2-B1-De2.tex" → mã "2-B1" → tra bảng chủ đề lớp 12.
    """
    basename = os.path.basename(filepath)
    # Pattern: {chương}-B{bài}-De{đề}.tex  hoặc  {chương}-{bài}-De{đề}.tex
    m = re.match(r'(\d+)-B?(\d+)', basename)
    if not m:
        return ""

    chuong = int(m.group(1))
    bai = int(m.group(2))

    # Bảng chủ đề Toán 12 (chuẩn SGK 2025)
    _TOPIC_MAP_12 = {
        (1, 1): "Tính đơn điệu của hàm số",
        (2, 1): "Sự đồng biến, nghịch biến của hàm số",
        (2, 2): "Cực trị của hàm số",
        (2, 3): "Giá trị lớn nhất, nhỏ nhất của hàm số",
        (2, 4): "Đường tiệm cận",
        (2, 5): "Khảo sát sự biến thiên và vẽ đồ thị hàm số",
        (3, 1): "Lũy thừa",
        (3, 2): "Hàm số mũ và logarithm",
        (3, 3): "Phương trình, bất phương trình mũ và logarithm",
        (4, 1): "Nguyên hàm",
        (4, 2): "Tích phân",
        (4, 3): "Ứng dụng tích phân",
        (5, 1): "Số phức",
        (5, 2): "Phép toán số phức",
        (6, 1): "Khối đa diện",
        (6, 2): "Khối tròn xoay",
        (7, 1): "Phương trình mặt phẳng",
        (7, 2): "Phương trình đường thẳng trong không gian",
    }

    # Thử exact match
    topic = _TOPIC_MAP_12.get((chuong, bai), "")
    if topic:
        return topic

    # Thử chỉ theo chương
    _CHAPTER_MAP_12 = {
        1: "Hàm số và đồ thị",
        2: "Hàm số và đồ thị",
        3: "Hàm số mũ và logarithm",
        4: "Nguyên hàm và tích phân",
        5: "Số phức",
        6: "Hình học không gian",
        7: "Hình học tọa độ trong không gian",
        8: "Xác suất và thống kê",
    }
    return _CHAPTER_MAP_12.get(chuong, "")


def _convert_code_to_new_id(q_code: str) -> str:
    """Chuyển mã câu cũ (ví dụ 2D1B1-1) → ID mới (12D1B1N1-01).

    Trả về chuỗi rỗng nếu không phải ID cũ hợp lệ.
    """
    if not q_code:
        return ""
    try:
        from core.latex_id_manager import convert_old_to_new, is_old_format, is_new_format
        # Nếu đã là new format → giữ nguyên
        if is_new_format(q_code):
            return q_code
        # Nếu là old format → convert
        if is_old_format(q_code):
            new_id = convert_old_to_new(q_code)
            return new_id or ""
    except Exception:
        pass
    return ""


def _parse_one_question(body: str, env_type: str,
                        section_topic: str = "") -> Optional[Question]:
    """Parse 1 khối câu hỏi LaTeX."""

    # ── Extract metadata từ comment %[mã câu]%[code] ──
    q_code = ""
    code_m = re.match(r'\s*%\[([^\]]*)\]\s*(?:%\[([^\]]*)\])?\s*', body)
    if code_m:
        c1 = code_m.group(1) or ""
        c2 = code_m.group(2) or ""
        q_code = c2 if c2 else c1
        body = body[code_m.end():]

    # ── Extract lời giải — tìm \loigiai ở mức ngoài cùng ──
    solution = ""
    sol_raw = ""
    loigiai_pos = _find_loigiai(body)
    if loigiai_pos >= 0:
        brace_start = body.index('{', loigiai_pos)
        sol_raw = _extract_brace_content(body, brace_start)
        solution = sol_raw
        brace_end = _find_matching_brace(body, brace_start)
        body = body[:loigiai_pos].strip()

    # ── Xử lý \loigiai nằm ngay sau \choice{...}{...}{...}{...\loigiai{}} ──
    # (trong một số file, \loigiai nằm bên trong brace cuối cùng của \choice)
    if not solution:
        inner_loigiai = re.search(r'\\loigiai\s*\{', body)
        if inner_loigiai:
            brace_start = body.index('{', inner_loigiai.start())
            sol_raw = _extract_brace_content(body, brace_start)
            solution = sol_raw
            brace_end = _find_matching_brace(body, brace_start)
            body = body[:inner_loigiai.start()] + body[brace_end + 1:]
            body = body.strip()

    # ── Xử lý \immini{nội dung}{hình vẽ} ──
    body = _unwrap_immini(body)

    # ── Detect loại câu hỏi ──
    q: Optional[Question] = None

    # 1. \choiceTF → DS (Đúng/Sai)
    #    Hỗ trợ: \choiceTF  hoặc  \choiceTF[t]  hoặc  \choiceTF[f]
    choice_tf_match = re.search(r'\\choiceTF\s*(?:\[[^\]]*\])?\s*', body)
    if choice_tf_match:
        q = _parse_ds(body, choice_tf_match, solution, sol_raw,
                       section_topic, q_code)

    # 2. \choice → TN (Trắc nghiệm)
    if q is None:
        choice_match = re.search(r'\\choice\b\s*', body)
        if choice_match:
            q = _parse_tn(body, choice_match, solution,
                           section_topic, q_code)

    # 3. \shortans → TLN  (hỗ trợ \shortans{...} và \shortans[...]{...})
    if q is None:
        shortans_match = re.search(r'\\shortans\s*(?:\[[^\]]*\])?\s*\{', body)
        if shortans_match:
            q = _parse_tln(body, shortans_match, solution,
                            section_topic, q_code)

    # 4. TL (tự luận)
    if q is None:
        q = _parse_tl(body, solution, section_topic, q_code)

    # ── Gán ID có cấu trúc từ mã cũ %[...] ──
    if q and q_code:
        new_id = _convert_code_to_new_id(q_code)
        if new_id:
            q.question_id = new_id

    return q


# ══════════════════════════════════════════════════════════════════════════════
#  PARSERS CHO TỪNG LOẠI
# ══════════════════════════════════════════════════════════════════════════════

def _parse_tn(body: str, choice_match, solution: str,
              section_topic: str, q_code: str) -> Optional[Question]:
    """Parse câu TN: \\choice{\\True A}{B}{C}{D}"""
    q_text = _clean_latex(body[:choice_match.start()].strip())
    if not q_text:
        return None

    after_choice = body[choice_match.end():]
    raw_opts = _extract_brace_groups(after_choice, 4)
    if len(raw_opts) < 4:
        return None

    options = {}
    answer = "A"
    labels = ["A", "B", "C", "D"]
    for opt_raw, label in zip(raw_opts, labels):
        is_true, opt_clean = _check_true_marker(opt_raw)
        options[label] = _clean_latex(opt_clean)
        if is_true:
            answer = label

    return Question(
        qtype="TN",
        level=_guess_level(q_code),
        topic=section_topic,
        question=q_text,
        options=options,
        answer=answer,
        solution=_clean_latex(solution),
    )


def _parse_ds(body: str, choice_tf_match, solution: str, sol_raw: str,
              section_topic: str, q_code: str) -> Optional[Question]:
    """Parse câu DS: \\choiceTF{\\True a}{b}{c}{\\True d}"""
    q_text = _clean_latex(body[:choice_tf_match.start()].strip())
    if not q_text:
        return None

    after = body[choice_tf_match.end():]
    raw_items = _extract_brace_groups(after, 4)
    if len(raw_items) < 4:
        return None

    items = {}
    answers = {}
    item_solutions = {}
    labels = ["a", "b", "c", "d"]

    for label, raw in zip(labels, raw_items):
        is_true, clean = _check_true_marker(raw)
        items[label] = _clean_latex(clean)
        answers[label] = is_true

    # ── Parse lời giải chi tiết ──
    if sol_raw:
        item_sols = _parse_itemchoice_solutions(sol_raw)
        if not item_sols:
            item_sols = _parse_itemize_solutions(sol_raw)
        if item_sols:
            for label in labels:
                if label in item_sols:
                    item_solutions[label] = item_sols[label]

    return Question(
        qtype="DS",
        level=_guess_level(q_code),
        topic=section_topic,
        question=q_text,
        items=items,
        answers=answers,
        item_solutions=item_solutions,
        solution=_clean_latex(solution),
    )


def _parse_tln(body: str, shortans_match, solution: str,
               section_topic: str, q_code: str) -> Optional[Question]:
    """Parse câu TLN: \\shortans{đáp án} hoặc \\shortans[...]{đáp án}"""
    q_text = _clean_latex(body[:shortans_match.start()].strip())
    if not q_text:
        return None

    # Tìm dấu { cuối cùng trong match (sau [...] optional)
    after_cmd = body[shortans_match.start():]
    brace_pos = after_cmd.index('{') + shortans_match.start()
    ans_raw = _extract_brace_content(body, brace_pos)
    answer = _clean_latex(ans_raw).strip()

    return Question(
        qtype="TLN",
        level=_guess_level(q_code),
        topic=section_topic,
        question=q_text,
        answer=answer,
        solution=_clean_latex(solution),
    )


def _parse_tl(body: str, solution: str,
              section_topic: str, q_code: str) -> Optional[Question]:
    """Parse câu TL (tự luận)."""
    q_text = _clean_latex(body.strip())
    if not q_text:
        return None

    return Question(
        qtype="TL",
        level=_guess_level(q_code),
        topic=section_topic,
        question=q_text,
        solution=_clean_latex(solution),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _find_loigiai(body: str) -> int:
    """Tìm vị trí \\loigiai ở mức brace depth ≤ 1 (ngoài cùng).
    Trả về index hoặc -1.
    """
    for m in re.finditer(r'\\loigiai\s*(?:\{)', body):
        depth = 0
        for i in range(m.start()):
            if body[i] == '{':
                depth += 1
            elif body[i] == '}':
                depth -= 1
        if depth <= 1:
            return m.start()
    return -1


def _find_matching_brace(text: str, open_pos: int) -> int:
    """Tìm vị trí } đóng tương ứng với { tại open_pos."""
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return i
    return len(text) - 1


def _unwrap_immini(body: str) -> str:
    """Xử lý \\immini{nội dung câu hỏi}{hình vẽ TikZ}.
    Giữ lại nội dung câu hỏi và CẢ phần hình vẽ (để module TikZ bóc tách), 
    giữ phần sau \\immini (\\choice...).
    """
    m = re.search(r'\\immini\s*\{', body)
    if not m:
        return body

    before = body[:m.start()].strip()

    # Extract argument thứ 1 (nội dung câu hỏi)
    brace1_start = body.index('{', m.start())
    content = _extract_brace_content(body, brace1_start)
    brace1_end = _find_matching_brace(body, brace1_start)

    # Extract argument thứ 2 (hình vẽ TikZ)
    after_brace1 = body[brace1_end + 1:]
    rest_stripped = after_brace1.lstrip()
    brace2_offset = brace1_end + 1 + (len(after_brace1) - len(rest_stripped))
    after_immini = ""
    tikz_content = ""

    if rest_stripped.startswith('{'):
        brace2_end = _find_matching_brace(body, brace2_offset)
        tikz_content = _extract_brace_content(body, brace2_offset)
        after_immini = body[brace2_end + 1:]
    else:
        after_immini = after_brace1

    if tikz_content.strip():
        m_choice = re.search(r'\\choice\b|\\choiceTF\b', content)
        if m_choice:
            content = content[:m_choice.start()] + "\n" + tikz_content.strip() + "\n" + content[m_choice.start():]
        else:
            content += "\n" + tikz_content.strip()

    # Ghép lại: before + nội dung (đã kèm hình vẽ) + phần sau
    parts = []
    if before:
        parts.append(before)
    parts.append(content)
    if after_immini.strip():
        parts.append("\n" + after_immini.strip())

    return "\n".join(parts)


def _extract_brace_content(text: str, start_pos: int) -> str:
    """Extract nội dung bên trong cặp {} bắt đầu tại start_pos."""
    if start_pos >= len(text) or text[start_pos] != '{':
        return ""
    depth = 0
    i = start_pos
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start_pos + 1: i]
        i += 1
    return text[start_pos + 1:]


def _extract_brace_groups(text: str, count: int) -> list[str]:
    """Extract N nhóm {...} liên tiếp từ đầu text."""
    groups = []
    pos = 0
    for _ in range(count):
        idx = text.find('{', pos)
        if idx == -1:
            break
        content = _extract_brace_content(text, idx)
        groups.append(content)
        end = _find_matching_brace(text, idx)
        pos = end + 1
    return groups


def _check_true_marker(text: str) -> tuple[bool, str]:
    """Kiểm tra \\True hoặc \\choice*[True] ở đầu text.
    Returns (is_true, cleaned_text).
    """
    stripped = text.strip()

    m = re.match(r'\\True\s*', stripped)
    if m:
        return True, stripped[m.end():]

    m2 = re.match(r'\\choice\*\[True\]\s*', stripped, re.IGNORECASE)
    if m2:
        return True, stripped[m2.end():]

    return False, stripped


def _parse_itemchoice_solutions(sol_raw: str) -> dict[str, str]:
    """Parse lời giải dạng \\begin{itemchoice} \\itemch ... \\end{itemchoice}."""
    result = {}
    labels = ["a", "b", "c", "d"]

    m = re.search(r'\\begin\{itemchoice\}(.*?)\\end\{itemchoice\}',
                   sol_raw, re.DOTALL)
    content = m.group(1) if m else sol_raw

    parts = re.split(r'\\itemch\b\s*', content)
    parts = [p.strip() for p in parts if p.strip()]

    for i, label in enumerate(labels):
        if i < len(parts):
            result[label] = _clean_latex(parts[i])

    return result


def _parse_itemize_solutions(sol_raw: str) -> dict[str, str]:
    """Parse lời giải dạng \\begin{itemize} \\item ... hoặc chỉ \\item ..."""
    result = {}
    labels = ["a", "b", "c", "d"]

    parts = re.split(r'\\item\s+', sol_raw)
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) >= 4:
        for i, label in enumerate(labels):
            if i < len(parts):
                result[label] = _clean_latex(parts[i])

    return result


_OLD_LEVEL_TO_QUESTION: dict[str, str] = {
    # new-format code → Question.level
    "N": "NB",   # Nhận biết
    "T": "TH",   # Thông hiểu
    "V": "VD",   # Vận dụng
    "G": "VD",   # Vận dụng cao → gộp vào VD (3 mức)
}


def _guess_level(q_code: str) -> str:
    """Đoán mức độ (NB / TH / VD) từ mã câu hỏi cũ.

    Hỗ trợ cả 2 hệ thống ID:
      System B: [G][Subj][Ch][Level][Type]-[Q]   ví dụ 2D1B1-1, 2D1K5-3
      System A: [G][Level][Ch][Sub][Sub]-[Q]      ví dụ 1C6B1-2, 1K6BH-1

    Mapping mức độ (ký tự thứ 4 trong System B, thứ 2 trong System A):
      B, N, Y     → NB  (Nhận biết / Cơ bản / Yếu)
      H, T        → TH  (Thông hiểu)
      K, V, C     → VD  (Vận dụng / Khá / Cao)
      G           → VD  (Vận dụng cao, gộp vào VD)
    """
    if not q_code:
        return "TH"  # mặc định

    try:
        from core.latex_id_manager import (
            parse_old_id, OLD_LEVEL_MAP_A, OLD_LEVEL_MAP_B,
        )
        old = parse_old_id(q_code)
        if old:
            if old.system == "B":
                new_code = OLD_LEVEL_MAP_B.get(old.level_b, "N")
            else:
                new_code = OLD_LEVEL_MAP_A.get(old.level_a, "N")
            return _OLD_LEVEL_TO_QUESTION.get(new_code, "TH")
    except Exception:
        pass

    # Fallback: regex trực tiếp trên ký tự thứ 4 (System B)
    code_up = q_code.strip().upper()
    if len(code_up) >= 4:
        ch4 = code_up[3]
        _DIRECT_MAP = {
            "B": "NB", "N": "NB", "Y": "NB",
            "H": "TH", "T": "TH",
            "K": "VD", "V": "VD", "C": "VD", "G": "VD",
        }
        if ch4 in _DIRECT_MAP:
            return _DIRECT_MAP[ch4]

    return "TH"


def _clean_latex(text: str) -> str:
    """Làm sạch text LaTeX — giữ nguyên công thức $...$, bỏ markup thừa."""
    if not text:
        return ""

    # Bỏ comment LaTeX (% ...) — phải làm trước để không ảnh hưởng nội dung
    text = re.sub(r'(?<!\\)%.*$', '', text, flags=re.MULTILINE)

    # Bỏ các thẻ trích dẫn kiểu AI: [cite: 41, 42], [cite: 41], v.v.
    text = re.sub(r'\[cite[a-z]*:\s*[\d,\s]+\]', '', text, flags=re.IGNORECASE)

    # 1. Tự động xóa \begin{center}...\end{center} bọc ngoài \begin{tikzpicture} hoặc \begin{tabular}
    text = re.sub(
        r'\\begin\{center\}\s*(\\begin\{(?:tikzpicture|tabular)\}(?:\[[^\]]*\])?(?:\{[^}]*\})?.*?\\end\{(?:tikzpicture|tabular)\})\s*\\end\{center\}',
        r'\1',
        text,
        flags=re.DOTALL
    )

    # Bỏ environment wrappers
    for env in ("itemize", "enumerate", "itemchoice", "align", "align*"):
        text = re.sub(rf'\\begin\{{{env}\}}', '', text)
        text = re.sub(rf'\\end\{{{env}\}}', '', text)

    # Bỏ center độc lập (nếu còn sót lại)
    text = re.sub(r'\\begin\{center\}', '', text)
    text = re.sub(r'\\end\{center\}', '', text)

    # Bỏ các lệnh LaTeX phổ biến nhưng GIỮ nội dung
    for cmd in ("textbf", "textit", "underline", "emph", "text"):
        text = re.sub(rf'\\{cmd}\{{([^}}]*)\}}', r'\1', text)

    # Bỏ các lệnh LaTeX không cần
    text = re.sub(r'\\(?:caulc|cauds|caukq|Opensolutionfile|Closesolutionfile|indapan|'
                   r'allowdisplaybreaks|immmark|hfill)\b[^\n]*', '', text)

    # Bỏ khoảng trắng thừa
    text = re.sub(r'\n\s*\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()

    return text
