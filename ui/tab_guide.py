"""
ui/tab_guide.py — Tab Hướng dẫn sử dụng từng mục MatrixExamAI.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from config import APP_VERSION

BG   = "#F9F7F4"
BLUE = "#1F497D"
CARD = "#FFFFFF"

# Nội dung hướng dẫn từng tab
GUIDES = [
    {
        "tab":   "Cài đặt",
        "icon":  "",
        "color": "#1F497D",
        "steps": [
            ("Chọn nhà cung cấp AI", [
                "Mở tab Cài đặt.",
                "Chọn nhà cung cấp: Google Gemini (khuyên dùng), Anthropic Claude, hoặc DeepSeek.",
                "Chọn mô hình phù hợp:",
                "  - Gemini 2.5 Flash — nhanh, rẻ, phù hợp hầu hết bài toán",
                "  - Gemini 2.5 Pro — mạnh nhất, tốt cho Toán phức tạp",
                "  - Gemini 2.5 Flash-Lite — siêu nhanh, tiết kiệm",
                "  - Gemini 3 Flash / 3.1 Flash-Lite (Preview) — thế hệ mới",
                "  - Claude Sonnet/Opus 4.6 — chất lượng cao, thế hệ mới nhất",
                "  - DeepSeek Chat/Reasoner — giá rẻ, reasoning mạnh",
            ]),
            ("Nhập API Key", [
                "Dán API Key vào ô 'Khóa API'.",
                "Nhấn 'Kiểm tra kết nối' để xác nhận key hợp lệ.",
                "API Key được lưu cục bộ trên máy — không gửi đi đâu khác.",
                "Gói Pro/Premium: Admin sẽ cấp sẵn API Key cho bạn.",
                "Gói Basic: Bạn tự đăng ký API Key tại trang của nhà cung cấp.",
            ]),
            ("Chọn môn và lớp", [
                "Chọn Môn học (Toán, Vật lý, Hóa học,...).",
                "Chọn Lớp (1 đến 12).",
                "Nhập Học kỳ (HK1 / HK2).",
                "Nhập Năm học (VD: 2025-2026).",
                "Nhập Thời gian làm bài (VD: 90 phút).",
            ]),
        ],
    },
    {
        "tab":   "Bảng câu hỏi (Ma trận đề)",
        "icon":  "",
        "color": "#0891B2",
        "steps": [
            ("Thiết lập ma trận đề", [
                "Mở tab Bảng câu hỏi (Ma trận đề thi).",
                "Nhập số lượng câu cho từng loại:",
                "  - TN: Trắc nghiệm nhiều phương án (A/B/C/D)",
                "  - DS: Đúng/Sai (4 ý a/b/c/d)",
                "  - TLN: Trả lời ngắn (điền số hoặc cụm từ)",
                "  - TL: Tự luận (bài toán giải chi tiết)",
                "Phân bổ theo mức độ: Nhận biết (NB), Thông hiểu (TH), Vận dụng (VD).",
                "Tổng điểm tự động tính theo thang 10 — kiểm tra trước khi tạo đề.",
            ]),
            ("Nhập chủ đề", [
                "Thêm các chủ đề/chương muốn ra đề vào danh sách.",
                "Có thể nhập nhiều chủ đề — AI sẽ phân bổ ngẫu nhiên.",
                "Nhập yêu cầu cần đạt để AI tạo câu hỏi sát hơn.",
                "Yêu cầu cần đạt được lưu lại — lần sau tự động gợi ý.",
            ]),
            ("Bật/Tắt từng câu", [
                "Click vào checkbox để bật/tắt từng câu trong ma trận.",
                "Câu bị tắt sẽ không được AI tạo.",
                "Có thể chỉnh sửa trực tiếp nội dung chủ đề, mức độ trên bảng.",
            ]),
        ],
    },
    {
        "tab":   "Tạo đề nhanh",
        "icon":  "",
        "color": "#D97706",
        "steps": [
            ("Cách sử dụng Tạo đề nhanh", [
                "Nhấn nút 'Tạo đề nhanh' trên thanh công cụ.",
                "Cửa sổ Tạo đề nhanh mở ra với 2 tab:",
                "  Tab 1 — Tạo tự động: Chọn lớp + thời lượng để app tự động phân bổ",
                "  Tab 2 — Tạo thủ công: Tự nhập từng câu hỏi vào ma trận",
            ]),
            ("Tab Tạo tự động", [
                "Chọn Lớp (1 đến 12).",
                "Chọn Thời lượng đề thi:",
                "  - 15 phút: 7 câu TN",
                "  - 45 phút: 12 TN + 2 DS + 3 TLN",
                "  - 60 phút: 15 TN + 3 DS + 4 TLN + 1 TL",
                "  - 90 phút: 18 TN + 4 DS + 6 TLN + 2 TL",
                "Chọn chủ đề từ danh sách gợi ý (tự động theo lớp).",
                "Có thể thêm chủ đề mới — chủ đề được lưu lại cho lần sau.",
                "Nhấn 'Tạo ma trận' -> App tự động phân bổ và điền vào bảng.",
            ]),
            ("Sau khi tạo ma trận nhanh", [
                "Kiểm tra lại bảng ma trận, chỉnh sửa nếu cần.",
                "Nhấn 'Tạo đề bằng AI' để bắt đầu tạo câu hỏi.",
                "Quá trình tạo mất 1-5 phút tùy số câu và model AI.",
            ]),
        ],
    },
    {
        "tab":   "Xem đề & Xuất file",
        "icon":  "",
        "color": "#059669",
        "steps": [
            ("Xem đề thi", [
                "Sau khi tạo xong, đề hiển thị ở tab Xem đề.",
                "Câu đúng đáp án hiển thị màu xanh; câu bị lỗi hiển thị màu đỏ.",
                "Điểm chất lượng hiển thị sau mỗi câu nếu đã chạy QC.",
                "Cuộn xuống để xem toàn bộ đề thi.",
            ]),
            ("Xuất Word", [
                "Nhấn 'Xuất Word' để lưu file .docx.",
                "File Word có thể chỉnh sửa tiếp trong Microsoft Word.",
                "Nếu cần PDF: mở file .docx bằng Word → 'File > Save as PDF'.",
                "File được lưu vào thư mục bạn chọn.",
            ]),
            ("Xuất nhiều mã đề", [
                "Nhấn 'Xuất nhiều mã đề' -> Hộp thoại tùy chọn hiện lên.",
                "Chọn số lượng mã đề (2 đến 6 mã đề: A, B, C, D, E, F).",
                "Tùy chọn 'Trộn câu hỏi': Xáo trộn thứ tự câu trong từng phần.",
                "Tùy chọn 'Trộn đáp án': Xáo trộn thứ tự A/B/C/D của câu TN.",
                "Tất cả mã đề được lưu trong thư mục riêng.",
                "Mỗi mã đề có file đề + file đáp án tương ứng.",
            ]),
        ],
    },
    {
        "tab":   "Ngân hàng câu hỏi",
        "icon":  "",
        "color": "#7C3AED",
        "steps": [
            ("Tìm và lọc câu hỏi", [
                "Dùng ô tìm kiếm để lọc theo từ khóa, môn, lớp, loại câu, mức độ.",
                "Nhấn đúp vào câu để xem chi tiết nội dung.",
                "Lọc theo nhiều tiêu chí cùng lúc để tìm câu phù hợp.",
            ]),
            ("Thêm câu vào đề", [
                "Chọn câu hỏi -> nhấn 'Thêm vào đề' để chèn vào đề đang soạn.",
                "Câu từ ngân hàng được gắn cờ nguồn gốc để phân biệt.",
            ]),
            ("Upload lên Cloud", [
                "Chọn câu hỏi -> nhấn 'Upload Cloud' để đồng bộ lên server.",
                "Câu hỏi trên Cloud có thể tải về ở nhiều máy khác nhau.",
                "Chỉ có gói Pro và Premium mới có tính năng Cloud.",
            ]),
            ("Xóa câu chất lượng thấp", [
                "Lọc câu có điểm CL < 0.7 -> chọn và nhấn 'Xóa'.",
                "Nên dọn dẹp định kỳ để giữ ngân hàng chất lượng cao.",
            ]),
        ],
    },
    {
        "tab":   "Kiểm tra chất lượng (QC)",
        "icon":  "",
        "color": "#DC2626",
        "steps": [
            ("Chạy pipeline QC", [
                "Nhấn 'Chạy QC' — AI sẽ đánh giá từng câu theo 6 tiêu chí:",
                "  1. Độ chính xác Toán học (30%)",
                "  2. Giải kép (Double-solve) (25%)",
                "  3. Độ rõ ràng câu hỏi (20%)",
                "  4. Phù hợp mức độ khó (15%)",
                "  5. Định dạng chuẩn (10%)",
                "  6. Không mơ hồ / đa nghĩa (10%)",
                "Quá trình mất 1-3 phút tùy số câu và mô hình AI.",
            ]),
            ("Đọc kết quả QC", [
                "Câu màu xanh (PASS >= 0.9): Đạt chất lượng tốt.",
                "Câu màu vàng (0.8-0.9): Nên xem lại trước khi dùng.",
                "Câu màu đỏ (< 0.8): Có vấn đề, cần chỉnh sửa hoặc tạo lại.",
            ]),
            ("AI Review & Fix", [
                "Chọn câu có vấn đề -> nhấn 'AI Review'.",
                "AI sẽ phân tích lỗi và đề xuất cách sửa.",
                "Nhấn 'Áp dụng sửa' để cập nhật câu hỏi.",
                "Chỉ có gói Premium mới có tính năng này.",
            ]),
        ],
    },
    {
        "tab":   "TikZ vẽ hình",
        "icon":  "",
        "color": "#0891B2",
        "steps": [
            ("Vẽ hình thủ công", [
                "Nhập code TikZ trực tiếp vào editor (có syntax highlighting).",
                "Chọn mẫu có sẵn: tam giác, hình chóp, đường tròn, đồ thị hàm số...",
                "Nhấn Ctrl+Space để mở gợi ý code TikZ (autocomplete).",
                "Nhấn ▶ Render để xem kết quả — hỗ trợ pgfplots cho đồ thị hàm số.",
            ]),
            ("AI vẽ hình tự động", [
                "Nhấn '🤖 AI vẽ hình' — mô tả hình cần vẽ bằng tiếng Việt.",
                "Ví dụ: 'tam giác ABC vuông tại A có đường cao AH'.",
                "Ví dụ: 'đồ thị hàm số y = x^3 - 3x có cực trị'.",
                "AI sẽ tạo code TikZ tự động — nhấn Render để xem.",
            ]),
            ("AI chỉnh sửa code", [
                "Nhấn '✏️ AI chỉnh sửa' để yêu cầu AI sửa code hiện tại.",
                "Ví dụ: 'thêm đường cao AH', 'đổi màu sang đỏ', 'thêm nhãn'.",
                "Code cũ sẽ được thay bằng code AI đã chỉnh sửa.",
            ]),
            ("Xuất hình ảnh", [
                "Copy ảnh: nhấn 📋 Copy ảnh để dán vào Word/PowerPoint.",
                "Lưu PNG: nhấn 💾 Lưu PNG (chất lượng cao, DPI tùy chỉnh 150-600).",
                "Lưu SVG: nhấn 💾 Lưu SVG để chèn vào tài liệu vector.",
                "Lưu EMF hoặc Copy EMF: app chuyển PDF standalone qua Inkscape để dán vào Word không vỡ nét.",
                "Overleaf: mở code trên trình duyệt và copy source .tex dự phòng.",
                "Hình render thành công được tự lưu vào Kho hình; render lại cùng code không tạo bản ghi trùng.",
                "Console bên dưới hiển thị log pdflatex + phân tích lỗi dễ hiểu.",
                "Chỉ có gói Premium mới có tính năng này.",
            ]),
        ],
    },
    {
        "tab":   "Hướng dẫn lấy API Key",
        "icon":  "",
        "color": "#E11D48",
        "steps": [
            ("Google Gemini (khuyên dùng)", [
                "Truy cập: aistudio.google.com",
                "Đăng nhập bằng tài khoản Google.",
                "Nhấn 'Get API key' -> 'Create API key'.",
                "Chọn project hoặc tạo mới -> nhấn 'Create'.",
                "Sao chép API Key (dạng AIzaSy...).",
                "Dán vào ô 'Khóa API' trong tab Cài đặt.",
                "Miễn phí với hạn mức cao — phù hợp cho hầu hết giáo viên.",
            ]),
            ("Anthropic Claude", [
                "Truy cập: console.anthropic.com",
                "Đăng ký tài khoản (cần email + số điện thoại).",
                "Vào Settings -> API Keys -> Create Key.",
                "Sao chép API Key (dạng sk-ant-...).",
                "Dán vào ô 'Khóa API' trong tab Cài đặt.",
                "Cần nạp tiền trước (tối thiểu $5) để sử dụng.",
            ]),
            ("DeepSeek", [
                "Truy cập: platform.deepseek.com",
                "Đăng ký tài khoản.",
                "Vào API Keys -> Create new API key.",
                "Sao chép API Key (dạng sk-...).",
                "Dán vào ô 'Khóa API' trong tab Cài đặt.",
                "Giá rẻ nhất — phù hợp khi cần tiết kiệm chi phí.",
            ]),
            ("Lưu ý quan trọng", [
                "API Key là bí mật — không chia sẻ cho người khác.",
                "App lưu Key cục bộ trên máy bạn, không gửi đi đâu khác.",
                "Gói Pro/Premium: Admin cấp sẵn Key — bạn không cần tự lấy.",
                "Có thể nhập nhiều Key (cách nhau bởi dấu phẩy) để tăng tốc độ.",
                "Nếu gặp lỗi 429 (rate-limit), thêm Key hoặc chờ vài phút.",
            ]),
        ],
    },
    {
        "tab":   "Kích hoạt & Giấy phép",
        "icon":  "",
        "color": "#1F497D",
        "steps": [
            ("Lấy Machine ID", [
                "Mở app — nếu chưa kích hoạt, màn hình kích hoạt sẽ hiện.",
                "Nhấn 'Sao chép' để sao chép Mã máy tính (Machine ID).",
                "Mã máy là duy nhất cho từng máy tính.",
            ]),
            ("Chọn gói dịch vụ", [
                "Có 3 gói dịch vụ: Basic, Pro, Premium.",
                "Mỗi gói có 4 thời hạn: 1 tháng, 3 tháng, 6 tháng, 12 tháng.",
                "Gói Pro (khuyên dùng): Tạo đề nhanh + Ngân hàng + Cloud.",
                "Gói Premium: Toàn quyền + QC + AI Review + TikZ vẽ hình.",
            ]),
            ("Thanh toán & kích hoạt", [
                "Chuyển khoản Vietcombank: 1017919118 — DO HUYNH BINH MINH.",
                "Nội dung chuyển khoản: Mã máy tính của bạn (bắt buộc).",
                "Hoặc quét mã QR trên màn hình kích hoạt (tự động điền thông tin).",
                "Gửi Mã máy + ảnh chuyển khoản cho admin qua Zalo 033.999.8261.",
                "Admin kích hoạt trong vòng 24 giờ (thường trong 1 giờ).",
                "Sau khi admin kích hoạt -> mở lại app hoặc nhấn 'Thử lại'.",
            ]),
            ("Gia hạn giấy phép", [
                "Khi giấy phép hết hạn, màn hình kích hoạt sẽ tự hiện.",
                "Thực hiện lại bước Thanh toán & kích hoạt bên trên.",
                "Machine ID không thay đổi — chỉ cần gửi ảnh CK mới.",
            ]),
        ],
    },
]


class TabGuide(tk.Frame):
    """Tab Hướng dẫn sử dụng — sidebar + nội dung chi tiết."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._active_idx = 0
        self._build()

    def _build(self):
        # ── Header ─────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BLUE)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"  Hướng dẫn sử dụng MatrixExamAI v{APP_VERSION}",
                 bg=BLUE, fg="white",
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=16, pady=10)
        tk.Label(hdr, text="Chọn mục bên trái để xem hướng dẫn chi tiết",
                 bg=BLUE, fg="#93c5fd",
                 font=("Segoe UI", 9)).pack(side="left", padx=4)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # ── Sidebar ──────────────────────────────────────────────────
        sidebar = tk.Frame(body, bg="#E8EDF2", width=300)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Chọn mục:", bg="#E8EDF2", fg="#888",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=4)

        self._nav_buttons = []
        for i, g in enumerate(GUIDES):
            btn = tk.Button(
                sidebar,
                text=f"  {g['icon']}  {g['tab']}" if g['icon'] else f"  {g['tab']}",
                font=("Segoe UI", 9),
                bg="#E8EDF2", fg="#374151",
                activebackground="#D1D9E6",
                relief="flat", cursor="hand2",
                anchor="w", padx=8, pady=7,
                command=lambda idx=i: self._show_guide(idx),
            )
            btn.pack(fill="x")
            self._nav_buttons.append(btn)

        # ── Vùng nội dung (scrollable) ─────────────────────────────
        content_wrap = tk.Frame(body, bg=BG)
        content_wrap.pack(side="left", fill="both", expand=True)

        self._canvas = tk.Canvas(content_wrap, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(content_wrap, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vsb.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        # Scrollbar luôn hiển thị.
        vsb.pack(side="right", fill="y")

        self._content = tk.Frame(self._canvas, bg=BG)
        self._cwin = self._canvas.create_window((0, 0), window=self._content, anchor="nw")

        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._cwin, width=e.width))
        self._content.bind("<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))

        def _scroll(e):
            n = int(-4 * (e.delta / 120))
            if n == 0:
                n = -1 if e.delta > 0 else 1
            self._canvas.yview_scroll(n, "units")
            return "break"
        self._canvas.bind("<MouseWheel>", _scroll)

        self._show_guide(0)

    def _show_guide(self, idx: int):
        self._active_idx = idx
        g = GUIDES[idx]

        # Cập nhật sidebar highlight
        for i, btn in enumerate(self._nav_buttons):
            btn.config(
                bg=g["color"] if i == idx else "#E8EDF2",
                fg="white"     if i == idx else "#374151",
                font=("Segoe UI", 9, "bold") if i == idx else ("Segoe UI", 9),
            )

        # Xóa nội dung cũ
        for w in self._content.winfo_children():
            w.destroy()

        # ── Tiêu đề mục ──────────────────────────────────────────
        title_f = tk.Frame(self._content, bg=g["color"])
        title_f.pack(fill="x", padx=0)
        title_text = f"  {g['icon']}  Hướng dẫn: {g['tab']}" if g['icon'] else f"  Hướng dẫn: {g['tab']}"
        tk.Label(title_f,
                 text=title_text,
                 bg=g["color"], fg="white",
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=14)

        # ── Từng nhóm bước ───────────────────────────────────────
        for step_title, steps in g["steps"]:
            grp = tk.Frame(self._content, bg=CARD,
                            highlightbackground="#E2E8F0", highlightthickness=1)
            grp.pack(fill="x", padx=20, pady=8)

            tk.Label(grp, text=f"  {step_title}",
                     bg="#F8FAFC", fg=BLUE,
                     font=("Segoe UI", 10, "bold"), anchor="w").pack(
                         fill="x", padx=0, pady=0)
            sep = tk.Frame(grp, bg="#E2E8F0", height=1)
            sep.pack(fill="x")

            for n, step in enumerate(steps, 1):
                row = tk.Frame(grp, bg=CARD)
                row.pack(fill="x", padx=12, pady=3)
                # Indent sub-items (starting with spaces or -)
                if step.startswith("  "):
                    tk.Label(row, text="", bg=CARD, width=4).pack(side="left", anchor="n")
                    lbl = tk.Label(row, text=step.strip(), bg=CARD, fg="#555",
                              font=("Segoe UI", 9),
                              anchor="w", justify="left",
                              wraplength=900)
                else:
                    tk.Label(row, text=f" {n}. ", bg=CARD, fg=g["color"],
                              font=("Segoe UI", 10, "bold"), width=4,
                              anchor="ne").pack(side="left", anchor="n")
                    lbl = tk.Label(row, text=step, bg=CARD, fg="#374151",
                              font=("Segoe UI", 10),
                              anchor="w", justify="left",
                              wraplength=900)
                lbl.pack(side="left", fill="x", expand=True, pady=2)
                self._canvas.bind("<Configure>",
                    lambda e, _l=lbl: _l.config(wraplength=max(400, e.width-80)) if _l.winfo_exists() else None, add="+")

        # Khoảng trống cuối
        tk.Frame(self._content, bg=BG, height=20).pack()
        self._canvas.yview_moveto(0)
