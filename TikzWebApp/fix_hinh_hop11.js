import fs from 'fs';
let content = fs.readFileSync('constants.tsx', 'utf8');

const strToFind = " \\foreach \\x/\\goc/\\t in {\\n A/170/A, B/-90/B, C/-90/C, D/0/D,\\n A'/90/A', B'/90/B', C'/-25/C', D'/90/D'\\n }{\\n \\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}, font=\\normalsize]{\\$\\t\\$};\\n }";
const t2new = " \\foreach \\p/\\goc in {\\n A/170, B/-90, C/-90, D/0,\\n A'/90, B'/90, C'/-25, D'/90\\n }{\\n \\draw (\\p) circle (0.4pt) node[shift={(\\goc:9pt)}]{\\$\\p\\$};\\n }";

// Let's do it by manipulating strings directly and handling all variations.
let idx = content.indexOf("C'/-25");
if (idx > 0) {
  let substart = content.lastIndexOf("\\foreach", idx);
  let subend = content.indexOf("}", idx);
  subend = content.indexOf("}", subend + 1); // wait, }{ => first }
  subend = content.indexOf("}", subend + 1); // next }
  // Replace that chunk with t2new
  content = content.substring(0, substart) + "\\foreach \\p/\\goc in {\\n A/170, B/-90, C/-90, D/0,\\n A'/90, B'/90, C'/-25, D'/90\\n }{\\n \\draw (\\p) circle (0.4pt) node[shift={(\\goc:9pt)}]{\\$\\p\\$};\\n }" + content.substring(subend + 1);
  console.log("Replaced chunk!");
}

fs.writeFileSync('constants.tsx', content);
