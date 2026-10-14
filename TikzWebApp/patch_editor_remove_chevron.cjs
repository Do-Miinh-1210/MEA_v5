const fs = require('fs');
let content = fs.readFileSync('components/Editor.tsx', 'utf8');

const oldStr = `                  <div className="flex items-center">
                      <button 
                        onClick={() => setIsEditorVisible(!isEditorVisible)}
                        className="flex items-center gap-1.5 text-yellow-500 dark:text-yellow-400 font-medium text-base hover:bg-slate-200 dark:hover:bg-slate-700 px-2 py-1 rounded-md whitespace-nowrap"
                      >
                          {isEditorVisible ? <ChevronDownIcon className="h-4 w-4" /> : <ChevronUpIcon className="h-4 w-4" />}
                      </button>
                      <span className="text-slate-300 dark:text-slate-600 mx-1">|</span>`;
const newStr = `                  <div className="flex items-center">`;
content = content.replace(oldStr, newStr);

fs.writeFileSync('components/Editor.tsx', content);
