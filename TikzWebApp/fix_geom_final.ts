import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');

// Find all indices of `name: `
const lines = content.split('\n');

let currentTopic = "";

for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    let matchTopic = line.match(/name:\s*'([^']+)'/);
    if (matchTopic) {
        currentTopic = matchTopic[1];
    }
    
    // Check if we are in geometry (1.1 -> 1.6)
    if (currentTopic.startsWith('1.1') || 
        currentTopic.startsWith('1.2') || 
        currentTopic.startsWith('1.3') || 
        currentTopic.startsWith('1.4') || 
        currentTopic.startsWith('1.5') || 
        currentTopic.startsWith('1.6')) {
        
        // Remove line join=round
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
    
    // Fix circle radius as well: geometry should be 0.4pt
    if (currentTopic.startsWith('1.1') || 
        currentTopic.startsWith('1.2') || 
        currentTopic.startsWith('1.3') || 
        currentTopic.startsWith('1.4') || 
        currentTopic.startsWith('1.5') || 
        currentTopic.startsWith('1.6')) {
        
        // Replace something like `circle (0.6pt)` with `circle (0.4pt)`
        // Wait, any circle (...pt) or circle(...) that represents A POINT.
        if (line.includes('circle')) {
            lines[i] = lines[i].replace(/circle\s*\([0-9.]+pt\)/g, 'circle (0.4pt)');
        }
    }
}

fs.writeFileSync('constants.tsx', lines.join('\n'));
console.log('Fixed constants.tsx');
