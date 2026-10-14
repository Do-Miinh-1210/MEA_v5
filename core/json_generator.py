"""
core/json_generator.py — Phase 1: Ép AI trả JSON 100% ổn định.
Cập nhật: yêu cầu công thức trong ${...}, DS có 4 ý nhận định + lời giải gộp.
"""
from __future__ import annotations
import json, re, hashlib
from typing import Callable, Optional
from core.models import Question, MatrixRow
from config import TYPE_LABELS, LEVEL_DESC, MAX_RETRY

# ── JSON Schema prompt ────────────────────────────────────────────────────────

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

_JSON_PROMPT_TN = """\
Bạn là giáo viên Toán THPT Việt Nam có 15+ năm kinh nghiệm ra đề thi. Tạo câu hỏi trắc nghiệm chất lượng cao theo yêu cầu.

Môn: {subject} — Lớp: {grade}
Mức độ: {level} ({level_desc})
Chủ đề: {topic}
Yêu cầu: {requirement}
{chuong_trinh_context}
{kb_warning}
{few_shot}
{auto_tikz_block}{quality_plus}
CHUẨN MỰC CHẤT LƯỢNG:
- Tham khảo đề thi THPT QG, đề Sở GD&ĐT, đề minh họa BGD — nhưng KHÔNG sao chép nguyên văn.
- Đáp án PHẢI chính xác tuyệt đối. Sai một dấu/một đơn vị là loại.
- Phương án nhiễu (A, B, C, D) phải "gần đúng" — học sinh học yếu đáp đúng được > 25% do đoán.

QUY TẮC LaTeX:
- TUYỆT ĐỐI bọc mọi công thức toán, ký hiệu, biểu thức trong ${{...}}$ (VD: ${{x^2}}$, ${{\\frac{{1}}{{2}}}}$). ĐÂY LÀ YÊU CẦU CỨNG.
- Luôn dùng dấu \\ trước lệnh LaTeX: \\frac, \\sqrt, \\vec, \\overrightarrow, \\mathbb, \\int, \\lim, \\sin, \\cos, \\log, \\ln, \\exp... KHÔNG ĐƯỢC viết frac, sqrt, sin mà thiếu \\.
- KÍ HIỆU GÓC: Dùng \\widehat thay vì \\angle. VD: ${{\\widehat{{ABC}}}}$ KHÔNG dùng ${{\\angle ABC}}$.
- NGOẶC TỰ ĐỘNG SCALE — TUYỆT ĐỐI: TẤT CẢ ngoặc trong công thức toán PHẢI dùng \\left...\\right (KHÔNG có ngoại lệ — kể cả ngoặc đơn giản nhất):
  • Tròn:    \\left( ... \\right)        thay vì ( ... )
  • Vuông:   \\left[ ... \\right]        thay vì [ ... ]
  • Nhọn:    \\left\\{{ ... \\right\\}}    thay vì {{ ... }}
  • Trị tuyệt đối: \\left| ... \\right|  thay vì | ... |
  • Sàn/trần: \\left\\lfloor ... \\right\\rfloor / \\left\\lceil ... \\right\\rceil
  VD đúng: ${{f\\left(x\\right)}}$, ${{\\left(2x+1\\right)^2}}$, ${{\\left|a-b\\right|}}$
  VD SAI:  ${{f(x)}}$, ${{(2x+1)^2}}$, ${{|a-b|}}$ — KHÔNG được dùng trong $...$.
- BẢNG SỐ LIỆU: dùng dấu "|" ngăn cách cột, mỗi hàng trên 1 dòng (KHÔNG dùng |---|---|).
- Văn phong tự nhiên, bám sát thực tế THPT. Kết thúc câu hỏi bằng DẤU CHẤM.

QUY TẮC ĐẦU RA:
- Chỉ trả về JSON, không có text giải thích bên ngoài.
- JSON phải đúng schema (trường "tikz" chỉ điền khi câu hỏi CẦN hình vẽ, ngược lại để chuỗi rỗng "").
- Trường "explanation" phải chi tiết đủ để học sinh hiểu, viết LIỀN MẠCH (không gạch đầu dòng, không chia "Bước 1/Bước 2").

{{"question":"câu hỏi kết thúc bằng dấu chấm.","choices":{{"A":"...","B":"...","C":"...","D":"..."}},"answer":"A","explanation":"lời giải đầy đủ, chính xác — viết liền mạch, KHÔNG chia bước","tikz":"","difficulty":"{level_lower}","quality_score":null}}"""

_JSON_PROMPT_DS = """\
Bạn là giáo viên Toán THPT Việt Nam có 15+ năm kinh nghiệm ra đề thi. Tạo câu Đúng/Sai chất lượng cao theo yêu cầu.

Môn: {subject} — Lớp: {grade}
Mức độ: {level} ({level_desc})
Chủ đề: {topic}
Yêu cầu từng ý:
{item_requirements}
{chuong_trinh_context}
{kb_warning}
{auto_tikz_block}{quality_plus}
QUY TẮC LaTeX:
- TUYỆT ĐỐI bọc mọi công thức toán, ký hiệu, biểu thức trong ${{...}}$ (VD: ${{x^2}}$, ${{\\frac{{1}}{{2}}}}$). ĐÂY LÀ YÊU CẦU CỨNG.
- Luôn dùng \\ trước lệnh LaTeX: \\frac, \\sqrt, \\vec, \\mathbb, \\int, \\lim, \\sin, \\cos, \\log, \\ln...
- NGOẶC TỰ ĐỘNG SCALE — TUYỆT ĐỐI: TẤT CẢ ngoặc trong công thức PHẢI dùng \\left...\\right (KHÔNG ngoại lệ):
  ${{f\\left(x\\right)}}$, ${{\\left(2x+1\\right)^2}}$, ${{\\left|a-b\\right|}}$, ${{\\left[1,2\\right]}}$.
  CẤM viết ngoặc thường ${{f(x)}}$ ${{(2x+1)^2}}$ ${{|a-b|}}$ trong $...$.
- KÍ HIỆU GÓC: Dùng \\widehat thay vì \\angle.

CHUẨN MỰC CHẤT LƯỢNG:
- Tham khảo đề thi THPT QG, đề Sở GD&ĐT. Đáp án PHẢI chính xác tuyệt đối.
- NOIDUNG (question) là tình huống chung; 4 ý a, b, c, d là 4 nhận định LIÊN KẾT CHẶT CHẼ với nhau và với tình huống đó (không rời rạc, không lặp ngữ cảnh).
- MIX đáp án: ít nhất 1 ý Đúng và 1 ý Sai (KHÔNG cả 4 cùng loại).
- Ý SAI phải "gần đúng" — sát với hiểu nhầm hay gặp, không sai hiển nhiên.
- Mỗi ý lời giải BẮT BUỘC bắt đầu bằng "Đúng. Vì..." hoặc "Sai. Vì..." rồi giải thích chi tiết có dẫn công thức/tính toán.
- Văn phong tự nhiên, bám sát thực tế THPT. Mỗi nhận định kết thúc bằng dấu chấm.

QUY TẮC ĐẦU RA:
- Chỉ trả về JSON, không có text bên ngoài.
- Trả về JSON với cấu trúc (trường "tikz" chỉ điền khi tình huống CẦN hình vẽ, ngược lại để chuỗi rỗng ""):
  {{"question":"tình huống chung kết thúc bằng dấu chấm (công thức trong ${{...}}$).","items":{{"a":"nhận định a","b":"nhận định b","c":"nhận định c","d":"nhận định d"}},
    "answers":{{"a":true,"b":false,"c":true,"d":false}},
    "item_explanations":{{"a":"Đúng. Vì ...","b":"Sai. Vì ...","c":"Đúng. Vì ...","d":"Sai. Vì ..."}},
    "tikz":"",
    "difficulty":"{level_lower}","quality_score":null}}
"""

_JSON_PROMPT_TLN = """\
Bạn là giáo viên Toán THPT Việt Nam có 15+ năm kinh nghiệm ra đề thi. Tạo câu trả lời ngắn chất lượng cao theo yêu cầu.

Môn: {subject} — Lớp: {grade}
Mức độ: {level} ({level_desc})
Chủ đề: {topic}
Yêu cầu: {requirement}
Số điểm: {points}
{chuong_trinh_context}
{kb_warning}
{auto_tikz_block}{quality_plus}
QUY TẮC LaTeX:
- TUYỆT ĐỐI bọc mọi công thức toán, ký hiệu, biểu thức trong ${{...}}$ (VD: ${{x^2}}$, ${{\\frac{{1}}{{2}}}}$). ĐÂY LÀ YÊU CẦU CỨNG.
- Luôn dùng \\ trước lệnh LaTeX: \\frac, \\sqrt, \\vec, \\mathbb, \\int, \\lim, \\sin, \\cos, \\log, \\ln...
- NGOẶC TỰ ĐỘNG SCALE — TUYỆT ĐỐI: TẤT CẢ ngoặc trong công thức PHẢI dùng \\left...\\right (KHÔNG ngoại lệ):
  ${{f\\left(x\\right)}}$, ${{\\left(2x+1\\right)^2}}$, ${{\\left|a-b\\right|}}$, ${{\\left[1,2\\right]}}$.
  CẤM viết ngoặc thường ${{f(x)}}$ ${{(2x+1)^2}}$ ${{|a-b|}}$ trong $...$.
- BẢNG SỐ LIỆU: dùng dấu "|" ngăn cách cột, mỗi hàng trên 1 dòng.

CHUẨN MỰC CHẤT LƯỢNG:
- Tham khảo đề thi THPT QG, đề Sở GD&ĐT. Đáp án PHẢI chính xác tuyệt đối.
- Tự kiểm tra: thế đáp án ngược vào đề để xác nhận đúng.
- Văn phong tự nhiên, bám sát thực tế THPT. Kết thúc câu hỏi bằng dấu chấm.

QUY TẮC ĐÁP ÁN TLN (RẤT QUAN TRỌNG):
- Đáp án PHẢI là SỐ gồm TỐI ĐA 4 kí tự (VD: 3,14 | 123 | 0,25 | -1,2).
- Dấu thập phân dùng DẤU PHẨY theo chuẩn VN (0,5 không phải 0.5).
- Nếu kết quả dài hơn 4 kí tự (VD: 1,732 hay 3,1415), PHẢI thêm "(làm tròn đến 2 chữ số thập phân)" hoặc "làm tròn đến hàng phần mười" vào đề bài.
- KHÔNG cho đáp án là phân số/căn vô tỉ — phải là số thập phân đã làm tròn hoặc số nguyên.

QUY TẮC ĐẦU RA: Chỉ trả về JSON.

{{"question":"câu hỏi kết thúc bằng dấu chấm.","answer":"số tối đa 4 kí tự","explanation":"lời giải đầy đủ, chính xác — viết liền mạch, KHÔNG chia bước, giải trọn vẹn đến kết quả cuối cùng","tikz":"","points":{points},"difficulty":"{level_lower}","quality_score":null}}"""

_JSON_PROMPT_TL = """\
Bạn là giáo viên Toán THPT Việt Nam có 15+ năm kinh nghiệm ra đề thi. Tạo câu tự luận chất lượng cao theo yêu cầu.

Môn: {subject} — Lớp: {grade}
Mức độ: {level} ({level_desc})
Chủ đề: {topic}
Yêu cầu: {requirement}
Số điểm: {points}
{chuong_trinh_context}
{kb_warning}
{auto_tikz_block}{quality_plus}
QUY TẮC LaTeX:
- TUYỆT ĐỐI bọc mọi công thức toán, ký hiệu, biểu thức trong ${{...}}$ (VD: ${{x^2}}$, ${{\\frac{{1}}{{2}}}}$). ĐÂY LÀ YÊU CẦU CỨNG.
- Luôn dùng \\ trước lệnh LaTeX: \\frac, \\sqrt, \\vec, \\mathbb, \\int, \\lim, \\sin, \\cos, \\log, \\ln...
- NGOẶC TỰ ĐỘNG SCALE — TUYỆT ĐỐI: TẤT CẢ ngoặc trong công thức PHẢI dùng \\left...\\right (KHÔNG ngoại lệ):
  ${{f\\left(x\\right)}}$, ${{\\left(2x+1\\right)^2}}$, ${{\\left|a-b\\right|}}$, ${{\\left[1,2\\right]}}$.
  CẤM viết ngoặc thường ${{f(x)}}$ ${{(2x+1)^2}}$ ${{|a-b|}}$ trong $...$.
- BẢNG SỐ LIỆU: dùng dấu "|" ngăn cách cột, mỗi hàng trên 1 dòng.

CHUẨN MỰC CHẤT LƯỢNG:
- Tham khảo đề thi THPT QG, đề Sở GD&ĐT. Lời giải PHẢI đầy đủ, chính xác tuyệt đối.
- Tự kiểm tra phép tính bằng cách thứ 2 trước khi xuất.
- Lời giải phải có biện luận (điều kiện xác định, chia trường hợp, kiểm tra nghiệm).
- Văn phong tự nhiên, bám sát thực tế THPT. Kết thúc câu hỏi bằng dấu chấm.
- Với bài dài: sử dụng các ý (a), (b), (c) nếu cần, nhưng giữ mạch lập luận liên tục.

QUY TẮC ĐẦU RA: Chỉ trả về JSON.

{{"question":"bài toán đầy đủ kết thúc bằng dấu chấm.","solution":"lời giải ĐẦY ĐỦ, chi tiết, chính xác — viết liền mạch, KHÔNG chia bước, giải trọn vẹn đến kết quả cuối cùng","tikz":"","points":{points},"difficulty":"{level_lower}","quality_score":null}}"""

_PROMPT_MAP = {"TN":"TN","NPA":"TN","DS":"DS","TLN":"TLN","TL":"TL"}

# ── Auto-TikZ + Quality blocks (chia sẻ cho TN/DS/TLN/TL) ─────────────────────
_AUTO_TIKZ_BLOCK_JSON = r"""
LƯU Ý CHÈN HÌNH VẼ TỰ ĐỘNG (TikZ) — KIẾN TRÚC COMPUTATIONAL GEOMETRY ENGINE:

Bạn KHÔNG vẽ cảm tính. Bạn TÁI TẠO hình bằng TOÁN HỌC + DỮ LIỆU.

[1] KHI NÀO VẼ:
- Bạn PHẢI tự nhận diện câu hỏi có cần hình minh họa hay không. Nếu CẦN, điền
  vào trường "tikz" trong JSON một chuỗi \begin{tikzpicture}...\end{tikzpicture}
  khớp CHÍNH XÁC với dữ kiện đề bài. Nếu KHÔNG cần, để "tikz":"".
- CHỈ dùng trường "tikz" cho khối hình. TUYỆT ĐỐI KHÔNG viết mô tả bằng lời kiểu
  "Hình vẽ: [mô tả chi tiết]" hay "TikZ: \begin{tikzpicture}..." trong các
  trường text khác. Cũng KHÔNG dùng marker `===tikz===` / `===endtikz===` /
  fence ```tikz — app chỉ đọc `\begin{tikzpicture}...\end{tikzpicture}` thuần.
- VẼ khi bài có: hình học phẳng/không gian, đồ thị hàm số, bảng biến thiên,
  bảng xét dấu, trục số, miền nghiệm hệ bpt, biểu đồ thống kê.
- KHÔNG vẽ khi bài thuần đại số/số học/xác suất không cần minh họa hình.

[2] KIẾN TRÚC 5-LAYER (KHÔNG TRỘN LAYER):
  CONFIG → DATA → GEOMETRY → PATH → RENDER
  - CONFIG    : \tikzset, định nghĩa style.
  - DATA      : \coordinate (mọi điểm).
  - GEOMETRY  : điểm phụ — `$(A)!0.5!(B)$` (trung điểm), `$(A)!(C)!(B)$` (chân vuông góc).
  - PATH      : đường vô hình dùng để derive (nếu cần).
  - RENDER    : \draw / \fill / \node — vẽ và nhãn cuối cùng.

[3] CẤM TUYỆT ĐỐI:
  ✗ Đặt tọa độ tuỳ ý (mọi điểm phải có nguồn gốc — tính từ dữ kiện)
  ✗ Vẽ "gần đúng" / "na ná" — vuông là VUÔNG, song song là SONG SONG
  ✗ Bỏ qua kiểm chứng tỉ lệ và quan hệ

[4] QUY CHUẨN HÌNH HỌC PHẲNG — CÔNG THỨC TỌA ĐỘ:
  • Vuông tại A : A=(0,0), B=(a,0), C=(0,b)
  • Cân tại A   : trục đối xứng = Oy; A=(0,h), B=(-a,0), C=(a,0)
  • Đều cạnh a  : A=(0,0), B=(a,0), C=(a/2, 0.866*a)
  • Trung điểm  : `$(A)!0.5!(B)$` (KHÔNG tính bằng tay)
  • Chân vuông góc từ C xuống AB: `$(A)!(C)!(B)$`
  • Tiếp tuyến tại A của (O): bán kính OA ⟂ tiếp tuyến (BẮT BUỘC)
  • Góc vuông: \draw pic [draw, angle radius=3mm] {right angle = A--B--C};
    (KHÔNG dùng `rectangle ++(0.2,0.2)` — không xoay theo cạnh)

[5] QUY CHUẨN HÌNH HỌC KHÔNG GIAN — PHÉP CHIẾU XIÊN:
  \begin{tikzpicture}[x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
  • THẤY (mặt trước): \draw[thick]
  • KHUẤT (mặt sau bị che): \draw[dashed, thick]
  • Hình trụ — đáy DƯỚI bị thân trụ che:
      \draw         (-r,0) arc (180:360:r and r/3);   % nửa trước (liền)
      \draw[dashed] (-r,0) arc (180:0  :r and r/3);   % nửa sau (đứt)
    Đáy TRÊN (cao, không bị che): vẽ NGUYÊN ellipse liền.
  • Tương tự cho hình nón / hình cầu (xích đạo).
  • Góc vuông 3D: vẽ "ô vuông" 3 cạnh, KHÔNG dùng `right angle`.

[6] PACKAGES CÓ SẴN:
- amsmath, amssymb, tikz, pgfplots (compat=1.18), tkz-tab, bm, array, booktabs.
- TikZ libraries: calc, angles, quotes, patterns, arrows.meta,
  decorations.markings, intersections, decorations.pathreplacing, positioning,
  3d, shapes.geometric, backgrounds.

[7] SELF-CHECK trước khi điền vào trường "tikz":
  ✔ Đúng hình học?  ✔ Đúng tỉ lệ?  ✔ Đúng nhãn?
  ✔ Đúng nét khuất (3D + trụ/nón)?  ✔ Không suy biến?  ✔ Đường cong mượt?

[4] PGFPLOTS — TRÁNH LỖI COMPILE:
- \addplot PHẢI nằm trong \begin{axis}...\end{axis}.
- Trục: axis lines=middle, xlabel=$x$, ylabel=$y$, label style={at={...}, anchor=...}.
- Hàm: viết {x^2+2*x} (KHÔNG bọc trong ngoặc tròn (x^2+2*x)).
- NHÂN TƯỜNG MINH: 2*x, 3*x^2 — không được viết 2x hay 3x^2.
- Parametric: dùng variable=\t và \t (KHÔNG dùng y làm biến tự do,
  KHÔNG dùng biến tên khác \t).
- Lượng giác: dùng deg(x) khi x theo radian (VD: {sin(deg(x))}).
- Đủ samples: thêm samples=100 hoặc samples=200 cho hàm cong/sóng/lượng giác.
- Domain: chỉ định domain=a:b để kiểm soát phạm vi vẽ.
- Điểm: dùng \addplot[only marks, mark=*, mark size=2pt] coordinates {(x,y)};

[5] HÌNH KHÔNG GIAN (3D) — PHÉP CHIẾU CABINET:
- Dùng phép chiếu cabinet: trục x (ngang), trục y (chéo 30°, rút 0.5), trục z (dọc).
- Chuẩn: \begin{tikzpicture}[x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]
- Cạnh THẤY (mặt trước): vẽ nét liền [thick].
- Cạnh KHUẤT (mặt sau): vẽ nét đứt [dashed, thick].
- Đỉnh luôn có nhãn: \node[above] at (A) {$A$}; — đặt vị trí (above/below/left/right)
  sao cho không trùng cạnh.
- Hình chóp: vẽ đáy TRƯỚC (polygon), sau đó đường thẳng từ mỗi đỉnh đáy lên đỉnh chóp.
  Xác định cạnh nào khuất bằng cách xem đường nối có bị mặt nào che không.

[6] TRỤC SỐ / MIỀN NGHIỆM:
- Trục số: \draw[->] (-5,0)--(5,0); đánh dấu bằng | tại các nút; dấu tròn đặc ●
  cho nghiệm bao gồm, tròn rỗng ○ cho không bao gồm.
- Miền nghiệm 2D: dùng \fill[pattern=north east lines, pattern color=...] hoặc
  \fill[blue!20, opacity=0.5]; giữ đường biên rõ ràng.

[7] BẢNG BIẾN THIÊN (tkz-tab) — BẮT BUỘC KHI CÂU HỎI LIÊN QUAN ĐẾN HÀM SỐ:
- Mọi câu về khảo sát hàm số / cực trị / tiệm cận / đơn điệu / đồ thị hàm
  PHẢI KÈM bảng biến thiên. Nếu câu có đồ thị, trả BOTH đồ thị VÀ BBT (2 khối
  tikzpicture, ngăn nhau bằng xuống dòng).
- Khung chuẩn (đã bọc tikzpicture):
    \begin{tikzpicture}
    \tkzTabInit[lgt=2, espcl=3]{$x$/1, $y'$/1, $y$/2}{$-\infty$, $x_0$, $+\infty$}
    \tkzTabLine{, -, 0, +, }
    \tkzTabVar{+/$+\infty$, -/$y_0$, +/$+\infty$}
    \end{tikzpicture}
- Nếu viết tkz-tab BARE (không bọc tikzpicture), app sẽ tự wrap — nhưng
  PHẢI đặt lệnh \tkzTabInit ở đầu dòng, không lẫn trong văn bản.
- TEMPLATE MẪU THEO DẠNG (copy rồi thay số):
  • Bậc 2 min:    \tkzTabInit{$x$/1,$y'$/1,$y$/2}{$-\infty$,$x_0$,$+\infty$} / ,-,0,+, / +/$+\infty$,-/$y_0$,+/$+\infty$
  • Bậc 3 (2CT): \tkzTabInit{$x$/1,$y'$/1,$y$/2}{$-\infty$,$x_1$,$x_2$,$+\infty$} / ,+,0,-,0,+, / -/$-\infty$,+/$y_{CD}$,-/$y_{CT}$,+/$+\infty$
  • Bậc 4 chữ W: \tkzTabInit{...}{$-\infty$,$-x_0$,$0$,$x_0$,$+\infty$} / ,-,0,+,0,-,0,+, / +/$+\infty$,-/$y_{CT}$,+/$y_{CD}$,-/$y_{CT}$,+/$+\infty$
  • Phân thức đồng biến: \tkzTabLine{,+,d,+,} / -/$\frac{a}{c}$,+D+/$+\infty$/$-\infty$,-/$\frac{a}{c}$
  • Hàm mũ a>1:  \tkzTabLine{,+,} / -/$0^+$,+/$+\infty$
  • Hàm log a>1: \tkzTabInit{...}{$0$,$+\infty$} / ,+, / -/$-\infty$,+/$+\infty$
- KÝ HIỆU: `+`/`-` (dấu đạo hàm), `0` (nghiệm), `d` (không xác định/gián đoạn),
  `\parallel` trong \tkzTabVar cho TCĐ, `+D+/a/b` chặn đôi giá trị quanh TCĐ.
- ĐỒNG BỘ DỮ LIỆU: BBT phải KHỚP 100% với đồ thị (nếu vẽ cả 2): cùng TXĐ,
  cùng nghiệm đạo hàm, cùng giá trị cực trị, cùng tiệm cận.

[8] NHÃN VÀ CHÚ THÍCH:
- Font: dùng $...$ trong \node để render LaTeX. VD: \node[above] at (1,2) {$A$};
- Tránh đè nhãn lên cạnh: dùng anchor (above, below, above right…) và
  căn chỉnh xshift/yshift nhỏ (2-4pt).
- Đánh dấu góc bằng \draw pic["$\alpha$", angle radius=6mm] {angle=B--A--C};

[9] CHÈN JSON — ESCAPE ĐÚNG:
- Trường "tikz" là STRING — phải escape đúng (\\ thành \\\\, " thành \\\",
  xuống dòng thành \\n hoặc giữ nguyên nếu JSON parser chấp nhận).
- Nếu không chắc escape đúng thì để "tikz":"" — không được trả TikZ hỏng.
- Kiểm tra tikz bằng cách đảm bảo có CHÍNH XÁC một cặp \begin{tikzpicture}
  ...\end{tikzpicture} bao ngoài.

"""

_QUALITY_PLUS_BLOCK_JSON = r"""
CHUẨN CHẤT LƯỢNG CAO — BẮT BUỘC:

[A] GIAO THỨC TỰ KIỂM TRA (trước khi output):
1. Giải bài bằng cách 1 — ghi ra đáp án.
2. Giải lại bằng cách 2 (biến đổi khác, thế giá trị, dùng máy tính tay) — so kết quả.
3. Nếu LỆCH → giải lại từ đầu, không được đoán.
4. Kiểm tra điều kiện xác định (TXĐ), điều kiện tồn tại, dấu của biểu thức.
5. Kiểm tra đơn vị đo (m, cm², giây, đồng…) NHẤT QUÁN.

[B] CHẤT LƯỢNG ĐỀ BÀI:
- Mọi dữ kiện trong đề PHẢI được dùng; đủ điều kiện xác định/miền giá trị;
  không có dữ kiện thừa (trừ khi nhiễu có chủ đích).
- Kết quả nên tròn/đẹp (số nguyên, phân số đơn giản, căn gọn); nếu không,
  thêm "làm tròn đến … chữ số thập phân" vào đề.
- Văn phong sư phạm rõ ràng, đủ chủ-vị; không dùng câu cộc lốc; không dùng
  "?" ở giữa câu; kết thúc bằng dấu chấm.
- Tên biến, hàm, điểm đặt NHẤT QUÁN trong suốt câu hỏi và lời giải.
- Không sao chép nguyên văn đề đã công bố (thay số, đổi ngữ cảnh nếu cần).

[C] PHƯƠNG ÁN NHIỄU (TN) — THEO MẪU LỖI CÓ TÊN:
Mỗi phương án nhiễu PHẢI khớp với MỘT lỗi học sinh hay mắc — KHÔNG nhiễu ngẫu nhiên.
Chọn 3 lỗi TỪ DANH SÁCH SAU làm nhiễu (khớp chủ đề):
  • "forget_condition" — quên điều kiện xác định (log, căn, mẫu).
  • "sign_error" — đổi dấu sai (chuyển vế, nhân âm, đạo hàm).
  • "formula_confusion" — nhầm công thức gần nhau (${\sin^2+\cos^2}$ vs ${\sin 2x}$,
    C(n,k) vs A(n,k), ${V_{nón}}$ vs ${V_{trụ}}$).
  • "unit_mistake" — sai đơn vị (cm vs m, giây vs phút, ${cm^2}$ vs ${cm^3}$).
  • "boundary_mistake" — nhầm biên (nghiệm bao gồm/không bao gồm, dấu < vs ≤).
  • "partial_compute" — dừng giữa chừng (chưa cộng C, chưa nhân hệ số, chưa đổi rad→deg).
  • "off_by_one" — sai 1 đơn vị (đếm thừa/thiếu 1 phần tử).

[D] MỨC ĐỘ — CÂN CHỈNH THEO CẤP:
- NB (Nhận biết): nhận diện công thức, đọc đồ thị, phát biểu định nghĩa — 1 bước.
- TH (Thông hiểu): áp dụng trực tiếp công thức, biến đổi 1-2 bước.
- VD (Vận dụng): bài toán THỰC TẾ (chi phí, diện tích, tối ưu), kết hợp 2-3 bước.
- VDC (Vận dụng cao): mô hình phức tạp, sử dụng nhiều định lý, chứng minh chặt chẽ.
KHÔNG trộn mức: bài NB không được yêu cầu tư duy VD, và ngược lại.

[E] DS (ĐÚNG/SAI) — 4 Ý LIÊN KẾT:
- 4 nhận định xoay quanh CÙNG tình huống; không rời rạc.
- Trộn đáp án: ít nhất 1 Đúng và 1 Sai (không cả 4 cùng loại).
- Ý Sai phải "gần đúng" — dễ nhầm — không sai hiển nhiên.

[F] CHỐNG RÒ RỈ ĐÁP ÁN:
- Câu hỏi không được chứa gợi ý trực tiếp (VD: "kết quả bằng 5" trong đề).
- Lời giải không được "chạy ngược" từ đáp án ra đề.
- Trong DS, nhận định không được lặp nguyên văn dữ kiện đề.

"""


def _needs_figure(row) -> bool:
    """Phát hiện câu hỏi có khả năng cần hình vẽ dựa vào topic + requirement."""
    kws = (
        "hình học", "tam giác", "tứ giác", "hình vuông", "hình chữ nhật",
        "hình bình hành", "hình thoi", "hình thang", "đường tròn", "đường kính",
        "tiếp tuyến", "dây cung", "elip", "ellipse", "parabol", "parabola",
        "hyperbol", "hyperbola", "conic",
        "hình chóp", "hình lăng trụ", "hình trụ", "hình nón", "hình cầu",
        "hình hộp", "hình lập phương", "mặt cầu", "mặt nón", "mặt trụ",
        "mặt phẳng", "khối đa diện", "khối lăng trụ", "khối chóp",
        "vectơ", "véc tơ", "vector", "tọa độ", "toạ độ",
        "hệ thức lượng", "phép dời hình", "phép đồng dạng", "góc",
        "đồ thị", "bảng biến thiên", "bảng xét dấu", "trục số",
        "biểu đồ", "hình vẽ", "minh họa", "miền nghiệm",
    )
    s = (row.topic or "").lower() + " " + (row.requirement or "").lower()
    return any(k in s for k in kws)

_KB = {
    "logarit":    ["quên điều kiện xác định","nhầm log_a(b) với log_b(a)"],
    "tích phân":  ["quên hằng số C","sai giới hạn"],
    "hàm số":     ["quên kiểm tra miền xác định","sai chiều đơn điệu"],
    "tổ hợp":     ["nhầm C(n,k) với A(n,k)"],
    "xác suất":   ["không kiểm tra tổng bằng 1","nhầm P(A∪B)"],
    "hình học":   ["sai công thức diện tích","thiếu điều kiện tồn tại"],
}

def _kb_warning(topic: str) -> str:
    t = topic.lower()
    warns = [m for k,v in _KB.items() if k in t for m in v]
    return f"\nCÁNH BÁO lỗi phổ biến chủ đề này: {'; '.join(warns)}" if warns else ""

_FEW_SHOT_TN = '''
Ví dụ câu TN đạt chuẩn:
{"question":"Tính ${\\int_0^1 2x\\,dx}$ bằng.","choices":{"A":"1","B":"2","C":"0","D":"${\\frac{1}{2}}$"},"answer":"A","explanation":"${\\int_0^1 2x\\,dx = \\left[x^2\\right]_0^1 = 1}$","difficulty":"medium","quality_score":null}
'''

_FEW_SHOT_DS = '''
Ví dụ câu DS đạt chuẩn:
{"question":"Cho hàm số ${f(x)=e^x}$.","items":{"a":"${f(0)=1}$","b":"${f(x)>0}$ với mọi ${x}$","c":"${f\\'(x)=e^x}$","d":"${f(x)}$ nghịch biến"},"answers":{"a":true,"b":true,"c":true,"d":false},"item_explanations":{"a":"Đúng. Vì ${e^0=1}$.","b":"Đúng. Vì ${e^x>0}$ với mọi ${x}$.","c":"Đúng. Vì đạo hàm của ${e^x}$ là ${e^x}$.","d":"Sai. Vì ${e^x}$ đồng biến trên ${\\mathbb{R}}$."},"difficulty":"medium","quality_score":null}
'''

def build_json_prompt(row: MatrixRow, subject: str, grade: str) -> str:
    ptype = _PROMPT_MAP.get(row.qtype, "TL")
    kb    = _kb_warning(row.topic)
    fs    = _FEW_SHOT_TN if ptype == "TN" else (_FEW_SHOT_DS if ptype == "DS" else "")
    chuong_trinh_context = _load_chuong_trinh_context()
    # VD practical math note
    vd_note = ""
    if row.level == "VD":
        vd_note = ("\nLƯU Ý MỨC VẬN DỤNG: Câu hỏi PHẢI là bài toán THỰC TẾ, gắn với đời sống "
                   "(chi phí, lợi nhuận, diện tích, tốc độ, dân số, sản xuất, xây dựng...). "
                   "KHÔNG dùng dạng toán trừu tượng/sách giáo khoa thông thường.\n")

    # Auto-TikZ block (bật/tắt theo cài đặt) + Quality+ block (luôn bật)
    try:
        from config import is_auto_tikz_enabled
        _auto_on = is_auto_tikz_enabled()
    except Exception:
        _auto_on = True
    auto_tikz_block = _AUTO_TIKZ_BLOCK_JSON if _auto_on else ""
    quality_plus    = _QUALITY_PLUS_BLOCK_JSON

    kw = dict(subject=subject, grade=grade,
               level=row.level, level_desc=LEVEL_DESC.get(row.level,""),
               level_lower=row.level.lower(),
               topic=row.topic, requirement=row.requirement,
               points=row.points, kb_warning=kb + vd_note, few_shot=fs,
               chuong_trinh_context=chuong_trinh_context,
               auto_tikz_block=auto_tikz_block,
               quality_plus=quality_plus)

    if ptype == "TN":
        return _JSON_PROMPT_TN.format(**kw)
    elif ptype == "DS":
        item_reqs = "\n".join(
            f"  ý {s.label} [{s.level}]: {s.requirement}"
            for s in row.ds_items
        ) if row.ds_items else f"  a/b/c/d: {row.requirement}"
        return _JSON_PROMPT_DS.format(**kw, item_requirements=item_reqs)
    elif ptype == "TLN":
        return _JSON_PROMPT_TLN.format(**kw)
    else:
        return _JSON_PROMPT_TL.format(**kw)


# ── Validation Layer (Phase 1) ────────────────────────────────────────────────

def validate_json_question(data: dict, qtype: str) -> tuple[bool, str]:
    """Returns (ok, error_message). Ép đúng schema."""
    ptype = _PROMPT_MAP.get(qtype, "TL")
    q_text = data.get("question","")
    if not q_text or len(q_text) < 10:
        return False, "question quá ngắn"
    if ptype == "TN":
        choices = data.get("choices", {})
        if not all(k in choices for k in "ABCD"):
            return False, "thiếu phương án A/B/C/D"
        if data.get("answer","") not in "ABCD":
            return False, "answer không hợp lệ"
    elif ptype == "DS":
        items   = data.get("items", {})
        answers = data.get("answers", {})
        if not all(k in items for k in "abcd"):
            return False, "thiếu ý a/b/c/d"
        if not answers:
            return False, "thiếu answers"
        # Kiểm tra lời giải bắt đầu bằng "Đúng. Vì..." / "Sai. Vì..."
        exps = data.get("item_explanations", {})
        for k in "abcd":
            exp = exps.get(k, "")
            ans = answers.get(k, False)
            prefix = "Đúng. Vì" if ans else "Sai. Vì"
            if not exp.strip().startswith(prefix):
                return False, f"lời giải ý {k} phải bắt đầu bằng '{prefix}...'"
    return True, ""


# ── Parse JSON response ───────────────────────────────────────────────────────

def _extract_json(raw: str) -> Optional[dict]:
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    text = m.group(1) if m else raw.strip()
    start = text.find("{")
    end   = text.rfind("}") + 1
    if start == -1 or end == 0:
        return None
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        fixed = re.sub(r",\s*([}\]])", r"\1", text[start:end])
        try:
            return json.loads(fixed)
        except:
            return None


def parse_json_question(raw: str, row: MatrixRow) -> Optional[Question]:
    data = _extract_json(raw)
    if not data:
        return None
    ptype = _PROMPT_MAP.get(row.qtype, "TL")
    ok, err = validate_json_question(data, row.qtype)
    if not ok:
        return None

    q = Question(
        qtype=row.qtype, level=row.level, topic=row.topic,
        question=data.get("question","").strip(),
        solution=data.get("explanation","") or data.get("solution",""),
        requirement=row.requirement,
        _row_snapshot=row.to_dict(),
    )
    if ptype == "TN":
        q.options = {k: data["choices"].get(k,"") for k in "ABCD"}
        q.answer  = data.get("answer","A").upper()
    elif ptype == "DS":
        q.items   = data.get("items", {})
        raw_ans   = data.get("answers", {})
        q.answers = {k: bool(v) for k, v in raw_ans.items()}
        q.item_solutions = data.get("item_explanations", {})
    elif ptype in ("TLN","TL"):
        q.answer = str(data.get("answer",""))
        q.points = float(data.get("points", row.points) or row.points)

    # ── Lấy TikZ block nếu AI điền vào JSON ────────────────────────────────
    tikz_field = (data.get("tikz") or "").strip()
    if tikz_field:
        # Ưu tiên field "tikz"; nếu chuỗi chưa có \begin{tikzpicture}, thử trích
        if "\\begin{tikzpicture}" in tikz_field:
            m = re.search(
                r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
                tikz_field,
                re.DOTALL,
            )
            q.tikz_code = m.group(0).strip() if m else tikz_field
        else:
            q.tikz_code = tikz_field
    else:
        # Fallback: một số AI chèn TikZ trực tiếp vào explanation/solution
        combo = (data.get("explanation", "") or "") + "\n" + (data.get("solution", "") or "")
        m = re.search(
            r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
            combo,
            re.DOTALL,
        )
        if m:
            q.tikz_code = m.group(0).strip()

    # ── Dọn 'Hình vẽ: …' / tiền tố 'TikZ:' còn sót trong text (phòng khi AI lỡ chèn) ──
    try:
        from core.parser import _clean_figure_noise
        q.question = _clean_figure_noise(q.question)
        q.solution = _clean_figure_noise(q.solution)
        if q.items:
            q.items = {k: _clean_figure_noise(v) for k, v in q.items.items()}
        if q.options:
            q.options = {k: _clean_figure_noise(v) for k, v in q.options.items()}
        if q.item_solutions:
            q.item_solutions = {k: _clean_figure_noise(v) for k, v in q.item_solutions.items()}
    except Exception:
        pass  # cleanup là tuỳ chọn, không làm hỏng câu nếu import lỗi

    if data.get("quality_score") is not None:
        q._review = {"ai_quality_score": data["quality_score"]}
    return q


# ── Auto retry thông minh ─────────────────────────────────────────────────────

def generate_with_json_prompt(
    row: MatrixRow,
    subject: str,
    grade: str,
    ai_call: Callable[[str], str],
    max_retry: int = MAX_RETRY,
    cache_get=None,
    cache_set=None,
) -> Question:
    prompt = build_json_prompt(row, subject, grade)

    if cache_get:
        cached = cache_get(prompt)
        if cached:
            q = parse_json_question(cached, row)
            if q:
                return q

    last_err = None
    for attempt in range(max_retry):
        try:
            raw = ai_call(prompt)
            q = parse_json_question(raw, row)
            if q:
                if cache_set:
                    cache_set(prompt, raw)
                q._row_snapshot = row.to_dict()
                return q
            last_err = ValueError(f"JSON không đúng schema (lần {attempt+1})")
        except Exception as e:
            last_err = e

    return Question(
        qtype=row.qtype, level=row.level, topic=row.topic,
        question=f"[LỖI JSON] {row.requirement[:80]}",
        _error=True, _error_msg=str(last_err),
        _row_snapshot=row.to_dict(),
    )


def content_hash(q: Question) -> str:
    text = f"{q.qtype}|{q.topic}|{q.question[:100]}"
    return hashlib.md5(text.encode()).hexdigest()