"""
ui/tab_matrix.py — Tab ② Bảng chỉnh sửa ma trận câu hỏi.
Hiển thị MatrixRow, cho phép bật/tắt, sửa trực tiếp.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from typing import Callable, Optional

from config import LEVEL_COLORS, TYPE_LABELS
from core.models import MatrixData, MatrixRow


class TabMatrix(ttk.Frame):
    """Tab ② — Bảng chỉnh sửa ma trận."""

    def __init__(self, parent,
                  on_export_matrix: Optional[Callable[[], None]] = None,
                  get_subject_grade: Optional[Callable] = None):
        super().__init__(parent)
        self.tier = "basic"  # default
        self._rows: list[MatrixRow] = []
        self._on_export_matrix = on_export_matrix
        self._get_subject_grade = get_subject_grade
        # Callback set bởi main_window khi user load template để cập nhật
        # ExamData (title + time_str) — KHÔNG bắt buộc.
        self._on_matrix_loaded: Optional[Callable[[MatrixData], None]] = None
        self._build()

    def set_matrix_loaded_callback(self, cb: Callable[[MatrixData], None]) -> None:
        """Đăng ký callback nhận MatrixData mới sau khi user load template."""
        self._on_matrix_loaded = cb

    # ── Build ──────────────────────────────────────────────────────────────

    def _build(self) -> None:
        # ── Toolbar: dark slate, icon buttons ──────────────────────────
        tb = tk.Frame(self, bg="#1E293B")
        tb.pack(fill="x", side="top")

        tk.Label(tb, text="  Bảng câu hỏi",
                bg="#1E293B", fg="white",
                font=("Segoe UI", 9, "bold")).pack(side="left", padx=4, pady=4)

        # ── [SPEED-3] Nút "Tải template" — left, accent màu sao cho nổi ──
        tk.Button(
            tb,
            text="📂 Tải template",
            command=self._open_template_picker,
            bg="#F59E0B", fg="white",
            activebackground="#D97706",
            font=("Segoe UI", 8, "bold"),
            relief="flat", cursor="hand2",
            padx=10, pady=3, bd=0,
        ).pack(side="left", padx=(4, 8), pady=4)

        _tb_items = [
            ("✅ Bật tất",    self._enable_all,  "#10B981"),
            ("☐ Tắt tất",    self._disable_all,  "#64748B"),
            ("🔃 Đảo",       self._toggle_all,  "#8B5CF6"),
        ]
        for txt, cmd, bg_c in _tb_items:
            tk.Button(tb, text=txt, command=cmd,
                      bg=bg_c, fg="white", activebackground=bg_c,
                      font=("Segoe UI", 7, "bold"), relief="flat",
                      cursor="hand2", padx=6, pady=2,
                      bd=0).pack(side="left", padx=2, pady=4)

        self._stat_lbl = tk.Label(
            tb, text="", fg="#94A3B8",
            font=("Segoe UI", 8, "bold"),
            bg="#1E293B")
        self._stat_lbl.pack(side="left", padx=12)

        if self._on_export_matrix:
            tk.Button(
                tb,
                text="📥  Xuất ma trận",
                command=self._on_export_matrix,
                bg="#0284C7",
                fg="white",
                activebackground="#0369A1",
                font=("Segoe UI", 7, "bold"),
                relief="flat",
                cursor="hand2",
                padx=8,
                pady=2,
                bd=0,
            ).pack(side="right", padx=8, pady=4)

        # ── Table area (tree_frame uses grid — self uses pack) ──────────
        tree_frame = tk.Frame(self, bg="#F8FAFC")
        tree_frame.pack(fill="both", expand=True, side="top")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        cols = ("✓", "STT", "Chủ đề", "Loại", "Mức", "Mã câu", "Yêu cầu")
        self._tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings",
            selectmode="extended",
        )
        widths = {"✓": 28, "STT": 36, "Chủ đề": 140, "Loại": 56, "Mức": 40,
                  "Mã câu": 64, "Yêu cầu": 240}
        for c in cols:
            self._tree.heading(c, text=c, command=lambda col=c: self._sort(col))
            self._tree.column(c, width=widths[c], minwidth=30)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Bindings
        self._tree.bind("<Double-1>", self._on_dbl_click)
        self._tree.bind("<space>",    self._on_space)
        self._tree.bind("<Delete>",   lambda _: self._delete_selected())

        # Context menu
        self._menu = tk.Menu(self, tearoff=False)
        self._menu.add_command(label="✏️ Chỉnh sửa",  command=self._edit_selected)
        self._menu.add_command(label="🗑 Xóa",         command=self._delete_selected)
        self._menu.add_separator()
        self._menu.add_command(label="✅ Bật câu này", command=lambda: self._set_enabled(True))
        self._menu.add_command(label="☐ Tắt câu này", command=lambda: self._set_enabled(False))
        self._tree.bind("<Button-3>", self._show_menu)

    # ── [SPEED-3] Template picker ─────────────────────────────────────────

    def _open_template_picker(self) -> None:
        """Mở dialog chọn template ma trận đề.

        Nếu ma trận hiện tại có dữ liệu → hỏi xác nhận trước khi thay.
        """
        if self._rows:
            ok = messagebox.askyesno(
                "Xác nhận thay ma trận",
                f"Bảng câu hỏi hiện có {len(self._rows)} dòng.\n\n"
                f"Tải template sẽ THAY THẾ toàn bộ ma trận hiện tại.\n"
                f"Bạn có chắc muốn tiếp tục?",
                parent=self.winfo_toplevel(),
            )
            if not ok:
                return

        from ui.dialog_matrix_template import MatrixTemplatePickerDialog

        # Lấy lớp hiện tại để pre-filter
        current_grade = None
        if self._get_subject_grade:
            try:
                _, current_grade = self._get_subject_grade()
            except Exception:
                pass

        def _on_pick(matrix: MatrixData, meta: dict):
            self.load_matrix(matrix)
            # Báo cho main_window để cập nhật ExamData title + time
            if self._on_matrix_loaded:
                try:
                    self._on_matrix_loaded(matrix)
                except Exception:
                    pass
            # Báo trạng thái
            tpl_name = meta.get("name", "template")
            messagebox.showinfo(
                "✅ Đã tải template",
                f"Đã tải '{tpl_name}'\n"
                f"→ Bảng câu hỏi có {len(matrix.rows)} dòng.\n\n"
                f"Bạn có thể chỉnh sửa từng dòng (double-click) trước khi tạo đề.",
                parent=self.winfo_toplevel(),
            )

        MatrixTemplatePickerDialog(
            self.winfo_toplevel(),
            on_pick=_on_pick,
            current_grade=current_grade,
        )

    # ── Load data ──────────────────────────────────────────────────────────

    def load_matrix(self, matrix_data: MatrixData) -> None:
        self._rows = list(matrix_data.rows)
        self._refresh()

    def set_rows(self, rows: list[MatrixRow]) -> None:
        self._rows = rows
        self._refresh()

    # ── Refresh Treeview ───────────────────────────────────────────────────

    def _refresh(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for i, r in enumerate(self._rows):
            tag = r.level
            check = "✓" if r.enabled else "—"
            self._tree.insert("", "end", iid=str(i), values=(
                check, r.stt, r.topic[:32], r.qtype, r.level,
                ",".join(r.codes[:2]) + ("…" if len(r.codes) > 2 else ""),
                r.requirement[:44],
            ), tags=(tag, "disabled" if not r.enabled else "enabled"))
        # Row coloring
        self._tree.tag_configure("NB",  background="#E8F5E9")
        self._tree.tag_configure("TH",  background="#E3F2FD")
        self._tree.tag_configure("VD",  background="#FFF3E0")
        self._tree.tag_configure("disabled", foreground="#AAAAAA")
        self._update_stats()

    def _update_stats(self) -> None:
        enabled = [r for r in self._rows if r.enabled]
        tn  = sum(1 for r in enabled if r.qtype == "TN")
        ds  = sum(1 for r in enabled if r.qtype == "DS")
        tl  = sum(1 for r in enabled if r.qtype in ("TL","TLN"))
        self._stat_lbl.config(
            text=f"Đã chọn: {len(enabled)}/{len(self._rows)} câu  "
                 f"({tn} TN + {ds} Đ/S + {tl} TL)"
        )

    # ── Events ─────────────────────────────────────────────────────────────

    def _on_dbl_click(self, event) -> None:
        """Double-click: toggle enabled."""
        iid = self._tree.identify_row(event.y)
        if iid:
            idx = int(iid)
            self._rows[idx].enabled = not self._rows[idx].enabled
            self._refresh()

    def _on_space(self, _event) -> None:
        """Space: toggle selected rows."""
        for iid in self._tree.selection():
            idx = int(iid)
            self._rows[idx].enabled = not self._rows[idx].enabled
        self._refresh()

    def _show_menu(self, event) -> None:
        iid = self._tree.identify_row(event.y)
        if iid:
            self._tree.selection_set(iid)
        self._menu.post(event.x_root, event.y_root)

    def _edit_selected(self) -> None:
        sel = self._tree.selection()
        if not sel: return
        idx  = int(sel[0])
        row  = self._rows[idx]
        dlg  = _RowEditDialog(self, row)
        self.wait_window(dlg)
        self._refresh()

    def _delete_selected(self) -> None:
        sel = sorted([int(i) for i in self._tree.selection()], reverse=True)
        for idx in sel:
            self._rows.pop(idx)
        self._refresh()

    def _set_enabled(self, val: bool) -> None:
        for iid in self._tree.selection():
            self._rows[int(iid)].enabled = val
        self._refresh()

    def _enable_all(self) -> None:
        for r in self._rows: r.enabled = True
        self._refresh()

    def _disable_all(self) -> None:
        for r in self._rows: r.enabled = False
        self._refresh()

    def _toggle_all(self) -> None:
        for r in self._rows: r.enabled = not r.enabled
        self._refresh()

    def _sort(self, col: str) -> None:
        """Sắp xếp theo cột."""
        col_map = {
            "Loại": "qtype", "Mức": "level",
            "Chủ đề": "topic", "STT": "stt",
        }
        attr = col_map.get(col)
        if attr:
            self._rows.sort(key=lambda r: getattr(r, attr, ""))
            self._refresh()

    # ── Public API ─────────────────────────────────────────────────────────

    def get_enabled_rows(self) -> list[MatrixRow]:
        return [r for r in self._rows if r.enabled]

    def get_all_rows(self) -> list[MatrixRow]:
        return list(self._rows)


# ── Inline row editor ────────────────────────────────────────────────────────

class _RowEditDialog(tk.Toplevel):
    def __init__(self, parent, row: MatrixRow):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("✏️ Sửa thông tin câu")
        self.grab_set()
        self._row = row
        self._ds_widgets: list[dict] = []
        self._build()

    def _build(self) -> None:
        f = tk.Frame(self, padx=14, pady=12); f.pack(fill="both", expand=True)

        tk.Label(f, text="Chủ đề:").grid(row=0, column=0, sticky="w")
        self._topic = tk.StringVar(value=self._row.topic)
        ttk.Entry(f, textvariable=self._topic, width=46).grid(
            row=0, column=1, columnspan=3, sticky="w", padx=6, pady=3)

        tk.Label(f, text="Loại:").grid(row=1, column=0, sticky="w")
        self._qtype = tk.StringVar(value=self._row.qtype)
        qtype_cb = ttk.Combobox(f, textvariable=self._qtype,
                     values=["TN","DS","TLN","TL"], width=8,
                     state="readonly")
        qtype_cb.grid(row=1, column=1, sticky="w", padx=6)
        qtype_cb.bind("<<ComboboxSelected>>", lambda _: self._on_qtype_change())

        tk.Label(f, text="Mức độ:").grid(row=1, column=2, sticky="w", padx=0)
        self._level = tk.StringVar(value=self._row.level)
        ttk.Combobox(f, textvariable=self._level,
                     values=["NB","TH","VD"], width=6,
                     state="readonly").grid(row=1, column=3, sticky="w", padx=6)

        tk.Label(f, text="Điểm:").grid(row=2, column=0, sticky="w", pady=3)
        self._pts = tk.DoubleVar(value=self._row.points)
        ttk.Spinbox(f, from_=0.25, to=5.0, increment=0.25,
                    textvariable=self._pts, width=7).grid(
            row=2, column=1, sticky="w", padx=6)

        # ── DS: 4 ý a,b,c,d ──────────────────────────────────────────────
        self._ds_frame = tk.LabelFrame(f, text="Cấu trúc 4 ý Đúng-Sai",
                                        fg="#6B21A8", font=("Segoe UI", 9, "bold"))
        # Sẽ hiện/ẩn qua _on_qtype_change

        ds_labels = ["a", "b", "c", "d"]
        default_levels = ["NB", "TH", "VD", "VD"]
        for i, label in enumerate(ds_labels):
            # Lấy dữ liệu từ ds_items hiện có nếu có
            existing = None
            if self._row.ds_items and i < len(self._row.ds_items):
                existing = self._row.ds_items[i]

            row_f = tk.Frame(self._ds_frame, bg="#F5F0FF")
            row_f.pack(fill="x", padx=6, pady=2)

            tk.Label(row_f, text=f"  {label})", bg="#F5F0FF",
                     font=("Segoe UI", 9, "bold"), fg="#6B21A8",
                     width=3).pack(side="left")

            lv_var = tk.StringVar(value=existing.level if existing else default_levels[i])
            lv_cb = ttk.Combobox(row_f, textvariable=lv_var,
                                 values=["NB", "TH", "VD"], width=6,
                                 state="readonly", font=("Segoe UI", 9))
            lv_cb.pack(side="left", padx=4)

            req_var = tk.StringVar(value=existing.requirement if existing else "")
            req_e = ttk.Entry(row_f, textvariable=req_var, font=("Segoe UI", 9))
            req_e.pack(side="left", fill="x", expand=True, padx=4)

            self._ds_widgets.append({
                "label": label, "level": lv_var, "requirement": req_var
            })

        # ── Yêu cầu chung ────────────────────────────────────────────────
        tk.Label(f, text="Yêu cầu cần đạt:").grid(row=4, column=0, sticky="nw", pady=3)
        self._req = tk.Text(f, height=4, width=48, wrap="word",
                             font=("Segoe UI", 9), relief="solid")
        self._req.insert("1.0", self._row.requirement)
        self._req.grid(row=4, column=1, columnspan=3, sticky="w", padx=6)

        btn = tk.Frame(f); btn.grid(row=5, column=0, columnspan=4, pady=10)
        ttk.Button(btn, text="💾 Lưu", command=self._save).pack(side="left", padx=8)
        ttk.Button(btn, text="Hủy",   command=self.destroy).pack(side="left")

        self._grid_frame = f
        self._on_qtype_change()  # hiện/ẩn DS frame ban đầu

    def _on_qtype_change(self):
        if self._qtype.get() == "DS":
            self._ds_frame.grid(row=3, column=0, columnspan=4, sticky="ew", padx=6, pady=4)
            self.geometry("580x480")
        else:
            self._ds_frame.grid_remove()
            self.geometry("560x320")

    def _save(self) -> None:
        from core.models import DSItem
        self._row.topic       = self._topic.get()
        self._row.qtype       = self._qtype.get()
        self._row.level       = self._level.get()
        self._row.points      = self._pts.get()

        if self._row.qtype == "DS" and self._ds_widgets:
            # Cập nhật ds_items từ UI
            items: list[DSItem] = []
            for dw in self._ds_widgets:
                lv = dw["level"].get()
                req = dw["requirement"].get().strip()
                label = dw["label"]
                if not req:
                    req = f"{self._row.topic} [{lv}]"
                code = f"DS{self._row.stt}{label}"
                items.append(DSItem(label=label, level=lv, requirement=req, code=code))
            self._row.ds_items = items
            # Cập nhật requirement tổng hợp
            self._row.requirement = " | ".join(
                f"ý {s.label} [{s.level}]: {s.requirement}" for s in items
            )
        else:
            self._row.requirement = self._req.get("1.0", "end").strip()

        self.destroy()
