# DEVELOPMENT STANDARDS

This document defines the non-negotiable standards for all work performed in this project, especially when using the agentic development loop.

All roles (Orchestrator, Coder, Tester, Debugger, Reviewer) must follow these rules without exception.

---

## 1. Language of Code, Comments, and Commits (Strict Rule)

**This is the most important rule in the entire agentic loop.**

When writing or modifying any source code:

- **All comments, docstrings, module-level documentation, and inline explanations must be written in natural Russian.**
- The style must be that of a real mid/senior human developer who has been actively working on this project for several months.
- Use professional, natural Russian that a real developer would actually write.
- **Absolutely forbidden**:
  - Writing comments in English
  - Using AI-typical phrasing ("As an AI language model...", "Here is the implementation...", "This function does the following...")
  - Any mention of AI, LLM, agent, MiniMax, Grok, Claude, neural network, "assisted by", or similar

**The same rule applies to git commit messages:**
- Every commit message must be written in natural Russian.
- It must sound like it was written by a real developer who understands the codebase.
- Never mention the agentic loop, AI, or any model in commit messages.

**Enforcement:**
- The **Reviewer** is responsible for catching violations.
- If non-compliant comments or commit messages are found, the Reviewer must reject the handoff and send the work back for correction.
- Repeated violations must be recorded in `SELF_IMPROVEMENT_LOG.md`.

---

## 2. Code Quality Standards

- All code must be production-grade: proper typing, error handling, logging, and meaningful tests.
- No stubs or TODO comments that block the next role.
- Prefer small, well-tested, incremental changes.
- Every meaningful change must be committed before handing off to the next role.

---

## 3. Self-Improvement Discipline

- The agentic loop exists to improve both the product **and** the development process itself.
- After every full cycle, the Reviewer must update:
  - `PROJECT_CONTEXT.md` (project state + decisions)
  - `SPRINTPLAN.md` (progress and next tasks)
  - `SELF_IMPROVEMENT_LOG.md` (what the loop learned about itself)
- Lessons about prompt effectiveness, role performance, and common failure patterns must be recorded.

---

## 4. Environment and Tooling Rules

- All Python work must happen inside the local `.venv`.
- Use the provided scripts (`scripts/setup.ps1`, `agentic_loop_template/setup_env.ps1`, etc.).
- Never run Python commands using the system `python` when a virtual environment is available.

---

## 5. Handoff and Process Discipline

- Always follow the exact JSON handoff schema defined in `HANDOFF_SCHEMA.md`.
- Never skip the PLAN → ACT → REFLECT pattern inside a role.
- The Reviewer has final authority on both code quality and process adherence.

---

**This document is the single source of truth for development standards in this project.**

When in doubt, re-read this file. The Reviewer will hold all roles accountable to these standards.