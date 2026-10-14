const Prism = require('prismjs');
require('prismjs/components/prism-latex');
const code = "Some \\$ inline\nmath \\$ here";
const highlighted = Prism.highlight(code, Prism.languages.latex, 'latex');
console.log(highlighted);
