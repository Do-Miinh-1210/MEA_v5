const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

const oldHandleCleanUp = /const handleCleanUp = \(\) => \{[\s\S]*?if \(tikzBeginMatch && tikzEndMatch\) \{[\s\S]*?return;\n    \}\n  \};/;

const newHandleCleanUp = `const handleCleanUp = () => {
    if (isLoading || !currentCode || !currentCode.trim()) return;
    
    let newCode = currentCode;

    const findCommentsBefore = (text, index) => {
        let beforeStr = text.substring(0, index);
        let lines = beforeStr.split('\\n');
        let commentLines = [];
        for (let i = lines.length - 1; i >= 0; i--) {
            let line = lines[i].trim();
            if (line === '' || line.startsWith('%')) {
                commentLines.unshift(lines[i]);
                if (line !== '' && !line.startsWith('%')) {
                    break;
                }
            } else {
                break;
            }
        }
        // Remove empty lines at the very beginning of the extracted comments
        while (commentLines.length > 0 && commentLines[0].trim() === '') {
            commentLines.shift();
        }
        return commentLines.join('\\n') + (commentLines.length > 0 ? '\\n' : '');
    };
    
    const docBegin = newCode.indexOf('\\\\begin{document}');
    const docClass = newCode.indexOf('\\\\documentclass');
    const docEnd = newCode.lastIndexOf('\\\\end{document}');
    
    if (docEnd !== -1) {
       let start = docClass !== -1 ? docClass : (docBegin !== -1 ? docBegin : 0);
       let comments = findCommentsBefore(newCode, start);
       const end = docEnd + '\\\\end{document}'.length;
       newCode = (comments + newCode.substring(start, end)).trim();
       setCurrentCode(newCode);
       return;
    }
    
    const tikzBeginMatch = newCode.match(/\\\\begin\\{(tikzpicture|circuitikz)\\}/);
    const tikzEndMatch = newCode.match(/\\\\end\\{(tikzpicture|circuitikz)\\}/g);
    
    if (tikzBeginMatch && tikzEndMatch) {
       let start = tikzBeginMatch.index;
       let comments = findCommentsBefore(newCode, start);
       const endMatchStr = tikzEndMatch[tikzEndMatch.length - 1];
       const end = newCode.lastIndexOf(endMatchStr) + endMatchStr.length;
       newCode = (comments + newCode.substring(start, end)).trim();
       setCurrentCode(newCode);
       return;
    }
  };`;

content = content.replace(oldHandleCleanUp, newHandleCleanUp);
fs.writeFileSync('App.tsx', content);
