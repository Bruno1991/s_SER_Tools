@echo off
title s_ADB_Tools - Abrir JPEXS FFDec GUI
chcp 65001 >nul
cd /d "%~dp0"
echo =======================================================
echo    s_ADB_Tools - JPEXS Free Flash Decompiler GUI
echo =======================================================
echo.
set /p TARGET="Digite o nome do pacote ou SWF a carregar (ou pressione ENTER para abrir vazio): "
echo.
if "%TARGET%"=="" (
    python main.py ffdec-gui
) else (
    python main.py ffdec-gui "%TARGET%"
)
echo.
pause
