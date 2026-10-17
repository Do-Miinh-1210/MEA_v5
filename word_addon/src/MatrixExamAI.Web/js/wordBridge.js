/**
 * MatrixExamAI WordBridge Client
 * Bi-directional JSON-RPC bridge over window.chrome.webview.postMessage
 * for communication between Microsoft Word Add-in (C#) and Sidebar Web UI.
 */
(function (global) {
  'use strict';

  class WordBridgeClient {
    constructor() {
      this.seq = 0;
      this.pendingRequests = new Map();
      this.eventListeners = new Map();
      this.isWebView2 = typeof window.chrome !== 'undefined' &&
                        typeof window.chrome.webview !== 'undefined' &&
                        typeof window.chrome.webview.postMessage === 'function';
      this._init();
    }

    _init() {
      if (this.isWebView2) {
        window.chrome.webview.addEventListener('message', (event) => {
          this._handleIncomingMessage(event.data);
        });
        console.log('[WordBridge] Connected to Microsoft Word WebView2 host.');
      } else {
        console.warn('[WordBridge] WebView2 environment not detected. Running in browser simulation mode.');
      }
    }

    _handleIncomingMessage(data) {
      if (!data) return;

      let message = data;
      if (typeof data === 'string') {
        try {
          message = JSON.parse(data);
        } catch (e) {
          console.error('[WordBridge] Failed to parse incoming message as JSON:', e, data);
          return;
        }
      }

      // 1. JSON-RPC Response to pending request
      if (message.id && this.pendingRequests.has(message.id)) {
        const { resolve, reject, timeoutId } = this.pendingRequests.get(message.id);
        clearTimeout(timeoutId);
        this.pendingRequests.delete(message.id);

        if (message.status === 'success') {
          resolve(message.data !== undefined ? message.data : {});
        } else {
          const errObj = message.error || {};
          const err = new Error(errObj.message || 'Lỗi xử lý từ Word Add-in');
          err.code = errObj.code || 'INTERNAL_ERROR';
          err.details = errObj.details || null;
          reject(err);
        }
        return;
      }

      // 2. JSON-RPC Push Event from C# (e.g., word/selectionChanged, ai/healingProgress, app/switchTab)
      if (message.event) {
        this._dispatchPushEvent(message.event, message.data);
      }
    }

    _dispatchPushEvent(eventName, data) {
      const key = (eventName || '').toLowerCase();
      const handlers = this.eventListeners.get(key) || [];
      for (const handler of handlers) {
        try {
          handler(data);
        } catch (err) {
          console.error(`[WordBridge] Error executing listener for event '${eventName}':`, err);
        }
      }
    }

    /**
     * Đăng ký lắng nghe sự kiện push từ C# (ví dụ: 'word/selectionChanged')
     */
    on(eventName, callback) {
      if (!eventName || typeof callback !== 'function') return () => {};
      const key = eventName.toLowerCase();
      if (!this.eventListeners.has(key)) {
        this.eventListeners.set(key, []);
      }
      this.eventListeners.get(key).push(callback);
      return () => this.off(eventName, callback);
    }

    /**
     * Hủy đăng ký lắng nghe sự kiện
     */
    off(eventName, callback) {
      const key = (eventName || '').toLowerCase();
      if (this.eventListeners.has(key)) {
        const filtered = this.eventListeners.get(key).filter(fn => fn !== callback);
        this.eventListeners.set(key, filtered);
      }
    }

    /**
     * Gửi yêu cầu JSON-RPC đến C# và chờ phản hồi qua Promise
     */
    async call(action, payload = {}, timeoutMs = 240000) {
      if (!this.isWebView2) {
        return this._mockCall(action, payload);
      }

      const id = `req_${Date.now()}_${++this.seq}`;

      return new Promise((resolve, reject) => {
        const timeoutId = setTimeout(() => {
          if (this.pendingRequests.has(id)) {
            this.pendingRequests.delete(id);
            reject(new Error(`Yêu cầu '${action}' quá thời gian chờ (${Math.round(timeoutMs / 1000)}s). Vui lòng thử lại.`));
          }
        }, timeoutMs);

        this.pendingRequests.set(id, { resolve, reject, timeoutId });

        try {
          const messageStr = JSON.stringify({
            id: id,
            action: action,
            payload: payload
          });
          window.chrome.webview.postMessage(messageStr);
        } catch (err) {
          clearTimeout(timeoutId);
          this.pendingRequests.delete(id);
          reject(err);
        }
      });
    }

    /**
     * Alias tương thích cho call(action, payload, timeoutMs)
     */
    async request(action, payload = {}, timeoutMs = 240000) {
      return this.call(action, payload, timeoutMs);
    }

    // Các hàm wrapper tiện ích cho các chức năng chính

    /**
     * Sinh mã TikZ từ prompt và ảnh (Multimodal Vision)
     */
    async generateTikz(prompt, options = {}) {
      const timeout = options.timeoutMs || 240000;
      return this.call('tikz/generate', {
        prompt: prompt,
        imageBase64: options.imageBase64 || null,
        imageMimeType: options.imageMimeType || 'image/png',
        diagramType: options.diagramType || 'Custom',
        extraPrompt: options.extraPrompt || null,
        enableNotes: options.enableNotes !== false,
        bbtNoFrame: !!options.bbtNoFrame,
        modelOverride: options.modelOverride || null
      }, timeout);
    }

    /**
     * Yêu cầu AI sửa mã TikZ hiện tại theo mô tả chỉnh sửa và hình ảnh đính kèm (Vision Multimodal)
     */
    async aiEditTikz(currentCode, editInstruction, options = {}) {
      const hasImage = !!options.imageBase64;
      const imageNote = hasImage
        ? "Người dùng đã đính kèm HÌNH ẢNH MINH HỌA. Hãy quan sát kỹ hình ảnh, đối chiếu với mã TikZ hiện tại và yêu cầu chỉnh sửa để cập nhật mã TikZ chính xác nhất.\n\n"
        : "";
      const prompt = `${imageNote}Mã TikZ hiện tại:\n${currentCode}\n\nYêu cầu chỉnh sửa: ${editInstruction}\nHãy giữ nguyên cấu trúc toán học và chỉ cập nhật theo đúng yêu cầu. Chỉ trả về khối mã \\begin{tikzpicture} ... \\end{tikzpicture}.`;
      return this.generateTikz(prompt, {
        diagramType: options.diagramType || 'Custom',
        imageBase64: options.imageBase64 || null,
        imageMimeType: options.imageMimeType || 'image/png',
        timeoutMs: 240000
      });
    }

    /**
     * Yêu cầu AI tối ưu hóa mã TikZ
     */
    async aiOptimizeTikz(currentCode, options = {}) {
      const prompt = `Bạn là chuyên gia LaTeX TikZ. Hãy tối ưu hóa đoạn mã TikZ dưới đây: chuẩn hóa tọa độ, loại bỏ các lệnh rác/dư thừa, đảm bảo nét vẽ và nhãn sắc nét, giữ nguyên ý nghĩa toán học. Chỉ trả về khối mã TikZ sạch bắt đầu bằng \\begin{tikzpicture} và kết thúc bằng \\end{tikzpicture}:\n\n${currentCode}`;
      return this.generateTikz(prompt, {
        diagramType: options.diagramType || 'Custom',
        timeoutMs: 240000
      });
    }

    /**
     * Lọc mã sạch bằng regex / TikzCodeExtractor
     */
    async cleanTikzCode(code) {
      return this.call('tikz/cleanCode', { code: code }, 30000);
    }

    /**
     * Biên dịch mã TikZ sang ảnh PNG 600 DPI, SVG hoặc EMF
     */
    async compileTikz(tikzCode, format = 'png', options = {}) {
      return this.call('tikz/compile', {
        tikzCode: tikzCode,
        format: format,
        border: options.border || '2pt',
        autoHeal: options.autoHeal !== false
      }, 120000);
    }

    /**
     * Sao chép vector EMF vào Clipboard
     */
    async copyEmf(tikzCode) {
      return this.call('tikz/copyEmf', { tikzCode: tikzCode }, 60000);
    }

    /**
     * Sao chép ảnh đã compile vào Clipboard
     */
    async copyImage(imagePath) {
      return this.call('tikz/copyImage', { imagePath: imagePath }, 30000);
    }

    /**
     * Lấy danh mục mẫu hình vẽ từ C#
     */
    async getTikzTemplates() {
      return this.call('tikz/templates', {}, 30000);
    }

    /**
     * Chèn hình ảnh vào vị trí con trỏ chuột trong Word kèm metadata mã TikZ
     */
    async insertPicture(imagePath, tikzCode) {
      return this.call('word/insertPicture', {
        imagePath: imagePath,
        tikzCode: tikzCode
      });
    }

    /**
     * Cập nhật hình ảnh đang được chọn trong Word
     */
    async updateSelectedPicture(imagePath, tikzCode) {
      return this.call('word/updateTikz', {
        imagePath: imagePath,
        tikzCode: tikzCode
      });
    }

    /**
     * Lấy mã TikZ của hình ảnh đang chọn trong Word
     */
    async getSelectedTikz() {
      return this.call('word/getSelectedTikz', {});
    }

    /**
     * Lấy đoạn văn bản Word đang bôi đen
     */
    async getSelectionText() {
      return this.call('word/getSelectionText', {});
    }

    /**
     * Thay thế đoạn văn bản Word đang bôi đen
     */
    async replaceSelectionText(newText) {
      return this.call('word/replaceSelectionText', { newText: newText });
    }

    /**
     * Lấy cấu hình hệ thống (API keys, models)
     */
    async getConfig() {
      return this.call('system/getConfig', {});
    }

    /**
     * Lưu cấu hình hệ thống
     */
    async saveConfig(config) {
      return this.call('system/saveConfig', config);
    }

    /**
     * Mock dữ liệu khi chạy thử nghiệm trên trình duyệt thông thường
     */
    async _mockCall(action, payload) {
      console.log(`[WordBridge Mock] Executing ${action} with payload:`, payload);
      await new Promise(r => setTimeout(r, 400));

      switch (action) {
        case 'app/ping':
          return { pong: true, timestamp: new Date().toISOString() };

        case 'system/getConfig':
          return {
            provider: 'gemini',
            model: 'gemini-3.8-flash',
            hasApiKey: false
          };

        case 'system/saveConfig':
          return { saved: true };

        case 'word/getSelectedTikz':
          return { hasTikz: false, tikzCode: '' };

        case 'tikz/generate':
          return {
            success: true,
            tikzCode: `% Mẫu TikZ sinh tự động (${payload.diagramType || 'Đồ thị'})\n\\begin{tikzpicture}[scale=1]\n\\draw[->, thick] (-3,0) -- (3,0) node[right] {$x$};\n\\draw[->, thick] (0,-3) -- (0,3) node[above] {$y$};\n\\draw[domain=-2.2:2.2, smooth, variable=\\x, blue, thick] plot ({\\x}, {\\x*\\x - 2});\n\\node at (0,0) [below left] {$O$};\n\\node at (0,-2) [below right] {$-2$};\n\\end{tikzpicture}`,
            model: 'gemini-3.8-flash',
            provider: 'Simulation',
            executionTimeMs: 450
          };

        case 'tikz/compile':
          return {
            success: true,
            imagePath: 'C:\\Temp\\mock_tikz_preview.png',
            previewDataUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="-150 -100 300 200"><rect x="-150" y="-100" width="300" height="200" fill="%231e293b"/><line x1="-130" y1="0" x2="130" y2="0" stroke="%2394a3b8" stroke-width="2"/><line x1="0" y1="80" x2="0" y2="-80" stroke="%2394a3b8" stroke-width="2"/><path d="M -100 50 Q 0 -80 100 50" stroke="%2338bdf8" stroke-width="3" fill="none"/><circle cx="0" cy="-15" r="4" fill="%23f43f5e"/><text x="10" y="-15" fill="%23f8fafc" font-size="12">Cực đại</text></svg>',
            format: payload.format || 'png',
            compilationTimeMs: 320
          };

        case 'word/insertPicture':
          return {
            success: true,
            shapeTitle: 'MatrixExamAI:TikZ',
            shapeId: 'shape_1'
          };

        case 'word/updateTikz':
          return {
            success: true,
            isUpdated: true
          };

        default:
          return { success: true };
      }
    }
  }

  // Khởi tạo instance toàn cục
  global.WordBridge = new WordBridgeClient();
})(window);
