"""
v5/nhch_stats.py — Dialog "Thống kê ngân hàng câu hỏi" (CTk port).

Hiển thị tổng số câu + phân bố theo môn/lớp/loại/mức. Đọc từ
``storage.database.db_stats()``.
"""
from __future__ import annotations

import customtkinter as ctk


class NHCHStatsDialog(ctk.CTkToplevel):
    WIDTH = 540
    HEIGHT = 560

    def __init__(self, parent):
        super().__init__(parent)
        self.title("📊  Thống kê ngân hàng câu hỏi")

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
        # Header
        hdr = ctk.CTkFrame(self, fg_color=("#10B981", "#047857"),
                            corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="📊  Thống kê ngân hàng câu hỏi",
                      text_color="white",
                      font=("Segoe UI", 16, "bold"),
                      anchor="w").pack(side="left", padx=16, pady=10)

        try:
            from storage.database import db_stats
            s = db_stats() or {}
        except Exception as e:
            ctk.CTkLabel(self,
                          text=f"⚠ Không đọc được DB: {e}",
                          font=("Segoe UI", 11),
                          text_color=("#DC2626", "#F87171")
                          ).pack(pady=40, padx=20)
            self._add_close_btn()
            return

        total = s.get("total", 0)
        # Big number total
        total_box = ctk.CTkFrame(self, fg_color=("#DCFCE7", "#064E3B"),
                                    corner_radius=10)
        total_box.pack(fill="x", padx=16, pady=(16, 12))
        ctk.CTkLabel(total_box, text="Tổng số câu trong NHCH",
                      font=("Segoe UI", 11),
                      text_color=("#065F46", "#A7F3D0")
                      ).pack(pady=(10, 0))
        ctk.CTkLabel(total_box, text=f"{total:,}",
                      font=("Segoe UI", 36, "bold"),
                      text_color=("#047857", "#34D399")
                      ).pack(pady=(0, 10))

        # 3 panels grid (theo môn/lớp · loại · mức)
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self._render_section(body, "📚  Theo môn / lớp",
                              s.get("by_subject", {}) or {})
        self._render_section(body, "📝  Theo loại câu hỏi",
                              s.get("by_type", {}) or {},
                              labels={"TN": "Trắc nghiệm",
                                      "DS": "Đúng/Sai",
                                      "TLN": "Trả lời ngắn",
                                      "TL": "Tự luận"})
        self._render_section(body, "🎯  Theo mức độ",
                              s.get("by_level", {}) or {},
                              labels={"NB": "Nhận biết",
                                      "TH": "Thông hiểu",
                                      "VD": "Vận dụng"})

        self._add_close_btn()

    def _render_section(self, parent, title: str, data: dict,
                          labels: dict | None = None):
        if not data:
            return
        card = ctk.CTkFrame(parent, fg_color=("white", "#1E293B"),
                              corner_radius=8, border_width=1,
                              border_color=("#E5E7EB", "#334155"))
        card.pack(fill="x", pady=4)
        ctk.CTkLabel(card, text=title,
                      font=("Segoe UI", 12, "bold"),
                      anchor="w"
                      ).pack(anchor="w", padx=12, pady=(8, 4))

        total = sum(data.values()) or 1
        # Sort desc
        for key, count in sorted(data.items(), key=lambda x: -x[1]):
            label = (labels.get(key, key) if labels else key) or "(rỗng)"
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(row, text=f"  • {label}", anchor="w",
                          font=("Segoe UI", 11),
                          text_color=("#374151", "#E5E7EB"), width=200
                          ).pack(side="left")
            pct = (count / total) * 100
            ctk.CTkLabel(row,
                          text=f"{count:>5,}  ({pct:5.1f}%)",
                          font=("Consolas", 11, "bold"),
                          text_color=("#1F497D", "#60A5FA"), width=120,
                          anchor="e"
                          ).pack(side="right")
        # Bottom spacer
        ctk.CTkFrame(card, fg_color="transparent", height=6).pack()

    def _add_close_btn(self):
        ctk.CTkButton(self, text="Đóng", width=100, height=32,
                        command=self.destroy
                        ).pack(pady=10)
