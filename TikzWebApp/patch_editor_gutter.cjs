const fs = require('fs');
let content = fs.readFileSync('components/SmartEditor.tsx', 'utf8');

const oldCss = `        .smart-editor-container textarea, .smart-editor-container pre {
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
        }`;

const newCss = `        .smart-editor-container {
          position: relative;
        }

        .smart-editor-container::before {
          content: "";
          position: absolute;
          top: 0;
          left: 0;
          width: 44px;
          height: 100%;
          background-color: #f8fafc;
          border-right: 1px solid #e2e8f0;
          z-index: 0;
          pointer-events: none;
        }
        
        .dark .smart-editor-container::before {
          background-color: #0f172a;
          border-right: 1px solid #1e293b;
        }

        .smart-editor-container textarea, .smart-editor-container pre {
          white-space: pre-wrap !important;
          word-break: break-word !important;
          overflow-wrap: anywhere !important;
          padding-left: 48px !important;
        }
        
        .editor-line {
          position: relative;
          z-index: 1;
        }
        
        .editor-line::before {
          content: attr(data-line);
          position: absolute;
          left: -40px;
          width: 32px;
          text-align: right;
          color: #64748b;
          user-select: none;
          font-size: 0.9em;
          font-weight: 500;
          pointer-events: none;
        }
        
        .dark .editor-line::before {
          color: #94a3b8;
        }`;

content = content.replace(oldCss, newCss);
fs.writeFileSync('components/SmartEditor.tsx', content);
