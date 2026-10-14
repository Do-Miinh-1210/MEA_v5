import React, { useState } from 'react';
import { CopyIcon, ChevronDownIcon, ChevronUpIcon, TrashIcon, SaveIcon } from '../constants';
import { playTaskCompleteSound, playErrorSound } from '../utils/audio';
import SmartEditor from './SmartEditor';

import { getOptimizedLatexCode, extractTikzCodeFromFull } from '../utils/latexBuilder';

const INSPIRATIONAL_QUOTES = [
  "Bạn vào mục Hỏi - Đáp để biết chi tiết các chức năng của App\n\n",
  "\"Thành công là kết quả của sự hoàn hảo, làm việc chăm chỉ, học hỏi từ thất bại, lòng trung thành và sự kiên trì.\" - Colin Powell",
  "\"Kỷ luật là cầu nối giữa mục tiêu và thành tựu.\" - Jim Rohn",
  "\"Đam mê là năng lượng. Hãy cảm nhận sức mạnh đến từ việc tập trung vào những gì làm bạn hứng thú.\" - Oprah Winfrey",
  "\"Sự kiên trì không phải là một cuộc chạy đua đường dài; nó là nhiều cuộc chạy đua ngắn liên tiếp nhau.\" - Walter Elliot",
  "\"Thất bại chỉ là cơ hội để bắt đầu lại một cách thông minh hơn.\" - Henry Ford",
  "\"Đừng sợ thất bại. Không phải thất bại, mà là mục tiêu quá thấp mới là tội lỗi. Trong những nỗ lực lớn lao, ngay cả thất bại cũng là vinh quang.\" - Bruce Lee",
  "\"Sự khác biệt giữa những người thành công và những người khác không phải là sự thiếu hụt sức mạnh, không phải là sự thiếu hụt kiến thức, mà đúng hơn là sự thiếu hụt ý chí.\" - Vince Lombardi",
  "\"Thiên tài là 1% cảm hứng và 99% mồ hôi.\" - Thomas Edison",
  "\"Không có bí mật nào cho thành công. Nó là kết quả của sự chuẩn bị, làm việc chăm chỉ và học hỏi từ thất bại.\" - Colin Powell",
  "\"Người có lòng kiên nhẫn có thể đạt được bất cứ điều gì họ muốn.\" - Benjamin Franklin",
  "\"Hãy làm việc khi người khác đang ngủ. Học hỏi khi người khác đang tiệc tùng. Tiết kiệm khi người khác đang tiêu xài. Và bạn sẽ sống cuộc sống mà người khác đang mơ ước.\" - Khuyết danh",
  "\"Thành công không phải là cuối cùng, thất bại không phải là chết người: Lòng can đảm đi tiếp mới là điều quan trọng.\" - Winston Churchill"
];

const ScrollingQuotes = () => {
  return (
    <div className="absolute inset-0 z-10 bg-transparent overflow-hidden pointer-events-none rounded-lg flex flex-col">
      <style>
        {`
          @keyframes scrollUp {
            from { top: 100%; transform: translateY(0); }
            to { top: 0; transform: translateY(-100%); }
          }
          .animate-scroll-up {
            animation: scrollUp 40s linear infinite;
          }
        `}
      </style>
      <div className="flex-1 relative overflow-hidden">
        <div className="animate-scroll-up absolute left-0 w-full flex flex-col gap-8 p-6">
          {INSPIRATIONAL_QUOTES.map((quote, idx) => (
            <p key={idx} className="text-teal-600 dark:text-teal-400 text-[13pt] font-sans text-center leading-relaxed italic whitespace-pre-line">
              {quote}
            </p>
          ))}
        </div>
      </div>
      <div className="absolute bottom-4 left-0 w-full flex justify-center gap-3">
         <div className="w-3 h-3 bg-cyan-400 rounded-full animate-bounce shadow-[0_0_10px_rgba(34,211,238,0.6)]" style={{ animationDelay: '0ms' }}></div>
         <div className="w-3 h-3 bg-teal-400 rounded-full animate-bounce shadow-[0_0_10px_rgba(45,212,191,0.6)]" style={{ animationDelay: '150ms' }}></div>
         <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce shadow-[0_0_10px_rgba(96,165,250,0.6)]" style={{ animationDelay: '300ms' }}></div>
      </div>
    </div>
  );
};

interface EditorProps {
  code: string;
  setCode: (code: string) => void;
  onSaveClick: () => void;
  isLoading: boolean;
  onApiKeyInvalid: (message: string) => void;
  isReadOnly: boolean;
  searchQuery: string;
  replaceQuery: string;
  setMatchCount: (count: number) => void;
  isNoteEnabled: boolean;
  setIsNoteEnabled: (enabled: boolean) => void;
  userEmail?: string;
  isBbtNoFrame?: boolean;
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
}) => {
  const [copyStatus, setCopyStatus] = useState('Sao chép');
  const [isEditorVisible, setIsEditorVisible] = useState(true);
  const [showFullCode, setShowFullCode] = useState(false);
  const [fontSize, setFontSize] = useState('normalsize');
  const [showOptionsMenu, setShowOptionsMenu] = useState(false);
const isGeneratingMessage = code.startsWith('%%GENERATING%%\n');
  const displayCode = isGeneratingMessage ? code.replace('%%GENERATING%%\n', '') : code;

  React.useEffect(() => {
    if (isGeneratingMessage) {
      setFontSize('normalsize');
    }
  }, [isGeneratingMessage]);

  const handleFontSizeChange = (newSize: string) => {
    const oldSize = fontSize;
    setFontSize(newSize);
    if (!code.trim() || isReadOnly) return;
    // Replace old font size with new font size in the code
    const regex = new RegExp('\\\\' + oldSize + '(?![a-zA-Z])', 'g');
    setCode(code.replace(regex, '\\' + newSize));
  };

  const getFullLatexCode = () => {
    return getOptimizedLatexCode(code);
  };

  const handleCopy = () => {
    const fullCode = getFullLatexCode();
    navigator.clipboard.writeText(fullCode).then(() => {
      setCopyStatus('Đã sao chép!');
      playTaskCompleteSound();
      setTimeout(() => setCopyStatus('Sao chép'), 2000);
    }, () => {
      setCopyStatus('Thất bại!');
      playErrorSound();
      setTimeout(() => setCopyStatus('Sao chép'), 2000);
    });
  };

  const handleClearCode = () => {
    if (isReadOnly) return;
    setCode('');
  };

  const handleOpenInOverleaf = () => {
    const fullCode = getFullLatexCode();
    
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = 'https://www.overleaf.com/docs';
    form.target = '_blank';

    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'snip';
    input.value = fullCode;

    form.appendChild(input);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
  };

  const handleReplaceAll = () => {
    if (!searchQuery || isReadOnly) return;
    // We can trigger the replace logic here, but it's already in SmartSearchBox.
    // Actually, SmartSearchBox handles the replace button click.
    // But Ctrl+Shift+R is handled in SmartEditor, so we need to pass the replace logic down or handle it there.
    // For simplicity, we can just let SmartSearchBox handle it, or pass a callback.
    // Let's pass a callback that does the same thing as SmartSearchBox.
    import('../utils/tikzOptimizer').then(({ smartSearch }) => {
      const { regex } = smartSearch(code, searchQuery);
      if (regex) {
        const newCode = code.replace(regex, replaceQuery);
        setCode(newCode);
      } else {
        const newCode = code.split(searchQuery).join(replaceQuery);
        setCode(newCode);
      }
    });
  };

  const handleToggleNote = async () => {
    const newNoteState = !isNoteEnabled;
    setIsNoteEnabled(newNoteState);
    
    if (!code.trim() || isGeneratingMessage || isReadOnly) return;

    if (!newNoteState) {
      // Remove notes instantly
      const newCode = code.replace(/^\s*%.*\n?/gm, '').trim();
      setCode(newCode);
    } else {
      // Add notes instantly via heuristic
      try {
        const { toggleCodeNotes } = await import('../services/geminiService');
        const newCode = await toggleCodeNotes(code, true);
        setCode(newCode);
      } catch (error) {
        console.error("Error toggling notes:", error);
      }
    }
  };

  return (
    <main className="flex-1 min-w-0 min-h-0 bg-white dark:bg-slate-900 flex flex-col p-[0.2cm] border-[2.5pt] border-yellow-600 rounded-lg">
          <div className="flex-1 flex flex-col border-[2pt] border-dashed border-yellow-500 rounded-lg p-1 bg-white dark:bg-slate-900 min-h-0">
              <div className="flex items-center justify-between px-2 py-0.5 border-y-[1.2pt] border-slate-300 dark:border-slate-600">
                  <div className="flex items-center">
                      <button
                        onClick={() => setShowFullCode(!showFullCode)}
                        className="text-base font-medium text-cyan-500 dark:text-cyan-400 hover:text-cyan-600 dark:hover:text-cyan-300 px-2 py-1 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors whitespace-nowrap"
                        title={showFullCode ? 'Chỉ hiển thị code TikZ' : 'Hiển thị toàn bộ file LaTeX'}
                      >
                        {showFullCode ? 'TikZ code' : 'Full code'}
                      </button>
                      <span className="text-slate-300 dark:text-slate-600 mx-1">|</span>
                      <button
                        onClick={handleToggleNote}
                        disabled={isGeneratingMessage}
                        className="text-base font-medium text-purple-500 dark:text-purple-400 hover:text-purple-600 dark:hover:text-purple-300 px-2 py-1 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
                        title={isNoteEnabled ? 'Tắt và xóa chú thích khỏi code' : 'Bật và thêm chú thích vào code'}
                      >
                        {isNoteEnabled ? 'No note' : 'Note'}
                      </button>
                      <div className="flex items-center ml-2 space-x-1 cursor-pointer select-none hover:bg-slate-100 dark:hover:bg-slate-800 px-1 py-1 rounded" title="Chọn kích thước font chữ">
                        <select
                          className="bg-transparent text-slate-700 dark:text-slate-300 text-sm cursor-pointer outline-none border-none focus:ring-0 disabled:opacity-50"
                          value={fontSize}
                          onChange={(e) => handleFontSizeChange(e.target.value)}
                          disabled={isGeneratingMessage || isReadOnly}
                        >
                          {['normalsize', 'large', 'Large', 'scriptsize', 'footnotesize', 'small'].map(size => (
                            <option key={size} value={size} className="bg-white dark:bg-slate-800">{size}</option>
                          ))}
                        </select>
                      </div>
                  </div>
                  <div className="flex items-center space-x-1.5">
                      {/* Tùy chọn Options Menu */}
                      <div className="relative" onMouseLeave={() => setShowOptionsMenu(false)}>
                        <button
                          onClick={() => {
                            setShowOptionsMenu(!showOptionsMenu);
                          }}
                          className="flex items-center gap-1 mr-2 text-sm font-medium text-slate-700 dark:text-slate-300 cursor-pointer hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors bg-transparent border-none px-2 py-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800"
                          title="Tùy chọn hiển thị đối tượng"
                        >
                          <span>Tùy chọn</span>
                          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3 h-3">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                          </svg>
                        </button>
                        {showOptionsMenu && (
                          <div className="absolute top-full left-0 pt-1 z-50 w-44 text-sm">
                            <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md shadow-lg overflow-hidden">

                            <label className={`flex items-center px-3 py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 ${!code?.includes('tkzTab') ? 'opacity-50 cursor-not-allowed' : ''}`}>
                              <input
                                type="checkbox"
                                className="mr-2 cursor-pointer rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                                checked={!isBbtNoFrame}
                                onChange={() => {
                                  if (setIsBbtNoFrame) setIsBbtNoFrame(!isBbtNoFrame);
                                }}
                                disabled={!code?.includes('tkzTab')}
                              />
                              <span className="text-slate-700 dark:text-slate-300">Viền BBT</span>
                            </label>
                            <label className={`flex items-center px-3 py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 ${!code?.includes('% --- TIỆM CẬN ---') ? 'opacity-50 cursor-not-allowed' : ''}`}>
                              <input
                                type="checkbox"
                                className="mr-2 cursor-pointer rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                                checked={!isAsymptoteHidden}
                                onChange={() => {
                                  if (setIsAsymptoteHidden) setIsAsymptoteHidden(!isAsymptoteHidden);
                                }}
                                disabled={!code?.includes('% --- TIỆM CẬN ---')}
                              />
                              <span className="text-slate-700 dark:text-slate-300">Nhãn tiệm cận</span>
                            </label>
                            <label className={`flex items-center px-3 py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 ${!code?.includes('% --- ĐỒ THỊ HÀM SỐ ---') ? 'opacity-50 cursor-not-allowed' : ''}`}>
                              <input
                                type="checkbox"
                                className="mr-2 cursor-pointer rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                                checked={!isFunctionHidden}
                                onChange={() => {
                                  if (setIsFunctionHidden) setIsFunctionHidden(!isFunctionHidden);
                                }}
                                disabled={!code?.includes('% --- ĐỒ THỊ HÀM SỐ ---')}
                              />
                              <span className="text-slate-700 dark:text-slate-300">Nhãn hàm số</span>
                            </label>
                            <label className={`flex items-center px-3 py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 ${!code?.includes('% --- ĐỒ THỊ HÀM SỐ THÀNH PHẦN ---') ? 'opacity-50 cursor-not-allowed' : ''}`}>
                              <input
                                type="checkbox"
                                className="mr-2 cursor-pointer rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                                checked={!isComponentFunctionHidden}
                                onChange={() => {
                                  if (setIsComponentFunctionHidden) setIsComponentFunctionHidden(!isComponentFunctionHidden);
                                }}
                                disabled={!code?.includes('% --- ĐỒ THỊ HÀM SỐ THÀNH PHẦN ---')}
                              />
                              <span className="text-slate-700 dark:text-slate-300">Nhãn hàm số thành phần</span>
                            </label>
                          
                            </div>
                          </div>
                        )}
                      </div>
                      <button 
                        onClick={async () => {
                          const fallbackDownload = () => {
                            const element = document.createElement("a");
                            const file = new Blob([getFullLatexCode()], {type: 'text/plain'});
                            element.href = URL.createObjectURL(file);
                            element.download = "tikz_code.tex";
                            document.body.appendChild(element);
                            element.click();
                            document.body.removeChild(element);
                          };

                          try {
                            if ('showSaveFilePicker' in window) {
                              try {
                                const handle = await (window as any).showSaveFilePicker({
                                  suggestedName: 'tikz_code.tex',
                                  types: [{
                                    description: 'TeX File',
                                    accept: {'text/plain': ['.tex']},
                                  }],
                                });
                                const writable = await handle.createWritable();
                                await writable.write(getFullLatexCode());
                                await writable.close();
                              } catch (pickerErr: any) {
                                if (pickerErr.name === 'AbortError') {
                                  return; // User cancelled
                                }
                                // If it fails due to security/iframe restrictions, use fallback
                                console.warn('showSaveFilePicker failed, using fallback:', pickerErr);
                                fallbackDownload();
                              }
                            } else {
                              fallbackDownload();
                            }
                          } catch (err: any) {
                            console.error('Error saving file:', err);
                            fallbackDownload();
                          }
                        }}
                        disabled={isGeneratingMessage || !code.trim()}
                        className={`flex items-center gap-1.5 px-2 py-1.5 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm ${code.trim() && !isGeneratingMessage ? 'text-blue-500 hover:bg-blue-500/20 dark:hover:bg-blue-500/20' : 'hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300'}`}
                        title="Tải file .tex"
                      >
                          
                          Tải TeX
                      </button>
                      <button 
                        onClick={handleCopy} 
                        disabled={isGeneratingMessage}
                        className={`p-1.5 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${code.trim() && !isGeneratingMessage ? 'text-teal-500 hover:bg-teal-500/20 dark:hover:bg-teal-500/20' : 'hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300'}`}
                        title={copyStatus === 'Sao chép' ? 'Sao chép toàn bộ mã LaTeX' : copyStatus}
                      >
                          <CopyIcon className="h-5 w-5" />
                      </button>
                      <button 
                        onClick={handleClearCode}
                        disabled={isReadOnly || isGeneratingMessage}
                        className={`p-1.5 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${code.trim() && !isGeneratingMessage ? 'text-red-500 hover:bg-red-500/20 dark:hover:bg-red-500/20' : 'hover:bg-red-500/20 dark:hover:bg-red-500/20 text-slate-600 dark:text-slate-300 hover:text-red-500 dark:hover:text-red-400'}`}
                        title="Xóa code"
                      >
                          <TrashIcon className="h-5 w-5" />
                      </button>
                      <button
                        onClick={onSaveClick}
                        disabled={isReadOnly || !code.trim() || isGeneratingMessage}
                        className="p-1.5 rounded-md hover:bg-blue-500/20 dark:hover:bg-blue-500/20 text-slate-600 dark:text-slate-300 hover:text-blue-500 dark:hover:text-blue-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        title=" Lưu vào thư viện"
                      >
                        <SaveIcon className="h-5 w-5" />
                      </button>
                      <button 
                        onClick={handleOpenInOverleaf}
                        disabled={isGeneratingMessage}
                        className="bg-green-600 hover:bg-green-700 text-white font-medium py-1 px-2 text-sm rounded-md transition-colors duration-200 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed ml-1"
                      >
                          Overleaf
                      </button>
                  </div>
              </div>

              {isEditorVisible && (
                isGeneratingMessage ? (
                  <div className="flex-1 w-full bg-white dark:bg-slate-900 overflow-hidden relative rounded-b-lg">
                    <style>
                      {`
                        @keyframes scrollUpEditor {
                          from { top: 100%; transform: translateY(0); }
                          to { top: 0; transform: translateY(-100%); }
                        }
                        .animate-scroll-up-editor {
                          animation: scrollUpEditor 80s linear infinite;
                        }
                      `}
                    </style>
                    <div className="animate-scroll-up-editor absolute left-0 w-full flex flex-col gap-8 p-6">
                      <div className="text-teal-600 dark:text-teal-400 text-[13pt] font-sans text-center leading-relaxed whitespace-pre-wrap">
                        {displayCode}
                      </div>
                      {INSPIRATIONAL_QUOTES.map((quote, idx) => (
                        <p key={idx} className="text-teal-600 dark:text-teal-400 text-[13pt] font-sans text-center leading-relaxed italic">
                          {quote}
                        </p>
                      ))}
                    </div>
                    <div className="absolute bottom-4 left-0 w-full flex justify-center gap-3">
                       <div className="w-3 h-3 bg-cyan-400 rounded-full animate-bounce shadow-[0_0_10px_rgba(34,211,238,0.6)]" style={{ animationDelay: '0ms' }}></div>
                       <div className="w-3 h-3 bg-teal-400 rounded-full animate-bounce shadow-[0_0_10px_rgba(45,212,191,0.6)]" style={{ animationDelay: '150ms' }}></div>
                       <div className="w-3 h-3 bg-blue-400 rounded-full animate-bounce shadow-[0_0_10px_rgba(96,165,250,0.6)]" style={{ animationDelay: '300ms' }}></div>
                    </div>
                  </div>
                ) : (
                  <div className="relative flex-1 min-h-0 flex flex-col">
                    <SmartEditor
                    isBbtNoFrame={isBbtNoFrame}
                    code={showFullCode ? getFullLatexCode() : code}
                    setCode={(newCode) => {
                      if (showFullCode) {
                        setCode(extractTikzCodeFromFull(newCode));
                      } else {
                        setCode(newCode);
                      }
                    }}
                    isReadOnly={isReadOnly}
                    searchQuery={searchQuery}
                    replaceQuery={replaceQuery}
                    onReplaceAll={handleReplaceAll}
                    setMatchCount={setMatchCount}
                  />
                  </div>
                )
              )}
          </div>
    </main>
  );
};

export default Editor;
