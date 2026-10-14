using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;
using MatrixExamAI.WordAddIn.Bridge;

namespace MatrixExamAI.WordAddIn.TaskPane
{
    [ComVisible(true)]
    [Guid("7A4C62A1-04EA-4D88-8EF5-6A94CE015F33")]
    [ProgId("MatrixExamAI.WordAddIn.SidebarUserControl")]
    public class SidebarUserControl : UserControl
    {
        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        private static extern bool SetDllDirectory(string lpPathName);

        static SidebarUserControl()
        {
            try
            {
                string dir = Path.GetDirectoryName(typeof(SidebarUserControl).Assembly.Location) ?? "";
                if (!string.IsNullOrEmpty(dir) && Directory.Exists(dir))
                {
                    SetDllDirectory(dir);
                }
            }
            catch { }

            AppDomain.CurrentDomain.AssemblyResolve += (s, e) =>
            {
                try
                {
                    var requestedName = new System.Reflection.AssemblyName(e.Name).Name;
                    string dir = Path.GetDirectoryName(typeof(SidebarUserControl).Assembly.Location) ?? "";
                    if (!string.IsNullOrEmpty(dir))
                    {
                        string candidate = Path.Combine(dir, requestedName + ".dll");
                        if (File.Exists(candidate))
                        {
                            return System.Reflection.Assembly.LoadFrom(candidate);
                        }
                    }
                }
                catch { }
                return null;
            };
        }

        private WebView2? _webView;
        private WordBridge? _bridge;
        private bool _isInitialized;

        public WordBridge? Bridge => _bridge;
        public WebView2? WebView => _webView;

        public SidebarUserControl()
        {
            AddInLog.Log("[SidebarUserControl] Constructor started.");
            InitializeComponent();
            _ = InitializeWebViewAsync();
        }

        private void InitializeComponent()
        {
            this.SuspendLayout();
            this.AutoScaleMode = AutoScaleMode.Dpi;
            this.Dock = DockStyle.Fill;
            this.Width = 460;
            this.Height = 700;

            _webView = new WebView2
            {
                Dock = DockStyle.Fill
            };

            this.Controls.Add(_webView);
            this.ResumeLayout(false);

            _bridge = new WordBridge(_webView, this, ThisAddIn.Current?.DocumentService);
        }

        public async Task InitializeWebViewAsync()
        {
            if (_isInitialized || _webView == null) return;

            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string baseFolder = Path.Combine(localAppData, "MatrixExamAI");
            string primaryUserDataFolder = Path.Combine(baseFolder, "WebView2_Profile");
            Directory.CreateDirectory(primaryUserDataFolder);

            var envOptions = new CoreWebView2EnvironmentOptions(
                additionalBrowserArguments: "--disable-features=msWebOOUI --enable-smooth-scrolling"
            );

            // Thử khởi tạo với profile chính trước, nếu bị xung đột khóa (0x800700AA do nhiều tiến trình Word mở đồng thời)
            // thì tự động chuyển sang profile riêng biệt theo Process ID
            bool initialized = false;
            string[] candidateFolders = new[]
            {
                primaryUserDataFolder,
                Path.Combine(baseFolder, $"WebView2_Profile_{Process.GetCurrentProcess().Id}"),
                Path.Combine(baseFolder, $"WebView2_Profile_{Guid.NewGuid():N}")
            };

            foreach (var folder in candidateFolders)
            {
                try
                {
                    Directory.CreateDirectory(folder);
                    var env = await CoreWebView2Environment.CreateAsync(null, folder, envOptions);
                    await _webView.EnsureCoreWebView2Async(env);
                    initialized = true;
                    AddInLog.Log($"[SidebarUserControl] CoreWebView2 initialized using profile: '{folder}'.");
                    break;
                }
                catch (Exception ex) when (ex.HResult == unchecked((int)0x800700AA) ||
                                           ex.Message.Contains("0x800700AA") ||
                                           ex.Message.IndexOf("in use", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    AddInLog.Log($"[SidebarUserControl] Profile '{folder}' is locked (0x800700AA). Trying next profile candidate...");
                }
            }

            if (!initialized)
            {
                // Fallback cuối cùng: null folder (hệ thống tự cấp phát profile mặc định)
                try
                {
                    var env = await CoreWebView2Environment.CreateAsync(null, null, envOptions);
                    await _webView.EnsureCoreWebView2Async(env);
                    initialized = true;
                    AddInLog.Log("[SidebarUserControl] CoreWebView2 initialized using default system profile.");
                }
                catch (Exception ex)
                {
                    AddInLog.LogError("[SidebarUserControl] All WebView2 initialization attempts failed.", ex);
                    ShowErrorPanel(ex.Message);
                    return;
                }
            }

            try
            {
                // Configure browser settings
                _webView.CoreWebView2.Settings.IsStatusBarEnabled = false;
                _webView.CoreWebView2.Settings.AreDefaultContextMenusEnabled = true;
                _webView.CoreWebView2.Settings.IsZoomControlEnabled = true;

                // Setup Virtual Host Name Mapping for matrixexamai.local
                SetupVirtualHostMapping();

                // Initialize Bi-directional JSON-RPC Bridge
                _bridge ??= new WordBridge(_webView, this, ThisAddIn.Current?.DocumentService);
                _bridge.Initialize();

                _isInitialized = true;
                AddInLog.Log("[SidebarUserControl] WebView2 Initialized successfully.");
            }
            catch (Exception ex)
            {
                AddInLog.LogError("[SidebarUserControl] Post-init configuration error", ex);
                ShowErrorPanel(ex.Message);
            }
        }

        private void SetupVirtualHostMapping()
        {
            if (_webView?.CoreWebView2 == null) return;

            string webDir = ResolveWebDirectory();

            if (!string.IsNullOrEmpty(webDir) && Directory.Exists(webDir))
            {
                _webView.CoreWebView2.SetVirtualHostNameToFolderMapping(
                    "matrixexamai.local",
                    webDir,
                    CoreWebView2HostResourceAccessKind.Allow
                );
                _webView.CoreWebView2.Navigate($"https://matrixexamai.local/index.html?v={DateTime.UtcNow.Ticks}");
            }
            else
            {
                // Serve native embedded interactive UI
                _webView.CoreWebView2.NavigateToString(GetEmbeddedInteractiveHtml());
            }
        }

        private string ResolveWebDirectory()
        {
            string assemblyDir = Path.GetDirectoryName(typeof(SidebarUserControl).Assembly.Location) ?? "";
            if (!string.IsNullOrEmpty(assemblyDir))
            {
                string webSub = Path.Combine(assemblyDir, "Web");
                if (Directory.Exists(webSub) && File.Exists(Path.Combine(webSub, "index.html")))
                {
                    return webSub;
                }
            }

            string baseDir = AppDomain.CurrentDomain.BaseDirectory;

            // 1. Candidate dev source paths relative to binary output
            string[] relativeCandidates = new[]
            {
                Path.Combine(baseDir, @"..\..\..\src\MatrixExamAI.Web"),
                Path.Combine(baseDir, @"..\..\..\..\src\MatrixExamAI.Web"),
                Path.Combine(baseDir, @"..\..\src\MatrixExamAI.Web"),
                Path.Combine(baseDir, "Web"),
                Path.Combine(baseDir, "WebSidebar"),
                @"X:\word_addon\src\MatrixExamAI.Web"
            };

            foreach (var rel in relativeCandidates)
            {
                try
                {
                    string fullPath = Path.GetFullPath(rel);
                    if (Directory.Exists(fullPath) && File.Exists(Path.Combine(fullPath, "index.html")))
                    {
                        return fullPath;
                    }
                }
                catch { }
            }

            // 2. Explicit workspace directory fallback
            string workspaceDevPath = @"m:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\word_addon\src\MatrixExamAI.Web";
            if (Directory.Exists(workspaceDevPath) && File.Exists(Path.Combine(workspaceDevPath, "index.html")))
            {
                return workspaceDevPath;
            }

            // 3. User LocalAppData deployment
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            string localAppWeb = Path.Combine(localAppData, "MatrixExamAI", "Web");
            if (Directory.Exists(localAppWeb) && File.Exists(Path.Combine(localAppWeb, "index.html")))
            {
                return localAppWeb;
            }

            return string.Empty;
        }

        public void NavigateToTab(string tabName)
        {
            _bridge?.SendPushEvent("app/switchTab", new { tab = tabName });
        }

        private void ShowErrorPanel(string errorMessage)
        {
            var label = new Label
            {
                Dock = DockStyle.Fill,
                TextAlign = System.Drawing.ContentAlignment.MiddleCenter,
                Text = $"Không thể tải giao diện WebView2.\n\nChi tiết: {errorMessage}\n\nVui lòng đảm bảo máy tính đã cài đặt Microsoft Edge WebView2 Runtime.",
                ForeColor = System.Drawing.Color.DarkRed,
                Font = new System.Drawing.Font("Segoe UI", 10, System.Drawing.FontStyle.Regular)
            };
            this.Controls.Clear();
            this.Controls.Add(label);
        }

        private string GetEmbeddedInteractiveHtml()
        {
            return @"<!DOCTYPE html>
<html lang=""vi"">
<head>
    <meta charset=""UTF-8"">
    <meta name=""viewport"" content=""width=device-width, initial-scale=1.0"">
    <title>MatrixExamAI Sidebar</title>
    <style>
        :root {
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --border: #334155;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --success: #10b981;
            --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg);
            color: var(--text);
            font-family: var(--font-family);
            font-size: 13px;
            line-height: 1.5;
            padding: 16px;
            overflow-y: auto;
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }
        .logo-title {
            font-size: 16px;
            font-weight: 700;
            color: #60a5fa;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .badge {
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 9999px;
            background-color: rgba(59, 130, 246, 0.2);
            color: #93c5fd;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .section-title {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 8px;
        }
        .chip-container {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 12px;
        }
        .chip {
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 4px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.15s ease;
        }
        .chip:hover, .chip.active {
            background: var(--primary);
            border-color: var(--primary);
            color: #fff;
        }
        .prompt-area {
            width: 100%;
            height: 90px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px;
            color: var(--text);
            font-family: inherit;
            font-size: 13px;
            resize: vertical;
            margin-bottom: 12px;
        }
        .prompt-area:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
        }
        .btn-row {
            display: flex;
            gap: 8px;
            margin-bottom: 16px;
        }
        .btn {
            flex: 1;
            padding: 8px 14px;
            border-radius: 6px;
            border: none;
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            transition: all 0.15s ease;
        }
        .btn-primary { background: var(--primary); color: #fff; }
        .btn-primary:hover { background: var(--primary-hover); }
        .btn-secondary { background: var(--surface); color: var(--text); border: 1px solid var(--border); }
        .btn-secondary:hover { background: var(--surface-hover); }
        .editor-container {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            margin-bottom: 16px;
            overflow: hidden;
        }
        .editor-header {
            padding: 8px 12px;
            background: rgba(0,0,0,0.2);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            font-weight: 600;
        }
        .code-area {
            width: 100%;
            height: 160px;
            background: transparent;
            border: none;
            padding: 10px;
            color: #38bdf8;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 12px;
            resize: vertical;
            white-space: pre;
        }
        .code-area:focus { outline: none; }
        .status-box {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #6ee7b7;
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 12px;
            font-size: 12px;
            display: none;
        }
    </style>
</head>
<body>
    <div class=""header"">
        <div class=""logo-title"">
            <span>MatrixExamAI</span>
            <span class=""badge"">TikZ AI v5.0</span>
        </div>
        <div id=""status-indicator"" style=""font-size: 11px; color: #10b981;"">● Sẵn sàng</div>
    </div>

    <div class=""section-title"">Loại hình toán học</div>
    <div class=""chip-container"">
        <button class=""chip active"" onclick=""selectType(this, 'dothi')"">Đồ thị hàm số</button>
        <button class=""chip"" onclick=""selectType(this, 'bbt')"">Bảng biến thiên</button>
        <button class=""chip"" onclick=""selectType(this, 'bxd')"">Bảng xét dấu</button>
        <button class=""chip"" onclick=""selectType(this, 'khonggian')"">Hình không gian</button>
    </div>

    <div class=""section-title"">Mô tả hoặc Dán ảnh bài toán (Ctrl+V)</div>
    <textarea id=""prompt"" class=""prompt-area"" placeholder=""Nhập yêu cầu: Ví dụ: Vẽ đồ thị hàm số y = x^3 - 3x + 1 có các điểm cực trị...""></textarea>

    <div class=""btn-row"">
        <button class=""btn btn-primary"" onclick=""generateTikz()"">✨ Tạo hình AI</button>
        <button class=""btn btn-secondary"" onclick=""compileTikz()"">⚙️ Biên dịch</button>
    </div>

    <div id=""status-box"" class=""status-box""></div>

    <div class=""editor-container"">
        <div class=""editor-header"">
            <span>Mã nguồn TikZ</span>
            <button style=""background:none; border:none; color:var(--text-muted); cursor:pointer;"" onclick=""copyCode()"">Sao chép</button>
        </div>
        <textarea id=""tikz-code"" class=""code-area"">% Nhập hoặc sinh mã TikZ tại đây
\begin{tikzpicture}[scale=1]
\draw[->] (-2.5,0) -- (3,0) node[right] {$x$};
\draw[->] (0,-3) -- (0,4) node[above] {$y$};
\draw[domain=-2:2.2, smooth, variable=\x, blue, thick] plot ({\x}, {\x*\x*\x - 3*\x + 1});
\node at (0,0) [below left] {$O$};
\end{tikzpicture}</textarea>
    </div>

    <div class=""btn-row"">
        <button class=""btn btn-primary"" style=""background:#10b981;"" onclick=""insertIntoWord()"">📥 Chèn vào Word</button>
        <button class=""btn btn-secondary"" onclick=""readSelectedShape()"">🔄 Đọc từ Word</button>
    </div>

    <script>
        let bridgeAvailable = typeof window.chrome !== 'undefined' && typeof window.chrome.webview !== 'undefined';

        function showStatus(msg) {
            const el = document.getElementById('status-box');
            el.innerText = msg;
            el.style.display = 'block';
            setTimeout(() => { el.style.display = 'none'; }, 4000);
        }

        function selectType(btn, type) {
            document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
        }

        function copyCode() {
            const code = document.getElementById('tikz-code').value;
            navigator.clipboard.writeText(code);
            showStatus('Đã sao chép mã TikZ vào Clipboard!');
        }

        // Bridge calls
        function callBridge(action, payload) {
            if (!bridgeAvailable) {
                console.warn('Bridge not available: ', action, payload);
                return;
            }
            const id = 'req_' + Date.now();
            window.chrome.webview.postMessage({ id, action, payload });
        }

        function generateTikz() {
            const prompt = document.getElementById('prompt').value;
            showStatus('Đang gửi yêu cầu sinh mã TikZ tới AI...');
            callBridge('tikz/generate', { prompt: prompt, diagramType: 'dothi' });
        }

        function compileTikz() {
            const code = document.getElementById('tikz-code').value;
            showStatus('Đang gọi bộ biên dịch TeXLive...');
            callBridge('tikz/compile', { tikzCode: code, format: 'png' });
        }

        function insertIntoWord() {
            const code = document.getElementById('tikz-code').value;
            showStatus('Đang chèn hình ảnh vào tài liệu Word...');
            callBridge('word/insertPicture', { tikzCode: code, imagePath: '' });
        }

        function readSelectedShape() {
            showStatus('Đang đọc mã TikZ từ hình ảnh trong Word...');
            callBridge('word/getSelectedTikz', {});
        }

        // Handle incoming messages & push events from C#
        if (bridgeAvailable) {
            window.chrome.webview.addEventListener('message', (event) => {
                const msg = event.data;
                if (!msg) return;

                if (msg.event === 'word/selectionChanged' && msg.data) {
                    if (msg.data.hasSelectedShape && msg.data.tikzCode) {
                        document.getElementById('tikz-code').value = msg.data.tikzCode;
                        showStatus('Đã nạp mã TikZ của hình ảnh được chọn trong Word!');
                    }
                } else if (msg.status === 'success' && msg.data) {
                    if (msg.data.tikzCode) {
                        document.getElementById('tikz-code').value = msg.data.tikzCode;
                        showStatus('Mã TikZ đã được cập nhật thành công!');
                    }
                    if (msg.data.success) {
                        showStatus('Thao tác chèn vào Word hoàn tất!');
                    }
                }
            });
        }
    </script>
</body>
</html>";
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                _bridge?.Dispose();
                _webView?.Dispose();
            }
            base.Dispose(disposing);
        }
    }
}
