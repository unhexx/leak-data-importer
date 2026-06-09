# SPRINTPLAN.md

> This file is updated by the **Orchestrator** at the start of each cycle and by the **Reviewer** at the end of each cycle.  
> All tasks must follow the INVEST principle: Independent, Negotiable, Valuable, Estimable, Small, Testable.  
> Language: English (instructions and planning). Code comments remain in Russian per project rules.

---

## Sprint Metadata

| Parameter           | Value                                      |
|---------------------|--------------------------------------------|
| **Cycle Number**    | 6                                          |
| **Sprint Goal**    | Phase 5: Production Readiness - Complete Exporters, Visualization, CLI, CI/CD and Documentation |
| **Start Date**     | 2026-05-30                                 |
| **Target Completion** | End of Cycle 6                            |

---

## Current Priorities (from TODO.md and Phase 4 completion)

1. Complete Neo4j exporter (batch, indexes, constraints) and add other exporters (CSV, JSON Lines, Parquet) — high value for analysis
2. Significantly enhance Streamlit visualization and UX
3. Enhance CLI with export, analyze, and link commands
4. Add CI/CD (GitHub Actions for lint, test, typecheck)
5. Improve documentation (API docs, user guide, security guidelines, examples)
6. Production hardening (Docker support, cross-platform notes, final PII storage protection if needed)

---

## Phase 0 — Environment & Context (Orchestrator)

| #   | Task                                      | Acceptance Criteria                                      | Status |
|-----|-------------------------------------------|----------------------------------------------------------|--------|
| 0.1 | Run environment bootstrap                 | `.venv` is healthy, all dependencies installed           | ✅ Done (Agent-Init.ps1 + venv + deps in Cycle 6) |
| 0.2 | Read full current context                 | `TODO.md`, `PROJECT_CONTEXT.md`, this file + plan.md reviewed | ✅ Done (Cycle 6 Orchestrator) |
| 0.3 | Validate agentic loop readiness           | All key files from `agentic_loop_template/` present; DEVELOPMENT_STANDARDS + HANDOFF_SCHEMA + roles understood | ✅ Done |
| 0.4 | Create initial SPRINTPLAN and PROJECT_CONTEXT | Both files exist with meaningful English content         | ✅ (prior cycles) |
| 0.5 | Set up git identity (if needed)           | `git config user.name` and `user.email` are realistic    | ✅ Done (Евгений Чистяков) |
| 0.6 | Adopt detailed launch-to-deploy plan      | plan.md (full session plan with Phases 5-8, exit criteria, best practices integration) read and used as north star | ✅ Done (this cycle) |

---

## Phase 1 — Graph Modeling & Neo4j Foundation (High Priority)

| #   | Task                                              | Acceptance Criteria                                                                 | Status |
|-----|---------------------------------------------------|-------------------------------------------------------------------------------------|--------|
| 1.1 | Extend graph entity model                         | Support for new entity types (events, locations, documents) with proper relationships | ✅ Done |
| 1.2 | Improve Neo4j exporter                            | Supports batch inserts, basic constraints, and indexing strategy                    | ✅ Done |
| 1.3 | Add temporal relationships                        | `registered_at` and event dates are properly modeled and exported                   | ✅ Done |
| 1.4 | Write integration tests for graph export          | Real sample reports can be imported and exported to a test Neo4j instance           | ✅ Done |
| 1.5 | Commit graph layer improvements                   | Natural Russian commit message, human developer style                               | ✅ Done |

---

## Phase 2 — Database Layer Modernization

| #   | Task                                              | Acceptance Criteria                                                                 | Status |
|-----|---------------------------------------------------|-------------------------------------------------------------------------------------|--------|
| 2.1 | Introduce SQLAlchemy 2.0 models                   | Core tables (persons, documents, events, links) are properly mapped                 | ✅ Done |
| 2.2 | Set up Alembic migrations                         | `alembic upgrade head` works cleanly from a fresh database                          | ✅ Done |
| 2.3 | Refactor existing DB code                         | `dossier_db_importer.py` and related modules use the new ORM layer                  | ✅ Done |
| 2.4 | Add basic CRUD operations with proper typing      | Repository pattern or service layer for main entities                               | ✅ Done |

---

## Phase 3 — Entity Resolution & Deduplication (Core Value)

| #   | Task                                              | Acceptance Criteria                                                                 | Status |
|-----|---------------------------------------------------|-------------------------------------------------------------------------------------|--------|
| 3.1 | Design and implement person linker                | Multiple fuzzy matching strategies (name + birthdate, phone, document number)       | ✅ Done |
| 3.2 | Cross-report deduplication                        | Ability to detect the same person across different reports with confidence scores   | ✅ Done |
| 3.3 | Persist linking decisions                         | Links are stored in DB and reflected in the graph                                   | ✅ Done |
| 3.4 | Add evaluation harness for linking quality        | Simple metrics or manual review tooling for linking accuracy                        | ✅ Done |

---

## Phase 5 — Production Readiness: Exporters, Visualization, CLI, CI/CD and Documentation

| #   | Task                                              | Acceptance Criteria                                                                 | Status |
|-----|---------------------------------------------------|-------------------------------------------------------------------------------------|--------|
| 5.1 | Complete Neo4j exporter (batch, indexes, constraints) | Full support for all current entities (Person, links, etc.); batch export works; indexes and constraints in place | ☐ (code largely present in neo4j_exporter.py; harden + parity in this cycle per plan.md) |
| 5.2 | Implement CSV and JSON Lines exporters            | Core exporters in exporters/ module; handle current entity types (graph + flat); tested with synthetic data + redaction; PII-safe | ☐ (primary first task for Coder this cycle) |
| 5.3 | Significantly enhance Streamlit app               | Improved UX (filters, search); better graph visualization; export buttons integrated; handles real data volumes | ☐      |
| 5.4 | Enhance CLI with export and analyze commands      | New subcommands (export, analyze, link) with good help and examples; integrated with existing importers | ☐      |
| 5.5 | Add basic GitHub Actions CI                       | .github/workflows/ with lint, test, and typecheck jobs on push/PR; passes cleanly | ☐      |
| 5.6 | Improve project documentation                     | Expanded README with real examples; added security guidelines and API notes; USAGE.md updated | ☐      |

**Cycle 6 Update:** Full path to deployed & launched (exporters → CLI/viz/CI → Docker/compose + idempotency → hardening + synthetic + release) defined in plan.md. All INVEST tasks trace to it. Fixture gap (sample_report.txt deleted) will be closed with synthetic generator in Phase 7 per plan. Hybrid execution preserves strict project agentic rules.

---

## Self-Improvement Tasks for the Agentic Loop (Reviewer Focus)

| #   | Task                                              | Acceptance Criteria                                                                 | Status |
|-----|---------------------------------------------------|-------------------------------------------------------------------------------------|--------|
| S1  | Integrate last_agent_completion.json into Reviewer workflow | All DONE decisions create the temp file + archive; Markdown captured correctly     | ☐      |
| S2  | Evaluate MiniMax 2.5 performance on Phase 5 exporter/visualization tasks | Document prompt effectiveness and any needed template tweaks in SELF_IMPROVEMENT_LOG.md | ☐      |
| S3  | Strengthen PII handling in new exporter code      | All new exporters use PiiSafeLogger and redaction utilities; audited by Reviewer   | ☐      |
| S4  | Update this SPRINTPLAN and context after each cycle | Clear progress; new INVEST tasks added as needed; natural Russian updates          | ☐      |

---

## Strategic Initiative: Production-Grade Investigation Interface (Idea #2)

This is a high-priority product-level initiative identified in the 2026-05-30 strategic research (see research plan in session artifacts, Section 9).

**Goal:** Transform the current basic Streamlit prototype into a trustworthy, PII-safe, analyst-grade investigation workbench with advanced filtering, provenance inspection, rich graph exploration, and tight integration with the exporter suite (Idea #1).

**Key Design Principles:** PII-First by Default, Provenance Everywhere, Graph as First Citizen, Progressive Disclosure.

**Dependencies:** Strong coupling with Idea #1 (Exporter Suite) for filtered exports from the UI.

| #    | Task                                                                 | Acceptance Criteria                                                                 | Status | Dependencies          |
|------|----------------------------------------------------------------------|-------------------------------------------------------------------------------------|--------|-----------------------|
| UI-01 | Add global PII Redaction Mode toggle (Full / Masked / Hidden)       | Three modes applied consistently across all entity displays and search; toggle persists in session | ☐      | Redaction utilities   |
| UI-02 | Implement safe-by-default property rendering                         | Passport, SNILS, INN, phones, emails never shown in cleartext unless Full mode explicitly chosen | ☐      | UI-01                 |
| UI-03 | Fix import path handling + add Streamlit file upload support         | Supports both local paths and direct file uploads; no hardcoded Windows paths      | ☐      | —                     |
| UI-04 | Add basic provenance panel                                           | Clicking any entity shows source_refs + sample of original raw data in side panel  | ☐      | —                     |
| UI-05 | Replace hard 50-item caps with proper pagination / "Load more"       | Entity lists support incremental loading without artificial limits                 | ☐      | —                     |
| UI-06 | Advanced entity & relationship filters                               | Filters by entity type, min confidence, source report, date ranges, relationship types; fast and combinable | ☐      | UI-01, UI-05          |
| UI-07 | Linked detail view (entity selection → show direct connections)      | Selecting entity highlights its relationships and shows connected entities in dedicated panel | ☐      | UI-04                 |
| UI-08 | Integration with Exporter Suite (Idea #1)                            | From any filtered view, trigger export (CSV/JSONL/Neo4j) of current filtered + redacted dataset | ☐      | Idea #1 exporters     |

---

## Notes for the Agent

- Prefer small, well-tested increments.
- Every meaningful change that passes checks must be committed with a natural Russian message written as a real developer.
- The Reviewer owns the quality of both code **and** the agentic process itself.
- Update `PROJECT_CONTEXT.md` with any important architectural or process decisions.

**Current Sprint Focus:** Completing production-ready exporters, visualization, and tooling (Phase 5) while maturing both development loops (heavy agentic for complex autonomous runs + lightweight agentless Solver Loop for direct Grok CLI / fast iterations).

**Optimization notes:**
- For long autonomous runs with MiniMax 2.5 / Blackbox: use the tuned `agentic_loop_template/` (role temperatures, Pre-Flight Checklist, JSON handoffs, Agent-Init.ps1). Follow PLAN → ACT → REFLECT per role.
- For direct work in Grok CLI, Cursor, or quick vertical slices: follow `AGENTS.md` + `agentless_loop/` (Solver Loop: max 3 tool calls per cluster, strong emphasis on Inspect + small measurable slices + Russian dev voice).
- All modes: English instructions/planning docs, strict natural Russian commits + code comments (no AI/LLM mentions), `.venv`-only Python, per DEVELOPMENT_STANDARDS.md.