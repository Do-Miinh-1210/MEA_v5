import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');
const lines = content.split('\n');
let currentTopic = "";
let found = 0;

for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    let matchTopic = line.match(/name:\s*'([^']+)'/);
    if (matchTopic) {
        currentTopic = matchTopic[1];
    }
    
    if (currentTopic === '1.7. Bảng biến thiên') {
        if (line.includes('line join=round') || line.includes('')) {
            console.log(`Found line join/cap=round in Bảng biến thiên at line ${i+1}`);
            found++;
        }
    }
}
if (found === 0) console.log("Clean!");
