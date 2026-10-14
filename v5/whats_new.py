"""
v5/whats_new.py — "What's New" dialog hiển thị changelog theo version.

Cơ chế:
    • CHANGELOG = {version: [list of bullet changes]}
    • Khi app khởi động, so settings.seen_whats_new vs __version__:
      - Nếu khác → show dialog 1 lần → set seen_whats_new = __version__
    • User cũng có thể mở qua QuickSwitcher action "whats_new"

Update CHANGELOG bằng cách add 1 key mới ở đầu dict + bump __version__.
"""
from __future__ import annotations

import customtkinter as ctk

from v5 import settings_store


# ── CHANGELOG ────────────────────────────────────────────────────────────
# Phiên bản mới nhất ở đầu dict. Mỗi entry: list[(emoji, title, desc)]
CHANGELOG: dict[str, list[tuple[str, str, str]]] = {
    "5.0.0": [
        ("🚀", "Phát hành chính thức MEA v5.0",
            "Phiên bản MEA 5.0 chính thức với giao diện hiện đại CustomTkinter, mở khóa toàn bộ tính năng."),
        ("🤖", "Cập nhật AI Models 2026 & 9Router",
            "Hỗ trợ Gemini 3.8/3.1, Claude 5, GPT-6, DeepSeek v4 và tích hợp cổng 9Router API (localhost:20128)."),
        ("🎨", "TikZ AI Skill chuẩn Thầy Đỗ Minh (WebTikZ)",
            "Tích hợp hệ sinh thái prompt, preflight kiểm tra và tự động sửa code TikZ chuyên sâu."),
        ("📱", "Giao diện chống tràn & tự động co giãn",
            "Chuẩn hóa CTkScrollableFrame cho toàn bộ các tab Convert, QC, Cấu hình, NHCH, Tạo đề."),
        ("📋", "Thông tin đề thi lên đầu",
            "Đưa khung thông tin trường, lớp, kỳ thi, giáo viên lên vị trí đầu tiên của tab Cài đặt."),
    ],
    "5.1.74-alpha": [
        ("🔓", "Mở khóa toàn bộ tính năng (Bản độc lập)",
            "Tất cả các tính năng Bảng câu hỏi, NHCH, QC, TikZ, Convert, Tạo đề nhanh, Trộn mã đề và Smart Prompt đều được mở khóa sẵn sàng sử dụng."),
        ("🛡️", "Hoạt động offline độc lập",
            "Ứng dụng tự động chuyển sang chế độ độc lập mở khóa khi database Supabase gặp lỗi, không có mạng hoặc máy chưa đăng ký."),
    ],
    "5.1.73-alpha": [
        ("✏️", "Editor câu hỏi rộng dữ liệu hơn",
            "Nội dung câu hỏi và lời giải trong dialog sửa câu được tăng chiều cao để đọc và chỉnh câu dài rõ hơn."),
        ("📋", "Đáp án dài không còn bị cắt một dòng",
            "Các phương án TN và mệnh đề Đúng/Sai chuyển sang ô nhiều dòng, giúp sửa đáp án dài, công thức hoặc lời văn không bị che khuất."),
        ("🔄", "Lưu/AI sửa vẫn tương thích dữ liệu cũ",
            "Thêm helper đọc/ghi widget để editor nhiều dòng vẫn lưu về Question model và nhận bản sửa từ AI/QC như trước."),
    ],
    "5.1.72-alpha": [
        ("📥", "Import Wizard gọn ở cửa sổ nhỏ",
            "Tuỳ chọn provider/model, lọc loại và max trang được gom vào grid responsive để không lệch hàng khi import PDF/Word/ảnh ở min-size."),
        ("📋", "Preview import giữ đủ chữ hơn",
            "Bảng câu trích được có minwidth rõ cho Loại/Mức/Nội dung và cột preview co giãn đúng kèm thanh cuộn ngang."),
        ("↔", "Footer import neo nút ổn định",
            "Các nút Lưu NHCH, Push Cloud và Đóng chuyển sang grid để vùng hành động luôn rõ, không trôi hoặc chồng ở dialog thấp."),
    ],
    "5.1.71-alpha": [
        ("🤖", "QC chọn model rõ ràng",
            "Tab QC có selector provider/model riêng cho chạy QC và AI sửa câu, đồng bộ cách chọn model với Convert và NHCH thay vì dùng model ngầm."),
        ("↔", "Toolbar QC khó tràn hơn",
            "Các nút Bắt đầu QC, Báo cáo, Áp dụng giữ một hàng riêng; progress và trạng thái chuyển xuống hàng dưới để không bị ép ở cửa sổ 1100x700."),
        ("📋", "Bảng QC đọc nội dung dài tốt hơn",
            "Cột vấn đề/gợi ý có minwidth và stretch rõ ràng, giữ horizontal scroll để lỗi dài không làm mất các cột Loại, Mức, Điểm."),
    ],
    "5.1.70-alpha": [
        ("🔄", "Bảng parity V4/V5",
            "Thêm tracker đồng bộ V4/V5 cho các workflow Tạo đề, Convert, NHCH, QC/TikZ để theo dõi business layer dùng chung, UI gap và gate test theo từng màn."),
        ("↔", "Tạo đề bớt tràn ở min-size",
            "Preview câu hỏi bỏ lỗi trộn layout grid/pack, có minwidth rõ hơn và toolbar TikZ/QC/điểm/báo lỗi tách status xuống dòng để nút không bị che ở 1100x700."),
        ("📋", "Bảng Convert/NHCH dễ đọc hơn",
            "Convert có thanh cuộn ngang cho bảng kết quả; NHCH đặt minwidth cho từng cột và cho Chủ đề/Preview co giãn đúng để nội dung dài không bị ép mất chữ."),
    ],
    "5.1.69-alpha": [
        ("🔄", "Workflow TikZ vector dùng chung V4/V5",
            "Màn Kết quả của cả hai phiên bản cùng gọi một workflow TikZ → EMF, nên cache, Inkscape, PNG preview và Word export không còn dễ lệch nhau."),
        ("📐", "V4 hiển thị đúng TikZ → EMF",
            "Nút chuyển hình trong V4 đổi tên và thông báo theo đúng kết quả vector, thay cho nhãn TikZ → Ảnh cũ."),
        ("✅", "Guard parity TikZ tự động",
            "Bổ sung test chặn V4 hoặc V5 quay lại luồng PNG riêng và kiểm tra hợp đồng PNG preview + EMF vector đến Word exporter."),
        ("↔", "Thanh hành động V4 không che nút",
            "Màn Xem đề & Xuất của V4 tách hành động thành hai hàng để TikZ → EMF, QC và tùy chọn kèm lời giải vẫn hiện đủ ở cửa sổ tối thiểu."),
    ],
    "5.1.68-alpha": [
        ("📐", "TikZ → EMF trong Tạo đề",
            "Nút chuyển hình trong màn Tạo đề nay tạo EMF vector để giữ chất lượng khi đưa sang Word, đồng thời giữ PNG preview cho card trong app."),
        ("🧩", "Slot ảnh có cặp preview/vector",
            "Pipeline TikZ lưu cặp PNG + EMF theo hash cache; card dùng PNG để xem nhanh, exporter Word ưu tiên EMF khi có thể."),
        ("⚠", "Báo rõ phụ thuộc Inkscape",
            "Nếu chưa cài Inkscape hoặc không tạo được EMF, luồng chuyển đổi báo lỗi thay vì âm thầm coi PNG là kết quả chính."),
    ],
    "5.1.67-alpha": [
        ("🖼", "Review ảnh trong Kho hình",
            "Kho NHCH hình vẽ hiển thị ảnh PNG đã render ngay trên code TikZ để chọn hình nhanh hơn, không phải đọc từng khối code dài."),
        ("📋", "Bảng kho hình dễ đọc hơn",
            "Dialog kho hình rộng hơn, cột ID/Tên/Nguồn/Tags/PNG/Ngày được nới mặc định và có thanh cuộn ngang dự phòng ở cửa sổ nhỏ."),
        ("✅", "Guard UI kho hình",
            "Bổ sung kiểm tra giữ panel ảnh render, layout bảng và liên kết PNG của từng entry trong dialog V5."),
    ],
    "5.1.66-alpha": [
        ("📝", "Editor TikZ rộng và dễ sửa hơn",
            "Vùng soạn TikZ trong QC tăng chiều cao và font monospace lớn hơn để nhìn rõ từng dòng khi chỉnh hình."),
        ("🧩", "Snippet TikZ gõ nhanh",
            "Có thể gõ #diem, #truc, #ham, #bbt, #bxd, #goc... rồi nhấn Space/Tab/Enter để bung code mẫu, hoặc chọn từ menu Chèn mẫu."),
        ("🧯", "Báo lỗi TikZ rõ nguyên nhân",
            "Preflight và render log nay phân loại thiếu ngoặc, sai môi trường, thiếu dấu chấm phẩy, thiếu package LaTeX, thiếu engine hoặc thiếu bộ chuyển PDF sang ảnh."),
    ],
    "5.1.65-alpha": [
        ("🤖", "Chọn model rõ ràng hơn",
            "Convert, Import PDF/Word/Ảnh → NHCH và AI sửa/QC trong NHCH có menu chọn model theo provider thay vì chỉ nhập tay hoặc dùng mặc định."),
        ("💎", "GEM Master prompt",
            "Prompt Gemini GEM được tổng hợp thành một mẫu duy nhất, có thêm quy tắc tạo/sửa câu hỏi, import OCR và TikZ cho MatrixExamAI."),
        ("🧭", "Sửa layout hướng dẫn và sidebar",
            "Hướng dẫn làm sạch bullet bị lệch, wrap chữ theo khung; hamburger sidebar ép đúng chiều rộng thu gọn để không còn chừa mảng trống lớn."),
    ],
    "5.1.64-alpha": [
        ("⚡", "Tăng tốc bằng lõi C++",
            "V5 nạp DLL native cho các primitive xử lý text CPU-heavy, đồng thời tự quay về Python fallback nếu DLL chưa sẵn sàng trong môi trường source."),
        ("🧩", "Import block chuẩn nhanh hơn",
            "Scanner C++ xử lý các khối ===CAU===...===KETCAU=== trong luồng Convert và Import, giảm thời gian quét payload lớn mà không đổi format dữ liệu."),
        ("📐", "Rewrite TikZ gọn và nhanh hơn",
            "Primitive native gộp dòng trống được dùng khi strip khối TikZ sau render; build EXE tự tạo và bundle DLL để artifact phát hành luôn có acceleration backend."),
    ],
    "5.1.63-alpha": [
        ("📥", "Import Wizard luôn thấy nút hoàn tất",
            "Footer hành động Lưu NHCH, Push Cloud và Đóng được neo ở đáy dialog, không còn bị preview đẩy ra khỏi viewport."),
        ("↕", "Preview import co giãn đúng",
            "Vùng danh sách câu nhận phần chiều cao còn lại thay vì làm cả wizard cuộn lồng nhau, giúp đọc bảng và thao tác ổn định hơn ở cửa sổ thấp."),
        ("🎨", "Phân cấp action rõ hơn",
            "Footer dùng surface và border token V5 để tách khu vực hoàn tất khỏi nội dung OCR mà vẫn đồng nhất Light/Dark."),
    ],
    "5.1.62-alpha": [
        ("🧭", "Sidebar gọn và có định hướng rõ",
            "Menu trái chỉ mở một nhóm tại một thời điểm, giữ đủ 9 màn hình chính trong viewport phổ biến và làm nổi bật mục đang xem."),
        ("📌", "Khôi phục đúng chế độ thu gọn",
            "Trạng thái sidebar thu gọn đã lưu được áp dụng ngay khi mở app, thay vì luôn quay về chiều rộng mặc định."),
        ("✨", "Điều hướng V5 đồng bộ",
            "Phím tắt, Quick Switcher và thao tác click đều cập nhật active state của sidebar theo cùng một nguồn route."),
    ],
    "5.1.61-alpha": [
        ("📖", "Hướng dẫn hiển thị đúng phiên bản V5",
            "Header tab Hướng dẫn lấy phiên bản trực tiếp từ package V5, không còn hiển thị nhầm phiên bản V4 dùng chung business layer."),
        ("🧩", "Một nguồn version cho runtime V5",
            "Shell, Hướng dẫn, What's New và script installer cùng bám theo v5.__version__ để tránh lệch nhãn giữa các màn hình và artifact phát hành."),
        ("✅", "Guard đồng bộ phiên bản",
            "Bổ sung regression test cho header Hướng dẫn và kiểm tra version V5 khớp changelog cùng installer_v5.iss đã sinh."),
    ],
    "5.1.60-alpha": [
        ("🌐", "Mở TikZ bằng Overleaf",
            "Toolbar preview TikZ có nút Overleaf để mở code trên trình duyệt và tự copy source .tex dự phòng vào clipboard."),
        ("📐", "TikZ → PDF → EMF vector",
            "Bổ sung Lưu EMF và Copy EMF: Inkscape chuyển PDF standalone sang EMF với chữ/công thức dạng path để dán vào Word không vỡ nét."),
        ("🗂", "Tự lưu hình sau render",
            "Hình TikZ render thành công được đồng bộ vào Kho hình. Hash code chuẩn hoá ngăn tạo bản ghi trùng khi xem hoặc render lại."),
    ],
    "5.1.59-alpha": [
        ("🛡", "Backup bắt buộc trước cập nhật",
            "Trước khi mở installer, V5 tự tạo snapshot dữ liệu đầy đủ gồm NHCH, settings, token LMS và API key đã mã hóa."),
        ("↩", "Có điểm rollback dữ liệu",
            "Snapshot được lưu riêng trong backups/pre_updates, giữ tối đa 5 bản gần nhất và ghi vào Nhật ký tác vụ để truy vết."),
        ("🧹", "Không backup ngược installer",
            "Thư mục updates được loại khỏi backup để file cài đặt lớn không bị đóng gói ngược vào snapshot trước nâng cấp."),
    ],
    "5.1.58-alpha": [
        ("🔄", "Cập nhật phần mềm thuần V5",
            "Bổ sung dialog CustomTkinter để kiểm tra phiên bản, xem nội dung phát hành, tải installer và mở trang release mà không gọi UI V4."),
        ("🌐", "Fallback nguồn phát hành rõ ràng",
            "Updater ưu tiên endpoint riêng, sau đó backend LMS đã cấu hình và cuối cùng GitHub Releases đúng repo phát hành."),
        ("🧩", "Kiểm tra ngay từ nhiều nơi",
            "Có thể mở Kiểm tra cập nhật từ Tuỳ chọn, Về MEA v5 hoặc Quick Switcher; phiên bản tùy chọn đã bỏ qua không nhắc lại khi khởi động."),
    ],
    "5.1.57-alpha": [
        ("🇻🇳", "Prompt ChatBotAI có dấu",
            "Toàn bộ mẫu Gemini GEM, ChatGPT, DeepSeek và prompt dựng động dùng tiếng Việt có dấu để đọc và chỉnh sửa dễ hơn."),
        ("🧩", "Giữ nguyên token parser",
            "Các mã ===CAU===, LOAI, DAPAN, LaTeX và TikZ vẫn giữ nguyên để import vào MatrixExamAI không đổi hành vi."),
        ("✅", "Không thêm chế độ không dấu",
            "Prompt mặc định dùng tiếng Việt có dấu; guard test chặn quay lại các tiêu đề không dấu cũ."),
    ],
    "5.1.56-alpha": [
        ("🧱", "Đủ nút thao tác Convert",
            "Hàng action kết quả chuyển thành grid 2x2 để Copy, Xuất Word, Lưu NHCH và Thêm vào đề luôn hiển thị đủ."),
        ("↔", "Co giãn theo chiều rộng khung",
            "Hai cột nút chia đều chiều rộng panel kết quả, không còn đẩy nút Thêm vào đề ra ngoài mép phải."),
        ("✅", "Guard layout action",
            "Bổ sung kiểm thử nguồn để hàng nút Convert không quay lại kiểu pack ngang dễ bị che."),
    ],
    "5.1.55-alpha": [
        ("📊", "Bảng kết quả Convert dễ đọc hơn",
            "Gộp Loại và Mức thành một cột Loại/Mức để bảng bên phải không còn bị bóp chữ ở cửa sổ hẹp."),
        ("↔", "Cột Nội dung rộng hơn",
            "Các cột nhỏ có minwidth cố định, còn Chủ đề/Nội dung co giãn theo khung, giúp xem câu hỏi thoáng hơn."),
        ("✅", "Guard chống quay lại bảng 5 cột",
            "Thêm kiểm thử nguồn để giữ layout bảng 4 cột và không tái xuất hiện lỗi Loại/Mức bị che."),
    ],
    "5.1.54-alpha": [
        ("🎛", "Convert AI Text gọn hơn",
            "Sắp lại card Prompt ChatBotAI thành bố cục ít chen nhau hơn, dùng nhãn mẫu ngắn để dropdown không đè vào ô nhập."),
        ("🧩", "Nút thao tác không bị che",
            "Vùng AI Text chuyển sang layout grid có hàng nút cố định, nên Nhận diện cục bộ và Chuẩn hóa bằng AI luôn hiện rõ khi cửa sổ thấp."),
        ("✅", "Guard layout prompt",
            "Bổ sung kiểm thử nguồn để giữ container co giãn, hàng nút cố định và menu prompt không quay lại kiểu dễ bị che."),
    ],
    "5.1.53-alpha": [
        ("📋", "Prompt ChatBotAI ngay trong Convert",
            "Tab AI Text có thư viện prompt gợi ý để copy sang Gemini GEM, ChatGPT hoặc DeepSeek rồi dán kết quả về V5."),
        ("🧠", "Nhiều dạng GEM/provider hơn V4",
            "Bổ sung các mẫu tạo TN, Đúng/Sai, trả lời ngắn, tự luận, TikZ, tạo theo ma trận, tạo tương tự, OCR/import và sửa format."),
        ("✅", "Guard test cho prompt library",
            "Catalog prompt và UI Copy/Xem prompt được kiểm thử để không mất lại luồng tạo câu hỏi từ ChatBotAI khi nâng cấp tiếp."),
    ],
    "5.1.52-alpha": [
        ("🖱️", "Cuộn chuột mượt hơn",
            "Thay cơ chế wheel cũ bằng router toàn cục idempotent, tự tìm vùng scroll dưới con trỏ thay vì swap bindtags theo từng frame."),
        ("⚡", "Gom nhiều nấc wheel trong một nhịp UI",
            "MouseWheel và Treeview scroll được coalesce qua `after_idle`, giảm số lần `yview_scroll` khi lăn nhanh hoặc dùng touchpad."),
        ("🧩", "Ít xung đột với widget con",
            "Router bỏ qua Text/Listbox/Treeview có scroll riêng và giữ Ctrl+Wheel cho zoom PDF/LaTeX, tránh trang chính cuộn theo sai ngữ cảnh."),
    ],
    "5.1.51-alpha": [
        ("🧾", "Xem từng câu mượt hơn khi đề dài",
            "Panel card câu hỏi trong màn Tạo đề render theo lô nhỏ, nên đề nhiều câu không còn dựng toàn bộ card trong một nhịp UI."),
        ("⚙️", "Import và tạo ma trận bớt nghẽn",
            "Import Wizard, dialog Tạo ma trận AI và dialog Đề tương tự AI dùng `UiThrottle` cho progress thay vì gửi cập nhật liên tục vào event loop."),
        ("✅", "Guard hiệu năng UI rộng hơn",
            "Bổ sung test giữ nhịp render card, progress import/ma trận/variant và chống quay lại kiểu callback dày gây giật."),
    ],
    "5.1.50-alpha": [
        ("⚡", "Giao diện mượt hơn khi chạy tác vụ dài",
            "Thêm `v5.ui_perf.UiThrottle` để gom cập nhật progress theo nhịp khung hình, tránh bắn quá nhiều callback `after(0)` vào Tkinter."),
        ("🧪", "QC và tạo đề ít giật hơn",
            "Progress sinh đề, tạo lại câu lỗi, upload ảnh LMS và bảng QC được throttle/batch; tag màu QC không còn cấu hình lại trên từng dòng."),
        ("✨", "Toast và spinner nhẹ hơn",
            "Giảm nhịp animation gây tốn event loop, bỏ các lần ép `update_idletasks()` trong toast để hạn chế khựng khi có nhiều thông báo."),
    ],
    "5.1.49-alpha": [
        ("🎨", "Bảng màu V5 rõ và ít trùng hơn",
            "Thêm `v5.ui_theme` để gom màu nền, viền, chữ phụ, cảnh báo và màu Guide; Home/App shell bắt đầu dùng token chung thay vì màu rời rạc."),
        ("📖", "Hướng dẫn dễ đọc hơn",
            "Tab Hướng dẫn chuyển sang layout 2 cột cố định, có ô tìm mục lục, banner rõ nét và vùng Bắt đầu nhanh cho mỗi mục."),
        ("🧭", "Sửa lệch layout Guide",
            "Các dòng hướng dẫn dùng grid theo cột số/bullet và text, wrap thống nhất, bỏ màu gray mờ gây khó đọc."),
    ],
    "5.1.48-alpha": [
        ("✏️", "Sửa đề nhanh hơn trong màn Kết quả",
            "Màn Tạo đề có thanh Sửa nhanh: nhập số câu, đi tới, sửa câu đang chọn, nhân bản để sửa hoặc chèn câu trống."),
        ("📄", "Nhân bản câu sạch metadata cũ",
            "Câu được nhân bản nhận question_id mới và xoá trạng thái lỗi/QC cũ, tránh xuất hoặc autosave nhầm review của câu gốc."),
        ("➕", "Soạn thủ công không cần gọi AI",
            "Có thể chèn câu trống vào đề đang mở rồi mở editor ngay, phù hợp khi cần bổ sung/sửa đề sau khi sinh bằng AI."),
    ],
    "5.1.47-alpha": [
        ("✅", "Áp dụng kết quả QC vào đề hiện tại",
            "Tab Chất lượng có nút Áp dụng để gắn metadata `_review` từ QC vào đúng câu trong ExamData đang mở."),
        ("🔗", "Đồng bộ workspace",
            "QCView nhận callback cập nhật đề từ app shell, nên Tracking, autosave, export và history thấy metadata QC mới."),
        ("🧪", "Guard test theo question_id",
            "Bổ sung test áp dụng `_review` theo `question_id`, kèm kiểm tra app shell truyền callback cho QC."),
    ],
    "5.1.46-alpha": [
        ("📥", "Báo cáo QC trong V5",
            "Tab Chất lượng có nút Báo cáo để xuất kết quả QC ra Excel hoặc CSV, không cần quay về UI V4."),
        ("📊", "Có sheet/tệp tổng hợp",
            "Báo cáo gồm loại câu, mức độ, điểm, trạng thái PASS/REVIEW, vấn đề/gợi ý, chủ đề và nội dung rút gọn."),
        ("✅", "Guard test cho report",
            "Bổ sung test source wiring và test CSV thật để đảm bảo báo cáo QC đọc được."),
    ],
    "5.1.45-alpha": [
        ("☑", "Toggle kèm đáp án/lời giải như V4",
            "Màn Kết quả có checkbox nhanh Kèm ĐA/LG, dùng cùng cấu hình xuất Word với dialog Cài đặt xuất."),
        ("🔁", "Đồng bộ mọi đường xuất",
            "Xuất Word thủ công, auto-export và trộn mã đề đều đọc trạng thái mới qua `_include_solutions_on_export()`."),
        ("✅", "Guard test cho quick toggle",
            "Bổ sung kiểm tra checkbox nhanh và setter cấu hình để không mất thao tác quen thuộc của V4."),
    ],
    "5.1.44-alpha": [
        ("🧮", "Kiểm tra điểm ngay tại Kết quả",
            "Màn Kết quả có nút Kiểm tra điểm, tự đồng bộ đề hiện tại và ưu tiên điểm từ row snapshot để đúng với ma trận tuỳ chỉnh."),
        ("📋", "Báo cáo lỗi câu sinh hỏng",
            "Có thể xuất TXT danh sách câu `_error`, kèm loại, mức độ, chủ đề, nội dung rút gọn và thông báo lỗi để sửa nhanh."),
        ("✅", "Guard test cho hành động Result",
            "Bổ sung kiểm tra score/error report wiring để tiếp tục chuyển đổi V4 mà không kéo lại module UI cũ."),
    ],
    "5.1.43-alpha": [
        ("✅", "QC trực tiếp đề hiện tại",
            "Màn Kết quả có nút QC đề hiện tại để chuyển sang tab Chất lượng với đúng đề đang mở, không cần load lại từ NHCH."),
        ("📄", "Tab QC nhận workspace exam",
            "QCView có nút Load đề hiện tại, tự nhận ExamData từ workspace V5 và reset bảng/thống kê trước khi chạy pipeline."),
        ("🧪", "Guard test cho luồng Result → QC",
            "Bổ sung kiểm tra app shell truyền current_exam cho QC và Exam Create điều hướng sang QC sau khi đồng bộ đề."),
    ],
    "5.1.42-alpha": [
        ("🔁", "Tạo lại toàn bộ câu lỗi",
            "Kết quả Tạo đề có nút Tạo lại lỗi, tự tìm các câu _error và sinh lại tuần tự bằng AI từ row ma trận gốc."),
        ("📌", "Chỉ bật khi thật sự cần",
            "Nút Tạo lại lỗi tự hiển thị số câu lỗi, tắt khi đề không còn lỗi và đồng bộ lại preview/export/LMS/autosave sau batch."),
        ("✅", "Guard test cho batch retry",
            "Bổ sung kiểm tra wiring batch retry, tiến trình và đồng bộ ExamData để không mất thao tác sửa chữa cấp đề."),
    ],
    "5.1.41-alpha": [
        ("🔄", "Tạo lại từng câu từ card kết quả",
            "Card Tạo đề có nút Tạo lại để sinh lại đúng một câu bằng AI từ row ma trận gốc, giống thao tác nhanh của V4."),
        ("🧷", "Giữ đồng bộ đề khi thay câu",
            "Câu mới thay vào danh sách hiện tại, giữ question_id cũ nếu có và cập nhật preview/export/LMS/autosave."),
        ("✅", "Guard test cho regenerate card",
            "Bổ sung kiểm tra wiring nút Tạo lại, row snapshot và generate_one để không mất chức năng này khi tiếp tục nâng cấp."),
    ],
    "5.1.40-alpha": [
        ("👁", "Xem LaTeX từng câu ngay trên card",
            "Card kết quả trong Tạo đề có nút LaTeX để render riêng từng câu, giúp xem công thức toán như bản V4 trước khi xuất Word/LMS."),
        ("🖼", "Copy/lưu ảnh preview không phụ thuộc UI cũ",
            "Dialog LaTeX Preview của V5 dùng service PDF chung, có Copy ảnh và Lưu PNG, không gọi lại module giao diện cũ."),
        ("✅", "Guard test cho LaTeX preview",
            "Bổ sung kiểm tra chuyển Question sang LaTeX, render qua PDF service và wiring nút preview trên card."),
    ],
    "5.1.39-alpha": [
        ("↕", "Đổi thứ tự câu ngay trên card",
            "Card kết quả trong Tạo đề có nút lên/xuống như V4 và đồng bộ lại thứ tự cho export, LMS, autosave."),
        ("✕", "Xoá câu khỏi đề đang mở",
            "Có thể xoá một câu trực tiếp từ card xem chi tiết; thao tác chỉ ảnh hưởng đề hiện tại, không xoá dữ liệu NHCH."),
        ("✅", "Guard test cho thao tác card",
            "Bổ sung kiểm tra wiring card move/delete để không mất các thao tác kết quả quan trọng khi tiếp tục nâng cấp V5."),
    ],
    "5.1.38-alpha": [
        ("👁", "Xem từng câu sau khi tạo đề",
            "Kết quả trong Tạo đề hiển thị card đầy đủ cho từng câu: nội dung, đáp án, lời giải và ảnh, đồng thời mở sửa trực tiếp."),
        ("🖼", "TikZ sang PNG ngay trong V5",
            "Nút TikZ → PNG quét các hình trong đề, render bằng pipeline độc lập UI V4 và cập nhật ảnh lên card/export Word."),
        ("✅", "Guard test cho preview và TikZ",
            "Bổ sung kiểm tra card và pipeline gắn PNG để không tái thiếu chức năng parity."),
    ],
    "5.1.37-alpha": [
        ("👤", "Thông tin người dùng giống V4 hơn",
            "Setup > License nay có hồ sơ người dùng, mã máy copy được, nguồn license, liên hệ hỗ trợ và copy gói thông tin gửi admin."),
        ("⏳", "Đếm ngược hạn dùng",
            "Ngày hết hạn được format rõ ràng kèm trạng thái còn hạn, sắp hết hạn, hết hạn hôm nay hoặc đã hết hạn."),
        ("🎁", "Danh sách quyền theo gói",
            "V5 hiển thị toàn bộ tính năng bật/tắt theo tier và admin override bằng helper thuần để dễ kiểm thử."),
    ],
    "5.1.36-alpha": [
        ("💾", "Nút lưu hình luôn hiển thị",
            "Dialog Lưu hình vào kho trong TikZ có footer cố định, kích thước tối thiểu lớn hơn và không còn bị cắt nút ở Windows scaling cao."),
        ("⌨️", "Phím tắt thao tác nhanh",
            "Có thể bấm Ctrl+Enter để lưu hình và Esc để đóng dialog khi đang nhập metadata."),
        ("✅", "Guard test cho Figure Bank",
            "Bổ sung kiểm tra tự động để V4/V5 không tái xuất hiện lỗi dialog lưu hình thiếu nút bấm."),
    ],
    "5.1.35-alpha": [
        ("⚙️", "Cài đặt xuất Word giống V4 hơn",
            "Màn Tạo đề có nút 'Cài đặt xuất' để chọn Text/MathType, bật tắt kèm đáp án-lời giải, "
            "tự mở file sau khi xuất và tự xuất sau khi sinh đề."),
        ("📄", "Xuất Word đọc đúng tuỳ chọn",
            "Xuất thủ công, lưu bản sao và auto-export không còn cố định kèm lời giải; tất cả đọc chung "
            "cấu hình đang lưu trong app_settings."),
        ("🏫", "Header và mặc định dùng chung",
            "Cài đặt xuất cũng cập nhật trường/GV cho đề hiện tại và lưu làm mặc định cho các đề sau."),
    ],
    "5.1.34-alpha": [
        ("✏️", "Sửa thông tin đề ngay trong Tạo đề",
            "Thêm nút 'Thông tin đề' để chỉnh tiêu đề, môn, lớp, kỳ, năm học, thời gian, "
            "trường và giáo viên trước khi xuất Word."),
        ("🏫", "Header Word giữ đúng trường/GV",
            "ExamData, autosave và lịch sử đề nay lưu lại school/teacher; Word export đọc trực tiếp "
            "metadata đang mở thay vì rơi về header mặc định."),
        ("💾", "Mặc định trường/GV cho các đề sau",
            "Dialog có tuỳ chọn lưu trường/GV vào app_settings để các đề mới tự nhận thông tin header."),
    ],
    "5.1.33-alpha": [
        ("📥", "Nạp đề có sẵn vào Tạo đề",
            "Màn Tạo đề có nút 'Nạp đề file' để đọc DOCX, PDF, TeX, TXT hoặc "
            "HTML rồi đưa câu hỏi thẳng vào preview."),
        ("🧩", "Parser 3 tầng của V4",
            "V5 dùng core.exam_file_loader: khung ===CAU===, natural parser, "
            "LaTeX parser; nếu chỉ đọc được text thì hỏi người dùng dùng AI fallback."),
        ("🤖", "AI fallback thuần V5",
            "Khi cần chuẩn hoá bằng AI, V5 dùng prompt/parse từ v5.convert_pipeline, "
            "không còn phụ thuộc ui.tab_convert."),
    ],
    "5.1.32-alpha": [
        ("🔀", "Xuất nhiều mã đề giống V4 hơn",
            "Nút Trộn mã trong Tạo đề nay dùng lại export_multi_code: xuất các "
            "mã A-F, file Word và bảng đáp án riêng thay vì tự shuffle đơn giản."),
        ("🎛️", "Tuỳ chọn trộn đầy đủ",
            "Dialog có chọn số mã, trộn câu trong từng phần, trộn đáp án TN, "
            "kèm lời giải trong file Word và progress khi xuất."),
        ("🔢", "Variant ngay khi xuất mã đề",
            "Có thể chọn không thay số, thay số Python/SymPy hoặc AI provider; "
            "vẫn có copy/xem-sửa prompt thủ công cho chatbot ngoài app."),
    ],
    "5.1.31-alpha": [
        ("🧬", "Đề tương tự trong V5",
            "Màn Tạo đề có nút 'Đề tương tự' để tạo bản thay số từ đề hiện tại "
            "rồi nạp lại thẳng vào preview/export/push/NHCH."),
        ("🧮", "Python/SymPy hoặc AI provider",
            "Có thể sinh nhanh bằng service Python/SymPy khi nhận diện được dạng "
            "toán, hoặc gọi AI provider đã cấu hình để xử lý đề rộng hơn."),
        ("📋", "Prompt thủ công",
            "Dialog mới cho copy hoặc xem/sửa prompt V4 để upload Word gốc sang "
            "ChatGPT/Claude/Gemini ngoài app, không phụ thuộc tab_result cũ."),
    ],
    "5.1.30-alpha": [
        ("📊", "Dashboard V4 trong Tracking",
            "Tracking có tab 'Tổng quan' mới: thống kê NHCH, đề đang mở, "
            "phân bổ chất lượng câu hỏi, so sánh mô hình AI và câu nghi ngờ sai."),
        ("🧠", "Phân tích phản hồi",
            "Nút 'Phân tích phản hồi' gọi lại adaptive_prompt để rút mẫu lỗi/mẫu tốt "
            "từ feedback và đưa vào prompt sinh đề các lần sau."),
        ("📄", "Xuất báo cáo Dashboard",
            "Có thể xuất báo cáo text từ Dashboard V5, không phụ thuộc tab_dashboard "
            "Tkinter cũ."),
    ],
    "5.1.29-alpha": [
        ("📊", "AI Usage chi tiết trong V5",
            "Tracking có nút 'Chi tiết AI' mở dialog CTk-native với KPI theo "
            "phạm vi, provider/model breakdown, quota warning và 50 request gần nhất."),
        ("📤", "Xuất và bảo trì log AI",
            "Dialog mới hỗ trợ làm mới, xuất CSV, mở thư mục log và xoá log như "
            "tab AI Usage của V4, không cần quay về giao diện cũ."),
        ("🧮", "Đọc đúng cả log ký tự và token",
            "V5 chuẩn hoá log prompt_chars/response_chars của service hiện tại "
            "và tokens_in/tokens_out nếu có; biểu đồ/cost không còn rơi về 0 giả."),
    ],
    "5.1.28-alpha": [
        ("📐", "Shape Builder trong V5",
            "Tab TikZ có nút 'Tạo hình' để dựng nhanh 39 loại hình từ thông số: "
            "hình phẳng, hình không gian, đồ thị, biểu đồ, BBT và bảng xét dấu."),
        ("🧮", "Sinh TikZ không cần AI",
            "Người dùng nhập hệ số, kích thước, nhãn hoặc nghiệm; app sinh code "
            "TikZ/tkz-tab ngay để chèn vào editor và render."),
        ("🧩", "Guardrail độc lập V4",
            "Shape Builder mới dùng module V5 riêng, có test phủ toàn bộ loại hình "
            "đăng ký và không phụ thuộc module Shape Builder Tkinter cũ."),
    ],
    "5.1.27-alpha": [
        ("🗂", "Kho NHCH hình vẽ trong V5",
            "Tab TikZ có nút 'Kho hình' để tìm, xem code, copy, sửa metadata, "
            "xoá và nạp lại các hình TikZ đã lưu."),
        ("💾", "Lưu hình TikZ vào kho",
            "Code hiện tại có thể lưu thẳng vào Figure Bank kèm tên, mô tả, "
            "tags và ảnh PNG đã render nếu có."),
        ("🧩", "Tách khỏi UI V4",
            "Dialog Figure Bank mới dùng CustomTkinter và service figure_bank, "
            "không còn gọi dialog Tkinter cũ trong ui.tab_tikz."),
    ],
    "5.1.26-alpha": [
        ("📋", "Phân tích đề thi thành ma trận",
            "Màn Tạo đề có nút 'Phân tích đề' để đọc DOCX/PDF/TXT, trích câu hỏi "
            "và nạp thẳng thành ma trận đặc tả chi tiết từng câu."),
        ("🤖", "AI tinh chỉnh ma trận",
            "Sau khi parser local tạo ma trận nháp, có thể gọi provider đã cấu hình "
            "để chuẩn hóa chủ đề, mức độ, loại câu, yêu cầu cần đạt và điểm."),
        ("📤", "Xuất ngay từ dialog phân tích",
            "Ma trận phân tích từ đề có thể xuất Word chuẩn BGD hoặc CSV trước khi "
            "đưa vào luồng sinh đề."),
    ],
    "5.1.25-alpha": [
        ("📚", "Thư viện mẫu ma trận trong V5",
            "Màn Tạo đề nay mở được các mẫu ma trận đóng gói, lọc theo lớp/từ khóa "
            "và nạp vào bảng chi tiết trước khi sinh đề."),
        ("📥", "Xuất ma trận đặc tả",
            "Ma trận đang chỉnh có thể xuất ngay sang Word chuẩn BGD hoặc CSV mà "
            "không cần quay về tab V4."),
        ("⚡", "Auto-export sau khi sinh đề",
            "Sau khi AI sinh đề, V5 tự xuất Word theo cài đặt, cho mở thư mục, "
            "lưu bản sao, đổi thư mục, tắt tự xuất và lưu câu hợp lệ vào NHCH."),
    ],
    "5.1.24-alpha": [
        ("🪪", "Quyền tính năng đồng bộ với V4",
            "TopBar hiện gói license thực tế thay vì luôn ghi PREMIUM. "
            "NHCH, QC, Convert, Smart Prompt, Cloud và trộn mã đề tuân theo "
            "feature catalog/override hiện có."),
        ("⌨", "Phím tắt đủ 8 màn hình",
            "Ctrl+5 mở Convert và Ctrl+8 mở Hướng dẫn; trợ giúp trong app "
            "và tài liệu đã đồng bộ với điều hướng thực tế."),
    ],
    "5.1.7-alpha": [
        ("↔", "Bảng ma trận cuộn ngang",
            "Chế độ 'Chi tiết từng câu' giờ có thanh cuộn ngang — cột 'Yêu "
            "cầu cần đạt' + 'Điểm' không còn bị che ngoài mép phải."),
    ],
    "5.1.6-alpha": [
        ("📋", "Ma trận đặc tả chi tiết từng câu",
            "Toggle 'Gộp chủ đề / Chi tiết từng câu' trong Tạo đề. Chế độ "
            "chi tiết hiện yêu cầu cần đạt mỗi câu (giữ từ file tải lên)."),
        ("✏️", "Sửa từng dòng ma trận (double-click)",
            "Double-click 1 dòng → sửa: gộp (chủ đề + số câu mỗi mức) hoặc "
            "chi tiết (chủ đề/mức/loại/yêu cầu/điểm). 2 view tự đồng bộ."),
        ("🎯", "Sinh đề giữ yêu cầu gốc",
            "Khi có ma trận chi tiết, AI sinh đề dùng đúng yêu cầu cần đạt "
            "từng câu (chất lượng sát đặc tả hơn)."),
    ],
    "5.1.5-alpha": [
        ("🎨", "Bảng (Treeview) đẹp hơn",
            "Tất cả bảng (ma trận, kết quả, NHCH, QC, thống kê, import) giờ "
            "có header xanh đậm, hàng cao 30px, sọc xen kẽ (zebra), hàng "
            "chọn màu accent, tự đổi màu theo Light/Dark."),
    ],
    "5.1.4-alpha": [
        ("📜", "Tạo đề cuộn được — xem hết nội dung",
            "View Tạo đề giờ cuộn dọc: ma trận nhiều dòng + section ④ Kết "
            "quả (sau khi sinh đề) đều xem được. Bảng ma trận co giãn cột "
            "chủ đề, không cắt cột Điểm/câu."),
        ("🔔", "Bảng thông báo không che mãi",
            "NotificationCenter (🔔) giờ đóng bằng Escape / click ngoài / "
            "tự đóng sau 12s — không che nội dung."),
    ],
    "5.1.3-alpha": [
        ("📂", "Tải file ma trận (port từ V4)",
            "Nút '📂 Tải file ma trận' trong Tạo đề — chọn Word/Excel/PDF/"
            "ảnh → parse rule-based, fallback AI nhận diện → nạp tự động vào "
            "bảng ma trận (parse_matrix_file + recognize_matrix)."),
        ("🩹", "Fix QuickSwitcher crash (Ctrl+T)",
            "'transparency is not allowed in tuple color' khi mở Ctrl+T đã "
            "sửa (dùng 'transparent' string thay vì tuple)."),
    ],
    "5.1.2-alpha": [
        ("🩹", "Fix 'Tạo đề' lỗi MatrixRow (nb)",
            "Lỗi 'MatrixRow got unexpected keyword nb' khi bấm Tạo đề đã sửa "
            "— ma trận gộp {NB,TH,VD} giờ expand đúng thành từng câu cho "
            "generate_all. Smart Prompt cũng đã sửa."),
        ("🩹", "Fix mở Cấu hình lỗi font (EXE)",
            "'Too early to use font: no default root window' khi mở Cấu hình/"
            "NHCH trong EXE đã sửa — ép default root window."),
        ("🩹", "Fix xoá dòng ma trận lỗi",
            "'invalid literal for int: Tích phân' khi xoá dòng đã sửa "
            "(dùng index của bảng thay vì parse cột chủ đề)."),
        ("🛟", "Báo lỗi rõ thay vì crash",
            "View lỗi giờ hiện màn hình '⚠ Không mở được' + ghi "
            "v5_view_errors.log + nút Thử lại, thay vì crash/màn hình mơ hồ."),
    ],
    "5.1.1-alpha": [
        ("🧭", "Hướng dẫn rõ ràng từng bước (UX)",
            "Tạo đề có banner quy trình ①②③④ + chú thích NB/TH/VD + chọn "
            "Lớp. NHCH + QC có dòng hướng dẫn cách dùng. Bớt 'mơ hồ'."),
        ("✏️", "QC: double-click câu lỗi → sửa ngay",
            "Trong QC, double-click 1 câu mở dialog sửa kèm gợi ý QC + nút "
            "AI fix → lưu lại NHCH. Trước đây chưa nối."),
        ("🎚", "Chọn Lớp khi tạo đề",
            "Không còn cố định lớp 12 — chọn 6-12 cho generate/sửa/push."),
    ],
    "5.1.0-alpha": [
        ("🏆", "Feature-complete — v5 độc lập 100%",
            "Cột mốc: 17/17 tính năng thuần CTk, không còn reuse v4. Đã "
            "verify frozen EXE 6/6 self-diagnostics qua nhiều vòng build."),
        ("🆔", "ID nhất quán khi import/Smart Prompt",
            "Câu từ Import wizard + Smart Prompt tự gán structured ID "
            "(12D1T1-0001) nếu chưa có — đồng bộ toàn hệ."),
    ],
    "5.0.9-alpha": [
        ("⛔", "Dừng Tạo đề giữa chừng",
            "Nút '⛔ Dừng' khi đang sinh đề — AI thoát sớm sau câu hiện tại "
            "(generate_all cancel_event). Khớp với QC + Import đã có Dừng."),
    ],
    "5.0.8-alpha": [
        ("⚡", "NHCH tìm kiếm mượt (debounce)",
            "Gõ từ khoá không còn lag với ngân hàng lớn — chờ 250ms sau "
            "phím cuối mới lọc."),
        ("🚀", "Giới hạn render 500 dòng",
            "NHCH nhiều nghìn câu chỉ render 500 dòng đầu (báo số khớp/tổng) "
            "→ không freeze UI. Gõ từ khoá để lọc hẹp."),
    ],
    "5.0.7-alpha": [
        ("🎉", "v5 độc lập 100% — không còn reuse v4",
            "Tính năng cuối (TikZ auto-heal/KB) đã port sang CTk. Toàn bộ "
            "17/17 workflow hằng ngày giờ chạy thuần v5."),
        ("🔧", "TikZ Auto-fix + Auto-heal",
            "QC tab: nút '🔧 Auto-fix' sửa lỗi LaTeX thường gặp (rule-based). "
            "Render fail → hỏi dùng AI sửa tự động (auto-heal 2 lớp)."),
        ("📚", "Kho mẫu TikZ (88 mẫu)",
            "Nút '📚 Kho mẫu' — duyệt/tìm 88 mẫu hình (BBT, tam giác, "
            "parabol…) → chèn thẳng vào editor."),
    ],
    "5.0.6-alpha": [
        ("📥", "Import wizard thuần CTk (Alpha 11)",
            "Import PDF/Word/Ảnh → NHCH viết lại bằng CustomTkinter — chọn "
            "file, AI Vision OCR, lọc loại câu, tự giải, preview, lưu local + "
            "push Cloud. Không còn dùng dialog Tkinter v4."),
        ("☁", "Tải NHCH từ Cloud",
            "NHCH → '⬇ Cloud' giờ tải thật câu hỏi từ Supabase về local "
            "(thay vì báo 'sắp ra'). Tối đa 200 câu/lần."),
    ],
    "5.0.5-alpha": [
        ("🩺", "Chẩn đoán hệ thống",
            "Preferences (Ctrl+,) → nút '🩺 Chẩn đoán' kiểm tra 6 mục: "
            "import module, LaTeX engine, xuất Word, TikZ render, core/NHCH, "
            "API key. Tự chẩn lỗi cài đặt không cần CLI."),
        ("🚑", "Fix EXE crash khi Xuất Word/Import PDF (quan trọng)",
            "Module docx/pdfplumber cần pkg_resources→jaraco; build trước "
            "thiếu jaraco → import crash 'No module named jaraco' trong EXE. "
            "Đã bundle jaraco + more_itertools. Verified frozen EXE 6/6 PASS."),
        ("🛡", "An toàn print() trong EXE windowed",
            "EXE console=False có sys.stdout=None → mọi print() có thể crash. "
            "Thêm _NullWriter guard."),
    ],
    "5.0.4-alpha": [
        ("🏁", "Beta 1 polish — Empty states",
            "NHCH trống hiện gợi ý Import/Tạo đề; lọc không khớp báo rõ. "
            "Trang chủ có banner '⚠ Chưa cấu hình AI' bấm thẳng tới Cấu hình."),
        ("🧭", "Hướng dẫn khi thiếu API key",
            "Bấm 'Tạo đề' chưa có key → hỏi 'Mở Cấu hình ngay?' nhảy thẳng "
            "tab Setup thay vì chỉ báo lỗi."),
        ("🛡", "Thêm guard race condition",
            "Tracking/statusbar không còn nguy cơ crash khi chuyển view giữa "
            "lúc load data nền."),
    ],
    "5.0.3-alpha": [
        ("✏️", "NHCH sửa câu thuần CTk (Alpha 10)",
            "Dialog 'Sửa câu' viết lại hoàn toàn bằng CustomTkinter — nhất "
            "quán giao diện v5. Hỗ trợ đủ 4 loại (TN/DS/TLN/TL), live ID, "
            "multi-image đề+lời giải, nút 🤖 AI sửa theo gợi ý QC. Không còn "
            "phụ thuộc dialog Tkinter v4."),
        ("🆔", "Live structured ID khi sửa",
            "ID câu (vd 12D1T1-0001) tự cập nhật real-time khi đổi loại/mức/"
            "chủ đề. Tự gán ID nếu câu chưa có khi lưu."),
        ("🖼", "TikZ render preview trong v5",
            "Nút '🖼 Render preview' trong QC → biên dịch LaTeX → hiển thị "
            "hình PNG ngay trong app (không cần mở v4)."),
        ("🔧", "Fix mất dữ liệu khi sửa câu DS/ảnh",
            "Convert NHCH→câu giờ map đủ items/answers/ảnh/item_solutions. "
            "Sửa câu Đúng-Sai không còn mất 4 ý + đáp án."),
        ("✏️", "Sửa câu generated trước khi xuất",
            "Double-click 1 câu trong preview Tạo đề → mở dialog sửa → lưu "
            "cập nhật ngay vào đề."),
        ("📦", "Fix EXE thiếu module (quan trọng)",
            "Build trước EXCLUDE nhầm docx/PyMuPDF/pdfplumber → Xuất Word, "
            "TikZ render, Import PDF bị lỗi trong EXE. Đã bundle đầy đủ."),
    ],
    "5.0.2-alpha": [
        ("🐛", "Sửa crash dialog khi chuyển view",
            "Race condition giữa background thread + widget destroy đã được "
            "lọc tại crash handler. App vẫn ghi log nhưng không popup dialog "
            "cho các lỗi benign (TclError invalid command name)."),
        ("🥧", "Biểu đồ theo Provider",
            "Tab '🥧 Theo Provider' trong Tracking — pie chart calls + bar "
            "chart cost theo Google/Anthropic/OpenAI/DeepSeek (7d/30d/all)."),
        ("📦", "Backup/Restore dữ liệu",
            "Trong Preferences (Ctrl+,) → 'Backup dữ liệu (ZIP)' / 'Restore'. "
            "Pack NHCH SQLite + settings + history. Optionally include LMS "
            "token. Restore tự tạo safety copy."),
        ("🛑", "Toast queue limit",
            "Tối đa 5 toast hiển thị cùng lúc — toast cũ tự dismiss để "
            "tránh ngập màn hình."),
        ("🔧", "Bug fix Setup view",
            "_update_license_ui giờ guard winfo_exists() trước khi configure "
            "label — không crash khi user chuyển view giữa lúc check license."),
        ("📊", "Splash progress thật",
            "Loading bar bây giờ hiển thị % cụ thể (10% → 30% → 55% → "
            "75% → 100%) thay vì indeterminate slide."),
        ("🔕", "Tắt auto-popup What's New",
            "Checkbox 'Đừng hiện tự động nữa' — vẫn xem được qua Ctrl+T → "
            "'whats new'."),
        ("🔍", "Search button trong TopBar",
            "Nút '🔍 Tìm kiếm (Ctrl+T)' bên trái để dễ thấy quick switcher."),
        ("👆", "Click toast/splash để skip",
            "Click toast → dismiss ngay. Click splash → bỏ qua loading."),
        ("🔴", "Crash count badge",
            "🔔 statusbar có badge đỏ hiển thị số crash chưa xem. Mở "
            "notification center → mark as read."),
        ("💬", "Smart Prompt (mới!)",
            "Tạo đề/câu hỏi từ mô tả tiếng Việt tự nhiên. Ctrl+Shift+P hoặc "
            "nút 💬 trong Tạo đề. VD: 'Đề 90 phút lớp 12 tích phân 18 TN 4 ĐS' "
            "→ ma trận tự động + follow-up chat-style điều chỉnh."),
        ("🩹", "Fix 'Tạo đề bằng AI' crash",
            "generate_all() trước đây bị gọi thiếu tham số semester/year + "
            "sai kwarg progress_callback → nút Tạo đề bị lỗi. Đã sửa cả "
            "Exam Create + Smart Prompt."),
        ("🚑", "Audit & fix core feature broken",
            "Phát hiện hàng loạt hàm gọi sai tên: QC (review_question→"
            "run_qc_pipeline), Xuất Word (export_exam_word→export_to_word), "
            "Nạp NHCH (list_all_questions→search_questions), Thống kê "
            "(list_exam_history→list_recent_sessions). Toàn bộ luồng chính "
            "(tạo đề/QC/xuất/ngân hàng) giờ hoạt động đúng."),
    ],
    "5.0.1-alpha": [
        ("🛡", "Crash reporter mới",
            "Tự ghi mọi lỗi vào ~/.exam_generator/crashes.jsonl + privacy "
            "scrub. Mở qua Ctrl+T → 'crash log'."),
        ("🔄", "Tự kiểm tra update",
            "App ping GitHub Releases 5s sau khi mở; toast 'Có phiên bản "
            "mới' kèm nút Tải về. Tắt trong Preferences."),
        ("⚙", "Preferences dialog (Ctrl+,)",
            "Popup quick toggle theme/accent/check_updates + maintenance: "
            "xem crash log, xoá session, mở thư mục dữ liệu."),
        ("ℹ", "About dialog",
            "Xem version, license, link Website/Docs/Issues. Mở qua "
            "Ctrl+T → 'about'."),
        ("📄", "Recent files dropdown",
            "TopBar có nút '📄 Gần đây ▾' — list 7 file vừa import, "
            "click mở Import Wizard."),
        ("💾", "Autosave indicator",
            "Statusbar hiện 'Lưu Xs trước' để biết session autosave còn "
            "hoạt động. Đã fix bug statusbar không tự refresh."),
        ("👋", "Welcome toast",
            "Khi mở lại app, toast hiển thị 'Lần mở cuối: 3h trước'."),
    ],
    "5.0.0-alpha": [
        ("🎨", "CustomTkinter rewrite",
            "Toàn bộ UI v5 viết lại bằng CustomTkinter — modern, dark mode, "
            "responsive."),
        ("⚡", "Lazy-load views",
            "Views chỉ load khi user click → startup nhanh hơn ~2s."),
        ("🔍", "Quick switcher (Ctrl+T)",
            "Command palette kiểu VSCode — fuzzy search 9 view + action."),
        ("💾", "Session autosave",
            "Tự save exam_data mỗi 60s + restore prompt khi mở app."),
        ("📊", "Stats dashboard",
            "Theo dõi & Thống kê với chart matplotlib + 4 stat cards."),
    ],
}


class WhatsNewDialog(ctk.CTkToplevel):
    """Modal hiển thị changelog của 1 version cụ thể (hoặc latest)."""

    WIDTH = 580
    HEIGHT = 560

    def __init__(self, parent, version: str | None = None):
        super().__init__(parent)
        self.title("✨ Có gì mới — MEA v5")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        try: self.attributes("-topmost", True)
        except: pass

        if version is None:
            version = next(iter(CHANGELOG), "")
        changes = CHANGELOG.get(version, [])

        # Header
        hdr = ctk.CTkFrame(self, fg_color=("#DBEAFE", "#1E3A8A"),
                             corner_radius=0, height=80)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="✨  Có gì mới",
                      font=("Segoe UI", 22, "bold"),
                      text_color=("#1E40AF", "#BFDBFE")
                      ).pack(side="left", padx=20, pady=4)
        ctk.CTkLabel(hdr, text=f"v{version}",
                      font=("Segoe UI", 14, "bold"),
                      text_color=("#1E40AF", "#BFDBFE")
                      ).pack(side="left", padx=4)

        # Body scrollable
        body = ctk.CTkScrollableFrame(self, fg_color=("#F9FAFB", "#0F172A"))
        body.pack(fill="both", expand=True, padx=12, pady=12)

        if not changes:
            ctk.CTkLabel(body,
                          text="(Chưa có ghi chú cho phiên bản này)",
                          text_color="gray").pack(pady=20)

        for emoji, title, desc in changes:
            card = ctk.CTkFrame(body, fg_color=("white", "#1E293B"),
                                  corner_radius=8,
                                  border_width=1,
                                  border_color=("#E5E7EB", "#334155"))
            card.pack(fill="x", padx=4, pady=4)
            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=12, pady=10)

            head = ctk.CTkFrame(inner, fg_color="transparent")
            head.pack(fill="x")
            ctk.CTkLabel(head, text=emoji,
                          font=("Segoe UI", 20)
                          ).pack(side="left", padx=(0, 8))
            ctk.CTkLabel(head, text=title,
                          font=("Segoe UI", 13, "bold"),
                          anchor="w"
                          ).pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(inner, text=desc,
                          font=("Segoe UI", 11),
                          text_color=("#374151", "#CBD5E1"),
                          anchor="w", justify="left", wraplength=480
                          ).pack(anchor="w", padx=(32, 0), pady=(2, 0))

        # Don't show again checkbox (n19)
        opt = ctk.CTkFrame(self, fg_color="transparent")
        opt.pack(fill="x", padx=12, pady=(0, 4))
        self._dont_show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opt, variable=self._dont_show_var,
                          text="Đừng hiện tự động nữa (vẫn xem qua Ctrl+T)",
                          font=("Segoe UI", 10),
                          command=self._toggle_show_whats_new
                          ).pack(anchor="w", padx=4)

        # Footer
        ftr = ctk.CTkFrame(self, fg_color="transparent")
        ftr.pack(fill="x", padx=12, pady=(0, 12))

        # Hiện danh sách version cũ
        old_vers = [v for v in CHANGELOG.keys() if v != version]
        if old_vers:
            ctk.CTkLabel(ftr, text="Phiên bản cũ:",
                          font=("Segoe UI", 10),
                          text_color="gray"
                          ).pack(side="left", padx=4)
            for v in old_vers[:3]:
                ctk.CTkButton(ftr, text=f"v{v}", width=90, height=24,
                                font=("Segoe UI", 9),
                                fg_color="transparent",
                                text_color=("#1F497D", "#60A5FA"),
                                hover_color=("#DBEAFE", "#1E3A8A"),
                                command=lambda vv=v: self._show_version(vv)
                                ).pack(side="left", padx=2)

        ctk.CTkButton(ftr, text="Đã hiểu",
                        width=120, command=self.destroy
                        ).pack(side="right", padx=4)

        # ESC to close
        self.bind("<Escape>", lambda e: self.destroy())
        try: self.grab_set()
        except: pass
        try: self.focus_force()
        except: pass

    def _show_version(self, v: str):
        """Đóng dialog hiện tại, mở dialog cho version v."""
        parent = self.master
        try: self.destroy()
        except: pass
        WhatsNewDialog(parent, version=v)

    def _toggle_show_whats_new(self):
        """User check "Đừng hiện nữa" → tắt auto-popup."""
        try:
            settings_store.set_value("show_whats_new",
                                       not self._dont_show_var.get())
        except Exception: pass


def show_if_new_version(app):
    """Auto-popup nếu seen_whats_new khác __version__.

    Tôn trọng setting show_whats_new (n19): nếu user tắt → bỏ qua.
    """
    try:
        from v5 import __version__
        s = settings_store.load()
        if not s.get("show_whats_new", True):
            return    # user đã tắt auto-popup
        seen = s.get("seen_whats_new", "")
        if seen == __version__:
            return    # đã xem rồi
        if __version__ not in CHANGELOG:
            return    # version này chưa có changelog
        # Schedule sau splash + welcome toast (~3s)
        def _do():
            try:
                WhatsNewDialog(app, version=__version__)
                settings_store.set_value("seen_whats_new", __version__)
            except Exception as e: print(f"whats_new fail: {e}")
        app.after(3000, _do)
    except Exception as e:
        print(f"check whats_new fail: {e}")
