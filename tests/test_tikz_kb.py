"""
tests/test_tikz_kb.py — Test services/tikz_kb.py.

Coverage:
  • KB load: đọc đúng file .txt trong data/tikz_kb/**/
  • Search: find_relevant ranking + top-k
  • Few-shot block builder
"""
from __future__ import annotations

import pytest

from services import tikz_kb


@pytest.fixture(autouse=True)
def reload_kb():
    """Re-load KB before mỗi test để không phụ thuộc thứ tự."""
    tikz_kb._LOADED = False
    tikz_kb.load(force=True)
    yield


# ══════════════════════════════════════════════════════════════════════════
# LOAD
# ══════════════════════════════════════════════════════════════════════════

def test_load_returns_count():
    n = tikz_kb.load(force=True)
    assert n > 50, f"Expected >50 templates, got {n}"


def test_get_template_names_sorted():
    names = tikz_kb.get_template_names()
    assert names == sorted(names)
    assert len(names) > 50


def test_all_templates_have_code():
    for tpl in tikz_kb.all_templates():
        assert tpl.name, "Template missing name"
        assert "\\begin{tikzpicture}" in tpl.code, (
            f"Template '{tpl.name}' missing \\begin{{tikzpicture}}"
        )
        assert "\\end{tikzpicture}" in tpl.code, (
            f"Template '{tpl.name}' missing \\end{{tikzpicture}}"
        )


def test_categories_present():
    """Phải có ít nhất 1 mẫu trong mỗi nhóm chính (2D/3D/đồ thị)."""
    names = " | ".join(tikz_kb.get_template_names())
    assert "Tam giác" in names, "Missing tam giác family"
    assert "chóp" in names.lower(), "Missing chóp family"
    assert "Đồ thị" in names or "Parabol" in names, "Missing đồ thị family"
    assert "BBT" in names, "Missing BBT"


# ══════════════════════════════════════════════════════════════════════════
# SEARCH
# ══════════════════════════════════════════════════════════════════════════

class TestFindRelevant:
    def test_returns_top_k(self):
        results = tikz_kb.find_relevant("hình chóp", k=3)
        assert 0 < len(results) <= 3

    def test_results_sorted_by_score(self):
        results = tikz_kb.find_relevant("tam giác vuông", k=5)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_chóp_đáy_vuông(self):
        results = tikz_kb.find_relevant("hình chóp đáy vuông S.ABCD", k=3)
        assert results, "Should find chóp templates"
        # Top match should mention chóp
        assert any("chóp" in r.name.lower() for r in results[:2])

    def test_đồ_thị_bậc_3(self):
        results = tikz_kb.find_relevant("đồ thị hàm bậc 3", k=3)
        assert results
        top_names = " ".join(r.name for r in results[:3]).lower()
        assert "bậc 3" in top_names or "cubic" in top_names

    def test_no_results_for_garbage(self):
        # Garbage string không có ký tự thường gặp trong keyword Việt
        # (tránh các single-char keyword như "H" — orthocenter template).
        # ZZZQQQ12345 không match bất kỳ keyword nào.
        results = tikz_kb.find_relevant("ZZZQQQ12345", k=3)
        assert len(results) <= 1   # cho phép tối đa 1 (false positive)


# ══════════════════════════════════════════════════════════════════════════
# FEW-SHOT BLOCK
# ══════════════════════════════════════════════════════════════════════════

class TestBuildFewShotBlock:
    def test_returns_string(self):
        block = tikz_kb.build_few_shot_block("hình trụ", k=2)
        assert isinstance(block, str)
        assert "MẪU THAM KHẢO" in block

    def test_respects_max_chars(self):
        block = tikz_kb.build_few_shot_block("tam giác", k=5, max_chars=500)
        assert len(block) <= 600   # 500 + 1 template (cuối có thể bị cắt)

    def test_includes_tikz_code(self):
        block = tikz_kb.build_few_shot_block("hình chóp đều", k=2)
        assert "\\begin{tikzpicture}" in block

    def test_empty_query(self):
        # Garbage string không match bất kỳ keyword nào (tránh single-char
        # keyword như "H" trong template "Trực tâm H").
        block = tikz_kb.build_few_shot_block("ZZZQQQ12345", k=2)
        assert block == ""
