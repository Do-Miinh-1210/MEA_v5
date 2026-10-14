"""
omr_exam/exam_shuffler.py — Engine trộn đề thi nâng cao:
- 3 Chế độ trộn: Trộn cả câu & phương án / Chỉ trộn câu / Chỉ trộn phương án.
- Smart Fixed Options: Tự động phát hiện và ghim phương án phụ thuộc ("Tất cả...", "Cả A và B...", "Không có...") ở vị trí D.
- Pin Questions: Cố định vị trí các câu hỏi chỉ định không bị xáo trộn.
- Tùy chỉnh danh sách mã đề (Custom codes hoặc start_code + num_codes).
- Theo dõi toàn diện ma trận hoán vị câu hỏi và ma trận hoán vị phương án (Phiếu soi câu).
"""
from __future__ import annotations
import random
import copy
import re
from typing import List, Dict, Set, Optional, Any
from omr_exam.models import ExamSection, ExamQuestion, OptionItem, ShuffledExamCode


def is_dependent_option_text(text: str) -> bool:
    """Kiểm tra xem nội dung phương án có phải là phương án phụ thuộc không.
    (Ví dụ: 'Cả A và B đều đúng', 'Tất cả các đáp án trên', 'Không có đáp án nào đúng'...)
    """
    clean = re.sub(r"\s+", " ", (text or "").strip().lower()).rstrip(".,:;")
    patterns = [
        r"^(cả\s+[a-d]\s+(và|và\s+cả|đều)\s+[a-d])",
        r"^(cả\s+[a-d]\s*,\s*[a-d])",
        r"^(tất cả\s+(các\s+)?(đáp án|phương án|ý|câu|lựa chọn)\s*(trên|đều đúng|đều sai)?)",
        r"^(các\s+(đáp án|phương án|ý)\s+trên\s+đều\s+(đúng|sai))",
        r"^(không\s+có\s+(đáp án|phương án|câu|lựa chọn)\s*(nào)?\s*(đúng|trên|chính xác)?)",
        r"^(cả\s+\d+\s+(đáp án|phương án|lựa chọn))",
        r"^(all of the above|none of the above|both [a-d] and [a-d])",
    ]
    for pat in patterns:
        if re.search(pat, clean):
            return True
    return False


def _shuffle_with_pinned(
    items: List[Any],
    pinned_indices: Set[int],
    rng: random.Random
) -> List[Any]:
    """Xáo trộn danh sách items nhưng giữ nguyên vị trí tuyệt đối của các item có index thuộc pinned_indices."""
    if not items or not pinned_indices:
        shuffled = list(items)
        rng.shuffle(shuffled)
        return shuffled
        
    n = len(items)
    res: List[Optional[Any]] = [None] * n
    unpinned_items = []
    unpinned_positions = []
    
    for pos, item in enumerate(items):
        idx = getattr(item, "index", pos + 1)
        if idx in pinned_indices:
            res[pos] = item
        else:
            unpinned_items.append(item)
            unpinned_positions.append(pos)
            
    rng.shuffle(unpinned_items)
    for pos, item in zip(unpinned_positions, unpinned_items):
        res[pos] = item
        
    return [x for x in res if x is not None]


def shuffle_exam(
    sections: List[ExamSection],
    num_codes: int = 4,
    start_code: int = 101,
    custom_codes: Optional[List[str]] = None,
    shuffle_mode: str = "both",  # "both", "questions_only", "options_only"
    auto_pin_dependent_options: bool = True,
    pinned_question_indices: Optional[Set[int]] = None,
    seed: int | None = None
) -> List[ShuffledExamCode]:
    """
    Tạo danh sách các mã đề thi đã được xáo trộn câu hỏi và phương án.
    Bảo đảm:
    - 3 Chế độ: 'both' (câu + đ/a), 'questions_only' (chỉ câu), 'options_only' (chỉ đ/a).
    - Cố định câu hỏi chỉ định qua pinned_question_indices.
    - Cố định phương án phụ thuộc ("Tất cả...", "Cả A và B...") ở vị trí cuối cùng (D).
    - Đáp án đúng được cập nhật chính xác theo nhãn mới (A/B/C/D).
    - Câu tự luận giữ nguyên thứ tự hoặc xếp sau phần trắc nghiệm.
    """
    result_codes: List[ShuffledExamCode] = []
    labels = ["A", "B", "C", "D"]
    pinned_set = set(pinned_question_indices or [])
    
    # Xác định danh sách mã đề
    if custom_codes and len(custom_codes) > 0:
        codes = [str(c).strip() for c in custom_codes if str(c).strip()]
    else:
        codes = [str(start_code + i) for i in range(num_codes)]
        
    for i, code_str in enumerate(codes):
        # Tạo seed ổn định từ mã đề để lặp lại được
        digits = re.sub(r"\D", "", code_str)
        code_seed = int(digits) if digits else (abs(hash(code_str)) % 100000)
        rng = random.Random(code_seed if seed is None else (seed + i))
        
        shuffled_sections: List[ExamSection] = []
        answer_key: Dict[int, str] = {}
        question_map: Dict[int, int] = {}
        option_map: Dict[int, Dict[str, str]] = {}
        
        global_q_index = 1
        
        for orig_sec in sections:
            sec_copy = ExamSection(title=orig_sec.title, questions=[])
            
            # Tách riêng câu trắc nghiệm và câu tự luận
            tn_questions = [q for q in orig_sec.questions if q.qtype == "TN"]
            tl_questions = [q for q in orig_sec.questions if q.qtype == "TL"]
            
            # 1. Trộn thứ tự câu hỏi trắc nghiệm
            if shuffle_mode in ("both", "questions_only"):
                shuffled_tn = _shuffle_with_pinned(
                    copy.deepcopy(tn_questions),
                    pinned_set,
                    rng
                )
            else:
                shuffled_tn = copy.deepcopy(tn_questions)
                
            # 2. Xử lý từng câu trắc nghiệm
            for q in shuffled_tn:
                orig_index = q.index
                q.index = global_q_index
                question_map[global_q_index] = orig_index
                
                # Trộn các phương án A, B, C, D
                if len(q.options) >= 2:
                    # Ghi nhớ đáp án đúng cũ & nội dung
                    correct_text = ""
                    orig_opts_by_label = {opt.label: opt for opt in q.options}
                    for opt in q.options:
                        if opt.is_correct or opt.label == q.correct_label:
                            correct_text = opt.text
                            break
                            
                    if shuffle_mode in ("both", "options_only"):
                        # Kiểm tra phương án phụ thuộc ("Tất cả...", "Cả A và B...")
                        dependent_opt = None
                        shufflable_opts = []
                        for opt in q.options:
                            if auto_pin_dependent_options and is_dependent_option_text(opt.text) and dependent_opt is None:
                                dependent_opt = opt
                            else:
                                shufflable_opts.append(opt)
                                
                        # Đảo các phương án được phép đảo
                        rng.shuffle(shufflable_opts)
                        
                        # Nếu có phương án phụ thuộc, ghép nó vào cuối cùng (vị trí D)
                        if dependent_opt is not None:
                            final_opts = shufflable_opts + [dependent_opt]
                        else:
                            final_opts = shufflable_opts
                    else:
                        final_opts = list(q.options)
                        
                    # Gán lại nhãn A, B, C, D theo thứ tự mới & theo dõi hoán vị
                    new_options = []
                    new_correct_label = ""
                    q_opt_perm: Dict[str, str] = {}
                    
                    for idx, opt in enumerate(final_opts):
                        new_lbl = labels[idx] if idx < len(labels) else f"({idx+1})"
                        orig_lbl = opt.label
                        q_opt_perm[new_lbl] = orig_lbl  # Ý mới này lấy từ ý gốc nào
                        
                        is_corr = (opt.text == correct_text) if correct_text else opt.is_correct
                        new_opt = OptionItem(
                            label=new_lbl,
                            text=opt.text,
                            is_correct=is_corr,
                            xml_content=opt.xml_content
                        )
                        new_options.append(new_opt)
                        if is_corr:
                            new_correct_label = new_lbl
                            
                    q.options = new_options
                    q.correct_label = new_correct_label
                    if new_correct_label:
                        answer_key[global_q_index] = new_correct_label
                    option_map[global_q_index] = q_opt_perm
                else:
                    if q.correct_label:
                        answer_key[global_q_index] = q.correct_label
                        
                sec_copy.questions.append(q)
                global_q_index += 1
                
            # 3. Câu tự luận: giữ nguyên hoặc thêm vào sau phần trắc nghiệm
            for q_tl in copy.deepcopy(tl_questions):
                orig_index = q_tl.index
                q_tl.index = global_q_index
                question_map[global_q_index] = orig_index
                sec_copy.questions.append(q_tl)
                global_q_index += 1
                
            shuffled_sections.append(sec_copy)
            
        shuffled_exam = ShuffledExamCode(
            code=code_str,
            sections=shuffled_sections,
            answer_key=answer_key,
            question_map=question_map,
            option_map=option_map
        )
        result_codes.append(shuffled_exam)
        
    return result_codes
