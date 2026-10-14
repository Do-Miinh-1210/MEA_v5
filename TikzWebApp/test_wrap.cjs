function wrapLinesWithLineNumbers(html) {
  const lines = html.split('\n');
  let openTags = [];
  
  return lines.map((line, i) => {
    let prefix = openTags.join('');
    
    const tagRegex = /<\/?([a-z0-9]+)[^>]*>/gi;
    let match;
    while ((match = tagRegex.exec(line)) !== null) {
      if (match[0].startsWith('</')) {
        openTags.pop();
      } else if (!match[0].endsWith('/>')) {
        openTags.push(match[0]);
      }
    }
    
    let suffix = openTags.slice().reverse().map(tag => {
      const tagName = tag.match(/<([a-z0-9]+)/i)[1];
      return `</${tagName}>`;
    }).join('');
    
    return `<span class="editor-line" data-line="${i + 1}">${prefix}${line}${suffix}</span>`;
  }).join('\n');
}

const html = `Some <span class="token equation string">$ inline
math $</span> here`;

console.log(wrapLinesWithLineNumbers(html));
