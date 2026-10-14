"""
core/exam_file_loader.py — Đọc đề kiểm tra từ nhiều định dạng file và chuyển
về `list[Question]` theo quy trình 3-tầng:

  Tầng 1 — STRUCTURED      :  khung `===CAU===...===KETCAU===` (chuẩn MEA)
                               và LaTeX `ex_test` (`ex` / `bt` / `vd`).
  Tầng 2 — NATURAL parser  :  `core.natural_parser` tự nhận diện "Câu 1:",
                               "A. …", "Đáp án: …" → chuyển về chuẩn.
  Tầng 3 — AI fallback     :  nếu cả 2 tầng trên không ra câu nào → UI hỏi
                               user có muốn dùng API không. (Hàm này chỉ
                               trả về raw text ở `tier="none"`; UI chịu
                               trách nhiệm gọi AI.)

Hỗ trợ định dạng:

    .docx   → python-docx (+ lxml để trích OMML thành LaTeX-like)
    .pdf    → PyMuPDF (fitz) — ưu tiên; pdfplumber fallback
    .tex    → đọc text rồi nhận diện đồng thời cấu trúc app + LaTeX `ex_test`.
    .txt    → đọc trực tiếp
    .html   → BeautifulSoup.get_text() (có fallback regex thô)

Public API:

    >>> from core.exam_file_loader import load_exam_from_file
    >>> res = load_exam_from_file("Đề thi.docx")
    >>> res["tier"], len(res["questions"])
    ('natural', 25)

LoadResult dict:
    {
        "path":        str       – đường dẫn file gốc
        "ext":         str       – ".docx" / ".pdf" / ".tex" / ".txt" / ".html"
        "text":        str       – raw text trích ra (luôn có, kể cả tier=exact)
        "questions":   list[Question]
        "tier":        "exact" | "natural" | "latex" | "mixed" | "none"
        "error":       str       – thông báo lỗi nếu parse hoàn toàn thất bại
    }

Lưu ý thiết kế:
  • Không bao giờ raise khi phát hiện file lạ — chuyển về tier="none" với
    error message để UI hiển thị thân thiện.
  • Tier "mixed" = nội dung có cả khung app và LaTeX `ex_test`; các câu được
    giữ đúng thứ tự xuất hiện trong nguồn.
  • Khi tier="none" mà text trống → UI có thể cảnh báo file không đọc được;
    text có nội dung → UI offer AI fallback.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any, Literal

from core.models import Question

# TypedDict chỉ để annotate — runtime không phụ thuộc (có từ Python 3.8+).
if sys.version_info >= (3, 8):
    from typing import TypedDict

    class LoadResult(TypedDict):
        path:      str
        ext:       str
        text:      str
        questions: list[Question]
        tier:      str  # "exact" | "natural" | "latex" | "mixed" | "none"
        error:     str
else:                                       # pragma: no cover
    LoadResult = dict                        # type: ignore[misc,assignment]

Tier = Literal["exact", "natural", "latex", "mixed", "none"]

_log = logging.getLogger(__name__)


# Các extension được hỗ trợ
SUPPORTED_EXTS = (".docx", ".pdf", ".tex", ".txt", ".html", ".htm")


# ══════════════════════════════════════════════════════════════════════════════
#  PARSE CACHE — key = (abspath, mtime_ns, size)
# ══════════════════════════════════════════════════════════════════════════════
#
# Khi user re-upload / open lại file đã parse, tránh chạy lại toàn bộ pipeline
# đắt đỏ (OCR/PDF → text → 3-tầng parser → sanitize).
# Cache invalidation:
#   • mtime_ns khác → file đã bị sửa → miss
#   • size khác    → defensive (đổi content mà mtime clock skew) → miss
# Kích thước cache nhỏ (MAX=8) — UI hiếm khi mở > 8 file cùng phiên.

_CACHE_MAX = 8
_parse_cache: dict[tuple[str, int, int], "LoadResult"] = {}
_parse_cache_order: list[tuple[str, int, int]] = []  # LRU order


def _cache_get(key: tuple[str, int, int]) -> "LoadResult | None":
    hit = _parse_cache.get(key)
    if hit is not None:
        # Đưa lên đầu (most-recently-used)
        try:
            _parse_cache_order.remove(key)
        except ValueError:
            pass
        _parse_cache_order.append(key)
    return hit


def _cache_put(key: tuple[str, int, int], val: "LoadResult") -> None:
    _parse_cache[key] = val
    _parse_cache_order.append(key)
    # Evict LRU nếu vượt giới hạn
    while len(_parse_cache_order) > _CACHE_MAX:
        oldest = _parse_cache_order.pop(0)
        _parse_cache.pop(oldest, None)


def clear_parse_cache() -> None:
    """Xoá cache — dùng khi test hoặc user ép refresh."""
    _parse_cache.clear()
    _parse_cache_order.clear()


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def load_exam_from_file(path: str, *, use_cache: bool = True) -> LoadResult:
    """Điểm vào chính. Xem module docstring để biết format trả về.

    Parameters
    ----------
    use_cache : bool
        True (default) → reuse kết quả parse cũ nếu file chưa thay đổi
        (mtime_ns + size match). Set False để ép parse lại.
    """
    p = Path(path)
    ext = p.suffix.lower()

    result: dict[str, Any] = {
        "path":      str(p),
        "ext":       ext,
        "text":      "",
        "questions": [],
        "tier":      "none",
        "error":     "",
    }

    if not p.exists():
        result["error"] = f"Không tìm thấy file: {path}"
        return result

    # ── Cache lookup (sau khi file chắc chắn tồn tại) ────────────────────────
    cache_key: tuple[str, int, int] | None = None
    if use_cache and ext in SUPPORTED_EXTS:
        try:
            st = p.stat()
            # resolve() để path chuẩn hoá — same file, different relative → cùng key
            cache_key = (str(p.resolve()), st.st_mtime_ns, st.st_size)
            cached = _cache_get(cache_key)
            if cached is not None:
                _log.debug("parse cache HIT: %s", p.name)
                return cached
        except OSError as e:
            _log.debug("parse cache stat fail: %s", e)
            cache_key = None

    if ext not in SUPPORTED_EXTS:
        result["error"] = (
            f"Định dạng {ext or '(không có)'} không hỗ trợ. "
            f"Chấp nhận: {', '.join(SUPPORTED_EXTS)}"
        )
        return result

    # ── Trích text từ file (mọi định dạng) ──────────────────────────────────
    try:
        text = extract_text_from_file(str(p))
    except Exception as e:
        result["error"] = f"Không đọc được file: {e}"
        return result

    result["text"] = text or ""

    if not text or not text.strip():
        result["error"] = result["error"] or "File rỗng hoặc không có text."
        return result

    # ── Chạy 3-tầng parser ──────────────────────────────────────────────────
    qs, tier = parse_questions_from_text(text)
    result["questions"] = qs
    result["tier"] = tier
    # Chỉ cache khi parser ra kết quả — tránh giữ "none" tier trong cache
    # (user có thể muốn thử AI fallback, hoặc fix format rồi retry).
    if cache_key is not None and qs:
        _cache_put(cache_key, result)  # type: ignore[arg-type]
    return result


def extract_text_from_file(path: str) -> str:
    """Đọc text thô từ file (không parse câu hỏi)."""
    p = Path(path)
    ext = p.suffix.lower()

    if ext == ".docx":
        return _read_text_docx(p)
    if ext == ".pdf":
        return _read_text_pdf(p)
    if ext == ".tex":
        return _read_text_raw(p)
    if ext == ".txt":
        return _read_text_raw(p)
    if ext in (".html", ".htm"):
        return _read_text_html(p)

    raise ValueError(f"Định dạng không hỗ trợ: {ext}")


def parse_questions_from_text(text: str) -> tuple[list[Question], Tier]:
    """Chạy các tầng parse text → Question objects.

    Returns
    -------
    (questions, tier) — tier ∈ {"exact", "latex", "mixed", "natural", "none"}

    Mỗi tier đều đi qua `sanitize_question_objects` để clip text quá dài
    & flag cấu trúc bất thường trước khi trả ra UI.
    """
    if not text or not text.strip():
        return [], "none"

    # Loại bỏ các thẻ citation [cite: ...] do AI sinh ra
    text = re.sub(r"\[cite[a-z]*:\s*[\d,\s]+\]", "", text, flags=re.IGNORECASE)

    from core.question_parser_common import sanitize_question_objects

    # ── Tầng 1: cấu trúc app và/hoặc LaTeX ex_test ──────────────────────────
    structured_qs, structured_tier = parse_structured_questions(text)
    if structured_qs:
        sanitized, _w = sanitize_question_objects(structured_qs, logger=_log)
        return sanitized, structured_tier

    # ── Tầng 2: parser tự nhiên ─────────────────────────────────────────────
    try:
        from core.natural_parser import parse_natural_questions
        nat_qs = parse_natural_questions(text)
        if nat_qs:
            # parse_natural_questions() đã sanitize nội bộ; double sanitize
            # là no-op idempotent nên không cần unwrap.
            return nat_qs, "natural"
    except Exception as e:
        # Không chặn pipeline — UI có thể offer AI fallback
        _log.warning("natural_parser error (sẽ fallback AI): %s", e,
                     exc_info=True)

    return [], "none"


# ══════════════════════════════════════════════════════════════════════════════
#  TIER-1 PARSER: ===CAU===...===KETCAU=== + LaTeX ex_test
# ══════════════════════════════════════════════════════════════════════════════

_EXACT_BLOCK_RE = re.compile(r"===\s*CAU\s*===(.*?)===\s*KETCAU\s*===",
                             re.DOTALL | re.IGNORECASE)
_EXACT_FULL_BLOCK_RE = re.compile(
    r"===\s*CAU\s*===.*?===\s*KETCAU\s*===",
    re.DOTALL | re.IGNORECASE,
)
_LATEX_FULL_BLOCK_RE = re.compile(
    r"\\begin\{(ex|bt|vd)\}.*?\\end\{\1\}",
    re.DOTALL,
)


def parse_structured_questions(
    text: str,
) -> tuple[list[Question], Literal["exact", "latex", "mixed", "none"]]:
    """Parse app blocks and LaTeX ``ex_test`` blocks in source order.

    The parser only requires recognizable question content. Topic and level
    may remain at parser defaults so the user or AI can classify them later.
    """
    if not text or not text.strip():
        return [], "none"

    exact_matches = list(_EXACT_FULL_BLOCK_RE.finditer(text))
    latex_matches = list(_LATEX_FULL_BLOCK_RE.finditer(text))
    latex_matches = [
        latex_match
        for latex_match in latex_matches
        if not any(
            exact_match.start() <= latex_match.start()
            and latex_match.end() <= exact_match.end()
            for exact_match in exact_matches
        )
    ]
    if not exact_matches and not latex_matches:
        return [], "none"

    if exact_matches and not latex_matches:
        questions = _parse_exact_structure(text)
        return (questions, "exact") if questions else ([], "none")

    if latex_matches and not exact_matches:
        try:
            from core.latex_parser import parse_latex_text

            questions = parse_latex_text(text)
            return (questions, "latex") if questions else ([], "none")
        except Exception as exc:
            _log.warning("latex_parser error: %s", exc, exc_info=True)
            return [], "none"

    try:
        from core.parser import parse_one_question
    except Exception:
        parse_one_question = None

    latex_questions: list[Question] = []
    if latex_matches:
        try:
            from core.latex_parser import parse_latex_text

            # Parse once with the complete source so section metadata survives.
            latex_questions = parse_latex_text(text)
        except Exception as exc:
            _log.warning("latex_parser error: %s", exc, exc_info=True)

    latex_by_start = {}
    if len(latex_questions) == len(latex_matches):
        latex_by_start = {
            match.start(): question
            for match, question in zip(latex_matches, latex_questions)
        }
    candidates: list[tuple[int, str, str]] = [
        (match.start(), "exact", match.group(0)) for match in exact_matches
    ]
    candidates.extend(
        (match.start(), "latex", match.group(0)) for match in latex_matches
    )
    candidates.sort(key=lambda item: item[0])

    questions: list[Question] = []
    parsed_kinds: set[str] = set()
    for start, kind, block in candidates:
        question: Question | None = None
        if kind == "exact" and parse_one_question is not None:
            try:
                question = parse_one_question(block)
            except Exception:
                question = None
        elif kind == "latex":
            question = latex_by_start.get(start)
            if question is None:
                try:
                    from core.latex_parser import parse_latex_text

                    parsed = parse_latex_text(block)
                    question = parsed[0] if parsed else None
                except Exception:
                    question = None

        if question is not None:
            questions.append(question)
            parsed_kinds.add(kind)

    if parsed_kinds == {"exact", "latex"}:
        return questions, "mixed"
    if "exact" in parsed_kinds:
        return questions, "exact"
    if "latex" in parsed_kinds:
        return questions, "latex"
    return [], "none"


def _parse_exact_structure(text: str) -> list[Question]:
    """Tìm các khối ===CAU===...===KETCAU=== và parse qua `core.parser`."""
    from services.native_accel import find_exact_blocks

    blocks = find_exact_blocks(text)
    if not blocks:
        return []

    try:
        from core.parser import parse_one_question
    except Exception:
        return []

    out: list[Question] = []
    for block in blocks:
        full = f"===CAU===\n{block.strip()}\n===KETCAU==="
        try:
            q = parse_one_question(full)
        except Exception:
            q = None
        if q:
            out.append(q)
    return out


# ══════════════════════════════════════════════════════════════════════════════
#  TEXT EXTRACTORS THEO ĐỊNH DẠNG
# ══════════════════════════════════════════════════════════════════════════════

def _read_text_raw(p: Path) -> str:
    """Đọc file text thô với UTF-8 (fallback sang cp1258/cp1252)."""
    for enc in ("utf-8", "utf-8-sig", "cp1258", "cp1252", "latin-1"):
        try:
            return p.read_text(encoding=enc, errors="strict")
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # Lỗi I/O khác — không nên retry, raise ngay
            raise e
    # Fallback cuối: đọc với errors='replace'
    return p.read_text(encoding="utf-8", errors="replace")


def _read_text_docx(p: Path) -> str:
    """Đọc .docx — ưu tiên python-docx + lxml (để lấy OMML math), fallback
    mammoth.
    """
    # Dùng lại hàm chuẩn đã có trong doc_question_parser — tái sử dụng code
    try:
        from core.doc_question_parser import _extract_text_docx
        return _extract_text_docx(str(p))
    except Exception:
        pass

    # Fallback tối giản: python-docx chỉ đọc paragraph.text (không có math)
    try:
        from docx import Document
        doc = Document(str(p))
        lines: list[str] = []
        for para in doc.paragraphs:
            if para.text.strip():
                lines.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if para.text.strip():
                            lines.append(para.text)
        return "\n".join(lines)
    except ImportError:
        raise ImportError(
            "Cần cài python-docx: pip install python-docx")


def _read_text_pdf(p: Path) -> str:
    """Đọc .pdf — ưu tiên PyMuPDF (fitz), fallback pdfplumber."""
    try:
        from core.doc_question_parser import _extract_text_pdf
        return _extract_text_pdf(str(p))
    except Exception:
        pass

    # Fallback inline (phòng khi doc_question_parser bị edit)
    try:
        import fitz  # type: ignore
        doc = fitz.open(str(p))
        parts = []
        for page in doc:
            t = page.get_text("text")
            if t:
                parts.append(t)
        doc.close()
        return "\n".join(parts)
    except ImportError:
        pass

    try:
        import pdfplumber  # type: ignore
        parts = []
        with pdfplumber.open(str(p)) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    parts.append(t)
        return "\n".join(parts)
    except ImportError:
        raise ImportError(
            "Cần cài PyMuPDF hoặc pdfplumber: pip install PyMuPDF")


def _read_text_html(p: Path) -> str:
    """Đọc .html/.htm — bỏ tag, giữ text và basic structure (newline sau
    block-level tags)."""
    html = _read_text_raw(p)

    # Ưu tiên BeautifulSoup (đã có trong requirements)
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Loại bỏ script / style
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # Block-level tags → newline sau text để giữ ngắt câu
        BLOCKS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4",
                  "h5", "h6", "pre", "blockquote"}
        for tag in soup.find_all(BLOCKS):
            tag.append("\n")

        text = soup.get_text()
    except ImportError:
        # Fallback thô: regex strip
        # 1. Xoá script/style kèm nội dung
        text = re.sub(r"<script\b[^>]*>.*?</script>", "",
                      html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style\b[^>]*>.*?</style>", "",
                      text, flags=re.DOTALL | re.IGNORECASE)
        # 2. Block-level → \n
        text = re.sub(r"</?(p|div|br|li|tr|h[1-6]|pre|blockquote)[^>]*>",
                      "\n", text, flags=re.IGNORECASE)
        # 3. Xoá tag còn lại
        text = re.sub(r"<[^>]+>", "", text)
        # 4. Giải escape HTML cơ bản
        text = (text.replace("&nbsp;", " ")
                    .replace("&amp;", "&")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">")
                    .replace("&quot;", '"')
                    .replace("&#39;", "'"))

    # Chuẩn hoá whitespace: nhiều blank lines → 1 blank line
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Space dư (vẫn giữ \n)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
