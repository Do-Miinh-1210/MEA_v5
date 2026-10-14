# 07 — NHÃN ĐIỂM, NHÃN ĐƯỜNG VÀ TRÁNH CHỒNG LẤN

---

## 7.1. NHÃN ĐIỂM TRONG HÌNH HỌC

### Cú pháp bắt buộc — `\foreach` 2 biến

```latex
\foreach \t/\goc in {A/135, B/-90, C/-30, D/210, S/90}{
  \draw[line width=0.6pt] (\t) circle (0.4pt) node[shift={(\goc:9pt)}]{$\t$};
}
```

**Trong đó:**
- `\t` — tên điểm (A, B, C, S…)
- `\goc` — góc đặt nhãn tính bằng **số đo độ** (không dùng above/below/left/right)
- `9pt` — khoảng cách từ điểm đến nhãn (bán kính)
- `circle (0.4pt)` — vẽ điểm đen rỗng bán kính 0.4pt

### Bảng góc tham khảo

| Vị trí mong muốn | Góc (độ) |
|---|---|
| Trên (trên đỉnh) | `90` |
| Dưới | `-90` hoặc `270` |
| Phải | `0` |
| Trái | `180` |
| Trên phải | `45` |
| Trên trái | `135` |
| Dưới phải | `-45` hoặc `315` |
| Dưới trái | `-135` hoặc `225` |

### Quy tắc chọn góc

1. Đặt nhãn về phía **NGOÀI** hình (tránh đè vào nét vẽ).
2. Đặt nhãn về phía **TRỐNG** (không có cạnh hoặc điểm khác).
3. Với đỉnh trên cùng → thường 90.
4. Với đỉnh dưới trái → thường 225.
5. Với đỉnh dưới phải → thường -45 hoặc 315.

---

## 7.2. ĐIỂM CÓ NHIỀU KÝ HIỆU GÓC VUÔNG

Khi tại một điểm cần đặt nhiều `pic right angle` (ví dụ điểm A trong hình chóp vuông SA⊥ABCD), nhãn bị đè:

```latex
% TÁCH RIÊNG điểm A ra ngoài \foreach
% Dùng bán kính lớn hơn (15pt thay vì 9pt):
\draw (A) circle (0.4pt) node[shift={(225:15pt)}, font=\normalsize]{$A$};

% Các điểm còn lại dùng foreach bình thường:
\foreach \t/\goc in {S/90, B/-90, C/-90, D/0, H/-90}{
  \draw[line width=0.6pt] (\t) circle (0.4pt) node[shift={(\goc:9pt)}]{$\t$};
}
```

---

## 7.3. NHÃN TRÊN ĐƯỜNG THẲNG VÀ ĐỒ THỊ

### Cú pháp chuẩn
```latex
node[pos=0.5, sloped, above]{$y = f(x)$}
```

**Giải thích:**
- `pos=0.5` — đặt tại điểm giữa đường (hoặc 0.4, 0.6 nếu vướng)
- `sloped` — nhãn xoay theo hướng đường
- `above` / `below` — phía trên hoặc dưới đường

### Chọn `pos` tự động
- Không có giao điểm → `pos=0.5`
- Có giao điểm gần giữa → `pos=0.4` hoặc `pos=0.6`
- Đường gần thẳng đứng → dùng `auto` thay vì `above`/`below`

```latex
\draw[line width=0.6pt] (A) -- (B)
  node[pos=0.5, sloped, above]{$a$};

\draw[line width=0.6pt] (C) -- (D)
  node[pos=0.6, sloped, below]{$b$};
```

### Nhãn đường cong (đồ thị)
```latex
% Ưu tiên dùng postaction (ẩn bằng comment):
\draw[line width=0.6pt, smooth, domain=...,
    % postaction={decoration={markings, mark=at position 0.8 with {
    %   \node[transform shape, sloped, above left]{$y=f(x)$};
    % }}, decorate}
]
  plot (\x, {f(\x)});
```

---

## 7.4. NHÃN TỌA ĐỘ TRÊN TRỤC

### Nhãn hoành độ (Ox)
```latex
\node[below] at (x1,0) {$x_1$};        % phổ biến nhất
\node[below, xshift=-8pt] at (x1,0) {$x_1$}; % dịch trái tránh chồng
\node[above] at (x1,0) {$x_1$};        % khi đồ thị ở dưới trục
```

### Nhãn tung độ (Oy)
```latex
\node[left] at (0,y1) {$y_1$};         % phổ biến nhất
\node[right] at (0,y1) {$y_1$};        % khi đồ thị ở bên trái
\node[left, yshift=8pt] at (0,y1) {$y_1$}; % dịch lên tránh chồng
```

### Kết hợp anchor được phép
```latex
above left    above right    below left    below right
above         below          left          right
```

> **TUYỆT ĐỐI KHÔNG** kết hợp `above below` (vô nghĩa).

---

## 7.5. NHÃN ĐIỂM TỌA ĐỘ — HỆ THỐNG ANCHOR

### Ưu tiên theo góc phần tư

| Góc phần tư | Điểm | Anchor ưu tiên |
|---|---|---|
| I (x>0, y>0) | Trên trục + đồ thị | `south west` → `south` → `west` |
| II (x<0, y>0) | | `south east` → `south` → `east` |
| III (x<0, y<0) | | `north east` → `north` → `east` |
| IV (x>0, y<0) | | `north west` → `north` → `west` |
| Gốc O (0,0) | | Chọn góc phần tư **trống nhất** |
| Gần tiệm cận đứng | | Tránh về phía tiệm cận |

```latex
% Ví dụ điểm A(2,3) ở góc phần tư I:
\node[anchor=south west] at (2,3) {$A(2;3)$};

% Điểm B(-1,2) ở góc phần tư II:
\node[anchor=south east] at (-1,2) {$B(-1;2)$};
```

---

## 7.6. CHUẨN HÓA ĐỘ CAO NHÃN (Baseline Alignment)

Khi nhãn nhỏ (như "O", "1") đứng cạnh nhãn to (như phân số), dùng `\vphantom` để cân bằng:

```latex
\node[anchor=south west] at (2,3) {$A\vphantom{(2;3)}$};
% \vphantom tạo không gian chiều dọc vô hình, cân bằng baseline
```

Hoặc dùng `text height` và `text depth`:
```latex
\node[text height=1.5ex, text depth=0.25ex] at (0,0) {$O$};
```

---

## 7.7. NHÃN VỊ TRÍ TIỆM CẬN

```latex
% Nhãn tiệm cận ngang (ở cuối đường):
\node[anchor=south east] at (xmax,{g(xmax)}) {$y=1$};

% Nhãn tiệm cận đứng (ở đầu đường):
\node[anchor=south west] at (x0,ymax) {$x=a$};

% Nếu nhãn bị chồng vào đồ thị:
\node[anchor=north east, xshift=-3pt] at (x0,ymax) {$x=a$};
```

---

## 7.8. CHECKLIST NHÃN TRƯỚC KHI XUẤT CODE

- [ ] Nhãn điểm trong `\foreach` dùng số đo độ, không dùng above/below/left/right?
- [ ] Nhãn trên đường có `sloped`?
- [ ] Điểm có nhiều ký hiệu góc đã tách riêng và dùng bán kính 15pt?
- [ ] Không kết hợp `above` và `below`?
- [ ] Nhãn cách đồ thị ≥ 2-3mm?
- [ ] Nhãn cách tiệm cận ≥ 3mm?
- [ ] Nhãn trên trục không chồng nhau (dùng xshift/yshift khi cần)?
- [ ] Nhãn O chọn đúng góc phần tư trống?
