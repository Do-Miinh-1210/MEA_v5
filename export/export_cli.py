"""
export/export_cli.py — CLI bridge for MEA Word Export.
Allows calling export_to_word directly from command line or external processes (C#, Add-In, scripts).

Usage:
    py -m export.export_cli --text-file input.txt -o output.docx [--subject Toan] [--grade 12]
    py -m export.export_cli --json-file input.json -o output.docx
    py -m export.export_cli --raw "Câu 1. ..." -o output.docx
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.models import ExamData, Question
from core.exam_file_loader import parse_questions_from_text
from export.word_exporter import export_to_word


def dict_to_question(d: dict) -> Question:
    """Chuyển đổi linh hoạt từ cả định dạng Python Question dict và C# QuestionItem dict."""
    if "qtype" in d and "question" in d:
        return Question.from_dict(d)

    qtype_raw = d.get("QuestionType") or d.get("qtype") or "TN"
    qtype_map = {
        "MultipleChoice4": "TN",
        "TrueFalse4": "DS",
        "ShortAnswer": "TLN",
        "Essay": "TL",
        "TN": "TN",
        "DS": "DS",
        "TLN": "TLN",
        "TL": "TL",
    }
    qtype = qtype_map.get(qtype_raw, "TN")
    question_text = d.get("Content") or d.get("question") or ""
    solution_text = d.get("Explanation") or d.get("solution") or ""
    ans_text = d.get("CorrectAnswer") or d.get("answer") or ""
    level = d.get("Level") or d.get("level") or "NB"
    topic = d.get("Topic") or d.get("topic") or ""

    opts = d.get("Options") or d.get("options") or {}
    items = {}
    answers = {}
    item_solutions = {}

    if qtype == "DS":
        items = {str(k).lower(): str(v) for k, v in opts.items()}
        raw_answers = d.get("Answers") or d.get("answers")
        if isinstance(raw_answers, dict):
            answers = raw_answers
        elif ans_text:
            import re
            for k in "abcd":
                m = re.search(rf"\b{k}\s*[\)\:\.]\s*([ĐDTS])", ans_text, re.IGNORECASE)
                if m:
                    ch = m.group(1).upper()
                    answers[k] = (ch in ("Đ", "D", "T"))

    parsed_opts = {str(k).upper(): str(v) for k, v in opts.items()} if qtype == "TN" else {}

    # Trích xuất hình ảnh từ Images list (C# QuestionItem.Images) hoặc AttachedImagePath
    images_list = d.get("Images") or d.get("images") or []
    q_img = ""
    if isinstance(images_list, list) and images_list:
        parsed_paths = []
        import tempfile
        import uuid
        import base64
        for img_item in images_list:
            if not img_item:
                continue
            str_item = str(img_item)
            if str_item.startswith("data:image") or (len(str_item) > 200 and not os.path.exists(str_item)):
                b64_data = str_item
                if "," in b64_data:
                    b64_data = b64_data.split(",", 1)[1]
                try:
                    raw_bytes = base64.b64decode(b64_data)
                    tmp_img = Path(tempfile.gettempdir()) / f"mea_img_{uuid.uuid4().hex}.png"
                    tmp_img.write_bytes(raw_bytes)
                    parsed_paths.append(str(tmp_img))
                except Exception:
                    pass
            elif os.path.exists(str_item):
                parsed_paths.append(str_item)
        if parsed_paths:
            q_img = "|".join(parsed_paths)
    if not q_img:
        q_img = d.get("AttachedImagePath") or d.get("question_image") or ""

    if not q_img and question_text:
        import re
        img_tags = re.findall(r'\[(?:HINH_ANH|IMAGE|ANH|H[ÌI]NH(?:\s*\d+)?):\s*([^\]]+)\]', question_text, re.IGNORECASE)
        found = [p.strip() for p in img_tags if os.path.exists(p.strip())]
        if found:
            q_img = "|".join(found)

    return Question(
        qtype=qtype,
        level=level,
        topic=topic,
        question=question_text,
        solution=solution_text,
        options=parsed_opts,
        answer=ans_text,
        items=items,
        answers=answers,
        item_solutions=item_solutions,
        question_image=q_img,
    )


def main():
    parser = argparse.ArgumentParser(description="MatrixExamAI CLI Word Exporter")
    parser.add_argument("-o", "--output", required=True, help="Path to output .docx file")
    parser.add_argument("--json-file", help="Path to JSON file containing ExamData or questions")
    parser.add_argument("--text-file", help="Path to raw text file containing exam questions")
    parser.add_argument("--raw", help="Raw string containing exam questions")
    parser.add_argument("--subject", default="Toán", help="Subject name (default: Toán)")
    parser.add_argument("--grade", default="12", help="Grade level (default: 12)")
    parser.add_argument("--exam-title", default="ĐỀ KIỂM TRA CHÍNH THỨC", help="Exam Title")
    parser.add_argument("--school", default="SỞ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG THPT ........................", help="School Name")
    parser.add_argument("--no-solution", action="store_true", help="Omit solution in output")
    parser.add_argument("--ma-de", default="101", help="Exam code (default: 101)")

    args = parser.parse_args()

    questions = []
    subject = args.subject
    grade = str(args.grade)
    exam_title = args.exam_title
    school = args.school
    ma_de = args.ma_de
    include_solution = not args.no_solution

    if args.json_file:
        with open(args.json_file, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            if "questions" in data:
                subject = data.get("subject", subject)
                grade = str(data.get("grade", grade))
                exam_title = data.get("exam_title", exam_title)
                school = data.get("school", school)
                ma_de = data.get("ma_de", ma_de)
                for q_dict in data["questions"]:
                    questions.append(dict_to_question(q_dict))
            elif isinstance(data, list):
                for q_dict in data:
                    questions.append(dict_to_question(q_dict))
                if data:
                    first_item = data[0]
                    if isinstance(first_item, dict):
                        sub_val = first_item.get("Subject") or first_item.get("subject")
                        if sub_val:
                            subject = sub_val
                        grd_val = first_item.get("Grade") or first_item.get("grade")
                        if grd_val:
                            grade = str(grd_val)

    elif args.text_file:
        with open(args.text_file, "r", encoding="utf-8-sig") as f:
            raw_text = f.read()
        qs, _ = parse_questions_from_text(raw_text)
        questions = qs

    elif args.raw:
        qs, _ = parse_questions_from_text(args.raw)
        questions = qs

    else:
        # Read from stdin
        raw_text = sys.stdin.read()
        if raw_text.strip():
            qs, _ = parse_questions_from_text(raw_text)
            questions = qs

    if not questions:
        sys.stderr.write("Error: No questions found to export.\n")
        sys.exit(1)

    exam = ExamData(
        exam_title=exam_title,
        subject=subject,
        grade=grade,
        semester="1",
        year="2025-2026",
        time="90 phút",
        questions=questions,
        ma_de=ma_de,
        school=school
    )

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    export_to_word(
        exam,
        str(out_path),
        include_solution=include_solution,
        auto_convert_tables=True
    )
    print(f"SUCCESS: Exported {len(questions)} questions to {out_path}")


if __name__ == "__main__":
    main()
