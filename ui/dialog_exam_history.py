"""
ui/dialog_exam_history.py — Dialog xem lịch sử phiên bản đề (P1.7).

Cho phép user:
  • Duyệt tất cả exam đã có history
  • Xem các version của 1 exam
  • So sánh 2 version (diff: số câu thêm/bớt/đổi, điểm chênh lệch)
  • Restore 1 version cũ làm exam hiện tại
  • Xoá version / xoá toàn bộ history của 1 exam
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from services import exam_history


class ExamHistoryDialog(tk.Toplevel):
    """Dialog xem & restore lịch sử exam."""

    def __init__(self, parent, on_restore: Optional[Callable[[dict], None]] = None):
        super().__init__(parent)
        self.title("🕒 Lịch sử phiên bản đề")
        self.configure(bg="#F8FAFC")
        self.grab_set()

        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        w, h = min(1000, sw - 80), min(640, sh - 100)
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.resizable(True, True)
        self.minsize(720, 480)

        self._on_restore = on_restore
        self._current_exam_id: str = ""

        self._build()
        self._refresh_exams()

        self.bind("<Escape>", lambda _e: self.destroy())

    # ── Build ───────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg="#0F2D52", height=56)
        hdr.pack(side="top", fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  🕒  LỊCH SỬ PHIÊN BẢN ĐỀ",
                 bg="#0F2D52", fg="white",
                 font=("Segoe UI", 14, "bold")).pack(side="left", padx=16, pady=12)
        self._stats_lbl = tk.Label(hdr, text="", bg="#0F2D52", fg="#FCD34D",
                                    font=("Segoe UI", 11, "bold"))
        self._stats_lbl.pack(side="right", padx=16, pady=12)
        tk.Frame(self, bg="#7C3AED", height=3).pack(side="top", fill="x")

        # Footer (pack BEFORE body to stick at bottom)
        self._build_footer()

        # Body — split: list exams (left) + list versions (right)
        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # ── LEFT: Exam list ──
        left = tk.Frame(body, bg="#FFFFFF", bd=1, relief="solid")
        body.add(left, weight=2)

        tk.Label(left, text="Đề thi (theo title)",
                 bg="#1E293B", fg="white",
                 font=("Segoe UI", 10, "bold"),
                 anchor="w", padx=10, pady=6).pack(side="top", fill="x")

        style = ttk.Style()
        style.configure("Hist.Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure("Hist.Treeview.Heading", font=("Segoe UI", 10, "bold"))

        cols_e = ("name", "n_versions", "latest")
        self._exam_tree = ttk.Treeview(left, columns=cols_e,
                                        show="headings", style="Hist.Treeview",
                                        height=15)
        for c, w_, h_ in [("name", 250, "Đề"), ("n_versions", 80, "# Versions"),
                          ("latest", 130, "Cập nhật cuối")]:
            self._exam_tree.heading(c, text=h_)
            self._exam_tree.column(c, width=w_, anchor="w")
        evsb = ttk.Scrollbar(left, orient="vertical", command=self._exam_tree.yview)
        self._exam_tree.configure(yscrollcommand=evsb.set)
        evsb.pack(side="right", fill="y")
        self._exam_tree.pack(side="left", fill="both", expand=True)
        self._exam_tree.bind("<<TreeviewSelect>>", self._on_select_exam)

        # ── RIGHT: Version list ──
        right = tk.Frame(body, bg="#FFFFFF", bd=1, relief="solid")
        body.add(right, weight=3)

        tk.Label(right, text="Phiên bản (mới → cũ)",
                 bg="#1E293B", fg="white",
                 font=("Segoe UI", 10, "bold"),
                 anchor="w", padx=10, pady=6).pack(side="top", fill="x")

        cols_v = ("version", "ts", "source", "n_q", "tn", "ds", "tln", "tl", "pts", "note")
        self._ver_tree = ttk.Treeview(right, columns=cols_v,
                                       show="headings", style="Hist.Treeview",
                                       height=15)
        widths = {"version": 60, "ts": 130, "source": 80, "n_q": 50,
                  "tn": 40, "ds": 40, "tln": 40, "tl": 40,
                  "pts": 60, "note": 200}
        labels = {"version": "v", "ts": "Thời gian", "source": "Nguồn",
                  "n_q": "Câu", "tn": "TN", "ds": "DS", "tln": "TLN", "tl": "TL",
                  "pts": "Điểm", "note": "Ghi chú"}
        for c in cols_v:
            self._ver_tree.heading(c, text=labels[c])
            self._ver_tree.column(c, width=widths[c],
                                   anchor="w" if c in ("ts", "source", "note") else "center")
        vvsb = ttk.Scrollbar(right, orient="vertical", command=self._ver_tree.yview)
        self._ver_tree.configure(yscrollcommand=vvsb.set)
        vvsb.pack(side="right", fill="y")
        self._ver_tree.pack(side="left", fill="both", expand=True)
        self._ver_tree.bind("<Double-1>", lambda _e: self._on_restore_version())

    def _build_footer(self):
        """Action bar ở đáy — pack với side="bottom" để luôn hiện."""
        # Hint
        tk.Label(self,
                 text="💡 Double-click vào version = Khôi phục đề  •  Esc = Đóng",
                 bg="#F8FAFC", fg="#64748B",
                 font=("Segoe UI", 8, "italic"),
                 ).pack(side="bottom", fill="x", pady=(0, 6))

        ab = tk.Frame(self, bg="#E2E8F0")
        ab.pack(side="bottom", fill="x", padx=10, pady=(4, 0))

        def _btn(text, bg, hover, cmd, primary=False):
            return tk.Button(
                ab, text=text, bg=bg, fg="white",
                activebackground=hover, activeforeground="white",
                font=("Segoe UI", 10 if not primary else 11, "bold"),
                relief="flat", cursor="hand2", padx=10, pady=6, bd=0,
                command=cmd,
            )

        ab.grid_columnconfigure(50, weight=1)
        _btn("  ✅  Khôi phục version  ", "#10B981", "#059669",
             self._on_restore_version, primary=True
             ).grid(row=0, column=1, padx=3, pady=4)
        _btn("  🔍  So sánh 2 version  ", "#3B82F6", "#2563EB",
             self._on_compare).grid(row=0, column=2, padx=3, pady=4)
        _btn("  🗑  Xoá version  ", "#EF4444", "#DC2626",
             self._on_delete_version).grid(row=0, column=3, padx=3, pady=4)
        _btn("  📁  Mở thư mục  ", "#0891B2", "#0E7490",
             self._on_open_folder).grid(row=0, column=99, padx=3, pady=4)
        _btn("  ✕  Đóng  ", "#94A3B8", "#64748B",
             self.destroy).grid(row=0, column=100, padx=3, pady=4)

    # ── Refresh ────────────────────────────────────────────────────────

    def _refresh_exams(self):
        for it in self._exam_tree.get_children():
            self._exam_tree.delete(it)
        items = exam_history.list_all_exams()
        for exam_id, n, ts in items:
            self._exam_tree.insert("", "end", iid=exam_id,
                                    values=(exam_id, n, ts[:16].replace("T", " ")))
        s = exam_history.stats()
        self._stats_lbl.config(
            text=f"Tổng: {s['n_exams']} đề  •  {s['total_versions']} versions",
        )
        # Clear version pane
        for it in self._ver_tree.get_children():
            self._ver_tree.delete(it)

    def _refresh_versions(self, exam_id: str):
        for it in self._ver_tree.get_children():
            self._ver_tree.delete(it)
        versions = exam_history.list_versions(exam_id)
        for v in versions:
            ts_short = v.timestamp[:16].replace("T", " ")
            self._ver_tree.insert("", "end", iid=str(v.version), values=(
                v.version, ts_short, v.source,
                v.n_questions, v.n_tn, v.n_ds, v.n_tln, v.n_tl,
                f"{v.total_points:.1f}đ",
                v.note[:60],
            ))

    def _on_select_exam(self, _e=None):
        sel = self._exam_tree.selection()
        if not sel:
            return
        self._current_exam_id = sel[0]
        self._refresh_versions(sel[0])

    # ── Actions ────────────────────────────────────────────────────────

    def _on_restore_version(self):
        if not self._current_exam_id:
            messagebox.showinfo("Chưa chọn đề",
                                "Hãy chọn 1 đề ở cột trái trước.",
                                parent=self)
            return
        sel = self._ver_tree.selection()
        if not sel:
            messagebox.showinfo("Chưa chọn version",
                                "Hãy chọn 1 version ở cột phải.", parent=self)
            return
        v = int(sel[0])
        if not messagebox.askyesno(
            "Khôi phục",
            f"Khôi phục đề về version {v}?\n\n"
            "Đề HIỆN TẠI sẽ được snapshot trước khi ghi đè.",
            parent=self,
        ):
            return
        data = exam_history.restore(self._current_exam_id, v)
        if data is None:
            messagebox.showerror("Lỗi", f"Không tìm thấy version {v}.",
                                 parent=self)
            return
        if self._on_restore:
            self._on_restore(data)
            self.destroy()
        else:
            messagebox.showinfo("OK", f"Đã restore data version {v}.",
                                parent=self)

    def _on_compare(self):
        if not self._current_exam_id:
            return
        sel = self._ver_tree.selection()
        if len(sel) < 2:
            # Bấm 1 lần lấy 2 version mới nhất + cũ nhất nếu chưa multi-select
            versions = exam_history.list_versions(self._current_exam_id)
            if len(versions) < 2:
                messagebox.showinfo("Cần ≥ 2 version",
                                    "Đề này chỉ có 1 version — không có gì để so sánh.",
                                    parent=self)
                return
            v1 = versions[-1].version  # cũ nhất
            v2 = versions[0].version   # mới nhất
        else:
            vs = sorted(int(s) for s in sel)
            v1, v2 = vs[0], vs[-1]
        diff = exam_history.compare(self._current_exam_id, v1, v2)
        if "error" in diff:
            messagebox.showerror("Lỗi", diff["error"], parent=self)
            return
        msg = (
            f"So sánh v{v1} → v{v2}:\n\n"
            f"  • Câu hỏi mới: +{diff['q_added']}\n"
            f"  • Câu hỏi bị xoá: -{diff['q_removed']}\n"
            f"  • Câu thay đổi nội dung: {diff['q_changed']}\n"
            f"  • Điểm: {diff['pts_diff']:+.2f}đ\n\n"
            f"Tip: Ctrl+click 2 version để so sánh chính xác cặp đó."
        )
        messagebox.showinfo(f"Diff v{v1} ↔ v{v2}", msg, parent=self)

    def _on_delete_version(self):
        if not self._current_exam_id:
            return
        sel = self._ver_tree.selection()
        if not sel:
            return
        v = int(sel[0])
        if not messagebox.askyesno(
            "Xoá version",
            f"Xoá version {v} của đề này?\n(Không thể khôi phục)",
            parent=self,
        ):
            return
        if exam_history.delete_version(self._current_exam_id, v):
            self._refresh_versions(self._current_exam_id)
            # Refresh stats trên header
            self._refresh_exams()
            # Reselect exam
            try:
                self._exam_tree.selection_set(self._current_exam_id)
            except Exception:
                pass

    def _on_open_folder(self):
        s = exam_history.stats()
        folder = s.get("dir", "")
        if not folder:
            return
        try:
            import os, sys, subprocess
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)
