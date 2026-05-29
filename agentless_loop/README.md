# Agentless Loop (Solver Loop)

Лёгкий одноагентный режим разработки для сильных моделей (Grok, Claude, GPT-4o, MiniMax и др.) в инструментах прямого взаимодействия: этот Grok CLI, Blackbox (прямой чат), Cursor Agent, Continue и т.п.

В отличие от `agentic_loop_template/` (многоролевая машина Orchestrator → Coder → Tester → Debugger → Reviewer со строгими JSON-хandoff по HANDOFF_SCHEMA), здесь **одна модель** последовательно проходит цикл сама, без передачи управления между ролями.

## Когда использовать agentless

- Быстрые итерации на сильной модели (включая работу в этом Grok CLI), где overhead от ролевой машины избыточен.
- Прямая работа без Blackbox/VSCode-агента (или когда хочется минимального количества артефактов).
- Задачи, которые хорошо ложатся на паттерн Solver Loop (см. SOLVER_LOOP.md).
- Когда не нужна жёсткая многоуровневая проверка (полноценный agentic — для очень крупных/рискованных фаз).

Полноценный agentic loop оставляй для сложных фаз с высоким риском (Phase 5 экспортеры + визуализация, масштабные рефакторинги).

## Основной цикл (Solver Loop)

Максимум **3 tool-вызова** без рефлексии внутри кластера.

1. **Inspect** — полностью прочитай релевантный код (importers, parsers/normalization, graph, тесты, фикстуры). Не начинай править, пока не понял «spine» системы.
2. **Define success** — чётко сформулируй measurable исход (тест прошёл на фикстуре, нормализация дала ожидаемый результат для СНИЛС/паспорта, экспорт в Neo4j создал верные узлы/связи и т.д.).
3. **Smallest vertical slice** — реализуй самый маленький end-to-end кусок, который доказывает, что идея работает.
4. **Proportional verification** — проверь на поверхности: pytest (с фикстурами!), ручная симуляция через CLI/Streamlit, чтение логов. Никогда не трогай реальные файлы в data/raw/.
5. **Reflect** — что сработало, что нет, нужно ли `git reset`. Только после этого расширяй scope или переходи к следующей задаче.

После рефлексии — можно новый кластер до 3 вызовов.

## Обязательные правила проекта (не нарушать)

- Все коммиты, комментарии в коде, docstrings — **только естественный русский**, голос реального mid/senior разработчика, работавшего над проектом месяцы.
- **Полный запрет** слов: AI, LLM, агент, нейросеть, MiniMax, Grok, Claude, "as an assistant" и т.п. в коммитах и комментариях к коду (см. `agentic_loop_template/DEVELOPMENT_STANDARDS.md`).
- Любая работа с Python — **только внутри `.venv`** (используй `scripts/setup.ps1` или `agentic_loop_template/setup_env.ps1`).
- Весь импорт/нормализация/граф — строго детерминированные. LLM никогда не вызывается внутри pipeline.
- Реальные утечки данных в `data/raw/` — только для анализа, никогда не коммитить и не выводить в логах/экспортах.

## Быстрый старт (для Grok CLI / Blackbox / Cursor)

1. В начале каждой сессии (или после `git pull`) обязательно:
   ```powershell
   . .\scripts\setup.ps1
   ```
   (или эквивалент из agentic_loop_template, если нужно больше контроля).

2. Прочитай в таком порядке (агрессивно суммируй длинные файлы):
   - `AGENTS.md` (главные правила + выбор режима)
   - `agentless_loop/README.md` + `agentless_loop/SOLVER_LOOP.md`
   - `PROJECT_CONTEXT.md` + `SPRINTPLAN.md` (текущий статус)
   - `TODO.md` (текущие задачи)
   - Ключевые исходники: `src/leak_data_importer/parsers/normalization.py`, `importers/txt_report.py`, `graph/`, тесты и фикстуры.

3. Выбери 1–2 задачи из TODO/SPRINTPLAN в стиле INVEST (маленькие, с чётким критерием успеха).

4. Применяй Solver Loop к каждой задаче (максимум 3 tool call → Reflect).

5. После значимого рабочего среза — коммит на естественном русском.

6. В конце сессии обнови:
   - `PROJECT_CONTEXT.md`
   - `SPRINTPLAN.md`
   - При необходимости — `TODO.md` и `SELF_IMPROVEMENT_LOG.md`

## Полезные файлы для agentless-работы

- `AGENTS.md` — переносимые правила + описание двух режимов
- `agentless_loop/SOLVER_LOOP.md` — практический паттерн с примерами под leak-data-importer
- `agentic_loop_template/DEVELOPMENT_STANDARDS.md` — конституция (русский язык, качество, UTF-8, self-improvement)
- `scripts/setup.ps1` — основной bootstrap окружения
- `PROJECT_CONTEXT.md`, `SPRINTPLAN.md`, `TODO.md`
- Фикстуры: `tests/fixtures/`

## Отличия от agentic_loop_template

| Аспект                  | agentic_loop_template                          | agentless_loop (Solver)                     |
|-------------------------|------------------------------------------------|---------------------------------------------|
| Кол-во ролей            | 5 (Orchestrator, Coder, Tester, Debugger, Reviewer) | 1 (модель сама)                            |
| Handoff                 | Строгий JSON по HANDOFF_SCHEMA + handoff_*.json | Нет, только рефлексия в тексте + малые коммиты |
| STATE файлы             | Много (handoff_*.json, last_agent_completion.json, reports/) | PROJECT_CONTEXT + SPRINTPLAN + TODO + AGENTS |
| Overhead                | Высокий (идеально для длинных автономных прогонов) | Низкий (быстрые итерации в CLI/Grok)       |
| Лучше для               | Очень сложные задачи, новички в коде, Phase 5 экспортеры | Сильные модели, прямой Grok, быстрые вертикальные срезы |
| Внутренний паттерн      | Solver Loop внутри каждой роли                 | Solver Loop — основной                      |

## Self-improvement

Даже в agentless-режиме после 2–3 кластеров делай architecture review и обновляй `PROJECT_CONTEXT.md` + `SELF_IMPROVEMENT_LOG.md` разделом уроков.

При систематических проблемах (забываешь читать spec, делаешь слишком большие прыжки) — переходи на agentic_loop_template или ужесточай правила в AGENTS.md.

---

**Лицензия**: MIT (как у проекта).

Используй ответственно. Все артефакты — в стиле реального разработчика. Реальные данные утечек никогда не покидают `data/raw/` и не попадают в коммиты/логи.