"""
v5/statusbar.py — Status bar dưới cùng cho ModernApp.

Hiển thị 4 indicator:
    1. 🌐 Online status — ping API/Supabase
    2. 🤖 AI calls hôm nay (đọc từ ai_usage.jsonl)
    3. 🏛 NHCH local count
    4. 📡 Backend status — login state

Tự refresh mỗi 30s.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

import customtkinter as ctk

USAGE_LOG = Path.home() / ".exam_generator" / "ai_usage.jsonl"


class StatusBar(ctk.CTkFrame):
    """Thin frame at bottom of app — show 4 indicators."""

    REFRESH_MS = 30_000   # 30s

    def __init__(self, parent):
        super().__init__(parent, height=28, corner_radius=0,
                          fg_color=("#F1F5F9", "#0F172A"),
                          border_width=0)
        self.pack_propagate(False)

        self._items: dict[str, ctk.CTkLabel] = {}
        # 5 segments (online | ai | nhch | backend | autosave)
        for key, init in [
            ("online",   "🌐 ⋯"),
            ("ai",       "🤖 ⋯"),
            ("nhch",     "🏛 ⋯"),
            ("backend",  "📡 ⋯"),
            ("autosave", "💾 ⋯"),
        ]:
            sep = ctk.CTkLabel(self, text=" │ ",
                                  text_color=("#9CA3AF", "#475569"),
                                  font=("Segoe UI", 9))
            sep.pack(side="left")
            lbl = ctk.CTkLabel(self, text=init,
                                  font=("Segoe UI", 9),
                                  text_color=("#4B5563", "#CBD5E1"))
            lbl.pack(side="left", padx=4)
            self._items[key] = lbl

        # Right side: 🔔 notification button + version
        from v5 import __version__
        ctk.CTkLabel(self, text=f"v{__version__} ",
                      font=("Segoe UI", 9),
                      text_color=("#9CA3AF", "#64748B")
                      ).pack(side="right", padx=4)

        self._notif_btn = ctk.CTkButton(
            self, text="🔔", width=32, height=24,
            font=("Segoe UI", 12),
            fg_color="transparent",
            text_color=("#4B5563", "#CBD5E1"),
            hover_color=("#E5E7EB", "#334155"),
            command=self._open_notif_center)
        self._notif_btn.pack(side="right", padx=2)

        # n27: Crash count badge — đỏ nhỏ ở góc 🔔 nếu có crash unread
        self._crash_badge = ctk.CTkLabel(
            self, text="", width=18, height=14,
            font=("Segoe UI", 8, "bold"),
            fg_color=("#DC2626", "#EF4444"),
            text_color="white",
            corner_radius=7)
        # Sẽ pack có điều kiện trong _refresh_crash_badge()
        self._crash_badge_packed = False

        # Initial + periodic refresh (BUG FIX: trước đây bị lồng trong
        # _open_notif_center → statusbar chỉ refresh sau khi user click 🔔)
        self.after(800, self.refresh)
        self.after(self.REFRESH_MS, self._tick)

    def _open_notif_center(self):
        from v5.toast import NotificationCenter
        NotificationCenter(self.winfo_toplevel())
        # Mark crash count seen
        self._mark_crashes_seen()

    def _refresh_crash_badge(self):
        """Hiển thị badge nhỏ với số crash unread."""
        try:
            from v5.crash_reporter import load_crashes
            from v5 import settings_store
            n = len(load_crashes())
            seen = settings_store.load().get("crashes_seen_count", 0)
            unread = max(0, n - seen)
            if unread > 0:
                txt = str(unread) if unread < 10 else "9+"
                self._crash_badge.configure(text=txt)
                if not self._crash_badge_packed:
                    self._crash_badge.pack(side="right", padx=(0, 1))
                    self._crash_badge_packed = True
            else:
                if self._crash_badge_packed:
                    self._crash_badge.pack_forget()
                    self._crash_badge_packed = False
        except Exception: pass

    def _mark_crashes_seen(self):
        """User click 🔔 → mark all crashes as seen."""
        try:
            from v5.crash_reporter import load_crashes
            from v5 import settings_store
            n = len(load_crashes())
            settings_store.set_value("crashes_seen_count", n)
            self._refresh_crash_badge()
        except Exception: pass

    def _tick(self):
        self.refresh()
        try:
            self.after(self.REFRESH_MS, self._tick)
        except Exception:
            pass

    def refresh(self):
        """Async refresh tất cả indicators."""
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        results: dict[str, tuple[str, str]] = {}

        # 1. Online status (ping Google to check internet)
        try:
            import socket
            socket.setdefaulttimeout(2)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(
                ("8.8.8.8", 53))
            results["online"] = ("🌐 Online", "#10B981")
        except Exception:
            results["online"] = ("🌐 Offline", "#EF4444")

        # 2. AI calls today (count entries in ai_usage.jsonl with today's date)
        n_today = 0
        if USAGE_LOG.exists():
            try:
                today = datetime.now().strftime("%Y-%m-%d")
                for line in USAGE_LOG.read_text(encoding="utf-8").splitlines():
                    try:
                        d = json.loads(line)
                        if d.get("ts", "").startswith(today):
                            n_today += 1
                    except: continue
            except: pass
        color = "#10B981" if n_today > 0 else "#6B7280"
        results["ai"] = (f"🤖 {n_today} calls hôm nay", color)

        # 3. NHCH local count
        try:
            from storage.database import search_questions
            n = len(search_questions() or [])
            results["nhch"] = (f"🏛 {n:,} câu NHCH", "#3B82F6" if n else "#6B7280")
        except Exception:
            results["nhch"] = ("🏛 NHCH —", "#6B7280")

        # 4. Backend status (logged in?)
        try:
            from services import api_client
            if not api_client.is_api_enabled():
                results["backend"] = ("📡 Chưa cấu hình API", "#6B7280")
            elif api_client.is_logged_in():
                tok = api_client.load_token()
                em = (tok.get("email") or "")[:20]
                results["backend"] = (f"📡 {em}", "#10B981")
            else:
                results["backend"] = ("📡 Chưa đăng nhập", "#F59E0B")
        except Exception:
            results["backend"] = ("📡 —", "#6B7280")

        # 5. Autosave indicator (đọc mtime v5_session.json)
        try:
            from v5.session_autosave import _FILE as SESSION_FILE
            if SESSION_FILE.exists():
                from datetime import datetime
                mt = datetime.fromtimestamp(SESSION_FILE.stat().st_mtime)
                ago = (datetime.now() - mt).total_seconds()
                if   ago < 90:      txt = f"💾 Lưu {int(ago)}s trước"
                elif ago < 3600:    txt = f"💾 Lưu {int(ago/60)}p trước"
                elif ago < 86400:   txt = f"💾 Lưu {int(ago/3600)}h trước"
                else:               txt = f"💾 Lưu {int(ago/86400)}d trước"
                color = "#10B981" if ago < 120 else (
                            "#F59E0B" if ago < 3600 else "#6B7280")
                results["autosave"] = (txt, color)
            else:
                results["autosave"] = ("💾 Chưa có phiên", "#6B7280")
        except Exception:
            results["autosave"] = ("💾 —", "#6B7280")

        # Push UI update
        from v5.safe_ui import safe_after
        safe_after(self, 0, lambda: self._render(results))

    def _render(self, results):
        # Guard: nếu widget đã destroy thì bỏ qua (race condition)
        try:
            if not self.winfo_exists(): return
        except Exception: return
        try:
            for key, (text, color) in results.items():
                if key in self._items:
                    self._items[key].configure(text=text, text_color=color)
            # Cập nhật crash badge mỗi lần refresh
            self._refresh_crash_badge()
        except Exception: pass
