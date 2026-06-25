# Work Tasks

Aplicativo desktop simples para organizar tarefas de trabalho com persistencia em arquivos locais.

## Recursos

- Criar, editar, concluir, reabrir e excluir tarefas.
- Prioridade, area/projeto, pessoa relacionada, contato, data de vencimento em `dd/mm/aaaa` e observacoes.
- Quantidade de horas por tarefa, com suporte a valores decimais.
- Busca por texto e ordenacao clicando nos cabecalhos.
- Cabecalho de cada coluna com botao separado para ordenar e botao de funil para filtrar.
- Filtros por coluna com texto e selecao de valores existentes.
- Exportacao da tabela visivel para `.xlsx`, incluindo horas, observacoes e contato da pessoa relacionada.
- Mascara automatica no campo de vencimento para `dd/mm/aaaa`.
- Status calculados: `Concluída`, `No prazo`, `Vence em 7 dias`, `Vence hoje` e `Em atraso`.
- Pasta de dados configuravel pela interface.
- Persistencia automatica em `tasks.json` dentro da pasta escolhida.
- Sem dependencias externas: usa Python e Tkinter.

## Como executar

Primeiro execute o setup uma unica vez para criar a `venv` e instalar o `requirements.txt`.

### Windows

Setup inicial:

```powershell
.\setup.bat
```

Se o script nao encontrar o Python automaticamente, cole o caminho completo do `python.exe` quando solicitado.

Depois, para abrir o app:

```powershell
.\abrir_app.bat
```

Tambem e possivel rodar manualmente pela `venv`:

```powershell
.\venv\Scripts\python.exe run.py
```

### Ubuntu/Linux

Instale Python, venv e Tkinter se necessario:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-tk
```

Setup inicial:

```bash
sh ./setup.sh
```

Depois, para abrir o app:

```bash
sh ./abrir_app.sh
```

Tambem e possivel rodar manualmente pela `venv`:

```bash
./venv/bin/python run.py
```

## Configuracao

O app lembra a pasta de dados escolhida em:

- Windows: `%APPDATA%\WorkTasks\settings.json`
- Ubuntu/Linux: `${XDG_CONFIG_HOME:-~/.config}/work-tasks/settings.json`

As tarefas ficam em `tasks.json` dentro da pasta selecionada pela interface.

## Testes

Windows:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests
```

Ubuntu/Linux:

```bash
./venv/bin/python -m unittest discover -s tests
```

## Estrutura

- `run.py`: ponto de entrada.
- `requirements.txt`: dependencias pip do projeto.
- `setup.bat`: cria a `venv` no Windows e instala os requirements.
- `setup.sh`: cria a `venv` no Ubuntu/Linux e instala os requirements.
- `abrir_app.bat`: atalho para abrir o aplicativo no Windows.
- `abrir_app.sh`: atalho para abrir o aplicativo no Ubuntu/Linux.
- `src/app.py`: interface grafica.
- `src/settings.py`: configuracao da pasta de dados escolhida.
- `src/storage.py`: leitura e escrita atomica do JSON local.
- `src/task_model.py`: modelo de dados da tarefa.
- `src/xlsx_export.py`: exportacao da tabela para `.xlsx`.
- `tests/test_storage.py`: testes da camada de persistencia.
