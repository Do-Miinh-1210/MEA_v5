"""
services/adaptive_prompt.py — Phase 5: Prompt tự cải thiện.

Dùng feedback từ smart_db để:
1. Inject bad patterns vào prompt (Avoid mistakes like...)
2. Lấy câu tốt nhất làm few-shot examples từ ngân hàng
3. Điều chỉnh temperature theo quality history
"""
from __future__ import annotations
from typing import Optional
from core.models import MatrixRow


def build_adaptive_prefix(row: MatrixRow, topic: str = "") -> str:
    """
    Tạo prefix thông minh cho prompt dựa trên lịch sử feedback.
    Được inject vào đầu prompt trước khi gửi AI.
    """
    parts = []
    try:
        from storage.smart_db import get_bad_patterns, get_good_examples
        # Bad patterns
        bad = get_bad_patterns(topic=topic or row.topic, limit=5)
        if bad:
            parts.append("TRÁNH các lỗi phổ biến từ lịch sử: " + "; ".join(bad))

        # Good examples từ ngân hàng (few-shot thực tế)
        good = get_good_examples(qtype=row.qtype, level=row.level,
                                  topic=topic or row.topic, limit=2)
        if good:
            ex_lines = []
            for ex in good:
                ex_lines.append(f"Ví dụ câu tốt ({ex.get('_quality_score',0):.2f} điểm):")
                ex_lines.append(ex.get("question","")[:150])
            parts.append("\n".join(ex_lines))
    except Exception:
        pass  # Smart DB chưa có dữ liệu → bỏ qua

    return "\n".join(parts) + "\n" if parts else ""


def get_adaptive_temperature(
    qtype: str,
    level: str,
    topic: str = "",
    default: float = 0.45,
) -> float:
    """
    Điều chỉnh temperature dựa trên lịch sử chất lượng câu hỏi cùng loại.
    - quality_score thấp → giảm temperature (ít sáng tạo hơn, ổn định hơn)
    - quality_score cao → tăng nhẹ (khuyến khích đa dạng)
    """
    try:
        from storage.smart_db import smart_search
        recent = smart_search(qtype=qtype, level=level, topic=topic,
                               min_score=0.0, valid_only=False,
                               order_by="created_at DESC", limit=20)
        scores = [r["_quality_score"] for r in recent if r.get("_quality_score") is not None]
        if not scores:
            return default
        avg = sum(scores) / len(scores)
        if avg < 0.7:
            return max(0.2, default - 0.15)   # Ổn định hơn
        elif avg > 0.9:
            return min(0.7, default + 0.1)    # Khuyến khích đa dạng
        return default
    except Exception:
        return default


def extract_patterns_from_feedback() -> dict:
    """
    Phân tích feedback để rút ra bad/good patterns tự động.
    Chạy định kỳ (ví dụ: khi lưu phiên).
    Returns: {"bad": [patterns], "good": [patterns]}
    """
    bad_patterns = []
    good_patterns = []
    try:
        from storage.smart_db import _get_con, update_patterns
        with _get_con() as con:
            edits = con.execute(
                "SELECT old_data, new_data, question_id FROM feedback WHERE action='edit' LIMIT 100"
            ).fetchall()
        for row in edits:
            try:
                import json
                old = json.loads(row["old_data"]) if row["old_data"] else {}
                new = json.loads(row["new_data"]) if row["new_data"] else {}
                old_q = old.get("question", "")
                new_q = new.get("question", "")
                # Nếu câu hỏi bị sửa nhiều → likely bad pattern
                if old_q and new_q and old_q != new_q:
                    # Tìm từ/cụm từ bị thay thế
                    words_old = set(old_q.split()[:10])
                    words_new = set(new_q.split()[:10])
                    removed = words_old - words_new
                    if removed:
                        pattern = " ".join(list(removed)[:3])
                        bad_patterns.append(pattern)
                        update_patterns(pattern, "bad")
                # Câu accepted → good pattern
                old_ans = old.get("answer","")
                new_ans = new.get("answer","")
                if old_ans and old_ans == new_ans:
                    good_patterns.append(f"answer={old_ans}")
                    update_patterns(f"answer={old_ans}", "good")
            except Exception:
                continue
    except Exception:
        pass
    return {"bad": bad_patterns[:10], "good": good_patterns[:5]}
