const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

const oldButton = `          {/* Bảng toggle */}
          <button
            onClick={() => setIsBbtNoFrame(!isBbtNoFrame)}
            className="flex items-center mr-2 text-sm font-medium text-slate-700 dark:text-slate-300 cursor-pointer hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors bg-transparent border-none px-1"
            title="Bật/Tắt viền bảng biến thiên"
          >
            {isBbtNoFrame ? 'No viền' : 'Viền'}
          </button>`;

const newDropdown = `          {/* Tùy chọn Options Menu */}
          <div className="relative" onMouseLeave={() => setShowOptionsMenu(false)}>
            <button
              onClick={() => setShowOptionsMenu(!showOptionsMenu)}
              className="flex items-center gap-1 mr-2 text-sm font-medium text-slate-700 dark:text-slate-300 cursor-pointer hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors bg-transparent border-none px-2 py-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800"
              title="Tùy chọn hiển thị đối tượng"
            >
              <span>Tùy chọn</span>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-3 h-3">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
              </svg>
            </button>
            {showOptionsMenu && (
              <div className="absolute top-full left-0 mt-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md shadow-lg z-50 w-36 overflow-hidden text-sm">
                <label className={\`flex items-center px-3 py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 \${!currentCode?.includes('tkzTab') ? 'opacity-50 cursor-not-allowed' : ''}\`}>
                  <input
                    type="checkbox"
                    className="mr-2 cursor-pointer rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    checked={!isBbtNoFrame}
                    onChange={() => setIsBbtNoFrame(!isBbtNoFrame)}
                    disabled={!currentCode?.includes('tkzTab')}
                  />
                  <span className="text-slate-700 dark:text-slate-300">Viền BBT</span>
                </label>
                <label className={\`flex items-center px-3 py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 \${!currentCode?.includes('% --- TIỆM CẬN ---') ? 'opacity-50 cursor-not-allowed' : ''}\`}>
                  <input
                    type="checkbox"
                    className="mr-2 cursor-pointer rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    checked={isAsymptoteHidden}
                    onChange={() => setIsAsymptoteHidden(!isAsymptoteHidden)}
                    disabled={!currentCode?.includes('% --- TIỆM CẬN ---')}
                  />
                  <span className="text-slate-700 dark:text-slate-300">Ẩn tiệm cận</span>
                </label>
                <label className={\`flex items-center px-3 py-2 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700 \${!currentCode?.includes('% --- ĐỒ THỊ HÀM SỐ ---') ? 'opacity-50 cursor-not-allowed' : ''}\`}>
                  <input
                    type="checkbox"
                    className="mr-2 cursor-pointer rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    checked={isFunctionHidden}
                    onChange={() => setIsFunctionHidden(!isFunctionHidden)}
                    disabled={!currentCode?.includes('% --- ĐỒ THỊ HÀM SỐ ---')}
                  />
                  <span className="text-slate-700 dark:text-slate-300">Ẩn hàm số</span>
                </label>
              </div>
            )}
          </div>`;

content = content.replace(oldButton, newDropdown);
fs.writeFileSync('App.tsx', content);
