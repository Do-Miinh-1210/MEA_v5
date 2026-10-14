# Bộ Prompt Chatbot Cho MatrixExamAI

Thư mục này chứa các prompt copy/paste dùng ngay để training GEM/Gemini hoặc dán vào chatbot ngoài app.

## Cách dùng nhanh

1. Dùng `00_PROMPT_GEM_TONG_HOP.md` làm prompt hệ thống cho GEM.
2. Khi cần một tác vụ cụ thể, copy thêm prompt tương ứng:
   - `01_PROMPT_TAO_CAU_HOI_CHUAN_APP.md`: tạo câu hỏi đúng khung app.
   - `02_PROMPT_TAO_DE_TU_MA_TRAN.md`: tạo đề từ ma trận/yêu cầu.
   - `03_PROMPT_VE_HINH_TIKZ.md`: vẽ hình TikZ.
   - `04_PROMPT_TAO_DE_TUONG_TU.md`: tạo đề tương tự từ file/ảnh/đề gốc.
   - `05_PROMPT_SMART_PROMPT_MA_TRAN.md`: chuyển yêu cầu tự nhiên thành ma trận.
   - `06_PROMPT_QC_REVIEW_FIX.md`: kiểm tra và sửa câu hỏi.
   - `07_PROMPT_OCR_IMPORT_WORD.md`: OCR/chuẩn hóa đề từ ảnh/PDF/Word.
   - `08_PROMPT_OVERLEAF_TIKZ.md`: tạo code TikZ dễ render trên Overleaf.
   - `09_PROMPT_VIET_YEU_CAU_CAI_TIEN_APP.md`: viết yêu cầu cải tiến app thành đặc tả triển khai.
   - `99_CHECKLIST_DINH_DANG_APP.md`: checklist format của app.

## Nguyên tắc chung

- Output câu hỏi cho app phải dùng khung `===CAU=== ... ===KETCAU===`.
- Công thức toán dùng `${...}`.
- Không dùng `$$...$$`, `\(...\)`, `\[...\]`.
- TikZ phải bắt đầu bằng `\begin{tikzpicture}` và kết thúc bằng `\end{tikzpicture}`.
- Không bọc output bằng markdown fence ``` khi app cần import trực tiếp.
