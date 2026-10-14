"""
ui/activation_dialog.py — Dialog kích hoạt app MatrixExamAI v4.1.0.
- Logo, bảng giá 3 gói (Basic/Pro/Premium) x 4 thời hạn
- QR Code động từ Machine ID + Gói được chọn
- Buttons luôn hiển thị (pack bottom trước)
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import hashlib, urllib.parse

ASSETS_DIR = Path(__file__).parent.parent / "assets"
BLUE = "#1F497D"; LBLUE = "#E3F2FD"; GREEN = "#10b981"
DARK_GREEN = "#059669"; RED = "#EF4444"; YELLOW_BG = "#FFF8E1"
YELLOW_BD = "#FFD54F"; BG = "#F9F7F4"

BANK_INFO = [
    ("Ngân hàng",      "Vietcombank"),
    ("Số tài khoản",   "1017919118"),
    ("Chủ tài khoản",  "DO HUYNH BINH MINH"),
    ("Nội dung CK",    "(Mã máy của bạn)"),
]

ADMIN_CONTACTS = [
    ("Zalo/SĐT",  "033.999.8261"),
    ("Gmail",      "domiinh.369@gmail.com"),
]

# ═══════════════════════════════════════════════════════════════════
#  BẢNG GIÁ MẶC ĐỊNH: 3 GÓI x 4 THỜI HẠN
# ═══════════════════════════════════════════════════════════════════
# Cấu trúc: tier -> list[{duration, price, hot}]
DEFAULT_PRICING = {
    "basic": {
        "name": "BASIC",
        "icon": "",
        "color": "#64748B",
        "desc": "Dùng thử — nhập số tiền tùy chọn",
        "features": [
            "Tạo đề (Bảng câu hỏi)",
            "Xem đề & Xuất Word",
        ],
        "custom_price": True,
        "durations": [
            {"duration": "Tùy chọn", "price": "0 đ", "hot": False, "enabled": True},
        ],
    },
    "pro": {
        "name": "PRO",
        "icon": "",
        "color": "#2563EB",
        "desc": "Admin cấp API Key, tạo đề nhanh",
        "features": [
            "Tất cả tính năng Basic",
            "Tạo đề nhanh (lớp 1-12)",
            "Ngân hàng câu hỏi",
            "NHCH Cloud (đồng bộ)",
        ],
        "durations": [
            {"duration": "1 tháng",  "price": "199.000 đ",   "hot": False, "enabled": True},
            {"duration": "3 tháng",  "price": "569.000 đ",   "hot": False, "enabled": True},
            {"duration": "6 tháng",  "price": "1.099.000 đ", "hot": True,  "enabled": True},
            {"duration": "12 tháng", "price": "1.999.000 đ", "hot": False, "enabled": True},
        ],
    },
    "premium": {
        "name": "PREMIUM",
        "icon": "",
        "color": "#7C3AED",
        "desc": "Toàn quyền + API key ưu tiên",
        "features": [
            "Tất cả tính năng Pro",
            "Nhiều mã đề (trộn đề)",
            "Kiểm tra chất lượng (QC)",
            "AI Review & Fix",
            "TikZ vẽ hình + AI vẽ hình",
        ],
        "durations": [
            {"duration": "1 tháng",  "price": "299.000 đ",   "hot": False, "enabled": True},
            {"duration": "3 tháng",  "price": "849.000 đ",   "hot": False, "enabled": True},
            {"duration": "6 tháng",  "price": "1.599.000 đ", "hot": True,  "enabled": True},
            {"duration": "12 tháng", "price": "2.999.000 đ", "hot": False, "enabled": True},
        ],
    },
}


def _fetch_pricing_from_cloud() -> dict | None:
    """Lấy bảng giá từ Supabase settings. Trả về dict hoặc None nếu lỗi."""
    try:
        from services.license_manager import admin_get_settings
        settings = admin_get_settings()
        if settings:
            import json
            raw = settings.get("pricing_v2")
            if raw:
                data = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(data, dict) and data:
                    return data
    except Exception:
        pass
    return None


def _load_logo(parent, size=52, bg=BLUE):
    try:
        from PIL import Image, ImageTk
        img = Image.open(ASSETS_DIR / "app.png").convert("RGBA").resize(
            (size, size), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        lbl = tk.Label(parent, image=photo, bg=bg)
        lbl.image = photo
        return lbl
    except Exception:
        return tk.Label(parent, text="E", bg=bg, fg="white",
                        font=("Segoe UI", int(size * 0.45), "bold"))


def _make_vietqr_url(machine_id: str, pkg: str, amount: str) -> str:
    bank_id  = "VCB"
    acc_no   = "1017919118"
    acc_name = "DO HUYNH BINH MINH"
    content  = urllib.parse.quote(f"{machine_id} {pkg}")
    amt      = amount.replace(".", "").replace(" đ", "").replace(" d", "").replace(",", "")
    return (f"https://img.vietqr.io/image/{bank_id}-{acc_no}-qr_only.png"
            f"?amount={amt}&addInfo={content}&accountName={urllib.parse.quote(acc_name)}")


class ActivationDialog(tk.Toplevel):
    def __init__(self, parent=None, license_result: dict | None = None):
        if parent:
            super().__init__(parent)
        else:
            super().__init__()
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.activated = False
        self._license_result = license_result or {}
        self._qr_photo = None
        self._pricing = _fetch_pricing_from_cloud() or DEFAULT_PRICING
        self._selected_tier = tk.StringVar(value="pro")
        self._selected_dur = tk.StringVar(value="6 tháng")
        self._build()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.resizable(True, True)
        self.minsize(900, 750)
        self.focus_force()

    def _build(self):
        from services.license_manager import get_machine_id, get_machine_display
        from config import APP_VERSION
        self.title(f"Kích hoạt phần mềm — MatrixExamAI v{APP_VERSION}")
        self.configure(bg=BG)
        W, H = 1000, 900
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BLUE)
        hdr.pack(fill="x", side="top")
        _load_logo(hdr, size=60, bg=BLUE).pack(side="left", padx=(18, 10), pady=10)
        htxt = tk.Frame(hdr, bg=BLUE)
        htxt.pack(side="left", pady=10)
        tk.Label(htxt, text="MatrixExamAI — Tạo đề Toán bằng AI",
                 bg=BLUE, fg="white", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        tk.Label(htxt, text="Phiên bản chưa được kích hoạt",
                 bg=BLUE, fg="#93c5fd", font=("Segoe UI", 11)).pack(anchor="w")

        # ── Bottom bar (luôn hiển thị) ────────────────────────────────────
        bot = tk.Frame(self, bg=BG, pady=12)
        bot.pack(fill="x", side="bottom")
        self._status_lbl = tk.Label(bot,
            text="Chờ admin kích hoạt rồi nhấn Thử lại.",
            bg=BG, fg="#555", font=("Segoe UI", 11))
        self._status_lbl.pack(pady=(0, 8))
        btn_row = tk.Frame(bot, bg=BG)
        btn_row.pack()
        tk.Button(btn_row,
            text="  Thử lại (sau khi admin kích hoạt)  ",
            font=("Segoe UI", 12, "bold"),
            bg=GREEN, fg="white", activebackground=DARK_GREEN,
            relief="flat", cursor="hand2", padx=18, pady=10,
            command=self._retry_check).pack(side="left", padx=(0, 12))
        tk.Button(btn_row,
            text="  Thoát  ",
            font=("Segoe UI", 12),
            bg=RED, fg="white", activebackground="#DC2626",
            relief="flat", cursor="hand2", padx=14, pady=10,
            command=self._on_close).pack(side="left")
        tk.Label(bot, text="Liên hệ admin để được hỗ trợ kích hoạt",
                 bg=BG, fg="#888", font=("Segoe UI", 10)).pack(pady=(8, 0))

        # ── Scrollable body ───────────────────────────────────────────────
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        body = tk.Frame(canvas, bg=BG)
        wid = canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
        body.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        def _wheel(e):
            n = int(-4 * (e.delta / 120))
            if n == 0:
                n = -1 if e.delta > 0 else 1
            canvas.yview_scroll(n, "units")
            return "break"
        canvas.bind("<MouseWheel>", _wheel)
        self.bind("<MouseWheel>", _wheel, add="+")


        # ── Thông báo trạng thái ──────────────────────────────────────────
        status = self._license_result.get("status", "not_found")
        msg_map = {
            "not_found":   ("", "Máy này chưa được đăng ký."),
            "revoked":     ("", "Giấy phép của bạn đã bị thu hồi. Liên hệ admin."),
            "expired":     ("", "Giấy phép đã hết hạn. Vui lòng gia hạn."),
            "maintenance": ("", self._license_result.get("message", "Đang bảo trì.")),
            "error":       ("", f"Lỗi kết nối: {self._license_result.get('message','')}"),
        }
        icon, msg = msg_map.get(status, ("", self._license_result.get("message", "Chưa kích hoạt.")))
        notice = tk.Frame(body, bg="#FEE2E2",
                           highlightbackground="#FCA5A5", highlightthickness=1)
        notice.pack(fill="x", padx=20, pady=(16, 10))
        tk.Label(notice, text=f"  {icon}  {msg}",
                 bg="#FEE2E2", fg="#991B1B",
                 font=("Segoe UI", 13, "bold"), anchor="w").pack(fill="x", padx=12, pady=10)

        # ── Machine ID ────────────────────────────────────────────────────
        self._machine_id = get_machine_id()
        mid_box = tk.Frame(body, bg=LBLUE,
                            highlightbackground="#90CAF9", highlightthickness=1)
        mid_box.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(mid_box, text="  Mã máy tính của bạn (Machine ID):",
                 bg=LBLUE, fg=BLUE, font=("Segoe UI", 12, "bold")).pack(
                     anchor="w", padx=14, pady=(12, 6))
        mid_row = tk.Frame(mid_box, bg=LBLUE)
        mid_row.pack(fill="x", padx=14, pady=(0, 6))
        e = tk.Entry(mid_row, font=("Consolas", 18, "bold"),
                     fg=BLUE, bg="white", relief="solid", bd=1,
                     justify="center", readonlybackground="white", state="readonly")
        e.pack(side="left", fill="x", expand=True, ipady=8)
        e.config(state="normal"); e.insert(0, self._machine_id); e.config(state="readonly")
        tk.Button(mid_row, text="  Sao chép  ",
                  font=("Segoe UI", 10, "bold"),
                  bg="#3B82F6", fg="white", activebackground="#2563EB",
                  relief="flat", cursor="hand2", pady=6,
                  command=lambda: self._copy(self._machine_id)).pack(side="left", padx=(10, 0))
        tk.Label(mid_box, text=f"Máy: {get_machine_display()}",
                 bg=LBLUE, fg="#555", font=("Segoe UI", 10)).pack(
                     anchor="w", padx=14, pady=(0, 10))

        # ══════════════════════════════════════════════════════════════════
        #  BẢNG GIÁ 3 GÓI
        # ══════════════════════════════════════════════════════════════════
        price_section = tk.Frame(body, bg=BG)
        price_section.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(price_section, text="  Chọn gói dịch vụ:",
                 bg=BG, fg=BLUE, font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))

        # 3 cột gói
        cards_frame = tk.Frame(price_section, bg=BG)
        cards_frame.pack(fill="x")
        cards_frame.columnconfigure((0, 1, 2), weight=1)

        self._tier_cards = {}
        self._dur_rows = {}
        self._custom_price_var = tk.StringVar(value="50000")

        # Tìm gói mặc định (hot duration trong Pro)
        _pro = self._pricing.get("pro", {})
        _default_combo = None
        for _d in _pro.get("durations", []):
            if _d.get("hot"):
                _default_combo = f"pro|{_d['duration']}"
                break
        if not _default_combo:
            _durs = _pro.get("durations", [])
            _default_combo = f"pro|{_durs[0]['duration']}" if _durs else "pro|6 tháng"

        for col_idx, (tier_key, tier_data) in enumerate(self._pricing.items()):
            color = tier_data.get("color", "#64748B")
            is_default = (tier_key == "pro")

            # Card container
            card = tk.Frame(cards_frame, bg="white",
                            highlightbackground=color if is_default else "#D1D5DB",
                            highlightthickness=3 if is_default else 1)
            card.grid(row=0, column=col_idx, sticky="nsew", padx=5, pady=2)
            self._tier_cards[tier_key] = card

            # Header gói
            card_hdr = tk.Frame(card, bg=color)
            card_hdr.pack(fill="x")
            name_text = f"{tier_data.get('icon', '')} {tier_data['name']}".strip()
            tk.Label(card_hdr, text=name_text,
                     bg=color, fg="white",
                     font=("Segoe UI", 14, "bold")).pack(pady=(10, 2))
            tk.Label(card_hdr, text=tier_data.get("desc", ""),
                     bg=color, fg="#E5E7EB",
                     font=("Segoe UI", 9)).pack(pady=(0, 8))

            # Recommended badge
            if is_default:
                tk.Label(card_hdr, text="  KHUYÊN DÙNG  ",
                         bg="#FCD34D", fg="#78350F",
                         font=("Segoe UI", 8, "bold")).pack(pady=(0, 6))

            # Tính năng gói
            feat_frame = tk.Frame(card, bg="white")
            feat_frame.pack(fill="x", padx=12, pady=(10, 6))
            for feat in tier_data.get("features", []):
                tk.Label(feat_frame, text=f"  {feat}",
                         bg="white", fg="#374151",
                         font=("Segoe UI", 9), anchor="w").pack(anchor="w", pady=1)

            # Separator
            tk.Frame(card, bg="#E5E7EB", height=1).pack(fill="x", padx=10, pady=6)

            is_custom = tier_data.get("custom_price", False)

            if is_custom:
                # ── BASIC: Nhập giá tùy chọn ──
                combo_val = f"{tier_key}|Tùy chọn"
                is_sel = (combo_val == _default_combo)

                custom_frame = tk.Frame(card, bg="white")
                custom_frame.pack(fill="x", padx=10, pady=4)

                r = tk.Frame(custom_frame, bg="#F0FDF4", cursor="hand2",
                             highlightbackground="#10B981",
                             highlightthickness=2 if is_sel else 0)
                r.pack(fill="x", pady=2)

                ind = tk.Label(r, text="✅" if is_sel else "⬜",
                               bg="#F0FDF4", font=("Segoe UI", 13))
                ind.pack(side="left", padx=(8, 4), pady=8)

                dur_lbl = tk.Label(r, text="Dùng thử", bg="#F0FDF4",
                                   fg="#374151", font=("Segoe UI", 11))
                dur_lbl.pack(side="left", padx=4, pady=8)

                price_lbl = tk.Label(r, text="", bg="#F0FDF4",
                                      fg="#166534", font=("Segoe UI", 10))
                price_lbl.pack(side="right", padx=8, pady=8)

                self._dur_rows[combo_val] = {
                    "frame": r, "indicator": ind,
                    "dur_lbl": dur_lbl, "price_lbl": price_lbl,
                    "hot": False, "tier_key": tier_key,
                }

                def _row_click_basic(e, tkey=tier_key, cv=combo_val):
                    self._on_select(tkey, cv)
                r.bind("<Button-1>", _row_click_basic)
                for w in r.winfo_children():
                    w.bind("<Button-1>", _row_click_basic)

                # Ô nhập giá tiền
                input_frame = tk.Frame(custom_frame, bg="white")
                input_frame.pack(fill="x", pady=(6, 4))

                tk.Label(input_frame, text="Nhập số tiền (VNĐ):",
                         bg="white", fg="#374151",
                         font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=4, pady=(0, 4))

                entry_row = tk.Frame(input_frame, bg="white")
                entry_row.pack(fill="x", padx=4)

                self._custom_entry = tk.Entry(
                    entry_row, textvariable=self._custom_price_var,
                    font=("Segoe UI", 14, "bold"), fg="#166534",
                    justify="center", bd=2, relief="solid",
                    highlightcolor="#10B981", highlightthickness=2)
                self._custom_entry.pack(side="left", fill="x", expand=True, ipady=6)

                tk.Label(entry_row, text=" đ", bg="white", fg="#374151",
                         font=("Segoe UI", 13, "bold")).pack(side="left", padx=(4, 0))

                # Gợi ý nhanh
                suggest_frame = tk.Frame(custom_frame, bg="white")
                suggest_frame.pack(fill="x", padx=4, pady=(4, 2))

                for amt_val, amt_text in [("20000", "20K"), ("50000", "50K"),
                                           ("100000", "100K"), ("200000", "200K")]:
                    def _set_amt(e, v=amt_val):
                        self._custom_price_var.set(v)
                        self._on_select(tier_key, combo_val)
                    btn = tk.Label(suggest_frame, text=amt_text,
                                   bg="#E5E7EB", fg="#374151", cursor="hand2",
                                   font=("Segoe UI", 9, "bold"), padx=10, pady=3)
                    btn.pack(side="left", padx=2)
                    btn.bind("<Button-1>", _set_amt)

                # Khi thay đổi giá → cập nhật QR
                def _on_price_change(*args):
                    if self._selected_tier.get() == "basic":
                        self._update_qr()
                self._custom_price_var.trace_add("write", _on_price_change)

            else:
                # ── PRO / PREMIUM: Bảng giá cố định ──
                durations = tier_data.get("durations", [])
                for dur_item in durations:
                    if not dur_item.get("enabled", True):
                        continue
                    dur = dur_item["duration"]
                    price = dur_item["price"]
                    hot = dur_item.get("hot", False)
                    combo_val = f"{tier_key}|{dur}"
                    is_sel = (combo_val == _default_combo)

                    # Màu nền theo trạng thái
                    if is_sel:
                        row_bg = "#FDE68A" if hot else "#DBEAFE"
                    elif hot:
                        row_bg = "#FEF3C7"
                    else:
                        row_bg = "white"

                    bd_color = ("#F59E0B" if hot else "#3B82F6") if is_sel else ("#FBBF24" if hot else "#E5E7EB")
                    r = tk.Frame(card, bg=row_bg, cursor="hand2",
                                 highlightbackground=bd_color,
                                 highlightthickness=2 if (is_sel or hot) else 0)
                    r.pack(fill="x", padx=6, pady=2)

                    # ✅ / ⬜ chỉ báo chọn
                    ind = tk.Label(r, text="✅" if is_sel else "⬜",
                                   bg=row_bg, font=("Segoe UI", 13))
                    ind.pack(side="left", padx=(8, 4), pady=8)

                    # Tên thời hạn + 🔥
                    dur_text = f"🔥 {dur}" if hot else dur
                    dur_lbl = tk.Label(r, text=dur_text, bg=row_bg,
                                       fg="#92400E" if hot else "#374151",
                                       font=("Segoe UI", 11, "bold" if hot else "normal"))
                    dur_lbl.pack(side="left", padx=4, pady=8)

                    # Badge HOT
                    if hot:
                        tk.Label(r, text=" HOT ", bg="#EF4444", fg="white",
                                 font=("Segoe UI", 7, "bold")).pack(side="left", padx=4, pady=8)

                    # Giá tiền
                    price_lbl = tk.Label(r, text=price, bg=row_bg,
                                          fg="#DC2626" if hot else "#166534",
                                          font=("Segoe UI", 12, "bold"), padx=8)
                    price_lbl.pack(side="right", pady=8)

                    # Lưu reference để cập nhật khi chọn
                    self._dur_rows[combo_val] = {
                        "frame": r, "indicator": ind,
                        "dur_lbl": dur_lbl, "price_lbl": price_lbl,
                        "hot": hot, "tier_key": tier_key,
                    }

                    # Bind click toàn bộ hàng + con
                    def _row_click(e, tkey=tier_key, cv=combo_val):
                        self._on_select(tkey, cv)
                    r.bind("<Button-1>", _row_click)
                    for w in r.winfo_children():
                        w.bind("<Button-1>", _row_click)

            # Padding bottom
            tk.Frame(card, bg="white", height=8).pack()

        # Set default selection
        self._selected_dur.set(_default_combo)
        self._selected_tier.set("pro")

        # ── 2 cột: Bank info + QR ─────────────────────────────────────────
        two_col = tk.Frame(body, bg=BG)
        two_col.pack(fill="x", padx=20, pady=(0, 10))
        two_col.columnconfigure(0, weight=3)
        two_col.columnconfigure(1, weight=2)

        # CỘT TRÁI: Thông tin CK
        bank_card = tk.Frame(two_col, bg="#F0FDF4",
                              highlightbackground="#86EFAC", highlightthickness=1)
        bank_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(bank_card, text="  Thông tin chuyển khoản:",
                 bg="#F0FDF4", fg="#166534",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=14, pady=(12, 8))
        bank_display = list(BANK_INFO)
        bank_display[3] = ("Nội dung CK", f'"{self._machine_id}"')
        for label, value in bank_display:
            r = tk.Frame(bank_card, bg="#F0FDF4"); r.pack(fill="x", padx=14, pady=3)
            tk.Label(r, text=f"{label}:", bg="#F0FDF4", fg="#555",
                     font=("Segoe UI", 11, "bold"), width=16, anchor="w").pack(side="left")
            tk.Label(r, text=value, bg="#F0FDF4", fg="#166534",
                     font=("Consolas", 11, "bold"), anchor="w").pack(side="left")
        tk.Label(bank_card,
                 text="Nội dung CK phải đúng để admin xác nhận.",
                 bg="#F0FDF4", fg="#6B7280",
                 font=("Segoe UI", 10, "italic"), wraplength=320).pack(
                     anchor="w", padx=14, pady=(6, 6))

        # Thông tin liên hệ admin
        sep = tk.Frame(bank_card, bg="#BBF7D0", height=2)
        sep.pack(fill="x", padx=12, pady=(2, 6))
        tk.Label(bank_card, text="  Liên hệ admin:",
                 bg="#F0FDF4", fg="#166534",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14)
        for clbl, cval in ADMIN_CONTACTS:
            cr = tk.Frame(bank_card, bg="#F0FDF4"); cr.pack(fill="x", padx=14, pady=2)
            tk.Label(cr, text=f"{clbl}:", bg="#F0FDF4", fg="#555",
                     font=("Segoe UI", 10, "bold"), width=12, anchor="w").pack(side="left")
            tk.Label(cr, text=cval, bg="#F0FDF4", fg="#166534",
                     font=("Segoe UI", 10), anchor="w").pack(side="left")
        tk.Frame(bank_card, bg="#F0FDF4", height=10).pack()

        # CỘT PHẢI: QR Code
        qr_frame = tk.Frame(two_col, bg="#F8FAFC",
                             highlightbackground="#CBD5E1", highlightthickness=1)
        qr_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(qr_frame,
                 text="  Quét mã QR để thanh toán:",
                 bg="#F8FAFC", fg=BLUE,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 6))

        self._qr_label = tk.Label(qr_frame, bg="#F8FAFC",
                                   text="Đang tải mã QR...",
                                   font=("Segoe UI", 11), fg="#888")
        self._qr_label.pack(padx=14, pady=(0, 6))

        self._qr_info_lbl = tk.Label(qr_frame, bg="#F8FAFC", fg="#374151",
                                      font=("Segoe UI", 10), justify="left",
                                      text="Chọn gói bên trên để tạo mã QR.")
        self._qr_info_lbl.pack(anchor="w", padx=14)
        tk.Label(qr_frame,
                 text="Mở app ngân hàng -> Quét mã QR\n"
                      "Thông tin tài khoản & số tiền được điền sẵn\n"
                      "Chỉ cần xác nhận và gửi",
                 bg="#F8FAFC", fg="#555",
                 font=("Segoe UI", 9), justify="left").pack(anchor="w", padx=14, pady=(6, 12))

        # ── Hướng dẫn ─────────────────────────────────────────────────────
        inst = tk.Frame(body, bg=YELLOW_BG,
                         highlightbackground=YELLOW_BD, highlightthickness=1)
        inst.pack(fill="x", padx=20, pady=(0, 12))
        tk.Label(inst, text="  Hướng dẫn kích hoạt:",
                 bg=YELLOW_BG, fg="#E65100",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(10, 4))
        for step in [
            "1.  Sao chép Mã máy tính ở trên",
            "2.  Chọn gói dịch vụ + thời hạn phù hợp",
            "3.  Quét QR hoặc chuyển khoản thủ công",
            "4.  Gửi Mã máy + ảnh CK cho admin qua Zalo / Email",
            "5.  Sau khi admin kích hoạt -> nhấn Thử lại",
        ]:
            tk.Label(inst, text=f"   {step}", bg=YELLOW_BG, fg="#333",
                     font=("Segoe UI", 11)).pack(anchor="w", padx=14, pady=1)
        tk.Label(inst, text="", bg=YELLOW_BG).pack(pady=3)

        # Tải QR ban đầu (delay đủ để UI render xong)
        self.after(800, self._update_qr)

    # ── Selection handler ───────────────────────────────────────────────
    def _on_select(self, tier_key, combo_val):
        self._selected_tier.set(tier_key)
        self._selected_dur.set(combo_val)

        # Cập nhật visual tất cả hàng thời hạn
        for cv, rd in self._dur_rows.items():
            is_sel = (cv == combo_val)
            hot = rd["hot"]
            is_basic = (rd["tier_key"] == "basic")
            if is_sel:
                bg = "#D1FAE5" if is_basic else ("#FDE68A" if hot else "#DBEAFE")
                bd = "#10B981" if is_basic else ("#F59E0B" if hot else "#3B82F6")
            else:
                bg = "#F0FDF4" if is_basic else ("#FEF3C7" if hot else "white")
                bd = "#A7F3D0" if is_basic else ("#FBBF24" if hot else "#E5E7EB")
            rd["frame"].config(bg=bg, highlightbackground=bd,
                               highlightthickness=2 if (is_sel or hot) else 0)
            rd["indicator"].config(text="✅" if is_sel else "⬜", bg=bg)
            rd["dur_lbl"].config(bg=bg)
            rd["price_lbl"].config(bg=bg)

        # Cập nhật viền card gói
        for tk_key, card in self._tier_cards.items():
            tier_data = self._pricing.get(tk_key, {})
            color = tier_data.get("color", "#64748B")
            if tk_key == tier_key:
                card.config(highlightbackground=color, highlightthickness=3)
            else:
                card.config(highlightbackground="#D1D5DB", highlightthickness=1)

        self._update_qr()

    # ── QR ────────────────────────────────────────────────────────────────
    def _update_qr(self):
        combo = self._selected_dur.get()
        if "|" in combo:
            tier_key, dur = combo.split("|", 1)
        else:
            tier_key, dur = "pro", "6 tháng"

        tier_data = self._pricing.get(tier_key, {})
        is_custom = tier_data.get("custom_price", False)

        if is_custom:
            # Basic — giá tùy chọn
            raw = self._custom_price_var.get().strip()
            amt = "".join(c for c in raw if c.isdigit())
            if not amt or int(amt) <= 0:
                amt = "0"
            # Format hiển thị
            try:
                display_price = f"{int(amt):,.0f} đ".replace(",", ".")
            except ValueError:
                display_price = f"{amt} đ"
            pkg_label = "BASIC Dùng thử"
        else:
            # Pro/Premium — giá cố định
            durations = tier_data.get("durations", [])
            price_str = "199000"
            for d in durations:
                if d["duration"] == dur:
                    price_str = d["price"]
                    break
            amt = price_str.replace(".", "").replace(" đ", "").replace(" d", "").replace(",", "")
            display_price = price_str
            pkg_label = f"{tier_data.get('name', tier_key)} {dur}"

        self._qr_info_lbl.config(
            text=f"Gói: {pkg_label}\n"
                 f"Số tiền: {display_price}\n"
                 f"Nội dung: {self._machine_id}")

        url = _make_vietqr_url(self._machine_id, pkg_label, amt)
        self._qr_label.config(text="Đang tải QR...")
        self.after(100, lambda: self._fetch_qr(url))

    def _fetch_qr(self, url: str):
        """Tải QR trực tiếp (không dùng thread để tránh race condition với Toplevel)."""
        try:
            data = None
            # Ưu tiên requests
            try:
                import requests as _req
                resp = _req.get(url, timeout=12,
                                headers={"User-Agent": "Mozilla/5.0 ExamAI/1.0"},
                                verify=True)
                resp.raise_for_status()
                data = resp.content
            except ImportError:
                pass

            # Fallback urllib
            if data is None:
                import urllib.request, ssl
                ctx = ssl.create_default_context()
                try:
                    import certifi
                    ctx.load_verify_locations(certifi.where())
                except Exception:
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                req = urllib.request.Request(
                    url, headers={"User-Agent": "Mozilla/5.0 ExamAI/1.0"})
                with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
                    data = r.read()

            if not data or len(data) < 500:
                raise ValueError(f"QR response too small: {len(data) if data else 0} bytes")

            from PIL import Image, ImageTk
            import io
            img_orig = Image.open(io.BytesIO(data)).convert("RGBA")
            display_size = 180
            img = img_orig.resize((display_size, display_size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._qr_photo = photo
            self._qr_label.config(image=photo, text="",
                                   width=display_size, height=display_size)
        except Exception as e:
            self._qr_label.config(
                image="",
                text=f"Không tải được QR\nChuyển khoản thủ công\ntheo thông tin bên trái.",
                font=("Segoe UI", 10), fg="#888",
                justify="center")
            print(f"[QR Error] {e}")

    # ── Helpers ───────────────────────────────────────────────────────────
    def _copy(self, text: str):
        self.clipboard_clear(); self.clipboard_append(text)
        messagebox.showinfo("Đã sao chép",
            f"Đã sao chép Mã máy:\n{text}\n\nHãy gửi mã này cho admin.", parent=self)

    def _retry_check(self):
        from services.license_manager import check_license, _clear_cache
        _clear_cache()
        self._status_lbl.config(text="Đang kết nối server...", fg="#555")
        self.update_idletasks()
        try:
            result = check_license(force_online=True)
        except Exception as e:
            self._status_lbl.config(
                text=f"Lỗi kết nối: {str(e)[:60]}",
                fg="#C62828")
            return
        if result.get("ok"):
            self._status_lbl.config(
                text=f"Kích hoạt thành công! Gói: {result.get('tier','?').upper()}",
                fg="#2E7D32")
            self.activated = True
            self.after(1500, self.destroy)
        else:
            self._status_lbl.config(
                text=f"{result.get('message','Chưa được kích hoạt.')}",
                fg="#C62828")

    def _on_close(self):
        if not self.activated:
            if messagebox.askyesno("Thoát",
                "Phần mềm chưa được kích hoạt.\nBạn có chắc muốn thoát không?",
                parent=self):
                self.activated = False; self.destroy()
        else:
            self.destroy()
