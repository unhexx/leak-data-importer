"""Importers package."""

from leak_data_importer.importers.base import BaseImporter
from leak_data_importer.importers.txt_report import TxtReportImporter
from leak_data_importer.importers.dossier_db_importer import DossierDBImporter

__all__ = ["BaseImporter", "TxtReportImporter", "DossierDBImporter"]

IMPORTER_REGISTRY = {
    "txt_report": TxtReportImporter,
    "txt": TxtReportImporter,
    "dossier": DossierDBImporter,   # new spec-compliant importer with DB support
}
