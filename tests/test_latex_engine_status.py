"""
tests/test_latex_engine_status.py -- UI-friendly LaTeX engine diagnostics.
"""
from __future__ import annotations

import services.latex_engine as latex_engine


def test_check_engine_status_reports_missing_engine(monkeypatch):
    latex_engine.reset_cache()
    monkeypatch.setattr(latex_engine.shutil, "which", lambda _name: None)

    status = latex_engine.check_engine_status()

    assert status["ok"] is False
    assert status["engine"] == ""
    assert status["available"] == []
    assert "MiKTeX" in "\n".join(status["install_hints"])


def test_check_engine_status_reports_detected_engine(monkeypatch):
    latex_engine.reset_cache()

    def fake_which(name: str):
        return r"C:\tex\pdflatex.exe" if name == "pdflatex" else None

    monkeypatch.setattr(latex_engine.shutil, "which", fake_which)

    status = latex_engine.check_engine_status()

    assert status["ok"] is True
    assert status["engine"] == "pdflatex"
    assert status["binary"] == r"C:\tex\pdflatex.exe"
    assert status["available"] == ["pdflatex"]


def test_smoke_test_engine_returns_missing_without_subprocess(monkeypatch):
    latex_engine.reset_cache()
    monkeypatch.setattr(latex_engine.shutil, "which", lambda _name: None)

    status = latex_engine.smoke_test_engine(timeout=1)

    assert status["ok"] is False
    assert status["engine"] == ""
    assert "Không tìm thấy LaTeX engine" in status["message"]
