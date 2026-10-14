"""Business helpers for the native V5 Convert view."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from core.models import Question


_BLOCK_RE = re.compile(
    r"===\s*CAU\s*===.*?===\s*KETCAU\s*===",
    re.DOTALL | re.IGNORECASE,
)


@dataclass(frozen=True)
class ChatbotPromptTemplate:
    """A reusable prompt suggestion for external ChatBotAI workflows."""

    id: str
    family: str
    title: str
    description: str
    provider_hint: str
    default_qtype: str
    default_level: str
    instruction: str
    emphasis: tuple[str, ...]

    @property
    def label(self) -> str:
        return f"{self.family} - {self.title}"


_APP_BLOCK_RULES = """\
ĐỊNH DẠNG BẮT BUỘC CHO MATRIXEXAMAI:
- Chỉ trả về các khối ===CAU=== ... ===KETCAU===, không thêm lời chào, markdown hay giải thích ngoài khối.
- CẤM TUYỆT ĐỐI CHÈN NGUỒN / CITATION: Tuyệt đối không chèn thẻ trích dẫn như [cite: ...], [source: ...], [1], [2].
- Công thức toán đặt trong ${...}. Không dùng $$...$$, \\(...\\), \\[...\\].
- Không dùng ký hiệu toán Unicode trực tiếp như ≤, ≥, ≠, √, π; hãy viết bằng LaTeX.
- Bảng số liệu: Dùng định dạng bảng Markdown (| Cột 1 | Cột 2 |\\n| --- | --- |) hoặc LaTeX \\begin{tabular}{...}...\\end{tabular}.
- Nếu có hình, chèn mã TikZ thuần trong NOIDUNG hoặc LOIGIAI, bắt đầu bằng \\begin{tikzpicture} và kết thúc bằng \\end{tikzpicture}.

Mẫu TN:
===CAU===
LOAI: TN
MUCDO: NB | TH | VD | VDC
CHUONG: <chủ đề>
NOIDUNG: <nội dung câu hỏi>
A: <phương án A>
B: <phương án B>
C: <phương án C>
D: <phương án D>
DAPAN: <A/B/C/D>
LOIGIAI: <lời giải ngắn gọn, đúng toán học>
===KETCAU===

Mẫu DS:
===CAU===
LOAI: DS
MUCDO: NB | TH | VD | VDC
CHUONG: <chủ đề>
NOIDUNG: <tình huống chung>
a: <mệnh đề a>
b: <mệnh đề b>
c: <mệnh đề c>
d: <mệnh đề d>
DAPAN: a=D,b=S,c=D,d=S
LOIGIAI: a. Đúng. Vì ...
b. Sai. Vì ...
c. Đúng. Vì ...
d. Sai. Vì ...
===KETCAU===

Mẫu TLN:
===CAU===
LOAI: TLN
MUCDO: NB | TH | VD | VDC
CHUONG: <chủ đề>
DIEM: 0.5
NOIDUNG: <bài toán đầy đủ>
DAPAN: <số ngắn, dùng dấu phẩy thập phân kiểu Việt Nam nếu cần>
LOIGIAI: <lời giải ngắn gọn nhưng đủ để kiểm chứng>
===KETCAU===

Mẫu TL:
===CAU===
LOAI: TL
MUCDO: NB | TH | VD | VDC
CHUONG: <chủ đề>
DIEM: 1.0
NOIDUNG: <bài toán tự luận>
DAPAN: xem lời giải
LOIGIAI: <lời giải đầy đủ tới kết quả cuối>
===KETCAU===
"""


_QUALITY_CHECKLIST = """\
DANH SÁCH KIỂM TRA TRƯỚC KHI TRẢ LỜI:
- Tổng số câu đúng yêu cầu.
- Không có bất kỳ thẻ trích dẫn [cite: ...] hay [source: ...].
- TN có đúng 4 phương án khác nhau và chỉ 1 đáp án đúng.
- DS có 4 ý a/b/c/d, có ít nhất 1 ý Đúng và 1 ý Sai.
- TLN có đáp án ngắn, ưu tiên số tối đa 4 ký tự khi có thể.
- Bảng số liệu bảo toàn cấu trúc bảng, không mất dòng hay gãy cột.
- Lời giải tự tính lại đáp án, không chỉ lặp lại đáp án.
- Không có văn bản ngoài khối, không có hàng rào markdown ``` trong kết quả.
"""


_GEM_MASTER_UNIFIED_RULES = """\
GEM MASTER MATRIXEXAMAI V5:
Đây là prompt hệ thống duy nhất cho Gemini GEM khi làm việc với MatrixExamAI. Bạn là giáo viên Toán THCS/THPT giàu kinh nghiệm, đồng thời là bộ tạo, chuyển đổi, sửa lỗi và kiểm tra câu hỏi tương thích trực tiếp với app.

I. NHẬN DIỆN CHẾ ĐỘ TỰ ĐỘNG
- Chế độ A - Tạo đề tương tự từ file: người dùng gửi Word/PDF/ảnh và yêu cầu tạo đề tương tự. Giữ số câu, thứ tự, loại câu, mức độ và dạng toán; thay toàn bộ số liệu, bối cảnh phụ, phương án nhiễu; tính lại đáp án và lời giải theo số mới.
- Chế độ A' - Chuyển đề về cấu trúc app: người dùng gửi file nhưng không yêu cầu tương tự. Giữ nguyên dữ kiện, đáp án và ý nghĩa toán học; chỉ chuẩn hóa OCR, LaTeX, TikZ và schema.
- Chế độ B - Tạo mới: người dùng chỉ nêu lớp, chủ đề, số câu, loại câu, mức độ hoặc yêu cầu riêng. Tạo câu hỏi mới đa dạng, không lặp số liệu/cách hỏi.
- Chế độ B' - Tạo theo ma trận: người dùng dán ma trận. Bám đúng phân bổ loại câu, mức độ, chương/chủ đề và số lượng.
- Nếu thiếu thông tin bắt buộc để làm đúng, hỏi lại đúng một dòng ngắn. Nếu đủ thông tin, trả lời ngay bằng khối câu hỏi.

II. QUY TẮC TẠO ĐỀ TƯƠNG TỰ
- Không sao chép nguyên văn đề chính thức; chỉ giữ cấu trúc tư duy và dạng toán.
- Số mới ưu tiên số nguyên trong khoảng -15 đến 15, khác toàn bộ số gốc và không làm mẫu bằng 0, căn/log vô nghĩa hoặc phương trình vô nghiệm ngoài ý muốn.
- Với TN, có đúng 1 đáp án đúng và 3 nhiễu hợp lý từ lỗi sai thường gặp: sai dấu, quên điều kiện, nhầm công thức, sai đơn vị, biến đổi thiếu bước.
- Với DS, luôn có 4 ý a/b/c/d, có ít nhất 1 ý D và 1 ý S.
- Với TLN/TL, đáp án phải kiểm chứng được; TLN ưu tiên số/biểu thức ngắn.

III. OUTPUT SCHEMA BẮT BUỘC
- Chỉ trả về các khối ===CAU=== ... ===KETCAU===; không lời chào, không markdown, không giải thích ngoài khối.
- CẤM TUYỆT ĐỐI CHÈN NGUỒN / CITATION: Không chèn bất kỳ nhãn trích dẫn như [cite: ...], [source: ...], [1], [2] vào đề hay lời giải.
- Mỗi field nằm trên dòng riêng, đúng thứ tự: LOAI, MUCDO, CHUONG, DIEM nếu có, NOIDUNG, phương án/ý, DAPAN, LOIGIAI.
- LOAI thuộc TN, DS, TLN, TL. MUCDO thuộc NB, TH, VD, VDC.
- Bảng số liệu: Dùng định dạng bảng Markdown (| Cột 1 | Cột 2 |\\n| --- | --- |) hoặc LaTeX \\begin{tabular}{...}...\\end{tabular}.
- DS dùng D/S không dấu trong DAPAN, ví dụ: DAPAN: a=D,b=S,c=D,d=S.
- TLN/TL có DIEM. TL có thể bỏ DAPAN nếu LOIGIAI kết luận rõ.
- Giữa hai câu chỉ để một dòng trống; output kết thúc ở ===KETCAU=== cuối cùng.

IV. CÔNG THỨC VÀ LỜI GIẢI
- Công thức inline duy nhất là ${...}$. Không dùng $$...$$, \\(...\\), \\[...\\].
- Không dùng ký hiệu toán Unicode trực tiếp như ≤, ≥, ≠, √, π, Δ, ×; viết bằng LaTeX.
- Lời giải bắt buộc nhiều dòng. Mỗi bước biến đổi hoặc kết luận trung gian là một dòng riêng.
- Dùng văn phong giáo viên: "Ta có", "Suy ra", "Do đó", "Thay vào", "Vậy", "Kết luận"; tránh lặp máy móc.
- Với DS, LOIGIAI giải thích riêng từng ý, bắt đầu bằng a., b., c., d.

V. TIKZ VÀ HÌNH VẼ
- Câu hình học, đồ thị hàm số, bảng biến thiên, bảng xét dấu hoặc dữ kiện trực quan nên kèm TikZ nếu hình giúp hiểu đề.
- TikZ đặt trực tiếp trong NOIDUNG hoặc LOIGIAI, bắt đầu bằng \\begin{tikzpicture} và kết thúc bằng \\end{tikzpicture}.
- Không dùng markdown fence, \\documentclass, \\usepackage hoặc preamble; app tự cung cấp môi trường render.
- Bảng biến thiên/bảng xét dấu dùng tkz-tab chuẩn: BẮT BUỘC dùng \\tkzTabVar (CẤM dùng \\tkzTabVector).
- Ưu tiên declare function ở đầu tikzpicture cho cạnh, chiều cao, bán kính, góc, hệ số co giãn và số liệu phụ; tránh hard-code dữ kiện chính rải rác.
- Điểm hình học thường dùng \\draw (P) circle (0.6pt); nhãn font \\large. BBT/BXD/đồ thị dùng every node/.style={font=\\Large} khi cần.
- Nét khuất dùng dash pattern=on 2pt off 1.5pt; pattern dùng Lines[angle=45, distance=3pt, line width=0.3pt], pattern color=gray!70.
- Bảng biến thiên/bảng xét dấu dùng tkz-tab chuẩn: nocadre=false, lgt tối thiểu 1.2, espcl hợp lý, deltacl=0.6; không lạm dụng \\Large trong từng ô khi đã có every node.
- Với đồ thị hàm số: khảo sát đạo hàm, cực trị, giao trục, tiệm cận, điểm đặc biệt trước; chọn khung hiển thị cân đối; nhãn không chồng đồ thị, trục hoặc tiệm cận; đường tiệm cận nằm cùng scope clip với đồ thị.

VI. CHECKLIST TRƯỚC KHI TRẢ LỜI
- Đủ số câu, đúng loại/mức độ/chủ đề/ma trận.
- Không có text ngoài khối, không markdown, không dòng thừa cuối output.
- Tất cả đáp án đã tính lại, đặc biệt khi tạo đề tương tự.
- TN đủ A/B/C/D khác nhau; DS đủ a/b/c/d và DAPAN dạng D/S.
- Công thức đúng ${...}$; TikZ raw không có preamble.
- Lời giải nhiều dòng, đủ căn cứ để giáo viên kiểm tra.
"""


_CHATBOT_PROMPT_TEMPLATES: tuple[ChatbotPromptTemplate, ...] = (
    ChatbotPromptTemplate(
        id="gemini_gem_master",
        family="Gemini GEM",
        title="GEM tổng hợp MatrixExamAI",
        description="Prompt hệ thống giúp GEM/Gemini ghi nhớ định dạng app và cách tạo đủ 4 loại câu.",
        provider_hint="Dùng làm hướng dẫn hệ thống cho Gemini GEM; sau đó gửi yêu cầu cụ thể bên dưới.",
        default_qtype="MIX",
        default_level="auto",
        instruction=(
            "Bạn là chuyên gia chuyên dụng cho MatrixExamAI. Hãy ưu tiên nội dung có thể copy trực tiếp vào app, "
            "không cần sửa tay, và tự kiểm tra định dạng trước khi trả lời."
        ),
        emphasis=(
            "Ghi nhớ định dạng app như một quy tắc hệ thống.",
            "Khi thiếu chi tiết, suy luận hợp lý thay vì hỏi lại quá nhiều.",
            "Phù hợp tạo câu hỏi, đề kiểm tra, ma trận, TikZ và sửa định dạng import.",
        ),
    ),
    ChatbotPromptTemplate(
        id="gemini_mixed_exam",
        family="Gemini GEM",
        title="Bộ câu hỏi hỗn hợp TN/DS/TLN/TL",
        description="Sinh nhiều dạng câu trong một lần, dùng cho đề THCS/THPT.",
        provider_hint="Hợp với Gemini 3.5 Flash hoặc Gemini 3.1 Pro Preview khi cần sáng tạo nhiều kiểu câu.",
        default_qtype="MIX",
        default_level="auto",
        instruction="Tạo bộ câu hỏi hỗn hợp, phân bổ loại câu và mức độ hợp lý theo chủ đề giáo viên đưa ra.",
        emphasis=(
            "Không lặp cùng một ý tưởng qua nhiều câu.",
            "Câu VD/VDC nên có ngữ cảnh thực tế hoặc bước biến đổi rõ.",
            "Mỗi câu có lời giải đủ để giáo viên soát đáp án.",
        ),
    ),
    ChatbotPromptTemplate(
        id="gemini_tn_fast",
        family="Gemini GEM",
        title="TN 4 lựa chọn nhanh",
        description="Sinh trắc nghiệm A/B/C/D có các phương án nhiễu hợp lý.",
        provider_hint="Dùng khi cần tạo nhanh ngân hàng TN bằng Gemini.",
        default_qtype="TN",
        default_level="TH",
        instruction="Tạo câu trắc nghiệm 4 lựa chọn, mỗi câu chỉ có một đáp án đúng và nhiễu được thiết kế theo lỗi sai thường gặp.",
        emphasis=(
            "4 phương án phải khác nhau và độ dài tương đối cân bằng.",
            "Nhiễu sai nên đến từ sai dấu, quên điều kiện, nhầm công thức, sai đơn vị.",
            "DAPAN chỉ ghi một ký tự A/B/C/D.",
        ),
    ),
    ChatbotPromptTemplate(
        id="gemini_ds_tln",
        family="Gemini GEM",
        title="Đúng-Sai và trả lời ngắn",
        description="Tạo DS 4 ý và TLN số ngắn đúng quy cách đề thi mới.",
        provider_hint="Hợp với Gemini khi cần các dạng câu mới sau 2025.",
        default_qtype="DS/TLN",
        default_level="VD",
        instruction="Tạo các câu đúng-sai và trả lời ngắn xoay quanh chủ đề, ưu tiên tính đúng/sai có giải thích từng ý.",
        emphasis=(
            "DS phải có 4 ý liên quan cùng một tình huống, không rời rạc.",
            "TLN có đáp án ngắn, dùng dấu phẩy thập phân kiểu Việt Nam nếu là số thập phân.",
            "Lời giải DS ghi rõ a/b/c/d, bắt đầu bằng Đúng. Vì... hoặc Sai. Vì...",
        ),
    ),
    ChatbotPromptTemplate(
        id="gemini_tikz_geometry",
        family="Gemini GEM",
        title="Câu có hình TikZ",
        description="Sinh câu hình học/đồ thị có mã TikZ thuần để app render PNG/Word.",
        provider_hint="Dùng Gemini khi cần hình vẽ có tọa độ, nhãn và quan hệ hình học.",
        default_qtype="MIX",
        default_level="VD",
        instruction="Tạo câu hỏi có hình minh họa bằng mã TikZ thuần, hình phải khớp dữ kiện và lời giải.",
        emphasis=(
            "TikZ đặt trực tiếp trong NOIDUNG, không dùng documentclass/usepackage.",
            "Tên điểm, đường thẳng, góc, song song/vuông góc phải trùng đề bài.",
            "Nếu hình quá phức tạp, đơn giản hóa nhưng giữ đúng bản chất toán.",
        ),
    ),
    ChatbotPromptTemplate(
        id="chatgpt_standard",
        family="ChatGPT",
        title="Tạo câu hỏi chuẩn app",
        description="Mẫu phổ thông để dán vào ChatGPT tạo câu hỏi đọc được ngay.",
        provider_hint="Dùng trên ChatGPT web hoặc OpenAI GPT khi cần đầu ra ổn định.",
        default_qtype="MIX",
        default_level="TH",
        instruction="Đóng vai giáo viên Toán THCS/THPT và tạo câu hỏi đúng khung MatrixExamAI.",
        emphasis=(
            "Chỉ trả các khối câu hỏi, không mở đầu/kết luận.",
            "Ưu tiên câu hỏi rõ ràng, không đánh đố bằng ngôn ngữ mơ hồ.",
            "Tự kiểm tra đáp án trước khi xuất.",
        ),
    ),
    ChatbotPromptTemplate(
        id="chatgpt_reasoned_solution",
        family="ChatGPT",
        title="Lời giải chất lượng cao",
        description="Tạo câu hỏi kèm lời giải có lập luận tốt để đưa vào đề.",
        provider_hint="Hợp với ChatGPT khi giáo viên cần lời giải đẹp, dễ đọc.",
        default_qtype="MIX",
        default_level="VD",
        instruction="Tạo câu hỏi và lời giải sư phạm chất lượng cao, trình bày mạch lạc nhưng vẫn gọn.",
        emphasis=(
            "Lời giải nêu công thức áp dụng, thay số và kết luận.",
            "Không bỏ qua điều kiện xác định, đơn vị, miền giá trị.",
            "Câu hỏi và đáp án khớp tuyệt đối.",
        ),
    ),
    ChatbotPromptTemplate(
        id="chatgpt_exam_matrix",
        family="ChatGPT",
        title="Tạo theo ma trận",
        description="Tạo bộ câu theo cơ cấu loại câu, mức độ và chủ đề giáo viên nhập.",
        provider_hint="Dùng khi đã có ma trận hoặc bảng phân bổ số câu.",
        default_qtype="MIX",
        default_level="auto",
        instruction="Đọc yêu cầu/ma trận, tạo đúng số câu theo từng loại và mức độ; nếu thiếu chi tiết thì phân bổ hợp lý.",
        emphasis=(
            "Giữ đúng tổng số câu và cơ cấu loại câu.",
            "Ghi CHUONG theo chủ đề cụ thể, không để trống.",
            "Không tạo hai câu chỉ thay số quá đơn giản nếu không được yêu cầu.",
        ),
    ),
    ChatbotPromptTemplate(
        id="chatgpt_cleanup_import",
        family="ChatGPT",
        title="Chuẩn hóa đầu ra/Word/OCR",
        description="Sửa văn bản câu hỏi thô thành khối MatrixExamAI.",
        provider_hint="Dùng ChatGPT khi có câu hỏi copy từ Word/PDF/OCR nhưng định dạng lộn xộn.",
        default_qtype="auto",
        default_level="auto",
        instruction="Chuyển văn bản nguồn thành các khối câu hỏi MatrixExamAI, giữ nguyên nội dung và đáp án nếu có.",
        emphasis=(
            "Không tự chế nội dung nếu văn bản nguồn đã đủ.",
            "Nếu thiếu đáp án, ghi DAPAN: <chưa có> và giải thích ngắn trong LOIGIAI.",
            "Chuẩn hóa A/B/C/D, a/b/c/d, DAPAN và LOIGIAI để app đọc được.",
        ),
    ),
    ChatbotPromptTemplate(
        id="chatgpt_similar_exam",
        family="ChatGPT",
        title="Tạo câu/đề tương tự",
        description="Sinh câu mới cùng dạng, khác số và ngữ cảnh với đề gốc.",
        provider_hint="Dùng khi có câu/đề mẫu và cần bản tương tự để luyện tập.",
        default_qtype="MIX",
        default_level="auto",
        instruction="Tạo câu hỏi tương tự với mẫu, giữ năng lực cần đo nhưng thay số liệu, ngữ cảnh và đáp án.",
        emphasis=(
            "Không sao chép nguyên văn câu gốc.",
            "Số liệu mới phải cho đáp án đẹp nếu là TLN/TN.",
            "Lời giải phải tính theo dữ liệu mới.",
        ),
    ),
    ChatbotPromptTemplate(
        id="deepseek_reasoner_math",
        family="DeepSeek",
        title="Reasoner toán học",
        description="Dùng DeepSeek Reasoner để soát logic, đáp án và lời giải.",
        provider_hint="Hợp với deepseek-reasoner khi cần tính toán/logic chặt.",
        default_qtype="MIX",
        default_level="VD",
        instruction="Giải nháp thật kỹ để đảm bảo đáp án đúng, nhưng chỉ xuất kết quả theo khối MatrixExamAI.",
        emphasis=(
            "Không in chuỗi suy luận dài ngoài LOIGIAI.",
            "Mỗi đáp án phải được tính lại từ đầu.",
            "Nếu bài có điều kiện, phải nêu trong lời giải.",
        ),
    ),
    ChatbotPromptTemplate(
        id="deepseek_batch_fast",
        family="DeepSeek",
        title="Batch nhanh nhiều câu",
        description="Sinh lô câu hỏi ngắn gọn, tiết kiệm token, dễ dán vào app.",
        provider_hint="Hợp với deepseek-chat khi cần tạo nhanh ngân hàng câu hỏi.",
        default_qtype="TN",
        default_level="TH",
        instruction="Tạo nhiều câu hỏi gọn, đúng định dạng, ưu tiên tính ổn định để parser đọc ngay.",
        emphasis=(
            "Mỗi câu độc lập, không tham chiếu câu trước.",
            "NOIDUNG ngắn nhưng đủ dữ kiện.",
            "Không chèn bảng markdown hay danh sách ngoài khối.",
        ),
    ),
    ChatbotPromptTemplate(
        id="deepseek_repair_format",
        family="DeepSeek",
        title="Sửa lỗi định dạng app",
        description="Sửa đầu ra AI bị sai thành khối MatrixExamAI hợp lệ.",
        provider_hint="Dùng khi đầu ra từ chatbot khác bị thừa markdown, sai DAPAN hoặc sai nhãn trường.",
        default_qtype="auto",
        default_level="auto",
        instruction="Sửa định dạng của văn bản nguồn để app đọc được, chỉ thay đổi hình thức nếu nội dung đã đúng.",
        emphasis=(
            "Xóa hàng rào markdown, tiêu đề, lời chào và văn bản ngoài khối.",
            "Chuẩn hóa LOAI, MUCDO, CHUONG, NOIDUNG, DAPAN, LOIGIAI.",
            "Bảo toàn đáp án/lời giải gốc nếu không có lỗi rõ ràng.",
        ),
    ),
    ChatbotPromptTemplate(
        id="deepseek_tln_numeric",
        family="DeepSeek",
        title="TLN số ngắn và đáp án đẹp",
        description="Tạo trả lời ngắn có đáp án số đẹp, dùng cho đề thi mới.",
        provider_hint="Dùng DeepSeek để tính đáp án số chính xác và gọn.",
        default_qtype="TLN",
        default_level="VD",
        instruction="Tạo câu trả lời ngắn, mỗi đáp án là số ngắn hoặc kết quả đã làm tròn theo đề bài.",
        emphasis=(
            "Đề bài phải quy định rõ đơn vị/làm tròn nếu cần.",
            "DAPAN không kèm đơn vị, chỉ ghi giá trị ngắn.",
            "Lời giải chứng minh đáp án là duy nhất.",
        ),
    ),
    ChatbotPromptTemplate(
        id="shared_qc_fix",
        family="Sửa/QC",
        title="Kiểm tra và sửa câu hỏi",
        description="Rà soát câu hỏi đã tạo, sửa lỗi đáp án/định dạng/LaTeX.",
        provider_hint="Dùng với Gemini, ChatGPT hoặc DeepSeek khi cần QC lại đầu ra.",
        default_qtype="auto",
        default_level="auto",
        instruction="Kiểm tra các câu hỏi nguồn, sửa lỗi định dạng và lỗi toán nếu có, rồi trả lại khối MatrixExamAI hợp lệ.",
        emphasis=(
            "Nếu đổi đáp án, phải cập nhật LOIGIAI tương ứng.",
            "Không bỏ sót câu nguồn.",
            "Giữ nguyên mức độ/chủ đề nếu hợp lý.",
        ),
    ),
    ChatbotPromptTemplate(
        id="shared_ocr_cleanup",
        family="OCR/Import",
        title="Làm sạch ảnh/PDF/Word",
        description="Biến nội dung OCR hoặc copy từ tài liệu thành câu hỏi app.",
        provider_hint="Dùng sau OCR, PDF scan, Word copy lỗi dòng hoặc mất nhãn đáp án.",
        default_qtype="auto",
        default_level="auto",
        instruction="Đọc văn bản OCR/copy thô, ghép dòng bị vỡ, nhận diện câu hỏi và xuất khối MatrixExamAI.",
        emphasis=(
            "Sửa lỗi OCR thông dụng nhưng không thay đổi ý nghĩa toán học.",
            "Nếu không chắc ký tự công thức, giữ dạng LaTeX an toàn và ghi chú ngắn trong LOIGIAI.",
            "Mỗi câu tách thành một khối riêng.",
        ),
    ),
)

_CHATBOT_PROMPT_BY_ID = {template.id: template for template in _CHATBOT_PROMPT_TEMPLATES}


def chatbot_prompt_catalog() -> list[dict[str, Any]]:
    """Return prompt suggestions grouped for the V5 ChatBotAI text workflow."""
    catalog: list[dict[str, Any]] = []
    for template in _CHATBOT_PROMPT_TEMPLATES:
        item = asdict(template)
        item["label"] = template.label
        catalog.append(item)
    return catalog


def get_chatbot_prompt_template(template_id: str) -> dict[str, Any]:
    """Return one prompt template as a plain dictionary."""
    template = _CHATBOT_PROMPT_BY_ID.get(template_id) or _CHATBOT_PROMPT_TEMPLATES[0]
    item = asdict(template)
    item["label"] = template.label
    return item


def build_chatbot_prompt(
    template_id: str,
    *,
    subject: str = "Toán",
    grade: str = "1-12",
    topic: str = "",
    count: int | str = 10,
    qtype: str = "auto",
    level: str = "auto",
    extra: str = "",
) -> str:
    """Build a copy-ready external chatbot prompt for creating/importing questions."""
    template = _CHATBOT_PROMPT_BY_ID.get(template_id) or _CHATBOT_PROMPT_TEMPLATES[0]
    try:
        count_value = max(1, int(str(count).strip() or "10"))
    except ValueError:
        count_value = 10
    qtype_value = (qtype or "auto").strip()
    if qtype_value.lower() == "auto":
        qtype_value = template.default_qtype
    level_value = (level or "auto").strip()
    if level_value.lower() == "auto":
        level_value = template.default_level
    topic_value = (topic or "").strip() or "chủ đề giáo viên cung cấp"
    subject_value = (subject or "Toán").strip()
    grade_value = str(grade or "1-12").strip()
    if template.id == "gemini_gem_master" and grade_value in {"", "12"}:
        grade_value = "1-12 (không bắt buộc lớp 12)"
    extra_value = (extra or "").strip() or "Không."
    emphasis = "\n".join(f"- {item}" for item in template.emphasis)
    master_rules = (
        f"\n{_GEM_MASTER_UNIFIED_RULES}\n"
        if template.id == "gemini_gem_master"
        else ""
    )

    return f"""\
VAI TRÒ / MODEL:
{template.provider_hint}

NHIỆM VỤ:
{template.instruction}

THÔNG TIN ĐỀ TẠO:
- Môn: {subject_value}
- Lớp/phạm vi: {grade_value}
- Chủ đề: {topic_value}
- Số câu: {count_value}
- Loại câu ưu tiên: {qtype_value}
- Mức độ ưu tiên: {level_value}
- Yêu cầu thêm: {extra_value}

TRỌNG TÂM CỦA MẪU "{template.family} - {template.title}":
{emphasis}
{master_rules}

{_APP_BLOCK_RULES}

{_QUALITY_CHECKLIST}

Hãy bắt đầu ngay bằng ===CAU=== và chỉ trả về các khối câu hỏi để tôi dán trực tiếp vào MatrixExamAI V5.
"""


_TIKZ_BLOCK_RE = re.compile(
    r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}",
    re.DOTALL | re.IGNORECASE,
)


def rewrite_tikz_blocks_in_text(text: str) -> str:
    """Apply safe local TikZ quick-fixes to every tikzpicture block in text."""
    raw = text or ""
    if not raw.strip():
        return ""
    try:
        from services.tikz_preflight import auto_fix
    except Exception:
        return raw

    def _fix(match: re.Match[str]) -> str:
        fixed = auto_fix(match.group(0)).strip()
        return fixed or match.group(0)

    return _TIKZ_BLOCK_RE.sub(_fix, raw)


def rewrite_prompt_and_tikz_text(text: str) -> str:
    """Rewrite a raw GEM prompt request and clean embedded TikZ blocks locally."""
    cleaned = rewrite_tikz_blocks_in_text(text or "").strip()
    if not cleaned:
        return build_chatbot_prompt("gemini_gem_master")
    if "===CAU===" in cleaned:
        return cleaned
    if "GEM MASTER MATRIXEXAMAI:" in cleaned:
        return cleaned
    master = build_chatbot_prompt(
        "gemini_gem_master",
        extra="Tong hop prompt nguon ben duoi thanh mot prompt duy nhat, ro rang, dung cho GEM.",
    )
    return (
        f"{master}\n\n"
        "PROMPT NGUON CAN VIET LAI / HINH TIKZ CAN LAM SACH:\n"
        f"{cleaned}\n"
    )


def parse_text_questions(text: str) -> list[Question]:
    """Parse app blocks, LaTeX ``ex_test`` blocks, or ordinary question text."""
    raw = (text or "").strip()
    if not raw:
        return []

    from core.exam_file_loader import parse_questions_from_text

    questions, _tier = parse_questions_from_text(raw)
    return questions


def combine_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Combine multiple file extraction results into one V5 result."""
    combined: dict[str, Any] = {
        "questions": [],
        "meta": {"subject": "Toán", "grade": "1-12", "topic": ""},
        "warnings": [],
        "raw_text": "",
        "methods": [],
    }
    raw_parts: list[str] = []
    for result in results:
        combined["questions"].extend(result.get("questions", []) or [])
        combined["warnings"].extend(result.get("warnings", []) or [])
        method = result.get("method")
        if method:
            combined["methods"].append(method)
        raw = result.get("raw_text", "")
        if raw:
            raw_parts.append(raw)
        meta = result.get("meta", {}) or {}
        for key in ("subject", "grade", "topic"):
            if meta.get(key):
                combined["meta"][key] = str(meta[key])
    combined["raw_text"] = "\n\n".join(raw_parts)
    return combined


def assign_ids_for_save(questions: list[Question], grade: str) -> None:
    """Assign structured IDs only to questions still carrying temporary IDs."""
    from core.models import compute_structured_id

    existing = {
        str(question.question_id)
        for question in questions
        if (getattr(question, "question_id", "") or "").strip()
        and not str(question.question_id).startswith("QID-")
    }
    topic_map: dict[str, int] = {}
    for question in questions:
        current = str(getattr(question, "question_id", "") or "")
        if current and not current.startswith("QID-"):
            continue
        question_id = compute_structured_id(
            question,
            str(grade or "12"),
            existing_qids=existing,
            topic_chapter_map=topic_map,
        )
        if question_id:
            question.question_id = question_id
            existing.add(question_id)


def build_text_normalize_prompt(text: str) -> str:
    """Create a focused prompt to convert pasted text into app blocks."""
    return f"""Chuyển văn bản câu hỏi sau sang cấu trúc MatrixExamAI.
Giữ nguyên nội dung, dữ kiện và đáp án; chỉ chuẩn hóa định dạng.
Mỗi câu phải nằm trong một khối:
===CAU===
LOAI: TN | DS | TLN | TL
MUCDO: NB | TH | VD
CHUONG: <chủ đề>
NOIDUNG: <nội dung>
A: ... B: ... C: ... D: ... (chỉ TN)
a: ... b: ... c: ... d: ... (chỉ DS)
DAPAN: <đáp án nếu có>
LOIGIAI: <lời giải nếu có>
===KETCAU===
Chỉ trả các khối, không thêm lời dẫn.

VĂN BẢN:
{text}"""
