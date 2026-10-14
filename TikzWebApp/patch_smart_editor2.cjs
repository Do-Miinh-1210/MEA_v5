const fs = require('fs');
let content = fs.readFileSync('components/SmartEditor.tsx', 'utf8');

const oldCode = `    // Add line numbers by wrapping each line in a span
    const lines = highlighted.split('\\n');
    highlighted = lines.map((line, i) => \`<span class="editor-line" data-line="\${i + 1}">\${line}</span>\`).join('\\n');`;

const newCode = `    // Add line numbers by wrapping each line in a span, preserving open tags
    const lines = highlighted.split('\\n');
    let openTags: string[] = [];
    
    highlighted = lines.map((line, i) => {
      let prefix = openTags.join('');
      
      const tagRegex = /<\\/?([a-z0-9]+)[^>]*>/gi;
      let match;
      while ((match = tagRegex.exec(line)) !== null) {
        if (match[0].startsWith('</')) {
          openTags.pop();
        } else if (!match[0].endsWith('/>')) {
          openTags.push(match[0]);
        }
      }
      
      let suffix = openTags.slice().reverse().map(tag => {
        const tagMatch = tag.match(/<([a-z0-9]+)/i);
        const tagName = tagMatch ? tagMatch[1] : 'span';
        return \`</\${tagName}>\`;
      }).join('');
      
      return \`<span class="editor-line" data-line="\${i + 1}">\${prefix}\${line}\${suffix}</span>\`;
    }).join('\\n');`;

content = content.replace(oldCode, newCode);

fs.writeFileSync('components/SmartEditor.tsx', content);
