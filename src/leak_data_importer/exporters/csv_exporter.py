"""
CSV-экспортёр для ImportGraphResult.

Экспортирует сущности и связи в CSV-файлы внутри указанной директории.
Поддерживает редактирование PII и фильтрацию по типам сущностей.

Пример использования:
    from leak_data_importer.exporters.csv_exporter import CSVExporter

    exporter = CSVExporter(redact_pii=True)
    metrics = exporter.export(result, "./data/processed/export_csv/")
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from leak_data_importer.exporters.base import BaseExporter
from leak_data_importer.graph.result import ImportGraphResult


class CSVExporter(BaseExporter):
    """
    Экспортирует граф в набор CSV-файлов.

    Структура выходной директории:
        output_dir/
            entities_person.csv
            entities_phone_number.csv
            ...
            relationships.csv

    Каждая сущность получает колонки: id, type, canonical_key, source_refs + все свои properties.
    Поддерживает entity_types= для фильтрации (через конструктор или опции).
    """

    def __init__(self, redaction_level: str = "standard", entity_types: list[str] | None = None, **options: Any):
        super().__init__(redaction_level=redaction_level, **options)
        self.entity_types = entity_types

    def export(
        self,
        result: ImportGraphResult,
        output_path: str | Path,
        **options: Any,
    ) -> dict[str, Any]:
        """
        Выполняет экспорт в CSV.

        Args:
            result: Результат импорта с графом.
            output_path: Путь к директории, куда будут записаны CSV-файлы.
            **options: Дополнительные параметры (пока не используются).

        Returns:
            Метрики экспорта: количество сущностей по типам, количество связей, список файлов.
        """
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)

        entities, relationships = self.get_entities_and_relationships(result)

        # Фильтрация по типам, если указана (поддержка entity_types= в конструкторе/экспорте)
        if getattr(self, "entity_types", None):
            entities = self.filter_entities(entities, self.entity_types)

        # Группируем сущности по типу
        entities_by_type: dict[str, list[dict]] = defaultdict(list)
        for entity in entities:
            # entity может быть dict после фильтра
            etype = entity.get("type") if isinstance(entity, dict) else getattr(entity, "type", "unknown")
            serialized = self._safe_serialize_entity(entity)
            entities_by_type[etype].append(serialized)

        created_files: list[str] = []

        # Пишем отдельный CSV для каждого типа сущностей
        for entity_type, rows in sorted(entities_by_type.items()):
            if not rows:
                continue

            filename = f"entities_{entity_type}.csv"
            filepath = output_dir / filename

            # Собираем все возможные колонки из первого ряда (стабильно)
            fieldnames = self._get_fieldnames(rows)

            with filepath.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)

            created_files.append(str(filepath))
            print(f"[CSV] Записан {len(rows)} записей в {filename}")

        # Экспорт связей (всегда один файл)
        rel_rows = [self._safe_serialize_relationship(r) for r in relationships]
        if rel_rows:
            rel_file = output_dir / "relationships.csv"
            rel_fieldnames = self._get_fieldnames(rel_rows)

            with rel_file.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rel_fieldnames, extrasaction="ignore")
                writer.writeheader()
                for row in rel_rows:
                    writer.writerow(row)

            created_files.append(str(rel_file))
            print(f"[CSV] Записано {len(rel_rows)} связей в relationships.csv")

        return {
            "entities_exported": len(entities),
            "relationships_exported": len(relationships),
            "files_created": created_files,
            "output_dir": str(output_dir),
            "redact_pii": self.redact_pii,
        }

    def _get_fieldnames(self, rows: list[dict[str, Any]]) -> list[str]:
        """Собирает стабильный список колонок из всех строк (union)."""
        if not rows:
            return ["id", "type", "canonical_key", "source_refs"]

        keys: set[str] = set()
        for row in rows:
            keys.update(row.keys())

        # Важные колонки всегда первыми
        priority = ["id", "type", "canonical_key", "source_refs", "confidence", "from_id", "to_id"]
        ordered = [k for k in priority if k in keys]

        remaining = sorted(k for k in keys if k not in priority)
        return ordered + remaining
