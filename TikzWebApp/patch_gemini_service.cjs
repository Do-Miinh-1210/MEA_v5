const fs = require('fs');
let content = fs.readFileSync('services/geminiService.ts', 'utf8');

const oldStr = `    - Tất cả các lệnh vẽ tiệm cận BẮT BUỘC phải được đặt ngay dưới dòng chú thích chuẩn sau:
      % --- TIỆM CẬN ---
      \\draw[dashed, line width=0.6pt, domain=xmin:xmax,
          % postaction={decoration={markings, mark=at position 0.2 with {\\node[transform shape, sloped, above left] {$y=... $};}}, decorate}
      ]
        plot (\\x, {g(\\x)});`;

const newStr = `    - BẮT BUỘC tất cả các lệnh vẽ tiệm cận (đứng, ngang, xiên) BẮT BUỘC phải được đặt ngay dưới dòng chú thích chuẩn:
      % --- TIỆM CẬN ---
    - VÀ tất cả các đường tiệm cận đều BẮT BUỘC phải có thêm tùy chọn nhãn ở chế độ không biên dịch (ẩn - comment %) để khi cần có thể bật lên:
      \\draw[dashed, line width=0.6pt, domain=xmin:xmax,
          % postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, above left] {$y=... $};}}, decorate}
      ]
        plot (\\x, {g(\\x)});
      (Chú ý thay đổi phương trình $y=...$ hoặc $x=...$ cho đúng với tiệm cận đó, và vị trí \`0.8\` có thể thay đổi tùy hình, nhưng mặc định là \`0.8\`).`;

content = content.replace(oldStr, newStr);

fs.writeFileSync('services/geminiService.ts', content);
