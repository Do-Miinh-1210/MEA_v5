
import React, { useState, useEffect } from 'react';
import { CopyIcon } from '../constants';

interface ShareModalProps {
  shareUrl: string;
  onClose: () => void;
}

const ShareModal: React.FC<ShareModalProps> = ({ shareUrl, onClose }) => {
  const [copyStatus, setCopyStatus] = useState('Sao chép');

  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => {
      window.removeEventListener('keydown', handleEsc);
    };
  }, [onClose]);

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl).then(() => {
      setCopyStatus('Đã sao chép!');
      setTimeout(() => setCopyStatus('Sao chép'), 2000);
    }).catch(() => {
      setCopyStatus('Thất bại!');
      setTimeout(() => setCopyStatus('Sao chép'), 2000);
    });
  };

  return (
    <div 
      className="fixed inset-0 bg-slate-800/80 dark:bg-slate-900/80 backdrop-blur-sm flex items-center justify-center z-50 font-sans"
      onClick={onClose}
    >
      <div 
        className="p-[0.5cm] bg-white dark:bg-slate-900 border-[2.5pt] border-cyan-500 rounded-xl"
        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside
      >
        <div 
          className="bg-slate-100 dark:bg-slate-800 rounded-lg p-6 max-w-xl w-full text-slate-900 dark:text-white"
        >
          <h2 className="text-xl font-bold mb-4">Chia sẻ bản vẽ TikZ</h2>
          <p className="text-slate-600 dark:text-slate-400 mb-4 text-[11pt]">
            Bất kỳ ai có liên kết này sẽ có thể xem bản vẽ của bạn ở chế độ chỉ đọc. Họ sẽ không thể chỉnh sửa code.
          </p>
          <div className="flex items-center space-x-2 bg-slate-200 dark:bg-slate-900 p-2 rounded-md border border-slate-300 dark:border-slate-700">
            <input
              type="text"
              value={shareUrl}
              readOnly
              className="flex-1 bg-transparent text-slate-700 dark:text-slate-300 focus:outline-none"
              onFocus={(e) => e.target.select()}
            />
            <button
              onClick={handleCopy}
              className="flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 text-white font-bold py-2 px-3 rounded-md transition-colors duration-200"
            >
              <CopyIcon className="h-4 w-4" />
              {copyStatus}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShareModal;