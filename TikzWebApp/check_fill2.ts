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
    
    if (currentTopic.startsWith('1.1') || 
        currentTopic.startsWith('1.2') || 
        currentTopic.startsWith('1.3') || 
        currentTopic.startsWith('1.4') || 
        currentTopic.startsWith('1.5') || 
        currentTopic.startsWith('1.6')) {
        
        if (line.includes('circle') && line.includes('fill')) {
            console.log(`line ${i+1}: ${line.trim()}`);
            lines[i] = lines[i].replace(/fill=[a-zA-Z0-9_-]+/g, '');
            // Actually maybe I shouldn't naively replace `fill=` because the circle could be a filled path, not a point?
            // "Các điểm trong hình học không tô trắng" -> points are not white.
        }
    }
}
