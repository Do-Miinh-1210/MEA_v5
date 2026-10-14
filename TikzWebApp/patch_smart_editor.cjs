const fs = require('fs');
let content = fs.readFileSync('components/SmartEditor.tsx', 'utf8');

// 1. Add line wrapping to highlightCode
content = content.replace(
  /    return highlighted;\n  \}, \[searchQuery\]\);/,
  `    // Add line numbers by wrapping each line in a span
    const lines = highlighted.split('\\n');
    highlighted = lines.map((line, i) => \`<span class="editor-line" data-line="\${i + 1}">\${line}</span>\`).join('\\n');
    
    return highlighted;
  }, [searchQuery]);`
);

// 2. Add CSS rules
content = content.replace(
  /        \.smart-editor-container textarea, \.smart-editor-container pre \{\n          white-space: pre-wrap !important;\n          word-break: break-word !important;\n          overflow-wrap: anywhere !important;\n        \}/,
  `        .smart-editor-container textarea, .smart-editor-container pre {
          white-space: pre-wrap !important;
          word-break: break-word !important;
          overflow-wrap: anywhere !important;
          padding-left: 48px !important;
        }
        
        .editor-line {
          position: relative;
        }
        
        .editor-line::before {
          content: attr(data-line);
          position: absolute;
          left: -40px;
          width: 32px;
          text-align: right;
          color: #94a3b8; /* slate-400 */
          user-select: none;
          font-size: 0.9em;
          opacity: 0.8;
          pointer-events: none;
        }
        
        .dark .editor-line::before {
          color: #64748b; /* slate-500 */
        }`
);

fs.writeFileSync('components/SmartEditor.tsx', content);
