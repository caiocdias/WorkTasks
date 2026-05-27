from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from .storage import TaskStore
from .task_model import (
    PRIORITIES,
    STATE_DONE,
    STATE_OVERDUE,
    STATE_SORT_RANK,
    TASK_STATES,
    Task,
    format_due_date_input,
    normalize_due_date,
    parse_due_date,
    task_state,
)


APP_TITLE = "Work Tasks"
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "tasks.json"
COLUMN_LABELS = {
    "title": "Tarefa",
    "area": "Area/Projeto",
    "priority": "Prioridade",
    "due_date": "Vencimento",
    "status": "Status",
}
COLUMNS = tuple(COLUMN_LABELS)
COLUMN_WIDTHS = {
    "title": 280,
    "area": 160,
    "priority": 100,
    "due_date": 110,
    "status": 130,
}


class TodoApp(tk.Tk):
    def __init__(self, store: TaskStore) -> None:
        super().__init__()
        self.store = store
        self.tasks = self.store.load()
        self.selected_task_id: str | None = None
        self.sort_column = "status"
        self.sort_reverse = False
        self.column_filters: dict[str, dict[str, object]] = {
            column: {"text": "", "values": None}
            for column in COLUMNS
        }
        self.sort_buttons: dict[str, ttk.Button] = {}
        self.filter_buttons: dict[str, ttk.Button] = {}
        self.is_formatting_due_date = False

        self.title(APP_TITLE)
        self.geometry("1060x680")
        self.minsize(940, 600)
        self.configure(bg="#f5f7fb")

        self._build_vars()
        self._build_style()
        self._build_layout()
        self._refresh_tree()

    def _build_vars(self) -> None:
        self.title_var = tk.StringVar()
        self.area_var = tk.StringVar()
        self.due_date_var = tk.StringVar()
        self.priority_var = tk.StringVar(value="Media")
        self.search_var = tk.StringVar()
        self.status_filter_var = tk.StringVar(value="Todas")

        self.search_var.trace_add("write", lambda *_: self._refresh_tree())
        self.status_filter_var.trace_add("write", lambda *_: self._refresh_tree())

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f7fb")
        style.configure("Panel.TFrame", background="#ffffff", relief="flat")
        style.configure("TLabel", background="#f5f7fb", foreground="#1f2937", font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background="#ffffff", foreground="#1f2937", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background="#f5f7fb", foreground="#111827", font=("Segoe UI Semibold", 20))
        style.configure("Muted.TLabel", background="#f5f7fb", foreground="#6b7280", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 8))
        style.configure("HeaderSort.TButton", font=("Segoe UI Semibold", 9), padding=(8, 5))
        style.configure("HeaderFilter.TButton", font=("Segoe UI", 9), padding=(6, 5))
        style.configure("Primary.TButton", background="#2563eb", foreground="#ffffff")
        style.map("Primary.TButton", background=[("active", "#1d4ed8")])
        style.configure("Treeview", rowheight=30, font=("Segoe UI", 10), fieldbackground="#ffffff")

    def _build_layout(self) -> None:
        shell = ttk.Frame(self, padding=24)
        shell.pack(fill=tk.BOTH, expand=True)
        shell.columnconfigure(0, weight=0)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(1, weight=1)

        ttk.Label(shell, text="Tarefas do trabalho", style="Header.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            shell,
            text="Organize prioridades, prazos e anotacoes em um arquivo local.",
            style="Muted.TLabel",
        ).grid(row=0, column=1, sticky="e", padx=(16, 0))

        form = ttk.Frame(shell, style="Panel.TFrame", padding=18)
        form.grid(row=1, column=0, sticky="ns", pady=(20, 0), padx=(0, 18))
        form.columnconfigure(0, weight=1)

        self.form_mode_label = ttk.Label(form, text="Nova tarefa", style="Panel.TLabel")
        self.form_mode_label.grid(row=0, column=0, sticky="w", pady=(0, 12))

        ttk.Label(form, text="Tarefa", style="Panel.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.title_var, width=34).grid(row=2, column=0, sticky="ew", pady=(4, 14))

        ttk.Label(form, text="Area ou projeto", style="Panel.TLabel").grid(row=3, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.area_var).grid(row=4, column=0, sticky="ew", pady=(4, 14))

        ttk.Label(form, text="Vencimento (DD/MM/AAAA)", style="Panel.TLabel").grid(row=5, column=0, sticky="w")
        self.due_date_entry = ttk.Entry(form, textvariable=self.due_date_var)
        self.due_date_entry.grid(row=6, column=0, sticky="ew", pady=(4, 14))
        self.due_date_entry.bind("<KeyRelease>", self._apply_due_date_mask)

        ttk.Label(form, text="Prioridade", style="Panel.TLabel").grid(row=7, column=0, sticky="w")
        ttk.Combobox(
            form,
            textvariable=self.priority_var,
            values=PRIORITIES,
            state="readonly",
        ).grid(row=8, column=0, sticky="ew", pady=(4, 14))

        ttk.Label(form, text="Observacoes", style="Panel.TLabel").grid(row=9, column=0, sticky="w")
        self.notes_text = tk.Text(
            form,
            height=8,
            width=34,
            wrap=tk.WORD,
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 10),
        )
        self.notes_text.grid(row=10, column=0, sticky="nsew", pady=(4, 16))

        self.save_button = ttk.Button(form, text="Criar tarefa", style="Primary.TButton", command=self._save_task)
        self.save_button.grid(
            row=11, column=0, sticky="ew", pady=(0, 8)
        )
        ttk.Button(form, text="Nova tarefa", command=self._clear_form).grid(row=12, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(form, text="Concluir / reabrir", command=self._toggle_selected).grid(
            row=13, column=0, sticky="ew", pady=(0, 8)
        )
        ttk.Button(form, text="Excluir selecionada", command=self._delete_selected).grid(
            row=14, column=0, sticky="ew"
        )

        list_panel = ttk.Frame(shell, style="Panel.TFrame", padding=18)
        list_panel.grid(row=1, column=1, sticky="nsew", pady=(20, 0))
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(3, weight=1)

        filters = ttk.Frame(list_panel, style="Panel.TFrame")
        filters.grid(row=0, column=0, sticky="ew")
        filters.columnconfigure(0, weight=1)

        ttk.Entry(filters, textvariable=self.search_var).grid(row=0, column=0, sticky="ew", padx=(0, 12))
        ttk.Combobox(
            filters,
            textvariable=self.status_filter_var,
            values=("Todas", *TASK_STATES),
            state="readonly",
            width=18,
        ).grid(row=0, column=1, sticky="e")

        self.summary_label = ttk.Label(list_panel, text="", style="Panel.TLabel")
        self.summary_label.grid(row=1, column=0, sticky="w", pady=(14, 8))

        self.header_frame = ttk.Frame(list_panel, style="Panel.TFrame")
        self.header_frame.grid(row=2, column=0, sticky="ew")
        self._build_table_header()

        self.tree = ttk.Treeview(list_panel, columns=COLUMNS, show="", selectmode="browse")
        self.tree.column("title", width=COLUMN_WIDTHS["title"], minwidth=220)
        self.tree.column("area", width=COLUMN_WIDTHS["area"], minwidth=120)
        self.tree.column("priority", width=COLUMN_WIDTHS["priority"], minwidth=90, anchor=tk.CENTER)
        self.tree.column("due_date", width=COLUMN_WIDTHS["due_date"], minwidth=100, anchor=tk.CENTER)
        self.tree.column("status", width=COLUMN_WIDTHS["status"], minwidth=120, anchor=tk.CENTER)
        self.tree.grid(row=3, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda _event: self._toggle_selected())

        scrollbar = ttk.Scrollbar(list_panel, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=3, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self._update_headings()

    def _build_table_header(self) -> None:
        for index, column in enumerate(COLUMNS):
            self.header_frame.columnconfigure(index, weight=COLUMN_WIDTHS[column], minsize=COLUMN_WIDTHS[column])

            cell = ttk.Frame(self.header_frame, style="Panel.TFrame")
            cell.grid(row=0, column=index, sticky="ew")
            cell.columnconfigure(0, weight=1)

            sort_button = ttk.Button(
                cell,
                style="HeaderSort.TButton",
                command=lambda selected_column=column: self._set_sort(selected_column),
            )
            sort_button.grid(row=0, column=0, sticky="ew")

            filter_button = ttk.Button(
                cell,
                style="HeaderFilter.TButton",
                width=3,
                command=lambda selected_column=column: self._open_column_filter(selected_column),
            )
            filter_button.grid(row=0, column=1, sticky="e")

            self.sort_buttons[column] = sort_button
            self.filter_buttons[column] = filter_button

    def _visible_tasks(self) -> list[Task]:
        search = self.search_var.get().strip().lower()
        status_filter = self.status_filter_var.get()

        tasks = self.tasks
        if status_filter != "Todas":
            tasks = [task for task in tasks if task_state(task) == status_filter]

        if search:
            tasks = [
                task
                for task in tasks
                if search in " ".join([task.title, task.area, task.notes, task_state(task)]).lower()
            ]

        tasks = [task for task in tasks if self._passes_column_filters(task)]
        return sorted(tasks, key=self._sort_key, reverse=self.sort_reverse)

    def _passes_column_filters(self, task: Task) -> bool:
        for column, column_filter in self.column_filters.items():
            value = self._task_column_value(task, column)
            text_filter = str(column_filter["text"]).strip().lower()
            selected_values = column_filter["values"]

            if text_filter and text_filter not in value.lower():
                return False
            if selected_values is not None and value not in selected_values:
                return False

        return True

    def _task_column_value(self, task: Task, column: str) -> str:
        if column == "title":
            return task.title
        if column == "area":
            return task.area
        if column == "priority":
            return task.priority
        if column == "due_date":
            return task.due_date
        if column == "status":
            return task_state(task)
        return ""

    def _due_date_sort_key(self, due_date: str) -> str:
        parsed = parse_due_date(due_date)
        if parsed is None:
            return "9999-99-99"
        return parsed.strftime("%Y-%m-%d")

    def _sort_key(self, task: Task) -> tuple[object, ...]:
        priority_rank = {"Urgente": 0, "Alta": 1, "Media": 2, "Baixa": 3}
        state = task_state(task)

        if self.sort_column == "title":
            return (task.title.lower(), STATE_SORT_RANK[state], self._due_date_sort_key(task.due_date))
        if self.sort_column == "area":
            return (task.area.lower(), STATE_SORT_RANK[state], self._due_date_sort_key(task.due_date))
        if self.sort_column == "priority":
            return (priority_rank[task.priority], STATE_SORT_RANK[state], self._due_date_sort_key(task.due_date))
        if self.sort_column == "due_date":
            return (self._due_date_sort_key(task.due_date), STATE_SORT_RANK[state], priority_rank[task.priority])

        return (STATE_SORT_RANK[state], self._due_date_sort_key(task.due_date), priority_rank[task.priority])

    def _set_sort(self, column: str) -> None:
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        self._update_headings()
        self._refresh_tree()

    def _update_headings(self) -> None:
        for column in COLUMNS:
            arrow = "↕"
            if self.sort_column == column:
                arrow = "↓" if self.sort_reverse else "↑"

            title = f"{COLUMN_LABELS[column]} {arrow}"
            funnel = "⏷"
            column_filter = self.column_filters[column]
            if column_filter["text"] or column_filter["values"] is not None:
                funnel = "⏷*"

            self.sort_buttons[column].configure(text=title)
            self.filter_buttons[column].configure(text=funnel)

    def _open_column_filter(self, column: str) -> None:
        values = self._column_filter_values(column)
        column_filter = self.column_filters[column]

        window = tk.Toplevel(self)
        window.title(f"Filtro - {COLUMN_LABELS[column]}")
        window.geometry("340x430")
        window.transient(self)
        window.grab_set()
        window.configure(bg="#ffffff")

        frame = ttk.Frame(window, style="Panel.TFrame", padding=16)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1)

        ttk.Label(frame, text=COLUMN_LABELS[column], style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        text_var = tk.StringVar(value=str(column_filter["text"]))
        ttk.Entry(frame, textvariable=text_var).grid(row=1, column=0, sticky="ew", pady=(6, 12))

        ttk.Label(frame, text="Valores existentes", style="Panel.TLabel").grid(row=2, column=0, sticky="w")
        list_frame = ttk.Frame(frame, style="Panel.TFrame")
        list_frame.grid(row=3, column=0, sticky="nsew", pady=(6, 12))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        listbox = tk.Listbox(
            list_frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=10,
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 10),
        )
        listbox.grid(row=0, column=0, sticky="nsew")
        value_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        value_scrollbar.grid(row=0, column=1, sticky="ns")
        listbox.configure(yscrollcommand=value_scrollbar.set)

        selected_values = column_filter["values"]
        for index, value in enumerate(values):
            display_value = self._display_filter_value(value)
            listbox.insert(tk.END, display_value)
            if selected_values is None or value in selected_values:
                listbox.selection_set(index)

        actions = ttk.Frame(frame, style="Panel.TFrame")
        actions.grid(row=4, column=0, sticky="ew")
        actions.columnconfigure((0, 1, 2, 3), weight=1)

        ttk.Button(actions, text="Todos", command=lambda: listbox.selection_set(0, tk.END)).grid(
            row=0, column=0, sticky="ew", padx=(0, 6)
        )
        ttk.Button(actions, text="Nenhum", command=lambda: listbox.selection_clear(0, tk.END)).grid(
            row=0, column=1, sticky="ew", padx=(0, 6)
        )
        ttk.Button(actions, text="Limpar", command=lambda: self._clear_column_filter(column, window)).grid(
            row=0, column=2, sticky="ew", padx=(0, 6)
        )
        ttk.Button(
            actions,
            text="Aplicar",
            style="Primary.TButton",
            command=lambda: self._apply_column_filter(column, text_var, listbox, values, window),
        ).grid(row=0, column=3, sticky="ew")

    def _column_filter_values(self, column: str) -> list[str]:
        values = {self._task_column_value(task, column) for task in self.tasks}
        if column == "priority":
            ordered_values = [priority for priority in PRIORITIES if priority in values]
            return ordered_values + sorted(values - set(ordered_values))
        if column == "status":
            ordered_values = [state for state in TASK_STATES if state in values]
            return ordered_values + sorted(values - set(ordered_values))
        if column == "due_date":
            return sorted(values, key=self._due_date_sort_key)
        return sorted(values, key=str.lower)

    def _display_filter_value(self, value: str) -> str:
        return value if value else "(vazio)"

    def _apply_column_filter(
        self,
        column: str,
        text_var: tk.StringVar,
        listbox: tk.Listbox,
        values: list[str],
        window: tk.Toplevel,
    ) -> None:
        selected_indexes = set(listbox.curselection())
        selected_values = {value for index, value in enumerate(values) if index in selected_indexes}
        value_filter = None if len(selected_values) == len(values) else selected_values

        self.column_filters[column] = {
            "text": text_var.get().strip(),
            "values": value_filter,
        }
        self._update_headings()
        self._refresh_tree()
        window.destroy()

    def _clear_column_filter(self, column: str, window: tk.Toplevel) -> None:
        self.column_filters[column] = {"text": "", "values": None}
        self._update_headings()
        self._refresh_tree()
        window.destroy()

    def _refresh_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        visible = self._visible_tasks()
        for task in visible:
            self.tree.insert(
                "",
                tk.END,
                iid=task.task_id,
                values=(task.title, task.area, task.priority, task.due_date, task_state(task)),
            )

        done_count = sum(1 for task in self.tasks if task_state(task) == STATE_DONE)
        overdue_count = sum(1 for task in self.tasks if task_state(task) == STATE_OVERDUE)
        self.summary_label.configure(
            text=f"{len(visible)} exibidas | {overdue_count} em atraso | {done_count} concluídas"
        )

    def _selected_task(self) -> Task | None:
        if not self.selected_task_id:
            return None
        return next((task for task in self.tasks if task.task_id == self.selected_task_id), None)

    def _on_select(self, _event: tk.Event) -> None:
        selection = self.tree.selection()
        if not selection:
            return

        self.selected_task_id = selection[0]
        task = self._selected_task()
        if not task:
            return

        self.title_var.set(task.title)
        self.area_var.set(task.area)
        self.due_date_var.set(task.due_date)
        self.priority_var.set(task.priority)
        self.notes_text.delete("1.0", tk.END)
        self.notes_text.insert("1.0", task.notes)
        self.form_mode_label.configure(text=f"Editando: {task.title}")
        self.save_button.configure(text="Atualizar tarefa")

    def _validate_form(self) -> bool:
        if not self.title_var.get().strip():
            messagebox.showwarning(APP_TITLE, "Informe o titulo da tarefa.")
            return False

        due_date = self.due_date_var.get().strip()
        if due_date:
            try:
                datetime.strptime(due_date, "%d/%m/%Y")
            except ValueError:
                messagebox.showwarning(APP_TITLE, "Use a data no formato DD/MM/AAAA.")
                return False

        return True

    def _apply_due_date_mask(self, _event: tk.Event) -> None:
        if self.is_formatting_due_date:
            return

        self.is_formatting_due_date = True
        formatted_value = format_due_date_input(self.due_date_var.get())
        self.due_date_var.set(formatted_value)
        self.due_date_entry.icursor(tk.END)
        self.is_formatting_due_date = False

    def _save_task(self) -> None:
        if not self._validate_form():
            return

        notes = self.notes_text.get("1.0", tk.END).strip()
        due_date = normalize_due_date(self.due_date_var.get())
        existing = self._selected_task()

        if existing:
            task = Task(
                task_id=existing.task_id,
                title=self.title_var.get().strip(),
                area=self.area_var.get().strip(),
                due_date=due_date,
                priority=self.priority_var.get(),
                notes=notes,
                status=existing.status,
                created_at=existing.created_at,
            )
            self.tasks = self.store.update(self.tasks, task)
        else:
            task = Task(
                title=self.title_var.get().strip(),
                area=self.area_var.get().strip(),
                due_date=due_date,
                priority=self.priority_var.get(),
                notes=notes,
            )
            self.tasks = self.store.add(self.tasks, task)
            self.selected_task_id = task.task_id

        self._refresh_tree()
        if self.selected_task_id in self.tree.get_children():
            self.tree.selection_set(self.selected_task_id)
            self.tree.focus(self.selected_task_id)

    def _clear_form(self) -> None:
        self.selected_task_id = None
        self.title_var.set("")
        self.area_var.set("")
        self.due_date_var.set("")
        self.priority_var.set("Media")
        self.notes_text.delete("1.0", tk.END)
        self.form_mode_label.configure(text="Nova tarefa")
        self.save_button.configure(text="Criar tarefa")
        self.tree.selection_remove(self.tree.selection())

    def _toggle_selected(self) -> None:
        task = self._selected_task()
        if not task:
            messagebox.showinfo(APP_TITLE, "Selecione uma tarefa primeiro.")
            return

        self.tasks = self.store.toggle_status(self.tasks, task.task_id)
        self._refresh_tree()
        if task.task_id in self.tree.get_children():
            self.tree.selection_set(task.task_id)
            self.tree.focus(task.task_id)

    def _delete_selected(self) -> None:
        task = self._selected_task()
        if not task:
            messagebox.showinfo(APP_TITLE, "Selecione uma tarefa primeiro.")
            return

        if not messagebox.askyesno(APP_TITLE, f"Excluir a tarefa '{task.title}'?"):
            return

        self.tasks = self.store.delete(self.tasks, task.task_id)
        self._clear_form()
        self._refresh_tree()


def main() -> None:
    app = TodoApp(TaskStore(DATA_FILE))
    app.mainloop()
