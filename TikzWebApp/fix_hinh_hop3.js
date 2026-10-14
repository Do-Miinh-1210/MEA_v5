import fs from 'fs';
let content = fs.readFileSync('constants.tsx', 'utf8');

const oldStr = `\\begin{tikzpicture}[declare function={a=5; b=3; h=4; k=0.5;}]
 \\path
 (0:0) coordinate (A)
 (220:b) coordinate (B)
 (0:a) coordinate (D)
 ($(B)+(D)-(A)$) coordinate (C)
 ;
 \\foreach \\x in {A,B,C,D}{
 \\path (\\x)++(90:h) coordinate (\\x1);
 }
 \\draw[dashed, line width=0.4pt] (A')--(A)--(B) (A)--(D);
 \\draw[line width=0.6pt]
 (B')--(A')--(D')--(C')
 (D')--(D)--(C)
 (B)--(C)--(C')--(B')--cycle
 ;
 \\foreach \\x/\\goc/\\t in {
 A/170/A, B/-90/B, C/-90/C, D/0/D,
 A1/90/A', B1/90/B', C1/90/C', D1/90/D'
 }{
 \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};
 }
\\end{tikzpicture}`;

const newStr = `\\begin{tikzpicture}[declare function={a=5; b=3; h=4; k=0.5;}]
 \\path
 (0:0) coordinate (A)
 (220:b) coordinate (B)
 (0:a) coordinate (D)
 ($(B)+(D)-(A)$) coordinate (C)
 ;
 \\foreach \\x in {A,B,C,D}{
 \\path (\\x)++(90:h) coordinate (\\x');
 }
 \\draw[dashed, line width=0.4pt] (A')--(A)--(B) (A)--(D);
 \\draw[line width=0.6pt]
 (B')--(A')--(D')--(C')
 (D')--(D)--(C)
 (B)--(C)--(C')--(B')--cycle
 ;
 \\foreach \\p/\\goc in {
 A/170, B/-90, C/-90, D/0,
 A'/90, B'/90, C'/-25, D'/90
 }{
 \\draw (\\p) circle (0.4pt) node[shift={(\\goc:9pt)}]{$\\p$};
 }
\\end{tikzpicture}`;

content = content.replace(oldStr, newStr);

fs.writeFileSync('constants.tsx', content);
