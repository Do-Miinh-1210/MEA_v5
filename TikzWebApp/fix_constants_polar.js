import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');

// Replace standard variables
content = content.replace(/\(a,\s*0\)/g, '(0:a)');
content = content.replace(/\(-a,\s*0\)/g, '(180:a)');
content = content.replace(/\(b,\s*0\)/g, '(0:b)');
content = content.replace(/\(-b,\s*0\)/g, '(180:b)');
content = content.replace(/\(c,\s*0\)/g, '(0:c)');
content = content.replace(/\(-c,\s*0\)/g, '(180:c)');

fs.writeFileSync('constants.tsx', content);
