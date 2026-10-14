"""Shared V5 color tokens.

Keep high-contrast colors in one place so views do not drift into muted,
duplicated palettes over time.
"""
from __future__ import annotations


UI_COLORS = {
    "app_bg": ("#F8FAFC", "#0F172A"),
    "surface": ("#FFFFFF", "#1E293B"),
    "surface_alt": ("#F1F5F9", "#111827"),
    "surface_soft": ("#EFF6FF", "#172033"),
    "border": ("#CBD5E1", "#334155"),
    "border_strong": ("#94A3B8", "#475569"),
    "text": ("#0F172A", "#F8FAFC"),
    "text_secondary": ("#334155", "#CBD5E1"),
    "text_muted": ("#64748B", "#94A3B8"),
    "text_on_accent": "#FFFFFF",
    "topbar": ("#1E3A8A", "#0B1F35"),
    "guide_nav": ("#F1F5F9", "#111827"),
    "guide_content": ("#F8FAFC", "#0F172A"),
    "guide_header": ("#1E40AF", "#0B1F35"),
    "guide_header_subtitle": ("#DBEAFE", "#BFDBFE"),
    "info_bg": ("#E0F2FE", "#0C4A6E"),
    "info_text": ("#075985", "#BAE6FD"),
    "warn_bg": ("#FEF3C7", "#3F2E12"),
    "warn_text": ("#92400E", "#FCD34D"),
    "success": "#059669",
    "primary": "#2563EB",
    "cyan": "#0891B2",
    "orange": "#EA580C",
    "purple": "#7C3AED",
    "indigo": "#4F46E5",
    "red": "#DC2626",
    "teal": "#0D9488",
    "rose": "#E11D48",
}


GUIDE_ACCENTS = [
    UI_COLORS["primary"],
    UI_COLORS["cyan"],
    UI_COLORS["orange"],
    UI_COLORS["success"],
    UI_COLORS["purple"],
    UI_COLORS["indigo"],
    UI_COLORS["red"],
    UI_COLORS["teal"],
    UI_COLORS["rose"],
]


def darken(hex_color: str, amount: float = 0.16) -> str:
    """Return a darker hex color for hover states."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        r, g, b = (int(max(0, c * (1 - amount))) for c in (r, g, b))
        return f"#{r:02X}{g:02X}{b:02X}"
    except Exception:
        return hex_color


def tint(hex_color: str, amount: float = 0.90) -> str:
    """Blend a color toward white for light-mode soft backgrounds."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
        r = int(r + (255 - r) * amount)
        g = int(g + (255 - g) * amount)
        b = int(b + (255 - b) * amount)
        return f"#{r:02X}{g:02X}{b:02X}"
    except Exception:
        return "#EFF6FF"
