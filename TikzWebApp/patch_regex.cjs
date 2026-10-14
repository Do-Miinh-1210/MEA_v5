const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

const oldLine = "      next = next.replace(/every node\\/\\.style=\\{font=\\\\[a-zA-Z]+\\}/g, 'every node/.style={font=\\\\' + fontSize + '}');";
const newLine = "      next = next.replace(/every node\\/\\.style=\\{\\s*font\\s*=\\s*\\\\[a-zA-Z]+\\s*\\}/g, 'every node/.style={font=\\\\' + fontSize + '}');";

content = content.replace(oldLine, newLine);
fs.writeFileSync('App.tsx', content);
