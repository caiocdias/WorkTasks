#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
    printf '%s\n' "Ambiente virtual nao encontrado."
    printf '%s\n' "Execute ./setup.sh uma vez antes de abrir o aplicativo."
    exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/run.py"

printf '%s\n' "Python 3 nao encontrado."
printf '%s\n' "No Ubuntu, instale com: sudo apt install python3 python3-tk"
exit 1
