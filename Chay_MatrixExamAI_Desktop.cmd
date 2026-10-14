@echo off
setlocal
chcp 65001 >nul
title MatrixExamAI Pro .NET 10 Desktop

set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

if not exist "X:\" (
    echo [1/3] Dang anh xa o dia ao X: -^> "%ROOT_DIR%"...
    subst X: "%ROOT_DIR%"
)

set "TARGET_DIR=X:\desktop_csharp\src\MatrixExamAI.Desktop\bin\Debug\net10.0-windows"
set "EXE_PATH=%TARGET_DIR%\MatrixExamAI.Desktop.exe"

if not exist "%EXE_PATH%" (
    echo [2/3] Dang bien dich du an MatrixExamAI.Desktop C# .NET 10...
    dotnet build "X:\desktop_csharp\src\MatrixExamAI.Desktop\MatrixExamAI.Desktop.csproj"
    if errorlevel 1 (
        echo [LOI] Khong the bien dich du an!
        pause
        exit /b 1
    )
)

echo [3/3] Dang khoi chay MatrixExamAI Pro (.NET 10 Fluent UI)...
cd /d "%TARGET_DIR%"
start "" /D "%TARGET_DIR%" "%EXE_PATH%"
exit /b 0
