import fs from 'fs';
const content = fs.readFileSync('constants.tsx', 'utf8');
const lines = content.split('\n');
lines.forEach((line, i) => {
    if (line.includes('circle')) {
        console.log(`${i+1}: ${line.trim()}`);
    }
});
