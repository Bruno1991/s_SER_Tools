@echo off
title s_ADB_Tools - Descompilar APK
chcp 65001 >nul
cd /d "%~dp0"
echo =======================================================
echo          s_ADB_Tools - Descompilador de APKs
echo =======================================================
echo.
set /p TARGET="Digite o nome do pacote ou APK (ex: com.smartexpenditure): "
if "%TARGET%"=="" (
    echo Nenhum pacote informado.
    pause
    exit /b
)
echo.
python main.py decompile "%TARGET%"
echo.
pause
