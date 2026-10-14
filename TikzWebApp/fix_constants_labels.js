import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');

const replacements = [
  {from: /node\\[shift=\\{\\(-6pt,-5pt\\)\\}\\]/g, to: "node[below left]"},
  {from: /node\\[shift=\\{\\(-45:12pt\\)\\}\\]/g, to: "node[below right]"},
  {from: /node\\[shift=\\{\\(45:10pt\\)\\}\\]/g, to: "node[above right]"},
  {from: /node\\[shift=\\{\\(45:9pt\\)\\}\\]/g, to: "node[above right]"},
  {from: /node\\[shift=\\{\\(-45:10pt\\)\\}\\]/g, to: "node[below right]"},
  {from: /node\\[shift=\\{\\(-45:9pt\\)\\}\\]/g, to: "node[below right]"},
  {from: /node\\[shift=\\{\\(135:10pt\\)\\}\\]/g, to: "node[above left]"},
  {from: /node\\[shift=\\{\\(135:9pt\\)\\}\\]/g, to: "node[above left]"},
  {from: /node\\[shift=\\{\\(135:12pt\\)\\}\\]/g, to: "node[above left]"},
  {from: /node\\[shift=\\{\\(-135:10pt\\)\\}\\]/g, to: "node[below left]"},
  {from: /node\\[shift=\\{\\(-135:12pt\\)\\}\\]/g, to: "node[below left]"},
  {from: /node\\[shift=\\{\\(-135:9pt\\)\\}\\]/g, to: "node[below left]"},
  {from: /node\\[shift=\\{\\(90:9pt\\)\\}\\]/g, to: "node[above]"},
  {from: /node\\[shift=\\{\\(90:10pt\\)\\}\\]/g, to: "node[above]"},
  {from: /node\\[shift=\\{\\(-90:9pt\\)\\}\\]/g, to: "node[below]"},
  {from: /node\\[shift=\\{\\(-90:10pt\\)\\}\\]/g, to: "node[below]"},
  {from: /node\\[shift=\\{\\(0:9pt\\)\\}\\]/g, to: "node[right]"},
  {from: /node\\[shift=\\{\\(0:10pt\\)\\}\\]/g, to: "node[right]"},
  {from: /node\\[shift=\\{\\(180:9pt\\)\\}\\]/g, to: "node[left]"},
  {from: /node\\[shift=\\{\\(180:10pt\\)\\}\\]/g, to: "node[left]"},
  {from: /node\\[shift=\\{\\(170:12pt\\)\\}\\]/g, to: "node[above left]"},
  {from: /node\\[shift=\\{\\(-145:12pt\\)\\}\\]/g, to: "node[below left]"},
  {from: /node\\[shift=\\{\\(-35:14pt\\)\\}\\]/g, to: "node[below right]"},

  // for loops with \g
  {from: /node\\[shift=\\{\\(\\\\g:.*pt\\)\\}\\]/g, to: "node[\\g]"},
  {from: /node\\[shift=\\{\\(\\\\goc:.*pt\\)\\}\\]/g, to: "node[\\goc]"},
  {from: /node\\[shift=\\{\\(\\\\pos:.*pt\\)\\}\\]/g, to: "node[\\pos]"},

  // degree map
  {from: /A\/90, B\/240, C\/-60, D\/-90/g, to: "A/above, B/below left, C/below right, D/below"},
  {from: /S\/90, A\/190, B\/-90, C\/0/g, to: "S/above, A/left, B/below, C/right"},
  {from: /A\/225, B\/-45, C\/135/g, to: "A/below left, B/below right, C/above left"},
  {from: /A\/90, B\/180, C\/0, D\/-90/g, to: "A/above, B/left, C/right, D/below"},
  {from: /A\/170, B\/-90, C\/-90, D\/0, S\/90/g, to: "A/above left, B/below, C/below, D/right, S/above"},
  {from: /A\/45\/A, B\/-90\/B, C\/-90\/C, D\/0\/D/g, to: "A/above right/A, B/below/B, C/below/C, D/right/D"},
  {from: /A1\/90\/A', B1\/90\/B', C1\/90\/C', D1\/90\/D'/g, to: "A1/above/A', B1/above/B', C1/above/C', D1/above/D'"},
  {from: /B\/-90, C\/-90, D\/0, S\/90/g, to: "B/below, C/below, D/right, S/above"},
  {from: /A\/180\/A, B\/-90\/B, C\/0\/C/g, to: "A/left/A, B/below/B, C/right/C"},
  {from: /A1\/100\/A', B1\/85\/B', C1\/80\/C'/g, to: "A1/above left/A', B1/above right/B', C1/above right/C'"},
  {from: /A\/170\/A, B\/-90\/B, C\/-90\/C, D\/0\/D/g, to: "A/above left/A, B/below/B, C/below/C, D/right/D"},
  {from: /B\/-90, C\/-90, D\/0, S\/120/g, to: "B/below, C/below, D/right, S/above left"},
  {from: /A\/255\/A, B\/-75\/B, C\/10\/C, D\/170\/D/g, to: "A/below left/A, B/below right/B, C/right/C, D/above left/D"},
  {from: /A_1\/135\/A', B_1\/90\/B', C_1\/45\/C', D_1\/90\/D'/g, to: "A_1/above left/A', B_1/above/B', C_1/above right/C', D_1/above/D'"},
  {from: /A\/150, B\/-90, C\/-60, D\/60, S\/90, O\/-90/g, to: "A/above left, B/below, C/below right, D/above right, S/above, O/below"},

  // specific to \goc
  {from: new RegExp("{A\\\\\\\\/goc, B\\\\\\\\/-goc, S\\\\\\\\/0, O\\\\\\\\/135}", "g"), to: "{A/above right, B/below right, S/right, O/above left}"},
  {from: new RegExp("{A\\\\\\\\/gocm, B\\\\\\\\/\\{180-goch\\}, C\\\\\\\\/goch, S\\\\\\\\/0, O\\\\\\\\/135}", "g"), to: "{A/above right, B/above left, C/below right, S/right, O/above left}"},
  {from: new RegExp("{A\\\\\\\\/goc, A'\\\\\\\\/goc, B\\\\\\\\/-goc, B'\\\\\\\\/-goc, O\\\\\\\\/180, O'\\\\\\\\/-90, S\\\\\\\\/0}", "g"), to: "{A/above right, A'/above right, B/below right, B'/below right, O/left, O'/below, S/right}"},
  {from: new RegExp("{A\\\\\\\\/goc, A'\\\\\\\\/goc, B\\\\\\\\/-goc, B'\\\\\\\\/-goc, O\\\\\\\\/-90, O'\\\\\\\\/-90, S\\\\\\\\/0}", "g"), to: "{A/above right, A'/above right, B/below right, B'/below right, O/below, O'/below, S/right}"},
  
  // also some remaining nodes like N13
  {from: "\\[yshift=8pt\\]", to: "[above] "},
  {from: "\\[yshift=-8pt\\]", to: "[below] "},
  {from: "\\[yshift=-16pt\\]", to: "[below] "},
  {from: "\\[yshift=16pt\\]", to: "[above] "},
  {from: "\\[yshift=-50pt\\]", to: "[below] "},
  {from: "\\[xshift=-16pt, yshift=8pt\\]", to: "[above left] "},
  {from: "\\[xshift=16pt, yshift=-8pt\\]", to: "[below right] "},
  
  // also need to handle global strings manually via code
];

for (const rep of replacements) {
    if (typeof rep.from === 'string') {
        content = content.split(rep.from).join(rep.to);
    } else {
        content = content.replace(rep.from, rep.to);
    }
}

fs.writeFileSync('constants.tsx', content);
console.log("Updated constants.tsx shift references successfully!");
