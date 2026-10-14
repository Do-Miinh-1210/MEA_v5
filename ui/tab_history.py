"""
ui/tab_history.py — Tab Lịch sử đề kiểm tra.
Hiển thị danh sách phiên đã lưu, cho phép mở lại / clone / xóa.
"""
from __future__ import annotations

import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Callable, Optional

from config import SESSION_DIR
from storage.database import list_recent_sessions, load_session, save_session


class TabHistory(ttk.Frame):
    """Tab Lịch sử — quản lý các phiên tạo đề đã lưu."""

    def __init__(
        self,
        parent,
        on_load_session: Optional[Callable[[dict, str], None]] = None,
    ):
        super().__init__(parent)
        self._on_load_session = on_load_session
        self._sessions: list[dict] = []
        self._build()
        self.refresh()

    def _build(self):
        # ── Thanh hành động ──
        act = tk.Frame(self, bg="#E2E8F0")
        act.pack(fill="x")

        ttk.Button(act, text="🔄 Làm mới", command=self.refresh).pack(
            side="left", padx=8, pady=6, ipadx=8)
        ttk.Button(act, text="📂 Mở file…", command=self._open_file).pack(
            side="left", padx=4, pady=6, ipadx=8)
        ttk.Button(act, text="📋 Clone đề", command=self._clone_session).pack(
            side="left", padx=4, pady=6, ipadx=8)
        ttk.Button(act, text="🗑 Xóa", command=self._delete_session).pack(
            side="left", padx=4, pady=6, ipadx=8)
        ttk.Button(act, text="📁 Mở thư mục", command=self._open_folder).pack(
            side="left", padx=4, pady=6, ipadx=8)

        # ── Bảng danh sách phiên ──
        cols = ("name", "subject", "grade", "questions", "saved_at")
        col_labels = {
            "name": "Tên phiên",
            "subject": "Môn",
            "grade": "Lớp",
            "questions": "Số câu",
            "saved_at": "Thời gian lưu",
        }
        col_widths = {"name": 250, "subject": 80, "grade": 60, "questions": 70, "saved_at": 180}

        tree_frame = tk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self._tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            selectmode="browse", height=20,
        )
        for c in cols:
            self._tree.heading(c, text=col_labels[c])
            self._tree.column(c, width=col_widths.get(c, 100), anchor="center" if c != "name" else "w")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)

        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.bind("<Double-1>", lambda _: self._load_selected())

        # ── Preview panel ──
        preview_frame = ttk.LabelFrame(self, text="📝  Xem trước")
        preview_frame.pack(fill="x", padx=8, pady=(0, 8))

        self._preview = tk.Text(
            preview_frame, font=("Segoe UI", 9), height=6,
            state="disabled", wrap="word", bg="#F8FAFC",
        )
        self._preview.pack(fill="x", padx=6, pady=6)

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

    def refresh(self):
        """Tải lại danh sách phiên gần đây."""
        self._sessions = list_recent_sessions(n=50)
        self._tree.delete(*self._tree.get_children())
        for s in self._sessions:
            self._tree.insert("", "end", values=(
                s.get("name", ""),
                s.get("subject", ""),
                s.get("grade", ""),
                s.get("n_questions", 0),
                s.get("saved_at", "")[:19].replace("T", " "),
            ))

    def _get_selected_session(self) -> Optional[dict]:
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Chưa chọn", "Vui lòng chọn một phiên trong danh sách.")
            return None
        idx = self._tree.index(sel[0])
        if idx < len(self._sessions):
            return self._sessions[idx]
        return None

    def _on_select(self, _event=None):
        """Hiển thị preview khi chọn phiên."""
        s = self._get_selected_session()
        if not s:
            return
        self._preview.config(state="normal")
        self._preview.delete("1.0", "end")
        info = (
            f"📁 {s.get('name', '')}\n"
            f"Môn: {s.get('subject', '')} — Lớp: {s.get('grade', '')} — "
            f"Số câu: {s.get('n_questions', 0)}\n"
            f"Lưu lúc: {s.get('saved_at', '')[:19].replace('T', ' ')}\n"
            f"Đường dẫn: {s.get('path', '')}"
        )
        self._preview.insert("1.0", info)
        self._preview.config(state="disabled")

    def _load_selected(self):
        """Mở phiên đã chọn."""
        s = self._get_selected_session()
        if not s:
            return
        path = s.get("path", "")
        if not path or not Path(path).exists():
            messagebox.showerror("Lỗi", f"File không tồn tại:\n{path}")
            return
        try:
            data = load_session(path)
            if self._on_load_session:
                self._on_load_session(data, path)
            messagebox.showinfo("Đã mở", f"Đã tải phiên: {s.get('name', '')}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở phiên:\n{e}")

    def _open_file(self):
        """Mở file phiên từ dialog."""
        path = filedialog.askopenfilename(
            parent=self,
            title="Mở phiên làm việc",
            initialdir=str(SESSION_DIR),
            filetypes=[("JSON", "*.json"), ("Tất cả", "*.*")],
        )
        if not path:
            return
        try:
            data = load_session(path)
            if self._on_load_session:
                self._on_load_session(data, path)
            messagebox.showinfo("Đã mở", f"Đã tải phiên từ file.")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở file:\n{e}")

    def _clone_session(self):
        """Clone phiên đã chọn — lưu thành bản copy mới."""
        s = self._get_selected_session()
        if not s:
            return
        path = s.get("path", "")
        if not path or not Path(path).exists():
            messagebox.showerror("Lỗi", "File gốc không tồn tại.")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Đổi tên + timestamp mới
            import datetime
            data["saved_at"] = datetime.datetime.now().isoformat()
            old_name = Path(path).stem
            new_name = f"{old_name}_clone_{datetime.datetime.now().strftime('%H%M%S')}"
            new_path = SESSION_DIR / f"{new_name}.json"

            with open(str(new_path), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("Clone thành công", f"Đã clone thành:\n{new_name}")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Lỗi clone", str(e))

    def _delete_session(self):
        """Xóa phiên đã chọn."""
        s = self._get_selected_session()
        if not s:
            return
        path = s.get("path", "")
        name = s.get("name", "")
        if not messagebox.askyesno("Xác nhận xóa", f"Xóa phiên '{name}'?\nThao tác này không thể hoàn tác."):
            return
        try:
            Path(path).unlink(missing_ok=True)
            messagebox.showinfo("Đã xóa", f"Đã xóa phiên: {name}")
            self.refresh()
        except Exception as e:
            messagebox.showerror("Lỗi xóa", str(e))

    def _open_folder(self):
        """Mở thư mục chứa phiên trong explorer."""
        import subprocess
        import sys
        folder = str(SESSION_DIR)
        if sys.platform == "win32":
            subprocess.Popen(["explorer", folder])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
