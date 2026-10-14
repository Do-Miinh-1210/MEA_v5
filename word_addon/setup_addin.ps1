# setup_addin.ps1 - Cài đặt Tiện ích MatrixExamAI Word Add-in (Không cần quyền Admin)
param (
    [switch]$ForceRebuild = $false
)

$ErrorActionPreference = "Stop"
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host " MatrixExamAI - Trợ lý Soạn thảo AI & Vẽ hình TikZ trong Word   " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Đảm bảo ánh xạ ổ đĩa ảo X: (tránh lỗi Unicode tiếng Việt trên .NET 4.8)
$repoRoot = "m:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0"
if (-not (Test-Path "X:\")) {
    Write-Host "[1/5] Ánh xạ ổ đĩa ảo X: -> $repoRoot..." -ForegroundColor Yellow
    subst X: "$repoRoot"
} else {
    Write-Host "[1/5] Ổ đĩa ảo X: đã sẵn sàng." -ForegroundColor Green
}

try {
    $runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    Set-ItemProperty -Path $runKey -Name "MatrixExamAI_DriveX" -Value "cmd.exe /c subst X: `"$repoRoot`"" -Force -ErrorAction SilentlyContinue
} catch {}

$addonDir = "X:\word_addon"
$solutionFile = Join-Path $addonDir "MatrixExamAI.sln"
$dllPath = Join-Path $addonDir "src\MatrixExamAI.WordAddIn\bin\Debug\net48\MatrixExamAI.WordAddIn.dll"

# 2. Biên dịch Solution nếu cần
if ($ForceRebuild -or (-not (Test-Path $dllPath))) {
    Write-Host "[2/5] Biên dịch giải pháp C# .NET..." -ForegroundColor Yellow
    dotnet build "$solutionFile" -c Debug
} else {
    Write-Host "[2/5] Bản build DLL đã sẵn sàng." -ForegroundColor Green
}

# 3. Đăng ký COM Add-in cho Người dùng hiện tại (HKCU - No Admin Required)
Write-Host "[3/5] Đăng ký COM Add-in vào Windows Registry (HKCU)..." -ForegroundColor Yellow
& (Join-Path $addonDir "register_addin.ps1")

# 4. Tự động đồng bộ khóa API từ MEA sang Word Add-in
Write-Host "[4/5] Đồng bộ API Key (Gemini 3.8 Flash, 9Router) từ hệ thống..." -ForegroundColor Yellow
$syncScript = Join-Path $addonDir "sync_keys.py"
if (Test-Path $syncScript) {
    py -3 "$syncScript"
}

# 5. Kiểm tra kết nối với Microsoft Word
Write-Host "[5/5] Kiểm tra nhận diện trên Microsoft Word..." -ForegroundColor Yellow
$wordAvailable = $false
try {
    $w = New-Object -ComObject Word.Application
    $w.Visible = $false
    foreach ($a in $w.COMAddIns) {
        if ($a.ProgId -like "*MatrixExamAI*") {
            $wordAvailable = [bool]$a.Connect
            break
        }
    }
    $w.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($w) | Out-Null
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
} catch {
    $wordAvailable = $false
}

if ($wordAvailable) {
    Write-Host "==================================================================" -ForegroundColor Green
    Write-Host " CÀI ĐẶT THÀNH CÔNG! Word Add-in đã kích hoạt (Connect = True)   " -ForegroundColor Green
    Write-Host " Khởi động Microsoft Word, bạn sẽ thấy thanh Ribbon 'MatrixExamAI'!" -ForegroundColor Green
    Write-Host "==================================================================" -ForegroundColor Green
} else {
    Write-Host "[CẢNH BÁO] Add-in đã đăng ký xong registry nhưng Word COM test trả về false. Có thể Word đang mở." -ForegroundColor Yellow
}
