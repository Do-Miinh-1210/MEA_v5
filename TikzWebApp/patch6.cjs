const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

const oldRegexCode = `      // Toggle Asymptotes
      if (isAsymptoteHidden) {
        next = next.replace(/(% --- TIỆM CẬN ---[\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1) => {
          // fallback in case p1 matching fails
          return match;
        }); // wait this is wrong regex format in my script!
      }`;

const exactReplacement = `      // Toggle Asymptote Labels
      if (isAsymptoteHidden) {
        next = next.replace(/(% --- TIỆM CẬN ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1% $4");
        });
      } else {
        next = next.replace(/(% --- TIỆM CẬN ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1$4");
        });
      }
      
      // Toggle Function Graph Labels
      if (isFunctionHidden) {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1% $4");
        });
      } else {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1$4");
        });
      }`;

const targetToReplace = `      // Toggle Asymptotes
      if (isAsymptoteHidden) {
        next = next.replace(/(% --- TIỆM CẬN ---[\\s\\S]*?)$/g, (match) => match); // just finding it
      }`;
