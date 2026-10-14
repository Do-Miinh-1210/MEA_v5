import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');

const newTemplates = `          {
            id: 'geo-3d-1',
            title: '1. Hình chóp tứ giác',
            description: 'Hình chóp tứ giác (đáy hình thang)',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=5; b=0.45*a; h=4;}]
 \\path
 (0,0) coordinate (B)
 (0:a) coordinate (C)
 (-45:b) coordinate (D)
 ($(D)+(0,h)$) coordinate (A)
 ;
 \\draw[dashed, line width=0.4pt] (B)--(C);
 \\draw[line width=0.6pt]
 (A)--(D)
 (A)--(B)--(D)--(C)--cycle
 ;
 \\foreach \\x/\\goc in {A/90, B/240, C/-60, D/-90}{
 \\draw (\\x) circle (0.8pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\x$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-2',
            title: '2. Hình chóp tam giác vuông',
            description: 'Hình chóp có đáy là tam giác vuông',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=5; b=0.45*a; h=0.65*a;}]
 \\path
 (0,0) coordinate (A)
 (0:a) coordinate (C)
 (-45:b) coordinate (B)
 ($(A)+(0,h)$) coordinate (S)
 ;
 \\foreach \\x/\\y/\\z in {B/A/S, C/A/S}{
 \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=\\x--\\y--\\z};
 }
 \\draw[dashed, line width=0.4pt] (A)--(C);
 \\draw[line width=0.6pt]
 (S)--(B)
 (S)--(A)--(B)--(C)--cycle
 ;
 \\foreach \\x/\\goc in {S/90, A/190, B/-90, C/0}{
 \\draw (\\x) circle (0.8pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\x$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-3',
            title: '3. Tam giác vuông',
            description: 'Tam giác vuông (hình phẳng)',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=5; c=3;}]
 \\path
 (0,0) coordinate (A)
 (0:a) coordinate (B)
 (180:c) coordinate (C)
 ;
 \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=B--A--C};
 \\draw[line width=0.6pt] (A)--(B)--(C)--cycle;
 \\foreach \\t/\\g in {A/225, B/-45, C/135}{
 \\draw (\\t) circle (0.8pt) node[shift={(\\g:8pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-4',
            title: '4. Hình chóp có đáy hình thang (dạng elip)',
            description: 'Hình chóp có đáy hình thang (dạng elip)',
            code: String.raw\`\\begin{tikzpicture}[declare function={r=2.5;}]
 \\path
 (90:{r*1.25}) coordinate (A)
 (160:{r} and {r*0.35}) coordinate (B)
 (20:{r} and {r*0.35}) coordinate (C)
 (260:{r} and {r*0.5}) coordinate (D)
 ;
 \\draw[dashed, line width=0.4pt] (B)--(C);
 \\draw[line width=0.6pt]
 (A)--(D)
 (A)--(B)--(D)--(C)--cycle
 ;
 \\foreach \\x/\\goc in {A/90, B/120, C/60, D/-90}{
 \\draw (\\x) circle (0.8pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\x$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-5',
            title: '5. Hình chóp cụt hình bình hành',
            description: 'Hình chóp cụt (đáy dưới là hình bình hành)',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=5; b=3; h=3.5; k=0.5;}]
 \\path
 (0,0) coordinate (A)
 (0:a) coordinate (D)
 (-135:b) coordinate (B)
 ($(B)+(D)-(A)$) coordinate (C)
 ($(A)+ (90:h)$) coordinate (S)
 ;
 \\draw[dashed, line width=0.4pt] (B)--(A)--(D) (A)--(S);
 \\draw[line width=0.6pt]
 (S)--(B)--(C)--(D)--cycle
 (S)--(C)
 ;
 \\foreach \\t/\\g in {A/180, B/-90, C/-90, D/90, S/90}{
 \\draw (\\t) circle (0.8pt) node[shift={(\\g:8pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-6',
            title: '6. Hình chóp cụt có dấu bằng',
            description: 'Hình chóp cụt (có dấu bằng trên các cạnh)',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=5; b=3; h=4; k=0.5;}]
 \\path
 (0,0) coordinate (A)
 (0:a) coordinate (D)
 (-135:b) coordinate (B)
 ($(B)+(D)-(A)$) coordinate (C)
 ($(0,h)+(-135:{0.35*b})$) coordinate (S)
 ;
 \\foreach \\x/\\y in {S/A, S/B}{
 \\path (\\x)--(\\y) node[pos=k, sloped]{\\tikz{\\draw[line width=0.6pt] (-90:1.5pt)--(90:1.5pt);}};
 }
 \\draw[dashed, line width=0.4pt] (B)--(A)--(D) (A)--(S);
 \\draw[line width=0.6pt]
 (S)--(B)--(C)--(D)--cycle
 (S)--(C)
 ;
 \\foreach \\t/\\g in {A/60, B/-90, C/-90, D/90, S/90}{
 \\draw (\\t) circle (0.8pt) node[shift={(\\g:8pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-7',
            title: '7. Hình lăng trụ đứng đáy thang',
            description: 'Hình lăng trụ đứng (đáy là hình thang)',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=4; b=0.5*a; h=1.25*a; k=0.5;}]
 \\path
 (0:0) coordinate (A)
 (220:b) coordinate (B)
 (0:a) coordinate (D)
 ($(B)+(D)-(A)$) coordinate (C)
 ;
 \\foreach \\x in {A,B,C,D}{
 \\path (\\x)++(90:h) coordinate (\\x1);
 }
 \\draw[dashed, line width=0.4pt] (A1)--(A)--(B) (A)--(D);
 \\draw[line width=0.6pt]
 (B1)--(A1)--(D1)--(C1)
 (D1)--(D)--(C)
 (B)--(C)--(C1)--(B1)--cycle
 ;
 \\foreach \\x/\\goc/\\t in {
 A/45/A, B/-90/B, C/-90/C, D/0/D,
 A1/90/A', B1/90/B', C1/90/C', D1/90/D'
 }{
 \\draw (\\x) circle (0.8pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-8',
            title: '8. Hình chóp đáy hình bình hành (góc vuông A)',
            description: 'Hình chóp có đáy hình bình hành (các góc vuông tại A)',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=5; b=3; h=3.5; k=0.5;}]
 \\path
 (0,0) coordinate (A)
 (0:a) coordinate (D)
 (-135:b) coordinate (B)
 ($(B)+(D)-(A)$) coordinate (C)
 (0,h) coordinate (S)
 ;
 \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=B--A--S};
 \\path pic[draw, line width=0.6pt, angle radius=5pt]{right angle=D--A--S};
 \\draw[dashed, line width=0.4pt] (B)--(A)--(D) (A)--(S);
 \\draw[line width=0.6pt]
 (S)--(B)--(C)--(D)--cycle
 (S)--(C)
 ;
 \\foreach \\t/\\g in {A/180, B/-90, C/-90, D/90, S/90}{
 \\draw (\\t) circle (0.8pt) node[shift={(\\g:8pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-9',
            title: '9. Hình lăng trụ tam giác',
            description: 'Hình lăng trụ tam giác',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=5; b=0.55*a; h=0.9*a; k=0.5;}]
 \\path
 (0:0) coordinate (A)
 (-43:b) coordinate (B)
 (0:a) coordinate (C)
 ;
 \\foreach \\x in {A,B,C}{
 \\path (\\x)++(90:h) coordinate (\\x1);
 }
 \\draw[dashed, line width=0.4pt] (A)--(C);
 \\draw[line width=0.6pt]
 (B1)--(A1)--(C1)--cycle
 (A1)--(A)--(B)--(B1)
 (C1)--(C)--(B)
 ;
 \\foreach \\x/\\goc/\\t in {
 A/180/A, B/-90/B, C/0/C,
 A1/100/A', B1/85/B', C1/80/C'
 }{
 \\draw (\\x) circle (0.8pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-10',
            title: '10. Hình hộp chữ nhật (lăng trụ đứng)',
            description: 'Hình hộp chữ nhật (lăng trụ đứng)',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=5; b=0.45*a; h=0.65*a; k=0.5;}]
 \\path
 (0:0) coordinate (A)
 (220:b) coordinate (B)
 (0:a) coordinate (D)
 ($(B)+(D)-(A)$) coordinate (C)
 ;
 \\foreach \\x in {A,B,C,D}{
 \\path (\\x)++(90:h) coordinate (\\x1);
 }
 \\draw[dashed, line width=0.4pt] (A1)--(A)--(B) (A)--(D);
 \\draw[line width=0.6pt]
 (B1)--(A1)--(D1)--(C1)
 (D1)--(D)--(C)
 (B)--(C)--(C1)--(B1)--cycle
 ;
 \\foreach \\x/\\goc/\\t in {
 A/45/A, B/-90/B, C/-90/C, D/0/D,
 A1/90/A', B1/90/B', C1/90/C', D1/90/D'
 }{
 \\draw (\\x) circle (0.8pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-11',
            title: '11. Hình chóp tam giác (đáy tam giác, đỉnh S)',
            description: 'Hình chóp tam giác (đáy tam giác, đỉnh S)',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=5; b=3; h=3.5; k=0.5;}]
 \\path
 (0,0) coordinate (A)
 (0:a) coordinate (D)
 (-45:b) coordinate (B)
 ($(B)+(0:{0.65*a})$) coordinate (C)
 ($(A)+(90:h) $) coordinate (S)
 ;
 \\path pic[draw, line width=0.6pt, angle radius=7pt]{right angle=B--A--S};
 \\path pic[draw, line width=0.6pt, angle radius=7pt]{right angle=D--A--S};
 \\draw[dashed, line width=0.4pt] (A)--(D);
 \\draw[line width=0.6pt]
 (S)--(B)--(C)--(D)--cycle
 (B)--(A)--(S)--(C)
 ;
 \\foreach \\t/\\g in {A/180, B/-90, C/-90, D/0, S/120}{
 \\draw (\\t) circle (0.8pt) node[shift={(\\g:8pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-12',
            title: '12. Hình lăng trụ tam giác (bản khác)',
            description: 'Hình lăng trụ tam giác (bản khác)',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=5; b=0.55*a; h=0.9*a; k=0.5;}]
 \\path
 (0:0) coordinate (A)
 (-43:b) coordinate (B)
 (0:a) coordinate (C)
 ;
 \\foreach \\x in {A,B,C}{
 \\path (\\x)++(80:h) coordinate (\\x1);
 }
 \\draw[dashed, line width=0.4pt] (A)--(C);
 \\draw[line width=0.6pt]
 (B1)--(A1)--(C1)--cycle
 (A1)--(A)--(B)--(B1)
 (C1)--(C)--(B)
 ;
 \\foreach \\x/\\goc/\\t in {
 A/180/A, B/-90/B, C/0/C,
 A1/100/A', B1/85/B', C1/80/C'
 }{
 \\draw (\\x) circle (0.8pt) node[shift={(\\g:8pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-13',
            title: '13. Hình hộp chữ nhật (phối cảnh)',
            description: 'Hình hộp chữ nhật (dạng phối cảnh)',
            code: String.raw\`\\begin{tikzpicture}[declare function={r=2.5; k=0.5;}]
 \\path
 (0:0) coordinate (A)
 (0:r) coordinate (B)
 (37:0.65*r) coordinate (D)
 ($(B)+(D)-(A)$) coordinate (C)
 ;
 \\foreach \\x in {A,B,C,D}{
 \\path (\\x)++(90:r) coordinate (\\x_1);
 }
 \\draw[dashed, line width=0.4pt] (D_1)--(D)--(A) (D)--(C);
 \\draw[line width=0.6pt]
 (A)--(B)--(C)
 (A)--(A_1)
 (B)--(B_1)
 (C)--(C_1)
 (A_1)--(B_1)--(C_1)--(D_1)--cycle
 ;
 \\foreach \\x/\\goc/\\t in {
 A/255/A, B/-75/B, C/10/C, D/170/D,
 A_1/135/A', B_1/90/B', C_1/45/C', D_1/90/D'
 }{
 \\draw (\\x) circle (0.8pt) node[shift={(\\g:8pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-14',
            title: '14. Hình chóp đáy bình hành (tâm O)',
            description: 'Hình chóp có đáy là hình bình hành (tâm O)',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=5; b=3; h=4.5; k=0.5;}]
 \\path
 (0,0) coordinate (A)
 (0:a) coordinate (D)
 (-135:b) coordinate (B)
 ($(B)+(D)-(A)$) coordinate (C)
 ($(A)!k!(C)$) coordinate (O)
 ($(O)+(0,h)$) coordinate (S)
 ;
 \\path pic[draw, line width=0.6pt, angle radius=6pt]{right angle=A--O--S};
 \\path pic[draw, line width=0.6pt, angle radius=6pt]{right angle=D--O--S};
 \\draw[dashed, line width=0.4pt] (B)--(A)--(D)--cycle (C)--(A)--(S)--(O);
 \\draw[line width=0.6pt]
 (S)--(B)--(C)--(D)--cycle
 (S)--(C)
 ;
 \\foreach \\t/\\g in {A/150, B/-90, C/-60, D/60, S/90, O/-90}{
 \\draw (\\t) circle (0.8pt) node[shift={(\\g:8pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-15',
            title: '15. Hình lăng trụ đứng (bản khác)',
            description: 'Hình lăng trụ đứng (bản khác)',
            code: String.raw\`\\begin{tikzpicture}[declare function={a=4; b=0.5*a; h=1.25*a; k=0.5;}]
 \\path
 (0:0) coordinate (A)
 (220:b) coordinate (B)
 (0:a) coordinate (D)
 ($(B)+(D)-(A)$) coordinate (C)
 ;
 \\foreach \\x in {A,B,C,D}{
 \\path (\\x)++(90:h) coordinate (\\x1);
 }
 \\draw[dashed, line width=0.4pt] (A1)--(A)--(B) (A)--(D);
 \\draw[line width=0.6pt]
 (B1)--(A1)--(D1)--(C1)
 (D1)--(D)--(C)
 (B)--(C)--(C1)--(B1)--cycle
 ;
 \\foreach \\x/\\goc/\\t in {
 A/45/A, B/-90/B, C/-90/C, D/0/D,
 A1/90/A', B1/90/B', C1/90/C', D1/90/D'
 }{
 \\draw (\\x) circle (0.8pt) node[shift={(\\g:8pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}\`
          },
          {
            id: 'geo-3d-16',
            title: '16. Khối đa diện mạng tinh thể',
            description: 'Khối đa diện (hình 6 mặt, 8 đỉnh, 12 cạnh) – mạng tinh thể',
            code: String.raw\`\\begin{tikzpicture}[declare function={r=2.5; goc=30; k=0.5;}]
 % Điểm A (tam giác đều)
 \\foreach \\i in {1,...,3}{
 \\path (goc+\\i*120-120:r) coordinate (A_\\i);
 }
 % Điểm B (tam giác đều xoay)
 \\foreach \\i in {1,...,3}{
 \\path (goc+\\i*120-60:r) coordinate (B_\\i);
 }
 % Điểm C (lục giác)
 \\foreach \\i in {1,...,6}{
 \\path (goc+\\i*60-60:1.5*r) coordinate (C_\\i);
 }
 % Nét đứt
 \\draw[dash pattern=on 2pt off 2pt, line width=0.4pt]
 (B_1)--(B_2)--(B_3)--cycle
 (B_1)--(C_1) (B_1)--(C_2) (B_1)--(C_3)
 (B_2)--(C_3) (B_2)--(C_4) (B_2)--(C_5)
 (B_3)--(C_5) (B_3)--(C_6) (B_3)--(C_1)
 ;
 % Nét liền
 \\draw[line width=0.6pt]
 (A_1)--(A_2)--(A_3)--cycle
 (A_1)--(C_6) (A_1)--(C_1) (A_1)--(C_2)
 (A_2)--(C_2) (A_2)--(C_3) (A_2)--(C_4)
 (A_3)--(C_4) (A_3)--(C_5) (A_3)--(C_6)
 (C_1)--(C_2)--(C_3)--(C_4)--(C_5)--(C_6)--cycle
 ;
 % Điểm
 \\foreach \\x in {A_1,A_2,A_3,B_1,B_2,B_3,C_1,C_2,C_3,C_4,C_5,C_6}{
 \\draw (\\x) circle (0.8pt);
 }
\\end{tikzpicture}\`
          }`;

// Replace the templates array in category "1.5. Đa diện"
const sectionRegex = /(name:\s*'1.5\.\s*Đa diện',\s*templates:\s*\[\s*)([\s\S]*?)(\s*\]\s*\},)/;
content = content.replace(sectionRegex, `$1${newTemplates}$3`);

// Replace occurrences of line join=round, line cap=round with empty strings
// specifically inside the constants.tsx or perhaps we can just update the geminiService instructions

fs.writeFileSync('constants.tsx', content);
