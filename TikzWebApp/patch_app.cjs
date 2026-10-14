const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

content = content.replace(
  /isBbtNoFrame=\{isBbtNoFrame\}\s*\/>/,
  `isBbtNoFrame={isBbtNoFrame}
          setIsBbtNoFrame={setIsBbtNoFrame}
          isAsymptoteHidden={isAsymptoteHidden}
          setIsAsymptoteHidden={setIsAsymptoteHidden}
          isFunctionHidden={isFunctionHidden}
          setIsFunctionHidden={setIsFunctionHidden}
          isComponentFunctionHidden={isComponentFunctionHidden}
          setIsComponentFunctionHidden={setIsComponentFunctionHidden}
        />`
);

// Remove the options menu from App.tsx
content = content.replace(
  /\{\/\* Tùy chọn Options Menu \*\/\}[^]+?(?=\{\/\* API Key Input \*\/)/,
  ''
);

// Remove the showOptionsMenu state from App.tsx
content = content.replace(
  /const \[showOptionsMenu, setShowOptionsMenu\] = useState<boolean>\(false\);\n/,
  ''
);

fs.writeFileSync('App.tsx', content);
