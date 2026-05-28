# TOOLS REGISTRY — Реестр инструментов агентного цикла

> Все инструменты, доступные агенту в рамках цикла.  
> Расширяйте этот файл при добавлении новых инструментов в локальный runner.

---

## Формат вызова инструмента

Все вызовы производятся через JSON-объект, испускаемый моделью и интерпретируемый локальным агентом:

```json
{
  "tool": "<имя инструмента>",
  "<параметр1>": "<значение1>",
  "<параметр2>": "<значение2>",
  "purpose": "<краткое описание цели вызова>"
}
```

Локальный агент возвращает:
```json
{
  "tool": "<имя инструмента>",
  "exit_code": 0,
  "stdout": "...",
  "stderr": "...",
  "elapsed_ms": 1234
}
```

---

## Базовые инструменты

### `powershell` — Выполнение команды в Windows PowerShell

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `command` | string | да | Команда PowerShell |
| `working_dir` | string | нет | Рабочая директория (по умолчанию: repo root) |
| `timeout_sec` | int | нет | Таймаут в секундах (по умолчанию: 60) |

```json
{
  "tool": "powershell",
  "command": "Get-ChildItem . -Recurse -Depth 2",
  "purpose": "показать структуру репозитория"
}
```

**Правила использования:**
- Всегда использовать Windows path-разделители (`\`)
- Для активации venv: `.\venv\Scripts\Activate.ps1`
- Для запуска Python внутри venv: `.\venv\Scripts\python.exe`
- PowerShell-семантика: `$env:VAR`, `Get-Content`, `Set-Content`, etc.

---

### `read_file` — Чтение файла

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `path` | string | да | Относительный путь от repo root |
| `encoding` | string | нет | Кодировка (по умолчанию: utf-8) |
| `lines_from` | int | нет | Начальная строка (1-based) |
| `lines_to` | int | нет | Конечная строка |

```json
{
  "tool": "read_file",
  "path": "PROJECT_CONTEXT.md",
  "purpose": "прочитать текущий контекст проекта"
}
```

---

### `write_file` — Запись файла (перезапись)

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `path` | string | да | Путь от repo root |
| `content` | string | да | Содержимое файла |
| `encoding` | string | нет | Кодировка (по умолчанию: utf-8) |

```json
{
  "tool": "write_file",
  "path": "src/parser.py",
  "content": "# ...",
  "purpose": "создать основной модуль парсера"
}
```

---

### `append_file` — Дозапись в файл

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `path` | string | да | Путь от repo root |
| `content` | string | да | Текст для добавления в конец |

```json
{
  "tool": "append_file",
  "path": "PROJECT_CONTEXT.md",
  "content": "\n## Цикл 1 — ...",
  "purpose": "обновить лог саморазвития"
}
```

---

### `list_dir` — Листинг директории

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `path` | string | да | Путь от repo root |
| `recursive` | bool | нет | Рекурсивный листинг (по умолчанию: false) |
| `depth` | int | нет | Глубина рекурсии (по умолчанию: 1) |

```json
{
  "tool": "list_dir",
  "path": ".",
  "recursive": true,
  "depth": 2,
  "purpose": "проверить структуру проекта"
}
```

---

### `git_status` — Статус git-репозитория

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| _(нет обязательных)_ | | | |

```json
{
  "tool": "git_status",
  "purpose": "проверить текущее состояние репозитория"
}
```

Возвращает: текущую ветку, список изменённых файлов, staged/unstaged статус.

---

### `git_commit` — Зафиксировать изменения

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `message` | string | да | Сообщение коммита (на русском, человеческое) |
| `add_all` | bool | нет | `git add -A` перед коммитом (по умолчанию: true) |
| `files` | array | нет | Конкретные файлы для `git add` |

```json
{
  "tool": "git_commit",
  "message": "Добавил модели данных для обработки отчётов",
  "add_all": true,
  "purpose": "зафиксировать реализацию моделей"
}
```

**Запрещено в message:** AI, LLM, agent, MiniMax, нейросеть, агентный цикл, автогенерация, автоматически.

---

### `run_tests` — Запуск тестов

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `test_path` | string | нет | Путь к тестам (по умолчанию: `tests/`) |
| `coverage` | bool | нет | Включить coverage (по умолчанию: true) |
| `verbose` | bool | нет | Подробный вывод (по умолчанию: true) |
| `fail_fast` | bool | нет | Остановиться на первом провале (по умолчанию: false) |
| `markers` | string | нет | pytest markers filter, например `"unit"` |

```json
{
  "tool": "run_tests",
  "test_path": "tests/",
  "coverage": true,
  "verbose": true,
  "purpose": "запустить полный тест-сьют с покрытием"
}
```

Возвращает: количество тестов (passed/failed/error), coverage %, список провалившихся тестов.

---

### `search_replace` — Поиск и замена в файле

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `path` | string | да | Путь к файлу |
| `pattern` | string | да | Регулярное выражение для поиска |
| `replacement` | string | да | Строка замены |
| `flags` | string | нет | Флаги regex: `i` (ignorecase), `m` (multiline), `s` (dotall) |
| `count` | int | нет | Максимальное число замен (по умолчанию: все) |

```json
{
  "tool": "search_replace",
  "path": "src/parser.py",
  "pattern": "TODO: implement normalization",
  "replacement": "return normalize_field(raw_value)",
  "purpose": "реализовать нормализацию поля"
}
```

---

## Расширенные инструменты (опциональные)

Добавляйте по необходимости для конкретного проекта:

### `run_migration` — Запуск Alembic-миграций

```json
{
  "tool": "powershell",
  "command": ".\\venv\\Scripts\\python.exe -m alembic upgrade head",
  "purpose": "применить миграции БД"
}
```

### `check_db_connection` — Проверка подключения к БД

```json
{
  "tool": "powershell",
  "command": ".\\venv\\Scripts\\python.exe scripts\\check_db.py",
  "purpose": "проверить соединение с PostgreSQL"
}
```

### `lint` — Проверка стиля кода

```json
{
  "tool": "powershell",
  "command": ".\\venv\\Scripts\\python.exe -m ruff check src/ tests/",
  "purpose": "проверить стиль кода"
}
```

### `type_check` — Статическая типизация

```json
{
  "tool": "powershell",
  "command": ".\\venv\\Scripts\\python.exe -m mypy src/ --strict",
  "purpose": "проверить типы"
}
```

---

## Правила использования инструментов

1. **Не более 3 tool calls подряд** без шага REFLECT.
2. Каждый вызов должен иметь поле `"purpose"` с кратким описанием цели.
3. При получении `exit_code != 0` — анализировать stderr, не игнорировать.
4. При timeout — логировать в `issues_found`, уменьшить область команды.
5. `write_file` с большим содержимым — разбить на логические блоки, коммитить по модулям.
6. Никогда не выполнять деструктивные операции без явного обоснования в `purpose`.
