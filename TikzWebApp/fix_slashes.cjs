const fs = require('fs');
let content = fs.readFileSync('services/geminiService.ts', 'utf8');

content = content.replace('\\draw[line width=0.6pt, smooth', '\\\\draw[line width=0.6pt, smooth');
content = content.replace('\\node[transform', '\\\\node[transform');
content = content.replace('\\draw[dashed, line width=0.6pt', '\\\\draw[dashed, line width=0.6pt');

fs.writeFileSync('services/geminiService.ts', content);
