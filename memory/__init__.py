"""
Agentic Loop Memory System

Workspace-scoped, structured, deduplicating memory for the self-improving
agentic development loop.

Inspired by:
- memory.py from the /implement skill
- Generative Agents (memory stream + reflection)
- Reflexion (verbal self-reflection)

Usage from the agent (via powershell tool):

    # Get workspace info
    python -m agentic_loop_template.memory info

    # Record distilled patterns (usually called by Reviewer)
    python -m agentic_loop_template.memory update --patterns '[{"category": "Testing", "description": "Missing edge case for empty input"}]'

    # Get current memory snapshot (JSON)
    python -m agentic_loop_template.memory snapshot

    # Simple query (future)
    python -m agentic_loop_template.memory query --category "Common Failure Patterns"
"""

from .workspace import get_workspace_id, memory_paths
from .store import read_memory, update_memory, snapshot, query_memory
from .schema import MemoryState, Pattern

__all__ = [
    "get_workspace_id",
    "memory_paths",
    "read_memory",
    "update_memory",
    "snapshot",
    "query_memory",
    "MemoryState",
    "Pattern",
]
