"""
v5/views/guide.py — Hướng dẫn sử dụng thuần CustomTkinter.

Layout 2 cột:
    ┌────────────┬─────────────────────────────────────┐
    │ [Section1] │  Header (màu theo section)          │
    │ [Section2] │                                       │
    │ [Section3] │  Card "Bước 1"                        │
    │ [..]       │    1. ...                             │
    │            │    2. ...                             │
    │            │  Card "Bước 2"                        │
    └────────────┴─────────────────────────────────────┘
"""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from v5 import __version__
from v5.guide_content import GUIDES
from v5.ui_theme import UI_COLORS, darken, tint


NAV_WIDTH = 300
GUIDE_WRAP = 860


class GuideView(ctk.CTkFrame):
    """View Hướng dẫn — sidebar trái + nội dung phải, modular theo section."""

    def __init__(self, parent, *, on_navigate: Callable[[str], None] | None = None):
        super().__init__(parent, fg_color="transparent")
        self._on_navigate = on_navigate
        self._guides = GUIDES
        self._active_idx = 0
        self._nav_buttons: list[ctk.CTkButton] = []
        self._nav_items: list[tuple[ctk.CTkButton, dict]] = []
        self._content_frame: ctk.CTkScrollableFrame | None = None
        self._filter_var = ctk.StringVar(value="")
        self._build()

    def _build(self):
        # ── Header chung ───────────────────────────────────────────
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(self, fg_color=UI_COLORS["guide_header"],
                            corner_radius=12, height=64)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_propagate(False)
        ctk.CTkLabel(
            hdr,
            text=f"📖  Hướng dẫn sử dụng MatrixExamAI v{__version__}",
            text_color=UI_COLORS["text_on_accent"],
            font=("Segoe UI", 17, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=(18, 12), pady=(11, 0))
        ctk.CTkLabel(
            hdr,
            text="Tra cứu theo mục, làm theo từng bước, ưu tiên các thao tác hay dùng.",
            text_color=UI_COLORS["guide_header_subtitle"],
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 10))
        ctk.CTkLabel(
            hdr,
            text="Ctrl+8 mở nhanh",
            text_color=UI_COLORS["text_on_accent"],
            fg_color=("#1D4ED8", "#1E3A8A"),
            corner_radius=16,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=2, rowspan=2, sticky="e", padx=16)

        # Empty state phòng khi resource hướng dẫn bị cấu hình rỗng.
        if not self._guides:
            self._render_empty()
            return

        # ── Body: sidebar trái + content phải ──────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=0, minsize=NAV_WIDTH)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_section_nav(body)
        self._build_content(body)

        # Hiện section đầu
        self.after(50, lambda: self._show_section(0))

    def _build_section_nav(self, parent):
        """Sidebar trái với danh sách section."""
        nav = ctk.CTkScrollableFrame(
            parent,
            width=NAV_WIDTH,
            corner_radius=12,
            fg_color=UI_COLORS["guide_nav"],
            scrollbar_button_color=UI_COLORS["border_strong"],
        )
        nav.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            nav,
            text="📑  Mục lục",
            anchor="w",
            text_color=UI_COLORS["text_secondary"],
            font=("Segoe UI", 11, "bold"),
        ).pack(fill="x", padx=10, pady=(8, 6))

        search = ctk.CTkEntry(
            nav,
            textvariable=self._filter_var,
            placeholder_text="Tìm mục hướng dẫn...",
            height=32,
        )
        search.pack(fill="x", padx=8, pady=(0, 8))
        self._filter_var.trace_add("write", lambda *_: self._filter_sections())

        for i, g in enumerate(self._guides):
            btn = ctk.CTkButton(
                nav,
                text=f"  {g.get('icon', '')}  {g['tab']}".strip(),
                anchor="w", height=38,
                font=("Segoe UI", 11),
                fg_color="transparent",
                text_color=UI_COLORS["text_secondary"],
                hover_color=("#E0F2FE", "#1E3A8A"),
                corner_radius=8,
                command=lambda idx=i: self._show_section(idx),
            )
            btn.pack(fill="x", padx=6, pady=2)
            self._nav_buttons.append(btn)
            self._nav_items.append((btn, g))

    def _build_content(self, parent):
        """Khung nội dung bên phải (scrollable)."""
        self._content_frame = ctk.CTkScrollableFrame(
            parent, corner_radius=12,
            fg_color=UI_COLORS["guide_content"],
            scrollbar_button_color=UI_COLORS["border_strong"])
        self._content_frame.grid(row=0, column=1, sticky="nsew")

    def _render_empty(self):
        """Khi không có dữ liệu GUIDES."""
        empty = ctk.CTkFrame(self, fg_color="transparent")
        empty.grid(row=1, column=0, sticky="nsew")
        ctk.CTkLabel(empty,
                      text="📭  Không tải được nội dung hướng dẫn",
                      font=("Segoe UI", 16, "bold"),
                      text_color=UI_COLORS["text_secondary"]).pack(pady=(60, 8))
        ctk.CTkLabel(empty,
                      text="Vui lòng kiểm tra resource nội dung hướng dẫn của V5.",
                      font=("Segoe UI", 11),
                      text_color=UI_COLORS["text_muted"]).pack()

    def _filter_sections(self) -> None:
        query = self._filter_var.get().strip().lower()
        for btn, guide in self._nav_items:
            haystack = f"{guide.get('tab', '')} {guide.get('icon', '')}".lower()
            if not query or query in haystack:
                if not btn.winfo_ismapped():
                    btn.pack(fill="x", padx=6, pady=2)
            else:
                btn.pack_forget()

    def _content_wraplength(self) -> int:
        width = self.winfo_width() or GUIDE_WRAP
        return min(GUIDE_WRAP, max(360, width - NAV_WIDTH - 120))

    @staticmethod
    def _clean_step_text(step: str) -> str:
        return (step or "").strip().lstrip("-•").strip()

    # ── Render nội dung 1 section ──────────────────────────────────
    def _show_section(self, idx: int):
        if not (0 <= idx < len(self._guides)):
            return
        self._active_idx = idx
        g = self._guides[idx]
        color = g.get("color", UI_COLORS["primary"])

        # Highlight nút active ở sidebar
        for i, btn in enumerate(self._nav_buttons):
            if i == idx:
                btn.configure(
                    fg_color=color,
                    hover_color=darken(color),
                    text_color=UI_COLORS["text_on_accent"],
                    font=("Segoe UI", 11, "bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    hover_color=("#E0F2FE", "#1E3A8A"),
                    text_color=UI_COLORS["text_secondary"],
                    font=("Segoe UI", 11),
                )

        if self._content_frame is None:
            return

        # Xoá nội dung cũ
        for w in self._content_frame.winfo_children():
            w.destroy()

        # ── Tiêu đề section (banner màu) ──────────────────────────
        title_bar = ctk.CTkFrame(
            self._content_frame,
            fg_color=color,
            corner_radius=12,
            height=74,
        )
        title_bar.pack(fill="x", padx=8, pady=(6, 10))
        title_bar.grid_columnconfigure(1, weight=1)
        title_bar.grid_propagate(False)
        icon = g.get("icon", "")
        title_text = (f"  {icon}  Hướng dẫn: {g['tab']}"
                       if icon else f"  Hướng dẫn: {g['tab']}")
        ctk.CTkLabel(
            title_bar,
            text=title_text,
            text_color=UI_COLORS["text_on_accent"],
            font=("Segoe UI", 17, "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(12, 0))
        ctk.CTkLabel(
            title_bar,
            text="Các bước được tách theo nhóm để dễ làm theo và dễ quay lại sửa.",
            text_color=("#E0F2FE", "#DBEAFE"),
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=18, pady=(0, 12))

        self._render_quick_start(g, color)

        # ── Mỗi nhóm "bước" → 1 card ──────────────────────────────
        for step_title, steps in g.get("steps", []):
            self._render_step_card(step_title, steps, color)

        # Đáy: spacer
        ctk.CTkFrame(self._content_frame, fg_color="transparent",
                      height=20).pack()

        # Reset scroll lên đầu
        try:
            self._content_frame._parent_canvas.yview_moveto(0)
        except Exception:
            pass

    def _render_quick_start(self, guide: dict, color: str) -> None:
        steps = guide.get("steps", [])
        first_steps = steps[0][1][:3] if steps else []
        if not first_steps:
            return
        box = ctk.CTkFrame(
            self._content_frame,
            fg_color=(tint(color, 0.88), "#0B253A"),
            corner_radius=12,
            border_width=1,
            border_color=(tint(color, 0.72), "#1E3A8A"),
        )
        box.pack(fill="x", padx=8, pady=(0, 10))
        ctk.CTkLabel(
            box,
            text="Bắt đầu nhanh",
            text_color=color,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 4))
        for i, step in enumerate(first_steps, 1):
            row = ctk.CTkFrame(box, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=2)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                row,
                text=str(i),
                width=24,
                height=24,
                fg_color=color,
                text_color=UI_COLORS["text_on_accent"],
                corner_radius=12,
                font=("Segoe UI", 10, "bold"),
            ).grid(row=0, column=0, sticky="n", padx=(0, 8))
            ctk.CTkLabel(
                row,
                text=self._clean_step_text(step),
                text_color=UI_COLORS["text_secondary"],
                font=("Segoe UI", 10),
                anchor="w",
                justify="left",
                wraplength=self._content_wraplength(),
            ).grid(row=0, column=1, sticky="ew", pady=1)
        ctk.CTkFrame(box, fg_color="transparent", height=8).pack()

    def _render_step_card(self, title: str, steps: list[str], color: str):
        """Card cho 1 nhóm bước (vd 'Chọn nhà cung cấp AI')."""
        card = ctk.CTkFrame(self._content_frame,
                              fg_color=UI_COLORS["surface"],
                              corner_radius=12,
                              border_width=1,
                              border_color=UI_COLORS["border"])
        card.pack(fill="x", padx=8, pady=6)

        # Header card
        hdr = ctk.CTkFrame(card, fg_color=UI_COLORS["surface_alt"],
                            corner_radius=10, height=38)
        hdr.pack(fill="x", padx=0, pady=0)
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text=f"  {title}",
                      text_color=color,
                      font=("Segoe UI", 12, "bold"),
                      anchor="w").pack(anchor="w", padx=12, pady=8)

        # Mỗi step → 1 row "n. <text>" hoặc sub-item indent
        for n, step in enumerate(steps, 1):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            row.grid_columnconfigure(1, weight=1)
            # Sub-item (2 spaces indent) → không đánh số
            if step.startswith("  "):
                ctk.CTkLabel(row, text="•", width=28,
                              text_color=color,
                              fg_color="transparent",
                              font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="ne", padx=(0, 8))
                ctk.CTkLabel(row, text=self._clean_step_text(step),
                              text_color=UI_COLORS["text_muted"],
                              font=("Segoe UI", 10),
                              anchor="w", justify="left",
                              wraplength=self._content_wraplength()
                              ).grid(row=0, column=1, sticky="ew", pady=1)
            else:
                ctk.CTkLabel(row, text=f"{n}.", width=28,
                              text_color=color,
                              font=("Segoe UI", 11, "bold"),
                              anchor="ne"
                              ).grid(row=0, column=0, sticky="ne", padx=(0, 8))
                ctk.CTkLabel(row, text=self._clean_step_text(step),
                              text_color=UI_COLORS["text_secondary"],
                              font=("Segoe UI", 11),
                              anchor="w", justify="left",
                              wraplength=self._content_wraplength()
                              ).grid(row=0, column=1, sticky="ew", pady=1)
        # Spacer dưới card
        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()
