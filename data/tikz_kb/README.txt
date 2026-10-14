═══════════════════════════════════════════════════════════════════════════════
  KHO HÌNH VẼ TIKZ — TÀI LIỆU NGUỒN
═══════════════════════════════════════════════════════════════════════════════

Thư mục này chứa các MẪU HÌNH VẼ TikZ chuẩn dùng làm few-shot context khi AI
sinh hình. App đọc các file *.txt trong các thư mục con LÚC KHỞI ĐỘNG, không
nhúng cứng vào code → bạn có thể bổ sung mẫu mà KHÔNG cần build lại app.

───────────────────────────────────────────────────────────────────────────────
CẤU TRÚC THƯ MỤC
───────────────────────────────────────────────────────────────────────────────

  data/tikz_kb/
  ├── 01_plane_geometry/   ← hình học phẳng (tam giác, tứ giác, đường tròn…)
  ├── 02_solid_geometry/   ← hình học không gian (chóp, lăng trụ, trụ, nón…)
  ├── 03_graphs/           ← đồ thị hàm số (bậc 2/3/4, mũ, log, lượng giác)
  ├── 04_tables/           ← bảng biến thiên, bảng xét dấu
  ├── 05_charts/           ← biểu đồ cột, đường, tròn
  └── 06_misc/             ← trục số, miền nghiệm BPT, hệ trục toạ độ…

Bạn có thể tạo file mới ở BẤT KỲ thư mục nào — app tự quét đệ quy.

───────────────────────────────────────────────────────────────────────────────
ĐỊNH DẠNG MỘT FILE .txt
───────────────────────────────────────────────────────────────────────────────

Mỗi file gồm 1 hoặc nhiều khối TEMPLATE. Định dạng mỗi khối:

    === TEMPLATE: <Tên hiển thị trên menu Combobox> ===
    TAGS: <từ khoá phân loại, cách nhau dấu phẩy>
    KEYWORDS: <từ khoá tìm kiếm, cách nhau dấu phẩy — dùng để match đề bài>
    NOTES: <ghi chú ngắn về tính chất hình học cần lưu ý — tuỳ chọn>

    \begin{tikzpicture}[scale=1.5, thick]
      ...code TikZ đầy đủ...
    \end{tikzpicture}

    === TEMPLATE: <Tên kế tiếp> ===
    ...

Quy tắc:
  • Dòng `=== TEMPLATE: NAME ===` mở đầu một template — phải có CHÍNH XÁC ký tự
    `===` ở đầu/cuối + 1 dấu cách + `TEMPLATE:` + tên.
  • TAGS, KEYWORDS, NOTES là metadata — có thể thiếu cũng được, nhưng càng đầy
    đủ thì AI càng dễ chọn đúng template phù hợp với đề.
  • Phần code bắt đầu từ dòng `\begin{tikzpicture}` đến dòng `\end{tikzpicture}`.
  • Cho phép có dòng trống / comment `%` bên trong code.
  • Mỗi file có thể chứa N template — không giới hạn.

───────────────────────────────────────────────────────────────────────────────
TIPS VIẾT TEMPLATE CHẤT LƯỢNG CAO
───────────────────────────────────────────────────────────────────────────────

[Hình phẳng]
  • Ký hiệu góc vuông: dùng `\draw pic [draw, angle radius=3mm,
    angle eccentricity=1] {right angle = A--B--C};`
    KHÔNG dùng `\draw (B) rectangle ++(0.2,0.2);` vì rectangle không
    xoay theo hướng cạnh.
  • Ký hiệu góc thường: `\pic [draw, "$\alpha$", angle radius=6mm,
    angle eccentricity=1.3] {angle = B--A--C};`
  • Cạnh bằng nhau: dùng tick `decorate, decoration={markings,
    mark=at position 0.5 with {\draw (-2pt,-2pt)--(2pt,2pt);}}`
  • Đặt nhãn xa cạnh để tránh đè: `[label=above right:$A$]`

[Hình không gian]
  • Phép chiếu cabinet (gãy 30°, rút 0.5):
    `\begin{tikzpicture}[x={(1cm,0cm)}, y={(0.5cm,0.3cm)}, z={(0cm,1cm)}]`
  • Cạnh THẤY: `\draw[thick]`. Cạnh KHUẤT: `\draw[dashed, thick]`.
  • Đáy thường vẽ trước (kèm cạnh khuất); đỉnh + cạnh bên vẽ sau.
  • Kèm chân đường cao (H = trung điểm/tâm đáy) bằng nét đứt.

[Đồ thị]
  • LUÔN khai báo `samples=100` (hàm cong) hoặc `samples=200` (lượng giác).
  • Lượng giác: bọc `deg(x)`: `\addplot {sin(deg(x))};`.
  • Nhân tường minh: `2*x` không phải `2x`.
  • Parametric: `\addplot[variable=\t, domain=...] ({f(\t)}, \t);`

[BBT/Xét dấu] — phải đồng bộ với đồ thị nếu vẽ cả 2 (cùng TXĐ, nghiệm, cực trị).

───────────────────────────────────────────────────────────────────────────────
THÊM TEMPLATE MỚI
───────────────────────────────────────────────────────────────────────────────

  1. Mở file .txt phù hợp (hoặc tạo file mới trong thư mục con).
  2. Thêm khối `=== TEMPLATE: <Tên> ===` với metadata + code TikZ.
  3. Lưu file. KHỞI ĐỘNG LẠI APP.
  4. Template mới sẽ:
     • Xuất hiện trên Combobox "Mẫu" ở tab TikZ.
     • Được AI tham khảo khi mô tả đề khớp KEYWORDS.

Không cần build lại app.
