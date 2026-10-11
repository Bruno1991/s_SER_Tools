@echo off
title s_ADB_Tools - Extrator Adobe AIR / Flash (SWF)
chcp 65001 >nul
cd /d "%~dp0"
echo =======================================================
echo    s_ADB_Tools - Extrator Adobe AIR / Flash (SWF)
echo =======================================================
echo.
set /p TARGET="Digite o nome do pacote ou APK (ex: air.com.hypah.io.slither): "
if "%TARGET%"=="" (
    echo Nenhum pacote informado.
    pause
    exit /b
)
echo.
python main.py air "%TARGET%"
echo.
pause
