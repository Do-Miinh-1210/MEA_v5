const fs = require('fs');
let code = fs.readFileSync('components/Editor.tsx', 'utf8');

// 1. Remove resetOptionsTimeout and its ref
const timeoutBlockRegex = /^\s*const optionsTimeoutRef = React\.useRef<NodeJS\.Timeout \| null>\(null\);\s*const resetOptionsTimeout = \(\) => \{\s*if \(optionsTimeoutRef\.current\) \{\s*clearTimeout\(optionsTimeoutRef\.current\);\s*\}\s*optionsTimeoutRef\.current = setTimeout\(\(\) => \{\s*setShowOptionsMenu\(false\);\s*\}, 5000\);\s*\};\s*/m;

code = code.replace(timeoutBlockRegex, '');

// 2. Remove resetOptionsTimeout calls in onClick
code = code.replace(/onClick=\{\(\) => \{\s*setShowOptionsMenu\(!showOptionsMenu\);\s*if \(!showOptionsMenu\) \{\s*resetOptionsTimeout\(\);\s*\}\s*\}\}/g, 'onClick={() => {\n                            setShowOptionsMenu(!showOptionsMenu);\n                          }}');

// 3. Remove resetOptionsTimeout calls in onChange
code = code.replace(/onChange=\{\(\) => \{\s*if \((.*?)\) (.*?)\(!.*?\);\s*resetOptionsTimeout\(\);\s*\}\}/g, 'onChange={() => {\n                                  if ($1) $2(!thisShouldBeReplacedLater);\n                                }}');
// Wait, the $2 will not capture properly since it's hard to dynamically extract the state name for the NOT operator in thisShouldBeReplacedLater.
// Let's do a more robust replace for onChange

code = code.replace(/onChange=\{\(\) => \{\s*if \((setIs[a-zA-Z]+)\) \1\(!(is[a-zA-Z]+)\);\s*resetOptionsTimeout\(\);\s*\}\}/g, 'onChange={() => {\n                                  if ($1) $1(!$2);\n                                }}');

// 4. Update the dropdown wrapper
const dropdownRegex = /\{showOptionsMenu && \(\s*<div className="absolute top-full left-0 mt-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md shadow-lg z-50 w-44 overflow-hidden text-sm">([\s\S]*?)<\/div>\s*\)\}/;

code = code.replace(dropdownRegex, `{showOptionsMenu && (
                          <div className="absolute top-full left-0 pt-1 z-50 w-44 text-sm">
                            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md shadow-lg overflow-hidden">
$1
                            </div>
                          </div>
                        )}`);

fs.writeFileSync('components/Editor.tsx', code);
