"""
v5/about.py — About dialog hiển thị version, license, links.

Mở qua QuickSwitcher action "about" hoặc menu Help nếu có.
"""
from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

import customtkinter as ctk


_ROOT = Path(__file__).resolve().parent.parent


def _assets_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets"
    return _ROOT / "assets"


def _first_existing_asset(*names: str) -> Path | None:
    base = _assets_dir()
    for name in names:
        path = base / name
        if path.exists():
            return path
    return None


class AboutDialog(ctk.CTkToplevel):
    """Modal compact — logo, version, build info, links và update."""

    WIDTH = 440
    HEIGHT = 540

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Về MEA v5")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        try: self.attributes("-topmost", True)
        except: pass
        try:
            ico = _first_existing_asset("app.ico", "icon_app.ico")
            if ico is not None:
                self.iconbitmap(default=str(ico))
        except Exception:
            pass

        from v5 import __version__

        # Logo / icon
        try:
            from PIL import Image
            logo_path = _first_existing_asset("app.png", "icon4.png")
            if logo_path is None:
                raise FileNotFoundError()
            logo = Image.open(logo_path).convert("RGBA")
            self._about_logo = ctk.CTkImage(
                light_image=logo,
                dark_image=logo,
                size=(88, 88),
            )
            ctk.CTkLabel(self, image=self._about_logo, text="").pack(
                pady=(24, 6))
        except Exception:
            ctk.CTkLabel(self, text="E", font=("Segoe UI", 46, "bold"),
                          text_color=("#1F497D", "#3A6FD8")
                          ).pack(pady=(28, 6))

        ctk.CTkLabel(self, text="MatrixExamAI",
                      font=("Segoe UI", 22, "bold")
                      ).pack(pady=(0, 2))

        ctk.CTkLabel(self, text="v5 Desktop — CustomTkinter",
                      font=("Segoe UI", 12),
                      text_color=("#6B7280", "#9CA3AF")
                      ).pack()

        # Version badge
        ver_frame = ctk.CTkFrame(self, fg_color=("#DBEAFE", "#1E3A8A"),
                                    corner_radius=12)
        ver_frame.pack(pady=12)
        ctk.CTkLabel(ver_frame, text=f"  v{__version__}  ",
                      font=("Segoe UI", 11, "bold"),
                      text_color=("#1E40AF", "#BFDBFE")
                      ).pack(padx=6, pady=2)

        # Tagline
        ctk.CTkLabel(self,
                      text="Tạo đề Toán bằng AI dành cho giáo viên THPT",
                      font=("Segoe UI", 11),
                      text_color=("#374151", "#D1D5DB")
                      ).pack(padx=20, pady=(8, 4))

        # Tech stack
        ctk.CTkLabel(self,
                      text=f"Python {sys.version.split()[0]}  •  "
                            f"CustomTkinter  •  Supabase",
                      font=("Segoe UI", 10),
                      text_color=("#6B7280", "#9CA3AF")
                      ).pack(pady=(0, 12))

        # Build info
        info_box = ctk.CTkFrame(self, fg_color=("#F3F4F6", "#293548"),
                                  corner_radius=6)
        info_box.pack(fill="x", padx=20, pady=4)
        for label, value in [
            ("Platform:", f"{sys.platform}"),
            ("Frozen:",   "yes (EXE)" if getattr(sys, "frozen", False)
                                       else "no (source)"),
            ("Data:",     str(Path.home() / ".exam_generator")),
        ]:
            row = ctk.CTkFrame(info_box, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=2)
            ctk.CTkLabel(row, text=label, width=80, anchor="w",
                          font=("Segoe UI", 10, "bold")
                          ).pack(side="left")
            ctk.CTkLabel(row, text=value, anchor="w",
                          font=("Segoe UI", 10),
                          text_color=("#374151", "#CBD5E1")
                          ).pack(side="left")

        # Links
        link_row = ctk.CTkFrame(self, fg_color="transparent")
        link_row.pack(pady=12)
        for label, url in [
            ("🌐 Website",      "https://matrixexam.ai"),
            ("📚 Tài liệu",      "https://github.com/matrixexamai/MEA/wiki"),
            ("🐛 Báo lỗi",       "https://github.com/matrixexamai/MEA/issues"),
        ]:
            ctk.CTkButton(link_row, text=label, width=110, height=28,
                            font=("Segoe UI", 10),
                            fg_color="transparent",
                            text_color=("#1F497D", "#60A5FA"),
                            hover_color=("#DBEAFE", "#1E3A8A"),
                            command=lambda u=url: webbrowser.open(u)
                            ).pack(side="left", padx=4)

        # Copyright
        ctk.CTkLabel(self,
                      text="© 2025 MatrixExam AI Team  •  MIT License",
                      font=("Segoe UI", 9),
                      text_color=("#9CA3AF", "#64748B")
                      ).pack(pady=(8, 0))

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(pady=(8, 16))
        ctk.CTkButton(
            footer, text="🔄 Kiểm tra cập nhật", width=160,
            command=self._open_update_check,
        ).pack(side="left", padx=4)
        ctk.CTkButton(footer, text="Đóng", width=100,
                        command=self.destroy
                        ).pack(side="left", padx=4)

        # ESC to close
        self.bind("<Escape>", lambda e: self.destroy())
        try: self.grab_set()
        except: pass
        try: self.focus_force()
        except: pass

    def _open_update_check(self):
        from v5.update_dialog import open_manual_update_check
        open_manual_update_check(self)
