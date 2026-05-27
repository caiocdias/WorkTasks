#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN=python
else
    printf '%s\n' "Python 3 nao encontrado."
    printf '%s\n' "No Ubuntu, instale com: sudo apt install python3 python3-venv python3-tk"
    exit 1
fi

if [ ! -x "$SCRIPT_DIR/venv/bin/python" ]; then
    printf '%s\n' "Criando ambiente virtual..."
    if ! "$PYTHON_BIN" -m venv "$SCRIPT_DIR/venv"; then
        printf '%s\n' "Nao foi possivel criar o ambiente virtual."
        printf '%s\n' "No Ubuntu, instale com: sudo apt install python3-venv python3-tk"
        exit 1
    fi
fi

. "$SCRIPT_DIR/venv/bin/activate"

printf '%s\n' "Instalando requirements..."
python -m pip install -r "$SCRIPT_DIR/requirements.txt"

if ! python -c "import tkinter"; then
    printf '%s\n' "Tkinter nao esta disponivel."
    printf '%s\n' "No Ubuntu, instale com: sudo apt install python3-tk"
    exit 1
fi

printf '%s\n' "Setup concluido. Use ./abrir_app.sh para iniciar o aplicativo."
