"""
v5/safe_ui.py — Helper decorator chống race condition khi widget bị destroy.

Vấn đề: Pattern phổ biến trong các view CTk:

    def _refresh_data(self):
        data = expensive_fetch()        # background thread
        self.after(0, lambda: self._render(data))

Khi user navigate sang view khác, parent.destroy() chạy → self bị huỷ.
Background thread vẫn tiếp tục, gọi self.after(0, …). Khi callback fire,
self._render() truy cập widget đã chết → TclError "invalid command name".

Giải pháp: dùng decorator @safe_ui_callback bọc các _render/_update methods.
Trước khi chạy thân hàm, kiểm winfo_exists() và bắt TclError.
"""
from __future__ import annotations

import functools
import tkinter as tk


_SCROLL_REGISTRY: dict[str, tuple[object, object, int]] = {}
_GLOBAL_WHEEL_BOUND = False
_NATIVE_SCROLL_CLASSES = {"Text", "Listbox", "Treeview"}
_SCROLLABLE_UNITS_PER_NOTCH = 24
_TREE_UNITS_PER_NOTCH = 3
_WHEEL_FLUSH_MS = 12


def safe_ui_callback(fn):
    """Decorator: nếu widget self đã destroy → bỏ qua thân hàm.

    Áp dụng cho methods của Frame/Toplevel mà có thể chạy async từ thread.
    """
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            if not self.winfo_exists():
                return None
        except (tk.TclError, AttributeError):
            return None
        try:
            return fn(self, *args, **kwargs)
        except tk.TclError as e:
            # Widget destroyed giữa chừng — bỏ qua
            msg = str(e).lower()
            if "invalid command name" in msg or "application has been destroyed" in msg:
                return None
            raise
        except AttributeError:
            # Widget attr đã bị clear khi destroy
            return None
    return wrapper


def safe_after(widget, ms: int, callback):
    """Wrapper for widget.after() — skip if widget destroyed by then."""
    try:
        if not widget.winfo_exists(): return None
    except Exception: return None

    def _wrapped():
        try:
            if not widget.winfo_exists(): return
            callback()
        except tk.TclError as e:
            msg = str(e).lower()
            if "invalid command name" not in msg \
                and "application has been destroyed" not in msg:
                raise
        except AttributeError:
            pass

    try:
        return widget.after(ms, _wrapped)
    except Exception: return None


def _is_alive(widget) -> bool:
    try:
        return bool(widget.winfo_exists())
    except Exception:
        return False


def _wheel_amount(event, units_per_notch: int) -> float:
    num = getattr(event, "num", None)
    if num == 4:
        return -float(units_per_notch)
    if num == 5:
        return float(units_per_notch)
    delta = float(getattr(event, "delta", 0) or 0)
    if delta == 0:
        return 0.0
    return -float(units_per_notch) * (delta / 120.0)


def _queue_yview_scroll(target, amount: float) -> None:
    if not _is_alive(target) or amount == 0:
        return
    try:
        target._v5_wheel_amount = float(getattr(target, "_v5_wheel_amount", 0.0)) + amount
        if getattr(target, "_v5_wheel_pending", False):
            return
        target._v5_wheel_pending = True
    except Exception:
        return

    def _flush():
        try:
            target._v5_wheel_pending = False
            amount_now = float(getattr(target, "_v5_wheel_amount", 0.0))
            whole_units = int(amount_now)
            if whole_units == 0 and abs(amount_now) >= 0.35:
                whole_units = 1 if amount_now > 0 else -1
            if whole_units == 0:
                return
            target._v5_wheel_amount = amount_now - whole_units
            target.yview_scroll(whole_units, "units")
        except Exception:
            pass

    try:
        target._v5_wheel_after_id = target.after(_WHEEL_FLUSH_MS, _flush)
    except Exception:
        try:
            target._v5_wheel_pending = False
        except Exception:
            pass


def _find_scroll_target(widget):
    current = widget
    while current is not None:
        try:
            entry = _SCROLL_REGISTRY.get(str(current))
            if entry:
                frame, canvas, units_per_notch = entry
                if _is_alive(frame) and _is_alive(canvas):
                    return canvas, units_per_notch
            parent_name = current.winfo_parent()
            if not parent_name:
                break
            current = current.nametowidget(parent_name)
        except Exception:
            break
    return None


def _route_global_mousewheel(event):
    widget = getattr(event, "widget", None)
    if widget is None:
        return None
    if int(getattr(event, "state", 0) or 0) & 0x0004:
        return None
    try:
        if widget.winfo_class() in _NATIVE_SCROLL_CLASSES and str(widget) not in _SCROLL_REGISTRY:
            return None
    except Exception:
        pass
    found = _find_scroll_target(widget)
    if not found:
        return None
    target, units_per_notch = found
    _queue_yview_scroll(target, _wheel_amount(event, units_per_notch))
    return "break"


def _install_global_wheel_router(widget) -> None:
    global _GLOBAL_WHEEL_BOUND
    if _GLOBAL_WHEEL_BOUND:
        return
    try:
        root = widget.winfo_toplevel()
        root.bind_all("<MouseWheel>", _route_global_mousewheel, add="+")
        root.bind_all("<Button-4>", _route_global_mousewheel, add="+")
        root.bind_all("<Button-5>", _route_global_mousewheel, add="+")
        _GLOBAL_WHEEL_BOUND = True
    except Exception:
        pass


def enable_mousewheel(scrollable_frame, *, units_per_notch: int = _SCROLLABLE_UNITS_PER_NOTCH):
    """Bind MouseWheel cho CTkScrollableFrame — vì CTk KHÔNG bind sẵn.

    Alpha 52: dùng một wheel router toàn cục, tra ancestor của widget đang
    nhận event để tìm CTkScrollableFrame tương ứng. Mỗi wheel burst được gom
    theo timer ngắn trước khi gọi yview_scroll, tránh khựng do nhiều callback.

    Cách dùng:
        scroll = ctk.CTkScrollableFrame(parent)
        enable_mousewheel(scroll)
    """
    try:
        canvas = scrollable_frame._parent_canvas
    except Exception:
        return

    # Idempotent — đã bind rồi thì skip
    if getattr(scrollable_frame, "_v5_wheel_bound", False):
        return
    scrollable_frame._v5_wheel_bound = True

    _SCROLL_REGISTRY[str(scrollable_frame)] = (scrollable_frame, canvas, units_per_notch)
    _SCROLL_REGISTRY[str(canvas)] = (scrollable_frame, canvas, units_per_notch)
    _install_global_wheel_router(scrollable_frame)

    def _cleanup(_event=None):
        _SCROLL_REGISTRY.pop(str(scrollable_frame), None)
        _SCROLL_REGISTRY.pop(str(canvas), None)

    try:
        scrollable_frame.bind("<Destroy>", _cleanup, add="+")
    except Exception: pass


def enable_treeview_mousewheel(tree, *, units_per_notch: int = _TREE_UNITS_PER_NOTCH):
    """Bind MouseWheel cho ttk.Treeview — idempotent.

    Tk mặc định cuộn 1 unit/wheel notch (rất chậm). Helper này cho 2 unit
    + bind Linux Button-4/-5. Gọi nhiều lần không tạo duplicate.
    """
    if getattr(tree, "_v5_wheel_bound", False):
        return
    tree._v5_wheel_bound = True

    def _on_wheel(event):
        amount = _wheel_amount(event, units_per_notch)
        _queue_yview_scroll(tree, amount)
        return "break"

    try:
        tree.bind("<MouseWheel>", _on_wheel, add="+")
        tree.bind("<Button-4>", _on_wheel, add="+")
        tree.bind("<Button-5>", _on_wheel, add="+")
    except Exception: pass
