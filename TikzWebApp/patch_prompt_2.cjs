const fs = require('fs');
let code = fs.readFileSync('services/geminiService.ts', 'utf8');

const regex = /Bước 4: Tính toán ngầm \(tọa độ, góc, tỷ lệ\) trước khi xuất code để đảm bảo hình vẽ chuẩn, đẹp và tối ưu\./;

const replacement = `Bước 4: Tính toán ngầm (tọa độ, góc, tỷ lệ) trước khi xuất code để đảm bảo hình vẽ chuẩn, đẹp và tối ưu.
        Bước 5: BẢO TỒN NGUYÊN TRẠNG cấu trúc và nội dung: Khi vẽ hình, ảnh, bảng biến thiên, đồ thị từ dữ liệu gốc, PHẢI bảo tồn tuyệt đối hình gốc. Tuyệt đối KHÔNG ĐƯỢC THÊM, BỚT, hay thay đổi bất kỳ thành phần nào của hình gốc (đường nét, điểm, nhãn, dữ liệu, mũi tên, v.v.) TRỪ KHI tôi có yêu cầu rõ ràng về việc thêm/bớt.`;

code = code.replace(regex, replacement);
fs.writeFileSync('services/geminiService.ts', code);
