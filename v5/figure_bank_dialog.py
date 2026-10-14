"""CTk dialogs for saving and browsing the TikZ figure bank.

This ports the V4 ``ui.tab_tikz`` Figure Bank workflow without depending on
the old Tk UI layer. Storage stays in ``services.figure_bank``.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from tkinter import messagebox, ttk


_SOURCE_OPTIONS = {
    "Tất cả": "",
    "AI": "ai",
    "Thủ công": "manual",
    "Mẫu": "template",
    "Import": "imported",
    "NHCH tự động": "nhch",
    "Render tự động": "rendered",
}


def _parse_tags(raw: str) -> list[str]:
    """Split comma-separated tags into unique, non-empty labels."""
    tags: list[str] = []
    seen: set[str] = set()
    for part in (raw or "").split(","):
        tag = part.strip()
        key = tag.casefold()
        if tag and key not in seen:
            tags.append(tag)
            seen.add(key)
    return tags


def _source_label(source: str) -> str:
    return {
        "ai": "AI",
        "manual": "Thủ công",
        "template": "Mẫu",
        "imported": "Import",
        "nhch": "NHCH tự động",
        "rendered": "Render tự động",
    }.get(source or "", source or "manual")


def _open_folder(path: str) -> None:
    if not path:
        return
    if sys.platform == "win32":
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


class SaveFigureDialog(ctk.CTkToplevel):
    """Collect metadata before saving current TikZ code to the figure bank."""

    def __init__(self, parent, *, has_rendered_image: bool = False):
        super().__init__(parent)
        self.title("Lưu hình vào kho")
        self.geometry("560x500")
        self.minsize(540, 480)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.confirmed = False
        self.result_title = ""
        self.result_desc = ""
        self.result_tags: list[str] = []
        self.save_png = False
        self._has_rendered_image = bool(has_rendered_image)

        self._build()
        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Control-Return>", lambda _e: self._confirm())
        try:
            self._title_var.set("Hình TikZ")
            self._title_entry.focus_set()
        except Exception:
            pass

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=("#DBEAFE", "#1E3A8A"),
                              corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="💾  Lưu hình vào kho NHCH",
            font=("Segoe UI", 18, "bold"),
            text_color=("#1E40AF", "#BFDBFE"),
        ).pack(anchor="w", padx=18, pady=14)

        footer = ctk.CTkFrame(self, fg_color=("#E2E8F0", "#111827"),
                              corner_radius=0, height=64)
        footer.pack(fill="x", side="bottom")
        buttons = ctk.CTkFrame(footer, fg_color="transparent")
        buttons.pack(fill="x", padx=18, pady=12)
        ctk.CTkButton(
            buttons, text="💾 Lưu hình", width=130,
            fg_color=("#10B981", "#047857"),
            hover_color=("#059669", "#065F46"),
            command=self._confirm,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            buttons, text="Huỷ", width=100,
            fg_color=("#6B7280", "#374151"),
            command=self.destroy,
        ).pack(side="right")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=14)

        self._title_var = ctk.StringVar()
        ctk.CTkLabel(body, text="Tên hình *",
                     font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self._title_entry = ctk.CTkEntry(body, textvariable=self._title_var)
        self._title_entry.pack(fill="x", pady=(3, 10))

        ctk.CTkLabel(body, text="Mô tả ngắn",
                     font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self._desc_box = ctk.CTkTextbox(body, height=86, wrap="word")
        self._desc_box.pack(fill="x", pady=(3, 10))

        self._tags_var = ctk.StringVar()
        ctk.CTkLabel(body, text="Tags (cách nhau bằng dấu phẩy)",
                     font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ctk.CTkEntry(
            body,
            textvariable=self._tags_var,
            placeholder_text="vd: 2D, tam giác, parabol",
        ).pack(fill="x", pady=(3, 12))

        self._save_png_var = ctk.BooleanVar(value=self._has_rendered_image)
        ctk.CTkCheckBox(
            body,
            text=("Lưu kèm ảnh PNG đã render" if self._has_rendered_image
                  else "Lưu kèm ảnh PNG (cần render preview trước)"),
            variable=self._save_png_var,
            state=("normal" if self._has_rendered_image else "disabled"),
        ).pack(anchor="w")

    def _confirm(self):
        title = self._title_var.get().strip()
        if not title:
            messagebox.showwarning("Thiếu tên", "Hãy nhập tên cho hình.",
                                   parent=self)
            return
        self.result_title = title
        self.result_desc = self._desc_box.get("1.0", "end").strip()
        self.result_tags = _parse_tags(self._tags_var.get())
        self.save_png = bool(self._save_png_var.get()) and self._has_rendered_image
        self.confirmed = True
        self.destroy()


class FigureBankDialog(ctk.CTkToplevel):
    """Browse/search/edit the saved figure bank and load code into an editor."""

    def __init__(
        self,
        parent,
        *,
        on_load: Callable[[str, str], None] | None = None,
    ):
        super().__init__(parent)
        self.title("Kho NHCH hình vẽ")
        self.geometry("1280x760")
        self.minsize(1040, 600)
        self.transient(parent)
        self.grab_set()

        self._on_load_cb = on_load
        self._selected_id = ""
        self._preview_image_ref = None
        self._build()
        self._refresh()
        self.bind("<Escape>", lambda _e: self.destroy())

    def _build(self):
        header = ctk.CTkFrame(self, fg_color=("#ECFDF5", "#064E3B"),
                              corner_radius=0)
        header.pack(fill="x")
        ctk.CTkLabel(
            header, text="🗂  Kho NHCH hình vẽ",
            font=("Segoe UI", 19, "bold"),
            text_color=("#065F46", "#A7F3D0"),
        ).pack(side="left", padx=18, pady=14)
        self._stats_lbl = ctk.CTkLabel(header, text="", font=("Segoe UI", 11),
                                       text_color=("#047857", "#D1FAE5"))
        self._stats_lbl.pack(side="right", padx=18)

        filters = ctk.CTkFrame(self, fg_color="transparent")
        filters.pack(fill="x", padx=16, pady=(12, 8))
        self._query_var = ctk.StringVar()
        ctk.CTkEntry(
            filters,
            textvariable=self._query_var,
            placeholder_text="Tìm theo tên, mô tả hoặc tag...",
            width=390,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._source_var = ctk.StringVar(value="Tất cả")
        ctk.CTkOptionMenu(
            filters,
            values=list(_SOURCE_OPTIONS),
            variable=self._source_var,
            width=140,
            command=lambda _value: self._refresh(),
        ).pack(side="left")
        self._query_var.trace_add("write", lambda *_: self._refresh())

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=7)
        body.grid_columnconfigure(1, weight=4)

        list_card = ctk.CTkFrame(body, fg_color=("white", "#1E293B"),
                                 corner_radius=8)
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        list_card.grid_rowconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=0)
        list_card.grid_columnconfigure(0, weight=1)

        columns = ("id", "title", "source", "tags", "png", "created")
        self._tree = ttk.Treeview(
            list_card, columns=columns, show="headings", selectmode="browse"
        )
        labels = {
            "id": "ID", "title": "Tên hình", "source": "Nguồn",
            "tags": "Tags", "png": "PNG", "created": "Ngày",
        }
        widths = {
            "id": 68, "title": 260, "source": 132,
            "tags": 215, "png": 64, "created": 112,
        }
        for col in columns:
            self._tree.heading(col, text=labels[col])
            self._tree.column(
                col,
                width=widths[col],
                minwidth=widths[col],
                anchor=("w" if col in {"title", "source", "tags"} else "center"),
                stretch=col in {"title", "tags"},
            )
        try:
            from v5.tree_style import style_treeview
            style_treeview(self._tree)
        except Exception:
            pass
        vsb = ttk.Scrollbar(list_card, orient="vertical",
                            command=self._tree.yview)
        hsb = ttk.Scrollbar(list_card, orient="horizontal",
                            command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>", lambda _e: self._load_selected())

        preview_card = ctk.CTkFrame(body, fg_color=("white", "#1E293B"),
                                    corner_radius=8)
        preview_card.grid(row=0, column=1, sticky="nsew")
        preview_card.grid_rowconfigure(2, weight=0)
        preview_card.grid_rowconfigure(4, weight=1)
        preview_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(preview_card, text="Xem trước",
                     font=("Segoe UI", 13, "bold")).grid(
                         row=0, column=0, sticky="w", padx=12, pady=(12, 2))
        self._meta_lbl = ctk.CTkLabel(preview_card, text="Chưa chọn hình",
                                      text_color="gray", anchor="w")
        self._meta_lbl.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        self._image_panel = ctk.CTkFrame(
            preview_card,
            fg_color=("#F8FAFC", "#0F172A"),
            corner_radius=8,
            border_width=1,
            border_color=("#E2E8F0", "#334155"),
            height=230,
        )
        self._image_panel.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        self._image_panel.grid_propagate(False)
        self._image_panel.grid_rowconfigure(0, weight=1)
        self._image_panel.grid_columnconfigure(0, weight=1)
        self._image_lbl = ctk.CTkLabel(
            self._image_panel,
            text="Chưa có ảnh render PNG.\nRender và lưu hình để xem ảnh tại đây.",
            text_color=("#64748B", "#CBD5E1"),
            compound="top",
        )
        self._image_lbl.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        ctk.CTkLabel(
            preview_card,
            text="Code TikZ",
            font=("Segoe UI", 12, "bold"),
            text_color=("#334155", "#CBD5E1"),
        ).grid(row=3, column=0, sticky="w", padx=12, pady=(0, 4))
        self._preview = ctk.CTkTextbox(
            preview_card,
            font=("Consolas", 10),
            fg_color=("#F8FAFC", "#0F172A"),
            wrap="none",
        )
        self._preview.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self._preview.configure(state="disabled")

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkButton(
            actions, text="✅ Nạp vào editor", width=145,
            fg_color=("#10B981", "#047857"),
            hover_color=("#059669", "#065F46"),
            command=self._load_selected,
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(actions, text="📋 Copy code", width=120,
                      command=self._copy_selected).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="✏️ Sửa metadata", width=135,
                      fg_color=("#7C3AED", "#5B21B6"),
                      hover_color=("#6D28D9", "#4C1D95"),
                      command=self._edit_selected).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="🗑 Xoá", width=90,
                      fg_color=("#EF4444", "#7F1D1D"),
                      hover_color=("#DC2626", "#991B1B"),
                      command=self._delete_selected).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="📁 Thư mục", width=105,
                      fg_color=("#0891B2", "#0E7490"),
                      hover_color=("#0E7490", "#155E75"),
                      command=self._open_bank_folder).pack(side="right", padx=2)
        ctk.CTkButton(actions, text="Đóng", width=90,
                      fg_color=("#6B7280", "#374151"),
                      command=self.destroy).pack(side="right", padx=2)

    def _refresh(self):
        from services import figure_bank

        selected = self._selected_id
        self._tree.delete(*self._tree.get_children())
        source_filter = _SOURCE_OPTIONS.get(self._source_var.get(), "")
        entries = figure_bank.list_entries(
            query=self._query_var.get(),
            source_filter=source_filter,
        )
        for entry in entries:
            self._tree.insert("", "end", iid=entry.id, values=(
                entry.id,
                entry.title,
                _source_label(entry.source),
                ", ".join(entry.tags[:6]),
                "Có" if entry.has_png else "",
                entry.created_at[:10] if entry.created_at else "",
            ))
        stats = figure_bank.stats()
        self._stats_lbl.configure(
            text=f"{stats.get('total', 0)} hình • {stats.get('with_png', 0)} PNG")
        if selected and self._tree.exists(selected):
            self._tree.selection_set(selected)
            self._tree.see(selected)
            self._on_select()
        elif entries:
            first = entries[0].id
            self._tree.selection_set(first)
            self._tree.see(first)
            self._on_select()
        else:
            self._selected_id = ""
            self._show_preview("", "", "", None)

    def _selected(self) -> str:
        selection = self._tree.selection()
        return str(selection[0]) if selection else ""

    def _on_select(self, _event=None):
        fid = self._selected()
        if not fid:
            return
        from services import figure_bank
        entry = figure_bank.get(fid)
        if not entry:
            return
        code = figure_bank.get_tikz(fid)
        self._selected_id = fid
        meta = (
            f"ID {entry.id} • {_source_label(entry.source)}"
            f" • {len(code)} ký tự"
            + (f" • PNG: {Path(entry.png_filename).name}" if entry.has_png else "")
        )
        png_path = entry.png_path() if entry.has_png else None
        self._show_preview(entry.title, meta, code, png_path)

    def _show_preview(self, title: str, meta: str, code: str, png_path=None):
        self._meta_lbl.configure(text=(f"{title}\n{meta}" if title else meta))
        self._show_render_image(png_path)
        self._preview.configure(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.insert("1.0", code)
        self._preview.configure(state="disabled")

    def _show_render_image(self, png_path) -> None:
        self._preview_image_ref = None
        if not png_path:
            self._image_lbl.configure(
                image=None,
                text="Chưa có ảnh render PNG.\nRender và lưu hình để xem ảnh tại đây.",
            )
            return
        path = Path(png_path)
        if not path.is_file():
            self._image_lbl.configure(
                image=None,
                text=f"Không tìm thấy ảnh PNG:\n{path.name}",
            )
            return
        try:
            from PIL import Image

            with Image.open(path) as image:
                preview = image.convert("RGBA")
            resample = getattr(getattr(Image, "Resampling", Image), "LANCZOS", 1)
            preview.thumbnail((440, 210), resample)
            ctk_image = ctk.CTkImage(
                light_image=preview,
                dark_image=preview,
                size=preview.size,
            )
            self._preview_image_ref = ctk_image
            self._image_lbl.configure(image=ctk_image, text="")
        except Exception as exc:
            self._image_lbl.configure(
                image=None,
                text=f"Không đọc được ảnh PNG:\n{exc}",
            )

    def _load_selected(self):
        fid = self._selected()
        if not fid:
            messagebox.showinfo("Chọn hình", "Hãy chọn 1 hình để nạp.",
                                parent=self)
            return
        from services import figure_bank
        entry = figure_bank.get(fid)
        code = figure_bank.get_tikz(fid)
        if not entry or not code:
            messagebox.showerror("Lỗi", "Không đọc được code TikZ của hình.",
                                 parent=self)
            return
        if callable(self._on_load_cb):
            self._on_load_cb(code, entry.title)
        self.destroy()

    def _copy_selected(self):
        fid = self._selected()
        if not fid:
            return
        from services import figure_bank
        code = figure_bank.get_tikz(fid)
        self.clipboard_clear()
        self.clipboard_append(code)
        messagebox.showinfo("Đã copy",
                            f"Đã copy code TikZ ({len(code)} ký tự).",
                            parent=self)

    def _edit_selected(self):
        fid = self._selected()
        if not fid:
            return
        from services import figure_bank
        entry = figure_bank.get(fid)
        if not entry:
            return
        MetadataDialog(self, entry, on_save=lambda data: self._save_metadata(fid, data))

    def _save_metadata(self, fid: str, data: dict):
        from services import figure_bank
        if figure_bank.update_metadata(
            fid,
            title=data["title"],
            description=data["description"],
            tags=data["tags"],
        ):
            self._refresh()

    def _delete_selected(self):
        fid = self._selected()
        if not fid:
            return
        if not messagebox.askyesno(
            "Xoá hình",
            f"Xoá hình ID {fid} khỏi kho?\nHành động này xoá cả file .tex/.png.",
            parent=self,
        ):
            return
        from services import figure_bank
        if figure_bank.delete(fid):
            self._selected_id = ""
            self._refresh()

    def _open_bank_folder(self):
        from services import figure_bank
        try:
            _open_folder(str(figure_bank.stats().get("dir", "")))
        except Exception as exc:
            messagebox.showerror("Lỗi mở thư mục", str(exc), parent=self)


class MetadataDialog(ctk.CTkToplevel):
    """Small CTk editor for FigureEntry metadata."""

    def __init__(self, parent, entry, *, on_save: Callable[[dict], None]):
        super().__init__(parent)
        self.title("Sửa metadata hình")
        self.geometry("500x390")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._on_save = on_save

        self._title_var = ctk.StringVar(value=entry.title)
        self._tags_var = ctk.StringVar(value=", ".join(entry.tags))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=18)
        ctk.CTkLabel(body, text=f"Sửa hình ID {entry.id}",
                     font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 12))
        ctk.CTkLabel(body, text="Tên hình").pack(anchor="w")
        ctk.CTkEntry(body, textvariable=self._title_var).pack(fill="x", pady=(2, 10))
        ctk.CTkLabel(body, text="Mô tả").pack(anchor="w")
        self._desc_box = ctk.CTkTextbox(body, height=88, wrap="word")
        self._desc_box.pack(fill="x", pady=(2, 10))
        self._desc_box.insert("1.0", entry.description or "")
        ctk.CTkLabel(body, text="Tags").pack(anchor="w")
        ctk.CTkEntry(body, textvariable=self._tags_var).pack(fill="x", pady=(2, 14))

        buttons = ctk.CTkFrame(body, fg_color="transparent")
        buttons.pack(fill="x")
        ctk.CTkButton(
            buttons, text="Lưu", width=110,
            fg_color=("#10B981", "#047857"),
            command=self._save,
        ).pack(side="left")
        ctk.CTkButton(
            buttons, text="Huỷ", width=90,
            fg_color=("#6B7280", "#374151"),
            command=self.destroy,
        ).pack(side="right")
        self.bind("<Escape>", lambda _e: self.destroy())

    def _save(self):
        title = self._title_var.get().strip()
        if not title:
            messagebox.showwarning("Thiếu tên", "Tên hình không được trống.",
                                   parent=self)
            return
        self._on_save({
            "title": title,
            "description": self._desc_box.get("1.0", "end").strip(),
            "tags": _parse_tags(self._tags_var.get()),
        })
        self.destroy()
