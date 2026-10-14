"""
Reusable expiry/date widgets for the desktop admin tool.
"""

from __future__ import annotations

import calendar as _calendar
from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import messagebox


DISPLAY_DATE_FORMAT = "%d-%m-%Y"
ISO_DATE_FORMAT = "%Y-%m-%d"

QUICK_EXPIRY_PRESETS: tuple[tuple[str, int | None], ...] = (
    ("Vĩnh viễn", None),
    ("7 ngày", 7),
    ("14 ngày", 14),
    ("30 ngày", 30),
    ("45 ngày", 45),
    ("90 ngày", 90),
    ("180 ngày", 180),
    ("365 ngày", 365),
)


def format_display_date(value: date | datetime) -> str:
    base = value.date() if isinstance(value, datetime) else value
    return base.strftime(DISPLAY_DATE_FORMAT)


def auto_format_display_date(raw: str) -> str:
    digits = "".join(ch for ch in raw if ch.isdigit())[:8]
    if not digits:
        return ""
    parts: list[str] = [digits[:2]]
    if len(digits) > 2:
        parts.append(digits[2:4])
    if len(digits) > 4:
        parts.append(digits[4:8])
    return "-".join(part for part in parts if part)


def compute_future_display(days: int, *, today: date | None = None) -> str:
    if days < 0:
        raise ValueError("days must be >= 0")
    anchor = today or date.today()
    return format_display_date(anchor + timedelta(days=days))


def display_to_iso(text: str) -> str:
    value = text.strip()
    if not value:
        return ""
    return datetime.strptime(value, DISPLAY_DATE_FORMAT).strftime(ISO_DATE_FORMAT)


def iso_to_display(text: str) -> str:
    value = text.strip()
    if not value or value in {"0", "Vĩnh viễn"}:
        return ""
    return datetime.strptime(value, ISO_DATE_FORMAT).strftime(DISPLAY_DATE_FORMAT)


def expiry_preview_text(text: str, *, today: date | None = None) -> tuple[str, str]:
    value = text.strip()
    if not value:
        return "♾️ Vĩnh viễn", "#10B981"

    current_day = today or date.today()
    try:
        exp_date = datetime.strptime(value, DISPLAY_DATE_FORMAT).date()
    except ValueError:
        return "⌨️ Nhập theo DD-MM-YYYY", "#9CA3AF"

    remaining = (exp_date - current_day).days
    if remaining < 0:
        return f"❌ Đã hết hạn {abs(remaining)} ngày trước", "#EF4444"
    if remaining == 0:
        return "⚠️ Hết hạn hôm nay", "#F59E0B"
    return f"📅 Còn {remaining} ngày ({exp_date.strftime('%d/%m/%Y')})", "#2563EB"


class CalendarPopup(tk.Toplevel):
    """Simple month picker without external dependencies."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        initial_date: date | None = None,
        on_select=None,
        anchor_widget: tk.Widget | None = None,
    ):
        super().__init__(parent)
        picked = initial_date or date.today()
        self._selected_date = picked
        self._view_year = picked.year
        self._view_month = picked.month
        self._on_select = on_select
        self._anchor_widget = anchor_widget or parent
        self.withdraw()
        self.overrideredirect(True)
        self.configure(bg="#CBDDD7")
        self.bind("<Escape>", lambda _e: self.destroy())
        self._build()
        self._position_near_anchor()
        self.deiconify()
        self.lift()
        self.focus_force()

    def _build(self) -> None:
        card = tk.Frame(self, bg="white", bd=0)
        card.pack(fill="both", expand=True, padx=1, pady=1)

        header = tk.Frame(card, bg="#0F4C5C")
        header.pack(fill="x")
        tk.Button(
            header,
            text="‹",
            command=lambda: self._shift_month(-1),
            bg="#0F4C5C",
            fg="white",
            bd=0,
            relief="flat",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            padx=10,
            pady=8,
        ).pack(side="left")
        self._title_var = tk.StringVar()
        tk.Label(
            header,
            textvariable=self._title_var,
            bg="#0F4C5C",
            fg="white",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left", expand=True)
        tk.Button(
            header,
            text="›",
            command=lambda: self._shift_month(1),
            bg="#0F4C5C",
            fg="white",
            bd=0,
            relief="flat",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            padx=10,
            pady=8,
        ).pack(side="right")

        self._days_frame = tk.Frame(card, bg="white")
        self._days_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self._render_days()

    def _position_near_anchor(self) -> None:
        self.update_idletasks()
        widget = self._anchor_widget
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() + widget.winfo_height() + 6
        screen_w = self.winfo_screenwidth()
        width = self.winfo_reqwidth()
        if x + width > screen_w - 12:
            x = max(12, screen_w - width - 12)
        self.geometry(f"+{x}+{y}")

    def _shift_month(self, delta: int) -> None:
        month = self._view_month + delta
        year = self._view_year
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1
        self._view_year = year
        self._view_month = month
        self._render_days()

    def _pick(self, picked: date) -> None:
        self._selected_date = picked
        if callable(self._on_select):
            self._on_select(picked)
        self.destroy()

    def _render_days(self) -> None:
        for child in self._days_frame.winfo_children():
            child.destroy()

        self._title_var.set(f"Tháng {self._view_month:02d}/{self._view_year}")
        weekdays = ("T2", "T3", "T4", "T5", "T6", "T7", "CN")
        for col, label in enumerate(weekdays):
            tk.Label(
                self._days_frame,
                text=label,
                bg="white",
                fg="#64748B",
                font=("Segoe UI", 9, "bold"),
                padx=8,
                pady=6,
            ).grid(row=0, column=col, sticky="nsew")
            self._days_frame.columnconfigure(col, weight=1)

        today = date.today()
        month_rows = _calendar.Calendar(firstweekday=0).monthdayscalendar(
            self._view_year,
            self._view_month,
        )
        for row_index, week in enumerate(month_rows, start=1):
            self._days_frame.rowconfigure(row_index, weight=1)
            for col, day_num in enumerate(week):
                if day_num == 0:
                    tk.Label(self._days_frame, text="", bg="white").grid(
                        row=row_index,
                        column=col,
                        sticky="nsew",
                        padx=2,
                        pady=2,
                    )
                    continue

                current = date(self._view_year, self._view_month, day_num)
                is_selected = current == self._selected_date
                is_today = current == today
                bg = "#0EA5A4" if is_selected else ("#EEF6FF" if is_today else "#F8FAFC")
                fg = "white" if is_selected else "#17313A"
                bd = 2 if is_today and not is_selected else 0
                tk.Button(
                    self._days_frame,
                    text=str(day_num),
                    command=lambda d=current: self._pick(d),
                    bg=bg,
                    fg=fg,
                    activebackground="#2563EB" if is_selected else "#DDEAF8",
                    activeforeground="white" if is_selected else "#17313A",
                    relief="solid",
                    bd=bd,
                    highlightthickness=0,
                    cursor="hand2",
                    font=("Segoe UI", 9, "bold" if is_today or is_selected else "normal"),
                    padx=8,
                    pady=7,
                ).grid(row=row_index, column=col, sticky="nsew", padx=2, pady=2)


class ExpiryEditor(tk.Frame):
    """Combined presets + custom days + date entry + calendar popup."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        bg: str = "#F9F7F4",
        initial_iso: str = "",
        day_default: int = 45,
        preview_note: str = "Để trống = Vĩnh viễn",
        quick_presets: tuple[tuple[str, int | None], ...] = QUICK_EXPIRY_PRESETS,
        **kw,
    ):
        super().__init__(parent, bg=bg, **kw)
        self._bg = bg
        self._display_var = tk.StringVar(value=iso_to_display(initial_iso))
        self._days_var = tk.StringVar(value=str(day_default))
        self._preview_note = preview_note
        self._quick_presets = quick_presets
        self._syncing = False
        self._calendar_popup: CalendarPopup | None = None
        self._preset_buttons: dict[str, tk.Button] = {}
        self._build()

    def _build(self) -> None:
        tk.Label(
            self,
            text="Gia hạn nhanh:",
            bg=self._bg,
            fg="#17313A",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        preset_row = tk.Frame(self, bg=self._bg)
        preset_row.pack(fill="x", pady=(4, 8))
        for label, days in self._quick_presets:
            btn = tk.Button(
                preset_row,
                text=label,
                font=("Segoe UI", 9, "bold" if days is None else "normal"),
                bg="#E2E8F0",
                fg="#334155",
                activebackground="#CBD5E1",
                relief="flat",
                cursor="hand2",
                padx=8,
                pady=4,
                command=lambda d=days: self.apply_days(d),
            )
            btn.pack(side="left", padx=(0, 4))
            self._preset_buttons[label] = btn

        custom_row = tk.Frame(self, bg=self._bg)
        custom_row.pack(fill="x", pady=(0, 8))
        tk.Label(custom_row, text="Tùy chỉnh số ngày:", bg=self._bg, font=("Segoe UI", 10)).pack(side="left")
        self._days_spin = tk.Spinbox(
            custom_row,
            from_=1,
            to=3650,
            textvariable=self._days_var,
            width=5,
            font=("Segoe UI", 10),
            justify="center",
        )
        self._days_spin.pack(side="left", padx=(8, 6), ipady=2)
        tk.Label(custom_row, text="ngày", bg=self._bg, font=("Segoe UI", 10)).pack(side="left")
        tk.Button(
            custom_row,
            text="Áp dụng",
            font=("Segoe UI", 9, "bold"),
            bg="#DDEAF8",
            fg="#1D4ED8",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.apply_custom_days,
        ).pack(side="left", padx=(8, 0))

        tk.Label(
            self,
            text="Ngày hết hạn:",
            bg=self._bg,
            fg="#17313A",
            font=("Segoe UI", 10),
        ).pack(anchor="w")

        date_row = tk.Frame(self, bg=self._bg)
        date_row.pack(anchor="w", pady=(4, 4))
        self._date_entry = tk.Entry(
            date_row,
            textvariable=self._display_var,
            font=("Consolas", 12),
            width=12,
            justify="center",
            relief="solid",
            bd=1,
        )
        self._date_entry.pack(side="left", ipady=4)
        tk.Button(
            date_row,
            text="📅",
            font=("Segoe UI", 10),
            bg="#E2E8F0",
            fg="#17313A",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=4,
            command=self.open_calendar,
        ).pack(side="left", padx=(6, 6))
        tk.Label(
            date_row,
            text="DD-MM-YYYY",
            bg=self._bg,
            fg="#9CA3AF",
            font=("Consolas", 10),
        ).pack(side="left")

        self._preview_lbl = tk.Label(
            self,
            text="",
            bg=self._bg,
            fg="#2563EB",
            font=("Segoe UI", 10, "bold"),
        )
        self._preview_lbl.pack(anchor="w", pady=(6, 0))
        tk.Label(
            self,
            text=self._preview_note,
            bg=self._bg,
            fg="#9CA3AF",
            font=("Segoe UI", 9, "italic"),
        ).pack(anchor="w", pady=(2, 0))

        self._display_var.trace_add("write", self._on_display_change)
        self._refresh_preview()

    def get_display_value(self) -> str:
        return self._display_var.get().strip()

    def get_iso_value(self) -> str:
        return display_to_iso(self.get_display_value())

    def set_iso_value(self, value: str) -> None:
        self._display_var.set(iso_to_display(value))

    def apply_days(self, days: int | None) -> None:
        if days is None:
            self._display_var.set("")
            return
        self._display_var.set(compute_future_display(days))

    def apply_custom_days(self) -> None:
        raw = self._days_var.get().strip()
        try:
            days = int(raw)
        except ValueError:
            messagebox.showwarning(
                "Sai số ngày",
                "Vui lòng nhập số ngày hợp lệ.",
                parent=self.winfo_toplevel(),
            )
            return
        if days <= 0:
            messagebox.showwarning(
                "Sai số ngày",
                "Số ngày phải lớn hơn 0.",
                parent=self.winfo_toplevel(),
            )
            return
        self.apply_days(days)

    def open_calendar(self) -> None:
        if self._calendar_popup is not None and self._calendar_popup.winfo_exists():
            self._calendar_popup.lift()
            return
        try:
            initial = datetime.strptime(self.get_display_value(), DISPLAY_DATE_FORMAT).date()
        except ValueError:
            initial = date.today()

        def _set_day(picked: date) -> None:
            self._calendar_popup = None
            self._display_var.set(format_display_date(picked))

        self._calendar_popup = CalendarPopup(
            self.winfo_toplevel(),
            initial_date=initial,
            on_select=_set_day,
            anchor_widget=self._date_entry,
        )

    def _on_display_change(self, *_args) -> None:
        if self._syncing:
            return
        current = self._display_var.get()
        formatted = auto_format_display_date(current)
        if formatted != current:
            self._syncing = True
            self._display_var.set(formatted)
            self._date_entry.icursor(len(formatted))
            self._syncing = False
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        text, color = expiry_preview_text(self.get_display_value())
        self._preview_lbl.config(text=text, fg=color)
