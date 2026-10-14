@echo off
setlocal
chcp 65001 >nul
title MatrixExamAI - Cai dat Word Add-in

echo ==================================================================
echo   MatrixExamAI - Tien ich Word Add-in (Soan thao AI va Ve TikZ)
echo ==================================================================
echo.

:: Lay thu muc hien tai va loai bo dau gach cheo o cuoi
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

:: 1. Kiem tra va anh xa o dia ao X:
if not exist "X:\" (
    echo [1/3] Dang anh xa o dia ao X: -^> "%ROOT_DIR%"...
    subst X: "%ROOT_DIR%"
) else (
    echo [1/3] O dia ao X: da san sang.
)

:: 2. Kiem tra file script tren o dia X:
if not exist "X:\word_addon\setup_addin.ps1" (
    echo [LOI] Khong tim thay file X:\word_addon\setup_addin.ps1!
    echo Vui long kiem tra thu muc word_addon.
    pause
    exit /b 1
)

:: 3. Chay script cai dat bang PowerShell
echo [2/3] Dang thuc thi cai dat MatrixExamAI Word Add-in...
powershell -NoProfile -ExecutionPolicy Bypass -File "X:\word_addon\setup_addin.ps1"

echo.
echo [3/3] Hoan tat quy trinh cai dat.
pause
