const fs = require('fs');

const data = `
% VÍ DỤ 1: DIỆN TÍCH HÌNH PHẲNG GIỮA HÀM BẬC 3 VÀ ĐƯỜNG THẲNG
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=1,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = \\x*\\x*\\x - 3*\\x;
 g(\\x) = \\x;
 xmin = -2.5; xmax = 2.5;
 ymin = -3.5; ymax = 3.5;
 x1 = -2; x2 = 0; x3 = 2;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 
 \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=blue!60]
 plot[domain=x1:x2, smooth] (\\x, {f(\\x)}) --
 plot[domain=x1:x2, smooth] (\\x, {g(\\x)}) -- cycle;
 
 \\fill[pattern={Lines[angle=135, distance=3pt, line width=0.3pt]}, pattern color=red!60]
 plot[domain=x2:x3, smooth] (\\x, {g(\\x)}) --
 plot[domain=x2:x3, smooth] (\\x, {f(\\x)}) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.85 with {\\node[transform shape, sloped, above] {$y=x^3-3x$};}}, decorate}
]
 plot (\\x, {f(\\x)});
 \\draw[line width=0.6pt, smooth, samples=2, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.15 with {\\node[transform shape, sloped, above] {$y=x$};}}, decorate}
]
 plot (\\x, {g(\\x)});
\\end{scope}
\\foreach \\i in {x1, x2, x3} \\fill (\\i,{g(\\i)}) circle (1.2pt);
\\draw[dashed, line width=0.6pt] (x1,0) node[above left] {$x_1$} -- (x1,{g(x1)});
\\draw[dashed, line width=0.6pt] (x3,0) node[below right] {$x_2$} -- (x3,{g(x3)});
\\end{tikzpicture}

% VÍ DỤ 2: DIỆN TÍCH DƯỚI ĐƯỜNG CONG SINE
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=1.5,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = sin(deg(\\x));
 xmin = -0.5; xmax = 3.5;
 ymin = -1.2; ymax = 1.2;
 a = 0; b = pi;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 
 \\fill[pattern={Lines[angle=60, distance=3.5pt, line width=0.3pt]}, pattern color=teal!70]
 plot[domain=a:b, smooth, samples=100] (\\x, {f(\\x)}) -- (b,0) -- (a,0) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.35 with {\\node[transform shape, sloped, above] {$y=\\sin x$};}}, decorate}
]
 plot (\\x, {f(\\x)});
\\end{scope}
\\fill (b,0) circle (0.4pt) node[below] {$\\pi$};
\\end{tikzpicture}

% VÍ DỤ 3: TÍNH ĐỐI XỨNG CỦA HÀM MŨ VÀ LOGARIT
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=1,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = exp(\\x);
 g(\\x) = ln(\\x);
 h(\\x) = \\x;
 xmin = -1.5; xmax = 4.5;
 ymin = -1.5; ymax = 4.5;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.7 with {\\node[transform shape, sloped, above] {$y=e^x$};}}, decorate}
]
 plot (\\x, {f(\\x)});
 \\draw[line width=0.6pt, smooth, samples=100, domain=0.01:xmax,
 postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, below] {$y=\\ln x$};}}, decorate}
]
 plot (\\x, {g(\\x)});
 \\draw[dashed, line width=0.5pt, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.9 with {\\node[transform shape, sloped, above] {$y=x$};}}, decorate}
]
 plot (\\x, {h(\\x)});
\\end{scope}
\\end{tikzpicture}

% VÍ DỤ 4: ĐỒ THỊ VÀ TIẾP TUYẾN
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=1.2,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = -0.5*\\x*\\x + 2*\\x + 1;
 df(\\x) = -\\x + 2;
 x0 = 3;
 y0 = f(x0);
 tangent(\\x) = df(x0)*(\\x - x0) + y0;
 xmin = -1.5; xmax = 5.5;
 ymin = -1; ymax = 4.5;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.25 with {\\node[transform shape, sloped, above] {$y=f(x)$};}}, decorate}
]
 plot (\\x, {f(\\x)});
 \\draw[line width=0.6pt, smooth, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, above] {$d$};}}, decorate}
]
 plot (\\x, {tangent(\\x)});
\\end{scope}
\\draw[dashed, line width=0.6pt] (x0,0) node[below] {$x_0$} -- (x0,y0) -- (0,y0) node[left] {$y_0$};
\\fill (x0,y0) circle (1.2pt) node[above right] {$M$};
\\end{tikzpicture}

% VÍ DỤ 5: DIỆN TÍCH GIỮA HAI PARABOL
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=1,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = -\\x*\\x + 4;
 g(\\x) = \\x*\\x - 2*\\x;
 xmin = -2.5; xmax = 3.5;
 ymin = -2.5; ymax = 5.5;
 a = -1; b = 2;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 \\fill[pattern={Lines[angle=60, distance=3pt, line width=0.3pt]}, pattern color=orange!70]
 plot[domain=a:b, smooth] (\\x, {f(\\x)}) --
 plot[domain=b:a, smooth] (\\x, {g(\\x)}) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.15 with {\\node[transform shape, sloped, above] {$y=-x^2+4$};}}, decorate}
]
 plot (\\x, {f(\\x)});
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.85 with {\\node[transform shape, sloped, below] {$y=x^2-2x$};}}, decorate}
]
 plot (\\x, {g(\\x)});
\\end{scope}
\\draw[dashed, line width=0.6pt] (a,0) node[below] {$a$} -- (a,{f(a)});
\\draw[dashed, line width=0.6pt] (b,0) node[below] {$b$} -- (b,{f(b)});
\\fill (a,{f(a)}) circle (1.2pt);
\\fill (b,{f(b)}) circle (1.2pt);
\\end{tikzpicture}

% VÍ DỤ 6: PARABOL VÀ TRỤC HOÀNH (Dạng cơ bản nhất)
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=1,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = -\\x*\\x + 4;
 xmin = -2.5; xmax = 2.5;
 ymin = -1; ymax = 5;
 a = -2; b = 2;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 
 \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=orange!70]
 plot[domain=a:b, smooth] (\\x, {f(\\x)}) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.35 with {\\node[transform shape, sloped, above] {$y=-x^2+4$};}}, decorate}
]
 plot (\\x, {f(\\x)});
\\end{scope}
\\foreach \\i in {a, b} \\fill (\\i,0) circle (1.2pt) node[below] {$\\i$};
\\end{tikzpicture}

% VÍ DỤ 7: HÀM BẬC 3 CẮT TRỤC HOÀNH (Phân tích dấu 2 miền)
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=0.8,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = \\x*\\x*\\x - 4*\\x;
 xmin = -2.5; xmax = 2.5;
 ymin = -4.5; ymax = 4.5;
 x1 = -2; x2 = 0; x3 = 2;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 
 \\fill[pattern={Lines[angle=60, distance=3pt, line width=0.3pt]}, pattern color=blue!60]
 plot[domain=x1:x2, smooth] (\\x, {f(\\x)}) -- cycle;
 
 \\fill[pattern={Lines[angle=120, distance=3pt, line width=0.3pt]}, pattern color=red!60]
 plot[domain=x2:x3, smooth] (\\x, {f(\\x)}) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.85 with {\\node[transform shape, sloped, above] {$y=x^3-4x$};}}, decorate}
]
 plot (\\x, {f(\\x)});
\\end{scope}
\\foreach \\i in {x1, x3} \\fill (\\i,0) circle (1.2pt) node[above] {$\\i$};
\\end{tikzpicture}

% VÍ DỤ 8: HAI ĐƯỜNG CONG CƠ BẢN
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=3,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = sqrt(abs(\\x));
 g(\\x) = \\x*\\x;
 xmin = -0.2; xmax = 1.3;
 ymin = -0.2; ymax = 1.3;
 a = 0; b = 1;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.5pt) node[shift={(-135:8pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 \\fill[pattern={Lines[angle=45, distance=2pt, line width=0.3pt]}, pattern color=purple!70]
 plot[domain=a:b, smooth, samples=100] (\\x, {f(\\x)}) --
 plot[domain=b:a, smooth, samples=100] (\\x, {g(\\x)}) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=100, domain=0:xmax,
 postaction={decoration={markings, mark=at position 0.6 with {\\node[transform shape, sloped, above] {$y=\\sqrt{x}$};}}, decorate}
]
 plot (\\x, {f(\\x)});
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, below right] {$y=x^2$};}}, decorate}
]
 plot (\\x, {g(\\x)});
\\end{scope}
\\draw[dashed, line width=0.4pt] (b,0) node[below] {$1$} -- (b,{f(b)}) -- (0,{f(b)}) node[left] {$1$};
\\fill (b,{f(b)}) circle (0.5pt);
\\end{tikzpicture}

% VÍ DỤ 9: HÀM LƯỢNG GIÁC GIAO NHAU
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=2,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = sin(deg(\\x));
 g(\\x) = cos(deg(\\x));
 xmin = -0.3; xmax = 1.8;
 ymin = -0.3; ymax = 1.3;
 x1 = 0; x2 = pi/4; x3 = pi/2;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.6pt) node[shift={(-135:8pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 \\fill[pattern={Lines[angle=60, distance=2.5pt, line width=0.3pt]}, pattern color=teal!70]
 plot[domain=x1:x2, smooth, samples=100] (\\x, {g(\\x)}) --
 plot[domain=x2:x1, smooth, samples=100] (\\x, {f(\\x)}) -- cycle;
 \\fill[pattern={Lines[angle=120, distance=2.5pt, line width=0.3pt]}, pattern color=cyan!70]
 plot[domain=x2:x3, smooth, samples=100] (\\x, {f(\\x)}) --
 plot[domain=x3:x2, smooth, samples=100] (\\x, {g(\\x)}) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.65 with {\\node[transform shape, sloped, above] {$y=\\sin x$};}}, decorate}
]
 plot (\\x, {f(\\x)});
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.15 with {\\node[transform shape, sloped, above] {$y=\\cos x$};}}, decorate}
]
 plot (\\x, {g(\\x)});
\\end{scope}
\\draw[dashed, line width=0.5pt] (x2,0) node[below] {$\\frac{\\pi}{4}$} -- (x2,{f(x2)});
\\draw[dashed, line width=0.5pt] (x3,0) node[below] {$\\frac{\\pi}{2}$} -- (x3,{f(x3)});
\\fill (x2,{f(x2)}) circle (0.6pt);
\\end{tikzpicture}

% VÍ DỤ 10: ỨNG DỤNG LOGARIT NÊ-PE
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=1.5,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = 1/\\x;
 xmin = -0.5; xmax = 3.5;
 ymin = -0.5; ymax = 2.5;
 a = 1; b = 2.718;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray!80]
 plot[domain=a:b, smooth, samples=100] (\\x, {f(\\x)}) -- (b,0) -- (a,0) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=200, domain=0.4:xmax,
 postaction={decoration={markings, mark=at position 0.15 with {\\node[transform shape, sloped, above] {$y=\\frac{1}{x}$};}}, decorate}
]
 plot (\\x, {f(\\x)});
\\end{scope}
\\draw[dashed, line width=0.6pt] (a,0) node[below] {$1$} -- (a,{f(a)});
\\draw[dashed, line width=0.6pt] (b,0) node[below] {$e$} -- (b,{f(b)});
\\fill (a,{f(a)}) circle (0.4pt);
\\fill (b,{f(b)}) circle (0.4pt);
\\end{tikzpicture}

% VÍ DỤ 11: HÀM SỐ MŨ
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=1.5,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = exp(\\x);
 g(\\x) = exp(-\\x);
 xmin = -1; xmax = 1.5;
 ymin = -0.5; ymax = 3.5;
 a = 0; b = 1;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 \\fill[pattern={Lines[angle=135, distance=3pt, line width=0.3pt]}, pattern color=magenta!70]
 plot[domain=a:b, smooth, samples=100] (\\x, {f(\\x)}) --
 plot[domain=b:a, smooth, samples=100] (\\x, {g(\\x)}) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.75 with {\\node[transform shape, sloped, above left] {$y=e^x$};}}, decorate}
]
 plot (\\x, {f(\\x)});
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.85 with {\\node[transform shape, sloped, above right] {$y=e^{-x}$};}}, decorate}
]
 plot (\\x, {g(\\x)});
\\end{scope}
\\draw[dashed, line width=0.6pt] (b,0) node[below] {$1$} -- (b,{f(b)});
\\fill (0,1) circle (0.4pt) node[left] {$1$};
\\end{tikzpicture}

% VÍ DỤ 12: ĐỒ THỊ, TIẾP TUYẾN VÀ TRỤC TUNG
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=1.5,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = \\x*\\x + 1;
 df(\\x) = 2*\\x;
 x0 = 1; y0 = 2;
 tangent(\\x) = df(x0)*(\\x - x0) + y0;
 xmin = -0.5; xmax = 2;
 ymin = -0.5; ymax = 3.5;
 a = 0; b = 1;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=violet!70]
 plot[domain=a:b, smooth, samples=100] (\\x, {f(\\x)}) --
 plot[domain=b:a, smooth, samples=100] (\\x, {tangent(\\x)}) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.65 with {\\node[transform shape, sloped, above] {$y=x^2+1$};}}, decorate}
]
 plot (\\x, {f(\\x)});
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.7 with {\\node[transform shape, sloped, below right] {$y=2x$};}}, decorate}
]
 plot (\\x, {tangent(\\x)});
\\end{scope}
\\draw[dashed, line width=0.6pt] (b,0) node[below] {$1$} -- (b,y0) -- (0,y0) node[left] {$2$};
\\fill (b,y0) circle (0.4pt);
\\fill (0,1) circle (0.4pt) node[above left] {$1$};
\\end{tikzpicture}

% VÍ DỤ 13: HÀM BẬC BỐN TRÙNG PHƯƠNG CẮT OX
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=0.8,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = -\\x*\\x*\\x*\\x + 5*\\x*\\x - 4;
 xmin = -2.5; xmax = 2.5;
 ymin = -5; ymax = 3.5;
 x1 = -2; x2 = -1; x3 = 1; x4 = 2;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-45:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=brown!80]
 plot[domain=x1:x2, smooth, samples=100] (\\x, {f(\\x)}) -- cycle;
 \\fill[pattern={Lines[angle=135, distance=3pt, line width=0.3pt]}, pattern color=olive!80]
 plot[domain=x2:x3, smooth, samples=100] (\\x, {f(\\x)}) -- cycle;
 \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=brown!80]
 plot[domain=x3:x4, smooth, samples=100] (\\x, {f(\\x)}) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=150, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.73 with {\\node[transform shape, sloped, below right] {$y=-x^4+5x^2-4$};}}, decorate}
]
 plot (\\x, {f(\\x)});
\\end{scope}
\\foreach \\i in {x1, x2, x3, x4} \\fill (\\i,0) circle (1.2pt) node[above right] {$\\i$};
\\end{tikzpicture}

% VÍ DỤ 14: HÀM CHỨA DẤU GIÁ TRỊ TUYỆT ĐỐI
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=0.8,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = abs(\\x*\\x - 1);
 g(\\x) = 3;
 xmin = -2.5; xmax = 2.5;
 ymin = -1; ymax = 4.5;
 a = -2; b = 2;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 \\fill[pattern={Lines[angle=60, distance=3pt, line width=0.3pt]}, pattern color=yellow!60!black]
 plot[domain=a:b, smooth, samples=300] (\\x, {f(\\x)}) -- (b,3) -- (a,3) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=300, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.27 with {\\node[transform shape, sloped, above] {$y=|x^2-1|$};}}, decorate}
]
 plot (\\x, {f(\\x)});
 \\draw[line width=0.6pt] (xmin,3) -- (xmax,3) node[above left] {$y=3$};
\\end{scope}
\\draw[dashed, line width=0.6pt] (a,0) node[below] {$-2$} -- (a,3);
\\draw[dashed, line width=0.6pt] (b,0) node[below] {$2$} -- (b,3);
\\fill (a,3) circle (1.2pt);
\\fill (b,3) circle (1.2pt);
\\end{tikzpicture}

% VÍ DỤ 15: HÌNH PHẲNG PHỨC TẠP GIỚI HẠN BỞI 3 ĐƯỜNG
\\begin{tikzpicture}[
 >=stealth, line join=round, scale=1.5,
 every node/.style={font=\\normalsize},
 declare function={
 f(\\x) = sqrt(abs(\\x));
 g(\\x) = \\x - 2;
 xmin = -0.5; xmax = 4.5;
 ymin = -1; ymax = 2.5;
 x1 = 0; x2 = 2; x3 = 4;
 }
]
\\draw[-Stealth, line width=0.7pt] (xmin,0) -- (xmax,0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0,ymin) -- (0,ymax) node[shift={(-6pt,-5pt)}] {$y$};
\\fill (0,0) circle (0.4pt) node[shift={(-135:12pt)}] {$O$};
\\begin{scope}
 \\clip (xmin,ymin) rectangle (xmax,ymax);
 % Tô miền 1: Dưới f(x) từ 0 đến 2
 \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=teal!70]
 plot[domain=x1:x2, smooth, samples=100] (\\x, {f(\\x)}) -- (x2,0) -- (x1,0) -- cycle;
 
 % Tô miền 2: Giữa f(x) và g(x) từ 2 đến 4
 \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=teal!70]
 plot[domain=x2:x3, smooth, samples=100] (\\x, {f(\\x)}) --
 plot[domain=x3:x2, smooth, samples=100] (\\x, {g(\\x)}) -- cycle;
 \\draw[line width=0.6pt, smooth, samples=200, domain=0:xmax,
 postaction={decoration={markings, mark=at position 0.5 with {\\node[transform shape, sloped, above] {$y=\\sqrt{x}$};}}, decorate}
]
 plot (\\x, {f(\\x)});
 \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
 postaction={decoration={markings, mark=at position 0.6 with {\\node[transform shape, sloped, below right] {$y=x-2$};}}, decorate}
]
 plot (\\x, {g(\\x)});
\\end{scope}
\\draw[dashed, line width=0.6pt] (x3,0) node[below] {$4$} -- (x3,{f(x3)});
\\fill (x2,0) circle (0.4pt) node[below right] {$2$};
\\fill (x3,{f(x3)}) circle (0.4pt);
\\end{tikzpicture}
`;

const examples = data.split(/% VÍ DỤ \d+:/).filter(Boolean);
const templates = examples.map((ex, index) => {
  const parts = ex.trim().split('\n');
  const title = (index + 1) + ". " + parts[0].trim();
  const code = parts.slice(1).join('\n').trim();
  return {
    id: `shading-${index + 1}`,
    title: title,
    description: title,
    code: code.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n')
  };
});

fs.writeFileSync('parsed_examples.json', JSON.stringify(templates, null, 2));
