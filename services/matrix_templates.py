"""
services/matrix_templates.py — Matrix templates library cho [SPEED-3].

Quản lý các template ma trận chuẩn theo BGD: load + serialize JSON, tạo
MatrixData ready-to-use. GV mới chỉ cần chọn 1 template thay vì nhập
ma trận từ đầu.

Template format (data/matrix_templates/<id>.json):
{
    "id":          "lop12_cuoi_ki_1_chuan_bgd",
    "name":        "Lớp 12 — Cuối kỳ I (chuẩn BGD 2025)",
    "description": "12 TN + 4 DS + 6 TLN. 40 NB / 35 TH / 25 VD. 90 phút.",
    "icon":        "📝",
    "subject":     "Toán",
    "grade":       "12",
    "time_str":    "90 phút",
    "title":       "ĐỀ KIỂM TRA CUỐI HỌC KÌ I — TOÁN 12",
    "tags":        ["cuối kỳ", "lớp 12", "chuẩn BGD"],
    "rows": [
        {
            "qtype": "TN", "level": "NB",
            "topic": "Ứng dụng đạo hàm",
            "requirement": "Nhận biết tính đơn điệu của hàm số",
            "points": 0.25
        },
        ...
    ]
}

API:
    >>> from services.matrix_templates import list_templates, load_template
    >>> templates = list_templates()  # → list[dict] metadata
    >>> matrix = load_template("lop12_cuoi_ki_1_chuan_bgd")
    >>> matrix.rows  # list[MatrixRow]
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from core.models import MatrixData, MatrixRow, DSItem
from config import POINTS_MAP

_log = logging.getLogger(__name__)

# Thư mục chứa templates — relative tới thư mục root của app
_TEMPLATES_DIR = Path(__file__).parent.parent / "data" / "matrix_templates"


# ──────────────────────────────────────────────────────────────────────────
#  PUBLIC API
# ──────────────────────────────────────────────────────────────────────────

def list_templates(filter_grade: Optional[str] = None,
                    filter_subject: Optional[str] = None) -> list[dict]:
    """Quét thư mục templates, trả list metadata cho UI hiển thị.

    Mỗi dict chứa: id, name, description, icon, subject, grade, time_str,
    title, tags, n_rows (tổng số câu trong template).

    Parameters
    ----------
    filter_grade:   nếu set → chỉ trả templates cho lớp này
    filter_subject: nếu set → chỉ trả templates cho môn này (case-insensitive)
    """
    if not _TEMPLATES_DIR.exists():
        _log.warning("Templates dir không tồn tại: %s", _TEMPLATES_DIR)
        return []

    out: list[dict] = []
    for file in sorted(_TEMPLATES_DIR.glob("*.json")):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
            tpl_id = data.get("id") or file.stem

            if filter_grade and str(data.get("grade", "")) != str(filter_grade):
                continue
            if filter_subject:
                if (data.get("subject", "") or "").lower() != filter_subject.lower():
                    continue

            n_rows = len(data.get("rows", []))
            stats = _row_stats(data.get("rows", []))
            out.append({
                "id":          tpl_id,
                "name":        data.get("name", tpl_id),
                "description": data.get("description", ""),
                "icon":        data.get("icon", "📋"),
                "subject":     data.get("subject", "Toán"),
                "grade":       data.get("grade", ""),
                "time_str":    data.get("time_str", ""),
                "title":       data.get("title", data.get("name", "")),
                "tags":        data.get("tags", []),
                "n_rows":      n_rows,
                "stats":       stats,  # {"TN": n, "DS": n, "TLN": n, "TL": n}
                "_path":       str(file),
            })
        except Exception as e:
            _log.warning("Failed to read template %s: %s", file, e)
    return out


def load_template(template_id: str) -> Optional[MatrixData]:
    """Load 1 template by id → MatrixData ready-to-use.

    Trả None nếu không tìm thấy.
    """
    file = _TEMPLATES_DIR / f"{template_id}.json"
    if not file.exists():
        _log.warning("Template không tồn tại: %s", template_id)
        return None

    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        _log.error("Failed to parse %s: %s", file, e)
        return None

    return _build_matrix_from_template(data)


# ──────────────────────────────────────────────────────────────────────────
#  INTERNAL
# ──────────────────────────────────────────────────────────────────────────

def _row_stats(rows: list[dict]) -> dict[str, int]:
    """Đếm số câu theo qtype trong template."""
    stats = {"TN": 0, "DS": 0, "TLN": 0, "TL": 0}
    for r in rows:
        qt = r.get("qtype", "TN")
        if qt in stats:
            stats[qt] += 1
    return stats


def _build_matrix_from_template(data: dict) -> MatrixData:
    """Convert template dict → MatrixData.

    - Auto-fill stt (1, 2, 3…)
    - Auto-fill codes ("TN1", "DS2", "TLN3", …)
    - Auto-fill enabled=True
    - DS: nếu template có `ds_items` → dùng; nếu không → default 4 ý NB/TH/VD/VD
    """
    title    = data.get("title", "ĐỀ KIỂM TRA")
    time_str = data.get("time_str", "60 phút")

    rows: list[MatrixRow] = []
    stt = 0
    for raw_r in data.get("rows", []):
        stt += 1
        qtype = raw_r.get("qtype", "TN")
        level = raw_r.get("level", "NB")
        topic = raw_r.get("topic", "")
        requirement = raw_r.get("requirement", f"{topic} [{level}]")
        points = float(raw_r.get("points", POINTS_MAP.get(qtype, 0.25)))
        codes = raw_r.get("codes", [f"{qtype}{stt}"])

        ds_items: list[DSItem] = []
        if qtype == "DS":
            raw_items = raw_r.get("ds_items", [])
            if raw_items:
                for i, di in enumerate(raw_items):
                    lbl = di.get("label", chr(ord('a') + i))
                    lv  = di.get("level", "NB")
                    rq  = di.get("requirement", f"{topic} [{lv}]")
                    cd  = di.get("code", f"DS{stt}{lbl}")
                    ds_items.append(DSItem(
                        label=lbl, level=lv,
                        requirement=rq, code=cd,
                    ))
            else:
                # Default: a-NB, b-TH, c-VD, d-VD
                for i, lv in enumerate(["NB", "TH", "VD", "VD"]):
                    lbl = chr(ord('a') + i)
                    ds_items.append(DSItem(
                        label=lbl, level=lv,
                        requirement=f"{topic} [{lv}]",
                        code=f"DS{stt}{lbl}",
                    ))
            # Re-compute codes từ ds_items
            codes = [it.code for it in ds_items]

        rows.append(MatrixRow(
            stt=str(stt),
            topic=topic,
            level=level,
            qtype=qtype,
            codes=codes,
            requirement=requirement,
            points=points,
            enabled=raw_r.get("enabled", True),
            ds_items=ds_items,
        ))

    return MatrixData(title=title, time_str=time_str, rows=rows)


def get_template_info(template_id: str) -> Optional[dict]:
    """Lấy metadata 1 template (không build MatrixData)."""
    file = _TEMPLATES_DIR / f"{template_id}.json"
    if not file.exists():
        return None
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        _log.warning("get_template_info failed: %s", e)
        return None


def get_templates_dir() -> Path:
    """Expose templates dir cho UI (vd: nút 'Mở thư mục template')."""
    return _TEMPLATES_DIR
