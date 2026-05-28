"""Command-line interface for leak-data-importer."""

import argparse
import sys
from importlib.metadata import version, PackageNotFoundError


def get_version() -> str:
    try:
        return version("leak-data-importer")
    except PackageNotFoundError:
        return "0.1.0 (development)"


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="leak-data-importer",
        description="Securely import, normalize, and process leaked or sensitive data sets.",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {get_version()}"
    )
    parser.add_argument(
        "command",
        choices=["import", "process", "export"],
        nargs="?",
        default="import",
        help="Operation to perform (default: import)",
    )
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        default=None,
        help="Path to source data file or directory",
    )
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        default="auto",
        help="Input format (csv, json, sql, auto)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="./data/processed/",
        help="Output directory or file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview without writing output",
    )

    args = parser.parse_args()

    print(f"leak-data-importer v{get_version()}")
    print(f"Command: {args.command}")
    print(f"Source : {args.source or '(not specified)'}")
    print(f"Format : {args.format}")
    print(f"Output : {args.output}")
    if args.dry_run:
        print("Mode   : DRY-RUN (no files will be written)")

    if args.command == "import":
        print("\n[INFO] Import functionality is not yet implemented.")
        print("       This is a skeleton CLI. Add your importer logic in cli.py or a dedicated module.")
    else:
        print(f"\n[INFO] The '{args.command}' command is planned but not implemented yet.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
