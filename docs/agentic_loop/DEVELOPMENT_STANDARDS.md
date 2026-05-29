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

## 6. File Encoding (UTF-8 by Default) — Critical for Stability

**This rule exists to prevent mojibake and broken handoff files on Windows (especially Russian systems).**

All text files (including handoff JSONs, logs, reports, etc.) **must** be written and read using UTF-8.

### Mandatory Rules When Writing Files

1. **Preferred method — Python (most reliable):**
   ```python
   import json
   with open("handoff_orchestrator_to_coder.json", "w", encoding="utf-8") as f:
       json.dump(data, f, ensure_ascii=False, indent=2)
   ```

2. **When using PowerShell:**
   - Always specify encoding explicitly:
     ```powershell
     Set-Content -Path "file.json" -Value $json -Encoding utf8
     "text" | Out-File -FilePath "file.txt" -Encoding utf8
     ```
   - Never rely on bare `>` or `>>` redirection without setting defaults first.

3. **Never** use:
   - Bare `echo "text" > file.json`
   - Python `open("file", "w")` without `encoding="utf-8"`
   - PowerShell redirection without explicit UTF-8

### When Reading Files

- PowerShell: `Get-Content "file.json" -Encoding utf8`
- Python: `open("file.json", encoding="utf-8")`

### Enforcement

- The **Reviewer** must check that all handoff JSON files and important text outputs are valid UTF-8.
- If mojibake appears in handoff files or logs, the Reviewer should treat it as a process violation and request correction.
- Record any encoding-related problems in `SELF_IMPROVEMENT_LOG.md`.

**Recommendation for the Orchestrator:**
At the beginning of every cycle, after running `Agent-Init.ps1`, ensure the current PowerShell session has UTF-8 defaults enabled.

---

**This document is the single source of truth for development standards in this project.**

When in doubt, re-read this file. The Reviewer will hold all roles accountable to these standards.