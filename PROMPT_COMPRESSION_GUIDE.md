# Prompt Compression Guide for Agentic Loop (v3+)

**Goal**: Maximize context efficiency (minimize tokens) while preserving or improving the quality and reliability of the self-improving development loop.

## Core Principles

1. **Distill, don't repeat**
   - Move all repeating rules, anti-patterns, values, and detailed explanations into `DEVELOPMENT_STANDARDS.md`.
   - The active prompt should only reference it, not restate it.

2. **Micro-prompts for roles**
   - Role blocks in `AGENT_ROLES.md` should be extremely short ("you are now X, follow the Constitution, do these immediate things").
   - Detailed examples and long explanations belong in previous cycles, docs, or appendices — not in the active context on every handoff.

3. **External memory is primary state**
   - `PROJECT_CONTEXT.md`, `SPRINTPLAN.md`, and `SELF_IMPROVEMENT_LOG.md` are the real working memory.
   - The prompt + recent handoffs should be as thin as possible.

4. **Delta communication**
   - Handoffs should communicate *changes* and compact summaries, not full history.
   - Use the `context_delta` field in the handoff schema.

5. **On-demand reading**
   - Tell the agent *where* to find information instead of including everything upfront.
   - "Read the relevant section of X only when needed."

6. **Self-improvement as a compression engine**
   - Use the loop's own output (lessons_learned) to iteratively shorten and sharpen the instructions themselves.

## Practical Techniques Applied

- Converted full role instructions → micro-prompts (major win on every handoff).
- Moved detailed GIT/COMMIT/CODE COMMENT rules out of SYSTEM_PROMPT → DEVELOPMENT_STANDARDS.md.
- Added explicit `context_delta` support in HANDOFF_SCHEMA.md.
- Strengthened guidance to keep `summary` extremely short.
- Added automatic environment reports and safe helper functions so the agent doesn't need long explanatory text in the prompt.

## Measurement & Maintenance

- Track approximate token counts of:
  - Full SYSTEM_PROMPT + current role block
  - Typical handoff + recent context files
- After every significant compression wave, record the before/after numbers in `SELF_IMPROVEMENT_LOG.md`.
- Reviewer should explicitly comment on context efficiency during handoff review.

## Future Opportunities

- Stronger automation of Context Distillation (e.g., token-count triggers in Agent-Init.ps1).
- More aggressive use of external memory / scratchpad files.
- Dynamic prompt loading based on current phase.
- Tool-assisted context pruning.

## Automatic Context Distillation (Implemented)

As of this version, the template includes an explicit **automatic Context Distillation** mechanism:

- Triggered primarily by the Reviewer at the end of full cycles (or on-demand when context feels heavy).
- Produces structured, high-density summaries using a defined format.
- Stored in `SELF_IMPROVEMENT_LOG.md` (and/or `PROJECT_CONTEXT.md`).
- Supported by an optional `distillation_performed` field in the handoff schema.
- Documented in `DEVELOPMENT_STANDARDS.md` (section 8) and the Reviewer role instructions.

This is the main mechanism for keeping very long-running loops (10+ cycles) practical. See `DEVELOPMENT_STANDARDS.md` and `AGENT_ROLES.md` (Reviewer section) for exact instructions.

**This document itself should stay relatively short.** Its purpose is to guide future compression work, not to become another source of bloat.

---

*Maintained as part of the agentic_loop_template optimization effort for MiniMax M2.7.*