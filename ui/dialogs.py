"""
ui/activation_dialog.py — Dialog kích hoạt app ExamAI.
- Logo, 2 cột: bank info + bảng giá
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
    ("📱 Zalo/SĐT",  "033.999.8261"),
    ("📧 Gmail",     "domiinh.369@gmail.com"),
]
DEFAULT_PRICING = [
    {"period": "1 tháng",  "price": "199.000 ₫",    "hot": False, "enabled": True},
    {"period": "3 tháng",  "price": "569.000 ₫",    "hot": False, "enabled": True},
    {"period": "6 tháng",  "price": "1.099.000 ₫",  "hot": True,  "enabled": True},
    {"period": "12 tháng", "price": "2.099.000 ₫",  "hot": False, "enabled": True},
]


def _fetch_pricing_from_db() -> list[dict]:
    """Lấy bảng giá từ Supabase settings. Trả về list dict hoặc None nếu lỗi."""
    try:
        import json
        from services.license_manager import admin_get_settings
        settings = admin_get_settings()
        if settings and "pricing" in settings:
            items = json.loads(settings["pricing"])
            if isinstance(items, list) and items:
                return items
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
        return tk.Label(parent, text="🎓", bg=bg, fg="white",
                        font=("Segoe UI", int(size * 0.45)))


def _make_vietqr_url(machine_id: str, pkg: str, amount: str) -> str:
    """Tạo URL VietQR độ phân giải cao để hiển thị rõ nét."""
    bank_id  = "VCB"
    acc_no   = "1017919118"
    acc_name = "DO HUYNH BINH MINH"
    content  = urllib.parse.quote(f"{machine_id} {pkg}")
    amt      = amount.replace(".", "").replace(" ₫", "").replace(",", "")
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
        self._pricing = _fetch_pricing_from_db() or DEFAULT_PRICING
        self._active_pricing = [p for p in self._pricing if p.get("enabled", True)]
        default_pkg = next(
            (p["period"] for p in self._active_pricing if p.get("hot")),
            self._active_pricing[0]["period"] if self._active_pricing else "6 tháng"
        )
        self._selected_pkg = tk.StringVar(value=default_pkg)
        self._build()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.resizable(True, True)
        self.minsize(780, 700)
        self.focus_force()

    def _build(self):
        from services.license_manager import get_machine_id, get_machine_display
        self.title("🔐 Kích hoạt phần mềm — ExamAI")
        self.configure(bg=BG)
        W, H = 880, 860
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BLUE)
        hdr.pack(fill="x", side="top")
        _load_logo(hdr, size=60, bg=BLUE).pack(side="left", padx=(18, 10), pady=10)
        htxt = tk.Frame(hdr, bg=BLUE)
        htxt.pack(side="left", pady=10)
        tk.Label(htxt, text="MatrixExamAI — Tạo đề kiểm tra THCS/THPT bằng AI",
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
            text="  🔄  Thử lại (sau khi admin kích hoạt)  ",
            font=("Segoe UI", 12, "bold"),
            bg=GREEN, fg="white", activebackground=DARK_GREEN,
            relief="flat", cursor="hand2", padx=18, pady=10,
            command=self._retry_check).pack(side="left", padx=(0, 12))
        tk.Button(btn_row,
            text="  ✖  Thoát  ",
            font=("Segoe UI", 12),
            bg=RED, fg="white", activebackground="#DC2626",
            relief="flat", cursor="hand2", padx=14, pady=10,
            command=self._on_close).pack(side="left")
        tk.Label(bot, text="📞 Liên hệ admin để được hỗ trợ kích hoạt",
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
            "not_found":   ("🔒", "Máy này chưa được đăng ký."),
            "revoked":     ("⛔", "Giấy phép của bạn đã bị thu hồi. Liên hệ admin."),
            "expired":     ("⏰", "Giấy phép đã hết hạn. Vui lòng gia hạn."),
            "maintenance": ("🔧", self._license_result.get("message", "Đang bảo trì.")),
            "error":       ("⚠️", f"Lỗi kết nối: {self._license_result.get('message','')}"),
        }
        icon, msg = msg_map.get(status, ("🔒", self._license_result.get("message", "Chưa kích hoạt.")))
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
        tk.Label(mid_box, text="📋  Mã máy tính của bạn (Machine ID):",
                 bg=LBLUE, fg=BLUE, font=("Segoe UI", 12, "bold")).pack(
                     anchor="w", padx=14, pady=(12, 6))
        mid_row = tk.Frame(mid_box, bg=LBLUE)
        mid_row.pack(fill="x", padx=14, pady=(0, 6))
        e = tk.Entry(mid_row, font=("Consolas", 18, "bold"),
                     fg=BLUE, bg="white", relief="solid", bd=1,
                     justify="center", readonlybackground="white", state="readonly")
        e.pack(side="left", fill="x", expand=True, ipady=8)
        e.config(state="normal"); e.insert(0, self._machine_id); e.config(state="readonly")
        tk.Button(mid_row, text="  📋 Sao chép  ",
                  font=("Segoe UI", 10, "bold"),
                  bg="#3B82F6", fg="white", activebackground="#2563EB",
                  relief="flat", cursor="hand2", pady=6,
                  command=lambda: self._copy(self._machine_id)).pack(side="left", padx=(10, 0))
        from services.license_manager import get_machine_display
        tk.Label(mid_box, text=f"Máy: {get_machine_display()}",
                 bg=LBLUE, fg="#555", font=("Segoe UI", 10)).pack(
                     anchor="w", padx=14, pady=(0, 10))

        # ── 2 cột: Bank + Giá ────────────────────────────────────────────
        two_col = tk.Frame(body, bg=BG)
        two_col.pack(fill="x", padx=20, pady=(0, 10))
        two_col.columnconfigure(0, weight=3)
        two_col.columnconfigure(1, weight=2)

        # CỘT TRÁI: Thông tin CK
        bank_card = tk.Frame(two_col, bg="#F0FDF4",
                              highlightbackground="#86EFAC", highlightthickness=1)
        bank_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(bank_card, text="💳  Thông tin chuyển khoản:",
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
                 text="⚠️ Nội dung CK phải đúng để admin xác nhận.",
                 bg="#F0FDF4", fg="#6B7280",
                 font=("Segoe UI", 9, "italic"), wraplength=320).pack(
                     anchor="w", padx=14, pady=(6, 6))

        # Thông tin liên hệ admin
        sep = tk.Frame(bank_card, bg="#BBF7D0", height=2)
        sep.pack(fill="x", padx=12, pady=(2, 6))
        tk.Label(bank_card, text="📞  Liên hệ admin:",
                 bg="#F0FDF4", fg="#166534",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14)
        for clbl, cval in ADMIN_CONTACTS:
            cr = tk.Frame(bank_card, bg="#F0FDF4"); cr.pack(fill="x", padx=14, pady=2)
            tk.Label(cr, text=f"{clbl}:", bg="#F0FDF4", fg="#555",
                     font=("Segoe UI", 10, "bold"), width=12, anchor="w").pack(side="left")
            tk.Label(cr, text=cval, bg="#F0FDF4", fg="#166534",
                     font=("Segoe UI", 10), anchor="w").pack(side="left")
        tk.Frame(bank_card, bg="#F0FDF4", height=10).pack()

        # CỘT PHẢI: Bảng giá
        price_card = tk.Frame(two_col, bg="#FFF7ED",
                               highlightbackground="#FDBA74", highlightthickness=1)
        price_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(price_card, text="🔥  Chi phí sử dụng:",
                 bg="#FFF7ED", fg="#9A3412",
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=14, pady=(12, 8))
        th = tk.Frame(price_card, bg="#EA580C")
        th.pack(fill="x", padx=10, pady=(0, 3))
        tk.Label(th, text="Gói", bg="#EA580C", fg="white",
                 font=("Segoe UI", 11, "bold"), width=10, anchor="w",
                 padx=8, pady=5).pack(side="left")
        tk.Label(th, text="Chi phí  ", bg="#EA580C", fg="white",
                 font=("Segoe UI", 11, "bold"), anchor="e",
                 padx=8, pady=5).pack(side="right", fill="x", expand=True)
        for item in self._active_pricing:
            period = item["period"]
            price  = item["price"]
            hot    = item.get("hot", False)
            row_bg = "#FED7AA" if hot else "#FFEDD5"
            r = tk.Frame(price_card, bg=row_bg)
            r.pack(fill="x", padx=10, pady=1)
            rb = tk.Radiobutton(r, text=f"{'🔥 ' if hot else '   '}{period}",
                                 variable=self._selected_pkg, value=period,
                                 bg=row_bg, fg="#7C2D12" if hot else "#374151",
                                 font=("Segoe UI", 11, "bold" if hot else "normal"),
                                 activebackground=row_bg, anchor="w",
                                 indicatoron=True,
                                 command=self._update_qr)
            rb.pack(side="left", padx=6, pady=6)
            tk.Label(r, text=price, bg=row_bg, fg="#C2410C" if hot else "#166534",
                     font=("Segoe UI", 12, "bold"), anchor="e",
                     padx=8).pack(side="right")
        tk.Label(price_card, text="✅ Thanh toán 1 lần, dùng ngay",
                 bg="#FFF7ED", fg="#9A3412",
                 font=("Segoe UI", 9, "italic")).pack(anchor="w", padx=12, pady=(6, 12))

        # ── QR Code ───────────────────────────────────────────────────────
        qr_frame = tk.Frame(body, bg="#F8FAFC",
                             highlightbackground="#CBD5E1", highlightthickness=1)
        qr_frame.pack(fill="x", padx=20, pady=(0, 10))
        tk.Label(qr_frame,
                 text="📱  Quét mã QR để thanh toán (cập nhật theo gói được chọn):",
                 bg="#F8FAFC", fg=BLUE,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 6))

        qr_inner = tk.Frame(qr_frame, bg="#F8FAFC")
        qr_inner.pack(padx=14, pady=(0, 12))

        self._qr_label = tk.Label(qr_inner, bg="#F8FAFC",
                                   text="⏳ Đang tải mã QR...",
                                   font=("Segoe UI", 11), fg="#888")
        self._qr_label.pack(side="left", padx=(0, 20))

        qr_info = tk.Frame(qr_inner, bg="#F8FAFC")
        qr_info.pack(side="left", anchor="w")
        self._qr_info_lbl = tk.Label(qr_info, bg="#F8FAFC", fg="#374151",
                                      font=("Segoe UI", 11), justify="left",
                                      text="Chọn gói bên trên để tạo mã QR.")
        self._qr_info_lbl.pack(anchor="w")
        tk.Label(qr_info,
                 text="• Mở app ngân hàng → Quét mã QR\n"
                      "• Thông tin tài khoản & số tiền được điền sẵn\n"
                      "• Chỉ cần xác nhận và gửi",
                 bg="#F8FAFC", fg="#555",
                 font=("Segoe UI", 10), justify="left").pack(anchor="w", pady=(6, 0))

        # ── Hướng dẫn ─────────────────────────────────────────────────────
        inst = tk.Frame(body, bg=YELLOW_BG,
                         highlightbackground=YELLOW_BD, highlightthickness=1)
        inst.pack(fill="x", padx=20, pady=(0, 12))
        tk.Label(inst, text="📌  Hướng dẫn kích hoạt:",
                 bg=YELLOW_BG, fg="#E65100",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(10, 4))
        for step in [
            "1️⃣   Sao chép Mã máy tính ở trên",
            "2️⃣   Chọn gói → Quét QR hoặc chuyển khoản thủ công",
            "3️⃣   Gửi Mã máy + ảnh CK cho admin qua Zalo / Email",
            "4️⃣   Sau khi admin kích hoạt → nhấn Thử lại",
        ]:
            tk.Label(inst, text=f"   {step}", bg=YELLOW_BG, fg="#333",
                     font=("Segoe UI", 11)).pack(anchor="w", padx=14, pady=1)
        tk.Label(inst, text="", bg=YELLOW_BG).pack(pady=3)

        # Tải QR ban đầu
        self.after(300, self._update_qr)

    # ── QR ────────────────────────────────────────────────────────────────────
    def _update_qr(self):
        pkg = self._selected_pkg.get()
        amt_map = {p["period"]: p["price"].replace(".", "").replace(" ₫", "")
                   for p in self._active_pricing}
        amt = amt_map.get(pkg, "199000")
        # Hiển thị đầy đủ machine_id, không cắt ngắn
        self._qr_info_lbl.config(
            text=f"Gói đã chọn: {pkg}\n"
                 f"Số tiền: {amt} VNĐ\n"
                 f"Nội dung: {self._machine_id}")

        url = _make_vietqr_url(self._machine_id, pkg, amt)
        self._qr_label.config(text="⏳ Đang tải QR...")
        self.after(100, lambda: self._fetch_qr(url))

    def _fetch_qr(self, url: str):
        try:
            import urllib.request
            from PIL import Image, ImageTk
            import io
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 ExamAI/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = r.read()
            img_orig = Image.open(io.BytesIO(data)).convert("RGBA")
            display_size = 180
            img = img_orig.resize((display_size, display_size), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._qr_photo = photo
            self._qr_label.config(image=photo, text="",
                                   width=display_size, height=display_size)
        except Exception as exc:
            self._qr_label.config(
                image="",
                text="📱 Không tải được QR\nChuyển khoản thủ công theo\nthông tin bên trái.",
                font=("Segoe UI", 10), fg="#888",
                justify="center")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _copy(self, text: str):
        self.clipboard_clear(); self.clipboard_append(text)
        messagebox.showinfo("Đã sao chép",
            f"Đã sao chép Mã máy:\n{text}\n\nHãy gửi mã này cho admin.", parent=self)

    def _retry_check(self):
        from services.license_manager import check_license, _clear_cache
        _clear_cache()
        self._status_lbl.config(text="⏳ Đang kết nối server...", fg="#555")
        self.update_idletasks()
        try:
            result = check_license(force_online=True)
        except Exception as e:
            self._status_lbl.config(
                text=f"❌ Lỗi kết nối: {str(e)[:60]}",
                fg="#C62828")
            return
        if result.get("ok"):
            self._status_lbl.config(
                text=f"✅ Kích hoạt thành công! Gói: {result.get('tier','?').upper()}",
                fg="#2E7D32")
            self.activated = True
            self.after(1500, self.destroy)
        else:
            self._status_lbl.config(
                text=f"❌ {result.get('message','Chưa được kích hoạt.')}",
                fg="#C62828")

    def _on_close(self):
        if not self.activated:
            if messagebox.askyesno("Thoát",
                "Phần mềm chưa được kích hoạt.\nBạn có chắc muốn thoát không?",
                parent=self):
                self.activated = False; self.destroy()
        else:
            self.destroy()