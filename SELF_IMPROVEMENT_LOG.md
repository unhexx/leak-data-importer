# SELF_IMPROVEMENT_LOG.md

> Dedicated log for the **agentic loop's own performance** and evolution.  
> Maintained primarily by the **Reviewer** at the end of each full external cycle.  
> Focus: How well the 5-role system (Orchestrator → Coder → Tester → Debugger → Reviewer) is working, not just the application code.  
> All content in English.

---

## Purpose

This file captures observations about the agentic development process itself so that the loop can become more effective over time. It is separate from project-specific context in `PROJECT_CONTEXT.md`.

---

## Critical Rules (Always Enforced)

**Code and Documentation Comments Rule:**

When the agent (in any role) produces or modifies source code:

- All comments, docstrings, and documentation inside Python files **must be written in natural Russian**.
- The language and style must match that of a real human mid/senior developer who has been working on this codebase for months.
- **Strictly forbidden**: Any mention of AI, LLM, agent, MiniMax, Grok, Claude, "neural network", "as an assistant", or any phrasing that reveals the work was performed or assisted by an AI system.
- This rule also applies to git commit messages.

The Reviewer is responsible for detecting and correcting violations of this rule before marking a cycle as complete.

---

## Cycle Performance Reviews

### Cycle 0 — Initial Seeding (2026-05-28)

**What worked well:**
- Strong existing `agentic_loop_template/` (v2.1) with clear role definitions and temperatures.
- Good separation between project work and agent tooling (PowerShell scripts, venv management).
- The Pre-Flight Checklist concept in `SYSTEM_PROMPT.md` is valuable.

**What needs improvement:**
- Initial context seeding was weak. The agent had to spend significant effort reconstructing project state.
- Lack of pre-existing `PROJECT_CONTEXT.md` and `SPRINTPLAN.md` in English made the first cycle slower.
- The rule about Russian code comments was not explicitly embedded in working state files before.

**Recommended adjustments for the loop:**
- Always seed `PROJECT_CONTEXT.md` and `SPRINTPLAN.md` with high-quality English content when starting work on a new project or after a long pause.
- Make the "Russian comments as human developer" rule extremely prominent in the files the agent reads most often (`PROJECT_CONTEXT.md`, `SPRINTPLAN.md`, and role instructions).
- Consider adding a lightweight checklist item in the Reviewer role specifically for comment language and style.

**Impact on future cycles:**
- Created baseline versions of `PROJECT_CONTEXT.md`, `SPRINTPLAN.md`, and this log file with explicit instructions.

---

## Observed Patterns (to be updated by Reviewer)

| Area                        | Observation                                      | Suggested Improvement                          | Status   |
|-----------------------------|--------------------------------------------------|------------------------------------------------|----------|
| Role handoff quality        | (to be filled after real cycles)                 |                                                | Pending  |
| Prompt adherence            |                                                  |                                                | Pending  |
| Russian comment enforcement |                                                  |                                                | Pending  |
| Context file maintenance    |                                                  |                                                | Pending  |
| Test quality in agent cycles|                                                  |                                                | Pending  |
| Self-awareness of the loop  |                                                  |                                                | Pending  |

---

## Long-term Goals for the Agentic Loop

- The loop should become better at estimating task complexity and breaking work into INVEST-sized chunks.
- The Reviewer should become stricter and more consistent at catching violations of the Russian commenting rule.
- Over time, the agent should maintain richer "institutional memory" about what approaches worked well for this specific domain (Russian leak data normalization and graph modeling).
- Reduce the number of cycles needed to deliver production-quality increments.

---

**Note to future Reviewers:**

Be honest and specific. Vague praise ("everything went well") is not useful. Focus on concrete behaviors, prompt effectiveness, and process friction. The goal is continuous improvement of the development *process*, not just the product.