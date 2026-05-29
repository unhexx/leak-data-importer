"""
PersonLinker - fuzzy cross-report person matching.

Goal: Find the same real person across different ParsedReport objects
using multiple matching strategies: FIO + birth_date + documents (passport, SNILS, INN) + phones.

Supports multiple strategies with weighted scoring:
- exact_passport: Exact passport match (highest confidence)
- exact_snils: Exact SNILS match
- exact_inn: Exact INN match
- fuzzy_fio: Fuzzy FIO match using Levenshtein distance
- fuzzy_phone: Phone number partial match
- fuzzy_birthdate: Birth date within tolerance

Each match strategy contributes to the overall confidence score.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Set
from rapidfuzz import fuzz
from datetime import date, timedelta

from leak_data_importer.parsers.dossier_models import ParsedReport, ParsedPerson


class MatchStrategy:
    """Enum-like class for match strategy names."""
    EXACT_PASSPORT = "exact_passport"
    EXACT_SNILS = "exact_snils"
    EXACT_INN = "exact_inn"
    EXACT_PHONE = "exact_phone"
    FUZZY_FIO = "fuzzy_fio"
    FUZZY_PHONE = "fuzzy_phone"
    FUZZY_BIRTHDATE = "fuzzy_birthdate"


class PersonLinker:
    """
    Finds potential matches between persons from different reports.
    
    Uses multiple strategies with weighted confidence scoring.
    """

    # Strategy weights (must sum to 1.0)
    STRATEGY_WEIGHTS = {
        MatchStrategy.EXACT_PASSPORT: 0.40,
        MatchStrategy.EXACT_SNILS: 0.25,
        MatchStrategy.EXACT_INN: 0.20,
        MatchStrategy.EXACT_PHONE: 0.05,
        MatchStrategy.FUZZY_FIO: 0.05,
        MatchStrategy.FUZZY_PHONE: 0.025,
        MatchStrategy.FUZZY_BIRTHDATE: 0.025,
    }
    # Total: 0.40 + 0.25 + 0.20 + 0.05 + 0.05 + 0.025 + 0.025 = 1.0

    def __init__(
        self,
        fio_threshold: float = 0.70,
        require_birth_date: bool = False,
        birth_date_tolerance_days: int = 30,
    ):
        """
        Initialize PersonLinker.
        
        Args:
            fio_threshold: Minimum FIO similarity for fuzzy match (0.0-1.0)
            require_birth_date: If True, require birth_date for any match
            birth_date_tolerance_days: Days tolerance for fuzzy birth date match
        """
        self.fio_threshold = fio_threshold
        self.require_birth_date = require_birth_date
        self.birth_date_tolerance_days = birth_date_tolerance_days

    def find_matches(
        self,
        reports: List[ParsedReport],
        min_score: float = 0.60
    ) -> List[Dict[str, Any]]:
        """
        Returns list of potential person clusters across reports.
        Each cluster is a list of person records with similarity score.
        
        Args:
            reports: List of parsed reports to match
            min_score: Minimum overall confidence score (0.0-1.0)
            
        Returns:
            List of match clusters with strategy details
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
                "snils": p.snils,
                "inn": p.inn,
                "passports": set(p.passports + p.extra_passports),
                "phones": set(p.phones + p.extra_phones),
            })

        clusters: List[List[Dict[str, Any]]] = []

        for p1 in all_persons:
            best_cluster: Optional[List[Dict[str, Any]]] = None
            best_score = 0.0

            for cluster in clusters:
                rep = cluster[0]
                score, _ = self._similarity_score_with_strategies(p1, rep)

                if score > best_score:
                    best_score = score
                    best_cluster = cluster

            if best_score >= min_score:
                best_cluster.append(p1)
            else:
                clusters.append([p1])

        results: List[Dict[str, Any]] = []
        for cluster in clusters:
            if len(cluster) > 1:
                result = self._format_cluster_result(cluster)
                results.append(result)

        return results

    def _similarity_score_with_strategies(
        self,
        p1: Dict[str, Any],
        p2: Dict[str, Any],
    ) -> tuple[float, Dict[str, float]]:
        """
        Calculate similarity score and return breakdown by strategy.
        
        Returns:
            Tuple of (overall_score, strategy_scores_dict)
        """
        strategy_scores: Dict[str, float] = {}
        
        # Exact passport match (strongest signal)
        shared_passports = p1["passports"] & p2["passports"]
        if shared_passports:
            strategy_scores[MatchStrategy.EXACT_PASSPORT] = 1.0
        
        # Exact SNILS match
        if p1.get("snils") and p2.get("snils") and p1["snils"] == p2["snils"]:
            strategy_scores[MatchStrategy.EXACT_SNILS] = 1.0
        
        # Exact INN match
        if p1.get("inn") and p2.get("inn") and p1["inn"] == p2["inn"]:
            strategy_scores[MatchStrategy.EXACT_INN] = 1.0
        
        # Exact phone match
        shared_phones = p1["phones"] & p2["phones"]
        if shared_phones:
            strategy_scores[MatchStrategy.EXACT_PHONE] = 1.0
        
        # Strong exact match - return 1.0 immediately
        if (
            MatchStrategy.EXACT_PASSPORT in strategy_scores or
            MatchStrategy.EXACT_SNILS in strategy_scores or
            MatchStrategy.EXACT_INN in strategy_scores
        ):
            return 1.0, strategy_scores
        
        # Fuzzy FIO (using token_sort_ratio for Russian names)
        if p1["fio"] and p2["fio"]:
            fio_score = fuzz.token_sort_ratio(p1["fio"], p2["fio"]) / 100.0
            if fio_score >= self.fio_threshold:
                strategy_scores[MatchStrategy.FUZZY_FIO] = fio_score
        
        # Fuzzy phone (partial match)
        phone_score = self._phone_similarity(p1["phones"], p2["phones"])
        if phone_score > 0:
            strategy_scores[MatchStrategy.FUZZY_PHONE] = phone_score
        
        # Fuzzy birth date (within tolerance)
        if p1["birth_date"] and p2["birth_date"]:
            birth_score = self._birthdate_similarity(
                p1["birth_date"], p2["birth_date"]
            )
            if birth_score > 0:
                strategy_scores[MatchStrategy.FUZZY_BIRTHDATE] = birth_score
        elif not self.require_birth_date and not p1.get("snils"):
            # No birth date but no strong ID either
            strategy_scores[MatchStrategy.FUZZY_BIRTHDATE] = 0.5

        # Calculate weighted confidence score
        overall_score = self._calculate_weighted_score(strategy_scores)
        
        return overall_score, strategy_scores

    def _calculate_weighted_score(self, strategy_scores: Dict[str, float]) -> float:
        """Calculate weighted score from strategy scores."""
        total = 0.0
        for strategy, score in strategy_scores.items():
            weight = self.STRATEGY_WEIGHTS.get(strategy, 0.0)
            total += score * weight
        return min(1.0, total)

    def _phone_similarity(self, phones1: Set[str], phones2: Set[str]) -> float:
        """Calculate phone similarity using partial matching."""
        if not phones1 or not phones2:
            return 0.0
        
        def normalize(phone: str) -> str:
            return phone.replace(" ", "").replace("-", "")[-6:]
        
        norm1 = {normalize(p) for p in phones1}
        norm2 = {normalize(p) for p in phones2}
        
        shared = norm1 & norm2
        if shared:
            return min(1.0, len(shared) * 0.3)
        return 0.0

    def _birthdate_similarity(self, d1: date, d2: date) -> float:
        """Calculate birth date similarity within tolerance."""
        if d1 == d2:
            return 1.0
        
        diff = abs((d1 - d2).days)
        if diff <= self.birth_date_tolerance_days:
            return 1.0 - (diff / self.birth_date_tolerance_days) * 0.5
        return 0.0

    def _format_cluster_result(self, cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format cluster result with strategy details."""
        scores = []
        strategies_used: Dict[str, List[str]] = {}
        
        for i, p1 in enumerate(cluster):
            for p2 in cluster[i+1:]:
                score, strategies = self._similarity_score_with_strategies(p1, p2)
                scores.append(score)
                for strat, strat_score in strategies.items():
                    strategies_used.setdefault(strat, []).append(
                        f"{p1['filename']} <-> {p2['filename']}: {strat_score:.2f}"
                    )
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        return {
            "persons": cluster,
            "confidence": avg_score,
            "match_count": len(cluster),
            "shared_documents": self._find_shared_documents(cluster),
            "strategies_used": strategies_used,
        }

    def _find_shared_documents(self, cluster: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Find documents that appear in multiple persons in the cluster."""
        all_docs: Dict[str, List[str]] = {}

        for p in cluster:
            for doc in p["passports"]:
                all_docs.setdefault(doc, []).append(p["filename"])

        shared = {doc: files for doc, files in all_docs.items() if len(files) > 1}
        return shared
