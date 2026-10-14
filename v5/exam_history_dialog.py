"""CTk dialog for browsing and restoring exam version history."""
from __future__ import annotations

import os
import subprocess
import sys
from typing import Callable
from tkinter import messagebox, ttk

import customtkinter as ctk

from services import exam_history
from v5.ui_constants import COLOR


class ExamHistoryDialogCTk(ctk.CTkToplevel):
    """Browse, compare, restore and delete saved exam versions."""

    def __init__(self, parent, on_restore: Callable[[dict], None] | None = None):
        super().__init__(parent)
        self.title("Lịch sử phiên bản đề")
        self._on_restore = on_restore
        self._current_exam_id = ""

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width, height = min(1120, screen_width - 80), min(680, screen_height - 100)
        self.geometry(f"{width}x{height}+{(screen_width - width) // 2}+{(screen_height - height) // 2}")
        self.minsize(760, 500)
        self.transient(parent)
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

        self._build()
        self._refresh_exams()
        self.bind("<Escape>", lambda _event: self.destroy())

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=("#0F2D52", "#0B1F35"), height=60)
        header.pack(fill="x", padx=10, pady=(10, 0))
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="  LỊCH SỬ PHIÊN BẢN ĐỀ",
            font=("Segoe UI", 16, "bold"),
            text_color="white",
        ).pack(side="left", padx=12, pady=14)
        self._stats_label = ctk.CTkLabel(
            header,
            text="",
            font=("Segoe UI", 11, "bold"),
            text_color="#FCD34D",
        )
        self._stats_label.pack(side="right", padx=16)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=10)
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        self._exam_tree = self._make_tree_panel(
            body,
            title="Đề thi",
            columns=("name", "n_versions", "latest"),
            labels={"name": "Đề", "n_versions": "# Versions", "latest": "Cập nhật cuối"},
            widths={"name": 245, "n_versions": 86, "latest": 130},
            column=0,
        )
        self._version_tree = self._make_tree_panel(
            body,
            title="Phiên bản (mới đến cũ)",
            columns=("version", "ts", "source", "n_q", "tn", "ds", "tln", "tl", "pts", "note"),
            labels={
                "version": "v", "ts": "Thời gian", "source": "Nguồn",
                "n_q": "Câu", "tn": "TN", "ds": "DS", "tln": "TLN",
                "tl": "TL", "pts": "Điểm", "note": "Ghi chú",
            },
            widths={
                "version": 42, "ts": 128, "source": 76, "n_q": 45,
                "tn": 38, "ds": 38, "tln": 40, "tl": 38, "pts": 58, "note": 180,
            },
            column=1,
        )
        self._exam_tree.bind("<<TreeviewSelect>>", self._on_select_exam)
        self._version_tree.bind("<Double-1>", lambda _event: self._restore_version())

        action_bar = ctk.CTkFrame(self, fg_color=("white", "#1E293B"))
        action_bar.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkButton(
            action_bar, text="Khôi phục version", height=36,
            fg_color=COLOR["primary"], hover_color=COLOR["primary_hover"],
            font=("Segoe UI", 12, "bold"), command=self._restore_version,
        ).pack(side="left", padx=(10, 4), pady=10)
        ctk.CTkButton(
            action_bar, text="So sánh 2 version", height=36,
            fg_color=COLOR["info"], hover_color=COLOR["info_hover"],
            command=self._compare_versions,
        ).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(
            action_bar, text="Xóa version", height=36,
            fg_color=COLOR["danger"], hover_color=COLOR["danger_hover"],
            command=self._delete_version,
        ).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(
            action_bar, text="Mở thư mục", height=36,
            fg_color=COLOR["cyan"], hover_color=COLOR["cyan_hover"],
            command=self._open_folder,
        ).pack(side="right", padx=(4, 10), pady=10)
        ctk.CTkButton(
            action_bar, text="Đóng", height=36,
            fg_color=COLOR["neutral"], hover_color=COLOR["neutral_hover"],
            command=self.destroy,
        ).pack(side="right", padx=4, pady=10)

        ctk.CTkLabel(
            self,
            text="Double-click phiên bản để khôi phục. Ctrl+click chọn hai phiên bản để so sánh.",
            font=("Segoe UI", 10),
            text_color=("gray40", "gray70"),
        ).pack(pady=(0, 8))

    def _make_tree_panel(self, parent, *, title, columns, labels, widths, column):
        panel = ctk.CTkFrame(parent, fg_color=("white", "#1E293B"), corner_radius=8)
        panel.grid(row=0, column=column, sticky="nsew", padx=(0, 5) if column == 0 else (5, 0))
        ctk.CTkLabel(
            panel, text=title, anchor="w",
            font=("Segoe UI", 11, "bold"),
        ).pack(fill="x", padx=12, pady=(10, 6))

        wrap = ctk.CTkFrame(panel, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        tree = ttk.Treeview(wrap, columns=columns, show="headings", selectmode="extended")
        for key in columns:
            tree.heading(key, text=labels[key])
            tree.column(
                key,
                width=widths[key],
                anchor="w" if key in ("name", "latest", "ts", "source", "note") else "center",
            )
        try:
            from v5.tree_style import style_treeview
            style_treeview(tree)
        except Exception:
            pass
        vertical = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        return tree

    def _refresh_exams(self):
        self._exam_tree.delete(*self._exam_tree.get_children())
        for exam_id, count, timestamp in exam_history.list_all_exams():
            self._exam_tree.insert(
                "", "end", iid=exam_id,
                values=(exam_id, count, timestamp[:16].replace("T", " ")),
            )
        stats = exam_history.stats()
        self._stats_label.configure(
            text=f"Tổng: {stats['n_exams']} đề  |  {stats['total_versions']} phiên bản"
        )
        self._version_tree.delete(*self._version_tree.get_children())

    def _refresh_versions(self, exam_id: str):
        self._version_tree.delete(*self._version_tree.get_children())
        for version in exam_history.list_versions(exam_id):
            self._version_tree.insert(
                "", "end", iid=str(version.version),
                values=(
                    version.version, version.timestamp[:16].replace("T", " "),
                    version.source, version.n_questions, version.n_tn,
                    version.n_ds, version.n_tln, version.n_tl,
                    f"{version.total_points:.1f}đ", version.note[:60],
                ),
            )

    def _on_select_exam(self, _event=None):
        selected = self._exam_tree.selection()
        if selected:
            self._current_exam_id = selected[0]
            self._refresh_versions(self._current_exam_id)

    def _restore_version(self):
        if not self._current_exam_id:
            messagebox.showinfo("Chưa chọn đề", "Hãy chọn một đề trước.", parent=self)
            return
        selected = self._version_tree.selection()
        if not selected:
            messagebox.showinfo("Chưa chọn version", "Hãy chọn một phiên bản.", parent=self)
            return
        version = int(selected[0])
        if not messagebox.askyesno(
            "Khôi phục",
            f"Khôi phục đề về version {version}?\n\nĐề hiện tại sẽ được snapshot trước khi ghi đè.",
            parent=self,
        ):
            return
        data = exam_history.restore(self._current_exam_id, version)
        if data is None:
            messagebox.showerror("Lỗi", f"Không tìm thấy version {version}.", parent=self)
            return
        if callable(self._on_restore):
            self._on_restore(data)
            self.destroy()
        else:
            messagebox.showinfo("Khôi phục", f"Đã tải version {version}.", parent=self)

    def _compare_versions(self):
        if not self._current_exam_id:
            messagebox.showinfo("Chưa chọn đề", "Hãy chọn một đề trước.", parent=self)
            return
        selected = self._version_tree.selection()
        if len(selected) >= 2:
            first, second = sorted(int(value) for value in selected)[:2]
        else:
            versions = exam_history.list_versions(self._current_exam_id)
            if len(versions) < 2:
                messagebox.showinfo(
                    "Cần 2 version", "Đề này chưa có đủ hai phiên bản để so sánh.", parent=self
                )
                return
            first, second = versions[-1].version, versions[0].version
        diff = exam_history.compare(self._current_exam_id, first, second)
        if "error" in diff:
            messagebox.showerror("Lỗi", diff["error"], parent=self)
            return
        messagebox.showinfo(
            f"So sánh v{first} và v{second}",
            (
                f"Câu hỏi mới: +{diff['q_added']}\n"
                f"Câu hỏi bị xóa: -{diff['q_removed']}\n"
                f"Câu thay đổi nội dung: {diff['q_changed']}\n"
                f"Chênh lệch điểm: {diff['pts_diff']:+.2f}đ"
            ),
            parent=self,
        )

    def _delete_version(self):
        if not self._current_exam_id:
            return
        selected = self._version_tree.selection()
        if not selected:
            return
        version = int(selected[0])
        if not messagebox.askyesno(
            "Xóa version", f"Xóa version {version}? Thao tác này không thể hoàn tác.", parent=self
        ):
            return
        if exam_history.delete_version(self._current_exam_id, version):
            exam_id = self._current_exam_id
            self._refresh_exams()
            if exam_history.list_versions(exam_id):
                self._current_exam_id = exam_id
                self._exam_tree.selection_set(exam_id)
                self._refresh_versions(exam_id)
            else:
                self._current_exam_id = ""

    def _open_folder(self):
        folder = exam_history.stats().get("dir", "")
        if not folder:
            return
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as exc:
            messagebox.showerror("Lỗi mở thư mục", str(exc), parent=self)
