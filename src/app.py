from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .settings import AppSettings
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
LEGACY_DATA_FOLDER = Path(__file__).resolve().parent.parent / "data"
COLUMN_LABELS = {
    "title": "Tarefa",
    "area": "Area/Projeto",
    "related_person": "Pessoa relacionada",
    "priority": "Prioridade",
    "due_date": "Vencimento",
    "status": "Status",
}
COLUMNS = tuple(COLUMN_LABELS)
COLUMN_WIDTHS = {
    "title": 260,
    "area": 145,
    "related_person": 170,
    "priority": 95,
    "due_date": 110,
    "status": 130,
}
COLUMN_MIN_WIDTHS = {
    "title": 190,
    "area": 105,
    "related_person": 145,
    "priority": 85,
    "due_date": 100,
    "status": 120,
}
FILTER_BUTTON_WIDTH = 30


class TodoApp(tk.Tk):
    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        self.settings = settings
        self.data_folder = self.settings.load_data_folder()
        self.store: TaskStore | None = None
        self.tasks: list[Task] = []
        self.selected_task_id: str | None = None
        self.sort_column = "status"
        self.sort_reverse = False
        self.column_filters: dict[str, dict[str, object]] = {
            column: {"text": "", "values": None}
            for column in COLUMNS
        }
        self.sort_buttons: dict[str, ttk.Button] = {}
        self.filter_buttons: dict[str, ttk.Button] = {}
        self.header_cells: dict[str, ttk.Frame] = {}
        self.syncing_table_widths = False
        self.is_formatting_due_date = False
        self.form_feedback_clear_after_id: str | None = None

        self.title(APP_TITLE)
        self.geometry("1180x720")
        self.minsize(1080, 640)
        self.configure(bg="#f5f7fb")

        if self.data_folder:
            self._load_data_folder(self.data_folder, save_setting=False)

        self._build_vars()
        self._build_style()
        self._build_layout()
        self._refresh_tree()

        if self.store is None:
            self.after(250, lambda: self._choose_data_folder(initial=True))

    def _build_vars(self) -> None:
        self.title_var = tk.StringVar()
        self.area_var = tk.StringVar()
        self.related_person_var = tk.StringVar()
        self.related_person_contact_var = tk.StringVar()
        self.due_date_var = tk.StringVar()
        self.priority_var = tk.StringVar(value="Media")
        self.search_var = tk.StringVar()
        self.data_folder_var = tk.StringVar(value=self._data_folder_text())
        self.form_feedback_var = tk.StringVar()

        self.search_var.trace_add("write", lambda *_: self._refresh_tree())

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f5f7fb")
        style.configure("Panel.TFrame", background="#ffffff", relief="flat")
        style.configure("TLabel", background="#f5f7fb", foreground="#1f2937", font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background="#ffffff", foreground="#1f2937", font=("Segoe UI", 10))
        style.configure("Success.Panel.TLabel", background="#ffffff", foreground="#047857", font=("Segoe UI Semibold", 9))
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

        ttk.Label(form, text="Pessoa relacionada", style="Panel.TLabel").grid(row=5, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.related_person_var).grid(row=6, column=0, sticky="ew", pady=(4, 14))

        ttk.Label(form, text="Contato da pessoa relacionada", style="Panel.TLabel").grid(row=7, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.related_person_contact_var).grid(
            row=8, column=0, sticky="ew", pady=(4, 14)
        )

        ttk.Label(form, text="Vencimento (DD/MM/AAAA)", style="Panel.TLabel").grid(row=9, column=0, sticky="w")
        self.due_date_entry = ttk.Entry(form, textvariable=self.due_date_var)
        self.due_date_entry.grid(row=10, column=0, sticky="ew", pady=(4, 14))
        self.due_date_entry.bind("<KeyRelease>", self._apply_due_date_mask)

        ttk.Label(form, text="Prioridade", style="Panel.TLabel").grid(row=11, column=0, sticky="w")
        ttk.Combobox(
            form,
            textvariable=self.priority_var,
            values=PRIORITIES,
            state="readonly",
        ).grid(row=12, column=0, sticky="ew", pady=(4, 14))

        ttk.Label(form, text="Observacoes", style="Panel.TLabel").grid(row=13, column=0, sticky="w")
        self.notes_text = tk.Text(
            form,
            height=5,
            width=34,
            wrap=tk.WORD,
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 10),
        )
        self.notes_text.grid(row=14, column=0, sticky="nsew", pady=(4, 16))

        ttk.Label(form, textvariable=self.form_feedback_var, style="Success.Panel.TLabel").grid(
            row=15, column=0, sticky="w", pady=(0, 6)
        )
        self.save_button = ttk.Button(form, text="Criar tarefa", style="Primary.TButton", command=self._save_task)
        self.save_button.grid(
            row=16, column=0, sticky="ew", pady=(0, 8)
        )
        ttk.Button(form, text="Nova tarefa", command=self._clear_form).grid(row=17, column=0, sticky="ew", pady=(0, 8))
        ttk.Button(form, text="Concluir / reabrir", command=self._toggle_selected).grid(
            row=18, column=0, sticky="ew", pady=(0, 8)
        )
        ttk.Button(form, text="Excluir selecionada", command=self._delete_selected).grid(
            row=19, column=0, sticky="ew"
        )

        list_panel = ttk.Frame(shell, style="Panel.TFrame", padding=18)
        list_panel.grid(row=1, column=1, sticky="nsew", pady=(20, 0))
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(4, weight=1)

        data_controls = ttk.Frame(list_panel, style="Panel.TFrame")
        data_controls.grid(row=0, column=0, sticky="ew")
        data_controls.columnconfigure(0, weight=1)

        ttk.Label(data_controls, textvariable=self.data_folder_var, style="Panel.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 12)
        )
        ttk.Button(data_controls, text="Alterar pasta de dados", command=self._choose_data_folder).grid(
            row=0, column=1, sticky="e"
        )

        filters = ttk.Frame(list_panel, style="Panel.TFrame")
        filters.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        filters.columnconfigure(0, weight=1)

        ttk.Entry(filters, textvariable=self.search_var).grid(row=0, column=0, sticky="ew")

        self.summary_label = ttk.Label(list_panel, text="", style="Panel.TLabel")
        self.summary_label.grid(row=2, column=0, sticky="w", pady=(14, 8))

        self.header_frame = ttk.Frame(list_panel, style="Panel.TFrame")
        self.header_frame.grid(row=3, column=0, sticky="ew")
        self._build_table_header()

        self.tree = ttk.Treeview(list_panel, columns=COLUMNS, show="", selectmode="browse")
        self.tree.column("#0", width=0, minwidth=0, stretch=False)
        self.tree.column("title", width=COLUMN_WIDTHS["title"], minwidth=COLUMN_MIN_WIDTHS["title"], stretch=False)
        self.tree.column("area", width=COLUMN_WIDTHS["area"], minwidth=COLUMN_MIN_WIDTHS["area"], stretch=False)
        self.tree.column(
            "related_person",
            width=COLUMN_WIDTHS["related_person"],
            minwidth=COLUMN_MIN_WIDTHS["related_person"],
            stretch=False,
        )
        self.tree.column(
            "priority",
            width=COLUMN_WIDTHS["priority"],
            minwidth=COLUMN_MIN_WIDTHS["priority"],
            anchor=tk.CENTER,
            stretch=False,
        )
        self.tree.column(
            "due_date",
            width=COLUMN_WIDTHS["due_date"],
            minwidth=COLUMN_MIN_WIDTHS["due_date"],
            anchor=tk.CENTER,
            stretch=False,
        )
        self.tree.column(
            "status",
            width=COLUMN_WIDTHS["status"],
            minwidth=COLUMN_MIN_WIDTHS["status"],
            anchor=tk.CENTER,
            stretch=False,
        )
        self.tree.grid(row=4, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda _event: self._toggle_selected())
        self.tree.bind("<Configure>", self._sync_table_widths)

        scrollbar = ttk.Scrollbar(list_panel, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=4, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.after_idle(self._sync_table_widths)
        self._update_headings()

    def _data_folder_text(self) -> str:
        if not self.data_folder:
            return "Pasta de dados: nenhuma selecionada"
        return f"Pasta de dados: {self.data_folder}"

    def _load_data_folder(self, folder: Path, save_setting: bool = True) -> bool:
        store = TaskStore(self.settings.tasks_file(folder))
        try:
            tasks = store.load()
        except (OSError, ValueError) as error:
            messagebox.showerror(APP_TITLE, f"Nao foi possivel carregar a pasta selecionada.\n\n{error}")
            return False

        self.data_folder = Path(folder)
        self.store = store
        self.tasks = tasks
        if save_setting:
            self.data_folder = self.settings.save_data_folder(folder)
            self.store = TaskStore(self.settings.tasks_file(self.data_folder))
        return True

    def _choose_data_folder(self, initial: bool = False, reset_form: bool = True) -> None:
        initial_dir = self.data_folder or (LEGACY_DATA_FOLDER if LEGACY_DATA_FOLDER.exists() else Path.home())
        selected_folder = filedialog.askdirectory(
            parent=self,
            title="Selecione a pasta de dados",
            initialdir=str(initial_dir),
            mustexist=True,
        )

        if not selected_folder:
            if initial and self.store is None:
                messagebox.showinfo(
                    APP_TITLE,
                    "Selecione uma pasta de dados para salvar e carregar suas tarefas.",
                )
            return

        if not self._load_data_folder(Path(selected_folder)):
            return

        self.data_folder_var.set(self._data_folder_text())
        if reset_form:
            self._clear_form()
        self._refresh_tree()

    def _ensure_store(self) -> bool:
        if self.store is not None:
            return True

        self._choose_data_folder(initial=True, reset_form=False)
        return self.store is not None

    def _build_table_header(self) -> None:
        for index, column in enumerate(COLUMNS):
            self.header_frame.columnconfigure(index, weight=0, minsize=COLUMN_WIDTHS[column])

            cell = ttk.Frame(self.header_frame, style="Panel.TFrame")
            cell.grid(row=0, column=index, sticky="ew")
            cell.configure(width=COLUMN_WIDTHS[column], height=31)
            cell.grid_propagate(False)
            cell.columnconfigure(0, weight=1)
            cell.rowconfigure(0, weight=1)

            sort_button = ttk.Button(
                cell,
                style="HeaderSort.TButton",
                command=lambda selected_column=column: self._set_sort(selected_column),
            )
            sort_button.grid(row=0, column=0, sticky="nsew", padx=(0, FILTER_BUTTON_WIDTH))

            filter_button = ttk.Button(
                cell,
                style="HeaderFilter.TButton",
                width=3,
                command=lambda selected_column=column: self._open_column_filter(selected_column),
            )
            filter_button.place(
                relx=1.0,
                x=-1,
                y=1,
                width=FILTER_BUTTON_WIDTH,
                relheight=1.0,
                height=-2,
                anchor="ne",
            )

            self.header_cells[column] = cell
            self.sort_buttons[column] = sort_button
            self.filter_buttons[column] = filter_button

    def _sync_table_widths(self, _event: tk.Event | None = None) -> None:
        if self.syncing_table_widths:
            return

        available_width = max(self.tree.winfo_width() - 2, sum(COLUMN_MIN_WIDTHS.values()))
        widths = self._calculate_column_widths(available_width)

        self.syncing_table_widths = True
        for index, column in enumerate(COLUMNS):
            width = widths[column]
            self.tree.column(column, width=width, stretch=False)
            self.header_cells[column].configure(width=width)
            self.header_frame.columnconfigure(index, minsize=width)
        self.syncing_table_widths = False

    def _calculate_column_widths(self, available_width: int) -> dict[str, int]:
        available_width = max(available_width, sum(COLUMN_MIN_WIDTHS.values()))
        extra_width = available_width - sum(COLUMN_MIN_WIDTHS.values())
        total_weight = sum(COLUMN_WIDTHS.values())
        widths: dict[str, int] = {}
        assigned_width = 0

        for column in COLUMNS[:-1]:
            width = COLUMN_MIN_WIDTHS[column] + round(extra_width * COLUMN_WIDTHS[column] / total_weight)
            widths[column] = width
            assigned_width += width

        last_column = COLUMNS[-1]
        widths[last_column] = available_width - assigned_width
        return widths

    def _visible_tasks(self) -> list[Task]:
        search = self.search_var.get().strip().lower()

        tasks = self.tasks
        if search:
            tasks = [
                task
                for task in tasks
                if search in " ".join(
                    [
                        task.title,
                        task.area,
                        task.related_person,
                        task.related_person_contact,
                        task.notes,
                        task_state(task),
                    ]
                ).lower()
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
        if column == "related_person":
            return task.related_person
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
        if self.sort_column == "related_person":
            return (task.related_person.lower(), STATE_SORT_RANK[state], self._due_date_sort_key(task.due_date))
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
                values=(
                    task.title,
                    task.area,
                    task.related_person,
                    task.priority,
                    task.due_date,
                    task_state(task),
                ),
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

        selected_task_id = selection[0]
        if selected_task_id != self.selected_task_id:
            self._clear_form_feedback()

        self.selected_task_id = selected_task_id
        task = self._selected_task()
        if not task:
            return

        self.title_var.set(task.title)
        self.area_var.set(task.area)
        self.related_person_var.set(task.related_person)
        self.related_person_contact_var.set(task.related_person_contact)
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
        if not self._ensure_store():
            return

        if not self._validate_form():
            return

        store = self.store
        if store is None:
            return

        notes = self.notes_text.get("1.0", tk.END).strip()
        due_date = normalize_due_date(self.due_date_var.get())
        existing = self._selected_task()

        if existing:
            task = Task(
                task_id=existing.task_id,
                title=self.title_var.get().strip(),
                area=self.area_var.get().strip(),
                related_person=self.related_person_var.get().strip(),
                related_person_contact=self.related_person_contact_var.get().strip(),
                due_date=due_date,
                priority=self.priority_var.get(),
                notes=notes,
                status=existing.status,
                created_at=existing.created_at,
            )
            self.tasks = store.update(self.tasks, task)
        else:
            task = Task(
                title=self.title_var.get().strip(),
                area=self.area_var.get().strip(),
                related_person=self.related_person_var.get().strip(),
                related_person_contact=self.related_person_contact_var.get().strip(),
                due_date=due_date,
                priority=self.priority_var.get(),
                notes=notes,
            )
            self.tasks = store.add(self.tasks, task)
            self._clear_form(clear_feedback=False)
            self._show_save_success()
            self._refresh_tree()
            return

        self._refresh_tree()
        if self.selected_task_id in self.tree.get_children():
            self.tree.selection_set(self.selected_task_id)
            self.tree.focus(self.selected_task_id)
        self._show_save_success()

    def _show_save_success(self) -> None:
        self.form_feedback_var.set("Tarefa salva com sucesso")
        self._cancel_form_feedback_timer()
        self.form_feedback_clear_after_id = self.after(3000, self._clear_form_feedback)

    def _clear_form_feedback(self) -> None:
        self.form_feedback_var.set("")
        self._cancel_form_feedback_timer()

    def _cancel_form_feedback_timer(self) -> None:
        if not self.form_feedback_clear_after_id:
            return

        try:
            self.after_cancel(self.form_feedback_clear_after_id)
        except tk.TclError:
            pass
        self.form_feedback_clear_after_id = None

    def _clear_form(self, clear_feedback: bool = True) -> None:
        self.selected_task_id = None
        self.title_var.set("")
        self.area_var.set("")
        self.related_person_var.set("")
        self.related_person_contact_var.set("")
        self.due_date_var.set("")
        self.priority_var.set("Media")
        self.notes_text.delete("1.0", tk.END)
        self.form_mode_label.configure(text="Nova tarefa")
        self.save_button.configure(text="Criar tarefa")
        if clear_feedback:
            self._clear_form_feedback()
        self.tree.selection_remove(self.tree.selection())

    def _toggle_selected(self) -> None:
        if not self._ensure_store():
            return

        task = self._selected_task()
        if not task:
            messagebox.showinfo(APP_TITLE, "Selecione uma tarefa primeiro.")
            return

        store = self.store
        if store is None:
            return

        self.tasks = store.toggle_status(self.tasks, task.task_id)
        self._refresh_tree()
        if task.task_id in self.tree.get_children():
            self.tree.selection_set(task.task_id)
            self.tree.focus(task.task_id)

    def _delete_selected(self) -> None:
        if not self._ensure_store():
            return

        task = self._selected_task()
        if not task:
            messagebox.showinfo(APP_TITLE, "Selecione uma tarefa primeiro.")
            return

        if not messagebox.askyesno(APP_TITLE, f"Excluir a tarefa '{task.title}'?"):
            return

        store = self.store
        if store is None:
            return

        self.tasks = store.delete(self.tasks, task.task_id)
        self._clear_form()
        self._refresh_tree()


def main() -> None:
    app = TodoApp(AppSettings())
    app.mainloop()
