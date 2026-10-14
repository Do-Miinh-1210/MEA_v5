# TÀI LIỆU 03: 5 KỊCH BẢN VI KHÓA HỌC (MICRO-LEARNING SCRIPTS)
## Thời Lượng: 5 – 15 Phút/Bài | Cấu Trúc Sư Phạm Chuẩn 4 Bước
### Dự Án Chuyển Đổi Số: Nền Tảng MatrixExamAI Pro (.NET 10 Native Fluent UI)

---

## NGUYÊN TẮC THIẾT KẾ VI KHÓA HỌC (MICRO-LEARNING)

Mỗi kịch bản được xây dựng cho một video bài giảng ngắn (5 – 15 phút) hoặc một hoạt động thực hành nhanh trên lớp tập huấn, tuân thủ nghiêm ngặt mô hình sư phạm tương tác 4 bước:

```
+---------------------------------------------------------------------------------------------------------+
|                                  CẤU TRÚC 4 BƯỚC VI KHÓA HỌC (4-STEP FRAMEWORK)                          |
+-------------------+--------------------+------------------------+---------------------------------------+
|  BƯỚC 1: HOOK     |  BƯỚC 2: THAO TÁC  |  BƯỚC 3: TÌNH HUỐNG    |  BƯỚC 4: TÓM TẮT & MẸO PRO            |
|  Móc nối nỗi đau  |  Chuyển giao thao  |  Minh họa bài toán     |  3 điểm cốt lõi, phím tắt vàng        |
|  thực tế giáo viên|  tác click & phím  |  Toán/KHTN THPT thực tế|  và cảnh báo lỗi thường gặp           |
+-------------------+--------------------+------------------------+---------------------------------------+
```

---

## BÀI 1: CHUẨN HÓA ĐỀ THI & CÔNG THỨC TOÁN TỪ PDF/WORD TRONG 3 PHÚT (CONVERTVIEW)
- **Thời lượng dự kiến**: 8 phút
- **Phân hệ sử dụng**: `ConvertView`
- **Mục tiêu**: Giáo viên nạp 1 đề thi PDF hoặc Word cũ bất kỳ, tự động kẹp công thức dạng `${...}$` và xuất ra file Word Native Equation chuẩn chỉnh chỉ trong 3 phút.

### Bước 1: Hook (Móc nối vấn đề)
> *"Kính chào quý Thầy Cô! Đã bao giờ Thầy Cô tìm thấy một file PDF đề thi rất hay trên mạng, nhưng khi copy sang Word thì toàn bộ công thức toán học bị biến dạng thành những ký tự lạ hoắc như `x^2` thành `x2`, dấu phân số vỡ vụn, các bảng biểu chạy lung tung khắp trang? Thầy Cô phải thức đến 1-2 giờ sáng để ngồi gõ lại từng công thức bằng MathType. Hôm nay, chúng ta sẽ chấm dứt nỗi ám ảnh đó! Với phân hệ ConvertView của MatrixExamAI Pro, Thầy Cô chỉ mất đúng 3 phút để biến toàn bộ file PDF đó thành tài liệu Word với công thức toán bản địa đẹp như sách giáo khoa!"*

### Bước 2: Chuyển giao thao tác (Operation Transfer)
1. **Bước 2.1**: Mở phần mềm MatrixExamAI Pro, tại thanh Menu bên trái, click chọn tab **Chuẩn hóa đề (ConvertView)** (biểu tượng mũi tên chuyển đổi).
2. **Bước 2.2**: Tại khu vực Cột trái (Nạp dữ liệu):
   - Click nút **Chọn tệp đề thi (.pdf, .docx)** hoặc kéo thả trực tiếp tệp PDF cần chuẩn hóa vào khung màn hình.
   - Tại dòng cấu hình: Chọn **Lớp** (ví dụ: `12`) và chọn **Môn** (ví dụ: `Toán`).
3. **Bước 2.3**: Click nút xanh **Chuẩn hóa đề thi** (hoặc nhấn tổ hợp phím `Ctrl + Shift + C`):
   - Động cơ *PdfPig* siêu tốc sẽ bóc tách toàn bộ văn bản.
   - Thuật toán thông minh tự động bao đóng toàn bộ công thức toán học vào cặp định dạng `${...}$`, đồng thời kích hoạt thuật toán bảo vệ dấu trị tuyệt đối `|x|` không bị lỗi thành bảng kẻ.
4. **Bước 2.4**: Quan sát Cột phải (Xem trước & Xuất bản):
   - Tab *Xem trước Word* sẽ hiển thị văn bản đã được căn lề, công thức toán hiển thị ngay ngắn.
   - Click nút **Xuất file Word (.docx)**. Hệ thống sẽ sinh file Word native và tự động kích hoạt Microsoft Word mở tài liệu lên màn hình.

### Bước 3: Tình huống thực tế (Real-world Scenario)
- **Đề bài thực tế**: Chuẩn hóa một câu hỏi Vận dụng cao môn Toán 12 từ đề thi thử trường THPT Chuyên:
  > *Câu 45. Cho hàm số $f(x) = \frac{x^2 - 2|x| + m}{x + 1}$. Tìm tất cả các giá trị thực của tham số $m$ để $\int_{0}^{2} |f'(x)| dx \le 5$.*
- **Thực nghiệm trên MatrixExamAI**:
  - Khi nạp văn bản thô, phần mềm tự động nhận diện và chuyển đổi thành:
    ```markdown
    ===CAU===
    Cho hàm số ${f(x) = \frac{x^2 - 2|x| + m}{x + 1}}$. Tìm tất cả các giá trị thực của tham số ${m}$ để ${\int_{0}^{2} |f'(x)| dx \le 5}$.
    A. ${m \in [1; 3]}$
    B. ${m \in (-\infty; 0)}$
    C. ${m \in (0; 2)}$
    D. ${m \in [2; +\infty)}$
    ```
  - Biểu thức trị tuyệt đối `|x|` và `|f'(x)|` được bảo vệ toàn vẹn 100%, không bị hiểu nhầm thành cột bảng Markdown, và khi xuất sang Word hiển thị trực tiếp bằng công thức Microsoft Equation chuẩn OMML.

### Bước 4: Thực hành tóm tắt & Mẹo chuyên gia (Practice Summary & Pro-tips)
- **3 Điểm cốt lõi cần nhớ**:
  1. Nạp file PDF/Word -> Nhấn **Chuẩn hóa** -> Nhấn **Xuất Word**.
  2. Ký hiệu `${...}$` là mã bao đóng thông minh giúp Word hiểu đây là công thức toán học native.
  3. Bảng Markdown được tự động chuyển thành bảng Word Table Grid có viền nét đơn chuẩn in ấn.
- **Phím tắt vàng**: `Ctrl + Shift + C` (Chuẩn hóa nhanh ngay sau khi dán văn bản).
- **Mẹo tránh lỗi**: Nếu file PDF là dạng scan ảnh cũ (không có text), hãy dùng tổ hợp phím `Win + Shift + S` chụp vùng câu hỏi rồi dùng tính năng AI Vision OCR (Bài 2) thay vì nạp trực tiếp qua PdfPig.

---

## BÀI 2: THIẾT LẬP MA TRẬN ĐỀ THI 22 CÂU CHUẨN BỘ GD&ĐT 2025 (EXAMMATRIXVIEW)
- **Thời lượng dự kiến**: 10 phút
- **Phân hệ sử dụng**: `ExamMatrixView`
- **Mục tiêu**: Thiết lập đề thi tốt nghiệp THPT theo đúng cấu trúc định dạng mới 2025 gồm 22 câu (3 phần thi), tự động cân bằng thang điểm 10.0 và xuất bản ma trận khảo thí.

### Bước 1: Hook (Móc nối vấn đề)
> *"Thưa Thầy Cô, cấu trúc đề thi tốt nghiệp THPT mới từ năm 2025 theo chương trình GDPT 2018 là một bài toán hóc búa đối với mọi tổ chuyên môn: Đề thi không còn là 50 câu trắc nghiệm đơn thuần nữa, mà chia làm 3 phần riêng biệt: 12 câu trắc nghiệm 4 lựa chọn (3.0 điểm), 4 câu Đúng/Sai gồm 16 lệnh hỏi (4.0 điểm), và 6 câu trả lời ngắn (3.0 điểm). Mỗi phần có barem chấm điểm hoàn toàn khác nhau. Nếu ngồi tính nhẩm trên Excel, Thầy Cô rất dễ bị lệch điểm hoặc sai tỷ lệ câu hỏi Nhận biết - Thông hiểu - Vận dụng. Với ExamMatrixView, mọi chuyện được giải quyết tự động chỉ trong 1 cú click!"*

### Bước 2: Chuyển giao thao tác (Operation Transfer)
1. **Bước 2.1**: Mở tab **Ma trận đề thi (ExamMatrixView)** trên thanh điều hướng bên trái.
2. **Bước 2.2**: Tại khu vực *Cấu hình Ma trận*:
   - Trong ô chọn mẫu, click chọn: **Mẫu Chuẩn Bộ GD&ĐT 2025 (22 câu - 10.0 điểm)**.
   - Hệ thống tự động thiết lập 3 nhóm câu hỏi:
     * *Phần I*: 12 câu Nhiều lựa chọn (Mỗi câu 0.25đ = 3.0đ).
     * *Phần II*: 4 câu Đúng/Sai (Mỗi câu gồm 4 ý a-b-c-d, thang điểm tối đa 1.0đ/câu theo quy tắc lũy tiến của Bộ = 4.0đ).
     * *Phần III*: 6 câu Trả lời ngắn (Mỗi câu 0.5đ = 3.0đ).
3. **Bước 2.3**: Thiết lập Tỷ lệ phân hóa nhận thức (NB - TH - VD - VDC):
   - Kéo thanh trượt hoặc nhập phần trăm: Nhận biết (30%), Thông hiểu (40%), Vận dụng (20%), Vận dụng cao (10%).
   - Quan sát ô tổng điểm góc trên bên phải: Luôn báo xanh **Tổng: 10.0 / 10.0 điểm**.
4. **Bước 2.4**: Click nút **AI Soạn đề theo Ma trận** (hoặc chọn 'Lấy từ Ngân hàng câu hỏi SQLite'):
   - AI sẽ tự động phân bổ và điền đúng số lượng câu hỏi tương ứng từng phần.
   - Nhấn **Xuất bản Đề & Ma trận ra Word**.

### Bước 3: Tình huống thực tế (Real-world Scenario)
- **Tình huống**: Thầy Nam Tổ trưởng cần tạo đề kiểm tra chất lượng học kỳ 1 môn Toán 12 gồm các chuyên đề: Tính đơn điệu, Cực trị, Giá trị lớn nhất - nhỏ nhất, Tiệm cận, và Khảo sát đồ thị.
- **Phân bổ ma trận thực tế trong phần mềm**:
  - *Phần I (12 câu)*: 6 câu NB (Đọc đồ thị, tìm khoảng đồng biến), 4 câu TH (Tìm tiệm cận, cực trị hàm phân thức), 2 câu VD.
  - *Phần II (4 câu Đúng/Sai)*: Mỗi câu là một bài toán liên hoàn có 4 nhận định a, b, c, d (ví dụ: Câu khảo sát hàm số bậc ba với 4 mệnh đề về đạo hàm, số điểm cực trị, phương trình tiếp tuyến và diện tích tam giác).
  - *Phần III (6 câu Trả lời ngắn)*: 4 câu VD và 2 câu VDC (Bài toán tối ưu thực tế, tìm vận tốc lớn nhất, tính chi phí tối thiểu làm bể cá).
- Kết quả xuất ra file Word có đầy đủ: Bảng ma trận đặc tả ma trận nhận thức, Bảng phân phối câu hỏi, Đề thi chuẩn và Barem đáp án chi tiết.

### Bước 4: Thực hành tóm tắt & Mẹo chuyên gia (Practice Summary & Pro-tips)
- **3 Điểm cốt lõi cần nhớ**:
  1. Cấu trúc chuẩn 2025: 12 câu Phần I + 4 câu Phần II + 6 câu Phần III = Đúng 22 câu = 10.0 điểm.
  2. Barem chấm Phần II là lũy tiến: Đúng 1 ý được 0.1đ; đúng 2 ý được 0.25đ; đúng 3 ý được 0.5đ; đúng cả 4 ý được 1.0đ.
  3. Có thể khóa cố định một số câu hỏi quen thuộc từ ngân hàng trước khi gọi AI sinh các câu còn lại.
- **Mẹo chuyên gia**: Khi biên soạn câu hỏi Phần II (Đúng/Sai), luôn kiểm tra để đảm bảo 4 ý a, b, c, d có tính độc lập logic tương đối, tránh tình trạng ý (a) sai dẫn đến học sinh không thể làm tiếp ý (b), (c), (d).

---

## BÀI 3: TRỘN ĐỀ HOÁN VỊ 4 MÃ ĐỀ KHÔNG LỆCH BẢNG ĐÁP ÁN & XUẤT OMR (SHUFFLEVIEW)
- **Thời lượng dự kiến**: 7 phút
- **Phân hệ sử dụng**: `ShuffleView`
- **Mục tiêu**: Xáo trộn đề thi gốc thành 4 mã đề hoán vị hoàn hảo, bảo vệ tuyệt đối các phương án phụ thuộc ("Cả A và B đều đúng"), và xuất ma trận đáp án chéo phục vụ máy chấm OMR.

### Bước 1: Hook (Móc nối vấn đề)
> *"Thầy Cô đã bao giờ gặp 'tai nạn' này khi trộn đề kiểm tra chưa: Câu hỏi có phương án D là 'Cả A và B đều đúng', nhưng khi qua phần mềm trộn đề, phương án này bị đảo lên thành phương án A: 'A. Cả A và B đều đúng'? Học sinh làm bài hoang mang, Thầy Cô phải đính chính giữa giờ thi rất mất uy tín. Chưa kể, ngồi dò bằng mắt để làm 4 bảng đáp án cho 4 mã đề rất dễ nhầm lẫn. Hôm nay, phân hệ ShuffleView sẽ giải quyết triệt để vấn đề này chỉ trong 60 giây!"*

### Bước 2: Chuyển giao thao tác (Operation Transfer)
1. **Bước 2.1**: Mở tab **Trộn đề hoán vị (ShuffleView)** trên thanh điều hướng bên trái.
2. **Bước 2.2**: Nạp đề thi nguồn:
   - Click nút **Nạp đề thi gốc** (chấp nhận file `.docx`, `.txt` hoặc đề vừa tạo từ ConvertView/ExamMatrixView).
3. **Bước 2.3**: Thiết lập thông số trộn đề:
   - Nhập danh sách mã đề cần sinh: `101, 102, 103, 104`.
   - **Thao tác then chốt**: Tích chọn ô kiểm **Khóa phương án phụ thuộc (Keep Dependent Choices Fixed)**.
   - Tích chọn: **Xáo trộn thứ tự câu hỏi** và **Xáo trộn thứ tự phương án A-B-C-D**.
4. **Bước 2.4**: Bấm nút **Trộn đề hoán vị** (hoặc phím `F9`):
   - Thuật toán xáo trộn câu hỏi và các phương án theo ma trận hoán vị ngẫu nhiên nhưng bảo toàn tính logic.
5. **Bước 2.5**: Xuất kết quả:
   - Click **Xuất 4 file đề thi Word (.docx)**.
   - Click **Xuất Bảng Ma trận Đáp án Chéo OMR (.xlsx / .docx)**.

### Bước 3: Tình huống thực tế (Real-world Scenario)
- **Đề bài kiểm tra thực tế**: Trong đề có câu hỏi lý thuyết:
  > *Câu 18. Khẳng định nào sau đây về hàm số đồng biến trên $\mathbb{R}$ là đúng?*
  > *A. Đạo hàm $f'(x) \ge 0$ với mọi $x \in \mathbb{R}$ và bằng 0 tại hữu hạn điểm.*
  > *B. Hàm số không có điểm cực trị.*
  > *C. Đồ thị hàm số luôn đi lên từ trái sang phải.*
  > *D. Cả A, B và C đều đúng.*
- **Kết quả sau khi trộn**:
  - Tại mã đề 101: Câu 18 trở thành Câu 05. Ba phương án A, B, C được hoán vị ngẫu nhiên giữa nhau, nhưng **phương án D ("Cả A, B và C đều đúng") được giữ cố định 100% tại vị trí cuối cùng**.
  - Bảng OMR tự động ghi nhận đáp án đúng của từng mã đề tương ứng mà không cần giáo viên dò lại thủ công.

### Bước 4: Thực hành tóm tắt & Mẹo chuyên gia (Practice Summary & Pro-tips)
- **3 Điểm cốt lõi cần nhớ**:
  1. Luôn luôn tích chọn ô kiểm **'Khóa phương án phụ thuộc'** khi trộn đề có chứa các câu lý thuyết tổng hợp.
  2. Bảng OMR ma trận đáp án chéo được xuất đồng thời, sẵn sàng nạp vào các phần mềm chấm trắc nghiệm bằng điện thoại (như TnMaker, CamScanner) hoặc máy quét OMR quang học.
  3. Đối với đề thi theo định dạng GDPT 2018: Phần I và Phần III được hoán vị vị trí câu hỏi, Phần II giữ nguyên thứ tự 4 ý a-b-c-d để không làm sai lệch bài toán tích hợp.
- **Phím tắt vàng**: `F9` (Kích hoạt trộn đề ngay lập tức).

---

## BÀI 4: AI VẼ HÌNH TOÁN HỌC TIKZ XUẤT SẮC TỪ ẢNH CHỤP & MÔ TẢ TIẾNG VIỆT (TIKZVIEW)
- **Thời lượng dự kiến**: 12 phút
- **Phân hệ sử dụng**: `TikzView`
- **Mục tiêu**: Làm chủ quy trình vẽ hình học không gian, đồ thị hàm số và bảng biến thiên chuẩn vector học thuật, xuất ảnh 600 DPI sắc nét và chèn thẳng vào Microsoft Word chỉ với 3 phím tắt.

### Bước 1: Hook (Móc nối vấn đề)
> *"Thưa Thầy Cô, nỗi khổ lớn nhất của giáo viên dạy Toán khi soạn đề là khâu vẽ hình! Lấy hình trên mạng về thì mờ căm, in photo đen trắng nét đứt nét liền dính tịt vào nhau, học sinh không nhìn rõ đường vuông góc để làm bài. Tự ngồi vẽ bằng Geogebra hay Word thì mất 30 phút một hình chóp phức tạp. Hôm nay, tôi sẽ hướng dẫn Thầy Cô một 'phép màu' công nghệ: Chỉ cần gõ một câu tiếng Việt hoặc chụp ảnh phác thảo tay, AI sẽ tự động sinh hình vẽ TikZ độ nét 600 DPI và dán thẳng vào Word trong vòng 10 giây!"*

### Bước 2: Chuyển giao thao tác (Operation Transfer)
1. **Bước 2.1**: Mở tab **AI Vẽ hình TikZ (TikzView)** trên thanh điều hướng bên trái.
2. **Bước 2.2**: Nạp yêu cầu vẽ hình:
   - *Cách 1 (Dùng mẫu)*: Click ComboBox **Danh mục mẫu** (Hình phẳng 2D / Đồ thị / Bảng biến thiên tkz-tab / Hình không gian 3D) -> Chọn mẫu cần dùng (Ví dụ: `Hình chóp S.ABCD đáy hình vuông`). Mã nguồn mẫu sẽ lập tức nạp vào ô soạn thảo bên trái.
   - *Cách 2 (Dán ảnh mẫu)*: Dùng `Win + Shift + S` chụp ảnh hình vẽ từ sách hoặc hình vẽ tay -> Nhấn `Ctrl + V` dán vào ô Xem trước ảnh.
   - *Cách 3 (Nhập mô tả tiếng Việt)*: Gõ vào ô mô tả: *"Vẽ đồ thị hàm số bậc ba $y = x^3 - 3x + 1$ có đủ các điểm cực trị gióng nét đứt vào hai trục"*.
3. **Bước 2.3**: Kích hoạt AI Sinh mã:
   - Nhấn tổ hợp phím **`Ctrl + Shift + G`**: AI Gemini / 9Router sẽ sinh mã nguồn LaTeX TikZ chuẩn mực trong 3 giây.
4. **Bước 2.4**: Biên dịch và Kiểm tra hình vẽ:
   - Nhấn phím **`F5`** (hoặc `Ctrl + Enter`): Động cơ `pdflatex` sẽ biên dịch mã nguồn thành hình ảnh đồ họa vector siêu nét với độ phân giải **600 DPI**.
   - Hình vẽ hiển thị ngay lập tức tại khung xem trước bên phải.
5. **Bước 2.5**: Chèn thẳng vào Microsoft Word:
   - Nhấn tổ hợp phím **`Ctrl + Shift + W`**: Hình vẽ lập tức được sao chép vào bộ nhớ đệm và chèn chính xác tại vị trí con trỏ chuột trong văn bản Word đang mở!

### Bước 3: Tình huống thực tế (Real-world Scenario)
- **Đề bài thực tế**: Vẽ hình học không gian cho bài toán khoảng cách:
  > *"Cho hình chóp $S.ABC$ có đáy $ABC$ là tam giác đều cạnh $a$. Cạnh bên $SA$ vuông góc với mặt phẳng đáy và $SA = a\sqrt{3}$. Gọi $M$ là trung điểm của cạnh $BC$. Tính khoảng cách từ điểm $A$ đến mặt phẳng $(SBC)$."*
- **Thực hành trên TikzView**:
  1. Gõ mô tả hoặc nạp mẫu Chóp tam giác $S.ABC$.
  2. Bấm `Ctrl+Shift+G` -> Bấm `F5`.
  3. Kết quả hình vẽ hiện lên: Cạnh đáy $BC$ và các cạnh bên $SB, SC$ nét liền; cạnh $AB, AC, AM$ nét đứt; đường cao $SA$ nét đứt dựng thẳng đứng; có ký hiệu góc vuông chuẩn xác tại đỉnh $A$ và góc vuông giữa đường gióng $AH$ với $SM$.
  4. Bấm `Ctrl+Shift+W`: Hình vẽ xuất hiện ngay ngắn bên cạnh câu hỏi trong giáo án Word với kích thước chuẩn 7cm, nét vẽ đen trắng sắc sảo, in photo cực kỳ rõ nét.

### Bước 4: Thực hành tóm tắt & Mẹo chuyên gia (Practice Summary & Pro-tips)
- **3 Điểm cốt lõi cần nhớ**:
  1. Bộ 3 phím tắt vàng quyền lực: **`Ctrl + Shift + G`** (Sinh mã) -> **`F5`** (Biên dịch 600 DPI) -> **`Ctrl + Shift + W`** (Dán vào Word).
  2. Thư viện mẫu có sẵn hơn 20 mẫu hình học, đồ thị và bảng biến thiên tkz-tab thông dụng nhất của chương trình THPT.
  3. Hình vẽ xuất ra ở định dạng 600 DPI bảo đảm khi in offset hoặc photocopy hàng loạt không bao giờ bị vỡ nét hay mờ căm.
- **Mẹo chuyên gia**: Khi vẽ đồ thị hàm số lượng giác (như hàm số $y = \sin x$), trong mã TikZ hàm sin/cos nhận giá trị độ, vì vậy luôn kiểm tra công thức có chuyển đổi `deg(x)` hoặc để tham số `domain` hợp lý từ -3.14 đến 3.14.

---

## BÀI 5: THẨM ĐỊNH QC TỰ ĐỘNG & ĐÓNG GÓI NGÂN HÀNG CÂU HỎI CHUẨN IN ẤN (QCVIEW & QUESTIONBANKVIEW)
- **Thời lượng dự kiến**: 10 phút
- **Phân hệ sử dụng**: `QcView` & `QuestionBankView`
- **Mục tiêu**: Sử dụng công cụ QC quét sạch 100% lỗi logic và lỗi cú pháp trước khi in sao đề thi; đóng gói câu hỏi vào cơ sở dữ liệu SQLite dùng chung nội bộ cho tổ chuyên môn.

### Bước 1: Hook (Móc nối vấn đề)
> *"Kính thưa Thầy Cô, sự cố tồi tệ nhất của một giáo viên ra đề thi là sau khi phát đề cho hàng trăm học sinh làm bài được 15 phút thì phát hiện: Câu 12 có hai phương án A và C giống hệt nhau, hoặc Câu 25 quên chưa bôi đen đáp án đúng trong đề gốc! Cả hội đồng thi nhốn nháo, phải viết biên bản đính chính. Chưa kể, qua từng năm học, hàng nghìn câu hỏi hay bị thất lạc nằm rải rác ở hàng chục file Word trên máy tính cá nhân. Hãy để QcView trở thành 'người gác cổng' mẫn cán quét sạch mọi lỗi sai trước giờ in ấn, và QuestionBankView giúp Thầy Cô xây dựng kho tàng câu hỏi dùng trọn đời!"*

### Bước 2: Chuyển giao thao tác (Operation Transfer)
1. **Bước 2.1**: Mở tab **Kiểm định chất lượng (QcView)** trên thanh điều hướng bên trái.
2. **Bước 2.2**: Quét lỗi đề thi tự động:
   - Click nút **Nạp tệp đề thi cần kiểm định** -> Click nút đỏ **Bắt đầu thẩm định QC** (hoặc phím `F7`).
   - Động cơ QC rà soát toàn bộ đề thi qua 3 bộ lọc độc lập:
     * *Lọc lỗi Phương án*: Phát hiện câu hỏi trùng lặp phương án (ví dụ: A và B cùng nội dung), câu hỏi thiếu phương án D, câu hỏi chưa đánh dấu đáp án đúng.
     * *Lọc lỗi Cú pháp*: Phát hiện lệch cặp dấu dollar `$`, dấu ngoặc nhọn `{}` chưa đóng trong công thức toán.
     * *Lọc lỗi Ma trận*: Cảnh báo câu hỏi chưa được gán mức độ nhận thức (NB/TH/VD/VDC).
3. **Bước 2.3**: Xử lý lỗi tự động:
   - Click nút **Tự động sửa lỗi (Auto-Fix)** để hệ thống tự cân bằng cú pháp và làm sạch định dạng.
   - Nhấp đúp chuột vào từng dòng cảnh báo để nhảy thẳng đến vị trí câu hỏi cần sửa chữa trên ô soạn thảo.
4. **Bước 2.4**: Đóng gói vào Ngân hàng câu hỏi SQLite:
   - Chuyển sang tab **Ngân hàng câu hỏi (QuestionBankView)**.
   - Click **Nhập câu hỏi từ đề thi hiện tại**: Hệ thống tự động bóc tách từng câu thành các bản ghi độc lập.
   - Gán thẻ chuyên đề (ví dụ: `Giải tích 12 > Nguyên hàm - Tích phân`) và mức độ nhận thức.
   - Click **Lưu vào Ngân hàng SQLite**: Dữ liệu được lưu vĩnh viễn trong file cơ sở dữ liệu nhẹ, không sợ mất mạng.

### Bước 3: Tình huống thực tế (Real-world Scenario)
- **Tình huống thẩm định đề thi khảo sát chất lượng khối 12**:
  - Thầy Nam nạp một đề thi gồm 50 câu nộp lên từ các giáo viên trong tổ.
  - Sau 1.5 giây quét, QcView phát hiện 3 lỗi nghiêm trọng:
    * *Câu 14*: Hai phương án $B$ và $D$ đều ghi giá trị `${x = 2}$` (lỗi do người gõ đề copy/paste nhưng quên đổi số).
    * *Câu 28*: Thiếu dấu đóng `$` ở công thức tích phân làm xô lệch dòng text tiếp theo.
    * *Câu 39*: Chưa chọn đáp án đúng (tất cả 4 phương án đều không có dấu gạch chân hoặc dấu sao).
  - Thầy Nam bấm 'Tự động sửa lỗi' khắc phục ngay lỗi câu 28, sau đó điều chỉnh câu 14 và câu 39 chỉ trong 1 phút. Đề thi đạt trạng thái hoàn hảo 100% trước khi ký lệnh in sao 800 bản cho học sinh toàn trường.

### Bước 4: Thực hành tóm tắt & Mẹo chuyên gia (Practice Summary & Pro-tips)
- **3 Điểm cốt lõi cần nhớ**:
  1. Quy tắc an toàn in ấn: **Không bao giờ in đề thi khi QcView chưa báo trạng thái '0 Errors'**.
  2. Cơ sở dữ liệu SQLite lưu trữ offline 100% trên máy tính, bảo mật tuyệt đối, không lo rò rỉ đề thi lên internet.
  3. Có thể xuất file cơ sở dữ liệu `.db` chia sẻ qua mạng nội bộ để các giáo viên trong tổ cùng đóng góp và khai thác chung một ngân hàng đề.
- **Phím tắt vàng**: `F7` (Bắt đầu thẩm định QC đề thi).
- **Mẹo chuyên gia**: Định kỳ cuối mỗi học kỳ, hãy dùng tính năng 'Sao lưu Ngân hàng câu hỏi' trong SettingsView để tạo file dự phòng lưu vào Google Drive hoặc USB của tổ chuyên môn.
