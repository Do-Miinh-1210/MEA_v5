"""
core/pdf_to_questions.py — Pipeline THÔNG MINH: PDF / DOCX / Ảnh → list[Question].

Triết lý:
    1. Phát hiện loại file + chất lượng:
        - PDF có text-layer  → extract trực tiếp (miễn phí, nhanh)
        - PDF scan ảnh        → render từng trang → AI Vision (đề thi chụp/scan)
        - DOCX               → python-docx + OMML→LaTeX (đã có exam_file_loader)
        - PNG/JPG/...        → AI Vision 1 lần
    2. Bám FORMAT CHUẨN BỘ GD&ĐT 2024-2026:
        - PHẦN I  — 12 câu TN (4 phương án A/B/C/D)
        - PHẦN II — 4 câu DS  (4 mệnh đề a/b/c/d, mỗi mệnh đề Đ/S)
        - PHẦN III— 6 câu TLN (đáp án là 1 SỐ)
    3. Trả về thẳng list[Question] + metadata (subject/grade/topic) sẵn sàng
       push lên NHCH bằng `services.license_manager.nhch_upload_batch`.

Sử dụng:
    >>> from core.pdf_to_questions import pdf_or_image_to_questions
    >>> from services.ai_service import build_ai_service
    >>> ai = build_ai_service(provider="gemini", api_key="...", model="gemini-2.5-pro")
    >>> res = pdf_or_image_to_questions(
    ...     "de_thi_an_giang.pdf",
    ...     ai_vision_call=ai.generate_with_image,
    ...     progress_cb=lambda i, n, msg: print(f"[{i}/{n}] {msg}"),
    ... )
    >>> len(res["questions"]), res["meta"]
    (22, {"subject": "Toán", "grade": "12", "topic": ""})

Đẩy lên NHCH:
    >>> from services.license_manager import nhch_upload_batch, get_machine_id
    >>> rows = [{
    ...     "question_id": f"PDF-{i:04d}",
    ...     "subject": res["meta"]["subject"],
    ...     "grade":   res["meta"]["grade"],
    ...     "topic":   q.topic or res["meta"]["topic"],
    ...     "level":   q.level,
    ...     "qtype":   q.qtype,
    ...     "question": q.question,
    ...     "options":  q.options,
    ...     "answer":   q.answer,
    ...     "solution": q.solution,
    ... } for i, q in enumerate(res["questions"], 1)]
    >>> nhch_upload_batch(rows, get_machine_id(), "Upload PDF")
"""
from __future__ import annotations

import logging
import re
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional

from core.models import Question

_log = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
PDF_EXTS   = {".pdf"}
DOC_EXTS   = {".docx", ".tex", ".txt", ".html", ".htm"}

_TEXT_LAYER_MIN_CHARS = 100   # < 100 chars → coi là scan, dùng AI Vision
_RENDER_DPI            = 200   # DPI cho render PDF page → PNG (cân bằng chất lượng/kích thước)


# ─────────────────────────────────────────────────────────────────────────────
#  PROMPT BỔ SUNG — format chuẩn Bộ GD&ĐT 2024-2026
# ─────────────────────────────────────────────────────────────────────────────

_BO_FORMAT_HINT = """\
════════════════════════════════════════════════════════════════════════
[!] FORMAT CHUẨN BỘ GD&ĐT 2024-2026 — ƯU TIÊN NHẬN DIỆN
════════════════════════════════════════════════════════════════════════
Đề thi THPT/Tốt nghiệp môn Toán theo Bộ gồm 3 PHẦN, mỗi phần có loại
câu RIÊNG. Nếu trong ảnh có "PHẦN I", "PHẦN II", "PHẦN III" (hoặc viết
thường) → câu nằm trong phần nào → LOAI tương ứng:

  ┌──────────────────────────────────────────────────────────────────┐
  │ PHẦN I  — TRẮC NGHIỆM (12 câu, mỗi câu 0.25đ)                    │
  │   "Câu 1." + 4 phương án "A." "B." "C." "D."                     │
  │   ➜ LOAI: TN                                                     │
  │                                                                  │
  │ PHẦN II — ĐÚNG/SAI (4 câu, mỗi câu tối đa 1.0đ)                  │
  │   "Câu 1." + câu dẫn + 4 mệnh đề "a)" "b)" "c)" "d)"             │
  │   Mỗi mệnh đề được đánh giá Đúng hoặc Sai                        │
  │   ➜ LOAI: DS                                                     │
  │                                                                  │
  │ PHẦN III— TRẢ LỜI NGẮN (6 câu, mỗi câu 0.5đ)                     │
  │   "Câu 1." + câu hỏi; đáp án là 1 SỐ (vd: 14, 0,5, -3)           │
  │   KHÔNG có A/B/C/D, KHÔNG có a/b/c/d                             │
  │   ➜ LOAI: TLN                                                    │
  └──────────────────────────────────────────────────────────────────┘

GỢI Ý MỨC ĐỘ THEO VỊ TRÍ CÂU (chỉ tham khảo, ưu tiên độ phức tạp thực tế):
  • Phần I  câu 1-4   → NB
  • Phần I  câu 5-9   → TH
  • Phần I  câu 10-12 → VD
  • Phần II / III     → TH hoặc VD (xét theo câu hỏi)

LƯU Ý ĐẶC BIỆT CHO PHẦN II (DS):
  • Câu dẫn (intro) → đặt vào NOIDUNG
  • 4 mệnh đề → 4 dòng "a:", "b:", "c:", "d:" sau NOIDUNG
  • Nếu ảnh có sẵn đáp án (a: Đ, b: S, ...) → ghi vào DAPAN dạng "a=Đ,b=S,c=Đ,d=S"

LƯU Ý ĐẶC BIỆT CHO PHẦN III (TLN):
  • Đáp án là 1 SỐ tối đa 4 ký tự, dùng dấu phẩy thập phân VN (vd: "0,5")
  • Nếu ảnh KHÔNG có đáp án → để DAPAN trống (app sẽ tự giải sau)

"""


# ═════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═════════════════════════════════════════════════════════════════════════════

def pdf_or_image_to_questions(
    filepath: str,
    ai_vision_call: Callable[[str, str], str],
    *,
    ai_text_call: Optional[Callable[[str], str]] = None,
    auto_solve: bool = False,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
    qtype_filter: str = "auto",
    use_text_layer: bool = True,
    max_pages: int = 50,
) -> dict[str, Any]:
    """Pipeline đầy đủ: file → list[Question] + metadata.

    Parameters
    ----------
    filepath : str
        Đường dẫn .pdf / .docx / ảnh
    ai_vision_call : (prompt, image_path) -> str
        Hàm gọi AI Vision (vd: `ai_service.generate_with_image`)
    ai_text_call : (prompt) -> str  (tuỳ chọn)
        Hàm gọi AI text-only. Bắt buộc khi `auto_solve=True`.
    auto_solve : bool
        True → sau khi OCR, tự gọi AI text để FILL các câu có DAPAN/LOIGIAI rỗng.
        Cực hữu ích cho đề thi không in sẵn đáp án trong PDF.
    progress_cb : (current, total, label) -> None | None
        Callback cập nhật tiến độ cho UI
    qtype_filter : "auto" | "TN" | "DS" | "TLN" | "TL"
        Ép loại nếu biết trước (vd: chỉ ảnh chụp phần TN)
    use_text_layer : bool
        True (mặc định) → thử extract text-layer trước (miễn phí). False →
        bắt buộc dùng AI Vision (tốn API quota nhưng đảm bảo OCR).
    max_pages : int
        Giới hạn số trang xử lý (mặc định 50, tránh hao quota)

    Returns
    -------
    dict {
        "questions":  list[Question]      # parse xong, sẵn sàng push NHCH
        "meta":       dict{subject, grade, topic}
        "raw_text":   str                 # concat ===CAU=== từ tất cả trang
        "n_pages":    int                 # số trang đã xử lý
        "method":     "text-layer" | "ai-vision" | "image" | "docx"
        "warnings":   list[str]
    }
    """
    path = Path(filepath)
    ext = path.suffix.lower()

    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {filepath}")

    # ── Ảnh đơn ───────────────────────────────────────────────────────────
    if ext in IMAGE_EXTS:
        result = _image_to_questions(str(path), ai_vision_call,
                                      progress_cb, qtype_filter)
        if auto_solve and ai_text_call:
            _autofill_answers(result, ai_text_call, progress_cb)
        return result

    # ── PDF ──────────────────────────────────────────────────────────────
    if ext in PDF_EXTS:
        if use_text_layer:
            text = _try_pdf_text_layer(str(path))
            if text and len(text.strip()) >= _TEXT_LAYER_MIN_CHARS:
                _log.info("PDF có text-layer (%d chars) → text-based parse",
                          len(text))
                result = _text_to_result(text, "text-layer")
                if auto_solve and ai_text_call:
                    _autofill_answers(result, ai_text_call, progress_cb)
                return result
            _log.info("PDF không có text-layer (≤%d chars) → AI Vision per page",
                       _TEXT_LAYER_MIN_CHARS)
        result = _pdf_scan_to_questions(str(path), ai_vision_call,
                                         progress_cb, qtype_filter, max_pages)
        if auto_solve and ai_text_call:
            _autofill_answers(result, ai_text_call, progress_cb)
        return result

    # ── DOCX ─────────────────────────────────────────────────────────────
    if ext in DOC_EXTS:
        result = _document_to_questions(str(path))
        if auto_solve and ai_text_call:
            _autofill_answers(result, ai_text_call, progress_cb)
        return result

    raise ValueError(
        f"Định dạng không hỗ trợ: {ext}. Chấp nhận: .pdf, "
        f"{', '.join(sorted(DOC_EXTS))}, "
        f"{', '.join(sorted(IMAGE_EXTS))}"
    )


# ═════════════════════════════════════════════════════════════════════════════
#  Branch handlers
# ═════════════════════════════════════════════════════════════════════════════

def _try_pdf_text_layer(filepath: str) -> str:
    """Extract text-layer (nếu PDF có). Trả "" nếu là scan."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        _log.warning("PyMuPDF chưa cài — bỏ qua text-layer detection")
        return ""

    try:
        doc = fitz.open(filepath)
        parts = []
        for page in doc:
            t = page.get_text("text")
            if t:
                parts.append(t)
        doc.close()
        return "\n".join(parts)
    except Exception as e:
        _log.debug("text-layer extraction fail: %s", e)
        return ""


def _pdf_scan_to_questions(
    filepath: str,
    ai_vision_call: Callable[[str, str], str],
    progress_cb: Optional[Callable],
    qtype_filter: str,
    max_pages: int,
) -> dict[str, Any]:
    """PDF scan → render từng trang ra PNG → AI Vision → concat."""
    try:
        import fitz
    except ImportError:
        raise ImportError(
            "Cần cài PyMuPDF để xử lý PDF scan: pip install PyMuPDF"
        )

    doc = fitz.open(filepath)
    total = min(len(doc), max_pages)
    if len(doc) > max_pages:
        _log.warning("PDF có %d trang, chỉ xử lý %d trang đầu (max_pages)",
                      len(doc), max_pages)

    all_blocks: list[str] = []
    meta = {"subject": "Toán", "grade": "12", "topic": ""}
    warnings: list[str] = []

    prompt = _build_enhanced_vision_prompt(qtype_filter)
    tmpdir = tempfile.mkdtemp(prefix="mea_pdf_vision_")
    _log.info("Render PDF → %s (DPI=%d)", tmpdir, _RENDER_DPI)

    try:
        for i in range(total):
            page = doc[i]
            if progress_cb:
                progress_cb(i + 1, total,
                             f"Trang {i+1}/{total} — gọi AI Vision…")

            pix = page.get_pixmap(dpi=_RENDER_DPI)
            png_path = str(Path(tmpdir) / f"page_{i+1:03d}.png")
            pix.save(png_path)

            try:
                raw = ai_vision_call(prompt, png_path)
            except Exception as e:
                _log.warning("AI Vision fail trang %d: %s", i + 1, e)
                warnings.append(f"Trang {i+1}: AI Vision lỗi — {e}")
                continue

            # Extract META từ trang đầu (nếu AI trả về)
            if i == 0:
                m = _META_RE.search(raw)
                if m:
                    meta = {
                        "subject": m.group(1) or "Toán",
                        "grade":   m.group(2) or "12",
                        "topic":   m.group(3) or "",
                    }
                    _log.info("Detected META: %s", meta)

            # Extract các khối ===CAU===
            blocks = _CAU_BLOCK_RE.findall(raw)
            all_blocks.extend(blocks)
            _log.info("Trang %d: %d câu", i + 1, len(blocks))
    finally:
        doc.close()

    if progress_cb:
        progress_cb(total, total, f"Parse {len(all_blocks)} câu…")

    raw_text = "\n\n".join(all_blocks)
    questions = _parse_cau_blocks(raw_text)

    return {
        "questions": questions,
        "meta":      meta,
        "raw_text":  raw_text,
        "n_pages":   total,
        "method":    "ai-vision",
        "warnings":  warnings,
    }


def _image_to_questions(
    filepath: str,
    ai_vision_call: Callable[[str, str], str],
    progress_cb: Optional[Callable],
    qtype_filter: str,
) -> dict[str, Any]:
    """Ảnh đơn → AI Vision → parse."""
    if progress_cb:
        progress_cb(1, 1, "Gọi AI Vision…")

    prompt = _build_enhanced_vision_prompt(qtype_filter)
    try:
        raw = ai_vision_call(prompt, filepath)
    except Exception as e:
        return {
            "questions": [],
            "meta":      {"subject": "Toán", "grade": "12", "topic": ""},
            "raw_text":  "",
            "n_pages":   1,
            "method":    "image",
            "warnings":  [f"AI Vision lỗi: {e}"],
        }

    meta = {"subject": "Toán", "grade": "12", "topic": ""}
    m = _META_RE.search(raw)
    if m:
        meta = {"subject": m.group(1) or "Toán",
                "grade":   m.group(2) or "12",
                "topic":   m.group(3) or ""}

    blocks = _CAU_BLOCK_RE.findall(raw)
    raw_text = "\n\n".join(blocks)
    questions = _parse_cau_blocks(raw_text)

    return {
        "questions": questions,
        "meta":      meta,
        "raw_text":  raw_text,
        "n_pages":   1,
        "method":    "image",
        "warnings":  [],
    }


def _document_to_questions(filepath: str) -> dict[str, Any]:
    """DOCX/TEX/TXT/HTML → parser dùng chung của ``exam_file_loader``."""
    from core.exam_file_loader import load_exam_from_file
    result = load_exam_from_file(filepath)
    return {
        "questions": result.get("questions", []),
        "meta":      _detect_meta_from_text(result.get("text", "")),
        "raw_text":  result.get("text", ""),
        "n_pages":   1,
        "method":    "document",
        "warnings":  [result.get("error", "")] if result.get("error") else [],
    }


def _text_to_result(text: str, method: str) -> dict[str, Any]:
    """Wrapper cho text-layer PDF."""
    questions = _parse_text_natural(text)
    return {
        "questions": questions,
        "meta":      _detect_meta_from_text(text),
        "raw_text":  text,
        "n_pages":   -1,
        "method":    method,
        "warnings":  [],
    }


# ═════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═════════════════════════════════════════════════════════════════════════════

_META_RE = re.compile(
    r'META:\s*\{[^}]*"subject"\s*:\s*"([^"]*)"[^}]*'
    r'"grade"\s*:\s*"([^"]*)"[^}]*"topic"\s*:\s*"([^"]*)"',
    re.IGNORECASE,
)

_CAU_BLOCK_RE = re.compile(
    r"===\s*CAU\s*===.*?===\s*KETCAU\s*===",
    re.DOTALL | re.IGNORECASE,
)


def _parse_cau_blocks(raw_text: str) -> list[Question]:
    """Parse các khối ===CAU===...===KETCAU=== thành list[Question]."""
    try:
        from core.parser import parse_one_question
    except ImportError:
        _log.error("Không import được core.parser.parse_one_question")
        return []

    out: list[Question] = []
    for m in _CAU_BLOCK_RE.finditer(raw_text):
        try:
            q = parse_one_question(m.group(0))
            if q:
                out.append(q)
        except Exception as e:
            _log.debug("parse block fail: %s", e)
    return out


def _parse_text_natural(text: str) -> list[Question]:
    """Parse text tự nhiên thành list[Question] (cho PDF text-layer/DOCX)."""
    try:
        from core.exam_file_loader import parse_questions_from_text

        questions, _tier = parse_questions_from_text(text)
        return questions
    except Exception as e:
        _log.warning("natural_parser fail: %s", e)
        return []


def _detect_meta_from_text(text: str) -> dict[str, str]:
    """Đoán môn/lớp/chủ đề từ text (cho text-layer path)."""
    meta = {"subject": "Toán", "grade": "12", "topic": ""}
    if not text:
        return meta

    # Subject — tìm từ khoá phổ biến
    if re.search(r'\bMôn\s*[:.]?\s*Toán', text, re.IGNORECASE):
        meta["subject"] = "Toán"
    elif re.search(r'\bMôn\s*[:.]?\s*(Vật\s*lý|Lý)\b', text, re.IGNORECASE):
        meta["subject"] = "Lý"
    elif re.search(r'\bMôn\s*[:.]?\s*Hóa', text, re.IGNORECASE):
        meta["subject"] = "Hóa"
    elif re.search(r'\bMôn\s*[:.]?\s*Sinh', text, re.IGNORECASE):
        meta["subject"] = "Sinh"

    # Grade
    for g in ("12", "11", "10"):
        if re.search(rf'\b(?:lớp\s*|TOÁN\s*){g}\b', text, re.IGNORECASE):
            meta["grade"] = g
            break

    return meta


def _build_enhanced_vision_prompt(qtype_filter: str) -> str:
    """Build a Vision prompt without depending on any UI implementation."""
    filter_hint = ""
    if qtype_filter and qtype_filter != "auto":
        filter_hint = (
            "\nYÊU CẦU LỌC: gán LOAI cho toàn bộ câu nhận diện là "
            f"{qtype_filter}.\n"
        )
    return _BO_FORMAT_HINT + "\n" + _MINIMAL_FALLBACK_PROMPT + filter_hint


_MINIMAL_FALLBACK_PROMPT = """\
Chuyển ảnh đề thi thành các khối ===CAU===...===KETCAU===.
Mỗi câu cần LOAI, MUCDO, CHUONG, NOIDUNG, (A/B/C/D nếu TN), DAPAN, LOIGIAI.
Công thức Toán bọc trong ${...}$. Bắt đầu ngay với "===CAU===".
"""


# ═════════════════════════════════════════════════════════════════════════════
#  AUTO-FILL: gọi AI text để giải các câu có DAPAN/LOIGIAI rỗng
# ═════════════════════════════════════════════════════════════════════════════

_SOLVE_PROMPT_TEMPLATE = """\
Bạn là chuyên gia Toán THPT 10+ năm kinh nghiệm. Giải câu hỏi sau cho ra
ĐÁP ÁN + LỜI GIẢI ngắn gọn, đúng pháp lý toán.

QUY ƯỚC:
- Công thức bọc trong ${{...}}$ (KHÔNG dùng $$ hay \\( \\)).
- DAPAN theo LOAI:
    TN  → 1 ký tự A | B | C | D.
    DS  → "a=Đ,b=S,c=Đ,d=S" (Đ/S cho 4 mệnh đề).
    TLN → 1 SỐ tối đa 4 ký tự, dùng dấu PHẨY thập phân VN (vd: 0,5).
    TL  → "xem lời giải".
- LOIGIAI: viết liền mạch 2-5 câu, đến kết quả cuối.

CÂU HỎI:
LOAI: {qtype}
NOIDUNG: {question}
{options_block}

OUTPUT — CHỈ trả 2 dòng:
DAPAN: <…>
LOIGIAI: <…>
"""


def _format_question_for_solve(q: Question) -> str:
    """Build options block để feed vào solver prompt."""
    if q.qtype == "TN":
        opts = q.options or {}
        return "\n".join(f"{k}: {v}" for k, v in opts.items())
    if q.qtype == "DS":
        items = q.items or {}
        return "\n".join(f"{k}: {v}" for k, v in items.items())
    return ""


def _parse_solve_output(raw: str) -> tuple[str, str]:
    """Parse output AI text → (dapan, loigiai)."""
    dapan = ""
    loigiai = ""
    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("DAPAN:"):
            dapan = line.split(":", 1)[1].strip()
        elif line.upper().startswith("LOIGIAI:"):
            loigiai = line.split(":", 1)[1].strip()
        elif loigiai:
            # Lời giải dài nhiều dòng → nối tiếp
            loigiai += "\n" + line
    return dapan, loigiai


def _apply_answer_to_question(q: Question, dapan: str, loigiai: str) -> None:
    """Gán đáp án parsed vào Question theo qtype."""
    if not loigiai and not dapan:
        return
    if loigiai:
        q.solution = loigiai
    if not dapan:
        return
    if q.qtype == "TN":
        # Lấy ký tự A/B/C/D đầu tiên
        m = re.search(r"[ABCD]", dapan.upper())
        if m:
            q.answer = m.group(0)
    elif q.qtype == "DS":
        # Parse "a=Đ,b=S,c=Đ,d=S"
        ans = dict(q.answers or {})
        for k in "abcd":
            m = re.search(rf"{k}\s*=\s*([ĐĐ́DSsTtFfTrueFalseĐúngSai]+)", dapan)
            if m:
                v = m.group(1).strip()
                ans[k] = v.upper().startswith(("Đ", "T")) or v.lower().startswith(("true", "đúng"))
        q.answers = ans
    elif q.qtype in ("TLN", "TL"):
        q.answer = dapan


def _autofill_answers(
    result: dict[str, Any],
    ai_text_call: Callable[[str], str],
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
) -> None:
    """Tìm các câu có DAPAN/LOIGIAI rỗng → gọi AI text giải → fill vào.

    Modify `result["questions"]` in-place. Câu nào AI lỗi sẽ giữ nguyên rỗng.
    """
    questions = result.get("questions", [])
    if not questions:
        return

    # Tìm câu cần solve
    todo = []
    for i, q in enumerate(questions):
        needs_answer = False
        if q.qtype == "TN":
            needs_answer = not (q.answer and q.answer.strip())
        elif q.qtype == "DS":
            # Cần solve nếu CHƯA có answers hoặc tất cả đều False (chưa set)
            needs_answer = not q.answers or all(not v for v in q.answers.values())
        elif q.qtype in ("TLN", "TL"):
            needs_answer = not (q.answer and q.answer.strip())
        needs_solution = not (q.solution and q.solution.strip())
        if needs_answer or needs_solution:
            todo.append((i, q))

    if not todo:
        _log.info("Auto-solve: tất cả câu đã có đáp án + lời giải, bỏ qua.")
        return

    _log.info("Auto-solve: %d/%d câu cần giải", len(todo), len(questions))
    warnings = result.setdefault("warnings", [])
    n = len(todo)

    for k, (idx, q) in enumerate(todo, 1):
        if progress_cb:
            progress_cb(k, n, f"AI giải câu {idx+1}/{len(questions)}…")
        prompt = _SOLVE_PROMPT_TEMPLATE.format(
            qtype=q.qtype,
            question=q.question or "(rỗng)",
            options_block=_format_question_for_solve(q),
        )
        try:
            raw = ai_text_call(prompt)
            dapan, loigiai = _parse_solve_output(raw)
            _apply_answer_to_question(q, dapan, loigiai)
        except Exception as e:
            warnings.append(f"Câu {idx+1}: AI giải lỗi — {e}")
            _log.warning("auto-solve câu %d fail: %s", idx + 1, e)


# ═════════════════════════════════════════════════════════════════════════════
#  Convenience: convert questions → rows sẵn sàng push NHCH
# ═════════════════════════════════════════════════════════════════════════════

def questions_to_nhch_rows(
    questions: list[Question],
    meta: dict[str, str],
    *,
    id_prefix: str = "PDF",
    source_file: str = "",
) -> list[dict]:
    """Chuyển list[Question] → list[dict] khớp với `nhch_upload_batch`.

    Tự sinh question_id duy nhất theo prefix + timestamp + index.
    """
    import hashlib
    import time

    seed = hashlib.md5(f"{source_file}{time.time()}".encode()).hexdigest()[:6].upper()
    rows = []
    for i, q in enumerate(questions, 1):
        # Build options dict
        if q.qtype == "TN":
            opts = q.options or {}
        elif q.qtype == "DS":
            opts = {k: v for k, v in (q.items or {}).items()}
        else:
            opts = {}

        # Build answer string
        if q.qtype == "DS":
            answer = ",".join(
                f"{k}={'Đ' if v else 'S'}"
                for k, v in (q.answers or {}).items()
            )
        else:
            answer = q.answer or ""

        rows.append({
            "question_id": f"{id_prefix}-{seed}-{i:03d}",
            "subject":  meta.get("subject", "Toán"),
            "grade":    meta.get("grade", "12"),
            "topic":    q.topic or meta.get("topic", ""),
            "level":    q.level or "TH",
            "qtype":    q.qtype,
            "question": q.question or "",
            "options":  opts,
            "answer":   answer,
            "solution": q.solution or "",
        })
    return rows
