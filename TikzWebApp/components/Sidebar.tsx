
import React, { useState, useEffect, useRef, useMemo } from 'react';
import type { Category, Template } from '../types';
import { SearchIcon, ChevronDownIcon, ChevronUpIcon } from '../constants';
import TemplateCard from './TemplateCard';

interface SidebarProps {
  categories: Category[];
  selectedCategory: string;
  onSelectCategory: (id: string) => void;
  onSelectTemplate: (code: string) => void;
  onDeleteTemplate?: (id: string) => void;
  onToggleOptimal?: (id: string) => void;
  onEditTemplate?: (template: Template & { categoryId?: string, subCategoryName?: string }) => void;
  duplicateInfo?: { duplicateNames: any[][], duplicateCodes: any[][] };
  width?: number;
}

const Sidebar: React.FC<SidebarProps> = ({ categories, selectedCategory, onSelectCategory, onSelectTemplate, onDeleteTemplate, onToggleOptimal, onEditTemplate, duplicateInfo, width }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [openSubCategories, setOpenSubCategories] = useState<Set<string>>(new Set());
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const activeCategory = categories.find(c => c.id === selectedCategory);
  const selectedCategoryName = activeCategory?.name || 'Chọn chủ đề';
  
  const isSearching = searchTerm.trim().length > 0;

  const globalSearchResults = useMemo(() => {
    if (!isSearching) return [];
    
    const term = searchTerm.toLowerCase();
    const results: { template: Template, categoryName: string, subCategoryName: string, isMyLibrary: boolean, categoryId: string }[] = [];
    
    categories.forEach(category => {
      const isMyLibrary = category.id === 'my-library' || category.id === 'creator-library';
      category.subCategories.forEach(subCat => {
        subCat.templates.forEach(template => {
          if (template.title.toLowerCase().includes(term) || template.description.toLowerCase().includes(term)) {
            results.push({ template, categoryName: category.name, subCategoryName: subCat.name, isMyLibrary, categoryId: category.id });
          }
        });
      });
    });
    
    // Sort: My Library first
    results.sort((a, b) => {
      if (a.isMyLibrary && !b.isMyLibrary) return -1;
      if (!a.isMyLibrary && b.isMyLibrary) return 1;
      return 0;
    });
    
    return results;
  }, [categories, searchTerm, isSearching]);

  const filteredSubCategories = activeCategory?.subCategories.map(subCat => ({
    ...subCat,
    templates: subCat.templates
  })).filter(subCat => subCat.templates.length > 0) || [];

  // When a new category is selected, open the first sub-category by default for a better UX.
  useEffect(() => {
    const newOpenSubCategories = new Set<string>();
    if (filteredSubCategories.length > 0) {
      newOpenSubCategories.add(filteredSubCategories[0].name);
    }
    setOpenSubCategories(newOpenSubCategories);
    // This effect should only run when the main category changes, not the search term.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategory]);
  
  // Effect to close dropdown on outside click
  useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
          if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
              setIsDropdownOpen(false);
          }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () => {
          document.removeEventListener("mousedown", handleClickOutside);
      };
  }, [dropdownRef]);

  const toggleSubCategory = (name: string) => {
    setOpenSubCategories(prev => {
      const newSet = new Set(prev);
      if (newSet.has(name)) {
        newSet.delete(name);
      } else {
        newSet.add(name);
      }
      return newSet;
    });
  };

  const isDuplicateName = (id: string) => {
      if (!duplicateInfo) return false;
      return duplicateInfo.duplicateNames.some(group => group.includes(id));
  };

  const isDuplicateCode = (id: string) => {
      if (!duplicateInfo) return false;
      return duplicateInfo.duplicateCodes.some(group => group.includes(id));
  };

  return (
    <aside 
      style={{ width: width ? `${width}px` : '6.8cm' }}
      className="shrink-0 bg-white dark:bg-slate-900 h-full flex flex-col p-6 border-[2.5pt] border-red-500 rounded-lg overflow-hidden"
    >
        {!isSearching && (
            <div className="relative mb-6" ref={dropdownRef}>
                <button
                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                    className="w-full flex justify-between items-center text-left px-4 py-3 rounded-md font-semibold transition-colors duration-200 bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-white hover:bg-slate-300 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500"
                >
                    <span>{selectedCategoryName}</span>
                    {isDropdownOpen ? <ChevronUpIcon className="h-5 w-5" /> : <ChevronDownIcon className="h-5 w-5" />}
                </button>
                {isDropdownOpen && (
                    <div className="absolute top-full mt-2 w-full bg-white dark:bg-slate-800 rounded-md shadow-lg z-10 border border-slate-200 dark:border-slate-700">
                        <ul>
                            {categories.map((category) => (
                                <li key={category.id}>
                                    <button
                                        onClick={() => {
                                            onSelectCategory(category.id);
                                            setIsDropdownOpen(false);
                                        }}
                                        className={`w-full text-left px-4 py-2 font-semibold transition-colors duration-150 ${
                                            selectedCategory === category.id
                                                ? 'bg-cyan-500/10 dark:bg-cyan-500/20 text-cyan-600 dark:text-cyan-300'
                                                : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                                        }`}
                                    >
                                        {category.name}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        )}

        <div className="relative mb-6">
            <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 h-6 w-6 text-cyan-500 dark:text-cyan-400" />
            <input
            type="text"
            placeholder="Tìm kiếm mẫu chung..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-200 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-md pl-12 pr-4 py-2 text-slate-800 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none placeholder:text-[11pt]"
            />
        </div>

        <div className="flex-1 overflow-y-auto pr-2 -mr-2">
            <div className="space-y-2">
                {isSearching ? (
                    globalSearchResults.length > 0 ? (
                        <div className="space-y-4">
                            <h3 className="text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Kết quả tìm kiếm</h3>
                            {globalSearchResults.map((result, idx) => (
                                <div key={`${result.template.id}-${idx}`} className="relative">
                                    <div className="text-xs text-cyan-600 dark:text-cyan-400 font-medium mb-1 flex items-center gap-1">
                                        {result.isMyLibrary ? (
                                            <span className="bg-cyan-100 dark:bg-cyan-900/40 px-1.5 py-0.5 rounded text-[10px]">Thư viện của tôi</span>
                                        ) : (
                                            <span className="bg-slate-200 dark:bg-slate-700 px-1.5 py-0.5 rounded text-[10px]">{result.categoryName}</span>
                                        )}
                                        <span className="text-slate-400 dark:text-slate-500">&bull;</span>
                                        <span className="text-slate-500 dark:text-slate-400">{result.subCategoryName}</span>
                                    </div>
                                    <TemplateCard 
                                        template={result.template} 
                                        onSelect={onSelectTemplate} 
                                        onDelete={result.categoryId === 'my-library' ? onDeleteTemplate : undefined}
                                        onToggleOptimal={result.categoryId === 'my-library' ? onToggleOptimal : undefined}
                                        onEdit={onEditTemplate ? () => onEditTemplate({ ...result.template, categoryId: result.categoryId, subCategoryName: result.subCategoryName }) : undefined}
                                        isDuplicateName={result.categoryId === 'my-library' ? isDuplicateName(result.template.id) : false}
                                        isDuplicateCode={result.categoryId === 'my-library' ? isDuplicateCode(result.template.id) : false}
                                    />
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="text-slate-500 dark:text-slate-400 text-center mt-8 text-[11pt]">Không tìm thấy mẫu nào.</p>
                    )
                ) : (
                    filteredSubCategories.map(subCat => {
                        const isOpen = openSubCategories.has(subCat.name);
                        return (
                            <div key={subCat.name}>
                                <button
                                    onClick={() => toggleSubCategory(subCat.name)}
                                    className="w-full flex items-center justify-between text-left p-3 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-cyan-500 transition-colors"
                                >
                                    <h3 className="text-lg font-semibold text-slate-800 dark:text-white">{subCat.name}</h3>
                                    {isOpen ? <ChevronUpIcon className="h-6 w-6 text-slate-500 flex-shrink-0" /> : <ChevronDownIcon className="h-6 w-6 text-slate-500 flex-shrink-0" />}
                                </button>
                                {isOpen && (
                                <div className="pl-4 pt-4 space-y-4 border-l-2 border-slate-200 dark:border-slate-600 ml-3 mt-2">
                                    <div className="space-y-4">
                                        {subCat.templates.map(template => (
                                        <TemplateCard 
                                            key={template.id} 
                                            template={template} 
                                            onSelect={onSelectTemplate} 
                                            onDelete={selectedCategory === 'my-library' ? onDeleteTemplate : undefined}
                                            onToggleOptimal={selectedCategory === 'my-library' ? onToggleOptimal : undefined}
                                            onEdit={onEditTemplate ? () => onEditTemplate({ ...template, categoryId: selectedCategory, subCategoryName: subCat.name }) : undefined}
                                            isDuplicateName={selectedCategory === 'my-library' ? isDuplicateName(template.id) : false}
                                            isDuplicateCode={selectedCategory === 'my-library' ? isDuplicateCode(template.id) : false}
                                        />
                                        ))}
                                    </div>
                                </div>
                                )}
                            </div>
                        );
                    })
                )}
                {!isSearching && filteredSubCategories.length === 0 && (
                    <p className="text-slate-500 dark:text-slate-400 text-center mt-8 text-[11pt]">Chưa có mẫu nào trong chủ đề này.</p>
                )}
            </div>
        </div>
    </aside>
  );
};

export default Sidebar;
