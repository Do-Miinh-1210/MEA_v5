import React, { useState, useEffect } from 'react';
import { SearchIcon } from '../constants';
import { smartSearch, smartReplace } from '../utils/tikzOptimizer';

interface SmartSearchBoxProps {
  code: string;
  setCode: (code: string) => void;
  isReadOnly: boolean;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  replaceQuery: string;
  setReplaceQuery: (query: string) => void;
  matchCount: number;
}

const SmartSearchBox: React.FC<SmartSearchBoxProps> = ({
  code,
  setCode,
  isReadOnly,
  searchQuery,
  setSearchQuery,
  replaceQuery,
  setReplaceQuery,
  matchCount
}) => {
  const [showMenu, setShowMenu] = useState(false);
  const [showSizeMenu, setShowSizeMenu] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (searchQuery && !isExpanded) {
      setIsExpanded(true);
    }
  }, [searchQuery]);

  const fontSizes = [
    '\\scriptsize',
    '\\Huge',
    '\\huge',
    '\\Large',
    '\\large',
    '\\normalsize',
    '\\small',
    '\\tiny'
  ];

  const handleReplace = () => {
    if (!searchQuery || isReadOnly) return;
    
    const { regex } = smartSearch(code, searchQuery);
    if (regex) {
      const newCode = code.replace(regex, replaceQuery);
      setCode(newCode);
    } else {
      // Fallback
      const newCode = code.split(searchQuery).join(replaceQuery);
      setCode(newCode);
    }
  };

  const applySmartReplace = (type: string) => {
    if (isReadOnly) return;
    const newCode = smartReplace(code, type);
    setCode(newCode);
    setShowMenu(false);
  };

  if (!isExpanded) {
    return (
      <div 
        className="flex items-center justify-center p-1.5 bg-white dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors shadow-sm text-slate-500 hover:text-teal-500"
        onClick={() => setIsExpanded(true)}
        title="Tìm kiếm và thay thế"
      >
        <SearchIcon className="h-4 w-4" />
      </div>
    );
  }

  return (
    <div className="relative flex items-center gap-1 bg-white dark:bg-slate-800 rounded border-[1.2pt] border-red-500 p-1 shadow-sm transition-colors">
      <div className="flex items-center px-1 text-teal-600 dark:text-teal-400 cursor-pointer" onClick={() => setShowMenu(!showMenu)} title="Tính năng thông minh">
        <SearchIcon className="h-4 w-4" />
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3 h-3 ml-0.5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </div>
      
      <div className="relative flex items-center">
        <input
          type="text"
          placeholder="Tìm kiếm..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="bg-transparent border-none focus:outline-none text-sm font-normal w-24 pr-8 text-black dark:text-white placeholder-slate-400 dark:placeholder-slate-500"
          title="Hỗ trợ tìm kiếm thông minh: \draw commands, circle, red, primary colors..."
        />
        {searchQuery && (
          <span className="absolute right-1 text-sm font-bold text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/50 px-1.5 rounded">
            {matchCount}
          </span>
        )}
      </div>
      
      <div className="w-px h-3 bg-slate-300 dark:bg-slate-600 mx-1"></div>
      
      <div className="relative flex items-center">
        <input
          type="text"
          placeholder="Thay thế..."
          value={replaceQuery}
          onChange={(e) => setReplaceQuery(e.target.value)}
          className="bg-transparent border-none focus:outline-none text-sm font-normal w-24 pr-5 text-black dark:text-white placeholder-slate-400 dark:placeholder-slate-500"
        />
        <button
          onClick={() => setShowSizeMenu(!showSizeMenu)}
          className="absolute right-0 text-slate-400 hover:text-teal-500 transition-colors"
          title="Gợi ý cỡ chữ"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3.5 h-3.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
          </svg>
        </button>
        
        {showSizeMenu && (
          <div className="absolute top-full right-0 mt-1 w-32 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded shadow-xl z-50 p-1 text-xs">
            <div className="font-semibold text-slate-700 dark:text-slate-300 mb-1 px-2 pb-1 border-b border-slate-200 dark:border-slate-700">
              Cỡ chữ
            </div>
            <div className="max-h-48 overflow-y-auto">
              {fontSizes.map(size => (
                <button
                  key={size}
                  onClick={() => {
                    setReplaceQuery(size);
                    setShowSizeMenu(false);
                  }}
                  className="block w-full text-left px-2 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-700 dark:text-slate-300 font-mono"
                >
                  {size}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
      
      <button
        onClick={handleReplace}
        disabled={!searchQuery || isReadOnly}
        className="ml-1 px-2 py-0.5 bg-cyan-500 hover:bg-cyan-600 text-white rounded text-[10px] font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors whitespace-nowrap"
        title="Thay thế tất cả (Ctrl+Shift+R)"
      >
        Thay thế
      </button>

      {(searchQuery || replaceQuery) && (
        <button
          onClick={() => {
            setSearchQuery('');
            setReplaceQuery('');
          }}
          className="ml-0.5 p-0.5 text-red-500 dark:text-red-400 hover:text-red-600 dark:hover:text-red-300 transition-colors rounded-full hover:bg-red-50 dark:hover:bg-red-900/30"
          title="Xóa tìm kiếm và thay thế"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-3.5 h-3.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}

      <button
        onClick={() => setIsExpanded(false)}
        className="ml-1 p-0.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors rounded hover:bg-slate-100 dark:hover:bg-slate-700"
        title="Thu gọn"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      {showMenu && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded shadow-xl z-50 p-2 text-xs">
          <div className="font-semibold text-slate-700 dark:text-slate-300 mb-1 border-b border-slate-200 dark:border-slate-700 pb-1">
            Chuẩn hóa & Tối ưu hóa
          </div>
          <button onClick={() => applySmartReplace('normalize-tikzstyle')} className="block w-full text-left px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-300">
            Chuẩn hóa \tikzstyle
          </button>
          <button onClick={() => applySmartReplace('normalize-coordinates')} className="block w-full text-left px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-300">
            Chuẩn hóa tọa độ (thêm cm)
          </button>
          <button onClick={() => applySmartReplace('better-arrows')} className="block w-full text-left px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-300">
            Đổi mũi tên thành -stealth
          </button>
          <button onClick={() => applySmartReplace('node-to-point')} className="block w-full text-left px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-300">
            Đổi node thành điểm đen
          </button>
          <button onClick={() => applySmartReplace('auto-scale')} className="block w-full text-left px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-300">
            Thêm scale=1
          </button>
          
          <div className="font-semibold text-slate-700 dark:text-slate-300 mt-2 mb-1 border-b border-slate-200 dark:border-slate-700 pb-1">
            Template thay thế nhanh
          </div>
          <button onClick={() => applySmartReplace('template-circle')} className="block w-full text-left px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-300">
            Tô màu & viền hình tròn
          </button>
          <button onClick={() => applySmartReplace('template-arrow')} className="block w-full text-left px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-300">
            Làm đậm mũi tên
          </button>
          <button onClick={() => applySmartReplace('template-node-text')} className="block w-full text-left px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded text-slate-600 dark:text-slate-300">
            Định dạng text cho node
          </button>
        </div>
      )}
    </div>
  );
};

export default SmartSearchBox;
