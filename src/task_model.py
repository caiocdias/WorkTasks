from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from uuid import uuid4


STATUS_PENDING = "pending"
STATUS_DONE = "done"
PRIORITIES = ("Baixa", "Media", "Alta", "Urgente")
STATE_DONE = "Concluída"
STATE_ON_TIME = "No prazo"
STATE_DUE_SOON = "Vence em 7 dias"
STATE_DUE_TODAY = "Vence hoje"
STATE_OVERDUE = "Em atraso"
TASK_STATES = (
    STATE_DONE,
    STATE_ON_TIME,
    STATE_DUE_SOON,
    STATE_DUE_TODAY,
    STATE_OVERDUE,
)
STATE_SORT_RANK = {
    STATE_OVERDUE: 0,
    STATE_DUE_TODAY: 1,
    STATE_DUE_SOON: 2,
    STATE_ON_TIME: 3,
    STATE_DONE: 4,
}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def normalize_due_date(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return ""

    for source_format in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, source_format).strftime("%d/%m/%Y")
        except ValueError:
            pass

    return value


def format_due_date_input(value: str) -> str:
    digits = "".join(character for character in str(value or "") if character.isdigit())[:8]
    if len(digits) <= 2:
        return digits
    if len(digits) <= 4:
        return f"{digits[:2]}/{digits[2:]}"
    return f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"


def parse_due_date(value: str) -> date | None:
    value = str(value or "").strip()
    if not value:
        return None

    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        return None


def task_state(task: "Task", today: date | None = None) -> str:
    if task.is_done:
        return STATE_DONE

    due_date = parse_due_date(task.due_date)
    if due_date is None:
        return STATE_ON_TIME

    current_date = today or date.today()
    days_until_due = (due_date - current_date).days

    if days_until_due < 0:
        return STATE_OVERDUE
    if days_until_due == 0:
        return STATE_DUE_TODAY
    if days_until_due <= 7:
        return STATE_DUE_SOON
    return STATE_ON_TIME


@dataclass
class Task:
    title: str
    notes: str = ""
    area: str = ""
    due_date: str = ""
    priority: str = "Media"
    status: str = STATUS_PENDING
    task_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    @property
    def is_done(self) -> bool:
        return self.status == STATUS_DONE

    def mark_updated(self) -> None:
        self.updated_at = now_iso()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.task_id,
            "title": self.title,
            "notes": self.notes,
            "area": self.area,
            "due_date": self.due_date,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Task":
        priority = raw.get("priority") or "Media"
        status = raw.get("status") or STATUS_PENDING

        if priority not in PRIORITIES:
            priority = "Media"
        if status not in {STATUS_PENDING, STATUS_DONE}:
            status = STATUS_PENDING

        return cls(
            task_id=str(raw.get("id") or uuid4()),
            title=str(raw.get("title") or "").strip(),
            notes=str(raw.get("notes") or ""),
            area=str(raw.get("area") or ""),
            due_date=normalize_due_date(str(raw.get("due_date") or "")),
            priority=priority,
            status=status,
            created_at=str(raw.get("created_at") or now_iso()),
            updated_at=str(raw.get("updated_at") or now_iso()),
        )
