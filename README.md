# Work Tasks

Aplicativo desktop simples para organizar tarefas de trabalho com persistencia em arquivos locais.

## Recursos

- Criar, editar, concluir, reabrir e excluir tarefas.
- Prioridade, area/projeto, data de vencimento em `dd/mm/aaaa` e observacoes.
- Busca por texto, filtro por status calculado e ordenacao clicando nos cabecalhos.
- Cabecalho de cada coluna com botao separado para ordenar e botao de funil para filtrar.
- Filtros por coluna com texto e selecao de valores existentes.
- Mascara automatica no campo de vencimento para `dd/mm/aaaa`.
- Status calculados: `Concluída`, `No prazo`, `Vence em 7 dias`, `Vence hoje` e `Em atraso`.
- Persistencia automatica em `data/tasks.json`.
- Sem dependencias externas: usa Python e Tkinter.

## Como executar

No Windows, execute o arquivo:

```powershell
.\abrir_app.bat
```

Ou rode manualmente com Python 3:

```powershell
py -3 run.py
```

Se o comando `py` nao estiver disponivel, use:

```powershell
python run.py
```

## Testes

```powershell
py -3 -m unittest discover -s tests
```

## Estrutura

- `run.py`: ponto de entrada.
- `abrir_app.bat`: atalho para abrir o aplicativo no Windows.
- `src/app.py`: interface grafica.
- `src/storage.py`: leitura e escrita atomica do JSON local.
- `src/task_model.py`: modelo de dados da tarefa.
- `tests/test_storage.py`: testes da camada de persistencia.
