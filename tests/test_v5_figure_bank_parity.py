"""Guard rails for the V5 Figure Bank TikZ workflow."""
from __future__ import annotations

from pathlib import Path

from v5.figure_bank_dialog import _parse_tags, _source_label


ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_parse_tags_deduplicates_and_strips():
    assert _parse_tags(" 2D, tam giác, 2d, , parabol ") == [
        "2D",
        "tam giác",
        "parabol",
    ]


def test_source_label_normalizes_known_sources():
    assert _source_label("ai") == "AI"
    assert _source_label("manual") == "Thủ công"
    assert _source_label("template") == "Mẫu"
    assert _source_label("imported") == "Import"
    assert _source_label("nhch") == "NHCH tự động"
    assert _source_label("rendered") == "Render tự động"


def test_v5_figure_bank_dialog_uses_service_without_v4_ui():
    source = _source("v5/figure_bank_dialog.py")

    assert "class SaveFigureDialog" in source
    assert "class FigureBankDialog" in source
    assert "from services import figure_bank" in source
    assert "figure_bank.list_entries" in source
    assert "figure_bank.update_metadata" in source
    assert "figure_bank.delete" in source
    assert "from ui." not in source
    assert "import ui." not in source


def test_v5_figure_bank_dialog_reviews_rendered_png_and_keeps_table_readable():
    source = _source("v5/figure_bank_dialog.py")

    assert 'self.geometry("1280x760")' in source
    assert 'self.minsize(1040, 600)' in source
    assert 'selectmode="browse"' in source
    assert "xscrollcommand=hsb.set" in source
    assert "self._image_panel" in source
    assert "self._image_lbl" in source
    assert "def _show_render_image" in source
    assert "CTkImage" in source
    assert "entry.png_path()" in source
    assert '"title": 260' in source
    assert '"source": 132' in source
    assert '"tags": 215' in source
    assert "entry.tags[:6]" in source


def test_figure_save_dialogs_keep_save_button_visible():
    v4_source = _source("ui/tab_tikz.py")
    v5_source = _source("v5/figure_bank_dialog.py")

    assert "w, h = 540, 520" in v4_source
    assert "btn_footer.pack(fill=\"x\", side=\"bottom\")" in v4_source
    assert "command=self._on_save" in v4_source
    assert "<Control-Return>" in v4_source

    assert "self.geometry(\"560x500\")" in v5_source
    assert "footer.pack(fill=\"x\", side=\"bottom\")" in v5_source
    assert "command=self._confirm" in v5_source
    assert "<Control-Return>" in v5_source


def test_qc_tikz_ports_v4_figure_bank_actions():
    source = _source("v5/views/qc.py")

    assert "def _save_tikz_to_bank" in source
    assert "def _open_figure_bank" in source
    assert "SaveFigureDialog" in source
    assert "FigureBankDialog" in source
    assert "figure_bank.save" in source
    assert "Lưu kho" in source
    assert "Kho hình" in source
    assert "def _tikz_open_overleaf" in source
    assert "def _tikz_save_emf" in source
    assert "def _tikz_copy_emf" in source
    assert "Lưu EMF" in source
    assert "Copy EMF" in source
    assert "Overleaf" in source
