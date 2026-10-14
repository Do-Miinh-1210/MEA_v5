"""
core/smart_prompt.py — Smart Prompt: phân tích yêu cầu tự nhiên thành ma trận đề.
GV chỉ cần nhập: "Tạo đề 1 tiết Toán 9 chương 2" → hệ thống tự xác định:
  - Thời lượng (15p/45p/60p/90p)
  - Lớp
  - Chương/chủ đề
  - Số câu theo mức độ
"""
from __future__ import annotations

import copy
import re
from typing import Optional

from core.models import MatrixData, MatrixRow
from config import POINTS_MAP
from core.quick_matrix import (
    build_quick_matrix,
    build_quick_matrix_custom,
    get_topics_for_grade,
    EXAM_TEMPLATES,
)


# ══════════════════════════════════════════════════════════════════════════════
#  PATTERN MATCHING — phân tích yêu cầu tiếng Việt
# ══════════════════════════════════════════════════════════════════════════════

_DURATION_PATTERNS = {
    "15p": [r"15\s*p", r"15\s*phút", r"kiểm tra miệng"],
    "45p": [r"45\s*p", r"45\s*phút", r"1\s*tiết", r"một\s*tiết", r"kt\s*1\s*tiết"],
    "60p": [r"60\s*p", r"60\s*phút", r"giữa\s*k[ìi]", r"giữa\s*hk", r"gk"],
    "90p": [r"90\s*p", r"90\s*phút", r"cuối\s*k[ìi]", r"cuối\s*hk", r"ck",
            r"h[ọo]c\s*k[ìi]"],
}

_GRADE_PATTERN = re.compile(
    r"(?:lớp|lop|l|khối|khoi)\s*(\d{1,2})",
    re.IGNORECASE,
)

_CHAPTER_PATTERN = re.compile(
    r"(?:chương|ch|chapter)\s*(\d+)",
    re.IGNORECASE,
)

_TOPIC_KEYWORDS = re.compile(
    r"(?:về|chủ đề|chủ_đề|topic)\s+(.+?)(?:\s*,|\s*$)",
    re.IGNORECASE,
)

_COUNT_PATTERNS = {
    "TN": re.compile(r"(\d+)\s*(?:câu\s*)?(?:trắc nghiệm|tn(?!l)|npa)", re.IGNORECASE),
    "DS": re.compile(r"(\d+)\s*(?:câu\s*)?(?:đúng.?sai|ds)", re.IGNORECASE),
    "TLN": re.compile(r"(\d+)\s*(?:câu\s*)?(?:trả lời ngắn|tln)", re.IGNORECASE),
    "TL": re.compile(r"(\d+)\s*(?:câu\s*)?(?:tự luận|tl(?!n))", re.IGNORECASE),
}

_SEMESTER_PATTERN = re.compile(
    r"(?:học kì|hk|kì|ki)\s*(\d)",
    re.IGNORECASE,
)


def parse_smart_prompt(text: str) -> dict:
    """Phân tích chuỗi yêu cầu tự nhiên.

    Returns:
        dict với các key:
        - duration: str | None  ("15p"/"45p"/"60p"/"90p")
        - grade: str | None     ("10"/"11"/"12"/...)
        - chapter: int | None   (số chương)
        - topics: list[str]     (danh sách chủ đề detected)
        - counts: dict          ({"TN": n, "DS": n, "TLN": n, "TL": n})
        - semester: str | None  ("1"/"2")
        - subject: str          ("Toán")
    """
    text_lower = text.lower().strip()

    # 1. Duration
    duration = None
    for dur_id, patterns in _DURATION_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                duration = dur_id
                break
        if duration:
            break

    # 2. Grade
    grade = None
    m = _GRADE_PATTERN.search(text)
    if m:
        grade = m.group(1)
    else:
        # Heuristic: "toán 9", "toán 12"
        m2 = re.search(r"toán\s*(\d{1,2})", text_lower)
        if m2:
            grade = m2.group(1)

    # 3. Chapter
    chapter = None
    m = _CHAPTER_PATTERN.search(text)
    if m:
        chapter = int(m.group(1))

    # 4. Topics (explicit)
    topics: list[str] = []
    m = _TOPIC_KEYWORDS.search(text)
    if m:
        raw = m.group(1).strip()
        topics = [t.strip() for t in raw.split(",") if t.strip()]

    # 5. Question counts (explicit)
    counts: dict[str, int] = {}
    for qtype, pat in _COUNT_PATTERNS.items():
        m = pat.search(text)
        if m:
            counts[qtype] = int(m.group(1))

    # 6. Semester
    semester = None
    m = _SEMESTER_PATTERN.search(text)
    if m:
        semester = m.group(1)

    # 7. Subject (chỉ hỗ trợ Toán hiện tại)
    subject = "Toán"

    return {
        "duration": duration,
        "grade": grade,
        "chapter": chapter,
        "topics": topics,
        "counts": counts,
        "semester": semester,
        "subject": subject,
    }


def smart_prompt_to_matrix(text: str) -> tuple[MatrixData, dict]:
    """Chuyển yêu cầu tự nhiên thành MatrixData.

    Returns:
        (MatrixData, parsed_info)
    """
    info = parse_smart_prompt(text)

    grade = info["grade"] or "12"
    duration = info["duration"] or "45p"
    subject = info["subject"]

    # Resolve topics
    available = get_topics_for_grade(grade)
    topics = info["topics"]

    # Nếu có chapter, lọc topics theo chapter
    if info["chapter"] and available:
        chapter_str = f"chương {info['chapter']}"
        chapter_str2 = f"ch.{info['chapter']}"
        filtered = [
            t for t in available
            if chapter_str in t.lower() or chapter_str2 in t.lower()
               or f"chương {info['chapter']}" in t.lower()
        ]
        if filtered:
            topics = filtered

    # Nếu có counts cụ thể → dùng custom matrix
    if info["counts"]:
        matrix = build_quick_matrix_custom(
            n_tn=info["counts"].get("TN", 0),
            n_ds=info["counts"].get("DS", 0),
            n_tln=info["counts"].get("TLN", 0),
            n_tl=info["counts"].get("TL", 0),
            time_str=EXAM_TEMPLATES.get(duration, {}).get("time_str", "45 phút"),
            grade=grade,
            topics=topics or None,
            subject=subject,
        )
    else:
        matrix = build_quick_matrix(
            duration=duration,
            grade=grade,
            topics=topics or None,
            subject=subject,
        )

    return matrix, info


# ══════════════════════════════════════════════════════════════════════════════
#  AI-POWERED SMART PROMPT (dùng AI để hiểu yêu cầu phức tạp)
# ══════════════════════════════════════════════════════════════════════════════

_AI_PARSE_PROMPT = """\
Bạn là hệ thống phân tích yêu cầu tạo đề kiểm tra Toán.
Phân tích yêu cầu sau và trả về JSON:

YÊU CẦU: {text}

Trả về ĐÚNG format JSON (không thêm gì khác):
{{
  "duration": "45p",
  "grade": "12",
  "chapter": null,
  "topics": [],
  "counts": {{"TN": 12, "DS": 2, "TLN": 3, "TL": 1}},
  "semester": "1",
  "subject": "Toán"
}}

Quy tắc:
- duration: "15p" | "45p" | "60p" | "90p"
- grade: "1"-"12"
- chapter: số chương hoặc null
- topics: list chủ đề cụ thể, rỗng nếu không rõ
- counts: số câu mỗi loại, null nếu dùng mặc định theo duration
- semester: "1" | "2" | null
"""


def smart_prompt_with_ai(
    text: str,
    ai_call=None,
) -> tuple[MatrixData, dict]:
    """Dùng AI để phân tích yêu cầu phức tạp, fallback sang regex."""
    # Thử regex trước
    info = parse_smart_prompt(text)

    # Nếu regex đã đủ thông tin → dùng luôn
    if info["duration"] and info["grade"]:
        return smart_prompt_to_matrix(text)

    # Nếu có AI → thử AI parse
    if ai_call:
        try:
            import json
            prompt = _AI_PARSE_PROMPT.replace("{text}", text)
            raw = ai_call(prompt)
            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
            if json_match:
                ai_info = json.loads(json_match.group())
                # Merge AI result with regex result (regex takes priority for non-None)
                for k, v in ai_info.items():
                    if v is not None and not info.get(k):
                        info[k] = v
        except Exception:
            pass

    # Build matrix from merged info
    grade = info.get("grade") or "12"
    duration = info.get("duration") or "45p"
    topics = info.get("topics") or None

    if info.get("counts"):
        counts = info["counts"]
        matrix = build_quick_matrix_custom(
            n_tn=counts.get("TN", 0),
            n_ds=counts.get("DS", 0),
            n_tln=counts.get("TLN", 0),
            n_tl=counts.get("TL", 0),
            time_str=EXAM_TEMPLATES.get(duration, {}).get("time_str", "45 phút"),
            grade=grade,
            topics=topics,
            subject=info.get("subject", "Toán"),
        )
    else:
        matrix = build_quick_matrix(
            duration=duration, grade=grade, topics=topics,
            subject=info.get("subject", "Toán"),
        )

    return matrix, info


# ══════════════════════════════════════════════════════════════════════════
#  [SMART-5] Follow-up: chỉnh ma trận hiện có bằng natural language
# ══════════════════════════════════════════════════════════════════════════

_FOLLOWUP_PROMPT = """\
Bạn đang trong session điều chỉnh ma trận đề kiểm tra.

═══════════════════════════════════════════════════════════════════════
MA TRẬN HIỆN TẠI:
{matrix_dump}

═══════════════════════════════════════════════════════════════════════
YÊU CẦU CỦA GIÁO VIÊN (LẦN NÀY):
{followup}

═══════════════════════════════════════════════════════════════════════
NHIỆM VỤ:
Phân tích yêu cầu trên và TRẢ MỘT JSON DUY NHẤT mô tả thao tác cần làm.
KHÔNG giải thích bằng văn bản — chỉ JSON.

Cấu trúc JSON:
{{
  "action": "add" | "remove" | "modify" | "replace_all",
  "added":  [
    {{"qtype": "TN|DS|TLN|TL",
      "level": "NB|TH|VD",
      "topic": "<chủ đề>",
      "requirement": "<yêu cầu cần đạt>",
      "points": 0.25
     }}
  ],
  "removed_indices": [<int>],
  "modify": [
    {{"stt": <int>, "field": "qtype|level|topic|requirement|points",
      "new_value": "<value>"}}
  ]
}}

Hướng dẫn ánh xạ YÊU CẦU → action:
  • "Thêm N câu về X mức độ Y" → action="add", added=[N câu]
  • "Xoá câu N" → action="remove", removed_indices=[N]
  • "Đổi câu N sang TN" → action="modify", modify=[{{stt:N, field:"qtype", new_value:"TN"}}]
  • "Tăng độ khó câu N" → action="modify", modify=[{{stt:N, field:"level", new_value:"VD"}}]
  • "Tạo lại ma trận với X câu Y" → action="replace_all", added=[X câu Y]

CHỈ trả JSON. Không thêm markdown fence ```. Không thêm lời mở.
"""


def followup_modify_matrix(
    current_matrix: MatrixData,
    followup_text: str,
    ai_call,
    subject: str = "Toán",
    grade: str = "12",
) -> tuple[MatrixData, str]:
    """[SMART-5] Áp dụng follow-up request lên matrix hiện tại.

    Returns
    -------
    (new_matrix, message) — message để hiển thị status cho user.
    Raise ValueError nếu AI không trả JSON hợp lệ.
    """
    import json
    if not ai_call:
        raise ValueError("Cần ai_call để xử lý follow-up")

    # Serialize ma trận hiện tại (gọn)
    def _dump_matrix(m: MatrixData) -> str:
        lines = [f"Title: {m.title}", f"Time:  {m.time_str}",
                 f"Số câu: {len(m.rows)}"]
        for i, r in enumerate(m.rows, 1):
            lines.append(
                f"  #{i}. [{r.qtype}/{r.level}] {r.topic} "
                f"({r.points}đ) — {r.requirement[:60]}"
            )
        return "\n".join(lines)

    matrix_dump = dump_matrix_brief(current_matrix)
    prompt = _FOLLOWUP_PROMPT.format(
        matrix_dump=matrix_dump, followup=followup_text)
    raw = ai_call(prompt) or ""

    # Strip markdown fence
    raw = re.sub(r"^```\w*\s*", "", raw.strip())
    raw = re.sub(r"\s*```\s*$", "", raw)

    m = re.search(r"\{[\s\S]*\}", raw)
    if not m:
        raise ValueError(f"AI không trả JSON. Raw:\n{raw[:200]}")
    try:
        data = json.loads(m.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON không hợp lệ: {e}\nRaw:\n{raw[:200]}")

    action = (data.get("action") or "").lower().strip()
    new_rows = [copy.deepcopy(r) for r in current_matrix.rows]

    def _make_row(spec: dict, stt: int) -> MatrixRow:
        qtype = spec.get("qtype", "TN").upper()
        level = spec.get("level", "TH").upper()
        topic = (spec.get("topic") or "").strip()
        req = (spec.get("requirement") or f"{topic} [{level}]").strip()
        points = float(spec.get("points") or POINTS_MAP.get(qtype, 0.25))
        return MatrixRow(
            stt=str(stt), topic=topic, level=level, qtype=qtype,
            codes=[f"{qtype}{stt}"], requirement=req, points=points,
            enabled=True,
        )

    msg_parts: list[str] = []

    if action == "replace_all":
        added = data.get("added", []) or []
        if not added:
            raise ValueError("action=replace_all nhưng 'added' rỗng")
        new_rows = [_make_row(s, i) for i, s in enumerate(added, 1)]
        msg_parts.append(f"🔁 Thay toàn bộ — {len(new_rows)} câu")
    else:
        # REMOVE (sort desc để index không lệch)
        removed_idx = sorted(set(data.get("removed_indices") or []),
                              reverse=True)
        if removed_idx:
            for idx in removed_idx:
                if 1 <= idx <= len(new_rows):
                    new_rows.pop(idx - 1)
            msg_parts.append(f"🗑️ Xoá {len(removed_idx)} câu")

        # MODIFY
        mods = data.get("modify", []) or []
        for mod in mods:
            stt = mod.get("stt")
            field = (mod.get("field") or "").lower()
            new_value = mod.get("new_value")
            if not (isinstance(stt, int) and 1 <= stt <= len(new_rows)
                     and field):
                continue
            row = new_rows[stt - 1]
            if field == "qtype":
                row.qtype = str(new_value).upper()
                row.codes = [f"{row.qtype}{stt}"]
            elif field == "level":
                row.level = str(new_value).upper()
            elif field == "topic":
                row.topic = str(new_value)
            elif field == "requirement":
                row.requirement = str(new_value)
            elif field == "points":
                try:
                    row.points = float(new_value)
                except Exception:
                    pass
        if mods:
            msg_parts.append(f"✏️ Chỉnh {len(mods)} câu")

        # ADD
        added = data.get("added", []) or []
        for spec in added:
            stt = len(new_rows) + 1
            new_rows.append(_make_row(spec, stt))
        if added:
            msg_parts.append(f"➕ Thêm {len(added)} câu")

    # Re-number stt
    for i, r in enumerate(new_rows, 1):
        r.stt = str(i)

    new_matrix = MatrixData(
        title=current_matrix.title,
        time_str=current_matrix.time_str,
        rows=new_rows,
    )
    msg = " | ".join(msg_parts) if msg_parts else "(không thay đổi)"
    return new_matrix, msg


def clone_matrix(matrix: MatrixData) -> MatrixData:
    """Deep clone MatrixData without keeping references to MatrixRow objects."""
    return MatrixData.from_dict(copy.deepcopy(matrix.to_dict()))


def dump_matrix_brief(matrix: MatrixData) -> str:
    """Serialize matrix into a short text block for AI context and UI preview."""
    lines = [f"Title: {matrix.title}", f"Time:  {matrix.time_str}",
             f"Số câu: {len(matrix.rows)}"]
    for i, row in enumerate(matrix.rows, 1):
        lines.append(
            f"  #{i}. [{row.qtype}/{row.level}] {row.topic} "
            f"({row.points}đ) — {row.requirement[:80]}"
        )
    return "\n".join(lines)


def diff_matrices(before: MatrixData, after: MatrixData) -> dict:
    """Return a compact position-based diff between two matrices."""
    compare_fields = ("qtype", "level", "topic", "requirement", "points", "enabled")
    before_rows = before.rows or []
    after_rows = after.rows or []
    max_common = min(len(before_rows), len(after_rows))
    modified: list[dict] = []

    for i in range(max_common):
        old = before_rows[i]
        new = after_rows[i]
        changes = {}
        for field_name in compare_fields:
            old_val = getattr(old, field_name)
            new_val = getattr(new, field_name)
            if old_val != new_val:
                changes[field_name] = {"old": old_val, "new": new_val}
        if changes:
            modified.append({
                "index": i + 1,
                "changes": changes,
                "old": {"qtype": old.qtype, "level": old.level, "topic": old.topic},
                "new": {"qtype": new.qtype, "level": new.level, "topic": new.topic},
            })

    added = [
        {
            "index": i + 1,
            "qtype": row.qtype,
            "level": row.level,
            "topic": row.topic,
            "points": row.points,
        }
        for i, row in enumerate(after_rows[max_common:], start=max_common)
    ]
    removed = [
        {
            "index": i + 1,
            "qtype": row.qtype,
            "level": row.level,
            "topic": row.topic,
            "points": row.points,
        }
        for i, row in enumerate(before_rows[max_common:], start=max_common)
    ]
    return {
        "before_count": len(before_rows),
        "after_count": len(after_rows),
        "modified": modified,
        "added": added,
        "removed": removed,
    }


def format_matrix_diff(diff: dict, *, max_items: int = 8) -> str:
    """Human-readable Smart Prompt diff preview."""
    lines: list[str] = []
    if diff.get("before_count") != diff.get("after_count"):
        lines.append(f"Số câu: {diff.get('before_count', 0)} → {diff.get('after_count', 0)}")

    shown = 0
    for item in diff.get("modified", []):
        if shown >= max_items:
            break
        bits = []
        for field_name, values in item.get("changes", {}).items():
            bits.append(f"{field_name}: {values.get('old')} → {values.get('new')}")
        lines.append(f"~ Câu {item['index']}: " + "; ".join(bits))
        shown += 1

    for item in diff.get("added", []):
        if shown >= max_items:
            break
        lines.append(f"+ Câu {item['index']}: {item['qtype']}/{item['level']} - {item['topic']}")
        shown += 1

    for item in diff.get("removed", []):
        if shown >= max_items:
            break
        lines.append(f"- Câu {item['index']}: {item['qtype']}/{item['level']} - {item['topic']}")
        shown += 1

    total = len(diff.get("modified", [])) + len(diff.get("added", [])) + len(diff.get("removed", []))
    if total > shown:
        lines.append(f"... và {total - shown} thay đổi khác")
    return "\n".join(lines) if lines else "Không có thay đổi."
