"""
services/tikz_kb.py — Knowledge Base loader cho TikZ templates.

App đọc các file .txt trong `data/tikz_kb/**/` lúc khởi động lần đầu, cache
trong RAM. Cấu trúc 1 file:

    === TEMPLATE: <Tên hiển thị> ===
    TAGS: <từ khoá phân loại, cách bằng dấu phẩy>
    KEYWORDS: <từ khoá tìm kiếm để match đề>
    NOTES: <ghi chú ngắn — tuỳ chọn>

    \\begin{tikzpicture}
      ...code...
    \\end{tikzpicture}

    === TEMPLATE: <Tên kế tiếp> ===
    ...

API chính:
    >>> from services import tikz_kb
    >>> tikz_kb.load()                    # gọi 1 lần lúc startup
    >>> tikz_kb.get_template_names()       # list tên cho Combobox
    >>> tikz_kb.get_template("Tam giác ABC")  # lấy code TikZ
    >>> tikz_kb.find_relevant("hình chóp đáy vuông", k=3)
    [TikzTemplate(name=..., code=..., score=...), ...]
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_log = logging.getLogger(__name__)


# ── Resolve KB directory ──────────────────────────────────────────────────────

def _kb_dir() -> Path:
    """Thư mục KB — `<repo>/data/tikz_kb/`. Tạo nếu chưa có."""
    here = Path(__file__).resolve().parent.parent  # .../MEA_v4/
    d = here / "data" / "tikz_kb"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class TikzTemplate:
    name:     str
    tags:     list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    notes:    str = ""
    code:     str = ""
    source:   str = ""   # đường dẫn file gốc (debug)
    score:    float = 0.0  # dùng khi search

    def kw_text(self) -> str:
        """Gộp tất cả text dùng cho match (lowercase)."""
        return " ".join([
            self.name.lower(),
            " ".join(self.tags).lower(),
            " ".join(self.keywords).lower(),
            self.notes.lower(),
        ])


# ── Module-level cache ───────────────────────────────────────────────────────

_TEMPLATES: dict[str, TikzTemplate] = {}
_LOADED: bool = False


# ── Parser ───────────────────────────────────────────────────────────────────

_HEADER_RE = re.compile(
    r"^=+\s*TEMPLATE\s*:\s*(.+?)\s*=+\s*$",
    re.MULTILINE | re.IGNORECASE,
)


def _parse_block(block: str, source: str) -> Optional[TikzTemplate]:
    """Parse 1 khối TEMPLATE đã tách. Trả None nếu không có code TikZ."""
    lines = block.splitlines()
    name = ""
    tags: list[str] = []
    keywords: list[str] = []
    notes = ""
    code_lines: list[str] = []
    in_code = False

    for ln in lines:
        stripped = ln.strip()
        if not in_code:
            if stripped.lower().startswith("tags:"):
                tags = [t.strip() for t in stripped[5:].split(",") if t.strip()]
            elif stripped.lower().startswith("keywords:"):
                keywords = [k.strip() for k in stripped[9:].split(",") if k.strip()]
            elif stripped.lower().startswith("notes:"):
                notes = stripped[6:].strip()
            elif stripped.startswith("\\begin{tikzpicture}"):
                in_code = True
                code_lines.append(ln)
            elif stripped == "" or stripped.startswith("==="):
                continue
            # ignore other lines (free text within metadata section)
        else:
            code_lines.append(ln)
            if stripped.startswith("\\end{tikzpicture}"):
                break

    code = "\n".join(code_lines).strip()
    if not code or "\\begin{tikzpicture}" not in code or "\\end{tikzpicture}" not in code:
        return None

    return TikzTemplate(
        name=name, tags=tags, keywords=keywords, notes=notes,
        code=code, source=source,
    )


def _parse_file(path: Path) -> list[TikzTemplate]:
    """Parse 1 file .txt → list TikzTemplate."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        _log.warning("Không đọc được %s: %s", path, e)
        return []

    # Tách theo `=== TEMPLATE: NAME ===`
    matches = list(_HEADER_RE.finditer(text))
    if not matches:
        return []

    out: list[TikzTemplate] = []
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        block_start = m.end()
        block_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block_text = text[block_start:block_end]

        tpl = _parse_block(block_text, source=str(path))
        if tpl is None:
            _log.warning(
                "Template '%s' trong %s thiếu \\begin/\\end{tikzpicture} — bỏ qua",
                name, path.name,
            )
            continue
        tpl.name = name
        out.append(tpl)

    return out


# ── Public API ───────────────────────────────────────────────────────────────

def load(force: bool = False) -> int:
    """Đọc TẤT CẢ file .txt trong KB. Idempotent — gọi nhiều lần OK.

    Returns: số template đã load.
    """
    global _LOADED
    if _LOADED and not force:
        return len(_TEMPLATES)

    _TEMPLATES.clear()
    root = _kb_dir()
    n = 0
    for path in sorted(root.rglob("*.txt")):
        if path.name.upper().startswith("README"):
            continue
        for tpl in _parse_file(path):
            # Dedupe theo name — file load sau ghi đè (nếu user copy template)
            _TEMPLATES[tpl.name] = tpl
            n += 1
    _LOADED = True
    _log.info("TikZ KB: loaded %d templates from %s", n, root)
    return n


def get_template_names() -> list[str]:
    """Trả list tên template cho Combobox UI."""
    if not _LOADED:
        load()
    return sorted(_TEMPLATES.keys())


def get_template(name: str) -> Optional[TikzTemplate]:
    """Lấy 1 template theo tên chính xác."""
    if not _LOADED:
        load()
    return _TEMPLATES.get(name)


def get_template_code(name: str, default: str = "") -> str:
    """Lấy code TikZ theo tên (tiện cho UI cũ chỉ cần str)."""
    tpl = get_template(name)
    return tpl.code if tpl else default


def all_templates() -> list[TikzTemplate]:
    if not _LOADED:
        load()
    return list(_TEMPLATES.values())


# ── Search / few-shot retrieval ──────────────────────────────────────────────

# Synonyms để boost match (vd "đáy vuông" ≈ "tứ giác đều", "lập phương" ≈ "cube")
_SYNONYMS = {
    "vuông": ["right angle", "perpendicular"],
    "đường tròn": ["circle"],
    "tam giác": ["triangle"],
    "tứ giác": ["quadrilateral"],
    "hình chóp": ["pyramid"],
    "chóp": ["pyramid"],
    "lăng trụ": ["prism"],
    "lập phương": ["cube"],
    "trụ": ["cylinder"],
    "nón": ["cone"],
    "cầu": ["sphere"],
    "tứ diện": ["tetrahedron"],
    "đồ thị": ["graph"],
    "bbt": ["bảng biến thiên", "table"],
    "bảng biến thiên": ["bbt"],
    "tiệm cận": ["asymptote"],
    "cực trị": ["cực đại", "cực tiểu"],
    "đường cao": ["altitude"],
    "trung tuyến": ["median"],
    "phân giác": ["bisector"],
    "tiếp tuyến": ["tangent"],
}


def _normalize(s: str) -> str:
    """Lowercase + thay synonym để text khớp KB tốt hơn."""
    out = s.lower()
    for k, vs in _SYNONYMS.items():
        if k in out:
            for v in vs:
                if v not in out:
                    out += " " + v
    return out


def find_relevant(query: str, k: int = 3) -> list[TikzTemplate]:
    """Trả top-k template liên quan nhất với mô tả `query`.

    Scoring: số keyword/tag/notes của template xuất hiện trong query (chuẩn hoá).
    Đơn giản nhưng đủ tốt cho few-shot retrieval. Không cần embeddings.
    """
    if not _LOADED:
        load()
    if not _TEMPLATES:
        return []

    q = _normalize(query)
    scored: list[tuple[float, TikzTemplate]] = []
    for tpl in _TEMPLATES.values():
        score = 0.0
        # Match từ khoá (mỗi hit = 2 điểm)
        for kw in tpl.keywords:
            if kw.lower() in q:
                score += 2.0
        # Match tag (mỗi hit = 1 điểm)
        for tag in tpl.tags:
            if tag.lower() in q:
                score += 1.0
        # Match name (3 điểm — name khớp = rất liên quan)
        nm_lower = tpl.name.lower()
        if nm_lower in q:
            score += 3.0
        else:
            # Match từng từ trong name
            for word in re.split(r"\s+", nm_lower):
                if len(word) >= 4 and word in q:
                    score += 0.5

        if score > 0:
            tpl_copy = TikzTemplate(
                name=tpl.name, tags=tpl.tags, keywords=tpl.keywords,
                notes=tpl.notes, code=tpl.code, source=tpl.source,
                score=score,
            )
            scored.append((score, tpl_copy))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [t for _, t in scored[:k]]


def build_few_shot_block(query: str, k: int = 2, max_chars: int = 2500) -> str:
    """Xây string few-shot examples để inject vào prompt AI.

    Lấy top-k template liên quan với `query`, format thành block context.
    Cắt nếu vượt `max_chars` để không phình prompt.
    """
    relevant = find_relevant(query, k=k)
    if not relevant:
        return ""

    parts = ["MẪU THAM KHẢO TỪ KHO HÌNH (chỉ dùng làm tham khảo cấu trúc — vẫn phải khớp dữ kiện đề bài):"]
    total = len(parts[0])
    for tpl in relevant:
        block = (
            f"\n\n--- {tpl.name} ---\n"
            + (f"Ghi chú: {tpl.notes}\n" if tpl.notes else "")
            + tpl.code
        )
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "".join(parts)
