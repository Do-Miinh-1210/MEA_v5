const fs = require('fs');
let code = fs.readFileSync('components/Editor.tsx', 'utf8');

code = code.replace(/if \(setIsBbtNoFrame\) setIsBbtNoFrame\(!thisShouldBeReplacedLater\);/, 'if (setIsBbtNoFrame) setIsBbtNoFrame(!isBbtNoFrame);');
code = code.replace(/if \(setIsAsymptoteHidden\) setIsAsymptoteHidden\(!thisShouldBeReplacedLater\);/, 'if (setIsAsymptoteHidden) setIsAsymptoteHidden(!isAsymptoteHidden);');
code = code.replace(/if \(setIsFunctionHidden\) setIsFunctionHidden\(!thisShouldBeReplacedLater\);/, 'if (setIsFunctionHidden) setIsFunctionHidden(!isFunctionHidden);');
code = code.replace(/if \(setIsComponentFunctionHidden\) setIsComponentFunctionHidden\(!thisShouldBeReplacedLater\);/, 'if (setIsComponentFunctionHidden) setIsComponentFunctionHidden(!isComponentFunctionHidden);');

fs.writeFileSync('components/Editor.tsx', code);
