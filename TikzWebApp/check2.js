import fs from 'fs';
const content = fs.readFileSync('constants.tsx', 'utf8');
const idx = content.indexOf("C'/-25");
console.log(content.substring(idx - 60, idx + 150));
