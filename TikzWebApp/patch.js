const fs = require('fs');
let content = fs.readFileSync('services/geminiService.ts', 'utf8');

const newRule = `
7. BẮT BUỘC ĐỐI VỚI VẼ ĐỒ THỊ HÀM SỐ VÀ TIỆM CẬN:
   - Tất cả các lệnh vẽ đồ thị hàm số BẮT BUỘC phải được đặt ngay dưới dòng chú thích đúng chuẩn (viết hoa, có dấu gạch ngang):
     % --- ĐỒ THỊ HÀM SỐ ---
     \\draw[line width=0.6pt, smooth, samples=..., domain=xmin:xmax,
         % postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, above left] {$y=... $};}}, decorate}
     ] % lưu ý: dấu đóng ngoặc vuông phải hiển thị riêng một dòng
       plot (\\x, {f(\\x)});
   - Tất cả các lệnh vẽ tiệm cận BẮT BUỘC phải được đặt ngay dưới dòng chú thích đúng chuẩn:
     % --- TIỆM CẬN ---
     \\draw[dashed, line width=0.6pt, domain=xmin:xmax]
       plot (\\x, {g(\\x)});
   - Áp dụng cấu trúc này cho TẤT CẢ các lệnh vẽ hàm số và tiệm cận để hệ thống có thể nhận diện và điều khiển Ẩn/Hiện. Đảm bảo phía sau mỗi khối lệnh vẽ là một dòng trống (blank line).
`;

content = content.replace("12. XỬ LÝ HÌNH ẢNH:", newRule + "\n12. XỬ LÝ HÌNH ẢNH:");
if(!content.includes("7. BẮT BUỘC ĐỐI VỚI VẼ ĐỒ THỊ HÀM SỐ VÀ TIỆM CẬN")) {
    content = content.replace("7. NGUYÊN TẮC: NHÃN TRÊN ĐƯỜNG", newRule + "\n7. NGUYÊN TẮC: NHÃN TRÊN ĐƯỜNG");
}
if(!content.includes("7. BẮT BUỘC ĐỐI VỚI VẼ ĐỒ THỊ HÀM SỐ VÀ TIỆM CẬN")) {
    content = content.replace("8. QUY TẮC PHÂN MẢNH VÀ TÔ MÀU (SHADING)", newRule + "\n8. QUY TẮC PHÂN MẢNH VÀ TÔ MÀU (SHADING)");
}
fs.writeFileSync('services/geminiService.ts', content);
