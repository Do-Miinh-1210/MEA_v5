"""MEA v5 Desktop — CustomTkinter rewrite của v4.

Structure:
    app.py            — Entry point: ModernApp với sidebar + content
    sidebar.py        — Sidebar 8 view + collapse menu
    views/            — 1 file per section (home, setup, exam_create, nhch,
                         convert, qc, tracking, guide)
    services/         — DI container, reuse v4 services

Để chạy:
    python -m v5.app

Để biết thêm: v5/README.md
"""
__version__ = "5.0.0"


# ── Auto-bind MouseWheel cho CTkScrollableFrame ─────────────────────────────
# CTk KHÔNG bind <MouseWheel> mặc định → user phải kéo scrollbar bằng chuột.
# Monkey-patch __init__ để mọi instance (cũ + mới) tự có wheel support.
# Alpha 52b: chặn binding wheel native của CTkScrollableFrame. CTk tự
# bind_all("<MouseWheel>") cho MỖI frame, nên app nhiều panel sẽ gọi hàng chục
# callback trên mỗi notch. V5 chỉ giữ một router toàn cục trong safe_ui.
def _patch_ctk_scroll_wheel():
    try:
        import customtkinter as _ctk
        _Original = _ctk.CTkScrollableFrame
        _orig_init = _Original.__init__
        _orig_bind_all = _Original.bind_all
        _blocked_global_scroll_sequences = {
            "<MouseWheel>",
            "<Button-4>",
            "<Button-5>",
            "<KeyPress-Shift_L>",
            "<KeyPress-Shift_R>",
            "<KeyRelease-Shift_L>",
            "<KeyRelease-Shift_R>",
        }

        def _patched_init(self, *args, **kwargs):
            def _bind_all_without_native_scroll(sequence=None, func=None, add=None):
                if sequence in _blocked_global_scroll_sequences:
                    return None
                return _orig_bind_all(self, sequence, func, add)

            try:
                self.bind_all = _bind_all_without_native_scroll
                _orig_init(self, *args, **kwargs)
            finally:
                try:
                    delattr(self, "bind_all")
                except Exception:
                    pass
            try:
                from v5.safe_ui import enable_mousewheel
                # Defer 1 tick để widget mount xong (canvas có size, root ready)
                self.after(50, lambda: enable_mousewheel(self))
            except Exception:
                pass

        _Original.__init__ = _patched_init
    except Exception as e:
        print(f"patch_ctk_scroll_wheel fail (non-fatal): {e}")


_patch_ctk_scroll_wheel()
