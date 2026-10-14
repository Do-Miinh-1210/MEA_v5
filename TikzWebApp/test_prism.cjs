const Prism = require('prismjs');
require('prismjs/components/prism-latex');
const code = "\\begin{tikzpicture}\n% A multiline\n% comment\n\\draw (0,0) -- (1,1);\n\\end{tikzpicture}";
const highlighted = Prism.highlight(code, Prism.languages.latex, 'latex');
console.log(JSON.stringify(highlighted));
