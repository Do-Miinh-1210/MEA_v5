@echo off
setlocal
chcp 65001 > nul
set "PYTHONUTF8=1"
title MEA v4/v5 - Full Build

echo.
echo  ==========================================================
echo   MEA v4/v5 - Build toan bo EXE + manifest + installer
echo   Su dung upgrade_app.py + PyInstaller + Inno Setup 6
echo  ==========================================================
echo.

cd /d "%~dp0"
echo  Thu muc: %CD%
echo.

echo %CD% | findstr /i "System32" > nul
if %errorlevel%==0 (
    echo  [LOI] Dang chay tu System32 - khong hop le.
    echo  Hay chay file build_exe.bat ngay trong thu muc du an.
    pause
    exit /b 1
)

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo  [LOI] Chua cai Python 3.12+
    echo  Tai tai: https://python.org/downloads
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [OK] %%v

echo.
echo  [1/5] Dong bo dependency build/runtime...
python -m pip install --upgrade pip
if %errorlevel% neq 0 goto :fail
python -m pip install --upgrade -r requirements.txt -r requirements-dev.txt
if %errorlevel% neq 0 goto :fail
python -m pip install --upgrade pyinstaller openpyxl
if %errorlevel% neq 0 goto :fail
python -m pip check > "%TEMP%\mea_build_pip_check.log" 2>&1
if %errorlevel% neq 0 (
    findstr /i /c:"supafunc " "%TEMP%\mea_build_pip_check.log" > nul && (
        echo  [WARN] pip check bao loi package ngoai du an ^(supafunc^). Tiep tuc build desktop.
        type "%TEMP%\mea_build_pip_check.log"
    ) || (
        type "%TEMP%\mea_build_pip_check.log"
        goto :fail
    )
)

echo.
echo  [2/5] Chay fast release tests...
python tools\upgrade_app.py --test-mode fast --test-only
if %errorlevel% neq 0 goto :fail

echo.
echo  [3/5] Build V4 + Admin + V5 qua staging + selftest...
python tools\upgrade_app.py --test-mode none
if %errorlevel% neq 0 goto :fail

echo.
echo  [4/5] Tao installer scripts...
python -c "import build_helper; build_helper.generate_inno_setup()"
if %errorlevel% neq 0 goto :fail
python build_v5_installer.py
if %errorlevel% neq 0 goto :fail

echo.
echo  [5/5] Build V4 installer neu co Inno Setup...
set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
)

if defined ISCC (
    echo  [OK] Tim thay Inno Setup tai: %ISCC%
    "%ISCC%" /Q installer.iss
    if %errorlevel% neq 0 goto :fail
    if exist "installer_v5.iss" (
        "%ISCC%" /Q installer_v5.iss
    )
) else (
    echo  [INFO] Khong tim thay Inno Setup 6 - bo qua compile MEA Setup.exe
    echo         installer.iss va installer_v5.iss van da duoc cap nhat.
)

echo.
echo  ==========================================================
echo   BUILD THANH CONG
echo.
echo   Artifact chinh:
echo     - dist\MEA_v4.exe
echo     - dist\MEA_v4_Admin.exe
echo     - dist\MEA_v5_alpha.exe
echo     - dist\update_manifest_v4.json
echo     - dist\update_manifest_v5.json
if exist "dist\installer\MEA_v4_Setup.exe" echo     - dist\installer\MEA_v4_Setup.exe
if exist "dist\installer\MEA_v5_Setup.exe" echo     - dist\installer\MEA_v5_Setup.exe
echo  ==========================================================
echo.
explorer dist 2>nul
exit /b 0

:fail
echo.
echo  [LOI] Build that bai. Xem thong bao o tren.
pause
exit /b 1
