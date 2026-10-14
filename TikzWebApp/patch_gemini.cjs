const fs = require('fs');

const file = 'services/geminiService.ts';
let content = fs.readFileSync(file, 'utf8');

const oldEnd = `    - Ví dụ đối với khoảng $(a; b)$: Sử dụng node chứa dấu "(" tại vị trí a và node chứa dấu ")" tại điểm b, thay vì dùng arc hay đường cong tròn.\n\`;`;

const newRules = `    - Ví dụ đối với khoảng $(a; b)$: Sử dụng node chứa dấu "(" tại vị trí a và node chứa dấu ")" tại điểm b, thay vì dùng arc hay đường cong tròn.

16. QUY TẮC VẼ ĐỒ THỊ TOÁN HỌC (TÔ MIỀN DIỆN TÍCH):
   - Cấu trúc chuẩn: Sử dụng \\\\documentclass[tikz,border=10mm]{standalone}. Bắt buộc gọi các thư viện: arrows.meta, patterns.meta, decorations.markings.
   - Tham số hóa tuyệt đối (Bắt buộc): Mọi hàm số ($f(x), g(x)...$), giới hạn vẽ ($xmin, xmax, ymin, ymax$), và các điểm giao/cận ($a, b$) phải được khai báo tập trung bằng declare function={...} ngay đầu môi trường tikzpicture. Không viết trực tiếp số liệu hay công thức vào bên trong các lệnh \\\\draw hay \\\\fill.
   - Clipping: Toàn bộ lệnh vẽ đồ thị và tô màu phải được bọc trong môi trường \\\\begin{scope} và bị cắt xén (clip) bởi vùng rectangle giới hạn từ $xmin, ymin$ đến $xmax, ymax$.
   - Trục tọa độ & Mũi tên: Trục tọa độ dùng mũi tên -Stealth, nét 0.7pt. Căn chỉnh nhãn $x, y, O$ bằng shift={...} để tránh đè nét.
   - Vẽ vùng diện tích: Dùng pattern=Lines với thông số cụ thể (góc, khoảng cách, độ dày nét) từ thư viện patterns.meta.
   - Gắn nhãn đồ thị (Labeling): Tuyệt đối không dùng tọa độ cứng để đặt tên hàm số. Bắt buộc dùng postaction={decoration={markings...}} kết hợp node có thuộc tính transform shape, sloped để nhãn trượt và xoay bám theo đường cong một cách tự nhiên.
   - Đường gióng & Giao điểm: Các đường dóng từ trục lên đồ thị phải là nét đứt (dashed), và phải tính tọa độ động dựa vào hàm số đã khai báo (VD: (a,{f(a)})). Chấm đậm các giao điểm nổi bật. Hiệu chỉnh thẩm mỹ với line join=round, line cap=round.\`;`;

content = content.replace(oldEnd, newRules);

fs.writeFileSync(file, content);
