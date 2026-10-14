const code = `
% --- ĐỒ THỊ HÀM SỐ ---
\\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax]
  plot (\\x, {f(\\x)});
  
\\fill (0,0) circle (1pt);
\\end{tikzpicture}
`;

let next = code;
next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\s*\n)([\s\S]*?(?=\n\s*\n|\n\s*\\end\{tikzpicture\}|$))/g, (match, p1, p2) => {
  return p1 + p2.split('\n').map(line => '% ' + line).join('\n');
});

console.log(next);
