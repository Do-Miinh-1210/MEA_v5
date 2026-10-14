# 04 — ĐỒ THỊ HÀM SỐ, HỆ TRỤC VÀ TIỆM CẬN

---

## 4.1. QUY TRÌNH KHẢO SÁT HÀM SỐ (TÍNH TOÁN NGẦM)

Trước khi viết code, bắt buộc tính ngầm các giá trị sau:

| Bước | Công việc | Kết quả cần biết |
|---|---|---|
| 1 | Tính f'(x), f''(x) | Cực trị, điểm uốn |
| 2 | Giải f'(x) = 0 | x cực trị → y cực trị |
| 3 | Tiệm cận | Đứng: limx→a, Ngang: limx→±∞, Xiên: y=ax+b |
| 4 | Tâm đối xứng | Giao hai tiệm cận (I(x₀,y₀)) hoặc điểm uốn |
| 5 | Giao trục | Giao Ox (y=0), giao Oy (x=0) |
| 6 | xmin, xmax | Cân đối quanh tâm đối xứng |
| 7 | ymin, ymax | `y_tâm - 4` đến `y_tâm + 4` |

---

## 4.2. HỆ TRỤC TỌA ĐỘ (CHUẨN)

```latex
% 1. HỆ TRỤC TỌA ĐỘ
\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below]{$x$};
\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[below left]{$y$};
```

Mũi tên: `-Stealth` (không phải `->` hay `->`).  
Độ dày: `0.7pt`.  
Nhãn O: Chọn góc phần tư trống để đặt, tránh đè đồ thị.

```latex
\node[below left] at (0,0) {$O$};  % hoặc anchor=north east, v.v.
```

---

## 4.3. VÙNG CLIP VÀ VỊ TRÍ TIỆM CẬN

> **Nguyên tắc cốt lõi:** Tiệm cận PHẢI nằm trong scope clip, và PHẢI đứng TRƯỚC đồ thị.

```latex
\begin{scope}
  \clip (xmin,ymin) rectangle (xmax,ymax);

  % --- TIỆM CẬN --- (vẽ TRƯỚC đồ thị → nằm DƯỚI đồ thị)
  \draw[dashed, line width=0.6pt, domain=xmin:xmax,
      % postaction={decoration={markings, mark=at position 0.8 with
      %   {\node[transform shape, sloped, above left]{$y=k$};}}, decorate}
  ]
    plot (\x, {k});  % tiệm cận ngang

  \draw[dashed, line width=0.6pt]
    (x0,ymin) -- (x0,ymax);  % tiệm cận đứng

  % --- ĐỒ THỊ HÀM SỐ --- (vẽ SAU → nằm TRÊN tiệm cận)
  \draw[line width=0.6pt, smooth, samples=150, domain=...:...,
      % postaction={decoration={markings, mark=at position 0.8 with
      %   {\node[transform shape, sloped, above left]{$y=f(x)$};}}, decorate}
  ]
    plot (\x, {f(\x)});

\end{scope}
```

**Lưu ý:** Dòng `% postaction=...` phải để dưới dạng comment `%`. Người dùng tự bật khi cần nhãn tự động bám đường cong.

---

## 4.4. ĐÁNH DẤU VÀ GIÓNG ĐIỂM

```latex
% 3. ĐÁNH DẤU VÀ GIÓNG ĐIỂM
% Chỉ gióng từ CỰC TRỊ, KHÔNG gióng điểm thường
\draw[dashed, line width=0.6pt] (xct,0) -- (xct,yct) -- (0,yct);

% Đánh dấu chấm tại các điểm giao với trục
\fill (xct,0) circle (1pt);
\fill (0,yct) circle (1pt);
\fill (xct,yct) circle (1pt);

% Nhãn tại các điểm trục (tránh chồng lấn tiệm cận)
\node[below] at (xct,0) {$x_1$};
\node[left] at (0,yct) {$y_1$};
```

**Ngoại lệ (Tô miền diện tích):** Chỉ gióng từ cận tích phân xuống Ox, KHÔNG gióng sang Oy.

---

## 4.5. NHÃN VỊ TRÍ THÔNG MINH — TRÁNH CHỒNG LẤN

### Hệ thống anchor theo góc phần tư

| Vị trí điểm | Anchor ưu tiên | Ý nghĩa |
|---|---|---|
| Góc phần tư I (x>0, y>0) | `south west` → `south` → `west` | Nhãn về phía dưới-trái |
| Góc phần tư II (x<0, y>0) | `south east` → `south` → `east` | Nhãn về phía dưới-phải |
| Góc phần tư III (x<0, y<0) | `north east` → `north` → `east` | Nhãn về phía trên-phải |
| Góc phần tư IV (x>0, y<0) | `north west` → `north` → `west` | Nhãn về phía trên-trái |
| Trên Ox (y=0) | `north` nếu đồ thị ở dưới, `south` nếu ở trên | Tránh đè đồ thị |
| Gốc O | Chọn góc phần tư trống nhất | Tránh đè đồ thị |
| Gần tiệm cận | Tránh phía tiệm cận, cách >3mm | — |

### Khoảng cách tối thiểu
- Nhãn đến đồ thị: ≥ 2-3mm
- Nhãn đến tiệm cận: ≥ 3mm (không được đè lên đường dashed)
- Các nhãn với nhau: ≥ 4mm

### Điều chỉnh bằng shift/xshift/yshift
```latex
% Dịch nhãn tránh đè tiệm cận đứng:
\node[anchor=north west, xshift=3pt] at (x0,0) {$x_0$};

% Dịch nhãn tránh đè nhau trên trục:
\node[below, xshift=-8pt] at (a,0) {$a$};
\node[below, xshift=8pt] at (b,0) {$b$};
```

---

## 4.6. DECLARE FUNCTION CHO ĐỒ THỊ

```latex
% Ví dụ đầy đủ: Hàm phân thức y = (x-1)/(x-2)
\begin{tikzpicture}[
  line join=round,
  every node/.style={font=\normalsize},
  declare function={
    f(\x) = (\x-1)/(\x-2);  % hàm chính
    g(\x) = 1;               % tiệm cận ngang
    xmin=-1; xmax=5.5;
    ymin=-3; ymax=5;         % tâm đối xứng tại I(2,1) → 1±4
    x0=2;                    % tiệm cận đứng
  }
]
```

---

## 4.7. CÁC DẠNG HÀM SỐ PHỔ BIẾN

### Hàm bậc ba y = ax³ + bx² + cx + d
```latex
declare function={
  f(\x) = \x^3 - 3*\x + 2;
  xmin=-3; xmax=3;
  ymin=-2; ymax=6;  % tâm uốn tại I(0,2) → 2±4
}
```

### Hàm phân thức y = (ax+b)/(cx+d)
```latex
declare function={
  f(\x) = (2*\x+1)/(\x-1);
  g(\x) = 2;         % tiệm cận ngang
  x0=1;              % tiệm cận đứng
  y0=2;              % tâm đối xứng tại I(1,2)
  xmin=-2; xmax=5.5;
  ymin=-2; ymax=6;   % 2-4 đến 2+4
}
```

### Hàm bậc bốn y = ax⁴ + bx² + c
```latex
declare function={
  f(\x) = \x^4 - 8*\x^2 + 7;
  xmin=-4; xmax=4;
  ymin=-10; ymax=12;  % tâm tại (0,c)
}
```

### Hàm lượng giác y = a*sin(bx + c) + d
```latex
declare function={
  f(\x) = 2*sin(deg(\x)) + 1;
  xmin=-7; xmax=7;
  ymin=-2; ymax=4;
}
% Lưu ý: trong TikZ dùng deg(\x) khi \x tính bằng radian
% hoặc sin(\x r) — r nghĩa là radian
```

---

## 4.8. VÍ DỤ CODE ĐẦY ĐỦ — HÀM PHÂN THỨC

```latex
\begin{tikzpicture}[
  line join=round, every node/.style={font=\normalsize},
  declare function={
    f(\x) = (\x+1)/(\x-1);
    g(\x) = 1;
    x0=1; y0=1;
    xmin=-3; xmax=5.5;
    ymin=-3; ymax=5;
  }
]

% 1. HỆ TRỤC TỌA ĐỘ
\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below]{$x$};
\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[below left]{$y$};
\node[below left] at (0,0) {$O$};

\begin{scope}
  \clip (xmin,ymin) rectangle (xmax,ymax);

  % --- TIỆM CẬN ---
  \draw[dashed, line width=0.6pt, domain=xmin:xmax,
      % postaction={decoration={markings, mark=at position 0.9 with
      %   {\node[transform shape, sloped, above left]{$y=1$};}}, decorate}
  ]
    plot (\x, {g(\x)});

  \draw[dashed, line width=0.6pt] (x0,ymin) -- (x0,ymax);

  % --- ĐỒ THỊ HÀM SỐ ---
  \draw[line width=0.6pt, smooth, samples=150, domain=xmin:0.85,
      % postaction={decoration={markings, mark=at position 0.3 with
      %   {\node[transform shape, sloped, above left]{$y=\frac{x+1}{x-1}$};}}, decorate}
  ]
    plot (\x, {f(\x)});

  \draw[line width=0.6pt, smooth, samples=150, domain=1.15:xmax]
    plot (\x, {f(\x)});

\end{scope}

% 3. ĐÁNH DẤU VÀ GIÓNG ĐIỂM
\fill (0,{f(0)}) circle (1pt);
\node[anchor=north east] at (0,{f(0)}) {$-1$};

\node[anchor=south west] at (x0,ymax) {$x=1$};
\node[anchor=south east] at (xmax,{g(xmax)}) {$y=1$};

\end{tikzpicture}
```
