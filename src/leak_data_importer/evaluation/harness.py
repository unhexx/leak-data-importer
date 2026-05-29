"""
Evaluation harness for entity resolution quality assessment.

Provides tools for reviewing and evaluating linking quality,
exporting results, and generating metrics.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from leak_data_importer.linkers.person_linker import PersonLinker, MatchStrategy


class EvaluationHarness:
    """
    Оценка качества entity resolution.
    
    Инструмент для проверки результатов связывания персон
    из разных отчётов и оценки качества совпадений.
    """
    
    def __init__(
        self,
        linker: Optional[PersonLinker] = None,
        min_confidence: float = 0.5,
    ):
        """
        Инициализация harness.
        
        Args:
            linker: PersonLinker для запуска (создаётся если None)
            min_confidence: Минимальная уверенность для показа
        """
        self.linker = linker or PersonLinker()
        self.min_confidence = min_confidence
        self.results: list[dict[str, Any]] = []
        
    def run_evaluation(
        self,
        reports: list[Any],
        min_score: float = 0.6,
    ) -> dict[str, Any]:
        """
        Запускает оценку на списке отчётов.
        
        Args:
            reports: Список ParsedReport объектов
            min_score: Минимальный скор для связывания
            
        Returns:
            словарь с результатами оценки
        """
        matches = self.linker.find_matches(reports, min_score=min_score)
        
        # Фильтруем по confidence
        filtered = [m for m in matches if m.get("confidence", 0) >= self.min_confidence]
        
        self.results = filtered
        
        return self._generate_report(filtered)
    
    def _generate_report(self, matches: list[dict[str, Any]]) -> dict[str, Any]:
        """Генерирует отчёт по результатам."""
        if not matches:
            return {
                "total_matches": 0,
                "high_confidence": 0,
                "medium_confidence": 0,
                "low_confidence": 0,
                "avg_confidence": 0.0,
                "strategy_breakdown": {},
            }
        
        # Категории по уверенности
        high = sum(1 for m in matches if m.get("confidence", 0) >= 0.8)
        medium = sum(1 for m in matches if 0.5 <= m.get("confidence", 0) < 0.8)
        low = sum(1 for m in matches if m.get("confidence", 0) < 0.5)
        
        avg = sum(m.get("confidence", 0) for m in matches) / len(matches)
        
        # Breakdown по стратегиям
        strategy_counts: dict[str, int] = {}
        for m in matches:
            strategies = m.get("strategies_used", {})
            for strat in strategies:
                strategy_counts[strat] = strategy_counts.get(strat, 0) + 1
        
        return {
            "total_matches": len(matches),
            "high_confidence": high,
            "medium_confidence": medium,
            "low_confidence": low,
            "avg_confidence": round(avg, 3),
            "strategy_breakdown": strategy_counts,
            "matches": matches,
        }
    
    def export_review_list(self, output_path: str) -> None:
        """
        Экспортирует список для ручного просмотра.
        
        Args:
            output_path: Путь для сохранения JSON
        """
        review_data = []
        
        for i, match in enumerate(self.results):
            persons = match.get("persons", [])
            
            # Формируем запись для review
            record = {
                "cluster_id": i + 1,
                "confidence": match.get("confidence", 0),
                "match_count": match.get("match_count", 0),
                "shared_documents": match.get("shared_documents", {}),
                "persons": [
                    {
                        "filename": p.get("filename"),
                        "fio": p.get("fio"),
                        "birth_date": str(p.get("birth_date", "")),
                    }
                    for p in persons
                ],
                "strategies_used": match.get("strategies_used", {}),
                "decision": "",  # Для заполнения при review
            }
            review_data.append(record)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(review_data, f, ensure_ascii=False, indent=2)
    
    def load_review_decisions(self, input_path: str) -> dict[str, bool]:
        """
        Загружает решения из файла review.
        
        Args:
            input_path: Путь к JSON с решениями
            
        Returns:
            словарь cluster_id -> is_confirmed
        """
        with open(input_path, encoding="utf-8") as f:
            decisions = json.load(f)
        
        return {
            str(d.get("cluster_id")): d.get("decision", "").lower() == "confirm"
            for d in decisions
        }
    
    def get_uncertain_matches(self, threshold: float = 0.7) -> list[dict[str, Any]]:
        """
        Возвращает матчи с низкой уверенностью для review.
        
        Args:
            threshold: Порог уверенности
            
        Returns:
            Список неопределённых матчей
        """
        return [
            m for m in self.results
            if m.get("confidence", 0) < threshold
        ][:50]  # Ограничиваем 50 для читаемости


def print_evaluation_summary(report: dict[str, Any]) -> None:
    """Печатает краткое резюме оценки."""
    print("\n" + "=" * 50)
    print("ENTITY RESOLUTION EVALUATION SUMMARY")
    print("=" * 50)
    print(f"Total matches found: {report.get('total_matches', 0)}")
    print(f"  - High confidence (>=0.8): {report.get('high_confidence', 0)}")
    print(f"  - Medium confidence (0.5-0.8): {report.get('medium_confidence', 0)}")
    print(f"  - Low confidence (<0.5): {report.get('low_confidence', 0)}")
    print(f"\nAverage confidence: {report.get('avg_confidence', 0):.3f}")
    
    strategies = report.get("strategy_breakdown", {})
    if strategies:
        print("\nStrategy usage:")
        for strat, count in sorted(strategies.items(), key=lambda x: -x[1]):
            print(f"  - {strat}: {count}")
    
    print("=" * 50 + "\n")


# Консольный интерфейс для быстрого запуска
if __name__ == "__main__":
    import sys
    from leak_data_importer.parsers.dossier_parser import DossierParser
    
    if len(sys.argv) < 2:
        print("Usage: python -m harness <report_dir>")
        sys.exit(1)
    
    report_dir = sys.argv[1]
    parser = DossierParser()
    
    # Парсим все отчёты
    from pathlib import Path
    reports = []
    for txt_file in Path(report_dir).glob("*.txt"):
        try:
            report = parser.parse_file(txt_file)
            reports.append(report)
        except Exception as e:
            print(f"Error parsing {txt_file}: {e}")
    
    # Запускаем evaluation
    harness = EvaluationHarness()
    result = harness.run_evaluation(reports)
    
    print_evaluation_summary(result)
    
    # Экспортируем для review
    harness.export_review_list("entity_resolution_review.json")
    print("Review list exported to: entity_resolution_review.json")
