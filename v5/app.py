"""
v5/app.py — Entry point cho MEA v5 Desktop (CustomTkinter rewrite).

Layout:
    ┌─────────────────────────────────────────────────────┐
    │ TopBar (logo + tier + user)                          │
    ├──────────────┬───────────────────────────────────────┤
    │ Sidebar 250  │ Content area (active view)            │
    │  🏠 Trang chủ │                                       │
    │  ⚙️ Cấu hình ▼│                                       │
    │  ✏️ Tạo đề ▼  │                                       │
    │  🏛 NHCH ▼   │                                       │
    │  🔄 Convert ▼│                                       │
    │  ✅ QC ▼     │                                       │
    │  📊 Theo dõi ▼                                       │
    │  📖 Hướng dẫn│                                       │
    └──────────────┴───────────────────────────────────────┘
"""
from __future__ import annotations

import sys
from pathlib import Path

# Cho phép import từ v4 (services, core, …)
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

import customtkinter as ctk

from v5 import __version__, settings_store
from v5.sidebar import Sidebar, SECTIONS
from v5.ui_theme import UI_COLORS
from v5.workspace import ExamWorkspace
# ── LAZY VIEW IMPORTS ────────────────────────────────────────────────────
# Defer heavy imports (matplotlib trong tracking, supabase trong setup)
# tới khi user click vào view tương ứng → giảm splash→first-paint time.
_VIEW_LAZY: dict[str, str] = {
    "home":        "v5.views.home.HomeView",
    "setup":       "v5.views.setup.SetupView",
    "exam_create": "v5.views.exam_create.ExamCreateView",
    "nhch":        "v5.views.nhch.NHCHView",
    "convert":     "v5.views.convert.ConvertView",
    "qc":          "v5.views.qc.QCView",
    "tracking":    "v5.views.tracking.TrackingView",   # ← matplotlib
    "omr_grade":   "omr_exam.app_ui.OMRExamApp",
    "guide":       "v5.views.guide.GuideView",
}
_VIEW_CACHE: dict[str, type] = {}


def _get_view_cls(view_id: str):
    """Lazy import 1 view class theo id."""
    if view_id in _VIEW_CACHE:
        return _VIEW_CACHE[view_id]
    path = _VIEW_LAZY.get(view_id)
    if not path:
        return None
    import importlib
    mod_path, cls_name = path.rsplit(".", 1)
    try:
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, cls_name)
        _VIEW_CACHE[view_id] = cls
        return cls
    except Exception as e:
        # Log đầy đủ traceback ra file (windowed EXE không có stdout)
        import traceback
        print(f"Lazy import {view_id} fail: {e}")
        try:
            from pathlib import Path
            lf = Path.home() / ".exam_generator" / "v5_view_errors.log"
            lf.parent.mkdir(parents=True, exist_ok=True)
            with lf.open("a", encoding="utf-8") as f:
                f.write(f"\n=== import {view_id} FAIL ===\n")
                f.write(traceback.format_exc())
        except Exception: pass
        return None

# Load settings để áp theme từ phiên trước
_SETTINGS = settings_store.load()
ctk.set_appearance_mode(_SETTINGS.get("theme", "System"))
# Color accent: blue (default) | green | dark-blue | mea-custom
_ACCENT_MAP = {
    "Xanh dương":  "blue",
    "Xanh lá":     "green",
    "Xanh đậm":    "dark-blue",
    "MEA Custom":  "mea-custom",   # → load v5/themes/mea_dark.json
}
_accent_saved = _SETTINGS.get("color_accent", "blue")
# Nếu user chọn theme custom → load từ JSON file
if _accent_saved == "mea-custom":
    from pathlib import Path as _P
    _custom_theme = _P(__file__).resolve().parent / "themes" / "mea_dark.json"
    try:
        ctk.set_default_color_theme(str(_custom_theme))
    except Exception:
        ctk.set_default_color_theme("blue")
else:
    try:
        ctk.set_default_color_theme(_accent_saved)
    except Exception:
        ctk.set_default_color_theme("blue")


def _assets_dir() -> Path:
    """Return bundled assets dir for source and PyInstaller one-file runs."""
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


class ModernApp(ctk.CTk):
    """Main window v5 — 1280×800, sidebar + content."""

    def __init__(self):
        super().__init__()
        self.title(f"MEA v{__version__} — MatrixExam AI (modern UI)")
        self._apply_v4_brand_icon()
        self._workspace = ExamWorkspace()
        self._license_info: dict = {}
        self._license_checked = False
        self._license_refreshing = False

        # Khôi phục geometry từ phiên trước
        geom = _SETTINGS.get("window_geometry", "1280x800")
        try: self.geometry(geom)
        except Exception: self.geometry("1280x800")
        self.minsize(1100, 700)

        # Grid: 0 = sidebar (fixed 250), 1 = content (expand)
        # Row 0 = topbar, row 1 = body (content/sidebar), row 2 = statusbar
        self.grid_columnconfigure(0, weight=0, minsize=250)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_topbar()
        self._build_sidebar()
        self._build_content()
        self._build_statusbar()

        # Khôi phục view cuối. View có feature gate chỉ được mở sau khi
        # license đã kiểm tra để không tạo cửa sổ thao tác premium tạm thời.
        last_view = _SETTINGS.get("last_view", "home")
        from v5.license_access import view_feature
        self._pending_initial_view = last_view if view_feature(last_view) else None
        self.show_view("home" if self._pending_initial_view else last_view)

        # Global keyboard shortcuts
        self._bind_shortcuts()
        # Check license without delaying first paint; V5 consumes the same
        # feature catalog as V4 once a result is available.
        self.after(250, self._refresh_license_state)
        self.after(5 * 60 * 1000, self._schedule_license_refresh)

        # Save settings khi đóng app
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Drag-drop file (PDF/Word/Ảnh → Import Wizard)
        self._setup_drag_drop()

        # ── Session autosave (mỗi 60s) + restore prompt ─────────────────
        from v5 import session_autosave
        # Background loop save exam_data của Exam Create view (nếu có)
        session_autosave.start_autosave(self, self._get_current_exam)
        # Hỏi user khôi phục session cũ (sau splash 1.5s)
        session_autosave.check_restore_prompt(self)

    def _apply_v4_brand_icon(self) -> None:
        """Use the same app icon assets as V4 for title bar and taskbar."""
        try:
            ico = _first_existing_asset("app.ico", "icon_app.ico")
            if ico is not None:
                self.iconbitmap(default=str(ico))
        except Exception:
            pass

        try:
            from PIL import Image, ImageTk
            png = _first_existing_asset("app.png", "icon4.png")
            if png is None:
                return
            image = Image.open(png).convert("RGBA")
            photos = []
            for size in (256, 64, 48, 32, 16):
                photos.append(ImageTk.PhotoImage(
                    image.resize((size, size), Image.LANCZOS)))
            self._window_icon_photos = photos
            self.wm_iconphoto(True, *photos)
        except Exception:
            pass

    def _get_current_exam(self):
        """Trả về đề hiện tại kể cả khi user đang ở view khác."""
        return self._workspace.current_exam

    def _on_exam_changed(self, exam):
        """Nhận thay đổi đề từ Exam Create và giữ ở cấp ứng dụng."""
        self._workspace.set_exam(exam)

    def _restore_session(self, exam):
        """Khôi phục ExamData vào Exam Create view."""
        self._workspace.set_exam(exam)
        if not self._license_checked:
            # Session data is already safe in workspace; defer gated routing
            # until license verification returns instead of dropping intent.
            self._pending_initial_view = "exam_create"
            self._notify_feature_locked(
                "Đã nạp phiên đề; sẽ mở màn Tạo đề sau khi kiểm tra giấy phép.")
            return
        self.show_view("exam_create")

    def _restore_history_exam(self, data: dict):
        """Khôi phục history vào workspace và mở ngay màn Tạo đề."""
        try:
            from services import exam_history
            exam = self._workspace.restore_history(
                data, snapshotter=exam_history.snapshot)
            self.show_view("exam_create")
            from v5.toast import show_toast
            show_toast(
                self,
                f"Đã khôi phục {len(exam.questions)} câu từ lịch sử",
                kind="success",
                duration=4,
            )
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi khôi phục", str(e), parent=self)

    def _add_bank_questions_to_exam(self, questions: list, metadata: dict):
        """Nhận câu được chọn từ NHCH và mở đề hiện tại để tiếp tục biên soạn."""
        try:
            from core.models import ExamData

            subject = str(metadata.get("subject") or "Toán")
            grade = str(metadata.get("grade") or "12")

            def _new_exam() -> ExamData:
                return ExamData(
                    exam_title="Đề biên soạn từ NHCH",
                    subject=subject,
                    grade=grade,
                    semester="",
                    year="",
                    time="45 phút",
                    questions=[],
                )

            result = self._workspace.add_questions(
                questions, exam_factory=_new_exam)
            if result.added:
                from v5 import session_autosave
                session_autosave.save_now(result.exam)
            self.show_view("exam_create")

            from v5.toast import show_toast
            message = f"Đã thêm {result.added} câu vào đề"
            if result.skipped:
                message += f" ({result.skipped} câu trùng đã bỏ qua)"
            show_toast(
                self,
                message,
                kind="success" if result.added else "warn",
                duration=5,
            )
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Lỗi thêm câu vào đề", str(e), parent=self)

    # ── TopBar ──────────────────────────────────────────────────────────────
    def _build_topbar(self):
        tb = ctk.CTkFrame(self, height=48, corner_radius=0,
                            fg_color=UI_COLORS["topbar"])
        tb.grid(row=0, column=0, columnspan=2, sticky="ew")
        tb.grid_columnconfigure(1, weight=1)

        # Logo + tên: dùng cùng app.png với V4 để đồng bộ nhận diện.
        brand = ctk.CTkFrame(tb, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="w", padx=(10, 4))
        try:
            from PIL import Image
            logo_path = _first_existing_asset("app.png", "icon4.png")
            if logo_path is None:
                raise FileNotFoundError()
            logo = Image.open(logo_path).convert("RGBA")
            self._topbar_logo = ctk.CTkImage(
                light_image=logo,
                dark_image=logo,
                size=(30, 30),
            )
            ctk.CTkLabel(brand, image=self._topbar_logo, text="").pack(
                side="left", padx=(0, 8))
        except Exception:
            ctk.CTkLabel(brand, text="  E  ", text_color="white",
                         font=("Segoe UI", 14, "bold")).pack(side="left")
        ctk.CTkLabel(brand, text="MatrixExamAI", text_color="white",
                     font=("Segoe UI", 14, "bold")).pack(side="left")

        # Tier badge updates asynchronously from the actual license state.
        self._tier_var = ctk.StringVar(value="LICENSE ...")
        self._tier_label = ctk.CTkLabel(
            tb, textvariable=self._tier_var, text_color="#FCD34D",
            font=("Segoe UI", 10, "bold"))
        self._tier_label.grid(row=0, column=2, sticky="e", padx=8)

        # Accent color picker (palette dropdown)
        accent_inv = {v: k for k, v in _ACCENT_MAP.items()}
        cur_label = accent_inv.get(_accent_saved, "Xanh dương")
        ctk.CTkOptionMenu(tb, values=list(_ACCENT_MAP.keys()),
                            width=110, height=28,
                            fg_color="#0B1F35", button_color="#163D6B",
                            command=self._on_accent_change,
                            ).set(cur_label) if False else None
        # Quick switcher hint button (n22) — col 1 (after logo, before stretch)
        ctk.CTkButton(tb, text="🔍 Tìm kiếm (Ctrl+T)",
                        width=160, height=28,
                        fg_color="transparent", text_color="#93C5FD",
                        hover_color="#0B1F35",
                        font=("Segoe UI", 10),
                        anchor="w",
                        command=self._open_quick_switch
                        ).grid(row=0, column=1, sticky="w", padx=(8, 0))

        # 📄 Recent files dropdown (n6) — col 3
        self._build_recent_menu(tb)

        accent_menu = ctk.CTkOptionMenu(
            tb, values=list(_ACCENT_MAP.keys()),
            width=110, height=28,
            fg_color="#0B1F35", button_color="#163D6B",
            text_color="white",
            command=self._on_accent_change)
        accent_menu.set(cur_label)
        accent_menu.grid(row=0, column=4, sticky="e", padx=(0, 4))

        # F1 help hint — col 5
        ctk.CTkButton(tb, text="F1 — Phím tắt", width=110, height=28,
                       fg_color="transparent", text_color="white",
                       hover_color="#0B1F35", font=("Segoe UI", 10),
                       command=self._show_help
                       ).grid(row=0, column=5, sticky="e", padx=(0, 4))

        # Theme switcher — col 6
        theme_btn = ctk.CTkSegmentedButton(
            tb, values=["☀", "🌙", "💻"], width=110,
            command=self._on_theme_change)
        theme_btn.set("💻")
        theme_btn.grid(row=0, column=6, sticky="e", padx=10)

    def _build_recent_menu(self, parent):
        """Dropdown 📄 — list 5 file gần nhất, click → mở Import Wizard."""
        self._recent_btn = ctk.CTkButton(
            parent, text="📄 Gần đây ▾", width=120, height=28,
            fg_color="transparent", text_color="white",
            hover_color="#0B1F35", font=("Segoe UI", 10),
            command=self._open_recent_popup)
        self._recent_btn.grid(row=0, column=3, sticky="e", padx=(0, 2))

    def _open_recent_popup(self):
        """Hiện popup nhỏ dưới nút 📄, list recent files."""
        try:
            files = settings_store.get_recent_files()[:7]
        except Exception:
            files = []

        # Tạo popup (CTkToplevel borderless)
        popup = ctk.CTkToplevel(self)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        # Position dưới nút
        try:
            self._recent_btn.update_idletasks()
            x = self._recent_btn.winfo_rootx()
            y = self._recent_btn.winfo_rooty() + self._recent_btn.winfo_height()
            popup.geometry(f"360x{min(40 + len(files)*30, 320)}+{x}+{y}")
        except Exception:
            popup.geometry("360x180+200+80")
        popup.configure(fg_color=("#FFFFFF", "#1E293B"))

        border = ctk.CTkFrame(popup, fg_color=("#3B82F6", "#3B82F6"),
                                corner_radius=6)
        border.pack(fill="both", expand=True, padx=1, pady=1)
        inner = ctk.CTkFrame(border, fg_color=("#FFFFFF", "#1E293B"),
                                corner_radius=5)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        if not files:
            ctk.CTkLabel(inner, text="(Chưa có file nào gần đây)",
                          text_color="gray", font=("Segoe UI", 10)
                          ).pack(pady=20)
        else:
            from pathlib import Path
            for p in files:
                name = Path(p).name
                btn = ctk.CTkButton(
                    inner, text=f"📄  {name[:42]}", anchor="w",
                    height=28, font=("Segoe UI", 10),
                    fg_color="transparent",
                    text_color=("#1F2937", "#F1F5F9"),
                    hover_color=("#DBEAFE", "#1E3A8A"),
                    corner_radius=4,
                    command=lambda pp=p: self._on_recent_click(popup, pp))
                btn.pack(fill="x", padx=4, pady=1)
            ctk.CTkButton(inner, text="🗑 Xoá lịch sử", height=24,
                            font=("Segoe UI", 9),
                            fg_color="transparent",
                            text_color=("#6B7280", "#9CA3AF"),
                            hover_color=("#FEE2E2", "#7F1D1D"),
                            command=lambda: self._clear_recent(popup)
                            ).pack(fill="x", padx=4, pady=(4, 2))

        # Click out → close
        popup.bind("<FocusOut>", lambda e: popup.after(150, popup.destroy))
        try: popup.focus_force()
        except: pass

    def _on_recent_click(self, popup, path: str):
        try: popup.destroy()
        except: pass
        from pathlib import Path
        p = Path(path)
        if not p.exists():
            from v5.toast import show_toast
            show_toast(self, f"File không còn tồn tại: {p.name}",
                        kind="warn", duration=4)
            return
        self._open_import_for(p)

    def _clear_recent(self, popup):
        try: popup.destroy()
        except: pass
        try:
            settings_store.set_value("recent_files", [])
            from v5.toast import show_toast
            show_toast(self, "✓ Đã xoá lịch sử file", kind="success")
        except Exception: pass

    def _on_theme_change(self, choice: str):
        mode = {"☀": "Light", "🌙": "Dark", "💻": "System"}.get(choice, "System")
        ctk.set_appearance_mode(mode)
        settings_store.set_value("theme", mode)

    def _on_accent_change(self, choice: str):
        """Đổi color accent — cần restart để áp dụng đầy đủ (CTk limitation)."""
        accent = _ACCENT_MAP.get(choice, "blue")
        settings_store.set_value("color_accent", accent)
        from v5.toast import show_toast
        show_toast(self,
                    f"Đã đổi sang {choice}. Khởi động lại app để áp dụng.",
                    kind="info", duration=4)

    # ── License / feature access ────────────────────────────────────────────
    def _refresh_license_state(self, force_online: bool = False):
        """Refresh license in background and update badge/feature access."""
        if self._license_refreshing:
            return
        self._license_refreshing = True

        def _worker():
            try:
                from services.license_manager import check_license
                info = check_license(force_online=force_online)
            except Exception as exc:
                info = {"ok": False, "status": "error", "message": str(exc)}

            def _apply():
                self._license_refreshing = False
                self._apply_license_state(info)

            try:
                self.after(0, _apply)
            except Exception:
                pass

        import threading
        threading.Thread(target=_worker, daemon=True).start()

    def _schedule_license_refresh(self):
        """Periodic recheck, matching V4's five-minute license refresh."""
        self._refresh_license_state(force_online=True)
        try:
            self.after(5 * 60 * 1000, self._schedule_license_refresh)
        except Exception:
            pass

    def _apply_license_state(self, info: dict):
        from v5.license_access import badge_presentation, effective_features

        self._license_info = info or {}
        self._license_checked = True
        self._features = effective_features(self._license_info)
        label, color = badge_presentation(self._license_info, checked=True)
        try:
            self._tier_var.set(label)
            self._tier_label.configure(text_color=color)
        except Exception:
            return

        pending = getattr(self, "_pending_initial_view", None)
        self._pending_initial_view = None
        if (
            pending
            and getattr(self, "_current_view_id", None) == "home"
            and self._view_allowed(pending, notify=False)
        ):
            self.show_view(pending)
            return

        current_id = getattr(self, "_current_view_id", None)
        if current_id and not self._view_allowed(current_id, notify=False):
            self.show_view("home")
            self._notify_feature_locked(
                "Màn hình vừa mở không khả dụng theo license hiện tại.")
            return
        view = getattr(self, "_current_view", None)
        if view is not None and hasattr(view, "apply_feature_gates"):
            try:
                view.apply_feature_gates(self._features)
            except Exception as exc:
                print(f"apply feature gates fail: {exc}")

    def _notify_feature_locked(self, message: str):
        try:
            from v5.toast import show_toast
            show_toast(self, f"🔒 {message}", kind="warn", duration=5)
        except Exception:
            pass

    def _can_use_feature(self, feature: str, *, notify: bool = True) -> bool:
        from v5.license_access import feature_allowed, restriction_message
        return True

    def _view_allowed(self, view_id: str, *, notify: bool = True) -> bool:
        from v5.license_access import view_feature
        return True

    # ── Sidebar ─────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = Sidebar(self, on_navigate=self.show_view,
                                on_action=self._on_sidebar_action)
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

    def _on_sidebar_action(self, action: str):
        """Trigger action từ sidebar sub-item (vd 'quick_gen', 'smart_prompt').

        Delay 200ms để view kịp render trước khi mở dialog / focus tab.
        Mapping:
            quick_gen / smart_prompt  → mở dialog (exam_create)
            import_pdf / sync_cloud   → action trên NHCH view
            ai_provider / subject / license       → focus tab Setup
            qc_focus / ai_review / tikz_focus     → focus tab QC
            track_dashboard / track_history / track_usage → focus tab Tracking
        """
        # Map action → (method_name_to_call_on_view, app_level_fn_optional)
        VIEW_METHOD = {
            "quick_gen":         "open_quick_gen",
            "import_pdf":         None,  # special: open_import | _open_import_pdf
            "sync_cloud":        "_sync_to_cloud",
            "ai_provider":       "focus_ai_provider",
            "subject":           "focus_subject",
            "license":           "focus_license",
            "qc_focus":          "focus_qc",
            "ai_review":         "focus_ai_review",
            "tikz_focus":        "focus_tikz",
            "track_dashboard":   "focus_dashboard",
            "track_history":     "focus_history",
            "track_usage":       "focus_usage",
            "conv_image":        "focus_image_mode",
            "conv_pdf":          "focus_pdf_mode",
            "conv_ai_text":      "focus_ai_text_mode",
            "exam_history":      "open_exam_history",
            "nhch_stats":        "open_stats",
            "ai_gen_matrix":     "open_ai_gen_matrix",
        }

        def _do():
            v = self._current_view
            if v is None: return
            try:
                if action == "smart_prompt":
                    # App-level: Smart Prompt mở qua callback exam_create
                    self._open_smart_prompt(); return
                if action in ("import_pdf", "import"):
                    fn = (getattr(v, "open_import", None)
                            or getattr(v, "_open_import_pdf", None))
                    if callable(fn): fn()
                    return
                method = VIEW_METHOD.get(action)
                if method:
                    fn = getattr(v, method, None)
                    if callable(fn): fn()
            except Exception as e:
                print(f"sidebar action {action} dispatch fail: {e}")

        # Nếu view đã render (winfo_exists) → dispatch ngay; chỉ delay khi
        # show_view vừa được gọi và view chưa được mount đủ.
        v = self._current_view
        try:
            ready = (v is not None and v.winfo_exists()
                       and v.winfo_ismapped())
        except Exception:
            ready = False
        if ready:
            _do()
        else:
            self.after(200, _do)

    # ── Content ─────────────────────────────────────────────────────────────
    def _build_content(self):
        # Wrapper với scroll (sẽ giao cho từng view tự render bên trong)
        self.content = ctk.CTkFrame(self, fg_color=UI_COLORS["app_bg"],
                                       corner_radius=0)
        self.content.grid(row=1, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self._current_view: ctk.CTkFrame | None = None
        self._current_view_id: str | None = None

    def _build_statusbar(self):
        from v5.statusbar import StatusBar
        self.statusbar = StatusBar(self)
        self.statusbar.grid(row=2, column=0, columnspan=2, sticky="ew")

    # ── Navigation ──────────────────────────────────────────────────────────
    def show_view(self, view_id: str):
        """Switch active view. view_id phải khớp SECTIONS."""
        if view_id not in SECTIONS:
            view_id = "home"
        if not self._view_allowed(view_id):
            return
        # Destroy view hiện tại
        if self._current_view is not None:
            try: self._current_view.destroy()
            except Exception: pass

        # Lazy-load view class chỉ khi user click → giảm startup time
        cls = _get_view_cls(view_id)
        ok = False
        if cls:
            try:
                kwargs = {"on_navigate": self.show_view}
                if view_id == "exam_create":
                    kwargs.update({
                        "initial_exam": self._workspace.current_exam,
                        "on_exam_changed": self._on_exam_changed,
                        "can_use_feature": self._can_use_feature,
                    })
                elif view_id == "nhch":
                    kwargs["on_add_questions"] = self._add_bank_questions_to_exam
                    kwargs["can_use_feature"] = self._can_use_feature
                elif view_id == "convert":
                    kwargs["on_add_questions"] = self._add_bank_questions_to_exam
                    kwargs["can_use_feature"] = self._can_use_feature
                elif view_id == "tracking":
                    kwargs["on_restore_exam"] = self._restore_history_exam
                    kwargs["get_current_exam"] = lambda: self._workspace.current_exam
                elif view_id == "qc":
                    kwargs["can_use_feature"] = self._can_use_feature
                    kwargs["initial_exam"] = self._workspace.current_exam
                    kwargs["get_current_exam"] = lambda: self._workspace.current_exam
                    kwargs["on_exam_changed"] = self._on_exam_changed
                elif view_id == "setup":
                    kwargs["on_license_update"] = self._apply_license_state
                self._current_view = cls(self.content, **kwargs)
                ok = True
            except Exception as e:
                # Instantiation lỗi → hiện view báo lỗi (không crash app)
                import traceback
                tb = traceback.format_exc()
                try:
                    from pathlib import Path
                    lf = Path.home() / ".exam_generator" / "v5_view_errors.log"
                    with lf.open("a", encoding="utf-8") as f:
                        f.write(f"\n=== build {view_id} FAIL ===\n{tb}")
                except Exception: pass
                self._current_view = _ErrorView(self.content, view_id, str(e))
        else:
            self._current_view = _StubView(self.content, view_id)

        self._current_view.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self._current_view_id = view_id
        try:
            self.sidebar.set_active(view_id)
        except Exception:
            pass
        if self._license_checked and hasattr(self._current_view, "apply_feature_gates"):
            try:
                self._current_view.apply_feature_gates(self._features)
            except Exception as exc:
                print(f"apply feature gates fail: {exc}")
        # Persist last_view (chỉ khi load thành công)
        if ok:
            settings_store.set_value("last_view", view_id)

    def _on_close(self):
        """Save state trước khi destroy app."""
        try:
            settings_store.save({
                "window_geometry": self.geometry(),
                "theme": ctk.get_appearance_mode(),
            })
        except Exception: pass
        self.destroy()

    # ── Keyboard shortcuts ──────────────────────────────────────────────
    def _bind_shortcuts(self):
        """Bind global shortcuts (Ctrl+1..9 / Ctrl+G/E/S / F1 / F5 / Ctrl+Q)."""
        view_order = ["home", "setup", "exam_create", "nhch",
                       "convert", "qc", "tracking", "guide"]
        for i, vid in enumerate(view_order, 1):
            if i <= 9:
                self.bind(f"<Control-Key-{i}>",
                            lambda e, v=vid: self.show_view(v))

        self.bind("<Control-g>", lambda e: self._trigger_action("generate"))
        self.bind("<Control-G>", lambda e: self._trigger_action("generate"))
        self.bind("<Control-e>", lambda e: self._trigger_action("export"))
        self.bind("<Control-E>", lambda e: self._trigger_action("export"))
        self.bind("<F1>", lambda e: self._show_help())
        self.bind("<F5>", lambda e: self._reload_current())
        self.bind("<Control-q>", lambda e: self.destroy())
        self.bind("<Control-Q>", lambda e: self.destroy())

        # Ctrl+T → Quick switcher (như VSCode command palette)
        self.bind("<Control-t>", lambda e: self._open_quick_switch())
        self.bind("<Control-T>", lambda e: self._open_quick_switch())

        # Ctrl+, → Preferences dialog (như VSCode/macOS convention)
        self.bind("<Control-comma>", lambda e: self._open_prefs())

        # Ctrl+Shift+P → Smart Prompt (tạo đề/câu hỏi bằng AI từ mô tả)
        self.bind("<Control-P>", lambda e: self._open_smart_prompt())

    def _open_prefs(self):
        from v5.preferences import PreferencesDialog
        PreferencesDialog(self)

    def _open_smart_prompt(self):
        """Mở Smart Prompt dialog với callback áp dụng matrix vào Exam Create."""
        if not self._can_use_feature("smart_prompt"):
            return
        from v5.smart_prompt import SmartPromptDialog
        SmartPromptDialog(self,
                            on_apply_matrix=self._apply_smart_matrix,
                            on_add_question=None)

    def _apply_smart_matrix(self, matrix, info: dict):
        """Áp dụng MatrixData từ Smart Prompt → Exam Create view."""
        self.show_view("exam_create")

        def _inject():
            v = self._current_view
            if v is None or not hasattr(v, "_matrix_rows"):
                return
            try:
                # Clear rows + nạp từ matrix (aggregate level đơn → grouped)
                v._matrix_rows.clear()
                if hasattr(v, "_apply_matrix_to_rows"):
                    v._apply_matrix_to_rows(matrix)
                if hasattr(v, "_render_matrix"):
                    v._render_matrix()
                # MatrixData dùng time_str (vd "90 phút") → parse số phút
                if hasattr(v, "_duration_var"):
                    import re as _re
                    ts = _re.search(r"\d+",
                                     str(getattr(matrix, "time_str", "") or ""))
                    if ts: v._duration_var.set(ts.group(0))
            except Exception as e:
                print(f"apply_smart_matrix inject fail: {e}")

        self.after(300, _inject)

    def _open_quick_switch(self):
        from v5.quickswitch import QuickSwitcher
        def _action(key):
            if   key == "F1":       self._show_help()
            elif key == "theme":
                cur = ctk.get_appearance_mode()
                nxt = {"Light": "Dark", "Dark": "System",
                       "System": "Light"}.get(cur, "System")
                ctk.set_appearance_mode(nxt)
                from v5 import settings_store
                settings_store.set_value("theme", nxt)
            elif key == "collapse" and hasattr(self, "sidebar"):
                self.sidebar.toggle_collapse()
            elif key == "import":
                from tkinter import filedialog
                from pathlib import Path
                p = filedialog.askopenfilename(
                    parent=self, title="Chọn file import",
                    filetypes=[("All", "*.pdf *.docx *.png *.jpg"),
                                ("PDF", "*.pdf"), ("Word", "*.docx"),
                                ("Ảnh", "*.png *.jpg *.jpeg")])
                if p: self._open_import_for(Path(p))
            elif key == "crash_log":
                from v5.crash_reporter import CrashLogViewer
                CrashLogViewer(self)
            elif key == "smart_prompt":
                self._open_smart_prompt()
            elif key == "quick_gen":
                # Mở exam_create + dialog Quick Gen
                self.show_view("exam_create")
                def _q():
                    v = self._current_view
                    if v and hasattr(v, "open_quick_gen"): v.open_quick_gen()
                self.after(250, _q)
            elif key == "exam_history":
                # Mở Tracking view (focus History) + dialog ExamHistory
                self.show_view("tracking")
                def _h():
                    v = self._current_view
                    if v and hasattr(v, "focus_history"): v.focus_history()
                    if v and hasattr(v, "open_exam_history"):
                        v.open_exam_history()
                self.after(250, _h)
            elif key == "nhch_stats":
                self.show_view("nhch")
                def _s():
                    v = self._current_view
                    if v and hasattr(v, "open_stats"): v.open_stats()
                self.after(200, _s)
            elif key == "task_log":
                from v5.task_log import TaskLogDialog
                TaskLogDialog(self)
            elif key == "ai_gen_matrix":
                self.show_view("exam_create")
                def _ai():
                    v = self._current_view
                    if v and hasattr(v, "open_ai_gen_matrix"):
                        v.open_ai_gen_matrix()
                self.after(250, _ai)
            elif key == "prefs":
                from v5.preferences import PreferencesDialog
                PreferencesDialog(self)
            elif key == "check_update":
                from v5.update_dialog import open_manual_update_check
                open_manual_update_check(self)
            elif key == "about":
                from v5.about import AboutDialog
                AboutDialog(self)
            elif key == "whats_new":
                from v5.whats_new import WhatsNewDialog
                WhatsNewDialog(self)
            elif key == "quit":     self.destroy()
        QuickSwitcher(self, on_navigate=self.show_view, on_action=_action)

    def _trigger_action(self, action: str):
        v = self._current_view
        if v is None: return
        method_map = {"generate": "_on_generate",
                      "export":   "_export_word"}
        m = getattr(v, method_map.get(action, ""), None)
        if callable(m):
            try: m()
            except Exception as e: print(f"Shortcut {action} fail: {e}")

    def _reload_current(self):
        if self._current_view is None: return
        cls_name = type(self._current_view).__name__
        view_id_map = {"HomeView": "home", "SetupView": "setup",
                        "ExamCreateView": "exam_create", "NHCHView": "nhch",
                        "QCView": "qc", "TrackingView": "tracking",
                        "GuideView": "guide",
                        "ConvertView": "convert"}
        vid = view_id_map.get(cls_name)
        if vid: self.show_view(vid)

    # ── Drag-drop ───────────────────────────────────────────────────────
    def _setup_drag_drop(self):
        """Cho phép kéo file PDF/Word/Ảnh vào cửa sổ → mở Import Wizard."""
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD
            # ModernApp đã inherit từ CTk (tk.Tk subclass). Monkey-patch DnD:
            try:
                self.tk.call("package", "require", "tkdnd")
            except Exception as e:
                print(f"tkdnd not available: {e}"); return
            # Register drop target
            self.tk.call("tkdnd::drop_target", "register", str(self), DND_FILES)
            self.bind("<<Drop>>", self._on_drop)
        except ImportError:
            print("tkinterdnd2 not installed — drag-drop disabled")
        except Exception as e:
            print(f"setup_drag_drop fail: {e}")

    def _on_drop(self, event):
        """File(s) được drop vào cửa sổ.

        - 1 file → mở Import Wizard với file đó
        - Nhiều file → hỏi user batch import; mở wizard từng cái tuần tự
        """
        from pathlib import Path
        import re as _re
        from v5.toast import show_toast

        raw = event.data
        paths = _re.findall(r'\{([^}]+)\}|(\S+)', raw)
        files = [(a or b).strip() for a, b in paths if (a or b).strip()]
        # Filter chỉ các file hợp lệ
        valid_exts = {".pdf", ".docx", ".png", ".jpg", ".jpeg",
                       ".bmp", ".webp", ".tiff"}
        files = [Path(f) for f in files
                  if Path(f).is_file()
                  and Path(f).suffix.lower() in valid_exts]
        if not files:
            show_toast(self, "Chỉ hỗ trợ PDF/Word/Ảnh", kind="warn")
            return

        if len(files) == 1:
            self._open_import_for(files[0])
        else:
            # Batch: hỏi user
            from tkinter import messagebox
            if not messagebox.askyesno(
                "Batch Import",
                f"Đã thả {len(files)} file vào cửa sổ.\n\n"
                f"Mở Import Wizard tuần tự cho từng file?\n"
                f"(Mỗi file 1 wizard riêng)",
                parent=self): return
            show_toast(self,
                        f"📥 Batch import {len(files)} file...",
                        kind="info", duration=2)
            # Mở từng wizard với delay nhỏ giữa các cái
            for i, f in enumerate(files):
                self.after(i * 400, lambda fp=f: self._open_import_for(fp))

    def _open_import_for(self, filepath):
        """Mở Import Wizard V5 cho một file và ghi nhận recent_files."""
        if not self._can_use_feature("tab_bank"):
            return
        # Track recent files
        try:
            settings_store.add_recent_file(str(filepath))
        except Exception: pass
        try:
            from v5.import_wizard import ImportWizardCTk
            ImportWizardCTk(
                self, str(filepath), subject="Toán", grade="12",
                can_use_feature=self._can_use_feature)
        except Exception as e:
            from v5.toast import show_toast
            show_toast(self, f"Lỗi mở Import V5: {e}",
                        kind="error", duration=5)

    def _show_help(self):
        from tkinter import messagebox
        messagebox.showinfo(
            "Phím tắt MEA v5",
            "Phím tắt toàn cục:\n\n"
            "  Ctrl+1     →  🏠 Trang chủ\n"
            "  Ctrl+2     →  ⚙️  Cấu hình\n"
            "  Ctrl+3     →  ✏️  Tạo đề\n"
            "  Ctrl+4     →  🏛 Ngân hàng\n"
            "  Ctrl+5     →  🔄 Convert câu hỏi\n"
            "  Ctrl+6     →  ✅ Chất lượng\n"
            "  Ctrl+7     →  📊 Theo dõi\n"
            "  Ctrl+8     →  📖 Hướng dẫn\n\n"
            "  Ctrl+G     →  Tạo đề (trong Exam Create)\n"
            "  Ctrl+E     →  Xuất Word\n"
            "  Ctrl+T     →  🔍 Quick switcher (gõ \"crash\" → xem log lỗi)\n"
            "  Ctrl+,     →  ⚙ Tuỳ chọn (Preferences)\n"
            "  Ctrl+Shift+P → 💬 Smart Prompt (tạo đề từ mô tả)\n"
            "  F1         →  Hiển thị help này\n"
            "  F5         →  Reload view hiện tại\n"
            "  Ctrl+Q     →  Thoát app\n\n"
            "  ☀  🌙  💻   →  Switch theme ở TopBar",
            parent=self)


class _StubView(ctk.CTkFrame):
    """Placeholder cho view chưa implement — hiện ngày phát triển dự kiến."""

    PLAN = {
        "setup":         ("⚙️ Cấu hình",  "Port từ v4: tab_config, tab_user_info"),
        "exam_create":   ("✏️ Tạo đề",    "Port: tab_matrix, tab_result, smart_prompt"),
        "nhch":          ("🏛 Ngân hàng",  "Port: tab_bank, dialog_import_pdf"),
        "convert":       ("🔄 Convert",    "Ảnh/PDF/Word/AI Text → câu hỏi trong workflow V5"),
        "qc":            ("✅ Chất lượng", "Port: tab_qc, ai_reviewer, tab_tikz"),
        "tracking":      ("📊 Theo dõi",   "Port: tab_dashboard, tab_history, tab_ai_usage"),
        "guide":         ("📖 Hướng dẫn",  "Port: tab_guide (Hướng dẫn từng tính năng)"),
    }

    def __init__(self, parent, view_id: str):
        super().__init__(parent, fg_color="transparent")
        title, plan = self.PLAN.get(view_id, ("?", "Chưa rõ"))
        ctk.CTkLabel(self, text=title,
                      font=("Segoe UI", 26, "bold")).pack(pady=(60, 8))
        ctk.CTkLabel(self,
                      text="Không tải được module V5 trong bản cài đặt",
                      font=("Segoe UI", 14),
                      text_color="gray").pack(pady=4)
        ctk.CTkLabel(self,
                      text=f"Kế hoạch: {plan}",
                      font=("Segoe UI", 11),
                      text_color="gray").pack(pady=4)

        ctk.CTkLabel(
            self,
            text="Mở Tùy chọn > Chẩn đoán hoặc gửi log lỗi để kiểm tra bản cài đặt.",
            text_color=("#1F497D", "#60A5FA"),
            font=("Segoe UI", 11),
        ).pack(pady=20)


class _ErrorView(ctk.CTkFrame):
    """Hiện khi 1 view lỗi lúc khởi tạo — báo rõ + nút thử lại, không crash."""

    def __init__(self, parent, view_id: str, err: str):
        super().__init__(parent, fg_color="transparent")
        self._view_id = view_id
        ctk.CTkLabel(self, text="⚠️  Không mở được mục này",
                      font=("Segoe UI", 22, "bold"),
                      text_color=("#DC2626", "#F87171")).pack(pady=(50, 6))
        ctk.CTkLabel(self, text=f"Lỗi: {err[:200]}",
                      font=("Segoe UI", 12), wraplength=620,
                      text_color=("#374151", "#CBD5E1")).pack(pady=4, padx=20)
        ctk.CTkLabel(self,
                      text="Chi tiết đã ghi vào ~/.exam_generator/v5_view_errors.log\n"
                           "Mở 🩺 Chẩn đoán (Ctrl+,) hoặc gửi log này để được hỗ trợ.",
                      font=("Segoe UI", 10), text_color="gray",
                      justify="center").pack(pady=8)
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=16)
        ctk.CTkButton(btns, text="🔄 Thử lại", width=120,
                        command=self._retry).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="📂 Mở log", width=120,
                        fg_color=("#6B7280", "#374151"),
                        command=self._open_log).pack(side="left", padx=4)

    def _retry(self):
        try:
            top = self.winfo_toplevel()
            if hasattr(top, "show_view"):
                _VIEW_CACHE.pop(self._view_id, None)
                top.show_view(self._view_id)
        except Exception: pass

    def _open_log(self):
        try:
            import subprocess
            from pathlib import Path
            lf = Path.home() / ".exam_generator" / "v5_view_errors.log"
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", str(lf)])
            else:
                subprocess.Popen(["xdg-open", str(lf.parent)])
        except Exception: pass

def _show_welcome_toast(app):
    """Toast chào mừng sau splash, hiển thị thời gian từ lần mở cuối.

    Lần đầu tiên (chưa có last_opened_ts) → bỏ qua, chỉ ghi timestamp.
    """
    from datetime import datetime
    last_iso = _SETTINGS.get("last_opened_ts", "")
    # Lưu now ngay để lần sau dùng
    now_iso = datetime.now().isoformat(timespec="seconds")
    try: settings_store.set_value("last_opened_ts", now_iso)
    except Exception: pass

    if not last_iso:
        return    # lần đầu — không show

    try:
        last = datetime.fromisoformat(last_iso)
        ago = (datetime.now() - last).total_seconds()
        if   ago < 60:      txt = f"vừa xong"
        elif ago < 3600:    txt = f"{int(ago/60)} phút trước"
        elif ago < 86400:   txt = f"{int(ago/3600)} giờ trước"
        else:               txt = f"{int(ago/86400)} ngày trước"
    except Exception:
        return

    def _do():
        try:
            from v5.toast import show_toast
            show_toast(app,
                        f"👋 Chào mừng quay lại! Lần mở cuối: {txt}",
                        kind="info", duration=4)
        except Exception: pass

    app.after(2200, _do)


def _selftest() -> int:
    """Chạy `MEA_v5_alpha.exe --selftest` để verify module bundled hoạt động.

    KHÔNG mở GUI. Dùng v5.diagnostics → ghi file + in (nếu có console).
    Return 0 nếu các check bắt buộc pass; LaTeX/API key chưa cấu hình là thông
    tin tùy chọn cho bản cài mới. Dùng để CI / verify build.
    """
    try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

    from v5.diagnostics import run_diagnostics, format_report, release_checks_pass
    results = run_diagnostics()
    report = format_report(results)
    all_ok = release_checks_pass(results)

    # Ghi file TRƯỚC (windowed EXE: sys.stdout=None → print() crash sau đó).
    try:
        from pathlib import Path
        rf = Path.home() / ".exam_generator" / "selftest_result.txt"
        rf.parent.mkdir(parents=True, exist_ok=True)
        rf.write_text(report + "\n", encoding="utf-8")
    except Exception: pass
    # In ra stdout nếu có (console build) — guard vì windowed = None
    try:
        if sys.stdout is not None:
            print(report)
    except Exception: pass
    return 0 if all_ok else 1


class _NullWriter:
    """Dummy stdout/stderr cho windowed EXE — print() không crash khi None."""
    def write(self, *a, **k): return 0
    def flush(self, *a, **k): pass
    def isatty(self): return False


def _ensure_std_streams():
    """Windowed PyInstaller (console=False) đặt sys.stdout/stderr = None.
    Mọi print() trong app sẽ raise AttributeError. Gán dummy để an toàn.
    """
    if sys.stdout is None:
        sys.stdout = _NullWriter()
    if sys.stderr is None:
        sys.stderr = _NullWriter()


def _viewtest() -> int:
    """Dựng ModernApp + show_view từng view → ghi PASS/FAIL ra file.

    Bắt lỗi font/import xảy ra trong EXE đóng băng (vd 'Too early to use
    font'). Không mainloop — show_view tạo view đồng bộ.
    """
    _ensure_std_streams()
    results = []
    try:
        app = ModernApp()
        # Ép default_root (giống run())
        try:
            import tkinter as _tk
            _tk._default_root = app
        except Exception: pass
        # Viewtest verifies rendering, not entitlement. Authorize every V5
        # view explicitly, then assert navigation really reached each id.
        from config import get_default_features
        app._apply_license_state({
            "ok": True,
            "status": "active",
            "tier": "premium",
            "features": get_default_features("premium"),
        })
        for vid in ["home", "setup", "exam_create", "nhch", "convert",
                     "qc", "tracking", "guide"]:
            try:
                app.show_view(vid)
                cur = app._current_view
                kind = type(cur).__name__
                ok = (
                    app._current_view_id == vid
                    and kind not in ("_StubView", "_ErrorView")
                )
                results.append((vid, ok, kind))
            except Exception as e:
                results.append((vid, False, f"{type(e).__name__}: {e}"))
        try: app.destroy()
        except Exception: pass
    except Exception as e:
        results.append(("APP", False, f"{type(e).__name__}: {e}"))

    lines = ["=" * 52, "  MEA v5 — VIEW TEST", "=" * 52]
    all_ok = True
    for vid, ok, info in results:
        if not ok: all_ok = False
        lines.append(f"  [{'PASS' if ok else 'FAIL'}] {vid:12s} {str(info)[:60]}")
    lines.append("=" * 52)
    lines.append(f"  RESULT: {'ALL VIEWS OK' if all_ok else 'SOME FAILED'}")
    report = "\n".join(lines)
    try:
        from pathlib import Path
        rf = Path.home() / ".exam_generator" / "viewtest_result.txt"
        rf.parent.mkdir(parents=True, exist_ok=True)
        rf.write_text(report + "\n", encoding="utf-8")
    except Exception: pass
    try:
        if sys.stdout is not None: print(report)
    except Exception: pass
    return 0 if all_ok else 1


def run():
    """Entry point — show splash, init app, hide splash."""
    # An toàn print() trong windowed EXE (sys.stdout có thể = None)
    _ensure_std_streams()

    # Selftest mode (verify bundled modules) — không mở GUI
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    # Viewtest mode — dựng app + thử mở từng view (bắt lỗi font/import trong EXE)
    if "--viewtest" in sys.argv:
        sys.exit(_viewtest())

    # Alpha 22 fix (orphan root): Tạo app TRƯỚC + withdraw, dùng làm parent
    # cho splash → không sinh implicit tk root (cửa sổ trống thừa).
    app = ModernApp()
    try: app.withdraw()  # ẩn cho đến khi load xong
    except Exception: pass

    # FIX (EXE): set default_root = app trước khi splash tạo Toplevel
    try:
        import tkinter as _tk
        _tk._default_root = app
    except Exception: pass

    # Splash dùng app làm parent — không spawn orphan tk root
    splash = None
    try:
        from v5.splash import show_splash
        splash = show_splash(app)
        splash.set_status("Đang khởi tạo…", pct=10)
    except Exception as e:
        print(f"Splash fail (non-fatal): {e}")

    if splash:
        try: splash.set_status("Đang tạo cửa sổ chính…", pct=30)
        except Exception: pass

    if splash:
        try: splash.set_status("Đang cài crash handler…", pct=55)
        except Exception: pass

    # Cài crash reporter (sys.excepthook + threading.excepthook + tk callback)
    try:
        from v5.crash_reporter import install_crash_handlers
        install_crash_handlers(app,
                                show_dialog=_SETTINGS.get("crash_dialog", True))
    except Exception as e:
        print(f"Crash reporter install fail (non-fatal): {e}")

    if splash:
        try: splash.set_status("Đang kiểm tra update…", pct=75)
        except Exception: pass

    # Check phiên bản mới (async, 5s sau khi mở app — không chặn startup)
    try:
        from v5.updater import check_for_update_async
        check_for_update_async(app, delay_ms=5000)
    except Exception as e:
        print(f"Updater init fail (non-fatal): {e}")

    # Welcome toast — hiện thời gian từ lần mở cuối (sau splash 2s)
    try:
        _show_welcome_toast(app)
    except Exception as e:
        print(f"Welcome toast fail (non-fatal): {e}")

    # What's New dialog (auto-popup sau 3s nếu version thay đổi)
    try:
        from v5.whats_new import show_if_new_version
        show_if_new_version(app)
    except Exception as e:
        print(f"What's New popup fail (non-fatal): {e}")

    if splash:
        splash.set_status("Sẵn sàng!", pct=100)
        # Giữ splash ngắn 0.8s để user thấy được
        app.after(800, splash.finish)
        try: splash.update()
        except Exception: pass

    # Show app sau splash (Alpha 22 — app đã withdraw ở đầu)
    app.after(900, lambda: (app.deiconify(),
                              app.lift(),
                              app.focus_force()))

    # Onboarding wizard lần đầu mở
    if not _SETTINGS.get("onboarded"):
        from v5.onboarding import OnboardingWizard
        # Chờ splash đóng xong rồi mở onboarding (1s)
        app.after(1300, lambda: OnboardingWizard(app))

    app.mainloop()


if __name__ == "__main__":
    run()
