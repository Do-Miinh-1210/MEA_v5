$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop "MatrixExamAI Pro.lnk"
$sc = $ws.CreateShortcut($shortcutPath)
$sc.TargetPath = "M:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\desktop_csharp\publish\MatrixExamAI.Desktop.exe"
$sc.WorkingDirectory = "M:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\desktop_csharp\publish"
$sc.IconLocation = "M:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\assets\icon_MaTrixExamAI.ico,0"
$sc.Save()
Write-Output "User Shortcut created at $shortcutPath"

try {
    $pubDesktop = [Environment]::GetFolderPath('CommonDesktopDirectory')
    $pubShortcut = Join-Path $pubDesktop "MatrixExamAI Pro.lnk"
    $scPub = $ws.CreateShortcut($pubShortcut)
    $scPub.TargetPath = "M:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\desktop_csharp\publish\MatrixExamAI.Desktop.exe"
    $scPub.WorkingDirectory = "M:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\desktop_csharp\publish"
    $scPub.IconLocation = "M:\IT\Phần mềm biên soạn tài liệu\MEA_v5.0\assets\icon_MaTrixExamAI.ico,0"
    $scPub.Save()
    Write-Output "Public Shortcut updated at $pubShortcut"
} catch {
    Write-Output "Could not update public desktop shortcut: $($_.Exception.Message)"
}
