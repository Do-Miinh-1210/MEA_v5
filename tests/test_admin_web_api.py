from __future__ import annotations

from types import SimpleNamespace

import admin_web.api.index as admin_web


def test_get_db_prefers_service_role_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "publishable-key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.setattr(admin_web, "_load_config_fallback", lambda: ("", ""))

    calls = {}

    def fake_create_client(url, key):
        calls["url"] = url
        calls["key"] = key
        return object()

    monkeypatch.setattr(admin_web, "create_client", fake_create_client)

    admin_web.get_db()

    assert calls == {
        "url": "https://example.supabase.co",
        "key": "service-role-key",
    }


def test_data_endpoint_returns_json_error(monkeypatch):
    def fail_db():
        raise ValueError("missing supabase config")

    monkeypatch.setattr(admin_web, "get_db", fail_db)

    response = admin_web.app.test_client().get("/api/data")

    assert response.status_code == 500
    assert response.is_json
    assert response.get_json()["ok"] is False
    assert "missing supabase config" in response.get_json()["error"]


def test_health_reports_config_source(monkeypatch):
    class FakeQuery:
        def select(self, *args, **kwargs):
            return self

        def limit(self, *_args):
            return self

        def execute(self):
            return SimpleNamespace(count=3)

    class FakeDb:
        def table(self, _name):
            return FakeQuery()

    monkeypatch.setattr(
        admin_web,
        "get_supabase_config",
        lambda: ("https://example.supabase.co", "key", "config.py"),
    )
    monkeypatch.setattr(admin_web, "get_db", lambda: FakeDb())

    response = admin_web.app.test_client().get("/api/health")
    data = response.get_json()

    assert response.status_code == 200
    assert data["ok"] is True
    assert data["config_source"] == "config.py"
    assert data["licenses_count"] == 3
