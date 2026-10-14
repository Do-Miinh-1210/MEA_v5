"""
admin/dialog_settings.py — Dialog thiết lập hệ thống (tính năng theo gói + bảng giá).
"""

from __future__ import annotations
import json
import tkinter as tk
from tkinter import ttk, messagebox

from config import get_default_features
from admin.constants import DEFAULT_PRICING_V2
from services.license_manager import admin_get_settings, admin_set_settings


class AdminSystemSettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("⚙️ Thiết lập Hệ thống & Bảng giá")
        self.geometry("1100x780")
        self.configure(bg="#F9F7F4")
        self.grab_set()
        self.focus_force()

        self.pricing_data = {}
        self.feature_data = {"basic": {}, "pro": {}, "premium": {}}
        self.feat_vars: dict[str, dict[str, tk.BooleanVar]] = {}

        self._load_data()
        self._build_ui()

    def _load_data(self):
        settings = admin_get_settings()
        try:
            raw = settings.get("pricing_v2")
            if raw:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                self.pricing_data = parsed if isinstance(parsed, dict) and parsed else DEFAULT_PRICING_V2
            else:
                self.pricing_data = DEFAULT_PRICING_V2
        except Exception:
            self.pricing_data = DEFAULT_PRICING_V2

        for tier in ["basic", "pro", "premium"]:
            try:
                feat_str = settings.get(f"features_{tier}")
                self.feature_data[tier] = json.loads(feat_str) if feat_str else get_default_features(tier)
            except Exception:
                self.feature_data[tier] = get_default_features(tier)

    def _build_ui(self):
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=("Segoe UI", 11, "bold"), padding=[20, 8])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=16)

        tab_features = tk.Frame(nb, bg="#F9F7F4")
        tab_pricing = tk.Frame(nb, bg="#F9F7F4")
        nb.add(tab_features, text="  🛠️ TÍNH NĂNG THEO GÓI  ")
        nb.add(tab_pricing,  text="  💰 QUẢN LÝ BẢNG GIÁ  ")

        self._build_tab_features(tab_features)
        self._build_tab_pricing(tab_pricing)

        bot = tk.Frame(self, bg="#E2E8F0", height=60); bot.pack(fill="x", side="bottom")
        tk.Button(bot, text="  💾 LƯU TOÀN BỘ THIẾT LẬP  ", font=("Segoe UI", 11, "bold"),
                  bg="#10B981", fg="white", activebackground="#059669", relief="flat", cursor="hand2",
                  padx=20, pady=10, command=self._save_all).pack(side="right", padx=16, pady=12)
        tk.Button(bot, text="  ✖ Hủy  ", font=("Segoe UI", 11),
                  bg="#64748B", fg="white", activebackground="#475569", relief="flat", cursor="hand2",
                  padx=16, pady=10, command=self.destroy).pack(side="right", padx=0, pady=12)

    def _build_tab_features(self, parent):
        tk.Label(parent, text="Click vào nút để Bật/Tắt tính năng mặc định cho từng gói:",
                 bg="#F9F7F4", fg="#1F497D", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(20, 10))

        tier_nb = ttk.Notebook(parent)
        tier_nb.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        all_features = [
            ("tab_matrix",  "📋 Quản lý Bảng câu hỏi"),
            ("tab_result",  "📄 Xem đề & Xuất file PDF/Word"),
            ("tab_bank",    "🏦 Truy cập Ngân hàng cục bộ"),
            ("tab_qc",      "✅ Sử dụng Tab Kiểm tra chất lượng"),
            ("tab_tikz",    "📐 TikZ vẽ hình toán học"),
            ("tab_convert", "🔄 Convert (Ảnh/PDF → Câu hỏi)"),
            ("quick_gen",   "⚡ Tính năng Tạo đề siêu tốc"),
            ("export_word", "📝 Cho phép xuất ra file Word"),
            ("nhch_cloud",  "☁️ Tải/Đồng bộ Ngân hàng Cloud"),
            ("ai_review",   "🤖 AI Review & Sửa lỗi tự động"),
            ("multi_code",  "🔀 Tính năng trộn Nhiều mã đề"),
        ]

        def _toggle_feature(var, btn):
            var.set(not var.get())
            if var.get():
                btn.config(text="  BẬT  ", bg="#10B981", fg="white")
            else:
                btn.config(text="  TẮT  ", bg="#E2E8F0", fg="#64748B")

        for tier, tier_name in [("basic", "🥉 BASIC"), ("pro", "🥈 PRO"), ("premium", "🏆 PREMIUM")]:
            f_frame = tk.Frame(tier_nb, bg="white", bd=1, relief="solid")
            tier_nb.add(f_frame, text=f"  {tier_name}  ")

            col1 = tk.Frame(f_frame, bg="white"); col1.pack(side="left", fill="both", expand=True, padx=40, pady=20)
            ttk.Separator(f_frame, orient="vertical").pack(side="left", fill="y", pady=20)
            col2 = tk.Frame(f_frame, bg="white"); col2.pack(side="left", fill="both", expand=True, padx=40, pady=20)

            self.feat_vars[tier] = {}
            for idx, (f_key, f_label) in enumerate(all_features):
                var = tk.BooleanVar(value=self.feature_data[tier].get(f_key, False))
                self.feat_vars[tier][f_key] = var
                target_col = col1 if idx < 6 else col2

                row = tk.Frame(target_col, bg="white"); row.pack(fill="x", pady=8)
                tk.Label(row, text=f_label, bg="white", font=("Segoe UI", 11)).pack(side="left")
                btn = tk.Label(row, text="  BẬT  " if var.get() else "  TẮT  ",
                               font=("Segoe UI", 10, "bold"), cursor="hand2",
                               bg="#10B981" if var.get() else "#E2E8F0",
                               fg="white" if var.get() else "#64748B",
                               padx=14, pady=6, borderwidth=0)
                btn.pack(side="right")
                btn.bind("<Button-1>", lambda e, v=var, b=btn: _toggle_feature(v, b))

    def _build_tab_pricing(self, parent):
        tk.Label(parent, text="Bảng giá 3 gói x 4 thời hạn — hiển thị ở Màn hình Kích hoạt:",
                 bg="#F9F7F4", fg="#1F497D", font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(20, 10))

        self._pricing_nb = ttk.Notebook(parent)
        self._pricing_nb.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        self._tier_trees: dict[str, ttk.Treeview] = {}
        _TIER_NAMES = {"basic": "🥉 BASIC", "pro": "🥈 PRO", "premium": "🏆 PREMIUM"}

        for tier_key in ["basic", "pro", "premium"]:
            tier_data = self.pricing_data.get(tier_key, {})
            tier_frame = tk.Frame(self._pricing_nb, bg="#F9F7F4")
            self._pricing_nb.add(tier_frame, text=f"  {_TIER_NAMES[tier_key]}  ")

            info_row = tk.Frame(tier_frame, bg="#F9F7F4"); info_row.pack(fill="x", padx=14, pady=(12, 6))
            tk.Label(info_row, text=f"Gói {tier_data.get('name', tier_key.upper())}",
                     bg="#F9F7F4", fg=tier_data.get("color", "#333"), font=("Segoe UI", 13, "bold")).pack(side="left")
            tk.Label(info_row, text=f"  —  {tier_data.get('desc', '')}",
                     bg="#F9F7F4", fg="#6B7280", font=("Segoe UI", 10)).pack(side="left")

            tree_frame = tk.Frame(tier_frame, bg="white", bd=1, relief="solid")
            tree_frame.pack(fill="both", expand=True, padx=14, pady=(0, 8))

            cols = ("duration", "price", "hot", "enabled")
            tv = ttk.Treeview(tree_frame, columns=cols, show="headings", height=5)
            tv.heading("duration", text="Thời hạn")
            tv.heading("price", text="Mức giá (VNĐ)")
            tv.heading("hot", text="Nổi bật")
            tv.heading("enabled", text="Trạng thái")
            tv.column("duration", width=160)
            tv.column("price", width=200)
            tv.column("hot", width=120, anchor="center")
            tv.column("enabled", width=120, anchor="center")
            tv.pack(fill="both", expand=True, side="left")

            scr = ttk.Scrollbar(tree_frame, orient="vertical", command=tv.yview)
            tv.configure(yscrollcommand=scr.set)
            scr.pack(side="right", fill="y")

            self._tier_trees[tier_key] = tv
            tv.bind("<ButtonRelease-1>", lambda e, t=tier_key: self._on_pricing_select(t))

        # Edit form
        form = tk.LabelFrame(parent, text=" Chỉnh sửa mức giá ", bg="#F9F7F4", font=("Segoe UI", 11, "bold"), fg="#1F497D")
        form.pack(fill="x", padx=16, pady=(0, 16))

        r1 = tk.Frame(form, bg="#F9F7F4"); r1.pack(fill="x", padx=14, pady=12)
        tk.Label(r1, text="Thời hạn:", bg="#F9F7F4", font=("Segoe UI", 10), width=10, anchor="e").pack(side="left")
        self.ent_period = ttk.Entry(r1, width=18, font=("Segoe UI", 11)); self.ent_period.pack(side="left", padx=8, ipady=3)
        tk.Label(r1, text="Giá tiền:", bg="#F9F7F4", font=("Segoe UI", 10), width=10, anchor="e").pack(side="left")
        self.ent_price = ttk.Entry(r1, width=18, font=("Segoe UI", 11)); self.ent_price.pack(side="left", padx=8, ipady=3)

        self.var_hot = tk.BooleanVar(value=False)
        self.lbl_hot = tk.Label(r1, text="⚪ HOT: TẮT", font=("Segoe UI", 10, "bold"), bg="#E2E8F0", fg="#64748B", cursor="hand2", padx=14, pady=6)
        self.lbl_hot.pack(side="left", padx=(20, 8))
        self.lbl_hot.bind("<Button-1>", self._toggle_hot)

        self.var_en = tk.BooleanVar(value=True)
        self.lbl_en = tk.Label(r1, text="✅ MỞ BÁN", font=("Segoe UI", 10, "bold"), bg="#10B981", fg="white", cursor="hand2", padx=14, pady=6)
        self.lbl_en.pack(side="left", padx=8)
        self.lbl_en.bind("<Button-1>", self._toggle_en)

        btn_row = tk.Frame(form, bg="#F9F7F4"); btn_row.pack(fill="x", padx=14, pady=(0, 14))
        tk.Button(btn_row, text=" ➕ THÊM ", font=("Segoe UI", 10, "bold"), bg="#3B82F6", fg="white", relief="flat", cursor="hand2", padx=12, pady=6, command=self._pricing_add).pack(side="left", padx=(84, 8))
        tk.Button(btn_row, text=" ✏️ CẬP NHẬT ", font=("Segoe UI", 10, "bold"), bg="#F59E0B", fg="white", relief="flat", cursor="hand2", padx=12, pady=6, command=self._pricing_update).pack(side="left", padx=8)
        tk.Button(btn_row, text=" 🗑️ XÓA ", font=("Segoe UI", 10, "bold"), bg="#EF4444", fg="white", relief="flat", cursor="hand2", padx=12, pady=6, command=self._pricing_delete).pack(side="left", padx=8)
        tk.Button(btn_row, text=" 🧹 DỌN ", font=("Segoe UI", 10, "bold"), bg="#94A3B8", fg="white", relief="flat", cursor="hand2", padx=12, pady=6, command=self._pricing_clear).pack(side="left", padx=8)

        self._refresh_pricing_tables()

    # ── Pricing helpers ──────────────────────────────────────────────────────

    def _get_active_tier(self) -> str:
        tab_names = ["basic", "pro", "premium"]
        idx = self._pricing_nb.index("current") if hasattr(self, "_pricing_nb") else 0
        return tab_names[idx] if idx < len(tab_names) else "basic"

    def _toggle_hot(self, event=None):
        self.var_hot.set(not self.var_hot.get())
        if self.var_hot.get(): self.lbl_hot.config(text="🔥 HOT: BẬT", bg="#F59E0B", fg="white")
        else: self.lbl_hot.config(text="⚪ HOT: TẮT", bg="#E2E8F0", fg="#64748B")

    def _toggle_en(self, event=None):
        self.var_en.set(not self.var_en.get())
        if self.var_en.get(): self.lbl_en.config(text="✅ MỞ BÁN", bg="#10B981", fg="white")
        else: self.lbl_en.config(text="❌ ĐÃ ẨN", bg="#EF4444", fg="white")

    def _refresh_pricing_tables(self):
        for tier_key, tv in self._tier_trees.items():
            tv.delete(*tv.get_children())
            tier_data = self.pricing_data.get(tier_key, {})
            for i, item in enumerate(tier_data.get("durations", [])):
                hot_text = "🔥 HOT" if item.get("hot") else ""
                en_text = "✅ Mở bán" if item.get("enabled", True) else "❌ Đã ẩn"
                tv.insert("", "end", iid=str(i), values=(item["duration"], item["price"], hot_text, en_text))

    def _on_pricing_select(self, tier_key):
        tv = self._tier_trees.get(tier_key)
        if not tv: return
        sel = tv.selection()
        if not sel: return
        idx = int(sel[0])
        durations = self.pricing_data.get(tier_key, {}).get("durations", [])
        if idx >= len(durations): return
        item = durations[idx]
        self._pricing_clear()
        self.ent_period.insert(0, item.get("duration", ""))
        self.ent_price.insert(0, item.get("price", ""))
        self.var_hot.set(item.get("hot", False))
        if self.var_hot.get(): self.lbl_hot.config(text="🔥 HOT: BẬT", bg="#F59E0B", fg="white")
        else: self.lbl_hot.config(text="⚪ HOT: TẮT", bg="#E2E8F0", fg="#64748B")
        self.var_en.set(item.get("enabled", True))
        if self.var_en.get(): self.lbl_en.config(text="✅ MỞ BÁN", bg="#10B981", fg="white")
        else: self.lbl_en.config(text="❌ ĐÃ ẨN", bg="#EF4444", fg="white")

    def _pricing_clear(self):
        self.ent_period.delete(0, 'end')
        self.ent_price.delete(0, 'end')
        self.var_hot.set(False)
        self.lbl_hot.config(text="⚪ HOT: TẮT", bg="#E2E8F0", fg="#64748B")
        self.var_en.set(True)
        self.lbl_en.config(text="✅ MỞ BÁN", bg="#10B981", fg="white")

    def _pricing_add(self):
        period = self.ent_period.get().strip()
        price = self.ent_price.get().strip()
        if not period or not price:
            messagebox.showwarning("Lỗi", "Vui lòng nhập Thời hạn và Giá tiền!", parent=self)
            return
        tier_key = self._get_active_tier()
        if tier_key not in self.pricing_data:
            self.pricing_data[tier_key] = {"name": tier_key.upper(), "color": "#64748B", "desc": "", "durations": []}
        self.pricing_data[tier_key]["durations"].append({
            "duration": period, "price": price, "hot": self.var_hot.get(), "enabled": self.var_en.get()
        })
        self._refresh_pricing_tables()
        self._pricing_clear()

    def _pricing_update(self):
        tier_key = self._get_active_tier()
        tv = self._tier_trees.get(tier_key)
        if not tv: return
        sel = tv.selection()
        if not sel: return
        idx = int(sel[0])
        durations = self.pricing_data.get(tier_key, {}).get("durations", [])
        if idx >= len(durations): return
        durations[idx] = {
            "duration": self.ent_period.get().strip(), "price": self.ent_price.get().strip(),
            "hot": self.var_hot.get(), "enabled": self.var_en.get()
        }
        self._refresh_pricing_tables()

    def _pricing_delete(self):
        tier_key = self._get_active_tier()
        tv = self._tier_trees.get(tier_key)
        if not tv: return
        sel = tv.selection()
        if not sel: return
        idx = int(sel[0])
        durations = self.pricing_data.get(tier_key, {}).get("durations", [])
        if idx < len(durations): del durations[idx]
        self._refresh_pricing_tables()
        self._pricing_clear()

    def _save_all(self):
        try:
            for tier in ["basic", "pro", "premium"]:
                updated_feats = {f_key: var.get() for f_key, var in self.feat_vars[tier].items()}
                admin_set_settings(f"features_{tier}", json.dumps(updated_feats, ensure_ascii=False))
            admin_set_settings("pricing_v2", json.dumps(self.pricing_data, ensure_ascii=False))
            messagebox.showinfo("Thành công", "Đã lưu thành công Thiết lập tính năng & Bảng giá lên hệ thống Cloud!", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu thiết lập:\n{e}", parent=self)
