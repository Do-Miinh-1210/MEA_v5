import React, { useState } from 'react';

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
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-md">
      <div className="bg-slate-50 dark:bg-slate-900 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col transform transition-all border border-slate-200 dark:border-slate-700">
        
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500"></div>
          <h2 className="text-2xl font-extrabold text-slate-800 dark:text-white flex items-center gap-3">
            <div className="bg-blue-100 dark:bg-blue-900/50 p-2 rounded-lg text-blue-600 dark:text-blue-400">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-7 h-7">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
              </svg>
            </div>
            Cẩm Nang Sử Dụng Ứng Dụng (Toàn Tập)
          </h2>
          {hasApiKey && (<button onClick={onClose} className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-all">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>)}
        </div>

        {/* Content */}
        <div className="p-0 overflow-y-auto flex-1 text-slate-700 dark:text-slate-300">
          
          <div className="max-w-4xl mx-auto p-6 md:p-8 space-y-10">
            {/* Section 1: Video */}
            <section className="bg-white dark:bg-slate-800 p-6 rounded-3xl border border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/5 dark:bg-red-500/10 rounded-full -mr-16 -mt-16 blur-2xl"></div>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-3">
                <span className="bg-red-100 text-red-600 dark:bg-red-900/50 dark:text-red-400 p-2 rounded-xl">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7">
                    <path d="M4.5 4.5a3 3 0 00-3 3v9a3 3 0 003 3h8.25a3 3 0 003-3v-9a3 3 0 00-3-3H4.5zM19.94 18.75l-2.69-2.69V7.94l2.69-2.69c.944-.945 2.56-.276 2.56 1.06v11.38c0 1.336-1.616 2.005-2.56 1.06z" />
                  </svg>
                </span>
                Phần 1: Xem Video Hướng Dẫn Nhanh
              </h3>
              <p className="mb-5 text-lg font-medium text-slate-600 dark:text-slate-400">
                Thầy/Cô vui lòng dành vài phút xem qua video dưới đây để nhanh chóng làm quen với các thao tác cốt lõi của phần mềm nhé:
              </p>
              <div className="aspect-video w-full rounded-2xl overflow-hidden shadow-lg border border-slate-200 dark:border-slate-700 bg-black">
                <iframe 
                  width="100%" 
                  height="100%" 
                  src="https://www.youtube.com/embed/3rxW0S5xhMw" 
                  title="Hướng dẫn sử dụng App" 
                  frameBorder="0" 
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                  referrerPolicy="strict-origin-when-cross-origin" 
                  allowFullScreen
                ></iframe>
              </div>
            </section>

            {/* Section 2: Detailed Guide */}
            <section className="space-y-6">
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-3 pb-3 border-b border-slate-200 dark:border-slate-700">
                <span className="bg-indigo-100 text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-400 p-2 rounded-xl">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-7 h-7">
                    <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12zm8.706-1.442c1.146-.573 2.437.463 2.126 1.706l-.709 2.836.042-.02a.75.75 0 01.67 1.34l-.04.022c-1.147.573-2.438-.463-2.127-1.706l.71-2.836-.042.02a.75.75 0 11-.671-1.34l.041-.022zM12 9a.75.75 0 100-1.5.75.75 0 000 1.5z" clipRule="evenodd" />
                  </svg>
                </span>
                Phần 2: Cẩm Nang Chi Tiết Từng Chức Năng
              </h3>
              
              <div className="grid grid-cols-1 gap-6">
                
                {/* Tính năng 1: Nhập API */}
                <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border-l-4 border-l-blue-500 border-y border-r border-slate-200 dark:border-slate-700 shadow-sm">
                  <div className="flex items-start gap-4">
                    <div className="bg-blue-100 dark:bg-blue-900/50 p-3 rounded-full text-blue-600 dark:text-blue-400 mt-1">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h4 className="text-xl font-bold text-slate-800 dark:text-white mb-2">1. Chìa Khóa Khởi Động: Nhập API Key</h4>
                      <p className="text-base text-slate-600 dark:text-slate-400 mb-3">
                        Ứng dụng cần có "API Key" của Google để kết nối trí tuệ nhân tạo.
                      </p>
                      <ul className="list-disc pl-5 space-y-1.5 text-base text-slate-700 dark:text-slate-300">
                        <li>Lấy API Key tại <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">Google AI Studio</a>.</li>
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
                      )}
                      <div className="mt-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/50 p-4 rounded-xl text-sm">
                        <strong className="text-amber-800 dark:text-amber-400 flex items-center gap-2 mb-1">
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                            <path fillRule="evenodd" d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                          </svg>
                          Cảnh Báo Quan Trọng:
                        </strong>
                        <p className="text-amber-900 dark:text-amber-200">
                          Mỗi tài khoản Google có giới hạn token (số từ) sử dụng miễn phí mỗi phút/mỗi ngày. <strong>Tuyệt đối không chia sẻ API Key</strong> của mình cho người khác, vì nếu họ dùng nhiều, tài khoản của Thầy/Cô sẽ bị "Quá tải" và không vẽ hình được nữa!
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Tính năng 2: Quét ảnh & Nhập liệu */}
                <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border-l-4 border-l-teal-500 border-y border-r border-slate-200 dark:border-slate-700 shadow-sm">
                  <div className="flex items-start gap-4">
                    <div className="bg-teal-100 dark:bg-teal-900/50 p-3 rounded-full text-teal-600 dark:text-teal-400 mt-1">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0zM18.75 10.5h.008v.008h-.008V10.5z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h4 className="text-xl font-bold text-slate-800 dark:text-white mb-2">2. Tính Năng Lõi: Chuyển Ảnh/Văn Bản Thành Mã LaTeX</h4>
                      <p className="text-base text-slate-600 dark:text-slate-400 mb-3">
                        Thầy/Cô có 3 cách để yêu cầu AI vẽ hình:
                      </p>
                      <ul className="list-disc pl-5 space-y-2 text-base text-slate-700 dark:text-slate-300">
                        <li><strong>Cách 1 (Dùng ảnh):</strong> Chụp màn hình (nhấn phím <code>PrintScreen</code> hoặc <code>Windows + Shift + S</code>) một đồ thị, hình học từ PDF/Word. Sau đó nhấn chuột vào khu vực bên trái ứng dụng và <code>Ctrl + V</code> (Dán). AI sẽ tự chạy ngay lập tức.</li>
                        <li><strong>Cách 2 (Dùng văn bản):</strong> Nhập mô tả bằng chữ vào ô trống (Ví dụ: <em>"Vẽ tam giác ABC vuông tại A, đường cao AH..."</em>) rồi bấm biểu tượng nút Gửi (Mũi tên lên).</li>
                        <li><strong>Cách 3 (Dùng giọng nói):</strong> Bấm biểu tượng <strong>Micro</strong>, đọc yêu cầu rồi bấm lại để gửi đi (Tiện lợi khi ngại gõ phím).</li>
                      </ul>
                      
                      <div className="mt-4 bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-700/50 p-4 rounded-xl text-sm">
                        <strong className="text-teal-800 dark:text-teal-400 flex items-center gap-2 mb-2">
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                            <path fillRule="evenodd" d="M10 2c-1.716 0-3.408.106-5.07.31C3.806 2.45 3 3.414 3 4.517V17.25a.75.75 0 001.065.682L10 15.032l5.935 2.9A.75.75 0 0017 17.25V4.517c0-1.103-.806-2.068-1.93-2.207A41.403 41.403 0 0010 2zm-.25 6.25a.75.75 0 011.5 0v3.5a.75.75 0 01-1.5 0v-3.5z" clipRule="evenodd" />
                            <path d="M10 14.5a.75.75 0 100-1.5.75.75 0 000 1.5z" />
                          </svg>
                          Mẹo Tối Ưu Tiết Kiệm Token & Tăng Độ Chính Xác:
                        </strong>
                        <ul className="list-decimal pl-5 space-y-1.5 text-teal-900 dark:text-teal-200">
                          <li><strong>Khi cắt ảnh:</strong> Hãy cắt <strong>GỌN</strong> và <strong>SÁT</strong> nhất vào đồ thị/hình vẽ. Đừng cắt dính theo các dòng chữ văn xuôi dài dòng của đề bài vì AI phải mất công đọc chữ, dẫn đến chạy rất chậm và tiêu tốn token vô ích.</li>
                          <li><strong>Đối với Hình Không Gian 3D:</strong> Hình 3D (hình chóp, lăng trụ...) thường là điểm yếu của AI khi chỉ nhìn ảnh. Để tránh lỗi sai, Thầy/Cô nên kết hợp <strong>Vừa dán ảnh vừa nhập thêm mô tả bằng chữ</strong> (VD: <em>"Hình chóp S.ABCD đáy là hình thoi, cạnh SA vuông góc với đáy"</em>).</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Tính năng 3 & 4: Trình Soạn Thảo */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Dọn rác */}
                  <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border-l-4 border-l-emerald-500 border-y border-r border-slate-200 dark:border-slate-700 shadow-sm">
                    <h4 className="text-lg font-bold text-slate-800 dark:text-white mb-2 flex items-center gap-2">
                      <span className="text-xl">🧹</span> 3. Dọn Rác (Lọc Mã Nhanh)
                    </h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                      Đôi lúc AI trả lời kèm những câu nói dài dòng như <em>"Dạ thưa Thầy, đây là mã..."</em>. Thầy/Cô chỉ cần bấm nút <strong>"Dọn rác"</strong> màu đỏ ở trên thanh công cụ.
                    </p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      App sẽ lập tức <strong>xóa mọi chữ dư thừa</strong>, chỉ chắt lọc lại đúng các thẻ mã <code>\begin&#123;tikzpicture&#125;</code> để copy thật sạch sẽ.
                    </p>
                  </div>

                  {/* Viền BBT */}
                  <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border-l-4 border-l-violet-500 border-y border-r border-slate-200 dark:border-slate-700 shadow-sm">
                    <h4 className="text-lg font-bold text-slate-800 dark:text-white mb-2 flex items-center gap-2">
                      <span className="text-xl">🔲</span> 4. Chế Độ "Viền" (Cho BBT)
                    </h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                      Dành riêng khi AI vẽ <strong>Bảng Biến Thiên (BBT)</strong>.
                    </p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Bấm nút <strong>"Viền"</strong> để bật/tắt khung ngoài cùng của bảng. Nút sẽ tự động chèn lệnh <code>nocadre=true</code> để tắt viền đi, giúp bảng nhìn thanh thoát, hiện đại, hòa hợp hơn với chữ viết xung quanh.
                    </p>
                  </div>
                </div>

                {/* Tính năng 5 & 6 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Trải nghiệm Overleaf */}
                  <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border-l-4 border-l-green-600 border-y border-r border-slate-200 dark:border-slate-700 shadow-sm">
                    <h4 className="text-lg font-bold text-slate-800 dark:text-white mb-2 flex items-center gap-2">
                      <span className="text-xl">🚀</span> 5. Biên Dịch Trực Tiếp (Overleaf)
                    </h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                      Sau khi có mã ở cửa sổ bên phải, Thầy/Cô tò mò không biết ảnh vẽ ra trông thế nào?
                    </p>
                    <p className="text-sm text-slate-600 dark:text-slate-400 font-medium">
                      Hãy nhấn nút <span className="text-white bg-green-600 px-2 py-0.5 rounded text-xs">Overleaf</span>. App sẽ mở tab mới, tự động dán mã vào trình biên dịch trực tuyến Overleaf để Thầy/Cô ngắm kết quả trực quan ngay lập tức.
                    </p>
                  </div>

                  {/* Quản lý Thư viện */}
                  <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl border-l-4 border-l-orange-500 border-y border-r border-slate-200 dark:border-slate-700 shadow-sm">
                    <h4 className="text-lg font-bold text-slate-800 dark:text-white mb-2 flex items-center gap-2">
                      <span className="text-xl">📚</span> 6. Lưu Trữ & Quản Lý Mẫu
                    </h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                      Lưu lại những hình vẽ tâm đắc để dùng cho lần sau bằng nút <strong>Lưu Mẫu</strong> ở trên.
                    </p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Mẫu sẽ được xếp vào Thư viện cá nhân ở thanh bên trái. Thầy/Cô có thể tạo Thư mục, phân loại từng chuyên đề (Hàm số, Oxyz, Khối đa diện...) để dễ dàng tìm kiếm.
                    </p>
                  </div>
                </div>

              </div>
              
              {/* Box Cảnh báo Chung */}
              <div className="bg-gradient-to-r from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-700 p-6 rounded-2xl mt-8 border border-slate-300 dark:border-slate-600">
                <h4 className="text-slate-800 dark:text-white font-bold text-lg mb-3 flex items-center gap-2">
                  <span className="text-2xl">⚠️</span> Khắc Phục Sự Cố Nhanh (Troubleshooting)
                </h4>
                <ul className="list-disc pl-5 space-y-2 text-sm text-slate-700 dark:text-slate-300">
                  <li><strong>Lỗi "TypeError/Không phản hồi":</strong> Thường do mất kết nối mạng cục bộ. Hãy làm mới (F5) trang web.</li>
                  <li><strong>Lỗi "Mã sinh ra bị cắt cụt một nửa":</strong> Có thể do chạm trần "giới hạn Token đầu ra" của AI (vì hình quá siêu phức tạp). Hãy yêu cầu AI: <em>"Viết tiếp phần mã còn dang dở"</em> ở ô chat.</li>
                  <li><strong>Sử dụng an toàn:</strong> Dữ liệu Thư viện được lưu tạm trong bộ nhớ trình duyệt web của máy Thầy/Cô. Nếu đổi máy tính hoặc xóa lịch sử duyệt web, dữ liệu sẽ mất. Thầy/Cô nên chủ động copy các mã quan trọng lưu vào file Word/Notepad để dự phòng.</li>
                </ul>
              </div>

            </section>
          </div>

          {/* Footer CTA */}
          <div className="sticky bottom-0 border-t border-slate-200 dark:border-slate-700 bg-white/90 dark:bg-slate-900/90 backdrop-blur-xl p-5 text-center shadow-[0_-15px_20px_-5px_rgba(0,0,0,0.05)]">
            <button 
                onClick={onClose}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-bold py-3.5 px-16 rounded-2xl shadow-xl hover:shadow-blue-500/40 transition-all transform hover:-translate-y-1 text-lg ring-2 ring-white/20"
            >
                Vào Trải Nghiệm Ngay!
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}
