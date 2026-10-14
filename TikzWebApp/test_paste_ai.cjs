const fs = require('fs');
let code = fs.readFileSync('components/AIAssistant.tsx', 'utf8');

const regex = /const handlePaste = useCallback\(async \(e: React\.ClipboardEvent\) => \{\s*if \(!isReadOnly && e\.clipboardData\) \{\s*await processDataTransfer\(e\.clipboardData\);\s*\}\s*\}, \[processDataTransfer, isReadOnly\]\);/;

const replacement = `const handlePaste = useCallback(async (e: React.ClipboardEvent) => {
    if (!isReadOnly && e.clipboardData) {
      if (e.clipboardData.files && e.clipboardData.files.length > 0) {
        // Don't prevent default if there are files, actually we might want to prevent default so the filename doesn't get pasted as text
        e.preventDefault();
        await processFiles(e.clipboardData.files as any);
      } else {
        const text = e.clipboardData.getData('text');
        if (text) {
          const matches = text.match(/\\\\begin\\{tikzpicture\\}[\\s\\S]*?\\\\end\\{tikzpicture\\}/g);
          if (matches && matches.length > 1) {
            e.preventDefault();
            const newFiles = matches.map((content, idx) => ({
              type: 'text' as const,
              name: \`Pasted_Code_\${Date.now()}_\${idx + 1}.tex\`,
              content,
              file: new File([content], \`Pasted_Code_\${Date.now()}_\${idx + 1}.tex\`, { type: 'text/plain' })
            }));
            setInputFiles(prev => [...prev, ...newFiles]);
          }
        }
      }
    }
  }, [processFiles, isReadOnly]);`;

code = code.replace(regex, replacement);
fs.writeFileSync('components/AIAssistant.tsx', code);
