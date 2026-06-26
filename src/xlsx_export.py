from __future__ import annotations

from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from .task_model import Task, task_state


EXPORT_HEADERS = (
    "Tarefa",
    "Area/Projeto",
    "Grupo",
    "Pessoa relacionada",
    "Contato da pessoa relacionada",
    "Prioridade",
    "Vencimento",
    "Horas",
    "Status",
    "Observacoes",
)
XMLNS_SPREADSHEET = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def export_tasks_to_xlsx(tasks: Iterable[Task], file_path: str | Path) -> Path:
    output_path = Path(file_path)
    if output_path.suffix.lower() != ".xlsx":
        output_path = output_path.with_suffix(".xlsx")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [EXPORT_HEADERS, *(_task_to_row(task) for task in tasks)]

    with ZipFile(output_path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml())
        archive.writestr("_rels/.rels", _package_relationships_xml())
        archive.writestr("docProps/app.xml", _app_properties_xml())
        archive.writestr("docProps/core.xml", _core_properties_xml())
        archive.writestr("xl/workbook.xml", _workbook_xml())
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_relationships_xml())
        archive.writestr("xl/worksheets/sheet1.xml", _worksheet_xml(rows))

    return output_path


def _task_to_row(task: Task) -> tuple[str, ...]:
    return (
        task.title,
        task.area,
        task.group,
        task.related_person,
        task.related_person_contact,
        task.priority,
        task.due_date,
        task.hours,
        task_state(task),
        task.notes,
    )


def _worksheet_xml(rows: list[tuple[str, ...]]) -> str:
    row_xml = "\n".join(_row_xml(index, row) for index, row in enumerate(rows, start=1))
    columns_xml = "\n".join(
        f'<col min="{index}" max="{index}" width="{width}" customWidth="1"/>'
        for index, width in enumerate((32, 20, 18, 24, 30, 14, 14, 12, 18, 42), start=1)
    )
    dimension = f"A1:{_column_name(len(EXPORT_HEADERS))}{max(len(rows), 1)}"

    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="{XMLNS_SPREADSHEET}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="{dimension}"/>
  <sheetViews>
    <sheetView workbookViewId="0"/>
  </sheetViews>
  <sheetFormatPr defaultRowHeight="15"/>
  <cols>
    {columns_xml}
  </cols>
  <sheetData>
    {row_xml}
  </sheetData>
</worksheet>'''


def _row_xml(row_index: int, row: tuple[str, ...]) -> str:
    cells = "".join(
        _cell_xml(row_index, column_index, value)
        for column_index, value in enumerate(row, start=1)
    )
    return f'<row r="{row_index}">{cells}</row>'


def _cell_xml(row_index: int, column_index: int, value: str) -> str:
    cell_reference = f"{_column_name(column_index)}{row_index}"
    text = escape(_clean_xml_text(value))
    return f'<c r="{cell_reference}" t="inlineStr"><is><t xml:space="preserve">{text}</t></is></c>'


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = f"{chr(65 + remainder)}{name}"
    return name


def _clean_xml_text(value: object) -> str:
    text = str(value or "")
    return "".join(character for character in text if _is_valid_xml_character(character))


def _is_valid_xml_character(character: str) -> bool:
    codepoint = ord(character)
    return (
        character in "\t\n\r"
        or 0x20 <= codepoint <= 0xD7FF
        or 0xE000 <= codepoint <= 0xFFFD
        or 0x10000 <= codepoint <= 0x10FFFF
    )


def _content_types_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>'''


def _package_relationships_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''


def _workbook_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Tarefas" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>'''


def _workbook_relationships_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''


def _app_properties_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Work Tasks</Application>
</Properties>'''


def _core_properties_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>Work Tasks</dc:creator>
  <cp:lastModifiedBy>Work Tasks</cp:lastModifiedBy>
</cp:coreProperties>'''
