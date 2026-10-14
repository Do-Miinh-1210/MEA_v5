"""
ui/tab_about.py — Tab Giới thiệu ứng dụng MatrixExamAI.
Có cuộn chuột, phóng to thu nhỏ, tiếng Việt đầy đủ.
Bảng giá 3 gói (Basic / Pro / Premium) x 4 thời hạn.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"

# ── Bảng màu mới đồng bộ với UI hiện đại ─────────────────────────────
PRIMARY = "#0284C7"  # Xanh dương đậm (Sky 600) - Dùng cho Header & Điểm nhấn chính
ACCENT = "#0EA5E9"   # Xanh Cyan (Sky 500) - Dùng cho các chi tiết phụ
BG = "#F8FAFC"       # Nền tổng thể sáng (Slate 50)
CARD = "#FFFFFF"     # Nền thẻ trắng tinh
TEXT_MAIN = "#334155" # Chữ chính (Slate 700)
TEXT_MUTED = "#64748B" # Chữ phụ (Slate 500)
BORDER = "#E2E8F0"   # Viền (Slate 200)

BANK_INFO = [
    ("Ngân hàng",      "Vietcombank"),
    ("Số tài khoản",   "1017919118"),
    ("Chủ tài khoản",  "DO HUYNH BINH MINH"),
    ("Nội dung CK",    '"MÃ KÍCH HOẠT"'),
]

# Bảng giá 3 gói
PRICING_TIERS = {
    "basic": {
        "name": "BASIC",
        "color": "#64748B", # Slate 500
        "desc": "2 đề/ngày, tự nhập API Key",
        "prices": [
            ("1 tháng", "99.000 ₫"),
            ("3 tháng", "259.000 ₫"),
            ("6 tháng", "479.000 ₫"),
            ("12 tháng", "899.000 ₫"),
        ],
    },
    "pro": {
        "name": "PRO",
        "color": "#0284C7", # Đồng bộ màu xanh Sky 600 mới
        "desc": "Admin cấp API Key, tạo đề nhanh",
        "prices": [
            ("1 tháng", "199.000 ₫"),
            ("3 tháng", "569.000 ₫"),
            ("6 tháng", "1.099.000 ₫"),
            ("12 tháng", "1.999.000 ₫"),
        ],
    },
    "premium": {
        "name": "PREMIUM",
        "color": "#8B5CF6", # Tím Violet 500 cho gói cao cấp nhất
        "desc": "Toàn quyền + API key ưu tiên",
        "prices": [
            ("1 tháng", "299.000 ₫"),
            ("3 tháng", "849.000 ₫"),
            ("6 tháng", "1.599.000 ₫"),
            ("12 tháng", "2.999.000 ₫"),
        ],
    },
}


def _load_logo(parent, size=100, bg=BG):
    try:
        from PIL import Image, ImageTk
        img = Image.open(ASSETS_DIR / "app.png").convert("RGBA").resize(
            (size, size), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        lbl = tk.Label(parent, image=photo, bg=bg)
        lbl.image = photo
        return lbl
    except Exception:
        return tk.Label(parent, text="E", bg=bg, font=("Segoe UI", int(size * 0.38), "bold"), fg=ACCENT)


class TabAbout(tk.Frame):
    """Tab Giới thiệu — cuộn chuột, phóng to thu nhỏ."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._build()

    def _build(self):
        # Scrollable canvas với cuộn chuột
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        # Scrollbar luôn hiển thị.
        vsb.pack(side="right", fill="y")

        inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", _on_resize)
        inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        def _scroll(e):
            n = int(-4 * (e.delta / 120))
            if n == 0:
                n = -1 if e.delta > 0 else 1
            canvas.yview_scroll(n, "units")
            return "break"
        canvas.bind("<MouseWheel>", _scroll)
        inner.bind("<MouseWheel>", _scroll)

        # ── Hero ──────────────────────────────────────────────────────
        # Nền Xanh Pastel nhạt (Sky 100) - Tươi sáng, hiện đại, không trùng logo
        HERO_BG = "#E0F2FE" 
        
        hero = tk.Frame(inner, bg=HERO_BG)
        hero.pack(fill="x")
        
        # Thêm một đường viền mỏng màu xanh Cyan nhạt ở dưới để phân cách mềm mại
        tk.Frame(inner, bg="#BAE6FD", height=2).pack(fill="x", pady=6)

        hero.bind("<MouseWheel>", _scroll)
        _load_logo(hero, size=120, bg=HERO_BG).pack(pady=10)
        
        # Chữ tiêu đề màu xanh biển đậm để tone-sur-tone
        tk.Label(hero, text="MatrixExamAI", bg=HERO_BG, fg="#0369A1",
                 font=("Segoe UI", 28, "bold")).pack()
        
        # Chữ phụ màu xám than (chống mỏi mắt)
        tk.Label(hero,
                 text="Tạo đề kiểm tra Toán bằng Trí tuệ Nhân tạo",
                 bg=HERO_BG, fg="#0F172A", font=("Segoe UI", 13)).pack(pady=0)
        # Lấy version từ config để tránh drift khi bump version sau này
        try:
            from config import APP_VERSION as _APP_VER
        except ImportError:
            _APP_VER = "4.1.0"
        tk.Label(hero, text=f"Phiên bản {_APP_VER}  |  Tác giả: DoMinhMath",
                 bg=HERO_BG, fg="#475569", font=("Segoe UI", 10)).pack(pady=(8, 4))

        tk.Button(hero, text="🔄  Kiểm tra cập nhật",
                  font=("Segoe UI", 9), bg="#0284C7", fg="white",
                  activebackground="#0369A1", relief="flat", cursor="hand2",
                  padx=14, pady=4,
                  command=self._check_update).pack(pady=(0, 16))

        # ── Card helper ──────────────────────────────────────────────
        def card(title, icon=""):
            wrap = tk.Frame(inner, bg=BG)
            wrap.pack(fill="x", padx=28, pady=6)
            wrap.bind("<MouseWheel>", _scroll)
            frm = tk.Frame(wrap, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            frm.pack(fill="x")
            hdr = tk.Label(frm,
                            text=f"  {icon}  {title}" if icon else f"  {title}",
                            bg=CARD, fg=PRIMARY, font=("Segoe UI", 12, "bold"), anchor="w")
            hdr.pack(fill="x", padx=12, pady=4)
            hdr.bind("<MouseWheel>", _scroll)
            sep = tk.Frame(frm, bg=BORDER, height=1)
            sep.pack(fill="x", padx=12)
            content = tk.Frame(frm, bg=CARD)
            content.pack(fill="x", padx=12, pady=12)
            content.bind("<MouseWheel>", _scroll)
            return content

        # ── Giới thiệu chi tiết ──────────────────────────────────────
        c1 = card("Giới thiệu MatrixExamAI")
        intro_text = (
            "MatrixExamAI là phần mềm hỗ trợ giáo viên Toán tạo đề kiểm tra tự động\n"
            "bằng công nghệ AI (Google Gemini / Anthropic Claude / DeepSeek).\n\n"
            "Phần mềm hỗ trợ đầy đủ các dạng câu hỏi theo chuẩn Bộ GD&ĐT:\n"
            "  • Trắc nghiệm nhiều phương án (TN) — 4 lựa chọn A/B/C/D\n"
            "  • Đúng/Sai (DS) — 4 ý a/b/c/d, học sinh chọn Đúng hoặc Sai\n"
            "  • Trả lời ngắn (TLN) — Học sinh điền số hoặc cụm từ ngắn\n"
            "  • Tự luận (TL) — Bài toán giải chi tiết\n\n"
            "MatrixExamAI tự động phân bổ câu hỏi theo 3 mức độ nhận thức:\n"
            "  • Nhận biết (NB): Nhớ, nhận dạng kiến thức cơ bản\n"
            "  • Thông hiểu (TH): Hiểu, giải thích, suy luận\n"
            "  • Vận dụng (VD): Áp dụng kiến thức giải bài toán mới\n\n"
            "Hỗ trợ toàn bộ chương trình Toán từ lớp 1 đến lớp 12."
        )
        lbl = tk.Label(c1, text=intro_text,
            bg=CARD, fg=TEXT_MAIN, font=("Segoe UI", 10), justify="left")
        lbl.pack(anchor="w")
        lbl.bind("<MouseWheel>", _scroll)

        # ── Tính năng chính ──────────────────────────────────────────
        c2 = card("Tính năng chính")
        features = [
            ("Tạo đề tự động",        "Dùng AI tạo đề kiểm tra theo ma trận chuẩn BGD"),
            ("Tạo đề nhanh",          "Chọn lớp (1–12) + thời lượng → tự động phân bổ câu hỏi"),
            ("Bảng ma trận",          "Thiết lập cấu trúc đề: số câu TN/DS/TLN/TL, mức độ NB/TH/VD"),
            ("Nhiều mã đề",           "Trộn thứ tự câu hỏi theo phần + trộn đáp án TN"),
            ("Ngân hàng câu hỏi",     "Lưu SQLite cục bộ + đồng bộ Cloud (Supabase)"),
            ("Kiểm tra chất lượng",   "Pipeline QC 6 tiêu chí, AI đánh giá tự động"),
            ("Xuất đề Word",          "Xuất file .docx với định dạng chuẩn (mở bằng Word để in/PDF)"),
            ("AI Review & Fix",       "AI tự kiểm tra và sửa lỗi câu hỏi"),
            ("TikZ vẽ hình + AI",     "Vẽ hình toán học, AI vẽ tự động, đồ thị pgfplots"),
            ("Quản lý giấy phép",     "3 gói dịch vụ: Basic / Pro / Premium"),
        ]
        for title, desc in features:
            row = tk.Frame(c2, bg=CARD)
            row.pack(fill="x", pady=3)
            row.bind("<MouseWheel>", _scroll)
            tk.Label(row, text=f"{title}:", bg=CARD, fg=PRIMARY,
                     font=("Segoe UI", 10, "bold"), width=22, anchor="w").pack(side="left")
            lbl2 = tk.Label(row, text=desc, bg=CARD, fg=TEXT_MUTED,
                             font=("Segoe UI", 9), anchor="w")
            lbl2.pack(side="left")
            lbl2.bind("<MouseWheel>", _scroll)

        # ── Hướng dẫn sử dụng nhanh ──────────────────────────────────
        c_guide = card("Hướng dẫn sử dụng nhanh")
        steps = [
            "Bước 1: Kích hoạt giấy phép",
            "  • Mở app → Màn hình kích hoạt hiện lên",
            "  • Sao chép Mã máy (Machine ID)",
            "  • Chuyển khoản theo bảng giá + gửi Mã máy cho admin",
            "  • Admin kích hoạt → nhấn 'Thử lại'",
            "",
            "Bước 2: Cài đặt AI Provider",
            "  • Tab 'Cài đặt' → Chọn nhà cung cấp: Gemini / Claude / DeepSeek",
            "  • Nhập API Key → Nhấn 'Kiểm tra kết nối'",
            "  • Chọn Môn học, Lớp, Học kỳ, Năm học",
            "",
            "Bước 3: Tạo đề kiểm tra",
            "  a) Cách 1 — Tạo đề thủ công:",
            "     Tab 'Bảng câu hỏi' → Nhập số lượng câu theo loại và mức độ",
            "     → Nhấn 'Tạo đề bằng AI'",
            "  b) Cách 2 — Tạo đề nhanh:",
            "     Nhấn 'Tạo đề nhanh' → Chọn lớp + thời lượng (15/45/60/90 phút)",
            "     → Chọn chủ đề → App tự động phân bổ và tạo đề",
            "",
            "Bước 4: Xem và xuất đề",
            "  • Tab 'Xem đề & Xuất' → Xem preview toàn bộ đề thi",
            "  • Nhấn 'Xuất Word' (mở bằng MS Word nếu cần in/PDF)",
            "  • Nhấn 'Xuất nhiều mã đề' → Chọn số lượng + tùy chọn trộn",
            "",
            "Bước 5: Quản lý ngân hàng câu hỏi",
            "  • Tab 'Ngân hàng' → Tìm kiếm, lọc, tái sử dụng câu hỏi",
            "  • Upload lên Cloud để đồng bộ giữa các máy",
            "",
            "Bước 6: Kiểm tra chất lượng (Premium)",
            "  • Tab 'QC' → Nhấn 'Chạy QC' → AI đánh giá từng câu",
            "  • Kết quả: PASS / Cần xem lại / Loại",
        ]
        for step in steps:
            if step == "":
                tk.Frame(c_guide, bg=CARD, height=6).pack()
                continue
            is_header = step.startswith("Bước")
            l = tk.Label(c_guide, text=f"  {step}", bg=CARD,
                         fg=PRIMARY if is_header else TEXT_MAIN,
                         font=("Segoe UI", 10, "bold" if is_header else "normal"),
                         anchor="w")
            l.pack(fill="x")
            l.bind("<MouseWheel>", _scroll)

        # ══════════════════════════════════════════════════════════════
        #  BẢNG GIÁ DỊCH VỤ
        # ══════════════════════════════════════════════════════════════
        c3 = card("Bảng giá dịch vụ")

        # ── Bảng so sánh tính năng ────────────────────────────────────
        tk.Label(c3, text="So sánh tính năng các gói:",
                 bg=CARD, fg=PRIMARY, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=8)

        feat_compare = [
            ("Tạo đề (Bảng câu hỏi)",         True,  True,  True),
            ("Xem đề & Xuất Word",             True,  True,  True),
            ("Tạo đề nhanh (lớp 1–12)",        False, True,  True),
            ("Ngân hàng câu hỏi",              False, True,  True),
            ("NHCH Cloud (đồng bộ)",            False, True,  True),
            ("Nhiều mã đề (trộn đề)",           False, False, True),
            ("Kiểm tra chất lượng (QC)",        False, False, True),
            ("AI Review & Fix",                 False, False, True),
            ("TikZ vẽ hình + AI vẽ hình",       False, False, True),
        ]

        # Treeview-style table using grid
        table = tk.Frame(c3, bg=BORDER)
        table.pack(fill="x", pady=4)
        table.bind("<MouseWheel>", _scroll)

        # Column config: feature=wide, 3 tiers=equal
        table.columnconfigure(0, weight=4, minsize=250)
        table.columnconfigure(1, weight=1, minsize=90)
        table.columnconfigure(2, weight=1, minsize=90)
        table.columnconfigure(3, weight=1, minsize=90)

        # Header row
        hdr_bg = "#0F172A" # Dark Slate
        tk.Label(table, text="  Tính năng", bg=hdr_bg, fg="white",
                 font=("Segoe UI", 10, "bold"), anchor="w",
                 padx=10, pady=8).grid(row=0, column=0, sticky="nsew")
        for ci, (name, color) in enumerate([
            ("Basic", "#64748B"), ("Pro", "#0284C7"), ("Premium", "#8B5CF6")
        ], 1):
            tk.Label(table, text=name, bg=color, fg="white",
                     font=("Segoe UI", 10, "bold"),
                     padx=8, pady=8).grid(row=0, column=ci, sticky="nsew", padx=0)

        # Data rows
        for ri, (feat_name, basic, pro, prem) in enumerate(feat_compare, 1):
            rbg = "#F8FAFC" if ri % 2 == 1 else "#FFFFFF"
            # Feature name
            tk.Label(table, text=f"  {feat_name}", bg=rbg, fg=TEXT_MAIN,
                     font=("Segoe UI", 10), anchor="w",
                     padx=10, pady=6).grid(row=ri, column=0, sticky="nsew")
            # Checkmarks
            for ci, val in enumerate([basic, pro, prem], 1):
                txt = "✅" if val else "❌"
                cell_bg = rbg
                tk.Label(table, text=txt, bg=cell_bg,
                         font=("Segoe UI", 11),
                         pady=6).grid(row=ri, column=ci, sticky="nsew", padx=0)

        # Separator
        tk.Frame(c3, bg=CARD, height=16).pack()

        # ── Bảng giá từng gói ────────────────────────────────────────
        tk.Label(c3, text="Chi phí theo thời hạn:",
                 bg=CARD, fg=PRIMARY, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=8)

        price_grid = tk.Frame(c3, bg=CARD)
        price_grid.pack(fill="x")
        price_grid.columnconfigure((0, 1, 2), weight=1)

        for col_idx, (tier_key, tier_data) in enumerate(PRICING_TIERS.items()):
            color = tier_data["color"]
            f = tk.Frame(price_grid, bg="white",
                         highlightbackground=color, highlightthickness=2)
            f.grid(row=0, column=col_idx, sticky="nsew", padx=4, pady=2)
            f.bind("<MouseWheel>", _scroll)

            # Tier header
            tk.Label(f, text=tier_data["name"],
                     bg=color, fg="white",
                     font=("Segoe UI", 12, "bold")).pack(fill="x", pady=8)
            tk.Label(f, text=tier_data["desc"],
                     bg="white", fg=TEXT_MUTED,
                     font=("Segoe UI", 9)).pack(pady=8)

            # Prices
            for dur, price in tier_data["prices"]:
                r = tk.Frame(f, bg="white")
                r.pack(fill="x", padx=10, pady=3)
                r.bind("<MouseWheel>", _scroll)
                tk.Label(r, text=dur, bg="white", fg=TEXT_MAIN,
                         font=("Segoe UI", 10), anchor="w").pack(side="left")
                tk.Label(r, text=price, bg="white", fg=color,
                         font=("Segoe UI", 10, "bold"), anchor="e").pack(side="right")

            tk.Frame(f, bg="white", height=8).pack()

        # ── Liên hệ admin ────────────────────────────────────────────
        c_contact = card("Liên hệ & Hỗ trợ")
        contacts = [
            ("📱 Zalo/SĐT",  "033.999.8261"),
            ("📧 Gmail",     "domiinh.369@gmail.com"),
        ]
        for clbl, cval in contacts:
            row = tk.Frame(c_contact, bg=CARD); row.pack(fill="x", pady=2)
            row.bind("<MouseWheel>", _scroll)
            tk.Label(row, text=f"{clbl}:", bg=CARD, fg=TEXT_MUTED,
                     font=("Segoe UI", 10, "bold"), width=13, anchor="w").pack(side="left")
            lbl_c = tk.Label(row, text=cval, bg=CARD, fg=PRIMARY,
                              font=("Segoe UI", 10), anchor="w")
            lbl_c.pack(side="left")
            lbl_c.bind("<MouseWheel>", _scroll)

        # ── Thông tin chuyển khoản ────────────────────────────────────
        c4 = card("Thông tin chuyển khoản")
        for label, value in BANK_INFO:
            row = tk.Frame(c4, bg=CARD)
            row.pack(fill="x", pady=2)
            row.bind("<MouseWheel>", _scroll)
            tk.Label(row, text=f"{label}:", bg=CARD, fg=TEXT_MUTED,
                     font=("Segoe UI", 10, "bold"), width=15, anchor="w").pack(side="left")
            lbl3 = tk.Label(row, text=value, bg=CARD, fg=PRIMARY,
                             font=("Consolas", 10, "bold"), anchor="w")
            lbl3.pack(side="left")
            lbl3.bind("<MouseWheel>", _scroll)
        note = tk.Label(c4,
            text="⚠️  Nội dung chuyển khoản phải điền đúng để admin xác nhận và kích hoạt.",
            bg=CARD, fg=TEXT_MUTED, font=("Segoe UI", 8, "italic"))
        note.pack(anchor="w", pady=0)
        note.bind("<MouseWheel>", _scroll)

        # ── Yêu cầu hệ thống ─────────────────────────────────────────
        #c5 = card("Yêu cầu hệ thống")
        #for req in [
        #    "Windows 10/11 (64-bit)",
        #    "Kết nối Internet (để gọi AI & kiểm tra giấy phép)",
        #    "API Key: Google Gemini, Anthropic Claude, hoặc DeepSeek",
        #    "Khi chạy từ source: Python 3.9+, các thư viện trong requirements.txt",
        #]:
        #    l = tk.Label(c5, text=f"  •  {req}", bg=CARD, fg=TEXT_MAIN,
        #                  font=("Segoe UI", 9), anchor="w")
        #    l.pack(fill="x")
        #    l.bind("<MouseWheel>", _scroll)

        # ── Footer ────────────────────────────────────────────────────
        footer = tk.Frame(inner, bg="#F1F5F9")
        footer.pack(fill="x", pady=0)
        footer.bind("<MouseWheel>", _scroll)
        tk.Label(footer,
                 text=f"© 2026 DoMinhMath — MatrixExamAI v{_APP_VER}  |  Bảo lưu mọi quyền",
                 bg="#F1F5F9", fg=TEXT_MUTED, font=("Segoe UI", 8)).pack(pady=12)

    def _check_update(self):
        """Mở dialog kiểm tra cập nhật thủ công."""
        from config import APP_VERSION
        from ui.dialog_update import CheckUpdateDialog
        CheckUpdateDialog(self.winfo_toplevel(), current_version=APP_VERSION)
