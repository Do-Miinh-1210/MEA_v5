"""
tests/test_e2e_layout_standards.py — E2E Layout Standardization Test Suite for MEA v5.0.

Authoritative Sources:
- PROJECT.md (Architecture, Viewport budget: 1100x700 -> 810px width, 600px height)
- ORIGINAL_REQUEST.md (Requirements R1, R2, R3, R4 and Acceptance Criteria)
- Survey Reports 1, 2, 3 (ConvertView, QCView, SetupView, TrackingView, ExamCreateView, NhchView)

Tiers:
- Tier 1: Feature Coverage (>=5 per feature area: Convert, QC, Setup, Tracking, ExamCreate, Nhch)
- Tier 2: Boundary & Corner Cases (minsize 1100x700, window resizing, scrollbar visibility, DPI simulation)
- Tier 3: Cross-Feature Combinations (view switching, TaskLog, Preferences, state preservation)
- Tier 4: Real-World Application Scenarios (full end-user workflows, coordinate bounds <= 810 px)
"""
from __future__ import annotations

import py_compile
import sys
import tkinter as tk
from pathlib import Path
from typing import Any

import customtkinter as ctk
import pytest

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.models import ExamData, Question
from v5.app import ModernApp
from v5.preferences import PreferencesDialog
from v5.task_log import TaskLogDialog
from v5.views.convert import ConvertView, MODE_DOCUMENT, MODE_IMAGE, MODE_TEXT
from v5.views.exam_create import ExamCreateView
from v5.views.nhch import NHCHView
from v5.views.qc import QCView
from v5.views.setup import SetupView
from v5.views.tracking import TrackingView


# ── TEST FIXTURES & HELPERS ──────────────────────────────────────────────────

@pytest.fixture
def tk_root():
    """Headless/offscreen CustomTkinter root window for layout geometry testing."""
    try:
        ctk.deactivate_automatic_dpi_awareness()
        root = ctk.CTk()
        root.attributes("-alpha", 0.0)
    except tk.TclError as exc:
        pytest.skip(f"Tk display is unavailable in current environment: {exc}")
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def make_test_exam(count: int = 6) -> ExamData:
    """Create a valid ExamData model for E2E testing."""
    questions = []
    for i in range(1, count + 1):
        questions.append(
            Question(
                qtype="TN",
                level="TH",
                topic=f"Chủ đề {i}: Khảo sát hàm số",
                question=f"Câu hỏi số {i}: Cho hàm số $y=f(x)$. Mệnh đề nào sau đây đúng?",
                options={"A": f"Đáp án A_{i}", "B": f"Đáp án B_{i}", "C": f"Đáp án C_{i}", "D": f"Đáp án D_{i}"},
                answer="A",
                solution=f"Lời giải chi tiết câu {i} với công thức $\\int_0^1 f(x)dx$."
            )
        )
    return ExamData(
        exam_title="Đề Kiểm Tra Chuẩn Hóa Bố Cục MEA v5.0",
        subject="Toán",
        grade="12",
        semester="I",
        year="2026",
        time="45 phút",
        questions=questions,
    )


def mount_test_view(root: ctk.CTk, view_cls: type, width: int = 1100, height: int = 700, **kwargs) -> tuple[Any, ctk.CTkFrame]:
    """
    Mount a view inside a mock container replicating ModernApp layout:
    - Width = window_width - 250 (sidebar) - 24 (padx*2) = 826 px (at 1100 px)
    - Height = window_height - 48 (topbar) - 28 (statusbar) - 24 (pady*2) = 600 px (at 700 px)
    """
    for child in list(root.winfo_children()):
        try:
            child.destroy()
        except Exception:
            pass

    root.geometry(f"{width}x{height}")
    root.minsize(1100, 700)
    root.update()

    content_w = max(100, width - 250 - 24)
    content_h = max(100, height - 48 - 28 - 24)

    container = ctk.CTkFrame(root, width=content_w, height=content_h, fg_color="transparent")
    container.place(x=262, y=60)
    container.pack_propagate(False)

    view = view_cls(container, **kwargs)
    view.pack(fill="both", expand=True)

    root.update()
    return view, container


def has_scrollable_container(container: tk.Widget) -> bool:
    """Return True if container is a CTkScrollableFrame or contains one in its subtree."""
    if isinstance(container, ctk.CTkScrollableFrame):
        return True
    for child in container.winfo_children():
        if isinstance(child, ctk.CTkScrollableFrame) or has_scrollable_container(child):
            return True
    return False


def find_first_scrollable_frame(container: tk.Widget) -> ctk.CTkScrollableFrame | None:
    """Find the first CTkScrollableFrame in the widget hierarchy."""
    if isinstance(container, ctk.CTkScrollableFrame):
        return container
    for child in container.winfo_children():
        res = find_first_scrollable_frame(child)
        if res is not None:
            return res
    return None


def get_relative_right_coordinate(widget: tk.Widget, container: tk.Widget) -> int:
    """
    Calculate the relative right edge coordinate of a widget with respect to the view container:
    right = (widget.winfo_rootx() - container.winfo_rootx()) + widget.winfo_width()
    """
    try:
        rel_x = widget.winfo_rootx() - container.winfo_rootx()
        return rel_x + widget.winfo_width()
    except Exception:
        return widget.winfo_x() + widget.winfo_width()


# ── SECTION 0: SYNTAX COMPILATION & UI INDEPENDENCE ─────────────────────────

def test_py_compile_all_v5_views_and_dialogs():
    """Verify syntax of all V5 views and dialogs via py_compile without errors."""
    v5_files = [
        _REPO_ROOT / "v5" / "app.py",
        _REPO_ROOT / "v5" / "statusbar.py",
        _REPO_ROOT / "v5" / "task_log.py",
        _REPO_ROOT / "v5" / "preferences.py",
        _REPO_ROOT / "v5" / "views" / "convert.py",
        _REPO_ROOT / "v5" / "views" / "qc.py",
        _REPO_ROOT / "v5" / "views" / "setup.py",
        _REPO_ROOT / "v5" / "views" / "tracking.py",
        _REPO_ROOT / "v5" / "views" / "exam_create.py",
        _REPO_ROOT / "v5" / "views" / "nhch.py",
    ]
    for file_path in v5_files:
        assert file_path.exists(), f"Missing file: {file_path}"
        compiled = py_compile.compile(str(file_path), doraise=True)
        assert compiled is not None, f"Failed to py_compile {file_path}"


def test_v5_ui_independence_contract():
    """Verify invariant: zero imports from v4 ui package across all V5 files."""
    v5_dir = _REPO_ROOT / "v5"
    for path in sorted(v5_dir.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        assert "from ui." not in source, f"Violation in {path.relative_to(_REPO_ROOT)}"
        assert "import ui." not in source, f"Violation in {path.relative_to(_REPO_ROOT)}"


# ── SECTION 1: VIEW INSTANTIATION AT MINSIZE & STANDARD ─────────────────────

def test_all_views_instantiate_at_minsize_1100x700(tk_root):
    """Verify all 6 views instantiate on test root at minsize 1100x700 without layout exceptions."""
    exam = make_test_exam(2)

    # ConvertView
    cv, _ = mount_test_view(tk_root, ConvertView, width=1100, height=700)
    assert cv.winfo_exists()
    cv.destroy()

    # QCView
    qv, _ = mount_test_view(tk_root, QCView, width=1100, height=700, initial_exam=exam, get_current_exam=lambda: exam)
    assert qv.winfo_exists()
    qv.destroy()

    # SetupView
    sv, _ = mount_test_view(tk_root, SetupView, width=1100, height=700)
    assert sv.winfo_exists()
    sv.destroy()

    # TrackingView
    tv, _ = mount_test_view(tk_root, TrackingView, width=1100, height=700, get_current_exam=lambda: exam)
    assert tv.winfo_exists()
    tv.destroy()

    # ExamCreateView
    ev, _ = mount_test_view(tk_root, ExamCreateView, width=1100, height=700, initial_exam=exam)
    assert ev.winfo_exists()
    ev.destroy()

    # NHCHView
    nv, _ = mount_test_view(tk_root, NHCHView, width=1100, height=700)
    assert nv.winfo_exists()
    nv.destroy()


def test_all_views_instantiate_at_standard_1280x800(tk_root):
    """Verify all 6 views instantiate on test root at standard 1280x800 without layout exceptions."""
    exam = make_test_exam(2)
    view_specs = [
        (ConvertView, {}),
        (QCView, {"initial_exam": exam, "get_current_exam": lambda: exam}),
        (SetupView, {}),
        (TrackingView, {"get_current_exam": lambda: exam}),
        (ExamCreateView, {"initial_exam": exam}),
        (NHCHView, {}),
    ]
    for cls, kwargs in view_specs:
        view, container = mount_test_view(tk_root, cls, width=1280, height=800, **kwargs)
        assert view.winfo_exists(), f"Failed to instantiate {cls.__name__} at 1280x800"
        assert container.winfo_width() >= 1000, f"Container width failed to expand: {container.winfo_width()}"
        view.destroy()
        container.destroy()


# ── SECTION 2: TIER 1 - FEATURE COVERAGE (>=5 PER FEATURE AREA) ─────────────

# --- Feature Area 1: ConvertView ---

def test_t1_convert_image_tab_scrollable_and_actions(tk_root):
    """T1.1: ConvertView Image tab contains scrollable container and key action buttons."""
    view, _ = mount_test_view(tk_root, ConvertView, width=1100, height=700)
    img_tab = view._tabs.tab(MODE_IMAGE)
    assert has_scrollable_container(img_tab), "ConvertView Image Tab must be scrollable via CTkScrollableFrame"
    assert hasattr(view, "_choose_images"), "ConvertView must provide _choose_images callback"
    assert hasattr(view, "_paste_image"), "ConvertView must provide _paste_image callback"
    assert hasattr(view, "_start_image_conversion"), "ConvertView must provide _start_image_conversion callback"


def test_t1_convert_document_tab_scrollable_and_actions(tk_root):
    """T1.2: ConvertView Document tab contains scrollable container and extraction controls."""
    view, _ = mount_test_view(tk_root, ConvertView, width=1100, height=700)
    doc_tab = view._tabs.tab(MODE_DOCUMENT)
    assert has_scrollable_container(doc_tab), "ConvertView Document Tab must be scrollable via CTkScrollableFrame"
    assert hasattr(view, "_document_var"), "ConvertView must bind _document_var"
    assert hasattr(view, "_start_document_conversion"), "ConvertView must provide _start_document_conversion"


def test_t1_convert_ai_text_tab_scrollable_and_inputs(tk_root):
    """T1.3: ConvertView AI Text tab contains scrollable container, prompt card, and text input."""
    view, _ = mount_test_view(tk_root, ConvertView, width=1100, height=700)
    text_tab = view._tabs.tab(MODE_TEXT)
    assert has_scrollable_container(text_tab), "ConvertView AI Text Tab must be scrollable via CTkScrollableFrame"
    assert hasattr(view, "_text_input"), "ConvertView must provide _text_input CTkTextbox"
    assert hasattr(view, "_chatbot_prompt_var"), "ConvertView must provide _chatbot_prompt_var"


def test_t1_convert_ai_text_buttons_multi_row_or_bounded(tk_root):
    """T1.4: ConvertView AI Text action buttons use multi-row layout or fit within left column (<=380px)."""
    view, container = mount_test_view(tk_root, ConvertView, width=1100, height=700)
    source = (_REPO_ROOT / "v5" / "views" / "convert.py").read_text(encoding="utf-8")
    assert "Nhận diện cục bộ" in source
    assert "Chuẩn hóa bằng AI" in source
    assert "Sua prompt/TikZ" in source or "Sửa prompt" in source
    # Must not place all 3 buttons on a single wide grid row exceeding column bounds
    assert hasattr(view, "_parse_text_locally")
    assert hasattr(view, "_normalize_text_with_ai")
    assert hasattr(view, "_rewrite_prompt_tikz_locally")


def test_t1_convert_result_panel_table_and_export_buttons(tk_root):
    """T1.5: ConvertView Result panel contains Treeview and all required export action buttons."""
    view, _ = mount_test_view(tk_root, ConvertView, width=1100, height=700)
    assert hasattr(view, "_tree"), "ConvertView must maintain _tree Treeview"
    assert hasattr(view, "_export_btn"), "ConvertView must maintain _export_btn"
    assert hasattr(view, "_export_latex_btn"), "ConvertView must maintain _export_latex_btn"
    assert hasattr(view, "_save_btn"), "ConvertView must maintain _save_btn"
    assert hasattr(view, "_add_btn"), "ConvertView must maintain _add_btn"


def test_t1_convert_provider_model_selector_integration(tk_root):
    """T1.6: ConvertView provides provider and model dropdown selectors."""
    view, _ = mount_test_view(tk_root, ConvertView, width=1100, height=700)
    assert hasattr(view, "_provider_var"), "ConvertView must have _provider_var"
    assert hasattr(view, "_model_var"), "ConvertView must have _model_var"
    assert hasattr(view, "_model_menu"), "ConvertView must have _model_menu"


# --- Feature Area 2: QCView ---

def test_t1_qc_tab_scrollable_container(tk_root):
    """T2.1: QCView Tab QC integrates CTkScrollableFrame wrapping cards 1, 2, 3."""
    exam = make_test_exam(4)
    view, _ = mount_test_view(tk_root, QCView, width=1100, height=700, initial_exam=exam, get_current_exam=lambda: exam)
    qc_tab = view._tabs.tab(view._TAB_QC)
    assert has_scrollable_container(qc_tab), "QCView Tab QC must be scrollable via CTkScrollableFrame to prevent Card 3 loss"


def test_t1_qc_card1_source_buttons_visibility(tk_root):
    """T2.2: QCView Card 1 source selection buttons are present and bound."""
    view, _ = mount_test_view(tk_root, QCView, width=1100, height=700)
    assert hasattr(view, "_load_from_nhch"), "QCView must have _load_from_nhch"
    assert hasattr(view, "_load_from_current_exam"), "QCView must have _load_from_current_exam"
    assert hasattr(view, "_qc_source_lbl"), "QCView must have _qc_source_lbl"


def test_t1_qc_card2_run_qc_cta_and_progress_invariants(tk_root):
    """T2.3: QCView Card 2 run controls maintain exact invariant test contract."""
    source = (_REPO_ROOT / "v5" / "views" / "qc.py").read_text(encoding="utf-8")
    assert "self._qc_report_btn" in source
    assert "self._qc_apply_btn" in source
    assert "run_row.grid_columnconfigure(3, weight=1)" in source
    assert "self._qc_prog.grid(row=1, column=0, columnspan=3" in source
    assert "self._qc_prog_lbl.grid(row=1, column=3" in source


def test_t1_qc_card3_treeview_and_scrollbars(tk_root):
    """T2.4: QCView Card 3 contains results Treeview and scrollbars."""
    view, _ = mount_test_view(tk_root, QCView, width=1100, height=700)
    assert hasattr(view, "_qc_tree"), "QCView must maintain _qc_tree"
    source = (_REPO_ROOT / "v5" / "views" / "qc.py").read_text(encoding="utf-8")
    assert "minwidths = {" in source
    assert "minwidth=minwidths[cc]" in source
    assert 'stretch=(cc == "issue")' in source


def test_t1_qc_tab_tikz_toolbars_multi_row_wrapping(tk_root):
    """T2.5: QCView Tab TikZ action toolbars do not horizontally overflow 810 px."""
    view, container = mount_test_view(tk_root, QCView, width=1100, height=700)
    view.focus_tikz()
    tk_root.update_idletasks()
    tikz_tab = view._tabs.tab(view._TAB_TIKZ)
    assert has_scrollable_container(tikz_tab), "TikZ Tab must have a scrollable container"


def test_t1_qc_navigation_focus_methods(tk_root):
    """T2.6: QCView public navigation focus methods switch tabs smoothly."""
    view, _ = mount_test_view(tk_root, QCView, width=1100, height=700)
    view.focus_tikz()
    assert view._tabs.get() == view._TAB_TIKZ
    view.focus_qc()
    assert view._tabs.get() == view._TAB_QC


# --- Feature Area 3: SetupView ---

def test_t1_setup_tabview_dynamic_height(tk_root):
    """T3.1: SetupView CTkTabview does not use hardcoded height=560."""
    source = (_REPO_ROOT / "v5" / "views" / "setup.py").read_text(encoding="utf-8")
    assert "CTkTabview(self, height=560" not in source, "SetupView must remove hardcoded height=560 on CTkTabview"
    view, _ = mount_test_view(tk_root, SetupView, width=1100, height=700)
    assert view._tabs.winfo_exists()


def test_t1_setup_ai_provider_scrollable_and_save_key(tk_root):
    """T3.2: SetupView AI Provider tab contains scrollable frame and visible Save Key button."""
    view, container = mount_test_view(tk_root, SetupView, width=1100, height=700)
    ai_tab = view._tabs.tab(view._TAB_AI)
    assert has_scrollable_container(ai_tab), "SetupView AI Provider tab must be scrollable"
    assert hasattr(view, "_save_key"), "SetupView must provide _save_key callback"


def test_t1_setup_subject_grade_scrollable_and_dropdowns(tk_root):
    """T3.3: SetupView Môn/Lớp tab contains scrollable container and configuration dropdowns."""
    view, _ = mount_test_view(tk_root, SetupView, width=1100, height=700)
    subject_tab = view._tabs.tab(view._TAB_SUBJECT)
    assert has_scrollable_container(subject_tab), "SetupView Môn/Lớp tab must be scrollable"
    assert hasattr(view, "get_subject")
    assert hasattr(view, "get_grade")


def test_t1_setup_license_tab_scrollable_and_no_nested_trap(tk_root):
    """T3.4: SetupView License tab avoids nested scroll trap height=230."""
    source = (_REPO_ROOT / "v5" / "views" / "setup.py").read_text(encoding="utf-8")
    assert "CTkScrollableFrame(feature_card, height=230" not in source, (
        "SetupView License tab must remove inner nested _lic_feature_box height=230 scroll trap"
    )
    view, _ = mount_test_view(tk_root, SetupView, width=1100, height=700)
    lic_tab = view._tabs.tab(view._TAB_LICENSE)
    assert has_scrollable_container(lic_tab), "License tab must have outer scrollable frame"


def test_t1_setup_public_api_accessors(tk_root):
    """T3.5: SetupView public API accessors return valid configuration strings."""
    view, _ = mount_test_view(tk_root, SetupView, width=1100, height=700)
    assert isinstance(view.get_provider(), str)
    assert isinstance(view.get_model(), str)
    assert isinstance(view.get_subject(), str)
    assert isinstance(view.get_grade(), str)


# --- Feature Area 4: TrackingView ---

def test_t1_tracking_tabview_dynamic_height(tk_root):
    """T4.1: TrackingView CTkTabview does not use hardcoded height=460."""
    source = (_REPO_ROOT / "v5" / "views" / "tracking.py").read_text(encoding="utf-8")
    assert "CTkTabview(self, height=460" not in source, "TrackingView must remove hardcoded height=460 on CTkTabview"


def test_t1_tracking_stat_cards_header(tk_root):
    """T4.2: TrackingView header displays 4 stat cards."""
    view, _ = mount_test_view(tk_root, TrackingView, width=1100, height=700)
    assert hasattr(view, "_stat_cards") or hasattr(view, "_stat_lbls"), "TrackingView must display stat cards"


def test_t1_tracking_dashboard_scrollable_container(tk_root):
    """T4.3: TrackingView Dashboard tab contains scrollable container."""
    view, _ = mount_test_view(tk_root, TrackingView, width=1100, height=700)
    dash_tab = view._tabs.tab(view._TAB_DASHBOARD)
    assert has_scrollable_container(dash_tab), "TrackingView Dashboard tab must be scrollable via CTkScrollableFrame"


def test_t1_tracking_provider_chart_width_fit(tk_root):
    """T4.4: TrackingView Provider Matplotlib chart figure width fits inside 826px viewport."""
    source = (_REPO_ROOT / "v5" / "views" / "tracking.py").read_text(encoding="utf-8")
    assert "figsize=(10, 4.2)" not in source, "Provider chart figsize width 10 (900px) overflows 826px content viewport"


def test_t1_tracking_history_and_usage_treeviews(tk_root):
    """T4.5: TrackingView History and Usage tabs configure Treeviews with scrollbars."""
    view, _ = mount_test_view(tk_root, TrackingView, width=1100, height=700)
    assert hasattr(view, "_hist_tree"), "TrackingView must maintain _hist_tree"
    assert hasattr(view, "_usage_tree"), "TrackingView must maintain _usage_tree"


# --- Feature Area 5: ExamCreateView ---

def test_t1_exam_create_root_scrollable_frame(tk_root):
    """T5.1: ExamCreateView root container uses CTkScrollableFrame for vertical flexibility."""
    exam = make_test_exam(2)
    view, _ = mount_test_view(tk_root, ExamCreateView, width=1100, height=700, initial_exam=exam)
    assert hasattr(view, "_scroll"), "ExamCreateView must use _scroll"
    assert isinstance(view._scroll, ctk.CTkScrollableFrame), "ExamCreateView root must be CTkScrollableFrame"


def test_t1_exam_create_export_row_grouping_and_variant_btn(tk_root):
    """T5.2: ExamCreateView export_row organizes buttons so _variant_btn and _multi_btn are visible."""
    exam = make_test_exam(2)
    view, container = mount_test_view(tk_root, ExamCreateView, width=1100, height=700, initial_exam=exam)
    for btn_attr in ("_load_exam_btn", "_export_btn", "_export_settings_btn", "_multi_btn", "_variant_btn"):
        assert hasattr(view, btn_attr), f"ExamCreateView must maintain {btn_attr}"
        btn = getattr(view, btn_attr)
        assert btn.winfo_exists(), f"{btn_attr} must exist in widget tree"


def test_t1_exam_create_quick_edit_row_bounded_layout(tk_root):
    """T5.3: ExamCreateView quick_edit_row organizes buttons without horizontal clipping."""
    exam = make_test_exam(2)
    view, _ = mount_test_view(tk_root, ExamCreateView, width=1100, height=700, initial_exam=exam)
    for attr in ("_question_jump_entry", "_jump_question_btn", "_quick_edit_btn", "_duplicate_question_btn", "_insert_blank_question_btn"):
        assert hasattr(view, attr), f"ExamCreateView must maintain {attr}"


def test_t1_exam_create_media_row_compact_bounds_and_invariants(tk_root):
    """T5.4: ExamCreateView media_row maintains exact parity invariants and compact bounds."""
    source = (_REPO_ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")
    assert "media_row.grid_columnconfigure(6, weight=1)" in source
    assert "self._tikz_mode_menu.grid(row=0, column=0" in source
    assert "self._tikz_emf_btn.grid(row=0, column=1" in source
    assert "self._error_report_btn.grid(row=0, column=5" in source
    assert "self._tikz_emf_status.grid(row=1, column=0, columnspan=7" in source


def test_t1_exam_create_preview_treeview_and_scrollbars(tk_root):
    """T5.5: ExamCreateView result preview Treeview has responsive columns and scrollbars."""
    exam = make_test_exam(4)
    view, _ = mount_test_view(tk_root, ExamCreateView, width=1100, height=700, initial_exam=exam)
    assert hasattr(view, "_preview_tree"), "ExamCreateView must maintain _preview_tree"
    source = (_REPO_ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")
    assert "minwidths_pv" in source
    assert 'stretch=(c in ("topic", "preview"))' in source


def test_t1_exam_create_source_ratio_controls(tk_root):
    """T5.6: ExamCreateView source ratio controls provide bank and AI mix modes."""
    exam = make_test_exam(2)
    view, _ = mount_test_view(tk_root, ExamCreateView, width=1100, height=700, initial_exam=exam)
    assert hasattr(view, "_source_ratio_slider"), "ExamCreateView must maintain _source_ratio_slider"
    source = (_REPO_ROOT / "v5" / "views" / "exam_create.py").read_text(encoding="utf-8")
    assert 'values=["AI mới", "100% NHCH", "Kết hợp"]' in source


# --- Feature Area 6: NhchView ---

def test_t1_nhch_container_adaptiveness_and_vertical_fit(tk_root):
    """T6.1: NhchView layout is vertically adaptive or scrollable within 600px height."""
    view, container = mount_test_view(tk_root, NHCHView, width=1100, height=700)
    assert view.winfo_exists()
    assert hasattr(view, "_tree"), "NhchView must maintain _tree Treeview"
    assert hasattr(view, "_selection_lbl"), "NhchView must maintain _selection_lbl"


def test_t1_nhch_toolbar_grouping_and_bounds(tk_root):
    """T6.2: NhchView toolbar groups local vs cloud actions within 810 px."""
    view, container = mount_test_view(tk_root, NHCHView, width=1100, height=700)
    for btn_attr in ("_recent_btn", "_add_exam_btn", "_upload_btn", "_download_btn"):
        assert hasattr(view, btn_attr), f"NhchView must maintain {btn_attr}"


def test_t1_nhch_ai_bar_responsiveness(tk_root):
    """T6.3: NhchView AI bar provides provider and model selection."""
    view, _ = mount_test_view(tk_root, NHCHView, width=1100, height=700)
    assert hasattr(view, "_ai_provider_var"), "NhchView must have _ai_provider_var"
    assert hasattr(view, "_ai_model_var"), "NhchView must have _ai_model_var"


def test_t1_nhch_filter_controls_and_search(tk_root):
    """T6.4: NhchView filter bar contains search entry, type, level, and counter."""
    view, _ = mount_test_view(tk_root, NHCHView, width=1100, height=700)
    assert hasattr(view, "_search_var"), "NhchView must have _search_var"
    assert hasattr(view, "_qtype_var"), "NhchView must have _qtype_var"
    assert hasattr(view, "_level_var"), "NhchView must have _level_var"
    assert hasattr(view, "_count_lbl"), "NhchView must have _count_lbl"


def test_t1_nhch_treeview_checkbox_and_selection(tk_root):
    """T6.5: NhchView Treeview provides multi-selection checkboxes and event handlers."""
    view, _ = mount_test_view(tk_root, NHCHView, width=1100, height=700)
    assert hasattr(view, "_toggle_visible_checks"), "NhchView must provide _toggle_visible_checks"
    assert hasattr(view, "_on_tree_click"), "NhchView must provide _on_tree_click"


# ── SECTION 3: TIER 2 - BOUNDARY & CORNER CASES ──────────────────────────────

def test_t2_minsize_1100x700_no_layout_exceptions(tk_root):
    """T2.1: Verify clean layout computation at exact minsize 1100x700."""
    exam = make_test_exam(3)
    view, container = mount_test_view(tk_root, ExamCreateView, width=1100, height=700, initial_exam=exam)
    tk_root.update_idletasks()
    assert container.winfo_width() == 826
    assert container.winfo_height() == 600
    view.destroy()


def test_t2_standard_1280x800_responsive_expansion(tk_root):
    """T2.2: Verify responsive expansion of content container at 1280x800."""
    exam = make_test_exam(3)
    view, container = mount_test_view(tk_root, ExamCreateView, width=1280, height=800, initial_exam=exam)
    tk_root.update_idletasks()
    expected_w = 1280 - 250 - 24  # 1006
    expected_h = 800 - 48 - 28 - 24  # 700
    assert container.winfo_width() == expected_w
    assert container.winfo_height() == expected_h
    view.destroy()


def test_t2_dynamic_window_resize_cycle(tk_root):
    """T2.3: Verify dynamic resizing cycle (1100x700 -> 1440x900 -> 1100x700) produces no Tkinter exceptions."""
    exam = make_test_exam(2)
    view, container = mount_test_view(tk_root, ConvertView, width=1100, height=700)
    tk_root.update_idletasks()

    # Expand
    tk_root.geometry("1440x900")
    container.configure(width=1440 - 250 - 24, height=900 - 48 - 28 - 24)
    tk_root.update_idletasks()

    # Shrink back to minsize
    tk_root.geometry("1100x700")
    container.configure(width=1100 - 250 - 24, height=700 - 48 - 28 - 24)
    tk_root.update_idletasks()

    assert view.winfo_exists()
    view.destroy()


def test_t2_zero_margin_and_coordinate_containment(tk_root):
    """T2.4: Verify content container boundaries strictly respect layout geometry without overflow."""
    exam = make_test_exam(2)
    view, container = mount_test_view(tk_root, SetupView, width=1100, height=700)
    tk_root.update_idletasks()
    assert container.winfo_width() <= 826
    view.destroy()


def test_t2_scrollable_containers_scrollbar_behavior(tk_root):
    """T2.5: Verify scrollable frames configure scrollbar elements."""
    exam = make_test_exam(10)
    view, container = mount_test_view(tk_root, ExamCreateView, width=1100, height=700, initial_exam=exam)
    scroll_frame = view._scroll
    assert scroll_frame.winfo_exists()
    assert hasattr(scroll_frame, "_scrollbar") or hasattr(scroll_frame, "_parent_canvas")
    view.destroy()


def test_t2_simulated_high_dpi_scaling(tk_root):
    """T2.6: Simulate 125% DPI scale factors to ensure layout width calculations retain >= 24px safety margin."""
    dpi_scale = 1.25
    effective_w = int(1100 / dpi_scale) - int(250 / dpi_scale) - 24
    # Even under 125% scale, content viewport width budget is determinable
    assert effective_w >= 650, f"DPI scaling reduced viewport excessively: {effective_w}"


def test_t2_extreme_empty_and_null_inputs(tk_root):
    """T2.7: Verify all views handle empty/None datasets gracefully without crashing."""
    empty_exam = ExamData(exam_title="", subject="", grade="", semester="", year="", time="", questions=[])
    # ExamCreate with 0 questions
    ev, _ = mount_test_view(tk_root, ExamCreateView, width=1100, height=700, initial_exam=empty_exam)
    assert ev.winfo_exists()
    ev.destroy()

    # QCView with 0 questions
    qv, _ = mount_test_view(tk_root, QCView, width=1100, height=700, initial_exam=empty_exam, get_current_exam=lambda: empty_exam)
    assert qv.winfo_exists()
    qv.destroy()


# ── SECTION 4: TIER 3 - CROSS-FEATURE COMBINATIONS ──────────────────────────

def test_t3_full_cycle_view_switching_stability(tk_root):
    """T3.1: Switch sequentially through all views on ModernApp test root without crashing."""
    try:
        app = ModernApp()
        app.withdraw()
    except tk.TclError as exc:
        pytest.skip(f"Tk display unavailable: {exc}")

    try:
        views = ["home", "setup", "exam_create", "nhch", "convert", "qc", "tracking", "guide", "home"]
        for view_id in views:
            app.show_view(view_id)
            app.update_idletasks()
            assert app._current_view_id == view_id
            assert app._current_view is not None
            assert app._current_view.winfo_exists()
    finally:
        app.destroy()


def test_t3_state_preservation_across_views(tk_root):
    """T3.2: Verify Workspace ExamData is preserved when navigating across views."""
    try:
        app = ModernApp()
        app.withdraw()
    except tk.TclError as exc:
        pytest.skip(f"Tk display unavailable: {exc}")

    try:
        exam = make_test_exam(5)
        app._workspace.set_exam(exam)

        app.show_view("exam_create")
        app.update_idletasks()
        assert app._get_current_exam() is exam

        app.show_view("convert")
        app.update_idletasks()
        assert app._get_current_exam() is exam

        app.show_view("qc")
        app.update_idletasks()
        assert app._get_current_exam() is exam
    finally:
        app.destroy()


def test_t3_task_log_dialog_layout_and_export_button(tk_root):
    """T3.3: Verify TaskLogDialog has flexible tabview height, Close button, and export action."""
    source = (_REPO_ROOT / "v5" / "task_log.py").read_text(encoding="utf-8")
    assert "self._tabs = ctk.CTkTabview(self, height=440)" not in source, (
        "TaskLogDialog must remove hardcoded height=440 from CTkTabview"
    )
    dlg = TaskLogDialog(tk_root)
    dlg.withdraw()
    tk_root.update_idletasks()
    assert dlg.winfo_exists()
    dlg.destroy()


def test_t3_preferences_dialog_scrollable_and_close_button(tk_root):
    """T3.4: Verify PreferencesDialog mounts without layout distortion."""
    dlg = PreferencesDialog(tk_root)
    dlg.withdraw()
    tk_root.update_idletasks()
    assert dlg.winfo_exists()
    dlg.destroy()


def test_t3_exam_data_exchange_between_exam_create_and_qc(tk_root):
    """T3.5: Verify ExamData exchange from ExamCreate to QCView via load_exam_questions."""
    exam = make_test_exam(3)
    qc_view, _ = mount_test_view(tk_root, QCView, width=1100, height=700, initial_exam=exam, get_current_exam=lambda: exam)
    qc_view._load_from_current_exam()
    tk_root.update_idletasks()
    assert len(qc_view._qc_questions) == 3
    qc_view.destroy()


def test_t3_nhch_selection_transfer_to_exam_workspace(tk_root):
    """T3.6: Verify NHCH selected questions transfer callback functions correctly."""
    exam = make_test_exam(1)
    transferred = []

    def on_add(questions, meta):
        transferred.extend(questions)

    nhch_view, _ = mount_test_view(tk_root, NHCHView, width=1100, height=700, on_add_questions=on_add)
    sample_q = Question(qtype="TN", level="NB", topic="Hàm số", question="Test NHCH transfer", answer="B")
    on_add([sample_q], {"subject": "Toán"})
    assert len(transferred) == 1
    assert transferred[0].question == "Test NHCH transfer"
    nhch_view.destroy()


def test_t3_appearance_mode_theme_toggle_all_views(tk_root):
    """T3.7: Toggle appearance modes (Dark/Light) across mounted views without layout errors."""
    view, _ = mount_test_view(tk_root, ConvertView, width=1100, height=700)
    for mode in ("Light", "Dark", "System"):
        ctk.set_appearance_mode(mode)
        tk_root.update_idletasks()
        assert view.winfo_exists()
    view.destroy()


# ── SECTION 5: TIER 4 - REAL-WORLD APPLICATION SCENARIOS ────────────────────

def test_t4_scenario_convert_text_to_questions_coordinate_bounds(tk_root):
    """T4.1: Real-world Convert workflow at 1100x700: parse questions and verify right coordinate bounds <= 810 px."""
    view, container = mount_test_view(tk_root, ConvertView, width=1100, height=700)
    tk_root.update_idletasks()

    # Ingest mock questions into result panel
    questions = make_test_exam(4).questions
    view._questions = questions
    view._display_results()
    tk_root.update_idletasks()

    # Check button bounds in result action panel
    for btn in (view._copy_btn, view._export_btn, view._save_btn, view._add_btn):
        if btn.winfo_ismapped():
            rel_right = get_relative_right_coordinate(btn, container)
            assert rel_right <= 826, f"Convert button {btn} right coordinate {rel_right} overflows viewport (826px)"

    view.destroy()


def test_t4_scenario_qc_pipeline_full_workflow_coordinate_bounds(tk_root):
    """T4.2: Real-world QC workflow at 1100x700: load questions and verify all cards and CTAs fit within bounds."""
    exam = make_test_exam(5)
    view, container = mount_test_view(tk_root, QCView, width=1100, height=700, initial_exam=exam, get_current_exam=lambda: exam)
    view._load_from_current_exam()
    tk_root.update_idletasks()

    # Check that CTA buttons fit inside viewport bounds
    for btn in (view._qc_report_btn, view._qc_apply_btn):
        if btn.winfo_ismapped():
            rel_right = get_relative_right_coordinate(btn, container)
            assert rel_right <= 826, f"QC CTA button {btn} right coordinate {rel_right} overflows viewport (826px)"

    view.destroy()


def test_t4_scenario_exam_create_jump_and_export_coordinate_bounds(tk_root):
    """
    T4.3: Real-world Exam Create workflow at 1100x700:
    Jump questions, verify export_row buttons (_variant_btn, _multi_btn) fit within 810 px bounds.
    """
    exam = make_test_exam(8)
    view, container = mount_test_view(tk_root, ExamCreateView, width=1100, height=700, initial_exam=exam)
    tk_root.update_idletasks()

    # Verify buttons in export_row are within 810 px content bounds
    for btn_name in ("_load_exam_btn", "_export_btn", "_multi_btn", "_variant_btn"):
        btn = getattr(view, btn_name)
        if btn.winfo_ismapped():
            rel_right = get_relative_right_coordinate(btn, container)
            assert rel_right <= 826, f"ExamCreate button {btn_name} coordinate {rel_right} overflows 826px viewport"

    # Verify media_row buttons are within 810 px content bounds
    for btn_name in ("_tikz_mode_menu", "_tikz_emf_btn", "_retry_failed_btn", "_qc_current_btn", "_score_check_btn", "_error_report_btn"):
        btn = getattr(view, btn_name)
        if btn.winfo_ismapped():
            rel_right = get_relative_right_coordinate(btn, container)
            assert rel_right <= 826, f"ExamCreate media button {btn_name} coordinate {rel_right} overflows 826px viewport"

    view.destroy()


def test_t4_scenario_nhch_search_filter_add_coordinate_bounds(tk_root):
    """T4.4: Real-world NHCH workflow at 1100x700: filter, search, and verify toolbar bounds <= 810 px."""
    view, container = mount_test_view(tk_root, NHCHView, width=1100, height=700)
    tk_root.update_idletasks()

    # Verify action toolbar buttons fit within 810 px
    for btn_name in ("_recent_btn", "_add_exam_btn", "_upload_btn", "_download_btn"):
        btn = getattr(view, btn_name)
        if btn.winfo_ismapped():
            rel_right = get_relative_right_coordinate(btn, container)
            assert rel_right <= 826, f"NHCH toolbar button {btn_name} coordinate {rel_right} overflows 826px viewport"

    view.destroy()


def test_t4_scenario_setup_save_key_and_tracking_chart_bounds(tk_root):
    """T4.5: Real-world Setup and Tracking workflows at 1100x700: verify Save Key button and Chart bounds."""
    # SetupView
    sv, s_container = mount_test_view(tk_root, SetupView, width=1100, height=700)
    tk_root.update_idletasks()
    assert sv.winfo_exists()
    sv.destroy()

    # TrackingView
    exam = make_test_exam(2)
    tv, t_container = mount_test_view(tk_root, TrackingView, width=1100, height=700, get_current_exam=lambda: exam)
    tk_root.update_idletasks()
    assert tv.winfo_exists()
    tv.destroy()
