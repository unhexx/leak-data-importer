# Phase 5 Implementation Plan: Production Readiness - Complete Exporters, Visualization, CLI, CI/CD and Documentation

## Overview

Phase 5 focuses on turning the solid foundation from previous phases into a truly production-ready tool. Key gaps remaining after Phase 4: incomplete Neo4j exporter, missing additional exporters, basic Streamlit and CLI, no CI/CD, and medium documentation.

All work will be executed through the agentic loop (Orchestrator → Coder → Tester → Debugger → Reviewer) using the tuned `agentic_loop_template/` optimized for Blackbox + MiniMax 2.5.

**Optimization for MiniMax 2.5:**
- Tasks broken into small (1-3 agent-day equivalent), INVEST-sized items with crystal-clear acceptance criteria.
- Orchestrator and Reviewer use temperature 0.0 for deterministic, high-quality planning and review.
- Coder and Debugger use temperature 0.2.
- Strict adherence to PLAN → ACT → REFLECT, Pre-Flight Checklist, and DEVELOPMENT_STANDARDS.md (especially UTF-8 file writing and natural Russian human-style commits/comments).
- Start every major cycle or complex step with `.\agentic_loop_template\Agent-Init.ps1`.

---

## Information Gathered

### Current State (post Phase 4)
- **Exporters**: Only basic/partial Neo4j exporter exists. No CSV, JSON Lines, or Parquet support.
- **Visualization**: Streamlit app is basic (limited filters, simple visualizations).
- **CLI**: Minimal (only basic import functionality).
- **CI/CD**: None.
- **Documentation**: Medium (good README and agentic docs, but lacks detailed API docs, security guidelines, and rich real-world examples).
- **Other**: Strong importers, parsers, normalization (including Phase 4 improvements), PersonLinker + dedup, SQLAlchemy 2.0 + repositories, solid test coverage (77+ tests), PII redaction utilities and PiiSafeLogger.

### What's Missing / Phase 5 Focus
1. Full Neo4j exporter (batch support, indexes, constraints, complete entity coverage).
2. Additional exporters (CSV, JSON Lines, Parquet — starting with core entities).
3. Major Streamlit enhancements (UX, advanced graph viz, filters, export integration).
4. CLI expansion (export, analyze, link commands with proper help and docs).
5. Basic but reliable GitHub Actions CI.
6. Documentation improvements (API docs, user guide expansion, security guidelines).

---

## Implementation Plan

### Step 1: Complete and Harden the Neo4j Exporter

**Files to modify/create:**
- `src/leak_data_importer/exporters/neo4j_exporter.py`
- Possibly new tests in `tests/test_neo4j_exporter.py`
- Updates to `migrations/` or schema if constraints require it (unlikely)

**Changes:**
1. Add full batch export support for all current entities (Person, PersonLink, etc.).
2. Implement proper index creation and constraints (e.g., uniqueness on key fields).
3. Add configuration for connection pooling and batch sizes.
4. Ensure PiiSafeLogger and redaction are used in any logging/export paths.
5. Write comprehensive tests (happy path + error cases).

**Acceptance Criteria (for the agentic loop):**
- All current entities export correctly in batches.
- Indexes and constraints are created automatically on first export.
- No PII leaks in logs or exported data.
- Performance acceptable on realistic dataset sizes (measured in tests).

### Step 2: Implement Core Additional Exporters (CSV + JSON Lines)

**Files to create/modify:**
- `src/leak_data_importer/exporters/csv_exporter.py`
- `src/leak_data_importer/exporters/jsonlines_exporter.py`
- Base exporter class improvements if needed (`src/leak_data_importer/exporters/base.py`)
- CLI integration in `src/leak_data_importer/cli.py`
- Tests

**Changes:**
1. Create clean, reusable exporter base if not sufficient.
2. Implement CSV and JSON Lines exporters for main entities (Person + links first).
3. Support common options (output path, filtering by entity type, PII redaction options).
4. Add CLI commands: `export csv ...` and `export jsonlines ...`.
5. Full test coverage.

**Acceptance Criteria:**
- Exporters produce valid, usable output files.
- Integrate cleanly with existing importers and graph layer.
- CLI commands work with good help text.
- No PII leakage.

### Step 3: Significantly Enhance the Streamlit Application

**Files to modify:**
- `app/streamlit_app.py`
- Possibly new components or utils in `src/leak_data_importer/`

**Changes:**
1. Major UX improvements (better navigation, search/filters for persons/links).
2. Advanced graph visualization (integrate pyvis or similar for interactive graphs).
3. Add export buttons (directly to the new exporters).
4. PII-safe display by default (with toggle for redacted views).
5. Performance improvements for larger datasets.
6. Better error handling and loading states.

**Acceptance Criteria:**
- App is noticeably more usable and professional.
- Supports filtering and visualization of linked entities.
- Export integration works end-to-end.
- Handles real leak report data without crashing or leaking PII.

### Step 4: Enhance the CLI

**Files to modify:**
- `src/leak_data_importer/cli.py`
- Possibly new exporter modules from Step 2

**Changes:**
1. Add `export` command group (csv, jsonlines, neo4j, parquet — once implemented).
2. Add `analyze` or `link` commands leveraging PersonLinker and repositories.
3. Improve help text, examples, and error messages across all commands.
4. Add `--output-format` and PII handling flags where appropriate.

**Acceptance Criteria:**
- New commands are discoverable and well-documented via `--help`.
- Common workflows (import → link → export) can be done via CLI.
- Consistent with existing command style.

### Step 5: Add Basic GitHub Actions CI

**Files to create:**
- `.github/workflows/ci.yml`

**Changes:**
1. Set up jobs for:
   - Ruff lint + format check
   - pytest (with coverage)
   - MyPy type checking
2. Run on push to main and on pull requests.
3. Use matrix for Python versions if beneficial (start with 3.11+).

**Acceptance Criteria:**
- CI passes on the current codebase.
- Fails clearly on lint/type/test issues.
- Easy to extend for future phases (e.g., integration with real Neo4j in CI later).

### Step 6: Documentation Improvements

**Files to modify/create:**
- `README.md` (expand Features, add real usage examples, security section)
- New or expanded `docs/` files (e.g., `docs/API.md`, `docs/SECURITY.md`, `docs/USAGE.md` if not present)
- Update agentic docs if needed for the new phase

**Changes:**
1. Flesh out the Features/Roadmap section with current status.
2. Add concrete examples for common workflows (including new exporters/CLI).
3. Add security guidelines (PII handling, legal use, redaction).
4. Document the agentic development process more clearly for contributors.

**Acceptance Criteria:**
- A new user can install and run meaningful workflows using only the docs.
- Security and legal responsibilities are clearly stated.
- The agentic loop template remains well-documented.

---

## Verification & Testing Strategy (for the Agentic Loop)

- Every sub-task must have passing tests (unit + integration where applicable).
- Full `scripts/test.ps1` + `scripts/lint.ps1` must pass at the end of each Coder/Debugger handoff.
- Reviewer must verify:
  - All acceptance criteria for the step.
  - No PII leaks in new code or outputs.
  - Natural Russian human-style commits and comments (per DEVELOPMENT_STANDARDS.md).
  - Proper UTF-8 handling for all new exporters and files.
  - The new artifacts (exporters, CLI commands, CI) integrate cleanly with the existing importer/graph/dedup layers.

**Success for Phase 5 overall:**
- A user can go from raw leak report → normalized + linked data → Neo4j + CSV/JSON Lines export → visualized in improved Streamlit, all via CLI or library, with CI guarding quality.
- Documentation allows a new user to do the above without reading source code.

---

**Next Cycle (Cycle 6) Orchestrator starting point:**
Read this plan + updated `SPRINTPLAN.md`, `TODO.md`, and `PROJECT_CONTEXT.md`.
Start with environment bootstrap via `Agent-Init.ps1`.
Follow the 5-role cycle with temperatures and standards from `agentic_loop_template/`.
Write all commits in natural Russian as a real mid/senior developer who has been working on this project for months.

This plan is designed to be executed cleanly through the existing agentic loop.