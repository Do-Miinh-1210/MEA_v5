"""
omr_exam/omr_grader.py — Thuật toán chấm bài thi OMR tự động từ hình ảnh:
1. Phát hiện 4 mốc định vị góc (Corner Markers).
2. Nắn phẳng phối cảnh (Perspective Warp) loại bỏ ảnh nghiêng, lệch góc.
3. Cân bằng ánh sáng và nhị phân hóa thích ứng (Adaptive Thresholding).
4. Đo mật độ điểm ảnh đen (Black pixel fill ratio) từng ô tròn.
5. Nhận diện: Ô đã tô, Bỏ trống, Tô nhiều ô trong 1 câu, Ô nghi ngờ.
6. Đọc Mã đề thi từ vùng tô mã đề.
7. Đối chiếu với Bảng đáp án chuẩn của mã đề đó -> Tính số câu đúng/sai và điểm số.
"""
from __future__ import annotations
try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class QuestionGradeResult:
    """Kết quả chi tiết của 1 câu trắc nghiệm."""
    question_idx: int
    student_answers: List[str]      # ["A"], ["B", "C"], hoặc [] (nếu bỏ trống)
    correct_answer: str             # "A", "B"...
    is_correct: bool = False
    status: str = "VALID"           # "VALID", "BLANK", "MULTIPLE", "UNCERTAIN"
    fill_ratios: Dict[str, float] = None


@dataclass
class ExamGradingReport:
    """Báo cáo tổng hợp kết quả chấm bài của một phiếu."""
    student_code: str = ""          # Số báo danh (nếu có)
    exam_code: str = ""             # Mã đề thi nhận diện được
    total_questions: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    blank_count: int = 0
    multiple_count: int = 0
    uncertain_count: int = 0
    total_score: float = 0.0        # Điểm thang 10
    max_score: float = 10.0
    details: List[QuestionGradeResult] = None
    warped_image: np.ndarray = None # Ảnh đã được nắn phẳng và vẽ viền xanh/đỏ để kiểm tra visual


# Ngưỡng tỷ lệ điểm ảnh tô đen
# Ô trống chứa nét viền và chữ A/B/C/D bên trong chiếm khoảng ~18% - 32% diện tích
# Ô tô bằng bút chì/bút bi đạt > 60% - 95% diện tích
THRESHOLD_FILLED = 0.52      # >= 52% là ô đã tô
THRESHOLD_BLANK = 0.35       # <= 35% là ô trống
# Từ 35% đến 52% rơi vào vùng nghi ngờ (tô mờ/tẩy chưa sạch/lệch) -> Đánh dấu UNCERTAIN kiểm tra thủ công


def align_omr_sheet(
    image: np.ndarray,
    target_w: int = 1240,
    target_h: int = 1754
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Tìm 4 mốc đen góc và nắn phối cảnh về ảnh phẳng kích thước chuẩn (target_w, target_h).
    """
    if image is None:
        return None, None
        
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    
    # Giảm nhiễu
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # Otsu thresholding để phát hiện khối đen
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Tìm contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Tìm 4 khối hình vuông định vị (kích thước tương đương MARKER_SIZE)
    # Đặc điểm: Contour có 4 đỉnh xấp xỉ, diện tích phù hợp, tỷ lệ cạnh gần 1:1
    candidate_markers = []
    
    img_area = gray.shape[0] * gray.shape[1]
    min_marker_area = img_area * 0.0003
    max_marker_area = img_area * 0.02
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_marker_area < area < max_marker_area:
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.7 <= aspect_ratio <= 1.4:
                    # Tính tâm của marker
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        candidate_markers.append((cx, cy))
                        
    # Nếu tìm được đủ 4 marker
    if len(candidate_markers) >= 4:
        # Lấy 4 điểm xa nhất về 4 góc
        pts = np.array(candidate_markers, dtype="float32")
        ordered_pts = _order_points(pts[:4])
        
        # Ma trận đích: tâm của 4 khối vuông (MARGIN_X + 25, MARGIN_Y + 25)
        # với MARKER_SIZE = 50 -> tâm là 60 + 25 = 85
        dst = np.array([
            [85, 85],
            [target_w - 85, 85],
            [target_w - 85, target_h - 85],
            [85, target_h - 85]
        ], dtype="float32")
        
        M = cv2.getPerspectiveTransform(ordered_pts, dst)
        warped = cv2.warpPerspective(image, M, (target_w, target_h))
        return warped, ordered_pts
    else:
        # Fallback: Nếu không tìm thấy marker rời rạc, thử tìm viền toàn bộ trang giấy A4
        peri = cv2.arcLength(thresh, True)
        approx = cv2.approxPolyDP(thresh, 0.02 * peri, True)
        if len(approx) == 4:
            ordered_pts = _order_points(approx.reshape(4, 2).astype("float32"))
            dst = np.array([
                [0, 0],
                [target_w - 1, 0],
                [target_w - 1, target_h - 1],
                [0, target_h - 1]
            ], dtype="float32")
            M = cv2.getPerspectiveTransform(ordered_pts, dst)
            warped = cv2.warpPerspective(image, M, (target_w, target_h))
            return warped, ordered_pts
            
    # Trường hợp không nhận diện được góc -> Trả về ảnh resize chuẩn
    resized = cv2.resize(image, (target_w, target_h))
    return resized, None


def grade_omr_sheet(
    image: np.ndarray,
    layout_meta: Dict,
    answer_keys_by_code: Dict[str, Dict[int, str]],
    default_code: str = "101"
) -> ExamGradingReport:
    """
    Quy trình chấm bài toàn diện:
    1. Căn chỉnh phối cảnh.
    2. Đọc mã đề thi đã tô.
    3. Đọc từng câu hỏi, đo độ lấp đầy A, B, C, D.
    4. Đối chiếu đáp án chuẩn.
    5. Xuất báo cáo điểm và vẽ hình kiểm chứng visual.
    """
    report = ExamGradingReport(details=[])
    
    # 1. Căn chỉnh phối cảnh
    is_moon = layout_meta.get("template_type") == "moon"
    if is_moon:
        from omr_exam.moon_template import align_moon_sheet
        warped, _ = align_moon_sheet(image, layout_meta["width"], layout_meta["height"])
    else:
        warped, _ = align_omr_sheet(image, layout_meta["width"], layout_meta["height"])
        
    if warped is None:
        report.exam_code = "ERR_ALIGN"
        return report
        
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    
    # Nhị phân hóa thích ứng (chống bóng mờ hoặc ánh sáng không đều)
    # Áp dụng Otsu hoặc Adaptive Threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 25, 9
    )
    
    # 2. Đọc MÃ ĐỀ THI
    detected_code_digits = []
    code_bubbles = layout_meta.get("code_bubbles", {})
    
    for col_idx in range(len(code_bubbles)):
        col_data = code_bubbles[col_idx]
        best_digit = None
        max_fill = 0.0
        
        for digit, (cx, cy, r) in col_data.items():
            fill_ratio = _measure_bubble_fill(thresh, cx, cy, r)
            if fill_ratio > THRESHOLD_FILLED and fill_ratio > max_fill:
                max_fill = fill_ratio
                best_digit = digit
                
        if best_digit is not None:
            detected_code_digits.append(str(best_digit))
        else:
            detected_code_digits.append("?")
            
    detected_code = "".join(detected_code_digits)
    # Nếu mã đề không hợp lệ, dùng mã đề đầu tiên hoặc fallback
    if "?" in detected_code or detected_code not in answer_keys_by_code:
        report.exam_code = default_code if default_code in answer_keys_by_code else (list(answer_keys_by_code.keys())[0] if answer_keys_by_code else "101")
    else:
        report.exam_code = detected_code
        
    active_answer_key = answer_keys_by_code.get(report.exam_code, {})
    
    # 3. Đọc từng câu hỏi trắc nghiệm
    question_bubbles = layout_meta.get("question_bubbles", {})
    report.total_questions = len(question_bubbles)
    
    visual_img = warped.copy()
    
    for q_idx, opts in sorted(question_bubbles.items()):
        correct_ans = active_answer_key.get(q_idx, "")
        
        q_res = QuestionGradeResult(
            question_idx=q_idx,
            student_answers=[],
            correct_answer=correct_ans,
            fill_ratios={}
        )
        
        # Đo từng ô A, B, C, D
        filled_opts = []
        uncertain_opts = []
        
        for opt_lbl, (cx, cy, r) in opts.items():
            ratio = _measure_bubble_fill(thresh, cx, cy, r)
            q_res.fill_ratios[opt_lbl] = round(ratio, 3)
            
            if ratio >= THRESHOLD_FILLED:
                filled_opts.append(opt_lbl)
            elif THRESHOLD_BLANK <= ratio < THRESHOLD_FILLED:
                uncertain_opts.append(opt_lbl)
                
        q_res.student_answers = filled_opts
        
        # Đánh giá trạng thái câu trả lời
        if len(filled_opts) == 0:
            if uncertain_opts:
                q_res.status = "UNCERTAIN"  # Có ô tô quá mờ cần kiểm tra
                report.uncertain_count += 1
            else:
                q_res.status = "BLANK"      # Bỏ trống
                report.blank_count += 1
        elif len(filled_opts) > 1:
            q_res.status = "MULTIPLE"       # Tô nhiều đáp án
            report.multiple_count += 1
        else:
            q_res.status = "VALID"          # Hợp lệ (1 đáp án)
            
        # Kiểm tra đúng / sai
        if q_res.status == "VALID" and correct_ans:
            if q_res.student_answers[0] == correct_ans:
                q_res.is_correct = True
                report.correct_count += 1
            else:
                q_res.is_correct = False
                report.wrong_count += 1
        elif q_res.status in ("MULTIPLE", "BLANK", "UNCERTAIN"):
            q_res.is_correct = False
            if q_res.status != "BLANK":
                report.wrong_count += 1
                
        report.details.append(q_res)
        
        # Vẽ phản hồi visual trực tiếp lên ảnh warped
        for opt_lbl, (cx, cy, r) in opts.items():
            if opt_lbl == correct_ans:
                # Viền xanh lá cho đáp án đúng của đề
                cv2.circle(visual_img, (cx, cy), r + 4, (0, 200, 0), 2)
            if opt_lbl in filled_opts:
                if q_res.is_correct:
                    # Học sinh tô đúng -> vòng tròn xanh
                    cv2.circle(visual_img, (cx, cy), r + 2, (0, 255, 0), -1)
                else:
                    # Học sinh tô sai -> gạch chéo đỏ
                    cv2.circle(visual_img, (cx, cy), r + 2, (0, 0, 255), 2)
                    cv2.line(visual_img, (cx - r, cy - r), (cx + r, cy + r), (0, 0, 255), 2)
                    cv2.line(visual_img, (cx - r, cy + r), (cx + r, cy - r), (0, 0, 255), 2)
                    
    # 4. Tính tổng điểm thang 10
    if report.total_questions > 0:
        report.total_score = round((report.correct_count / report.total_questions) * 10.0, 2)
    else:
        report.total_score = 0.0
        
    report.warped_image = visual_img
    return report


def _measure_bubble_fill(thresh_img: np.ndarray, cx: int, cy: int, radius: int) -> float:
    """Đo tỷ lệ pixel trắng (tô đen trong ảnh gốc đã bị INV) bên trong ô tròn."""
    h, w = thresh_img.shape
    r = int(radius * 0.75)  # Đo vùng lõi bên trong ô để tránh viền tròn mép ngoài
    
    x1, y1 = max(0, cx - r), max(0, cy - r)
    x2, y2 = min(w, cx + r + 1), min(h, cy + r + 1)
    
    roi = thresh_img[y1:y2, x1:x2]
    if roi.size == 0:
        return 0.0
        
    # Tạo mask hình tròn với tâm là tâm tương đối của ROI
    mask = np.zeros(roi.shape, dtype=np.uint8)
    center_roi_x = cx - x1
    center_roi_y = cy - y1
    cv2.circle(mask, (center_roi_x, center_roi_y), r, 255, -1)
    
    total_circle_pixels = cv2.countNonZero(mask)
    if total_circle_pixels == 0:
        return 0.0
        
    filled_pixels = cv2.countNonZero(cv2.bitwise_and(roi, mask))
    return float(filled_pixels) / float(total_circle_pixels)


def _order_points(pts: np.ndarray) -> np.ndarray:
    """Sắp xếp 4 điểm theo thứ tự: Top-Left, Top-Right, Bottom-Right, Bottom-Left."""
    rect = np.zeros((4, 2), dtype="float32")
    
    # Top-Left có tổng (x+y) nhỏ nhất, Bottom-Right có tổng lớn nhất
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Top-Right có hiệu (y - x) nhỏ nhất, Bottom-Left có hiệu lớn nhất
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect
