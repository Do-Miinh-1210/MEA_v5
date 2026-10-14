# uninstall_addin.ps1 - Gỡ bỏ cài đặt MatrixExamAI Word Add-in
$ErrorActionPreference = "SilentlyContinue"

Write-Host "Đang gỡ bỏ tiện ích MatrixExamAI Word Add-in..." -ForegroundColor Cyan

# 1. Xóa các khóa đăng ký trong HKCU Office Word Addins
$subKeys = @(
    "HKCU:\Software\Microsoft\Office\Word\Addins\MatrixExamAI.WordAddIn",
    "HKCU:\Software\Microsoft\Office\Word\Addins\MatrixExamAI.WordAddIn.Connect"
)

foreach ($key in $subKeys) {
    if (Test-Path $key) {
        Remove-Item -Path $key -Recurse -Force
        Write-Host "Đã xóa $key" -ForegroundColor Yellow
    }
}

# 2. Xóa các khóa COM Classes đã đăng ký cho người dùng
$classKeys = @(
    "HKCU:\Software\Classes\MatrixExamAI.WordAddIn",
    "HKCU:\Software\Classes\MatrixExamAI.WordAddIn.Connect",
    "HKCU:\Software\Classes\MatrixExamAI.WordAddIn.SidebarUserControl",
    "HKCU:\Software\Classes\MatrixExamAI.WordAddIn.Ribbon.RibbonController",
    "HKCU:\Software\Classes\CLSID\{9B302F31-155D-4A2D-BE45-219C1D9D6C99}",
    "HKCU:\Software\Classes\CLSID\{7A4C62A1-04EA-4D88-8EF5-6A94CE015F33}",
    "HKCU:\Software\Classes\CLSID\{43A7C8E2-2C99-4A94-BFD1-85E951E91C61}"
)

foreach ($key in $classKeys) {
    if (Test-Path $key) {
        Remove-Item -Path $key -Recurse -Force
    }
}

Write-Host "Hoàn tất gỡ bỏ MatrixExamAI Word Add-in!" -ForegroundColor Green
