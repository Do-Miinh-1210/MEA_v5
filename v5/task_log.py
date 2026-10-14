"""
v5/task_log.py — Dialog "Nhật ký tác vụ + Bộ nhớ đệm" (CTk-native).

Hai tab:
  • 📋  Nhật ký tác vụ — list ``services.task_events.list_task_events``
  • 💾  Cache AI — stats ``services.cache_service.CacheService.stats``,
    nút "Xoá toàn bộ".
"""
from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk


class TaskLogDialog(ctk.CTkToplevel):
    WIDTH = 860
    HEIGHT = 540

    def __init__(self, parent):
        super().__init__(parent)
        self.title("📋  Nhật ký tác vụ + Bộ nhớ đệm")
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

        self._build()
        self.bind("<Escape>", lambda e: self.destroy())

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=("#1F497D", "#0B1F35"),
                            corner_radius=0, height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🔧  Nhật ký + Bộ nhớ đệm",
                      text_color="white",
                      font=("Segoe UI", 14, "bold")
                      ).pack(side="left", padx=14, pady=10)

        self._tabs = ctk.CTkTabview(self)
        self._tabs.pack(fill="both", expand=True, padx=10, pady=8)
        self._tabs.add("📋  Nhật ký tác vụ")
        self._tabs.add("💾  Cache AI")

        self._build_tasks(self._tabs.tab("📋  Nhật ký tác vụ"))
        self._build_cache(self._tabs.tab("💾  Cache AI"))

        ctk.CTkButton(self, text="Đóng", width=100, height=30,
                        command=self.destroy
                        ).pack(pady=6)

    # ── Tab Task log ──────────────────────────────────────────────────
    def _build_tasks(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", pady=(4, 6))
        self._task_count_lbl = ctk.CTkLabel(bar,
            text="", font=("Segoe UI", 11, "bold"),
            text_color=("#1F497D", "#60A5FA"))
        self._task_count_lbl.pack(side="left", padx=4)
        ctk.CTkButton(bar, text="🔄 Refresh", width=90, height=28,
                       command=self._refresh_tasks
                       ).pack(side="right", padx=2)
        ctk.CTkButton(bar, text="📤 Xuất log", width=96, height=28,
                       fg_color=("#0EA5E9", "#0284C7"),
                       hover_color=("#0284C7", "#0369A1"),
                       command=self._export_tasks
                       ).pack(side="right", padx=2)
        ctk.CTkButton(bar, text="🗑 Xoá log", width=100, height=28,
                       fg_color="#DC2626", hover_color="#B91C1C",
                       command=self._clear_tasks
                       ).pack(side="right", padx=2)

        wrap = ctk.CTkFrame(parent, fg_color=("white", "#1E293B"))
        wrap.pack(fill="both", expand=True, pady=4)
        cols = ("time", "status", "kind", "title", "message")
        self._task_tree = ttk.Treeview(wrap, columns=cols, show="headings",
                                          height=14)
        for c, lab, w in [("time", "Thời gian", 130),
                            ("status", "Status", 80),
                            ("kind", "Loại", 110),
                            ("title", "Tiêu đề", 200),
                            ("message", "Mô tả", 280)]:
            self._task_tree.heading(c, text=lab)
            self._task_tree.column(c, width=w,
                                       anchor=("w" if c not in ("status",)
                                                else "center"))
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._task_tree)
        except Exception: pass
        # Alpha 21: HSB + grid layout
        vsb = ttk.Scrollbar(wrap, orient="vertical",
                              command=self._task_tree.yview)
        hsb = ttk.Scrollbar(wrap, orient="horizontal",
                              command=self._task_tree.xview)
        self._task_tree.configure(yscrollcommand=vsb.set,
                                     xscrollcommand=hsb.set)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        self._task_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Color tags
        self._task_tree.tag_configure("ok",    background="#D1FAE5")
        self._task_tree.tag_configure("err",   background="#FEE2E2")
        self._task_tree.tag_configure("info",  background="#DBEAFE")

        self._refresh_tasks()

    def _refresh_tasks(self):
        for item in self._task_tree.get_children():
            self._task_tree.delete(item)
        try:
            from services.task_events import list_task_events
            evts = list_task_events(limit=200) or []
        except Exception as e:
            self._task_count_lbl.configure(text=f"⚠ Lỗi: {e}")
            return

        self._task_count_lbl.configure(
            text=f"  {len(evts)} sự kiện gần nhất")

        for ev in evts:
            ts = (ev.created_at or "")[:19].replace("T", " ")
            status = ev.status or "info"
            tag = ("ok" if status == "success"
                    else "err" if status == "error"
                    else "info")
            self._task_tree.insert("", "end",
                values=(ts, status, ev.kind, ev.title, ev.message),
                tags=(tag,))

    def _clear_tasks(self):
        if not messagebox.askyesno("Xoá log",
            "Xoá toàn bộ nhật ký tác vụ?", parent=self):
            return
        try:
            from services.task_events import clear_task_events
            n = clear_task_events()
            messagebox.showinfo("Đã xoá",
                f"Đã xoá {n} sự kiện.", parent=self)
            self._refresh_tasks()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)

    def _export_tasks(self):
        try:
            from services.task_events import list_task_events
            evts = list_task_events(limit=5000) or []
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải nhật ký tác vụ: {e}", parent=self)
            return

        if not evts:
            messagebox.showinfo("Chưa có dữ liệu", "Không có sự kiện tác vụ nào để xuất.", parent=self)
            return

        from datetime import datetime
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Xuất nhật ký tác vụ",
            defaultextension=".txt",
            initialfile=f"task_log_{now_str}.txt",
            filetypes=[
                ("Văn bản (*.txt)", "*.txt"),
                ("CSV (*.csv)", "*.csv"),
                ("JSONL (*.jsonl)", "*.jsonl"),
                ("Tất cả tập tin (*.*)", "*.*"),
            ],
        )
        if not path:
            return

        try:
            p = Path(path)
            ext = p.suffix.lower()
            if ext == ".csv":
                import csv
                with open(p, "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Thời gian", "Status", "Loại", "Tiêu đề", "Mô tả", "Thời lượng (ms)"])
                    for ev in evts:
                        writer.writerow([
                            ev.created_at or "",
                            ev.status or "",
                            ev.kind or "",
                            ev.title or "",
                            ev.message or "",
                            ev.duration_ms if ev.duration_ms is not None else "",
                        ])
            elif ext == ".jsonl":
                import json
                with open(p, "w", encoding="utf-8") as f:
                    for ev in evts:
                        f.write(json.dumps(ev.to_dict(), ensure_ascii=False) + "\n")
            else:
                with open(p, "w", encoding="utf-8") as f:
                    f.write("=== NHẬT KÝ TÁC VỤ MEA V5 ===\n\n")
                    for ev in evts:
                        ts = (ev.created_at or "")[:19].replace("T", " ")
                        f.write(f"[{ts}] [{ev.status.upper()}] [{ev.kind}] {ev.title}\n")
                        if ev.message:
                            f.write(f"    Chi tiết: {ev.message}\n")
                        if ev.duration_ms is not None:
                            f.write(f"    Thời lượng: {ev.duration_ms} ms\n")
                        f.write("\n")
            messagebox.showinfo("Đã xuất", f"Đã xuất {len(evts)} sự kiện:\n{path}", parent=self)
        except Exception as exc:
            messagebox.showerror("Lỗi xuất log", str(exc), parent=self)

    # ── Tab Cache AI ──────────────────────────────────────────────────
    def _build_cache(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x", pady=(4, 6))
        ctk.CTkButton(bar, text="🔄 Refresh", width=90, height=28,
                       command=self._refresh_cache
                       ).pack(side="right", padx=2)
        ctk.CTkButton(bar, text="🗑 Xoá cache", width=110, height=28,
                       fg_color="#DC2626", hover_color="#B91C1C",
                       command=self._clear_cache
                       ).pack(side="right", padx=2)

        self._cache_box = ctk.CTkFrame(parent,
                                          fg_color=("#F3F4F6", "#0F172A"),
                                          corner_radius=8)
        self._cache_box.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(parent,
                      text="Cache lưu kết quả AI để câu hỏi lặp không gọi lại.\n"
                           "Xoá khi: đổi model · debug · giảm dung lượng đĩa.",
                      font=("Segoe UI", 10),
                      text_color="gray",
                      justify="left").pack(anchor="w", padx=10, pady=4)

        self._refresh_cache()

    def _refresh_cache(self):
        for w in self._cache_box.winfo_children():
            try: w.destroy()
            except Exception: pass
        try:
            from services.cache_service import CacheService
            stats = CacheService().stats() or {}
        except Exception as e:
            ctk.CTkLabel(self._cache_box,
                          text=f"⚠ Lỗi đọc cache: {e}",
                          text_color=("#DC2626", "#F87171")
                          ).pack(pady=12, padx=10)
            return

        rows = [
            ("RAM entries",     stats.get("memory_entries", 0)),
            ("RAM size (KB)",   stats.get("memory_size_kb", 0)),
            ("File entries",    stats.get("file_entries", 0)),
            ("Tổng dung lượng (KB)", stats.get("total_size_kb", 0)),
        ]
        for label, val in rows:
            row = ctk.CTkFrame(self._cache_box, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(row, text=label, anchor="w",
                          font=("Segoe UI", 11),
                          text_color=("#374151", "#E5E7EB"), width=220
                          ).pack(side="left")
            ctk.CTkLabel(row, text=f"{val:,}" if isinstance(val, int)
                                                 else f"{val}",
                          font=("Consolas", 11, "bold"),
                          text_color=("#1F497D", "#60A5FA"), width=120,
                          anchor="e"
                          ).pack(side="right")

    def _clear_cache(self):
        if not messagebox.askyesno("Xoá cache",
            "Xoá toàn bộ cache AI?\n"
            "(Câu hỏi lặp sẽ phải gọi lại API)", parent=self):
            return
        try:
            from services.cache_service import CacheService
            n = CacheService().clear_all()
            messagebox.showinfo("Đã xoá", f"Đã xoá {n} entries.",
                                  parent=self)
            self._refresh_cache()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)
