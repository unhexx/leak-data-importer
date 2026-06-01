"""Пакет экспортёров.

Содержит готовые экспортёры для разных целей:
- CSVExporter — табличный экспорт в директорию с CSV-файлами
- JSONLinesExporter — потоковый NDJSON (удобно для дальнейшей обработки)
- Neo4j — графовый экспорт (существующий)

Также предоставляет BaseExporter для создания собственных экспортёров.
"""

from leak_data_importer.exporters.base import BaseExporter, get_default_redactors
from leak_data_importer.exporters.csv_exporter import CSVExporter
from leak_data_importer.exporters.jsonlines_exporter import JSONLinesExporter
from leak_data_importer.exporters.neo4j_exporter import (
    export_person_links,
    export_to_neo4j,
    export_to_neo4j_legacy,
    setup_neo4j_constraints,
)

__all__ = [
    "BaseExporter",
    "CSVExporter",
    "JSONLinesExporter",
    "export_to_neo4j",
    "setup_neo4j_constraints",
    "export_person_links",
    "export_to_neo4j_legacy",
    "get_default_redactors",
]

# Удобный реестр для CLI и динамического выбора
EXPORTER_REGISTRY = {
    "csv": CSVExporter,
    "jsonlines": JSONLinesExporter,
    "jsonl": JSONLinesExporter,
    # Neo4j остаётся отдельной функцией из-за необходимости соединения
}
