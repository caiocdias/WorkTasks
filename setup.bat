@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON_CMD="

call :try_python py -3
if not defined PYTHON_CMD call :try_python python
if not defined PYTHON_CMD call :try_python python3
if not defined PYTHON_CMD call :find_python_in "%LocalAppData%\Programs\Python"
if not defined PYTHON_CMD call :find_python_in "%ProgramFiles%"
if not defined PYTHON_CMD call :find_python_in "%ProgramFiles(x86)%"
if not defined PYTHON_CMD call :find_python_in "C:\"
if not defined PYTHON_CMD call :ask_python_path

if not defined PYTHON_CMD (
    echo Python 3 nao encontrado.
    echo Instale o Python em https://www.python.org/downloads/ ou adicione o Python ao PATH.
    echo Se o Python ja estiver instalado, execute:
    echo   py -3 -m venv venv
    echo ou informe o caminho completo do python.exe no PATH do Windows.
    pause
    exit /b 1
)

echo Usando Python: %PYTHON_CMD%

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

:try_python
if defined PYTHON_CMD exit /b 0
%* -c "import sys; raise SystemExit(0 if sys.version_info[0] == 3 else 1)" >nul 2>nul
if errorlevel 1 exit /b 0
set "PYTHON_CMD=%*"
exit /b 0

:find_python_in
if defined PYTHON_CMD exit /b 0
set "PYTHON_ROOT=%~1"
if "%PYTHON_ROOT%"=="" exit /b 0
if not exist "%PYTHON_ROOT%" exit /b 0

set "PYTHON_PATTERN=%PYTHON_ROOT%\Python*"
if "%PYTHON_ROOT:~-1%"=="\" set "PYTHON_PATTERN=%PYTHON_ROOT%Python*"

for /d %%D in ("%PYTHON_PATTERN%") do (
    if exist "%%~fD\python.exe" (
        call :try_python "%%~fD\python.exe"
        if defined PYTHON_CMD exit /b 0
    )
)

exit /b 0

:ask_python_path
if defined PYTHON_CMD exit /b 0
echo Python 3 nao foi encontrado automaticamente.
echo Se ele ja estiver instalado, cole abaixo o caminho completo do python.exe.
set "PYTHON_PATH="
set /p "PYTHON_PATH=Caminho do python.exe (Enter para cancelar): "
if not defined PYTHON_PATH exit /b 0
set "PYTHON_PATH=%PYTHON_PATH:"=%"
call :try_python "%PYTHON_PATH%"
if not defined PYTHON_CMD echo O caminho informado nao parece ser um Python 3 valido.
exit /b 0
