"""
services/perf.py — Performance utilities for MEA v4.
Cung cấp: async UI helpers, debounce, batch update, memory management.
Nguyên tắc: "UI không bao giờ được chờ xử lý"
"""
from __future__ import annotations
import threading
import time
import weakref
from functools import wraps
from typing import Callable, Optional, Any


# ══════════════════════════════════════════════════════════════════════════════
#  THREADED UI HELPER — chạy task nặng ở background, callback về UI thread
# ══════════════════════════════════════════════════════════════════════════════

def run_in_background(
    task: Callable[[], Any],
    on_done: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[Exception], None]] = None,
    tk_widget=None,
) -> threading.Thread:
    """
    Chạy `task` trên background thread.
    Khi xong, gọi `on_done(result)` hoặc `on_error(exc)` trên UI thread
    (qua widget.after(0, ...)) nếu tk_widget được truyền.

    Usage:
        run_in_background(
            task=lambda: heavy_api_call(),
            on_done=lambda result: update_ui(result),
            on_error=lambda e: show_error(e),
            tk_widget=self,  # tkinter widget để schedule callback
        )
    """
    def _worker():
        try:
            result = task()
            if on_done:
                if tk_widget:
                    tk_widget.after(0, lambda r=result: on_done(r))
                else:
                    on_done(result)
        except Exception as e:
            if on_error:
                if tk_widget:
                    tk_widget.after(0, lambda err=e: on_error(err))
                else:
                    on_error(e)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t


# ══════════════════════════════════════════════════════════════════════════════
#  DEBOUNCE — tránh gọi hàm liên tục (vd: search khi gõ)
# ══════════════════════════════════════════════════════════════════════════════

class Debouncer:
    """Debounce function calls. Chỉ gọi hàm sau khi user ngừng trigger `delay` giây."""

    def __init__(self, delay: float = 0.3):
        self._delay = delay
        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()

    def __call__(self, func: Callable, *args, **kwargs) -> None:
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(
                self._delay, func, args=args, kwargs=kwargs
            )
            self._timer.daemon = True
            self._timer.start()

    def cancel(self) -> None:
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None


def debounce(delay: float = 0.3):
    """Decorator: debounce function calls."""
    def decorator(func):
        _debouncer = Debouncer(delay)

        @wraps(func)
        def wrapper(*args, **kwargs):
            _debouncer(func, *args, **kwargs)
        wrapper.cancel = _debouncer.cancel
        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════════
#  BATCH UI UPDATE — gom nhiều update thành 1 lần render
# ══════════════════════════════════════════════════════════════════════════════

class BatchUpdater:
    """
    Gom nhiều UI updates thành 1 lần render.
    Thay vì update_ui() cho mỗi item, gom tất cả rồi flush 1 lần.

    Usage:
        updater = BatchUpdater(widget, interval_ms=50)
        for item in data:
            updater.schedule(lambda i=item: tree.insert('', 'end', values=i))
        updater.flush()  # force flush ngay
    """

    def __init__(self, tk_widget, interval_ms: int = 50):
        self._widget = tk_widget
        self._interval = interval_ms
        self._pending: list[Callable] = []
        self._lock = threading.Lock()
        self._scheduled = False

    def schedule(self, update_fn: Callable) -> None:
        with self._lock:
            self._pending.append(update_fn)
            if not self._scheduled:
                self._scheduled = True
                self._widget.after(self._interval, self._flush)

    def _flush(self) -> None:
        with self._lock:
            batch = self._pending[:]
            self._pending.clear()
            self._scheduled = False
        for fn in batch:
            try:
                fn()
            except Exception:
                pass

    def flush(self) -> None:
        """Force flush all pending updates immediately."""
        self._flush()


# ══════════════════════════════════════════════════════════════════════════════
#  LAZY PROPERTY — chỉ tính khi truy cập lần đầu
# ══════════════════════════════════════════════════════════════════════════════

class lazy_property:
    """Descriptor: tính giá trị lần đầu, cache kết quả."""

    def __init__(self, func):
        self.func = func
        self.attr_name = f"_lazy_{func.__name__}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if not hasattr(obj, self.attr_name):
            setattr(obj, self.attr_name, self.func(obj))
        return getattr(obj, self.attr_name)


# ══════════════════════════════════════════════════════════════════════════════
#  MEMORY TRACKER — theo dõi và giải phóng bộ nhớ
# ══════════════════════════════════════════════════════════════════════════════

class MemoryManager:
    """
    Quản lý bộ nhớ: theo dõi objects lớn, tự cleanup khi cần.
    Dùng weakref để không giữ reference cứng.
    """

    def __init__(self, max_mb: float = 200.0):
        self._max_bytes = int(max_mb * 1024 * 1024)
        self._tracked: dict[str, weakref.ref] = {}
        self._cleanups: list[Callable] = []

    def track(self, name: str, obj: Any) -> None:
        """Track object bằng weakref."""
        try:
            self._tracked[name] = weakref.ref(obj)
        except TypeError:
            pass  # Some objects don't support weakref

    def register_cleanup(self, fn: Callable) -> None:
        """Đăng ký hàm cleanup (gọi khi cần giải phóng RAM)."""
        self._cleanups.append(fn)

    def cleanup(self) -> int:
        """Chạy tất cả cleanup functions. Trả về số cleanups đã chạy."""
        import gc
        count = 0
        for fn in self._cleanups:
            try:
                fn()
                count += 1
            except Exception:
                pass
        # Remove dead weakrefs
        dead = [k for k, ref in self._tracked.items() if ref() is None]
        for k in dead:
            del self._tracked[k]
        gc.collect()
        return count

    def get_usage_mb(self) -> float:
        """Ước lượng RAM usage (MB) — chỉ cho monitoring."""
        import sys
        total = 0
        for name, ref in self._tracked.items():
            obj = ref()
            if obj is not None:
                total += sys.getsizeof(obj)
        return total / (1024 * 1024)


# Global memory manager
_mem_manager = MemoryManager()


def get_memory_manager() -> MemoryManager:
    return _mem_manager


# ══════════════════════════════════════════════════════════════════════════════
#  THROTTLE — giới hạn tần suất gọi hàm
# ══════════════════════════════════════════════════════════════════════════════

def throttle(interval: float = 0.1):
    """Decorator: đảm bảo hàm chỉ được gọi tối đa 1 lần mỗi `interval` giây."""
    def decorator(func):
        last_call = [0.0]
        lock = threading.Lock()

        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.time()
                if now - last_call[0] < interval:
                    return None
                last_call[0] = now
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════════
#  CONNECTION POOL cho SQLite — thread-safe
# ══════════════════════════════════════════════════════════════════════════════

class SQLitePool:
    """
    Thread-safe SQLite connection pool.
    Mỗi thread dùng 1 connection riêng, tái sử dụng qua thread-local storage.
    """

    def __init__(self, db_path: str, max_connections: int = 5):
        self._db_path = db_path
        self._local = threading.local()
        self._lock = threading.Lock()

    def get_connection(self):
        """Lấy connection cho thread hiện tại (tạo mới nếu chưa có)."""
        import sqlite3
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging — nhanh hơn
            conn.execute("PRAGMA synchronous=NORMAL")  # Cân bằng speed/safety
            conn.execute("PRAGMA cache_size=-8000")  # 8MB cache
            conn.execute("PRAGMA temp_store=MEMORY")  # Temp tables in RAM
            self._local.conn = conn
        return self._local.conn

    def close_all(self) -> None:
        """Đóng connection của thread hiện tại."""
        if hasattr(self._local, 'conn') and self._local.conn:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None


# ══════════════════════════════════════════════════════════════════════════════
#  PRELOADER — preload data ở background khi app idle
# ══════════════════════════════════════════════════════════════════════════════

class Preloader:
    """Preload data ở background khi app rảnh."""

    def __init__(self):
        self._tasks: list[Callable] = []
        self._results: dict[str, Any] = {}
        self._lock = threading.Lock()

    def register(self, name: str, loader: Callable) -> None:
        """Đăng ký task cần preload."""
        self._tasks.append((name, loader))

    def start(self) -> None:
        """Bắt đầu preload tất cả tasks ở background."""
        def _run():
            for name, loader in self._tasks:
                try:
                    result = loader()
                    with self._lock:
                        self._results[name] = result
                except Exception:
                    pass

        threading.Thread(target=_run, daemon=True).start()

    def get(self, name: str, default=None) -> Any:
        """Lấy kết quả preload (None nếu chưa xong)."""
        with self._lock:
            return self._results.get(name, default)
