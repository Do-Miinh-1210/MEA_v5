"""
v5/diagnostics.py — Bộ kiểm tra sức khoẻ cài đặt (dùng chung CLI + GUI).

Chạy các check:
    • imports     — docx/fitz/pdfplumber/mammoth (module vừa bundle)
    • native_cpp  — DLL C++ acceleration đã bundle và đúng ABI
    • export_word — thử xuất 1 file .docx
    • tikz_render — thử render TikZ → PNG (cần LaTeX + fitz)
    • core_funcs  — generator/qc/storage import
    • ai_keys     — có ít nhất 1 API key chưa
    • latex       — pdflatex có trong PATH không

Dùng bởi:
    • app._selftest()         — CLI `--selftest`
    • PreferencesDialog       — nút "🩺 Chẩn đoán"
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable


def release_checks_pass(results: list[tuple[str, bool, str]]) -> bool:
    """Return whether an installation is runnable without optional setup."""
    return all(status != "FAIL" for status, _name, _message in _report_rows(results))


def _report_rows(results: list[tuple[str, bool, str]]) -> list[tuple[str, str, str]]:
    """Classify missing optional configuration separately from broken runtime."""
    latex_available = any(name == "LaTeX engine" and ok for name, ok, _msg in results)
    rows: list[tuple[str, str, str]] = []
    for name, ok, message in results:
        if ok:
            status = "PASS"
        elif name == "API key":
            status = "INFO"
        elif name in {"LaTeX engine", "TikZ render"} and not latex_available:
            status = "INFO"
        else:
            status = "FAIL"
        rows.append((status, name, message))
    return rows


def run_diagnostics(progress_cb: Callable[[str], None] | None = None
                     ) -> list[tuple[str, bool, str]]:
    """Chạy tất cả check. Trả list (name, ok, message).

    progress_cb(name): gọi trước mỗi check (cho GUI update status).
    """
    results: list[tuple[str, bool, str]] = []

    def _check(name, fn):
        if progress_cb:
            try: progress_cb(name)
            except Exception: pass
        try:
            msg = fn() or "OK"
            results.append((name, True, str(msg)))
        except Exception as e:
            results.append((name, False, f"{type(e).__name__}: {e}"))

    # 1. Import critical modules
    def _imports():
        import docx, fitz, pdfplumber, mammoth          # noqa: F401
        return "docx + fitz + pdfplumber + mammoth"
    _check("Import modules", _imports)

    # 2. Native C++ text primitives bundled with V5.
    def _native():
        from services.native_accel import require_native
        return require_native()
    _check("Native C++", _native)

    # 3. Cùng engine selection với renderer thực tế.
    def _latex():
        from services.latex_engine import get_engine
        engine = get_engine()
        return f"{engine.name}: {os.path.basename(engine.binary)}"
    _check("LaTeX engine", _latex)

    # 4. Export Word
    def _export():
        from core.models import ExamData, Question
        from export.word_exporter import export_to_word
        q = Question(qtype="TN", level="TH", topic="Test",
                      question="1+1=?", options={"A": "2", "B": "3"},
                      answer="A", solution="2", points=0.25)
        ex = ExamData(exam_title="Diag", subject="Toán", grade="12",
                       semester="1", year="", time="45 phút", questions=[q])
        out = os.path.join(tempfile.gettempdir(), "mea_diag.docx")
        export_to_word(ex, out, include_solution=True)
        sz = os.path.getsize(out)
        try: os.unlink(out)
        except Exception: pass
        return f"{sz} bytes .docx"
    _check("Xuất Word", _export)

    # 5. TikZ render
    def _tikz():
        from services.tikz_pipeline import render_single
        code = r"\begin{tikzpicture}\draw (0,0)--(1,1);\end{tikzpicture}"
        png, err = render_single(code, dpi=120)
        if err and not png:
            raise RuntimeError(f"{err[:80]}")
        return "render PNG OK"
    _check("TikZ render", _tikz)

    # 6. Core functions
    def _core():
        from core.generator import generate_all          # noqa: F401
        from core.quality_pipeline import run_qc_pipeline # noqa: F401
        from storage.database import search_questions
        n = len(search_questions() or [])
        return f"generator+qc OK · NHCH {n} câu"
    _check("Core + NHCH", _core)

    # 7. Packaged data needed by quick-create and TikZ workflows.
    def _data():
        from services import tikz_kb
        from services.matrix_templates import list_templates

        tikz_count = tikz_kb.load(force=True)
        template_count = len(list_templates())
        context = Path(__file__).resolve().parent.parent / "data" / "chuongtrinhhoctap.txt"
        if tikz_count <= 0 or template_count <= 0 or not context.exists():
            raise RuntimeError(
                f"Thiếu data: tikz={tikz_count}, matrix={template_count}, context={context.exists()}"
            )
        return f"{tikz_count} TikZ, {template_count} ma trận, context OK"
    _check("Dữ liệu V5", _data)

    # 8. AI keys
    def _keys():
        from services.key_manager import get_key_manager
        km = get_key_manager()
        have = [p for p in ("Google Gemini", "Anthropic Claude",
                             "DeepSeek", "OpenAI") if km.load(p)]
        if not have:
            raise RuntimeError("Chưa cấu hình API key nào")
        return "có key: " + ", ".join(p.split()[-1] for p in have)
    _check("API key", _keys)

    return results


def format_report(results: list[tuple[str, bool, str]]) -> str:
    """Format list kết quả → text report."""
    lines = ["=" * 56, "  MEA v5 — CHẨN ĐOÁN HỆ THỐNG", "=" * 56]
    rows = _report_rows(results)
    for flag, name, msg in rows:
        lines.append(f"  [{flag}] {name:16s} {msg[:84]}")
    lines.append("=" * 56)
    n_pass = sum(1 for status, _name, _msg in rows if status == "PASS")
    n_info = sum(1 for status, _name, _msg in rows if status == "INFO")
    ready = release_checks_pass(results)
    lines.append(
        f"  KẾT QUẢ: {n_pass}/{len(results)} PASS"
        + (f"  |  {n_info} tùy chọn chưa sẵn sàng" if n_info else "")
        + ("" if ready else "  |  có lỗi bắt buộc")
    )
    lines.append("=" * 56)
    return "\n".join(lines)
