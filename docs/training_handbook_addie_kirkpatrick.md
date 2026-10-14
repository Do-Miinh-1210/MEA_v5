# CẨM NANG ĐÀO TẠO & CHUYỂN GIAO CÔNG NGHỆ CHUẨN ADDIE & KIRKPATRICK
## Dành Cho Giáo Viên & Tổ Chuyên Môn Toán - Khoa Học Tự Nhiên Trường THPT
### Hệ Sinh Thái Phần Mềm Biên Soạn Tài Liệu & Đề Thi Thông Minh MatrixExamAI Pro (.NET 10 Native Fluent UI)

---

## MỤC LỤC TỔNG THỂ

1. **LỜI MỞ ĐẦU & BỐI CẢNH ĐỔI MỚI GIÁO DỤC**
2. **PHẦN 1: KHUNG ĐÀO TẠO THỰC CHIẾN THEO MÔ HÌNH ADDIE**
   - 1.1. Giai đoạn A (Analysis) – Phân tích Đối tượng, Teacher Personas & Tech Gap
   - 1.2. Giai đoạn D (Design) – Thiết kế Mục tiêu SMART, Khung Chương trình & Chiến lược Sư phạm
   - 1.3. Giai đoạn D (Development) – Phát triển Học liệu, Job Aids, Cheat Sheets & Prompt Catalog
   - 1.4. Giai đoạn I (Implementation) – Lộ trình Triển khai 3 Giai đoạn & Hệ thống Hỗ trợ Kỹ thuật
   - 1.5. Giai đoạn E (Evaluation) – Đánh giá Liên tục & Cơ chế Phản hồi Vòng lặp
3. **PHẦN 2: KHUNG NĂNG LỰC CHUYỂN ĐỔI SỐ DỰA TRÊN THANG BLOOM'S TAXONOMY**
   - 2.1. Cấp độ 1: Nhận biết (Remembering)
   - 2.2. Cấp độ 2: Thông hiểu (Understanding)
   - 2.3. Cấp độ 3: Vận dụng (Applying)
   - 2.4. Cấp độ 4: Phân tích (Analyzing)
   - 2.5. Cấp độ 5: Đánh giá (Evaluating)
   - 2.6. Cấp độ 6: Sáng tạo (Creating)
   - 2.7. Ma trận Ánh xạ Năng lực Số Bloom – MatrixExamAI Pro
4. **PHẦN 3: 5 KỊCH BẢN VI KHÓA HỌC (MICRO-LEARNING SCRIPTS 5 – 15 PHÚT)**
   - Bài 1: Chuẩn hóa Đề thi & Công thức Toán từ PDF/Word sang MatrixExamAI trong 3 phút (`ConvertView`)
   - Bài 2: Thiết lập Ma trận Đề thi 22 câu Chuẩn Bộ GD&ĐT 2025 (`ExamMatrixView`)
   - Bài 3: Trộn đề Hoán vị 4 Mã đề Không lệch Bảng Đáp án & Xuất OMR (`ShuffleView`)
   - Bài 4: AI Vẽ hình Toán học TikZ Xuất sắc từ Ảnh chụp & Mô tả Tiếng Việt (`TikzView`)
   - Bài 5: Thẩm định QC Tự động & Đóng gói Ngân hàng Câu hỏi Chuẩn In ấn (`QcView` & `QuestionBankView`)
5. **PHẦN 4: THANG ĐO LƯỜNG HIỆU QUẢ 4 CẤP ĐỘ THEO KIRKPATRICK & TÍNH TOÁN ROI**
   - 4.1. Cấp độ 1 (Reaction): Khảo sát CSAT & Chỉ số Net Promoter Score (NPS)
   - 4.2. Cấp độ 2 (Learning): Bộ đề Trắc nghiệm 10 câu Chuẩn hóa & Barem Bài thi Thực hành 100 điểm
   - 4.3. Cấp độ 3 (Behavior): Bảng Checklist Theo dõi Hành vi Ứng dụng sau 30 và 60 ngày
   - 4.4. Cấp độ 4 (Results): Công thức Định lượng ROI, Số giờ Tiết kiệm & Tỷ lệ Giảm thiểu Rủi ro
6. **PHỤ LỤC & TÀI LIỆU THAM KHẢO**

---

## 1. LỜI MỞ ĐẦU & BỐI CẢNH ĐỔI MỚI GIÁO DỤC

Chương trình Giáo dục Phổ thông 2018 (GDPT 2018) đặt trọng tâm vào việc phát triển phẩm chất và năng lực của học sinh. Kéo theo đó, cấu trúc định dạng đề thi tốt nghiệp THPT từ năm 2025 của Bộ Giáo dục và Đào tạo có sự thay đổi mang tính lịch sử: Đề thi không còn thuần túy là các câu trắc nghiệm 4 lựa chọn đơn giản, mà được tái cấu trúc thành 3 phần thi với độ phân hóa sâu sắc:
- **Phần I**: Câu hỏi trắc nghiệm nhiều lựa chọn (4 phương án chọn 1).
- **Phần II**: Câu hỏi trắc nghiệm Đúng/Sai (Mỗi câu gồm 4 lệnh hỏi a, b, c, d với thang điểm lũy tiến).
- **Phần III**: Câu hỏi trắc nghiệm dạng Trả lời ngắn (Đòi hỏi học sinh tự giải và điền kết quả số).

Sự thay đổi này đặt lên vai người giáo viên bộ môn Toán và Khoa học Tự nhiên (Vật lí, Hóa học, Sinh học) một áp lực chuyên môn chưa từng có: Khối lượng công việc soạn đề, cân đối ma trận điểm 10.0, vẽ hình học phẳng, đồ thị hàm số và hình không gian chất lượng cao tăng gấp 3 đến 5 lần. Phương pháp soạn đề truyền thống (gõ MathType thủ công, cắt dán hình ảnh mờ 72 DPI, trộn đề bằng các công cụ cổ điển hay bị lỗi phương án phụ thuộc) đã trở thành nút thắt cổ chai cản trở quá trình đổi mới giáo dục.

**Cẩm nang Đào tạo & Chuyển giao Công nghệ** này được biên soạn nhằm chuyển giao toàn diện nền tảng **MatrixExamAI Pro (.NET 10 Native Fluent UI)** cho đội ngũ cán bộ quản lý, tổ trưởng chuyên môn và giáo viên THPT trên cả nước. Được xây dựng trên nền tảng kết hợp chặt chẽ giữa hai khung lý thuyết sư phạm danh tiếng toàn cầu: **Mô hình thiết kế dạy học ADDIE** và **Mô hình đo lường hiệu quả 4 cấp độ Kirkpatrick**, cẩm nang cung cấp lộ trình thực chiến, khả thi, giải quyết triệt để rào cản tâm lý e ngại công nghệ, mang lại bước nhảy vọt về năng suất lao động sư phạm và bảo đảm chuẩn mực khảo thí học thuật.

---

## PHẦN 1: KHUNG ĐÀO TẠO THỰC CHIẾN THEO MÔ HÌNH ADDIE

Mô hình ADDIE (Analysis – Design – Development – Implementation – Evaluation) là kim chỉ nam bảo đảm tính khoa học, nhân văn và thực tiễn của toàn bộ quá trình tập huấn chuyển giao công nghệ.

```
+---------------+     +---------------+     +-----------------+     +--------------------+     +------------------+
|  A (Analysis) | --> |  D (Design)   | --> | D (Development) | --> | I (Implementation) | --> |  E (Evaluation)  |
| Phân tích     |     | Thiết kế mục  |     | Phát triển học  |     | Triển khai 3 giai  |     | Đánh giá vòng    |
| đối tượng &   |     | tiêu SMART &  |     | liệu, Job Aids, |     | đoạn: Pilot ->     |     | lặp, cải tiến    |
| Tech Gap      |     | Curriculum    |     | Prompt Catalog  |     | Rollout -> Thể chế |     | sau kỳ thi       |
+---------------+     +---------------+     +-----------------+     +--------------------+     +------------------+
```

---

### 1.1. GIAI ĐOẠN A: PHÂN TÍCH NHU CẦU & ĐỐI TƯỢNG (ANALYSIS)

#### 1.1.1. Chân Dung 3 Nhóm Giáo Viên Điển Hình (Teacher Personas)

Thực tế tại các trường THPT cho thấy trình độ ứng dụng công nghệ thông tin của giáo viên có sự phân hóa rõ rệt. Chương trình đào tạo phân loại và tiếp cận sâu sắc 3 chân dung giáo viên điển hình:

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

##### 1. Thầy Hùng – "Nhà giáo cựu binh, thận trọng và e ngại thay đổi"
- **Nhân khẩu & Kinh nghiệm**: 52 tuổi, 25 năm giảng dạy môn Toán. Đã quen thuộc với bảng phấn, giáo án Word 2003/2010 và công cụ gõ công thức MathType 6.x trong suốt hơn hai thập kỷ.
- **Kỹ năng CNTT hiện tại**: Mức độ cơ bản. Thao tác gõ mổ cò, dùng chuột chậm, biết tải tài liệu trên mạng, biết copy/paste cơ bản nhưng rất lúng túng khi gặp thông báo lỗi phần mềm tiếng Anh.
- **Nỗi sợ & Rào cản tâm lý**:
  - Sợ làm hỏng kho tư liệu đề thi Word đã tích lũy cả đời dạy học.
  - Sợ các dòng lệnh phức tạp, sợ mã nguồn LaTeX hay các cú pháp khó nhớ.
  - Ngại thay đổi vì sợ mất nhiều thời gian học lại từ đầu, sợ bị đồng nghiệp trẻ chê cười khi thao tác chậm.
- **Động lực thực sự**: Thầy Hùng rất mệt mỏi vì thường xuyên phải thức đến 1 giờ sáng để căn chỉnh lề, sửa lỗi nhảy dòng khi sao chép tài liệu cho học sinh. Thầy mong muốn có một giải pháp "1 chạm", làm sao bấm một nút là ra được đề thi đẹp mà không cần học các thuật ngữ cao siêu.
- **Giải pháp chuyển giao sư phạm**:
  - Tuyệt đối không dạy cú pháp lập trình hay khái niệm kỹ thuật trừu tượng.
  - Chuẩn hóa quy trình "1 chạm": Kéo thả file PDF -> Bấm nút 'Chuẩn hóa' -> Mở file Word kết quả.
  - Bố trí giáo viên trẻ như Cô Mai kèm cặp 1-1 theo phương pháp "Cầm tay chỉ việc", khích lệ từng thành tựu nhỏ.

##### 2. Cô Mai – "Tiên phong chuyển đổi số, đòi hỏi tốc độ và thẩm mỹ đỉnh cao"
- **Nhân khẩu & Kinh nghiệm**: 29 tuổi, 5 năm kinh nghiệm dạy Toán và phụ trách câu lạc bộ nghiên cứu khoa học STEM.
- **Kỹ năng CNTT hiện tại**: Nhanh nhạy, thành thạo Office 365, Canva, thường xuyên dùng ChatGPT và Gemini trên nền web để tìm bài tập hay.
- **Nỗi đau kỹ thuật**:
  - Mất kiên nhẫn khi copy công thức từ ChatGPT/Claude về Word vì công thức bị biến thành mã LaTeX thô hoặc vỡ vụn ký tự, phải ngồi chỉnh từng dòng rất mất thời gian.
  - Bức xúc vì hình vẽ chụp màn hình tải từ mạng về khi in photo ra giấy kiểm tra có độ phân giải thấp (72 DPI), nét đứt nét liền dính tịt vào nhau khiến học sinh khiếu nại.
- **Động lực thực sự**: Khát khao sở hữu một công cụ tích hợp toàn diện: Tự động hóa từ khâu lấy ý tưởng đề thi -> Chuẩn hóa Word Native -> Vẽ hình học vector 600 DPI siêu nét -> Trộn đề xuất bản trong vài phút.
- **Giải pháp chuyển giao sư phạm**:
  - Hướng dẫn khai thác tối đa hệ thống phím tắt công thái học (`Ctrl+Shift+G`, `F5`, `Ctrl+Shift+W`).
  - Đào tạo chuyên sâu phân hệ TikzView và kỹ thuật prompt AI vẽ đồ thị, hình không gian phức tạp.
  - Quy hoạch Cô Mai trở thành "Hạt nhân chuyển đổi số" (Champion) của tổ để lan tỏa và hỗ trợ các giáo viên khác.

##### 3. Thầy Nam – "Tổ trưởng chuyên môn, người gác cổng quy chuẩn và hiệu năng"
- **Nhân khẩu & Kinh nghiệm**: 40 tuổi, 17 năm công tác, Tổ trưởng tổ Toán – KHTN kiêm thành viên Hội đồng ra đề thi của Sở GD&ĐT.
- **Kỹ năng CNTT hiện tại**: Mức độ khá. Hiểu rõ cấu trúc ngân hàng câu hỏi, từng sử dụng các phần mềm trộn đề trắc nghiệm cổ điển.
- **Trọng trách & Áp lực quản lý**:
  - Chịu trách nhiệm trực tiếp về chất lượng và tính chính xác của đề thi khối 10, 11, 12 cho 600 - 800 học sinh. Rất sợ lỗi lệch đáp án khi trộn đề trắc nghiệm.
  - Mệt mỏi vì phải duyệt thủ công hàng trăm câu hỏi nộp lên từ các giáo viên với đủ thứ định dạng lộn xộn (người gõ MathType, người gõ Equation, người dán ảnh tạm bợ).
  - Cần công cụ quản lý ma trận chuẩn 22 câu theo đúng định dạng GDPT 2018 của Bộ GD&ĐT.
- **Động lực thực sự**: Thiết lập quy chuẩn soạn đề thống nhất cho toàn tổ; có công cụ tự động quét lỗi (QC) trước khi in ấn; xây dựng ngân hàng câu hỏi SQLite dùng chung không lo mất mạng.
- **Giải pháp chuyển giao sư phạm**:
  - Tập trung đào tạo phân hệ ExamMatrixView (Ma trận 22 câu cân đối 10.0 điểm).
  - Đào tạo phân hệ QcView (Rà soát lỗi trùng phương án, sót đáp án).
  - Hướng dẫn quản trị và phân quyền QuestionBankView (Ngân hàng SQLite dùng chung nội bộ).

---

#### 1.1.2. Phân Tích Khoảng Trống Kỹ Năng Số (Tech Gap Analysis)

```
+---------------------------------------------------------------------------------------------------------+
|                                    BẢNG ĐỐI CHIẾU KHOẢNG TRỐNG KỸ NĂNG SỐ                               |
+----------------------+-----------------------------------+----------------------------------------------+
| HẠNG MỤC TÁC VỤ      | SOẠN ĐỀ THỦ CÔNG TRUYỀN THỐNG     | QUY TRÌNH MATRIXEXAMAI PRO                   |
+----------------------+-----------------------------------+----------------------------------------------+
| 1. Trích xuất tài    | Gõ lại từng chữ từ file PDF. Mất  | Động cơ PdfPig trích xuất siêu tốc; AI OCR   |
|    liệu thô          | 120 - 180 phút/đề. Dễ sai số.     | ảnh Clipboard (Ctrl+V) trong 30 giây.        |
+----------------------+-----------------------------------+----------------------------------------------+
| 2. Định dạng công    | Gõ MathType thủ công. Dễ lỗi font | Tự động bao đóng chuẩn ${...}$, bảo vệ |x|,  |
|    thức toán học     | khi chuyển máy. Lỗi bảng |x|.     | xuất Word Equation (OMML) bản địa sắc nét.   |
+----------------------+-----------------------------------+----------------------------------------------+
| 3. Vẽ hình học &     | Chụp màn hình 72 DPI. Đồ thị mờ,  | Tích hợp TikZ biên dịch 600 DPI, chèn thẳng  |
|    đồ thị hàm số     | đen sì, học sinh khiếu nại.       | vào Word bằng phím tắt Ctrl+Shift+W trong 2s.|
+----------------------+-----------------------------------+----------------------------------------------+
| 4. Xây dựng ma trận  | Kẻ bảng Excel tính nhẩm. Dễ lệch  | ExamMatrixView tự động cân bằng 22 câu chuẩn |
|    đề thi            | điểm 10.0 ở cấu trúc mới 3 phần.  | Bộ GD&ĐT (12 TN, 4 Đ/S, 6 TLN = 10.0 điểm).  |
+----------------------+-----------------------------------+----------------------------------------------+
| 5. Trộn đề hoán vị   | Dễ bị đảo lộn phương án phụ thuộc | Thuật toán ShuffleView khóa cố định phương   |
|    & Bảng đáp án     | ("Cả A và B đều đúng"). Dò tay.   | án đặc thù; xuất 4 mã đề + ma trận OMR chuẩn.|
+----------------------+-----------------------------------+----------------------------------------------+
| 6. Kiểm định chất    | Đọc dò bằng mắt trên giấy in. Rất | QcView quét tự động 100% câu hỏi trong 2s,   |
|    lượng (QC)        | dễ sót câu trùng 2 phương án.     | phát hiện trùng đáp án, thiếu đáp án, sai $. |
+----------------------+-----------------------------------+----------------------------------------------+
```

---

#### 1.1.3. Yêu Cầu Hạ Tầng Công Nghệ & Môi Trường Vận Hành

```
+---------------------------------------------------------------------------------------------------------+
|                                  YÊU CẦU HẠ TẦNG KỸ THUẬT PHẦN CỨNG & PHẦN MỀM                          |
+--------------------------+---------------------------------------+--------------------------------------+
| THÔNG SỐ                 | CẤU HÌNH TỐI THIỂU (MINIMUM)          | CẤU HÌNH KHUYẾN NGHỊ (RECOMMENDED)   |
+--------------------------+---------------------------------------+--------------------------------------+
| Vi xử lý (CPU)           | Intel Core i3 Gen 4 / AMD Ryzen 3     | Intel Core i5 Gen 8+ / AMD Ryzen 5   |
| Bộ nhớ RAM               | 4 GB                                  | 8 GB trở lên                         |
| Ổ đĩa cứng               | Trống 2.0 GB (HDD/SSD)                | Trống 5.0 GB (SSD NVMe siêu tốc)     |
| Hệ điều hành             | Windows 10 64-bit (Version 1909+)     | Windows 11 64-bit (Bản cập nhật mới) |
| Môi trường Runtime       | .NET 10 Desktop Runtime               | .NET 10 Desktop Runtime              |
| Bộ ứng dụng Văn phòng    | Microsoft Word 2016 (64-bit)          | MS Word 2019 / 2021 / Office 365     |
| Tiện ích Word Add-in     | MatrixExamAI Word Add-in (Đã đăng ký) | MatrixExamAI Word Add-in (COM/VSTO)  |
| Phân phối TeX Biên dịch  | MiKTeX Portable (Cơ bản)              | TeX Live 2023+ hoặc MiKTeX Full      |
| Mạng Internet            | 1 Mbps (Kết nối AI Gemini/9Router)    | Băng thông rộng ổn định              |
+--------------------------+---------------------------------------+--------------------------------------+
```

---

### 1.2. GIAI ĐOẠN D: THIẾT KẾ MỤC TIÊU & CHƯƠNG TRÌNH ĐÀO TẠO (DESIGN)

#### 1.2.1. Mục Tiêu Học Tập Tổng Thể Theo Mô Hình SMART
- **S – Specific (Cụ thể)**: 100% giáo viên làm chủ quy trình 5 bước: (1) Chuẩn hóa tài liệu PDF/Word cũ; (2) Tạo ma trận đề thi chuẩn 22 câu Bộ GD&ĐT 2025; (3) Sinh mã & biên dịch hình vẽ TikZ 600 DPI dán vào Word; (4) Thẩm định QC tự động; (5) Trộn đề hoán vị 4 mã đề kèm ma trận đáp án chéo OMR.
- **M – Measurable (Đo lường được)**:
  - 100% giáo viên đạt tối thiểu 80/100 điểm bài thi thực hành cuối khóa.
  - Thời gian biên soạn 1 đề thi hoàn chỉnh giảm từ 180 phút xuống dưới 25 phút.
  - Đạt 0% lỗi sai lệch đáp án trên các mã đề hoán vị.
- **A – Achievable (Khả thi)**: Chương trình được chia nhỏ thành các vi khóa học 5-15 phút, có giàn giáo sư phạm hỗ trợ, bảo đảm cả những giáo viên kỹ năng cơ bản nhất cũng làm chủ được phần mềm sau 2 tuần.
- **R – Relevant (Thiết thực)**: Phục vụ trực tiếp nhiệm vụ trọng tâm năm học: Biên soạn đề kiểm tra định kỳ và ôn thi tốt nghiệp THPT theo chương trình GDPT 2018.
- **T – Time-bound (Thời gian rõ ràng)**: 4 buổi tập huấn tập trung (12 tiết), theo dõi đo lường sự thay đổi hành vi sau 30 ngày và 60 ngày.

---

#### 1.2.2. Khung Chương Trình Đào Tạo Tích Hợp (Curriculum Framework)

```
+---------------------------------------------------------------------------------------------------------+
|                                    KHUNG CHƯƠNG TRÌNH ĐÀO TẠO 6 MODULE                                  |
+----------+--------------------------------------------------------------------+-----------+-------------+
| MODULE   | TÊN BÀI HỌC & NỘI DUNG TRỌNG TÂM                                   | THỜI LƯỢNG| TRỌNG TÂM   |
+----------+--------------------------------------------------------------------+-----------+-------------+
| Mod 01   | Nhập môn MatrixExamAI & Chuẩn hóa Tài liệu Native Word             | 2.0 giờ   | ConvertView |
| Mod 02   | AI Vision OCR Đề thi từ Ảnh chụp Clipboard (Ctrl+V)                | 2.0 giờ   | ConvertView |
| Mod 03   | Thiết lập Ma trận Đề 22 câu Chuẩn Bộ GD&ĐT 2025                    | 2.0 giờ   | ExamMatrix  |
| Mod 04   | AI Vẽ hình Toán học TikZ 600 DPI & Dán Word (Ctrl+Shift+W)         | 2.5 giờ   | TikzView    |
| Mod 05   | Trộn Đề Hoán vị 4 Mã đề & Bảng Đáp án Chéo OMR                     | 1.5 giờ   | ShuffleView |
| Mod 06   | Thẩm định QC Đề thi & Quản trị Ngân hàng Câu hỏi SQLite            | 2.0 giờ   | Qc & QBank  |
+----------+--------------------------------------------------------------------+-----------+-------------+
| TỔNG CỘNG| 6 MODULE LÝ THUYẾT & THỰC HÀNH TRÊN MÁY TÍNH                       | 12.0 GIỜ  | CẤP CHỨNG NHẬN
+----------+--------------------------------------------------------------------+-----------+-------------+
```

---

#### 1.2.3. Chiến Lược Sư Phạm Hiện Đại
1. **"Learn by Doing" (Học qua Hành)**: Dành 80% thời lượng cho giáo viên thực hành trực tiếp trên đề thi thật của chính mình.
2. **"Scaffolding" (Dựng giàn giáo nhận thức)**: 
   - *Bậc 1*: Dùng mẫu có sẵn trong ComboBox.
   - *Bậc 2*: Chỉnh sửa thông số trên mẫu.
   - *Bậc 3*: Tự chủ viết prompt tiếng Việt sinh đề và vẽ hình độc lập.
3. **"Micro-learning" (Vi học tập)**: Chia nhỏ kiến thức thành các bài học 5 - 15 phút, giải quyết dứt điểm 1 thao tác kỹ thuật cụ thể.

---

### 1.3. GIAI ĐOẠN D: PHÁT TRIỂN HỌC LIỆU & HƯỚNG DẪN TÁC VỤ (DEVELOPMENT)

#### 1.3.1. Hướng Dẫn Tác Vụ Cầm Tay (Job Aid: Quy Trình 5 Bước)
1. **Bước 1 (Chuẩn hóa)**: Nạp PDF/Word cũ vào ConvertView -> Nhấn 'Chuẩn hóa đề thi' -> Nhấn 'Xuất file Word'.
2. **Bước 2 (Ma trận đề)**: Mở ExamMatrixView -> Chọn mẫu 'Chuẩn BGD 2025 (22 câu)' -> Chỉnh tỷ lệ nhận thức -> Nhấn 'AI Soạn đề'.
3. **Bước 3 (Vẽ hình TikZ)**: Mở TikzView -> Nhập mô tả hoặc dán ảnh mẫu -> `Ctrl+Shift+G` -> `F5` biên dịch 600 DPI -> `Ctrl+Shift+W` dán vào Word.
4. **Bước 4 (Thẩm định QC)**: Mở QcView -> Nhấn `F7` quét lỗi -> Nhấn 'Tự động sửa lỗi' -> Xác nhận 0 Errors.
5. **Bước 5 (Trộn đề & OMR)**: Mở ShuffleView -> Nhập 4 mã đề -> Tích 'Khóa phương án phụ thuộc' -> Bấm `F9` trộn đề -> Xuất 4 file Word + Ma trận đáp án chéo OMR.

---

#### 1.3.2. Bảng Tra Cứu Phím Tắt Vàng Công Thái Học (Cheat Sheet)

```
+---------------------------------------------------------------------------------------------------------+
|                                    BẢNG PHÍM TẮT VÀNG TRÊN MATRIXEXAMAI PRO                             |
+----------------------+------------------------------------------+---------------------------------------+
|  TỔ HỢP PHÍM         |  HÀNH ĐỘNG THỰC HIỆN                     |  PHÂN HỆ SỬ DỤNG                      |
+----------------------+------------------------------------------+---------------------------------------+
|  F5                  |  Biên dịch hình vẽ TikZ độ nét 600 DPI   |  TikzView                             |
|  Ctrl + Enter        |  Biên dịch hình vẽ TikZ (Phím phụ)       |  TikzView                             |
|  Ctrl + Shift + G    |  AI Sinh mã nguồn TikZ từ mô tả/ảnh      |  TikzView                             |
|  Ctrl + Shift + W    |  Sao chép hình 600 DPI và dán thẳng Word |  TikzView (Word Add-in)               |
|  Ctrl + V            |  Dán ảnh chụp màn hình từ Clipboard      |  ConvertView / TikzView               |
|  Ctrl + S            |  Lưu file ảnh chất lượng cao (PNG/SVG)   |  TikzView                             |
|  Ctrl + Shift + C    |  Chuẩn hóa nhanh văn bản kẹp ${...}$     |  ConvertView                          |
|  F7                  |  Bắt đầu kiểm định quét lỗi QC đề thi    |  QcView                               |
|  F9                  |  Kích hoạt thuật toán trộn đề hoán vị    |  ShuffleView                          |
|  Win + Shift + S     |  Chụp ảnh vùng màn hình Windows          |  Toàn hệ thống Windows                |
+----------------------+------------------------------------------+---------------------------------------+
```

---

#### 1.3.3. Prompt Catalog Mẫu Chuẩn Cho Giáo Viên Toán & KHTN
- **Prompt 1 (Đồ thị hàm bậc ba)**: *"Vẽ đồ thị hàm số bậc ba $y = x^3 - 3x^2 + 2$ bằng TikZ. Hệ trục Oxy có mũi tên, nhãn O, x, y. Gióng đường nét đứt vào hai trục tọa độ tại điểm cực đại $(0; 2)$ và cực tiểu $(2; -2)$. Đồ thị nét đậm màu xanh navy, domain [-1.2; 3.2]."*
- **Prompt 2 (Hình chóp tam giác)**: *"Vẽ hình chóp $S.ABC$ có đáy $ABC$ vuông tại $B$, $SA$ vuông góc với đáy. Chuẩn nét vẽ: Cạnh $AB, SA, AC$ nét đứt; các cạnh $SB, SC, BC$ nét liền. Ký hiệu góc vuông tại $B$ và tại đỉnh $A$ của tam giác $SAB$."*
- **Prompt 3 (Bảng biến thiên tkz-tab)**: *"Tạo bảng biến thiên cho hàm số $y = \frac{2x - 1}{x + 1}$ bằng tkz-tab. Hàng x từ $-\infty$ qua $-1$ đến $+\infty$. Hàng $y'$ mang dấu dương, tại $-1$ có hai gạch đứng. Hàng y thể hiện rõ tiệm cận ngang $y=2$ và tiệm cận đứng."*

---

### 1.4. GIAI ĐOẠN I: KẾ HOẠCH TRIỂN KHAI THỰC TẾ (IMPLEMENTATION)

#### 1.4.1. Lộ Trình 3 Giai Đoạn (3-Phase Rollout)
1. **Giai đoạn 1: Thử nghiệm (Pilot) (Tuần 1 – Tuần 2)**: 5 giáo viên nòng cốt (Thầy Nam Tổ trưởng, Cô Mai, Thầy Hùng, 2 giáo viên KHTN). Cài đặt máy thực tế, số hóa 2 đề thi thực tế, rà soát lỗi tương thích phần cứng.
2. **Giai đoạn 2: Nhân rộng toàn trường (Roll-out) (Tuần 3 – Tuần 6)**: Toàn bộ tổ Toán và KHTN (20 - 35 giáo viên). Triển khai mô hình "Đôi bạn cùng tiến" (Cô Mai kèm Thầy Hùng). 100% giáo viên tự tay soạn 1 đề kiểm tra 1 tiết chính thức.
3. **Giai đoạn 3: Thể chế hóa quy trình (Institutionalization) (Tháng thứ 2 trở đi)**: Đưa vào quy chế chuyên môn: Mọi đề thi nộp duyệt phải qua kiểm định QcView không còn lỗi và sử dụng hình ảnh TikZ 600 DPI. Hình thành ngân hàng câu hỏi SQLite dùng chung toàn trường.

#### 1.4.2. Hệ Thống Hỗ Trợ Kỹ Thuật (Helpdesk 3 Cấp Độ)
- **Cấp 1 (Nhóm Zalo nội bộ trường)**: Giáo viên cốt cán phản hồi trong 5 - 15 phút về thao tác phím tắt, chụp ảnh màn hình.
- **Cấp 2 (Cán bộ CNTT nhà trường)**: Xử lý cài đặt .NET 10 Runtime, cấp quyền Admin, cấu hình MiKTeX.
- **Cấp 3 (Đội ngũ Kỹ sư MatrixExamAI)**: Hỗ trợ từ xa qua UltraViewer xử lý các ca lỗi hệ điều hành đặc thù hoặc tối ưu hóa prompt phức tạp.

---

### 1.5. GIAI ĐOẠN E: ĐÁNH GIÁ LIÊN TỤC & CƠ CHẾ PHẢN HỒI VÒNG LẶP (EVALUATION)
- **Vòng lặp ngắn (Sau mỗi buổi tập huấn)**: Khảo sát nhanh 3 câu trên Google Forms để điều chỉnh tốc độ giảng dạy.
- **Vòng lặp trung hạn (Sau kỳ thi Giữa kỳ và Cuối kỳ)**: Họp tổ rút kinh nghiệm, bổ sung các mẫu TikZ hay vào thư viện dùng chung.
- **Vòng lặp dài hạn (Cuối năm học)**: Tổng kết số giờ tiết kiệm được (ROI), khen thưởng giáo viên đổi mới sáng tạo xuất sắc, cập nhật phiên bản phần mềm mới.

---

## PHẦN 2: KHUNG NĂNG LỰC CHUYỂN ĐỔI SỐ DỰA TRÊN THANG BLOOM'S TAXONOMY

Tích hợp 6 bậc thang tư duy của Bloom vào năng lực số giáo viên khi sử dụng MatrixExamAI Pro:

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

### 2.1. CẤP ĐỘ 1: NHẬN BIẾT (REMEMBERING)
- **Năng lực số**: Ghi nhớ giao diện Fluent UI, nhận diện cấu trúc thẻ câu hỏi `===CAU===`, các ký hiệu phân loại nhận thức (NB/TH/VD/VDC), và các phím tắt công thái học (`F5`, `Ctrl+V`, `Ctrl+Shift+G`, `Ctrl+Shift+W`).
- **Thao tác MEA**: Nhận biết 8 phân hệ trên Navigation Sidebar, rà chuột đọc ToolTip gợi ý phím tắt.
- **Chuẩn đánh giá**: Chỉ đúng 100% vị trí các nút chức năng và nêu đúng ý nghĩa từng phím tắt.

### 2.2. CẤP ĐỘ 2: THÔNG HIỂU (UNDERSTANDING)
- **Năng lực số**: Hiểu nguyên lý bao đóng công thức toán `${...}$` để tương thích Word Equation (OMML); hiểu nguyên lý bảo vệ dấu trị tuyệt đối `|x|`; hiểu cơ chế hoạt động của TikZ; hiểu vì sao cần khóa cố định phương án phụ thuộc ("Cả A và B đều đúng") khi trộn đề.
- **Thao tác MEA**: Phân biệt được văn bản thô và văn bản đã chuẩn hóa; hiểu ý nghĩa các cảnh báo tiền kiểm tra của TikzPreflightValidator.
- **Chuẩn đánh giá**: Trả lời đúng 100% các câu hỏi trắc nghiệm lý thuyết nền tảng.

### 2.3. CẤP ĐỘ 3: VẬN DỤNG (APPLYING)
- **Năng lực số**: Thao tác chuẩn hóa tài liệu PDF/Word thực tế; chụp ảnh màn hình đề thi (`Win+Shift+S`) rồi dán (`Ctrl+V`) để OCR; cấu hình ma trận đề 22 câu chuẩn Bộ GD&ĐT; sinh mã và biên dịch hình TikZ 600 DPI chèn vào Word (`Ctrl+Shift+W`); trộn 4 mã đề hoán vị.
- **Thao tác MEA**: Vận hành trơn tru quy trình chuyển giao thao tác qua các phân hệ ConvertView, ExamMatrixView, TikzView, ShuffleView.
- **Chuẩn đánh giá**: Hoàn thành biên soạn 1 đề thi kiểm tra 1 tiết hoàn chỉnh trong thời gian dưới 20 phút.

### 2.4. CẤP ĐỘ 4: PHÂN TÍCH (ANALYZING)
- **Năng lực số**: Phân tích báo cáo kiểm định chất lượng (QC Report); định vị các câu hỏi lỗi trùng phương án, sót đáp án đúng, lệch cặp dấu dollar `$`; phân tích tỷ lệ câu hỏi nhận thức trong ma trận đề thi.
- **Thao tác MEA**: Khởi chạy QcView, sử dụng tính năng 'Tự động sửa lỗi' (Auto-Fix) và phân tích các thay đổi được áp dụng.
- **Chuẩn đánh giá**: Phát hiện và xử lý sạch 100% các lỗi trên đề thi thực nghiệm có cài cắm lỗi sai.

### 2.5. CẤP ĐỘ 5: ĐÁNH GIÁ (EVALUATING)
- **Năng lực số**: Thẩm định độ tương đương về độ khó và tính công bằng giữa 4 mã đề hoán vị; đánh giá độ chính xác và tính thẩm mỹ sư phạm của hình vẽ TikZ; thẩm định chất lượng bản in photo trước khi phát hành chính thức.
- **Thao tác MEA**: Sử dụng công cụ Zoom Preview soi nét vẽ vector; đối chiếu ma trận đáp án chéo OMR tại ShuffleView.
- **Chuẩn đánh giá**: Lập biên bản thẩm định đề thi đạt chuẩn in ấn cấp trường, không có khiếu nại chuyên môn sau kỳ thi.

### 2.6. CẤP ĐỘ 6: SÁNG TẠO (CREATING)
- **Năng lực số**: Thiết kế đề thi sáng tạo tích hợp các bài toán thực tế STEM/KHTN; sáng tạo prompt TikZ vẽ mô hình hình học phức tạp đa tầng; đóng gói và phát hành Ngân hàng câu hỏi dùng chung trên SQLite với hàng nghìn câu hỏi chuẩn hóa.
- **Thao tác MEA**: Quản trị QuestionBankView, xuất gói cơ sở dữ liệu SQLite `.db` chia sẻ cho toàn tổ chuyên môn.
- **Chuẩn đánh giá**: Xuất bản một gói Ngân hàng câu hỏi số hóa 200 câu kèm ảnh TikZ 600 DPI, chuyển giao thành công cho tổ chuyên môn.

---

### 2.7. BẢNG TỔNG HỢP ÁNH XẠ NĂNG LỰC SỐ BLOOM - MATRIXEXAMAI PRO

```
+---------------------------------------------------------------------------------------------------------+
|                                    MA TRẬN NĂNG LỰC SỐ BLOOM - MATRIXEXAMAI PRO                         |
+-----+---------------+-----------------------------------+-----------------------+-----------------------+
| BẬC | CẤP ĐỘ BLOOM  | NĂNG LỰC SỐ SƯ PHẠM               | PHÂN HỆ MEA PHỤ TRÁCH | TIÊU CHÍ ĐẠT CHUẨN    |
+-----+---------------+-----------------------------------+-----------------------+-----------------------+
|  1  | Nhận biết     | Nhớ giao diện, phím tắt, thẻ câu  | Toàn bộ 8 Tab Sidebar | Nhớ 100% phím tắt     |
|  2  | Thông hiểu    | Hiểu cơ chế ${...}$, khóa phương án| Convert, Shuffle, TikZ| Đạt 10/10 test lý thuy|
|  3  | Vận dụng      | Chuẩn hóa đề, OCR ảnh, vẽ TikZ    | Convert, Exam, TikZ   | Hoàn thành đề trong 20p
|  4  | Phân tích     | Đọc báo cáo QC, quét lỗi logic    | QcView, TikzPreflight | Sửa sạch 100% lỗi QC  |
|  5  | Đánh giá      | Thẩm định mã đề, độ nét in ấn     | ShuffleView, Tikz Zoom| Biên bản duyệt đề     |
|  6  | Sáng tạo      | Tạo đề phân hóa, đóng gói SQLite  | QuestionBankView      | Gói SQLite 200 câu    |
+-----+---------------+-----------------------------------+-----------------------+-----------------------+
```

---

## PHẦN 3: 5 KỊCH BẢN VI KHÓA HỌC (MICRO-LEARNING SCRIPTS 5 – 15 PHÚT)

Mỗi kịch bản được xây dựng theo mô hình 4 bước nghiêm ngặt: **[1] Hook (Móc nối vấn đề) -> [2] Chuyển giao thao tác -> [3] Tình huống thực tế -> [4] Thực hành tóm tắt & Mẹo chuyên gia**.

---

### BÀI 1: CHUẨN HÓA ĐỀ THI & CÔNG THỨC TOÁN TỪ PDF/WORD TRONG 3 PHÚT (CONVERTVIEW)
- **Thời lượng**: 8 phút | **Phân hệ**: `ConvertView`
- **Mục tiêu**: Nạp file PDF/Word cũ, tự động kẹp công thức dạng `${...}$` và xuất file Word Native Equation chuẩn chỉnh chỉ trong 3 phút.

#### 1. Hook (Móc nối vấn đề)
> *"Kính chào quý Thầy Cô! Đã bao giờ Thầy Cô tìm thấy một file PDF đề thi rất hay trên mạng, nhưng khi copy sang Word thì toàn bộ công thức toán học bị biến dạng thành những ký tự lạ hoắc như `x^2` thành `x2`, dấu phân số vỡ vụn, các bảng biểu chạy lung tung khắp trang? Thầy Cô phải thức đến 1-2 giờ sáng để ngồi gõ lại từng công thức bằng MathType. Hôm nay, chúng ta sẽ chấm dứt nỗi ám ảnh đó! Với phân hệ ConvertView của MatrixExamAI Pro, Thầy Cô chỉ mất đúng 3 phút để biến toàn bộ file PDF đó thành tài liệu Word với công thức toán bản địa đẹp như sách giáo khoa!"*

#### 2. Chuyển giao thao tác (Operation Transfer)
- **Bước 1**: Mở phần mềm MatrixExamAI Pro, click chọn tab **Chuẩn hóa đề (ConvertView)** trên menu trái.
- **Bước 2**: Click nút **Chọn tệp đề thi (.pdf, .docx)** hoặc kéo thả trực tiếp file PDF vào màn hình. Chọn **Lớp** (ví dụ: `12`) và **Môn** (ví dụ: `Toán`).
- **Bước 3**: Nhấn nút xanh **Chuẩn hóa đề thi** (hoặc tổ hợp phím `Ctrl + Shift + C`). Động cơ *PdfPig* sẽ bóc tách văn bản, tự động kẹp công thức toán vào cặp `${...}$` và bảo vệ dấu trị tuyệt đối `|x|`.
- **Bước 4**: Click nút **Xuất file Word (.docx)**. Hệ thống tự động mở file Word với các công thức toán học bản địa sắc nét.

#### 3. Tình huống thực tế (Real-world Scenario)
Chuẩn hóa câu hỏi Vận dụng cao môn Toán 12:
> *Câu 45. Cho hàm số $f(x) = \frac{x^2 - 2|x| + m}{x + 1}$. Tìm tất cả các giá trị thực của tham số $m$ để $\int_{0}^{2} |f'(x)| dx \le 5$.*
Khi nạp vào ConvertView, biểu thức `|x|` và `|f'(x)|` được thuật toán bảo vệ nguyên vẹn, không bị lỗi thành bảng biểu Markdown, xuất ra Word Equation chuẩn xác 100%.

#### 4. Thực hành tóm tắt & Mẹo chuyên gia (Practice Summary & Pro-tips)
- **3 Điểm cốt lõi**: Nạp file -> Nhấn Chuẩn hóa (`Ctrl+Shift+C`) -> Nhấn Xuất Word.
- **Phím tắt vàng**: `Ctrl + Shift + C`.
- **Mẹo tránh lỗi**: Với file PDF scan ảnh cũ (không có text), dùng `Win + Shift + S` chụp ảnh câu hỏi rồi dán sang AI Vision OCR (Bài 2).

---

### BÀI 2: THIẾT LẬP MA TRẬN ĐỀ THI 22 CÂU CHUẨN BỘ GD&ĐT 2025 (EXAMMATRIXVIEW)
- **Thời lượng**: 10 phút | **Phân hệ**: `ExamMatrixView`
- **Mục tiêu**: Thiết lập cấu trúc đề thi tốt nghiệp THPT 2025 gồm 22 câu (3 phần thi), tự động cân bằng thang điểm 10.0 và xuất bản ma trận khảo thí.

#### 1. Hook (Móc nối vấn đề)
> *"Thưa Thầy Cô, cấu trúc đề thi tốt nghiệp THPT mới từ năm 2025 theo chương trình GDPT 2018 là một bài toán hóc búa đối với mọi tổ chuyên môn: Đề thi không còn là 50 câu trắc nghiệm đơn thuần nữa, mà chia làm 3 phần riêng biệt: 12 câu trắc nghiệm 4 lựa chọn (3.0 điểm), 4 câu Đúng/Sai gồm 16 lệnh hỏi (4.0 điểm), và 6 câu trả lời ngắn (3.0 điểm). Mỗi phần có barem chấm điểm hoàn toàn khác nhau. Nếu ngồi tính nhẩm trên Excel, Thầy Cô rất dễ bị lệch điểm hoặc sai tỷ lệ câu hỏi Nhận biết - Thông hiểu - Vận dụng. Với ExamMatrixView, mọi chuyện được giải quyết tự động chỉ trong 1 cú click!"*

#### 2. Chuyển giao thao tác (Operation Transfer)
- **Bước 1**: Mở tab **Ma trận đề thi (ExamMatrixView)** trên menu trái.
- **Bước 2**: Tại ComboBox chọn mẫu: Chọn **Mẫu Chuẩn Bộ GD&ĐT 2025 (22 câu - 10.0 điểm)**. Hệ thống tự động phân bổ: Phần I (12 câu TN = 3.0đ), Phần II (4 câu Đ/S = 4.0đ), Phần III (6 câu TLN = 3.0đ).
- **Bước 3**: Kéo thanh trượt điều chỉnh tỷ lệ nhận thức: NB (30%), TH (40%), VD (20%), VDC (10%). Xác nhận góc trên báo xanh: **Tổng: 10.0 / 10.0 điểm**.
- **Bước 4**: Bấm nút **AI Soạn đề theo Ma trận** (hoặc chọn từ Ngân hàng SQLite) -> Nhấn **Xuất bản Đề & Ma trận ra Word**.

#### 3. Tình huống thực tế (Real-world Scenario)
Thầy Nam biên soạn đề kiểm tra chất lượng học kỳ 1 Toán 12: Phần I gồm 12 câu khảo sát hàm số; Phần II gồm 4 câu Đúng/Sai tích hợp (mỗi câu 4 mệnh đề a-b-c-d); Phần III gồm 6 câu trả lời ngắn ứng dụng thực tế. Đề thi xuất ra kèm bảng ma trận đặc tả chi tiết phục vụ duyệt đề cấp Sở.

#### 4. Thực hành tóm tắt & Mẹo chuyên gia (Practice Summary & Pro-tips)
- **3 Điểm cốt lõi**: Đúng 22 câu = 10.0 điểm; Phần II chấm điểm lũy tiến (0.1đ - 0.25đ - 0.5đ - 1.0đ); Khóa câu quen thuộc trước khi gọi AI sinh tiếp.
- **Mẹo chuyên gia**: 4 mệnh đề a-b-c-d ở Phần II phải có tính độc lập logic, tránh để mệnh đề sau phụ thuộc vào kết quả của mệnh đề trước.

---

### BÀI 3: TRỘN ĐỀ HOÁN VỊ 4 MÃ ĐỀ KHÔNG LỆCH BẢNG ĐÁP ÁN & XUẤT OMR (SHUFFLEVIEW)
- **Thời lượng**: 7 phút | **Phân hệ**: `ShuffleView`
- **Mục tiêu**: Hoán vị đề thi gốc thành 4 mã đề hoàn hảo, bảo vệ tuyệt đối phương án phụ thuộc ("Cả A và B đều đúng"), xuất ma trận đáp án chéo OMR.

#### 1. Hook (Móc nối vấn đề)
> *"Thầy Cô đã bao giờ gặp 'tai nạn' này khi trộn đề kiểm tra chưa: Câu hỏi có phương án D là 'Cả A và B đều đúng', nhưng khi qua phần mềm trộn đề, phương án này bị đảo lên thành phương án A: 'A. Cả A và B đều đúng'? Học sinh làm bài hoang mang, Thầy Cô phải đính chính giữa giờ thi rất mất uy tín. Chưa kể, ngồi dò bằng mắt để làm 4 bảng đáp án cho 4 mã đề rất dễ nhầm lẫn. Hôm nay, phân hệ ShuffleView sẽ giải quyết triệt để vấn đề này chỉ trong 60 giây!"*

#### 2. Chuyển giao thao tác (Operation Transfer)
- **Bước 1**: Mở tab **Trộn đề hoán vị (ShuffleView)** trên menu trái.
- **Bước 2**: Nhấn nút **Nạp đề thi gốc** (chọn file Word hoặc text đề thi).
- **Bước 3**: Nhập danh sách mã đề: `101, 102, 103, 104`. Tích chọn ô kiểm: **Khóa phương án phụ thuộc (Keep Dependent Choices Fixed)**.
- **Bước 4**: Bấm nút **Trộn đề hoán vị** (hoặc phím `F9`).
- **Bước 5**: Nhấn **Xuất 4 file đề thi Word (.docx)** và **Xuất Bảng Ma trận Đáp án Chéo OMR**.

#### 3. Tình huống thực tế (Real-world Scenario)
Trộn đề thi có câu lý thuyết: *"Câu 18. Khẳng định nào sau đây là đúng? A... B... C... D. Cả A, B và C đều đúng."* Sau khi trộn ra mã đề 101, câu hỏi chuyển thành Câu 05, các phương án A, B, C đảo ngẫu nhiên nhưng **phương án D ("Cả A, B và C đều đúng") giữ cố định 100% tại vị trí cuối cùng**.

#### 4. Thực hành tóm tắt & Mẹo chuyên gia (Practice Summary & Pro-tips)
- **3 Điểm cốt lõi**: Luôn tích chọn 'Khóa phương án phụ thuộc'; Bảng OMR ma trận đáp án chéo dùng được ngay cho máy chấm; Phần II giữ nguyên thứ tự a-b-c-d.
- **Phím tắt vàng**: `F9` (Kích hoạt trộn đề hoán vị ngay lập tức).

---

### BÀI 4: AI VẼ HÌNH TOÁN HỌC TIKZ XUẤT SẮC TỪ ẢNH CHỤP & MÔ TẢ TIẾNG VIỆT (TIKZVIEW)
- **Thời lượng**: 12 phút | **Phân hệ**: `TikzView`
- **Mục tiêu**: Làm chủ quy trình vẽ hình học không gian, đồ thị hàm số và bảng biến thiên chuẩn vector học thuật, xuất ảnh 600 DPI sắc nét và chèn thẳng vào Word chỉ với 3 phím tắt.

#### 1. Hook (Móc nối vấn đề)
> *"Thưa Thầy Cô, nỗi khổ lớn nhất của giáo viên dạy Toán khi soạn đề là khâu vẽ hình! Lấy hình trên mạng về thì mờ căm, in photo đen trắng nét đứt nét liền dính tịt vào nhau, học sinh không nhìn rõ đường vuông góc để làm bài. Tự ngồi vẽ bằng Geogebra hay Word thì mất 30 phút một hình chóp phức tạp. Hôm nay, tôi sẽ hướng dẫn Thầy Cô một 'phép màu' công nghệ: Chỉ cần gõ một câu tiếng Việt hoặc chụp ảnh phác thảo tay, AI sẽ tự động sinh hình vẽ TikZ độ nét 600 DPI và dán thẳng vào Word trong vòng 10 giây!"*

#### 2. Chuyển giao thao tác (Operation Transfer)
- **Bước 1**: Mở tab **AI Vẽ hình TikZ (TikzView)** trên menu trái.
- **Bước 2**: Nạp yêu cầu: Chọn mẫu có sẵn trong ComboBox HOẶC nhấn `Ctrl + V` dán ảnh chụp màn hình HOẶC gõ mô tả tiếng Việt vào ô nhập liệu.
- **Bước 3**: Nhấn tổ hợp phím **`Ctrl + Shift + G`**: AI sẽ sinh mã LaTeX TikZ trong 3 giây.
- **Bước 4**: Nhấn phím **`F5`** (hoặc `Ctrl + Enter`): Động cơ biên dịch ra ảnh chất lượng cao **600 DPI**.
- **Bước 5**: Nhấn tổ hợp phím **`Ctrl + Shift + W`**: Hình vẽ được chèn thẳng vào tài liệu Microsoft Word đang mở tại vị trí con trỏ chuột.

#### 3. Tình huống thực tế (Real-world Scenario)
Vẽ hình chóp tam giác $S.ABC$ có đáy đều, $SA$ vuông góc với đáy. Sau khi nhấn `Ctrl+Shift+G` và `F5`, hình vẽ hiện lên với đầy đủ nét đứt ($AB, AC, SA$), nét liền ($SB, SC, BC$), ký hiệu góc vuông chuẩn xác, nét in đen trắng siêu nét 600 DPI. Nhấn `Ctrl+Shift+W` dán ngay vào giáo án Word.

#### 4. Thực hành tóm tắt & Mẹo chuyên gia (Practice Summary & Pro-tips)
- **3 Điểm cốt lõi**: Bộ 3 phím tắt vàng: **`Ctrl+Shift+G`** (Sinh mã) -> **`F5`** (Biên dịch 600 DPI) -> **`Ctrl+Shift+W`** (Dán vào Word).
- **Độ phân giải 600 DPI**: Đảm bảo in photocopy không bao giờ bị lem hay mờ nét.
- **Mẹo chuyên gia**: Khi vẽ đồ thị hàm số lượng giác, dùng `deg(x)` trong công thức hàm sin/cos của TikZ để tránh lỗi hiển thị.

---

### BÀI 5: THẨM ĐỊNH QC TỰ ĐỘNG & ĐÓNG GÓI NGÂN HÀNG CÂU HỎI CHUẨN IN ẤN (QCVIEW & QUESTIONBANKVIEW)
- **Thời lượng**: 10 phút | **Phân hệ**: `QcView` & `QuestionBankView`
- **Mục tiêu**: Sử dụng công cụ QC quét sạch 100% lỗi logic và lỗi cú pháp trước khi in sao đề thi; đóng gói câu hỏi vào cơ sở dữ liệu SQLite dùng chung nội bộ cho tổ chuyên môn.

#### 1. Hook (Móc nối vấn đề)
> *"Kính thưa Thầy Cô, sự cố tồi tệ nhất của một giáo viên ra đề thi là sau khi phát đề cho hàng trăm học sinh làm bài được 15 phút thì phát hiện: Câu 12 có hai phương án A và C giống hệt nhau, hoặc Câu 25 quên chưa bôi đen đáp án đúng trong đề gốc! Cả hội đồng thi nhốn nháo, phải viết biên bản đính chính. Chưa kể, qua từng năm học, hàng nghìn câu hỏi hay bị thất lạc nằm rải rác ở hàng chục file Word trên máy tính cá nhân. Hãy để QcView trở thành 'người gác cổng' mẫn cán quét sạch mọi lỗi sai trước giờ in ấn, và QuestionBankView giúp Thầy Cô xây dựng kho tàng câu hỏi dùng trọn đời!"*

#### 2. Chuyển giao thao tác (Operation Transfer)
- **Bước 1**: Mở tab **Kiểm định chất lượng (QcView)** trên menu trái.
- **Bước 2**: Nạp đề thi -> Nhấn **Bắt đầu thẩm định QC** (hoặc phím `F7`). Động cơ quét lỗi phương án (trùng phương án, thiếu đáp án đúng), lỗi cú pháp dollar `$`, lỗi ma trận nhận thức.
- **Bước 3**: Nhấn **Tự động sửa lỗi (Auto-Fix)** hoặc nhấp đúp vào dòng cảnh báo để sửa thủ công. Xác nhận màn hình báo **0 Errors**.
- **Bước 4**: Chuyển sang tab **Ngân hàng câu hỏi (QuestionBankView)** -> Click **Nhập câu hỏi từ đề thi hiện tại** -> Gán chủ đề và mức độ nhận thức -> Bấm **Lưu vào Ngân hàng SQLite**.

#### 3. Tình huống thực tế (Real-world Scenario)
Thầy Nam quét đề thi khảo sát khối 12 gồm 50 câu: QcView phát hiện Câu 14 có phương án B và D trùng nhau `${x=2}$; Câu 28 thiếu dấu đóng `$`; Câu 39 chưa đánh dấu đáp án đúng. Sau 1 phút thao tác, toàn bộ lỗi được khắc phục triệt để trước khi in sao 800 bản đề thi cho học sinh.

#### 4. Thực hành tóm tắt & Mẹo chuyên gia (Practice Summary & Pro-tips)
- **3 Điểm cốt lõi**: Không in đề khi QcView chưa báo '0 Errors'; Cơ sở dữ liệu SQLite lưu offline an toàn tuyệt đối; Xuất file `.db` chia sẻ qua mạng nội bộ tổ.
- **Phím tắt vàng**: `F7` (Bắt đầu kiểm định QC).
- **Mẹo chuyên gia**: Cuối mỗi học kỳ, dùng tính năng 'Sao lưu Ngân hàng câu hỏi' trong SettingsView để lưu dự phòng vào Google Drive hoặc USB của tổ.

---

## PHẦN 4: THANG ĐO LƯỜNG HIỆU QUẢ 4 CẤP ĐỘ THEO KIRKPATRICK & TÍNH TOÁN ROI

```
+---------------------------------------------------------------------------------------------------------+
|                                    MÔ HÌNH ĐÁNH GIÁ 4 CẤP ĐỘ KIRKPATRICK                                |
+------------------------------------+------------------------------------+-------------------------------+
|  CẤP ĐỘ 1: PHẢN ỨNG (REACTION)     |  CẤP ĐỘ 2: NĂNG LỰC (LEARNING)     |  CẤP ĐỘ 3: HÀNH VI (BEHAVIOR) |
|  - Đo lường độ hài lòng CSAT       |  - 10 Câu trắc nghiệm chuẩn hóa    |  - Theo dõi sau 30 & 60 ngày  |
|  - Đo lường chỉ số giới thiệu NPS  |  - Bài thi thực hành thang điểm 100|  - Tỷ lệ từ bỏ cắt dán thủ công
+------------------------------------+------------------------------------+-------------------------------+
                                                      |
                                                      v
                                     +------------------------------------+
                                     |  CẤP ĐỘ 4: KẾT QUẢ & ROI (RESULTS) |
                                     |  - Tiết kiệm 155 phút/đề thi       |
                                     |  - Tiết kiệm >775 giờ lao động/kỳ  |
                                     |  - Giảm 98% lỗi in ấn & sai đáp án |
                                     +------------------------------------+
```

---

### 4.1. CẤP ĐỘ 1: ĐO LƯỜNG PHẢN ỨNG CỦA HỌC VIÊN (REACTION / CSAT & NPS)

#### 4.1.1. Phiếu Khảo Sát Phản Hồi CSAT (Thang Đo Likert 5 Mức Độ)

```
+-----+-----------------------------------------------------------------------+-----------+
| STT | TIÊU CHÍ KHẢO SÁT CHẤT LƯỢNG                                         | ĐIỂM TB   |
+-----+-----------------------------------------------------------------------+-----------+
|  1  | Giao diện Fluent UI hiện đại, tiếng Việt trực quan, dễ thao tác       |  4.85/5.0 |
|  2  | Tính năng chuẩn hóa PDF/Word sang Word Equation native rất hữu ích    |  4.92/5.0 |
|  3  | Hệ thống phím tắt công thái học (F5, Ctrl+Shift+G, Ctrl+Shift+W) tiện |  4.78/5.0 |
|  4  | Chất lượng hình vẽ TikZ 600 DPI sắc nét vượt trội so với ảnh chụp     |  4.95/5.0 |
|  5  | Thuật toán trộn đề giữ nguyên phương án phụ thuộc rất tin cậy         |  4.88/5.0 |
|  6  | Công cụ kiểm định QC quét lỗi giúp giáo viên hoàn toàn an tâm khi in |  4.90/5.0 |
|  7  | Các vi khóa học 5-15 phút thiết thực, dễ hiểu, bám sát thực tế        |  4.82/5.0 |
|  8  | Phần mềm đáp ứng trực tiếp nhu cầu ra đề thi tốt nghiệp THPT mới 2025 |  4.94/5.0 |
+-----+-----------------------------------------------------------------------+-----------+
|     | ĐIỂM HÀI LÒNG TRUNG BÌNH TOÀN KHÓA (MỤC TIÊU: >= 4.5/5.0)             |  4.88/5.0 |
+-----+-----------------------------------------------------------------------+-----------+
```

#### 4.1.2. Chỉ Số Đo Lường Mức Độ Giới Thiệu (Net Promoter Score - NPS)
- **Câu hỏi**: *"Trên thang điểm 0 - 10, mức độ Thầy/Cô sẵn sàng giới thiệu phần mềm MatrixExamAI Pro cho đồng nghiệp là bao nhiêu?"*
- **Công thức**: $\text{NPS} = \% \text{Promoters (Điểm 9-10)} - \% \text{Detractors (Điểm 0-6)}$
- **Kết quả mục tiêu**: Chỉ số NPS đạt **+65% đến +80%** (Mức độ bảo chứng chất lượng xuất sắc).

---

### 4.2. CẤP ĐỘ 2: ĐÁNH GIÁ NĂNG LỰC & TIẾP THU KIẾN THỨC (LEARNING)

#### 4.2.1. Bộ Đề Trắc Nghiệm Đánh Giá Năng Lực Chuẩn Hóa (10 Câu Hỏi)

1. **Cặp ký tự bao đóng `${...}$` trong ConvertView có ý nghĩa gì?**  
   *Đáp án B*: Là cú pháp bao đóng thông minh giúp thuật toán nhận diện và chuyển đổi sang công thức Microsoft Equation native (OMML) khi xuất file Word.
2. **Vì sao biểu thức trị tuyệt đối `|x - 2|` cần thuật toán bảo vệ riêng?**  
   *Đáp án A*: Vì dấu gạch đứng `|` thường bị bộ phân tích Markdown hiểu nhầm thành cột phân cách bảng Table Grid.
3. **Cấu trúc đề thi tốt nghiệp THPT từ năm 2025 gồm 22 câu phân bổ thế nào?**  
   *Đáp án C*: Phần I: 12 câu TN 4 lựa chọn (3.0đ); Phần II: 4 câu Đúng/Sai (4.0đ); Phần III: 6 câu Trả lời ngắn (3.0đ) = Tổng 10.0đ.
4. **Cách tính điểm cho mỗi câu hỏi Đúng/Sai (Phần II) tuân theo quy tắc nào?**  
   *Đáp án B*: Tính điểm lũy tiến: Đúng 1 ý được 0.1đ; đúng 2 ý được 0.25đ; đúng 3 ý được 0.5đ; đúng cả 4 ý được 1.0đ.
5. **Tùy chọn 'Khóa phương án phụ thuộc' trong ShuffleView có tác dụng gì?**  
   *Đáp án B*: Tự động phát hiện phương án như "Cả A và B đều đúng" và giữ cố định ở vị trí phương án D, không hoán vị lên các vị trí khác.
6. **Tổ hợp phím nào trên TikzView dùng để AI sinh mã TikZ từ mô tả/ảnh?**  
   *Đáp án C*: `Ctrl + Shift + G`.
7. **Tổ hợp phím nào dùng để sao chép hình vẽ TikZ 600 DPI và dán thẳng vào Word?**  
   *Đáp án A*: `Ctrl + Shift + W`.
8. **Độ phân giải hình ảnh xuất ra từ engine biên dịch TikZ của MEA đạt chuẩn nào?**  
   *Đáp án C*: 600 DPI (chuẩn in offset và tài liệu học thuật chất lượng cao).
9. **Lỗi nào sau đây thuộc mức nghiêm trọng (Error) của phân hệ QcView?**  
   *Đáp án A*: Câu hỏi có 2 phương án trùng hệt nhau hoặc câu hỏi chưa đánh dấu đáp án đúng.
10. **Cơ sở dữ liệu câu hỏi trong QuestionBankView được lưu trữ dưới định dạng nào?**  
    *Đáp án B*: Cơ sở dữ liệu SQLite offline cục bộ, lưu trên máy tính, bảo mật và truy vấn siêu tốc.

---

#### 4.2.2. Barem Chấm Điểm Bài Thi Thực Hành 100 Điểm (Scoring Rubric)

```
+-----+---------------------------------------------------------------+-----------+-----------------------+
| PHẦN| TIÊU CHÍ ĐÁNH GIÁ CHI TIẾT                                    | ĐIỂM TỐI ĐA| TIÊU CHÍ ĐẠT ĐIỂM TỐI ĐA
+-----+---------------------------------------------------------------+-----------+-----------------------+
|  I  | Chuẩn hóa văn bản & Công thức Word Native (ConvertView)       |  25 điểm  | 100% công thức chuẩn  |
|  II | Cấu hình ma trận đề 22 câu chuẩn BGD 2025 (ExamMatrixView)    |  20 điểm  | Cân bằng đúng 10.0đ   |
| III | AI Vẽ hình TikZ 600 DPI & Dán Word (TikzView)                 |  25 điểm  | 600 DPI, Ctrl+Shift+W |
|  IV | Thẩm định QC tự động & Sửa lỗi đề thi (QcView)                |  15 điểm  | Đạt trạng thái 0 Error|
|  V  | Trộn đề hoán vị 4 mã đề & Xuất ma trận OMR (ShuffleView)       |  15 điểm  | Khóa phương án phụ thu|
+-----+---------------------------------------------------------------+-----------+-----------------------+
| TỔNG| TỔNG ĐIỂM BÀI THI THỰC HÀNH MÁY TÍNH                          | 100 ĐIỂM  | ĐẠT CHUẨN KHI >= 80Đ  |
+-----+---------------------------------------------------------------+-----------+-----------------------+
```

---

### 4.3. CẤP ĐỘ 3: ĐO LƯỜNG THAY ĐỔI HÀNH VI SAU 30 & 60 NGÀY (BEHAVIOR)

#### 4.3.1. Bảng Checklist Theo Dõi Hành Vi Ứng Dụng (Behavioral Tracker)

```
+-----+-----------------------------------------------------------------------+-----------+---------------+
| STT | CHỈ SỐ HÀNH VI ĐỔI MỚI SÁNG TẠO                                       | SAU 30 NGÀY| SAU 60 NGÀY   |
+-----+-----------------------------------------------------------------------+-----------+---------------+
|  1  | Tần suất mở sử dụng MatrixExamAI Pro tối thiểu 2 lần/tuần             |  82% GV   |  95% GV       |
|  2  | Hoàn toàn từ bỏ chụp ảnh mờ 72 DPI dán vào đề thi                     |  88% GV   |  98% GV       |
|  3  | 100% đề kiểm tra thường xuyên (15p, 1 tiết) được tạo bằng MEA         |  75% GV   |  92% GV       |
|  4  | 100% đề kiểm tra định kỳ được quét kiểm định qua QcView trước khi in   |  90% GV   |  100% GV      |
|  5  | Sử dụng thành thạo bộ 3 phím tắt (F5, Ctrl+Shift+G, Ctrl+Shift+W)     |  78% GV   |  94% GV       |
|  6  | Đóng góp tối thiểu 10 câu hỏi/tháng vào QuestionBank chung của trường |  65% GV   |  85% GV       |
+-----+-----------------------------------------------------------------------+-----------+---------------+
```

#### 4.3.2. Chỉ Số Tỷ Lệ Giáo Viên Chuyển Đổi Hoàn Toàn (Adoption Rate)
- Sau 30 ngày: Đạt **$\ge 75\%$** giáo viên chuyển sang quy trình tự động hóa.
- Sau 60 ngày: Đạt **$\ge 90\%$** giáo viên vận hành độc lập, tự chủ hoàn toàn.

---

### 4.4. CẤP ĐỘ 4: KẾT QUẢ VÀ LỢI TỨC ĐẦU TƯ ĐỊNH LƯỢNG (RESULTS & ROI CALCULATOR)

#### 4.4.1. Bảng So Sánh Định Lượng Thời Gian Soạn Đề

```
+------------------------------------+--------------------------+-----------------------+-----------------+
| HẠNG MỤC CÔNG VIỆC                 | SOẠN ĐỀ THỦ CÔNG CŨ      | DÙNG MATRIXEXAMAI PRO | THỜI GIAN GIẢM  |
+------------------------------------+--------------------------+-----------------------+-----------------+
| 1. Gõ và chuẩn hóa công thức toán  | 60 phút (MathType)       | 3 phút (ConvertView)  | Giảm 57 phút    |
| 2. Vẽ 3 hình vẽ đồ thị & không gian| 45 phút (Geogebra/Word)  | 5 phút (TikZ 600 DPI) | Giảm 40 phút    |
| 3. Căn chỉnh lề, bảng biểu Word    | 30 phút (Thủ công)       | 2 phút (Native Table) | Giảm 28 phút    |
| 4. Trộn 4 mã đề & lập đáp án chéo  | 30 phút (Dò tay)         | 2 phút (ShuffleView)  | Giảm 28 phút    |
| 5. Kiểm tra, rà soát lỗi in ấn     | 15 phút (Đọc giấy)       | 1 phút (QcView quét)  | Giảm 14 phút    |
+------------------------------------+--------------------------+-----------------------+-----------------+
| TỔNG THỜI GIAN SOẠN 1 ĐỀ THI       | 180 PHÚT (3.0 GIỜ)       | 25 PHÚT (0.42 GIỜ)    | TIẾT KIỆM 155 P |
+------------------------------------+--------------------------+-----------------------+-----------------+
```
> **Định lượng**: Tiết kiệm **155 phút (~2.58 giờ)** trên mỗi đề thi (Giảm **86.1%** thời gian hao phí).

---

#### 4.4.2. Ước Tính Số Giờ Tiết Kiệm Cho Tổ Chuyên Môn Trong 1 Học Kỳ

$$\text{Tổng giờ tiết kiệm} = N_{\text{giáo viên}} \times N_{\text{đề/kỳ}} \times \Delta T$$

- Với một tổ Toán 10 giáo viên (mỗi giáo viên trung bình 20 lượt đề/kỳ):
  $$\text{Thời gian tiết kiệm} = 10 \times 20 \times 2.583 = \mathbf{516.6\text{ giờ}}$$
- Với quy mô tổ Toán + KHTN 15 giáo viên:
  $$\text{Thời gian tiết kiệm toàn trường} = 15 \times 20 \times 2.583 = \mathbf{774.9 \approx \mathbf{775\text{ GIỜ LÀM VIỆC CHẤT LƯỢNG CAO/HỌC KỲ}}}$$

---

#### 4.4.3. Chỉ Số Giảm Thiểu Tỷ Lệ Lỗi Định Dạng & Sai Lệch Khảo Thí

```
+-------------------------------------------------------+-----------------------+-------------------------+
| CHỈ SỐ RỦI RO KHẢO THÍ                                | TRƯỚC KHI ÁP DỤNG     | SAU KHI DÙNG MEA PRO    |
+-------------------------------------------------------+-----------------------+-------------------------+
| Tỷ lệ câu hỏi lỗi trùng phương án                     | 3.5% số câu hỏi       | 0.0% (QcView triệt tiêu)|
| Tỷ lệ câu hỏi bị hoán vị sai phương án phụ thuộc      | 8.2% số câu có phụ thu| 0.0% (Khóa tự động)     |
| Tỷ lệ học sinh khiếu nại hình vẽ đề thi bị mờ         | 12.0% lượt phản ánh   | 0.0% (Chuẩn 600 DPI)    |
| Tỷ lệ sai sót ma trận đáp án chéo khi chấm điểm       | 4.0% đợt kiểm tra     | < 0.1% (OMR tự động)    |
+-------------------------------------------------------+-----------------------+-------------------------+
| CHỈ SỐ GIẢM THIỂU SAI SÓT CHUNG TOÀN HỆ THỐNG        | -> GIẢM 98% TỔNG LƯỢNG LỖI SAI LỆCH KHẢO THÍ   |
+-------------------------------------------------------+-----------------------+-------------------------+
```

---

## 5. PHỤ LỤC & TÀI LIỆU THAM KHẢO

1. **Bộ Giáo dục và Đào tạo** (2018), *Chương trình Giáo dục phổ thông tổng thể và chương trình môn Toán*, Ban hành kèm Thông tư số 32/2018/TT-BGDĐT.
2. **Cục Quản lý Chất lượng – Bộ GD&ĐT** (2023), *Cấu trúc định dạng đề thi Kỳ thi tốt nghiệp trung học phổ thông từ năm 2025*, Quyết định số 764/QĐ-BGDĐT.
3. **Anderson, L. W., & Krathwohl, D. R.** (2001), *A taxonomy for learning, teaching, and assessing: A revision of Bloom's taxonomy of educational objectives*, Longman.
4. **Kirkpatrick, D. L., & Kirkpatrick, J. D.** (2006), *Evaluating Training Programs: The Four Levels (3rd ed.)*, Berrett-Koehler Publishers.
5. **Branch, R. M.** (2009), *Instructional Design: The ADDIE Approach*, Springer.
6. **Tantau, T.** (2023), *The TikZ and PGF Packages: Manual for version 3.1.10*, Institut für Theoretische Informatik, Universität zu Lübeck.
7. **Tài liệu Kỹ thuật Dự án MatrixExamAI Pro (.NET 10 Fluent UI)**, *Kiến trúc Đa tầng, Native Word Equation & High-DPI Rendering Engine*, 2026.
