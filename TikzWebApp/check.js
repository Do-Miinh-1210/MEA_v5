import fs from 'fs';
const content = fs.readFileSync('constants.tsx', 'utf8');

const idx = content.indexOf('A/170/A');
console.log("Index 1:", idx);
if (idx > 0) {
  console.log(content.substring(idx - 20, idx + 150));
}

const idx2 = content.indexOf("10. Hình hộp chữ nhật");
console.log("Index 2:", idx2);
if (idx2 > 0) {
  console.log(content.substring(idx2 - 20, idx2 + 600));
}
