# leak-data-importer

A Python tool for securely importing, normalizing, and processing leaked or sensitive data sets.

> **Security Notice**: This tool is intended for legitimate security research, incident response, and data recovery scenarios only. Never use it to handle data you do not have explicit authorization to process. Always follow applicable laws and data protection regulations (GDPR, etc.).

## Features (Roadmap)

- Import data from various leak formats (CSV, JSON, SQL dumps, archives)
- Data normalization and schema mapping
- Deduplication and enrichment pipelines
- Safe handling of PII / sensitive fields (hashing, tokenization)
- Export to databases, data lakes, or analysis tools
- CLI + optional library usage

## Quick Start

### 1. Clone & Environment

```bash
git clone https://github.com/unhexx/leak-data-importer.git
cd leak-data-importer

# Create and activate virtual environment
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux/macOS
source .venv/bin/activate

# Install in editable mode
pip install -e ".[dev]"
```

### 2. Usage

```bash
leak-data-importer --help
```

Example (placeholder):

```bash
leak-data-importer import --source ./data/raw/leak.csv --format csv --output ./data/processed/
```

## Project Structure

```
leak-data-importer/
├── src/
│   └── leak_data_importer/
│       ├── __init__.py
│       └── cli.py
├── data/
│   ├── raw/          # NEVER commit real leak data here
│   └── processed/
├── pyproject.toml
├── README.md
└── .gitignore
```

## Development

- Python >= 3.10
- Use `ruff` for linting/formatting
- Tests with `pytest`

## Contributing

Pull requests welcome for importers, normalizers, and exporters.

## License

MIT License — see [LICENSE](LICENSE) file.

## Disclaimer

This project does **not** distribute or host any leaked data. Users are fully responsible for the legality and ethics of the data they process with this tool.

## Autonomous Agentic Development

Для длительной автономной разработки рекомендуется использовать улучшенный **Agentic Loop Template**:

- Расположение: `agentic_loop_template/`
- Полный архив для старта новых проектов: `agentic_loop_template_v2.zip`
- Особенности: принудительное использование локального `.venv`, английские инструкции + требование писать коммиты на русском от лица разработчика, хорошая совместимость с неинтерактивными агентами (Blackbox и др.)

**Быстрый старт с Blackbox + MiniMax2.5 в VSCode:**

```powershell
.\agentic_loop_template\Agent-Init.ps1
```

Подробная инструкция — в `agentic_loop_template/Agent-Init.md`.

## Windows helpers

Для комфортной работы в классической Windows PowerShell в репозитории есть инструмент:

**posh-bash-chaining**

Позволяет использовать `&&`, `||`, `|&`, `&>` и `>&` точно как в bash.

Установка:

```powershell
cd posh-bash-chaining
.\Install.ps1
```

Подробнее — смотри [posh-bash-chaining/README.md](posh-bash-chaining/README.md)
