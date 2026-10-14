# 02 — CẤU TRÚC CODE, KHAI BÁO BIẾN VÀ FONT CHỮ

---

## 2.1. KHAI BÁO BIẾN VỚI `declare function` (QUAN TRỌNG NHẤT)

### Nguyên tắc cốt lõi
**KHÔNG BAO GIỜ** dùng số liệu cứng trực tiếp trong tọa độ các điểm chính.  
**BẮT BUỘC** dùng `declare function` ngay trong phần options của `\begin{tikzpicture}`.

### Cú pháp chuẩn

```latex
\begin{tikzpicture}[
  declare function={
    a=5;         % cạnh đáy
    h=4;         % chiều cao
    r=3;         % bán kính
    goc=60;      % góc (độ)
    xmot=sqrt(2)/2;   % biến phụ cho số cồng kềnh
    ymot=-3*sqrt(2);  % biến phụ
  },
  every node/.style={font=\normalsize}
]
```

### Khi nào dùng biến phụ?
Khi nghiệm hoặc tọa độ cồng kềnh (căn, phân số phức tạp), đặt biến trung gian:
```latex
declare function={
  xmot=(1+sqrt(5))/2;    % thay vì viết trực tiếp vào tọa độ
  ymot=xmot^2 - 3*xmot;
}
```

### Ví dụ ĐÚNG vs SAI

```latex
% SAI — số cứng trực tiếp:
\path (0,0) coordinate (A) (5,0) coordinate (B) (-45:3) coordinate (C);

% ĐÚNG — dùng declare function:
\begin{tikzpicture}[declare function={a=5; b=3; goc=-45;}]
\path (0,0) coordinate (A) (0:a) coordinate (B) (goc:b) coordinate (C);
```

---

## 2.2. FONT CHỮ — QUY TẮC `\normalsize`

### Nguyên tắc
- **TOÀN BỘ** hệ thống chỉ dùng một kích thước font duy nhất: `\normalsize`.
- Đặt một lần duy nhất vào options của `tikzpicture`: `every node/.style={font=\normalsize}`.
- **TUYỆT ĐỐI KHÔNG** dùng `\Large`, `\large`, `\small`, `\footnotesize` hay bất kỳ kích thước nào khác.
- **KHÔNG** bọc nội dung dòng BBT trong font size: `{$x$/0.7}` là đúng, `{{\large$x$}/0.7}` là sai.

### Template chuẩn cho từng loại hình

```latex
% ĐỒ THỊ HÀM SỐ (dùng line join=round):
\begin{tikzpicture}[>=stealth, line join=round, every node/.style={font=\normalsize},
  declare function={...}]

% HÌNH HỌC PHẲNG / KHÔNG GIAN (không dùng line join=round):
\begin{tikzpicture}[>=stealth, every node/.style={font=\normalsize},
  declare function={...}]

% BẢNG BIẾN THIÊN (cần thêm arrows.meta):
\begin{tikzpicture}[every node/.style={font=\normalsize}]
```

---

## 2.3. LINE JOIN VÀ LINE CAP

| Thuộc tính | Dùng cho | Không dùng cho |
|---|---|---|
| `line join=round` | Đồ thị hàm số, đường cong | Hình học phẳng, không gian, đa giác |
| `line cap=round` | **CẤM TUYỆT ĐỐI** — không dùng bao giờ | — |
| `line join=miter` (mặc định) | Hình học — cạnh vuông vắn | — |

---

## 2.4. ĐỘ DÀY NÉT CHUẨN

| Đối tượng | Độ dày | Lệnh |
|---|---|---|
| Trục tọa độ | `0.7pt` | `line width=0.7pt` |
| Nét đồ thị, tiệm cận, đường phụ | `0.6pt` | `line width=0.6pt` |
| Nét khuất (3D) | `0.4pt` dashed | `line width=0.4pt` |
| Điểm hình học | `0.6pt` (vòng tròn rỗng `0.4pt`) | `\draw[line width=0.6pt] (X) circle (0.4pt)` |
| Điểm đồ thị | `1pt` (chấm đặc) | `\fill (x,y) circle (1pt)` |
| Góc vuông | `0.6pt` | `pic[draw, line width=0.6pt, angle radius=5pt]` |
| Bảng biến thiên (đường kẻ gạch đôi) | `0.4pt` | `\draw[double distance=1pt, double=white, line width=0.4pt]` |

---

## 2.5. MŨI TÊN CHUẨN

**Luôn dùng `-Stealth`** cho tất cả mũi tên (trục, mũi tên biến thiên…).  
Khai báo trong options: `>=stealth` hoặc ghi trực tiếp `[-Stealth]`.

```latex
% Trục x:
\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below]{$x$};

% Mũi tên biến thiên trong BBT:
\draw[-Stealth] (A1) -- (A2);
```
