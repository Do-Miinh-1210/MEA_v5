"""
v5/onboarding.py — Wizard 3 bước lần đầu mở app.

Steps:
    1. Welcome — giới thiệu MEA v5
    2. AI Provider — chọn Gemini/Claude/... + paste API key
    3. Done — vào trang chủ

Lưu `onboarded: true` vào v5_settings.json để không hiện lại.
"""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk
from tkinter import messagebox

from v5 import __version__, settings_store
from services.key_manager import get_key_manager


PROVIDERS = ["Google Gemini", "Anthropic Claude", "DeepSeek", "OpenAI"]


class OnboardingWizard(ctk.CTkToplevel):
    """3-step onboarding modal."""

    def __init__(self, parent, *, on_complete: Callable | None = None):
        super().__init__(parent)
        self.title("🚀 Chào mừng đến MEA v5")
        self.geometry("640x500")
        self.transient(parent); self.grab_set()
        self._on_complete = on_complete
        self._current_step = 0
        self._steps = [
            self._build_step_welcome,
            self._build_step_ai_key,
            self._build_step_done,
        ]
        self._build_shell()
        self._render_step()

    def _build_shell(self):
        # Top: progress dots
        top = ctk.CTkFrame(self, fg_color="transparent", height=40)
        top.pack(fill="x", padx=20, pady=(20, 10))
        self._dots = []
        for i in range(len(self._steps)):
            dot = ctk.CTkLabel(top, text=f"●", font=("Segoe UI", 14),
                                  text_color="#CBD5E1")
            dot.pack(side="left", padx=4)
            self._dots.append(dot)

        # Body container
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="both", expand=True, padx=20, pady=10)

        # Bottom: buttons
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.pack(fill="x", padx=20, pady=20)
        ctk.CTkButton(bot, text="Bỏ qua", width=100,
                       fg_color="#6B7280", hover_color="#4B5563",
                       command=self._skip).pack(side="left")
        self._back_btn = ctk.CTkButton(bot, text="←  Quay lại", width=100,
                                          fg_color="#6B7280",
                                          hover_color="#4B5563",
                                          command=self._prev)
        self._back_btn.pack(side="right", padx=4)
        self._next_btn = ctk.CTkButton(bot, text="Tiếp →", width=120,
                                          fg_color="#10B981",
                                          hover_color="#059669",
                                          command=self._next)
        self._next_btn.pack(side="right", padx=4)

    def _render_step(self):
        # Clear body
        for c in self._body.winfo_children():
            c.destroy()
        # Update dots
        for i, dot in enumerate(self._dots):
            dot.configure(text_color="#10B981" if i == self._current_step
                            else "#3B82F6" if i < self._current_step
                            else "#CBD5E1")
        # Render current step
        self._steps[self._current_step]()
        # Update buttons
        self._back_btn.configure(state="normal" if self._current_step > 0
                                    else "disabled")
        is_last = self._current_step == len(self._steps) - 1
        self._next_btn.configure(text="✓ Hoàn tất" if is_last else "Tiếp →")

    def _next(self):
        # Validate bước hiện tại trước khi next
        if not self._validate_current():
            return
        if self._current_step == len(self._steps) - 1:
            self._finish()
        else:
            self._current_step += 1
            self._render_step()

    def _prev(self):
        if self._current_step > 0:
            self._current_step -= 1
            self._render_step()

    def _skip(self):
        if not messagebox.askyesno("Bỏ qua",
            "Bỏ qua wizard này? Bạn có thể vào tab ⚙️ Cấu hình sau.",
            parent=self): return
        settings_store.set_value("onboarded", True)
        self.destroy()
        if self._on_complete: self._on_complete()

    def _finish(self):
        settings_store.set_value("onboarded", True)
        if getattr(self, "_shortcut_var", None) and self._shortcut_var.get():
            try:
                from services.desktop_shortcut import create_desktop_shortcut
                create_desktop_shortcut()
            except Exception:
                pass
        self.destroy()
        if self._on_complete: self._on_complete()

    def _validate_current(self) -> bool:
        # Hiện tại chỉ validate step AI key
        if self._current_step == 1:  # AI key
            if not self._ai_key_var.get().strip():
                if not messagebox.askyesno(
                    "Chưa nhập key",
                    "Bạn chưa nhập API key. Tiếp tục mà không setup?",
                    parent=self): return False
            else:
                # Save key
                try:
                    get_key_manager().save(self._provider_var.get(),
                                              self._ai_key_var.get().strip())
                except Exception as e:
                    messagebox.showerror("Lỗi lưu key", str(e), parent=self)
                    return False
        return True

    # ── Steps ─────────────────────────────────────────────────────────────
    def _build_step_welcome(self):
        ctk.CTkLabel(self._body, text="👋", font=("Segoe UI", 60)
                      ).pack(pady=(20, 8))
        ctk.CTkLabel(self._body, text="Chào mừng đến MEA v5!",
                      font=("Segoe UI", 22, "bold")
                      ).pack(pady=(0, 8))
        ctk.CTkLabel(self._body,
                      text=f"Phiên bản {__version__} • UI hiện đại (CustomTkinter)\n"
                           "Wizard 3 bước này giúp bạn setup nhanh.",
                      font=("Segoe UI", 12), text_color="gray",
                      justify="center"
                      ).pack(pady=(0, 16))

        features = ctk.CTkFrame(self._body, fg_color=("white", "#293548"),
                                   corner_radius=10)
        features.pack(fill="x", padx=20, pady=12)
        ctk.CTkLabel(features, text="✨ Tính năng nổi bật:",
                      font=("Segoe UI", 12, "bold"), anchor="w"
                      ).pack(anchor="w", padx=16, pady=(12, 4))
        for item in [
            "  • Tạo đề bằng AI (5 providers)",
            "  • Import PDF/Word/Ảnh → câu hỏi (AI Vision)",
            "  • QC chất lượng 6 tiêu chí",
            "  • Multi-image + drag-drop",
        ]:
            ctk.CTkLabel(features, text=item, font=("Segoe UI", 11),
                          text_color=("#374151", "#CBD5E1"),
                          anchor="w").pack(anchor="w", padx=16, pady=1)
        ctk.CTkLabel(features, text="", height=8).pack()

    def _build_step_ai_key(self):
        ctk.CTkLabel(self._body, text="🤖", font=("Segoe UI", 48)
                      ).pack(pady=(8, 4))
        ctk.CTkLabel(self._body, text="Bước 2: AI Provider",
                      font=("Segoe UI", 18, "bold")).pack(pady=(0, 4))
        ctk.CTkLabel(self._body,
                      text="Chọn provider và paste API key.",
                      font=("Segoe UI", 11), text_color="gray"
                      ).pack(pady=(0, 12))

        # Provider dropdown
        row = ctk.CTkFrame(self._body, fg_color="transparent")
        row.pack(fill="x", padx=40, pady=4)
        ctk.CTkLabel(row, text="Provider:", width=100, anchor="w"
                      ).pack(side="left")
        self._provider_var = ctk.StringVar(value="Google Gemini")
        ctk.CTkOptionMenu(row, values=PROVIDERS,
                            variable=self._provider_var, width=200
                            ).pack(side="left")

        # API key entry
        ctk.CTkLabel(self._body, text="API Key:", anchor="w"
                      ).pack(anchor="w", padx=40, pady=(12, 2))
        self._ai_key_var = ctk.StringVar()
        ctk.CTkEntry(self._body, textvariable=self._ai_key_var,
                       show="•", width=400, height=36,
                       placeholder_text="Paste key vào đây..."
                       ).pack(padx=40, pady=2)

        # Tips
        tips = ctk.CTkFrame(self._body, fg_color=("#FFFBEB", "#3F2E12"),
                               corner_radius=8)
        tips.pack(fill="x", padx=40, pady=(16, 0))
        ctk.CTkLabel(tips,
                      text="💡 Lấy API key miễn phí:\n"
                           "  • Gemini: https://aistudio.google.com/app/apikey\n"
                           "  • Claude: https://console.anthropic.com/\n"
                           "  • DeepSeek: https://platform.deepseek.com/\n\n"
                           "Bỏ trống nếu chưa có — bạn vẫn dùng được các tính năng offline.",
                      font=("Segoe UI", 10), justify="left", anchor="w",
                      text_color=("#92400E", "#FCD34D")
                      ).pack(anchor="w", padx=12, pady=10)

    def _build_step_backend(self):
        ctk.CTkLabel(self._body, text="🌐", font=("Segoe UI", 48)
                      ).pack(pady=(8, 4))
        ctk.CTkLabel(self._body, text="Bước 3: Cấu hình nâng cao",
                      font=("Segoe UI", 18, "bold")).pack(pady=(0, 4))
        ctk.CTkLabel(self._body,
                      text="Bước này đang được rút gọn để tập trung vào bản desktop.",
                      font=("Segoe UI", 11), text_color="gray", justify="center"
                      ).pack(pady=(0, 16))

        ctk.CTkLabel(self._body, text="Backend URL:",
                      anchor="w").pack(anchor="w", padx=40, pady=(0, 2))
        self._url_var = ctk.StringVar(value="http://localhost:8000")
        ctk.CTkEntry(self._body, textvariable=self._url_var, width=400,
                       height=36, placeholder_text="http://localhost:8000",
                       font=("Consolas", 11)
                       ).pack(padx=40, pady=2)

        info = ctk.CTkFrame(self._body, fg_color=("#EFF6FF", "#1E3A8A"),
                               corner_radius=8)
        info.pack(fill="x", padx=40, pady=(16, 0))
        ctk.CTkLabel(info,
                      text="ℹ️  Backend MEA v5 cho phép:\n"
                           "  • Đồng bộ NHCH Cloud\n\n"
                           "Có thể cấu hình các phần nâng cao sau trong mục Cấu hình.",
                      font=("Segoe UI", 10), justify="left", anchor="w",
                      text_color=("#1E40AF", "#93C5FD")
                      ).pack(anchor="w", padx=12, pady=10)

    def _build_step_done(self):
        ctk.CTkLabel(self._body, text="🎉", font=("Segoe UI", 70)
                      ).pack(pady=(20, 8))
        ctk.CTkLabel(self._body, text="Hoàn tất setup!",
                      font=("Segoe UI", 22, "bold"),
                      text_color="#10B981").pack()
        ctk.CTkLabel(self._body,
                      text="MEA v5 đã sẵn sàng. Một số bước nên làm tiếp:",
                      font=("Segoe UI", 11), text_color="gray"
                      ).pack(pady=(8, 16))

        nxt = ctk.CTkFrame(self._body, fg_color=("white", "#293548"),
                              corner_radius=10)
        nxt.pack(fill="x", padx=20, pady=8)
        for emoji, text in [
            ("✏️", "Vào tab Tạo đề → thử sinh 1 đề bằng AI"),
            ("📄", "Hoặc thả file PDF vào cửa sổ → import nhanh"),
            ("🏛", "Xem NHCH → quản lý câu hỏi"),
            ("⚙️", "Chỉnh sửa cấu hình bất kỳ lúc nào ở tab Cấu hình"),
        ]:
            row = ctk.CTkFrame(nxt, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(row, text=emoji, font=("Segoe UI", 14), width=30
                          ).pack(side="left")
            ctk.CTkLabel(row, text=text, font=("Segoe UI", 11), anchor="w"
                          ).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(nxt, text="", height=4).pack()

        self._shortcut_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self._body,
            text="📌 Thêm lối tắt MEA v5 vào Màn hình chính (Desktop)",
            variable=self._shortcut_var,
            font=("Segoe UI", 11, "bold"),
            text_color="#10B981",
        ).pack(pady=(10, 4))

        ctk.CTkLabel(self._body, text="Nhấn F1 bất kỳ lúc nào để xem phím tắt.",
                      font=("Segoe UI", 10, "italic"),
                      text_color="gray").pack(pady=(8, 0))
