const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

const oldState = `  const [showEmailManager, setShowEmailManager] = useState<boolean>(false);`;
const newState = `  const [showEmailManager, setShowEmailManager] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);`;

content = content.replace(oldState, newState);

const oldToggle = `  const toggleTheme = () => {`;
const newToggle = `  const toggleFullScreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((err) => {
        showToast(\`Error attempting to enable fullscreen: \${err.message}\`);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const toggleTheme = () => {`;

content = content.replace(oldToggle, newToggle);

const oldHdsdButton = `          {/* HDSD button */}
          <button`;
const newHdsdButton = `          {/* Full Màn hình button */}
          <button
            onClick={toggleFullScreen}
            className="flex items-center gap-1 text-purple-600 dark:text-purple-500 font-bold text-sm px-2 py-1 rounded-md hover:bg-purple-50 dark:hover:bg-purple-950/30 transition-colors whitespace-nowrap mr-2 bg-transparent border-none"
            title={isFullscreen ? "Thu nhỏ màn hình" : "Toàn màn hình"}
          >
            {isFullscreen ? (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
              </svg>
            )}
            Full Màn hình
          </button>

          {/* HDSD button */}
          <button`;

content = content.replace(oldHdsdButton, newHdsdButton);

fs.writeFileSync('App.tsx', content);
