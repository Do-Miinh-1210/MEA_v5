"""
v5/views/home.py — Trang chủ với cards nhanh + stats.
"""
from __future__ import annotations

import threading
from typing import Callable

import customtkinter as ctk

from v5.ui_theme import UI_COLORS, darken as theme_darken


class HomeView(ctk.CTkFrame):
    """Trang chủ: welcome + 4 cards quick-action + stats nhanh."""

    def __init__(self, parent, *, on_navigate: Callable[[str], None]):
        super().__init__(parent, fg_color="transparent")
        self._on_navigate = on_navigate
        self._stat_value_lbls: dict[str, ctk.CTkLabel] = {}
        self._build()
        # Load stats thật (async, không chặn render)
        threading.Thread(target=self._load_stats, daemon=True).start()

    def _build(self):
        # ── Welcome ────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="👋  Xin chào, Giáo viên!",
            font=("Segoe UI", 26, "bold"),
        ).pack(anchor="w", pady=(8, 4))

        self._subtitle_lbl = ctk.CTkLabel(
            self,
            text="MatrixExam AI v5 — UI hiện đại hơn, gọn hơn, tập trung tạo đề và xử lý tài liệu.",
            font=("Segoe UI", 12),
            text_color=UI_COLORS["text_secondary"],
        )
        self._subtitle_lbl.pack(anchor="w", pady=(0, 12))

        # ── Banner cảnh báo chưa cấu hình AI (chỉ hiện nếu thiếu key) ──
        self._setup_banner = ctk.CTkFrame(
            self, fg_color=UI_COLORS["warn_bg"], corner_radius=8)
        # pack có điều kiện trong _check_setup_banner()
        ctk.CTkLabel(self._setup_banner,
                      text="⚠  Chưa cấu hình AI provider — Tạo đề/QC cần API key",
                      font=("Segoe UI", 11, "bold"),
                      text_color=UI_COLORS["warn_text"]
                      ).pack(side="left", padx=12, pady=8)
        ctk.CTkButton(self._setup_banner, text="⚙ Thiết lập ngay", width=140,
                        fg_color=("#F59E0B", "#B45309"),
                        hover_color=("#D97706", "#92400E"),
                        command=lambda: self._on_navigate("setup")
                        ).pack(side="right", padx=12, pady=6)

        # ── Quick action cards (4 cột) ───────────────────────────
        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", pady=(0, 24))
        for i in range(4):
            cards_row.grid_columnconfigure(i, weight=1, uniform="cards")

        cards = [
            ("✏️", "Tạo đề bằng AI",
             "Sinh đề theo ma trận đặc tả với 5 AI provider.",
             "exam_create", "#3B82F6"),
            ("📄", "Import PDF/Word/Ảnh",
             "Upload đề cũ → AI Vision OCR → NHCH.",
             "nhch", "#A78BFA"),
            ("✅", "QC chất lượng",
             "Solver 1+2 → Critic → Math → Score 0-10.",
             "qc", "#10B981"),
            ("🔄", "Convert tài liệu",
             "PDF/Word/Ảnh/Text → câu hỏi để xuất Word hoặc lưu NHCH.",
             "convert", "#F59E0B"),
        ]
        for i, (emoji, title, desc, view_id, color) in enumerate(cards):
            self._render_card(cards_row, emoji, title, desc, view_id, color, i)

        # ── Recent activity / stats loaded asynchronously ─────────
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 16))
        for i in range(3):
            stats_row.grid_columnconfigure(i, weight=1, uniform="stats")

        stats = [
            ("session", "📋 Đề gần đây", "—", "phiên đã lưu"),
            ("nhch",    "📚 Câu trong NHCH", "—", "tổng cộng"),
            ("ai",      "🤖 AI calls", "—", "hôm nay"),
        ]
        for i, (key, label, value, sub) in enumerate(stats):
            self._render_stat(stats_row, key, label, value, sub, i)

        # ── Footer tip ─────────────────────────────────────────────
        tip = ctk.CTkFrame(self, fg_color=UI_COLORS["warn_bg"],
                              corner_radius=8)
        tip.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(tip,
                      text="💡 Mẹo: Nhấn Ctrl+T để mở Quick Switcher tìm nhanh. "
                           "Ctrl+Shift+P để Smart Prompt tạo đề từ mô tả. "
                           "Ctrl+, để mở Tuỳ chọn.",
                      text_color=UI_COLORS["warn_text"],
                      font=("Segoe UI", 10), anchor="w", justify="left",
                      ).pack(anchor="w", padx=12, pady=10)

    def _render_card(self, parent, emoji, title, desc, view_id, color, col):
        card = ctk.CTkFrame(parent, fg_color=UI_COLORS["surface"],
                              corner_radius=10, border_width=1,
                              border_color=UI_COLORS["border"])
        card.grid(row=0, column=col, sticky="nsew", padx=6, pady=4)
        # Emoji + gradient header
        hdr = ctk.CTkFrame(card, fg_color=color, height=8, corner_radius=10)
        hdr.pack(fill="x", side="top")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=12)
        ctk.CTkLabel(inner, text=emoji, font=("Segoe UI", 22)
                      ).pack(anchor="w")
        ctk.CTkLabel(inner, text=title,
                      font=("Segoe UI", 13, "bold"),
                      anchor="w").pack(anchor="w", pady=(4, 2))
        ctk.CTkLabel(inner, text=desc, text_color=UI_COLORS["text_secondary"],
                      font=("Segoe UI", 10), justify="left",
                      wraplength=200, anchor="w"
                      ).pack(anchor="w", pady=(0, 8))
        ctk.CTkButton(inner, text="Mở →", width=80, height=28,
                       font=("Segoe UI", 11, "bold"),
                       fg_color=color, hover_color=theme_darken(color),
                       command=lambda v=view_id: self._on_navigate(v)
                       ).pack(anchor="w")

    def _render_stat(self, parent, key, label, value, sub, col):
        stat = ctk.CTkFrame(parent, fg_color=UI_COLORS["surface"],
                              corner_radius=10, border_width=1,
                              border_color=UI_COLORS["border"])
        stat.grid(row=0, column=col, sticky="nsew", padx=6, pady=4)
        inner = ctk.CTkFrame(stat, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=12)
        ctk.CTkLabel(inner, text=label, text_color=UI_COLORS["text_secondary"],
                      font=("Segoe UI", 10), anchor="w"
                      ).pack(anchor="w")
        val_lbl = ctk.CTkLabel(inner, text=value,
                                  font=("Segoe UI", 22, "bold"), anchor="w")
        val_lbl.pack(anchor="w", pady=(4, 0))
        self._stat_value_lbls[key] = val_lbl
        ctk.CTkLabel(inner, text=sub, text_color=UI_COLORS["text_muted"],
                      font=("Segoe UI", 9), anchor="w"
                      ).pack(anchor="w")

    def _load_stats(self):
        """Async load stats thật cho 3 card."""
        out = {"session": "—", "nhch": "—", "ai": "—"}
        # Phiên gần đây
        try:
            from storage.database import list_recent_sessions
            out["session"] = f"{len(list_recent_sessions(n=50) or [])}"
        except Exception: pass
        # NHCH count
        try:
            from storage.database import search_questions
            out["nhch"] = f"{len(search_questions() or []):,}"
        except Exception: pass
        # AI calls hôm nay
        try:
            import json
            from datetime import datetime
            from pathlib import Path
            log = Path.home() / ".exam_generator" / "ai_usage.jsonl"
            if log.exists():
                today = datetime.now().strftime("%Y-%m-%d")
                n = 0
                for line in log.read_text(encoding="utf-8").splitlines():
                    try:
                        if json.loads(line).get("ts", "").startswith(today):
                            n += 1
                    except Exception: continue
                out["ai"] = str(n)
        except Exception: pass
        # Check AI key để quyết định hiện banner setup
        has_key = False
        try:
            from services.key_manager import get_key_manager
            km = get_key_manager()
            for prov in ("Google Gemini", "Anthropic Claude", "DeepSeek", "OpenAI"):
                if km.load(prov):
                    has_key = True; break
        except Exception: pass

        # Guard widget destroyed while navigating.
        def _apply():
            try:
                if not self.winfo_exists(): return
                for k, lbl in self._stat_value_lbls.items():
                    lbl.configure(text=out.get(k, "—"))
                # Hiện banner setup nếu chưa có key nào
                if not has_key:
                    self._setup_banner.pack(fill="x", pady=(0, 12),
                                              after=self._subtitle_lbl)
            except Exception: pass
        try: self.after(0, _apply)
        except Exception: pass
