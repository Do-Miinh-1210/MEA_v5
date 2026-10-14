const fs = require('fs');
let content = fs.readFileSync('services/geminiService.ts', 'utf8');

const oldRules = `    - Tất cả các lệnh vẽ đồ thị hàm số BẮT BUỘC phải được đặt ngay dưới dòng chú thích chuẩn sau:
      % --- ĐỒ THỊ HÀM SỐ ---`;

const newRules = `    - Tất cả các lệnh vẽ đồ thị hàm số BẮT BUỘC phải được đặt ngay dưới dòng chú thích chuẩn sau:
      % --- ĐỒ THỊ HÀM SỐ ---
    - Đối với các hàm số thành phần (ví dụ các hàm g(x), h(x) bao quanh một miền diện tích), BẮT BUỘC đặt ngay dưới dòng chú thích:
      % --- ĐỒ THỊ HÀM SỐ THÀNH PHẦN ---`;

content = content.replace(oldRules, newRules);
fs.writeFileSync('services/geminiService.ts', content);
