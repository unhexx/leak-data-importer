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
        from pathlib import Path
        from leak_data_importer.importers import IMPORTER_REGISTRY

        if not args.source:
            print("[ERROR] --source is required for import command")
            return 1

        source = Path(args.source)
        fmt = args.format.lower()

        if fmt == "auto":
            if source.suffix.lower() == ".txt" or source.name.startswith("report_"):
                fmt = "txt_report"
            else:
                fmt = "txt_report"  # default for now

        importer_cls = IMPORTER_REGISTRY.get(fmt)
        if not importer_cls:
            print(f"[ERROR] Unknown format: {fmt}. Available: {list(IMPORTER_REGISTRY.keys())}")
            return 1

        print(f"\n[INFO] Using importer: {importer_cls.name}")
        print(f"[INFO] Source: {source}")

        try:
            importer = importer_cls(source)
            records = list(importer.iter_records())
            print(f"[SUCCESS] Parsed {len(records)} records")

            if args.dry_run:
                print("\n--- First 3 records (dry-run) ---")
                for rec in records[:3]:
                    print(f"  {rec.full_name} | phones={rec.phones} | emails={rec.emails}")
            else:
                # TODO: implement actual export (csv/json/parquet)
                print("[INFO] Writing output is not implemented yet. Use --dry-run for now.")
        except Exception as e:
            print(f"[ERROR] {e}")
            return 1
    else:
        print(f"\n[INFO] The '{args.command}' command is planned but not implemented yet.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
