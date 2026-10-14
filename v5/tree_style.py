"""
v5/tree_style.py — Style ttk.Treeview cho khớp theme v5 (đẹp + dark mode).

ttk.Treeview mặc định trông thô (nền trắng, header xám). Helper này áp style
'MEA.Treeview': header xanh đậm bo, hàng cao 30px, zebra stripes, hàng chọn
màu accent. Tự đổi màu theo Light/Dark.

Usage:
    from v5.tree_style import style_treeview, zebra_tag
    style_treeview(tree)                       # gọi sau khi tạo Treeview
    tree.insert("", "end", values=..., tags=(zebra_tag(i),))   # khi thêm row
"""
from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk

_PALETTE = {
    True: {   # dark
        "bg": "#162033", "fg": "#E6ECF7", "field": "#162033",
        "sel": "#2956B8", "sel_fg": "#FFFFFF",
        "head_bg": "#1E2A40", "head_fg": "#93C5FD", "head_active": "#243352",
        "odd": "#1A2740", "even": "#162033",
    },
    False: {  # light
        "bg": "#FFFFFF", "fg": "#1F2937", "field": "#FFFFFF",
        "sel": "#3A6FD8", "sel_fg": "#FFFFFF",
        "head_bg": "#1F497D", "head_fg": "#FFFFFF", "head_active": "#163D6B",
        "odd": "#F1F5F9", "even": "#FFFFFF",
    },
}


def _is_dark() -> bool:
    try:
        return ctk.get_appearance_mode().lower() == "dark"
    except Exception:
        return False


def style_treeview(tree: ttk.Treeview, *, row_height: int = 30,
                    font_size: int = 11) -> None:
    """Áp style đẹp 'MEA.Treeview' cho 1 Treeview + cấu hình zebra tags."""
    dark = _is_dark()
    p = _PALETTE[dark]
    style = ttk.Style()
    try: style.theme_use("clam")     # clam cho phép tô màu đầy đủ
    except Exception: pass

    style.configure(
        "MEA.Treeview",
        background=p["bg"], foreground=p["fg"], fieldbackground=p["field"],
        rowheight=row_height, borderwidth=0, relief="flat",
        font=("Segoe UI", font_size))
    style.configure(
        "MEA.Treeview.Heading",
        background=p["head_bg"], foreground=p["head_fg"],
        font=("Segoe UI", font_size, "bold"),
        relief="flat", padding=(8, 7), borderwidth=0)
    style.map(
        "MEA.Treeview",
        background=[("selected", p["sel"])],
        foreground=[("selected", p["sel_fg"])])
    style.map(
        "MEA.Treeview.Heading",
        background=[("active", p["head_active"])],
        foreground=[("active", p["head_fg"])])

    try:
        tree.configure(style="MEA.Treeview")
        tree.tag_configure("oddrow", background=p["odd"], foreground=p["fg"])
        tree.tag_configure("evenrow", background=p["even"], foreground=p["fg"])
        # tag cho hàng lỗi (QC) — đỏ nhạt
        tree.tag_configure("rowfail",
                            background=("#FEE2E2" if not dark else "#3F1D1D"),
                            foreground=("#7F1D1D" if not dark else "#FCA5A5"))
        tree.tag_configure("rowok",
                            foreground=("#065F46" if not dark else "#6EE7B7"))
    except Exception:
        pass

    # Alpha 23b: bind MouseWheel cho cuộn mượt (idempotent)
    try:
        from v5.safe_ui import enable_treeview_mousewheel
        enable_treeview_mousewheel(tree)
    except Exception: pass


def zebra_tag(index: int) -> str:
    """Trả 'oddrow'/'evenrow' theo chỉ số hàng (cho sọc xen kẽ)."""
    return "evenrow" if index % 2 == 0 else "oddrow"
