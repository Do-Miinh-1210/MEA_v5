"""
v5/quick_gen.py — Dialog "Tạo đề nhanh" (CTk port từ ui/dialog_quick_gen.py).

Hai chế độ:
  1) 🤖 Tự động: chọn lớp + thời lượng (15p/45p/60p/90p) + chủ đề (auto-pick
     3-5 chủ đề nếu để trống) → AI tự phân bổ số câu theo template chuẩn BGD.
  2) 🛠 Thủ công: nhập số câu TN/DS/TLN/TL + thời lượng + lớp + chủ đề.

Dùng ``core.quick_matrix.build_quick_matrix`` /
``build_quick_matrix_custom`` — full backward-compat với v4.

API:
    QuickGenDialogV5(parent, on_accept=lambda matrix, subject, grade: ...)
"""
from __future__ import annotations

from tkinter import messagebox
from typing import Callable

import customtkinter as ctk


DURATIONS = [
    ("15p", "15 phút",  "7 câu TN"),
    ("45p", "45 phút",  "12 TN + 2 DS + 3 TLN"),
    ("60p", "60 phút",  "15 TN + 3 DS + 4 TLN + 1 TL"),
    ("90p", "90 phút",  "18 TN + 4 DS + 6 TLN + 2 TL"),
]
GRADES = ["6", "7", "8", "9", "10", "11", "12"]


class QuickGenDialogV5(ctk.CTkToplevel):
    """Dialog CTk modal — sinh MatrixData rồi gọi on_accept(matrix, subject, grade)."""

    WIDTH  = 760
    HEIGHT = 600

    def __init__(self, parent,
                 on_accept: Callable | None = None,
                 default_subject: str = "Toán",
                 default_grade: str = "12"):
        super().__init__(parent)
        self.title("🚀  Tạo đề nhanh")
        self._on_accept = on_accept
        self._subject = default_subject

        # Center on screen
        try:
            sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
            x = (sw - self.WIDTH) // 2; y = (sh - self.HEIGHT) // 2
            self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")
        except Exception:
            self.geometry(f"{self.WIDTH}x{self.HEIGHT}")

        try: self.attributes("-topmost", True)
        except: pass
        try: self.grab_set()
        except: pass

        self._mode = ctk.StringVar(value="auto")
        self._grade_var = ctk.StringVar(value=default_grade)
        self._duration_var = ctk.StringVar(value="90p")
        self._n_tn_var  = ctk.StringVar(value="15")
        self._n_ds_var  = ctk.StringVar(value="3")
        self._n_tln_var = ctk.StringVar(value="4")
        self._n_tl_var  = ctk.StringVar(value="1")
        self._time_str_var = ctk.StringVar(value="60 phút")
        self._selected_topics: set[str] = set()
        self._topic_checkbox_vars: dict[str, ctk.BooleanVar] = {}

        self._build()
        self._on_mode_change("auto")

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Return>", lambda e: self._on_accept_click())

    # ── Layout ─────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=("#1F497D", "#0B1F35"),
                            corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🚀  Tạo đề nhanh",
                      text_color="white",
                      font=("Segoe UI", 16, "bold"),
                      anchor="w").pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(hdr,
                      text="Chọn mẫu thời lượng (Tự động) hoặc nhập số câu (Thủ công)",
                      text_color="#93C5FD",
                      font=("Segoe UI", 10),
                      anchor="w").pack(side="left", padx=8, pady=10)

        # Mode selector
        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(mode_row, text="Chế độ:",
                      font=("Segoe UI", 11, "bold")
                      ).pack(side="left", padx=(0, 8))
        seg = ctk.CTkSegmentedButton(
            mode_row,
            values=["🤖 Tự động", "🛠 Thủ công"],
            command=lambda v: self._on_mode_change(
                "auto" if v.startswith("🤖") else "manual"),
        )
        seg.set("🤖 Tự động")
        seg.pack(side="left")

        # Body
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=16, pady=(6, 6))

        self._auto_frame   = ctk.CTkFrame(self._body, fg_color="transparent")
        self._manual_frame = ctk.CTkFrame(self._body, fg_color="transparent")

        self._build_auto(self._auto_frame)
        self._build_manual(self._manual_frame)

        # Topics card (shared, always visible)
        topics_card = ctk.CTkFrame(self, fg_color=("#F8FAFC", "#1E293B"),
                                      corner_radius=8)
        topics_card.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        ctk.CTkLabel(topics_card,
                      text="📚  Chủ đề (để trống → AI tự chọn 3–5 chủ đề ngẫu nhiên)",
                      font=("Segoe UI", 11, "bold"),
                      anchor="w").pack(anchor="w", padx=10, pady=(8, 4))

        self._topics_scroll = ctk.CTkScrollableFrame(topics_card,
                                                       fg_color="transparent",
                                                       height=140)
        self._topics_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        # Sẽ refresh sau khi grade đổi
        self._refresh_topics_for_grade(self._grade_var.get())

        # Buttons
        btns = ctk.CTkFrame(self, fg_color=("#F3F4F6", "#0F172A"),
                              corner_radius=0, height=56)
        btns.pack(fill="x", side="bottom")
        btns.pack_propagate(False)
        ctk.CTkButton(btns, text="❌  Huỷ", width=120, height=34,
                       fg_color=("#6B7280", "#374151"),
                       hover_color=("#4B5563", "#1F2937"),
                       command=self.destroy
                       ).pack(side="right", padx=8, pady=10)
        ctk.CTkButton(btns, text="🚀  Tạo ma trận", width=160, height=34,
                       fg_color="#10B981", hover_color="#059669",
                       font=("Segoe UI", 12, "bold"),
                       command=self._on_accept_click
                       ).pack(side="right", padx=4, pady=10)

    def _build_auto(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="Lớp:", width=60,
                      font=("Segoe UI", 11)).pack(side="left")
        ctk.CTkOptionMenu(row, values=GRADES, variable=self._grade_var,
                            width=80,
                            command=self._on_grade_change
                            ).pack(side="left", padx=(0, 16))
        ctk.CTkLabel(row, text="Thời lượng:", width=92,
                      font=("Segoe UI", 11)).pack(side="left")
        ctk.CTkOptionMenu(row,
                            values=[d[0] for d in DURATIONS],
                            variable=self._duration_var,
                            width=80
                            ).pack(side="left")

        # Description grid
        desc = ctk.CTkFrame(parent, fg_color=("#F0F9FF", "#0F172A"),
                              corner_radius=8)
        desc.pack(fill="x", pady=(8, 4))
        ctk.CTkLabel(desc,
                      text="📊  Mẫu phân bổ theo thời lượng:",
                      font=("Segoe UI", 10, "bold"),
                      anchor="w").pack(anchor="w", padx=10, pady=(6, 2))
        for code, label, blueprint in DURATIONS:
            ctk.CTkLabel(desc,
                          text=f"     • {label}:  {blueprint}",
                          font=("Segoe UI", 10),
                          text_color=("#374151", "#CBD5E1"),
                          anchor="w").pack(anchor="w", padx=10)
        ctk.CTkLabel(desc,
                      text="",
                      font=("Segoe UI", 4)).pack(padx=10, pady=2)

    def _build_manual(self, parent):
        # Lớp + thời lượng (chuỗi)
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", pady=4)
        ctk.CTkLabel(row1, text="Lớp:", width=60,
                      font=("Segoe UI", 11)).pack(side="left")
        ctk.CTkOptionMenu(row1, values=GRADES, variable=self._grade_var,
                            width=80,
                            command=self._on_grade_change
                            ).pack(side="left", padx=(0, 16))
        ctk.CTkLabel(row1, text="Thời lượng:", width=92,
                      font=("Segoe UI", 11)).pack(side="left")
        ctk.CTkEntry(row1, textvariable=self._time_str_var, width=120
                       ).pack(side="left")

        # Số câu theo loại
        row2 = ctk.CTkFrame(parent, fg_color=("#F0F9FF", "#0F172A"),
                              corner_radius=8)
        row2.pack(fill="x", pady=(8, 4))

        ctk.CTkLabel(row2, text="📝  Số lượng câu mỗi loại:",
                      font=("Segoe UI", 10, "bold"),
                      anchor="w").grid(row=0, column=0, columnspan=4,
                                          sticky="w", padx=10, pady=(6, 4))

        def _add_input(col, label, var, hint):
            cell = ctk.CTkFrame(row2, fg_color="transparent")
            cell.grid(row=1, column=col, padx=8, pady=4)
            ctk.CTkLabel(cell, text=label, font=("Segoe UI", 11, "bold")
                          ).pack(anchor="w")
            ctk.CTkEntry(cell, textvariable=var, width=72).pack()
            ctk.CTkLabel(cell, text=hint,
                          font=("Segoe UI", 9), text_color="gray"
                          ).pack(anchor="w")

        _add_input(0, "TN",  self._n_tn_var,  "Trắc nghiệm")
        _add_input(1, "DS",  self._n_ds_var,  "Đúng/Sai")
        _add_input(2, "TLN", self._n_tln_var, "Trả lời ngắn")
        _add_input(3, "TL",  self._n_tl_var,  "Tự luận")
        # spacer row
        ctk.CTkLabel(row2, text="", font=("Segoe UI", 4)
                      ).grid(row=2, column=0, columnspan=4, pady=2)

    # ── Topic chips ───────────────────────────────────────────────────────
    def _refresh_topics_for_grade(self, grade: str):
        """Reload danh sách chủ đề cho lớp + render checkbox grid."""
        # Clear
        for w in self._topics_scroll.winfo_children():
            try: w.destroy()
            except Exception: pass
        self._topic_checkbox_vars.clear()
        # Giữ selected khi đổi grade nếu topic vẫn còn
        prev_selected = set(self._selected_topics)
        self._selected_topics.clear()

        try:
            from core.quick_matrix import get_topics_for_grade
            topics = get_topics_for_grade(grade) or []
        except Exception:
            topics = []

        if not topics:
            ctk.CTkLabel(self._topics_scroll,
                          text=f"(Không có chủ đề định sẵn cho lớp {grade})",
                          text_color="gray",
                          font=("Segoe UI", 10)
                          ).pack(anchor="w", padx=8, pady=4)
            return

        # Grid 2 cột
        cur_row = None
        for i, t in enumerate(topics):
            if i % 2 == 0:
                cur_row = ctk.CTkFrame(self._topics_scroll,
                                          fg_color="transparent")
                cur_row.pack(fill="x")
            var = ctk.BooleanVar(value=(t in prev_selected))
            self._topic_checkbox_vars[t] = var
            if t in prev_selected:
                self._selected_topics.add(t)
            chk = ctk.CTkCheckBox(
                cur_row, text=t[:62] + ("…" if len(t) > 62 else ""),
                variable=var,
                font=("Segoe UI", 10),
                onvalue=True, offvalue=False,
                command=lambda topic=t, v=var: self._toggle_topic(topic, v),
            )
            chk.pack(side="left", padx=6, pady=2, anchor="w", expand=True,
                      fill="x")

    def _toggle_topic(self, topic: str, var: ctk.BooleanVar):
        if var.get():
            self._selected_topics.add(topic)
        else:
            self._selected_topics.discard(topic)

    def _on_grade_change(self, _val=None):
        self._refresh_topics_for_grade(self._grade_var.get())

    # ── Mode switch ───────────────────────────────────────────────────────
    def _on_mode_change(self, mode: str):
        self._mode.set(mode)
        if mode == "auto":
            self._manual_frame.pack_forget()
            self._auto_frame.pack(fill="x")
        else:
            self._auto_frame.pack_forget()
            self._manual_frame.pack(fill="x")

    # ── Accept ────────────────────────────────────────────────────────────
    def _on_accept_click(self):
        topics = sorted(self._selected_topics) or None
        grade = self._grade_var.get()
        mode = self._mode.get()

        try:
            from core.quick_matrix import (build_quick_matrix,
                                              build_quick_matrix_custom)
            if mode == "auto":
                duration = self._duration_var.get()
                matrix = build_quick_matrix(
                    duration=duration,
                    grade=grade,
                    topics=topics,
                    subject=self._subject,
                )
            else:
                # Manual — parse số câu
                def _to_int(s, default=0):
                    try: return max(0, int(str(s).strip()))
                    except Exception: return default

                n_tn  = _to_int(self._n_tn_var.get())
                n_ds  = _to_int(self._n_ds_var.get())
                n_tln = _to_int(self._n_tln_var.get())
                n_tl  = _to_int(self._n_tl_var.get())
                if n_tn + n_ds + n_tln + n_tl == 0:
                    messagebox.showwarning(
                        "Thiếu dữ liệu",
                        "Nhập ít nhất 1 câu (TN / DS / TLN / TL).",
                        parent=self)
                    return
                matrix = build_quick_matrix_custom(
                    n_tn=n_tn, n_ds=n_ds, n_tln=n_tln, n_tl=n_tl,
                    time_str=self._time_str_var.get() or "45 phút",
                    grade=grade,
                    topics=topics,
                    subject=self._subject,
                )
        except Exception as e:
            messagebox.showerror(
                "Lỗi tạo ma trận",
                f"{type(e).__name__}: {e}",
                parent=self)
            return

        try:
            if callable(self._on_accept):
                self._on_accept(matrix, self._subject, grade)
        except Exception as e:
            messagebox.showerror(
                "Lỗi callback", f"on_accept lỗi:\n{e}", parent=self)
            return

        # Toast success qua root nếu có
        try:
            from v5.toast import show_toast
            n_rows = len(getattr(matrix, "rows", []))
            show_toast(self.master,
                        f"✓ Đã sinh ma trận {n_rows} câu — lớp {grade}",
                        kind="success", duration=3)
        except Exception: pass

        self.destroy()
