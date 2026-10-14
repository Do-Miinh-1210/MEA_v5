import fs from 'fs';
let content = fs.readFileSync('constants.tsx', 'utf8');

// Replace standard box 1
content = content.replace(
  /A\/170\/A, B\/-90\/B, C\/-90\/C, D\/0\/D,\\n\s*A1\/90\/A', B1\/90\/B', C1\/90\/C', D1\/90\/D'/g,
  "A/170, B/-90, C/-90, D/0,\n A'/90, B'/90, C'/-25, D'/90"
).replace(
  /A\/45\/A, B\/-90\/B, C\/-90\/C, D\/0\/D,\\n\s*A1\/90\/A', B1\/90\/B', C1\/90\/C', D1\/90\/D'/g,
  "A/170, B/-90, C/-90, D/0,\n A'/90, B'/90, C'/-25, D'/90"
);

// We need to also replace the `\x/\goc/\t` to `\p/\goc` and `$\t$` to `$\p$` for these blocks?
// Wait, actually earlier I ran a script fix_vars_t_g.js which already changed \t/\g to \p/\goc. But here it's \x/\goc/\t.
// Let's replace \x/\goc/\t with \p/\goc for those that match the box.
// It's tricky to target exactly. Let's just fix the whole string for "Hình hộp chữ nhật"

fs.writeFileSync('constants.tsx', content);
