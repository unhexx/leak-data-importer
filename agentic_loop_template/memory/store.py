"""
Core read/update logic for the agentic loop memory with concurrency safety.

Cross-platform (Windows + POSIX). Locking prefers filelock (if installed),
otherwise falls back to a pure-stdlib polling exclusive-file lock that works
everywhere. This is the critical adaptation from the POSIX-only reference
memory.py in the /implement skill.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .schema import (
    MemoryState,
    parse_memory_file,
    render_memory_file,
    normalize,
    Pattern,
    MAX_PATTERNS_PER_CATEGORY,
    MAX_RECENT_DISTILLATIONS,
)
from .workspace import memory_paths

# --- Constants (imported from schema for single source of truth; lock tuning stays here) ---
LOCK_TIMEOUT_SECONDS = 30.0
LOCK_POLL_INTERVAL = 0.2

# Try to use the excellent pure-Python filelock package when available.
# This gives robust, cross-platform locking with minimal code.
try:
    from filelock import FileLock, Timeout as FileLockTimeout  # type: ignore

    _HAS_FILELOCK = True
except ImportError:
    _HAS_FILELOCK = False
    FileLock = None  # type: ignore
    FileLockTimeout = Exception  # type: ignore


@contextmanager
def _locked(lock_path: Path, timeout: float = LOCK_TIMEOUT_SECONDS):
    """
    Cross-platform exclusive lock context manager.

    - If filelock is installed: uses FileLock (recommended for production).
    - Otherwise: simple stdlib polling lock using O_EXCL create + unlink.
      Sufficient for the single-user agentic loop use case on Windows.

    The lock file itself is never used for data — only for coordination.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    if _HAS_FILELOCK and FileLock is not None:
        # Preferred path: robust, well-tested, works on Windows + POSIX
        lock = FileLock(str(lock_path))
        try:
            lock.acquire(timeout=timeout)
            yield
        except FileLockTimeout as e:
            raise RuntimeError(
                f"Could not acquire memory lock on {lock_path} within {timeout}s "
                "(another process holds it or high contention). "
                "Consider installing 'filelock' for better diagnostics if not already present."
            ) from e
        finally:
            try:
                lock.release()
            except Exception:
                pass
        return

    # Fallback: pure stdlib polling exclusive-file lock (works on Windows without extra packages)
    lock_path.touch(exist_ok=True)
    deadline = time.monotonic() + timeout
    fd = None
    acquired = False

    try:
        while time.monotonic() < deadline:
            try:
                # O_EXCL + O_CREAT gives atomic exclusive create on both Win and POSIX
                # (when the file does not already exist or we can replace it safely).
                # We open for writing but do not actually write data to the lock file.
                fd = os.open(
                    str(lock_path),
                    os.O_CREAT | os.O_EXCL | os.O_RDWR,
                )
                acquired = True
                break
            except FileExistsError:
                time.sleep(LOCK_POLL_INTERVAL)
            except OSError as e:
                # Permission or other transient — retry until timeout
                if time.monotonic() >= deadline:
                    raise
                time.sleep(LOCK_POLL_INTERVAL)

        if not acquired or fd is None:
            raise RuntimeError(
                f"Could not acquire memory lock on {lock_path} within {timeout}s "
                "(fallback stdlib lock). Install 'filelock' for more reliable locking on Windows."
            )

        yield

    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if acquired:
            try:
                lock_path.unlink(missing_ok=True)
            except OSError:
                pass


def _compact_state(state: MemoryState) -> dict[str, int]:
    """
    Enforce size limits and return stats about what was dropped.
    Called inside the lock after all merges.
    """
    stats: dict[str, int] = {"categories_capped": 0, "patterns_dropped": 0}

    for category, patterns in list(state.patterns.items()):
        if len(patterns) > MAX_PATTERNS_PER_CATEGORY:
            # Sort by count desc, then description for determinism; keep the strongest signals
            patterns.sort(key=lambda p: (-p.count, p.description.lower()))
            dropped = len(patterns) - MAX_PATTERNS_PER_CATEGORY
            del patterns[MAX_PATTERNS_PER_CATEGORY:]
            stats["categories_capped"] += 1
            stats["patterns_dropped"] += dropped

    if len(state.recent_distillations) > MAX_RECENT_DISTILLATIONS:
        before = len(state.recent_distillations)
        state.recent_distillations = state.recent_distillations[-MAX_RECENT_DISTILLATIONS:]
        stats["distillations_dropped"] = before - len(state.recent_distillations)
    else:
        stats["distillations_dropped"] = 0

    return stats


def read_memory() -> MemoryState:
    """Read and parse the memory file for the current workspace."""
    paths = memory_paths()
    if not paths["file"].exists():
        return MemoryState()

    content = paths["file"].read_text(encoding="utf-8")
    return parse_memory_file(content)


def update_memory(
    *,
    new_patterns: list[dict[str, Any]] | None = None,
    distillation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Merge new patterns and/or a distillation record into the memory file.

    This is the main entry point for the Reviewer (and potentially Orchestrator for retrieval prep).
    """
    paths = memory_paths(create_dir=True)

    with _locked(paths["lock"]):
        state = read_memory()

        # Merge patterns with deduplication
        if new_patterns:
            for p in new_patterns:
                category = p.get("category", "Uncategorized")
                desc = p.get("description", "").strip()
                if not desc:
                    continue

                norm = normalize(desc)
                existing = state.patterns.setdefault(category, [])

                found = False
                for existing_p in existing:
                    if normalize(existing_p.description) == norm:
                        existing_p.count += 1
                        found = True
                        break

                if not found:
                    existing.append(Pattern(description=desc, count=1))

        # Append distillation record
        if distillation:
            state.recent_distillations.append(distillation)

        # Automatic compaction (dedup already happened above)
        compact_stats = _compact_state(state)

        # Render and atomically write (same safe pattern as reference memory.py)
        rendered = render_memory_file(state)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=paths["file"].parent,
            delete=False,
            suffix=".tmp",
        ) as tmp:
            tmp.write(rendered)
            tmp_path = Path(tmp.name)

        tmp_path.replace(paths["file"])
        try:
            paths["file"].chmod(0o600)
        except PermissionError:
            pass

    total_patterns = sum(len(v) for v in state.patterns.values())
    return {
        "patterns_count": total_patterns,
        "recent_distillations": len(state.recent_distillations),
        "compaction": compact_stats,
        "workspace_id": memory_paths()["file"].stem,  # for agent visibility
    }


def snapshot() -> dict[str, Any]:
    """Return a JSON-serializable snapshot of the memory (for the agent to consume easily)."""
    state = read_memory()
    return {
        "patterns": {
            cat: [{"description": p.description, "count": p.count} for p in pats]
            for cat, pats in state.patterns.items()
        },
        "recent_distillations": state.recent_distillations,
    }


def query_memory(
    *,
    category: str | None = None,
    top_n: int = 5,
    contains: str | None = None,
) -> list[dict[str, Any]]:
    """
    Simple, fast query for the agent (Orchestrator at cycle start).

    Returns up to top_n patterns (highest count first), optionally filtered
    by exact category and/or substring in description (case-insensitive).

    This is the primary 'what should I watch for?' interface.
    """
    state = read_memory()
    results: list[dict[str, Any]] = []

    cats_to_scan = [category] if category else list(state.patterns.keys())

    for cat in cats_to_scan:
        if cat not in state.patterns:
            continue
        for p in state.patterns[cat]:
            if contains and contains.lower() not in p.description.lower():
                continue
            results.append(
                {
                    "category": cat,
                    "description": p.description,
                    "count": p.count,
                }
            )

    # Highest count first, stable tie-break on description
    results.sort(key=lambda r: (-r["count"], r["description"].lower()))
    return results[:top_n]
