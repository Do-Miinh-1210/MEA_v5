"""Dependency guardrails for migrated V5 workflows."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATED_WORKFLOW_FILES = (
    "v5/app.py",
    "v5/ai_usage_dialog.py",
    "v5/ai_usage_summary.py",
    "v5/analyze_exam.py",
    "v5/dashboard_insights.py",
    "v5/edit_question.py",
    "v5/figure_bank_dialog.py",
    "v5/latex_preview.py",
    "v5/question_cards.py",
    "v5/import_wizard.py",
    "v5/tikz_shape_builder.py",
    "v5/variant_dialog.py",
    "v5/views/exam_create.py",
    "v5/views/nhch.py",
    "v5/views/convert.py",
    "v5/views/qc.py",
    "v5/views/tracking.py",
)

MIGRATED_SHARED_FILES = (
    "core/pdf_to_questions.py",
    "services/api_client.py",
    "services/image_fields.py",
    "services/tikz_renderer.py",
    "services/tikz_pipeline.py",
    "services/tikz_thumbnail.py",
)


def test_nhch_import_edit_slice_does_not_import_v4_ui():
    for relative_path in MIGRATED_WORKFLOW_FILES:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "from ui." not in source, relative_path
        assert "import ui." not in source, relative_path


def test_all_v5_runtime_modules_do_not_import_v4_ui():
    for path in sorted((ROOT / "v5").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "from ui." not in source, path.relative_to(ROOT)
        assert "import ui." not in source, path.relative_to(ROOT)


def test_shared_runtime_packages_used_by_v5_do_not_import_v4_ui():
    for package in ("core", "services", "storage", "export"):
        for path in sorted((ROOT / package).rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            assert "from ui." not in source, path.relative_to(ROOT)
            assert "import ui." not in source, path.relative_to(ROOT)


def test_migrated_shared_files_do_not_depend_on_v4_ui():
    for relative_path in MIGRATED_SHARED_FILES:
        source = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "from ui." not in source, relative_path
        assert "import ui." not in source, relative_path
        assert "ui.tab_convert" not in source, relative_path
        assert "ui.tab_tikz" not in source, relative_path


def test_v5_guide_content_includes_migrated_workflows():
    from v5.guide_content import GUIDES

    sections = {guide["tab"] for guide in GUIDES}
    assert {"Ngân hàng câu hỏi", "Convert", "Kiểm tra chất lượng (QC)", "TikZ vẽ hình"} <= sections


def test_v5_guide_uses_shared_theme_and_fixed_two_column_layout():
    source = (ROOT / "v5" / "views" / "guide.py").read_text(encoding="utf-8")

    assert "from v5 import __version__" in source
    assert "from config import APP_VERSION" not in source
    assert 'text=f"📖  Hướng dẫn sử dụng MatrixExamAI v{__version__}"' in source
    assert "from v5.ui_theme import UI_COLORS, darken, tint" in source
    assert "NAV_WIDTH = 300" in source
    assert "GUIDE_WRAP = 860" in source
    assert "body.grid_columnconfigure(0, weight=0, minsize=NAV_WIDTH)" in source
    assert "def _filter_sections" in source
    assert "def _render_quick_start" in source
    assert "def _content_wraplength" in source
    assert "def _clean_step_text" in source
    assert "placeholder_text=\"Tìm mục hướng dẫn...\"" in source
    assert "text_color=\"gray\"" not in source
    assert "wraplength=820" not in source
    assert "wraplength=self._content_wraplength()" in source


def test_v5_guide_content_has_distinct_accents_and_icons():
    from v5.guide_content import GUIDES

    colors = [guide["color"] for guide in GUIDES]
    icons = [guide.get("icon", "") for guide in GUIDES]

    assert len(colors) == len(set(colors))
    assert all(color.startswith("#") and len(color) == 7 for color in colors)
    assert all(icon.strip() for icon in icons)


def test_v5_ui_theme_exposes_high_contrast_tokens():
    from v5.ui_theme import GUIDE_ACCENTS, UI_COLORS, darken, tint

    for key in ("surface", "surface_alt", "border", "text_secondary", "text_muted", "guide_header"):
        assert key in UI_COLORS
    assert len(GUIDE_ACCENTS) >= 9
    assert darken("#2563EB") != "#2563EB"
    assert tint("#2563EB").startswith("#")


def test_v5_branding_uses_v4_logo_assets():
    app_source = (ROOT / "v5" / "app.py").read_text(encoding="utf-8")
    about_source = (ROOT / "v5" / "about.py").read_text(encoding="utf-8")

    assert '_first_existing_asset("app.ico", "icon_app.ico")' in app_source
    assert '_first_existing_asset("app.png", "icon4.png")' in app_source
    assert 'text="  π  MatrixExam AI  "' not in app_source
    assert '_first_existing_asset("app.png", "icon4.png")' in about_source
    assert 'text="π"' not in about_source


def test_v5_sidebar_is_compact_active_and_restores_collapsed_state():
    source = (ROOT / "v5" / "sidebar.py").read_text(encoding="utf-8")
    app_source = (ROOT / "v5" / "app.py").read_text(encoding="utf-8")

    assert 'settings_store.load().get("sidebar_collapsed", False)' in source
    assert "self.pack_propagate(False)" in source
    assert "def _apply_width(self) -> None" in source
    assert "self.master.grid_columnconfigure(0, minsize=new_w, weight=0)" in source
    assert 'text="" if self._collapsed else getattr(self, "_footer_text", "")' in source
    assert "self._expanded = set() if key in self._expanded else {key}" in source
    assert "self._active_key = key" in source
    assert "def set_active(self, key: str)" in source
    assert "self.sidebar.set_active(view_id)" in app_source


def test_v5_model_selectors_are_explicit_in_convert_import_and_nhch():
    config_source = (ROOT / "config.py").read_text(encoding="utf-8")
    convert_source = (ROOT / "v5" / "views" / "convert.py").read_text(encoding="utf-8")
    wizard_source = (ROOT / "v5" / "import_wizard.py").read_text(encoding="utf-8")
    nhch_source = (ROOT / "v5" / "views" / "nhch.py").read_text(encoding="utf-8")
    qc_source = (ROOT / "v5" / "views" / "qc.py").read_text(encoding="utf-8")
    setup_source = (ROOT / "v5" / "views" / "setup.py").read_text(encoding="utf-8")

    new_gemini_models = [
        "gemini-3.8-flash",
        "gemini-3.1-pro",
        "gemini-3.8-live",
        "gemini-3.5-flash-lite",
    ]
    for model in new_gemini_models:
        assert model in config_source
        assert model in setup_source
        assert model in convert_source
        assert model in wizard_source
        assert model in nhch_source
        assert model in qc_source

    for source in (convert_source, wizard_source):
        assert "MODEL_OPTIONS" in source or "_MODEL_OPTIONS" in source
        assert "_model_menu = ctk.CTkOptionMenu" in source
        assert "_model_menu.configure(values=values)" in source

    assert "AI_MODEL_OPTIONS" in nhch_source
    assert "_ai_model_menu = ctk.CTkOptionMenu" in nhch_source
    assert "def _resolve_ai_call(self)" in nhch_source
    assert "model = self._ai_model_var.get()" in nhch_source

    assert "QC_AI_MODEL_OPTIONS" in qc_source
    assert "_qc_model_menu = ctk.CTkOptionMenu" in qc_source
    assert "def _resolve_ai_call_qc(self)" in qc_source
    assert "self._qc_model_var.get()" in qc_source


def test_v5_tikz_editor_has_large_editor_snippets_and_error_diagnostics():
    source = (ROOT / "v5" / "views" / "qc.py").read_text(encoding="utf-8")

    assert "TIKZ_SNIPPETS" in source
    assert '"#diem"' in source
    assert '"#bbt"' in source
    assert '"#bxd"' in source
    assert "height=360" in source
    assert 'font=("Consolas", 12)' in source
    assert "_tikz_error_box = ctk.CTkTextbox" in source
    assert "def _expand_tikz_snippet" in source
    assert "explain_render_error" in source


def test_v5_priority_tables_keep_readable_widths_and_scrollbars():
    nhch_source = (ROOT / "v5" / "views" / "nhch.py").read_text(encoding="utf-8")
    convert_source = (ROOT / "v5" / "views" / "convert.py").read_text(encoding="utf-8")
    qc_source = (ROOT / "v5" / "views" / "qc.py").read_text(encoding="utf-8")
    wizard_source = (ROOT / "v5" / "import_wizard.py").read_text(encoding="utf-8")

    assert "minwidths = {" in nhch_source
    assert "minwidth=minwidths[c]" in nhch_source
    assert 'stretch=c in ("topic", "preview")' in nhch_source
    assert "xscrollcommand=hsb.set" in nhch_source
    assert 'hscroll = ttk.Scrollbar(table, orient="horizontal"' in convert_source
    assert "xscrollcommand=hscroll.set" in convert_source
    assert "minwidths = {" in qc_source
    assert "minwidth=minwidths[cc]" in qc_source
    assert 'stretch=(cc == "issue")' in qc_source
    assert "xscrollcommand=hsb.set" in qc_source
    assert "preview_minwidths = {" in wizard_source
    assert "minwidth=preview_minwidths[c]" in wizard_source
    assert 'stretch=(c == "preview")' in wizard_source
    assert "xscrollcommand=hsb.set" in wizard_source
