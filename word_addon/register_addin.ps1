# Register MatrixExamAI Word Add-in for current user (No Admin Required)
$ErrorActionPreference = "Stop"

$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dllPath = Join-Path $baseDir "MatrixExamAI.WordAddIn.dll"
if (-not (Test-Path "$dllPath")) {
    $dllPath = Join-Path $baseDir "src\MatrixExamAI.WordAddIn\bin\Debug\net48\MatrixExamAI.WordAddIn.dll"
}
$regFile = Join-Path $baseDir "addon_x64.reg"
$hkcuRegFile = Join-Path $baseDir "addon_hkcu.reg"

Write-Host "1. Generating COM registration script with RegAsm..." -ForegroundColor Cyan
& "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\RegAsm.exe" "$dllPath" /codebase /regfile:"$regFile"

if (-not (Test-Path "$regFile")) {
    throw "Failed to generate $regFile"
}

Write-Host "2. Converting to Per-User (HKCU\Software\Classes) format..." -ForegroundColor Cyan
$raw = Get-Content -Path "$regFile" -Raw
$hkcu = $raw.Replace("HKEY_CLASSES_ROOT", "HKEY_CURRENT_USER\Software\Classes")

$extra = @"

[HKEY_CURRENT_USER\Software\Microsoft\Office\Word\Addins\MatrixExamAI.WordAddIn]
"FriendlyName"="MatrixExamAI Word Add-in"
"Description"="Trợ lý Soạn thảo AI & Vẽ hình TikZ MatrixExamAI"
"LoadBehavior"=dword:00000003
"CommandLineSafe"=dword:00000000

[HKEY_CURRENT_USER\Software\Classes\MatrixExamAI.WordAddIn.Connect\CLSID]
@="{9B302F31-155D-4A2D-BE45-219C1D9D6C99}"

"@

$fullContent = $hkcu + "`r`n" + $extra
[System.IO.File]::WriteAllText($hkcuRegFile, $fullContent, [System.Text.Encoding]::Unicode)

Write-Host "3. Importing into Windows Registry..." -ForegroundColor Cyan
$proc = Start-Process reg.exe -ArgumentList "import `"$hkcuRegFile`"" -Wait -PassThru
if ($proc.ExitCode -eq 0) {
    Write-Host "SUCCESS: MatrixExamAI Word Add-in registered for Current User!" -ForegroundColor Green
} else {
    throw "reg import failed with exit code $($proc.ExitCode)"
}

# Verify Word Addin key
Write-Host "4. Verifying registry keys..." -ForegroundColor Cyan
Get-ItemProperty "HKCU:\Software\Microsoft\Office\Word\Addins\MatrixExamAI.WordAddIn" | Format-List FriendlyName, Description, LoadBehavior
