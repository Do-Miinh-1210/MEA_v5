import fs from 'fs';
let content = fs.readFileSync('constants.tsx', 'utf8');

// I'll revert it back to standard text by finding the exact block first.
let idx = content.indexOf("A/170, B/-90, C/-90, D/0,\\n A'/90, B'/90, C'/-25, D'/90");
if (idx > 0) {
  let substart = content.lastIndexOf("\\foreach", idx);
  let subend = content.indexOf(";", idx); // wait, "};" or ";\n }"
  subend = content.indexOf("}", subend);
  
  content = content.substring(0, substart) + "\\\\foreach \\\\p/\\\\goc in {\\n A/170, B/-90, C/-90, D/0,\\n A'/90, B'/90, C'/-25, D'/90\\n }{\\n \\\\draw (\\\\p) circle (0.4pt) node[shift={(\\\\goc:9pt)}]{\\\\\$\\\\p\\\\\$\};\\n }" + content.substring(subend + 1);
  console.log("Replaced chunk correctly!");
}

fs.writeFileSync('constants.tsx', content);
