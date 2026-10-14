import { GoogleGenAI, ThinkingLevel } from "@google/genai";
import { CATEGORIES } from '../constants';
import type { Category } from '../types';

// Function to get the Gemini AI client instance
const getGoogleGenAIClient = () => {
  // Ưu tiên lấy từ localStorage (do người dùng nhập), sau đó mới đến biến môi trường
  const userKey = typeof window !== 'undefined' ? localStorage.getItem('GEMINI_USER_KEY') : null;
  let apiKey = userKey || process.env.GEMINI_API_KEY || process.env.API_KEY;

  if (!apiKey) {
    throw new Error("API Key not found. Please enter your API Key.");
  }
  
  // Clean apiKey to prevent "String contains non ISO-8859-1 code point" in Headers
  apiKey = apiKey.trim().replace(/[^\x20-\x7E]/g, '');

  return new GoogleGenAI({ apiKey });
};

// ĐỊNH NGHĨA PHONG CÁCH VẼ CỦA THẦY TUẤN
// Đây là "trí nhớ" của AI về phong cách cụ thể mà bạn yêu cầu.
const USER_STYLE_GUIDE = `
QUY TẮC VẼ HÌNH TIKZ CỦA TÔI (BẮT BUỘC TUÂN THỦ 100%):

1. CẤU TRÚC KỊCH BẢN TIKZ (BẮT BUỘC):
   - Toàn bộ hệ thống code mã tikz bắt buộc phải sử dụng nhất quán và đồng bộ font chữ "\normalsize" (ví dụ: \begin{tikzpicture}[..., every node/.style={font=\normalsize}, ...]).

2. KHAI BÁO BIẾN & THAM SỐ (QUAN TRỌNG NHẤT):
   - KHÔNG dùng số liệu cứng trực tiếp trong tọa độ các điểm chính.
   - BẮT BUỘC sử dụng \`declare function\` ngay đầu \`tikzpicture\` để định nghĩa: cạnh (a, b, c), chiều cao (h), bán kính (r), góc (goc/alpha...), hệ số co giãn, v.v.
   - Với số liệu cồng kềnh thì đặt biến phụ trước để code gọn gàng và dễ nhận biết chỉnh sửa nếu cần (ví dụ như nghiệm cồng kềnh thì đặt biến phụ "xmot, xhai, ymot, yhai").
   - Ví dụ chuẩn: \`\\begin{tikzpicture}[declare function={a=5; h=4; r=3; goc=60; xmot=sqrt(2)/2; ymot=-3*sqrt(2);}]\`

2. HÌNH HỌC KHÔNG GIAN (3D) & XỬ LÝ NÉT KHUẤT:
   - ĐỐI VỚI HÌNH ĐA DIỆN (CHÓP, LĂNG TRỤ, CHỮ NHẬT...):
     + LUÔN xác định điểm gốc có tọa độ (0,0). Các điểm còn lại xác định bằng tọa độ cực và các phép biến hình (phép đối xứng, tỷ lệ, tịnh tiến, vị tự,...).
     + LƯU Ý QUAN TRỌNG VỀ TỌA ĐỘ CỰC TRÊN TRỤC HOÀNH: Thay vì dùng tọa độ đề-các (a,0) thì BẮT BUỘC dùng tọa độ cực (0:a) (với a>0). Thay vì dùng (-a,0) (với a>0) thì BẮT BUỘC dùng (180:a). Học và áp dụng đồng nhất trên hệ thống.
     + TUYỆT ĐỐI KHÔNG dùng \`line cap=round\` trong bất kỳ trường hợp nào (đã bị loại bỏ trong hệ thống). KHÔNG dùng \`line join=round\` cho các hình hình học/đa diện cần sự vuông vắn.
     + Ký hiệu góc vuông LUÔN dùng: \`\\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=...--...--...};\`.
   - Phải xác định đúng góc nhìn để phân biệt nét liền/nét đứt.
   - Sử dụng thư viện \`tikz-3dplot\` và lệnh \`\\tdplotsetmaincoords{...}{...}\` khi cần thiết.
   - Đáy tròn/Elip 3D:
     - PHẢI chia miền vẽ (\`domain\`) thành 2 phần riêng biệt.
     - Phần bị khuất: Dùng \`dash pattern=on 2pt off 1.5pt\`.
     - Phần nhìn thấy: Vẽ thường.
     - Ví dụ chuẩn: 
       \`\\draw[dash pattern=on 2pt off 1.5pt] plot[domain=0:180] ({r*cos(\\x)},{r*sin(\\x)},0);\`
       \`\\draw plot[domain=180:360] ({r*cos(\\x)},{r*sin(\\x)},0);\`

3. TỰ ĐỘNG HÓA & GÁN NHÃN:
   - Sử dụng vòng lặp \`\\foreach\` để vẽ điểm và gán nhãn hàng loạt. KHÔNG code thủ công từng dòng nếu có thể gộp.
   - Đối với tất cả các hình học, các nhãn điểm ở lệnh foreach luôn điều chỉnh bằng độ (tuỳ chỉnh góc). BẮT BUỘC dùng nhãn điểm 2 biến trong lệnh \`\\foreach\` (đó là tên nhãn và góc đặt nhãn). Cú pháp chuẩn: \`node[shift={(\\goc:9pt)}]{\\$\\t\\$}\`. Nhãn điểm trong hình vẽ luôn tối ưu lệnh \`\\foreach\` như thế này (Ví dụ kỹ thuật phong cách: Gom các điểm có cùng góc vào một lệnh \`\\foreach\`):
     \`\\foreach \\x/\\goc in {A/170, B/-90, C/-90, D/0, A'/90, B'/90, C'/90, D'/90}{\`
       \`\\draw[line width=0.6pt] (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}] {$\\x$};\`
     \`}\`
   - TUYỆT ĐỐI không dùng các từ khoá "above, below, left, right" trong mảng vị trí của foreach. Phải dùng số đo phần độ.

4. QUY TẮC VẼ PATTERN (GẠCH CHÉO, NỀN CHÌM):
   - Khi cần vẽ vùng gạch chéo (ví dụ: bảng biến thiên, miền nghiệm), BẮT BUỘC dùng cú pháp: \`pattern={Lines[angle=..., distance=..., line width=0.3pt]}, pattern color=gray!70\`.
   - Đối với đồ thị miền nghiệm bất phương trình, các đường pattern KHÔNG được gạch ở các góc 0, 90, 180, -90 độ. PHẢI dùng các đường xiên với các góc như 30, 45, 60, 75, 120, 150 độ để tránh nhầm lẫn với trục tọa độ. CHÚ Ý khoảng cách khoảng kẻ (distance) phải thực hiện nghiêm ngặt như sau:
     + Luôn dùng \`distance=4pt\` nếu biểu diễn 1 đến 2 miền nghiệm bất phương trình.
     + Luôn dùng \`distance=5pt\` nếu biểu diễn từ 3 miền nghiệm bất phương trình trở lên.
   - KHÔNG dùng \`pattern=north west lines\` hay \`pattern color=black!70\` để đảm bảo đường kẻ mảnh, khoảng cách đều và nền chìm.

5. BẢNG BIẾN THIÊN (tkz-tab) THEO PHONG CÁCH "BẢNG BIẾN THIÊN 2" VÀ "BẢNG BIẾN THIÊN 3":
   - BẮT BUỘC KHÔNG DÙNG \`\\tkzTabVar\` để vẽ mũi tên biến thiên. Phải vẽ thủ công bằng \`\\path\` và \`\\draw[-Stealth]\`.
   - Sử dụng gói \`tkz-tab\` với các tùy chọn chuẩn: \`\\tkzTabInit[nocadre=false, lgt=..., espcl=..., deltacl=0.6]\`. Bảng biến thiên luôn ở chế độ mặc định "nocadre=false" và BẮT BUỘC "deltacl=0.6".
   - NGUYÊN TẮC QUAN TRỌNG VỀ THAM SỐ lgt: Tự động nhận diện nhãn hàm số để đưa ra lgt phù hợp, nếu có nhãn là “y” thì \`lgt=1.2\`, nếu có nhãn là “f(x)” thì \`lgt=1.5\`.
   - QUY TẮC ĐIỀU CHỈNH TỌA ĐỘ TRONG BIẾN THIÊN 3:
     1. Vị trí các giá trị:
        - Nhãn giá trị của y (f(x)) luôn phân cấp theo các điểm N_{ij} (với j chỉ nhận giá trị 2 hoặc 3).
        - Nếu giá trị gần dòng kẻ 2 (điểm cao): dùng N_{i2} kèm theo \`yshift=-8pt\` (hoặc \`yshift=-16pt\` nếu cần xa hơn một chút). Ví dụ: \`[yshift=-8pt]N22\`.
        - Nếu giá trị ở giữa: cũng dùng N_{i2} kèm \`yshift=-16pt\`.
        - Nếu giá trị thấp nhất (gần dòng kẻ 3): dùng N_{i3} kèm theo \`yshift=8pt\` (hoặc \`yshift=16pt\` nếu cần xa hơn). Ví dụ: \`[yshift=8pt]N13\`.
        - Nếu ở vị trí tiệm cận đứng (2 gạch), phải dịch sang bên trái/phải bằng \`xshift=-16pt\` hoặc \`xshift=16pt\`. Ví dụ: \`[xshift=-16pt, yshift=8pt]N23\`, \`[xshift=16pt, yshift=-8pt]N22\`.
        - Các vị trí ở giữa chia đều theo giá trị còn lại để bảng biến thiên luôn trực quan.
      2. QUY TẮC CO GIÃN THÔNG MINH VÀ espcl (THỰC HIỆN NGHIÊM NGẶT):
         - Cột 1 (chứa x, f'(x), f(x) hoặc y', y): Phù hợp với lgt như trên.
         - Độ rộng dòng 1 và dòng 2 (chiều cao dòng): Tất cả bảng biến thiên ĐỀU 0.7 mặc định (ví dụ: \`$x$/0.7, $f'(x)$/0.7\` hoặc \`$y'$/0.7\`).
         - Dựa vào SỐ GIÁ TRỊ của x (tính cả âm vô cùng và dương vô cùng), BẮT BUỘC áp dụng:
           + Nếu x có 3 giá trị: \`espcl=3.5\` làm mặc định; dòng cuối là hàm số với chiều cao 2 (ví dụ: \`$y$/2.\` hoặc \`$f(x)$/2.\`).
           + Nếu x có 4 giá trị: \`espcl=2.5\` làm mặc định; dòng cuối là hàm số với chiều cao 2.5 (ví dụ: \`$y$/2.5\` hoặc \`$f(x)$/2.5\`).
           + Nếu x có 5 giá trị: \`espcl=2\` làm mặc định; dòng cuối là hàm số với chiều cao 2.5 (ví dụ: \`$y$/2.5\` hoặc \`$f(x)$/2.5\`).
      3. Điểm không xác định: Các giá trị làm cho y' và y không xác định thì luôn dùng 2 đoạn thẳng song song cách nhau 1pt. Lệnh bắt buộc phải là: \`\\draw[double distance=1pt, double=white, line width=0.4pt] (N...) -- (N...);\`. Trong bảng biến thiên độ dày đường kẻ luôn mặc định như trên.
   - Định dạng chiều cao các dòng ví dụ: \`{ $x$/0.7, $f'(x)$/0.7, $f(x)$/2.5}\` (KHÔNG ĐƯỢC thêm bất kỳ lệnh font nào vì đã có \`every node/.style={font=\\normalsize}\`).
   - Các giá trị x: \`{ $-\\infty$, $0$, $+\\infty$}\` (KHÔNG ĐƯỢC thêm lệnh font kích thước).
   - Dòng xét dấu: \`\\tkzTabLine{, +, 0, -, 0, +, }\` (KHÔNG ĐƯỢC bọc trong lệnh font kích thước). 
     + NGUYÊN TẮC BẮT BUỘC: Trong mã code tikz bảng biến thiên bỏ chữ "d" trong đoạn mã dòng xét dấu. Ví dụ: thay vì ghi \`\\tkzTabLine{, -, 0, +, d, +, 0, -, }\` thì TUYỆT ĐỐI bỏ chữ "d" và để trống khoảng cách đó, tức là chỉ ghi: \`\\tkzTabLine{, -, 0, +,  , +, 0, -, }\`.
   - Tất cả phân số trong code bắt buộc phải ghi dạng \`\\dfrac{}{}\`.
   - Vẽ mũi tên biến thiên thủ công:
     + Dùng \`\\path\` kết hợp tọa độ sinh ra bởi \`tkz-tab\` (như \`N13\`, \`N22\`, \`N32\`, \`N42\`) và \`yshift\` để đặt các node giá trị (A1, A2, A3...).
     + Ví dụ (KHÔNG ĐƯỢC dùng lệnh font chữ khác): 
       \`\\path\`
       \`([yshift=8pt]N13) node (A1) { $-\\infty$}\`
       \`([yshift=-8pt]N22) node (A2) { $-\\dfrac{22}{27}$}\`
       \`([yshift=-50pt]N32) node (A3) { $-2$}\`
       \`([yshift=-8pt]N42) node (A4) { $+\\infty$};\`
     + Dùng vòng lặp \`\\foreach\` để vẽ mũi tên:
       \`\\foreach \\i/\\j in {1/2, 2/3, 3/4} { \\draw[-Stealth] (A\\i) -- (A\\j); }\`

5.5 BẢNG XÉT DẤU (BXD):
   - Bảng xét dấu (BXD) tương tự như Bảng biến thiên nhưng CHỈ CÓ 2 DÒNG (dòng $x$ và dòng $f'(x)$ hoặc biểu thức cần xét dấu).
   - Sử dụng \`\\tkzTabInit[nocadre=false, lgt=..., espcl=2.5, deltacl=0.6]\` (lgt=1.2 nếu nhãn là "y", lgt=1.5 nếu nhãn là "f(x)").
   - Định dạng chiều cao các dòng: \`{ $x$/1, $f'(x)$/0.7}\` (KHÔNG ĐƯỢC thêm lệnh font kích thước).
   - Các giá trị x: \`{ $-\\infty$, $0$, $+\\infty$}\` (KHÔNG ĐƯỢC thêm lệnh font kích thước).
   - Dòng xét dấu: Tuân thủ nghiêm ngặt nguyên tắc bỏ chữ "d" và để trống như ở phần Bảng biến thiên. Ví dụ: \`\\tkzTabLine{, +, 0, -,  , +, 0, -, }\`.
   - Tất cả phân số phải ghi dạng \`\\dfrac{}{}\`.
   - Không có dòng thứ 3 (không có \`\\tkzTabVar\` hay vẽ mũi tên).

6. QUY TẮC FONT CHỮ VÀ ĐIỂM (RẤT QUAN TRỌNG - THỰC HIỆN NGHIÊM NGẶT):
   - MỤC 1: Đối với MỌI code TikZ vẽ phần "bảng biến thiên", "đồ thị hàm số", "bảng xét dấu", hình học không gian, hình học phẳng... TÓM LẠI LÀ TOÀN BỘ HỆ THỐNG CODE MÃ TIKZ:
     + BẮT BUỘC sử dụng nhất quán và đồng bộ font chữ \`\\normalsize\`. BẮT BUỘC bỏ tất cả các lệnh font khác (như \`\\Large\`, \`\\large\`).
     + Cách duy nhất để thiết lập font chữ là thêm \`every node/.style={font=\\normalsize}\` vào phần tùy chọn của môi trường \`tikzpicture\`.
     + LƯU Ý KHI DÙNG LINE JOIN: CẤM DÙNG \`line join=round\` cho các hình cần sự vuông vắn (như hình học phẳng, hình học không gian, đa giác...). CHỈ DÙNG \`line join=round\` cho đồ thị hàm số hoặc các đường cong.
     + VỀ LINE CAP: TUYỆT ĐỐI KHÔNG SỬ DỤNG \`line cap=round\` trong bất kỳ code TikZ nào.
     + Ví dụ chuẩn đồ thị: \`\\begin{tikzpicture}[>=stealth, line join=round, every node/.style={font=\\normalsize}, declare function={...}]\`
     + Ví dụ chuẩn hình học: \`\\begin{tikzpicture}[>=stealth, every node/.style={font=\\normalsize}, declare function={...}]\`
   - MỤC 2: Đối với điểm:
     + Các điểm trong hình học không tô trắng mà để màu đen mặc định với đường tròn có bán kính \`0.4pt\`. Các điểm đối với đồ thị hàm số thường là \`1pt\` (hoặc theo yêu cầu cụ thể).
     + Ví dụ câu lệnh chuẩn trong hình học: \`\\foreach \\p/\\goc in {S/135, A/-45, B/-135, C/-45, D/0, H/-90, M/45, N/-45}{ \\draw[line width=0.6pt] (\\p) circle (0.4pt) node[shift={(\\goc:9pt)}] {$\\p$}; }\`
   - Áp dụng nghiêm ngặt cho cả code xuất từ thư viện có sẵn hoặc tạo mới.

6.5. NGUYÊN TẮC: NHÃN TRÊN ĐƯỜNG VÀ ĐỒ THỊ HÀM SỐ (THỰC HIỆN NGHIÊM NGẶT):
   - Đối với nhãn đường thẳng và đồ thị hàm số, BẮT BUỘC thực hiện cú pháp: \`node[pos=..., sloped, above/below] {$...$}\`.
   - Ví dụ: \`node[pos=0.5, sloped, above] {$x+y=5$};\`
   - TỰ ĐỘNG XỬ LÝ (áp dụng cho mọi nhãn trên đường thẳng/đường cong):
     + Mọi nhãn trên đường thẳng hoặc đường cong đều phải có: \`sloped\`.
     + Vị trí \`pos\` tự động chọn: \`0.5\` nếu không có giao điểm, \`0.4\` hoặc \`0.6\` nếu có.
     + \`above\`/\`below\`: dựa trên hướng vẽ (trái→phải: \`above\`, phải→trái: \`below\`).
     + Nếu đường gần thẳng đứng: dùng \`auto\` để TikZ tự quyết định.

6.6. NGUYÊN TẮC BẮT BUỘC: VỊ TRÍ NHÃN TỌA ĐỘ VÀ ĐIỂM TRONG HÌNH HỌC:
   - Tất cả vị trí nhãn giá trị hoành độ và tung độ, nhãn điểm trong hình học sử dụng linh hoạt độc lập hoặc kết hợp các chức năng sau: "above", "below", "right", "left".
   - LƯU Ý: Tuyệt đối không kết hợp "above và below". 
   - Ví dụ hợp lệ: "above left, above right, below left, below right, above, below, left, right".

7. NGUỒN THAM KHẢO & HỌC HỎI:
   - Hãy sử dụng kiến thức rộng lớn của bạn về TikZ, bao gồm cả các kỹ thuật từ "https://texample.net/" (ví dụ: shading, intersections phức tạp, lăng trụ, pattern).
   - TUY NHIÊN: Khi áp dụng các kỹ thuật đó, bạn PHẢI VIẾT LẠI CODE theo phong cách (1), (2), (3), (4), (5), (6) của tôi (dùng declare function, dash pattern cụ thể).

8. CÔNG CỤ HỖ TRỢ:
   - Dùng thư viện \`calc\` để tính toán tọa độ trung điểm, giao điểm...
   - Dùng \`intersection of\` để tìm giao điểm tự động.
9. GHI CHÚ KHI CÓ NHIỀU PHẦN (BẢNG BIẾN THIÊN VÀ ĐỒ THỊ):
   - Nếu yêu cầu vẽ cả bảng biến thiên và đồ thị hàm số, BẮT BUỘC phải thêm ghi chú rõ ràng ở đầu mỗi phần.
   - Ví dụ: Thêm dòng \`% code Bảng biến thiên\` trước đoạn code vẽ bảng biến thiên.
   - Thêm một dòng trắng giữa hai phần.
   - Thêm dòng \`% code đồ thị hàm số\` trước đoạn code vẽ đồ thị.

10. QUY TRÌNH VẼ ĐỒ THỊ HÀM SỐ (BẮT BUỘC TÍNH TOÁN TRƯỚC KHI XUẤT CODE):
   - PHASE 1: KHẢO SÁT VÀ TÍNH TOÁN CHI TIẾT HÀM SỐ
     + Tính đạo hàm (cấp 1, cấp 2) để tìm cực trị, điểm uốn.
     + Tìm cực trị (nếu có) để xác định tọa độ các điểm đặc biệt.
     + Tìm giao điểm với trục Ox, Oy.
     + Xác định tiệm cận (đứng, ngang, xiên).
     + Tìm điểm uốn, tâm đối xứng.
     + Xét tính chẵn lẻ, tuần hoàn.
   - PHASE 2: THIẾT LẬP KHÔNG GIAN HIỂN THỊ CÂN ĐỐI
     + Xác định tâm đối xứng & khoảng hiển thị: Hàm chẵn (Trục Oy, x thuộc [-a, a]), Hàm lẻ (Gốc O, x thuộc [-a, a]), Hàm bậc 3 (Điểm uốn I(x0, y0), x thuộc [x0-a, x0+a]), Hàm tuần hoàn (Tâm chu kỳ, 1 hoặc 2 chu kỳ), Hàm phân thức (Giao 2 tiệm cận, cân đối quanh giao điểm).
     + Cân chỉnh tỷ lệ & bố cục: Đối xứng trái-phải, trên-dưới; Tỷ lệ khung hình (xscale, yscale); Hai nhánh đồ thị phải có cùng độ dài và độ cong tương ứng.
     + NGUYÊN TẮC BẮT BUỘC TÍNH ymin, ymax: Căn cứ vào tung độ "tâm đối xứng" (giao điểm hai tiệm cận đối với đồ thị có 2 tiệm cận, hoặc tọa độ điểm uốn đối với đồ thị hàm đa thức), bạn PHẢI thiết lập \`ymin = y_{tâm đối xứng} - 4\` và \`ymax = y_{tâm đối xứng} + 4\` một cách nghiêm khắc, bắt buộc tính toán sao cho phần đồ thị được cắt chính xác.
     + Xác định vị trí đặt nhãn (label): Chọn anchor phù hợp, đặt ở đầu mút hoặc giữa trục, cách an toàn 2-3mm, không chồng lấn.
   - PHASE 2.5: TỐI ƯU VỊ TRÍ NHÃN - GIẢI QUYẾT TRIỆT ĐỂ VẤN ĐỀ CHỒNG LẤN & CÂN ĐỐI (BẮT BUỘC)
     + LUÔN ƯU TIÊN DÙNG "anchor" KẾT HỢP VỚI "south, north, west, east" để tối ưu hóa việc nhãn đè lên tiệm cận, đồ thị và các nhãn khác.
     + VỊ TRÍ NHÃN: TÍNH TOÁN KỸ LƯỠNG, KIỂM CHỨNG VÀ THỬ NGHIỆM HÌNH ẢNH TRƯỚC KHI XUẤT CODE TIKZ TRÁNH BỊ ĐÈ LÊN NHAU. BẠN PHẢI TÍNH TOÁN, KIỂM TRA, THỬ NGHIỆM TRƯỚC KHI XUẤT CODE CHÍNH THỨC.
     + Hệ thống Anchor ưu tiên:
       * Góc phần tư I (x>0, y>0): south west -> south -> west. Đặt nhãn về phía dưới-trái.
       * Góc phần tư II (x<0, y>0): south east -> south -> east. Đặt nhãn về phía dưới-phải.
       * Góc phần tư III (x<0, y<0): north east -> north -> east. Đặt nhãn về phía trên-phải.
       * Góc phần tư IV (x>0, y<0): north west -> north -> west. Đặt nhãn về phía trên-trái.
       * Trên trục Ox (y=0, x≠0): north (nếu đồ thị ở dưới) -> south (nếu đồ thị ở trên). Tránh đè lên đồ thị.
       * Trên trục Oy (x=0, y≠0): east (nếu đồ thị ở trái) -> west (nếu đồ thị ở phải). Tránh đè lên đồ thị.
       * Điểm gốc tọa độ O (x=0, y=0): Thực hiện nghiêm ngặt việc luôn tìm vị trí góc trống (1 trong 4 góc phần tư) để đặt nhãn điểm "O", tránh đè lên đồ thị.
       * Gần tiệm cận đứng/ngang: Tránh về phía xa tiệm cận. Không để nhãn chạm tiệm cận.
     + Quy trình kiểm tra và điều chỉnh nhãn (4 bước bắt buộc):
       1. Phân tích vùng trống: Xác định vùng trống, hướng di chuyển tránh chồng lấn, ưu tiên đặt nhãn vào vùng trống rộng nhất.
       2. Áp dụng anchor phù hợp theo thứ tự ưu tiên.
       3. Dịch chuyển nhãn khi cần (Label offset): Có thể sử dụng các giá trị định vị như "above, below, left" hoặc sử dụng 'shift={(độ:bán kính)}' (ví dụ: 'shift={(170:9pt)}') để điều chỉnh nhãn xoay quanh điểm tọa độ.
       4. Kiểm tra và cân chỉnh độ cao nhãn: Chuẩn hóa độ cao bằng cách dùng \`\\vphantom\` (ví dụ: \`\\node[anchor=south west] at (2,3) {$A\\vphantom{(2;3)}$};\`) hoặc dùng \`text height\`, \`text depth\`.
     + Kiểm tra chồng lấn cụ thể:
       * Điểm gốc O: Thực hiện nghiêm ngặt việc luôn tìm vị trí góc trống (1 trong 4 góc phần tư) để đặt nhãn điểm "O".
       * Với đồ thị: Khoảng cách tối thiểu 2-3mm từ nhãn đến đồ thị. Nếu chạm -> dịch chuyển nhãn ra xa.
       * Với tiệm cận: Nhãn không được đè lên đường tiệm cận (dashed), không được quá sát tiệm cận (< 3mm).
       * Với nhau: Các nhãn không được chồng lấn lên nhau. Khoảng cách giữa các nhãn >= 4mm. Sắp xếp theo hàng/lối nếu có thể.
       * Với trục: Nhãn số trên trục không chạm vào nhau, cách vạch chia 1-2mm, không đè lên đồ thị.
     + Chuẩn hóa vị trí nhãn (Label Alignment Standardization): Dùng cùng một anchor cho nhóm nhãn, dùng baseline đồng nhất (\`text height=1.5ex, text depth=0.25ex\`), sắp xếp theo hàng ngang/dọc.
     + Nguyên tắc vàng cho nhãn đẹp: Ưu tiên vùng trống, Anchor đúng góc phần tư, Dịch chuyển nhẹ (1-2mm), Đồng bộ độ cao, Cùng anchor cho nhóm, Kiểm tra chồng lấn, Khoảng cách >= 3mm, Hài hòa tổng thể.
   - PHASE 3: KIỂM TRA LỖI & TỐI ƯU
     + Kiểm tra phép tính không xác định (chia 0, logarit âm, căn bậc chẵn âm).
     + Đảm bảo các điểm đặc biệt nằm trong khung hình hiển thị.
     + Kiểm tra trực quan đồ thị không bị lệch.
     + Khoảng trống hai bên, trên dưới cân đối.
   - PHASE 4: XUẤT CODE TIKZ HOÀN CHỈNH
     + CHỈ XUẤT CODE khi đã hoàn thành tất cả các phase trên trong tư duy/tính toán (không xuất kết quả trung gian).
     + Giữ nguyên nhãn theo yêu cầu, bố trí hợp lý, đường nét rõ ràng (đồ thị đậm hơn trục tọa độ), màu sắc phù hợp.

10. ĐÁNH DẤU VÀ GIÓNG ĐIỂM TRỤC TỌA ĐỘ (BẮT BUỘC):
    - Thực hiện nghiêm ngặt bắt buộc: Chỉ gióng các đoạn thẳng từ các điểm cực trị (không gióng các đoạn thẳng từ các điểm khác nếu tôi không yêu cầu).
    - MỘT NGOẠI LỆ ĐẶC BIỆT THỰC HIỆN NGHIÊM NGẶT: Khi tô diện tích giới hạn bởi đồ thị hàm số (có 2 hoặc 3 đồ thị), bạn CHỈ CẦN GIÓNG XUỐNG TRỤC HOÀNH (Ox) từ cận dưới, cận trên và giao điểm nằm giữa cận dưới và cận trên. TUYỆT ĐỐI KHÔNG gióng sang trục tung (Oy) ở bài toán tô miền diện tích này. KHÔNG gióng các điểm khác.
    - Bắt buộc phải luôn đánh dấu điểm (ví dụ: dùng \`\\fill (x,0) circle (1pt);\` và \`\\fill (0,y) circle (1pt);\`) ở các vị trí gióng trục từ điểm cực trị hoặc các giao điểm/cận tích phân xuống trục tọa độ (lưu ý ngoại lệ tô miền diện tích thì chỉ đánh dấu trên Ox).
    - Không được bỏ sót các điểm gióng này trên trục.

11. YÊU CẦU KỸ THUẬT BẮT BUỘC (ĐỘ DÀY, MŨI TÊN, ĐIỂM & NHÃN):
    - AI luôn ghi nhớ và thực hiện nghiêm ngặt mặc định cho tôi:
      + Mũi tên luôn là \`-Stealth\`.
      + Độ dày các trục tọa độ luôn là \`0.7pt\` (sử dụng \`line width=0.7pt\`).
      + Độ lớn của điểm đối với đồ thị hàm số là \`1pt\` (ví dụ: \`\\fill (x,y) circle (1pt);\`). Đối với các hình khác (hình học phẳng, không gian...), điểm là đường tròn màu đen mặc định, không tô trắng, bán kính \`0.4pt\` (ví dụ: \`\\draw[line width=0.6pt] (x,y) circle (0.4pt);\`).
      + Các đối tượng còn lại (đồ thị, tiệm cận, đường gióng...) độ dày luôn là \`0.6pt\` (sử dụng \`line width=0.6pt\`).
      + Nếu có thay đổi tôi sẽ bổ sung ở yêu cầu thêm đối với từng hình cụ thể.
    - Xử lý nhãn tại giao điểm với tiệm cận đứng và trục hoành:
      + Kiểm tra và điều chỉnh vị trí nhãn số để tránh chồng lấn lên đường tiệm cận.
      + Dịch chuyển nhãn sang trái/phải hoặc lên/xuống phù hợp (sử dụng \`xshift\`, \`yshift\` hoặc các anchor như \`above left\`, \`below right\`).
      + Vị trí nhãn hoành độ điểm giao giữa tiệm cận và trục hoành bị chồng lấn lên nhau bạn kiểm tra để điều chỉnh nhãn sang vị trí hợp lý.
    - Đối với hình vẽ 2D và 3D (Hình học phẳng, Hình học không gian):
      + Tính tọa độ chính xác để đặt các nhãn ở vị trí thích hợp, cân đối, đẹp mắt.
      + Nếu vị trí điểm đó có nhiều ký hiệu góc làm cho đặt nhãn điểm bị đè hoặc quá sát (ví dụ cho hình chóp S.ABCD có SA vuông góc với (ABCD) mà ta ký hiệu 2 góc vuông ở điểm A), BẮT BUỘC phải tách riêng nhãn điểm đó ra khỏi lệnh '\\foreach' chung và thiết lập bán kính lớn hơn ở lệnh 'shift' (ví dụ: dùng 'shift={(225:15pt)}' thay vì '9pt').
      + Đối với hình hộp chữ nhật, hình lập phương, khối hộp (hoặc các hình có cấu trúc tương tự): Vị trí điểm C' CẦN đặt ở góc 90 độ hoặc -25 độ, và điểm A CẦN đặt ở vị trí 170 độ để tránh đè nét và tối ưu hiển thị.
    - Quy tắc trình bày:
      + Luôn kiểm tra tỉ lệ và khoảng cách để hình vẽ cân đối, trực quan.
      + Đảm bảo tính thẩm mỹ và rõ ràng.

12. QUY TẮC VẼ ĐƯỜNG TIỆM CẬN (BẮT BUỘC):
    - Thực hiện nghiêm ngặt: Đối với vẽ đồ thị có tiệm cận thì code tiệm cận PHẢI đưa cùng vào bảng cắt hình ảnh (clip) cùng với đồ thị. Đưa code vẽ các đường tiệm cận (nếu có) vào giữa \`\\begin{scope}\` và \`\\end{scope}\` sau lệnh \`\\clip (xmin, ymin) rectangle (xmax, ymax);\` nhưng TRƯỚC code vẽ đồ thị hàm số.
    - Điều này đảm bảo tiệm cận không bị tràn ra ngoài khung hình và nằm dưới đồ thị hàm số.

13. QUY TẮC VẼ HỆ TRỤC TỌA ĐỘ (BẮT BUỘC):
    - Đối với hệ trục tọa độ luôn mặc định sử dụng đoạn code sau:
      \`% 2. HỆ TRỤC TỌA ĐỘ\`
      \`\\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};\`
      \`\\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[below left] {$y$};\`

14. YÊU CẦU ĐỐI VỚI VẼ ĐỒ THỊ VÀ TÔ MIỀN DIỆN TÍCH TỪ SGK MỚI:
    - Tham số hóa tuyệt đối (Bắt buộc): Mọi hàm số ($f(x), g(x)...$), giới hạn vẽ ($xmin, xmax, ymin, ymax$), và các điểm giao/cận ($a, b$) PHẢI được khai báo tập trung bằng \`declare function={...}\` ngay đầu môi trường \`tikzpicture\`. Tuyệt đối không viết trực tiếp số liệu hay công thức vào bên trong các lệnh \`\\draw\`.
    - Clipping: Toàn bộ lệnh vẽ đồ thị và tô màu phải được bọc trong môi trường \`\\begin{scope}\` và bị cắt xén (clip) bởi \`\\clip (xmin,ymin) rectangle (xmax,ymax);\`.
    - Vẽ vùng diện tích: BẮT BUỘC dùng \`pattern={Lines[angle=..., distance=..., line width=...]}\` từ thư viện \`patterns.meta\`.
    - Gắn nhãn đồ thị (Labeling): BẮT BUỘC LUÔN LUÔN tạo mã để gắn nhãn hàm số (tên đồ thị, cho mọi đồ thị hàm số và đồ thị thành phần) và nhãn tiệm cận (nếu có). Tuyệt đối không dùng tọa độ cứng để đặt tên hàm số, mà BẮT BUỘC dùng \`postaction={decoration={markings, mark=at position ... with {\\\node[transform shape, sloped, above left] {$...$}}}}\` để nhãn trượt và xoay bám theo đường cong tự nhiên. Tuy nhiên, toàn bộ dòng lệnh \`postaction=...\` này mặc định phải được đặt trong chế độ comment (%) (tức là ẩn đi), ví dụ: \`% postaction={...}\`.
    - Đường gióng & Giao điểm: Các đường gióng phải thiết lập tọa độ động ví dụ \`(a,{f(a)})\`, chấm đậm các giao điểm nổi bật. Hiệu chỉnh thẩm mỹ với \`line join=round\` (TUYỆT ĐỐI KHÔNG DÙNG \`line cap=round\`).


16. BẮT BUỘC ĐỐI VỚI VẼ ĐỒ THỊ HÀM SỐ VÀ TIỆM CẬN (ĐỂ HỖ TRỢ ẨN/HIỆN CODE):
    - Tất cả các lệnh vẽ đồ thị hàm số BẮT BUỘC phải được đặt ngay dưới dòng chú thích chuẩn sau:
      % --- ĐỒ THỊ HÀM SỐ ---
    - Đối với các hàm số thành phần (ví dụ các hàm g(x), h(x) bao quanh một miền diện tích), BẮT BUỘC đặt ngay dưới dòng chú thích:
      % --- ĐỒ THỊ HÀM SỐ THÀNH PHẦN ---
      \\draw[line width=0.6pt, smooth, samples=..., domain=xmin:xmax,
          % postaction={decoration={markings, mark=at position 0.8 with {\node[transform shape, sloped, above left] {$y=... $};}}, decorate}
      ] % lưu ý: dấu đóng ngoặc vuông phải hiển thị riêng một dòng
        plot (\\x, {f(\\x)});
    - Tất cả các lệnh vẽ tiệm cận (đứng, ngang, xiên) BẮT BUỘC phải được đặt ngay dưới dòng chú thích chuẩn sau:
      % --- TIỆM CẬN ---
    - VÀ tất cả các đường tiệm cận BẮT BUỘC phải có thêm tùy chọn nhãn ở chế độ không biên dịch (ẩn - comment %) để khi cần có thể bật lên:
      \\draw[dashed, line width=0.6pt, domain=xmin:xmax,
          % postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, above left] {$y=... $};}}, decorate}
      ]
        plot (\\x, {g(\\x)});
    - Phải có một dòng trống (blank line) phân tách giữa các khối vẽ này.

15. QUY TẮC HIỂN THỊ KHOẢNG/ĐOẠN TRÊN TRỤC SỐ (BẮT BUỘC):
    - Khi biểu diễn khoảng, nửa khoảng, đoạn trên trục số, TUYỆT ĐỐI KHÔNG vẽ cung tròn.
    - BẮT BUỘC sử dụng trực tiếp các ký tự dấu ngoặc có trên bàn phím: \`(\`, \`)\`, \`[\`, \`]\`.
    - Ví dụ đối với khoảng $(a; b)$: Sử dụng node chứa dấu "(" tại vị trí a và node chứa dấu ")" tại điểm b, thay vì dùng arc hay đường cong tròn.

16. QUY TẮC VẼ ĐỒ THỊ TOÁN HỌC (TÔ MIỀN DIỆN TÍCH):
   - Cấu trúc chuẩn: Sử dụng \\documentclass[tikz,border=10mm]{standalone}. Bắt buộc gọi các thư viện: arrows.meta, patterns.meta, decorations.markings.
   - Tham số hóa tuyệt đối (Bắt buộc): Mọi hàm số ($f(x), g(x)...$), giới hạn vẽ ($xmin, xmax, ymin, ymax$), và các điểm giao/cận ($a, b$) phải được khai báo tập trung bằng declare function={...} ngay đầu môi trường tikzpicture. Không viết trực tiếp số liệu hay công thức vào bên trong các lệnh \\draw hay \\fill.
   - Clipping: Toàn bộ lệnh vẽ đồ thị và tô màu phải được bọc trong môi trường \\begin{scope} và bị cắt xén (clip) bởi vùng rectangle giới hạn từ $xmin, ymin$ đến $xmax, ymax$.
   - Trục tọa độ & Mũi tên: Trục tọa độ dùng mũi tên -Stealth, nét 0.7pt. Căn chỉnh nhãn $x, y, O$ bằng shift={...} để tránh đè nét.
   - Vẽ vùng diện tích: Dùng pattern=Lines với thông số cụ thể (góc, khoảng cách, độ dày nét) từ thư viện patterns.meta.
   - Gắn nhãn đồ thị (Labeling): Tuyệt đối không dùng tọa độ cứng để đặt tên hàm số. Bắt buộc dùng postaction={decoration={markings...}} kết hợp node có thuộc tính transform shape, sloped để nhãn trượt và xoay bám theo đường cong một cách tự nhiên.
   - Đường gióng & Giao điểm: Các đường dóng từ trục lên đồ thị phải là nét đứt (dashed), và phải tính tọa độ động dựa vào hàm số đã khai báo (VD: (a,{f(a)})). Chấm đậm các giao điểm nổi bật. Hiệu chỉnh thẩm mỹ với line join=round, line cap=round.`;

export interface ImagePart {
    inlineData: {
        mimeType: string;
        data: string;
    };
}

const getTemplateLibraryAsString = (userLibrary?: Category): string => {
  let libraryString = '';
  
  if (userLibrary && userLibrary.subCategories.length > 0) {
    libraryString += `\n=== THƯ VIỆN CỦA TÔI (ƯU TIÊN CAO NHẤT) ===\n`;
    userLibrary.subCategories.forEach(subCategory => {
      subCategory.templates.forEach(template => {
        libraryString += `\nMẫu: ${template.title}\nMô tả: ${template.description}\nCode:\n\`\`\`latex\n${template.code}\n\`\`\`\n`;
      });
    });
  }

  libraryString += `\n=== THƯ VIỆN MẶC ĐỊNH ===\n`;
  CATEGORIES.forEach(category => {
    category.subCategories.forEach(subCategory => {
      subCategory.templates.forEach(template => {
        libraryString += `\nMẫu: ${template.title}\nMô tả: ${template.description}\nCode:\n\`\`\`latex\n${template.code}\n\`\`\`\n`;
      });
    });
  });

  return libraryString;
};


export const toggleCodeNotes = async (code: string, enableNotes: boolean): Promise<string> => {
    // Instant heuristic injection
    let cleanCode = code.replace(/^\s*%.*\n?/gm, '');
    // Normalize blank lines
    cleanCode = cleanCode.replace(/\n\s*\n/g, '\n');
    let lines = cleanCode.split('\n');
    let result: string[] = [];
    
    let addedMain = false;
    let addedAxes = false;
    let addedGraph = false;
    let addedPoints = false;
    
    const isTab = cleanCode.includes('tkzTabInit');

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];
        let trimmed = line.trim();

        if (!addedMain && trimmed.startsWith('\\begin{tikzpicture}')) {
            result.push(line);
            if (enableNotes) {
                result.push(isTab ? '\t% BẢNG BIẾN THIÊN' : '\t% ĐỒ THỊ HÀM SỐ');
            } else {
                result.push(''); // Blank line
            }
            addedMain = true;
            continue;
        }

        if (isTab) {
            if (trimmed.startsWith('\\tkzTabInit')) {
                if (enableNotes) result.push('\t% KHỞI TẠO BẢNG'); else if (result.length > 0 && result[result.length-1].trim() !== '') result.push('');
            }
            else if (trimmed.startsWith('\\tkzTabLine')) {
                if (enableNotes) result.push('\t% DÒNG DẤU ĐẠO HÀM'); else if (result.length > 0 && result[result.length-1].trim() !== '') result.push('');
            }
            else if (trimmed.startsWith('\\tkzTabVar')) {
                if (enableNotes) result.push('\t% DÒNG BIẾN THIÊN'); else if (result.length > 0 && result[result.length-1].trim() !== '') result.push('');
            }
        } else {
            if (!addedAxes && (trimmed.includes('\\draw[-Stealth') || trimmed.includes('\\draw[->')) && (trimmed.includes('xmin') || trimmed.includes('ymin') || trimmed.includes('0) --') || trimmed.includes('(0,'))) {
                if (enableNotes) result.push('\t% 1. HỆ TRỤC TỌA ĐỘ'); else if (result.length > 0 && result[result.length-1].trim() !== '') result.push('');
                addedAxes = true;
            }
            else if (!addedGraph && addedAxes && (trimmed.startsWith('\\begin{scope}') || trimmed.startsWith('\\clip') || trimmed.includes('plot ') || trimmed.includes('samples='))) {
                if (enableNotes) result.push('\t% 2. ĐỒ THỊ VÀ TIỆM CẬN'); else if (result.length > 0 && result[result.length-1].trim() !== '') result.push('');
                addedGraph = true;
            }
            else if (!addedPoints && addedGraph && (trimmed.startsWith('\\draw[dashed]') || trimmed.startsWith('\\fill') || (trimmed.startsWith('\\node') && !trimmed.includes('{$x$}') && !trimmed.includes('{$y$}')))) {
                if (enableNotes) result.push('\t% 3. ĐÁNH DẤU VÀ GIÓNG ĐIỂM'); else if (result.length > 0 && result[result.length-1].trim() !== '') result.push('');
                addedPoints = true;
            }
        }

        result.push(line);
    }

    return result.join('\n').replace(/\n{3,}/g, '\n\n').trim();
};

export const categorizeCode = async (code: string): Promise<string> => {
  try {
    const ai = getGoogleGenAIClient();
    const prompt = `Bạn là một chuyên gia phân loại mã nguồn TikZ/LaTeX. Hãy đọc đoạn mã sau và trả về MỘT TÊN NHÓM DUY NHẤT (ngắn gọn, dưới 6 từ) phản ánh tính chất của hình vẽ (ví dụ: Hình chóp, Đồ thị hàm số, Bảng biến thiên, Hình học phẳng, Hình học không gian, Hình trụ, Hình nón, Hình cầu, v.v.). CHỈ TRẢ VỀ TÊN NHÓM, KHÔNG GIẢI THÍCH THÊM.\n\nCode:\n${code.substring(0, 1500)}`;
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: prompt,
    });
    return response.text?.trim().replace(/["']/g, '') || "Chưa phân loại";
  } catch (error) {
    console.error("Error categorizing code:", error);
    return "Chưa phân loại";
  }
};

export const getHelpResponse = async (question: string): Promise<string> => {
    try {
        const ai = getGoogleGenAIClient();
        
        const systemPrompt = `Bạn là trợ lý ảo vui tính, hài hước và trung thực của ứng dụng "Code TikZ AI" do Thầy Tuấn phát triển.
Nhiệm vụ của bạn là trả lời các câu hỏi của người dùng về ứng dụng một cách linh hoạt, tự nhiên và không cứng nhắc.

Dưới đây là thông tin về ứng dụng để bạn dựa vào đó trả lời:
1. TÍNH NĂNG CHÍNH & TIỆN ÍCH ẨN:
- Tạo mã TikZ tự động từ văn bản, hình ảnh, hoặc tài liệu đính kèm.
- Chuyên vẽ: Đồ thị hàm số, Bảng biến thiên (BBT), Bảng xét dấu (BXD), Hình học không gian (3D), Hình học phẳng.
- Tải xuống file .tex, xem trước (Preview) hình ảnh trực tiếp trên web.
- Hỗ trợ nhập liệu bằng giọng nói (Micro), Giao diện tối/sáng (Dark/Light mode).
- **Chia sẻ code (Share Code):** Người dùng có thể tạo "Mã chia sẻ" cho một thư mục cụ thể. Đồng nghiệp chỉ cần nhập mã này vào App là nhận được toàn bộ code trong thư mục đó. Rất tiện cho làm việc nhóm!
- **Lưu trữ Thư viện cá nhân an toàn & thông minh:** Dữ liệu được lưu trữ an toàn. Người dùng nên phân loại code theo Thư mục/Nhóm (ví dụ: "Hình học 11", "Đề thi HSG") và dùng tính năng "Tìm kiếm nhanh" để quản lý thông minh.
- **Tải file .tex lên Thư viện (Bulk Upload):** Chỉ cần kéo thả hàng loạt file .tex hoặc .txt vào App, hệ thống sẽ tự động bóc tách và lưu trữ đồng loạt vào thư viện mà không cần nhập từng cái.
- **Vẽ hình nhanh và chính xác từ ảnh thực tế/mô phỏng:** Người dùng có thể chụp ảnh thực tế, hình mô phỏng hoặc vẽ tay nguệch ngoạc, tải lên App kèm prompt mô tả các điểm/trục tọa độ cần thiết. AI có khả năng "nhìn" ảnh và chuyển đổi thành code TikZ cực kỳ chuẩn xác.

2. HẠN CHẾ (TRUNG THỰC):
- Vì là AI nên đôi khi có thể "ngáo" nhẹ, vẽ sai tỷ lệ hoặc hiểu nhầm ý nếu prompt quá mập mờ.
- Các hình quá phức tạp hoặc không theo chuẩn toán học thông thường có thể cần người dùng tự tinh chỉnh thêm code.
- Việc xử lý hình ảnh/tài liệu đính kèm sẽ tốn thời gian hơn một chút so với văn bản thuần.

3. MẸO & LỜI KHUYÊN SỬ DỤNG HIỆU QUẢ (ĐỂ TIẾT KIỆM LƯỢT/API):
- Hãy gom nhiều yêu cầu vào một lần hỏi (ví dụ: "Vẽ đồ thị hàm số y=x^2 và bảng biến thiên của nó") thay vì hỏi lắt nhắt nhiều lần để tiết kiệm lượt sử dụng.
- Càng mô tả chi tiết (tọa độ, màu sắc, độ dày nét), AI càng vẽ chuẩn xác.
- Tận dụng tối đa "Thư viện của tôi" để lưu lại các hình đã ưng ý, lần sau chỉ cần gọi ra dùng lại hoặc sửa nhẹ.
- Sử dụng các checkbox (BBT, Đồ thị, Hình vẽ, TikZ) để ra lệnh nhanh mà không cần gõ nhiều.

PHONG CÁCH TRẢ LỜI:
- Hài hước, thân thiện, xưng "mình" hoặc "trợ lý" và gọi người dùng là "bạn" hoặc "thầy/cô".
- Trả lời ĐÚNG trọng tâm câu hỏi, KHÔNG tuôn một tràng dài liệt kê tất cả mọi thứ nếu người dùng chỉ hỏi 1 ý nhỏ.
- Tuy nhiên, nếu người dùng hỏi chung chung (ví dụ: "App này làm được gì?", "Hướng dẫn sử dụng", "Giới thiệu app"), bạn HÃY kể hết các tính năng, lưu ý, mẹo, và cả những hạn chế của app. Đặc biệt nhấn mạnh lời khuyên sử dụng hiệu quả (gom nhiều yêu cầu) để dùng được nhiều lượt cho một tài khoản.
- Trình bày rõ ràng, dùng markdown (in đậm, gạch đầu dòng) cho dễ đọc.

Câu hỏi của người dùng: "${question}"`;

        const response = await ai.models.generateContent({
            model: 'gemini-3.1-pro-preview',
            contents: systemPrompt,
        });

        return response.text?.trim() || "Xin lỗi, hiện tại mình đang hơi 'lag' một chút. Bạn thử hỏi lại sau nhé!";
    } catch (error) {
        console.error("Error getting help response:", error);
        return "Ối, có lỗi xảy ra rồi! Có thể là do API Key chưa được thiết lập đúng hoặc mạng đang chập chờn. Bạn kiểm tra lại giúp mình nhé!";
    }
};

export const getAiAssistance = async (prompt: string, images: ImagePart[], userLibrary?: Category, signal?: AbortSignal, isNoteEnabled?: boolean, isBbtNoFrame?: boolean): Promise<string> => {
    try {
        const ai = getGoogleGenAIClient();
        const templateLibrary = getTemplateLibraryAsString(userLibrary);
        
        const noteInstruction = isNoteEnabled 
            ? "BẮT BUỘC THÊM CHÚ THÍCH (GHI CHÚ): Chỉ cần chú thích tên chủ đề và tên các nhóm lệnh chính để phân chia bố cục (ví dụ: '% ĐỒ THỊ HÀM SỐ', '% 1. HỆ TRỤC TỌA ĐỘ', '% 2. ĐỒ THỊ VÀ TIỆM CẬN', '% 3. ĐÁNH DẤU VÀ GIÓNG ĐIỂM'). KHÔNG CẦN chú thích chi tiết cho từng dòng lệnh nhỏ."
            : "KHÔNG THÊM CHÚ THÍCH (GHI CHÚ): Chỉ xuất code TikZ thuần túy, tuyệt đối không thêm bất kỳ dòng chú thích (comment %) nào. BẮT BUỘC PHẢI TẮT/XÓA BỎ HOÀN TOÀN các chú thích phân chia bố cục. TUY NHIÊN, PHẢI SỬ DỤNG DÒNG TRẮNG (blank lines) để phân cách các môi trường, các nhóm lệnh chính (như hệ trục, đồ thị, đánh dấu điểm) để code nhìn mạch lạc, rõ ràng.";

        const finalStyleGuide = isBbtNoFrame
            ? USER_STYLE_GUIDE.replace(/nocadre=false/g, 'nocadre=true')
            : USER_STYLE_GUIDE;
            
        const finalTemplateLibrary = isBbtNoFrame
            ? templateLibrary.replace(/nocadre=false/g, 'nocadre=true')
            : templateLibrary;

        const fullPrompt = `Bạn là trợ lý AI chuyên vẽ hình TikZ cho giáo viên Toán (Thầy Tuấn).
        
        TÔI CẦN BẠN VẼ HÌNH ĐÚNG PHONG CÁCH CỦA TÔI. Đừng vẽ theo cách mặc định của bạn.
        
        QUY TRÌNH XỬ LÝ (BẮT BUỘC TUÂN THỦ):
        Bước 1: Kiểm tra xem hình vẽ yêu cầu có trong "THƯ VIỆN CỦA TÔI" không. Nếu có, HÃY LẤY CODE ĐÓ LÀM ƯU TIÊN CAO NHẤT và chỉnh sửa nhẹ nếu cần.
        Bước 2: Nếu không có trong thư viện của tôi, hãy tìm trong "THƯ VIỆN MẶC ĐỊNH" hoặc các nguồn khác.
        Bước 3: Nếu vẫn không có, hãy tự vẽ nhưng PHẢI HỌC PHONG CÁCH TỪ CÁC CODE MẪU BÊN DƯỚI. ĐẶC BIỆT LƯU Ý HỌC HỎI PHONG CÁCH "BẢNG BIẾN THIÊN 2" VÀ "BẢNG BIẾN THIÊN 3" (vẽ mũi tên thủ công bằng \\path và \\draw[-Stealth], tuân thủ quy tắc yshift).
        Bước 4: Tính toán ngầm (tọa độ, góc, tỷ lệ) trước khi xuất code để đảm bảo hình vẽ chuẩn, đẹp và tối ưu.
        Bước 5: BẢO TỒN NGUYÊN TRẠNG cấu trúc và nội dung: Khi vẽ hình, ảnh, bảng biến thiên, đồ thị từ dữ liệu gốc, PHẢI bảo tồn tuyệt đối hình gốc. Tuyệt đối KHÔNG ĐƯỢC THÊM, BỚT, hay thay đổi bất kỳ thành phần nào của hình gốc (đường nét, điểm, nhãn, dữ liệu, mũi tên, v.v.) TRỪ KHI tôi có yêu cầu rõ ràng về việc thêm/bớt.

        === STYLE GUIDE (QUY TẮC BẮT BUỘC) ===
        ${finalStyleGuide}

        === QUY TẮC CHÚ THÍCH CODE ===
        ${noteInstruction}

        === NGÂN HÀNG CODE MẪU (HỌC TỪ ĐÂY) ===
        ${finalTemplateLibrary}
        ========================================

        Yêu cầu vẽ hình: "${prompt}"

        Hướng dẫn xuất code:
        - BƯỚC QUAN TRỌNG: Trước khi xuất code TikZ, bạn PHẢI luôn tự kiểm tra đối chiếu (ví dụ: trong phần thinking) và đặt câu hỏi: "còn yêu cầu nào chưa được kiểm tra khắc phục không nhỉ?". Từ đó thực hiện kiểm tra 2 chiều, bổ sung, chỉnh sửa để khi code xuất ra chuẩn không cần chỉnh. Đảm bảo tuân thủ hết các quy tắc nhãn điểm, chữ d, phân số, tiệm cận...
        - Bắt đầu bằng \`\\begin{tikzpicture}[declare function={...}]\` (hoặc \`\\begin{circuitikz}\` nếu vẽ mạch điện).
        - Chỉ xuất code TikZ thô.
        - Không thêm markdown (\`\`\`).
        - NẾU bạn phải xuất toàn bộ cấu trúc tài liệu (\\documentclass), BẮT BUỘC PHẢI CÓ gói \`\\usepackage[utf8]{vietnam}\` trong phần preamble.
        - NẾU người dùng cung cấp ảnh/file đề thi/bài tập: BẮT BUỘC thêm một dòng chú thích ở ngay ĐẦU code TikZ ghi rõ hình đó thuộc "Phần nào? Câu mấy?" (dựa trên nội dung ảnh), ví dụ: "% code Hình chóp cụt - phần 1 câu 7." để người dùng dễ tra cứu.
        - ĐỐI VỚI MẠCH ĐIỆN (circuitikz): 
          + Mặc định vẽ theo chuẩn Châu Âu (european). Chỉ vẽ theo chuẩn Mỹ (american) nếu có yêu cầu rõ ràng.
          + BẮT BUỘC dùng cú pháp chuẩn của \`circuitikz\` (ví dụ: \`\\draw (0,0) to[R, l=$R_1$] (2,0);\`). Không dùng thư viện \`circuits.ee.IEC\` cũ của TikZ để tránh xung đột.
          + Chú ý với các linh kiện lưỡng cực (bipoles) như R (điện trở), L (cuộn cảm), C (tụ điện), pin (battery), nguồn (V, I) phải dùng cú pháp \`to[...]\`.
          + Nên bao bọc bằng \`\\begin{circuitikz} ... \\end{circuitikz}\`.`;

        const contents = {
            parts: [
                { text: fullPrompt },
                ...images
            ]
        };

        const responseStreamPromise = ai.models.generateContentStream({
            model: 'gemini-3.1-pro-preview',
            contents: contents,
            config: {
                thinkingConfig: { thinkingLevel: ThinkingLevel.HIGH }
            }
        });

        const abortPromise = new Promise<never>((_, reject) => {
            if (signal?.aborted) {
                reject(new Error('AbortError'));
            }
            signal?.addEventListener('abort', () => {
                reject(new Error('AbortError'));
            });
        });

        const responseStream = await Promise.race([responseStreamPromise, abortPromise]);

        let fullText = '';
        const iterator = responseStream[Symbol.asyncIterator]();
        
        while (true) {
            const result = await Promise.race([iterator.next(), abortPromise]);
            if (result.done) break;
            const chunk = result.value;
            if (chunk.text) {
                fullText += chunk.text;
            }
        }

        return fullText.trim();
    } catch (error) {
        console.error("Error getting AI assistance:", error);
        throw error;
    }
};