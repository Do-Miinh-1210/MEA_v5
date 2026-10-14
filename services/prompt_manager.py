"""
services/prompt_manager.py — Prompt Management System (Spec module 15).

Tính năng:
  - Lưu prompt versions với metadata
  - Xem prompt history
  - A/B test: so sánh 2 prompt version theo quality_score
  - Rollback về version cũ
  - Thêm bad_patterns tự động vào prompt

Lưu trong: ~/.exam_generator/prompts/
"""

from __future__ import annotations
import datetime
import json
import re
from pathlib import Path
from typing import Optional

from config import APP_DIR

PROMPT_DIR = APP_DIR / "prompts"
PROMPT_DIR.mkdir(parents=True, exist_ok=True)

_INDEX_FILE = PROMPT_DIR / "index.json"


# ── Data structure ────────────────────────────────────────────────────────────

def _load_index() -> dict:
    if not _INDEX_FILE.exists():
        return {"versions": {}, "active": {}}
    try:
        return json.loads(_INDEX_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"versions": {}, "active": {}}


def _save_index(index: dict) -> None:
    _INDEX_FILE.write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── Save / Load ───────────────────────────────────────────────────────────────

def save_prompt_version(
    name: str,
    prompt_text: str,
    description: str = "",
    tags: list[str] | None = None,
) -> str:
    """
    Lưu 1 version prompt.
    name: định danh (ví dụ: "TN_main", "DS_v2", "fix_safe")
    Returns: version_id (e.g. "TN_main_v3")
    """
    index = _load_index()
    versions = index.setdefault("versions", {})

    # Tính version number
    existing = [v for v in versions if v.startswith(f"{name}_v")]
    n = len(existing) + 1
    vid = f"{name}_v{n}"

    # Lưu file
    path = PROMPT_DIR / f"{vid}.txt"
    path.write_text(prompt_text, encoding="utf-8")

    versions[vid] = {
        "name":        name,
        "version":     n,
        "description": description,
        "tags":        tags or [],
        "created_at":  datetime.datetime.now().isoformat(),
        "path":        str(path),
        "char_count":  len(prompt_text),
        "ab_score":    None,   # Điền sau khi A/B test
        "use_count":   0,
    }
    _save_index(index)
    return vid


def load_prompt(version_id: str) -> Optional[str]:
    """Tải nội dung prompt theo version_id."""
    index = _load_index()
    meta  = index.get("versions", {}).get(version_id)
    if not meta:
        return None
    path = Path(meta["path"])
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def set_active_prompt(name: str, version_id: str) -> None:
    """Đặt version active cho 1 prompt name."""
    index = _load_index()
    index.setdefault("active", {})[name] = version_id
    _save_index(index)


def get_active_prompt(name: str) -> Optional[str]:
    """Trả về nội dung prompt đang active cho name."""
    index = _load_index()
    vid = index.get("active", {}).get(name)
    if not vid:
        return None
    return load_prompt(vid)


def list_prompts(name_filter: str = "") -> list[dict]:
    """Liệt kê tất cả versions (có thể lọc theo name)."""
    index = _load_index()
    active = index.get("active", {})
    result = []
    for vid, meta in index.get("versions", {}).items():
        if name_filter and not vid.startswith(name_filter):
            continue
        result.append({
            **meta,
            "version_id": vid,
            "is_active": active.get(meta["name"]) == vid,
        })
    return sorted(result, key=lambda x: x["created_at"], reverse=True)


def rollback_prompt(name: str, version_id: str) -> bool:
    """Rollback về version cũ hơn."""
    index = _load_index()
    if version_id not in index.get("versions", {}):
        return False
    index.setdefault("active", {})[name] = version_id
    _save_index(index)
    return True


def increment_use_count(version_id: str) -> None:
    """Tăng use_count khi prompt được dùng."""
    index = _load_index()
    if version_id in index.get("versions", {}):
        index["versions"][version_id]["use_count"] = \
            index["versions"][version_id].get("use_count", 0) + 1
        _save_index(index)


# ── A/B Testing ───────────────────────────────────────────────────────────────

def record_ab_result(version_id: str, score: float) -> None:
    """Ghi kết quả A/B test cho 1 version."""
    index = _load_index()
    if version_id in index.get("versions", {}):
        old = index["versions"][version_id].get("ab_score")
        if old is None:
            index["versions"][version_id]["ab_score"] = round(score, 3)
        else:
            # Rolling average
            index["versions"][version_id]["ab_score"] = round((old + score) / 2, 3)
        _save_index(index)


def compare_ab(name: str) -> list[dict]:
    """
    So sánh tất cả versions của 1 prompt theo ab_score.
    Returns: list sorted by ab_score descending.
    """
    versions = [v for v in list_prompts(name) if v.get("ab_score") is not None]
    return sorted(versions, key=lambda x: x["ab_score"], reverse=True)


def suggest_best_version(name: str) -> Optional[str]:
    """Gợi ý version tốt nhất dựa trên A/B score."""
    ranked = compare_ab(name)
    return ranked[0]["version_id"] if ranked else None


# ── Template injection ────────────────────────────────────────────────────────

def inject_bad_patterns(base_prompt: str, bad_patterns: list[str]) -> str:
    """
    Inject danh sách bad_patterns vào prompt.
    Thêm section "TRÁNH CÁC LỖI SAU:" trước phần cuối prompt.
    """
    if not bad_patterns:
        return base_prompt
    section = (
        "\nTRÁNH CÁC LỖI PHỔ BIẾN TỪ LỊCH SỬ:\n"
        + "\n".join(f"  - {p}" for p in bad_patterns[:8])
        + "\n"
    )
    # Chèn trước dòng cuối (thường là schema JSON)
    lines = base_prompt.rstrip().split("\n")
    insert_at = max(0, len(lines) - 3)
    lines.insert(insert_at, section)
    return "\n".join(lines)


def inject_few_shot(base_prompt: str, examples: list[str]) -> str:
    """Inject few-shot examples vào prompt."""
    if not examples:
        return base_prompt
    section = "\nVÍ DỤ CÂU HỎI ĐẠT CHUẨN (few-shot):\n" + "\n---\n".join(examples[:3]) + "\n"
    # Chèn sau phần giới thiệu (dòng đầu tiên có "Môn:")
    lines = base_prompt.split("\n")
    for i, line in enumerate(lines):
        if "Môn:" in line or "mức độ" in line.lower():
            lines.insert(i + 1, section)
            break
    else:
        lines.insert(2, section)
    return "\n".join(lines)


# ── Bootstrap: lưu các prompt mặc định ────────────────────────────────────────

def bootstrap_default_prompts(force: bool = False) -> None:
    """
    Lưu các prompt mặc định khi app khởi động lần đầu.
    Chỉ chạy nếu chưa có version nào (hoặc force=True).
    """
    index = _load_index()
    if index.get("versions") and not force:
        return  # Đã có prompts rồi

    # Import từ json_generator
    try:
        from core.json_generator import (
            _JSON_PROMPT_TN, _JSON_PROMPT_DS,
            _JSON_PROMPT_TLN, _JSON_PROMPT_TL,
        )
        for name, text in [
            ("TN_json",  _JSON_PROMPT_TN),
            ("DS_json",  _JSON_PROMPT_DS),
            ("TLN_json", _JSON_PROMPT_TLN),
            ("TL_json",  _JSON_PROMPT_TL),
        ]:
            vid = save_prompt_version(
                name, text,
                description=f"Prompt JSON mặc định cho {name}",
                tags=["default", "json", "v1"]
            )
            set_active_prompt(name, vid)
    except ImportError:
        pass

    # Lưu review/fix prompt
    try:
        from core.ai_reviewer import _FIX_PROMPT_SAFE, _FIX_PROMPT_SMART
        for name, text in [
            ("fix_safe",  _FIX_PROMPT_SAFE),
            ("fix_smart", _FIX_PROMPT_SMART),
        ]:
            vid = save_prompt_version(name, text,
                description=f"Fix prompt {name}", tags=["fix", "default"])
            set_active_prompt(name, vid)
    except (ImportError, AttributeError):
        pass
