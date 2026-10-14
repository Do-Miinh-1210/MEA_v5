import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');

// Replace line join=round
// For anything except graphs, we remove this.
// A simple way is to remove these from ALL tikzpicture definitions if they don't contain 'plot' or 'tkzTab' or whatever.
// But actually, line join=round is perfectly fine in graphs, but forbidden for square-ish geometries.
// We'll iterate through all tikzpicture definitions in the file.
// Or we can just use regex over the whole file, maybe check if the template has `plot` in it.
// Even better, just replace circle (0.8pt) and circle (0.6pt) and circle (1.2pt) etc with circle (0.4pt)
// EXCEPT where it's specifically a plot explicitly.
// But the prompt says "Các điểm trong hình học không tô trắng...".
// Let's just remove "line join=round" and "" if they appear in any scope/tikzpicture EXCEPT graphs.
// I will parse the 'code:' blocks.

const regex = /code:\s*`([\s\S]*?)`/g;

content = content.replace(regex, (match, p1) => {
    let result = p1;
    // Check if it's a geometric drawing (not graph)
    const isGraph = result.includes('plot') || result.includes('f(\\x)') || result.includes('tkzTabInit');
    
    if (!isGraph) {
        // remove line join and line cap variations
        result = result.replace(/,\s*line join=round/g, '');
        result = result.replace(/line join=round,\s*/g, '');
        result = result.replace(/line join=round/g, '');
        result = result.replace(/,\s*/g, '');
        result = result.replace(/\s*/g, '');
        result = result.replace(//g, '');
        
        // replace point circles: circle (\d.\dpt) or circle (\dpt) to circle (0.4pt)
        // usually \draw[something] (\t) circle (0.8pt) or \fill (...) circle (0.8pt)
        result = result.replace(/circle\s*\([\d.]+pt\)/g, 'circle (0.4pt)');
        
        // make sure there's no \fill[white] inside points if possible.
        // Actually, the easiest way is to enforce it per the user prompt.
    }
    
    return "code: `" + result + "`";
});

// Also there are some json templates with "code": "..."
const jsonRegex = /"code":\s*"([\s\S]*?)"/g;
content = content.replace(jsonRegex, (match, p1) => {
    let unescaped = p1.replace(/\\n/g, '\n').replace(/\\\\/g, '\\');
    const isGraph = unescaped.includes('plot') || unescaped.includes('f(\\x)') || unescaped.includes('tkzTabInit');
    
    if (!isGraph) {
        p1 = p1.replace(/,\\s*line join=round/g, '');
        p1 = p1.replace(/line join=round,\\s*/g, '');
        p1 = p1.replace(/line join=round/g, '');
        p1 = p1.replace(/,\\s*/g, '');
        p1 = p1.replace(/\\s*/g, '');
        p1 = p1.replace(//g, '');
        
        p1 = p1.replace(/circle\s*\([\\d.]+pt\)/g, 'circle (0.4pt)');
    }
    
    return `"code": "${p1}"`;
});

// Write it back
fs.writeFileSync('constants.tsx', content);
console.log('Fixed geometry templates in constants.tsx');
