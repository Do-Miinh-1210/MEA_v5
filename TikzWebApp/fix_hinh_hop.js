import fs from 'fs';
let content = fs.readFileSync('constants.tsx', 'utf8');

// Replace A1 with A' coordinates generation
content = content.replace(/\\foreach \\x in \{A,B,C,D\}\{\\n\s*\\path \(\\x\)\+\+\(90:h\) coordinate \(\\x1\);\\n\s*\}/g, 
  "\\foreach \\x in {A,B,C,D}{\\n \\path (\\x)++(90:h) coordinate (\\x\');\\n }");

// Replace manual usages of A1, B1, C1, D1
content = content.replace(/\(A1\)/g, "(A')")
                 .replace(/\(B1\)/g, "(B')")
                 .replace(/\(C1\)/g, "(C')")
                 .replace(/\(D1\)/g, "(D')");

content = content.replace(/\\foreach \\x\/\\goc\/\\t in \{\n\s*A\/45\/A, B\/-90\/B, C\/-90\/C, D\/0\/D,\n\s*A'\/90\/A', B'\/90\/B', C'\/90\/C', D'\/90\/D'\n\s*\}/g,
  "\\foreach \\x\/\\goc in {\n A\/170, B\/-90, C\/-90, D\/0,\n A'\/90, B'\/90, C'\/-25, D'\/90\n }");

content = content.replace(/\\foreach \\x\/\\goc\/\\t in \{\n\s*A\/170\/A, B\/-90\/B, C\/-90\/C, D\/0\/D,\n\s*A'\/90\/A', B'\/90\/B', C'\/90\/C', D'\/90\/D'\n\s*\}/g,
  "\\foreach \\x\/\\goc in {\n A\/170, B\/-90, C\/-90, D\/0,\n A'\/90, B'\/90, C'\/-25, D'\/90\n }");

content = content.replace(/\\draw \(\\x\) circle \(0\.4pt\) node\[shift=\{\(\\goc:9pt\)\}, font=\\normalsize\]\{\$\\t\$\};/g,
  "\\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}]{\\$\\x\\$};");
  
content = content.replace(/\\draw \(\\x\) circle \(0\.4pt\) node\[shift=\{\(\\goc:9pt\)\}\]\{\$\\t\$\};/g,
  "\\draw (\\x) circle (0.4pt) node[shift={(\\goc:9pt)}]{\\$\\x\\$};");

fs.writeFileSync('constants.tsx', content);
console.log("Replaced 3 variable foreach to 2 variable foreach for Box shapes.");
