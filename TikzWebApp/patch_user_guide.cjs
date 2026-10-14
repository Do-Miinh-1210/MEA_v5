const fs = require('fs');
let content = fs.readFileSync('components/UserGuideModal.tsx', 'utf8');

const oldProps = `import React from 'react';

interface UserGuideModalProps {
  onClose: () => void;
}

export default function UserGuideModal({ onClose }: UserGuideModalProps) {`;

const newProps = `import React, { useState } from 'react';

interface UserGuideModalProps {
  onClose: () => void;
  hasApiKey?: boolean;
  onSaveApiKey?: (key: string) => void;
}

export default function UserGuideModal({ onClose, hasApiKey = true, onSaveApiKey }: UserGuideModalProps) {
  const [apiKeyInput, setApiKeyInput] = useState('');
  
  const handleSave = () => {
    if (onSaveApiKey) {
      onSaveApiKey(apiKeyInput);
    }
  };`;

content = content.replace(oldProps, newProps);

const oldCloseButton = `<button onClick={onClose} className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-all">`;
const newCloseButton = `{hasApiKey && (<button onClick={onClose} className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-all">`;

content = content.replace(oldCloseButton, newCloseButton);

const oldCloseIcon = `<path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>`;
const newCloseIcon = `<path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>)}`;

content = content.replace(oldCloseIcon, newCloseIcon);

const oldSection1 = `<li>Dán dãy ký tự <strong>API Key</strong> vào ô góc trên bên phải màn hình.</li>
                        <li>Bấm nút <strong>Lưu</strong> (biểu tượng đĩa mềm). Hệ thống sẽ tự động lưu lại và Thầy/Cô không cần nhập lại vào lần sau.</li>
                      </ul>`;
const newSection1 = `<li>Lấy API Key tại <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">Google AI Studio</a>.</li>
                        <li>Dán dãy ký tự <strong>API Key</strong> vào ô dưới đây (hoặc góc trên bên phải màn hình).</li>
                      </ul>
                      
                      {!hasApiKey && (
                        <div className="mt-3 flex items-center gap-2 bg-white dark:bg-slate-800 p-2 rounded-lg border border-red-300 dark:border-red-700 shadow-sm">
                          <input
                            type="password"
                            placeholder="Nhập API Key của bạn vào đây..."
                            value={apiKeyInput}
                            onChange={(e) => setApiKeyInput(e.target.value)}
                            className="flex-1 bg-transparent border-none focus:outline-none text-sm text-slate-800 dark:text-slate-200 px-2"
                          />
                          <button
                            onClick={handleSave}
                            disabled={!apiKeyInput.trim()}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded-md text-sm font-medium transition-colors disabled:opacity-50"
                          >
                            Lưu API Key
                          </button>
                        </div>
                      )}`;

content = content.replace(oldSection1, newSection1);

fs.writeFileSync('components/UserGuideModal.tsx', content);
