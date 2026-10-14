const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

content = content.replace(
  /\(\?=\\n\\s\*\(\?:% ---\|\$\)\)/g, 
  '(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$)'
);

fs.writeFileSync('App.tsx', content);
