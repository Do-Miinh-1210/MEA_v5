import fs from 'fs';
let content = fs.readFileSync('constants.tsx', 'utf8');

const t2 = "\\\\foreach \\\\x/\\\\goc/\\\\t in {\\n A/170/A, B/-90/B, C/-90/C, D/0/D,\\n A'/90/A', B'/90/B', C'/-25/C', D'/90/D'\\n }{\\n \\\\draw (\\\\x) circle (0.4pt) node[shift={(\\\\goc:9pt)}, font=\\\\normalsize]{$\\\\t$};\\n }";
const t2new = "\\\\foreach \\\\p/\\\\goc in {\\n A/170, B/-90, C/-90, D/0,\\n A'/90, B'/90, C'/-25, D'/90\\n }{\\n \\\\draw (\\\\p) circle (0.4pt) node[shift={(\\\\goc:9pt)}]{$\\\\p$};\\n }";

if (content.includes(t2)) {
  content = content.replace(t2, t2new);
  console.log("Replaced t2");
}

fs.writeFileSync('constants.tsx', content);
