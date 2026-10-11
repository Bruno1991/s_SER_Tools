@echo off
title s_ADB_Tools - Extrator de APKs
chcp 65001 >nul
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo Ocorreu um erro na execucao. Pressione qualquer tecla para sair.
    pause >nul
)
