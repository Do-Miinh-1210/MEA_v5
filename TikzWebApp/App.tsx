import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import AIAssistant from './components/AIAssistant';
import Editor from './components/Editor';
import ShareModal from './components/ShareModal';
import SaveModal from './components/SaveModal';
import ImportModal from './components/ImportModal';
import RenameGroupModal from './components/RenameGroupModal';
import HelpModal from './components/HelpModal';
import UserGuideModal from './components/UserGuideModal';
import EmailManagerDropdown from './components/EmailManagerDropdown';
import SmartSearchBox from './components/SmartSearchBox';
import DuplicateWarningPanel from './components/DuplicateWarningPanel';
import { CATEGORIES } from './constants';
import type { Category } from './types';
import { BookIcon, PencilIcon, EyeIcon, ShareIcon } from './constants';
import { useLibrary } from './hooks/useLibrary';
import { ALLOWED_EMAILS, CREATOR_LIBRARY_DATA } from './config';
import { playStartSound, playTaskCompleteSound, playErrorSound } from './utils/audio';
import { categorizeCode } from './services/geminiService';
import LZString from 'lz-string';
import { compressCode, decompressCode } from './utils/compression';

const App: React.FC = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [hasApiKey, setHasApiKey] = useState<boolean>(false);

  // Changed default to '' to show "Chọn chủ đề" initially
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [currentCode, setCurrentCode] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [apiKeyError, setApiKeyError] = useState<string | null>(null);
  
  const [isReadOnly, setIsReadOnly] = useState<boolean>(false);
  const [showShareModal, setShowShareModal] = useState<boolean>(false);
  const [showSaveModal, setShowSaveModal] = useState<boolean>(false);
  const [showImportModal, setShowImportModal] = useState<boolean>(false);
  const [showRenameModal, setShowRenameModal] = useState<boolean>(false);
  const [showHelpModal, setShowHelpModal] = useState<boolean>(false);
  const [showUserGuideModal, setShowUserGuideModal] = useState<boolean>(false);
  const [showEmailManager, setShowEmailManager] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [shareUrl, setShareUrl] = useState<string>('');
  const [editingTemplate, setEditingTemplate] = useState<any>(null);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [replaceQuery, setReplaceQuery] = useState('');
  const [matchCount, setMatchCount] = useState(0);
  const [isNoteEnabled, setIsNoteEnabled] = useState<boolean>(false);
  const [isBbtNoFrame, setIsBbtNoFrame] = useState<boolean>(false);
  const [isAsymptoteHidden, setIsAsymptoteHidden] = useState<boolean>(true);
  const [isFunctionHidden, setIsFunctionHidden] = useState<boolean>(true);
  const [isComponentFunctionHidden, setIsComponentFunctionHidden] = useState<boolean>(true);
  
  const [elapsedTime, setElapsedTime] = useState(0);
  const startTimeRef = React.useRef<number | null>(null);

  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (isLoading) {
      if (startTimeRef.current === null) {
        startTimeRef.current = Date.now();
        setElapsedTime(0);
      }
      interval = setInterval(() => {
        if (startTimeRef.current !== null) {
          setElapsedTime(Math.floor((Date.now() - startTimeRef.current) / 1000));
        }
      }, 1000);
    } else {
      startTimeRef.current = null;
    }

    return () => clearInterval(interval);
  }, [isLoading]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const handleCleanUp = () => {
    if (isLoading || !currentCode || !currentCode.trim()) return;
    
    let newCode = currentCode;

    const findCommentsBefore = (text, index) => {
        let beforeStr = text.substring(0, index);
        let lines = beforeStr.split('\n');
        let commentLines = [];
        for (let i = lines.length - 1; i >= 0; i--) {
            let line = lines[i].trim();
            if (line === '' || line.startsWith('%')) {
                commentLines.unshift(lines[i]);
                if (line !== '' && !line.startsWith('%')) {
                    break;
                }
            } else {
                break;
            }
        }
        // Remove empty lines at the very beginning of the extracted comments
        while (commentLines.length > 0 && commentLines[0].trim() === '') {
            commentLines.shift();
        }
        return commentLines.join('\n') + (commentLines.length > 0 ? '\n' : '');
    };
    
    const docBegin = newCode.indexOf('\\begin{document}');
    const docClass = newCode.indexOf('\\documentclass');
    const docEnd = newCode.lastIndexOf('\\end{document}');
    
    if (docEnd !== -1) {
       let start = docClass !== -1 ? docClass : (docBegin !== -1 ? docBegin : 0);
       let comments = findCommentsBefore(newCode, start);
       const end = docEnd + '\\end{document}'.length;
       newCode = (comments + newCode.substring(start, end)).trim();
       setCurrentCode(newCode);
       return;
    }
    
    const tikzBeginMatch = newCode.match(/\\begin\{(tikzpicture|circuitikz)\}/);
    const tikzEndMatch = newCode.match(/\\end\{(tikzpicture|circuitikz)\}/g);
    
    if (tikzBeginMatch && tikzEndMatch) {
       let start = tikzBeginMatch.index;
       let comments = findCommentsBefore(newCode, start);
       const endMatchStr = tikzEndMatch[tikzEndMatch.length - 1];
       const end = newCode.lastIndexOf(endMatchStr) + endMatchStr.length;
       newCode = (comments + newCode.substring(start, end)).trim();
       setCurrentCode(newCode);
       return;
    }
  };

  useEffect(() => {
    setCurrentCode(prev => {
      let next = prev;
      
      // Toggle BBT Frame
      if (isBbtNoFrame && next.includes('nocadre=false')) {
        next = next.replace(/nocadre=false/g, 'nocadre=true');
      } else if (!isBbtNoFrame && next.includes('nocadre=true')) {
        next = next.replace(/nocadre=true/g, 'nocadre=false');
      }
      
      // Toggle Asymptote Labels
      if (isAsymptoteHidden) {
        next = next.replace(/(% --- TIỆM CẬN ---\s*\n)([\s\S]*?(?=\n\s*\n|\n\s*\\end\{tikzpicture\}|\n\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\n\s*)(%?\s*)(postaction=\{[^}]*\}\}, decorate\})/g, "$1% $3");
        });
      } else {
        next = next.replace(/(% --- TIỆM CẬN ---\s*\n)([\s\S]*?(?=\n\s*\n|\n\s*\\end\{tikzpicture\}|\n\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\n\s*)(%?\s*)(postaction=\{[^}]*\}\}, decorate\})/g, "$1$3");
        });
      }
      
      // Toggle Function Graph Labels
      if (isFunctionHidden) {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\s*\n)([\s\S]*?(?=\n\s*\n|\n\s*\\end\{tikzpicture\}|\n\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\n\s*)(%?\s*)(postaction=\{[^}]*\}\}, decorate\})/g, "$1% $3");
        });
      } else {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ ---\s*\n)([\s\S]*?(?=\n\s*\n|\n\s*\\end\{tikzpicture\}|\n\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\n\s*)(%?\s*)(postaction=\{[^}]*\}\}, decorate\})/g, "$1$3");
        });
      }

      // Toggle Component Function Labels
      if (isComponentFunctionHidden) {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ THÀNH PHẦN ---\s*\n)([\s\S]*?(?=\n\s*\n|\n\s*\\end\{tikzpicture\}|\n\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\n\s*)(%?\s*)(postaction=\{[^}]*\}\}, decorate\})/g, "$1% $3");
        });
      } else {
        next = next.replace(/(% --- ĐỒ THỊ HÀM SỐ THÀNH PHẦN ---\s*\n)([\s\S]*?(?=\n\s*\n|\n\s*\\end\{tikzpicture\}|\n\s*(?:% ---)|$))/g, (match, p1, p2) => {
          return p1 + p2.replace(/(\n\s*)(%?\s*)(postaction=\{[^}]*\}\}, decorate\})/g, "$1$3");
        });
      }

      return next;
    });
  }, [isBbtNoFrame, isAsymptoteHidden, isFunctionHidden, isComponentFunctionHidden]);

  const [userEmail, setUserEmail] = useState<string>(() => localStorage.getItem('TIKZ_USER_EMAIL') || '');
  const [apiKeyInput, setApiKeyInput] = useState<string>(() => localStorage.getItem('GEMINI_USER_KEY') || '');
  const [managedEmailsUpdateTrigger, setManagedEmailsUpdateTrigger] = useState(0);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const toastTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  const [isSidebarVisible, setIsSidebarVisible] = useState<boolean>(true);
  const [sidebarWidth, setSidebarWidth] = useState<number>(257); // ~6.8cm
  const [aiAssistantWidth, setAiAssistantWidth] = useState<number>(302); // ~8cm

  const handleSidebarResize = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = sidebarWidth;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newWidth = Math.max(150, Math.min(600, startWidth + (moveEvent.clientX - startX)));
      setSidebarWidth(newWidth);
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = 'default';
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
    document.body.style.cursor = 'col-resize';
  };

  const handleAIAssistantResize = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = aiAssistantWidth;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newWidth = Math.max(200, Math.min(800, startWidth + (moveEvent.clientX - startX)));
      setAiAssistantWidth(newWidth);
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = 'default';
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
    document.body.style.cursor = 'col-resize';
  };

  const showToast = (message: string, duration: number = 6000) => {
    setToastMessage(message);
    if (toastTimeoutRef.current) {
      clearTimeout(toastTimeoutRef.current);
    }
    toastTimeoutRef.current = setTimeout(() => {
      setToastMessage(null);
    }, duration);
  };

  const { userTemplates, saveTemplate, deleteTemplate, updateTemplate, renameGroup } = useLibrary();

  const duplicateInfo = React.useMemo(() => {
    const duplicateNames: string[][] = [];
    const duplicateCodes: string[][] = [];

    // Group templates by categoryId
    const templatesByCategory = new Map<string, typeof userTemplates>();
    userTemplates.forEach(t => {
      const catId = t.categoryId || 'my-library';
      if (!templatesByCategory.has(catId)) templatesByCategory.set(catId, []);
      templatesByCategory.get(catId)!.push(t);
    });

    // Check duplicates within each category
    templatesByCategory.forEach(templates => {
      const nameMap = new Map<string, string[]>();
      const codeMap = new Map<string, string[]>();
      
      templates.forEach(t => {
        const name = t.title.toLowerCase().trim();
        const code = t.code.trim();
        
        if (!nameMap.has(name)) nameMap.set(name, []);
        nameMap.get(name)!.push(t.id);
        
        if (!codeMap.has(code)) codeMap.set(code, []);
        codeMap.get(code)!.push(t.id);
      });
      
      duplicateNames.push(...Array.from(nameMap.values()).filter(ids => ids.length > 1));
      duplicateCodes.push(...Array.from(codeMap.values()).filter(ids => ids.length > 1));
    });
    
    return { duplicateNames, duplicateCodes };
  }, [userTemplates]);

  const handleToggleOptimal = (id: string) => {
    const template = userTemplates.find(t => t.id === id);
    if (template) {
      updateTemplate(id, { isOptimal: !template.isOptimal });
    }
  };

  const isEmailAllowed = (email: string) => {
    if (!email) return false;
    const normalized = email.trim().toLowerCase();
    if (ALLOWED_EMAILS.includes(normalized)) return true;
    
    try {
      const stored = localStorage.getItem('TIKZ_MANAGED_EMAILS');
      if (stored) {
        const emails: { email: string, allowed: boolean }[] = JSON.parse(stored);
        const found = emails.find(e => e.email === normalized);
        if (found && found.allowed) return true;
      }
    } catch (e) {}
    
    return false;
  };

  // Merge user templates into categories
  const allCategories = React.useMemo(() => {
    // Start with base categories
    const mergedCategories = [...CATEGORIES].map(cat => ({
      ...cat,
      subCategories: cat.subCategories.map(subCat => ({
        ...subCat,
        templates: [...subCat.templates]
      }))
    }));

    // Add shared library
    const sharedLibrary: Category = {
      id: 'shared-library',
      name: 'Thư viện chung',
      subCategories: CREATOR_LIBRARY_DATA.subCategories.map(subCat => ({
        name: subCat.name,
        templates: [...subCat.templates]
      }))
    };
    mergedCategories.push(sharedLibrary);

    // Add my library
    const myLibrary: Category = {
      id: 'my-library',
      name: 'Thư viện của tôi',
      subCategories: []
    };
    mergedCategories.push(myLibrary);

    // Distribute user templates
    userTemplates.forEach(t => {
      const targetCategoryId = t.categoryId || 'my-library';
      let targetCategory = mergedCategories.find(c => c.id === targetCategoryId);
      
      if (!targetCategory) {
        targetCategory = myLibrary;
      }

      let subCategory = targetCategory.subCategories.find(s => s.name === t.subCategoryName);
      if (!subCategory) {
        subCategory = { name: t.subCategoryName, templates: [] };
        targetCategory.subCategories.push(subCategory);
      }
      const existingIndex = subCategory.templates.findIndex(existing => existing.id === t.id);
      if (existingIndex >= 0) {
        subCategory.templates[existingIndex] = {
          ...subCategory.templates[existingIndex],
          id: t.id,
          title: t.title,
          description: t.description,
          code: t.code,
          isOptimal: t.isOptimal !== undefined ? t.isOptimal : subCategory.templates[existingIndex].isOptimal
        };
      } else {
        subCategory.templates.push({
          id: t.id,
          title: t.title,
          description: t.description,
          code: t.code,
          isOptimal: t.isOptimal
        });
      }
    });

    return mergedCategories;
  }, [userTemplates]);

  const sharedLibrary = allCategories.find(c => c.id === 'shared-library') || allCategories[0];
  const myLibrary = allCategories.find(c => c.id === 'my-library') || allCategories[0];
  const existingSubCategories = Array.from(new Set(userTemplates.map(t => t.subCategoryName)));

  useEffect(() => {
    localStorage.setItem('TIKZ_USER_EMAIL', userEmail);
  }, [userEmail]);

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  // Check for API Key on mount
  useEffect(() => {
    const storedKey = localStorage.getItem('GEMINI_USER_KEY');
    if (storedKey) {
      setHasApiKey(true);
      setApiKeyInput(storedKey);
    }
  }, []);

  const handleSaveApiKey = (key: string) => {
    localStorage.setItem('GEMINI_USER_KEY', key);
    setApiKeyInput(key);
    if (key.trim()) {
      setHasApiKey(true);
      setApiKeyError(null);
    } else {
      setHasApiKey(false);
    }
  };

  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((err) => {
        showToast(`Error attempting to enable fullscreen: ${err.message}`);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'dark' ? 'light' : 'dark');
  };

  useEffect(() => {
    const loadInitialCode = () => {
        // Do nothing, leave code empty by default
    };
    
    // Check if it's the first time opening the app
    const hasSeenGuide = localStorage.getItem('TIKZ_HAS_SEEN_GUIDE');
    const storedApiKey = localStorage.getItem('GEMINI_USER_KEY');
    
    if (!storedApiKey) {
      setShowUserGuideModal(true);
      setTimeout(() => {
        showToast('Hãy đọc HDSD để nhập API key và cách dùng App', 8000);
      }, 500);
    } else if (!hasSeenGuide) {
      setShowUserGuideModal(true);
      localStorage.setItem('TIKZ_HAS_SEEN_GUIDE', 'true');
    }
    
    const urlParams = new URLSearchParams(window.location.search);
    const sharedCodeRaw = urlParams.get('share');

    if (sharedCodeRaw) {
      try {
        let decodedCode = null;
        
        if (sharedCodeRaw.startsWith('f_')) {
          // New fflate compression
          decodedCode = decompressCode(sharedCodeRaw.substring(2));
        } else {
          // Legacy LZString compression
          decodedCode = LZString.decompressFromEncodedURIComponent(sharedCodeRaw);
          
          if (!decodedCode) {
            // Fallback to old base64 method
            // Replace spaces with + because URLSearchParams might have converted + to space
            const base64Str = sharedCodeRaw.replace(/ /g, '+');
            decodedCode = decodeURIComponent(atob(base64Str));
          }
        }
        
        if (decodedCode) {
          setCurrentCode(decodedCode);
          setIsReadOnly(true);
          // Clean the URL for aesthetic purposes
          window.history.replaceState(null, '', window.location.pathname);
        } else {
          throw new Error("Decompression returned null");
        }
      } catch (e) {
        console.error("Failed to decode shared code:", e);
        setError("Không thể tải mã được chia sẻ. Liên kết có thể bị hỏng.");
        loadInitialCode();
      }
    } else {
      loadInitialCode();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  
  const handleApiKeyInvalid = (message: string) => {
    // If API key is invalid during usage, force them to re-enter
    localStorage.removeItem('GEMINI_USER_KEY');
    setHasApiKey(false);
    setApiKeyInput('');
    setApiKeyError(message);
    setIsLoading(false);
  };

  const handleShareClick = () => {
    try {
      const compressed = compressCode(currentCode);
      const url = `${window.location.origin}${window.location.pathname}?share=f_${compressed}`;
      setShareUrl(url);
      setShowShareModal(true);
    } catch (e) {
      console.error("Failed to compress code for sharing:", e);
      showToast("Lỗi khi tạo liên kết chia sẻ. Mã có thể quá dài.", 4000);
    }
  };

  const handleSaveToLibrary = (title: string, description: string, categoryId: string, subCategoryName: string, overwriteId?: string) => {
    const codeToSave = editingTemplate ? editingTemplate.code : currentCode;
    if (overwriteId) {
      updateTemplate(overwriteId, { title, description, categoryId, subCategoryName, code: codeToSave });
    } else {
      saveTemplate(title, description, categoryId, subCategoryName, codeToSave);
    }
    setShowSaveModal(false);
    setEditingTemplate(null);
    playTaskCompleteSound();
  };

  const handleFilesDropped = (files: { name: string; content: string }[]) => {
    files.forEach(file => {
      const title = file.name.replace(/\.[^/.]+$/, "");
      saveTemplate(title, 'Imported file', 'my-library', 'Imported', file.content);
    });
    playTaskCompleteSound();
    alert(`Đã lưu ${files.length} tệp vào thư viện (nhóm "Imported").`);
  };

  return (
    <div className={`flex flex-col h-screen font-sans ${theme}`}>
      <header className="bg-slate-100/80 dark:bg-slate-900/80 backdrop-blur-sm shadow-md shadow-black/20 flex items-center justify-between p-2 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-2">
          <button 
            onClick={() => setIsSidebarVisible(!isSidebarVisible)} 
            className="p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors" 
            title="Ẩn/hiện thanh bên"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>
          <h1 className="text-lg font-bold text-slate-800 dark:text-white whitespace-nowrap">Code TikZ AI</h1>
          
          {/* Rename Group Button */}
          <button
            onClick={() => setShowRenameModal(true)}
            className="ml-2 px-2 py-1 bg-white dark:bg-slate-800 border-[1.2pt] border-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 text-slate-700 dark:text-slate-300 rounded text-xs font-medium transition-colors flex items-center gap-1 shadow-sm whitespace-nowrap"
            title="Sửa tên nhóm trong thư viện"
          >
            <PencilIcon className="h-3 w-3" />
            <span>Sửa nhóm</span>
          </button>

          {/* Help Button */}
          <button
            onClick={() => setShowHelpModal(true)}
            className="ml-2 px-3 py-1 bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-600 hover:to-blue-600 text-white border-none rounded text-xs font-bold transition-all flex items-center gap-1.5 shadow-[0_0_8px_rgba(20,184,166,0.6)] hover:shadow-[0_0_12px_rgba(20,184,166,0.8)] whitespace-nowrap relative"
            title="Hướng dẫn sử dụng"
          >
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
            </span>
            <span className="text-sm">💬</span>
            <span className="uppercase tracking-wide">Hỏi đáp</span>
          </button>

          {/* Import to Library Button */}
          <button
            onClick={() => setShowImportModal(true)}
            className="ml-2 px-2 py-1 bg-white dark:bg-slate-800 border-[1.2pt] border-green-500 hover:bg-green-50 dark:hover:bg-green-900/20 text-slate-700 dark:text-slate-300 rounded text-xs font-medium transition-colors flex items-center gap-1 shadow-sm whitespace-nowrap"
            title="Thêm file vào thư viện"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3 h-3">
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
            </svg>
            <span>Thêm file</span>
          </button>

          {/* Export Library Button (Only for Creator) */}
          {userEmail?.trim() === 'totoancvabd@gmail.com' && (
            <button
              onClick={() => {
                const data = localStorage.getItem('TIKZ_USER_LIBRARY');
                if (data) {
                  navigator.clipboard.writeText(data);
                  alert('Đã copy dữ liệu thư viện vào clipboard. Hãy dán vào mảng templates trong file src/config.ts để cập nhật CREATOR_LIBRARY_DATA.');
                } else {
                  alert('Thư viện của bạn đang trống.');
                }
              }}
              className="ml-1 px-2 py-1 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 hover:border-cyan-500 dark:hover:border-cyan-500 text-slate-700 dark:text-slate-300 rounded text-xs font-medium transition-colors flex items-center gap-1 shadow-sm whitespace-nowrap"
              title="Copy dữ liệu thư viện để cập nhật vào source code"
            >
              <ShareIcon className="h-3 w-3" />
              <span>Xuất TV</span>
            </button>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {/* Email Manager Button (Only for Creator) */}
          {userEmail?.trim() === 'totoancvabd@gmail.com' && (
            <div className="relative flex items-center">
              <button
                onClick={() => setShowEmailManager(!showEmailManager)}
                className={`px-2 py-1 bg-white dark:bg-slate-800 border ${showEmailManager ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400' : 'border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300'} hover:border-cyan-500 dark:hover:border-cyan-500 rounded text-xs font-medium transition-colors flex items-center gap-1 shadow-sm whitespace-nowrap`}
                title="Quản lý danh sách email được phép truy cập"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3 h-3">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
                </svg>
                <span>QL Email</span>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={`w-3 h-3 transition-transform ${showEmailManager ? 'rotate-180' : ''}`}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
              </button>

              {showEmailManager && (
                <EmailManagerDropdown onClose={() => {
                  setShowEmailManager(false);
                  setManagedEmailsUpdateTrigger(prev => prev + 1);
                }} />
              )}
            </div>
          )}

          {/* Full Màn hình button */}
          <button
            onClick={toggleFullScreen}
            className="flex items-center gap-1 text-black dark:text-white font-normal text-sm p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors mr-2 bg-transparent border-none"
            title={isFullscreen ? "Thu nhỏ màn hình" : "Toàn màn hình"}
          >
            {isFullscreen ? (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
              </svg>
            )}
          </button>

          {/* HDSD button */}
          <button
            onClick={() => setShowUserGuideModal(true)}
            className="flex items-center gap-1 text-blue-600 dark:text-blue-500 font-bold text-sm px-2 py-1 rounded-md hover:bg-blue-50 dark:hover:bg-blue-950/30 transition-colors whitespace-nowrap mr-2 bg-transparent border-none"
            title="Hướng dẫn sử dụng"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
            </svg>
            HDSD
          </button>

          {/* Clean up button */}
          <button
            onClick={handleCleanUp}
            disabled={isLoading || !currentCode || !currentCode.trim()}
            className="flex items-center gap-1 text-red-600 dark:text-red-500 font-bold text-sm px-2 py-1 rounded-md hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors whitespace-nowrap mr-3 disabled:opacity-50 disabled:cursor-not-allowed bg-transparent border-none"
            title="Xóa rác văn bản ngoài khối mã"
          >
             Dọn rác
          </button>

          {/* Stopwatch */}
          <div className="flex items-center text-teal-600 dark:text-teal-400 font-mono text-lg leading-none tracking-tight mr-2" title="Thời gian tạo">
            {formatTime(elapsedTime)}
          </div>

          {/* API Key Input */}
          <div className={`flex items-center gap-1 bg-white dark:bg-slate-800 rounded border-[1.2pt] p-1 shadow-sm transition-all relative group ${!hasApiKey ? 'border-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]' : 'border-teal-500'}`}>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={!hasApiKey ? 2.5 : 1.5} stroke="currentColor" className={`w-4 h-4 ml-1 ${!hasApiKey ? 'text-red-500 animate-pulse' : 'text-teal-500'}`}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
            </svg>
            <input
              type="password"
              placeholder="Dán API vào đây"
              value={apiKeyInput}
              onChange={(e) => handleSaveApiKey(e.target.value)}
              className={`bg-transparent border-none focus:outline-none text-xs w-32 text-slate-800 dark:text-slate-200 px-1 ${!hasApiKey ? 'placeholder-red-500 placeholder:font-bold' : ''}`}
              title="Nhập API Key cá nhân của bạn"
            />
            <a 
              href="https://aistudio.google.com/app/apikey" 
              target="_blank" 
              rel="noopener noreferrer"
              className={`px-1 ${!hasApiKey ? 'text-red-500 hover:text-red-600 animate-pulse' : 'text-teal-500 hover:text-teal-600'}`}
              title="Nhấn vào đây để lấy API Key"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={!hasApiKey ? 2.5 : 1.5} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
              </svg>
            </a>
            {/* Hướng dẫn API Key Hover */}
            <div className="absolute top-full right-0 mt-2 w-72 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 p-4 pointer-events-none">
              <h3 className="font-bold text-sm text-slate-800 dark:text-white mb-2">Cách lấy API Key:</h3>
              <ol className="text-xs text-slate-600 dark:text-slate-300 space-y-2 list-decimal list-inside">
                <li>Bấm vào biểu tượng liên kết (bên phải ô nhập) để tới <span className="font-semibold text-teal-600 dark:text-teal-400">Google AI Studio</span>.</li>
                <li>Đăng nhập bằng tài khoản Google của bạn.</li>
                <li>Nhấn nút <span className="font-semibold text-slate-800 dark:text-white bg-slate-100 dark:bg-slate-700 px-1 rounded">Create API key</span>.</li>
                <li>Copy dãy ký tự đó và dán vào ô này.</li>
              </ol>
            </div>

          </div>

          {/* Search and Replace */}
          <SmartSearchBox
            code={currentCode}
            setCode={setCurrentCode}
            isReadOnly={isReadOnly}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            replaceQuery={replaceQuery}
            setReplaceQuery={setReplaceQuery}
            matchCount={matchCount}
          />

          <div className="h-5 w-px bg-slate-300 dark:bg-slate-700 mx-1"></div>

          <a 
            href="https://texample.net/category/science-technology/mathematics/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="bg-teal-100 hover:bg-teal-200 dark:bg-teal-900/40 dark:hover:bg-teal-800/60 text-teal-700 dark:text-teal-300 font-semibold py-1 px-2 rounded text-[11pt] transition-colors flex items-center gap-1 whitespace-nowrap"
            title="Xem kho code mẫu trên texample.net"
          >
            <span>code mẫu</span>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3 h-3">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
            </svg>
          </a>

           {!isReadOnly && (
            <button 
              onClick={handleShareClick}
              className="p-1.5 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300"
              title="Chia sẻ"
            >
              <ShareIcon className="h-5 w-5" />
            </button>
           )}
           {isReadOnly && (
              <div className="flex items-center gap-1 bg-yellow-500/10 text-yellow-500 dark:text-yellow-400 px-2 py-1 rounded-full font-semibold whitespace-nowrap">
                  <EyeIcon className="h-4 w-4"/>
                  <span className="text-[10px]">Chỉ đọc</span>
              </div>
          )}
          <button 
            onClick={toggleTheme} 
            className="p-1.5 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300"
            title="Toggle theme"
          >
            {theme === 'dark' ? 
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg> 
              : 
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            }
          </button>
        </div>
      </header>
      
      <div className={`flex-1 flex min-h-0 bg-slate-100 dark:bg-slate-800 p-[0.3cm] ${!hasApiKey ? 'opacity-20 pointer-events-none filter blur-sm' : ''}`}>
        <DuplicateWarningPanel 
          duplicateInfo={duplicateInfo} 
          userTemplates={userTemplates} 
          selectedCategory={selectedCategory} 
        />
        {isSidebarVisible && (
          <>
            <Sidebar
              width={sidebarWidth}
              categories={allCategories}
              selectedCategory={selectedCategory}
              onSelectCategory={(id) => {
                setSelectedCategory(id);
              }}
              onSelectTemplate={(code) => {
                setCurrentCode(code);
                setIsReadOnly(false);
              }}
              onDeleteTemplate={deleteTemplate}
              onToggleOptimal={handleToggleOptimal}
              onEditTemplate={(template) => {
                setEditingTemplate(template);
                setShowSaveModal(true);
              }}
              duplicateInfo={duplicateInfo}
            />
            <div 
              className="w-[0.2cm] shrink-0 cursor-col-resize transition-all flex items-center justify-center group"
              onMouseDown={handleSidebarResize}
              title="Kéo để thay đổi kích thước"
            >
              <div className="h-[1cm] w-[1.2pt] bg-gradient-to-b from-yellow-300 to-amber-500 group-hover:from-yellow-200 group-hover:to-amber-400 rounded-full shadow-[0_0_4px_rgba(251,191,36,0.8)]"></div>
            </div>
          </>
        )}
        <AIAssistant
          width={aiAssistantWidth}
          setCode={setCurrentCode}
          onApiKeyInvalid={handleApiKeyInvalid}
          isReadOnly={isReadOnly}
          onFilesDropped={handleFilesDropped}
          userLibrary={sharedLibrary}
          isNoteEnabled={isNoteEnabled}
          isBbtNoFrame={isBbtNoFrame}
          onBoilerplateRemoved={() => {
            showToast('Đã tự động xóa mẫu code TikZ trùng lặp.', 6000);
          }}
          currentCode={currentCode}
          onLoadingChange={setIsLoading}
        />
        <div 
          className="w-[0.2cm] shrink-0 cursor-col-resize transition-all flex items-center justify-center group"
          onMouseDown={handleAIAssistantResize}
          title="Kéo để thay đổi kích thước"
        >
          <div className="h-[1cm] w-[1.2pt] bg-gradient-to-b from-yellow-300 to-amber-500 group-hover:from-yellow-200 group-hover:to-amber-400 rounded-full shadow-[0_0_4px_rgba(251,191,36,0.8)]"></div>
        </div>
        <Editor
          code={currentCode}
          setCode={setCurrentCode}
          onSaveClick={() => setShowSaveModal(true)}
          isLoading={isLoading}
          onApiKeyInvalid={handleApiKeyInvalid}
          isReadOnly={isReadOnly}
          searchQuery={searchQuery}
          replaceQuery={replaceQuery}
          setMatchCount={setMatchCount}
          isNoteEnabled={isNoteEnabled}
          setIsNoteEnabled={setIsNoteEnabled}
          
          isBbtNoFrame={isBbtNoFrame}
          setIsBbtNoFrame={setIsBbtNoFrame}
          isAsymptoteHidden={isAsymptoteHidden}
          setIsAsymptoteHidden={setIsAsymptoteHidden}
          isFunctionHidden={isFunctionHidden}
          setIsFunctionHidden={setIsFunctionHidden}
          isComponentFunctionHidden={isComponentFunctionHidden}
          setIsComponentFunctionHidden={setIsComponentFunctionHidden}
        />
      </div>
      
      {error && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-md shadow-lg z-50" role="alert">
          <strong className="font-bold">Lỗi!</strong>
          <span className="block sm:inline ml-2">{error}</span>
        </div>
      )}
      {showShareModal && (
        <ShareModal shareUrl={shareUrl} onClose={() => setShowShareModal(false)} />
      )}
      {showSaveModal && (
        <SaveModal
          code={editingTemplate ? editingTemplate.code : currentCode}
          onSave={handleSaveToLibrary}
          onClose={() => {
            setShowSaveModal(false);
            setEditingTemplate(null);
          }}
          categories={allCategories}
          existingTemplates={userTemplates.map(t => ({ id: t.id, title: t.title, categoryId: t.categoryId }))}
          initialTemplate={editingTemplate}
          
        />
      )}
      {showImportModal && (
          <ImportModal
          onImport={async (files, categoryId, subCategoryName) => {
            setShowImportModal(false);
            const categoryName = allCategories.find(c => c.id === categoryId)?.name || 'Thư viện của tôi';
            
            if (subCategoryName === '') {
              // Auto-categorize
              showToast('Đang tự động phân loại và lưu tệp...', 15000);
              for (const file of files) {
                const title = file.name.replace(/\.[^/.]+$/, "");
                const autoCategory = await categorizeCode(file.content);
                saveTemplate(title, 'Imported file', categoryId, autoCategory, file.content);
              }
            } else {
              files.forEach(file => {
                const title = file.name.replace(/\.[^/.]+$/, "");
                saveTemplate(title, 'Imported file', categoryId, subCategoryName, file.content);
              });
            }
            
            playTaskCompleteSound();
            let fileNames = files.map(f => f.name).join(', ');
            if (fileNames.length > 50) {
              fileNames = fileNames.substring(0, 47) + '...';
            }
            showToast(`Tôi đã lưu "${fileNames}" vào "${categoryName}" thành công. Bạn có thể kiểm tra lại trong thư viện nhé.`, 15000);
          }}
          onClose={() => setShowImportModal(false)}
          categories={allCategories}
          
        />
      )}
      {showRenameModal && (
        <RenameGroupModal
          existingGroups={existingSubCategories}
          onRename={renameGroup}
          onClose={() => setShowRenameModal(false)}
        />
      )}
      {showHelpModal && (
        <HelpModal 
          onClose={() => setShowHelpModal(false)} 
        />
      )}
      {showUserGuideModal && (
        <UserGuideModal  
          onClose={() => setShowUserGuideModal(false)}
          hasApiKey={hasApiKey}
          onSaveApiKey={(key) => {
            handleSaveApiKey(key);
            if (key && key.trim().length > 10) {
               setShowUserGuideModal(false);
            }
          }}
        />
      )}
      
      {toastMessage && (
        <div className="fixed bottom-4 right-4 bg-emerald-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 flex items-center gap-3 max-w-md animate-fade-in-up">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6 shrink-0">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm font-medium">{toastMessage}</p>
          <button onClick={() => {
            setToastMessage(null);
            if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
          }} className="shrink-0 hover:text-emerald-200 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};

export default App;