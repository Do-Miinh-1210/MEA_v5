"""
services/figure_bank.py — NHCH HÌNH VẼ (Figure Bank)

Lưu trữ các hình TikZ do user/AI vẽ:
  • figure_<id>.tex   — code TikZ
  • figure_<id>.png   — ảnh render (tuỳ chọn — user chọn save_png=True)
  • index.json        — metadata: id, title, description, tags, created_at,
                       has_png, source ("ai"/"manual"/"template")

Cấu trúc folder:
  ~/.exam_generator/figures/
  ├── index.json
  ├── figure_001.tex
  ├── figure_001.png    (nếu có)
  ├── figure_002.tex
  └── ...

Có thể đổi đường dẫn qua Settings → "figures_dir".

API:
    >>> from services import figure_bank
    >>> fid = figure_bank.save(
    ...     tikz_code="\\begin{tikzpicture}...\\end{tikzpicture}",
    ...     title="Tam giác ABC vuông tại A",
    ...     description="...", tags=["2D", "tam giác"],
    ...     png_pil=img,  # PIL Image, optional
    ... )
    >>> entries = figure_bank.list_entries()
    >>> entry = figure_bank.get(fid)
    >>> figure_bank.delete(fid)
"""

from __future__ import annotations

import datetime
import json
import logging
import re
import shutil
import threading
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional, Any

_log = logging.getLogger(__name__)
_INDEX_LOCK = threading.RLock()


def _bank_dir() -> Path:
    from config import get_figures_dir
    return get_figures_dir()


def _index_file() -> Path:
    return _bank_dir() / "index.json"


# ── Dataclass ───────────────────────────────────────────────────────────────

@dataclass
class FigureEntry:
    id:           str
    title:        str
    description:  str = ""
    tags:         list[str] = field(default_factory=list)
    created_at:   str = ""
    source:       str = "manual"   # "ai" | "manual" | "template" | "imported" | "nhch" | "rendered"
    tex_filename: str = ""
    png_filename: str = ""    # rỗng nếu không có PNG
    char_count:   int = 0     # chiều dài code TikZ (debug)
    tikz_hash:    str = ""    # hash chuẩn hoá để tự lưu sau render không bị trùng

    @property
    def has_png(self) -> bool:
        return bool(self.png_filename)

    def tex_path(self) -> Path:
        return _bank_dir() / self.tex_filename

    def png_path(self) -> Optional[Path]:
        return (_bank_dir() / self.png_filename) if self.png_filename else None


# ── Index helpers ───────────────────────────────────────────────────────────

def _load_index() -> list[dict]:
    p = _index_file()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        _log.warning("Không đọc được %s: %s", p, e)
        return []


def _save_index(items: list[dict]) -> None:
    p = _index_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(items, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _next_id(existing: list[dict]) -> str:
    """Sinh id dạng 3-digit zero-padded: 001, 002, ..."""
    used = set()
    for it in existing:
        m = re.match(r"^(\d+)$", it.get("id", ""))
        if m:
            used.add(int(m.group(1)))
    n = 1
    while n in used:
        n += 1
    return f"{n:03d}"


# ── Public API ──────────────────────────────────────────────────────────────

def save(
    tikz_code: str,
    title: str,
    description: str = "",
    tags: Optional[list[str]] = None,
    source: str = "manual",
    png_pil=None,             # PIL.Image.Image | None
) -> str:
    """Lưu 1 hình vào kho. Returns: id mới."""
    if not tikz_code.strip():
        raise ValueError("Code TikZ rỗng")
    if not title.strip():
        title = f"Hình không tên — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"

    with _INDEX_LOCK:
        items = _load_index()
        fid = _next_id(items)
        bank_dir = _bank_dir()
        bank_dir.mkdir(parents=True, exist_ok=True)

        tex_name = f"figure_{fid}.tex"
        tex_path = bank_dir / tex_name
        tex_path.write_text(tikz_code, encoding="utf-8")

        png_name = ""
        if png_pil is not None:
            try:
                png_name = f"figure_{fid}.png"
                png_path = bank_dir / png_name
                png_pil.save(png_path, format="PNG")
            except Exception as e:
                _log.warning("Không lưu được PNG cho figure %s: %s", fid, e)
                png_name = ""

        from services.tikz_cache import hash_of

        entry = FigureEntry(
            id=fid, title=title.strip(),
            description=description.strip(),
            tags=tags or [],
            created_at=datetime.datetime.now().isoformat(timespec="seconds"),
            source=source,
            tex_filename=tex_name,
            png_filename=png_name,
            char_count=len(tikz_code),
            tikz_hash=hash_of(tikz_code),
        )
        items.insert(0, asdict(entry))   # mới nhất lên đầu
        _save_index(items)
        return fid


def save_rendered(
    tikz_code: str,
    *,
    png_path: str | Path | None = None,
    png_pil=None,
    title: str = "",
    description: str = "",
    tags: Optional[list[str]] = None,
    source: str = "nhch",
) -> tuple[str, bool]:
    """Lưu hình vừa render nếu chưa có; trả ``(id, created)``.

    Luồng tự động dùng hash TikZ chuẩn hoá để render lại hoặc cache hit không
    tạo thêm bản ghi. Nếu bản cũ chưa có PNG, ảnh vừa render được bổ sung.
    """
    if not tikz_code.strip():
        raise ValueError("Code TikZ rỗng")

    from services.tikz_cache import hash_of

    fingerprint = hash_of(tikz_code)
    with _INDEX_LOCK:
        items = _load_index()
        changed = False
        for item in items:
            item_hash = str(item.get("tikz_hash") or "")
            if not item_hash:
                tex_name = str(item.get("tex_filename") or "")
                tex_file = _bank_dir() / tex_name
                if tex_name and tex_file.is_file():
                    try:
                        item_hash = hash_of(tex_file.read_text(encoding="utf-8"))
                    except OSError:
                        item_hash = ""
                if item_hash:
                    item["tikz_hash"] = item_hash
                    changed = True
            if item_hash != fingerprint:
                continue

            if not item.get("png_filename"):
                source_png = Path(png_path) if png_path else None
                if source_png and source_png.is_file():
                    png_name = f"figure_{item['id']}.png"
                    target_png = _bank_dir() / png_name
                    target_png.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_png, target_png)
                    item["png_filename"] = png_name
                    changed = True
                elif png_pil is not None:
                    png_name = f"figure_{item['id']}.png"
                    target_png = _bank_dir() / png_name
                    target_png.parent.mkdir(parents=True, exist_ok=True)
                    png_pil.save(target_png, format="PNG")
                    item["png_filename"] = png_name
                    changed = True
            if changed:
                _save_index(items)
            return str(item["id"]), False

        rendered_pil = png_pil
        if rendered_pil is None and png_path:
            source_png = Path(png_path)
            if source_png.is_file():
                from PIL import Image

                with Image.open(source_png) as image:
                    rendered_pil = image.copy()
        fid = save(
            tikz_code=tikz_code,
            title=title or "Hình TikZ tự lưu sau render",
            description=description,
            tags=tags or ["TikZ", "tự lưu"],
            source=source,
            png_pil=rendered_pil,
        )
        return fid, True


def list_entries(query: str = "", source_filter: str = "") -> list[FigureEntry]:
    """List tất cả figure (có lọc theo title/description hoặc source)."""
    items = _load_index()
    out: list[FigureEntry] = []
    q = query.strip().lower()
    for d in items:
        e = FigureEntry(**{k: v for k, v in d.items()
                           if k in FigureEntry.__dataclass_fields__})
        if source_filter and e.source != source_filter:
            continue
        if q:
            hay = (e.title + " " + e.description + " " + " ".join(e.tags)).lower()
            if q not in hay:
                continue
        out.append(e)
    return out


def get(fid: str) -> Optional[FigureEntry]:
    """Lấy 1 entry theo id."""
    for e in list_entries():
        if e.id == fid:
            return e
    return None


def get_tikz(fid: str) -> str:
    """Đọc code TikZ của 1 figure."""
    e = get(fid)
    if not e:
        return ""
    p = e.tex_path()
    return p.read_text(encoding="utf-8") if p.exists() else ""


def delete(fid: str) -> bool:
    """Xoá entry + file .tex + .png. Trả True nếu xoá được."""
    items = _load_index()
    for i, d in enumerate(items):
        if d.get("id") == fid:
            tex = _bank_dir() / d.get("tex_filename", "")
            png = _bank_dir() / d.get("png_filename", "") if d.get("png_filename") else None
            try:
                if tex.exists():
                    tex.unlink()
                if png and png.exists():
                    png.unlink()
            except Exception as e:
                _log.warning("Lỗi xoá file figure %s: %s", fid, e)
            items.pop(i)
            _save_index(items)
            return True
    return False


def update_metadata(fid: str, title: str = None, description: str = None,
                    tags: list[str] = None) -> bool:
    """Cập nhật metadata. Truyền None để giữ nguyên."""
    items = _load_index()
    for d in items:
        if d.get("id") == fid:
            if title is not None:       d["title"] = title.strip()
            if description is not None: d["description"] = description.strip()
            if tags is not None:        d["tags"] = list(tags)
            _save_index(items)
            return True
    return False


def count() -> int:
    return len(_load_index())


def stats() -> dict[str, Any]:
    """Tổng quan: tổng, theo source, có PNG…"""
    items = _load_index()
    by_src: dict[str, int] = {}
    with_png = 0
    for d in items:
        s = d.get("source", "manual")
        by_src[s] = by_src.get(s, 0) + 1
        if d.get("png_filename"):
            with_png += 1
    return {
        "total": len(items),
        "with_png": with_png,
        "by_source": by_src,
        "dir": str(_bank_dir()),
    }
