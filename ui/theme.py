"""
ui/theme.py — Centralized design tokens & shared UI utilities.
Dùng chung cho tất cả các tab, đảm bảo UI nhất quán.

P1.8: Dark mode support — `C` dict swap-able lúc startup.
  • get_active_theme()   — trả "light" | "dark"
  • set_active_theme(n)  — lưu preference vào app_settings.json
  • _apply_palette(n)    — swap values trong C dict in-place
"""

import tkinter as tk
from tkinter import ttk

# ══════════════════════════════════════════════════════════════════════════════
#  COLOR PALETTE — Modern Education Theme
# ══════════════════════════════════════════════════════════════════════════════

# Background layers
C = dict(
    # Neutrals
    bg          = "#F8FAFC",   # Window/app background  (slate-50)
    surface     = "#FFFFFF",   # Card / panel background
    surface_2   = "#F1F5F9",   # Toolbar / secondary surface (slate-100)
    surface_3   = "#E2E8F0",   # Borders / dividers     (slate-200)
    border      = "#CBD5E1",   # Subtle borders         (slate-300)

    # Text
    text_main   = "#1E293B",   # Primary text          (slate-800)
    text_body   = "#334155",   # Body text             (slate-700)
    text_sub    = "#475569",   # Secondary text        (slate-600)
    text_muted  = "#64748B",   # Muted/label text      (slate-500)
    text_hint   = "#94A3B8",   # Placeholder/hint      (slate-400)

    # Brand — Sky Blue (primary)
    primary       = "#0284C7",   # Sky-600  (active tab, key actions)
    primary_light = "#0369A1",   # Sky-700  (hover)
    primary_xl    = "#0EA5E9",   # Sky-500  (accent line, buttons)
    primary_bg    = "#E0F2FE",   # Sky-100  (selected bg)
    primary_xlbg  = "#BAE6FD",   # Sky-200  (light bg)

    # Success / Pass
    success       = "#10B981",   # Emerald-500
    success_light = "#059669",   # Emerald-600
    success_bg    = "#ECFDF5",   # Emerald-50
    success_dark  = "#065F46",   # Emerald-800

    # Warning / Review
    warning       = "#F59E0B",   # Amber-500
    warning_light = "#D97706",   # Amber-600
    warning_bg    = "#FFFBEB",   # Amber-50
    warning_dark  = "#92400E",   # Amber-800

    # Danger / Reject
    danger        = "#EF4444",   # Red-500
    danger_light  = "#DC2626",   # Red-600
    danger_bg     = "#FEF2F2",   # Red-50
    danger_dark    = "#991B1B",   # Red-800

    # Purple / Violet (secondary accent)
    purple        = "#8B5CF6",   # Violet-500
    purple_light = "#7C3AED",   # Violet-600
    purple_bg     = "#F5F3FF",   # Violet-50

    # Slate dark (header, nav)
    dark          = "#0F172A",   # Slate-900
    dark_2        = "#1E293B",   # Slate-800
    dark_3        = "#334155",   # Slate-700
)

# ── Dark theme palette (swap vào C khi user chọn dark mode) ──────────────
_DARK_PALETTE = dict(
    # Neutrals — invert
    bg          = "#0F172A",   # Slate-900 (was slate-50)
    surface     = "#1E293B",   # Slate-800 (was white)
    surface_2   = "#334155",   # Slate-700 (was slate-100)
    surface_3   = "#475569",   # Slate-600 (was slate-200)
    border      = "#64748B",   # Slate-500 (was slate-300)

    # Text — invert
    text_main   = "#F1F5F9",   # Slate-100 (was slate-800)
    text_body   = "#E2E8F0",   # Slate-200
    text_sub    = "#CBD5E1",   # Slate-300
    text_muted  = "#94A3B8",   # Slate-400 (giữ tương đối)
    text_hint   = "#64748B",   # Slate-500 (was slate-400)

    # Brand — Sky Blue (giữ — vẫn nổi bật trên dark)
    primary       = "#38BDF8",   # Sky-400 (sáng hơn cho dark bg)
    primary_light = "#0EA5E9",   # Sky-500
    primary_xl    = "#7DD3FC",   # Sky-300 (accent)
    primary_bg    = "#0C4A6E",   # Sky-900 (selected bg trên dark)
    primary_xlbg  = "#075985",   # Sky-800

    # Success — sáng hơn
    success       = "#34D399",   # Emerald-400
    success_light = "#10B981",   # Emerald-500
    success_bg    = "#064E3B",   # Emerald-900
    success_dark  = "#A7F3D0",   # Emerald-200 (cho text)

    # Warning
    warning       = "#FBBF24",   # Amber-400
    warning_light = "#F59E0B",
    warning_bg    = "#78350F",   # Amber-900
    warning_dark  = "#FDE68A",   # Amber-200

    # Danger
    danger        = "#F87171",   # Red-400
    danger_light  = "#EF4444",
    danger_bg     = "#7F1D1D",   # Red-900
    danger_dark   = "#FECACA",   # Red-200

    # Purple
    purple        = "#A78BFA",   # Violet-400
    purple_light  = "#8B5CF6",
    purple_bg     = "#4C1D95",   # Violet-900

    # "Dark" — trong dark theme thực ra là "lighter dark"
    dark          = "#020617",   # Slate-950
    dark_2        = "#0F172A",
    dark_3        = "#1E293B",
)

# ── Theme manager ────────────────────────────────────────────────────────

def get_active_theme() -> str:
    """Trả "light" | "dark" từ app_settings.json (default = light)."""
    try:
        from config import load_app_settings
        s = load_app_settings()
        return "dark" if s.get("theme") == "dark" else "light"
    except Exception:
        return "light"


def set_active_theme(name: str) -> None:
    """Lưu theme vào app_settings.json. Không apply ngay — cần restart."""
    if name not in ("light", "dark"):
        return
    try:
        from config import load_app_settings, save_app_settings
        s = load_app_settings()
        s["theme"] = name
        save_app_settings(s)
    except Exception:
        pass


def _apply_palette(name: str) -> None:
    """Swap values trong `C` dict in-place.
    Modules đã import `C` thấy giá trị mới ngay (vì dict là mutable shared)."""
    if name == "dark":
        for k, v in _DARK_PALETTE.items():
            C[k] = v


# Apply theme khi module load (sau khi C dict đã định nghĩa xong)
try:
    _apply_palette(get_active_theme())
except Exception:
    pass


# Type badge colors
TYPE_COLORS = {
    "TN":  ("#3B82F6", "#EFF6FF"),   # blue
    "DS":  ("#8B5CF6", "#F5F3FF"),   # purple
    "TLN": ("#F59E0B", "#FFFBEB"),   # amber
    "TL":  ("#EF4444", "#FEF2F2"),   # red
}
TYPE_NAMES = {
    "TN":  "Trắc nghiệm",
    "DS":  "Đúng / Sai",
    "TLN": "Trả lời ngắn",
    "TL":  "Tự luận",
}

# Level badge colors
LEVEL_COLORS = {
    "NB":  ("#22C55E", "#F0FDF4"),   # green
    "TH":  ("#3B82F6", "#EFF6FF"),   # blue
    "VD":  ("#F59E0B", "#FFFBEB"),   # amber
}

# QC verdict colors
QC_PASS    = ("#10B981", "#ECFDF5")
QC_REVIEW  = ("#F59E0B", "#FFFBEB")
QC_REJECT  = ("#EF4444", "#FEF2F2")

# ══════════════════════════════════════════════════════════════════════════════
#  TYPOGRAPHY
# ══════════════════════════════════════════════════════════════════════════════

FONT = dict(
    app    = "Segoe UI",
    mono   = "Consolas",
    size_xs = 7,
    size_sm = 8,
    size_md = 9,
    size_lg = 10,
    size_xl = 11,
    size_2xl = 12,
    size_3xl = 13,
    size_hero = 16,
    size_logo = 20,
)

# ══════════════════════════════════════════════════════════════════════════════
#  SPACING
# ══════════════════════════════════════════════════════════════════════════════

PAD = dict(
    xs   = 2,
    sm   = 4,
    md   = 6,
    lg   = 8,
    xl   = 12,
    xxl  = 16,
    padx = 10,
    pady = 6,
)

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS — reusable widget builders
# ══════════════════════════════════════════════════════════════════════════════

def style_toolbar(frame: "tk.BaseWidget"):
    """Set toolbar background color."""
    frame.configure(bg=C["surface_2"])


def style_info_bar(frame: "tk.BaseWidget"):
    """Set info bar background color."""
    frame.configure(bg=C["primary_xlbg"])


def make_badge(parent, text: str, color: str, text_color: str = "white",
               font_size: int = None) -> "tk.Label":
    """Create a colored badge/label."""
    fs = font_size or FONT["size_sm"]
    lbl = tk.Label(
        parent, text=f" {text} ",
        bg=color, fg=text_color,
        font=(FONT["app"], fs, "bold"),
        padx=4, pady=1,
    )
    return lbl


def make_icon_btn(parent, text: str, command,
                  bg: str, fg: str = "white",
                  active_bg: str = None,
                  font_size: int = None,
                  padx: int = 8, pady: int = 3,
                  **kwargs) -> "tk.Button":
    """Create a flat-styled icon button."""
    fs = font_size or FONT["size_sm"]
    abg = active_bg or bg
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=abg, activeforeground=fg,
        font=(FONT["app"], fs, "bold"),
        relief="flat", cursor="hand2", bd=0,
        padx=padx, pady=pady,
        **kwargs,
    )
    return btn


def make_card(parent, bg: str = None, padx: int = 12, pady: int = 8,
               **kwargs) -> "tk.Frame":
    """Create a card frame with white background and subtle border."""
    bg = bg or C["surface"]
    frm = tk.Frame(parent, bg=bg, **kwargs)
    frm.pack_propagate(False)
    return frm


def make_separator(parent, height: int = 1, color: str = None) -> "tk.Frame":
    """Create a horizontal separator line."""
    color = color or C["border"]
    sep = tk.Frame(parent, bg=color, height=height)
    sep.pack(fill="x")
    return sep


def make_section_label(parent, text: str, font_size: int = None) -> "tk.Label":
    """Create a section header label."""
    fs = font_size or FONT["size_md"]
    return tk.Label(
        parent, text=text,
        bg=C["surface"], fg=C["primary"],
        font=(FONT["app"], fs, "bold"),
    )


def apply_badge_tags(text_widget: "tk.Text"):
    """Apply color tags to a ScrolledText widget for question display."""
    text_widget.tag_configure("hdr",     font=(FONT["app"], FONT["size_md"], "bold"), foreground=C["primary"])
    text_widget.tag_configure("qid",    font=(FONT["mono"], FONT["size_xs"], "bold"), foreground=C["purple"])
    text_widget.tag_configure("answer", foreground=C["success_dark"], font=(FONT["app"], FONT["size_md"], "bold"))
    text_widget.tag_configure("solution", foreground=C["warning_dark"])
    text_widget.tag_configure("error",  foreground=C["danger"], background=C["danger_bg"])
    text_widget.tag_configure("sep",    foreground=C["border"])
    text_widget.tag_configure("tag_green", background="#DCFCE7")
    text_widget.tag_configure("tag_blue",  background="#DBEAFE")
    text_widget.tag_configure("tag_amber", background="#FEF3C7")
    text_widget.tag_configure("tag_red",   background="#FEE2E2")


def insert_separator(text_widget: "tk.Text", char: str = "─", length: int = 38):
    text_widget.insert("end", f"\n{char * length}\n", "sep")


def safe_grid(parent, widget, row: int, col: int,
              sticky: str = "w", padx: int = PAD["lg"], pady: int = PAD["sm"], **kwargs):
    widget.grid(row=row, column=col, sticky=sticky, padx=padx, pady=pady, **kwargs)


def make_card_label(parent, title: str, icon: str = "") -> tuple["tk.Frame", "tk.Frame"]:
    """Create a card wrapper (wrap → card → header/content). Returns (wrap, content)."""
    wrap = tk.Frame(parent, bg=C["bg"])
    wrap.pack(fill="x", padx=PAD["xl"], pady=PAD["sm"])

    card = tk.Frame(wrap, bg=C["surface"],
                    highlightbackground=C["border"],
                    highlightthickness=1)
    card.pack(fill="x")

    label_text = f"  {icon}  {title}" if icon else f"  {title}"
    hdr = tk.Label(card, text=label_text,
                   bg=C["surface"], fg=C["primary"],
                   font=(FONT["app"], FONT["size_lg"], "bold"),
                   anchor="w", padx=PAD["xl"], pady=(PAD["lg"], PAD["xs"]))
    hdr.pack(fill="x")
    make_separator(card)

    content = tk.Frame(card, bg=C["surface"])
    content.pack(fill="x", padx=PAD["xl"], pady=(PAD["sm"], PAD["lg"]))

    return wrap, content


# ── Scrollable canvas helper ────────────────────────────────────────────────

class ScrollableFrame:
    """Mixin to create a scrollable canvas with mouse wheel support."""

    def _setup_scrollable(self, parent) -> tuple["tk.Canvas", "tk.Frame"]:
        """Returns (canvas, inner_frame). Call from __init__."""
        canvas = tk.Canvas(parent, bg=C["surface"],
                           highlightthickness=0, takefocus=0)
        vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=C["surface"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_resize(e):
            canvas.itemconfig(win_id, width=e.width)

        def _scrollregion(*_):
            try:
                canvas.update_idletasks()
                bbox = canvas.bbox("all")
                req_h = inner.winfo_reqheight()
                req_w = inner.winfo_reqwidth()
                h = max(req_h, bbox[3] if bbox else 0)
                w = max(req_w, bbox[2] if bbox else 0)
                if h > 0:
                    canvas.configure(scrollregion=(0, 0, w, h))
            except Exception:
                pass

        def _on_mousewheel(e):
            n = int(-4 * (e.delta / 120))
            if n == 0:
                n = -1 if e.delta > 0 else 1
            canvas.yview_scroll(n, "units")
            return "break"

        canvas.bind("<Configure>", _on_resize)
        inner.bind("<Configure>", _scrollregion)
        canvas.bind("<MouseWheel>", _on_mousewheel)
        inner.bind("<MouseWheel>", _on_mousewheel)
        # Linux support
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-4, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(4, "units"))
        inner.bind("<Button-4>", lambda e: canvas.yview_scroll(-4, "units"))
        inner.bind("<Button-5>", lambda e: canvas.yview_scroll(4, "units"))

        return canvas, inner


def bind_mousewheel(canvas: "tk.Canvas", widget: "tk.Widget", speed: int = 4):
    """Bind mouse wheel scrolling on *widget* to scroll *canvas*.
    Use this to propagate scroll from child widgets inside a canvas.
    """
    def _wheel(e):
        n = int(-speed * (e.delta / 120))
        if n == 0:
            n = -1 if e.delta > 0 else 1
        canvas.yview_scroll(n, "units")
        return "break"
    widget.bind("<MouseWheel>", _wheel)
    widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-speed, "units"))
    widget.bind("<Button-5>", lambda e: canvas.yview_scroll(speed, "units"))


def setup_autohide_scrollbar(parent: "tk.Widget", scrollbar: "ttk.Scrollbar"):
    """Make a scrollbar show only when the mouse enters its parent container."""
    scrollbar._visible = False
    _pack_info = {"side": "right", "fill": "y"}

    def _show(_e=None):
        if not scrollbar._visible:
            scrollbar.pack(**_pack_info)
            scrollbar._visible = True

    def _hide(_e=None):
        if scrollbar._visible:
            scrollbar.pack_forget()
            scrollbar._visible = False

    parent.bind("<Enter>", _show)
    parent.bind("<Leave>", _hide)


# ── Custom checkbox images (larger, clearer) ──────────────────────────────

_checkbox_images: dict = {}
_radio_images: dict = {}


def get_checkbox_images(size: int = 20):
    """Return (unchecked_img, checked_img) PhotoImage objects at *size* px.
    Cached so they are created only once per size.
    """
    import tkinter as _tk
    if size in _checkbox_images:
        return _checkbox_images[size]

    border_c = C["border"]       # "#CBD5E1"
    inner_c = "#FFFFFF"
    fill_c = C["primary"]        # "#0284C7"
    check_c = "#FFFFFF"
    bw = 2  # border width

    # ── unchecked: border box, white inside ──
    off = _tk.PhotoImage(width=size, height=size)
    for y in range(size):
        row = []
        for x in range(size):
            if x < bw or x >= size - bw or y < bw or y >= size - bw:
                row.append(border_c)
            else:
                row.append(inner_c)
        off.put("{" + " ".join(row) + "}", to=(0, y))

    # ── checked: filled primary box with white checkmark ──
    on = _tk.PhotoImage(width=size, height=size)
    # Fill all with primary
    for y in range(size):
        on.put("{" + (" ".join([fill_c] * size)) + "}", to=(0, y))

    # Draw checkmark ✓ (scaled)
    s = size / 20.0
    check_points = set()
    for bx, by in [
        (4, 10), (5, 10), (6, 11), (7, 12), (8, 13), (9, 14),
        (10, 13), (11, 12), (12, 11), (13, 10), (14, 9), (15, 8), (16, 7),
        (4, 11), (5, 11), (6, 12), (7, 13), (8, 14), (9, 15),
        (10, 14), (11, 13), (12, 12), (13, 11), (14, 10), (15, 9), (16, 8),
        (5, 12), (6, 13), (7, 14), (8, 15),
        (9, 12), (10, 12), (11, 11), (12, 10), (13, 9), (14, 8), (15, 7),
    ]:
        px, py = int(bx * s), int(by * s)
        if 0 <= px < size and 0 <= py < size:
            check_points.add((px, py))
    for px, py in check_points:
        on.put(check_c, (px, py))

    _checkbox_images[size] = (off, on)
    return off, on


def get_radio_images(size: int = 20, bg: str = "#FAFAFA"):
    """Return (unselected_img, selected_img) circular RadioButton images.
    *bg* is the background color outside the circle.
    Cached per (size, bg).
    """
    import tkinter as _tk
    key = (size, bg)
    if key in _radio_images:
        return _radio_images[key]

    border_c = C["border"]       # "#CBD5E1"
    inner_c = "#FFFFFF"
    fill_c = C["primary"]        # "#0284C7"
    dot_c = "#FFFFFF"
    r = size / 2.0
    bw = 2  # border width

    # ── unselected: circle with border ──
    off = _tk.PhotoImage(width=size, height=size)
    for y in range(size):
        row = []
        for x in range(size):
            dx, dy = x - r + 0.5, y - r + 0.5
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= r and dist > r - bw:
                row.append(border_c)
            elif dist <= r - bw:
                row.append(inner_c)
            else:
                row.append(bg)
        off.put("{" + " ".join(row) + "}", to=(0, y))

    # ── selected: filled circle with white dot center ──
    on = _tk.PhotoImage(width=size, height=size)
    dot_r = r * 0.38  # inner dot radius
    for y in range(size):
        row = []
        for x in range(size):
            dx, dy = x - r + 0.5, y - r + 0.5
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= dot_r:
                row.append(dot_c)
            elif dist <= r:
                row.append(fill_c)
            else:
                row.append(bg)
        on.put("{" + " ".join(row) + "}", to=(0, y))

    _radio_images[key] = (off, on)
    return off, on


# ── ttk Style helpers ──────────────────────────────────────────────────────

def apply_ttk_theme(style: ttk.Style):
    """Apply the modern theme to ttk widgets (call from main_window)."""
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Notebook
    style.configure("TNotebook", background=C["bg"], borderwidth=0,
                    tabmargins=[2, 3, 0, 0])
    style.configure("TNotebook.Tab",
                    font=(FONT["app"], FONT["size_sm"], "bold"),
                    padding=[6, 4],
                    background=C["surface_2"],
                    foreground=C["text_muted"],
                    borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", C["surface"]),
                          ("!selected", C["surface_2"]),
                          ("active",    C["surface_3"])],
              foreground=[("selected", C["primary"]),
                          ("!selected", C["text_muted"]),
                          ("active",    C["text_body"])],
              expand=[("selected", [0, 0, 0, 2])])

    # Labelframe
    style.configure("TLabelframe", background=C["surface"],
                    font=(FONT["app"], FONT["size_md"], "bold"),
                    foreground=C["text_main"])
    style.configure("TLabelframe.Label", background=C["surface"],
                    font=(FONT["app"], FONT["size_md"], "bold"),
                    foreground=C["primary"])

    # Primary button (sky blue)
    style.configure("Primary.TButton",
                    font=(FONT["app"], FONT["size_sm"], "bold"),
                    padding=[8, 4],
                    background=C["primary_xl"], foreground="white", borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", C["primary"]),
                          ("pressed", C["primary_light"]),
                          ("disabled", C["surface_3"])],
              foreground=[("disabled", C["text_hint"])])

    # Accent button (green)
    style.configure("Accent.TButton",
                    font=(FONT["app"], FONT["size_md"], "bold"),
                    padding=[10, 5],
                    background=C["success"], foreground="white", borderwidth=0)
    style.map("Accent.TButton",
              background=[("active", C["success_light"]), ("pressed", C["success"])])

    # Warning button (amber)
    style.configure("Warning.TButton",
                    font=(FONT["app"], FONT["size_md"], "bold"),
                    padding=[10, 5],
                    background=C["warning"], foreground="white", borderwidth=0)
    style.map("Warning.TButton",
              background=[("active", C["warning_light"]), ("pressed", C["warning"])])

    # Danger button (red)
    style.configure("Danger.TButton",
                    font=(FONT["app"], FONT["size_md"], "bold"),
                    padding=[10, 5],
                    background=C["danger"], foreground="white", borderwidth=0)
    style.map("Danger.TButton",
              background=[("active", C["danger_light"]), ("pressed", C["danger"])])

    # Treeview — gọn hơn để chừa chỗ cho thêm công cụ / bảng lớn
    style.configure("Treeview", font=(FONT["app"], FONT["size_md"]),
                    rowheight=26,
                    background=C["surface"],
                    fieldbackground=C["surface"],
                    bordercolor=C["border"])
    style.configure("Treeview.Heading",
                    font=(FONT["app"], FONT["size_sm"], "bold"),
                    foreground=C["text_body"],
                    background=C["surface_2"],
                    borderwidth=0)
    style.map("Treeview.Heading", background=[("active", C["surface_3"])])
    style.map("Treeview",
              background=[("selected", C["primary_bg"])],
              foreground=[("selected", C["primary"])])

    style.configure("TCombobox", font=(FONT["app"], FONT["size_md"]))

    # Spinbox
    style.configure("TSpinbox", font=(FONT["app"], FONT["size_md"], "bold"),
                    padding=[2, 2], arrowsize=14)

    # Checkbutton
    style.configure("TCheckbutton", font=(FONT["app"], FONT["size_md"]),
                    background=C["surface"], foreground=C["text_main"])
    style.map("TCheckbutton",
              indicatorcolor=[("selected", C["primary_xl"]), ("!selected", C["border"])],
              background=[("active", C["bg"])],
              foreground=[("disabled", C["text_hint"])])

    # Radiobutton
    style.configure("TRadiobutton", font=(FONT["app"], FONT["size_md"]),
                    background=C["surface"], foreground=C["text_main"])
    style.map("TRadiobutton",
              indicatorcolor=[("selected", C["primary_xl"]), ("!selected", C["border"])],
              background=[("active", C["bg"])],
              foreground=[("disabled", C["text_hint"])])

    # Scrollbar — rõ ràng, dễ kéo (ttk)
    style.configure("Vertical.TScrollbar", background=C["primary_light"],
                    troughcolor=C["surface_2"], borderwidth=0, arrowsize=14,
                    width=12)
    style.map("Vertical.TScrollbar",
              background=[("active", C["primary"]),
                          ("pressed", C["primary_xl"])])
    style.configure("Horizontal.TScrollbar", background=C["primary_light"],
                    troughcolor=C["surface_2"], borderwidth=0, arrowsize=14,
                    width=12)
    style.map("Horizontal.TScrollbar",
              background=[("active", C["primary"]),
                          ("pressed", C["primary_xl"])])
