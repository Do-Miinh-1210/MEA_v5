"""
tests/test_figure_bank.py — Test services/figure_bank.py.

Dùng `monkeypatch` để redirect FIGURES_DIR → tmp_path để không đụng dữ liệu thật.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_bank(monkeypatch, tmp_path):
    """Redirect figure_bank vào tmp dir."""
    # Patch _bank_dir() trong figure_bank để dùng tmp
    from services import figure_bank
    fake_dir = tmp_path / "figures"
    fake_dir.mkdir()
    monkeypatch.setattr(figure_bank, "_bank_dir", lambda: fake_dir)
    return fake_dir


# ══════════════════════════════════════════════════════════════════════════
# SAVE / GET / DELETE
# ══════════════════════════════════════════════════════════════════════════

class TestSaveAndGet:
    def test_save_returns_id(self, tmp_bank):
        from services import figure_bank
        fid = figure_bank.save(
            tikz_code="\\begin{tikzpicture}\\draw(0,0)circle(1);\\end{tikzpicture}",
            title="Test circle",
            tags=["test"],
        )
        assert fid == "001"

    def test_save_creates_tex_file(self, tmp_bank):
        from services import figure_bank
        figure_bank.save(
            tikz_code="\\begin{tikzpicture}\\draw(0,0)--(1,1);\\end{tikzpicture}",
            title="Line",
        )
        assert (tmp_bank / "figure_001.tex").exists()
        # No PNG by default
        assert not (tmp_bank / "figure_001.png").exists()

    def test_save_updates_index(self, tmp_bank):
        from services import figure_bank
        figure_bank.save(
            tikz_code="\\begin{tikzpicture}\\end{tikzpicture}",
            title="A", tags=["x", "y"],
        )
        idx_file = tmp_bank / "index.json"
        assert idx_file.exists()
        data = json.loads(idx_file.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["title"] == "A"
        assert data[0]["tags"] == ["x", "y"]

    def test_save_increments_id(self, tmp_bank):
        from services import figure_bank
        f1 = figure_bank.save(tikz_code="\\begin{tikzpicture}\\end{tikzpicture}", title="A")
        f2 = figure_bank.save(tikz_code="\\begin{tikzpicture}\\end{tikzpicture}", title="B")
        f3 = figure_bank.save(tikz_code="\\begin{tikzpicture}\\end{tikzpicture}", title="C")
        assert (f1, f2, f3) == ("001", "002", "003")

    def test_get_returns_entry(self, tmp_bank):
        from services import figure_bank
        fid = figure_bank.save(
            tikz_code="\\begin{tikzpicture}A\\end{tikzpicture}",
            title="Foo", description="bar", tags=["tag1"],
        )
        e = figure_bank.get(fid)
        assert e is not None
        assert e.title == "Foo"
        assert e.description == "bar"
        assert e.tags == ["tag1"]

    def test_get_tikz_returns_code(self, tmp_bank):
        from services import figure_bank
        code = "\\begin{tikzpicture}original\\end{tikzpicture}"
        fid = figure_bank.save(tikz_code=code, title="X")
        assert figure_bank.get_tikz(fid) == code

    def test_save_rejects_empty(self, tmp_bank):
        from services import figure_bank
        with pytest.raises(ValueError):
            figure_bank.save(tikz_code="   ", title="T")

    def test_save_rendered_deduplicates_tikz_and_keeps_png(self, tmp_bank, tmp_path):
        from PIL import Image
        from services import figure_bank

        png = tmp_path / "render.png"
        Image.new("RGB", (12, 8), "white").save(png)
        code = "\\begin{tikzpicture}\\draw(0,0)--(1,1);\\end{tikzpicture}"

        first, created_first = figure_bank.save_rendered(code, png_path=png)
        second, created_second = figure_bank.save_rendered(f"  {code}\n", png_path=png)

        assert first == second == "001"
        assert created_first is True
        assert created_second is False
        assert figure_bank.count() == 1
        assert (tmp_bank / "figure_001.png").exists()

    def test_save_rendered_accepts_v4_pil_image(self, tmp_bank):
        from PIL import Image
        from services import figure_bank

        code = "\\begin{tikzpicture}\\draw(0,0)circle(1);\\end{tikzpicture}"
        fid, created = figure_bank.save_rendered(
            code,
            png_pil=Image.new("RGB", (10, 10), "white"),
            source="rendered",
        )

        assert fid == "001"
        assert created is True
        assert (tmp_bank / "figure_001.png").exists()
        assert figure_bank.get(fid).source == "rendered"


# ══════════════════════════════════════════════════════════════════════════
# LIST + SEARCH + FILTER
# ══════════════════════════════════════════════════════════════════════════

class TestListAndFilter:
    def _seed(self, figure_bank):
        figure_bank.save(tikz_code="\\begin{tikzpicture}\\end{tikzpicture}",
                          title="Tam giác vuông", tags=["2D"], source="manual")
        figure_bank.save(tikz_code="\\begin{tikzpicture}\\end{tikzpicture}",
                          title="Hình chóp", tags=["3D"], source="ai")
        figure_bank.save(tikz_code="\\begin{tikzpicture}\\end{tikzpicture}",
                          title="Đồ thị parabol", tags=["graph"], source="manual")

    def test_list_all(self, tmp_bank):
        from services import figure_bank
        self._seed(figure_bank)
        entries = figure_bank.list_entries()
        assert len(entries) == 3

    def test_search_by_title(self, tmp_bank):
        from services import figure_bank
        self._seed(figure_bank)
        results = figure_bank.list_entries(query="tam giác")
        assert len(results) == 1
        assert results[0].title == "Tam giác vuông"

    def test_filter_by_source(self, tmp_bank):
        from services import figure_bank
        self._seed(figure_bank)
        ai_only = figure_bank.list_entries(source_filter="ai")
        assert len(ai_only) == 1
        assert ai_only[0].title == "Hình chóp"

    def test_search_combined_with_filter(self, tmp_bank):
        from services import figure_bank
        self._seed(figure_bank)
        results = figure_bank.list_entries(query="tam giác", source_filter="ai")
        assert len(results) == 0   # tam giác chỉ có manual


# ══════════════════════════════════════════════════════════════════════════
# DELETE + UPDATE
# ══════════════════════════════════════════════════════════════════════════

class TestDeleteAndUpdate:
    def test_delete_removes_files(self, tmp_bank):
        from services import figure_bank
        fid = figure_bank.save(tikz_code="\\begin{tikzpicture}\\end{tikzpicture}",
                                title="Del me")
        assert figure_bank.delete(fid) is True
        assert figure_bank.get(fid) is None
        assert not (tmp_bank / f"figure_{fid}.tex").exists()

    def test_delete_nonexistent_returns_false(self, tmp_bank):
        from services import figure_bank
        assert figure_bank.delete("999") is False

    def test_update_metadata(self, tmp_bank):
        from services import figure_bank
        fid = figure_bank.save(tikz_code="\\begin{tikzpicture}\\end{tikzpicture}",
                                title="Old name", tags=["old"])
        ok = figure_bank.update_metadata(
            fid, title="New name", description="New desc", tags=["new1", "new2"],
        )
        assert ok
        e = figure_bank.get(fid)
        assert e.title == "New name"
        assert e.description == "New desc"
        assert e.tags == ["new1", "new2"]


# ══════════════════════════════════════════════════════════════════════════
# STATS
# ══════════════════════════════════════════════════════════════════════════

def test_stats_empty(tmp_bank):
    from services import figure_bank
    s = figure_bank.stats()
    assert s["total"] == 0
    assert s["with_png"] == 0
    assert s["by_source"] == {}


def test_stats_with_data(tmp_bank):
    from services import figure_bank
    figure_bank.save(tikz_code="\\begin{tikzpicture}\\end{tikzpicture}", title="A", source="ai")
    figure_bank.save(tikz_code="\\begin{tikzpicture}\\end{tikzpicture}", title="B", source="manual")
    figure_bank.save(tikz_code="\\begin{tikzpicture}\\end{tikzpicture}", title="C", source="ai")
    s = figure_bank.stats()
    assert s["total"] == 3
    assert s["by_source"]["ai"] == 2
    assert s["by_source"]["manual"] == 1


def test_no_auto_save_in_do_render():
    """Đảm bảo _do_render không tự động lưu rác sau khi render."""
    from pathlib import Path
    tab_tikz_code = (Path(__file__).parent.parent / "ui" / "tab_tikz.py").read_text(encoding="utf-8")
    assert "def _do_render" in tab_tikz_code
    # Kiểm tra dòng gọi hàm _auto_save_rendered_figure đã được bỏ / comment khỏi _do_render
    assert "self._auto_save_rendered_figure(tikz_code, img)" not in tab_tikz_code


def test_figure_bank_entry_png_path_available(tmp_bank):
    """Đảm bảo entry trong kho có png_path để mở ngay lập tức."""
    from PIL import Image
    from services import figure_bank
    im = Image.new("RGB", (100, 100), color="blue")
    fid = figure_bank.save(
        tikz_code="\\begin{tikzpicture}\\draw (0,0) -- (1,1);\\end{tikzpicture}",
        title="Test Figure With PNG",
        png_pil=im,
    )
    e = figure_bank.get(fid)
    assert e is not None
    assert e.has_png
    png_p = e.png_path()
    assert png_p is not None and png_p.is_file()
    # Mở lại ảnh không cần render lại
    loaded_img = Image.open(png_p)
    assert loaded_img.size == (100, 100)

