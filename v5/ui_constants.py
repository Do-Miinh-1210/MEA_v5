"""
v5/ui_constants.py — Tham chiếu kích thước/màu/font chuẩn cho mọi view + dialog.

Hệ thống 3 tầng:
  • PRIMARY   (40 × 13 bold)  — CTA chính, action quan trọng nhất ở mỗi view
                                 (vd "▶ Tạo đề bằng AI", "🔑 Đăng nhập",
                                 "📄 Import PDF" trong NHCH).
  • SECONDARY (32 × 12 bold)  — Action ở header, switch mode, navigation
                                 (vd "💬 Smart Prompt", "🔄 Reload",
                                 "📊 Thống kê", "💾 Lưu key").
  • TERTIARY  (28 × 11)       — Action vận hành, nút phụ, hiển thị/ẩn
                                 (vd "➕ Thêm dòng", "🗑 Xoá", "👁 Hiện/Ẩn").

Width:
  • XS  = 80  — icon + 1-2 từ ngắn ("Lưu", "Test")
  • SM  = 100 — 2-3 từ ("Xoá key")
  • MD  = 140 — 3-4 từ ("Đăng nhập")
  • LG  = 170 — 4-5 từ ("AI tạo ma trận")
  • XL  = 200 — primary CTA dài
"""
from __future__ import annotations

# ── Heights ─────────────────────────────────────────────────────────────────
H_PRIMARY   = 40
H_SECONDARY = 32
H_TERTIARY  = 28

# ── Fonts ────────────────────────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"
FONT_PRIMARY   = (FONT_FAMILY, 13, "bold")
FONT_SECONDARY = (FONT_FAMILY, 12, "bold")
FONT_TERTIARY  = (FONT_FAMILY, 11)
FONT_TERTIARY_BOLD = (FONT_FAMILY, 11, "bold")

# ── Widths ───────────────────────────────────────────────────────────────────
W_XS = 80
W_SM = 100
W_MD = 140
W_LG = 170
W_XL = 200

# ── Color presets ────────────────────────────────────────────────────────────
COLOR = {
    # Primary (CTA chính — xanh)
    "primary":       "#10B981",
    "primary_hover": "#059669",

    # Info / navigation (xanh dương)
    "info":          "#3B82F6",
    "info_hover":    "#2563EB",

    # Smart prompt / AI (tím)
    "ai":            "#7C3AED",
    "ai_hover":      "#6D28D9",

    # Warning (vàng/cam)
    "warn":          "#F59E0B",
    "warn_hover":    "#D97706",

    # Danger (đỏ)
    "danger":        "#DC2626",
    "danger_hover": "#B91C1C",

    # Neutral (xám)
    "neutral":       "#6B7280",
    "neutral_hover":"#4B5563",

    # Cyan / Sync
    "cyan":          "#0EA5E9",
    "cyan_hover":    "#0284C7",

    # Purple light (matrix import)
    "purple":        "#A78BFA",
    "purple_hover":  "#8B5CF6",
}


def primary_btn(parent, text, command=None, *,
                  width=W_XL, color="primary", **kw):
    """Helper tạo CTkButton primary CTA."""
    import customtkinter as ctk
    return ctk.CTkButton(
        parent, text=text, command=command,
        width=width, height=H_PRIMARY,
        font=FONT_PRIMARY,
        fg_color=COLOR[color], hover_color=COLOR[f"{color}_hover"],
        **kw,
    )


def secondary_btn(parent, text, command=None, *,
                    width=W_MD, color="info", **kw):
    """Helper tạo CTkButton secondary."""
    import customtkinter as ctk
    return ctk.CTkButton(
        parent, text=text, command=command,
        width=width, height=H_SECONDARY,
        font=FONT_SECONDARY,
        fg_color=COLOR[color], hover_color=COLOR[f"{color}_hover"],
        **kw,
    )


def tertiary_btn(parent, text, command=None, *,
                   width=W_SM, bold=False, **kw):
    """Helper tạo CTkButton tertiary (transparent default)."""
    import customtkinter as ctk
    return ctk.CTkButton(
        parent, text=text, command=command,
        width=width, height=H_TERTIARY,
        font=FONT_TERTIARY_BOLD if bold else FONT_TERTIARY,
        **kw,
    )
