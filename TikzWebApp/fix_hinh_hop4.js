import fs from 'fs';
let content = fs.readFileSync('constants.tsx', 'utf8');

// Replace standard box 10.
content = content.replace(
  /\\foreach \\x\/\\goc\/\\t in \{\\n A\/170\/A, B\/-90\/B, C\/-90\/C, D\/0\/D,\\n A1\/90\/A', B1\/90\/B', C1\/90\/C', D1\/90\/D'\\n \}\{\\n \\draw \(\\x\) circle \(0\.4pt\) node\[shift=\{\(\\goc:9pt\)\}, font=\\normalsize\]\{\$\\t\$\};\\n \}/g,
  "\\foreach \\p\/\\goc in {\\n A\/170, B\/-90, C\/-90, D\/0,\\n A'\/90, B'\/90, C'\/-25, D'\/90\\n }{\\n \\draw (\\p) circle (0.4pt) node[shift={(\\goc:9pt)}]{$\\p$};\\n }"
);

// We must also rename `\x1` to `\x'` in the first foreach.
content = content.replace(
  /\\foreach \\x in \{A,B,C,D\}\{\\n \\path \(\\x\)\+\+\(90:h\) coordinate \(\\x1\);\\n \}/g,
  "\\foreach \\x in {A,B,C,D}{\\n \\path (\\x)++(90:h) coordinate (\\x');\\n }"
);

fs.writeFileSync('constants.tsx', content);
