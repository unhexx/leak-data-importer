"""
Structured schema and (de)serialization for the agentic loop memory file.

Designed to be both human-readable (markdown) and easily machine-processable.
"""

from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any

# Re-export constants so schema is self-describing (store imports/uses them for compaction)
# Single source of truth for the memory file limits.
MAX_PATTERNS_PER_CATEGORY = 30
MAX_RECENT_DISTILLATIONS = 20

# --- Parsing regexes ---

_SECTION_HEADER = re.compile(r"^#\s+Agentic Loop Memory")
_CATEGORY_RE = re.compile(r"^##\s+(.+?)\s*$")
_PATTERN_RE = re.compile(r"^-\s+(.+?)\s+\(seen\s+(\d+)\s+times?\)\s*$")
_RUN_RE = re.compile(r"^###\s+(\d{4}-\d{2}-\d{2})\s*[\u2014\u2013-]\s*(.+?)\s*$")


@dataclass
class Pattern:
    description: str
    count: int = 1


@dataclass
class MemoryState:
    """In-memory representation of the agentic memory file."""
    header: list[str] = field(default_factory=list)
    patterns: OrderedDict[str, list[Pattern]] = field(default_factory=OrderedDict)  # category -> patterns
    recent_distillations: list[dict[str, Any]] = field(default_factory=list)  # list of {date, summary, ...}


def parse_memory_file(content: str) -> MemoryState:
    """Parse the memory markdown into a structured MemoryState."""
    state = MemoryState()

    if not content or not content.strip():
        return state

    lines = content.splitlines()
    section = "header"
    current_category: str | None = None
    current_distillation: dict[str, Any] | None = None

    for line in lines:
        if _SECTION_HEADER.match(line):
            continue

        cat_match = _CATEGORY_RE.match(line)
        if cat_match:
            if current_distillation is not None:
                state.recent_distillations.append(current_distillation)
                current_distillation = None

            section = "patterns"
            current_category = cat_match.group(1).strip()
            state.patterns.setdefault(current_category, [])
            continue

        if section == "header":
            state.header.append(line)
            continue

        if section == "patterns" and current_category:
            pat_match = _PATTERN_RE.match(line)
            if pat_match:
                desc = pat_match.group(1).strip()
                count = int(pat_match.group(2))
                state.patterns[current_category].append(Pattern(description=desc, count=count))
            continue

        # For simplicity in v1 we treat everything after patterns as recent distillations
        # A more sophisticated version can parse ### Date — Summary blocks

    if current_distillation is not None:
        state.recent_distillations.append(current_distillation)

    # Trim trailing blank lines from header
    while state.header and not state.header[-1].strip():
        state.header.pop()

    return state


def render_memory_file(state: MemoryState) -> str:
    """Render MemoryState back to clean markdown."""
    out: list[str] = []

    if state.header:
        out.extend(state.header)
        out.append("")

    out.append("# Agentic Loop Memory")
    out.append("")

    if not state.patterns:
        out.append("## No patterns recorded yet.")
        out.append("")
    else:
        for category, patterns in state.patterns.items():
            if not patterns:
                continue
            out.append(f"## {category}")
            for p in patterns:
                times = "time" if p.count == 1 else "times"
                out.append(f"- {p.description} (seen {p.count} {times})")
            out.append("")

    if state.recent_distillations:
        out.append("## Recent Distillations")
        out.append("")
        for d in state.recent_distillations[-5:]:  # keep last 5 for readability
            out.append(f"### {d.get('date', 'unknown')} — {d.get('summary', '')}")
            if d.get("details"):
                out.append(d["details"])
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def normalize(text: str) -> str:
    """Normalize a pattern description for deduplication."""
    text = text.lower().strip()
    text = re.sub(r"[.;:,!?\s]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text
