@echo off
chcp 65001 >nul
title Chess.com Bots - Catalogo e Inspecao
cd /d "%~dp0"

echo ========================================================
echo       Chess.com - Catalogo de Bots e Motores
echo ========================================================
echo.

python main.py bots summary
echo.
set /p botname="Deseja ver a ficha tecnica de algum bot? Digite o nome (ou Enter para sair): "
if not "%botname%"=="" (
    python main.py bots info "%botname%"
)

pause
