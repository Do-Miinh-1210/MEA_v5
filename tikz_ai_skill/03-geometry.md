# 03 — HÌNH HỌC PHẲNG VÀ KHÔNG GIAN 3D

---

## 3.1. ĐIỂM GỐC VÀ TỌA ĐỘ CỰC

### Nguyên tắc cốt lõi
- Luôn xác định **một điểm gốc tại `(0,0)`**.
- Tất cả điểm còn lại xác định bằng **tọa độ cực** và/hoặc **phép biến hình**.

### Tọa độ cực trên trục hoành (BẮT BUỘC)

| Thay vì | Phải dùng |
|---|---|
| `(a, 0)` với a > 0 | `(0:a)` |
| `(-a, 0)` với a > 0 | `(180:a)` |
| `(0, h)` | `(90:h)` |
| `(0, -h)` | `(-90:h)` hoặc `(270:h)` |

```latex
% SAI:
\path (0,0) coordinate (A) (5,0) coordinate (B) (-5,0) coordinate (C);

% ĐÚNG:
\begin{tikzpicture}[declare function={a=5;}]
\path (0,0) coordinate (A) (0:a) coordinate (B) (180:a) coordinate (C);
```

### Phép biến hình thường dùng
```latex
% Tịnh tiến (vector):
($(A) + (0:a)$)    % A dịch sang phải a đơn vị

% Điểm trung điểm:
($(A)!0.5!(B)$)    % trung điểm AB

% Điểm cách A một khoảng k theo hướng AB:
($(A)!k!(B)$)

% Phép đối xứng qua trục:
($2*(M) - (A)$)    % đối xứng A qua M

% Điểm vuông góc (rotate 90 độ):
($(A)!1!-90:(B)$)  % vuông góc với AB tại A, cùng chiều dài
```

---

## 3.2. KÝ HIỆU GÓC VUÔNG

**Luôn dùng `pic` với `right angle`**, không tự vẽ bằng `\draw rectangle`:

```latex
\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=C--A--B};
```

Thứ tự điểm: `right angle=C--ĐỈNH--B` (ĐỈNH là điểm có góc vuông).

```latex
% Ví dụ: góc vuông tại A trong tam giác ABC vuông tại A:
\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=B--A--C};
```

---

## 3.3. VÒNG LẶP `\foreach` VẼ ĐIỂM VÀ NHÃN

### Cú pháp chuẩn — 2 biến `\t` (tên) và `\goc` (góc nhãn)

```latex
\foreach \t/\goc in {A/135, B/-90, C/-30, D/210, S/90}{
  \draw[line width=0.6pt] (\t) circle (0.4pt) node[shift={(\goc:9pt)}]{$\t$};
}
```

### Quy tắc góc nhãn
- Dùng **số đo độ**. TUYỆT ĐỐI không dùng `above`, `below`, `left`, `right` trong mảng của `\foreach`.
- Chọn góc sao cho nhãn nằm về phía NGOÀI hình, không đè vào nét vẽ.
- Góc thường dùng: 90 (trên), -90 (dưới), 0 (phải), 180 (trái), 135 (trên trái), -45 (dưới phải), 225 (dưới trái), 45 (trên phải).

### Trường hợp điểm có nhiều ký hiệu góc
Khi tại một điểm cần vẽ nhiều ký hiệu góc vuông (ví dụ điểm A trong hình chóp SA⊥ABCD), nhãn dễ bị đè:
```latex
% Tách riêng điểm A ra ngoài foreach và dùng bán kính lớn hơn:
\draw (A) circle (0.4pt) node[shift={(225:15pt)}, font=\normalsize]{$A$};
\foreach \t/\goc in {S/90, B/-90, C/-90, D/0}{
  \draw[line width=0.6pt] (\t) circle (0.4pt) node[shift={(\goc:9pt)}]{$\t$};
}
```

---

## 3.4. HÌNH HỌC KHÔNG GIAN 3D

### Nguyên tắc nét khuất vs nét thấy
```latex
% Nét khuất (bị che khuất):
\draw[dashed, line width=0.4pt] (A) -- (B);

% Nét thấy:
\draw[line width=0.6pt] (C) -- (D);
```

### Đáy elip/tròn trong 3D — Chia 2 phần
```latex
% Phần khuất (nửa trên/dưới tùy góc nhìn):
\draw[dash pattern=on 2pt off 1.5pt, line width=0.6pt]
  plot[domain=0:180] ({r*cos(\x)}, {r*sin(\x)}, 0);

% Phần thấy:
\draw[line width=0.6pt]
  plot[domain=180:360] ({r*cos(\x)}, {r*sin(\x)}, 0);
```

### Hình hộp chữ nhật — Vị trí nhãn đặc biệt
- Điểm `C'`: góc **90 hoặc -25** độ
- Điểm `A`: góc **170** độ
```latex
\foreach \p/\goc in {
  A/170, B/-90, C/-90, D/0,
  A'/90, B'/90, C'/-25, D'/90
}{
  \draw (\p) circle (0.4pt) node[shift={(\goc:9pt)}]{$\p$};
}
```

### Dùng thư viện 3D
Khi cần phối cảnh 3D thực sự:
```latex
\usepackage{tikz-3dplot}
\tdplotsetmaincoords{70}{110}   % góc nhìn: elevation, azimuth
\begin{tikzpicture}[tdplot_main_coords, ...]
```

---

## 3.5. XẾP LỚP VẼ (LAYERING)

Luôn vẽ từ lớp dưới lên trên:

| Thứ tự | Lớp | Lệnh |
|---|---|---|
| 1 (dưới cùng) | Tô màu vùng (Fill/Shade) | `\fill`, `\shade` |
| 2 | Đường nét đứt (khuất) | `\draw[dashed]` |
| 3 | Đường nét liền (thấy) | `\draw[line width=0.6pt]` |
| 4 | Điểm (Points) | `\draw circle (0.4pt)`, `\fill circle (1pt)` |
| 5 (trên cùng) | Nhãn văn bản | `\node`, nhãn trong `\foreach` |

---

## 3.6. MẪU CODE NHANH — CÁC HÌNH PHỔ BIẾN

### Tam giác (bất kỳ)
```latex
\begin{tikzpicture}[declare function={a=5; b=3; goc=60;}, every node/.style={font=\normalsize}]
  \path
  (0,0) coordinate (A)
  (0:a) coordinate (B)
  (goc:b) coordinate (C)
  ;
  \draw[line width=0.6pt] (A)--(B)--(C)--cycle;
  \foreach \t/\g in {A/225, B/-45, C/90}{
    \draw[line width=0.6pt] (\t) circle (0.4pt) node[shift={(\g:9pt)}]{$\t$};
  }
\end{tikzpicture}
```

### Hình chóp S.ABCD (đáy hình bình hành)
```latex
\begin{tikzpicture}[declare function={a=5; b=3; h=3.5;}, every node/.style={font=\normalsize}]
  \path
  (0,0) coordinate (A)
  (0:a) coordinate (D)
  (-135:b) coordinate (B)
  ($(B)+(D)-(A)$) coordinate (C)
  (0,h) coordinate (S)
  ;
  \draw[dashed, line width=0.4pt] (B)--(A)--(D) (A)--(S);
  \draw[line width=0.6pt]
    (S)--(B)--(C)--(D)--cycle
    (S)--(C)
  ;
  \foreach \t/\g in {A/170, B/-90, C/-90, D/0, S/90}{
    \draw (\t) circle (0.4pt) node[shift={(\g:9pt)}]{$\t$};
  }
\end{tikzpicture}
```
