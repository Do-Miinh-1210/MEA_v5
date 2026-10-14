const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

const oldEffect = `  useEffect(() => {
    setCurrentCode(prev => {
      if (isBbtNoFrame && prev.includes('nocadre=false')) {
        return prev.replace(/nocadre=false/g, 'nocadre=true');
      } else if (!isBbtNoFrame && prev.includes('nocadre=true')) {
        return prev.replace(/nocadre=true/g, 'nocadre=false');
      }
      return prev;
    });
  }, [isBbtNoFrame]);`;

const newEffect = `  useEffect(() => {
    setCurrentCode(prev => {
      let next = prev;
      
      // Toggle BBT Frame
      if (isBbtNoFrame && next.includes('nocadre=false')) {
        next = next.replace(/nocadre=false/g, 'nocadre=true');
      } else if (!isBbtNoFrame && next.includes('nocadre=true')) {
        next = next.replace(/nocadre=true/g, 'nocadre=false');
      }
      
      // Toggle Asymptotes
      if (isAsymptoteHidden) {
        next = next.replace(/(% --- TIỆM CẬN ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*(?:% ---|$)))/g, (match, p1, p2) => {
          if (p2.trim().startsWith('% \\\\draw')) return match;
          return p1 + p2.split('\\n').map(line => '% ' + line).join('\\n');
        });
      } else {
        next = next.replace(/(% --- TIỆM CẬN ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*(?:% ---|$)))/g, (match, p1, p2) => {
          if (p2.trim().startsWith('\\\\draw')) return match;
          return p1 + p2.split('\\n').map(line => line.replace(/^%\\s?/, '')).join('\\n');
        });
      }
      
      // Toggle Function Graph
      if (isFunctionHidden) {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*(?:% ---|$)))/g, (match, p1, p2) => {
          if (p2.trim().startsWith('% \\\\draw')) return match;
          return p1 + p2.split('\\n').map(line => '% ' + line).join('\\n');
        });
      } else {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\\s*\\n)([\\s\\S]*?(?=\\n\\s*(?:% ---|$)))/g, (match, p1, p2) => {
          if (p2.trim().startsWith('\\\\draw')) return match;
          return p1 + p2.split('\\n').map(line => line.replace(/^%\\s?/, '')).join('\\n');
        });
      }

      return next;
    });
  }, [isBbtNoFrame, isAsymptoteHidden, isFunctionHidden]);`;

content = content.replace(oldEffect, newEffect);
fs.writeFileSync('App.tsx', content);
