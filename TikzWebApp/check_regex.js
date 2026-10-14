const code = `
% --- ĐỒ THỊ HÀM SỐ ---
\\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
    % postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, above left] {$y=x^2+1$};}}, decorate}
]
  plot (\\x, {f(\\x)});

% --- TIỆM CẬN ---
\\draw[dashed, line width=0.6pt, domain=-2:2]
  plot (\\x, {x+1});
`;

let hidden = code.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\s*\n)(\\draw[^;]*;)/g, (match, p1, p2) => {
  return p1 + p2.split('\n').map(line => '% ' + line).join('\n');
});

console.log("HIDDEN:\n", hidden);

let shown = hidden.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\s*\n)((?:% \\draw[^;]*;)|(?:% \\draw[\s\S]*?;))/g, (match, p1, p2) => {
  return p1 + p2.split('\n').map(line => line.replace(/^%\s?/, '')).join('\n');
});

console.log("SHOWN:\n", shown);
