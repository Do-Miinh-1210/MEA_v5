const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

// 1. Add state
const stateOld = `  const [isComponentFunctionHidden, setIsComponentFunctionHidden] = useState<boolean>(true);`;
const stateNew = `  const [isComponentFunctionHidden, setIsComponentFunctionHidden] = useState<boolean>(true);\n  const [fontSize, setFontSize] = useState<string>('normalsize');`;
content = content.replace(stateOld, stateNew);

// 2. Add replace logic in useEffect
const useEffectOld = `      // Toggle Component Function Labels
      if (isComponentFunctionHidden) {`;
const useEffectNew = `      // Set Font Size
      next = next.replace(/every node\\/\\.style=\\{font=\\\\[a-zA-Z]+\\}/g, 'every node/.style={font=\\\\' + fontSize + '}');

      // Toggle Component Function Labels
      if (isComponentFunctionHidden) {`;
content = content.replace(useEffectOld, useEffectNew);

// 3. Fix dependency array
const depOld = `  }, [isBbtNoFrame, isAsymptoteHidden, isFunctionHidden]);`;
const depNew = `  }, [isBbtNoFrame, isAsymptoteHidden, isFunctionHidden, isComponentFunctionHidden, fontSize]);`;
content = content.replace(depOld, depNew);

// 4. Add the Size options in the dropdown
const menuOld = `                  <span className="text-slate-700 dark:text-slate-300">Nhãn hàm số thành phần</span>
                </label>
              </div>
            )}`;
const menuNew = `                  <span className="text-slate-700 dark:text-slate-300">Nhãn hàm số thành phần</span>
                </label>
                <div className="border-t border-slate-200 dark:border-slate-700 my-1"></div>
                <div className="px-3 py-1 text-xs font-semibold text-slate-500 uppercase tracking-wider">Size</div>
                {['normalsize', 'large', 'Large', 'scriptsize', 'footnotesize', 'small'].map(size => (
                  <label key={size} className="flex items-center px-3 py-1.5 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700">
                    <input
                      type="radio"
                      name="fontSize"
                      className="mr-2 cursor-pointer text-teal-600 focus:ring-teal-500 border-slate-300"
                      checked={fontSize === size}
                      onChange={() => setFontSize(size)}
                    />
                    <span className="text-slate-700 dark:text-slate-300 text-xs">\\{size}</span>
                  </label>
                ))}
              </div>
            )}`;
content = content.replace(menuOld, menuNew);

fs.writeFileSync('App.tsx', content);
