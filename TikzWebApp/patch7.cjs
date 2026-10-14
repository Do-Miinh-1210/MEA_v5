const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

const oldRegexCode = `      // Toggle Asymptotes
      if (isAsymptoteHidden) {
        next = next.replace(/(% --- TIỆM CẬN ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          if (p2.trim().startsWith('% \\\\draw')) return match;
          return p1 + p2.split('\\n').map(line => '% ' + line).join('\\n');
        });
      } else {
        next = next.replace(/(% --- TIỆM CẬN ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          if (p2.trim().startsWith('\\\\draw')) return match;
          return p1 + p2.split('\\n').map(line => line.replace(/^%\\s?/, '')).join('\\n');
        });
      }
      
      // Toggle Function Graph
      if (isFunctionHidden) {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          if (p2.trim().startsWith('% \\\\draw')) return match;
          return p1 + p2.split('\\n').map(line => '% ' + line).join('\\n');
        });
      } else {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          if (p2.trim().startsWith('\\\\draw')) return match;
          return p1 + p2.split('\\n').map(line => line.replace(/^%\\s?/, '')).join('\\n');
        });
      }`;

const exactReplacement = `      // Toggle Asymptote Labels
      if (isAsymptoteHidden) {
        next = next.replace(/(% --- TIỆM CẬN ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1% $3");
        });
      } else {
        next = next.replace(/(% --- TIỆM CẬN ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1$3");
        });
      }
      
      // Toggle Function Graph Labels
      if (isFunctionHidden) {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1% $3");
        });
      } else {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*\\n|\\n\\s*\\\\end\\{tikzpicture\\}|\\n\\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\\n\\s*)(%?\\s*)(postaction=\\{[^}]*\\}\\}, decorate\\})/g, "$1$3");
        });
      }`;

content = content.replace(oldRegexCode, exactReplacement);
fs.writeFileSync('App.tsx', content);
