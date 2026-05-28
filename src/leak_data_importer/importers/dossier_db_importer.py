"""
DossierDBImporter - High-level integration layer.

Combines:
- DossierParser (detailed parsing)
- PersonLinker (optional cross-report fuzzy linking)
- ReportMapper (DB insertion)
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from leak_data_importer.parsers.dossier_parser import DossierParser
from leak_data_importer.parsers.dossier_models import ParsedReport
from leak_data_importer.db.report_mapper import ReportMapper
from leak_data_importer.linkers.person_linker import PersonLinker


class DossierDBImporter:
    """
    Convenient high-level class for importing dossier reports into the database.
    """

    def __init__(self, dsn: str):
        self.parser = DossierParser()
        self.mapper = ReportMapper(dsn)
        self.linker = PersonLinker()

    def import_file(
        self,
        path: Path | str,
        created_by: Optional[str] = None,
        do_linking: bool = False,
        other_reports: Optional[List[ParsedReport]] = None
    ) -> dict:
        """
        Parse a single file and import it into the database.

        Returns summary with report_id and optional linking results.
        """
        path = Path(path)
        report = self.parser.parse_file(path)

        with self.mapper as m:
            report_id = m.insert_report(report, created_by=created_by)

        result = {
            "report_id": str(report_id),
            "filename": report.filename,
            "main_fio": report.main_person.fio,
            "warnings": report.warnings,
        }

        # Optional cross-report linking
        if do_linking and other_reports:
            matches = self.linker.find_matches([report] + other_reports)
            result["potential_links"] = matches

        return result

    def import_many(
        self,
        paths: List[Path | str],
        created_by: Optional[str] = None,
        perform_cross_linking: bool = True
    ) -> dict:
        """
        Import multiple reports and optionally run fuzzy linking across all of them.
        """
        reports: List[ParsedReport] = []
        inserted_ids = []

        for p in paths:
            report = self.parser.parse_file(p)
            reports.append(report)

            with self.mapper as m:
                rid = m.insert_report(report, created_by=created_by)
                inserted_ids.append(str(rid))

        result = {
            "imported_reports": len(reports),
            "report_ids": inserted_ids,
        }

        if perform_cross_linking and len(reports) > 1:
            links = self.linker.find_matches(reports)
            result["cross_report_links"] = links

        return result
