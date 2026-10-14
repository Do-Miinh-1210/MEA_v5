"""
omr_exam/sheet_generator.py — Thiết kế & Tạo phiếu trả lời trắc nghiệm chuẩn OMR:
- Thiết kế hình học tối ưu: 4 mốc định vị góc (Corner Markers) cho camera nắn phối cảnh.
- Ô tô tròn nền trắng, viền đen, rõ ràng, khoảng cách đều đặn.
- Vùng tô Mã đề thi (0-9 cho 3 chữ số).
- Vùng câu hỏi: 20, 40 hoặc 50 câu (mỗi câu 4 ô A, B, C, D).
- Vùng viết tự luận (dòng kẻ) nếu đề có phần tự luận.
- Xuất ra file hình ảnh PNG độ nét cao (300 DPI) để in giấy A4 trực tiếp.
"""
from __future__ import annotations
import math
try:
    import numpy as np
    import cv2
except Exception:
    np = None
    cv2 = None
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Tuple, List, Optional


# Kích thước trang A4 ở 150 DPI: 1240 x 1754 px (chuẩn in rõ nét & xử lý OpenCV nhanh)
A4_WIDTH = 1240
A4_HEIGHT = 1754

MARKER_SIZE = 50   # Kích thước khối vuông đen ở 4 góc để nắn phối cảnh
MARGIN_X = 60
MARGIN_Y = 60


def generate_omr_sheet_image(
    num_questions: int = 40,
    has_essay: bool = False,
    essay_lines: int = 6,
    exam_title: str = "PHIẾU TRẢ LỜI TRẮC NGHIỆM"
) -> Tuple[np.ndarray, Dict]:
    """
    Tạo ảnh phiếu trả lời trắc nghiệm OMR chuẩn hóa và trả về:
    - img_bgr: Ảnh OpenCV (numpy array BGR) sẵn sàng lưu hoặc in.
    - layout_meta: Tọa độ pixel chính xác của từng ô tròn (A, B, C, D) và ô Mã đề.
    """
    # 1. Tạo ảnh trắng
    canvas = np.full((A4_HEIGHT, A4_WIDTH, 3), 255, dtype=np.uint8)
    
    # 2. Vẽ 4 Marker vuông màu đen ở 4 góc
    # Top-Left, Top-Right, Bottom-Left, Bottom-Right
    markers = [
        (MARGIN_X, MARGIN_Y),
        (A4_WIDTH - MARGIN_X - MARKER_SIZE, MARGIN_Y),
        (MARGIN_X, A4_HEIGHT - MARGIN_Y - MARKER_SIZE),
        (A4_WIDTH - MARGIN_X - MARKER_SIZE, A4_HEIGHT - MARGIN_Y - MARKER_SIZE),
    ]
    for mx, my in markers:
        cv2.rectangle(canvas, (mx, my), (mx + MARKER_SIZE, my + MARKER_SIZE), (0, 0, 0), -1)
        # Thêm viền trắng mỏng bên trong để tạo đặc trưng góc sắc nét
        cv2.rectangle(canvas, (mx + 8, my + 8), (mx + MARKER_SIZE - 8, my + MARKER_SIZE - 8), (255, 255, 255), 3)
        cv2.rectangle(canvas, (mx + 16, my + 16), (mx + MARKER_SIZE - 16, my + MARKER_SIZE - 16), (0, 0, 0), -1)
        
    pil_img = Image.fromarray(canvas)
    draw = ImageDraw.Draw(pil_img)
    
    # Tiêu đề phiếu
    font_large = _get_font(26, bold=True)
    font_medium = _get_font(18, bold=True)
    font_small = _get_font(14, bold=False)
    font_bubble = _get_font(13, bold=True)
    
    title_text = exam_title.upper()
    draw.text((A4_WIDTH // 2 - 200, MARGIN_Y + 10), title_text, fill=(0, 0, 0), font=font_large)
    
    # Thông tin thí sinh (Khung chữ nhật bên trái)
    info_x1, info_y1 = MARGIN_X + MARKER_SIZE + 30, MARGIN_Y + 70
    info_x2, info_y2 = A4_WIDTH // 2 - 20, MARGIN_Y + 230
    draw.rectangle([info_x1, info_y1, info_x2, info_y2], outline=(0, 0, 0), width=2)
    
    draw.text((info_x1 + 15, info_y1 + 15), "Họ và tên thí sinh: ......................................................", fill=(0, 0, 0), font=font_small)
    draw.text((info_x1 + 15, info_y1 + 55), "Ngày sinh: .................... Lớp: ................. Phòng thi: ........", fill=(0, 0, 0), font=font_small)
    draw.text((info_x1 + 15, info_y1 + 95), "Chữ ký giám thị 1: .................. Giám thị 2: ....................", fill=(0, 0, 0), font=font_small)
    draw.text((info_x1 + 15, info_y1 + 135), "LƯU Ý: Dùng bút chì tô ĐEN KÍN ô tròn. Không gạch chéo.", fill=(180, 0, 0), font=font_small)

    # Vùng tô MÃ ĐỀ THI (Bên phải thông tin thí sinh)
    # 3 cột số: Hàng trăm, Hàng chục, Hàng đơn vị (mỗi cột 0 -> 9)
    code_box_x1, code_box_y1 = A4_WIDTH // 2 + 30, MARGIN_Y + 70
    code_box_x2, code_box_y2 = A4_WIDTH - MARGIN_X - MARKER_SIZE - 30, MARGIN_Y + 260
    draw.rectangle([code_box_x1, code_box_y1, code_box_x2, code_box_y2], outline=(0, 0, 0), width=2)
    draw.text((code_box_x1 + 15, code_box_y1 + 8), "MÃ ĐỀ THI", fill=(0, 0, 0), font=font_medium)
    
    # Tọa độ lưu metadata để OMR Grader quét chính xác
    layout_meta = {
        "markers": markers,
        "width": A4_WIDTH,
        "height": A4_HEIGHT,
        "code_bubbles": {},     # {col_idx (0..2): {digit (0..9): (cx, cy, r)}}
        "question_bubbles": {}, # {q_idx: {"A": (cx, cy, r), "B": ..., "C": ..., "D": ...}}
        "has_essay": has_essay,
    }
    
    # Vẽ các ô tô Mã đề thi
    code_cols = 3
    col_spacing = 55
    code_start_x = code_box_x1 + 35
    code_start_y = code_box_y1 + 45
    radius = 12
    
    for c in range(code_cols):
        layout_meta["code_bubbles"][c] = {}
        cx = code_start_x + c * col_spacing
        for digit in range(10):
            cy = code_start_y + digit * 17
            # Vẽ ô tròn nền trắng viền đen
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=(0, 0, 0), width=2)
            # Số bên trong
            draw.text((cx - 4, cy - 8), str(digit), fill=(0, 0, 0), font=font_bubble)
            layout_meta["code_bubbles"][c][digit] = (cx, cy, radius)

    # 3. VÙNG TÔ ĐÁP ÁN TRẮC NGHIỆM
    # Chia làm 2 hoặc 4 cột câu hỏi tùy số lượng câu (thông thường 40 câu -> 2 cột hoặc 4 cột)
    ans_start_y = MARGIN_Y + 280
    num_cols = 2 if num_questions <= 30 else (4 if not has_essay else 3)
    questions_per_col = math.ceil(num_questions / num_cols)
    
    col_width = (A4_WIDTH - 2 * MARGIN_X - 60) // num_cols
    labels = ["A", "B", "C", "D"]
    opt_spacing = 38
    
    for q_idx in range(1, num_questions + 1):
        col_idx = (q_idx - 1) // questions_per_col
        row_idx = (q_idx - 1) % questions_per_col
        
        base_x = MARGIN_X + 30 + col_idx * col_width
        cy = ans_start_y + row_idx * 28
        
        # Số thứ tự câu (vd: "01.", "12.")
        q_label_str = f"{q_idx:02d}."
        draw.text((base_x, cy - 8), q_label_str, fill=(0, 0, 0), font=font_medium)
        
        layout_meta["question_bubbles"][q_idx] = {}
        
        # 4 ô A, B, C, D
        for opt_i, opt_lbl in enumerate(labels):
            cx = base_x + 50 + opt_i * opt_spacing
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=(0, 0, 0), width=2)
            draw.text((cx - 5, cy - 8), opt_lbl, fill=(0, 0, 0), font=font_bubble)
            layout_meta["question_bubbles"][q_idx][opt_lbl] = (cx, cy, radius)
            
    # 4. VÙNG TỰ LUẬN (Nếu đề có phần TL)
    if has_essay:
        tl_start_y = ans_start_y + questions_per_col * 28 + 30
        draw.line([MARGIN_X, tl_start_y, A4_WIDTH - MARGIN_X, tl_start_y], fill=(0, 0, 0), width=3)
        draw.text((MARGIN_X + 20, tl_start_y + 10), "PHẦN TRẢ LỜI CÂU HỎI TỰ LUẬN (TL):", fill=(0, 0, 0), font=font_medium)
        
        line_y = tl_start_y + 45
        for _ in range(essay_lines + 2):  # Yêu cầu 4: Dư thêm 2 dòng
            if line_y < A4_HEIGHT - MARGIN_Y - MARKER_SIZE - 20:
                draw.line([MARGIN_X + 20, line_y, A4_WIDTH - MARGIN_X - 20, line_y], fill=(160, 160, 160), width=1)
                line_y += 32
                
    result_bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return result_bgr, layout_meta


def _get_font(size: int, bold: bool = False):
    """Lấy font hệ thống Windows Segoe UI / Arial."""
    font_names = [
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            pass
    return ImageFont.load_default()
