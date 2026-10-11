@echo off
title s_ADB_Tools - Servidor Web Local
chcp 65001 >nul
cd /d "%~dp0"
python web_server.py
if errorlevel 1 (
    echo.
    echo Ocorreu um erro ao iniciar o servidor web.
    pause
)
