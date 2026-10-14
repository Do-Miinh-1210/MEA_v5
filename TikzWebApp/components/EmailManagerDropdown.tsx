import React, { useState, useEffect, useRef } from 'react';

interface ManagedEmail {
  email: string;
  allowed: boolean;
}

interface Props {
  onClose: () => void;
}

const EmailManagerDropdown: React.FC<Props> = ({ onClose }) => {
  const [emails, setEmails] = useState<ManagedEmail[]>([]);
  const [newEmail, setNewEmail] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem('TIKZ_MANAGED_EMAILS');
    if (stored) {
      try {
        setEmails(JSON.parse(stored));
      } catch (e) {}
    }
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const saveEmails = (updated: ManagedEmail[]) => {
    const sorted = [...updated].sort((a, b) => a.email.localeCompare(b.email));
    setEmails(sorted);
    localStorage.setItem('TIKZ_MANAGED_EMAILS', JSON.stringify(sorted));
  };

  const handleAdd = () => {
    if (!newEmail.trim() || !newEmail.includes('@')) return;
    const email = newEmail.trim().toLowerCase();
    if (emails.find(e => e.email === email)) return;
    
    saveEmails([...emails, { email, allowed: true }]);
    setNewEmail('');
  };

  const toggleAllow = (email: string) => {
    saveEmails(emails.map(e => e.email === email ? { ...e, allowed: !e.allowed } : e));
  };

  const removeEmail = (email: string) => {
    saveEmails(emails.filter(e => e.email !== email));
  };

  return (
    <div 
      ref={dropdownRef}
      className="absolute top-full right-0 mt-2 bg-white dark:bg-slate-800 rounded-lg p-4 w-[350px] shadow-xl border border-slate-200 dark:border-slate-700 z-50"
    >
      <h2 className="text-sm font-bold text-slate-800 dark:text-white mb-3">Quản lý Email truy cập</h2>
      
      <div className="flex gap-2 mb-3">
        <input
          type="email"
          value={newEmail}
          onChange={e => setNewEmail(e.target.value)}
          placeholder="Nhập email mới..."
          className="flex-1 px-2 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-800 dark:text-white focus:outline-none focus:border-cyan-500"
          onKeyDown={e => e.key === 'Enter' && handleAdd()}
        />
        <button
          onClick={handleAdd}
          className="px-3 py-1.5 bg-cyan-500 hover:bg-cyan-600 text-white rounded text-sm font-medium transition-colors"
        >
          Thêm
        </button>
      </div>

      <div className="max-h-[250px] overflow-y-auto border border-slate-200 dark:border-slate-700 rounded bg-slate-50 dark:bg-slate-800/50">
        {emails.length === 0 ? (
          <div className="p-3 text-center text-xs text-slate-500">Chưa có email nào</div>
        ) : (
          <ul className="divide-y divide-slate-200 dark:divide-slate-700">
            {emails.map(item => (
              <li key={item.email} className="p-2 flex items-center justify-between hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                <label className="flex items-center gap-2 cursor-pointer flex-1 overflow-hidden">
                  <input
                    type="checkbox"
                    checked={item.allowed}
                    onChange={() => toggleAllow(item.email)}
                    className="w-3.5 h-3.5 text-cyan-500 rounded border-slate-300 focus:ring-cyan-500"
                  />
                  <span className={`text-xs truncate ${!item.allowed ? 'text-slate-400 dark:text-slate-500 line-through' : 'text-slate-700 dark:text-slate-200'}`} title={item.email}>
                    {item.email}
                  </span>
                </label>
                <button
                  onClick={() => removeEmail(item.email)}
                  className="text-red-400 hover:text-red-600 p-1 ml-1"
                  title="Xóa"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default EmailManagerDropdown;
