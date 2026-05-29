# Agentic Loop Template (MiniMax2.5)

A complete, self-contained template for running a closed-loop, self-improving multi-role agentic development cycle powered by **MiniMax2.5**.

The agent cycles through roles (Orchestrator → Coder → Tester → Debugger → Reviewer) until the task fully meets the specification. All work happens inside a **local Python virtual environment** that is created and maintained by the agent itself.

## Key Improvements in This Version

- **Mandatory local Python environment**: The Orchestrator must ensure a `.venv` exists and all requirements from `pyproject.toml` (or `requirements.txt`) are installed at the beginning of every cycle.
- **Non-interactive friendly**: Designed to work when AI agents (Blackbox, Continue, etc.) spawn fresh PowerShell processes.
- **English primary language** with explicit requirement for **Russian commit messages** written in the voice of a real human developer (no mention of AI, LLM, agent, or model names in commits).
- Aligned with the project's `docs/MiniMax2.5_agent_tools.md`.

## Directory Structure

```
agentic_loop_template/
├── README.md
├── SYSTEM_PROMPT.md              # Main system prompt
├── AGENT_ROLES.md
├── HANDOFF_SCHEMA.md
├── TOOLS_REGISTRY.md
├── PROJECT_CONTEXT_TEMPLATE.md
├── SPRINTPLAN_TEMPLATE.md
├── setup_env.ps1                 # Python venv + requirements bootstrap
├── Profile-Bootstrap.ps1         # PowerShell profile helper
├── Agent-Init.ps1                # Robust setup for Blackbox + VSCode (auto-heals broken .venv)
└── Agent-Init.md                 # Detailed guide for Blackbox / MiniMax2.5 in VSCode
```

## Quick Start (Recommended for Blackbox + MiniMax 2.5)

1. Copy the template into your project root.
2. Fill **all** `{{ ... }}` placeholders in `SYSTEM_PROMPT.md` (see the Pre-Flight Checklist inside it).
3. Create your main specification file (e.g. `TASK_SPECIFICATION.md` or `TODO.md`).
4. **For Blackbox + VSCode users** (strongly recommended):
   ```powershell
   .\agentic_loop_template\Agent-Init.ps1
   ```
   This prepares the Python environment and generates a ready-to-use starter prompt.

5. Start the loop by sending the content of `SYSTEM_PROMPT.md` (with placeholders filled) as the system prompt to MiniMax 2.5 via Blackbox.

See `Agent-Init.md` for the detailed Blackbox + VSCode launch guide, including recommended Custom Instructions and the first message.

## Environment Management (Critical)

The agent **must** maintain a local Python environment:

- At the start of every cycle, the **Orchestrator** should call:
  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\setup_env.ps1
  ```
- The script is idempotent and prefers `pyproject.toml`.
- Never run Python commands outside the activated `.venv`.

See `setup_env.ps1` for details.

## Commit Rules (Strict)

All git commits **must** be written in natural Russian, in the voice of a real mid/senior human developer who has been working on the project for months.

**Forbidden** in commit messages:
- Any mention of AI, LLM, agent, MiniMax, Grok, Claude, "as an assistant", "нейросеть", "агент", etc.

Good examples (from real developer style):
- "добавил более устойчивый парсер блоков для report_*.txt"
- "починил нормализацию СНИЛС и телефонов, добавил тесты на edge cases"

The Orchestrator and Reviewer are responsible for enforcing this rule.

## Adaptation to MiniMax2.5

This template is tuned for MiniMax2.5. Recommended settings per role are included in `SYSTEM_PROMPT.md`.

It is designed to be compatible with the tool set described in `docs/MiniMax2.5_agent_tools.md` of the host project.

## Standalone Archive

A ready-to-use zip of this template (for starting new autonomous agentic projects) is provided as `agentic_loop_template_v3_final.zip`.

Для запуска нового цикла Orchestrator'а используйте подготовленные промпты в корне проекта:
- `orchestrator_start_prompt_*.md` — готовые промпты под конкретные фазы
- `orchestrator_start_prompt_template.md` — универсальный шаблон для будущих циклов или возобновления работы.

## Applying to an Existing Project

1. Copy the template.
2. Wire the `setup_env.ps1` call into your existing scripts.
3. Update `docs/MiniMax2.5_agent_tools.md` (or equivalent) with a link to the new `agentic_loop_template/`.
4. Add a note in the root README about the autonomous development loop.

## Recommendations (Added for This Project)

- Always run the environment bootstrap as the very first action of the Orchestrator in cycle 0 and after any `git pull`.
- Keep `PROJECT_CONTEXT.md` under 3000 tokens by aggressive summarization.
- After 3 failed cycles without reaching DONE — force an architecture review step.
- For heavy data-processing projects (like leak-data-importer), add a dedicated "Data Sanity Checker" role if needed.

---

**License**: MIT (same as host project)

Use this template responsibly and only on codebases you have full rights to modify.