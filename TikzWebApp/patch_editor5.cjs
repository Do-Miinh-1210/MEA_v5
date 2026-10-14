const fs = require('fs');
let content = fs.readFileSync('components/Editor.tsx', 'utf8');

content = content.replace("Mã TikZ {isEditorVisible ? <ChevronDownIcon className=\"h-4 w-4\" /> : <ChevronUpIcon className=\"h-4 w-4\" />}", "{isEditorVisible ? <ChevronDownIcon className=\"h-4 w-4\" /> : <ChevronUpIcon className=\"h-4 w-4\" />}");

fs.writeFileSync('components/Editor.tsx', content);
