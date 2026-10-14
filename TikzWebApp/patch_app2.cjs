const fs = require('fs');
let content = fs.readFileSync('App.tsx', 'utf8');

const oldComponentCall = `<AIAssistant
          width={aiAssistantWidth}
          setCode={setCurrentCode}
          onApiKeyInvalid={handleApiKeyInvalid}
          isReadOnly={isReadOnly}
          onFilesDropped={handleFilesDropped}
          userLibrary={sharedLibrary}
          isNoteEnabled={isNoteEnabled}
          isBbtNoFrame={isBbtNoFrame}
          onBoilerplateRemoved={() => {
            showToast('Đã tự động xóa mẫu code TikZ trùng lặp.', 6000);
          }}
          currentCode={currentCode}
        />`;

const newComponentCall = `<AIAssistant
          width={aiAssistantWidth}
          setCode={setCurrentCode}
          onApiKeyInvalid={handleApiKeyInvalid}
          isReadOnly={isReadOnly}
          onFilesDropped={handleFilesDropped}
          userLibrary={sharedLibrary}
          isNoteEnabled={isNoteEnabled}
          isBbtNoFrame={isBbtNoFrame}
          onBoilerplateRemoved={() => {
            showToast('Đã tự động xóa mẫu code TikZ trùng lặp.', 6000);
          }}
          currentCode={currentCode}
          onLoadingChange={setIsLoading}
        />`;

content = content.replace(oldComponentCall, newComponentCall);

fs.writeFileSync('App.tsx', content);
