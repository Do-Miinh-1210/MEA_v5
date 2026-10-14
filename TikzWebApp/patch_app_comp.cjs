const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

// 1. Add state
const stateOld = `  const [isFunctionHidden, setIsFunctionHidden] = useState<boolean>(true);`;
const stateNew = `  const [isFunctionHidden, setIsFunctionHidden] = useState<boolean>(true);\n  const [isComponentFunctionHidden, setIsComponentFunctionHidden] = useState<boolean>(true);`;
content = content.replace(stateOld, stateNew);

// 2. Add replace logic
const replaceOld = `      // Toggle Function Graph Labels
      if (isFunctionHidden) {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1% $3");
        });
      } else {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1$3");
        });
      }`;
const replaceNew = `      // Toggle Function Graph Labels
      if (isFunctionHidden) {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1% $3");
        });
      } else {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1$3");
        });
      }

      // Toggle Component Function Labels
      if (isComponentFunctionHidden) {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ THÀNH PHẦN ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1% $3");
        });
      } else {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ THÀNH PHẦN ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1$3");
        });
      }`;
content = content.replace(replaceOld, replaceNew);

// 3. Add checkbox
const checkboxOld = `                <label className={\`flex items-center px-3 py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 \${!currentCode?.includes('% --- ĐỒ THỊ HÀM SỐ ---') ? 'opacity-50 cursor-not-allowed' : ''}\`}>
                  <input
                    type="checkbox"
                    className="mr-2 cursor-pointer rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    checked={!isFunctionHidden}
                    onChange={() => setIsFunctionHidden(!isFunctionHidden)}
                    disabled={!currentCode?.includes('% --- ĐỒ THỊ HÀM SỐ ---')}
                  />
                  <span className="text-slate-700 dark:text-slate-300">Nhãn hàm số</span>
                </label>
              </div>
            )}
          </div>`;
const checkboxNew = `                <label className={\`flex items-center px-3 py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 \${!currentCode?.includes('% --- ĐỒ THỊ HÀM SỐ ---') ? 'opacity-50 cursor-not-allowed' : ''}\`}>
                  <input
                    type="checkbox"
                    className="mr-2 cursor-pointer rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    checked={!isFunctionHidden}
                    onChange={() => setIsFunctionHidden(!isFunctionHidden)}
                    disabled={!currentCode?.includes('% --- ĐỒ THỊ HÀM SỐ ---')}
                  />
                  <span className="text-slate-700 dark:text-slate-300">Nhãn hàm số</span>
                </label>
                <label className={\`flex items-center px-3 py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 \${!currentCode?.includes('% --- ĐỒ THỊ HÀM SỐ THÀNH PHẦN ---') ? 'opacity-50 cursor-not-allowed' : ''}\`}>
                  <input
                    type="checkbox"
                    className="mr-2 cursor-pointer rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    checked={!isComponentFunctionHidden}
                    onChange={() => setIsComponentFunctionHidden(!isComponentFunctionHidden)}
                    disabled={!currentCode?.includes('% --- ĐỒ THỊ HÀM SỐ THÀNH PHẦN ---')}
                  />
                  <span className="text-slate-700 dark:text-slate-300">Nhãn hàm số TP</span>
                </label>
              </div>
            )}
          </div>`;
content = content.replace(checkboxOld, checkboxNew);

fs.writeFileSync('App.tsx', content);
