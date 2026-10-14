"""
v5/pdf_viewer.py — Overleaf-style PDF viewer widget cho CTk.

Tính năng:
  • Multi-page rendering (PyMuPDF) — mỗi trang là 1 ảnh trên Canvas thẳng đứng.
  • Zoom in / out / fit / 100% — re-render từng page khi đổi zoom (vector
    quality ở mọi level, KHÔNG resize raster như trước).
  • Pan kéo chuột (drag với chuột giữa hoặc Shift+Left).
  • MouseWheel cuộn trang. Ctrl+MouseWheel = zoom.
  • Page indicator "Trang 1 / 3" + nút next/prev.
  • Background xám trung tính (giống Adobe / Overleaf), page có shadow.

Cách dùng:
    viewer = PDFViewer(parent)
    viewer.pack(fill="both", expand=True)
    viewer.load_pdf("/path/to/file.pdf")
    viewer.set_zoom(1.5)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox


class PDFViewer(ctk.CTkFrame):
    """Overleaf-style PDF viewer: canvas + scrollbars + toolbar."""

    PAGE_BG  = "#FFFFFF"
    PAGE_SHADOW = "#94A3B8"
    BG_LIGHT = "#E5E7EB"
    BG_DARK  = "#0F172A"
    PAGE_SPACING = 16   # px giữa các trang
    BASE_DPI = 96       # DPI gốc cho zoom = 1.0

    ZOOM_MIN  = 0.25
    ZOOM_MAX  = 5.0
    ZOOM_STEP = 1.25

    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color="transparent", **kw)
        self._pdf_path: str = ""
        self._page_count: int = 0
        self._zoom: float = 1.0
        self._fit_mode: str = "fit_width"  # 'fit_width' | 'fit_page' | 'custom'
        self._page_imgs: list = []       # giữ ImageTk.PhotoImage tránh GC
        self._page_meta: list[dict] = []   # {y, w, h} sau khi vẽ
        self._drag_data = {"x": 0, "y": 0, "active": False}
        self._build()

    # ── Layout ─────────────────────────────────────────────────────────
    def _build(self):
        # Toolbar
        tb = ctk.CTkFrame(self, fg_color=("#F3F4F6", "#1E293B"),
                            corner_radius=0, height=40)
        tb.pack(fill="x", side="top")
        tb.pack_propagate(False)

        # Page navigation
        self._prev_btn = ctk.CTkButton(tb, text="◀", width=36, height=28,
                                          font=("Segoe UI", 13, "bold"),
                                          command=self._prev_page)
        self._prev_btn.pack(side="left", padx=(8, 2), pady=6)
        self._page_var = tk.StringVar(value="0 / 0")
        ctk.CTkLabel(tb, textvariable=self._page_var,
                      width=80, font=("Segoe UI", 11, "bold")
                      ).pack(side="left", padx=2)
        self._next_btn = ctk.CTkButton(tb, text="▶", width=36, height=28,
                                          font=("Segoe UI", 13, "bold"),
                                          command=self._next_page)
        self._next_btn.pack(side="left", padx=2, pady=6)

        ctk.CTkLabel(tb, text=" │ ", text_color="gray",
                      font=("Segoe UI", 12)).pack(side="left")

        # Zoom controls
        ctk.CTkButton(tb, text="🔍 -", width=46, height=28,
                        font=("Segoe UI", 11, "bold"),
                        command=lambda: self.zoom_by(1 / self.ZOOM_STEP)
                        ).pack(side="left", padx=2, pady=6)
        self._zoom_var = tk.StringVar(value="100%")
        ctk.CTkLabel(tb, textvariable=self._zoom_var,
                      width=58, font=("Segoe UI", 11)
                      ).pack(side="left", padx=2)
        ctk.CTkButton(tb, text="🔍 +", width=46, height=28,
                        font=("Segoe UI", 11, "bold"),
                        command=lambda: self.zoom_by(self.ZOOM_STEP)
                        ).pack(side="left", padx=2, pady=6)
        ctk.CTkButton(tb, text="↔ Fit", width=64, height=28,
                        font=("Segoe UI", 11),
                        fg_color="#6B7280", hover_color="#4B5563",
                        command=self._fit_width
                        ).pack(side="left", padx=(8, 2), pady=6)
        ctk.CTkButton(tb, text="100%", width=56, height=28,
                        font=("Segoe UI", 11),
                        fg_color="#6B7280", hover_color="#4B5563",
                        command=lambda: self.set_zoom(1.0)
                        ).pack(side="left", padx=2, pady=6)

        # Status bên phải
        self._status_var = tk.StringVar(value="Chưa load PDF")
        ctk.CTkLabel(tb, textvariable=self._status_var,
                      text_color="gray",
                      font=("Segoe UI", 10, "italic"),
                      anchor="e"
                      ).pack(side="right", padx=10, pady=6)

        # Body: canvas + scrollbars
        body = tk.Frame(self, bg=self.BG_LIGHT)
        body.pack(fill="both", expand=True)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self._canvas = tk.Canvas(body, bg=self.BG_LIGHT,
                                    highlightthickness=0, bd=0)
        self._canvas.grid(row=0, column=0, sticky="nsew")

        from tkinter import ttk
        self._vsb = ttk.Scrollbar(body, orient="vertical",
                                    command=self._canvas.yview)
        self._vsb.grid(row=0, column=1, sticky="ns")
        self._hsb = ttk.Scrollbar(body, orient="horizontal",
                                    command=self._canvas.xview)
        self._hsb.grid(row=1, column=0, sticky="ew")
        self._canvas.configure(
            yscrollcommand=self._vsb.set,
            xscrollcommand=self._hsb.set)

        # Sync background với theme
        try:
            mode = ctk.get_appearance_mode().lower()
            self._canvas.configure(
                bg=self.BG_DARK if mode == "dark" else self.BG_LIGHT)
            body.configure(bg=self._canvas.cget("bg"))
        except Exception: pass

        # ── Bindings ────────────────────────────────────────────────────
        self._canvas.bind("<MouseWheel>", self._on_wheel)
        self._canvas.bind("<Button-4>",
                            lambda e: self._canvas.yview_scroll(-3, "units"))
        self._canvas.bind("<Button-5>",
                            lambda e: self._canvas.yview_scroll(3, "units"))
        self._canvas.bind("<Control-MouseWheel>", self._on_ctrl_wheel)
        # Pan: chuột giữa hoặc Shift+Left
        self._canvas.bind("<ButtonPress-2>", self._pan_start)
        self._canvas.bind("<B2-Motion>", self._pan_move)
        self._canvas.bind("<ButtonRelease-2>", self._pan_end)
        self._canvas.bind("<Shift-ButtonPress-1>", self._pan_start)
        self._canvas.bind("<Shift-B1-Motion>", self._pan_move)
        self._canvas.bind("<Shift-ButtonRelease-1>", self._pan_end)
        # Resize → recompute fit
        self._canvas.bind("<Configure>", self._on_resize)
        # Focus canvas khi click → keyboard work
        self._canvas.bind("<Button-1>",
                            lambda e: self._canvas.focus_set())
        # Keyboard nav
        self._canvas.bind("<Key-Prior>",
                            lambda e: self._canvas.yview_scroll(-10, "units"))
        self._canvas.bind("<Key-Next>",
                            lambda e: self._canvas.yview_scroll(10, "units"))
        self._canvas.bind("<Key-Home>",
                            lambda e: self._canvas.yview_moveto(0))
        self._canvas.bind("<Key-End>",
                            lambda e: self._canvas.yview_moveto(1))

    # ── Public API ──────────────────────────────────────────────────────
    def load_pdf(self, pdf_path: str):
        """Mở PDF, render trang đầu, fit width."""
        p = Path(pdf_path)
        if not p.exists():
            self._show_message(f"PDF không tồn tại:\n{pdf_path}")
            return False
        self._pdf_path = str(p.absolute())
        try:
            import fitz
            doc = fitz.open(self._pdf_path)
            self._page_count = doc.page_count
            doc.close()
        except Exception as e:
            self._show_message(f"Lỗi mở PDF: {e}")
            return False
        if self._page_count == 0:
            self._show_message("PDF không có trang nào.")
            return False
        self._status_var.set(f"📄 {p.name}  ·  {self._page_count} trang")
        # Render trang đầu để compute fit
        self._fit_mode = "fit_width"
        self._fit_width()
        return True

    def set_zoom(self, zoom: float):
        self._zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, zoom))
        self._fit_mode = "custom"
        self._render_all_pages()

    def zoom_by(self, factor: float):
        self.set_zoom(self._zoom * factor)

    def clear(self):
        self._pdf_path = ""
        self._page_count = 0
        self._page_imgs.clear()
        self._page_meta.clear()
        self._canvas.delete("all")
        self._zoom_var.set("—")
        self._page_var.set("0 / 0")
        self._status_var.set("Chưa load PDF")

    # ── Internal: render ────────────────────────────────────────────────
    def _show_message(self, msg: str):
        self._canvas.delete("all")
        try:
            cw = self._canvas.winfo_width() or 600
            ch = self._canvas.winfo_height() or 400
            self._canvas.create_text(cw // 2, ch // 2,
                text=msg, fill="#6B7280",
                font=("Segoe UI", 11), justify="center")
        except Exception: pass
        self._status_var.set("⚠ " + msg.split("\n")[0])

    def _compute_fit_zoom(self) -> float:
        """Tính zoom để trang đầu fit width canvas.

        Cap max 2.5x — hình TikZ nhỏ (~5cm) sẽ không bị phóng lên 6x lấp
        toàn canvas, nhìn xấu + render lâu. User vẫn zoom+ thủ công được.
        """
        if not self._pdf_path: return 1.0
        try:
            import fitz
            doc = fitz.open(self._pdf_path)
            page = doc[0]
            page_w_pt = page.rect.width   # PDF dùng points (72/inch)
            doc.close()
            canvas_w = max(200, self._canvas.winfo_width() or 600) - 40
            base_px = page_w_pt * (self.BASE_DPI / 72.0)
            zoom = canvas_w / base_px
            return max(0.3, min(2.5, zoom))
        except Exception:
            return 1.0

    def _fit_width(self):
        self._fit_mode = "fit_width"
        self._zoom = self._compute_fit_zoom()
        self._render_all_pages()

    def _on_resize(self, event=None):
        if self._fit_mode == "fit_width" and self._pdf_path:
            new_zoom = self._compute_fit_zoom()
            if abs(new_zoom - self._zoom) > 0.05:
                self._zoom = new_zoom
                self._render_all_pages()

    def _render_all_pages(self):
        """Re-render mọi trang ở zoom hiện tại — vector → raster qua fitz."""
        if not self._pdf_path: return
        self._canvas.delete("all")
        self._page_imgs.clear()
        self._page_meta.clear()
        self._zoom_var.set(f"{int(self._zoom * 100)}%")

        try:
            import fitz
            from PIL import Image as PILImage, ImageTk
        except ImportError as e:
            self._show_message(f"Thiếu thư viện: {e}")
            return

        dpi = max(50, int(self.BASE_DPI * self._zoom))
        mat_zoom = dpi / 72.0
        mat = fitz.Matrix(mat_zoom, mat_zoom)

        try:
            doc = fitz.open(self._pdf_path)
        except Exception as e:
            self._show_message(f"Lỗi mở PDF: {e}")
            return

        canvas_w = max(200, self._canvas.winfo_width() or 600)
        y_cur = self.PAGE_SPACING
        max_x = 0
        try:
            for i in range(doc.page_count):
                page = doc[i]
                pix = page.get_pixmap(matrix=mat, alpha=False)
                pil = PILImage.frombytes(
                    "RGB", [pix.width, pix.height], pix.samples)
                photo = ImageTk.PhotoImage(pil)
                self._page_imgs.append(photo)
                # Tính x để căn giữa
                x = max(self.PAGE_SPACING, (canvas_w - pix.width) // 2)
                # Shadow (vẽ rect lớn hơn 1 chút)
                self._canvas.create_rectangle(
                    x + 3, y_cur + 3,
                    x + pix.width + 3, y_cur + pix.height + 3,
                    fill=self.PAGE_SHADOW, outline="")
                # Page image
                self._canvas.create_image(x, y_cur,
                    image=photo, anchor="nw")
                # (Bỏ overlay "Trang N/M" — đã hiện ở toolbar trên)

                self._page_meta.append(
                    {"y": y_cur, "h": pix.height, "w": pix.width, "x": x})
                y_cur += pix.height + self.PAGE_SPACING
                max_x = max(max_x, x + pix.width)
        finally:
            doc.close()

        self._canvas.configure(
            scrollregion=(0, 0, max(canvas_w, max_x + self.PAGE_SPACING),
                            y_cur))
        self._update_page_indicator()

    # ── Mouse / nav ─────────────────────────────────────────────────────
    def _on_wheel(self, event):
        # Alpha 23b: 1 notch = 2 units (trước 3) → cuộn mượt hơn,
        # không bị "khựng" theo block 3 dòng.
        n = int(-2 * (event.delta / 120))
        if n == 0:
            n = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(n, "units")
        # Debounce update indicator để tránh flicker khi cuộn liên tục
        if hasattr(self, "_wheel_after_id"):
            try: self.after_cancel(self._wheel_after_id)
            except Exception: pass
        self._wheel_after_id = self.after(80, self._update_page_indicator)
        return "break"

    def _on_ctrl_wheel(self, event):
        """Ctrl + wheel → zoom."""
        if event.delta > 0:
            self.zoom_by(self.ZOOM_STEP)
        else:
            self.zoom_by(1 / self.ZOOM_STEP)
        return "break"

    def _pan_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._drag_data["active"] = True
        self._canvas.configure(cursor="fleur")

    def _pan_move(self, event):
        if not self._drag_data["active"]: return
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        self._canvas.xview_scroll(-dx, "units")
        self._canvas.yview_scroll(-dy, "units")
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._update_page_indicator()

    def _pan_end(self, event):
        self._drag_data["active"] = False
        self._canvas.configure(cursor="")

    def _current_page(self) -> int:
        """Trả về index trang đang nằm ở giữa viewport."""
        if not self._page_meta: return 0
        try:
            # Vị trí y giữa canvas viewport (đơn vị canvas coord)
            view_top = self._canvas.canvasy(0)
            view_h = self._canvas.winfo_height()
            view_mid = view_top + view_h // 2
            for i, meta in enumerate(self._page_meta):
                if meta["y"] <= view_mid <= meta["y"] + meta["h"]:
                    return i
            # Nếu chưa hit trang nào, lấy trang đầu chưa qua giữa
            for i, meta in enumerate(self._page_meta):
                if view_mid < meta["y"]:
                    return max(0, i - 1)
            return len(self._page_meta) - 1
        except Exception:
            return 0

    def _update_page_indicator(self):
        if self._page_count == 0:
            self._page_var.set("0 / 0")
            return
        cur = self._current_page()
        self._page_var.set(f"{cur + 1} / {self._page_count}")

    def _prev_page(self):
        if not self._page_meta: return
        cur = self._current_page()
        target = max(0, cur - 1)
        self._scroll_to_page(target)

    def _next_page(self):
        if not self._page_meta: return
        cur = self._current_page()
        target = min(len(self._page_meta) - 1, cur + 1)
        self._scroll_to_page(target)

    def _scroll_to_page(self, page_idx: int):
        if not (0 <= page_idx < len(self._page_meta)): return
        meta = self._page_meta[page_idx]
        # Scroll canvas sao cho top của page đúng top viewport
        try:
            scroll_h = float(self._canvas.cget("scrollregion").split()[3])
            self._canvas.yview_moveto(meta["y"] / scroll_h)
            self._update_page_indicator()
        except Exception: pass
