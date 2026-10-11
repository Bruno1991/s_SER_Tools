@echo off
title s_ADB_Tools - JADX-GUI (Visualizador de Codigo)
chcp 65001 >nul
cd /d "%~dp0"
echo =======================================================
echo          s_ADB_Tools - JADX-GUI Visualizador
echo =======================================================
echo.
set /p TARGET="Digite o nome do APK/pacote para abrir (ou Enter para vazio): "
if "%TARGET%"=="" (
    python main.py gui
) else (
    python main.py gui "%TARGET%"
)
