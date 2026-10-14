import fs from 'fs';
let content = fs.readFileSync('constants.tsx', 'utf8');

// replace \t/\g with \p/\goc
content = content.split('\\t/\\g in').join('\\p/\\goc in');
// \g:9pt to \goc:9pt
content = content.replace(/\\g:/g, '\\goc:');
// $\t$ to $\p$
content = content.split('$\\t$').join('$\\p$');
// replace \fill (\t) with \fill (\p)
content = content.split('(\\t)').join('(\\p)');

fs.writeFileSync('constants.tsx', content);
console.log("Updated loop variables.");
