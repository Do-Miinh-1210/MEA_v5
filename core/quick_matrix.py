"""
core/quick_matrix.py — Tạo ma trận đề nhanh theo thời lượng chuẩn BGD.
Hỗ trợ: 15 phút, 45 phút, 60 phút, 90 phút.
Tự phân bổ câu hỏi theo mức độ NB/TH/VD và loại TN/DS/TLN/TL.
Cập nhật: lấy chủ đề động từ file data/chuongtrinhhoctap.txt
"""

from __future__ import annotations
import random
import json
from pathlib import Path
from core.models import MatrixRow, MatrixData, DSItem

# ══════════════════════════════════════════════════════════════════════════════
#  CẤU TRÚC ĐỀ MẪU THEO THỜI LƯỢNG
# ══════════════════════════════════════════════════════════════════════════════

EXAM_TEMPLATES: dict[str, dict] = {
    "15p": {
        "time_str": "15 phút",
        "title_fmt": "KIỂM TRA 15 PHÚT",
        # (qtype, level, count)
        "questions": [
            ("TN", "NB", 3),
            ("TN", "TH", 2),
            ("TN", "VD", 2),
        ],
    },
    "45p": {
        "time_str": "45 phút",
        "title_fmt": "KIỂM TRA 1 TIẾT",
        "questions": [
            ("TN", "NB", 4), ("TN", "TH", 4), ("TN", "VD", 4),
            ("DS", "mixed", 2),       # 2 câu DS, mỗi câu 4 ý NB/TH/VD/VD
            ("TLN", "NB", 1), ("TLN", "TH", 1), ("TLN", "VD", 1),
        ],
    },
    "60p": {
        "time_str": "60 phút",
        "title_fmt": "KIỂM TRA GIỮA KÌ",
        "questions": [
            ("TN", "NB", 5), ("TN", "TH", 5), ("TN", "VD", 5),
            ("DS", "mixed", 3),
            ("TLN", "NB", 1), ("TLN", "TH", 2), ("TLN", "VD", 1),
            ("TL", "VD", 1),
        ],
    },
    "90p": {
        "time_str": "90 phút",
        "title_fmt": "KIỂM TRA CUỐI KÌ",
        "questions": [
            ("TN", "NB", 6), ("TN", "TH", 6), ("TN", "VD", 6),
            ("DS", "mixed", 4),
            ("TLN", "NB", 2), ("TLN", "TH", 2), ("TLN", "VD", 2),
            ("TL", "VD", 2),
        ],
    },
}

# ══════════════════════════════════════════════════════════════════════════════
#  CHỦ ĐỀ ĐỘNG TỪ FILE DATA
# ══════════════════════════════════════════════════════════════════════════════

_CHUONG_TRINH_DATA = None

def load_chuong_trinh() -> dict:
    """Đọc file data/chuongtrinhhoctap.txt, trả về dict."""
    global _CHUONG_TRINH_DATA
    if _CHUONG_TRINH_DATA is None:
        try:
            path = Path(__file__).parent.parent / "data" / "chuongtrinhhoctap.txt"
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    _CHUONG_TRINH_DATA = json.load(f)
            else:
                _CHUONG_TRINH_DATA = {}
        except Exception:
            _CHUONG_TRINH_DATA = {}
    return _CHUONG_TRINH_DATA

def get_topics_for_grade(grade: str) -> list[str]:
    """Trả về danh sách chủ đề động cho lớp grade, fallback sang mặc định.

    Mỗi topic = "<Tên chương> – <Tên bài>". Flat list, dùng khi cần list
    để random pick hoặc filter.
    """
    data = load_chuong_trinh()
    subject = "Toán"  # mặc định, có thể mở rộng sau
    grade_data = data.get(subject, {}).get(grade, [])
    topics = []
    for chapter in grade_data:
        chapter_name = chapter.get("chapter", "")
        for lesson in chapter.get("lessons", []):
            topics.append(f"{chapter_name} – {lesson}")
    if not topics:
        # fallback về danh sách cứng cũ
        return _FALLBACK_TOPICS.get(grade, _FALLBACK_TOPICS["12"])
    return topics


def get_chapters_for_grade(grade: str, subject: str = "Toán") -> list[dict]:
    """Trả về cấu trúc chương + bài cho lớp grade.

    Cho phép UI hiển thị hierarchical: chương → các bài bên trong.
    Dùng cho [SPEED-2] — cho user multi-select chương / bài cụ thể.

    Returns
    -------
    list[dict] — mỗi dict có shape:
        {
            "chapter": str,   # "Chương I: Tập hợp các số tự nhiên"
            "lessons": list[str],  # ["Tập hợp, phần tử…", "Cách ghi số…"]
            "topics":  list[str],  # ["Chương I: … – Tập hợp, …", …]
                                   #  ↑ đã ghép sẵn cho match TOPICS_BY_GRADE
        }
    Trả list rỗng nếu không có data cho grade này.
    """
    data = load_chuong_trinh()
    grade_data = data.get(subject, {}).get(grade, [])
    result = []
    for chap in grade_data:
        chapter_name = chap.get("chapter", "")
        if not chapter_name:
            continue
        lessons = list(chap.get("lessons", []))
        topics = [f"{chapter_name} – {ls}" for ls in lessons]
        result.append({
            "chapter": chapter_name,
            "lessons": lessons,
            "topics":  topics,
        })

    # Fallback: dùng _FALLBACK_TOPICS, mỗi topic = "Chương" (không có lesson)
    if not result:
        fb = _FALLBACK_TOPICS.get(grade, _FALLBACK_TOPICS.get("12", []))
        # Synthesize fake chapters từ flat list
        for i, t in enumerate(fb, 1):
            result.append({
                "chapter": t,        # chính là topic
                "lessons": [],
                "topics":  [t],
            })
    return result


def get_chapters_with_lessons(grade: str, subject: str = "Toán") -> list[dict]:
    """Alias dài hơn — backward compat nếu có code khác gọi tên này."""
    return get_chapters_for_grade(grade, subject)

_FALLBACK_TOPICS = {
    "1": ["Các số đến 10", "Phép cộng và phép trừ trong phạm vi 10",
          "Các số đến 20", "Các số đến 100", "Hình học trực quan"],
    "2": ["Phép cộng và phép trừ có nhớ trong phạm vi 100",
          "Phép nhân và phép chia", "Bảng nhân", "Đo lường",
          "Hình học phẳng"],
    "3": ["Phép nhân và phép chia trong phạm vi 1000",
          "Các số đến 10000", "Phân số", "Đo lường (khối lượng, thời gian)",
          "Hình học phẳng", "Thống kê đơn giản"],
    "4": ["Số tự nhiên lớn hơn 1000", "Phân số – Số thập phân",
          "Các phép tính với phân số", "Đo lường (diện tích, thể tích)",
          "Hình học không gian đơn giản", "Biểu đồ"],
    "5": ["Phân số và số thập phân", "Tỉ số phần trăm",
          "Số đo thời gian, diện tích, thể tích",
          "Hình tam giác, hình thang, hình tròn",
          "Tốc độ, quãng đường, thời gian"],
    "6": ["Tập hợp các số tự nhiên", "Số nguyên", "Phân số",
          "Số thập phân", "Hình học trực quan",
          "Tính đối xứng của hình phẳng", "Thống kê và xác suất"],
    "7": ["Số hữu tỉ", "Số thực", "Biểu thức đại số",
          "Đường thẳng và góc", "Tam giác",
          "Tỉ lệ thức và đại lượng tỉ lệ", "Thống kê"],
    "8": ["Phép nhân và phép chia đa thức", "Phân thức đại số",
          "Phương trình bậc nhất một ẩn", "Bất phương trình bậc nhất",
          "Tứ giác", "Tam giác đồng dạng",
          "Hình lăng trụ và hình chóp", "Thống kê"],
    "9": ["Căn bậc hai và căn bậc ba", "Hàm số bậc nhất",
          "Hệ phương trình bậc nhất hai ẩn", "Hàm số bậc hai",
          "Đường tròn", "Hình trụ, hình nón, hình cầu",
          "Xác suất"],
    "10": [
        "Mệnh đề và tập hợp",
        "Bất phương trình và hệ bất phương trình bậc nhất hai ẩn",
        "Hàm số và đồ thị",
        "Hàm số bậc hai",
        "Phương trình và hệ phương trình",
        "Bất đẳng thức và bất phương trình bậc hai",
        "Hệ thức lượng trong tam giác",
        "Vectơ",
        "Toạ độ và đường thẳng trong mặt phẳng toạ độ",
        "Thống kê mô tả và phân tích dữ liệu",
        "Xác suất của biến cố",
        "Đại số tổ hợp",
    ],
    "11": [
        "Hàm số lượng giác và phương trình lượng giác",
        "Quy tắc đếm và xác suất",
        "Dãy số, cấp số cộng, cấp số nhân",
        "Giới hạn và hàm số liên tục",
        "Đạo hàm và ứng dụng",
        "Quan hệ song song trong không gian",
        "Quan hệ vuông góc trong không gian",
        "Phép biến hình phẳng",
    ],
    "12": [
        "Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số",
        "Hàm số mũ và hàm số logarit",
        "Nguyên hàm và tích phân",
        "Ứng dụng tích phân",
        "Số phức",
        "Khối đa diện",
        "Mặt nón, mặt trụ, mặt cầu",
        "Phương pháp tọa độ trong không gian",
        "Thống kê và xác suất nâng cao",
    ],
}

class _DynamicTopicsProxy(dict):
    """Proxy dict that returns dynamic topics from chuongtrinhhoctap.txt, falling back to _FALLBACK_TOPICS."""
    def __getitem__(self, key):
        return get_topics_for_grade(str(key))
    def get(self, key, default=None):
        result = get_topics_for_grade(str(key))
        return result if result else (default or _FALLBACK_TOPICS.get(str(key), []))
    def __contains__(self, key):
        return str(key) in _FALLBACK_TOPICS

# Alias cho import ở dialog_quick_gen — uses dynamic data from chuongtrinhhoctap.txt
TOPICS_BY_GRADE = _DynamicTopicsProxy()

# ══════════════════════════════════════════════════════════════════════════════
#  BUILD MATRIX
# ══════════════════════════════════════════════════════════════════════════════

def get_available_durations() -> list[dict]:
    """Return list of available durations for the quick generator."""
    return [
        {"id": "15p", "label": "15 phút", "desc": "7 câu TN"},
        {"id": "45p", "label": "45 phút", "desc": "12 TN + 2 DS + 3 TLN"},
        {"id": "60p", "label": "60 phút", "desc": "15 TN + 3 DS + 4 TLN + 1 TL"},
        {"id": "90p", "label": "90 phút", "desc": "18 TN + 4 DS + 6 TLN + 2 TL"},
    ]


def get_topics_for_grade_old(grade: str) -> list[str]:
    """Keep old function for compatibility, but now uses dynamic."""
    return get_topics_for_grade(grade)


def build_quick_matrix(
    duration: str,
    grade: str = "12",
    topics: list[str] | None = None,
    subject: str = "Toán",
) -> MatrixData:
    """Build a random matrix for the given duration and topics.

    Parameters
    ----------
    duration : '15p' | '45p' | '60p' | '90p'
    grade : '10' | '11' | '12'
    topics : optional list of topic strings; if None, pick random from grade
    subject : subject name for title
    """
    from config import POINTS_MAP

    tpl = EXAM_TEMPLATES.get(duration)
    if not tpl:
        raise ValueError(f"Thời lượng không hỗ trợ: {duration}. Chọn: 15p, 45p, 60p, 90p")

    # Resolve topics
    available = get_topics_for_grade(grade)
    if not topics:
        # Pick 3–5 random topics
        n = min(len(available), random.randint(3, 5))
        topics = random.sample(available, n)
    else:
        # Filter valid topics, fallback to available
        topics = [t for t in topics if t in available] or topics

    title = f"{tpl['title_fmt']} {subject.upper()} {grade}"

    rows: list[MatrixRow] = []
    stt = 0

    for qtype, level, count in tpl["questions"]:
        if qtype == "DS" and level == "mixed":
            # DS: each question has 4 items (a-NB, b-TH, c-VD, d-VDC)
            for k in range(count):
                stt += 1
                topic = topics[(stt - 1) % len(topics)]
                ds_levels = ["NB", "TH", "VD", "VD"]
                items: list[DSItem] = []
                for idx, lv in enumerate(ds_levels):
                    label = chr(ord('a') + idx)
                    items.append(DSItem(
                        label=label, level=lv,
                        requirement=f"{topic} [{lv}]",
                        code=f"DS{stt}{label}",
                    ))
                lvl_order = {"NB": 0, "TH": 1, "VD": 2}
                top_lv = max(items, key=lambda x: lvl_order.get(x.level, 0)).level
                all_reqs = " | ".join(
                    f"ý {s.label} [{s.level}]: {s.requirement}" for s in items
                )
                rows.append(MatrixRow(
                    stt=str(stt), topic=topic, level=top_lv,
                    qtype="DS", codes=[s.code for s in items],
                    requirement=all_reqs,
                    points=POINTS_MAP.get("DS", 1.0),
                    enabled=True, ds_items=items,
                ))
        else:
            # TN / TLN / TL
            for k in range(count):
                stt += 1
                topic = topics[(stt - 1) % len(topics)]
                code = f"{qtype}{stt}"
                rows.append(MatrixRow(
                    stt=str(stt), topic=topic, level=level,
                    qtype=qtype, codes=[code],
                    requirement=f"{topic} [{level}]",
                    points=POINTS_MAP.get(qtype, 1.0),
                    enabled=True,
                ))

    return MatrixData(title=title, time_str=tpl["time_str"], rows=rows)


def build_quick_matrix_custom(
    n_tn: int = 0,
    n_ds: int = 0,
    n_tln: int = 0,
    n_tl: int = 0,
    time_str: str = "45 phút",
    grade: str = "12",
    topics: list[str] | None = None,
    subject: str = "Toán",
) -> MatrixData:
    """Build matrix với số lượng câu tùy chỉnh cho từng loại."""
    from config import POINTS_MAP

    available = get_topics_for_grade(grade)
    if not topics:
        n = min(len(available), random.randint(3, 5))
        topics = random.sample(available, n)
    else:
        topics = [t for t in topics if t in available] or topics

    title = f"KIỂM TRA {subject.upper()} {grade}"

    # Phân bổ TN theo mức độ: 40% NB, 35% TH, 25% VD
    tn_nb = max(1, round(n_tn * 0.40)) if n_tn > 0 else 0
    tn_th = max(1, round(n_tn * 0.35)) if n_tn > 1 else 0
    tn_vd = n_tn - tn_nb - tn_th

    # Phân bổ TLN theo mức độ
    tln_nb = max(1, n_tln // 3) if n_tln > 0 else 0
    tln_th = max(1, n_tln // 3) if n_tln > 1 else 0
    tln_vd = n_tln - tln_nb - tln_th

    questions: list[tuple[str, str, int]] = []
    if tn_nb > 0: questions.append(("TN", "NB", tn_nb))
    if tn_th > 0: questions.append(("TN", "TH", tn_th))
    if tn_vd > 0: questions.append(("TN", "VD", tn_vd))
    if n_ds > 0:  questions.append(("DS", "mixed", n_ds))
    if tln_nb > 0: questions.append(("TLN", "NB", tln_nb))
    if tln_th > 0: questions.append(("TLN", "TH", tln_th))
    if tln_vd > 0: questions.append(("TLN", "VD", tln_vd))
    if n_tl > 0:  questions.append(("TL", "VD", n_tl))

    rows: list[MatrixRow] = []
    stt = 0

    for qtype, level, count in questions:
        if qtype == "DS" and level == "mixed":
            for k in range(count):
                stt += 1
                topic = topics[(stt - 1) % len(topics)]
                ds_levels = ["NB", "TH", "VD", "VD"]
                items: list[DSItem] = []
                for idx, lv in enumerate(ds_levels):
                    label = chr(ord('a') + idx)
                    items.append(DSItem(
                        label=label, level=lv,
                        requirement=f"{topic} [{lv}]",
                        code=f"DS{stt}{label}",
                    ))
                lvl_order = {"NB": 0, "TH": 1, "VD": 2}
                top_lv = max(items, key=lambda x: lvl_order.get(x.level, 0)).level
                all_reqs = " | ".join(
                    f"ý {s.label} [{s.level}]: {s.requirement}" for s in items
                )
                rows.append(MatrixRow(
                    stt=str(stt), topic=topic, level=top_lv,
                    qtype="DS", codes=[s.code for s in items],
                    requirement=all_reqs,
                    points=POINTS_MAP.get("DS", 1.0),
                    enabled=True, ds_items=items,
                ))
        else:
            for k in range(count):
                stt += 1
                topic = topics[(stt - 1) % len(topics)]
                code = f"{qtype}{stt}"
                rows.append(MatrixRow(
                    stt=str(stt), topic=topic, level=level,
                    qtype=qtype, codes=[code],
                    requirement=f"{topic} [{level}]",
                    points=POINTS_MAP.get(qtype, 1.0),
                    enabled=True,
                ))

    return MatrixData(title=title, time_str=time_str, rows=rows)