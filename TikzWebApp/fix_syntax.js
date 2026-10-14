import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');
const lines = content.split('\n');

const startIdx = lines.findIndex(l => l.includes("name: '1.1. Tam giác'"));
const endIdx = lines.findIndex(l => l.includes("name: '1.5. Đa diện'"));

if (startIdx !== -1 && endIdx !== -1) {
    let rStart = startIdx;
    while(rStart > 0 && !lines[rStart].includes("{")) rStart--;
    
    let rEnd = endIdx;
    while(rEnd > 0 && !lines[rEnd].includes("{")) rEnd--;
    
    const before = lines.slice(0, rStart);
    const after = lines.slice(rEnd);
    fs.writeFileSync('constants.tsx', before.join('\n') + '\n' + after.join('\n'));
    console.log("Trimmed section between " + rStart + " and " + rEnd);
} else {
    console.log("Could not find start/end indices");
}
