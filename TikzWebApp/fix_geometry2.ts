import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');

// The JSON parsed string needs to correctly match literal \d. Actually /circle\s*\([\d.]+pt\)/g is correct for both since it's a JS regex object!
const jsonRegex = /"code":\s*"([\s\S]*?)"/g;
content = content.replace(jsonRegex, (match, p1) => {
    let unescaped = p1.replace(/\\n/g, '\n').replace(/\\\\/g, '\\');
    const isGraph = unescaped.includes('plot') || unescaped.includes('f(\\x)') || unescaped.includes('tkzTabInit');
    
    if (!isGraph) {        
        p1 = p1.replace(/circle\\s*\\([\\d.]+pt\\)/g, 'circle (0.4pt)');
        p1 = p1.replace(/circle\s*\([\d.]+pt\)/g, 'circle (0.4pt)');
    }
    
    return `"code": "${p1}"`;
});

fs.writeFileSync('constants.tsx', content);
console.log('Fixed geometry again');
