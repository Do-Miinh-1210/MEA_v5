const fs = require('fs');
let code = fs.readFileSync('components/AIAssistant.tsx', 'utf8');
code = code.replace(/BXD\s*<\/label>/, 'TikZ\n            </label>');
fs.writeFileSync('components/AIAssistant.tsx', code);
