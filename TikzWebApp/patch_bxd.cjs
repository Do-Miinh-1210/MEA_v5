const fs = require('fs');
let code = fs.readFileSync('components/AIAssistant.tsx', 'utf8');

code = code.replace(/if \(isBxdChecked\) selectedTasks\.push\("Bảng xét dấu \(BXD\)"\);/, 'if (isBxdChecked) selectedTasks.push("vẽ TẤT CẢ các hình, đồ thị, bảng biến thiên, ... (TikZ) có trong file hoặc yêu cầu mà không bỏ sót hình, BBT, đồ thị nào (trừ hình thực tế quá phức tạp)");');

code = code.replace(/<label className="flex items-center gap-1\.5 text-sm text-slate-700 dark:text-slate-300 cursor-pointer select-none font-medium hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">\s*<input\s*type="checkbox"\s*checked=\{isBxdChecked\}\s*onChange=\{\(e\) => setIsBxdChecked\(e\.target\.checked\)\}\s*className="rounded border-slate-300 text-cyan-500 focus:ring-cyan-500 w-4 h-4 cursor-pointer"\s*\/>\s*BXD\s*<\/label>/, `<label className="flex items-center gap-1.5 text-sm text-slate-700 dark:text-slate-300 cursor-pointer select-none font-medium hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
              <input 
                type="checkbox" 
                checked={isBxdChecked}
                onChange={(e) => setIsBxdChecked(e.target.checked)}
                className="rounded border-slate-300 text-cyan-500 focus:ring-cyan-500 w-4 h-4 cursor-pointer" 
              />
              TikZ
            </label>`);

fs.writeFileSync('components/AIAssistant.tsx', code);
