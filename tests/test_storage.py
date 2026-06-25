from __future__ import annotations

from datetime import date
import json
import tempfile
import unittest
from pathlib import Path

from src.storage import TaskStore
from src.task_model import (
    STATE_DONE,
    STATE_DUE_SOON,
    STATE_DUE_TODAY,
    STATE_ON_TIME,
    STATE_OVERDUE,
    STATUS_DONE,
    STATUS_PENDING,
    Task,
    format_due_date_input,
    normalize_hours,
    parse_hours,
    task_state,
)


class TaskStoreTest(unittest.TestCase):
    def test_save_and_load_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = TaskStore(Path(directory) / "tasks.json")
            task = Task(
                title="Preparar relatorio",
                area="Financeiro",
                related_person="Mariana",
                related_person_contact="(31) 99999-0000",
                hours="2,5",
                priority="Alta",
            )

            store.save([task])
            loaded = store.load()

            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].title, "Preparar relatorio")
            self.assertEqual(loaded[0].area, "Financeiro")
            self.assertEqual(loaded[0].related_person, "Mariana")
            self.assertEqual(loaded[0].related_person_contact, "(31) 99999-0000")
            self.assertEqual(loaded[0].hours, "2,5")
            self.assertEqual(loaded[0].priority, "Alta")

    def test_toggle_status_persists_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = TaskStore(Path(directory) / "tasks.json")
            task = Task(title="Responder cliente")

            tasks = store.add([], task)
            tasks = store.toggle_status(tasks, task.task_id)
            loaded = store.load()

            self.assertEqual(tasks[0].status, STATUS_DONE)
            self.assertEqual(loaded[0].status, STATUS_DONE)

    def test_load_rejects_invalid_root_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "tasks.json"
            file_path.write_text(json.dumps({"tasks": []}), encoding="utf-8")
            store = TaskStore(file_path)

            with self.assertRaises(ValueError):
                store.load()

    def test_unknown_status_falls_back_to_pending(self) -> None:
        task = Task.from_dict({"title": "Revisar proposta", "status": "waiting"})

        self.assertEqual(task.status, STATUS_PENDING)

    def test_missing_related_person_loads_as_empty_text(self) -> None:
        task = Task.from_dict({"title": "Revisar proposta"})

        self.assertEqual(task.related_person, "")

    def test_missing_related_person_contact_loads_as_empty_text(self) -> None:
        task = Task.from_dict({"title": "Revisar proposta"})

        self.assertEqual(task.related_person_contact, "")

    def test_missing_hours_loads_as_empty_text(self) -> None:
        task = Task.from_dict({"title": "Revisar proposta"})

        self.assertEqual(task.hours, "")

    def test_legacy_due_date_is_loaded_as_brazilian_format(self) -> None:
        task = Task.from_dict({"title": "Fechar folha", "due_date": "2026-05-30"})

        self.assertEqual(task.due_date, "30/05/2026")

    def test_hours_are_normalized_from_comma_or_dot(self) -> None:
        self.assertEqual(normalize_hours("2"), "2")
        self.assertEqual(normalize_hours("2.50"), "2,5")
        self.assertEqual(normalize_hours("2,50"), "2,5")
        self.assertIsNotNone(parse_hours("0,25"))
        self.assertIsNone(parse_hours("-1"))
        self.assertIsNone(parse_hours("duas"))

    def test_due_date_input_mask_keeps_only_date_digits(self) -> None:
        self.assertEqual(format_due_date_input("1"), "1")
        self.assertEqual(format_due_date_input("120"), "12/0")
        self.assertEqual(format_due_date_input("12052026"), "12/05/2026")
        self.assertEqual(format_due_date_input("12a05b2026xyz"), "12/05/2026")
        self.assertEqual(format_due_date_input("1205202600"), "12/05/2026")

    def test_task_state_uses_due_date_and_completion(self) -> None:
        today = date(2026, 5, 26)

        self.assertEqual(task_state(Task(title="Sem prazo"), today), STATE_ON_TIME)
        self.assertEqual(task_state(Task(title="Atrasada", due_date="25/05/2026"), today), STATE_OVERDUE)
        self.assertEqual(task_state(Task(title="Hoje", due_date="26/05/2026"), today), STATE_DUE_TODAY)
        self.assertEqual(task_state(Task(title="Semana", due_date="02/06/2026"), today), STATE_DUE_SOON)
        self.assertEqual(task_state(Task(title="Futuro", due_date="03/06/2026"), today), STATE_ON_TIME)
        self.assertEqual(
            task_state(Task(title="Feita", due_date="25/05/2026", status=STATUS_DONE), today),
            STATE_DONE,
        )


if __name__ == "__main__":
    unittest.main()
