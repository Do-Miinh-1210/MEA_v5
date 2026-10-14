"""
services/adaptive_prompts.py — [SMART-2] Prompt theo (lớp, môn, chủ đề).

Chỉ là registry các "style hint" — đoạn text ngắn (50-300 ký tự) inject
vào prompt cuối, KHÔNG thay thế prompt chính.

Cấu trúc rule:
    {
        "name":    "Tên rule (debug)",
        "grade":   ["10", "11", "12"] hoặc None (mọi lớp),
        "subject": ["Toán", "Lý"] hoặc None (mọi môn),
        "topic_keywords": ["đạo hàm", "cực trị"],  # OR — match nếu chứa 1 từ
        "hint":    "Đoạn text inject vào prompt",
        "priority": int (cao hơn = match trước nếu nhiều rule),
    }

Lookup: trả về hint TỐT NHẤT khớp (priority cao nhất, hoặc trống nếu không khớp).
"""

from __future__ import annotations
import logging
import re
from typing import Optional

_log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════
#  RULES — sorted by priority (cao → thấp) trong list
# ══════════════════════════════════════════════════════════════════════════

_RULES: list[dict] = [
    # ─────────── TOÁN 12 ───────────
    {
        "name":     "Toán 12 — Đạo hàm & khảo sát hàm số",
        "grade":    ["12"],
        "subject":  ["Toán"],
        "topic_keywords": [
            "đạo hàm", "cực trị", "đơn điệu", "tiệm cận",
            "khảo sát hàm", "đồ thị hàm", "biến thiên",
        ],
        "priority": 100,
        "hint": (
            "PHONG CÁCH (Toán 12 — Đạo hàm):\n"
            "  • Câu NB: đọc trực tiếp từ BBT hoặc đồ thị có sẵn.\n"
            "  • Câu TH: 2-3 bước biến đổi, dùng đạo hàm bậc 1.\n"
            "  • Câu VD: BÀI TOÁN CÓ THAM SỐ m, tìm m để hàm có cực trị / đơn điệu /\n"
            "    đồ thị qua điểm cho trước. Hoặc bài toán THỰC TẾ tối ưu hoá\n"
            "    (chi phí thấp nhất, lợi nhuận cao nhất, diện tích lớn nhất).\n"
            "  • LUÔN có hình vẽ BBT hoặc đồ thị cho câu khảo sát.\n"
        ),
    },
    {
        "name":     "Toán 12 — Tích phân & ứng dụng",
        "grade":    ["12"],
        "subject":  ["Toán"],
        "topic_keywords": [
            "tích phân", "nguyên hàm", "diện tích hình phẳng",
            "thể tích vật thể", "khối tròn xoay",
        ],
        "priority": 100,
        "hint": (
            "PHONG CÁCH (Toán 12 — Tích phân):\n"
            "  • Câu NB: bảng nguyên hàm cơ bản (x^n, e^x, sin x, cos x).\n"
            "  • Câu TH: đổi biến số đơn giản (u = ...) hoặc tích phân từng phần.\n"
            "  • Câu VD: diện tích hình phẳng giới hạn bởi 2 đường y=f(x), y=g(x);\n"
            "    thể tích khối tròn xoay quanh trục Ox.\n"
            "  • Đáp án TLN: dùng dấu PHẨY thập phân VN, làm tròn 2 chữ số.\n"
        ),
    },
    {
        "name":     "Toán 12 — Số phức",
        "grade":    ["12"],
        "subject":  ["Toán"],
        "topic_keywords": ["số phức", "mô-đun", "argument", "tập hợp điểm"],
        "priority": 100,
        "hint": (
            "PHONG CÁCH (Toán 12 — Số phức):\n"
            "  • Câu NB: phần thực / phần ảo / mô-đun của số phức.\n"
            "  • Câu TH: phép toán +/-/× với số phức.\n"
            "  • Câu VD: bài toán quỹ tích / tập hợp điểm biểu diễn trên mp phức,\n"
            "    hoặc giá trị lớn nhất / nhỏ nhất của |z + a|.\n"
        ),
    },
    {
        "name":     "Toán 12 — Hình không gian Oxyz",
        "grade":    ["12"],
        "subject":  ["Toán"],
        "topic_keywords": [
            "tọa độ", "toạ độ", "không gian Oxyz", "oxyz",
            "phương trình mặt phẳng", "phương trình đường thẳng",
            "mặt cầu", "phương trình mặt cầu",
        ],
        "priority": 100,
        "hint": (
            "PHONG CÁCH (Toán 12 — Hình không gian Oxyz):\n"
            "  • Câu NB: tọa độ điểm, vector cơ bản; PT mặt phẳng dạng Ax+By+Cz+D=0.\n"
            "  • Câu TH: viết PT mặt phẳng / đường thẳng / mặt cầu qua dữ kiện cụ thể.\n"
            "  • Câu VD: khoảng cách từ điểm đến mặt phẳng / đường thẳng; góc;\n"
            "    bài toán cực trị (M, N thoả ràng buộc, tìm M, N để khoảng cách\n"
            "    nhỏ nhất / lớn nhất).\n"
            "  • Hình không gian dùng phép chiếu cabinet trong TikZ.\n"
        ),
    },
    {
        "name":     "Toán 12 — Khối đa diện / Mặt tròn xoay",
        "grade":    ["12"],
        "subject":  ["Toán"],
        "topic_keywords": [
            "khối đa diện", "lăng trụ", "hình chóp", "khối chóp", "thể tích",
            "mặt cầu", "mặt nón", "mặt trụ", "hình nón", "hình trụ", "hình cầu",
        ],
        "priority": 95,
        "hint": (
            "PHONG CÁCH (Toán 12 — Hình không gian thể tích):\n"
            "  • Câu NB: công thức V cơ bản (chóp = 1/3 × đáy × cao).\n"
            "  • Câu TH: thể tích chóp / lăng trụ với dữ kiện rõ ràng.\n"
            "  • Câu VD: tỉ số thể tích 2 khối; khoảng cách phức tạp.\n"
            "  • Hình vẽ TikZ luôn dùng cabinet 30°, cạnh khuất dashed.\n"
        ),
    },
    # ─────────── TOÁN 11 ───────────
    {
        "name":     "Toán 11 — Lượng giác",
        "grade":    ["11"],
        "subject":  ["Toán"],
        "topic_keywords": ["lượng giác", "sin", "cos", "tan", "cot",
                            "phương trình lượng giác"],
        "priority": 100,
        "hint": (
            "PHONG CÁCH (Toán 11 — Lượng giác):\n"
            "  • Câu NB: tập xác định, tập giá trị, chu kỳ hàm cơ bản.\n"
            "  • Câu TH: phương trình sin x = m / cos x = m / tan x = m;\n"
            "    biến đổi công thức cộng / nhân đôi / hạ bậc.\n"
            "  • Câu VD: phương trình lượng giác BẬC 2 đối với 1 hàm (vd: 2sin²x − 3sinx + 1 = 0);\n"
            "    hoặc bài toán THỰC TẾ (dao động, sóng).\n"
            "  • Tránh phương trình quá phức tạp dạng đề thi tốt nghiệp.\n"
        ),
    },
    {
        "name":     "Toán 11 — Dãy số / Cấp số",
        "grade":    ["11"],
        "subject":  ["Toán"],
        "topic_keywords": ["dãy số", "cấp số cộng", "cấp số nhân", "csc", "csn"],
        "priority": 100,
        "hint": (
            "PHONG CÁCH (Toán 11 — Dãy số):\n"
            "  • Câu NB: nhận biết CSC / CSN; công thức số hạng tổng quát.\n"
            "  • Câu TH: tính tổng n số hạng đầu; số hạng thứ k cho trước u1 + d/q.\n"
            "  • Câu VD: BÀI TOÁN THỰC TẾ — lãi kép, tăng trưởng dân số,\n"
            "    chuỗi sinh học (tế bào nhân đôi).\n"
        ),
    },
    {
        "name":     "Toán 11 — Giới hạn / Liên tục",
        "grade":    ["11"],
        "subject":  ["Toán"],
        "topic_keywords": ["giới hạn", "liên tục", "vô cùng"],
        "priority": 95,
        "hint": (
            "PHONG CÁCH (Toán 11 — Giới hạn):\n"
            "  • Câu NB: nhận biết giới hạn dạng a/b cơ bản; định nghĩa liên tục.\n"
            "  • Câu TH: tính giới hạn dạng 0/0, ∞/∞ — đặt nhân tử chung / liên hợp.\n"
            "  • Câu VD: tìm m để hàm số liên tục tại x₀;\n"
            "    giới hạn lượng giác sin x / x.\n"
        ),
    },
    {
        "name":     "Toán 11 — Quan hệ song song / vuông góc",
        "grade":    ["11"],
        "subject":  ["Toán"],
        "topic_keywords": [
            "song song", "vuông góc", "quan hệ song song", "quan hệ vuông góc",
            "thiết diện", "giao tuyến",
        ],
        "priority": 95,
        "hint": (
            "PHONG CÁCH (Toán 11 — Hình không gian):\n"
            "  • Câu NB: nhận biết 2 đường thẳng song song / chéo nhau / cắt nhau.\n"
            "  • Câu TH: chứng minh đường // mặt; mặt // mặt; ⊥.\n"
            "  • Câu VD: bài toán DỰNG GIAO TUYẾN / THIẾT DIỆN — yêu cầu vẽ hình.\n"
            "  • Bắt buộc kèm TikZ cabinet projection 3D.\n"
        ),
    },
    # ─────────── TOÁN 10 ───────────
    {
        "name":     "Toán 10 — Mệnh đề / Tập hợp",
        "grade":    ["10"],
        "subject":  ["Toán"],
        "topic_keywords": ["mệnh đề", "tập hợp", "phủ định", "tập con", "phép hợp"],
        "priority": 100,
        "hint": (
            "PHONG CÁCH (Toán 10 — Mệnh đề & tập hợp):\n"
            "  • Câu NB: ngôn ngữ ĐƠN GIẢN, ví dụ đời sống.\n"
            "  • Tránh ký hiệu logic phức tạp ∀ ∃ — dùng từ 'mọi', 'tồn tại'.\n"
            "  • Câu TH: phép hợp / giao / hiệu của tập hợp số.\n"
            "  • Câu VD: bài toán dạng 'có bao nhiêu HS biết tiếng Anh hoặc Pháp'.\n"
        ),
    },
    {
        "name":     "Toán 10 — Hàm số / Đồ thị",
        "grade":    ["10"],
        "subject":  ["Toán"],
        "topic_keywords": [
            "hàm số", "đồ thị", "hàm bậc hai", "parabol",
            "hàm bậc nhất", "đường thẳng",
        ],
        "priority": 95,
        "hint": (
            "PHONG CÁCH (Toán 10 — Hàm số):\n"
            "  • Câu NB: tập xác định; tính chẵn / lẻ; đọc đồ thị cho sẵn.\n"
            "  • Câu TH: vẽ + biện luận đồ thị parabol; tìm đỉnh, trục đối xứng.\n"
            "  • Câu VD: tham số m để parabol đi qua điểm / cắt trục / có 2 nghiệm.\n"
            "  • Câu hỏi tránh dùng LaTeX phức như \\sum, \\int — đơn giản dạng ax²+bx+c.\n"
        ),
    },
    {
        "name":     "Toán 10 — Bất phương trình hai ẩn / Tối ưu",
        "grade":    ["10"],
        "subject":  ["Toán"],
        "topic_keywords": ["bất phương trình bậc nhất hai ẩn", "miền nghiệm",
                            "tối ưu"],
        "priority": 95,
        "hint": (
            "PHONG CÁCH (Toán 10 — Bất phương trình hai ẩn):\n"
            "  • Câu NB: nhận biết miền nghiệm 1 bất phương trình.\n"
            "  • Câu TH: vẽ miền nghiệm của hệ.\n"
            "  • Câu VD: BÀI TOÁN TỐI ƯU thực tế — phân bổ tài nguyên,\n"
            "    sản xuất, lập kế hoạch (yêu cầu vẽ miền + tìm GTLN của f = ax+by).\n"
        ),
    },
    # ─────────── THCS (lớp 6-9) ───────────
    {
        "name":     "Toán 8 — Phân tích đa thức / Phân thức",
        "grade":    ["8"],
        "subject":  ["Toán"],
        "topic_keywords": ["đa thức", "phân thức", "hằng đẳng thức"],
        "priority": 90,
        "hint": (
            "PHONG CÁCH (Toán 8 — Đại số):\n"
            "  • Dùng số nguyên / phân số đơn giản — TRÁNH số thập phân vô tỉ.\n"
            "  • Câu NB: nhận biết hạng tử / nhân tử / 7 hằng đẳng thức.\n"
            "  • Câu TH: phân tích thành nhân tử bằng cách 1 trong 7 hằng đẳng thức.\n"
            "  • Câu VD: rút gọn biểu thức phân thức + điều kiện xác định.\n"
        ),
    },
    {
        "name":     "Toán 9 — Căn bậc hai / Hàm bậc nhất",
        "grade":    ["9"],
        "subject":  ["Toán"],
        "topic_keywords": ["căn bậc hai", "căn bậc ba", "hàm bậc nhất"],
        "priority": 90,
        "hint": (
            "PHONG CÁCH (Toán 9):\n"
            "  • Câu NB: điều kiện tồn tại căn; căn của số dương.\n"
            "  • Câu TH: rút gọn biểu thức chứa căn 1-2 bước.\n"
            "  • Câu VD: bài toán bằng hệ phương trình (chuyển động, năng suất).\n"
            "  • Ngôn ngữ ngắn gọn, dữ kiện rõ ràng, tránh từ chuyên ngành.\n"
        ),
    },
    {
        "name":     "Toán 9 — Đường tròn",
        "grade":    ["9"],
        "subject":  ["Toán"],
        "topic_keywords": ["đường tròn", "tiếp tuyến", "dây cung", "tâm"],
        "priority": 90,
        "hint": (
            "PHONG CÁCH (Toán 9 — Đường tròn):\n"
            "  • Câu NB: định nghĩa tâm / bán kính / đường kính / dây cung.\n"
            "  • Câu TH: vị trí tương đối đường thẳng - đường tròn / 2 đường tròn.\n"
            "  • Câu VD: tiếp tuyến chung; bài toán dựng hình + chứng minh.\n"
            "  • Luôn có TikZ vẽ đường tròn, dây, tiếp tuyến.\n"
        ),
    },
    # ─────────── VẬT LÝ ───────────
    {
        "name":     "Lý 11 — Sóng / Dao động",
        "grade":    ["11"],
        "subject":  ["Lý", "Vật lý"],
        "topic_keywords": ["sóng", "dao động", "dao động điều hòa",
                            "con lắc", "lò xo"],
        "priority": 100,
        "hint": (
            "PHONG CÁCH (Lý 11 — Sóng & dao động):\n"
            "  • Công thức cơ bản: T = 2π√(m/k); ω = √(k/m); f = 1/T.\n"
            "  • Phương trình DĐĐH: x = A·cos(ωt + φ).\n"
            "  • Câu NB: nhận biết biên độ / pha / tần số.\n"
            "  • Câu TH: tính chu kỳ / tần số khi biết m, k.\n"
            "  • Câu VD: bài toán năng lượng / quãng đường trong thời gian t.\n"
            "  • Đáp án TLN: làm tròn theo đơn vị SI.\n"
        ),
    },
]


# ══════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════════════

def get_adaptive_hint(
    subject: str,
    grade: str,
    topic: str,
    requirement: str = "",
) -> str:
    """[SMART-2] Trả về style hint phù hợp nhất với (subject, grade, topic).

    Trả "" nếu không có rule khớp — caller dùng prompt mặc định.
    Lookup: filter theo grade + subject trước, sau đó match topic_keywords
    (case-insensitive trong topic + requirement). Pick rule có priority cao
    nhất nếu nhiều match.
    """
    if not (grade or subject):
        return ""

    grade_str = str(grade).strip()
    subject_norm = (subject or "").strip().lower()
    topic_lower = (topic or "").lower()
    req_lower = (requirement or "").lower()
    haystack = topic_lower + " " + req_lower

    matches: list[tuple[int, dict]] = []
    for rule in _RULES:
        # Filter grade
        rule_grades = rule.get("grade")
        if rule_grades and grade_str not in rule_grades:
            continue
        # Filter subject (case-insensitive)
        rule_subjects = rule.get("subject")
        if rule_subjects:
            if not any(s.lower() == subject_norm
                       or s.lower() in subject_norm
                       or subject_norm in s.lower()
                       for s in rule_subjects):
                continue
        # Filter topic keywords
        kws = rule.get("topic_keywords", [])
        if kws:
            if not any(kw.lower() in haystack for kw in kws):
                continue
        matches.append((rule.get("priority", 0), rule))

    if not matches:
        return ""

    # Pick highest priority
    matches.sort(key=lambda t: t[0], reverse=True)
    best = matches[0][1]
    _log.debug(
        "Adaptive prompt: matched rule '%s' for %s lớp %s — %s",
        best.get("name"), subject, grade, topic[:40],
    )
    return best.get("hint", "")


def list_rules() -> list[dict]:
    """Debug helper — trả về tất cả rules (không deep-copy)."""
    return list(_RULES)


def count_rules_for_grade(grade: str) -> int:
    """Số rule áp dụng cho grade cụ thể (debug / coverage stats)."""
    grade_str = str(grade).strip()
    return sum(
        1 for r in _RULES
        if not r.get("grade") or grade_str in r["grade"]
    )
