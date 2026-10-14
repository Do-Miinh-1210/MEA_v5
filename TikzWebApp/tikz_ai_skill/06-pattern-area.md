# 06 — TÔ MIỀN DIỆN TÍCH, PATTERN VÀ TRỤC SỐ

---

## 6.1. PATTERN — GẠCH CHÉO VÀ NỀN CHÌM

### Thư viện cần khai báo
```latex
\usetikzlibrary{patterns.meta}
```

### Cú pháp chuẩn (BẮT BUỘC)
```latex
pattern={Lines[angle=45, distance=4pt, line width=0.3pt]}, pattern color=gray!70
```

### Quy tắc chọn tham số

| Tham số | Giá trị | Điều kiện |
|---|---|---|
| `angle` | 30, 45, 60, 75, 120, 150 | **PHẢI là góc xiên** — CẤM 0, 90, 180, -90 |
| `distance` | `4pt` | 1-2 miền nghiệm |
| `distance` | `5pt` | 3 miền nghiệm trở lên |
| `line width` | `0.3pt` | Cố định — nét mảnh |
| `pattern color` | `gray!70` | Cố định |

### TUYỆT ĐỐI KHÔNG dùng
- `pattern=north west lines` (pattern cũ)
- `pattern color=black!70`

---

## 6.2. TÔ MIỀN DIỆN TÍCH TÍCH PHÂN

### Cấu trúc chuẩn (các thư viện cần)
```latex
\usetikzlibrary{arrows.meta, patterns.meta, decorations.markings}
```

### Declare function đầy đủ
```latex
\begin{tikzpicture}[
  line join=round, every node/.style={font=\normalsize},
  declare function={
    f(\x) = \x^2 - 2*\x;       % hàm số chính
    g(\x) = \x;                 % hàm thứ 2 (nếu có)
    a=0;                        % cận dưới
    b=3;                        % cận trên
    xmin=-1; xmax=4.5;
    ymin=-2; ymax=4;
  }
]
```

### Vẽ miền diện tích
```latex
\begin{scope}
  \clip (xmin,ymin) rectangle (xmax,ymax);

  % Tô miền giới hạn bởi hai đường (f trên, g dưới):
  \fill[pattern={Lines[angle=45, distance=4pt, line width=0.3pt]},
        pattern color=gray!70,
        domain=a:b, samples=150]
    plot (\x, {f(\x)}) -- (b,{g(b)}) -- cycle
    plot[domain=b:a] (\x, {g(\x)});

  % Hoặc dùng fillbetween (cần pgfplots.fillbetween):
  % \addplot[pattern=...] fill between [of=curveF and curveG];
\end{scope}
```

### Đường gióng (chỉ xuống Ox — KHÔNG sang Oy)
```latex
% Chỉ gióng xuống trục Ox từ cận tích phân và giao điểm giữa
\draw[dashed, line width=0.6pt] (a,{f(a)}) -- (a,0);
\draw[dashed, line width=0.6pt] (b,{f(b)}) -- (b,0);

% Đánh dấu điểm trên Ox (KHÔNG đánh trên Oy)
\fill (a,0) circle (1pt);
\fill (b,0) circle (1pt);

\node[below] at (a,0) {$a$};
\node[below] at (b,0) {$b$};
```

---

## 6.3. VÍ DỤ ĐẦY ĐỦ — TÔ MIỀN S GIỮA HAI ĐỒ THỊ

```latex
\begin{tikzpicture}[
  line join=round, every node/.style={font=\normalsize},
  declare function={
    f(\x) = -\x^2 + 4;
    g(\x) = \x + 2;
    a=-1; b=2;   % giao điểm của f và g
    xmin=-2.5; xmax=3.5;
    ymin=-1; ymax=5.5;
  }
]

% 1. HỆ TRỤC TỌA ĐỘ
\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below]{$x$};
\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[below left]{$y$};
\node[below left] at (0,0) {$O$};

\begin{scope}
  \clip (xmin,ymin) rectangle (xmax,ymax);

  % Tô miền S
  \fill[pattern={Lines[angle=45, distance=4pt, line width=0.3pt]},
        pattern color=gray!70,
        samples=150, domain=a:b]
    plot (\x, {f(\x)}) -- (b,{g(b)})
    -- plot[domain=b:a] (\x, {g(\x)}) -- cycle;

  % --- ĐỒ THỊ HÀM SỐ THÀNH PHẦN ---
  \draw[line width=0.6pt, smooth, samples=150, domain=xmin:xmax,
      % postaction={decoration={markings, mark=at position 0.85 with
      %   {\node[transform shape, sloped, above left]{$y=-x^2+4$};}}, decorate}
  ]
    plot (\x, {f(\x)});

  \draw[line width=0.6pt, smooth, samples=150, domain=xmin:xmax,
      % postaction={decoration={markings, mark=at position 0.85 with
      %   {\node[transform shape, sloped, above left]{$y=x+2$};}}, decorate}
  ]
    plot (\x, {g(\x)});

\end{scope}

% 3. ĐÁNH DẤU ĐIỂM
\draw[dashed, line width=0.6pt] (a,0) -- (a,{f(a)});
\draw[dashed, line width=0.6pt] (b,0) -- (b,{f(b)});

\fill (a,0) circle (1pt);
\fill (b,0) circle (1pt);
\fill (a,{f(a)}) circle (1pt);
\fill (b,{f(b)}) circle (1pt);

\node[below] at (a,0) {$-1$};
\node[below] at (b,0) {$2$};

% Nhãn miền S
\node at ({(a+b)/2}, {(f((a+b)/2)+g((a+b)/2))/2}) {$S$};

\end{tikzpicture}
```

---

## 6.4. BIỂU DIỄN KHOẢNG/ĐOẠN TRÊN TRỤC SỐ

### Nguyên tắc cốt lõi
- **TUYỆT ĐỐI KHÔNG** vẽ cung tròn hay arc để ký hiệu đầu khoảng.
- **BẮT BUỘC** dùng ký tự ngoặc trực tiếp trên bàn phím: `(`, `)`, `[`, `]`.

### Cú pháp chuẩn
```latex
\begin{tikzpicture}[declare function={a=1; b=4;}, every node/.style={font=\normalsize}]

% Trục số
\draw[-Stealth, line width=0.7pt] (-0.5,0) -- (5.5,0) node[below]{};

% Đánh dấu điểm
\fill (a,0) circle (1pt);
\fill (b,0) circle (1pt);

% Nhãn số
\node[below] at (a,0) {$a$};
\node[below] at (b,0) {$b$};

% Khoảng mở (a;b) — dùng ký tự ( và )
\node[above] at (a,0) {$($};
\node[above] at (b,0) {$)$};

% Đoạn đóng [a;b] — dùng ký tự [ và ]
\node[above] at (a,0) {$[$};
\node[above] at (b,0) {$]$};

% Nửa khoảng [a;b) — kết hợp
\node[above] at (a,0) {$[$};
\node[above] at (b,0) {$)$};

\end{tikzpicture}
```

### Biểu diễn nhiều khoảng (miền nghiệm bất phương trình)
```latex
% Pattern cho từng miền:
\fill[pattern={Lines[angle=45, distance=4pt, line width=0.3pt]},
      pattern color=gray!70]
  (a,0.05) rectangle (b,-0.05);
```

---

## 6.5. NHÃN TỰ ĐỘNG BÁM ĐƯỜNG CONG (COMMENT)

Tất cả nhãn tự động bám đường cong phải **ẩn bằng `%`** theo mẫu sau:

```latex
\draw[line width=0.6pt, smooth, samples=150, domain=xmin:xmax,
    % postaction={decoration={markings, mark=at position 0.8 with {
    %   \node[transform shape, sloped, above left]{$y=f(x)$};
    % }}, decorate}
]
  plot (\x, {f(\x)});
```

Khi người dùng muốn bật nhãn, họ chỉ cần xóa dấu `%` ở các dòng `postaction`.
