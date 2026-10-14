import fs from 'fs';
const content = fs.readFileSync('constants.tsx', 'utf8');

// Also remove from templates that use `\plot` just in case? No, the prompt differentiates graph from geometry.
// Let's count occurrences of line join=round in constants.tsx
let count = (content.match(/line join=round/g) || []).length;
console.log('line join=round count:', count);
let circle08 = (content.match(/circle \(0.8pt\)/g) || []).length;
console.log('circle 0.8pt count:', circle08);
let circle06 = (content.match(/circle \(0.6pt\)/g) || []).length;
console.log('circle 0.6pt count:', circle06);
let circle04 = (content.match(/circle \(0.4pt\)/g) || []).length;
console.log('circle 0.4pt count:', circle04);
