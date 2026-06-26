from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile

from src.task_model import Task
from src.xlsx_export import export_tasks_to_xlsx


class XlsxExportTest(unittest.TestCase):
    def test_export_includes_table_and_extra_contact_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "tarefas.xlsx"
            task = Task(
                title="Preparar relatorio",
                area="Financeiro",
                group="Fechamento",
                related_person="Mariana",
                related_person_contact="(31) 99999-0000",
                due_date="30/05/2026",
                hours="2,5",
                priority="Alta",
                notes="Enviar previa por e-mail",
            )

            exported_path = export_tasks_to_xlsx([task], output_path)

            self.assertEqual(exported_path, output_path)
            with ZipFile(exported_path) as archive:
                self.assertIn("xl/worksheets/sheet1.xml", archive.namelist())
                worksheet = archive.read("xl/worksheets/sheet1.xml")

        root = ElementTree.fromstring(worksheet)
        namespace = {"sheet": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        exported_text = [node.text for node in root.findall(".//sheet:t", namespace)]

        self.assertIn("Contato da pessoa relacionada", exported_text)
        self.assertIn("Grupo", exported_text)
        self.assertIn("Horas", exported_text)
        self.assertIn("Observacoes", exported_text)
        self.assertIn("Fechamento", exported_text)
        self.assertIn("(31) 99999-0000", exported_text)
        self.assertIn("2,5", exported_text)
        self.assertIn("Enviar previa por e-mail", exported_text)

    def test_export_adds_xlsx_extension_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            exported_path = export_tasks_to_xlsx([], Path(directory) / "tarefas")

            self.assertEqual(exported_path.name, "tarefas.xlsx")
            self.assertTrue(exported_path.exists())


if __name__ == "__main__":
    unittest.main()
