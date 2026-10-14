import React, { useState } from 'react';

interface SaveModalProps {
  code: string;
  onSave: (title: string, description: string, categoryId: string, subCategoryName: string, overwriteId?: string) => void;
  onClose: () => void;
  categories: { id: string, name: string, subCategories: { name: string }[] }[];
  existingTemplates: { id: string, title: string, categoryId?: string }[];
  initialTemplate?: { id: string, title: string, description: string, categoryId?: string, subCategoryName: string };
  userEmail?: string;
}

const SaveModal: React.FC<SaveModalProps> = ({ code, onSave, onClose, categories, existingTemplates, initialTemplate, userEmail }) => {
  const isCreator = userEmail === 'totoancvabd@gmail.com';
  const allowedCategories = isCreator ? categories : categories.filter(c => c.id === 'my-library' || c.id === 'shared-library');

  const [title, setTitle] = useState(initialTemplate?.title || '');
  const [description, setDescription] = useState(initialTemplate?.description || '');
  const [categoryId, setCategoryId] = useState(initialTemplate?.categoryId || (allowedCategories.length > 0 ? allowedCategories[allowedCategories.length - 1].id : 'my-library')); // Default to my-library
  
  const selectedCategory = allowedCategories.find(c => c.id === categoryId) || allowedCategories[0];
  const existingSubCategories = selectedCategory ? selectedCategory.subCategories.map(s => s.name) : [];
  
  const [subCategoryName, setSubCategoryName] = useState(initialTemplate?.subCategoryName || existingSubCategories[0] || 'Chung');
  const [isNewSubCategory, setIsNewSubCategory] = useState(initialTemplate ? !existingSubCategories.includes(initialTemplate.subCategoryName) : existingSubCategories.length === 0);
  const [newSubCategoryName, setNewSubCategoryName] = useState(initialTemplate && !existingSubCategories.includes(initialTemplate.subCategoryName) ? initialTemplate.subCategoryName : '');

  // Update subcategory when category changes
  React.useEffect(() => {
    if (initialTemplate && categoryId === initialTemplate.categoryId) {
      setSubCategoryName(initialTemplate.subCategoryName);
      setIsNewSubCategory(!existingSubCategories.includes(initialTemplate.subCategoryName));
      return;
    }
    if (existingSubCategories.length > 0) {
      setSubCategoryName(existingSubCategories[0]);
      setIsNewSubCategory(false);
    } else {
      setSubCategoryName('');
      setIsNewSubCategory(true);
    }
  }, [categoryId]);

  const handleSave = () => {
    if (!title.trim()) {
      alert('Vui lòng nhập tên mẫu.');
      return;
    }
    const finalSubCategory = isNewSubCategory ? newSubCategoryName.trim() : subCategoryName;
    if (!finalSubCategory) {
      alert('Vui lòng nhập tên nhóm.');
      return;
    }

    const existing = existingTemplates.find(t => t.title.toLowerCase() === title.trim().toLowerCase() && (t.categoryId || 'my-library') === categoryId);
    if (existing && (!initialTemplate || existing.id !== initialTemplate.id)) {
      if (window.confirm(`Mẫu "${title.trim()}" đã tồn tại trong thư viện này. Bạn có muốn ghi đè lên mẫu cũ không?`)) {
        onSave(title.trim(), description.trim(), categoryId, finalSubCategory, existing.id);
        return;
      } else {
        return; // Cancel save
      }
    }

    onSave(title.trim(), description.trim(), categoryId, finalSubCategory, initialTemplate?.id);
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-md overflow-hidden border border-slate-200 dark:border-slate-700">
        <div className="p-6">
          <h2 className="text-2xl font-bold text-slate-800 dark:text-white mb-6">Lưu vào thư viện</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Tên mẫu (ngắn gọn, gợi nhớ)</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md px-4 py-2 text-slate-800 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                placeholder="VD: Tam giác vuông cân"
                autoFocus
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Mô tả (tùy chọn)</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md px-4 py-2 text-slate-800 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none resize-none"
                placeholder="Mô tả chi tiết hơn về hình vẽ..."
                rows={3}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Thư viện</label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
                className="w-full bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md px-4 py-2 text-slate-800 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none mb-4"
              >
                {allowedCategories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>

              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Nhóm hình</label>
              {existingSubCategories.length > 0 && !isNewSubCategory ? (
                <div className="flex gap-2">
                  <select
                    value={subCategoryName}
                    onChange={(e) => setSubCategoryName(e.target.value)}
                    className="flex-1 bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md px-4 py-2 text-slate-800 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                  >
                    {existingSubCategories.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => setIsNewSubCategory(true)}
                    className="px-3 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-md hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors text-sm font-medium"
                  >
                    Tạo mới
                  </button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newSubCategoryName}
                    onChange={(e) => setNewSubCategoryName(e.target.value)}
                    className="flex-1 bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-md px-4 py-2 text-slate-800 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:outline-none"
                    placeholder="Nhập tên nhóm mới..."
                  />
                  {existingSubCategories.length > 0 && (
                    <button
                      onClick={() => setIsNewSubCategory(false)}
                      className="px-3 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-md hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors text-sm font-medium"
                    >
                      Hủy
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="bg-slate-50 dark:bg-slate-800/50 px-6 py-4 flex justify-end gap-3 border-t border-slate-200 dark:border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-slate-600 dark:text-slate-400 font-medium hover:bg-slate-200 dark:hover:bg-slate-700 rounded-md transition-colors"
          >
            Hủy
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-cyan-500 hover:bg-cyan-600 text-white font-bold rounded-md transition-colors shadow-md shadow-cyan-500/20"
          >
            Lưu
          </button>
        </div>
      </div>
    </div>
  );
};

export default SaveModal;
