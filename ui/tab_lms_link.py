"""
ui/tab_lms_link.py — Tab "🌐 LMS" cho v4 Desktop.

Cho phép:
    1. Cấu hình MEA_API_URL (lưu vào ~/.exam_generator/lms.json)
    2. Login Supabase Auth (email + password)
    3. Kiểm tra trạng thái kết nối (health + license_ping)
    4. Push đề hiện tại lên LMS Web (qua /v1/desktop/sync/exam)
    5. Đẩy NHCH cục bộ lên Cloud (qua /v1/desktop/sync/questions)
    6. Logout

Phụ thuộc: services.api_client, services.license_manager.
"""
from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Optional

from services import api_client

BLUE   = "#1F497D"
GREEN  = "#10B981"
RED    = "#EF4444"
GRAY   = "#6B7280"
BG     = "#F9F7F4"


class TabLMSLink(ttk.Frame):
    """Tab kết nối với Web LMS qua FastAPI Backend."""

    def __init__(self, parent, *,
                 get_current_exam: Optional[Callable[[], Any]] = None,
                 get_nhch_questions: Optional[Callable[[], list]] = None,
                 **kw):
        super().__init__(parent, **kw)
        self._get_current_exam = get_current_exam
        self._get_nhch_questions = get_nhch_questions
        self._busy = False
        self._build()
        self._refresh_status()

    # ──────────────────────────────────────────────────────────────────────
    #  BUILD UI
    # ──────────────────────────────────────────────────────────────────────

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(99, weight=1)

        # ── Header ────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BLUE)
        hdr.grid(row=0, column=0, sticky="ew")
        tk.Label(hdr, text="  🌐  Kết nối Web LMS (MEA v5)",
                 bg=BLUE, fg="white",
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=12, pady=8)

        # ── 1. Cấu hình API URL ──────────────────────────────────────
        f1 = tk.LabelFrame(self, text="  1️⃣  Cấu hình Backend URL  ",
                            bg=BG, fg=BLUE, padx=12, pady=8,
                            font=("Segoe UI", 10, "bold"))
        f1.grid(row=1, column=0, sticky="ew", padx=10, pady=(8, 4))

        tk.Label(f1, text="API URL:", bg=BG, font=("Segoe UI", 10)
                 ).grid(row=0, column=0, sticky="w")
        self._url_var = tk.StringVar(value=api_client.api_url() or
                                            "http://localhost:8000")
        ttk.Entry(f1, textvariable=self._url_var, width=50,
                  font=("Consolas", 10)
                  ).grid(row=0, column=1, sticky="ew", padx=6)
        f1.columnconfigure(1, weight=1)
        tk.Button(f1, text="💾 Lưu URL", bg=BLUE, fg="white",
                  relief="flat", cursor="hand2", padx=10,
                  command=self._save_url
                  ).grid(row=0, column=2, padx=2)
        tk.Button(f1, text="🩺 Test kết nối", bg=GRAY, fg="white",
                  relief="flat", cursor="hand2", padx=10,
                  command=self._test_connection
                  ).grid(row=0, column=3, padx=2)

        self._url_status = tk.Label(f1, text="", bg=BG,
                                      font=("Segoe UI", 9, "italic"))
        self._url_status.grid(row=1, column=0, columnspan=4,
                                sticky="w", pady=(4, 0))

        # ── 2. Đăng nhập ──────────────────────────────────────────────
        f2 = tk.LabelFrame(self, text="  2️⃣  Đăng nhập tài khoản LMS  ",
                            bg=BG, fg=BLUE, padx=12, pady=8,
                            font=("Segoe UI", 10, "bold"))
        f2.grid(row=2, column=0, sticky="ew", padx=10, pady=4)

        tk.Label(f2, text="Email:", bg=BG, font=("Segoe UI", 10)
                 ).grid(row=0, column=0, sticky="w", pady=2)
        self._email_var = tk.StringVar()
        ttk.Entry(f2, textvariable=self._email_var, width=40,
                  font=("Segoe UI", 10)
                  ).grid(row=0, column=1, sticky="w", padx=6, pady=2)

        tk.Label(f2, text="Mật khẩu:", bg=BG, font=("Segoe UI", 10)
                 ).grid(row=1, column=0, sticky="w", pady=2)
        self._pwd_var = tk.StringVar()
        ttk.Entry(f2, textvariable=self._pwd_var, width=40, show="•",
                  font=("Segoe UI", 10)
                  ).grid(row=1, column=1, sticky="w", padx=6, pady=2)

        btns2 = tk.Frame(f2, bg=BG)
        btns2.grid(row=2, column=0, columnspan=3, sticky="w", pady=(6, 0))
        self._login_btn = tk.Button(btns2, text="🔑 Đăng nhập",
                                      bg=GREEN, fg="white", relief="flat",
                                      cursor="hand2", padx=14, pady=4,
                                      font=("Segoe UI", 10, "bold"),
                                      command=self._do_login)
        self._login_btn.pack(side="left", padx=2)
        self._logout_btn = tk.Button(btns2, text="🚪 Đăng xuất",
                                       bg=RED, fg="white", relief="flat",
                                       cursor="hand2", padx=10, pady=4,
                                       state="disabled",
                                       command=self._do_logout)
        self._logout_btn.pack(side="left", padx=2)

        self._login_status = tk.Label(f2, text="", bg=BG, fg=BLUE,
                                        font=("Segoe UI", 9, "italic"))
        self._login_status.grid(row=3, column=0, columnspan=3,
                                  sticky="w", pady=(4, 0))

        # ── 3. Push đề ────────────────────────────────────────────────
        f3 = tk.LabelFrame(self, text="  3️⃣  Đồng bộ dữ liệu lên LMS  ",
                            bg=BG, fg=BLUE, padx=12, pady=8,
                            font=("Segoe UI", 10, "bold"))
        f3.grid(row=3, column=0, sticky="ew", padx=10, pady=4)

        self._push_exam_btn = tk.Button(
            f3, text="🚀 Push đề hiện tại lên LMS",
            bg=BLUE, fg="white", relief="flat", cursor="hand2",
            padx=14, pady=6, font=("Segoe UI", 10, "bold"),
            command=self._push_exam, state="disabled")
        self._push_exam_btn.pack(side="left", padx=2)

        self._push_nhch_btn = tk.Button(
            f3, text="📚 Đẩy NHCH cục bộ → Cloud",
            bg="#7C3AED", fg="white", relief="flat", cursor="hand2",
            padx=14, pady=6, font=("Segoe UI", 10),
            command=self._push_nhch, state="disabled")
        self._push_nhch_btn.pack(side="left", padx=2)

        self._update_btn = tk.Button(
            f3, text="⬇️ Kiểm tra cập nhật EXE",
            bg=GRAY, fg="white", relief="flat", cursor="hand2",
            padx=10, pady=6, font=("Segoe UI", 9),
            command=self._check_update)
        self._update_btn.pack(side="left", padx=2)

        # ── 4. Log ─────────────────────────────────────────────────────
        f4 = tk.LabelFrame(self, text="  📋  Log hoạt động  ",
                            bg=BG, fg=BLUE, padx=8, pady=4,
                            font=("Segoe UI", 10, "bold"))
        f4.grid(row=99, column=0, sticky="nsew", padx=10, pady=(4, 8))
        f4.rowconfigure(0, weight=1)
        f4.columnconfigure(0, weight=1)

        self._log_text = tk.Text(f4, wrap="word", font=("Consolas", 9),
                                   bg="#1E293B", fg="#E2E8F0",
                                   relief="flat", padx=8, pady=6)
        vsb = ttk.Scrollbar(f4, orient="vertical",
                              command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=vsb.set, state="disabled")
        self._log_text.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # Tag colors
        self._log_text.tag_configure("info",    foreground="#93C5FD")
        self._log_text.tag_configure("success", foreground="#86EFAC")
        self._log_text.tag_configure("error",   foreground="#FCA5A5")
        self._log_text.tag_configure("warn",    foreground="#FCD34D")

    # ──────────────────────────────────────────────────────────────────────
    #  ACTIONS
    # ──────────────────────────────────────────────────────────────────────

    def _log(self, msg: str, level: str = "info"):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_text.config(state="normal")
        self._log_text.insert("end", f"[{ts}] ", "info")
        self._log_text.insert("end", msg + "\n", level)
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    def _save_url(self):
        url = self._url_var.get().strip().rstrip("/")
        if not url:
            messagebox.showwarning("Thiếu URL",
                                    "Vui lòng nhập URL backend.", parent=self)
            return
        # Lưu vào env (current process) + ghi đè vào .env file
        os.environ["MEA_API_URL"] = url
        self._write_env_file("MEA_API_URL", url)
        self._log(f"✓ Đã lưu MEA_API_URL = {url}", "success")
        self._refresh_status()

    @staticmethod
    def _write_env_file(key: str, value: str):
        """Cập nhật key=value vào file .env ở thư mục app (giữ các dòng khác)."""
        from pathlib import Path
        env_path = Path(__file__).resolve().parent.parent / ".env"
        try:
            if env_path.exists():
                lines = env_path.read_text(encoding="utf-8").splitlines()
            else:
                lines = []
            found = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key}="):
                    lines[i] = f"{key}={value}"
                    found = True
                    break
            if not found:
                lines.append(f"{key}={value}")
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Write .env fail: %s", e)

    def _test_connection(self):
        self._url_status.config(text="⏳ Đang test...", fg=BLUE)
        def _do():
            ok = api_client.is_api_reachable()
            self.after(0, lambda: (
                self._url_status.config(
                    text=f"{'✓ Backend OK' if ok else '✘ Không kết nối được'} "
                          f"({api_client.api_url()})",
                    fg=GREEN if ok else RED),
                self._log(f"{'✓' if ok else '✘'} Test backend → "
                           f"{'OK' if ok else 'FAIL'}",
                           "success" if ok else "error")
            ))
        threading.Thread(target=_do, daemon=True).start()

    def _do_login(self):
        email = self._email_var.get().strip()
        pwd = self._pwd_var.get()
        if not email or not pwd:
            messagebox.showwarning("Thiếu thông tin",
                                    "Nhập email + mật khẩu.", parent=self)
            return
        self._login_btn.config(state="disabled")
        self._log(f"⏳ Đang đăng nhập {email}...", "info")

        def _do():
            res = api_client.login(email, pwd)
            self.after(0, lambda: self._on_login_done(res))
        threading.Thread(target=_do, daemon=True).start()

    def _on_login_done(self, res: dict):
        self._login_btn.config(state="normal")
        if res.get("ok"):
            self._log(f"✓ Đăng nhập thành công ({res.get('email')})", "success")
            # Xoá mật khẩu khỏi UI
            self._pwd_var.set("")
            self._refresh_status()
        else:
            self._log(f"✘ Đăng nhập lỗi: {res.get('error', '?')}", "error")
            messagebox.showerror("Đăng nhập thất bại",
                                  res.get("error", "Không rõ lỗi"),
                                  parent=self)

    def _do_logout(self):
        api_client.clear_token()
        self._log("✓ Đã đăng xuất", "info")
        self._refresh_status()

    def _refresh_status(self):
        """Cập nhật UI theo trạng thái api_client."""
        logged_in = api_client.is_logged_in()
        tok = api_client.load_token()
        if logged_in:
            email = tok.get("email", "(?)")
            self._login_status.config(
                text=f"✓ Đã đăng nhập: {email}", fg=GREEN)
            self._login_btn.config(state="disabled")
            self._logout_btn.config(state="normal")
            self._push_exam_btn.config(state="normal")
            self._push_nhch_btn.config(state="normal")
        else:
            self._login_status.config(text="✘ Chưa đăng nhập", fg=GRAY)
            self._login_btn.config(state="normal")
            self._logout_btn.config(state="disabled")
            self._push_exam_btn.config(state="disabled")
            self._push_nhch_btn.config(state="disabled")

    def _push_exam(self):
        if not self._get_current_exam:
            messagebox.showinfo("Chưa có đề",
                "Tab LMS cần callback get_current_exam — main_window chưa truyền.",
                parent=self); return
        exam_data = self._get_current_exam()
        if not exam_data:
            messagebox.showwarning("Chưa có đề",
                "Hãy tạo/mở 1 đề trước khi push.", parent=self); return

        # Convert ExamData → format mà /v1/desktop/sync/exam expect
        try:
            exam_payload, q_payloads = self._exam_to_payload(exam_data)
        except Exception as e:
            messagebox.showerror("Lỗi chuẩn bị payload",
                                  str(e), parent=self); return

        self._log(f"⏳ Push đề '{exam_payload.get('title')}' "
                   f"({len(q_payloads)} câu)...", "info")
        self._push_exam_btn.config(state="disabled")

        def _do():
            res = api_client.sync_exam(exam_payload, q_payloads, publish=True)
            self.after(0, lambda: self._on_push_exam_done(res))
        threading.Thread(target=_do, daemon=True).start()

    def _on_push_exam_done(self, res: dict):
        self._push_exam_btn.config(state="normal")
        if res.get("ok"):
            d = res.get("data", {})
            code = d.get("code")
            self._log(f"✓ Đề đã publish! exam_code = {code} "
                       f"({d.get('questions_added')} câu thêm, "
                       f"{d.get('nhch_upserted')} câu lên NHCH)", "success")
            messagebox.showinfo(
                "Push thành công",
                f"Mã đề: {code}\n\nHS truy cập:\n"
                f"{api_client.api_url().replace(':8000', ':3000')}/exam/{code}",
                parent=self)
        else:
            self._log(f"✘ Push lỗi: {res.get('error', '?')[:200]}", "error")
            messagebox.showerror("Push thất bại",
                                  res.get("error", "?"), parent=self)

    @staticmethod
    def _exam_to_payload(exam_data) -> tuple[dict, list[dict]]:
        """Chuyển ExamData v4 → (exam_dict, questions_list) cho API."""
        exam_dict = {
            "title":        getattr(exam_data, "title", "Đề chưa đặt tên"),
            "subject":      getattr(exam_data, "subject", "Toán"),
            "grade":        str(getattr(exam_data, "grade", "12")),
            "duration_min": int(getattr(exam_data, "duration_min", 45)),
        }
        questions = []
        for q in getattr(exam_data, "questions", []):
            options_payload = (q.options or {}) if q.qtype == "TN" else {}
            answer = q.answer or ""
            if q.qtype == "DS" and q.answers:
                answer = ",".join(f"{k}={'Đ' if v else 'S'}"
                                   for k, v in q.answers.items())
            questions.append({
                "question_id": getattr(q, "question_id", None)
                                 or f"EXE-{id(q):x}",
                "subject":     exam_dict["subject"],
                "grade":       exam_dict["grade"],
                "topic":       q.topic or "",
                "level":       q.level or "TH",
                "qtype":       q.qtype,
                "question":    q.question or "",
                "options":     options_payload,
                "answer":      answer,
                "solution":    q.solution or "",
                "points":      float(getattr(q, "points", 1.0)),
            })
        return exam_dict, questions

    def _push_nhch(self):
        if not self._get_nhch_questions:
            messagebox.showinfo("Không có nguồn NHCH",
                "main_window chưa truyền get_nhch_questions.", parent=self)
            return
        questions = self._get_nhch_questions() or []
        if not questions:
            messagebox.showwarning("NHCH cục bộ trống",
                "Chưa có câu nào để đẩy.", parent=self); return

        if not messagebox.askyesno("Xác nhận",
            f"Đẩy {len(questions)} câu NHCH cục bộ lên Cloud?",
            parent=self): return

        # Chuẩn hoá format
        payload = []
        from datetime import datetime
        seed = datetime.now().strftime("%Y%m%d%H%M%S")
        for i, q in enumerate(questions, 1):
            d = q if isinstance(q, dict) else q.__dict__
            payload.append({
                "question_id": d.get("question_id") or f"NHCH-{seed}-{i:04d}",
                "subject":     d.get("subject", "Toán"),
                "grade":       str(d.get("grade", "12")),
                "topic":       d.get("topic", ""),
                "level":       d.get("level", "TH"),
                "qtype":       d.get("qtype", "TN"),
                "question":    d.get("question", ""),
                "options":     d.get("options") or d.get("options_json") or {},
                "answer":      d.get("answer", ""),
                "solution":    d.get("solution", ""),
            })

        self._log(f"⏳ Đẩy {len(payload)} câu NHCH...", "info")
        self._push_nhch_btn.config(state="disabled")

        def _do():
            res = api_client.sync_questions(payload)
            self.after(0, lambda: self._on_push_nhch_done(res))
        threading.Thread(target=_do, daemon=True).start()

    def _on_push_nhch_done(self, res: dict):
        self._push_nhch_btn.config(state="normal")
        if res.get("ok"):
            d = res.get("data", {})
            self._log(f"✓ Đã upsert {d.get('upserted')} câu, "
                       f"bỏ qua {d.get('skipped')} trùng", "success")
        else:
            self._log(f"✘ Push NHCH lỗi: {res.get('error', '?')[:200]}", "error")

    def _check_update(self):
        self._log("⏳ Đang kiểm tra cập nhật...", "info")

        def _do():
            try:
                from services.updater import check_for_update
                info = check_for_update()
                self.after(0, lambda: self._on_update_checked(info))
            except Exception as e:
                self.after(0, lambda: self._log(f"✘ Update check lỗi: {e}",
                                                  "error"))
        threading.Thread(target=_do, daemon=True).start()

    def _on_update_checked(self, info):
        if not info:
            self._log("✓ Không có bản cập nhật mới hoặc nguồn cập nhật chưa khả dụng",
                       "success")
            return

        latest = str(info.get("version") or info.get("latest") or "?")
        current = str(info.get("current") or "")
        source = str(info.get("source") or "server")
        self._log(f"⬆ Có bản mới v{latest} từ {source}", "warn")
        try:
            from config import APP_VERSION
            from ui.dialog_update import UpdateDialog
            UpdateDialog(
                self.winfo_toplevel(),
                info,
                current_version=current or APP_VERSION,
            )
        except Exception as exc:
            self._log(f"✘ Không mở được dialog cập nhật: {exc}", "error")
