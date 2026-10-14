# 10 — CODE MẪU CHUẨN THEO TỪNG LOẠI HÌNH

Các đoạn code này được trích trực tiếp từ thư viện mặc định của ứng dụng. Sử dụng làm tham chiếu để học phong cách và cú pháp chuẩn.

---

## 10.1. HÌNH PHẲNG CƠ BẢN

### Tam giác thường
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

### Hình bình hành
```latex
\begin{tikzpicture}[declare function={a=3; b=5; h=3.5; k=0.5;}, every node/.style={font=\normalsize}]
  \path
  (0,0) coordinate (A)
  (0:a) coordinate (B)
  (-110:h) coordinate (D)
  ($(D)+(B)-(A)$) coordinate (C)
  ;
  \draw[line width=0.6pt] (A)--(B)--(C)--(D)--cycle;
  \foreach \t/\g in {A/120, B/45, C/-30, D/210}{
    \draw[line width=0.6pt] (\t) circle (0.4pt) node[shift={(\g:9pt)}]{$\t$};
  }
\end{tikzpicture}
```

### Tứ giác nội tiếp đường tròn
```latex
\begin{tikzpicture}[declare function={r=3;}, line width=0.6pt, every node/.style={font=\normalsize}]
  \path
  (0,0) coordinate (O)
  (120:r) coordinate (A)
  (45:r) coordinate (B)
  (-30:r) coordinate (C)
  (210:r) coordinate (D)
  ;
  \draw (A)--(B)--(C)--(D)--cycle (O) circle (r);
  \foreach \t/\g in {A/120, B/45, C/-30, D/210, O/-90}{
    \draw[line width=0.6pt] (\t) circle (0.4pt) node[shift={(\g:9pt)}]{$\t$};
  }
\end{tikzpicture}
```

---

## 10.2. HÌNH KHÔNG GIAN (3D)

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

### Hình hộp chữ nhật
```latex
\begin{tikzpicture}[declare function={a=5; b=3; h=4;}, every node/.style={font=\normalsize}]
  \path
  (0:0) coordinate (A)
  (220:b) coordinate (B)
  (0:a) coordinate (D)
  ($(B)+(D)-(A)$) coordinate (C)
  ;
  \foreach \x in {A,B,C,D}{
    \path (\x)++(90:h) coordinate (\x');
  }
  \draw[dashed, line width=0.4pt] (A')--(A)--(B) (A)--(D);
  \draw[line width=0.6pt]
    (B')--(A')--(D')--(C')
    (D')--(D)--(C)
    (B)--(C)--(C')--(B')--cycle
  ;
  \foreach \p/\goc in {
    A/170, B/-90, C/-90, D/0,
    A'/90, B'/90, C'/-25, D'/90
  }{
    \draw (\p) circle (0.4pt) node[shift={(\goc:9pt)}]{$\p$};
  }
\end{tikzpicture}
```

---

## 10.3. ĐỒ THỊ HÀM SỐ

### Hàm phân thức y = (x+1)/(x-1)
```latex
\begin{tikzpicture}[
  line join=round, every node/.style={font=\normalsize},
  declare function={
    f(\x) = (\x+1)/(\x-1);
    g(\x) = 1;
    x0=1;
    xmin=-2; xmax=5.5;
    ymin=-3; ymax=5;
  }
]
\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below]{$x$};
\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[below left]{$y$};
\node[below left] at (0,0) {$O$};

\begin{scope}
  \clip (xmin,ymin) rectangle (xmax,ymax);

  % --- TIỆM CẬN ---
  \draw[dashed, line width=0.6pt, domain=xmin:xmax]
    plot (\x, {g(\x)});
  \draw[dashed, line width=0.6pt] (x0,ymin) -- (x0,ymax);

  % --- ĐỒ THỊ HÀM SỐ ---
  \draw[line width=0.6pt, smooth, samples=150, domain=xmin:0.85]
    plot (\x, {f(\x)});
  \draw[line width=0.6pt, smooth, samples=150, domain=1.15:xmax]
    plot (\x, {f(\x)});
\end{scope}

\fill (0,{f(0)}) circle (1pt);
\node[anchor=north east] at (0,{f(0)}) {$-1$};
\node[anchor=south west] at (x0,ymax) {$x=1$};
\node[anchor=south east] at (xmax,{g(xmax)}) {$y=1$};
\end{tikzpicture}
```

---

## 10.4. BẢNG BIẾN THIÊN

### BBT hàm bậc ba (2 cực trị, 4 giá trị x)
```latex
% code Bảng biến thiên
\begin{tikzpicture}[every node/.style={font=\normalsize}]

\tkzTabInit[nocadre=false, lgt=1.5, espcl=2.5, deltacl=0.6]
  {$x$/0.7, $f'(x)$/0.7, $f(x)$/2.5}%
  {$-\infty$, $-1$, $2$, $+\infty$}

\tkzTabLine{, +, 0, -,  , +, }

\path
  ([yshift=8pt]N13) node (A1){$-\infty$}
  ([yshift=-8pt]N22) node (A2){$\dfrac{4}{27}$}
  ([yshift=8pt]N33) node (A3){$-2$}
  ([yshift=-8pt]N42) node (A4){$+\infty$};

\foreach \i/\j in {1/2, 2/3, 3/4}{\draw[-Stealth](A\i)--(A\j);}

\end{tikzpicture}
```

### BXD bảng xét dấu
```latex
\begin{tikzpicture}[every node/.style={font=\normalsize}]

\tkzTabInit[nocadre=false, lgt=1.5, espcl=2.5, deltacl=0.6]
  {$x$/1, $f'(x)$/0.7}%
  {$-\infty$, $-2$, $3$, $+\infty$}

\tkzTabLine{, -, 0, +,  , +, }

\end{tikzpicture}
```

---

## 10.5. TÔ MIỀN DIỆN TÍCH

### Tô miền giới hạn bởi đồ thị và trục Ox
```latex
\begin{tikzpicture}[
  line join=round, every node/.style={font=\normalsize},
  declare function={
    f(\x) = \x^2 - 2*\x;
    a=0; b=2;
    xmin=-1; xmax=3.5;
    ymin=-1.5; ymax=3;
  }
]
\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below]{$x$};
\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[below left]{$y$};
\node[below left] at (0,0) {$O$};

\begin{scope}
  \clip (xmin,ymin) rectangle (xmax,ymax);

  % Tô miền S
  \fill[pattern={Lines[angle=45, distance=4pt, line width=0.3pt]},
        pattern color=gray!70,
        samples=150, domain=a:b]
    plot (\x, {f(\x)}) -- (b,0) -- (a,0) -- cycle;

  % --- ĐỒ THỊ HÀM SỐ ---
  \draw[line width=0.6pt, smooth, samples=150, domain=xmin:xmax]
    plot (\x, {f(\x)});
\end{scope}

\draw[dashed, line width=0.6pt] (b,{f(b)}) -- (b,0);
\fill (a,0) circle (1pt);
\fill (b,0) circle (1pt);
\node[below] at (a,0) {$0$};
\node[below] at (b,0) {$2$};
\end{tikzpicture}
```

---

## 10.6. HÌNH TRÒN VÀ ĐƯỜNG CONIC

### Đường tròn tâm O, tiếp tuyến
```latex
\begin{tikzpicture}[declare function={r=3;}, line width=0.6pt, every node/.style={font=\normalsize}]
  \path
  (0,0) coordinate (O)
  (-45:r) coordinate (A)
  ($(A)!1!-90:(O)$) coordinate (T)
  ($2*(A)-(T)$) coordinate (Th)
  ;
  \path pic[draw, angle radius=5pt]{right angle=O--A--T};
  \draw (O)--(A) (T)--(Th)
    let \p1=($(O)-(A)$) in (O) circle ({veclen(\x1,\y1)});
  \foreach \t/\g in {A/-90, O/90}{
    \draw[line width=0.6pt] (\t) circle (0.4pt) node[shift={(\g:9pt)}]{$\t$};
  }
\end{tikzpicture}
```

### Elip với tiêu điểm
```latex
\begin{tikzpicture}[
  declare function={a=2.5; b=2; goc=60; c=sqrt(a^2-b^2);},
  every node/.style={font=\normalsize}
]
  \path
  (goc:a and b) coordinate (M)
  (0:c) coordinate (F2)
  (180:c) coordinate (F1)
  ;
  \draw[dashed, line width=0.6pt] (F1) -- (M) -- (F2);
  \draw[line width=0.6pt] (0,0) ellipse (a and b);
  \foreach \p/\pos/\lab in {M/115/M, F2/-90/F_2, F1/-90/F_1}{
    \draw[line width=0.6pt] (\p) circle (0.4pt) node[shift={(\pos:9pt)}]{$\lab$};
  }
\end{tikzpicture}
```

---

## 10.7. MẠCH ĐIỆN (CIRCUITIKZ)

```latex
\begin{circuitikz}[european, every node/.style={font=\normalsize}]
  \draw
    (0,0) to[battery, l=$E$] (0,3)
    to[R, l=$R_1$] (3,3)
    to[R, l=$R_2$] (3,0)
    to (0,0)
  ;
  % Nhánh song song:
  \draw (3,3) to[C, l=$C$] (6,3) to[R, l=$R_3$] (6,0) -- (3,0);
\end{circuitikz}
```
