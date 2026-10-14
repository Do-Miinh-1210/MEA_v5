Set WshShell = CreateObject("WScript.Shell")

' 1. Kiem tra o dia ao X:
Set fso = CreateObject("Scripting.FileSystemObject")
If Not fso.FolderExists("X:\") Then
    Dim scriptDir
    scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
    WshShell.Run "subst X: """ & scriptDir & """", 0, True
End If

' 2. Khoi chay ung dung Desktop C# .NET 10
Dim exePath, workingDir
exePath = "X:\desktop_csharp\src\MatrixExamAI.Desktop\bin\Debug\net10.0-windows\MatrixExamAI.Desktop.exe"
workingDir = "X:\desktop_csharp\src\MatrixExamAI.Desktop\bin\Debug\net10.0-windows"

If fso.FileExists(exePath) Then
    WshShell.CurrentDirectory = workingDir
    WshShell.Run """" & exePath & """", 1, False
Else
    WshShell.Run "dotnet build ""X:\desktop_csharp\src\MatrixExamAI.Desktop\MatrixExamAI.Desktop.csproj""", 1, True
    WshShell.CurrentDirectory = workingDir
    WshShell.Run """" & exePath & """", 1, False
End If
