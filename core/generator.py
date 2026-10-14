"""
core/generator.py — Xây dựng prompt và điều phối tạo câu hỏi song song.
Cập nhật: yêu cầu công thức trong ${...}, DS có 4 ý nhận định liên kết + lời giải gộp.
Hỗ trợ: Cross-Model Verification (Phase 2) — dùng 2 model xác nhận đáp án.
"""
from __future__ import annotations
import copy
import random
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from config import (
    TYPE_LABELS, LEVEL_DESC, MAX_WORKERS, MAX_RETRY,
    MA_DE_LABELS, TIME_MAP,
    CROSS_MODEL_VERIFY, CROSS_MODEL_MAX_ATTEMPTS,
)
from core.models import MatrixRow, Question, ExamData, assign_structured_ids
from core.parser import parse_one_question
from core.ai_reviewer import get_few_shot

# ══════════════════════════════════════════════════════════════════════════════
#  PROMPT TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

# Hàm load context từ file chương trình học
_CHUONG_TRINH_CACHE = None

def _load_chuong_trinh_context() -> str:
    global _CHUONG_TRINH_CACHE
    if _CHUONG_TRINH_CACHE is None:
        try:
            from pathlib import Path
            context_path = Path(__file__).parent.parent / "data" / "chuongtrinhhoctap.txt"
            if context_path.exists():
                _CHUONG_TRINH_CACHE = context_path.read_text(encoding="utf-8")
            else:
                _CHUONG_TRINH_CACHE = ""
        except Exception:
            _CHUONG_TRINH_CACHE = ""
    return _CHUONG_TRINH_CACHE

_PROMPT = """\
Bạn là giáo viên Toán THPT Việt Nam có 15+ năm kinh nghiệm ra đề thi và chấm thi THPT QG. Hãy soạn CÂU HỎI SAU theo đúng mẫu.
Môn: {subject} — Lớp: {grade}

THÔNG TIN CÂU HỎI:
  Loại    : {qtype_label}
  Mức độ  : {level} ({level_desc})
  Chủ đề  : {topic}
  Yêu cầu : {requirement}

{chuong_trinh_context}

YÊU CẦU CHẤT LƯỢNG — BẮT BUỘC:
- Tham khảo đề thi THPT QG, đề Sở GD&ĐT, đề minh họa BGD — KHÔNG sao chép nguyên văn.
- Câu hỏi PHẢI có đáp án chính xác TUYỆT ĐỐI, đã kiểm chứng bằng 2 cách giải khác nhau trước khi xuất.
- Số liệu, kết quả phải ĐÚNG toán học. Sai một dấu/một đơn vị là loại.
- Phương án nhiễu (TN) phải gắn với MỘT lỗi sai có tên (forget_condition, sign_error, formula_confusion, unit_mistake, boundary_mistake…); KHÔNG tạo nhiễu ngẫu nhiên.
- Mức độ câu hỏi PHÙ HỢP với {level} — không quá dễ, không quá khó so với yêu cầu.
- LỜI GIẢI NGẮN GỌN, SÚC TÍCH: Chỉ ghi công thức → thay số vào → ra kết quả. KHÔNG viết nhiều dòng tính trung gian. VD đúng: "Thay vào công thức: ${M_e = 5 + \\frac{20-8}{15} \\cdot 5 = 9}$." VD sai: viết 5 dòng triển khai từng phép tính.
- TỰ KIỂM TRA trước khi trả lời: thế ngược đáp án vào đề, giải lại bằng cách khác. Lệch → làm lại.
- Dữ kiện trong đề PHẢI được dùng hết; không thừa, không thiếu điều kiện xác định.
- Đơn vị đo (m, cm², giây, đồng…) NHẤT QUÁN trong toàn bài.
{geometry_tikz_note}
QUY TẮC ĐỊNH DẠNG — TUYỆT ĐỐI TUÂN THỦ:
- YÊU CẦU CỨNG: Mọi công thức toán, ký hiệu, biểu thức PHẢI đặt trong ${...}$ (VD: ${x^2}$, ${\\frac{1}{2}}$, ${\\sqrt{x}}$). KHÔNG viết công thức ngoài ${...}$.
- YÊU CẦU LaTeX: Luôn dùng dấu \\ trước lệnh LaTeX: \\frac, \\sqrt, \\vec, \\overrightarrow, \\mathbb, \\int, \\lim, \\sum, \\log, \\ln, \\sin, \\cos, \\tan, \\infty, \\alpha, \\beta... KHÔNG viết frac, sqrt, sin thiếu dấu \\.
- KÍ HIỆU GÓC: Dùng \\widehat thay vì \\angle. VD: ${\\widehat{{ABC}}}$ thay vì ${\\angle ABC}$. KHÔNG ĐƯỢC dùng \\angle.
- NGOẶC TỰ ĐỘNG SCALE — TUYỆT ĐỐI TUÂN THỦ (KHÔNG ngoại lệ):
  TẤT CẢ ngoặc xuất hiện BÊN TRONG ${...}$ PHẢI dùng \\left...\\right, kể cả
  ngoặc đơn giản nhất hoặc khi bên trong không có biểu thức cao.
  • Ngoặc tròn: \\left( ... \\right)         thay vì ( ... )
  • Ngoặc vuông: \\left[ ... \\right]         thay vì [ ... ]
  • Ngoặc nhọn: \\left\\{{ ... \\right\\}}     thay vì {{ ... }}
  • Giá trị tuyệt đối: \\left| ... \\right|   thay vì | ... |
  • Sàn/trần: \\left\\lfloor ... \\right\\rfloor / \\left\\lceil ... \\right\\rceil
  • Cặp đa cấp: dùng \\left.( hoặc \\right.) khi chỉ cần một bên (vd: ${\\left.\\frac{{dy}}{{dx}}\\right|_{{x=0}}}$)
  VD đúng: ${\\left(\\frac{{1}}{{2}}\\right)^n}$, ${f\\left(x\\right) = 2x+1}$,
           ${\\left[x^2+1\\right]}$, ${\\left|a-b\\right| < 5}$,
           ${\\left\\{{x \\in \\mathbb{{R}} : x>0\\right\\}}}$
  VD SAI:  ${(\\frac{{1}}{{2}})^n}$, ${f(x) = 2x+1}$, ${[x^2+1]}$,
           ${|a-b| < 5}$, ${\\{{x \\in \\mathbb{{R}}\\}}}$
- Mỗi dòng KEY: value — không xuống dòng giữa chừng.
- Chỉ trả về 1 khối ===CAU=== ... ===KETCAU===, không thêm gì khác.
- BẢNG SỐ LIỆU (RẤT QUAN TRỌNG): Nếu câu hỏi liên quan đến thống kê, tần số, bảng phân phối, số liệu ghép nhóm, bảng giá trị... thì BẮT BUỘC phải CÓ bảng số liệu ĐẦY ĐỦ trong NOIDUNG.
  Cách viết bảng: đặt NGAY trong NOIDUNG, dùng "|" ngăn cách cột, mỗi hàng 1 dòng:
  NOIDUNG: Dưới đây là bảng tần số ghép nhóm về điểm kiểm tra...
  Khoảng điểm | Tần số
  [0;2) | 5
  [2;4) | 8
  [4;6) | 12
  Trung bình cộng của mẫu số liệu trên là bao nhiêu?
  (KHÔNG dùng dòng gạch ngang |---|---|)
  (Các dòng bảng viết LIỀN sau dòng NOIDUNG:, KHÔNG cần thêm key mới)
- HÌNH VẼ: Nếu câu cần hình vẽ/biểu đồ, CHÈN TRỰC TIẾP khối TikZ vào NOIDUNG (hoặc LOIGIAI) — đặt trên DÒNG RIÊNG:
  \\begin{{tikzpicture}}...\\end{{tikzpicture}}
  TUYỆT ĐỐI KHÔNG viết "Hình vẽ: [mô tả]" hay bất kỳ mô tả bằng lời về hình.
  TUYỆT ĐỐI KHÔNG dùng tiền tố "TikZ:" trước khối. Hệ thống tự nhận diện khối `\\begin{{tikzpicture}}...\\end{{tikzpicture}}` và chuyển sang PNG.

{vd_note}{ds_note}{format_block}"""

_VD_NOTE = """\
LƯU Ý MỨC VẬN DỤNG (VD):
- Câu hỏi VD PHẢI là bài toán THỰC TẾ, gắn với đời sống: chi phí kinh doanh,
  lợi nhuận, tối ưu diện tích/thể tích đất xây dựng, vận tốc xe-máy bay,
  nhiệt độ theo thời gian, dân số tăng/giảm, sản xuất-đóng gói hàng hóa,
  thể thao (quỹ đạo bóng, góc bắn), y tế (nồng độ thuốc, tăng trưởng vi khuẩn),
  tài chính (lãi kép, trái phiếu, vay trả góp)…
- KHÔNG dùng dạng toán trừu tượng/sách giáo khoa thông thường cho mức VD.
- Ngữ cảnh phải TỰ NHIÊN: có tên người/địa điểm Việt Nam, số liệu hợp lý
  (không xa rời thực tế như "người đi bộ với vận tốc 500 km/h").
- Đơn vị đo phải đúng (m, km, giờ, đồng, kg…) và thống nhất.
- Phải kết hợp 2-3 bước: lập hàm/phương trình → tính → biện luận kết quả.

"""

_GEOMETRY_TIKZ_NOTE = """\
LƯU Ý HÌNH HỌC:
- Bài toán hình học PHẢI có hình minh họa chi tiết bằng TikZ.
- Đặt khối TikZ trên DÒNG RIÊNG, RAW — KHÔNG tiền tố "TikZ:", KHÔNG mô tả "Hình vẽ: ...":
    \\begin{{tikzpicture}}...\\end{{tikzpicture}}
- Hình vẽ phải KHỚP dữ kiện đề bài: tên đỉnh, số đo, quan hệ vuông góc/song song
  đúng hệt yêu cầu. Tỉ lệ hợp lý (đoạn dài hơn vẽ dài hơn, góc lớn hơn vẽ rộng hơn).
- Hình không gian (3D): dùng phép chiếu cabinet
  `[x={{(1cm,0cm)}}, y={{(0.5cm,0.3cm)}}, z={{(0cm,1cm)}}]`;
  cạnh thấy `[thick]`, cạnh khuất `[dashed, thick]`.
- Nhãn đỉnh bằng `\\node[above] at (A) {{$A$}};` — đặt vị trí không trùng cạnh.
- Đánh dấu: góc vuông bằng `pic {{right angle=A--B--C}}`, góc thường bằng
  `pic["$\\alpha$", angle radius=6mm] {{angle=B--A--C}}`.
- VD: tam giác ABC, hình chóp S.ABCD, hình trụ, mặt cầu, đồ thị hàm, miền nghiệm… đều cần TikZ.

"""

# ── Auto-TikZ: khối hướng dẫn AI tự nhận diện và vẽ hình khi cần ──────────────
# Áp dụng cho MỌI loại bài toán (không chỉ hình học): đồ thị hàm, bảng biến
# thiên, biểu đồ thống kê, tứ giác toạ độ, parabol, ellipse, khối không gian…
_AUTO_TIKZ_BLOCK = r"""
LƯU Ý CHÈN HÌNH VẼ TỰ ĐỘNG (TikZ) — QUY TẮC CHẤT LƯỢNG CAO:

[1] KHI NÀO VẼ:
- Bạn PHẢI tự nhận diện câu hỏi có cần hình minh họa hay không. Nếu CẦN, CHÈN
  một khối TikZ đúng CHÍNH XÁC theo dữ kiện đề bài.
- BẮT BUỘC vẽ TikZ khi bài toán có 1 trong các yếu tố:
  • Hình học phẳng: tam giác, tứ giác, đường tròn, đường conic (parabol, ellipse, hyperbol), góc, tiếp tuyến…
  • Hình không gian: hình chóp, lăng trụ, lập phương, hộp, trụ, nón, cầu.
  • Đồ thị hàm số, bất phương trình, tập nghiệm trên trục số, miền nghiệm hệ bpt.
  • Bảng biến thiên, bảng xét dấu (dùng `tkz-tab`).
  • Biểu đồ thống kê: cột (bar), tần số, hình tròn (pie) nếu đề yêu cầu.
  • Hệ trục tọa độ có điểm/vector/đường thẳng/đường cong.
- Nếu câu KHÔNG cần hình (đại số thuần, tính toán số học…) thì KHÔNG chèn TikZ.

[2] CÁCH CHÈN:
- Đặt khối TikZ trên DÒNG RIÊNG, dạng RAW — KHÔNG tiền tố "TikZ:", KHÔNG mô tả "Hình vẽ: ...":
    \begin{tikzpicture} ... \end{tikzpicture}
  (Không bọc `\documentclass`, `\usepackage`, `\begin{document}` — hệ thống tự thêm.)
- TUYỆT ĐỐI KHÔNG viết đoạn "Hình vẽ: …" mô tả hình bằng lời bên cạnh khối TikZ.
  App tự nhận diện khối `\begin{tikzpicture}...\end{tikzpicture}` và chuyển sang PNG.

[3] KIỂM TRA THỰC TẾ (reality-check) — BẮT BUỘC:
- Mọi nhãn điểm/cạnh/góc trong hình PHẢI khớp tên trong đề (A, B, C, ${\alpha}$…).
- Mọi SỐ ĐO trong hình (độ dài, góc, tọa độ) PHẢI khớp dữ kiện — không được bịa.
- Quan hệ vuông góc / song song / tiếp xúc PHẢI đúng; đánh dấu vuông góc bằng
  ô vuông nhỏ (pic right angle), đánh dấu góc bằng cung (arc) có chú thích.
- Nếu đề nói "tam giác vuông tại A" thì A PHẢI ở góc vuông; "cân tại B" → đỉnh B…
- Tỉ lệ hợp lý: đoạn dài hơn phải vẽ dài hơn; góc lớn hơn phải vẽ rộng hơn.

[4] PACKAGES CÓ SẴN:
- amsmath, amssymb, tikz, pgfplots (compat=1.18), tkz-tab, bm, array, booktabs.
- TikZ libraries: calc, angles, quotes, patterns, arrows.meta,
  decorations.markings, intersections, decorations.pathreplacing, positioning,
  3d, shapes.geometric, backgrounds.

[5] PGFPLOTS — TRÁNH LỖI COMPILE:
- `\addplot` PHẢI nằm trong `\begin{axis}...\end{axis}`; dùng `axis lines=middle`.
- Hàm y=f(x): `\addplot[domain=-5:5, samples=100] {x^2+2*x};` — không bọc ngoặc tròn biểu thức.
- NHÂN TƯỜNG MINH: `2*x`, `3*x^2` — không viết `2x` hay `3x^2`.
- Parametric: `\addplot[variable=\t, domain=a:b, samples=100] ({x(\t)}, {\t});`
  — TUYỆT ĐỐI KHÔNG dùng `y` làm biến tự do (pgfplots sẽ báo lỗi).
- Lượng giác: dùng `deg(x)` khi x theo radian: `{sin(deg(x))}`, `{cos(deg(x))}`.
- Samples: thêm `samples=100` hoặc `samples=200` cho hàm cong/sóng.
- Domain: chỉ định `domain=a:b` để kiểm soát phạm vi vẽ.
- Điểm: `\addplot[only marks, mark=*, mark size=2pt] coordinates {(x,y)};`.

[6] HÌNH KHÔNG GIAN (3D) — PHÉP CHIẾU CABINET:
- Dùng phép chiếu cabinet: trục x (ngang), trục y (chéo 30°, rút 0.5), trục z (dọc).
- Chuẩn: `\begin{tikzpicture}[x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]`
- Cạnh THẤY (mặt trước): vẽ `[thick]`.
- Cạnh KHUẤT (mặt sau): vẽ `[dashed, thick]`.
- Đỉnh luôn có nhãn: `\node[above] at (A) {$A$};` — đặt vị trí (above/below/left/right)
  sao cho không trùng cạnh.
- Hình chóp S.ABCD: vẽ đáy ABCD trước (polygon), rồi nối từ mỗi đỉnh lên S.
  Xác định cạnh khuất bằng cách xem đường nối có bị mặt nào che không.

[7] TRỤC SỐ / MIỀN NGHIỆM / BBT:
- Trục số: `\draw[->] (-5,0)--(5,0);` đánh dấu bằng `|` tại các nút;
  nghiệm bao gồm → chấm đặc `\fill (x,0) circle (2pt);`,
  không bao gồm → chấm rỗng `\draw (x,0) circle (2pt);`.
- Miền nghiệm 2D: dùng `\fill[pattern=north east lines, pattern color=blue!50]`
  hoặc `\fill[blue!20, opacity=0.5]`; giữ đường biên rõ ràng.
- Bảng biến thiên (tkz-tab) — BẮT BUỘC KHI BÀI LIÊN QUAN HÀM SỐ:
  Mọi câu về khảo sát hàm / cực trị / tiệm cận / đồ thị PHẢI có BBT. Nếu có
  đồ thị, trả CẢ đồ thị VÀ BBT (2 khối tikzpicture, cách nhau 1 dòng trống).
  Khung chuẩn (đã bọc tikzpicture):
    \begin{tikzpicture}
    \tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$-\infty$, $x_0$, $+\infty$}
    \tkzTabLine{, -, 0, +, }
    \tkzTabVar{+/$+\infty$, -/$y_0$, +/$+\infty$}
    \end{tikzpicture}
  Ký hiệu: `+`/`-` (dấu đạo hàm), `0` (nghiệm), `d` (không xác định/gián đoạn),
  `+D+/a/b` chặn đôi giá trị quanh TCĐ trong \tkzTabVar.
  Mẫu theo dạng: bậc 2 (min/max), bậc 3 (có/không cực trị), bậc 4 trùng phương
  (W/M/U), phân thức (1 TCĐ / 2 tiệm cận / TC xiên), mũ/log (đồng/nghịch biến),
  căn, hàm gián đoạn. BBT phải ĐỒNG BỘ với đồ thị (cùng TXĐ, nghiệm, tiệm cận).

[8] QUY TẮC TIKZ CHUNG:
- Tọa độ dùng dấu phẩy: `(2,3)`; tên node không có khoảng trắng.
- Escape trong `\node`: `\%`, `\&`, `\#`, `\_`.
- Font nhãn: dùng `$...$` trong `\node` để render LaTeX. VD: `\node[above] at (1,2) {$A$};`.
- Tránh đè nhãn lên cạnh: dùng anchor (above, below, above right…)
  và xshift/yshift nhỏ (2-4pt) nếu cần.
- Đánh dấu góc: `\draw pic["$\alpha$", angle radius=6mm] {angle=B--A--C};`.
- Góc vuông: `\draw pic {right angle=A--B--C};` hoặc nét đánh dấu ngắn ở đỉnh.

[9] NHẤT QUÁN VỚI ĐỀ:
- Hình vẽ phải KHỚP dữ kiện đề bài: tên đỉnh, số đo, nhãn, vị trí tương đối
  đúng như yêu cầu; không tự thêm dữ kiện lạ.
- Nếu đề không nêu tọa độ cụ thể, chọn tọa độ hợp lý để hình rõ ràng, CÂN ĐỐI.

"""

_QUALITY_PLUS_BLOCK = r"""
CHUẨN CHẤT LƯỢNG CAO — BẮT BUỘC:

[A] GIAO THỨC TỰ KIỂM TRA (trước khi trả lời):
1. Giải bài bằng cách 1 — ghi ra đáp án.
2. Giải lại bằng cách 2 (biến đổi khác, thế giá trị, dùng máy tính tay) — so kết quả.
3. Nếu LỆCH → giải lại từ đầu, không đoán.
4. Kiểm tra điều kiện xác định (TXĐ), điều kiện tồn tại, dấu của biểu thức.
5. Kiểm tra đơn vị đo (m, cm², giây, đồng…) NHẤT QUÁN trong toàn bài.

[B] CHẤT LƯỢNG ĐỀ BÀI:
- Mỗi dữ kiện trong đề PHẢI được dùng trong lời giải; không dữ kiện thừa,
  không thiếu điều kiện xác định/miền giá trị.
- Số liệu dùng đơn vị thực tế, hợp lý (không ra các số xấu như 17,3281…). Nếu
  kết quả không tròn, điều chỉnh dữ kiện hoặc thêm "làm tròn đến …" vào đề.
- Văn phong sư phạm: mệnh đề rõ ràng, đủ chủ-vị, chấm câu đầy đủ; không dùng
  câu mệnh lệnh cộc lốc kiểu "Tính X.", thay bằng ngữ cảnh cụ thể.
- Tên biến, hàm, điểm NHẤT QUÁN trong suốt câu hỏi và lời giải.
- Không sao chép nguyên văn đề đã công bố; chỉ lấy cảm hứng về dạng bài.

[C] PHƯƠNG ÁN NHIỄU (TN) — THEO MẪU LỖI CÓ TÊN:
Mỗi phương án nhiễu gắn với MỘT lỗi học sinh hay mắc — KHÔNG nhiễu ngẫu nhiên.
Chọn 3 lỗi TỪ DANH SÁCH (khớp chủ đề):
  • "forget_condition" — quên điều kiện xác định (log, căn, mẫu).
  • "sign_error" — đổi dấu sai (chuyển vế, nhân âm, đạo hàm).
  • "formula_confusion" — nhầm công thức gần nhau (C(n,k) vs A(n,k), V_{nón} vs V_{trụ}).
  • "unit_mistake" — sai đơn vị (cm vs m, giây vs phút, cm² vs cm³).
  • "boundary_mistake" — nhầm biên (nghiệm bao gồm/không bao gồm, dấu < vs ≤).
  • "partial_compute" — dừng giữa chừng (chưa cộng C, chưa nhân hệ số).
  • "off_by_one" — sai 1 đơn vị (đếm thừa/thiếu 1).

[D] MỨC ĐỘ — CÂN CHỈNH THEO CẤP:
- NB (Nhận biết): nhận diện công thức, đọc đồ thị — 1 bước áp dụng trực tiếp.
- TH (Thông hiểu): áp dụng công thức, biến đổi 1-2 bước.
- VD (Vận dụng): bài toán THỰC TẾ (chi phí, diện tích, tối ưu), kết hợp 2-3 bước.
- VDC (Vận dụng cao): mô hình phức tạp, nhiều định lý, chứng minh chặt chẽ.
KHÔNG trộn mức: bài NB không được yêu cầu tư duy VD, và ngược lại.

[E] DS (ĐÚNG/SAI):
- 4 nhận định xoay quanh CÙNG tình huống; không rời rạc.
- Trộn đáp án: ít nhất 1 Đúng và 1 Sai (không toàn Đúng hoặc toàn Sai).
- Ý Sai phải "gần đúng" — dễ nhầm — không sai hiển nhiên.
- Mỗi lời giải bắt đầu bằng "Đúng. Vì…" / "Sai. Vì…" và nêu rõ căn cứ toán học.

[F] TLN & TL:
- TLN: đáp số là SỐ ≤ 4 ký tự; nếu vượt, thêm "làm tròn đến …" vào đề.
  Dấu thập phân dùng dấu PHẨY (0,5 không phải 0.5).
- TL: lời giải ĐẦY ĐỦ tới kết quả cuối, không bỏ bước; viết liền mạch, không
  dùng "Bước 1/2/3".

[G] CHỐNG RÒ RỈ ĐÁP ÁN:
- Câu hỏi không chứa gợi ý trực tiếp (VD: "kết quả bằng 5" trong đề).
- Lời giải không "chạy ngược" từ đáp án ra đề.
- Trong DS, nhận định không lặp nguyên văn dữ kiện đề.

"""

_DS_NOTE = """\
LƯU Ý CHO CÂU ĐÚNG/SAI:
- NOIDUNG là 1 TÌNH HUỐNG/NGỮ CẢNH chung (cho hàm f(x), cho dãy số, cho hình học...)
- 4 ý a, b, c, d là các NHẬN ĐỊNH LIÊN KẾT VỚI NHAU về tình huống đó — các ý phải có mối liên hệ logic
- TUYỆT ĐỐI bọc mọi công thức toán trong ${...}$ (ví dụ: ${x^2}$, ${\\frac{1}{2}}$). Luôn dùng \\ trước lệnh LaTeX. Dùng \\left(...)\\right), \\left[...]\\right], \\left\\{...\\right\\} cho mọi ngoặc chứa công thức
- Cấu trúc trả về:
  NOIDUNG: <Tình huống chung, công thức trong ${...}$>
  a: <Nhận định a, liên kết với tình huống>
  b: <Nhận định b, liên kết với tình huống>
  c: <Nhận định c, liên kết với tình huống>
  d: <Nhận định d, liên kết với tình huống>
  DAPAN: a=D,b=S,c=D,d=S  (mix đáp án, không phải tất cả D hoặc tất cả S)
  LOIGIAI: a. Đúng. Vì ... | b. Sai. Vì ... | c. Đúng. Vì ... | d. Sai. Vì ...
  (Mỗi ý lời giải BẮT BUỘC bắt đầu bằng "Đúng." hoặc "Sai." rồi giải thích)
Yêu cầu từng ý:
{item_requirements}

"""

_FMT_TN = """\
===CAU===
LOAI: TN
MUCDO: {level}
CHUONG: {topic}
NOIDUNG: <câu hỏi đầy đủ, công thức trong ${...}$. Nếu có bảng số liệu thì viết bảng ngay dòng tiếp theo:>
<Tiêu đề 1 | Tiêu đề 2 (nếu có bảng)>
<Giá trị 1 | Giá trị 2 (nếu có bảng)>
<Câu hỏi cuối (nếu có)>
A: <phương án A>
B: <phương án B>
C: <phương án C>
D: <phương án D>
DAPAN: <A hoặc B hoặc C hoặc D>
LOIGIAI: <lời giải NGẮN GỌN: chỉ ghi công thức → thay số → kết quả. KHÔNG viết nhiều dòng trung gian, KHÔNG lặp lại phép tính. VD: "Ta có ${{M_e = 5 + \\frac{{20-8}}{{15}} \\cdot 5 = 9}}$. Vậy trung vị là ${{9}}$.">
===KETCAU==="""

_FMT_DS = """\
===CAU===
LOAI: DS
MUCDO: {level}
CHUONG: {topic}
NOIDUNG: <Tình huống/ngữ cảnh CHUNG — công thức trong ${...}$, làm nền liên kết cho 4 ý dưới>
a: <Nhận định a — liên kết với tình huống, công thức trong ${...}$>
b: <Nhận định b — liên kết với tình huống, công thức trong ${...}$>
c: <Nhận định c — liên kết với tình huống, công thức trong ${...}$>
d: <Nhận định d — liên kết với tình huống, công thức trong ${...}$>
DAPAN: a=D,b=S,c=D,d=S
LOIGIAI: a. Đúng. Vì ... [Xuống dòng] b. Sai. Vì ... [Xuống dòng] c. Đúng. Vì ... [Xuống dòng] d. Sai. Vì ... (Mỗi ý giải NGẮN GỌN: công thức → thay số → kết quả, KHÔNG viết nhiều dòng trung gian)
===KETCAU==="""

_FMT_TLN = """\
===CAU===
LOAI: TLN
MUCDO: {level}
CHUONG: {topic}
DIEM: {points}
NOIDUNG: <bài toán đầy đủ, công thức trong ${...}$>
DAPAN: <kết quả là SỐ gồm TỐI ĐA 4 kí tự, ví dụ: 3,14 | 123 | 4321 | 0,14 | -1,2. Nếu kết quả vượt quá 4 kí tự, PHẢI thêm yêu cầu "làm tròn đến ..." vào đề bài để đáp án còn ≤ 4 kí tự. KHÔNG ĐƯỢC viết phương trình hay biểu thức dài>
LOIGIAI: <lời giải NGẮN GỌN: chỉ ghi công thức → thay số → kết quả. KHÔNG viết nhiều dòng trung gian, KHÔNG lặp phép tính. Viết liền mạch, KHÔNG dùng "Bước 1/2/3">
===KETCAU==="""

_FMT_TL = """\
===CAU===
LOAI: TL
MUCDO: {level}
CHUONG: {topic}
DIEM: {points}
NOIDUNG: <bài toán tự luận đầy đủ, công thức trong ${...}$>
LOIGIAI: <lời giải NGẮN GỌN nhưng ĐẦY ĐỦ: ghi công thức → thay số → kết quả. KHÔNG viết nhiều dòng trung gian, KHÔNG lặp phép tính. Viết liền mạch, KHÔNG dùng "Bước 1/2/3". Phải giải trọn vẹn đến kết quả cuối cùng>
===KETCAU==="""

_FMT_MAP = {"TN": _FMT_TN, "DS": _FMT_DS, "TLN": _FMT_TLN, "TL": _FMT_TL}

def _safe_format(template: str, **kwargs) -> str:
    result = template
    for key, val in kwargs.items():
        result = result.replace("{" + key + "}", str(val))
    return result

def build_prompt(row: MatrixRow, subject: str, grade: str) -> str:
    fmt = _safe_format(
        _FMT_MAP.get(row.qtype, _FMT_TL),
        level=row.level, topic=row.topic, points=str(row.points),
    )
    ds_note = ""
    if row.qtype == "DS":
        if row.ds_items:
            item_reqs = "\n".join(
                f"  ý {s.label} [{s.level}]: {s.requirement}"
                for s in row.ds_items
            )
        else:
            item_reqs = f"  ý a/b/c/d: {row.requirement}"
        ds_note = _safe_format(_DS_NOTE, item_requirements=item_reqs)

    vd_note = _VD_NOTE if row.level == "VD" else ""

    # Detect figure-needing topic for TikZ note (mở rộng ra cả đồ thị, thống kê, bbt…)
    _fig_kw = (
        # hình học phẳng / không gian
        "hình học", "tam giác", "tứ giác", "hình vuông", "hình chữ nhật",
        "hình bình hành", "hình thoi", "hình thang", "đường tròn", "đường kính",
        "tiếp tuyến", "dây cung", "elip", "ellipse", "parabol", "parabola",
        "hyperbol", "hyperbola", "conic",
        "hình chóp", "hình lăng trụ", "hình trụ", "hình nón", "hình cầu",
        "hình hộp", "hình lập phương", "mặt cầu", "mặt nón", "mặt trụ",
        "mặt phẳng", "khối đa diện", "khối lăng trụ", "khối chóp",
        "vectơ", "véc tơ", "vector", "tọa độ", "toạ độ",
        "hệ thức lượng", "phép dời hình", "phép đồng dạng", "góc",
        # đồ thị / bảng
        "đồ thị", "bảng biến thiên", "bảng xét dấu", "trục số",
        "biểu đồ", "hình vẽ", "minh họa", "miền nghiệm",
    )
    _req_lower = (row.requirement or "").lower()
    topic_lower = row.topic.lower()
    need_figure = any(k in topic_lower or k in _req_lower for k in _fig_kw)

    # Ưu tiên block Auto-TikZ mở rộng nếu người dùng bật; fallback về note cũ.
    try:
        from config import is_auto_tikz_enabled
        _auto_tikz_on = is_auto_tikz_enabled()
    except Exception:
        _auto_tikz_on = True

    if _auto_tikz_on:
        # Luôn chèn block để AI tự quyết; kèm note cứng khi phát hiện topic có hình.
        geometry_tikz_note = _AUTO_TIKZ_BLOCK + (_GEOMETRY_TIKZ_NOTE if need_figure else "")
    else:
        geometry_tikz_note = _GEOMETRY_TIKZ_NOTE if need_figure else ""

    few_shot = get_few_shot(row.qtype)
    chuong_trinh_context = _load_chuong_trinh_context()

    # [SMART-2] Adaptive prompt hint theo (lớp, môn, chủ đề)
    adaptive_hint = ""
    try:
        from services.adaptive_prompts import get_adaptive_hint
        adaptive_hint = get_adaptive_hint(
            subject=subject, grade=grade,
            topic=row.topic, requirement=row.requirement,
        )
    except Exception:
        # Không fatal — generator vẫn chạy được với prompt mặc định
        pass

    base_prompt = _safe_format(
        _PROMPT,
        subject=subject, grade=grade,
        qtype_label=TYPE_LABELS.get(row.qtype, row.qtype),
        level=row.level,
        level_desc=LEVEL_DESC.get(row.level, ""),
        topic=row.topic,
        requirement=row.requirement,
        ds_note=ds_note,
        vd_note=vd_note,
        geometry_tikz_note=geometry_tikz_note + _QUALITY_PLUS_BLOCK,
        format_block=fmt,
        chuong_trinh_context=chuong_trinh_context,
    )
    # Inject adaptive hint vào CUỐI prompt (ngay trước format_block) — vị trí
    # cuối giúp AI "nhớ" rõ nhất khi sinh câu.
    if adaptive_hint:
        # Chèn vào sau geometry_tikz_note (đứng giữa main prompt + format)
        base_prompt = base_prompt + "\n\n" + adaptive_hint
    return few_shot + base_prompt if few_shot else base_prompt


# ══════════════════════════════════════════════════════════════════════════════
#  GENERATE ONE QUESTION (with retry + cache)
# ══════════════════════════════════════════════════════════════════════════════

def generate_one(
    row: MatrixRow,
    subject: str,
    grade: str,
    ai_call: Callable[[str], str],
    cache_get: Optional[Callable[[str], Optional[str]]] = None,
    cache_set: Optional[Callable[[str, str], None]] = None,
    verifier_ai: Optional[Callable[[str], str]] = None,
    cancel_event: Optional[threading.Event] = None,
) -> Question:
    """Sinh 1 câu hỏi từ 1 MatrixRow.

    Tham số mới: `cancel_event` — nếu set() thì mọi retry bị bỏ qua và hàm
    trả về một Question gắn cờ `_error=True` ngay lập tức, để UI có thể
    kết thúc batch nhanh chóng khi user hủy.
    """
    def _cancelled() -> bool:
        return cancel_event is not None and cancel_event.is_set()

    def _regenerate_fn() -> Question:
        """Hàm tái tạo câu hỏi — dùng cho cross-model khi không đồng ý."""
        if _cancelled():
            return Question(
                qtype=row.qtype, level=row.level, topic=row.topic,
                question=f"[HỦY] {row.requirement[:80]}",
                _error=True, _error_msg="Cancelled",
                _row_snapshot=row.to_dict(),
            )
        prompt2 = build_prompt(row, subject, grade)
        raw2 = ai_call(prompt2)
        q2 = parse_one_question(raw2)
        if q2:
            q2.requirement   = row.requirement
            q2._row_snapshot = row.to_dict()
        return q2 or Question(
            qtype=row.qtype, level=row.level, topic=row.topic,
            question=f"[LỖI] {row.requirement[:80]}",
            _error=True, _error_msg="Regenerate failed",
            _row_snapshot=row.to_dict(),
        )

    # Kiểm tra cancel NGAY đầu hàm — tiết kiệm cả prompt build + cache lookup
    if _cancelled():
        return Question(
            qtype=row.qtype, level=row.level, topic=row.topic,
            question=f"[HỦY] {row.requirement[:80]}",
            _error=True, _error_msg="Cancelled before start",
            _row_snapshot=row.to_dict(),
        )

    prompt = build_prompt(row, subject, grade)

    if cache_get:
        cached = cache_get(prompt)
        if cached:
            q = parse_one_question(cached)
            if q:
                q.requirement   = row.requirement
                q._row_snapshot = row.to_dict()
                return q

    last_err: Optional[Exception] = None
    for attempt in range(MAX_RETRY):
        if _cancelled():
            last_err = RuntimeError("Cancelled by user")
            break
        try:
            raw = ai_call(prompt)
            if cache_set:
                cache_set(prompt, raw)
            q = parse_one_question(raw)
            if q:
                q.requirement   = row.requirement
                q._row_snapshot = row.to_dict()

                # ── Phase 2: Cross-Model Verification ─────────────────────
                if verifier_ai is not None and CROSS_MODEL_VERIFY and not q._error:
                    try:
                        from services.cross_model import cross_model_pipeline as _cm_pipeline
                        q, meta = _cm_pipeline(
                            q, ai_call, verifier_ai,
                            regenerate_fn=_regenerate_fn,
                            max_attempts=CROSS_MODEL_MAX_ATTEMPTS,
                        )
                        # Lưu metadata verification vào _review
                        q._review = q._review or {}
                        q._review["cross_model"] = meta
                    except Exception:
                        pass  # Bỏ qua lỗi verification
                # ── End Cross-Model ────────────────────────────────────────

                return q
            last_err = ValueError(f"AI trả về không đúng định dạng (lần {attempt+1})")
        except Exception as e:
            last_err = e

    return Question(
        qtype=row.qtype, level=row.level, topic=row.topic,
        question=f"[LỖI] {row.requirement[:80]}",
        _error=True,
        _error_msg=str(last_err),
        _row_snapshot=row.to_dict(),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  GENERATE ALL — PARALLEL (V2) với progress callback
# ══════════════════════════════════════════════════════════════════════════════

def generate_all(
    rows: list[MatrixRow],
    subject: str,
    grade: str,
    semester: str,
    year: str,
    ai_call: Callable[[str], str],
    cache_get: Optional[Callable[[str], Optional[str]]] = None,
    cache_set: Optional[Callable[[str, str], None]] = None,
    progress_cb: Optional[Callable[[int, int, str], None]] = None,
    verifier_ai: Optional[Callable[[str], str]] = None,
    cancel_event: Optional[threading.Event] = None,
) -> ExamData:
    """Sinh toàn bộ đề song song với `ThreadPoolExecutor`.

    Parameters
    ----------
    cancel_event : threading.Event, optional
        Set() để dừng batch giữa chừng. Các future chưa chạy sẽ bị cancel,
        các future đang chạy sẽ trả về placeholder "[HỦY]" Question nhờ
        check ở `generate_one`. Caller (UI) thường tạo event ở __init__
        và gọi event.set() trong handler nút Cancel.
    """
    enabled = [r for r in rows if r.enabled]
    total   = len(enabled)
    results: list[tuple[int, Question]] = []
    # Lock bảo vệ append vào results — mặc dù list.append là atomic trong
    # CPython, ta vẫn giữ Lock để defensive và rõ ý định thread-safety.
    _results_lock = threading.Lock()

    import time as _time

    _call_count = [0]
    _orig_ai = ai_call
    def _staggered_ai(prompt: str) -> str:
        # Respect cancel trong stagger sleep — dùng event.wait thay time.sleep
        # để hủy nhanh thay vì phải chờ hết stagger window.
        idx = _call_count[0]
        _call_count[0] += 1
        if idx > 0:
            delay = 0.5 * (idx % MAX_WORKERS)
            if cancel_event is not None:
                if cancel_event.wait(timeout=delay):
                    raise RuntimeError("Cancelled by user")
            else:
                _time.sleep(delay)
        if cancel_event is not None and cancel_event.is_set():
            raise RuntimeError("Cancelled by user")
        return _orig_ai(prompt)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        future_map = {
            pool.submit(
                generate_one, row, subject, grade, _staggered_ai,
                cache_get, cache_set, verifier_ai, cancel_event,
            ): (idx, row)
            for idx, row in enumerate(enabled)
        }
        done = 0
        for future in as_completed(future_map):
            idx, row = future_map[future]
            # Nếu user hủy — cancel các future chưa chạy (tiết kiệm API calls)
            if cancel_event is not None and cancel_event.is_set():
                for f in future_map:
                    if not f.done():
                        f.cancel()
            try:
                q = future.result()
            except Exception as e:
                q = Question(
                    qtype=row.qtype, level=row.level, topic=row.topic,
                    question=f"[LỖI] {row.requirement[:80]}",
                    _error=True, _error_msg=str(e),
                    _row_snapshot=row.to_dict(),
                )
            with _results_lock:
                results.append((idx, q))
                done += 1
                done_snapshot = done
            if progress_cb:
                try:
                    progress_cb(done_snapshot, total, row.topic)
                except Exception:
                    # progress callback không được phá pipeline
                    pass

    results.sort(key=lambda x: x[0])
    questions = [q for _, q in results]

    # Gán ID có cấu trúc thay vì QID-hash
    assign_structured_ids(questions, grade, rows=enabled)

    return ExamData(
        exam_title=f"ĐỀ KIỂM TRA {semester.upper()} — TOÁN {grade}",
        subject=subject,
        grade=grade,
        semester=semester,
        year=year,
        time=TIME_MAP.get(grade, "90 phút"),
        questions=questions,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  REVIEW PROMPT (từ V2)
# ══════════════════════════════════════════════════════════════════════════════

_REVIEW_PROMPT = """\
Bạn là chuyên gia kiểm định đề thi Toán THPT Việt Nam.
Hãy review CÂU HỎI sau và đánh giá chất lượng.
MÔN: {subject} — LỚP: {grade}
LOẠI: {qtype_label} | MỨC ĐỘ: {level}
CHỦ ĐỀ: {topic}

NỘI DUNG:
{question_content}

Trả về đánh giá theo đúng định dạng (CHỈ trả về block này):
===REVIEW===
DIEM: <1-10>
OK: <true hoặc false>
VAN_DE: <"Không có" hoặc mô tả ngắn>
GOI_Y: <gợi ý cải thiện hoặc "Đạt yêu cầu">
===END_REVIEW=="""


def build_review_prompt(q: Question, subject: str, grade: str) -> str:
    lines = [f"Câu hỏi: {q.question}"]
    if q.qtype == "TN":
        for k, v in q.options.items():
            mark = " ← ĐÁP ÁN" if k == q.answer else ""
            lines.append(f"  {k}. {v}{mark}")
        if q.solution:
            lines.append(f"Lời giải: {q.solution}")
    elif q.qtype == "DS":
        for k, v in q.items.items():
            verdict = "Đ" if q.answers.get(k) else "S"
            lines.append(f"  ({k}) {v}  [{verdict}]")
            if q.item_solutions.get(k):
                lines.append(f"      Giải: {q.item_solutions[k]}")
    else:
        if q.answer:
            lines.append(f"Đáp án: {q.answer}")
        if q.solution:
            lines.append(f"Lời giải: {q.solution}")

    return _safe_format(
        _REVIEW_PROMPT,
        subject=subject, grade=grade,
        qtype_label=TYPE_LABELS.get(q.qtype, q.qtype),
        level=q.level, topic=q.topic,
        question_content="\n".join(lines),
    )


def parse_review(raw: str) -> dict:
    m = re.search(r"===REVIEW===(.*?)===END_REVIEW===", raw, re.DOTALL | re.IGNORECASE)
    block = m.group(1) if m else raw
    kv: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            kv[k.strip().upper()] = v.strip()
    score_str = kv.get("DIEM", "5")
    return {
        "score": int(score_str) if score_str.isdigit() else 5,
        "ok":    kv.get("OK", "true").lower() != "false",
        "issue": kv.get("VAN_DE", ""),
        "tip":   kv.get("GOI_Y", ""),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  MULTI-CODE EXAM — SHUFFLE (từ V2)
# ══════════════════════════════════════════════════════════════════════════════

def shuffle_exam(
    exam: ExamData, seed: int,
    shuffle_questions: bool = True,
    shuffle_answers: bool = True,
) -> ExamData:
    rng = random.Random(seed)
    new_exam = copy.deepcopy(exam)
    qs = new_exam.questions

    if shuffle_questions:
        # Trộn câu hỏi TRONG TỪNG PHẦN (loại), không trộn lẫn giữa các phần
        groups: dict[str, list] = {}
        order: list[str] = []
        for q in qs:
            if q.qtype not in groups:
                groups[q.qtype] = []
                order.append(q.qtype)
            groups[q.qtype].append(q)
        for qtype in order:
            rng.shuffle(groups[qtype])
        qs = []
        for qtype in order:
            qs.extend(groups[qtype])
    else:
        qs = list(qs)

    if shuffle_answers:
        for q in qs:
            if q.qtype == "TN" and q.options:
                old_opts = q.options
                old_ans  = q.answer
                keys     = list("ABCD")
                shuffled = keys[:]
                rng.shuffle(shuffled)
                new_opts: dict[str, str] = {}
                new_ans  = old_ans
                for new_k, old_k in zip(shuffled, keys):
                    new_opts[new_k] = old_opts.get(old_k, "")
                    if old_k == old_ans:
                        new_ans = new_k
                q.options = new_opts
                q.answer  = new_ans

    new_exam.questions = qs
    return new_exam


def build_answer_key(shuffled: list[tuple[str, ExamData]]) -> str:
    if not shuffled:
        return ""
    lines = ["BẢNG ĐÁP ÁN", "=" * 60]
    header = f"{'Câu':>4} | " + " | ".join(f" Mã {lbl} " for lbl, _ in shuffled)
    lines.append(header)
    lines.append("-" * len(header))
    n_tn = len([q for q in shuffled[0][1].questions if q.qtype == "TN"])
    for i in range(n_tn):
        row_cells = []
        for _, exam in shuffled:
            tn_qs = [q for q in exam.questions if q.qtype == "TN"]
            ans   = tn_qs[i].answer if i < len(tn_qs) else "?"
            row_cells.append(f"   {ans}   ")
        lines.append(f"{i+1:>4} | " + " | ".join(row_cells))
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════════════════════
#  YÊU CẦU 5 — Đa dạng nguồn tạo đề: AI / NHCH / Kết hợp
# ══════════════════════════════════════════════════════════════════════════════

def generate_from_bank(
    rows: list["MatrixRow"],
    subject: str,
    grade: str,
    bank_ratio: int = 100,
) -> list["Question"]:
    from storage.database import search_questions
    results = []
    for row in rows:
        candidates = search_questions(
            subject=subject, grade=grade,
            qtype=row.qtype, level=row.level,
            keyword=row.topic[:20] if row.topic else "",
            limit=20,
        )
        if candidates:
            import random
            q_dict = random.choice(candidates)
            try:
                q = Question.from_dict(q_dict)
                results.append(q)
            except Exception:
                results.append(None)
        else:
            results.append(None)
    return results


def generate_exam_with_source(
    rows: list["MatrixRow"],
    subject: str,
    grade: str,
    ai_call,
    mode: str = "ai_only",     # "ai_only" | "bank_only" | "mixed"
    bank_ratio: int = 50,       # % lấy từ NHCH khi mode=mixed
    progress_cb=None,
    verifier_ai: Optional[Callable] = None,
) -> list["Question"]:
    import random
    n = len(rows)
    questions: list["Question"] = [None] * n  # type: ignore

    if mode == "ai_only":
        bank_indices = set()
    elif mode == "bank_only":
        bank_indices = set(range(n))
    else:  # mixed
        k = max(1, int(n * bank_ratio / 100))
        bank_indices = set(random.sample(range(n), min(k, n)))

    for i, row in enumerate(rows):
        if i not in bank_indices:
            continue
        if progress_cb:
            progress_cb(i, n, f"[NHCH] {row.topic}")
        from storage.database import search_questions
        candidates = search_questions(
            subject=subject, grade=grade,
            qtype=row.qtype, level=row.level,
            keyword=row.topic[:20] if row.topic else "",
            limit=20,
        )
        if candidates:
            q_dict = random.choice(candidates)
            try:
                questions[i] = Question.from_dict(q_dict)
                continue
            except Exception:
                pass
        bank_indices.discard(i)

    ai_rows = [(i, rows[i]) for i in range(n) if questions[i] is None]
    if ai_rows:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(generate_one, row, subject, grade, ai_call, None, None, verifier_ai): (i, row)
                for i, row in ai_rows
            }
            for fut in as_completed(futures):
                i, row = futures[fut]
                if progress_cb:
                    progress_cb(i, n, f"[AI] {row.topic}")
                try:
                    questions[i] = fut.result()
                except Exception as e:
                    questions[i] = Question(
                        qtype=row.qtype, level=row.level, topic=row.topic,
                        question="[Lỗi tạo câu]", _error=True, _error_msg=str(e),
                        requirement=row.requirement,
                        _row_snapshot=row.to_dict(),
                    )

    final = [q for q in questions if q is not None]

    # Gán ID có cấu trúc
    assign_structured_ids(final, grade, rows=rows)

    return final