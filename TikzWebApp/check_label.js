const code = `
% --- ĐỒ THỊ HÀM SỐ ---
\\draw[line width=0.6pt, smooth, samples=100, domain=xmin:xmax,
    % postaction={decoration={markings, mark=at position 0.8 with {\\node[transform shape, sloped, above left] {$y=x^2+1$};}}, decorate}
] % lưu ý: dấu đóng ngoặc vuông phải hiển thị riêng một dòng
  plot (\\x, {f(\\x)});

% --- TIỆM CẬN ---
\\draw[dashed, line width=0.6pt, domain=-2:2,
  postaction={decoration={markings, mark=at position 0.2 with {\\node[transform shape, sloped, above left] {$y=x+1$};}}, decorate}
]
  plot (\\x, {x+1});
`;

let next = code;

// Hide Function Graph Label
next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\s*\n[\s\S]*?)(\n\s*)(%?\s*)(postaction=\{[^}]*\}\}, decorate\})/g, (match, p1, p2, p3, p4) => {
  return p1 + p2 + '% ' + p4;
});
console.log("HIDE FUNC:\n", next);

// Show Function Graph Label
next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\s*\n[\s\S]*?)(\n\s*)(%?\s*)(postaction=\{[^}]*\}\}, decorate\})/g, (match, p1, p2, p3, p4) => {
  return p1 + p2 + p4;
});
console.log("SHOW FUNC:\n", next);

// Same for Asymptotes
next = next.replace(/(% --- TIỆM CẬN ---\s*\n[\s\S]*?)(\n\s*)(%?\s*)(postaction=\{[^}]*\}\}, decorate\})/g, (match, p1, p2, p3, p4) => {
  return p1 + p2 + '% ' + p4;
});
console.log("HIDE ASYMP:\n", next);

