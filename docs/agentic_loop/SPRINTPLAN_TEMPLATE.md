# SPRINTPLAN.md

> Updated by the **Orchestrator** at the beginning of each cycle and by the **Reviewer** at the end.  
> All tasks must follow the INVEST principle: Independent, Negotiable, Valuable, Estimable, Small, Testable.  
> All planning content is in English.

---

## Sprint Metadata

| Parameter           | Value                                      |
|---------------------|--------------------------------------------|
| **Cycle Number**    | `{{ 0 }}`                                  |
| **Start Date**      | `{{ YYYY-MM-DD }}`                         |
| **Sprint Goal**     | `{{ Implement full parser X with 90%+ coverage }}` |

---

## Phases and Tasks

### Phase 0 — Environment Preparation (Orchestrator)

| #   | Task                              | Acceptance Criteria                                      | Status |
|-----|-----------------------------------|----------------------------------------------------------|--------|
| 0.1 | Run `setup_env.ps1`               | Environment is ready, dependencies installed             | ☐      |
| 0.2 | Check git status and branch       | Clean working tree on a feature branch                   | ☐      |
| 0.3 | Read full specification           | All requirements understood                              | ☐      |
| 0.4 | Update PROJECT_CONTEXT.md         | File is up to date and under token limit                 | ☐      |
| 0.5 | Create / update this SPRINTPLAN   | All phases have INVEST tasks                             | ☐      |
| 0.6 | Configure git identity            | Realistic developer name and email are set               | ☐      |

---

### Phase 1 — Models & Normalizers (Coder)

| #   | Task                              | Acceptance Criteria                                      | Status |
|-----|-----------------------------------|----------------------------------------------------------|--------|
| 1.1 | Implement models                  | All Pydantic v2 models match specification               | ☐      |
| 1.2 | Implement normalizers             | All functions are deterministic and unit-tested          | ☐      |
| 1.3 | Implement DB models               | SQLAlchemy models match database schema                  | ☐      |
| 1.4 | Create Alembic migrations         | `alembic upgrade head` succeeds cleanly                  | ☐      |
| 1.5 | Write test skeletons              | Test files created with clear TODO markers               | ☐      |
| 1.6 | Commit                            | Natural Russian commit message (human developer style)   | ☐      |

---

### Phase 2 — Core Parser & CLI (Coder)

| #   | Task                              | Acceptance Criteria                                      | Status |
|-----|-----------------------------------|----------------------------------------------------------|--------|
| 2.1 | Implement main parser             | Deterministic, handles all sections from specification   | ☐      |
| 2.2 | Implement CLI / entry point       | Works on provided sample input files                   | ☐      |
| 2.3 | Manual smoke test                 | All sample files parse without errors                    | ☐      |
| 2.4 | Commit                            | Natural Russian commit message                           | ☐      |

---

### Phase 3 — Testing (Tester)

| #   | Task                              | Acceptance Criteria                                      | Status |
|-----|-----------------------------------|----------------------------------------------------------|--------|
| 3.1 | Write model tests                 | Full field coverage + validators                         | ☐      |
| 3.2 | Write normalizer tests            | Including edge cases from specification                  | ☐      |
| 3.3 | Write parser tests                | Happy path + all specified edge cases                    | ☐      |
| 3.4 | Write DB integration tests        | Full roundtrip: insert → query → assert                  | ☐      |
| 3.5 | Write E2E integration tests       | Parse file → insert → verify graph/DB state              | ☐      |
| 3.6 | Run full test suite + coverage    | Report generated and metrics recorded in handoff         | ☐      |

---

### Phase 4 — Debugging (Debugger)

| #   | Task                              | Acceptance Criteria                                      | Status |
|-----|-----------------------------------|----------------------------------------------------------|--------|
| 4.1 | Fix all failing tests             | `pytest` returns 0 failures                              | ☐      |
| 4.2 | Achieve ≥ 90% coverage            | `coverage report` shows target                           | ☐      |
| 4.3 | No regressions                    | All previously passing tests still pass                  | ☐      |
| 4.4 | Commit fixes                      | Natural Russian commit message                           | ☐      |

---

### Phase 5 — Review & Finalization (Reviewer)

| #   | Task                                      | Acceptance Criteria                                      | Status |
|-----|-------------------------------------------|----------------------------------------------------------|--------|
| 5.1 | Full specification compliance checklist   | All items from Reviewer role in AGENT_ROLES.md passed    | ☐      |
| 5.2 | Final smoke tests                         | All sample inputs process cleanly                        | ☐      |
| 5.3 | Update documentation                      | README, USAGE.md, and other docs are accurate            | ☐      |
| 5.4 | Update Self-Improvement records           | PROJECT_CONTEXT.md and this file contain cycle summary   | ☐      |
| 5.5 | Enforce code comment rules                | All new comments are in natural Russian, human style     | ☐      |
| 5.6 | Merge to main                             | Clean merge, no conflicts                                | ☐      |

---

## Process Improvements (Maintained by Reviewer)

> History of improvements to the development *process* itself.

### Cycle 0
*(Fill after first cycle completion)*

- **Added:**
- **Changed:**
- **Removed:**

---

## Recurrent Problems

> Issues that appeared more than once and require systemic solutions.

| Problem | Cycles | Resolution |
|---------|--------|------------|
| *(empty)* | | |

---

## Sprint Done Criteria

A sprint is considered **DONE** only when **ALL** of the following are true:

- [ ] `pytest` exits with 0 failures
- [ ] Coverage meets or exceeds target (usually ≥ 90%)
- [ ] All acceptance criteria for Phases 0–5 are satisfied
- [ ] All git commit messages are natural Russian, written as a real developer
- [ ] No English comments or AI-style language remain in the codebase
- [ ] Reviewer confirms 100% compliance with the specification
- [ ] `PROJECT_CONTEXT.md` and `SPRINTPLAN.md` are up to date

---

**Reminder to all roles:** The Reviewer is the final gatekeeper not only for code quality, but also for adherence to the agentic process rules, including language and style of comments and commits.