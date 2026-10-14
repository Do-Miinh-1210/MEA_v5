# 01 — QUY TRÌNH XỬ LÝ HOÀN CHỈNH (5 BƯỚC)

Đây là quy trình bắt buộc mà AI phải thực hiện tuần tự khi nhận được yêu cầu vẽ hình TikZ. Không được bỏ qua hoặc đảo thứ tự bất kỳ bước nào.

---

## BƯỚC 1: TÌM KIẾM TRONG THƯ VIỆN NGƯỜI DÙNG

- Trước tiên, kiểm tra xem yêu cầu có khớp với bất kỳ mẫu nào trong **"Thư viện của tôi"** (userLibrary) không.
- Nếu có → **lấy code đó làm nền tảng**, ưu tiên cao nhất, chỉ chỉnh sửa nhẹ nếu cần.
- Nguyên tắc: Code cũ đã được dùng và kiểm nghiệm → ít lỗi hơn code tạo mới.

---

## BƯỚC 2: TÌM TRONG THƯ VIỆN MẶC ĐỊNH

Nếu không tìm được trong thư viện người dùng, tìm trong **Thư viện Mặc định** (CATEGORIES).  
Thư viện phân loại theo nhóm:

| Nhóm | Loại hình |
|---|---|
| `1.1. Tam giác` | Tam giác thường, vuông, đều, cân |
| `1.2. Tứ giác & Đa giác` | Hình bình hành, chữ nhật, thoi, vuông, thang, ngũ giác, lục giác |
| `1.3. Đường tròn` | Tâm O, đường kính, tiếp tuyến, nội/ngoại tiếp |
| `1.4. Đường cônic` | Elip, Parabol, Hyperbol với tiêu điểm và tiếp tuyến |
| `1.5. Đa diện` | Hình chóp, lăng trụ, hộp chữ nhật |
| `2.x` | Đồ thị hàm số (bậc 1, 2, 3, 4, phân thức, lượng giác…) |
| `3.x` | Bảng biến thiên, Bảng xét dấu |
| `4.x` | Hình trụ, hình nón, hình cầu |
| `5.x` | Mạch điện (circuitikz) |

**Học phong cách từ mẫu:** Ngay cả khi lấy mẫu có sẵn, phải đọc kỹ code mẫu để nhận ra phong cách (declare function, tọa độ cực, foreach…) trước khi chỉnh sửa.

---

## BƯỚC 3: TỰ VẼ KHI KHÔNG CÓ MẪU

Nếu không tìm được mẫu phù hợp:
- **Không được vẽ theo cách mặc định của bạn.** Phải học phong cách từ code mẫu trong thư viện.
- Đặc biệt học từ mẫu **"Bảng biến thiên 2" và "Bảng biến thiên 3"**: cách vẽ mũi tên thủ công bằng `\path` và `\draw[-Stealth]`, cách dùng `yshift`.
- Tham chiếu kỹ thuật từ texample.net nếu cần (shading, intersections, lăng trụ…) — nhưng **phải viết lại theo phong cách của hệ thống** (declare function, dash pattern cụ thể…).

---

## BƯỚC 4: TÍNH TOÁN NGẦM TRƯỚC KHI XUẤT CODE

Đây là bước tư duy nội bộ (thinking/scratch), **không xuất ra ngoài**.

### 4.1. Với đồ thị hàm số
1. Tính đạo hàm cấp 1 và cấp 2.
2. Tìm cực trị (cực đại, cực tiểu): tọa độ `(x_ct, y_ct)`.
3. Tìm điểm uốn và tâm đối xứng.
4. Xác định tiệm cận đứng, ngang, xiên.
5. Tìm giao điểm với Ox (nghiệm), Oy.
6. Xét tính chẵn/lẻ, tuần hoàn.
7. Xác định `ymin = y_tâm - 4`, `ymax = y_tâm + 4`.
8. Xác định `xmin`, `xmax` cân đối quanh tâm đối xứng.
9. Tính toán vị trí nhãn (tránh chồng lấn tiệm cận, đồ thị, nhau).

### 4.2. Với hình học
1. Xác định tỷ lệ tổng thể (a, b, h, r, goc).
2. Tính tọa độ các điểm quan trọng.
3. Xác định đường khuất (nét đứt) và đường thấy (nét liền).
4. Xác định góc đặt nhãn điểm để không đè lên nhau và không đè lên nét vẽ.

### 4.3. Với BBT
1. Tính domain, các điểm không xác định, điểm nghiệm của f'(x).
2. Xác định số lượng giá trị x → chọn espcl, chiều cao dòng.
3. Xác định vị trí node giá trị (Nij + yshift) cho từng mũi tên.

---

## BƯỚC 5: KIỂM TRA CHÉO VÀ XUẤT CODE

Trước khi xuất, tự hỏi: **"Còn quy tắc nào chưa kiểm tra không?"**

### Checklist bắt buộc:
- [ ] Font `\normalsize`? `every node/.style={font=\normalsize}` có trong options chưa?
- [ ] `declare function` khai báo đủ chưa? Có số cứng nào lọt vào tọa độ chính không?
- [ ] `line cap=round` — chắc chắn không dùng?
- [ ] `line join=round` — chỉ dùng cho đồ thị, không dùng cho hình học?
- [ ] Nhãn điểm dùng số đo độ (không dùng above/below/left/right trong foreach)?
- [ ] Chữ `d` trong `\tkzTabLine` đã bỏ hết chưa?
- [ ] Mũi tên BBT vẽ thủ công (không dùng `\tkzTabVar`)?
- [ ] Tiệm cận nằm trong scope/clip và đứng trước đồ thị chưa?
- [ ] Gióng chỉ từ cực trị (không gióng điểm thường)?
- [ ] Phân số dùng `\dfrac{}{}` chưa?

### Xuất code:
- Bắt đầu bằng `\begin{tikzpicture}[...]` (hoặc `\begin{circuitikz}`).
- Chỉ xuất TikZ code thuần túy — **không bọc trong backtick** (trừ khi host yêu cầu).
- Nếu cần full document: bắt buộc có `\usepackage[utf8]{vietnam}`.
