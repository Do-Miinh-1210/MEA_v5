const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

const oldEffect = `    // Check if it's the first time opening the app
    const hasSeenGuide = localStorage.getItem('TIKZ_HAS_SEEN_GUIDE');
    if (!hasSeenGuide) {
      setShowUserGuideModal(true);
      localStorage.setItem('TIKZ_HAS_SEEN_GUIDE', 'true');
    }`;

const newEffect = `    // Check if it's the first time opening the app
    const hasSeenGuide = localStorage.getItem('TIKZ_HAS_SEEN_GUIDE');
    const storedApiKey = localStorage.getItem('GEMINI_USER_KEY');
    
    if (!storedApiKey) {
      setShowUserGuideModal(true);
      setTimeout(() => {
        showToast('Hãy đọc HDSD để nhập API key và cách dùng App', 8000);
      }, 500);
    } else if (!hasSeenGuide) {
      setShowUserGuideModal(true);
      localStorage.setItem('TIKZ_HAS_SEEN_GUIDE', 'true');
    }`;

content = content.replace(oldEffect, newEffect);

const oldUserGuide = `{showUserGuideModal && (
        <UserGuideModal  
          onClose={() => setShowUserGuideModal(false)} 
        />
      )}`;

const newUserGuide = `{showUserGuideModal && (
        <UserGuideModal  
          onClose={() => setShowUserGuideModal(false)}
          hasApiKey={hasApiKey}
          onSaveApiKey={(key) => {
            handleSaveApiKey(key);
            if (key && key.trim().length > 10) {
               setShowUserGuideModal(false);
            }
          }}
        />
      )}`;

content = content.replace(oldUserGuide, newUserGuide);

fs.writeFileSync('App.tsx', content);
