@echo off
setlocal
chcp 65001 >nul
title MatrixExamAI Pro - Python Version

set "PYTHON_EXE=C:\Users\domin\AppData\Local\Python\bin\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

cd /d "%~dp0"
"%PYTHON_EXE%" main.py
