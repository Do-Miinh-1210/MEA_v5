"""Tests for PDF vector -> EMF conversion through Inkscape."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from services import tikz_vector_export


def test_find_inkscape_accepts_explicit_path(tmp_path):
    executable = tmp_path / "inkscape.exe"
    executable.write_bytes(b"fake")

    assert tikz_vector_export.find_inkscape(executable) == executable.resolve()


def test_convert_pdf_to_emf_invokes_vector_export_flags(tmp_path, monkeypatch):
    executable = tmp_path / "inkscape.exe"
    executable.write_bytes(b"fake")
    source = tmp_path / "figure.pdf"
    source.write_bytes(b"%PDF-test")
    target = tmp_path / "figure.emf"
    calls: list[list[str]] = []

    def fake_run(argv, **_kwargs):
        calls.append(argv)
        target.write_bytes(b"EMF-test")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(tikz_vector_export.subprocess, "run", fake_run)

    result = tikz_vector_export.convert_pdf_to_emf(
        source,
        target,
        inkscape_path=executable,
    )

    assert result == target.resolve()
    assert calls
    assert "--export-type=emf" in calls[0]
    assert f"--export-filename={target.resolve()}" in calls[0]
    assert "--export-overwrite" in calls[0]
    assert "--export-text-to-path" in calls[0]


def test_convert_pdf_to_emf_reports_missing_pdf(tmp_path):
    with pytest.raises(FileNotFoundError, match="PDF TikZ"):
        tikz_vector_export.convert_pdf_to_emf(tmp_path / "missing.pdf")


def test_copy_emf_to_clipboard_reports_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="EMF"):
        tikz_vector_export.copy_emf_to_clipboard(tmp_path / "missing.emf")
