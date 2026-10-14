const fs = require('fs');

const rawCode = `
\\begin{tikzpicture}[
  >=stealth, line join=round, line cap=round,
  every node/.style={font=\\normalsize},
  declare function={
    f(\\x) = \\x*\\x*\\x - 3*\\x + 1;
    g(\\x) = -\\x*\\x + 1;
    xmin = -3; xmax = 2.5;
    ymin = -5.5; ymax = 4.5;
    x1 = (-1 - sqrt(13))/2;
    x2 = 0;
    x3 = (-1 + sqrt(13))/2;
  }
]
\\draw[-Stealth, line width=0.7pt] (xmin, 0) -- (xmax, 0) node[below] {$x$};
\\draw[-Stealth, line width=0.7pt] (0, ymin) -- (0, ymax) node[shift={(-6pt,-5pt)}] {$y$};

\\begin{scope}
  \\clip (xmin, ymin) rectangle (xmax, ymax);
  
  \\fill[pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=teal]
    plot[domain=x1:x2, smooth, samples=150] (\\x, {f(\\x)}) --
    plot[domain=x2:x1, smooth, samples=150] (\\x, {g(\\x)}) -- cycle;
    
  \\fill[pattern={Lines[angle=135, distance=3pt, line width=0.3pt]}, pattern color=orange]
    plot[domain=x2:x3, smooth, samples=150] (\\x, {g(\\x)}) --
    plot[domain=x3:x2, smooth, samples=150] (\\x, {f(\\x)}) -- cycle;
    
  \\draw[line width=0.6pt, smooth, samples=300, domain=xmin:xmax,
    postaction={decoration={markings, mark=at position 0.86 with {\\node[transform shape, sloped, above left] {$y=x^3-3x+1$};}}, decorate}]
    plot (\\x, {f(\\x)});
    
  \\draw[line width=0.6pt, smooth, samples=300, domain=xmin:xmax,
    postaction={decoration={markings, mark=at position 0.82 with {\\node[transform shape, sloped, below right] {$y=-x^2+1$};}}, decorate}]
    plot (\\x, {g(\\x)});
\\end{scope}

\\draw[dashed, line width=0.4pt] (x1, {g(x1)}) -- (180:{-x1});
\\draw[dashed, line width=0.4pt] (x3, {g(x3)}) -- (0:x3);

\\fill (0,0) circle (0.8pt) node[shift={(-135:10pt)}] {$O$};
\\fill (x1, {g(x1)}) circle (0.8pt);
\\fill (180:{-x1}) circle (0.8pt) node[above] {$x_1$};
\\fill (90:1) circle (0.8pt) node[shift={(45:10pt)}] {$1$};
\\fill (x3, {g(x3)}) circle (0.8pt);
\\fill (0:x3) circle (0.8pt) node[above] {$x_2$};
\\end{tikzpicture}
`.trim();

const item16 = `          ,{
            id: "shading-16",
            title: "16. Diện tích giữa 2 đồ thị",
            description: "Diện tích giữa 2 đồ thị và 2 đường thẳng x=a, x=b",
            code: ${JSON.stringify(rawCode)}
          }`;

const constants = fs.readFileSync('constants.tsx', 'utf8');

// Find the end of shading-15 and insert shading-16
const regex = /(id:\s*"shading-15"[\s\S]*?\n\s*\})/;

const newConstants = constants.replace(regex, (m, p1) => {
  return p1 + '\n' + item16;
});

fs.writeFileSync('constants.tsx', newConstants);
