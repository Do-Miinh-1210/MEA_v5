"""Small UI pacing helpers for the V5 CustomTkinter shell.

Tkinter is most responsive when background workers send fewer, coalesced
updates to the main loop. These helpers keep progress labels and lightweight
animations from overwhelming the event queue.
"""
from __future__ import annotations

import threading
import time
from typing import Any, Callable


DEFAULT_UI_FRAME_MS = 80
ANIMATION_INTERVAL_MS = 120
TOAST_FADE_INTERVAL_MS = 35
CARD_RENDER_BATCH_SIZE = 6
CARD_RENDER_INTERVAL_MS = 20
CARD_DESTROY_BATCH_SIZE = 10
CARD_DESTROY_INTERVAL_MS = 12
CARD_THUMBNAIL_CACHE_MAX = 96


class UiThrottle:
    """Coalesce repeated UI updates and run only the latest one per interval."""

    def __init__(self, widget: Any, interval_ms: int = DEFAULT_UI_FRAME_MS):
        self._widget = widget
        self._interval_ms = max(1, int(interval_ms))
        self._last_fire_ms = 0.0
        self._after_id: Any | None = None
        self._pending: tuple[Callable[..., Any], tuple[Any, ...], dict[str, Any]] | None = None
        self._lock = threading.Lock()

    def schedule(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        """Schedule ``func`` on the widget loop, replacing older pending calls."""
        with self._lock:
            self._pending = (func, args, kwargs)
            if self._after_id is not None:
                return
            now_ms = time.monotonic() * 1000
            delay = max(0, int(self._interval_ms - (now_ms - self._last_fire_ms)))
            try:
                self._after_id = self._widget.after(delay, self._flush)
            except Exception:
                self._after_id = None
                self._pending = None

    def cancel(self) -> None:
        """Drop any pending update."""
        with self._lock:
            after_id = self._after_id
            self._after_id = None
            self._pending = None
        if after_id is not None:
            try:
                self._widget.after_cancel(after_id)
            except Exception:
                pass

    def _flush(self) -> None:
        with self._lock:
            pending = self._pending
            self._pending = None
            self._after_id = None
            self._last_fire_ms = time.monotonic() * 1000
        if pending is None:
            return
        func, args, kwargs = pending
        try:
            func(*args, **kwargs)
        except Exception:
            pass
