"""
export/word_exporter.py — Xuất đề kiểm tra ra Word chuẩn giáo viên THPT.
Cập nhật: cấu trúc xuất câu Đúng/Sai — câu hỏi chính, 4 ý, sau đó in đậm "Lời giải." và lời giải từng ý.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

from core.models import ExamData, Question
from core.generator import shuffle_exam, build_answer_key
from config import MA_DE_LABELS

from pathlib import Path as _Path


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

_TAB_4COL = [5.0, 9.5, 14.0]
_TAB_2COL = [8.0]
_WRAP_THRESHOLD = 32          # Tăng từ 24→32 để ưu tiên layout ngang nhiều hơn
_OPT_INDENT    = 0.5
_DS_ITEM_INDENT = 0.5
_SOL_INDENT     = 1.0
_DS_SOL_INDENT  = 1.5

_SPACE_AFTER_QUESTION = 2
_SPACE_AFTER_OPTIONS  = 8
_SPACE_AFTER_SECTION  = 4


def export_to_word(
    exam_data: ExamData,
    output_path: str,
    include_solution: bool = True,
    math_mode: str = "text",
    school_name: str = "",
    teacher_name: str = "",
    auto_convert_tables: bool = True,
) -> None:
    # Tự động chuyển đổi khối TikZ sang EMF/PNG nếu còn khối thô
    try:
        from services.tikz_vector_workflow import convert_exam_tikz_to_emf, count_pending_blocks
        if count_pending_blocks(exam_data) > 0:
            convert_exam_tikz_to_emf(exam_data)
    except Exception as _tz_err:
        import logging
        logging.getLogger(__name__).warning("Lỗi tự động chuyển TikZ trước khi xuất Word: %s", _tz_err)

    try:
        from docx import Document
        from docx.shared import Pt, Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
        from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError as exc:
        raise ImportError("Chưa cài python-docx\nChạy: pip install python-docx") from exc

    doc = Document()
    section = doc.sections[0]
    section.top_margin    = Cm(1.0)
    section.bottom_margin = Cm(1.0)
    section.left_margin   = Cm(1.5)
    section.right_margin  = Cm(1.5)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    try:
        style.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    except Exception:
        pass

    qs    = exam_data.questions
    npa_q = [q for q in qs if q.qtype == "TN"]
    ds_q  = [q for q in qs if q.qtype == "DS"]
    tn_q  = [q for q in qs if q.qtype == "TLN"]
    tl_q  = [q for q in qs if q.qtype == "TL"]

    def _font(run, bold=False, size=12, italic=False):
        run.font.name  = "Times New Roman"
        run.font.size  = Pt(size)
        run.bold       = bold
        run.italic     = italic
        try:
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        except Exception:
            pass

    def _add_text(paragraph, text: str, bold=False, size=12, italic=False):
        if math_mode == "equation" and "$" in text:
            from export.math_converter import split_text_and_math, insert_math_in_paragraph
            parts = split_text_and_math(text)
            for is_math, content in parts:
                if is_math:
                    if not insert_math_in_paragraph(paragraph, content):
                        r = paragraph.add_run(f"${content}$")
                        _font(r, bold=bold, size=size, italic=True)
                elif content:
                    r = paragraph.add_run(content)
                    _font(r, bold=bold, size=size, italic=italic)
        elif "$" in text:
            from export.math_converter import split_text_and_math
            parts = split_text_and_math(text)
            for is_math, content in parts:
                if is_math:
                    r = paragraph.add_run(f"${content}$")
                    _font(r, bold=bold, size=size, italic=True)
                elif content:
                    r = paragraph.add_run(content)
                    _font(r, bold=bold, size=size, italic=italic)
        else:
            r = paragraph.add_run(text)
            _font(r, bold=bold, size=size, italic=italic)

    def _section_heading(text: str) -> None:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after  = Pt(_SPACE_AFTER_SECTION)
        r = p.add_run(text)
        _font(r, bold=True)

    def _center_title(text: str, size: int = 12, space_before: int = 4) -> None:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(space_before)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(text)
        _font(r, bold=True, size=size)

    def _part_label(text: str) -> None:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(text)
        _font(r, bold=True)

    def _set_table_borders(table, val: str = "single", size: str = "4") -> None:
        tbl_pr = table._tbl.tblPr
        old = tbl_pr.find(qn("w:tblBorders"))
        if old is not None:
            tbl_pr.remove(old)
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            elem = OxmlElement(f"w:{edge}")
            elem.set(qn("w:val"), val)
            elem.set(qn("w:sz"), "0" if val == "none" else size)
            elem.set(qn("w:space"), "0")
            elem.set(qn("w:color"), "auto")
            borders.append(elem)
        tbl_pr.append(borders)

    def _clear_cell(cell) -> None:
        cell.text = ""
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    def _write_cell_lines(cell, lines: list[tuple[str, bool]], size: int = 12) -> None:
        _clear_cell(cell)
        for i, (text, bold) in enumerate(lines):
            p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            _add_text(p, text, bold=bold, size=size)

    def _write_cell_text(cell, text: str, bold: bool = False, center: bool = True, size: int = 12) -> None:
        _clear_cell(cell)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        _add_text(p, str(text), bold=bold, size=size)

    def _add_exam_header() -> None:
        table = doc.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        _set_table_borders(table, val="none")

        try:
            table.columns[0].width = Cm(7.25)
            table.columns[1].width = Cm(11.25)
            table.rows[0].cells[0].width = Cm(7.25)
            table.rows[0].cells[1].width = Cm(11.25)
        except Exception:
            pass

        total_questions = len(qs)
        school = (school_name or getattr(exam_data, "school", "") or "").strip()
        teacher = (teacher_name or getattr(exam_data, "teacher", "") or "").strip()
        left_lines: list[tuple[str, bool]] = [
            ("SỞ GIÁO DỤC VÀ ĐÀO TẠO", True),
            ((school if school else "TRƯỜNG THPT ........................."), True),
            (f"(Đề thi gồm {total_questions:02d} câu)", False),
        ]
        if teacher:
            left_lines.append((f"GV ra đề: {teacher}", False))

        title = (exam_data.exam_title or "ĐỀ KIỂM TRA CHÍNH THỨC").strip().upper()
        subj = (exam_data.subject or "TOÁN").upper()
        grd = f" - Khối {exam_data.grade}" if exam_data.grade else " - Khối 12"
        subject_line = f"Môn: {subj}{grd}"
        time_text = exam_data.time or "90 phút (không kể phát đề)"
        if not time_text.endswith("không kể phát đề") and not time_text.endswith("phát đề)"):
            time_text = f"{time_text} (không kể phát đề)"
        right_lines: list[tuple[str, bool]] = [
            (title, True),
            (subject_line, True),
            (f"Thời gian làm bài: {time_text}", False),
        ]

        _write_cell_lines(table.rows[0].cells[0], left_lines)
        _write_cell_lines(table.rows[0].cells[1], right_lines)

    def _add_candidate_line() -> None:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        for stop_cm in (0.5, 5.0, 9.5, 14.0):
            p.paragraph_format.tab_stops.add_tab_stop(Cm(stop_cm), WD_TAB_ALIGNMENT.LEFT)
        _add_text(p, "Họ và tên thí sinh: ....................................................   Số báo danh: ..............   ")
        ma_de = (getattr(exam_data, "ma_de", "") or "101").strip()
        r = p.add_run(f"Mã đề {ma_de}")
        _font(r, bold=True)
        _add_hrule(doc)

    def _is_table_line(line: str) -> bool:
        """Kiểm tra dòng có phải dòng bảng (chứa | ngăn cách cột).

        Loại trừ các dòng mà dấu | chỉ xuất hiện bên trong công thức
        toán học $...$ hoặc $$...$$ (ví dụ: $|x| < 5$, $\\left|a\\right|$).
        """
        stripped = line.strip()
        if not stripped or "|" not in stripped:
            return False
        # Bỏ qua dòng separator markdown (|---|---| hoặc |:---:|)
        if re.match(r"^[\s|:\-]+$", stripped):
            return False
        # Thay thế nội dung bên trong $...$ thành 'MATH' trước khi kiểm tra |
        # để tránh nhầm ký hiệu toán học (|x|, \left|, v.v.) với cột bảng,
        # đồng thời bảo toàn các ô chỉ chứa công thức toán.
        masked = re.sub(r"\$\$.*?\$\$|\$[^$\n]+?\$", "MATH", stripped, flags=re.DOTALL)
        if "|" not in masked:
            return False
        parts = [p.strip() for p in masked.split("|")]
        # Ít nhất 2 cột có nội dung
        non_empty = sum(1 for p in parts if p)
        return non_empty >= 2

    def _split_table_cells(line: str) -> list[str]:
        """Tách các ô trong dòng bảng bằng '|' mà không tách nhầm '|' bên trong công thức toán."""
        stripped = line.strip()
        math_spans = []
        for m in re.finditer(r"\$\$.*?\$\$|\$[^$\n]+?\$", stripped):
            math_spans.append((m.start(), m.end()))

        def in_any_span(pos: int) -> bool:
            return any(s <= pos < e for s, e in math_spans)

        cells = []
        current = []
        for pos, ch in enumerate(stripped):
            if ch == "|" and not in_any_span(pos):
                cells.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
        cells.append("".join(current).strip())
        if cells and not cells[0]:
            cells = cells[1:]
        if cells and not cells[-1]:
            cells = cells[:-1]
        return cells

    def _parse_latex_tabular(tex_block: str) -> list[list[str]]:
        """Chuyển đổi nội dung bên trong \\begin{tabular} thành list[list[str]]."""
        cleaned = re.sub(r"\\(?:hline|cline\{[^}]*\}|toprule|midrule|bottomrule)", "", tex_block)
        raw_rows = [r.strip() for r in cleaned.split(r"\\") if r.strip()]
        rows = []
        for r in raw_rows:
            math_spans = [(m.start(), m.end()) for m in re.finditer(r"\$\$.*?\$\$|\$[^$\n]+?\$", r)]
            cells = []
            cur = []
            for pos, ch in enumerate(r):
                if ch == "&" and not any(s <= pos < e for s, e in math_spans):
                    cells.append("".join(cur).strip())
                    cur = []
                else:
                    cur.append(ch)
            cells.append("".join(cur).strip())
            if any(c for c in cells):
                rows.append(cells)
        return rows

    def _split_text_and_tables(text: str):
        """Tách text thành các đoạn: ('text', str) hoặc ('table', list[list[str]])."""
        # Xóa citation [cite: ...]
        text = re.sub(r"\[cite[a-z]*:\s*[\d,\s]+\]", "", str(text or ""), flags=re.IGNORECASE)

        if not auto_convert_tables:
            plain = text.strip()
            return [("text", plain)] if plain else []

        # 1. Kiểm tra bảng LaTeX \\begin{tabular}
        if r"\begin{tabular}" in text:
            segments = []
            last_idx = 0
            tabular_re = re.compile(r"\\begin\{tabular\}(?:\[[^\]]*\])?\{[^}]*\}(.*?)\\end\{tabular\}", re.DOTALL)
            for m in tabular_re.finditer(text):
                before = text[last_idx:m.start()].strip()
                if before:
                    # Đệ quy tách markdown tables trong phần before
                    segments.extend(_split_markdown_tables(before))
                rows = _parse_latex_tabular(m.group(1))
                if rows:
                    segments.append(("table", rows))
                last_idx = m.end()
            after = text[last_idx:].strip()
            if after:
                segments.extend(_split_markdown_tables(after))
            return segments

        return _split_markdown_tables(text)

    def _split_markdown_tables(text: str):
        """Tách text chứa bảng Markdown '| ... |'."""
        lines = text.split("\n")
        segments = []
        current_text_lines = []
        current_table_rows = []

        def _flush_text():
            if current_text_lines:
                combined = "\n".join(current_text_lines).strip()
                if combined:
                    segments.append(("text", combined))
                current_text_lines.clear()

        def _flush_table():
            if current_table_rows:
                segments.append(("table", list(current_table_rows)))
                current_table_rows.clear()

        for line in lines:
            stripped = line.strip()
            # Bỏ qua dòng separator markdown
            if re.match(r"^[\s|:\-]+$", stripped) and "|" in stripped:
                continue
            if _is_table_line(line):
                _flush_text()
                cells = _split_table_cells(line)
                current_table_rows.append(cells)
            else:
                _flush_table()
                current_text_lines.append(line)

        _flush_text()
        _flush_table()
        return segments

    def _add_word_table(rows_data: list[list[str]]) -> None:
        """Thêm bảng Word từ dữ liệu dạng list[list[str]]."""
        if not rows_data:
            return
        n_cols = max(len(row) for row in rows_data)
        n_rows = len(rows_data)
        tbl = doc.add_table(rows=n_rows, cols=n_cols)
        tbl.style = "Normal Table"
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(tbl, val="single", size="4")

        for ri, row in enumerate(rows_data):
            for ci in range(n_cols):
                val = row[ci] if ci < len(row) else ""
                cell = tbl.rows[ri].cells[ci]
                _write_cell_text(cell, val.strip(), bold=(ri == 0 or ci == 0), size=11)

        # Thêm khoảng trống sau bảng
        sp = doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(2)

    def _write_question_head(idx: int, level: str, text: str, pts: Optional[float] = None) -> None:
        """In tiêu đề câu: "Câu N. <nội dung>." — Câu N. in đậm.

        Per spec người dùng: KHÔNG hiển thị tag mức độ "[NB]" hay điểm "(1đ)"
        trong heading — chỉ "Câu N. <content>". Mức độ vẫn lưu trong Question
        làm metadata để filter trong NHCH, nhưng không in ra Word.
        """
        # `level` và `pts` giữ trong signature để các call site cũ không vỡ,
        # nhưng KHÔNG render vào output — clean format theo spec.
        _ = (level, pts)

        import re
        q_text = re.sub(r'^(?:Câu|Bài|CÂU|BÀI)\s*\d+[\.:\)]\s*', '', str(text or '')).strip()

        # Tách text và bảng
        segments = _split_text_and_tables(q_text)

        # Nếu không có bảng → xuất bình thường
        if len(segments) == 1 and segments[0][0] == "text":
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent = Cm(0)
            pf.first_line_indent = Cm(0)
            pf.space_before = Pt(0)
            pf.space_after = Pt(_SPACE_AFTER_QUESTION)

            r1 = p.add_run(f"Câu {idx}. ")
            _font(r1, bold=True)
            _add_text(p, segments[0][1])
            return

        # Có bảng → xuất từng segment
        first_text = True
        for seg_type, seg_data in segments:
            if seg_type == "text":
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.left_indent = Cm(0)
                pf.first_line_indent = Cm(0)
                pf.space_before = Pt(0)
                pf.space_after = Pt(_SPACE_AFTER_QUESTION)

                if first_text:
                    r1 = p.add_run(f"Câu {idx}. ")
                    _font(r1, bold=True)
                    first_text = False
                _add_text(p, seg_data)
            else:
                # Nếu bảng xuất hiện đầu tiên, thêm header câu hỏi trước
                if first_text:
                    p = doc.add_paragraph()
                    r1 = p.add_run(f"Câu {idx}. ")
                    _font(r1, bold=True)
                    first_text = False
                _add_word_table(seg_data)

    def _ensure_dot(text: str) -> str:
        """Đảm bảo text kết thúc bằng dấu chấm."""
        t = text.strip()
        if t and not t.endswith((".", "?", "!", ":", ";")):
            t += "."
        return t

    def _write_options(q: Question) -> None:
        opts    = q.options
        max_len = max((len(v) for v in opts.values()), default=0)

        if max_len <= _WRAP_THRESHOLD:
            # 4 đáp án trên 1 dòng (ngang)
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.left_indent    = Cm(_OPT_INDENT)
            pf.space_after    = Pt(_SPACE_AFTER_OPTIONS)

            for stop_cm in _TAB_4COL:
                p.paragraph_format.tab_stops.add_tab_stop(Cm(stop_cm), WD_TAB_ALIGNMENT.LEFT)

            for i, k in enumerate("ABCD"):
                v = _ensure_dot(opts.get(k, ""))
                if i > 0:
                    p.add_run("\t")
                # Chỉ bold nhãn "A.", "B."..., nội dung không bold, toàn bộ màu đen
                r_lbl = p.add_run(f"{k}. ")
                _font(r_lbl, bold=True)
                _add_text(p, v, bold=False)

        elif max_len <= _WRAP_THRESHOLD * 2:
            # 2 đáp án mỗi dòng (2×2)
            for pair in [("A", "B"), ("C", "D")]:
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.left_indent = Cm(_OPT_INDENT)
                pf.space_after = Pt(2)
                p.paragraph_format.tab_stops.add_tab_stop(Cm(7.5), WD_TAB_ALIGNMENT.LEFT)

                for i, k in enumerate(pair):
                    v = _ensure_dot(opts.get(k, ""))
                    if i > 0:
                        p.add_run("\t")
                    r_lbl = p.add_run(f"{k}. ")
                    _font(r_lbl, bold=True)
                    _add_text(p, v, bold=False)
            doc.paragraphs[-1].paragraph_format.space_after = Pt(_SPACE_AFTER_OPTIONS)

        else:
            # Mỗi đáp án 1 dòng (đứng)
            for k in "ABCD":
                v = _ensure_dot(opts.get(k, ""))
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.left_indent       = Cm(_OPT_INDENT)
                pf.first_line_indent = Cm(0)
                pf.space_after       = Pt(2 if k != "D" else _SPACE_AFTER_OPTIONS)

                r_lbl = p.add_run(f"{k}. ")
                _font(r_lbl, bold=True)
                _add_text(p, v, bold=False)

    def _add_solution(text: str, indent_cm: float = _SOL_INDENT) -> None:
        """In phần lời giải: "Lời giải:" in đậm + nội dung (không ► icon).

        Theo spec mới: bỏ icon trang trí "►", bỏ màu nâu — clean như đề thi
        thật để copy/in ấn không nhiễu. "Lời giải:" in đậm, nội dung bình
        thường (đen).
        """
        sol_text = str(text)
        segments = _split_text_and_tables(sol_text)

        # Nếu không có bảng → xuất bình thường
        if all(s[0] == "text" for s in segments):
            sp = doc.add_paragraph()
            sp.paragraph_format.left_indent = Cm(indent_cm)
            sp.paragraph_format.space_after = Pt(2)
            r1 = sp.add_run("Lời giải: ")
            _font(r1, bold=True)
            plain = " ".join(s[1] for s in segments)
            _add_text(sp, plain)
            return

        # Có bảng → xuất từng segment
        first = True
        for seg_type, seg_data in segments:
            if seg_type == "text":
                sp = doc.add_paragraph()
                sp.paragraph_format.left_indent = Cm(indent_cm)
                sp.paragraph_format.space_after = Pt(2)
                if first:
                    r1 = sp.add_run("Lời giải: ")
                    _font(r1, bold=True)
                    first = False
                _add_text(sp, seg_data)
            else:
                if first:
                    sp = doc.add_paragraph()
                    sp.paragraph_format.left_indent = Cm(indent_cm)
                    r1 = sp.add_run("Lời giải: ")
                    _font(r1, bold=True)
                    first = False
                _add_word_table(seg_data)

    def _emf_size_cm(path: _Path, max_width_cm: float) -> tuple[float, float]:
        try:
            import struct
            header = path.read_bytes()[:40]
            _itype, _size, *_rects = struct.unpack("<II8i", header)
            frame_left, frame_top, frame_right, frame_bottom = _rects[4:8]
            width_cm = abs(frame_right - frame_left) / 1000.0
            height_cm = abs(frame_bottom - frame_top) / 1000.0
            if 0.2 <= width_cm <= 100 and 0.2 <= height_cm <= 100:
                scale = min(1.0, max_width_cm / width_cm)
                return width_cm * scale, height_cm * scale
        except Exception:
            pass
        return min(12.0, max_width_cm), min(7.0, max_width_cm * 0.62)

    def _add_emf_image(path: _Path, indent_cm: float = 0.0,
                       max_width_cm: float = 14.0) -> bool:
        try:
            from docx.oxml import parse_xml
            from docx.oxml.ns import nsdecls
            from docx.opc.constants import RELATIONSHIP_TYPE as _RT
            from docx.parts.image import ImagePart

            package = doc.part.package
            partname = package.next_partname("/word/media/image%d.emf")
            image_part = ImagePart(partname, "image/x-emf", path.read_bytes())
            rid = doc.part.relate_to(image_part, _RT.IMAGE)
            width_cm, height_cm = _emf_size_cm(path, max_width_cm)
            cx = int(width_cm * 360000)
            cy = int(height_cm * 360000)
            docpr_id = len(doc.part.rels) + 1000
            drawing = parse_xml(f"""
                <w:drawing {nsdecls('w', 'wp', 'a', 'pic', 'r')}>
                  <wp:inline distT="0" distB="0" distL="0" distR="0">
                    <wp:extent cx="{cx}" cy="{cy}"/>
                    <wp:docPr id="{docpr_id}" name="TikZ EMF"/>
                    <wp:cNvGraphicFramePr>
                      <a:graphicFrameLocks noChangeAspect="1"/>
                    </wp:cNvGraphicFramePr>
                    <a:graphic>
                      <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                        <pic:pic>
                          <pic:nvPicPr>
                            <pic:cNvPr id="0" name="{path.name}"/>
                            <pic:cNvPicPr/>
                          </pic:nvPicPr>
                          <pic:blipFill>
                            <a:blip r:embed="{rid}"/>
                            <a:stretch><a:fillRect/></a:stretch>
                          </pic:blipFill>
                          <pic:spPr>
                            <a:xfrm>
                              <a:off x="0" y="0"/>
                              <a:ext cx="{cx}" cy="{cy}"/>
                            </a:xfrm>
                            <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                          </pic:spPr>
                        </pic:pic>
                      </a:graphicData>
                    </a:graphic>
                  </wp:inline>
                </w:drawing>
            """)
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Cm(indent_cm)
            para.paragraph_format.space_before = Pt(2)
            para.paragraph_format.space_after = Pt(4)
            para.add_run()._r.append(drawing)
            return True
        except Exception:
            return False

    def _add_image(image_value, indent_cm: float = 0.0,
                    max_width_cm: float = 14.0) -> None:
        """Chèn ảnh vào document — hỗ trợ MULTI-IMAGE (chèn lần lượt).

        `image_value`: chấp nhận
            - str path đơn         "a.png"
            - str '|'-separated    "a.png|b.png|c.png"
            - list[str]            ["a.png", "b.png"]
            - "" / None            → bỏ qua
        """
        try:
            from services.image_fields import normalize_image_field
            paths = normalize_image_field(image_value, prefer_vector=True)
        except Exception:
            if isinstance(image_value, str) and "|" in image_value:
                paths = [x.strip() for x in image_value.split("|") if x.strip()]
            elif isinstance(image_value, (list, tuple)):
                paths = [str(x).strip() for x in image_value if str(x).strip()]
            else:
                paths = [image_value] if image_value else []

        for image_path in paths:
            if not image_path:
                continue
            p = _Path(image_path)
            if not p.exists():
                continue
            if p.suffix.lower() == ".emf":
                if _add_emf_image(p, indent_cm, max_width_cm):
                    inserted = True
                    continue
            try:
                from docx.shared import Cm as _Cm
                from PIL import Image
                img = Image.open(str(p))
                w_px, h_px = img.size
                dpi = img.info.get("dpi", (96, 96))
                w_inch = w_px / dpi[0]
                w_cm = w_inch * 2.54
                if w_cm > max_width_cm:
                    w_cm = max_width_cm
                para = doc.add_paragraph()
                para.paragraph_format.left_indent = Cm(indent_cm)
                para.paragraph_format.space_before = Pt(2)
                para.paragraph_format.space_after = Pt(4)
                run = para.add_run()
                run.add_picture(str(p), width=_Cm(w_cm))
                inserted = True
            except ImportError:
                # PIL không có → chèn ảnh với kích thước mặc định
                try:
                    para = doc.add_paragraph()
                    para.paragraph_format.left_indent = Cm(indent_cm)
                    run = para.add_run()
                    run.add_picture(str(p), width=Cm(min(14, max_width_cm)))
                    inserted = True
                except Exception:
                    pass
            except Exception:
                pass

    # Helper: in "Đáp án: <X>" với "Đáp án:" in đậm (clean, không icon).
    def _write_dapan(label_or_value: str, indent_cm: float = _SOL_INDENT) -> None:
        ap = doc.add_paragraph()
        ap.paragraph_format.left_indent = Cm(indent_cm)
        ap.paragraph_format.space_after = Pt(2)
        r1 = ap.add_run("Đáp án: ")
        _font(r1, bold=True)
        _add_text(ap, str(label_or_value))

    def _tn_answer(q: Question) -> str:
        ans = (q.answer or "").strip().upper()
        return ans[0] if ans and ans[0] in "ABCD" else ""

    def _ds_marks(q: Question) -> list[str]:
        marks: list[str] = []
        raw = (q.answer or "").upper().replace(" ", "")
        for i, k in enumerate("abcd"):
            val = q.answers.get(k) if q.answers else None
            if val is None and i < len(raw):
                ch = raw[i]
                if ch in ("Đ", "D"):
                    val = True
                elif ch == "S":
                    val = False
            marks.append("Đ" if val is True else ("S" if val is False else ""))
        return marks

    def _ds_compact(q: Question) -> str:
        return "".join(_ds_marks(q))

    def _has_solution(q: Question) -> bool:
        return bool(
            (q.solution or "").strip()
            or any((v or "").strip() for v in (q.item_solutions or {}).values())
            or _tn_answer(q)
            or (q.answer or "").strip()
            or _ds_compact(q)
        )

    def _add_answer_table(rows_data: list[list[str]]) -> None:
        if not rows_data:
            return
        n_cols = max(len(row) for row in rows_data)
        table = doc.add_table(rows=len(rows_data), cols=n_cols)
        table.style = "Normal Table"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        _set_table_borders(table, val="single", size="4")
        for ri, row in enumerate(rows_data):
            for ci in range(n_cols):
                text = row[ci] if ci < len(row) else ""
                _write_cell_text(
                    table.rows[ri].cells[ci],
                    text,
                    bold=(ri == 0 or ci == 0),
                    center=True,
                    size=11,
                )
        sp = doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(2)

    def _write_solution_text(text: str, indent_cm: float = 0.0) -> None:
        for seg_type, seg_data in _split_text_and_tables(str(text or "")):
            if seg_type == "table":
                _add_word_table(seg_data)
                continue
            for line in str(seg_data).splitlines():
                line = line.strip()
                if not line:
                    continue
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(indent_cm)
                p.paragraph_format.space_after = Pt(1)
                _add_text(p, line)

    def _write_solution_question_label(idx: int) -> None:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(f"Câu {idx}.")
        _font(r, bold=True)

    def _add_exam_end() -> None:
        _center_title("HẾT", size=12, space_before=6)

    def _add_answer_reference() -> None:
        _center_title("ĐÁP ÁN THAM KHẢO", size=12, space_before=4)
        if npa_q:
            _part_label("PHẦN I.")
            _add_answer_table([
                ["Câu"] + [str(i) for i in range(1, len(npa_q) + 1)],
                ["Đáp án"] + [_tn_answer(q) for q in npa_q],
            ])
        if ds_q:
            _part_label("PHẦN II.")
            rows = [["Câu", "a", "b", "c", "d"]]
            for i, q in enumerate(ds_q, 1):
                rows.append([f"Câu {i}"] + _ds_marks(q))
            _add_answer_table(rows)
        if tn_q:
            _part_label("PHẦN III.")
            _add_answer_table([
                ["Câu"] + [str(i) for i in range(1, len(tn_q) + 1)],
                ["Đáp số"] + [(q.answer or "").strip() for q in tn_q],
            ])

    def _add_solution_reference() -> None:
        if not any(_has_solution(q) for q in qs):
            return

        _center_title("LỜI GIẢI THAM KHẢO", size=12, space_before=6)

        if npa_q:
            _part_label("PHẦN I.")
            for i, q in enumerate(npa_q, 1):
                _write_solution_question_label(i)
                if q.solution:
                    _write_solution_text(q.solution)
                ans = _tn_answer(q)
                if ans:
                    p = doc.add_paragraph()
                    p.paragraph_format.space_after = Pt(2)
                    r = p.add_run(f"Chọn {ans}.")
                    _font(r, bold=True)
                _add_image(getattr(q, "solution_image", ""), indent_cm=0.0)

        if ds_q:
            from export.question_formatter import ensure_terminator

            _part_label("PHẦN II")
            for i, q in enumerate(ds_q, 1):
                _write_solution_question_label(i)
                if q.item_solutions:
                    for k in "abcd":
                        sol_text = (q.item_solutions.get(k, "") or "").strip()
                        if not sol_text:
                            continue
                        verdict = ""
                        if q.answers and k in q.answers:
                            verdict = "Đúng" if q.answers[k] else "Sai"
                        p = doc.add_paragraph()
                        p.paragraph_format.space_after = Pt(1)
                        r_lbl = p.add_run(f"{k}) ")
                        _font(r_lbl, bold=True)
                        if verdict:
                            r_verdict = p.add_run(f"{verdict}. ")
                            _font(r_verdict, bold=True)
                        _add_text(p, ensure_terminator(sol_text))
                elif q.solution:
                    _write_solution_text(q.solution)

                compact = _ds_compact(q)
                if compact:
                    p = doc.add_paragraph()
                    p.paragraph_format.space_after = Pt(2)
                    _add_text(p, f"Vậy Câu {i}: {compact}.", bold=True)

        if tn_q:
            _part_label("PHẦN III")
            for i, q in enumerate(tn_q, 1):
                _write_solution_question_label(i)
                if q.solution:
                    _write_solution_text(q.solution)
                ans = (q.answer or "").strip()
                if ans:
                    p = doc.add_paragraph()
                    p.paragraph_format.space_after = Pt(2)
                    r = p.add_run(f"Đáp số: {ans}.")
                    _font(r, bold=True)
                _add_image(getattr(q, "solution_image", ""), indent_cm=0.0)

        if tl_q:
            _part_label("PHẦN IV")
            for i, q in enumerate(tl_q, 1):
                _write_solution_question_label(i)
                if q.solution:
                    _write_solution_text(q.solution)
                    _add_image(getattr(q, "solution_image", ""), indent_cm=0.0)

    _add_exam_header()
    _add_candidate_line()

    # ── PHẦN I ─────────────────────────────────────────────────────────────
    if npa_q:
        _section_heading(
            f"PHẦN I. Thí sinh trả lời từ câu 1 đến câu {len(npa_q)}. "
            "Mỗi câu hỏi thí sinh chỉ chọn một phương án."
        )

        for i, q in enumerate(npa_q, 1):
            _write_question_head(i, q.level, q.question)
            _add_image(getattr(q, "question_image", ""))
            _write_options(q)
            # Ảnh từng đáp án
            opt_imgs = getattr(q, "option_images", {}) or {}
            for k in "ABCD":
                _add_image(opt_imgs.get(k, ""), indent_cm=_OPT_INDENT)

    # ── PHẦN II (Đúng/Sai) – cấu trúc mới ────────────────────────────────────
    if ds_q:
        from export.question_formatter import ensure_terminator

        _section_heading(
            f"PHẦN II. Thí sinh trả lời từ câu 1 đến câu {len(ds_q)}. "
            "Mỗi ý a), b), c), d) ở mỗi câu hỏi, thí sinh chọn đúng hoặc sai."
        )

        for i, q in enumerate(ds_q, 1):
            # In câu hỏi chính
            _write_question_head(i, q.level, q.question)
            _add_image(getattr(q, "question_image", ""))

            # In 4 ý a, b, c, d — "a) " in đậm, nội dung kết thúc bằng "."
            item_imgs = getattr(q, "item_images", {}) or {}
            for k in "abcd":
                v = ensure_terminator(q.items.get(k, ""))
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.left_indent   = Cm(_DS_ITEM_INDENT)
                pf.space_after   = Pt(2)

                r_lbl = p.add_run(f"{k}) ")
                _font(r_lbl, bold=True)
                _add_text(p, v)
                _add_image(item_imgs.get(k, ""), indent_cm=_DS_ITEM_INDENT)

            # Khoảng cách giữa các câu DS
            doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # ── PHẦN III (Trả lời ngắn) ────────────────────────────────────────────
    if tn_q:
        _section_heading(f"PHẦN III. Thí sinh trả lời từ câu 1 đến câu {len(tn_q)}.")

        for i, q in enumerate(tn_q, 1):
            _write_question_head(i, q.level, q.question, pts=q.points)
            _add_image(getattr(q, "question_image", ""))

    # ── PHẦN IV (Tự luận) ──────────────────────────────────────────────────
    if tl_q:
        _section_heading(f"PHẦN IV. Thí sinh trình bày lời giải từ câu 1 đến câu {len(tl_q)}.")

        for i, q in enumerate(tl_q, 1):
            _write_question_head(i, q.level, q.question, pts=q.points)
            _add_image(getattr(q, "question_image", ""))
            if not include_solution:
                for _ in range(4):
                    blank = doc.add_paragraph()
                    blank.paragraph_format.space_after = Pt(12)

    _add_exam_end()
    if include_solution:
        _add_answer_reference()
        _add_solution_reference()

    doc.save(str(Path(output_path)))


def _add_hrule(doc) -> None:
    try:
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
        from docx.shared import Pt

        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after  = Pt(6)

        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"),   "single")
        bottom.set(qn("w:sz"),    "6")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "1F497D")
        pBdr.append(bottom)
        pPr.append(pBdr)
    except Exception:
        pass


def export_multi_code(
    exam_data:        ExamData,
    output_dir:       str,
    n_codes:          int = 4,
    include_solution: bool = False,
    shuffle_questions: bool = True,
    shuffle_answers:   bool = True,
    variant_mode:     str = "none",            # "none" | "python" | "ai"
    ai_call=None,                               # callable(prompt)->str — chỉ dùng khi variant_mode="ai"
    progress_cb=None,                           # callable(stage, i, n) — báo tiến độ
    auto_convert_tables: bool = True,
) -> list[str]:
    """Xuất nhiều mã đề + (tùy chọn) đa dạng hoá số liệu.

    Parameters
    ----------
    variant_mode:
        "none"    — các mã dùng chung số liệu, chỉ trộn thứ tự.
        "python"  — mỗi mã thay số bằng Python/sympy cho các dạng hỗ trợ
                    (pt bậc 1, bậc 2). Câu không nhận dạng được giữ nguyên.
        "ai"      — mỗi mã nhờ AI thay số cho toàn bộ câu (chậm, tốn API).
    ai_call:
        callable(prompt:str) -> response:str. Bắt buộc khi variant_mode="ai".
    progress_cb:
        callback(stage:str, i_current:int, n_total:int). stage: "variant"/"export".
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Tự động chuyển đổi khối TikZ sang EMF/PNG nếu còn khối thô
    try:
        from services.tikz_vector_workflow import convert_exam_tikz_to_emf, count_pending_blocks
        if count_pending_blocks(exam_data) > 0:
            convert_exam_tikz_to_emf(exam_data)
    except Exception as _tz_err:
        import logging
        logging.getLogger(__name__).warning("Lỗi tự động chuyển TikZ trước khi xuất nhiều mã đề: %s", _tz_err)

    subj  = exam_data.subject
    grade = exam_data.grade
    base  = exam_data.exam_title
    files_created:  list[str] = []
    shuffled_list: list[tuple[str, ExamData]] = []

    # Lazy import để tránh phụ thuộc cứng khi user không bật variant
    _similar = None
    _ai_var = None
    if variant_mode == "python":
        try:
            from services import similar_generator as _similar  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Không thể import similar_generator: {e}")
    elif variant_mode == "ai":
        if ai_call is None:
            raise ValueError("variant_mode='ai' yêu cầu ai_call callable.")
        try:
            from services import ai_variant_generator as _ai_var  # type: ignore
        except Exception as e:
            raise RuntimeError(f"Không thể import ai_variant_generator: {e}")

    n_total = min(n_codes, len(MA_DE_LABELS))
    for idx in range(n_total):
        label = MA_DE_LABELS[idx]
        if progress_cb:
            try:
                progress_cb("variant", idx + 1, n_total)
            except Exception:
                pass

        # Bước 1: Đa dạng hoá số liệu (nếu bật)
        if variant_mode == "python" and _similar is not None:
            base_exam, _rep, _keep = _similar.make_variant_exam(
                exam_data, seed=idx * 137 + 11)
        elif variant_mode == "ai" and _ai_var is not None:
            base_exam, _rep, _keep = _ai_var.generate_ai_variant_exam(
                exam_data, ai_call=ai_call)
        else:
            base_exam = exam_data

        # Bước 2: Trộn thứ tự câu hỏi & đáp án
        variant = shuffle_exam(
            base_exam, seed=idx * 137 + 42,
            shuffle_questions=shuffle_questions,
            shuffle_answers=shuffle_answers,
        )
        variant.exam_title = f"{base} — Mã đề {label}"
        variant.ma_de      = label

        # Bước 3: Xuất Word
        if progress_cb:
            try:
                progress_cb("export", idx + 1, n_total)
            except Exception:
                pass
        path = str(out / f"De_{subj}{grade}_Ma{label}.docx")
        export_to_word(
            variant,
            path,
            include_solution=include_solution,
            auto_convert_tables=auto_convert_tables,
        )
        files_created.append(path)
        shuffled_list.append((label, variant))

    ans_key  = build_answer_key(shuffled_list)
    ans_path = out / f"Bang_dap_an_{subj}{grade}.txt"
    ans_path.write_text(ans_key, encoding="utf-8")
    files_created.append(str(ans_path))

    return files_created
