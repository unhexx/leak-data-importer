"""
Command-line interface for the agentic loop memory system.

Usage examples (from project root, after venv activation):

    python -m agentic_loop_template.memory info
    python -m agentic_loop_template.memory path
    python -m agentic_loop_template.memory snapshot
    python -m agentic_loop_template.memory query --category "Common Failure Patterns" --top 5
    python -m agentic_loop_template.memory update --json '{"patterns": [{"category": "Testing", "description": "..."}]}'
"""

from __future__ import annotations

import argparse
import json
import sys

from .workspace import get_workspace_id, memory_paths
from .store import read_memory, update_memory, snapshot, query_memory


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic Loop Memory System")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # info
    subparsers.add_parser("info", help="Show workspace ID and memory file location")

    # path
    subparsers.add_parser("path", help="Print the path to the memory file")

    # snapshot
    subparsers.add_parser("snapshot", help="Print current memory as JSON")

    # update
    update_p = subparsers.add_parser("update", help="Merge patterns and/or a distillation record")
    update_p.add_argument("--json", required=True, help="JSON payload with 'patterns' and/or 'distillation'")

    # query (simple agent-facing retrieval)
    query_p = subparsers.add_parser("query", help="Return top-N patterns (highest count first), optionally filtered")
    query_p.add_argument("--category", help="Exact category to filter (e.g. 'Common Failure Patterns')")
    query_p.add_argument("--top", type=int, default=5, help="Maximum number of results (default 5)")
    query_p.add_argument("--contains", help="Substring filter (case-insensitive) on description")

    args = parser.parse_args()

    if args.command == "info":
        wid = get_workspace_id()
        paths = memory_paths()
        print(f"Workspace ID : {wid}")
        print(f"Memory file  : {paths['file']}")
        print(f"Lock file    : {paths['lock']}")

    elif args.command == "path":
        print(memory_paths()["file"])

    elif args.command == "snapshot":
        data = snapshot()
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif args.command == "update":
        try:
            payload = json.loads(args.json)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
            sys.exit(4)

        result = update_memory(
            new_patterns=payload.get("patterns"),
            distillation=payload.get("distillation"),
        )
        print(json.dumps(result, indent=2))

    elif args.command == "query":
        res = query_memory(
            category=args.category,
            top_n=args.top,
            contains=args.contains,
        )
        print(json.dumps(res, indent=2, ensure_ascii=False))

    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
