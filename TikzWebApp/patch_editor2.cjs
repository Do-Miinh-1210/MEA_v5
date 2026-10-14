const fs = require('fs');
let content = fs.readFileSync('components/Editor.tsx', 'utf8');

const newHandler = `  const handleFontSizeChange = (newSize: string) => {
    const oldSize = fontSize;
    setFontSize(newSize);
    if (!code.trim() || isReadOnly) return;
    // Replace old font size with new font size in the code
    const regex = new RegExp('\\\\\\\\\\\\b' + oldSize + '\\\\b', 'g');
    setCode(code.replace(regex, '\\\\' + newSize));
  };`;

content = content.replace(/  const handleToggleLargeFont = \(\) => \{[\s\S]*?\};\n/, newHandler + '\n');
fs.writeFileSync('components/Editor.tsx', content);
