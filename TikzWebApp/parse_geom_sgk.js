import fs from 'fs';

const triCodes = [
    { title: "1. Tam giác thường", desc: "Tam giác thường",
      code: `\\begin{tikzpicture}[declare function={a=5; b=3;}]
  \\path
  (0,0) coordinate (B)
  (0:a) coordinate (C)
  (65:b) coordinate (A)
  ;
  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;
  \\foreach \\t/\\pos in {A/90, B/-90, C/-90}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
    { title: "2. Tam giác vuông cân tại A", desc: "Tam giác vuông cân tại A",
      code: `\\begin{tikzpicture}[declare function={r=3; k=0.5;}]
  \\path
  (90:r) coordinate (A)
  (180:r) coordinate (B)
  (0:r) coordinate (C)
  ;
  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;
  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=B--A--C};
  \\foreach \\x/\\y in {A/B, A/C}{
  \\path (\\x)--(\\y) node[pos=k, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};
  }
  \\foreach \\t/\\pos in {A/90, B/-90, C/-90}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "3. Tam giác tù tại A", desc: "Tam giác tù tại A",
code: `\\begin{tikzpicture}[declare function={r=3; }]
  \\path
  (110:r) coordinate (A)
  (180:r) coordinate (B)
  (0:r) coordinate (C)
  ;
  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;
  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=B--A--C};
  \\foreach \\t/\\pos in {A/90, B/-90, C/-90}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "4. Tam giác vuông tại A", desc: "Tam giác vuông tại A (hai cạnh góc vuông không bằng nhau)",
code: `\\begin{tikzpicture}[declare function={a=5; c=3;}]
  \\path
  (0,0) coordinate (A)
  (0:a) coordinate (B)
  (90:c) coordinate (C)
  ;
  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;
  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=B--A--C};
  \\foreach \\t/\\pos in {A/225, B/-45, C/135}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "5. Tam giác cân tại A", desc: "Tam giác cân tại A",
code: `\\begin{tikzpicture}[declare function={h=4.5; a=2.5; k=0.5;}]
  \\path
  (90:h) coordinate (A)
  (180:a) coordinate (B)
  (0:a) coordinate (C)
  ;
  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;
  \\foreach \\x/\\y in {A/B, A/C}{
  \\path (\\x)--(\\y) node[pos=k, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};
  }
  \\foreach \\t/\\pos in {A/90, B/-90, C/-90}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "6. Tam giác đều", desc: "Tam giác đều",
code: `\\begin{tikzpicture}[declare function={r=3;}]
  \\path
  (90:r) coordinate (A)
  (210:r) coordinate (B)
  (330:r) coordinate (C)
  ;
  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;
  \\foreach \\t/\\pos in {A/90, B/-90, C/-90}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "7. Đường trung tuyến AM", desc: "Đường trung tuyến AM",
code: `\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]
  \\path
  (0,0) coordinate (B)
  (0:a) coordinate (C)
  (50:b) coordinate (A)
  ($(B)!k!(C)$) coordinate (M)
  ;
  \\draw[line width=0.6pt] (A)--(M) (A)--(B)--(C)--cycle;
  \\foreach \\x/\\y in {B/M, M/C}{
  \\path (\\x)--(\\y) node[pos=k, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};
  }
  \\foreach \\t/\\pos in {A/90, B/-90, C/-90, M/-90}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "8. Đường cao AH", desc: "Đường cao AH",
code: `\\begin{tikzpicture}[declare function={a=5; b=3;}]
  \\path
  (0,0) coordinate (B)
  (0:a) coordinate (C)
  (50:b) coordinate (A)
  ($(B)!(A)!(C)$) coordinate (H)
  ;
  \\draw[line width=0.6pt] (A)--(H) (A)--(B)--(C)--cycle;
  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=C--H--A};
  \\foreach \\t/\\pos in {A/90, B/-90, C/-90, H/-90}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "9. Đường phân giác AD", desc: "Đường phân giác AD",
code: `\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]
  \\path
  (0,0) coordinate (B)
  (0:a) coordinate (C)
  (50:b) coordinate (A)
  ($(A)!1cm!(B)$) coordinate (Nt)
  ($(A)!1cm!(C)$) coordinate (Mt)
  ($(Mt)!k!(Nt)$) coordinate (Xt)
  (intersection of A--Xt and B--C) coordinate (D)
  ;
  \\draw[line width=0.6pt] (A)--(D) (A)--(B)--(C)--cycle;
  \\draw[line width=0.4pt, dashed] (Mt)--(Nt);
  \\path
  pic[draw, line width=0.6pt, angle radius=7pt]{angle=B--A--D}
  pic[draw, line width=0.6pt, angle radius=9pt]{angle=D--A--C}
  ;
  \\foreach \\t/\\pos in {A/90, B/-90, C/-90, D/-90}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "10. Đường trung bình MN", desc: "Đường trung bình MN",
code: `\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]
  \\path
  (0,0) coordinate (B)
  (0:a) coordinate (C)
  (50:b) coordinate (A)
  ($(A)!k!(B)$) coordinate (M)
  ($(A)!k!(C)$) coordinate (N)
  ;
  \\draw[line width=0.6pt] (M)--(N) (A)--(B)--(C)--cycle;
  \\foreach \\x/\\y in {A/M, M/B}{
  \\path (\\x)--(\\y) node[pos=0.5, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};
  }
  \\foreach \\x/\\y in {A/N, N/C}{
  \\path (\\x)--(\\y) node[pos=0.5, sloped]{
  \\tikz{
  \\draw[line width=0.6pt, shift={(-1pt,0)}] (-90:1.5pt)--(90:1.5pt);
  \\draw[line width=0.6pt, shift={(1pt,0)}] (-90:1.5pt)--(90:1.5pt);
  }
  };
  }
  \\foreach \\t/\\pos in {A/90, B/-90, C/-90, M/180, N/0}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "11. Trọng tâm G", desc: "Trọng tâm G",
code: `\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]
  \\path
  (0,0) coordinate (B)
  (0:a) coordinate (C)
  (70:b) coordinate (A)
  ($(A)!k!(B)$) coordinate (D)
  ($(B)!k!(C)$) coordinate (E)
  ($(C)!k!(A)$) coordinate (F)
  (intersection of A--E and B--F) coordinate (G)
  ;
  \\draw[line width=0.6pt] (A)--(E) (B)--(F) (C)--(D) (A)--(B)--(C)--cycle;
  \\draw[line width=0.4pt, dashed] (C)--(D);
  \\foreach \\x/\\y in {A/D, D/B}{
  \\path (\\x)--(\\y) node[pos=0.5, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};
  }
  \\foreach \\x/\\y in {B/E, E/C}{
  \\path (\\x)--(\\y) node[pos=0.5, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};
  }
  \\foreach \\x/\\y in {C/F, F/A}{
  \\path (\\x)--(\\y) node[pos=0.5, sloped]{
  \\tikz{
  \\draw[line width=0.6pt, shift={(-1pt,0)}] (-90:1.5pt)--(90:1.5pt);
  \\draw[line width=0.6pt, shift={(1pt,0)}] (-90:1.5pt)--(90:1.5pt);
  }
  };
  }
  \\foreach \\t/\\pos in {A/90, B/-120, C/-60, G/60, D/150, E/-90, F/60}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "12. Trực tâm H", desc: "Trực tâm H",
code: `\\begin{tikzpicture}[declare function={a=5; b=3;}]
  \\path
  (0,0) coordinate (B)
  (0:a) coordinate (C)
  (65:b) coordinate (A)
  ($(A)!(C)!(B)$) coordinate (D)
  ($(B)!(A)!(C)$) coordinate (E)
  ($(C)!(B)!(A)$) coordinate (F)
  (intersection of A--E and B--F) coordinate (H)
  ;
  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;
  \\draw[line width=0.4pt, dashed] (A)--(E) (B)--(F) (C)--(D);
  \\foreach \\x/\\y/\\z in {C/E/A, B/F/C, B/D/C}{
  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=\\x--\\y--\\z};
  }
  \\foreach \\t/\\pos in {A/90, B/-120, C/-60, H/5, D/150, E/-90, F/60}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "13. Đường tròn ngoại tiếp (tâm O)", desc: "Đường tròn ngoại tiếp",
code: `\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]
  \\path
  (0,0) coordinate (B)
  (0:a) coordinate (C)
  (70:b) coordinate (A)
  ;
  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;
  \\begin{scope}[overlay]
  \\path
  ($(A)!k!(B)$) coordinate (Nt)
  ($(Nt)!1!90:(A)$) coordinate (Xt)
  ($(B)!k!(C)$) coordinate (Mt)
  ($(Mt)!1!90:(B)$) coordinate (Yt)
  (intersection of Nt--Xt and Mt--Yt) coordinate (O)
  ;
  \\end{scope}
  \\draw[line width=0.4pt, dashed] (Nt)--(Xt) (Mt)--(Yt);
  \\draw[line width=0.6pt] let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)});
  \\foreach \\t/\\pos in {A/90, B/-120, C/-60, O/-90}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`},
{ title: "14. Đường tròn nội tiếp (tâm I)", desc: "Đường tròn nội tiếp",
code: `\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5; t=0.5; m=1cm;}]
  \\path
  (0,0) coordinate (B)
  (0:a) coordinate (C)
  (70:b) coordinate (A)
  ($(A)!m!(B)$) coordinate (Nt)
  ($(A)!m!(C)$) coordinate (Mt)
  ($(Mt)!k!(Nt)$) coordinate (Xt)
  ($(B)!m!(C)$) coordinate (Kt)
  ($(B)!m!(A)$) coordinate (Lt)
  ($(Kt)!t!(Lt)$) coordinate (Yt)
  (intersection of A--Xt and B--Yt) coordinate (I)
  ($(A)!(I)!(B)$) coordinate (D)
  ($(B)!(I)!(C)$) coordinate (E)
  ($(C)!(I)!(A)$) coordinate (F)
  ;
  \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;
  \\draw[line width=0.4pt, dashed] (A)--(Xt) (B)--(Yt);
  \\draw[line width=0.6pt] let \\p1=($(I)-(D)$) in (I) circle ({veclen(\\x1,\\y1)});
  \\draw[line width=0.4pt, dashed] (I)--(D);
  \\foreach \\t/\\pos in {A/90, B/-120, C/-60, I/-60, D/150, E/-90, F/60}{
  \\draw[line width=0.6pt] (\\t) circle (0.4pt) node[shift={(\\pos:9pt)}] {$\\t$};
  }
\\end{tikzpicture}`}
];

const polyCodes = [
    { title: "1. Tứ giác lồi nội tiếp (bất kỳ)", desc: "Tứ giác lồi nội tiếp đường tròn",
      code: `\\begin{tikzpicture}[declare function={r=3;}]
  \\path
  (120:r) coordinate (A)
  (45:r) coordinate (B)
  (-30:r) coordinate (C)
  (210:r) coordinate (D)
  ;
  \\draw (A)--(B)--(C)--(D)--cycle;
  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "2. Hình bình hành (tổng quát)", desc: "Hình bình hành",
      code: `\\begin{tikzpicture}[declare function={a=3; b=5; h=3.5; k=0.5;}]
  \\path
  (0,0) coordinate (A)
  (0:a) coordinate (B)
  (-110:h) coordinate (D)
  ($(D)+(B)-(A)$) coordinate (C)
  ;
  \\draw (A)--(B)--(C)--(D)--cycle;
  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "3. Hình thang cân", desc: "Hình thang cân",
      code: `\\begin{tikzpicture}[declare function={a=3; h=3.5; goc=-130; k=0.5;}]
  \\path
  (0,0) coordinate (A)
  (0:a) coordinate (B)
  (goc:h) coordinate (D)
  ($(B)+({-180-goc}:h)$) coordinate (C)
  ;
  \\foreach \\x/\\y in {A/D, B/C}{
  \\path (\\x)--(\\y) node[pos=k, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};
  }
  \\draw (A)--(B)--(C)--(D)--cycle;
  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "4. Hình thang vuông", desc: "Hình thang vuông",
      code: `\\begin{tikzpicture}[declare function={a=3.5; h=3; goc=-60; c=abs(h/sin(goc)); k=1;}]
  \\path
  (0,0) coordinate (A)
  (0:a) coordinate (B)
  (-90:h) coordinate (D)
  ($(B)+(goc:c)$) coordinate (C)
  ;
  \\foreach \\x/\\y/\\z in {D/A/B, C/D/A}{
  \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=\\x--\\y--\\z};
  }
  \\draw (A)--(B)--(C)--(D)--cycle;
  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "5. Hình bình hành (cách dựng bằng vectơ)", desc: "Hình bình hành",
      code: `\\begin{tikzpicture}[declare function={a=5; b=3;}]
  \\path
  (0,0) coordinate (A)
  (0:a) coordinate (B)
  (-120:b) coordinate (D)
  ($(D)+(B)-(A)$) coordinate (C)
  ;
  \\draw (A)--(B)--(C)--(D)--cycle;
  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "6. Hình chữ nhật", desc: "Hình chữ nhật",
      code: `\\begin{tikzpicture}[declare function={a=5; b=3;}]
  \\path
  (0,0) coordinate (A)
  (0:a) coordinate (B)
  (-90:b) coordinate (D)
  ($(D)+(B)-(A)$) coordinate (C)
  ;
  \\draw (A)--(B)--(C)--(D)--cycle;
  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "7. Hình vuông (có tâm O là giao đường chéo)", desc: "Hình vuông",
      code: `\\begin{tikzpicture}[declare function={a=5; k=0.5;}]
  \\path
  (0,0) coordinate (A)
  (0:a) coordinate (B)
  (-90:a) coordinate (D)
  ($(D)+(B)-(A)$) coordinate (C)
  ($(A)!k!(C)$) coordinate (O)
  ;
  \\draw (A)--(B)--(C)--(D)--cycle;
  \\foreach \\t/\\g in {A/135, B/45, C/-45, D/225}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "8. Hình thoi (các đỉnh trên trục tọa độ)", desc: "Hình thoi",
      code: `\\begin{tikzpicture}[declare function={a=5; b=3; k=0.5;}]
  \\path
  (90:{0.5*b}) coordinate (A)
  (0:{0.5*a}) coordinate (B)
  (270:{0.5*b}) coordinate (C)
  (180:{0.5*a}) coordinate (D)
  ;
  \\draw (A)--(B)--(C)--(D)--cycle;
  \\foreach \\t/\\g in {A/90, B/0, C/-90, D/180}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "9. Ngũ giác đều", desc: "Ngũ giác đều",
      code: `\\begin{tikzpicture}[declare function={r=3; goc=360/5;}]
  \\path
  (90:r) coordinate (A)
  ({90+goc}:r) coordinate (B)
  ({90+2*goc}:r) coordinate (C)
  ({90+3*goc}:r) coordinate (D)
  ({90+4*goc}:r) coordinate (E)
  ;
  \\draw (A)--(B)--(C)--(D)--(E)--cycle;
  \\foreach[count=\\i] \\t in {A,B,C,D,E}{
  \\draw (\\t) circle (0.4pt) node[shift={({90-goc+goc*\\i}:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "10. Lục giác đều", desc: "Lục giác đều (goc=60°)",
      code: `\\begin{tikzpicture}[declare function={r=3; goc=60;}]
  \\path
  (90:r) coordinate (A)
  ({90+goc}:r) coordinate (B)
  ({90+2*goc}:r) coordinate (C)
  ({90+3*goc}:r) coordinate (D)
  ({90+4*goc}:r) coordinate (E)
  ({90+5*goc}:r) coordinate (F)
  ;
  \\draw (A)--(B)--(C)--(D)--(E)--(F)--cycle;
  \\foreach[count=\\i] \\t in {A,B,C,D,E,F}{
  \\draw (\\t) circle (0.4pt) node[shift={({90-goc+goc*\\i}:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "11. Ngôi sao 5 cánh", desc: "Ngôi sao 5 cánh",
      code: `\\begin{tikzpicture}[declare function={r=3; goc=360/5;}]
  \\path
  (90:r) coordinate (A)
  ({90+goc}:r) coordinate (B)
  ({90+2*goc}:r) coordinate (C)
  ({90+3*goc}:r) coordinate (D)
  ({90+4*goc}:r) coordinate (E)
  ;
  \\draw (A)--(C)--(E)--(B)--(D)--cycle;
  \\foreach[count=\\i] \\t in {A,B,C,D,E}{
  \\draw (\\t) circle (0.4pt) node[shift={({90-goc+goc*\\i}:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`}
];

const circleCodes = [
    { title: "1. Đường tròn tâm O", desc: "Đường tròn tâm O bán kính r",
      code: `\\begin{tikzpicture}[declare function={r=3;}, line width=0.6pt]
  \\path
  (0,0) coordinate (O)
  (45:r) coordinate (A)
  ;
  \\draw (O)--(A) node[above, pos=0.5, sloped, font=\\normalsize]{$r$};
  \\draw let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)});
  \\foreach \\t/\\g in {A/45, O/-90}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "2. Đường tròn đường kính AB", desc: "Tâm O là trung điểm",
      code: `\\begin{tikzpicture}[declare function={r=3; k=0.5;}, line width=0.6pt]
  \\path
  (180:r) coordinate (A)
  (0:r) coordinate (B)
  ($(A)!k!(B)$) coordinate (O)
  ;
  \\draw (B)--(A);
  \\draw let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)});
  \\foreach \\t/\\g in {A/180, B/0, O/-90}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "3. Tiếp tuyến tại A của đường tròn", desc: "Tiếp tuyến tại 1 điểm",
      code: `\\begin{tikzpicture}[declare function={r=3;}, line width=0.6pt]
  \\path
  (0,0) coordinate (O)
  (-45:r) coordinate (A)
  ($(A)!1!-90:(O)$) coordinate (T)
  ($2*(A)-(T)$) coordinate (Th)
  ;
  \\path pic[draw, angle radius=5pt]{right angle=O--A--T};
  \\draw
  (O)--(A)
  (T)--(Th)
  let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)})
  ;
  \\foreach \\t/\\g in {A/-90, O/90}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "4. Hình thoi nội tiếp đường tròn", desc: "Tứ giác đối xứng",
      code: `\\begin{tikzpicture}[declare function={r=3; goc=55; k=1;}, line width=0.6pt]
  \\path
  (0,0) coordinate (O)
  (goc:r) coordinate (A)
  (-goc:r) coordinate (B)
  ;
  \\begin{scope}[overlay]
  \\path
  ($(A)!k!-90:(O)$) coordinate (OA)
  ($(B)!k!-90:(O)$) coordinate (OB)
  (intersection of A--OA and B--OB) coordinate (S)
  ;
  \\end{scope}
  \\path
  pic[draw, angle radius=5pt]{right angle=O--A--S}
  pic[draw, angle radius=5pt]{right angle=O--B--S}
  ;
  \\draw
  (O)--(A)--(S)--(B)--cycle
  let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)})
  ;
  \\foreach \\t/\\g in {A/goc, B/-goc, S/0, O/135}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "5. Nửa đường tròn đường kính AB", desc: "Nửa đường tròn",
      code: `\\begin{tikzpicture}[declare function={r=3;}, line width=0.6pt]
  \\path
  (0,0) coordinate (O)
  (180:r) coordinate (A)
  (0:r) coordinate (B)
  ;
  \\draw (B) arc (0:180:r)--cycle;
  \\foreach \\t/\\g in {A/180, B/0, O/-90}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "6. Hình thang cân nội tiếp", desc: "Nội tiếp nửa đường tròn",
      code: `\\begin{tikzpicture}[declare function={r=3; k=1;}, line width=0.6pt]
  \\path
  (0,0) coordinate (O)
  (180:r) coordinate (A)
  (0:r) coordinate (B)
  (65:r) coordinate (C)
  ;
  \\begin{scope}[overlay]
  \\path
  ($(A)!k!-90:(O)$) coordinate (OA)
  ($(B)!k!-90:(O)$) coordinate (OB)
  ($(C)!k!-90:(O)$) coordinate (OC)
  (intersection of A--OA and C--OC) coordinate (M)
  (intersection of B--OB and C--OC) coordinate (N)
  ;
  \\end{scope}
  \\draw
  (A)--(M)--(N)--(B)--cycle
  (B) arc (0:180:r)
  ;
  \\foreach \\t/\\g in {A/180, B/0, O/-90, M/180, N/0, C/goc}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "7. Tứ giác lồi nội tiếp đường tròn", desc: "Tứ giác nội tiếp",
      code: `\\begin{tikzpicture}[declare function={r=3;}, line width=0.6pt]
  \\path
  (0,0) coordinate (O)
  (120:r) coordinate (A)
  (45:r) coordinate (B)
  (-30:r) coordinate (C)
  (210:r) coordinate (D)
  ;
  \\draw
  (A)--(B)--(C)--(D)--cycle
  (O) circle (r)
  ;
  \\foreach \\t/\\g in {A/120, B/45, C/-30, D/210, O/-90}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "8. Tứ giác ngoại tiếp đường tròn", desc: "Các cạnh tiếp xúc",
      code: `\\begin{tikzpicture}[declare function={r=2.5; k=1;}, line width=0.6pt]
  \\path
  (0,0) coordinate (O)
  (-90:r) coordinate (M)
  (75:r) coordinate (N)
  (25:r) coordinate (P)
  (155:r) coordinate (Q)
  ;
  \\begin{scope}[overlay]
  \\path
  ($(M)!k!-90:(O)$) coordinate (AB)
  ($(N)!k!-90:(O)$) coordinate (CD)
  ($(P)!k!-90:(O)$) coordinate (BC)
  ($(Q)!k!-90:(O)$) coordinate (AD)
  (intersection of AB--M and Q--AD) coordinate (A)
  (intersection of AB--M and P--BC) coordinate (B)
  (intersection of CD--N and Q--AD) coordinate (D)
  (intersection of CD--N and P--BC) coordinate (C)
  ;
  \\end{scope}
  \\draw
  (A)--(B)--(C)--(D)--cycle
  (O) circle (r)
  ;
  \\foreach \\t/\\g in {A/-90, B/-90, C/0, D/180, O/-90}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "9. Tiếp tuyến kẻ từ D đến đường tròn", desc: "Một tiếp tuyến",
      code: `\\begin{tikzpicture}[declare function={r=3; gocm=50; goch=-35;}, line width=0.6pt]
  \\path
  (0,0) coordinate (O)
  (gocm:r) coordinate (A)
  ({180-goch}:r) coordinate (B)
  (goch:r) coordinate (C)
  ;
  \\begin{scope}[overlay]
  \\path
  ($(A)!1!-90:(O)$) coordinate (OA)
  (intersection of A--OA and B--C) coordinate (S)
  ;
  \\end{scope}
  \\path pic[draw, angle radius=5pt]{right angle=O--A--S};
  \\draw
  (O)--(A)--(S)--(B)
  let \\p1=($(O)-(A)$) in (O) circle ({veclen(\\x1,\\y1)})
  ;
  \\foreach \\t/\\g in {A/gocm, B/{180-goch}, C/goch, S/0, O/135}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "10. Hai đường tròn tiếp xúc ngoài", desc: "Tiếp tuyến chung ngoài",
      code: `\\begin{tikzpicture}[
  declare function={
    R=3;
    r=0.35*R;
    d=R+r+2;
    goc=acos((R-r)/d);
    goch=acos((R+r)/d);
    k=1;
  },
  line width=0.6pt
]
  \\path
  (0,0) coordinate (O)
  (d,0) coordinate (O')
  (goc:R) coordinate (A)
  (-goc:R) coordinate (B)
  (goch:R) coordinate (C)
  (-goch:R) coordinate (D)
  ($(d,0)+(goc:r)$) coordinate (A')
  ($(d,0)+(-goc:r)$) coordinate (B')
  (intersection of A--A' and B--B') coordinate (S)
  ;
  \\foreach \\x/\\y/\\z in {O/A/S, O/B/S}{
  \\path pic[draw, angle radius=5pt]{right angle=\\x--\\y--\\z};
  }
  \\draw
  (O) circle (R)
  (O') circle (r)
  (A)--(S)--(B)--(O)--cycle
  ;
  \\foreach \\t/\\g in {A/goc, A'/goc, B/-goc, B'/-goc, O/180, O'/-90, S/0}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "11. Hai đường tròn cắt nhau", desc: "Và tiếp tuyến chung trong",
      code: `\\begin{tikzpicture}[
  declare function={
    R=3;
    r=1.5;
    d=R+r;
    goc=acos((R-r)/d);
    goch=acos((R+r)/d);
  },
  line width=0.6pt
]
  \\path
  (0,0) coordinate (O)
  (0:d) coordinate (O')
  (goc:R) coordinate (A)
  (-goc:R) coordinate (B)
  (goch:R) coordinate (C)
  (-goch:R) coordinate (D)
  ($(0:d)+(goc:r)$) coordinate (A')
  ($(0:d)+(-goc:r)$) coordinate (B')
  (intersection of A--A' and B--B') coordinate (S)
  ;
  \\draw
  (O) circle (R)
  (O') circle (r)
  (A)--(S)--(B)
  ;
  \\foreach \\t/\\g in {A/goc, A'/goc, B/-goc, B'/-goc, O/-90, O'/-90, S/0}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`},
    { title: "12. Hai đường tròn tiếp xúc trong", desc: "Tiếp xúc trong",
      code: `\\begin{tikzpicture}[declare function={R=5; r=2; d=R-r;}, line width=0.6pt]
  \\path
  (0,0) coordinate (O)
  (0:d) coordinate (O')
  (0:R) coordinate (A)
  ;
  \\draw
  (O) circle (R)
  (O') circle (r)
  ;
  \\foreach \\t/\\g in {O/180, O'/-90, A/0}{
  \\draw (\\t) circle (0.4pt) node[shift={(\\g:9pt)}, font=\\normalsize]{$\\t$};
  }
\\end{tikzpicture}`}
];

const conicCodes = [
    { title: "1. Đường Elip", desc: "Đường elip",
      code: `\\begin{tikzpicture}[declare function={a=2.5; b=2;}]
  \\draw[line width=0.6pt] (0,0) ellipse (a and b);
\\end{tikzpicture}`},
    { title: "2. Parabol y = a*x^2 (hướng lên)", desc: "Parabol hướng lên",
      code: `\\begin{tikzpicture}[declare function={a=0.65; xmin=-4; xmax=4; ymin=-1; ymax=5.15;}]
  \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};
  \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[shift={(-6pt,-5pt)}] {$y$};
  \\begin{scope}
  \\clip (xmin, ymin) rectangle (xmax, ymax);
  \\draw[line width=0.6pt, smooth, samples=150, domain=-3:3] plot (\\x, {a*(\\x)^2});
  \\end{scope}
\\end{tikzpicture}`},
    { title: "3. Parabol x = a*y^2 (hướng sang phải)", desc: "Parabol hướng sang phải",
      code: `\\begin{tikzpicture}[declare function={a=0.65; xmin=-1; xmax=4; ymin=-3.25; ymax=3.25;}]
  \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};
  \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[shift={(-6pt,-5pt)}] {$y$};
  \\begin{scope}
  \\clip (xmin, ymin) rectangle (xmax, ymax);
  \\draw[line width=0.6pt, smooth, samples=150, domain=-3.5:3.5] plot ({a*(\\x)^2}, \\x);
  \\end{scope}
\\end{tikzpicture}`},
    { title: "4. Elip với tiêu điểm và bán kính vectơ", desc: "Elip và bán kính vectơ",
      code: `\\begin{tikzpicture}[
  declare function={
    a=2.5;
    b=2;
    xmin=-a-0.5;
    xmax=-xmin;
    ymin=-b-0.5;
    ymax=-ymin;
    c=sqrt(a^2-b^2);
  }
]
  \\path
  (60:a and b) coordinate (M)
  (0:c) coordinate (F2)
  (180:c) coordinate (F1)
  ;
  \\draw[dashed, line width=0.6pt] (F1) -- (M) -- (F2);
  \\draw[line width=0.6pt] (0,0) ellipse (a and b);
  \\foreach \\p/\\pos/\\lab in {M/115/M, F2/-90/F_2, F1/-90/F_1} {
  \\draw (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};
  }
\\end{tikzpicture}`},
    { title: "5. Hyperbol với tiếp tuyến", desc: "Hyperbol với tiếp tuyến",
      code: `\\begin{tikzpicture}[
  declare function={
    a=0.65;
    b=0.6;
    c=sqrt(a^2+b^2);
    goc=0.75;
  }
]
  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({a*cosh(\\x)}, {b*sinh(\\x)});
  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({-a*cosh(\\x)}, {b*sinh(\\x)});
  \\path
  let \\n1={4*c} in
  (180:c) coordinate (F1)
  (0:c) coordinate (F2)
  ({a*cosh(goc)}, {b*sinh(goc)}) coordinate (M)
  ($(F1)!\\n1 cm!(M)$) coordinate (A)
  ;
  \\draw[cyan, line width=0.6pt] (F2) -- (M) -- (A);
  \\foreach \\p/\\pos/\\lab in {F1/180/F_1, F2/0/F_2, M/135/M, A/0/A} {
  \\draw (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};
  }
\\end{tikzpicture}`},
    { title: "6. Elip đầy đủ (tâm, đỉnh, tiêu điểm)", desc: "Đầy đủ các điểm đặc biệt",
      code: `\\begin{tikzpicture}[
  declare function={
    a=2.5;
    b=2;
    xmin=-a-0.5;
    xmax=-xmin;
    ymin=-b-0.5;
    ymax=-ymin;
    goc=60;
    c=sqrt(a^2-b^2);
  }
]
  \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};
  \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[shift={(-6pt,-5pt)}] {$y$};
  \\path
  (0,0) coordinate (O)
  (goc:a and b) coordinate (M)
  (180:a) coordinate (A1)
  (0:a) coordinate (A2)
  (-90:b) coordinate (B1)
  (90:b) coordinate (B2)
  (0:c) coordinate (F2)
  (180:c) coordinate (F1)
  ;
  \\draw[dashed, line width=0.6pt] (F1) -- (M) -- (F2);
  \\draw[line width=0.6pt] (0,0) ellipse (a and b);
  \\foreach \\p/\\pos/\\lab in {
  O/-135/O,
  A1/-135/A_1,
  A2/-45/A_2,
  B1/-45/B_1,
  B2/45/B_2,
  F1/-90/F_1,
  F2/-90/F_2,
  M/45/M
  } {
  \\draw (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};
  }
\\end{tikzpicture}`},
    { title: "7. Hyperbol đầy đủ (tiệm cận, HCN)", desc: "Đầy đủ với tiệm cận",
      code: `\\begin{tikzpicture}[
  declare function={
    a=1.5;
    b=1.3;
    c=sqrt(a^2+b^2);
    goc=0.75;
    xmin=-4;
    xmax=4.25;
    ymin=-2.5;
    ymax=2.75;
  }
]
  \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};
  \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[shift={(-6pt,-5pt)}] {$y$};
  \\begin{scope}
  \\clip (xmin, ymin) rectangle (xmax, ymax);
  \\draw[dashed, line width=0.6pt, smooth, samples=30, domain=-8:8] plot (\\x, {-(b/a)*\\x});
  \\draw[dashed, line width=0.6pt, smooth, samples=30, domain=-8:8] plot (\\x, {(b/a)*\\x});
  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({a*cosh(\\x)}, {b*sinh(\\x)});
  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({-a*cosh(\\x)}, {b*sinh(\\x)});
  \\end{scope}
  \\draw[dashed, line width=0.6pt] (-a,-b) rectangle (a,b);
  \\path
  (a,b) coordinate (P)
  (90:b) coordinate (B2)
  (-a,b) coordinate (Q)
  (180:a) coordinate (A1)
  (0,0) coordinate (O)
  (-a,-b) coordinate (R)
  (-90:b) coordinate (B1)
  (a,-b) coordinate (S)
  (0:a) coordinate (A2)
  (180:c) coordinate (F1)
  (0:c) coordinate (F2)
  ;
  \\foreach \\p/\\pos/\\lab in {
  P/120/P,
  B2/45/B_2,
  Q/60/Q,
  A1/-45/A_1,
  O/-135/O,
  R/-60/R,
  B1/-45/B_1,
  S/240/S,
  A2/-45/A_2,
  F1/-90/F_1,
  F2/-90/F_2
  } {
  \\draw (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};
  }
\\end{tikzpicture}`},
    { title: "8. Parabol với tiêu điểm và đường chuẩn", desc: "Với tiêu điểm và đường chuẩn",
      code: `\\begin{tikzpicture}[
  declare function={
    p=0.45;
    xt=1.5;
    xmin=-3.25;
    xmax=3.25;
    ymin=-1.5*p;
    ymax=4;
  }
]
  \\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};
  \\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[shift={(-6pt,-5pt)}] {$y$};
  \\begin{scope}[color=teal!85!blue]
  \\clip (-3.5, {-1.5*p}) rectangle (3.5, 4.1);
  \\path
  (0, {-0.5*p}) coordinate (A)
  (xt, {-0.5*p}) coordinate (B)
  (xt, {2*p*xt*xt}) coordinate (M)
  (0, {0.5*p}) coordinate (F)
  ;
  \\path pic[draw, angle radius=5pt, line width=0.6pt]{right angle=A--B--M};
  \\draw[dashed, line width=0.6pt] (B) -- (M) -- (F);
  \\draw[line width=0.6pt, smooth, samples=150, domain=-3.5:3.5] plot (\\x, {2*p*(\\x)^2});
  \\draw[line width=0.6pt] (-3, {-0.5*p}) -- (3, {-0.5*p}) node[shift={(0.25,-0.25)}, font=\\normalsize] {$\\Delta$};
  \\foreach \\p/\\pos/\\lab in {F/150/F, M/10/M, B/-90/A} {
  \\draw (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};
  }
  \\end{scope}
\\end{tikzpicture}`},
    { title: "9. Tiếp tuyến của elip tại một điểm", desc: "Elip với tiếp tuyến",
      code: `\\begin{tikzpicture}[
  declare function={
    a=2.5;
    b=0.65*a;
    goc=60;
    xv=a*sin(goc);
    yv=-b*cos(goc);
  }
]
  \\path
  (goc:a and b) coordinate (M)
  ($(M)+(xv,yv)$) coordinate (A1)
  ($(M)!3cm!(A1)$) coordinate (T1)
  ($2*(M)-(T1)$) coordinate (T2)
  ;
  \\draw[line width=0.6pt] (T1) -- (T2);
  \\draw[line width=0.6pt] (0,0) ellipse (a and b);
  \\draw (M) circle (0.8pt) node[shift={(goc:8pt)}, font=\\normalsize] {$M$};
\\end{tikzpicture}`},
    { title: "10. Tiếp tuyến của hyperbol tại hai điểm", desc: "Hyperbol với 2 tiếp tuyến",
      code: `\\begin{tikzpicture}[
  declare function={
    a=0.65;
    b=0.6;
    c=sqrt(a^2+b^2);
    goc=1.25;
  }
]
  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({a*cosh(\\x)}, {b*sinh(\\x)});
  \\draw[line width=0.6pt, smooth, samples=150, domain=-2:2] plot ({-a*cosh(\\x)}, {b*sinh(\\x)});
  \\path
  (180:c) coordinate (F1)
  (0:c) coordinate (F2)
  ({a*cosh(goc)}, {b*sinh(goc)}) coordinate (M)
  ({a*sinh(goc)}, {b*cosh(goc)}) coordinate (Mt)
  ($(M)+(Mt)$) coordinate (A1)
  ($(M)!2cm!(A1)$) coordinate (T1)
  ($2*(M)-(T1)$) coordinate (T2)
  ;
  \\path
  ({-a*cosh(goc)}, {b*sinh(goc)}) coordinate (N)
  ({a*sinh(goc)}, {-b*cosh(goc)}) coordinate (Nt)
  ($(N)+(Nt)$) coordinate (B1)
  ($(N)!2cm!(B1)$) coordinate (K1)
  ($2*(N)-(K1)$) coordinate (K2)
  ;
  \\draw[blue, line width=0.6pt] (T1) -- (T2);
  \\draw[blue, line width=0.6pt] (K1) -- (K2);
  \\foreach \\p/\\pos/\\lab in {M/135/M, N/45/N} {
  \\draw (\\p) circle (0.4pt) node[shift={(\\pos:9pt)}, font=\\normalsize] {$\\lab$};
  }
\\end{tikzpicture}`},
    { title: "11. Parabol với tiếp tuyến", desc: "Tiếp tuyến parabol",
      code: `\\begin{tikzpicture}[
  declare function={
    a=0.65;
    xt=1;
    xmin=-1;
    xmax=4;
    ymin=-3;
    ymax=3;
  }
]
  \\path
  ({a*(xt)*(xt)}, xt) coordinate (M)
  ({2*a*xt}, 1) coordinate (vt)
  ($(M)+(vt)$) coordinate (Xt)
  ($(M)!2cm!(Xt)$) coordinate (X) 
  ($2*(M)-(X)$) coordinate (Y)
  ;
  \\draw[line width=0.6pt, smooth, samples=150, domain=-2.5:2.5] plot ({a*(\\x)^2}, \\x);
  \\draw[line width=0.6pt] (M) -- (X) node[pos=1, shift={(-0.5,0.1)}, font=\\normalsize] {$(t_M)$} -- (Y);
  \\draw (M) circle (0.8pt) node[shift={(120:8pt)}, font=\\normalsize] {$M$};
\\end{tikzpicture}`}
];

let content = fs.readFileSync('constants.tsx', 'utf8');

function updateTemplates(categoryName, newItems) {
    const escapedCategoryName = categoryName.replace(/\./g, "\\.");
    const rx = new RegExp("(name:\\s*'\\s*" + escapedCategoryName + "'\\s*,[\\s\\S]*?templates:\\s*\\[)([\\s\\S]*?)(\\]\\s*\\}\\s*,?)");
    const match = content.match(rx);
    if (!match) {
        console.error("Could not find category:", categoryName);
        return;
    }
    
    let replacement = newItems.map((item, index) => {
        let prefix = "geo-" + categoryName.split(".")[0].trim().replace(".","-") + "-" + index;
        return "          {\n" +
               "            \"id\": \"" + prefix + "\",\n" +
               "            \"title\": " + JSON.stringify(item.title) + ",\n" +
               "            \"description\": " + JSON.stringify(item.desc) + ",\n" +
               "            \"code\": " + JSON.stringify(item.code) + "\n" +
               "          }";
    }).join(",\n");
    
    content = content.replace(rx, function(match, p1, p2, p3) {
        return p1 + "\n" + replacement + "\n          " + p3;
    });
}

updateTemplates("1.1. Tam giác", triCodes);
updateTemplates("1.2. Đa giác", polyCodes);
updateTemplates("1.3. Đường tròn", circleCodes);
updateTemplates("1.4. Đường cônic", conicCodes);

fs.writeFileSync('constants.tsx', content);
console.log("Updated constants.tsx");
