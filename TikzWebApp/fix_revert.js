import fs from 'fs';

let content = fs.readFileSync('constants.tsx', 'utf8');

// The replacements we applied:
// {from: /node\\[shift=\\{\\(\\\\g:.*pt\\)\\}\\]/g, to: "node[\\g]"},
// {from: /node\\[shift=\\{\\(\\\\goc:.*pt\\)\\}\\]/g, to: "node[\\goc]"},
// {from: /node\\[shift=\\{\\(\\\\pos:.*pt\\)\\}\\]/g, to: "node[\\pos]"},

// So we currently have "node[\\g]" and we want "node[shift={(\\g:9pt)}]"

content = content.replace(/node\[\\\\g\]/g, "node[shift={(\\\\g:9pt)}]");
content = content.replace(/node\[\\\\goc\]/g, "node[shift={(\\\\goc:9pt)}]");
content = content.replace(/node\[\\\\pos\]/g, "node[shift={(\\\\pos:9pt)}]");

// What if there is a font command inside, like node[\g, font=\normalsize]?
content = content.replace(/node\[\\\\g,/g, "node[shift={(\\\\g:9pt)},");
content = content.replace(/node\[\\\\goc,/g, "node[shift={(\\\\goc:9pt)},");
content = content.replace(/node\[\\\\pos,/g, "node[shift={(\\\\pos:9pt)},");


fs.writeFileSync('constants.tsx', content);

// Do the same for constants.new.tsx just in case
let content2 = fs.existsSync('constants.new.tsx') ? fs.readFileSync('constants.new.tsx', 'utf8') : '';
if (content2) {
    content2 = content2.replace(/node\[\\\\g\]/g, "node[shift={(\\\\g:9pt)}]");
    content2 = content2.replace(/node\[\\\\goc\]/g, "node[shift={(\\\\goc:9pt)}]");
    content2 = content2.replace(/node\[\\\\pos\]/g, "node[shift={(\\\\pos:9pt)}]");

    content2 = content2.replace(/node\[\\\\g,/g, "node[shift={(\\\\g:9pt)},");
    content2 = content2.replace(/node\[\\\\goc,/g, "node[shift={(\\\\goc:9pt)},");
    content2 = content2.replace(/node\[\\\\pos,/g, "node[shift={(\\\\pos:9pt)},");
    fs.writeFileSync('constants.new.tsx', content2);
}

console.log("Reverted node array variable label formatting back to shift.");
