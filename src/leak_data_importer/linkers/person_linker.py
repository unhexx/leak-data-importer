"""
PersonLinker - fuzzy cross-report person matching.

Goal: Find the same real person across different ParsedReport objects
using FIO + birth_date + documents (with fuzzy tolerance).
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz
from datetime import date

from leak_data_importer.parsers.dossier_models import ParsedReport, ParsedPerson


class PersonLinker:
    """
    Finds potential matches between persons from different reports.
    """

    def __init__(self, fio_threshold: int = 85, require_birth_date: bool = False):
        self.fio_threshold = fio_threshold
        self.require_birth_date = require_birth_date

    def find_matches(
        self,
        reports: List[ParsedReport],
        min_score: float = 0.75
    ) -> List[Dict[str, Any]]:
        """
        Returns list of potential person clusters across reports.
        Each cluster is a list of (report_id, person) with similarity score.
        """
        all_persons: List[Dict[str, Any]] = []

        for report in reports:
            p = report.main_person
            all_persons.append({
                "report_id": str(report.report_id),
                "filename": report.filename,
                "person": p,
                "fio": p.fio,
                "birth_date": p.birth_date,
                "passports": set(p.passports + p.extra_passports),
                "phones": set(p.phones + p.extra_phones),
            })

        clusters: List[List[Dict[str, Any]]] = []

        for i, p1 in enumerate(all_persons):
            best_cluster = None
            best_score = 0.0

            for cluster in clusters:
                # Compare against representative of the cluster
                rep = cluster[0]
                score = self._similarity_score(p1, rep)

                if score > best_score:
                    best_score = score
                    best_cluster = cluster

            if best_score >= min_score:
                best_cluster.append(p1)
            else:
                clusters.append([p1])

        # Filter and format results
        results = []
        for cluster in clusters:
            if len(cluster) > 1:
                results.append({
                    "persons": cluster,
                    "avg_score": sum(self._similarity_score(a, b) for a in cluster for b in cluster if a != b) / max(1, len(cluster)*(len(cluster)-1)),
                    "shared_documents": self._find_shared_documents(cluster),
                })

        return results

    def _similarity_score(self, p1: Dict, p2: Dict) -> float:
        fio_score = fuzz.token_sort_ratio(p1["fio"], p2["fio"]) / 100.0

        birth_score = 0.0
        if p1["birth_date"] and p2["birth_date"]:
            birth_score = 1.0 if p1["birth_date"] == p2["birth_date"] else 0.3
        elif not self.require_birth_date:
            birth_score = 0.6

        # Strong boost from shared passports
        shared_passports = len(p1["passports"] & p2["passports"])
        passport_boost = min(0.4, shared_passports * 0.2)

        score = (fio_score * 0.55) + (birth_score * 0.25) + passport_boost
        return min(1.0, score)

    def _find_shared_documents(self, cluster: List[Dict]) -> Dict[str, List[str]]:
        """Find documents that appear in multiple persons in the cluster."""
        all_docs: Dict[str, List[str]] = {}  # doc -> list of report filenames

        for p in cluster:
            for doc in p["passports"]:
                all_docs.setdefault(doc, []).append(p["filename"])

        shared = {doc: files for doc, files in all_docs.items() if len(files) > 1}
        return shared
