"""Native V5 Convert view: images, documents, or text to questions."""
from __future__ import annotations

import tempfile
import threading
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk

from core.models import ExamData, Question
from v5.convert_pipeline import (
    assign_ids_for_save,
    build_chatbot_prompt,
    build_text_normalize_prompt,
    chatbot_prompt_catalog,
    combine_results,
    parse_text_questions,
    rewrite_prompt_and_tikz_text,
)


PROVIDERS = ["Google Gemini", "Anthropic Claude", "DeepSeek", "9Router"]
VISION_PROVIDERS = {"Google Gemini", "Anthropic Claude", "9Router"}
MODE_IMAGE = "Ảnh -> Câu hỏi"
MODE_DOCUMENT = "PDF/Word/TeX/Text -> Câu hỏi"
MODE_TEXT = "AI Text -> Câu hỏi"
MODELS = {
    "Google Gemini": "gemini-3.8-flash",
    "Anthropic Claude": "claude-sonnet-4-5",
    "DeepSeek": "deepseek-chat",
    "9Router": "ag/gemini-3.8-flash",
}
MODEL_OPTIONS = {
    "Google Gemini": [
        "gemini-3.8-flash",
        "gemini-3.1-pro",
        "gemini-3.8-live",
        "gemini-3.5-flash-lite",
        "gemini-2.5-pro",
        "gemini-2.5-flash",
    ],
    "Anthropic Claude": ["claude-sonnet-4-5", "claude-opus-4-1", "claude-haiku-4-5"],
    "DeepSeek": ["deepseek-chat", "deepseek-reasoner"],
    "9Router": [
        "ag/gemini-3.8-flash",
        "ag/gemini-3.8-flash-high",
        "ag/gemini-3.7-flash-high",
        "ag/gemini-3.6-flash-high",
        "ag/gemini-3.1-pro-low",
        "ag/claude-sonnet-4-6",
        "ag/gpt-oss-120b-medium",
        "gemini-3.8-flash",
    ],
}


class ConvertView(ctk.CTkFrame):
    """Convert source content to editable Question objects entirely in V5."""

    def __init__(
        self,
        parent,
        *,
        on_navigate: Callable[[str], None] | None = None,
        on_add_questions: Callable[[list[Question], dict], None] | None = None,
        can_use_feature: Callable[..., bool] | None = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self._on_navigate = on_navigate
        self._on_add_questions = on_add_questions
        self._can_use_feature = can_use_feature
        self._questions: list[Question] = []
        self._meta: dict[str, str] = {"subject": "Toán", "grade": "12", "topic": ""}
        self._image_files: list[str] = []
        self._document_paths: list[str] = []
        self._temp_images: list[str] = []
        self._busy = False
        self._cancel = threading.Event()
        self._build()

    def _feature_allowed(self, feature: str, *, notify: bool = True) -> bool:
        if not callable(self._can_use_feature):
            return True
        try:
            return bool(self._can_use_feature(feature, notify=notify))
        except TypeError:
            return bool(self._can_use_feature(feature))

    def _build(self) -> None:
        self._build_header()

        settings = ctk.CTkFrame(self, fg_color=("white", "#162033"), corner_radius=8)
        settings.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(settings, text="AI Provider:", font=("Segoe UI", 11, "bold")).pack(
            side="left", padx=(12, 6), pady=8
        )
        self._provider_var = ctk.StringVar(value=self._detect_provider())
        ctk.CTkOptionMenu(
            settings,
            variable=self._provider_var,
            values=PROVIDERS,
            width=170,
            command=self._on_provider_change,
        ).pack(side="left", padx=(0, 8), pady=8)
        self._model_var = ctk.StringVar(value=MODELS[self._provider_var.get()])
        self._model_menu = ctk.CTkOptionMenu(
            settings,
            variable=self._model_var,
            values=self._model_options(self._provider_var.get()),
            width=210,
        )
        self._model_menu.pack(side="left", pady=8)
        self._status = ctk.CTkLabel(
            settings, text="Sẵn sàng", anchor="e", text_color="gray"
        )
        self._status.pack(side="right", fill="x", expand=True, padx=12)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=4)
        body.grid_columnconfigure(1, weight=5)
        body.grid_rowconfigure(0, weight=1)

        self._tabs = ctk.CTkTabview(body, corner_radius=8)
        self._tabs.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        for mode in (MODE_IMAGE, MODE_DOCUMENT, MODE_TEXT):
            self._tabs.add(mode)
        self._build_image_tab(self._tabs.tab(MODE_IMAGE))
        self._build_document_tab(self._tabs.tab(MODE_DOCUMENT))
        self._build_text_tab(self._tabs.tab(MODE_TEXT))

        self._build_result_panel(body)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(
            self, fg_color=("#1F497D", "#0B1F35"), corner_radius=10, height=64
        )
        header.pack(fill="x", pady=(0, 8))
        header.pack_propagate(False)
        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", padx=16, pady=9)
        ctk.CTkLabel(
            left, text="🔄  Convert", text_color="white", font=("Segoe UI", 18, "bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            left,
            text="Ảnh, PDF/Word/TeX/Text hoặc văn bản -> câu hỏi cấu trúc V5",
            text_color="#93C5FD",
            font=("Segoe UI", 10),
        ).pack(anchor="w")
        ctk.CTkButton(
            header,
            text="📋  Dán ảnh",
            width=112,
            height=32,
            fg_color="#10B981",
            hover_color="#059669",
            font=("Segoe UI", 12, "bold"),
            command=self._action_paste_image,
        ).pack(side="right", padx=(4, 12), pady=14)
        ctk.CTkButton(
            header,
            text="📂  Chọn file",
            width=112,
            height=32,
            font=("Segoe UI", 12, "bold"),
            command=self._action_pick_file,
        ).pack(side="right", padx=4, pady=14)

    def _build_image_tab(self, parent) -> None:
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        parent = scroll

        ctk.CTkLabel(
            parent,
            text="Chọn nhiều ảnh đề hoặc dán ảnh từ clipboard. AI Vision sẽ nhận diện câu hỏi.",
            anchor="w",
            justify="left",
            wraplength=320,
            text_color="gray",
        ).pack(fill="x", padx=10, pady=(10, 8))
        self._image_label = ctk.CTkLabel(
            parent,
            text="Chưa chọn ảnh.",
            anchor="w",
            justify="left",
            fg_color=("white", "#162033"),
            corner_radius=6,
            height=70,
            wraplength=320,
        )
        self._image_label.pack(fill="x", padx=10, pady=(0, 8))
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=4)
        ctk.CTkButton(row, text="Chọn ảnh", width=95, command=self._choose_images).pack(
            side="left", padx=(0, 5)
        )
        ctk.CTkButton(row, text="Dán ảnh", width=95, command=self._paste_image).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            row, text="Xóa", width=70, fg_color="#6B7280", command=self._clear_images
        ).pack(side="left", padx=5)
        self._image_qtype = self._build_extract_options(parent)
        ctk.CTkButton(
            parent,
            text="▶  Nhận diện ảnh",
            height=38,
            font=("Segoe UI", 12, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            command=self._start_image_conversion,
        ).pack(anchor="w", padx=10, pady=(12, 4))

    def _build_document_tab(self, parent) -> None:
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        parent = scroll

        ctk.CTkLabel(
            parent,
            text=(
                "Chọn cùng lúc PDF, Word, TeX hoặc Text. Cấu trúc app và LaTeX "
                "ex_test được nhận diện cục bộ; PDF scan dùng AI Vision theo trang."
            ),
            anchor="w",
            justify="left",
            wraplength=320,
            text_color="gray",
        ).pack(fill="x", padx=10, pady=(10, 8))
        file_row = ctk.CTkFrame(parent, fg_color="transparent")
        file_row.pack(fill="x", padx=10, pady=4)
        self._document_var = ctk.StringVar(value="(chưa chọn file)")
        ctk.CTkEntry(file_row, textvariable=self._document_var, state="readonly").pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )
        ctk.CTkButton(file_row, text="Chọn", width=70, command=self._choose_document).pack(
            side="left"
        )
        self._doc_info = ctk.CTkLabel(parent, text="", anchor="w", text_color="gray")
        self._doc_info.pack(fill="x", padx=10)
        options = ctk.CTkFrame(parent, fg_color="transparent")
        options.pack(fill="x", padx=10, pady=(12, 2))
        self._textlayer_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options, text="Ưu tiên text-layer PDF", variable=self._textlayer_var
        ).pack(anchor="w", pady=3)
        self._doc_qtype = self._build_extract_options(parent)
        pages = ctk.CTkFrame(parent, fg_color="transparent")
        pages.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(pages, text="Tối đa trang PDF:").pack(side="left")
        self._max_pages_var = ctk.StringVar(value="50")
        ctk.CTkEntry(pages, textvariable=self._max_pages_var, width=65).pack(
            side="left", padx=8
        )
        ctk.CTkButton(
            parent,
            text="▶  Trích xuất file",
            height=38,
            font=("Segoe UI", 12, "bold"),
            command=self._start_document_conversion,
        ).pack(anchor="w", padx=10, pady=(12, 4))

    def _build_text_tab(self, parent) -> None:
        catalog = chatbot_prompt_catalog()
        labels: list[str] = []
        self._chatbot_prompt_label_to_id = {}
        for item in catalog:
            family = str(item["family"])
            title = str(item["title"])
            short_title = title if len(title) <= 28 else f"{title[:25]}..."
            label = f"{family}: {short_title}"
            if label in self._chatbot_prompt_label_to_id:
                label = f"{label[:29]} #{len(labels) + 1}"
            labels.append(label)
            self._chatbot_prompt_label_to_id[label] = str(item["id"])
        self._chatbot_prompt_var = ctk.StringVar(value=labels[0] if labels else "")
        self._prompt_count_var = ctk.StringVar(value="10")
        self._prompt_topic_var = ctk.StringVar(value="")
        self._prompt_qtype_var = ctk.StringVar(value="auto")
        self._prompt_level_var = ctk.StringVar(value="auto")
        self._prompt_extra_var = ctk.StringVar(value="")

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        parent = scroll

        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=4, pady=(6, 8))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(2, weight=1)

        prompt_card = ctk.CTkFrame(container, fg_color=("white", "#162033"), corner_radius=10)
        prompt_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        prompt_card.grid_columnconfigure(0, weight=1)

        prompt_head = ctk.CTkFrame(prompt_card, fg_color="transparent")
        prompt_head.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        prompt_head.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkLabel(
            prompt_head,
            text="Prompt gợi ý ChatBotAI",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))
        ctk.CTkButton(
            prompt_head,
            text="GEM Master",
            height=28,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self._copy_gem_master_prompt,
        ).grid(row=1, column=0, padx=(0, 3), sticky="ew")
        ctk.CTkButton(
            prompt_head,
            text="Xem",
            height=28,
            fg_color="#6366F1",
            hover_color="#4F46E5",
            command=self._preview_chatbot_prompt,
        ).grid(row=1, column=1, padx=2, sticky="ew")
        ctk.CTkButton(
            prompt_head,
            text="Copy",
            height=28,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._copy_chatbot_prompt,
        ).grid(row=1, column=2, padx=(3, 0), sticky="ew")

        select_row = ctk.CTkFrame(prompt_card, fg_color="transparent")
        select_row.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 6))
        select_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(select_row, text="Mẫu", width=36, anchor="w").grid(row=0, column=0, padx=(0, 6))
        ctk.CTkOptionMenu(
            select_row,
            variable=self._chatbot_prompt_var,
            values=labels,
        ).grid(row=0, column=1, sticky="ew")

        form = ctk.CTkFrame(prompt_card, fg_color="transparent")
        form.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        form.grid_columnconfigure(1, weight=0)
        form.grid_columnconfigure(3, weight=1)
        form.grid_columnconfigure(5, weight=1)
        ctk.CTkLabel(form, text="Số").grid(row=0, column=0, padx=(0, 3), pady=(0, 4), sticky="w")
        ctk.CTkEntry(form, textvariable=self._prompt_count_var, width=46).grid(
            row=0, column=1, padx=(0, 5), pady=(0, 4), sticky="w"
        )
        ctk.CTkLabel(form, text="Loại").grid(row=0, column=2, padx=(0, 3), pady=(0, 4), sticky="w")
        ctk.CTkOptionMenu(
            form,
            variable=self._prompt_qtype_var,
            values=["auto", "MIX", "TN", "DS", "TLN", "TL", "DS/TLN", "TikZ"],
            width=76,
        ).grid(row=0, column=3, padx=(0, 5), pady=(0, 4), sticky="ew")
        ctk.CTkLabel(form, text="Mức").grid(row=0, column=4, padx=(0, 3), pady=(0, 4), sticky="w")
        ctk.CTkOptionMenu(
            form,
            variable=self._prompt_level_var,
            values=["auto", "NB", "TH", "VD", "VDC"],
            width=70,
        ).grid(row=0, column=5, pady=(0, 4), sticky="ew")

        ctk.CTkLabel(form, text="Chủ đề").grid(row=1, column=0, padx=(0, 3), sticky="w")
        ctk.CTkEntry(
            form,
            textvariable=self._prompt_topic_var,
            placeholder_text="vd: Hàm số, xác suất, hình không gian...",
        ).grid(row=1, column=1, columnspan=5, sticky="ew")

        ctk.CTkLabel(
            container,
            text=(
                "Cách dùng: chọn mẫu Gemini GEM / ChatGPT / DeepSeek -> Copy prompt -> dán sang chatbot -> "
                "dán kết quả dạng ===CAU=== hoặc LaTeX ex_test vào ô dưới. "
                "Có thể trộn cả hai cấu trúc; parser cục bộ không tốn API."
            ),
            anchor="w",
            justify="left",
            wraplength=320,
            text_color=("gray35", "gray70"),
            font=("Segoe UI", 10),
        ).grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self._text_input = ctk.CTkTextbox(container, height=190, wrap="word")
        self._text_input.grid(row=2, column=0, sticky="nsew", pady=(0, 8))

        buttons = ctk.CTkFrame(container, fg_color="transparent")
        buttons.grid(row=3, column=0, sticky="ew")
        buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            buttons,
            text="⚡ Nhận diện cục bộ",
            height=34,
            fg_color="#10B981",
            hover_color="#059669",
            font=("Segoe UI", 12, "bold"),
            command=self._parse_text_locally,
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        ctk.CTkButton(
            buttons,
            text="🤖 Chuẩn hóa bằng AI",
            height=34,
            fg_color="#A78BFA",
            hover_color="#8B5CF6",
            command=self._normalize_text_with_ai,
        ).grid(row=1, column=0, padx=(0, 4), sticky="ew")
        ctk.CTkButton(
            buttons,
            text="Sua prompt/TikZ",
            height=34,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self._rewrite_prompt_tikz_locally,
        ).grid(row=1, column=1, padx=(4, 0), sticky="ew")

    def _build_extract_options(self, parent) -> ctk.StringVar:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(10, 2))
        ctk.CTkLabel(row, text="Loại câu:").pack(side="left")
        qtype = ctk.StringVar(value="auto")
        ctk.CTkOptionMenu(row, variable=qtype, values=["auto", "TN", "DS", "TLN", "TL"], width=85).pack(
            side="left", padx=(6, 10)
        )
        solve = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(row, text="AI điền đáp án/lời giải", variable=solve).pack(
            side="left"
        )
        qtype._solve_var = solve  # type: ignore[attr-defined]
        return qtype

    def _build_result_panel(self, body) -> None:
        result = ctk.CTkFrame(body, fg_color=("white", "#162033"), corner_radius=8)
        result.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        result.grid_rowconfigure(1, weight=3)
        result.grid_rowconfigure(2, weight=2)
        result.grid_columnconfigure(0, weight=1)
        self._summary = ctk.CTkLabel(
            result,
            text="Kết quả: chưa có câu hỏi",
            anchor="w",
            font=("Segoe UI", 12, "bold"),
        )
        self._summary.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        table = ctk.CTkFrame(result, fg_color="transparent")
        table.grid(row=1, column=0, sticky="nsew", padx=10)
        table.grid_rowconfigure(0, weight=1)
        table.grid_rowconfigure(1, weight=0)
        table.grid_columnconfigure(0, weight=1)
        cols = ("no", "kind", "topic", "question")
        self._tree = ttk.Treeview(table, columns=cols, show="headings")
        for column, text, width, min_width, stretch, anchor in (
            ("no", "#", 42, 34, False, "center"),
            ("kind", "Loại/Mức", 92, 82, False, "center"),
            ("topic", "Chủ đề", 125, 92, True, "w"),
            ("question", "Nội dung", 280, 180, True, "w"),
        ):
            self._tree.heading(column, text=text)
            self._tree.column(
                column,
                width=width,
                minwidth=min_width,
                stretch=stretch,
                anchor=anchor,
            )
        try:
            from v5.tree_style import style_treeview

            style_treeview(self._tree)
        except Exception:
            pass
        scroll = ttk.Scrollbar(table, orient="vertical", command=self._tree.yview)
        hscroll = ttk.Scrollbar(table, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=scroll.set, xscrollcommand=hscroll.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")
        self._tree.bind("<Double-1>", self._edit_selected_question)

        self._output = ctk.CTkTextbox(result, wrap="word", height=150)
        self._output.grid(row=2, column=0, sticky="nsew", padx=10, pady=(8, 6))
        self._output.configure(state="disabled")

        actions = ctk.CTkFrame(result, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", padx=10, pady=(4, 10))
        actions.grid_columnconfigure((0, 1, 2), weight=1, uniform="convert_result_actions")
        self._copy_btn = ctk.CTkButton(actions, text="Copy Word", command=self._copy_output)
        self._copy_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=(0, 4))
        self._copy_latex_btn = ctk.CTkButton(
            actions, text="Copy LaTeX", command=self._copy_latex
        )
        self._copy_latex_btn.grid(row=0, column=1, sticky="ew", padx=4, pady=(0, 4))
        self._export_btn = ctk.CTkButton(actions, text="Xuất Word", command=self._export_word)
        self._export_btn.grid(row=0, column=2, sticky="ew", padx=(4, 0), pady=(0, 4))
        self._export_latex_btn = ctk.CTkButton(
            actions, text="Xuất LaTeX", command=self._export_latex
        )
        self._export_latex_btn.grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(4, 0))
        self._save_btn = ctk.CTkButton(actions, text="Lưu NHCH", command=self._save_local)
        self._save_btn.grid(row=1, column=1, sticky="ew", padx=4, pady=(4, 0))
        self._add_btn = ctk.CTkButton(
            actions, text="Thêm vào đề", fg_color="#10B981", command=self._add_to_exam
        )
        self._add_btn.grid(row=1, column=2, sticky="ew", padx=(4, 0), pady=(4, 0))
        self._set_result_actions(False)

    def _detect_provider(self) -> str:
        try:
            from services.key_manager import get_key_manager

            manager = get_key_manager()
            for provider in PROVIDERS:
                if manager.load(provider):
                    return provider
        except Exception:
            pass
        return "Google Gemini"

    def _on_provider_change(self, provider: str) -> None:
        values = self._model_options(provider)
        if hasattr(self, "_model_menu"):
            self._model_menu.configure(values=values)
        self._model_var.set(MODELS.get(provider, values[0]))

    @staticmethod
    def _model_options(provider: str) -> list[str]:
        return MODEL_OPTIONS.get(provider) or [MODELS.get(provider, "gemini-3.8-flash")]

    @staticmethod
    def _create_ai_service(provider: str, model: str, require_vision: bool = False):
        if require_vision and provider not in VISION_PROVIDERS:
            raise ValueError("Nhận diện ảnh/PDF scan cần Google Gemini hoặc Anthropic Claude.")
        from services.key_manager import get_key_manager
        from services.ai_service import create_ai_service
        from services.retry_service import split_keys

        key = get_key_manager().load(provider)
        if not key and provider != "9Router":
            raise ValueError(f"Chưa có API key cho {provider}. Hãy nhập key trong Cấu hình.")
        keys = (key if isinstance(key, list) else split_keys(key)) if key else ["dummy_key"]
        return create_ai_service(provider, keys, model)

    def _build_ai_service(self, require_vision: bool = False):
        return self._create_ai_service(
            self._provider_var.get(),
            self._model_var.get(),
            require_vision=require_vision,
        )

    def _action_paste_image(self) -> None:
        self.focus_image_mode()
        self._paste_image()

    def _action_pick_file(self) -> None:
        if self._tabs.get() == MODE_DOCUMENT:
            self._choose_document()
        else:
            self.focus_image_mode()
            self._choose_images()

    def _choose_images(self) -> None:
        selected = filedialog.askopenfilenames(
            parent=self,
            title="Chọn ảnh đề",
            filetypes=[("Ảnh", "*.png *.jpg *.jpeg *.bmp *.webp"), ("Tất cả", "*.*")],
        )
        if selected:
            self._image_files.extend(path for path in selected if path not in self._image_files)
            self._render_image_files()

    def _paste_image(self) -> None:
        try:
            from PIL import ImageGrab

            image = ImageGrab.grabclipboard()
            if image is None or not hasattr(image, "save"):
                raise ValueError("Clipboard không chứa ảnh.")
            temp = tempfile.NamedTemporaryFile(prefix="mea_v5_paste_", suffix=".png", delete=False)
            temp.close()
            image.save(temp.name, format="PNG")
            self._temp_images.append(temp.name)
            self._image_files.append(temp.name)
            self._render_image_files()
        except Exception as exc:
            messagebox.showerror("Không dán được ảnh", str(exc), parent=self)

    def _clear_images(self) -> None:
        self._image_files.clear()
        for filename in self._temp_images:
            try:
                Path(filename).unlink(missing_ok=True)
            except Exception:
                pass
        self._temp_images.clear()
        self._render_image_files()

    def _render_image_files(self) -> None:
        if not self._image_files:
            self._image_label.configure(text="Chưa chọn ảnh.")
            return
        names = [Path(path).name for path in self._image_files]
        suffix = "" if len(names) <= 3 else f"\n... và {len(names) - 3} ảnh khác"
        self._image_label.configure(text="\n".join(names[:3]) + suffix)

    def _choose_document(self) -> None:
        selected = filedialog.askopenfilenames(
            parent=self,
            title="Chọn PDF, Word, TeX hoặc Text",
            filetypes=[
                ("Tài liệu hỗ trợ", "*.pdf *.docx *.tex *.txt *.html *.htm"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx"),
                ("LaTeX", "*.tex"),
                ("Text", "*.txt *.html *.htm"),
            ],
        )
        if not selected:
            return
        self._document_paths = [str(path) for path in selected]
        paths = [Path(path) for path in self._document_paths]
        self._document_var.set(
            str(paths[0]) if len(paths) == 1 else f"{len(paths)} file đã chọn"
        )
        total_kb = sum(path.stat().st_size for path in paths) / 1024
        suffixes = ", ".join(sorted({path.suffix.upper()[1:] for path in paths}))
        text = f"{suffixes} - {total_kb:.0f} KB"
        if len(paths) > 1:
            text += f" - {len(paths)} file"
        pdf_paths = [path for path in paths if path.suffix.lower() == ".pdf"]
        if len(pdf_paths) == 1:
            try:
                import fitz

                document = fitz.open(str(pdf_paths[0]))
                text += f" - {len(document)} trang"
                document.close()
            except Exception:
                pass
        self._doc_info.configure(text=text)

    def _start_image_conversion(self) -> None:
        files = [path for path in self._image_files if Path(path).exists()]
        if not files:
            messagebox.showwarning("Thiếu ảnh", "Hãy chọn hoặc dán ít nhất một ảnh.", parent=self)
            return
        self._start_file_worker(
            files,
            qtype=self._image_qtype.get(),
            auto_solve=self._image_qtype._solve_var.get(),  # type: ignore[attr-defined]
            use_text_layer=False,
            max_pages=1,
        )

    def _start_document_conversion(self) -> None:
        files = [path for path in self._document_paths if Path(path).exists()]
        if not files:
            messagebox.showwarning(
                "Thiếu file", "Hãy chọn PDF, Word, TeX hoặc Text.", parent=self
            )
            return
        try:
            max_pages = max(1, int(self._max_pages_var.get()))
        except ValueError:
            max_pages = 50
        self._start_file_worker(
            files,
            qtype=self._doc_qtype.get(),
            auto_solve=self._doc_qtype._solve_var.get(),  # type: ignore[attr-defined]
            use_text_layer=self._textlayer_var.get(),
            max_pages=max_pages,
        )

    def _start_file_worker(
        self,
        files: list[str],
        *,
        qtype: str,
        auto_solve: bool,
        use_text_layer: bool,
        max_pages: int,
    ) -> None:
        if self._busy:
            return
        self._busy = True
        self._cancel.clear()
        self._status.configure(text="Đang trích xuất...", text_color="#3B82F6")
        provider = self._provider_var.get()
        model = self._model_var.get()

        def worker() -> None:
            try:
                from core.pdf_to_questions import pdf_or_image_to_questions
                from services.key_manager import get_key_manager
                from services.ai_service import create_ai_service
                from services.retry_service import split_keys

                service = None

                def get_service(require_vision: bool = False):
                    nonlocal service
                    if require_vision and provider not in VISION_PROVIDERS:
                        raise ValueError("Nhận diện ảnh/PDF scan cần Google Gemini hoặc Anthropic Claude.")
                    if service is None:
                        key = get_key_manager().load(provider)
                        if not key:
                            raise ValueError(f"Chưa có API key cho {provider}.")
                        keys = key if isinstance(key, list) else split_keys(key)
                        service = create_ai_service(provider, keys, model)
                    return service

                results = []
                for file_index, filename in enumerate(files, 1):
                    if self._cancel.is_set():
                        raise InterruptedError("Đã dừng")

                    def progress(current, total, label, prefix=file_index):
                        self._schedule(
                            lambda: self._status.configure(
                                text=f"File {prefix}/{len(files)} - {label}",
                                text_color="#3B82F6",
                            )
                        )

                    result = pdf_or_image_to_questions(
                        filename,
                        ai_vision_call=lambda prompt, image: get_service(True).generate_with_image(prompt, image),
                        ai_text_call=(lambda prompt: get_service(False).generate(prompt)) if auto_solve else None,
                        auto_solve=auto_solve,
                        progress_cb=progress,
                        qtype_filter=qtype,
                        use_text_layer=use_text_layer,
                        max_pages=max_pages,
                    )
                    results.append(result)
                combined = combine_results(results)
                self._schedule(lambda: self._finish_conversion(combined, None))
            except InterruptedError as exc:
                self._schedule(lambda: self._finish_conversion(None, str(exc)))
            except Exception as exc:
                    self._schedule(lambda: self._finish_conversion(None, str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _selected_chatbot_prompt_id(self) -> str:
        var = getattr(self, "_chatbot_prompt_var", None)
        label = var.get() if var is not None else ""
        mapping = getattr(self, "_chatbot_prompt_label_to_id", {})
        return mapping.get(label) or next(iter(mapping.values()), "gemini_gem_master")

    def _build_selected_chatbot_prompt(self) -> str:
        meta = self._current_meta()
        topic = self._prompt_topic_var.get().strip() or meta.get("topic", "")
        return build_chatbot_prompt(
            self._selected_chatbot_prompt_id(),
            subject=meta.get("subject", "Toán"),
            grade=("1-12" if self._selected_chatbot_prompt_id() == "gemini_gem_master" else str(meta.get("grade", "12"))),
            topic=topic,
            count=self._prompt_count_var.get(),
            qtype=self._prompt_qtype_var.get(),
            level=self._prompt_level_var.get(),
            extra=self._prompt_extra_var.get(),
        )

    def _copy_chatbot_prompt(self) -> None:
        prompt = self._build_selected_chatbot_prompt()
        self.clipboard_clear()
        self.clipboard_append(prompt)
        self._status.configure(text="Đã copy prompt ChatBotAI. Dán vào Gemini/ChatGPT/DeepSeek rồi paste kết quả về đây.", text_color="#10B981")
        self._toast("Đã copy prompt ChatBotAI.", "success")

    def _copy_gem_master_prompt(self) -> None:
        prompt = build_chatbot_prompt(
            "gemini_gem_master",
            subject=self._current_meta().get("subject", "ToÃ¡n"),
            grade="1-12",
            topic=self._prompt_topic_var.get().strip(),
            count=self._prompt_count_var.get(),
            qtype=self._prompt_qtype_var.get(),
            level=self._prompt_level_var.get(),
            extra=self._prompt_extra_var.get(),
        )
        self.clipboard_clear()
        self.clipboard_append(prompt)
        self._status.configure(text="Da copy GEM Master prompt tong hop.", text_color="#10B981")
        self._toast("Da copy GEM Master prompt.", "success")

    def _preview_chatbot_prompt(self) -> None:
        try:
            from v5.variant_dialog import PromptPreviewDialog

            PromptPreviewDialog(
                self.winfo_toplevel(),
                self._build_selected_chatbot_prompt(),
                title="Prompt ChatBotAI tạo câu hỏi",
                intro=(
                    "Bạn có thể sửa prompt trước khi copy sang Gemini GEM, ChatGPT hoặc DeepSeek. "
                    "Kết quả trả về dán lại vào ô AI Text bên dưới."
                ),
            )
        except TypeError:
            from v5.variant_dialog import PromptPreviewDialog

            PromptPreviewDialog(self.winfo_toplevel(), self._build_selected_chatbot_prompt())
        except Exception as exc:
            messagebox.showerror("Không mở được prompt", str(exc), parent=self)

    def _parse_text_locally(self) -> None:
        text = self._text_input.get("1.0", "end").strip()
        questions = parse_text_questions(text)
        if not questions:
            messagebox.showinfo(
                "Chưa nhận diện được",
                "Không tìm thấy câu hỏi. Có thể dùng nút Chuẩn hóa bằng AI.",
                parent=self,
            )
            return
        self._finish_conversion({"questions": questions, "meta": self._current_meta(), "warnings": []}, None)

    def _rewrite_prompt_tikz_locally(self) -> None:
        raw = self._text_input.get("1.0", "end").strip()
        if not raw:
            raw = self._build_selected_chatbot_prompt()
        rewritten = rewrite_prompt_and_tikz_text(raw)
        self._text_input.delete("1.0", "end")
        self._text_input.insert("1.0", rewritten)
        self._status.configure(text="Da tu dong viet lai prompt va lam sach TikZ.", text_color="#10B981")
        self._toast("Da sua prompt/TikZ cuc bo.", "success")

    def _normalize_text_with_ai(self) -> None:
        raw = self._text_input.get("1.0", "end").strip()
        if not raw:
            messagebox.showwarning("Thiếu văn bản", "Hãy dán nội dung cần chuyển đổi.", parent=self)
            return
        if self._busy:
            return
        self._busy = True
        self._status.configure(text="AI đang chuẩn hóa văn bản...", text_color="#3B82F6")
        provider = self._provider_var.get()
        model = self._model_var.get()

        def worker() -> None:
            try:
                service = self._create_ai_service(provider, model)
                response = service.generate(build_text_normalize_prompt(raw))
                questions = parse_text_questions(response)
                if not questions:
                    raise ValueError("AI không trả về cấu trúc câu hỏi đọc được.")
                result = {"questions": questions, "meta": self._current_meta(), "warnings": []}
                self._schedule(lambda: self._finish_conversion(result, None))
            except Exception as exc:
                self._schedule(lambda: self._finish_conversion(None, str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _current_meta(self) -> dict[str, str]:
        try:
            from v5 import settings_store

            settings = settings_store.load()
            return {
                "subject": settings.get("subject", "Toán"),
                "grade": str(settings.get("grade", "12")),
                "topic": "",
            }
        except Exception:
            return {"subject": "Toán", "grade": "12", "topic": ""}

    def _finish_conversion(self, result, error: str | None) -> None:
        self._busy = False
        if error:
            self._status.configure(text=f"Lỗi: {error[:70]}", text_color="#EF4444")
            messagebox.showerror("Lỗi Convert V5", error, parent=self)
            return
        self._questions = list(result.get("questions", []) or [])
        self._meta = result.get("meta", {}) or self._current_meta()
        warnings = result.get("warnings", []) or []
        self._render_results()
        if not self._questions:
            detail = "\n".join(str(warning) for warning in warnings) or "Không trích được câu hỏi nào."
            self._status.configure(text="Không có câu hỏi", text_color="#F59E0B")
            messagebox.showwarning("Kết quả trống", detail[:500], parent=self)
        elif warnings:
            self._status.configure(
                text=f"Đã trích {len(self._questions)} câu, có {len(warnings)} cảnh báo",
                text_color="#F59E0B",
            )
        else:
            self._status.configure(
                text=f"Đã trích {len(self._questions)} câu", text_color="#10B981"
            )

    def _render_results(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for index, question in enumerate(self._questions, 1):
            preview = (question.question or "").replace("\n", " ")[:100]
            qtype = (question.qtype or "").strip()
            level = (question.level or "").strip()
            kind = f"{qtype}/{level}" if qtype and level else (qtype or level or "-")
            self._tree.insert(
                "",
                "end",
                values=(index, kind, question.topic, preview),
            )
        stats = {
            code: sum(1 for question in self._questions if question.qtype == code)
            for code in ("TN", "DS", "TLN", "TL")
        }
        self._summary.configure(
            text=(
                f"Kết quả: {len(self._questions)} câu | TN {stats['TN']} | DS {stats['DS']} | "
                f"TLN {stats['TLN']} | TL {stats['TL']}"
            )
        )
        try:
            from export.question_formatter import format_questions

            output = format_questions(self._questions, include_solution=True)
        except Exception:
            output = "\n\n".join(question.question for question in self._questions)
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.insert("1.0", output)
        self._output.configure(state="disabled")
        self._set_result_actions(bool(self._questions))

    _display_results = _render_results

    def _set_result_actions(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for button in (
            self._copy_btn,
            self._copy_latex_btn,
            self._export_btn,
            self._export_latex_btn,
            self._save_btn,
            self._add_btn,
        ):
            button.configure(state=state)

    def _copy_output(self) -> None:
        output = self._output.get("1.0", "end").strip()
        if output:
            self.clipboard_clear()
            self.clipboard_append(output)
            self._toast("Đã copy kết quả Convert.", "success")

    def _copy_latex(self) -> None:
        if not self._questions:
            return
        from export.latex_exporter import format_questions_ex_test

        source = format_questions_ex_test(self._questions, include_solution=True)
        self.clipboard_clear()
        self.clipboard_append(source)
        self._toast("Đã copy cấu trúc LaTeX ex_test.", "success")

    def _export_word(self) -> None:
        if not self._questions:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Xuất câu hỏi Convert",
            defaultextension=".docx",
            initialfile="convert_v5.docx",
            filetypes=[("Word", "*.docx")],
        )
        if not path:
            return
        try:
            from export.word_exporter import export_to_word
            from config import is_word_auto_convert_tables_enabled

            exam = ExamData(
                exam_title="CÂU HỎI CHUYỂN ĐỔI V5",
                subject=self._meta.get("subject", "Toán"),
                grade=str(self._meta.get("grade", "12")),
                semester="",
                year="",
                time="",
                questions=self._questions,
            )
            export_to_word(
                exam,
                path,
                include_solution=True,
                auto_convert_tables=is_word_auto_convert_tables_enabled(),
            )
            self._toast(f"Đã xuất {len(self._questions)} câu ra Word.", "success")
        except Exception as exc:
            messagebox.showerror("Lỗi xuất Word", str(exc), parent=self)

    def _export_latex(self) -> None:
        if not self._questions:
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Xuất câu hỏi Convert sang LaTeX",
            defaultextension=".tex",
            initialfile="convert_v5.tex",
            filetypes=[("LaTeX", "*.tex")],
        )
        if not path:
            return
        try:
            from export.latex_exporter import export_to_latex

            export_to_latex(self._questions, path, include_solution=True)
            self._toast(f"Đã xuất {len(self._questions)} câu ra LaTeX.", "success")
        except Exception as exc:
            messagebox.showerror("Lỗi xuất LaTeX", str(exc), parent=self)

    def _save_local(self) -> None:
        if not self._questions:
            return
        try:
            grade = str(self._meta.get("grade", "12"))
            assign_ids_for_save(self._questions, grade)
            from storage.database import save_questions

            count = save_questions(
                self._questions,
                subject=self._meta.get("subject", "Toán"),
                grade=grade,
                source="convert_v5",
            )
            self._toast(f"Đã lưu {count} câu vào NHCH local.", "success")
        except Exception as exc:
            messagebox.showerror("Lỗi lưu NHCH", str(exc), parent=self)

    def _add_to_exam(self) -> None:
        if self._questions and callable(self._on_add_questions):
            self._on_add_questions(self._questions, self._meta)
        elif self._questions:
            messagebox.showinfo("Thông báo", "Không thể mở đề hiện tại.", parent=self)

    def _edit_selected_question(self, _event=None) -> None:
        selected = self._tree.selection()
        if not selected:
            return
        index = int(self._tree.item(selected[0], "values")[0]) - 1
        question = self._questions[index]

        def on_save(updated: Question) -> None:
            self._questions[index] = updated
            self._render_results()

        try:
            from v5.edit_question import EditQuestionDialogCTk

            EditQuestionDialogCTk(
                self.winfo_toplevel(),
                question,
                on_save_cb=on_save,
                get_ai_call=(lambda: self._build_ai_service().generate)
                if self._feature_allowed("ai_review", notify=False) else None,
                subject=self._meta.get("subject", "Toán"),
                grade=str(self._meta.get("grade", "12")),
            )
        except Exception as exc:
            messagebox.showerror("Lỗi sửa câu hỏi", str(exc), parent=self)

    def focus_image_mode(self) -> None:
        self._tabs.set(MODE_IMAGE)

    def focus_pdf_mode(self) -> None:
        self._tabs.set(MODE_DOCUMENT)

    def focus_ai_text_mode(self) -> None:
        self._tabs.set(MODE_TEXT)

    def _schedule(self, callback) -> None:
        from v5.safe_ui import safe_after

        safe_after(self, 0, callback)

    def _toast(self, text: str, kind: str = "info") -> None:
        try:
            from v5.toast import show_toast

            show_toast(self.winfo_toplevel(), text, kind=kind, duration=4)
        except Exception:
            pass
