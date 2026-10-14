"""
ui/pdf_preview_dialog.py — Dialog xem PDF với zoom vector-quality (PyMuPDF).

Khác với hiển thị PNG cố định DPI rồi resize, dialog này RE-RENDER PDF mỗi lần
zoom đổi → giữ chất lượng vector ở mọi mức zoom.

Sử dụng:
    >>> from ui.pdf_preview_dialog import PDFPreviewDialog
    >>> PDFPreviewDialog(parent, pdf_path="/tmp/figure.pdf",
    ...                  title="Xem trước câu hỏi")

Hoặc compile LaTeX rồi xem:
    >>> PDFPreviewDialog.from_latex(parent, latex_source="$x^2+1=0$",
    ...                              title="Câu hỏi #5")

Thread-safe: compile LaTeX chạy ở background thread, hiển thị spinner.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional


class PDFPreviewDialog(tk.Toplevel):
    """Dialog hiển thị PDF với zoom vector-quality."""

    BG = "#F9F7F4"
    HEADER_BG = "#1E40AF"

    # Zoom levels (DPI). 100% = 150 DPI screen-friendly; cap 1200 DPI tránh OOM
    _ZOOM_PRESETS = [50, 75, 100, 125, 150, 200, 300, 400, 600]
    _DEFAULT_DPI = 150  # 100% zoom

    def __init__(
        self,
        parent: tk.Misc,
        pdf_path: str,
        title: str = "Xem trước PDF",
        cleanup_paths: Optional[list[str]] = None,
    ):
        """
        Args:
            pdf_path: đường dẫn tới file PDF.
            title: tiêu đề dialog.
            cleanup_paths: list path/dir sẽ xóa khi dialog đóng (vd: tmp dir).
        """
        super().__init__(parent)
        self.title(title)
        self.configure(bg=self.BG)
        try:
            top = parent.winfo_toplevel()
            self.transient(top)
        except Exception:
            pass

        try:
            from ui import set_dialog_icon
            set_dialog_icon(self)
        except Exception:
            pass

        self._pdf_path = pdf_path
        self._cleanup_paths = list(cleanup_paths or [])
        self._renderer = None  # services.pdf_renderer.PDFRenderer
        self._img_tk = None
        self._current_page = 0
        self._dpi = self._DEFAULT_DPI

        self._build_ui()
        self._open_pdf()

        # Sizing
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = min(1100, sw - 100), min(800, sh - 100)
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.minsize(600, 500)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.lift()
        self.focus_force()

    # ── Class-method: từ LaTeX source → compile → preview ────────────────
    @classmethod
    def from_latex(
        cls,
        parent: tk.Misc,
        latex_source: str,
        title: str = "Xem trước",
    ) -> Optional["PDFPreviewDialog"]:
        """Compile LaTeX source → PDF → mở dialog. Return None nếu compile fail.

        Hiển thị spinner trong lúc compile (~1-3s). Nếu fail, popup error.
        """
        # Show spinner
        spinner = tk.Toplevel(parent)
        spinner.title("Đang compile…")
        spinner.configure(bg=cls.BG)
        spinner.transient(parent.winfo_toplevel())
        spinner.grab_set()
        spinner.resizable(False, False)
        try:
            from ui import set_dialog_icon
            set_dialog_icon(spinner)
        except Exception:
            pass

        sw, sh = spinner.winfo_screenwidth(), spinner.winfo_screenheight()
        spinner.geometry(f"320x120+{(sw - 320) // 2}+{(sh - 120) // 2}")
        tk.Label(spinner, text="⏳", font=("Segoe UI", 32),
                 bg=cls.BG, fg=cls.HEADER_BG).pack(pady=(10, 0))
        status_var = tk.StringVar(value="Đang compile LaTeX…")
        tk.Label(spinner, textvariable=status_var, font=("Segoe UI", 10),
                 bg=cls.BG, fg="#475569").pack()

        result: dict = {"pdf": None, "tmpdir": None, "err": None}

        def _worker():
            try:
                from services.pdf_renderer import compile_latex_to_pdf
                tmpdir = tempfile.mkdtemp(prefix="qc_preview_")
                pdf = compile_latex_to_pdf(latex_source, workdir=tmpdir)
                result["pdf"] = pdf
                result["tmpdir"] = tmpdir
            except Exception as exc:
                result["err"] = str(exc)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

        # Poll until done (UI vẫn responsive vì spinner.update())
        while t.is_alive():
            spinner.update()
            time.sleep(0.05)
        spinner.destroy()

        if result["err"] or not result["pdf"]:
            messagebox.showerror(
                "Lỗi compile",
                f"Không compile được LaTeX:\n\n{(result['err'] or 'unknown')[:500]}",
                parent=parent,
            )
            if result["tmpdir"]:
                shutil.rmtree(result["tmpdir"], ignore_errors=True)
            return None

        # OK → mở dialog với cleanup tmpdir khi đóng
        return cls(
            parent,
            pdf_path=result["pdf"],
            title=title,
            cleanup_paths=[result["tmpdir"]],
        )

    # ── UI build ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=self.HEADER_BG)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  📄 " + self.title(),
                 font=("Segoe UI", 11, "bold"),
                 bg=self.HEADER_BG, fg="white"
                 ).pack(side="left", padx=12, pady=8)

        # Toolbar
        tb = tk.Frame(self, bg="#E2E8F0")
        tb.pack(fill="x")

        # Page navigation
        self._page_var = tk.StringVar(value="1 / 1")
        tk.Button(tb, text="◀", font=("Segoe UI", 10, "bold"),
                  bg="#94A3B8", fg="white", activebackground="#64748B",
                  relief="flat", cursor="hand2", padx=8, pady=2,
                  command=self._prev_page).pack(side="left", padx=(8, 2), pady=4)
        tk.Label(tb, textvariable=self._page_var, font=("Segoe UI", 10),
                 bg="#E2E8F0", width=8, anchor="center"
                 ).pack(side="left", padx=2)
        tk.Button(tb, text="▶", font=("Segoe UI", 10, "bold"),
                  bg="#94A3B8", fg="white", activebackground="#64748B",
                  relief="flat", cursor="hand2", padx=8, pady=2,
                  command=self._next_page).pack(side="left", padx=2, pady=4)

        # Spacer
        tk.Label(tb, text="", bg="#E2E8F0").pack(side="left", padx=8)

        # Zoom controls
        tk.Button(tb, text="−", font=("Segoe UI", 11, "bold"),
                  bg="#3B82F6", fg="white", activebackground="#2563EB",
                  relief="flat", cursor="hand2", padx=6, pady=2,
                  command=self._zoom_out).pack(side="left", padx=2, pady=4)
        self._zoom_var = tk.StringVar(value="100%")
        tk.Label(tb, textvariable=self._zoom_var, font=("Segoe UI", 10, "bold"),
                 bg="#E2E8F0", width=6, anchor="center"
                 ).pack(side="left", padx=2)
        tk.Button(tb, text="+", font=("Segoe UI", 11, "bold"),
                  bg="#3B82F6", fg="white", activebackground="#2563EB",
                  relief="flat", cursor="hand2", padx=6, pady=2,
                  command=self._zoom_in).pack(side="left", padx=2, pady=4)
        tk.Button(tb, text="100%", font=("Segoe UI", 9),
                  bg="#10B981", fg="white", activebackground="#059669",
                  relief="flat", cursor="hand2", padx=8, pady=2,
                  command=self._zoom_reset).pack(side="left", padx=4, pady=4)
        tk.Button(tb, text="Fit", font=("Segoe UI", 9),
                  bg="#8B5CF6", fg="white", activebackground="#7C3AED",
                  relief="flat", cursor="hand2", padx=8, pady=2,
                  command=self._zoom_fit).pack(side="left", padx=2, pady=4)

        # Right: Save copy + Close
        tk.Button(tb, text="💾 Lưu PDF", font=("Segoe UI", 9, "bold"),
                  bg="#0891B2", fg="white", activebackground="#0E7490",
                  relief="flat", cursor="hand2", padx=8, pady=2,
                  command=self._save_pdf).pack(side="right", padx=8, pady=4)

        # Canvas + scrollbars
        body = tk.Frame(self, bg="#1E293B")
        body.pack(fill="both", expand=True, padx=2, pady=(2, 0))

        self._canvas = tk.Canvas(body, bg="#374151", highlightthickness=0)
        vsb = ttk.Scrollbar(body, orient="vertical", command=self._canvas.yview)
        hsb = ttk.Scrollbar(body, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._canvas.pack(side="left", fill="both", expand=True)

        # Zoom: Ctrl+Wheel
        self._canvas.bind("<Control-MouseWheel>", self._on_ctrl_wheel)
        # Scroll: Wheel
        self._canvas.bind("<MouseWheel>",
                           lambda e: self._canvas.yview_scroll(int(-e.delta / 120), "units"))
        # Pan: middle/right click drag
        self._canvas.bind("<ButtonPress-2>", lambda e: self._canvas.scan_mark(e.x, e.y))
        self._canvas.bind("<B2-Motion>", lambda e: self._canvas.scan_dragto(e.x, e.y, gain=1))

        # Page nav: arrow keys
        self.bind("<Left>", lambda e: self._prev_page())
        self.bind("<Right>", lambda e: self._next_page())
        self.bind("<Escape>", lambda e: self._on_close())
        self.bind("<plus>", lambda e: self._zoom_in())
        self.bind("<minus>", lambda e: self._zoom_out())

        # Status bar
        self._status_var = tk.StringVar(value="")
        tk.Label(self, textvariable=self._status_var, font=("Segoe UI", 8),
                 bg=self.BG, fg="#64748B", anchor="w"
                 ).pack(fill="x", padx=8, pady=2)

    # ── PDF lifecycle ───────────────────────────────────────────────────────

    def _open_pdf(self):
        try:
            from services.pdf_renderer import PDFRenderer
            self._renderer = PDFRenderer(self._pdf_path)
        except Exception as exc:
            messagebox.showerror(
                "Lỗi mở PDF", f"Không mở được PDF:\n{exc}", parent=self,
            )
            self.after(50, self.destroy)
            return
        self._page_var.set(f"1 / {self._renderer.page_count}")
        # Render first page sau khi window sized
        self.after(100, self._render_current)

    def _render_current(self):
        if self._renderer is None:
            return
        try:
            img = self._renderer.render(page=self._current_page, dpi=self._dpi)
        except Exception as exc:
            self._status_var.set(f"Lỗi render: {exc}")
            return

        from PIL import ImageTk
        self._img_tk = ImageTk.PhotoImage(img)
        self._canvas.delete("all")
        self._canvas.create_image(0, 0, image=self._img_tk, anchor="nw")
        self._canvas.configure(scrollregion=(0, 0, img.width, img.height))
        self._zoom_var.set(f"{int(self._dpi * 100 / self._DEFAULT_DPI)}%")
        self._status_var.set(
            f"Trang {self._current_page + 1}/{self._renderer.page_count}  ·  "
            f"{img.width}×{img.height}px @ {self._dpi} DPI"
        )

    # ── Zoom ────────────────────────────────────────────────────────────────

    def _zoom_in(self):
        # Tìm preset > current; nếu không có, x1.25
        for preset in self._ZOOM_PRESETS:
            target_dpi = int(preset * self._DEFAULT_DPI / 100)
            if target_dpi > self._dpi:
                self._dpi = target_dpi
                self._render_current()
                return
        self._dpi = min(int(self._dpi * 1.25), 1200)
        self._render_current()

    def _zoom_out(self):
        for preset in reversed(self._ZOOM_PRESETS):
            target_dpi = int(preset * self._DEFAULT_DPI / 100)
            if target_dpi < self._dpi:
                self._dpi = target_dpi
                self._render_current()
                return
        self._dpi = max(int(self._dpi / 1.25), 36)
        self._render_current()

    def _zoom_reset(self):
        self._dpi = self._DEFAULT_DPI
        self._render_current()

    def _zoom_fit(self):
        if self._renderer is None:
            return
        cw = self._canvas.winfo_width() or 800
        ch = self._canvas.winfo_height() or 600
        page_w_pt, page_h_pt = self._renderer.page_size_pt(self._current_page)
        # DPI để page vừa khít canvas (theo chiều bị giới hạn nhiều hơn)
        dpi_w = cw / page_w_pt * 72
        dpi_h = ch / page_h_pt * 72
        self._dpi = max(36, min(int(min(dpi_w, dpi_h) * 0.95), 1200))
        self._render_current()

    def _on_ctrl_wheel(self, event):
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()
        return "break"

    # ── Page nav ────────────────────────────────────────────────────────────

    def _prev_page(self):
        if self._renderer is None:
            return
        if self._current_page > 0:
            self._current_page -= 1
            self._page_var.set(f"{self._current_page + 1} / {self._renderer.page_count}")
            self._render_current()

    def _next_page(self):
        if self._renderer is None:
            return
        if self._current_page < self._renderer.page_count - 1:
            self._current_page += 1
            self._page_var.set(f"{self._current_page + 1} / {self._renderer.page_count}")
            self._render_current()

    # ── Save copy ───────────────────────────────────────────────────────────

    def _save_pdf(self):
        from tkinter import filedialog
        out = filedialog.asksaveasfilename(
            parent=self,
            title="Lưu PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf"), ("All files", "*.*")],
            initialfile="preview.pdf",
        )
        if not out:
            return
        try:
            shutil.copy2(self._pdf_path, out)
            messagebox.showinfo(
                "Đã lưu", f"PDF đã lưu vào:\n{out}", parent=self,
            )
        except Exception as exc:
            messagebox.showerror(
                "Lỗi lưu", f"Không lưu được:\n{exc}", parent=self,
            )

    # ── Close ───────────────────────────────────────────────────────────────

    def _on_close(self):
        # Release PDF handle TRƯỚC khi xóa file (Windows lock)
        if self._renderer is not None:
            try:
                self._renderer.close()
            except Exception:
                pass
            self._renderer = None
        # Cleanup tmp dirs (nếu có)
        for path in self._cleanup_paths:
            if path and os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    try:
                        os.remove(path)
                    except Exception:
                        pass
        self.destroy()
