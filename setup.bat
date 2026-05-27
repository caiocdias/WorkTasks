@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD="

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 set "PYTHON_CMD=python"
)

if "%PYTHON_CMD%"=="" (
    echo Python 3 nao encontrado.
    echo Instale o Python em https://www.python.org/downloads/ ou habilite o Python Launcher para Windows.
    pause
    exit /b 1
)

if not exist "%~dp0venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    %PYTHON_CMD% -m venv "%~dp0venv"
    if errorlevel 1 (
        echo Nao foi possivel criar o ambiente virtual.
        pause
        exit /b 1
    )
)

call "%~dp0venv\Scripts\activate.bat"

echo Instalando requirements...
python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 exit /b 1

python -c "import tkinter"
if errorlevel 1 (
    echo Tkinter nao esta disponivel nesta instalacao do Python.
    echo Reinstale o Python marcando a opcao tcl/tk and IDLE.
    pause
    exit /b 1
)

echo Setup concluido. Use abrir_app.bat para iniciar o aplicativo.
pause
exit /b 0
