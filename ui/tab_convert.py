"""
ui/tab_convert.py — Tab "Convert": Chuyển đổi ảnh → văn bản / câu hỏi.
Hỗ trợ: Paste ảnh (Ctrl+V), upload ảnh, PDF → Word (giữ hình ảnh).
Dùng AI Vision (Gemini / Claude) để OCR ảnh thành text có cấu trúc.
"""

from __future__ import annotations
import base64
import io
import logging
import os
import re
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Any, Callable, Optional

from ui.theme import C, FONT, PAD

_log = logging.getLogger(__name__)

# ── Colours ──────────────────────────────────────────────────────────────────
BG       = C["bg"]           # "#F8FAFC"
SURFACE  = C["surface"]      # "#FFFFFF"
PRIMARY  = C["primary"]      # "#0284C7"
BORDER   = C["border"]       # "#CBD5E1"
TEXT     = C["text_main"]    # "#1E293B"
HINT     = C["text_hint"]    # "#94A3B8"



def _has_matching_outer_braces(s: str) -> bool:
    """Kiểm tra chuỗi có được bọc bởi cặp ngoặc nhọn { ... } ngoài cùng cân bằng hay không."""
    s = s.strip()
    if not (s.startswith("{") and s.endswith("}")):
        return False
    depth = 0
    for i, c in enumerate(s):
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i == len(s) - 1
    return False


def normalize_math_to_braced_dollars(text: str) -> str:
    r"""Chuẩn hóa mọi công thức toán học về dạng chuẩn ${...}$ (có ngoặc nhọn bên trong $).

    Quy tắc:
      - \( ... \)  → ${...}$
      - \[ ... \]  → ${...}$
      - $$ ... $$  → ${...}$
      - $ ... $    → ${...}$ (nếu chưa có { } ngoài cùng)
    Không bọc lặp nếu biểu thức đã có dạng chuẩn ${...}$.
    """
    if not text:
        return text

    def _replace_latex_bracket(m):
        inner = m.group(1).strip()
        if _has_matching_outer_braces(inner):
            return f"${inner}$"
        return f"${{{inner}}}$"

    # 1. LaTeX \( ... \) và \[ ... \]
    text = re.sub(r"\\\[(.*?)\\\]", _replace_latex_bracket, text, flags=re.DOTALL)
    text = re.sub(r"\\\((.*?)\\\)", _replace_latex_bracket, text, flags=re.DOTALL)

    # 2. Block math $$ ... $$
    def _replace_double_dollar(m):
        inner = m.group(1).strip()
        if _has_matching_outer_braces(inner):
            return f"${inner}$"
        return f"${{{inner}}}$"

    text = re.sub(r"\$\$(.*?)\$\$", _replace_double_dollar, text, flags=re.DOTALL)

    # 3. Inline math $ ... $
    def _replace_single_dollar(m):
        inner = m.group(1).strip()
        if not inner:
            return "$$"
        if _has_matching_outer_braces(inner):
            return f"${inner}$"
        return f"${{{inner}}}$"

    text = re.sub(r"\$([^$\n]+?)\$", _replace_single_dollar, text)
    return text


def _mask_math_pipes(s: str) -> tuple[str, dict[str, str]]:
    """Thay thế tạm thời ký tự '|' nằm bên trong công thức toán học (${...}$, $...$, $$...$$)."""
    math_tokens = {}
    counter = 0

    def _mask_match(m):
        nonlocal counter
        content = m.group(0)
        if "|" in content:
            key = f"__PIPE_MATH_{counter}__"
            counter += 1
            math_tokens[key] = content
            return key
        return content

    masked = re.sub(r"\$\$.*?\$\$|\$[^$\n]+?\$|\\\[.*?\\\]|\\\(.*?\\\)", _mask_match, s, flags=re.DOTALL)
    return masked, math_tokens


# ══════════════════════════════════════════════════════════════════════════════
#  PROMPT — yêu cầu AI trả text có cấu trúc
# ══════════════════════════════════════════════════════════════════════════════

# Hint cho prompt khi user chọn loại câu hỏi cụ thể (không phải "auto").
# App sẽ chèn vào đầu prompt vision để ép AI gán đúng LOAI.
_QTYPE_HINTS = {
    "TN": (
        "[!] CHẾ ĐỘ ÉP LOẠI — TRẮC NGHIỆM (TN):\n"
        "Tất cả câu trong ảnh đều là TN với 4 phương án A/B/C/D.\n"
        "  • PHẢI gán LOAI: TN.\n"
        "  • Mỗi câu PHẢI có đủ 4 dòng A: B: C: D:.\n"
        "  • KHÔNG bịa nếu ảnh không có 4 phương án rõ ràng — bỏ qua câu đó.\n"
        "  • Vẫn PHẢI bọc trong ===CAU===...===KETCAU===.\n\n"
    ),
    "DS": (
        "[!] CHẾ ĐỘ ÉP LOẠI — ĐÚNG/SAI (DS):\n"
        "Tất cả câu trong ảnh đều là DS với 4 mệnh đề a/b/c/d.\n"
        "  • PHẢI gán LOAI: DS.\n"
        "  • Mỗi câu PHẢI có đủ 4 dòng a: b: c: d:.\n"
        "  • Vẫn PHẢI bọc trong ===CAU===...===KETCAU===.\n\n"
    ),
    "TLN": (
        "[!] CHẾ ĐỘ ÉP LOẠI — TRẢ LỜI NGẮN (TLN):\n"
        "Tất cả câu trong ảnh đều là TLN — đáp án là 1 SỐ (tối đa 4 ký tự).\n"
        "  • PHẢI gán LOAI: TLN.\n"
        "  • KHÔNG có A/B/C/D, KHÔNG có a/b/c/d.\n"
        "  • Câu hỏi đặt trong NOIDUNG, đáp án (nếu có trong ảnh) vào DAPAN.\n"
        "  • Để DAPAN trống nếu ảnh không có đáp án — app sẽ tự giải.\n"
        "  • Vẫn PHẢI bọc trong ===CAU===...===KETCAU===.\n\n"
        "VÍ DỤ OUTPUT cho 1 câu TLN:\n"
        "===CAU===\n"
        "LOAI: TLN\n"
        "MUCDO: VD\n"
        "CHUONG: Hình không gian\n"
        "NOIDUNG: Trong không gian ${Oxyz}$, cho ... Độ dài đoạn ${MN}$ "
        "bằng bao nhiêu? (Kết quả làm tròn đến hàng phần trăm).\n"
        "DAPAN:\n"
        "LOIGIAI:\n"
        "===KETCAU===\n\n"
    ),
    "TL": (
        "[!] CHẾ ĐỘ ÉP LOẠI — TỰ LUẬN (TL):\n"
        "Tất cả câu trong ảnh đều là TL — trình bày lời giải.\n"
        "  • PHẢI gán LOAI: TL.\n"
        "  • KHÔNG có 4 phương án A/B/C/D rời.\n"
        "  • Để LOIGIAI trống nếu ảnh không có lời giải sẵn.\n"
        "  • Vẫn PHẢI bọc trong ===CAU===...===KETCAU===.\n\n"
    ),
}


def _build_vision_prompt(qtype_filter: str = "auto") -> str:
    """Trả prompt vision có hint cho LOAI cụ thể (nếu khác 'auto').

    qtype_filter: "auto" | "TN" | "DS" | "TLN" | "TL".
    """
    hint = _QTYPE_HINTS.get(qtype_filter, "")
    return hint + _VISION_PROMPT_STRUCT


# Vision → cấu trúc ===CAU===/===KETCAU=== (KHÔNG giải, chỉ chuẩn hoá).
# App sau đó tự gọi AI text để giải + verify (nếu user không tick "skip solve").
_VISION_PROMPT_STRUCT = """\
Bạn là trợ lý OCR chuyên xử lý đề thi / bài kiểm tra Toán THPT Việt Nam,
10+ năm kinh nghiệm. NHIỆM VỤ DUY NHẤT: chuyển ảnh thành các khối câu hỏi
chuẩn của app, KHÔNG GIẢI, KHÔNG SỬA, KHÔNG bịa đáp án.

════════════════════════════════════════════════════════════════════════
[1] NGUYÊN TẮC TỐI THƯỢNG
════════════════════════════════════════════════════════════════════════
- Nhận diện CHÍNH XÁC từng ký tự — tiếng Việt có dấu đầy đủ.
- Giữ NGUYÊN đánh số câu, A/B/C/D, mệnh đề a/b/c/d.
- KHÔNG bịa câu, KHÔNG bịa phương án, KHÔNG bịa đáp án.
- CẤM TUYỆT ĐỐI CHÈN NGUỒN / CITATION: Không chèn bất kỳ thẻ trích dẫn nào như [cite: ...], [source: ...], [1], [2]. Nếu tài liệu có, phải LOẠI BỎ HOÀN TOÀN.
- BẢNG SỐ LIỆU: Giữ đúng định dạng bảng Markdown (| Cột 1 | Cột 2 | \n | --- | --- |) hoặc bảng LaTeX (\\begin{tabular}{...}...\\end{tabular}), đảm bảo đủ số cột ở mọi dòng.
- Nếu trong ảnh KHÔNG có đáp án rõ ràng → để trống DAPAN.
- Nếu trong ảnh KHÔNG có lời giải → để trống LOIGIAI (app sẽ tự giải sau).

════════════════════════════════════════════════════════════════════════
[2] CÔNG THỨC TOÁN — CHỈ DÙNG ${...}$
════════════════════════════════════════════════════════════════════════
- CHỈ MỘT định dạng: ${biểu_thức}$ — luôn có { } bên trong cặp $.
    ĐÚNG : ${x^2 - 5x + 6 = 0}$, ${\\frac{1}{2}}$, ${\\sqrt{x+1}}$
    SAI  : $x^2 - 5x + 6 = 0$ (thiếu {}), $$...$$, \\(x^2\\), \\[x^2\\].
- CẤM Unicode toán: x², √x, ≠, π, ∫, ≤, ≥ → LaTeX hoá hết.
- Phân số ${\\frac{a}{b}}$, căn ${\\sqrt{x}}$, mũ ${x^{n}}$,
  chỉ số ${a_{n}}$, góc ${\\widehat{ABC}}$ (KHÔNG dùng \\angle).
- Dùng \\ trước mọi lệnh LaTeX: \\frac, \\sqrt, \\sin, \\cos, \\log,
  \\alpha, \\Delta, \\pi, \\int, \\sum, \\lim…

════════════════════════════════════════════════════════════════════════
[3] PHÂN LOẠI LOAI (tự nhận diện từ ảnh)
════════════════════════════════════════════════════════════════════════
- TN  — có 4 phương án A/B/C/D, 1 đáp án đúng.
- DS  — câu dẫn + 4 mệnh đề a/b/c/d; mỗi mệnh đề Đ/S.
- TLN — không có A/B/C/D, đáp án là 1 SỐ (tối đa 4 ký tự, vd: 14, 0,5).
- TL  — bài tự luận, yêu cầu trình bày các bước (không có lựa chọn).

════════════════════════════════════════════════════════════════════════
[4] HÌNH VẼ / BẢNG BIẾN THIÊN / ĐỒ THỊ TRONG ẢNH
════════════════════════════════════════════════════════════════════════
- Nếu câu có hình → chèn marker [HÌNH: <mô tả CHI TIẾT bằng tiếng Việt>]
  vào đúng vị trí trong NOIDUNG.
- Mô tả phải đủ thông tin để có thể VẼ LẠI bằng TikZ:
    + Hình học phẳng: tên đỉnh, số đo cạnh/góc, vuông góc / song song
      (vd: "tam giác ABC vuông tại A, AB=3, AC=4, M là trung điểm BC").
    + Hình không gian: hình chóp/lăng trụ, đỉnh đáy, đường vuông góc.
    + Đồ thị hàm số: dạng (parabol, bậc 3), điểm đặc biệt, trục đối xứng.
    + Bảng biến thiên: x = …, y' dấu …, y giá trị cực trị / tiệm cận.
- TUYỆT ĐỐI KHÔNG viết code TikZ — chỉ mô tả tự nhiên. App tự sinh TikZ.

════════════════════════════════════════════════════════════════════════
[4b] SUY LUẬN LỚP + MÔN + CHỦ ĐỀ (BẮT BUỘC — đặt ở ĐẦU output)
════════════════════════════════════════════════════════════════════════
TRƯỚC khi xuất các khối ===CAU===, hãy SUY LUẬN từ nội dung ảnh:
  • subject: "Toán" | "Lý" | "Hóa" | "Sinh" | "Văn" | "Sử" | "Địa" | "Anh" |
             "GDCD" | "Tin" | … (nếu không chắc → "Toán")
  • grade:   "6"..."12" (đoán từ độ phức tạp kiến thức)
  • topic:   chủ đề chính (1 cụm ngắn, vd: "Tích phân", "Dao động sóng")

In ra MỘT DÒNG DUY NHẤT theo format CHÍNH XÁC NÀY trước mọi khối câu:
  META: {"subject": "<...>", "grade": "<...>", "topic": "<...>"}

Lưu ý quan trọng:
  • Nếu ảnh chứa từ "Lớp 11" / "Toán 12" / "Kì thi" → ưu tiên lấy từ ảnh.
  • Nếu không có hint → đoán từ kiến thức:
      - Đạo hàm, tích phân, số phức, không gian Oxyz → lớp 12 Toán.
      - Lượng giác, dãy số, cấp số, giới hạn → lớp 11 Toán.
      - Hàm bậc hai, bất phương trình hai ẩn → lớp 10 Toán.
      - Phân thức, tứ giác, hình lăng trụ → lớp 8 Toán.
  • JSON phải hợp lệ — quote " " bao tất cả keys + values.
  • Nếu KHÔNG đoán được → ghi {"subject": "", "grade": "", "topic": ""}.

════════════════════════════════════════════════════════════════════════
[5] CẤU TRÚC OUTPUT — COPY CHÍNH XÁC TỪNG DÒNG
════════════════════════════════════════════════════════════════════════

META: {"subject": "Toán", "grade": "12", "topic": "Tích phân"}

===CAU===
LOAI: TN | DS | TLN | TL
MUCDO: NB | TH | VD
CHUONG: <chủ đề tự suy từ nội dung — "Hàm số bậc hai", "Xác suất", …>
NOIDUNG: <nội dung câu hỏi; công thức trong ${...}$; có thể chèn [HÌNH: …]>
A: <phương án A>                                       (chỉ TN)
B: <phương án B>                                       (chỉ TN)
C: <phương án C>                                       (chỉ TN)
D: <phương án D>                                       (chỉ TN)
a: <mệnh đề a>                                         (chỉ DS)
b: <mệnh đề b>                                         (chỉ DS)
c: <mệnh đề c>                                         (chỉ DS)
d: <mệnh đề d>                                         (chỉ DS)
DAPAN: <giữ nguyên nếu ảnh có; để TRỐNG nếu ảnh không có>
LOIGIAI: <giữ nguyên nếu ảnh có; để TRỐNG nếu ảnh không có>
===KETCAU===

════════════════════════════════════════════════════════════════════════
[6] CHECKLIST — BẮT BUỘC KIỂM TRA TRƯỚC KHI TRẢ LỜI
════════════════════════════════════════════════════════════════════════
[ ] Mỗi câu (KỂ CẢ KHI CHỈ CÓ 1 CÂU) bọc trong ===CAU===...===KETCAU===.
[ ] Giữa các câu có ĐÚNG 1 dòng trống.
[ ] Công thức luôn dạng ${...}$ — không có $$...$$, \\(...\\), \\[...\\].
[ ] Không Unicode toán (², √, ≠, π…).
[ ] TN có đủ 4 phương án; DS có đủ 4 ý.
[ ] Hình vẽ trong ảnh → [HÌNH: mô tả] đúng vị trí.
[ ] DAPAN/LOIGIAI để TRỐNG khi ảnh không có (app sẽ tự giải sau).
[ ] KHÔNG markdown fence ```, KHÔNG lời mở đầu/kết thúc.

⚠️ QUAN TRỌNG: Dù ảnh chỉ có 1 câu hỏi duy nhất, VẪN PHẢI bọc trong
===CAU===...===KETCAU===. Đây là yêu cầu bắt buộc của hệ thống parser.

CHỈ trả các khối ===CAU===...===KETCAU===. Bắt đầu NGAY với "===CAU===".
"""

# AI giải 1 câu: nhận text câu hỏi đã chuẩn hoá → fill DAPAN + LOIGIAI.
_SOLVE_PROMPT = """\
Bạn là chuyên gia Toán THPT, 10+ năm kinh nghiệm dạy & ra đề. Hãy GIẢI
câu hỏi sau theo phong cách giảng dạy — rõ ràng, đúng pháp lý toán, gọn.

NGUYÊN TẮC:
- Bám sát DỮ KIỆN trong đề. KHÔNG bịa thêm.
- LOIGIAI: viết liền mạch, không "Bước 1/Bước 2", giải đến kết quả cuối.
- DAPAN theo đúng loại câu:
    TN  → 1 ký tự A | B | C | D.
    DS  → "a=Đ,b=S,c=Đ,d=S"  (Đ=Đúng, S=Sai).
    TLN → 1 SỐ tối đa 4 ký tự, dùng dấu PHẨY thập phân VN (vd: 0,5).
    TL  → "xem lời giải".
- Công thức trong ${...}$ — KHÔNG dùng $$ hay \\( \\).

CÂU HỎI (đã chuẩn hoá):
{cau_block}

OUTPUT — CHỈ trả 2 dòng, KHÔNG thêm gì khác:
DAPAN: <…>
LOIGIAI: <…>
"""

# AI verify đáp án: nhận câu + đáp án + lời giải đã có → kiểm tra ĐÚNG/SAI.
_VERIFY_PROMPT = """\
Bạn là giám khảo Toán nghiêm khắc. Hãy KIỂM TRA xem đáp án và lời giải
sau có CHÍNH XÁC không.

CÂU HỎI:
{cau_block}

ĐÁP ÁN ĐANG CÓ: {dapan}
LỜI GIẢI ĐANG CÓ:
{loigiai}

YÊU CẦU:
1. Tính lại độc lập (không bị đáp án có sẵn dẫn dắt).
2. So sánh với đáp án đang có.
3. Trả về DUY NHẤT 1 trong 2 dạng:
   - Nếu ĐÚNG → trả:  OK
   - Nếu SAI  → trả:  SAI | DAPAN_DUNG: <đáp án đúng> | LOIGIAI_SUA: <lời giải đúng, ngắn gọn 2-4 câu>

TUYỆT ĐỐI không thêm lời giải thích ngoài 2 dạng trên.
"""

# AI sinh TikZ từ mô tả hình.
_TIKZ_FROM_DESC_PROMPT = r"""
Bạn là chuyên gia LaTeX/TikZ, vẽ hình Toán THPT.

NHIỆM VỤ: vẽ lại CHÍNH XÁC hình mô tả dưới đây bằng TikZ. Output PHẢI là
khối `\begin{tikzpicture} ... \end{tikzpicture}` thuần — không bọc
\documentclass, không lời mở đầu, không markdown fence.

QUY TẮC:
- Đảm bảo dữ kiện ĐÚNG: tên đỉnh, số đo, góc vuông, song song… khớp mô tả.
- Tam giác vuông tại A → A nằm ở đỉnh có ô vuông (\draw pic {right angle=B--A--C};).
- Tam giác cân tại B → BA=BC.
- Hình chóp S.ABCD → vẽ đáy ABCD trước, nối các đỉnh lên S; cạnh khuất dashed.
- Đồ thị: dùng pgfplots, axis lines=middle, samples=100.
- Bảng biến thiên: dùng tkz-tab, bọc trong tikzpicture.
- Ký hiệu góc: \draw pic["$\alpha$", angle radius=6mm] {angle=B--A--C};
- Nhãn điểm: \node[above] at (A) {$A$}; — chọn anchor không đè cạnh.
- TUYỆT ĐỐI không vẽ tự do — phải bám mô tả.

PACKAGES có sẵn: amsmath, amssymb, tikz, pgfplots (compat=1.18), tkz-tab.
TikZ libraries: calc, angles, quotes, arrows.meta, intersections, positioning,
3d, shapes.geometric, decorations.markings, patterns.

MÔ TẢ HÌNH (rút từ ảnh đề):
{description}

NGỮ CẢNH CÂU HỎI (giúp bạn hiểu yêu cầu):
{question}

OUTPUT (chỉ khối tikzpicture, không thêm gì khác):
"""

_VISION_PROMPT_PDF_PAGE = """\
Bạn là trợ lý OCR chuyên nghiệp xử lý PDF tiếng Việt và tài liệu đề thi Toán THPT. Chuyển đổi CHÍNH XÁC nội dung trang PDF trong ảnh thành văn bản có cấu trúc.

[1] NGUYÊN TẮC:
- Giữ NGUYÊN bố cục, thứ tự đọc, đánh số gốc của trang.
- ĐỀ THI 2 CỘT: Nếu trang có bố cục chia 2 cột, PHẢI đọc và xuất nội dung theo thứ tự đọc tự nhiên: đọc hết từ trên xuống dưới của CỘT BÊN TRÁI trước, sau đó mới đọc tiếp CỘT BÊN PHẢI. TUYỆT ĐỐI KHÔNG đọc ngang cắt qua 2 cột.
- Tiếng Việt có dấu đầy đủ, chính xác.
- Giữ nguyên tiêu đề, header, footer, khung thông tin kỳ thi/Sở/Trường nếu có.
- KHÔNG thêm lời giải thích, KHÔNG "sửa" lỗi người soạn, KHÔNG thêm trích dẫn kiểu [cite: ...] hay số nguồn rác.

[2] CÔNG THỨC TOÁN — BẮT BUỘC KẸP TRONG ${...}$:
- MỌI công thức toán học, ký hiệu toán, biến số (kể cả biến đơn x, y, z hay biểu thức phức tạp) BẮT BUỘC PHẢI KẸP TRONG ${...}$ (luôn có cặp ngoặc nhọn { } bên trong cặp dấu $).
  Ví dụ ĐÚNG: ${x^2 - 5x + 6 = 0}$, ${\\frac{1}{2}}$, ${\\sqrt{x+1}}$, ${x \\in \\mathbb{R}}$, ${\\vec{a}}$, ${\\widehat{ABC}}$, ${\\int_{0}^{1} f(x)\\,dx}$.
  TUYỆT ĐỐI KHÔNG dùng $...$ trần (thiếu {}), KHÔNG dùng $$...$$, \\(...\\), \\[...\\].
- CẤM Unicode toán: ², √, ≠, π, ∫, ≤, ≥ → luôn chuyển sang LaTeX bên trong ${...}$.
- Phân số ${\\frac{a}{b}}$, căn ${\\sqrt{x}}$, mũ ${x^{n}}$, chỉ số ${a_{n}}$, góc ${\\widehat{ABC}}$ (KHÔNG dùng \\angle).
- Dùng \\\\ trước mọi lệnh LaTeX: \\\\frac, \\\\sqrt, \\\\sin, \\\\cos, \\\\log, \\\\alpha, \\\\Delta, \\\\pi, \\\\int, \\\\sum, \\\\lim…

[3] NHẬN DẠNG BẢNG BIỂU & BẢNG BIẾN THIÊN (DÙNG KÝ TỰ "|"):
- Khi gặp bảng số liệu, bảng thống kê, bảng phân loại, bảng biến thiên, bảng xét dấu:
  BẮT BUỘC định dạng cấu trúc bảng phân cách rõ ràng bằng ký tự "|" ở đầu, giữa và cuối mỗi dòng:
      | Tiêu đề 1 | Tiêu đề 2 | Tiêu đề 3 |
      | Dữ liệu 1 | Dữ liệu 2 | Dữ liệu 3 |
- Với BẢNG BIẾN THIÊN / BẢNG XÉT DẤU:
  Dòng x:  | x  | -\\infty | 0 | +\\infty |
  Dòng y': | y' | | + | 0 | - | |
  Dòng y:  | y  | | 1 | \\searrow | -\\infty |
- Mỗi ô phải có nội dung tương ứng (nếu ô trống thì để "| |" hoặc "|  |").
- Đảm bảo các dòng trong cùng một bảng có số lượng cột đồng nhất để hệ thống tự động dựng thành bảng Word Native.

[4] HÌNH VẼ / ĐỒ THỊ — QUAN TRỌNG:
- Trong trang có thể có nhiều hình. Bạn sẽ nhận ĐÚNG số hình ở tham số đầu.
- Với MỖI hình, chèn marker dạng:
      [HÌNH 1: mô tả ngắn 1 dòng]
      [HÌNH 2: mô tả ngắn 1 dòng]
      …
  theo THỨ TỰ ĐỌC (từ trên xuống, từ trái qua phải) — đánh số 1, 2, 3…
- Marker đặt trên DÒNG RIÊNG, ngay tại vị trí trong trang mà hình xuất hiện:
      * Nếu hình nằm GIỮA câu hỏi và phương án → đặt marker sau nội dung câu,
        trước dòng "A.".
      * Nếu hình thuộc 1 câu cụ thể → đặt TRONG câu đó, không đặt ngoài.
      * Nếu hình đứng riêng (đồ thị tổng quát) → đặt giữa 2
        đoạn text, có dòng trống phía trên/dưới.
- Mô tả nên ngắn gọn: loại hình (tam giác, parabol, đồ thị…), đặc điểm chính
  (các đỉnh, trục đối xứng, điểm cực trị…). KHÔNG cố gắng viết TikZ.
- Số marker [HÌNH N] phải khớp với số hình thực tế đã extract trong trang.
- Nếu trong trang KHÔNG có hình nào → đừng chèn [HÌNH N] nào cả.

[5] CẤU TRÚC CÂU HỎI (nếu trang chứa câu hỏi đề thi):
- Mỗi câu bắt đầu bằng "Câu N:", "Bài N:" hoặc số thứ tự rõ ràng.
- Giữ nguyên dấu xuống dòng giữa các phương án A/B/C/D để dễ parse.
- Nếu đề có các ý a), b), c), d) (kiểu đúng/sai) → giữ nguyên markers a/b/c/d.

[6] CẤU TRÚC ĐẶC BIỆT:
- Công thức block standalone → đặt trên dòng riêng nhưng vẫn kẹp trong ${...}$.
- Liệt kê đánh số → giữ nguyên.
- Đoạn văn dài → tách đoạn đúng như gốc.

[7] OUTPUT:
- CHỈ trả nội dung văn bản của trang.
- KHÔNG thêm markdown fence ```.
- KHÔNG thêm lời mở đầu / kết thúc.
- Bắt đầu ngay từ nội dung trang đầu tiên.
"""


# ══════════════════════════════════════════════════════════════════════════════
#  TAB CONVERT
# ══════════════════════════════════════════════════════════════════════════════

class TabConvert(ttk.Frame):
    """Tab Convert — Ảnh → Văn bản / Câu hỏi, placeholder PDF."""

    def __init__(self, parent, get_ai_call: Callable | None = None,
                 get_subject_grade: Callable | None = None,
                 on_apply_detected_meta: Callable | None = None,
                 **kw):
        super().__init__(parent, **kw)
        self._get_ai_call = get_ai_call
        self._get_subject_grade = get_subject_grade
        # [SMART-1] Callback (subj, grade, topic) → áp dụng vào tab Cài đặt
        self._on_apply_detected_meta = on_apply_detected_meta
        self._image_data: Optional[bytes] = None   # raw PNG/JPEG bytes
        self._image_ext: str = "png"
        self._img_detected_meta: dict = {}
        self._busy = False
        self._build()

    # ──────────────────────────────────────────────────────────────────────
    #  BUILD UI
    # ──────────────────────────────────────────────────────────────────────

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Toolbar ──────────────────────────────────────────────────────
        toolbar = tk.Frame(self, bg=C["surface_2"])
        toolbar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        # Sub-tab selector (Ảnh → Văn bản | PDF → … | AI Text → …)
        self._mode_var = tk.StringVar(value="image")
        self._mode_buttons: list[tk.Button] = []
        modes = [
            ("image",   "🖼️  Ảnh → Văn bản"),
            ("pdf",     "📄  PDF → Word"),
            ("ai_text", "🤖  Text/LaTeX → Câu hỏi"),
        ]
        for val, label in modes:
            btn = tk.Button(
                toolbar, text=label,
                font=(FONT["app"], FONT["size_md"], "bold"),
                bg=C["surface_2"], fg=C["text_muted"],
                activebackground=C["surface_3"], activeforeground=TEXT,
                relief="flat", bd=0, cursor="hand2",
                padx=16, pady=8,
                command=lambda v=val: self._select_mode(v),
            )
            btn.pack(side="left", padx=2, pady=4)
            self._mode_buttons.append((val, btn))

        # ── Bộ chọn Lớp & Môn trực tiếp trên Convert toolbar ────────────
        sel_frame = tk.Frame(toolbar, bg=C["surface_2"])
        sel_frame.pack(side="right", padx=12, pady=4)

        init_subj, init_grade = "Toán", "12"
        if self._get_subject_grade:
            try:
                s, g = self._get_subject_grade()
                if s: init_subj = s
                if g: init_grade = g
            except Exception:
                pass

        self._grade_var = tk.StringVar(value=init_grade)
        self._subject_var = tk.StringVar(value=init_subj)

        tk.Label(
            sel_frame, text="🏷️ Lớp:", bg=C["surface_2"], fg=TEXT,
            font=(FONT["app"], FONT["size_sm"], "bold"),
        ).pack(side="left", padx=(4, 2))
        self._grade_combo = ttk.Combobox(
            sel_frame, textvariable=self._grade_var,
            values=["10", "11", "12", "6", "7", "8", "9", "Khác"],
            width=5, state="readonly",
        )
        self._grade_combo.pack(side="left", padx=(0, 8))

        tk.Label(
            sel_frame, text="Môn:", bg=C["surface_2"], fg=TEXT,
            font=(FONT["app"], FONT["size_sm"], "bold"),
        ).pack(side="left", padx=(4, 2))
        self._subject_combo = ttk.Combobox(
            sel_frame, textvariable=self._subject_var,
            values=["Toán", "Vật lí", "Hóa học", "Sinh học", "Ngữ văn", "Lịch sử", "Địa lí", "Tiếng Anh", "Tin học", "GDCD"],
            width=8, state="readonly",
        )
        self._subject_combo.pack(side="left", padx=(0, 4))

        # ── Main content (switched by mode) ──────────────────────────────
        self._content = tk.Frame(self, bg=BG)
        self._content.grid(row=1, column=0, sticky="nsew")
        self._content.columnconfigure(0, weight=1)
        self._content.columnconfigure(1, weight=1)
        self._content.rowconfigure(0, weight=1)

        self._build_image_mode()
        self._build_pdf_mode()
        self._build_ai_text_mode()

        self._on_mode_change()

    # ── Image mode ───────────────────────────────────────────────────────

    def _build_image_mode(self):
        """UI mới: Ảnh → Cấu trúc Word câu hỏi (4 bước).

        Bước 1: Vision OCR → ===CAU===/===KETCAU=== (KHÔNG giải).
        Bước 2: AI text giải từng câu (DAPAN + LOIGIAI) — có thể skip.
        Bước 3: AI verify đáp án (double-check) — có thể skip.
        Bước 4: AI sinh TikZ cho câu có [HÌNH: …] → render PNG.
        Cuối:   user export Word (tự mở) hoặc Thêm vào NHCH (dialog xem trước).
        """
        self._img_frame = tk.Frame(self._content, bg=BG)

        # ── State ─────────────────────────────────────────────────────────
        self._img_questions: list = []          # list[Question] sau pipeline
        self._img_raw_struct: str = ""           # raw ===CAU=== text từ Vision
        self._img_skip_solve = tk.BooleanVar(value=False)
        self._img_do_tikz    = tk.BooleanVar(value=True)
        self._img_start_time = 0.0
        self._img_timer_id = None
        self._img_last_exported_path: Optional[str] = None
        # Filter loại câu — "auto" hoặc 1 trong TN / DS / TLN / TL.
        # Mặc định "auto": AI tự nhận diện. Khi user chọn cụ thể → ép tất cả
        # câu về loại đó (giúp khi ảnh có cả TN lẫn TL mà user chỉ muốn TN).
        self._img_qtype = tk.StringVar(value="auto")
        # Mapping: hiển thị ↔ giá trị nội bộ
        self._qtype_display_to_code = {
            "🔍 Tự nhận diện": "auto",
            "🅰️ Trắc nghiệm (TN)": "TN",
            "✅ Đúng / Sai (DS)": "DS",
            "🔢 Trả lời ngắn (TLN)": "TLN",
            "✍️ Tự luận (TL)": "TL",
        }
        self._qtype_code_to_display = {v: k
            for k, v in self._qtype_display_to_code.items()}

        # Left: image input + options
        left = tk.Frame(self._img_frame, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(8, 4), pady=8)

        # ── [SPEED-6] Drop / paste zone — hỗ trợ BATCH multi-image ─────
        # Cấu trúc: drop_zone (frame) chứa:
        #   • _drop_label  — hiện khi batch RỖNG ("kéo thả / dán / click")
        #   • _thumb_scroll — Canvas + grid thumbnails (hiện khi batch ≥ 1)
        drop_zone = tk.Frame(left, bg="#F0F9FF",
                             highlightbackground=C["primary_light"],
                             highlightthickness=2, cursor="hand2")
        self._drop_zone = drop_zone

        self._drop_label = tk.Label(
            drop_zone,
            text=("📋  Dán ảnh đề (Ctrl+V)\n"
                  "hoặc nhấn để chọn FILE (có thể chọn nhiều)\n\n"
                  "💡 App xử lý tất cả ảnh thành 1 đề Word"),
            bg="#F0F9FF", fg=C["text_body"],
            font=(FONT["app"], 12),
            justify="center", wraplength=350,
        )
        self._drop_label.pack(expand=True)

        # Scrollable thumbnail grid (hidden ban đầu)
        self._thumb_scroll = tk.Canvas(drop_zone, bg="#F0F9FF",
                                       highlightthickness=0)
        self._thumb_vsb = ttk.Scrollbar(
            drop_zone, orient="vertical",
            command=self._thumb_scroll.yview)
        self._thumb_scroll.configure(yscrollcommand=self._thumb_vsb.set)
        # _thumb_grid: inner frame chứa các thumbnail
        self._thumb_grid = tk.Frame(self._thumb_scroll, bg="#F0F9FF")
        self._thumb_grid_win = self._thumb_scroll.create_window(
            (0, 0), window=self._thumb_grid, anchor="nw")

        # Sync scrollregion when grid resizes
        def _sync_thumb_scrollregion(_e=None):
            try:
                self._thumb_scroll.configure(
                    scrollregion=self._thumb_scroll.bbox("all"))
            except Exception:
                pass
        self._thumb_grid.bind("<Configure>", _sync_thumb_scrollregion)
        self._thumb_scroll.bind(
            "<Configure>",
            lambda e: self._thumb_scroll.itemconfig(
                self._thumb_grid_win, width=e.width))

        # Mouse wheel scroll
        def _on_thumb_wheel(e):
            n = int(-3 * (e.delta / 120))
            if n == 0:
                n = -1 if e.delta > 0 else 1
            self._thumb_scroll.yview_scroll(n, "units")
        self._thumb_scroll.bind("<MouseWheel>", _on_thumb_wheel)
        self._thumb_grid.bind("<MouseWheel>", _on_thumb_wheel)

        # Click drop_zone (chỉ khi rỗng) → mở file dialog
        drop_zone.bind("<Button-1>", lambda e: self._upload_image())
        self._drop_label.bind("<Button-1>", lambda e: self._upload_image())

        # State BATCH (replace _image_data single)
        # Mỗi item: dict {data: bytes, ext: str, name: str, thumb: PhotoImage}
        self._image_batch: list[dict] = []
        # _image_data + _image_ext giữ làm backward-compat: trỏ tới phần tử
        # đầu tiên trong batch (cho code cũ dùng); pipeline mới đọc trực tiếp
        # batch.

        # ── Buttons under drop zone (input actions) ─────────────────────
        btn_row = tk.Frame(left, bg=BG)
        
        tk.Button(
            btn_row, text="📂 Chọn ảnh",
            bg=PRIMARY, fg="white",
            activebackground=C["primary_xl"], activeforeground="white",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=14, pady=6,
            command=self._upload_image,
        ).pack(side="left", padx=4)

        tk.Button(
            btn_row, text="📋 Dán ảnh (Ctrl+V)",
            bg="#E0F2FE", fg=C["primary_xl"], activebackground="#BAE6FD",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=14, pady=6,
            command=self._paste_image,
        ).pack(side="left", padx=4)

        self._clear_btn = tk.Button(
            btn_row, text="🗑️ Xóa ảnh",
            bg=C["danger"], fg="white",
            activebackground="#DC2626", activeforeground="white",
            disabledforeground="#FECACA",
            font=(FONT["app"], FONT["size_md"]),
            relief="flat", cursor="hand2", bd=0, padx=14, pady=6,
            command=self._clear_image,
            state="disabled",
        )
        self._clear_btn.pack(side="left", padx=4)

        # ── Options panel (qtype + checkboxes) ──────────────────────────
        opt_frame = tk.LabelFrame(
            left, text=" ⚙️ Tuỳ chọn xử lý ",
            bg=BG, fg=C["text_main"],
            font=(FONT["app"], FONT["size_md"], "bold"),
            padx=8, pady=6,
        )
        
        # Hàng 1: chọn loại câu (combobox)
        qtype_row = tk.Frame(opt_frame, bg=BG)
        qtype_row.pack(fill="x", anchor="w", pady=(0, 4))
        tk.Label(
            qtype_row, text="Loại câu:", bg=BG, fg=C["text_body"],
            font=(FONT["app"], FONT["size_md"]),
        ).pack(side="left", padx=(0, 6))

        self._img_qtype_display = tk.StringVar(value="🔍 Tự nhận diện")
        qtype_cb = ttk.Combobox(
            qtype_row,
            textvariable=self._img_qtype_display,
            values=list(self._qtype_display_to_code.keys()),
            state="readonly", width=24,
            font=(FONT["app"], FONT["size_md"]),
        )
        qtype_cb.pack(side="left")
        qtype_cb.bind("<<ComboboxSelected>>", self._on_qtype_changed)

        # Hint nhỏ giải thích
        tk.Label(
            qtype_row,
            text=" (ép AI gán loại — hữu ích khi ảnh có nhiều loại trộn lẫn)",
            bg=BG, fg=HINT,
            font=(FONT["app"], FONT["size_sm"], "italic"),
        ).pack(side="left", padx=(4, 0))

        # Hàng 2 & 3: checkbox
        tk.Checkbutton(
            opt_frame,
            text="📋  Không giải đáp án — chỉ chuẩn hoá cấu trúc Word",
            variable=self._img_skip_solve,
            bg=BG, fg=C["text_body"], activebackground=BG,
            font=(FONT["app"], FONT["size_md"]),
            anchor="w",
        ).pack(fill="x", anchor="w")

        tk.Checkbutton(
            opt_frame,
            text="🎨  Vẽ lại hình bằng TikZ (nếu đề có hình vẽ)",
            variable=self._img_do_tikz,
            bg=BG, fg=C["text_body"], activebackground=BG,
            font=(FONT["app"], FONT["size_md"]),
            anchor="w",
        ).pack(fill="x", anchor="w")

        # ── Convert button + status (ghim cố định ở đáy) ─────────────────
        act_row = tk.Frame(left, bg=BG)
        act_row.pack(side="bottom", fill="x", pady=(8, 0))

        self._convert_btn = tk.Button(
            act_row, text="🚀 Chuyển đổi",
            bg=C["success"], fg="white",
            activebackground="#059669", activeforeground="white",
            disabledforeground="#A7F3D0",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=18, pady=8,
            command=self._start_convert,
            state="disabled",
        )
        self._convert_btn.pack(side="left", padx=4)

        self._status_lbl = tk.Label(act_row, text="", bg=BG, fg=HINT,
                                    font=(FONT["app"], FONT["size_sm"]),
                                    anchor="w")
        self._status_lbl.pack(side="left", padx=8, fill="x", expand=True)

        # Đóng gói options & buttons lên trên act_row, ghim ở đáy
        opt_frame.pack(side="bottom", fill="x", pady=(6, 0))
        btn_row.pack(side="bottom", fill="x", pady=(6, 0))

        # Cuối cùng drop_zone chiếm toàn bộ phần trên còn lại
        drop_zone.pack(fill="both", expand=True)

        # ── Right: progress + result ────────────────────────────────────
        right = tk.Frame(self._img_frame, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=(4, 8), pady=8)

        # Progress bar (4-stage pipeline)
        prog_frame = tk.Frame(right, bg=SURFACE,
                              highlightbackground=BORDER, highlightthickness=1)
        prog_frame.pack(fill="x", pady=(0, 8))

        prog_hdr = tk.Frame(prog_frame, bg="#E0F2FE")
        prog_hdr.pack(fill="x")
        tk.Label(prog_hdr, text="📊 Tiến trình", bg="#E0F2FE",
                 fg=C["primary_xl"],
                 font=(FONT["app"], FONT["size_md"], "bold"),
                 padx=8, pady=6).pack(side="left")

        # Timer label bên phải
        self._img_timer_var = tk.StringVar(value="⏱️ 00:00")
        self._img_timer_lbl = tk.Label(
            prog_hdr, textvariable=self._img_timer_var,
            bg="#E0F2FE", fg=C["primary_xl"],
            font=(FONT["app"], FONT["size_md"], "bold"),
            padx=8, pady=6,
        )
        self._img_timer_lbl.pack(side="right")

        prog_body = tk.Frame(prog_frame, bg=SURFACE)
        prog_body.pack(fill="x", padx=12, pady=8)

        style = ttk.Style()
        style.configure("IMG.Horizontal.TProgressbar",
                        troughcolor=C["surface_2"], background=C["success"],
                        thickness=12)
        self._img_pb = ttk.Progressbar(
            prog_body, mode="determinate", maximum=100,
            style="IMG.Horizontal.TProgressbar")
        self._img_pb.pack(fill="x", pady=(0, 4))
        self._img_pb["value"] = 0

        self._img_stage_var = tk.StringVar(value="Chưa bắt đầu")
        tk.Label(prog_body, textvariable=self._img_stage_var,
                 bg=SURFACE, fg=C["text_body"],
                 font=(FONT["app"], FONT["size_sm"])).pack(anchor="w")

        # ── Action buttons & Output text ghim ở đáy (side="bottom") ──
        txt_frame = tk.Frame(right, bg=BORDER)
        txt_frame.pack(side="bottom", fill="x", pady=(4, 0))

        out_lbl_row = tk.Frame(right, bg=BG)
        out_lbl_row.pack(side="bottom", fill="x", pady=(6, 0))
        tk.Label(out_lbl_row,
                 text="Văn bản (Ctrl+C để copy → paste vào Word):",
                 bg=BG, fg=C["text_muted"],
                 font=(FONT["app"], FONT["size_sm"], "bold")
                 ).pack(side="left", padx=4)

        act_btn_row = tk.Frame(right, bg=BG)
        act_btn_row.pack(side="bottom", fill="x", pady=(6, 0))

        self._img_export_btn = tk.Button(
            act_btn_row, text="💾 Xuất Word & mở",
            bg=PRIMARY, fg="white",
            activebackground=C["primary_xl"], activeforeground="white",
            disabledforeground="#BAE6FD",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=16, pady=6,
            command=self._img_export_word,
            state="disabled",
        )
        self._img_export_btn.pack(side="left", padx=4)

        self._img_folder_btn = tk.Button(
            act_btn_row, text="📁 Mở thư mục",
            bg="#0284C7", fg="white",
            activebackground="#0369A1", activeforeground="white",
            disabledforeground="#BAE6FD",
            font=(FONT["app"], FONT["size_md"]),
            relief="flat", cursor="hand2", bd=0, padx=12, pady=6,
            command=self._img_open_folder,
            state="disabled",
        )
        self._img_folder_btn.pack(side="left", padx=4)

        self._img_nhch_btn = tk.Button(
            act_btn_row, text="⬆️ Thêm vào NHCH",
            bg="#7C3AED", fg="white",
            activebackground="#6D28D9", activeforeground="white",
            disabledforeground="#C4B5FD",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=14, pady=6,
            command=self._img_save_nhch,
            state="disabled",
        )
        self._img_nhch_btn.pack(side="left", padx=4)

        self._copy_btn = tk.Button(
            act_btn_row, text="📋 Copy text",
            bg="#E0F2FE", fg=C["primary_xl"],
            activebackground="#BAE6FD",
            disabledforeground="#94A3B8",
            font=(FONT["app"], FONT["size_md"]),
            relief="flat", cursor="hand2", bd=0, padx=12, pady=6,
            command=self._copy_result,
            state="disabled",
        )
        self._copy_btn.pack(side="left", padx=4)

        # ── Question structure panel (chiếm phần còn lại ở giữa) ─────────
        self._q_panel = tk.Frame(right, bg=BG)
        self._q_panel.pack(fill="both", expand=True)

        q_hdr = tk.Frame(self._q_panel, bg="#ECFDF5")
        q_hdr.pack(fill="x")
        tk.Label(q_hdr, text="📊 Câu hỏi đã nhận diện",
                 bg="#ECFDF5", fg="#065F46",
                 font=(FONT["app"], FONT["size_md"], "bold"),
                 padx=8, pady=6).pack(side="left")
        # Hint nhỏ cho user biết có thể sửa
        tk.Label(q_hdr,
                 text="(💡 Double-click 1 dòng để sửa nội dung / chủ đề / mức độ)",
                 bg="#ECFDF5", fg="#065F46",
                 font=(FONT["app"], FONT["size_sm"], "italic"),
                 ).pack(side="left", padx=(4, 0))
        self._img_count_lbl = tk.Label(q_hdr, text="", bg="#ECFDF5", fg="#065F46",
                                       font=(FONT["app"], FONT["size_sm"]))
        self._img_count_lbl.pack(side="right", padx=8)

        # Treeview with scrollbars
        tree_frame = tk.Frame(self._q_panel, bg=BG)
        tree_frame.pack(fill="both", expand=True, pady=(4, 0))

        cols = ("stt", "qtype", "level", "topic", "answer", "content_preview")
        self._q_tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            height=8, selectmode="browse",
        )
        self._q_tree.heading("stt", text="#")
        self._q_tree.heading("qtype", text="Loại")
        self._q_tree.heading("level", text="Mức")
        self._q_tree.heading("topic", text="Chủ đề")
        self._q_tree.heading("answer", text="Đáp án")
        self._q_tree.heading("content_preview", text="Nội dung")
        self._q_tree.column("stt", width=35, minwidth=30, anchor="center")
        self._q_tree.column("qtype", width=50, minwidth=40, anchor="center")
        self._q_tree.column("level", width=45, minwidth=40, anchor="center")
        self._q_tree.column("topic", width=130, minwidth=80, anchor="w")
        self._q_tree.column("answer", width=90, minwidth=60, anchor="w")
        self._q_tree.column("content_preview", width=320, minwidth=150, anchor="w")

        tree_vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                                  command=self._q_tree.yview)
        tree_hsb = ttk.Scrollbar(tree_frame, orient="horizontal",
                                  command=self._q_tree.xview)
        self._q_tree.configure(yscrollcommand=tree_vsb.set,
                               xscrollcommand=tree_hsb.set)
        self._q_tree.grid(row=0, column=0, sticky="nsew")
        tree_vsb.grid(row=0, column=1, sticky="ns")
        tree_hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Tag câu cần xem lại (verify thấy sai)
        self._q_tree.tag_configure("verify_fail", background="#FEF3C7")

        # Double-click → mở dialog sửa câu hỏi (nội dung / chủ đề / mức độ /
        # phương án / lời giải) trước khi xuất Word hoặc thêm vào NHCH.
        self._q_tree.bind("<Double-1>", self._on_q_tree_double_click)

        self._output_text = tk.Text(
            txt_frame, wrap="word", height=6,
            font=(FONT["app"], FONT["size_sm"]),
            bg=SURFACE, fg=C["text_body"],
            insertbackground=TEXT,
            highlightthickness=0, bd=0,
            padx=8, pady=6,
        )
        vsb = ttk.Scrollbar(txt_frame, orient="vertical",
                             command=self._output_text.yview)
        self._output_text.configure(yscrollcommand=vsb.set)
        self._output_text.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._output_text.insert("1.0",
            "Tải ảnh đề lên → nhấn 'Chuyển đổi'.\n"
            "App sẽ:\n"
            "  1️⃣ Nhận diện cấu trúc câu hỏi từ ảnh\n"
            "  2️⃣ Tự giải đáp án + lời giải (có thể bỏ qua)\n"
            "  3️⃣ Kiểm tra lại đáp án trước khi trả về\n"
            "  4️⃣ Vẽ lại hình bằng TikZ (nếu có)\n\n"
            "Kết quả hiện ra ở đây sẽ là VĂN BẢN CHUẨN WORD:\n"
            "  • Câu N. ... in đậm tự động.\n"
            "  • TN: A./B./C./D. cùng dòng, ngăn TAB.\n"
            "  • DS: a/b/c/d mỗi ý 1 dòng.\n"
            "  • TLN: đáp án dạng hộp |0|,|7|5|.\n"
            "  • 'Đáp án:' và 'Lời giải:' in đậm.\n\n"
            "Có thể: Xuất Word (tự mở) — Thêm vào NHCH — Copy text (paste Word).")
        self._output_text.configure(state="disabled")

        # Alias để code cũ (nếu còn tham chiếu) không vỡ
        self._parsed_questions: list = self._img_questions

    # ── PDF placeholder ──────────────────────────────────────────────────

    def _build_pdf_mode(self):
        """Xây dựng UI cho chế độ PDF → Word."""
        self._pdf_frame = tk.Frame(self._content, bg=BG)

        # ── State cho PDF mode ──
        self._pdf_path: Optional[str] = None
        self._pdf_busy = False
        self._pdf_cancel = False
        # threading.Event dùng cho extract_page_images — set() khi user hủy
        # hoặc _pdf_cancel=True, giúp dừng vòng trích image trong page.
        import threading as _threading
        self._pdf_cancel_event = _threading.Event()
        self._pdf_page_count = 0
        self._pdf_start_time = 0.0
        self._pdf_timer_id = None
        self._pdf_timer_var = tk.StringVar(value="⏱️ 00:00")
        self._pdf_eta_var = tk.StringVar(value="")
        self._pdf_auto_open_var = tk.BooleanVar(value=True)
        self._pdf_range_mode = tk.StringVar(value="all")
        self._pdf_pages_entry = tk.StringVar(value="")

        # ── Left: Input ──
        left = tk.Frame(self._pdf_frame, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(8, 4), pady=8)

        # Convert button + cancel + auto open (ghim đáy trước)
        pdf_act_row = tk.Frame(left, bg=BG)
        pdf_act_row.pack(side="bottom", fill="x", pady=(8, 0))

        # Checkbox auto-open Word
        tk.Checkbutton(
            pdf_act_row,
            text="Tự động mở Word khi xong",
            variable=self._pdf_auto_open_var,
            bg=BG, fg=C["text_body"], activebackground=BG,
            font=(FONT["app"], FONT["size_sm"]),
        ).pack(side="right", padx=(4, 0))

        # ── Phạm vi trang chuyển đổi (Page Range) ──
        range_frame = tk.LabelFrame(
            left, text=" 📑 Phạm vi trang chuyển đổi ",
            bg=BG, fg=C["text_main"],
            font=(FONT["app"], FONT["size_sm"], "bold"),
            padx=8, pady=4,
        )
        range_frame.pack(side="bottom", fill="x", pady=(6, 0))

        range_row = tk.Frame(range_frame, bg=BG)
        range_row.pack(fill="x")

        tk.Radiobutton(
            range_row, text="Toàn bộ file",
            variable=self._pdf_range_mode, value="all",
            bg=BG, fg=C["text_body"], activebackground=BG,
            font=(FONT["app"], FONT["size_sm"]),
            command=self._on_pdf_range_mode_changed,
        ).pack(side="left", padx=(0, 10))

        tk.Radiobutton(
            range_row, text="Chỉ các trang:",
            variable=self._pdf_range_mode, value="custom",
            bg=BG, fg=C["text_body"], activebackground=BG,
            font=(FONT["app"], FONT["size_sm"]),
            command=self._on_pdf_range_mode_changed,
        ).pack(side="left")

        self._pdf_pages_input = ttk.Entry(
            range_row, textvariable=self._pdf_pages_entry,
            width=14, font=(FONT["app"], FONT["size_sm"]),
        )
        self._pdf_pages_input.pack(side="left", padx=4)
        self._pdf_pages_entry.trace_add("write", lambda *_: self._update_pdf_estimate())

        tk.Label(
            range_frame, text="Ví dụ: 1-3, 5 (giúp tiết kiệm API khi chỉ cần chuyển vài trang)",
            bg=BG, fg=HINT, font=(FONT["app"], FONT["size_xs"], "italic"),
        ).pack(anchor="w", pady=(2, 0))

        # ── API estimate info ──
        est_frame = tk.Frame(left, bg="#FFF7ED",
                             highlightbackground=C["warning"], highlightthickness=1)
        est_frame.pack(side="bottom", fill="x", pady=(6, 0))

        self._pdf_estimate_var = tk.StringVar(
            value="📊 Chọn file PDF để xem ước tính số lần gọi API")
        tk.Label(
            est_frame, textvariable=self._pdf_estimate_var,
            bg="#FFF7ED", fg=C["warning_dark"],
            font=(FONT["app"], FONT["size_sm"]),
            justify="left", wraplength=400, padx=8, pady=6,
        ).pack(fill="x")

        # Buttons (chọn file)
        pdf_btn_row = tk.Frame(left, bg=BG)
        pdf_btn_row.pack(side="bottom", fill="x", pady=(6, 0))

        tk.Button(
            pdf_btn_row, text="📂 Chọn PDF",
            bg=C["warning"], fg="white",
            activebackground=C["warning_light"], activeforeground="white",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=14, pady=6,
            command=self._choose_pdf,
        ).pack(side="left", padx=4)

        self._pdf_clear_btn = tk.Button(
            pdf_btn_row, text="🗑️ Xóa",
            bg=C["danger"], fg="white",
            activebackground="#DC2626", activeforeground="white",
            disabledforeground="#FECACA",
            font=(FONT["app"], FONT["size_md"]),
            relief="flat", cursor="hand2", bd=0, padx=14, pady=6,
            command=self._clear_pdf, state="disabled",
        )
        self._pdf_clear_btn.pack(side="left", padx=4)

        # Drop zone (chiếm phần còn lại ở trên)
        pdf_drop = tk.Frame(left, bg="#FFF7ED",
                            highlightbackground=C["warning"], highlightthickness=2)
        pdf_drop.pack(fill="both", expand=True)

        self._pdf_drop_label = tk.Label(
            pdf_drop,
            text="📄\n\nKéo thả hoặc nhấn để chọn file PDF\n\n"
                 "Hỗ trợ: .pdf",
            bg="#FFF7ED", fg=C["text_body"],
            font=(FONT["app"], 11),
            justify="center", wraplength=280,
        )
        self._pdf_drop_label.pack(expand=True, padx=20, pady=20)
        pdf_drop.bind("<Button-1>", lambda e: self._choose_pdf())
        self._pdf_drop_label.bind("<Button-1>", lambda e: self._choose_pdf())

        self._pdf_convert_btn = tk.Button(
            pdf_act_row, text="🚀 Chuyển đổi PDF → Word",
            bg=C["success"], fg="white",
            activebackground="#059669", activeforeground="white",
            disabledforeground="#A7F3D0",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=18, pady=8,
            command=self._start_pdf_convert, state="disabled",
        )
        self._pdf_convert_btn.pack(side="left", padx=4)

        self._pdf_cancel_btn = tk.Button(
            pdf_act_row, text="⏹ Hủy",
            bg=C["danger"], fg="white",
            activebackground="#DC2626", activeforeground="white",
            disabledforeground="#FECACA",
            font=(FONT["app"], FONT["size_md"]),
            relief="flat", cursor="hand2", bd=0, padx=14, pady=8,
            command=self._cancel_pdf_convert, state="disabled",
        )
        self._pdf_cancel_btn.pack(side="left", padx=4)

        # ── Right: Progress + Output ──
        right = tk.Frame(self._pdf_frame, bg=BG)
        right.pack(side="right", fill="both", expand=True, padx=(4, 8), pady=8)

        # Progress section
        prog_frame = tk.Frame(right, bg=SURFACE,
                              highlightbackground=BORDER, highlightthickness=1)
        prog_frame.pack(fill="x", pady=(0, 8))

        prog_hdr = tk.Frame(prog_frame, bg="#E0F2FE")
        prog_hdr.pack(fill="x")
        tk.Label(prog_hdr, text="📊 Tiến trình chuyển đổi", bg="#E0F2FE",
                 fg=C["primary_xl"],
                 font=(FONT["app"], FONT["size_md"], "bold"),
                 padx=8, pady=6).pack(side="left")

        # Timer label bên phải
        self._pdf_timer_lbl = tk.Label(
            prog_hdr, textvariable=self._pdf_timer_var,
            bg="#E0F2FE", fg=C["primary_xl"],
            font=(FONT["app"], FONT["size_md"], "bold"),
            padx=8, pady=6,
        )
        self._pdf_timer_lbl.pack(side="right")

        prog_body = tk.Frame(prog_frame, bg=SURFACE)
        prog_body.pack(fill="x", padx=12, pady=8)

        # Progress bar
        style = ttk.Style()
        style.configure("PDF.Horizontal.TProgressbar",
                        troughcolor=C["surface_2"], background=C["success"],
                        thickness=12)
        self._pdf_pb = ttk.Progressbar(
            prog_body, mode="determinate", maximum=100,
            style="PDF.Horizontal.TProgressbar")
        self._pdf_pb.pack(fill="x", pady=(0, 4))
        self._pdf_pb["value"] = 0

        # Progress status & ETA row
        prog_status_row = tk.Frame(prog_body, bg=SURFACE)
        prog_status_row.pack(fill="x")

        self._pdf_progress_var = tk.StringVar(value="Chưa bắt đầu")
        tk.Label(prog_status_row, textvariable=self._pdf_progress_var,
                 bg=SURFACE, fg=C["text_body"],
                 font=(FONT["app"], FONT["size_sm"], "bold")).pack(side="left")

        tk.Label(prog_status_row, textvariable=self._pdf_eta_var,
                 bg=SURFACE, fg=C["warning_dark"],
                 font=(FONT["app"], FONT["size_sm"])).pack(side="right")

        # ── Log / preview output ──
        log_frame = tk.Frame(right, bg=SURFACE,
                             highlightbackground=BORDER, highlightthickness=1)
        log_frame.pack(fill="both", expand=True)

        log_hdr = tk.Frame(log_frame, bg="#E0F2FE")
        log_hdr.pack(fill="x")
        tk.Label(log_hdr, text="📝 Nhật ký chuyển đổi", bg="#E0F2FE",
                 fg=C["primary_xl"],
                 font=(FONT["app"], FONT["size_md"], "bold"),
                 padx=8, pady=6).pack(side="left")

        self._pdf_open_btn = tk.Button(
            log_hdr, text="📂 Mở file Word",
            bg=C["success"], fg="white",
            activebackground="#059669", activeforeground="white",
            disabledforeground="#A7F3D0",
            font=(FONT["app"], FONT["size_sm"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=12, pady=4,
            command=self._open_pdf_result, state="disabled",
        )
        self._pdf_open_btn.pack(side="right", padx=(4, 8), pady=4)

        self._pdf_folder_btn = tk.Button(
            log_hdr, text="📁 Mở thư mục",
            bg="#0284C7", fg="white",
            activebackground="#0369A1", activeforeground="white",
            disabledforeground="#BAE6FD",
            font=(FONT["app"], FONT["size_sm"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=10, pady=4,
            command=self._open_pdf_folder, state="disabled",
        )
        self._pdf_folder_btn.pack(side="right", padx=(4, 0), pady=4)

        log_body = tk.Frame(log_frame, bg=SURFACE)
        log_body.pack(fill="both", expand=True, padx=4, pady=4)

        self._pdf_log = tk.Text(
            log_body, wrap="word", state="disabled",
            bg=SURFACE, fg=C["text_body"],
            font=(FONT["app"], FONT["size_sm"]),
            relief="flat", bd=0, padx=8, pady=4,
        )
        pdf_log_sb = ttk.Scrollbar(log_body, command=self._pdf_log.yview)
        self._pdf_log.configure(yscrollcommand=pdf_log_sb.set)
        self._pdf_log.pack(side="left", fill="both", expand=True)
        pdf_log_sb.pack(side="right", fill="y")

        # Output path holder
        self._pdf_output_path: Optional[str] = None

    # ── AI Text mode ────────────────────────────────────────────────────

    # ── Prompt template for users to copy to external chatbots ─────────
    # Các ô [...] là CHỖ TRỐNG cho người dùng chỉnh trước khi gửi cho
    # ChatGPT/Claude/Gemini. App tự điền sẵn {grade}/{topic} dựa trên cấu
    # hình hiện tại; phần còn lại do user quyết định.
    _CHATBOT_PROMPT_TEMPLATE = """\
Bạn là AI chuyên gia biên soạn đề Toán THPT Việt Nam, 10+ năm kinh nghiệm.
Hãy tạo BỘ CÂU HỎI theo YÊU CẦU bên dưới và tuân thủ TUYỆT ĐỐI cấu trúc app.

════════════════════════════════════════════════════════════════════════
[★] YÊU CẦU CỦA TÔI — BẠN ĐỌC KỸ TRƯỚC KHI LÀM
════════════════════════════════════════════════════════════════════════
• Môn:     [Toán]
• Lớp:     [{grade}]
• Chủ đề:  [{topic}]

CƠ CẤU CÂU HỎI (điền số câu mỗi loại; để 0 nếu không cần):
• TN  — Trắc nghiệm 4 phương án A/B/C/D :  [{n_tn}] câu
• DS  — Đúng/Sai 4 ý a/b/c/d            :  [{n_ds}] câu
• TLN — Trả lời ngắn (đáp án là 1 số)   :  [{n_tln}] câu
• TL  — Tự luận trình bày các bước       :  [{n_tl}] câu
→ TỔNG CỘNG: [{num_questions}] câu

PHÂN BỔ MỨC ĐỘ (% hoặc số câu — tổng = 100%):
• NB (Nhận biết)  : [40%]
• TH (Thông hiểu) : [40%]
• VD (Vận dụng)   : [20%]

YÊU CẦU THÊM (tuỳ chọn — xoá nếu không cần):
• [Tập trung dạng bài: ...]
• [Tránh dạng bài: ...]
• [Có/không có hình vẽ; có/không có ngữ cảnh thực tế]

════════════════════════════════════════════════════════════════════════
QUY TẮC BẮT BUỘC — KHÔNG ĐƯỢC VI PHẠM
════════════════════════════════════════════════════════════════════════

[A] KHUNG KHỐI (quan trọng nhất — sai là app không đọc được)
    • Mỗi câu BẮT BUỘC bọc trong cặp ===CAU=== ... ===KETCAU===
    • Giữa 2 khối có 1 dòng trống. KHÔNG đặt text ngoài khối.
    • KHÔNG dùng markdown (``` ``` , **, ##…) — chỉ text thuần.
    • CẤM TUYỆT ĐỐI CHÈN NGUỒN / CITATION: TUYỆT ĐỐI KHÔNG chèn bất kỳ thẻ trích dẫn
      nguồn như [cite: ...], [source: ...], [1], [2] vào bất kỳ vị trí nào.

[B] CÔNG THỨC TOÁN — CHỈ DÙNG ${{...}}$ (KHÔNG dùng $$...$$)
    • CHỈ MỘT định dạng duy nhất: ${{biểu_thức}}$ — luôn có cặp {{ }}
      bọc bên trong cặp $ $.
        ĐÚNG  : ${{x^2 - 5x + 6 = 0}}$
        ĐÚNG  : ${{\\frac{{1}}{{2}}}}$, ${{\\sqrt{{x+1}}}}$
        SAI   : $x^2 - 5x + 6 = 0$            ← thiếu {{ }}
        SAI   : $$\\int_0^1 x^2\\,dx$$        ← CẤM $$ ... $$
        SAI   : \\(x^2\\), \\[x^2\\]          ← CẤM \\( \\) và \\[ \\]
    • Lý do: app chỉ render đúng dạng ${{...}}$. $$ ... $$ hay \\( \\)
      sẽ bị hỏng định dạng khi xuất Word.
    • CẤM Unicode ký hiệu toán:
         SAI:  x² − 5x + 6 = 0, √(x+1), ≤, ≥, ≠, π, α, β, ∫, ∑
         ĐÚNG: ${{x^2 - 5x + 6 = 0}}$, ${{\\sqrt{{x+1}}}}$, ${{\\leq}}$,
               ${{\\geq}}$, ${{\\neq}}$, ${{\\pi}}$, ${{\\alpha}}$,
               ${{\\beta}}$, ${{\\int}}$, ${{\\sum}}$
    • Phân số ${{\\frac{{a}}{{b}}}}$, căn ${{\\sqrt{{x}}}}$,
      mũ ${{x^{{n}}}}$, chỉ số ${{a_{{n}}}}$, nhân ${{\\cdot}}$
      (KHÔNG dùng × hoặc *).
    • Ngoặc bao biểu thức cao: dùng \\left( \\right), \\left[ \\right],
      \\left\\{{ \\right\\}}, \\left| \\right|.
    • Ký hiệu góc: ${{\\widehat{{ABC}}}}$ — KHÔNG dùng ${{\\angle ABC}}$.

[C] PHÂN LOẠI LOẠI CÂU (LOAI)
    • TN  — Trắc nghiệm: ĐÚNG 4 phương án A/B/C/D, 1 đáp án đúng.
          Distractor (3 phương án sai) phải là LỖI SAI HỢP LÝ học sinh
          thường mắc (nhầm dấu, sai công thức nghiệm, quên chia hệ số).
          Tất cả 4 phương án phải KHÁC NHAU và độ dài tương đương.
    • DS  — Đúng–Sai: ĐÚNG 4 mệnh đề a/b/c/d cùng xoay quanh 1 tình huống.
          Chuẩn: ít nhất 1 ý Đ và 1 ý S (tránh 4/4 cùng phía).
          Lời giải mỗi ý BẮT ĐẦU bằng "Đúng. Vì..." hoặc "Sai. Vì...".
    • TLN — Trả lời ngắn: đáp án là 1 SỐ tối đa 4 ký tự (VD: 14, 0,5, -1,2).
          Dùng dấu PHẨY thập phân kiểu Việt Nam (0,5 không phải 0.5).
    • TL  — Tự luận: trình bày lời giải đầy đủ, viết liền mạch (KHÔNG
          chia "Bước 1/Bước 2"), giải đến kết quả cuối cùng.

[D] PHÂN LOẠI MỨC ĐỘ (MUCDO)
    • NB (Nhận biết) — 1 bước áp dụng công thức, dùng số nguyên nhỏ.
    • TH (Thông hiểu) — 2–3 bước biến đổi, hiểu bản chất khái niệm.
    • VD (Vận dụng) — bài toán thực tế (chi phí, diện tích, tối ưu),
                      kết hợp 2–3 bước; KHÔNG dạng SGK trừu tượng.

[E] ĐA DẠNG HOÁ & BẢNG SỐ LIỆU & HÌNH VẼ
    • Các câu phải đa dạng: không hỏi cùng 1 chi tiết, không dùng cùng
      1 con số, không lặp cách dẫn.
    • BẢNG SỐ LIỆU: Dùng bảng Markdown chuẩn (| Cột 1 | Cột 2 |\n| :--- | :--- |\n| A | B |),
      hoặc bảng LaTeX \\begin{{tabular}}{{...}}...\\end{{tabular}}, hoặc phân cách bằng "|".
      Đảm bảo đủ số cột ở mọi dòng, không ngắt dòng dở dang.
    • HÌNH VẼ / ĐỒ THỊ / BBT: Dùng mã TikZ trực tiếp trong NOIDUNG hoặc LOIGIAI.
      Vẽ bảng biến thiên dùng \\tkzTabVar (CẤM dùng \\tkzTabVector).
      KHÔNG viết "Hình vẽ:" mô tả bằng chữ.

════════════════════════════════════════════════════════════════════════
CẤU TRÚC MỖI CÂU — COPY CHÍNH XÁC TỪNG DÒNG
════════════════════════════════════════════════════════════════════════

===CAU===
LOAI: TN | DS | TLN | TL
MUCDO: NB | TH | VD
CHUONG: <tên chủ đề cụ thể, VD: "Hàm số bậc hai", "Tích phân", "Xác suất">
NOIDUNG: <nội dung câu hỏi; công thức trong ${{...}}$>
A: <phương án A>           (chỉ TN)
B: <phương án B>           (chỉ TN)
C: <phương án C>           (chỉ TN)
D: <phương án D>           (chỉ TN)
a: <mệnh đề a>             (chỉ DS)
b: <mệnh đề b>             (chỉ DS)
c: <mệnh đề c>             (chỉ DS)
d: <mệnh đề d>             (chỉ DS)
DAPAN: <định dạng như mục [F] dưới đây>
LOIGIAI: <lời giải: công thức áp dụng → thay số → kết quả>
===KETCAU===

[F] ĐỊNH DẠNG DAPAN THEO LOẠI
    • TN :  DAPAN: A                      (1 ký tự A/B/C/D)
    • DS :  DAPAN: a=Đ,b=S,c=Đ,d=S        (Đ=Đúng, S=Sai)
    • TLN:  DAPAN: 14                     (số tối đa 4 ký tự, dấu , VN)
    • TL :  DAPAN: xem lời giải

════════════════════════════════════════════════════════════════════════
VÍ DỤ MINH HOẠ (1 CÂU TN — chú ý mọi ${{...}}$ ĐỀU CÓ {{ }})
════════════════════════════════════════════════════════════════════════

===CAU===
LOAI: TN
MUCDO: TH
CHUONG: Phương trình bậc hai
NOIDUNG: Giải phương trình ${{x^2 - 5x + 6 = 0}}$, ta được tập nghiệm là:
A: ${{\\left\\{{1;\\,6\\right\\}}}}$
B: ${{\\left\\{{2;\\,3\\right\\}}}}$
C: ${{\\left\\{{-2;\\,-3\\right\\}}}}$
D: ${{\\left\\{{0;\\,5\\right\\}}}}$
DAPAN: B
LOIGIAI: Ta có ${{\\Delta = 25 - 24 = 1 > 0}}$. Nghiệm
${{x = \\frac{{5 \\pm 1}}{{2}}}}$, tức ${{x_1 = 2}}$ hoặc ${{x_2 = 3}}$.
Vậy tập nghiệm là ${{\\left\\{{2;\\,3\\right\\}}}}$.
===KETCAU===

════════════════════════════════════════════════════════════════════════
CHECKLIST TỰ KIỂM TRA TRƯỚC KHI TRẢ LỜI
════════════════════════════════════════════════════════════════════════

[ ] Đủ tổng số câu yêu cầu, mỗi câu bọc trong ===CAU===...===KETCAU===.
[ ] TUYỆT ĐỐI KHÔNG có thẻ trích dẫn [cite: ...] hay [source: ...].
[ ] MỌI công thức nằm trong ${{...}}$ — có {{ và }} bọc trong cặp $.
[ ] KHÔNG có $$...$$, KHÔNG có \\(...\\), KHÔNG có \\[...\\].
[ ] Không dùng Unicode toán (², √, ≠, π, ∫, ∑, ×, ÷).
[ ] TN: đủ 4 phương án khác nhau, distractor hợp lý, không trùng đáp án.
[ ] DS: đủ 4 ý, DAPAN a=Đ,b=S,c=Đ,d=S; lời giải bắt đầu "Đúng. Vì..."/"Sai. Vì...".
[ ] TLN: đáp án ≤ 4 ký tự, dùng dấu phẩy thập phân (0,5).
[ ] Bảng số liệu đúng cấu trúc (Markdown/LaTeX), không mất dòng.
[ ] KHÔNG thêm lời mở đầu / kết thúc / markdown fence ``` ```.

CHỈ trả các khối ===CAU===...===KETCAU===. Bắt đầu ngay với ===CAU===.
"""

    def _build_ai_text_mode(self):
        """Xây dựng UI cho chế độ AI Text → Câu hỏi."""
        self._ai_text_frame = tk.Frame(self._content, bg=BG)
        self._ai_text_frame.columnconfigure(0, weight=1, uniform="ai_text_col")
        self._ai_text_frame.columnconfigure(1, weight=1, uniform="ai_text_col")
        self._ai_text_frame.rowconfigure(0, weight=1)
        self._ai_parsed_questions: list = []  # list[Question]
        self._ai_busy = False

        # ── Left: Input ──
        left = tk.Frame(self._ai_text_frame, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)

        # Header with prompt copy button
        inp_hdr = tk.Frame(left, bg="#EDE9FE")
        inp_hdr.pack(fill="x")
        tk.Label(inp_hdr, text="🤖 Dán hoặc tải cấu trúc app / LaTeX",
                 bg="#EDE9FE", fg="#5B21B6",
                 font=(FONT["app"], FONT["size_md"], "bold"),
                 padx=8, pady=6).pack(side="left")

        inp_hdr_actions = tk.Frame(left, bg="#F5F3FF")
        inp_hdr_actions.pack(fill="x")

        tk.Button(
            inp_hdr_actions, text="🗑️ Xóa",
            bg=C["danger"], fg="white",
            activebackground="#DC2626", activeforeground="white",
            font=(FONT["app"], FONT["size_sm"]),
            relief="flat", cursor="hand2", bd=0, padx=10, pady=3,
            command=self._ai_text_clear_input,
        ).pack(side="right", padx=8, pady=4)

        self._prompt_copy_btn = tk.Button(
            inp_hdr_actions, text="📋 Copy Prompt hỏi Chatbot",
            bg="#7C3AED", fg="white",
            activebackground="#6D28D9", activeforeground="white",
            font=(FONT["app"], FONT["size_sm"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=10, pady=3,
            command=self._copy_chatbot_prompt,
        )
        self._prompt_copy_btn.pack(side="left", padx=8, pady=4)

        self._ai_load_text_btn = tk.Button(
            inp_hdr_actions, text="📂 Tải TeX/TXT",
            bg="#2563EB", fg="white",
            activebackground="#1D4ED8", activeforeground="white",
            font=(FONT["app"], FONT["size_sm"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=10, pady=3,
            command=self._ai_text_load_files,
        )
        self._ai_load_text_btn.pack(side="left", padx=4, pady=4)

        # Lớp & Môn selector ngay tại header ô nhập
        tk.Label(
            inp_hdr_actions, text="🏷️ Lớp:", bg="#F5F3FF", fg=TEXT,
            font=(FONT["app"], FONT["size_sm"], "bold"),
        ).pack(side="left", padx=(8, 2))
        ttk.Combobox(
            inp_hdr_actions, textvariable=self._grade_var,
            values=["10", "11", "12", "6", "7", "8", "9", "Khác"],
            width=5, state="readonly",
        ).pack(side="left", padx=(0, 6))

        tk.Label(
            inp_hdr_actions, text="Môn:", bg="#F5F3FF", fg=TEXT,
            font=(FONT["app"], FONT["size_sm"], "bold"),
        ).pack(side="left", padx=(2, 2))
        ttk.Combobox(
            inp_hdr_actions, textvariable=self._subject_var,
            values=["Toán", "Vật lí", "Hóa học", "Sinh học", "Ngữ văn", "Lịch sử", "Địa lí", "Tiếng Anh", "Tin học", "GDCD"],
            width=8, state="readonly",
        ).pack(side="left", padx=(0, 4))

        # Action buttons ghim cố định ở đáy (side="bottom")
        act_area = tk.Frame(left, bg=BG)
        act_area.pack(side="bottom", fill="x", pady=(8, 0))

        # Input text area (chiếm phần còn lại ở trên)
        inp_frame = tk.Frame(left, bg=BORDER)
        inp_frame.pack(fill="both", expand=True, pady=(4, 0))

        self._ai_input_text = tk.Text(
            inp_frame, wrap="word", height=8,
            font=(FONT["app"], FONT["size_md"]),
            bg=SURFACE, fg=C["text_body"],
            insertbackground=TEXT,
            highlightthickness=0, bd=0,
            padx=12, pady=10,
            undo=True,
        )
        inp_sb = ttk.Scrollbar(inp_frame, orient="vertical",
                                command=self._ai_input_text.yview)
        self._ai_input_text.configure(yscrollcommand=inp_sb.set)
        self._ai_input_text.pack(side="left", fill="both", expand=True)
        inp_sb.pack(side="right", fill="y")

        # Placeholder
        self._ai_placeholder_text = (
            "Dán văn bản câu hỏi từ ChatGPT, Gemini, Claude… vào đây.\n\n"
            "Cách dùng:\n"
            "1. Nhấn \"Copy Prompt hỏi Chatbot\" → dán prompt lên ChatGPT/Gemini\n"
            "2. Copy kết quả từ chatbot → dán vào đây\n"
            "3. Chọn Lớp ngay bên trên → Nhấn \"🚀 Xuất Word trực tiếp (Auto TikZ)\" hoặc \"⚡ Nhận diện câu hỏi\"\n\n"
            "App nhận diện TRỰC TIẾP (không tốn lượt API) các dạng:\n"
            "  • Khung ===CAU===...===KETCAU===\n"
            "  • LaTeX ex_test: \\begin{ex}...\\end{ex}, \\begin{bt}...\\end{bt}\n"
            "  • Tự động loại bỏ các thẻ [cite: 41, 42] và chuẩn hóa bảng Markdown/LaTeX\n"
            "  • Tự động chuyển đổi hình vẽ TikZ sang ảnh khi xuất Word\n"
            "  • \"Câu N:\" + A./B./C./D. + \"Đáp án: X\"\n"
            "  • \"Câu N:\" + a)/b)/c)/d) + \"Đáp án: a=Đ,b=S,...\" (Đúng-Sai)\n"
            "  • \"Câu N:\" + \"Đáp án: <số>\" (Trả lời ngắn)\n\n"
            "Chỉ khi app KHÔNG nhận diện được → mới hỏi bạn có gọi AI hay không.")
        self._ai_input_text.insert("1.0", self._ai_placeholder_text)
        self._ai_input_text.configure(fg=HINT)
        self._ai_input_text.bind("<FocusIn>", self._ai_text_focus_in)
        self._ai_input_text.bind("<FocusOut>", self._ai_text_focus_out)
        self._ai_input_placeholder = True
        act_primary_row = tk.Frame(act_area, bg=BG)
        act_primary_row.pack(fill="x")
        act_secondary_row = tk.Frame(act_area, bg=BG)
        act_secondary_row.pack(fill="x", pady=(4, 0))
        act_latex_row = tk.Frame(act_area, bg=BG)
        act_latex_row.pack(fill="x", pady=(4, 0))

        # ── Hàng nút chính: Nhận diện, Xuất Word trực tiếp (Auto TikZ), Gọi AI
        self._ai_convert_btn = tk.Button(
            act_primary_row, text="⚡ Nhận diện câu hỏi",
            bg=C["success"], fg="white",
            activebackground="#059669", activeforeground="white",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=10, pady=6,
            command=self._ai_text_convert,
        )
        self._ai_convert_btn.pack(side="left", padx=4)

        self._ai_direct_export_btn = tk.Button(
            act_primary_row, text="🚀 Xuất Word trực tiếp (Auto TikZ)",
            bg="#2563EB", fg="white",
            activebackground="#1D4ED8", activeforeground="white",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=12, pady=6,
            command=self._ai_text_direct_export_word,
        )
        self._ai_direct_export_btn.pack(side="left", padx=4)

        self._ai_invoke_btn = tk.Button(
            act_primary_row, text="🤖 Gọi AI ngay",
            bg="#0EA5E9", fg="white",
            activebackground="#0284C7", activeforeground="white",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=10, pady=6,
            command=self._ai_text_invoke_inapp,
        )
        self._ai_invoke_btn.pack(side="left", padx=4)

        self._ai_export_btn = None

        self._ai_nhch_btn = tk.Button(
            act_secondary_row, text="⬆️ Thêm NHCH",
            bg="#7C3AED", fg="white",
            activebackground="#6D28D9", activeforeground="white",
            disabledforeground="#C4B5FD",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=10, pady=6,
            command=self._ai_text_upload_nhch,
            state="disabled",
        )
        self._ai_nhch_btn.pack(side="left", padx=4)

        self._ai_copy_btn = tk.Button(
            act_secondary_row, text="📋 Copy",
            bg="#E0F2FE", fg=C["primary_xl"],
            activebackground="#BAE6FD",
            disabledforeground="#94A3B8",
            font=(FONT["app"], FONT["size_md"]),
            relief="flat", cursor="hand2", bd=0, padx=8, pady=6,
            command=self._ai_text_copy_result,
            state="disabled",
        )
        self._ai_copy_btn.pack(side="left", padx=4)

        self._ai_copy_latex_btn = tk.Button(
            act_latex_row, text="📋 Copy LaTeX",
            bg="#FEF3C7", fg="#92400E",
            activebackground="#FDE68A",
            disabledforeground="#94A3B8",
            font=(FONT["app"], FONT["size_md"]),
            relief="flat", cursor="hand2", bd=0, padx=8, pady=6,
            command=self._ai_text_copy_latex,
            state="disabled",
        )
        self._ai_copy_latex_btn.pack(side="left", padx=4)

        self._ai_export_latex_btn = tk.Button(
            act_latex_row, text="📥 Xuất LaTeX",
            bg="#D97706", fg="white",
            activebackground="#B45309", activeforeground="white",
            disabledforeground="#FDE68A",
            font=(FONT["app"], FONT["size_md"], "bold"),
            relief="flat", cursor="hand2", bd=0, padx=10, pady=6,
            command=self._ai_text_export_latex,
            state="disabled",
        )
        self._ai_export_latex_btn.pack(side="left", padx=4)

        self._ai_status_lbl = tk.Label(act_area, text="", bg=BG, fg=HINT,
                                        font=(FONT["app"], FONT["size_sm"]))
        self._ai_status_lbl.pack(fill="x", anchor="w", padx=4, pady=(4, 0))

        # ── Right: Output ──
        right = tk.Frame(self._ai_text_frame, bg=BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 8), pady=8)

        # Bảng nhận diện và kết quả dùng PanedWindow để user tự kéo tỷ lệ.
        # minsize giữ bảng không bị co còn 1 dòng khi output text chiếm chỗ.
        self._ai_result_panes = tk.PanedWindow(
            right,
            orient=tk.VERTICAL,
            bg=BORDER,
            bd=0,
            sashwidth=8,
            sashrelief="raised",
            showhandle=True,
            handlesize=10,
            handlepad=4,
            opaqueresize=True,
        )
        self._ai_result_panes.pack(fill="both", expand=True)

        # Question treeview panel (top pane)
        self._ai_q_panel = tk.Frame(self._ai_result_panes, bg=BG)

        q_hdr = tk.Frame(self._ai_q_panel, bg="#EDE9FE")
        q_hdr.pack(fill="x")
        tk.Label(q_hdr, text="📊 Câu hỏi đã nhận diện", bg="#EDE9FE", fg="#5B21B6",
                 font=(FONT["app"], FONT["size_md"], "bold"),
                 padx=8, pady=6).pack(side="left")

        self._ai_q_count_lbl = tk.Label(q_hdr, text="0 câu", bg="#EDE9FE", fg="#7C3AED",
                                         font=(FONT["app"], FONT["size_sm"]))
        self._ai_q_count_lbl.pack(side="right", padx=8)

        self._ai_q_detail_lbl = tk.Label(
            self._ai_q_panel,
            text="Double-click để sửa · kéo thanh phân cách để đổi chiều cao",
            bg="#F5F3FF", fg="#7C3AED",
            font=(FONT["app"], FONT["size_sm"], "italic"),
            anchor="w", justify="left", padx=8, pady=3,
        )
        self._ai_q_detail_lbl.pack(fill="x")

        # Treeview with scrollbars
        tree_frame = tk.Frame(self._ai_q_panel, bg=BG)
        tree_frame.pack(fill="both", expand=True, pady=(4, 0))

        cols = ("stt", "subject_grade", "qtype", "level", "topic", "content_preview")
        self._ai_q_tree = ttk.Treeview(tree_frame, columns=cols,
                                        show="headings", height=10,
                                        selectmode="browse")
        self._ai_q_tree.heading("stt", text="#")
        self._ai_q_tree.heading("subject_grade", text="Môn/Lớp")
        self._ai_q_tree.heading("qtype", text="Loại")
        self._ai_q_tree.heading("level", text="Mức")
        self._ai_q_tree.heading("topic", text="Chủ đề")
        self._ai_q_tree.heading("content_preview", text="Câu hỏi")
        self._ai_q_tree.column("stt", width=35, minwidth=30, anchor="center")
        self._ai_q_tree.column("subject_grade", width=70, minwidth=60, anchor="center")
        self._ai_q_tree.column("qtype", width=45, minwidth=40, anchor="center")
        self._ai_q_tree.column("level", width=40, minwidth=35, anchor="center")
        self._ai_q_tree.column("topic", width=130, minwidth=80, anchor="w")
        self._ai_q_tree.column("content_preview", width=350, minwidth=150, anchor="w")

        # Vertical + horizontal scrollbars
        tree_vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                                  command=self._ai_q_tree.yview)
        tree_hsb = ttk.Scrollbar(tree_frame, orient="horizontal",
                                  command=self._ai_q_tree.xview)
        self._ai_q_tree.configure(yscrollcommand=tree_vsb.set,
                                   xscrollcommand=tree_hsb.set)
        self._ai_q_tree.grid(row=0, column=0, sticky="nsew")
        tree_vsb.grid(row=0, column=1, sticky="ns")
        tree_hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        self._ai_q_tree.bind("<Double-1>", self._on_ai_q_tree_double_click)

        # Output text (bottom pane)
        self._ai_output_panel = tk.Frame(self._ai_result_panes, bg=BG)
        out_hdr = tk.Frame(self._ai_output_panel, bg="#ECFDF5")
        out_hdr.pack(fill="x", pady=(8, 0))
        tk.Label(out_hdr, text="📝 Kết quả chuyển đổi", bg="#ECFDF5", fg="#065F46",
                 font=(FONT["app"], FONT["size_md"], "bold"),
                 padx=8, pady=6).pack(side="left")

        out_frame = tk.Frame(self._ai_output_panel, bg=BORDER)
        out_frame.pack(fill="both", expand=True, pady=(4, 0))

        self._ai_output_text = tk.Text(
            out_frame, wrap="word",
            font=(FONT["app"], FONT["size_md"]),
            bg=SURFACE, fg=C["text_body"],
            insertbackground=TEXT,
            highlightthickness=0, bd=0,
            padx=12, pady=10,
        )
        out_sb = ttk.Scrollbar(out_frame, orient="vertical",
                                command=self._ai_output_text.yview)
        self._ai_output_text.configure(yscrollcommand=out_sb.set)
        self._ai_output_text.pack(side="left", fill="both", expand=True)
        out_sb.pack(side="right", fill="y")

        self._ai_output_text.insert("1.0", "Kết quả chuyển đổi sẽ hiện ở đây…")
        self._ai_output_text.configure(state="disabled")

        self._ai_result_panes.add(
            self._ai_q_panel, minsize=250, stretch="always")
        self._ai_result_panes.add(
            self._ai_output_panel, minsize=170, stretch="always")

    # ── AI Text: placeholder handling ────────────────────────────────────

    def _ai_text_focus_in(self, event=None):
        if self._ai_input_placeholder:
            self._ai_input_text.delete("1.0", "end")
            self._ai_input_text.configure(fg=C["text_body"])
            self._ai_input_placeholder = False

    def _ai_text_focus_out(self, event=None):
        if not self._ai_input_text.get("1.0", "end-1c").strip():
            self._ai_input_placeholder = True
            self._ai_input_text.insert("1.0", self._ai_placeholder_text)
            self._ai_input_text.configure(fg=HINT)

    def _ai_text_load_files(self):
        """Load multiple app/LaTeX text sources into the shared local parser."""
        paths = filedialog.askopenfilenames(
            title="Tải cấu trúc app hoặc LaTeX",
            filetypes=[
                ("Tài liệu hỗ trợ", "*.tex *.txt *.docx *.html *.htm"),
                ("LaTeX", "*.tex"),
                ("Text", "*.txt"),
                ("Word", "*.docx"),
                ("HTML", "*.html *.htm"),
            ],
        )
        if not paths:
            return

        from core.exam_file_loader import extract_text_from_file

        parts = []
        errors = []
        for path in paths:
            try:
                text = extract_text_from_file(path)
                if text.strip():
                    parts.append(text.strip())
            except Exception as exc:
                errors.append(f"{Path(path).name}: {exc}")

        if not parts:
            messagebox.showerror(
                "Không đọc được file",
                "\n".join(errors) or "Các file đã chọn không có nội dung text.",
            )
            return

        self._ai_text_clear_input()
        self._ai_input_text.insert("1.0", "\n\n".join(parts))
        self._ai_input_placeholder = False
        self._ai_input_text.configure(fg=C["text_body"])
        self._ai_status_lbl.configure(
            text=f"📂 Đã tải {len(parts)}/{len(paths)} file, đang nhận diện cục bộ…"
        )
        if errors:
            messagebox.showwarning("Có file không đọc được", "\n".join(errors[:8]))
        self._ai_text_convert()

    def _ai_text_clear_input(self):
        self._ai_input_text.configure(fg=C["text_body"])
        self._ai_input_text.delete("1.0", "end")
        self._ai_input_placeholder = False
        self._ai_output_text.configure(state="normal")
        self._ai_output_text.delete("1.0", "end")
        self._ai_output_text.insert("1.0", "Kết quả chuyển đổi sẽ hiện ở đây…")
        self._ai_output_text.configure(state="disabled")
        self._clear_ai_question_table()
        self._ai_parsed_questions.clear()
        if self._ai_export_btn:
            self._ai_export_btn.configure(state="disabled")
        self._ai_nhch_btn.configure(state="disabled")
        self._ai_copy_btn.configure(state="disabled")
        self._ai_copy_latex_btn.configure(state="disabled")
        self._ai_export_latex_btn.configure(state="disabled")
        self._ai_status_lbl.configure(text="")

    def _clear_ai_question_table(self):
        """Xóa dữ liệu nhưng giữ bảng nhận diện luôn đủ lớn để thao tác."""
        for item in self._ai_q_tree.get_children():
            self._ai_q_tree.delete(item)
        self._ai_q_count_lbl.configure(text="0 câu")
        self._ai_q_detail_lbl.configure(
            text="Double-click để sửa · kéo thanh phân cách để đổi chiều cao")
        self._ensure_ai_question_table_height()

    def _ensure_ai_question_table_height(self):
        """Khôi phục tỷ lệ hợp lý nếu bảng từng bị sash kéo quá thấp."""
        def _adjust():
            try:
                total = self._ai_result_panes.winfo_height()
                current = self._ai_q_panel.winfo_height()
                if total < 400:
                    return
                target = min(max(270, int(total * 0.50)), total - 170)
                if target > 0 and current < target - 10:
                    self._ai_result_panes.sash_place(0, 0, target)
            except (tk.TclError, AttributeError):
                pass

        self.after_idle(_adjust)

    # ── AI Text: copy prompt for chatbot ───────────────────────────────

    def _copy_chatbot_prompt(self):
        """Copy prompt mẫu cho chatbot bên ngoài.

        Các trường {grade}/{topic} được app điền sẵn từ cấu hình hiện tại.
        Các trường còn lại ([n_tn]/[n_ds]/...) là placeholder; user mở
        chatbot lên thấy ngay các ô [...] và tự sửa số trước khi gửi.
        """
        subj, grade = "Toán", "12"
        if self._get_subject_grade:
            subj, grade = self._get_subject_grade()

        # Placeholder defaults — gợi ý hợp lý nhưng user sẽ sửa nếu cần.
        prompt = self._CHATBOT_PROMPT_TEMPLATE.format(
            grade=grade,
            topic=f"{subj} lớp {grade}",
            n_tn="10",
            n_ds="2",
            n_tln="2",
            n_tl="0",
            num_questions="14",
        )
        self.clipboard_clear()
        self.clipboard_append(prompt)
        self._prompt_copy_btn.configure(text="✅ Đã copy prompt!")
        self.after(2500, lambda: self._prompt_copy_btn.configure(
            text="📋 Copy Prompt hỏi Chatbot"))

    # ── AI Text: convert logic ───────────────────────────────────────────

    _AI_SYNC_PROMPT = """\
Bạn là chuyên gia biên soạn đề Toán THPT Việt Nam, 10+ năm kinh nghiệm.
CÔNG VIỆC của bạn bây giờ là CHUYỂN ĐỔI văn bản thô bên dưới sang CẤU TRÚC
CHUẨN của app MatrixExamAI. Bạn KHÔNG tạo đề mới, KHÔNG sửa lỗi toán, KHÔNG
thay đổi dữ kiện — chỉ CHUẨN HOÁ format.

════════════════════════════════════════════════════════════════════════
[1] NGUYÊN TẮC TỐI THƯỢNG — KHÔNG ĐƯỢC VI PHẠM
════════════════════════════════════════════════════════════════════════
• GIỮ NGUYÊN nội dung và ý nghĩa câu hỏi. Không đổi số, không đổi đáp án.
• KHÔNG thêm/bớt dữ kiện. Nếu đề gốc thiếu đáp án — bạn cũng ĐỂ TRỐNG.
• KHÔNG "sửa" lỗi của người nhập (sai chính tả, sai toán). GIỮ NGUYÊN.
• CHỈ LÀM SẠCH định dạng + bọc vào khung ===CAU===...===KETCAU===.

════════════════════════════════════════════════════════════════════════
[2] DỌN DẸP TEXT
════════════════════════════════════════════════════════════════════════
• Bỏ lời chào chatbot: "Sure, here is...", "Dưới đây là...", "Tôi đã tạo...",
  "Chắc chắn rồi,...", "Đây là đáp án mà...".
• Bỏ markdown fence ```, ``` ```, các dòng ---, ***, === trang trí.
• Bỏ dấu ** quanh chữ (giữ nội dung): **Đáp án** → Đáp án.
• LOẠI BỎ TRIỆT ĐỂ mọi thẻ trích dẫn, nguồn tham chiếu như [cite: 41, 42],
  [cite: ...], [source: ...], [1], [2]. Tuyệt đối không để sót lại trong text.
• Giữ nguyên số thứ tự câu gốc ("Câu 1:", "Bài 2:").
• Nếu chatbot đánh số các phương án "1)", "2)", "3)", "4)" → chuyển thành
  A/B/C/D (giữ nguyên thứ tự).
• Tương tự "(a)", "(b)", "(c)", "(d)" → a/b/c/d với DS.

════════════════════════════════════════════════════════════════════════
[3] CÔNG THỨC TOÁN — CHỈ DÙNG ${{...}}$ (KHÔNG dùng $$...$$)
════════════════════════════════════════════════════════════════════════
• CHỈ MỘT định dạng duy nhất: ${{biểu_thức}}$ — luôn có cặp {{ }} bọc
  bên trong cặp $ $.
       ĐÚNG : ${{x^2 - 5x + 6 = 0}}$, ${{\\frac{{1}}{{2}}}}$
       SAI  : $x^2 - 5x + 6 = 0$            ← thiếu {{ }}, BUỘC bọc lại
       SAI  : $$\\int_0^1 x^2\\,dx$$        ← CẤM $$ ... $$, ÉP về ${{...}}$
       SAI  : \\(x^2\\), \\[x^2\\]          ← CẤM \\( \\) và \\[ \\]
• Khi văn bản gốc dùng $$...$$ hoặc $...$ thiếu {{ }} → TỰ CHUYỂN VỀ ${{...}}$.
• CẤM Unicode ký hiệu toán:
     x² → ${{x^2}}$         √x → ${{\\sqrt{{x}}}}$    ≠ → ${{\\neq}}$
     ≤ → ${{\\leq}}$         ≥ → ${{\\geq}}$           π → ${{\\pi}}$
     α → ${{\\alpha}}$       β → ${{\\beta}}$           ∫ → ${{\\int}}$
     × → ${{\\cdot}}$ (nếu là nhân) hoặc ${{\\times}}$
• Nếu văn bản gốc thiếu \\ trước lệnh LaTeX (frac, sqrt, sin, cos, log, ln,
  pi, alpha, beta, Delta…) → TỰ THÊM vào.
• Nếu văn bản có biểu thức toán NHƯNG KHÔNG bọc ${{...}}$ → TỰ BỌC vào.

════════════════════════════════════════════════════════════════════════
[4] NHẬN DIỆN LOẠI CÂU (LOAI)
════════════════════════════════════════════════════════════════════════
TN  — Trắc nghiệm:
      ✓ Nhận diện: có 4 dòng "A.", "B.", "C.", "D." (hoặc "A)", "(A)"…).
      ✓ DAPAN: 1 ký tự A/B/C/D.

DS  — Đúng–Sai:
      ✓ Nhận diện: câu dẫn + 4 mệnh đề "a)", "b)", "c)", "d)".
      ✓ Hoặc: văn bản nói "Xét các khẳng định sau…"/"Trong các phát biểu
        sau, phát biểu nào đúng?".
      ✓ DAPAN: a=Đ,b=S,c=Đ,d=S (Đ=Đúng, S=Sai).
      ✓ Nếu mỗi ý có "(Đúng)" / "(Sai)" ở cuối → đưa vào DAPAN.

TLN — Trả lời ngắn:
      ✓ Nhận diện: không có A/B/C/D; câu kết bằng "bằng bao nhiêu?",
        "tính…", "$X = ?$", "giá trị… là…".
      ✓ DAPAN là 1 số hoặc 1 biểu thức ngắn (ví dụ: 14, $\\frac{{1}}{{2}}$, 1.5).

TL  — Tự luận:
      ✓ Nhận diện: bài dài có nhiều ý (a), (b), (c); các yêu cầu "Chứng
        minh", "Giải và biện luận", "Tìm và chứng minh".
      ✓ DAPAN: xem lời giải.

════════════════════════════════════════════════════════════════════════
[5] MỨC ĐỘ (MUCDO) — tự phán đoán từ nội dung
════════════════════════════════════════════════════════════════════════
• NB — Nhận biết: 1 bước công thức, dữ kiện đơn giản.
• TH — Thông hiểu: 2–3 bước biến đổi, hiểu khái niệm.
• VD — Vận dụng: bài toán thực tế, nhiều bước, cần chiến lược.
• KHÔNG xác định được → ghi TH (mặc định).

════════════════════════════════════════════════════════════════════════
[6] CẤU TRÚC OUTPUT — COPY ĐÚNG TỪNG DÒNG
════════════════════════════════════════════════════════════════════════

===CAU===
LOAI: TN | DS | TLN | TL
MUCDO: NB | TH | VD
CHUONG: <tên chủ đề tự suy từ nội dung, VD "Hàm số bậc hai", "Tích phân",
         "Xác suất", "Nguyên hàm", "Khoảng cách trong không gian"…>
NOIDUNG: <nội dung câu hỏi; công thức trong ${{...}}$>
A: <phương án A>                          (chỉ cho TN)
B: <phương án B>                          (chỉ cho TN)
C: <phương án C>                          (chỉ cho TN)
D: <phương án D>                          (chỉ cho TN)
a: <mệnh đề a>                            (chỉ cho DS)
b: <mệnh đề b>                            (chỉ cho DS)
c: <mệnh đề c>                            (chỉ cho DS)
d: <mệnh đề d>                            (chỉ cho DS)
DAPAN: <tùy loại — xem mục [4]>
LOIGIAI: <nếu gốc có lời giải → giữ nguyên; nếu không có → ghi "Xem hướng dẫn">
===KETCAU===

════════════════════════════════════════════════════════════════════════
[7] XỬ LÝ ĐẶC BIỆT
════════════════════════════════════════════════════════════════════════
• Nếu có code TikZ: \\begin{{tikzpicture}}...\\end{{tikzpicture}} → GIỮ NGUYÊN
  trong NOIDUNG hoặc LOIGIAI. KHÔNG viết "Hình vẽ:" mô tả bằng chữ.
• Nếu có bảng số liệu (bảng Markdown | col | col |, LaTeX \\begin{{tabular}}...\\end{{tabular}},
  hoặc phân cách |): Giữ nguyên đúng định dạng bảng, bảo toàn đầy đủ các dòng và cột.
• Văn bản có nhiều câu → tách thành nhiều khối ===CAU===...===KETCAU===,
  theo thứ tự xuất hiện.
• Một đề thi đầy đủ → xử lý TẤT CẢ các câu, không bỏ sót.

════════════════════════════════════════════════════════════════════════
[8] CHECKLIST TỰ KIỂM TRA TRƯỚC KHI TRẢ LỜI
════════════════════════════════════════════════════════════════════════
[ ] Mỗi câu bọc đúng trong cặp ===CAU===...===KETCAU===.
[ ] ĐÃ XÓA SẠCH toàn bộ thẻ trích dẫn [cite: ...] và [source: ...].
[ ] Không có text ngoài khối (không preamble, không postscript).
[ ] MỌI công thức nằm trong ${{...}}$ — có {{ và }} bọc trong cặp $.
[ ] KHÔNG còn $$...$$, KHÔNG còn \\(...\\), KHÔNG còn \\[...\\].
[ ] Không còn Unicode toán (², √, ≠, π, ∫, α, ×, ÷) — đã LaTeX hoá.
[ ] TN có đủ 4 phương án + 1 đáp án; DS có đủ 4 ý + DAPAN a=/b=/c=/d=.
[ ] Bảng số liệu giữ nguyên cấu trúc (Markdown/LaTeX), không mất dòng.
[ ] LOAI / MUCDO / CHUONG đều có giá trị, không để trống.
[ ] LOIGIAI — giữ nguyên nếu gốc có, ghi "Xem hướng dẫn" nếu không.

CHỈ trả các khối ===CAU===...===KETCAU===. Bắt đầu ngay ở dòng đầu tiên.
KHÔNG thêm lời mở đầu, KHÔNG thêm lời kết thúc, KHÔNG thêm markdown.

════════════════════════════════════════════════════════════════════════
VĂN BẢN CẦN CHUYỂN ĐỔI (ở bên dưới — bắt đầu xử lý ngay):
════════════════════════════════════════════════════════════════════════
"""

    def _ai_text_invoke_inapp(self):
        """[FRICTION-1] Gọi AI nội bộ với prompt template chuẩn → trả questions.

        Bỏ qua flow "copy prompt → chatbot ngoài → paste" — user chỉ cần:
          1. (Optional) Đọc tab Cài đặt để xác nhận Lớp/Môn.
          2. Click "🤖 Gọi AI ngay".
          3. App tự build prompt + gọi AI + đổ kết quả vào input box.
          4. _ai_text_convert() tự chạy parse + show questions.

        Worker thread → không block UI.
        """
        if self._ai_busy:
            return
        if self._get_ai_call is None:
            messagebox.showerror(
                "Chưa cấu hình AI",
                "Vui lòng vào tab Cài đặt ⚙️ và nhập API Key.",
            )
            return

        # Build prompt template từ Cài đặt hiện tại
        subj, grade = "Toán", "12"
        if self._get_subject_grade:
            try:
                subj, grade = self._get_subject_grade()
            except Exception:
                pass

        # Dùng template prompt sẵn có _CHATBOT_PROMPT_TEMPLATE — placeholder
        # đã được {grade}/{topic} fill sẵn ở app, user không cần sửa gì.
        prompt = self._CHATBOT_PROMPT_TEMPLATE.format(
            grade=grade,
            topic=f"{subj} lớp {grade}",
            n_tn="10",  # default — user có thể chỉnh sau ở Smart Prompt
            n_ds="2",
            n_tln="2",
            n_tl="0",
            num_questions="14",
        )

        # Confirm với user trước (vì tốn nhiều lượt API)
        ok = messagebox.askyesno(
            "Gọi AI nội bộ",
            f"Sẽ gọi AI với prompt chuẩn cho:\n"
            f"  • Môn: {subj}\n"
            f"  • Lớp: {grade}\n"
            f"  • 14 câu (10 TN + 2 DS + 2 TLN)\n\n"
            f"Tác vụ tốn 1 lượt API. Tiếp tục?",
        )
        if not ok:
            return

        self._ai_busy = True
        self._ai_invoke_btn.configure(state="disabled", text="⏳ AI đang tạo…")
        self._ai_status_lbl.configure(text="🤖 Đang gọi AI nội bộ…")

        def _worker():
            try:
                ai_gen = self._get_ai_call()
                response = ai_gen(prompt) or ""
                self.after(0, self._on_inapp_response, response, None)
            except Exception as e:
                self.after(0, self._on_inapp_response, "", str(e))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_inapp_response(self, response: str, error: Optional[str]) -> None:
        """[FRICTION-1] Callback (main thread) sau khi AI in-app trả lời."""
        self._ai_busy = False
        self._ai_invoke_btn.configure(state="normal",
                                       text="🤖 Gọi AI ngay")

        if error:
            self._ai_status_lbl.configure(text=f"❌ AI lỗi: {error[:80]}")
            messagebox.showerror("Lỗi gọi AI", error)
            return

        if not response.strip():
            self._ai_status_lbl.configure(text="⚠️ AI trả về rỗng")
            messagebox.showwarning(
                "AI không trả lời",
                "AI trả về rỗng. Hãy thử lại sau ít phút.",
            )
            return

        # Đổ response vào input box → trigger _ai_text_convert ngay
        self._ai_text_clear_input()  # clear placeholder + old content
        self._ai_input_text.insert("1.0", response)
        self._ai_input_placeholder = False
        self._ai_input_text.configure(fg=C["text_body"])
        # Auto-parse
        self._ai_text_convert()

    def _ai_text_convert(self):
        """Convert pasted AI text into structured questions.

        Pipeline nhận diện:
          [1] Thử parser dùng chung cho cấu trúc app, LaTeX ex_test, nội dung
              trộn hai cấu trúc và văn bản tự nhiên.
          [2] Nếu local parser không nhận diện được câu nào → hỏi user
              có muốn nhờ AI đồng bộ không (tốn lượt gọi API). Chỉ gọi AI khi
              user xác nhận.
        """
        raw = self._ai_input_text.get("1.0", "end-1c").strip()
        if not raw or self._ai_input_placeholder:
            messagebox.showinfo("Thông báo", "Vui lòng dán văn bản AI vào ô bên trái.")
            return

        # ── [1] Thử LOCAL PARSER dùng chung (không cần AI) ─────────────────
        try:
            from core.exam_file_loader import parse_questions_from_text

            local_qs, local_tier = parse_questions_from_text(raw)
        except Exception as e:
            _log.warning("shared question parser error (fallback AI): %s",
                         e, exc_info=True)
            local_qs = []
            local_tier = "none"

        if local_qs:
            # Gán grade và subject đã chọn
            subj = self._subject_var.get() if hasattr(self, "_subject_var") and self._subject_var.get() else "Toán"
            grade = self._grade_var.get() if hasattr(self, "_grade_var") and self._grade_var.get() else "12"
            for q in local_qs:
                if not getattr(q, "topic", ""):
                    q.topic = f"{subj} {grade}".strip()

            # Tự động chuyển đổi TikZ sang ảnh nếu phát hiện câu có TikZ
            try:
                from core.models import ExamData
                from services.tikz_vector_workflow import count_pending_blocks, convert_exam_tikz_to_png
                temp_exam = ExamData("TEMP", subj, grade, "1", "2025", "90", local_qs)
                if count_pending_blocks(temp_exam) > 0:
                    convert_exam_tikz_to_png(temp_exam)
            except Exception as e_tikz:
                _log.warning("Auto render TikZ in _ai_text_convert: %s", e_tikz)

            self._show_parsed_questions_direct(local_qs)
            tier_labels = {
                "exact": "cấu trúc app",
                "latex": "LaTeX ex_test",
                "mixed": "cấu trúc app + LaTeX",
                "natural": "văn bản tự nhiên",
            }
            self._ai_status_lbl.configure(
                text=(
                    f"⚡ Nhận diện cục bộ {len(local_qs)} câu "
                    f"({tier_labels.get(local_tier, local_tier)}, không dùng AI)"
                )
            )
            return

        # ── [2] Không parse được → hỏi user có muốn gọi AI không ────────────
        if self._ai_busy:
            return
        if self._get_ai_call is None:
            messagebox.showerror(
                "Không nhận diện được",
                "Không nhận diện được câu hỏi nào trong văn bản, và cũng chưa\n"
                "cấu hình AI để đồng bộ cấu trúc.\n\n"
                "Hãy kiểm tra:\n"
                "  • Văn bản có dòng 'Câu 1:', 'Bài 1:' không?\n"
                "  • Có đáp án 'Đáp án: X' hay 'A./B./C./D.' không?\n"
                "  • Hoặc vào tab Cài đặt → nhập API key để bật AI đồng bộ.")
            return

        confirm = messagebox.askyesno(
            "Nhận diện cục bộ thất bại",
            "Không nhận diện được cấu trúc câu hỏi trong văn bản này.\n\n"
            "Bạn có muốn nhờ AI đồng bộ cấu trúc không?\n"
            "(Việc này sẽ TỐN 1 LƯỢT gọi API của bạn.)\n\n"
            "Mẹo: có thể chỉnh văn bản theo mẫu 'Câu 1: ... A. ... Đáp án: …'\n"
            "để app nhận diện trực tiếp mà không cần AI.")
        if not confirm:
            self._ai_status_lbl.configure(
                text="⏸ Đã huỷ — văn bản chưa đúng cấu trúc để parse tự động.")
            return

        self._ai_busy = True
        self._ai_convert_btn.configure(state="disabled", text="⏳ AI đang đồng bộ…")
        self._ai_status_lbl.configure(text="Đang gửi tới AI…")

        threading.Thread(target=self._do_ai_sync, args=(raw,), daemon=True).start()

    def _do_ai_sync(self, raw: str):
        """Worker thread: call AI to convert text → ===CAU=== structure."""
        try:
            ai_gen = self._get_ai_call()
            prompt = self._AI_SYNC_PROMPT + raw
            result = ai_gen(prompt)
            self.after(0, self._on_ai_sync_done, result, None)
        except Exception as e:
            self.after(0, self._on_ai_sync_done, None, e)

    def _on_ai_sync_done(self, result: Optional[str], error: Optional[Exception]):
        self._ai_busy = False
        self._ai_convert_btn.configure(state="normal", text="⚡ Nhận diện câu hỏi")

        if error:
            self._ai_status_lbl.configure(text="❌ Lỗi AI")
            messagebox.showerror("Lỗi AI", str(error))
            return

        # Parse AI response for ===CAU=== blocks
        blocks = re.findall(r"===CAU===(.*?)===KETCAU===", result, re.DOTALL | re.IGNORECASE)
        if blocks:
            self._parse_and_show_questions(blocks)
        else:
            # AI didn't return structured output → show cleaned text
            self._clear_ai_question_table()
            self._ai_parsed_questions.clear()
            cleaned = self._clean_ai_text(result)
            self._ai_output_text.configure(state="normal")
            self._ai_output_text.delete("1.0", "end")
            self._ai_output_text.insert("1.0", cleaned)
            self._ai_output_text.configure(state="disabled")
            self._ai_status_lbl.configure(
                text="⚠️ AI không trả về cấu trúc. Hiển thị văn bản đã làm sạch.")
            self._ai_copy_btn.configure(state="normal")
            if self._ai_export_btn:
                self._ai_export_btn.configure(state="normal")

    def _parse_and_show_questions(self, blocks: list[str]):
        """Parse ===CAU=== blocks → Question objects and display."""
        from core.parser import parse_one_question

        questions = []
        errors = []
        for i, block in enumerate(blocks, 1):
            full_block = f"===CAU===\n{block}\n===KETCAU==="
            q = parse_one_question(full_block)
            if q:
                questions.append(q)
            else:
                errors.append(i)

        self._ai_parsed_questions = questions

        # Get subject/grade from config
        subj, grade = "Toán", ""
        if self._get_subject_grade:
            subj, grade = self._get_subject_grade()
        subj_grade = f"{subj} {grade}".strip() if grade else subj

        _QTYPE_SHORT = {"TN": "TN", "DS": "DS", "TLN": "TLN", "TL": "TL"}

        # Show in treeview
        for item in self._ai_q_tree.get_children():
            self._ai_q_tree.delete(item)

        for idx, q in enumerate(questions, 1):
            preview = q.question[:120] + "…" if len(q.question) > 120 else q.question
            preview = preview.replace("\n", " ")
            topic = q.topic[:30] + "…" if len(q.topic) > 30 else q.topic
            self._ai_q_tree.insert("", "end", iid=str(idx - 1),
                values=(
                    idx,
                    subj_grade,
                    _QTYPE_SHORT.get(q.qtype, q.qtype),
                    q.level,
                    topic,
                    preview,
                ))

        self._ai_q_count_lbl.configure(text=f"{len(questions)} câu")
        self._ai_q_detail_lbl.configure(
            text=f"Double-click để sửa · TN: {sum(1 for q in questions if q.qtype=='TN')}  "
                 f"DS: {sum(1 for q in questions if q.qtype=='DS')}  "
                 f"TLN: {sum(1 for q in questions if q.qtype=='TLN')}  "
                 f"TL: {sum(1 for q in questions if q.qtype=='TL')}")
        self._ensure_ai_question_table_height()

        # Show formatted output
        output = self._format_questions_text(questions)
        self._ai_output_text.configure(state="normal")
        self._ai_output_text.delete("1.0", "end")
        self._ai_output_text.insert("1.0", output)
        self._ai_output_text.configure(state="disabled")

        status = f"✅ Nhận diện {len(questions)}/{len(blocks)} câu hỏi"
        if errors:
            status += f"  ⚠️ Lỗi câu: {', '.join(str(e) for e in errors)}"
        self._ai_status_lbl.configure(text=status)
        if self._ai_export_btn:
            self._ai_export_btn.configure(state="normal")
        self._ai_nhch_btn.configure(state="normal")
        self._ai_copy_btn.configure(state="normal")
        self._ai_copy_latex_btn.configure(state="normal")
        self._ai_export_latex_btn.configure(state="normal")

    def _show_parsed_questions_direct(self, questions: list):
        """Hiển thị list[Question] đã được parse sẵn (bởi natural_parser).

        Khác `_parse_and_show_questions`: hàm kia nhận string blocks và tự parse;
        hàm này nhận trực tiếp Question objects → chỉ lo phần hiển thị.
        """
        self._ai_parsed_questions = list(questions)

        # Lấy subject/grade từ config (nếu có)
        subj, grade = "Toán", ""
        if self._get_subject_grade:
            subj, grade = self._get_subject_grade()
        subj_grade = f"{subj} {grade}".strip() if grade else subj

        _QTYPE_SHORT = {"TN": "TN", "DS": "DS", "TLN": "TLN", "TL": "TL"}

        # Clear + đổ dữ liệu vào treeview
        for item in self._ai_q_tree.get_children():
            self._ai_q_tree.delete(item)

        for idx, q in enumerate(questions, 1):
            preview = q.question[:120] + "…" if len(q.question) > 120 else q.question
            preview = preview.replace("\n", " ")
            topic = (q.topic or "")
            topic = topic[:30] + "…" if len(topic) > 30 else topic
            self._ai_q_tree.insert("", "end", iid=str(idx - 1),
                values=(
                    idx, subj_grade,
                    _QTYPE_SHORT.get(q.qtype, q.qtype),
                    q.level, topic, preview,
                ))

        self._ai_q_count_lbl.configure(text=f"{len(questions)} câu")
        self._ai_q_detail_lbl.configure(
            text=f"Double-click để sửa · TN: {sum(1 for q in questions if q.qtype=='TN')}  "
                 f"DS: {sum(1 for q in questions if q.qtype=='DS')}  "
                 f"TLN: {sum(1 for q in questions if q.qtype=='TLN')}  "
                 f"TL: {sum(1 for q in questions if q.qtype=='TL')}")
        self._ensure_ai_question_table_height()

        # Formatted output text
        output = self._format_questions_text(questions)
        self._ai_output_text.configure(state="normal")
        self._ai_output_text.delete("1.0", "end")
        self._ai_output_text.insert("1.0", output)
        self._ai_output_text.configure(state="disabled")

        self._ai_status_lbl.configure(
            text=f"⚡ Nhận diện cục bộ: {len(questions)} câu (không tốn API)")
        if self._ai_export_btn:
            self._ai_export_btn.configure(state="normal")
        self._ai_nhch_btn.configure(state="normal")
        self._ai_copy_btn.configure(state="normal")
        self._ai_copy_latex_btn.configure(state="normal")
        self._ai_export_latex_btn.configure(state="normal")

    def _on_ai_q_tree_double_click(self, event=None):
        """Double-click một dòng AI Text để sửa câu trước khi xuất/lưu."""
        sel = self._ai_q_tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])
        except (ValueError, TypeError):
            return
        if idx < 0 or idx >= len(self._ai_parsed_questions):
            return

        subj, grade = "Toán", "12"
        if self._get_subject_grade:
            try:
                subj, grade = self._get_subject_grade()
            except Exception:
                pass

        try:
            from ui.dialog_nhch_preview import _QuestionEditDialog
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không mở được dialog sửa: {exc}")
            return

        _QuestionEditDialog(
            self.winfo_toplevel(),
            self._ai_parsed_questions[idx],
            subj,
            grade,
            on_save=self._refresh_ai_question_table_after_edit,
        )

    def _refresh_ai_question_table_after_edit(self):
        """Cập nhật bảng và văn bản AI Text sau khi sửa một câu hỏi."""
        questions = self._ai_parsed_questions
        if not questions:
            return

        subj, grade = "Toán", ""
        if self._get_subject_grade:
            try:
                subj, grade = self._get_subject_grade()
            except Exception:
                pass
        subj_grade = f"{subj} {grade}".strip() if grade else subj

        for idx, q in enumerate(questions, 1):
            preview = (q.question or "").replace("\n", " ")
            preview = preview[:120] + "…" if len(preview) > 120 else preview
            topic = q.topic or ""
            topic = topic[:30] + "…" if len(topic) > 30 else topic
            try:
                self._ai_q_tree.item(
                    str(idx - 1),
                    values=(idx, subj_grade, q.qtype, q.level, topic, preview),
                )
            except tk.TclError:
                pass

        self._ai_q_count_lbl.configure(text=f"{len(questions)} câu")
        self._ai_q_detail_lbl.configure(
            text=f"Double-click để sửa · TN: {sum(1 for q in questions if q.qtype=='TN')}  "
                 f"DS: {sum(1 for q in questions if q.qtype=='DS')}  "
                 f"TLN: {sum(1 for q in questions if q.qtype=='TLN')}  "
                 f"TL: {sum(1 for q in questions if q.qtype=='TL')}")

        output = self._format_questions_text(questions)
        self._ai_output_text.configure(state="normal")
        self._ai_output_text.delete("1.0", "end")
        self._ai_output_text.insert("1.0", output)
        self._ai_output_text.configure(state="disabled")
        self._ai_status_lbl.configure(text="✅ Đã cập nhật câu hỏi đã sửa")

    @staticmethod
    def _clean_ai_text(raw: str) -> str:
        """Clean AI chatbot text: strip markdown, filler, preserve math."""
        lines = raw.splitlines()
        cleaned = []
        skip_patterns = [
            r"^\s*(?:Sure|Here|Of course|Certainly|I'll|Let me|Okay|Great)",
            r"^\s*(?:Dưới đây|Tôi sẽ|Đây là|Chắc chắn|Được rồi|Rất xin lỗi|Xin lỗi)",
            r"^\s*(?:Để tiện cho bạn|Mình xin trình bày|Đề tiện)",
            r"^\s*```",
            r"^\s*---+\s*$",
            r"^\s*\*\*\*+\s*$",
            r"^\s*#{1,3}\s*$",
        ]
        for line in lines:
            stripped = line.strip()
            # Skip empty lines at start
            if not cleaned and not stripped:
                continue
            # Skip AI filler lines
            if any(re.match(p, stripped, re.IGNORECASE) for p in skip_patterns):
                continue
            cleaned.append(line)

        # Remove trailing empty lines
        while cleaned and not cleaned[-1].strip():
            cleaned.pop()

        text = "\n".join(cleaned)

        # Clean markdown: **bold** → bold, *italic* → italic
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", text)

        # Clean leading bullet markers: "* text" → "text" (but not inside math $*$)
        text = re.sub(r"^(\s*)\*\s+", r"\1", text, flags=re.MULTILINE)

        # Chuẩn hóa toàn bộ công thức toán học về dạng ${...}$
        text = normalize_math_to_braced_dollars(text)

        return text.strip()

    @staticmethod
    def _format_questions_text(questions: list) -> str:
        """Format danh sách Question → text Word-ready (paste vào Word đẹp ngay).

        Dùng `export/question_formatter.py` — nguồn duy nhất cho format
        chuẩn xuất Word. Đảm bảo:
          • "Câu N." mở đầu mỗi câu.
          • TN: A./B./C./D. cùng dòng, ngăn TAB.
          • DS: a./b./c./d. trên các dòng riêng.
          • TLN: hộp đáp án |a|b|c|d| 4 ô.
          • Đáp án: ...   Lời giải: ...
          • Mỗi câu cách nhau ĐÚNG 1 dòng trống.
        """
        from export.question_formatter import format_questions
        return format_questions(questions, include_solution=True)

    # ── AI Text: 1-Click Direct Export Word (Auto Normalize -> Auto TikZ -> Word) ───

    def _ai_text_direct_export_word(self):
        """[1-CLICK WORKFLOW] Chuẩn hóa câu hỏi -> Tự động chuyển đổi TikZ -> Xuất Word."""
        raw = self._ai_input_text.get("1.0", "end-1c").strip()
        if not raw or self._ai_input_placeholder:
            messagebox.showinfo(
                "Thông báo",
                "Vui lòng dán nội dung câu hỏi hoặc LaTeX vào ô bên trái trước khi xuất Word."
            )
            return

        default_file = "De_thi_chuyen_doi.docx"
        save_path = filedialog.asksaveasfilename(
            title="Lưu file Word (Đã tự động chuyển ảnh TikZ)",
            defaultextension=".docx",
            initialfile=default_file,
            filetypes=[("Word Document", "*.docx")],
        )
        if not save_path:
            return

        self._ai_busy = True
        self._ai_convert_btn.configure(state="disabled")
        if hasattr(self, "_ai_direct_export_btn"):
            self._ai_direct_export_btn.configure(state="disabled", text="⏳ Đang xử lý…")
        self._ai_status_lbl.configure(text="⏳ Đang chuẩn hóa câu hỏi, bảng & chuyển đổi ảnh TikZ...")

        subj = self._subject_var.get() if hasattr(self, "_subject_var") and self._subject_var.get() else "Toán"
        grade = self._grade_var.get() if hasattr(self, "_grade_var") and self._grade_var.get() else "12"

        def _worker():
            try:
                from core.exam_file_loader import parse_questions_from_text
                from core.models import ExamData
                from export.word_exporter import export_to_word
                from services.tikz_vector_workflow import convert_exam_tikz_to_emf, convert_exam_tikz_to_png, count_pending_blocks
                from config import is_word_auto_convert_tables_enabled

                # 1. Parse câu hỏi (đã tích hợp tự động dọn dẹp [cite: ...] và nhận diện cấu trúc)
                qs, tier = parse_questions_from_text(raw)
                if not qs:
                    self.after(0, self._on_direct_export_failed,
                               "Không nhận diện được câu hỏi nào từ nội dung đã nhập.\n"
                               "Hãy kiểm tra lại định dạng câu hỏi hoặc cấu trúc LaTeX.")
                    return

                # 2. Gán metadata cho các câu
                for q in qs:
                    if not getattr(q, "topic", ""):
                        q.topic = f"{subj} {grade}".strip()

                # 3. Tạo ExamData
                exam_title = f"ĐỀ THI MÔN {subj.upper()} - LỚP {grade}".strip()
                exam = ExamData(
                    exam_title=exam_title,
                    subject=subj,
                    grade=grade,
                    semester="1",
                    year="2025-2026",
                    time="90",
                    questions=qs,
                )

                # 4. Tự động chuyển đổi toàn bộ hình vẽ TikZ sang ảnh
                if count_pending_blocks(exam) > 0:
                    try:
                        convert_exam_tikz_to_emf(exam)
                    except Exception as e_emf:
                        _log.warning("convert_exam_tikz_to_emf fallback: %s", e_emf)
                        try:
                            convert_exam_tikz_to_png(exam)
                        except Exception as e_png:
                            _log.warning("convert_exam_tikz_to_png failed: %s", e_png)

                # 5. Xuất file Word với chuẩn hóa bảng tự động
                export_to_word(
                    exam,
                    save_path,
                    include_solution=True,
                    auto_convert_tables=is_word_auto_convert_tables_enabled(),
                )

                self.after(0, self._on_direct_export_done, qs, save_path)
            except Exception as exc:
                _log.exception("Direct export error: %s", exc)
                self.after(0, self._on_direct_export_failed, str(exc))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_direct_export_done(self, questions: list, save_path: str):
        self._ai_busy = False
        self._ai_convert_btn.configure(state="normal")
        if hasattr(self, "_ai_direct_export_btn"):
            self._ai_direct_export_btn.configure(state="normal", text="🚀 Xuất Word trực tiếp (Auto TikZ)")
        self._show_parsed_questions_direct(questions)
        fname = Path(save_path).name
        self._ai_status_lbl.configure(text=f"✅ Đã chuẩn hóa, render TikZ & xuất Word: {fname}")
        try:
            os.startfile(save_path)
        except Exception:
            pass
        messagebox.showinfo(
            "Xuất Word thành công",
            f"Đã chuẩn hóa {len(questions)} câu hỏi, chuyển đổi hình ảnh TikZ\nvà xuất file Word thành công!\n\nĐường dẫn:\n{save_path}",
        )

    def _on_direct_export_failed(self, error_msg: str):
        self._ai_busy = False
        self._ai_convert_btn.configure(state="normal")
        if hasattr(self, "_ai_direct_export_btn"):
            self._ai_direct_export_btn.configure(state="normal", text="🚀 Xuất Word trực tiếp (Auto TikZ)")
        self._ai_status_lbl.configure(text=f"❌ Lỗi xuất Word: {error_msg[:60]}")
        messagebox.showerror("Lỗi xuất Word", error_msg)

    # ── AI Text: export Word (từ danh sách đã nhận diện) ────────────────

    def _ai_text_export_word(self):
        """Export parsed questions to Word or plain formatted text to Word."""
        save_path = filedialog.asksaveasfilename(
            title="Lưu file Word",
            defaultextension=".docx",
            initialfile="AI_convert.docx",
            filetypes=[("Word Document", "*.docx")],
        )
        if not save_path:
            return

        if self._ai_parsed_questions:
            try:
                from core.models import ExamData
                from export.word_exporter import export_to_word
                from services.tikz_vector_workflow import count_pending_blocks, convert_exam_tikz_to_emf, convert_exam_tikz_to_png
                from config import is_word_auto_convert_tables_enabled

                subj = self._subject_var.get() if hasattr(self, "_subject_var") and self._subject_var.get() else "Toán"
                grade = self._grade_var.get() if hasattr(self, "_grade_var") and self._grade_var.get() else "12"

                exam = ExamData(
                    exam_title=f"CÂU HỎI CHUYỂN ĐỔI - {subj.upper()} {grade}".strip(),
                    subject=subj, grade=grade,
                    semester="1", year="2025-2026", time="90",
                    questions=self._ai_parsed_questions,
                )

                if count_pending_blocks(exam) > 0:
                    try:
                        convert_exam_tikz_to_emf(exam)
                    except Exception:
                        try:
                            convert_exam_tikz_to_png(exam)
                        except Exception:
                            pass

                export_to_word(
                    exam,
                    save_path,
                    include_solution=True,
                    auto_convert_tables=is_word_auto_convert_tables_enabled(),
                )

                self._ai_status_lbl.configure(
                    text=f"✅ Đã xuất {len(self._ai_parsed_questions)} câu → Word")
                messagebox.showinfo("Thành công",
                    f"Đã xuất {len(self._ai_parsed_questions)} câu hỏi ra Word:\n{save_path}")
                os.startfile(save_path)
            except Exception as e:
                messagebox.showerror("Lỗi xuất Word", str(e))
        else:
            try:
                from docx import Document
                from docx.shared import Pt, Cm

                doc = Document()
                for section in doc.sections:
                    section.page_width = Cm(21.0)
                    section.page_height = Cm(29.7)
                    section.top_margin = Cm(2.0)
                    section.bottom_margin = Cm(2.0)
                    section.left_margin = Cm(2.0)
                    section.right_margin = Cm(2.0)

                style = doc.styles["Normal"]
                style.font.name = "Times New Roman"
                style.font.size = Pt(12)
                style.paragraph_format.line_spacing = 1.15
                style.paragraph_format.space_after = Pt(3)

                text = self._ai_output_text.get("1.0", "end-1c")
                lines = text.splitlines()
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    if not line:
                        i += 1
                        continue

                    # Thử nhận dạng bảng
                    if self._is_table_line(line):
                        table_lines = [line]
                        j = i + 1
                        while j < len(lines):
                            next_l = lines[j].strip()
                            if self._is_table_line(next_l) or self._is_separator_line(next_l):
                                table_lines.append(next_l)
                                j += 1
                            elif not next_l:
                                break
                            else:
                                break

                        if len(table_lines) >= 2:
                            first_row = self._parse_table_row(table_lines[0])
                            data = []
                            start_idx = 1
                            if len(table_lines) > 1 and self._is_separator_line(table_lines[1]):
                                start_idx = 2
                            for tl in table_lines[start_idx:]:
                                if self._is_separator_line(tl):
                                    continue
                                data.append(self._parse_table_row(tl))
                            if first_row:
                                self._add_word_table(doc, first_row, data)
                                i = j
                                continue

                        # Không dựng được bảng Word -> xuất dòng chứa "|" với ${...}$
                        doc.add_paragraph(normalize_math_to_braced_dollars(line))
                        i += 1
                    else:
                        doc.add_paragraph(normalize_math_to_braced_dollars(line))
                        i += 1

                doc.save(save_path)
                self._ai_status_lbl.configure(text="✅ Đã xuất văn bản → Word")
                messagebox.showinfo("Thành công",
                    f"Đã xuất văn bản ra Word:\n{save_path}")
                os.startfile(save_path)
            except Exception as e:
                messagebox.showerror("Lỗi xuất Word", str(e))

    def _ai_text_export_latex(self):
        """Export parsed questions as a complete ex_test LaTeX document."""
        if not self._ai_parsed_questions:
            messagebox.showinfo("Thông báo", "Chưa có câu hỏi để xuất LaTeX.")
            return
        save_path = filedialog.asksaveasfilename(
            title="Lưu file LaTeX",
            defaultextension=".tex",
            initialfile="AI_convert.tex",
            filetypes=[("LaTeX", "*.tex")],
        )
        if not save_path:
            return
        try:
            from export.latex_exporter import export_to_latex

            export_to_latex(
                self._ai_parsed_questions,
                save_path,
                include_solution=True,
            )
            self._ai_status_lbl.configure(
                text=f"✅ Đã xuất {len(self._ai_parsed_questions)} câu → LaTeX"
            )
            messagebox.showinfo(
                "Thành công",
                f"Đã xuất {len(self._ai_parsed_questions)} câu hỏi ra LaTeX:\n{save_path}",
            )
            os.startfile(save_path)
        except Exception as e:
            messagebox.showerror("Lỗi xuất LaTeX", str(e))

    # ── AI Text: upload to NHCH ──────────────────────────────────────────

    def _ai_text_upload_nhch(self):
        """Upload parsed questions to NHCH (Ngân hàng câu hỏi).

        Trước khi mở dialog xem trước, các câu chưa có structured ID (vẫn ở
        dạng QID-XXXXXXXX random — như khi paste từ ChatGPT/Gemini/etc và
        natural_parser tạo Question với UUID mặc định) được gán ID có cấu
        trúc theo format `[Grade][Subj][Chap][Level][Qtype]-[Seq]` (ví dụ
        `12D1N1-01`) — đồng bộ với flow tạo câu từ Prompt và AI generation.
        """
        if not self._ai_parsed_questions:
            messagebox.showinfo("Thông báo", "Chưa có câu hỏi để thêm vào NHCH.")
            return

        subj, grade = "Toán", "12"
        if self._get_subject_grade:
            subj, grade = self._get_subject_grade()

        # ── Gán structured ID cho câu chưa có (đồng bộ với prompt/AI flow) ──
        try:
            from core.models import assign_structured_ids
            need_id = [
                q for q in self._ai_parsed_questions
                if getattr(q, "question_id", "").startswith("QID-")
            ]
            if need_id:
                # Topic mặc định = subject để _detect_subject hoạt động đúng
                # khi natural_parser không trích được topic từ text gốc.
                for q in need_id:
                    if not q.topic:
                        q.topic = subj
                assign_structured_ids(need_id, grade)
        except Exception as e:
            _log.warning("assign_structured_ids failed (chatbot paste flow): %s", e)

        from ui.dialog_nhch_preview import NHCHPreviewDialog
        from storage.database import save_questions

        # Holder để closure đọc grade override TỪ dialog (user có thể đổi
        # Lớp ngay trên header dialog trước khi save).
        _holder: dict = {"dialog": None}

        def _do_save(questions):
            dlg = _holder.get("dialog")
            # Ưu tiên override từ dialog; fallback giá trị từ tab Cài đặt.
            final_subj = getattr(dlg, "final_subject", None) or subj
            final_grade = getattr(dlg, "final_grade", None) or grade
            try:
                n = save_questions(questions, final_subj, final_grade,
                                    source="AI Convert")
                self._ai_status_lbl.configure(
                    text=f"✅ Đã lưu {n} câu vào NHCH "
                         f"(Môn: {final_subj}, Lớp: {final_grade})")
                messagebox.showinfo(
                    "Thành công",
                    f"Đã lưu {n} câu hỏi vào ngân hàng câu hỏi!\n"
                    f"Môn: {final_subj}  •  Lớp: {final_grade}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu vào NHCH:\n{e}")

        _holder["dialog"] = NHCHPreviewDialog(
            self.winfo_toplevel(),
            self._ai_parsed_questions,
            subj, grade,
            on_confirm=_do_save,
        )

    # ── AI Text: copy ────────────────────────────────────────────────────

    def _ai_text_copy_result(self):
        text = self._ai_output_text.get("1.0", "end-1c")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._ai_copy_btn.configure(text="✅ Đã copy!")
            self.after(2000, lambda: self._ai_copy_btn.configure(text="📋 Copy"))

    def _ai_text_copy_latex(self):
        if not self._ai_parsed_questions:
            return
        from export.latex_exporter import format_questions_ex_test

        source = format_questions_ex_test(
            self._ai_parsed_questions,
            include_solution=True,
        )
        self.clipboard_clear()
        self.clipboard_append(source)
        self._ai_copy_latex_btn.configure(text="✅ Đã copy LaTeX!")
        self.after(
            2000,
            lambda: self._ai_copy_latex_btn.configure(text="📋 Copy LaTeX"),
        )

    # ──────────────────────────────────────────────────────────────────────
    #  MODE SWITCH
    # ──────────────────────────────────────────────────────────────────────

    def _select_mode(self, mode: str):
        self._mode_var.set(mode)
        self._on_mode_change()

    def _on_mode_change(self):
        mode = self._mode_var.get()

        # Update tab button styles
        for val, btn in self._mode_buttons:
            if val == mode:
                btn.configure(bg=PRIMARY, fg="white",
                              activebackground=C["primary_xl"], activeforeground="white")
            else:
                btn.configure(bg=C["surface_2"], fg=C["text_muted"],
                              activebackground=C["surface_3"], activeforeground=TEXT)

        self._img_frame.grid_forget()
        self._pdf_frame.grid_forget()
        self._ai_text_frame.grid_forget()
        if mode == "image":
            self._img_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        elif mode == "pdf":
            self._pdf_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        elif mode == "ai_text":
            self._ai_text_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
            self._ensure_ai_question_table_height()

    # ──────────────────────────────────────────────────────────────────────
    #  IMAGE INPUT
    # ──────────────────────────────────────────────────────────────────────

    def _upload_image(self):
        """[SPEED-6] Mở dialog → cho chọn NHIỀU file ảnh cùng lúc."""
        paths = filedialog.askopenfilenames(
            title="Chọn ảnh (có thể chọn nhiều — Ctrl/Shift + click)",
            filetypes=[
                ("Ảnh", "*.png *.jpg *.jpeg *.bmp *.webp"),
                ("Tất cả", "*.*"),
            ],
        )
        if not paths:
            return
        try:
            from services.image_precheck import analyze_many_images, format_image_quality_warnings

            warning = format_image_quality_warnings(analyze_many_images(paths))
            if warning:
                messagebox.showwarning("Cảnh báo OCR", warning)
        except Exception as e:
            _log.debug("Image precheck skipped: %s", e)
        added = 0
        errors: list[str] = []
        for path in paths:
            try:
                with open(path, "rb") as f:
                    data = f.read()
                ext = path.rsplit(".", 1)[-1].lower()
                ext = "jpeg" if ext in ("jpg", "jpeg") else "png"
                name = path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
                self._add_image_to_batch(data, ext, name)
                added += 1
            except Exception as e:
                errors.append(f"{path.rsplit('/', 1)[-1]}: {e}")
        if added:
            self._status_lbl.configure(
                text=f"📥 Đã thêm {added} ảnh — tổng {len(self._image_batch)} ảnh")
        if errors:
            messagebox.showwarning(
                "Một số ảnh không đọc được",
                f"Bỏ qua {len(errors)} ảnh:\n" + "\n".join(errors[:5]),
            )

    def _paste_image(self):
        """Paste image from clipboard — APPEND vào batch."""
        try:
            from PIL import ImageGrab
            img = ImageGrab.grabclipboard()
            if img is None:
                messagebox.showinfo("Thông báo",
                    "Clipboard không có ảnh.\nHãy copy ảnh trước (Ctrl+C).")
                return
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            name = f"clipboard_{len(self._image_batch) + 1}.png"
            try:
                from services.image_precheck import analyze_image_quality, format_image_quality_warnings

                warning = format_image_quality_warnings([
                    analyze_image_quality(img, name=name)
                ])
                if warning:
                    messagebox.showwarning("Cảnh báo OCR", warning)
            except Exception as e:
                _log.debug("Clipboard image precheck skipped: %s", e)
            self._add_image_to_batch(buf.getvalue(), "png", name)
            self._status_lbl.configure(
                text=f"📋 Đã dán — tổng {len(self._image_batch)} ảnh")
        except ImportError:
            messagebox.showerror("Lỗi", "Cần cài Pillow:\npip install Pillow")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể dán ảnh:\n{e}")

    def _add_image_to_batch(self, data: bytes, ext: str, name: str) -> None:
        """Thêm 1 ảnh vào batch + render thumbnail."""
        # Tạo thumbnail PhotoImage
        thumb_photo = None
        try:
            from PIL import Image, ImageTk
            img = Image.open(io.BytesIO(data))
            # Thumbnail vuông ~96px
            max_dim = 96
            w, h = img.size
            ratio = min(max_dim / w, max_dim / h, 1.0)
            new_w, new_h = max(1, int(w * ratio)), max(1, int(h * ratio))
            img_thumb = img.resize((new_w, new_h), Image.LANCZOS)
            thumb_photo = ImageTk.PhotoImage(img_thumb)
        except Exception as e:
            _log.debug("Thumbnail gen failed for %s: %s", name, e)

        item = {
            "data":  data,
            "ext":   ext,
            "name":  name,
            "thumb": thumb_photo,  # giữ reference, tránh GC
        }
        self._image_batch.append(item)
        # Backward compat: trỏ _image_data tới ảnh đầu tiên
        if self._image_batch:
            self._image_data = self._image_batch[0]["data"]
            self._image_ext  = self._image_batch[0]["ext"]
        self._refresh_thumb_grid()
        self._update_convert_btn_state()

    def _refresh_thumb_grid(self) -> None:
        """Render lại grid thumbnail từ self._image_batch."""
        # Clear old thumbnails
        for w in self._thumb_grid.winfo_children():
            w.destroy()

        if not self._image_batch:
            # Empty → show drop_label only
            try:
                self._thumb_scroll.pack_forget()
                self._thumb_vsb.pack_forget()
            except Exception:
                pass
            self._drop_label.pack(expand=True)
            return

        # Hide drop_label, show scroll
        self._drop_label.pack_forget()
        self._thumb_scroll.pack(side="left", fill="both", expand=True,
                                 padx=8, pady=8)
        self._thumb_vsb.pack(side="right", fill="y")

        # Grid: 4 thumbnail per row
        COLS = 4
        for idx, item in enumerate(self._image_batch):
            self._build_thumb_cell(idx, item, row=idx // COLS, col=idx % COLS)

        # Grid columns expand evenly
        for c in range(COLS):
            self._thumb_grid.grid_columnconfigure(c, weight=1, uniform="thumb")

    def _build_thumb_cell(self, idx: int, item: dict, row: int, col: int):
        """1 thumbnail cell: ảnh + nút X xoá + index."""
        cell = tk.Frame(self._thumb_grid, bg="#FFFFFF",
                        highlightbackground=C["primary_light"],
                        highlightthickness=1)
        cell.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")

        # Top bar: index + close button
        topbar = tk.Frame(cell, bg=C["primary_light"])
        topbar.pack(fill="x")

        tk.Label(topbar, text=f"#{idx + 1}",
                 bg=C["primary_light"], fg="white",
                 font=(FONT["app"], FONT["size_sm"], "bold"),
                 padx=4).pack(side="left")

        close_btn = tk.Label(topbar, text="✕",
                              bg=C["primary_light"], fg="white",
                              font=(FONT["app"], FONT["size_sm"], "bold"),
                              padx=4, cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>",
                       lambda _e, i=idx: self._remove_image_at(i))

        # Thumbnail
        thumb_lbl = tk.Label(cell, bg="#FFFFFF", padx=4, pady=4)
        if item.get("thumb") is not None:
            thumb_lbl.configure(image=item["thumb"])
        else:
            thumb_lbl.configure(text="📷", font=(FONT["app"], 32))
        thumb_lbl.pack()

        # Filename (truncated)
        name = item.get("name", "")
        if len(name) > 18:
            name = name[:15] + "…"
        tk.Label(cell, text=name,
                 bg="#FFFFFF", fg=C["text_muted"],
                 font=(FONT["app"], FONT["size_sm"])
                 ).pack(pady=(0, 4))

    def _remove_image_at(self, idx: int) -> None:
        """Xoá 1 ảnh khỏi batch theo index."""
        if 0 <= idx < len(self._image_batch):
            self._image_batch.pop(idx)
            if self._image_batch:
                self._image_data = self._image_batch[0]["data"]
                self._image_ext  = self._image_batch[0]["ext"]
            else:
                self._image_data = None
            self._refresh_thumb_grid()
            self._update_convert_btn_state()
            self._status_lbl.configure(
                text=f"🗑️ Đã xoá — còn {len(self._image_batch)} ảnh"
                if self._image_batch else "")

    def _update_convert_btn_state(self) -> None:
        """Enable/disable Convert + Clear buttons theo batch size."""
        has_any = bool(self._image_batch)
        self._convert_btn.configure(state="normal" if has_any else "disabled")
        self._clear_btn.configure(state="normal" if has_any else "disabled")

    def _set_image(self, data: bytes, ext: str):
        """LEGACY: Set single image. Wraps _add_image_to_batch (clear + add 1)."""
        # Compatibility: behaviour cũ là replace toàn bộ
        self._image_batch.clear()
        self._add_image_to_batch(data, ext, name="image.png")

    def _clear_image(self):
        """Clear toàn bộ batch."""
        self._image_batch.clear()
        self._image_data = None
        self._refresh_thumb_grid()
        self._update_convert_btn_state()
        self._status_lbl.configure(text="")
        # Đặt drop_label về default text
        self._drop_label.configure(
            text=("📋  Dán ảnh đề (Ctrl+V)\n"
                  "hoặc nhấn để chọn FILE (có thể chọn nhiều)\n\n"
                  "💡 App xử lý tất cả ảnh thành 1 đề Word"),
            fg=C["text_body"])

    # ──────────────────────────────────────────────────────────────────────
    #  CONVERT — pipeline 4 bước
    # ──────────────────────────────────────────────────────────────────────

    def _start_img_timer(self):
        """Bắt đầu đếm thời gian cho Image convert."""
        self._stop_img_timer()
        import time as _time
        self._img_start_time = _time.time()
        self._img_timer_var.set("⏱️ 00:00")
        self._tick_img_timer()

    def _tick_img_timer(self):
        """Tick đếm giờ mỗi giây."""
        if not self._busy:
            return
        import time as _time
        elapsed = int(_time.time() - self._img_start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        self._img_timer_var.set(f"⏱️ {mins:02d}:{secs:02d}")
        self._img_timer_id = self.after(1000, self._tick_img_timer)

    def _stop_img_timer(self):
        """Dừng đồng hồ bấm giờ."""
        if self._img_timer_id:
            try:
                self.after_cancel(self._img_timer_id)
            except Exception:
                pass
            self._img_timer_id = None

    def _img_open_folder(self):
        """Mở thư mục chứa file Word vừa xuất từ ảnh."""
        if self._img_last_exported_path and os.path.exists(self._img_last_exported_path):
            folder = os.path.dirname(os.path.abspath(self._img_last_exported_path))
            if os.path.isdir(folder):
                try:
                    os.startfile(folder)
                except Exception as e:
                    messagebox.showerror("Lỗi mở thư mục", str(e))

    def _start_convert(self):
        """[SPEED-6] Kick off batch convert — process tất cả ảnh trong batch."""
        if self._busy or not self._image_batch:
            return
        if self._get_ai_call is None:
            messagebox.showerror("Lỗi", "Chưa cấu hình AI. Kiểm tra tab Cài đặt.")
            return

        self._busy = True
        self._start_img_timer()
        n_img = len(self._image_batch)
        self._convert_btn.configure(
            state="disabled",
            text=f"⏳ Đang xử lý {n_img} ảnh…")
        self._img_export_btn.configure(state="disabled")
        self._img_folder_btn.configure(state="disabled")
        self._img_nhch_btn.configure(state="disabled")
        self._copy_btn.configure(state="disabled")
        self._img_pb["value"] = 0
        self._img_stage_var.set("Bắt đầu…")
        self._status_lbl.configure(text="")

        # Reset state
        self._img_questions = []
        self._img_raw_struct = ""
        for item in self._q_tree.get_children():
            self._q_tree.delete(item)
        self._img_count_lbl.configure(text="")
        self._output_text.configure(state="normal")
        self._output_text.delete("1.0", "end")
        self._output_text.configure(state="disabled")

        skip_solve = self._img_skip_solve.get()
        do_tikz    = self._img_do_tikz.get()
        qtype_filter = self._img_qtype.get() or "auto"
        # Snapshot batch (copy) — user thêm/xoá ảnh trong khi đang convert
        # cũng không ảnh hưởng tới task hiện tại.
        batch_snapshot = list(self._image_batch)
        threading.Thread(
            target=self._do_full_convert,
            args=(batch_snapshot, skip_solve, do_tikz, qtype_filter),
            daemon=True,
        ).start()

    def _on_qtype_changed(self, event=None):
        """Callback khi user chọn loại câu từ combobox — sync display ↔ code."""
        display = self._img_qtype_display.get()
        code = self._qtype_display_to_code.get(display, "auto")
        self._img_qtype.set(code)

    def _img_update_stage(self, text: str, pct: int):
        """Cập nhật progress bar + stage label (gọi qua self.after)."""
        try:
            self._img_pb["value"] = max(0, min(100, pct))
            self._img_stage_var.set(text)
        except tk.TclError:
            # Widget đã destroy (user đóng tab) — bỏ qua
            pass

    def _do_full_convert(self, batch: list, skip_solve: bool, do_tikz: bool,
                          qtype_filter: str = "auto"):
        """[SPEED-6] Worker thread: pipeline 4 bước cho BATCH ảnh.

        Stage 1 (Vision OCR) chạy tuần tự cho TỪNG ảnh — kết quả questions
        từ tất cả ảnh được gộp lại. Stages 2-4 chạy trên list gộp (giải +
        verify + TikZ cho tất cả các câu cùng lúc).

        Parameters
        ----------
        batch: list[dict] với mỗi item {data, ext, name, thumb} — snapshot
               tại thời điểm user nhấn Convert.
        qtype_filter: "auto" → AI tự nhận diện; "TN"/"DS"/"TLN"/"TL" → ép
                      tất cả câu về loại đó.
        """
        try:
            # ── Stage 1: Vision OCR cho từng ảnh ─────────────────────────
            n_img = len(batch)
            all_questions = []
            raw_per_image: list[str] = []  # giữ lại raw response cho debug
            # [SMART-1] Aggregate META từ tất cả ảnh — majority-vote
            meta_votes: dict = {"subject": [], "grade": [], "topic": []}

            for img_idx, img_item in enumerate(batch):
                pct_stage1 = int(20 * ((img_idx + 1) / n_img))
                stage1_label = (
                    f"🔍 Bước 1/4: Vision OCR ảnh {img_idx + 1}/{n_img}"
                )
                if qtype_filter != "auto":
                    stage1_label += f" (ép loại: {qtype_filter})"
                stage1_label += "…"
                self.after(0, self._img_update_stage, stage1_label, pct_stage1)

                # Vision call cho ảnh hiện tại — tạm gán _image_data để
                # _call_vision_api dùng đúng ảnh
                self._image_data = img_item["data"]
                self._image_ext  = img_item["ext"]

                vision_prompt = _build_vision_prompt(qtype_filter)
                try:
                    struct_text = self._call_vision_api(vision_prompt) or ""
                except Exception as e:
                    _log.exception("Vision call failed for image %d", img_idx + 1)
                    self.after(0, self._on_convert_failed,
                               f"Lỗi gọi Vision cho ảnh {img_idx + 1}/{n_img}:\n{e}")
                    return
                raw_per_image.append(struct_text)
                _log.info("Image %d/%d: Vision returned %d chars",
                          img_idx + 1, n_img, len(struct_text))

                # [SMART-1] Extract META metadata
                meta = self._parse_meta_line(struct_text)
                if meta:
                    for k, v in meta.items():
                        if v:
                            meta_votes[k].append(v)

                # Parse blocks → Question[]
                imgs_qs = self._parse_vision_response(
                    struct_text, qtype_filter)
                _log.info("Image %d: parsed %d questions",
                          img_idx + 1, len(imgs_qs))
                all_questions.extend(imgs_qs)

            # Gộp raw text từ tất cả ảnh cho output preview / debug
            self._img_raw_struct = "\n\n=== ẢNH MỚI ===\n\n".join(raw_per_image)

            questions = all_questions

            if not questions:
                # Vẫn không có gì → show raw AI response cho user debug
                preview = (self._img_raw_struct
                           or "(AI không trả lời)")[:1500]
                self.after(0, self._on_convert_failed,
                           f"Không nhận diện được câu hỏi nào trong "
                           f"{n_img} ảnh.\n\n"
                           "Có thể nguyên nhân:\n"
                           "  • Ảnh quá mờ / chứa nét tay khó đọc.\n"
                           "  • AI Vision trả về không đúng format chuẩn.\n"
                           "  • Ảnh không chứa câu hỏi.\n\n"
                           f"AI trả về (rút gọn):\n{preview}")
                self.after(0, self._show_raw_response, self._img_raw_struct)
                return

            # qtype filter + ép loại đã handle trong _parse_vision_response
            # → questions list giờ đã consistent.

            n = len(questions)
            self.after(0, self._img_update_stage,
                       f"✓ Nhận diện {n} câu từ {n_img} ảnh — chuẩn bị xử lý tiếp…",
                       22)

            # ── Stage 2: AI solve (optional) ─────────────────────────────
            if not skip_solve:
                for i, q in enumerate(questions):
                    pct = 20 + int(35 * ((i + 1) / n))
                    self.after(0, self._img_update_stage,
                               f"💡 Bước 2/4: Giải câu {i+1}/{n}…", pct)
                    try:
                        self._solve_question(q)
                    except Exception as e:
                        _log.warning("Solve câu %d failed: %s", i + 1, e)

                # ── Stage 3: AI verify (optional) ────────────────────────
                for i, q in enumerate(questions):
                    pct = 55 + int(20 * ((i + 1) / n))
                    self.after(0, self._img_update_stage,
                               f"✔️ Bước 3/4: Kiểm tra đáp án câu {i+1}/{n}…", pct)
                    try:
                        self._verify_question(q)
                    except Exception as e:
                        _log.warning("Verify câu %d failed: %s", i + 1, e)
            else:
                self.after(0, self._img_update_stage,
                           "⏭ Bỏ qua giải — chỉ chuẩn hoá cấu trúc.", 75)

            # ── Stage 4: TikZ (optional) ─────────────────────────────────
            if do_tikz:
                # Sinh TikZ cho mỗi câu có [HÌNH: ...]
                for i, q in enumerate(questions):
                    if not self._has_figure_marker(q):
                        continue
                    pct = 75 + int(20 * ((i + 1) / n))
                    self.after(0, self._img_update_stage,
                               f"🎨 Bước 4/4: Vẽ hình câu {i+1}/{n}…", pct)
                    try:
                        self._generate_tikz_for_question(q)
                    except Exception as e:
                        _log.warning("TikZ câu %d failed: %s", i + 1, e)

                # Chuyển TikZ → EMF vector, giữ PNG preview trong slot ảnh.
                self.after(0, self._img_update_stage,
                           "📐 Đang chuyển TikZ → EMF + PNG preview…", 95)
                self._apply_tikz_pipeline(questions)

            # [SMART-1] Majority vote cho META — chọn giá trị xuất hiện nhiều nhất
            from collections import Counter
            detected_meta = {}
            for k, votes in meta_votes.items():
                if votes:
                    # Counter.most_common(1)[0] = (value, count)
                    detected_meta[k] = Counter(votes).most_common(1)[0][0]

            self.after(0, self._img_update_stage, "✅ Hoàn tất!", 100)
            self.after(0, self._on_convert_done, questions,
                       self._img_raw_struct, None, detected_meta)
        except Exception as e:
            _log.exception("Convert pipeline error")
            self.after(0, self._on_convert_failed, str(e))

    @staticmethod
    def _parse_meta_line(struct_text: str) -> dict:
        """[SMART-1] Extract META: {...} line từ vision response.

        Trả dict {"subject": ..., "grade": ..., "topic": ...} hoặc {} nếu
        không tìm thấy / JSON invalid. KHÔNG raise.
        """
        if not struct_text:
            return {}
        # Match dòng "META: {...}" (case-insensitive, single line)
        m = re.search(
            r"^\s*META\s*:\s*(\{[^\n}]*\})",
            struct_text, re.MULTILINE | re.IGNORECASE,
        )
        if not m:
            return {}

        raw_json = m.group(1)
        try:
            import json
            data = json.loads(raw_json)
            if not isinstance(data, dict):
                return {}
            # Normalize keys
            return {
                "subject": str(data.get("subject", "")).strip(),
                "grade":   str(data.get("grade", "")).strip(),
                "topic":   str(data.get("topic", "")).strip(),
            }
        except Exception as e:
            _log.debug("Failed to parse META JSON: %s (raw=%s)", e, raw_json[:80])
            return {}

    def _parse_vision_response(self, struct_text: str,
                                qtype_filter: str = "auto") -> list:
        """Parse raw Vision response → list[Question] với 3-level fallback.

        Extracted từ inline logic của _do_full_convert để hỗ trợ batch.
        Mỗi ảnh trong batch gọi method này riêng → results gộp ở caller.

        Steps:
          1. Tìm ===CAU===/===KETCAU=== blocks → parse_one_question.
          2. Nếu rỗng → natural_parser (đề chuẩn "Câu N: …").
          3. Nếu rỗng → best-effort wrap raw text thành 1 câu đơn.
          4. Ép qtype nếu qtype_filter != "auto".
        """
        from core.parser import parse_one_question

        # ── 1. Block-level parse ──
        blocks = re.findall(r"===CAU===(.*?)===KETCAU===",
                            struct_text or "", re.DOTALL | re.IGNORECASE)
        questions = []
        for block in blocks:
            full_block = f"===CAU===\n{block}\n===KETCAU==="
            q = parse_one_question(full_block)
            if q:
                questions.append(q)

        # ── 2. Natural parser fallback ──
        if not questions:
            try:
                from core.natural_parser import parse_natural_questions
                questions = parse_natural_questions(struct_text or "") or []
                if questions:
                    _log.info("Natural parser recovered %d câu", len(questions))
            except Exception as e:
                _log.warning("natural_parser fallback failed: %s", e)

        # ── 3. Best-effort wrap ──
        if not questions:
            cleaned = self._best_effort_strip(struct_text or "")
            if len(cleaned) >= 30:
                _log.warning(
                    "Both parsers failed. Best-effort: wrap raw text "
                    "as single %s question (%d chars).",
                    qtype_filter, len(cleaned))
                from core.models import Question
                fallback_q = Question(
                    qtype=qtype_filter if qtype_filter != "auto" else "TLN",
                    level="TH",
                    topic="",
                    question=cleaned,
                )
                questions = [fallback_q]

        # ── 4. Ép qtype nếu user chọn loại cụ thể ──
        if qtype_filter != "auto":
            for q in questions:
                if q.qtype != qtype_filter:
                    _log.info(
                        "Ép loại: '%s...' từ %s → %s",
                        (q.question or "")[:40], q.qtype, qtype_filter)
                    q.qtype = qtype_filter
                    # Dọn các field không phù hợp với loại mới
                    if qtype_filter != "TN":
                        q.options = {}
                        if qtype_filter != "TLN":
                            q.answer = ""
                    if qtype_filter != "DS":
                        q.items = {}
                        q.answers = {}
                        q.item_solutions = {}

        return questions

    # ── Stage 2 helper: gọi AI giải 1 câu ─────────────────────────────────

    def _solve_question(self, q):
        """Gọi AI text để fill DAPAN + LOIGIAI cho 1 câu.

        Nếu lần đầu AI không trả đáp án (parser không bắt được), retry 1 lần
        với prompt nhấn mạnh format. Giúp robust với các AI hay "quên" prefix
        DAPAN:/LOIGIAI:.
        """
        # Nếu câu đã có cả DAPAN và LOIGIAI từ ảnh → skip
        if q.solution.strip() and self._has_answer(q):
            return

        cau_block = self._question_to_cau_block(q)
        ai_gen = self._get_ai_call()
        prompt = _SOLVE_PROMPT.format(cau_block=cau_block)
        result = (ai_gen(prompt) or "").strip()
        if not result:
            _log.warning("Solve: AI trả empty cho câu '%s...'",
                         (q.question or "")[:40])
            return

        self._apply_solve_result(q, result)

        # ── Retry nếu vẫn không có đáp án sau parse ─────────────────────
        if not self._has_answer(q):
            _log.info("Solve: parser không bắt được đáp án, retry với "
                      "prompt đơn giản hơn")
            retry_prompt = (
                f"Giải câu Toán sau. Chỉ trả 2 dòng — KHÔNG thêm gì khác:\n"
                f"DAPAN: <đáp án>\n"
                f"LOIGIAI: <lời giải ngắn>\n\n"
                f"CÂU HỎI:\n{q.question}\n\n"
                f"LOẠI CÂU: {q.qtype}\n"
            )
            if q.qtype == "TN":
                retry_prompt += (
                    "ĐÁP ÁN: 1 ký tự A/B/C/D.\n"
                    f"Các phương án:\n"
                    f"A. {q.options.get('A', '')}\n"
                    f"B. {q.options.get('B', '')}\n"
                    f"C. {q.options.get('C', '')}\n"
                    f"D. {q.options.get('D', '')}\n"
                )
            elif q.qtype == "TLN":
                retry_prompt += (
                    "ĐÁP ÁN: 1 SỐ tối đa 4 ký tự, dấu phẩy thập phân VN "
                    "(vd: 0,5 hoặc 12 hoặc -1,25).\n"
                )
            elif q.qtype == "DS":
                retry_prompt += (
                    "ĐÁP ÁN: dạng a=Đ,b=S,c=Đ,d=S — đúng đủ 4 ý.\n"
                )

            try:
                result2 = (ai_gen(retry_prompt) or "").strip()
                if result2:
                    self._apply_solve_result(q, result2)
            except Exception as e:
                _log.warning("Solve retry failed: %s", e)

    def _verify_question(self, q):
        """Gọi AI text để kiểm tra đáp án + lời giải hiện tại có đúng không."""
        if not self._has_answer(q):
            return  # không có đáp án để verify

        cau_block = self._question_to_cau_block(q)
        dapan_str = self._format_dapan(q)
        ai_gen = self._get_ai_call()
        prompt = _VERIFY_PROMPT.format(
            cau_block=cau_block,
            dapan=dapan_str,
            loigiai=q.solution or "(không có)",
        )
        result = (ai_gen(prompt) or "").strip()
        first_line = result.splitlines()[0].strip().upper() if result else ""
        if first_line.startswith("OK"):
            q._review = {"ok": True, "raw": result}
            return

        # SAI → parse đáp án đúng + lời giải sửa
        q._review = {"ok": False, "raw": result}
        m_dapan = re.search(r"DAPAN_DUNG\s*:\s*(.+?)(?=\||$)", result, re.IGNORECASE)
        m_solve = re.search(r"LOIGIAI_SUA\s*:\s*(.+)$", result,
                            re.IGNORECASE | re.DOTALL)
        if m_dapan:
            self._apply_dapan_string(q, m_dapan.group(1).strip())
        if m_solve:
            q.solution = m_solve.group(1).strip()

    def _generate_tikz_for_question(self, q):
        """Tìm [HÌNH: …] trong NOIDUNG, gọi AI sinh TikZ thay thế."""
        pattern = re.compile(r"\[H[ÌI]NH\s*(?:\d+)?\s*:?\s*([^\]]*)\]",
                             re.IGNORECASE)
        text = q.question or ""
        match = pattern.search(text)
        if not match:
            return

        desc = (match.group(1) or "").strip() or text[:300]
        ai_gen = self._get_ai_call()
        prompt = _TIKZ_FROM_DESC_PROMPT.format(
            description=desc, question=text)
        result = ai_gen(prompt) or ""

        # Strip markdown fence nếu AI vô tình thêm
        result = re.sub(r"^```\w*\s*", "", result.strip())
        result = re.sub(r"\s*```$", "", result)

        tm = re.search(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
                       result, re.DOTALL)
        if not tm:
            return  # AI không trả TikZ hợp lệ — giữ marker để user thấy

        tikz_block = tm.group(0)
        # Thay marker bằng khối tikzpicture (tikz_pipeline sẽ strip & render)
        q.question = text[:match.start()] + "\n" + tikz_block + "\n" + text[match.end():]

    def _apply_tikz_pipeline(self, questions: list):
        """Chạy workflow vector dùng chung → EMF cho Word + PNG preview."""
        try:
            from core.models import ExamData
            from services.tikz_vector_workflow import convert_exam_tikz_to_emf
            exam = ExamData(
                exam_title="", subject="", grade="",
                semester="", year="", time="",
                questions=questions,
            )
            convert_exam_tikz_to_emf(exam)
        except Exception as e:
            _log.warning("tikz_pipeline error: %s", e, exc_info=True)

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _has_figure_marker(q) -> bool:
        """True nếu câu có [HÌNH: …] hoặc khối tikzpicture trong NOIDUNG."""
        text = (q.question or "")
        if "[HÌNH" in text.upper() or "[HINH" in text.upper():
            return True
        if "\\begin{tikzpicture}" in text:
            return True
        return False

    @staticmethod
    def _has_answer(q) -> bool:
        """True nếu câu đã có đáp án (DAPAN khác rỗng)."""
        if q.qtype == "TN":
            return bool(q.answer.strip())
        if q.qtype == "DS":
            return bool(q.answers)
        if q.qtype == "TLN":
            return bool(q.answer.strip())
        # TL: luôn coi là "có đáp án = xem lời giải"
        return bool(q.solution.strip())

    @staticmethod
    def _format_dapan(q) -> str:
        """Format DAPAN dạng chuỗi để verify/hiển thị."""
        if q.qtype == "TN":
            return q.answer or "?"
        if q.qtype == "DS":
            if not q.answers:
                return "?"
            return ",".join(f"{k}={'Đ' if v else 'S'}"
                            for k, v in q.answers.items())
        if q.qtype == "TLN":
            return q.answer or "?"
        return "xem lời giải"

    @staticmethod
    def _question_to_cau_block(q) -> str:
        """Serialize Question về dạng ===CAU===...===KETCAU=== cho prompt."""
        lines = [
            "===CAU===",
            f"LOAI: {q.qtype}",
        ]
        if q.level:
            lines.append(f"MUCDO: {q.level}")
        if q.topic:
            lines.append(f"CHUONG: {q.topic}")
        lines.append(f"NOIDUNG: {q.question or ''}")
        if q.qtype == "TN":
            for k in "ABCD":
                lines.append(f"{k}: {q.options.get(k, '')}")
        elif q.qtype == "DS":
            for k in "abcd":
                lines.append(f"{k}: {q.items.get(k, '')}")
        lines.append("===KETCAU===")
        return "\n".join(lines)

    def _apply_solve_result(self, q, result: str):
        """Parse output AI solve → fill DAPAN + LOIGIAI vào q.

        Chấp nhận nhiều biến thể format từ AI:
          • "DAPAN: X" / "DAPAN:X"
          • "Đáp án: X" / "Đáp số: X"
          • "Answer: X"
          • "LOIGIAI: …" / "Lời giải: …" / "Giải: …"
        Đồng thời nếu AI không dùng prefix → fallback heuristic.
        """
        if not result:
            return

        # ── Đáp án: thử nhiều regex ────────────────────────────────────
        ans_patterns = [
            r"^\s*DAPAN\s*[:.]?\s*(.+?)\s*$",
            r"^\s*Đáp\s*án\s*[:.]?\s*(.+?)\s*$",
            r"^\s*Đáp\s*số\s*[:.]?\s*(.+?)\s*$",
            r"^\s*ĐA\s*[:.]?\s*(.+?)\s*$",
            r"^\s*Answer\s*[:.]?\s*(.+?)\s*$",
        ]
        ans_found = None
        for pat in ans_patterns:
            m = re.search(pat, result, re.IGNORECASE | re.MULTILINE)
            if m:
                ans_found = m.group(1).strip()
                # Cắt mọi text sau xuống dòng đầu (đề phòng AI dán cả lời giải)
                ans_found = ans_found.split("\n", 1)[0].strip()
                if ans_found:
                    break

        if ans_found:
            self._apply_dapan_string(q, ans_found)

        # ── Lời giải: thử nhiều regex ──────────────────────────────────
        sol_patterns = [
            r"^\s*LOIGIAI\s*[:.]?\s*(.*)$",
            r"^\s*Lời\s*giải\s*[:.]?\s*(.*)$",
            r"^\s*Giải\s*[:.]?\s*(.*)$",
            r"^\s*Hướng\s*dẫn(?:\s*giải)?\s*[:.]?\s*(.*)$",
            r"^\s*Solution\s*[:.]?\s*(.*)$",
        ]
        sol_found = None
        for pat in sol_patterns:
            m = re.search(pat, result, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if m:
                sol_found = m.group(1).strip()
                # Cắt trước dòng "DAPAN:" / "Đáp án:" nếu AI dán ngược thứ tự
                sol_found = re.split(
                    r"(?im)^(?:DAPAN|Đáp\s*án|Đáp\s*số)\s*:",
                    sol_found)[0].strip()
                if sol_found:
                    break

        if sol_found:
            q.solution = sol_found

        # ── Fallback: nếu AI không có prefix nào → toàn bộ là lời giải ──
        if not ans_found and not sol_found:
            cleaned = result.strip()
            # Bỏ markdown fence nếu có
            cleaned = re.sub(r"^```\w*\s*", "", cleaned)
            cleaned = re.sub(r"\s*```\s*$", "", cleaned)
            if cleaned and len(cleaned) > 10:
                q.solution = cleaned
                _log.info(
                    "Solve fallback: AI không có prefix, lưu toàn text "
                    "làm lời giải (%d chars)", len(cleaned))

    @staticmethod
    def _apply_dapan_string(q, dapan: str):
        """Gán DAPAN string vào Question theo đúng loại câu.

        - TN  : extract 1 ký tự A/B/C/D đầu tiên.
        - DS  : parse "a=Đ,b=S…" hoặc "a:Đ b:S".
        - TLN : extract số (giữ dấu phẩy thập phân VN), strip ký tự lạ.
        - TL  : giữ nguyên hoặc "xem lời giải" nếu rỗng.
        """
        dapan = (dapan or "").strip()
        if not dapan:
            return

        if q.qtype == "TN":
            up = dapan.upper()
            for c in up:
                if c in "ABCD":
                    q.answer = c
                    return

        elif q.qtype == "DS":
            answers = {}
            # Format chuẩn "a=Đ,b=S,c=Đ,d=S" hoặc "a:Đ b:S"
            for m in re.finditer(
                r"([a-d])\s*[=:\-]\s*(Đ|S|Đúng|Sai|T|F|True|False)",
                dapan, re.IGNORECASE,
            ):
                k = m.group(1).lower()
                v = m.group(2).upper()
                answers[k] = v in ("D", "Đ", "T", "TRUE", "ĐÚNG")
            if answers:
                q.answers = answers

        elif q.qtype == "TLN":
            # Trích số từ chuỗi — chấp nhận dạng "1,5", "1.5", "−1,5", "12"
            # Giữ dấu phẩy VN (chuyển dấu chấm thành phẩy nếu có)
            cleaned = dapan.strip()
            # Bỏ ký tự `${...}$` LaTeX bao quanh
            cleaned = re.sub(r"^\$+\{?|\}?\$+$", "", cleaned).strip()
            # Bỏ "frac{a}{b}" và các lệnh LaTeX cơ bản — chỉ giữ số/dấu
            # Nếu AI trả về "${0,5}$" → "0,5". Nếu trả về "0.5" → "0,5".
            num_match = re.search(
                r"[-−]?\d+(?:[.,]\d+)?",
                cleaned,
            )
            if num_match:
                num = num_match.group(0).replace(".", ",").replace("−", "-")
                # Cắt tối đa 4 ký tự đáp số (theo spec TLN)
                q.answer = num[:4]
            else:
                # Không tìm thấy số → giữ nguyên text gốc (max 4 ký tự)
                q.answer = cleaned[:4]

        else:  # TL
            q.answer = dapan or "xem lời giải"

    def _call_vision_api(self, prompt: str) -> str:
        """Call AI Vision API with image."""
        ai_gen = self._get_ai_call()  # returns service.generate

        # Encode image to base64
        b64 = base64.b64encode(self._image_data).decode("utf-8")
        mime = f"image/{self._image_ext}"

        # Try provider-specific vision calls
        # The ai_gen is bound method, we can inspect the service
        service = ai_gen.__self__

        if hasattr(service, '_keys') and hasattr(service, '_model'):
            provider = service.provider_name

            if provider == "Google Gemini":
                return self._call_gemini_vision(service, prompt, b64, mime)
            elif provider == "Anthropic Claude":
                return self._call_claude_vision(service, prompt, b64, mime)
            elif hasattr(service, "generate_with_image"):
                img_bytes = base64.b64decode(b64)
                return service.generate_with_image(prompt, img_bytes)

        # Fallback: try Gemini-style
        raise RuntimeError(
            "Provider hiện tại không hỗ trợ Vision.\n"
            "Vui lòng dùng Google Gemini hoặc Anthropic Claude."
        )

    def _call_gemini_vision(self, service, prompt: str, b64: str, mime: str) -> str:
        from google import genai as _genai
        from google.genai import types as _types
        from config import (
            AI_ERROR_KEYWORDS_INVALID_KEY, AI_ERROR_KEYWORDS_SERVER,
            AI_SERVER_ERROR_RETRY_DELAY,
        )
        import time as _time

        img_bytes = base64.b64decode(b64)
        last_err = None

        # ── Outer loop: retry trên transient server errors (503/500/overload).
        # Đặc biệt Gemini 2.x free tier hay trả 503 "high demand" lúc cao điểm.
        # Backoff: 3s → 6s → 12s (3 lần thử).
        max_outer = 3
        for outer in range(1, max_outer + 1):
            for key in service._keys:
                try:
                    if key not in service._client_cache:
                        service._client_cache[key] = _genai.Client(api_key=key)
                    client = service._client_cache[key]

                    response = client.models.generate_content(
                        model=service._model,
                        contents=[
                            _types.Content(
                                parts=[
                                    _types.Part(text=prompt),
                                    _types.Part(
                                        inline_data=_types.Blob(
                                            mime_type=mime,
                                            data=img_bytes,
                                        )
                                    ),
                                ]
                            )
                        ],
                        config=_types.GenerateContentConfig(
                            temperature=0.1,
                            max_output_tokens=8000,
                        ),
                    )
                    return response.text
                except Exception as e:
                    last_err = e
                    msg = str(e).lower()
                    if any(kw in msg for kw in AI_ERROR_KEYWORDS_INVALID_KEY):
                        continue  # đổi key
                    if any(kw in msg for kw in AI_ERROR_KEYWORDS_SERVER):
                        # 503 / 500 / overloaded → break inner loop để chờ retry
                        break
                    raise
            else:
                # All keys exhausted với quota error → không retry nữa
                break

            # Outer retry vẫn còn → chờ backoff
            if outer < max_outer:
                wait = AI_SERVER_ERROR_RETRY_DELAY * (2 ** (outer - 1))
                _log.info("Gemini Vision 503 — chờ %ds rồi thử lại "
                          "(lần %d/%d)", wait, outer + 1, max_outer)
                _time.sleep(wait)

        # ── Định dạng lỗi cuối cùng — phân biệt 503 vs các lỗi khác ──
        err_str = str(last_err) if last_err else "Không rõ lỗi"
        if any(kw in err_str.lower() for kw in AI_ERROR_KEYWORDS_SERVER):
            raise RuntimeError(
                f"Gemini đang quá tải sau {max_outer} lần thử "
                f"(503 UNAVAILABLE).\n\n"
                f"Cách khắc phục:\n"
                f"  • Chờ 30-60 giây rồi nhấn lại 'Chuyển đổi'.\n"
                f"  • Hoặc đổi model ở tab Cài đặt sang Gemini 1.5 Pro "
                f"(ít overload hơn)."
            )
        raise RuntimeError(f"Gemini Vision lỗi: {last_err}")

    def _call_claude_vision(self, service, prompt: str, b64: str, mime: str) -> str:
        import anthropic as _anthropic
        import time as _time
        from config import (
            MODEL_MAX_TOKENS, DEFAULT_MAX_TOKENS,
            AI_ERROR_KEYWORDS_INVALID_KEY, AI_ERROR_KEYWORDS_SERVER,
            AI_SERVER_ERROR_RETRY_DELAY,
        )

        max_tokens = MODEL_MAX_TOKENS.get(service._model, DEFAULT_MAX_TOKENS)
        last_err = None
        max_outer = 3

        for outer in range(1, max_outer + 1):
            for key in service._keys:
                try:
                    client = _anthropic.Anthropic(api_key=key)
                    resp = client.messages.create(
                        model=service._model,
                        max_tokens=max_tokens,
                        messages=[{
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime,
                                        "data": b64,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": prompt,
                                },
                            ],
                        }],
                    )
                    return resp.content[0].text
                except Exception as e:
                    last_err = e
                    msg = str(e).lower()
                    if any(kw in msg for kw in AI_ERROR_KEYWORDS_INVALID_KEY):
                        continue
                    if any(kw in msg for kw in AI_ERROR_KEYWORDS_SERVER):
                        break  # chờ outer retry
                    raise
            else:
                break

            if outer < max_outer:
                wait = AI_SERVER_ERROR_RETRY_DELAY * (2 ** (outer - 1))
                _log.info("Claude Vision overload — chờ %ds (lần %d/%d)",
                          wait, outer + 1, max_outer)
                _time.sleep(wait)

        err_str = str(last_err) if last_err else "Không rõ lỗi"
        if any(kw in err_str.lower() for kw in AI_ERROR_KEYWORDS_SERVER):
            raise RuntimeError(
                f"Claude đang quá tải sau {max_outer} lần thử.\n\n"
                f"Hãy chờ ít phút rồi thử lại."
            )
        raise RuntimeError(f"Claude Vision lỗi: {last_err}")

    # ──────────────────────────────────────────────────────────────────────
    #  RESULT HANDLING
    # ──────────────────────────────────────────────────────────────────────

    def _on_convert_done(self, questions: list, raw_struct: str,
                          _error_unused=None, detected_meta: Optional[dict] = None):
        """Pipeline thành công — đổ vào treeview + bật nút export.

        Output text dùng format Word-ready (paste vào Word ăn ngay), KHÔNG
        hiển thị raw ===CAU===/===KETCAU=== nữa — đỡ làm rối mắt user.
        Raw struct vẫn được lưu ở `self._img_raw_struct` phòng khi cần debug.

        Parameters
        ----------
        detected_meta: [SMART-1] dict {subject, grade, topic} từ Vision —
                       Nếu khác giá trị hiện tại ở tab Cài đặt → show toast
                       gợi ý áp dụng.
        """
        self._busy = False
        self._convert_btn.configure(state="normal", text="🚀 Chuyển đổi")
        self._img_detected_meta = detected_meta or {}

        self._img_questions = list(questions)

        # Đổ vào treeview
        for item in self._q_tree.get_children():
            self._q_tree.delete(item)

        for idx, q in enumerate(questions, 1):
            content = (q.question or "").replace("\n", " ")
            preview = content[:100] + "…" if len(content) > 100 else content
            topic = (q.topic or "")
            topic = topic[:25] + "…" if len(topic) > 25 else topic

            tags = ()
            review = getattr(q, "_review", None)
            if isinstance(review, dict) and review.get("ok") is False:
                tags = ("verify_fail",)

            self._q_tree.insert(
                "", "end", iid=str(idx - 1),
                values=(
                    idx, q.qtype, q.level or "—",
                    topic, self._format_dapan(q), preview,
                ),
                tags=tags,
            )

        # Đếm số câu cần xem lại
        n_fail = sum(
            1 for q in questions
            if isinstance(getattr(q, "_review", None), dict)
            and q._review.get("ok") is False
        )
        n = len(questions)
        info = (f"{n} câu  |  TN: {sum(1 for q in questions if q.qtype=='TN')}  "
                f"DS: {sum(1 for q in questions if q.qtype=='DS')}  "
                f"TLN: {sum(1 for q in questions if q.qtype=='TLN')}  "
                f"TL: {sum(1 for q in questions if q.qtype=='TL')}")
        if n_fail:
            info += f"  ⚠️ {n_fail} câu cần xem lại"
        self._img_count_lbl.configure(text=info)

        # Show Word-ready text (paste vào Word là đẹp ngay, không cần chỉnh)
        try:
            from export.question_formatter import format_questions
            preview_text = format_questions(questions, include_solution=True)
        except Exception as e:
            _log.warning("format_questions failed, fallback to raw: %s", e)
            preview_text = raw_struct or ""

        self._output_text.configure(state="normal")
        self._output_text.delete("1.0", "end")
        self._output_text.insert("1.0", preview_text)
        self._output_text.configure(state="disabled")

        # Enable action buttons
        self._img_export_btn.configure(state="normal")
        self._img_nhch_btn.configure(state="normal")
        self._copy_btn.configure(state="normal")

        self._stop_img_timer()
        import time as _time
        elapsed = int(_time.time() - self._img_start_time) if self._img_start_time else 0
        mins, secs = divmod(elapsed, 60)
        self._img_timer_var.set(f"⏱️ {mins:02d}:{secs:02d}")
        self._img_stage_var.set(f"✅ Hoàn tất trong {mins:02d}:{secs:02d}!")

        msg = f"✅ Hoàn tất! Đã trích {n} câu hỏi ({mins:02d}:{secs:02d})"
        if n_fail:
            msg += f" (có {n_fail} câu được AI đánh dấu cần xem lại)"
        self._status_lbl.configure(text=msg)

        # [SMART-1] Show suggestion toast nếu Vision detect được metadata
        # khác giá trị hiện tại ở tab Cài đặt.
        self._maybe_show_meta_suggestion(detected_meta)

    def _maybe_show_meta_suggestion(self, detected: Optional[dict]) -> None:
        """[SMART-1] Hiện toast gợi ý apply detected metadata vào tab Cài đặt.

        Chỉ hiện toast nếu:
          - Có ít nhất 1 field detected (subject/grade/topic) khác rỗng
          - Khác giá trị hiện tại
          - Có get_subject_grade callback (để biết giá trị hiện tại)
        """
        if not detected:
            return
        det_subj = detected.get("subject", "").strip()
        det_grade = detected.get("grade", "").strip()
        det_topic = detected.get("topic", "").strip()
        if not (det_subj or det_grade or det_topic):
            return

        # So sánh với giá trị hiện tại
        cur_subj, cur_grade = "", ""
        if self._get_subject_grade:
            try:
                cur_subj, cur_grade = self._get_subject_grade()
            except Exception:
                pass

        # Chỉ suggest nếu khác (case-insensitive cho subject)
        subj_diff = det_subj and det_subj.lower() != cur_subj.lower()
        grade_diff = det_grade and str(det_grade) != str(cur_grade)
        if not (subj_diff or grade_diff):
            # Có thể vẫn show "topic" nhưng nhẹ hơn — bỏ qua nếu topic không
            # khác đáng kể. Đơn giản: skip nếu subject + grade khớp.
            _log.info("Detected meta khớp với cài đặt hiện tại — skip toast")
            return

        # Build toast message
        parts = []
        if subj_diff:
            parts.append(f"Môn: {cur_subj or '(trống)'} → {det_subj}")
        if grade_diff:
            parts.append(f"Lớp: {cur_grade or '(trống)'} → {det_grade}")
        if det_topic:
            parts.append(f"Chủ đề: {det_topic}")
        msg = "Vision phát hiện trong ảnh:\n• " + "\n• ".join(parts)

        try:
            from ui.toast import Toast
        except Exception as e:
            _log.debug("Toast import failed: %s", e)
            return

        def _apply_meta():
            """Apply detected meta vào tab Cài đặt (qua callback nếu có)."""
            if self._on_apply_detected_meta is None:
                # Không có callback → chỉ update exam_data hiện tại
                pass
            else:
                try:
                    self._on_apply_detected_meta(det_subj, det_grade, det_topic)
                except Exception as e:
                    _log.warning("apply_detected_meta failed: %s", e)
            self._status_lbl.configure(
                text=f"✅ Đã áp dụng môn/lớp từ Vision: "
                     f"{det_subj or cur_subj} {det_grade or cur_grade}")

        try:
            Toast(
                self.winfo_toplevel(),
                title="🔍 Phát hiện thông tin đề",
                message=msg,
                actions=[
                    ("✓ Áp dụng", _apply_meta),
                    ("Bỏ qua", None),
                ],
                duration_ms=15000,
                variant="info",
            ).show()
        except Exception as e:
            _log.debug("Toast show failed: %s", e)

    def _on_convert_failed(self, error_msg: str):
        """Pipeline lỗi — bật lại nút Convert + báo lỗi."""
        self._busy = False
        self._stop_img_timer()
        self._convert_btn.configure(state="normal", text="🚀 Chuyển đổi")
        self._img_pb["value"] = 0
        head = (error_msg.splitlines()[0] if error_msg else "Lỗi")[:100]
        self._img_stage_var.set("❌ " + head)
        self._status_lbl.configure(text="❌ Lỗi")
        messagebox.showerror("Lỗi chuyển đổi", error_msg or "Không rõ lỗi.")

    def _show_raw_response(self, raw: str):
        """Hiện raw AI response trong output_text — dùng khi parse fail.

        Giúp user xem AI trả về gì để debug (vd: prompt sai, ảnh khó OCR).
        """
        try:
            self._output_text.configure(state="normal")
            self._output_text.delete("1.0", "end")
            self._output_text.insert("1.0",
                "AI Vision trả về (KHÔNG parse được — hiển thị nguyên văn):\n"
                "─────────────────────────────────────────\n" +
                (raw or "(rỗng)") +
                "\n─────────────────────────────────────────\n"
                "Bạn có thể: copy → chỉnh thủ công → dán lại vào tab "
                "'AI Text → Câu hỏi' để parse.")
            self._output_text.configure(state="disabled")
        except Exception as e:
            _log.debug("show_raw_response failed: %s", e)

    @staticmethod
    def _best_effort_strip(text: str) -> str:
        """Strip AI response → text câu hỏi gốc.

        - Bỏ markdown fence ```.
        - Bỏ dòng "===CAU===" / "===KETCAU===" / "LOAI:" / "MUCDO:" etc.
        - Bỏ dòng "DAPAN:" / "LOIGIAI:" rỗng.
        - Bỏ "NOIDUNG:" prefix (giữ phần sau).
        - Bỏ lời chào AI thường gặp.
        """
        if not text:
            return ""

        # Strip markdown fence
        t = text.strip()
        if t.startswith("```"):
            t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        if t.endswith("```"):
            t = re.sub(r"\s*```\s*$", "", t)

        lines = t.splitlines()
        kept: list[str] = []
        SKIP_PREFIXES = (
            "===CAU===", "===KETCAU===",
            "LOAI:", "MUCDO:", "CHUONG:",
            "NOIDUNG:",
            "DAPAN:", "LOIGIAI:",
            "A:", "B:", "C:", "D:",
            "a:", "b:", "c:", "d:",
        )
        SKIP_PHRASES = (
            "dưới đây là", "sau đây là", "đây là",
            "tôi sẽ", "tôi đã", "chắc chắn", "được rồi",
            "sure,", "here is", "of course",
        )
        for ln in lines:
            stripped = ln.strip()
            if not stripped:
                kept.append("")
                continue
            up = stripped.upper()
            if any(up.startswith(p.upper()) for p in SKIP_PREFIXES):
                # Special-case NOIDUNG: giữ phần sau dấu ":"
                if up.startswith("NOIDUNG:"):
                    rest = stripped.split(":", 1)[1].strip()
                    if rest:
                        kept.append(rest)
                continue
            low = stripped.lower()
            if any(low.startswith(p) for p in SKIP_PHRASES):
                continue
            kept.append(stripped)

        # Bỏ "Câu N." prefix ở dòng đầu (sẽ được app tự thêm lại)
        result = "\n".join(kept).strip()
        result = re.sub(
            r"^(?:Câu|CÂU|Bài|BÀI)\s*\d+\s*[.\):]\s*",
            "", result, count=1, flags=re.IGNORECASE,
        )
        # Squash dòng trống liên tiếp
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()

    # ──────────────────────────────────────────────────────────────────────
    #  EDIT — sửa câu hỏi inline trước khi xuất / lưu NHCH
    # ──────────────────────────────────────────────────────────────────────

    def _on_q_tree_double_click(self, event=None):
        """Double-click 1 dòng → mở dialog sửa câu hỏi đó.

        Dùng lại `_QuestionEditDialog` của NHCH preview — cho phép sửa
        nội dung, chủ đề, mức độ, phương án, đáp án, lời giải, ảnh kèm…
        """
        sel = self._q_tree.selection()
        if not sel:
            return
        try:
            idx = int(sel[0])  # iid được set = string(idx)
        except (ValueError, TypeError):
            return
        if idx < 0 or idx >= len(self._img_questions):
            return

        q = self._img_questions[idx]

        # Lấy subject + grade từ tab Cài đặt cho dialog gợi ý
        subj, grade = "Toán", "12"
        if self._get_subject_grade:
            try:
                subj, grade = self._get_subject_grade()
            except Exception:
                pass

        # Mở dialog edit (chia sẻ với NHCH preview)
        try:
            from ui.dialog_nhch_preview import _QuestionEditDialog
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không mở được dialog sửa: {e}")
            return

        def _on_save():
            # Sau khi user lưu → refresh treeview + output text
            self._refresh_after_edit()

        _QuestionEditDialog(
            self.winfo_toplevel(),
            q, subj, grade,
            on_save=_on_save,
        )

    def _refresh_after_edit(self):
        """Cập nhật treeview + output text sau khi user sửa 1 câu hỏi."""
        questions = self._img_questions
        if not questions:
            return

        # Cập nhật từng dòng trong treeview
        for idx, q in enumerate(questions, 1):
            content = (q.question or "").replace("\n", " ")
            preview = content[:100] + "…" if len(content) > 100 else content
            topic = (q.topic or "")
            topic = topic[:25] + "…" if len(topic) > 25 else topic
            iid = str(idx - 1)
            try:
                self._q_tree.item(
                    iid, values=(
                        idx, q.qtype, q.level or "—",
                        topic, self._format_dapan(q), preview,
                    ),
                )
            except tk.TclError:
                pass

        # Refresh output text (Word-ready)
        try:
            from export.question_formatter import format_questions
            preview_text = format_questions(questions, include_solution=True)
            self._output_text.configure(state="normal")
            self._output_text.delete("1.0", "end")
            self._output_text.insert("1.0", preview_text)
            self._output_text.configure(state="disabled")
        except Exception as e:
            _log.debug("refresh format_questions failed: %s", e)

    # ──────────────────────────────────────────────────────────────────────
    #  EXPORT — Word (auto-open) / NHCH
    # ──────────────────────────────────────────────────────────────────────

    def _img_export_word(self):
        """Build ExamData → export Word → tự mở file khi xong."""
        if not self._img_questions:
            messagebox.showinfo("Thông báo", "Chưa có câu hỏi để xuất.")
            return

        save_path = filedialog.asksaveasfilename(
            title="Lưu file Word",
            defaultextension=".docx",
            initialfile="Convert_Anh.docx",
            filetypes=[("Word", "*.docx")],
        )
        if not save_path:
            return

        try:
            from core.models import ExamData
            from export.word_exporter import export_to_word
            from config import is_word_auto_convert_tables_enabled

            subj, grade = "Toán", ""
            if self._get_subject_grade:
                try:
                    subj, grade = self._get_subject_grade()
                except Exception:
                    pass

            exam = ExamData(
                exam_title="CÂU HỎI CHUYỂN TỪ ẢNH",
                subject=subj, grade=grade or "",
                semester="", year="", time="",
                questions=self._img_questions,
            )
            export_to_word(
                exam,
                save_path,
                include_solution=True,
                auto_convert_tables=is_word_auto_convert_tables_enabled(),
            )
            self._status_lbl.configure(
                text=f"✅ Đã xuất {len(self._img_questions)} câu → Word")
            self._img_last_exported_path = save_path
            self._img_folder_btn.configure(state="normal")

            # Auto-open theo yêu cầu [3]
            try:
                os.startfile(save_path)
            except Exception as e:
                _log.warning("Không thể tự mở file Word: %s", e)
                messagebox.showinfo(
                    "Đã xuất xong",
                    f"Đã xuất xong:\n{save_path}\n\n"
                    f"(Không tự mở được — bạn mở thủ công.)")
        except Exception as e:
            _log.exception("Export Word failed")
            messagebox.showerror("Lỗi xuất Word", str(e))

    def _img_save_nhch(self):
        """Mở dialog NHCH xem trước → cho user sửa metadata → lưu."""
        if not self._img_questions:
            messagebox.showinfo("Thông báo", "Chưa có câu hỏi để lưu vào NHCH.")
            return

        subj, grade = "Toán", "12"
        if self._get_subject_grade:
            try:
                subj, grade = self._get_subject_grade()
            except Exception:
                pass

        # Gán structured ID nếu cần
        try:
            from core.models import assign_structured_ids
            need_id = [
                q for q in self._img_questions
                if getattr(q, "question_id", "").startswith("QID-")
            ]
            if need_id:
                for q in need_id:
                    if not q.topic:
                        q.topic = subj
                assign_structured_ids(need_id, grade)
        except Exception as e:
            _log.warning("assign_structured_ids failed (image flow): %s", e)

        from ui.dialog_nhch_preview import NHCHPreviewDialog
        from storage.database import save_questions

        _holder: dict = {"dialog": None}

        def _do_save(questions):
            dlg = _holder.get("dialog")
            final_subj = getattr(dlg, "final_subject", None) or subj
            final_grade = getattr(dlg, "final_grade", None) or grade
            try:
                n = save_questions(questions, final_subj, final_grade,
                                    source="Image Convert")
                self._status_lbl.configure(
                    text=f"✅ Đã lưu {n} câu vào NHCH "
                         f"(Môn: {final_subj}, Lớp: {final_grade})")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể lưu vào NHCH:\n{e}")

        _holder["dialog"] = NHCHPreviewDialog(
            self.winfo_toplevel(),
            self._img_questions,
            subj, grade,
            on_confirm=_do_save,
        )

    # ──────────────────────────────────────────────────────────────────────
    #  COPY
    # ──────────────────────────────────────────────────────────────────────

    def _copy_result(self):
        text = self._output_text.get("1.0", "end-1c")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._copy_btn.configure(text="✅ Đã copy!")
            self.after(2000, lambda: self._copy_btn.configure(text="📋 Copy text"))

    # ──────────────────────────────────────────────────────────────────────
    #  PDF → WORD
    # ──────────────────────────────────────────────────────────────────────

    def _pdf_log_append(self, text: str):
        """Thêm dòng vào log panel (thread-safe qua after)."""
        def _do():
            self._pdf_log.configure(state="normal")
            self._pdf_log.insert("end", text + "\n")
            self._pdf_log.see("end")
            self._pdf_log.configure(state="disabled")
        self.after(0, _do)

    # ── PDF Timer & Range Helpers ──

    def _start_pdf_timer(self):
        """Bắt đầu đếm thời gian cho PDF convert."""
        self._stop_pdf_timer()
        import time as _time
        self._pdf_start_time = _time.time()
        self._pdf_timer_var.set("⏱️ 00:00")
        self._pdf_eta_var.set("")
        self._tick_pdf_timer()

    def _tick_pdf_timer(self):
        """Cập nhật đồng hồ bấm giờ mỗi giây."""
        if not self._pdf_busy:
            return
        import time as _time
        elapsed = int(_time.time() - self._pdf_start_time)
        mins = elapsed // 60
        secs = elapsed % 60
        self._pdf_timer_var.set(f"⏱️ {mins:02d}:{secs:02d}")
        self._pdf_timer_id = self.after(1000, self._tick_pdf_timer)

    def _stop_pdf_timer(self):
        """Dừng đồng hồ bấm giờ."""
        if self._pdf_timer_id:
            try:
                self.after_cancel(self._pdf_timer_id)
            except Exception:
                pass
            self._pdf_timer_id = None

    def _on_pdf_range_mode_changed(self):
        """Callback khi chuyển chế độ chọn trang (Toàn bộ / Tùy chọn)."""
        if self._pdf_range_mode.get() == "custom":
            try:
                self._pdf_pages_input.focus_set()
            except Exception:
                pass
        self._update_pdf_estimate()

    def _parse_pdf_page_range(self, total_pages: int) -> list[int]:
        """Xác định danh sách chỉ số trang (0-indexed) cần chuyển đổi."""
        if self._pdf_range_mode.get() == "all" or not self._pdf_pages_entry.get().strip():
            return list(range(total_pages))

        spec = self._pdf_pages_entry.get().strip()
        pages = set()
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                try:
                    s_str, e_str = part.split("-", 1)
                    s = max(1, min(total_pages, int(s_str.strip())))
                    e = max(1, min(total_pages, int(e_str.strip())))
                    step = 1 if s <= e else -1
                    pages.update(range(s - 1, e, step) if step == 1 else range(e - 1, s))
                except Exception:
                    pass
            else:
                try:
                    p = int(part)
                    if 1 <= p <= total_pages:
                        pages.add(p - 1)
                except Exception:
                    pass
        res = sorted(list(pages))
        return res if res else list(range(total_pages))

    def _update_pdf_estimate(self):
        """Cập nhật nhãn ước tính số lần gọi API theo trang đã chọn."""
        if not self._pdf_path or not self._pdf_page_count:
            return
        target_pages = self._parse_pdf_page_range(self._pdf_page_count)
        n = len(target_pages)
        if n == self._pdf_page_count:
            page_text = f"toàn bộ {n} trang"
        else:
            page_text = f"{n}/{self._pdf_page_count} trang đã chọn ({', '.join(str(p+1) for p in target_pages[:8])}{'...' if n > 8 else ''})"

        self._pdf_estimate_var.set(
            f"📊 Ước tính: {n} lần gọi API ({page_text})\n"
            f"💡 Mỗi trang sẽ được chụp ảnh nét cao → AI Vision đọc toàn bộ văn bản và công thức LaTeX."
        )

    def _choose_pdf(self):
        path = filedialog.askopenfilename(
            title="Chọn file PDF",
            filetypes=[("PDF", "*.pdf"), ("Tất cả", "*.*")],
        )
        if not path:
            return
        self._pdf_path = path
        self._pdf_clear_btn.configure(state="normal")

        # Đếm số trang
        try:
            import fitz
            doc = fitz.open(path)
            self._pdf_page_count = len(doc)
            doc.close()
        except ImportError:
            messagebox.showerror(
                "Thiếu thư viện",
                "Cần cài PyMuPDF để xử lý PDF:\n\npip install pymupdf")
            self._pdf_path = None
            return
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được PDF:\n{e}")
            self._pdf_path = None
            return

        fname = Path(path).name
        try:
            sz_mb = os.path.getsize(path) / (1024 * 1024)
            sz_text = f" ({sz_mb:.1f} MB)" if sz_mb >= 1 else f" ({int(os.path.getsize(path)/1024)} KB)"
        except Exception:
            sz_text = ""

        self._pdf_drop_label.configure(
            text=f"📄 {fname}{sz_text}\n\n📑 {self._pdf_page_count} trang\n\n(Nhấn để chọn file khác)")

        # Ước tính API calls
        self._update_pdf_estimate()

        self._pdf_convert_btn.configure(state="normal")

        # Reset progress
        self._pdf_pb["value"] = 0
        self._pdf_progress_var.set("Sẵn sàng chuyển đổi")
        self._pdf_timer_var.set("⏱️ 00:00")
        self._pdf_eta_var.set("")
        self._pdf_log.configure(state="normal")
        self._pdf_log.delete("1.0", "end")
        self._pdf_log.configure(state="disabled")
        self._pdf_open_btn.configure(state="disabled")
        self._pdf_folder_btn.configure(state="disabled")
        self._pdf_output_path = None

    def _clear_pdf(self):
        self._stop_pdf_timer()
        self._pdf_path = None
        self._pdf_page_count = 0
        self._pdf_drop_label.configure(
            text="📄\n\nKéo thả hoặc nhấn để chọn file PDF\n\nHỗ trợ: .pdf")
        self._pdf_estimate_var.set(
            "📊 Chọn file PDF để xem ước tính số lần gọi API")
        self._pdf_convert_btn.configure(state="disabled")
        self._pdf_clear_btn.configure(state="disabled")
        self._pdf_pb["value"] = 0
        self._pdf_progress_var.set("Chưa bắt đầu")
        self._pdf_timer_var.set("⏱️ 00:00")
        self._pdf_eta_var.set("")
        self._pdf_log.configure(state="normal")
        self._pdf_log.delete("1.0", "end")
        self._pdf_log.configure(state="disabled")
        self._pdf_open_btn.configure(state="disabled")
        self._pdf_folder_btn.configure(state="disabled")
        self._pdf_output_path = None

    def _cancel_pdf_convert(self):
        self._pdf_cancel = True
        self._stop_pdf_timer()
        # Set event để extract_page_images (đang chạy trong worker thread)
        # thoát ngay thay vì phải chờ hết trang hiện tại.
        try:
            self._pdf_cancel_event.set()
        except AttributeError as e:
            _log.debug("cancel_event missing (hot-reload?): %s", e)
        self._pdf_cancel_btn.configure(state="disabled")
        self._pdf_eta_var.set("Đã dừng")

    def _start_pdf_convert(self):
        if self._pdf_busy or not self._pdf_path:
            return
        if self._get_ai_call is None:
            messagebox.showerror("Lỗi", "Chưa cấu hình AI. Kiểm tra tab Cài đặt.")
            return

        target_pages = self._parse_pdf_page_range(self._pdf_page_count)
        if not target_pages:
            messagebox.showwarning("Cảnh báo", "Không có trang nào hợp lệ được chọn!")
            return

        # Xác nhận với user
        total_sel = len(target_pages)
        msg_pages = f"Toàn bộ {total_sel} trang" if total_sel == self._pdf_page_count else f"{total_sel}/{self._pdf_page_count} trang đã chọn"
        ok = messagebox.askyesno(
            "Xác nhận chuyển đổi",
            f"File: {Path(self._pdf_path).name}\n"
            f"Phạm vi: {msg_pages}\n"
            f"Số lần gọi API Vision: {total_sel}\n\n"
            f"Bạn có muốn bắt đầu chuyển đổi?",
        )
        if not ok:
            return

        # Chọn nơi lưu
        save_path = filedialog.asksaveasfilename(
            title="Lưu file Word",
            defaultextension=".docx",
            initialfile=Path(self._pdf_path).stem + "_converted.docx",
            filetypes=[("Word", "*.docx")],
        )
        if not save_path:
            return

        self._pdf_busy = True
        self._pdf_cancel = False
        # Reset event cho phiên convert mới (clear() làm is_set()=False)
        try:
            self._pdf_cancel_event.clear()
        except AttributeError as e:
            _log.debug("cancel_event missing on clear (hot-reload?): %s", e)
        self._pdf_convert_btn.configure(state="disabled",
                                        text="⏳ Đang xử lý…")
        self._pdf_cancel_btn.configure(state="normal")
        self._pdf_clear_btn.configure(state="disabled")
        self._pdf_open_btn.configure(state="disabled")
        self._pdf_folder_btn.configure(state="disabled")
        self._pdf_output_path = save_path

        self._pdf_log.configure(state="normal")
        self._pdf_log.delete("1.0", "end")
        self._pdf_log.configure(state="disabled")

        # Bật đồng hồ bấm giờ
        self._start_pdf_timer()

        threading.Thread(
            target=self._do_pdf_convert,
            args=(self._pdf_path, save_path, target_pages),
            daemon=True,
        ).start()

    def _do_pdf_convert(self, pdf_path: str, output_path: str,
                        target_page_indices: Optional[list[int]] = None):
        """Worker thread: PDF → ảnh từng trang → AI OCR → Word.

        Đã nâng cấp:
          • Hỗ trợ dải trang tùy chọn (Page Range).
          • Đo thời gian thực tế từng trang và tính thời gian còn lại (ETA).
          • Trích xuất hình ảnh kèm bounding box, lọc logo, sort reading order.
          • Prompt Vision yêu cầu marker dạng [HÌNH 1], [HÌNH 2]…
        """
        import fitz
        from core.pdf_image_extractor import extract_page_images, ExtractionCancelled
        import time as _time

        try:
            doc = fitz.open(pdf_path)
            total_doc = len(doc)
            if target_page_indices is None:
                target_page_indices = list(range(total_doc))

            total_sel = len(target_page_indices)
            self._pdf_log_append(f"📄 Mở file: {Path(pdf_path).name} (Xử lý {total_sel}/{total_doc} trang)")

            page_results: list[dict] = []

            for step_idx, page_idx in enumerate(target_page_indices):
                if self._pdf_cancel:
                    self._pdf_log_append("⏹ Đã hủy bởi người dùng.")
                    self.after(0, self._pdf_convert_finished, None, "Đã hủy")
                    doc.close()
                    return

                page = doc[page_idx]
                page_num = page_idx + 1
                page_start = _time.time()

                pct = int((step_idx / total_sel) * 90)

                # Cập nhật ETA ước tính còn lại
                if step_idx > 0:
                    elapsed_so_far = _time.time() - self._pdf_start_time
                    avg_per_page = elapsed_so_far / step_idx
                    rem_sec = int(avg_per_page * (total_sel - step_idx))
                    rem_m, rem_s = divmod(rem_sec, 60)
                    eta_text = f"⏳ Còn: ~{rem_m:02d}:{rem_s:02d} ({int(avg_per_page)}s/trang)"
                    self.after(0, self._pdf_eta_var.set, eta_text)

                self.after(0, self._pdf_update_progress, pct,
                           f"Đang xử lý trang {page_num} ({step_idx + 1}/{total_sel})…")
                self._pdf_log_append(f"\n── Trang {page_num} ({step_idx + 1}/{total_sel}) ──")

                # 1) Render trang → ảnh PNG (300 DPI) để gửi Vision
                zoom = 300 / 72.0
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_bytes = pix.tobytes("png")
                self._pdf_log_append(
                    f"  📷 Chụp trang {page_num}: {pix.width}×{pix.height}px")
                try:
                    from services.image_precheck import analyze_image_quality

                    quality = analyze_image_quality(img_bytes, name=f"page {page_num}")
                    if quality.warnings:
                        self._pdf_log_append(
                            f"  OCR pre-check: confidence {int(quality.confidence * 100)}% - "
                            + "; ".join(quality.warnings[:3]))
                    else:
                        self._pdf_log_append(
                            f"  OCR pre-check OK: confidence {int(quality.confidence * 100)}%")
                except Exception as e:
                    _log.debug("PDF page precheck skipped: %s", e)

                # 2) Trích xuất hình ảnh với POSITION + FILTER + SORT
                try:
                    page_images = extract_page_images(
                        page, doc,
                        cancel_event=self._pdf_cancel_event,
                    )
                except ExtractionCancelled:
                    self._pdf_log_append("⏹ Hủy giữa trang — dừng trích ảnh.")
                    self.after(0, self._pdf_convert_finished, None, "Đã hủy")
                    doc.close()
                    return
                if page_images:
                    bboxes_str = ", ".join(
                        f"#{im['index']}@({int(im['rect'][0])},{int(im['rect'][1])})"
                        for im in page_images[:8])
                    tail = "…" if len(page_images) > 8 else ""
                    self._pdf_log_append(
                        f"  🖼️ {len(page_images)} hình hợp lệ "
                        f"(đã lọc logo/bg): {bboxes_str}{tail}")
                else:
                    self._pdf_log_append("  🖼️ Không có hình nào (hoặc toàn ảnh trang trí)")

                # 3) Gửi Vision với thông tin số hình → AI chèn đúng [HÌNH N]
                self._pdf_log_append(f"  🤖 Gọi AI Vision OCR…")
                try:
                    b64 = base64.b64encode(img_bytes).decode("utf-8")
                    text = self._call_pdf_vision(
                        b64, "image/png", n_images=len(page_images))
                    text = normalize_math_to_braced_dollars(text)
                    page_dur = _time.time() - page_start
                    self._pdf_log_append(
                        f"  ✅ Nhận {len(text)} ký tự (xong trong {page_dur:.1f}s)")
                except Exception as e:
                    self._pdf_log_append(f"  ❌ Lỗi trang {page_num}: {e}")
                    text = f"[Lỗi OCR trang {page_num}: {e}]"

                page_results.append({
                    "text": text,
                    "images": page_images,
                    "page_num": page_num,
                })

            doc.close()

            # 4) Xuất Word
            self.after(0, self._pdf_update_progress, 92,
                       "Đang tạo file Word…")
            self._pdf_log_append(f"\n📝 Đang đóng gói file Word .docx…")

            self._build_word_from_pages(page_results, output_path)

            elapsed_total = int(_time.time() - self._pdf_start_time)
            mins, secs = divmod(elapsed_total, 60)
            avg_sec = elapsed_total / max(1, total_sel)
            self._pdf_log_append(f"✅ Hoàn tất! Đã lưu: {output_path}")
            self._pdf_log_append(
                f"⏱️ Tổng thời gian: {mins:02d}:{secs:02d} "
                f"(Trung bình {avg_sec:.1f}s/trang cho {total_sel} trang)")
            self.after(0, self._pdf_convert_finished, output_path, None)

        except Exception as e:
            self._pdf_log_append(f"\n❌ Lỗi: {e}")
            self.after(0, self._pdf_convert_finished, None, str(e))

    def _call_pdf_vision(self, b64: str, mime: str,
                         n_images: int = 0) -> str:
        """Gọi AI Vision cho 1 trang PDF (tái sử dụng logic Gemini/Claude).

        Parameters
        ----------
        b64       : base64 PNG trang đã render 300 DPI
        mime      : "image/png" hoặc "image/jpeg"
        n_images  : số hình thực tế đã extract — AI dùng để chèn đúng số
                    marker [HÌNH 1] … [HÌNH N].
        """
        # Build prompt động với số hình
        if n_images > 0:
            hint = (
                f"\n\n[!] TRANG NÀY CÓ ĐÚNG {n_images} HÌNH ẢNH (đã extract). "
                f"Bạn PHẢI chèn ĐÚNG {n_images} marker dạng "
                f"[HÌNH 1: …], [HÌNH 2: …]… [HÌNH {n_images}: …] "
                f"theo thứ tự đọc. Không thêm, không bớt, không bỏ sót.\n"
            )
        else:
            hint = (
                "\n\n[!] TRANG NÀY KHÔNG CÓ HÌNH ẢNH NÀO. "
                "TUYỆT ĐỐI KHÔNG chèn marker [HÌNH …] vào output.\n"
            )
        prompt = _VISION_PROMPT_PDF_PAGE + hint

        ai_gen = self._get_ai_call()
        service = ai_gen.__self__

        if hasattr(service, '_keys') and hasattr(service, '_model'):
            provider = service.provider_name
            if provider == "Google Gemini":
                return self._call_gemini_vision(service, prompt, b64, mime)
            elif provider == "Anthropic Claude":
                return self._call_claude_vision(service, prompt, b64, mime)
            elif hasattr(service, "generate_with_image"):
                img_bytes = base64.b64decode(b64)
                return service.generate_with_image(prompt, img_bytes)

        raise RuntimeError(
            "Provider hiện tại không hỗ trợ Vision.\n"
            "Vui lòng dùng Google Gemini hoặc Anthropic Claude.")

    # ── Helpers: detect & build Word tables ──

    @staticmethod
    def _is_table_line(line: str) -> bool:
        """Kiểm tra dòng có phải dòng bảng (| ... | ... |).

        Loại trừ các dòng mà dấu | chỉ xuất hiện bên trong công thức toán học.
        """
        s = line.strip()
        if not s or "|" not in s:
            return False

        masked, _ = _mask_math_pipes(s)
        if "|" not in masked:
            return False

        if masked.startswith("|") and masked.endswith("|") and len(masked) > 2:
            return True

        if masked.count("|") >= 2:
            return True

        return False

    @staticmethod
    def _is_separator_line(line: str) -> bool:
        """Kiểm tra dòng phân cách bảng: |---|---| hoặc |:---|:---|"""
        s = line.strip()
        if not (s.startswith("|") and s.endswith("|")):
            return False
        inner = s[1:-1]
        cells = inner.split("|")
        return all(re.match(r'^[\s\-:]+$', c) for c in cells)

    @staticmethod
    def _parse_table_row(line: str) -> list[str]:
        """Tách các ô từ dòng bảng, bảo vệ tuyệt đối dấu '|' trong công thức toán và kẹp ${...}$."""
        s = line.strip()
        masked, tokens = _mask_math_pipes(s)
        if masked.startswith("|"):
            masked = masked[1:]
        if masked.endswith("|"):
            masked = masked[:-1]

        raw_cells = masked.split("|")
        cells = []
        for c in raw_cells:
            cell_text = c.strip()
            for k, v in tokens.items():
                cell_text = cell_text.replace(k, v)
            cell_text = normalize_math_to_braced_dollars(cell_text)
            cells.append(cell_text)
        return cells

    def _add_word_table(self, doc, header_cells: list[str],
                        data_rows: list[list[str]]):
        """Tạo bảng Word thật từ dữ liệu đã parse."""
        from docx.shared import Pt, Inches, Cm, RGBColor
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn

        num_cols = max(len(header_cells), max((len(r) for r in data_rows), default=0))
        if num_cols <= 0:
            return

        num_rows = 1 + len(data_rows)

        table = doc.add_table(rows=num_rows, cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.style = "Table Grid"

        # Header row
        for j in range(num_cols):
            cell = table.cell(0, j)
            cell_text = header_cells[j] if j < len(header_cells) else ""
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(cell_text)
            run.bold = True
            run.font.size = Pt(11)
            run.font.name = "Times New Roman"
            # Nền header xám xanh nhạt
            shading = cell._element.get_or_add_tcPr()
            shading_elm = shading.makeelement(
                qn("w:shd"),
                {qn("w:fill"): "D9E2F3", qn("w:val"): "clear"})
            shading.append(shading_elm)

        # Data rows
        for i, row_data in enumerate(data_rows):
            for j in range(num_cols):
                cell = table.cell(i + 1, j)
                cell_text = row_data[j] if j < len(row_data) else ""
                cell.text = ""
                p = cell.paragraphs[0]
                # Canh giữa cho số, dấu hoặc công thức ngắn
                if len(cell_text) <= 8 or any(sym in cell_text for sym in ["+", "-", "0", "\\infty", "\\nearrow", "\\searrow"]):
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(cell_text)
                run.font.size = Pt(11)
                run.font.name = "Times New Roman"

        # Thêm paragraph trống sau bảng cho spacing
        p_sp = doc.add_paragraph("")
        p_sp.paragraph_format.space_before = Pt(2)
        p_sp.paragraph_format.space_after = Pt(4)

    def _build_word_from_pages(self, page_results: list[dict],
                               output_path: str):
        """Tạo file Word từ kết quả OCR — bảng → bảng Word, hình → hình.

        Đã nâng cấp (v4.1.0):
          • Parse marker dạng [HÌNH N: mô tả] — dùng N để tìm hình đúng vị trí.
          • Fallback: [HÌNH: mô tả] không số → gán tuần tự như cũ.
          • Sau khi render text xong, chèn mọi hình CHƯA dùng ở cuối trang
            (tránh mất hình).
        """
        from docx import Document
        from docx.shared import Inches, Pt, Cm
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()
        for section in doc.sections:
            section.page_width = Cm(21.0)
            section.page_height = Cm(29.7)
            section.top_margin = Cm(2.0)
            section.bottom_margin = Cm(2.0)
            section.left_margin = Cm(2.0)
            section.right_margin = Cm(2.0)

        # Style mặc định
        style = doc.styles["Normal"]
        style.font.name = "Times New Roman"
        style.font.size = Pt(12)
        style.paragraph_format.line_spacing = 1.15
        style.paragraph_format.space_after = Pt(3)

        # Regex: khớp cả [HÌNH 1: desc], [HÌNH1:desc], [HÌNH: desc]
        # và cả biến thể [HINH N: ...] (AI đôi khi quên dấu)
        MARKER_RE = re.compile(r"\[H[ÌI]NH\s*(\d+)?\s*:?[^\]]*\]",
                               re.IGNORECASE)

        def _insert_image(img_data: dict):
            """Chèn 1 hình (centered) vào doc."""
            try:
                img_stream = io.BytesIO(img_data["data"])
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                w_px = img_data.get("width", 0)
                max_in = 5.0
                display_w = min(max_in, w_px / 96.0) if w_px > 0 else 3.0
                run = p.add_run()
                run.add_picture(img_stream, width=Inches(display_w))
            except Exception as e:
                # Không thể chèn — thêm placeholder để user biết
                doc.add_paragraph(f"[Lỗi chèn hình: {e}]")

        for pr in page_results:
            text = pr["text"]
            images: list[dict] = pr["images"]
            page_num = pr["page_num"]

            # Thêm ngắt trang (trừ trang đầu)
            if page_num > 1:
                doc.add_page_break()

            # Build map: index → image (1-based)
            img_by_index: dict[int, dict] = {
                im.get("index", 0): im for im in images if im.get("index", 0) > 0
            }
            # Dùng tuần tự nếu marker không có số
            seq_iter = iter(images)
            used_indices: set[int] = set()

            def _resolve_image(n: Optional[int]) -> Optional[dict]:
                """Lấy image theo số (nếu có), else tuần tự."""
                if n is not None and n in img_by_index:
                    used_indices.add(n)
                    return img_by_index[n]
                # Tuần tự — lấy ảnh đầu chưa dùng
                for im in images:
                    idx = im.get("index", 0)
                    if idx not in used_indices:
                        used_indices.add(idx)
                        return im
                return None

            # Tách text theo marker [HÌNH …] — dùng finditer để giữ cả text xen kẽ
            # Mỗi event = ('text', chuỗi) hoặc ('img', số-nguyên-hoặc-None)
            events: list[tuple[str, Any]] = []
            last_end = 0
            for m in MARKER_RE.finditer(text):
                if m.start() > last_end:
                    events.append(("text", text[last_end:m.start()]))
                num_str = m.group(1)
                num = int(num_str) if num_str else None
                events.append(("img", num))
                last_end = m.end()
            if last_end < len(text):
                events.append(("text", text[last_end:]))

            # Render events
            for kind, payload in events:
                if kind == "img":
                    img_data = _resolve_image(payload)
                    if img_data:
                        _insert_image(img_data)
                    # Nếu không resolve được → bỏ marker (KHÔNG in text "[HÌNH N:…]")
                    continue

                # kind == "text" → xử lý bảng / đoạn
                text_block = payload.strip()
                if not text_block:
                    continue

                lines = text_block.split("\n")
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    if not line:
                        i += 1
                        continue

                    # Thử nhận dạng bảng
                    if self._is_table_line(line):
                        table_lines = [line]
                        j = i + 1
                        while j < len(lines):
                            next_l = lines[j].strip()
                            if self._is_table_line(next_l) or \
                               self._is_separator_line(next_l):
                                table_lines.append(next_l)
                                j += 1
                            elif not next_l:
                                break
                            else:
                                break

                        if len(table_lines) >= 2:
                            first_row = self._parse_table_row(table_lines[0])
                            data = []
                            start_idx = 1
                            if len(table_lines) > 1 and self._is_separator_line(table_lines[1]):
                                start_idx = 2
                            for tl in table_lines[start_idx:]:
                                if self._is_separator_line(tl):
                                    continue
                                data.append(self._parse_table_row(tl))
                            if first_row:
                                self._add_word_table(doc, first_row, data)
                                i = j
                                continue

                        # Không dựng được bảng Word -> xuất dòng chứa "|" với ${...}$
                        doc.add_paragraph(normalize_math_to_braced_dollars(line))
                        i += 1
                    else:
                        doc.add_paragraph(normalize_math_to_braced_dollars(line))
                        i += 1

            # Chèn hình còn sót (AI quên mention) xuống cuối trang
            for im in images:
                idx = im.get("index", 0)
                if idx and idx not in used_indices:
                    _insert_image(im)
                    used_indices.add(idx)

        doc.save(output_path)

    def _pdf_update_progress(self, pct: int, text: str):
        self._pdf_pb["value"] = pct
        self._pdf_progress_var.set(text)

    def _pdf_convert_finished(self, output_path: Optional[str],
                              error: Optional[str]):
        """Callback khi chuyển đổi PDF hoàn tất."""
        self._stop_pdf_timer()
        self._pdf_busy = False
        self._pdf_cancel = False
        self._pdf_convert_btn.configure(
            state="normal", text="🚀 Chuyển đổi PDF → Word")
        self._pdf_cancel_btn.configure(state="disabled")
        self._pdf_clear_btn.configure(state="normal")
        self._pdf_eta_var.set("")

        if error:
            self._pdf_pb["value"] = 0
            self._pdf_progress_var.set(f"❌ {error}")
            if error != "Đã hủy":
                messagebox.showerror("Lỗi chuyển đổi PDF", error)
        else:
            self._pdf_pb["value"] = 100
            import time as _time
            elapsed = int(_time.time() - self._pdf_start_time) if self._pdf_start_time else 0
            mins, secs = divmod(elapsed, 60)
            self._pdf_progress_var.set(f"✅ Hoàn tất trong {mins:02d}:{secs:02d}!")
            self._pdf_timer_var.set(f"⏱️ {mins:02d}:{secs:02d}")
            self._pdf_output_path = output_path
            self._pdf_open_btn.configure(state="normal")
            self._pdf_folder_btn.configure(state="normal")

            # Tự động mở Word nếu checkbox được chọn
            if self._pdf_auto_open_var.get() and output_path and os.path.exists(output_path):
                try:
                    os.startfile(output_path)
                except Exception as open_err:
                    _log.warning("Không thể tự mở file Word: %s", open_err)

            messagebox.showinfo(
                "Chuyển đổi thành công",
                f"Đã lưu file Word tại:\n{output_path}\n\nTổng thời gian xử lý: {mins:02d}:{secs:02d}")

    def _open_pdf_result(self):
        """Mở file Word kết quả."""
        if self._pdf_output_path and os.path.exists(self._pdf_output_path):
            try:
                os.startfile(self._pdf_output_path)
            except Exception as e:
                messagebox.showerror("Lỗi mở file", f"Không thể mở file Word:\n{e}")

    def _open_pdf_folder(self):
        """Mở thư mục chứa file Word kết quả."""
        if self._pdf_output_path and os.path.exists(self._pdf_output_path):
            folder = os.path.dirname(os.path.abspath(self._pdf_output_path))
            if os.path.isdir(folder):
                try:
                    os.startfile(folder)
                except Exception as e:
                    messagebox.showerror("Lỗi mở thư mục", f"Không thể mở thư mục:\n{e}")

    # ──────────────────────────────────────────────────────────────────────
    #  KEYBOARD BINDINGS
    # ──────────────────────────────────────────────────────────────────────

    def bind_shortcuts(self, root):
        """Bind Ctrl+V globally when this tab is visible."""
        root.bind("<Control-v>", self._on_ctrl_v)
        root.bind("<Control-V>", self._on_ctrl_v)

    def _on_ctrl_v(self, event=None):
        """Handle Ctrl+V — paste image vào tab Convert (chế độ ảnh hoặc PDF).

        Quy tắc bỏ qua (cho Ctrl+V mặc định chạy):
          • Tab hiện tại KHÔNG phải tab Convert.
          • Đang ở chế độ "AI Text" (paste text vào input box).
          • Focus đang ở 1 Text/Entry CÒN EDIT ĐƯỢC (state="normal"). Text
            chỉ-đọc (state="disabled" như output preview) thì vẫn cho paste
            ảnh — vì paste text vào read-only widget chẳng có tác dụng gì,
            user kỳ vọng dán ảnh.
        """
        # ── 1) Tab Convert có đang được chọn không? ──────────────────────
        try:
            nb = self.master
            if isinstance(nb, ttk.Notebook):
                current = nb.select()
                # nametowidget() để so sánh WIDGET, không dùng so sánh string
                # (path string có thể khác nhau về dấu chấm leading).
                if current:
                    try:
                        current_widget = self.nametowidget(current)
                        if current_widget is not self:
                            return
                    except Exception:
                        # Không resolve được → fallback so chuỗi
                        if str(current) != str(self):
                            return
        except Exception as e:
            _log.debug("notebook inspect failed in Ctrl+V handler: %s", e)
            return

        # ── 2) Đang ở chế độ AI Text → để Ctrl+V dán text ────────────────
        if self._mode_var.get() == "ai_text":
            return

        # ── 3) Focus đang ở widget edit-được → để Ctrl+V dán text ────────
        focused = self.focus_get()
        if isinstance(focused, (tk.Text, tk.Entry, ttk.Entry)):
            try:
                state = str(focused.cget("state"))
            except Exception:
                state = "normal"
            # Chỉ skip khi widget thực sự edit được (state="normal").
            # Read-only / disabled → vẫn paste ảnh.
            if state in ("normal",):
                return

        # ── 4) Tiến hành dán ảnh ─────────────────────────────────────────
        self._paste_image()
        return "break"  # ngăn tk paste text vào widget khác sau đó
