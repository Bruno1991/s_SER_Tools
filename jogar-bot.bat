@echo off
chcp 65001 >nul
title Chess.com Bots - Partida Interativa
cd /d "%~dp0"

echo ========================================================
echo       Chess.com - Partida contra Bot no Terminal
echo ========================================================
echo.
echo Exemplos de Bots disponiveis:
echo   - Martin (Elo 250, Iniciante)
echo   - Nelson (Elo 1300, Ataques de Dama)
echo   - GothamChess (Elo 1800, Criador)
echo   - Hikaru (Elo 2820, Super GM)
echo   - Fabian (Elo 250, Bot Premium liberado)
echo.

set /p botname="Nome do bot que deseja enfrentar [Padrao: Martin]: "
if "%botname%"=="" set botname=Martin

python main.py bots play "%botname%"

pause
