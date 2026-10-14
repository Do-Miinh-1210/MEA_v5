const fs = require('fs');
let content = fs.readFileSync('services/geminiService.ts', 'utf8');

const oldAsymptote = `      % --- TIỆM CẬN ---
      \\\\draw[dashed, line width=0.6pt, domain=xmin:xmax]
        plot (\\\\x, {g(\\\\x)});`;

const newAsymptote = `      % --- TIỆM CẬN ---
      \\\\draw[dashed, line width=0.6pt, domain=xmin:xmax,
          % postaction={decoration={markings, mark=at position 0.2 with {\\\\node[transform shape, sloped, above left] {$y=... $};}}, decorate}
      ]
        plot (\\\\x, {g(\\\\x)});`;

content = content.replace(oldAsymptote, newAsymptote);
fs.writeFileSync('services/geminiService.ts', content);
