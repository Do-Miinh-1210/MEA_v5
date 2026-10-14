const fs = require('fs');
let code = fs.readFileSync('components/ImportModal.tsx', 'utf8');

const regex = /const text = e\.clipboardData\.getData\('text'\);\s*if \(text\) \{\s*setFiles\(prev => \[\.\.\.prev, \{ name: \`Pasted_Code_\$\{Date\.now\(\)\}\.tex\`, content: text \}\]\);\s*\}/;

const replacement = `const text = e.clipboardData.getData('text');
      if (text) {
        const matches = text.match(/\\\\begin\\{tikzpicture\\}[\\s\\S]*?\\\\end\\{tikzpicture\\}/g);
        if (matches && matches.length > 1) {
          const newFiles = matches.map((content, idx) => ({
            name: \`Pasted_Code_\${Date.now()}_\${idx + 1}.tex\`,
            content
          }));
          setFiles(prev => [...prev, ...newFiles]);
        } else {
          setFiles(prev => [...prev, { name: \`Pasted_Code_\${Date.now()}.tex\`, content: text }]);
        }
      }`;

code = code.replace(regex, replacement);
fs.writeFileSync('components/ImportModal.tsx', code);
