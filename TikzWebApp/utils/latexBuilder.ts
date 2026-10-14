export function getOptimizedLatexCode(code: string): string {
  // Extract pure tikz code first to prevent double preambles
  const pureCode = extractTikzCodeFromFull(code);

  const packages: string[] = [
    '\\usepackage[utf8]{vietnam}',
    '\\usepackage{amsmath,amssymb,amsfonts,mathtools,bm}'
  ];
  
  const tikzLibraries: Set<string> = new Set();
  const configs: string[] = [];

  // Conditional Packages
  if (/(?:\\qty|\\SI|\\norm|\\abs|\\dd|\\dv|\\pdv|\\var|\\eval|\\order|\\comm|\\acomm|\\pb|\\laplacian|\\Tr|\\tr|\\rank|\\erf|\\Res|\\principalvalue)\\b/.test(pureCode)) {
    packages.push('\\usepackage{physics,siunitx}');
    configs.push('\\sisetup{per-mode=symbol}');
  }
  
  if (/(?:\\ce|\\ch|\\chemfig)\\b/.test(pureCode)) {
    packages.push('\\usepackage[version=4]{mhchem}');
    packages.push('\\usepackage{chemfig}');
  }

  if (/circuitikz|to\s*\[/.test(pureCode) || /\\begin\{circuitikz\}/.test(pureCode)) {
    if (/american/i.test(pureCode)) {
      packages.push('\\usepackage[american, scale=1.2]{circuitikz}');
    } else {
      packages.push('\\usepackage[european, scale=1.2]{circuitikz}');
    }
  }

  const extraGraphics: string[] = [];
  if (/\\includegraphics/.test(pureCode)) extraGraphics.push('graphicx');
  if (/pgfplots|axis|addplot/.test(pureCode)) {
    extraGraphics.push('pgfplots');
    configs.push('\\pgfplotsset{compat=1.18}');
    configs.push('\\usepgfplotslibrary{fillbetween,statistics}');
  }
  if (/\\tkz(?!Tab)/.test(pureCode)) extraGraphics.push('tkz-euclide');
  if (/tdplot/.test(pureCode)) extraGraphics.push('tikz-3dplot');
  
  if (extraGraphics.length > 0) {
    packages.push(`\\usepackage{${extraGraphics.join(',')}}`);
  }

  const extraMisc: string[] = [];
  if (/lstlisting|\\lst/.test(pureCode)) extraMisc.push('listings');
  if (/\\tkzTab/.test(pureCode)) extraMisc.push('tkz-tab', 'tabvar');
  if (/tabular|table|figure|wrapfig|multirow|\\toprule/.test(pureCode)) {
    extraMisc.push('float', 'caption', 'subcaption', 'booktabs', 'multirow', 'array');
  }
  
  if (extraMisc.length > 0) {
    packages.push(`\\usepackage{${extraMisc.join(',')}}`);
  }

  // Conditional TikZ Libraries
  tikzLibraries.add('arrows.meta'); // Very common
  
  if (/\$|calc/.test(pureCode)) tikzLibraries.add('calc');
  if (/intersection/.test(pureCode)) tikzLibraries.add('intersections');
  if (/above=|below=|left=|right=|positioning/.test(pureCode)) tikzLibraries.add('positioning');
  if (/ellipse|polygon|star|shapes\.geometric/.test(pureCode)) tikzLibraries.add('shapes.geometric');
  if (/pattern/.test(pureCode)) tikzLibraries.add('patterns.meta');
  if (/decorat/.test(pureCode)) {
    tikzLibraries.add('decorations.markings');
    tikzLibraries.add('decorations.pathmorphing');
  }
  if (/pic|angle|right angle/.test(pureCode)) {
    tikzLibraries.add('angles');
    tikzLibraries.add('quotes');
    configs.push('\\tikzset{right angle/.style={angle}}');
  }
  if (/circle through/.test(pureCode)) tikzLibraries.add('through');
  if (/background/.test(pureCode)) tikzLibraries.add('backgrounds');
  if (/fit=/.test(pureCode)) tikzLibraries.add('fit');
  if (/mark=/.test(pureCode)) tikzLibraries.add('plotmarks');
  if (/chain/.test(pureCode)) tikzLibraries.add('chains');
  if (/matrix/.test(pureCode)) tikzLibraries.add('matrix');
  if (/perspective/.test(pureCode)) tikzLibraries.add('perspective');
  if (/canvas is/.test(pureCode)) tikzLibraries.add('3d');

  let preamble = `\\documentclass[tikz,border=10mm]{standalone}\n`;
  
  if (packages.length > 0) {
    preamble += packages.join('\n') + '\n';
  }
  
  if (tikzLibraries.size > 0) {
    preamble += `\\usetikzlibrary{${Array.from(tikzLibraries).join(',')}}\n`;
  }
  
  if (configs.length > 0) {
    preamble += configs.join('\n') + '\n';
  }

  preamble += `\n\\begin{document}\n`;

  return preamble + pureCode + `\n\\end{document}`;
}

export function extractTikzCodeFromFull(fullCode: string): string {
  const beginMatch = fullCode.match(/\\begin\{document\}/);
  const endMatch = fullCode.match(/\\end\{document\}/);
  
  if (beginMatch && endMatch) {
    const startIdx = beginMatch.index! + beginMatch[0].length;
    const endIdx = endMatch.index!;
    return fullCode.substring(startIdx, endIdx).trim();
  }
  
  // If no \begin{document}, it might still have \documentclass
  // We can try to extract just the tikzpicture if it exists
  const tikzBeginMatch = fullCode.match(/\\begin\{tikzpicture\}/);
  const tikzEndMatch = fullCode.match(/\\end\{tikzpicture\}/);
  if (tikzBeginMatch && tikzEndMatch && fullCode.includes('\\documentclass')) {
     const startIdx = tikzBeginMatch.index!;
     const endIdx = tikzEndMatch.index! + tikzEndMatch[0].length;
     return fullCode.substring(startIdx, endIdx).trim();
  }
  
  const circuitikzBeginMatch = fullCode.match(/\\begin\{circuitikz\}/);
  const circuitikzEndMatch = fullCode.match(/\\end\{circuitikz\}/);
  if (circuitikzBeginMatch && circuitikzEndMatch && fullCode.includes('\\documentclass')) {
     const startIdx = circuitikzBeginMatch.index!;
     const endIdx = circuitikzEndMatch.index! + circuitikzEndMatch[0].length;
     return fullCode.substring(startIdx, endIdx).trim();
  }

  return fullCode;
}
