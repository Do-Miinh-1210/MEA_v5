const fs = require('fs');

const constants = fs.readFileSync('constants.tsx', 'utf8');
const parsed = JSON.parse(fs.readFileSync('parsed_examples.json', 'utf8'));

// Extract the 16th example from constants
const match = constants.match(/\{\s*id:\s*"shading-16"[\s\S]*?\n\s*\},/);
let template16 = '';
if (match) {
  template16 = match[0];
}

const templatesStr = parsed.map(t => {
  return `          {
            id: "${t.id}",
            title: ${JSON.stringify(t.title)},
            description: ${JSON.stringify(t.description)},
            code: ${JSON.stringify(t.code)}
          }`;
}).join(',\n');

// Find where "1.8. Tô miền diện tích" is and replace its templates
const regex = /(name:\s*"1.8\.\s*Tô miền diện tích",\s*templates:\s*\[)([\s\S]*?)(\n\s*\]\s*,\s*\n\s*\},)/;

const newConstants = constants.replace(regex, (m, p1, p2, p3) => {
  let combined = templatesStr;
  if (template16) {
     combined += ',\n' + template16.slice(0, -1); // remove trailing comma
  }
  return p1 + '\n' + combined + p3;
});

fs.writeFileSync('constants.tsx', newConstants);
