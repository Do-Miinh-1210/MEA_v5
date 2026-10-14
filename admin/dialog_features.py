"""
admin/dialog_features.py — Dialog ghi đè tính năng cá nhân cho 1 user.
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox

from config import FEATURE_CATALOG, get_default_features
from services.license_manager import admin_set_features


class FeatureDialog(tk.Toplevel):
    def __init__(self, parent, mid: str, record: dict):
        super().__init__(parent)
        self.title(f"Quản lý tính năng cá nhân — {mid}")
        self.configure(bg="#F9F7F4")
        self.geometry("650x550")
        self.grab_set()
        self._saved = False
        self._mid = mid
        self._tier = str(record.get("tier", "basic")).lower()
        raw_feat = record.get("features", {})
        self._custom = raw_feat if isinstance(raw_feat, dict) else {}
        self._defaults = get_default_features(self._tier)
        self._build()

    def _build(self):
        tk.Label(self, text=f"⚙️ Ghi đè tính năng riêng cho máy: {self._mid}",
                 bg="#0F2D52", fg="white", font=("Segoe UI", 12, "bold")).pack(fill="x")

        canvas = tk.Canvas(self, bg="#F9F7F4", highlightthickness=0)
        scr = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        feat_frame = tk.Frame(canvas, bg="#F9F7F4")

        canvas.configure(yscrollcommand=scr.set)
        scr.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=16, pady=8)
        canvas.create_window((0, 0), window=feat_frame, anchor="nw")
        feat_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self._vars: dict[str, tk.IntVar] = {}
        self._toggle_btns: dict[str, list[tk.Label]] = {}
        _STYLES = {
            0:  {"bg": "#64748B", "t": "Theo gói"},
            1:  {"bg": "#059669", "t": " BẬT "},
            -1: {"bg": "#DC2626", "t": " TẮT "},
        }

        for i, (key, info) in enumerate(FEATURE_CATALOG.items(), start=1):
            val = 1 if self._custom.get(key) is True else (-1 if self._custom.get(key) is False else 0)
            var = tk.IntVar(value=val)
            self._vars[key] = var

            tk.Label(feat_frame,
                     text=f" {info['label']} (Mặc định: {'Bật' if self._defaults.get(key) else 'Tắt'})",
                     bg="#F9F7F4", font=("Segoe UI", 9)).grid(row=i, column=0, sticky="w", pady=4, padx=(0, 20))
            btns = []
            for ci, v in enumerate([0, 1, -1], start=1):
                btn = tk.Label(feat_frame, text=_STYLES[v]["t"], font=("Segoe UI", 9, "bold"),
                               bg=_STYLES[v]["bg"] if var.get() == v else "#E2E8F0",
                               fg="white" if var.get() == v else "#94A3B8",
                               cursor="hand2", padx=8, pady=5)
                btn.bind("<Button-1>", lambda e, k=key, val=v: self._on_toggle(k, val))
                btn.grid(row=i, column=ci, padx=2, pady=2)
                btns.append(btn)
            self._toggle_btns[key] = btns

        btn_f = tk.Frame(self, bg="#F9F7F4")
        btn_f.pack(fill="x", padx=16, pady=10)
        tk.Button(btn_f, text=" Hủy ", bg="#E5E7EB", command=self.destroy).pack(side="right", padx=4)
        tk.Button(btn_f, text=" Lưu ghi đè ", bg="#10B981", fg="white",
                  font=("Segoe UI", 9, "bold"), command=self._save).pack(side="right", padx=4)

    def _on_toggle(self, key, val):
        self._vars[key].set(val)
        _STYLES = {0: "#64748B", 1: "#059669", -1: "#DC2626"}
        for v, btn in zip([0, 1, -1], self._toggle_btns[key]):
            btn.configure(
                bg=_STYLES[v] if self._vars[key].get() == v else "#E2E8F0",
                fg="white" if self._vars[key].get() == v else "#94A3B8",
            )

    def _save(self):
        features = {
            key: (True if var.get() == 1 else False)
            for key, var in self._vars.items() if var.get() != 0
        }
        if admin_set_features(self._mid, features).get("ok"):
            self._saved = True
            messagebox.showinfo("Thành công", "Đã lưu tính năng cá nhân!", parent=self)
            self.destroy()
