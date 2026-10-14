
import React from 'react';
import type { Template } from '../types';

import { TrashIcon } from '../constants';

interface TemplateCardProps {
  template: Template;
  onSelect: (code: string) => void;
  onDelete?: (id: string) => void;
  onToggleOptimal?: (id: string) => void;
  onEdit?: (template: Template) => void;
  isDuplicateName?: boolean;
  isDuplicateCode?: boolean;
}

const TemplateCard: React.FC<TemplateCardProps> = ({ template, onSelect, onDelete, onToggleOptimal, onEdit, isDuplicateName, isDuplicateCode }) => {
  return (
    <div className={`bg-slate-50 dark:bg-slate-800 rounded-lg p-4 border ${template.isOptimal ? 'border-yellow-400 dark:border-yellow-500 shadow-sm shadow-yellow-400/20' : (isDuplicateName || isDuplicateCode) ? 'border-orange-400 dark:border-orange-500 shadow-sm shadow-orange-400/20' : 'border-slate-200 dark:border-slate-700'} relative group`}>
      {(isDuplicateName || isDuplicateCode) && !template.isOptimal && (
        <div className="absolute -top-2 -left-2 bg-orange-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm z-10">
          Trùng lặp
        </div>
      )}
      <div className="absolute top-2 right-2 flex items-center gap-1 transition-all">
        {onToggleOptimal && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleOptimal(template.id);
            }}
            className={`p-1.5 rounded-md transition-colors ${template.isOptimal ? 'text-yellow-500 hover:bg-yellow-50 dark:hover:bg-yellow-500/10 opacity-100' : 'text-slate-400 hover:text-yellow-500 hover:bg-yellow-50 dark:hover:bg-yellow-500/10 opacity-0 group-hover:opacity-100'}`}
            title={template.isOptimal ? "Bỏ đánh dấu code tối ưu" : "Đánh dấu là code tối ưu (lưu trữ lâu dài)"}
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill={template.isOptimal ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
            </svg>
          </button>
        )}
        {onEdit && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onEdit(template);
            }}
            className="p-1.5 text-slate-400 hover:text-cyan-500 hover:bg-cyan-50 dark:hover:bg-cyan-500/10 rounded-md transition-colors opacity-0 group-hover:opacity-100"
            title="Chỉnh sửa mẫu này"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125" />
            </svg>
          </button>
        )}
        {onDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(template.id);
            }}
            className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-md transition-colors opacity-0 group-hover:opacity-100"
            title="Xóa mẫu này"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        )}
      </div>
      <h4 className="font-semibold text-cyan-500 dark:text-cyan-400 mb-2 pr-16">{template.title}</h4>
      <p className="text-slate-600 dark:text-slate-400 text-[11pt] mb-4 leading-relaxed">{template.description}</p>
      <button
        onClick={() => onSelect(template.code)}
        className="w-full bg-cyan-500 hover:bg-cyan-600 dark:bg-cyan-600 dark:hover:bg-cyan-700 text-white font-bold py-2 px-4 rounded-md transition-colors duration-200"
      >
        Sử dụng mẫu
      </button>
    </div>
  );
};

export default TemplateCard;