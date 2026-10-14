import React, { useState, useEffect, useRef, useCallback } from 'react';
import { PaperclipIcon, MicrophoneIcon, SendIcon, HourglassIcon, TrashIcon, CopyIcon, ZapIcon } from '../constants';
import { getAiAssistance, ImagePart } from '../services/geminiService';
import { playStartSound, playTaskCompleteSound, playErrorSound } from '../utils/audio';
import type { Category } from '../types';

import { cleanBoilerplate } from '../utils/codeCleaner';

const TIKZ_OPTIMIZATION_PROMPT = `[VAI TRÒ]
Bạn là một Chuyên gia Hình học Toán học và Kiến trúc sư mã TiKZ cấp cao.
[MỤC TIÊU CỐT LÕI]
Khi nhận được mã TiKZ đầu vào (từ cửa sổ làm việc/cửa sổ phải), tuyệt đối KHÔNG được tự ý sáng tác hay tạo lại code từ đầu. Nhiệm vụ của bạn là phân tích cấu trúc hình học, tính toán nhiều chiều, qua 6-10 lượt (multi-pass analysis) để tái cấu trúc, chuẩn hóa và tối ưu hóa đoạn mã đó đạt chuẩn xuất bản chuyên nghiệp. Chỉ xuất ra đoạn mã TiKZ đã được chuẩn hóa.
[NGUYÊN TẮC TỐI ƯU HÓA (OPTIMIZATION RULES)]
1. Tham số hóa (Parameterization): Thay thế các giá trị cứng (hardcode) bằng các biến số hoặc tham số (ví dụ: \\begin{tikzpicture}[>=stealth, every node/.style={font=\\normalsize}, declare function={R=2.5; r=0.8; h=5;}]) ở đầu môi trường tikzpicture để dễ dàng tinh chỉnh.
2. Xóa điểm chết (Dead-code Elimination): Loại bỏ hoàn toàn các tọa độ (\\coordinate), node (\\node), hoặc đường vẽ không đóng góp vào hình vẽ cuối cùng.
3. Hình học giải tích & Phép biến hình: Không tọa độ hóa thủ công các điểm phụ thuộc. Sử dụng thư viện calc, intersections hoặc các phép biến hình (rotate, shift, scale, xscale, yscale) để dựng hình chính xác.
4. Ưu tiên tọa độ cực: Sử dụng tọa độ cực thay cho tọa độ Descartes khi thao tác với đường tròn, đa giác đều, hoặc các góc quay, giúp mã ngắn gọn và mang tính toán học cao hơn.
5. Tối ưu bằng phép lặp: Khai thác tối đa vòng lặp \\foreach cho các chi tiết có tính quy luật (chia vạch, vẽ lưới, gán nhãn hàng loạt, vẽ chuỗi điểm).
6. Linh hoạt nhãn điểm (Dynamic Labeling): Định dạng nhãn thông minh bằng các tùy chọn vị trí tương đối (above, below left, v.v.) hoặc góc độ cụ thể (label={[angle]Name}). Căn chỉnh vị trí nhãn để không cắt đứt các đường vẽ hoặc đè lên nhau.
7. Khoảng/đoạn trên trục số: Khi biểu diễn khoảng, đoạn trên trục số, TUYỆT ĐỐI KHÔNG dùng cung tròn hay vẽ cung cong. BẮT BUỘC sử dụng ký tự ngoặc có sẵn trên bàn phím: "(", ")", "[", "]".
8. Bảo tồn nguyên trạng cấu trúc và nội dung: Khi vẽ lại hoặc tối ưu hình, ảnh, bảng biến thiên, đồ thị, PHẢI bảo tồn tuyệt đối hình gốc. Tuyệt đối KHÔNG ĐƯỢC THÊM, BỚT, hay thay đổi bất kỳ thành phần nào của hình gốc (đường nét, điểm, nhãn, dữ liệu, mũi tên, v.v.) TRỪ KHI tôi có yêu cầu rõ ràng về việc thêm/bớt đó.
[NGUYÊN TẮC XẾP LỚP (LAYERING RULES)]
Cấu trúc lại thứ tự các lệnh vẽ từ trên xuống dưới theo nguyên tắc quang học (từ dưới lên trên mặt phẳng), tuân thủ tuyệt đối thứ tự sau:
• Lớp 1 (Dưới cùng): Các lệnh tô màu vùng (Fill/Shade) - Sử dụng màu có độ trong suốt phù hợp (opacity).
• Lớp 2: Các đường nét đứt (Dashed/Dotted lines) - Thể hiện các đường khuất.
• Lớp 3: Các đường nét liền (Solid lines) - Thể hiện các đường thấy, đường viền chính.
• Lớp 4: Các điểm (Points/Coordinates) - Lệnh vẽ các dấu chấm tròn (\\filldraw) tại các đỉnh, giao điểm quan trọng.
• Lớp 5 (Trên cùng): Nhãn văn bản và ký hiệu toán học (Labels/Nodes) - Đảm bảo luôn hiển thị rõ ràng nhất, không bị bất kỳ nét vẽ hay mảng màu nào che khuất. Có thể dùng fill=white, inner sep=1pt cho nền nhãn nếu bắt buộc phải đè lên nét vẽ như chú thích diện tích.
[QUY TRÌNH THỰC THI BẮT BUỘC]
• Bước 1 (Phân tích): Đọc mã gốc, trích xuất danh sách các điểm cơ sở và quan hệ hình học giữa chúng.
• Bước 2 (Lên kế hoạch): Xác định các thành phần có thể gộp thành vòng lặp, các điểm cần chuyển sang tính toán tương đối/tọa độ cực.
• Bước 3 (Tái cấu trúc): Viết lại mã theo đúng cấu trúc 5 lớp (Layering Rules).
• Bước 4 (Kiểm tra chéo): Rà soát lại xem hình học có bị thay đổi không, các nhãn toán học có được bọc trong cặp dấu chuẩn xác chưa.
• Bước 5 (Xuất kết quả): Cung cấp đoạn mã TiKZ tối ưu duy nhất để thay thế trực tiếp vào cửa sổ bên phải. Không kèm theo các lời giải thích dài dòng nếu không có cảnh báo lỗi hình học nghiêm trọng.
Một số lưu ý thêm để tăng tính chuyên nghiệp:
Về thư viện (Libraries): Đôi khi mã ban đầu không chứa khai báo thư viện nhưng lại sử dụng cú pháp thư viện. Bạn có thể bổ sung thêm một dòng vào Prompt yêu cầu AI: "Tự động ghi chú các thư viện TiKZ cần thiết (ví dụ: \\usetikzlibrary{calc, intersections, angles, quotes}) ở dạng comment ngay phía trên \\begin{tikzpicture} để người dùng tiện đối chiếu."
Về định dạng Toán học: Trong TiKZ, việc đặt tên điểm và hiển thị nhãn rất dễ bị sai font nếu thiếu dấu đô la. Các công thức toán trên hình, tọa độ đỉnh hoặc tọa độ đều sẽ được AI xử lý mượt mà khi có yêu cầu ở Bước 4 của quy trình trên. Nếu cần chèn phương trình phức tạp dạng hiển thị trên biểu đồ, hệ thống cũng sẽ tự động xử lý nó tối ưu nhất.
# khi tôi xác nhận lệnh biểu tượng tia chớp thì bạn tối ưu hóa mã code tikz ở cửa sổ bên phải ngoài cùng cho tôi.`;

interface AIAssistantProps {
  setCode: (code: string) => void;
  onApiKeyInvalid: (message: string) => void;
  isReadOnly: boolean;
  onFilesDropped?: (files: { name: string; content: string }[]) => void;
  userLibrary?: Category;
  isNoteEnabled: boolean;
  isBbtNoFrame?: boolean;
  onBoilerplateRemoved?: () => void;
  width?: number;
  currentCode?: string;
  onLoadingChange?: (loading: boolean) => void;
}

// Helper to convert file to base64
const fileToBase64 = (file: File): Promise<{ data: string; mimeType: string }> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      const base64Data = result.split(',')[1];
      let mimeType = file.type;
      if (!mimeType) {
        if (file.name.endsWith('.pdf')) mimeType = 'application/pdf';
        else if (file.name.endsWith('.docx')) mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
        else if (file.name.endsWith('.doc')) mimeType = 'application/msword';
        else mimeType = 'application/octet-stream';
      }
      resolve({ data: base64Data, mimeType });
    };
    reader.onerror = (error) => reject(error);
    reader.readAsDataURL(file);
  });
};

const AIAssistant: React.FC<AIAssistantProps> = ({ setCode, onApiKeyInvalid, isReadOnly, onFilesDropped, userLibrary, isNoteEnabled, isBbtNoFrame, onBoilerplateRemoved, width, currentCode, onLoadingChange }) => {
  const [promptText, setPromptText] = useState('');
  const [inputFiles, setInputFiles] = useState<{ type: 'image' | 'text' | 'document'; name: string; url?: string; content?: string; file: File }[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [copyStatus, setCopyStatus] = useState('Sao chép');
  
  const [isBbtChecked, setIsBbtChecked] = useState(false);

  useEffect(() => {
    if (onLoadingChange) {
      onLoadingChange(isGenerating);
    }
  }, [isGenerating, onLoadingChange]);
  const [isGraphChecked, setIsGraphChecked] = useState(false);
  const [isDrawingChecked, setIsDrawingChecked] = useState(false);
  const [isBxdChecked, setIsBxdChecked] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const recognitionRef = useRef<any>(null);
  const textBeforeRecordingRef = useRef('');
  const abortControllerRef = useRef<AbortController | null>(null);

  const fileStats = React.useMemo(() => {
    const stats: Record<string, number> = {};
    inputFiles.forEach(f => {
      const extMatch = f.name.match(/\.([^.]+)$/);
      let ext = extMatch ? extMatch[1].toUpperCase() : 'KHÁC';
      if (ext === 'JPEG') ext = 'JPG';
      stats[ext] = (stats[ext] || 0) + 1;
    });
    return Object.entries(stats).map(([ext, count]) => ({ ext, count }));
  }, [inputFiles]);

  const getExtColor = (ext: string) => {
    switch (ext) {
      case 'PDF': return 'bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800';
      case 'JPG':
      case 'PNG':
      case 'GIF':
      case 'WEBP': return 'bg-blue-100 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800';
      case 'TEX': return 'bg-teal-100 text-teal-700 border-teal-200 dark:bg-teal-900/30 dark:text-teal-400 dark:border-teal-800';
      case 'TXT': return 'bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800/50 dark:text-gray-400 dark:border-gray-700';
      case 'DOC':
      case 'DOCX': return 'bg-indigo-100 text-indigo-700 border-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:border-indigo-800';
      default: return 'bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-900/30 dark:text-orange-400 dark:border-orange-800';
    }
  };

  // Setup Speech Recognition
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'vi-VN';

      recognitionRef.current.onresult = (event: any) => {
        let interimTranscript = '';
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript + ' ';
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }
        if (finalTranscript) {
          textBeforeRecordingRef.current += finalTranscript;
        }
        setPromptText(textBeforeRecordingRef.current + interimTranscript);
      };
      
      recognitionRef.current.onend = () => {
        setIsRecording(false);
      };
    }
  }, []);

  const handleMicClick = () => {
    if (isReadOnly) return;
    if (!recognitionRef.current) {
      alert("Trình duyệt của bạn không hỗ trợ nhận dạng giọng nói.");
      return;
    }
    if (isRecording) {
      recognitionRef.current.stop();
    } else {
      textBeforeRecordingRef.current = promptText ? promptText.trim() + ' ' : '';
      setPromptText(textBeforeRecordingRef.current);
      recognitionRef.current.start();
      setIsRecording(true);
    }
  };

  const processFiles = useCallback(async (files: FileList) => {
    if (isReadOnly) return;
    const newFiles: { type: 'image' | 'text' | 'document'; name: string; url?: string; content?: string; file: File }[] = [];

    const filePromises = Array.from(files).map(async (file) => {
      if (file.size > 19 * 1024 * 1024) {
        alert(`Tệp ${file.name} quá lớn (vượt quá 19MB). Vui lòng chọn tệp nhỏ hơn.`);
        return null;
      }
      if (file.type.startsWith('image/')) {
        return { type: 'image' as const, name: file.name, url: URL.createObjectURL(file), file };
      } else if (file.name.endsWith('.tex') || file.name.endsWith('.txt') || file.type.startsWith('text/')) {
        const text = await file.text();
        return { type: 'text' as const, name: file.name, content: text, file };
      } else {
        return { type: 'document' as const, name: file.name, file };
      }
    });

    const results = await Promise.all(filePromises);
    
    results.forEach(res => {
      if (res) newFiles.push(res);
    });

    if (newFiles.length > 0) {
      setInputFiles(prev => [...prev, ...newFiles]);
    }
  }, [isReadOnly]);

  const processDataTransfer = useCallback(async (dataTransfer: DataTransfer) => {
    if (isReadOnly) return;
    
    const items = dataTransfer.items;
    if (!items) return;

    const newFiles: { type: 'image' | 'text' | 'document'; name: string; url?: string; content?: string; file: File }[] = [];

    const traverseFileTree = async (item: any) => {
      if (item.isFile) {
        const file = await new Promise<File>((resolve) => item.file(resolve));
        if (file.size > 19 * 1024 * 1024) {
          alert(`Tệp ${file.name} quá lớn (vượt quá 19MB). Vui lòng chọn tệp nhỏ hơn.`);
          return;
        }
        if (file.type.startsWith('image/')) {
          newFiles.push({ type: 'image', name: file.name, url: URL.createObjectURL(file), file });
        } else if (file.name.endsWith('.tex') || file.name.endsWith('.txt') || file.type.startsWith('text/')) {
          const text = await file.text();
          newFiles.push({ type: 'text', name: file.name, content: text, file });
        } else {
          newFiles.push({ type: 'document', name: file.name, file });
        }
      } else if (item.isDirectory) {
        const dirReader = item.createReader();
        let allEntries: any[] = [];
        
        const readEntries = () => new Promise<any[]>((resolve) => {
          dirReader.readEntries((entries: any[]) => resolve(entries));
        });

        let entries = await readEntries();
        while (entries.length > 0) {
          allEntries = allEntries.concat(entries);
          entries = await readEntries();
        }

        for (const entry of allEntries) {
          await traverseFileTree(entry);
        }
      }
    };

    for (let i = 0; i < items.length; i++) {
      const item = items[i].webkitGetAsEntry ? items[i].webkitGetAsEntry() : null;
      if (item) {
        await traverseFileTree(item);
      } else {
        const file = items[i].getAsFile();
        if (file) {
           if (file.size > 19 * 1024 * 1024) {
             alert(`Tệp ${file.name} quá lớn (vượt quá 19MB). Vui lòng chọn tệp nhỏ hơn.`);
             continue;
           }
           if (file.type.startsWith('image/')) {
             newFiles.push({ type: 'image', name: file.name, url: URL.createObjectURL(file), file });
           } else if (file.name.endsWith('.tex') || file.name.endsWith('.txt') || file.type.startsWith('text/')) {
             const text = await file.text();
             newFiles.push({ type: 'text', name: file.name, content: text, file });
           } else {
             newFiles.push({ type: 'document', name: file.name, file });
           }
        }
      }
    }

    if (newFiles.length > 0) {
      setInputFiles(prev => [...prev, ...newFiles]);
    }
  }, [isReadOnly]);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isReadOnly) setIsDragging(true);
  }, [isReadOnly]);
  
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (!isReadOnly && e.dataTransfer) {
      await processDataTransfer(e.dataTransfer);
      e.dataTransfer.clearData();
    }
  }, [processDataTransfer, isReadOnly]);

  const handlePaste = useCallback(async (e: React.ClipboardEvent) => {
    if (!isReadOnly && e.clipboardData) {
      if (e.clipboardData.files && e.clipboardData.files.length > 0) {
        // Don't prevent default if there are files, actually we might want to prevent default so the filename doesn't get pasted as text
        e.preventDefault();
        await processFiles(e.clipboardData.files as any);
      } else {
        const text = e.clipboardData.getData('text');
        if (text) {
          const matches = text.match(/\\begin\{tikzpicture\}[\s\S]*?\\end\{tikzpicture\}/g);
          if (matches && matches.length > 1) {
            e.preventDefault();
            const newFiles = matches.map((content, idx) => ({
              type: 'text' as const,
              name: `Pasted_Code_${Date.now()}_${idx + 1}.tex`,
              content,
              file: new File([content], `Pasted_Code_${Date.now()}_${idx + 1}.tex`, { type: 'text/plain' })
            }));
            setInputFiles(prev => [...prev, ...newFiles]);
          }
        }
      }
    }
  }, [processFiles, isReadOnly]);

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  const handleOptimizeCode = async () => {
    if (isReadOnly || !currentCode || isGenerating) return;
    
    if (isRecording) {
      recognitionRef.current.stop();
    }
    
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    setIsGenerating(true);
    playStartSound();
    
    setCode('%%GENERATING%%\nĐang tối ưu hóa mã TiKZ...');

    try {
      const finalPrompt = `${TIKZ_OPTIMIZATION_PROMPT}\n\n--- MÃ TIKZ ĐẦU VÀO TỪ CỬA SỔ PHẢI ---\n${currentCode}\n`;

      const aiResponseText = await getAiAssistance(finalPrompt, [], userLibrary, signal, isNoteEnabled, isBbtNoFrame);
      
      if (signal.aborted) {
        throw new Error('AbortError');
      }

      const { cleanedCode, wasRemoved } = cleanBoilerplate(aiResponseText);
      if (wasRemoved && onBoilerplateRemoved) {
        onBoilerplateRemoved();
      }

      setCode(cleanedCode);
      playTaskCompleteSound();
    } catch (error: any) {
      if (error?.message === 'AbortError' || error?.name === 'AbortError') {
        setCode(currentCode || '');
        return;
      }
      playErrorSound();
      console.error('Error optimizing code:', error);
      const errorMessagePayload = error?.message || '';
      const errorJsonStr = typeof error === 'object' ? JSON.stringify(error) : '';
      const errorMessageStr = error.toString() + ' ' + errorMessagePayload + ' ' + errorJsonStr;
      
      if (errorMessageStr.includes('429') || errorMessageStr.includes('RESOURCE_EXHAUSTED') || errorMessageStr.includes('quota') || errorMessageStr.includes('Quota exceeded')) {
        onApiKeyInvalid('API Key của bạn đã vượt quá giới hạn sử dụng (Quota exceeded). Vui lòng thử lại sau hoặc sử dụng API Key khác.');
        setCode('% Lỗi: Bạn đã vượt quá giới hạn (Quota). Thử lại sau.');
      } else if (errorMessageStr.includes('400') || errorMessageStr.toLowerCase().includes('api key') || errorMessageStr.includes('API key not valid')) {
        onApiKeyInvalid('Khóa API không hợp lệ hoặc đã hết hạn.');
        setCode('% Lỗi: Khóa API không hợp lệ.');
      } else {
        setCode('Lỗi: ' + (errorMessagePayload || 'Không thể tạo mã.'));
      }
      setTimeout(() => {
        if (!abortControllerRef.current?.signal.aborted) {
           setCode(currentCode || '');
        }
      }, 5000);
    } finally {
      setIsGenerating(false);
      abortControllerRef.current = null;
    }
  };

  const handleGenerateCode = async () => {
    if ((!promptText.trim() && inputFiles.length === 0) || isReadOnly) return;
    if (isRecording) {
      recognitionRef.current.stop();
    }
    
    // Create a new AbortController for this request
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    setIsGenerating(true);
    playStartSound();
    
    // We need to get the current code from props, but we only have setCode.
    // However, the user wants the code to be cleared anyway.
    // If it fails, we can just set it to empty string or an error message.
    setCode('%%GENERATING%%\nĐang tạo mã cho yêu cầu...');

    const imageParts: ImagePart[] = await Promise.all(
        inputFiles.filter(f => f.type === 'image' || f.type === 'document').map(async (f) => {
            const { data, mimeType } = await fileToBase64(f.file);
            return { inlineData: { data, mimeType } };
        })
    );
    
    try {
      let finalPrompt = promptText;
      const selectedTasks = [];
      if (isBbtChecked) {
        selectedTasks.push(isBbtNoFrame ? "Bảng biến thiên (BBT) (nocadre=true)" : "Bảng biến thiên (BBT) có kẻ bảng (nocadre=false)");
      }
      if (isGraphChecked) selectedTasks.push("Đồ thị");
      if (isDrawingChecked) selectedTasks.push("Hình vẽ");
      if (isBxdChecked) selectedTasks.push("vẽ TẤT CẢ các hình, đồ thị, bảng biến thiên, ... (TikZ) có trong file hoặc yêu cầu mà không bỏ sót hình, BBT, đồ thị nào (trừ hình thực tế quá phức tạp)");

      if (selectedTasks.length > 0) {
        finalPrompt = `Hãy tạo/vẽ ${selectedTasks.join(", ")} cho yêu cầu sau:\n${promptText}`;
      }

      if (promptText.includes('[VAI TRÒ]') && currentCode) {
        finalPrompt += `\n\n--- MÃ TIKZ ĐẦU VÀO TỪ CỬA SỔ PHẢI ---\n${currentCode}\n`;
      }

      const textFiles = inputFiles.filter(f => f.type === 'text');
      if (textFiles.length > 0) {
        finalPrompt += `\n\nNội dung các tệp đính kèm:\n`;
        textFiles.forEach(file => {
          finalPrompt += `\n--- Tệp: ${file.name} ---\n${file.content}\n`;
        });
      }

      const aiResponseText = await getAiAssistance(finalPrompt, imageParts, userLibrary, signal, isNoteEnabled, isBbtNoFrame);
      
      if (signal.aborted) {
        throw new Error('AbortError');
      }

      const { cleanedCode, wasRemoved } = cleanBoilerplate(aiResponseText);
      if (wasRemoved && onBoilerplateRemoved) {
        onBoilerplateRemoved();
      }

      setCode(cleanedCode);
      playTaskCompleteSound();
    } catch (error: any) {
        if (error.message === 'AbortError' || error.name === 'AbortError') {
            setCode('');
            return;
        }
        
        const errorMessagePayload = error?.message || '';
        const errorJsonStr = typeof error === 'object' ? JSON.stringify(error) : '';
        const errorMessageStr = error.toString() + ' ' + errorMessagePayload + ' ' + errorJsonStr;
        if (errorMessageStr.includes('429') || errorMessageStr.includes('RESOURCE_EXHAUSTED') || errorMessageStr.includes('quota') || errorMessageStr.includes('Quota exceeded')) {
            onApiKeyInvalid('API Key của bạn đã vượt quá giới hạn sử dụng (Quota exceeded). Vui lòng thử lại sau hoặc sử dụng API Key khác.');
            setCode('% Lỗi: Bạn đã vượt quá giới hạn sử dụng (Quota exceeded). Vui lòng thử lại sau.');
        } else if (errorMessageStr.includes('400') || errorMessageStr.toLowerCase().includes('api key') || errorMessageStr.includes('API key not valid')) {
            onApiKeyInvalid('API Key của bạn không hợp lệ. Vui lòng kiểm tra lại.');
            setCode('');
        } else {
           console.error("Failed to generate code:", error);
           setCode('% Lỗi: ' + error.toString() + (errorMessagePayload ? ' - ' + errorMessagePayload : ''));
        }
        playErrorSound();
    } finally {
      if (abortControllerRef.current?.signal === signal) {
        abortControllerRef.current = null;
      }
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    if (promptText) {
      navigator.clipboard.writeText(promptText);
      setCopyStatus('Đã sao chép!');
      setTimeout(() => setCopyStatus('Sao chép'), 2000);
    }
  };

  return (
    <div 
      style={{ width: width ? `${width}px` : '8cm' }}
      className="shrink-0 bg-white dark:bg-slate-900 h-full flex flex-col p-4 border-[2.5pt] border-cyan-500 rounded-lg relative overflow-hidden"
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
    >
        {isDragging && (
          <div 
              className="absolute inset-0 bg-cyan-500/30 backdrop-blur-sm flex items-center justify-center border-4 border-dashed border-cyan-500 rounded-lg z-10"
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
          >
              <p className="text-center font-bold text-white px-4">Thả tệp vào đây</p>
          </div>
        )}
        
        <div className="flex items-center mb-4">
          <div className="flex items-center">
            <h2 className="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
              <SendIcon className="h-5 w-5 text-cyan-500" />
              Nhập yêu cầu
            </h2>
            <button
              onClick={handleOptimizeCode}
              disabled={isGenerating || !currentCode}
              className="ml-3 text-yellow-500 hover:text-yellow-600 transition-colors bg-transparent border-none p-0 outline-none disabled:opacity-50 disabled:cursor-not-allowed"
              title="Tối ưu hóa mã TiKZ"
            >
              <ZapIcon className="h-7 w-7" />
            </button>
          </div>
          <div className="ml-auto flex items-center gap-3">
            {inputFiles.length > 0 && (
              <div className="flex flex-wrap gap-1 justify-end mr-2">
                {fileStats.map(({ ext, count }) => (
                  <span key={ext} className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${getExtColor(ext)} shadow-sm`} title={`${count} tệp ${ext}`}>
                    {count} {ext}
                  </span>
                ))}
              </div>
            )}
            <button
              onClick={handleCopy}
              className={`transition-colors ${(promptText.trim().length > 0 || inputFiles.length > 0) ? 'text-teal-500 hover:text-teal-600' : 'text-slate-400 hover:text-slate-500'}`}
              title={copyStatus === 'Sao chép' ? 'Sao chép yêu cầu' : copyStatus}
            >
              <CopyIcon className="h-5 w-5" />
            </button>
            <button
              onClick={() => {
                setPromptText('');
                setInputFiles([]);
                setIsBbtChecked(false);
                setIsGraphChecked(false);
                setIsDrawingChecked(false);
                setIsBxdChecked(false);
              }}
              className="text-red-500 hover:text-red-600 transition-colors"
              title="Xóa yêu cầu"
            >
              <TrashIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {!isReadOnly && (
          <div className="flex gap-4 mb-3 px-1">
            <div className="flex items-center gap-1">
              <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 cursor-pointer hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
                <input 
                  type="checkbox" 
                  checked={isBbtChecked}
                  onChange={(e) => setIsBbtChecked(e.target.checked)}
                  className="rounded border-slate-300 text-cyan-500 focus:ring-cyan-500 w-4 h-4 cursor-pointer" 
                />
                BBT
              </label>
            </div>
            <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 cursor-pointer hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
              <input 
                type="checkbox" 
                checked={isGraphChecked}
                onChange={(e) => setIsGraphChecked(e.target.checked)}
                className="rounded border-slate-300 text-cyan-500 focus:ring-cyan-500 w-4 h-4 cursor-pointer" 
              />
              Đ.Thị
            </label>
            <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 cursor-pointer hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
              <input 
                type="checkbox" 
                checked={isDrawingChecked}
                onChange={(e) => setIsDrawingChecked(e.target.checked)}
                className="rounded border-slate-300 text-cyan-500 focus:ring-cyan-500 w-4 h-4 cursor-pointer" 
              />
              H.Vẽ
            </label>
            <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300 cursor-pointer hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
              <input 
                type="checkbox" 
                checked={isBxdChecked}
                onChange={(e) => setIsBxdChecked(e.target.checked)}
                className="rounded border-slate-300 text-cyan-500 focus:ring-cyan-500 w-4 h-4 cursor-pointer" 
              />
              TikZ
            </label>
          </div>
        )}

        {!isReadOnly ? (
          <div className="flex-1 flex flex-col min-h-0">
            <div className="flex-1 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg flex flex-col min-h-0 relative overflow-hidden">
              {inputFiles.length > 0 && (
                <div className="p-2 flex gap-2 overflow-x-auto border-b border-slate-200 dark:border-slate-700">
                  {inputFiles.map((file, index) => (
                    <div key={index} className="relative flex-shrink-0 flex items-center justify-center bg-slate-200 dark:bg-slate-700 rounded-md h-16 min-w-[4rem] px-2">
                      {file.type === 'image' && file.url ? (
                        <img src={file.url} className="h-16 w-16 object-cover rounded-md" alt="preview" />
                      ) : (
                        <div className="flex flex-col items-center justify-center text-xs text-slate-600 dark:text-slate-300 max-w-[5rem] overflow-hidden text-ellipsis whitespace-nowrap">
                          <PaperclipIcon className="h-6 w-6 mb-1" />
                          <span className="truncate w-full text-center">{file.name}</span>
                        </div>
                      )}
                      <button 
                        onClick={() => setInputFiles(prev => prev.filter((_, i) => i !== index))}
                        className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full h-4 w-4 text-xs flex items-center justify-center hover:bg-red-600 transition-colors">
                        &times;
                      </button>
                    </div>
                  ))}
                </div>
              )}
              <textarea
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                onKeyDown={(e) => { 
                  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { 
                    e.preventDefault(); 
                    handleGenerateCode(); 
                  } 
                }}
                placeholder="Nhập yêu cầu, dán hình ảnh, hoặc nhấn micro để nói... (Ctrl+Enter để gửi)"
                className="flex-1 w-full bg-transparent p-3 resize-none focus:outline-none placeholder:text-slate-500 dark:placeholder:text-slate-400 text-slate-900 dark:text-white text-[11pt]"
                disabled={isGenerating}
                onPaste={handlePaste}
              />
            </div>

            <div className="mt-4 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1">
                  <button 
                    onClick={() => fileInputRef.current?.click()}
                    className="p-2 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors"
                    title="Đính kèm tệp">
                    <PaperclipIcon className="h-6 w-6" />
                  </button>
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={(e) => { if(e.target.files && e.target.files.length > 0) processFiles(e.target.files); }} 
                    className="hidden" 
                    multiple 
                  />
                  <button
                    onClick={handleMicClick}
                    className={`p-2 rounded-md transition-colors ${isRecording ? 'bg-red-500 text-white animate-pulse' : 'bg-transparent text-teal-600 dark:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/20'}`}
                    title={isRecording ? 'Đang ghi âm...' : 'Nói để nhập liệu'}
                  >
                    <MicrophoneIcon className="h-6 w-6" />
                  </button>
                  <a
                    href="https://gemini.google.com/gem/c22746684763"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 px-3 py-1.5 rounded-md text-sm font-bold bg-indigo-50 text-indigo-600 hover:bg-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-400 dark:hover:bg-indigo-900/50 transition-colors flex items-center gap-1"
                    title="Mở Gems Gemini"
                  >
                    Gemini
                  </a>
                </div>
                
                <div className="flex items-center gap-2">
                  {isGenerating && (
                    <button
                      onClick={handleCancel}
                      className="text-red-500 hover:text-red-600 bg-transparent px-2 py-2 transition-colors font-bold flex items-center gap-2"
                      title="Hủy"
                    >
                      <span>Hủy</span>
                    </button>
                  )}
                  <button
                    onClick={handleGenerateCode}
                    disabled={isGenerating || (!promptText.trim() && inputFiles.length === 0)}
                    className="bg-cyan-500 hover:bg-cyan-600 text-white p-2.5 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                    title="Gửi (Ctrl+Enter)"
                  >
                    {isGenerating ? <HourglassIcon className="h-5 w-5 animate-spin" /> : <SendIcon className="h-5 w-5" />}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-500 dark:text-slate-400 italic text-center px-4">
            Chế độ chỉ đọc. Bạn không thể nhập yêu cầu mới.
          </div>
        )}
    </div>
  );
};

export default AIAssistant;
