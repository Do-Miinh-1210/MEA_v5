"""
v5/sidebar.py — Sidebar trái với 8 mục view + collapse submenu.

Cấu trúc:
    🏠 Trang chủ            (1 click → home view)
    ⚙️ Cấu hình ▼           (expand → AI Provider, License)
    ✏️ Tạo đề ▼
    🏛 NHCH ▼
    🔄 Convert ▼
    ✅ Chất lượng ▼
    📊 Theo dõi ▼
    📖 Hướng dẫn
"""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from v5.ui_theme import UI_COLORS


# ─── 8 view + sub-items ─────────────────────────────────────────────────────

SECTIONS: dict[str, dict] = {
    "home": {"label": "🏠  Trang chủ", "items": []},
    "setup": {
        "label": "⚙️  Cấu hình",
        "items": [
            ("setup",      "AI Provider",  "ai_provider"),
            ("setup",      "Môn / Lớp",    "subject"),
            ("setup",      "License",      "license"),
        ],
    },
    "exam_create": {
        "label": "✏️  Tạo đề",
        "items": [
            ("exam_create", "Ma trận đặc tả"),
            ("exam_create", "Smart Prompt",     "smart_prompt"),
            ("exam_create", "Tạo đề nhanh",      "quick_gen"),
        ],
    },
    "nhch": {
        "label": "🏛  Ngân hàng",
        "items": [
            ("nhch", "Duyệt câu hỏi"),
            ("nhch", "Import PDF/Word/Ảnh", "import_pdf"),
            ("nhch", "Đồng bộ Cloud",       "sync_cloud"),
        ],
    },
    "convert": {
        "label": "🔄  Convert",
        "items": [
            ("convert", "Ảnh → Câu hỏi (AI Vision)",  "conv_image"),
            ("convert", "PDF/Word → Câu hỏi",          "conv_pdf"),
            ("convert", "AI Text → Câu hỏi",           "conv_ai_text"),
        ],
    },
    "qc": {
        "label": "✅  Chất lượng",
        "items": [
            ("qc", "QC pipeline 6 tiêu chí", "qc_focus"),
            ("qc", "AI Review & Fix",        "ai_review"),
            ("qc", "TikZ vẽ hình",            "tikz_focus"),
        ],
    },
    "tracking": {
        "label": "📊  Theo dõi",
        "items": [
            ("tracking", "Dashboard",   "track_dashboard"),
            ("tracking", "Lịch sử đề",  "track_history"),
            ("tracking", "AI Usage",    "track_usage"),
        ],
    },
    "omr_grade": {
        "label": "🎲  Trộn đề thi",
        "items": [],
    },
    "guide": {
        "label": "📖  Hướng dẫn",
        "items": [],
    },
}


class Sidebar(ctk.CTkFrame):
    """Sidebar trái 250px với navigation (có thể collapse → 60px)."""

    EXPANDED_W  = 250
    COLLAPSED_W = 60

    def __init__(self, parent, *,
                 on_navigate: Callable[[str], None],
                 on_action: Callable[[str], None] | None = None):
        super().__init__(parent, width=self.EXPANDED_W, corner_radius=0,
                          fg_color=("#FFFFFF", "#1E293B"))
        self.grid_propagate(False)
        self.pack_propagate(False)
        self._on_navigate = on_navigate
        # Action handler cho item dạng 3-tuple (view_id, label, action_key).
        # Khi user click, gọi on_navigate(view_id) trước rồi on_action(action_key).
        self._on_action = on_action
        self._expanded: set[str] = set()       # group_id đang mở
        self._active_key = "home"
        self._section_buttons: dict[str, ctk.CTkButton] = {}
        try:
            from v5 import settings_store
            self._collapsed = bool(
                settings_store.load().get("sidebar_collapsed", False))
        except Exception:
            self._collapsed = False
        self._build()

    def _build(self):
        # Collapse toggle button (☰)
        top = ctk.CTkFrame(self, fg_color="transparent", height=36)
        top.pack(fill="x", pady=(6, 2))
        self._toggle_btn = ctk.CTkButton(
            top, text="☰", width=44, height=28,
            fg_color="transparent",
            text_color=("#374151", "#F1F5F9"),
            hover_color=("#E5E7EB", "#334155"),
            font=("Segoe UI", 16),
            command=self.toggle_collapse)
        self._toggle_btn.pack(side="left", padx=8)

        # Scrollable container (phòng khi sub-items nhiều)
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=("#CBD5E1", "#475569"))
        self._scroll.pack(fill="both", expand=True, padx=0, pady=(2, 8))
        self._render_navigation()

        # Footer
        ctk.CTkFrame(self, height=1, fg_color=("#E5E7EB", "#334155")
                      ).pack(fill="x", side="bottom")
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=8, padx=10)
        try:
            from v5 import __version__ as _v
        except Exception:
            _v = "5.x"
        self._footer_text = f"MEA v{_v}"
        self._footer_label = ctk.CTkLabel(footer, text=self._footer_text, text_color="gray",
                                          font=("Segoe UI", 9))
        self._footer_label.pack(side="left")
        self._apply_width()

    def _render_navigation(self):
        """Rebuild navigation after active, expand, or collapse state changes."""
        for child in self._scroll.winfo_children():
            child.destroy()
        self._section_buttons.clear()
        for key, meta in SECTIONS.items():
            self._render_section(
                self._scroll, key, meta, collapsed=self._collapsed)

    def _button_colors(self, key: str):
        if key == self._active_key:
            return (("#DBEAFE", "#1E3A8A"), ("#1D4ED8", "#FFFFFF"))
        return ("transparent", ("#1F2937", "#F1F5F9"))

    def _render_section(self, parent, key: str, meta: dict,
                         collapsed: bool = False):
        items = meta["items"]
        is_group = bool(items)

        # Collapsed mode: chỉ icon (emoji đầu)
        if collapsed:
            emoji = meta["label"].strip().split()[0] if meta["label"].strip() else "?"
            fg_color, text_color = self._button_colors(key)
            btn = ctk.CTkButton(
                parent, text=emoji, height=40, width=44,
                font=("Segoe UI", 18),
                fg_color=fg_color,
                text_color=text_color,
                hover_color=("#E5E7EB", "#334155"),
                corner_radius=8,
                command=lambda k=key: self._on_main_click(k))
            btn.pack(padx=4, pady=2)
            self._section_buttons[key] = btn
            return

        # Main button row
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=2)

        fg_color, text_color = self._button_colors(key)
        btn = ctk.CTkButton(
            row, text=meta["label"], anchor="w", height=36,
            font=("Segoe UI", 12, "bold"),
            fg_color=fg_color,
            text_color=text_color,
            hover_color=("#E5E7EB", "#334155"),
            corner_radius=8,
            command=lambda k=key: self._on_main_click(k))
        btn.pack(fill="x", expand=True, side="left")
        self._section_buttons[key] = btn

        if is_group:
            is_expanded = key in self._expanded
            chevron = ctk.CTkLabel(
                row, text="▾" if is_expanded else "▸",
                width=20, anchor="e", text_color=UI_COLORS["text_muted"],
                font=("Segoe UI", 10))
            chevron.pack(side="right")

            # Sub-items container
            if is_expanded:
                sub = ctk.CTkFrame(parent, fg_color="transparent")
                sub.pack(fill="x", padx=24, pady=(0, 4))
                for item in items:
                    # item có thể là 2-tuple (view_id, label) hoặc 3-tuple
                    # (view_id, label, action_key). Action chỉ kích hoạt khi
                    # on_action được parent cung cấp.
                    if len(item) == 3:
                        item_key, item_label, action_key = item
                    else:
                        item_key, item_label = item; action_key = None
                    ctk.CTkButton(
                        sub, text=f"  • {item_label}", anchor="w", height=28,
                        font=("Segoe UI", 11),
                        fg_color="transparent",
                        text_color=("#4B5563", "#CBD5E1"),
                        hover_color=("#F3F4F6", "#293548"),
                        corner_radius=6,
                        command=lambda k=item_key, a=action_key:
                            self._on_subitem_click(k, a),
                    ).pack(fill="x", pady=1)

    def _on_main_click(self, key: str):
        """Navigate and toggle only the selected submenu."""
        if not self._collapsed and SECTIONS.get(key, {}).get("items"):
            self._expanded = set() if key in self._expanded else {key}
            self._render_navigation()
        self._on_navigate(key)

    def _on_subitem_click(self, view_key: str, action_key: str | None):
        """Click sub-item: navigate + (optional) trigger action."""
        self._on_navigate(view_key)
        if action_key and callable(self._on_action):
            try:
                self._on_action(action_key)
            except Exception as e:
                print(f"sidebar action {action_key} fail: {e}")

    # ── Collapse toggle ──────────────────────────────────────────────────
    def toggle_collapse(self):
        """Thu nhỏ / mở rộng sidebar."""
        self._collapsed = not self._collapsed
        self._apply_width()
        # Ép parent grid update minsize
        # Rebuild items với label rút gọn (chỉ emoji)
        self._render_navigation()

        # Save state
        try:
            from v5 import settings_store
            settings_store.set_value("sidebar_collapsed", self._collapsed)
        except Exception: pass

    def _apply_width(self) -> None:
        """Force parent grid and inner widgets to the selected sidebar width."""
        new_w = self.COLLAPSED_W if self._collapsed else self.EXPANDED_W
        self.configure(width=new_w)
        self.grid_propagate(False)
        self.pack_propagate(False)
        try:
            self.master.grid_columnconfigure(0, minsize=new_w, weight=0)
        except Exception:
            pass
        if hasattr(self, "_scroll"):
            try:
                self._scroll.configure(width=max(44, new_w - 8))
            except Exception:
                pass
        if hasattr(self, "_footer_label"):
            try:
                self._footer_label.configure(
                    text="" if self._collapsed else getattr(self, "_footer_text", "")
                )
            except Exception:
                pass

    def set_active(self, key: str):
        """Keep the visible navigation state in sync with routed content."""
        if key not in SECTIONS or key == self._active_key:
            return
        self._active_key = key
        self._render_navigation()
