import fs from 'fs';
let content = fs.readFileSync('constants.tsx', 'utf8');

const oldStr = ` \\foreach \\x/\\goc/\\t in {
 A/170/A, B/-90/B, C/-90/C, D/0/D,
 A1/90/A', B1/90/B', C1/90/C', D1/90/D'
 }{
 \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};
 }`;

const newStr = ` \\foreach \\x/\\goc in {
 A/170, B/-90, C/-90, D/0,
 A'/90, B'/90, C'/-25, D'/90
 }{
 \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}]{$\\x$};
 }`;

content = content.replace(oldStr, newStr);

// Also update `coordinate (\x1)` to `coordinate (\x')`
content = content.replace(
  ` \\foreach \\x in {A,B,C,D}{
 \\path (\\x)++(90:h) coordinate (\\x1);
 }`,
  ` \\foreach \\x in {A,B,C,D}{
 \\path (\\x)++(90:h) coordinate (\\x');
 }`
);

// We should also look for other similar ones:
content = content.replace(
  ` \\foreach \\x/\\goc/\\t in {
 A/45/A, B/-90/B, C/-90/C, D/0/D,
 A1/90/A', B1/90/B', C1/90/C', D1/90/D'
 }{
 \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{$\\t$};
 }`,
   ` \\foreach \\x/\\goc in {
 A/170, B/-90, C/-90, D/0,
 A'/90, B'/90, C'/-25, D'/90
 }{
 \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}]{$\\x$};
 }`
);

fs.writeFileSync('constants.tsx', content);
