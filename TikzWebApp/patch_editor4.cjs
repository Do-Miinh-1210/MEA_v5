const fs = require('fs');
let content = fs.readFileSync('components/Editor.tsx', 'utf8');

content = content.replace(/const regex = new RegExp\([^)]+\);/, "const regex = new RegExp('\\\\\\\\' + oldSize + '(?![a-zA-Z])', 'g');");

fs.writeFileSync('components/Editor.tsx', content);
