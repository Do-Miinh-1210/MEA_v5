import fs from 'fs';

const TIKZ_SUGGESTIONS_STR = `
const TIKZ_SUGGESTIONS = [
  { label: '\\\\draw', insertText: '\\\\draw ' },
  { label: '\\\\fill', insertText: '\\\\fill ' },
  { label: '\\\\path', insertText: '\\\\path ' },
  { label: '\\\\node', insertText: '\\\\node[' },
  { label: '\\\\coordinate', insertText: '\\\\coordinate ' },
  { label: '\\\\begin{tikzpicture}', insertText: '\\\\begin{tikzpicture}[\\n  >=stealth, line join=round,\\n  every node/.style={font=\\\\normalsize}\\n]\\n  \\n\\\\end{tikzpicture}' },
  { label: '\\\\end{tikzpicture}', insertText: '\\\\end{tikzpicture}' },
  { label: '\\\\foreach', insertText: '\\\\foreach \\\\p/\\\\goc in {} {\\n  \\\\draw (\\\\p) circle (0.4pt) node[shift={(\\\\goc:9pt)}]{\\\\$\\\\p\\\\$};\\n}' },
  { label: 'circle', insertText: 'circle (0.4pt)' },
  { label: 'rectangle', insertText: 'rectangle ()' },
  { label: '\\\\tkzTabInit', insertText: '\\\\tkzTabInit[nocadre=false, lgt=1.2, espcl=2.5, deltacl=0.6]\\n  {$x$/0.7, $y$/2}\\n  {$-\\\\infty$, $+\\\\infty$}' },
  { label: '\\\\tkzTabLine', insertText: '\\\\tkzTabLine{, +, 0, -, }' },
  { label: 'every', insertText: 'every node/.style={font=\\\\normalsize}' },
  { label: 'line', insertText: 'line width=0.6pt' },
  { label: '-Stealth', insertText: '-Stealth' },
  { label: 'double', insertText: 'double distance=1pt, double=white, line width=0.4pt' },
  { label: 'pattern', insertText: 'pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray' },
  { label: 'shift', insertText: 'shift={(:9pt)}' },
  { label: '\\\\clip', insertText: '\\\\clip ' },
  { label: 'dashed', insertText: 'dashed, line width=0.4pt' },
];
`;

let content = fs.readFileSync('components/SmartEditor.tsx', 'utf8');

// Insert suggests array
content = content.replace("interface SmartEditorProps", TIKZ_SUGGESTIONS_STR + "\\ninterface SmartEditorProps");

// Update states
content = content.replace(
  "const [suggestions, setSuggestions] = useState<string[]>([]);",
  `const [suggestions, setSuggestions] = useState<typeof TIKZ_SUGGESTIONS>([]);
  const [activeSuggestion, setActiveSuggestion] = useState(0);
  const [currentPrefix, setCurrentPrefix] = useState("");`
);

// Add keydown handler
const handleKeyDownCapture = `
  const handleKeyDownCapture = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (suggestions.length > 0) {
      if (e.key === 'Tab' || e.key === 'Enter') {
        e.preventDefault();
        e.stopPropagation();
        applySuggestion(suggestions[activeSuggestion]);
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        e.stopPropagation();
        setActiveSuggestion((a) => (a + 1) % suggestions.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        e.stopPropagation();
        setActiveSuggestion((a) => (a - 1 + suggestions.length) % suggestions.length);
      } else if (e.key === 'Escape') {
        setSuggestions([]);
      }
    }
  };

  const applySuggestion = (sug: typeof TIKZ_SUGGESTIONS[0]) => {
    const activeEl = document.activeElement as HTMLTextAreaElement;
    const pos = activeEl ? activeEl.selectionStart : code.length;
    
    const textBefore = code.slice(0, pos);
    const textAfter = code.slice(pos);
    const prefixLength = currentPrefix.length;
    
    const newCode = textBefore.slice(0, -prefixLength) + sug.insertText + textAfter;
    
    setCode(newCode);
    setSuggestions([]);
    
    setTimeout(() => {
      if (activeEl) {
        let newPos = pos - prefixLength + sug.insertText.length;
        const cursorOffset1 = sug.insertText.indexOf('()');
        const cursorOffset2 = sug.insertText.indexOf('{}');
        if (cursorOffset1 !== -1) {
           newPos = pos - prefixLength + cursorOffset1 + 1;
        } else if (cursorOffset2 !== -1) {
           newPos = pos - prefixLength + cursorOffset2 + 1;
        } else if (sug.insertText.includes('\\n  \\n')) {
           newPos = pos - prefixLength + sug.insertText.indexOf('\\n  \\n') + 3;
        }
        activeEl.selectionStart = newPos;
        activeEl.selectionEnd = newPos;
        activeEl.focus();
      }
    }, 10);
  };
`;
content = content.replace("// Smart typing suggestions", handleKeyDownCapture + "\\n\\n  // Smart typing suggestions");

// Replacement for handleChange
const newHandleChange = `
  const handleChange = (newCode: string) => {
    setCode(newCode);
    
    const activeEl = document.activeElement as HTMLTextAreaElement;
    if (!activeEl || activeEl.tagName !== 'TEXTAREA') {
      setSuggestions([]);
      return;
    }
    
    const pos = activeEl.selectionStart;
    const textBefore = newCode.slice(0, pos);
    
    // Split to find the word being typed
    const parts = textBefore.split(/[ \\n\\t{}()[\\];,=\\/]/);
    const prefix = parts[parts.length - 1];

    if (prefix.length >= 2) {
      const matched = TIKZ_SUGGESTIONS.filter(s => 
        s.label.toLowerCase().startsWith(prefix.toLowerCase())
      ).slice(0, 8);
      
      if (matched.length > 0) {
        setSuggestions(matched);
        setCurrentPrefix(prefix);
        setActiveSuggestion(0);
      } else {
        setSuggestions([]);
      }
    } else {
      setSuggestions([]);
    }
  };
`;
content = content.replace(/const handleChange = \(newCode: string\) => \{[\s\S]*?\};\n/, Object.values({newHandleChange})[0] + "\\n");

// Replace return block
const UI = `
  return (
    <div className="relative flex-1 w-full h-full overflow-auto" onKeyDownCapture={handleKeyDownCapture}>
      <style>{\`
        .language-tikz .token.keyword { color: #008080 !important; }
        .language-tikz .token.class-name { color: #00BCD4 !important; }
        .language-tikz .token.string { color: #008000 !important; }
        .language-tikz .token.variable { color: #FF9800 !important; }
        .language-tikz .token.number { color: inherit !important; }
        .language-tikz .token.punctuation { color: #555555 !important; }
        .language-tikz .token.operator { color: #555555 !important; }
        .language-tikz .token.comment { color: #888888 !important; font-style: italic; }
        
        .dark .language-tikz .token.keyword { color: #4DB6AC !important; }
        .dark .language-tikz .token.class-name { color: #80DEEA !important; }
        .dark .language-tikz .token.string { color: #81C784 !important; }
        .dark .language-tikz .token.variable { color: #FFB74D !important; }
        .dark .language-tikz .token.number { color: inherit !important; }
        .dark .language-tikz .token.punctuation { color: #AAAAAA !important; }
        .dark .language-tikz .token.operator { color: #AAAAAA !important; }

        .smart-editor-container textarea, .smart-editor-container pre {
          white-space: pre-wrap !important;
          word-break: break-word !important;
          overflow-wrap: anywhere !important;
        }
      \`}</style>
      <Editor
        value={code}
        onValueChange={handleChange}
        highlight={highlightCode}
        padding={16}
        readOnly={isReadOnly}
        className="smart-editor-container font-mono text-[11pt] min-h-full bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200 focus:outline-none"
        style={{
          fontFamily: '"JetBrains Mono", "Fira Code", monospace',
        }}
        textareaClassName="focus:outline-none"
      />
      {suggestions.length > 0 && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white dark:bg-slate-800 border border-cyan-500 rounded-xl shadow-2xl p-2 z-50 min-w-[260px] max-w-[400px]">
          <div className="flex justify-between items-center px-1 mb-2 border-b border-slate-200 dark:border-slate-700 pb-1">
            <span className="text-[10px] font-semibold tracking-wider uppercase text-slate-400">Gợi ý code</span>
            <span className="text-[10px] text-slate-400">Tab / Enter</span>
          </div>
          <div className="flex flex-col gap-1">
            {suggestions.map((sug, i) => (
              <button
                key={i}
                className={\`block w-full text-left px-3 py-1.5 text-sm font-mono rounded transition-colors \${i === activeSuggestion ? 'bg-cyan-100 dark:bg-cyan-900/60 text-cyan-800 dark:text-cyan-200' : 'hover:bg-slate-50 dark:hover:bg-slate-700/50 text-slate-700 dark:text-slate-300'}\`}
                onClick={() => applySuggestion(sug)}
              >
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{sug.label}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
`;
content = content.replace(/return \(\s*<div className="relative flex-1[\s\S]*\);\s*\};/m, UI + "\\n};");

fs.writeFileSync('components/SmartEditor.tsx', content);
