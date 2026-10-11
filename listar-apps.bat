@echo off
title s_ADB_Tools - Listar Apps Instalados
chcp 65001 >nul
cd /d "%~dp0"
python main.py list
echo.
pause
