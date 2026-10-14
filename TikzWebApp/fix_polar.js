import fs from 'fs';

let content = fs.readFileSync('services/geminiService.ts', 'utf8');
const searchStr = `   - ĐỐI VỚI HÌNH ĐA DIỆN (CHÓP, LĂNG TRỤ, CHỮ NHẬT...):
     + LUÔN xác định điểm gốc có tọa độ (0,0). Các điểm còn lại xác định bằng tọa độ cực và các phép biến hình (phép đối xứng, tỷ lệ, tịnh tiến, vị tự,...).`;

const replaceStr = `   - ĐỐI VỚI HÌNH ĐA DIỆN (CHÓP, LĂNG TRỤ, CHỮ NHẬT...):
     + LUÔN xác định điểm gốc có tọa độ (0,0). Các điểm còn lại xác định bằng tọa độ cực và các phép biến hình (phép đối xứng, tỷ lệ, tịnh tiến, vị tự,...).
     + LƯU Ý QUAN TRỌNG VỀ TỌA ĐỘ CỰC TRÊN TRỤC HOÀNH: Thay vì dùng tọa độ đề-các (a,0) thì BẮT BUỘC dùng tọa độ cực (0:a) (với a>0). Thay vì dùng (-a,0) (với a>0) thì BẮT BUỘC dùng (180:a). Học và áp dụng đồng nhất trên hệ thống.`;

content = content.replace(searchStr, replaceStr);
fs.writeFileSync('services/geminiService.ts', content);
