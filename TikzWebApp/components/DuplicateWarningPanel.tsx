import React, { useState } from 'react';

interface DuplicateWarningPanelProps {
  duplicateInfo?: { duplicateNames: string[][], duplicateCodes: string[][] };
  userTemplates: any[];
  selectedCategory: string;
}

const DuplicateWarningPanel: React.FC<DuplicateWarningPanelProps> = ({ duplicateInfo, userTemplates, selectedCategory }) => {
  const [isMinimized, setIsMinimized] = useState(false);

  if (!duplicateInfo) return null;

  // Filter duplicates for the current category
  const currentCategoryTemplates = userTemplates.filter(t => (t.categoryId || 'my-library') === selectedCategory);
  const currentCategoryTemplateIds = new Set(currentCategoryTemplates.map(t => t.id));

  const currentCategoryDuplicateNames = duplicateInfo.duplicateNames.filter(group => group.some(id => currentCategoryTemplateIds.has(id)));
  const currentCategoryDuplicateCodes = duplicateInfo.duplicateCodes.filter(group => group.some(id => currentCategoryTemplateIds.has(id)));

  if (currentCategoryDuplicateNames.length === 0 && currentCategoryDuplicateCodes.length === 0) {
    return null;
  }

  const renderDuplicateGroup = (group: string[], type: 'name' | 'code') => {
    const templates = group.map(id => userTemplates.find(t => t.id === id)).filter(Boolean);
    if (templates.length === 0) return null;

    const mainTitle = templates[0].title;
    
    return (
      <div key={group.join('-')} className="mb-3 last:mb-0 border-b border-orange-200 dark:border-orange-800/50 pb-2 last:border-0">
        <div className="font-semibold text-orange-800 dark:text-orange-300 text-xs mb-1">
          {type === 'name' ? `Trùng tên: "${mainTitle}"` : `Trùng mã TikZ (ví dụ: "${mainTitle}")`}
        </div>
        <ul className="space-y-1">
          {templates.map(t => (
            <li key={t.id} className="text-[11px] text-orange-700 dark:text-orange-400 flex items-start gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-orange-400 dark:bg-orange-500 mt-1 shrink-0"></span>
              <span>
                <span className="font-medium">{t.title}</span>
                <span className="opacity-75"> (Nhóm: {t.subCategoryName || 'Chung'})</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="fixed top-20 right-6 z-40 w-80 shadow-xl rounded-lg border border-orange-300 dark:border-orange-700 bg-orange-50 dark:bg-slate-800 overflow-hidden transition-all duration-300 ease-in-out">
      <div 
        className="bg-orange-100 dark:bg-orange-900/40 px-3 py-2 flex items-center justify-between cursor-pointer"
        onClick={() => setIsMinimized(!isMinimized)}
      >
        <div className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 text-orange-600 dark:text-orange-400">
            <path fillRule="evenodd" d="M9.401 3.003c1.155-2 4.043-2 5.197 0l7.355 12.748c1.154 2-.29 4.5-2.599 4.5H4.645c-2.309 0-3.752-2.5-2.598-4.5L9.4 3.003zM12 8.25a.75.75 0 01.75.75v3.75a.75.75 0 01-1.5 0V9a.75.75 0 01.75-.75zm0 8.25a.75.75 0 100-1.5.75.75 0 000 1.5z" clipRule="evenodd" />
          </svg>
          <h3 className="text-sm font-bold text-orange-800 dark:text-orange-300">Cảnh báo trùng lặp</h3>
        </div>
        <button className="text-orange-600 dark:text-orange-400 hover:text-orange-800 dark:hover:text-orange-200">
          {isMinimized ? (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 15.75l7.5-7.5 7.5 7.5" />
            </svg>
          )}
        </button>
      </div>
      
      {!isMinimized && (
        <div className="p-3 max-h-[60vh] overflow-y-auto">
          {currentCategoryDuplicateNames.length > 0 && (
            <div className="mb-4">
              {currentCategoryDuplicateNames.map(group => renderDuplicateGroup(group, 'name'))}
            </div>
          )}
          
          {currentCategoryDuplicateCodes.length > 0 && (
            <div>
              {currentCategoryDuplicateCodes.map(group => renderDuplicateGroup(group, 'code'))}
            </div>
          )}
          
          <p className="text-[10px] text-orange-600 dark:text-orange-500 mt-3 pt-2 border-t border-orange-200 dark:border-orange-800/50 italic text-center">
            Hãy kiểm tra và xóa bớt các mẫu không cần thiết.
          </p>
        </div>
      )}
    </div>
  );
};

export default DuplicateWarningPanel;
