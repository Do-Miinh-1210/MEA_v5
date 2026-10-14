const code = `
% --- ĐỒ THỊ HÀM SỐ ---
\\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
    % postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, above left] {$y=x^2+1$};}}, decorate}
] % lưu ý: dấu đóng ngoặc vuông phải hiển thị riêng một dòng
  plot (\\x, {f(\\x)});
`;

let next = code.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\s*\n)([\s\S]*?(?=\n\s*\n|\n\s*\\end\{tikzpicture\}|\n\s*(?:% ---)|$))/g, (match, p1, p2) => {
  return p1 + p2.replace(/(\n\s*)(%?\s*)(postaction=\{[^}]*\}\}, decorate\})/g, "$1$4");
});
console.log("SHOW:\n" + next);

let hidden = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\s*\n)([\s\S]*?(?=\n\s*\n|\n\s*\\end\{tikzpicture\}|\n\s*(?:% ---)|$))/g, (match, p1, p2) => {
  return p1 + p2.replace(/(\n\s*)(%?\s*)(postaction=\{[^}]*\}\}, decorate\})/g, "$1% $3$4");
});
console.log("HIDE:\n" + hidden);
