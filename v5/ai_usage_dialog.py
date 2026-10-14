"""
v5/ai_usage_dialog.py -- CTk-native detailed AI usage statistics.

This ports the useful parts of V4's ``tab_ai_usage`` into V5 without depending
on the old Tkinter UI: range KPIs, provider/model breakdown, quota warnings,
recent request table, CSV export, open log folder and clear log.
"""
from __future__ import annotations

import os
import subprocess
import sys
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from v5.ai_cost import format_cost
from v5.ai_usage_summary import (
    export_usage_csv,
    filter_usage_entries,
    format_cost_label,
    format_duration_ms,
    format_number,
    quota_warnings,
    range_label,
    read_usage_entries,
    recent_usage_rows,
    summarize_usage,
    usage_log_path,
)
from v5.ui_constants import COLOR, FONT_SECONDARY, H_SECONDARY


_RANGE_LABEL_TO_KEY = {
    "Hôm nay": "today",
    "7 ngày": "7",
    "30 ngày": "30",
    "Tất cả": "all",
}

_LEVEL_ICON = {
    "ok": "✓",
    "warn": "!",
    "danger": "!!",
    "over": "X",
}


class AIUsageDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Thống kê sử dụng AI")
        self.geometry("1120x720")
        self.minsize(980, 620)
        try:
            self.transient(parent)
        except Exception:
            pass

        self._all_entries: list[dict] = []
        self._shown_entries: list[dict] = []
        self._range_var = ctk.StringVar(value="30 ngày")
        self._kpi_labels: dict[str, ctk.CTkLabel] = {}

        self._build()
        self.refresh()
        self.after(80, self.lift)

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkLabel(
            header,
            text="📊  Thống kê sử dụng AI",
            font=("Segoe UI", 22, "bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header,
            text="✕ Đóng",
            width=90,
            height=H_SECONDARY,
            fg_color=COLOR["neutral"],
            hover_color=COLOR["neutral_hover"],
            command=self.destroy,
        ).pack(side="right")

        toolbar = ctk.CTkFrame(self, fg_color=("white", "#1E293B"), corner_radius=10)
        toolbar.pack(fill="x", padx=18, pady=(0, 10))
        inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)

        ctk.CTkButton(
            inner,
            text="🔄 Làm mới",
            width=110,
            height=H_SECONDARY,
            font=FONT_SECONDARY,
            fg_color=COLOR["info"],
            hover_color=COLOR["info_hover"],
            command=self.refresh,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            inner,
            text="📤 Xuất CSV",
            width=110,
            height=H_SECONDARY,
            font=FONT_SECONDARY,
            fg_color=COLOR["primary"],
            hover_color=COLOR["primary_hover"],
            command=self._export_csv,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            inner,
            text="📁 Mở thư mục log",
            width=145,
            height=H_SECONDARY,
            font=FONT_SECONDARY,
            fg_color=COLOR["cyan"],
            hover_color=COLOR["cyan_hover"],
            command=self._open_log_dir,
        ).pack(side="left", padx=6)
        ctk.CTkButton(
            inner,
            text="🗑 Xoá log",
            width=105,
            height=H_SECONDARY,
            font=FONT_SECONDARY,
            fg_color=COLOR["danger"],
            hover_color=COLOR["danger_hover"],
            command=self._clear_log,
        ).pack(side="left", padx=6)

        ctk.CTkLabel(inner, text="Phạm vi:", font=("Segoe UI", 11, "bold")).pack(
            side="left", padx=(18, 6)
        )
        ctk.CTkSegmentedButton(
            inner,
            values=list(_RANGE_LABEL_TO_KEY),
            variable=self._range_var,
            command=lambda _value: self.refresh(),
        ).pack(side="left")

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", padx=18, pady=(0, 10))
        for i in range(5):
            cards.grid_columnconfigure(i, weight=1, uniform="usage")
        for i, (key, icon, label, color) in enumerate(
            (
                ("total", "📨", "Tổng request", "#3B82F6"),
                ("success", "✅", "Tỉ lệ thành công", "#10B981"),
                ("chars", "📝", "Tổng ký tự", "#7C3AED"),
                ("avg", "⏱", "Avg duration", "#F59E0B"),
                ("cost", "💵", "Ước tính cost", "#0EA5E9"),
            )
        ):
            self._make_kpi(cards, key, icon, label, color, i)

        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(fill="x", padx=18, pady=(0, 10))
        mid.grid_columnconfigure(0, weight=1, uniform="mid")
        mid.grid_columnconfigure(1, weight=1, uniform="mid")

        self._provider_box = self._make_text_panel(mid, "Theo provider / model", 0)
        self._quota_box = self._make_text_panel(mid, "Cảnh báo quota hôm nay", 1)

        table_frame = ctk.CTkFrame(self, fg_color=("white", "#1E293B"), corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        ctk.CTkLabel(
            table_frame,
            text="50 request gần nhất trong phạm vi đã chọn",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(anchor="w", padx=10, pady=(8, 4))

        wrap = ctk.CTkFrame(table_frame, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        cols = (
            "ts",
            "provider",
            "model",
            "kind",
            "ok",
            "prompt",
            "response",
            "tokens",
            "cost",
            "duration",
        )
        self._tree = ttk.Treeview(wrap, columns=cols, show="headings", height=12)
        labels = {
            "ts": "Thời gian",
            "provider": "Provider",
            "model": "Model",
            "kind": "Kind",
            "ok": "OK",
            "prompt": "Prompt",
            "response": "Response",
            "tokens": "Tokens",
            "cost": "Cost",
            "duration": "Time",
        }
        widths = {
            "ts": 145,
            "provider": 120,
            "model": 170,
            "kind": 130,
            "ok": 48,
            "prompt": 75,
            "response": 75,
            "tokens": 85,
            "cost": 80,
            "duration": 78,
        }
        for col in cols:
            self._tree.heading(col, text=labels[col])
            self._tree.column(
                col,
                width=widths[col],
                anchor=("w" if col in ("ts", "provider", "model", "kind") else "center"),
            )
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._tree, font_size=10)
        except Exception:
            pass

        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(wrap, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._status = ctk.CTkLabel(self, text="", text_color="gray", anchor="w")
        self._status.pack(fill="x", padx=20, pady=(0, 10))

    def _make_kpi(self, parent, key: str, icon: str, label: str, color: str, col: int) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=("white", "#293548"),
            corner_radius=10,
            border_width=1,
            border_color=("#E5E7EB", "#334155"),
        )
        card.grid(row=0, column=col, sticky="nsew", padx=5)
        ctk.CTkFrame(card, fg_color=color, height=5, corner_radius=10).pack(fill="x")
        ctk.CTkLabel(card, text=f"{icon} {label}", text_color="gray").pack(
            anchor="w", padx=12, pady=(10, 0)
        )
        value = ctk.CTkLabel(card, text="0", font=("Segoe UI", 20, "bold"))
        value.pack(anchor="w", padx=12, pady=(2, 10))
        self._kpi_labels[key] = value

    def _make_text_panel(self, parent, title: str, col: int) -> ctk.CTkTextbox:
        panel = ctk.CTkFrame(parent, fg_color=("white", "#1E293B"), corner_radius=10)
        panel.grid(row=0, column=col, sticky="nsew", padx=(0, 5) if col == 0 else (5, 0))
        ctk.CTkLabel(panel, text=title, font=("Segoe UI", 12, "bold")).pack(
            anchor="w", padx=10, pady=(8, 2)
        )
        box = ctk.CTkTextbox(panel, height=112, wrap="word")
        box.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        box.configure(state="disabled")
        return box

    def _selected_range(self) -> str:
        return _RANGE_LABEL_TO_KEY.get(self._range_var.get(), "30")

    def refresh(self) -> None:
        self._all_entries = read_usage_entries()
        range_key = self._selected_range()
        self._shown_entries = filter_usage_entries(self._all_entries, range_key)
        summary = summarize_usage(self._shown_entries)

        self._kpi_labels["total"].configure(text=f"{summary['total']:,}")
        self._kpi_labels["success"].configure(text=f"{summary['success_rate']}%")
        self._kpi_labels["chars"].configure(text=format_number(summary["total_chars"]))
        self._kpi_labels["avg"].configure(text=format_duration_ms(summary["avg_duration_ms"]))
        self._kpi_labels["cost"].configure(
            text=format_cost_label(summary["cost_usd"], estimated=summary["tokens_estimated"])
        )

        self._render_provider_text(summary)
        self._render_quota_text()
        self._render_table()

        path = usage_log_path()
        size_kb = path.stat().st_size / 1024 if path.exists() else 0.0
        estimated_note = " • * token/cost ước tính từ ký tự" if summary["tokens_estimated"] else ""
        self._status.configure(
            text=(
                f"Log: {path} • {size_kb:.1f} KB • "
                f"Phạm vi: {range_label(range_key)} • "
                f"Lỗi: {summary['errors']} / {summary['total']}{estimated_note}"
            )
        )

    def _render_provider_text(self, summary: dict) -> None:
        lines: list[str] = []
        if summary["total"]:
            for provider, count in summary["by_provider"].items():
                pct = count / summary["total"] * 100
                cost = summary["cost_by_provider"].get(provider, 0.0)
                lines.append(f"• {provider}: {count} request ({pct:.0f}%) • {format_cost(cost)}")
            if summary["by_model"]:
                lines.append("")
                lines.append("Theo model:")
                for model, count in list(summary["by_model"].items())[:8]:
                    lines.append(f"  - {model}: {count}")
            if summary["by_kind"]:
                lines.append("")
                lines.append("Theo tác vụ:")
                for kind, count in summary["by_kind"].items():
                    lines.append(f"  - {kind}: {count}")
        else:
            lines.append("(Chưa có request nào trong phạm vi này)")
        self._set_box_text(self._provider_box, "\n".join(lines))

    def _render_quota_text(self) -> None:
        today_entries = filter_usage_entries(self._all_entries, "today")
        if not today_entries:
            self._set_box_text(self._quota_box, "✓ Hôm nay chưa dùng AI")
            return
        statuses = quota_warnings(today_entries)
        if not statuses:
            self._set_box_text(self._quota_box, "(Chưa đủ dữ liệu quota)")
            return

        lines = []
        for item in statuses[:10]:
            level = str(item.get("level") or "ok")
            icon = _LEVEL_ICON.get(level, "?")
            model = str(item.get("model") or "")[:34]
            used = int(item.get("used_today", 0) or 0)
            limit = int(item.get("limit_today", 0) or 0)
            pct = float(item.get("percent", 0) or 0)
            lines.append(f"{icon} {model:<34} {used:>4} / {limit:<5} ({pct:>5.1f}%)")
        self._set_box_text(self._quota_box, "\n".join(lines))

    def _render_table(self) -> None:
        try:
            from v5.tree_style import zebra_tag
        except Exception:
            zebra_tag = lambda index: ""

        self._tree.delete(*self._tree.get_children())
        for index, row in enumerate(recent_usage_rows(self._shown_entries, limit=50)):
            token_note = "*" if row["tokens_estimated"] else ""
            self._tree.insert(
                "",
                "end",
                values=(
                    row["ts"][:19].replace("T", " "),
                    row["provider"],
                    row["model"][:28],
                    row["kind"],
                    "✓" if row["ok"] else "✗",
                    format_number(row["prompt_chars"]),
                    format_number(row["response_chars"]),
                    f"{format_number(row['total_tokens'])}{token_note}",
                    format_cost_label(row["cost_usd"], estimated=row["tokens_estimated"]),
                    format_duration_ms(row["duration_ms"]),
                ),
                tags=(zebra_tag(index),),
            )

    @staticmethod
    def _set_box_text(box: ctk.CTkTextbox, text: str) -> None:
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("end", text)
        box.configure(state="disabled")

    def _export_csv(self) -> None:
        if not self._shown_entries:
            messagebox.showinfo("Chưa có dữ liệu", "Không có log trong phạm vi này.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Xuất AI usage CSV",
            defaultextension=".csv",
            initialfile=f"ai_usage_{self._selected_range()}.csv",
            filetypes=[("CSV", "*.csv")],
        )
        if not path:
            return
        try:
            count = export_usage_csv(self._shown_entries, path)
            messagebox.showinfo("Đã xuất", f"Đã xuất {count} dòng:\n{path}", parent=self)
        except Exception as exc:
            messagebox.showerror("Lỗi xuất CSV", str(exc), parent=self)

    def _open_log_dir(self) -> None:
        from config import APP_DIR
        try:
            if sys.platform == "win32":
                os.startfile(str(APP_DIR))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(APP_DIR)])
            else:
                subprocess.Popen(["xdg-open", str(APP_DIR)])
        except Exception as exc:
            messagebox.showerror("Lỗi mở thư mục", str(exc), parent=self)

    def _clear_log(self) -> None:
        if not messagebox.askyesno(
            "Xác nhận xoá",
            "Xoá toàn bộ log AI usage?\nKhông thể khôi phục.",
            parent=self,
        ):
            return
        try:
            from services import ai_usage_log
            ok = ai_usage_log.clear_log()
        except Exception:
            ok = False
        if ok:
            self.refresh()
            messagebox.showinfo("Đã xoá", "Đã xoá log usage.", parent=self)
        else:
            messagebox.showerror("Lỗi", "Không xoá được log.", parent=self)
