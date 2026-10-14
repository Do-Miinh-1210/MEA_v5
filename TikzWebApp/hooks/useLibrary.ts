import { useState, useEffect } from 'react';
import type { Category, Template } from '../types';

export interface UserTemplate extends Template {
  categoryId?: string;
  subCategoryName: string;
}

export const useLibrary = () => {
  const [userTemplates, setUserTemplates] = useState<UserTemplate[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem('TIKZ_USER_LIBRARY');
    if (stored) {
      try {
        let parsed: UserTemplate[] = JSON.parse(stored);
        const originalLength = parsed.length;
        // Remove the specific template requested by the user
        parsed = parsed.filter(t => !t.title.toLowerCase().includes('ad-bc>0'));
        
        // Ensure all templates have a categoryId
        parsed = parsed.map(t => ({
          ...t,
          categoryId: t.categoryId || 'my-library'
        }));

        setUserTemplates(parsed);
        
        if (parsed.length !== originalLength) {
          localStorage.setItem('TIKZ_USER_LIBRARY', JSON.stringify(parsed));
        }
      } catch (e) {
        console.error("Failed to parse user library", e);
      }
    }
  }, []);

  const saveTemplate = (title: string, description: string, categoryId: string, subCategoryName: string, code: string) => {
    const newTemplate: UserTemplate = {
      id: `user-${Date.now()}`,
      title,
      description,
      code,
      categoryId,
      subCategoryName
    };
    
    const updated = [...userTemplates, newTemplate];
    setUserTemplates(updated);
    localStorage.setItem('TIKZ_USER_LIBRARY', JSON.stringify(updated));
  };

  const deleteTemplate = (id: string) => {
    const updated = userTemplates.filter(t => t.id !== id);
    setUserTemplates(updated);
    localStorage.setItem('TIKZ_USER_LIBRARY', JSON.stringify(updated));
  };

  const updateTemplate = (id: string, updates: Partial<UserTemplate>) => {
    let found = false;
    let updated = userTemplates.map(t => {
      if (t.id === id) {
        found = true;
        return { ...t, ...updates };
      }
      return t;
    });
    
    if (!found) {
      const newTemplate: UserTemplate = {
        id: id,
        title: updates.title || 'Untitled',
        description: updates.description || '',
        code: updates.code || '',
        categoryId: updates.categoryId || 'my-library',
        subCategoryName: updates.subCategoryName || 'Chung',
        ...updates
      };
      updated = [...updated, newTemplate];
    }
    
    setUserTemplates(updated);
    localStorage.setItem('TIKZ_USER_LIBRARY', JSON.stringify(updated));
  };

  const renameGroup = (oldName: string, newName: string) => {
    const updated = userTemplates.map(t => 
      t.subCategoryName === oldName ? { ...t, subCategoryName: newName } : t
    );
    setUserTemplates(updated);
    localStorage.setItem('TIKZ_USER_LIBRARY', JSON.stringify(updated));
  };

  return {
    userTemplates,
    saveTemplate,
    deleteTemplate,
    updateTemplate,
    renameGroup
  };
};
