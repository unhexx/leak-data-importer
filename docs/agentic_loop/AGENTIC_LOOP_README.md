# Шаблон: Саморазвивающийся Agentic Loop

> Шаблон окружения для замкнутого саморазвивающегося агентного цикла на базе MiniMax-M2.5.  
> Версия: 1.0 | Платформа: Windows (PowerShell) | Модель: MiniMax-M2.5

---

## Что это

Полный шаблон для запуска многоролевого агентного цикла, в котором одна языковая модель (MiniMax-M2.5) последовательно исполняет роли **Orchestrator → Coder → Tester → Debugger → Reviewer**, работая над задачей до полного соответствия спецификации.

Цикл:
- **Замкнутый** — Reviewer возвращает управление Orchestrator'у если задача не выполнена
- **Саморазвивающийся** — уроки каждого цикла кристаллизуются в постоянные правила
- **Детерминированный** — JSON handoff между ролями обеспечивает точную передачу состояния

---

## Структура шаблона

```
agentic_loop_template/
├── SYSTEM_PROMPT.md              ← Главный системный промпт (заполнить {{ ... }})
├── AGENT_ROLES.md                ← Инструкции для каждой из 5 ролей
├── HANDOFF_SCHEMA.md             ← Полная схема JSON передачи управления
├── TOOLS_REGISTRY.md             ← Реестр доступных инструментов
├── PROJECT_CONTEXT_TEMPLATE.md  ← Шаблон PROJECT_CONTEXT.md
├── SPRINTPLAN_TEMPLATE.md        ← Шаблон SPRINTPLAN.md
├── setup_env_template.ps1        ← Скрипт подготовки окружения (Windows PowerShell)
└── AGENTIC_LOOP_README.md        ← Этот файл
```

---

## Быстрый старт: адаптация под новый проект

### Шаг 1: Скопировать шаблон в репозиторий проекта

```powershell
Copy-Item -Recurse agentic_loop_template\* your_project_root\
```

### Шаг 2: Заполнить переменные в SYSTEM_PROMPT.md

Найдите и замените все `{{ ... }}`:

| Переменная | Описание | Пример |
|-----------|----------|--------|
| `{{ Краткое описание цели }}` | Цель проекта | Реализовать парсер OSINT-отчётов |
| `{{ TASK_SPECIFICATION.md }}` | Имя файла спецификации | `PARSER_SPEC.md` |
| `{{ Python 3.11 / ... }}` | Технологический стек | `Python 3.11, FastAPI, Redis` |
| `{{ /path/to/repo }}` | Путь к репозиторию | `C:\Projects\my-parser` |
| `{{ название-фичи }}` | Название ветки | `json-export-module` |
| `{{ Имя Фамилия }}` | Git user.name | `Алексей Петров` |
| `{{ email@domain.ru }}` | Git user.email | `aleksey@company.ru` |

### Шаг 3: Скопировать шаблоны контекстных файлов

```powershell
Copy-Item PROJECT_CONTEXT_TEMPLATE.md PROJECT_CONTEXT.md
Copy-Item SPRINTPLAN_TEMPLATE.md SPRINTPLAN.md
Copy-Item setup_env_template.ps1 scripts\setup_env.ps1
```

Заполнить `PROJECT_CONTEXT.md` и `SPRINTPLAN.md` по аналогии — заменить `{{ ... }}`.

### Шаг 4: Подготовить спецификацию задачи

Создать `TASK_SPECIFICATION.md` с:
- Полным описанием задачи
- Acceptance criteria для каждого модуля
- Edge-кейсами с ожидаемым поведением
- Примерами входных/выходных данных

### Шаг 5: Инициализировать агентный цикл

Использовать `SYSTEM_PROMPT.md` как системный промпт для MiniMax-M2.5.  
Первое сообщение пользователя: пустое или `"Начать цикл 0"`.

---

## Как работает цикл

```
┌─────────────────────────────────────────────────────────────┐
│                    ВНЕШНИЙ ЦИКЛ (sprint)                    │
│                                                             │
│  [Orchestrator] ──→ [Coder] ──→ [Tester] ──→ [Debugger]   │
│       ↑                                           │         │
│       │              [Reviewer] ←─────────────────┘         │
│       │                  │                                   │
│       └── NOT DONE ──────┘     DONE → завершение            │
└─────────────────────────────────────────────────────────────┘

Внутри каждой роли:
  PLAN → ACT → REFLECT → ACT → REFLECT → ...
  (не более 3 tool calls без REFLECT)
```

### Передача управления

Каждое сообщение агента заканчивается JSON-объектом (схема в `HANDOFF_SCHEMA.md`).  
Локальный агент (ваш runner) парсит JSON и:
1. Извлекает `handoff_to`
2. Подставляет инструкции нужной роли из `AGENT_ROLES.md`
3. Передаёт управление следующей роли

---

## Требования к локальному runner'у

Шаблон рассчитан на следующий интерфейс локального агента:

```
MiniMax-M2.5 ←→ [Local Runner] ←→ Windows PowerShell
                      ↑
                 Парсит JSON tool calls
                 Возвращает stdout/stderr
```

Runner должен поддерживать инструменты из `TOOLS_REGISTRY.md`:
- `powershell` — выполнение команд
- `read_file` / `write_file` / `append_file`
- `list_dir`
- `git_status` / `git_commit`
- `run_tests`
- `search_replace`

---

## Настройки модели (рекомендуемые)

| Роль | Temperature | Top-P | Max Tokens |
|------|-------------|-------|------------|
| Orchestrator | 0.0 | 0.9 | 4096 |
| Coder | 0.2 | 0.95 | 8192 |
| Tester | 0.0 | 0.9 | 4096 |
| Debugger | 0.2 | 0.95 | 4096 |
| Reviewer | 0.0 | 0.9 | 4096 |

---

## Правила Git (обязательные)

- Рабочая ветка: `feature-{{ название-фичи }}`
- Commit-сообщения: на русском, от лица разработчика-человека
- **Запрещено в commit-сообщениях:** AI, LLM, agent, MiniMax, нейросеть, агентный цикл
- Коммит после каждого значимого изменения (модуль, тесты, исправление)

---

## Файлы, которые редактирует агент

| Файл | Кто обновляет | Частота |
|------|--------------|---------|
| `PROJECT_CONTEXT.md` | Orchestrator (статус) + Reviewer (лог) | Каждый цикл |
| `SPRINTPLAN.md` | Orchestrator (создаёт/обновляет) + Reviewer (процессные улучшения) | Каждый цикл |
| `src/*.py` | Coder + Debugger | Фазы 1–4 |
| `tests/*.py` | Tester + Debugger | Фазы 3–4 |
| `migrations/` | Coder | Фаза 1 |
| `README.md`, `USAGE.md`, `pyproject.toml` | Reviewer | Финализация |

---

## Расширение шаблона

### Добавить новый инструмент
1. Зарегистрировать в `TOOLS_REGISTRY.md` — описание, параметры, примеры
2. Реализовать в локальном runner'е
3. Обновить системный промпт (раздел "Доступные инструменты")

### Добавить новую роль
1. Добавить блок в `AGENT_ROLES.md`
2. Обновить матрицу передачи управления в `HANDOFF_SCHEMA.md`
3. Добавить допустимое значение в `handoff_to` в схеме
4. Обновить описание ролей в `SYSTEM_PROMPT.md`

### Адаптировать под Linux / macOS
- Заменить `powershell` tool на `bash`
- Поправить пути (разделитель `/`)
- Заменить `.\venv\Scripts\Activate.ps1` на `. .venv/bin/activate`
- Обновить `setup_env.ps1` → `setup_env.sh`

---

## Ограничения шаблона

- Рассчитан на MiniMax-M2.5; для других моделей может потребоваться адаптация инструкций по INTERLEAVED THINKING и tool call форматам
- Предполагает Windows PowerShell на локальной машине
- Не включает CI/CD интеграцию (расширяется через новые tool call типы)
- Максимум 3–4 цикла запроектировано; при большем числе рекомендуется architecture review
