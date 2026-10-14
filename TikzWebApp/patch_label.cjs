const fs = require('fs');
let content = fs.readFileSync('services/geminiService.ts', 'utf8');

const oldLabeling = `    - Gắn nhãn đồ thị (Labeling): CHỈ hiển thị nhãn của hàm số (tên đồ thị) khi người dùng yêu cầu rõ ràng. CHÚ Ý TUYỆT ĐỐI KHÔNG TỰ Ý GHI NHÃN HÀM SỐ NẾU KHÔNG CÓ YÊU CẦU. Nếu được yêu cầu ghi nhãn, tuyệt đối không dùng tọa độ cứng để đặt tên hàm số, mà BẮT BUỘC dùng \\\`postaction={decoration={markings, mark=at position ... with {\\\\\\node[transform shape, sloped, above] {$...$}}}}\\\` để nhãn trượt và xoay bám theo đường cong tự nhiên. Đối với miền nghiệm bất phương trình, đặt điểm mark sao cho nhãn phương trình nằm thoáng ở phần nửa trên đồ thị (ví dụ \\\`mark=at position 0.8\\\`), và mặc định để trong chế độ comment (%) (tắt hiển thị), chỉ người dùng xóa dấu % mới xuất hiện (ví dụ: \\\`% postaction={...}\\\`).`;

const newLabeling = `    - Gắn nhãn đồ thị (Labeling): BẮT BUỘC LUÔN LUÔN tạo mã để gắn nhãn hàm số (tên đồ thị, cho mọi đồ thị hàm số và đồ thị thành phần) và nhãn tiệm cận (nếu có). Tuyệt đối không dùng tọa độ cứng để đặt tên hàm số, mà BẮT BUỘC dùng \\\`postaction={decoration={markings, mark=at position ... with {\\\\\\node[transform shape, sloped, above left] {$...$}}}}\\\` để nhãn trượt và xoay bám theo đường cong tự nhiên. Tuy nhiên, toàn bộ dòng lệnh \\\`postaction=...\\\` này mặc định phải được đặt trong chế độ comment (%) (tức là ẩn đi), ví dụ: \\\`% postaction={...}\\\`.`;

content = content.replace(oldLabeling, newLabeling);
fs.writeFileSync('services/geminiService.ts', content);
