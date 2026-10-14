const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

// Revert 1. Add state
const stateNew = `  const [isComponentFunctionHidden, setIsComponentFunctionHidden] = useState<boolean>(true);\n  const [fontSize, setFontSize] = useState<string>('normalsize');`;
const stateOld = `  const [isComponentFunctionHidden, setIsComponentFunctionHidden] = useState<boolean>(true);`;
content = content.replace(stateNew, stateOld);

// Revert 2. Add replace logic in useEffect
const useEffectNew = `      // Set Font Size\n      next = next.replace(/every node\\/\\.style=\\{\\s*font\\s*=\\s*\\\\[a-zA-Z]+\\s*\\}/g, 'every node/.style={font=\\\\' + fontSize + '}');\n\n      // Toggle Component Function Labels\n      if (isComponentFunctionHidden) {`;
const useEffectOld = `      // Toggle Component Function Labels\n      if (isComponentFunctionHidden) {`;
content = content.replace(useEffectNew, useEffectOld);

// Revert 3. Fix dependency array
const depNew = `  }, [isBbtNoFrame, isAsymptoteHidden, isFunctionHidden, isComponentFunctionHidden, fontSize]);`;
const depOld = `  }, [isBbtNoFrame, isAsymptoteHidden, isFunctionHidden, isComponentFunctionHidden]);`;
content = content.replace(depNew, depOld);

// Revert 4. Add the Size options in the dropdown
const menuNew = `                  <span className="text-slate-700 dark:text-slate-300">Nhãn hàm số thành phần</span>\n                </label>\n                <div className="border-t border-slate-200 dark:border-slate-700 my-1"></div>\n                <div className="px-3 py-1 text-xs font-semibold text-slate-500 uppercase tracking-wider">Size</div>\n                {['normalsize', 'large', 'Large', 'scriptsize', 'footnotesize', 'small'].map(size => (\n                  <label key={size} className="flex items-center px-3 py-1.5 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700">\n                    <input\n                      type="radio"\n                      name="fontSize"\n                      className="mr-2 cursor-pointer text-teal-600 focus:ring-teal-500 border-slate-300"\n                      checked={fontSize === size}\n                      onChange={() => setFontSize(size)}\n                    />\n                    <span className="text-slate-700 dark:text-slate-300 text-xs">\\\\{size}</span>\n                  </label>\n                ))}\n              </div>\n            )}`;
const menuOld = `                  <span className="text-slate-700 dark:text-slate-300">Nhãn hàm số thành phần</span>\n                </label>\n              </div>\n            )}`;
content = content.replace(menuNew, menuOld);

fs.writeFileSync('App.tsx', content);
