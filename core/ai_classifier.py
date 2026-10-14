"""
core/ai_classifier.py — AI phân loại chủ đề & mức độ cho câu hỏi.

Dùng khi upload câu hỏi từ file (Word/PDF/LaTeX) mà thiếu metadata chủ đề.
Gửi batch câu hỏi cho AI → nhận lại topic + level cho mỗi câu.
"""

from __future__ import annotations
import json
import re
from typing import Callable, Optional
from core.models import Question


_CLASSIFY_PROMPT = """Bạn là chuyên gia phân loại câu hỏi thi THCS/THPT Việt Nam.

Cho danh sách câu hỏi bên dưới, hãy xác định MÔN HỌC, CHỦ ĐỀ, MỨC ĐỘ và LOẠI CÂU cho mỗi câu.

MÔN HỌC: Toán, Vật lý, Hóa học, Sinh học, Ngữ văn, Lịch sử, Địa lý, GDCD, Tiếng Anh, Tin học...

CHỦ ĐỀ TOÁN phổ biến:
Dưới đây là chi tiết hóa các chủ đề Toán phổ biến từ lớp 1 đến lớp 12 theo từng cấp học (Tiểu học – THCS – THPT), kèm theo các nội dung cụ thể, dạng bài tập minh họa và gợi ý phân bố mức độ NB – TH – VD. Cấu trúc này có thể dùng để xây dựng chương trình, ngân hàng câu hỏi hoặc hướng dẫn AI ra đề.

---

 📐 TOÁN TIỂU HỌC (LỚP 1 – 5)

# 1. Số tự nhiên và các phép tính
- Lớp 1-2: Đọc, viết, so sánh số trong phạm vi 100; cộng, trừ không nhớ/có nhớ.
- Lớp 3-4: Số đến 100 000; bảng nhân, chia; tính giá trị biểu thức (có dấu ngoặc).
- Lớp 5: Số tự nhiên lớn; dấu hiệu chia hết (2,3,5,9); ước và bội.

# 2. Phân số – Số thập phân
- Lớp 4: Khái niệm phân số; so sánh; cộng trừ phân số cùng mẫu.
- Lớp 5: Các phép tính với phân số khác mẫu; hỗn số; số thập phân; tỉ số phần trăm.

# 3. Đại lượng và đo lường
- Độ dài: cm, dm, m, km (lớp 2-3).
- Khối lượng: g, kg (lớp 3-4).
- Diện tích: cm², dm², m² (lớp 4-5).
- Thời gian: giờ, phút, giây; bài toán tính thời gian (lớp 3-5).
- Thể tích: cm³, dm³, m³ (lớp 5).

# 4. Hình học cơ bản
- Lớp 1-2: Nhận biết hình vuông, tròn, tam giác, chữ nhật; điểm, đoạn thẳng.
- Lớp 3-4: Chu vi, diện tích hình vuông, chữ nhật; góc vuông; đường thẳng song song.
- Lớp 5: Hình tam giác (chiều cao, đáy); hình thang; hình tròn (bán kính, đường kính, chu vi, diện tích); hình hộp chữ nhật, hình lập phương (diện tích xung quanh, toàn phần, thể tích).

# 5. Giải toán có lời văn
- Dạng: Hơn kém, tổng – hiệu, tổng – tỉ, hiệu – tỉ (lớp 4-5).
- Bài toán chuyển động đều (quãng đường, vận tốc, thời gian – lớp 5).
- Bài toán về tỉ lệ thuận, tỉ lệ nghịch (lớp 5).

# 6. Thống kê đơn giản
- Đọc biểu đồ tranh, biểu đồ cột; xác định số lần xuất hiện (lớp 3-5).

# 7. Yếu tố đại số sơ khai
- Tìm số trung bình cộng (lớp 4).
- Tìm thành phần chưa biết (x) trong phép tính (lớp 2-5).

---

 📐 TOÁN TRUNG HỌC CƠ SỞ (LỚP 6 – 9)

# 1. Số học
- Lớp 6: Tập hợp số tự nhiên, số nguyên, ước chung – bội chung, số nguyên tố, phân số tối giản.
- Lớp 7: Số hữu tỉ, số thực, giá trị tuyệt đối, tỉ lệ thức.
- Lớp 8,9: Số vô tỉ, căn bậc hai, căn bậc ba, so sánh căn.

# 2. Hàm số và đồ thị (sơ khai)
- Lớp 7: Đại lượng tỉ lệ thuận, nghịch; mặt phẳng tọa độ.
- Lớp 8,9: Hàm số bậc nhất y = ax + b (đồ thị, hệ số góc, tính đồng biến, nghịch biến).
- Lớp 9: Hàm số bậc hai y = ax² (đồ thị parabol); phương trình bậc hai; hệ phương trình bậc nhất hai ẩn.

# 3. Phương trình – Bất phương trình
- Lớp 6-7: Phương trình bậc nhất một ẩn; bất phương trình bậc nhất.
- Lớp 8: Phương trình chứa ẩn ở mẫu; giải bài toán bằng cách lập phương trình.
- Lớp 9: Phương trình bậc hai (công thức nghiệm, hệ thức Vi-ét); phương trình quy về bậc hai; hệ phương trình bậc nhất hai ẩn.

# 4. Hình học phẳng
- Lớp 6: Điểm, đường thẳng, tia, đoạn thẳng; trung điểm; góc.
- Lớp 7: Hai góc đối đỉnh, so le trong, đồng vị; tam giác (tổng ba góc, các trường hợp bằng nhau); tam giác cân, đều, vuông.
- Lớp 8: Định lý Thales; tam giác đồng dạng; các đường đặc biệt trong tam giác; hình bình hành, hình chữ nhật, hình thoi, hình vuông.
- Lớp 9: Hệ thức lượng trong tam giác vuông; đường tròn (góc ở tâm, góc nội tiếp, tiếp tuyến); tứ giác nội tiếp; độ dài cung, diện tích hình tròn, quạt tròn.

# 5. Hình học không gian (sơ khai)
- Lớp 8: Hình hộp chữ nhật, hình lăng trụ đứng (diện tích xung quanh, thể tích).
- Lớp 9: Hình trụ, hình nón, hình cầu (công thức diện tích, thể tích).

# 6. Vectơ (lớp 10 nhưng THCS có thể giới thiệu ở lớp 9 nâng cao – không bắt buộc)

# 7. Thống kê – Xác suất sơ cấp
- Lớp 6-7: Thu thập số liệu, bảng tần số, biểu đồ (cột, đoạn thẳng, hình quạt).
- Lớp 7-8: Số trung bình cộng, mốt, trung vị (sơ lược).
- Lớp 8-9: Xác suất thực nghiệm (tung đồng xu, xúc xắc); không gian mẫu đơn giản.

# 8. Dãy số – Cấp số (giới thiệu ở lớp 9 chuyên)
- Cấp số cộng, cấp số nhân (công thức số hạng tổng quát, tổng n số hạng đầu).

---

 📐 TOÁN TRUNG HỌC PHỔ THÔNG (LỚP 10 – 12)

Dưới đây là chi tiết các chủ đề bạn liệt kê, bổ sung thêm nội dung cụ thể theo từng lớp.

# 1. Mệnh đề và tập hợp (Lớp 10)
- Mệnh đề, mệnh đề kéo theo, tương đương; phủ định.
- Tập hợp con, hợp, giao, hiệu, phần bù.
- Các phép toán trên tập hợp; biểu đồ Ven.

# 2. Hàm số và đồ thị (Lớp 10, 12)
- Lớp 10: Tập xác định; sự biến thiên; tính chẵn lẻ; đồ thị hàm số bậc nhất, bậc hai; hàm số y = |ax + b|; hàm số bậc nhất trên bậc nhất (y = (ax+b)/(cx+d)).
- Lớp 12: Hàm số bậc ba, trùng phương, phân thức; khảo sát và vẽ đồ thị; tương giao; tiếp tuyến.

# 3. Giới hạn và liên tục (Lớp 11)
- Giới hạn dãy số, giới hạn hàm số (hữu hạn, vô cực, một bên).
- Các dạng vô định (0/0, ∞/∞, ∞ – ∞).
- Hàm số liên tục tại điểm, trên khoảng; ứng dụng chứng minh phương trình có nghiệm.

# 4. Đạo hàm và ứng dụng (Lớp 11, 12)
- Lớp 11: Định nghĩa đạo hàm; quy tắc tính (tổng, hiệu, tích, thương); đạo hàm của hàm số sơ cấp; đạo hàm cấp cao.
- Lớp 12: Ứng dụng: tính đơn điệu, cực trị, giá trị lớn nhất – nhỏ nhất; tiệm cận; tiếp tuyến; bài toán tốc độ (vật lý).

# 5. Nguyên hàm và tích phân (Lớp 12)
- Nguyên hàm (bảng công thức, phương pháp đổi biến, từng phần).
- Tích phân xác định; tính chất; ứng dụng: diện tích hình phẳng, thể tích vật thể tròn xoay.

# 6. Hình học không gian (Lớp 11, 12)
- Lớp 11: Đường thẳng và mặt phẳng trong không gian; quan hệ song song (chứng minh, tìm giao tuyến, thiết diện).
- Lớp 11: Quan hệ vuông góc (đường thẳng vuông góc mặt phẳng, hai mặt phẳng vuông góc; góc; khoảng cách).
- Lớp 12: Thể tích khối chóp, khối lăng trụ, khối tròn xoay (nón, trụ, cầu) – nhưng chủ yếu ở hình học 12 nâng cao.

# 7. Hình học tọa độ trong không gian (Lớp 12)
- Hệ trục Oxyz; tọa độ điểm, vectơ; tích vô hướng, tích có hướng.
- Phương trình mặt phẳng (tổng quát, đoạn chắn); đường thẳng (tham số, chính tắc); mặt cầu.
- Vị trí tương đối, khoảng cách, góc; bài toán viết phương trình hình chiếu.

# 8. Hình học tọa độ phẳng (Lớp 10)
- Vectơ trong mặt phẳng; tọa độ điểm; biểu thức tọa độ của phép toán vectơ.
- Đường thẳng (phương trình tổng quát, tham số, hệ số góc); khoảng cách, góc.
- Đường tròn (phương trình chính tắc, tổng quát); tiếp tuyến; vị trí tương đối.
- Ba đường conic: Elip, Hypebol, Parabol (lớp 10 nâng cao hoặc 12 cơ bản).

# 9. Lượng giác (Lớp 10, 11)
- Lớp 10: Góc và cung lượng giác; giá trị lượng giác (sin, cos, tan, cot); các hệ thức cơ bản; công thức cộng, nhân đôi, hạ bậc; biến đổi tổng thành tích, tích thành tổng.
- Lớp 11: Phương trình lượng giác cơ bản; phương trình bậc nhất, bậc hai đối với một hàm số lượng giác; phương trình thuần nhất, đối xứng.

# 10. Hàm số mũ và logarithm (Lớp 11, 12)
- Lớp 11: Lũy thừa với số mũ hữu tỉ, vô tỉ; hàm số mũ, hàm số logarit (tập xác định, đồ thị, tính chất).
- Lớp 12: Phương trình, bất phương trình mũ và logarit (cùng cơ số, đặt ẩn phụ, mũ hóa, logarit hóa); ứng dụng (lãi kép, tăng trưởng).

# 11. Tổ hợp và xác suất (Lớp 10, 11)
- Lớp 10: Quy tắc cộng, quy tắc nhân; hoán vị, chỉnh hợp, tổ hợp (công thức, tính chất).
- Lớp 11: Nhị thức Newton; biến cố, không gian mẫu; xác suất cổ điển (công thức cộng, nhân); biến ngẫu nhiên rời rạc (kỳ vọng, phương sai).

# 12. Dãy số – Cấp số cộng – Cấp số nhân (Lớp 11)
- Dãy số (cách cho, tăng, giảm, bị chặn); phương pháp quy nạp.
- Cấp số cộng: số hạng tổng quát, tổng n số hạng đầu; tính chất.
- Cấp số nhân: tương tự; ứng dụng thực tế.

# 13. Phương trình – Bất phương trình (tổng hợp, nâng cao ở lớp 10, 12)
- Lớp 10: Hệ bất phương trình bậc nhất hai ẩn; dấu tam thức bậc hai; bất phương trình bậc hai.
- Lớp 12: Phương trình, bất phương trình chứa căn, chứa trị tuyệt đối, chứa mũ – logarit; giải bằng phương pháp đồ thị, hàm số.

# 14. Vectơ (Lớp 10)
- Định nghĩa; tổng, hiệu; tích vô hướng; ứng dụng chứng minh vuông góc, tính góc, độ dài.

---

 📌 GHI CHÚ ÁP DỤNG CHO CÁC MÔN KHÁC

Đối với môn Vật lý, Hóa học, Sinh học, Tin học, Lịch sử, Địa lý, GDCD, Ngoại ngữ, bạn có thể tự xác định chủ đề phù hợp theo nguyên tắc:

1. Vật lý: Chia theo mảng: Cơ học (lực, chuyển động, áp suất, công), Nhiệt học, Điện từ học, Quang học, Vật lý hạt nhân. Mỗi mảng có công thức, định luật, bài tập thí nghiệm.
2. Hóa học: Cấu tạo nguyên tử, bảng tuần hoàn, liên kết hóa học, phản ứng oxi hóa khử, tốc độ phản ứng, cân bằng, hóa hữu cơ (hidrocacbon, dẫn xuất).
3. Sinh học: Tế bào, di truyền, tiến hóa, sinh thái, sinh lý thực vật – động vật.
4. Tin học: Lập trình (biến, câu lệnh điều kiện, vòng lặp, mảng, hàm); cấu trúc dữ liệu và giải thuật (cơ bản).
5. Lịch sử: Các mốc thời gian, sự kiện, nhân vật, nguyên nhân – kết quả, ý nghĩa.
6. Địa lý: Tự nhiên (khí hậu, địa hình, sông ngòi), dân cư, kinh tế (nông – công – dịch vụ), bản đồ.
7. GDCD: Pháp luật, đạo đức, quyền và nghĩa vụ công dân.
8. Ngoại ngữ (Anh): Ngữ pháp (thì, câu điều kiện, bị động, so sánh), từ vựng theo chủ đề, kỹ năng đọc – viết – nghe – nói.

---

Mức độ: NB (Nhận biết), TH (Thông hiểu), VD (Vận dụng), VDC (Vận dụng cao)
MỨC ĐỘ 1: NHẬN BIẾT (NB)

Đặc điểm chung:
- Yêu cầu tái hiện kiến thức đã học, không cần suy luận hay biến đổi.  
- Câu hỏi thường ở dạng: định nghĩa, liệt kê, nhận diện, ghi nhớ công thức, thuật ngữ, sự kiện, quy tắc.

Chi tiết các dạng câu hỏi / bài tập:

1. Lý thuyết cơ bản:
   - Nêu định nghĩa của một khái niệm (ví dụ: "Định nghĩa tam giác cân").  
   - Phát biểu định lý, tính chất, quy tắc (ví dụ: "Phát biểu định lý Pytago").  
   - Kể tên các thành phần, bộ phận, giai đoạn (ví dụ: "Kể tên các loại máy cơ đơn giản").

2. Nhận diện:
   - Nhận dạng đồ thị, hình vẽ, biểu đồ tương ứng với khái niệm (ví dụ: "Hình nào sau đây là đồ thị hàm số bậc nhất?").  
   - Xác định đúng/sai một mệnh đề đơn giản dựa vào định nghĩa (ví dụ: "3 là số nguyên tố – đúng hay sai?").  
   - Phân loại đối tượng theo tiêu chí có sẵn.

3. Công thức, ký hiệu:
   - Viết đúng công thức (ví dụ: "Viết công thức tính diện tích hình chữ nhật").  
   - Nêu đơn vị của đại lượng (ví dụ: "Đơn vị của vận tốc là gì?").  
   - Nhớ và nhắc lại hằng số, hệ số (ví dụ: "Hằng số Avogadro có giá trị bao nhiêu?").

4. Bài tập tính toán cực kỳ đơn giản:  
   - Chỉ cần thay số trực tiếp vào công thức, không biến đổi.  
   - Kết quả có thể nhẩm được.  
   - Ví dụ: "Tính diện tích hình vuông cạnh 5 cm."

---

MỨC ĐỘ 2: THÔNG HIỂU (TH)

Đặc điểm chung:
- Hiểu được ý nghĩa của khái niệm, công thức, có thể diễn giải, so sánh, hoặc áp dụng trực tiếp trong 1–2 bước tính toán.  
- Chưa yêu cầu kết hợp nhiều mảng kiến thức hay suy luận phức tạp.

Chi tiết các dạng câu hỏi / bài tập:

1. Diễn giải, giải thích: 
   - Giải thích ý nghĩa của một kết quả, hiện tượng (ví dụ: "Tại sao khi đun nóng chất khí trong bình kín, áp suất lại tăng?").  
   - Chuyển đổi giữa các dạng biểu diễn: lời – công thức – đồ thị (ví dụ: "Cho hàm số y = 2x + 1, hãy vẽ đồ thị của nó").

2. So sánh, phân biệt:
   - Chỉ ra điểm giống và khác nhau giữa hai khái niệm (ví dụ: "So sánh điểm khác nhau giữa phản ứng tỏa nhiệt và thu nhiệt").  
   - Xếp thứ tự, phân cấp theo tiêu chí.

3. Áp dụng công thức đơn giản (1–2 bước):  
   - Tính toán với công thức đã học, có thể cần chuyển đổi đơn vị đơn giản.  
   - Ví dụ: "Một ô tô đi quãng đường 120 km trong 2 giờ. Tính vận tốc trung bình (km/h và m/s)."

4. Suy luận trực tiếp, không rẽ nhánh:  
   - Từ một dữ kiện suy ra dữ kiện khác theo quan hệ nhân quả rõ ràng.  
   - Ví dụ: "Biết a // b và c ⊥ a, hãy kết luận về quan hệ giữa c và b."

5. Bài tập có bước trung gian đơn giản:  
   - Cần thực hiện 1 phép biến đổi hoặc 1 phép suy luận trước khi áp dụng công thức.  
   - Ví dụ: "Tìm x biết 2x + 5 = 15" (giải bậc nhất 1 bước).

---

MỨC ĐỘ 3: VẬN DỤNG (VD)

Đặc điểm chung:
- Yêu cầu tư duy bậc cao, tổng hợp, phân tích, đánh giá, kết hợp nhiều kiến thức, nhiều kỹ năng.  
- Bài toán có nhiều bước (từ 3 bước trở lên), có thể có nhiều cách giải, nhiều tình huống phụ, hoặc cần sáng tạo.

Chi tiết các dạng câu hỏi / bài tập:

1. Bài toán nhiều bước (tổng hợp kiến thức):  
   - Kết hợp 2–3 chương hoặc 2–3 lĩnh vực khác nhau.  
   - Ví dụ: "Cho hình chóp S.ABCD có đáy là hình vuông, cạnh bên SA vuông góc đáy. Tính thể tích khối chóp biết góc giữa SC và mặt đáy là 30°." (cần hình học không gian + lượng giác + công thức thể tích).

2. Tình huống có nhiều trường hợp / điều kiện biên: 
   - Phải xét các khả năng khác nhau, loại trừ nghiệm ngoại lai.  
   - Ví dụ: "Giải phương trình chứa căn √(x+3) = x – 3" (cần đặt điều kiện, bình phương, thử lại).

3. Suy luận logic, tư duy phản biện:  
   - Chứng minh một mệnh đề không tầm thường.  
   - Tìm phản ví dụ, bác bỏ giả thuyết.  
   - Ví dụ: "Chứng minh rằng với mọi số tự nhiên n, n³ – n chia hết cho 6."

4. Bài toán thực tế phức tạp: 
   - Mô hình hóa tình huống thực tế thành bài toán.  
   - Cần lập phương trình / hệ phương trình, tối ưu hóa, dự báo.  
   - Ví dụ: "Một công ty sản xuất hộp sữa hình trụ với thể tích 1 lít. Hãy tìm kích thước để tiết kiệm nguyên liệu nhất."

5. Yêu cầu phân tích, đánh giá:
   - So sánh các phương án, lựa chọn giải pháp tối ưu.  
   - Nhận xét ưu, nhược điểm của một cách giải quyết vấn đề.

6. Bài toán mở, có nhiều hướng giải:
   - Không có một khuôn mẫu duy nhất, khuyến khích sáng tạo.  
   - Ví dụ: "Hãy đề xuất ít nhất hai cách khác nhau để xác định chiều cao của một tòa nhà mà không cần leo lên đỉnh."

LOẠI CÂU: TN (trắc nghiệm 4 đáp án), DS (đúng-sai 4 ý), TLN (trả lời ngắn), TL (tự luận)

Trả về JSON array, mỗi phần tử:
{{"idx": 0, "subject": "Toán", "topic": "Đạo hàm và ứng dụng", "level": "TH", "qtype": "TN"}}

QUAN TRỌNG: Chỉ trả về JSON array, không kèm text khác.

DANH SÁCH CÂU HỎI:
{questions_text}
"""

# Kích thước batch tối đa (tránh token limit)
_BATCH_SIZE = 10


def classify_questions_batch(
    questions: list[Question],
    ai_call: Callable,
    subject: str = "Toán",
    grade: str = "12",
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> list[Question]:
    """
    Phân loại chủ đề + mức độ cho danh sách câu hỏi bằng AI.

    Args:
        questions:   danh sách Question cần phân loại
        ai_call:     callable(prompt) -> text (từ AI service)
        subject:     môn học
        grade:       lớp
        on_progress: callback(done, total) để báo tiến độ

    Returns:
        Cùng danh sách questions nhưng đã được gán topic + level
    """
    total = len(questions)
    done = 0

    for batch_start in range(0, total, _BATCH_SIZE):
        batch = questions[batch_start: batch_start + _BATCH_SIZE]
        _classify_one_batch(batch, ai_call, batch_start, subject, grade)
        done += len(batch)
        if on_progress:
            on_progress(done, total)

    return questions


def _classify_one_batch(
    batch: list[Question],
    ai_call: Callable,
    offset: int,
    subject: str,
    grade: str,
) -> None:
    """Phân loại 1 batch câu hỏi."""
    # Build text mô tả từng câu
    lines = []
    for i, q in enumerate(batch):
        q_preview = q.question[:200].replace('\n', ' ')
        qtype_label = {"TN": "Trắc nghiệm", "DS": "Đúng/Sai",
                        "TLN": "Trả lời ngắn", "TL": "Tự luận"}.get(q.qtype, q.qtype)

        line = f"[{i}] ({qtype_label}) {q_preview}"

        # Thêm đáp án/ý/lời giải để AI hiểu rõ hơn
        if q.qtype == "TN" and q.options:
            opts = "  |  ".join(f"{k}. {v[:50]}" for k, v in q.options.items())
            line += f"\n    Đáp án: {opts}"
            if q.answer:
                line += f"\n    Đáp án đúng: {q.answer}"
        elif q.qtype == "DS" and q.items:
            items = "  |  ".join(f"({k}) {v[:50]}" for k, v in q.items.items())
            line += f"\n    Các ý: {items}"
        if q.solution and len(q.solution) > 10:
            line += f"\n    Lời giải: {q.solution[:100]}"

        lines.append(line)

    questions_text = "\n\n".join(lines)
    prompt = _CLASSIFY_PROMPT.format(questions_text=questions_text)

    try:
        response = ai_call(prompt)
        results = _parse_classify_response(response, len(batch))

        for r in results:
            idx = r.get("idx", -1)
            if 0 <= idx < len(batch):
                topic = r.get("topic", "").strip()
                level = r.get("level", "").strip().upper()
                ai_subject = r.get("subject", "").strip()
                ai_qtype = r.get("qtype", "").strip().upper()
                if topic:
                    batch[idx].topic = topic
                if level in ("NB", "TH", "VD", "VDC"):
                    batch[idx].level = level
                if ai_subject:
                    batch[idx].ai_subject = ai_subject
                if ai_qtype in ("TN", "DS", "TLN", "TL"):
                    batch[idx].qtype = ai_qtype
    except Exception:
        # AI fail → giữ nguyên, không crash
        pass


def _parse_classify_response(response: str, expected: int) -> list[dict]:
    """Parse JSON response từ AI."""
    text = response.strip()

    # Tìm JSON array trong response
    # Thử parse trực tiếp trước
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass

    # Tìm [...] trong text
    m = re.search(r'\[.*\]', text, re.DOTALL)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    # Tìm từng {...} riêng lẻ
    results = []
    for m in re.finditer(r'\{[^}]+\}', text):
        try:
            obj = json.loads(m.group(0))
            if "topic" in obj:
                results.append(obj)
        except json.JSONDecodeError:
            pass

    return results
