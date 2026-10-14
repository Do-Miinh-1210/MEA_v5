import fs from 'fs';
const content = fs.readFileSync('constants.tsx', 'utf8');

const regex = /id:\s*'([^']+)'[\s\S]*?(line join=round)[\s\S]*?}/g;
let match;
while ((match = regex.exec(content)) !== null) {
    // console.log("id:", match[1]);
}

// Just match all tikzpactures with line join=round and print some context
const lines = content.split('\n');
for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('line join=round')) {
        console.log(`line ${i+1}: ${lines[i].substring(0, 100)}`);
    }
}
