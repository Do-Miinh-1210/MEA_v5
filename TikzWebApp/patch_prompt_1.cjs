const fs = require('fs');
let code = fs.readFileSync('components/AIAssistant.tsx', 'utf8');

const regex = /20-7\. Khoảng\/đoạn trên trục số: Khi biểu diễn khoảng, đoạn trên trục số, TUYỆT ĐỐI KHÔNG dùng cung tròn hay vẽ cung cong\. BẮT BUỘC sử dụng ký tự ngoặc có sẵn trên bàn phím: "\(", "\)", "\[", "\]"\./;

const replacement = `20-7. Khoảng/đoạn trên trục số: Khi biểu diễn khoảng, đoạn trên trục số, TUYỆT ĐỐI KHÔNG dùng cung tròn hay vẽ cung cong. BẮT BUỘC sử dụng ký tự ngoặc có sẵn trên bàn phím: "(", ")", "[", "]".
21-8. Bảo tồn nguyên trạng cấu trúc và nội dung: Khi vẽ lại hoặc tối ưu hình, ảnh, bảng biến thiên, đồ thị, PHẢI bảo tồn tuyệt đối hình gốc. Tuyệt đối KHÔNG ĐƯỢC THÊM, BỚT, hay thay đổi bất kỳ thành phần nào của hình gốc (đường nét, điểm, nhãn, dữ liệu, mũi tên, v.v.) TRỪ KHI có yêu cầu rõ ràng về việc thêm/bớt đó.`;

// Note: I will replace the raw text in the file.
// The raw text doesn't have "20-". Let's match the actual content.
