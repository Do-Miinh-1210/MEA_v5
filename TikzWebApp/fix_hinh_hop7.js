import fs from 'fs';
let content = fs.readFileSync('constants.tsx', 'utf8');

// The block to replace:
const target1 = "A/170/A, B/-90/B, C/-90/C, D/0/D,\\n A1/90/A', B1/90/B', C1/90/C', D1/90/D'";
if (content.includes(target1)) {
  content = content.replace(target1, "A/170/A, B/-90/B, C/-90/C, D/0/D,\\n A'/90/A', B'/90/B', C'/-25/C', D'/90/D'");
}

const target2 = "\\\\foreach \\\\x in {A,B,C,D}{\\n \\\\path (\\\\x)++(90:h) coordinate (\\\\x1);\\n }";
if (content.includes(target2)) {
  content = content.replace(target2, "\\\\foreach \\\\x in {A,B,C,D}{\\n \\\\path (\\\\x)++(90:h) coordinate (\\\\x\');\\n }");
}

fs.writeFileSync('constants.tsx', content);
