"""
ui/main_window.py — Shell chính: menu bar, notebook, kết nối tất cả các tab.
Chịu trách nhiệm: điều phối luồng generate, autosave, session restore.
Không chứa business logic — chỉ wiring.
"""

from __future__ import annotations
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional

# Module logger — ghi các lỗi không block UI (autosave, restore...) ra app.log
_log = logging.getLogger(__name__)

from config import APP_DIR, SESSION_DIR, AI_PROVIDERS, FEATURE_CATALOG, get_default_features, APP_VERSION
from core.models import MatrixData, MatrixRow, ExamData, Question
from core.generator import generate_all
from services.ai_service import create_ai_service
from services.cache_service import CacheService
from storage.database import (
    save_questions, save_session, load_session,
    list_recent_sessions, autosave_session,
)
from ui.tab_config import TabConfig
from ui.tab_matrix import TabMatrix
# Lazy-loaded tabs — chỉ import khi user thực sự click vào tab đó
# from ui.tab_result import TabResult
# from ui.tab_bank   import TabBank
# from ui.tab_qc     import TabQC
# from ui.tab_tikz import TabTikZ
# from ui.tab_convert import TabConvert
# from ui.tab_history import TabHistory
# from ui.tab_about  import TabAbout
# from ui.tab_user_info import TabUserInfo
# from ui.tab_guide  import TabGuide
from storage.smart_db import smart_db_init, smart_save, log_feedback, smart_stats
from core.json_generator import generate_with_json_prompt
from services.cross_model import cross_model_pipeline
from services.adaptive_prompt import build_adaptive_prefix, extract_patterns_from_feedback
from services.prompt_manager import bootstrap_default_prompts, list_prompts, set_active_prompt, load_prompt
from services.logger import get_logger as _app_logger, get_monitor_stats


class MainWindow(tk.Tk):
    """Cửa sổ chính của ứng dụng."""

    def __init__(self, license_result: dict | None = None):
        super().__init__()
        self.title("🎓 Tạo đề kiểm tra bằng AI [Phần mềm được tạo bởi 👉Đỗ Miinh Math👈 nhằm phục vụ nhu cầu giảng dạy và học tập].")
        self.geometry("1080x820")
        self.minsize(860, 600)
        self.configure(bg="#F8FAFC") # Nền sáng hiện đại

        # ── Feature gating từ license (Bản mở khóa toàn bộ tính năng) ───────
        lr = license_result or {}
        self._tier = "premium"
        self._license_info = lr
        self._features: dict[str, bool] = get_default_features("premium")

        # ── Icon cửa sổ + taskbar ────────────────────────────────────────
        try:
            from pathlib import Path as _P
            for _ico_name in ("app.ico", "icon_app.ico"):
                _ico = _P(__file__).parent.parent / "assets" / _ico_name
                if _ico.exists():
                    self.iconbitmap(default=str(_ico))
                    break
        except Exception:
            pass

        # ── Application state ─────────────────────────────────────────────
        self._matrix_data:          Optional[MatrixData] = None
        self._exam_data:            Optional[ExamData]   = None
        self._current_session_path: Optional[str]        = None
        self._cache = CacheService()

        # Event hủy generation — set() để dừng batch sớm. Worker
        # `_do_gen` truyền event này vào generate_all(). UI có thể gọi
        # `cancel_generation()` để set event.
        self._gen_cancel_event = threading.Event()
        # Lock bảo vệ truy cập `_exam_data` từ nhiều chỗ. Hiện tại mọi
        # assignment đều chạy trên UI thread (qua `self.after`), nhưng
        # giữ lock cho defensive + tương lai có access từ thread khác.
        self._exam_data_lock = threading.RLock()

        # ── YC7: UI theme ────────────────────────────────────────────────
        self._apply_theme()

        # ── Build UI ──────────────────────────────────────────────────────
        # Thanh trạng thái pack trước (side=bottom) để vùng giữa còn chỗ cho notebook.
        self._build_statusbar()
        self._build_header(license_result)
        self._build_progress_panel()
        self._build_notebook()
        self._build_menu()
        self._check_deps()
        self._setup_global_mousewheel()

        # ── Áp dụng feature gates ────────────────────────────────────────
        self._apply_feature_gates()

        # ── Kiểm tra hạn dùng định kỳ (mỗi 5 phút) ───────────────────
        self._license_locked = False
        self._schedule_license_recheck()

        # ── Memory management: cleanup khi đóng app ──────────────────
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        # Periodic cache cleanup (mỗi 10 phút)
        self._schedule_memory_cleanup()

        # [FRICTION-5] Auto-save session mỗi 60s + check restore on startup
        self._last_autosave_hash: str = ""
        self.after(self._AUTOSAVE_INTERVAL_MS, self._schedule_periodic_autosave)
        # Defer check restore ~2s — sau khi UI ổn định + tab_history loaded
        self.after(2000, self._check_autosave_on_startup)

    def _on_close(self) -> None:
        """Cleanup tài nguyên trước khi đóng app."""
        try:
            # Đóng DB connections
            from storage.database import close_db
            close_db()
        except Exception:
            pass
        try:
            # Xóa L1 cache (giải phóng RAM)
            self._cache.clear_memory()
        except Exception:
            pass
        try:
            import gc
            gc.collect()
        except Exception:
            pass
        self.destroy()

    def _schedule_memory_cleanup(self) -> None:
        """Periodic cleanup: xóa cache L1 cũ, garbage collect mỗi 10 phút."""
        def _cleanup():
            try:
                import gc
                gc.collect()
            except Exception:
                pass
        import threading
        threading.Thread(target=_cleanup, daemon=True).start()
        self.after(10 * 60 * 1000, self._schedule_memory_cleanup)

    # ──────────────────────────────────────────────────────────────────────
    #  [FRICTION-5] Auto-save session mỗi 60s
    # ──────────────────────────────────────────────────────────────────────

    _AUTOSAVE_INTERVAL_MS = 60 * 1000   # 60 giây
    _AUTOSAVE_MIN_AGE_DAYS = 1          # khi mở app: chỉ suggest restore nếu < 1 ngày

    def _schedule_periodic_autosave(self) -> None:
        """[FRICTION-5] Auto-save mỗi 60s nếu có thay đổi từ lần snap trước.

        Chỉ chạy khi có _exam_data hoặc _matrix_data. KHÔNG show dialog
        (tránh spam) — chỉ update _session_lbl ở status bar.
        """
        try:
            self._do_periodic_autosave()
        except Exception as e:
            _log.debug("Periodic autosave skipped: %s", e)
        # Reschedule
        self.after(self._AUTOSAVE_INTERVAL_MS, self._schedule_periodic_autosave)

    def _do_periodic_autosave(self) -> None:
        """Thực hiện 1 vòng autosave — check hash thay đổi trước."""
        # Bỏ qua nếu không có data nào
        if not (self._exam_data or self._matrix_data):
            return

        # Hash state hiện tại để detect thay đổi
        try:
            cur_hash = self._compute_session_hash()
        except Exception:
            cur_hash = None

        last_hash = getattr(self, "_last_autosave_hash", None)
        if cur_hash and cur_hash == last_hash:
            # Không có thay đổi → skip để khỏi spam file
            return

        # Thực hiện autosave (không block UI — autosave_session sync nhưng nhanh)
        try:
            self._session_autosave()
            self._last_autosave_hash = cur_hash
        except Exception as e:
            _log.warning("Periodic autosave failed: %s", e)

    def _compute_session_hash(self) -> str:
        """Hash gọn của exam_data + matrix_data để detect thay đổi."""
        import hashlib, json
        parts = []
        try:
            if self._exam_data is not None:
                parts.append("exam:" + json.dumps(
                    self._exam_data.to_dict(),
                    ensure_ascii=False, sort_keys=True, default=str,
                )[:50000])  # truncate cho speed
        except Exception:
            pass
        try:
            if self._matrix_data is not None:
                parts.append("matrix:" + json.dumps(
                    self._matrix_data.to_dict(),
                    ensure_ascii=False, sort_keys=True, default=str,
                )[:50000])
        except Exception:
            pass
        if not parts:
            return ""
        return hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()[:16]

    def _check_autosave_on_startup(self) -> None:
        """[FRICTION-5] Tìm autosave gần đây + show toast suggest restore.

        Chỉ trigger khi:
          - Có file autosave_*.json trong SESSION_DIR < _AUTOSAVE_MIN_AGE_DAYS
          - User chưa mở session khác manually
          - Chưa có _exam_data đang load
        """
        if self._exam_data or self._matrix_data:
            return  # đã có data đang work — không restore

        try:
            from config import SESSION_DIR
            import datetime
            now = datetime.datetime.now()
            cutoff = now - datetime.timedelta(days=self._AUTOSAVE_MIN_AGE_DAYS)

            # Tìm autosave gần nhất
            candidates = []
            for f in SESSION_DIR.glob("autosave_*.json"):
                try:
                    mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime > cutoff:
                        candidates.append((mtime, f))
                except Exception:
                    continue
            if not candidates:
                return

            # Lấy file mới nhất
            candidates.sort(reverse=True)
            mtime, latest = candidates[0]
        except Exception as e:
            _log.debug("Autosave scan failed: %s", e)
            return

        # Show toast
        try:
            from ui.toast import Toast
        except Exception:
            return

        # Format thời gian friendly
        delta = (now - mtime)
        if delta.total_seconds() < 60:
            time_str = "vài giây trước"
        elif delta.total_seconds() < 3600:
            time_str = f"{int(delta.total_seconds() // 60)} phút trước"
        elif delta.total_seconds() < 86400:
            time_str = f"{int(delta.total_seconds() // 3600)} giờ trước"
        else:
            time_str = f"{delta.days} ngày trước"

        def _do_restore():
            try:
                from storage.database import load_session
                data = load_session(str(latest))
                self._restore_session(data)
                self._current_session_path = str(latest)
                self._set_status(f"📂 Đã khôi phục autosave: {latest.name}")
            except Exception as e:
                messagebox.showerror("Lỗi khôi phục", str(e))

        def _ignore():
            pass  # Toast tự đóng

        try:
            Toast(
                self,
                title="💾 Tìm thấy autosave gần đây",
                message=(
                    f"File: {latest.name}\n"
                    f"Lưu lúc: {time_str}\n\n"
                    f"Bạn có muốn khôi phục phiên làm việc gần nhất?"
                ),
                actions=[
                    ("📂 Khôi phục", _do_restore),
                    ("Bỏ qua", _ignore),
                ],
                duration_ms=20000,
                variant="info",
            ).show()
        except Exception as e:
            _log.debug("Toast restore show failed: %s", e)

    def _init_tabs(self) -> None:
        """Khởi tạo các tab — TRUE LAZY LOADING.

        Tab Config + Matrix được tải ngay (cần thiết cho UX đầu tiên).
        Các tab còn lại CHỈ TẠO KHI USER CLICK vào tab đó lần đầu.
        → Giảm startup time 60-80%, giảm RAM ban đầu.
        """
        nb = self._nb

        # ── Tabs cần thiết ngay lập tức ──
        self._tab_config = TabConfig(
            nb,
            on_matrix_loaded=self._on_matrix_loaded,
            license_info=self._license_info,
        )
        self._tab_matrix = TabMatrix(
            nb,
            on_export_matrix=self._export_current_matrix,
            get_subject_grade=lambda: (
                self._tab_config.get_subject(),
                self._tab_config.get_grade(),
            ),
        )
        # Khi user load template → cập nhật ExamData (title + time_str)
        self._tab_matrix.set_matrix_loaded_callback(self._on_template_loaded)

        # ── Lazy tabs: chỉ tạo placeholder frame, load thực khi click ──
        self._lazy_tab_defs = {
            "tab_result":    self._create_tab_result,
            "tab_shuffle":   self._create_tab_shuffle,
            "tab_bank":      self._create_tab_bank,
            "tab_qc":        self._create_tab_qc,
            "tab_tikz":      self._create_tab_tikz,
            "tab_convert":   self._create_tab_convert,
            "tab_ai_usage":  self._create_tab_ai_usage,
            "tab_history":   self._create_tab_history,
            "tab_about":     self._create_tab_about,
            "tab_user_info": self._create_tab_user_info,
            "tab_guide":     self._create_tab_guide,
        }
        self._lazy_loaded: set[str] = set()

        # Tạo placeholder frames cho mỗi lazy tab
        import tkinter as tk
        for key in self._lazy_tab_defs:
            placeholder = ttk.Frame(nb)
            # Loading indicator cho placeholder
            loading_lbl = tk.Label(
                placeholder, text="⏳ Đang tải...",
                font=("Segoe UI", 12), fg="#64748B", bg="#F8FAFC",
            )
            loading_lbl.place(relx=0.5, rely=0.5, anchor="center")
            setattr(self, f"_{key}", placeholder)
            setattr(self, f"_{key}_loading_lbl", loading_lbl)

    # ── Lazy tab factory methods ────────────────────────────────────────────

    def _replace_lazy_tab(self, attr_name: str, new_tab, select: bool = True) -> None:
        """Thay thế placeholder tab bằng tab thực. An toàn với concurrent lazy loading."""
        nb = self._nb
        old = getattr(self, attr_name)
        try:
            tab_text = nb.tab(old, "text")
            tab_state = nb.tab(old, "state")
            # Insert tab mới ngay TRƯỚC placeholder (dùng widget ref, không dùng index số)
            nb.insert(old, new_tab, text=tab_text, state=tab_state)
            # Xóa placeholder
            nb.forget(old)
            old.destroy()
        except Exception:
            # Fallback: thêm vào cuối
            nb.add(new_tab, text=getattr(new_tab, "_tab_text", attr_name))
        setattr(self, attr_name, new_tab)
        if select:
            try:
                nb.select(new_tab)
            except Exception:
                pass

    def _create_tab_result(self) -> None:
        from ui.tab_result import TabResult
        new_tab = TabResult(
            self._nb,
            get_ai_call=self._make_ai_call,
            get_subject_grade=lambda: (
                self._tab_config.get_subject(),
                self._tab_config.get_grade(),
            ),
        )
        self._replace_lazy_tab("_tab_result", new_tab)

    def _create_tab_shuffle(self) -> None:
        from ui.tab_shuffle import TabShuffle
        new_tab = TabShuffle(
            self._nb,
            get_exam_data=lambda: self._exam_data,
            on_status_change=self._set_status,
            get_ai_call=self._make_ai_call,
        )
        self._replace_lazy_tab("_tab_shuffle", new_tab)

    def _create_tab_bank(self) -> None:
        from ui.tab_bank import TabBank
        new_tab = TabBank(
            self._nb,
            get_ai_call=self._make_ai_call,
            get_subject_grade=lambda: (
                self._tab_config.get_subject(),
                self._tab_config.get_grade(),
            ),
            on_add_to_exam_cb=self._add_q_to_exam,
        )
        self._replace_lazy_tab("_tab_bank", new_tab)

    def _create_tab_qc(self) -> None:
        from ui.tab_qc import TabQC
        new_tab = TabQC(
            self._nb,
            get_ai_call=self._make_ai_call,
            get_subject_grade=lambda: (
                self._tab_config.get_subject(),
                self._tab_config.get_grade(),
            ),
            get_exam_data=lambda: self._exam_data,
        )
        self._replace_lazy_tab("_tab_qc", new_tab)

    def _create_tab_tikz(self) -> None:
        from ui.tab_tikz import TabTikZ
        new_tab = TabTikZ(self._nb, get_ai_call=self._make_ai_call)
        self._replace_lazy_tab("_tab_tikz", new_tab)

    def _create_tab_convert(self) -> None:
        from ui.tab_convert import TabConvert
        new_tab = TabConvert(
            self._nb,
            get_ai_call=self._make_ai_call,
            get_subject_grade=lambda: (
                self._tab_config.get_subject(),
                self._tab_config.get_grade(),
            ),
            # [SMART-1] Callback áp dụng auto-detected môn/lớp từ Vision
            on_apply_detected_meta=self._apply_detected_meta,
        )
        self._replace_lazy_tab("_tab_convert", new_tab)
        # Ctrl+V phải bind SAU khi tab thực được tạo — bind sớm (lúc init)
        # KHÔNG dùng được vì _tab_convert lúc đó còn là placeholder Frame
        # (lazy-load), không có method bind_shortcuts.
        try:
            new_tab.bind_shortcuts(self)
        except Exception as e:
            print(f"[WARNING] bind_shortcuts failed: {e}")

    def _create_tab_history(self) -> None:
        from ui.tab_history import TabHistory
        new_tab = TabHistory(
            self._nb,
            on_load_session=lambda data, path: (
                self._restore_session(data),
                setattr(self, "_current_session_path", path),
            ),
        )
        self._replace_lazy_tab("_tab_history", new_tab)

    def _create_tab_about(self) -> None:
        from ui.tab_about import TabAbout
        new_tab = TabAbout(self._nb)
        self._replace_lazy_tab("_tab_about", new_tab)

    def _create_tab_ai_usage(self) -> None:
        from ui.tab_ai_usage import TabAIUsage
        new_tab = TabAIUsage(self._nb)
        self._replace_lazy_tab("_tab_ai_usage", new_tab)

    def _create_tab_user_info(self) -> None:
        from ui.tab_user_info import TabUserInfo
        new_tab = TabUserInfo(self._nb, license_info=self._license_info)
        self._replace_lazy_tab("_tab_user_info", new_tab)

    def _create_tab_guide(self) -> None:
        from ui.tab_guide import TabGuide
        new_tab = TabGuide(self._nb)
        self._replace_lazy_tab("_tab_guide", new_tab)

    def _on_tab_changed(self, event) -> None:
        """Handler: khi user click vào tab → lazy-load nếu chưa tạo."""
        try:
            sel = self._nb.select()
            widget = self.nametowidget(sel)
        except Exception:
            return

        # Tìm tab key tương ứng
        tab_keys = [
            "tab_result", "tab_shuffle", "tab_bank", "tab_qc", "tab_tikz",
            "tab_convert", "tab_ai_usage", "tab_history", "tab_about",
            "tab_user_info", "tab_guide",
        ]
        for key in tab_keys:
            if widget is getattr(self, f"_{key}", None) and key not in self._lazy_loaded:
                creator = self._lazy_tab_defs.get(key)
                if creator:
                    self._lazy_loaded.add(key)
                    try:
                        creator()
                    except Exception as e:
                        import traceback
                        tb = traceback.format_exc()
                        _log.error("Lazy load %s failed:\n%s", key, tb)
                        print(f"[ERROR] Lazy load {key} failed: {e}\n{tb}")
                        self._lazy_loaded.discard(key)
                        lbl = getattr(self, f"_{key}_loading_lbl", None)
                        if lbl:
                            try:
                                lbl.config(
                                    text=f"❌ Không thể tải tab này:\n{e}\n\n(Nhấn lại tab để thử lại)",
                                    fg="#DC2626",
                                    justify="center",
                                )
                            except Exception:
                                pass
                break

    # ══════════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════════════════
    #  THEME — delegated to ui/theme.py for consistency
    # ══════════════════════════════════════════════════════════════════════════════

    def _apply_theme(self) -> None:
        """Apply modern theme from ui/theme.py."""
        from ui.theme import apply_ttk_theme
        style = ttk.Style(self)
        apply_ttk_theme(style)

    #  FEATURE GATING
    # ══════════════════════════════════════════════════════════════════════

    def _is_feature_enabled(self, key: str) -> bool:
        return True

    def _apply_feature_gates(self) -> None:
        tab_map = {
            "tab_matrix":    (self._tab_matrix,    "📋  Bảng câu hỏi"),
            "tab_result":    (self._tab_result,    "📄  Xem đề & Xuất file"),
            "tab_bank":      (self._tab_bank,      "🏦  Ngân hàng câu hỏi"),
            "tab_qc":        (self._tab_qc,        "✅  Kiểm tra chất lượng"),
            "tab_tikz":      (self._tab_tikz,       "📐  TikZ vẽ hình"),
            "tab_convert":   (self._tab_convert,    "🔄  Convert"),
            "tab_history":   (self._tab_history,    "🕐  Lịch sử"),
        }
        for feat_key, (widget, label) in tab_map.items():
            try:
                self._nb.tab(widget, state="normal", text=label)
            except Exception:
                pass

        try:
            self._quick_btn.config(state="normal", bg="#F59E0B", fg="white")
        except Exception:
            pass

        # Feature gates cho lazy tabs: chỉ apply nếu đã load thực
        for tab_key in ("tab_result", "tab_bank", "tab_qc"):
            if tab_key in getattr(self, "_lazy_loaded", set()):
                tab = getattr(self, f"_{tab_key}", None)
                if tab and hasattr(tab, "apply_feature_gates"):
                    tab.apply_feature_gates(self._features)

    # ══════════════════════════════════════════════════════════════════════
    #  AUTO LICENSE RECHECK (mỗi 5 phút)
    # ══════════════════════════════════════════════════════════════════════

    def _schedule_license_recheck(self) -> None:
        """Lên lịch kiểm tra hạn dùng mỗi 5 phút (an toàn, không khóa app)."""
        self._do_license_recheck()
        self.after(5 * 60 * 1000, self._schedule_license_recheck)

    def _do_license_recheck(self) -> None:
        """Kiểm tra hạn dùng: bản mở khóa luôn duy trì trạng thái hoạt động."""
        import threading

        def _check():
            try:
                from services.license_manager import check_license
                result = check_license(force_online=False)
                self.after(0, lambda: self._handle_recheck_result(result))
            except Exception:
                pass  # Lỗi mạng/DB → giữ nguyên trạng thái mở khóa

        threading.Thread(target=_check, daemon=True).start()

    def _handle_recheck_result(self, result: dict) -> None:
        """Xử lý kết quả kiểm tra hạn dùng: luôn đảm bảo mở khóa đầy đủ."""
        self._features = get_default_features("premium")
        self._tier = "premium"
        if self._license_locked:
            self._license_locked = False
            self._unlock_app()
        else:
            self._apply_feature_gates()

    def _lock_app(self, message: str) -> None:
        """Bản mở khóa: không khóa ứng dụng khi database gặp lỗi."""
        pass

    def _unlock_app(self) -> None:
        """Mở khóa app sau khi admin gia hạn."""
        try:
            self._gen_btn.config(state="normal", bg="#10B981", fg="white")
            self._quick_btn.config(state="normal", bg="#F59E0B", fg="white")
        except Exception:
            pass

        # Re-enable tất cả tab trước, rồi apply feature gates lại
        all_tab_keys = ("tab_matrix", "tab_result", "tab_bank", "tab_qc",
                        "tab_tikz", "tab_convert", "tab_history")
        for tab_key in all_tab_keys:
            tab = getattr(self, f"_{tab_key}", None)
            if tab:
                try:
                    # Xóa icon khóa khỏi text
                    old_text = self._nb.tab(tab, "text")
                    clean_text = old_text.replace("🔒", "")
                    self._nb.tab(tab, text=clean_text, state="normal")
                except Exception:
                    pass

        self._apply_feature_gates()
        self._set_status("✅ Giấy phép đã được gia hạn — sẵn sàng sử dụng")

    # ══════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════

    def _build_header(self, license_result: dict | None = None) -> None:
        # Nền xanh dương sáng — hiện đại, thoáng
        hdr_bg = "#E0F2FE"
        hdr_fg = "#0C4A6E"          # text chính (xanh đậm)
        hdr_fg_sub = "#0369A1"      # text phụ

        # ── Top accent stripe (brand color) ──
        tk.Frame(self, bg="#0EA5E9", height=4).pack(fill="x")

        # ── Main header bar (đủ cao để badge + hàng nút + progress không bị cắt) ──
        hdr = tk.Frame(self, bg=hdr_bg, height=100)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Left: Logo + Title
        left = tk.Frame(hdr, bg=hdr_bg)
        left.pack(side="left", padx=0, pady=0, fill="y")

        try:
            from PIL import Image, ImageTk
            from pathlib import Path
            for _ico_name in ("app.png", "icon4.png"):
                _logo_path = Path(__file__).parent.parent / "assets" / _ico_name
                if _logo_path.exists():
                    _img = Image.open(_logo_path).convert("RGBA").resize((40, 40), Image.LANCZOS)
                    self._logo_photo = ImageTk.PhotoImage(_img)
                    tk.Label(left, image=self._logo_photo, bg=hdr_bg).pack(
                        side="left", pady=10, padx=10)
                    break
            else:
                raise FileNotFoundError()
        except Exception:
            tk.Label(left, text="📐", bg=hdr_bg, fg="#0EA5E9",
                    font=("Segoe UI", 22)).pack(side="left", pady=10, padx=8)

        title_col = tk.Frame(left, bg=hdr_bg)
        title_col.pack(side="left", pady=10)
        tk.Label(title_col, text="MatrixExamAI",
                bg=hdr_bg, fg=hdr_fg,
                font=("Segoe UI", 16, "bold"),
                anchor="w").pack(anchor="w")
        tk.Label(title_col, text="Tạo đề kiểm tra THCS/THPT bằng AI",
                bg=hdr_bg, fg=hdr_fg_sub,
                font=("Segoe UI", 9),
                anchor="w").pack(anchor="w")

        # ── Right: badge trên, nút tác vụ giữa, progress dưới (không chồng lên nhau) ──
        right = tk.Frame(hdr, bg=hdr_bg)
        right.pack(side="right", padx=12, fill="y", pady=10)

        tier = self._tier
        tier_colors = {"basic": "#64748B", "pro": "#0284C7", "premium": "#8B5CF6"}
        tier_bg = tier_colors.get(tier, "#64748B")
        tier_icons = {"basic": "🥉", "pro": "🥈", "premium": "🏆"}
        tk.Label(right, text=f"  {tier_icons.get(tier,'🥉')} {tier.upper()}  ",
                bg=tier_bg, fg="white",
                font=("Segoe UI", 9, "bold"),
                padx=10, pady=4).pack(side="top", anchor="e")

        btn_row = tk.Frame(right, bg=hdr_bg)
        btn_row.pack(side="top", anchor="e", pady=(6, 4))

        # ── [SPEED-5] Nút "📂 Mở lại" — dropdown 5 phiên gần nhất ───────
        # Đặt đầu btn_row để user thấy ngay khi mở app + dễ scan.
        self._recent_btn = tk.Button(
            btn_row, text="📂 Mở lại ▾",
            bg="#475569", fg="white", activebackground="#334155",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", bd=0,
            padx=10, pady=6,
            command=self._toggle_recent_dropdown,
        )
        self._recent_btn.pack(side="left", padx=3)
        self._recent_dropdown = None  # init lazy

        self._quick_btn = tk.Button(
            btn_row, text="⚡ Tạo đề nhanh",
            bg="#F59E0B", fg="white", activebackground="#D97706",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", bd=0,
            padx=12, pady=6, command=self._open_quick_gen)
        self._quick_btn.pack(side="left", padx=3)

        self._ai_matrix_btn = tk.Button(
            btn_row, text="🤖 Tạo ma trận AI",
            bg="#7C3AED", fg="white", activebackground="#6D28D9",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", bd=0,
            padx=12, pady=6, command=self._open_ai_gen_matrix)
        self._ai_matrix_btn.pack(side="left", padx=3)

        self._smart_btn = tk.Button(
            btn_row, text="💬 Smart Prompt",
            bg="#8B5CF6", fg="white", activebackground="#7C3AED",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", bd=0,
            padx=12, pady=6, command=self._open_smart_prompt)
        self._smart_btn.pack(side="left", padx=3)

        self._src_btn = tk.Button(
            btn_row, text="🎯 Nguồn tạo đề",
            bg="#0284C7", fg="white", activebackground="#0369A1",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", bd=0,
            padx=12, pady=6, command=self._choose_source)
        self._src_btn.pack(side="left", padx=3)

        self._gen_btn = tk.Button(
            btn_row, text="✨ Tạo đề bằng AI",
            bg="#10B981", fg="white", activebackground="#059669",
            font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2", bd=0,
            padx=14, pady=6, command=self._start_generation)
        self._gen_btn.pack(side="left", padx=3)

        self._shuffle_btn = tk.Button(
            btn_row, text="🎲 Trộn đề thi",
            bg="#0284C7", fg="white", activebackground="#0369A1",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2", bd=0,
            padx=12, pady=6, command=self._switch_to_shuffle_tab)
        self._shuffle_btn.pack(side="left", padx=3)

        prog = tk.Frame(right, bg=hdr_bg)
        prog.pack(side="top", anchor="e", pady=(2, 0))
        self._progress_lbl = tk.Label(prog, text="",
                                     bg=hdr_bg, fg="#64748B",
                                     font=("Segoe UI", 8))
        self._progress_lbl.pack(side="left", padx=8)
        self._progress_bar = ttk.Progressbar(prog, mode="indeterminate", length=140)
        self._progress_bar.pack(side="left")
        self._progress_time_lbl = tk.Label(
            prog, text="", bg="#FFFFFF", fg="#0C4A6E",
            font=("Segoe UI", 8, "bold"), padx=6, pady=1,
        )
        self._progress_time_lbl.pack(side="left", padx=(8, 0))

        self._source_mode  = "ai_only"
        self._source_ratio = 50

    # ══════════════════════════════════════════════════════════════════════
    #  PROGRESS PANEL — thanh tiến độ chi tiết khi tạo đề
    # ══════════════════════════════════════════════════════════════════════

    def _build_progress_panel(self) -> None:
        """Progress panel nằm giữa header và notebook, ẩn khi không tạo đề."""
        import time as _time
        self._gen_start_time = 0.0
        self._prog_panel_min_height = 96
        self._prog_panel_max_height = 140

        panel = tk.Frame(self, bg="#EFF6FF", height=0)
        panel.pack(fill="x")
        panel.pack_propagate(False)
        self._prog_panel = panel

        inner = tk.Frame(panel, bg="#EFF6FF")
        inner.pack(fill="x", padx=16, pady=(8, 10))
        self._prog_inner = inner

        # Row 1: status text + percentage + elapsed
        row1 = tk.Frame(inner, bg="#EFF6FF")
        row1.pack(fill="x", pady=(0, 2))
        row1.grid_columnconfigure(0, weight=1)

        self._prog_status = tk.Label(
            row1, text="Đang tạo đề…", bg="#EFF6FF", fg="#0C4A6E",
            font=("Segoe UI", 10, "bold"), anchor="w")
        self._prog_status.grid(row=0, column=0, sticky="w")

        self._prog_pct = tk.Label(
            row1, text="0%", bg="#EFF6FF", fg="#0284C7",
            font=("Segoe UI", 10, "bold"), anchor="e")
        self._prog_pct.grid(row=0, column=1, sticky="e", padx=(12, 14))

        self._prog_elapsed = tk.Label(
            row1, text="", bg="#EFF6FF", fg="#64748B",
            font=("Segoe UI", 9), anchor="e")
        self._prog_elapsed.grid(row=0, column=2, sticky="e")

        # Row 2: determinate progress bar (custom canvas)
        bar_frame = tk.Frame(inner, bg="#CBD5E1", height=10)
        bar_frame.pack(fill="x", pady=(6, 5))

        self._prog_canvas = tk.Canvas(
            bar_frame, height=10, bg="#CBD5E1",
            highlightthickness=0, bd=0)
        self._prog_canvas.pack(fill="x")
        self._prog_bar_id = None

        # Row 3: detail text (topic being generated)
        self._prog_detail = tk.Label(
            inner, text="", bg="#EFF6FF", fg="#64748B",
            font=("Segoe UI", 9), anchor="w", justify="left")
        self._prog_detail.pack(fill="x", pady=(1, 0))

    def _sync_progress_panel_layout(self) -> None:
        """Resize progress panel so status/detail text is never vertically clipped."""
        try:
            if int(self._prog_panel.cget("height")) <= 0:
                return

            panel_w = max(520, self._prog_panel.winfo_width())
            detail_w = max(360, panel_w - 64)
            self._prog_detail.configure(wraplength=detail_w)
            self._prog_inner.update_idletasks()
            required = self._prog_inner.winfo_reqheight() + 20
            height = max(
                self._prog_panel_min_height,
                min(self._prog_panel_max_height, required),
            )
            self._prog_panel.configure(height=height)
        except Exception:
            self._prog_panel.configure(height=self._prog_panel_min_height)

    def _show_progress_panel(self) -> None:
        import time as _time
        self._gen_start_time = _time.time()
        self._prog_panel.configure(height=self._prog_panel_min_height)
        self._prog_status.configure(text="⏳ Đang khởi tạo…")
        self._prog_pct.configure(text="0%")
        self._prog_detail.configure(text="")
        self._prog_elapsed.configure(text="")
        self._progress_time_lbl.configure(text="")
        self._runtime_var.set("")
        self._update_progress_bar(0)
        self.after_idle(self._sync_progress_panel_layout)
        self._tick_elapsed()

    def _hide_progress_panel(self) -> None:
        self._prog_panel.configure(height=0)
        self._progress_time_lbl.configure(text="")
        self._runtime_var.set("")

    def _update_progress_bar(self, fraction: float) -> None:
        """Update the determinate progress bar (0.0 → 1.0)."""
        c = self._prog_canvas
        c.delete("bar")
        c.update_idletasks()
        w = c.winfo_width()
        if w < 2:
            w = 600
        fill_w = max(0, int(w * fraction))
        if fill_w > 0:
            # Gradient effect: lighter left, primary right
            c.create_rectangle(0, 0, fill_w, 12, fill="#0284C7",
                               outline="", tags="bar")
            # Glow at tip
            if fill_w > 4:
                c.create_rectangle(fill_w - 4, 0, fill_w, 12,
                                   fill="#0EA5E9", outline="", tags="bar")

    def _update_gen_progress(self, done: int, total: int, topic: str) -> None:
        """Called from progress_cb on the main thread."""
        frac = done / total if total > 0 else 0
        pct = int(frac * 100)

        self._prog_status.configure(text=f"🔄 Đang tạo câu {done}/{total}")
        self._prog_pct.configure(text=f"{pct}%")
        detail = (topic or "").strip()
        self._prog_detail.configure(text=f"📝 {detail}" if detail else "")
        self._update_progress_bar(frac)
        self.after_idle(self._sync_progress_panel_layout)

        # Also update header label
        self._progress_lbl.config(text=f"[{done}/{total}]")

    def _tick_elapsed(self) -> None:
        """Update elapsed time every second while progress panel is visible."""
        import time as _time
        if self._prog_panel.cget("height") == 0:
            return
        if self._gen_start_time <= 0:
            return
        elapsed = _time.time() - self._gen_start_time
        m, s = divmod(int(elapsed), 60)
        tstr = f"⏱ {m:02d}:{s:02d}"
        self._prog_elapsed.configure(text=tstr)
        self._progress_time_lbl.configure(text=tstr)
        self._runtime_var.set(f"Đang tạo đề  {tstr}")
        self.after(1000, self._tick_elapsed)

    def _build_notebook(self) -> None:
        # ── Tab bar with light background ──
        nb_frm = tk.Frame(self, bg="#E2E8F0")
        nb_frm.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self._nb = ttk.Notebook(nb_frm)
        self._nb.pack(fill="both", expand=True, padx=2, pady=2)

        # Tab widgets phải là con của Notebook (không phải Tk gốc) mới hiển thị đúng trên Windows.
        self._init_tabs()

        # Design: icon + label, compact tabs
        tabs = [
            ("⚙️", "Cài đặt"),
            ("📋", "Câu hỏi"),
            ("📄", "Xuất đề"),
            ("🎲", "Trộn đề"),
            ("🏦", "Ngân hàng"),
            ("✅", "Chất lượng"),
            ("📐", "Vẽ hình"),
            ("🔄", "Convert"),
            ("📊", "AI Usage"),
            ("🕐", "Lịch sử"),
            ("🪪", "Giới thiệu"),
            ("👤", "Người dùng"),
            ("📚", "Hướng dẫn"),
        ]
        tab_widgets = [
            self._tab_config, self._tab_matrix, self._tab_result,
            self._tab_shuffle,
            self._tab_bank, self._tab_qc, self._tab_tikz,
            self._tab_convert,
            self._tab_ai_usage,
            self._tab_history,
            self._tab_about, self._tab_user_info, self._tab_guide,
        ]
        for (icon, label), widget in zip(tabs, tab_widgets):
            self._nb.add(widget, text=f" {icon} {label} ")

        # ── Lazy tab loading: bind tab-change event ──
        self._nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # ── Deferred init: chạy background thay vì block startup ──
        import threading
        def _deferred_init():
            try:
                smart_db_init()
            except Exception as e:
                _log.error("smart_db_init failed: %s", e, exc_info=True)
            try:
                bootstrap_default_prompts()
            except Exception as e:
                _log.error("bootstrap_default_prompts failed: %s", e, exc_info=True)
            try:
                _app_logger().info('App started')
            except Exception as e:
                _log.debug("app logger info failed: %s", e)
            # P1.5: pre-render thumbnail cho KB templates (chạy nền — không block UI)
            try:
                self._preload_kb_thumbnails()
            except Exception as e:
                _log.debug("preload_kb_thumbnails failed: %s", e)
        threading.Thread(target=_deferred_init, daemon=True).start()

    def _preload_kb_thumbnails(self):
        """Pre-render thumbnail cho KB templates chưa có cache.
        Chạy SAU khi UI đã sẵn sàng — chậm không sao vì đã ở background."""
        try:
            from services import tikz_kb, tikz_thumbnail
        except Exception:
            return

        # Load KB nếu chưa
        try:
            tikz_kb.load()
        except Exception:
            return

        # Filter: chỉ render những template CHƯA có thumbnail
        all_tpls = tikz_kb.all_templates()
        to_render = [tpl.code for tpl in all_tpls
                     if not tikz_thumbnail.has_thumb(tpl.code)]
        if not to_render:
            _log.info("KB thumbnails: tất cả đã cache (%d templates)",
                      len(all_tpls))
            return

        _log.info("KB thumbnails: pre-render %d/%d (background)",
                  len(to_render), len(all_tpls))

        def _on_progress(done, total, name):
            # Update statusbar nếu có
            try:
                self._set_status(f"🎨 Pre-render thumbnail: {done}/{total}")
            except Exception:
                pass

        def _on_done(rendered, failed):
            try:
                self._set_status(
                    f"✓ Pre-render xong: {rendered} thumbnail "
                    f"(lỗi {failed})"
                )
            except Exception:
                pass
            _log.info("KB thumbnails done: %d ok, %d failed", rendered, failed)

        tikz_thumbnail.preload_async(
            to_render,
            on_progress=_on_progress,
            on_done=_on_done,
        )

    def _build_statusbar(self) -> None:
        # ── Status bar: dark slate, compact ──
        sb = tk.Frame(self, bg="#1E293B", height=26)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)

        # Left: version badge
        tk.Label(sb, text=f"  v{APP_VERSION}  ",
                bg="#334155", fg="#94A3B8",
                font=("Segoe UI", 7, "bold"),
                padx=6, pady=0).pack(side="left", fill="y")

        # Left: status
        self._status_var = tk.StringVar(value="Sẵn sàng — MatrixExamAI")
        tk.Label(sb, textvariable=self._status_var,
                bg="#1E293B", fg="#94A3B8",
                font=("Segoe UI", 8),
                anchor="w", padx=6).pack(side="left", fill="y", pady=4)

        # [FRICTION-3 lite] Middle: exam info — luôn thấy đang work exam nào
        self._exam_info_var = tk.StringVar(value="")
        tk.Label(sb, textvariable=self._exam_info_var,
                bg="#1E293B", fg="#10B981",
                font=("Segoe UI", 8, "bold"),
                anchor="center", padx=10).pack(side="left", padx=8, pady=4)

        # Right: session info
        self._session_lbl = tk.Label(sb, text="",
                bg="#1E293B", fg="#64748B",
                font=("Segoe UI", 8),
                anchor="e", padx=6)
        self._session_lbl.pack(side="right", fill="y", pady=4)

        # Runtime pill: hiển thị thời gian tác vụ dài ngay ở status bar để
        # user không phải kéo panel/header mới thấy timer.
        self._runtime_var = tk.StringVar(value="")
        tk.Label(sb, textvariable=self._runtime_var,
                bg="#0F172A", fg="#FBBF24",
                font=("Segoe UI", 8, "bold"),
                anchor="e", padx=8).pack(side="right", fill="y", pady=3)

        # Right: dot indicator (online/offline)
        self._status_dot = tk.Label(sb, text="●",
                bg="#1E293B", fg="#10B981",
                font=("Segoe UI", 8),
                padx=4)
        self._status_dot.pack(side="right", fill="y", pady=4)

    def _setup_global_mousewheel(self) -> None:
        """Kích hoạt cuộn chuột (MouseWheel) thông minh trên TOÀN BỘ ứng dụng.

        Cho phép người dùng rê chuột vào bất cứ đâu (Label, Button, Entry, Frame...)
        và lăn chuột thì vùng cuộn gần nhất (Canvas, Text, Treeview, Listbox, CTkScrollableFrame)
        sẽ tự động cuộn lên/xuống mượt mà mà không đòi hỏi phải rê đúng mép.
        Hỗ trợ Scroll Chaining / Bubbling: khi chuột ở trên Text/Treeview đã cuộn hết hoặc
        toàn bộ nội dung đã hiển thị, sự kiện cuộn sẽ tự động nổi bọt lên Canvas cha!
        """
        def _on_mousewheel(event):
            try:
                # 1. Tìm widget dưới con trỏ chuột
                x, y = self.winfo_pointerx(), self.winfo_pointery()
                target = None
                try:
                    w = getattr(event, "widget", None)
                    if w and hasattr(w, "winfo_containing"):
                        target = w.winfo_containing(x, y)
                except Exception:
                    pass
                if not target:
                    try:
                        target = self.winfo_containing(x, y)
                    except Exception:
                        pass
                if not target:
                    target = getattr(event, "widget", None)
                if not target:
                    return

                # 2. Chuẩn hóa độ lệch notch cuộn chuột cross-platform
                delta = getattr(event, "delta", 0)
                if delta:
                    notch = float(delta) / 120.0
                else:
                    num = getattr(event, "num", 0)
                    if num == 4:
                        notch = 1.0   # Cuộn lên
                    elif num == 5:
                        notch = -1.0  # Cuộn xuống
                    else:
                        return

                if notch == 0:
                    return

                # Tính số đơn vị cuộn theo tốc độ lăn chuột
                canvas_units = int(-1.0 * notch * 3)
                if canvas_units == 0:
                    canvas_units = -1 if notch > 0 else 1
                text_units = int(-1.0 * notch * 2)
                if text_units == 0:
                    text_units = -1 if notch > 0 else 1

                # 3. Duyệt ngược cây widget từ target lên root để tìm container cuộn phù hợp
                curr = target
                while curr:
                    # A. Widget Text, Treeview, Listbox
                    if isinstance(curr, (tk.Text, ttk.Treeview, tk.Listbox)):
                        try:
                            first, last = curr.yview()
                            # Nếu nội dung đã hiển thị hết 100% -> cho phép cuộn tiếp lên container cha
                            if first <= 0.001 and last >= 0.999:
                                pass
                            # Nếu đang lăn lên mà đã ở kịch đỉnh -> cho phép cuộn tiếp lên container cha
                            elif notch > 0 and first <= 0.001:
                                pass
                            # Nếu đang lăn xuống mà đã ở kịch đáy -> cho phép cuộn tiếp lên container cha
                            elif notch < 0 and last >= 0.999:
                                pass
                            else:
                                curr.yview_scroll(text_units, "units")
                                return "break"
                        except Exception:
                            pass

                    # B. CTkScrollableFrame hoặc widget có _parent_canvas
                    p_canvas = getattr(curr, "_parent_canvas", None)
                    if p_canvas and hasattr(p_canvas, "yview_scroll"):
                        try:
                            first, last = p_canvas.yview()
                            if not (first <= 0.001 and last >= 0.999):
                                p_canvas.yview_scroll(canvas_units, "units")
                                return "break"
                        except Exception:
                            pass

                    # C. Standard tk.Canvas
                    if isinstance(curr, tk.Canvas):
                        try:
                            first, last = curr.yview()
                            # Nếu canvas có scrollable range
                            if not (first <= 0.001 and last >= 0.999):
                                curr.yview_scroll(canvas_units, "units")
                                return "break"
                        except Exception:
                            pass

                    curr = getattr(curr, "master", None)
            except Exception:
                pass

        # Bind toàn ứng dụng trên Windows và X11/Linux
        self.bind_all("<MouseWheel>", _on_mousewheel, add="+")
        self.bind_all("<Button-4>", lambda e: _on_mousewheel(type("E", (), {"delta": 120, "num": 4, "widget": getattr(e, "widget", None)})()), add="+")
        self.bind_all("<Button-5>", lambda e: _on_mousewheel(type("E", (), {"delta": -120, "num": 5, "widget": getattr(e, "widget", None)})()), add="+")

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        m_session = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Phiên làm việc", menu=m_session)
        m_session.add_command(label="💾  Lưu phiên (Ctrl+S)",    command=self._session_save,     accelerator="Ctrl+S")
        m_session.add_command(label="💾  Lưu thành file…",      command=self._session_save_as)
        m_session.add_command(label="📂  Mở phiên…",       command=self._session_open)
        m_session.add_command(label="🕐  Phiên làm việc gần đây…",  command=self._session_recent)
        m_session.add_separator()
        # [SPEED-4] "Tải đề từ file" chuyển từ toolbar TabResult vào đây —
        # đây là import path, không phải primary action.
        m_session.add_command(
            label="📥  Tải đề từ file (Word/PDF/TeX)…",
            command=lambda: (self._ensure_tab_loaded("tab_result"),
                             self._tab_result._load_exam_from_file()),
        )
        # [FRICTION-4] Smart import — auto-detect type
        m_session.add_command(
            label="📁  Tải đa định dạng (Word/PDF/ảnh)…",
            command=self._smart_import_file,
        )
        m_session.add_separator()
        m_session.add_command(label="🚪  Thoát",               command=self.destroy)

        m_bank = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Ngân hàng câu hỏi", menu=m_bank)
        m_bank.add_command(label="💾  Lưu đề vào ngân hàng câu hỏi", command=self._save_to_bank)
        m_bank.add_command(label="📊  Thống kê ngân hàng câu hỏi",   command=self._show_bank_stats)
        m_bank.add_separator()
        m_bank.add_command(label="📄  Import đề từ PDF / Word / Ảnh…", command=self._open_import_pdf_dialog)

        m_cache = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Bộ nhớ đệm", menu=m_cache)
        m_cache.add_command(label="📊  Thống kê bộ nhớ đệm",  command=self._show_cache_stats)
        m_cache.add_command(label="🗑  Xóa bộ nhớ đệm",       command=self._clear_cache)

        m_tools = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Công cụ", menu=m_tools)
        m_tools.add_command(label="⚡  Tạo đề nhanh (Ctrl+Q)",  command=self._open_quick_gen, accelerator="Ctrl+Q")
        m_tools.add_command(label="💬  Smart Prompt (Ctrl+P)",    command=self._open_smart_prompt, accelerator="Ctrl+P")
        m_tools.add_command(label="🤖  Tạo ma trận bằng AI",     command=self._open_ai_gen_matrix)
        m_tools.add_command(label="📥  Tải mẫu ma trận…",        command=lambda: self._tab_config._download_template())
        m_tools.add_separator()
        m_tools.add_command(label="🎲  Trộn đề thi hoán vị mã đề…", command=self._switch_to_shuffle_tab)
        m_tools.add_command(label="📄  Xuất Word (Ctrl+E)",       command=lambda: (self._ensure_tab_loaded("tab_result"), self._tab_result._export_word()), accelerator="Ctrl+E")
        m_tools.add_command(label="📋  Nhật ký tác vụ…",          command=self._open_task_history_dialog)

        m_settings = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Cài đặt", menu=m_settings)
        m_settings.add_command(label="⚙  Cài đặt ứng dụng…",  command=self._open_settings_dialog)
        m_settings.add_command(label="👤  Thông tin người dùng",  command=lambda: self._nb.select(self._tab_user_info))
        m_settings.add_separator()
        # P1.8: Theme toggle
        m_settings.add_command(label="🌓  Chuyển Light / Dark mode",
                                command=self._toggle_theme)
        # P1.7: Exam history dialog
        m_settings.add_command(label="🕒  Lịch sử phiên bản đề",
                                command=self._open_exam_history)

        self.bind("<Control-s>", lambda _: self._session_save())
        self.bind("<Control-q>", lambda _: self._open_quick_gen())
        self.bind("<Control-e>", lambda _: (self._ensure_tab_loaded("tab_result"), self._tab_result._export_word()))
        self.bind("<Control-g>", lambda _: self._start_generation())
        self.bind("<Control-p>", lambda _: self._open_smart_prompt())
        # bind_shortcuts deferred — tab_convert chưa load thực
        try:
            if hasattr(self._tab_convert, 'bind_shortcuts'):
                self._tab_convert.bind_shortcuts(self)
        except Exception:
            pass
        for i in range(9):
            self.bind(f"<Alt-{i+1}>", lambda e, idx=i: self._nb.select(idx))

    def _open_task_history_dialog(self) -> None:
        """Hiển thị nhật ký tác vụ nền: backup/restore, cloud, render..."""
        try:
            from services.task_events import clear_task_events, list_task_events
        except Exception as exc:
            messagebox.showerror("Lỗi nhật ký tác vụ", f"Không mở được nhật ký: {exc}", parent=self)
            return

        win = tk.Toplevel(self)
        win.title("📋 Nhật ký tác vụ")
        win.geometry("820x420")
        win.minsize(680, 320)
        win.configure(bg="#F8FAFC")
        try:
            win.transient(self)
        except Exception:
            pass

        top = tk.Frame(win, bg="#F8FAFC")
        top.pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(
            top,
            text="Nhật ký tác vụ gần đây",
            bg="#F8FAFC", fg="#0F172A",
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left")

        cols = ("time", "status", "kind", "title", "message")
        frame = tk.Frame(win, bg="#F8FAFC")
        frame.pack(fill="both", expand=True, padx=12, pady=6)
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        headings = {
            "time": "Thời gian",
            "status": "Trạng thái",
            "kind": "Loại",
            "title": "Tác vụ",
            "message": "Chi tiết",
        }
        widths = {"time": 140, "status": 90, "kind": 90, "title": 180, "message": 280}
        for col in cols:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col], anchor="w")
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

        def _load_events() -> None:
            tree.delete(*tree.get_children())
            events = list_task_events(limit=200)
            if not events:
                tree.insert("", "end", values=("", "info", "", "Chưa có tác vụ", ""))
                return
            for event in events:
                tree.insert(
                    "",
                    "end",
                    values=(
                        event.created_at,
                        event.status,
                        event.kind,
                        event.title,
                        event.message[:160],
                    ),
                )

        def _clear_events() -> None:
            if not messagebox.askyesno("Xóa nhật ký", "Xóa toàn bộ nhật ký tác vụ?", parent=win):
                return
            removed = clear_task_events()
            _load_events()
            self._set_status(f"Đã xóa {removed} dòng nhật ký tác vụ")

        btns = tk.Frame(win, bg="#F8FAFC")
        btns.pack(fill="x", padx=12, pady=(6, 12))
        tk.Button(
            btns,
            text="Làm mới",
            bg="#0EA5E9", fg="white", activebackground="#0284C7",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
            padx=12, pady=5,
            command=_load_events,
        ).pack(side="left")
        tk.Button(
            btns,
            text="Xóa nhật ký",
            bg="#EF4444", fg="white", activebackground="#DC2626",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
            padx=12, pady=5,
            command=_clear_events,
        ).pack(side="left", padx=8)
        ttk.Button(btns, text="Đóng", command=win.destroy).pack(side="right")
        _load_events()

    # ══════════════════════════════════════════════════════════════════════
    #  CALLBACKS
    # ══════════════════════════════════════════════════════════════════════

    def _on_matrix_loaded(self, matrix_data: MatrixData) -> None:
        self._matrix_data = matrix_data
        self._tab_matrix.load_matrix(matrix_data)
        self._nb.select(1)
        self._set_status(f"✅ Đọc xong: {len(matrix_data.rows)} câu — {matrix_data.title[:50]}")

    def _update_exam_info_bar(self) -> None:
        """[FRICTION-3 lite] Cập nhật label giữa status bar với info exam hiện tại."""
        try:
            if self._exam_data is None:
                self._exam_info_var.set("(chưa có đề)")
                return
            ex = self._exam_data
            stats = ex.stats
            txt = (
                f"📝 {ex.subject or 'Toán'} {ex.grade or '?'} • "
                f"{stats.get('total', 0)} câu "
                f"({stats.get('TN', 0)}TN/{stats.get('DS', 0)}DS/"
                f"{stats.get('TLN', 0)}TLN/{stats.get('TL', 0)}TL)"
            )
            self._exam_info_var.set(txt)
        except Exception:
            pass

    def _smart_import_file(self) -> None:
        """[FRICTION-4] Universal import — chọn 1 file, app tự route theo type.

        Type → đích:
          .docx        → tab Xuất đề (parse → load exam)
          .pdf         → tab Convert (PDF → Word pipeline)
          .png/.jpg/.. → tab Convert (Ảnh → Word pipeline)
          .tex/.txt    → tab Xuất đề (parse natural)
          .json (phiên) → load session
        """
        path = filedialog.askopenfilename(
            parent=self,
            title="Chọn file để import (app sẽ tự nhận diện type)",
            filetypes=[
                ("Tất cả định dạng hỗ trợ",
                 "*.docx *.pdf *.png *.jpg *.jpeg *.bmp *.webp *.tex *.txt *.json"),
                ("Word (.docx)",  "*.docx"),
                ("PDF",           "*.pdf"),
                ("Ảnh",           "*.png *.jpg *.jpeg *.bmp *.webp"),
                ("LaTeX/Text",    "*.tex *.txt"),
                ("Phiên (.json)", "*.json"),
                ("Tất cả",        "*.*"),
            ],
        )
        if not path:
            return

        from pathlib import Path as _P
        suffix = _P(path).suffix.lower()

        try:
            if suffix == ".docx":
                # Word đề → TabResult
                self._ensure_tab_loaded("tab_result")
                self._tab_result._load_exam_from_path(path) \
                    if hasattr(self._tab_result, "_load_exam_from_path") \
                    else self._smart_route_word(path)
            elif suffix == ".pdf":
                # PDF → tab Convert PDF mode
                self._ensure_tab_loaded("tab_convert")
                self._nb.select(self._tab_convert)
                if hasattr(self._tab_convert, "_select_mode"):
                    self._tab_convert._select_mode("pdf")
                if hasattr(self._tab_convert, "_pdf_path"):
                    self._tab_convert._pdf_path = path
                    # Auto-trigger choose PDF logic to populate fields
                    if hasattr(self._tab_convert, "_choose_pdf_from_path"):
                        self._tab_convert._choose_pdf_from_path(path)
                self._set_status(f"📄 PDF mở ở tab Convert: {_P(path).name}")
            elif suffix in (".png", ".jpg", ".jpeg", ".bmp", ".webp"):
                # Ảnh → tab Convert Image mode
                self._ensure_tab_loaded("tab_convert")
                self._nb.select(self._tab_convert)
                if hasattr(self._tab_convert, "_select_mode"):
                    self._tab_convert._select_mode("image")
                # Add ảnh vào batch
                if hasattr(self._tab_convert, "_add_image_to_batch"):
                    try:
                        with open(path, "rb") as f:
                            data = f.read()
                        ext = "jpeg" if suffix in (".jpg", ".jpeg") else "png"
                        self._tab_convert._add_image_to_batch(
                            data, ext, _P(path).name)
                        self._set_status(f"🖼️ Ảnh thêm vào batch: {_P(path).name}")
                    except Exception as e:
                        messagebox.showerror("Lỗi đọc ảnh", str(e))
            elif suffix in (".tex", ".txt"):
                # LaTeX/Text → TabResult parse
                self._ensure_tab_loaded("tab_result")
                if hasattr(self._tab_result, "_load_exam_from_file_path"):
                    self._tab_result._load_exam_from_file_path(path)
                else:
                    # Fallback: open file dialog với file đã chọn (UX hơi awkward)
                    self._tab_result._load_exam_from_file()
            elif suffix == ".json":
                # Session JSON
                try:
                    from storage.database import load_session
                    data = load_session(path)
                    self._restore_session(data)
                    self._current_session_path = path
                    self._set_status(f"📂 Đã mở phiên: {_P(path).name}")
                except Exception as e:
                    messagebox.showerror("Lỗi mở phiên", str(e))
            else:
                messagebox.showwarning(
                    "Định dạng chưa hỗ trợ",
                    f"App chưa hỗ trợ file '{suffix}'.\n"
                    f"Định dạng được hỗ trợ: .docx .pdf .png .jpg .tex .txt .json"
                )
        except Exception as e:
            _log.exception("smart_import_file failed")
            messagebox.showerror("Lỗi import", str(e))

    def _smart_route_word(self, path: str) -> None:
        """Fallback: Word → đặt làm initial file rồi gọi _load_exam_from_file."""
        # tab_result._load_exam_from_file mở dialog mới — tạm bỏ qua,
        # chỉ thông báo cho user.
        self._nb.select(self._tab_result)
        messagebox.showinfo(
            "Tải Word",
            f"Hãy chọn file '{path}' trong dialog tiếp theo.",
        )
        self._tab_result._load_exam_from_file()

    def _maybe_suggest_nhch_reuse(self, rows: list) -> bool:
        """[SMART-3] Suggest user dùng NHCH thay vì AI gen mới.

        Returns
        -------
        True  → tiếp tục generation (user chọn AI / Mix / Bank)
        False → abort (user nhấn Hủy)
        """
        try:
            from services.smart_defaults import (
                recommend_source_mode,
                format_recommendation_summary,
            )
        except Exception as e:
            _log.warning("smart_defaults import failed: %s", e)
            return True  # không block generation

        subject = self._tab_config.get_subject()
        grade   = self._tab_config.get_grade()
        provider = self._tab_config.get_provider()
        model = self._tab_config.get_model()

        try:
            rec = recommend_source_mode(
                rows,
                subject=subject,
                grade=grade,
                provider=provider,
                model=model,
                tier=getattr(self, "_tier", "premium"),
                features=getattr(self, "_features", {}),
            )
        except Exception as e:
            _log.warning("smart source recommendation failed: %s", e)
            return True

        # Không làm phiền nếu Smart Defaults không có gợi ý hữu ích.
        if not rec.should_prompt:
            if rec.warnings:
                self._set_status("⚠️ " + rec.warnings[0])
            return True

        # Show suggestion dialog
        msg = format_recommendation_summary(rec, subject, grade)
        dlg = tk.Toplevel(self)
        try:
            from ui import set_dialog_icon
            set_dialog_icon(dlg)
        except Exception:
            pass
        dlg.title("💡 Smart Defaults — Chọn nguồn tạo đề")
        dlg.geometry("560x440")
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg="#F8FAFC")
        dlg.protocol("WM_DELETE_WINDOW", lambda: _close("cancel"))

        # Header
        hdr = tk.Frame(dlg, bg="#0F2D52")
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="💡  NHCH ĐÃ CÓ NHIỀU CÂU PHÙ HỢP",
            bg="#0F2D52", fg="white",
            font=("Segoe UI", 11, "bold"),
            pady=10, padx=14,
        ).pack(side="left")
        tk.Frame(dlg, bg="#10B981", height=2).pack(fill="x")

        # Body
        body = tk.Frame(dlg, bg="#F8FAFC")
        body.pack(fill="both", expand=True, padx=16, pady=12)

        tk.Label(
            body, text=msg,
            bg="#F8FAFC", fg="#0F172A",
            font=("Segoe UI", 10),
            justify="left", anchor="w",
        ).pack(fill="x", pady=(0, 8))

        # Mode options
        chosen = {"mode": "ai_only", "ratio": 0}  # default if user closes window

        def _close(choice: str, ratio: int | None = None):
            chosen["mode"] = choice
            if ratio is not None:
                chosen["ratio"] = ratio
            dlg.destroy()

        opt_frame = tk.LabelFrame(
            body, text=" Chọn cách tạo đề ",
            bg="#F8FAFC", fg="#0F172A",
            font=("Segoe UI", 9, "bold"),
            padx=10, pady=8,
        )
        opt_frame.pack(fill="x", pady=(4, 8))

        rec_mode = rec.mode
        mixed_ratio = rec.bank_ratio if rec.bank_ratio and rec.bank_ratio < 100 else 70

        for val, ratio, label, desc, is_rec in [
            ("bank_only",
             100,
             "🏦 Dùng 100% NHCH (FREE — không tốn API)",
             "Lấy hoàn toàn từ ngân hàng câu hỏi đã có.",
             rec_mode == "bank_only"),
            ("mixed",
             mixed_ratio,
             f"🔀 Mix {mixed_ratio}% NHCH + {100 - mixed_ratio}% AI mới",
             "Ưu tiên NHCH, AI chỉ sinh phần thiếu/đa dạng hoá.",
             rec_mode == "mixed"),
            ("ai_only",
             0,
             "✨ Gen 100% AI mới (như cũ)",
             "Tạo toàn bộ câu mới bằng AI — tốn lượt API.",
             rec_mode == "ai_only"),
        ]:
            tag = " ⭐ Đề xuất" if is_rec else ""
            btn = tk.Button(
                opt_frame,
                text=f"  {label}{tag}\n  {desc}  ",
                bg="#10B981" if is_rec else "#E2E8F0",
                fg="white" if is_rec else "#1E293B",
                activebackground="#059669" if is_rec else "#CBD5E1",
                font=("Segoe UI", 10, "bold" if is_rec else "normal"),
                relief="flat", cursor="hand2", bd=0,
                padx=14, pady=8,
                justify="left", anchor="w",
                command=lambda v=val, r=ratio: _close(v, r),
            )
            btn.pack(fill="x", pady=3)

        # Cancel button
        btn_f = tk.Frame(dlg, bg="#F8FAFC")
        btn_f.pack(fill="x", padx=16, pady=(0, 12))
        tk.Button(
            btn_f, text="  ✖ Hủy tạo đề  ",
            bg="#64748B", fg="white",
            activebackground="#475569",
            font=("Segoe UI", 9),
            relief="flat", cursor="hand2", bd=0,
            padx=12, pady=6,
            command=lambda: _close("cancel"),
        ).pack(side="right")

        self.wait_window(dlg)

        mode = chosen["mode"]
        if mode == "cancel":
            return False

        # Apply chosen mode
        self._source_mode = mode
        self._source_ratio = chosen["ratio"]
        mode_labels = {
            "ai_only": "✨ AI mới",
            "bank_only": "📚 100% NHCH",
            "mixed": f"🔀 Mix {self._source_ratio}% NHCH",
        }
        self._src_btn.config(text=f"  {mode_labels.get(mode, mode)}  ")
        self._set_status(f"💡 Smart Defaults chọn: {mode_labels.get(mode, mode)}")
        return True

    def _apply_detected_meta(self, subject: str, grade: str, topic: str) -> None:
        """[SMART-1] Áp dụng metadata Vision detect được vào tab Cài đặt.

        Update subject + grade trong _tab_config — đồng bộ với get_subject_grade().
        topic được dùng làm gợi ý hiển thị (không lưu vào config).
        """
        try:
            if subject:
                self._tab_config.set_subject(subject)
            if grade:
                self._tab_config.set_grade(str(grade))
            _log.info("[SMART-1] Applied detected meta: %s lớp %s — %s",
                      subject, grade, topic)
        except Exception as e:
            _log.warning("apply_detected_meta failed: %s", e)

    def _on_template_loaded(self, matrix: MatrixData) -> None:
        """[SPEED-3] Callback khi user load template ma trận.

        Cập nhật `_matrix_data` để xuất ma trận / tạo đề dùng đúng title +
        time_str của template (KHÔNG dùng giá trị cũ từ tab Cài đặt).
        """
        self._matrix_data = matrix
        self._nb.select(1)  # chuyển sang tab Câu hỏi để user thấy ngay
        self._set_status(
            f"✅ Tải template: {matrix.title[:60]} — {len(matrix.rows)} câu")

    def _export_current_matrix(self) -> None:
        """Xuất ma trận hiện tại (đã chỉnh trên tab Bảng câu hỏi) ra CSV hoặc Word."""
        rows = self._tab_matrix.get_all_rows()
        if not rows:
            messagebox.showwarning(
                "Chưa có dữ liệu",
                "Chưa có dòng ma trận để xuất. Hãy tải ma trận hoặc phân tích file trước.",
                parent=self,
            )
            return
        title = self._matrix_data.title if self._matrix_data else "Ma trận đề kiểm tra"
        time_str = self._matrix_data.time_str if self._matrix_data else ""
        md = MatrixData(title=title, time_str=time_str, rows=rows)
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Lưu ma trận / ma trận đặc tả",
            defaultextension=".docx",
            filetypes=[
                ("Word (.docx)", "*.docx"),
                ("CSV (Excel)", "*.csv"),
                ("Tất cả", "*.*"),
            ],
        )
        if not path:
            return
        ext = Path(path).suffix.lower()
        try:
            from export.matrix_exporter import export_matrix_csv, export_matrix_docx

            if ext == ".csv":
                export_matrix_csv(md, path)
            else:
                out = path if ext == ".docx" else str(Path(path).with_suffix(".docx"))
                export_matrix_docx(md, out)
                path = out
            messagebox.showinfo("Đã xuất", f"Đã lưu file:\n{path}", parent=self)
            self._set_status(f"📥 Đã xuất ma trận: {Path(path).name}")
        except Exception as e:
            messagebox.showerror("Lỗi xuất ma trận", str(e), parent=self)

    def _ensure_tab_loaded(self, tab_key: str) -> None:
        """Đảm bảo lazy tab đã được load thực sự (cho programmatic access)."""
        if tab_key not in self._lazy_loaded:
            creator = self._lazy_tab_defs.get(tab_key)
            if creator:
                self._lazy_loaded.add(tab_key)
                try:
                    creator()
                except Exception as e:
                    self._lazy_loaded.discard(tab_key)
                    _log.error("Ensure tab %s loaded failed: %s", tab_key, e, exc_info=True)
                    raise

    def _make_ai_call(self):
        provider = self._tab_config.get_provider()
        keys     = self._tab_config.get_api_keys()
        model    = self._tab_config.get_model()
        if not keys or not keys[0]:
            raise ValueError("Vui lòng nhập API Key ở tab Cài đặt ⚙️.")
        service = create_ai_service(provider, keys, model)
        return service.generate

    # ══════════════════════════════════════════════════════════════════════
    #  GENERATION
    # ══════════════════════════════════════════════════════════════════════

    def _start_generation(self) -> None:
        # Kiểm tra khóa hạn dùng
        if self._license_locked:
            messagebox.showwarning(
                "Đã hết hạn",
                "Giấy phép đã hết hạn. Không thể tạo đề.\n"
                "Vui lòng liên hệ admin để gia hạn."
            )
            return

        keys = self._tab_config.get_api_keys()
        if not keys or not keys[0]:
            messagebox.showwarning("Thiếu API Key", "Vui lòng nhập API Key ở tab Cài đặt ⚙️.")
            return

        enabled_rows = self._tab_matrix.get_enabled_rows()
        if not enabled_rows:
            messagebox.showwarning("Không có câu", "Không có câu nào được bật trong bảng ma trận.\nVui lòng bật ít nhất 1 câu ở tab Cài đặt ⚙️.")
            return

        # [SMART-3] Suggest dùng lại NHCH nếu có nhiều câu phù hợp.
        # Chỉ check khi user đang ở mode "ai_only" — nếu user đã chủ động
        # chọn "mixed" hoặc "bank_only" thì respect choice của họ.
        cur_mode = getattr(self, "_source_mode", "ai_only")
        if cur_mode == "ai_only":
            if not self._maybe_suggest_nhch_reuse(enabled_rows):
                # User chọn Hủy → abort generation
                return

        # Kiểm tra giới hạn đề cho gói Basic
        from storage.database import get_today_exam_count, log_exam_generation
        from services.license_manager import get_machine_id
        tier = getattr(self, "_tier", "basic")
        if tier == "basic":
            machine_id = get_machine_id()
            count_today = get_today_exam_count(machine_id)
            if count_today >= 2:
                messagebox.showwarning(
                    "Hết lượt tạo đề",
                    "Bạn đã hết lượt tạo đề trong ngày (tối đa 2 đề/ngày).\n"
                    "Vui lòng nâng cấp lên gói PRO hoặc Premium để tiếp tục sử dụng không giới hạn."
                )
                return

        self._gen_btn.config(state="disabled")
        self._progress_bar.start(10)
        self._progress_lbl.config(text="Tạo đề")
        self._set_status(f"🔄 Đang tạo {len(enabled_rows)} câu hỏi song song…")
        self._show_progress_panel()

        provider = self._tab_config.get_provider()
        model    = self._tab_config.get_model()
        subject  = self._tab_config.get_subject()
        grade    = self._tab_config.get_grade()
        time     = self._tab_config.get_time()
        semester = self._tab_config.get_semester()
        year     = self._tab_config.get_year()

        try:
            service = create_ai_service(provider, keys, model)
        except Exception as e:
            self._gen_btn.config(state="normal")
            self._progress_bar.stop()
            messagebox.showerror("Lỗi khởi tạo AI", str(e))
            return

        # ── Cross-Model Verification: tạo verifier service ────────────────
        verifier_ai = None
        if self._tab_config.get_cross_model_enabled():
            try:
                vp = self._tab_config.get_verifier_provider()
                vk = self._tab_config.get_verifier_keys()
                vm = self._tab_config.get_verifier_model()
                if vk and vk[0].strip() and vm:
                    verifier_service = create_ai_service(vp, vk, vm)
                    verifier_ai = verifier_service.generate
                    self._set_status(f"✅ Cross-Model ON: Verifier = {vp} {vm}")
                else:
                    self._set_status("⚠️ Cross-Model: thiếu API key cho verifier")
            except Exception as e:
                self._set_status(f"⚠️ Cross-Model lỗi: {e}")

        cache_get = self._cache.get
        cache_set = self._cache.set

        def progress_cb(done: int, total: int, topic: str) -> None:
            self.after(0, lambda d=done, t=total, tp=topic: (
                self._update_gen_progress(d, t, tp),
                self._set_status(f"🔄 Đang tạo câu {d}/{t}…"),
            ))

        def _do_gen() -> None:
            try:
                source_mode  = getattr(self, "_source_mode",  "ai_only")
                source_ratio = getattr(self, "_source_ratio", 50)

                if source_mode in ("bank_only", "mixed"):
                    from core.generator import generate_exam_with_source
                    questions = generate_exam_with_source(
                        rows=enabled_rows, subject=subject, grade=grade,
                        ai_call=service.generate, mode=source_mode, bank_ratio=source_ratio,
                        progress_cb=lambda i,n,t: progress_cb(i,n,t),
                        verifier_ai=verifier_ai,
                    )
                    from core.models import ExamData
                    from config import TIME_MAP
                    exam = ExamData(
                        exam_title=f"ĐỀ KIỂM TRA {semester.upper()} - {subject.upper()} {grade}",
                        subject=subject, grade=grade, semester=semester, year=year,
                        time=TIME_MAP.get(grade, "90 phút"), questions=questions,
                        school=self._tab_config.get_school_name(),
                        teacher=self._tab_config.get_teacher_name(),
                    )
                else:
                    exam = generate_all(
                        rows=enabled_rows, subject=subject, grade=grade,
                        semester=semester, year=year, ai_call=service.generate,
                        cache_get=cache_get, cache_set=cache_set, progress_cb=progress_cb,
                        verifier_ai=verifier_ai,
                        cancel_event=self._gen_cancel_event,
                    )
                    exam.time = time
                    # Inject school + teacher từ tab Cài đặt vào ExamData
                    # → cho phép edit sau qua dialog Sửa thông tin đề.
                    exam.school = self._tab_config.get_school_name()
                    exam.teacher = self._tab_config.get_teacher_name()
                # Kiểm tra cancel ở cuối — nếu event được set thì không push kết quả
                if self._gen_cancel_event.is_set():
                    self.after(0, lambda: self._on_gen_error("Đã hủy bởi người dùng."))
                else:
                    self.after(0, lambda e=exam: self._on_gen_done(e))
            except Exception as ex:
                self.after(0, lambda err=str(ex): self._on_gen_error(err))

        # Clear event trước khi start để đảm bảo không bị dính cancel cũ
        self._gen_cancel_event.clear()
        threading.Thread(target=_do_gen, daemon=True).start()

    def cancel_generation(self) -> None:
        """Yêu cầu hủy batch generation hiện tại.

        Set `_gen_cancel_event` — các worker trong ThreadPoolExecutor sẽ
        check cờ và trả về placeholder Question "[HỦY]". Cuối pipeline,
        `_do_gen` sẽ gọi `_on_gen_error("Đã hủy...")` thay vì `_on_gen_done`.

        An toàn để gọi nhiều lần — chỉ set lại Event đã set (no-op).
        """
        try:
            self._gen_cancel_event.set()
            self._set_status("⏹ Đang dừng — chờ các worker kết thúc…")
        except Exception as e:
            _log.warning("cancel_generation failed: %s", e)

    def _on_gen_done(self, exam: ExamData) -> None:
        self._progress_bar.stop()
        self._gen_btn.config(state="normal")
        self._progress_lbl.config(text="")

        # Cập nhật progress panel: hoàn tất rồi ẩn sau 3 giây
        import time as _time
        elapsed = _time.time() - self._gen_start_time if self._gen_start_time else 0
        m, s = divmod(int(elapsed), 60)
        done_time = f"⏱ {m:02d}:{s:02d}"
        self._prog_status.configure(text="✅ Hoàn tất!")
        self._prog_pct.configure(text="100%")
        self._prog_detail.configure(text=f"Tạo xong trong {done_time}")
        self._prog_elapsed.configure(text=done_time)
        self._progress_time_lbl.configure(text=f"✅ {done_time}")
        self._runtime_var.set(f"Tạo xong  {done_time}")
        self._gen_start_time = 0.0
        self._update_progress_bar(1.0)
        self.after(3000, self._hide_progress_panel)

        self._exam_data = exam
        self._update_exam_info_bar()  # [FRICTION-3 lite]
        stats = exam.stats
        errors = stats["errors"]
        total  = stats["total"]

        # ── P1.7: Snapshot exam history (để có thể restore version cũ) ──
        try:
            from services import exam_history
            exam_history.snapshot(
                exam, source="ai",
                note=f"AI generation — {total} câu, {errors} lỗi",
            )
        except Exception as _e:
            _log.debug("snapshot failed: %s", _e)

        # Ghi log tạo đề thành công (cho giới hạn Basic) — chạy background
        import threading
        def _log_gen():
            from storage.database import log_exam_generation
            from services.license_manager import get_machine_id
            log_exam_generation(get_machine_id())
        threading.Thread(target=_log_gen, daemon=True).start()

        # Thống kê cross-model verification
        cross_verified = 0
        cross_disagreed = 0
        for q in exam.questions:
            if q._review and "cross_model" in q._review:
                cross_verified += 1
                if not q._review["cross_model"].get("agreed", True):
                    cross_disagreed += 1

        # Ensure tab_result is loaded before accessing it
        self._ensure_tab_loaded("tab_result")
        self._tab_result.load_exam(exam)
        self._nb.select(2)

        msg = (f"✅ Tạo xong {total} câu hỏi!\n"
               f"  TN: {stats['TN']}  Đ/S: {stats['DS']}  TLN: {stats['TLN']}  TL: {stats['TL']}")
        if cross_verified > 0:
            msg += f"\n🔬 Cross-Model: {cross_verified} câu đã xác minh"
            if cross_disagreed > 0:
                msg += f" | ⚠️ {cross_disagreed} câu không đồng ý (cần review)"
        if errors:
            msg += f"\n⚠️ {errors} câu bị lỗi — nhấn '🔁 Tạo lại câu lỗi' để thử lại."

        self._set_status(msg.splitlines()[0])
        if errors:
            messagebox.showwarning("Có câu lỗi", msg)

        # ── [SPEED-1] Auto-export Word + toast ──────────────────────────────
        # Mặc định BẬT: app tự lưu Word vào Documents/MEA Exam + tự mở file.
        # User có thể tắt qua tab Cài đặt; khi tắt → fallback về dialog cũ.
        try:
            from config import is_auto_export_enabled
            auto_on = is_auto_export_enabled()
        except Exception:
            auto_on = True  # default ON

        if auto_on:
            self.after(200, lambda: self._do_auto_export(exam))
        else:
            self.after(200, lambda: self._ask_save_after_gen(exam))

    def _do_auto_export(self, exam) -> None:
        """[SPEED-1] Tự xuất Word + mở file + toast với options.

        Toast hiển thị 4 hành động:
          • Đổi vị trí — di chuyển file sang folder khác
          • Lưu thêm bản — save as với tên/folder khác (không xoá bản gốc)
          • Thêm vào NHCH — mở NHCHPreviewDialog để lưu vào ngân hàng
          • Tắt auto-export — disable feature, lần sau dùng dialog cũ
        """
        import os
        import subprocess
        from services.auto_export import auto_export_exam, save_extra_copy
        from ui.toast import Toast

        path, err = auto_export_exam(exam, include_solution=True)
        if err or path is None:
            # Lỗi → fallback về dialog cũ + toast cảnh báo
            try:
                Toast(
                    self, title="⚠️ Auto-export thất bại",
                    message=(err or "Không rõ lỗi") + "\nVui lòng chọn vị trí lưu thủ công.",
                    duration_ms=8000, variant="warning",
                ).show()
            except Exception:
                pass
            self._ask_save_after_gen(exam)
            return

        def _open_folder(folder):
            try:
                if os.name == "nt":
                    os.startfile(str(folder))
                elif os.name == "posix":
                    subprocess.Popen(["xdg-open", str(folder)])
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không mở được thư mục:\n{e}")

        # ── Build toast actions ──
        def _on_open_folder():
            """Mở thư mục chứa file vừa auto-export."""
            _open_folder(path.parent)

        def _on_relocate():
            """Đổi vị trí file (di chuyển sang folder khác)."""
            from tkinter import filedialog
            from pathlib import Path as _P
            import shutil
            new_dir = filedialog.askdirectory(
                title="Chọn thư mục mới",
                initialdir=str(path.parent),
            )
            if not new_dir:
                return
            new_path = _P(new_dir) / path.name
            try:
                shutil.move(str(path), str(new_path))
                self._set_status(f"✅ Đã chuyển file → {new_path}")
                # Đặt làm thư mục mặc định cho lần sau
                from config import set_auto_export_dir
                set_auto_export_dir(str(new_dir))
                # Mở folder mới
                _open_folder(new_dir)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không di chuyển được: {e}")

        def _on_duplicate():
            """Lưu thêm 1 bản với tên/folder khác."""
            extra_path, extra_err = save_extra_copy(
                exam, initial_dir=path.parent,
                initial_filename=path.name,
            )
            if extra_path:
                self._set_status(f"✅ Đã lưu thêm: {extra_path.name}")
                try:
                    os.startfile(str(extra_path))
                except Exception:
                    pass
            elif extra_err:
                messagebox.showerror("Lỗi", extra_err)

        def _on_save_nhch():
            """Mở NHCHPreviewDialog để chọn câu lưu vào ngân hàng."""
            try:
                from ui.dialog_nhch_preview import NHCHPreviewDialog
                from storage.database import save_questions
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không mở NHCH: {e}")
                return

            valid_qs = [q for q in exam.questions if not q._error]
            if not valid_qs:
                messagebox.showinfo("Thông báo", "Không có câu hợp lệ để lưu.")
                return

            subject = self._tab_config.get_subject()
            grade   = self._tab_config.get_grade()

            def _do_bank_save(questions):
                try:
                    n = save_questions(
                        questions, subject, grade, source=exam.exam_title)
                    if "tab_bank" in self._lazy_loaded:
                        self._tab_bank.refresh()
                    self._set_status(f"✅ {n} câu đã lưu vào NHCH")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không lưu NHCH: {e}")

            NHCHPreviewDialog(self, valid_qs, subject, grade,
                              on_confirm=_do_bank_save)

        def _on_disable_auto():
            """Tắt auto-export — lần sau sẽ hỏi vị trí lưu."""
            from config import set_auto_export_enabled
            set_auto_export_enabled(False)
            messagebox.showinfo(
                "Đã tắt auto-export",
                "Lần sau khi tạo đề xong, app sẽ hỏi bạn nơi lưu file.\n"
                "Có thể bật lại trong tab Cài đặt.",
            )

        try:
            Toast(
                self,
                title=f"✅ Đã lưu Word: {path.name}",
                message=(
                    f"📁 {path.parent}\n"
                    f"File đã tự mở. Bạn có thể:"
                ),
                actions=[
                    ("📁 Thư mục",  _on_open_folder),
                    ("📂 Đổi chỗ",  _on_relocate),
                    ("➕ Bản sao",   _on_duplicate),
                    ("🏦 NHCH",      _on_save_nhch),
                    ("⏸ Tắt auto",  _on_disable_auto),
                ],
                duration_ms=15000,  # 15s — đủ user đọc + click
                variant="success",
            ).show()
        except Exception as e:
            _log.debug("toast show failed: %s", e)

        # Cập nhật status bar
        self._set_status(f"✅ Đã lưu Word: {path.name}")

    def _ask_save_after_gen(self, exam) -> None:
        win = tk.Toplevel(self)
        win.title("Lưu đề kiểm tra")
        win.geometry("480x500")
        win.resizable(True, True)
        win.minsize(480, 480)
        win.grab_set()
        win.configure(bg="#FFFFFF")

        hdr = tk.Frame(win, bg="#F8FAFC")
        hdr.pack(fill="x")
        tk.Label(hdr, text="Tạo đề thành công!", bg="#F8FAFC", fg="#0F172A", font=("Segoe UI", 12, "bold")).pack(padx=16, pady=10)
        tk.Frame(win, bg="#E2E8F0", height=1).pack(fill="x") # Dòng kẻ ngang nhẹ

        stats = exam.stats
        n_err = stats.get("errors", 0)
        stat_txt = f"  {stats.get('TN',0)} câu TN  |  {stats.get('DS',0)} câu DS  |  {stats.get('TLN',0)} câu TLN  |  {stats.get('TL',0)} câu TL  =  {stats.get('total',0)} câu tổng"
        if n_err: stat_txt += f"  |  {n_err} câu lỗi"
        tk.Label(win, text=stat_txt, bg="#FFFFFF", fg="#475569", font=("Segoe UI", 9)).pack(pady=4)
        tk.Label(win, text="Bạn muốn lưu đề này vào đâu?", bg="#FFFFFF", fg="#0F172A", font=("Segoe UI", 10, "bold")).pack(pady=8)

        opt_f = tk.Frame(win, bg="#FFFFFF")
        opt_f.pack(fill="x", padx=24)
        save_var = tk.StringVar(value="both")

        _SAVE_OPTS = [
            ("both", "Lưu cả hai (PC + Ngân hàng câu hỏi)", "#0EA5E9"),
            ("PC", "Chỉ lưu PC (Có thể mở lại sau)", "#0284C7"),
            ("bank", "Chỉ lưu vào Ngân hàng câu hỏi", "#8B5CF6"),
            ("none", "Bỏ qua (không lưu)", "#94A3B8"),
        ]
        _save_btns: dict[str, tk.Label] = {}

        def _select_save(v):
            save_var.set(v)
            for k, btn in _save_btns.items():
                color = next(c for vv, _, c in _SAVE_OPTS if vv == k)
                btn.configure(bg=color if k == v else "#F1F5F9", fg="white" if k == v else "#475569", relief="flat")

        for val, label, color in _SAVE_OPTS:
            is_sel = val == "both"
            lbl = tk.Label(opt_f, text=f"  {label}  ", bg=color if is_sel else "#F1F5F9", fg="white" if is_sel else "#475569", font=("Segoe UI", 9, "bold"), cursor="hand2", relief="flat", padx=8, pady=6, anchor="w")
            lbl.pack(fill="x", pady=2)
            lbl.bind("<Button-1>", lambda e, v=val: _select_save(v))
            _save_btns[val] = lbl

        def choose_folder():
            from tkinter import filedialog as _fd
            from config import EXPORT_DIR
            d = _fd.askdirectory(title="Chọn thư mục lưu file xuất", initialdir=getattr(self._tab_result, "_save_dir", str(EXPORT_DIR)), parent=win)
            if d:
                self._tab_result._save_dir = d
                folder_lbl.config(text=f"Thư mục: {d}", fg="#059669")

        def do_save():
            choice = save_var.get()
            subject = self._tab_config.get_subject()
            grade   = self._tab_config.get_grade()
            saved_session = False

            if choice in ("both", "PC"):
                try:
                    self._session_autosave()
                    saved_session = True
                except Exception as e: messagebox.showwarning("Lỗi lưu PC", str(e), parent=win)

            if choice in ("both", "bank"):
                valid_qs = [q for q in exam.questions if not q._error]
                if valid_qs:
                    from ui.dialog_nhch_preview import NHCHPreviewDialog

                    def _do_bank_save(questions):
                        try:
                            from storage.database import save_questions
                            n = save_questions(questions, subject, grade, source=exam.exam_title)
                            if "tab_bank" in self._lazy_loaded:
                                self._tab_bank.refresh()
                            parts = []
                            if n > 0: parts.append(f"{n} câu đã lưu vào NHCH")
                            if saved_session: parts.append("PC đã lưu")
                            if parts: self._set_status("  |  ".join(parts))
                        except Exception as e: messagebox.showwarning("Lỗi lưu NHCH", str(e))

                    win.destroy()
                    NHCHPreviewDialog(self, valid_qs, subject, grade, on_confirm=_do_bank_save)
                    return

            win.destroy()
            if choice == "none": return
            parts = []
            if saved_session: parts.append("PC đã lưu")
            if parts: self._set_status("  |  ".join(parts))

        from config import EXPORT_DIR
        fld_f = tk.Frame(win, bg="#FFFFFF"); fld_f.pack(fill="x", padx=24, pady=4)
        tk.Label(fld_f, text="Thư mục xuất file:", bg="#FFFFFF", font=("Segoe UI", 9)).pack(side="left")
        folder_lbl = tk.Label(fld_f, text=f"Mặc định: {str(EXPORT_DIR)}", fg="#64748B", bg="#FFFFFF", font=("Segoe UI", 8))
        folder_lbl.pack(side="left", padx=6)
        tk.Button(fld_f, text="  📂 Chọn...  ", font=("Segoe UI", 8, "bold"), bg="#E2E8F0", fg="#334155", activebackground="#CBD5E1", relief="flat", cursor="hand2", pady=2, command=choose_folder).pack(side="left")

        btn_f = tk.Frame(win, bg="#FFFFFF"); btn_f.pack(pady=16)
        tk.Button(btn_f, text="  Xác nhận  ", font=("Segoe UI", 10, "bold"), bg="#10B981", fg="white", activebackground="#059669", relief="flat", cursor="hand2", padx=14, pady=7, command=do_save).pack(side="left", padx=8)
        tk.Button(btn_f, text="  Bỏ qua  ", font=("Segoe UI", 10), bg="#F1F5F9", fg="#475569", activebackground="#E2E8F0", relief="flat", cursor="hand2", padx=14, pady=7, command=win.destroy).pack(side="left")

    def _on_gen_error(self, err: str) -> None:
        self._progress_bar.stop()
        self._gen_btn.config(state="normal")
        self._progress_lbl.config(text="❌ Lỗi!")
        self._set_status("❌ Lỗi tạo đề")

        # Cập nhật progress panel: hiển thị lỗi rồi ẩn
        import time as _time
        elapsed = _time.time() - self._gen_start_time if self._gen_start_time else 0
        m, s = divmod(int(elapsed), 60)
        err_time = f"⏱ {m:02d}:{s:02d}"
        self._prog_status.configure(text="❌ Lỗi tạo đề!")
        self._prog_pct.configure(text="")
        self._prog_elapsed.configure(text=err_time)
        self._progress_time_lbl.configure(text=f"❌ {err_time}")
        self._runtime_var.set(f"Lỗi sau  {err_time}")
        self._gen_start_time = 0.0
        self._prog_detail.configure(text=str(err)[:80])
        self.after(5000, self._hide_progress_panel)

        messagebox.showerror("Lỗi tạo đề", err)

    # ══════════════════════════════════════════════════════════════════════
    #  SESSION
    # ══════════════════════════════════════════════════════════════════════

    def _collect_session_args(self) -> dict:
        return dict(
            subject=self._tab_config.get_subject(),
            grade=self._tab_config.get_grade(),
            semester=self._tab_config.get_semester(),
            year=self._tab_config.get_year(),
            provider=self._tab_config.get_provider(),
            model=self._tab_config.get_model(),
            matrix_data=self._matrix_data,
            table_rows=self._tab_matrix.get_all_rows(),
            exam_data=self._exam_data,
        )

    def _session_autosave(self) -> None:
        try:
            path = autosave_session(**self._collect_session_args())
            self._session_lbl.config(text=f"AutoSave: {Path(path).name}")
            # Refresh history tab (only if already loaded)
            if "tab_history" in self._lazy_loaded and hasattr(self._tab_history, 'refresh'):
                self._tab_history.refresh()
        except Exception as e:
            # Không hiện dialog để tránh phiền user mỗi vòng autosave — chỉ
            # log + cập nhật status bar cho user biết có vấn đề.
            _log.warning("Autosave failed: %s", e, exc_info=True)
            try:
                self._session_lbl.config(text="AutoSave: lỗi (xem app.log)")
            except Exception:
                pass

    def _session_save(self) -> None:
        if self._current_session_path:
            try:
                save_session(self._current_session_path, **self._collect_session_args())
                self._set_status(f"💾 Đã lưu: {Path(self._current_session_path).name}")
            except Exception as e: messagebox.showerror("Lỗi lưu phiên", str(e))
        else: self._session_save_as()

    def _session_save_as(self) -> None:
        if not self._matrix_data and not self._exam_data:
            messagebox.showinfo("Chưa có dữ liệu", "Hãy tải ma trận hoặc tạo đề trước.")
            return
        import datetime
        subj = self._tab_config.get_subject().replace(" ", "_")
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("Phiên làm việc", "*.json")],
            initialdir=str(SESSION_DIR), initialfile=f"phien_{subj}_{ts}.json", title="Lưu phiên làm việc",
        )
        if not path: return
        try:
            save_session(path, **self._collect_session_args())
            self._current_session_path = path
            self.title(f"🎓 Tạo đề kiểm tra  —  {Path(path).name}")
            self._set_status(f"💾 Đã lưu: {Path(path).name}")
        except Exception as e: messagebox.showerror("Lỗi lưu", str(e))

    def _session_open(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Phiên làm việc", "*.json")], initialdir=str(SESSION_DIR), title="Mở phiên làm việc")
        if not path: return
        try:
            data = load_session(path)
            self._restore_session(data)
            self._current_session_path = path
            self.title(f"🎓 Tạo đề kiểm tra  —  {Path(path).name}")
        except Exception as e: messagebox.showerror("Lỗi mở phiên", str(e))

    def _session_recent(self) -> None:
        from ui.dialogs import SessionDialog
        SessionDialog(self, on_open_cb=lambda data, path: (
            self._restore_session(data),
            setattr(self, "_current_session_path", path),
        ))

    def _restore_session(self, data: dict) -> None:
        # Thông báo cho user nếu phiên được migrate từ version cũ
        migration_warnings = data.get("_migration_warnings") or []
        if migration_warnings:
            messagebox.showinfo(
                "Đã nâng cấp phiên cũ",
                "Phiên làm việc được tạo bởi phiên bản MatrixExamAI cũ — "
                "hệ thống đã tự động nâng cấp cấu trúc:\n\n  • "
                + "\n  • ".join(migration_warnings)
                + "\n\nKhuyến nghị: lưu lại phiên (Ctrl+S) để dùng định dạng mới.",
            )

        self._tab_config.subject_var.set(data.get("subject", ""))
        self._tab_config.grade_var.set(data.get("grade", ""))
        self._tab_config.semester_var.set(data.get("semester", ""))
        self._tab_config.year_var.set(data.get("year", ""))
        self._tab_config.provider_var.set(data.get("provider", "Google Gemini"))
        self._tab_config.model_var.set(data.get("model", ""))
        self._tab_config._update_model_desc()

        if data.get("matrix_data"):
            try:
                self._matrix_data = MatrixData.from_dict(data["matrix_data"])
            except Exception as e:
                _log.error("restore matrix_data failed: %s", e, exc_info=True)
                self._matrix_data = None

        if data.get("table_rows"):
            try:
                rows = [MatrixRow.from_dict(r) for r in data["table_rows"]]
                self._tab_matrix.set_rows(rows)
                self._nb.select(1)
            except Exception as e:
                _log.error("restore table_rows failed: %s", e, exc_info=True)
                messagebox.showwarning(
                    "Lỗi khôi phục ma trận",
                    f"Không khôi phục được bảng ma trận:\n{e}\n"
                    "Phần còn lại của phiên vẫn được tải.")

        if data.get("exam_data"):
            try:
                exam = ExamData.from_dict(data["exam_data"])
                self._exam_data = exam
                self._update_exam_info_bar()  # [FRICTION-3 lite]
                self._ensure_tab_loaded("tab_result")
                self._tab_result.load_exam(exam)
                self._nb.select(2)
            except Exception as e:
                _log.error("restore exam_data failed: %s", e, exc_info=True)
                messagebox.showwarning(
                    "Lỗi khôi phục đề",
                    f"Không khôi phục được dữ liệu đề:\n{e}\n"
                    "Phần còn lại của phiên vẫn được tải.")

        self._set_status(f"✅ Đã mở phiên: {data.get('saved_at','')[:16]}")

    # ══════════════════════════════════════════════════════════════════════
    #  NGÂN HÀNG
    # ══════════════════════════════════════════════════════════════════════

    def _save_to_bank(self) -> None:
        if not self._exam_data:
            messagebox.showwarning("Chưa có đề", "Vui lòng tạo đề trước.")
            return
        subject = self._tab_config.get_subject()
        grade   = self._tab_config.get_grade()
        valid_qs = [q for q in self._exam_data.questions if not q._error]
        if not valid_qs:
            messagebox.showwarning("Không có câu hỏi", "Không có câu hỏi hợp lệ để lưu.")
            return

        from ui.dialog_nhch_preview import NHCHPreviewDialog
        source = self._exam_data.exam_title

        def _do_save(questions):
            try:
                n = save_questions(questions, subject, grade, source=source)
                messagebox.showinfo("✅ Đã lưu", f"Lưu {n} câu vào ngân hàng thành công!")
                self._ensure_tab_loaded("tab_bank")
                self._tab_bank.refresh()
                self._nb.select(3)
            except Exception as e: messagebox.showerror("Lỗi lưu ngân hàng", str(e))

        NHCHPreviewDialog(self, valid_qs, subject, grade, on_confirm=_do_save)

    def _show_bank_stats(self) -> None:
        from storage.database import db_stats
        try:
            s = db_stats()
            lines = [f"Tổng: {s['total']} câu", "", "Theo môn/lớp:", *[f"  {k}: {v}" for k, v in s.get("by_subject", {}).items()], "", "Theo loại:", *[f"  {k}: {v}" for k, v in s.get("by_type", {}).items()], "", "Theo mức:", *[f"  {k}: {v}" for k, v in s.get("by_level", {}).items()]]
            messagebox.showinfo("📊 Thống kê ngân hàng", "\n".join(lines))
        except Exception as e: messagebox.showerror("Lỗi", str(e))

    def _open_import_pdf_dialog(self) -> None:
        """Wizard: Import đề PDF/Word/Ảnh → AI Vision/OCR → NHCH."""
        from ui.dialog_import_pdf import open_import_pdf_dialog
        subject = "Toán"
        grade = "12"
        try:
            if hasattr(self, "_tab_config"):
                subject = (getattr(self._tab_config, "_subject_var", None)
                            and self._tab_config._subject_var.get()) or "Toán"
                grade = (getattr(self._tab_config, "_grade_var", None)
                          and self._tab_config._grade_var.get()) or "12"
        except Exception:
            pass
        open_import_pdf_dialog(
            self, subject=subject, grade=grade,
            tab_config=getattr(self, "_tab_config", None),
        )

    # ══════════════════════════════════════════════════════════════════════
    #  CACHE
    # ══════════════════════════════════════════════════════════════════════

    def _show_cache_stats(self) -> None:
        s = self._cache.stats()
        messagebox.showinfo("📊 Cache", f"RAM entries : {s['memory_entries']}\nFile entries: {s['file_entries']}\nDung lượng  : {s['total_size_kb']} KB")

    def _clear_cache(self) -> None:
        if messagebox.askyesno("Xóa cache", "Xóa toàn bộ cache AI?"):
            n = self._cache.clear_all()
            messagebox.showinfo("✅ Đã xóa", f"Đã xóa {n} file cache.")

    # ══════════════════════════════════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def _choose_source(self) -> None:
        from ui.dialogs_new import SourceSelectorDialog
        def on_confirm(mode, ratio):
            self._source_mode  = mode
            self._source_ratio = ratio
            mode_labels = {"ai_only": "✨ AI mới hoàn toàn", "bank_only": "📚 100% từ NHCH", "mixed": f"🔀 Kết hợp ({ratio}% NHCH)"}
            self._src_btn.config(text=f"  {mode_labels.get(mode,mode)}  ")
            self._set_status(f"✅ Chế độ: {mode_labels.get(mode,mode)}")
        SourceSelectorDialog(self, on_confirm_cb=on_confirm)

    def _toggle_theme(self) -> None:
        """P1.8: Chuyển Light ↔ Dark mode. Cần restart để áp dụng đầy đủ."""
        from ui.theme import get_active_theme, set_active_theme
        current = get_active_theme()
        new = "dark" if current == "light" else "light"
        set_active_theme(new)
        msg_label = "Dark" if new == "dark" else "Light"
        ans = messagebox.askyesno(
            "Đổi giao diện",
            f"Đã chọn chế độ: {msg_label}.\n\n"
            "Cần KHỞI ĐỘNG LẠI app để áp dụng đầy đủ.\n"
            "Bạn có muốn khởi động lại ngay?",
            parent=self,
        )
        if ans:
            try:
                import os, sys
                python = sys.executable
                os.execl(python, python, *sys.argv)
            except Exception as e:
                messagebox.showinfo(
                    "Vui lòng restart",
                    f"Không tự restart được ({e}). Hãy đóng và mở lại app.",
                    parent=self,
                )

    def _open_exam_history(self) -> None:
        """P1.7: Mở dialog xem lịch sử phiên bản đề và restore."""
        from ui.dialog_exam_history import ExamHistoryDialog
        dlg = ExamHistoryDialog(self, on_restore=self._restore_exam_version)
        self.wait_window(dlg)

    def _restore_exam_version(self, exam_data_dict: dict) -> None:
        """Callback từ ExamHistoryDialog — restore exam từ snapshot dict."""
        try:
            from core.models import ExamData, Question
            exam = ExamData.from_dict(exam_data_dict) \
                if hasattr(ExamData, "from_dict") else None
            if exam is None:
                # Fallback build manually
                exam = ExamData(
                    exam_title=exam_data_dict.get("exam_title", ""),
                    subject=exam_data_dict.get("subject", ""),
                    grade=exam_data_dict.get("grade", ""),
                    semester=exam_data_dict.get("semester", "1"),
                    year=exam_data_dict.get("year", ""),
                    time=exam_data_dict.get("time", "90 phút"),
                )
                # Try to populate questions
                qs_data = exam_data_dict.get("questions", [])
                if hasattr(Question, "from_dict"):
                    exam.questions = [Question.from_dict(q) for q in qs_data]
            self._exam_data = exam
            self._update_exam_info_bar()  # [FRICTION-3 lite]
            self._ensure_tab_loaded("tab_result")
            self._tab_result.set_exam(exam)
            self._nb.select(self._tab_result)
            self._set_status(
                f"✅ Đã khôi phục đề: {len(exam.questions)} câu"
            )
        except Exception as e:
            messagebox.showerror(
                "Lỗi khôi phục",
                f"Không khôi phục được: {e}", parent=self,
            )

    def _open_settings_dialog(self) -> None:
        """Mở dialog cài đặt ứng dụng (NHCH, auto-start, open-after-export, v3 engine)."""
        tc = self._tab_config
        win = tk.Toplevel(self)
        win.title("⚙ Cài đặt ứng dụng")
        win.geometry("560x340")
        win.resizable(False, False)
        win.grab_set()
        win.configure(bg="#FFFFFF")

        ga = tk.Frame(win, bg="#FFFFFF")
        ga.pack(fill="x", padx=16, pady=16)
        ga.columnconfigure(1, weight=1)

        tk.Label(ga, text="Thư mục NHCH:", bg="#FFFFFF", fg="#334155",
                 font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(ga, textvariable=tc._nhch_var, width=48).grid(
            row=0, column=1, sticky="ew", padx=6, pady=6)
        ttk.Button(ga, text="📂 Duyệt...", width=10,
                   command=lambda: self._browse_nhch_dialog(tc, win)).grid(
            row=0, column=2, padx=4, pady=6)

        tk.Checkbutton(ga, text="Khởi động ExamAI cùng Windows",
                       variable=tc._autostart_var, bg="#FFFFFF", fg="#334155",
                       font=("Segoe UI", 10),
                       command=tc._toggle_autostart).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=4)

        tk.Checkbutton(ga, text="Mở file Word sau khi xuất",
                       variable=tc._open_after_var, bg="#FFFFFF", fg="#334155",
                       font=("Segoe UI", 10),
                       command=tc._save_app_settings).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=4)

        backup_row = tk.Frame(ga, bg="#FFFFFF")
        backup_row.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 2))
        tk.Button(
            backup_row,
            text="🧰 Tạo backup dữ liệu...",
            bg="#10B981", fg="white", activebackground="#059669",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
            padx=10, pady=4,
            command=lambda: self._create_local_backup_dialog(win),
        ).pack(side="left")
        tk.Button(
            backup_row,
            text="↩ Khôi phục...",
            bg="#6366F1", fg="white", activebackground="#4F46E5",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
            padx=10, pady=4,
            command=lambda: self._restore_local_backup_dialog(win),
        ).pack(side="left", padx=(6, 0))
        tk.Label(
            backup_row,
            text="Backup/restore NHCH local, phiên làm việc, settings và kho hình.",
            bg="#FFFFFF", fg="#64748B", font=("Segoe UI", 8),
        ).pack(side="left", padx=8)

        # MEA v3 toggle tạm ẩn ở bản v4.0.x — xem chú thích trong config.py.

        btn_f = tk.Frame(win, bg="#FFFFFF")
        btn_f.pack(pady=12)
        tk.Button(btn_f, text="  💾 Lưu cài đặt  ", bg="#0EA5E9", fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", cursor="hand2",
                  command=lambda: [tc._save_app_settings(), win.destroy()]).pack(
            side="left", padx=6)
        ttk.Button(btn_f, text="Đóng", command=win.destroy).pack(side="left", padx=6)

    def _browse_nhch_dialog(self, tc, parent) -> None:
        d = filedialog.askdirectory(
            title="Chọn thư mục lưu Ngân hàng câu hỏi",
            initialdir=tc._nhch_var.get(), parent=parent)
        if d:
            tc._nhch_var.set(d)
            tc._save_app_settings()

    def _create_local_backup_dialog(self, parent) -> None:
        target = filedialog.askdirectory(
            title="Chọn thư mục lưu backup dữ liệu",
            initialdir=str(APP_DIR / "backups"),
            parent=parent,
        )
        if not target:
            return
        try:
            from services.local_backup import create_local_backup

            result = create_local_backup(output_dir=target)
            size_mb = result.total_bytes / (1024 * 1024)
            messagebox.showinfo(
                "Backup hoàn tất",
                (
                    f"Đã tạo backup dữ liệu:\n{result.path}\n\n"
                    f"Số file: {result.file_count}\n"
                    f"Dung lượng dữ liệu: {size_mb:.2f} MB"
                ),
                parent=parent,
            )
            self._set_status(f"Đã tạo backup dữ liệu: {result.path}")
            try:
                from services.task_events import record_task_event
                record_task_event(
                    kind="backup",
                    title="Tạo backup dữ liệu",
                    status="success",
                    message=f"{result.file_count} file, {size_mb:.2f} MB",
                    meta={"path": str(result.path)},
                )
            except Exception:
                pass
        except Exception as exc:
            try:
                from services.task_events import record_task_event
                record_task_event(
                    kind="backup",
                    title="Tạo backup dữ liệu",
                    status="error",
                    message=str(exc),
                )
            except Exception:
                pass
            messagebox.showerror("Lỗi backup", f"Không tạo được backup: {exc}", parent=parent)

    def _restore_local_backup_dialog(self, parent) -> None:
        backup_file = filedialog.askopenfilename(
            title="Chọn file backup dữ liệu MatrixExamAI",
            initialdir=str(APP_DIR / "backups"),
            filetypes=[
                ("MatrixExamAI backup", "MEA_backup_*.zip"),
                ("Zip file", "*.zip"),
                ("Tất cả file", "*.*"),
            ],
            parent=parent,
        )
        if not backup_file:
            return
        try:
            from services.local_backup import preview_local_backup, restore_local_backup

            preview = preview_local_backup(backup_file)
            size_mb = preview.total_bytes / (1024 * 1024)
            warning_text = ""
            if preview.warnings:
                warning_text = "\n\nCảnh báo:\n- " + "\n- ".join(preview.warnings[:5])
                if len(preview.warnings) > 5:
                    warning_text += f"\n- ... và {len(preview.warnings) - 5} cảnh báo khác"

            ok = messagebox.askyesno(
                "Xác nhận khôi phục backup",
                (
                    f"File backup:\n{preview.path}\n\n"
                    f"Ngày tạo: {preview.created_at or 'không rõ'}\n"
                    f"Số file sẽ khôi phục: {preview.file_count}\n"
                    f"Dung lượng dữ liệu: {size_mb:.2f} MB\n\n"
                    "App sẽ tạo một restore-point trước khi ghi đè dữ liệu hiện tại."
                    f"{warning_text}\n\n"
                    "Tiếp tục khôi phục?"
                ),
                parent=parent,
            )
            if not ok:
                return

            result = restore_local_backup(
                backup_file,
                overwrite=True,
                create_restore_point=True,
            )
            restore_point_text = f"\nRestore-point: {result.restore_point}" if result.restore_point else ""
            result_warning_text = ""
            if result.warnings:
                result_warning_text = "\n\nCảnh báo:\n- " + "\n- ".join(result.warnings[:5])
                if len(result.warnings) > 5:
                    result_warning_text += f"\n- ... và {len(result.warnings) - 5} cảnh báo khác"

            messagebox.showinfo(
                "Khôi phục hoàn tất",
                (
                    f"Đã khôi phục {result.restored_count} file từ backup.\n"
                    f"Bỏ qua: {result.skipped_count} file"
                    f"{restore_point_text}\n\n"
                    "Nên khởi động lại app để mọi cài đặt được nạp lại đầy đủ."
                    f"{result_warning_text}"
                ),
                parent=parent,
            )
            self._set_status(
                f"Đã khôi phục backup: {result.restored_count} file, bỏ qua {result.skipped_count} file"
            )
            try:
                from services.task_events import record_task_event
                record_task_event(
                    kind="restore",
                    title="Khôi phục backup dữ liệu",
                    status="success",
                    message=f"{result.restored_count} file, bỏ qua {result.skipped_count}",
                    meta={
                        "path": str(result.path),
                        "restore_point": str(result.restore_point) if result.restore_point else "",
                    },
                )
            except Exception:
                pass
        except Exception as exc:
            try:
                from services.task_events import record_task_event
                record_task_event(
                    kind="restore",
                    title="Khôi phục backup dữ liệu",
                    status="error",
                    message=str(exc),
                )
            except Exception:
                pass
            messagebox.showerror("Lỗi khôi phục backup", f"Không khôi phục được backup: {exc}", parent=parent)

    def _open_ai_gen_matrix(self) -> None:
        """Mở dialog tạo ma trận đề bằng AI."""
        if self._license_locked:
            messagebox.showwarning("Đã hết hạn",
                "Giấy phép đã hết hạn.\nVui lòng liên hệ admin để gia hạn.")
            return
        from ui.dialog_ai_gen_matrix import AIGenMatrixDialog
        dlg = AIGenMatrixDialog(self, get_ai_call=self._make_ai_call)
        self.wait_window(dlg)
        if dlg.result is not None:
            self._matrix_data = dlg.result
            self._tab_matrix.load_matrix(dlg.result)
            self._tab_config.matrix_data = dlg.result
            self._set_status(
                f"🤖 Ma trận AI: {len(dlg.result.rows)} câu — "
                f"{dlg.result.title}")
            self._nb.select(1)  # Chuyển sang tab Ma trận

    # ══════════════════════════════════════════════════════════════════════
    #  [SPEED-5] Recent Exams Dropdown
    # ══════════════════════════════════════════════════════════════════════

    def _toggle_recent_dropdown(self) -> None:
        """Toggle dropdown 5 phiên gần nhất từ exam_history."""
        from ui.dropdown_recent import RecentExamsDropdown

        # Tạo lần đầu, sau đó reuse — show() có toggle behavior
        if self._recent_dropdown is None:
            self._recent_dropdown = RecentExamsDropdown(
                anchor=self._recent_btn,
                on_restore=self._on_recent_picked,
                limit=5,
            )
            # Link "Xem tất cả →" → mở tab Lịch sử
            self._recent_dropdown.set_view_all_callback(
                lambda: (self._ensure_tab_loaded("tab_history"),
                         self._nb.select(self._tab_history)))

        self._recent_dropdown.show()

    def _on_recent_picked(self, exam) -> None:
        """Callback khi user pick 1 đề từ dropdown.

        Load vào TabResult + chuyển tab + báo trạng thái. KHÔNG snapshot lại
        (snapshot chỉ ở `_on_gen_done` để tránh duplicate).
        """
        try:
            self._exam_data = exam
            self._update_exam_info_bar()  # [FRICTION-3 lite]
            self._ensure_tab_loaded("tab_result")
            self._tab_result.load_exam(exam)
            self._nb.select(self._tab_result)
            stats = exam.stats
            msg = (
                f"📂 Đã mở lại: {exam.exam_title[:60]} | "
                f"{stats['total']} câu (TN {stats['TN']}, DS {stats['DS']}, "
                f"TLN {stats['TLN']}, TL {stats['TL']})"
            )
            self._set_status(msg)
        except Exception as e:
            messagebox.showerror("Lỗi mở đề", f"Không khôi phục được: {e}")

    def _open_smart_prompt(self) -> None:
        """Smart Prompt: GV nhập tự nhiên, hệ thống tự tạo ma trận hoặc tạo câu hỏi đơn lẻ."""
        if self._license_locked:
            messagebox.showwarning("Đã hết hạn",
                "Giấy phép đã hết hạn.\nVui lòng liên hệ admin để gia hạn.")
            return
        if not self._is_feature_enabled("smart_prompt"):
            messagebox.showinfo("Nâng cấp gói",
                "Smart Prompt chỉ dành cho gói PRO / Premium.\nVui lòng nâng cấp để sử dụng.")
            return

        from ui.dialog_smart_prompt import SmartPromptDialog

        def on_apply_matrix(matrix, subject, grade):
            self._matrix_data = matrix
            self._tab_matrix.load_matrix(matrix)
            self._tab_config.subject_var.set(subject)
            self._tab_config.grade_var.set(grade)
            self._tab_config.matrix_data = matrix
            self._set_status(
                f"💬 Smart Prompt: {len(matrix.rows)} câu — "
                f"Nhấn 'Tạo đề bằng AI' để sinh đề")
            self._nb.select(1)

        def on_add_to_bank(q, subject, grade):
            from storage.database import save_questions
            save_questions([q], subject, grade, source="Smart Prompt")

        def get_ai_service():
            provider = self._tab_config.get_provider()
            keys = self._tab_config.get_api_keys()
            model = self._tab_config.get_model()
            if not keys or not keys[0]:
                raise ValueError("Vui lòng nhập API Key ở tab Cài đặt ⚙️.")
            return create_ai_service(provider, keys, model)

        SmartPromptDialog(
            self,
            get_ai_call=self._make_ai_call,
            get_ai_service=get_ai_service,
            on_apply_matrix=on_apply_matrix,
            on_add_to_bank=on_add_to_bank,
            default_subject=self._tab_config.get_subject(),
            default_grade=self._tab_config.get_grade(),
        )

    def _open_quick_gen(self) -> None:
        if self._license_locked:
            messagebox.showwarning("Đã hết hạn",
                "Giấy phép đã hết hạn. Không thể tạo đề nhanh.\nVui lòng liên hệ admin để gia hạn.")
            return
        if not self._is_feature_enabled("quick_gen"):
            messagebox.showinfo("Nâng cấp gói",
                "Tính năng Tạo đề nhanh chỉ dành cho gói PRO / Premium.\nVui lòng nâng cấp để sử dụng.")
            return
        from ui.dialog_quick_gen import QuickGenDialog
        def on_accept(matrix_data, subject, grade):
            self._matrix_data = matrix_data
            self._tab_matrix.load_matrix(matrix_data)
            self._tab_config.subject_var.set(subject)
            self._tab_config.grade_var.set(grade)
            self._tab_config.matrix_data = matrix_data
            self._set_status(f"⚡ Ma trận nhanh: {len(matrix_data.rows)} câu — Nhấn 'Tạo đề bằng AI' để sinh đề")
            self._nb.select(1)
        QuickGenDialog(self, on_accept=on_accept)

    def _add_q_to_exam(self, q: "Question", *, _batch: bool = False) -> None:
        if not self._exam_data:
            from core.models import ExamData
            subject, grade, time, semester, year = self._tab_config.get_subject(), self._tab_config.get_grade(), self._tab_config.get_time(), self._tab_config.get_semester(), self._tab_config.get_year()
            self._exam_data = ExamData(exam_title=f"ĐỀ KIỂM TRA - {subject.upper()} {grade}", subject=subject, grade=grade, semester=semester, year=year, time=time)
        self._exam_data.questions.append(q)
        if not _batch:
            self._ensure_tab_loaded("tab_result")
            self._tab_result.load_exam(self._exam_data)
            self._nb.select(2)

    def _flush_exam_ui(self) -> None:
        if self._exam_data:
            self._ensure_tab_loaded("tab_result")
            self._tab_result.load_exam(self._exam_data)
            self._nb.select(2)

    def _set_status(self, msg: str) -> None:
        self._status_var.set(msg)

    def _check_deps(self) -> None:
        """Kiểm tra dependencies — chạy background để không block startup."""
        import threading
        def _check():
            missing = []
            try: from docx import Document
            except ImportError: missing.append("python-docx   →  pip install python-docx")
            if missing:
                self.after(0, lambda: messagebox.showwarning(
                    "Thiếu thư viện",
                    "Các thư viện bắt buộc chưa cài:\n\n" + "\n".join(missing)))
        threading.Thread(target=_check, daemon=True).start()

    # ══════════════════════════════════════════════════════════════════════
    #  PROMPT MANAGER + MONITORING
    # ══════════════════════════════════════════════════════════════════════

    def _open_prompt_manager(self) -> None:
        win = tk.Toplevel(self); win.title("Quản lý Prompt Versions"); win.geometry("860x540"); win.configure(bg="#FFFFFF")
        cols = ("Version ID", "Name", "Đúng", "A/B Score", "Ngày tạo", "Mô tả")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=16)
        for c, w in [("Version ID",160),("Name",100),("Đúng",55), ("A/B Score",80),("Ngày tạo",130),("Mô tả",240)]: tree.heading(c, text=c); tree.column(c, width=w)
        tree.pack(fill="both", expand=True, padx=8, pady=8)

        def refresh():
            tree.delete(*tree.get_children())
            for p in list_prompts(): tree.insert("", "end", iid=p["version_id"], values=(p["version_id"], p["name"], "Active" if p.get("is_active") else "", f"{p['ab_score']:.3f}" if p.get("ab_score") else "-", p.get("created_at","")[:16], p.get("description","")[:60]))
        refresh()

        def on_set_active():
            sel = tree.selection()
            if not sel: return
            vid, name = sel[0], tree.item(sel[0])["values"][1]
            set_active_prompt(name, vid); refresh(); messagebox.showinfo("Đã đặt", f"Active: {vid}")

        def on_view():
            sel = tree.selection()
            if not sel: return
            text = load_prompt(sel[0]) or "(Không tìm thấy)"
            d = tk.Toplevel(win); d.title(f"Nội dung: {sel[0]}"); d.geometry("700x500"); d.configure(bg="#FFFFFF")
            from tkinter import scrolledtext as _st
            t = _st.ScrolledText(d, wrap="word", font=("Consolas",9), bg="#F8FAFC"); t.pack(fill="both", expand=True, padx=8, pady=8); t.insert("end", text); t.config(state="disabled")

        bf = tk.Frame(win, bg="#FFFFFF"); bf.pack(pady=6)
        tk.Button(bf, text="  ✅ Đặt làm Active  ", font=("Segoe UI", 9, "bold"), bg="#10B981", fg="white", activebackground="#059669", relief="flat", cursor="hand2", pady=4, command=on_set_active).pack(side="left", padx=6)
        tk.Button(bf, text="  📄 Xem nội dung  ", font=("Segoe UI", 9, "bold"), bg="#0EA5E9", fg="white", activebackground="#0284C7", relief="flat", cursor="hand2", pady=4, command=on_view).pack(side="left", padx=6)
        tk.Button(bf, text="  Đóng  ", font=("Segoe UI", 9), bg="#F1F5F9", fg="#475569", activebackground="#E2E8F0", relief="flat", cursor="hand2", pady=4, command=win.destroy).pack(side="left", padx=6)

    def _open_monitoring(self) -> None:
        from services.logger import get_monitor_stats, get_log_tail
        win = tk.Toplevel(self); win.title("Logs & Monitoring"); win.geometry("860x560"); win.configure(bg="#FFFFFF")
        nb2 = ttk.Notebook(win); nb2.pack(fill="both", expand=True)
        stat_f, log_f = ttk.Frame(nb2), ttk.Frame(nb2)
        nb2.add(stat_f, text="  Thống kê 24h  "); nb2.add(log_f, text="  Log gần nhất  ")

        from tkinter import scrolledtext as _st
        stat_txt = _st.ScrolledText(stat_f, font=("Segoe UI",10), bg="#F8FAFC", state="disabled"); stat_txt.pack(fill="both", expand=True, padx=8, pady=8)

        def load_stats():
            s = get_monitor_stats(24)
            lines = [f"Thống kê 24 giờ gần nhất", "=" * 45, f"Tổng gọi API:    {s.get('total_calls',0)}", f"Thành công:      {s.get('ok_calls',0)} ({s.get('success_rate',0)}%)", f"Lỗi:             {s.get('error_calls',0)} ({s.get('error_rate',0)}%)", f"Retry:           {s.get('retry_calls',0)}", f"Latency TB:      {s.get('avg_latency_ms',0)}ms", f"Điểm CL TB:      {s.get('avg_score',0):.3f}", "", "Theo model:"]
            for m, cnt in s.get("by_model",{}).items(): lines.append(f"  {m}: {cnt} gọi, {s.get('model_errors',{}).get(m, 0)} lỗi")
            lines += ["", " Lỗi gần nhất:"]
            for e in s.get("recent_errors",[])[:5]: lines.append(f"  {e.get('created_at','')[:16]} [{e.get('model','')}] {e.get('error_type','')[:50]}")
            stat_txt.config(state="normal"); stat_txt.delete("1.0","end"); stat_txt.insert("end", "\n".join(lines)); stat_txt.config(state="disabled")

        load_stats()
        tk.Button(stat_f, text="  🔄 Làm mới  ", font=("Segoe UI", 9, "bold"), bg="#0EA5E9", fg="white", activebackground="#0284C7", relief="flat", cursor="hand2", pady=3, command=load_stats).pack(pady=4)

        cols2 = ("Thời gian","Event","Model","Topic","Latency","Score","Lỗi")
        log_tree = ttk.Treeview(log_f, columns=cols2, show="headings", height=18)
        for c, w in [("Thời gian",120),("Event",70),("Model",130), ("Topic",130),("Latency",70),("Score",65),("Lỗi",180)]: log_tree.heading(c,text=c); log_tree.column(c,width=w)
        log_tree.tag_configure("error", background="#FEE2E2"); log_tree.tag_configure("retry", background="#FEF3C7")
        log_tree.pack(fill="both", expand=True, padx=8, pady=8)

        def load_logs():
            log_tree.delete(*log_tree.get_children())
            for row in get_log_tail(60):
                tag = "error" if row["event"]=="error" else ("retry" if row["event"]=="retry" else "")
                log_tree.insert("", "end", tags=(tag,), values=(row.get("created_at","")[:16], row.get("event",""), row.get("model","")[:20], row.get("topic","")[:18], f"{row.get('latency_ms',0)}ms", f"{row.get('quality_score',0):.2f}" if row.get("quality_score") else "-", row.get("error_type","")[:50]))

        load_logs()
        tk.Button(log_f, text="  🔄 Làm mới  ", font=("Segoe UI", 9, "bold"), bg="#0EA5E9", fg="white", activebackground="#0284C7", relief="flat", cursor="hand2", pady=3, command=load_logs).pack(pady=4)

    def _switch_to_shuffle_tab(self) -> None:
        """Chuyển trực tiếp sang Tab Trộn đề trong app gốc."""
        try:
            self._ensure_tab_loaded("tab_shuffle")
            tab = getattr(self, "_tab_shuffle", None)
            if tab:
                self._nb.select(tab)
                if hasattr(tab, "check_auto_load_exam"):
                    tab.check_auto_load_exam()
                self._set_status("🎲 Đã chuyển sang Tab Trộn đề thi hoán vị mã đề")
        except Exception as e:
            _log.warning("Switch to shuffle tab failed: %s", e)

    def _open_omr_window(self) -> None:
        """Alias tương thích cũ: chuyển sang Tab Trộn đề trong app gốc thay vì popup rời."""
        self._switch_to_shuffle_tab()
