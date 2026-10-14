"""Tests for modernized admin panels and dialogs."""
from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

from admin.dialog_add_user import AddUserDialog
from admin.dialog_system import SystemControlDialog
from admin.dialog_lookup import LookupUserDialog
from admin.dialog_admin_info import AdminInfoDialog
from admin.panel_users import UserTablePanel


def _make_dummy_app():
    root = tk.Tk()
    root.withdraw()
    root.all_records = [
        {
            "machine_id": "TEST-MID-001",
            "name": "Thầy Nam",
            "tier": "pro",
            "status": "active",
            "expiry": "2026-12-31",
            "admin_api_key": "sk-12345",
            "issued_at": "2026-01-01T00:00:00",
            "last_check": "2026-08-01T10:00:00",
            "note": "THPT Chuyên",
        },
        {
            "machine_id": "TEST-MID-002",
            "name": "Cô Lan",
            "tier": "basic",
            "status": "revoked",
            "expiry": "",
            "admin_api_key": "",
            "issued_at": "2026-02-01T00:00:00",
            "last_check": "",
            "note": "Hết hạn",
        },
    ]
    root.maintenance_on = False
    root.set_status = MagicMock()
    root.refresh = MagicMock()
    return root


def test_add_user_dialog_instantiation():
    app = _make_dummy_app()
    try:
        dlg = AddUserDialog(app, app)
        assert hasattr(dlg, "_mid_var")
        assert hasattr(dlg, "_name_var")
        assert hasattr(dlg, "_tier_var")
        assert hasattr(dlg, "_expiry_editor")
        assert dlg._tier_var.get() == "pro"
        dlg.destroy()
    finally:
        app.destroy()


def test_system_control_dialog_instantiation():
    app = _make_dummy_app()
    try:
        dlg = SystemControlDialog(app, app)
        assert hasattr(dlg, "_maint_toggle_btn")
        dlg.destroy()
    finally:
        app.destroy()


def test_lookup_user_dialog_search():
    app = _make_dummy_app()
    try:
        dlg = LookupUserDialog(app, app)
        dlg._mid_var.set("TEST-MID-001")
        dlg._do_check()
        assert "Thầy Nam" in dlg._result_text.cget("text")
        assert "ACTIVE" in dlg._result_text.cget("text")
        dlg.destroy()
    finally:
        app.destroy()


def test_admin_info_dialog_instantiation():
    app = _make_dummy_app()
    try:
        dlg = AdminInfoDialog(app, app)
        dlg.destroy()
    finally:
        app.destroy()


def test_user_table_panel_filtering_and_status():
    app = _make_dummy_app()
    try:
        panel = UserTablePanel(app, app)
        panel.apply_filter()
        assert len(panel._filtered_records) == 2

        # Search by keyword
        panel._search_var.set("Nam")
        panel.apply_filter()
        assert len(panel._filtered_records) == 1
        assert panel._filtered_records[0]["machine_id"] == "TEST-MID-001"

        # Filter by status
        panel._search_var.set("")
        panel._filter_var.set("revoked")
        panel.apply_filter()
        assert len(panel._filtered_records) == 1
        assert panel._filtered_records[0]["machine_id"] == "TEST-MID-002"

        panel.destroy()
    finally:
        app.destroy()
