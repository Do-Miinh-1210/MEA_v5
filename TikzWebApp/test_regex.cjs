const oldSize = 'normalsize'; 
const regex = new RegExp('\\\\' + oldSize + '(?![a-zA-Z])', 'g'); 
console.log(regex); 
console.log('\\normalsize something'.replace(regex, '\\large'));
