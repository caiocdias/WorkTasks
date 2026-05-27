@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    start "" py -3 "%~dp0run.py"
    exit /b 0
)

where python >nul 2>nul
if %errorlevel%==0 (
    start "" python "%~dp0run.py"
    exit /b 0
)

echo Python 3 nao encontrado.
echo Instale o Python em https://www.python.org/downloads/ ou habilite o Python Launcher para Windows.
pause
exit /b 1
