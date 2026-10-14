const code = `
% --- ĐỒ THỊ HÀM SỐ ---
% \\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
%     % postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, above left] {$y=x^2+1$};}}, decorate}
% ]
%   plot (\\x, {f(\\x)});

% --- TIỆM CẬN ---
\\draw[dashed, line width=0.6pt, domain=-2:2]
  plot (\\x, {x+1});
`;

let shown = code.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\s*\n)([\s\S]*?(?=\n\s*(?:% ---|$)))/g, (match, p1, p2) => {
  if (p2.trim().startsWith('\\draw')) return match; // already shown
  return p1 + p2.split('\n').map(line => line.replace(/^%\s?/, '')).join('\n');
});

let hidden = shown.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\s*\n)([\s\S]*?(?=\n\s*(?:% ---|$)))/g, (match, p1, p2) => {
  if (p2.trim().startsWith('% \\draw')) return match; // already hidden
  return p1 + p2.split('\n').map(line => '% ' + line).join('\n');
});

console.log("SHOWN:\n", shown);
console.log("HIDDEN:\n", hidden);
