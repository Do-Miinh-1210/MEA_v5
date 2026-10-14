"""
ui/tab_bank.py — Tab ④ Ngân hàng câu hỏi.
Cập nhật:
  - Mỗi câu có question_id riêng hiển thị rõ ràng
  - Nút upload NHCH chung lên Cloud (Supabase)
  - Fix hiển thị ảnh QR rõ nét
  - Thông tin admin: SĐT/Zalo + Gmail
  - Tự động nhận diện Môn học, Chủ đề bằng AI khi upload file Word/PDF
"""

from __future__ import annotations
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Callable, Optional

from storage.database import db_stats, search_questions, delete_question, save_questions
from core.models import Question
from config import TYPE_LABELS, LEVEL_COLORS

BLUE = "#1F497D"; BG = "#F9F7F4"


class _CloudConflictResolverDialog(tk.Toplevel):
    """Resolve NHCH cloud conflicts per question before importing."""

    def __init__(self, parent, details: list):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("Xu ly xung dot NHCH Cloud")
        self.transient(parent)
        self.grab_set()
        self.result: Optional[dict[str, str]] = None
        self._details = details
        self._decisions = {d.question_id: "copy" for d in details}

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w = min(980, max(760, int(sw * 0.72)))
        h = min(620, max(460, int(sh * 0.62)))
        self.geometry(f"{w}x{h}+{(sw - w)//2}+{max(0, (sh - h)//2 - 20)}")
        self.minsize(720, 420)
        self.configure(bg="#FFFFFF")

        hdr = tk.Frame(self, bg=BLUE)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="Xu ly xung dot cau hoi Cloud",
            bg=BLUE,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            pady=10,
        ).pack(side="left", padx=14)

        tk.Label(
            self,
            text=(
                "Moi dong la mot cau trung question_id nhung noi dung khac. "
                "Mac dinh: nhap ban Cloud thanh ban rieng de khong ghi de local."
            ),
            bg="#FFFFFF",
            fg="#475569",
            font=("Segoe UI", 9),
            wraplength=w - 40,
            justify="left",
        ).pack(fill="x", padx=14, pady=(10, 6))

        body = tk.Frame(self, bg="#FFFFFF")
        body.pack(fill="both", expand=True, padx=14, pady=6)
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)

        cols = ("action", "qid", "fields", "local", "cloud")
        self._tree = ttk.Treeview(body, columns=cols, show="headings", height=12)
        headings = {
            "action": "Hanh dong",
            "qid": "ID",
            "fields": "Khac truong",
            "local": "Local preview",
            "cloud": "Cloud preview",
        }
        widths = {"action": 120, "qid": 130, "fields": 150, "local": 250, "cloud": 250}
        for col in cols:
            self._tree.heading(col, text=headings[col])
            self._tree.column(col, width=widths[col], minwidth=80, stretch=col in {"local", "cloud"})
        self._tree.grid(row=0, column=0, sticky="nsew")
        ysb = ttk.Scrollbar(body, orient="vertical", command=self._tree.yview)
        ysb.grid(row=0, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=ysb.set)
        self._tree.bind("<Double-1>", lambda _e: self._cycle_selected())

        for detail in details:
            self._tree.insert("", "end", iid=detail.question_id, values=(
                self._action_label("copy"),
                detail.question_id,
                ", ".join(detail.changed_fields[:5]) or "noi dung",
                detail.local_preview,
                detail.cloud_preview,
            ))

        btns = tk.Frame(self, bg="#FFFFFF")
        btns.pack(fill="x", padx=14, pady=(4, 12))
        for text, action, color in [
            ("Ban chon: nhap ban sao", "copy", "#10B981"),
            ("Ban chon: giu local", "skip", "#F59E0B"),
        ]:
            tk.Button(
                btns,
                text=text,
                bg=color,
                fg="white",
                relief="flat",
                cursor="hand2",
                font=("Segoe UI", 9, "bold"),
                padx=10,
                pady=6,
                command=lambda a=action: self._set_selected(a),
            ).pack(side="left", padx=4)

        tk.Button(
            btns,
            text="Tat ca: nhap ban sao",
            bg="#E0F2FE",
            fg="#075985",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=6,
            command=lambda: self._set_all("copy"),
        ).pack(side="left", padx=4)
        tk.Button(
            btns,
            text="Tat ca: giu local",
            bg="#FEF3C7",
            fg="#92400E",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=6,
            command=lambda: self._set_all("skip"),
        ).pack(side="left", padx=4)

        tk.Button(
            btns,
            text="Huy",
            bg="#F1F5F9",
            fg="#475569",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self.destroy,
        ).pack(side="right", padx=4)
        tk.Button(
            btns,
            text="Ap dung",
            bg="#0EA5E9",
            fg="white",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=6,
            command=self._apply,
        ).pack(side="right", padx=4)

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.focus_force()

    @staticmethod
    def _action_label(action: str) -> str:
        return "Nhap ban sao" if action == "copy" else "Giu local"

    def _refresh_iid(self, iid: str) -> None:
        values = list(self._tree.item(iid, "values"))
        values[0] = self._action_label(self._decisions.get(iid, "copy"))
        self._tree.item(iid, values=values)

    def _set_selected(self, action: str) -> None:
        selection = self._tree.selection()
        if not selection:
            messagebox.showinfo("Chua chon cau", "Hay chon it nhat mot dong xung dot.", parent=self)
            return
        for iid in selection:
            self._decisions[iid] = action
            self._refresh_iid(iid)

    def _set_all(self, action: str) -> None:
        for detail in self._details:
            self._decisions[detail.question_id] = action
            self._refresh_iid(detail.question_id)

    def _cycle_selected(self) -> None:
        selection = self._tree.selection()
        for iid in selection:
            self._decisions[iid] = "skip" if self._decisions.get(iid) == "copy" else "copy"
            self._refresh_iid(iid)

    def _apply(self) -> None:
        self.result = dict(self._decisions)
        self.destroy()


class TabBank(ttk.Frame):
    """Tab ④ — Ngân hàng câu hỏi."""

    def __init__(self, parent,
                 get_ai_call:       Optional[Callable] = None,
                 get_subject_grade: Optional[Callable] = None,
                 on_add_to_exam_cb: Optional[Callable] = None):
        super().__init__(parent)
        self._results:        list[dict] = []
        self._get_ai          = get_ai_call
        self._get_subj_grade  = get_subject_grade
        self._on_add_to_exam  = on_add_to_exam_cb
        self._cloud_cancel_event = None
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # ── Thanh tìm kiếm ────────────────────────────────────────────────
        frm_s = ttk.LabelFrame(self, text="🔍  Tìm kiếm câu hỏi")
        frm_s.pack(fill="x", padx=8, pady=6)
        g = tk.Frame(frm_s); g.pack(fill="x", padx=8, pady=6)

        # Bố cục 2 hàng để các nút luôn nhìn thấy được ở cửa sổ nhỏ:
        #   Hàng 0: Môn / Lớp / Loại / Mức / Từ khoá
        #   Hàng 1: nhóm nút Tìm / Lớp hiện tại / Xoá lọc (canh phải để cân)
        tk.Label(g, text="Môn:").grid(row=0, column=0, sticky="w")
        self.subject_var = tk.StringVar()
        ttk.Entry(g, textvariable=self.subject_var, width=10
                  ).grid(row=0, column=1, sticky="w", padx=6)

        tk.Label(g, text="Lớp:").grid(row=0, column=2, sticky="w")
        self.grade_var = tk.StringVar()
        ttk.Combobox(g, textvariable=self.grade_var, width=6,
                      values=["", "1", "2", "3", "4", "5", "6", "7", "8",
                              "9", "10", "11", "12"],
                      state="normal"
                      ).grid(row=0, column=3, sticky="w", padx=6)

        tk.Label(g, text="Loại câu:").grid(row=0, column=4, sticky="w")
        self.qtype_var = tk.StringVar()
        ttk.Combobox(g, textvariable=self.qtype_var, width=8,
                      values=["", "TN", "DS", "TLN", "TL"],
                      state="normal"
                      ).grid(row=0, column=5, sticky="w", padx=6)

        tk.Label(g, text="Mức độ:").grid(row=0, column=6, sticky="w")
        self.level_var = tk.StringVar()
        ttk.Combobox(g, textvariable=self.level_var, width=7,
                      values=["", "NB", "TH", "VD"],
                      state="normal"
                      ).grid(row=0, column=7, sticky="w", padx=6)

        tk.Label(g, text="Từ khoá:").grid(row=0, column=8, sticky="w", padx=0)
        self.kw_var = tk.StringVar()
        ttk.Entry(g, textvariable=self.kw_var, width=22).grid(
            row=0, column=9, columnspan=3, sticky="we", padx=6)

        # Hàng 2: các nút hành động (luôn nằm dưới input, không tràn ngang).
        btns = tk.Frame(g)
        btns.grid(row=1, column=0, columnspan=12, sticky="we", pady=(6, 0))
        # Đẩy nhóm nút sang trái — trải đều khoảng cách.
        ttk.Button(btns, text="🔍  Tìm kiếm",
                   command=self._search).pack(side="left", padx=3)
        # Nút quick-fill từ tab Cài đặt → giảm thao tác cho GV
        ttk.Button(btns, text="📌 Lớp hiện tại",
                   command=self._fill_current_grade
                   ).pack(side="left", padx=3)
        ttk.Button(btns, text="🗑 Xóa lọc",
                   command=self._clear_filters
                   ).pack(side="left", padx=3)
        # Auto-fill subject + grade ban đầu nếu có từ tab Cài đặt
        try:
            if self._get_subj_grade:
                _s, _g = self._get_subj_grade()
                if _s:
                    self.subject_var.set(_s)
                if _g:
                    self.grade_var.set(str(_g))
        except Exception:
            pass

        self._stats_lbl = tk.Label(frm_s, text="", fg="#555", font=("Segoe UI", 8))
        self._stats_lbl.pack(anchor="w", padx=10, pady=4)

        # ── Toolbar 2 hàng: hàng 1 chọn câu, hàng 2 NHCH (luôn thấy, không bị chen chúc) ──
        bar_wrap = tk.Frame(self, bg="#1E293B")
        bar_wrap.pack(fill="x", padx=8, pady=(4, 2))

        bar = tk.Frame(bar_wrap, bg="#1E293B")
        bar.pack(fill="x")

        tk.Label(bar, text="🏦  Ngân hàng câu hỏi",
                bg="#1E293B", fg="white",
                font=("Segoe UI", 11, "bold")).pack(side="left", padx=4, pady=6)

        self._del_sel_btn = None
        for txt, cmd, bg_c in [
            ("☑ Bật tất",  self._select_all,       "#10B981"),
            ("☐ Tắt tất", self._deselect_all,     "#64748B"),
            ("🔄 Đảo",    self._invert_selection, "#8B5CF6"),
            ("🗑 Xóa",    self._delete_sel,       "#EF4444"),
        ]:
            btn = tk.Button(bar, text=txt, command=cmd,
                    bg=bg_c, fg="white", activebackground=bg_c,
                    font=("Segoe UI", 9, "bold"),
                    relief="flat", cursor="hand2", bd=0,
                    padx=10, pady=6)
            btn.pack(side="left", padx=2)
            if self._del_sel_btn is None:
                self._del_sel_btn = btn

        self._sel_count_lbl = tk.Label(bar, text="Chưa chọn",
                fg="#94A3B8", font=("Segoe UI", 9, "bold"),
                bg="#1E293B")
        self._sel_count_lbl.pack(side="left", padx=12)

        bar_cloud = tk.Frame(bar_wrap, bg="#334155")
        bar_cloud.pack(fill="x", pady=(4, 6))
        tk.Label(bar_cloud, text="☁️  Đồng bộ NHCH chung:",
                bg="#334155", fg="#E2E8F0",
                font=("Segoe UI", 9, "bold")).pack(side="left", padx=8, pady=6)

        self._upload_btn = None
        self._download_btn = None
        for i, (txt, cmd, bg_c) in enumerate([
            ("☁️  Upload lên NHCH chung",  self._upload_to_nhch,    "#7C3AED"),
            ("📥  Tải từ NHCH chung",    self._download_from_nhch, "#0891B2"),
            ("📄  Upload Word/PDF/Ảnh", self._upload_from_file,   "#2563EB"),
        ]):
            btn = tk.Button(bar_cloud, text=txt, command=cmd,
                    bg=bg_c, fg="white", activebackground=bg_c,
                    font=("Segoe UI", 9, "bold"),
                    relief="flat", cursor="hand2", bd=0,
                    padx=12, pady=8)
            btn.pack(side="left", padx=4)
            if i == 0:
                self._upload_btn = btn
            elif i == 1:
                self._download_btn = btn

        # ── Thanh tiến độ ─────────────────────────────────────────────────
        prog_f = tk.Frame(self)
        prog_f.pack(fill="x", padx=8, pady=2)
        self._prog_lbl = tk.Label(prog_f, text="", fg="#1F497D",
                                   font=("Segoe UI", 8))
        self._prog_lbl.pack(side="left", padx=4)
        self._prog_bar = ttk.Progressbar(prog_f, mode="determinate",
                                          length=300, maximum=100)
        self._prog_bar.pack(side="left", padx=4)
        self._prog_bar.pack_forget()  # ẩn ban đầu
        self._cloud_cancel_btn = tk.Button(
            prog_f, text="⏹ Hủy sync", command=self._cancel_cloud_sync,
            bg="#EF4444", fg="white", activebackground="#DC2626",
            font=("Segoe UI", 8, "bold"), relief="flat", cursor="hand2",
            bd=0, padx=8, pady=3,
        )
        self._cloud_cancel_btn.pack(side="left", padx=4)
        self._cloud_cancel_btn.pack_forget()

        # ── Toolbar thao tác câu đơn ─────────────────────────────────────
        act = tk.Frame(self, bg=BG)
        act.pack(fill="x", padx=8, pady=4)
        tk.Label(act, text="Thao tác câu:", font=("Segoe UI", 8, "bold"),
                 bg=BG).pack(side="left", padx=4)
        for txt, cmd in [
            ("✏️ Chỉnh sửa",         self._edit_selected),
            ("➕ Thêm vào đề",        self._add_selected_to_exam),
            ("🤖 Sửa lỗi AI",        self._ai_fix_selected),
            ("📋 Sao chép nội dung", self._copy_selected),
        ]:
            ttk.Button(act, text=txt, command=cmd).pack(
                side="left", padx=3, pady=3, ipadx=4)

        # ── Main: Tree + Detail ───────────────────────────────────────────
        main = tk.Frame(self)
        main.pack(fill="both", expand=True, padx=8)

        cols = ("✓", "QID", "ID", "Môn/Lớp", "Loại", "Mức",
                "Chủ đề", "Câu hỏi (tóm tắt)", "Trạng thái", "Ngày tạo")
        self._tree = ttk.Treeview(main, columns=cols, show="headings",
                                   height=16, selectmode="extended")
        ws = {"✓": 44, "QID": 120, "ID": 42, "Môn/Lớp": 70, "Loại": 52,
              "Mức": 42, "Chủ đề": 106, "Câu hỏi (tóm tắt)": 210,
              "Trạng thái": 68, "Ngày tạo": 96}
        for c in cols:
            self._tree.heading(c, text=c,
                               command=lambda _c=c: self._sort_by(_c))
            self._tree.column(c, width=ws[c], minwidth=22)

        # Cột checkbox — cột rộng + font lớn để dễ bấm
        self._tree.column("✓", width=44, minwidth=40, anchor="center")
        self._tree.heading("✓", text="✓")

        vsb = ttk.Scrollbar(main, orient="vertical",   command=self._tree.yview)
        hsb = ttk.Scrollbar(main, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.tag_configure("error_row",  foreground="#CC0000", background="#FFF0F0")
        self._tree.tag_configure("review_bad", foreground="#E65100", background="#FFF3E0")
        self._tree.tag_configure("ok_row",     foreground="#2E7D32")
        self._tree.tag_configure("checked",    background="#EDE9FE")
        self._tree.tag_configure("duplicate",  foreground="#B45309", background="#FEF3C7")

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, weight=1)

        self._checked_ids: set = set()   # tập iid đang được tích ✓
        self._drag_selecting = False
        self._drag_start_state = False

        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self._tree.bind("<Double-1>",         lambda e: self._edit_selected())
        self._tree.bind("<Return>",           lambda e: self._edit_selected())
        self._tree.bind("<Motion>",           self._on_hover)
        self._tree.bind("<Leave>",            lambda e: None)
        self._tree.bind("<Control-a>",        lambda e: self._select_all())
        self._tree.bind("<Control-A>",        lambda e: self._select_all())
        # Click vào cột checkbox
        self._tree.bind("<ButtonPress-1>",    self._on_click)
        self._tree.bind("<B1-Motion>",        self._on_drag)
        self._tree.bind("<ButtonRelease-1>",  self._on_release)
        self._last_hover_id = None

        # Detail pane
        detail_f = tk.Frame(main, width=310)
        detail_f.grid(row=0, column=2, sticky="ns", padx=0)
        detail_f.grid_propagate(False)
        tk.Label(detail_f, text="Chi tiết câu hỏi",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=4)
        self._detail = scrolledtext.ScrolledText(
            detail_f, font=("Segoe UI", 9),
            state="disabled", wrap="word", width=38, height=22)
        self._detail.pack(fill="both", expand=True)

        self._detail.tag_configure("hdr",      font=("Segoe UI", 9, "bold"), foreground=BLUE)
        self._detail.tag_configure("qid",      font=("Consolas", 8, "bold"), foreground="#7C3AED")
        self._detail.tag_configure("answer",   foreground="#007000", font=("Segoe UI", 9, "bold"))
        self._detail.tag_configure("solution", foreground="#804000")
        self._detail.tag_configure("error",    foreground="#CC0000", background="#FFF0F0")

        self._refresh_stats()

    # ── Search ────────────────────────────────────────────────────────────────
    # ── Helpers cho filter ────────────────────────────────────────────────
    def _fill_current_grade(self) -> None:
        """Quick-fill Môn + Lớp từ tab Cài đặt → search ngay."""
        if not self._get_subj_grade:
            return
        try:
            subj, grade = self._get_subj_grade()
            if subj:
                self.subject_var.set(subj)
            if grade:
                self.grade_var.set(str(grade))
            self._search()
        except Exception:
            pass

    def _clear_filters(self) -> None:
        """Xóa toàn bộ filter để xem tất cả câu trong NHCH."""
        for var_name in ("subject_var", "grade_var", "qtype_var",
                          "level_var", "kw_var"):
            try:
                getattr(self, var_name).set("")
            except Exception:
                pass
        self._search()

    def _search(self) -> None:
        try:
            self._results = search_questions(
                subject=self.subject_var.get(),
                grade=self.grade_var.get(),
                qtype=self.qtype_var.get(),
                level=self.level_var.get(),
                keyword=self.kw_var.get(),
                limit=5000,
            )
        except Exception as e:
            messagebox.showerror("Lỗi tìm kiếm", str(e)); return

        self._checked_ids.clear()
        self._tree.delete(*self._tree.get_children())

        # Phát hiện câu trùng lặp dựa trên nội dung câu hỏi
        import re as _re
        _seen: dict[str, int] = {}   # normalized_text → first index
        _dup_indices: set[int] = set()
        for i, q in enumerate(self._results):
            raw = (q.get("question", "") or "").strip()
            # Normalize: lowercase, remove whitespace/punctuation
            norm = _re.sub(r'\s+', '', raw.lower())[:120]
            if norm and len(norm) > 15:
                if norm in _seen:
                    _dup_indices.add(i)
                    _dup_indices.add(_seen[norm])
                else:
                    _seen[norm] = i

        n_dup = 0
        for i, q in enumerate(self._results):
            created  = (q.get("_created_at") or "")[:10]
            has_err  = q.get("_error", False)
            review   = q.get("_review") or {}
            rev_ok   = review.get("ok", True)
            qid      = q.get("question_id", "") or ""
            is_dup   = i in _dup_indices

            if is_dup:
                row_tag, status = "duplicate", "🔁 Trùng"
                n_dup += 1
            elif has_err:
                row_tag, status = "error_row",  "⚠️ Lỗi"
            elif not rev_ok:
                row_tag, status = "review_bad", "⚠️ Xem lại"
            else:
                row_tag, status = "ok_row",     "✅ OK"

            self._tree.insert("", "end", values=(
                "☐",
                qid,
                q.get("_bank_id", ""),
                f"{q.get('subject','')} {q.get('grade','')}",
                q.get("qtype", q.get("type", "")),
                q.get("level", ""),
                q.get("topic", "")[:26],
                q.get("question", "")[:60],
                status,
                created,
            ), tags=(row_tag,))

        dup_text = f"  │  🔁 {n_dup} câu trùng" if n_dup else ""
        self._stats_lbl.config(text=f"Tìm thấy: {len(self._results)} câu{dup_text} — Shift+Click chọn dải  Ctrl+A chọn tất")
        self._update_sel_count()

    def _sort_by(self, col: str) -> None:
        data = [(self._tree.set(k, col), k) for k in self._tree.get_children("")]
        data.sort()
        for i, (_, k) in enumerate(data):
            self._tree.move(k, "", i)

    # ── Checkbox / Bulk-select helpers ────────────────────────────────────────
    def _toggle_check(self, iid: str) -> None:
        """Bật/tắt checkbox của một dòng."""
        if iid in self._checked_ids:
            self._checked_ids.discard(iid)
            self._tree.set(iid, "✓", "☐")
            tags = [t for t in self._tree.item(iid, "tags") if t != "checked"]
            self._tree.item(iid, tags=tags)
        else:
            self._checked_ids.add(iid)
            self._tree.set(iid, "✓", "☑")
            tags = list(self._tree.item(iid, "tags")) + ["checked"]
            self._tree.item(iid, tags=tags)
        self._update_sel_count()

    def _on_click(self, event) -> None:
        """Click cột ✓ → toggle checkbox; click ô khác → bình thường."""
        region = self._tree.identify_region(event.x, event.y)
        col    = self._tree.identify_column(event.x)
        iid    = self._tree.identify_row(event.y)
        if not iid:
            return
        if region == "cell" and col == "#1":   # cột ✓
            self._toggle_check(iid)
            self._drag_selecting = True
            self._drag_start_state = iid in self._checked_ids
            return "break"

    def _on_drag(self, event) -> None:
        """Quét chuột qua cột ✓ → chọn hàng loạt."""
        if not self._drag_selecting:
            return
        col = self._tree.identify_column(event.x)
        iid = self._tree.identify_row(event.y)
        if not iid or col != "#1":
            return
        if self._drag_start_state:
            if iid not in self._checked_ids:
                self._checked_ids.add(iid)
                self._tree.set(iid, "✓", "☑")
                tags = list(self._tree.item(iid, "tags")) + ["checked"]
                self._tree.item(iid, tags=tags)
        else:
            if iid in self._checked_ids:
                self._checked_ids.discard(iid)
                self._tree.set(iid, "✓", "☐")
                tags = [t for t in self._tree.item(iid, "tags") if t != "checked"]
                self._tree.item(iid, tags=tags)
        self._update_sel_count()

    def _on_release(self, event) -> None:
        self._drag_selecting = False

    def _select_all(self) -> None:
        for iid in self._tree.get_children():
            self._checked_ids.add(iid)
            self._tree.set(iid, "✓", "☑")
            tags = list(self._tree.item(iid, "tags"))
            if "checked" not in tags:
                self._tree.item(iid, tags=tags + ["checked"])
        self._update_sel_count()

    def _deselect_all(self) -> None:
        for iid in list(self._checked_ids):
            self._tree.set(iid, "✓", "☐")
            tags = [t for t in self._tree.item(iid, "tags") if t != "checked"]
            self._tree.item(iid, tags=tags)
        self._checked_ids.clear()
        self._update_sel_count()

    def _invert_selection(self) -> None:
        all_iids = set(self._tree.get_children())
        new_checked = all_iids - self._checked_ids
        # Bỏ tích cũ
        for iid in list(self._checked_ids):
            self._tree.set(iid, "✓", "☐")
            tags = [t for t in self._tree.item(iid, "tags") if t != "checked"]
            self._tree.item(iid, tags=tags)
        # Tích mới
        self._checked_ids = new_checked
        for iid in self._checked_ids:
            self._tree.set(iid, "✓", "☑")
            tags = list(self._tree.item(iid, "tags"))
            if "checked" not in tags:
                self._tree.item(iid, tags=tags + ["checked"])
        self._update_sel_count()

    def _update_sel_count(self) -> None:
        n = len(self._checked_ids)
        if n == 0:
            self._sel_count_lbl.config(text="Chưa chọn câu nào", fg="#888")
        else:
            self._sel_count_lbl.config(text=f"Đã chọn: {n} câu", fg="#7C3AED")

    def _get_selected_q(self) -> Optional[dict]:
        # Ưu tiên tree selection (click thường)
        sel = self._tree.selection()
        if sel:
            bank_id = self._tree.item(sel[0])["values"][2]  # index 2 = ID
            return next((x for x in self._results if x.get("_bank_id") == bank_id), None)
        return None

    def _get_checked_questions(self) -> list[dict]:
        """Trả về list câu hỏi đang được tích ✓."""
        results = []
        for iid in self._checked_ids:
            try:
                bank_id = self._tree.item(iid)["values"][2]
                q = next((x for x in self._results if x.get("_bank_id") == bank_id), None)
                if q:
                    results.append(q)
            except Exception:
                pass
        return results

    def _get_all_selected(self) -> list[dict]:
        """Lấy câu đang tích ✓; nếu không có thì lấy tree selection."""
        checked = self._get_checked_questions()
        if checked:
            return checked
        # fallback: tree selection
        results = []
        for iid in self._tree.selection():
            bank_id = self._tree.item(iid)["values"][2]
            q = next((x for x in self._results if x.get("_bank_id") == bank_id), None)
            if q:
                results.append(q)
        return results

    # ── Detail panel ─────────────────────────────────────────────────────────
    def _on_hover(self, event) -> None:
        """Rê chuột qua dòng → hiện chi tiết bên phải."""
        row_id = self._tree.identify_row(event.y)
        if not row_id or row_id == self._last_hover_id:
            return
        self._last_hover_id = row_id
        try:
            bank_id = self._tree.item(row_id)["values"][2]   # index 2 = _bank_id
            q = next((x for x in self._results if x.get("_bank_id") == bank_id), None)
            if q:
                self._show_detail(q)
        except Exception:
            pass

    def _on_tree_select(self, _event) -> None:
        sel = self._tree.selection()
        n = len(sel)
        if n > 1:
            self._stats_lbl.config(
                text=f"Đã chọn (highlight): {n} câu  |  ☑ để tích chọn hàng loạt"
            )
        q = self._get_selected_q()
        if q:
            self._show_detail(q)

    def _show_detail(self, q: dict) -> None:
        dt = self._detail
        dt.config(state="normal")
        dt.delete("1.0", "end")

        def ins(t, tag=None):
            dt.insert("end", t, tag) if tag else dt.insert("end", t)

        qtype = q.get("qtype", q.get("type", ""))
        ins(f"{TYPE_LABELS.get(qtype, qtype)}  │  {q.get('level','')}  │  "
            f"{q.get('subject','')} {q.get('grade','')}\n", "hdr")

        qid = q.get("question_id", "") or ""
        if qid:
            ins(f"🔑 ID: {qid}\n", "qid")

        ins(f"Chủ đề: {q.get('topic','')}\n", "hdr")
        ins("─" * 36 + "\n")

        if q.get("_error"):
            ins("⚠️ CÂU NÀY CÓ LỖI KHI TẠO\n", "error")

        ins(q.get("question", "") + "\n")

        if qtype == "TN":
            opts   = q.get("options") or {}
            answer = q.get("answer",  "")
            ins("─" * 36 + "\n")
            for k, v in opts.items():
                mark = "  ◄ ĐÁP ÁN" if k == answer else ""
                ins(f"  {k}. {v}{mark}\n", "answer" if mark else None)

        elif qtype == "DS":
            ins("─" * 36 + "\n")
            items   = q.get("items")   or {}
            answers = q.get("answers") or {}
            for k, v in items.items():
                verdict = "[Đ]" if answers.get(k) else "[S]"
                ins(f"  ({k}) {v}  {verdict}\n",
                    "answer" if answers.get(k) else None)

        elif qtype in ("TLN", "TL"):
            ans = q.get("answer", "")
            pts = q.get("points", "")
            if pts: ins(f"Điểm: {pts}\n")
            if ans: ins(f"Đáp số: {ans}\n", "answer")

        sol = q.get("solution", "")
        if sol:
            ins("─" * 36 + "\n")
            ins(f"Lời giải:\n{sol}\n", "solution")

        review = q.get("_review") or {}
        if review:
            ins("─" * 36 + "\n")
            ok_str = "✅ Đạt" if review.get("ok", True) else "❌ Có vấn đề"
            ins(f"Review AI: {ok_str}  Điểm: {review.get('score','?')}/10\n")
            if review.get("issue"):
                ins(f"Vấn đề: {review['issue']}\n", "error")

        dt.config(state="disabled")

    # ── Actions ───────────────────────────────────────────────────────────────
    def _edit_selected(self) -> None:
        q_dict = self._get_selected_q()
        if not q_dict:
            messagebox.showinfo("Chưa chọn", "Hãy chọn một câu hỏi."); return
        try:
            q = Question.from_dict(q_dict)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không đọc được câu hỏi: {e}"); return

        subject, grade = "", ""
        if self._get_subj_grade:
            subject, grade = self._get_subj_grade()

        from ui.dialogs_new import EditQuestionDialogV2

        def _on_save(updated_q: Question) -> None:
            try:
                from storage.database import update_question
                update_question(q_dict["_bank_id"], updated_q)
                messagebox.showinfo("✅", "Đã lưu thay đổi vào Ngân hàng.")
                self._search()
            except Exception as ex:
                messagebox.showerror("Lỗi lưu", str(ex))

        EditQuestionDialogV2(self, q, on_save_cb=_on_save,
                              get_ai_call=self._get_ai,
                              subject=subject, grade=grade)

    def _add_selected_to_exam(self) -> None:
        all_q = self._get_all_selected()
        if not all_q:
            messagebox.showinfo("Chưa chọn", "Hãy chọn ít nhất một câu hỏi."); return
        if not self._on_add_to_exam:
            messagebox.showinfo("Chưa có đề",
                                "Vui lòng tạo đề trước rồi quay lại thêm câu."); return

        # Convert tất cả trước, rồi mới add batch
        questions = []
        errors = []
        for q_dict in all_q:
            try:
                questions.append(Question.from_dict(q_dict))
            except Exception as e:
                errors.append(str(e))

        # Tự động chuyển đổi TikZ sang ảnh (EMF/PNG) nếu có
        try:
            from services.tikz_vector_workflow import convert_questions_tikz_to_emf, count_pending_blocks
            if count_pending_blocks(questions) > 0:
                convert_questions_tikz_to_emf(questions)
        except Exception as _tz_err:
            import logging
            logging.getLogger(__name__).warning("Lỗi tự động chuyển TikZ khi thêm vào đề: %s", _tz_err)

        # Batch add: chỉ reload UI 1 lần cuối cùng
        added = 0
        for i, q in enumerate(questions):
            is_last = (i == len(questions) - 1)
            try:
                self._on_add_to_exam(q, _batch=not is_last)
                added += 1
            except Exception as e:
                errors.append(str(e))

        if added:
            messagebox.showinfo("✅", f"Đã thêm {added} câu vào đề.")
        if errors:
            messagebox.showwarning("Lỗi", f"{len(errors)} câu bị lỗi:\n" + "\n".join(errors[:5]))

    def _ai_fix_selected(self) -> None:
        q_dict = self._get_selected_q()
        if not q_dict:
            messagebox.showinfo("Chưa chọn", "Hãy chọn một câu hỏi."); return
        if not self._get_ai:
            messagebox.showwarning("Chưa cấu hình AI", "Cần cài đặt API Key trước."); return
        try:
            q = Question.from_dict(q_dict)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e)); return
        subject, grade = "", ""
        if self._get_subj_grade:
            subject, grade = self._get_subj_grade()
        from ui.dialogs_new import EditQuestionDialogV2

        def _on_save(updated_q: Question) -> None:
            try:
                from storage.database import update_question
                update_question(q_dict["_bank_id"], updated_q)
                self._search()
            except Exception as ex:
                messagebox.showerror("Lỗi lưu", str(ex))

        dlg = EditQuestionDialogV2(self, q, on_save_cb=_on_save,
                                    get_ai_call=self._get_ai,
                                    subject=subject, grade=grade)
        self.after(300, dlg._ai_fix)

    def _copy_selected(self) -> None:
        """Copy câu đang chọn ra clipboard ở định dạng Word-ready.

        Dùng `export.question_formatter.format_question` — paste vào Word
        sẽ ra đúng cấu trúc: "Câu N." + TN/DS/TLN format chuẩn.
        """
        q_dict = self._get_selected_q()
        if not q_dict:
            messagebox.showinfo("Chưa chọn", "Hãy chọn một câu hỏi.")
            return
        try:
            from core.models import Question
            from export.question_formatter import format_question
            q = Question.from_dict(q_dict)
            text = format_question(q, idx=1, include_solution=True)
        except Exception as e:
            # Fallback: text thuần nếu format lỗi
            text = q_dict.get("question", "") or ""
            messagebox.showwarning(
                "Cảnh báo format", f"Không format được Word: {e}\nĐã copy text thô.")
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo(
            "✅ Đã sao chép",
            "Đã copy câu hỏi (định dạng Word-ready).\nPaste thẳng vào Word.")

    def _delete_sel(self) -> None:
        """Xóa các câu đang tích ✓ (hoặc tree-selection nếu không tích)."""
        to_del = self._get_all_selected()
        if not to_del:
            messagebox.showinfo("Chưa chọn", "Hãy tích ☑ câu muốn xóa trước."); return
        if not messagebox.askyesno("Xóa",
            f"Xóa {len(to_del)} câu hỏi đã chọn?", parent=self): return

        self._set_busy(True, f"Đang xóa 0/{len(to_del)}...")

        def _do_delete():
            total = len(to_del)
            for i, q in enumerate(to_del, 1):
                try:
                    delete_question(int(q["_bank_id"]))
                except Exception:
                    pass
                self.after(0, lambda i=i, t=total: self._update_progress(
                    int(i/t*100), f"Đang xóa {i}/{t}..."))
            self.after(0, self._on_delete_done)

        threading.Thread(target=_do_delete, daemon=True).start()

    def _on_delete_done(self) -> None:
        self._set_busy(False)
        self._refresh_stats()
        self._deselect_all()
        self._search()

    # ── Progress helpers ──────────────────────────────────────────────────────
    def _set_busy(self, busy: bool, msg: str = "") -> None:
        """Hiện/ẩn thanh tiến độ và khóa/mở nút."""
        if busy:
            self._prog_bar.pack(side="left", padx=4)
            self._prog_bar["value"] = 0
            self._prog_lbl.config(text=msg)
            self._cloud_cancel_btn.pack(side="left", padx=4)
            if self._upload_btn:
                self._upload_btn.config(state="disabled")
            if self._download_btn:
                self._download_btn.config(state="disabled")
            if self._del_sel_btn:
                self._del_sel_btn.config(state="disabled")
        else:
            self._prog_bar.pack_forget()
            self._cloud_cancel_btn.pack_forget()
            self._prog_lbl.config(text="")
            if self._upload_btn:
                self._upload_btn.config(state="normal")
            if self._download_btn:
                self._download_btn.config(state="normal")
            if self._del_sel_btn:
                self._del_sel_btn.config(state="normal")
        self.update_idletasks()

    def _update_progress(self, pct: int, msg: str = "") -> None:
        self._prog_bar["value"] = pct
        if msg:
            self._prog_lbl.config(text=msg)
        self.update_idletasks()

    def _cancel_cloud_sync(self) -> None:
        if self._cloud_cancel_event is not None:
            self._cloud_cancel_event.set()
            self._prog_lbl.config(text="⏹ Đang hủy đồng bộ sau batch hiện tại...")

    # ── Upload / Download NHCH chung ─────────────────────────────────────────
    def _upload_to_nhch(self) -> None:
        """Upload câu đang tích ✓ (hoặc tất cả kết quả search) lên NHCH chung (Supabase)."""
        selected = self._get_all_selected()
        if not selected:
            if not self._results:
                messagebox.showinfo("Chưa có câu",
                    "Hãy tìm kiếm câu hỏi trước, rồi tích ☑ câu muốn upload."); return
            if not messagebox.askyesno("Upload tất cả?",
                f"Bạn chưa tích câu cụ thể.\n"
                f"Upload tất cả {len(self._results)} câu trong kết quả tìm kiếm?",
                parent=self):
                return
            selected = self._results

        if not messagebox.askyesno("Xác nhận upload",
            f"Upload {len(selected)} câu lên Ngân hàng câu hỏi chung (Cloud)?\n\n"
            "Câu hỏi đã tồn tại sẽ được tự động bỏ qua.", parent=self):
            return

        import uuid as _uuid
        qs_for_cloud = []
        for q in selected:
            qid = (q.get("question_id") or "").strip()
            if not qid:
                qid = f"QID-{_uuid.uuid4().hex[:10].upper()}"
            opts = q.get("options") or {}
            if not isinstance(opts, dict):
                opts = {}
            qs_for_cloud.append({
                "question_id": qid,
                "subject":     q.get("subject", ""),
                "grade":       q.get("grade",   ""),
                "topic":       q.get("topic",   ""),
                "level":       q.get("level",   ""),
                "qtype":       q.get("qtype",   q.get("type", "")),
                "question":    q.get("question",""),
                "options":     opts,
                "answer":      q.get("answer",  ""),
                "solution":    q.get("solution",""),
            })

        self._cloud_cancel_event = threading.Event()
        self._set_busy(True, f"Chuẩn bị upload {len(qs_for_cloud)} câu...")

        def _do_upload():
            try:
                from services.license_manager import get_machine_id
                from services.cloud_workflow import upload_questions_with_progress
                mid = get_machine_id()

                def _on_progress(event: dict):
                    pct = int(event.get("pct", 0))
                    msg = event.get("message") or "☁️ Đang đồng bộ Cloud..."
                    self.after(0, lambda p=pct, m=msg: self._update_progress(p, m))

                res = upload_questions_with_progress(
                    qs_for_cloud,
                    mid=mid,
                    batch_size=40,
                    cancel_event=self._cloud_cancel_event,
                    progress_cb=_on_progress,
                )
                self.after(0, lambda r=res: self._on_upload_result(r))

            except Exception as e:
                self.after(0, lambda err=str(e): self._on_upload_error(err))

        threading.Thread(target=_do_upload, daemon=True).start()

    def _on_upload_result(self, result) -> None:
        self._cloud_cancel_event = None
        if getattr(result, "cancelled", False):
            self._set_busy(False)
            messagebox.showwarning(
                "Đã hủy upload",
                result.message,
                parent=self,
            )
            return
        if not getattr(result, "ok", False):
            self._on_upload_error(result.message)
            return
        self._on_upload_done(
            getattr(result, "added", 0),
            getattr(result, "skipped", 0),
            getattr(result, "errors", []),
            getattr(result, "total", 0),
        )

    def _on_upload_done(self, added, skipped, errors, total) -> None:
        self._cloud_cancel_event = None
        self._set_busy(False)
        detail = f"✅ Đã thêm mới:  {added} câu\n⏭️ Bỏ qua trùng:  {skipped} câu"
        if errors:
            detail += f"\n⚠️ Lỗi {len(errors)} câu: {errors[0]}"
        messagebox.showinfo("Upload hoàn tất ✅",
            f"Đã xử lý {total} câu hỏi!\n\n{detail}", parent=self)

    def _on_upload_error(self, err: str) -> None:
        self._cloud_cancel_event = None
        self._set_busy(False)
        messagebox.showerror("Lỗi upload", f"Không thể tải lên Cloud:\n{err}", parent=self)

    # ── YC3: Upload Word/PDF/Ảnh vào ngân hàng ──────────────────────────────
    def _upload_from_file(self) -> None:
        """Upload câu hỏi từ file Word/PDF/Ảnh/LaTeX vào ngân hàng.

        Logic mới (v4.2+):
          • .pdf / .png / .jpg / ...  → mở wizard `dialog_import_pdf`
            (AI Vision + auto-solve + preview + push NHCH cloud)
          • .docx / .tex             → vẫn dùng parser cũ text-only
            (đủ tốt cho file Word có cấu trúc rõ)
        """
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Chọn file Word/PDF/Ảnh/LaTeX chứa câu hỏi",
            filetypes=[
                ("Tất cả hỗ trợ", "*.docx *.pdf *.tex *.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
                ("PDF / Ảnh (AI Vision)", "*.pdf *.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
                ("Word Document", "*.docx"),
                ("LaTeX", "*.tex"),
                ("Tất cả", "*.*"),
            ],
        )
        if not path:
            return

        import os
        ext = os.path.splitext(path)[1].lower()

        # ── PDF / Ảnh → wizard mới (AI Vision pipeline) ─────────────────
        if ext in (".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"):
            try:
                from ui.dialog_import_pdf import ImportPdfDialog
                # Lấy môn/lớp đang chọn ở filter để pre-fill
                subject = (self._subject_var.get()
                            if hasattr(self, "_subject_var") else "Toán") or "Toán"
                grade = (self._grade_var.get()
                          if hasattr(self, "_grade_var") else "12") or "12"
                # Lấy tab_config từ main_window để dialog dùng luôn API key đã lưu
                top = self.winfo_toplevel()
                tab_cfg = getattr(top, "_tab_config", None)
                dlg = ImportPdfDialog(top, subject=subject, grade=grade,
                                        tab_config=tab_cfg)
                # Pre-fill file path
                dlg._filepath = path
                dlg._file_var.set(path)
                # Trigger info update
                try:
                    if ext == ".pdf":
                        import fitz
                        d = fitz.open(path); n = len(d); d.close()
                        dlg._file_info.config(
                            text=f"PDF • {n} trang • "
                                  f"{os.path.getsize(path)/1024:.0f} KB",
                            fg="#1F497D")
                    else:
                        dlg._file_info.config(
                            text=f"Ảnh • {os.path.getsize(path)/1024:.0f} KB",
                            fg="#1F497D")
                except Exception:
                    pass
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror(
                    "Lỗi mở wizard",
                    f"Không mở được dialog import PDF: {e}",
                    parent=self)
            return

        # ── DOCX / TEX → parser cũ text-based ──────────────────────────
        self._prog_lbl.config(text="⏳ Đang phân tích file…")
        self._prog_bar.pack(side="left", padx=4)
        self._prog_bar["value"] = 20
        self.update_idletasks()

        import threading
        def _do():
            try:
                from core.doc_question_parser import parse_questions_from_file
                questions = parse_questions_from_file(path)
                self.after(0, lambda q=questions: self._on_file_parsed(q, path))
            except Exception as e:
                self.after(0, lambda err=str(e): self._on_file_error(err))

        threading.Thread(target=_do, daemon=True).start()

    def _on_file_parsed(self, questions: list, filepath: str) -> None:
        """Sau khi parse xong file Word/PDF/LaTeX."""
        import os
        self._prog_bar["value"] = 60

        if not questions:
            self._prog_lbl.config(text="⚠️ Không tìm thấy câu hỏi nào trong file.")
            self._prog_bar.pack_forget()
            ext = os.path.splitext(filepath)[1].lower()
            if ext == ".tex":
                hint = ("Kiểm tra định dạng LaTeX:\n"
                        "• TN: \\begin{ex}...\\choice{\\True ...}{...}{...}{...}\\end{ex}\n"
                        "• DS: \\begin{ex}...\\choiceTF{...}{...}{...}{...}\\end{ex}\n"
                        "• TLN: \\begin{ex}...\\shortans{...}\\end{ex}\n"
                        "• TL: \\begin{bt}...\\end{bt}")
            else:
                hint = "Kiểm tra định dạng: mỗi câu bắt đầu bằng 'Câu X:' hoặc 'Câu X.'"
            messagebox.showwarning(
                "Không có câu hỏi",
                f"Không phân tích được câu hỏi từ file:\n{os.path.basename(filepath)}\n\n{hint}",
            )
            return

        fname = os.path.basename(filepath)
        missing_topic = sum(1 for q in questions if not q.topic)

        if self._get_ai:
            # Luôn hỏi người dùng có muốn dùng AI phân loại không
            msg = (
                f"Đã nhận dạng {len(questions)} câu hỏi từ {fname}.\n\n"
                "Bạn có muốn dùng AI tự động đọc nội dung để nhận diện\n"
                "MÔN HỌC, CHỦ ĐỀ và MỨC ĐỘ cho từng câu không?\n"
            )
            if missing_topic > 0:
                msg += f"\n⚠️ {missing_topic} câu chưa xác định được Chủ đề.\n"
            msg += "\n(Cần API Key đã cấu hình ở tab Cài đặt)"
            do_classify = messagebox.askyesno(
                "AI phân loại câu hỏi",
                msg,
                parent=self,
            )
            if do_classify:
                self._prog_lbl.config(text="🤖 AI đang phân loại Môn học & Chủ đề…")
                self._prog_bar["value"] = 65
                self.update_idletasks()
                self._run_ai_classify(questions, filepath)
                return

        # Lưu trực tiếp (không AI classify)
        self._save_parsed_questions(questions, filepath)

    def _run_ai_classify(self, questions: list, filepath: str) -> None:
        """Chạy AI phân loại chủ đề trong thread riêng."""
        import threading

        def _do_classify():
            try:
                from core.ai_classifier import classify_questions_batch
                ai_call = self._get_ai()

                def _on_prog(done, total):
                    pct = 65 + int(done / max(total, 1) * 25)
                    self.after(0, lambda p=pct, d=done, t=total:
                               (self._prog_bar.__setitem__("value", p),
                                self._prog_lbl.config(
                                    text=f"🤖 AI phân loại: {d}/{t} câu…")))

                classify_questions_batch(questions, ai_call, on_progress=_on_prog)
                self.after(0, lambda: self._save_parsed_questions(questions, filepath))
            except Exception as e:
                # Lưu chuỗi lỗi vào biến thường TRƯỚC khi except block kết thúc
                # (Python 3 tự xóa biến e sau except, lambda sẽ lỗi NameError nếu dùng e trực tiếp)
                err_msg = str(e)[:80]
                self.after(0, lambda msg=err_msg: self._on_classify_error(msg, questions, filepath))

        threading.Thread(target=_do_classify, daemon=True).start()

    def _on_classify_error(self, err_msg: str, questions: list, filepath: str) -> None:
        """Xử lý lỗi AI phân loại — hiển thị thông báo và lưu câu hỏi không phân loại."""
        self._prog_lbl.config(text=f"⚠️ AI phân loại lỗi — lưu câu hỏi không phân loại")
        messagebox.showwarning(
            "AI phân loại thất bại",
            f"Không thể phân loại câu hỏi bằng AI:\n{err_msg}\n\n"
            "Câu hỏi vẫn được lưu vào ngân hàng (không có phân loại AI).",
            parent=self,
        )
        self._save_parsed_questions(questions, filepath)

    def _save_parsed_questions(self, questions: list, filepath: str) -> None:
        """Hiển thị preview dialog rồi lưu câu hỏi đã parse vào NHCH."""
        import os
        from ui.dialog_nhch_preview import NHCHPreviewDialog

        # Môn học mặc định lấy từ giao diện nếu AI không nhận diện được
        default_subj = self._get_subj_grade()[0] if self._get_subj_grade else "Toán"
        grade = self._get_subj_grade()[1] if self._get_subj_grade else "12"

        # ── Gán ID có cấu trúc cho câu chưa có ID mới ──
        try:
            from core.models import assign_structured_ids
            need_id = [q for q in questions if q.question_id.startswith("QID-")]
            if need_id:
                assign_structured_ids(need_id, grade)
        except Exception:
            pass
        source_name = f"Upload: {os.path.basename(filepath)}"

        self._prog_bar["value"] = 90
        self._prog_lbl.config(text="Xem trước câu hỏi...")
        self.update_idletasks()

        # Holder cho dialog reference (đọc grade override sau khi user xác nhận)
        _holder: dict = {"dialog": None}

        def _do_save_after_preview(confirmed_questions):
            from storage.database import save_questions

            # Tự động chuyển đổi TikZ sang ảnh (EMF/PNG) trước khi lưu vào ngân hàng
            try:
                from services.tikz_vector_workflow import convert_questions_tikz_to_emf, count_pending_blocks
                if count_pending_blocks(confirmed_questions) > 0:
                    convert_questions_tikz_to_emf(confirmed_questions)
            except Exception as _tz_err:
                import logging
                logging.getLogger(__name__).warning("Lỗi tự động chuyển TikZ trước khi lưu NHCH: %s", _tz_err)

            # Đọc Lớp override từ dialog (nếu user đổi). Dùng cho cả nhóm.
            dlg = _holder.get("dialog")
            target_grade = getattr(dlg, "final_grade", None) or grade
            forced_subject = getattr(dlg, "final_subject", None)

            # Thuật toán phân nhóm câu hỏi theo môn học AI nhận diện —
            # NHƯNG nếu user đã set Môn override ở dialog → dùng forced_subject
            # cho TẤT CẢ câu (override AI classification).
            grouped_qs = {}
            for q in confirmed_questions:
                if forced_subject:
                    subj = forced_subject
                else:
                    subj = getattr(q, 'ai_subject', default_subj) or default_subj
                grouped_qs.setdefault(subj, []).append(q)

            # Lưu từng nhóm vào Database — dùng target_grade
            total_saved = 0
            for subj, qs in grouped_qs.items():
                saved = save_questions(qs, subj, target_grade, source=source_name)
                total_saved += saved

            # Thống kê phân loại
            classified = sum(1 for q in confirmed_questions if q.topic)
            subjects_found = len(grouped_qs.keys())
            cls_info = f" ({classified} câu đã phân loại thành {subjects_found} môn)" if classified else ""

            self._prog_bar["value"] = 100
            self._prog_lbl.config(text=f"✅ Đã nhập {total_saved}/{len(confirmed_questions)} câu.{cls_info}")
            self._prog_bar.pack_forget()
            self._search()
            self._refresh_stats()

            subjects_list = ", ".join(grouped_qs.keys())
            messagebox.showinfo(
                "Upload thành công",
                f"Đã nhập {total_saved} câu hỏi từ file vào ngân hàng.{cls_info}\n"
                f"Các môn học phát hiện được: {subjects_list}\n\n"
                "Bạn có thể tìm kiếm theo môn để kiểm tra lại các câu vừa thêm.",
            )

        # Mở preview dialog
        valid_qs = [q for q in questions if not q._error]
        if not valid_qs:
            self._prog_lbl.config(text="⚠️ Không có câu hỏi hợp lệ để lưu.")
            self._prog_bar.pack_forget()
            return

        def _on_preview_cancel():
            self._prog_lbl.config(text="Đã hủy upload.")
            self._prog_bar.pack_forget()

        dlg = NHCHPreviewDialog(
            self, valid_qs, default_subj, grade,
            on_confirm=_do_save_after_preview,
        )
        _holder["dialog"] = dlg  # closure trong _do_save_after_preview đọc lại
        dlg.protocol("WM_DELETE_WINDOW", lambda: (_on_preview_cancel(), dlg.destroy()))

    def _on_file_error(self, error: str) -> None:
        self._prog_lbl.config(text=f"❌ Lỗi: {error[:80]}")
        self._prog_bar.pack_forget()
        messagebox.showerror("Lỗi upload", f"Không thể đọc file:\n{error}")

    def _download_from_nhch(self) -> None:
        """Tải câu hỏi từ NHCH chung — có filter + preview trước khi nhập."""
        dlg = _NHCHDownloadDialog(self)
        self.wait_window(dlg)
        if dlg.result_saved > 0:
            self._search()
            self._refresh_stats()

    # ── Stats ─────────────────────────────────────────────────────────────────
    def _refresh_stats(self) -> None:
        try:
            s = db_stats()
            self._stats_lbl.config(
                text=f"Ngân hàng cục bộ: {s['total']} câu  │  "
                     + "  ".join(f"{k}:{v}" for k, v in s.get("by_type", {}).items()))
        except Exception:
            pass

    def refresh(self) -> None:
        self._refresh_stats()
        # Tự động load toàn bộ NHCH khi mở tab
        self._search()

    # ── Feature gating ──────────────────────────────────────────────────
    def apply_feature_gates(self, features: dict[str, bool]) -> None:
        """Bản mở khóa: luôn giữ các nút ở trạng thái hoạt động."""
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  Dialog Tải NHCH nâng cao — filter + preview + progress + thread
# ══════════════════════════════════════════════════════════════════════════════

class _NHCHDownloadDialog(tk.Toplevel):
    """
    Dialog tải câu hỏi từ NHCH chung:
      • Cho phép lọc Môn / Lớp / Loại / Mức độ / Giới hạn
      • Preview danh sách trước khi nhập
      • Thanh tiến độ % — chạy trên thread riêng, UI không bị đơ
    """

    def __init__(self, parent):
        super().__init__(parent)
        from ui import set_dialog_icon
        set_dialog_icon(self)
        self.title("📥  Tải từ Ngân hàng câu hỏi chung (NHCH)")
        self.geometry("820x620")
        self.minsize(700, 500)
        self.grab_set()
        self.configure(bg="#F9F7F4")
        self.result_saved = 0
        self._fetched: list[dict] = []
        self._conflict_summary = None
        self._fetch_cancel_event = None
        self._build()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # Header
        hdr = tk.Frame(self, bg="#0F2D52")
        hdr.pack(fill="x")
        tk.Label(hdr, text="📥  Tải từ Ngân hàng câu hỏi chung (Cloud)",
                 bg="#0F2D52", fg="white",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=14, pady=10)
        tk.Frame(self, bg="#10B981", height=3).pack(fill="x")

        # ── Bộ lọc ────────────────────────────────────────────────────────
        frm_f = ttk.LabelFrame(self, text="🔍  Bộ lọc tìm kiếm")
        frm_f.pack(fill="x", padx=10, pady=8)
        g = tk.Frame(frm_f); g.pack(fill="x", padx=10, pady=8)

        labels_vars = [
            ("Môn học:",  "flt_subject", 14, ""),
            ("Lớp:",      "flt_grade",    6, ""),
            ("Loại câu:", "flt_qtype",    8, ""),
            ("Mức độ:",   "flt_level",    8, ""),
        ]
        for col, (lbl, attr, w, val) in enumerate(labels_vars):
            tk.Label(g, text=lbl).grid(row=0, column=col*2,
                                        sticky="w", padx=0)
            var = tk.StringVar(value=val)
            setattr(self, attr, var)
            ttk.Entry(g, textvariable=var, width=w).grid(
                row=0, column=col*2+1, sticky="w", padx=8)

        tk.Label(g, text="Giới hạn:").grid(row=0, column=8, sticky="w", padx=0)
        self.flt_limit = tk.StringVar(value="200")
        ttk.Combobox(g, textvariable=self.flt_limit,
                     values=["50", "100", "200", "500", "1000"],
                     width=6, state="readonly").grid(
                         row=0, column=9, sticky="w", padx=8)

        self._fetch_btn = tk.Button(
            g, text="🔍  Tìm & Xem trước",
            bg="#1F497D", fg="white", activebackground="#163a66",
            relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"),
            padx=10, pady=4,
            command=self._start_fetch,
        )
        self._fetch_btn.grid(row=0, column=10, padx=6)

        # ── Progress ──────────────────────────────────────────────────────
        pf = tk.Frame(self); pf.pack(fill="x", padx=10, pady=4)
        self._dlg_prog_lbl = tk.Label(pf, text="", fg="#1F497D",
                                       font=("Segoe UI", 8))
        self._dlg_prog_lbl.pack(side="left", padx=4)
        self._dlg_prog = ttk.Progressbar(pf, mode="determinate",
                                          length=350, maximum=100)
        self._dlg_prog.pack(side="left", padx=4)
        self._dlg_prog.pack_forget()
        self._fetch_cancel_btn = tk.Button(
            pf, text="Hủy tải",
            bg="#EF4444", fg="white", activebackground="#DC2626",
            relief="flat", cursor="hand2", font=("Segoe UI", 8, "bold"),
            padx=8, pady=2,
            command=self._cancel_fetch,
        )
        self._fetch_cancel_btn.pack(side="left", padx=4)
        self._fetch_cancel_btn.pack_forget()

        # ── Preview tree ──────────────────────────────────────────────────
        frm_t = ttk.LabelFrame(self, text="📋  Danh sách câu hỏi (xem trước)")
        frm_t.pack(fill="both", expand=True, padx=10, pady=4)

        cols = ("✓", "QID", "Môn/Lớp", "Loại", "Mức", "Chủ đề", "Câu hỏi")
        self._ptree = ttk.Treeview(frm_t, columns=cols,
                                    show="headings", height=14,
                                    selectmode="extended")
        ws2 = {"✓": 44, "QID": 120, "Môn/Lớp": 72, "Loại": 50,
               "Mức": 42, "Chủ đề": 110, "Câu hỏi": 240}
        for c in cols:
            self._ptree.heading(c, text=c)
            self._ptree.column(c, width=ws2[c], minwidth=22)
        self._ptree.column("✓", anchor="center")

        vsb2 = ttk.Scrollbar(frm_t, orient="vertical",
                              command=self._ptree.yview)
        self._ptree.configure(yscrollcommand=vsb2.set)
        self._ptree.pack(side="left", fill="both", expand=True)
        vsb2.pack(side="right", fill="y")

        self._preview_checked: set = set()
        self._ptree.bind("<ButtonPress-1>", self._ptree_click)

        # Info bar
        self._info_lbl = tk.Label(self, text="Chưa tải — nhấn Tìm & Xem trước",
                                   fg="#888", font=("Segoe UI", 8))
        self._info_lbl.pack(anchor="w", padx=14)

        # ── Bottom toolbar ─────────────────────────────────────────────────
        bot = tk.Frame(self, bg="#E8EDF4")
        bot.pack(fill="x", pady=6, padx=10)

        tk.Button(bot, text="✅ Chọn tất cả",
                  bg="#3B82F6", fg="white", activebackground="#2563EB",
                  relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"),
                  command=self._preview_select_all).pack(side="left", padx=4, pady=4)
        tk.Button(bot, text="☐ Bỏ chọn tất cả",
                  bg="#64748B", fg="white", activebackground="#475569",
                  relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"),
                  command=self._preview_deselect_all).pack(side="left", padx=4)

        self._import_btn = tk.Button(
            bot,
            text="💾  Nhập vào ngân hàng cục bộ",
            bg="#059669", fg="white", activebackground="#047857",
            relief="flat", cursor="hand2",
            font=("Segoe UI", 9, "bold"), padx=12, pady=5,
            state="disabled",
            command=self._start_import,
        )
        self._import_btn.pack(side="right", padx=6)

        tk.Button(bot, text="✖  Đóng",
                  bg="#EF4444", fg="white", activebackground="#DC2626",
                  relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"),
                  command=self.destroy).pack(side="right", padx=4)

    # ── Fetch (threaded) ──────────────────────────────────────────────────────
    def _start_fetch(self) -> None:
        self._fetch_cancel_event = threading.Event()
        self._fetch_btn.config(state="disabled")
        self._import_btn.config(state="disabled")
        self._ptree.delete(*self._ptree.get_children())
        self._preview_checked.clear()
        self._fetched = []
        self._dlg_prog.pack(side="left", padx=4)
        self._dlg_prog["mode"] = "determinate"
        self._dlg_prog["value"] = 0
        self._fetch_cancel_btn.config(state="normal")
        self._fetch_cancel_btn.pack(side="left", padx=4)
        self._dlg_prog_lbl.config(text="Đang tải từ Cloud (Supabase)...")

        def _fetch():
            try:
                from services.cloud_workflow import download_questions_with_progress
                from services.license_manager import nhch_list
                subject = self.flt_subject.get().strip()
                grade   = self.flt_grade.get().strip()
                qtype   = self.flt_qtype.get().strip()
                level   = self.flt_level.get().strip()
                limit   = int(self.flt_limit.get() or 200)

                def _progress(event: dict) -> None:
                    self.after(0, lambda ev=event: self._update_fetch_progress(ev))

                result = download_questions_with_progress(
                    subject=subject,
                    grade=grade,
                    qtype=qtype,
                    level=level,
                    limit=limit,
                    page_size=50,
                    cancel_event=self._fetch_cancel_event,
                    progress_cb=_progress,
                    list_fn=nhch_list,
                )
                self.after(0, lambda res=result: self._on_fetch_result(res))
            except Exception as e:
                self.after(0, lambda err=str(e): self._on_fetch_error(err))

        threading.Thread(target=_fetch, daemon=True).start()

    def _update_fetch_progress(self, event: dict) -> None:
        pct = int(event.get("pct", 0) or 0)
        self._dlg_prog["value"] = max(0, min(100, pct))
        msg = event.get("message") or "Đang tải từ Cloud..."
        self._dlg_prog_lbl.config(text=msg)

    def _cancel_fetch(self) -> None:
        if self._fetch_cancel_event is not None:
            self._fetch_cancel_event.set()
        self._fetch_cancel_btn.config(state="disabled")
        self._dlg_prog_lbl.config(text="Đang hủy tải cloud...")

    def _finish_fetch_progress(self) -> None:
        try:
            self._dlg_prog.stop()
        except Exception:
            pass
        self._dlg_prog.pack_forget()
        self._fetch_cancel_btn.pack_forget()
        self._dlg_prog_lbl.config(text="")
        self._fetch_btn.config(state="normal")

    def _on_fetch_result(self, result) -> None:
        if getattr(result, "cancelled", False):
            self._finish_fetch_progress()
            self._info_lbl.config(text=result.message, fg="#CC4400")
            return
        if not getattr(result, "ok", False):
            self._on_fetch_error(getattr(result, "message", "Cloud download error"))
            return
        self._on_fetch_done(getattr(result, "questions", []))

    def _on_fetch_done(self, qs: list[dict]) -> None:
        self._finish_fetch_progress()
        self._fetch_btn.config(state="normal")
        self._fetched = qs

        if not qs:
            self._info_lbl.config(
                text="Không tìm thấy câu nào — thử thay đổi bộ lọc.", fg="#CC4400")
            return

        try:
            from services.cloud_workflow import summarize_cloud_import, format_conflict_summary

            self._conflict_summary = summarize_cloud_import(qs)
            summary_text = format_conflict_summary(self._conflict_summary)
        except Exception:
            self._conflict_summary = None
            summary_text = ""

        for q in qs:
            opts_raw = q.get("options_json") or q.get("options") or ""
            self._ptree.insert("", "end", values=(
                "☐",
                q.get("question_id", "")[:20],
                f"{q.get('subject','')} {q.get('grade','')}",
                q.get("qtype", ""),
                q.get("level", ""),
                (q.get("topic") or "")[:26],
                (q.get("question") or "")[:70],
            ))

        info = f"Tìm thấy {len(qs)} câu — tích ☑ những câu muốn nhập rồi bấm Nhập."
        if summary_text:
            info += f"  ({summary_text})"
        self._info_lbl.config(
            text=info,
            fg="#1F497D")
        self._import_btn.config(state="normal")

    def _on_fetch_error(self, err: str) -> None:
        self._finish_fetch_progress()
        self._info_lbl.config(text=f"❌ Lỗi: {err}", fg="#CC0000")

    # ── Preview checkbox ──────────────────────────────────────────────────────
    def _ptree_click(self, event) -> None:
        col = self._ptree.identify_column(event.x)
        iid = self._ptree.identify_row(event.y)
        if iid and col == "#1":
            if iid in self._preview_checked:
                self._preview_checked.discard(iid)
                self._ptree.set(iid, "✓", "☐")
            else:
                self._preview_checked.add(iid)
                self._ptree.set(iid, "✓", "☑")
                self._ptree.item(iid, tags=("checked",))
            return "break"

    def _preview_select_all(self) -> None:
        for iid in self._ptree.get_children():
            self._preview_checked.add(iid)
            self._ptree.set(iid, "✓", "☑")

    def _preview_deselect_all(self) -> None:
        for iid in self._ptree.get_children():
            self._preview_checked.discard(iid)
            self._ptree.set(iid, "✓", "☐")

    # ── Import (threaded) ─────────────────────────────────────────────────────
    def _start_import(self) -> None:
        all_iids = list(self._ptree.get_children())
        selected_iids = list(self._preview_checked) if self._preview_checked else all_iids
        if not selected_iids:
            messagebox.showinfo("Chưa có câu", "Không có câu nào để nhập.", parent=self)
            return

        iid_index = {iid: i for i, iid in enumerate(all_iids)}
        to_import = [self._fetched[iid_index[iid]]
                     for iid in selected_iids if iid in iid_index]

        if not messagebox.askyesno("Xác nhận nhập",
            f"Nhập {len(to_import)} câu vào ngân hàng cục bộ?", parent=self):
            return

        try:
            from services.cloud_workflow import (
                build_conflict_details,
                resolve_cloud_import,
            )

            details = build_conflict_details(to_import)
            decisions = {}
            if details:
                dlg = _CloudConflictResolverDialog(self, details)
                self.wait_window(dlg)
                if dlg.result is None:
                    return
                decisions = dlg.result

            resolved_import = resolve_cloud_import(
                to_import,
                decisions=decisions,
                default_conflict_action="copy",
            )
            to_import = resolved_import.questions
            self._last_import_note = resolved_import.message
            if not to_import:
                messagebox.showinfo(
                    "Khong co cau moi",
                    "Tat ca cau da co san hoac da duoc bo qua theo lua chon xu ly xung dot.",
                    parent=self,
                )
                return
        except Exception:
            self._last_import_note = ""

        self._import_btn.config(state="disabled")
        self._fetch_btn.config(state="disabled")
        self._dlg_prog["mode"] = "determinate"
        self._dlg_prog["maximum"] = 100
        self._dlg_prog["value"] = 0
        self._dlg_prog.pack(side="left", padx=4)
        self._dlg_prog_lbl.config(text="⏳ Đang nhập...")

        def _do_import():
            try:
                from storage.database import save_questions as _save_q
                converted = []
                total = len(to_import)
                for i, qd in enumerate(to_import, 1):
                    try:
                        opts = {}
                        raw_opts = qd.get("options") or qd.get("options_json") or "{}"
                        if isinstance(raw_opts, str):
                            opts = json.loads(raw_opts)
                        elif isinstance(raw_opts, dict):
                            opts = raw_opts
                        q = Question(
                            question_id = qd.get("question_id", ""),
                            qtype       = qd.get("qtype", "TN"),
                            level       = qd.get("level", "NB"),
                            topic       = qd.get("topic", ""),
                            question    = qd.get("question", ""),
                            options     = opts,
                            answer      = qd.get("answer", ""),
                            solution    = qd.get("solution", ""),
                        )
                        converted.append(q)
                    except Exception:
                        pass
                    pct = int(i / total * 100)
                    self.after(0, lambda p=pct, ci=i, ct=total:
                               self._dlg_update_prog(p, f"Nhập {ci}/{ct}..."))

                subj  = to_import[0].get("subject", "") if to_import else ""
                grade = to_import[0].get("grade", "") if to_import else ""
                saved = _save_q(converted, subj, grade, source="nhch_shared")
                self.after(0, lambda: self._on_import_done(saved, total))
            except Exception as e:
                self.after(0, lambda err=str(e): self._on_import_error(err))

        threading.Thread(target=_do_import, daemon=True).start()

    def _dlg_update_prog(self, pct: int, msg: str) -> None:
        self._dlg_prog["value"] = pct
        self._dlg_prog_lbl.config(text=msg)
        self.update_idletasks()

    def _on_import_done(self, saved: int, total: int) -> None:
        self._dlg_prog.pack_forget()
        self._dlg_prog_lbl.config(text="")
        self._import_btn.config(state="normal")
        self._fetch_btn.config(state="normal")
        self.result_saved = saved
        note = getattr(self, "_last_import_note", "")
        detail = f"\n\n{note}" if note else ""
        messagebox.showinfo("Nhập hoàn tất ✅",
            f"Đã nhập {saved}/{total} câu vào ngân hàng cục bộ.{detail}", parent=self)
        self.destroy()

    def _on_import_error(self, err: str) -> None:
        self._dlg_prog.pack_forget()
        self._dlg_prog_lbl.config(text="")
        self._import_btn.config(state="normal")
        self._fetch_btn.config(state="normal")
        messagebox.showerror("Lỗi nhập", err, parent=self)
