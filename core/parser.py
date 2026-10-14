"""
core/parser.py — Đọc file .docx, parse câu hỏi từ AI response, render LaTeX preview.
Hỗ trợ 3 định dạng ma trận:
  - Simple 6-col  (mặc định app: STT | Chủ đề | Mức độ | Loại câu | Mã câu | Yêu cầu)
  - BGD 19-col    (Bộ Giáo dục: bảng ma trận + bản đặc tả)
  - School 12-col (GV tự soạn: bảng tóm tắt + bản đặc tả)
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

from core.models import MatrixRow, MatrixData, DSItem, Question


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def ensure_math_braces(text: str) -> str:
    """Tự động bổ sung ``{...}`` cho công thức toán ``$...$`` chưa có braces.

    Quy tắc:
      - ``${formula}$``  → giữ nguyên (đã đúng).
      - ``$formula$``    → chuyển thành ``${formula}$``.
      - ``$$...$$``      → giữ nguyên (display math, không sửa).
      - ``\\\\$``         → giữ nguyên (escaped dollar).

    Ví dụ::

        ensure_math_braces('Tính $x^2$')          → 'Tính ${x^2}$'
        ensure_math_braces('Đã đúng ${x^2}$')     → 'Đã đúng ${x^2}$'
        ensure_math_braces('$|x| < 5$')           → '${|x| < 5}$'
        ensure_math_braces('$$x^2$$')             → '$$x^2$$'
    """
    result: list[str] = []
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]

        # Escaped dollar \$ → pass through unchanged
        if ch == '\\' and i + 1 < n and text[i + 1] == '$':
            result.append('\\$')
            i += 2
            continue

        if ch != '$':
            result.append(ch)
            i += 1
            continue

        # ── Found '$' ────────────────────────────────────────────────────────

        # Case 1: $$...$$  — display math, keep as-is
        if i + 1 < n and text[i + 1] == '$':
            close = text.find('$$', i + 2)
            if close >= 0:
                result.append(text[i: close + 2])
                i = close + 2
            else:
                result.append('$')
                i += 1
            continue

        # Case 2: ${...}$  — already correct, keep as-is
        if i + 1 < n and text[i + 1] == '{':
            # Scan for matching closing }$
            depth = 0
            j = i + 1
            found = False
            while j < n:
                c = text[j]
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        if j + 1 < n and text[j + 1] == '$':
                            result.append(text[i: j + 2])
                            i = j + 2
                            found = True
                        break
                elif c == '$' and depth == 0:
                    # Stray $ inside before closing } — not a clean ${...}$
                    break
                j += 1
            if not found:
                # Malformed ${... — output $ literally and continue
                result.append('$')
                i += 1
            continue

        # Case 3: $formula$  — needs wrapping to ${formula}$
        # Scan for the closing $, not crossing newlines (inline math)
        j = i + 1
        wrapped = False
        while j < n:
            c = text[j]
            if c == '$':
                # Make sure it's not $$
                if j + 1 < n and text[j + 1] == '$':
                    # Hit $$ — this inline formula is not well-formed, bail
                    break
                # Found closing $
                formula = text[i + 1: j]
                if formula.strip():
                    result.append('${' + formula + '}$')
                    i = j + 1
                    wrapped = True
                break
            elif c == '\n':
                # Don't cross newlines for inline math
                break
            j += 1

        if not wrapped:
            # No valid closing $ found — output literal $
            result.append('$')
            i += 1

    return ''.join(result)


def _unique_cells(row) -> list[str]:
    """Deduplicate merged cells in a docx table row (by tc identity)."""
    seen, result = set(), []
    for cell in row.cells:
        cid = id(cell._tc)
        if cid not in seen:
            seen.add(cid)
            result.append(cell.text.strip())
    return result


def _raw_grid(tbl_obj) -> list[list[str]]:
    """Full cell grid preserving column positions (merged cells repeat)."""
    return [[cell.text.strip() for cell in row.cells] for row in tbl_obj.rows]


def _extract_count(cell_text: str) -> int | None:
    """Extract integer count from a cell like '2', '1 (0.50)', '3,0'. Returns None on failure."""
    t = cell_text.strip()
    if not t:
        return None
    # "1 (0.50)" → extract leading integer
    m = re.match(r"^(\d+)", t)
    if m:
        return int(m.group(1))
    return None


def _extract_codes_from_cell(cell_text: str) -> list[str]:
    """Extract question codes from cell.

    Supports formats:
      C1, C13a, C13b          (C + number + optional suffix)
      TL1, TL1a, TL3b         (TL + number + optional suffix)
      TLN1, TLN2               (TLN + number — short-answer)
      TN1, TN2                 (TN + number + optional suffix)
      Câu 1, Câu 2,3           (Câu + number(s))
      1a, 2b                   (number + letter suffix)

    Lowercase variants (c1, tl1, tln1) are accepted; they are normalized to
    uppercase in the returned codes so downstream matching is consistent.
    """
    # Remove (NL ...) annotations
    cleaned = re.sub(r"\(NL\s*[\d.]+\)", "", cell_text, flags=re.IGNORECASE)

    codes = []

    # Pattern: "Câu 1", "Câu 2,3", "Câu 16, 17, 18"
    for m in re.finditer(r"[Cc]âu\s+([\d,\s]+)", cleaned):
        nums = re.findall(r"\d+", m.group(1))
        codes.extend(f"Câu {n}" for n in nums)

    # Pattern: TLN1, TLN2 (short-answer codes — must come BEFORE TN/TL to
    # avoid being shadowed by them)
    codes.extend(m.upper() for m in re.findall(r"TLN\d+", cleaned, re.IGNORECASE))

    # Pattern: TN1, TN2, TN10 (TN + number + optional a-d)
    codes.extend(m.upper() for m in re.findall(r"TN\d+[a-d]?", cleaned, re.IGNORECASE))

    # Pattern: TL1, TL1a, TL3b (TL + number + optional a-d) — but NOT TLN
    codes.extend(m.upper() for m in re.findall(r"TL\d+[a-d]?", cleaned, re.IGNORECASE))

    # Pattern: C1, c1, C13a (C + number + optional a-d, but NOT "Câu")
    # Case-insensitive so user matrices that mix C/c are handled correctly.
    for m in re.findall(r"(?<![âÂ])[Cc]\d+[a-d]?", cleaned):
        # Normalize leading letter to uppercase, preserve trailing a/b/c/d
        codes.append("C" + m[1:])

    # Pattern: standalone "1a", "2b" (number + letter, at word boundary)
    codes.extend(re.findall(r"\b\d+[a-d]\b", cleaned))

    # Deduplicate while preserving order
    seen = set()
    result = []
    for c in codes:
        c = c.strip()
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


def _normalize_level(text: str) -> str:
    """Normalize level text to standard code (NB/TH/VD). VDC → VD."""
    t = text.strip().rstrip(":").strip().upper()
    if t in ("NB", "NHẬN BIẾT", "NHẬN BIÊT", "BIẾT", "BIÊT"):  return "NB"
    if t in ("TH", "THÔNG HIỂU", "HIỂU"):   return "TH"
    if t in ("VDC", "VẬN DỤNG CAO"):         return "VD"   # VDC → VD
    if t in ("VD", "VẬN DỤNG"):              return "VD"
    # Partial match fallback
    if "VẬN DỤNG CAO" in t:                  return "VD"   # VDC → VD
    if "VẬN DỤNG" in t:                      return "VD"
    if "NHẬN BIẾT" in t or "NHẬN BIÊT" in t or t in ("BIẾT", "BIÊT"):  return "NB"
    if "THÔNG HIỂU" in t or t == "HIỂU":    return "TH"
    return ""


def _strict_level_header(text: str) -> str:
    """Like _normalize_level, but EXACT match only.

    Used when scanning header rows of a table to identify which columns are
    level columns. Avoids false positives where a long requirement-cell text
    that *contains* "Nhận biết …" would otherwise be classified as the NB
    column header.
    """
    t = text.strip().rstrip(":").strip()
    if not t or len(t) > 25:    # header cells are short labels, not sentences
        return ""
    tu = t.upper()
    if tu in ("NB", "NHẬN BIẾT", "NHẬN BIÊT", "BIẾT", "BIÊT"):
        return "NB"
    if tu in ("TH", "THÔNG HIỂU", "HIỂU"):
        return "TH"
    if tu in ("VDC", "VẬN DỤNG CAO"):
        return "VD"
    if tu in ("VD", "VẬN DỤNG"):
        return "VD"
    return ""


# ══════════════════════════════════════════════════════════════════════════════
#  TABLE CLASSIFICATION
# ══════════════════════════════════════════════════════════════════════════════

def _classify_table(tbl: list[list[str]]) -> str:
    """Phân loại bảng: 'spec' (Bản đặc tả), 'summary' (Ma trận đếm), 'other'."""
    if not tbl or len(tbl) < 2:
        return "other"

    # Check up to 5 header rows for keywords
    header_text = " ".join(cell for row in tbl[:5] for cell in row).upper()
    # Also check just rows 0-2 for type keywords (they're usually in merged headers)
    header_top = " ".join(cell for row in tbl[:3] for cell in row).upper()

    # Question-type indicators
    has_types = any(tp in header_text for tp in (
        "TRẮC NGHIỆM", "NPA", "ĐÚNG SAI", "ĐÚNG/SAI", "ĐÚNG-SAI",
        "TỰ LUẬN", "TRẢ LỜI NGẮN", "TNKQ",
        "NHIỀU LỰA CHỌN", "4 PHƯƠNG ÁN",
    ))

    # Level indicators (including abbreviated forms like "Biết"/"Hiểu")
    has_levels = any(lv in header_text for lv in (
        "NHẬN BIẾT", "NHẬN BIÊT", "THÔNG HIỂU", "VẬN DỤNG", "BIẾT", "BIÊT", "HIỂU",
    ))

    # Check data rows for question codes (TN1, TL1a, Câu 1, C1, etc.)
    # If we find codes → it's a spec table, not a summary
    _code_pat = re.compile(
        r"TN\d|TL\d|[Cc]\d+[a-d]?|[Cc]âu\s*\d+|\b\d+[a-d]\b", re.IGNORECASE)
    data_has_codes = False
    for row in tbl[2:min(8, len(tbl))]:
        for cell in row:
            if _code_pat.search(cell):
                data_has_codes = True
                break
        if data_has_codes:
            break

    # Summary table: has type headers AND level headers → count/summary table
    # Also: wide table (≥10 cols) with repeated level columns → summary
    max_cols = max((len(row) for row in tbl), default=0)
    if has_types and has_levels:
        level_count = sum(1 for row in tbl[:5] for cell in row
                         if _normalize_level(cell))
        # If data has codes like TN1, TL1a → it's a spec table, not summary
        if data_has_codes and level_count <= 8:
            return "spec"
        if level_count >= 6:
            return "summary"
        if max_cols >= 10 and level_count >= 3:
            return "summary"

    # Level-column spec: headers have level words (NB/TH/VD) as column
    # headers AND data rows contain question codes → spec
    if has_levels and data_has_codes:
        return "spec"

    # Spec table: has ≥2 of (Mức độ, Kiến thức, Yêu cầu, Dạng, Loại câu)
    spec_kw = sum(1 for kw in ("YÊU CẦU", "DẠNG", "LOẠI CÂU")
                  if kw in header_top)
    spec_kw += sum(1 for kw in ("MỨC ĐỘ",) if kw in header_top
                   and "MỨC ĐỘ ĐÁNH GIÁ" not in header_top)
    if "YÊU CẦU CẦN ĐẠT" in header_top:
        spec_kw += 1
    if "MỨC ĐỘ ĐÁNH GIÁ / YÊU CẦU" in header_top:
        spec_kw += 2

    if spec_kw >= 2:
        return "spec"

    # Fallback: wide table with types → summary
    if max_cols >= 8 and has_types:
        return "summary"
    if max_cols >= 8 and has_levels:
        return "summary"

    if any(kw in header_top for kw in ("KIẾN THỨC", "NỘI DUNG")) and spec_kw >= 1:
        return "spec"

    return "other"


# ══════════════════════════════════════════════════════════════════════════════
#  PARSE FILE .DOCX → MatrixData  (auto-detect format)
# ══════════════════════════════════════════════════════════════════════════════

def parse_matrix_file(filepath: str) -> MatrixData:
    """Parse .docx matrix file.  Auto-detects: BGD 19-col, School 12-col, Simple 6-col."""
    try:
        from docx import Document as DocxDocument
        import docx.table as _dt
        import docx.text.paragraph as _dp
        from docx.oxml.ns import qn as _qn
    except ImportError as exc:
        raise ImportError("Chưa cài python-docx\nChạy: pip install python-docx") from exc

    doc = DocxDocument(filepath)
    tables_unique: list[list[list[str]]] = []
    tables_raw: list = []          # raw Table objects (for summary grid)
    paragraphs_text: list[str] = []

    for child in doc.element.body.iterchildren():
        if child.tag == _qn("w:p"):
            t = _dp.Paragraph(child, doc).text.strip()
            if t:
                paragraphs_text.append(t)
        elif child.tag == _qn("w:tbl"):
            tbl = _dt.Table(child, doc)
            tables_unique.append([_unique_cells(row) for row in tbl.rows])
            tables_raw.append(tbl)

    title = next(
        (p for p in paragraphs_text
         if "MA TRẬN" in p.upper() or "ĐẶC TẢ" in p.upper()),
        "ĐỀ KIỂM TRA",
    )
    time_str = "90 phút"
    for p in paragraphs_text:
        m = re.search(r"(\d+)\s*phút", p)
        if m:
            time_str = m.group(0)
            break

    # ── Classify every table ─────────────────────────────────────────────
    spec_idx: Optional[int] = None
    summary_idx: Optional[int] = None
    for i, tbl in enumerate(tables_unique):
        cls = _classify_table(tbl)
        if cls == "spec" and spec_idx is None:
            spec_idx = i
        elif cls == "summary" and summary_idx is None:
            summary_idx = i

    # ── Strategy 1: Bản đặc tả (spec table) ─────────────────────────────
    if spec_idx is not None:
        raw_grid = _raw_grid(tables_raw[spec_idx]) if spec_idx < len(tables_raw) else None
        if raw_grid:
            # Try level-column spec (NB/TH/VD as column headers with codes)
            rows = _parse_level_col_spec_table(raw_grid)
            if rows:
                return MatrixData(title=title, time_str=time_str, rows=rows)
            # Try level-column count (NB/TH/VD headers with integer counts)
            rows = _parse_level_col_count_table(raw_grid)
            if rows:
                return MatrixData(title=title, time_str=time_str, rows=rows)
        # Try wide-spec (BGD-style spec with type×level sub-columns)
        raw_grid_spec = _raw_grid(tables_raw[spec_idx]) if spec_idx < len(tables_raw) else None
        if raw_grid_spec and len(raw_grid_spec[0]) >= 10:
            rows = _parse_wide_spec_table(raw_grid_spec)
            if rows:
                return MatrixData(title=title, time_str=time_str, rows=rows)
        # Fall back to standard spec
        rows = _parse_spec_table(tables_unique[spec_idx])
        if rows:
            return MatrixData(title=title, time_str=time_str, rows=rows)

    # ── Strategy 2: Summary / count table (ma trận đếm) ─────────────────
    if summary_idx is not None:
        rows = _parse_summary_to_rows(tables_raw[summary_idx])
        if rows:
            return MatrixData(title=title, time_str=time_str, rows=rows)

    # ── Strategy 3: legacy keyword heuristic ─────────────────────────────
    for tbl in tables_unique:
        if tbl and any(
            "Kiến thức" in str(r) or "Mức độ" in str(r) or "Dạng" in str(r)
            for r in tbl[:2]
        ):
            rows = _parse_spec_table(tbl)
            if rows:
                return MatrixData(title=title, time_str=time_str, rows=rows)

    # Try second table, then first
    for idx in ([1, 0] if len(tables_unique) > 1 else [0] if tables_unique else []):
        rows = _parse_spec_table(tables_unique[idx])
        if rows:
            return MatrixData(title=title, time_str=time_str, rows=rows)

    # ── Strategy 4: mammoth fallback ─────────────────────────────────────
    return _parse_matrix_mammoth(filepath, title, time_str)


# ══════════════════════════════════════════════════════════════════════════════
#  SPEC TABLE PARSER  (Bản đặc tả / Simple 6-col)
# ══════════════════════════════════════════════════════════════════════════════

def _parse_spec_table(spec_table):
    raw_rows = _extract_raw_rows(spec_table)
    if not raw_rows:
        return []
    expanded = _expand_rows(raw_rows)
    return _group_ds_rows(expanded)


def _detect_spec_columns(header_row: list[str]) -> dict[str, int]:
    """Auto-detect column indices for a spec table header."""
    cols: dict[str, int] = {}
    for i, cell in enumerate(header_row):
        text = cell.upper().strip()
        if not text:
            continue
        if ("STT" in text or text == "TT") and "stt" not in cols:
            cols["stt"] = i
        elif any(kw in text for kw in ("KIẾN THỨC", "NỘI DUNG", "CHỦ ĐỀ", "CHƯƠNG")) \
                and "topic" not in cols:
            cols["topic"] = i
        elif "MỨC" in text and "level" not in cols:
            cols["level"] = i
        elif any(kw in text for kw in ("DẠNG", "LOẠI CÂU", "HÌNH THỨC")) \
                and "qtype" not in cols:
            cols["qtype"] = i
        elif any(kw in text for kw in ("CÂU HỎI", "MÃ CÂU", "SỐ CÂU")) \
                and "codes" not in cols:
            cols["codes"] = i
        elif "CÂU" in text and "codes" not in cols:
            cols["codes"] = i
        elif any(kw in text for kw in ("YÊU CẦU", "MÔ TẢ")) \
                and "requirement" not in cols:
            cols["requirement"] = i
        # Combined "Mức độ đánh giá / Yêu cầu cần đạt" column → treat as both level+requirement
        if "MỨC ĐỘ" in text and "YÊU CẦU" in text:
            cols["level"] = i
            cols["requirement"] = i
    return cols


def _extract_raw_rows(spec_table):
    """Extract raw row dicts from spec table — auto-detect columns, then fixed fallback."""
    if not spec_table or len(spec_table) < 2:
        return []

    cols = _detect_spec_columns(spec_table[0])

    # If auto-detection found at least level + (topic or requirement) → use flex
    if "level" in cols and ("topic" in cols or "requirement" in cols):
        rows = _extract_with_col_map(spec_table, cols)
        if rows:
            return rows

    # Fallback: fixed-position extraction (original Simple 6-col logic)
    return _extract_fixed_position(spec_table)


def _extract_with_col_map(spec_table, cols: dict[str, int]):
    """Extract rows using auto-detected column mapping."""
    raw_rows = []
    last_topic = ""
    last_level = ""

    for row in spec_table[1:]:
        def _get(field: str) -> str:
            idx = cols.get(field, -1)
            return row[idx].strip() if 0 <= idx < len(row) else ""

        codes_raw = _get("codes")
        # Skip rows that are clearly summary / footer ("Tổng câu", "Tỉ lệ %",
        # "Tổng điểm") — they have no real codes.
        topic_raw_for_check = _get("topic").upper()
        if any(kw in topic_raw_for_check for kw in (
                "TỔNG CÂU", "TỔNG ĐIỂM", "TỔNG SỐ", "TỈ LỆ", "TỔNG CỘNG")):
            continue

        level = _normalize_level(_get("level"))
        # If level is empty, inherit from previous row only when the row
        # clearly continues the previous one (has a code in the codes column).
        # This handles spec tables where teachers leave 'Mức độ' blank for
        # extra codes belonging to the same level as the row above (e.g.
        # row 20 of the user's matrix: empty Mức độ, code C14).
        if not level:
            if codes_raw and last_level:
                level = last_level
            else:
                continue
        last_level = level

        topic = _get("topic")
        if not topic and last_topic:
            topic = last_topic
        if topic:
            last_topic = topic

        # Note: dtype is NOT inherited from previous row — it would mis-classify
        # rows like 'TLN1' (with empty Dạng) as DS just because the previous
        # row was Đ-S. Let _detect_qtype derive the type from the code itself.
        dtype     = _get("qtype")
        req       = _get("requirement")
        stt       = _get("stt")

        qtype = _detect_qtype(dtype, codes_raw)
        codes = _extract_codes_from_cell(codes_raw)
        if not codes:
            codes = re.findall(r"(c\d+|TL\d+|\d+[a-d])", codes_raw, re.IGNORECASE)
        if not codes:
            codes = [codes_raw] if codes_raw else ["?"]

        raw_rows.append({
            "stt":         stt,
            "topic":       topic,
            "level":       level,
            "qtype":       qtype,
            "codes":       [c.strip() for c in codes],
            "requirement": req or f"{topic} [{level}]",
        })
    return raw_rows


def _extract_fixed_position(spec_table):
    """Original fixed-position extraction for Simple 6-col format."""
    raw_rows = []
    for row in spec_table[1:]:
        if len(row) < 4:
            continue
        if len(row) >= 6:
            stt, topic, level, dtype, codes_raw, req = (
                row[0], row[1], row[2], row[3], row[4], row[5])
        elif len(row) == 5:
            stt, topic, level, dtype, codes_raw, req = (
                "", row[0], row[1], row[2], row[3], row[4])
        else:
            continue

        level = _normalize_level(level)
        if not level:
            continue

        qtype = _detect_qtype(dtype, codes_raw)
        codes = re.findall(r"(c\d+|TL\d+|\d+[a-d])", codes_raw, re.IGNORECASE)
        if not codes:
            codes = [codes_raw.strip()] if codes_raw.strip() else ["?"]

        raw_rows.append({
            "stt":         stt.strip(),
            "topic":       topic.strip(),
            "level":       level,
            "qtype":       qtype,
            "codes":       [c.strip() for c in codes],
            "requirement": req.strip(),
        })
    return raw_rows


# ══════════════════════════════════════════════════════════════════════════════
#  SUMMARY TABLE PARSER  (BGD 19-col / School 12-col → MatrixRows)
# ══════════════════════════════════════════════════════════════════════════════

def _detect_summary_qtype(text: str) -> str:
    """Detect question type from a summary-table header cell."""
    t = text.upper().strip()
    if not t:
        return ""
    # Check specific sub-types FIRST (before generic TNKQ catch-all)
    if ("ĐÚNG" in t and "SAI" in t) or t == "ĐS":
        return "DS"
    if "TRẢ LỜI NGẮN" in t or t == "TLN":
        return "TLN"
    if "TỰ LUẬN" in t or "TỰ LUÂN" in t or t in ("TL", "TULUAN"):
        return "TL"
    if "LUẬN" in t:
        return "TL"
    # Now check for TN (multiple choice)
    if "NPA" in t or "4 PHƯƠNG ÁN" in t:
        return "TN"
    if "NHIỀU LỰA CHỌN" in t:
        return "TN"
    if "TRẮC NGHIỆM" in t:
        return "TN"
    # Generic TNKQ — only if no sub-type detected above
    if "TNKQ" in t:
        return "TN"
    return ""


def _build_summary_col_map(grid: list[list[str]]):
    """Build column map for a summary/count table.

    Returns
    -------
    col_map : dict[int, tuple[str, str]]   col_index → (qtype, level)
    topic_col : int
    content_col : int   (-1 if absent)
    data_start : int    first data-row index
    """
    if not grid:
        return {}, 1, -1, 0

    ncols = len(grid[0])

    # ── Find where numeric data starts ───────────────────────────────────
    data_start = 2
    for ri in range(1, min(len(grid), 6)):
        # Count cells that contain numeric data (plain "2" or "1 (0.50)")
        num_count = sum(1 for c in grid[ri][2:]
                        if _extract_count(c) is not None and _extract_count(c) > 0)
        if num_count >= 2:
            data_start = ri
            break

    # ── Find type-label spans in header rows ─────────────────────────────
    # In raw grid, merged cells repeat the same text → detect spans
    # Scan ALL header rows, keep the one with MOST type ranges (most specific)
    type_col_ranges: list[tuple[int, int, str]] = []
    best_ranges: list[tuple[int, int, str]] = []
    for hri in range(min(data_start, 5)):
        if hri >= len(grid):
            break
        row = grid[hri]
        candidate: list[tuple[int, int, str]] = []
        i = 0
        while i < len(row):
            qtype = _detect_summary_qtype(row[i])
            if qtype:
                start = i
                # Advance through merged (repeated) cells
                while i + 1 < len(row) and row[i + 1] == row[start]:
                    i += 1
                candidate.append((start, i, qtype))
            i += 1
        # Keep the row with most distinct type ranges
        if len(candidate) > len(best_ranges):
            best_ranges = candidate
    type_col_ranges = best_ranges

    # ── Find level labels in header rows ─────────────────────────────────
    col_map: dict[int, tuple[str, str]] = {}
    for hri in range(min(data_start, 4)):
        if hri >= len(grid):
            break
        for ci, cell in enumerate(grid[hri]):
            level = _normalize_level(cell)
            if not level:
                continue
            # Match to the enclosing type span
            for s, e, qtype in type_col_ranges:
                if s <= ci <= e:
                    col_map[ci] = (qtype, level)
                    break

    # ── Find topic / content columns ─────────────────────────────────────
    topic_col = 1
    content_col = -1
    row0 = grid[0]
    for ci, cell in enumerate(row0):
        t = cell.upper()
        if any(kw in t for kw in ("CHƯƠNG", "CHỦ ĐỀ")):
            topic_col = ci
        elif "NỘI DUNG" in t and content_col < 0:
            content_col = ci

    return col_map, topic_col, content_col, data_start


def _parse_summary_to_rows(tbl_obj) -> list[MatrixRow]:
    """Parse a summary/count table into MatrixRows (when no Bản đặc tả available)."""
    from config import POINTS_MAP

    grid = _raw_grid(tbl_obj)
    if not grid or len(grid) < 3:
        return []

    col_map, topic_col, content_col, data_start = _build_summary_col_map(grid)
    if not col_map:
        return []

    rows: list[MatrixRow] = []
    stt_counter = 0

    for ri in range(data_start, len(grid)):
        row = grid[ri]
        if not row or len(row) < 3:
            continue

        # Skip total / footer rows
        row_text = " ".join(row).upper()
        if any(kw in row_text for kw in ("TỔNG", "CỘNG", "TỈ LỆ", "TỔNG SỐ")):
            continue

        topic = row[topic_col] if topic_col < len(row) else ""
        if content_col >= 0 and content_col != topic_col and content_col < len(row):
            c = row[content_col]
            if c and c != topic:
                topic = f"{topic} – {c}"
        topic = topic.strip()
        if not topic:
            continue

        stt_counter += 1
        has_data = False

        # ── Non-DS types ─────────────────────────────────────────────────
        for ci in sorted(col_map.keys()):
            qtype, level = col_map[ci]
            if qtype == "DS" or ci >= len(row):
                continue
            count = _extract_count(row[ci])
            if count is None:
                continue
            if count <= 0:
                continue
            has_data = True
            pts = POINTS_MAP.get(qtype, 1.0)
            for k in range(count):
                code = f"{qtype}{stt_counter}.{k + 1}"
                rows.append(MatrixRow(
                    stt=str(stt_counter), topic=topic, level=level,
                    qtype=qtype, codes=[code],
                    requirement=f"{topic} [{level}]",
                    points=pts, enabled=True,
                ))

        # ── DS: collect all items for this topic, group by 4 ─────────────
        ds_levels: list[str] = []
        for ci in sorted(col_map.keys()):
            qtype, level = col_map[ci]
            if qtype != "DS" or ci >= len(row):
                continue
            count = _extract_count(row[ci])
            if count is None:
                continue
            if count > 0:
                ds_levels.extend([level] * count)
                has_data = True

        q_idx = 0
        while ds_levels:
            batch = ds_levels[:4]
            ds_levels = ds_levels[4:]
            q_idx += 1
            # Pad to 4 items if needed
            while len(batch) < 4:
                batch.append(batch[-1] if batch else "NB")

            items: list[DSItem] = []
            for idx, lv in enumerate(batch):
                label = chr(ord('a') + idx)
                code = f"DS{stt_counter}.{q_idx}{label}"
                items.append(DSItem(
                    label=label, level=lv,
                    requirement=f"{topic} [{lv}]", code=code,
                ))

            lvl_order = {"NB": 0, "TH": 1, "VD": 2}
            top_lv = max(items, key=lambda x: lvl_order.get(x.level, 0)).level
            all_reqs = " | ".join(
                f"ý {s.label} [{s.level}]: {s.requirement}" for s in items
            )
            rows.append(MatrixRow(
                stt=str(stt_counter), topic=topic, level=top_lv,
                qtype="DS", codes=[s.code for s in items],
                requirement=all_reqs, points=1.0, enabled=True,
                ds_items=items,
            ))

        if not has_data:
            stt_counter -= 1  # undo counter for empty rows

    return rows


# ══════════════════════════════════════════════════════════════════════════════
#  LEVEL-COLUMN SPEC PARSER  (Bản đặc tả with NB/TH/VD/VDC as column headers)
# ══════════════════════════════════════════════════════════════════════════════

def _parse_level_col_spec_table(tbl: list[list[str]]) -> list[MatrixRow]:
    """Parse spec tables where level names are column headers and cells contain codes.

    Format (8-10 cols):
      Row 0: STT | Chương/Chủ đề | Nội dung | Mức độ đánh giá | Nhận biết | Thông hiểu | Vận dụng | VDC
      Row 1: (same or sub-header)
      Row 2+: data with codes like TN1, TL1a, Câu 1 in level columns
    """
    from config import POINTS_MAP

    if not tbl or len(tbl) < 3:
        return []

    # ── Find level columns — STRICT match, header rows only ──
    # Only treat a cell as a "level column header" if it is exactly one of the
    # short level labels (NB / Nhận biết / TH / …). This avoids false positives
    # like requirement cells beginning with "Nhận biết khái niệm…" being
    # picked up as the NB column.
    # Heuristic for "where the headers stop": the first row whose col 0 is a
    # plain integer (1, 2, …) is data; anything before is header.
    header_end = 0
    for ri in range(min(4, len(tbl))):
        c0 = tbl[ri][0].strip() if tbl[ri] else ""
        if re.match(r"^\d+$", c0):
            header_end = ri
            break
    else:
        header_end = min(2, len(tbl))

    level_cols: dict[int, str] = {}  # col_idx -> level
    for hdr_row in tbl[:max(1, header_end)]:
        for ci, cell in enumerate(hdr_row):
            lv = _strict_level_header(cell)
            if lv and ci not in level_cols:
                level_cols[ci] = lv

    # Need at least 2 distinct level columns to be a real "level-column" table.
    # A single hit is almost always a false positive (e.g. cell happens to read
    # exactly "NB" because it's a data-row level value, not a header).
    if len(level_cols) < 2:
        return []

    # ── Find topic, content, requirement columns ──
    topic_col = -1
    content_col = -1
    req_col = -1

    for ci, cell in enumerate(tbl[0]):
        t = cell.upper().strip()
        if ci in level_cols:
            continue
        if any(kw in t for kw in ("CHỦ ĐỀ", "CHƯƠNG")):
            topic_col = ci
        elif any(kw in t for kw in ("NỘI DUNG", "KIẾN THỨC", "ĐƠN VỊ")):
            content_col = ci
        elif any(kw in t for kw in ("MỨC ĐỘ", "YÊU CẦU")):
            req_col = ci

    if topic_col < 0 and content_col >= 0:
        topic_col = content_col
        content_col = -1

    # ── Find data start row (first row with codes in level columns) ──
    code_pat = re.compile(
        r"TN\d|TL\d|[Cc]\d+[a-d]?|[Cc]âu\s*\d+|\b\d+[a-d]\b", re.IGNORECASE)
    data_start = max(2, header_end)
    for ri in range(1, min(5, len(tbl))):
        for ci in level_cols:
            if ci < len(tbl[ri]) and code_pat.search(tbl[ri][ci]):
                data_start = ri
                break
        else:
            continue
        break

    # ── Parse data rows ──
    rows: list[MatrixRow] = []
    stt_counter = 0
    last_topic = ""

    # Determine which columns are "identity" columns (STT, topic, content)
    # — skip req_col and level cols when checking for summary-row keywords
    _id_cols = sorted(set(c for c in [0, topic_col, content_col] if c >= 0))

    for ri in range(data_start, len(tbl)):
        row = tbl[ri]
        if not row or len(row) < 3:
            continue
        # Only check identity columns for summary keywords to avoid false
        # positives from requirement text containing "tổng", "cộng"
        id_text = " ".join(row[c] for c in _id_cols if c < len(row)).upper()
        if any(kw in id_text for kw in ("TỔNG", "TỈ LỆ", "CỘNG", "TỈ LỆ CHUNG")):
            continue

        # Topic
        topic = row[topic_col].strip() if 0 <= topic_col < len(row) else ""
        # Clean "Chủ đề:" prefix
        topic = re.sub(r"^Chủ\s*đề\s*:\s*", "", topic, flags=re.IGNORECASE).strip()
        if content_col >= 0 and content_col < len(row):
            c = row[content_col].strip()
            c = re.sub(r"^Nội\s*dung\s*\d*\s*:\s*", "", c, flags=re.IGNORECASE).strip()
            if c and c != topic:
                topic = f"{topic} – {c}" if topic else c
        if not topic and last_topic:
            topic = last_topic
        if topic:
            last_topic = topic

        # Requirement (from "Mức độ đánh giá" column)
        req = row[req_col].strip() if 0 <= req_col < len(row) else ""

        has_any = False
        for ci in sorted(level_cols.keys()):
            level = level_cols[ci]
            if ci >= len(row):
                continue
            cell = row[ci].strip()
            if not cell:
                continue

            codes = _extract_codes_from_cell(cell)
            if not codes:
                continue

            if not has_any:
                stt_counter += 1
                has_any = True

            # Detect qtype from codes
            for code in codes:
                cu = code.upper()
                if cu.startswith("TN") or cu.startswith("CÂU"):
                    qtype = "TN"
                elif cu.startswith("TL"):
                    qtype = "TL"
                elif cu.startswith("C") and re.match(r"C\d", cu):
                    qtype = "TN"
                else:
                    qtype = "TL"

                pts = POINTS_MAP.get(qtype, 1.0)
                rows.append(MatrixRow(
                    stt=str(stt_counter), topic=topic, level=level,
                    qtype=qtype, codes=[code],
                    requirement=req or f"{topic} [{level}]",
                    points=pts, enabled=True,
                ))

    return _group_ds_rows_from_list(rows)


def _parse_level_col_count_table(tbl: list[list[str]]) -> list[MatrixRow]:
    """Parse tables where level names are column headers and cells contain counts.

    Format (8 cols):
      Row 0: STT | Chương/Chủ đề | Nội dung | Yêu cầu cần đạt | NB | TH | VD | VDC
      Row 1+: data with integer counts in level columns
    """
    from config import POINTS_MAP

    if not tbl or len(tbl) < 2:
        return []

    # ── Find level columns — STRICT match, header rows only ──
    # Same rationale as _parse_level_col_spec_table: only short, exact level
    # labels in header rows count.
    header_end = 0
    for ri in range(min(4, len(tbl))):
        c0 = tbl[ri][0].strip() if tbl[ri] else ""
        if re.match(r"^\d+$", c0):
            header_end = ri
            break
    else:
        header_end = min(2, len(tbl))

    level_cols: dict[int, str] = {}
    for hdr_row in tbl[:max(1, header_end)]:
        for ci, cell in enumerate(hdr_row):
            lv = _strict_level_header(cell)
            if lv and ci not in level_cols:
                level_cols[ci] = lv

    if len(level_cols) < 2:
        return []

    # ── Find topic, content, requirement columns ──
    topic_col = -1
    content_col = -1
    req_col = -1

    for ci, cell in enumerate(tbl[0]):
        t = cell.upper().strip()
        if ci in level_cols:
            continue
        if any(kw in t for kw in ("CHỦ ĐỀ", "CHƯƠNG")):
            topic_col = ci
        elif any(kw in t for kw in ("NỘI DUNG", "KIẾN THỨC", "ĐƠN VỊ")):
            content_col = ci
        elif any(kw in t for kw in ("YÊU CẦU", "MÔ TẢ")):
            req_col = ci

    if topic_col < 0 and content_col >= 0:
        topic_col = content_col
        content_col = -1

    # ── Verify data rows have counts (not codes) ──
    has_counts = False
    for ri in range(1, min(4, len(tbl))):
        for ci in level_cols:
            if ci < len(tbl[ri]):
                cell = tbl[ri][ci].strip()
                if cell and re.match(r"^\d+$", cell):
                    has_counts = True
                    break
        if has_counts:
            break

    if not has_counts:
        return []

    # ── Parse data rows ──
    rows: list[MatrixRow] = []
    stt_counter = 0
    last_topic = ""
    qtype = "TN"
    pts = POINTS_MAP.get(qtype, 1.0)

    for ri in range(1, len(tbl)):
        row = tbl[ri]
        if not row or len(row) < 3:
            continue
        # Skip summary/total rows — data rows have numeric STT;
        # summary rows have "Tổng", "Tỉ lệ %", etc. in cell 0
        cell0 = row[0].strip().upper()
        if not re.match(r"^\d+$", cell0):
            continue

        # Topic
        topic = row[topic_col].strip() if 0 <= topic_col < len(row) else ""
        topic = re.sub(r"^Chủ\s*đề\s*:\s*", "", topic, flags=re.IGNORECASE).strip()
        if content_col >= 0 and content_col < len(row):
            c = row[content_col].strip()
            if c and c != topic:
                topic = f"{topic} – {c}" if topic else c
        if not topic and last_topic:
            topic = last_topic
        if topic:
            last_topic = topic

        # Requirement
        req = row[req_col].strip() if 0 <= req_col < len(row) else ""

        stt_counter += 1
        for ci in sorted(level_cols.keys()):
            level = level_cols[ci]
            if ci >= len(row):
                continue
            cell = row[ci].strip()
            count = _extract_count(cell)
            if not count or count <= 0:
                continue

            for k in range(count):
                rows.append(MatrixRow(
                    stt=str(stt_counter), topic=topic, level=level,
                    qtype=qtype, codes=[f"Q{stt_counter}_{level}_{k+1}"],
                    requirement=req or f"{topic} [{level}]",
                    points=pts, enabled=True,
                ))

    return rows


# ══════════════════════════════════════════════════════════════════════════════
#  SHARED HELPERS  (used by both spec & summary parsers)
# ══════════════════════════════════════════════════════════════════════════════

def _parse_wide_spec_table(grid: list[list[str]]) -> list[MatrixRow]:
    """Parse a wide spec table (BGD-style with type×level sub-columns and code/requirement cells).

    These tables have headers like:
      R[0]: TT | Chương | Nội dung | Yêu cầu | Số câu hỏi... (merged across type cols)
      R[1]: ... | TNKQ (merged) | Tự luận (merged)
      R[2]: ... | Nhiều lựa chọn | Đúng sai | Trả lời ngắn | TL
      R[3]: ... | Biết | Hiểu | VD | Biết | Hiểu | VD | ...
    Data rows have codes in cells like "C1 C3 (NL 1.1)".
    """
    from config import POINTS_MAP

    if not grid or len(grid) < 4:
        return []

    col_map, topic_col, content_col, data_start = _build_summary_col_map(grid)
    if not col_map:
        return []

    # Check if this is really a spec table: data cells should contain codes, not just numbers
    has_codes = False
    for ri in range(data_start, min(len(grid), data_start + 3)):
        for ci in col_map:
            if ci < len(grid[ri]):
                cell = grid[ri][ci]
                if re.search(r"[Cc]\d+|TL\d+", cell):
                    has_codes = True
                    break
        if has_codes:
            break

    if not has_codes:
        return []  # Not a spec table — it's a summary/count table

    # Find requirement column (usually "Yêu cầu cần đạt")
    req_col = -1
    for ci, cell in enumerate(grid[0]):
        t = cell.upper()
        if "YÊU CẦU" in t or "MỨC ĐỘ ĐÁNH GIÁ" in t:
            req_col = ci
            break

    rows: list[MatrixRow] = []
    stt_counter = 0
    last_topic = ""

    for ri in range(data_start, len(grid)):
        row = grid[ri]
        if not row or len(row) < 3:
            continue
        # Skip footer rows
        row_text = " ".join(row).upper()
        if any(kw in row_text for kw in ("TỔNG", "TỈ LỆ", "CỘNG")):
            continue

        topic = row[topic_col] if topic_col < len(row) else ""
        if content_col >= 0 and content_col != topic_col and content_col < len(row):
            c = row[content_col]
            if c and c != topic:
                topic = f"{topic} – {c}"
        topic = topic.strip()
        if not topic and last_topic:
            topic = last_topic
        if topic:
            last_topic = topic

        req = row[req_col].strip() if 0 <= req_col < len(row) else ""

        has_any = False
        for ci in sorted(col_map.keys()):
            qtype, level = col_map[ci]
            if ci >= len(row):
                continue
            cell = row[ci].strip()
            if not cell:
                continue

            codes = _extract_codes_from_cell(cell)
            if not codes:
                # Try extracting as count (e.g. "1 (0.50)")
                count = _extract_count(cell)
                if count and count > 0:
                    codes = [f"{qtype}{stt_counter + 1}.{k+1}" for k in range(count)]
                else:
                    continue

            if not has_any:
                stt_counter += 1
                has_any = True

            pts = POINTS_MAP.get(qtype, 1.0)
            for code in codes:
                rows.append(MatrixRow(
                    stt=str(stt_counter), topic=topic, level=level,
                    qtype=qtype, codes=[code],
                    requirement=req or f"{topic} [{level}]",
                    points=pts, enabled=True,
                ))

    # Group DS rows
    return _group_ds_rows_from_list(rows)


def _group_ds_rows_from_list(rows: list[MatrixRow]) -> list[MatrixRow]:
    """Group consecutive DS single-item rows into DS questions of 4 items."""
    result: list[MatrixRow] = []
    i = 0
    while i < len(rows):
        if rows[i].qtype != "DS":
            result.append(rows[i])
            i += 1
            continue
        # Collect consecutive DS rows for same topic
        group = [rows[i]]
        j = i + 1
        while j < len(rows) and rows[j].qtype == "DS" and rows[j].topic == rows[i].topic:
            group.append(rows[j])
            j += 1

        # Batch by 4
        for batch_start in range(0, len(group), 4):
            batch = group[batch_start:batch_start + 4]
            items: list[DSItem] = []
            for idx, mr in enumerate(batch):
                label = chr(ord('a') + idx)
                code = mr.codes[0] if mr.codes else f"DS.{label}"
                items.append(DSItem(
                    label=label, level=mr.level,
                    requirement=mr.requirement, code=code,
                ))
            while len(items) < 4:
                items.append(DSItem(
                    label=chr(ord('a') + len(items)),
                    level=items[-1].level if items else "NB",
                    requirement=items[-1].requirement if items else "",
                    code=f"DS.pad{len(items)}",
                ))

            lvl_order = {"NB": 0, "TH": 1, "VD": 2}
            top_lv = max(items, key=lambda x: lvl_order.get(x.level, 0)).level
            all_reqs = " | ".join(f"ý {s.label} [{s.level}]: {s.requirement}" for s in items)
            result.append(MatrixRow(
                stt=batch[0].stt, topic=batch[0].topic, level=top_lv,
                qtype="DS", codes=[s.code for s in items],
                requirement=all_reqs, points=1.0, enabled=True,
                ds_items=items,
            ))
        i = j
    return result


def _detect_qtype(dtype: str, codes_raw: str) -> str:
    """Nhận dạng loại câu — hỗ trợ cả V1 (NPA) và V2 (TN)."""
    dtype_up = dtype.strip().upper().replace("-", "").replace(" ", "")
    # V1: NPA, TNPA → TN
    if "NPA" in dtype_up or "TNPA" in dtype_up:
        return "TN"
    if "TN" in dtype_up and "TLN" not in dtype_up and "TL" not in dtype_up:
        return "TN"
    # Đúng/Sai
    if "ĐS" in dtype_up or dtype_up == "DS" or "ĐÚNGSAI" in dtype_up:
        return "DS"
    # Trả lời ngắn
    if "TLN" in dtype_up or "NGẮN" in dtype.upper():
        return "TLN"
    # Tự luận
    if "TỰLUẬN" in dtype_up or "TULUAN" in dtype_up or "TL" in dtype_up:
        return "TL"
    # Suy từ mã câu — TLN PHẢI check trước TL vì cùng tiền tố
    codes_up = codes_raw.upper()
    if re.search(r"TLN\d", codes_up):     return "TLN"
    if re.search(r"TL\d", codes_up):      return "TL"
    if re.search(r"\d+[A-D]", codes_up):  return "DS"
    if re.search(r"C\d", codes_up):       return "TN"
    return "TL"


def _expand_rows(raw_rows):
    from config import POINTS_MAP
    expanded = []
    for r in raw_rows:
        if r["qtype"] == "DS":
            expanded.append(r)
            continue
        pts   = POINTS_MAP.get(r["qtype"], 1.0)
        codes = r["codes"]
        if len(codes) <= 1:
            expanded.append({**r, "points": pts, "enabled": True})
        else:
            for code in codes:
                expanded.append({**r, "codes": [code], "points": pts, "enabled": True})
    return expanded


def _ds_code_qnum(code: str) -> str:
    """Trích số đứng đầu mã DS (vd '1a' → '1', '2c' → '2'). Rỗng nếu không có."""
    m = re.match(r"^\s*(\d+)\s*[a-d]\s*$", code, re.IGNORECASE)
    return m.group(1) if m else ""


def _group_ds_rows(expanded):
    # ── Two-strategy grouping ──
    # 1) Codes like "1a/1b/1c/1d" → group by leading number REGARDLESS of
    #    topic/order. This matches Vietnamese exam matrices where ý a/b/c/d
    #    of one Đ-S question commonly span multiple chapters.
    # 2) Otherwise, fall back to consecutive same-stt-or-same-topic grouping.

    # ── Strategy 1: number-prefix grouping ──
    ds_indices = [i for i, r in enumerate(expanded) if r["qtype"] == "DS"]
    by_qnum: dict[str, list[int]] = {}
    have_numbered = False
    for i in ds_indices:
        for code in expanded[i]["codes"]:
            qn = _ds_code_qnum(code)
            if qn:
                by_qnum.setdefault(qn, []).append(i)
                have_numbered = True
                break  # one assignment per row is enough

    if have_numbered and len(by_qnum) >= 1 and all(len(v) >= 1 for v in by_qnum.values()):
        # Build result preserving original non-DS order; emit each DS group
        # at the position of its first member.
        result: list[MatrixRow] = []
        consumed: set[int] = set()
        # Map first-appearance index → qnum
        first_of_group = {min(idxs): qn for qn, idxs in by_qnum.items()}
        for idx, r in enumerate(expanded):
            if idx in consumed:
                continue
            if r["qtype"] != "DS":
                result.append(MatrixRow(
                    stt=r["stt"], topic=r["topic"], level=r["level"],
                    qtype=r["qtype"], codes=r["codes"],
                    requirement=r["requirement"],
                    points=r.get("points", 1.0), enabled=r.get("enabled", True),
                ))
                continue
            if idx in first_of_group:
                qn = first_of_group[idx]
                group = [expanded[j] for j in by_qnum[qn]]
                consumed.update(by_qnum[qn])
                ds_items: list[DSItem] = []
                for g in group:
                    for code in g["codes"]:
                        m = re.search(r"([a-d])$", code, re.IGNORECASE)
                        label = m.group(1).lower() if m else chr(ord("a") + len(ds_items))
                        ds_items.append(DSItem(
                            label=label, level=g["level"],
                            requirement=g["requirement"], code=code,
                        ))
                # Sort by label so a/b/c/d come out in order
                ds_items.sort(key=lambda x: x.label)
                # Pad to 4 ý for downstream renderers that assume exactly 4
                while len(ds_items) < 4:
                    pad = ds_items[-1] if ds_items else DSItem("a", "NB", "", "DS.pad")
                    ds_items.append(DSItem(
                        label=chr(ord("a") + len(ds_items)),
                        level=pad.level, requirement=pad.requirement,
                        code=f"DS.pad{len(ds_items)}",
                    ))
                lvl_order = {"NB": 0, "TH": 1, "VD": 2, "VDC": 3}
                top_level = max((it.level for it in ds_items),
                                key=lambda lv: lvl_order.get(lv, 0))
                # Topic = topic of the FIRST ý for stable display
                first = group[0]
                all_reqs = " | ".join(
                    f"ý {s.label} [{s.level}]: {s.requirement}" for s in ds_items
                )
                result.append(MatrixRow(
                    stt=first["stt"], topic=first["topic"], level=top_level,
                    qtype="DS", codes=[s.code for s in ds_items],
                    requirement=all_reqs, points=1.0, enabled=True,
                    ds_items=ds_items,
                ))
            # else: this is a DS row whose group anchor is earlier — skip (consumed)
        return result

    # ── Strategy 2: legacy consecutive grouping ──
    result: list[MatrixRow] = []
    i = 0
    while i < len(expanded):
        r = expanded[i]
        if r["qtype"] != "DS":
            result.append(MatrixRow(
                stt=r["stt"], topic=r["topic"], level=r["level"],
                qtype=r["qtype"], codes=r["codes"],
                requirement=r["requirement"],
                points=r.get("points", 1.0), enabled=r.get("enabled", True),
            ))
            i += 1
            continue

        group = [r]
        j = i + 1
        while j < len(expanded):
            nxt = expanded[j]
            if nxt["qtype"] != "DS":
                break
            same_stt  = bool(r["stt"]) and nxt["stt"] == r["stt"]
            diff_stt  = bool(r["stt"]) and bool(nxt["stt"]) and nxt["stt"] != r["stt"]
            same_topic = nxt["topic"] == r["topic"] or not nxt["topic"]
            if diff_stt:
                break
            if same_stt or same_topic:
                group.append(nxt)
                j += 1
            else:
                break

        ds_items: list[DSItem] = []
        for g in group:
            for code in g["codes"]:
                m = re.search(r"([a-d])$", code, re.IGNORECASE)
                label = m.group(1).lower() if m else chr(ord("a") + len(ds_items))
                ds_items.append(DSItem(
                    label=label, level=g["level"],
                    requirement=g["requirement"], code=code,
                ))

        lvl_order = {"NB": 0, "TH": 1, "VD": 2, "VDC": 3}
        top_level = max(
            (item.level for item in ds_items),
            key=lambda lv: lvl_order.get(lv, 0),
        )
        all_reqs = " | ".join(
            f"ý {s.label} [{s.level}]: {s.requirement}" for s in ds_items
        )
        result.append(MatrixRow(
            stt=r["stt"], topic=r["topic"], level=top_level,
            qtype="DS", codes=[s.code for s in ds_items],
            requirement=all_reqs, points=1.0, enabled=True,
            ds_items=ds_items,
        ))
        i = j
    return result


# ══════════════════════════════════════════════════════════════════════════════
#  MAMMOTH FALLBACK
# ══════════════════════════════════════════════════════════════════════════════

def _parse_matrix_mammoth(filepath: str, title: str, time_str: str) -> MatrixData:
    try:
        import mammoth
        with open(filepath, "rb") as fh:
            text = mammoth.extract_raw_text(fh).value
    except ImportError as exc:
        raise ImportError(
            "Không đọc được file docx.\nCài thêm: pip install mammoth"
        ) from exc

    rows: list[MatrixRow] = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            continue
        level = ""
        for p in parts:
            if p.upper() in ("NB", "TH", "VD", "VDC"):  # VDC tương thích ngược → VD
                level = p.upper()
                break
        if not level:
            continue
        qtype = _detect_qtype(parts[2] if len(parts) > 2 else "", "")
        rows.append(MatrixRow(
            stt="", topic=parts[0], level=level, qtype=qtype,
            codes=[], requirement=parts[-1], points=1.0, enabled=True,
        ))
    return MatrixData(title=title, time_str=time_str, rows=rows)


# ══════════════════════════════════════════════════════════════════════════════
#  PARSE AI RESPONSE → Question
#  Hỗ trợ cả V1 (LOAI: NPA) và V2 (LOAI: TN/DS/TLN/TL)
# ══════════════════════════════════════════════════════════════════════════════

def _extract_tikz_block(raw: str) -> str:
    """Trích khối \\begin{tikzpicture}...\\end{tikzpicture} đầu tiên trong raw.

    Trả chuỗi rỗng nếu không có. Không ép định dạng ngoài; block trả về giữ
    nguyên whitespace bên trong để tab_tikz có thể render trực tiếp.
    """
    if not raw:
        return ""
    m = re.search(
        r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
        raw,
        re.DOTALL,
    )
    return m.group(0).strip() if m else ""


# Xoá các dòng rác quanh hình TikZ mà AI hay sinh kèm:
#   • "Hình vẽ: <mô tả bằng lời>"   → app không cần, sẽ có PNG thay thế
#   • "TikZ:" tiền tố trước block   → pipeline sẽ nhận raw `\begin{tikzpicture}`
# Các dòng này bị xoá NGAY khi parse AI output → model sạch từ đầu.
_FIG_DESC_RE = re.compile(
    r"(?im)^[ \t]*(?:H[ìi]nh\s*v[ẽe]|Figure)\s*:[^\n]*\n?",
)
_TIKZ_PREFIX_RE = re.compile(
    r"(?im)^[ \t]*TikZ\s*:[ \t]*(?=\\begin\{tikzpicture\}|$)",
)


def _clean_figure_noise(text: str) -> str:
    """Xoá mô tả 'Hình vẽ: …' và tiền tố 'TikZ:' còn sót trong 1 field text."""
    if not text:
        return text
    out = _FIG_DESC_RE.sub("", text)
    out = _TIKZ_PREFIX_RE.sub("", out)
    
    # Bỏ \begin{center} ... \end{center} bọc quanh tikzpicture hoặc tabular
    out = re.sub(
        r'\\begin\{center\}\s*(\\begin\{(?:tikzpicture|tabular)\}(?:\[[^\]]*\])?(?:\{[^}]*\})?.*?\\end\{(?:tikzpicture|tabular)\})\s*\\end\{center\}',
        r'\1',
        out,
        flags=re.DOTALL
    )
    
    # Gộp dòng trống thừa tạo ra sau khi xoá
    lines = out.split("\n")
    squashed: list[str] = []
    prev_blank = False
    for ln in lines:
        blank = not ln.strip()
        if blank and prev_blank:
            continue
        squashed.append(ln)
        prev_blank = blank
    return "\n".join(squashed).strip()


def parse_one_question(raw: str) -> Optional[Question]:
    # Tách khối TikZ (nếu AI có chèn) TRƯỚC khi cắt block ===CAU===/===KETCAU===
    _tikz = _extract_tikz_block(raw)

    m = re.search(r"===CAU===(.*?)===KETCAU===", raw, re.DOTALL | re.IGNORECASE)
    block = m.group(1) if m else raw

    # Các key đã biết — dùng để phân biệt dòng key mới vs dòng tiếp tục
    _KNOWN_KEYS = {
        "LOAI", "MUCDO", "CHUONG", "NOIDUNG", "DAPAN", "LOIGIAI", "DIEM",
        "A", "B", "C", "D",
    }
    _KNOWN_KEYS_LOWER = {"a", "b", "c", "d"}

    def _is_key_line(line: str):
        """Kiểm tra dòng có phải KEY: value không.

        Nhận dạng các format:
          - ``KEY: value``   (chuẩn, dấu hai chấm)
          - ``A. value``     (dấu chấm — phổ biến trong đề thi)
          - ``A) value``     (ngoặc đơn)
        cho các key A, B, C, D (option câu TN) và a, b, c, d (ý câu DS).
        """
        stripped = line.strip()
        # Format chuẩn: KEY: value
        if ":" in stripped:
            k, _, v = stripped.partition(":")
            k_stripped = k.strip()
            if k_stripped.upper() in _KNOWN_KEYS:
                return (k_stripped.upper(), v.strip())
            if k_stripped in _KNOWN_KEYS_LOWER:
                return (k_stripped, v.strip())
        # Format dấu chấm/ngoặc đơn cho options A/B/C/D và ý a/b/c/d:
        #   "A. text", "B. text", "a. text", "b. text"
        #   "A) text", "B) text", "a) text", "b) text"
        m_dot = re.match(r'^([A-Da-d])[.)]\s+(.*)', stripped)
        if m_dot:
            k_char = m_dot.group(1)
            v_text = m_dot.group(2).strip()
            if k_char.upper() in ("A", "B", "C", "D"):
                return (k_char.upper(), v_text)
            if k_char in ("a", "b", "c", "d"):
                return (k_char, v_text)
        return None

    # Parse thông minh: hỗ trợ NOIDUNG và LOIGIAI nhiều dòng (bảng số liệu)
    kv: dict[str, str] = {}
    current_key: str = ""
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped:
            # Dòng trống — nếu đang thu thập NOIDUNG/LOIGIAI thì giữ xuống dòng
            if current_key in ("NOIDUNG", "LOIGIAI"):
                kv[current_key] = kv.get(current_key, "") + "\n"
            continue

        parsed = _is_key_line(stripped)
        if parsed is not None:
            k, v = parsed
            # Khi đang trong LOIGIAI, không cho format dấu chấm/ngoặc đơn
            # (a. / A.) thoát ra thành key mới — các marker đó thuộc về lời giải
            # và sẽ được tách sau bởi marker_re. Chỉ format KEY: value mới thoát.
            if current_key == "LOIGIAI" and k in ("A", "B", "C", "D", "a", "b", "c", "d"):
                colon_match = re.match(r'^[A-Da-d]\s*:', stripped)
                if not colon_match:
                    # Là "a. text" hoặc "a) text" trong LOIGIAI → nối tiếp
                    kv[current_key] = kv.get(current_key, "") + "\n" + stripped
                    continue
            if k not in kv:
                kv[k] = v
                current_key = k
            elif current_key in ("NOIDUNG", "LOIGIAI") and k == current_key:
                # Trùng key → bỏ qua (giữ giá trị đầu tiên)
                pass
            else:
                kv[k] = v
                current_key = k
        else:
            # Dòng không phải key → nối tiếp vào key hiện tại (bảng số liệu)
            if current_key and current_key in ("NOIDUNG", "LOIGIAI"):
                kv[current_key] = kv.get(current_key, "") + "\n" + stripped

    # Trim trailing newlines
    for k in kv:
        kv[k] = kv[k].strip()

    loai = kv.get("LOAI", "").upper()
    # V1 dùng "NPA" → map sang "TN"
    if loai == "NPA":
        loai = "TN"
    if loai not in ("TN", "DS", "TLN", "TL"):
        return None

    # ── Chuẩn hoá ${formula}$ cho mọi trường text ───────────────────────────
    # Nếu AI hoặc user nhập $formula$ (thiếu {}), tự động bổ sung thành ${formula}$
    _MATH_KEYS = {"NOIDUNG", "LOIGIAI", "A", "B", "C", "D", "a", "b", "c", "d"}
    for _k in _MATH_KEYS:
        if _k in kv and kv[_k]:
            kv[_k] = ensure_math_braces(kv[_k])

    q = Question(
        qtype=loai,
        level=kv.get("MUCDO", "").upper(),   # không bắt buộc — "" nếu không có
        topic=kv.get("CHUONG", ""),
        question=kv.get("NOIDUNG", ""),
        solution=kv.get("LOIGIAI", ""),
    )

    if loai == "TN":
        q.options = {k: kv.get(k, "") for k in "ABCD"}
        ans = kv.get("DAPAN", "A").strip().upper()
        q.answer = ans if ans in "ABCD" else "A"

    elif loai == "DS":
        items, answers, solutions = {}, {}, {}
        # Lấy nội dung các ý a,b,c,d
        for ky in "abcd":
            items[ky] = kv.get(ky.upper(), kv.get(ky, ""))
        # Lấy DAPAN
        for part in re.split(r"[,;]", kv.get("DAPAN", "")):
            if "=" in part:
                k2, v2 = part.split("=", 1)
                answers[k2.strip().lower()] = (
                    v2.strip().upper() in ("D", "Đ", "T", "TRUE", "1", "ĐÚNG")
                )
        # Xử lý LOIGIAI tổng hợp — hỗ trợ cả 2 định dạng:
        #   (cũ)  "a. ... | b. ... | c. ... | d. ..."  (một dòng, dùng pipe)
        #   (mới) "a. ...\nb. ...\nc. ...\nd. ..."     (nhiều dòng — chuẩn prompt
        #         template hiện tại)
        # Quét toàn bộ LOIGIAI bằng regex stateful: mỗi marker "a./b./c./d." có
        # thể đứng đầu chuỗi, sau pipe, hoặc đầu dòng. Lấy text từ marker này
        # đến marker tiếp theo (hoặc hết chuỗi) làm lời giải của ý đó.
        loigiai = kv.get("LOIGIAI", "")
        if loigiai:
            marker_re = re.compile(
                r'(?:^|\n|\|)\s*([a-d])[\.\):]\s*',
                re.MULTILINE | re.IGNORECASE,
            )
            markers = list(marker_re.finditer(loigiai))
            for i, m in enumerate(markers):
                label = m.group(1).lower()
                start = m.end()
                end = markers[i + 1].start() if i + 1 < len(markers) else len(loigiai)
                sol_text = loigiai[start:end].strip().rstrip('|').strip()
                if sol_text:
                    solutions[label] = sol_text
        # Nếu không tách được thì giữ nguyên fallback
        if not solutions:
            for ky in "abcd":
                solutions[ky] = kv.get(f"GIAI_{ky.upper()}", kv.get(f"GIAI_{ky}", ""))
        q.items          = items
        q.answers        = answers
        q.item_solutions = solutions

    elif loai in ("TLN", "TL"):
        try:
            q.points = float(kv.get("DIEM", "1.0").replace(",", "."))
        except ValueError:
            q.points = 0.5 if loai == "TLN" else 1.0
        if loai == "TLN":
            q.answer = kv.get("DAPAN", "")

    # ── Gán TikZ block nếu AI đã chèn ──
    if _tikz:
        q.tikz_code = _tikz

    # ── Dọn mô tả 'Hình vẽ: …' / tiền tố 'TikZ:' còn sót trong mọi field text ──
    # Tránh việc UI hiển thị 2 lần (ảnh + mô tả bằng lời) khi pipeline render xong.
    q.question = _clean_figure_noise(q.question)
    q.solution = _clean_figure_noise(q.solution)
    if q.items:
        q.items = {k: _clean_figure_noise(v) for k, v in q.items.items()}
    if q.options:
        q.options = {k: _clean_figure_noise(v) for k, v in q.options.items()}
    if q.item_solutions:
        q.item_solutions = {k: _clean_figure_noise(v) for k, v in q.item_solutions.items()}

    # ── Validation: reject incomplete questions ──
    if not q.question or len(q.question.strip()) < 10:
        return None  # Câu hỏi quá ngắn hoặc rỗng
    if loai == "TN":
        # Phải có đủ 4 phương án và đáp án
        if not all(q.options.get(k, "").strip() for k in "ABCD"):
            return None
        if q.answer not in "ABCD":
            return None
    elif loai == "DS":
        # Phải có đủ 4 ý và đáp án
        if not all(q.items.get(k, "").strip() for k in "abcd"):
            return None
        if len(q.answers) < 4:
            return None
    elif loai == "TLN":
        # Phải có đáp số
        if not q.answer or not q.answer.strip():
            return None

    return q


# ══════════════════════════════════════════════════════════════════════════════
#  LaTeX → Unicode PREVIEW (V1 + V2 merged)
# ══════════════════════════════════════════════════════════════════════════════

_LATEX_UNICODE = [
    (r"\alpha","α"),(r"\beta","β"),(r"\gamma","γ"),(r"\delta","δ"),
    (r"\pi","π"),(r"\theta","θ"),(r"\lambda","λ"),(r"\mu","μ"),
    (r"\sigma","σ"),(r"\omega","ω"),(r"\infty","∞"),(r"\phi","φ"),
    (r"\leq","≤"),(r"\geq","≥"),(r"\neq","≠"),(r"\le","≤"),
    (r"\ge","≥"),(r"\ne","≠"),(r"\approx","≈"),(r"\equiv","≡"),
    (r"\rightarrow","→"),(r"\leftarrow","←"),
    (r"\Rightarrow","⇒"),(r"\Leftrightarrow","⟺"),
    (r"\times","×"),(r"\div","÷"),(r"\pm","±"),(r"\cdot","·"),
    (r"\in","∈"),(r"\notin","∉"),(r"\cup","∪"),(r"\cap","∩"),
    (r"\subset","⊂"),(r"\emptyset","∅"),
    (r"\sin","sin"),(r"\cos","cos"),(r"\tan","tan"),
    (r"\log","log"),(r"\ln","ln"),(r"\lim","lim"),
    (r"\left(","("),(r"\right",")"),(r"\left[","["),(r"\right]","]"),
    (r"\left\{","{"),(r"\right\}","}"),
    (r"\,", " "),(r"\:", " "),(r"\!", ""),(r"\\","↵"),(r"\%","%"),
]


def latex_to_preview(text: str) -> str:
    if "$" not in text:
        return text
    result = []
    i = 0
    while i < len(text):
        if text[i] == "$":
            j = text.find("$", i + 1)
            if j == -1:
                result.append(text[i:])
                break
            formula = text[i + 1: j]
            for cmd, uni in _LATEX_UNICODE:
                formula = formula.replace(cmd, uni)
            formula = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1/\2)", formula)
            formula = re.sub(r"frac\{([^}]*)\}\{([^}]*)\}", r"(\1/\2)", formula)
            formula = re.sub(r"\^\{([^}]+)\}", r"^\1", formula)
            formula = re.sub(r"_\{([^}]+)\}", r"_\1", formula)
            formula = formula.replace("{", "").replace("}", "")
            formula = re.sub(r"\\[a-zA-Z]+", "", formula)
            result.append(formula)
            i = j + 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)