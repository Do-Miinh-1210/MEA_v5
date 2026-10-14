const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

content = content.replace(/<div className="border-t border-slate-200 dark:border-slate-700 my-1"><\/div>[\s\S]*?\}\)\]\}[\s\S]*?<\/div>/, '</div>');
content = content.replace(/const \[fontSize, setFontSize\] = useState<string>\('normalsize'\);\n\s*/, '');
content = content.replace(/\/\/ Set Font Size[\s\S]*?next = next\.replace\(\/every node\[\s\S]*?\);\n/, '');
content = content.replace(/, fontSize\]\);/, ']');

fs.writeFileSync('App.tsx', content);
