"""Static help content displayed by the V5 Guide view."""
from __future__ import annotations


GUIDES = [
    {
        "tab": "Cài đặt",
        "icon": "⚙",
        "color": "#2563EB",
        "steps": [
            ("Chọn nhà cung cấp AI", [
                "Mở mục Cài đặt.",
                "Chọn nhà cung cấp: Google Gemini, Anthropic Claude hoặc DeepSeek.",
                "Chọn mô hình phù hợp với tốc độ, chi phí và độ phức tạp của đề.",
                "  - Mô hình nhanh phù hợp tạo đề thường ngày và xử lý batch.",
                "  - Mô hình reasoning phù hợp câu Toán phức tạp hoặc kiểm tra chất lượng.",
            ]),
            ("Nhập API Key", [
                "Dán API Key vào ô Khóa API.",
                "Nhấn Kiểm tra kết nối để xác nhận key hợp lệ.",
                "API Key được lưu cục bộ trên máy.",
            ]),
            ("Thiết lập đề mặc định", [
                "Chọn môn học và lớp.",
                "Nhập học kỳ, năm học và thời gian làm bài.",
                "Các thông tin này được dùng khi tạo đề và xuất Word.",
            ]),
        ],
    },
    {
        "tab": "Bảng câu hỏi (Ma trận đề)",
        "icon": "▦",
        "color": "#0891B2",
        "steps": [
            ("Thiết lập ma trận", [
                "Nhập số câu cho từng loại: TN, Đúng/Sai, Trả lời ngắn và Tự luận.",
                "Phân bổ theo mức độ Nhận biết, Thông hiểu và Vận dụng.",
                "Kiểm tra tổng điểm trước khi tạo đề.",
            ]),
            ("Chủ đề và yêu cầu cần đạt", [
                "Thêm chương hoặc chủ đề muốn ra đề.",
                "Ghi yêu cầu cần đạt để AI bám sát nội dung dạy học.",
                "Bật hoặc tắt từng dòng để kiểm soát phần sẽ được sinh.",
            ]),
        ],
    },
    {
        "tab": "Tạo đề nhanh",
        "icon": "⚡",
        "color": "#EA580C",
        "steps": [
            ("Tạo tự động", [
                "Mở Tạo đề nhanh và chọn lớp, thời lượng.",
                "Chọn chủ đề gợi ý hoặc thêm chủ đề mới.",
                "Nhấn Tạo ma trận để app tự phân bổ cấu trúc đề.",
            ]),
            ("Tiếp tục biên soạn", [
                "Kiểm tra và sửa ma trận nếu cần.",
                "Nhấn Tạo đề để sinh câu hỏi.",
                "Đề đang làm được giữ khi chuyển qua NHCH, Convert hoặc Theo dõi.",
            ]),
        ],
    },
    {
        "tab": "Xem đề và Xuất file",
        "icon": "📄",
        "color": "#059669",
        "steps": [
            ("Xem và sửa đề", [
                "Sau khi tạo xong, xem danh sách câu trong màn Tạo đề.",
                "Dùng thanh Sửa nhanh để nhập số câu, đi tới câu cần sửa hoặc sửa câu đang chọn.",
                "Dùng Nhân bản để sửa khi muốn tạo câu tương tự mà không giữ lỗi/QC cũ.",
                "Dùng Câu trống để thêm thủ công một câu mới vào đề hiện tại.",
                "Mở câu cần chỉnh để sửa nội dung, đáp án, lời giải hoặc ảnh.",
                "Chạy QC trước khi sử dụng đề chính thức.",
            ]),
            ("Xuất Word và nhiều mã đề", [
                "Nhấn Xuất Word để lưu file DOCX có thể chỉnh sửa tiếp.",
                "Dùng Trộn mã đề để xáo câu và đáp án TN theo từng mã.",
                "Đáp án tương ứng được xuất cùng mỗi mã đề.",
            ]),
        ],
    },
    {
        "tab": "Ngân hàng câu hỏi",
        "icon": "🏛",
        "color": "#7C3AED",
        "steps": [
            ("Tìm và chỉnh sửa", [
                "Lọc câu theo từ khóa, loại câu hoặc mức độ.",
                "Nhấn đúp một câu để mở trình sửa câu V5.",
                "Import PDF, Word hoặc ảnh để bổ sung câu mới.",
            ]),
            ("Thêm vào đề đang soạn", [
                "Tích một hoặc nhiều dòng trong cột chọn.",
                "Nhấn Thêm vào đề để đưa các câu đã chọn vào đề hiện tại.",
                "Nếu chưa có đề, ứng dụng tạo bản nháp; câu trùng được bỏ qua.",
            ]),
            ("Đồng bộ cloud", [
                "Upload hoặc tải câu hỏi khi tài khoản có quyền cloud.",
                "Kiểm tra xung đột trước khi ghi dữ liệu tải về vào NHCH local.",
            ]),
        ],
    },
    {
        "tab": "Convert",
        "icon": "⇄",
        "color": "#4F46E5",
        "steps": [
            ("Chọn Lớp & Môn trực tiếp", [
                "Chọn Lớp (Lớp 10, 11, 12...) và Môn học ngay trên thanh công cụ Convert.",
                "Không cần chuyển sang tab Cấu hình để cài đặt thông tin nữa.",
            ]),
            ("Ảnh và tài liệu", [
                "Dùng tab Ảnh để nhận diện một hoặc nhiều ảnh bằng AI Vision.",
                "Dùng tab PDF/Word để trích câu hỏi từ tài liệu hoặc trang scan.",
            ]),
            ("AI Text & Quy trình 1-Click (Auto TikZ)", [
                "Dán văn bản câu hỏi (định dạng LaTeX Ex-test hoặc khối app) vào ô bên trái.",
                "Tự động loại bỏ triệt để 100% trích dẫn nguồn AI (như [cite: 41, 42]).",
                "Nhấn nút '🚀 Xuất Word trực tiếp (Auto TikZ)' để ứng dụng thực hiện trọn gói:",
                "  1. Nhận diện & chuẩn hóa cấu trúc câu hỏi.",
                "  2. Tự động biên dịch hình vẽ TikZ sang ảnh vector EMF sắc nét + PNG preview.",
                "  3. Tự động xuất file Word chuẩn MEA v5.0 (kèm bảng số liệu) và tự động mở file Word.",
            ]),
            ("Đưa kết quả vào công việc", [
                "Double-click vào một dòng câu hỏi trong bảng để sửa trực tiếp nội dung.",
                "Dùng Copy text / Copy LaTeX, lưu vào Ngân hàng câu hỏi (NHCH) hoặc thêm vào đề thi.",
            ]),
        ],
    },
    {
        "tab": "Kiểm tra chất lượng (QC)",
        "icon": "✓",
        "color": "#DC2626",
        "steps": [
            ("Chạy kiểm tra", [
                "Tải câu từ NHCH hoặc đề đang xử lý rồi chạy QC.",
                "Xem bảng kết quả để tìm câu cần sửa hoặc đánh giá lại.",
            ]),
            ("AI Review và Fix", [
                "Chọn câu có vấn đề để xem góp ý.",
                "Sửa câu và chạy lại kiểm tra trước khi xuất hoặc phát hành.",
            ]),
        ],
    },
    {
        "tab": "TikZ vẽ hình",
        "icon": "△",
        "color": "#0D9488",
        "steps": [
            ("Tạo hình", [
                "Nhập code TikZ hoặc chọn mẫu trong kho mẫu.",
                "Dùng AI để tạo hoặc sửa code từ mô tả tiếng Việt.",
                "Auto-fix hỗ trợ xử lý một số lỗi cú pháp phổ biến.",
            ]),
            ("Render và xuất", [
                "Render preview/PDF trực tiếp trong QC V5.",
                "Renderer dùng LaTeX cục bộ để tạo ảnh và PDF chất lượng cao.",
                "Dùng Overleaf khi muốn mở code TikZ trên trình duyệt để chỉnh sửa hoặc biên dịch online.",
                "Dùng Lưu EMF hoặc Copy EMF để chuyển PDF vector qua Inkscape và dán vào Word không vỡ nét.",
                "Hình render thành công được tự động đồng bộ vào Kho hình; app không tạo bản ghi trùng khi render lại cùng code.",
                "Nếu render lỗi, xem log và dùng AI heal để sửa lại code.",
            ]),
        ],
    },
    {
        "tab": "API Key và Giấy phép",
        "icon": "🔑",
        "color": "#E11D48",
        "steps": [
            ("Lấy API Key", [
                "Google Gemini: truy cập aistudio.google.com và tạo API key.",
                "Anthropic Claude: truy cập console.anthropic.com và tạo key.",
                "DeepSeek: truy cập platform.deepseek.com và tạo API key.",
                "Không chia sẻ API Key; kiểm tra kết nối sau khi nhập vào ứng dụng.",
            ]),
            ("Kích hoạt và gia hạn", [
                "Sao chép Machine ID tại màn kích hoạt khi được yêu cầu.",
                "Thực hiện theo hướng dẫn thanh toán và gửi Machine ID cho quản trị viên.",
                "Khi gia hạn, Machine ID không thay đổi.",
            ]),
        ],
    },
    {
        "tab": "Cập nhật và bảo trì",
        "icon": "🔄",
        "color": "#9333EA",
        "steps": [
            ("Kiểm tra phiên bản mới", [
                "Mở Tuỳ chọn hoặc Về MEA v5 rồi nhấn Kiểm tra cập nhật.",
                "Ứng dụng ưu tiên máy chủ cập nhật riêng và GitHub Releases theo thứ tự.",
                "Nếu có installer, nhấn Tải và cài đặt; nếu chưa có, mở trang phát hành để tải thủ công.",
                "Trước khi mở installer, app tự backup dữ liệu đầy đủ vào backups/pre_updates để có điểm rollback.",
            ]),
            ("Nhắc sau hoặc bỏ qua", [
                "Dùng Nhắc sau nếu muốn tiếp tục công việc hiện tại.",
                "Dùng Bỏ qua bản này để không hiện lại thông báo cho đúng phiên bản tùy chọn đó.",
                "Khi chủ động nhấn Kiểm tra cập nhật, app vẫn hiển thị lại bản đã bỏ qua để bạn có thể cài đặt.",
            ]),
        ],
    },
]
