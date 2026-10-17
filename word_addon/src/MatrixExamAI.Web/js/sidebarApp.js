/**
 * MatrixExamAI Sidebar Application Logic
 * Integrates prompt management, clipboard image paste, preset chips,
 * code editor with line numbers, zoom/pan visual preview, and Word COM actions.
 */
(function () {
  'use strict';

  // Sample default TikZ code
  const DEFAULT_TIKZ_CODE = `% ĐỒ THỊ HÀM SỐ BẬC 3
\\begin{tikzpicture}[>=stealth, scale=0.95]
  % Trục tọa độ
  \\draw[->, thick] (-2.5,0) -- (3,0) node[right] {$x$};
  \\draw[->, thick] (0,-3) -- (0,3.5) node[above] {$y$};
  \\node at (0,0) [below left] {$O$};

  % Đồ thị hàm số y = x^3 - 3x + 1
  \\draw[domain=-2.1:2.2, smooth, variable=\\x, blue, very thick] 
    plot ({\\x}, {\\x*\\x*\\x - 3*\\x + 1});

  % Điểm cực đại (-1, 3) và cực tiểu (1, -1)
  \\draw[dashed, thin] (-1,0) -- (-1,3) -- (0,3);
  \\draw[dashed, thin] (1,0) -- (1,-1) -- (0,-1);
  \\fill[red] (-1,3) circle (2pt) node[above left, black] {$A(-1;3)$};
  \\fill[red] (1,-1) circle (2pt) node[below right, black] {$B(1;-1)$};

  \\node at (-1,0) [below] {$-1$};
  \\node at (1,0) [above] {$1$};
  \\node at (0,3) [right] {$3$};
  \\node at (0,-1) [left] {$-1$};
\\end{tikzpicture}`;

  // Presets mapping
  const PRESET_TEMPLATES = {
    BBT: {
      label: 'Bảng biến thiên 3 dòng',
      prompt: 'Vẽ bảng biến thiên 3 dòng hàm số y = (2x - 1)/(x + 1) có tiệm cận đứng x = -1 và tiệm cận ngang y = 2',
      sampleCode: `% BẢNG BIẾN THIÊN 3 DÒNG (tkz-tab)
\\begin{tikzpicture}
  \\tkzTabInit[lgt=1.5, espcl=2.5, deltacl=0.6]
    {$x$ / 1, $y'$ / 1, $y$ / 2.5}
    {$-\\infty$, $-1$, $+\\infty$}
  \\tkzTabLine{ , +, d, +, }
  \\tkzTabVar{-/ $2$, +D-/ $+\\infty$ / $-\\infty$, +/ $2$}
\\end{tikzpicture}`
    },
    BXD: {
      label: 'Bảng xét dấu',
      prompt: 'Vẽ bảng xét dấu đạo hàm f\'(x) = (x^2 - 4)(3 - x) với các nghiệm -2, 2, 3',
      sampleCode: `% BẢNG XÉT DẤU
\\begin{tikzpicture}
  \\tkzTabInit[lgt=1.2, espcl=2.2, deltacl=0.6]
    {$x$ / 1, $f'(x)$ / 1}
    {$-\\infty$, $-2$, $2$, $3$, $+\\infty$}
  \\tkzTabLine{ , +, 0, -, 0, +, 0, -, }
\\end{tikzpicture}`
    },
    DoThi: {
      label: 'Đồ thị hàm số',
      prompt: 'Vẽ đồ thị hàm số y = x^3 - 3x + 1 có các điểm cực đại, cực tiểu và các đường gióng tọa độ',
      sampleCode: DEFAULT_TIKZ_CODE
    },
    HinhKhongGian: {
      label: 'Hình không gian 3D',
      prompt: 'Vẽ hình chóp tam giác S.ABC có đáy ABC là tam giác vuông tại B, SA vuông góc với đáy (ABC)',
      sampleCode: `% HÌNH CHÓP S.ABC
\\begin{tikzpicture}[scale=0.9]
  \\coordinate (A) at (0,0);
  \\coordinate (B) at (1.5,-1.2);
  \\coordinate (C) at (4.5,0);
  \\coordinate (S) at (0,3.5);

  % Nét đứt (khuất)
  \\draw[dashed, thick] (A) -- (C);
  
  % Nét liền (thấy)
  \\draw[thick] (S) -- (A) -- (B) -- (C) -- (S);
  \\draw[thick] (S) -- (B);

  % Ký hiệu vuông góc
  \\draw (0,0.3) -- (0.3,0.3) -- (0.3,0);
  \\draw (1.3,-1.0) -- (1.5,-0.8) -- (1.7,-1.0);

  % Nhãn điểm
  \\node at (S) [above] {$S$};
  \\node at (A) [left] {$A$};
  \\node at (B) [below] {$B$};
  \\node at (C) [right] {$C$};
\\end{tikzpicture}`
    }
  };

  // State
  const state = {
    prompt: '',
    selectedDiagramType: 'DoThi',
    pastedImageBase64: null,
    pastedImageMimeType: 'image/png',
    pastedImageSizeKB: 0,
    currentTikzCode: DEFAULT_TIKZ_CODE,
    compiledImagePath: null,
    compiledPreviewUrl: null,
    compiledFormat: 'png',
    hasWordTikzSelected: false,
    selectedWordShapeTitle: '',
    isGenerating: false,
    isCompiling: false,
    isInserting: false,
    // Convert State
    activeMainTab: 'tikz',
    convertImageBase64: null,
    convertImageMimeType: 'image/png',
    convertExtractedQuestions: [],
    convertFormattedText: '',
    isConverting: false,
    // Zoom and Pan
    zoom: 1.0,
    pan: { x: 0, y: 0 },
    isDragging: false,
    dragStart: { x: 0, y: 0 }
  };

  // DOM Elements cache
  let dom = {};

  function initDomElements() {
    dom = {
      promptCard: document.getElementById('tikz-prompt-card'),
      promptTextarea: document.getElementById('prompt-input'),
      clearPromptBtn: document.getElementById('clear-prompt-btn'),
      btnGetWordImage: document.getElementById('btn-get-word-image'),
      btnPasteClipboardImage: document.getElementById('btn-paste-clipboard-image'),
      presetChips: document.querySelectorAll('.preset-chip'),
      imagePreviewContainer: document.getElementById('image-preview-container'),
      imageThumb: document.getElementById('image-thumb'),
      imageMetaDetails: document.getElementById('image-meta-details'),
      removeImageBtn: document.getElementById('remove-image-btn'),
      
      btnGenerateAi: document.getElementById('btn-generate-ai'),
      btnCompileTikz: document.getElementById('btn-compile-tikz'),
      btnInsertWord: document.getElementById('btn-insert-word'),
      btnUpdateWord: document.getElementById('btn-update-word'),

      selectionBanner: document.getElementById('selection-banner'),
      selectionTitle: document.getElementById('selection-title'),
      statusToast: document.getElementById('status-toast'),
      toastMessage: document.getElementById('toast-message'),
      toastClose: document.getElementById('toast-close'),

      tabEditorBtn: document.getElementById('tab-editor-btn'),
      tabPreviewBtn: document.getElementById('tab-preview-btn'),
      tabEditorContent: document.getElementById('tab-editor-content'),
      tabPreviewContent: document.getElementById('tab-preview-content'),

      codeTextarea: document.getElementById('code-textarea'),
      lineNumbers: document.getElementById('line-numbers'),
      btnCopyCode: document.getElementById('btn-copy-code'),
      btnClearCode: document.getElementById('btn-clear-code'),
      codeLineCount: document.getElementById('code-line-count'),

      previewViewport: document.getElementById('preview-viewport'),
      previewCanvas: document.getElementById('preview-canvas-wrapper'),
      previewImage: document.getElementById('preview-image'),
      previewEmptyState: document.getElementById('preview-empty-state'),
      zoomLevelDisplay: document.getElementById('zoom-level-display'),
      btnZoomIn: document.getElementById('btn-zoom-in'),
      btnZoomOut: document.getElementById('btn-zoom-out'),
      btnZoomReset: document.getElementById('btn-zoom-reset'),
      btnZoomFit: document.getElementById('btn-zoom-fit'),
      formatBtns: document.querySelectorAll('.format-btn'),

      latexErrorPanel: document.getElementById('latex-error-panel'),
      latexErrorContent: document.getElementById('latex-error-content'),

      btnOpenSettings: document.getElementById('btn-open-settings'),
      settingsModal: document.getElementById('settings-modal'),
      btnCloseSettings: document.getElementById('btn-close-settings'),
      btnSaveSettings: document.getElementById('btn-save-settings'),
      providerSelect: document.getElementById('provider-select'),
      modelSelect: document.getElementById('model-select'),
      apiKeyLabel: document.getElementById('api-key-label'),
      apiKeyInput: document.getElementById('api-key-input'),
      apiKeyHint: document.getElementById('api-key-hint'),
      btnTestConnection: document.getElementById('btn-test-connection'),
      settingsTestStatus: document.getElementById('settings-test-status'),

      // Feature Nav & Panels (5 tabs)
      navBtnTikz: document.getElementById('nav-btn-tikz'),
      navBtnAuthoring: document.getElementById('nav-btn-authoring'),
      navBtnQuestionBank: document.getElementById('nav-btn-questionbank'),
      navBtnMatrix: document.getElementById('nav-btn-matrix'),
      navBtnNormalize: document.getElementById('nav-btn-normalize'),

      focusedModuleIcon: document.getElementById('focused-module-icon'),
      focusedModuleTitle: document.getElementById('focused-module-title'),
      focusedModuleSubtitle: document.getElementById('focused-module-subtitle'),
      btnToggleModuleMenu: document.getElementById('btn-toggle-module-menu'),
      moduleDropdownMenu: document.getElementById('module-dropdown-menu'),
      moduleSwitchWrapper: document.querySelector('.module-switch-wrapper'),

      panelTikz: document.getElementById('panel-tikz'),
      panelAuthoring: document.getElementById('panel-authoring'),
      panelQuestionBank: document.getElementById('panel-questionbank'),
      panelMatrix: document.getElementById('panel-matrix'),
      panelNormalize: document.getElementById('panel-normalize'),

      // Phase 2 Authoring
      btnReloadSelection: document.getElementById('btn-reload-selection'),
      authoringSelectedText: document.getElementById('authoring-selected-text'),
      authoringMetaCount: document.getElementById('authoring-meta-count'),
      authoringMetaBadge: document.getElementById('authoring-meta-badge'),
      authoringActionTiles: document.querySelectorAll('.action-tile'),
      authoringCustomPrompt: document.getElementById('authoring-custom-prompt'),
      btnExecuteCustomAi: document.getElementById('btn-execute-custom-ai'),
      authoringResultSection: document.getElementById('authoring-result-section'),
      authoringTaskTitle: document.getElementById('authoring-task-title'),
      authoringModelUsed: document.getElementById('authoring-model-used'),
      authoringResultContent: document.getElementById('authoring-result-content'),
      btnCopyResult: document.getElementById('btn-copy-result'),
      btnClearResult: document.getElementById('btn-clear-result'),
      btnReplaceWordText: document.getElementById('btn-replace-word-text'),
      btnInsertWordText: document.getElementById('btn-insert-word-text'),

      // Phase 3 Question Bank
      qbSearchInput: document.getElementById('qb-search-input'),
      qbBtnSearch: document.getElementById('qb-btn-search'),
      qbFilterGrade: document.getElementById('qb-filter-grade'),
      qbFilterLevel: document.getElementById('qb-filter-level'),
      qbFilterType: document.getElementById('qb-filter-type'),
      qbBtnSaveSelection: document.getElementById('qb-btn-save-selection'),
      qbBtnRefresh: document.getElementById('qb-btn-refresh'),
      qbCountBadge: document.getElementById('qb-count-badge'),
      qbQuestionsList: document.getElementById('qb-questions-list'),

      // Phase 4 Exam Matrix
      matrixTitleInput: document.getElementById('matrix-title-input'),
      matrixGradeSelect: document.getElementById('matrix-grade-select'),
      matrixP1Count: document.getElementById('matrix-p1-count'),
      matrixP2Count: document.getElementById('matrix-p2-count'),
      matrixP3Count: document.getElementById('matrix-p3-count'),
      matrixBtnGenerate: document.getElementById('matrix-btn-generate'),
      matrixResultSection: document.getElementById('matrix-result-section'),
      matrixResultBadge: document.getElementById('matrix-result-badge'),
      matrixResultContent: document.getElementById('matrix-result-content'),
      matrixBtnExportWord: document.getElementById('matrix-btn-export-word'),

      // Convert Module Elements (Ảnh + Text/LaTeX)
      navBtnConvert: document.getElementById('nav-btn-convert'),
      panelConvert: document.getElementById('panel-convert'),
      convertSubtabImg: document.getElementById('convert-subtab-img'),
      convertSubtabText: document.getElementById('convert-subtab-text'),
      convertModeImage: document.getElementById('convert-mode-image'),
      convertModeText: document.getElementById('convert-mode-text'),

      // Image Mode Elements
      btnConvertPaste: document.getElementById('btn-convert-paste'),
      btnConvertPickFile: document.getElementById('btn-convert-pick-file'),
      convertFileInput: document.getElementById('convert-file-input'),
      convertImagePreviewContainer: document.getElementById('convert-image-preview-container'),
      convertImageMeta: document.getElementById('convert-image-meta'),
      convertImageThumb: document.getElementById('convert-image-thumb'),
      btnConvertClearImage: document.getElementById('btn-convert-clear-image'),
      convertQtypeSelect: document.getElementById('convert-qtype-select'),
      convertIncludeSolution: document.getElementById('convert-include-solution'),
      btnConvertRun: document.getElementById('btn-convert-run'),

      // Text/LaTeX Mode Elements
      btnConvertCopyPrompt: document.getElementById('btn-convert-copy-prompt'),
      btnConvertLoadTextFile: document.getElementById('btn-convert-load-text-file'),
      convertTextFilePicker: document.getElementById('convert-text-file-picker'),
      convertTextGrade: document.getElementById('convert-text-grade'),
      convertTextSubject: document.getElementById('convert-text-subject'),
      btnConvertClearText: document.getElementById('btn-convert-clear-text'),
      convertRawText: document.getElementById('convert-raw-text'),
      btnConvertParseLocal: document.getElementById('btn-convert-parse-local'),
      btnConvertTextInsertWord: document.getElementById('btn-convert-text-insert-word'),
      btnConvertTextCallAi: document.getElementById('btn-convert-text-call-ai'),
      btnConvertTextSaveBank: document.getElementById('btn-convert-text-save-bank'),
      btnConvertTextCopy: document.getElementById('btn-convert-text-copy'),

      // Shared Result Elements
      convertResultSection: document.getElementById('convert-result-section'),
      convertResultBadge: document.getElementById('convert-result-badge'),
      convertMetaSummary: document.getElementById('convert-meta-summary'),
      convertResultContent: document.getElementById('convert-result-content'),
      btnConvertCopyResult: document.getElementById('btn-convert-copy-result'),
      btnConvertClearResult: document.getElementById('btn-convert-clear-result'),
      btnConvertInsertWord: document.getElementById('btn-convert-insert-word'),
      btnConvertSaveQb: document.getElementById('btn-convert-save-qb'),

      // Phase 5 Normalize
      normFontName: document.getElementById('norm-font-name'),
      normFontSize: document.getElementById('norm-font-size'),
      normLineSpacing: document.getElementById('norm-line-spacing'),
      btnStandardizeSelection: document.getElementById('btn-standardize-selection'),
      btnStandardizeDoc: document.getElementById('btn-standardize-doc')
    };
  }

  // Toast / Status Notification
  let toastTimer = null;
  function showToast(message, type = 'info', duration = 4000) {
    if (!dom.statusToast) return;
    if (toastTimer) clearTimeout(toastTimer);

    dom.statusToast.className = `status-toast active ${type}`;
    dom.toastMessage.innerText = message;

    if (duration > 0) {
      toastTimer = setTimeout(() => {
        hideToast();
      }, duration);
    }
  }

  function hideToast() {
    if (dom.statusToast) {
      dom.statusToast.classList.remove('active');
    }
  }

  // Auto-expand Textarea
  function autoExpandTextarea(textarea) {
    if (!textarea) return;
    textarea.style.height = 'auto';
    const newHeight = Math.min(Math.max(textarea.scrollHeight, 72), 180);
    textarea.style.height = newHeight + 'px';

    if (dom.clearPromptBtn) {
      dom.clearPromptBtn.style.display = textarea.value.trim() ? 'flex' : 'none';
    }
  }

  // Line Numbers Synchronization
  function updateLineNumbers() {
    if (!dom.codeTextarea || !dom.lineNumbers) return;
    const lines = dom.codeTextarea.value.split('\n').length;
    let numbers = '';
    for (let i = 1; i <= lines; i++) {
      numbers += i + '\n';
    }
    dom.lineNumbers.textContent = numbers;
    if (dom.codeLineCount) {
      dom.codeLineCount.innerText = `${lines} dòng`;
    }
  }

  function syncScroll() {
    if (dom.lineNumbers && dom.codeTextarea) {
      dom.lineNumbers.scrollTop = dom.codeTextarea.scrollTop;
    }
  }

  // Set TikZ Image to Preview & State
  function setTikzImage(base64Data, mimeType, sizeKb, dataUrl) {
    if (!base64Data) return;
    mimeType = mimeType || 'image/png';
    sizeKb = sizeKb || Math.round(base64Data.length * 0.75 / 1024);
    dataUrl = dataUrl || `data:${mimeType};base64,${base64Data}`;

    state.pastedImageBase64 = base64Data;
    state.pastedImageMimeType = mimeType;
    state.pastedImageSizeKB = sizeKb;

    if (dom.imageThumb) dom.imageThumb.src = dataUrl;
    if (dom.imageMetaDetails) {
      dom.imageMetaDetails.innerText = `${mimeType} • ${sizeKb} KB • Ảnh bài toán`;
    }
    if (dom.imagePreviewContainer) {
      dom.imagePreviewContainer.classList.add('active');
    }
  }

  // Lấy ảnh đang chọn trong Word hoặc từ Clipboard
  async function loadWordSelectedImage() {
    try {
      showToast('Đang quét ảnh từ Word & Clipboard...', 'info', 1500);
      const res = await window.WordBridge.request('word/getSelectedImage');
      if (res && res.success && res.hasImage && res.imageBase64) {
        setTikzImage(res.imageBase64, res.mimeType || 'image/png', res.sizeKb);
        showToast('✓ Đã nạp hình ảnh từ Word thành công!', 'success', 3000);
        return true;
      } else {
        const nativeOk = await pasteTikzImageFromNativeClipboard();
        if (!nativeOk) {
          showToast('Vui lòng chọn hình ảnh trong tài liệu Word hoặc sao chép ảnh (Ctrl+C) trước!', 'warning', 3500);
        }
        return nativeOk;
      }
    } catch (e) {
      console.warn('loadWordSelectedImage error:', e);
      return await pasteTikzImageFromNativeClipboard();
    }
  }

  // Clipboard Image Paste Handler (Web + Native Word Fallback)
  function handleClipboardPaste(e) {
    const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items;
    let foundWebImage = false;

    if (items) {
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type.indexOf('image') !== -1) {
          e.preventDefault();
          foundWebImage = true;
          const file = item.getAsFile();
          if (!file) continue;

          const reader = new FileReader();
          reader.onload = function (event) {
            const dataUrl = event.target.result;
            const base64Data = dataUrl.split(',')[1];
            const mimeType = file.type || 'image/png';
            const sizeKb = Math.round(file.size / 1024);

            // Route to Convert tab if active
            if (state.activeMainTab === 'convert') {
              switchConvertSubtab('image');
              setConvertImage(base64Data, mimeType, sizeKb, dataUrl);
              return;
            }

            setTikzImage(base64Data, mimeType, sizeKb, dataUrl);
            showToast('✓ Đã dán ảnh (Ctrl+V) thành công!', 'success');
          };
          reader.readAsDataURL(file);
          break;
        }
      }
    }

    // Nếu không tìm thấy format web image (ảnh copy từ Word), gọi native Windows clipboard
    if (!foundWebImage && state.activeMainTab === 'tikz') {
      pasteTikzImageFromNativeClipboard();
    }
  }

  // Drag & Drop handlers for Prompt Card
  function setupPromptDragAndDrop() {
    const dropTargets = [dom.promptCard, dom.promptTextarea].filter(Boolean);
    dropTargets.forEach(target => {
      target.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (dom.promptCard) dom.promptCard.classList.add('drag-over');
      });

      target.addEventListener('dragenter', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (dom.promptCard) dom.promptCard.classList.add('drag-over');
      });

      target.addEventListener('dragleave', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (dom.promptCard) dom.promptCard.classList.remove('drag-over');
      });

      target.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (dom.promptCard) dom.promptCard.classList.remove('drag-over');

        const files = e.dataTransfer && e.dataTransfer.files;
        if (files && files.length > 0) {
          const file = files[0];
          if (file.type && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (ev) => {
              const dataUrl = ev.target.result;
              const base64Data = dataUrl.split(',')[1];
              const mimeType = file.type || 'image/png';
              const sizeKb = Math.round(file.size / 1024);
              setTikzImage(base64Data, mimeType, sizeKb, dataUrl);
              showToast('✓ Đã nạp hình ảnh từ thao tác kéo thả thành công!', 'success');
            };
            reader.readAsDataURL(file);
            return;
          }
        }

        // Kiểm tra drag từ Word (HTML OLE / image) hoặc gọi fallback
        const html = e.dataTransfer ? e.dataTransfer.getData('text/html') : '';
        if (html && html.indexOf('<img') !== -1) {
          const match = html.match(/<img[^>]+src=["']([^"']+)["']/i);
          if (match && match[1]) {
            const src = match[1];
            if (src.startsWith('data:image')) {
              const parts = src.split(',');
              const mime = parts[0].match(/:(.*?);/)?.[1] || 'image/png';
              const b64 = parts[1];
              setTikzImage(b64, mime, Math.round(b64.length * 0.75 / 1024), src);
              showToast('✓ Đã nạp hình ảnh kéo thả từ Word!', 'success');
              return;
            }
          }
        }

        loadWordSelectedImage();
      });
    });
  }

  function removePastedImage() {
    state.pastedImageBase64 = null;
    state.pastedImageSizeKB = 0;
    if (dom.imagePreviewContainer) {
      dom.imagePreviewContainer.classList.remove('active');
    }
    if (dom.imageThumb) {
      dom.imageThumb.src = '';
    }
    showToast('Đã gỡ ảnh đính kèm.', 'info', 2000);
  }

  // Preset Selection
  function selectPreset(typeKey) {
    state.selectedDiagramType = typeKey;

    dom.presetChips.forEach(chip => {
      if (chip.getAttribute('data-type') === typeKey) {
        chip.classList.add('active');
      } else {
        chip.classList.remove('active');
      }
    });

    const preset = PRESET_TEMPLATES[typeKey];
    if (preset) {
      dom.promptTextarea.value = preset.prompt;
      autoExpandTextarea(dom.promptTextarea);

      if (preset.sampleCode) {
        dom.codeTextarea.value = preset.sampleCode;
        state.currentTikzCode = preset.sampleCode;
        updateLineNumbers();
      }

      // Tự động biên dịch mẫu tức thì để người dùng xem trước
      compileTikzCode(false);
    }
  }

  // Zoom and Pan Viewport
  function updateTransform() {
    if (!dom.previewCanvas) return;
    dom.previewCanvas.style.transform = `translate(${state.pan.x}px, ${state.pan.y}px) scale(${state.zoom})`;
    if (dom.zoomLevelDisplay) {
      dom.zoomLevelDisplay.innerText = `${Math.round(state.zoom * 100)}%`;
    }
  }

  function setZoom(newZoom) {
    state.zoom = Math.max(0.2, Math.min(5.0, newZoom));
    updateTransform();
  }

  function resetZoomAndPan() {
    state.zoom = 1.0;
    state.pan = { x: 0, y: 0 };
    updateTransform();
  }

  function fitToViewport() {
    state.zoom = 0.9;
    state.pan = { x: 0, y: 0 };
    updateTransform();
  }

  function initZoomPanEvents() {
    const viewport = dom.previewViewport;
    if (!viewport) return;

    // Mouse wheel zoom
    viewport.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
      setZoom(state.zoom * zoomFactor);
    }, { passive: false });

    // Drag to Pan
    viewport.addEventListener('mousedown', (e) => {
      if (e.button !== 0) return; // Left mouse only
      state.isDragging = true;
      state.dragStart = { x: e.clientX - state.pan.x, y: e.clientY - state.pan.y };
      viewport.style.cursor = 'grabbing';
    });

    window.addEventListener('mousemove', (e) => {
      if (!state.isDragging) return;
      state.pan.x = e.clientX - state.dragStart.x;
      state.pan.y = e.clientY - state.dragStart.y;
      updateTransform();
    });

    window.addEventListener('mouseup', () => {
      if (state.isDragging) {
        state.isDragging = false;
        if (dom.previewViewport) dom.previewViewport.style.cursor = 'grab';
      }
    });
  }

  // Tab switching
  function switchTab(tabName) {
    if (tabName === 'editor') {
      dom.tabEditorBtn.classList.add('active');
      dom.tabPreviewBtn.classList.remove('active');
      dom.tabEditorContent.classList.add('active');
      dom.tabPreviewContent.classList.remove('active');
      updateLineNumbers();
    } else {
      dom.tabEditorBtn.classList.remove('active');
      dom.tabPreviewBtn.classList.add('active');
      dom.tabEditorContent.classList.remove('active');
      dom.tabPreviewContent.classList.add('active');
      updateTransform();
    }
  }

  // Multi-Feature Nav Switching (All 5 modules)
  function switchMainTab(tabKey) {
    const allNavBtns = [
      dom.navBtnTikz, 
      dom.navBtnAuthoring,
      dom.navBtnConvert,
      dom.navBtnQuestionBank, 
      dom.navBtnMatrix, 
      dom.navBtnNormalize
    ];
    const allPanels = [
      dom.panelTikz, 
      dom.panelAuthoring,
      dom.panelConvert,
      dom.panelQuestionBank, 
      dom.panelMatrix, 
      dom.panelNormalize
    ];

    allNavBtns.forEach(btn => btn && btn.classList.remove('active'));
    allPanels.forEach(p => p && (p.style.display = 'none'));

    // Đóng dropdown menu nếu đang mở
    if (dom.moduleSwitchWrapper) {
      dom.moduleSwitchWrapper.classList.remove('open');
    }

    if (tabKey === 'ai-authoring' || tabKey === 'ai-explain') {
      state.activeMainTab = 'ai-authoring';
      if (dom.navBtnAuthoring) dom.navBtnAuthoring.classList.add('active');
      if (dom.panelAuthoring) dom.panelAuthoring.style.display = 'block';
      if (dom.focusedModuleIcon) dom.focusedModuleIcon.innerText = '✨';
      if (dom.focusedModuleTitle) dom.focusedModuleTitle.innerText = 'Soạn thảo & Giải bài AI';
      if (dom.focusedModuleSubtitle) dom.focusedModuleSubtitle.innerText = 'Phân tích câu hỏi & Sinh lời giải chi tiết';
      reloadSelectionFromWord(false);
    } else if (tabKey === 'convert') {
      state.activeMainTab = 'convert';
      if (dom.navBtnConvert) dom.navBtnConvert.classList.add('active');
      if (dom.panelConvert) dom.panelConvert.style.display = 'block';
      if (dom.focusedModuleIcon) dom.focusedModuleIcon.innerText = '🔄';
      if (dom.focusedModuleTitle) dom.focusedModuleTitle.innerText = 'Convert Đề thi AI';
      if (dom.focusedModuleSubtitle) dom.focusedModuleSubtitle.innerText = 'Ảnh, clipboard → Soạn đề Word';
    } else if (tabKey === 'question-bank') {
      state.activeMainTab = 'question-bank';
      if (dom.navBtnQuestionBank) dom.navBtnQuestionBank.classList.add('active');
      if (dom.panelQuestionBank) dom.panelQuestionBank.style.display = 'block';
      if (dom.focusedModuleIcon) dom.focusedModuleIcon.innerText = '🗃️';
      if (dom.focusedModuleTitle) dom.focusedModuleTitle.innerText = 'Ngân hàng câu hỏi';
      if (dom.focusedModuleSubtitle) dom.focusedModuleSubtitle.innerText = 'Tra cứu, lưu từ Word & Chèn câu hỏi';
      searchQuestionBank();
    } else if (tabKey === 'exam-matrix') {
      if (dom.navBtnMatrix) dom.navBtnMatrix.classList.add('active');
      if (dom.panelMatrix) dom.panelMatrix.style.display = 'block';
      if (dom.focusedModuleIcon) dom.focusedModuleIcon.innerText = '📊';
      if (dom.focusedModuleTitle) dom.focusedModuleTitle.innerText = 'Ma trận & Trộn đề thi';
      if (dom.focusedModuleSubtitle) dom.focusedModuleSubtitle.innerText = 'Cấu trúc đề chuẩn BGD 3 phần';
    } else if (tabKey === 'normalize' || tabKey === 'standardize') {
      if (dom.navBtnNormalize) dom.navBtnNormalize.classList.add('active');
      if (dom.panelNormalize) dom.panelNormalize.style.display = 'block';
      if (dom.focusedModuleIcon) dom.focusedModuleIcon.innerText = '📑';
      if (dom.focusedModuleTitle) dom.focusedModuleTitle.innerText = 'Chuẩn hóa định dạng Word';
      if (dom.focusedModuleSubtitle) dom.focusedModuleSubtitle.innerText = 'Font, cỡ chữ & giãn dòng chuẩn Bộ GD&ĐT';
    } else {
      // Default: TikZ
      if (dom.navBtnTikz) dom.navBtnTikz.classList.add('active');
      if (dom.panelTikz) dom.panelTikz.style.display = 'block';
      if (dom.focusedModuleIcon) dom.focusedModuleIcon.innerText = '📐';
      if (dom.focusedModuleTitle) dom.focusedModuleTitle.innerText = 'Vẽ hình TikZ AI';
      if (dom.focusedModuleSubtitle) dom.focusedModuleSubtitle.innerText = 'Biên dịch LaTeX & Chèn Word 2 chiều';
    }
  }

  // Phase 3: Question Bank Functions
  async function searchQuestionBank() {
    const keyword = dom.qbSearchInput ? dom.qbSearchInput.value.trim() : '';
    const grade = dom.qbFilterGrade && dom.qbFilterGrade.value ? parseInt(dom.qbFilterGrade.value, 10) : null;
    const level = dom.qbFilterLevel ? dom.qbFilterLevel.value : null;
    const qtype = dom.qbFilterType ? dom.qbFilterType.value : null;

    showToast('🔍 Đang tra cứu ngân hàng câu hỏi SQLite...', 'info', 1500);

    try {
      const payload = {
        keyword: keyword || null,
        grade: grade,
        level: level || null,
        questionType: qtype || null,
        limit: 50
      };

      const res = await window.WordBridge.request('questionBank/search', payload);
      if (res && res.success && Array.isArray(res.questions)) {
        renderQuestionCards(res.questions);
        if (dom.qbCountBadge) dom.qbCountBadge.innerText = `${res.questions.length} câu`;
      } else {
        renderQuestionCards([]);
        if (dom.qbCountBadge) dom.qbCountBadge.innerText = `0 câu`;
      }
    } catch (err) {
      console.error('[SidebarApp] QuestionBank search error:', err);
      showToast('Lỗi tra cứu ngân hàng: ' + (err.message || err), 'error');
    }
  }

  function renderQuestionCards(questions) {
    if (!dom.qbQuestionsList) return;
    dom.qbQuestionsList.innerHTML = '';

    if (!questions || questions.length === 0) {
      dom.qbQuestionsList.innerHTML = `
        <div class="preview-empty-state">
          <span class="empty-icon">🗃️</span>
          <span>Không tìm thấy câu hỏi phù hợp</span>
          <span style="font-size: 11px;">Thử thay đổi bộ lọc hoặc lưu câu hỏi mới từ Word</span>
        </div>`;
      return;
    }

    questions.forEach(q => {
      const card = document.createElement('div');
      card.className = 'qb-card';

      let optionsHtml = '';
      if (q.options && typeof q.options === 'object') {
        const optEntries = Object.entries(q.options);
        if (optEntries.length > 0) {
          optionsHtml = `<div style="font-size: 11.5px; color: #94a3b8; margin-top: 4px; display: grid; grid-template-columns: 1fr 1fr; gap: 4px;">
            ${optEntries.map(([k, v]) => `<div><strong>${k}.</strong> ${escapeHtml(v)}</div>`).join('')}
          </div>`;
        }
      }

      card.innerHTML = `
        <div class="qb-card-header">
          <div class="qb-card-meta">
            <span class="qb-badge-code">${escapeHtml(q.questionCode || ('#ID' + q.id))}</span>
            <span class="badge-tag">${escapeHtml(q.cognitiveLevel || 'Thông hiểu')}</span>
            <span class="badge-tag" style="background: rgba(14, 165, 233, 0.15); color: #38bdf8;">Lớp ${q.grade || 12}</span>
          </div>
          <button class="icon-btn qb-btn-delete" title="Xóa câu hỏi khỏi ngân hàng" style="width: 22px; height: 22px; color: #ef4444;">&times;</button>
        </div>
        <div class="qb-card-content">${escapeHtml(q.content || '')}</div>
        ${optionsHtml}
        ${q.correctAnswer ? `<div style="font-size: 11px; color: #10b981; font-weight: 600;">Đáp án: ${escapeHtml(q.correctAnswer)}</div>` : ''}
        <div class="qb-card-footer">
          <span style="font-size: 10.5px; color: #64748b;">${escapeHtml(q.topic || 'Chung')}</span>
          <button class="btn btn-primary btn-compact qb-btn-insert" style="font-size: 11px; padding: 4px 8px;">
            <span>📥</span> Chèn vào Word
          </button>
        </div>
      `;

      // Wire Insert to Word
      const btnInsert = card.querySelector('.qb-btn-insert');
      if (btnInsert) {
        btnInsert.addEventListener('click', async () => {
          let textToInsert = q.content || '';
          if (q.options && typeof q.options === 'object') {
            const opts = Object.entries(q.options).map(([k, v]) => `${k}. ${v}`).join('\n');
            if (opts) textToInsert += '\n' + opts;
          }
          if (q.correctAnswer) textToInsert += `\nLời giải: Đáp án ${q.correctAnswer}`;

          try {
            const insRes = await window.WordBridge.request('word/insertTextAfterSelection', { text: textToInsert });
            if (insRes && insRes.success) {
              showToast('✓ Đã chèn câu hỏi vào Word thành công!', 'success', 2500);
            }
          } catch (e) {
            showToast('Lỗi chèn câu hỏi: ' + e.message, 'error');
          }
        });
      }

      // Wire Delete
      const btnDel = card.querySelector('.qb-btn-delete');
      if (btnDel) {
        btnDel.addEventListener('click', async () => {
          if (confirm(`Bạn có chắc chắn muốn xóa câu hỏi ${q.questionCode || ('#ID' + q.id)} khỏi ngân hàng?`)) {
            try {
              const delRes = await window.WordBridge.request('questionBank/delete', { id: q.id });
              if (delRes && delRes.success) {
                showToast('Đã xóa câu hỏi khỏi ngân hàng!', 'success', 2000);
                searchQuestionBank();
              } else {
                showToast('Không thể xóa câu hỏi.', 'error');
              }
            } catch (e) {
              showToast('Lỗi xóa câu hỏi: ' + e.message, 'error');
            }
          }
        });
      }

      dom.qbQuestionsList.appendChild(card);
    });
  }

  async function saveSelectionToQuestionBank() {
    try {
      const res = await window.WordBridge.request('word/getSelectionText');
      const text = (res && res.text) ? res.text.trim() : '';
      if (!text) {
        showToast('Vui lòng bôi đen câu hỏi trong Word trước khi lưu vào kho.', 'warning', 3500);
        return;
      }

      const gradeVal = dom.qbFilterGrade && dom.qbFilterGrade.value ? parseInt(dom.qbFilterGrade.value, 10) : 12;
      const levelVal = dom.qbFilterLevel && dom.qbFilterLevel.value ? dom.qbFilterLevel.value : 'Thông hiểu';
      const typeVal = dom.qbFilterType && dom.qbFilterType.value ? dom.qbFilterType.value : 'MultipleChoice4';

      const payload = {
        questionCode: 'WORD_' + Date.now().toString(36).toUpperCase(),
        subject: 'Toán',
        grade: gradeVal,
        topic: 'Đại số & Giải tích',
        cognitiveLevel: levelVal,
        questionType: typeVal,
        content: text
      };

      const insRes = await window.WordBridge.request('questionBank/insert', payload);
      if (insRes && insRes.success) {
        showToast('🎉 Đã lưu câu hỏi từ Word vào ngân hàng SQLite thành công!', 'success', 3500);
        searchQuestionBank();
      } else {
        showToast('Không thể lưu câu hỏi vào ngân hàng.', 'error');
      }
    } catch (e) {
      showToast('Lỗi lưu câu hỏi: ' + e.message, 'error');
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Phase 4: Exam Matrix Functions
  let currentGeneratedExamText = '';

  async function generateExamFromMatrix() {
    const title = dom.matrixTitleInput ? dom.matrixTitleInput.value.trim() : 'ĐỀ KIỂM TRA TOÁN';
    const grade = dom.matrixGradeSelect ? parseInt(dom.matrixGradeSelect.value, 10) : 12;
    const p1 = dom.matrixP1Count ? parseInt(dom.matrixP1Count.value, 10) : 12;
    const p2 = dom.matrixP2Count ? parseInt(dom.matrixP2Count.value, 10) : 4;
    const p3 = dom.matrixP3Count ? parseInt(dom.matrixP3Count.value, 10) : 6;

    showToast('⚙️ Đang bốc đề ngẫu nhiên theo ma trận từ ngân hàng câu hỏi...', 'info', 0);

    try {
      const payload = {
        title: title,
        grade: grade,
        part1Count: p1,
        part2Count: p2,
        part3Count: p3
      };

      const res = await window.WordBridge.request('examMatrix/generate', payload);

      if (res && res.success) {
        let fullText = `${res.title || title}\nKhối: Lớp ${grade} | Thời gian: 90 phút\n\n`;
        
        fullText += `--- PHẦN I: CÂU TRẮC NGHIỆM NHIỀU PHƯƠNG ÁN LỰA CHỌN (${(res.part1 || []).length} câu) ---\n`;
        (res.part1 || []).forEach((q, idx) => {
          fullText += `Câu ${idx + 1}: ${q.content || ''}\n`;
          if (q.options) {
            Object.entries(q.options).forEach(([k, v]) => { fullText += `  ${k}. ${v}\n`; });
          }
          fullText += '\n';
        });

        fullText += `--- PHẦN II: CÂU TRẮC NGHIỆM ĐÚNG SAI (${(res.part2 || []).length} câu) ---\n`;
        (res.part2 || []).forEach((q, idx) => {
          fullText += `Câu ${idx + 1}: ${q.content || ''}\n`;
          if (q.options) {
            Object.entries(q.options).forEach(([k, v]) => { fullText += `  ${k}) ${v}\n`; });
          }
          fullText += '\n';
        });

        fullText += `--- PHẦN III: CÂU HỎI TRẢ LỜI NGẮN (${(res.part3 || []).length} câu) ---\n`;
        (res.part3 || []).forEach((q, idx) => {
          fullText += `Câu ${idx + 1}: ${q.content || ''}\n\n`;
        });

        currentGeneratedExamText = fullText;

        if (dom.matrixResultSection) dom.matrixResultSection.style.display = 'block';
        if (dom.matrixResultBadge) dom.matrixResultBadge.innerText = `${res.totalQuestions || 0} câu`;
        if (dom.matrixResultContent) dom.matrixResultContent.innerText = fullText;

        showToast(`🎉 Đã trộn đề thành công (${res.totalQuestions || 0} câu)!`, 'success', 3500);
      } else {
        const err = (res && res.errorMessage) || 'Không thể sinh đề từ ma trận.';
        showToast(err, 'error', 4500);
      }
    } catch (err) {
      showToast('Lỗi trộn đề: ' + err.message, 'error');
    }
  }

  async function exportExamToWord() {
    if (!currentGeneratedExamText) {
      showToast('Chưa có đề thi nào được tạo.', 'warning');
      return;
    }

    try {
      const res = await window.WordBridge.request('word/insertTextAfterSelection', { text: currentGeneratedExamText });
      if (res && res.success) {
        showToast('🎉 Đã xuất toàn bộ đề thi ra Microsoft Word thành công!', 'success', 4000);
      } else {
        showToast('Không thể xuất đề thi vào Word.', 'error');
      }
    } catch (e) {
      showToast('Lỗi xuất đề: ' + e.message, 'error');
    }
  }

  // Phase 5: Normalization & OMML Functions
  async function standardizeFormatting(entireDoc = false) {
    const fontName = dom.normFontName ? dom.normFontName.value : 'Times New Roman';
    const fontSize = dom.normFontSize ? parseFloat(dom.normFontSize.value) : 12;
    const lineSpacing = dom.normLineSpacing ? parseFloat(dom.normLineSpacing.value) : 1.15;

    showToast(`Đang chuẩn hóa định dạng (${fontName}, ${fontSize}pt, ${lineSpacing} lines)...`, 'info', 0);

    try {
      const res = await window.WordBridge.request('word/standardizeDocument', {
        fontName,
        fontSize,
        lineSpacing,
        entireDocument: entireDoc
      });

      if (res && res.success) {
        showToast(`✓ Đã chuẩn hóa định dạng ${entireDoc ? 'toàn bộ tài liệu' : 'vùng chọn'} thành công!`, 'success', 3500);
      } else {
        showToast('Không thể chuẩn hóa định dạng Word.', 'error');
      }
    } catch (e) {
      showToast('Lỗi chuẩn hóa: ' + e.message, 'error');
    }
  }

  // =========================================================================
  // Phân hệ Convert Đề thi AI (Vision OCR -> Trắc nghiệm, Đúng/Sai, TLN, TL)
  // Giữ nguyên 100% công thức toán học dưới dạng LaTeX $ ... $
  // =========================================================================

  function handleConvertFilePicker() {
    if (dom.convertFileInput) {
      dom.convertFileInput.click();
    }
  }

  function handleConvertFileChange(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (event) {
      const dataUrl = event.target.result;
      const base64Data = dataUrl.split(',')[1];
      const mimeType = file.type || 'image/png';
      const sizeKb = Math.round(file.size / 1024);

      setConvertImage(base64Data, mimeType, sizeKb, dataUrl);
    };
    reader.readAsDataURL(file);
  }

  function setConvertImage(base64, mimeType, sizeKb, dataUrl) {
    state.convertImageBase64 = base64;
    state.convertImageMimeType = mimeType;

    if (dom.convertImagePreviewContainer) {
      dom.convertImagePreviewContainer.style.display = 'block';
    }
    if (dom.convertImageThumb) {
      dom.convertImageThumb.src = dataUrl;
    }
    if (dom.convertImageMeta) {
      dom.convertImageMeta.innerText = `Ảnh đã nạp (${sizeKb} KB • ${mimeType})`;
    }

    showToast(`Đã nạp ảnh đề thi (${sizeKb} KB). Nhấn "Nhận diện & Trích xuất câu hỏi" để tiếp tục!`, 'success', 3500);
  }

  function clearConvertImage() {
    state.convertImageBase64 = null;
    state.convertImageMimeType = 'image/png';

    if (dom.convertImagePreviewContainer) {
      dom.convertImagePreviewContainer.style.display = 'none';
    }
    if (dom.convertImageThumb) {
      dom.convertImageThumb.src = '';
    }
    if (dom.convertFileInput) {
      dom.convertFileInput.value = '';
    }

    showToast('Đã xóa ảnh đề thi.', 'info', 2000);
  }

  async function pasteImageFromClipboardManually() {
    showToast('Đang đọc từ Clipboard Windows...', 'info', 1000);

    // Cách 1: Gọi trực tiếp Native Bridge C# (chính xác 100%, không phụ thuộc quyền web)
    try {
      const res = await window.WordBridge.request('clipboard/getImage');
      if (res && res.success && res.hasImage && res.imageBase64) {
        const mimeType = res.mimeType || 'image/png';
        const dataUrl = `data:${mimeType};base64,${res.imageBase64}`;
        const sizeKb = res.sizeKb || Math.round(res.imageBase64.length * 0.75 / 1024);
        switchConvertSubtab('image');
        setConvertImage(res.imageBase64, mimeType, sizeKb, dataUrl);
        showToast(`✓ Đã dán ảnh đề thi từ Clipboard thành công (${sizeKb} KB)!`, 'success', 3500);
        return;
      } else if (res && res.hasText && !res.hasImage) {
        if (dom.convertRawText && res.text && res.text.trim()) {
          dom.convertRawText.value = res.text.trim();
          switchConvertSubtab('text');
          showToast('✓ Clipboard có văn bản: Đã dán vào ô nhập câu hỏi Text/LaTeX!', 'success', 3500);
          return;
        }
        showToast('Clipboard hiện có văn bản rỗng.', 'warning', 3000);
        return;
      } else if (res && !res.success && res.message) {
        showToast(res.message, 'warning', 4000);
        return;
      }
    } catch (bridgeErr) {
      console.warn('Native clipboard bridge failed, trying browser clipboard:', bridgeErr);
    }

    // Cách 2: Fallback browser navigator.clipboard.read / readText
    try {
      if (navigator.clipboard && navigator.clipboard.read) {
        const items = await navigator.clipboard.read();
        for (const item of items) {
          const imageType = item.types.find(t => t.startsWith('image/'));
          if (imageType) {
            const blob = await item.getType(imageType);
            const reader = new FileReader();
            reader.onload = function (event) {
              const dataUrl = event.target.result;
              const base64Data = dataUrl.split(',')[1];
              const sizeKb = Math.round(blob.size / 1024);
              switchConvertSubtab('image');
              setConvertImage(base64Data, imageType, sizeKb, dataUrl);
              showToast(`✓ Đã dán ảnh đề thi từ Clipboard thành công (${sizeKb} KB)!`, 'success', 3500);
            };
            reader.readAsDataURL(blob);
            return;
          }
        }
      }

      // Check text fallback
      if (navigator.clipboard && navigator.clipboard.readText) {
        const clipText = await navigator.clipboard.readText();
        if (clipText && clipText.trim()) {
          if (dom.convertRawText) {
            dom.convertRawText.value = clipText.trim();
            switchConvertSubtab('text');
            showToast('✓ Đã dán văn bản từ Clipboard vào ô Text/LaTeX!', 'success', 3500);
            return;
          }
        }
      }

      showToast('Clipboard hiện không có ảnh hoặc văn bản đề thi.', 'warning', 4000);
    } catch (err) {
      console.warn('Clipboard read error:', err);
      showToast('Không đọc được Clipboard. Hãy dùng Ctrl+V trực tiếp vào ô nhập!', 'warning', 4000);
    }
  }

  async function pasteTikzImageFromNativeClipboard() {
    try {
      const res = await window.WordBridge.request('clipboard/getImage');
      if (res && res.success && res.hasImage && res.imageBase64) {
        const mimeType = res.mimeType || 'image/png';
        const dataUrl = `data:${mimeType};base64,${res.imageBase64}`;
        const sizeKb = res.sizeKb || Math.round(res.imageBase64.length * 0.75 / 1024);

        state.pastedImageBase64 = res.imageBase64;
        state.pastedImageMimeType = mimeType;
        state.pastedImageSizeKB = sizeKb;

        if (dom.imageThumb) dom.imageThumb.src = dataUrl;
        if (dom.imageMetaDetails) {
          dom.imageMetaDetails.innerText = `${mimeType} • ${sizeKb} KB • Ảnh từ Clipboard`;
        }
        if (dom.imagePreviewContainer) {
          dom.imagePreviewContainer.classList.add('active');
        }

        showToast('✓ Đã dán ảnh từ Clipboard vào TikZ thành công!', 'success', 3500);
        return true;
      }
    } catch (e) {
      console.warn('pasteTikzImageFromNativeClipboard error:', e);
    }
    return false;
  }

  async function executeConvertImage() {
    if (!state.convertImageBase64) {
      showToast('Vui lòng nạp ảnh chụp đề thi trước (bằng Ctrl+V hoặc Chọn file ảnh)!', 'warning', 3500);
      return;
    }

    if (state.isConverting) return;
    state.isConverting = true;

    if (dom.btnConvertRun) {
      dom.btnConvertRun.disabled = true;
      dom.btnConvertRun.innerHTML = '<span class="spinner"></span> Đang nhận diện AI Vision...';
    }

    showToast('Đang gọi AI Vision nhận diện đề thi Toán và trích xuất LaTeX...', 'info', 0);

    try {
      const payload = {
        imageBase64: state.convertImageBase64,
        mimeType: state.convertImageMimeType || 'image/png',
        questionTypeHint: dom.convertQtypeSelect ? dom.convertQtypeSelect.value : 'auto',
        includeSolution: dom.convertIncludeSolution ? dom.convertIncludeSolution.checked : true
      };

      const res = await window.WordBridge.request('convert/extract', payload);

      if (res && res.success) {
        state.convertExtractedQuestions = res.questions || [];
        state.convertFormattedText = res.formattedDocText || res.rawOutput || '';

        // Đính kèm ảnh đề thi vào câu hỏi đầu tiên nếu chưa có ảnh
        if (state.convertExtractedQuestions.length > 0 && state.convertSelectedImageBase64) {
          const firstQ = state.convertExtractedQuestions[0];
          firstQ.images = firstQ.images || [];
          if (firstQ.images.length === 0) {
            firstQ.images.push(state.convertSelectedImageBase64);
          }
        }

        showToast('🚀 Đang chèn đề thi chuẩn hóa kèm hình ảnh vào Word...', 'info', 0);
        const resWord = await window.WordBridge.request('word/insertTextAfterSelection', {
          questions: state.convertExtractedQuestions,
          text: state.convertFormattedText
        });

        if (resWord && resWord.success) {
          showToast(`🎉 Nhận diện thành công ${state.convertExtractedQuestions.length} câu hỏi và đã xuất vào Word chuẩn hóa!`, 'success', 4500);
        } else {
          showToast(`Đã nhận diện xong ${state.convertExtractedQuestions.length} câu hỏi.`, 'info', 3000);
        }
      } else {
        throw new Error(res?.errorMessage || 'Không thể nhận diện nội dung từ ảnh đề thi.');
      }
    } catch (err) {
      console.error('[SidebarApp] executeConvertImage error:', err);
      showToast('Lỗi nhận diện đề thi: ' + (err.message || err), 'error', 6000);
    } finally {
      state.isConverting = false;
      if (dom.btnConvertRun) {
        dom.btnConvertRun.disabled = false;
        dom.btnConvertRun.innerHTML = '<span>⚡</span> Nhận diện & Xuất vào Word';
      }
    }
  }

  async function insertConvertedToWord() {
    const textToInsert = dom.convertResultContent ? dom.convertResultContent.innerText.trim() : state.convertFormattedText;
    if (!textToInsert) {
      showToast('Chưa có nội dung đề thi để chèn vào Word!', 'warning', 2500);
      return;
    }

    showToast('Đang chèn đề thi vào tài liệu Word (giữ nguyên LaTeX)...', 'info', 0);
    try {
      const res = await window.WordBridge.request('word/insertTextAfterSelection', { text: textToInsert });
      if (res && res.success) {
        showToast('✓ Đã chèn đề thi vào Word thành công!', 'success', 3500);
      } else {
        showToast('Không thể chèn văn bản vào Word.', 'error');
      }
    } catch (e) {
      showToast('Lỗi chèn vào Word: ' + e.message, 'error');
    }
  }

  async function saveConvertedQuestionsToBank() {
    if (!state.convertExtractedQuestions || state.convertExtractedQuestions.length === 0) {
      showToast('Không có câu hỏi hợp lệ nào để lưu vào ngân hàng!', 'warning', 2500);
      return;
    }

    showToast(`Đang lưu ${state.convertExtractedQuestions.length} câu hỏi vào Ngân hàng SQLite...`, 'info', 0);
    try {
      const res = await window.WordBridge.request('convert/saveToBank', {
        questions: state.convertExtractedQuestions
      });

      if (res && res.success) {
        showToast(`✓ Đã lưu thành công ${res.savedCount || state.convertExtractedQuestions.length} câu hỏi vào Kho!`, 'success', 3500);
      } else {
        showToast('Không thể lưu câu hỏi vào ngân hàng.', 'error');
      }
    } catch (e) {
      showToast('Lỗi lưu ngân hàng: ' + e.message, 'error');
    }
  }

  function copyConvertedResult() {
    if (!dom.convertResultContent) return;
    const text = dom.convertResultContent.innerText;
    navigator.clipboard.writeText(text).then(() => {
      if (dom.btnConvertCopyResult) {
        dom.btnConvertCopyResult.innerText = '✓ Đã chép!';
        setTimeout(() => {
          dom.btnConvertCopyResult.innerText = '📋 Sao chép';
        }, 2000);
      }
    });
  }

  function clearConvertedResult() {
    if (dom.convertResultContent) dom.convertResultContent.innerText = '';
    if (dom.convertResultSection) dom.convertResultSection.style.display = 'none';
    state.convertExtractedQuestions = [];
    state.convertFormattedText = '';
    showToast('Đã xóa kết quả trích xuất.', 'info', 2000);
  }

  // =========================================================================
  // Phân hệ Convert Chế độ 2: Text/LaTeX -> Câu hỏi Word
  // =========================================================================

  function switchConvertSubtab(subtabKey) {
    if (subtabKey === 'text') {
      if (dom.convertSubtabText) dom.convertSubtabText.classList.add('active');
      if (dom.convertSubtabImg) dom.convertSubtabImg.classList.remove('active');
      if (dom.convertModeText) dom.convertModeText.style.display = 'block';
      if (dom.convertModeImage) dom.convertModeImage.style.display = 'none';
    } else {
      if (dom.convertSubtabImg) dom.convertSubtabImg.classList.add('active');
      if (dom.convertSubtabText) dom.convertSubtabText.classList.remove('active');
      if (dom.convertModeImage) dom.convertModeImage.style.display = 'block';
      if (dom.convertModeText) dom.convertModeText.style.display = 'none';
    }
  }

  async function copyChatbotPrompt() {
    const grade = dom.convertTextGrade ? parseInt(dom.convertTextGrade.value, 10) : 12;
    const subject = dom.convertTextSubject ? dom.convertTextSubject.value : 'Toán';
    showToast('Đang tạo prompt mẫu chuẩn cho Chatbot...', 'info', 1000);

    try {
      const res = await window.WordBridge.request('convert/getPromptTemplate', {
        subject,
        grade,
        topic: ''
      });

      const template = (res && res.template) ? res.template : '';
      if (!template) {
        throw new Error('Không nhận được prompt mẫu từ hệ thống.');
      }

      await navigator.clipboard.writeText(template);

      if (dom.btnConvertCopyPrompt) {
        const origText = dom.btnConvertCopyPrompt.innerHTML;
        dom.btnConvertCopyPrompt.innerHTML = '<span>✓</span> Đã chép Prompt!';
        setTimeout(() => { dom.btnConvertCopyPrompt.innerHTML = origText; }, 2500);
      }
      showToast('🎉 Đã chép Prompt chuẩn hỏi Chatbot vào Clipboard! Hãy dán vào ChatGPT / Gemini.', 'success', 4000);
    } catch (e) {
      console.warn('copyChatbotPrompt error:', e);
      showToast('Lỗi sao chép prompt: ' + e.message, 'error', 3500);
    }
  }

  function handleConvertTextFilePicker() {
    if (dom.convertTextFilePicker) {
      dom.convertTextFilePicker.click();
    }
  }

  function handleConvertTextFileChange(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (event) {
      const text = event.target.result || '';
      if (dom.convertRawText) {
        dom.convertRawText.value = text;
      }
      showToast(`✓ Đã nạp file "${file.name}" (${Math.round(file.size / 1024)} KB) thành công!`, 'success', 3500);
    };
    reader.onerror = function () {
      showToast('Lỗi khi đọc file văn bản.', 'error', 3000);
    };
    reader.readAsText(file, 'utf-8');
  }

  function clearConvertRawText() {
    if (dom.convertRawText) {
      dom.convertRawText.value = '';
    }
    showToast('Đã xóa nội dung nhập.', 'info', 1500);
  }

  async function executeLocalParseText() {
    const rawText = dom.convertRawText ? dom.convertRawText.value.trim() : '';
    if (!rawText) {
      showToast('Vui lòng dán văn bản hoặc tải file TeX/TXT trước khi nhận diện!', 'warning', 3500);
      return;
    }

    const grade = dom.convertTextGrade ? parseInt(dom.convertTextGrade.value, 10) : 12;
    const subject = dom.convertTextSubject ? dom.convertTextSubject.value : 'Toán';

    showToast('⚡ Đang nhận diện câu hỏi bằng Local Parser (không tốn API)...', 'info', 0);
    if (dom.btnConvertParseLocal) {
      dom.btnConvertParseLocal.disabled = true;
      dom.btnConvertParseLocal.innerHTML = '<span class="spinner"></span> Đang nhận diện...';
    }

    try {
      const res = await window.WordBridge.request('convert/parseText', {
        rawText,
        subject,
        grade
      });

      if (res && res.success) {
        state.convertExtractedQuestions = res.questions || [];
        state.convertFormattedText = res.formattedDocText || '';

        if (dom.convertResultSection) {
          dom.convertResultSection.style.display = 'block';
        }
        if (dom.convertResultBadge) {
          dom.convertResultBadge.innerText = `${state.convertExtractedQuestions.length} câu`;
        }
        if (dom.convertMetaSummary) {
          dom.convertMetaSummary.innerText = `${res.subject || subject} • Lớp ${res.grade || grade} (Local Parser)`;
        }
        if (dom.convertResultContent) {
          dom.convertResultContent.innerText = state.convertFormattedText;
        }

        if (state.convertExtractedQuestions.length > 0) {
          showToast(`🎉 Nhận diện thành công ${state.convertExtractedQuestions.length} câu hỏi (Giữ nguyên LaTeX, không tốn API)!`, 'success', 4000);
        } else {
          showToast('Không tách được câu hỏi theo cấu trúc chuẩn. Bạn có thể bấm "🤖 Gọi AI ngay" để AI tự động chuẩn hóa!', 'warning', 5000);
        }
      } else {
        throw new Error(res?.errorMessage || 'Lỗi khi nhận diện văn bản.');
      }
    } catch (err) {
      console.error('[SidebarApp] executeLocalParseText error:', err);
      showToast('Lỗi nhận diện văn bản: ' + (err.message || err), 'error', 5000);
    } finally {
      if (dom.btnConvertParseLocal) {
        dom.btnConvertParseLocal.disabled = false;
        dom.btnConvertParseLocal.innerHTML = '<span>⚡</span> Nhận diện câu hỏi';
      }
    }
  }

  async function executeAiCallForText() {
    const rawText = dom.convertRawText ? dom.convertRawText.value.trim() : '';
    if (!rawText) {
      showToast('Vui lòng dán văn bản thô đề thi trước khi gọi AI!', 'warning', 3500);
      return;
    }

    const grade = dom.convertTextGrade ? parseInt(dom.convertTextGrade.value, 10) : 12;
    const subject = dom.convertTextSubject ? dom.convertTextSubject.value : 'Toán';

    showToast('🤖 Đang gọi AI Gemini chuẩn hóa cấu trúc đề thi và công thức LaTeX...', 'info', 0);
    if (dom.btnConvertTextCallAi) {
      dom.btnConvertTextCallAi.disabled = true;
      dom.btnConvertTextCallAi.innerHTML = '<span class="spinner"></span> AI đang xử lý...';
    }

    try {
      const res = await window.WordBridge.request('convert/extract', {
        rawInputText: rawText,
        qtypeFilter: 'auto',
        includeSolution: true
      });

      if (res && res.success) {
        state.convertExtractedQuestions = res.questions || [];
        state.convertFormattedText = res.formattedDocText || res.rawOutput || '';

        if (dom.convertResultSection) {
          dom.convertResultSection.style.display = 'block';
        }
        if (dom.convertResultBadge) {
          dom.convertResultBadge.innerText = `${state.convertExtractedQuestions.length} câu`;
        }
        if (dom.convertMetaSummary) {
          dom.convertMetaSummary.innerText = `${res.subject || subject} • Lớp ${res.grade || grade} (${res.modelUsed || 'AI'})`;
        }
        if (dom.convertResultContent) {
          dom.convertResultContent.innerText = state.convertFormattedText;
        }

        showToast(`🎉 AI đã chuẩn hóa thành công ${state.convertExtractedQuestions.length} câu hỏi!`, 'success', 4000);
      } else {
        throw new Error(res?.errorMessage || 'Không thể chuẩn hóa văn bản bằng AI.');
      }
    } catch (err) {
      console.error('[SidebarApp] executeAiCallForText error:', err);
      showToast('Lỗi AI chuẩn hóa: ' + (err.message || err), 'error', 6000);
    } finally {
      if (dom.btnConvertTextCallAi) {
        dom.btnConvertTextCallAi.disabled = false;
        dom.btnConvertTextCallAi.innerHTML = '<span>🤖</span> Gọi AI ngay';
      }
    }
  }

  async function insertConvertTextDirectlyToWord() {
    let textToInsert = '';
    if (state.convertFormattedText && state.convertFormattedText.trim()) {
      textToInsert = state.convertFormattedText.trim();
    } else if (dom.convertRawText && dom.convertRawText.value.trim()) {
      const rawText = dom.convertRawText.value.trim();
      const grade = dom.convertTextGrade ? parseInt(dom.convertTextGrade.value, 10) : 12;
      const subject = dom.convertTextSubject ? dom.convertTextSubject.value : 'Toán';
      try {
        const res = await window.WordBridge.request('convert/parseText', { rawText, subject, grade });
        if (res && res.success && res.formattedDocText && res.formattedDocText.trim()) {
          textToInsert = res.formattedDocText.trim();
          state.convertExtractedQuestions = res.questions || [];
          state.convertFormattedText = textToInsert;
        } else {
          textToInsert = rawText;
        }
      } catch (e) {
        textToInsert = rawText;
      }
    }

    if (!textToInsert) {
      showToast('Chưa có nội dung đề thi để chèn vào Word!', 'warning', 2500);
      return;
    }

    showToast('🚀 Đang chuẩn hóa cấu trúc và xuất vào tài liệu Word...', 'info', 0);
    try {
      const questionsToSend = (state.convertExtractedQuestions && state.convertExtractedQuestions.length > 0)
        ? state.convertExtractedQuestions
        : undefined;
      const res = await window.WordBridge.request('word/insertTextAfterSelection', {
        questions: questionsToSend,
        text: textToInsert
      });
      if (res && res.success) {
        showToast('🎉 Đã xuất đề thi chuẩn hóa dạng bảng kèm in đậm vào Word thành công!', 'success', 3500);
      } else {
        showToast('Không thể xuất văn bản vào Word.', 'error');
      }
    } catch (e) {
      showToast('Lỗi xuất vào Word: ' + e.message, 'error');
    }
  }

  function copyConvertRawText() {
    const text = (dom.convertRawText && dom.convertRawText.value.trim())
      || (dom.convertResultContent && dom.convertResultContent.innerText.trim())
      || state.convertFormattedText;
    if (!text) {
      showToast('Chưa có nội dung để sao chép!', 'warning', 2000);
      return;
    }
    navigator.clipboard.writeText(text).then(() => {
      if (dom.btnConvertTextCopy) {
        const orig = dom.btnConvertTextCopy.innerHTML;
        dom.btnConvertTextCopy.innerHTML = '<span>✓</span> Đã chép!';
        setTimeout(() => { dom.btnConvertTextCopy.innerHTML = orig; }, 2000);
      }
      showToast('✓ Đã sao chép nội dung vào Clipboard!', 'success', 2500);
    });
  }

  async function saveConvertTextToBank() {
    if (!state.convertExtractedQuestions || state.convertExtractedQuestions.length === 0) {
      const rawText = dom.convertRawText ? dom.convertRawText.value.trim() : '';
      if (rawText) {
        const grade = dom.convertTextGrade ? parseInt(dom.convertTextGrade.value, 10) : 12;
        const subject = dom.convertTextSubject ? dom.convertTextSubject.value : 'Toán';
        try {
          const res = await window.WordBridge.request('convert/parseText', { rawText, subject, grade });
          if (res && res.success && res.questions && res.questions.length > 0) {
            state.convertExtractedQuestions = res.questions;
            state.convertFormattedText = res.formattedDocText || '';
          }
        } catch (e) { }
      }
    }

    if (!state.convertExtractedQuestions || state.convertExtractedQuestions.length === 0) {
      showToast('Vui lòng bấm "⚡ Nhận diện câu hỏi" trước để tách cấu trúc câu trước khi lưu ngân hàng!', 'warning', 3500);
      return;
    }

    await saveConvertedQuestionsToBank();
  }

  // Reload selected text from Word
  async function reloadSelectionFromWord(notify = true) {
    try {
      const res = await window.WordBridge.request('word/getSelectionText');
      const text = (res && res.text) ? res.text.trim() : '';
      if (dom.authoringSelectedText) {
        dom.authoringSelectedText.value = text;
        updateAuthoringMeta();
      }
      if (notify) {
        if (text) {
          showToast('Đã lấy đoạn văn bản đang bôi đen từ Word!', 'success', 2500);
        } else {
          showToast('Chưa có đoạn văn bản nào được bôi đen trong Word.', 'warning', 3000);
        }
      }
    } catch (e) {
      console.warn('Lỗi lấy vùng chọn:', e);
    }
  }

  // Update text meta (word count, question type)
  function updateAuthoringMeta() {
    if (!dom.authoringSelectedText) return;
    const text = dom.authoringSelectedText.value.trim();
    if (!text) {
      if (dom.authoringMetaCount) dom.authoringMetaCount.innerText = '0 từ • 0 ký tự';
      if (dom.authoringMetaBadge) dom.authoringMetaBadge.innerText = 'Chưa có văn bản';
      return;
    }

    const words = text.split(/\s+/).filter(Boolean).length;
    const chars = text.length;
    if (dom.authoringMetaCount) {
      dom.authoringMetaCount.innerText = `${words} từ • ${chars} ký tự`;
    }

    // Detect format
    if (dom.authoringMetaBadge) {
      if (/[A-D]\.\s*|A\.\s*|B\.\s*|C\.\s*|D\.\s*/i.test(text)) {
        dom.authoringMetaBadge.innerText = 'Trắc nghiệm ABCD';
      } else if (/đúng|sai|mệnh đề/i.test(text)) {
        dom.authoringMetaBadge.innerText = 'Đúng / Sai';
      } else {
        dom.authoringMetaBadge.innerText = 'Tự luận / Đề toán';
      }
    }
  }

  // Execute AI Authoring
  async function executeAiAuthoring(taskType, customPrompt = '') {
    const selectedText = dom.authoringSelectedText ? dom.authoringSelectedText.value.trim() : '';
    if (!selectedText) {
      showToast('Vui lòng bôi đen câu hỏi trong Word hoặc nhập nội dung vào ô trên!', 'warning', 3500);
      dom.authoringSelectedText.focus();
      return;
    }

    let taskTitle = 'Lời giải chi tiết';
    if (taskType === 'authoring') taskTitle = 'Chuẩn hóa câu hỏi';
    else if (taskType === 'rewrite') taskTitle = 'Câu hỏi tương tự';
    else if (taskType === 'solve') taskTitle = 'Viết tiếp câu hỏi';

    showToast(`✨ Gemini 3.8 Flash đang thực hiện "${taskTitle}"...`, 'info', 0);

    try {
      const res = await window.WordBridge.request('ai/assistant', {
        taskType: taskType,
        selectedText: selectedText,
        prompt: customPrompt
      });

      if (res && res.success && res.resultText) {
        if (dom.authoringResultSection) dom.authoringResultSection.style.display = 'block';
        if (dom.authoringTaskTitle) dom.authoringTaskTitle.innerText = taskTitle;
        if (dom.authoringResultContent) dom.authoringResultContent.innerText = res.resultText;
        if (dom.authoringModelUsed) dom.authoringModelUsed.innerText = res.model || 'Gemini 3.8 Flash';

        showToast(`Đã hoàn tất "${taskTitle}" (${res.latencyMs || 0}ms)!`, 'success', 3000);
      } else {
        const err = (res && res.errorMessage) || 'Xử lý AI không thành công.';
        showToast('Lỗi AI: ' + err, 'error', 4000);
      }
    } catch (err) {
      showToast('Lỗi khi gọi AI: ' + err.message, 'error', 4000);
    }
  }

  // Replace text in Word
  async function replaceTextInWord() {
    if (!dom.authoringResultContent) return;
    const text = dom.authoringResultContent.innerText.trim();
    if (!text) {
      showToast('Không có nội dung để thay thế.', 'warning');
      return;
    }

    try {
      const res = await window.WordBridge.request('word/replaceSelectionText', { newText: text });
      if (res && res.success) {
        showToast('✓ Đã thay thế đoạn bôi đen trong Word thành công!', 'success', 3000);
      } else {
        showToast('Không thể thay thế văn bản trong Word.', 'error');
      }
    } catch (e) {
      showToast('Lỗi thay thế: ' + e.message, 'error');
    }
  }

  // Insert text after selection in Word
  async function insertTextAfterSelectionInWord() {
    if (!dom.authoringResultContent) return;
    const text = dom.authoringResultContent.innerText.trim();
    if (!text) {
      showToast('Không có nội dung để chèn.', 'warning');
      return;
    }

    try {
      const res = await window.WordBridge.request('word/insertTextAfterSelection', { text: text });
      if (res && res.success) {
        showToast('✓ Đã chèn lời giải vào bên dưới câu hỏi trong Word!', 'success', 3000);
      } else {
        showToast('Không thể chèn văn bản vào Word.', 'error');
      }
    } catch (e) {
      showToast('Lỗi chèn văn bản: ' + e.message, 'error');
    }
  }

  // Actions
  async function generateTikzFromAi() {
    const prompt = dom.promptTextarea.value.trim();
    if (!prompt && !state.pastedImageBase64) {
      showToast('Vui lòng nhập mô tả hoặc dán ảnh bài toán (Ctrl+V) trước khi tạo hình.', 'warning');
      dom.promptTextarea.focus();
      return;
    }

    state.isGenerating = true;
    updateActionButtons();
    showToast('✨ AI Gemini 3.8 Flash đang phân tích và sinh mã TikZ...', 'info', 0);

    try {
      const options = {
        imageBase64: state.pastedImageBase64,
        imageMimeType: state.pastedImageMimeType,
        diagramType: state.selectedDiagramType
      };

      const result = await window.WordBridge.generateTikz(prompt, options);

      if (result && result.success && result.tikzCode) {
        state.currentTikzCode = result.tikzCode;
        dom.codeTextarea.value = result.tikzCode;
        updateLineNumbers();

        showToast(`Tạo mã TikZ thành công qua ${result.model || 'Gemini 3.8 Flash'} (${result.executionTimeMs || 0}ms)! Đang biên dịch xem trước...`, 'success', 3500);

        // Auto-compile to preview visual image
        await compileTikzCode(true);
      } else {
        const errorMsg = (result && result.errorMessage) || 'Không thể tạo mã TikZ từ AI.';
        showToast(errorMsg, 'error', 6000);
      }
    } catch (err) {
      console.error('[SidebarApp] Generate error:', err);
      showToast('Lỗi sinh mã TikZ: ' + (err.message || err), 'error', 6000);
    } finally {
      state.isGenerating = false;
      updateActionButtons();
    }
  }

  async function compileTikzCode(silentToast = false) {
    const code = dom.codeTextarea.value.trim();
    if (!code) {
      showToast('Mã TikZ rỗng, không thể biên dịch.', 'warning');
      return;
    }

    state.isCompiling = true;
    updateActionButtons();
    if (!silentToast) {
      showToast('⚙️ Đang biên dịch mã TikZ qua TeXLive (pdflatex)...', 'info', 0);
    }

    // Hide error panel
    if (dom.latexErrorPanel) dom.latexErrorPanel.classList.remove('active');

    try {
      const result = await window.WordBridge.compileTikz(code, state.compiledFormat, {
        border: '2pt',
        autoHeal: true
      });

      if (result && result.success) {
        state.compiledImagePath = result.imagePath;
        state.compiledPreviewUrl = result.previewDataUrl;

        // Render preview image
        if (dom.previewImage) {
          dom.previewImage.src = result.previewDataUrl;
          dom.previewImage.style.display = 'block';
        }
        if (dom.previewEmptyState) {
          dom.previewEmptyState.style.display = 'none';
        }

        // Switch to preview tab
        switchTab('preview');
        resetZoomAndPan();

        showToast(`Biên dịch thành công (${result.compilationTimeMs || 0}ms)!`, 'success', 3000);
      } else {
        const errorMsg = (result && result.errorMessage) || 'Biên dịch pdflatex thất bại.';
        showToast(errorMsg, 'error', 6000);

        if (dom.latexErrorPanel && result && result.rawLog) {
          dom.latexErrorPanel.classList.add('active');
          dom.latexErrorContent.textContent = result.parsedError 
            ? `${result.parsedError}\n\n${result.rawLog}`
            : result.rawLog;
        }
      }
    } catch (err) {
      console.error('[SidebarApp] Compile error:', err);
      showToast('Lỗi biên dịch TeXLive: ' + (err.message || err), 'error', 6000);
    } finally {
      state.isCompiling = false;
      updateActionButtons();
    }
  }

  async function insertIntoWord() {
    const code = dom.codeTextarea.value.trim();
    if (!code) {
      showToast('Vui lòng tạo hoặc nhập mã TikZ trước khi chèn vào Word.', 'warning');
      return;
    }

    state.isInserting = true;
    updateActionButtons();
    showToast('📥 Đang chèn hình ảnh vào vị trí con trỏ chuột trong Word...', 'info', 0);

    try {
      // Ensure image is compiled first
      let imagePath = state.compiledImagePath;
      if (!imagePath || !state.compiledPreviewUrl) {
        const compRes = await window.WordBridge.compileTikz(code, 'png');
        if (!compRes || !compRes.success || !compRes.imagePath) {
          throw new Error('Biên dịch hình ảnh thất bại: ' + (compRes?.errorMessage || 'Không tạo được file ảnh'));
        }
        imagePath = compRes.imagePath;
        state.compiledImagePath = imagePath;
      }

      const result = await window.WordBridge.insertPicture(imagePath, code);

      if (result && result.success) {
        showToast('🎉 Đã chèn hình ảnh và lưu mã TikZ hai chiều vào Word thành công!', 'success', 4000);
      } else {
        throw new Error('Word không phản hồi thành công khi chèn ảnh.');
      }
    } catch (err) {
      console.error('[SidebarApp] Insert error:', err);
      showToast('Lỗi chèn vào Word: ' + (err.message || err), 'error', 6000);
    } finally {
      state.isInserting = false;
      updateActionButtons();
    }
  }

  async function updateSelectedWordPicture() {
    const code = dom.codeTextarea.value.trim();
    if (!code) {
      showToast('Mã TikZ rỗng, không thể cập nhật.', 'warning');
      return;
    }

    state.isInserting = true;
    updateActionButtons();
    showToast('🔄 Đang cập nhật hình ảnh TikZ trong tài liệu Word...', 'info', 0);

    try {
      // Compile new image
      const compRes = await window.WordBridge.compileTikz(code, 'png');
      if (!compRes || !compRes.success || !compRes.imagePath) {
        throw new Error('Biên dịch hình ảnh thất bại: ' + (compRes?.errorMessage || 'Lỗi TeXLive'));
      }

      const result = await window.WordBridge.updateSelectedPicture(compRes.imagePath, code);

      if (result && result.success) {
        showToast('🎉 Đã cập nhật lại hình ảnh trong tài liệu Word thành công!', 'success', 4000);
      } else {
        throw new Error('Không thể cập nhật hình ảnh Word (vui lòng chọn hình ảnh cần sửa trong Word).');
      }
    } catch (err) {
      console.error('[SidebarApp] Update error:', err);
      showToast('Lỗi cập nhật hình Word: ' + (err.message || err), 'error', 6000);
    } finally {
      state.isInserting = false;
      updateActionButtons();
    }
  }

  function updateActionButtons() {
    if (dom.btnGenerateAi) {
      dom.btnGenerateAi.disabled = state.isGenerating || state.isCompiling || state.isInserting;
      dom.btnGenerateAi.innerHTML = state.isGenerating
        ? '<span class="spinner"></span> Đang tạo AI...'
        : '<span class="btn-icon">✨</span> Tạo hình bằng AI';
    }

    if (dom.btnCompileTikz) {
      dom.btnCompileTikz.disabled = state.isGenerating || state.isCompiling || state.isInserting;
      dom.btnCompileTikz.innerHTML = state.isCompiling
        ? '<span class="spinner"></span> Đang biên dịch...'
        : '<span class="btn-icon">⚙️</span> Biên dịch lại';
    }

    if (dom.btnInsertWord) {
      dom.btnInsertWord.disabled = state.isGenerating || state.isCompiling || state.isInserting;
      dom.btnInsertWord.innerHTML = state.isInserting
        ? '<span class="spinner"></span> Đang chèn...'
        : '<span class="btn-icon">📥</span> Chèn vào Word';
    }

    if (dom.btnUpdateWord) {
      const canUpdate = state.hasWordTikzSelected && !state.isGenerating && !state.isCompiling && !state.isInserting;
      dom.btnUpdateWord.disabled = !canUpdate;
    }
  }

  // Setup Event Listeners
  function attachEventListeners() {
    // Prompt Textarea
    dom.promptTextarea.addEventListener('input', () => {
      autoExpandTextarea(dom.promptTextarea);
    });

    dom.clearPromptBtn.addEventListener('click', () => {
      dom.promptTextarea.value = '';
      autoExpandTextarea(dom.promptTextarea);
      dom.promptTextarea.focus();
    });

    // Global & prompt paste for images
    window.addEventListener('paste', handleClipboardPaste);
    dom.promptTextarea.addEventListener('paste', handleClipboardPaste);

    // Global Ctrl+V key shortcut support
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key && e.key.toLowerCase() === 'v') {
        const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
        if (activeTag !== 'textarea' && activeTag !== 'input') {
          e.preventDefault();
          if (state.activeMainTab === 'convert') {
            pasteImageFromClipboardManually();
          } else if (state.activeMainTab === 'tikz') {
            pasteTikzImageFromNativeClipboard();
          }
        }
      }
    });

    // Drag & Drop for prompt card
    setupPromptDragAndDrop();

    // Button: Lấy ảnh từ Word
    if (dom.btnGetWordImage) {
      dom.btnGetWordImage.addEventListener('click', loadWordSelectedImage);
    }

    // Button: Dán ảnh từ Clipboard
    if (dom.btnPasteClipboardImage) {
      dom.btnPasteClipboardImage.addEventListener('click', pasteTikzImageFromNativeClipboard);
    }

    // Remove Image button
    dom.removeImageBtn.addEventListener('click', removePastedImage);

    // Preset Chips
    dom.presetChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const typeKey = chip.getAttribute('data-type');
        selectPreset(typeKey);
      });
    });

    // Code Textarea Input & Indent
    dom.codeTextarea.addEventListener('input', updateLineNumbers);
    dom.codeTextarea.addEventListener('scroll', syncScroll);

    dom.codeTextarea.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        const start = dom.codeTextarea.selectionStart;
        const end = dom.codeTextarea.selectionEnd;
        const val = dom.codeTextarea.value;
        dom.codeTextarea.value = val.substring(0, start) + '  ' + val.substring(end);
        dom.codeTextarea.selectionStart = dom.codeTextarea.selectionEnd = start + 2;
        updateLineNumbers();
      }
    });

    // Copy Code Button
    dom.btnCopyCode.addEventListener('click', () => {
      const code = dom.codeTextarea.value;
      navigator.clipboard.writeText(code).then(() => {
        dom.btnCopyCode.innerText = '✓ Đã chép!';
        setTimeout(() => { dom.btnCopyCode.innerText = 'Sao chép'; }, 2000);
      });
    });

    // Clear Code Button
    dom.btnClearCode.addEventListener('click', () => {
      if (confirm('Bạn có chắc chắn muốn xóa toàn bộ mã nguồn TikZ hiện tại?')) {
        dom.codeTextarea.value = '';
        updateLineNumbers();
      }
    });

    // Tabs
    dom.tabEditorBtn.addEventListener('click', () => switchTab('editor'));
    dom.tabPreviewBtn.addEventListener('click', () => {
      switchTab('preview');
      if (!dom.previewImage.src || dom.previewImage.style.display === 'none') {
        compileTikzCode(false);
      }
    });

    // Module Switcher Dropdown
    if (dom.btnToggleModuleMenu && dom.moduleSwitchWrapper) {
      dom.btnToggleModuleMenu.addEventListener('click', (e) => {
        e.stopPropagation();
        dom.moduleSwitchWrapper.classList.toggle('open');
      });
      document.addEventListener('click', (e) => {
        if (!dom.moduleSwitchWrapper.contains(e.target)) {
          dom.moduleSwitchWrapper.classList.remove('open');
        }
      });
    }

    // Zoom Controls
    dom.btnZoomIn.addEventListener('click', () => setZoom(state.zoom * 1.25));
    dom.btnZoomOut.addEventListener('click', () => setZoom(state.zoom * 0.8));
    dom.btnZoomReset.addEventListener('click', resetZoomAndPan);
    dom.btnZoomFit.addEventListener('click', fitToViewport);

    // Format Selector
    dom.formatBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        dom.formatBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.compiledFormat = btn.getAttribute('data-format');
        compileTikzCode(false);
      });
    });

    // Action Buttons
    dom.btnGenerateAi.addEventListener('click', generateTikzFromAi);
    dom.btnCompileTikz.addEventListener('click', () => compileTikzCode(false));
    dom.btnInsertWord.addEventListener('click', insertIntoWord);
    dom.btnUpdateWord.addEventListener('click', updateSelectedWordPicture);

    // Toast Close
    dom.toastClose.addEventListener('click', hideToast);

    // Settings Modal
    dom.btnOpenSettings.addEventListener('click', openSettingsModal);
    dom.btnCloseSettings.addEventListener('click', closeSettingsModal);
    dom.btnSaveSettings.addEventListener('click', saveSettings);

    // Phase 2 Feature Nav Bar
    if (dom.navBtnTikz) {
      dom.navBtnTikz.addEventListener('click', () => switchMainTab('tikz'));
    }
    if (dom.navBtnAuthoring) {
      dom.navBtnAuthoring.addEventListener('click', () => switchMainTab('ai-authoring'));
    }

    // Phase 2 Authoring Elements
    if (dom.btnReloadSelection) {
      dom.btnReloadSelection.addEventListener('click', () => reloadSelectionFromWord(true));
    }
    if (dom.authoringSelectedText) {
      dom.authoringSelectedText.addEventListener('input', updateAuthoringMeta);
    }
    if (dom.authoringActionTiles) {
      dom.authoringActionTiles.forEach(tile => {
        tile.addEventListener('click', () => {
          const taskType = tile.getAttribute('data-task') || 'explain';
          const prompt = dom.authoringCustomPrompt ? dom.authoringCustomPrompt.value.trim() : '';
          executeAiAuthoring(taskType, prompt);
        });
      });
    }
    if (dom.btnExecuteCustomAi) {
      dom.btnExecuteCustomAi.addEventListener('click', () => {
        const prompt = dom.authoringCustomPrompt ? dom.authoringCustomPrompt.value.trim() : '';
        executeAiAuthoring('authoring', prompt);
      });
    }
    if (dom.btnCopyResult) {
      dom.btnCopyResult.addEventListener('click', () => {
        if (!dom.authoringResultContent) return;
        const text = dom.authoringResultContent.innerText;
        navigator.clipboard.writeText(text).then(() => {
          dom.btnCopyResult.innerText = '✓ Đã chép!';
          setTimeout(() => { dom.btnCopyResult.innerText = '📋 Sao chép'; }, 2000);
        });
      });
    }
    if (dom.btnClearResult) {
      dom.btnClearResult.addEventListener('click', () => {
        if (dom.authoringResultContent) dom.authoringResultContent.innerText = '';
        if (dom.authoringResultSection) dom.authoringResultSection.style.display = 'none';
      });
    }
    if (dom.btnReplaceWordText) {
      dom.btnReplaceWordText.addEventListener('click', replaceTextInWord);
    }
    if (dom.btnInsertWordText) {
      dom.btnInsertWordText.addEventListener('click', insertTextAfterSelectionInWord);
    }

    // Feature Nav Bar (Phases 3, 4, 5)
    if (dom.navBtnQuestionBank) {
      dom.navBtnQuestionBank.addEventListener('click', () => switchMainTab('question-bank'));
    }
    if (dom.navBtnMatrix) {
      dom.navBtnMatrix.addEventListener('click', () => switchMainTab('exam-matrix'));
    }
    if (dom.navBtnNormalize) {
      dom.navBtnNormalize.addEventListener('click', () => switchMainTab('normalize'));
    }

    // Phase 3 Question Bank Elements
    if (dom.qbBtnSearch) {
      dom.qbBtnSearch.addEventListener('click', () => searchQuestionBank());
    }
    if (dom.qbSearchInput) {
      dom.qbSearchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') searchQuestionBank();
      });
    }
    if (dom.qbFilterGrade) dom.qbFilterGrade.addEventListener('change', () => searchQuestionBank());
    if (dom.qbFilterLevel) dom.qbFilterLevel.addEventListener('change', () => searchQuestionBank());
    if (dom.qbFilterType) dom.qbFilterType.addEventListener('change', () => searchQuestionBank());
    if (dom.qbBtnSaveSelection) {
      dom.qbBtnSaveSelection.addEventListener('click', saveSelectionToQuestionBank);
    }
    if (dom.qbBtnRefresh) {
      dom.qbBtnRefresh.addEventListener('click', () => searchQuestionBank());
    }

    // Phase 4 Exam Matrix Elements
    if (dom.matrixBtnGenerate) {
      dom.matrixBtnGenerate.addEventListener('click', generateExamFromMatrix);
    }
    if (dom.matrixBtnExportWord) {
      dom.matrixBtnExportWord.addEventListener('click', exportExamToWord);
    }

    // Phase 5 Normalize & OMML & MathType Elements
    if (dom.btnStandardizeSelection) {
      dom.btnStandardizeSelection.addEventListener('click', () => standardizeFormatting(false));
    }
    if (dom.btnStandardizeDoc) {
      dom.btnStandardizeDoc.addEventListener('click', () => standardizeFormatting(true));
    }

    // Convert Module Elements (Ảnh + Text/LaTeX)
    if (dom.navBtnConvert) {
      dom.navBtnConvert.addEventListener('click', () => switchMainTab('convert'));
    }

    // Subtabs Switcher
    if (dom.convertSubtabImg) {
      dom.convertSubtabImg.addEventListener('click', () => switchConvertSubtab('image'));
    }
    if (dom.convertSubtabText) {
      dom.convertSubtabText.addEventListener('click', () => switchConvertSubtab('text'));
    }

    // Image Mode Handlers
    if (dom.btnConvertPickFile) {
      dom.btnConvertPickFile.addEventListener('click', handleConvertFilePicker);
    }
    if (dom.convertFileInput) {
      dom.convertFileInput.addEventListener('change', handleConvertFileChange);
    }
    if (dom.btnConvertPaste) {
      dom.btnConvertPaste.addEventListener('click', pasteImageFromClipboardManually);
    }
    if (dom.btnConvertClearImage) {
      dom.btnConvertClearImage.addEventListener('click', clearConvertImage);
    }
    if (dom.btnConvertRun) {
      dom.btnConvertRun.addEventListener('click', executeConvertImage);
    }

    // Text/LaTeX Mode Handlers
    if (dom.btnConvertCopyPrompt) {
      dom.btnConvertCopyPrompt.addEventListener('click', copyChatbotPrompt);
    }
    if (dom.btnConvertLoadTextFile) {
      dom.btnConvertLoadTextFile.addEventListener('click', handleConvertTextFilePicker);
    }
    if (dom.convertTextFilePicker) {
      dom.convertTextFilePicker.addEventListener('change', handleConvertTextFileChange);
    }
    if (dom.btnConvertClearText) {
      dom.btnConvertClearText.addEventListener('click', clearConvertRawText);
    }
    if (dom.btnConvertParseLocal) {
      dom.btnConvertParseLocal.addEventListener('click', executeLocalParseText);
    }
    if (dom.btnConvertTextInsertWord) {
      dom.btnConvertTextInsertWord.addEventListener('click', insertConvertTextDirectlyToWord);
    }
    if (dom.btnConvertTextCallAi) {
      dom.btnConvertTextCallAi.addEventListener('click', executeAiCallForText);
    }
    if (dom.btnConvertTextSaveBank) {
      dom.btnConvertTextSaveBank.addEventListener('click', saveConvertTextToBank);
    }
    if (dom.btnConvertTextCopy) {
      dom.btnConvertTextCopy.addEventListener('click', copyConvertRawText);
    }

    // Shared Result Handlers
    if (dom.btnConvertInsertWord) {
      dom.btnConvertInsertWord.addEventListener('click', insertConvertedToWord);
    }
    if (dom.btnConvertSaveQb) {
      dom.btnConvertSaveQb.addEventListener('click', saveConvertedQuestionsToBank);
    }
    if (dom.btnConvertCopyResult) {
      dom.btnConvertCopyResult.addEventListener('click', copyConvertedResult);
    }
    if (dom.btnConvertClearResult) {
      dom.btnConvertClearResult.addEventListener('click', clearConvertedResult);
    }

    // Settings Provider & Connection Listeners
    if (dom.providerSelect) {
      dom.providerSelect.addEventListener('change', handleProviderChange);
    }
    if (dom.btnTestConnection) {
      dom.btnTestConnection.addEventListener('click', testAiConnection);
    }
  }

  // Multi-Provider Models Dictionary (đồng bộ với Desktop App)
  const MODELS_BY_PROVIDER = {
    '9Router': [
      'ag/gemini-3.8-flash-high',
      'ag/gemini-3.8-flash',
      'ag/gemini-3.7-flash-high',
      'ag/gemini-3.6-flash-high',
      'ag/gemini-3.1-pro-low',
      'ag/claude-sonnet-5-5',
      'ag/claude-sonnet-4-6',
      'ag/gpt-oss-120b-medium',
      'gemini-3.8-flash'
    ],
    'Google Gemini': [
      'gemini-3.8-flash',
      'gemini-3.1-pro',
      'gemini-3.8-live',
      'gemini-3.6-flash',
      'gemini-3.5-flash-lite',
      'gemini-2.5-pro',
      'gemini-2.5-flash'
    ],
    'Anthropic Claude': [
      'claude-sonnet-5',
      'claude-sonnet-4-6',
      'claude-sonnet-4-5',
      'claude-opus-5',
      'claude-haiku-4-5'
    ],
    'DeepSeek': [
      'deepseek-chat',
      'deepseek-reasoner',
      'deepseek-v4.1-flash'
    ],
    'OpenAI GPT': [
      'gpt-4o',
      'gpt-4o-mini',
      'gpt-4.5'
    ]
  };

  let cachedConfig = {};

  function populateModelsForProvider(provider, selectedModel) {
    if (!dom.modelSelect) return;
    dom.modelSelect.innerHTML = '';
    const models = MODELS_BY_PROVIDER[provider] || MODELS_BY_PROVIDER['9Router'];
    models.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      if (selectedModel && (m.toLowerCase() === selectedModel.toLowerCase() || m.endsWith(selectedModel))) {
        opt.selected = true;
      }
      dom.modelSelect.appendChild(opt);
    });

    if (dom.apiKeyLabel) {
      dom.apiKeyLabel.textContent = `Khóa API (${provider}):`;
    }
    if (dom.apiKeyInput) {
      dom.apiKeyInput.placeholder = provider === 'Google Gemini' ? 'AIzaSy...' : 'sk-...';
    }
  }

  function handleProviderChange() {
    const prov = dom.providerSelect ? dom.providerSelect.value : '9Router';
    let existingKey = '';
    if (cachedConfig.keysByProvider && cachedConfig.keysByProvider[prov]) {
      existingKey = cachedConfig.keysByProvider[prov];
    } else if (prov === '9Router' && cachedConfig.nineRouterApiKey) {
      existingKey = cachedConfig.nineRouterApiKey;
    } else if (prov === cachedConfig.provider && cachedConfig.apiKey) {
      existingKey = cachedConfig.apiKey;
    }

    populateModelsForProvider(prov);
    if (dom.apiKeyInput) dom.apiKeyInput.value = existingKey;
  }

  // Settings Modal Handlers
  async function openSettingsModal() {
    dom.settingsModal.classList.add('active');
    if (dom.settingsTestStatus) dom.settingsTestStatus.style.display = 'none';

    try {
      const cfg = await window.WordBridge.getConfig();
      cachedConfig = cfg || {};
      const activeProvider = cfg?.provider || '9Router';
      const activeModel = cfg?.model || 'ag/gemini-3.8-flash-high';

      if (dom.providerSelect) {
        dom.providerSelect.value = activeProvider;
      }
      populateModelsForProvider(activeProvider, activeModel);

      let key = '';
      if (cfg?.keysByProvider && typeof cfg.keysByProvider === 'object' && cfg.keysByProvider[activeProvider]) {
        key = cfg.keysByProvider[activeProvider];
      } else if (cfg?.apiKey) {
        key = cfg.apiKey;
      } else if (activeProvider === '9Router' && cfg?.nineRouterApiKey) {
        key = cfg.nineRouterApiKey;
      }
      if (dom.apiKeyInput) dom.apiKeyInput.value = key;
    } catch (e) {
      console.warn('Error loading config:', e);
    }
  }

  function closeSettingsModal() {
    dom.settingsModal.classList.remove('active');
  }

  async function testAiConnection() {
    if (!dom.btnTestConnection) return;
    dom.btnTestConnection.disabled = true;
    dom.btnTestConnection.innerHTML = '<span class="spinner"></span> Đang thử...';
    if (dom.settingsTestStatus) {
      dom.settingsTestStatus.style.display = 'block';
      dom.settingsTestStatus.style.background = 'rgba(56, 189, 248, 0.15)';
      dom.settingsTestStatus.style.color = '#38bdf8';
      dom.settingsTestStatus.textContent = 'Đang gửi truy vấn thử nghiệm đến máy chủ AI...';
    }

    const provider = dom.providerSelect ? dom.providerSelect.value : '9Router';
    const model = dom.modelSelect ? dom.modelSelect.value : '';
    const apiKey = dom.apiKeyInput ? dom.apiKeyInput.value.trim() : '';

    try {
      const res = await window.WordBridge.request('ai/testConnection', { provider, model, apiKey });
      if (res && res.success) {
        if (dom.settingsTestStatus) {
          dom.settingsTestStatus.style.background = 'rgba(16, 185, 129, 0.15)';
          dom.settingsTestStatus.style.color = '#10b981';
          dom.settingsTestStatus.textContent = '✓ ' + (res.message || 'Kết nối AI thành công!');
        }
        showToast('✓ Kết nối AI thành công!', 'success', 2500);
      } else {
        if (dom.settingsTestStatus) {
          dom.settingsTestStatus.style.background = 'rgba(239, 68, 68, 0.15)';
          dom.settingsTestStatus.style.color = '#ef4444';
          dom.settingsTestStatus.textContent = '⚠ ' + (res?.message || 'Kết nối thất bại.');
        }
        showToast('Kết nối thất bại: ' + (res?.message || ''), 'warning', 3500);
      }
    } catch (err) {
      if (dom.settingsTestStatus) {
        dom.settingsTestStatus.style.background = 'rgba(239, 68, 68, 0.15)';
        dom.settingsTestStatus.style.color = '#ef4444';
        dom.settingsTestStatus.textContent = '⚠ Lỗi kiểm tra: ' + err.message;
      }
    } finally {
      dom.btnTestConnection.disabled = false;
      dom.btnTestConnection.innerHTML = '<span>⚡</span> Kiểm tra kết nối';
    }
  }

  async function saveSettings() {
    const provider = dom.providerSelect ? dom.providerSelect.value : '9Router';
    const model = dom.modelSelect ? dom.modelSelect.value : 'ag/gemini-3.8-flash-high';
    const apiKey = dom.apiKeyInput ? dom.apiKeyInput.value.trim() : '';

    const keysByProvider = (cachedConfig.keysByProvider && typeof cachedConfig.keysByProvider === 'object')
      ? { ...cachedConfig.keysByProvider }
      : {};
    keysByProvider[provider] = apiKey;

    const config = {
      ...cachedConfig,
      provider: provider,
      model: model,
      apiKey: apiKey,
      keysByProvider: keysByProvider
    };

    if (provider === '9Router') {
      config.nineRouterApiKey = apiKey;
    } else if (provider === 'OpenAI GPT') {
      config.openAiApiKey = apiKey;
    }

    try {
      await window.WordBridge.saveConfig(config);
      cachedConfig = config;
      showToast(`✓ Đã lưu cài đặt AI: ${provider} (${model})`, 'success');
      closeSettingsModal();
    } catch (err) {
      showToast('Lỗi khi lưu cấu hình: ' + err.message, 'error');
    }
  }

  // Word Push Event Listeners
  function attachBridgeListeners() {
    // 1. Selection change event from Word
    window.WordBridge.on('word/selectionChanged', (data) => {
      console.log('[SidebarApp] Received word/selectionChanged:', data);
      const isSelected = !!(data && (data.hasTikzShape || data.hasSelectedShape));

      state.hasWordTikzSelected = isSelected;
      state.selectedWordShapeTitle = (data && data.shapeTitle) || '';

      if (isSelected) {
        dom.selectionBanner.classList.add('active');
        dom.selectionTitle.innerText = state.selectedWordShapeTitle || 'Hình TikZ đã chọn';

        // Load TikZ code from Word into editor if present
        if (data.tikzCode && data.tikzCode.trim()) {
          state.currentTikzCode = data.tikzCode;
          dom.codeTextarea.value = data.tikzCode;
          updateLineNumbers();
          showToast('Đã nạp mã nguồn TikZ từ hình ảnh trong Word!', 'info', 2500);

          // Auto compile preview
          compileTikzCode(true);
        }
      } else {
        dom.selectionBanner.classList.remove('active');
      }

      updateActionButtons();
    });

    // 2. Auto-healing progress event from C#
    window.WordBridge.on('ai/healingProgress', (data) => {
      console.log('[SidebarApp] Healing progress:', data);
      showToast(`Đang tự sửa lỗi cú pháp TikZ (Lần thử ${data.attempt || 1})...`, 'warning', 0);
    });

    // 3. Tab switch event from Ribbon
    window.WordBridge.on('app/switchTab', (data) => {
      if (data && data.tab) {
        if (data.tab === 'preview') switchTab('preview');
        else if (data.tab === 'editor') switchTab('editor');
        else if (data.tab === 'ai-authoring' || data.tab === 'ai-explain') {
          switchMainTab('ai-authoring');
        } else if (data.tab === 'tikz') {
          switchMainTab('tikz');
        } else if (data.tab === 'convert') {
          switchMainTab('convert');
        } else if (data.tab === 'question-bank') {
          switchMainTab('question-bank');
        } else if (data.tab === 'exam-matrix') {
          switchMainTab('exam-matrix');
        } else if (data.tab === 'standardize' || data.tab === 'latex-omml' || data.tab === 'normalize') {
          switchMainTab('normalize');
        } else if (data.tab === 'settings') {
          openSettingsModal();
        }
      }
    });

    // 4. Ribbon AI events
    window.WordBridge.on('ai/selectionLoaded', (data) => {
      if (data && data.selectedText && dom.authoringSelectedText) {
        dom.authoringSelectedText.value = data.selectedText;
        updateAuthoringMeta();
      }
    });

    window.WordBridge.on('ai/authoringResult', (data) => {
      if (data && data.resultText) {
        switchMainTab('ai-authoring');
        if (dom.authoringResultSection) dom.authoringResultSection.style.display = 'block';
        if (dom.authoringTaskTitle) dom.authoringTaskTitle.innerText = 'Chuẩn hóa câu hỏi';
        if (dom.authoringResultContent) dom.authoringResultContent.innerText = data.resultText;
        if (dom.authoringModelUsed) dom.authoringModelUsed.innerText = data.model || 'Gemini 3.8 Flash';
        showToast('Đã nhận kết quả soạn thảo từ Ribbon!', 'success', 3000);
      }
    });

    window.WordBridge.on('ai/explainResult', (data) => {
      if (data && data.resultText) {
        switchMainTab('ai-authoring');
        if (dom.authoringResultSection) dom.authoringResultSection.style.display = 'block';
        if (dom.authoringTaskTitle) dom.authoringTaskTitle.innerText = 'Lời giải chi tiết';
        if (dom.authoringResultContent) dom.authoringResultContent.innerText = data.resultText;
        if (dom.authoringModelUsed) dom.authoringModelUsed.innerText = data.model || 'Gemini 3.8 Flash';
        showToast('Đã nhận lời giải chi tiết từ Ribbon!', 'success', 3000);
      }
    });
  }

  // Initial Boot
  window.addEventListener('DOMContentLoaded', () => {
    initDomElements();
    initZoomPanEvents();
    attachEventListeners();
    attachBridgeListeners();

    // Init defaults
    dom.codeTextarea.value = state.currentTikzCode;
    updateLineNumbers();
    autoExpandTextarea(dom.promptTextarea);
    updateActionButtons();

    // Check if shape is already selected in Word at startup
    window.WordBridge.getSelectedTikz().then(res => {
      if (res && res.hasTikz && res.tikzCode) {
        state.hasWordTikzSelected = true;
        dom.selectionBanner.classList.add('active');
        dom.selectionTitle.innerText = 'Hình TikZ trong Word';
        dom.codeTextarea.value = res.tikzCode;
        updateLineNumbers();
        compileTikzCode(true);
        updateActionButtons();
      } else {
        // Tự động biên dịch hình mẫu đầu tiên để sẵn sàng xem trước
        compileTikzCode(true);
      }
    }).catch(() => {
      compileTikzCode(true);
    });

    console.log('[SidebarApp] Initialized successfully.');
  });
})();
