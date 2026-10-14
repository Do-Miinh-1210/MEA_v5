"""
ui/tooltip.py — Hover tooltip cho preview câu hỏi (Yêu cầu 8).
"""
from __future__ import annotations
import tkinter as tk
from typing import Optional
from config import TYPE_LABELS


class QuestionTooltip:
    """Popup box xuất hiện khi rê chuột vào câu hỏi trong preview."""

    def __init__(self, widget: tk.Text):
        self._widget  = widget
        self._tip:    Optional[tk.Toplevel] = None
        self._after:  Optional[str]          = None
        self._cur_idx = -1

    # ── Public ─────────────────────────────────────────────────────────────

    def schedule(self, q, q_idx: int, root_x: int, root_y: int, delay=450) -> None:
        """Lên lịch hiện tooltip sau `delay` ms nếu vẫn cùng câu."""
        if q_idx == self._cur_idx:
            return
        self.hide()
        self._cur_idx = q_idx
        self._after = self._widget.after(
            delay, lambda: self._show(q, q_idx, root_x, root_y)
        )

    def hide(self) -> None:
        """Ẩn tooltip ngay lập tức."""
        if self._after:
            try: self._widget.after_cancel(self._after)
            except Exception: pass
            self._after = None
        if self._tip:
            try: self._tip.destroy()
            except Exception: pass
            self._tip = None
        self._cur_idx = -1

    # ── Internal ───────────────────────────────────────────────────────────

    def _show(self, q, q_idx: int, x: int, y: int) -> None:
        self._tip = tw = tk.Toplevel(self._widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x+14}+{y+8}")
        tw.attributes("-topmost", True)

        # Frame viền
        outer = tk.Frame(tw, bg="#1F497D", padx=1, pady=1)
        outer.pack()
        inner = tk.Frame(outer, bg="#FFFEF0", padx=12, pady=8)
        inner.pack()

        text = self._build_text(q, q_idx)
        tk.Label(
            inner, text=text, bg="#FFFEF0", fg="#1a1a1a",
            font=("Segoe UI", 9), justify="left", wraplength=440,
        ).pack()

    @staticmethod
    def _build_text(q, q_idx: int) -> str:
        qtype  = getattr(q, "qtype", "") or q.get("qtype","") if isinstance(q, dict) else q.qtype
        level  = getattr(q, "level", "?") if not isinstance(q, dict) else q.get("level","?")
        topic  = getattr(q, "topic", "")  if not isinstance(q, dict) else q.get("topic","")
        is_err = getattr(q, "_error", False) if not isinstance(q, dict) else q.get("_error", False)

        sep = "─" * 52
        header = (f"Câu {q_idx+1}  ──  "
                  f"{TYPE_LABELS.get(qtype, qtype)}  │  "
                  f"Mức: {level}  │  {topic[:40]}")
        lines = [header, sep]

        if is_err:
            lines.append("⚠️  Câu lỗi — Double-click để tạo lại hoặc chỉnh sửa.")
            return "\n".join(lines)

        question = (getattr(q,"question","") if not isinstance(q,dict) else q.get("question",""))
        if question:
            short = question[:130] + ("…" if len(question) > 130 else "")
            lines.append(f"Nội dung: {short}")

        if qtype == "TN":
            opts   = (q.options if not isinstance(q,dict) else q.get("options",{}))
            answer = (q.answer  if not isinstance(q,dict) else q.get("answer",""))
            for k, v in opts.items():
                v_s = (v[:55]+"…") if len(v)>55 else v
                mark = "  ✓" if k == answer else ""
                lines.append(f"  {k}. {v_s}{mark}")
            sol = (q.solution if not isinstance(q,dict) else q.get("solution",""))
            if sol:
                lines.append(f"Giải: {sol[:80]}{'…' if len(sol)>80 else ''}")

        elif qtype == "DS":
            items   = (q.items   if not isinstance(q,dict) else q.get("items",{}))
            answers = (q.answers if not isinstance(q,dict) else q.get("answers",{}))
            lines.append(sep[:30])
            for k, v in items.items():
                v_s     = (v[:52]+"…") if len(v)>52 else v
                verdict = "[Đ]" if answers.get(k) else "[S]"
                lines.append(f"  ({k}) {v_s}  {verdict}")

        elif qtype in ("TLN", "TL"):
            pts = (q.points if not isinstance(q,dict) else q.get("points",""))
            ans = (q.answer if not isinstance(q,dict) else q.get("answer",""))
            if pts: lines.append(f"Điểm: {pts}")
            if ans: lines.append(f"Đáp số: {ans}")
            sol = (q.solution if not isinstance(q,dict) else q.get("solution",""))
            if sol:
                lines.append(f"Giải: {sol[:80]}{'…' if len(sol)>80 else ''}")

        lines += [sep, "Double-click → chỉnh sửa  •  Hover để xem tóm tắt"]
        return "\n".join(lines)
