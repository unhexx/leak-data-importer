# SPRINTPLAN.md

> This file is updated by the **Orchestrator** at the start of each cycle and by the **Reviewer** at the end of each cycle.  
> All tasks must follow the INVEST principle: Independent, Negotiable, Valuable, Estimable, Small, Testable.  
> Language: English (instructions and planning). Code comments remain in Russian per project rules.

---

## Sprint Metadata

| Parameter           | Value                                      |
|---------------------|--------------------------------------------|
| **Cycle Number**    | 0 (initial)                                |
| **Sprint Goal**     | Establish solid foundation for graph-based analysis of leak data with reliable import pipeline |
| **Start Date**      | 2026-05-28                                 |
| **Target Completion** | End of Cycle 2–3                        |

---

## Current Priorities (from TODO.md)

1. Graph + Neo4j layer — bring to usable state (highest value feature)
2. Database layer — SQLAlchemy 2.0 + proper migrations
3. Deduplication and entity linking — core analytical capability
4. High-quality tests on real examples
5. Normalization improvements (especially documents and addresses)
6. Maturation of the agentic development loop itself

---

## Phase 0 — Environment & Context (Orchestrator)

| #   | Task                                      | Acceptance Criteria                                      | Status |
|-----|-------------------------------------------|----------------------------------------------------------|--------|
| 0.1 | Run environment bootstrap                 | `.venv` is healthy, all dependencies installed           | ☐      |
| 0.2 | Read full current context                 | `TODO.md`, `PROJECT_CONTEXT.md`, and this file reviewed  | ☐      |
| 0.3 | Validate agentic loop readiness           | All key files from `agentic_loop_template/` are present and understood | ☐      |
| 0.4 | Create initial SPRINTPLAN and PROJECT_CONTEXT | Both files exist with meaningful English content         | ☐      |
| 0.5 | Set up git identity (if needed)           | `git config user.name` and `user.email` are realistic    | ☐      |

---

## Phase 1 — Graph Modeling & Neo4j Foundation (High Priority)

| #   | Task                                              | Acceptance Criteria                                                                 | Status |
|-----|---------------------------------------------------|-------------------------------------------------------------------------------------|--------|
| 1.1 | Extend graph entity model                         | Support for new entity types (events, locations, documents) with proper relationships | ✅ Done |
| 1.2 | Improve Neo4j exporter                            | Supports batch inserts, basic constraints, and indexing strategy                    | ✅ Done |
| 1.3 | Add temporal relationships                        | `registered_at` and event dates are properly modeled and exported                   | ✅ Done |
| 1.4 | Write integration tests for graph export          | Real sample reports can be imported and exported to a test Neo4j instance           | ☐      |
| 1.5 | Commit graph layer improvements                   | Natural Russian commit message, human developer style                               | ☐      |

---

## Phase 2 — Database Layer Modernization

| #   | Task                                              | Acceptance Criteria                                                                 | Status |
|-----|---------------------------------------------------|-------------------------------------------------------------------------------------|--------|
| 2.1 | Introduce SQLAlchemy 2.0 models                   | Core tables (persons, documents, events, links) are properly mapped                 | ☐      |
| 2.2 | Set up Alembic migrations                         | `alembic upgrade head` works cleanly from a fresh database                          | ☐      |
| 2.3 | Refactor existing DB code                         | `dossier_db_importer.py` and related modules use the new ORM layer                  | ☐      |
| 2.4 | Add basic CRUD operations with proper typing      | Repository pattern or service layer for main entities                               | ☐      |

---

## Phase 3 — Entity Resolution & Deduplication (Core Value)

| #   | Task                                              | Acceptance Criteria                                                                 | Status |
|-----|---------------------------------------------------|-------------------------------------------------------------------------------------|--------|
| 3.1 | Design and implement person linker                | Multiple fuzzy matching strategies (name + birthdate, phone, document number)       | ☐      |
| 3.2 | Cross-report deduplication                        | Ability to detect the same person across different reports with confidence scores   | ☐      |
| 3.3 | Persist linking decisions                         | Links are stored in DB and reflected in the graph                                   | ☐      |
| 3.4 | Add evaluation harness for linking quality        | Simple metrics or manual review tooling for linking accuracy                        | ☐      |

---

## Phase 4 — Testing, Quality & PII Safety

| #   | Task                                              | Acceptance Criteria                                                                 | Status |
|-----|---------------------------------------------------|-------------------------------------------------------------------------------------|--------|
| 4.1 | Significantly increase test coverage              | All critical importers and normalizers have meaningful tests on real-like data      | ☐      |
| 4.2 | Add PII handling strategy (hashing/tokenization)  | Sensitive fields are never stored in plain text in DB or graph (at minimum design + skeleton) | ☐      |
| 4.3 | Improve normalization for documents and addresses | Edge cases from real reports are handled correctly                                  | ☐      |
| 4.4 | Run full lint + type check + test suite           | `scripts/lint.ps1` and `scripts/test.ps1` pass cleanly                              | ☐      |

---

## Self-Improvement Tasks for the Agentic Loop (Reviewer Focus)

| #   | Task                                              | Acceptance Criteria                                                                 | Status |
|-----|---------------------------------------------------|-------------------------------------------------------------------------------------|--------|
| S1  | Evaluate current role prompts and temperatures    | Document what worked well and what needs tuning in `PROJECT_CONTEXT.md`             | ☐      |
| S2  | Improve handoff quality between roles             | Reduce malformed JSON handoffs; update `HANDOFF_SCHEMA.md` if needed                | ☐      |
| S3  | Strengthen enforcement of Russian code comments   | Reviewer catches and corrects any English comments or AI-style language             | ☐      |
| S4  | Update this SPRINTPLAN after each cycle           | Clear progress tracking and reprioritization based on real outcomes                 | ☐      |

---

## Notes for the Agent

- Prefer small, well-tested increments.
- Every meaningful change that passes checks must be committed with a natural Russian message written as a real developer.
- The Reviewer owns the quality of both code **and** the agentic process itself.
- Update `PROJECT_CONTEXT.md` with any important architectural or process decisions.

**Current Sprint Focus:** Laying strong foundations for the graph analysis capability while maturing the agentic development loop.