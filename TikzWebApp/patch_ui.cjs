const fs = require('fs');
let code = fs.readFileSync('App.tsx', 'utf8');

// 1. Remove text "Full Màn hình" and change padding to be square
const fullScreenButtonRegex = /className="flex items-center gap-1 text-black dark:text-white font-normal text-sm px-2 py-1 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors whitespace-nowrap mr-2 bg-transparent border-none"/g;
code = code.replace(fullScreenButtonRegex, 'className="flex items-center gap-1 text-black dark:text-white font-normal text-sm p-1.5 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors mr-2 bg-transparent border-none"');

const fullScreenTextRegex = /\{\s*\}\s*Full Màn hình\s*<\/button>/;
// Wait, looking at grep -n "Full Màn hình":
/*
653-              </svg>
654-            )}
655:            Full Màn hình
656-          </button>
*/
code = code.replace(/<\/svg>\s*\)\}\s*Full Màn hình\s*<\/button>/g, '</svg>\n            )}\n          </button>');


// 2. Modify API Key Input
const apiInputRegex = /<input\s+type="password"\s+placeholder=\{!hasApiKey \? "Bạn cần nhập API" : "Nhập API Key\.\.\."\}\s+value=\{apiKeyInput\}\s+onChange=\{\(e\) => handleSaveApiKey\(e\.target\.value\)\}\s+className=\{`bg-transparent border-none focus:outline-none text-xs w-11 text-slate-800 dark:text-slate-200 px-1 \$\{!hasApiKey \? 'placeholder-red-500 placeholder:font-bold' : ''\}`\}\s+title="Nhập API Key cá nhân của bạn"\s+\/>/;

const newApiInput = `<input
              type="password"
              placeholder="Dán API vào đây"
              value={apiKeyInput}
              onChange={(e) => handleSaveApiKey(e.target.value)}
              className={\`bg-transparent border-none focus:outline-none text-xs w-32 text-slate-800 dark:text-slate-200 px-1 \${!hasApiKey ? 'placeholder-red-500 placeholder:font-bold' : ''}\`}
              title="Nhập API Key cá nhân của bạn"
            />`;

code = code.replace(apiInputRegex, newApiInput);

// Add Tooltip to the group
const apiGroupRegex = /<div className=\{\`flex items-center gap-1 bg-white dark:bg-slate-800 rounded border-\[1\.2pt\] p-1 shadow-sm transition-all relative group \$\{!\w+ \? 'border-red-500 shadow-\[0_0_8px_rgba\(239,68,68,0\.5\)\]' : 'border-teal-500'\}\`\}>/;

const tooltipHTML = `
            {/* Hướng dẫn API Key Hover */}
            <div className="absolute top-full right-0 mt-2 w-72 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 p-4 pointer-events-none">
              <h3 className="font-bold text-sm text-slate-800 dark:text-white mb-2">Cách lấy API Key:</h3>
              <ol className="text-xs text-slate-600 dark:text-slate-300 space-y-2 list-decimal list-inside">
                <li>Bấm vào biểu tượng liên kết (bên phải ô nhập) để tới <span className="font-semibold text-teal-600 dark:text-teal-400">Google AI Studio</span>.</li>
                <li>Đăng nhập bằng tài khoản Google của bạn.</li>
                <li>Nhấn nút <span className="font-semibold text-slate-800 dark:text-white bg-slate-100 dark:bg-slate-700 px-1 rounded">Create API key</span>.</li>
                <li>Copy dãy ký tự đó và dán vào ô này.</li>
              </ol>
            </div>
`;

// we need to insert the tooltip right after the closing </a> tag of the API Key input block.
const apiBlockRegex = /(<a \s*href="https:\/\/aistudio\.google\.com\/app\/apikey"[\s\S]*?<\/a>)/;
code = code.replace(apiBlockRegex, `$1${tooltipHTML}`);

fs.writeFileSync('App.tsx', code);
