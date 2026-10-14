"""V5 LaTeX preview dialog for a single generated question."""
from __future__ import annotations

import io
import re
import sys
import tempfile
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

import customtkinter as ctk


LATEX_QUESTION_TEMPLATE = r"""\documentclass[12pt,border=10pt]{standalone}
\usepackage{iftex}
\ifPDFTeX
  \usepackage[utf8]{inputenc}
  \usepackage[T5]{fontenc}
\fi
\usepackage[vietnamese]{babel}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usetikzlibrary{calc,angles,quotes,patterns,arrows.meta,intersections}
\usepackage{array}
\usepackage{varwidth}
\begin{document}
\begin{varwidth}{15cm}
%(content)s
\end{varwidth}
\end{document}
"""

QTYPE_LABELS = {
    "TN": "Trắc nghiệm",
    "DS": "Đúng--Sai",
    "TLN": "Trả lời ngắn",
    "TL": "Tự luận",
}


def _math_safe_text(text: Any) -> str:
    """Normalize lightweight math notation and escape text-only separators."""
    value = "" if text is None else str(text)
    value = re.sub(r"\$\{(.+?)\}\$", r"$\1$", value)
    parts = re.split(r"(\$[^$]+\$)", value)
    escaped: list[str] = []
    for part in parts:
        if part.startswith("$") and part.endswith("$"):
            escaped.append(part)
        else:
            escaped.append(part.replace("&", r"\&").replace("%", r"\%"))
    return "".join(escaped)


def _ordered_keys(mapping: dict, preferred: str) -> list[str]:
    keys = [key for key in preferred if key in mapping]
    extras = [str(key) for key in mapping.keys() if str(key) not in keys]
    return keys + sorted(extras)


def question_to_latex(question: Any, index: int) -> str:
    """Convert a Question-like object to LaTeX content for preview rendering."""
    qtype = str(getattr(question, "qtype", "") or "")
    level = str(getattr(question, "level", "") or "")
    type_label = QTYPE_LABELS.get(qtype, qtype or "?")
    lines: list[str] = [
        rf"\noindent\textbf{{Câu {index + 1}.}} "
        rf"\textit{{[{type_label} -- {level}]}}",
        "",
        r"\medskip",
        _math_safe_text(getattr(question, "question", "")),
        "",
    ]

    options = getattr(question, "options", {}) or {}
    answer = str(getattr(question, "answer", "") or "")
    if qtype == "TN" and options:
        lines.extend([
            r"\begin{enumerate}",
            r"\renewcommand{\labelenumi}{\textbf{\Alph{enumi}.}}",
        ])
        for key in _ordered_keys(options, "ABCD"):
            marker = r" \quad $\Leftarrow$ \textbf{ĐÁP ÁN}" if key == answer else ""
            lines.append(r"\item " + _math_safe_text(options.get(key, "")) + marker)
        lines.append(r"\end{enumerate}")

    elif qtype == "DS":
        items = getattr(question, "items", {}) or {}
        answers = getattr(question, "answers", {}) or {}
        for key in _ordered_keys(items, "abcd"):
            is_true = bool(answers.get(key, False))
            marker = r"\textbf{(Đ)}" if is_true else r"\textbf{(S)}"
            lines.append(
                rf"\noindent\textbf{{{key}.}} "
                + _math_safe_text(items.get(key, ""))
                + r" \hfill "
                + marker
            )
            lines.append(r"\smallskip")

    elif qtype == "TLN" and answer:
        lines.append(r"\medskip")
        lines.append(r"\noindent\textbf{Đáp số:} " + _math_safe_text(answer))

    solution = str(getattr(question, "solution", "") or "")
    item_solutions = getattr(question, "item_solutions", {}) or {}
    if qtype == "DS" and item_solutions:
        solution_parts = []
        for key in _ordered_keys(item_solutions, "abcd"):
            value = str(item_solutions.get(key, "") or "")
            if value.strip():
                solution_parts.append(rf"\textbf{{{key}.}} {_math_safe_text(value)}")
        if solution_parts:
            solution = r" \\ ".join(solution_parts)

    if solution.strip():
        lines.extend([
            r"\medskip",
            r"\noindent\rule{\linewidth}{0.4pt}",
            r"\smallskip",
            r"\noindent\textbf{Lời giải:} " + _math_safe_text(solution),
        ])

    return "\n".join(lines)


def render_question_latex(question: Any, index: int, dpi: int = 200):
    from services.latex_engine import safe_temporary_directory
    from services.pdf_renderer import compile_latex_to_pdf, render_pdf_page

    content = question_to_latex(question, index)
    source = LATEX_QUESTION_TEMPLATE % {"content": content}
    with safe_temporary_directory(prefix="v5_latex_preview_") as temp_dir:
        pdf_path = compile_latex_to_pdf(source, workdir=temp_dir, timeout=45)
        return render_pdf_page(pdf_path, page=0, dpi=dpi)


def copy_pil_image_to_clipboard(image) -> None:
    """Copy a PIL image to the native clipboard on Windows."""
    if not sys.platform.startswith("win"):
        raise RuntimeError("Copy ảnh vào clipboard hiện chỉ hỗ trợ Windows.")
    try:
        import win32clipboard  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Thiếu pywin32 nên chưa copy ảnh vào clipboard được.") from exc

    output = io.BytesIO()
    image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    finally:
        win32clipboard.CloseClipboard()


class LatexPreviewDialog(ctk.CTkToplevel):
    """Render and display one generated question as a LaTeX PNG preview."""

    def __init__(self, parent, question: Any, index: int):
        super().__init__(parent)
        self.title(f"Xem trước LaTeX - Câu {index + 1}")
        self.transient(parent)
        self.grab_set()

        self._question = question
        self._index = index
        self._img_pil = None
        self._img_tk = None

        self._build_ui(index)
        self.after(80, self._start_render)

    def _build_ui(self, index: int) -> None:
        self.configure(fg_color=("#F8FAFC", "#0F172A"))
        header = ctk.CTkFrame(self, fg_color=("#1F497D", "#0F172A"), corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header,
            text=f"  👁  Xem trước LaTeX - Câu {index + 1}",
            font=("Segoe UI", 14, "bold"),
            text_color="white",
            anchor="w",
        ).pack(side="left", padx=12, pady=10)

        bar = ctk.CTkFrame(self, fg_color=("#E2E8F0", "#1E293B"), corner_radius=0)
        bar.pack(fill="x")
        ctk.CTkButton(
            bar,
            text="📋 Copy ảnh",
            width=112,
            fg_color="#3B82F6",
            hover_color="#2563EB",
            command=self._copy_image,
        ).pack(side="left", padx=(10, 5), pady=7)
        ctk.CTkButton(
            bar,
            text="💾 Lưu PNG",
            width=108,
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            command=self._save_png,
        ).pack(side="left", padx=5, pady=7)
        self._status = ctk.CTkLabel(
            bar,
            text="Đang render...",
            font=("Segoe UI", 10),
            text_color="gray",
        )
        self._status.pack(side="right", padx=10)

        canvas_frame = ctk.CTkFrame(self, fg_color=("#FFFFFF", "#111827"))
        canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        vsb = ttk.Scrollbar(canvas_frame, orient="vertical", command=self._canvas.yview)
        hsb = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._canvas.create_text(
            320,
            120,
            text="Đang render LaTeX...",
            fill="#64748B",
            font=("Segoe UI", 14, "bold"),
        )

        self._error_text = tk.Text(
            self,
            font=("Consolas", 9),
            bg="#FEF2F2",
            fg="#DC2626",
            height=5,
            wrap="word",
            state="disabled",
        )

        self._canvas.bind(
            "<MouseWheel>",
            lambda event: self._canvas.yview_scroll(int(-4 * (event.delta / 120)), "units"),
        )
        self.geometry("900x680")
        self.minsize(640, 420)

    def _start_render(self) -> None:
        threading.Thread(target=self._render_worker, daemon=True).start()

    def _render_worker(self) -> None:
        try:
            image = render_question_latex(self._question, self._index, dpi=200)
        except Exception as exc:
            message = str(exc)
            self.after(0, lambda: self._show_error(message))
            return
        self._img_pil = image
        self.after(0, lambda: self._show_image(image))

    def _show_image(self, image) -> None:
        from PIL import ImageTk

        self._error_text.pack_forget()
        canvas_width = max(self._canvas.winfo_width(), 500)
        scale = min(canvas_width / max(image.width + 20, 1), 1.0)
        display = image
        if scale < 1.0:
            display = image.resize((int(image.width * scale), int(image.height * scale)))
        self._img_tk = ImageTk.PhotoImage(display)
        self._canvas.delete("all")
        self._canvas.create_image(10, 10, image=self._img_tk, anchor="nw")
        self._canvas.configure(scrollregion=(0, 0, display.width + 20, display.height + 20))
        self._status.configure(
            text=f"✓ Render OK - {image.width}x{image.height}px",
            text_color="#10B981",
        )

    def _show_error(self, message: str) -> None:
        self._status.configure(text="Lỗi render", text_color="#DC2626")
        self._canvas.delete("all")
        self._canvas.create_text(
            320,
            70,
            text="Không render được LaTeX",
            fill="#DC2626",
            font=("Segoe UI", 13, "bold"),
        )
        self._error_text.configure(state="normal")
        self._error_text.delete("1.0", "end")
        self._error_text.insert("1.0", message[:3000])
        self._error_text.configure(state="disabled")
        self._error_text.pack(fill="x", padx=10, pady=(0, 10))

    def _copy_image(self) -> None:
        if self._img_pil is None:
            messagebox.showwarning("Chưa có ảnh", "Đợi render xong rồi copy ảnh.", parent=self)
            return
        try:
            copy_pil_image_to_clipboard(self._img_pil)
        except Exception as exc:
            messagebox.showerror("Lỗi copy ảnh", str(exc), parent=self)
            return
        self._status.configure(text="📋 Đã copy ảnh", text_color="#10B981")

    def _save_png(self) -> None:
        if self._img_pil is None:
            messagebox.showwarning("Chưa có ảnh", "Đợi render xong rồi lưu PNG.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            initialfile=f"cau_{self._index + 1}.png",
        )
        if not path:
            return
        target = Path(path)
        self._img_pil.save(target, dpi=(200, 200))
        self._status.configure(text=f"💾 Đã lưu {target.name}", text_color="#10B981")
        messagebox.showinfo("Đã lưu", f"Đã lưu ảnh:\n{target}", parent=self)
