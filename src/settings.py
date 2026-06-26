from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Mapping


TASKS_FILE_NAME = "tasks.json"
DEFAULT_THEME = "light"
VALID_THEMES = {"light", "dark"}


def default_config_dir(os_name: str | None = None, env: Mapping[str, str] | None = None) -> Path:
    current_os = os_name if os_name is not None else os.name
    current_env = env if env is not None else os.environ

    if current_os == "nt":
        appdata = current_env.get("APPDATA")
        if appdata:
            return Path(appdata) / "WorkTasks"
        return Path.home() / "AppData" / "Roaming" / "WorkTasks"

    xdg_config_home = current_env.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "work-tasks"
    return Path.home() / ".config" / "work-tasks"


def default_config_file() -> Path:
    return default_config_dir() / "settings.json"


APP_CONFIG_DIR = default_config_dir()
CONFIG_FILE = default_config_file()


class AppSettings:
    def __init__(self, config_file: str | Path | None = None) -> None:
        self.config_file = Path(config_file) if config_file else default_config_file()

    def _load_payload(self) -> dict[str, object]:
        if not self.config_file.exists():
            return {}

        try:
            with self.config_file.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except (OSError, json.JSONDecodeError):
            return {}

        if not isinstance(payload, dict):
            return {}

        return payload

    def _save_payload(self, payload: dict[str, object]) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.config_file.parent,
            delete=False,
            suffix=".tmp",
        ) as temp_file:
            json.dump(payload, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
            temp_name = temp_file.name

        Path(temp_name).replace(self.config_file)

    def load_data_folder(self) -> Path | None:
        payload = self._load_payload()

        data_folder = payload.get("data_folder")
        if not isinstance(data_folder, str) or not data_folder.strip():
            return None

        return Path(data_folder).expanduser()

    def save_data_folder(self, data_folder: str | Path) -> Path:
        resolved_folder = Path(data_folder).expanduser().resolve()
        resolved_folder.mkdir(parents=True, exist_ok=True)

        payload = self._load_payload()
        payload["data_folder"] = str(resolved_folder)
        self._save_payload(payload)
        return resolved_folder

    def load_theme(self) -> str:
        payload = self._load_payload()
        theme = payload.get("theme")
        if isinstance(theme, str) and theme in VALID_THEMES:
            return theme
        return DEFAULT_THEME

    def save_theme(self, theme: str) -> str:
        if theme not in VALID_THEMES:
            raise ValueError(f"Tema invalido: {theme}")

        payload = self._load_payload()
        payload["theme"] = theme
        self._save_payload(payload)
        return theme

    def tasks_file(self, data_folder: str | Path) -> Path:
        return Path(data_folder).expanduser() / TASKS_FILE_NAME
