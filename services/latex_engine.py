"""
services/latex_engine.py — Auto-detect và chọn LaTeX engine để compile TikZ/preview.

Ưu tiên detection (PATH search):
    pdflatex > xelatex > tectonic

Lý do thứ tự:
  • pdflatex:  phổ biến nhất trong TeX Live/MiKTeX, predictable.
  • xelatex:   font Việt tốt hơn (UTF-8 native), cài cùng TeX distribution.
  • tectonic:  1 file, không cần TeX distribution, lần đầu cần tải package
               (1-2 phút), lần sau rất nhanh.

User override qua biến `config.LATEX_ENGINE_PREFERENCE`:
    "auto"      → detect theo priority (mặc định)
    "pdflatex"  → ép pdflatex
    "xelatex"   → ép xelatex
    "tectonic"  → ép tectonic
Nếu engine ép không có trong PATH → fallback auto-detect + log warning.

Preamble compatibility:
    pdflatex:           cần \\usepackage[utf8]{inputenc}, \\usepackage[T5]{fontenc}
    xelatex/tectonic:   XeTeX → KHÔNG cần inputenc/fontenc

→ Dùng `neutral_font_preamble()` chèn vào template để code chạy được mọi engine:
        \\usepackage{iftex}
        \\ifPDFTeX
          \\usepackage[utf8]{inputenc}
          \\usepackage[T5]{fontenc}
        \\fi
"""

from __future__ import annotations

import contextlib
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional

_log = logging.getLogger(__name__)


@contextlib.contextmanager
def safe_temporary_directory(prefix: str = "mea_tex_"):
    """Tạo thư mục tạm an toàn trên Windows, chống lỗi WinError 32 file locking khi dọn dẹp."""
    try:
        td = tempfile.TemporaryDirectory(prefix=prefix, ignore_cleanup_errors=True)
    except TypeError:
        td = tempfile.TemporaryDirectory(prefix=prefix)
    try:
        yield td.name
    finally:
        try:
            td.cleanup()
        except Exception:
            pass
        if os.path.exists(td.name):
            try:
                shutil.rmtree(td.name, ignore_errors=True)
            except Exception:
                pass


class LatexEngineNotFound(RuntimeError):
    """Không tìm thấy LaTeX engine nào trong PATH."""
    pass


@dataclass(frozen=True)
class LatexEngine:
    name: str        # "pdflatex" | "xelatex" | "tectonic"
    binary: str      # absolute path từ shutil.which

    @property
    def is_xetex_based(self) -> bool:
        """True nếu engine dùng XeTeX (xelatex, tectonic) — UTF-8 native."""
        return self.name in ("xelatex", "tectonic")

    def build_argv(self, tex_filename: str) -> list[str]:
        """Build argv để truyền vào subprocess.run.
        Caller cần đặt cwd = thư mục chứa file .tex."""
        if self.name == "tectonic":
            return [
                self.binary,
                "--keep-logs",
                "--chatter=minimal",
                tex_filename,
            ]
        # pdflatex / xelatex: cùng args
        return [
            self.binary,
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex_filename,
        ]


_ENGINE_PRIORITY: tuple[str, ...] = ("pdflatex", "xelatex", "tectonic")
_cached_engine: Optional[LatexEngine] = None
_cached_prefer: object = ...   # sentinel khác mọi giá trị hợp lệ

_INSTALL_HINTS = [
    "MiKTeX (Windows, khuyên dùng): https://miktex.org/",
    "TeX Live: https://tug.org/texlive/",
    "Tectonic (gọn nhẹ): https://tectonic-typesetting.github.io/",
]


def _read_config_preference() -> Optional[str]:
    """Đọc LATEX_ENGINE_PREFERENCE từ config; trả None nếu không có hoặc 'auto'."""
    try:
        from config import LATEX_ENGINE_PREFERENCE  # type: ignore
    except (ImportError, AttributeError):
        return None
    if not LATEX_ENGINE_PREFERENCE or LATEX_ENGINE_PREFERENCE == "auto":
        return None
    return str(LATEX_ENGINE_PREFERENCE)


def get_engine(prefer: Optional[str] = None) -> LatexEngine:
    """Tìm engine khả dụng. Cache để không shutil.which lặp.

    Args:
        prefer: ép dùng 1 trong "pdflatex"/"xelatex"/"tectonic".
                None → đọc config, hoặc auto-detect theo priority.

    Raises:
        LatexEngineNotFound nếu không có engine nào trong PATH.
    """
    global _cached_engine, _cached_prefer

    if prefer is None:
        prefer = _read_config_preference()

    if _cached_engine is not None and _cached_prefer == prefer:
        return _cached_engine

    # Bước 1: thử engine ép (nếu có)
    if prefer:
        binary = shutil.which(prefer)
        if binary:
            engine = LatexEngine(name=prefer, binary=binary)
            _log.info("LaTeX engine: %s (forced by config) → %s", prefer, binary)
            _cached_engine, _cached_prefer = engine, prefer
            return engine
        _log.warning(
            "LaTeX engine '%s' không có trong PATH — fallback auto-detect.",
            prefer,
        )

    # Bước 2: auto-detect theo priority
    for name in _ENGINE_PRIORITY:
        binary = shutil.which(name)
        if binary:
            engine = LatexEngine(name=name, binary=binary)
            _log.info("LaTeX engine: %s (auto) → %s", name, binary)
            _cached_engine, _cached_prefer = engine, prefer
            return engine

    raise LatexEngineNotFound(
        "Không tìm thấy LaTeX engine!\n"
        "Cài 1 trong các tuỳ chọn sau:\n"
        "  • TeX Live (đa nền tảng):           https://tug.org/texlive/\n"
        "  • MiKTeX (Windows, khuyên dùng):    https://miktex.org/\n"
        "  • Tectonic (1 file, không cần TeX): https://tectonic-typesetting.github.io/"
    )


def list_available() -> list[str]:
    """List engine đang có trong PATH (cho UI Cài đặt hiển thị)."""
    return [n for n in _ENGINE_PRIORITY if shutil.which(n)]


def check_engine_status(prefer: Optional[str] = None) -> dict:
    """Return UI-friendly LaTeX engine diagnostic."""
    available = list_available()
    try:
        engine = get_engine(prefer)
        return {
            "ok": True,
            "engine": engine.name,
            "binary": engine.binary,
            "available": available,
            "message": f"Đã tìm thấy {engine.name}: {engine.binary}",
            "install_hints": list(_INSTALL_HINTS),
        }
    except LatexEngineNotFound as exc:
        return {
            "ok": False,
            "engine": "",
            "binary": "",
            "available": available,
            "message": str(exc),
            "install_hints": list(_INSTALL_HINTS),
        }


def smoke_test_engine(prefer: Optional[str] = None, timeout: int = 20) -> dict:
    """Compile a tiny TikZ document to verify the detected local engine.

    This is intended for an explicit UI "check engine" action, not for app
    startup, because Tectonic may download packages the first time it runs.
    """
    try:
        engine = get_engine(prefer)
    except LatexEngineNotFound as exc:
        return {
            "ok": False,
            "engine": "",
            "binary": "",
            "message": str(exc),
            "log": "",
            "install_hints": list(_INSTALL_HINTS),
        }

    tex = r"""\documentclass[border=4pt]{standalone}
\usepackage{tikz}
\begin{document}
\begin{tikzpicture}
  \draw[thick] (0,0) -- (1,0);
\end{tikzpicture}
\end{document}
"""
    with safe_temporary_directory(prefix="mea_tex_engine_") as td:
        tex_path = os.path.join(td, "engine_smoke.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex)
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            proc = subprocess.run(
                engine.build_argv("engine_smoke.tex"),
                cwd=td,
                capture_output=True,
                text=True,
                timeout=timeout,
                **kwargs,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "ok": False,
                "engine": engine.name,
                "binary": engine.binary,
                "message": f"{engine.name} chạy quá {timeout}s khi compile mẫu.",
                "log": str(exc),
                "install_hints": list(_INSTALL_HINTS),
            }
        except Exception as exc:
            return {
                "ok": False,
                "engine": engine.name,
                "binary": engine.binary,
                "message": f"Không chạy được {engine.name}: {exc}",
                "log": str(exc),
                "install_hints": list(_INSTALL_HINTS),
            }

        log = (proc.stdout or "") + "\n" + (proc.stderr or "")
        pdf_path = os.path.join(td, "engine_smoke.pdf")
        ok = proc.returncode == 0 and os.path.exists(pdf_path)
        return {
            "ok": ok,
            "engine": engine.name,
            "binary": engine.binary,
            "message": (
                f"{engine.name} compile mẫu TikZ thành công."
                if ok else f"{engine.name} tìm thấy nhưng compile mẫu thất bại."
            ),
            "log": log[-3000:],
            "install_hints": list(_INSTALL_HINTS),
        }


def neutral_font_preamble() -> str:
    """Đoạn preamble font/encoding tự thích nghi engine (pdflatex hay xetex).

    Yêu cầu engine LaTeX hiện đại (đã có gói `iftex` — mặc định trong TeX Live
    2010+, MiKTeX, Tectonic). Nhúng trực tiếp vào template:

        \\documentclass[...]{standalone}
        % --- font/encoding (auto theo engine) ---
        \\usepackage{iftex}
        \\ifPDFTeX
          \\usepackage[utf8]{inputenc}
          \\usepackage[T5]{fontenc}
        \\fi
        % --- packages còn lại ---
        \\usepackage{amsmath}
        ...
    """
    return (
        r"\usepackage{iftex}" "\n"
        r"\ifPDFTeX" "\n"
        r"  \usepackage[utf8]{inputenc}" "\n"
        r"  \usepackage[T5]{fontenc}" "\n"
        r"\fi"
    )


def reset_cache() -> None:
    """Clear cache — gọi sau khi đổi LATEX_ENGINE_PREFERENCE runtime."""
    global _cached_engine, _cached_prefer
    _cached_engine = None
    _cached_prefer = ...
