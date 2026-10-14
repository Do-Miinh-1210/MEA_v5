"""Question-by-question preview cards for the V5 Exam Create result panel."""
from __future__ import annotations

import copy
from collections import OrderedDict, deque
from pathlib import Path
from typing import Any, Callable
import uuid

import customtkinter as ctk

from v5.ui_perf import (
    CARD_DESTROY_BATCH_SIZE,
    CARD_DESTROY_INTERVAL_MS,
    CARD_RENDER_BATCH_SIZE,
    CARD_RENDER_INTERVAL_MS,
    CARD_THUMBNAIL_CACHE_MAX,
)


QTYPE_LABELS = {
    "TN": "Trắc nghiệm",
    "DS": "Đúng - Sai",
    "TLN": "Trả lời ngắn",
    "TL": "Tự luận",
}

QTYPE_COLORS = {
    "TN": "#2563EB",
    "DS": "#7C3AED",
    "TLN": "#D97706",
    "TL": "#DC2626",
}

LEVEL_COLORS = {
    "NB": "#16A34A",
    "TH": "#2563EB",
    "VD": "#D97706",
    "VDC": "#DC2626",
}

PREVIEW_THUMBNAIL_SIZE = (260, 150)
_THUMBNAIL_CACHE: OrderedDict[tuple[str, int, int, int, int], Any] = OrderedDict()


def card_render_ranges(total: int, batch_size: int = CARD_RENDER_BATCH_SIZE) -> list[tuple[int, int]]:
    """Return card index ranges for incremental rendering."""
    total = max(0, int(total or 0))
    batch_size = max(1, int(batch_size or 1))
    return [(start, min(start + batch_size, total))
            for start in range(0, total, batch_size)]


def clear_preview_thumbnail_cache() -> None:
    """Clear the small in-memory thumbnail cache used by question cards."""
    _THUMBNAIL_CACHE.clear()


def load_preview_thumbnail(path: str | Path, size: tuple[int, int] = PREVIEW_THUMBNAIL_SIZE):
    """Load and resize a preview image, reusing it while the file is unchanged."""
    try:
        image_path = Path(path)
        stat = image_path.stat()
        width, height = max(1, int(size[0])), max(1, int(size[1]))
        key = (
            str(image_path.resolve()),
            int(stat.st_mtime_ns),
            int(stat.st_size),
            width,
            height,
        )
        cached = _THUMBNAIL_CACHE.get(key)
        if cached is not None:
            _THUMBNAIL_CACHE.move_to_end(key)
            return cached

        from PIL import Image

        with Image.open(image_path) as original:
            source = original.copy()
        source.thumbnail((width, height))
        _THUMBNAIL_CACHE[key] = source
        while len(_THUMBNAIL_CACHE) > CARD_THUMBNAIL_CACHE_MAX:
            _THUMBNAIL_CACHE.popitem(last=False)
        return source
    except Exception:
        return None


def answer_lines(question) -> list[tuple[str, str, bool]]:
    """Return answer rows for display without depending on desktop widgets."""
    qtype = str(getattr(question, "qtype", "") or "")
    if qtype == "TN":
        options = getattr(question, "options", {}) or {}
        correct = str(getattr(question, "answer", "") or "")
        return [(key, str(options.get(key, "")), key == correct)
                for key in "ABCD" if key in options]
    if qtype == "DS":
        items = getattr(question, "items", {}) or {}
        answers = getattr(question, "answers", {}) or {}
        return [(str(key), str(value), bool(answers.get(key, False)))
                for key, value in sorted(items.items())]
    answer = str(getattr(question, "answer", "") or "")
    return [("Đáp án", answer, True)] if answer else []


def image_rows(question) -> list[tuple[str, str]]:
    """Return preview image slots produced by upload or the TikZ-to-EMF pipeline."""
    def _preview_path(value) -> str:
        try:
            from services.image_fields import normalize_image_field
            paths = normalize_image_field(value)
            return paths[0] if paths else ""
        except Exception:
            return str(value or "")

    rows: list[tuple[str, str]] = []
    question_path = _preview_path(getattr(question, "question_image", ""))
    solution_path = _preview_path(getattr(question, "solution_image", ""))
    if question_path:
        rows.append(("Hình câu hỏi", question_path))
    for key, path in sorted((getattr(question, "option_images", {}) or {}).items()):
        preview = _preview_path(path)
        if preview:
            rows.append((f"Hình đáp án {key}", preview))
    for key, path in sorted((getattr(question, "item_images", {}) or {}).items()):
        preview = _preview_path(path)
        if preview:
            rows.append((f"Hình ý {key}", preview))
    if solution_path:
        rows.append(("Hình lời giải", solution_path))
    return rows


def pending_tikz_count(question) -> int:
    try:
        from services.tikz_detector import count_blocks
        return int(count_blocks(question))
    except Exception:
        return 0


def clone_question_for_edit(question):
    """Create a clean duplicate that can be edited as a new question."""
    cloned = copy.deepcopy(question)
    cloned.question_id = f"QID-{uuid.uuid4().hex[:10].upper()}"
    cloned._review = None
    cloned._error = False
    cloned._error_msg = ""
    return cloned


class QuestionCardsPanel(ctk.CTkFrame):
    """Display full generated questions as readable cards, like the V4 result tab."""

    def __init__(
        self,
        parent,
        *,
        on_edit: Callable[[int], None] | None = None,
        on_latex: Callable[[int], None] | None = None,
        on_regenerate: Callable[[int], None] | None = None,
        on_move: Callable[[int, int], None] | None = None,
        on_delete: Callable[[int], None] | None = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self._on_edit = on_edit
        self._on_latex = on_latex
        self._on_regenerate = on_regenerate
        self._on_move = on_move
        self._on_delete = on_delete
        self._images: list[ctk.CTkImage] = []
        self._render_after_id = None
        self._destroy_after_id = None
        self._destroy_queue = deque()
        self._render_token = 0
        self._render_questions: list = []
        self._render_total = 0
        self._render_index = 0
        self.set_questions([])

    def set_questions(self, questions: list) -> None:
        self._cancel_pending_render()
        self._schedule_destroy_children(self.winfo_children())
        self._images.clear()
        self._render_token += 1
        if not questions:
            ctk.CTkLabel(
                self,
                text="Chưa có câu hỏi để xem chi tiết.",
                text_color="gray",
                anchor="w",
            ).pack(fill="x", padx=4, pady=8)
            return
        self._render_questions = list(questions)
        self._render_total = len(self._render_questions)
        self._render_index = 0
        self._render_next_batch(self._render_token)

    def _cancel_pending_render(self) -> None:
        after_id = self._render_after_id
        self._render_after_id = None
        self._render_questions = []
        self._render_total = 0
        self._render_index = 0
        if after_id is not None:
            try:
                self.after_cancel(after_id)
            except Exception:
                pass

    def _schedule_destroy_children(self, children) -> None:
        queued = []
        for child in list(children):
            try:
                if not child.winfo_exists():
                    continue
                self._detach_child(child)
                queued.append(child)
            except Exception:
                pass
        if not queued:
            return
        self._destroy_queue.extend(queued)
        if self._destroy_after_id is None:
            try:
                self._destroy_after_id = self.after(1, self._destroy_next_batch)
            except Exception:
                self._destroy_after_id = None

    @staticmethod
    def _detach_child(child) -> None:
        for forget in ("pack_forget", "grid_forget", "place_forget"):
            try:
                getattr(child, forget)()
                return
            except Exception:
                continue

    def _destroy_next_batch(self) -> None:
        self._destroy_after_id = None
        for _ in range(min(CARD_DESTROY_BATCH_SIZE, len(self._destroy_queue))):
            child = self._destroy_queue.popleft()
            try:
                if child.winfo_exists():
                    child.destroy()
            except Exception:
                pass
        if self._destroy_queue:
            try:
                self._destroy_after_id = self.after(
                    CARD_DESTROY_INTERVAL_MS,
                    self._destroy_next_batch,
                )
            except Exception:
                self._destroy_after_id = None

    def _render_next_batch(self, token: int) -> None:
        if token != self._render_token:
            return
        start = self._render_index
        end = min(start + CARD_RENDER_BATCH_SIZE, self._render_total)
        for index in range(start, end):
            self._build_card(index, self._render_questions[index], self._render_total)
        self._render_index = end
        if end < self._render_total:
            try:
                self._render_after_id = self.after(
                    CARD_RENDER_INTERVAL_MS,
                    lambda current_token=token: self._render_next_batch(current_token),
                )
            except Exception:
                self._render_after_id = None
        else:
            self._render_after_id = None

    def _build_card(self, index: int, question, total: int) -> None:
        is_error = bool(getattr(question, "_error", False))
        border = "#EF4444" if is_error else ("#CBD5E1", "#334155")
        card = ctk.CTkFrame(
            self,
            fg_color=("#FFFFFF", "#172033"),
            border_width=1,
            border_color=border,
            corner_radius=10,
        )
        card.pack(fill="x", padx=2, pady=5)

        header = ctk.CTkFrame(
            card,
            fg_color=("#F1F5F9", "#1E293B"),
            corner_radius=8,
        )
        header.pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkLabel(
            header,
            text=f"Câu {index + 1}",
            font=("Segoe UI", 11, "bold"),
            text_color="#FFFFFF",
            fg_color="#0284C7",
            corner_radius=6,
            width=68,
        ).pack(side="left", padx=(6, 5), pady=6)
        qtype = str(getattr(question, "qtype", "") or "")
        ctk.CTkLabel(
            header,
            text=QTYPE_LABELS.get(qtype, qtype),
            font=("Segoe UI", 10, "bold"),
            text_color="#FFFFFF",
            fg_color=QTYPE_COLORS.get(qtype, "#64748B"),
            corner_radius=6,
            width=95,
        ).pack(side="left", padx=3, pady=6)
        level = str(getattr(question, "level", "") or "")
        ctk.CTkLabel(
            header,
            text=level,
            font=("Segoe UI", 10, "bold"),
            text_color="#FFFFFF",
            fg_color=LEVEL_COLORS.get(level, "#64748B"),
            corner_radius=6,
            width=44,
        ).pack(side="left", padx=3, pady=6)
        ctk.CTkLabel(
            header,
            text=str(getattr(question, "topic", "") or ""),
            text_color="gray",
            font=("Segoe UI", 9, "italic"),
        ).pack(side="left", padx=8, pady=6)
        if callable(self._on_delete):
            ctk.CTkButton(
                header,
                text="✕",
                width=34,
                height=27,
                fg_color=("#EF4444", "#991B1B"),
                hover_color=("#DC2626", "#7F1D1D"),
                command=lambda idx=index: self._on_delete(idx),
            ).pack(side="right", padx=(3, 6), pady=5)
        if callable(self._on_move):
            ctk.CTkButton(
                header,
                text="↓",
                width=34,
                height=27,
                fg_color=("#10B981", "#047857"),
                hover_color=("#059669", "#065F46"),
                state=("normal" if index < total - 1 else "disabled"),
                command=lambda idx=index: self._on_move(idx, 1),
            ).pack(side="right", padx=3, pady=5)
            ctk.CTkButton(
                header,
                text="↑",
                width=34,
                height=27,
                fg_color=("#10B981", "#047857"),
                hover_color=("#059669", "#065F46"),
                state=("normal" if index > 0 else "disabled"),
                command=lambda idx=index: self._on_move(idx, -1),
            ).pack(side="right", padx=3, pady=5)
        if callable(self._on_edit):
            ctk.CTkButton(
                header,
                text="✏️ Sửa",
                width=70,
                height=27,
                command=lambda idx=index: self._on_edit(idx),
            ).pack(side="right", padx=3, pady=5)
        if callable(self._on_regenerate):
            ctk.CTkButton(
                header,
                text="🔄 Tạo lại",
                width=88,
                height=27,
                fg_color=("#3B82F6", "#1D4ED8"),
                hover_color=("#2563EB", "#1E40AF"),
                command=lambda idx=index: self._on_regenerate(idx),
            ).pack(side="right", padx=3, pady=5)
        if callable(self._on_latex):
            ctk.CTkButton(
                header,
                text="👁 LaTeX",
                width=82,
                height=27,
                fg_color=("#8B5CF6", "#6D28D9"),
                hover_color=("#7C3AED", "#5B21B6"),
                command=lambda idx=index: self._on_latex(idx),
            ).pack(side="right", padx=3, pady=5)

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=14, pady=(3, 10))
        ctk.CTkLabel(
            body,
            text=str(getattr(question, "question", "") or "(Không có nội dung)"),
            justify="left",
            anchor="w",
            wraplength=920,
            font=("Segoe UI", 11),
        ).pack(fill="x", pady=(2, 6))

        for label, text, correct in answer_lines(question):
            verdict = ""
            if qtype == "DS":
                verdict = "Đúng" if correct else "Sai"
            prefix = "✓" if correct else " "
            value = f"{label}. {text}" if qtype in ("TN", "DS") else f"{label}: {text}"
            if verdict:
                value = f"{value}  [{verdict}]"
            ctk.CTkLabel(
                body,
                text=f"{prefix}  {value}",
                justify="left",
                anchor="w",
                wraplength=900,
                font=("Segoe UI", 10),
                text_color=("#15803D" if correct else ("#334155", "#CBD5E1")),
            ).pack(fill="x", padx=10, pady=1)

        solution = str(getattr(question, "solution", "") or "").strip()
        if solution:
            solution_box = ctk.CTkFrame(body, fg_color=("#F0FDF4", "#132A22"),
                                        corner_radius=7)
            solution_box.pack(fill="x", pady=(8, 4))
            ctk.CTkLabel(
                solution_box,
                text=f"Lời giải: {solution}",
                justify="left",
                anchor="w",
                wraplength=900,
                font=("Segoe UI", 10),
                text_color=("#166534", "#86EFAC"),
            ).pack(fill="x", padx=10, pady=8)

        blocks = pending_tikz_count(question)
        if blocks:
            ctk.CTkLabel(
                body,
                text=f"⚠ Có {blocks} khối TikZ chưa chuyển bằng menu TikZ.",
                justify="left",
                anchor="w",
                text_color="#D97706",
                font=("Segoe UI", 10, "bold"),
            ).pack(fill="x", pady=(6, 2))

        for image_label, path in image_rows(question):
            self._build_image_row(body, image_label, path)

        if is_error:
            ctk.CTkLabel(
                body,
                text=f"Lỗi sinh câu: {getattr(question, '_error_msg', '')}",
                text_color="#EF4444",
                anchor="w",
                font=("Segoe UI", 10, "bold"),
            ).pack(fill="x", pady=(6, 0))

    def _build_image_row(self, parent, label: str, path: str) -> None:
        row = ctk.CTkFrame(parent, fg_color=("#EFF6FF", "#142438"),
                           corner_radius=7)
        row.pack(fill="x", pady=(5, 0))
        ctk.CTkLabel(
            row,
            text=f"🖼 {label}",
            width=120,
            anchor="w",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", padx=(10, 8), pady=7)
        image_path = Path(path)
        if image_path.exists():
            try:
                source = load_preview_thumbnail(image_path)
                if source is None:
                    raise RuntimeError("thumbnail load failed")
                photo = ctk.CTkImage(light_image=source, dark_image=source,
                                     size=source.size)
                self._images.append(photo)
                ctk.CTkLabel(row, text="", image=photo).pack(
                    side="left", padx=(0, 10), pady=7)
                return
            except Exception:
                pass
        ctk.CTkLabel(
            row,
            text=path,
            text_color="gray",
            anchor="w",
            font=("Consolas", 9),
        ).pack(side="left", fill="x", expand=True, padx=(0, 10), pady=7)
