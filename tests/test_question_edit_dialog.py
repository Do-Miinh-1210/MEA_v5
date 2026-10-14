"""Smoke + behaviour tests for ui.dialog_nhch_preview._QuestionEditDialog.

The dialog is the "Chỉnh sửa câu hỏi" window opened from the NHCH preview.
After the v4.1 redesign:

  - TN option entries and DS item entries are tk.Text widgets (was Entry).
    Long math content with ${...}$ formulas can now wrap and be edited
    in full instead of being clipped at width=50.
  - DS items get a per-item solution editor saved into q.item_solutions.
  - The "Đáp án:" plain text field is hidden for DS and TL where it has
    no meaning.

These tests build the dialog headless (root.withdraw) and verify the new
widget types and the save round-trip.
"""
import tkinter as tk

import pytest

from core.models import Question
from ui.dialog_nhch_preview import _QuestionEditDialog


@pytest.fixture(scope="module")
def tk_root():
    # Tk init/teardown trên Windows có thể flake nếu mỗi test tạo+huỷ
    # tk.Tk() — share 1 root cho toàn module, đảm bảo Tcl/Tk init đúng 1 lần.
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk display is unavailable: {exc}")
    root.withdraw()
    yield root
    root.destroy()


def _ds_fixture() -> Question:
    return Question(
        question_id="12H1V2-01",
        qtype="DS",
        level="VD",
        topic="Phương pháp tọa độ trong không gian",
        points=1.0,
        question="Trong không gian ${Oxyz}$, cho mặt cầu ${(S)}$.",
        items={
            "a": "Vectơ ${\\vec{u} = (1; -1; 0)}$ là một vectơ chỉ phương.",
            "b": "Khoảng cách bằng ${6\\sqrt{2}}$.",
            "c": "Bán kính bằng 25.",
            "d": "Có thời điểm tiếp xúc.",
        },
        answers={"a": True, "b": True, "c": False, "d": False},
        item_solutions={
            "a": "Đúng. Vì AB = (1; -1; 0).",
            "b": "Đúng. Tính được 6√2.",
            "c": "Sai. R = 5.",
            "d": "Sai. Vô nghiệm.",
        },
        solution="",
    )


def _tn_fixture() -> Question:
    return Question(
        question_id="TN-01",
        qtype="TN",
        level="TH",
        topic="Đạo hàm",
        points=0.25,
        question="Đạo hàm của ${y = x^2 + 3x}$?",
        options={"A": "${2x + 3}$", "B": "${2x}$", "C": "${x^2}$", "D": "${3}$"},
        answer="A",
        solution="${y' = 2x + 3}$.",
    )


def test_ds_dialog_uses_text_widgets_for_items_and_per_item_solutions(tk_root):
    q = _ds_fixture()
    dlg = _QuestionEditDialog(tk_root, q, subject="Toán", grade="12")
    try:
        # Items moved from StringVar(Entry) to Text widget — long math is
        # no longer clipped to width=50.
        for k in "abcd":
            assert isinstance(dlg._ds_entries[k], tk.Text)
            loaded = dlg._ds_entries[k].get("1.0", "end-1c").strip()
            assert loaded == q.items[k]

        # New: per-item solution editors.
        for k in "abcd":
            assert isinstance(dlg._ds_sol_texts[k], tk.Text)
            loaded = dlg._ds_sol_texts[k].get("1.0", "end-1c").strip()
            assert loaded == q.item_solutions[k]
    finally:
        dlg.destroy()


def test_ds_dialog_save_round_trip(tk_root):
    q = _ds_fixture()
    dlg = _QuestionEditDialog(tk_root, q, subject="Toán", grade="12")
    try:
        # User edits item 'a' text, flips answer for 'c', rewrites
        # per-item solution for 'a'.
        dlg._ds_entries["a"].delete("1.0", "end")
        dlg._ds_entries["a"].insert("1.0", "Edited a content")
        dlg._ds_answers["c"].set(True)
        dlg._ds_sol_texts["a"].delete("1.0", "end")
        dlg._ds_sol_texts["a"].insert("1.0", "New solution a")
    finally:
        # _save destroys the dialog, so wrap in try/finally above the call.
        pass
    dlg._save()

    assert q.items["a"] == "Edited a content"
    assert q.answers == {"a": True, "b": True, "c": True, "d": False}
    assert q.item_solutions["a"] == "New solution a"
    # Items not edited stay intact.
    assert q.items["b"].startswith("Khoảng cách")
    assert q.item_solutions["d"] == "Sai. Vô nghiệm."


def test_tn_dialog_uses_text_widgets_for_options(tk_root):
    q = _tn_fixture()
    dlg = _QuestionEditDialog(tk_root, q, subject="Toán", grade="12")
    try:
        for k in "ABCD":
            assert isinstance(dlg._opt_entries[k], tk.Text)
            loaded = dlg._opt_entries[k].get("1.0", "end-1c").strip()
            assert loaded == q.options[k]
    finally:
        dlg.destroy()


def test_tn_dialog_save_round_trip(tk_root):
    q = _tn_fixture()
    dlg = _QuestionEditDialog(tk_root, q, subject="Toán", grade="12")
    dlg._opt_entries["B"].delete("1.0", "end")
    dlg._opt_entries["B"].insert("1.0", "${2x + 3}$ alt")
    dlg._answer_var.set("B")
    dlg._save()

    assert q.options["B"] == "${2x + 3}$ alt"
    assert q.answer == "B"


def test_mousewheel_on_text_does_not_scroll_outer_canvas(tk_root):
    """User report: cuộn chuột trên 'Nội dung câu hỏi' Text widget khiến cả
    dialog cũng cuộn theo. Handler phải bỏ qua canvas scroll khi event xuất
    phát từ Text (Text tự xử lý)."""
    q = _ds_fixture()
    # Đẩy thêm nội dung dài cho question_text để Text có thứ để cuộn nội bộ
    q.question = "\n".join(f"dòng {i} ${{x_{i}}}$" for i in range(60))
    dlg = _QuestionEditDialog(tk_root, q, subject="Toán", grade="12")
    dlg.update_idletasks()
    try:
        # Tìm canvas chứa content (canvas + scrollbar được pack vào dialog)
        canvas = None
        for child in dlg.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
                break
        assert canvas is not None, "canvas not found in dialog"

        # State ban đầu của canvas viewport
        before = canvas.yview()

        # Simulate wheel event PHÁT TỪ Text widget của Nội dung câu hỏi
        evt = tk.Event()
        evt.widget = dlg._question_text
        evt.delta = -120  # cuộn xuống
        evt.x = 100
        evt.y = 100
        # Trigger handler trực tiếp — bind_all đã wired tới handler thật
        dlg._question_text.event_generate("<MouseWheel>", delta=-120, when="now")
        dlg.update_idletasks()

        after = canvas.yview()
        # Canvas viewport KHÔNG được cuộn theo
        assert before == after, (
            f"Canvas scrolled when wheel was on Text widget: {before} -> {after}"
        )
    finally:
        dlg.destroy()
