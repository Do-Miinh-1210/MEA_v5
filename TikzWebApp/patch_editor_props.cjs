const fs = require('fs');
let content = fs.readFileSync('components/Editor.tsx', 'utf8');

const oldProps = `  isBbtNoFrame?: boolean;
}

const Editor: React.FC<EditorProps> = ({ 
  code, 
  setCode, 
  onSaveClick, 
  isLoading, 
  isReadOnly,
  searchQuery,
  replaceQuery,
  setMatchCount,
  isNoteEnabled,
  setIsNoteEnabled,
  userEmail,
  isBbtNoFrame
}) => {`;

const newProps = `  isBbtNoFrame?: boolean;
  setIsBbtNoFrame?: (val: boolean) => void;
  isAsymptoteHidden?: boolean;
  setIsAsymptoteHidden?: (val: boolean) => void;
  isFunctionHidden?: boolean;
  setIsFunctionHidden?: (val: boolean) => void;
  isComponentFunctionHidden?: boolean;
  setIsComponentFunctionHidden?: (val: boolean) => void;
}

const Editor: React.FC<EditorProps> = ({ 
  code, 
  setCode, 
  onSaveClick, 
  isLoading, 
  isReadOnly,
  searchQuery,
  replaceQuery,
  setMatchCount,
  isNoteEnabled,
  setIsNoteEnabled,
  userEmail,
  isBbtNoFrame,
  setIsBbtNoFrame,
  isAsymptoteHidden,
  setIsAsymptoteHidden,
  isFunctionHidden,
  setIsFunctionHidden,
  isComponentFunctionHidden,
  setIsComponentFunctionHidden
}) => {`;

content = content.replace(oldProps, newProps);

fs.writeFileSync('components/Editor.tsx', content);
