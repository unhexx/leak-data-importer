# PROJECT_CONTEXT.md

> **Source of Truth:** `TODO.md` and `TASK_SPECIFICATION.md` (when present)  
> This file is maintained by the Orchestrator (for status) and the Reviewer (for self-improvement log).  
> Keep it under ~3000 tokens. Compress older entries when necessary.  
> **Language:** All content in this file is in English.

---

## Project Identification

| Parameter       | Value                                      |
|-----------------|--------------------------------------------|
| **Project**     | leak-data-importer                         |
| **Goal**        | Build a production-ready, secure pipeline for importing, normalizing, and analyzing leaked/sensitive data with graph-based relationship analysis. |
| **Tech Stack**  | Python 3.11+, Pydantic v2, SQLAlchemy 2.0 (target), Neo4j, Streamlit, pytest, ruff + mypy |
| **Current Branch** | main (or active feature branch)          |
| **Git User**    | Евгений Чистяков <unhandled@exception.expert> |

---

## Current State

| Field                  | Value                                      |
|------------------------|--------------------------------------------|
| **Cycle Number**       | 6                                          |
| **Current Phase**      | Phase 5 start: Production Readiness (Exporters, Visualization, CLI, CI/CD) — detailed launch plan adopted |
| **Active Role**        | Orchestrator (Cycle 6 kickoff / Phase 5)   |
| **Overall Status**    | Phase 4 COMPLETE (Cycle 5); Cycle 6 Orchestrator bootstrap + plan.md adoption complete; first handoff prepared |
| **Last Updated**      | 2026-06 (Cycle 6 Orchestrator after Agent-Init + pull + context sync) |

### What Already Exists (High-Level)

**Core Domain Models**
- Basic `Person` model and related entities in `src/leak_data_importer/models/`
- Graph entities and relationships in `src/leak_data_importer/graph/`

**Importers**
- `TxtReportImporter` (partial but functional for real reports)
- `DossierDBImporter` (basic)

**Parsers & Normalization**
- `dossier_parser.py` and `normalization.py` with support for Russian names, phones, passports, SNILS, addresses
- Handling of different encodings

**Graph Layer**
- Entity factories and basic relationship modeling
- Initial Neo4j exporter (incomplete)

**Infrastructure**
- CLI entry point
- Streamlit visualization app (basic)
- Database schema draft (`db/schema.sql`)
- Local venv management scripts (`scripts/setup.ps1`, `agentic_loop_template/setup_env.ps1`)

**Development Loops (dual mode)**
- Heavy: full `agentic_loop_template/` (v2.1) with 5-role cycle (Orchestrator → Coder → Tester → Debugger → Reviewer), JSON handoffs, self-improvement artifacts
- Lightweight: `agentless_loop/` (Solver Loop) — single-model Inspect→Define success→Smallest vertical slice→Proportional verification→Reflect (рекомендуется для прямой работы в Grok CLI и быстрых итераций)
- Общие правила (русский язык коммитов/комментариев, .venv-only, запрет упоминаний AI) — `agentic_loop_template/DEVELOPMENT_STANDARDS.md` + `AGENTS.md`
- Robust Windows PowerShell support (including bash-style chaining via posh-bash-chaining/)

---

## Key Architectural Decisions

- All data processing must be **deterministic** — no LLM calls inside the import/normalization pipeline.
- Strong focus on **Russian-language data quality** (names, patronymics, document formats, addresses).
- Graph modeling is the primary long-term value (relationships between people, events, locations).
- Security and PII handling are critical (hashing/tokenization planned but not yet implemented).
- Development is done through structured self-improving loops (dual-mode: heavy agentic or lightweight agentless Solver Loop) with strict standards on language, quality, and environment.

---

## Known Limitations and Risks (updated Cycle 6 after Agent-Init bootstrap + code review + plan adoption)

- Neo4j exporter largely functional (batch UNWIND + simple constraints in neo4j_exporter.py + export_person_links; see prior handoff); needs full parity audit vs DB models + error handling + masking options.
- Additional exporters (CSV, JSON Lines, Parquet) **absent** — highest priority per plan.md Phase 5.2.
- Streamlit usable (import dashboard, entity detail, search, pyvis) but limited (hardcoded, capped lists, in-mem, incomplete export wiring).
- CLI import functional for txt_report; export/analyze/link stubs only.
- No .github/workflows, no Dockerfile/docker-compose.
- Docs: solid high-level + agentic instructions; missing rich runnable examples (synthetic), SECURITY runbook, USAGE with workflows.
- PII storage protection (hash/tokenize) partial (redaction + PiiSafeLogger strong in code paths).
- Windows-first (Agent-Init + posh-bash excellent); fixture sample_report.txt deleted in history (synthetic fixtures + generator planned Phase 7).
- Branch was behind origin (3 doc commits) — ff pull done in kickoff; tracked delete of fixture remains.
- Detailed to-launch plan (Phases 5 complete + 6 deploy foundation + 7 hardening + 8 docs/release/launch, exit criteria, best practices from ETL/PII/Neo4j/ER research) now lives in session plan.md. Execution strictly via project 5-role agentic loop (Russian human-dev commits/comments, last_agent_completion, UTF-8, venv). Grok tools (search_replace, terminal scripts, tdd/review skills, subagents) used only to accelerate within the loop discipline.

---

## Self-Improvement Guidelines for Development Loops

This project supports two complementary development modes:

- **Agentic** (heavy): closed-loop process with strict role separation (Orchestrator → Coder → Tester → Debugger → Reviewer) and JSON handoffs. Use for complex phases.
- **Agentless** (lightweight Solver Loop): single strong model follows Inspect → Define success → Smallest vertical slice → Proportional verification → Reflect. Recommended default for direct work in this Grok CLI, Cursor, etc. See `AGENTS.md` + `agentless_loop/`.

Both modes share the same non-negotiable standards (see `agentic_loop_template/DEVELOPMENT_STANDARDS.md` and `AGENTS.md`).

**Critical Rule — Code Comments and Documentation (Strict Enforcement):**

When any role (especially Coder, Debugger, or Reviewer) modifies source code:

- All comments, docstrings, inline explanations, and module-level documentation **must be written in natural Russian**.
- Write as a real mid/senior human developer who has been actively working on this project for several months.
- Use natural, professional Russian that a real developer would write.
- **Never** mention AI, LLM, agent, MiniMax, Grok, Claude, neural network, "as an assistant", or any indication that changes were generated or assisted by an AI system.
- The same rule applies to git commit messages (already enforced by the loop).

This rule exists to maintain code quality and authenticity. The Reviewer is responsible for catching violations.

**Self-Improvement Focus Areas (updated by Reviewer after each full cycle):**

- Strategic product direction: After completing core Phase 5 technical items, prioritize turning the strong graph + normalization engine into a usable product. The detailed plan for "Production-Grade Investigation Interface" (Idea #2) is a key vehicle for this — it directly addresses the gap between powerful internals and analyst adoption.

- Effectiveness of the current role prompts and temperatures (especially for MiniMax 2.5 on exporter/visualization tasks)
- Quality of handoffs between roles (JSON schema adherence) and integration of `last_agent_completion.json`
- How well the agent maintains `PROJECT_CONTEXT.md`, `SPRINTPLAN.md`, and the new Phase 5 artifacts
- Common failure patterns when implementing exporters or visualization features
- Improvements to the local development environment, tooling, and agentic loop (including UTF-8 and file-writing standards)

---

## Recent Cycle History (Self-Improvement Log Summary)

| Cycle | Main Focus                  | Key Outcome                          | Lessons for Loop                  |
|-------|-----------------------------|--------------------------------------|-----------------------------------|
| 0     | Initial seeding             | Created baseline PROJECT_CONTEXT and SPRINTPLAN | Need stronger initial context seeding |

*(Reviewer will append real entries after each completed external cycle)*

---

## Open Questions / Areas Requiring Attention

- How to safely handle and store real PII during development and testing?
- Best strategy for fuzzy entity resolution across multiple reports?
- Should we introduce a dedicated "Data Quality" role or keep it inside Coder/Tester?

---

**Remember:** This file is the living memory of both the project state **and** how effectively the agentic loop is operating. Keep it honest and actionable.