from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from .task_model import STATUS_DONE, STATUS_PENDING, Task


class TaskStore:
    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> list[Task]:
        if not self.file_path.exists():
            return []

        with self.file_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        if not isinstance(payload, list):
            raise ValueError("Arquivo de tarefas invalido: esperado uma lista JSON.")

        return [Task.from_dict(item) for item in payload if isinstance(item, dict)]

    def save(self, tasks: list[Task]) -> None:
        payload = [task.to_dict() for task in tasks]

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.file_path.parent,
            delete=False,
            suffix=".tmp",
        ) as temp_file:
            json.dump(payload, temp_file, ensure_ascii=False, indent=2)
            temp_file.write("\n")
            temp_name = temp_file.name

        Path(temp_name).replace(self.file_path)

    def add(self, tasks: list[Task], task: Task) -> list[Task]:
        updated = [*tasks, task]
        self.save(updated)
        return updated

    def update(self, tasks: list[Task], replacement: Task) -> list[Task]:
        replacement.mark_updated()
        updated = [
            replacement if task.task_id == replacement.task_id else task
            for task in tasks
        ]
        self.save(updated)
        return updated

    def delete(self, tasks: list[Task], task_id: str) -> list[Task]:
        updated = [task for task in tasks if task.task_id != task_id]
        self.save(updated)
        return updated

    def toggle_status(self, tasks: list[Task], task_id: str) -> list[Task]:
        updated: list[Task] = []
        for task in tasks:
            if task.task_id == task_id:
                task.status = STATUS_PENDING if task.status == STATUS_DONE else STATUS_DONE
                task.mark_updated()
            updated.append(task)

        self.save(updated)
        return updated

