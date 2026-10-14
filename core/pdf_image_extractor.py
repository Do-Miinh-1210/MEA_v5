"""
core/pdf_image_extractor.py — Trích xuất hình ảnh từ trang PDF với thông tin
VỊ TRÍ (bounding box) để chèn đúng chỗ khi xuất Word.

Vấn đề của cách cũ (`page.get_images(full=True)`):
  • Trả về theo thứ tự XREF (internal PDF object ID) — KHÔNG phải thứ tự đọc.
  • Không có bounding box → không biết hình nằm ở đâu trong trang.
  • Không lọc được ảnh trang trí bé xíu (logo header, border).
  • Không bind được hình với câu hỏi nào.

Cách mới:
  1. Dùng `page.get_image_info()` / `page.get_image_rects(xref)` để lấy bbox.
  2. Lọc ảnh:
        • Quá nhỏ  (< 40px cạnh)        → bỏ (logo / icon).
        • Full-page (chiếm > 90% diện tích) → bỏ (background/scan).
  3. Sort theo reading order: (y0, x0) — trên xuống, trái qua phải.
  4. Gán INDEX 1, 2, 3… theo thứ tự đọc — dùng cho marker [HÌNH 1], [HÌNH 2]…
  5. Fallback: nếu `extract_image(xref)` fail (PDF dùng XObject phức tạp) →
     render region của bbox làm PNG thay thế.

API:
    >>> from core.pdf_image_extractor import extract_page_images
    >>> images = extract_page_images(fitz_page, fitz_doc)
    >>> images[0]
    {
        "data": b"...",           # bytes PNG/JPG
        "ext":  "png",
        "width": 800, "height": 600,
        "rect": (x0, y0, x1, y1), # page coords (points)
        "index": 1,               # thứ tự đọc 1-based
        "area": 480000,
        "rel_area": 0.35,         # tỉ lệ với trang
    }

Quy ước bbox (PyMuPDF):
  • Toạ độ tính từ GÓC TRÊN BÊN TRÁI, đơn vị điểm (points, 72 pt = 1 inch).
  • rect = (x0, y0, x1, y1) với x0<x1, y0<y1.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Optional

_log = logging.getLogger(__name__)

# Threshold tuning — điều chỉnh khi gặp PDF đặc biệt
MIN_SIDE_PX   = 40       # ảnh nhỏ hơn → bỏ (logo)
MIN_AREA_PX   = 40 * 40  # diện tích tối thiểu
MAX_REL_AREA  = 0.90     # > 90% trang → bỏ (background scan)
MIN_REL_AREA  = 0.001    # < 0.1% trang → bỏ (dots/noise)


class ExtractionCancelled(Exception):
    """Raised khi caller cancel trong lúc extract (cancel_event.is_set())."""
    pass


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def extract_page_images(
    page: Any,
    doc: Any,
    cancel_event: Optional[threading.Event] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> list[dict]:
    """Trích hình từ 1 trang PDF, đã lọc + sort theo reading order.

    Parameters
    ----------
    page : fitz.Page
    doc  : fitz.Document
    cancel_event : threading.Event, optional
        Nếu set() giữa chừng → dừng ngay và raise ExtractionCancelled.
        Worker UI nên truyền vào để user hủy được pipeline PDF→Word khi
        có trang có hàng trăm image objects.
    on_progress : callable(done: int, total: int), optional
        Gọi sau mỗi image đã xử lý (đủ bước decode + build_item). Callback
        phải thread-safe — caller UI thường dùng `root.after(0, ...)`.

    Returns
    -------
    list[dict]  — mỗi dict có các key: data, ext, width, height, rect,
                  index (1-based), area, rel_area.
                  Đã được lọc ảnh decorative và sort theo thứ tự đọc.

    Raises
    ------
    ExtractionCancelled — caller set cancel_event trong lúc extract.
    """
    def _check_cancel() -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise ExtractionCancelled("Cancelled by caller")

    def _report(done: int, total: int) -> None:
        if on_progress is None:
            return
        try:
            on_progress(done, total)
        except Exception as e:
            # Callback lỗi — không được crash pipeline extract
            _log.debug("on_progress callback error: %s", e)

    try:
        page_rect = page.rect
        page_area = max(1.0, page_rect.width * page_rect.height)
    except Exception as e:
        _log.debug("page.rect unavailable: %s", e)
        return []

    raw_items: list[dict] = []

    # ── Bước 1: dùng get_image_info() nếu có (PyMuPDF >= 1.18) ─────────────
    # Cái này trả bbox SẴN trong kết quả — tiết kiệm 1 lần gọi get_image_rects
    try:
        info_list = page.get_image_info(xrefs=True)
    except Exception as e:
        _log.debug("get_image_info fallback: %s", e)
        info_list = []

    if info_list:
        total = len(info_list)
        for done_idx, info in enumerate(info_list, start=1):
            _check_cancel()
            xref = info.get("xref", 0)
            bbox = info.get("bbox")
            if not bbox or xref <= 0:
                _report(done_idx, total)
                continue
            rect = _coerce_rect(bbox)
            item = _build_image_item(doc, page, xref, rect, page_area)
            if item:
                raw_items.append(item)
            _report(done_idx, total)

    # ── Bước 2: fallback sang get_images() + get_image_rects() ─────────────
    if not raw_items:
        try:
            images_info = page.get_images(full=True)
        except Exception as e:
            _log.debug("get_images fallback: %s", e)
            images_info = []

        total_fb = len(images_info)
        for done_idx, img_info in enumerate(images_info, start=1):
            _check_cancel()
            xref = img_info[0]
            try:
                rects = page.get_image_rects(xref)
            except Exception as e:
                _log.debug("get_image_rects(%d) failed: %s", xref, e)
                rects = []
            if not rects:
                _report(done_idx, total_fb)
                continue
            for rect_obj in rects:
                _check_cancel()
                rect = _coerce_rect(rect_obj)
                item = _build_image_item(doc, page, xref, rect, page_area)
                if item:
                    raw_items.append(item)
            _report(done_idx, total_fb)

    if not raw_items:
        return []

    # ── Bước 3: lọc ảnh trang trí / background ──────────────────────────────
    filtered = [x for x in raw_items if _is_keep(x)]

    # ── Bước 4: dedup — cùng xref + bbox gần giống → chỉ giữ 1 ─────────────
    filtered = _dedup_by_bbox(filtered)

    # ── Bước 5: sort reading order: trên→dưới, trái→phải ──────────────────
    #    Dùng tolerance theo hàng: ảnh cùng "row" (y0 gần nhau ±20pt) sort
    #    theo x0; khác row thì sort theo y0.
    filtered.sort(key=lambda x: (round(x["rect"][1] / 20) * 20, x["rect"][0]))

    # ── Bước 6: gán index 1-based ───────────────────────────────────────────
    for idx, item in enumerate(filtered, start=1):
        item["index"] = idx

    return filtered


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _coerce_rect(r: Any) -> tuple[float, float, float, float]:
    """Chuẩn hóa bbox về tuple (x0, y0, x1, y1). fitz.Rect có indexing."""
    try:
        if hasattr(r, "x0"):
            return (float(r.x0), float(r.y0), float(r.x1), float(r.y1))
        return (float(r[0]), float(r[1]), float(r[2]), float(r[3]))
    except Exception:
        return (0.0, 0.0, 0.0, 0.0)


def _build_image_item(doc: Any, page: Any, xref: int,
                      rect: tuple[float, float, float, float],
                      page_area: float) -> Optional[dict]:
    """Lấy bytes ảnh cho 1 xref + bbox. Fallback = render vùng bbox."""
    x0, y0, x1, y1 = rect
    w_pt = max(0.0, x1 - x0)
    h_pt = max(0.0, y1 - y0)
    area_pt = w_pt * h_pt

    # Thử extract_image (raw image bytes in PDF)
    data: Optional[bytes] = None
    ext = "png"
    px_w, px_h = 0, 0

    try:
        base = doc.extract_image(xref)
        if base and base.get("image"):
            data = base["image"]
            ext = base.get("ext", "png")
            px_w = int(base.get("width", 0))
            px_h = int(base.get("height", 0))
    except Exception:
        data = None

    # Fallback: render vùng bbox thành PNG
    if not data:
        try:
            data, px_w, px_h, ext = _render_clip(page, rect)
        except Exception:
            data = None

    if not data:
        return None

    # Dùng pixel size nếu có, else ước lượng từ pt size (1 pt ≈ 1.33 px @96dpi)
    if px_w <= 0 or px_h <= 0:
        px_w = max(1, int(w_pt * 1.33))
        px_h = max(1, int(h_pt * 1.33))

    return {
        "data":     data,
        "ext":      ext,
        "width":    px_w,
        "height":   px_h,
        "rect":     rect,
        "area":     area_pt,
        "rel_area": (area_pt / page_area) if page_area > 0 else 0.0,
        "index":    0,  # sẽ gán sau khi sort
    }


def _render_clip(page: Any, rect: tuple[float, float, float, float]
                 ) -> tuple[bytes, int, int, str]:
    """Fallback: render vùng bbox của page thành PNG."""
    import fitz
    x0, y0, x1, y1 = rect
    zoom = 300 / 72.0  # 300 DPI
    mat = fitz.Matrix(zoom, zoom)
    clip = fitz.Rect(x0, y0, x1, y1)
    pix = page.get_pixmap(matrix=mat, alpha=False, clip=clip)
    return pix.tobytes("png"), pix.width, pix.height, "png"


def _is_keep(item: dict) -> bool:
    """Quyết định giữ hay bỏ 1 ảnh dựa trên kích thước."""
    w = item["width"]
    h = item["height"]
    rel = item["rel_area"]

    if w < MIN_SIDE_PX or h < MIN_SIDE_PX:
        return False
    if w * h < MIN_AREA_PX:
        return False
    if rel > MAX_REL_AREA:
        return False  # full-page background
    if rel < MIN_REL_AREA:
        return False  # dot/noise
    return True


def _dedup_by_bbox(items: list[dict]) -> list[dict]:
    """Khử trùng ảnh cùng bbox (một số PDF embed 1 hình nhiều lần)."""
    out: list[dict] = []
    seen: list[tuple[float, float, float, float]] = []
    for it in items:
        r = it["rect"]
        dup = any(_bbox_close(r, s) for s in seen)
        if not dup:
            out.append(it)
            seen.append(r)
    return out


def _bbox_close(a: tuple[float, float, float, float],
                b: tuple[float, float, float, float],
                tol: float = 2.0) -> bool:
    """2 bbox được coi là 'giống nhau' nếu lệch ≤ tol điểm ở mọi cạnh."""
    return all(abs(a[i] - b[i]) <= tol for i in range(4))


# ══════════════════════════════════════════════════════════════════════════════
#  BIND IMAGE ↔ QUESTION (cho tab AI Text → Câu hỏi)
# ══════════════════════════════════════════════════════════════════════════════

def bind_images_to_questions(images: list[dict],
                             question_bboxes: list[tuple[int, tuple[float, float, float, float]]]
                             ) -> dict[int, list[int]]:
    """Map image_index → list các question_index mà image nằm trong vùng y của
    câu đó.

    Parameters
    ----------
    images          : kết quả `extract_page_images`
    question_bboxes : list[(question_index, (x0,y0,x1,y1))] — bbox câu hỏi
                      trên page coord (có thể suy từ text blocks)

    Returns
    -------
    dict[img_index, list[question_index]]
        Với mỗi ảnh, danh sách câu hỏi mà nó overlap vùng y (thường 1 câu).
    """
    result: dict[int, list[int]] = {}
    for img in images:
        img_idx = img["index"]
        img_y0 = img["rect"][1]
        img_y1 = img["rect"][3]
        matched: list[int] = []
        for q_idx, q_box in question_bboxes:
            q_y0, q_y1 = q_box[1], q_box[3]
            # Overlap theo trục y
            if img_y1 >= q_y0 and img_y0 <= q_y1:
                matched.append(q_idx)
        if matched:
            result[img_idx] = matched
    return result
