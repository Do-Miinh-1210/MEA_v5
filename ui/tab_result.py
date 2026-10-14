"""
ui/tab_result.py — Tab ③ Xem đề & Xuất file.
Toàn bộ giao diện sử dụng tiếng Việt có dấu.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Callable, Optional

from services.tikz_vector_workflow import (
    TIKZ_CONVERSION_OPTIONS,
    TIKZ_CONVERT_ACTION_LABEL,
    TIKZ_TO_EMF_ACTION_LABEL,
    TIKZ_TO_EMF_DESCRIPTION,
    TIKZ_OUTPUT_MODE_EMF,
    TIKZ_OUTPUT_MODE_PNG,
    get_tikz_conversion_option,
)
from ui.image_helper import pick_and_copy_image, load_tk_image


class TabResult(ttk.Frame):
    """Tab ③ — Xem đề & Xuất file."""

    def __init__(self, parent,
                 get_ai_call: Callable,
                 get_subject_grade: Callable):
        super().__init__(parent)
        self._get_ai         = get_ai_call
        self._get_subj_grade = get_subject_grade
        self._exam_data      = None
        self._sol_var        = tk.BooleanVar(value=True)  # Kèm lời giải mặc định bật
        self._gated_buttons: dict[str, tk.Widget] = {}  # feature-gated buttons
        try:
            from config import get_word_math_mode, is_word_auto_convert_tables_enabled
            math_mode = get_word_math_mode()
            auto_tables = is_word_auto_convert_tables_enabled()
        except Exception:
            math_mode = "text"
            auto_tables = True
        self._math_mode_var  = tk.StringVar(value=math_mode)  # YC4: text hoặc equation
        self._auto_table_var = tk.BooleanVar(value=auto_tables)
        self._tk_images: list = []  # giữ reference ảnh preview
        self._build()

    def set_exam(self, exam_data):
        self._exam_data = exam_data
        self._render_exam()

    def load_exam(self, exam_data):
        """Alias của set_exam — tương thích với main_window."""
        self.set_exam(exam_data)

    def _build(self):
        # ── [SPEED-4] Quick Action Bar: 3 nhóm rõ ràng ──────────────────
        # • HOÀN TẤT  → primary action lớn nhất (Xuất Word)
        # • TÙY CHỈNH → secondary actions (Nhiều mã đề / TikZ / Cài đặt xuất)
        # • SỬA CHỮA  → warning actions (Tạo lại lỗi / Kiểm tra CL)
        # Lý do: giảm decision fatigue, user mới nhìn 1 lần thấy ngay primary
        # action. "Tải đề từ file" đã chuyển vào menu "Phiên làm việc".
        tb = tk.Frame(self, bg="#1E293B")
        tb.pack(fill="x")
        primary_row = tk.Frame(tb, bg="#1E293B")
        primary_row.pack(fill="x")
        secondary_row = tk.Frame(tb, bg="#0F172A")
        secondary_row.pack(fill="x")
        self._toolbar_primary_row = primary_row
        self._toolbar_secondary_row = secondary_row

        # ── Group 1: HOÀN TẤT — primary button (lớn, xanh lá) ───────────
        self._btn_export_main = tk.Button(
            primary_row, text="📄 Xuất Word & mở",
            command=self._export_word,
            bg="#10B981", fg="white",
            activebackground="#059669",
            font=("Segoe UI", 11, "bold"),
            relief="flat", cursor="hand2", bd=0,
            padx=18, pady=8,
        )
        self._btn_export_main.pack(side="left", padx=(8, 4), pady=4)

        # Vertical separator
        tk.Frame(primary_row, bg="#475569", width=1).pack(
            side="left", fill="y", padx=4, pady=8)

        # ── Group 2: TÙY CHỈNH — secondary actions ──────────────────────
        for label, cmd, bg_c in [
            ("📂 Nhiều mã đề",   self._export_multi,           "#7C3AED"),
            ("🎲 Trộn đề thi",   self._switch_to_shuffle_tab,  "#0284C7"),
            ("__tikz_convert__", self._on_tikz_to_emf_click, "#F59E0B"),
            ("⚙️ Cài đặt xuất",   self._open_export_settings,   "#475569"),
        ]:
            if label == "__tikz_convert__":
                btn = tk.Menubutton(
                    primary_row, text=f"📐 {TIKZ_CONVERT_ACTION_LABEL}",
                    bg=bg_c, fg="white", activebackground=bg_c,
                    font=("Segoe UI", 9, "bold"),
                    relief="flat", cursor="hand2", bd=0,
                    padx=10, pady=5,
                    direction="below",
                )
                menu = tk.Menu(btn, tearoff=False)
                for option in TIKZ_CONVERSION_OPTIONS:
                    menu.add_command(
                        label=f"{option['label']} - {option['description']}",
                        command=lambda mode=option["mode"]: self._on_tikz_convert_click(mode),
                    )
                btn.configure(menu=menu)
            else:
                btn = tk.Button(
                    primary_row, text=label, command=cmd,
                    bg=bg_c, fg="white", activebackground=bg_c,
                    font=("Segoe UI", 9, "bold"),
                    relief="flat", cursor="hand2", bd=0,
                    padx=10, pady=5,
                )
            btn.pack(side="left", padx=2, pady=4)
            if "TikZ" in label:
                self._btn_tikz2emf = btn
            elif label == "__tikz_convert__":
                self._btn_tikz2emf = btn

        # ── Group 3: SỬA CHỮA — warning actions ─────────────────────────
        tk.Label(
            secondary_row, text="SỬA CHỮA & TÙY CHỌN",
            bg="#0F172A", fg="#CBD5E1",
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left", padx=(10, 6))
        for label, cmd, bg_c in [
            ("🔁 Tạo lại lỗi",         self._retry_failed, "#D97706"),
            ("✅ Kiểm tra chất lượng",  self._run_review,   "#0369A1"),
        ]:
            tk.Button(
                secondary_row, text=label, command=cmd,
                bg=bg_c, fg="white", activebackground=bg_c,
                font=("Segoe UI", 9, "bold"),
                relief="flat", cursor="hand2", bd=0,
                padx=10, pady=5,
            ).pack(side="left", padx=2, pady=4)

        # ── Right: ☑ Kèm lời giải (giữ nguyên hành vi cũ) ───────────────
        tk.Checkbutton(secondary_row, text="Kèm lời giải & đáp án",
                       variable=self._sol_var,
                       bg="#0F172A", fg="white",
                       selectcolor="#334155",
                       font=("Segoe UI", 9),
                       activebackground="#0F172A",
                       activeforeground="white").pack(side="right", padx=8)

        # ── Thông tin đề thi (info bar) ──────────────────────────────
        info_bar = tk.Frame(self, bg="#EFF6FF", height=28)
        info_bar.pack(fill="x")
        info_bar.pack_propagate(False)
        self._info_lbl = tk.Label(
            info_bar,
            text="Chưa có đề thi. Nhấn 'Tạo đề bằng AI' để bắt đầu.",
            bg="#EFF6FF", fg="#1D4ED8",
            font=("Segoe UI", 9), anchor="w", padx=10)
        self._info_lbl.pack(anchor="w", padx=10, pady=4)

        # ── Khung xem đề (scrollable cards) ──────────────────────────────
        view_f = tk.Frame(self)
        view_f.pack(fill="both", expand=True, padx=8, pady=8)

        self._view_canvas = tk.Canvas(view_f, bg="#F9F7F4", highlightthickness=0)
        vsb = ttk.Scrollbar(view_f, orient="vertical", command=self._view_canvas.yview)
        self._view_canvas.pack(side="left", fill="both", expand=True)
        # Scrollbar luôn hiển thị (giúp user thấy ngay là tab có thể cuộn).
        vsb.pack(side="right", fill="y")
        self._view_canvas.configure(yscrollcommand=vsb.set)

        self._cards_frame = tk.Frame(self._view_canvas, bg="#F9F7F4")
        self._cards_window = self._view_canvas.create_window(
            (0, 0), window=self._cards_frame, anchor="nw")

        # Throttled scrollregion update — gọi bbox("all") mỗi event Configure
        # rất tốn (phải duyệt mọi widget); coalesce qua after_idle.
        self._scrollregion_pending = False
        def _update_scrollregion():
            self._scrollregion_pending = False
            try:
                self._view_canvas.configure(
                    scrollregion=self._view_canvas.bbox("all"))
            except Exception:
                pass
        def _schedule_scrollregion(_e=None):
            if self._scrollregion_pending:
                return
            self._scrollregion_pending = True
            self._view_canvas.after_idle(_update_scrollregion)
        self._cards_frame.bind("<Configure>", _schedule_scrollregion)
        self._view_canvas.bind("<Configure>",
            lambda e: self._view_canvas.itemconfig(self._cards_window, width=e.width))

        # ── Smooth mouse wheel scroll ─────────────────────────────────────
        # Chỉ bind GLOBAL (bind_all) khi chuột vào canvas — tránh phải bind
        # vào hàng nghìn child widget của các card (gây khựng khi render).
        # Tích lũy delta để touchpad gửi delta nhỏ (~12 units) không bị
        # int() truncate mất → cuộn mượt cả với touchpad/mouse cao cấp.
        self._scroll_accum = 0.0
        # Coalesce nhiều event wheel liên tiếp vào 1 lần update canvas
        self._wheel_pending = False

        # Placeholder khi chưa có đề
        self._placeholder = tk.Label(
            self._cards_frame,
            text="Chưa có đề thi.\nNhấn '✨ Tạo đề bằng AI' để bắt đầu.",
            bg="#F9F7F4", fg="#9CA3AF",
            font=("Segoe UI", 12), justify="center",
        )
        self._placeholder.pack(pady=60)

        # Bind local mousewheel trên view_canvas — sự kiện còn lại được xử lý tự động bởi _setup_global_mousewheel
        self._view_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._view_canvas.bind("<Button-4>",   self._on_mousewheel)
        self._view_canvas.bind("<Button-5>",   self._on_mousewheel)

        # Danh sách card widgets
        self._q_cards: list[dict] = []

    # ── Smooth mouse wheel handlers (bind_all approach) ─────────────────────
    def _on_mousewheel(self, e):
        """Wheel handler — chuẩn hóa delta cross-platform + tích lũy."""
        # Windows: e.delta = ±120 mỗi notch (chuột), nhỏ hơn cho touchpad
        # Mac:     e.delta = ±1 mỗi notch (đã được OS chuẩn hóa)
        # Linux:   không có e.delta, dùng e.num = 4 (up) / 5 (down)
        delta = getattr(e, "delta", 0)
        if delta:
            if abs(delta) >= 30:
                # Mouse wheel: 120/30 = 4 units per notch (giữ tốc độ cũ)
                units = -delta / 30.0
            else:
                # Touchpad / Mac: nhân hệ số cao hơn
                units = -delta * 0.5
        else:
            num = getattr(e, "num", 0)
            if num == 4:
                units = -3
            elif num == 5:
                units = 3
            else:
                return

        self._scroll_accum += units
        if self._wheel_pending:
            return
        self._wheel_pending = True
        self.after_idle(self._flush_wheel_scroll)

    def _flush_wheel_scroll(self):
        """Áp dụng tích lũy delta vào canvas, chỉ gọi yview_scroll 1 lần."""
        self._wheel_pending = False
        n = int(self._scroll_accum)
        if n == 0:
            # Chưa đủ 1 unit — giữ accumulator cho lần wheel kế tiếp.
            # Nhưng nếu đã >0.5 thì làm tròn để cảm giác phản hồi tức thì.
            if self._scroll_accum >= 0.5:
                n = 1
            elif self._scroll_accum <= -0.5:
                n = -1
            else:
                return
        self._scroll_accum -= n
        try:
            self._view_canvas.yview_scroll(n, "units")
        except Exception:
            pass


    def _redirect_wheel_to_canvas(self, widget) -> None:
        """Khi wheel xảy ra trên widget có scroll riêng (Text/Listbox), forward
        sự kiện về canvas chính và return 'break' để widget không tự cuộn.
        Gọi cho tk.Text trong card — không cần đệ quy toàn bộ children."""
        def _forward(e):
            self._on_mousewheel(e)
            return "break"
        try:
            widget.bind("<MouseWheel>", _forward, add="+")
            widget.bind("<Button-4>",   _forward, add="+")
            widget.bind("<Button-5>",   _forward, add="+")
        except Exception:
            pass

    # ── Hiển thị đề (dạng card chỉnh sửa được) ──────────────────────────────
    def _render_exam(self):
        d = self._exam_data
        # Xóa cards cũ
        for w in self._cards_frame.winfo_children():
            w.destroy()
        self._q_cards.clear()
        self._tk_images.clear()

        if not d:
            self._placeholder = tk.Label(
                self._cards_frame,
                text="Chưa có đề thi.\nNhấn '✨ Tạo đề bằng AI' để bắt đầu.",
                bg="#F9F7F4", fg="#9CA3AF",
                font=("Segoe UI", 12), justify="center",
            )
            self._placeholder.pack(pady=60)
            self._info_lbl.config(text="Chưa có đề thi.")
            return

        qs = d.questions
        # Hiển thị thêm school + teacher nếu có (mới ở v4.1.0+)
        school_part = f"  |  Trường: {d.school}" if getattr(d, "school", "") else ""
        teacher_part = f"  |  GV: {d.teacher}" if getattr(d, "teacher", "") else ""
        self._info_lbl.config(
            text=f"Môn: {d.subject}  |  Lớp: {d.grade}  |  "
                 f"Năm học: {d.year}  |  Thời gian: {d.time}"
                 f"{school_part}{teacher_part}  |  "
                 f"Tổng: {len(qs)} câu"
        )

        # Màu badge theo loại
        _TYPE_COLORS = {
            "TN": ("#3B82F6", "Trắc nghiệm"),
            "DS": ("#8B5CF6", "Đúng – Sai"),
            "TLN": ("#F59E0B", "Trả lời ngắn"),
            "TL": ("#EF4444", "Tự luận"),
        }
        _LEVEL_COLORS = {
            "NB": "#22C55E", "TH": "#3B82F6",
            "VD": "#F59E0B",
        }

        # Tiêu đề đề thi — modern dark header với nút SỬA THÔNG TIN
        title_f = tk.Frame(self._cards_frame, bg="#0F2D52")
        title_f.pack(fill="x", padx=4, pady=6)

        # Title text bên trái
        title_text = (
            f"  📝  {d.exam_title or f'ĐỀ KIỂM TRA {d.subject.upper()}  —  LỚP {d.grade}'}"
            f"  |  {d.year}  |  {d.time}"
        )
        if getattr(d, "school", ""):
            title_text += f"  |  {d.school}"
        if getattr(d, "teacher", ""):
            title_text += f"  |  GV: {d.teacher}"

        tk.Label(title_f, text=title_text,
                 bg="#0F2D52", fg="white",
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(side="left", padx=10, pady=7)

        # Nút sửa thông tin đề — nổi bật góc phải header
        tk.Button(
            title_f, text="✏️ Sửa thông tin đề",
            font=("Segoe UI", 9, "bold"),
            bg="#10B981", fg="white",
            activebackground="#059669", activeforeground="white",
            relief="flat", cursor="hand2", bd=0,
            padx=10, pady=4,
            command=self._edit_exam_info,
        ).pack(side="right", padx=10, pady=4)

        # Tạo card cho từng câu
        for idx, q in enumerate(qs):
            self._create_question_card(idx, q, _TYPE_COLORS, _LEVEL_COLORS)

        # KHÔNG cần bind mousewheel cho từng child nữa — đã dùng bind_all
        # global trong _bind_mousewheel_global khi chuột vào vùng canvas.
        # Scroll lên đầu
        self._view_canvas.yview_moveto(0)

    def _make_card_image_row(self, parent, q, attr_or_key: str,
                             card_bg: str, is_dict: bool = False,
                             dict_key: str = "") -> tk.Frame:
        """Tạo hàng hiển thị/chèn ảnh trong question card.

        attr_or_key: tên attribute trên q (vd 'question_image')
        is_dict + dict_key: nếu True thì dùng getattr(q, attr_or_key).get(dict_key)
        """
        row = tk.Frame(parent, bg=card_bg)
        row.pack(fill="x", padx=12, pady=1)

        if is_dict:
            current_path = getattr(q, attr_or_key, {}).get(dict_key, "")
        else:
            current_path = getattr(q, attr_or_key, "") or ""

        preview_lbl = tk.Label(row, bg="#F0F0F0", relief="groove")

        def _refresh(path: str):
            tk_img = load_tk_image(path, max_w=320, max_h=180)
            if tk_img:
                self._tk_images.append(tk_img)
                preview_lbl.config(image=tk_img, text="")
                preview_lbl.pack(side="left", padx=4, pady=2)
            else:
                preview_lbl.pack_forget()

        def _pick():
            new_path = pick_and_copy_image(self.winfo_toplevel())
            if new_path:
                if is_dict:
                    d = getattr(q, attr_or_key, {})
                    d[dict_key] = new_path
                    setattr(q, attr_or_key, d)
                else:
                    setattr(q, attr_or_key, new_path)
                _refresh(new_path)

        def _remove():
            if is_dict:
                d = getattr(q, attr_or_key, {})
                d.pop(dict_key, None)
                setattr(q, attr_or_key, d)
            else:
                setattr(q, attr_or_key, "")
            preview_lbl.pack_forget()

        tk.Button(row, text="🖼 Ảnh", font=("Segoe UI", 7),
                  bg="#E0E7FF", fg="#3730A3", relief="flat", cursor="hand2",
                  padx=4, pady=1, command=_pick).pack(side="left", padx=2)
        tk.Button(row, text="✕", font=("Segoe UI", 7),
                  bg="#FEE2E2", fg="#991B1B", relief="flat", cursor="hand2",
                  padx=3, pady=1, command=_remove).pack(side="left")

        if current_path:
            _refresh(current_path)

        return row

    # ── DIALOG: Sửa thông tin đề (sau khi đã tạo) ────────────────────────────
    def _edit_exam_info(self) -> None:
        """Mở dialog cho phép edit metadata đề: subject, grade, semester,
        year, time, school, teacher, exam_title. Sau khi save → re-render
        để header cập nhật + sync với Word/PDF khi xuất.
        """
        if not self._exam_data:
            messagebox.showinfo(
                "Chưa có đề",
                "Hãy tạo đề trước khi sửa thông tin.",
                parent=self,
            )
            return

        d = self._exam_data
        dlg = tk.Toplevel(self)
        dlg.title("Sửa thông tin đề")
        dlg.configure(bg="#F9F7F4")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.resizable(False, False)
        try:
            from ui import set_dialog_icon
            set_dialog_icon(dlg)
        except Exception:
            pass

        # Header
        hdr = tk.Frame(dlg, bg="#0F2D52")
        hdr.pack(fill="x")
        tk.Label(hdr, text="  ✏️ Sửa thông tin đề kiểm tra",
                 font=("Segoe UI", 12, "bold"),
                 bg="#0F2D52", fg="white").pack(side="left", padx=12, pady=8)

        body = tk.Frame(dlg, bg="#F9F7F4")
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.grid_columnconfigure(1, weight=1, minsize=250)
        body.grid_columnconfigure(3, weight=1, minsize=110)

        # Vars
        title_var    = tk.StringVar(value=d.exam_title)
        subject_var  = tk.StringVar(value=d.subject)
        grade_var    = tk.StringVar(value=str(d.grade))
        semester_var = tk.StringVar(value=d.semester)
        year_var     = tk.StringVar(value=d.year)
        time_var     = tk.StringVar(value=d.time)
        school_var   = tk.StringVar(value=getattr(d, "school", ""))
        teacher_var  = tk.StringVar(value=getattr(d, "teacher", ""))

        # Grid layout: label | entry, 2 cột × N hàng
        def _row(parent, label: str, var: tk.StringVar, row_idx: int,
                 col: int = 0, width: int = 22, values: list | None = None):
            tk.Label(parent, text=label, font=("Segoe UI", 9, "bold"),
                     bg="#F9F7F4", fg="#334155", anchor="e"
                     ).grid(row=row_idx, column=col*2, sticky="e", padx=(0, 6), pady=4)
            if values:
                w = ttk.Combobox(parent, textvariable=var, values=values,
                                  width=width-2, state="normal")
            else:
                w = tk.Entry(parent, textvariable=var, font=("Segoe UI", 10),
                              width=width, bd=1, relief="solid")
            w.grid(row=row_idx, column=col*2+1, sticky="we", padx=(0, 12), pady=4)
            return w

        # Tiêu đề đề (full width)
        tk.Label(body, text="Tiêu đề đề:", font=("Segoe UI", 9, "bold"),
                 bg="#F9F7F4", fg="#334155", anchor="e"
                 ).grid(row=0, column=0, sticky="e", padx=(0, 6), pady=4)
        tk.Entry(body, textvariable=title_var, font=("Segoe UI", 10),
                 width=58, bd=1, relief="solid"
                 ).grid(row=0, column=1, columnspan=3, sticky="we", padx=(0, 12), pady=4)

        # Hàng 2: Môn + Lớp
        _row(body, "Môn:", subject_var, 1, col=0)
        _row(body, "Lớp:", grade_var, 1, col=1, width=10,
             values=[str(i) for i in range(1, 13)])

        # Hàng 3: Kỳ + Năm
        _row(body, "Kỳ:", semester_var, 2, col=0,
             values=["Giữa kì I", "Cuối kì I", "Giữa kì II", "Cuối kì II"])
        _row(body, "Năm:", year_var, 2, col=1, width=12)

        # Hàng 4: Thời gian + (placeholder)
        _row(body, "Thời gian:", time_var, 3, col=0,
             values=["15 phút", "30 phút", "45 phút", "60 phút", "90 phút", "120 phút"])

        # Hàng 5: Trường (full width)
        tk.Label(body, text="Tên trường:", font=("Segoe UI", 9, "bold"),
                 bg="#F9F7F4", fg="#334155", anchor="e"
                 ).grid(row=4, column=0, sticky="e", padx=(0, 6), pady=4)
        tk.Entry(body, textvariable=school_var, font=("Segoe UI", 10),
                 width=58, bd=1, relief="solid"
                 ).grid(row=4, column=1, columnspan=3, sticky="we", padx=(0, 12), pady=4)

        # Hàng 6: GV (full width)
        tk.Label(body, text="GV ra đề:", font=("Segoe UI", 9, "bold"),
                 bg="#F9F7F4", fg="#334155", anchor="e"
                 ).grid(row=5, column=0, sticky="e", padx=(0, 6), pady=4)
        tk.Entry(body, textvariable=teacher_var, font=("Segoe UI", 10),
                 width=58, bd=1, relief="solid"
                 ).grid(row=5, column=1, columnspan=3, sticky="we", padx=(0, 12), pady=4)

        # Buttons
        btn_f = tk.Frame(dlg, bg="#F9F7F4")
        btn_f.pack(fill="x", padx=16, pady=(4, 12))

        def _save():
            d.exam_title = title_var.get().strip() or d.exam_title
            d.subject    = subject_var.get().strip() or d.subject
            d.grade      = grade_var.get().strip() or d.grade
            d.semester   = semester_var.get().strip() or d.semester
            d.year       = year_var.get().strip() or d.year
            d.time       = time_var.get().strip() or d.time
            d.school     = school_var.get().strip()
            d.teacher    = teacher_var.get().strip()
            dlg.destroy()
            # Re-render header với info mới
            self._render_exam()

        tk.Button(btn_f, text="  💾 Lưu  ",
                  font=("Segoe UI", 10, "bold"),
                  bg="#10B981", fg="white",
                  activebackground="#059669", activeforeground="white",
                  relief="flat", cursor="hand2", padx=16, pady=5,
                  command=_save).pack(side="right", padx=4)
        tk.Button(btn_f, text="  Hủy  ",
                  font=("Segoe UI", 10),
                  bg="#94A3B8", fg="white",
                  activebackground="#64748B", activeforeground="white",
                  relief="flat", cursor="hand2", padx=16, pady=5,
                  command=dlg.destroy).pack(side="right", padx=4)

        # Sizing
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        dlg.update_idletasks()
        max_w = max(520, sw - 40)
        w = min(max(760, dlg.winfo_reqwidth() + 24), max_w)
        h = dlg.winfo_reqheight() + 20
        dlg.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        dlg.lift()
        dlg.focus_force()

    def _create_question_card(self, idx: int, q, type_colors: dict, level_colors: dict):
        """Tạo 1 card câu hỏi chỉnh sửa được."""
        is_error = q._error
        border_color = "#EF4444" if is_error else "#CBD5E1"
        card_bg = "#FEF2F2" if is_error else "#FFFFFF"

        # Outer border frame
        border = tk.Frame(self._cards_frame, bg=border_color)
        border.pack(fill="x", padx=4, pady=3)

        card = tk.Frame(border, bg=card_bg)
        card.pack(fill="x", padx=2, pady=2)

        # ── Header row ──
        hdr_bg = "#334155" if is_error else "#1E293B"
        hdr = tk.Frame(card, bg=hdr_bg)
        hdr.pack(fill="x")

        # Question number badge
        tk.Label(hdr, text=f" Câu {idx + 1} ",
                 bg="#0284C7", fg="white",
                 font=("Segoe UI", 10, "bold"),
                 padx=8, pady=4).pack(side="left", padx=4, pady=4)

        # Type badge
        tc, tname = type_colors.get(q.qtype, ("#6B7280", q.qtype))
        tk.Label(hdr, text=f" {tname} ",
                 bg=tc, fg="white",
                 font=("Segoe UI", 8, "bold"),
                 padx=6, pady=3).pack(side="left", padx=2, pady=4)

        # Level badge — chỉ hiện khi có mức độ
        if q.level:
            lc = level_colors.get(q.level, "#6B7280")
            tk.Label(hdr, text=f" {q.level} ",
                     bg=lc, fg="white",
                     font=("Segoe UI", 8, "bold"),
                     padx=6, pady=3).pack(side="left", padx=2, pady=4)

        # Quality score badge
        if q._review and "quality_score" in q._review:
            sc = q._review["quality_score"]
            if isinstance(sc, dict): sc = sc.get("final_score")
            if sc is not None:
                sc_color = "#10B981" if sc >= 0.9 else ("#F59E0B" if sc >= 0.8 else "#EF4444")
                tk.Label(hdr, text=f" ★ {float(sc):.2f} ",
                         bg=sc_color, fg="white",
                         font=("Segoe UI", 8, "bold"),
                         padx=5, pady=3).pack(side="left", padx=2, pady=4)

        # Error badge
        if is_error:
            tk.Label(hdr, text=f" ❌ {q._error_msg or 'Lỗi'} ",
                     bg="#EF4444", fg="white",
                     font=("Segoe UI", 8, "bold")).pack(side="left", padx=6, pady=4)

        # Topic (right side)
        tk.Label(hdr, text=f" {q.topic} ",
                 bg=hdr_bg, fg="#94A3B8",
                 font=("Segoe UI", 8, "italic")).pack(side="right", padx=6, pady=4)

        # Action buttons (right side)
        btn_cfg = [
            ("👁 LaTeX",   "#7C3AED", self._preview_latex),
            ("🔄 Tạo lại", "#3B82F6", self._regenerate_question),
            ("⬆",         "#10B981", lambda i=idx: self._move_question(i, -1)),
            ("⬇",         "#10B981", lambda i=idx: self._move_question(i,  1)),
            ("✕",         "#EF4444", None),
        ]
        for txt, bg_c, cmd in reversed(btn_cfg):
            if cmd:
                btn = tk.Label(hdr, text=f" {txt} ", bg=bg_c, fg="white",
                             font=("Segoe UI", 8, "bold"), cursor="hand2", padx=5, pady=3)
            else:
                btn = tk.Label(hdr, text=f" {txt} ", bg=bg_c, fg="white",
                             font=("Segoe UI", 9, "bold"), cursor="hand2", padx=5, pady=3)
            btn.pack(side="right", padx=2, pady=4)
            if txt == "✕":
                btn.bind("<Button-1>", lambda e, i=idx, bf=border: self._delete_question(i, bf))
                btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#DC2626"))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#EF4444"))
            elif txt == "⬆":
                btn.bind("<Button-1>", lambda e, i=idx: self._move_question(i, -1))
                btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#059669"))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#10B981"))
            elif txt == "⬇":
                btn.bind("<Button-1>", lambda e, i=idx: self._move_question(i, 1))
                btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#059669"))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#10B981"))
            elif txt == "🔄 Tạo lại":
                btn.bind("<Button-1>", lambda e, i=idx: self._regenerate_question(i))
                btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#2563EB"))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#3B82F6"))
            elif txt == "👁 LaTeX":
                btn.bind("<Button-1>", lambda e, i=idx: self._preview_latex(i))
                btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#6D28D9"))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#7C3AED"))

        # ── Nội dung câu hỏi (editable) ──
        body = tk.Frame(card, bg=card_bg)
        body.pack(fill="x", padx=8, pady=2)

        q_text = tk.Text(body, font=("Segoe UI", 10), wrap="word",
                         bg=card_bg, relief="flat", borderwidth=0,
                         height=max(2, min(6, q.question.count('\n') + 2)))
        q_text.insert("1.0", q.question)
        q_text.pack(fill="x")
        # Forward wheel events lên canvas chính để cuộn mượt
        self._redirect_wheel_to_canvas(q_text)

        # Ảnh câu hỏi
        self._make_card_image_row(card, q, "question_image", card_bg)

        card_data = {"q": q, "q_text": q_text}

        # ── Phương án / Items / Đáp án (theo loại câu) ──
        if q.qtype == "TN" and not is_error:
            opts_f = tk.Frame(card, bg=card_bg)
            opts_f.pack(fill="x", padx=12, pady=4)
            opt_vars = {}
            opts = q.options if isinstance(q.options, dict) else {}
            answer_var = tk.StringVar(value=q.answer)
            for label in "ABCD":
                opt_text = opts.get(label, "")
                row = tk.Frame(opts_f, bg=card_bg)
                row.pack(fill="x", pady=1)
                is_ans = (q.answer == label)
                # Radio để chọn đáp án đúng
                rb = ttk.Radiobutton(row, variable=answer_var, value=label)
                rb.pack(side="left")
                tk.Label(row, text=f"{label}.", bg=card_bg,
                         fg="#22C55E" if is_ans else "#374151",
                         font=("Segoe UI", 10, "bold" if is_ans else "normal"),
                         width=2).pack(side="left")
                ov = tk.StringVar(value=opt_text)
                oe = ttk.Entry(row, textvariable=ov, font=("Segoe UI", 10))
                oe.pack(side="left", fill="x", expand=True, padx=4)
                opt_vars[label] = ov
                # Ảnh đáp án
                self._make_card_image_row(opts_f, q, "option_images", card_bg,
                                          is_dict=True, dict_key=label)
            card_data["opt_vars"] = opt_vars
            card_data["answer_var"] = answer_var

        elif q.qtype == "DS" and not is_error:
            ds_f = tk.Frame(card, bg=card_bg)
            ds_f.pack(fill="x", padx=12, pady=4)
            items_dict = q.items if isinstance(q.items, dict) else {}
            answers_dict = q.answers if isinstance(q.answers, dict) else {}
            item_sols = q.item_solutions if isinstance(getattr(q, 'item_solutions', None), dict) else {}
            ds_vars = {}
            ds_ans_vars = {}
            ds_sol_vars = {}

            for k in sorted(items_dict.keys()):
                v = items_dict[k]
                row = tk.Frame(ds_f, bg=card_bg)
                row.pack(fill="x", pady=2)

                # Toggle Đúng|Sai
                ans_v = tk.BooleanVar(value=bool(answers_dict.get(k, False)))
                toggle_btn = tk.Label(row, text="Đúng" if ans_v.get() else " Sai ",
                                       bg="#10B981" if ans_v.get() else "#EF4444",
                                       fg="white",
                                       font=("Segoe UI", 8, "bold"),
                                       width=5, relief="flat", cursor="hand2",
                                       padx=4, pady=1)
                toggle_btn.pack(side="left", padx=4)

                def _toggle_ds(e, var=ans_v, btn=toggle_btn):
                    var.set(not var.get())
                    if var.get():
                        btn.config(text="Đúng", bg="#10B981")
                    else:
                        btn.config(text=" Sai ", bg="#EF4444")
                toggle_btn.bind("<Button-1>", _toggle_ds)

                tk.Label(row, text=f"({k})", bg=card_bg,
                         font=("Segoe UI", 9, "bold"), width=3).pack(side="left")
                iv = tk.StringVar(value=v)
                ie = ttk.Entry(row, textvariable=iv, font=("Segoe UI", 10))
                ie.pack(side="left", fill="x", expand=True, padx=4)
                ds_vars[k] = iv
                ds_ans_vars[k] = ans_v
                # Ảnh ý DS
                self._make_card_image_row(ds_f, q, "item_images", card_bg,
                                          is_dict=True, dict_key=k)

            # ── Lời giải từng ý a/b/c/d ──
            sol_section = tk.Frame(card, bg=card_bg)
            sol_section.pack(fill="x", padx=12, pady=4)
            sol_visible = tk.BooleanVar(value=False)
            sol_content = tk.Frame(sol_section, bg="#F0FDF4", bd=1, relief="solid")

            for k in sorted(items_dict.keys()):
                sol_row = tk.Frame(sol_content, bg="#F0FDF4")
                sol_row.pack(fill="x", padx=8, pady=2)
                is_true = bool(answers_dict.get(k, False))
                verdict = "Đúng" if is_true else "Sai"
                v_color = "#16A34A" if is_true else "#DC2626"
                tk.Label(sol_row, text=f"({k}) {verdict}.",
                         bg="#F0FDF4", fg=v_color,
                         font=("Segoe UI", 9, "bold")).pack(side="left")
                sol_text_val = item_sols.get(k, "")
                sv = tk.StringVar(value=sol_text_val)
                se = ttk.Entry(sol_row, textvariable=sv, font=("Segoe UI", 9))
                se.pack(side="left", fill="x", expand=True, padx=4)
                ds_sol_vars[k] = sv

            def _toggle_sol_ds(sv=sol_visible, sc=sol_content, sb=None):
                if sv.get():
                    sc.pack(fill="x", pady=0)
                else:
                    sc.pack_forget()

            sol_btn = tk.Label(sol_section, text="▶ Xem lời giải", bg=card_bg,
                               fg="#16A34A", font=("Segoe UI", 9, "bold"),
                               cursor="hand2")
            sol_btn.pack(anchor="w")
            sol_btn.bind("<Button-1>", lambda e, sv=sol_visible, sb=sol_btn:
                         (sv.set(not sv.get()),
                          sb.config(text="▼ Ẩn lời giải" if sv.get() else "▶ Xem lời giải"),
                          _toggle_sol_ds()))

            card_data["ds_vars"] = ds_vars
            card_data["ds_ans_vars"] = ds_ans_vars
            card_data["ds_sol_vars"] = ds_sol_vars

        elif q.qtype in ("TLN", "TL") and not is_error:
            ans_f = tk.Frame(card, bg=card_bg)
            ans_f.pack(fill="x", padx=12, pady=4)
            tk.Label(ans_f, text="Đáp án:", bg=card_bg,
                     fg="#22C55E", font=("Segoe UI", 9, "bold")).pack(side="left")
            ans_var = tk.StringVar(value=q.answer or "")
            ans_e = ttk.Entry(ans_f, textvariable=ans_var, font=("Segoe UI", 10))
            ans_e.pack(side="left", fill="x", expand=True, padx=4)
            card_data["answer_var"] = ans_var

        # ── Lời giải (thu gọn) — chỉ cho TN/TLN/TL, DS đã có section riêng ──
        if q.solution and not is_error and q.qtype != "DS":
            sol_f = tk.Frame(card, bg=card_bg)
            sol_f.pack(fill="x", padx=8, pady=4)
            sol_visible = tk.BooleanVar(value=False)
            sol_lines = max(3, q.solution.count('\n') + 2, len(q.solution) // 80 + 2)
            sol_text = tk.Text(sol_f, font=("Segoe UI", 9), wrap="word",
                               bg="#F0FDF4", fg="#166534", relief="flat",
                               height=min(12, sol_lines))
            sol_text.insert("1.0", q.solution)
            # Forward wheel events lên canvas chính
            self._redirect_wheel_to_canvas(sol_text)

            def toggle_sol(sv=sol_visible, st=sol_text):
                if sv.get():
                    st.pack(fill="x", pady=0)
                else:
                    st.pack_forget()

            sol_btn = tk.Label(sol_f, text="▶ Xem lời giải", bg=card_bg,
                               fg="#16A34A", font=("Segoe UI", 8, "bold"),
                               cursor="hand2")
            sol_btn.pack(anchor="w")
            sol_btn.bind("<Button-1>", lambda e, sv=sol_visible, sb=sol_btn:
                         (sv.set(not sv.get()),
                          sb.config(text="▼ Ẩn lời giải" if sv.get() else "▶ Xem lời giải"),
                          toggle_sol()))
            card_data["sol_text"] = sol_text
            # Ảnh lời giải
            self._make_card_image_row(sol_f, q, "solution_image", card_bg)

        self._q_cards.append(card_data)
        # [FRICTION-2] Bind auto-save on blur cho mỗi widget editable
        self._bind_inplace_autosave(card_data)

    def _bind_inplace_autosave(self, card_data: dict) -> None:
        """[FRICTION-2] Auto-sync 1 card vào exam_data khi user blur khỏi field.

        Bind <FocusOut> cho mọi Text/Entry editable trong card. Khi user
        click ra ngoài hoặc Tab/Shift+Tab → sync ngay → KHÔNG mất edits.
        """
        def _save_one(_e=None):
            try:
                self._sync_one_card(card_data)
            except Exception as ex:
                _log.debug("inline autosave failed: %s", ex)

        # Question text
        if "q_text" in card_data:
            card_data["q_text"].bind("<FocusOut>", _save_one, add="+")

        # Solution text
        if "sol_text" in card_data:
            card_data["sol_text"].bind("<FocusOut>", _save_one, add="+")

        # TN options + answer
        if "opt_vars" in card_data:
            for var in card_data["opt_vars"].values():
                var.trace_add("write", lambda *_, cb=_save_one: cb())
        if "answer_var" in card_data:
            card_data["answer_var"].trace_add(
                "write", lambda *_, cb=_save_one: cb())

        # DS items / answers / solutions
        for key in ("ds_vars", "ds_ans_vars", "ds_sol_vars"):
            if key in card_data:
                for var in card_data[key].values():
                    var.trace_add("write", lambda *_, cb=_save_one: cb())

    def _sync_one_card(self, card: dict) -> None:
        """[FRICTION-2] Sync chỉ 1 card vào exam_data.questions[i]."""
        if not self._exam_data:
            return
        q = card.get("q")
        if q is None:
            return

        # Tương tự _sync_cards_to_data nhưng cho 1 q
        if "q_text" in card:
            new_text = card["q_text"].get("1.0", "end-1c").strip()
            if new_text != q.question:
                q.question = new_text

        if q.qtype == "TN" and "opt_vars" in card:
            for label, var in card["opt_vars"].items():
                q.options[label] = var.get()
            if "answer_var" in card:
                q.answer = card["answer_var"].get()

        elif q.qtype == "DS" and "ds_vars" in card:
            for k, var in card["ds_vars"].items():
                q.items[k] = var.get()
            for k, var in card.get("ds_ans_vars", {}).items():
                q.answers[k] = var.get()
            if "ds_sol_vars" in card:
                if not hasattr(q, "item_solutions") or not isinstance(
                    q.item_solutions, dict
                ):
                    q.item_solutions = {}
                for k, var in card["ds_sol_vars"].items():
                    q.item_solutions[k] = var.get()

        elif q.qtype in ("TLN", "TL") and "answer_var" in card:
            q.answer = card["answer_var"].get()

        if "sol_text" in card:
            q.solution = card["sol_text"].get("1.0", "end-1c").strip()

    # ── Xem trước LaTeX ────────────────────────────────────────────────────
    def _preview_latex(self, idx: int):
        """Render và hiển thị preview LaTeX cho câu hỏi."""
        if not self._exam_data or idx >= len(self._exam_data.questions):
            return
        self._sync_cards_to_data()
        q = self._exam_data.questions[idx]
        _LaTeXPreviewDialog(self.winfo_toplevel(), q, idx)

    # ── Tạo lại câu hỏi bằng AI ────────────────────────────────────────────
    def _regenerate_question(self, idx: int):
        """Tạo lại 1 câu hỏi bằng AI."""
        if not self._exam_data or idx >= len(self._exam_data.questions):
            return
        q = self._exam_data.questions[idx]
        row_dict = getattr(q, '_row_snapshot', None)
        if not row_dict:
            messagebox.showwarning(
                "Không thể tạo lại",
                f"Câu {idx+1} không có thông tin ma trận gốc.\n"
                "Chỉ có thể tạo lại câu được sinh từ AI.",
                parent=self,
            )
            return

        if not messagebox.askyesno(
            "Tạo lại câu hỏi",
            f"Tạo lại Câu {idx+1} bằng AI?\n"
            f"Chủ đề: {q.topic}\nLoại: {q.qtype} | Mức: {q.level}",
            parent=self,
        ):
            return

        # Sync trước khi tạo lại
        self._sync_cards_to_data()

        from core.models import MatrixRow
        try:
            row = MatrixRow.from_dict(row_dict)
        except Exception:
            messagebox.showerror("Lỗi", "Không thể khôi phục thông tin ma trận.", parent=self)
            return

        ai_call = self._get_ai()
        if not ai_call:
            messagebox.showwarning("Chưa cấu hình AI",
                                    "Hãy chọn nhà cung cấp AI và nhập API key trước.",
                                    parent=self)
            return

        subject, grade = self._get_subj_grade()

        # Chạy trong thread
        import threading
        def _do_regen():
            try:
                from core.generator import generate_one
                new_q = generate_one(row, subject, grade, ai_call)
                self.after(0, lambda: self._on_regen_done(idx, new_q))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Lỗi tạo lại", str(e), parent=self))

        threading.Thread(target=_do_regen, daemon=True).start()
        messagebox.showinfo("Đang tạo lại",
                             f"Đang tạo lại Câu {idx+1} bằng AI...\n"
                             "Vui lòng chờ trong giây lát.",
                             parent=self)

    def _on_regen_done(self, idx: int, new_q):
        """Callback khi tạo lại câu hỏi xong."""
        if not self._exam_data or idx >= len(self._exam_data.questions):
            return
        # Gán ID có cấu trúc cho câu mới
        try:
            from core.models import assign_structured_ids
            subject, grade = self._get_subj_grade()
            assign_structured_ids([new_q], grade)
        except Exception:
            pass
        self._exam_data.questions[idx] = new_q
        self._render_exam()
        if new_q._error:
            messagebox.showerror("Lỗi tạo lại",
                                  f"Câu {idx+1} bị lỗi: {new_q._error_msg}",
                                  parent=self)
        else:
            messagebox.showinfo("Tạo lại thành công",
                                 f"Đã tạo lại Câu {idx+1} thành công!",
                                 parent=self)

    # ── Xóa câu hỏi ─────────────────────────────────────────────────────────
    def _delete_question(self, idx: int, border_frame: tk.Frame):
        """Xóa câu hỏi khỏi đề và UI."""
        if not self._exam_data:
            return
        q = self._exam_data.questions[idx] if idx < len(self._exam_data.questions) else None
        topic = q.topic[:30] if q else ""
        if not messagebox.askyesno(
            "Xóa câu hỏi",
            f"Bạn có chắc muốn xóa Câu {idx + 1}?\n{topic}",
            parent=self,
        ):
            return
        # Sync trước khi xóa để không mất chỉnh sửa ở các câu khác
        self._sync_cards_to_data()
        # Xóa khỏi data
        self._exam_data.questions.pop(idx)
        # Re-render toàn bộ
        self._render_exam()

    # ── Sắp xếp câu hỏi (lên/xuống) ──────────────────────────────────────
    def _move_question(self, idx: int, direction: int):
        """Di chuyển câu hỏi lên (direction=-1) hoặc xuống (direction=1) trong danh sách."""
        if not self._exam_data:
            return
        qs = self._exam_data.questions
        n = len(qs)
        if n <= 1:
            return

        new_idx = idx + direction
        if new_idx < 0 or new_idx >= n:
            return  # Không thể di chuyển

        # Sync trước để không mất chỉnh sửa
        self._sync_cards_to_data()

        # Hoán đổi vị trí
        qs[idx], qs[new_idx] = qs[new_idx], qs[idx]

        # Re-render
        self._render_exam()
        messagebox.showinfo(
            "Sắp xếp",
            f"Đã di chuyển Câu {idx + 1} → Câu {new_idx + 1}",
            parent=self,
        )

    # ── Sync edits từ cards về exam_data ─────────────────────────────────────
    def _sync_cards_to_data(self):
        """Đọc nội dung từ các card UI và cập nhật lại exam_data.questions."""
        if not self._exam_data:
            return
        for card in self._q_cards:
            q = card["q"]
            # Nội dung câu hỏi
            q.question = card["q_text"].get("1.0", "end-1c").strip()
            # Phương án TN
            if q.qtype == "TN" and "opt_vars" in card:
                for label, var in card["opt_vars"].items():
                    q.options[label] = var.get()
                q.answer = card.get("answer_var", tk.StringVar()).get()
            # DS
            elif q.qtype == "DS" and "ds_vars" in card:
                for k, var in card["ds_vars"].items():
                    q.items[k] = var.get()
                for k, var in card["ds_ans_vars"].items():
                    q.answers[k] = var.get()
                # Sync lời giải từng ý
                if "ds_sol_vars" in card:
                    if not hasattr(q, 'item_solutions') or not isinstance(q.item_solutions, dict):
                        q.item_solutions = {}
                    for k, var in card["ds_sol_vars"].items():
                        q.item_solutions[k] = var.get()
            # TLN / TL
            elif q.qtype in ("TLN", "TL") and "answer_var" in card:
                q.answer = card["answer_var"].get()
            # Lời giải
            if "sol_text" in card:
                q.solution = card["sol_text"].get("1.0", "end-1c").strip()

    # ── Xuất file ─────────────────────────────────────────────────────────────
    def _get_save_dir(self) -> str:
        """Trả về thư mục lưu mặc định (từ settings hoặc Desktop)."""
        from config import EXPORT_DIR
        saved = getattr(self, "_save_dir", None)
        if saved and Path(saved).exists():
            return saved
        return str(EXPORT_DIR)

    def _choose_save_dir(self) -> None:
        """Dialog chọn thư mục lưu mặc định."""
        d = filedialog.askdirectory(
            title="Chọn thư mục lưu mặc định",
            initialdir=self._get_save_dir(),
        )
        if d:
            self._save_dir = d
            messagebox.showinfo("Đã chọn", f"Thư mục lưu mặc định:\n{d}")

    def _smart_save_path(self, suffix: str, ext: str) -> str:
        """Sinh đường dẫn mặc định từ thông tin đề."""
        d = self._exam_data
        name = f"{suffix}"
        if d:
            subj  = (d.subject or "De").replace(" ", "_")
            grade = d.grade or ""
            name  = f"{suffix}_{subj}{grade}"
        return str(Path(self._get_save_dir()) / f"{name}{ext}")

    # ── TikZ conversion ───────────────────────────────────────────────
    def _on_tikz_convert_click(self, mode: str = TIKZ_OUTPUT_MODE_EMF) -> None:
        """Quét toàn bộ đề, tạo ảnh TikZ theo lựa chọn trong menu."""
        option = get_tikz_conversion_option(mode)
        label = option["label"]
        if not self._exam_data or not getattr(self._exam_data, "questions", None):
            messagebox.showinfo(
                "Chưa có đề",
                f"Hãy tạo đề trước khi chuyển {label}.",
                parent=self,
            )
            return

        self._sync_cards_to_data()

        from services.tikz_vector_workflow import (
            convert_exam_tikz_to_emf,
            convert_exam_tikz_to_png,
            count_pending_blocks,
        )

        converter = (
            convert_exam_tikz_to_png
            if mode == TIKZ_OUTPUT_MODE_PNG
            else convert_exam_tikz_to_emf
        )
        total = count_pending_blocks(self._exam_data)
        if total == 0:
            messagebox.showinfo(
                "Không có TikZ",
                f"Đề hiện tại không có khối TikZ nào cần chuyển bằng {label}.",
                parent=self,
            )
            return

        dlg = tk.Toplevel(self)
        dlg.title(f"Chuyển {label}")
        dlg.configure(bg="#FFFBEB")
        dlg.geometry("480x200")
        dlg.resizable(False, False)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        tk.Label(
            dlg,
            text=f"📐  Đang chuyển {total} khối TikZ bằng {label}...",
            bg="#FFFBEB",
            fg="#92400E",
            font=("Segoe UI", 11, "bold"),
        ).pack(pady=(18, 6))

        pb = ttk.Progressbar(
            dlg, orient="horizontal", mode="determinate", length=420, maximum=total
        )
        pb.pack(padx=20, pady=4)

        status_var = tk.StringVar(value="0 / {} (0 lỗi)".format(total))
        tk.Label(
            dlg,
            textvariable=status_var,
            bg="#FFFBEB",
            fg="#334155",
            font=("Segoe UI", 9),
        ).pack(pady=(2, 6))

        hint_var = tk.StringVar(
            value=option["description"]
            + " Lần đầu cần LaTeX nên có thể tốn vài giây/khối."
        )
        tk.Label(
            dlg,
            textvariable=hint_var,
            bg="#FFFBEB",
            fg="#64748B",
            font=("Segoe UI", 8, "italic"),
            wraplength=440,
            justify="left",
        ).pack(pady=(2, 6))

        import threading, queue as _queue

        cancel_evt = threading.Event()
        btn_row = tk.Frame(dlg, bg="#FFFBEB")
        btn_row.pack(pady=(2, 10))
        cancel_btn = tk.Button(
            btn_row,
            text="Hủy",
            bg="#E5E7EB",
            fg="#111827",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=4,
            command=lambda: (cancel_evt.set(), cancel_btn.config(state="disabled")),
        )
        cancel_btn.pack()

        self._btn_tikz2emf.config(state="disabled", text="⏳ Đang chuyển...")
        q_evt: _queue.Queue = _queue.Queue()

        def _worker():
            try:
                def _cb(done, total_n, errs):
                    q_evt.put(("progress", done, total_n, errs))

                report = converter(
                    self._exam_data,
                    dpi=300,
                    progress_cb=_cb,
                    cancel_event=cancel_evt,
                )
                q_evt.put(("done", report))
            except Exception as e:
                q_evt.put(("fatal", str(e)[:500]))

        threading.Thread(target=_worker, daemon=True).start()

        def _drain():
            try:
                while True:
                    ev = q_evt.get_nowait()
                    kind = ev[0]
                    if kind == "progress":
                        _, done, total_n, errs = ev
                        pb["value"] = done
                        status_var.set(f"{done} / {total_n} ({errs} lỗi)")
                    elif kind == "done":
                        report = ev[1]
                        dlg.grab_release()
                        dlg.destroy()
                        self._btn_tikz2emf.config(
                            state="normal",
                            text=f"📐 {TIKZ_CONVERT_ACTION_LABEL}",
                        )
                        self._render_exam()
                        self._show_tikz_conversion_report(report, mode)
                        return
                    elif kind == "fatal":
                        dlg.grab_release()
                        dlg.destroy()
                        self._btn_tikz2emf.config(
                            state="normal",
                            text=f"📐 {TIKZ_CONVERT_ACTION_LABEL}",
                        )
                        messagebox.showerror(
                            "Lỗi hệ thống",
                            f"TikZ pipeline thất bại:\n{ev[1]}",
                            parent=self,
                        )
                        return
            except _queue.Empty:
                pass
            self.after(120, _drain)

        self.after(120, _drain)

    def _on_tikz_to_png_click(self) -> None:
        self._on_tikz_convert_click(TIKZ_OUTPUT_MODE_PNG)

    def _show_tikz_conversion_report(self, report, mode: str) -> None:
        if mode == TIKZ_OUTPUT_MODE_EMF:
            self._show_tikz_emf_report(report)
            return
        label = get_tikz_conversion_option(mode)["label"]
        if report.failed == 0:
            messagebox.showinfo(
                f"Hoàn tất {label}",
                f"{report.summary()}\n\n"
                "PNG đã được gán vào đề để xem trong app và xuất Word nhanh.",
                parent=self,
            )
            return
        failed = [
            f"Câu {result.q_index + 1}: {result.error}"
            for result in report.results
            if result.error
        ]
        messagebox.showwarning(
            f"Báo cáo {label}",
            report.summary() + "\n\n" + "\n".join(failed)[:900],
            parent=self,
        )

    def _on_tikz_to_emf_click(self) -> None:
        """Quét toàn bộ đề, tạo EMF vector kèm PNG preview trong slot ảnh.

        Chạy trong thread riêng để không đóng băng UI; progress poll qua
        `after()` trên main thread.
        """
        self._on_tikz_convert_click(TIKZ_OUTPUT_MODE_EMF)
        return

        if not self._exam_data or not getattr(self._exam_data, "questions", None):
            messagebox.showinfo("Chưa có đề",
                                "Hãy tạo đề trước khi chuyển TikZ → EMF.",
                                parent=self)
            return

        # Lưu trạng thái hiện tại của cards vào data trước khi xử lý
        self._sync_cards_to_data()

        # Lazy import để tránh kéo render engine nếu user không bấm.
        from services.tikz_vector_workflow import (
            convert_exam_tikz_to_emf,
            count_pending_blocks,
        )

        total = count_pending_blocks(self._exam_data)
        if total == 0:
            messagebox.showinfo(
                "Không có TikZ",
                "Đề hiện tại không có khối TikZ nào cần chuyển sang EMF.",
                parent=self,
            )
            return

        # ── Dialog progress ────────────────────────────────────────────
        dlg = tk.Toplevel(self)
        dlg.title("Chuyển TikZ → EMF")
        dlg.configure(bg="#FFFBEB")
        dlg.geometry("480x200")
        dlg.resizable(False, False)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        tk.Label(dlg, text=f"📐  Đang chuyển {total} khối TikZ thành EMF...",
                 bg="#FFFBEB", fg="#92400E",
                 font=("Segoe UI", 11, "bold")).pack(pady=(18, 6))

        pb = ttk.Progressbar(dlg, orient="horizontal",
                             mode="determinate", length=420, maximum=total)
        pb.pack(padx=20, pady=4)

        status_var = tk.StringVar(value="0 / {} (0 lỗi)".format(total))
        tk.Label(dlg, textvariable=status_var,
                 bg="#FFFBEB", fg="#334155",
                 font=("Segoe UI", 9)).pack(pady=(2, 6))

        hint_var = tk.StringVar(
            value=TIKZ_TO_EMF_DESCRIPTION
            + " Lần đầu cần LaTeX và Inkscape nên có thể tốn vài giây/khối."
        )
        tk.Label(dlg, textvariable=hint_var,
                 bg="#FFFBEB", fg="#64748B",
                 font=("Segoe UI", 8, "italic"), wraplength=440,
                 justify="left").pack(pady=(2, 6))

        import threading, queue as _queue
        cancel_evt = threading.Event()
        btn_row = tk.Frame(dlg, bg="#FFFBEB")
        btn_row.pack(pady=(2, 10))
        cancel_btn = tk.Button(
            btn_row, text="Hủy",
            bg="#E5E7EB", fg="#111827",
            font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
            padx=16, pady=4,
            command=lambda: (cancel_evt.set(), cancel_btn.config(state="disabled")),
        )
        cancel_btn.pack()

        self._btn_tikz2emf.config(state="disabled", text="⏳ Đang chuyển...")

        q_evt: _queue.Queue = _queue.Queue()

        def _worker():
            try:
                def _cb(done, total_n, errs):
                    q_evt.put(("progress", done, total_n, errs))
                report = convert_exam_tikz_to_emf(
                    self._exam_data,
                    dpi=300,
                    progress_cb=_cb,
                    cancel_event=cancel_evt,
                )
                q_evt.put(("done", report))
            except Exception as e:
                q_evt.put(("fatal", str(e)[:500]))

        threading.Thread(target=_worker, daemon=True).start()

        def _drain():
            try:
                while True:
                    ev = q_evt.get_nowait()
                    kind = ev[0]
                    if kind == "progress":
                        _, done, total_n, errs = ev
                        pb["value"] = done
                        status_var.set(f"{done} / {total_n} ({errs} lỗi)")
                    elif kind == "done":
                        report = ev[1]
                        dlg.grab_release()
                        dlg.destroy()
                        self._btn_tikz2emf.config(
                            state="normal",
                            text=f"📐 {TIKZ_TO_EMF_ACTION_LABEL}",
                        )
                        self._render_exam()  # refresh UI với ảnh mới
                        self._show_tikz_emf_report(report)
                        return
                    elif kind == "fatal":
                        dlg.grab_release()
                        dlg.destroy()
                        self._btn_tikz2emf.config(
                            state="normal",
                            text=f"📐 {TIKZ_TO_EMF_ACTION_LABEL}",
                        )
                        messagebox.showerror(
                            "Lỗi hệ thống",
                            f"TikZ pipeline thất bại:\n{ev[1]}",
                            parent=self,
                        )
                        return
            except _queue.Empty:
                pass
            self.after(120, _drain)

        self.after(120, _drain)

    def _show_tikz_emf_report(self, report) -> None:
        """Hiện tóm tắt kết quả EMF + danh sách lỗi để user sửa tay."""
        if report.failed == 0:
            messagebox.showinfo(
                "Hoàn tất TikZ → EMF",
                f"{report.summary()}\n\n"
                "EMF vector đã sẵn sàng cho Word; PNG preview vẫn được giữ để xem trong app.",
                parent=self,
            )
            return

        # Có lỗi → mở dialog chi tiết
        win = tk.Toplevel(self)
        win.title("Báo cáo TikZ → EMF")
        win.geometry("720x480")
        win.configure(bg="#FFFFFF")
        win.transient(self.winfo_toplevel())

        tk.Label(win, text=report.summary(),
                 bg="#FFFFFF", fg="#0F172A",
                 font=("Segoe UI", 11, "bold")).pack(pady=(12, 4), padx=12, anchor="w")

        tk.Label(
            win,
            text=f"Có {report.failed} khối TikZ không render được. Copy mã TikZ bị lỗi vào tab 'TikZ vẽ hình' để sửa tay.",
            bg="#FFFFFF", fg="#B91C1C",
            font=("Segoe UI", 9), wraplength=680, justify="left",
        ).pack(padx=12, anchor="w")

        # Bảng lỗi
        cols = ("q", "field", "err")
        tv = ttk.Treeview(win, columns=cols, show="headings", height=14)
        tv.heading("q",     text="Câu")
        tv.heading("field", text="Trường")
        tv.heading("err",   text="Lỗi")
        tv.column("q",     width=60,  anchor="center")
        tv.column("field", width=140, anchor="w")
        tv.column("err",   width=480, anchor="w")
        tv.pack(fill="both", expand=True, padx=12, pady=8)

        err_payload: dict[str, str] = {}   # iid → code để copy
        for r in report.results:
            if r.error:
                iid = tv.insert("", "end", values=(r.q_index + 1, r.block.field, r.error))
                err_payload[iid] = r.block.code

        def _copy_selected():
            sel = tv.selection()
            if not sel:
                return
            code = err_payload.get(sel[0], "")
            if not code:
                return
            try:
                self.clipboard_clear()
                self.clipboard_append(code)
                messagebox.showinfo("Đã copy",
                                    "Đã copy mã TikZ lỗi vào clipboard. Mở tab TikZ để dán và sửa.",
                                    parent=win)
            except Exception:
                pass

        def _open_selected_overleaf():
            sel = tv.selection()
            if not sel:
                return
            code = err_payload.get(sel[0], "")
            if not code:
                return
            try:
                from services import overleaf_exporter
                _launcher_path, tex_source = overleaf_exporter.open_tikz_in_overleaf(code)
                self.clipboard_clear()
                self.clipboard_append(tex_source)
                self.update()
                messagebox.showinfo(
                    "Đã mở Overleaf",
                    "Đã mở mã TikZ lỗi trong Overleaf.\n\n"
                    "Nếu trình duyệt không tự import code, source .tex đã được copy vào clipboard để dán thủ công.",
                    parent=win,
                )
            except Exception as e:
                messagebox.showerror("Lỗi Overleaf", str(e), parent=win)

        row = tk.Frame(win, bg="#FFFFFF")
        row.pack(fill="x", padx=12, pady=(0, 12))
        tk.Button(row, text="📋 Copy mã TikZ lỗi",
                  bg="#0EA5E9", fg="white", activebackground="#0284C7",
                  font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                  padx=12, pady=4, command=_copy_selected).pack(side="left")
        tk.Button(row, text="🌐 Mở trên Overleaf",
                  bg="#16A34A", fg="white", activebackground="#15803D",
                  font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                  padx=12, pady=4, command=_open_selected_overleaf).pack(side="left", padx=6)
        tk.Button(row, text="Đóng",
                  bg="#E5E7EB", fg="#111827",
                  font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                  padx=12, pady=4, command=win.destroy).pack(side="right")

    # ──────────────────────────────────────────────────────────────────────
    #  [SPEED-4] ⚙️ CÀI ĐẶT XUẤT — popover gọn cho options Word
    # ──────────────────────────────────────────────────────────────────────
    def _open_export_settings(self) -> None:
        """Popover nhỏ cho cấu hình xuất Word.

        Gom các option đang rải rác:
          • Math mode (text inline LaTeX / equation OMML)
          • Tên trường + tên GV (header Word)
          • Auto-open file sau khi xuất (link tới setting global)
          • Auto-export sau khi gen ([SPEED-1] setting)

        Modal nhỏ, không grab toàn app — user vẫn click toolbar được.
        """
        dlg = tk.Toplevel(self.winfo_toplevel())
        try:
            from ui import set_dialog_icon
            set_dialog_icon(dlg)
        except Exception:
            pass
        dlg.title("⚙️ Cài đặt xuất Word")
        dlg.geometry("520x610")
        dlg.resizable(False, False)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.configure(bg="#F8FAFC")

        # ── Header ──
        hdr = tk.Frame(dlg, bg="#0F2D52")
        hdr.pack(fill="x")
        tk.Label(
            hdr, text="⚙️  Cài đặt xuất Word",
            bg="#0F2D52", fg="white",
            font=("Segoe UI", 11, "bold"),
        ).pack(side="left", padx=14, pady=10)
        tk.Frame(dlg, bg="#10B981", height=2).pack(fill="x")

        body = tk.Frame(dlg, bg="#F8FAFC")
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # ── 1. Math mode ──
        sec1 = tk.LabelFrame(
            body, text="  Chế độ công thức toán  ",
            bg="#F8FAFC", fg="#0F172A",
            font=("Segoe UI", 9, "bold"),
            padx=10, pady=8,
        )
        sec1.pack(fill="x", pady=(0, 8))

        for val, label, desc in [
            ("text",
             "📝  Text chuẩn $..$",
             "Giữ nguyên $..$, dùng MathType Toggle TeX trên Word để chuyển đổi, không ép sang Equation."),
            ("equation",
             "📐  Word Equation (OMML)",
             "Tự động chuyển đổi công thức sang Word Equation của Microsoft Office."),
        ]:
            row = tk.Frame(sec1, bg="#F8FAFC")
            row.pack(fill="x", pady=2)
            tk.Radiobutton(
                row, text=label, variable=self._math_mode_var, value=val,
                bg="#F8FAFC", fg="#0F172A",
                font=("Segoe UI", 9, "bold"),
                activebackground="#F8FAFC",
                anchor="w",
            ).pack(side="left", padx=(0, 4))
            tk.Label(
                row, text=desc,
                bg="#F8FAFC", fg="#64748B",
                font=("Segoe UI", 8, "italic"),
                anchor="w",
            ).pack(side="left")

        # ── 2. Thông tin header ──
        sec2 = tk.LabelFrame(
            body, text="  Thông tin in trên đầu đề  ",
            bg="#F8FAFC", fg="#0F172A",
            font=("Segoe UI", 9, "bold"),
            padx=10, pady=8,
        )
        sec2.pack(fill="x", pady=(0, 8))

        # Load existing values
        school_init  = (getattr(self._exam_data, "school", "") or "") if self._exam_data else ""
        teacher_init = (getattr(self._exam_data, "teacher", "") or "") if self._exam_data else ""
        try:
            import json
            from pathlib import Path as _P
            _sf = _P.home() / ".exam_generator" / "web_settings.json"
            if _sf.exists():
                _s = json.loads(_sf.read_text(encoding="utf-8"))
                school_init = school_init or _s.get("school_name", "")
                teacher_init = teacher_init or _s.get("teacher_name", "")
        except Exception:
            pass

        school_var = tk.StringVar(value=school_init)
        teacher_var = tk.StringVar(value=teacher_init)

        for lbl, var in [
            ("🏫 Trường:", school_var),
            ("👨‍🏫 GV:",   teacher_var),
        ]:
            row = tk.Frame(sec2, bg="#F8FAFC")
            row.pack(fill="x", pady=3)
            tk.Label(row, text=lbl, bg="#F8FAFC", fg="#0F172A",
                     font=("Segoe UI", 9), width=12, anchor="w"
                     ).pack(side="left")
            tk.Entry(row, textvariable=var, font=("Segoe UI", 9),
                     relief="solid", bd=1
                     ).pack(side="left", fill="x", expand=True, padx=4, ipady=2)

        # ── 3. Auto-open + auto-export toggles ──
        sec3 = tk.LabelFrame(
            body, text="  Hành vi sau khi xuất  ",
            bg="#F8FAFC", fg="#0F172A",
            font=("Segoe UI", 9, "bold"),
            padx=10, pady=8,
        )
        sec3.pack(fill="x", pady=(0, 8))

        # Read current global settings
        try:
            from config import (
                load_app_settings,
                is_auto_export_enabled,
                is_word_auto_convert_tables_enabled,
            )
            settings = load_app_settings()
            auto_open_init = settings.get("open_after_export", True)
            auto_export_init = is_auto_export_enabled()
            auto_table_init = is_word_auto_convert_tables_enabled()
        except Exception:
            auto_open_init = True
            auto_export_init = True
            auto_table_init = True

        auto_open_var = tk.BooleanVar(value=auto_open_init)
        auto_export_var = tk.BooleanVar(value=auto_export_init)
        auto_table_var = tk.BooleanVar(value=auto_table_init)

        tk.Checkbutton(
            sec3,
            text="📂 Tự mở file Word sau khi xuất",
            variable=auto_open_var,
            bg="#F8FAFC", fg="#0F172A",
            font=("Segoe UI", 9),
            activebackground="#F8FAFC",
            anchor="w",
        ).pack(fill="x", anchor="w", pady=2)

        tk.Checkbutton(
            sec3,
            text="⚡ Tự xuất Word ngay sau khi tạo đề bằng AI (SPEED-1)",
            variable=auto_export_var,
            bg="#F8FAFC", fg="#0F172A",
            font=("Segoe UI", 9),
            activebackground="#F8FAFC",
            anchor="w",
        ).pack(fill="x", anchor="w", pady=2)

        tk.Checkbutton(
            sec3,
            text="Tự chuyển dòng có dấu | thành bảng Word",
            variable=auto_table_var,
            bg="#F8FAFC", fg="#0F172A",
            font=("Segoe UI", 9),
            activebackground="#F8FAFC",
            anchor="w",
        ).pack(fill="x", anchor="w", pady=(8, 2))
        tk.Label(
            sec3,
            text="Tắt nếu công thức hoặc hình vẽ bị nhảy thành bảng.",
            bg="#F8FAFC", fg="#64748B",
            font=("Segoe UI", 8, "italic"),
            anchor="w",
        ).pack(fill="x", padx=(22, 0), pady=(0, 2))

        # ── Buttons ──
        btn_f = tk.Frame(dlg, bg="#F8FAFC")
        btn_f.pack(fill="x", padx=16, pady=(0, 14))

        def _save_and_close():
            # Save school/teacher into exam_data if available
            if self._exam_data is not None:
                self._exam_data.school = school_var.get().strip()
                self._exam_data.teacher = teacher_var.get().strip()

            # Persist to web_settings.json (used as fallback)
            try:
                import json
                from pathlib import Path as _P
                _sf = _P.home() / ".exam_generator" / "web_settings.json"
                _data = {}
                if _sf.exists():
                    _data = json.loads(_sf.read_text(encoding="utf-8"))
                _data["school_name"]  = school_var.get().strip()
                _data["teacher_name"] = teacher_var.get().strip()
                _sf.parent.mkdir(parents=True, exist_ok=True)
                _sf.write_text(json.dumps(_data, ensure_ascii=False, indent=2),
                               encoding="utf-8")
            except Exception:
                pass

            # Persist auto_open + auto_export
            try:
                from config import (
                    load_app_settings,
                    save_app_settings,
                    set_auto_export_enabled,
                    set_word_auto_convert_tables_enabled,
                    set_word_math_mode,
                )
                s = load_app_settings()
                s["open_after_export"] = bool(auto_open_var.get())
                save_app_settings(s)
                set_auto_export_enabled(bool(auto_export_var.get()))
                set_word_math_mode(self._math_mode_var.get())
                set_word_auto_convert_tables_enabled(bool(auto_table_var.get()))
                self._auto_table_var.set(bool(auto_table_var.get()))
            except Exception:
                pass

            dlg.destroy()

        tk.Button(
            btn_f, text="  💾 Lưu  ",
            bg="#10B981", fg="white",
            activebackground="#059669",
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", bd=0,
            padx=20, pady=6,
            command=_save_and_close,
        ).pack(side="right", padx=4)

        tk.Button(
            btn_f, text="  Hủy  ",
            bg="#64748B", fg="white",
            activebackground="#475569",
            font=("Segoe UI", 9),
            relief="flat", cursor="hand2", bd=0,
            padx=14, pady=6,
            command=dlg.destroy,
        ).pack(side="right")

    # ──────────────────────────────────────────────────────────────────────
    #  📥 TẢI ĐỀ TỪ FILE — Word / PDF / TeX / TXT / HTML
    # ──────────────────────────────────────────────────────────────────────
    def _load_exam_from_file(self):
        """Cho phép user tải 1 file đề (.docx/.pdf/.tex/.txt/.html) →
        quét + nhận diện theo quy trình 3-tầng:
            [1] Khung ===CAU===/===KETCAU=== (cấu trúc chuẩn)
            [2] natural_parser (tự chuyển về chuẩn)
            [3] AI fallback (phải xác nhận vì tốn API)

        Kết quả đổ vào tab đề hiện tại như sau khi Tạo đề bằng AI.
        """
        path = filedialog.askopenfilename(
            title="Chọn file đề cần tải",
            filetypes=[
                ("Tất cả định dạng hỗ trợ",
                 "*.docx *.pdf *.tex *.txt *.html *.htm"),
                ("Word Document",      "*.docx"),
                ("PDF",                "*.pdf"),
                ("LaTeX",              "*.tex"),
                ("Text thuần",         "*.txt"),
                ("HTML",               "*.html *.htm"),
                ("Tất cả file",        "*.*"),
            ])
        if not path:
            return

        # Cảnh báo nếu đang có đề — tránh ghi đè nhầm
        if self._exam_data and getattr(self._exam_data, "questions", None):
            ok = messagebox.askyesno(
                "Đã có đề",
                "Đề hiện tại sẽ bị thay bằng đề tải từ file.\n\nBạn có chắc?")
            if not ok:
                return

        # Hiện cursor chờ + disable toolbar khi đọc file (đọc docx/pdf có thể
        # mất 1-3 giây).
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            try:
                from core.exam_file_loader import load_exam_from_file
                result = load_exam_from_file(path)
            except ImportError as e:
                messagebox.showerror(
                    "Thiếu thư viện",
                    f"Không thể đọc file: {e}\n\n"
                    "Hãy cài các thư viện cần thiết:\n"
                    "  pip install python-docx PyMuPDF beautifulsoup4")
                return
            except Exception as e:
                messagebox.showerror(
                    "Lỗi đọc file", f"Không đọc được file:\n{e}")
                return
        finally:
            self.configure(cursor="")

        tier = result.get("tier", "none")
        questions: list = result.get("questions", [])
        text: str = result.get("text", "")
        err: str = result.get("error", "")

        # ── TH1: parser tại chỗ đã ra câu hỏi → set exam luôn ────────────
        if tier in ("exact", "natural", "latex", "mixed") and questions:
            self._populate_exam_from_loaded(questions, path, tier)
            return

        # ── TH2: không parse được nhưng có text → offer AI ────────────────
        if text and text.strip():
            self._offer_ai_fallback_for_loaded_file(text, path, err)
            return

        # ── TH3: file rỗng / không đọc được ───────────────────────────────
        messagebox.showerror(
            "Không tải được đề",
            err or "File rỗng hoặc không đọc được nội dung nào.")

    def _populate_exam_from_loaded(self, questions: list,
                                   src_path: str, tier: str):
        """Bọc list[Question] vào ExamData + set vào tab → render ngay."""
        from core.models import ExamData
        from pathlib import Path

        # Lấy subject/grade từ tab_config (nếu có)
        subj, grade = "Toán", ""
        try:
            if self._get_subj_grade:
                s, g = self._get_subj_grade()
                subj  = s or subj
                grade = g or grade
        except Exception:
            pass

        exam = ExamData(
            exam_title=f"ĐỀ TẢI TỪ FILE — {Path(src_path).stem}",
            subject=subj,
            grade=grade,
            semester="",
            year="",
            time="90 phút",
            questions=list(questions),
        )
        self.set_exam(exam)

        tier_label = {
            "exact":   "khung ===CAU=== chuẩn",
            "natural": "nhận diện tự nhiên (không dùng AI)",
            "latex":   "LaTeX cấu trúc",
            "mixed":   "cấu trúc app + LaTeX ex_test",
            "ai":      "AI đồng bộ cấu trúc",
        }.get(tier, tier)
        messagebox.showinfo(
            "Đã tải đề từ file",
            f"✅ Nhận diện {len(questions)} câu hỏi từ:\n"
            f"     {Path(src_path).name}\n\n"
            f"Phương pháp: {tier_label}.\n\n"
            "Bạn có thể chỉnh sửa các câu rồi xuất Word / nhiều mã đề.")

    def _offer_ai_fallback_for_loaded_file(self, text: str,
                                           src_path: str, err: str):
        """Không parse được cấu trúc → hỏi user có dùng AI không (tốn API)."""
        from pathlib import Path

        if self._get_ai is None:
            reason = err.strip() if err else "Exact parser và natural parser đều không nhận diện được câu hỏi."
            messagebox.showerror(
                "Không nhận diện được",
                f"Không nhận diện được câu hỏi nào trong file:\n"
                f"     {Path(src_path).name}\n\n"
                f"Lý do gần nhất: {reason[:220]}\n\n"
                "Và cũng chưa cấu hình AI key. Bạn có thể:\n"
                "  • Chỉnh lại file theo mẫu 'Câu 1: … A. … Đáp án: …'.\n"
                "  • Với Đúng/Sai, dùng a), b), c), d) và dòng Đáp án: a=Đ,b=S.\n"
                "  • Hoặc vào tab Cài đặt → nhập API key để bật AI.")
            return

        # Preview tối đa 300 ký tự text để user biết app đã đọc được gì
        preview = text.strip().replace("\n", " ")[:300]
        if len(text) > 300:
            preview += "…"

        confirm = messagebox.askyesno(
            "Nhận diện cục bộ thất bại",
            f"File {Path(src_path).name} đã đọc được nội dung nhưng\n"
            f"KHÔNG khớp cấu trúc câu hỏi chuẩn.\n\n"
            f"Lý do gần nhất: {(err or 'Parser không tìm thấy câu hỏi hợp lệ.')[:220]}\n\n"
            f"Bạn có muốn nhờ AI phân tích + phân loại?\n"
            f"(Sẽ TỐN 1 LƯỢT gọi API của bạn.)\n\n"
            "Gợi ý nếu không dùng AI: sửa text về dạng 'Câu 1:', các đáp án A/B/C/D,\n"
            "và dòng 'Đáp án:' rõ ràng rồi tải lại.\n\n"
            f"Xem trước nội dung đã đọc:\n{preview}")
        if not confirm:
            return

        # Chạy AI trong thread phụ để không block UI
        import threading
        self.configure(cursor="watch")
        self._set_info("⏳ Đang gửi nội dung file tới AI để đồng bộ cấu trúc…")
        threading.Thread(
            target=self._ai_sync_file_worker,
            args=(text, src_path),
            daemon=True,
        ).start()

    def _ai_sync_file_worker(self, raw_text: str, src_path: str):
        """Worker thread: gọi AI đồng bộ cấu trúc, parse kết quả, set exam."""
        import re as _re
        try:
            # Dùng cùng prompt "AI sync" của tab_convert để AI trả về khung
            # ===CAU===/===KETCAU===. _AI_SYNC_PROMPT là class-attribute.
            from ui.tab_convert import TabConvert as _TC
            ai_call = self._get_ai()
            prompt = _TC._AI_SYNC_PROMPT + raw_text
            raw_out = ai_call(prompt)
        except Exception as e:
            self.after(0, self._ai_sync_file_done, None, e, src_path)
            return

        # Parse ===CAU===...===KETCAU=== khối
        try:
            from core.parser import parse_one_question
            blocks = _re.findall(r"===CAU===(.*?)===KETCAU===",
                                 raw_out or "", _re.DOTALL | _re.IGNORECASE)
            qs: list = []
            for b in blocks:
                q = parse_one_question(f"===CAU===\n{b}\n===KETCAU===")
                if q:
                    qs.append(q)
        except Exception as e:
            self.after(0, self._ai_sync_file_done, None, e, src_path)
            return

        self.after(0, self._ai_sync_file_done, qs, None, src_path)

    def _ai_sync_file_done(self, questions, error, src_path: str):
        """Callback UI thread: đổ kết quả AI sync vào tab."""
        self.configure(cursor="")

        if error:
            self._set_info("❌ Lỗi AI")
            messagebox.showerror(
                "Lỗi AI", f"Không gọi được AI để đồng bộ cấu trúc:\n{error}")
            return

        if not questions:
            self._set_info("⚠️ AI không trả về câu hỏi nào")
            messagebox.showwarning(
                "AI không nhận diện được",
                "AI đã gọi thành công nhưng KHÔNG trả về câu hỏi nào đúng\n"
                "chuẩn. Hãy thử chỉnh file theo mẫu 'Câu 1: … A. … Đáp án: …'\n"
                "rồi tải lại.")
            return

        # Đổ vào tab đề như TH1
        self._populate_exam_from_loaded(questions, src_path, tier="ai")

    def _set_info(self, msg: str):
        """Helper: cập nhật info label nếu có, bỏ qua nếu chưa build."""
        try:
            self._info_lbl.config(text=msg)
        except Exception:
            pass

    def _export_word(self):
        if not self._exam_data:
            messagebox.showwarning("Chưa có đề", "Hãy tạo đề trước khi xuất."); return
        self._sync_cards_to_data()
        default = self._smart_save_path("De_KiemTra", ".docx")
        path = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")],
            initialdir=str(Path(default).parent),
            initialfile=Path(default).name)
        if not path: return
        self._save_dir = str(Path(path).parent)
        try:
            from export.word_exporter import export_to_word
            include_sol = self._sol_var.get()
            math_mode = self._math_mode_var.get()
            # ƯU TIÊN school/teacher trên ExamData (đã có thể edit qua dialog
            # "Sửa thông tin đề"). Fallback về web_settings.json nếu ExamData
            # rỗng (đề tạo trước v4.1.0).
            school_name = getattr(self._exam_data, "school", "") or ""
            teacher_name = getattr(self._exam_data, "teacher", "") or ""
            if not school_name or not teacher_name:
                try:
                    import json
                    _sf = Path.home() / ".exam_generator" / "web_settings.json"
                    if _sf.exists():
                        _s = json.loads(_sf.read_text(encoding="utf-8"))
                        school_name = school_name or _s.get("school_name", "")
                        teacher_name = teacher_name or _s.get("teacher_name", "")
                except Exception:
                    pass
            export_to_word(
                self._exam_data, path,
                include_solution=include_sol,
                math_mode=math_mode,
                school_name=school_name,
                teacher_name=teacher_name,
                auto_convert_tables=bool(self._auto_table_var.get()),
            )
            try:
                self._render_exam()
            except Exception:
                pass
            # Hỏi mở file Word sau khi lưu
            self._ask_open_file(path)
        except Exception as e:
            messagebox.showerror("Lỗi xuất Word", str(e))

    def _ask_open_file(self, path: str):
        """Hỏi xác nhận mở file sau khi xuất thành công."""
        import os
        # Kiểm tra setting
        open_after = True
        try:
            from config import load_app_settings
            settings = load_app_settings()
            open_after = settings.get("open_after_export", True)
        except Exception:
            pass

        if open_after:
            result = messagebox.askyesno(
                "Xuất thành công",
                f"Đã lưu tại:\n{path}\n\nBạn có muốn mở file ngay không?")
            if result:
                try:
                    os.startfile(path)
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể mở file:\n{e}")
        else:
            messagebox.showinfo("Xuất thành công", f"Đã lưu tại:\n{path}")

    # NOTE: Tính năng xuất PDF đã bị loại bỏ. Dùng "📄 Xuất Word" và mở bằng
    # MS Word nếu cần in/PDF — Word giữ nguyên công thức MathType/OMML, đổi sang
    # PDF từ Word chất lượng cao hơn mọi pipeline Python trực tiếp từng có.

    def _export_multi(self):
        if not self._exam_data:
            messagebox.showwarning("Chưa có đề", "Hãy tạo đề trước khi xuất."); return
        self._sync_cards_to_data()

        # ── Dialog cấu hình xuất nhiều mã đề ──
        dlg = tk.Toplevel(self)
        from ui import set_dialog_icon
        set_dialog_icon(dlg)
        dlg.title("📂 Xuất nhiều mã đề")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.transient(self.winfo_toplevel())
        dlg.configure(bg="#F9F7F4")

        # ── Header (compact) ──
        hdr = tk.Frame(dlg, bg="#1F497D")
        hdr.pack(fill="x")
        tk.Label(hdr, text="  📂  Cấu hình xuất nhiều mã đề",
                 font=("Segoe UI", 14, "bold"), bg="#1F497D", fg="white"
                 ).pack(pady=10, padx=16, anchor="w")
        tk.Frame(dlg, bg="#10B981", height=2).pack(fill="x")

        body = tk.Frame(dlg, bg="#F9F7F4")
        body.pack(fill="x", padx=22, pady=0)

        # ── Số lượng đề — custom spinbox với nút ± to dễ nhấn ──
        row1 = tk.Frame(body, bg="#F9F7F4")
        row1.pack(fill="x", pady=8)
        tk.Label(row1, text="Số lượng đề:", font=("Segoe UI", 13),
                 bg="#F9F7F4", anchor="w").pack(side="left")

        n_var = tk.IntVar(value=4)
        N_MIN, N_MAX = 2, 6

        spin_frame = tk.Frame(row1, bg="#F9F7F4")
        spin_frame.pack(side="left", padx=10)

        def _spin_dec():
            try:
                v = n_var.get()
            except Exception:
                v = N_MIN
            if v > N_MIN:
                n_var.set(v - 1)

        def _spin_inc():
            try:
                v = n_var.get()
            except Exception:
                v = N_MIN
            if v < N_MAX:
                n_var.set(v + 1)

        _btn_style = dict(
            font=("Segoe UI", 14, "bold"),
            bd=0, relief="flat", cursor="hand2",
            bg="#E2E8F0", fg="#1F2937",
            activebackground="#CBD5E1", activeforeground="#1F2937",
            width=3,
        )
        tk.Button(spin_frame, text="−", command=_spin_dec, **_btn_style
                  ).pack(side="left", ipady=4)
        tk.Entry(spin_frame, textvariable=n_var, width=4,
                 font=("Segoe UI", 14, "bold"), justify="center",
                 bd=1, relief="solid", bg="white",
                 highlightthickness=1, highlightbackground="#CBD5E1"
                 ).pack(side="left", ipady=5, padx=2)
        tk.Button(spin_frame, text="+", command=_spin_inc, **_btn_style
                  ).pack(side="left", ipady=4)

        tk.Label(row1, text=f"({N_MIN} – {N_MAX} mã đề)",
                 font=("Segoe UI", 10),
                 bg="#F9F7F4", fg="#888").pack(side="left", padx=6)

        tk.Frame(body, bg="#CBD5E1", height=1).pack(fill="x", pady=3)

        # ── Helper: pseudo big-checkbox (Unicode icon + clickable frame) ────
        BG_ROW = "#F9F7F4"
        BG_ROW_HOVER = "#EEF2FF"
        FG_ICON_OFF = "#9CA3AF"
        FG_ICON_ON  = "#10B981"

        def _big_check(parent, text, variable, subtext=None):
            """Checkbox compact: icon font 18, text font 12, toàn row clickable."""
            row = tk.Frame(parent, bg=BG_ROW, cursor="hand2",
                           bd=1, relief="solid", highlightthickness=0)
            row.pack(fill="x", pady=3, ipady=2)
            row.config(bg=BG_ROW)
            icon = tk.Label(row, text="☐", font=("Segoe UI", 18),
                            bg=BG_ROW, fg=FG_ICON_OFF, padx=10, pady=2)
            icon.pack(side="left")
            lbl = tk.Label(row, text=text, font=("Segoe UI", 12),
                           bg=BG_ROW, anchor="w", padx=2, pady=2)
            lbl.pack(side="left", fill="x", expand=True)

            def _toggle(_e=None):
                variable.set(not variable.get())

            def _refresh(*_a):
                on = bool(variable.get())
                icon.config(text="☑" if on else "☐",
                            fg=FG_ICON_ON if on else FG_ICON_OFF)
                row.config(highlightbackground="#10B981" if on else "#CBD5E1",
                           highlightthickness=1,
                           bd=0)

            def _hover_in(_e=None):
                for w in (row, icon, lbl):
                    w.config(bg=BG_ROW_HOVER)

            def _hover_out(_e=None):
                for w in (row, icon, lbl):
                    w.config(bg=BG_ROW)

            for w in (row, icon, lbl):
                w.bind("<Button-1>", _toggle)
                w.bind("<Enter>", _hover_in)
                w.bind("<Leave>", _hover_out)
            variable.trace_add("write", _refresh)
            _refresh()

            if subtext:
                tk.Label(parent, text="        " + subtext,
                         font=("Segoe UI", 9, "italic"),
                         bg="#F9F7F4", fg="#64748B",
                         justify="left", anchor="w").pack(anchor="w", padx=2)
            return row

        def _big_radio(parent, text, variable, value, subtext=None):
            """Radio button compact: icon font 18, text font 12, toàn row clickable."""
            row = tk.Frame(parent, bg=BG_ROW, cursor="hand2",
                           bd=0, highlightthickness=1,
                           highlightbackground="#E5E7EB")
            row.pack(fill="x", pady=2, ipady=2)
            icon = tk.Label(row, text="○", font=("Segoe UI", 18, "bold"),
                            bg=BG_ROW, fg=FG_ICON_OFF, padx=10, pady=2)
            icon.pack(side="left")
            lbl = tk.Label(row, text=text, font=("Segoe UI", 12),
                           bg=BG_ROW, anchor="w", padx=2, pady=2)
            lbl.pack(side="left", fill="x", expand=True)

            def _select(_e=None):
                variable.set(value)

            def _refresh(*_a):
                sel = variable.get() == value
                icon.config(text="●" if sel else "○",
                            fg=FG_ICON_ON if sel else FG_ICON_OFF)
                row.config(highlightbackground="#10B981" if sel else "#E5E7EB",
                           highlightthickness=2 if sel else 1)
                new_bg = "#ECFDF5" if sel else BG_ROW
                for w in (row, icon, lbl):
                    w.config(bg=new_bg)

            def _hover_in(_e=None):
                if variable.get() != value:
                    for w in (row, icon, lbl):
                        w.config(bg=BG_ROW_HOVER)

            def _hover_out(_e=None):
                if variable.get() != value:
                    for w in (row, icon, lbl):
                        w.config(bg=BG_ROW)

            for w in (row, icon, lbl):
                w.bind("<Button-1>", _select)
                w.bind("<Enter>", _hover_in)
                w.bind("<Leave>", _hover_out)
            variable.trace_add("write", _refresh)
            _refresh()

            if subtext:
                tk.Label(parent, text="        " + subtext,
                         font=("Segoe UI", 9, "italic"),
                         bg="#F9F7F4", fg="#64748B",
                         justify="left", anchor="w").pack(anchor="w", padx=2)
            return row

        # ── Trộn câu hỏi ────────────────────────────────────────────────────
        shuffle_q_var = tk.BooleanVar(value=True)
        _big_check(body, "Trộn câu hỏi (trong từng phần)", shuffle_q_var,
                   subtext=("Chỉ trộn vị trí câu trong cùng loại "
                            "(TN / DS / TLN / TL), không trộn giữa các phần."))

        # ── Trộn đáp án ─────────────────────────────────────────────────────
        shuffle_a_var = tk.BooleanVar(value=True)
        _big_check(body, "Trộn đáp án (áp dụng với Trắc nghiệm)", shuffle_a_var)

        tk.Frame(body, bg="#CBD5E1", height=1).pack(fill="x", pady=(6, 2))

        # ── Đa dạng hoá số liệu ─────────────────────────────────────────────
        tk.Label(body, text="🔢 Đa dạng hoá số liệu (mỗi mã có số khác nhau):",
                 font=("Segoe UI", 11, "bold"),
                 bg="#F9F7F4", fg="#1F497D", anchor="w"
                 ).pack(fill="x", pady=(4, 2))

        variant_mode_var = tk.StringVar(value="none")

        _big_radio(body, "Không (tất cả mã dùng chung số liệu)",
                   variant_mode_var, "none")
        _big_radio(body, "Thay số bằng Python/SymPy (nhanh, chắc đúng)",
                   variant_mode_var, "python",
                   subtext=("Hỗ trợ: pt bậc 1 (ax+b=0), pt bậc 2 (ax²+bx+c=0). "
                            "Dạng khác giữ nguyên số gốc."))
        _big_radio(body, "Thay số bằng AI (đa dạng hơn, chậm hơn, tốn API)",
                   variant_mode_var, "ai",
                   subtext="AI chỉ thay số, KHÔNG tạo đề mới. Mọi câu đều được biến đổi.")

        # ── Prompt AI thủ công (không cần API) ─────────────────────────────
        tk.Frame(body, bg="#CBD5E1", height=1).pack(fill="x", pady=(6, 2))

        tk.Label(body,
                 text="📋  Hoặc: Dùng AI bên ngoài (ChatGPT / Claude / Gemini — MIỄN PHÍ)",
                 font=("Segoe UI", 11, "bold"),
                 bg="#F9F7F4", fg="#1F497D", anchor="w"
                 ).pack(fill="x", pady=(4, 0))

        tk.Label(body,
                 text="Copy prompt → upload Word vào chatbot → AI trả đề khác số.",
                 font=("Segoe UI", 9), bg="#F9F7F4", fg="#64748B",
                 justify="left", anchor="w"
                 ).pack(fill="x", pady=(0, 4))

        def _copy_manual_prompt():
            try:
                from services.ai_variant_generator import get_manual_variant_prompt
                prompt_text = get_manual_variant_prompt()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không nạp được prompt:\n{e}",
                                     parent=dlg)
                return
            try:
                dlg.clipboard_clear()
                dlg.clipboard_append(prompt_text)
                dlg.update()  # giữ clipboard sau khi dialog đóng
            except Exception as e:
                messagebox.showerror("Lỗi clipboard", str(e), parent=dlg)
                return
            messagebox.showinfo(
                "✅ Đã copy prompt",
                "Prompt đã được copy vào clipboard.\n\n"
                "Các bước tiếp theo:\n"
                "  1. Xuất 1 file Word đề gốc (dùng nút '📄 Xuất Word' "
                "ở tab này để có 1 file mẫu).\n"
                "  2. Mở ChatGPT / Claude / Gemini (bản web).\n"
                "  3. Upload file Word vừa xuất vào khung chat.\n"
                "  4. Dán prompt (Ctrl+V) rồi gửi.\n"
                "  5. Lưu kết quả AI trả về làm đề tương tự.\n\n"
                "Mẹo: có thể gửi lại prompt nhiều lần để AI sinh "
                "nhiều đề khác nhau.",
                parent=dlg,
            )

        def _preview_manual_prompt():
            try:
                from services.ai_variant_generator import get_manual_variant_prompt
                prompt_text = get_manual_variant_prompt()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không nạp được prompt:\n{e}",
                                     parent=dlg)
                return
            pdlg = tk.Toplevel(dlg)
            try:
                from ui import set_dialog_icon
                set_dialog_icon(pdlg)
            except Exception:
                pass
            pdlg.title("👁  Xem / chỉnh prompt đề tương tự")
            pdlg.configure(bg="#F9F7F4")
            pdlg.geometry("860x620")
            pdlg.transient(dlg)
            pdlg.grab_set()

            tk.Label(pdlg,
                     text="👁  Prompt đề tương tự — có thể chỉnh trước khi copy",
                     font=("Segoe UI", 13, "bold"),
                     bg="#1F497D", fg="white",
                     anchor="w", padx=16, pady=10
                     ).pack(fill="x")

            tk.Label(pdlg,
                     text=("Bạn có thể chỉnh sửa nội dung bên dưới (thêm ràng buộc"
                           " riêng, đổi ngôn ngữ…). Nút 'Copy' sẽ copy BẢN HIỆN TẠI"
                           " trong ô."),
                     font=("Segoe UI", 10), bg="#F9F7F4", fg="#475569",
                     justify="left", anchor="w", wraplength=820
                     ).pack(fill="x", padx=12, pady=(10, 4))

            tframe = tk.Frame(pdlg, bg="#F9F7F4")
            tframe.pack(fill="both", expand=True, padx=12, pady=(0, 8))
            txt = tk.Text(tframe, font=("Consolas", 10), wrap="word",
                          bd=1, relief="solid",
                          bg="white", fg="#1F2937",
                          padx=10, pady=8, undo=True)
            sb = ttk.Scrollbar(tframe, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=sb.set)
            sb.pack(side="right", fill="y")
            txt.pack(side="left", fill="both", expand=True)
            txt.insert("1.0", prompt_text)

            def _reset():
                txt.delete("1.0", "end")
                txt.insert("1.0", prompt_text)

            def _copy_edited():
                content = txt.get("1.0", "end-1c")
                if not content.strip():
                    messagebox.showwarning("Trống",
                                           "Prompt đang trống.", parent=pdlg)
                    return
                try:
                    pdlg.clipboard_clear()
                    pdlg.clipboard_append(content)
                    pdlg.update()
                except Exception as e:
                    messagebox.showerror("Lỗi clipboard", str(e), parent=pdlg)
                    return
                messagebox.showinfo("✅ Đã copy",
                                    "Đã copy prompt (bản hiện tại) vào clipboard.",
                                    parent=pdlg)

            bfr = tk.Frame(pdlg, bg="#F9F7F4")
            bfr.pack(fill="x", padx=12, pady=(0, 12))
            tk.Button(bfr, text="📋  Copy prompt này",
                      command=_copy_edited,
                      bg="#10B981", fg="white",
                      font=("Segoe UI", 12, "bold"),
                      padx=18, pady=8, relief="flat", cursor="hand2"
                      ).pack(side="left")
            tk.Button(bfr, text="↺  Khôi phục bản mặc định",
                      command=_reset,
                      bg="#E2E8F0", font=("Segoe UI", 11),
                      padx=14, pady=7, relief="flat", cursor="hand2"
                      ).pack(side="left", padx=8)
            tk.Button(bfr, text="Đóng", command=pdlg.destroy,
                      font=("Segoe UI", 11), padx=18, pady=7,
                      bg="#E2E8F0", relief="flat", cursor="hand2"
                      ).pack(side="right")

        prow = tk.Frame(body, bg="#F9F7F4")
        prow.pack(fill="x", pady=(0, 2))
        tk.Button(prow, text="📋  Copy prompt vào clipboard",
                  command=_copy_manual_prompt,
                  bg="#10B981", fg="white",
                  font=("Segoe UI", 11, "bold"),
                  padx=14, pady=5, relief="flat", cursor="hand2"
                  ).pack(side="left")
        tk.Button(prow, text="👁  Xem / chỉnh",
                  command=_preview_manual_prompt,
                  bg="#E2E8F0", font=("Segoe UI", 11),
                  padx=12, pady=5, relief="flat", cursor="hand2"
                  ).pack(side="left", padx=8)

        _result = {"ok": False}

        def _do_export():
            _result["ok"] = True
            _result["n"] = max(2, min(6, n_var.get()))
            _result["shuffle_q"] = shuffle_q_var.get()
            _result["shuffle_a"] = shuffle_a_var.get()
            _result["variant_mode"] = variant_mode_var.get()
            dlg.destroy()

        btn_f = tk.Frame(dlg, bg="#F9F7F4")
        btn_f.pack(fill="x", padx=22, pady=12)
        tk.Button(btn_f, text="  📂  Chọn thư mục & Xuất  ",
                  command=_do_export, bg="#10B981", fg="white",
                  font=("Segoe UI", 12, "bold"), relief="flat",
                  cursor="hand2", padx=18, pady=7).pack(side="left", fill="x", expand=True)
        tk.Button(btn_f, text="  Hủy  ", command=dlg.destroy,
                  font=("Segoe UI", 11), padx=14, pady=6,
                  relief="flat", bg="#E2E8F0", cursor="hand2").pack(side="right", padx=0)

        # Center dialog
        dlg.update_idletasks()
        dw = dlg.winfo_reqwidth() + 60
        dh = dlg.winfo_reqheight() + 20
        dw = max(dw, 560)
        sw = dlg.winfo_screenwidth()
        sh = dlg.winfo_screenheight()
        # Clamp để không tràn screen trên laptop thấp (1366x768 etc.)
        dh = min(dh, sh - 80)
        dw = min(dw, sw - 40)
        dlg.geometry(f"{dw}x{dh}+{(sw-dw)//2}+{(sh-dh)//2}")

        dlg.focus_force()
        self.wait_window(dlg)

        if not _result.get("ok"):
            return

        folder = filedialog.askdirectory(
            title="Chọn thư mục xuất nhiều mã đề",
            initialdir=self._get_save_dir())
        if not folder:
            return
        self._save_dir = folder
        try:
            from export.word_exporter import export_multi_code

            variant_mode = _result.get("variant_mode", "none")
            ai_call = None
            if variant_mode == "ai":
                # Lấy ai_call từ main_window (giống pipeline tạo đề)
                ai_call = self._get_ai_call_for_variant()
                if ai_call is None:
                    messagebox.showerror(
                        "Chưa cấu hình AI",
                        "Chế độ 'Thay số bằng AI' yêu cầu đã cấu hình API key.\n"
                        "Vui lòng mở Tab ① → 'Cài đặt AI' và nhập API key.")
                    return

            files = export_multi_code(
                self._exam_data, folder,
                n_codes=_result["n"],
                shuffle_questions=_result["shuffle_q"],
                shuffle_answers=_result["shuffle_a"],
                variant_mode=variant_mode,
                ai_call=ai_call,
                auto_convert_tables=bool(self._auto_table_var.get()),
            )
            # Thông điệp khác nhau theo chế độ
            extra = ""
            if variant_mode == "python":
                extra = "\n(Đã thay số bằng SymPy cho các dạng hỗ trợ.)"
            elif variant_mode == "ai":
                extra = "\n(Đã nhờ AI thay số cho mọi câu.)"
            messagebox.showinfo("Xuất thành công",
                f"Đã tạo {len(files)} file tại:\n{folder}{extra}")
        except Exception as e:
            messagebox.showerror("Lỗi xuất nhiều mã đề", str(e))

    def _switch_to_shuffle_tab(self):
        """Chuyển sang Tab Trộn đề thi trong ứng dụng và nạp đề hiện tại."""
        try:
            cur = self.master
            while cur and not hasattr(cur, "_switch_to_shuffle_tab"):
                cur = getattr(cur, "master", None)
            if cur and hasattr(cur, "_switch_to_shuffle_tab"):
                cur._switch_to_shuffle_tab()
            else:
                nb = self.master
                if isinstance(nb, ttk.Notebook):
                    for tab_id in nb.tabs():
                        tab_w = nb.nametowidget(tab_id)
                        if hasattr(tab_w, "_on_load_from_app_exam"):
                            nb.select(tab_id)
                            tab_w._on_load_from_app_exam(silent=True)
                            return
        except Exception as e:
            messagebox.showwarning("Thông báo", f"Không thể chuyển sang Tab Trộn đề: {e}")

    def _open_omr_window(self):
        """Alias tương thích cũ."""
        self._switch_to_shuffle_tab()

    def _get_ai_call_for_variant(self):
        """Lấy ai_call từ main_window để phục vụ variant_mode='ai'.

        Trả None nếu không có cấu hình AI. Không fail nếu main_window không có
        _make_ai_call (app cũ).
        """
        try:
            top = self.winfo_toplevel()
            if hasattr(top, "_make_ai_call"):
                return top._make_ai_call()
        except Exception:
            pass
        return None

    def _retry_failed(self):
        messagebox.showinfo("Tạo lại câu lỗi",
                             "Tính năng này sẽ tự động tạo lại các câu bị lỗi.\n"
                             "Hãy nhấn 'Tạo đề' từ cửa sổ chính để thực hiện.")

    def _open_ai_fix(self):
        messagebox.showinfo("AI kiểm duyệt & sửa",
                             "AI sẽ kiểm duyệt và đề xuất sửa các câu có vấn đề.\n"
                             "Vui lòng chạy pipeline QC ở tab ⑤ trước.")

    def _check_score(self):
        if not self._exam_data: return
        self._sync_cards_to_data()
        qs = self._exam_data.questions
        from config import POINTS_MAP
        total = sum(POINTS_MAP.get(q.qtype, 0.25) for q in qs)
        messagebox.showinfo("Kiểm tra điểm",
                             f"Tổng điểm tính theo thang 10:\n\n"
                             f"Số câu: {len(qs)}\nTổng điểm: {total:.2f}\n\n"
                             + ("✅ Đạt thang 10 điểm." if abs(total - 10) < 0.01
                                else f"⚠️ Chưa đủ 10 điểm (còn thiếu {10-total:.2f} điểm)."))

    def _run_review(self):
        messagebox.showinfo("Kiểm tra chất lượng",
                             "Hãy sang tab ⑤ Kiểm tra chất lượng để chạy pipeline QC đầy đủ.")

    def _export_error_report(self):
        if not self._exam_data: return
        qs   = self._exam_data.questions
        errs = [(i+1, q._error) for i, q in enumerate(qs) if q._error]
        if not errs:
            messagebox.showinfo("Báo cáo lỗi", "✅ Không có câu bị lỗi!"); return
        lines = [f"BÁO CÁO LỖI — {len(errs)} câu bị lỗi:", ""]
        for n, err in errs:
            lines.append(f"Câu {n}: {err}")
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Văn bản", "*.txt")],
            initialfile="bao_cao_loi.txt")
        if path:
            from pathlib import Path
            Path(path).write_text("\n".join(lines), encoding="utf-8")
            messagebox.showinfo("Đã xuất", f"Lưu tại:\n{path}")

    # ── Feature gating ──────────────────────────────────────────────────
    def apply_feature_gates(self, features: dict[str, bool]) -> None:
        """Bản mở khóa: luôn giữ các nút ở trạng thái hoạt động."""
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  LaTeX Preview Dialog — Render câu hỏi với công thức toán học
# ══════════════════════════════════════════════════════════════════════════════

_LATEX_Q_TEMPLATE = r"""\documentclass[12pt, border=10pt]{{standalone}}
\usepackage{{iftex}}
\ifPDFTeX
  \usepackage[utf8]{{inputenc}}
\fi
\usepackage[vietnamese]{{babel}}
\usepackage{{amsmath, amssymb, amsfonts}}
\usepackage{{tikz}}
\usetikzlibrary{{calc,angles,quotes}}
\usepackage{{array}}
\begin{{document}}
\begin{{minipage}}{{14cm}}
{content}
\end{{minipage}}
\end{{document}}
"""


def _q_to_latex(q, idx: int) -> str:
    """Convert a Question object to LaTeX source for preview."""
    import re

    def _fix(text: str) -> str:
        """Convert ${...}$ notation to standard LaTeX $...$."""
        # ${...}$ → $...$
        text = re.sub(r'\$\{(.+?)\}\$', r'$\1$', text)
        # Escape % and & in non-math parts
        parts = re.split(r'(\$[^$]+\$)', text)
        result = []
        for p in parts:
            if p.startswith('$') and p.endswith('$'):
                result.append(p)
            else:
                p = p.replace('&', r'\&')
                result.append(p)
        return ''.join(result)

    lines = []
    lines.append(r'\noindent\textbf{Câu ' + str(idx + 1) + r'.} ')

    # Badge
    type_map = {"TN": "Trắc nghiệm", "DS": "Đúng--Sai",
                "TLN": "Trả lời ngắn", "TL": "Tự luận"}
    lines.append(r'\textit{[' + type_map.get(q.qtype, q.qtype)
                 + ' -- ' + q.level + r']}')
    lines.append('')

    # Question text
    lines.append(r'\medskip')
    lines.append(_fix(q.question))
    lines.append('')

    if q.qtype == "TN" and q.options:
        lines.append(r'\begin{enumerate}')
        lines.append(r'\renewcommand{\labelenumi}{\textbf{\Alph{enumi}.}}')
        for k in "ABCD":
            v = q.options.get(k, "")
            mark = r' \quad $\Leftarrow$ \textbf{ĐÁP ÁN}' if k == q.answer else ''
            lines.append(r'\item ' + _fix(v) + mark)
        lines.append(r'\end{enumerate}')

    elif q.qtype == "DS" and q.items:
        for k in "abcd":
            v = q.items.get(k, "")
            ans = q.answers.get(k, False) if q.answers else False
            mark = r'\textbf{(Đ)}' if ans else r'\textbf{(S)}'
            lines.append(r'\noindent\textbf{' + k + r'.} ' + _fix(v)
                         + r' \hfill ' + mark)
            lines.append(r'\smallskip')

    elif q.qtype == "TLN" and q.answer:
        lines.append(r'\medskip')
        lines.append(r'\noindent\textbf{Đáp số:} ' + _fix(str(q.answer)))

    # Solution
    sol = q.solution or ""
    if q.qtype == "DS" and q.item_solutions:
        sol_parts = []
        for k in "abcd":
            s = q.item_solutions.get(k, "")
            if s:
                sol_parts.append(f"\\textbf{{{k}.}} {_fix(s)}")
        if sol_parts:
            sol = r' \\ '.join(sol_parts)

    if sol:
        lines.append(r'\medskip')
        lines.append(r'\noindent\rule{\linewidth}{0.4pt}')
        lines.append(r'\smallskip')
        lines.append(r'\noindent\textbf{Lời giải:} ' + _fix(sol))

    return '\n'.join(lines)


class _LaTeXPreviewDialog(tk.Toplevel):
    """Dialog xem trước câu hỏi với công thức LaTeX được render."""

    def __init__(self, parent, q, idx: int):
        super().__init__(parent)
        self.title(f"Xem trước LaTeX — Câu {idx + 1}")
        self.configure(bg="#F9F7F4")
        self.transient(parent)
        self.grab_set()

        try:
            from ui import set_dialog_icon
            set_dialog_icon(self)
        except Exception:
            pass

        self._q = q
        self._idx = idx
        self._img_pil = None
        self._img_tk = None

        # ── Header ──
        hdr = tk.Frame(self, bg="#1F497D")
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"  👁  Xem trước LaTeX — Câu {idx + 1}",
                 font=("Segoe UI", 12, "bold"), bg="#1F497D", fg="white"
                 ).pack(side="left", padx=12, pady=8)
        tk.Frame(self, bg="#8B5CF6", height=3).pack(fill="x")

        # ── Action bar ──
        act = tk.Frame(self, bg="#E2E8F0")
        act.pack(fill="x")

        tk.Button(act, text="  📋 Copy ảnh  ", font=("Segoe UI", 9, "bold"),
                  bg="#3B82F6", fg="white", activebackground="#2563EB",
                  relief="flat", cursor="hand2", padx=8, pady=2,
                  command=self._copy_image).pack(side="left", padx=8, pady=4)
        tk.Button(act, text="  💾 Lưu PNG  ", font=("Segoe UI", 9, "bold"),
                  bg="#8B5CF6", fg="white", activebackground="#7C3AED",
                  relief="flat", cursor="hand2", padx=8, pady=2,
                  command=self._save_png).pack(side="left", padx=2, pady=4)

        self._status = tk.Label(act, text="", fg="#64748B",
                                 font=("Segoe UI", 8), bg="#E2E8F0")
        self._status.pack(side="right", padx=8)

        # ── Canvas ──
        canvas_f = tk.Frame(self, bg="white", bd=1, relief="solid")
        canvas_f.pack(fill="both", expand=True, padx=10, pady=8)

        self._canvas = tk.Canvas(canvas_f, bg="white", highlightthickness=0)
        vsb = ttk.Scrollbar(canvas_f, orient="vertical", command=self._canvas.yview)
        hsb = ttk.Scrollbar(canvas_f, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self._canvas.pack(fill="both", expand=True)

        self._canvas.create_text(300, 100, text="Đang render...",
                                  fill="#9CA3AF", font=("Segoe UI", 14))

        # ── Error text ──
        self._err_text = tk.Text(self, font=("Consolas", 9),
                                  bg="#FEF2F2", fg="#DC2626", height=4,
                                  wrap="word", state="disabled")

        # ── Geometry ──
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = min(900, sw - 100), min(700, sh - 100)
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(600, 400)

        # Start rendering
        self._canvas.bind("<MouseWheel>",
                           lambda e: self._canvas.yview_scroll(int(-4*(e.delta/120)), "units"))

        import threading
        threading.Thread(target=self._do_render, daemon=True).start()

    def _do_render(self):
        try:
            latex_src = _q_to_latex(self._q, self._idx)
            full_src = _LATEX_Q_TEMPLATE.format(content=latex_src)
            img = _render_latex_doc(full_src, dpi=200)
            self._img_pil = img
            self.after(0, lambda: self._show_image(img))
            self.after(0, lambda: self._status.config(
                text=f"✅ {img.width}×{img.height}px", fg="#059669"))
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda msg=err_msg: self._show_error(msg))

    def _show_image(self, img):
        from PIL import ImageTk
        cw = max(self._canvas.winfo_width(), 500)
        ch = max(self._canvas.winfo_height(), 300)
        scale = min(cw / img.width, 1.0)
        if scale < 1.0:
            display = img.resize((int(img.width * scale), int(img.height * scale)),
                                  resample=3)
        else:
            display = img
        self._img_tk = ImageTk.PhotoImage(display)
        self._canvas.delete("all")
        self._canvas.create_image(10, 10, image=self._img_tk, anchor="nw")
        self._canvas.configure(scrollregion=(0, 0, display.width + 20, display.height + 20))

    def _show_error(self, msg: str):
        self._status.config(text="❌ Lỗi render", fg="#DC2626")
        self._canvas.delete("all")
        self._canvas.create_text(300, 60, text="Lỗi render LaTeX",
                                  fill="#DC2626", font=("Segoe UI", 13, "bold"))
        self._err_text.config(state="normal")
        self._err_text.delete("1.0", "end")
        self._err_text.insert("1.0", msg[:3000])
        self._err_text.config(state="disabled")
        self._err_text.pack(fill="x", padx=10, pady=8)

    def _copy_image(self):
        if not self._img_pil:
            messagebox.showwarning("Chưa có ảnh", "Đợi render xong."); return
        try:
            from ui.tab_tikz import _copy_pil_to_clipboard
            _copy_pil_to_clipboard(self._img_pil)
            self._status.config(text="📋 Đã copy!", fg="#059669")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _save_png(self):
        if not self._img_pil:
            messagebox.showwarning("Chưa có ảnh", "Đợi render xong."); return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
            initialfile=f"cau_{self._idx+1}.png")
        if path:
            self._img_pil.save(path, dpi=(200, 200))
            messagebox.showinfo("OK", f"Đã lưu:\n{path}")


def _render_latex_doc(latex_src: str, dpi: int = 200):
    """Render a full LaTeX document source → PIL Image.

    Chạy LaTeX engine subprocess — PHẢI gọi từ worker thread (không UI thread)
    vì subprocess.run blocking tới PDFLATEX_TIMEOUT giây. Caller hiện tại:
    `LatexPreviewDialog._do_render` (đã ở thread riêng).
    """
    import os, tempfile, subprocess
    from config import PDFLATEX_TIMEOUT
    from services import latex_engine

    try:
        engine = latex_engine.get_engine()
    except latex_engine.LatexEngineNotFound as e:
        raise RuntimeError(str(e))

    with latex_engine.safe_temporary_directory(prefix="latex_prev_") as tmpdir:
        tex_path = os.path.join(tmpdir, "preview.tex")
        pdf_path = os.path.join(tmpdir, "preview.pdf")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_src)

        si = None
        cflags = 0
        if os.name == "nt":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            cflags = subprocess.CREATE_NO_WINDOW

        result = subprocess.run(
            engine.build_argv("preview.tex"),
            cwd=tmpdir, capture_output=True, text=True, timeout=PDFLATEX_TIMEOUT,
            startupinfo=si, creationflags=cflags,
        )

        if not os.path.exists(pdf_path):
            log = result.stdout or ""
            err_lines = [l for l in log.splitlines() if l.startswith("!")]
            err_msg = "\n".join(err_lines[:10]) if err_lines else log[-2000:]
            raise RuntimeError(f"{engine.name} lỗi:\n{err_msg}")

        try:
            import fitz
            doc = fitz.open(pdf_path)
            page = doc[0]
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            from PIL import Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            doc.close()
            return img
        except ImportError:
            raise RuntimeError("Cần cài PyMuPDF: pip install PyMuPDF")
