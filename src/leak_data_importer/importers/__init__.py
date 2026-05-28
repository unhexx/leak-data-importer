"""Importers package."""

from leak_data_importer.importers.base import BaseImporter
from leak_data_importer.importers.txt_report import TxtReportImporter

__all__ = ["BaseImporter", "TxtReportImporter"]

IMPORTER_REGISTRY = {
    "txt_report": TxtReportImporter,
    "txt": TxtReportImporter,   # alias
}
