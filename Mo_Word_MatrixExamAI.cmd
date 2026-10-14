@echo off
setlocal
chcp 65001 >nul
title MatrixExamAI - Mo Microsoft Word

:: Lay thu muc hien tai va loai bo dau gach cheo o cuoi
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

:: 1. Kiem tra va anh xa o dia ao X: neu chua co
if not exist "X:\" (
    echo Dang anh xa o dia ao X: -^> "%ROOT_DIR%"...
    subst X: "%ROOT_DIR%"
)

echo ==================================================================
echo   Dang khoi dong Microsoft Word voi Tien ich MatrixExamAI...
echo ==================================================================
start "" "C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"
