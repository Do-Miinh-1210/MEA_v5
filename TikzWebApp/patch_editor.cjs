const fs = require('fs');
let content = fs.readFileSync('components/Editor.tsx', 'utf8');

// 1. Change state
content = content.replace(
  "const [isLargeFont, setIsLargeFont] = useState(false);",
  "const [fontSize, setFontSize] = useState('normalsize');"
);

// 2. Change effect
content = content.replace(
  /if \(isGeneratingMessage\) \{\s*setIsLargeFont\(false\);\s*\}/,
  "if (isGeneratingMessage) {\n      setFontSize('normalsize');\n    }"
);

// 3. Change handler
const oldHandler = `  const handleToggleLargeFont = () => {
    const nextState = !isLargeFont;
    setIsLargeFont(nextState);
    if (!code.trim() || isReadOnly) return;
    if (nextState) {
      setCode(code.replace(/\\\\normalsize/g, '\\\\large'));
    } else {
      setCode(code.replace(/\\\\large/g, '\\\\normalsize'));
    }
  };`;
const newHandler = `  const handleFontSizeChange = (newSize: string) => {
    const oldSize = fontSize;
    setFontSize(newSize);
    if (!code.trim() || isReadOnly) return;
    // Replace old font size with new font size in the code
    const regex = new RegExp('\\\\\\\\' + oldSize, 'g');
    setCode(code.replace(regex, '\\\\' + newSize));
  };`;
content = content.replace(oldHandler, newHandler);

// 4. Change JSX
const oldJsx = `                      <label className="flex items-center ml-2 space-x-1 cursor-pointer select-none text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 px-1 py-1 rounded">
                        <input
                          type="checkbox"
                          className="w-3.5 h-3.5 accent-blue-600"
                          checked={isLargeFont}
                          onChange={handleToggleLargeFont}
                          disabled={isGeneratingMessage || isReadOnly}
                        />
                        <span className="text-sm">large</span>
                      </label>`;
const newJsx = `                      <div className="flex items-center ml-2 space-x-1 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 px-1 py-1 rounded" title="Chọn kích thước font chữ">
                        <span className="text-sm text-slate-700 dark:text-slate-300">Size</span>
                        <select
                          className="bg-transparent text-slate-700 dark:text-slate-300 text-sm cursor-pointer outline-none border-none focus:ring-0 disabled:opacity-50"
                          value={fontSize}
                          onChange={(e) => handleFontSizeChange(e.target.value)}
                          disabled={isGeneratingMessage || isReadOnly}
                        >
                          {['normalsize', 'large', 'Large', 'scriptsize', 'footnotesize', 'small'].map(size => (
                            <option key={size} value={size} className="bg-white dark:bg-slate-800">{size}</option>
                          ))}
                        </select>
                      </div>`;
content = content.replace(oldJsx, newJsx);

fs.writeFileSync('components/Editor.tsx', content);
