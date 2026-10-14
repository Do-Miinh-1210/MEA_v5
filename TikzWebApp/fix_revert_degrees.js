import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');

const replacements = [
  // degree map from fix_constants_labels.js REVERSED
  {to: /A\/90, B\/240, C\/-60, D\/-90/g, from: "A/above, B/below left, C/below right, D/below"},
  {to: /S\/90, A\/190, B\/-90, C\/0/g, from: "S/above, A/left, B/below, C/right"},
  {to: /A\/225, B\/-45, C\/135/g, from: "A/below left, B/below right, C/above left"},
  {to: /A\/90, B\/180, C\/0, D\/-90/g, from: "A/above, B/left, C/right, D/below"},
  {to: /A\/170, B\/-90, C\/-90, D\/0, S\/90/g, from: "A/above left, B/below, C/below, D/right, S/above"},
  {to: /A\/45\/A, B\/-90\/B, C\/-90\/C, D\/0\/D/g, from: "A/above right/A, B/below/B, C/below/C, D/right/D"},
  {to: /A1\/90\/A', B1\/90\/B', C1\/90\/C', D1\/90\/D'/g, from: "A1/above/A', B1/above/B', C1/above/C', D1/above/D'"},
  {to: /B\/-90, C\/-90, D\/0, S\/90/g, from: "B/below, C/below, D/right, S/above"},
  {to: /A\/180\/A, B\/-90\/B, C\/0\/C/g, from: "A/left/A, B/below/B, C/right/C"},
  {to: /A1\/100\/A', B1\/85\/B', C1\/80\/C'/g, from: "A1/above left/A', B1/above right/B', C1/above right/C'"},
  {to: /A\/170\/A, B\/-90\/B, C\/-90\/C, D\/0\/D/g, from: "A/above left/A, B/below/B, C/below/C, D/right/D"},
  {to: /B\/-90, C\/-90, D\/0, S\/120/g, from: "B/below, C/below, D/right, S/above left"},
  {to: /A\/255\/A, B\/-75\/B, C\/10\/C, D\/170\/D/g, from: "A/below left/A, B/below right/B, C/right/C, D/above left/D"},
  {to: /A_1\/135\/A', B_1\/90\/B', C_1\/45\/C', D_1\/90\/D'/g, from: "A_1/above left/A', B_1/above/B', C_1/above right/C', D_1/above/D'"},
  {to: /A\/150, B\/-90, C\/-60, D\/60, S\/90, O\/-90/g, from: "A/above left, B/below, C/below right, D/above right, S/above, O/below"},

  // specific to \goc
  {to: "{A/goc, B/-goc, S/0, O/135}", from: "{A/above right, B/below right, S/right, O/above left}"},
  {to: "{A/gocm, B/{180-goch}, C/goch, S/0, O/135}", from: "{A/above right, B/above left, C/below right, S/right, O/above left}"},
  {to: "{A/goc, A'/goc, B/-goc, B'/-goc, O/180, O'/-90, S/0}", from: "{A/above right, A'/above right, B/below right, B'/below right, O/left, O'/below, S/right}"},
  {to: "{A/goc, A'/goc, B/-goc, B'/-goc, O/-90, O'/-90, S/0}", from: "{A/above right, A'/above right, B/below right, B'/below right, O/below, O'/below, S/right}"},
];

for (const rep of replacements) {
    if (typeof rep.to === 'string') {
        content = content.split(rep.from).join(rep.to);
    } else {
        // Here `to` is a regex, which means we want to extract its string representation
        const toStr = rep.to.source.replace(/\\\//g, '/');
        content = content.split(rep.from).join(toStr);
    }
}

// We reverted the nodes correctly.

// also make sure we use \goc instead of \goc:9pt, etc. no!
// "luôn điều chỉnh bằng độ"
// so node[shift={(\goc:9pt)}] should be output? Yes, we already restored node[shift={(\goc:9pt)}]

fs.writeFileSync('constants.tsx', content);

let content2 = fs.existsSync('constants.new.tsx') ? fs.readFileSync('constants.new.tsx', 'utf8') : '';
if (content2) {
    for (const rep of replacements) {
        if (typeof rep.to === 'string') {
            content2 = content2.split(rep.from).join(rep.to);
        } else {
            const toStr = rep.to.source.replace(/\\\//g, '/');
            content2 = content2.split(rep.from).join(toStr);
        }
    }
    fs.writeFileSync('constants.new.tsx', content2);
}

console.log("Reverted words to degrees.");
