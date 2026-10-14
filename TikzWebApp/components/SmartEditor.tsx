import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import Editor from 'react-simple-code-editor';
import Prism from 'prismjs';
import 'prismjs/components/prism-latex';
import 'prismjs/themes/prism.css';
import { TikzError } from '../utils/tikzOptimizer';

function injectMarks(html: string, marks: {start: number, end: number, className: string, title: string}[]) {
  marks.sort((a, b) => a.start - b.start);
  
  let result = '';
  let rawIndex = 0;
  let htmlIndex = 0;
  let markIndex = 0;
  let activeMarks: typeof marks = [];
  
  while (htmlIndex < html.length || markIndex < marks.length || activeMarks.length > 0) {
    // Check if any marks start here
    while (markIndex < marks.length && marks[markIndex].start === rawIndex) {
      activeMarks.push(marks[markIndex]);
      result += `<mark class="${marks[markIndex].className}" title="${marks[markIndex].title.replace(/"/g, '&quot;')}">`;
      markIndex++;
    }
    
    // Check if any marks end here
    let endedMarks = [];
    for (let i = 0; i < activeMarks.length; i++) {
      if (activeMarks[i].end === rawIndex) {
        result += `</mark>`;
        endedMarks.push(i);
      }
    }
    for (let i = endedMarks.length - 1; i >= 0; i--) {
      activeMarks.splice(endedMarks[i], 1);
    }
    
    if (htmlIndex >= html.length) break;
    
    // Handle HTML tags
    if (html[htmlIndex] === '<') {
      let tagEnd = html.indexOf('>', htmlIndex);
      if (tagEnd === -1) tagEnd = html.length - 1;
      
      // If we have active marks, we need to close them before the tag and reopen them after
      if (activeMarks.length > 0) {
        for (let i = activeMarks.length - 1; i >= 0; i--) result += `</mark>`;
        result += html.substring(htmlIndex, tagEnd + 1);
        for (let i = 0; i < activeMarks.length; i++) result += `<mark class="${activeMarks[i].className}" title="${activeMarks[i].title.replace(/"/g, '&quot;')}">`;
      } else {
        result += html.substring(htmlIndex, tagEnd + 1);
      }
      
      htmlIndex = tagEnd + 1;
      continue;
    }
    
    // Handle HTML entities
    let charLength = 1;
    let charStr = html[htmlIndex];
    if (html[htmlIndex] === '&') {
      let entityEnd = html.indexOf(';', htmlIndex);
      if (entityEnd !== -1 && entityEnd - htmlIndex < 10) {
        charLength = entityEnd - htmlIndex + 1;
        charStr = html.substring(htmlIndex, entityEnd + 1);
      }
    }
    
    result += charStr;
    rawIndex++;
    htmlIndex += charLength;
  }
  
  return result;
}

// Custom TikZ grammar for Prism
Prism.languages.tikz = {
  'comment': /%.*/,
  'math-mode': {
    pattern: /\$[^$]+\$/,
    inside: {
      'math-command': {
        pattern: /\\[a-zA-Z]+/,
        alias: 'variable' // orange
      },
      'math-number': {
        pattern: /\b\d+(?:\.\d+)?\b/,
        alias: 'string' // green
      },
      'math-delimiter': {
        pattern: /\$/,
        alias: 'string' // green
      }
    }
  },
  'environment': {
    pattern: /\\(?:begin|end)\{[^}]+\}/,
    inside: {
      'environment-command': {
        pattern: /^\\(?:begin|end)/,
        alias: 'keyword' // teal
      },
      'punctuation': /[\{\}]/,
      'environment-name': {
        pattern: /[^\{\}]+/,
        alias: 'class-name' // cyan
      }
    }
  },
  'math-command': {
    pattern: /\\(?:dfrac|sqrt|infty|frac|int|sum|prod|alpha|beta|gamma|delta|theta|pi|sigma|phi|omega|Large|huge|small|tiny)\b/,
    alias: 'variable' // orange
  },
  'tikz-command': {
    pattern: /\\(?:path|draw|fill|node|coordinate|clip|tkzTabInit|tkzTabLine|tkz[a-zA-Z]+)\b/,
    alias: 'string' // green
  },
  'command': {
    pattern: /\\[a-zA-Z@]+/,
    alias: 'keyword' // teal
  },
  'options': {
    pattern: /\[[^\]]+\]/,
    inside: {
      'punctuation': /[\[\]=,]/,
      'command': {
        pattern: /\\[a-zA-Z@]+/,
        alias: 'keyword'
      }
    }
  },
  'coordinate': {
    pattern: /\([^\)]+\)/,
    inside: {
      'punctuation': /[\(\),]/,
      'number': /-?\d+(?:\.\d+)?/
    }
  },
  'braces': {
    pattern: /\{[^\}]*\}/,
    inside: {
      'punctuation': /[\{\}]/,
      'command': {
        pattern: /\\[a-zA-Z@]+/,
        alias: 'keyword'
      }
    }
  },
  'operator': /--|\.\.|->|<-|-stealth|stealth-|\|-|-\|/,
  'punctuation': /[;,]/
};


const TIKZ_SUGGESTIONS = [
  { label: '\\draw', insertText: '\\draw [line width=0.6pt] () -- ();' },
  { label: '\\fill', insertText: '\\fill [color=gray!20] () circle (1cm);' },
  { label: '\\path', insertText: '\\path () -- () node[midway] {};' },
  { label: '\\node', insertText: '\\node [above] at () {$A$};' },
  { label: '\\coordinate', insertText: '\\coordinate (A) at ();' },
  { label: '\\begin{tikzpicture}', insertText: '\\begin{tikzpicture}[\n  >=stealth, line join=round,\n  every node/.style={font=\\normalsize}\n]\n  \n\\end{tikzpicture}' },
  { label: '\\end{tikzpicture}', insertText: '\\end{tikzpicture}' },
  { label: '\\foreach', insertText: '\\foreach \\p/\\goc in {} {\n  \\draw (\\p) circle (0.4pt) node[shift={(\\goc:9pt)}]{\\$\\p\\$};\n}' },
  { label: 'circle', insertText: 'circle ()' },
  { label: 'rectangle', insertText: 'rectangle ()' },
  { label: '\\tkzTabInit', insertText: '\\tkzTabInit[nocadre=false, lgt=1.2, espcl=2.5, deltacl=0.6]\n  {$x$/0.7, $y$/2}\n  {$-\\infty$, $+\\infty$}' },
  { label: '\\tkzTabLine', insertText: '\\tkzTabLine{, +, 0, -, }' },
  { label: 'every', insertText: 'every node/.style={font=\\normalsize}' },
  { label: 'line width', insertText: 'line width=0.6pt' },
  { label: '-Stealth', insertText: '-Stealth' },
  { label: 'double', insertText: 'double distance=1pt, double=white, line width=0.4pt' },
  { label: 'pattern', insertText: 'pattern={Lines[angle=45, distance=3pt, line width=0.3pt]}, pattern color=gray' },
  { label: 'shift', insertText: 'shift={(:9pt)}' },
  { label: '\\clip', insertText: '\\clip () rectangle ();' },
  { label: 'dashed', insertText: 'dashed, line width=0.4pt' },
  { label: '\\filldraw', insertText: '\\filldraw [fill=gray!20, draw=black] () circle ();' },
  { label: '\\tkzDefPoint', insertText: '\\tkzDefPoint(0,0){A}' },
  { label: '\\tkzDrawPolygon', insertText: '\\tkzDrawPolygon(A,B,C)' },
  { label: '\\tkzDrawSegments', insertText: '\\tkzDrawSegments(A,B C,D)' },
  { label: '\\tkzDrawPoints', insertText: '\\tkzDrawPoints(A,B,C)' },
  { label: '\\tkzLabelPoints', insertText: '\\tkzLabelPoints[below](A,B,C)' },
  { label: '\\tkzMarkRightAngle', insertText: '\\tkzMarkRightAngle[size=0.2](A,B,C)' },
  { label: '\\tkzMarkAngle', insertText: '\\tkzMarkAngle[size=0.4,mark=|](A,B,C)' },
  { label: '\\draw[->]', insertText: '\\draw [->, >=stealth, line width=0.6pt] () -- ();' },
];

interface SmartEditorProps {
  code: string;
  setCode: (code: string) => void;
  isReadOnly: boolean;
  searchQuery: string;
  replaceQuery: string;
  onReplaceAll: () => void;
  setMatchCount: (count: number) => void;
  isBbtNoFrame?: boolean;
}

const SmartEditor: React.FC<SmartEditorProps> = ({
  code,
  setCode,
  isReadOnly,
  searchQuery,
  replaceQuery,
  onReplaceAll,
  setMatchCount,
  isBbtNoFrame
}) => {
  const [suggestions, setSuggestions] = useState<typeof TIKZ_SUGGESTIONS>([]);
  const [activeSuggestion, setActiveSuggestion] = useState(0);
  const [currentPrefix, setCurrentPrefix] = useState("");
  const [cursorPos, setCursorPos] = useState({ top: 0, left: 0 });
  const editorRef = useRef<any>(null);

  // Tự động ẩn gợi ý sau 10 giây
  useEffect(() => {
    if (suggestions.length > 0) {
      const timer = setTimeout(() => {
        setSuggestions([]);
      }, 10000);
      return () => clearTimeout(timer);
    }
  }, [suggestions]);

  // Calculate match count in a useEffect to avoid setState during render
  useEffect(() => {
    if (!searchQuery) {
      setMatchCount(0);
      return;
    }
    try {
      let regexStr = searchQuery;
      
      // A. Cú pháp TikZ
      if (searchQuery === '\\draw commands') regexStr = '\\\\draw[^;]*;';
      else if (searchQuery === '\\node commands') regexStr = '\\\\node[^;]*;';
      else if (searchQuery === '\\path commands') regexStr = '\\\\path[^;]*;';
      else if (searchQuery === '\\fill commands') regexStr = '\\\\fill[^;]*;';
      // B. Đối tượng hình học
      else if (searchQuery === 'circle' || searchQuery === 'ellipse') regexStr = '\\b(circle|ellipse)\\b';
      else if (searchQuery === 'rectangle') regexStr = '\\brectangle\\b';
      else if (searchQuery === 'node' || searchQuery === 'coordinate') regexStr = '\\b(node|coordinate)\\b';
      else if (searchQuery === 'plot' || searchQuery === 'to' || searchQuery === 'controls') regexStr = '\\b(plot|to|controls)\\b';
      // C. Màu sắc
      else if (searchQuery === 'primary colors') regexStr = '\\b(red|blue|yellow|green|black|white|cyan|magenta)\\b';
      else if (searchQuery === 'secondary colors') regexStr = '\\b(orange|purple|brown|pink|gray|teal|lime)\\b';
      
      const isSmartQuery = [
        '\\draw commands', '\\node commands', '\\path commands', '\\fill commands',
        'circle', 'ellipse', 'rectangle', 'node', 'coordinate', 'plot', 'to', 'controls',
        'primary colors', 'secondary colors'
      ].includes(searchQuery);

      if (!isSmartQuery && !searchQuery.startsWith('\\\\')) {
         regexStr = searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      }

      const regex = new RegExp(`(${regexStr})`, 'gi');
      const matches = code.match(regex);
      setMatchCount(matches ? matches.length : 0);
    } catch (e) {
      setMatchCount(0);
    }
  }, [code, searchQuery, setMatchCount]);

  // Highlighting logic with search results
  const highlightCode = useCallback((codeToHighlight: string) => {
    let highlighted = Prism.highlight(codeToHighlight, Prism.languages.tikz, 'tikz');

    // 2. Highlight search results
    if (searchQuery) {
      try {
        // Smart search logic
        let regexStr = searchQuery;
        
        // A. Cú pháp TikZ
        if (searchQuery === '\\draw commands') regexStr = '\\\\draw[^;]*;';
        else if (searchQuery === '\\node commands') regexStr = '\\\\node[^;]*;';
        else if (searchQuery === '\\path commands') regexStr = '\\\\path[^;]*;';
        else if (searchQuery === '\\fill commands') regexStr = '\\\\fill[^;]*;';
        // B. Đối tượng hình học
        else if (searchQuery === 'circle' || searchQuery === 'ellipse') regexStr = '\\b(circle|ellipse)\\b';
        else if (searchQuery === 'rectangle') regexStr = '\\brectangle\\b';
        else if (searchQuery === 'node' || searchQuery === 'coordinate') regexStr = '\\b(node|coordinate)\\b';
        else if (searchQuery === 'plot' || searchQuery === 'to' || searchQuery === 'controls') regexStr = '\\b(plot|to|controls)\\b';
        // C. Màu sắc
        else if (searchQuery === 'primary colors') regexStr = '\\b(red|blue|yellow|green|black|white|cyan|magenta)\\b';
        else if (searchQuery === 'secondary colors') regexStr = '\\b(orange|purple|brown|pink|gray|teal|lime)\\b';
        
        // Escape regex if it's a normal string and not a smart query
        const isSmartQuery = [
          '\\draw commands', '\\node commands', '\\path commands', '\\fill commands',
          'circle', 'ellipse', 'rectangle', 'node', 'coordinate', 'plot', 'to', 'controls',
          'primary colors', 'secondary colors'
        ].includes(searchQuery);

        if (!isSmartQuery && !searchQuery.startsWith('\\\\')) {
           // Basic escape for normal search
           regexStr = searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        }

        // Highlight matches in yellow
        // We need to be careful not to break HTML tags from Prism
        const safeRegex = new RegExp(`(?![^<]*>)(${regexStr})`, 'gi');
        const parts = highlighted.split(safeRegex);
        if (parts.length > 1) {
          highlighted = highlighted.replace(safeRegex, '<mark class="bg-yellow-300 dark:bg-yellow-600 text-black dark:text-white rounded px-0.5">$&</mark>');
        }
      } catch (e) {
         // Ignore errors during highlight
      }
    }
    // Add line numbers by wrapping each line in a span, preserving open tags
    const lines = highlighted.split('\n');
    let openTags: string[] = [];
    
    highlighted = lines.map((line, i) => {
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
        const tagMatch = tag.match(/<([a-z0-9]+)/i);
        const tagName = tagMatch ? tagMatch[1] : 'span';
        return `</${tagName}>`;
      }).join('');
      
      return `<span class="editor-line" data-line="${i + 1}">${prefix}${line}${suffix}</span>`;
    }).join('\n');
    
    return highlighted;
  }, [searchQuery]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'R') {
        e.preventDefault();
        onReplaceAll();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onReplaceAll]);

  
  const handleKeyDownCapture = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (suggestions.length > 0) {
      if (e.key === 'Tab' || e.key === 'Enter') {
        e.preventDefault();
        e.stopPropagation();
        applySuggestion(suggestions[activeSuggestion]);
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        e.stopPropagation();
        setActiveSuggestion((a) => (a + 1) % suggestions.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        e.stopPropagation();
        setActiveSuggestion((a) => (a - 1 + suggestions.length) % suggestions.length);
      } else if (e.key === 'Escape') {
        setSuggestions([]);
      }
    }
  };

  const applySuggestion = (sug: typeof TIKZ_SUGGESTIONS[0]) => {
    const activeEl = document.activeElement as HTMLTextAreaElement;
    const pos = activeEl ? activeEl.selectionStart : code.length;
    
    const textBefore = code.slice(0, pos);
    const textAfter = code.slice(pos);
    const prefixLength = currentPrefix.length;
    
    let insertTextContent = sug.insertText;
    if (isBbtNoFrame && insertTextContent.includes('nocadre=false')) {
      insertTextContent = insertTextContent.replace(/nocadre=false/g, 'nocadre=true');
    }
    
    const newCode = textBefore.slice(0, -prefixLength) + insertTextContent + textAfter;
    
    setCode(newCode);
    setSuggestions([]);
    
    setTimeout(() => {
      if (activeEl) {
        let newPos = pos - prefixLength + insertTextContent.length;
        const cursorOffset1 = insertTextContent.indexOf('()');
        const cursorOffset2 = insertTextContent.indexOf('{}');
        if (cursorOffset1 !== -1) {
           newPos = pos - prefixLength + cursorOffset1 + 1;
        } else if (cursorOffset2 !== -1) {
           newPos = pos - prefixLength + cursorOffset2 + 1;
        } else if (insertTextContent.includes('\n  \n')) {
           newPos = pos - prefixLength + insertTextContent.indexOf('\n  \n') + 3;
        }
        activeEl.selectionStart = newPos;
        activeEl.selectionEnd = newPos;
        activeEl.focus();
      }
    }, 10);
  };

  // Smart typing suggestions
  
  const handleChange = (newCode: string) => {
    setCode(newCode);
    
    const activeEl = document.activeElement as HTMLTextAreaElement;
    if (!activeEl || activeEl.tagName !== 'TEXTAREA') {
      setSuggestions([]);
      return;
    }
    
    const pos = activeEl.selectionStart;
    const textBefore = newCode.slice(0, pos);
    
    // Split to find the word being typed
    const parts = textBefore.split(/[ \n\t{}()[\];,=\/]/);
    const prefix = parts[parts.length - 1];

    if (prefix.length >= 2) {
      const matched = TIKZ_SUGGESTIONS.filter(s => 
        s.label.toLowerCase().startsWith(prefix.toLowerCase())
      ).slice(0, 8);
      
      if (matched.length > 0) {
        setSuggestions(matched);
        setCurrentPrefix(prefix);
        setActiveSuggestion(0);
      } else {
        setSuggestions([]);
      }
    } else {
      setSuggestions([]);
    }
  };


  return (
    <div className="relative flex-1 w-full h-full overflow-auto" onKeyDownCapture={handleKeyDownCapture}>
      <style>{`
        .language-tikz .token.keyword { color: #008080 !important; }
        .language-tikz .token.class-name { color: #00BCD4 !important; }
        .language-tikz .token.string { color: #008000 !important; }
        .language-tikz .token.variable { color: #FF9800 !important; }
        .language-tikz .token.number { color: inherit !important; }
        .language-tikz .token.punctuation { color: #555555 !important; }
        .language-tikz .token.operator { color: #555555 !important; }
        .language-tikz .token.comment { color: #888888 !important; font-style: italic; }
        
        .dark .language-tikz .token.keyword { color: #4DB6AC !important; }
        .dark .language-tikz .token.class-name { color: #80DEEA !important; }
        .dark .language-tikz .token.string { color: #81C784 !important; }
        .dark .language-tikz .token.variable { color: #FFB74D !important; }
        .dark .language-tikz .token.number { color: inherit !important; }
        .dark .language-tikz .token.punctuation { color: #AAAAAA !important; }
        .dark .language-tikz .token.operator { color: #AAAAAA !important; }

        .smart-editor-container {
          position: relative;
        }

        .smart-editor-container::before {
          content: "";
          position: absolute;
          top: 0;
          left: 0;
          width: 44px;
          height: 100%;
          background-color: #f8fafc;
          border-right: 1px solid #e2e8f0;
          z-index: 0;
          pointer-events: none;
        }
        
        .dark .smart-editor-container::before {
          background-color: #0f172a;
          border-right: 1px solid #1e293b;
        }

        .smart-editor-container textarea, .smart-editor-container pre {
          white-space: pre-wrap !important;
          word-break: break-word !important;
          overflow-wrap: anywhere !important;
          padding-left: 48px !important;
        }
        
        .editor-line {
          position: relative;
          z-index: 1;
        }
        
        .editor-line::before {
          content: attr(data-line);
          position: absolute;
          left: -40px;
          width: 32px;
          text-align: right;
          color: #64748b;
          user-select: none;
          font-size: 0.9em;
          font-weight: 500;
          pointer-events: none;
        }
        
        .dark .editor-line::before {
          color: #94a3b8;
        }
      `}</style>
      <Editor
        value={code}
        onValueChange={handleChange}
        highlight={highlightCode}
        padding={16}
        readOnly={isReadOnly}
        className="smart-editor-container font-mono text-[11pt] min-h-full bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-200 focus:outline-none"
        style={{
          fontFamily: '"JetBrains Mono", "Fira Code", monospace',
        }}
        textareaClassName="focus:outline-none"
      />
      {suggestions.length > 0 && (
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white dark:bg-slate-800 border border-cyan-500 rounded-xl shadow-2xl p-2 z-50 min-w-[280px] max-w-[420px]">
          <div className="flex justify-between items-center px-1 mb-2 border-b border-slate-200 dark:border-slate-700 pb-1">
            <span className="text-[10px] font-semibold tracking-wider uppercase text-slate-400">Cú pháp & Mã code</span>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-slate-400 tracking-wide">Tab / Enter</span>
              <button 
                onClick={() => setSuggestions([])}
                className="text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition-colors p-0.5 rounded-sm"
                title="Đóng"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
          </div>
          <div className="flex flex-col gap-1 max-h-[300px] overflow-y-auto">
            {suggestions.map((sug, i) => (
              <button
                key={i}
                className={`block w-full text-left px-3 py-2 text-sm font-mono rounded transition-colors ${i === activeSuggestion ? 'bg-cyan-100 dark:bg-cyan-900/60 text-cyan-800 dark:text-cyan-200' : 'hover:bg-slate-50 dark:hover:bg-slate-700/50 text-slate-700 dark:text-slate-300'}`}
                onClick={() => applySuggestion(sug)}
              >
                <div className="flex flex-col gap-0.5">
                  <span className="font-semibold text-[13px]">{sug.label}</span>
                  <span className="text-[11px] opacity-70 whitespace-pre-wrap leading-tight">{sug.insertText}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SmartEditor;
