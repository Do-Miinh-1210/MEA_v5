from datetime import date

from admin.date_picker import (
    auto_format_display_date,
    compute_future_display,
    display_to_iso,
    expiry_preview_text,
    iso_to_display,
)


def test_auto_format_display_date_inserts_dashes():
    assert auto_format_display_date("11062026") == "11-06-2026"
    assert auto_format_display_date("11/06/2026") == "11-06-2026"
    assert auto_format_display_date("1106") == "11-06"


def test_compute_future_display_uses_day_offsets():
    assert compute_future_display(45, today=date(2026, 6, 11)) == "26-07-2026"


def test_display_iso_roundtrip():
    assert display_to_iso("11-06-2026") == "2026-06-11"
    assert iso_to_display("2026-06-11") == "11-06-2026"
    assert iso_to_display("") == ""


def test_expiry_preview_text_reports_states():
    today = date(2026, 6, 11)
    assert expiry_preview_text("", today=today)[0] == "♾️ Vĩnh viễn"
    assert "hôm nay" in expiry_preview_text("11-06-2026", today=today)[0]
    assert "Còn 10 ngày" in expiry_preview_text("21-06-2026", today=today)[0]
    assert "Đã hết hạn" in expiry_preview_text("01-06-2026", today=today)[0]
