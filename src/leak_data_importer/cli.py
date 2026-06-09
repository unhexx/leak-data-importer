"""Command-line interface for leak-data-importer.

Поддерживает команды:
  import     — импорт и нормализация данных
  export     — экспорт результатов в CSV, JSON Lines и другие форматы

Примеры:
  leak-data-importer import --source data/raw/report_*.txt --stats
  leak-data-importer export csv --input data/processed/result.json --output ./export/
  leak-data-importer export jsonlines --input data/processed/result.json --output ./export/
"""

import argparse
import json
import sys
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from typing import Any


def get_version() -> str:
    try:
        return version("leak-data-importer")
    except PackageNotFoundError:
        return "0.1.0 (development)"


def load_graph_result(path: str | Path) -> Any:
    """Загружает сохранённый ImportGraphResult (пока упрощённо из JSON)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Файл с результатом не найден: {p}")

    with p.open(encoding="utf-8") as f:
        data = json.load(f)

    # В будущем здесь будет нормальная десериализация ImportGraphResult
    # Пока возвращаем сырые данные для прототипа экспорта
    return data


def cmd_import(args: argparse.Namespace) -> int:
    """Обработка команды import."""
    from leak_data_importer.importers import IMPORTER_REGISTRY

    if not args.source:
        print("[ERROR] Для команды import требуется --source")
        return 1

    source = Path(args.source)
    fmt = args.format.lower()

    if fmt == "auto":
        if source.suffix.lower() == ".txt" or source.name.startswith("report_"):
            fmt = "txt_report"
        else:
            fmt = "txt_report"

    importer_cls = IMPORTER_REGISTRY.get(fmt)
    if not importer_cls:
        print(f"[ERROR] Неизвестный формат: {fmt}. Доступны: {list(IMPORTER_REGISTRY.keys())}")
        return 1

    print(f"leak-data-importer v{get_version()}")
    print(f"[INFO] Используется импортёр: {importer_cls.name}")
    print(f"[INFO] Источник: {source}")

    try:
        importer = importer_cls(source)

        if args.stats or fmt == "txt_report":
            records, stats = (
                importer.parse_with_stats()
                if hasattr(importer, "parse_with_stats")
                else (list(importer.iter_records()), None)
            )
            print(f"[SUCCESS] Извлечено {len(records)} записей")
            if stats:
                print("  Стратегии:", stats.by_strategy)
                print("  Низкая уверенность:", stats.low_confidence_records)
        else:
            records = list(importer.iter_records())
            print(f"[SUCCESS] Обработано {len(records)} записей")

        if args.dry_run or args.stats:
            if records:
                print("\n--- Примеры записей ---")
                for rec in records[:3]:
                    print(f"  {getattr(rec, 'full_name', rec)}")

        # TODO: полноценная запись в БД/граф будет добавлена позже
        if not args.dry_run:
            print("[INFO] Запись результатов в БД/граф пока не реализована в этой версии CLI.")

    except Exception as e:
        print(f"[ERROR] {e}")
        return 1

    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Обработка команды export — полноценный экспорт в CSV / JSON Lines.

    Поддерживает два режима:
    - Прямой экспорт из отчёта утечки (--input report_*.txt) — запускает импортёр + parse_to_graph на лету.
    - Экспорт из ранее сохранённого JSON-результата (с ключами entities/graph).
    """
    from leak_data_importer.exporters import EXPORTER_REGISTRY
    from leak_data_importer.importers.txt_report import TxtReportImporter

    print(f"leak-data-importer v{get_version()}")
    print(f"[INFO] Формат экспорта: {args.format}")

    if not args.input:
        print("[ERROR] Требуется --input (путь к отчёту .txt или к JSON с результатом графа)")
        return 1

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        # === Режим 1: прямой импорт из исходного отчёта утечки ===
        if input_path.suffix.lower() in (".txt",) or input_path.name.startswith("report_") or input_path.name.startswith("synthetic"):
            print(f"[INFO] Распознан исходный отчёт. Запускаем импорт + экспорт на лету: {input_path}")
            importer = TxtReportImporter(input_path)
            result = importer.parse_to_graph()
            print(f"[INFO] Получено сущностей: {len(result.graph.entities)}, связей: {len(result.graph.relationships)}")

        # === Режим 2: загрузка ранее сохранённого результата (JSON) ===
        else:
            if input_path.is_dir():
                print("[ERROR] Прямой экспорт из директории пока не поддерживается. Укажите файл.")
                return 1

            print(f"[INFO] Чтение сохранённого результата из {input_path}")
            with input_path.open(encoding="utf-8") as f:
                raw = json.load(f)

            if "entities" not in raw and "graph" not in raw:
                print("[ERROR] Файл не похож на сохранённый результат графа (нужен JSON с 'entities'/'graph').")
                print("        Для прямого экспорта из отчёта используйте .txt файл как --input.")
                return 1

            # Минимальная обёртка, совместимая с экспортёрами
            class SimpleGraphResult:
                def __init__(self, data: dict):
                    g = data.get("graph", data)
                    self.graph = type("G", (), {
                        "entities": g.get("entities", data.get("entities", [])),
                        "relationships": g.get("relationships", data.get("relationships", [])),
                    })()
                    self.flat_records = data.get("flat_records", [])
                    self.stats = data.get("stats", {})

            result = SimpleGraphResult(raw)

        # Выбор экспортёра
        exporter_cls = EXPORTER_REGISTRY.get(args.format) or EXPORTER_REGISTRY.get("csv")
        if not exporter_cls:
            print(f"[ERROR] Неизвестный формат: {args.format}. Доступны: {list(EXPORTER_REGISTRY.keys())}")
            return 1

        exporter = exporter_cls(
            redact_pii=not getattr(args, "no_redact", False),
            entity_types=args.entity_types.split(",") if getattr(args, "entity_types", None) else None,
        )

        metrics = exporter.export(result, output_path)

        print("\n[SUCCESS] Экспорт завершён")
        print(f"  Сущностей: {metrics.get('entities_exported', 0)}")
        print(f"  Связей:    {metrics.get('relationships_exported', 0)}")
        print(f"  Файлы:     {metrics.get('files_created', [])}")
        print(f"  Выход:     {output_path}")

    except Exception as e:
        print(f"[ERROR] Ошибка экспорта: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="leak-data-importer",
        description="Безопасный импорт, нормализация и обработка утечек и чувствительных данных.",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {get_version()}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # === import ===
    p_import = subparsers.add_parser("import", help="Импорт и нормализация данных из утечек")
    p_import.add_argument("--source", "-s", required=True, help="Путь к файлу или папке с данными")
    p_import.add_argument("--format", "-f", default="auto", help="Формат входных данных")
    p_import.add_argument("--dry-run", action="store_true", help="Только анализ, без записи")
    p_import.add_argument("--stats", action="store_true", help="Показать подробную статистику парсинга")
    p_import.set_defaults(func=cmd_import)

    # === export ===
    p_export = subparsers.add_parser("export", help="Экспорт обработанных данных")
    p_export.add_argument(
        "format",
        choices=["csv", "jsonlines", "jsonl"],
        help="Целевой формат экспорта",
    )
    p_export.add_argument(
        "--input", "-i",
        required=True,
        help="Путь к сохранённому результату импорта (JSON с графом)",
    )
    p_export.add_argument(
        "--output", "-o",
        default="./data/processed/export/",
        help="Путь для результатов экспорта (файл или директория)",
    )
    p_export.add_argument(
        "--no-redact",
        action="store_true",
        help="Не маскировать PII (по умолчанию PII редактируется)",
    )
    p_export.add_argument(
        "--entity-types",
        help="Ограничить экспорт только указанными типами (через запятую)",
    )
    p_export.set_defaults(func=cmd_export)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
