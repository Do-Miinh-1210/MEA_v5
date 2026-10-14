"""
tests/test_timer_and_global_mousewheel.py — Kiểm tra bộ đếm giờ (stopwatch/timer)
khi tạo/trộn đề và hệ thống cuộn chuột (MouseWheel) toàn ứng dụng.
"""
import time
import pathlib
import pytest
import tkinter as tk
from ui.tab_shuffle import TabShuffle, LoadedExamItem
from omr_exam.models import ExamSection, ExamQuestion, OptionItem


def test_format_duration_helper():
    """Kiểm tra format thời gian thân thiện."""
    assert TabShuffle._format_duration(5.4) == "5.4 giây"
    assert TabShuffle._format_duration(45.0) == "45.0 giây"
    assert TabShuffle._format_duration(60.0) == "1 phút"
    assert TabShuffle._format_duration(125.0) == "2 phút 05 giây"
    assert TabShuffle._format_duration(180.0) == "3 phút"
    assert TabShuffle._format_duration(3605.0) == "60 phút 05 giây"


def test_tab_shuffle_timer_lifecycle():
    """Kiểm tra vòng đời của bộ đếm giờ trong TabShuffle."""
    root = tk.Tk()
    root.withdraw()
    try:
        tab = TabShuffle(root)

        # 1. Ban đầu timer chưa chạy
        assert not tab._ai_timer_running
        assert tab._ai_timer_start == 0.0

        # 2. Khởi động timer
        tab._start_ai_timer("Đang kết nối AI...")
        assert tab._ai_timer_running
        assert tab._ai_timer_start > 0
        assert "Đang kết nối AI..." in tab._lbl_shuffle_status.cget("text")
        assert "⏱️" in tab._lbl_shuffle_status.cget("text")

        # 3. Cập nhật tiến trình
        tab._update_ai_status("Đang xử lý câu 3/10")
        assert "Đang xử lý câu 3/10" in tab._lbl_shuffle_status.cget("text")
        assert "⏱️" in tab._lbl_shuffle_status.cget("text")

        # 4. Giả lập trôi qua một khoảng thời gian
        tab._ai_timer_start -= 65.0  # Giả lập đã chạy 65 giây
        tab._tick_ai_timer()
        assert "01:05" in tab._lbl_shuffle_status.cget("text")

        # 5. Dừng timer
        elapsed = tab._stop_ai_timer()
        assert not tab._ai_timer_running
        assert elapsed >= 65.0
    finally:
        root.destroy()


def test_no_unbind_all_in_ui_codebase():
    """Kiểm tra không còn bất kỳ lệnh unbind_all nào gây hại app trong thư mục ui/."""
    ui_dir = pathlib.Path("ui")
    for py_file in ui_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "unbind_all" not in content, f"File {py_file} vẫn còn unbind_all gây lỗi mất cuộn chuột toàn app!"


def test_global_mousewheel_configured_in_main_window():
    """Kiểm tra main_window.py có hàm _setup_global_mousewheel với add='+' và scroll bubbling."""
    mw_source = pathlib.Path("ui/main_window.py").read_text(encoding="utf-8")
    assert "def _setup_global_mousewheel(self) -> None:" in mw_source
    assert 'self.bind_all("<MouseWheel>", _on_mousewheel, add="+")' in mw_source
    assert "canvas_units" in mw_source
    assert "text_units" in mw_source
    # Kiểm tra scroll bubbling: khi Text/Treeview cuộn hết thì nhường sự kiện cho Canvas cha
    assert "yview_scroll" in mw_source


def test_tab_shuffle_mousewheel_and_text_delegation():
    """Kiểm tra TabShuffle có canvas, scrollable_frame và hỗ trợ cuộn chuột thông minh."""
    root = tk.Tk()
    root.withdraw()
    try:
        tab = TabShuffle(root)
        assert hasattr(tab, "_canvas")
        assert hasattr(tab, "_scrollable_frame")
        assert hasattr(tab, "_txt_preview")
        assert hasattr(tab, "_txt_keys")
        assert hasattr(tab, "_txt_map")

        # Kiểm tra bindings có MouseWheel
        assert "<MouseWheel>" in tab._canvas.bind()
        assert "<MouseWheel>" in tab._txt_preview.bind()
        assert "<MouseWheel>" in tab._txt_keys.bind()
        assert "<MouseWheel>" in tab._txt_map.bind()
    finally:
        root.destroy()


def test_standard_shuffle_measures_and_displays_timer(monkeypatch):
    """Kiểm tra trộn đề thông thường đo đạc thời gian thực hiện và hiển thị ⏱️."""
    root = tk.Tk()
    root.withdraw()
    try:
        tab = TabShuffle(root)

        q1 = ExamQuestion(
            index=1, qtype="TN", content="Câu 1: 1+1=?",
            options=[OptionItem("A", "2", True), OptionItem("B", "3", False)]
        )
        sec = ExamSection(title="Phần 1", questions=[q1])
        item = LoadedExamItem(name="Đề 1", file_path=None, sections=[sec])
        tab._loaded_exams.append(item)
        tab._active_exam_idx = 0

        # Mock messagebox.showinfo để không hiển thị popup khi chạy test tự động
        monkeypatch.setattr("tkinter.messagebox.showinfo", lambda *args, **kwargs: None)

        tab._on_do_shuffle()

        status = tab._lbl_shuffle_status.cget("text")
        assert "✓ Đã trộn thành công" in status
        assert "⏱️" in status
        assert "s" in status
    finally:
        root.destroy()


def test_tab_config_key_expand_and_mousewheel():
    """Kiểm tra tính năng mở rộng/thu nhỏ ô nhập API key và cuộn chuột ngang/dọc trong TabConfig."""
    root = tk.Tk()
    root.withdraw()
    try:
        from ui.tab_config import TabConfig
        tab = TabConfig(root, on_matrix_loaded=lambda *a: None)
        assert hasattr(tab, "_key_expanded")
        assert not tab._key_expanded
        assert tab._key_text.cget("height") == 1
        assert "Mở rộng" in tab._expand_btn.cget("text")

        # Test mở rộng
        tab._toggle_expand_key()
        assert tab._key_expanded
        assert tab._key_text.cget("height") == 5
        assert "Thu nhỏ" in tab._expand_btn.cget("text")

        # Test thu nhỏ lại
        tab._toggle_expand_key()
        assert not tab._key_expanded
        assert tab._key_text.cget("height") == 1
        assert "Mở rộng" in tab._expand_btn.cget("text")

        # Test cuộn chuột ngang
        sample_key = "sk-0164a072ee86d38e-ozkcup-30196a48-long-api-key-" * 5
        tab._set_key_text(sample_key)
        tab._key_text.xview_scroll(5, "units")
        first, last = tab._key_text.xview()
        assert first > 0.0
    finally:
        root.destroy()

