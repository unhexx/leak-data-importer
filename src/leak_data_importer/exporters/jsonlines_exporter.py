"""
JSON Lines экспортёр (NDJSON).

Каждая сущность и каждая связь записывается отдельной строкой в JSON.
Удобно для потоковой обработки, Spark, BigQuery, ClickHouse и т.д.

Пример:
    from leak_data_importer.exporters.jsonlines_exporter import JSONLinesExporter

    exporter = JSONLinesExporter(redact_pii=True)
    exporter.export(result, "./data/processed/entities.jsonl")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from leak_data_importer.exporters.base import BaseExporter
from leak_data_importer.graph.result import ImportGraphResult


class JSONLinesExporter(BaseExporter):
    """
    Экспортирует сущности и связи в формате JSON Lines.

    По умолчанию пишет два файла:
        - entities.jsonl
        - relationships.jsonl

    Можно указать единый файл через параметр combined=True.
    """

    def export(
        self,
        result: ImportGraphResult,
        output_path: str | Path,
        combined: bool = False,
        **options: Any,
    ) -> dict[str, Any]:
        """
        Выполняет экспорт в JSON Lines.

        Args:
            result: Результат импорта.
            output_path: Путь к файлу или директории.
            combined: Если True — пишет всё в один файл (с полем "record_type").
            **options: Доп. параметры.

        Returns:
            Метрики экспорта.
        """
        output = Path(output_path)

        entities, relationships = self.get_entities_and_relationships(result)

        if combined:
            # Один файл со всеми записями
            output.parent.mkdir(parents=True, exist_ok=True)
            count = self._write_combined(output, entities, relationships)
            return {
                "entities_exported": len(entities),
                "relationships_exported": len(relationships),
                "files_created": [str(output)],
                "combined": True,
            }

        # Два отдельных файла
        if output.suffix:
            # Пользователь указал файл — используем как базовое имя
            base = output.with_suffix("")
            entities_file = base.with_name(base.name + "_entities.jsonl")
            rels_file = base.with_name(base.name + "_relationships.jsonl")
        else:
            # Указана директория
            output.mkdir(parents=True, exist_ok=True)
            entities_file = output / "entities.jsonl"
            rels_file = output / "relationships.jsonl"

        entities_file.parent.mkdir(parents=True, exist_ok=True)

        ent_count = self._write_lines(entities_file, entities, "entity")
        rel_count = self._write_lines(rels_file, relationships, "relationship")

        return {
            "entities_exported": ent_count,
            "relationships_exported": rel_count,
            "files_created": [str(entities_file), str(rels_file)],
            "combined": False,
            "redact_pii": self.redact_pii,
        }

    def _write_lines(self, filepath: Path, items: list[Any], record_type: str) -> int:
        """Пишет список объектов построчно в JSON Lines."""
        count = 0
        with filepath.open("w", encoding="utf-8") as f:
            for item in items:
                if record_type == "entity":
                    data = self._safe_serialize_entity(item)
                else:
                    data = self._safe_serialize_relationship(item)

                data["_record_type"] = record_type
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
                count += 1

        print(f"[JSONL] Записано {count} записей в {filepath.name}")
        return count

    def _write_combined(self, filepath: Path, entities: list, relationships: list) -> int:
        """Пишет сущности + связи в один файл."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        total = 0

        with filepath.open("w", encoding="utf-8") as f:
            for e in entities:
                data = self._safe_serialize_entity(e)
                data["_record_type"] = "entity"
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
                total += 1

            for r in relationships:
                data = self._safe_serialize_relationship(r)
                data["_record_type"] = "relationship"
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
                total += 1

        print(f"[JSONL] Записано {total} записей (комбинировано) в {filepath.name}")
        return total
