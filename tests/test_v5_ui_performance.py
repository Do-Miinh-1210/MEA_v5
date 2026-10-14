"""Guard rails for V5 UI frame pacing and lightweight animations."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from v5.ui_perf import (
    ANIMATION_INTERVAL_MS,
    CARD_DESTROY_BATCH_SIZE,
    CARD_DESTROY_INTERVAL_MS,
    CARD_RENDER_BATCH_SIZE,
    CARD_RENDER_INTERVAL_MS,
    CARD_THUMBNAIL_CACHE_MAX,
    TOAST_FADE_INTERVAL_MS,
    UiThrottle,
)


ROOT = Path(__file__).resolve().parents[1]


class FakeWidget:
    def __init__(self):
        self._next_id = 0
        self.calls = []
        self.cancelled = set()

    def after(self, delay_ms, callback):
        self._next_id += 1
        after_id = f"after-{self._next_id}"
        self.calls.append((after_id, delay_ms, callback))
        return after_id

    def after_cancel(self, after_id):
        self.cancelled.add(after_id)

    def run_all(self):
        calls = list(self.calls)
        self.calls.clear()
        for after_id, _delay, callback in calls:
            if after_id not in self.cancelled:
                callback()


def test_ui_throttle_coalesces_to_latest_pending_call():
    widget = FakeWidget()
    throttle = UiThrottle(widget, 80)
    seen = []

    throttle.schedule(seen.append, "first")
    throttle.schedule(seen.append, "latest")

    assert len(widget.calls) == 1
    widget.run_all()
    assert seen == ["latest"]


def test_ui_throttle_cancel_drops_pending_call():
    widget = FakeWidget()
    throttle = UiThrottle(widget, 80)
    seen = []

    throttle.schedule(seen.append, "pending")
    throttle.cancel()
    widget.run_all()

    assert seen == []
    assert widget.cancelled == {"after-1"}


def test_spinner_and_toast_use_lighter_animation_cadence():
    spinner_source = (ROOT / "v5" / "spinner.py").read_text(encoding="utf-8")
    toast_source = (ROOT / "v5" / "toast.py").read_text(encoding="utf-8")
    toast_reposition = toast_source.split("def _reposition", 1)[1].split("def _fade", 1)[0]

    assert ANIMATION_INTERVAL_MS >= 100
    assert TOAST_FADE_INTERVAL_MS >= 30
    assert "ANIMATION_INTERVAL_MS" in spinner_source
    assert "after(80" not in spinner_source
    assert "TOAST_FADE_INTERVAL_MS" in toast_source
    assert "after(15" not in toast_source
    assert "update_idletasks" not in toast_reposition
    assert "WIDTH  = 288" in toast_source
    assert "HEIGHT = 44" in toast_source
    assert "winfo_reqwidth" not in toast_reposition
    assert "winfo_reqheight" not in toast_reposition


def test_exam_create_progress_updates_are_throttled():
    source = (ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")

    assert "from v5.ui_perf import UiThrottle" in source
    assert "self._generate_progress_throttle = UiThrottle(self, 80)" in source
    assert "throttle.schedule(self._update_generate_progress" in source
    assert "def _finish_generate_worker" in source
    assert "progress_throttle.schedule(" in source
    assert "status_throttle = UiThrottle(self, 120)" in source
    assert "dlg.update()" not in source
    assert "self.after(0, lambda d=done, t=total, m=msg" not in source


def test_qc_rows_and_progress_are_batched():
    source = (ROOT / "v5" / "views" / "qc.py").read_text(encoding="utf-8")
    add_row = source.split("def _add_qc_row", 1)[1].split("def _update_qc_stats", 1)[0]

    assert "from v5.ui_perf import UiThrottle" in source
    assert "progress_throttle.schedule(self._update_qc_progress" in source
    assert "row_throttle.schedule(_flush_rows)" in source
    assert "def _configure_qc_tree_tags" in source
    assert "def _update_qc_progress" in source
    assert "tag_configure" not in add_row


def test_question_cards_render_incrementally_in_batches():
    from v5.question_cards import card_render_ranges

    source = (ROOT / "v5" / "question_cards.py").read_text(encoding="utf-8")
    set_questions = source.split("def set_questions", 1)[1].split("def _cancel_pending_render", 1)[0]

    assert CARD_RENDER_BATCH_SIZE == 6
    assert CARD_RENDER_INTERVAL_MS <= 30
    assert card_render_ranges(14, 6) == [(0, 6), (6, 12), (12, 14)]
    assert "def _render_next_batch" in source
    assert "def _cancel_pending_render" in source
    assert "CARD_RENDER_INTERVAL_MS" in source
    assert "CARD_DESTROY_BATCH_SIZE" in source
    assert "CARD_DESTROY_INTERVAL_MS" in source
    assert "def _schedule_destroy_children" in source
    assert "def _destroy_next_batch" in source
    assert "self._schedule_destroy_children(self.winfo_children())" in set_questions
    assert "after_cancel" in source
    assert "for index, question in enumerate(questions)" not in set_questions
    assert "for child in self.winfo_children():\n            child.destroy()" not in set_questions


def test_question_card_thumbnail_cache_reuses_and_bounds_images(tmp_path):
    from v5.question_cards import (
        _THUMBNAIL_CACHE,
        clear_preview_thumbnail_cache,
        load_preview_thumbnail,
    )

    clear_preview_thumbnail_cache()
    image_path = tmp_path / "figure.png"
    Image.new("RGB", (640, 360), "white").save(image_path)

    first = load_preview_thumbnail(image_path)
    second = load_preview_thumbnail(image_path)

    assert first is second
    assert first.size[0] <= 260
    assert first.size[1] <= 150
    assert CARD_THUMBNAIL_CACHE_MAX >= 32

    for index in range(CARD_THUMBNAIL_CACHE_MAX + 3):
        path = tmp_path / f"figure_{index}.png"
        Image.new("RGB", (12, 12), "white").save(path)
        load_preview_thumbnail(path, size=(8, 8))

    assert len(_THUMBNAIL_CACHE) <= CARD_THUMBNAIL_CACHE_MAX
    clear_preview_thumbnail_cache()
    assert len(_THUMBNAIL_CACHE) == 0


def test_import_matrix_and_variant_progress_are_throttled():
    import_source = (ROOT / "v5" / "import_wizard.py").read_text(encoding="utf-8")
    matrix_source = (ROOT / "v5" / "ai_gen_matrix.py").read_text(encoding="utf-8")
    variant_source = (ROOT / "v5" / "variant_dialog.py").read_text(encoding="utf-8")

    assert "from v5.ui_perf import UiThrottle" in import_source
    assert "progress_throttle = UiThrottle(self, 80)" in import_source
    assert "progress_throttle.schedule(self._set_progress" in import_source
    assert "self.after(0, lambda: self._set_progress" not in import_source

    assert "from v5.ui_perf import UiThrottle" in matrix_source
    assert "progress_throttle.schedule(self._set_progress_message" in matrix_source
    assert "def _set_progress_message" in matrix_source
    assert "try: self.after(0, _u)" not in matrix_source

    assert "from v5.ui_perf import UiThrottle" in variant_source
    assert "progress_throttle.schedule(self._update_ai_variant_progress" in variant_source
    assert "def _update_ai_variant_progress" in variant_source
    assert "self.after(0, lambda d=done, t=total" not in variant_source


def test_import_wizard_keeps_footer_visible_and_preview_flexible():
    source = (ROOT / "v5" / "import_wizard.py").read_text(encoding="utf-8")
    build = source.split("def _build(self):", 1)[1].split("def _card", 1)[0]

    assert "body = ctk.CTkScrollableFrame" not in build
    assert 'self._footer.pack(fill="x", side="bottom")' in build
    assert build.index("self._footer.pack") < build.index("body = ctk.CTkFrame")
    assert "opt_grid = ctk.CTkFrame(o_card" in build
    assert "opt_grid.grid_columnconfigure(1, weight=1)" in build
    assert "opt_grid.grid_columnconfigure(3, weight=1)" in build
    assert 'p_card = self._card(body,' in build
    assert 'expand=True)' in build
    assert "preview_minwidths = {" in build
    assert "minwidth=preview_minwidths[c]" in build
    assert 'stretch=(c == "preview")' in build
    assert "save_row = ctk.CTkFrame(self._footer" in build
    assert "save_row.grid_columnconfigure(2, weight=1)" in build
    assert "self._save_btn.grid(row=0, column=0" in build
    assert "self._push_btn.grid(row=0, column=1" in build
    assert "def _card(self, parent, title, *, expand: bool = False)" in source
    assert 'outer.pack(fill=("both" if expand else "x"), expand=expand' in source


def test_mousewheel_router_is_global_coalesced_and_idempotent():
    source = (ROOT / "v5" / "safe_ui.py").read_text(encoding="utf-8")
    init_source = (ROOT / "v5" / "__init__.py").read_text(encoding="utf-8")

    assert "_SCROLL_REGISTRY" in source
    assert "def _route_global_mousewheel" in source
    assert "def _queue_yview_scroll" in source
    assert "_SCROLLABLE_UNITS_PER_NOTCH = 24" in source
    assert "_TREE_UNITS_PER_NOTCH = 3" in source
    assert "_WHEEL_FLUSH_MS = 12" in source
    assert "target.after(_WHEEL_FLUSH_MS, _flush)" in source
    assert "target.after_idle(_flush)" not in source
    assert "root.bind_all(\"<MouseWheel>\", _route_global_mousewheel, add=\"+\")" in source
    assert "scrollable_frame.bind(\"<Destroy>\", _cleanup, add=\"+\")" in source
    assert "root.bindtags" not in source
    assert "bind_class(bind_tag" not in source
    assert "_queue_yview_scroll(tree, amount)" in source
    assert "_blocked_global_scroll_sequences" in init_source
    assert "_bind_all_without_native_scroll" in init_source
