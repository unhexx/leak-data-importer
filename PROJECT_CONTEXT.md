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
| **Cycle Number**       | 4                                          |
| **Current Phase**      | Phase 4 — Testing, Quality & PII Safety     |
| **Active Role**        | Orchestrator → Coder (starting work)        |
| **Overall Status**    | IN_PROGRESS (Phase 3 APPROVED)             |
| **Last Updated**      | 2026-05-30                                 |

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

**Agentic Development Loop**
- Full `agentic_loop_template/` (v2.1) with 5-role cycle
- Robust Windows PowerShell support (including bash-style chaining)
- Strong emphasis on local `.venv` usage

---

## Key Architectural Decisions

- All data processing must be **deterministic** — no LLM calls inside the import/normalization pipeline.
- Strong focus on **Russian-language data quality** (names, patronymics, document formats, addresses).
- Graph modeling is the primary long-term value (relationships between people, events, locations).
- Security and PII handling are critical (hashing/tokenization planned but not yet implemented).
- Development is done through a structured self-improving agentic loop with strict role separation.

---

## Known Limitations and Risks

- Insufficient test coverage on real "dirty" leak data.
- No proper PII protection layer yet (high compliance risk).
- Database layer is still basic (no SQLAlchemy 2.0 models or migrations).
- Cross-report entity resolution / deduplication is missing (core analytical feature).
- Neo4j exporter is incomplete (no batching, constraints, or indexing strategy).
- Windows-centric tooling (PowerShell scripts) — cross-platform support is weak.

---

## Self-Improvement Guidelines for the Agentic Loop

This project uses a closed-loop agentic development process (Orchestrator → Coder → Tester → Debugger → Reviewer).

**Critical Rule — Code Comments and Documentation (Strict Enforcement):**

When any role (especially Coder, Debugger, or Reviewer) modifies source code:

- All comments, docstrings, inline explanations, and module-level documentation **must be written in natural Russian**.
- Write as a real mid/senior human developer who has been actively working on this project for several months.
- Use natural, professional Russian that a real developer would write.
- **Never** mention AI, LLM, agent, MiniMax, Grok, Claude, neural network, "as an assistant", or any indication that changes were generated or assisted by an AI system.
- The same rule applies to git commit messages (already enforced by the loop).

This rule exists to maintain code quality and authenticity. The Reviewer is responsible for catching violations.

**Self-Improvement Focus Areas (updated by Reviewer after each full cycle):**

- Effectiveness of the current role prompts and temperatures
- Quality of handoffs between roles (JSON schema adherence)
- How well the agent maintains `PROJECT_CONTEXT.md` and `SPRINTPLAN.md`
- Common failure patterns in parsing real leak data
- Improvements to the local development environment and tooling

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