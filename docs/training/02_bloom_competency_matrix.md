# TÀI LIỆU 02: KHUNG NĂNG LỰC CHUYỂN ĐỔI SỐ DỰA TRÊN THANG NHẬN THỨC BLOOM
## Ứng Dụng Trong Giảng Dạy & Biên Soạn Đề Thi Môn Toán - KHTN THPT
### Dự Án Chuyển Đổi Số: Nền Tảng MatrixExamAI Pro (.NET 10 Native Fluent UI)

---

## 1. NGUYÊN LÝ THIẾT KẾ KHUNG NĂNG LỰC SỐ BLOOM-MEA

Thang cấp độ tư duy nhận thức của Benjamin Bloom (được hiệu đính bởi Anderson & Krathwohl) gồm 6 bậc: **Nhận biết (Remembering) -> Thông hiểu (Understanding) -> Vận dụng (Applying) -> Phân tích (Analyzing) -> Đánh giá (Evaluating) -> Sáng tạo (Creating)**.

Khi áp dụng vào quá trình chuyển đổi số công tác biên soạn đề thi và tài liệu dạy học với phần mềm MatrixExamAI Pro, thang nhận thức này được tích hợp hữu cơ với **Khung năng lực số dành cho nhà giáo (Digital Competence Framework for Educators - DigCompEdu)**, giúp giáo viên không chỉ dừng lại ở việc "sử dụng phần mềm như một người thợ", mà nâng tầm thành "chuyên gia thiết kế học liệu số thông minh".

```
                          +-----------------------------------+
                          |           6. SÁNG TẠO            |
                          |  Thiết kế đề phân hóa cao, đóng   |
                          |  gói ngân hàng SQLite toàn trường |
                          +-----------------+-----------------+
                                            |
                               +------------+------------+
                               |      5. ĐÁNH GIÁ        |
                               |  Thẩm định độ khó mã đề,|
                               |  chuẩn hóa in ấn 600 DPI|
                               +------------+------------+
                                            |
                               +------------+------------+
                               |      4. PHÂN TÍCH       |
                               |  Đọc báo cáo QC, bắt lỗi|
                               |  trùng đáp án, lệch ma trận
                               +------------+------------+
                                            |
                               +------------+------------+
                               |      3. VẬN DỤNG        |
                               |  OCR ảnh đề, tạo đề 22c,|
                               |  vẽ hình TikZ dán Word  |
                               +------------+------------+
                                            |
                               +------------+------------+
                               |     2. THÔNG HIỂU       |
                               |  Hiểu cơ chế ${...}$,   |
                               |  khóa phương án phụ thuộc|
                               +------------+------------+
                                            |
                               +------------+------------+
                               |      1. NHẬN BIẾT       |
                               |  Nhớ vị trí Tab, phím tắt|
                               |  F5, Ctrl+V, thẻ ===CAU==|
                               +-------------------------+
```

---

## 2. MA TRẬN CHI TIẾT 6 CẤP ĐỘ NĂNG LỰC SỐ BLOOM - MATRIXEXAMAI

### CẤP ĐỘ 1: NHẬN BIẾT (REMEMBERING)

#### 1.1. Mô tả năng lực nhận thức & năng lực số
- Giáo viên có khả năng ghi nhớ, nhận diện các thành phần giao diện người dùng Fluent UI của MatrixExamAI.
- Nhớ được tên gọi và chức năng của 8 phân hệ cốt lõi: ConvertView, ExamMatrixView, TikzView, ShuffleView, QuestionBankView, QcView, SettingsView, DashboardView.
- Nhớ được cú pháp thẻ phân cách câu hỏi `===CAU===` và các ký hiệu mức độ nhận thức chuẩn (NB, TH, VD, VDC).
- Nhớ được các phím tắt công thái học thông dụng (`F5`, `Ctrl+V`, `Ctrl+Shift+G`, `Ctrl+Shift+W`, `Win+Shift+S`).

#### 1.2. Tính năng & Thao tác trên MatrixExamAI
- Nhận biết thanh điều hướng bên trái (Navigation Sidebar) để chuyển đổi giữa các tab công việc.
- Rà chuột qua các nút bấm trên thanh công cụ để đọc gợi ý phím tắt trên ToolTip.
- Nhận biết các chỉ báo trạng thái: Icon tròn xanh lá ("Sẵn sàng xuất Word"), chỉ báo phiên bản TeX ("pdflatex: Sẵn sàng").

#### 1.3. Tiêu chí đánh giá & Minh chứng đạt chuẩn
- **Tiêu chí**: Chỉ đúng 100% vị trí các phân hệ trên màn hình và phát biểu chính xác chức năng của từng phím tắt.
- **Minh chứng**: Hoàn thành bài trắc nghiệm nhận diện giao diện đạt điểm tuyệt đối 10/10 trong thời gian dưới 3 phút.

---

### CẤP ĐỘ 2: THÔNG HIỂU (UNDERSTANDING)

#### 2.1. Mô tả năng lực nhận thức & năng lực số
- Hiểu được nguyên lý hoạt động của cơ chế bao đóng công thức toán học `${...}$` trong việc bảo toàn ký tự và chuyển đổi sang công thức Word Equation native (OMML).
- Hiểu vì sao dấu gạch đứng trong biểu thức trị tuyệt đối `|x - 2|` dễ bị hiểu nhầm thành cột phân cách bảng Markdown nếu không có thuật toán bảo vệ riêng.
- Hiểu cơ chế hoạt động của thuật toán trộn đề hoán vị: Tại sao các phương án đặc thù ("Cả A và B đều đúng", "Tất cả các đáp án trên") bắt buộc phải được giữ cố định ở vị trí phương án D để không làm sai lệch tính logic của câu hỏi.
- Hiểu cấu trúc cấu tạo của mã nguồn đồ họa TikZ (khung `\begin{tikzpicture}`, hệ tọa độ, các lệnh `\draw`, `\node`, `\fill`).
- Hiểu cơ cấu 3 phần thi của đề thi tốt nghiệp THPT theo GDPT 2018 (Phần I: 12 câu trắc nghiệm nhiều lựa chọn; Phần II: 4 câu Đúng/Sai gồm 16 ý a-b-c-d; Phần III: 6 câu trả lời ngắn).

#### 2.2. Tính năng & Thao tác trên MatrixExamAI
- Giải thích được sự khác biệt giữa text thô và công thức toán sau khi chuẩn hóa.
- Hiểu ý nghĩa của bảng ma trận chéo đáp án OMR sinh ra sau khi trộn đề tại ShuffleView.
- Hiểu ý nghĩa các cảnh báo của bộ tiền kiểm tra TikzPreflightValidator (lỗi mất dấu chấm phẩy `;`, lỗi chưa đóng ngoặc nhọn `{}`).

#### 2.3. Tiêu chí đánh giá & Minh chứng đạt chuẩn
- **Tiêu chí**: Giải thích mạch lạc cho đồng nghiệp về nguyên tắc bảo vệ công thức toán và quy tắc phân bổ điểm số trong ma trận đề 22 câu.
- **Minh chứng**: Trả lời đúng các câu hỏi tình huống: "Tại sao phương án Cả A và B đều đúng không được đảo lên vị trí A?" và "Vì sao công thức toán cần bao đóng `${...}$` thay vì để text trần?".

---

### CẤP ĐỘ 3: VẬN DỤNG (APPLYING)

#### 2.1. Mô tả năng lực nhận thức & năng lực số
- Vận dụng thành thạo phần mềm để giải quyết các tác vụ biên soạn tài liệu giảng dạy hàng ngày.
- Nạp tài liệu đề thi thô dạng PDF hoặc Word cũ, thực hiện chuẩn hóa ra tài liệu Word mới với công thức toán chuẩn, bảng biểu ngay ngắn.
- Vận dụng AI Vision OCR: Chụp ảnh một câu hỏi khó từ nhóm trao đổi chuyên môn, dán trực tiếp (`Ctrl+V`) vào phần mềm để nhận diện thành văn bản có thể chỉnh sửa trong tích tắc.
- Thiết lập ma trận đề thi 22 câu cho bài kiểm tra 1 tiết hoặc thi thử, cân đối đúng tỷ lệ điểm số 10.0.
- Sinh mã TikZ từ mô tả tiếng Việt hoặc ảnh chụp phác thảo, biên dịch ra ảnh chất lượng cao 600 DPI và dán ngay vào giáo án Microsoft Word bằng tổ hợp phím `Ctrl+Shift+W`.
- Trộn đề hoán vị thành 4 mã đề thi chính thức kèm phiếu đáp án OMR phục vụ chấm thi trắc nghiệm.

#### 2.2. Tính năng & Thao tác trên MatrixExamAI
- Thao tác tại ConvertView: Chọn môn Toán/Lí/Hóa -> Nhấn 'Chuẩn hóa đề thi' -> Nhấn 'Xuất file Word (.docx)'.
- Thao tác tại TikzView: Nhập prompt tiếng Việt -> Nhấn `Ctrl+Shift+G` -> Nhấn `F5` -> Nhấn `Ctrl+Shift+W`.
- Thao tác tại ExamMatrixView: Chọn template 'Chuẩn BGD 2025' -> Bấm 'AI Soạn đề tự động' -> Xuất đề thi.

#### 2.3. Tiêu chí đánh giá & Minh chứng đạt chuẩn
- **Tiêu chí**: Biên soạn hoàn chỉnh 1 đề kiểm tra 1 tiết gồm 4 mã đề hoán vị, có ít nhất 2 hình vẽ TikZ 600 DPI trong thời gian không quá 20 phút.
- **Minh chứng**: Xuất trình được 4 file Word đề thi và 1 bảng đáp án OMR in ra giấy không có bất kỳ lỗi định dạng nào.

---

### CẤP ĐỘ 4: PHÂN TÍCH (ANALYZING)

#### 4.1. Mô tả năng lực nhận thức & năng lực số
- Có khả năng phân tích, mổ xẻ cấu trúc đề thi và báo cáo chất lượng để phát hiện sớm các nguy cơ rủi ro.
- Đọc hiểu và phân tích báo cáo kiểm định chất lượng (QC Report) từ phân hệ QcView.
- Phát hiện các lỗi tư duy ra đề: Câu hỏi có 2 phương án trùng nội dung, câu hỏi bị thiếu đáp án đúng, câu hỏi có độ dài phương án quá chênh lệch khiến học sinh dễ đoán mò.
- Phát hiện các lỗi cú pháp LaTeX tiềm ẩn: Mất cân bằng cặp dấu dollar `$`, thiếu dấu gạch chéo ngược `\` trước các hàm số chuẩn như `\sin`, `\cos`, `\ln`.
- Phân tích độ phân hóa của ma trận đề thi: Đối chiếu số lượng câu hỏi thực tế ở các mức Nhận biết - Thông hiểu - Vận dụng - Vận dụng cao so với mục tiêu sư phạm đề ra.

#### 4.2. Tính năng & Thao tác trên MatrixExamAI
- Khởi chạy phân hệ QcView trên tệp đề thi trước khi in ấn.
- Đọc danh sách phân loại lỗi theo mức độ nghiêm trọng: Error (Bắt buộc sửa), Warning (Cảnh báo chú ý), Suggestion (Gợi ý tối ưu).
- Sử dụng tính năng 'Tự động sửa lỗi' (Auto-Fix) và phân tích các thay đổi mà thuật toán đã áp dụng lên văn bản.
- Kiểm tra tính cân bằng độ khó giữa các mã đề sau khi trộn hoán vị tại ShuffleView.

#### 4.3. Tiêu chí đánh giá & Minh chứng đạt chuẩn
- **Tiêu chí**: Phát hiện và xử lý triệt để 100% các lỗi logic và cú pháp trong một đề thi thử nghiệm có cài cắm sẵn lỗi sai.
- **Minh chứng**: Bản báo cáo QC sau khi xử lý đạt trạng thái sạch hoàn toàn (0 Errors, 0 Critical Warnings).

---

### CẤP ĐỘ 5: ĐÁNH GIÁ (EVALUATING)

#### 5.1. Mô tả năng lực nhận thức & năng lực số
- Đánh giá, thẩm định chất lượng học liệu số dựa trên các tiêu chuẩn khảo thí khoa học và quy chuẩn thẩm mỹ sư phạm.
- So sánh, thẩm định độ tương đương về độ khó và tính công bằng giữa các mã đề thi hoán vị (bảo đảm học sinh làm mã đề 101 và 102 có xác suất gặp câu hỏi khó ở các vị trí tương đồng, không bị lệch tâm lý).
- Thẩm định độ chính xác hình học và tính trực quan của các hình vẽ TikZ: Kiểm tra tỷ lệ hình học, góc nghiêng của hình không gian, vị trí tiệm cận của đồ thị hàm số, tính đúng đắn của bảng xét dấu tkz-tab.
- Thẩm định độ sắc nét in ấn: So sánh bản in photo thực tế giữa hình ảnh cắt dán 72 DPI truyền thống với hình TikZ 600 DPI của phần mềm để đưa ra quyết định chuẩn hóa.
- Đánh giá hiệu quả của từng prompt AI để không ngừng tinh chỉnh câu lệnh đạt độ chính xác cao nhất.

#### 5.2. Tính năng & Thao tác trên MatrixExamAI
- Sử dụng công cụ xem trước Split View và bộ phóng to thu nhỏ (Zoom Preview) trên TikzView để soi từng điểm ảnh của hình vẽ vector.
- Đối chiếu ma trận câu hỏi giữa các đề thi hoán vị trong ShuffleView.
- Thiết lập các bộ tiêu chí thẩm định (Checklist) trong quy trình duyệt đề thi của tổ chuyên môn.

#### 5.3. Tiêu chí đánh giá & Minh chứng đạt chuẩn
- **Tiêu chí**: Đưa ra biên bản thẩm định đề thi định kỳ cấp trường, có nhận xét phản biện xác đáng về chất lượng hình vẽ, tính logic của các câu hỏi Đúng/Sai và tính tương đương giữa các mã đề.
- **Minh chứng**: Ký duyệt biên bản nghiệm thu đề thi không có khiếu nại chuyên môn từ giáo viên và học sinh sau kỳ thi.

---

### CẤP ĐỘ 6: SÁNG TẠO (CREATING)

#### 6.1. Mô tả năng lực nhận thức & năng lực số
- Năng lực kiến tạo học liệu số ở cấp độ chuyên gia: Tự thiết kế các cấu trúc đề thi sáng tạo, các dạng bài toán thực tế tích hợp STEM/KHTN chưa từng có trong sách giáo khoa.
- Sáng tạo các cấu trúc hình vẽ TikZ phức tạp, kết hợp đa tầng: Đồ thị hàm hợp liên kết trực tiếp với bảng biến thiên, mô hình không gian cắt khối lăng trụ bằng mặt phẳng nghiêng, sơ đồ mạch điện phức hợp cho môn Vật lí, mô hình cấu trúc phân tử hữu cơ 3D cho môn Hóa học.
- Đóng gói và phát hành Ngân hàng câu hỏi dùng chung (Shared Question Bank) trên nền tảng SQLite với hàng nghìn câu hỏi chuẩn hóa được phân loại chi tiết theo chương mục, bài học và mức độ nhận thức.
- Xây dựng quy trình làm việc phối hợp (Collaborative Workflow) cho toàn trường hoặc cụm chuyên môn liên trường.

#### 6.2. Tính năng & Thao tác trên MatrixExamAI
- Sử dụng QuestionBankView: Tạo chủ đề mới, nhập hàng loạt câu hỏi từ các file Word chuẩn hóa, xuất gói dữ liệu `.db` phân phối cho đồng nghiệp.
- Viết các prompt AI bậc cao kết hợp hình ảnh mẫu phác thảo tay để sinh ra các mô hình hình học chưa có trong thư viện mẫu mặc định.
- Tự thiết lập các mẫu ma trận đề thi tùy biến cho các kỳ thi học sinh giỏi, khảo sát năng lực đầu năm, thi thử tốt nghiệp THPT.

#### 6.3. Tiêu chí đánh giá & Minh chứng đạt chuẩn
- **Tiêu chí**: Xuất bản một gói Ngân hàng câu hỏi số hóa hoàn chỉnh gồm tối thiểu 200 câu hỏi chuẩn hóa chất lượng cao kèm hình vẽ TikZ 600 DPI, chia sẻ thành công cho tổ chuyên môn.
- **Minh chứng**: Gói dữ liệu SQLite được toàn thể giáo viên trong tổ tích hợp vào máy tính cá nhân và tái sử dụng hiệu quả trong các đợt thi định kỳ.

---

## 3. BẢNG TỔNG HỢP ÁNH XẠ NĂNG LỰC SỐ BLOOM - MATRIXEXAMAI PRO

| Cấp độ Bloom | Năng lực Số Cốt lõi | Phân hệ MEA Chuyên trách | Thao tác Đặc trưng | Chuẩn Đầu ra Tối thiểu |
|:---:|---|---|---|---|
| **1. Nhận biết** | Ghi nhớ giao diện, phím tắt, thẻ dữ liệu | Toàn bộ 8 Tab (Navigation Sidebar) | Rà chuột xem ToolTip phím tắt, nhận diện thẻ `===CAU===` | Thuộc 100% phím tắt vàng và 8 phân hệ |
| **2. Thông hiểu** | Hiểu cơ chế bao đóng `${...}$`, khóa phương án | ConvertView, ShuffleView, TikzPreflight | Giải thích nguyên lý chuyển đổi sang Word Equation | Đạt điểm tuyệt đối bài test lý thuyết nền tảng |
| **3. Vận dụng** | Chuẩn hóa đề, OCR ảnh, vẽ hình TikZ, trộn đề | ConvertView, TikzView, ExamMatrixView | `Win+Shift+S` -> `Ctrl+V` -> `Ctrl+Shift+G` -> `F5` -> `Ctrl+Shift+W` | Hoàn thành 1 đề thi hoàn chỉnh trong < 20 phút |
| **4. Phân tích** | Quét lỗi logic đề thi, soát cú pháp LaTeX | QcView, TikzPreflightValidator | Chạy QC Engine, lọc lỗi trùng phương án, lỗi lệch dollar | Sửa sạch 100% lỗi trên đề thi thực nghiệm |
| **5. Đánh giá** | Thẩm định tính tương đương mã đề, độ nét in ấn | ShuffleView, TikzView (Zoom 600 DPI) | Thẩm định ma trận OMR, so sánh bản in thực tế | Lập biên bản thẩm định đề thi đạt chuẩn in ấn |
| **6. Sáng tạo** | Tạo đề phân hóa cao, thiết kế TikZ đa tầng, ngân hàng | QuestionBankView (SQLite), Custom Prompts | Xuất bản gói ngân hàng câu hỏi 200 câu cho tổ | Chuyển giao gói câu hỏi SQLite dùng chung toàn trường |
