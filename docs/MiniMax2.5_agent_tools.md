# Tools for Local Development Agent (MiniMax2.5)

This document describes the **tools** a local autonomous development agent (such as MiniMax2.5 or similar) can reliably use while working on the `leak-data-importer` project.

> **Recommended:** For long-running autonomous development, use the improved Agentic Loop Template located at `agentic_loop_template/`. It enforces local Python venv usage, English instructions + Russian developer-style commits, and is tuned for MiniMax2.5 in non-interactive agent environments.

The goal is to give the agent a clear, stable interface so it can develop features, debug, test, and ship code without constant human intervention.

---

## Core Principles for the Agent

- Always work inside `C:\_PROJECT\leak-data-importer` (or the equivalent absolute path on the machine).
- Prefer making small, incremental, well-tested changes.
- Every meaningful change that passes basic checks **must** be committed with a natural Russian commit message (see the agentic prompt).
- Never push broken code. Always run tests / smoke tests before pushing.
- When you encounter encoding or parsing problems with real leak files — treat them as first-class citizens of the project.

---

## Available Tool Categories

### 1. File System & Code Editing
- Read any file (source, tests, docs, configs)
- Write / create new files
- Edit existing files (search & replace style)
- List directories recursively (respecting .gitignore where reasonable)
- Create directories

**Restrictions**: Never delete the real files in `data/raw/` that contain actual leaked data. Work on copies or fixtures in `tests/fixtures/`.

### 2. Git Operations (Critical)
The agent **must** be able to do the full cycle:
- `git status`
- `git diff`
- `git add`
- `git commit -m "..."` (messages **in Russian**, sounding like a real developer)
- `git pull --rebase origin main` (or equivalent)
- `git push origin main`
- `git log --oneline -10`
- `git fetch origin`

Recommended safe workflow:
```bash
git pull --rebase origin main
# ... do work ...
git add -A
git commit -m "реализовал парсер для отчётов report_*.txt + добавил нормализацию телефонов"
git push origin main
```

### 3. Python Execution & Testing
- Run any Python module or script via the project venv (`.\.venv\Scripts\python.exe`)
- Run `pytest` (with specific files or markers)
- Run `ruff check .` and `ruff format`
- Run `mypy src`
- Execute one-off experiments against the importer on `tests/fixtures/`

Example:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q --tb=short
```

> Для использования bash-операторов (`&&`, `||`, `|&`, `&>`) в обычной Windows PowerShell смотри `posh-bash-chaining/` — там есть удобный установщик.

### Запуск Agentic Loop через Blackbox + MiniMax2.5

Для длительной автономной работы рекомендуется использовать улучшенный шаблон из `agentic_loop_template/`.

**Быстрый старт:**

1. Выполни один раз:
   ```powershell
   .\agentic_loop_template\Agent-Init.ps1
   ```

2. В настройках Blackbox добавь в Custom Instructions блок из `agentic_loop_template/Agent-Init.md`.

3. В качестве первого сообщения используй промпт, сгенерированный скриптом (или текст из `Agent-Init.md`).

Шаблон специально адаптирован под неинтерактивные сессии Blackbox и модель MiniMax2.5. Он автоматически подключает локальное Python-окружение и требует писать коммиты на русском от лица разработчика.

### 4. Project-Specific High-Level Tools (Recommended to Implement)

The agent should eventually be able to call these via CLI or Python:

| Tool / Command                        | Purpose                                      | Example |
|---------------------------------------|----------------------------------------------|--------|
| `leak-data-importer import --source tests/fixtures/sample_report.txt --format txt_report --dry-run` | Parse a file and show extracted records     | Primary development tool |
| `leak-data-importer import --source data/raw/ --format txt_report --output data/processed/` | Process real (dangerous) dumps              | Use with extreme caution |
| Custom Python entrypoints in `scripts/` | One-off analysis, statistics, export        | To be created by the agent |

### 5. Debugging & Inspection Tools
- Print / pretty-print `PersonRecord` objects
- Run the importer in debug mode with `print()` or logging on specific blocks
- Compare output against expected normalized data (golden tests)
- Inspect encoding of any file in `data/raw/`

### 6. Environment & Dependency Tools
- Modify `pyproject.toml` (dependencies, scripts)
- Reinstall the project in the venv: `python -m pip install -e ".[dev]"`
- Add new dev dependencies when genuinely needed

---

## What the Agent Should NOT Do

- Never commit or push real personal data from `data/raw/` (the .gitignore already protects this).
- Never hardcode real names, phones, or emails from production leaks into tests or code.
- Never force-push unless explicitly authorized for a very good reason.
- Do not create huge PRs. Prefer many small, reviewable commits.

---

## Success Criteria for the Agent

The agent is considered effective when it can, in a continuous loop:
1. Pull latest changes
2. Identify the next valuable improvement for the `txt_report` importer (or new importers)
3. Implement + add a small test
4. Verify it works on both the synthetic fixture and the real samples (without leaking data)
5. Write a natural Russian commit message
6. Push safely
7. Repeat

This document should be kept up-to-date as the project grows.
