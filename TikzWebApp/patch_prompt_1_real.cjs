const fs = require('fs');
let code = fs.readFileSync('components/AIAssistant.tsx', 'utf8');

const regex = /7\. Khoảng\/đoạn trên trục số: Khi biểu diễn khoảng, đoạn trên trục số, TUYỆT ĐỐI KHÔNG dùng cung tròn hay vẽ cung cong\. BẮT BUỘC sử dụng ký tự ngoặc có sẵn trên bàn phím: "\(", "\)", "\[", "\]"\./;

const replacement = `7. Khoảng/đoạn trên trục số: Khi biểu diễn khoảng, đoạn trên trục số, TUYỆT ĐỐI KHÔNG dùng cung tròn hay vẽ cung cong. BẮT BUỘC sử dụng ký tự ngoặc có sẵn trên bàn phím: "(", ")", "[", "]".\n8. Bảo tồn nguyên trạng cấu trúc và nội dung: Khi vẽ lại hoặc tối ưu hình, ảnh, bảng biến thiên, đồ thị, PHẢI bảo tồn tuyệt đối hình gốc. Tuyệt đối KHÔNG ĐƯỢC THÊM, BỚT, hay thay đổi bất kỳ thành phần nào của hình gốc (đường nét, điểm, nhãn, dữ liệu, mũi tên, v.v.) TRỪ KHI tôi có yêu cầu rõ ràng về việc thêm/bớt đó.`;

code = code.replace(regex, replacement);
fs.writeFileSync('components/AIAssistant.tsx', code);
