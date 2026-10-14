"""
ui/tab_user_info.py — Tab Thông tin người dùng: tên, mã máy, gói, đếm ngược hết hạn.
Cuộn chuột, copy mã máy, logo giống tab_about.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from pathlib import Path
from config import APP_VERSION

ASSETS_DIR = Path(__file__).parent.parent / "assets"

# ── Bảng màu mới đồng bộ với UI hiện đại ─────────────────────────────
PRIMARY = "#0284C7"  # Xanh dương đậm (Sky 600)
ACCENT = "#0EA5E9"   # Xanh Cyan (Sky 500)
BG = "#F8FAFC"       # Nền tổng thể sáng (Slate 50)
CARD = "#FFFFFF"     # Nền thẻ trắng tinh
TEXT_MAIN = "#334155" # Chữ chính (Slate 700)
TEXT_MUTED = "#64748B" # Chữ phụ (Slate 500)
BORDER = "#E2E8F0"   # Viền (Slate 200)

# Nền Banner Hero (Xanh Pastel nhạt đồng bộ với tab_about)
HERO_BG = "#E0F2FE"

TIER_COLORS = {
    "basic":   ("#64748B", "#F1F5F9", "🥉"),
    "pro":     ("#0284C7", "#E0F2FE", "🥈"),
    "premium": ("#8B5CF6", "#F3E8FF", "🏆"),
}

TIER_LABELS = {
    "basic":   "Basic — Tự nhập API key",
    "pro":     "PRO — Admin cấp API key, mở rộng tính năng",
    "premium": "Premium — Toàn quyền, ưu tiên API key",
}


def _load_logo(parent, size=80, bg=HERO_BG):
    try:
        from PIL import Image, ImageTk
        img = Image.open(ASSETS_DIR / "app.png").convert("RGBA").resize(
            (size, size), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        lbl = tk.Label(parent, image=photo, bg=bg)
        lbl.image = photo
        return lbl
    except Exception:
        return tk.Label(parent, text="🎓", bg=bg, font=("Segoe UI", int(size * 0.38)), fg=PRIMARY)


class TabUserInfo(tk.Frame):
    """Tab Thông tin người dùng — hiển thị license, đếm ngược hết hạn."""

    def __init__(self, parent, license_info: dict | None = None):
        super().__init__(parent, bg=BG)
        self._license = license_info or {}
        self._countdown_id = None
        self._build()

    def _build(self):
        li = self._license
        name = li.get("name", "Khách")
        mid = li.get("mid", "N/A")
        tier = li.get("tier", "basic").lower()
        expiry = li.get("expiry", "Vĩnh viễn")
        status = li.get("status", "active")

        if not mid or mid == "N/A":
            try:
                from services.license_manager import get_machine_id
                mid = get_machine_id()
            except Exception:
                mid = "N/A"
        self._machine_id = mid

        tier_color, tier_bg, tier_icon = TIER_COLORS.get(tier, TIER_COLORS["basic"])
        tier_label = TIER_LABELS.get(tier, tier.upper())

        # ── Scrollable canvas ───────────────────────────────────────────
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        # Scrollbar luôn hiển thị (giúp user nhận biết tab có thể cuộn).
        vsb.pack(side="right", fill="y")

        inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", _on_resize)
        inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Cuộn chuột — bind toàn bộ widget con
        def _scroll(e):
            n = int(-4 * (e.delta / 120))
            if n == 0:
                n = -1 if e.delta > 0 else 1
            canvas.yview_scroll(n, "units")
            return "break"
        canvas.bind("<MouseWheel>", _scroll)
        inner.bind("<MouseWheel>", _scroll)

        # ── Card helper ─────────────────────────────────────────────────
        def card(title, icon="", bg_color=CARD):
            wrap = tk.Frame(inner, bg=BG)
            wrap.pack(fill="x", padx=28, pady=8)
            wrap.bind("<MouseWheel>", _scroll)
            frm = tk.Frame(wrap, bg=bg_color, highlightbackground=BORDER,
                           highlightthickness=1)
            frm.pack(fill="x")
            frm.bind("<MouseWheel>", _scroll)
            hdr = tk.Label(frm,
                           text=f"  {icon}  {title}" if icon else f"  {title}",
                           bg=bg_color, fg=PRIMARY, font=("Segoe UI", 11, "bold"),
                           anchor="w")
            hdr.pack(fill="x", padx=12, pady=4)
            hdr.bind("<MouseWheel>", _scroll)
            sep = tk.Frame(frm, bg=BORDER, height=1)
            sep.pack(fill="x", padx=12)
            content = tk.Frame(frm, bg=bg_color)
            content.pack(fill="x", padx=12, pady=12)
            content.bind("<MouseWheel>", _scroll)
            return content

        # ── Hero banner ─────────────────────────────────────────────────
        hero = tk.Frame(inner, bg=HERO_BG)
        hero.pack(fill="x")
        
        # Viền phân cách dưới Hero giống tab_about
        tk.Frame(inner, bg="#BAE6FD", height=2).pack(fill="x", pady=6)

        hero.bind("<MouseWheel>", _scroll)
        _load_logo(hero, size=80, bg=HERO_BG).pack(pady=8)
        tk.Label(hero, text=f"{tier_icon}  {name}", bg=HERO_BG, fg="#0369A1",
                 font=("Segoe UI", 20, "bold")).pack(pady=4)

        # Mã máy — cho phép select & copy
        mid_frame = tk.Frame(hero, bg=HERO_BG)
        mid_frame.pack(pady=4)
        mid_frame.bind("<MouseWheel>", _scroll)
        mid_entry = tk.Entry(mid_frame, font=("Consolas", 12, "bold"), fg="#0284C7",
                             bg="#F0F9FF", relief="solid", bd=1,
                             readonlybackground="#F0F9FF", justify="center",
                             width=len(mid) + 4)
        mid_entry.insert(0, mid)
        mid_entry.config(state="readonly")
        mid_entry.pack(side="left", padx=6, ipady=2)

        copy_btn = tk.Button(mid_frame, text="📋 Copy", bg=PRIMARY, fg="white",
                             font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                             bd=0, padx=8, pady=2,
                             command=lambda: self._copy_mid(mid))
        copy_btn.pack(side="left")

        # Badge gói
        badge_frm = tk.Frame(hero, bg=tier_color)
        badge_frm.pack(pady=16)
        badge_frm.bind("<MouseWheel>", _scroll)
        tk.Label(badge_frm, text=f"  {tier_icon} {tier.upper()}  ", bg=tier_color,
                 fg="white", font=("Segoe UI", 11, "bold"),
                 padx=12, pady=4).pack()

        # ── Card: Thông tin tài khoản ───────────────────────────────────
        c1 = card("Thông tin tài khoản", "👤")
        # Chuyển YYYY-MM-DD → DD/MM/YYYY để hiển thị
        expiry_display = expiry
        if expiry and expiry not in ("Vĩnh viễn", "0", ""):
            try:
                expiry_display = datetime.strptime(expiry, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                pass
        info_rows = [
            ("Tên người dùng", name),
            ("Gói dịch vụ", f"{tier_icon} {tier_label}"),
            ("Trạng thái", "✅ Đang hoạt động" if status == "active" else f"⚠️ {status}"),
            ("Ngày hết hạn", expiry_display),
        ]
        for label, value in info_rows:
            row = tk.Frame(c1, bg=CARD)
            row.pack(fill="x", pady=3)
            row.bind("<MouseWheel>", _scroll)
            tk.Label(row, text=f"{label}:", bg=CARD, fg=TEXT_MUTED,
                     font=("Segoe UI", 10), width=22, anchor="w").pack(side="left")
            lbl = tk.Label(row, text=value, bg=CARD, fg=TEXT_MAIN,
                     font=("Segoe UI", 10, "bold"), anchor="w")
            lbl.pack(side="left")
            lbl.bind("<MouseWheel>", _scroll)

        # Mã máy riêng — có nút copy
        mid_row = tk.Frame(c1, bg=CARD)
        mid_row.pack(fill="x", pady=3)
        mid_row.bind("<MouseWheel>", _scroll)
        tk.Label(mid_row, text="Mã máy (Machine ID):", bg=CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 10), width=22, anchor="w").pack(side="left")
        mid_val = tk.Entry(mid_row, font=("Consolas", 10, "bold"), fg=TEXT_MAIN,
                           bg=CARD, relief="flat", bd=0, readonlybackground=CARD,
                           width=len(mid) + 2)
        mid_val.insert(0, mid)
        mid_val.config(state="readonly")
        mid_val.pack(side="left")
        tk.Button(mid_row, text="📋 Copy", bg=BORDER, fg=TEXT_MAIN,
                  font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2",
                  bd=0, padx=6, pady=1,
                  command=lambda: self._copy_mid(mid)).pack(side="left", padx=0)

        # ── Card: Đếm ngược hết hạn ────────────────────────────────────
        c2 = card("Thời hạn sử dụng", "⏳")
        self._exp_str = expiry
        self._countdown_lbl = tk.Label(c2, text="", bg=CARD,
                                        font=("Segoe UI", 14, "bold"),
                                        anchor="w")
        self._countdown_lbl.pack(anchor="w", pady=2)
        self._countdown_lbl.bind("<MouseWheel>", _scroll)

        self._countdown_detail = tk.Label(c2, text="", bg=CARD, fg=TEXT_MUTED,
                                           font=("Segoe UI", 10), anchor="w")
        self._countdown_detail.pack(anchor="w")
        self._countdown_detail.bind("<MouseWheel>", _scroll)

        # Progress bar hạn dùng
        self._exp_progress = ttk.Progressbar(c2, length=400, mode="determinate")
        self._exp_progress.pack(anchor="w", pady=4)

        self._exp_note = tk.Label(c2, text="", bg=CARD, fg="#9CA3AF",
                                   font=("Segoe UI", 9, "italic"), anchor="w")
        self._exp_note.pack(anchor="w")
        self._exp_note.bind("<MouseWheel>", _scroll)

        # ── Card: Quyền lợi gói ────────────────────────────────────────
        c3 = card("Quyền lợi gói dịch vụ", "🎁", bg_color=tier_bg)

        # Icon cho từng feature
        _FEAT_ICONS = {
            "tab_matrix":  "📝", "tab_result":  "📄", "tab_bank":    "🏦",
            "tab_qc":      "✅", "tab_tikz":    "✏️", "tab_convert": "🖼️",
            "quick_gen":   "⚡", "export_word": "📄", "nhch_cloud":  "☁️",
            "ai_review":   "🤖", "multi_code":  "🔢",
        }

        # Thêm perk riêng về API key
        if tier == "basic":
            perks = [("🔑", "Tự nhập API key")]
        elif tier == "pro":
            perks = [("🔑", "Admin cấp API key hoặc tự nhập")]
        else:
            perks = [("🔑", "API key ưu tiên do Admin cấp")]

        # Lấy danh sách tính năng từ FEATURE_CATALOG
        from config import FEATURE_CATALOG
        for feat_key, feat_info in FEATURE_CATALOG.items():
            enabled = feat_info.get(tier, False)
            if enabled:
                icon = _FEAT_ICONS.get(feat_key, "•")
                perks.append((icon, feat_info["label"]))

        for icon, text in perks:
            row = tk.Frame(c3, bg=tier_bg)
            row.pack(fill="x", pady=2)
            row.bind("<MouseWheel>", _scroll)
            lbl = tk.Label(row, text=f"  {icon}  {text}", bg=tier_bg, fg=TEXT_MAIN,
                     font=("Segoe UI", 10), anchor="w")
            lbl.pack(anchor="w")
            lbl.bind("<MouseWheel>", _scroll)

        # ── Liên hệ gia hạn ────────────────────────────────────────────
        c4 = card("Liên hệ & Hỗ trợ", "📞")
        contacts = [
            ("📱 Zalo/SĐT", "033.999.8261"),
            ("📧 Gmail", "domiinh.369@gmail.com"),
        ]
        for clbl, cval in contacts:
            row = tk.Frame(c4, bg=CARD)
            row.pack(fill="x", pady=2)
            row.bind("<MouseWheel>", _scroll)
            tk.Label(row, text=f"{clbl}:", bg=CARD, fg=TEXT_MUTED,
                     font=("Segoe UI", 9, "bold"), width=13, anchor="w").pack(side="left")
            lbl_c = tk.Label(row, text=cval, bg=CARD, fg=PRIMARY,
                              font=("Segoe UI", 9), anchor="w")
            lbl_c.pack(side="left")
            lbl_c.bind("<MouseWheel>", _scroll)

        # ── Footer ──────────────────────────────────────────────────────
        footer = tk.Frame(inner, bg="#F1F5F9")
        footer.pack(fill="x", pady=0)
        footer.bind("<MouseWheel>", _scroll)
        tk.Label(footer,
                 text=f"© 2026 DoMinhMath — MatrixExamAI v{APP_VERSION}  |  Bảo lưu mọi quyền",
                 bg="#F1F5F9", fg=TEXT_MUTED, font=("Segoe UI", 8)).pack(pady=12)

        # ── Bắt đầu đếm ngược ──────────────────────────────────────────
        self._update_countdown()

    # ── Copy Machine ID ─────────────────────────────────────────────────

    def _copy_mid(self, mid: str):
        self.clipboard_clear()
        self.clipboard_append(mid)
        messagebox.showinfo("Đã sao chép",
            f"Đã sao chép Mã máy:\n{mid}\n\nGửi mã này cho admin để kích hoạt/gia hạn.",
            parent=self.winfo_toplevel())

    # ── Countdown logic ─────────────────────────────────────────────────

    def _update_countdown(self):
        expiry = self._exp_str

        if not expiry or expiry in ("Vĩnh viễn", "0", ""):
            self._countdown_lbl.config(text="♾️  Vĩnh viễn", fg="#10B981")
            self._countdown_detail.config(text="Gói của bạn không có thời hạn.")
            self._exp_progress["value"] = 100
            self._exp_note.config(text="")
            return

        try:
            exp_date = datetime.strptime(expiry, "%Y-%m-%d").date()
        except Exception:
            self._countdown_lbl.config(text=f"📅 {expiry}", fg=TEXT_MUTED)
            self._countdown_detail.config(text="")
            return

        today = date.today()
        remaining = (exp_date - today).days

        if remaining < 0:
            self._countdown_lbl.config(
                text=f"❌  Đã hết hạn {abs(remaining)} ngày trước", fg="#EF4444")
            self._countdown_detail.config(
                text=f"Hết hạn: {exp_date.strftime('%d/%m/%Y')}. Liên hệ admin để gia hạn.")
            self._exp_progress["value"] = 0
            self._exp_note.config(text="⚠️ Vui lòng gia hạn để tiếp tục sử dụng.",
                                   fg="#EF4444")
        elif remaining == 0:
            self._countdown_lbl.config(
                text="⚠️  Hết hạn hôm nay!", fg="#F59E0B")
            self._countdown_detail.config(
                text=f"Ngày hết hạn: {exp_date.strftime('%d/%m/%Y')}")
            self._exp_progress["value"] = 1
            self._exp_note.config(text="⚠️ Gia hạn ngay để không bị gián đoạn.",
                                   fg="#F59E0B")
        elif remaining <= 7:
            self._countdown_lbl.config(
                text=f"⚠️  Còn {remaining} ngày", fg="#F59E0B")
            self._countdown_detail.config(
                text=f"Hết hạn: {exp_date.strftime('%d/%m/%Y')} — sắp hết hạn!")
            self._exp_progress["value"] = max(5, remaining * 3)
            self._exp_note.config(text="💡 Gia hạn sớm để không bị gián đoạn.",
                                   fg="#F59E0B")
        elif remaining <= 30:
            self._countdown_lbl.config(
                text=f"📅  Còn {remaining} ngày", fg=PRIMARY)
            self._countdown_detail.config(
                text=f"Hết hạn: {exp_date.strftime('%d/%m/%Y')}")
            self._exp_progress["value"] = min(100, remaining * 3)
            self._exp_note.config(text="")
        else:
            self._countdown_lbl.config(
                text=f"✅  Còn {remaining} ngày", fg="#10B981")
            self._countdown_detail.config(
                text=f"Hết hạn: {exp_date.strftime('%d/%m/%Y')}")
            self._exp_progress["value"] = min(100, remaining)
            self._exp_note.config(text="")

        # Cập nhật mỗi 60 giây
        self._countdown_id = self.after(60_000, self._update_countdown)

    def destroy(self):
        if self._countdown_id:
            self.after_cancel(self._countdown_id)
        super().destroy()
