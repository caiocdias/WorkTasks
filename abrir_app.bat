@echo off
setlocal
cd /d "%~dp0"

set "VENV_PYTHON=%~dp0venv\Scripts\pythonw.exe"
if not exist "%VENV_PYTHON%" set "VENV_PYTHON=%~dp0venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Ambiente virtual nao encontrado.
    echo Execute setup.bat uma vez antes de abrir o aplicativo.
    pause
    exit /b 1
)

start "" "%VENV_PYTHON%" "%~dp0run.py"
exit /b 0
