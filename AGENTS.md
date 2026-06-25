# Repository Guidelines

## Project Structure & Module Organization

This is a small Python desktop app for managing local work tasks. The entry point is `run.py`, which calls `src.app.main()`. Application code lives in `src/`: `app.py` contains the Tkinter UI, `task_model.py` defines task data and date/status helpers, `storage.py` handles JSON persistence, `settings.py` manages the configured data folder, and `xlsx_export.py` writes spreadsheet exports. Tests live in `tests/` and mirror the modules they cover, for example `tests/test_storage.py` and `tests/test_xlsx_export.py`. Setup and launch helpers are provided as platform-specific scripts at the repo root.

## Build, Test, and Development Commands

- `.\setup.bat` or `sh ./setup.sh`: create the virtual environment and install `requirements.txt`.
- `.\abrir_app.bat` or `sh ./abrir_app.sh`: launch the desktop app through the local virtual environment.
- `.\venv\Scripts\python.exe run.py`: run the app manually on Windows.
- `./venv/bin/python run.py`: run the app manually on Linux.
- `.\venv\Scripts\python.exe -m unittest discover -s tests`: run the test suite on Windows.
- `./venv/bin/python -m unittest discover -s tests`: run the test suite on Linux.

The project currently uses only the Python standard library. On Linux, Tkinter may require the system package `python3-tk`.

## Coding Style & Naming Conventions

Use Python 3 with 4-space indentation, type hints, and `from __future__ import annotations` as in the existing modules. Prefer `pathlib.Path` for filesystem paths and keep persistence code explicit about UTF-8 encoding. Module, function, and variable names use `snake_case`; classes use `PascalCase`; constants use `UPPER_SNAKE_CASE`. Keep UI-facing labels consistent with the app's existing Portuguese text.

## Testing Guidelines

Tests use the standard `unittest` framework. Add new tests under `tests/` with filenames matching `test_*.py` and test methods named `test_*`. Use `tempfile.TemporaryDirectory()` for filesystem behavior so tests do not touch real user data. Cover model validation, storage edge cases, settings paths, and export output when changing related modules.

## Commit & Pull Request Guidelines

Recent commits use short, imperative summaries such as `Add related person field to tasks` and `Resizable side bar`. Keep commit subjects concise and describe the user-visible change. Pull requests should include a brief description, test results, linked issues when applicable, and screenshots or notes for Tkinter UI changes.

## Security & Configuration Tips

Do not commit generated `tasks.json`, virtual environments, or local settings. The app stores configuration outside the repo (`%APPDATA%\WorkTasks\settings.json` on Windows or `${XDG_CONFIG_HOME:-~/.config}/work-tasks/settings.json` on Linux), while task data is saved in the folder selected by the user.
