from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.settings import AppSettings, DEFAULT_THEME, TASKS_FILE_NAME, default_config_dir


class AppSettingsTest(unittest.TestCase):
    def test_save_and_load_data_folder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "settings.json"
            data_folder = Path(directory) / "database"
            settings = AppSettings(config_file)

            saved_folder = settings.save_data_folder(data_folder)

            self.assertEqual(saved_folder, data_folder.resolve())
            self.assertEqual(settings.load_data_folder(), data_folder.resolve())
            self.assertTrue(data_folder.exists())

    def test_tasks_file_uses_selected_folder(self) -> None:
        settings = AppSettings(Path("settings.json"))

        self.assertEqual(settings.tasks_file(Path("chosen")), Path("chosen") / TASKS_FILE_NAME)

    def test_invalid_settings_file_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "settings.json"
            config_file.write_text("not json", encoding="utf-8")

            self.assertIsNone(AppSettings(config_file).load_data_folder())

    def test_save_and_load_theme_preserves_data_folder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "settings.json"
            data_folder = Path(directory) / "database"
            settings = AppSettings(config_file)

            settings.save_data_folder(data_folder)
            saved_theme = settings.save_theme("dark")

            self.assertEqual(saved_theme, "dark")
            self.assertEqual(settings.load_theme(), "dark")
            self.assertEqual(settings.load_data_folder(), data_folder.resolve())

    def test_invalid_theme_loads_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "settings.json"
            config_file.write_text('{"theme": "neon"}', encoding="utf-8")

            self.assertEqual(AppSettings(config_file).load_theme(), DEFAULT_THEME)

    def test_save_data_folder_preserves_theme(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "settings.json"
            data_folder = Path(directory) / "database"
            settings = AppSettings(config_file)

            settings.save_theme("dark")
            settings.save_data_folder(data_folder)

            self.assertEqual(settings.load_theme(), "dark")

    def test_windows_config_dir_uses_appdata(self) -> None:
        config_dir = default_config_dir("nt", {"APPDATA": "C:/Users/Example/AppData/Roaming"})

        self.assertEqual(config_dir, Path("C:/Users/Example/AppData/Roaming") / "WorkTasks")

    def test_linux_config_dir_uses_xdg_config_home(self) -> None:
        config_dir = default_config_dir("posix", {"XDG_CONFIG_HOME": "/home/example/.config"})

        self.assertEqual(config_dir, Path("/home/example/.config") / "work-tasks")


if __name__ == "__main__":
    unittest.main()
