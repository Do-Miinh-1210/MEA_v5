import React, { useState, useRef, useCallback } from 'react';

interface ImportModalProps {
  onImport: (files: { name: string; content: string }[], categoryId: string, subCategoryName: string) => void;
  onClose: () => void;
  categories: { id: string, name: string, subCategories: { name: string }[] }[];
  userEmail?: string;
}

const ImportModal: React.FC<ImportModalProps> = ({ onImport, onClose, categories, userEmail }) => {
  const isCreator = userEmail === 'totoancvabd@gmail.com';
  const [libType, setLibType] = useState<'my-library' | 'shared-library' | 'source'>('my-library');
  const [categoryId, setCategoryId] = useState('my-library');
  
  // Update categoryId when libType changes
  React.useEffect(() => {
    if (libType === 'my-library') setCategoryId('my-library');
    else if (libType === 'shared-library') setCategoryId('shared-library');
    else if (libType === 'source') {
      const firstSource = categories.find(c => c.id !== 'my-library' && c.id !== 'shared-library');
      if (firstSource) setCategoryId(firstSource.id);
    }
  }, [libType, categories]);

  const selectedCategory = categories.find(c => c.id === categoryId);
  const existingSubCategories = selectedCategory ? selectedCategory.subCategories.map(s => s.name) : [];
  
  const [subCategoryName, setSubCategoryName] = useState('auto');
  const [isNewSubCategory, setIsNewSubCategory] = useState(false);
  const [newSubCategoryName, setNewSubCategoryName] = useState('');
  
  const [files, setFiles] = useState<{ name: string; content: string }[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    setSubCategoryName('auto');
    setIsNewSubCategory(false);
  }, [categoryId]);

  const processFiles = async (fileList: FileList | File[]) => {
    const newFiles: { name: string; content: string }[] = [];
    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
      if (file.size > 19 * 1024 * 1024) {
        alert(`Tệp ${file.name} quá lớn (vượt quá 19MB). Vui lòng chọn tệp nhỏ hơn.`);
        continue;
      }
      if (file.name.endsWith('.tex') || file.name.endsWith('.txt') || file.type.startsWith('text/')) {
        const content = await file.text();
        newFiles.push({ name: file.name, content });
      }
    }
    if (newFiles.length > 0) {
      setFiles(prev => [...prev, ...newFiles]);
    } else if (fileList.length > 0) {
      alert('Vui lòng chọn tệp văn bản (.tex, .txt, ...)');
    }
  };

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await processFiles(e.dataTransfer.files);
    }
  }, []);

  const handlePaste = useCallback(async (e: React.ClipboardEvent) => {
    if (e.clipboardData.files && e.clipboardData.files.length > 0) {
      await processFiles(e.clipboardData.files);
    } else {
      const text = e.clipboardData.getData('text');
      if (text) {
        const matches = text.match(/\\begin\{tikzpicture\}[\s\S]*?\\end\{tikzpicture\}/g);
        if (matches && matches.length > 1) {
          const newFiles = matches.map((content, idx) => ({
            name: `Pasted_Code_${Date.now()}_${idx + 1}.tex`,
            content
          }));
          setFiles(prev => [...prev, ...newFiles]);
        } else {
          setFiles(prev => [...prev, { name: `Pasted_Code_${Date.now()}.tex`, content: text }]);
        }
      }
    }
  }, []);

  const handleImport = () => {
    if (files.length === 0) {
      alert('Vui lòng thêm ít nhất một tệp.');
      return;
    }
    let finalSubCategory = '';
    if (isNewSubCategory) {
      finalSubCategory = newSubCategoryName.trim();
      if (!finalSubCategory) {
        alert('Vui lòng nhập tên nhóm.');
        return;
      }
    } else {
      finalSubCategory = subCategoryName === 'auto' ? '' : subCategoryName;
    }
    onImport(files, categoryId, finalSubCategory);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" onPaste={handlePaste}>
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden border border-slate-200 dark:border-slate-700 flex flex-col max-h-[95vh]">
        <div className="flex justify-between items-center p-3 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
          <h2 className="text-base font-bold text-slate-800 dark:text-white">Thêm tệp vào thư viện</h2>
          <button 
            onClick={onClose}
            className="p-1 bg-red-500 text-white hover:bg-red-600 rounded-md transition-colors shadow-sm"
            title="Đóng"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="p-3 flex-1 overflow-y-auto space-y-3">
          <div className="flex items-center gap-3 mb-1">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Loại thư viện:</label>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-1 text-sm cursor-pointer">
                <input type="radio" name="libType" value="my-library" checked={libType === 'my-library'} onChange={() => setLibType('my-library')} className="text-cyan-500 focus:ring-cyan-500" />
                Của tôi
              </label>
              <label className="flex items-center gap-1 text-sm cursor-pointer">
                <input type="radio" name="libType" value="shared-library" checked={libType === 'shared-library'} onChange={() => setLibType('shared-library')} className="text-cyan-500 focus:ring-cyan-500" />
                Dùng chung
              </label>
              {isCreator && (
                <label className="flex items-center gap-1 text-sm cursor-pointer">
                  <input type="radio" name="libType" value="source" checked={libType === 'source'} onChange={() => setLibType('source')} className="text-cyan-500 focus:ring-cyan-500" />
                  Nạp nguồn
                </label>
              )}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {libType === 'source' && (
              <div>
                <label className="block text-[11px] font-medium text-slate-700 dark:text-slate-300 mb-0.5">Thư viện</label>
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className="w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md px-2 py-1 text-xs text-slate-800 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                >
                  {categories.filter(c => c.id !== 'my-library' && c.id !== 'shared-library').map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
            )}

            <div className={libType === 'source' ? '' : 'col-span-2'}>
              <label className="block text-[11px] font-medium text-slate-700 dark:text-slate-300 mb-0.5">Nhóm hình</label>
              <select
                value={isNewSubCategory ? 'new' : subCategoryName}
                onChange={(e) => {
                  if (e.target.value === 'new') {
                    setIsNewSubCategory(true);
                  } else {
                    setIsNewSubCategory(false);
                    setSubCategoryName(e.target.value);
                  }
                }}
                className="w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md px-2 py-1 text-xs text-slate-800 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none"
              >
                <option value="auto">✨ Tự động phân loại (AI)</option>
                {existingSubCategories.map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
                <option value="new" className="font-bold text-cyan-600 dark:text-cyan-400">+ Tạo nhóm mới</option>
              </select>
            </div>

            <div className={libType === 'source' ? '' : 'col-span-1'}>
              <label className="block text-[11px] font-medium text-slate-700 dark:text-slate-300 mb-0.5">Tên nhóm mới</label>
              <input
                type="text"
                value={newSubCategoryName}
                onChange={(e) => {
                  setNewSubCategoryName(e.target.value);
                  if (e.target.value) setIsNewSubCategory(true);
                }}
                disabled={!isNewSubCategory && subCategoryName !== 'new'}
                className="w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md px-2 py-1 text-xs text-slate-800 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none disabled:opacity-50"
                placeholder={isNewSubCategory ? "Nhập tên nhóm..." : "Chọn + Tạo nhóm mới"}
              />
            </div>
          </div>

          <div 
            className={`mt-1 border-2 border-dashed rounded-lg p-3 flex flex-col items-center justify-center transition-colors ${isDragging ? 'border-cyan-500 bg-cyan-50 dark:bg-cyan-900/20' : 'border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-800/50'}`}
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-slate-400 mb-1">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m3.75 9v6m3-3H9m1.5-12H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <p className="text-slate-600 dark:text-slate-400 text-center text-xs mb-2">
              Kéo thả hoặc dán (Ctrl+V) tệp/code vào đây
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-2 py-1 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-md hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors text-xs font-medium"
            >
              Chọn tệp
            </button>
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={(e) => { if(e.target.files) processFiles(e.target.files); }} 
              className="hidden" 
              multiple 
              accept=".tex,.txt,text/plain"
            />
          </div>

          {files.length > 0 && (
            <div className="mt-1">
              <div className="flex justify-between items-center mb-1">
                <h3 className="text-[11px] font-medium text-slate-700 dark:text-slate-300">Tệp đã chọn ({files.length})</h3>
                <button 
                  onClick={() => setFiles([])}
                  className="text-[11px] text-red-500 hover:text-red-600"
                >
                  Xóa tất cả
                </button>
              </div>
              <ul className="max-h-20 overflow-y-auto space-y-1 pr-1">
                {files.map((f, i) => (
                  <li key={i} className="flex items-center justify-between bg-slate-100 dark:bg-slate-900 px-2 py-1 rounded-md border border-slate-200 dark:border-slate-700">
                    <span className="text-[11px] text-slate-700 dark:text-slate-300 truncate pr-2">{f.name}</span>
                    <button 
                      onClick={() => setFiles(prev => prev.filter((_, idx) => idx !== i))}
                      className="text-red-500 hover:text-red-600 p-0.5"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3.5 h-3.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        <div className="bg-slate-50 dark:bg-slate-800/50 px-3 py-2 flex justify-end gap-2 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-sm text-slate-600 dark:text-slate-400 font-medium hover:bg-slate-200 dark:hover:bg-slate-700 rounded-md transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleImport}
            className="px-4 py-1.5 bg-cyan-500 hover:bg-cyan-600 text-white text-sm font-bold rounded-md transition-colors shadow-md shadow-cyan-500/20"
          >
            Thêm vào thư viện
          </button>
        </div>
      </div>
    </div>
  );
};

export default ImportModal;
