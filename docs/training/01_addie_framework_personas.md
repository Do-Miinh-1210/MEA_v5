# TÀI LIỆU 01: KHUNG ĐÀO TẠO THỰC CHIẾN THEO MÔ HÌNH ADDIE
## Dành Cho Giáo Viên & Tổ Chuyên Môn Toán - Khoa Học Tự Nhiên THPT
### Dự Án Chuyển Đổi Số: Nền Tảng MatrixExamAI Pro (.NET 10 Native Fluent UI)

---

## 1. TỔNG QUAN VÀ BỐI CẢNH SƯ PHẠM

Trong bối cảnh triển khai Chương trình Giáo dục Phổ thông 2018 (GDPT 2018) và định dạng cấu trúc đề thi tốt nghiệp THPT mới từ năm 2025 của Bộ Giáo dục và Đào tạo (với 3 phần thi: Trắc nghiệm 4 lựa chọn, Trắc nghiệm Đúng/Sai, Trả lời ngắn), khối lượng công việc và áp lực biên soạn đề kiểm tra, đánh giá của giáo viên bộ môn Toán và Khoa học Tự nhiên (Vật lí, Hóa học, Sinh học) tăng lên gấp nhiều lần.

Việc ứng dụng mô hình thiết kế dạy học **ADDIE** (Analysis – Design – Development – Implementation – Evaluation) bảo đảm chương trình đào tạo và chuyển giao công nghệ phần mềm MatrixExamAI không chỉ mang tính chuyển giao kỹ thuật thuần túy, mà là một quy trình sư phạm bài bản, thấu cảm với rào cản tâm lý của từng nhóm giáo viên, bám sát năng lực số thực tế và mang lại hiệu quả bền vững cho nhà trường.

```
+---------------+     +---------------+     +-----------------+     +--------------------+     +------------------+
|  A (Analysis) | --> |  D (Design)   | --> | D (Development) | --> | I (Implementation) | --> |  E (Evaluation)  |
| Phân tích     |     | Thiết kế mục  |     | Phát triển học  |     | Triển khai 3 giai  |     | Đánh giá vòng    |
| đối tượng &   |     | tiêu SMART &  |     | liệu, Job Aids, |     | đoạn: Pilot ->     |     | lặp, cải tiến    |
| Tech Gap      |     | Curriculum    |     | Prompt Catalog  |     | Rollout -> Thể chế |     | sau kỳ thi       |
+---------------+     +---------------+     +-----------------+     +--------------------+     +------------------+
```

---

## 2. GIAI ĐOẠN A: PHÂN TÍCH NHU CẦU & ĐỐI TƯỢNG (ANALYSIS)

### 2.1. Chân Dung 3 Nhóm Giáo Viên Điển Hình (Teacher Personas)

Để chương trình đào tạo thành công, không thể áp dụng một giáo trình rập khuôn cho toàn bộ hội đồng sư phạm. Cần phân tích sâu sắc 3 chân dung giáo viên điển hình tại các trường THPT Việt Nam hiện nay:

```
+---------------------------------------------------------------------------------------------------------+
|                                    CHÂN DUNG GIÁO VIÊN ĐIỂN HÌNH (PERSONAS)                             |
+------------------------------------+------------------------------------+-------------------------------+
|  1. THẦY HÙNG (52 tuổi)             |  2. CÔ MAI (29 tuổi)               |  3. THẦY NAM (40 tuổi)        |
|  - 25 năm kinh nghiệm dạy Toán      |  - 5 năm kinh nghiệm dạy Toán      |  - Tổ trưởng Chuyên môn KHTN  |
|  - Thói quen: Word cũ, MathType     |  - Thói quen: ChatGPT, Canva, Web  |  - Trọng trách: Duyệt đề khối |
|  - Rào cản: Sợ lỗi định dạng, sợ    |  - Bức xúc: Công thức vỡ vụn, hình |  - Mục tiêu: Chuẩn 22 câu BGD,|
|    cú pháp lệnh, thao tác chậm      |    mờ 72 DPI, mất công chỉnh sửa   |    QC quét lỗi, kho dùng chung|
+------------------------------------+------------------------------------+-------------------------------+
```

#### Persona 1: Thầy Hùng – "Cựu binh dày dạn, cẩn trọng nhưng e ngại công nghệ"
- **Đặc điểm nhân khẩu & kinh nghiệm**: 52 tuổi, 25 năm đứng lớp giảng dạy môn Toán tại trường THPT vùng thị xã. Đã quen thuộc với bảng phấn, giáo án in và phần mềm Microsoft Word 2003/2010 kết hợp MathType 6.x suốt hai thập kỷ.
- **Kỹ năng công nghệ hiện tại**: Cơ bản. Gõ bàn phím tốc độ trung bình (thường dùng 2-4 ngón), biết tải file trên mạng, biết copy/paste cơ bản. Rất sợ khi màn hình xuất hiện thông báo lỗi tiếng Anh hoặc hộp thoại lạ.
- **Nỗi đau & Rào cản tâm lý**:
  - Sợ làm hỏng định dạng tài liệu Word đã tích lũy nhiều năm.
  - Ngại học các cú pháp lệnh phức tạp (như mã nguồn LaTeX, thẻ HTML hay phím tắt khó nhớ).
  - Thường xuyên mất 3 - 4 tiếng mỗi đêm chỉ để căn lề, sửa lỗi nhảy dòng khi sao chép tài liệu ôn tập cho học sinh.
- **Động lực chuyển đổi**: Muốn giảm bớt thời gian thức khuya chuẩn bị đề ôn tập, muốn tài liệu in ra học sinh không bị lỗi font chữ hay nhảy trang, muốn bảo vệ thị lực và sức khỏe.
- **Chiến lược tiếp cận & Chuyển giao**:
  - Tuyệt đối không dạy cú pháp lập trình hay lý thuyết trừu tượng.
  - Thiết kế quy trình "1 chạm": Mở phần mềm -> Kéo thả file PDF -> Nhấn 1 nút 'Chuẩn hóa' -> Mở file Word kết quả.
  - Ngôn ngữ giao diện 100% tiếng Việt rõ ràng, cỡ chữ hiển thị to, màu sắc tương phản cao.
  - Bố trí đồng nghiệp trẻ (như Cô Mai) kèm cặp 1-1 theo phương thức "cầm tay chỉ việc".

#### Persona 2: Cô Mai – "Thế hệ số tiên phong, đòi hỏi tốc độ và thẩm mỹ đỉnh cao"
- **Đặc điểm nhân khẩu & kinh nghiệm**: 29 tuổi, 5 năm kinh nghiệm giảng dạy môn Toán và phụ trách câu lạc bộ STEM của trường THPT chuyên/trọng điểm.
- **Kỹ năng công nghệ hiện tại**: Nhanh nhạy, thành thạo Office 365, Canva, thường xuyên ứng dụng các công cụ AI tạo sinh (ChatGPT, Claude, Gemini web) để tìm kiếm ý tưởng bài tập mới.
- **Nỗi đau & Rào cản kỹ thuật**:
  - Mất kiên nhẫn khi phải sao chép công thức toán từ AI web về Word vì công thức bị chuyển thành text thô dạng `$x^2$` hoặc mã LaTeX vỡ vụn, phải dùng add-in chuyển đổi từng dòng rất tốn thời gian.
  - Hình vẽ đồ thị hàm số và hình học không gian chụp từ màn hình hoặc tải trên mạng khi in photo ra giấy kiểm tra có độ phân giải thấp (72 DPI), bị lem mực, nét đứt nét liền dính tịt vào nhau khiến học sinh khiếu nại.
  - Cần một công cụ khép kín: Sinh đề -> Trộn đề -> Vẽ hình vector/sắc nét -> Xuất bản Word chuẩn in ấn.
- **Động lực chuyển đổi**: Tối ưu hóa hiệu suất làm việc gấp 5 - 10 lần, tạo ra các đề thi thử và chuyên đề ôn tập có tính thẩm mỹ chuyên nghiệp chuẩn sách giáo khoa, chia sẻ chuyên môn trên các diễn đàn giáo viên.
- **Chiến lược tiếp cận & Chuyển giao**:
  - Chuyển giao hệ thống phím tắt công thái học nâng cao (`Ctrl+Shift+G`, `F5`, `Ctrl+Shift+W`).
  - Hướng dẫn khai thác tối đa phân hệ **TikzView** với chất lượng xuất ảnh 600 DPI và khả năng dán trực tiếp vào Word trong 1 giây.
  - Định vị Cô Mai trở thành "Giáo viên hạt nhân" (Key Opinion Leader - KOL) của trường để lan tỏa giải pháp cho tổ chuyên môn.

#### Persona 3: Thầy Nam – "Tổ trưởng chuyên môn, người gác cổng chuẩn mực và hiệu năng"
- **Đặc điểm nhân khẩu & kinh nghiệm**: 40 tuổi, 17 năm công tác, Tổ trưởng tổ Toán – Tin kiêm thành viên Hội đồng ra đề thi cấp Sở GD&ĐT.
- **Kỹ năng công nghệ hiện tại**: Khá. Thành thạo các phần mềm quản lý điểm, trộn đề trắc nghiệm cổ điển (McMix, Young Mix), hiểu rõ cấu trúc ngân hàng câu hỏi.
- **Nỗi đau & Trọng trách quản lý**:
  - Chịu trách nhiệm trực tiếp về tính chính xác của đề thi chung khối 10, 11, 12 cho hơn 800 học sinh. Rất sợ tình trạng lỗi đáp án do phần mềm trộn hoán vị bị lỗi các phương án phụ thuộc ("Cả A và B đều đúng", "Không có đáp án nào").
  - Mệt mỏi vì phải duyệt thủ công hàng trăm câu hỏi nộp lên từ các giáo viên trong tổ với định dạng lộn xộn, người dùng MathType, người gõ Equation Word, người cắt ảnh dán tạm bợ.
  - Thiếu một công cụ số hóa đồng bộ ma trận đề thi 22 câu theo đúng Thông tư và hướng dẫn khảo thí mới nhất của Bộ GD&ĐT.
- **Động lực chuyển đổi**: Chuẩn hóa toàn bộ quy trình ra đề và kiểm tra đánh giá của tổ; xây dựng ngân hàng câu hỏi dùng chung nội bộ trên định dạng SQLite nhẹ, bảo mật; tự động hóa khâu thẩm định (QC) phát hiện lỗi sai trước khi ký duyệt in sao đề thi.
- **Chiến lược tiếp cận & Chuyển giao**:
  - Tập trung vào tính năng **ExamMatrixView** (Ma trận chuẩn 22 câu 3 phần: 12 TN, 4 Đ/S, 6 TLN cân đối 10.0 điểm).
  - Đào tạo chuyên sâu phân hệ **QcView** (Kiểm định tự động: phát hiện trùng phương án, sót đáp án đúng, lỗi dấu dollar).
  - Hướng dẫn thiết lập và sao lưu **QuestionBankView** (Ngân hàng dữ liệu SQLite offline dùng chung trong mạng nội bộ trường).

---

### 2.2. Phân Tích Khoảng Trống Kỹ Năng Số (Tech Gap Analysis)

Bảng đối chiếu toàn diện khoảng cách giữa phương pháp biên soạn đề thi thủ công truyền thống và quy trình tự động hóa tích hợp trên nền tảng MatrixExamAI Pro:

| Hạng mục Tác vụ | Phương pháp Thủ công Truyền thống | Quy trình Tự động hóa MatrixExamAI Pro | Khoảng trống Kỹ năng Cần bù đắp |
|---|---|---|---|
| **1. Trích xuất tài liệu từ PDF/Ảnh** | - Gõ lại thủ công từng từ trên Word.<br>- Mất 120 - 180 phút/đề thi 50 câu.<br>- Rất dễ sai sót chỉ số trên/dưới. | - Trích xuất text qua engine PdfPig.<br>- AI Vision OCR từ ảnh chụp Clipboard (`Ctrl+V`).<br>- Hoàn tất chuẩn hóa trong 30 giây - 2 phút. | Kỹ năng chụp ảnh màn hình sạch (`Win+Shift+S`), thao tác dán (`Ctrl+V`) và chọn profile môn học phù hợp. |
| **2. Định dạng Công thức Toán học** | - Bật MathType gõ từng công thức.<br>- Thường xuyên bị lỗi font MathType khi chuyển máy in.<br>- Dấu trị tuyệt đối `\|x\|` bị Word hiểu nhầm thành kẻ bảng. | - Tự động bao đóng chuẩn `${...}$`.<br>- Thuật toán bảo vệ dấu trị tuyệt đối `\|x\|`.<br>- Xuất sang Native Word Equation chuẩn OMML hiển thị sắc nét trên mọi phiên bản Word. | Hiểu nguyên lý kẹp công thức `${...}$` thay vì cố gắng chỉnh sửa từng ký tự toán bằng chuột. |
| **3. Vẽ Hình học & Đồ thị Hàm số** | - Chụp màn hình từ Geogebra/sách cũ (72 DPI).<br>- Ảnh mờ, răng cưa, đen sì khi in photo đề thi.<br>- Học sinh thường xuyên khiếu nại nét vẽ dính vào nhau. | - Tích hợp engine biên dịch TikZ chuẩn học thuật.<br>- Xuất file ảnh độ phân giải cao **600 DPI**.<br>- Dán trực tiếp vào Word qua Clipboard (`Ctrl+Shift+W`). | Kỹ năng viết prompt mô tả hình học bằng tiếng Việt và thao tác phím tắt biên dịch `F5`. |
| **4. Xây dựng Ma trận Đề thi** | - Kẻ bảng Excel tính nhẩm tỷ lệ câu hỏi nhận thức.<br>- Dễ mất cân đối tổng điểm 10.0 khi áp dụng định dạng mới GDPT 2018 (3 phần thi). | - **ExamMatrixView** tích hợp sẵn template chuẩn Bộ GD&ĐT 2025: 12 TN (3đ) + 4 Đ/S (4đ) + 6 TLN (3đ) = 10.0đ.<br>- Tự động cân bằng số câu theo ma trận NB-TH-VD-VDC. | Kỹ năng thiết lập tỷ lệ phân hóa nhận thức và liên kết câu hỏi từ ngân hàng câu hỏi. |
| **5. Trộn Đề Hoán vị & Bảng Đáp án** | - Trộn bằng phần mềm cũ hay bị đảo lộn câu hỏi mẹ con hoặc hoán vị phương án phụ thuộc ("Cả A và B đều đúng").<br>- Phải dò mắt lập bảng đáp án từng mã đề rất dễ nhầm. | - Thuật toán **ShuffleView** thông minh: tự động phát hiện và cố định phương án phụ thuộc.<br>- Xuất đồng thời 4 mã đề Word + 1 ma trận đáp án chéo OMR phục vụ chấm tự động. | Kỹ năng kiểm tra tùy chọn 'Khóa phương án phụ thuộc' và đọc hiểu bảng ma trận đáp án chéo OMR. |
| **6. Thẩm định & Kiểm duyệt Đề (QC)** | - Giáo viên đọc dò từng chữ trên bản in giấy.<br>- Dễ sót lỗi trùng 2 phương án A và C, sót câu chưa chọn đáp án đúng. | - **QcView** quét tự động 100% câu hỏi trong 2 giây.<br>- Báo cáo chi tiết: Trùng phương án, Thiếu đáp án, Lệch cú pháp LaTeX dollar. | Kỹ năng đọc báo cáo QC, định vị số thứ tự câu lỗi và nhấn nút 'Tự động sửa lỗi' (Auto-Fix). |

---

### 2.3. Yêu Cầu Hạ Tầng Công Nghệ & Môi Trường Vận Hành

Để bảo đảm ứng dụng MatrixExamAI Pro vận hành trơn tru trên máy tính của giáo viên tại nhà trường và gia đình, cấu hình kỹ thuật được quy định chi tiết:

```
+---------------------------------------------------------------------------------------------------------+
|                                    YÊU CẦU CẤU HÌNH HỆ THỐNG MÁY TÍNH                                   |
+------------------------------------+------------------------------------+-------------------------------+
|  THÔNG SỐ                          |  CẤU HÌNH TỐI THIỂU (MINIMUM)      |  CẤU HÌNH KHUYẾN NGHỊ (IDEAL) |
+------------------------------------+------------------------------------+-------------------------------+
|  Bộ vi xử lý (CPU)                 |  Intel Core i3 Gen 4 / AMD Ryzen 3 |  Intel Core i5 Gen 8+ / Ryzen5|
|  Bộ nhớ trong (RAM)                |  4.0 GB                            |  8.0 GB trở lên               |
|  Ổ đĩa lưu trữ                     |  Trống 2.0 GB (HDD)                |  Trống 5.0 GB (SSD NVMe)      |
|  Hệ điều hành                      |  Windows 10 64-bit (Build 1909+)   |  Windows 11 64-bit (Mới nhất) |
|  Môi trường .NET                   |  .NET 10 Desktop Runtime           |  .NET 10 Desktop Runtime      |
|  Microsoft Office                  |  MS Word 2016 (64-bit)             |  MS Word 2019/2021/Office 365 |
|  Bổ trợ Word Add-in                |  MatrixExamAI Word Add-in (COM)    |  MatrixExamAI Word Add-in     |
|  Phân phối TeX (Biên dịch TikZ)    |  MiKTeX Portable (Cơ bản)          |  TeX Live 2023+ hoặc MiKTeX   |
|  Kết nối Mạng                      |  1 Mbps (Kết nối API Gemini)       |  Internet băng thông rộng     |
+------------------------------------+------------------------------------+-------------------------------+
```

---

## 3. GIAI ĐOẠN D: THIẾT KẾ MỤC TIÊU & CHƯƠNG TRÌNH ĐÀO TẠO (DESIGN)

### 3.1. Mục Tiêu Học Tập Tổng Thể Theo Mô Hình SMART

Khóa tập huấn chuyển giao công nghệ được thiết kế bảo đảm 5 tiêu chí SMART:

- **S – Specific (Cụ thể)**: 100% giáo viên tham gia nắm vững quy trình 4 bước chuẩn: (1) Chuẩn hóa tài liệu thô -> (2) Tạo ma trận đề chuẩn 22 câu Bộ GD&ĐT -> (3) Biên tập & chèn hình vẽ TikZ 600 DPI -> (4) Thẩm định QC và xuất 4 mã đề hoán vị kèm bảng OMR.
- **M – Measurable (Đo lường được)**: 
  - Đạt tối thiểu **80/100 điểm** trong bài thi thực hành cuối khóa.
  - Rút ngắn thời gian biên soạn 1 đề kiểm tra 1 tiết từ trung bình 180 phút xuống dưới **25 phút/đề**.
  - Đạt **0% lỗi sai lệch đáp án** trên các mã đề hoán vị.
- **A – Achievable (Khả thi)**: Chương trình được phân nhỏ thành các vi khóa học 5-15 phút, có giàn giáo hỗ trợ sư phạm (Scaffolding), giáo viên kỹ năng cơ bản (như Thầy Hùng) hoàn toàn có thể làm chủ sau 2 tuần.
- **R – Relevant (Phù hợp & Thiết thực)**: Giải quyết trực tiếp nhiệm vụ trọng tâm năm học: biên soạn đề thi học kỳ và đề thi tốt nghiệp THPT theo đúng cấu trúc đề minh họa mới nhất của Bộ GD&ĐT.
- **T – Time-bound (Rõ ràng về thời gian)**: Hoàn thành khóa đào tạo tập trung trong **4 buổi (tổng 12 tiết)**; theo dõi và đo lường sự thay đổi hành vi sau **30 ngày** và **60 ngày**.

---

### 3.2. Khung Chương Trình Đào Tạo Tích Hợp (Curriculum Framework)

Chương trình được cấu trúc thành 6 Module liên hoàn từ cơ bản đến chuyên sâu:

```
+---------------------------------------------------------------------------------------------------------+
|                                  KHUNG CHƯƠNG TRÌNH ĐÀO TẠO 6 MODULE                                     |
+----------+------------------------------------------------------------------+-----------+---------------+
| MODULE   | TÊN MODULE & NỘI DUNG TRỌNG TÂM                                  | THỜI LƯỢNG| ĐỐI TƯỢNG ƯU TIÊN|
+----------+------------------------------------------------------------------+-----------+---------------+
| Mod 01   | Nhập môn MatrixExamAI & Chuẩn hóa Tài liệu Toán Native Word      | 2 giờ     | Tất cả (Thầy Hùng)
| Mod 02   | AI Vision OCR Đề thi từ Ảnh chụp & Clipboard (Ctrl+V)            | 2 giờ     | Tất cả (Cô Mai)
| Mod 03   | Thiết lập Ma trận Đề 22 câu Chuẩn Bộ GD&ĐT 2025                  | 2 giờ     | Thầy Nam, Thầy Hùng
| Mod 04   | AI Vẽ hình Toán học TikZ 600 DPI & Tích hợp Microsoft Word      | 2.5 giờ   | Cô Mai, Thầy Hùng
| Mod 05   | Trộn Đề Hoán vị 4 Mã đề & Xuất Ma trận Đáp án Chéo OMR           | 1.5 giờ   | Tất cả giáo viên
| Mod 06   | Thẩm định QC Đề thi & Quản trị Ngân hàng Câu hỏi SQLite          | 2 giờ     | Thầy Nam, Tổ phó
+----------+------------------------------------------------------------------+-----------+---------------+
| TỔNG CỘNG| 6 MODULE LÝ THUYẾT & THỰC HÀNH TỔNG HỢP                          | 12 GIỜ    | CẤP CHỨNG NHẬN|
+----------+------------------------------------------------------------------+-----------+---------------+
```

---

### 3.3. Chiến Lược Sư Phạm Hiện Đại

#### 1. Chiến lược "Learn by Doing" (Học qua Thực hành Thực chiến)
- 80% thời lượng khóa học là giáo viên thao tác trực tiếp trên máy tính cá nhân.
- Không sử dụng đề thi mẫu trừu tượng. Giáo viên mang trực tiếp đề kiểm tra giữa kỳ, học kỳ thực tế của chính mình đến lớp tập huấn để thực hành chuẩn hóa ngay tại chỗ.

#### 2. Chiến lược "Scaffolding" (Dựng giàn giáo nhận thức)
Quá trình chuyển giao kỹ năng tuân thủ nghiêm ngặt 3 giai đoạn:
1. *Giàn giáo cấp 1 (Mẫu có sẵn - Template-driven)*: Giáo viên chọn các mẫu có sẵn trong thư viện (ComboBox) và bấm áp dụng để thấy ngay thành quả.
2. *Giàn giáo cấp 2 (Tùy biến có hướng dẫn - Guided Customization)*: Giáo viên thay đổi tham số, chỉnh sửa nội dung câu chữ trên nền mẫu đã nạp.
3. *Giàn giáo cấp 3 (Tự chủ sáng tạo - Autonomous Creation)*: Giáo viên tự viết prompt tiếng Việt, phối hợp các phân hệ và xuất bản đề thi độc lập không cần hỗ trợ.

#### 3. Phương pháp "Micro-learning" (Vi học tập 5 - 15 phút)
Mỗi bài học được thiết kế cô đọng, giải quyết dứt điểm đúng 1 thao tác kỹ thuật, có thể theo dõi trên điện thoại hoặc máy tính trong giờ nghỉ giải lao 10 phút giữa hai tiết dạy.

---

## 4. GIAI ĐOẠN D: PHÁT TRIỂN HỌC LIỆU & CÔNG CỤ HỖ TRỢ (DEVELOPMENT)

### 4.1. Bộ Tài Liệu Hướng Dẫn Tác Vụ (Job Aids)

Bộ Job Aid cầm tay được in màu 2 mặt, ép plastic và phát cho từng giáo viên đặt tại bàn làm việc:

```
+---------------------------------------------------------------------------------------------------------+
|                               JOB AID: QUY TRÌNH 5 BƯỚC SOẠN ĐỀ HOÀN CHỈNH                             |
+---------------------------------------------------------------------------------------------------------+
|                                                                                                         |
|  [BƯỚC 1: NẠP & CHUẨN HÓA]                                                                              |
|  Mở ConvertView -> Kéo file Word/PDF hoặc nhấn Ctrl+V dán ảnh đề -> Nhấn 'Chuẩn hóa đề thi'.          |
|  *Kiểm tra*: Nhãn xanh 'Sẵn sàng xuất Word' sáng lên.                                                  |
|                                                                                                         |
|  [BƯỚC 2: MA TRẬN ĐỀ THI]                                                                               |
|  Mở ExamMatrixView -> Chọn Template 'Chuẩn BGD 2025 (22 câu)' -> Chọn mức độ nhận thức -> Bấm 'Sinh đề'.|
|  *Kiểm tra*: Tổng điểm hiển thị chính xác 10.0 / 10.0 điểm.                                             |
|                                                                                                         |
|  [BƯỚC 3: AI VẼ HÌNH TIKZ]                                                                              |
|  Mở TikzView -> Nhập mô tả tiếng Việt hoặc Ctrl+V dán ảnh mẫu -> Ctrl+Shift+G -> F5 biên dịch          |
|  -> Nhấn Ctrl+Shift+W dán thẳng hình 600 DPI vào văn bản Word.                                          |
|                                                                                                         |
|  [BƯỚC 4: THẨM ĐỊNH QC]                                                                                 |
|  Mở QcView -> Nhấn 'Bắt đầu kiểm định QC' -> Kiểm tra danh sách cảnh báo -> Nhấn 'Tự động sửa lỗi'.   |
|  *Kiểm tra*: Số lượng lỗi nghiêm trọng (Errors) về 0.                                                   |
|                                                                                                         |
|  [BƯỚC 5: TRỘN ĐỀ & XUẤT BẢN]                                                                           |
|  Mở ShuffleView -> Nhập 4 mã đề (101, 102, 103, 104) -> Tích 'Khóa phương án phụ thuộc'                 |
|  -> Bấm 'Trộn đề hoán vị' -> Nhận 4 file Word đề thi và 1 file ma trận đáp án chéo OMR.                 |
+---------------------------------------------------------------------------------------------------------+
```

---

### 4.2. Bảng Tra Cứu Phím Tắt Vàng Công Thái Học (Cheat Sheet)

Bảng tra cứu các phím tắt nhanh được tối ưu hóa cho thao tác 1 tay của giáo viên:

```
+---------------------------------------------------------------------------------------------------------+
|                                   BẢNG PHÍM TẮT VÀNG TRÊN MATRIXEXAMAI PRO                              |
+----------------------+------------------------------------------+---------------------------------------+
|  TỔ HỢP PHÍM         |  CHỨC NĂNG TƯƠNG ỨNG                     |  PHÂN HỆ / NGỮ CẢNH                   |
+----------------------+------------------------------------------+---------------------------------------+
|  F5                  |  Biên dịch hình vẽ TikZ độ nét 600 DPI   |  TikzView                             |
|  Ctrl + Enter        |  Biên dịch hình vẽ TikZ (Phím tắt phụ)   |  TikzView                             |
|  Ctrl + Shift + G    |  AI Sinh mã nguồn TikZ từ mô tả/ảnh      |  TikzView                             |
|  Ctrl + Shift + W    |  Sao chép hình vẽ và chèn thẳng vào Word |  TikzView (Word Add-in)               |
|  Ctrl + V            |  Dán ảnh chụp màn hình từ Clipboard      |  ConvertView / TikzView               |
|  Ctrl + S            |  Lưu file ảnh chất lượng cao (PNG/SVG)   |  TikzView                             |
|  Win + Shift + S     |  Công cụ chụp vùng màn hình Windows      |  Toàn hệ thống Windows                |
|  Ctrl + Shift + C    |  Chuẩn hóa nhanh văn bản kẹp ${...}$     |  ConvertView                          |
|  F7                  |  Kích hoạt thẩm định kiểm định lỗi QC    |  QcView                               |
|  F9                  |  Kích hoạt thuật toán trộn đề hoán vị    |  ShuffleView                          |
+----------------------+------------------------------------------+---------------------------------------+
```

---

### 4.3. Prompt Catalog Mẫu Chuẩn Cho Giáo Viên Toán & KHTN

Các mẫu câu lệnh (prompt) được tinh chỉnh tối ưu dành cho giáo viên tương tác với hệ thống AI của MatrixExamAI:

#### 1. Prompt Vẽ Đồ Thị Hàm Số Bậc Ba Khảo Sát Đầy Đủ
> "Hãy vẽ đồ thị hàm số bậc ba $y = x^3 - 3x^2 + 2$ bằng TikZ. Yêu cầu: Trục tọa độ Oxy có mũi tên và nhãn gốc O, x, y. Thể hiện rõ tọa độ điểm cực đại $(0; 2)$ và điểm cực tiểu $(2; -2)$ bằng các đường nét đứt gióng vào hai trục. Đồ thị vẽ bằng nét đậm màu xanh navy, domain từ -1.2 đến 3.2. Điền nhãn tọa độ rõ ràng, không bị đè chữ."

#### 2. Prompt Vẽ Hình Chóp Đáy Tam Giác Có Đường Cao Vuông Góc
> "Vẽ hình chóp $S.ABC$ có đáy $ABC$ là tam giác vuông tại $B$, cạnh bên $SA$ vuông góc với mặt phẳng đáy $(ABC)$. Yêu cầu chuẩn quy ước vẽ hình học không gian THPT: Cạnh $AB, SA, SB, SC, BC, AC$ thể hiện đúng nét liền và nét đứt ($AC$ và $AB$ là nét đứt bên trong, các cạnh nhìn thấy là nét liền). Ký hiệu góc vuông tại đỉnh $B$ của đáy và tại đỉnh $A$ của tam giác $SAB$. Đặt tên các đỉnh bằng font chữ in hoa nghiêng chuẩn toán học."

#### 3. Prompt Bảng Biến Thiên Hàm Phân Thức Hữu Tỉ (tkz-tab)
> "Tạo bảng biến thiên cho hàm số $y = \frac{2x - 1}{x + 1}$ bằng gói lệnh tkz-tab. Yêu cầu: Hàng x chạy từ $-\infty$, tiệm cận đứng $-1$, đến $+\infty$. Hàng $y'$ mang dấu dương trên cả hai khoảng xác định, tại $x = -1$ có dấu hai gạch không xác định. Hàng y thể hiện rõ tiệm cận ngang $y = 2$ tại vô cực và giới hạn tiến tới $+\infty, -\infty$ tại vị trí không xác định."

---

## 5. GIAI ĐOẠN I: KẾ HOẠCH TRIỂN KHAI THỰC TẾ (IMPLEMENTATION)

### 5.1. Lộ Trình 3 Giai Đoạn (3-Phase Rollout Plan)

Quá trình chuyển giao công nghệ tại mỗi trường THPT được phân bổ thành 3 giai đoạn chặt chẽ:

```
+---------------------------------------------------------------------------------------------------------+
|                                    LỘ TRÌNH TRIỂN KHAI 3 GIAI ĐOẠN                                      |
+------------------------------------+------------------------------------+-------------------------------+
|  GIAI ĐOẠN 1: THỬ NGHIỆM (PILOT)   |  GIAI ĐOẠN 2: NHÂN RỘNG (ROLL-OUT) |  GIAI ĐOẠN 3: THỂ CHẾ HÓA     |
|  - Thời gian: Tuần 1 - Tuần 2      |  - Thời gian: Tuần 3 - Tuần 6      |  - Thời gian: Tháng thứ 2+    |
|  - Quy mô: 5 giáo viên cốt cán     |  - Quy mô: Toàn bộ tổ Toán & KHTN  |  - Quy mô: Toàn trường & Cụm  |
|  - Mục tiêu: Rà soát lỗi, thích    |  - Mục tiêu: 100% giáo viên sử     |  - Mục tiêu: Đưa vào quy chế  |
|    ứng trên máy tính thực tế       |    dụng soạn đề kiểm tra 1 tiết    |    sinh hoạt chuyên môn chính |
+------------------------------------+------------------------------------+-------------------------------+
```

#### Giai đoạn 1: Thử nghiệm Pilot (Tuần 1 – Tuần 2)
- **Quy mô**: 5 giáo viên nòng cốt (Bao gồm Thầy Nam Tổ trưởng, Cô Mai giáo viên trẻ, Thầy Hùng đại diện nhóm giáo viên thâm niên cao, và 2 giáo viên Vật lí/Hóa học).
- **Hoạt động**: Cài đặt phần mềm trực tiếp, hướng dẫn chuyên sâu, yêu cầu mỗi giáo viên thực hiện số hóa 2 đề thi thực tế của học kỳ trước.
- **Mục tiêu**: Thu thập toàn bộ các trường hợp ngoại lệ (Edge cases), lỗi máy tính không tương thích (ví dụ: máy tính cài Office lậu bị chặn COM Add-in, thiếu font ký hiệu TeX).

#### Giai đoạn 2: Nhân rộng toàn diện (Roll-out) (Tuần 3 – Tuần 6)
- **Quy mô**: Toàn bộ giáo viên tổ Toán và tổ Khoa học Tự nhiên (khoảng 20 – 35 giáo viên).
- **Hoạt động**: Tổ chức 2 buổi hội thảo tập huấn tập trung vào thứ Bảy. Triển khai mô hình "Đôi bạn cùng tiến": Mỗi giáo viên trẻ thành thạo công nghệ ghép đôi hỗ trợ 1 giáo viên lớn tuổi.
- **Mục tiêu**: 100% giáo viên tự tay soạn và xuất bản thành công đề kiểm tra định kỳ (giữa kỳ/cuối kỳ) bằng MatrixExamAI Pro.

#### Giai đoạn 3: Thể chế hóa quy trình (Institutionalization) (Từ tháng thứ 2 trở đi)
- **Quy mô**: Đưa vào quy định chuyên môn chính thức của trường THPT.
- **Hoạt động**: Ban Giám hiệu ban hành quy chuẩn nộp đề thi: Mọi đề thi nộp duyệt phải đi kèm file Word chuẩn hóa Native Equation, hình vẽ TikZ tối thiểu 300-600 DPI, và biên bản báo cáo kiểm định QC không còn lỗi nghiêm trọng.
- **Mục tiêu**: Hình thành Ngân hàng câu hỏi dùng chung toàn trường với hơn 1.000 câu hỏi chuẩn hóa được lưu trữ trên hệ thống SQLite.

---

### 5.2. Kế Hoạch Hỗ Trợ Kỹ Thuật (Helpdesk & Technical Support)

Mô hình hỗ trợ 3 tầng (3-Tier Support Model) bảo đảm không giáo viên nào bị bỏ lại phía sau:

- **Tầng 1 (Cấp cơ sở - Nhóm Zalo chuyên môn trường)**: Các giáo viên cốt cán (Cô Mai, Thầy Nam) giải đáp ngay lập tức các thắc mắc thao tác hàng ngày (như quên phím tắt, cách chụp ảnh màn hình). Phản hồi trong vòng 5 - 15 phút.
- **Tầng 2 (Cấp kỹ thuật trường - Cán bộ CNTT/Thiết bị)**: Xử lý các vấn đề về cài đặt môi trường: Cài .NET 10 Runtime, cấp quyền Administrator, cài đặt bổ sung MiKTeX hoặc kích hoạt Word Add-in bị ẩn.
- **Tầng 3 (Cấp chuyên gia phần mềm - Đội ngũ kỹ sư MatrixExamAI)**: Hỗ trợ từ xa qua UltraViewer/AnyDesk đối với các lỗi crash hệ thống, xung đột hệ điều hành đặc thù hoặc tối ưu hóa prompt AI cho các bài toán cực khó.

#### Bảng FAQ 5 Lỗi Thường Gặp & Cách Khắc Phục Nhanh:
1. *Hỏi: Tại sao tôi bấm nút 'Xuất Word' mà file Word không tự mở lên?*  
   -> *Đáp*: Kiểm tra xem máy tính có đang mở một file Word cùng tên hay không. Hãy đóng file Word cũ hoặc lưu sang tên mới rồi xuất lại.
2. *Hỏi: Công thức toán sau khi chuẩn hóa có dấu lạ `${...}$` là gì?*  
   -> *Đáp*: Đây là ký hiệu bao đóng thông minh để hệ thống nhận diện công thức toán. Khi xuất ra file Word native, ký tự này sẽ tự động chuyển đổi thành công thức Toán chuẩn Microsoft Equation siêu nét.
3. *Hỏi: Máy tính báo "pdflatex: Không tìm thấy lệnh" khi biên dịch TikZ?*  
   -> *Đáp*: Máy tính của thầy/cô chưa cài đặt MiKTeX hoặc TeX Live. Hệ thống sẽ tự động chuyển sang chế độ Xem trước Vector Fallback. Để xuất ảnh 600 DPI, vui lòng nhờ kỹ thuật viên cài bộ MiKTeX Portable theo hướng dẫn.
4. *Hỏi: Làm sao để cố định câu có phương án "Cả A và B đều đúng" khi trộn đề?*  
   -> *Đáp*: Tại phân hệ ShuffleView, chỉ cần tích chọn ô 'Khóa phương án phụ thuộc'. Thuật toán sẽ tự động phát hiện các cụm từ này và giữ nguyên vị trí phương án D.
5. *Hỏi: AI Vision OCR báo lỗi không đọc được ảnh đề thi?*  
   -> *Đáp*: Kiểm tra lại ảnh chụp màn hình. Hãy dùng tổ hợp `Win+Shift+S` kéo vùng ảnh vừa đủ câu hỏi, tránh chụp quá xa hoặc để chữ bị mờ, lóa sáng.

---

## 6. GIAI ĐOẠN E: ĐÁNH GIÁ & CẢI TIẾN LIÊN TỤC (EVALUATION)

Để bảo đảm tính bền vững của dự án chuyển đổi số, cơ chế phản hồi vòng lặp (Feedback Loops) được thiết lập tại 3 mốc thời gian trọng yếu:

```
+---------------------------------------------------------------------------------------------------------+
|                                  CƠ CHẾ PHẢN HỒI VÒNG LẶP (FEEDBACK LOOPS)                              |
+------------------------------------+------------------------------------+-------------------------------+
|  VÒNG LẶP 1: SAU MỖI BUỔI HỌC      |  VÒNG LẶP 2: SAU KỲ THI ĐỊNH KỲ    |  VÒNG LẶP 3: TỔNG KẾT HỌC KỲ  |
|  - Khảo sát nhanh 3 câu hỏi        |  - Họp rút kinh nghiệm tổ          |  - Đánh giá chỉ số ROI & KPI  |
|  - Điều chỉnh tốc độ giảng dạy     |  - Cập nhật thêm mẫu TikZ chuyên đề|  - Nâng cấp phiên bản phần mềm|
|  - Bổ sung tài liệu kèm cặp        |  - Chuẩn hóa ngân hàng đề tổ       |  - Tuyên dương cá nhân xuất sắc|
+------------------------------------+------------------------------------+-------------------------------+
```

1. **Vòng lặp ngắn (Sau mỗi buổi đào tạo)**: Khảo sát nhanh trên Google Forms (3 câu trắc nghiệm cảm xúc: Dễ hiểu / Bình thường / Khó hiểu). Nếu có trên 20% giáo viên cảm thấy thao tác khó khăn, buổi học tiếp theo sẽ dành 30 phút đầu giờ để ôn tập thực hành.
2. **Vòng lặp trung hạn (Sau kỳ thi Giữa kỳ và Cuối kỳ)**: Tổ chuyên môn họp tổng kết rút kinh nghiệm: Có bao nhiêu đề thi được tạo bằng MatrixExamAI? Có câu hỏi nào bị lỗi định dạng khi in ra giấy hay không? Học sinh có phản ánh về hình vẽ mờ hay không? Các mẫu TikZ mới xuất hiện trong đề thi sẽ được tổng hợp đưa vào thư viện dùng chung của trường.
3. **Vòng lặp dài hạn (Cuối mỗi năm học)**: Đối chiếu các chỉ số Kirkpatrick (Cấp độ 3 và 4), tính toán số giờ lao động tiết kiệm được, tổ chức khen thưởng giáo viên tích cực đổi mới sáng tạo và chuyển giao bản cập nhật phần mềm mới nhất.
