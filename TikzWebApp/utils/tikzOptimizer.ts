export const smartSearch = (code: string, query: string): { matches: RegExpMatchArray | null, regex: RegExp | null } => {
  if (!query) return { matches: null, regex: null };

  let regexStr = query;
  let flags = 'gi';

  // A. Tìm theo cú pháp TikZ
  if (query === '\\draw commands') regexStr = '\\\\draw[^;]*;';
  else if (query === '\\node commands') regexStr = '\\\\node[^;]*;';
  else if (query === '\\path commands') regexStr = '\\\\path[^;]*;';
  else if (query === '\\fill commands') regexStr = '\\\\fill[^;]*;';
  else if (query.startsWith('[') && query.endsWith(']')) {
    // Parameter search, e.g., [rounded corners] or [thick]
    const param = query.slice(1, -1);
    regexStr = `\\[[^\\]]*\\b${param}\\b[^\\]]*\\]`;
  }
  else if (query === '\\') regexStr = '\\\\[a-zA-Z@]+'; // All TikZ commands

  // B. Tìm theo đối tượng hình học
  else if (query === 'circle' || query === 'ellipse') regexStr = '\\b(circle|ellipse)\\b';
  else if (query === 'rectangle') regexStr = '\\brectangle\\b';
  else if (query === 'node' || query === 'coordinate') regexStr = '\\b(node|coordinate)\\b';
  else if (query === 'plot' || query === 'to' || query === 'controls') regexStr = '\\b(plot|to|controls)\\b';

  // C. Tìm theo màu sắc
  else if (query === 'red' || query.startsWith('red!')) {
    regexStr = '\\bred(?:!\\d+(?:![a-zA-Z]+)?)?\\b';
  }
  else if (query === 'primary colors') regexStr = '\\b(red|blue|yellow|green|black|white|cyan|magenta)\\b';
  else if (query === 'secondary colors') regexStr = '\\b(orange|purple|brown|pink|gray|teal|lime)\\b';

  // Default text search
  else {
    regexStr = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // Escape regex
  }

  try {
    const regex = new RegExp(`(${regexStr})`, flags);
    const matches = code.match(regex);
    return { matches, regex };
  } catch (e) {
    return { matches: null, regex: null };
  }
};

export const smartReplace = (code: string, type: string): string => {
  let newCode = code;

  switch (type) {
    // 2.A Chuẩn hóa code
    case 'normalize-tikzstyle':
      // \tikzstyle{name} = [options] -> \tikzset{name/.style={options}}
      newCode = newCode.replace(/\\tikzstyle\{([^}]+)\}\s*=\s*\[(.*?)\]/g, '\\tikzset{$1/.style={$2}}');
      break;
    case 'normalize-coordinates':
      // (1,2) -> (1cm,2cm) if missing units
      newCode = newCode.replace(/\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)/g, '($1cm,$2cm)');
      break;

    // 2.B Thay thế thông minh theo ngữ cảnh
    case 'better-arrows':
      // \draw[->] -> \draw[-stealth]
      newCode = newCode.replace(/\\draw\s*\[(.*?)->(.*?)\]/g, '\\draw[$1-stealth$2]');
      break;
    case 'node-to-point':
      // node -> node[circle, fill=black] for points. Be careful with this one.
      // Let's replace simple nodes without options
      newCode = newCode.replace(/\\node\s*(?!\s*\[)/g, '\\node[circle, fill=black, inner sep=1.5pt] ');
      break;
    case 'auto-scale':
      // Add scale=1 to \begin{tikzpicture} if missing
      if (newCode.includes('\\begin{tikzpicture}') && !newCode.includes('scale=')) {
        newCode = newCode.replace(/\\begin\{tikzpicture\}\s*(?:\[(.*?)\])?/, (match, p1) => {
          if (p1) return `\\begin{tikzpicture}[${p1}, scale=1]`;
          return `\\begin{tikzpicture}[scale=1]`;
        });
      }
      break;

    // 2.C Tối ưu hóa mã TikZ
    case 'group-draws':
      // Very basic grouping: \draw[red] (0,0)--(1,1); \draw[red] (1,1)--(2,2); -> \draw[red] (0,0)--(1,1) (1,1)--(2,2);
      // This is complex to do perfectly with regex, but we can try a simple version.
      // For now, let's just do a simple replace for adjacent identical draws.
      const drawRegex = /\\draw\s*\[(.*?)\]\s*(.*?);\s*\\draw\s*\[\1\]\s*(.*?);/g;
      while (drawRegex.test(newCode)) {
        newCode = newCode.replace(drawRegex, '\\draw[$1] $2 $3;');
      }
      break;
    case 'extract-colors':
      // Replace duplicate colors with variables.
      // E.g. \draw[red] ... \draw[red] -> \colorlet{mycolor}{red}
      const colorMatches = newCode.match(/\[([^\]]*\b(?:red|blue|green|yellow|orange|purple|cyan|magenta)\b[^\]]*)\]/g);
      if (colorMatches && colorMatches.length > 2) {
        // Just a placeholder implementation
        if (!newCode.includes('\\colorlet{mycolor}')) {
          newCode = '\\colorlet{mycolor}{red}\n' + newCode.replace(/\[red\]/g, '[mycolor]');
        }
      }
      break;

    // 3. TEMPLATE THAY THẾ NHANH
    case 'template-circle':
      // \draw (X) circle (Y); -> \fill[cyan!20] (X) circle (Y); \draw[thick] (X) circle (Y);
      newCode = newCode.replace(/\\draw\s+(\(.*?\))\s+circle\s+(\(.*?\))\s*;/g, '\\fill[cyan!20] $1 circle $2;\n\\draw[thick] $1 circle $2;');
      break;
    case 'template-arrow':
      // \draw[->] (A) -- (B); -> \draw[-stealth, thick] (A) -- (B);
      newCode = newCode.replace(/\\draw\s*\[(.*?)->(.*?)\]\s+(\(.*?\))\s*--\s+(\(.*?\))\s*;/g, '\\draw[-stealth, thick, $1$2] $3 -- $4;');
      break;
    case 'template-node-text':
      // node {text} -> node[font=\small, above] {text}
      newCode = newCode.replace(/node\s*\{([^}]+)\}/g, 'node[font=\\small, above] {$1}');
      break;
  }

  return newCode;
};

export interface TikzError {
  message: string;
  start: number;
  end: number;
}

function isInComment(code: string, index: number): boolean {
  const lastNewline = code.lastIndexOf('\n', index);
  const lineStart = lastNewline === -1 ? 0 : lastNewline + 1;
  const commentIdx = code.indexOf('%', lineStart);
  return commentIdx !== -1 && commentIdx < index && (commentIdx === 0 || code[commentIdx - 1] !== '\\');
}

export const checkSyntaxErrors = (code: string): TikzError[] => {
  const errors: TikzError[] = [];
  
  // 1. Check environments (\begin and \end)
  const envStack: { name: string, start: number, end: number }[] = [];
  const beginRegex = /\\begin\{([^}]+)\}/g;
  const endRegex = /\\end\{([^}]+)\}/g;
  
  let match;
  while ((match = beginRegex.exec(code)) !== null) {
    if (isInComment(code, match.index)) continue;
    envStack.push({ name: match[1], start: match.index, end: match.index + match[0].length });
  }
  
  while ((match = endRegex.exec(code)) !== null) {
    if (isInComment(code, match.index)) continue;
    const name = match[1];
    let found = false;
    for (let i = envStack.length - 1; i >= 0; i--) {
      if (envStack[i].name === name) {
        envStack.splice(i, 1);
        found = true;
        break;
      }
    }
    if (!found) {
      errors.push({
        message: `Lỗi: Dư thừa \\end{${name}}`,
        start: match.index,
        end: match.index + match[0].length
      });
    }
  }
  
  for (const env of envStack) {
    errors.push({
      message: `Lỗi: Thiếu \\end{${env.name}}`,
      start: env.start,
      end: env.end
    });
  }

  // 2. Check brackets, braces, parens
  const stack: { char: string, index: number }[] = [];
  let inComment = false;
  for (let i = 0; i < code.length; i++) {
    const char = code[i];
    const prevChar = i > 0 ? code[i-1] : '';
    
    if (char === '%' && prevChar !== '\\') {
      inComment = true;
    }
    if (char === '\n') {
      inComment = false;
    }
    
    if (inComment) continue;
    if (prevChar === '\\') continue;
    
    if (char === '{' || char === '[' || char === '(') {
      stack.push({ char, index: i });
    } else if (char === '}' || char === ']' || char === ')') {
      const expected = char === '}' ? '{' : char === ']' ? '[' : '(';
      if (stack.length === 0 || stack[stack.length - 1].char !== expected) {
        errors.push({
          message: `Lỗi: Dư thừa dấu ngoặc '${char}' hoặc thiếu dấu mở ngoặc tương ứng`,
          start: i,
          end: i + 1
        });
      } else {
        stack.pop();
      }
    }
  }
  
  for (const item of stack) {
    errors.push({
      message: `Lỗi: Thiếu dấu đóng ngoặc cho '${item.char}'`,
      start: item.index,
      end: item.index + 1
    });
  }

  // 3. Check missing semicolons for TikZ commands
  let braceLevel = 0;
  let activeCmd: { name: string, start: number } | null = null;
  let lastNonSpaceIdx = -1;

  for (let i = 0; i < code.length; i++) {
    if (isInComment(code, i)) continue;
    
    const char = code[i];
    
    if (char === '{') braceLevel++;
    else if (char === '}') braceLevel--;
    
    if (!/\s/.test(char)) {
      if (char === ';') {
        if (activeCmd && braceLevel === 0) {
          activeCmd = null;
        }
      }
      
      if (char === '\\' && braceLevel === 0) {
        const match = code.slice(i).match(/^\\([a-zA-Z]+)/);
        if (match) {
          const cmdName = match[1];
          const isTopLevel = ['draw', 'fill', 'path', 'clip', 'filldraw', 'pattern', 'shade', 'shadedraw', 'node', 'coordinate', 'pic', 'matrix'].includes(cmdName);
          const isEnv = ['begin', 'end'].includes(cmdName);
          
          if (isTopLevel || isEnv) {
            if (activeCmd && lastNonSpaceIdx !== -1) {
              errors.push({
                message: `Lỗi: Lệnh '\\${activeCmd.name}' thiếu dấu chấm phẩy ';' kết thúc.`,
                start: lastNonSpaceIdx,
                end: lastNonSpaceIdx + 1
              });
            }
            if (isTopLevel) {
              activeCmd = { name: cmdName, start: i };
            } else {
              activeCmd = null;
            }
          }
        }
      }
      
      lastNonSpaceIdx = i;
    }
  }
  
  if (activeCmd && lastNonSpaceIdx !== -1) {
    errors.push({
      message: `Lỗi: Lệnh '\\${activeCmd.name}' thiếu dấu chấm phẩy ';' kết thúc.`,
      start: lastNonSpaceIdx,
      end: lastNonSpaceIdx + 1
    });
  }

  // 4. Check for redundant semicolons
  const doubleSemiRegex = /;(\s*;)+/g;
  let doubleSemiMatch;
  while ((doubleSemiMatch = doubleSemiRegex.exec(code)) !== null) {
    if (isInComment(code, doubleSemiMatch.index)) continue;
    const firstSemiIdx = code.indexOf(';', doubleSemiMatch.index);
    let redundantStart = code.indexOf(';', firstSemiIdx + 1);
    
    while (redundantStart !== -1 && redundantStart < doubleSemiMatch.index + doubleSemiMatch[0].length) {
      errors.push({
        message: `Lỗi: Dư thừa dấu chấm phẩy ';'`,
        start: redundantStart,
        end: redundantStart + 1
      });
      redundantStart = code.indexOf(';', redundantStart + 1);
    }
  }

  const envSemiRegex = /\\(begin|end)\{[^}]*\}\s*;/g;
  let envSemiMatch;
  while ((envSemiMatch = envSemiRegex.exec(code)) !== null) {
    if (isInComment(code, envSemiMatch.index)) continue;
    
    const matchStr = envSemiMatch[0];
    const semiIdx = envSemiMatch.index + matchStr.lastIndexOf(';');
    
    errors.push({
      message: `Lỗi: Dư thừa dấu chấm phẩy ';' sau môi trường \\${envSemiMatch[1]}`,
      start: semiIdx,
      end: semiIdx + 1
    });
  }

  return errors;
};
