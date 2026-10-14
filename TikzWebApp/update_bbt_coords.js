import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');

function updateCode(id, newCode) {
  const regex = new RegExp(`(id: '${id}',[\\s\\S]*?code: \\\`)([\\s\\S]*?)(\\\`)`);
  content = content.replace(regex, `$1${newCode}$3`);
}

updateCode('math-bbt-1', `\\\\begin{tikzpicture}[every node/.style={font=\\\\normalsize}, declare function={f(\\\\x)=\\\\x^3-3*\\\\x+2;}]
\\\\tkzTabInit[nocadre=false, lgt=1.5, espcl=2.5, deltacl=0.6]
{$x$/0.7, $f'(x)$/0.7, $f(x)$/2.5}
{$-\\\\infty$, $-1$, $1$, $+\\\\infty$}
\\\\tkzTabLine{, +, 0, -, 0, +, }

\\\\path
([yshift=8pt]N13) node (A1) {$-\\\\infty$}
([yshift=-16pt]N22) node (A2) {$4$}
([yshift=16pt]N33) node (A3) {$0$}
([yshift=-8pt]N42) node (A4) {$+\\\\infty$}
;

\\\\foreach \\\\i/\\\\j in {1/2, 2/3, 3/4}{
\\\\draw[-Stealth, line width=0.6pt] (A\\\\i) -- (A\\\\j);
}
\\\\end{tikzpicture}`);

updateCode('math-bbt-18', `\\\\begin{tikzpicture}[>=stealth, every node/.style={font=\\\\normalsize}, declare function={f(\\\\x)=(\\\\x*\\\\x-2*\\\\x+2)/(\\\\x-1);}]
\\\\tkzTabInit[nocadre=false, lgt=1.5, espcl=2, deltacl=0.6]
{$x$/0.7, $f'(x)$/0.7, $f(x)$/2.5}
{$-\\\\infty$, $0$, $1$, $2$, $+\\\\infty$}
\\\\tkzTabLine{, +, 0, -, , -, 0, +, }
\\\\draw[double distance=1pt, double=white, line width=0.6pt] (N31) -- (N33);

\\\\path
([yshift=8pt]N13) node (A1) {$-\\\\infty$}
([yshift=-16pt]N22) node (A2) {$-2$}
([xshift=-16pt, yshift=8pt]N33) node (A3) {$-\\\\infty$}
([xshift=16pt, yshift=-8pt]N32) node (A4) {$+\\\\infty$}
([yshift=16pt]N43) node (A5) {$2$}
([yshift=-8pt]N52) node (A6) {$+\\\\infty$}
;

\\\\foreach \\\\i/\\\\j in {1/2, 2/3, 4/5, 5/6}{
\\\\draw[-Stealth, line width=0.6pt] (A\\\\i) -- (A\\\\j);
}
\\\\end{tikzpicture}`);

fs.writeFileSync('constants.tsx', content);
