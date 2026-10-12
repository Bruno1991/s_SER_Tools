@echo off
title s_ADB_Tools - Descompilador SWF / ActionScript 3 (FFDec)
chcp 65001 >nul
cd /d "%~dp0"
echo =======================================================
echo    s_ADB_Tools - Descompilador Flash / SWF (FFDec)
echo =======================================================
echo.
set /p TARGET="Digite o nome do pacote, APK ou arquivo .swf (ex: air.com.hypah.io.slither): "
if "%TARGET%"=="" (
    echo Nenhum pacote ou SWF informado.
    pause
    exit /b
)
echo.
python main.py ffdec "%TARGET%"
echo.
pause
