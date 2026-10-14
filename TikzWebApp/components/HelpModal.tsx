import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { getHelpResponse } from '../services/geminiService';

interface HelpModalProps {
  onClose: () => void;
}

interface Message {
  id: string;
  role: 'assistant' | 'user';
  content: React.ReactNode;
}

const initialMessage: React.ReactNode = (
  <div className="space-y-4 text-[11pt] leading-relaxed">
    <p>
      Xin chào! Tôi là trợ lý ảo của <strong>Code TikZ AI</strong>. Lời đầu tiên, xin gửi lời cảm ơn chân thành và sâu sắc nhất đến bạn vì đã tin tưởng và sử dụng ứng dụng của Thầy Tuấn. Sự ủng hộ của bạn là động lực to lớn để chúng tôi tiếp tục phát triển! ❤️
    </p>
    <p>
      Ứng dụng Code TikZ AI được thiết kế để giúp bạn tạo và quản lý code TikZ một cách nhanh chóng, chuẩn xác và chuyên nghiệp nhất. Dưới đây là tất cả các tính năng và cách bạn có thể sử dụng App:
    </p>
    
    <div>
      <h4 className="font-bold text-slate-800 dark:text-white flex items-center gap-2 mb-2">
        🌟 CÁC TÍNH NĂNG NỔI BẬT & VÍ DỤ MINH HỌA:
      </h4>
      <ul className="list-disc pl-5 space-y-2">
        <li><strong>AI tự động vẽ hình TikZ:</strong> Tạo code TikZ chất lượng 4K, sắc nét từ yêu cầu của bạn. <em>(Ví dụ: Yêu cầu "Vẽ đồ thị hàm số y = x^2 - 4x + 3 có đỉnh và trục đối xứng", hoặc "Vẽ hình chóp S.ABCD đáy hình chữ nhật, SA vuông góc đáy")</em></li>
        <li><strong>Quản lý thư viện cá nhân:</strong> Lưu trữ, phân loại, tìm kiếm, sửa và xóa các mẫu code TikZ. <em>(Ví dụ: Tạo các nhóm "Hình học không gian 11", "Đồ thị hàm số 12" để phân loại code dễ tìm)</em></li>
        <li><strong>Smart Editor:</strong> Trình soạn thảo code thông minh với highlight cú pháp, tự động lưu và thanh công cụ chèn nhanh lệnh TikZ. <em>(Ví dụ: Chỉ cần click nút trên thanh công cụ để chèn nhanh khung code TikZ chuẩn, hoặc dễ dàng phát hiện lỗi sai nhờ màu sắc cú pháp)</em></li>
        <li><strong>Tải lên hàng loạt:</strong> Thêm nhanh nhiều file .tex hoặc .txt vào thư viện. <em>(Ví dụ: Kéo thả cùng lúc 10 file .tex chứa các hình vẽ cũ của bạn vào App để lưu trữ đồng loạt)</em></li>
        <li><strong>Chia sẻ thư viện:</strong> Dễ dàng chia sẻ bộ sưu tập code của bạn cho người khác qua mã chia sẻ. <em>(Ví dụ: Bạn tạo mã chia sẻ cho nhóm "Đề thi thử 2024" và gửi mã đó cho đồng nghiệp, họ nhập mã là có ngay toàn bộ code của bạn)</em></li>
      </ul>
    </div>

    <div>
      <h4 className="font-bold text-slate-800 dark:text-white flex items-center gap-2 mb-2">
        💡 CÁCH NHẬP YÊU CẦU (PROMPT) HIỆU QUẢ:
      </h4>
      <p className="mb-2">Bạn có thể yêu cầu AI vẽ hình bằng rất nhiều cách linh hoạt:</p>
      <ol className="list-decimal pl-5 space-y-2">
        <li><strong>Mô tả bằng văn bản:</strong> Nhập trực tiếp yêu cầu chi tiết <em>(ví dụ: "Vẽ hình nón có bán kính r=3, chiều cao h=4, có đánh dấu góc ở đỉnh")</em>.</li>
        <li><strong>Chụp ảnh đề bài:</strong> Chụp lại đề toán trong sách hoặc trên màn hình và tải lên.</li>
        <li><strong>Phác họa ra giấy:</strong> Bạn chỉ cần vẽ tay phác thảo hình dáng mong muốn ra giấy, chụp ảnh lại và gửi lên App, AI sẽ hiểu và vẽ lại bằng code TikZ cực chuẩn!</li>
        <li><strong>Tải lên code cũ:</strong> Gửi đoạn code TikZ bạn đang có để AI sửa lỗi, tối ưu hoặc vẽ thêm chi tiết.</li>
      </ol>
    </div>

    <div>
      <h4 className="font-bold text-slate-800 dark:text-white flex items-center gap-2 mb-2">
        🔥 NHỮNG TIỆN ÍCH "ẨN" BẠN NÊN BIẾT:
      </h4>
      <ul className="list-disc pl-5 space-y-2">
        <li><strong>Chia sẻ code cực nhanh:</strong> Bạn có thể tạo "Mã chia sẻ" cho bất kỳ thư mục nào trong Thư viện. Người khác chỉ cần nhập mã này là sẽ nhận được toàn bộ code của bạn. Rất tuyệt vời để làm việc nhóm!</li>
        <li><strong>Lưu trữ Thư viện an toàn & thông minh:</strong> Dữ liệu của bạn được lưu trữ an toàn trên trình duyệt. Hãy tạo các thư mục rõ ràng (ví dụ: "Hình học 11", "Đề thi HSG") để dễ dàng quản lý và tìm kiếm lại sau này.</li>
        <li><strong>Tải file .tex hàng loạt:</strong> Không cần copy-paste từng file! Bạn chỉ cần kéo thả nhiều file .tex hoặc .txt cùng lúc vào màn hình Thư viện, App sẽ tự động bóc tách và lưu tất cả vào thư mục cho bạn.</li>
        <li><strong>Vẽ hình siêu tốc từ ảnh thực tế/mô phỏng:</strong> Chụp ảnh thực tế hoặc hình mô phỏng, tải lên App và thêm vài dòng mô tả tọa độ/điểm quan trọng. AI sẽ "nhìn" ảnh và chuyển đổi thành code TikZ chính xác đến bất ngờ!</li>
      </ul>
    </div>

    <p className="font-medium text-slate-800 dark:text-white mt-4">
      Bạn có thắc mắc và muốn hỏi thêm điều gì, hay trợ giúp gì?
    </p>
  </div>
);

const HelpModal: React.FC<HelpModalProps> = ({ onClose }) => {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'assistant', content: initialMessage }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);
  const textBeforeRecordingRef = useRef<string>('');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'vi-VN';

      recognition.onstart = () => {
        setIsRecording(true);
      };

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';

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
        
        setInputValue(textBeforeRecordingRef.current + interimTranscript);
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error', event.error);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const handleMicClick = () => {
    if (!recognitionRef.current) {
      alert("Trình duyệt của bạn không hỗ trợ nhận dạng giọng nói.");
      return;
    }
    if (isRecording) {
      recognitionRef.current.stop();
    } else {
      textBeforeRecordingRef.current = inputValue ? inputValue.trim() + ' ' : '';
      setInputValue(textBeforeRecordingRef.current);
      recognitionRef.current.start();
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userText = inputValue;
    const newUserMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userText
    };

    setMessages(prev => [...prev, newUserMsg]);
    setInputValue('');

    // Add a loading message
    const loadingMsgId = (Date.now() + 1).toString();
    const loadingMsg: Message = {
      id: loadingMsgId,
      role: 'assistant',
      content: (
        <div className="flex items-center gap-2 text-slate-500">
          <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      )
    };
    setMessages(prev => [...prev, loadingMsg]);

    try {
      const responseText = await getHelpResponse(userText);
      
      setMessages(prev => prev.map(msg => 
        msg.id === loadingMsgId 
          ? { ...msg, content: <div className="markdown-body"><ReactMarkdown>{responseText}</ReactMarkdown></div> }
          : msg
      ));
    } catch (error) {
      setMessages(prev => prev.map(msg => 
        msg.id === loadingMsgId 
          ? { ...msg, content: <p className="text-red-500">Xin lỗi, có lỗi xảy ra khi kết nối. Vui lòng thử lại sau!</p> }
          : msg
      ));
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <style>
        {`
          .markdown-body h1 { font-size: 1.5em; font-weight: bold; margin-top: 1em; margin-bottom: 0.5em; }
          .markdown-body h2 { font-size: 1.3em; font-weight: bold; margin-top: 1em; margin-bottom: 0.5em; }
          .markdown-body h3 { font-size: 1.1em; font-weight: bold; margin-top: 1em; margin-bottom: 0.5em; }
          .markdown-body p { margin-bottom: 0.5em; }
          .markdown-body ul { list-style-type: disc; padding-left: 1.5em; margin-bottom: 0.5em; }
          .markdown-body ol { list-style-type: decimal; padding-left: 1.5em; margin-bottom: 0.5em; }
          .markdown-body li { margin-bottom: 0.25em; }
          .markdown-body strong { font-weight: bold; }
          .markdown-body em { font-style: italic; }
          .markdown-body code { background-color: rgba(0,0,0,0.1); padding: 0.2em 0.4em; border-radius: 3px; font-family: monospace; }
          .dark .markdown-body code { background-color: rgba(255,255,255,0.1); }
        `}
      </style>
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-4xl h-[85vh] flex flex-col overflow-hidden animate-slide-up">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/50 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
                <path fillRule="evenodd" d="M4.804 21.644A6.707 6.707 0 006 21.75a6.721 6.721 0 003.583-1.029c.774.182 1.584.279 2.417.279 5.322 0 9.75-3.97 9.75-9 0-5.03-4.428-9-9.75-9s-9.75 3.97-9.75 9c0 2.409 1.025 4.587 2.674 6.192.232.226.277.428.254.543a3.73 3.73 0 01-.814 1.686.75.75 0 00.44 1.223zM8.25 10.875a1.125 1.125 0 100 2.25 1.125 1.125 0 000-2.25zM10.875 12a1.125 1.125 0 112.25 0 1.125 1.125 0 01-2.25 0zm4.875-1.125a1.125 1.125 0 100 2.25 1.125 1.125 0 000-2.25z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800 dark:text-white leading-tight">
                Trợ lý Hỏi đáp
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Giải đáp mọi thắc mắc về Code TikZ AI
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <a
              href="https://youtu.be/3rxW0S5xhMw"
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/50 dark:text-blue-300 dark:hover:bg-blue-800/50 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" clipRule="evenodd" />
              </svg>
              Hướng dẫn sử dụng
            </a>
            <button
              onClick={onClose}
              className="p-2 text-white bg-red-500 hover:bg-red-600 rounded-lg transition-colors shadow-md hover:shadow-lg flex items-center justify-center"
              title="Đóng cửa sổ"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        {/* Guide Links Section */}
        <div className="px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border-b border-blue-100 dark:border-blue-800 flex items-center gap-4 text-sm">
          <span className="font-medium text-blue-800 dark:text-blue-300">Xem nhanh:</span>
          {(() => {
            let videoLink = '';
            let fileLink = '';
            try {
              const savedGuide = localStorage.getItem('TIKZ_USER_GUIDE');
              if (savedGuide) {
                const parsed = JSON.parse(savedGuide);
                videoLink = parsed.videoLink || '';
                fileLink = parsed.fileLink || '';
              }
            } catch (e) {}
            
            return (
              <>
                {videoLink ? (
                  <a href={videoLink} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                      <path d="M3.25 4A2.25 2.25 0 001 6.25v7.5A2.25 2.25 0 003.25 16h7.5A2.25 2.25 0 0013 13.75v-7.5A2.25 2.25 0 0010.75 4h-7.5zM19 4.75a.75.75 0 00-1.28-.53l-3 3a.75.75 0 00-.22.53v4.5c0 .199.079.39.22.53l3 3a.75.75 0 001.28-.53V4.75z" />
                    </svg>
                    Video Hướng dẫn
                  </a>
                ) : (
                  <span className="text-slate-400 italic">Chưa có video</span>
                )}
                
                {fileLink ? (
                  <a href={fileLink} target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                      <path fillRule="evenodd" d="M4.5 2A1.5 1.5 0 003 3.5v13A1.5 1.5 0 004.5 18h11a1.5 1.5 0 001.5-1.5V7.621a1.5 1.5 0 00-.44-1.06l-4.12-4.122A1.5 1.5 0 0011.378 2H4.5zm2.25 8.5a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5zm0 3a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5z" clipRule="evenodd" />
                    </svg>
                    File HDSD
                  </a>
                ) : (
                  <span className="text-slate-400 italic">Chưa có file HDSD</span>
                )}
              </>
            );
          })()}
        </div>
        
        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6 bg-slate-50/50 dark:bg-slate-900/20 border-[2pt] border-yellow-500 m-2 rounded-lg">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                <div className="flex-shrink-0 mt-1">
                  {msg.role === 'assistant' ? (
                    <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/50 rounded-full flex items-center justify-center text-blue-600 dark:text-blue-400">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                        <path fillRule="evenodd" d="M4.804 21.644A6.707 6.707 0 006 21.75a6.721 6.721 0 003.583-1.029c.774.182 1.584.279 2.417.279 5.322 0 9.75-3.97 9.75-9 0-5.03-4.428-9-9.75-9s-9.75 3.97-9.75 9c0 2.409 1.025 4.587 2.674 6.192.232.226.277.428.254.543a3.73 3.73 0 01-.814 1.686.75.75 0 00.44 1.223zM8.25 10.875a1.125 1.125 0 100 2.25 1.125 1.125 0 000-2.25zM10.875 12a1.125 1.125 0 112.25 0 1.125 1.125 0 01-2.25 0zm4.875-1.125a1.125 1.125 0 100 2.25 1.125 1.125 0 000-2.25z" clipRule="evenodd" />
                      </svg>
                    </div>
                  ) : (
                    <div className="w-8 h-8 bg-teal-100 dark:bg-teal-900/50 rounded-full flex items-center justify-center text-teal-600 dark:text-teal-400">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                        <path fillRule="evenodd" d="M7.5 6a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM3.751 20.105a8.25 8.25 0 0116.498 0 .75.75 0 01-.437.695A18.683 18.683 0 0112 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 01-.437-.695z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>
                <div className={`p-4 rounded-2xl ${
                  msg.role === 'user' 
                    ? 'bg-teal-500 text-white rounded-tr-sm' 
                    : 'bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 rounded-tl-sm shadow-sm'
                }`}>
                  {typeof msg.content === 'string' ? (
                    <p className="whitespace-pre-wrap text-[11pt]">{msg.content}</p>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-900 rounded-full px-4 py-2 border-[1pt] border-red-500 focus-within:border-teal-500 dark:focus-within:border-teal-500 transition-colors">
            <button
              onClick={handleMicClick}
              className={`p-2 rounded-full transition-colors flex-shrink-0 bg-transparent ${
                isRecording 
                  ? 'text-red-500 animate-pulse' 
                  : 'text-teal-500 hover:text-teal-600 hover:bg-teal-50 dark:hover:bg-teal-900/20'
              }`}
              title={isRecording ? 'Đang ghi âm...' : 'Nhập bằng giọng nói'}
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
              </svg>
            </button>
            
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Nhập câu hỏi của bạn... (Enter để gửi)"
              className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0 text-teal-600 dark:text-teal-400 text-[12pt] placeholder:text-slate-400 dark:placeholder:text-slate-500 py-2"
            />
            
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              className={`p-2 rounded-full transition-colors flex-shrink-0 ${
                inputValue.trim() 
                  ? 'bg-teal-500 text-white hover:bg-teal-600 shadow-sm' 
                  : 'bg-slate-200 text-slate-400 dark:bg-slate-800 dark:text-slate-600 cursor-not-allowed'
              }`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HelpModal;
