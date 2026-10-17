; Inno Setup Script — MatrixExamAI Pro v5.3.0.23 (.NET 10 WPF + Word Add-in)
#define MyAppName "MatrixExamAI Pro"
#define MyAppVersion "5.3.0.23"
#define MyAppPublisher "Do Minh Math"
#define MyAppURL "https://github.com/Do-Miinh-1210/MEA_v5"
#define MyAppExeName "MatrixExamAI.Desktop.exe"

[Setup]
AppId={{E6B4A3C2-1F5D-4E8A-9C7B-3A2F1E4D6C85}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\MatrixExamAI Pro
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=dist\installer
OutputBaseFilename=MatrixExamAI_Pro_Setup
SetupIconFile=assets\app.ico
UninstallDisplayIcon={app}\assets\app.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Languages]
Name: "vietnamese"; MessagesFile: "compiler:Default.isl"

[Messages]
vietnamese.ButtonNext=Tiếp tục >
vietnamese.ButtonBack=< Quay lại
vietnamese.ButtonInstall=Cài đặt
vietnamese.ButtonCancel=Hủy bỏ
vietnamese.ButtonFinish=Hoàn tất
vietnamese.WelcomeLabel1=Chào mừng bạn đến với MatrixExamAI Pro v5.1!
vietnamese.WelcomeLabel2=Trình cài đặt sẽ cài đặt MatrixExamAI Pro v{#MyAppVersion} (.NET 10 WPF + Word Add-in) chính thức vào hệ thống máy tính.%n%nKhuyến nghị: Đóng các ứng dụng Microsoft Word trước khi tiếp tục.%n%nNhấn "Tiếp tục" để bắt đầu cài đặt.
vietnamese.FinishedHeadingLabel=Hoàn tất cài đặt MatrixExamAI Pro!
vietnamese.FinishedLabel=Cài đặt MatrixExamAI Pro v{#MyAppVersion} vào hệ thống thành công!%n%nBiểu tượng đã được tạo trên Màn hình chính (Desktop) và Start Menu.%nAdd-in đã được tích hợp vào Microsoft Word.

[Tasks]
Name: "cleanold"; Description: "Tự động gỡ bỏ các phiên bản cũ trước khi cài đặt mới"; GroupDescription: "Nâng cấp hệ thống:"; Flags: checkedonce
Name: "desktopicon"; Description: "Tạo biểu tượng MatrixExamAI Pro trên Màn hình chính (Desktop)"; GroupDescription: "Biểu tượng lối tắt:"
Name: "wordaddin"; Description: "Tích hợp Add-in vào Microsoft Word (Ribbon MatrixExamAI & TikZ)"; GroupDescription: "Tiện ích mở rộng Microsoft Word:"; Flags: checkedonce

[Files]
Source: "desktop_csharp\publish\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "data\matrix_templates\*"; DestDir: "{app}\data\matrix_templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "word_addon\src\MatrixExamAI.WordAddIn\bin\Debug\net48\*"; DestDir: "{app}\word_addon"; Flags: ignoreversion recursesubdirs createallsubdirs; Tasks: wordaddin
Source: "word_addon\*.ps1"; DestDir: "{app}\word_addon"; Flags: ignoreversion; Tasks: wordaddin
Source: "word_addon\*.reg"; DestDir: "{app}\word_addon"; Flags: ignoreversion; Tasks: wordaddin

[Dirs]
Name: "{app}"; Permissions: users-full
Name: "{app}\logs"; Permissions: users-full
Name: "{app}\storage"; Permissions: users-full
Name: "{app}\word_addon"; Permissions: users-full; Tasks: wordaddin

[Icons]
Name: "{autoprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\app.ico"
Name: "{autoprograms}\{#MyAppName}\Gỡ cài đặt {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\assets\app.ico"; Tasks: desktopicon

[Run]
Filename: "{cmd}"; Parameters: "/c icacls ""{app}"" /grant *S-1-5-32-545:(OI)(CI)F /t /q & icacls ""{app}"" /grant Users:(OI)(CI)F /t /q"; StatusMsg: "Đang cấp quyền ghi cập nhật tự động..."; Flags: runhidden
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File ""{app}\word_addon\register_addin.ps1"""; StatusMsg: "Đang kích hoạt MatrixExamAI Word Add-in..."; Flags: runhidden; Tasks: wordaddin
Filename: "{app}\{#MyAppExeName}"; Description: "Chạy MatrixExamAI Pro ngay sau khi cài đặt"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#MyAppExeName}"; Flags: nowait; Check: ShouldLaunchSilent

[UninstallRun]
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -NoProfile -File ""{app}\word_addon\uninstall_addin.ps1"""; Flags: runhidden

[Code]
function ShouldLaunchSilent: Boolean;
begin
  Result := WizardSilent;
end;

function GetUninstallString(AppIdStr: String): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstallString := '';
  sUnInstPath := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\' + AppIdStr + '_is1';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    if not RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString) then
      if not RegQueryStringValue(HKLM64, sUnInstPath, 'UninstallString', sUnInstallString) then
        RegQueryStringValue(HKCU64, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

procedure UnInstallOldVersion(AppIdStr: String);
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  sUnInstallString := GetUninstallString(AppIdStr);
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    Exec(sUnInstallString, '/VERYSILENT /NORESTART /SUPPRESSMSGBOXES', '', SW_HIDE, ewWaitUntilTerminated, iResultCode);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  iResultCode: Integer;
begin
  if (CurStep = ssInstall) then begin
    Exec('cmd.exe', '/c taskkill /f /im MatrixExamAI.Desktop.exe', '', SW_HIDE, ewWaitUntilTerminated, iResultCode);
    if WizardIsTaskSelected('cleanold') then begin
      UnInstallOldVersion('{B8E5F3A2-7C4D-4E9F-A1B3-2D8F6E4C9A71}');
      UnInstallOldVersion('{C9F2E7B1-8D5C-4F3A-B2E8-1C9A7E5F4D60}');
      UnInstallOldVersion('MEA_v5');
      UnInstallOldVersion('MEA_v4');
    end;
  end;
end;
