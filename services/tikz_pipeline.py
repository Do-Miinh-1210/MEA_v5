"""
services/tikz_pipeline.py — Pipeline async: Detect → Cache → Render → Rewrite Question.

Thiết kế đã fix các điểm lưu ý:

  #1  Dùng `services.tikz_renderer.render_tikz_to_image` để pipeline không
      phụ thuộc UI (pdflatex + PyMuPDF/pdftoppm fallback, timeout cấu hình).
  #2  Hash SAU KHI chuẩn hoá — dùng `services.tikz_cache.hash_of()`.
  #3  Batch để có progress bar, không phải để tăng tốc — ThreadPoolExecutor với
      max_workers=min(3, cpu). Mỗi call render_tikz_to_image đã có TemporaryDirectory
      riêng nên không đụng file lock giữa các worker.
  #4  KHÔNG render inline khi tạo câu — pipeline chạy theo yêu cầu của user
      (từ nút bấm trong tab Xuất đề).
  #5  Exports không cần biết marker — pipeline STRIP khối TikZ khỏi text và gán
      cặp PNG preview + EMF vector vào slot ảnh có sẵn (q.question_image,
      q.solution_image, q.item_images, q.option_images). Word exporter ưu tiên
      EMF, còn UI tiếp tục dùng PNG để preview.
"""

from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from services import tikz_cache, tikz_detector
from services.tikz_detector import TikzBlock

from config import APP_DIR  # type: ignore


_EMF_CACHE_DIR = APP_DIR / "cache" / "tikz_emf"
_EMF_CACHE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_MODE_EMF = "emf"
OUTPUT_MODE_PNG = "png"
_OUTPUT_MODES = {OUTPUT_MODE_EMF, OUTPUT_MODE_PNG}


# Lazy-import render engine để chỉ tải thư viện render khi thật sự cần.
def _get_render_fn():
    from services.tikz_renderer import render_tikz_to_image  # noqa: WPS433
    return render_tikz_to_image


def _emf_path_for(code: str) -> Path:
    return _EMF_CACHE_DIR / f"{tikz_cache.hash_of(code)}.emf"


def _get_emf(code: str) -> str | None:
    path = _emf_path_for(code)
    return str(path) if path.exists() and path.stat().st_size > 0 else None


@dataclass
class RenderResult:
    q_index: int
    block:   TikzBlock
    png:     Optional[str] = None   # None nếu lỗi
    emf:     Optional[str] = None
    cached:  bool = False
    error:   str  = ""


@dataclass
class PipelineReport:
    total:   int = 0
    ok:      int = 0
    cached:  int = 0
    emf:     int = 0
    failed:  int = 0
    bank_saved: int = 0
    output_mode: str = OUTPUT_MODE_EMF
    results: list[RenderResult] = field(default_factory=list)

    def summary(self) -> str:
        vector_part = (
            f"EMF vector: {self.emf}"
            if self.output_mode == OUTPUT_MODE_EMF
            else f"PNG: {self.ok}"
        )
        return (
            f"Tổng: {self.total} khối TikZ  |  "
            f"Thành công: {self.ok}  "
            f"(cache hit: {self.cached})  |  "
            f"{vector_part}  |  "
            f"Lỗi: {self.failed}  |  "
            f"Kho hình mới: {self.bank_saved}"
        )


# ── Render 1 block ──────────────────────────────────────────────────────────

_RENDER_LOCKS: dict[str, threading.Lock] = {}
_RENDER_LOCKS_GUARD = threading.Lock()


def _get_code_lock(code_hash: str) -> threading.Lock:
    with _RENDER_LOCKS_GUARD:
        if code_hash not in _RENDER_LOCKS:
            _RENDER_LOCKS[code_hash] = threading.Lock()
        return _RENDER_LOCKS[code_hash]


def _render_one(
    idx: int,
    blk: TikzBlock,
    dpi: int,
    output_mode: str = OUTPUT_MODE_EMF,
) -> RenderResult:
    from services.tikz_preflight import auto_fix

    # Tự động sửa các lỗi cú pháp phổ biến (vd: \tkzTabVector -> \tkzTabVar)
    fixed_code = auto_fix(blk.code)
    if fixed_code != blk.code:
        blk = TikzBlock(blk.field, blk.start, blk.end, fixed_code)

    code_hash = tikz_cache.hash_of(blk.code)
    lock = _get_code_lock(code_hash)
    with lock:
        cached = tikz_cache.get(blk.code)
        cached_emf = _get_emf(blk.code)
        if output_mode == OUTPUT_MODE_PNG and cached:
            return RenderResult(idx, blk, cached, None, cached=True)
        if cached and cached_emf:
            return RenderResult(idx, blk, cached, cached_emf, cached=True)

        try:
            png_path = cached
            pdf_path = ""
            if not png_path:
                render_fn = _get_render_fn()
                img, _log_text, pdf_path = render_fn(blk.code, dpi=dpi, return_log=True)
                png_path = tikz_cache.put_pil(blk.code, img)

            if output_mode == OUTPUT_MODE_PNG:
                return RenderResult(idx, blk, png_path, None, cached=bool(cached))

            emf_path = cached_emf
            if not emf_path:
                target = _emf_path_for(blk.code)
                if pdf_path:
                    from services.tikz_vector_export import convert_pdf_to_emf
                    emf_path = str(convert_pdf_to_emf(pdf_path, target))
                else:
                    from services.tikz_vector_export import export_tikz_to_emf
                    emf_path = str(export_tikz_to_emf(blk.code, target))
            return RenderResult(idx, blk, png_path, emf_path, cached=bool(cached and cached_emf))
        except Exception as e:  # noqa: BLE001 — thu thập mọi lỗi vào report
            return RenderResult(idx, blk, None, error=(str(e)[:500] or type(e).__name__))


# ── Rewrite: strip TikZ khỏi text + gán PNG preview / EMF vector ───────────

def _slot_for(field_name: str) -> tuple[str, Optional[str]]:
    """Map field → (attr trên Question, key phụ nếu là dict).

    Trả (attr, None) cho slot str, (attr, key) cho slot dict.
    (attr, None) với attr rỗng = không có slot (skip).
    """
    if field_name in ("tikz_code", "question"):
        return ("question_image", None)
    if field_name == "solution":
        return ("solution_image", None)
    if field_name.startswith("items."):
        return ("item_images", field_name.split(".", 1)[1])
    if field_name.startswith("item_solutions."):
        # Không có slot riêng → nối vào solution_image (chỉ 1 ảnh/câu)
        return ("solution_image", None)
    if field_name.startswith("options."):
        return ("option_images", field_name.split(".", 1)[1])
    return ("", None)


def _strip_block_from_text(text: str, blk: TikzBlock) -> str:
    """Cắt khối TikZ khỏi text gốc, giữ lại các phần còn lại (gộp khoảng trắng thừa)."""
    if not text:
        return text
    out = text[:blk.start] + text[blk.end:]
    from services.native_accel import collapse_blank_lines
    return collapse_blank_lines(out)


# Nhận diện các dòng rác quanh khối TikZ mà AI hay sinh kèm:
#   • "Hình vẽ: <mô tả bằng lời>"   → không cần vì đã có ảnh PNG
#   • "TikZ:" còn sót (block bên dưới đã bị strip)
# Áp dụng SAU khi strip block để đảm bảo model cũ (đã lỡ sinh text đó) cũng sạch.
import re as _re
_FIGURE_DESC_RE = _re.compile(
    r"(?im)^[ \t]*(?:H[ìi]nh\s*v[ẽe]|Figure)\s*:[^\n]*\n?",
)
_TIKZ_PREFIX_ORPHAN_RE = _re.compile(
    r"(?im)^[ \t]*TikZ\s*:\s*\n?",
)


def _strip_figure_noise(text: str) -> str:
    """Xoá các dòng 'Hình vẽ: ...' và tiền tố 'TikZ:' còn sót sau khi strip block.

    Idempotent — gọi nhiều lần cũng không hư text. Không chạm vào công thức toán
    hay bảng số liệu; chỉ bắt đúng dòng header có dấu 2 chấm.
    """
    if not text:
        return text
    out = _FIGURE_DESC_RE.sub("", text)
    out = _TIKZ_PREFIX_ORPHAN_RE.sub("", out)
    # Gộp nhiều dòng trống liên tiếp (sau khi xoá có thể tạo khoảng trắng thừa)
    from services.native_accel import collapse_blank_lines
    return collapse_blank_lines(out)


def _apply_rewrites(exam, results: list[RenderResult]) -> None:
    """Strip TikZ khỏi text + gán PNG/EMF vào slot, không làm lệch offset."""
    from collections import defaultdict
    from services.image_fields import serialize_vector_image
    from services.tikz_preflight import auto_fix

    # Gom theo (q_idx, field)
    groups: dict[tuple[int, str], list[RenderResult]] = defaultdict(list)
    for r in results:
        if r.png:  # chỉ rewrite khi có ảnh thật
            groups[(r.q_index, r.block.field)].append(r)

    for (qi, fld), items in groups.items():
        q = exam.questions[qi]
        attr, key = _slot_for(fld)
        if not attr:
            continue  # không có slot nào để gán → skip

        # Sort ngược theo start để slicing không lệch offset
        items.sort(key=lambda r: r.block.start, reverse=True)

        if fld == "tikz_code":
            # Block dedicated: gán ảnh vào slot, xóa code khỏi model
            if not getattr(q, attr, ""):
                setattr(q, attr, serialize_vector_image(items[0].png or "", items[0].emf or ""))
            q.tikz_code = ""
            continue

        # Field là text → strip khối TikZ ra và gán preview/vector nếu slot rỗng.
        if key is None:
            # slot là str
            cur_text = getattr(q, fld, "")
            for r in items:
                cur_text = _strip_block_from_text(cur_text, r.block)
            cur_text = _strip_figure_noise(cur_text)
            setattr(q, fld, cur_text)

            if not getattr(q, attr, ""):
                setattr(q, attr, serialize_vector_image(items[0].png or "", items[0].emf or ""))

            # Dọn q.tikz_code nếu đã render xong để tránh còn sót code thô
            cur_tc = getattr(q, "tikz_code", "")
            if cur_tc:
                norm_tc = "".join(auto_fix(cur_tc).split())
                if any(
                    norm_tc == "".join(r.block.code.split())
                    or norm_tc in "".join(r.block.code.split())
                    for r in items
                ):
                    q.tikz_code = ""
        else:
            # slot là dict (items/option_images)
            # fld = "items.a" / "options.B"  → parent dict name
            parent = fld.split(".", 1)[0]
            cur_dict = getattr(q, parent, {}) or {}
            cur_text = cur_dict.get(key, "")
            for r in items:
                cur_text = _strip_block_from_text(cur_text, r.block)
            cur_text = _strip_figure_noise(cur_text)
            cur_dict[key] = cur_text
            setattr(q, parent, cur_dict)

            slot_dict = getattr(q, attr, {}) or {}
            if not slot_dict.get(key):
                slot_dict[key] = serialize_vector_image(items[0].png or "", items[0].emf or "")
                setattr(q, attr, slot_dict)


def _save_rendered_to_bank(exam, results: list[RenderResult]) -> int:
    """Đồng bộ hình render thành công vào kho hình, có chống trùng theo hash."""
    from services import figure_bank

    saved = 0
    for result in results:
        if not result.png:
            continue
        question = exam.questions[result.q_index]
        qid = str(getattr(question, "question_id", "") or result.q_index + 1)
        try:
            _fid, created = figure_bank.save_rendered(
                result.block.code,
                png_path=result.png,
                title=f"Hình NHCH {qid} - {result.block.field}",
                description="Tự động lưu sau khi render TikZ trong NHCH.",
                tags=["TikZ", "NHCH", result.block.field],
                source="nhch",
            )
            if created:
                saved += 1
        except Exception:
            # Figure Bank là bản lưu bổ sung; không làm hỏng luồng xuất đề nếu
            # thư mục kho bị khoá hoặc không thể ghi.
            continue
    return saved


# ── Entry point công khai ───────────────────────────────────────────────────

def process_exam(
    exam,
    *,
    dpi: int = 300,
    max_workers: Optional[int] = None,
    progress_cb: Optional[Callable[[int, int, int], None]] = None,
    cancel_event: Optional[threading.Event] = None,
    output_mode: str = OUTPUT_MODE_EMF,
) -> PipelineReport:
    """Render mọi khối TikZ, tạo PNG hoặc EMF + PNG preview, rồi gán vào slot ảnh.

    Args:
        exam:        ExamData (có `.questions: list[Question]`)
        dpi:         Độ phân giải PNG (mặc định 300 để in ấn đẹp).
        max_workers: Số worker song song. Mặc định min(3, cpu).
        progress_cb: callback(done, total, errors) sau mỗi task.
        cancel_event: Event để huỷ giữa chừng (UI bấm "Hủy").
        output_mode: "emf" để tạo EMF vector + PNG preview, hoặc "png" để chỉ tạo PNG.

    Returns:
        PipelineReport — tóm tắt + list RenderResult chi tiết để UI show dialog lỗi.
    """
    if output_mode not in _OUTPUT_MODES:
        raise ValueError(f"Unsupported TikZ output mode: {output_mode}")

    if max_workers is None:
        max_workers = max(1, min(3, (os.cpu_count() or 2)))

    # 1) Quét tất cả blocks
    tasks: list[tuple[int, TikzBlock]] = []
    for i, q in enumerate(exam.questions):
        for blk in tikz_detector.scan_question(q):
            tasks.append((i, blk))

    report = PipelineReport(total=len(tasks), output_mode=output_mode)
    if not tasks:
        return report

    # 2) Render song song (render engine đã per-call TemporaryDirectory)
    errs = 0
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="tikz") as pool:
        futs = {
            pool.submit(_render_one, i, b, dpi, output_mode): (i, b)
            for i, b in tasks
        }
        for fut in as_completed(futs):
            if cancel_event is not None and cancel_event.is_set():
                # Không thể cancel job đã submit, nhưng không submit thêm (đã submit xong)
                # Thu kết quả những cái đã chạy xong rồi break
                r = fut.result()
                report.results.append(r)
                continue
            r = fut.result()
            report.results.append(r)
            if r.error:
                errs += 1
                report.failed += 1
            else:
                report.ok += 1
                if r.emf:
                    report.emf += 1
                if r.cached:
                    report.cached += 1

            if progress_cb is not None:
                try:
                    progress_cb(len(report.results), report.total, errs)
                except Exception:
                    pass

    # 3) Đồng bộ hình đã render vào Figure Bank trước khi strip code khỏi model.
    report.bank_saved = _save_rendered_to_bank(exam, report.results)

    # 4) Rewrite: strip TikZ text + gán PNG slot (chạy trên main-ish thread,
    #    không cần lock vì exam giờ chỉ có 1 caller truy cập)
    _apply_rewrites(exam, report.results)
    return report


# ── Single-block helper (cho dialog preview hoặc web API 1-shot) ────────────

def render_single(code: str, *, dpi: int = 300) -> tuple[Optional[str], str]:
    """Render 1 block TikZ, trả (png_path, error). png_path=None nếu lỗi."""
    cached = tikz_cache.get(code)
    if cached:
        return cached, ""
    try:
        render_fn = _get_render_fn()
        img = render_fn(code, dpi=dpi)
        return tikz_cache.put_pil(code, img), ""
    except Exception as e:  # noqa: BLE001
        return None, (str(e)[:500] or type(e).__name__)
