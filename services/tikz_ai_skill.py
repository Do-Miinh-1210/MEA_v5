"""
services/tikz_ai_skill.py — Module tích hợp kỹ năng vẽ hình TikZ AI (Phong cách Thầy Đỗ Minh - DoMinhMath).

Tích hợp toàn diện các quy tắc từ `tikz_ai_skill/`:
1. System Prompt & Draw/Edit Prompts chuẩn Thầy Đỗ Minh (10 Invariants, 5-Step Workflow).
2. Optimization Prompt: Tối ưu hóa code TikZ 5 lớp (Layering Rules, Parameterization, Dead-code Elimination).
3. LaTeX Builder: Tự động phân tích code TikZ, phát hiện packages/libraries và tạo standalone LaTeX (.tex).
4. Code Extractor: Trích xuất code TikZ thuần túy từ phản hồi của AI hoặc tài liệu LaTeX hoàn chỉnh.
5. Skill Docs & Code Examples Loader.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_log = logging.getLogger(__name__)


# ── ĐƯỜNG DẪN THƯ MỤC SKILL ──────────────────────────────────────────────────

def _get_skill_dir() -> Path:
    """Trả về đường dẫn tới thư mục `tikz_ai_skill` nếu tồn tại."""
    base_dir = Path(__file__).resolve().parent.parent
    skill_dir = base_dir / "tikz_ai_skill"
    return skill_dir


def _read_skill_file(filename: str) -> str:
    """Đọc nội dung file markdown trong thư mục tikz_ai_skill (nếu có)."""
    skill_dir = _get_skill_dir()
    target = skill_dir / filename
    if target.is_file():
        try:
            return target.read_text(encoding="utf-8")
        except Exception as exc:
            _log.warning("Không thể đọc file skill %s: %s", filename, exc)
    return ""


# ── NỘI DUNG NHÚNG DỰ PHÒNG (FALLBACK KHI CHẠY STANDALONE EXE) ───────────────

_EMBEDDED_SYSTEM_PROMPT = r"""Bạn là Trợ lý AI chuyên gia vẽ hình TikZ/LaTeX Toán học theo đúng chuẩn và phong cách của Thầy Đỗ Minh (DoMinhMath). Nhiệm vụ: tạo mã TikZ chuẩn xác, đẹp mắt, tuân thủ 100% các quy tắc phong cách sau. Đọc toàn bộ quy tắc trước khi viết bất kỳ dòng code nào.

=== QUY TRÌNH 5 BƯỚC BẮT BUỘC ===
Bước 1: Tìm code tương tự trong Thư viện của người dùng -> ưu tiên cao nhất.
Bước 2: Tìm trong Thư viện mặc định (hình phẳng, hình không gian, đồ thị...).
Bước 3: Nếu không có mẫu -> tự vẽ nhưng phải học phong cách từ code mẫu.
Bước 4: Tính toán ngầm (tọa độ, góc, tỷ lệ, cực trị, tiệm cận) TRƯỚC khi xuất code.
Bước 5: Kiểm tra chéo toàn bộ quy tắc rồi mới xuất. Tự hỏi: "còn quy tắc nào chưa kiểm tra không?".

=== 10 QUY TẮC VÀNG (INVARIANTS) CỦA THẦY ĐỖ MINH ===
1. FONT: \every node/.style={font=\normalsize} — đặt vào options của \begin{tikzpicture}. TUYỆT ĐỐI không dùng \Large, \large hay font size khác bất kỳ đâu.
2. KHAI BÁO BIẾN (declare function): BẮT BUỘC dùng declare function={a=5; h=4; r=3; goc=60;} ngay đầu \begin{tikzpicture}[...]. KHÔNG dùng số cứng trong tọa độ chính.
3. TỌA ĐỘ CỰC TRÊN TRỤC HOÀNH: Dùng (0:a) thay vì (a,0); dùng (180:a) thay vì (-a,0).
4. LINE CAP: line cap=round là TUYỆT ĐỐI CẤM dùng trong mọi trường hợp.
5. LINE JOIN: line join=round CHỈ dùng cho đồ thị hàm số / đường cong. CẤM dùng cho hình học phẳng và không gian.
6. ĐIỂM VÀ NHÃN:
   - Điểm hình học: \draw[line width=0.6pt] (X) circle (0.4pt) -> đen rỗng, KHÔNG tô trắng.
   - Điểm đồ thị: \fill (x,y) circle (1pt) -> đen đặc.
   - Nhãn điểm hình học trong \foreach: PHẢI dùng 2 biến: node[shift={(\goc:9pt)}]{$\t$}. KHÔNG dùng above/below/left/right trong mảng \foreach — phải dùng số đo độ.
   - Nhãn trên đường thẳng/cong: node[pos=0.5, sloped, above/below]{$...$}.
   - Nếu điểm có nhiều ký hiệu góc -> tách riêng khỏi \foreach, dùng shift={(225:15pt)} bán kính lớn hơn.
   - Không kết hợp above và below (sai). Hợp lệ: above left, above right, below left, below right.
   - Tất cả ký hiệu toán học / tên đỉnh PHẢI đặt trong $...$.
7. ĐỒ THỊ HÀM SỐ:
   - Hệ trục:
     \draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below]{$x$};
     \draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[below left]{$y$};
   - Đồ thị: line width=0.6pt, smooth, samples=150.
   - Tiệm cận: nét đứt dashed, line width=0.6pt.
   - Clip: Bọc đồ thị + tiệm cận trong \begin{scope} với \clip (xmin,ymin) rectangle (xmax,ymax). Tiệm cận đặt SAU \clip nhưng TRƯỚC đồ thị.
   - Gióng điểm: Chỉ gióng từ CỰC TRỊ xuống trục (ngoại lệ: tô miền diện tích -> gióng từ cận tích phân xuống Ox mà thôi). Đánh dấu chấm tại điểm gióng trên trục.
   - ymin/ymax: tính từ tung độ tâm đối xứng (giao tiệm cận hoặc điểm uốn): ymin = y_tâm - 4, ymax = y_tâm + 4.
   - Nhãn đồ thị: Đặt dưới dạng comment % postaction={decoration={markings, mark=at position 0.8 with {\node[transform shape, sloped, above left]{$y=...$};}}, decorate} — ẨN bằng % để người dùng tự bật khi cần.
8. BẢNG BIẾN THIÊN (BBT) & BẢNG XÉT DẤU (BXD):
   - Khởi tạo: \tkzTabInit[nocadre=false, lgt=..., espcl=..., deltacl=0.6]
     + lgt=1.2 nếu nhãn là "y"; lgt=1.5 nếu nhãn là "f(x)".
     + espcl: 3 giá trị x -> 3.5; 4 giá trị -> 2.5; 5 giá trị -> 2.
   - Chiều cao dòng: x và f'(x) đều 0.7; dòng hàm số cuối là 2 hoặc 2.5.
   - Dòng xét dấu: BỎ chữ "d", để trống: \tkzTabLine{, -, 0, +,  , +, 0, -, }
   - Mũi tên: CẤM \tkzTabVar. Vẽ thủ công:
     \path ([yshift=8pt]N13) node (A1){$-\infty$}
           ([yshift=-8pt]N22) node (A2){$-\dfrac{22}{27}$}
           ([yshift=-8pt]N32) node (A3){$+\infty$};
     \foreach \i/\j in {1/2, 2/3}{\draw[-Stealth](A\i)--(A\j);}
   - Điểm không xác định: \draw[double distance=1pt, double=white, line width=0.4pt](N...) -- (N...);
   - Phân số: BẮT BUỘC dùng \dfrac{}{}.
   - BXD: Giống BBT nhưng chỉ có 2 dòng {$x$/1, $f'(x)$/0.7}, không có dòng mũi tên biến thiên.
9. TÔ PATTERN VÀ MIỀN DIỆN TÍCH:
   - Pattern: pattern={Lines[angle=45, distance=4pt, line width=0.3pt]}, pattern color=gray!70
   - Góc pattern: BẮT BUỘC góc xiên (30, 45, 60, 120, 150) — KHÔNG dùng 0, 90, 180.
   - Distance: 1-2 miền -> 4pt; 3 miền trở lên -> 5pt.
   - KHÔNG dùng pattern=north west lines hay pattern color=black!70.
10. HÌNH KHÔNG GIAN (3D) VÀ TRỤC SỐ:
   - Điểm gốc: Luôn xác định (0,0) là điểm cơ sở. Các điểm còn lại dùng tọa độ cực + phép biến hình.
   - Ký hiệu góc vuông: \path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=A--B--C};
   - Elip/tròn 3D: Chia domain thành 2 phần — phần khuất dùng dash pattern=on 2pt off 1.5pt, phần thấy vẽ liền.
   - Nét khuất 3D: line width=0.4pt dashed. Nét thấy: line width=0.6pt.
   - Hình hộp: C' đặt nhãn ở góc 90 hoặc -25 độ; A ở 170 độ.
   - Trục số: KHÔNG vẽ cung tròn. Dùng ký tự ngoặc (, ), [, ] đặt vào node trên trục.
   - Mạch điện: circuitikz chuẩn european. Lưỡng cực: \draw ... to[R, l=$R_1$] ...;

=== XUẤT CODE ===
- Bắt đầu bằng \begin{tikzpicture}[...] (hoặc \begin{circuitikz}).
- Kết thúc bằng \end{tikzpicture} (hoặc \end{circuitikz}).
- Chỉ xuất code TikZ thuần túy. KHÔNG kèm \documentclass / \usepackage / \begin{document}.
- KHÔNG bọc trong markdown fences hay lời giải thích dài dòng.
"""

_EMBEDDED_OPTIMIZATION_PROMPT = r"""[VAI TRÒ]
Bạn là một Chuyên gia Hình học Toán học và Kiến trúc sư mã TikZ cấp cao (Phong cách Thầy Đỗ Minh - DoMinhMath).

[MỤC TIÊU CỐT LÕI]
Khi nhận được mã TikZ đầu vào, TUYỆT ĐỐI KHÔNG tự ý sáng tác hay tạo lại code từ đầu.
Nhiệm vụ: phân tích cấu trúc hình học, tính toán nhiều chiều, qua 6-10 lượt (multi-pass analysis)
để tái cấu trúc, chuẩn hóa và tối ưu hóa đoạn mã đó đạt chuẩn xuất bản chuyên nghiệp.
Chỉ xuất ra đoạn mã TikZ đã được chuẩn hóa, không có lời giải thích dài dòng.

[NGUYÊN TẮC TỐI ƯU HÓA]
1. THAM SỐ HÓA (Parameterization):
   Thay thế tất cả giá trị cứng (hardcode) bằng biến số trong declare function:
   \begin{tikzpicture}[>=stealth, every node/.style={font=\normalsize},
     declare function={R=2.5; r=0.8; h=5;}]

2. XÓA ĐIỂM CHẾT (Dead-code Elimination):
   Loại bỏ hoàn toàn: \coordinate, \node, \draw không đóng góp vào hình vẽ cuối cùng.

3. HÌNH HỌC GIẢI TÍCH VÀ PHÉP BIẾN HÌNH:
   - Không tọa độ hóa thủ công các điểm phụ thuộc.
   - Dùng thư viện calc, intersections, phép biến hình (rotate, shift, scale...).
   - Ưu tiên tọa độ cực thay tọa độ Descartes cho đường tròn, đa giác đều, góc quay.
   - Tọa độ cực trên trục hoành: (0:a) và (180:a).

4. TỐI ƯU VÒNG LẶP:
   Khai thác tối đa \foreach cho các chi tiết có tính quy luật
   (chia vạch, vẽ lưới, gán nhãn hàng loạt, vẽ chuỗi điểm).

5. NHÃN ĐIỂM LINH HOẠT:
   - Dùng góc độ cụ thể: node[shift={(135:9pt)}]{$A$}
   - TUYỆT ĐỐI không dùng above/below/left/right trong \foreach.
   - Đảm bảo nhãn không cắt đứt đường vẽ hoặc đè lên nhau.

6. KHOẢNG/ĐOẠN TRÊN TRỤC SỐ:
   TUYỆT ĐỐI KHÔNG dùng cung tròn hay arc.
   BẮT BUỘC dùng ký tự ngoặc: "(", ")", "[", "]" đặt vào node trên trục.

7. BẢO TỒN NGUYÊN TRẠNG:
   Khi tối ưu, PHẢI bảo tồn tuyệt đối hình gốc.
   KHÔNG ĐƯỢC THÊM, BỚT, hay thay đổi bất kỳ thành phần nào
   (đường nét, điểm, nhãn, dữ liệu, mũi tên) TRỪ KHI có yêu cầu rõ ràng.

8. BẢNG BIẾN THIÊN (BBT):
   - Thay thế \tkzTabVar bằng vẽ mũi tên thủ công (\path ([yshift=...]N...) node ... + \draw[-Stealth]).
   - Bỏ chữ "d" trong \tkzTabLine, thay bằng khoảng trống.

9. TÔ MIỀN DIỆN TÍCH:
   - Chuẩn hóa sang patterns.meta: pattern={Lines[angle=45, distance=4pt, line width=0.3pt]}, pattern color=gray!70.
   - Loại bỏ pattern=north west lines hoặc pattern color=black!70.

10. LINE CAP & LINE JOIN:
   - Loại bỏ hoàn toàn line cap=round.
   - Chỉ giữ line join=round đối với đồ thị hoặc đường cong, xóa khỏi hình phẳng / hình không gian.

[NGUYÊN TẮC XẾP LỚP (LAYERING RULES)]
Cấu trúc lại thứ tự lệnh vẽ từ dưới lên trên:
• Lớp 1 (Dưới cùng): Tô màu vùng (\fill, \shade) — opacity phù hợp
• Lớp 2: Đường nét đứt (\draw[dashed]) — đường khuất
• Lớp 3: Đường nét liền (\draw) — đường thấy, viền chính
• Lớp 4: Điểm (\draw circle (0.4pt), \fill circle (1pt)) — đỉnh, giao điểm
• Lớp 5 (Trên cùng): Nhãn văn bản, ký hiệu toán học — luôn hiển thị rõ nhất

[QUY TRÌNH THỰC THI BẮT BUỘC]
• Bước 1 (Phân tích): Đọc mã gốc, trích xuất danh sách điểm cơ sở và quan hệ hình học.
• Bước 2 (Lên kế hoạch): Xác định thành phần có thể gộp thành vòng lặp, điểm cần chuyển sang tọa độ tương đối/cực.
• Bước 3 (Tái cấu trúc): Viết lại theo 5 lớp Layering Rules.
• Bước 4 (Kiểm tra chéo): Rà soát hình học có thay đổi không, nhãn toán học có bọc đúng trong $...$ không.
• Bước 5 (Xuất kết quả): Chỉ cung cấp đoạn mã TikZ tối ưu duy nhất (\begin{tikzpicture}...\end{tikzpicture}). Không kèm giải thích.
"""


# ── PROMPT GENERATORS ────────────────────────────────────────────────────────

def get_tikz_system_prompt() -> str:
    """Trả về System Prompt chuẩn Thầy Đỗ Minh (ưu tiên từ `SKILL.md`, fallback sang embedded)."""
    content = _read_skill_file("SKILL.md")
    if content:
        # Nếu đọc được file SKILL.md, trích xuất phần System Prompt hoặc trả về toàn bộ hướng dẫn
        match = re.search(r"## SYSTEM PROMPT TỔNG HỢP[\s\S]*?```(?:\w+)?\n([\s\S]*?)```", content)
        if match:
            return match.group(1).strip()
    return _EMBEDDED_SYSTEM_PROMPT.strip()


def get_tikz_draw_prompt(description: str, kb_examples: str = "") -> str:
    """Tạo prompt vẽ hình TikZ từ mô tả hoặc bài toán hình học theo phong cách Thầy Đỗ Minh."""
    system_rules = get_tikz_system_prompt()
    
    kb_section = ""
    if kb_examples and kb_examples.strip():
        kb_section = f"""
══════════════════════════════════════════════════════════════════════════
MẪU THƯ VIỆN THAM KHẢO (HỌC PHONG CÁCH VÀ CẤU TRÚC TỪ CÁC MẪU NÀY):
══════════════════════════════════════════════════════════════════════════
{kb_examples.strip()}
"""

    prompt = f"""{system_rules}

══════════════════════════════════════════════════════════════════════════
INPUT: MÔ TẢ HOẶC ĐỀ BÀI HÌNH HỌC CẦN VẼ
══════════════════════════════════════════════════════════════════════════
{description.strip()}
{kb_section}
══════════════════════════════════════════════════════════════════════════
YÊU CẦU ĐẦU RA:
1. Bắt đầu từ \\begin{{tikzpicture}}[declare function={{...}}, every node/.style={{font=\\normalsize}}, ...]
   và kết thúc bằng \\end{{tikzpicture}} (hoặc circuitikz nếu là mạch điện).
2. KHÔNG kèm \\documentclass, \\usepackage hay \\begin{{document}}.
3. KHÔNG kèm lời dẫn, giải thích hay markdown code block (```latex).
4. CHỈ TRẢ VỀ ĐOẠN MÃ TIKZ THUẦN TÚY ĐÃ ĐƯỢC KIỂM TRA CHÉO HOÀN HẢO.
══════════════════════════════════════════════════════════════════════════
"""
    return prompt.strip()


def get_tikz_edit_prompt(current_code: str, edit_request: str) -> str:
    """Tạo prompt chỉnh sửa code TikZ hiện tại theo yêu cầu người dùng."""
    system_rules = get_tikz_system_prompt()
    
    prompt = f"""{system_rules}

══════════════════════════════════════════════════════════════════════════
CODE TIKZ HIỆN TẠI:
══════════════════════════════════════════════════════════════════════════
{current_code.strip()}

══════════════════════════════════════════════════════════════════════════
YÊU CẦU CHỈNH SỬA:
══════════════════════════════════════════════════════════════════════════
{edit_request.strip()}

══════════════════════════════════════════════════════════════════════════
QUY TẮC CHỈNH SỬA:
1. BẢO TỒN NGUYÊN TRẠNG các phần không liên quan; chỉ sửa hoặc bổ sung phần được yêu cầu.
2. Áp dụng chuẩn Thầy Đỗ Minh (declare function, \\normalsize, shift góc cho nhãn, không line cap=round).
3. Đảm bảo toàn bộ quan hệ hình học (vuông góc, song song, tiếp xúc, tỉ lệ) đúng tuyệt đối.
4. Trả về toàn bộ code TikZ hoàn chỉnh từ \\begin{{tikzpicture}} đến \\end{{tikzpicture}}.
5. KHÔNG kèm \\documentclass / \\usepackage / \\begin{{document}}.
6. CHỈ TRẢ VỀ CODE TIKZ THUẦN, KHÔNG GIẢI THÍCH.
══════════════════════════════════════════════════════════════════════════
"""
    return prompt.strip()


def get_tikz_optimization_prompt(current_code: str) -> str:
    """Tạo prompt tối ưu hóa code TikZ có sẵn theo 5 lớp và 10 invariants (09-optimization-prompt.md)."""
    raw_opt = _read_skill_file("09-optimization-prompt.md")
    opt_body = ""
    if raw_opt:
        match = re.search(r"## 9\.1\. SYSTEM PROMPT TỐI ƯU HÓA[\s\S]*?```(?:\w+)?\n([\s\S]*?)```", raw_opt)
        if match:
            opt_body = match.group(1).strip()
    if not opt_body:
        opt_body = _EMBEDDED_OPTIMIZATION_PROMPT.strip()

    prompt = f"""{opt_body}

══════════════════════════════════════════════════════════════════════════
CODE TIKZ CẦN TỐI ƯU HÓA:
══════════════════════════════════════════════════════════════════════════
{current_code.strip()}
"""
    return prompt.strip()


def get_tikz_vision_prompt(
    extra_prompt: str = "",
    tasks: Optional[list[str]] = None,
    enable_notes: bool = True,
    bbt_no_frame: bool = False,
    kb_examples: str = "",
) -> str:
    """Tạo Multimodal Vision Prompt chuẩn WebTikZ & Thầy Đỗ Minh để AI phân tích ảnh và tự động vẽ TikZ trực tiếp."""
    system_rules = get_tikz_system_prompt()
    if bbt_no_frame:
        system_rules = system_rules.replace("nocadre=false", "nocadre=true")

    note_rule = (
        "BẮT BUỘC THÊM CHÚ THÍCH (GHI CHÚ): Chỉ cần chú thích tên chủ đề và tên các nhóm lệnh chính để phân chia bố cục "
        "(ví dụ: '% ĐỒ THỊ HÀM SỐ', '% 1. HỆ TRỤC TỌA ĐỘ', '% 2. ĐỒ THỊ VÀ TIỆM CẬN', '% 3. ĐÁNH DẤU VÀ GIÓNG ĐIỂM'). "
        "KHÔNG CẦN chú thích chi tiết cho từng dòng lệnh nhỏ."
        if enable_notes
        else "KHÔNG THÊM CHÚ THÍCH (GHI CHÚ): Chỉ xuất code TikZ thuần túy, tuyệt đối không thêm bất kỳ dòng chú thích (comment %) nào. "
        "Dùng dòng trống (blank lines) để phân cách các môi trường, các nhóm lệnh chính."
    )

    task_str = ""
    if tasks:
        task_str = f"YÊU CẦU TRỌNG TÂM: Hãy nhận diện và vẽ: {', '.join(tasks)} từ hình ảnh được cung cấp.\n"

    kb_section = ""
    if kb_examples and kb_examples.strip():
        kb_section = f"\n=== NGÂN HÀNG CODE MẪU THAM KHẢO ===\n{kb_examples.strip()}\n"

    extra_str = f"\nYÊU CẦU BỔ SUNG TỪ NGƯỜI DÙNG: {extra_prompt.strip()}\n" if extra_prompt and extra_prompt.strip() else ""

    prompt = f"""Bạn là trợ lý AI chuyên gia vẽ hình TikZ Toán học hàng đầu (Phong cách Thầy Đỗ Minh & WebTikZ).

NHIỆM VỤ CỐT LÕI:
Người dùng gửi cho bạn một HÌNH ẢNH (đề thi, đồ thị, hình học phẳng, hình học không gian, bảng biến thiên, bảng xét dấu, hoặc hình vẽ toán học).
Bạn hãy QUAN SÁT VÀ PHÂN TÍCH TOÀN DIỆN HÌNH ẢNH, sau đó TỰ ĐỘNG LẬP TRÌNH VÀ VẼ LẠI CHÍNH XÁC HÌNH ĐÓ BẰNG MÃ TIKZ HOÀN CHỈNH.

{task_str}{extra_str}
QUY TRÌNH XỬ LÝ TRỰC QUAN BẮT BUỘC:
Bước 1: Quan sát kỹ hình ảnh: nhận diện loại hình (đa diện 3D, tròn/elip, hình phẳng, đồ thị hàm số, bảng biến thiên tkz-tab, bảng xét dấu, miền diện tích...).
Bước 2: Trích xuất chính xác mọi đỉnh (A, B, C, S...), tọa độ tương đối, độ dài, góc, tiệm cận, cực trị, chiều mũi tên, nét đứt/liền.
Bước 3: BẢO TỒN NGUYÊN TRẠNG cấu trúc và dữ liệu từ ảnh gốc: tuyệt đối không tự ý thêm bớt các đỉnh hoặc bóp méo hình gốc trừ khi có yêu cầu thêm.
Bước 4: Tính toán ngầm tham số (declare function), tọa độ cực, tỉ lệ cân đối trước khi xuất mã.
Bước 5: Tự kiểm tra đối chiếu (2 chiều) các quy tắc font \\normalsize, nhãn trong foreach dùng góc độ shift={{\\goc:9pt}}, không dùng line cap=round.

=== QUY TẮC PHONG CÁCH BẮT BUỘC (STYLE GUIDE) ===
{system_rules}

=== QUY TẮC CHÚ THÍCH CODE ===
{note_rule}
{kb_section}
=== HƯỚNG DẪN XUẤT CODE (RẤT QUAN TRỌNG) ===
1. Bắt đầu ngay bằng: \\begin{{tikzpicture}}[declare function={{...}}, every node/.style={{font=\\normalsize}}, ...] (hoặc \\begin{{circuitikz}}).
2. Kết thúc bằng: \\end{{tikzpicture}} (hoặc \\end{{circuitikz}}).
3. NẾU phát hiện hình thuộc câu hỏi / bài tập trong đề thi, thêm 1 dòng comment ở đầu: % code [Tên hình/bài] - [Câu số nếu thấy].
4. CHỈ TRẢ VỀ DUY NHẤT MÃ TIKZ THUẦN TÚY.
5. TUYỆT ĐỐI KHÔNG BỌC TRONG MARKDOWN FENCES (```latex), KHÔNG KÈM LỜI DẪN HAY GIẢI THÍCH."""

    return prompt.strip()


def clean_tikz_boilerplate(code: str) -> str:
    """Làm sạch code TikZ từ AI theo chuẩn WebTikZ (loại bỏ markdown, preamble, boilerplates)."""
    return extract_tikz_code(code)


# ── CODE EXTRACTION (TRÍCH XUẤT TIKZ THUẦN) ──────────────────────────────────

def extract_tikz_code(raw_text: str) -> str:
    """
    Trích xuất code TikZ thuần túy từ phản hồi của AI hoặc file LaTeX hoàn chỉnh.
    Thứ tự ưu tiên theo chuẩn `08-latex-builder.md`:
    1. Giữa `\\begin{document}` và `\\end{document}`
    2. `\\begin{tikzpicture} ... \\end{tikzpicture}`
    3. `\\begin{circuitikz} ... \\end{circuitikz}`
    4. Markdown code fence ```(?:latex|tex|tikz)? ... ```
    5. `\\begin{axis} ... \\end{axis}` (tự động bọc trong tikzpicture)
    6. Fallback về raw_text đã strip
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # 1. Trích xuất giữa \begin{document} và \end{document}
    doc_match = re.search(r"\\begin\{document\}([\s\S]*?)\\end\{document\}", text)
    if doc_match:
        text = doc_match.group(1).strip()

    # 2. Bỏ qua markdown fence nếu có bọc bên ngoài
    fence_match = re.search(r"```(?:latex|tex|tikz)?\s*([\s\S]*?)```", text)
    if fence_match:
        text = fence_match.group(1).strip()

    # 3. Ưu tiên tìm môi trường tikzpicture
    tikz_match = re.search(r"(\\begin\{tikzpicture\}[\s\S]*?\\end\{tikzpicture\})", text)
    if tikz_match:
        return tikz_match.group(1).strip()

    # 4. Tìm môi trường circuitikz
    circuit_match = re.search(r"(\\begin\{circuitikz\}[\s\S]*?\\end\{circuitikz\})", text)
    if circuit_match:
        return circuit_match.group(1).strip()

    # 5. Nếu AI chỉ trả về \begin{axis}...\end{axis}, tự động bọc trong tikzpicture
    axis_match = re.search(r"(\\begin\{axis\}[\s\S]*?\\end\{axis\})", text)
    if axis_match:
        return (
            "\\begin{tikzpicture}[every node/.style={font=\\normalsize}]\n"
            + axis_match.group(1).strip()
            + "\n\\end{tikzpicture}"
        )

    # 6. Loại bỏ \documentclass nếu còn sót lại ở đầu chuỗi
    if "\\documentclass" in text:
        text = re.sub(r"\\documentclass(?:\[[^\]]*\])?\{[^}]*\}", "", text).strip()

    return text.strip()


def clean_boilerplate(code: str) -> Tuple[str, bool]:
    """Làm sạch code TikZ: bóc tách phần thân tikzpicture/circuitikz, loại bỏ \\documentclass, \\usepackage thừa (tương tự WebTikZ).
    
    Returns:
        (cleaned_code, was_removed): mã đã lọc sạch và cờ báo hiệu có loại bỏ boilerplate hay không.
    """
    if not code:
        return "", False
    extracted = extract_tikz_code(code)
    if extracted and extracted.strip() != code.strip():
        return extracted, True
    return code, False


# ── STANDALONE LATEX BUILDER (LATEX PREAMBLE DỰA TRÊN 08-latex-builder.md) ────

def build_standalone_latex(tikz_code: str, *, border: str = "10mm") -> str:
    """
    Tự động quét mã TikZ, phát hiện packages và libraries cần thiết,
    tạo document LaTeX standalone hoàn chỉnh theo chuẩn `08-latex-builder.md`.
    """
    code = extract_tikz_code(tikz_code)
    if not code:
        code = (tikz_code or "").strip()

    packages: List[str] = [
        r"\usepackage[utf8]{vietnam}",
        r"\usepackage{amsmath,amssymb,amsfonts,mathtools,bm}",
        r"\usepackage{tikz}",
        r"\usepackage{pgfplots}",
    ]
    extra_configs: List[str] = [
        r"\pgfplotsset{compat=1.18}",
    ]

    # ── Phát hiện packages (Bảng 8.2) ──
    code_lower = code.lower()

    # physics, siunitx
    if any(k in code for k in [r"\qty", r"\SI", r"\norm", r"\abs", r"\dd", r"\dv"]):
        packages.append(r"\usepackage{physics,siunitx}")
        extra_configs.append(r"\sisetup{per-mode=symbol}")

    # mhchem, chemfig
    if any(k in code for k in [r"\ce", r"\ch", r"\chemfig"]):
        packages.append(r"\usepackage[version=4]{mhchem}")
        packages.append(r"\usepackage{chemfig}")

    # circuitikz
    if "circuitikz" in code_lower or "to[" in code:
        if "american" in code_lower:
            packages.append(r"\usepackage[american, scale=1.2]{circuitikz}")
        else:
            packages.append(r"\usepackage[european, scale=1.2]{circuitikz}")

    # graphicx
    if r"\includegraphics" in code:
        packages.append(r"\usepackage{graphicx}")

    # pgfplots libraries (pgfplots is in default packages)
    if any(k in code for k in ["pgfplots", r"\begin{axis}", r"\addplot"]):
        extra_configs.append(r"\usepgfplotslibrary{fillbetween,statistics}")

    # tkz-euclide
    if r"\tkz" in code and r"\tkzTab" not in code:
        packages.append(r"\usepackage{tkz-euclide}")

    # tikz-3dplot
    if "tdplot" in code:
        packages.append(r"\usepackage{tikz-3dplot}")

    # listings
    if "lstlisting" in code or r"\lst" in code:
        packages.append(r"\usepackage{listings}")

    # tkz-tab
    if r"\tkzTab" in code:
        packages.append(r"\usepackage{tkz-tab,tabvar}")

    # tabular, table, figure
    if any(k in code for k in ["tabular", "table", "figure", "multirow", r"\toprule"]):
        packages.append(r"\usepackage{float,caption,subcaption,booktabs,multirow,array}")

    # ── Phát hiện TikZ libraries (Bảng 8.3) ──
    libraries: List[str] = ["arrows.meta"]

    if "$" in code or "calc" in code:
        libraries.append("calc")
    if "intersection" in code:
        libraries.append("intersections")
    if any(k in code for k in ["above=", "below=", "left=", "right=", "positioning"]):
        libraries.append("positioning")
    if any(k in code for k in ["ellipse", "polygon", "star", "shapes.geometric"]):
        libraries.append("shapes.geometric")
    if "pattern" in code:
        libraries.append("patterns.meta")
    if "decorat" in code:
        libraries.append("decorations.markings")
        libraries.append("decorations.pathmorphing")
    if any(k in code for k in ["pic", "angle", "right angle"]):
        libraries.append("angles")
        libraries.append("quotes")
        extra_configs.append(r"\tikzset{right angle/.style={angle}}")
    if "circle through" in code:
        libraries.append("through")
    if "background" in code:
        libraries.append("backgrounds")
    if "fit=" in code:
        libraries.append("fit")
    if "mark=" in code:
        libraries.append("plotmarks")
    if "chain" in code:
        libraries.append("chains")
    if "matrix" in code:
        libraries.append("matrix")
    if "perspective" in code:
        libraries.append("perspective")
    if "canvas is" in code:
        libraries.append("3d")

    # Loại bỏ duplicate giữ nguyên thứ tự
    seen_libs = set()
    uniq_libs = []
    for lib in libraries:
        if lib not in seen_libs:
            seen_libs.add(lib)
            uniq_libs.append(lib)

    pkg_str = "\n".join(packages)
    lib_str = f"\\usetikzlibrary{{{', '.join(uniq_libs)}}}"
    cfg_str = "\n".join(extra_configs) if extra_configs else ""

    doc = [
        f"\\documentclass[tikz,border={border}]{{standalone}}",
        "% --- PACKAGES TỰ ĐỘNG PHÁT HIỆN THEO CHUẨN TIKZ AI SKILL ---",
        pkg_str,
        lib_str,
    ]
    if cfg_str:
        doc.append("% --- CẤU HÌNH BỔ SUNG ---")
        doc.append(cfg_str)
    doc.extend([
        "\\begin{document}",
        code,
        "\\end{document}",
    ])

    return "\n".join(doc)


# ── TRUY XUẤT TÀI LIỆU VÀ MẪU CỦA SKILL ──────────────────────────────────────

def get_skill_docs() -> Dict[str, str]:
    """Trả về dict chứa tất cả tài liệu markdown trong thư mục `tikz_ai_skill/`."""
    skill_dir = _get_skill_dir()
    docs: Dict[str, str] = {}
    if not skill_dir.is_dir():
        return docs

    for md_file in sorted(skill_dir.glob("*.md")):
        try:
            docs[md_file.name] = md_file.read_text(encoding="utf-8")
        except Exception as exc:
            _log.warning("Không thể nạp file %s: %s", md_file.name, exc)
    return docs


def get_skill_examples(category: str = "") -> str:
    """Trả về code ví dụ từ `10-code-examples.md`, có thể lọc theo category."""
    content = _read_skill_file("10-code-examples.md")
    if not content:
        return ""
    if not category:
        return content

    # Lọc phần tương ứng
    pattern = rf"##\s*[\d\.]*\s*{re.escape(category)}[\s\S]*?(?=\n##|\Z)"
    match = re.search(pattern, content, re.IGNORECASE)
    if match:
        return match.group(0).strip()
    return content
