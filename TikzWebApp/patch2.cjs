const fs = require('fs');
let content = fs.readFileSync('services/geminiService.ts', 'utf8');

const newRule = `
16. BẮT BUỘC ĐỐI VỚI VẼ ĐỒ THỊ HÀM SỐ VÀ TIỆM CẬN (ĐỂ HỖ TRỢ ẨN/HIỆN CODE):
    - Tất cả các lệnh vẽ đồ thị hàm số BẮT BUỘC phải được đặt ngay dưới dòng chú thích chuẩn sau:
      % --- ĐỒ THỊ HÀM SỐ ---
      \\draw[line width=0.6pt, smooth, samples=..., domain=xmin:xmax,
          % postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, above left] {$y=... $};}}, decorate}
      ] % lưu ý: dấu đóng ngoặc vuông phải hiển thị riêng một dòng
        plot (\\x, {f(\\x)});
    - Tất cả các lệnh vẽ tiệm cận BẮT BUỘC phải được đặt ngay dưới dòng chú thích chuẩn sau:
      % --- TIỆM CẬN ---
      \\draw[dashed, line width=0.6pt, domain=xmin:xmax]
        plot (\\x, {g(\\x)});
    - Phải có một dòng trống (blank line) phân tách giữa các khối vẽ này.
`;

content = content.replace("15. QUY TẮC HIỂN THỊ KHOẢNG/ĐOẠN TRÊN TRỤC SỐ (BẮT BUỘC):", newRule + "\n15. QUY TẮC HIỂN THỊ KHOẢNG/ĐOẠN TRÊN TRỤC SỐ (BẮT BUỘC):");
fs.writeFileSync('services/geminiService.ts', content);
