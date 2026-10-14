const fs = require('fs');
let content = fs.readFileSync('components/AIAssistant.tsx', 'utf8');

const oldProps = `interface AIAssistantProps {
  setCode: (code: string) => void;
  onApiKeyInvalid: (message: string) => void;
  isReadOnly: boolean;
  onFilesDropped?: (files: { name: string; content: string }[]) => void;
  userLibrary?: Category;
  isNoteEnabled: boolean;
  isBbtNoFrame?: boolean;
  onBoilerplateRemoved?: () => void;
  width?: number;
  currentCode?: string;
}`;

const newProps = `interface AIAssistantProps {
  setCode: (code: string) => void;
  onApiKeyInvalid: (message: string) => void;
  isReadOnly: boolean;
  onFilesDropped?: (files: { name: string; content: string }[]) => void;
  userLibrary?: Category;
  isNoteEnabled: boolean;
  isBbtNoFrame?: boolean;
  onBoilerplateRemoved?: () => void;
  width?: number;
  currentCode?: string;
  onLoadingChange?: (loading: boolean) => void;
}`;

content = content.replace(oldProps, newProps);

const oldComponentDef = `const AIAssistant: React.FC<AIAssistantProps> = ({ setCode, onApiKeyInvalid, isReadOnly, onFilesDropped, userLibrary, isNoteEnabled, isBbtNoFrame, onBoilerplateRemoved, width, currentCode }) => {`;
const newComponentDef = `const AIAssistant: React.FC<AIAssistantProps> = ({ setCode, onApiKeyInvalid, isReadOnly, onFilesDropped, userLibrary, isNoteEnabled, isBbtNoFrame, onBoilerplateRemoved, width, currentCode, onLoadingChange }) => {`;

content = content.replace(oldComponentDef, newComponentDef);

const oldEffect = `  const [isBbtChecked, setIsBbtChecked] = useState(false);`;
const newEffect = `  const [isBbtChecked, setIsBbtChecked] = useState(false);

  useEffect(() => {
    if (onLoadingChange) {
      onLoadingChange(isGenerating);
    }
  }, [isGenerating, onLoadingChange]);`;

content = content.replace(oldEffect, newEffect);

fs.writeFileSync('components/AIAssistant.tsx', content);
