import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');
const lines = content.split('\n');
let currentTopic = "";

for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    let matchTopic = line.match(/name:\s*'([^']+)'/);
    if (matchTopic) {
        currentTopic = matchTopic[1];
    }
    
    if (currentTopic === '1.7. Bảng biến thiên') {
        if (line.includes('line join=round')) {
            lines[i] = lines[i].replace(/,\s*line join=round/g, '')
                               .replace(/line join=round,\s*/g, '')
                               .replace(/line join=round/g, '');
        }
        if (line.includes('')) {
            lines[i] = lines[i].replace(/,\s*/g, '')
                               .replace(/\s*/g, '')
                               .replace(//g, '');
        }
    }
}

fs.writeFileSync('constants.tsx', lines.join('\n'));
console.log('Fixed constants.tsx');
